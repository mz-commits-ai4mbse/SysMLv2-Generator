import pytest

from modules.target_model_formulation import (
    APOLLO_REFERENCE_SOURCE_ID,
    PRIMARY_SYNTAX_ROLE,
    PRIMARY_SYNTAX_SOURCE_ID,
    VALIDATED_FIXTURE_ROLE,
    TargetModelFormulationError,
    create_formulation_candidate,
    create_formulation_review,
    create_reference_evidence,
    create_review_item,
)


def _release_ref():
    return create_reference_evidence(
        source_id=PRIMARY_SYNTAX_SOURCE_ID,
        role=PRIMARY_SYNTAX_ROLE,
        locator="external/sysml-v2-release/",
        evidence_note="Primary local SysML v2 release/specification evidence.",
    )


def _fixture_ref():
    return create_reference_evidence(
        source_id="LOCAL_SYSIDE_FIXTURE",
        role=VALIDATED_FIXTURE_ROLE,
        locator="tests/fixtures/sysml_generation/stakeholder_part_definition.sysml",
        evidence_note="Validated syntax fixture for the selected construct.",
    )


def _apollo_ref():
    return create_reference_evidence(
        source_id=APOLLO_REFERENCE_SOURCE_ID,
        role="non_normative_modeling_pattern_reference",
        locator="external/apollo11-sysml-v2/",
        evidence_note="Non-normative modeling-pattern evidence only.",
    )


def test_apollo_cannot_be_promoted_to_syntax_authority():
    with pytest.raises(
        TargetModelFormulationError,
        match="non-normative",
    ):
        create_reference_evidence(
            source_id=APOLLO_REFERENCE_SOURCE_ID,
            role=PRIMARY_SYNTAX_ROLE,
            locator="external/apollo11-sysml-v2/",
            evidence_note="invalid",
        )


def test_only_registered_release_repo_can_claim_primary_syntax_authority():
    with pytest.raises(
        TargetModelFormulationError,
        match="only be the registered release repository",
    ):
        create_reference_evidence(
            source_id="SOME_EXAMPLE_MODEL",
            role=PRIMARY_SYNTAX_ROLE,
            locator="example/",
            evidence_note="invalid",
        )


def test_formal_materialization_requires_release_and_validated_fixture_evidence():
    with pytest.raises(
        TargetModelFormulationError,
        match="validated syntax-fixture",
    ):
        create_formulation_candidate(
            candidate_id="TFC-000001",
            relevance_outcome="materialize_formally",
            target_model_pattern_id="stakeholder_role_definition",
            target_notation_construct_id="TN_003",
            formulation_text="microscope operator",
            reference_evidence=(_release_ref(), _apollo_ref()),
            rationale="Pattern is plausible but not yet syntax-validated.",
        )


def test_formal_materialization_may_use_non_normative_pattern_evidence_but_not_as_syntax():
    candidate = create_formulation_candidate(
        candidate_id="TFC-000001",
        relevance_outcome="materialize_formally",
        target_model_pattern_id="stakeholder_role_definition",
        target_notation_construct_id="TN_003",
        formulation_text="microscope operator",
        reference_evidence=(_release_ref(), _fixture_ref(), _apollo_ref()),
        rationale="Formal construct is separately grounded and validated.",
    )

    roles = {item.role for item in candidate.reference_evidence}
    assert PRIMARY_SYNTAX_ROLE in roles
    assert VALIDATED_FIXTURE_ROLE in roles
    assert "non_normative_modeling_pattern_reference" in roles


def test_intentional_non_materialization_cannot_claim_notation_construct():
    with pytest.raises(
        TargetModelFormulationError,
        match="must not claim",
    ):
        create_formulation_candidate(
            candidate_id="TFC-000001",
            relevance_outcome="intentionally_not_materialized",
            target_model_pattern_id=None,
            target_notation_construct_id="TN_013",
            formulation_text=None,
            reference_evidence=(_release_ref(),),
            rationale="No semantically faithful relationship form is authorized.",
        )


def test_unresolved_candidate_requires_explicit_question():
    with pytest.raises(
        TargetModelFormulationError,
        match="unresolved questions",
    ):
        create_formulation_candidate(
            candidate_id="TFC-000001",
            relevance_outcome="unresolved_human_review",
            target_model_pattern_id=None,
            target_notation_construct_id=None,
            formulation_text=None,
            reference_evidence=(_release_ref(), _apollo_ref()),
            rationale="More target-model evidence is required.",
        )


def test_review_binds_exact_existing_c6_authority():
    candidate = create_formulation_candidate(
        candidate_id="TFC-000001",
        relevance_outcome="unresolved_human_review",
        target_model_pattern_id=None,
        target_notation_construct_id=None,
        formulation_text=None,
        reference_evidence=(_release_ref(), _apollo_ref()),
        rationale="Definition-vs-usage remains to be Human-authorized.",
        unresolved_questions=(
            "Should this Stakeholder role be a Part Definition or Part Usage?",
        ),
    )
    item = create_review_item(
        subject_kind="element",
        authority_subject_id="IME-000001",
        current_engineering_type="stakeholder",
        current_target_representation="stakeholder",
        candidates=(candidate,),
    )
    review = create_formulation_review(
        project_id="120412",
        review_id="TFR-000001",
        source_internal_engineering_model_id="IEM-000001",
        source_internal_engineering_model_fingerprint="1" * 64,
        final_model_review_decision_id="FAD-000001",
        final_model_review_decision_fingerprint="2" * 64,
        target_model_profile_id="TURING_SYSML_V2_TARGET_MODEL",
        target_model_profile_version="0.1.0-draft",
        target_model_profile_fingerprint="3" * 64,
        target_notation_fingerprint="4" * 64,
        items=(item,),
        created_at="2026-08-25T13:30:00Z",
    )

    assert review.source_internal_engineering_model_id == "IEM-000001"
    assert review.final_model_review_decision_id == "FAD-000001"
    assert review.items[0].authority_subject_id == "IME-000001"
    assert len(review.content_fingerprint) == 64
