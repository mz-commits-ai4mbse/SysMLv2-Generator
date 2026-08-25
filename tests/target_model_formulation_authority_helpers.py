from modules.target_model_formulation import (
    PRIMARY_SYNTAX_ROLE,
    PRIMARY_SYNTAX_SOURCE_ID,
    VALIDATED_FIXTURE_ROLE,
    create_formulation_candidate,
    create_formulation_review,
    create_reference_evidence,
    create_review_item,
)


def release_ref():
    return create_reference_evidence(
        source_id=PRIMARY_SYNTAX_SOURCE_ID,
        role=PRIMARY_SYNTAX_ROLE,
        locator="external/sysml-v2-release/",
        evidence_note="Primary syntax authority.",
    )


def fixture_ref():
    return create_reference_evidence(
        source_id="SFX-C6C3-001",
        role=VALIDATED_FIXTURE_ROLE,
        locator="context/sysml/fixtures/c6c3/stakeholder_role_part_definition.sysml",
        evidence_note="Validated standalone Part Definition fixture.",
    )


def formal_candidate(candidate_id, text):
    return create_formulation_candidate(
        candidate_id=candidate_id,
        relevance_outcome="materialize_formally",
        target_model_pattern_id="standalone_reusable_stakeholder_role_part_definition",
        target_notation_construct_id="TN_003",
        formulation_text=text,
        reference_evidence=(release_ref(), fixture_ref()),
        rationale="Reviewed standalone stakeholder role proposal.",
    )


def omit_candidate(candidate_id):
    return create_formulation_candidate(
        candidate_id=candidate_id,
        relevance_outcome="intentionally_not_materialized",
        target_model_pattern_id=None,
        target_notation_construct_id=None,
        formulation_text=None,
        reference_evidence=(release_ref(),),
        rationale="No faithful formal trace construct is locally authorized.",
    )


def unresolved_candidate(candidate_id):
    return create_formulation_candidate(
        candidate_id=candidate_id,
        relevance_outcome="unresolved_human_review",
        target_model_pattern_id=None,
        target_notation_construct_id=None,
        formulation_text=None,
        reference_evidence=(release_ref(),),
        rationale="More evidence required.",
        unresolved_questions=("Which target-model form is correct?",),
    )


def review_four():
    items = (
        create_review_item(
            subject_kind="element",
            authority_subject_id="IME-000001",
            current_engineering_type="stakeholder",
            current_target_representation="stakeholder",
            candidates=(formal_candidate("TFC-000001", "part def 'microscope operator';"),),
        ),
        create_review_item(
            subject_kind="element",
            authority_subject_id="IME-000003",
            current_engineering_type="stakeholder",
            current_target_representation="stakeholder",
            candidates=(formal_candidate("TFC-000002", "part def 'separate client application user';"),),
        ),
        create_review_item(
            subject_kind="relationship",
            authority_subject_id="IMR-000001",
            current_engineering_type="traces_to",
            current_target_representation="traces_to",
            candidates=(omit_candidate("TFC-000003"),),
        ),
        create_review_item(
            subject_kind="relationship",
            authority_subject_id="IMR-000003",
            current_engineering_type="traces_to",
            current_target_representation="traces_to",
            candidates=(omit_candidate("TFC-000004"),),
        ),
    )
    return create_formulation_review(
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
        items=items,
        created_at="2026-08-25T13:50:00Z",
    )
