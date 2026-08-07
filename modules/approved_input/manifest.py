"""Create and serialize immutable Approved Input manifests."""

from __future__ import annotations

from dataclasses import asdict, fields, replace
import hashlib
import json
import re
from typing import Any

from modules.human_review.identifiers import (
    is_valid_human_review_decision_id,
)
from modules.project_processing.errors import (
    ProcessingValidationError,
)
from modules.project_processing.event_manifest import (
    validate_processing_artifact_reference,
)
from modules.project_processing.identifiers import (
    is_valid_processing_attempt_id,
    is_valid_processing_run_id,
)
from modules.project_processing.types import (
    ProcessingArtifactReference,
)
from modules.project_sources.errors import SourceManifestError
from modules.project_sources.identifiers import validate_source_id
from modules.project_workspace.identifiers import is_valid_project_id
from modules.review_workspace.identifiers import (
    is_valid_review_document_id,
    is_valid_review_document_version_id,
    is_valid_review_item_id,
    is_valid_review_revision_id,
)

from .errors import (
    ApprovedInputIntegrityError,
    ApprovedInputValidationError,
)
from .identifiers import validate_approved_input_id
from .types import (
    APPROVED_INPUT_AUTHORITY_STATES,
    APPROVED_INPUT_KINDS,
    INITIAL_APPROVED_INPUT_AUTHORITY_STATE,
    ApprovedInputCanonicalContent,
    ApprovedInputManifest,
    ApprovedInputRelationshipProperty,
    ApprovedInputRelationshipRepresentation,
)


APPROVED_INPUT_MANIFEST_SCHEMA_VERSION = "1.0.0"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_STABLE_SUBJECT_KEY_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9._:-]{0,239}$"
)
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_MANIFEST_FIELDS = frozenset(
    field.name for field in fields(ApprovedInputManifest)
)
_CANONICAL_CONTENT_FIELDS = frozenset(
    field.name for field in fields(ApprovedInputCanonicalContent)
)
_RELATIONSHIP_FIELDS = frozenset(
    field.name
    for field in fields(ApprovedInputRelationshipRepresentation)
)
_RELATIONSHIP_PROPERTY_FIELDS = frozenset(
    field.name
    for field in fields(ApprovedInputRelationshipProperty)
)
_ARTIFACT_REFERENCE_FIELDS = frozenset(
    field.name for field in fields(ProcessingArtifactReference)
)

_REVIEW_ITEM_KIND_BY_APPROVED_INPUT_KIND = {
    "element_statement": "element",
    "relationship_statement": "relationship",
    "human_clarification": "open_question",
}


def create_approved_input_manifest(
    *,
    project_id: str,
    approved_input_id: str,
    approved_input_kind: str,
    canonical_content: ApprovedInputCanonicalContent,
    selected_classification: str | None,
    selected_framework_assignment: str | None,
    selected_terminology_assignment: str | None,
    selected_source_assignments: tuple[str, ...],
    selected_relationship_representation: (
        ApprovedInputRelationshipRepresentation | None
    ),
    stable_subject_key: str,
    review_document_id: str,
    review_document_version_id: str,
    review_revision_id: str,
    review_item_id: str,
    review_item_kind: str,
    review_item_fingerprint: str,
    finalized_artifact_set_fingerprint: str,
    finalization_decision_id: str,
    finalization_decision_fingerprint: str,
    finalization_validation_fingerprint: str,
    source_id: str,
    source_sha256: str,
    processing_run_id: str,
    attempt_id: str,
    primary_artifact_reference: ProcessingArtifactReference,
    supporting_artifact_references: tuple[
        ProcessingArtifactReference,
        ...,
    ],
    proposal_references: tuple[str, ...],
    created_at: str,
) -> ApprovedInputManifest:
    """Create one deterministic immutable Approved Input manifest."""

    relationship = _normalize_relationship(
        selected_relationship_representation
    )

    provisional = ApprovedInputManifest(
        schema_version=APPROVED_INPUT_MANIFEST_SCHEMA_VERSION,
        project_id=project_id,
        approved_input_id=approved_input_id,
        approved_input_kind=approved_input_kind,
        authority_state=INITIAL_APPROVED_INPUT_AUTHORITY_STATE,
        canonical_content=canonical_content,
        selected_classification=selected_classification,
        selected_framework_assignment=selected_framework_assignment,
        selected_terminology_assignment=(
            selected_terminology_assignment
        ),
        selected_source_assignments=tuple(
            sorted(selected_source_assignments)
        ),
        selected_relationship_representation=relationship,
        stable_subject_key=stable_subject_key,
        review_document_id=review_document_id,
        review_document_version_id=review_document_version_id,
        review_revision_id=review_revision_id,
        review_item_id=review_item_id,
        review_item_kind=review_item_kind,
        review_item_fingerprint=review_item_fingerprint,
        finalized_artifact_set_fingerprint=(
            finalized_artifact_set_fingerprint
        ),
        finalization_decision_id=finalization_decision_id,
        finalization_decision_fingerprint=(
            finalization_decision_fingerprint
        ),
        finalization_validation_fingerprint=(
            finalization_validation_fingerprint
        ),
        source_id=source_id,
        source_sha256=source_sha256,
        processing_run_id=processing_run_id,
        attempt_id=attempt_id,
        primary_artifact_reference=primary_artifact_reference,
        supporting_artifact_references=tuple(
            sorted(
                supporting_artifact_references,
                key=_artifact_reference_sort_key,
            )
        ),
        proposal_references=tuple(sorted(proposal_references)),
        created_at=created_at,
        content_fingerprint="0" * 64,
    )

    manifest = replace(
        provisional,
        content_fingerprint=(
            calculate_approved_input_manifest_fingerprint(
                provisional
            )
        ),
    )

    validate_approved_input_manifest(manifest)
    return manifest


def parse_approved_input_manifest(
    payload: object,
) -> ApprovedInputManifest:
    """Parse and validate one strict Approved Input mapping."""

    data = _exact_object(
        payload,
        expected_fields=_MANIFEST_FIELDS,
        label="Approved Input Manifest",
    )

    source_assignments = data["selected_source_assignments"]
    supporting_references = data[
        "supporting_artifact_references"
    ]
    proposal_references = data["proposal_references"]

    if not isinstance(source_assignments, list):
        raise ApprovedInputValidationError(
            "selected_source_assignments must be a JSON array."
        )
    if not isinstance(supporting_references, list):
        raise ApprovedInputValidationError(
            "supporting_artifact_references must be a JSON array."
        )
    if not isinstance(proposal_references, list):
        raise ApprovedInputValidationError(
            "proposal_references must be a JSON array."
        )

    relationship_payload = data[
        "selected_relationship_representation"
    ]

    manifest = ApprovedInputManifest(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        approved_input_id=data["approved_input_id"],
        approved_input_kind=data["approved_input_kind"],
        authority_state=data["authority_state"],
        canonical_content=_parse_canonical_content(
            data["canonical_content"]
        ),
        selected_classification=data[
            "selected_classification"
        ],
        selected_framework_assignment=data[
            "selected_framework_assignment"
        ],
        selected_terminology_assignment=data[
            "selected_terminology_assignment"
        ],
        selected_source_assignments=tuple(source_assignments),
        selected_relationship_representation=(
            None
            if relationship_payload is None
            else _parse_relationship(relationship_payload)
        ),
        stable_subject_key=data["stable_subject_key"],
        review_document_id=data["review_document_id"],
        review_document_version_id=data[
            "review_document_version_id"
        ],
        review_revision_id=data["review_revision_id"],
        review_item_id=data["review_item_id"],
        review_item_kind=data["review_item_kind"],
        review_item_fingerprint=data["review_item_fingerprint"],
        finalized_artifact_set_fingerprint=data[
            "finalized_artifact_set_fingerprint"
        ],
        finalization_decision_id=data[
            "finalization_decision_id"
        ],
        finalization_decision_fingerprint=data[
            "finalization_decision_fingerprint"
        ],
        finalization_validation_fingerprint=data[
            "finalization_validation_fingerprint"
        ],
        source_id=data["source_id"],
        source_sha256=data["source_sha256"],
        processing_run_id=data["processing_run_id"],
        attempt_id=data["attempt_id"],
        primary_artifact_reference=_parse_artifact_reference(
            data["primary_artifact_reference"]
        ),
        supporting_artifact_references=tuple(
            _parse_artifact_reference(reference)
            for reference in supporting_references
        ),
        proposal_references=tuple(proposal_references),
        created_at=data["created_at"],
        content_fingerprint=data["content_fingerprint"],
    )

    validate_approved_input_manifest(manifest)
    return manifest


def approved_input_manifest_from_json(
    text: object,
) -> ApprovedInputManifest:
    """Parse one Approved Input manifest from strict JSON."""

    if not isinstance(text, str):
        raise ApprovedInputValidationError(
            "Approved Input Manifest JSON must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except ApprovedInputValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ApprovedInputValidationError(
            "Approved Input Manifest is not valid JSON."
        ) from exc

    return parse_approved_input_manifest(payload)


def approved_input_manifest_to_dict(
    manifest: ApprovedInputManifest,
) -> dict[str, object]:
    """Serialize one validated Approved Input manifest."""

    validate_approved_input_manifest(manifest)
    return _manifest_payload(manifest, include_fingerprint=True)


def approved_input_manifest_to_json(
    manifest: ApprovedInputManifest,
) -> str:
    """Serialize one Approved Input manifest deterministically."""

    return (
        json.dumps(
            approved_input_manifest_to_dict(manifest),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def calculate_approved_input_manifest_fingerprint(
    manifest: ApprovedInputManifest,
) -> str:
    """Calculate the deterministic Approved Input fingerprint."""

    _validate_manifest(manifest, verify_fingerprint=False)

    canonical_json = json.dumps(
        _manifest_payload(manifest, include_fingerprint=False),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()


def validate_approved_input_manifest(
    manifest: ApprovedInputManifest,
) -> None:
    """Validate one complete Approved Input manifest."""

    _validate_manifest(manifest, verify_fingerprint=True)


def _validate_manifest(
    manifest: ApprovedInputManifest,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(manifest, ApprovedInputManifest):
        raise ApprovedInputValidationError(
            "manifest must be an ApprovedInputManifest."
        )

    if (
        manifest.schema_version
        != APPROVED_INPUT_MANIFEST_SCHEMA_VERSION
    ):
        raise ApprovedInputValidationError(
            "Invalid Approved Input Manifest schema_version."
        )

    if not is_valid_project_id(manifest.project_id):
        raise ApprovedInputValidationError(
            "project_id must be a valid six-digit Project ID."
        )

    validate_approved_input_id(manifest.approved_input_id)

    if manifest.approved_input_kind not in APPROVED_INPUT_KINDS:
        raise ApprovedInputValidationError(
            "approved_input_kind is invalid."
        )

    if manifest.authority_state not in APPROVED_INPUT_AUTHORITY_STATES:
        raise ApprovedInputValidationError(
            "authority_state is invalid."
        )

    if (
        manifest.authority_state
        != INITIAL_APPROVED_INPUT_AUTHORITY_STATE
    ):
        raise ApprovedInputValidationError(
            "An immutable Approved Input Manifest must record "
            "its initial authority_state as active."
        )

    _validate_canonical_content(manifest.canonical_content)

    _validate_optional_text(
        manifest.selected_classification,
        label="selected_classification",
    )
    _validate_optional_text(
        manifest.selected_framework_assignment,
        label="selected_framework_assignment",
    )
    _validate_optional_text(
        manifest.selected_terminology_assignment,
        label="selected_terminology_assignment",
    )
    _validate_sorted_unique_strings(
        manifest.selected_source_assignments,
        label="selected_source_assignments",
    )
    _validate_stable_subject_key(manifest.stable_subject_key)

    if not is_valid_review_document_id(manifest.review_document_id):
        raise ApprovedInputValidationError(
            "review_document_id is invalid."
        )
    if not is_valid_review_document_version_id(
        manifest.review_document_version_id
    ):
        raise ApprovedInputValidationError(
            "review_document_version_id is invalid."
        )
    if not is_valid_review_revision_id(manifest.review_revision_id):
        raise ApprovedInputValidationError(
            "review_revision_id is invalid."
        )
    if not is_valid_review_item_id(manifest.review_item_id):
        raise ApprovedInputValidationError(
            "review_item_id is invalid."
        )

    expected_review_item_kind = (
        _REVIEW_ITEM_KIND_BY_APPROVED_INPUT_KIND[
            manifest.approved_input_kind
        ]
    )
    if manifest.review_item_kind != expected_review_item_kind:
        raise ApprovedInputValidationError(
            "review_item_kind does not match approved_input_kind."
        )

    _validate_sha256(
        manifest.review_item_fingerprint,
        label="review_item_fingerprint",
    )
    _validate_sha256(
        manifest.finalized_artifact_set_fingerprint,
        label="finalized_artifact_set_fingerprint",
    )

    if not is_valid_human_review_decision_id(
        manifest.finalization_decision_id
    ):
        raise ApprovedInputValidationError(
            "finalization_decision_id is invalid."
        )

    _validate_sha256(
        manifest.finalization_decision_fingerprint,
        label="finalization_decision_fingerprint",
    )
    _validate_sha256(
        manifest.finalization_validation_fingerprint,
        label="finalization_validation_fingerprint",
    )

    try:
        validate_source_id(manifest.source_id)
    except SourceManifestError as exc:
        raise ApprovedInputValidationError(
            "source_id is invalid."
        ) from exc

    _validate_sha256(manifest.source_sha256, label="source_sha256")

    if not is_valid_processing_run_id(manifest.processing_run_id):
        raise ApprovedInputValidationError(
            "processing_run_id is invalid."
        )
    if not is_valid_processing_attempt_id(manifest.attempt_id):
        raise ApprovedInputValidationError(
            "attempt_id is invalid."
        )

    _validate_artifact_reference(
        manifest.primary_artifact_reference,
        label="primary_artifact_reference",
    )

    if not isinstance(manifest.supporting_artifact_references, tuple):
        raise ApprovedInputValidationError(
            "supporting_artifact_references must be a tuple."
        )

    for reference in manifest.supporting_artifact_references:
        _validate_artifact_reference(
            reference,
            label="supporting_artifact_reference",
        )

    supporting_keys = tuple(
        _artifact_reference_sort_key(reference)
        for reference in manifest.supporting_artifact_references
    )
    if supporting_keys != tuple(sorted(supporting_keys)):
        raise ApprovedInputValidationError(
            "supporting_artifact_references must use "
            "deterministic order."
        )
    if len(supporting_keys) != len(set(supporting_keys)):
        raise ApprovedInputValidationError(
            "supporting_artifact_references must be unique."
        )
    if _artifact_reference_sort_key(
        manifest.primary_artifact_reference
    ) in set(supporting_keys):
        raise ApprovedInputValidationError(
            "primary_artifact_reference must not be repeated "
            "as a supporting reference."
        )

    _validate_sorted_unique_strings(
        manifest.proposal_references,
        label="proposal_references",
    )
    _validate_relationship_contract(manifest)
    _validate_utc_timestamp(manifest.created_at, label="created_at")

    if verify_fingerprint:
        _validate_sha256(
            manifest.content_fingerprint,
            label="content_fingerprint",
        )
        expected_fingerprint = (
            calculate_approved_input_manifest_fingerprint(manifest)
        )
        if manifest.content_fingerprint != expected_fingerprint:
            raise ApprovedInputIntegrityError(
                "content_fingerprint does not match "
                "Approved Input Manifest content."
            )


def _validate_relationship_contract(
    manifest: ApprovedInputManifest,
) -> None:
    relationship = manifest.selected_relationship_representation

    if manifest.approved_input_kind == "relationship_statement":
        if relationship is None:
            raise ApprovedInputValidationError(
                "relationship_statement requires one "
                "selected_relationship_representation."
            )
        _validate_relationship(relationship)
        return

    if relationship is not None:
        raise ApprovedInputValidationError(
            "selected_relationship_representation is permitted "
            "only for relationship_statement."
        )


def _validate_canonical_content(
    content: ApprovedInputCanonicalContent,
) -> None:
    if not isinstance(content, ApprovedInputCanonicalContent):
        raise ApprovedInputValidationError(
            "canonical_content must be ApprovedInputCanonicalContent."
        )

    _validate_required_text(content.title, label="canonical_content.title")
    _validate_required_text(
        content.primary_text,
        label="canonical_content.primary_text",
    )
    _validate_optional_text(
        content.description,
        label="canonical_content.description",
    )
    _validate_optional_text(
        content.information_type,
        label="canonical_content.information_type",
    )
    _validate_optional_text(
        content.modality,
        label="canonical_content.modality",
    )
    _validate_optional_text(
        content.epistemic_status,
        label="canonical_content.epistemic_status",
    )


def _validate_relationship(
    relationship: ApprovedInputRelationshipRepresentation,
) -> None:
    if not isinstance(
        relationship,
        ApprovedInputRelationshipRepresentation,
    ):
        raise ApprovedInputValidationError(
            "selected_relationship_representation has invalid type."
        )

    _validate_stable_subject_key(relationship.source_subject_key)
    _validate_stable_subject_key(relationship.target_subject_key)
    _validate_required_text(
        relationship.semantic_intent,
        label="relationship.semantic_intent",
    )
    _validate_required_text(
        relationship.sysml_v2_construct,
        label="relationship.sysml_v2_construct",
    )

    if not isinstance(relationship.construct_properties, tuple):
        raise ApprovedInputValidationError(
            "relationship.construct_properties must be a tuple."
        )

    property_keys: list[tuple[str, str]] = []
    for property_ in relationship.construct_properties:
        if not isinstance(
            property_,
            ApprovedInputRelationshipProperty,
        ):
            raise ApprovedInputValidationError(
                "relationship construct property has invalid type."
            )
        _validate_required_text(
            property_.name,
            label="relationship property name",
        )
        _validate_required_text(
            property_.value,
            label="relationship property value",
        )
        property_keys.append((property_.name, property_.value))

    property_key_tuple = tuple(property_keys)
    if property_key_tuple != tuple(sorted(property_key_tuple)):
        raise ApprovedInputValidationError(
            "relationship.construct_properties must use "
            "deterministic order."
        )
    if len(property_key_tuple) != len(set(property_key_tuple)):
        raise ApprovedInputValidationError(
            "relationship.construct_properties must be unique."
        )

    _validate_required_text(
        relationship.target_notation_profile_id,
        label="relationship.target_notation_profile_id",
    )
    _validate_required_text(
        relationship.target_notation_profile_version,
        label="relationship.target_notation_profile_version",
    )
    _validate_required_text(
        relationship.textual_notation_preview,
        label="relationship.textual_notation_preview",
    )

    if relationship.profile_validation_status != "valid":
        raise ApprovedInputValidationError(
            "Approved relationship representation must have "
            "profile_validation_status valid."
        )

    _validate_sha256(
        relationship.profile_validation_fingerprint,
        label="relationship.profile_validation_fingerprint",
    )


def _normalize_relationship(
    relationship: ApprovedInputRelationshipRepresentation | None,
) -> ApprovedInputRelationshipRepresentation | None:
    if relationship is None:
        return None
    if not isinstance(
        relationship,
        ApprovedInputRelationshipRepresentation,
    ):
        return relationship

    return replace(
        relationship,
        construct_properties=tuple(
            sorted(
                relationship.construct_properties,
                key=lambda property_: (
                    property_.name,
                    property_.value,
                ),
            )
        ),
    )


def _validate_artifact_reference(
    reference: ProcessingArtifactReference,
    *,
    label: str,
) -> None:
    try:
        validate_processing_artifact_reference(reference)
    except ProcessingValidationError as exc:
        raise ApprovedInputValidationError(
            f"{label} is invalid."
        ) from exc


def _artifact_reference_sort_key(
    reference: ProcessingArtifactReference,
) -> tuple[str, str, str, str]:
    return (
        reference.artifact_type,
        reference.artifact_id,
        reference.content_fingerprint,
        reference.repository_relative_path,
    )


def _validate_sorted_unique_strings(
    values: object,
    *,
    label: str,
) -> None:
    if not isinstance(values, tuple):
        raise ApprovedInputValidationError(
            f"{label} must be a tuple."
        )

    for value in values:
        _validate_required_text(value, label=f"{label} entry")

    if values != tuple(sorted(values)):
        raise ApprovedInputValidationError(
            f"{label} must use deterministic order."
        )
    if len(values) != len(set(values)):
        raise ApprovedInputValidationError(
            f"{label} must contain unique values."
        )


def _validate_required_text(value: object, *, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ApprovedInputValidationError(
            f"{label} must be a non-empty string."
        )


def _validate_optional_text(value: object, *, label: str) -> None:
    if value is None:
        return
    _validate_required_text(value, label=label)


def _validate_stable_subject_key(value: object) -> None:
    if (
        not isinstance(value, str)
        or _STABLE_SUBJECT_KEY_PATTERN.fullmatch(value) is None
    ):
        raise ApprovedInputValidationError(
            "stable subject key must match "
            "^[a-z0-9][a-z0-9._:-]{0,239}$."
        )


def _validate_sha256(value: object, *, label: str) -> None:
    if (
        not isinstance(value, str)
        or _SHA256_PATTERN.fullmatch(value) is None
    ):
        raise ApprovedInputValidationError(
            f"{label} must be a lowercase SHA-256 hex digest."
        )


def _validate_utc_timestamp(value: object, *, label: str) -> None:
    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None
    ):
        raise ApprovedInputValidationError(
            f"{label} must be a UTC timestamp ending in Z."
        )


def _manifest_payload(
    manifest: ApprovedInputManifest,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    payload = _json_compatible(asdict(manifest))
    if not include_fingerprint:
        payload.pop("content_fingerprint")
    return payload


def _json_compatible(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _json_compatible(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_json_compatible(item) for item in value]
    if isinstance(value, list):
        return [_json_compatible(item) for item in value]
    return value


def _parse_canonical_content(
    payload: object,
) -> ApprovedInputCanonicalContent:
    data = _exact_object(
        payload,
        expected_fields=_CANONICAL_CONTENT_FIELDS,
        label="canonical_content",
    )
    return ApprovedInputCanonicalContent(
        title=data["title"],
        primary_text=data["primary_text"],
        description=data["description"],
        information_type=data["information_type"],
        modality=data["modality"],
        epistemic_status=data["epistemic_status"],
    )


def _parse_relationship(
    payload: object,
) -> ApprovedInputRelationshipRepresentation:
    data = _exact_object(
        payload,
        expected_fields=_RELATIONSHIP_FIELDS,
        label="selected_relationship_representation",
    )

    properties = data["construct_properties"]
    if not isinstance(properties, list):
        raise ApprovedInputValidationError(
            "construct_properties must be a JSON array."
        )

    return ApprovedInputRelationshipRepresentation(
        source_subject_key=data["source_subject_key"],
        target_subject_key=data["target_subject_key"],
        semantic_intent=data["semantic_intent"],
        sysml_v2_construct=data["sysml_v2_construct"],
        construct_properties=tuple(
            _parse_relationship_property(property_)
            for property_ in properties
        ),
        target_notation_profile_id=data[
            "target_notation_profile_id"
        ],
        target_notation_profile_version=data[
            "target_notation_profile_version"
        ],
        textual_notation_preview=data[
            "textual_notation_preview"
        ],
        profile_validation_status=data[
            "profile_validation_status"
        ],
        profile_validation_fingerprint=data[
            "profile_validation_fingerprint"
        ],
    )


def _parse_relationship_property(
    payload: object,
) -> ApprovedInputRelationshipProperty:
    data = _exact_object(
        payload,
        expected_fields=_RELATIONSHIP_PROPERTY_FIELDS,
        label="relationship property",
    )
    return ApprovedInputRelationshipProperty(
        name=data["name"],
        value=data["value"],
    )


def _parse_artifact_reference(
    payload: object,
) -> ProcessingArtifactReference:
    data = _exact_object(
        payload,
        expected_fields=_ARTIFACT_REFERENCE_FIELDS,
        label="Processing Artifact Reference",
    )
    return ProcessingArtifactReference(
        artifact_type=data["artifact_type"],
        artifact_id=data["artifact_id"],
        content_fingerprint=data["content_fingerprint"],
        repository_relative_path=data["repository_relative_path"],
    )


def _exact_object(
    payload: object,
    *,
    expected_fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ApprovedInputValidationError(
            f"{label} must be a JSON object."
        )

    actual_fields = frozenset(payload)
    if actual_fields != expected_fields:
        missing = sorted(expected_fields - actual_fields)
        unexpected = sorted(actual_fields - expected_fields)
        raise ApprovedInputValidationError(
            f"{label} fields do not match contract; "
            f"missing={missing}, unexpected={unexpected}."
        )

    return payload


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ApprovedInputValidationError(
                f"Duplicate JSON key: {key!r}."
            )
        result[key] = value
    return result
