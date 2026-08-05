"""Public API tests for P4 evidence-reference binding."""

from __future__ import annotations

import modules.review_workspace as review_workspace


def test_p4_evidence_reference_adapter_is_publicly_importable() -> None:
    assert (
        review_workspace
        .P4InformationUnitEvidenceReferences
        is not None
    )
    assert (
        review_workspace
        .P4StructuredEvidenceReferenceSet
        is not None
    )
    assert callable(
        review_workspace
        .construct_p4_evidence_references
    )


def test_p4_evidence_reference_roles_are_public() -> None:
    assert (
        review_workspace
        .P4_INFORMATION_UNIT_EVIDENCE_ROLE
        == "p4_information_unit"
    )
    assert (
        review_workspace
        .P4_TERMINOLOGY_MAPPING_EVIDENCE_ROLE
        == "p4_terminology_mapping"
    )
    assert (
        review_workspace
        .P4_FRAMEWORK_ASSIGNMENT_EVIDENCE_ROLE
        == "p4_framework_assignment"
    )
    assert (
        review_workspace
        .P4_HUMAN_REVIEW_EVIDENCE_ROLE
        == "p4_human_review_decision"
    )


def test_p4_evidence_reference_exports_are_declared() -> None:
    required_exports = {
        "P4_INFORMATION_UNIT_EVIDENCE_ROLE",
        "P4_TERMINOLOGY_MAPPING_EVIDENCE_ROLE",
        "P4_FRAMEWORK_ASSIGNMENT_EVIDENCE_ROLE",
        "P4_HUMAN_REVIEW_EVIDENCE_ROLE",
        "P4InformationUnitEvidenceReferences",
        "P4StructuredEvidenceReferenceSet",
        "construct_p4_evidence_references",
    }

    assert required_exports <= set(
        review_workspace.__all__
    )
