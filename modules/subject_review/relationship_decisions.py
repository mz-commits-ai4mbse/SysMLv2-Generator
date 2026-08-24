"""Persist Human decisions for R4c pre-model relationship hypotheses."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re

from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.identifiers import is_valid_project_id
from .types import RELATIONSHIP_REVIEW_OUTCOMES


SCHEMA_VERSION = "1.0.0"
DIRECTORY_NAME = "subject_review_relationship_decisions"

_DECISION_RE = re.compile(r"^SRD-([0-9]{6})$")
_REVIEW_DOCUMENT_RE = re.compile(r"^RVD-[0-9]{6}$")
_REVIEW_VERSION_RE = re.compile(r"^RVV-[0-9]{6}$")
_REVIEW_REVISION_RE = re.compile(r"^RVR-[0-9]{6}$")
_SUBJECT_RE = re.compile(r"^SUBJ-[0-9]{6}$")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)


@dataclass(frozen=True, slots=True)
class SubjectRelationshipDecisionRecord:
    schema_version: str
    project_id: str
    review_document_id: str
    review_document_version_id: str
    review_revision_id: str
    decision_id: str
    predecessor_decision_id: str | None
    subject_review_card_fingerprint: str
    source_subject_id: str
    relationship_kind: str
    target_subject_id: str
    outcome: str
    rationale: str | None
    reviewer_identity: str
    created_at: str
    content_fingerprint: str


def create_subject_relationship_decision_record(
    *,
    project_id: str,
    review_document_id: str,
    review_document_version_id: str,
    review_revision_id: str,
    decision_id: str,
    predecessor_decision_id: str | None,
    subject_review_card_fingerprint: str,
    source_subject_id: str,
    relationship_kind: str,
    target_subject_id: str,
    outcome: str,
    rationale: str | None,
    reviewer_identity: str,
    created_at: str,
) -> SubjectRelationshipDecisionRecord:
    provisional = SubjectRelationshipDecisionRecord(
        schema_version=SCHEMA_VERSION,
        project_id=project_id,
        review_document_id=review_document_id,
        review_document_version_id=review_document_version_id,
        review_revision_id=review_revision_id,
        decision_id=decision_id,
        predecessor_decision_id=predecessor_decision_id,
        subject_review_card_fingerprint=subject_review_card_fingerprint,
        source_subject_id=source_subject_id,
        relationship_kind=relationship_kind,
        target_subject_id=target_subject_id,
        outcome=outcome,
        rationale=rationale,
        reviewer_identity=reviewer_identity,
        created_at=created_at,
        content_fingerprint="0" * 64,
    )
    _validate(provisional, verify_fingerprint=False)
    return SubjectRelationshipDecisionRecord(
        **_body(provisional),
        content_fingerprint=_fingerprint(provisional),
    )


def subject_relationship_decision_to_json(
    value: SubjectRelationshipDecisionRecord,
) -> str:
    _validate(value, verify_fingerprint=True)
    return (
        json.dumps(
            {
                **_body(value),
                "content_fingerprint": value.content_fingerprint,
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )


def subject_relationship_decision_from_json(
    text: str,
) -> SubjectRelationshipDecisionRecord:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("Relationship decision JSON is invalid.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Relationship decision root must be an object.")
    expected = set(SubjectRelationshipDecisionRecord.__dataclass_fields__)
    if set(payload) != expected:
        raise ValueError("Relationship decision fields are invalid.")
    value = SubjectRelationshipDecisionRecord(**payload)
    _validate(value, verify_fingerprint=True)
    return value


class SubjectRelationshipDecisionRepository:
    """Append-only project-local relationship decision store."""

    def __init__(self, root: Path | str = Path("data/projects")) -> None:
        self.root = Path(root)
        self._workspace = ProjectWorkspace(root=self.root)

    def list_decisions(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> tuple[SubjectRelationshipDecisionRecord, ...]:
        self._workspace.load_project(project_id)
        root = self._version_root(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        if not root.exists():
            return ()
        if root.is_symlink() or not root.is_dir():
            raise ValueError("Relationship decision directory is unsafe.")

        result = []
        for path in sorted(root.glob("SRD-*.json")):
            if path.is_symlink() or not path.is_file():
                raise ValueError("Relationship decision entry is unsafe.")
            value = subject_relationship_decision_from_json(
                path.read_text(encoding="utf-8")
            )
            if (
                value.project_id != project_id
                or value.review_document_id != review_document_id
                or value.review_document_version_id
                != review_document_version_id
            ):
                raise ValueError(
                    "Relationship decision escaped selected Review authority."
                )
            result.append(value)

        return tuple(
            sorted(
                result,
                key=lambda item: _decision_sequence(item.decision_id),
            )
        )

    def latest_by_relationship(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> tuple[SubjectRelationshipDecisionRecord, ...]:
        latest = {}
        for item in self.list_decisions(
            project_id,
            review_document_id,
            review_document_version_id,
        ):
            latest[_relationship_key(item)] = item
        return tuple(latest[key] for key in sorted(latest))

    def next_decision_id(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> str:
        existing = self.list_decisions(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        next_sequence = (
            max(
                (_decision_sequence(item.decision_id) for item in existing),
                default=0,
            )
            + 1
        )
        if next_sequence > 999_999:
            raise ValueError("Relationship decision ID space exhausted.")
        return f"SRD-{next_sequence:06d}"

    def append(self, value: SubjectRelationshipDecisionRecord) -> None:
        _validate(value, verify_fingerprint=True)
        self._workspace.load_project(value.project_id)

        existing = self.list_decisions(
            value.project_id,
            value.review_document_id,
            value.review_document_version_id,
        )
        expected_id = f"SRD-{len(existing) + 1:06d}"
        if value.decision_id != expected_id:
            raise ValueError("Relationship decision ID is not next.")

        predecessors = [
            item
            for item in existing
            if _relationship_key(item) == _relationship_key(value)
        ]
        expected_predecessor = (
            predecessors[-1].decision_id if predecessors else None
        )
        if value.predecessor_decision_id != expected_predecessor:
            raise ValueError("Relationship decision predecessor is stale.")

        root = self._version_root(
            value.project_id,
            value.review_document_id,
            value.review_document_version_id,
        )
        root.mkdir(parents=True, exist_ok=True)
        if root.is_symlink():
            raise ValueError("Relationship decision directory is unsafe.")

        target = root / f"{value.decision_id}.json"
        temporary = root / f".{value.decision_id}.json.tmp"
        if target.exists() or target.is_symlink():
            raise ValueError("Relationship decision already exists.")
        if temporary.exists() or temporary.is_symlink():
            raise ValueError("Relationship decision temp path exists.")

        try:
            temporary.write_text(
                subject_relationship_decision_to_json(value),
                encoding="utf-8",
            )
            os.replace(temporary, target)
        finally:
            if temporary.exists() and temporary.is_file():
                temporary.unlink()

    def _version_root(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> Path:
        if not is_valid_project_id(project_id):
            raise ValueError("project_id is invalid.")
        document_id = _review_identifier(
            review_document_id,
            _REVIEW_DOCUMENT_RE,
            "review_document_id",
        )
        version_id = _review_identifier(
            review_document_version_id,
            _REVIEW_VERSION_RE,
            "review_document_version_id",
        )
        return (
            self.root
            / project_id
            / DIRECTORY_NAME
            / document_id
            / version_id
        )


def _relationship_key(value: SubjectRelationshipDecisionRecord):
    return (
        value.source_subject_id,
        value.relationship_kind,
        value.target_subject_id,
    )


def _review_identifier(
    value: object,
    pattern: re.Pattern[str],
    label: str,
) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise ValueError(f"{label} is invalid.")
    return value


def _decision_sequence(value: str) -> int:
    match = _DECISION_RE.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise ValueError("Relationship decision ID is invalid.")
    return int(match.group(1))


def _validate(
    value: SubjectRelationshipDecisionRecord,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(value, SubjectRelationshipDecisionRecord):
        raise ValueError("Invalid relationship decision type.")
    if value.schema_version != SCHEMA_VERSION:
        raise ValueError("Relationship decision schema is unsupported.")
    if not is_valid_project_id(value.project_id):
        raise ValueError("project_id is invalid.")
    _review_identifier(
        value.review_document_id,
        _REVIEW_DOCUMENT_RE,
        "review_document_id",
    )
    _review_identifier(
        value.review_document_version_id,
        _REVIEW_VERSION_RE,
        "review_document_version_id",
    )
    _review_identifier(
        value.review_revision_id,
        _REVIEW_REVISION_RE,
        "review_revision_id",
    )
    _decision_sequence(value.decision_id)
    if value.predecessor_decision_id is not None:
        _decision_sequence(value.predecessor_decision_id)
        if value.predecessor_decision_id == value.decision_id:
            raise ValueError("Decision cannot reference itself.")

    if (
        not isinstance(value.subject_review_card_fingerprint, str)
        or _SHA_RE.fullmatch(value.subject_review_card_fingerprint) is None
    ):
        raise ValueError("Review Card fingerprint is invalid.")

    for subject_id in (
        value.source_subject_id,
        value.target_subject_id,
    ):
        if (
            not isinstance(subject_id, str)
            or _SUBJECT_RE.fullmatch(subject_id) is None
        ):
            raise ValueError("Canonical Subject ID is invalid.")
    if value.source_subject_id == value.target_subject_id:
        raise ValueError("Self-directed relationship decision is invalid.")

    if (
        not isinstance(value.relationship_kind, str)
        or not value.relationship_kind.strip()
        or value.relationship_kind != value.relationship_kind.strip()
        or "\n" in value.relationship_kind
    ):
        raise ValueError("relationship_kind is invalid.")

    if value.outcome not in RELATIONSHIP_REVIEW_OUTCOMES:
        raise ValueError("Relationship decision outcome is invalid.")

    if value.rationale is not None and (
        not isinstance(value.rationale, str)
        or not value.rationale.strip()
        or value.rationale != value.rationale.strip()
    ):
        raise ValueError("Relationship rationale is invalid.")
    if value.outcome == "rejected" and value.rationale is None:
        raise ValueError("Rejected relationship requires rationale.")

    if (
        not isinstance(value.reviewer_identity, str)
        or not value.reviewer_identity.strip()
        or value.reviewer_identity != value.reviewer_identity.strip()
    ):
        raise ValueError("reviewer_identity is invalid.")
    if (
        not isinstance(value.created_at, str)
        or _UTC_RE.fullmatch(value.created_at) is None
    ):
        raise ValueError("created_at must be UTC.")

    if verify_fingerprint and (
        not isinstance(value.content_fingerprint, str)
        or _SHA_RE.fullmatch(value.content_fingerprint) is None
        or value.content_fingerprint != _fingerprint(value)
    ):
        raise ValueError("Relationship decision fingerprint mismatch.")


def _body(value: SubjectRelationshipDecisionRecord) -> dict:
    return {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "review_document_id": value.review_document_id,
        "review_document_version_id": value.review_document_version_id,
        "review_revision_id": value.review_revision_id,
        "decision_id": value.decision_id,
        "predecessor_decision_id": value.predecessor_decision_id,
        "subject_review_card_fingerprint": (
            value.subject_review_card_fingerprint
        ),
        "source_subject_id": value.source_subject_id,
        "relationship_kind": value.relationship_kind,
        "target_subject_id": value.target_subject_id,
        "outcome": value.outcome,
        "rationale": value.rationale,
        "reviewer_identity": value.reviewer_identity,
        "created_at": value.created_at,
    }


def _fingerprint(value: SubjectRelationshipDecisionRecord) -> str:
    canonical = json.dumps(
        _body(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
