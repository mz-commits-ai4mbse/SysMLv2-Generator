"""Strict deterministic JSON serialization for Final Model Review evidence."""

from __future__ import annotations

from dataclasses import asdict, replace
import json
from typing import Any

from .contracts import (
    FINAL_MODEL_REVIEW_SCHEMA_VERSION,
    create_evidence_reference,
    create_final_model_review_decision,
    create_final_model_review_item,
    create_final_model_review_manifest,
    create_final_model_review_revision,
    create_generated_unit_reference,
    validate_final_model_review_decision,
    validate_final_model_review_item,
    validate_final_model_review_manifest,
    validate_final_model_review_revision,
)
from .errors import FinalModelReviewIntegrityError, FinalModelReviewValidationError
from .fingerprints import calculate_json_fingerprint, validate_sha256_fingerprint
from .types import (
    FINAL_MODEL_REVIEW_STORED_FILE_ROLES,
    FinalModelReviewDecision,
    FinalModelReviewDecisionTargetSnapshot,
    FinalModelReviewItem,
    FinalModelReviewManifest,
    FinalModelReviewRevision,
    FinalModelReviewRevisionStorageManifest,
    FinalModelReviewStoredFileReference,
)

STORAGE_SCHEMA_VERSION = "1.0.0"


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise FinalModelReviewValidationError(f"duplicate JSON key: {key!r}.")
        result[key] = value
    return result


def _load(text: object, label: str) -> dict[str, object]:
    if not isinstance(text, str):
        raise FinalModelReviewValidationError(f"{label} JSON must be a string.")
    try:
        value = json.loads(text, object_pairs_hook=_pairs)
    except FinalModelReviewValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise FinalModelReviewValidationError(f"{label} contains invalid JSON.") from exc
    if not isinstance(value, dict):
        raise FinalModelReviewValidationError(f"{label} must be a JSON object.")
    return value


def _exact(data: dict[str, object], fields: set[str], label: str) -> None:
    actual = set(data)
    if actual != fields:
        raise FinalModelReviewValidationError(
            f"{label} has invalid fields; missing={sorted(fields-actual)}, unknown={sorted(actual-fields)}."
        )


def _same(stored: object, expected: str, label: str) -> None:
    validate_sha256_fingerprint(stored, label=f"{label} fingerprint")
    if stored != expected:
        raise FinalModelReviewIntegrityError(f"{label} fingerprint mismatch.")


def _identity(actual: str, expected: str | None, label: str) -> None:
    if expected is not None and actual != expected:
        raise FinalModelReviewIntegrityError(f"{label} does not match persistence path.")


def final_model_review_manifest_to_json(value: FinalModelReviewManifest) -> str:
    validate_final_model_review_manifest(value)
    return _dump(asdict(value))


def final_model_review_manifest_from_json(text, *, expected_project_id=None, expected_review_id=None):
    data = _load(text, "Final Model Review manifest")
    _exact(data, {"schema_version","project_id","final_model_review_id","created_at","content_fingerprint"}, "Final Model Review manifest")
    if data["schema_version"] != FINAL_MODEL_REVIEW_SCHEMA_VERSION:
        raise FinalModelReviewValidationError("unsupported Final Model Review manifest schema_version.")
    value = create_final_model_review_manifest(
        project_id=data["project_id"], final_model_review_id=data["final_model_review_id"], created_at=data["created_at"]
    )
    _same(data["content_fingerprint"], value.content_fingerprint, "Final Model Review manifest")
    _identity(value.project_id, expected_project_id, "manifest project_id")
    _identity(value.final_model_review_id, expected_review_id, "manifest review ID")
    return value


def _evidence(values: object):
    if not isinstance(values, list):
        raise FinalModelReviewValidationError("evidence_references must be a JSON array.")
    return tuple(
        create_evidence_reference(
            evidence_type=item["evidence_type"],
            reference_id=item["reference_id"],
            content_fingerprint=item["content_fingerprint"],
        )
        for item in values
    )


def final_model_review_revision_to_json(value: FinalModelReviewRevision) -> str:
    validate_final_model_review_revision(value)
    return _dump(asdict(value))


def final_model_review_revision_from_json(text, *, expected_project_id=None, expected_review_id=None, expected_revision_id=None):
    data = _load(text, "Final Model Review revision")
    fields = {"schema_version","project_id","final_model_review_id","final_model_review_revision_id","predecessor_revision_id","source_internal_engineering_model_id","generated_artifact_set_fingerprint","validation_result_fingerprint","validation_status","publication_gate","generated_units","evidence_references","review_subject_fingerprint","created_at","content_fingerprint"}
    _exact(data, fields, "Final Model Review revision")
    if data["schema_version"] != FINAL_MODEL_REVIEW_SCHEMA_VERSION:
        raise FinalModelReviewValidationError("unsupported Final Model Review revision schema_version.")
    if not isinstance(data["generated_units"], list):
        raise FinalModelReviewValidationError("generated_units must be a JSON array.")
    units = tuple(
        create_generated_unit_reference(
            generated_unit_id=item["generated_unit_id"],
            relative_path=item["relative_path"],
            content_fingerprint=item["content_fingerprint"],
        ) for item in data["generated_units"]
    )
    value = create_final_model_review_revision(
        project_id=data["project_id"],
        final_model_review_id=data["final_model_review_id"],
        final_model_review_revision_id=data["final_model_review_revision_id"],
        predecessor_revision_id=data["predecessor_revision_id"],
        source_internal_engineering_model_id=data["source_internal_engineering_model_id"],
        generated_artifact_set_fingerprint=data["generated_artifact_set_fingerprint"],
        validation_result_fingerprint=data["validation_result_fingerprint"],
        validation_status=data["validation_status"],
        publication_gate=data["publication_gate"],
        generated_units=units,
        evidence_references=_evidence(data["evidence_references"]),
        created_at=data["created_at"],
    )
    _same(data["review_subject_fingerprint"], value.review_subject_fingerprint, "review subject")
    _same(data["content_fingerprint"], value.content_fingerprint, "Final Model Review revision")
    _identity(value.project_id, expected_project_id, "revision project_id")
    _identity(value.final_model_review_id, expected_review_id, "revision review ID")
    _identity(value.final_model_review_revision_id, expected_revision_id, "revision ID")
    return value


def final_model_review_item_to_json(value: FinalModelReviewItem) -> str:
    validate_final_model_review_item(value)
    return _dump(asdict(value))


def final_model_review_item_from_json(text, *, expected_project_id=None, expected_review_id=None, expected_revision_id=None, expected_item_id=None):
    data = _load(text, "Final Model Review item")
    fields = {"schema_version","project_id","final_model_review_id","final_model_review_revision_id","final_model_review_item_id","item_kind","summary","detail","mandatory","generated_unit_id","generated_symbol_id","evidence_references","content_fingerprint"}
    _exact(data, fields, "Final Model Review item")
    if data["schema_version"] != FINAL_MODEL_REVIEW_SCHEMA_VERSION:
        raise FinalModelReviewValidationError("unsupported Final Model Review item schema_version.")
    value = create_final_model_review_item(
        project_id=data["project_id"], final_model_review_id=data["final_model_review_id"],
        final_model_review_revision_id=data["final_model_review_revision_id"], final_model_review_item_id=data["final_model_review_item_id"],
        item_kind=data["item_kind"], summary=data["summary"], detail=data["detail"], mandatory=data["mandatory"],
        generated_unit_id=data["generated_unit_id"], generated_symbol_id=data["generated_symbol_id"], evidence_references=_evidence(data["evidence_references"])
    )
    _same(data["content_fingerprint"], value.content_fingerprint, "Final Model Review item")
    _identity(value.project_id, expected_project_id, "item project_id")
    _identity(value.final_model_review_id, expected_review_id, "item review ID")
    _identity(value.final_model_review_revision_id, expected_revision_id, "item revision ID")
    _identity(value.final_model_review_item_id, expected_item_id, "item ID")
    return value


def final_model_review_decision_to_json(value: FinalModelReviewDecision) -> str:
    validate_final_model_review_decision(value)
    return _dump(asdict(value))


def final_model_review_decision_from_json(text, *, expected_project_id=None, expected_review_id=None, expected_decision_id=None):
    data = _load(text, "Final Model Review decision")
    _exact(data, {"schema_version","project_id","final_model_review_decision_id","target","decision","reviewer_identity","rationale","reviewed_at","decision_fingerprint"}, "Final Model Review decision")
    if data["schema_version"] != FINAL_MODEL_REVIEW_SCHEMA_VERSION:
        raise FinalModelReviewValidationError("unsupported Final Model Review decision schema_version.")
    target = data["target"]
    if not isinstance(target, dict):
        raise FinalModelReviewValidationError("decision target must be a JSON object.")
    snapshot = FinalModelReviewDecisionTargetSnapshot(**target)
    value = create_final_model_review_decision(
        project_id=data["project_id"], final_model_review_decision_id=data["final_model_review_decision_id"],
        target=snapshot, decision=data["decision"], reviewer_identity=data["reviewer_identity"], rationale=data["rationale"], reviewed_at=data["reviewed_at"]
    )
    _same(data["decision_fingerprint"], value.decision_fingerprint, "Final Model Review decision")
    _identity(value.project_id, expected_project_id, "decision project_id")
    _identity(value.target.final_model_review_id, expected_review_id, "decision review ID")
    _identity(value.final_model_review_decision_id, expected_decision_id, "decision ID")
    return value


def create_revision_storage_manifest(*, project_id: str, final_model_review_id: str, final_model_review_revision_id: str, revision_content_fingerprint: str, files: tuple[FinalModelReviewStoredFileReference, ...]):
    if not isinstance(files, tuple) or not files:
        raise FinalModelReviewValidationError("stored files must be a non-empty tuple.")
    paths=[]; roles=[]
    for item in files:
        if item.role not in FINAL_MODEL_REVIEW_STORED_FILE_ROLES:
            raise FinalModelReviewValidationError("stored file role is invalid.")
        if not item.relative_path or item.relative_path.startswith("/") or "\\" in item.relative_path or any(p in {"",".",".."} for p in item.relative_path.split("/")):
            raise FinalModelReviewValidationError("stored file path is unsafe.")
        validate_sha256_fingerprint(item.content_fingerprint, label="stored file content_fingerprint")
        if item.role == "generated_sysml_unit" and item.source_generated_unit_id is None:
            raise FinalModelReviewValidationError("generated SysML stored file requires source_generated_unit_id.")
        if item.role != "generated_sysml_unit" and item.source_generated_unit_id is not None:
            raise FinalModelReviewValidationError("only generated SysML files may have source_generated_unit_id.")
        paths.append(item.relative_path); roles.append(item.role)
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise FinalModelReviewValidationError("stored files must be unique and canonically ordered.")
    for role in ("revision","artifact_set_snapshot","validation_result_snapshot"):
        if roles.count(role) != 1:
            raise FinalModelReviewValidationError(f"storage manifest requires exactly one {role} file.")
    if roles.count("generated_sysml_unit") < 1:
        raise FinalModelReviewValidationError("storage manifest requires generated SysML content.")
    provisional = FinalModelReviewRevisionStorageManifest(
        schema_version=STORAGE_SCHEMA_VERSION, project_id=project_id, final_model_review_id=final_model_review_id,
        final_model_review_revision_id=final_model_review_revision_id, revision_content_fingerprint=revision_content_fingerprint,
        files=files, content_fingerprint="0"*64
    )
    payload=asdict(provisional); payload.pop("content_fingerprint")
    return replace(provisional, content_fingerprint=calculate_json_fingerprint(payload))


def revision_storage_manifest_to_json(value: FinalModelReviewRevisionStorageManifest) -> str:
    expected=create_revision_storage_manifest(
        project_id=value.project_id, final_model_review_id=value.final_model_review_id,
        final_model_review_revision_id=value.final_model_review_revision_id, revision_content_fingerprint=value.revision_content_fingerprint, files=value.files
    )
    if expected.content_fingerprint != value.content_fingerprint:
        raise FinalModelReviewIntegrityError("storage manifest fingerprint mismatch.")
    return _dump(asdict(value))


def revision_storage_manifest_from_json(text, *, expected_project_id=None, expected_review_id=None, expected_revision_id=None):
    data=_load(text,"Final Model Review storage manifest")
    _exact(data, {"schema_version","project_id","final_model_review_id","final_model_review_revision_id","revision_content_fingerprint","files","content_fingerprint"}, "Final Model Review storage manifest")
    if data["schema_version"] != STORAGE_SCHEMA_VERSION:
        raise FinalModelReviewValidationError("unsupported Final Model Review storage-manifest schema_version.")
    if not isinstance(data["files"], list):
        raise FinalModelReviewValidationError("storage manifest files must be a JSON array.")
    files=tuple(FinalModelReviewStoredFileReference(**item) for item in data["files"])
    value=create_revision_storage_manifest(
        project_id=data["project_id"], final_model_review_id=data["final_model_review_id"], final_model_review_revision_id=data["final_model_review_revision_id"],
        revision_content_fingerprint=data["revision_content_fingerprint"], files=files
    )
    _same(data["content_fingerprint"],value.content_fingerprint,"storage manifest")
    _identity(value.project_id,expected_project_id,"storage project_id")
    _identity(value.final_model_review_id,expected_review_id,"storage review ID")
    _identity(value.final_model_review_revision_id,expected_revision_id,"storage revision ID")
    return value
