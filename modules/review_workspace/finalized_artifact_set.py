"""Bind finalized review artifacts as one exact in-memory integrity set."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import re

from .effective_decisions_manifest import (
    EffectiveReviewDecisionSet,
    effective_review_decision_set_to_json,
    validate_effective_review_decision_set,
)
from .errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from .paths import (
    EFFECTIVE_DECISIONS_FILENAME,
    REVIEWED_DOCUMENT_FILENAME,
    REVIEWED_REPORT_FILENAME,
)
from .reviewed_document_manifest import (
    FinalizedReviewedDocument,
    finalized_reviewed_document_to_json,
    validate_finalized_reviewed_document,
)
from .reviewed_report_renderer import (
    RenderedReviewedReport,
    create_rendered_reviewed_report,
    reviewed_report_to_markdown,
    validate_rendered_reviewed_report,
    validate_reviewed_report_source_binding,
)


FINALIZED_REVIEW_ARTIFACT_SET_SCHEMA_VERSION = "1.0.0"

FINALIZED_REVIEW_ARTIFACT_ORDER = (
    REVIEWED_DOCUMENT_FILENAME,
    EFFECTIVE_DECISIONS_FILENAME,
    REVIEWED_REPORT_FILENAME,
)

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class FinalizedReviewArtifact:
    """One exact UTF-8 byte representation in the finalized artifact set."""

    filename: str
    content: bytes
    byte_fingerprint: str


@dataclass(frozen=True, slots=True)
class FinalizedReviewArtifactSet:
    """One exact three-artifact finalization set held only in memory."""

    schema_version: str
    reviewed_document: FinalizedReviewedDocument
    effective_decisions: EffectiveReviewDecisionSet
    reviewed_report: RenderedReviewedReport
    artifacts: tuple[FinalizedReviewArtifact, ...]
    artifact_set_fingerprint: str


def create_finalized_review_artifact_set(
    reviewed_document: FinalizedReviewedDocument,
    effective_decisions: EffectiveReviewDecisionSet,
    reviewed_report: RenderedReviewedReport,
) -> FinalizedReviewArtifactSet:
    """Create one exact validated in-memory finalization artifact set."""

    validate_finalized_reviewed_document(
        reviewed_document
    )
    validate_effective_review_decision_set(
        effective_decisions
    )
    validate_rendered_reviewed_report(
        reviewed_report
    )
    validate_reviewed_report_source_binding(
        reviewed_document,
        effective_decisions,
    )

    expected_report = create_rendered_reviewed_report(
        reviewed_document,
        effective_decisions,
    )

    if reviewed_report != expected_report:
        raise ReviewIntegrityError(
            "Reviewed Report is not the exact "
            "deterministic rendering of the finalized "
            "review sources."
        )

    artifacts = _create_exact_artifacts(
        reviewed_document,
        effective_decisions,
        reviewed_report,
    )

    provisional = FinalizedReviewArtifactSet(
        schema_version=(
            FINALIZED_REVIEW_ARTIFACT_SET_SCHEMA_VERSION
        ),
        reviewed_document=reviewed_document,
        effective_decisions=effective_decisions,
        reviewed_report=reviewed_report,
        artifacts=artifacts,
        artifact_set_fingerprint="0" * 64,
    )

    artifact_set = replace(
        provisional,
        artifact_set_fingerprint=(
            calculate_finalized_review_artifact_set_fingerprint(
                provisional
            )
        ),
    )

    validate_finalized_review_artifact_set(
        artifact_set
    )

    return artifact_set


def calculate_finalized_review_artifact_fingerprint(
    content: object,
) -> str:
    """Calculate the SHA-256 of one exact artifact byte sequence."""

    if not isinstance(content, bytes):
        raise ReviewValidationError(
            "Finalized review artifact content must be bytes."
        )

    return hashlib.sha256(content).hexdigest()


def calculate_finalized_review_artifact_set_fingerprint(
    artifact_set: FinalizedReviewArtifactSet,
) -> str:
    """Derive the deterministic in-memory artifact-set fingerprint."""

    _validate_artifact_set(
        artifact_set,
        verify_set_fingerprint=False,
    )

    canonical_json = json.dumps(
        _artifact_set_fingerprint_payload(
            artifact_set
        ),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()


def validate_finalized_review_artifact_set(
    artifact_set: FinalizedReviewArtifactSet,
) -> None:
    """Validate one exact finalized three-artifact integrity set."""

    _validate_artifact_set(
        artifact_set,
        verify_set_fingerprint=True,
    )


def _create_exact_artifacts(
    reviewed_document: FinalizedReviewedDocument,
    effective_decisions: EffectiveReviewDecisionSet,
    reviewed_report: RenderedReviewedReport,
) -> tuple[FinalizedReviewArtifact, ...]:
    return tuple(
        FinalizedReviewArtifact(
            filename=filename,
            content=content,
            byte_fingerprint=(
                calculate_finalized_review_artifact_fingerprint(
                    content
                )
            ),
        )
        for filename, content in _exact_artifact_contents(
            reviewed_document,
            effective_decisions,
            reviewed_report,
        )
    )


def _exact_artifact_contents(
    reviewed_document: FinalizedReviewedDocument,
    effective_decisions: EffectiveReviewDecisionSet,
    reviewed_report: RenderedReviewedReport,
) -> tuple[tuple[str, bytes], ...]:
    return (
        (
            REVIEWED_DOCUMENT_FILENAME,
            finalized_reviewed_document_to_json(
                reviewed_document
            ).encode("utf-8"),
        ),
        (
            EFFECTIVE_DECISIONS_FILENAME,
            effective_review_decision_set_to_json(
                effective_decisions
            ).encode("utf-8"),
        ),
        (
            REVIEWED_REPORT_FILENAME,
            reviewed_report_to_markdown(
                reviewed_report
            ).encode("utf-8"),
        ),
    )


def _validate_artifact_set(
    artifact_set: FinalizedReviewArtifactSet,
    *,
    verify_set_fingerprint: bool,
) -> None:
    if not isinstance(
        artifact_set,
        FinalizedReviewArtifactSet,
    ):
        raise ReviewValidationError(
            "artifact_set must be a "
            "FinalizedReviewArtifactSet."
        )

    if (
        artifact_set.schema_version
        != FINALIZED_REVIEW_ARTIFACT_SET_SCHEMA_VERSION
    ):
        raise ReviewValidationError(
            "Invalid Finalized Review Artifact Set "
            "schema_version."
        )

    validate_finalized_reviewed_document(
        artifact_set.reviewed_document
    )
    validate_effective_review_decision_set(
        artifact_set.effective_decisions
    )
    validate_rendered_reviewed_report(
        artifact_set.reviewed_report
    )
    validate_reviewed_report_source_binding(
        artifact_set.reviewed_document,
        artifact_set.effective_decisions,
    )

    expected_report = create_rendered_reviewed_report(
        artifact_set.reviewed_document,
        artifact_set.effective_decisions,
    )

    if artifact_set.reviewed_report != expected_report:
        raise ReviewIntegrityError(
            "Reviewed Report is not the exact "
            "deterministic rendering of the finalized "
            "review sources."
        )

    if not isinstance(artifact_set.artifacts, tuple):
        raise ReviewValidationError(
            "artifacts must be a tuple."
        )

    if len(artifact_set.artifacts) != 3:
        raise ReviewIntegrityError(
            "Finalized Review Artifact Set must contain "
            "exactly three artifacts."
        )

    for artifact in artifact_set.artifacts:
        _validate_artifact(artifact)

    actual_order = tuple(
        artifact.filename
        for artifact in artifact_set.artifacts
    )

    if actual_order != FINALIZED_REVIEW_ARTIFACT_ORDER:
        raise ReviewIntegrityError(
            "Finalized Review Artifact Set does not use "
            "the exact artifact order."
        )

    expected_contents = _exact_artifact_contents(
        artifact_set.reviewed_document,
        artifact_set.effective_decisions,
        artifact_set.reviewed_report,
    )

    for artifact, (expected_filename, expected_content) in zip(
        artifact_set.artifacts,
        expected_contents,
        strict=True,
    ):
        if artifact.filename != expected_filename:
            raise ReviewIntegrityError(
                "Finalized Review Artifact filename does "
                "not match the exact artifact contract."
            )

        if artifact.content != expected_content:
            raise ReviewIntegrityError(
                f"{artifact.filename} does not contain "
                "the exact deterministic bytes."
            )

        expected_byte_fingerprint = (
            calculate_finalized_review_artifact_fingerprint(
                expected_content
            )
        )

        if (
            artifact.byte_fingerprint
            != expected_byte_fingerprint
        ):
            raise ReviewIntegrityError(
                f"{artifact.filename} byte fingerprint "
                "does not match the exact deterministic "
                "bytes."
            )

    _sha256(
        artifact_set.artifact_set_fingerprint,
        "artifact_set_fingerprint",
    )

    if verify_set_fingerprint and (
        artifact_set.artifact_set_fingerprint
        != calculate_finalized_review_artifact_set_fingerprint(
            artifact_set
        )
    ):
        raise ReviewIntegrityError(
            "Artifact-set fingerprint does not match "
            "the exact finalized artifact set."
        )


def _validate_artifact(
    artifact: FinalizedReviewArtifact,
) -> None:
    if not isinstance(
        artifact,
        FinalizedReviewArtifact,
    ):
        raise ReviewValidationError(
            "artifacts must contain only "
            "FinalizedReviewArtifact values."
        )

    if not isinstance(artifact.filename, str):
        raise ReviewValidationError(
            "Finalized review artifact filename "
            "must be a string."
        )

    if not artifact.filename:
        raise ReviewValidationError(
            "Finalized review artifact filename "
            "must not be empty."
        )

    if not isinstance(artifact.content, bytes):
        raise ReviewValidationError(
            "Finalized review artifact content "
            "must be bytes."
        )

    _sha256(
        artifact.byte_fingerprint,
        "byte_fingerprint",
    )

    if (
        artifact.byte_fingerprint
        != calculate_finalized_review_artifact_fingerprint(
            artifact.content
        )
    ):
        raise ReviewIntegrityError(
            f"{artifact.filename} byte fingerprint "
            "does not match its exact content."
        )


def _artifact_set_fingerprint_payload(
    artifact_set: FinalizedReviewArtifactSet,
) -> dict[str, object]:
    reviewed_document = artifact_set.reviewed_document
    effective_decisions = artifact_set.effective_decisions
    reviewed_report = artifact_set.reviewed_report

    return {
        "schema_version": artifact_set.schema_version,
        "project_id": reviewed_document.project_id,
        "review_document_id": (
            reviewed_document.review_document_id
        ),
        "review_document_version_id": (
            reviewed_document.review_document_version_id
        ),
        "review_revision_id": (
            reviewed_document.review_revision_id
        ),
        "finalized_at": reviewed_document.finalized_at,
        "finalization_decision_id": (
            reviewed_document.finalization_decision_id
        ),
        "finalization_decision_fingerprint": (
            reviewed_document
            .finalization_decision_fingerprint
        ),
        "finalization_validation_fingerprint": (
            reviewed_document
            .finalization_validation_fingerprint
        ),
        "finalization_authorization_fingerprint": (
            reviewed_document
            .finalization_authorization_fingerprint
        ),
        "reviewed_document_content_fingerprint": (
            reviewed_document.content_fingerprint
        ),
        "effective_decision_set_content_fingerprint": (
            effective_decisions.content_fingerprint
        ),
        "reviewed_report_content_fingerprint": (
            reviewed_report.content_fingerprint
        ),
        "artifacts": [
            {
                "filename": artifact.filename,
                "byte_fingerprint": (
                    artifact.byte_fingerprint
                ),
            }
            for artifact in artifact_set.artifacts
        ],
    }


def _sha256(
    value: object,
    label: str,
) -> None:
    if (
        not isinstance(value, str)
        or not _SHA256_PATTERN.fullmatch(value)
    ):
        raise ReviewValidationError(
            f"{label} must be a lowercase SHA-256 hex digest."
        )
