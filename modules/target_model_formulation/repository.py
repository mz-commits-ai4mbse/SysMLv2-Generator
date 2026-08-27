"""Immutable filesystem persistence for Target-Model Formulation Human authority."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import re

from .authority import (
    TargetModelFormulationAuthoritySet,
    TargetModelFormulationDecision,
    create_formulation_authority_set,
    create_formulation_decision,
    validate_decision_against_review,
)
from .contract import (
    create_formulation_candidate,
    create_formulation_review,
    create_reference_evidence,
    create_review_item,
)
from .errors import TargetModelFormulationError
from .types import TargetModelFormulationReview


_TFR = re.compile(r"^TFR-([0-9]{6})\.json$")
_TFD = re.compile(r"^TFD-([0-9]{6})\.json$")
_TFA = re.compile(r"^TFA-([0-9]{6})\.json$")


class TargetModelFormulationAuthorityRepository:
    """Persist TFR/TFD/TFA artifacts without mutating prior Human authority."""

    def __init__(self, root: Path | str = Path("data/projects")) -> None:
        self.root = Path(root)

    def record_review(self, review: TargetModelFormulationReview) -> Path:
        path = self._review_path(review.project_id, review.review_id)
        self._write_immutable(path, asdict(review), "Target-Model Formulation review")
        return path

    def allocate_review_id(self, project_id: str) -> str:
        numbers = [
            int(match.group(1))
            for path in self._reviews_dir(project_id).glob("TFR-*.json")
            if (match := _TFR.fullmatch(path.name)) is not None
        ]
        return f"TFR-{(max(numbers, default=0) + 1):06d}"

    def load_review(
        self,
        project_id: str,
        review_id: str,
    ) -> TargetModelFormulationReview:
        path = self._review_path(project_id, review_id)
        if not path.is_file() or path.is_symlink():
            raise TargetModelFormulationError(
                "Target-Model Formulation review not found."
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            review = _review_from_payload(payload)
        except TargetModelFormulationError:
            raise
        except Exception as exc:
            raise TargetModelFormulationError(
                "Persisted Target-Model Formulation review is invalid."
            ) from exc
        if review.project_id != project_id or review.review_id != review_id:
            raise TargetModelFormulationError(
                "Persisted Target-Model Formulation review binding is invalid."
            )
        return review

    def list_reviews(
        self,
        project_id: str,
    ) -> tuple[TargetModelFormulationReview, ...]:
        directory = self._reviews_dir(project_id)
        if not directory.exists():
            return ()
        if directory.is_symlink() or not directory.is_dir():
            raise TargetModelFormulationError(
                "Target-Model Formulation review path is unsafe."
            )
        result = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if path.is_symlink() or not path.is_file():
                raise TargetModelFormulationError(
                    "Unexpected Target-Model Formulation review entry."
                )
            if _TFR.fullmatch(path.name) is None:
                raise TargetModelFormulationError(
                    "Unexpected Target-Model Formulation review entry."
                )
            result.append(self.load_review(project_id, path.stem))
        return tuple(result)

    def find_review_for_source(
        self,
        project_id: str,
        source_internal_engineering_model_id: str,
        source_internal_engineering_model_fingerprint: str,
    ) -> TargetModelFormulationReview | None:
        matches = tuple(
            review
            for review in self.list_reviews(project_id)
            if (
                review.source_internal_engineering_model_id
                == source_internal_engineering_model_id
                and review.source_internal_engineering_model_fingerprint
                == source_internal_engineering_model_fingerprint
            )
        )
        if not matches:
            return None

        # Immutable review revisions are permitted for the same exact
        # source Internal Model. Review IDs are allocated monotonically,
        # so the highest ID is the current review while all prior reviews
        # remain preserved as Human-authority history.
        return max(
            matches,
            key=lambda review: review.review_id,
        )

    def allocate_decision_id(self, project_id: str) -> str:
        numbers = [
            int(match.group(1))
            for path in self._decisions_dir(project_id).glob("TFD-*.json")
            if (match := _TFD.fullmatch(path.name)) is not None
        ]
        return f"TFD-{(max(numbers, default=0) + 1):06d}"

    def allocate_authority_set_id(self, project_id: str) -> str:
        numbers = [
            int(match.group(1))
            for path in self._authority_sets_dir(project_id).glob("TFA-*.json")
            if (match := _TFA.fullmatch(path.name)) is not None
        ]
        return f"TFA-{(max(numbers, default=0) + 1):06d}"

    def record_selection(
        self,
        *,
        review: TargetModelFormulationReview,
        authority_subject_id: str,
        selected_candidate_id: str,
        reviewer_identity: str,
        rationale: str,
        decided_at: str,
    ) -> TargetModelFormulationDecision:
        self._require_persisted_review(review)
        latest = self.latest_decision_for_subject(
            review.project_id,
            review.review_id,
            authority_subject_id,
        )
        decision = create_formulation_decision(
            review=review,
            decision_id=self.allocate_decision_id(review.project_id),
            authority_subject_id=authority_subject_id,
            selected_candidate_id=selected_candidate_id,
            reviewer_identity=reviewer_identity,
            rationale=rationale,
            decided_at=decided_at,
            supersedes_decision_id=(
                latest.decision_id if latest is not None else None
            ),
        )
        self.record_decision(review=review, decision=decision)
        return decision

    def record_decision(
        self,
        *,
        review: TargetModelFormulationReview,
        decision: TargetModelFormulationDecision,
    ) -> Path:
        self._require_persisted_review(review)
        validate_decision_against_review(review, decision)

        existing_path = self._decision_path(review.project_id, decision.decision_id)
        if existing_path.exists():
            self._write_immutable(
                existing_path,
                asdict(decision),
                "Target-Model Formulation decision",
            )
            return existing_path

        latest = self.latest_decision_for_subject(
            review.project_id,
            review.review_id,
            decision.authority_subject_id,
        )
        if latest is None:
            if decision.supersedes_decision_id is not None:
                raise TargetModelFormulationError(
                    "First Target-Model Formulation decision for a subject must not supersede another decision."
                )
        else:
            if decision.supersedes_decision_id != latest.decision_id:
                raise TargetModelFormulationError(
                    "Target-Model Formulation successor must supersede the current effective decision."
                )

        self._write_immutable(
            existing_path,
            asdict(decision),
            "Target-Model Formulation decision",
        )
        return existing_path

    def latest_decision_for_subject(
        self,
        project_id: str,
        review_id: str,
        authority_subject_id: str,
    ) -> TargetModelFormulationDecision | None:
        decisions = [
            decision
            for decision in self._load_project_decisions(project_id)
            if decision.review_id == review_id
            and decision.authority_subject_id == authority_subject_id
        ]
        if not decisions:
            return None

        superseded = {
            decision.supersedes_decision_id
            for decision in decisions
            if decision.supersedes_decision_id is not None
        }
        effective = [
            decision for decision in decisions
            if decision.decision_id not in superseded
        ]
        if len(effective) != 1:
            raise TargetModelFormulationError(
                "Target-Model Formulation decision history has multiple effective decisions."
            )
        return effective[0]

    def effective_decisions(
        self,
        review: TargetModelFormulationReview,
    ) -> tuple[TargetModelFormulationDecision, ...]:
        self._require_persisted_review(review)
        decisions = []
        for item in review.items:
            decision = self.latest_decision_for_subject(
                review.project_id,
                review.review_id,
                item.authority_subject_id,
            )
            if decision is None:
                continue
            validate_decision_against_review(review, decision)
            decisions.append(decision)
        return tuple(decisions)

    def finalize_authority_set(
        self,
        *,
        review: TargetModelFormulationReview,
        created_at: str,
    ) -> TargetModelFormulationAuthoritySet:
        self._require_persisted_review(review)
        authority = create_formulation_authority_set(
            review=review,
            authority_set_id=self.allocate_authority_set_id(review.project_id),
            effective_decisions=self.effective_decisions(review),
            created_at=created_at,
        )
        self.record_authority_set(review=review, authority_set=authority)
        return authority

    def record_authority_set(
        self,
        *,
        review: TargetModelFormulationReview,
        authority_set: TargetModelFormulationAuthoritySet,
    ) -> Path:
        self._require_persisted_review(review)
        expected = create_formulation_authority_set(
            review=review,
            authority_set_id=authority_set.authority_set_id,
            effective_decisions=authority_set.effective_decisions,
            created_at=authority_set.created_at,
        )
        if expected.content_fingerprint != authority_set.content_fingerprint:
            raise TargetModelFormulationError(
                "Target-Model Formulation authority-set fingerprint is invalid."
            )
        path = self._authority_set_path(
            review.project_id,
            authority_set.authority_set_id,
        )
        self._write_immutable(
            path,
            asdict(authority_set),
            "Target-Model Formulation authority set",
        )
        return path

    def load_authority_set(
        self,
        project_id: str,
        authority_set_id: str,
    ) -> TargetModelFormulationAuthoritySet:
        path = self._authority_set_path(project_id, authority_set_id)
        if not path.is_file() or path.is_symlink():
            raise TargetModelFormulationError(
                "Target-Model Formulation authority set not found."
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            decisions = tuple(
                TargetModelFormulationDecision(**item)
                for item in payload["effective_decisions"]
            )
            value = TargetModelFormulationAuthoritySet(
                schema_version=payload["schema_version"],
                project_id=payload["project_id"],
                authority_set_id=payload["authority_set_id"],
                review_id=payload["review_id"],
                review_fingerprint=payload["review_fingerprint"],
                source_internal_engineering_model_id=(
                    payload["source_internal_engineering_model_id"]
                ),
                source_internal_engineering_model_fingerprint=(
                    payload["source_internal_engineering_model_fingerprint"]
                ),
                final_model_review_decision_id=(
                    payload["final_model_review_decision_id"]
                ),
                final_model_review_decision_fingerprint=(
                    payload["final_model_review_decision_fingerprint"]
                ),
                target_model_profile_id=payload["target_model_profile_id"],
                target_model_profile_version=(
                    payload["target_model_profile_version"]
                ),
                target_model_profile_fingerprint=(
                    payload["target_model_profile_fingerprint"]
                ),
                target_notation_fingerprint=(
                    payload["target_notation_fingerprint"]
                ),
                effective_decisions=decisions,
                created_at=payload["created_at"],
                content_fingerprint=payload["content_fingerprint"],
            )
        except Exception as exc:
            raise TargetModelFormulationError(
                "Persisted Target-Model Formulation authority set is invalid."
            ) from exc
        if value.project_id != project_id or value.authority_set_id != authority_set_id:
            raise TargetModelFormulationError(
                "Persisted Target-Model Formulation authority-set binding is invalid."
            )
        review = self.load_review(project_id, value.review_id)
        expected = create_formulation_authority_set(
            review=review,
            authority_set_id=value.authority_set_id,
            effective_decisions=value.effective_decisions,
            created_at=value.created_at,
        )
        if expected.content_fingerprint != value.content_fingerprint:
            raise TargetModelFormulationError(
                "Persisted Target-Model Formulation authority-set fingerprint is invalid."
            )
        return value

    def list_authority_sets(
        self,
        project_id: str,
    ) -> tuple[TargetModelFormulationAuthoritySet, ...]:
        directory = self._authority_sets_dir(project_id)
        if not directory.exists():
            return ()
        if directory.is_symlink() or not directory.is_dir():
            raise TargetModelFormulationError(
                "Target-Model Formulation authority-set path is unsafe."
            )
        result = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if path.is_symlink() or not path.is_file():
                raise TargetModelFormulationError(
                    "Unexpected Target-Model Formulation authority-set entry."
                )
            if _TFA.fullmatch(path.name) is None:
                raise TargetModelFormulationError(
                    "Unexpected Target-Model Formulation authority-set entry."
                )
            result.append(self.load_authority_set(project_id, path.stem))
        return tuple(result)

    def latest_authority_set_for_review(
        self,
        project_id: str,
        review_id: str,
    ) -> TargetModelFormulationAuthoritySet | None:
        values = tuple(
            item
            for item in self.list_authority_sets(project_id)
            if item.review_id == review_id
        )
        return None if not values else values[-1]

    def _load_project_decisions(
        self,
        project_id: str,
    ) -> tuple[TargetModelFormulationDecision, ...]:
        values = []
        for path in sorted(self._decisions_dir(project_id).glob("TFD-*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            values.append(TargetModelFormulationDecision(**data))
        return tuple(values)

    def _require_persisted_review(
        self,
        review: TargetModelFormulationReview,
    ) -> None:
        path = self._review_path(review.project_id, review.review_id)
        if not path.is_file():
            raise TargetModelFormulationError(
                "Target-Model Formulation review must be persisted before Human decisions."
            )
        stored = json.loads(path.read_text(encoding="utf-8"))
        if stored.get("content_fingerprint") != review.content_fingerprint:
            raise TargetModelFormulationError(
                "Persisted Target-Model Formulation review fingerprint does not match."
            )

    def _project_dir(self, project_id: str) -> Path:
        if not isinstance(project_id, str) or not project_id.strip():
            raise TargetModelFormulationError("project_id is required.")
        return self.root / project_id.strip() / "target_model_formulation"

    def _reviews_dir(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "reviews"

    def _decisions_dir(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "decisions"

    def _authority_sets_dir(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "authority_sets"

    def _review_path(self, project_id: str, review_id: str) -> Path:
        return self._reviews_dir(project_id) / f"{review_id}.json"

    def _decision_path(self, project_id: str, decision_id: str) -> Path:
        return self._decisions_dir(project_id) / f"{decision_id}.json"

    def _authority_set_path(self, project_id: str, authority_set_id: str) -> Path:
        return self._authority_sets_dir(project_id) / f"{authority_set_id}.json"

    @staticmethod
    def _write_immutable(path: Path, payload: dict, label: str) -> None:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ) + "\n"
        if path.exists():
            existing = path.read_text(encoding="utf-8")
            if existing == canonical:
                return
            raise TargetModelFormulationError(
                f"{label} is immutable and already exists with different content."
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical, encoding="utf-8")

def _review_from_payload(payload: dict) -> TargetModelFormulationReview:
    items = []
    for raw_item in payload["items"]:
        candidates = []
        for raw_candidate in raw_item["candidates"]:
            references = tuple(
                create_reference_evidence(
                    source_id=raw_ref["source_id"],
                    role=raw_ref["role"],
                    locator=raw_ref["locator"],
                    evidence_note=raw_ref["evidence_note"],
                )
                for raw_ref in raw_candidate["reference_evidence"]
            )
            for created, raw_ref in zip(
                references,
                raw_candidate["reference_evidence"],
            ):
                if created.content_fingerprint != raw_ref["content_fingerprint"]:
                    raise TargetModelFormulationError(
                        "Persisted Target-Model reference evidence fingerprint is invalid."
                    )
            candidate = create_formulation_candidate(
                candidate_id=raw_candidate["candidate_id"],
                relevance_outcome=raw_candidate["relevance_outcome"],
                target_model_pattern_id=raw_candidate["target_model_pattern_id"],
                target_notation_construct_id=(
                    raw_candidate["target_notation_construct_id"]
                ),
                formulation_text=raw_candidate["formulation_text"],
                applied_formulation_rule_ids=tuple(
                    raw_candidate["applied_formulation_rule_ids"]
                ),
                reference_evidence=references,
                rationale=raw_candidate["rationale"],
                unresolved_questions=tuple(
                    raw_candidate["unresolved_questions"]
                ),
            )
            if candidate.content_fingerprint != raw_candidate["content_fingerprint"]:
                raise TargetModelFormulationError(
                    "Persisted Target-Model candidate fingerprint is invalid."
                )
            candidates.append(candidate)

        item = create_review_item(
            subject_kind=raw_item["subject_kind"],
            authority_subject_id=raw_item["authority_subject_id"],
            current_engineering_type=raw_item["current_engineering_type"],
            current_target_representation=raw_item["current_target_representation"],
            candidates=tuple(candidates),
        )
        if item.content_fingerprint != raw_item["content_fingerprint"]:
            raise TargetModelFormulationError(
                "Persisted Target-Model review-item fingerprint is invalid."
            )
        items.append(item)

    review = create_formulation_review(
        project_id=payload["project_id"],
        review_id=payload["review_id"],
        source_internal_engineering_model_id=(
            payload["source_internal_engineering_model_id"]
        ),
        source_internal_engineering_model_fingerprint=(
            payload["source_internal_engineering_model_fingerprint"]
        ),
        final_model_review_decision_id=payload["final_model_review_decision_id"],
        final_model_review_decision_fingerprint=(
            payload["final_model_review_decision_fingerprint"]
        ),
        target_model_profile_id=payload["target_model_profile_id"],
        target_model_profile_version=payload["target_model_profile_version"],
        target_model_profile_fingerprint=(
            payload["target_model_profile_fingerprint"]
        ),
        target_notation_fingerprint=payload["target_notation_fingerprint"],
        items=tuple(items),
        created_at=payload["created_at"],
    )
    if review.schema_version != payload["schema_version"]:
        raise TargetModelFormulationError(
            "Persisted Target-Model Formulation review schema is invalid."
        )
    if review.content_fingerprint != payload["content_fingerprint"]:
        raise TargetModelFormulationError(
            "Persisted Target-Model Formulation review fingerprint is invalid."
        )
    return review
