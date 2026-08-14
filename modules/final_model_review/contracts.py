"""Strict constructors, validation and fingerprints for Final Model Review."""

from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import PurePosixPath
import re

from .errors import (
    FinalModelReviewIntegrityError,
    FinalModelReviewValidationError,
)
from .fingerprints import (
    calculate_json_fingerprint,
    validate_sha256_fingerprint,
)
from .identifiers import (
    validate_final_model_review_decision_id,
    validate_final_model_review_id,
    validate_final_model_review_item_id,
    validate_final_model_review_revision_id,
)
from .types import (
    FINAL_MODEL_REVIEW_DECISIONS,
    FINAL_MODEL_REVIEW_EVIDENCE_TYPES,
    FINAL_MODEL_REVIEW_ITEM_KINDS,
    FINAL_MODEL_REVIEW_PUBLICATION_GATES,
    FINAL_MODEL_REVIEW_VALIDATION_STATUSES,
    FinalModelGeneratedUnitReference,
    FinalModelReviewDecision,
    FinalModelReviewDecisionTargetSnapshot,
    FinalModelReviewEvidenceReference,
    FinalModelReviewItem,
    FinalModelReviewManifest,
    FinalModelReviewRevision,
)


FINAL_MODEL_REVIEW_SCHEMA_VERSION = "1.0.0"

_PROJECT_ID = re.compile(r"^[0-9]{6}$")
_IEM_ID = re.compile(r"^IEM-[0-9]{6}$")
_GSU_ID = re.compile(r"^GSU-[0-9]{6}$")
_GENERATED_SYMBOL = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_TIMESTAMP = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?Z$"
)

_VALID_STATUS_GATE_PAIRS = {
    ("valid", "passed"),
    ("invalid", "blocked"),
    ("incomplete", "blocked"),
}


def create_final_model_review_manifest(
    *,
    project_id: str,
    final_model_review_id: str,
    created_at: str,
) -> FinalModelReviewManifest:
    provisional = FinalModelReviewManifest(
        schema_version=FINAL_MODEL_REVIEW_SCHEMA_VERSION,
        project_id=_project_id(project_id),
        final_model_review_id=validate_final_model_review_id(
            final_model_review_id
        ),
        created_at=_timestamp(created_at, "created_at"),
        content_fingerprint="0" * 64,
    )
    return replace(
        provisional,
        content_fingerprint=calculate_final_model_review_manifest_fingerprint(
            provisional
        ),
    )


def calculate_final_model_review_manifest_fingerprint(
    manifest: FinalModelReviewManifest,
) -> str:
    _validate_manifest(manifest, verify_fingerprint=False)
    payload = asdict(manifest)
    payload.pop("content_fingerprint")
    return calculate_json_fingerprint(payload)


def validate_final_model_review_manifest(
    manifest: FinalModelReviewManifest,
) -> None:
    _validate_manifest(manifest, verify_fingerprint=True)


def create_generated_unit_reference(
    *,
    generated_unit_id: str,
    relative_path: str,
    content_fingerprint: str,
) -> FinalModelGeneratedUnitReference:
    return FinalModelGeneratedUnitReference(
        generated_unit_id=_generated_unit_id(generated_unit_id),
        relative_path=_safe_relative_path(relative_path),
        content_fingerprint=validate_sha256_fingerprint(
            content_fingerprint,
            label="generated unit content_fingerprint",
        ),
    )


def create_evidence_reference(
    *,
    evidence_type: str,
    reference_id: str,
    content_fingerprint: str,
) -> FinalModelReviewEvidenceReference:
    return FinalModelReviewEvidenceReference(
        evidence_type=_choice(
            evidence_type,
            FINAL_MODEL_REVIEW_EVIDENCE_TYPES,
            "evidence_type",
        ),
        reference_id=_text(reference_id, "reference_id"),
        content_fingerprint=validate_sha256_fingerprint(
            content_fingerprint,
            label="evidence content_fingerprint",
        ),
    )


def calculate_review_subject_fingerprint(
    *,
    project_id: str,
    source_internal_engineering_model_id: str,
    generated_artifact_set_fingerprint: str,
    validation_result_fingerprint: str,
    validation_status: str,
    publication_gate: str,
    generated_units: tuple[FinalModelGeneratedUnitReference, ...],
    evidence_references: tuple[FinalModelReviewEvidenceReference, ...],
) -> str:
    validated_units = _generated_units(generated_units)
    validated_evidence = _evidence_references(evidence_references)
    status = _choice(
        validation_status,
        FINAL_MODEL_REVIEW_VALIDATION_STATUSES,
        "validation_status",
    )
    gate = _choice(
        publication_gate,
        FINAL_MODEL_REVIEW_PUBLICATION_GATES,
        "publication_gate",
    )
    _status_gate(status, gate)
    payload = {
        "project_id": _project_id(project_id),
        "source_internal_engineering_model_id": _iem_id(
            source_internal_engineering_model_id
        ),
        "generated_artifact_set_fingerprint": validate_sha256_fingerprint(
            generated_artifact_set_fingerprint,
            label="generated_artifact_set_fingerprint",
        ),
        "validation_result_fingerprint": validate_sha256_fingerprint(
            validation_result_fingerprint,
            label="validation_result_fingerprint",
        ),
        "validation_status": status,
        "publication_gate": gate,
        "generated_units": [asdict(item) for item in validated_units],
        "evidence_references": [
            asdict(item) for item in validated_evidence
        ],
    }
    return calculate_json_fingerprint(payload)


def create_final_model_review_revision(
    *,
    project_id: str,
    final_model_review_id: str,
    final_model_review_revision_id: str,
    predecessor_revision_id: str | None,
    source_internal_engineering_model_id: str,
    generated_artifact_set_fingerprint: str,
    validation_result_fingerprint: str,
    validation_status: str,
    publication_gate: str,
    generated_units: tuple[FinalModelGeneratedUnitReference, ...],
    evidence_references: tuple[FinalModelReviewEvidenceReference, ...] = (),
    created_at: str,
) -> FinalModelReviewRevision:
    review_id = validate_final_model_review_id(final_model_review_id)
    revision_id = validate_final_model_review_revision_id(
        final_model_review_revision_id
    )
    predecessor = (
        None
        if predecessor_revision_id is None
        else validate_final_model_review_revision_id(predecessor_revision_id)
    )
    if predecessor == revision_id:
        raise FinalModelReviewValidationError(
            "predecessor_revision_id must not equal the current revision ID."
        )
    units = _generated_units(generated_units)
    evidence = _evidence_references(evidence_references)
    status = _choice(
        validation_status,
        FINAL_MODEL_REVIEW_VALIDATION_STATUSES,
        "validation_status",
    )
    gate = _choice(
        publication_gate,
        FINAL_MODEL_REVIEW_PUBLICATION_GATES,
        "publication_gate",
    )
    _status_gate(status, gate)
    subject_fingerprint = calculate_review_subject_fingerprint(
        project_id=project_id,
        source_internal_engineering_model_id=(
            source_internal_engineering_model_id
        ),
        generated_artifact_set_fingerprint=(
            generated_artifact_set_fingerprint
        ),
        validation_result_fingerprint=validation_result_fingerprint,
        validation_status=status,
        publication_gate=gate,
        generated_units=units,
        evidence_references=evidence,
    )
    provisional = FinalModelReviewRevision(
        schema_version=FINAL_MODEL_REVIEW_SCHEMA_VERSION,
        project_id=_project_id(project_id),
        final_model_review_id=review_id,
        final_model_review_revision_id=revision_id,
        predecessor_revision_id=predecessor,
        source_internal_engineering_model_id=_iem_id(
            source_internal_engineering_model_id
        ),
        generated_artifact_set_fingerprint=validate_sha256_fingerprint(
            generated_artifact_set_fingerprint,
            label="generated_artifact_set_fingerprint",
        ),
        validation_result_fingerprint=validate_sha256_fingerprint(
            validation_result_fingerprint,
            label="validation_result_fingerprint",
        ),
        validation_status=status,
        publication_gate=gate,
        generated_units=units,
        evidence_references=evidence,
        review_subject_fingerprint=subject_fingerprint,
        created_at=_timestamp(created_at, "created_at"),
        content_fingerprint="0" * 64,
    )
    return replace(
        provisional,
        content_fingerprint=calculate_final_model_review_revision_fingerprint(
            provisional
        ),
    )


def calculate_final_model_review_revision_fingerprint(
    revision: FinalModelReviewRevision,
) -> str:
    _validate_revision(revision, verify_fingerprint=False)
    payload = asdict(revision)
    payload.pop("content_fingerprint")
    return calculate_json_fingerprint(payload)


def validate_final_model_review_revision(
    revision: FinalModelReviewRevision,
) -> None:
    _validate_revision(revision, verify_fingerprint=True)


def create_final_model_review_item(
    *,
    project_id: str,
    final_model_review_id: str,
    final_model_review_revision_id: str,
    final_model_review_item_id: str,
    item_kind: str,
    summary: str,
    detail: str | None,
    mandatory: bool,
    generated_unit_id: str | None = None,
    generated_symbol_id: str | None = None,
    evidence_references: tuple[FinalModelReviewEvidenceReference, ...] = (),
) -> FinalModelReviewItem:
    if generated_symbol_id is not None and generated_unit_id is None:
        raise FinalModelReviewValidationError(
            "generated_symbol_id requires generated_unit_id."
        )
    provisional = FinalModelReviewItem(
        schema_version=FINAL_MODEL_REVIEW_SCHEMA_VERSION,
        project_id=_project_id(project_id),
        final_model_review_id=validate_final_model_review_id(
            final_model_review_id
        ),
        final_model_review_revision_id=(
            validate_final_model_review_revision_id(
                final_model_review_revision_id
            )
        ),
        final_model_review_item_id=validate_final_model_review_item_id(
            final_model_review_item_id
        ),
        item_kind=_choice(
            item_kind,
            FINAL_MODEL_REVIEW_ITEM_KINDS,
            "item_kind",
        ),
        summary=_text(summary, "summary"),
        detail=_optional_text(detail, "detail"),
        mandatory=_bool(mandatory, "mandatory"),
        generated_unit_id=(
            None
            if generated_unit_id is None
            else _generated_unit_id(generated_unit_id)
        ),
        generated_symbol_id=(
            None
            if generated_symbol_id is None
            else _generated_symbol(generated_symbol_id)
        ),
        evidence_references=_evidence_references(evidence_references),
        content_fingerprint="0" * 64,
    )
    return replace(
        provisional,
        content_fingerprint=calculate_final_model_review_item_fingerprint(
            provisional
        ),
    )


def calculate_final_model_review_item_fingerprint(
    item: FinalModelReviewItem,
) -> str:
    _validate_item(item, verify_fingerprint=False)
    payload = asdict(item)
    payload.pop("content_fingerprint")
    return calculate_json_fingerprint(payload)


def validate_final_model_review_item(item: FinalModelReviewItem) -> None:
    _validate_item(item, verify_fingerprint=True)


def create_final_model_review_decision_target(
    revision: FinalModelReviewRevision,
) -> FinalModelReviewDecisionTargetSnapshot:
    validate_final_model_review_revision(revision)
    return FinalModelReviewDecisionTargetSnapshot(
        final_model_review_id=revision.final_model_review_id,
        final_model_review_revision_id=(
            revision.final_model_review_revision_id
        ),
        revision_content_fingerprint=revision.content_fingerprint,
        review_subject_fingerprint=revision.review_subject_fingerprint,
        generated_artifact_set_fingerprint=(
            revision.generated_artifact_set_fingerprint
        ),
        validation_result_fingerprint=(
            revision.validation_result_fingerprint
        ),
        validation_status=revision.validation_status,
        publication_gate=revision.publication_gate,
    )


def create_final_model_review_decision(
    *,
    project_id: str,
    final_model_review_decision_id: str,
    target: FinalModelReviewDecisionTargetSnapshot,
    decision: str,
    reviewer_identity: str,
    rationale: str | None,
    reviewed_at: str,
) -> FinalModelReviewDecision:
    validated_target = _decision_target(target)
    selected = _choice(
        decision,
        FINAL_MODEL_REVIEW_DECISIONS,
        "decision",
    )
    if (
        selected == "approved_for_publication"
        and (
            validated_target.validation_status != "valid"
            or validated_target.publication_gate != "passed"
        )
    ):
        raise FinalModelReviewValidationError(
            "approved_for_publication requires validation_status=valid "
            "and publication_gate=passed."
        )
    provisional = FinalModelReviewDecision(
        schema_version=FINAL_MODEL_REVIEW_SCHEMA_VERSION,
        project_id=_project_id(project_id),
        final_model_review_decision_id=(
            validate_final_model_review_decision_id(
                final_model_review_decision_id
            )
        ),
        target=validated_target,
        decision=selected,
        reviewer_identity=_text(
            reviewer_identity,
            "reviewer_identity",
        ),
        rationale=_optional_text(rationale, "rationale"),
        reviewed_at=_timestamp(reviewed_at, "reviewed_at"),
        decision_fingerprint="0" * 64,
    )
    return replace(
        provisional,
        decision_fingerprint=(
            calculate_final_model_review_decision_fingerprint(
                provisional
            )
        ),
    )


def calculate_final_model_review_decision_fingerprint(
    decision: FinalModelReviewDecision,
) -> str:
    _validate_decision(decision, verify_fingerprint=False)
    payload = asdict(decision)
    payload.pop("final_model_review_decision_id")
    payload.pop("reviewed_at")
    payload.pop("decision_fingerprint")
    return calculate_json_fingerprint(payload)


def validate_final_model_review_decision(
    decision: FinalModelReviewDecision,
) -> None:
    _validate_decision(decision, verify_fingerprint=True)


def _validate_manifest(
    manifest: FinalModelReviewManifest,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(manifest, FinalModelReviewManifest):
        raise FinalModelReviewValidationError(
            "manifest must be a FinalModelReviewManifest."
        )
    _schema(manifest.schema_version)
    _project_id(manifest.project_id)
    validate_final_model_review_id(manifest.final_model_review_id)
    _timestamp(manifest.created_at, "created_at")
    validate_sha256_fingerprint(
        manifest.content_fingerprint,
        label="content_fingerprint",
    )
    if verify_fingerprint:
        expected = calculate_final_model_review_manifest_fingerprint(
            replace(manifest, content_fingerprint="0" * 64)
        )
        if manifest.content_fingerprint != expected:
            raise FinalModelReviewIntegrityError(
                "Final Model Review manifest fingerprint mismatch."
            )


def _validate_revision(
    revision: FinalModelReviewRevision,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(revision, FinalModelReviewRevision):
        raise FinalModelReviewValidationError(
            "revision must be a FinalModelReviewRevision."
        )
    _schema(revision.schema_version)
    _project_id(revision.project_id)
    validate_final_model_review_id(revision.final_model_review_id)
    validate_final_model_review_revision_id(
        revision.final_model_review_revision_id
    )
    if revision.predecessor_revision_id is not None:
        validate_final_model_review_revision_id(
            revision.predecessor_revision_id
        )
        if (
            revision.predecessor_revision_id
            == revision.final_model_review_revision_id
        ):
            raise FinalModelReviewValidationError(
                "predecessor_revision_id must not equal the current revision ID."
            )
    _iem_id(revision.source_internal_engineering_model_id)
    validate_sha256_fingerprint(
        revision.generated_artifact_set_fingerprint,
        label="generated_artifact_set_fingerprint",
    )
    validate_sha256_fingerprint(
        revision.validation_result_fingerprint,
        label="validation_result_fingerprint",
    )
    status = _choice(
        revision.validation_status,
        FINAL_MODEL_REVIEW_VALIDATION_STATUSES,
        "validation_status",
    )
    gate = _choice(
        revision.publication_gate,
        FINAL_MODEL_REVIEW_PUBLICATION_GATES,
        "publication_gate",
    )
    _status_gate(status, gate)
    units = _generated_units(revision.generated_units)
    evidence = _evidence_references(revision.evidence_references)
    expected_subject = calculate_review_subject_fingerprint(
        project_id=revision.project_id,
        source_internal_engineering_model_id=(
            revision.source_internal_engineering_model_id
        ),
        generated_artifact_set_fingerprint=(
            revision.generated_artifact_set_fingerprint
        ),
        validation_result_fingerprint=(
            revision.validation_result_fingerprint
        ),
        validation_status=status,
        publication_gate=gate,
        generated_units=units,
        evidence_references=evidence,
    )
    validate_sha256_fingerprint(
        revision.review_subject_fingerprint,
        label="review_subject_fingerprint",
    )
    if revision.review_subject_fingerprint != expected_subject:
        raise FinalModelReviewIntegrityError(
            "Final Model Review subject fingerprint mismatch."
        )
    _timestamp(revision.created_at, "created_at")
    validate_sha256_fingerprint(
        revision.content_fingerprint,
        label="content_fingerprint",
    )
    if verify_fingerprint:
        expected = calculate_final_model_review_revision_fingerprint(
            replace(revision, content_fingerprint="0" * 64)
        )
        if revision.content_fingerprint != expected:
            raise FinalModelReviewIntegrityError(
                "Final Model Review revision fingerprint mismatch."
            )


def _validate_item(
    item: FinalModelReviewItem,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(item, FinalModelReviewItem):
        raise FinalModelReviewValidationError(
            "item must be a FinalModelReviewItem."
        )
    _schema(item.schema_version)
    _project_id(item.project_id)
    validate_final_model_review_id(item.final_model_review_id)
    validate_final_model_review_revision_id(
        item.final_model_review_revision_id
    )
    validate_final_model_review_item_id(item.final_model_review_item_id)
    _choice(item.item_kind, FINAL_MODEL_REVIEW_ITEM_KINDS, "item_kind")
    _text(item.summary, "summary")
    _optional_text(item.detail, "detail")
    _bool(item.mandatory, "mandatory")
    if item.generated_unit_id is not None:
        _generated_unit_id(item.generated_unit_id)
    if item.generated_symbol_id is not None:
        if item.generated_unit_id is None:
            raise FinalModelReviewValidationError(
                "generated_symbol_id requires generated_unit_id."
            )
        _generated_symbol(item.generated_symbol_id)
    _evidence_references(item.evidence_references)
    validate_sha256_fingerprint(
        item.content_fingerprint,
        label="content_fingerprint",
    )
    if verify_fingerprint:
        expected = calculate_final_model_review_item_fingerprint(
            replace(item, content_fingerprint="0" * 64)
        )
        if item.content_fingerprint != expected:
            raise FinalModelReviewIntegrityError(
                "Final Model Review item fingerprint mismatch."
            )


def _validate_decision(
    decision: FinalModelReviewDecision,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(decision, FinalModelReviewDecision):
        raise FinalModelReviewValidationError(
            "decision must be a FinalModelReviewDecision."
        )
    _schema(decision.schema_version)
    _project_id(decision.project_id)
    validate_final_model_review_decision_id(
        decision.final_model_review_decision_id
    )
    target = _decision_target(decision.target)
    selected = _choice(
        decision.decision,
        FINAL_MODEL_REVIEW_DECISIONS,
        "decision",
    )
    if (
        selected == "approved_for_publication"
        and (
            target.validation_status != "valid"
            or target.publication_gate != "passed"
        )
    ):
        raise FinalModelReviewValidationError(
            "approved_for_publication requires validation_status=valid "
            "and publication_gate=passed."
        )
    _text(decision.reviewer_identity, "reviewer_identity")
    _optional_text(decision.rationale, "rationale")
    _timestamp(decision.reviewed_at, "reviewed_at")
    validate_sha256_fingerprint(
        decision.decision_fingerprint,
        label="decision_fingerprint",
    )
    if verify_fingerprint:
        expected = calculate_final_model_review_decision_fingerprint(
            replace(decision, decision_fingerprint="0" * 64)
        )
        if decision.decision_fingerprint != expected:
            raise FinalModelReviewIntegrityError(
                "Final Model Review decision fingerprint mismatch."
            )


def _decision_target(
    target: FinalModelReviewDecisionTargetSnapshot,
) -> FinalModelReviewDecisionTargetSnapshot:
    if not isinstance(target, FinalModelReviewDecisionTargetSnapshot):
        raise FinalModelReviewValidationError(
            "target must be a FinalModelReviewDecisionTargetSnapshot."
        )
    validate_final_model_review_id(target.final_model_review_id)
    validate_final_model_review_revision_id(
        target.final_model_review_revision_id
    )
    validate_sha256_fingerprint(
        target.revision_content_fingerprint,
        label="revision_content_fingerprint",
    )
    validate_sha256_fingerprint(
        target.review_subject_fingerprint,
        label="review_subject_fingerprint",
    )
    validate_sha256_fingerprint(
        target.generated_artifact_set_fingerprint,
        label="generated_artifact_set_fingerprint",
    )
    validate_sha256_fingerprint(
        target.validation_result_fingerprint,
        label="validation_result_fingerprint",
    )
    status = _choice(
        target.validation_status,
        FINAL_MODEL_REVIEW_VALIDATION_STATUSES,
        "validation_status",
    )
    gate = _choice(
        target.publication_gate,
        FINAL_MODEL_REVIEW_PUBLICATION_GATES,
        "publication_gate",
    )
    _status_gate(status, gate)
    return target


def _generated_units(
    value: tuple[FinalModelGeneratedUnitReference, ...],
) -> tuple[FinalModelGeneratedUnitReference, ...]:
    if not isinstance(value, tuple) or not value:
        raise FinalModelReviewValidationError(
            "generated_units must be a non-empty tuple."
        )
    ids: list[str] = []
    paths: list[str] = []
    for item in value:
        if not isinstance(item, FinalModelGeneratedUnitReference):
            raise FinalModelReviewValidationError(
                "generated_units must contain FinalModelGeneratedUnitReference values."
            )
        ids.append(_generated_unit_id(item.generated_unit_id))
        paths.append(_safe_relative_path(item.relative_path))
        validate_sha256_fingerprint(
            item.content_fingerprint,
            label="generated unit content_fingerprint",
        )
    if len(ids) != len(set(ids)):
        raise FinalModelReviewValidationError(
            "generated_units must not contain duplicate unit IDs."
        )
    if len(paths) != len(set(paths)):
        raise FinalModelReviewValidationError(
            "generated_units must not contain duplicate relative paths."
        )
    if tuple(ids) != tuple(sorted(ids)):
        raise FinalModelReviewValidationError(
            "generated_units must be ordered by generated_unit_id."
        )
    return value


def _evidence_references(
    value: tuple[FinalModelReviewEvidenceReference, ...],
) -> tuple[FinalModelReviewEvidenceReference, ...]:
    if not isinstance(value, tuple):
        raise FinalModelReviewValidationError(
            "evidence_references must be a tuple."
        )
    keys: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, FinalModelReviewEvidenceReference):
            raise FinalModelReviewValidationError(
                "evidence_references must contain FinalModelReviewEvidenceReference values."
            )
        evidence_type = _choice(
            item.evidence_type,
            FINAL_MODEL_REVIEW_EVIDENCE_TYPES,
            "evidence_type",
        )
        reference_id = _text(item.reference_id, "reference_id")
        validate_sha256_fingerprint(
            item.content_fingerprint,
            label="evidence content_fingerprint",
        )
        keys.append((evidence_type, reference_id))
    if len(keys) != len(set(keys)):
        raise FinalModelReviewValidationError(
            "evidence_references must not contain duplicate type/reference pairs."
        )
    if tuple(keys) != tuple(sorted(keys)):
        raise FinalModelReviewValidationError(
            "evidence_references must use canonical type/reference ordering."
        )
    return value


def _schema(value: object) -> str:
    if value != FINAL_MODEL_REVIEW_SCHEMA_VERSION:
        raise FinalModelReviewValidationError(
            "unsupported Final Model Review schema_version."
        )
    return value


def _project_id(value: object) -> str:
    if not isinstance(value, str) or _PROJECT_ID.fullmatch(value) is None:
        raise FinalModelReviewValidationError(
            "project_id must be a string containing exactly six digits."
        )
    return value


def _iem_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or _IEM_ID.fullmatch(value) is None
        or value == "IEM-000000"
    ):
        raise FinalModelReviewValidationError(
            "source_internal_engineering_model_id must match "
            "^IEM-[0-9]{6}$ with sequence 000001..999999."
        )
    return value


def _generated_unit_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or _GSU_ID.fullmatch(value) is None
        or value == "GSU-000000"
    ):
        raise FinalModelReviewValidationError(
            "generated_unit_id must match ^GSU-[0-9]{6}$ "
            "with sequence 000001..999999."
        )
    return value


def _generated_symbol(value: object) -> str:
    if (
        not isinstance(value, str)
        or _GENERATED_SYMBOL.fullmatch(value) is None
    ):
        raise FinalModelReviewValidationError(
            "generated_symbol_id must be a machine-safe generated symbol."
        )
    return value


def _safe_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise FinalModelReviewValidationError(
            "relative_path must be a non-empty string."
        )
    if "\\" in value:
        raise FinalModelReviewValidationError(
            "relative_path must use POSIX separators."
        )
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise FinalModelReviewValidationError(
            "relative_path must be a safe project-relative POSIX path."
        )
    normalized = path.as_posix()
    if normalized != value:
        raise FinalModelReviewValidationError(
            "relative_path must already be normalized."
        )
    return value


def _status_gate(status: str, gate: str) -> None:
    if (status, gate) not in _VALID_STATUS_GATE_PAIRS:
        raise FinalModelReviewValidationError(
            "validation_status/publication_gate combination is invalid."
        )


def _choice(
    value: object,
    allowed: tuple[str, ...],
    label: str,
) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise FinalModelReviewValidationError(
            f"{label} must be one of {allowed}."
        )
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FinalModelReviewValidationError(
            f"{label} must be a non-empty string."
        )
    if value != value.strip():
        raise FinalModelReviewValidationError(
            f"{label} must not contain surrounding whitespace."
        )
    return value


def _optional_text(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _text(value, label)


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise FinalModelReviewValidationError(
            f"{label} must be a boolean."
        )
    return value


def _timestamp(value: object, label: str) -> str:
    if not isinstance(value, str) or _TIMESTAMP.fullmatch(value) is None:
        raise FinalModelReviewValidationError(
            f"{label} must be an ISO-8601 UTC timestamp ending in Z."
        )
    return value
