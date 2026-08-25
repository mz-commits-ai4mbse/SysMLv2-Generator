"""Human Final Model Review over one exact Model Assembly Draft."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import uuid

from modules.model_placement.errors import ModelPlacementContractError


MODEL_ASSEMBLY_FINAL_REVIEW_SCHEMA_VERSION = "1.0.0"
MODEL_ASSEMBLY_FINAL_REVIEW_DECISIONS = frozenset(
    {"approved", "changes_requested"}
)
_FINAL_DECISION_ID = re.compile(r"^FAD-[0-9]{6}$")


@dataclass(frozen=True, slots=True)
class FinalModelRelationshipResolution:
    relationship_decision_id: str
    selected_rule_id: str
    resolution_source: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelAssemblyFinalReviewDecision:
    schema_version: str
    project_id: str
    final_assembly_decision_id: str
    comparison_fingerprint: str
    assembly_draft_fingerprint: str
    approved_placement_set_fingerprint: str
    approved_engineering_information_fingerprint: str
    decision: str
    relationship_resolutions: tuple[
        FinalModelRelationshipResolution, ...
    ]
    reviewer_identity: str
    rationale: str | None
    reviewed_at: str
    decision_fingerprint: str


def build_final_model_review_options(*, draft, profile):
    """Return exact Human-selectable target rules per assembled Relationship."""

    all_rules = tuple(
        sorted(
            f"relationship:{item.semantic_intent}"
            for item in profile.relationship_semantics
        )
    )
    if not all_rules and draft.relationships:
        raise ModelPlacementContractError(
            "Final Model Review requires profile-controlled Relationship rules."
        )

    result = {}
    for relationship in draft.relationships:
        proposed = tuple(sorted(set(relationship.candidate_rule_ids)))
        if relationship.representation_status == "exact_profile_match":
            if len(proposed) != 1:
                raise ModelPlacementContractError(
                    "Exact Relationship representation must bind one rule."
                )
            options = proposed
        elif relationship.representation_status == "persona_unanimous_proposal":
            if len(proposed) != 1:
                raise ModelPlacementContractError(
                    "Unanimous Relationship proposal must bind one rule."
                )
            options = tuple(sorted(set((*proposed, *all_rules))))
        elif relationship.representation_status == "persona_variance":
            if len(proposed) < 2:
                raise ModelPlacementContractError(
                    "Relationship variance must preserve multiple alternatives."
                )
            options = tuple(sorted(set((*proposed, *all_rules))))
        elif relationship.representation_status == "unmapped":
            options = all_rules
        else:
            raise ModelPlacementContractError(
                "Unsupported Relationship representation status."
            )
        result[relationship.relationship_decision_id] = options
    return result


def create_final_model_review_decision(
    *,
    draft,
    profile,
    final_assembly_decision_id: str,
    decision: str,
    selected_relationship_rules: dict[str, str] | None,
    reviewer_identity: str,
    rationale: str | None = None,
    reviewed_at: str | None = None,
) -> ModelAssemblyFinalReviewDecision:
    """Create one immutable whole-model Human decision."""

    if decision not in MODEL_ASSEMBLY_FINAL_REVIEW_DECISIONS:
        raise ModelPlacementContractError(
            "Final Model Review decision is invalid."
        )
    if _FINAL_DECISION_ID.fullmatch(final_assembly_decision_id) is None:
        raise ModelPlacementContractError(
            "Final Model Review decision ID is invalid."
        )
    reviewer = reviewer_identity.strip()
    if not reviewer:
        raise ModelPlacementContractError(
            "Final Model Review requires reviewer identity."
        )
    rationale_value = (
        None if rationale is None or not rationale.strip()
        else rationale.strip()
    )
    if decision == "changes_requested" and rationale_value is None:
        raise ModelPlacementContractError(
            "Changes requested requires a Human rationale."
        )

    options = build_final_model_review_options(
        draft=draft,
        profile=profile,
    )
    selected = selected_relationship_rules or {}
    if decision == "changes_requested":
        resolutions = ()
    else:
        if set(selected) != set(options):
            raise ModelPlacementContractError(
                "Final approval requires one Human Relationship representation "
                "for every assembled Relationship."
            )
        resolutions_list = []
        attention_resolved = False
        by_id = {
            item.relationship_decision_id: item
            for item in draft.relationships
        }
        for relationship_id in sorted(options):
            selected_rule = selected[relationship_id]
            if selected_rule not in options[relationship_id]:
                raise ModelPlacementContractError(
                    "Final Model Review selected a Relationship rule outside "
                    "the pinned profile options."
                )
            relationship = by_id[relationship_id]
            if relationship.representation_status == "exact_profile_match":
                source = "exact_profile_match"
            elif (
                relationship.representation_status
                == "persona_unanimous_proposal"
                and selected_rule in relationship.candidate_rule_ids
            ):
                source = "human_confirmed_persona_proposal"
            else:
                source = "human_resolved_final_review"
                attention_resolved = True

            payload = {
                "relationship_decision_id": relationship_id,
                "selected_rule_id": selected_rule,
                "resolution_source": source,
            }
            resolutions_list.append(
                FinalModelRelationshipResolution(
                    **payload,
                    content_fingerprint=_fingerprint(payload),
                )
            )
        if attention_resolved and rationale_value is None:
            raise ModelPlacementContractError(
                "Resolving Relationship variance or unmapped representation "
                "requires a Human rationale."
            )
        resolutions = tuple(resolutions_list)

    timestamp = reviewed_at or _timestamp()
    body = {
        "schema_version": MODEL_ASSEMBLY_FINAL_REVIEW_SCHEMA_VERSION,
        "project_id": draft.project_id,
        "final_assembly_decision_id": final_assembly_decision_id,
        "comparison_fingerprint": draft.comparison_fingerprint,
        "assembly_draft_fingerprint": draft.content_fingerprint,
        "approved_placement_set_fingerprint": (
            draft.approved_placement_set_fingerprint
        ),
        "approved_engineering_information_fingerprint": (
            draft.approved_engineering_information_fingerprint
        ),
        "decision": decision,
        "relationship_resolutions": [
            _resolution_payload(item)
            for item in resolutions
        ],
        "reviewer_identity": reviewer,
        "rationale": rationale_value,
        "reviewed_at": timestamp,
    }
    return ModelAssemblyFinalReviewDecision(
        schema_version=MODEL_ASSEMBLY_FINAL_REVIEW_SCHEMA_VERSION,
        project_id=draft.project_id,
        final_assembly_decision_id=final_assembly_decision_id,
        comparison_fingerprint=draft.comparison_fingerprint,
        assembly_draft_fingerprint=draft.content_fingerprint,
        approved_placement_set_fingerprint=(
            draft.approved_placement_set_fingerprint
        ),
        approved_engineering_information_fingerprint=(
            draft.approved_engineering_information_fingerprint
        ),
        decision=decision,
        relationship_resolutions=resolutions,
        reviewer_identity=reviewer,
        rationale=rationale_value,
        reviewed_at=timestamp,
        decision_fingerprint=_fingerprint(body),
    )


def final_model_review_decision_to_json(value) -> str:
    payload = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "final_assembly_decision_id": value.final_assembly_decision_id,
        "comparison_fingerprint": value.comparison_fingerprint,
        "assembly_draft_fingerprint": value.assembly_draft_fingerprint,
        "approved_placement_set_fingerprint": (
            value.approved_placement_set_fingerprint
        ),
        "approved_engineering_information_fingerprint": (
            value.approved_engineering_information_fingerprint
        ),
        "decision": value.decision,
        "relationship_resolutions": [
            _resolution_payload(item)
            for item in value.relationship_resolutions
        ],
        "reviewer_identity": value.reviewer_identity,
        "rationale": value.rationale,
        "reviewed_at": value.reviewed_at,
        "decision_fingerprint": value.decision_fingerprint,
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def final_model_review_decision_from_json(text: str):
    try:
        payload = json.loads(text)
        resolutions = tuple(
            FinalModelRelationshipResolution(**item)
            for item in payload["relationship_resolutions"]
        )
        value = ModelAssemblyFinalReviewDecision(
            schema_version=payload["schema_version"],
            project_id=payload["project_id"],
            final_assembly_decision_id=(
                payload["final_assembly_decision_id"]
            ),
            comparison_fingerprint=payload["comparison_fingerprint"],
            assembly_draft_fingerprint=(
                payload["assembly_draft_fingerprint"]
            ),
            approved_placement_set_fingerprint=(
                payload["approved_placement_set_fingerprint"]
            ),
            approved_engineering_information_fingerprint=(
                payload[
                    "approved_engineering_information_fingerprint"
                ]
            ),
            decision=payload["decision"],
            relationship_resolutions=resolutions,
            reviewer_identity=payload["reviewer_identity"],
            rationale=payload["rationale"],
            reviewed_at=payload["reviewed_at"],
            decision_fingerprint=payload["decision_fingerprint"],
        )
    except Exception as exc:
        raise ModelPlacementContractError(
            "Final Model Review decision JSON violates the exact contract."
        ) from exc

    if value.schema_version != MODEL_ASSEMBLY_FINAL_REVIEW_SCHEMA_VERSION:
        raise ModelPlacementContractError(
            "Final Model Review decision schema version is unsupported."
        )
    if value.decision not in MODEL_ASSEMBLY_FINAL_REVIEW_DECISIONS:
        raise ModelPlacementContractError(
            "Final Model Review decision is invalid."
        )
    if _FINAL_DECISION_ID.fullmatch(value.final_assembly_decision_id) is None:
        raise ModelPlacementContractError(
            "Final Model Review decision ID is invalid."
        )

    body = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "final_assembly_decision_id": value.final_assembly_decision_id,
        "comparison_fingerprint": value.comparison_fingerprint,
        "assembly_draft_fingerprint": value.assembly_draft_fingerprint,
        "approved_placement_set_fingerprint": (
            value.approved_placement_set_fingerprint
        ),
        "approved_engineering_information_fingerprint": (
            value.approved_engineering_information_fingerprint
        ),
        "decision": value.decision,
        "relationship_resolutions": [
            _resolution_payload(item)
            for item in value.relationship_resolutions
        ],
        "reviewer_identity": value.reviewer_identity,
        "rationale": value.rationale,
        "reviewed_at": value.reviewed_at,
    }
    if _fingerprint(body) != value.decision_fingerprint:
        raise ModelPlacementContractError(
            "Final Model Review decision fingerprint is invalid."
        )
    for resolution in value.relationship_resolutions:
        check = {
            "relationship_decision_id": (
                resolution.relationship_decision_id
            ),
            "selected_rule_id": resolution.selected_rule_id,
            "resolution_source": resolution.resolution_source,
        }
        if _fingerprint(check) != resolution.content_fingerprint:
            raise ModelPlacementContractError(
                "Final Relationship resolution fingerprint is invalid."
            )
    return value


class ModelAssemblyFinalReviewRepository:
    """Immutable Final Model Review decisions bound to Assembly Drafts."""

    def __init__(
        self,
        root=Path("data/projects"),
        *,
        clock=None,
    ):
        self.root = Path(root)
        self._clock = clock

    def list_decisions(
        self,
        project_id: str,
        comparison_fingerprint: str,
    ):
        directory = self._decision_dir(
            project_id,
            comparison_fingerprint,
        )
        if not directory.exists():
            return ()
        if directory.is_symlink() or not directory.is_dir():
            raise ModelPlacementContractError(
                "Final Model Review decisions path is unsafe."
            )
        result = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if path.is_symlink() or not path.is_file():
                raise ModelPlacementContractError(
                    "Unexpected Final Model Review decision entry."
                )
            if not re.fullmatch(r"FAD-[0-9]{6}\.json", path.name):
                raise ModelPlacementContractError(
                    "Unexpected Final Model Review decision entry."
                )
            result.append(
                final_model_review_decision_from_json(
                    path.read_text(encoding="utf-8")
                )
            )
        return tuple(result)

    def latest_decision(
        self,
        project_id: str,
        comparison_fingerprint: str,
    ):
        decisions = self.list_decisions(
            project_id,
            comparison_fingerprint,
        )
        return None if not decisions else decisions[-1]

    def record(
        self,
        *,
        draft,
        profile,
        decision: str,
        selected_relationship_rules: dict[str, str] | None,
        reviewer_identity: str,
        rationale: str | None = None,
    ):
        existing = self.list_decisions(
            draft.project_id,
            draft.comparison_fingerprint,
        )
        if existing:
            raise ModelPlacementContractError(
                "Final Model Review already has an immutable decision for "
                "this exact Assembly Draft."
            )
        decision_id = "FAD-000001"
        value = create_final_model_review_decision(
            draft=draft,
            profile=profile,
            final_assembly_decision_id=decision_id,
            decision=decision,
            selected_relationship_rules=selected_relationship_rules,
            reviewer_identity=reviewer_identity,
            rationale=rationale,
            reviewed_at=self._now(),
        )
        directory = self._decision_dir(
            draft.project_id,
            draft.comparison_fingerprint,
        )
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{decision_id}.json"
        if path.exists() or path.is_symlink():
            raise ModelPlacementContractError(
                "Final Model Review decision path is occupied."
            )
        temp = directory / f".{decision_id}.tmp-{uuid.uuid4().hex}"
        temp.write_text(
            final_model_review_decision_to_json(value),
            encoding="utf-8",
        )
        temp.replace(path)
        loaded = self.latest_decision(
            draft.project_id,
            draft.comparison_fingerprint,
        )
        if loaded != value:
            raise ModelPlacementContractError(
                "Persisted Final Model Review decision differs from source."
            )
        return loaded

    def _decision_dir(
        self,
        project_id: str,
        comparison_fingerprint: str,
    ):
        return (
            self.root
            / project_id
            / "model_assemblies"
            / comparison_fingerprint
            / "final_review"
            / "decisions"
        )

    def _now(self):
        if self._clock is None:
            return _timestamp()
        value = self._clock()
        return value.astimezone(timezone.utc).isoformat().replace(
            "+00:00",
            "Z",
        )


def _resolution_payload(item):
    return {
        "relationship_decision_id": item.relationship_decision_id,
        "selected_rule_id": item.selected_rule_id,
        "resolution_source": item.resolution_source,
        "content_fingerprint": item.content_fingerprint,
    }


def _timestamp():
    return datetime.now(timezone.utc).isoformat().replace(
        "+00:00",
        "Z",
    )


def _fingerprint(payload):
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
