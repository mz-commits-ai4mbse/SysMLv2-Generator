"""Immutable persistence for SEM-015 model-quality Review 2."""

from __future__ import annotations

import json
from pathlib import Path
import re
import uuid

from .authority import (
    create_quality_authority_set,
    create_quality_decision,
    validate_quality_decision,
)
from .contract import bundle_to_json, request_to_json
from .errors import ModelQualityError
from .types import (
    ModelQualityAuthoritySet,
    ModelQualityDecision,
)


_REVIEW_FILE = re.compile(r"^MQR-[0-9]{6}$")
_DECISION_FILE = re.compile(r"^MQD-[0-9]{6}\.json$")
_AUTHORITY_FILE = re.compile(r"^MQA-[0-9]{6}\.json$")


class ModelQualityRepository:
    def __init__(self, root=Path("data/projects")) -> None:
        self.root = Path(root)

    def allocate_review_id(self, project_id: str) -> str:
        numbers = []
        directory = self._reviews_root(project_id)
        if directory.exists():
            for entry in directory.iterdir():
                if entry.is_symlink() or not entry.is_dir():
                    raise ModelQualityError(
                        "Unexpected model-quality review repository entry."
                    )
                if _REVIEW_FILE.fullmatch(entry.name) is None:
                    raise ModelQualityError(
                        "Unexpected model-quality review repository entry."
                    )
                numbers.append(int(entry.name.split("-")[1]))
        return f"MQR-{(max(numbers, default=0) + 1):06d}"

    def record_review(self, *, request, bundle):
        if (
            bundle.project_id != request.project_id
            or bundle.request_fingerprint != request.request_fingerprint
            or bundle.source_internal_engineering_model_id
            != request.source_internal_engineering_model_id
            or bundle.source_internal_engineering_model_fingerprint
            != request.source_internal_engineering_model_fingerprint
        ):
            raise ModelQualityError(
                "Model-quality review bundle does not bind its exact request."
            )
        directory = self._review_dir(request.project_id, bundle.review_id)
        if directory.exists() or directory.is_symlink():
            raise ModelQualityError(
                "Model-quality review is immutable and already exists."
            )
        temp = directory.parent / (
            f".{bundle.review_id}.tmp-{uuid.uuid4().hex}"
        )
        temp.mkdir(parents=True)
        (temp / "request.json").write_text(
            request_to_json(request),
            encoding="utf-8",
        )
        (temp / "bundle.json").write_text(
            bundle_to_json(bundle),
            encoding="utf-8",
        )
        temp.replace(directory)
        return directory

    def find_review_for_source(
        self,
        project_id: str,
        source_iem_id: str,
        source_iem_fingerprint: str,
        request_fingerprint: str,
    ):
        directory = self._reviews_root(project_id)
        if not directory.exists():
            return None
        matches = []
        for entry in sorted(directory.iterdir(), key=lambda item: item.name):
            if entry.is_symlink() or not entry.is_dir():
                raise ModelQualityError(
                    "Unexpected model-quality review repository entry."
                )
            bundle = self._load_bundle_json(entry / "bundle.json")
            if (
                bundle["source_internal_engineering_model_id"] == source_iem_id
                and bundle["source_internal_engineering_model_fingerprint"]
                == source_iem_fingerprint
                and bundle["request_fingerprint"] == request_fingerprint
            ):
                matches.append(bundle)
        if len(matches) > 1:
            raise ModelQualityError(
                "Multiple model-quality reviews bind the same exact request."
            )
        return None if not matches else matches[0]

    def raw_review(self, project_id: str, review_id: str) -> tuple[dict, dict]:
        directory = self._review_dir(project_id, review_id)
        return (
            self._load_json(directory / "request.json"),
            self._load_bundle_json(directory / "bundle.json"),
        )

    def record_decision(
        self,
        *,
        bundle,
        internal_model_element_id: str,
        decision: str,
        reviewer_identity: str,
        rationale: str,
        decided_at: str,
        approved_name: str | None = None,
        approved_description: str | None = None,
    ) -> ModelQualityDecision:
        latest = self.latest_decision_for_element(
            bundle.project_id,
            bundle.review_id,
            internal_model_element_id,
        )
        value = create_quality_decision(
            bundle=bundle,
            decision_id=self._next_decision_id(bundle.project_id),
            internal_model_element_id=internal_model_element_id,
            decision=decision,
            reviewer_identity=reviewer_identity,
            rationale=rationale,
            decided_at=decided_at,
            approved_name=approved_name,
            approved_description=approved_description,
            supersedes_decision_id=(
                None if latest is None else latest.decision_id
            ),
        )
        self._persist_decision(value)
        return value

    def list_decisions(self, project_id: str) -> tuple[ModelQualityDecision, ...]:
        directory = self._decisions_root(project_id)
        if not directory.exists():
            return ()
        result = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if path.is_symlink() or not path.is_file():
                raise ModelQualityError(
                    "Unexpected model-quality decision repository entry."
                )
            if _DECISION_FILE.fullmatch(path.name) is None:
                raise ModelQualityError(
                    "Unexpected model-quality decision repository entry."
                )
            result.append(_decision_from_payload(self._load_json(path)))
        return tuple(result)

    def effective_decisions(self, bundle) -> tuple[ModelQualityDecision, ...]:
        by_element = {}
        for decision in self.list_decisions(bundle.project_id):
            if decision.review_id != bundle.review_id:
                continue
            validate_quality_decision(bundle, decision)
            current = by_element.get(decision.internal_model_element_id)
            if current is None:
                if decision.supersedes_decision_id is not None:
                    raise ModelQualityError(
                        "First model-quality decision for an element cannot supersede another."
                    )
            else:
                if decision.supersedes_decision_id != current.decision_id:
                    raise ModelQualityError(
                        "Model-quality successor must supersede the current effective decision."
                    )
            by_element[decision.internal_model_element_id] = decision
        return tuple(
            by_element[item.internal_model_element_id]
            for item in bundle.proposals
            if item.internal_model_element_id in by_element
        )

    def latest_decision_for_element(
        self,
        project_id: str,
        review_id: str,
        element_id: str,
    ):
        values = tuple(
            item
            for item in self.list_decisions(project_id)
            if item.review_id == review_id
            and item.internal_model_element_id == element_id
        )
        return None if not values else values[-1]

    def finalize(
        self,
        *,
        bundle,
        created_at: str,
    ) -> ModelQualityAuthoritySet:
        effective = self.effective_decisions(bundle)
        authority = create_quality_authority_set(
            bundle=bundle,
            authority_set_id=self._next_authority_id(bundle.project_id),
            effective_decisions=effective,
            created_at=created_at,
        )
        path = (
            self._authority_root(bundle.project_id)
            / f"{authority.authority_set_id}.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() or path.is_symlink():
            raise ModelQualityError(
                "Model-quality authority-set path is occupied."
            )
        temp = path.parent / f".{path.name}.tmp-{uuid.uuid4().hex}"
        temp.write_text(
            json.dumps(
                _authority_payload(authority),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        temp.replace(path)
        return authority

    def latest_authority_set_for_review(
        self,
        project_id: str,
        review_id: str,
    ) -> dict | None:
        directory = self._authority_root(project_id)
        if not directory.exists():
            return None
        matches = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if path.is_symlink() or not path.is_file():
                raise ModelQualityError(
                    "Unexpected model-quality authority-set entry."
                )
            if _AUTHORITY_FILE.fullmatch(path.name) is None:
                raise ModelQualityError(
                    "Unexpected model-quality authority-set entry."
                )
            payload = self._load_json(path)
            if payload["review_id"] == review_id:
                matches.append(payload)
        return None if not matches else matches[-1]

    def _persist_decision(self, value):
        path = (
            self._decisions_root(value.project_id)
            / f"{value.decision_id}.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() or path.is_symlink():
            raise ModelQualityError(
                "Model-quality decision path is occupied."
            )
        temp = path.parent / f".{path.name}.tmp-{uuid.uuid4().hex}"
        temp.write_text(
            json.dumps(
                _decision_payload(value),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        temp.replace(path)

    def _next_decision_id(self, project_id):
        values = self.list_decisions(project_id)
        numbers = [
            int(item.decision_id.split("-")[1])
            for item in values
        ]
        return f"MQD-{(max(numbers, default=0) + 1):06d}"

    def _next_authority_id(self, project_id):
        directory = self._authority_root(project_id)
        numbers = []
        if directory.exists():
            for path in directory.iterdir():
                if path.is_symlink() or not path.is_file():
                    raise ModelQualityError(
                        "Unexpected model-quality authority-set entry."
                    )
                if _AUTHORITY_FILE.fullmatch(path.name) is None:
                    raise ModelQualityError(
                        "Unexpected model-quality authority-set entry."
                    )
                numbers.append(int(path.stem.split("-")[1]))
        return f"MQA-{(max(numbers, default=0) + 1):06d}"

    def _reviews_root(self, project_id):
        return self.root / project_id / "model_quality" / "reviews"

    def _review_dir(self, project_id, review_id):
        if _REVIEW_FILE.fullmatch(review_id) is None:
            raise ModelQualityError("Model-quality review ID is invalid.")
        return self._reviews_root(project_id) / review_id

    def _decisions_root(self, project_id):
        return self.root / project_id / "model_quality" / "decisions"

    def _authority_root(self, project_id):
        return self.root / project_id / "model_quality" / "authority_sets"

    @staticmethod
    def _load_json(path):
        if path.is_symlink() or not path.is_file():
            raise ModelQualityError("Model-quality repository artifact not found.")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ModelQualityError(
                "Model-quality repository artifact is invalid JSON."
            ) from exc

    def _load_bundle_json(self, path):
        payload = self._load_json(path)
        required = {
            "schema_version",
            "project_id",
            "review_id",
            "request_fingerprint",
            "source_internal_engineering_model_id",
            "source_internal_engineering_model_fingerprint",
            "quality_profile_id",
            "quality_profile_version",
            "quality_profile_fingerprint",
            "provider",
            "model",
            "proposals",
            "supporting_response_fingerprints",
            "generated_at",
            "content_fingerprint",
        }
        if set(payload) != required:
            raise ModelQualityError(
                "Persisted model-quality bundle violates exact schema."
            )
        return payload


def _decision_from_payload(payload):
    try:
        body = dict(payload)
        fingerprint = body.pop("content_fingerprint")
        canonical = json.dumps(
            body,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        import hashlib
        expected = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()
        if expected != fingerprint:
            raise ModelQualityError(
                "Persisted model-quality decision fingerprint is invalid."
            )
        return ModelQualityDecision(
            **body,
            content_fingerprint=fingerprint,
        )
    except Exception as exc:
        if isinstance(exc, ModelQualityError):
            raise
        raise ModelQualityError(
            "Persisted model-quality decision violates exact schema."
        ) from exc


def _decision_payload(item):
    return {
        "schema_version": item.schema_version,
        "project_id": item.project_id,
        "decision_id": item.decision_id,
        "review_id": item.review_id,
        "review_fingerprint": item.review_fingerprint,
        "internal_model_element_id": item.internal_model_element_id,
        "proposal_fingerprint": item.proposal_fingerprint,
        "decision": item.decision,
        "approved_name": item.approved_name,
        "approved_description": item.approved_description,
        "reviewer_identity": item.reviewer_identity,
        "rationale": item.rationale,
        "decided_at": item.decided_at,
        "supersedes_decision_id": item.supersedes_decision_id,
        "content_fingerprint": item.content_fingerprint,
    }


def _authority_payload(item):
    return {
        "schema_version": item.schema_version,
        "project_id": item.project_id,
        "authority_set_id": item.authority_set_id,
        "review_id": item.review_id,
        "review_fingerprint": item.review_fingerprint,
        "source_internal_engineering_model_id": (
            item.source_internal_engineering_model_id
        ),
        "source_internal_engineering_model_fingerprint": (
            item.source_internal_engineering_model_fingerprint
        ),
        "effective_decisions": [
            _decision_payload(value)
            for value in item.effective_decisions
        ],
        "created_at": item.created_at,
        "content_fingerprint": item.content_fingerprint,
    }
