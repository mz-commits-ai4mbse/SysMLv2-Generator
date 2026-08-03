"""Tests for immutable Review Revision manifests."""

from __future__ import annotations

from dataclasses import replace

import pytest

from modules.project_processing import (
    ProcessingArtifactReference,
)
from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from modules.review_workspace.item_manifest import (
    create_review_item,
)
from modules.review_workspace.revision_manifest import (
    REVIEW_REVISION_SCHEMA_VERSION,
    calculate_review_revision_fingerprint,
    create_review_revision,
    parse_review_revision,
    review_revision_filename,
    review_revision_from_json,
    review_revision_to_dict,
    review_revision_to_json,
    validate_review_revision,
)
from modules.review_workspace.types import (
    ReviewDimensionSelection,
    ReviewEvidenceReference,
    ReviewItemContent,
    ReviewProposalReference,
)


def _artifact(
    *,
    project_id: str = "000001",
    artifact_id: str = "AGENT-001",
) -> ProcessingArtifactReference:
    return ProcessingArtifactReference(
        artifact_type="agent_outputs",
        artifact_id=artifact_id,
        content_fingerprint="a" * 64,
        repository_relative_path=(
            f"data/projects/{project_id}/runs/"
            "RUN-000001/artifacts/agent_outputs/"
            f"{artifact_id}.json"
        ),
    )


def _review_item(
    *,
    project_id: str = "000001",
    review_document_id: str = "RVD-000001",
    review_document_version_id: str = "RVV-000001",
    review_item_id: str = "RIT-000001",
    stable_subject_key: str = "upload-engineering-source",
):
    proposal = ReviewProposalReference(
        artifact_reference=_artifact(
            project_id=project_id,
        ),
        agent_id="AGENT_001",
        persona_id="systems_engineer",
        proposal_id="CAND-001",
        proposal_content_fingerprint="b" * 64,
        original_report_locator=(
            "candidate-elements/CAND-001"
        ),
        review_state="selected",
    )

    evidence = ReviewEvidenceReference(
        artifact_reference=_artifact(
            project_id=project_id,
            artifact_id="EVIDENCE-001",
        ),
        evidence_role="source_evidence",
        evidence_locator="source-information/SI-001",
        evidence_content_fingerprint="c" * 64,
    )

    content = ReviewItemContent(
        title="Upload engineering source",
        primary_text=(
            "The system shall accept an engineering source."
        ),
        description=None,
        information_type="requirement",
        modality="shall",
        epistemic_status="asserted",
        human_rationale=None,
        human_confidence="high",
        relationship_representation=None,
    )

    outcome = ReviewDimensionSelection(
        dimension="review_outcome",
        selected_values=("accepted_as_generated",),
        value_origin="item_override",
        source_reference_ids=("CAND-001",),
        rationale=None,
        selected_by="reviewer@example.com",
        selected_at="2026-08-03T16:00:00Z",
    )

    return create_review_item(
        project_id=project_id,
        review_document_id=review_document_id,
        review_document_version_id=(
            review_document_version_id
        ),
        review_item_id=review_item_id,
        review_item_kind="element",
        stable_subject_key=stable_subject_key,
        section="elements",
        lineage_operation="original",
        derived_from_review_item_ids=(),
        original_report_locator=(
            "candidate-elements/CAND-001"
        ),
        proposal_references=(proposal,),
        source_evidence_references=(evidence,),
        consensus_evidence_references=(),
        current_content=content,
        dimension_selections=(outcome,),
        effective_review_outcome=(
            "accepted_as_generated"
        ),
    )


def _first_revision():
    return create_review_revision(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        revision_sequence=1,
        predecessor_revision_id=None,
        review_items=(_review_item(),),
        scoped_review_action_ids=("SRA-000001",),
        created_by="reviewer@example.com",
        timestamp="2026-08-03T16:00:00Z",
    )


def _successor_revision():
    return create_review_revision(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000002",
        revision_sequence=2,
        predecessor_revision_id="RVR-000001",
        review_items=(_review_item(),),
        scoped_review_action_ids=("SRA-000001",),
        created_by="reviewer@example.com",
        timestamp="2026-08-03T16:15:00Z",
    )


def test_create_review_revision_is_fingerprinted() -> None:
    revision = _first_revision()

    assert revision.schema_version == (
        REVIEW_REVISION_SCHEMA_VERSION
    )
    assert revision.revision_fingerprint == (
        calculate_review_revision_fingerprint(revision)
    )

    validate_review_revision(revision)


@pytest.mark.parametrize(
    "revision",
    (
        _first_revision(),
        _successor_revision(),
    ),
)
def test_review_revision_round_trip_is_deterministic(
    revision,
) -> None:
    serialized = review_revision_to_json(revision)

    assert serialized.endswith("\n")
    assert review_revision_from_json(serialized) == revision
    assert review_revision_to_json(
        review_revision_from_json(serialized)
    ) == serialized


def test_review_revision_dict_has_exact_fields() -> None:
    payload = review_revision_to_dict(_first_revision())

    assert set(payload) == {
        "schema_version",
        "project_id",
        "review_document_id",
        "review_document_version_id",
        "review_revision_id",
        "revision_sequence",
        "predecessor_revision_id",
        "review_items",
        "scoped_review_action_ids",
        "created_by",
        "created_at",
        "revision_fingerprint",
    }


def test_revision_filename_is_canonical() -> None:
    assert review_revision_filename(
        "RVR-000042"
    ) == "RVR-000042.json"

    with pytest.raises(ReviewValidationError):
        review_revision_filename("INVALID")


def test_revision_rejects_modified_content() -> None:
    revision = _first_revision()

    modified = replace(
        revision,
        created_by="other@example.com",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="fingerprint",
    ):
        validate_review_revision(modified)


def test_first_revision_rejects_predecessor() -> None:
    revision = _first_revision()

    modified = replace(
        revision,
        predecessor_revision_id="RVR-000001",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="must not have a predecessor",
    ):
        validate_review_revision(modified)


def test_successor_requires_predecessor() -> None:
    revision = _successor_revision()

    modified = replace(
        revision,
        predecessor_revision_id=None,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="requires predecessor_revision_id",
    ):
        validate_review_revision(modified)


def test_predecessor_must_be_earlier() -> None:
    revision = _successor_revision()

    modified = replace(
        revision,
        predecessor_revision_id="RVR-000003",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="earlier",
    ):
        validate_review_revision(modified)


def test_review_item_ids_must_be_unique() -> None:
    revision = _first_revision()
    item = revision.review_items[0]

    modified = replace(
        revision,
        review_items=(item, item),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="Review Item IDs",
    ):
        validate_review_revision(modified)


def test_stable_subject_keys_must_be_unique() -> None:
    revision = _first_revision()
    second_item = _review_item(
        review_item_id="RIT-000002",
    )

    modified = replace(
        revision,
        review_items=(
            revision.review_items[0],
            second_item,
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="stable_subject_key",
    ):
        validate_review_revision(modified)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        (
            "project_id",
            "000002",
            "project_id",
        ),
        (
            "review_document_id",
            "RVD-000002",
            "review_document_id",
        ),
        (
            "review_document_version_id",
            "RVV-000002",
            "review_document_version_id",
        ),
    ),
)
def test_review_items_must_match_revision_binding(
    field: str,
    value: str,
    message: str,
) -> None:
    revision = _first_revision()
    item = _review_item(**{field: value})

    modified = replace(
        revision,
        review_items=(item,),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match=message,
    ):
        validate_review_revision(modified)


def test_scoped_action_ids_must_be_unique() -> None:
    revision = _first_revision()

    modified = replace(
        revision,
        scoped_review_action_ids=(
            "SRA-000001",
            "SRA-000001",
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="unique",
    ):
        validate_review_revision(modified)


def test_scoped_action_ids_are_strictly_validated() -> None:
    revision = _first_revision()

    modified = replace(
        revision,
        scoped_review_action_ids=("INVALID",),
    )

    with pytest.raises(ReviewValidationError):
        validate_review_revision(modified)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("project_id", "INVALID"),
        ("review_document_id", "INVALID"),
        ("review_document_version_id", "INVALID"),
        ("review_revision_id", "INVALID"),
        ("revision_sequence", 0),
        ("revision_sequence", True),
        ("created_by", ""),
        ("created_at", "invalid"),
        ("revision_fingerprint", "invalid"),
    ),
)
def test_revision_rejects_invalid_fields(
    field: str,
    value: object,
) -> None:
    revision = _first_revision()

    modified = replace(
        revision,
        **{field: value},
    )

    with pytest.raises(
        (
            ReviewValidationError,
            ReviewIntegrityError,
        )
    ):
        validate_review_revision(modified)


def test_parse_rejects_missing_and_unknown_fields() -> None:
    payload = review_revision_to_dict(_first_revision())

    missing = dict(payload)
    missing.pop("created_by")

    with pytest.raises(
        ReviewValidationError,
        match="missing",
    ):
        parse_review_revision(missing)

    unknown = {
        **payload,
        "unexpected": True,
    }

    with pytest.raises(
        ReviewValidationError,
        match="unknown",
    ):
        parse_review_revision(unknown)


def test_parse_rejects_non_array_nested_fields() -> None:
    payload = review_revision_to_dict(_first_revision())

    payload["review_items"] = {}

    with pytest.raises(
        ReviewValidationError,
        match="review_items",
    ):
        parse_review_revision(payload)

    payload = review_revision_to_dict(_first_revision())
    payload["scoped_review_action_ids"] = {}

    with pytest.raises(
        ReviewValidationError,
        match="scoped_review_action_ids",
    ):
        parse_review_revision(payload)


def test_json_rejects_duplicate_keys() -> None:
    text = review_revision_to_json(_first_revision())

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
        review_revision_from_json(duplicated)


def test_json_rejects_invalid_input() -> None:
    with pytest.raises(ReviewValidationError):
        review_revision_from_json(None)

    with pytest.raises(ReviewValidationError):
        review_revision_from_json("{invalid")
