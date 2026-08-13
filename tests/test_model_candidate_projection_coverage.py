"""Tests for H9.1-H9.3 projection coverage and strict compatibility."""

from dataclasses import replace

import pytest

from modules.approved_input.manifest import create_approved_input_manifest
from modules.approved_input.types import (
    ApprovedInputCanonicalContent,
    ApprovedInputRelationshipProperty,
    ApprovedInputRelationshipRepresentation,
)
from modules.model_candidates import (
    MODEL_CANDIDATE_PROJECTION_DISPOSITIONS,
    ModelCandidateDerivationError,
    ModelCandidateDerivationRequest,
    ModelCandidateReferenceError,
    ProfileDrivenModelCandidateDeriver,
    ProfileProjectionResolver,
    load_model_derivation_rules_reference,
    load_model_structure_profile,
    model_structure_profile_reference,
)
from modules.project_processing.types import ProcessingArtifactReference
from modules.project_workspace.types import FrameworkTemplateReference


PROJECT_ID = "318604"
A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64


def _artifact(number: int) -> ProcessingArtifactReference:
    return ProcessingArtifactReference(
        artifact_type="information_unit",
        artifact_id=f"IU-{number:06d}",
        content_fingerprint=A,
        repository_relative_path=(
            f"data/projects/{PROJECT_ID}/semantics/"
            f"information_units/IU-{number:06d}.json"
        ),
    )


def _relationship(
    *,
    intent: str = "allocated_to",
) -> ApprovedInputRelationshipRepresentation:
    return ApprovedInputRelationshipRepresentation(
        source_subject_key="subject.source",
        target_subject_key="subject.target",
        semantic_intent=intent,
        sysml_v2_construct="allocation",
        construct_properties=(
            ApprovedInputRelationshipProperty(
                name="direction",
                value="source_to_target",
            ),
        ),
        target_notation_profile_id="SYSIDE_SYSML_V2",
        target_notation_profile_version="1.0.0",
        textual_notation_preview="relationship preview",
        profile_validation_status="valid",
        profile_validation_fingerprint=E,
    )


def _input(
    number: int,
    *,
    kind: str = "element_statement",
    subject: str = "subject.source",
    title: str = "Source",
    classification: str | None = "System Requirement",
    framework: str | None = "System Requirements",
    information_type: str | None = "requirement",
    relationship: ApprovedInputRelationshipRepresentation | None = None,
):
    review_kind = {
        "element_statement": "element",
        "relationship_statement": "relationship",
        "human_clarification": "open_question",
    }[kind]
    return create_approved_input_manifest(
        project_id=PROJECT_ID,
        approved_input_id=f"AIN-{number:06d}",
        approved_input_kind=kind,
        canonical_content=ApprovedInputCanonicalContent(
            title=title,
            primary_text=f"{title} reviewed engineering information.",
            description=f"{title} reviewed description.",
            information_type=information_type,
            modality="shall",
            epistemic_status="reviewed",
        ),
        selected_classification=classification,
        selected_framework_assignment=framework,
        selected_terminology_assignment="requirement",
        selected_source_assignments=("SRC-000001",),
        selected_relationship_representation=relationship,
        stable_subject_key=subject,
        review_document_id=f"RVD-{number:06d}",
        review_document_version_id=f"RVV-{number:06d}",
        review_revision_id=f"RVR-{number:06d}",
        review_item_id=f"RIT-{number:06d}",
        review_item_kind=review_kind,
        review_item_fingerprint=A,
        finalized_artifact_set_fingerprint=B,
        finalization_decision_id=f"HRD-{number:06d}",
        finalization_decision_fingerprint=C,
        finalization_validation_fingerprint=D,
        source_id="SRC-000001",
        source_sha256=E,
        processing_run_id=f"RUN-{number:06d}",
        attempt_id="ATT-000001",
        primary_artifact_reference=_artifact(number),
        supporting_artifact_references=(),
        proposal_references=(),
        created_at="2026-08-13T14:00:00Z",
    )


def _setup():
    profile = load_model_structure_profile()
    rules = load_model_derivation_rules_reference()
    deriver = ProfileDrivenModelCandidateDeriver(
        profile=profile,
        derivation_rules_reference=rules,
    )
    resolver = ProfileProjectionResolver(profile=profile)
    return profile, rules, deriver, resolver


def _request(inputs):
    profile, rules, _, _ = _setup()
    return ModelCandidateDerivationRequest(
        project_id=PROJECT_ID,
        approved_inputs=tuple(inputs),
        framework_template_reference=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        model_structure_profile_reference=(
            model_structure_profile_reference(profile)
        ),
        derivation_rules_reference=rules,
        predecessor_candidate_set=None,
    )


def test_projection_disposition_vocabulary_is_exact():
    assert MODEL_CANDIDATE_PROJECTION_DISPOSITIONS == frozenset(
        {
            "mapped",
            "ambiguous",
            "unmapped",
            "intentionally_not_projected",
        }
    )


def test_mixed_snapshot_has_complete_explicit_coverage():
    _, _, deriver, _ = _setup()
    mapped = _input(1)
    ambiguous = _input(
        2,
        subject="subject.function",
        title="Function",
        classification="Function",
        framework=None,
        information_type="function",
    )
    unmapped = _input(
        3,
        subject="subject.mystery",
        title="Mystery",
        classification="Mystery",
        framework=None,
        information_type="mystery",
    )
    clarification = _input(
        4,
        kind="human_clarification",
        subject="clarification.one",
        title="Clarification",
        classification=None,
        framework=None,
        information_type=None,
    )

    coverage = deriver.assess_projection_coverage(
        _request((mapped, ambiguous, unmapped, clarification))
    )

    assert coverage.total_count == 4
    assert coverage.mapped_count == 1
    assert coverage.ambiguous_count == 1
    assert coverage.unmapped_count == 1
    assert coverage.intentionally_not_projected_count == 1
    assert coverage.is_complete
    assert tuple(
        item.approved_input_id for item in coverage.entries
    ) == (
        "AIN-000001",
        "AIN-000002",
        "AIN-000003",
        "AIN-000004",
    )
    assert coverage.unresolved_approved_input_ids == (
        "AIN-000002",
        "AIN-000003",
    )


def test_element_coverage_exposes_selected_and_candidate_rules():
    _, _, deriver, _ = _setup()

    mapped = deriver.assess_projection_coverage(
        _request((_input(1),))
    ).entries[0]
    assert mapped.disposition == "mapped"
    assert mapped.selected_rule_id == "ELEMENT_SYSTEM_REQUIREMENT"
    assert mapped.candidate_rule_ids == (
        "ELEMENT_SYSTEM_REQUIREMENT",
    )

    ambiguous = deriver.assess_projection_coverage(
        _request(
            (
                _input(
                    2,
                    classification="Function",
                    framework=None,
                    information_type="function",
                ),
            )
        )
    ).entries[0]
    assert ambiguous.disposition == "ambiguous"
    assert ambiguous.selected_rule_id is None
    assert set(ambiguous.candidate_rule_ids) == {
        "ELEMENT_SUBSYSTEM_FUNCTION",
        "ELEMENT_SYSTEM_FUNCTION",
    }


def test_human_clarification_is_explicitly_not_projected():
    _, _, deriver, _ = _setup()
    clarification = _input(
        1,
        kind="human_clarification",
        classification=None,
        framework=None,
        information_type=None,
    )

    coverage = deriver.assess_projection_coverage(
        _request((clarification,))
    )
    entry = coverage.entries[0]
    assert entry.disposition == "intentionally_not_projected"
    assert entry.reason_code == "context_only_human_clarification"

    plan = deriver.derive(_request((clarification,)))
    assert plan.element_drafts == ()
    assert plan.relationship_drafts == ()


def test_strict_deterministic_path_still_maps_supported_input():
    _, _, deriver, _ = _setup()
    plan = deriver.derive(_request((_input(1),)))
    assert len(plan.element_drafts) == 1
    draft = plan.element_drafts[0]
    assert draft.model_area == "system.requirements"
    assert draft.element_type == "system_requirement"
    assert draft.support_level == "supported"


@pytest.mark.parametrize(
    ("approved", "expected_disposition"),
    [
        (
            _input(
                1,
                classification="Function",
                framework=None,
                information_type="function",
            ),
            "ambiguous",
        ),
        (
            _input(
                2,
                classification="Mystery",
                framework=None,
                information_type="mystery",
            ),
            "unmapped",
        ),
    ],
)
def test_strict_path_still_fails_closed_for_unresolved_elements(
    approved,
    expected_disposition,
):
    _, _, deriver, _ = _setup()
    coverage = deriver.assess_projection_coverage(
        _request((approved,))
    )
    assert coverage.entries[0].disposition == expected_disposition

    with pytest.raises(ModelCandidateDerivationError):
        deriver.derive(_request((approved,)))


def test_relationship_coverage_distinguishes_supported_and_unknown_semantics():
    _, _, deriver, _ = _setup()

    supported = _input(
        1,
        kind="relationship_statement",
        classification=None,
        framework=None,
        information_type="relationship",
        relationship=_relationship(intent="allocated_to"),
    )
    unknown = _input(
        2,
        kind="relationship_statement",
        classification=None,
        framework=None,
        information_type="relationship",
        relationship=_relationship(intent="mystery_relation"),
    )

    coverage = deriver.assess_projection_coverage(
        _request((supported, unknown))
    )
    assert tuple(item.disposition for item in coverage.entries) == (
        "mapped",
        "unmapped",
    )
    assert coverage.entries[1].reason_code == (
        "unsupported_relationship_semantic"
    )

    with pytest.raises(ModelCandidateDerivationError):
        deriver.derive(_request((supported, unknown)))


def test_resolver_rejects_duplicate_or_cross_project_snapshot():
    _, _, _, resolver = _setup()
    approved = _input(1)

    with pytest.raises(ModelCandidateDerivationError):
        resolver.assess_snapshot(
            project_id=PROJECT_ID,
            approved_inputs=(approved, approved),
        )

    foreign = replace(approved, project_id="999999")
    with pytest.raises(ModelCandidateDerivationError):
        resolver.assess_snapshot(
            project_id=PROJECT_ID,
            approved_inputs=(foreign,),
        )


def test_projection_coverage_preserves_profile_binding_validation():
    profile, _, deriver, _ = _setup()
    request = _request((_input(1),))
    bad = replace(
        request,
        model_structure_profile_reference=replace(
            model_structure_profile_reference(profile),
            profile_fingerprint="f" * 64,
        ),
    )

    with pytest.raises(ModelCandidateReferenceError):
        deriver.assess_projection_coverage(bad)
