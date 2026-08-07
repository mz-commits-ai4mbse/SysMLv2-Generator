"""Tests for the immutable Approved Input Manifest contract."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
import json

import pytest

from modules.approved_input.errors import (
    ApprovedInputIntegrityError,
    ApprovedInputValidationError,
)
from modules.approved_input.manifest import (
    APPROVED_INPUT_MANIFEST_SCHEMA_VERSION,
    approved_input_manifest_from_json,
    approved_input_manifest_to_dict,
    approved_input_manifest_to_json,
    calculate_approved_input_manifest_fingerprint,
    create_approved_input_manifest,
    parse_approved_input_manifest,
    validate_approved_input_manifest,
)
from modules.approved_input.types import (
    ApprovedInputCanonicalContent,
    ApprovedInputManifest,
    ApprovedInputRelationshipProperty,
    ApprovedInputRelationshipRepresentation,
)
from modules.project_processing.types import ProcessingArtifactReference


PROJECT_ID = "318604"
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64


def _artifact_reference(
    artifact_id: str = "IU-000001",
    fingerprint: str = SHA_A,
) -> ProcessingArtifactReference:
    return ProcessingArtifactReference(
        artifact_type="information_unit",
        artifact_id=artifact_id,
        content_fingerprint=fingerprint,
        repository_relative_path=(
            f"data/projects/{PROJECT_ID}/semantics/"
            f"information_units/{artifact_id}.json"
        ),
    )


def _canonical_content() -> ApprovedInputCanonicalContent:
    return ApprovedInputCanonicalContent(
        title="System shall preserve traceability",
        primary_text=(
            "The system shall preserve exact review traceability."
        ),
        description="Reviewed engineering statement.",
        information_type="requirement",
        modality="shall",
        epistemic_status="reviewed",
    )


def _relationship() -> ApprovedInputRelationshipRepresentation:
    return ApprovedInputRelationshipRepresentation(
        source_subject_key="subject.source",
        target_subject_key="subject.target",
        semantic_intent="dependency",
        sysml_v2_construct="dependency",
        construct_properties=(
            ApprovedInputRelationshipProperty(
                name="zeta",
                value="2",
            ),
            ApprovedInputRelationshipProperty(
                name="alpha",
                value="1",
            ),
        ),
        target_notation_profile_id="SYSIDE_SYSML_V2",
        target_notation_profile_version="1.0.0",
        textual_notation_preview=(
            "dependency from 'Source' to 'Target';"
        ),
        profile_validation_status="valid",
        profile_validation_fingerprint=SHA_E,
    )


def _manifest(
    *,
    approved_input_kind: str = "element_statement",
) -> ApprovedInputManifest:
    review_item_kind = {
        "element_statement": "element",
        "relationship_statement": "relationship",
        "human_clarification": "open_question",
    }[approved_input_kind]

    relationship = (
        _relationship()
        if approved_input_kind == "relationship_statement"
        else None
    )

    return create_approved_input_manifest(
        project_id=PROJECT_ID,
        approved_input_id="AIN-000001",
        approved_input_kind=approved_input_kind,
        canonical_content=_canonical_content(),
        selected_classification="System Requirement",
        selected_framework_assignment="System Requirements",
        selected_terminology_assignment="requirement",
        selected_source_assignments=(
            "SRC-000002",
            "SRC-000001",
        ),
        selected_relationship_representation=relationship,
        stable_subject_key="requirement.traceability",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        review_item_id="RIT-000001",
        review_item_kind=review_item_kind,
        review_item_fingerprint=SHA_A,
        finalized_artifact_set_fingerprint=SHA_B,
        finalization_decision_id="HRD-000001",
        finalization_decision_fingerprint=SHA_C,
        finalization_validation_fingerprint=SHA_D,
        source_id="SRC-000001",
        source_sha256=SHA_E,
        processing_run_id="RUN-000001",
        attempt_id="ATT-000001",
        primary_artifact_reference=_artifact_reference(),
        supporting_artifact_references=(
            _artifact_reference("IU-000003", SHA_C),
            _artifact_reference("IU-000002", SHA_B),
        ),
        proposal_references=(
            "proposal-z",
            "proposal-a",
        ),
        created_at="2026-08-07T08:30:00Z",
    )


def test_manifest_types_are_frozen_and_slotted() -> None:
    data_types = (
        ApprovedInputCanonicalContent,
        ApprovedInputRelationshipProperty,
        ApprovedInputRelationshipRepresentation,
        ApprovedInputManifest,
    )

    for data_type in data_types:
        assert data_type.__dataclass_params__.frozen
        assert data_type.__slots__

    manifest = _manifest()

    with pytest.raises(FrozenInstanceError):
        manifest.approved_input_id = "AIN-000002"


def test_manifest_field_contract_is_explicit() -> None:
    names = {field.name for field in fields(ApprovedInputManifest)}

    assert names == {
        "schema_version",
        "project_id",
        "approved_input_id",
        "approved_input_kind",
        "authority_state",
        "canonical_content",
        "selected_classification",
        "selected_framework_assignment",
        "selected_terminology_assignment",
        "selected_source_assignments",
        "selected_relationship_representation",
        "stable_subject_key",
        "review_document_id",
        "review_document_version_id",
        "review_revision_id",
        "review_item_id",
        "review_item_kind",
        "review_item_fingerprint",
        "finalized_artifact_set_fingerprint",
        "finalization_decision_id",
        "finalization_decision_fingerprint",
        "finalization_validation_fingerprint",
        "source_id",
        "source_sha256",
        "processing_run_id",
        "attempt_id",
        "primary_artifact_reference",
        "supporting_artifact_references",
        "proposal_references",
        "created_at",
        "content_fingerprint",
    }


def test_create_manifest_sets_initial_authority_and_normalizes_order() -> None:
    manifest = _manifest()

    assert manifest.schema_version == APPROVED_INPUT_MANIFEST_SCHEMA_VERSION
    assert manifest.authority_state == "active"
    assert manifest.selected_source_assignments == (
        "SRC-000001",
        "SRC-000002",
    )
    assert manifest.proposal_references == (
        "proposal-a",
        "proposal-z",
    )
    assert tuple(
        reference.artifact_id
        for reference in manifest.supporting_artifact_references
    ) == (
        "IU-000002",
        "IU-000003",
    )
    assert len(manifest.content_fingerprint) == 64


def test_relationship_manifest_normalizes_properties() -> None:
    manifest = _manifest(
        approved_input_kind="relationship_statement"
    )

    relationship = manifest.selected_relationship_representation
    assert relationship is not None
    assert tuple(
        property_.name
        for property_ in relationship.construct_properties
    ) == ("alpha", "zeta")


def test_manifest_round_trip_is_deterministic() -> None:
    manifest = _manifest()

    text = approved_input_manifest_to_json(manifest)
    assert text.endswith("\n")
    assert approved_input_manifest_from_json(text) == manifest
    assert (
        approved_input_manifest_to_json(
            approved_input_manifest_from_json(text)
        )
        == text
    )


def test_manifest_dict_is_json_ready() -> None:
    payload = approved_input_manifest_to_dict(_manifest())

    assert isinstance(payload["selected_source_assignments"], list)
    assert isinstance(payload["supporting_artifact_references"], list)
    json.dumps(payload)


def test_manifest_fingerprint_is_deterministic() -> None:
    manifest = _manifest()

    assert (
        calculate_approved_input_manifest_fingerprint(manifest)
        == manifest.content_fingerprint
    )
    assert _manifest().content_fingerprint == manifest.content_fingerprint


def test_tampered_manifest_fingerprint_is_rejected() -> None:
    manifest = replace(
        _manifest(),
        selected_classification="Stakeholder Requirement",
    )

    with pytest.raises(ApprovedInputIntegrityError):
        validate_approved_input_manifest(manifest)


def test_manifest_must_record_initial_active_state() -> None:
    manifest = replace(_manifest(), authority_state="revoked")

    with pytest.raises(
        ApprovedInputValidationError,
        match="initial authority_state as active",
    ):
        validate_approved_input_manifest(manifest)


@pytest.mark.parametrize(
    ("kind", "review_kind"),
    (
        ("element_statement", "relationship"),
        ("relationship_statement", "element"),
        ("human_clarification", "element"),
    ),
)
def test_approved_input_kind_must_match_review_item_kind(
    kind: str,
    review_kind: str,
) -> None:
    manifest = _manifest(approved_input_kind=kind)
    manifest = replace(
        manifest,
        review_item_kind=review_kind,
    )

    with pytest.raises(ApprovedInputValidationError):
        validate_approved_input_manifest(manifest)


def test_relationship_statement_requires_profile_valid_representation() -> None:
    manifest = _manifest(
        approved_input_kind="relationship_statement"
    )
    manifest = replace(
        manifest,
        selected_relationship_representation=None,
    )

    with pytest.raises(ApprovedInputValidationError):
        validate_approved_input_manifest(manifest)


def test_non_relationship_input_rejects_relationship_representation() -> None:
    manifest = _manifest()
    manifest = replace(
        manifest,
        selected_relationship_representation=_relationship(),
    )

    with pytest.raises(ApprovedInputValidationError):
        validate_approved_input_manifest(manifest)


def test_invalid_relationship_profile_status_is_rejected() -> None:
    manifest = _manifest(
        approved_input_kind="relationship_statement"
    )
    relationship = manifest.selected_relationship_representation
    assert relationship is not None

    manifest = replace(
        manifest,
        selected_relationship_representation=replace(
            relationship,
            profile_validation_status="invalid",
        ),
    )

    with pytest.raises(ApprovedInputValidationError):
        validate_approved_input_manifest(manifest)


def test_duplicate_proposal_references_are_rejected() -> None:
    with pytest.raises(ApprovedInputValidationError):
        create_approved_input_manifest(
            **{
                **_creation_arguments(),
                "proposal_references": (
                    "proposal-a",
                    "proposal-a",
                ),
            }
        )


def _creation_arguments() -> dict[str, object]:
    return {
        "project_id": PROJECT_ID,
        "approved_input_id": "AIN-000001",
        "approved_input_kind": "element_statement",
        "canonical_content": _canonical_content(),
        "selected_classification": "System Requirement",
        "selected_framework_assignment": "System Requirements",
        "selected_terminology_assignment": "requirement",
        "selected_source_assignments": ("SRC-000001",),
        "selected_relationship_representation": None,
        "stable_subject_key": "requirement.traceability",
        "review_document_id": "RVD-000001",
        "review_document_version_id": "RVV-000001",
        "review_revision_id": "RVR-000001",
        "review_item_id": "RIT-000001",
        "review_item_kind": "element",
        "review_item_fingerprint": SHA_A,
        "finalized_artifact_set_fingerprint": SHA_B,
        "finalization_decision_id": "HRD-000001",
        "finalization_decision_fingerprint": SHA_C,
        "finalization_validation_fingerprint": SHA_D,
        "source_id": "SRC-000001",
        "source_sha256": SHA_E,
        "processing_run_id": "RUN-000001",
        "attempt_id": "ATT-000001",
        "primary_artifact_reference": _artifact_reference(),
        "supporting_artifact_references": (),
        "proposal_references": ("proposal-a",),
        "created_at": "2026-08-07T08:30:00Z",
    }


def test_parse_rejects_missing_or_unknown_fields() -> None:
    payload = approved_input_manifest_to_dict(_manifest())

    missing = dict(payload)
    missing.pop("source_sha256")

    with pytest.raises(ApprovedInputValidationError):
        parse_approved_input_manifest(missing)

    unexpected = dict(payload)
    unexpected["generation_ready"] = True

    with pytest.raises(ApprovedInputValidationError):
        parse_approved_input_manifest(unexpected)


def test_json_rejects_duplicate_keys() -> None:
    text = approved_input_manifest_to_json(_manifest())
    duplicate = text.replace(
        '  "project_id": "318604",',
        '  "project_id": "318604",\n'
        '  "project_id": "318604",',
        1,
    )

    with pytest.raises(
        ApprovedInputValidationError,
        match="Duplicate JSON key",
    ):
        approved_input_manifest_from_json(duplicate)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("project_id", "42"),
        ("approved_input_id", "AIN-000000"),
        ("review_document_id", "RVD-000000"),
        ("review_document_version_id", "RVV-000000"),
        ("review_revision_id", "RVR-000000"),
        ("review_item_id", "RIT-000000"),
        ("finalization_decision_id", "HRD-000000"),
        ("source_id", "SRC-000000"),
        ("processing_run_id", "RUN-000000"),
        ("attempt_id", "ATT-000000"),
        ("review_item_fingerprint", "not-a-sha"),
    ),
)
def test_invalid_identity_or_fingerprint_is_rejected(
    field_name: str,
    invalid_value: str,
) -> None:
    manifest = replace(
        _manifest(),
        **{field_name: invalid_value},
    )

    with pytest.raises(ApprovedInputValidationError):
        validate_approved_input_manifest(manifest)
