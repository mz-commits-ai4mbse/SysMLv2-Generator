"""Create and serialize immutable Finalized Reviewed Documents."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import hashlib
import json
import re
from typing import Any

from modules.project_processing.errors import (
    ProcessingValidationError,
)
from modules.project_processing.identifiers import (
    validate_processing_attempt_id,
    validate_processing_run_id,
)
from modules.project_sources.errors import (
    SourceManifestError,
)
from modules.project_sources.identifiers import (
    validate_source_id,
)
from modules.project_workspace.identifiers import (
    is_valid_project_id,
)

from .document_manifest import (
    validate_review_document,
)
from .errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from .finalization_authorization import (
    ReviewFinalizationAuthorization,
    validate_review_finalization_authorization,
)
from .identifiers import (
    validate_review_document_id,
    validate_review_document_version_id,
    validate_review_item_id,
    validate_review_revision_id,
)
from .revision_manifest import (
    validate_review_revision,
)
from .types import (
    REVIEW_ITEM_KINDS,
    REVIEW_ITEM_OUTCOMES,
    REVIEW_ITEM_SECTIONS,
    ReviewDocument,
    ReviewDocumentVersion,
    ReviewRevision,
)
from .version_manifest import (
    validate_review_document_version,
)


FINALIZED_REVIEWED_DOCUMENT_SCHEMA_VERSION = "1.0.0"

FINALIZED_REVIEW_ITEM_OUTCOMES = frozenset(
    REVIEW_ITEM_OUTCOMES
    - {
        "open",
        "unresolved",
    }
)

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_STABLE_SUBJECT_KEY_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9._:-]{0,239}$"
)
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_ITEM_SECTION_BY_KIND = {
    "element": "elements",
    "relationship": "relationships",
    "open_question": "open_questions",
}

_FINALIZED_REVIEWED_DOCUMENT_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "review_document_id",
        "review_document_version_id",
        "version_number",
        "predecessor_version_id",
        "review_revision_id",
        "source_id",
        "source_sha256",
        "processing_run_id",
        "attempt_id",
        "review_document_content_fingerprint",
        "draft_version_content_fingerprint",
        "finalized_version_content_fingerprint",
        "review_revision_fingerprint",
        "finalization_decision_id",
        "finalization_decision_fingerprint",
        "finalization_validation_fingerprint",
        "finalization_authorization_fingerprint",
        "reviewer_identity",
        "decision_at",
        "finalized_at",
        "review_items",
        "content_fingerprint",
    }
)

_REVIEW_ITEM_REFERENCE_FIELDS = frozenset(
    {
        "review_item_id",
        "stable_subject_key",
        "review_item_kind",
        "section",
        "effective_review_outcome",
        "item_content_fingerprint",
    }
)


@dataclass(frozen=True, slots=True)
class FinalizedReviewItemReference:
    """One exact Review Item contained in a finalized revision."""

    review_item_id: str
    stable_subject_key: str
    review_item_kind: str
    section: str
    effective_review_outcome: str
    item_content_fingerprint: str


@dataclass(frozen=True, slots=True)
class FinalizedReviewedDocument:
    """Immutable identity and integrity manifest of one final review."""

    schema_version: str
    project_id: str
    review_document_id: str
    review_document_version_id: str
    version_number: int
    predecessor_version_id: str | None
    review_revision_id: str
    source_id: str
    source_sha256: str
    processing_run_id: str
    attempt_id: str
    review_document_content_fingerprint: str
    draft_version_content_fingerprint: str
    finalized_version_content_fingerprint: str
    review_revision_fingerprint: str
    finalization_decision_id: str
    finalization_decision_fingerprint: str
    finalization_validation_fingerprint: str
    finalization_authorization_fingerprint: str
    reviewer_identity: str
    decision_at: str
    finalized_at: str
    review_items: tuple[
        FinalizedReviewItemReference,
        ...,
    ]
    content_fingerprint: str


def create_finalized_reviewed_document(
    document: ReviewDocument,
    finalized_version: ReviewDocumentVersion,
    revision: ReviewRevision,
    authorization: ReviewFinalizationAuthorization,
) -> FinalizedReviewedDocument:
    """Create one exact immutable Finalized Reviewed Document."""

    validate_review_document(document)
    validate_review_document_version(finalized_version)
    validate_review_revision(revision)
    validate_review_finalization_authorization(
        authorization
    )

    _validate_source_binding(
        document,
        finalized_version,
        revision,
        authorization,
    )

    item_references = tuple(
        sorted(
            (
                FinalizedReviewItemReference(
                    review_item_id=item.review_item_id,
                    stable_subject_key=(
                        item.stable_subject_key
                    ),
                    review_item_kind=(
                        item.review_item_kind
                    ),
                    section=item.section,
                    effective_review_outcome=(
                        item.effective_review_outcome
                    ),
                    item_content_fingerprint=(
                        item.item_content_fingerprint
                    ),
                )
                for item in revision.review_items
            ),
            key=lambda item: item.review_item_id,
        )
    )

    provisional = FinalizedReviewedDocument(
        schema_version=(
            FINALIZED_REVIEWED_DOCUMENT_SCHEMA_VERSION
        ),
        project_id=document.project_id,
        review_document_id=(
            document.review_document_id
        ),
        review_document_version_id=(
            finalized_version
            .review_document_version_id
        ),
        version_number=finalized_version.version_number,
        predecessor_version_id=(
            finalized_version.predecessor_version_id
        ),
        review_revision_id=(
            revision.review_revision_id
        ),
        source_id=document.source_id,
        source_sha256=document.source_sha256,
        processing_run_id=document.processing_run_id,
        attempt_id=document.attempt_id,
        review_document_content_fingerprint=(
            document.content_fingerprint
        ),
        draft_version_content_fingerprint=(
            authorization
            .draft_version_content_fingerprint
        ),
        finalized_version_content_fingerprint=(
            finalized_version.content_fingerprint
        ),
        review_revision_fingerprint=(
            revision.revision_fingerprint
        ),
        finalization_decision_id=(
            authorization.human_review_decision_id
        ),
        finalization_decision_fingerprint=(
            authorization
            .human_review_decision_fingerprint
        ),
        finalization_validation_fingerprint=(
            authorization.validation_fingerprint
        ),
        finalization_authorization_fingerprint=(
            authorization.authorization_fingerprint
        ),
        reviewer_identity=(
            authorization.reviewer_identity
        ),
        decision_at=authorization.decided_at,
        finalized_at=authorization.finalized_at,
        review_items=item_references,
        content_fingerprint="0" * 64,
    )

    manifest = replace(
        provisional,
        content_fingerprint=(
            calculate_finalized_reviewed_document_fingerprint(
                provisional
            )
        ),
    )

    validate_finalized_reviewed_document(manifest)

    return manifest


def parse_finalized_reviewed_document(
    payload: object,
) -> FinalizedReviewedDocument:
    """Parse and validate one strict manifest mapping."""

    data = _exact_object(
        payload,
        expected_fields=(
            _FINALIZED_REVIEWED_DOCUMENT_FIELDS
        ),
        label="Finalized Reviewed Document",
    )

    item_payloads = data["review_items"]

    if not isinstance(item_payloads, list):
        raise ReviewValidationError(
            "review_items must be a JSON array."
        )

    manifest = FinalizedReviewedDocument(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        review_document_id=(
            data["review_document_id"]
        ),
        review_document_version_id=(
            data["review_document_version_id"]
        ),
        version_number=data["version_number"],
        predecessor_version_id=(
            data["predecessor_version_id"]
        ),
        review_revision_id=(
            data["review_revision_id"]
        ),
        source_id=data["source_id"],
        source_sha256=data["source_sha256"],
        processing_run_id=(
            data["processing_run_id"]
        ),
        attempt_id=data["attempt_id"],
        review_document_content_fingerprint=(
            data[
                "review_document_content_fingerprint"
            ]
        ),
        draft_version_content_fingerprint=(
            data[
                "draft_version_content_fingerprint"
            ]
        ),
        finalized_version_content_fingerprint=(
            data[
                "finalized_version_content_fingerprint"
            ]
        ),
        review_revision_fingerprint=(
            data["review_revision_fingerprint"]
        ),
        finalization_decision_id=(
            data["finalization_decision_id"]
        ),
        finalization_decision_fingerprint=(
            data[
                "finalization_decision_fingerprint"
            ]
        ),
        finalization_validation_fingerprint=(
            data[
                "finalization_validation_fingerprint"
            ]
        ),
        finalization_authorization_fingerprint=(
            data[
                "finalization_authorization_fingerprint"
            ]
        ),
        reviewer_identity=data["reviewer_identity"],
        decision_at=data["decision_at"],
        finalized_at=data["finalized_at"],
        review_items=tuple(
            _parse_review_item_reference(value)
            for value in item_payloads
        ),
        content_fingerprint=(
            data["content_fingerprint"]
        ),
    )

    validate_finalized_reviewed_document(manifest)

    return manifest


def finalized_reviewed_document_from_json(
    text: object,
) -> FinalizedReviewedDocument:
    """Parse one manifest from strict JSON."""

    if not isinstance(text, str):
        raise ReviewValidationError(
            "Finalized Reviewed Document JSON "
            "must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=(
                _object_without_duplicate_keys
            ),
        )
    except ReviewValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ReviewValidationError(
            "Finalized Reviewed Document is not "
            "valid JSON."
        ) from exc

    return parse_finalized_reviewed_document(payload)


def finalized_reviewed_document_to_dict(
    manifest: FinalizedReviewedDocument,
) -> dict[str, object]:
    """Serialize one validated manifest."""

    validate_finalized_reviewed_document(manifest)

    return _manifest_payload(
        manifest,
        include_fingerprint=True,
    )


def finalized_reviewed_document_to_json(
    manifest: FinalizedReviewedDocument,
) -> str:
    """Serialize one manifest deterministically."""

    return (
        json.dumps(
            finalized_reviewed_document_to_dict(
                manifest
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def calculate_finalized_reviewed_document_fingerprint(
    manifest: FinalizedReviewedDocument,
) -> str:
    """Calculate the deterministic manifest fingerprint."""

    _validate_manifest(
        manifest,
        verify_fingerprint=False,
    )

    payload = _manifest_payload(
        manifest,
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


def validate_finalized_reviewed_document(
    manifest: FinalizedReviewedDocument,
) -> None:
    """Validate one complete manifest."""

    _validate_manifest(
        manifest,
        verify_fingerprint=True,
    )


def _validate_source_binding(
    document: ReviewDocument,
    finalized_version: ReviewDocumentVersion,
    revision: ReviewRevision,
    authorization: ReviewFinalizationAuthorization,
) -> None:
    if finalized_version.version_state != "finalized":
        raise ReviewIntegrityError(
            "Finalized Reviewed Document requires "
            "a finalized Review Document Version."
        )

    project_ids = {
        document.project_id,
        finalized_version.project_id,
        revision.project_id,
        authorization.project_id,
    }

    if len(project_ids) != 1:
        raise ReviewIntegrityError(
            "Finalized review inputs do not belong "
            "to the same Project."
        )

    document_ids = {
        document.review_document_id,
        finalized_version.review_document_id,
        revision.review_document_id,
        authorization.review_document_id,
    }

    if len(document_ids) != 1:
        raise ReviewIntegrityError(
            "Finalized review inputs do not belong "
            "to the same Review Document."
        )

    version_ids = {
        finalized_version.review_document_version_id,
        revision.review_document_version_id,
        authorization.review_document_version_id,
    }

    if len(version_ids) != 1:
        raise ReviewIntegrityError(
            "Finalized review inputs do not belong "
            "to the same Review Document Version."
        )

    if (
        finalized_version.finalized_revision_id
        != revision.review_revision_id
        or authorization.review_revision_id
        != revision.review_revision_id
    ):
        raise ReviewIntegrityError(
            "Finalized review inputs do not bind "
            "the same Review Revision."
        )

    if (
        finalized_version.finalization_decision_id
        != authorization.human_review_decision_id
    ):
        raise ReviewIntegrityError(
            "Finalized Review Version does not bind "
            "the authorization decision."
        )

    if (
        finalized_version.content_fingerprint
        != authorization
        .finalized_version_content_fingerprint
    ):
        raise ReviewIntegrityError(
            "Finalized Review Version fingerprint "
            "does not match its authorization."
        )

    if (
        revision.revision_fingerprint
        != authorization.review_revision_fingerprint
    ):
        raise ReviewIntegrityError(
            "Review Revision fingerprint does not "
            "match its authorization."
        )

    if (
        finalized_version.finalized_at
        != authorization.finalized_at
    ):
        raise ReviewIntegrityError(
            "Finalization timestamps do not match."
        )


def _validate_manifest(
    manifest: FinalizedReviewedDocument,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(
        manifest,
        FinalizedReviewedDocument,
    ):
        raise ReviewValidationError(
            "manifest must be a "
            "FinalizedReviewedDocument."
        )

    if (
        manifest.schema_version
        != FINALIZED_REVIEWED_DOCUMENT_SCHEMA_VERSION
    ):
        raise ReviewValidationError(
            "Invalid Finalized Reviewed Document "
            "schema_version."
        )

    if not is_valid_project_id(manifest.project_id):
        raise ReviewValidationError(
            "project_id must be a valid six-digit "
            "Project ID."
        )

    validate_review_document_id(
        manifest.review_document_id
    )
    validate_review_document_version_id(
        manifest.review_document_version_id
    )
    validate_review_revision_id(
        manifest.review_revision_id
    )

    if (
        isinstance(manifest.version_number, bool)
        or not isinstance(
            manifest.version_number,
            int,
        )
        or manifest.version_number < 1
    ):
        raise ReviewValidationError(
            "version_number must be an integer "
            "of at least 1."
        )

    if manifest.version_number == 1:
        if manifest.predecessor_version_id is not None:
            raise ReviewIntegrityError(
                "The first finalized version must not "
                "have a predecessor."
            )
    else:
        if manifest.predecessor_version_id is None:
            raise ReviewIntegrityError(
                "A successor finalized version requires "
                "predecessor_version_id."
            )

        validate_review_document_version_id(
            manifest.predecessor_version_id
        )

    _adapt_source_validator(
        validate_source_id,
        manifest.source_id,
        "source_id",
    )
    _adapt_processing_validator(
        validate_processing_run_id,
        manifest.processing_run_id,
        "processing_run_id",
    )
    _adapt_processing_validator(
        validate_processing_attempt_id,
        manifest.attempt_id,
        "attempt_id",
    )

    _sha256(
        manifest.source_sha256,
        "source_sha256",
    )

    for label, value in (
        (
            "review_document_content_fingerprint",
            manifest
            .review_document_content_fingerprint,
        ),
        (
            "draft_version_content_fingerprint",
            manifest
            .draft_version_content_fingerprint,
        ),
        (
            "finalized_version_content_fingerprint",
            manifest
            .finalized_version_content_fingerprint,
        ),
        (
            "review_revision_fingerprint",
            manifest.review_revision_fingerprint,
        ),
        (
            "finalization_decision_fingerprint",
            manifest
            .finalization_decision_fingerprint,
        ),
        (
            "finalization_validation_fingerprint",
            manifest
            .finalization_validation_fingerprint,
        ),
        (
            "finalization_authorization_fingerprint",
            manifest
            .finalization_authorization_fingerprint,
        ),
        (
            "content_fingerprint",
            manifest.content_fingerprint,
        ),
    ):
        _sha256(value, label)

    _text(
        manifest.finalization_decision_id,
        "finalization_decision_id",
    )
    _text(
        manifest.reviewer_identity,
        "reviewer_identity",
    )

    decision_at = _utc_timestamp(
        manifest.decision_at,
        "decision_at",
    )
    finalized_at = _utc_timestamp(
        manifest.finalized_at,
        "finalized_at",
    )

    if finalized_at < decision_at:
        raise ReviewIntegrityError(
            "finalized_at must not be earlier "
            "than decision_at."
        )

    if not isinstance(manifest.review_items, tuple):
        raise ReviewValidationError(
            "review_items must be a tuple."
        )

    for item in manifest.review_items:
        _validate_review_item_reference(item)

    item_ids = tuple(
        item.review_item_id
        for item in manifest.review_items
    )

    if len(item_ids) != len(set(item_ids)):
        raise ReviewIntegrityError(
            "review_items must not contain "
            "duplicate Review Item IDs."
        )

    if item_ids != tuple(sorted(item_ids)):
        raise ReviewIntegrityError(
            "review_items must be ordered by "
            "review_item_id."
        )

    if verify_fingerprint and (
        manifest.content_fingerprint
        != calculate_finalized_reviewed_document_fingerprint(
            manifest
        )
    ):
        raise ReviewIntegrityError(
            "Finalized Reviewed Document fingerprint "
            "does not match its content."
        )


def _validate_review_item_reference(
    reference: FinalizedReviewItemReference,
) -> None:
    if not isinstance(
        reference,
        FinalizedReviewItemReference,
    ):
        raise ReviewValidationError(
            "review_items must contain "
            "FinalizedReviewItemReference values."
        )

    validate_review_item_id(reference.review_item_id)

    if (
        not isinstance(reference.stable_subject_key, str)
        or _STABLE_SUBJECT_KEY_PATTERN.fullmatch(
            reference.stable_subject_key
        )
        is None
    ):
        raise ReviewValidationError(
            "stable_subject_key is invalid."
        )

    if reference.review_item_kind not in REVIEW_ITEM_KINDS:
        raise ReviewValidationError(
            "review_item_kind is invalid."
        )

    if reference.section not in REVIEW_ITEM_SECTIONS:
        raise ReviewValidationError(
            "section is invalid."
        )

    if (
        reference.section
        != _ITEM_SECTION_BY_KIND[
            reference.review_item_kind
        ]
    ):
        raise ReviewIntegrityError(
            "Review Item section does not match "
            "review_item_kind."
        )

    if (
        reference.effective_review_outcome
        not in FINALIZED_REVIEW_ITEM_OUTCOMES
    ):
        raise ReviewIntegrityError(
            "A finalized Review Item must have "
            "a non-blocking effective outcome."
        )

    _sha256(
        reference.item_content_fingerprint,
        "item_content_fingerprint",
    )


def _parse_review_item_reference(
    payload: object,
) -> FinalizedReviewItemReference:
    data = _exact_object(
        payload,
        expected_fields=_REVIEW_ITEM_REFERENCE_FIELDS,
        label="Finalized Review Item Reference",
    )

    reference = FinalizedReviewItemReference(
        review_item_id=data["review_item_id"],
        stable_subject_key=(
            data["stable_subject_key"]
        ),
        review_item_kind=(
            data["review_item_kind"]
        ),
        section=data["section"],
        effective_review_outcome=(
            data["effective_review_outcome"]
        ),
        item_content_fingerprint=(
            data["item_content_fingerprint"]
        ),
    )

    _validate_review_item_reference(reference)

    return reference


def _manifest_payload(
    manifest: FinalizedReviewedDocument,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": manifest.schema_version,
        "project_id": manifest.project_id,
        "review_document_id": (
            manifest.review_document_id
        ),
        "review_document_version_id": (
            manifest.review_document_version_id
        ),
        "version_number": manifest.version_number,
        "predecessor_version_id": (
            manifest.predecessor_version_id
        ),
        "review_revision_id": (
            manifest.review_revision_id
        ),
        "source_id": manifest.source_id,
        "source_sha256": manifest.source_sha256,
        "processing_run_id": (
            manifest.processing_run_id
        ),
        "attempt_id": manifest.attempt_id,
        "review_document_content_fingerprint": (
            manifest
            .review_document_content_fingerprint
        ),
        "draft_version_content_fingerprint": (
            manifest
            .draft_version_content_fingerprint
        ),
        "finalized_version_content_fingerprint": (
            manifest
            .finalized_version_content_fingerprint
        ),
        "review_revision_fingerprint": (
            manifest.review_revision_fingerprint
        ),
        "finalization_decision_id": (
            manifest.finalization_decision_id
        ),
        "finalization_decision_fingerprint": (
            manifest
            .finalization_decision_fingerprint
        ),
        "finalization_validation_fingerprint": (
            manifest
            .finalization_validation_fingerprint
        ),
        "finalization_authorization_fingerprint": (
            manifest
            .finalization_authorization_fingerprint
        ),
        "reviewer_identity": (
            manifest.reviewer_identity
        ),
        "decision_at": manifest.decision_at,
        "finalized_at": manifest.finalized_at,
        "review_items": [
            {
                "review_item_id": item.review_item_id,
                "stable_subject_key": (
                    item.stable_subject_key
                ),
                "review_item_kind": (
                    item.review_item_kind
                ),
                "section": item.section,
                "effective_review_outcome": (
                    item.effective_review_outcome
                ),
                "item_content_fingerprint": (
                    item.item_content_fingerprint
                ),
            }
            for item in manifest.review_items
        ],
    }

    if include_fingerprint:
        payload["content_fingerprint"] = (
            manifest.content_fingerprint
        )

    return payload


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


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise ReviewValidationError(
                f"Duplicate JSON key: {key!r}."
            )

        result[key] = value

    return result


def _adapt_source_validator(
    validator: Any,
    value: object,
    label: str,
) -> None:
    try:
        validator(value)
    except SourceManifestError as exc:
        raise ReviewValidationError(
            f"{label} is invalid."
        ) from exc


def _adapt_processing_validator(
    validator: Any,
    value: object,
    label: str,
) -> None:
    try:
        validator(value)
    except ProcessingValidationError as exc:
        raise ReviewValidationError(
            f"{label} is invalid."
        ) from exc


def _sha256(
    value: object,
    label: str,
) -> str:
    if (
        not isinstance(value, str)
        or _SHA256_PATTERN.fullmatch(value)
        is None
    ):
        raise ReviewValidationError(
            f"{label} must be a lowercase SHA-256."
        )

    return value


def _text(
    value: object,
    label: str,
) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
    ):
        raise ReviewValidationError(
            f"{label} must be non-empty text "
            "without surrounding whitespace."
        )

    return value


def _utc_timestamp(
    value: object,
    label: str,
) -> datetime:
    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value)
        is None
    ):
        raise ReviewValidationError(
            f"{label} must be a UTC timestamp."
        )

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )
