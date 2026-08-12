"""Create, validate and serialize immutable Review Documents."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import hashlib
import json
from pathlib import PurePosixPath
import re
from typing import Any

from modules.project_processing import (
    ProcessingArtifactReference,
    ProcessingValidationError,
    SemanticReferenceVersion,
    create_processing_artifact_reference,
    create_semantic_reference_version,
    validate_processing_artifact_reference,
)
from modules.project_processing.identifiers import (
    validate_processing_attempt_id,
    validate_processing_run_id,
)
from modules.project_sources.errors import SourceManifestError
from modules.project_sources.identifiers import validate_source_id
from modules.project_workspace.identifiers import is_valid_project_id
from modules.project_workspace.types import FrameworkTemplateReference

from .errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from .identifiers import validate_review_document_id
from .types import ReviewDocument


REVIEW_DOCUMENT_SCHEMA_VERSION = "1.0.0"
REVIEW_DOCUMENT_MANIFEST_FILENAME = (
    "review_document_manifest.json"
)

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_FRAMEWORK_TEMPLATE_ID_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9_]*$"
)
_REFERENCE_SYSTEM_ID_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9_]*$"
)
_SEMANTIC_VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+$"
)
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_REVIEW_DOCUMENT_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "review_document_id",
        "source_id",
        "source_sha256",
        "processing_run_id",
        "attempt_id",
        "primary_review_artifact_reference",
        "supporting_artifact_references",
        "framework_template",
        "semantic_reference_versions",
        "created_at",
        "content_fingerprint",
    }
)

_ARTIFACT_REFERENCE_FIELDS = frozenset(
    {
        "artifact_type",
        "artifact_id",
        "content_fingerprint",
        "repository_relative_path",
    }
)

_FRAMEWORK_TEMPLATE_FIELDS = frozenset(
    {
        "template_id",
        "template_version",
    }
)

_SEMANTIC_REFERENCE_FIELDS = frozenset(
    {
        "reference_system_id",
        "reference_version",
    }
)


def create_review_document(
    *,
    project_id: str,
    review_document_id: str,
    source_id: str,
    source_sha256: str,
    processing_run_id: str,
    attempt_id: str,
    primary_review_artifact_reference: (
        ProcessingArtifactReference
    ),
    supporting_artifact_references: tuple[
        ProcessingArtifactReference,
        ...,
    ],
    framework_template: FrameworkTemplateReference,
    semantic_reference_versions: tuple[
        SemanticReferenceVersion,
        ...,
    ],
    timestamp: str,
) -> ReviewDocument:
    """Create one fingerprinted immutable Review Document."""

    provisional = ReviewDocument(
        schema_version=REVIEW_DOCUMENT_SCHEMA_VERSION,
        project_id=project_id,
        review_document_id=review_document_id,
        source_id=source_id,
        source_sha256=source_sha256,
        processing_run_id=processing_run_id,
        attempt_id=attempt_id,
        primary_review_artifact_reference=(
            primary_review_artifact_reference
        ),
        supporting_artifact_references=(
            supporting_artifact_references
        ),
        framework_template=framework_template,
        semantic_reference_versions=(
            semantic_reference_versions
        ),
        created_at=timestamp,
        content_fingerprint="0" * 64,
    )

    _validate_review_document(
        provisional,
        verify_fingerprint=False,
    )

    document = replace(
        provisional,
        content_fingerprint=(
            calculate_review_document_fingerprint(provisional)
        ),
    )

    validate_review_document(document)

    return document


def parse_review_document(
    payload: object,
) -> ReviewDocument:
    """Parse and validate one Review Document mapping."""

    data = _exact_object(
        payload,
        expected_fields=_REVIEW_DOCUMENT_FIELDS,
        label="Review Document",
    )

    primary_reference = _parse_artifact_reference(
        data["primary_review_artifact_reference"]
    )

    supporting_payloads = data[
        "supporting_artifact_references"
    ]

    if not isinstance(supporting_payloads, list):
        raise ReviewValidationError(
            "supporting_artifact_references must be "
            "a JSON array."
        )

    supporting_references = tuple(
        _parse_artifact_reference(item)
        for item in supporting_payloads
    )

    framework_template = _parse_framework_template(
        data["framework_template"]
    )

    semantic_payloads = data[
        "semantic_reference_versions"
    ]

    if not isinstance(semantic_payloads, list):
        raise ReviewValidationError(
            "semantic_reference_versions must be a JSON array."
        )

    semantic_references = tuple(
        _parse_semantic_reference(item)
        for item in semantic_payloads
    )

    document = ReviewDocument(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        review_document_id=data["review_document_id"],
        source_id=data["source_id"],
        source_sha256=data["source_sha256"],
        processing_run_id=data["processing_run_id"],
        attempt_id=data["attempt_id"],
        primary_review_artifact_reference=primary_reference,
        supporting_artifact_references=(
            supporting_references
        ),
        framework_template=framework_template,
        semantic_reference_versions=semantic_references,
        created_at=data["created_at"],
        content_fingerprint=data["content_fingerprint"],
    )

    validate_review_document(document)

    return document


def review_document_from_json(
    text: object,
) -> ReviewDocument:
    """Parse one Review Document from strict JSON."""

    if not isinstance(text, str):
        raise ReviewValidationError(
            "Review Document JSON must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except ReviewValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ReviewValidationError(
            "Review Document is not valid JSON."
        ) from exc

    return parse_review_document(payload)


def review_document_to_dict(
    document: ReviewDocument,
) -> dict[str, object]:
    """Serialize one validated Review Document."""

    validate_review_document(document)

    return _review_document_payload(
        document,
        include_fingerprint=True,
    )


def review_document_to_json(
    document: ReviewDocument,
) -> str:
    """Serialize one Review Document as deterministic JSON."""

    return (
        json.dumps(
            review_document_to_dict(document),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def calculate_review_document_fingerprint(
    document: ReviewDocument,
) -> str:
    """Calculate the deterministic Review Document fingerprint."""

    _validate_review_document(
        document,
        verify_fingerprint=False,
    )

    payload = _review_document_payload(
        document,
        include_fingerprint=False,
    )

    canonical_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()


def validate_review_document(
    document: ReviewDocument,
) -> None:
    """Validate one complete Review Document."""

    _validate_review_document(
        document,
        verify_fingerprint=True,
    )


def _validate_review_document(
    document: ReviewDocument,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(document, ReviewDocument):
        raise ReviewValidationError(
            "document must be a ReviewDocument."
        )

    if document.schema_version != REVIEW_DOCUMENT_SCHEMA_VERSION:
        raise ReviewValidationError(
            "schema_version must be "
            f"{REVIEW_DOCUMENT_SCHEMA_VERSION!r}."
        )

    if not is_valid_project_id(document.project_id):
        raise ReviewValidationError(
            "project_id must be a valid six-digit Project ID."
        )

    _adapt_validation_error(
        validate_review_document_id,
        document.review_document_id,
        "review_document_id",
    )

    _adapt_validation_error(
        validate_source_id,
        document.source_id,
        "source_id",
    )

    _sha256(document.source_sha256, "source_sha256")

    _adapt_validation_error(
        validate_processing_run_id,
        document.processing_run_id,
        "processing_run_id",
    )

    _adapt_validation_error(
        validate_processing_attempt_id,
        document.attempt_id,
        "attempt_id",
    )

    _validate_artifact_reference(
        document.primary_review_artifact_reference,
        project_id=document.project_id,
        label="primary_review_artifact_reference",
    )

    if (
        document.primary_review_artifact_reference.artifact_type
        != "review_reports"
    ):
        raise ReviewIntegrityError(
            "primary_review_artifact_reference must have "
            "artifact_type 'review_reports'."
        )

    if not isinstance(
        document.supporting_artifact_references,
        tuple,
    ):
        raise ReviewValidationError(
            "supporting_artifact_references must be a tuple."
        )

    artifact_keys = {
        _artifact_reference_key(
            document.primary_review_artifact_reference
        )
    }

    for reference in document.supporting_artifact_references:
        _validate_artifact_reference(
            reference,
            project_id=document.project_id,
            label="supporting_artifact_reference",
        )

        key = _artifact_reference_key(reference)

        if key in artifact_keys:
            raise ReviewIntegrityError(
                "Review Document artifact references must "
                "be unique."
            )

        artifact_keys.add(key)

    _validate_framework_template(
        document.framework_template
    )

    if not isinstance(
        document.semantic_reference_versions,
        tuple,
    ):
        raise ReviewValidationError(
            "semantic_reference_versions must be a tuple."
        )

    semantic_keys: set[tuple[str, str]] = set()

    for reference in document.semantic_reference_versions:
        _validate_semantic_reference(reference)

        key = (
            reference.reference_system_id,
            reference.reference_version,
        )

        if key in semantic_keys:
            raise ReviewIntegrityError(
                "semantic_reference_versions must be unique."
            )

        semantic_keys.add(key)

    _utc_timestamp(document.created_at, "created_at")
    _sha256(
        document.content_fingerprint,
        "content_fingerprint",
    )

    if verify_fingerprint and (
        document.content_fingerprint
        != calculate_review_document_fingerprint(document)
    ):
        raise ReviewIntegrityError(
            "Review Document fingerprint does not match "
            "its content."
        )


def _review_document_payload(
    document: ReviewDocument,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": document.schema_version,
        "project_id": document.project_id,
        "review_document_id": document.review_document_id,
        "source_id": document.source_id,
        "source_sha256": document.source_sha256,
        "processing_run_id": document.processing_run_id,
        "attempt_id": document.attempt_id,
        "primary_review_artifact_reference": (
            _artifact_reference_payload(
                document.primary_review_artifact_reference
            )
        ),
        "supporting_artifact_references": [
            _artifact_reference_payload(reference)
            for reference in (
                document.supporting_artifact_references
            )
        ],
        "framework_template": {
            "template_id": (
                document.framework_template.template_id
            ),
            "template_version": (
                document.framework_template.template_version
            ),
        },
        "semantic_reference_versions": [
            {
                "reference_system_id": (
                    reference.reference_system_id
                ),
                "reference_version": (
                    reference.reference_version
                ),
            }
            for reference in (
                document.semantic_reference_versions
            )
        ],
        "created_at": document.created_at,
    }

    if include_fingerprint:
        payload["content_fingerprint"] = (
            document.content_fingerprint
        )

    return payload


def _parse_artifact_reference(
    payload: object,
) -> ProcessingArtifactReference:
    data = _exact_object(
        payload,
        expected_fields=_ARTIFACT_REFERENCE_FIELDS,
        label="Processing Artifact Reference",
    )

    try:
        return create_processing_artifact_reference(
            artifact_type=data["artifact_type"],
            artifact_id=data["artifact_id"],
            content_fingerprint=data["content_fingerprint"],
            repository_relative_path=(
                data["repository_relative_path"]
            ),
        )
    except ProcessingValidationError as exc:
        raise ReviewValidationError(
            "Processing Artifact Reference is invalid."
        ) from exc


def _artifact_reference_payload(
    reference: ProcessingArtifactReference,
) -> dict[str, str]:
    return {
        "artifact_type": reference.artifact_type,
        "artifact_id": reference.artifact_id,
        "content_fingerprint": (
            reference.content_fingerprint
        ),
        "repository_relative_path": (
            reference.repository_relative_path
        ),
    }


def _validate_artifact_reference(
    reference: ProcessingArtifactReference,
    *,
    project_id: str,
    label: str,
) -> None:
    try:
        validate_processing_artifact_reference(reference)
    except ProcessingValidationError as exc:
        raise ReviewValidationError(
            f"{label} is invalid."
        ) from exc

    path = PurePosixPath(reference.repository_relative_path)

    expected_prefix = (
        "data",
        "projects",
        project_id,
    )

    if path.parts[:3] != expected_prefix:
        raise ReviewIntegrityError(
            f"{label} must remain inside the selected Project."
        )


def _artifact_reference_key(
    reference: ProcessingArtifactReference,
) -> tuple[str, str, str, str]:
    return (
        reference.artifact_type,
        reference.artifact_id,
        reference.content_fingerprint,
        reference.repository_relative_path,
    )


def _parse_framework_template(
    payload: object,
) -> FrameworkTemplateReference:
    data = _exact_object(
        payload,
        expected_fields=_FRAMEWORK_TEMPLATE_FIELDS,
        label="Framework Template Reference",
    )

    reference = FrameworkTemplateReference(
        template_id=data["template_id"],
        template_version=data["template_version"],
    )

    _validate_framework_template(reference)

    return reference


def _validate_framework_template(
    reference: FrameworkTemplateReference,
) -> None:
    if not isinstance(reference, FrameworkTemplateReference):
        raise ReviewValidationError(
            "framework_template must be a "
            "FrameworkTemplateReference."
        )

    _identifier(
        reference.template_id,
        _FRAMEWORK_TEMPLATE_ID_PATTERN,
        "framework_template.template_id",
    )

    _identifier(
        reference.template_version,
        _SEMANTIC_VERSION_PATTERN,
        "framework_template.template_version",
    )


def _parse_semantic_reference(
    payload: object,
) -> SemanticReferenceVersion:
    data = _exact_object(
        payload,
        expected_fields=_SEMANTIC_REFERENCE_FIELDS,
        label="Semantic Reference Version",
    )

    try:
        return create_semantic_reference_version(
            reference_system_id=data["reference_system_id"],
            reference_version=data["reference_version"],
        )
    except ProcessingValidationError as exc:
        raise ReviewValidationError(
            "Semantic Reference Version is invalid."
        ) from exc


def _validate_semantic_reference(
    reference: SemanticReferenceVersion,
) -> None:
    if not isinstance(reference, SemanticReferenceVersion):
        raise ReviewValidationError(
            "semantic_reference_versions entries must be "
            "SemanticReferenceVersion values."
        )

    # Review Documents preserve the exact semantic-reference binding
    # from the authoritative Processing Run. Semantic reference
    # versions are not necessarily SemVer (for example BFO "2020"
    # or IOF "202602"), so reuse the Processing contract instead of
    # imposing a narrower Review-only syntax.
    try:
        create_semantic_reference_version(
            reference_system_id=reference.reference_system_id,
            reference_version=reference.reference_version,
        )
    except ProcessingValidationError as exc:
        raise ReviewValidationError(
            "Semantic Reference Version is invalid."
        ) from exc


def _exact_object(
    value: object,
    *,
    expected_fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReviewValidationError(
            f"{label} must be a JSON object."
        )

    actual_fields = frozenset(value)

    if actual_fields != expected_fields:
        raise ReviewValidationError(
            f"{label} has invalid fields; "
            f"missing={sorted(expected_fields - actual_fields)}, "
            f"unknown={sorted(actual_fields - expected_fields)}."
        )

    return value


def _adapt_validation_error(
    validator: Any,
    value: object,
    label: str,
) -> None:
    try:
        validator(value)
    except (
        ReviewValidationError,
        ProcessingValidationError,
        SourceManifestError,
    ) as exc:
        raise ReviewValidationError(
            f"{label} is invalid."
        ) from exc


def _identifier(
    value: object,
    pattern: re.Pattern[str],
    label: str,
) -> str:
    selected = _text(value, label)

    if pattern.fullmatch(selected) is None:
        raise ReviewValidationError(
            f"{label} has invalid syntax."
        )

    return selected


def _sha256(value: object, label: str) -> str:
    return _identifier(
        value,
        _SHA256_PATTERN,
        label,
    )


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ReviewValidationError(
            f"{label} must be a non-empty string."
        )

    if value != value.strip():
        raise ReviewValidationError(
            f"{label} must not contain surrounding whitespace."
        )

    return value


def _utc_timestamp(value: object, label: str) -> str:
    selected = _identifier(
        value,
        _UTC_TIMESTAMP_PATTERN,
        label,
    )

    try:
        datetime.fromisoformat(
            selected.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ReviewValidationError(
            f"{label} is not a valid UTC timestamp."
        ) from exc

    return selected


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise ReviewValidationError(
                f"Duplicate JSON object key: {key!r}."
            )

        result[key] = value

    return result
