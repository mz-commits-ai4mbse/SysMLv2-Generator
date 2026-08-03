"""Tests for the immutable Review Document manifest."""

from __future__ import annotations

from dataclasses import replace
import json

import pytest

from modules.project_processing import (
    ProcessingArtifactReference,
    SemanticReferenceVersion,
)
from modules.project_workspace.types import (
    FrameworkTemplateReference,
)
from modules.review_workspace.document_manifest import (
    REVIEW_DOCUMENT_SCHEMA_VERSION,
    calculate_review_document_fingerprint,
    create_review_document,
    parse_review_document,
    review_document_from_json,
    review_document_to_dict,
    review_document_to_json,
    validate_review_document,
)
from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)


def _artifact_reference(
    *,
    artifact_type: str = "review_reports",
    artifact_id: str = "REPORT-001",
    fingerprint: str = "a" * 64,
    path: str = (
        "data/projects/000001/runs/RUN-000001/"
        "artifacts/review_reports/report.md"
    ),
) -> ProcessingArtifactReference:
    return ProcessingArtifactReference(
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        content_fingerprint=fingerprint,
        repository_relative_path=path,
    )


def _document():
    return create_review_document(
        project_id="000001",
        review_document_id="RVD-000001",
        source_id="SRC-000001",
        source_sha256="b" * 64,
        processing_run_id="RUN-000001",
        attempt_id="ATT-000001",
        primary_review_artifact_reference=(
            _artifact_reference()
        ),
        supporting_artifact_references=(
            _artifact_reference(
                artifact_type="agent_outputs",
                artifact_id="AGENT-001",
                fingerprint="c" * 64,
                path=(
                    "data/projects/000001/runs/RUN-000001/"
                    "artifacts/agent_outputs/agent.json"
                ),
            ),
        ),
        framework_template=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        semantic_reference_versions=(
            SemanticReferenceVersion(
                reference_system_id="TURING_CORE",
                reference_version="1.0.0",
            ),
        ),
        timestamp="2026-08-03T15:00:00Z",
    )


def test_create_review_document_is_fingerprinted() -> None:
    document = _document()

    assert document.schema_version == (
        REVIEW_DOCUMENT_SCHEMA_VERSION
    )
    assert len(document.content_fingerprint) == 64
    assert document.content_fingerprint == (
        calculate_review_document_fingerprint(document)
    )

    validate_review_document(document)


def test_review_document_round_trip_is_deterministic() -> None:
    document = _document()

    serialized = review_document_to_json(document)

    assert serialized.endswith("\n")
    assert review_document_from_json(serialized) == document
    assert review_document_to_json(
        review_document_from_json(serialized)
    ) == serialized


def test_review_document_dict_has_exact_fields() -> None:
    payload = review_document_to_dict(_document())

    assert set(payload) == {
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


def test_review_document_rejects_modified_content() -> None:
    document = _document()

    modified = replace(
        document,
        source_sha256="d" * 64,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="fingerprint",
    ):
        validate_review_document(modified)


@pytest.mark.parametrize(
    "field",
    (
        "project_id",
        "review_document_id",
        "source_id",
        "source_sha256",
        "processing_run_id",
        "attempt_id",
    ),
)
def test_review_document_rejects_invalid_identity_fields(
    field: str,
) -> None:
    document = _document()

    modified = replace(
        document,
        **{field: "INVALID"},
    )

    with pytest.raises(ReviewValidationError):
        validate_review_document(modified)


def test_primary_artifact_must_be_review_report() -> None:
    document = _document()

    modified = replace(
        document,
        primary_review_artifact_reference=(
            _artifact_reference(
                artifact_type="agent_outputs",
            )
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="review_reports",
    ):
        validate_review_document(modified)


def test_artifacts_must_remain_inside_project() -> None:
    document = _document()

    modified = replace(
        document,
        primary_review_artifact_reference=(
            _artifact_reference(
                path=(
                    "data/projects/000002/runs/RUN-000001/"
                    "artifacts/review_reports/report.md"
                )
            )
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="selected Project",
    ):
        validate_review_document(modified)


def test_artifact_references_must_be_unique() -> None:
    document = _document()

    modified = replace(
        document,
        supporting_artifact_references=(
            document.primary_review_artifact_reference,
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="unique",
    ):
        validate_review_document(modified)


def test_semantic_references_must_be_unique() -> None:
    document = _document()

    reference = document.semantic_reference_versions[0]

    modified = replace(
        document,
        semantic_reference_versions=(
            reference,
            reference,
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="unique",
    ):
        validate_review_document(modified)


def test_framework_template_is_strictly_validated() -> None:
    document = _document()

    modified = replace(
        document,
        framework_template=FrameworkTemplateReference(
            template_id="invalid template",
            template_version="1",
        ),
    )

    with pytest.raises(ReviewValidationError):
        validate_review_document(modified)


def test_parse_rejects_missing_and_unknown_fields() -> None:
    payload = review_document_to_dict(_document())

    missing = dict(payload)
    missing.pop("source_id")

    with pytest.raises(
        ReviewValidationError,
        match="missing",
    ):
        parse_review_document(missing)

    unknown = {
        **payload,
        "unexpected": True,
    }

    with pytest.raises(
        ReviewValidationError,
        match="unknown",
    ):
        parse_review_document(unknown)


def test_json_rejects_duplicate_object_keys() -> None:
    text = review_document_to_json(_document())

    duplicated = text.replace(
        '"project_id": "000001",',
        (
            '"project_id": "000001",\n'
            '  "project_id": "000001",'
        ),
        1,
    )

    with pytest.raises(
        ReviewValidationError,
        match="Duplicate JSON object key",
    ):
        review_document_from_json(duplicated)


def test_json_rejects_invalid_input() -> None:
    with pytest.raises(ReviewValidationError):
        review_document_from_json(None)

    with pytest.raises(ReviewValidationError):
        review_document_from_json("{invalid")


def test_parse_rejects_invalid_nested_artifact() -> None:
    payload = review_document_to_dict(_document())

    primary = dict(
        payload["primary_review_artifact_reference"]
    )
    primary["content_fingerprint"] = "invalid"

    payload["primary_review_artifact_reference"] = primary

    with pytest.raises(ReviewValidationError):
        parse_review_document(payload)


def test_serialized_fingerprint_is_not_self_referential() -> None:
    document = _document()
    payload = review_document_to_dict(document)

    payload_without_fingerprint = dict(payload)
    payload_without_fingerprint.pop("content_fingerprint")

    canonical = json.dumps(
        payload_without_fingerprint,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    assert canonical
    assert document.content_fingerprint not in canonical
