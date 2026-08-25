from dataclasses import replace
from types import SimpleNamespace

from modules.target_model_formulation.evidence import (
    LocalReferenceAssessment,
)
from modules.target_model_formulation.proposals import (
    build_blk006_formulation_review,
)


def _snapshot():
    return SimpleNamespace(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
        content_fingerprint="1" * 64,
        final_model_review_decision_id="FAD-000001",
        final_model_review_decision_fingerprint="2" * 64,
        elements=(
            SimpleNamespace(
                internal_model_element_id="IME-000001",
                element_type="stakeholder",
            ),
            SimpleNamespace(
                internal_model_element_id="IME-000002",
                element_type="system_requirement",
            ),
            SimpleNamespace(
                internal_model_element_id="IME-000003",
                element_type="stakeholder",
            ),
        ),
        relationships=(
            SimpleNamespace(
                internal_model_relationship_id="IMR-000001",
                semantic_intent="traces_to",
            ),
            SimpleNamespace(
                internal_model_relationship_id="IMR-000002",
                semantic_intent="dependency",
            ),
            SimpleNamespace(
                internal_model_relationship_id="IMR-000003",
                semantic_intent="traces_to",
            ),
        ),
    )


def _assessment(trace_matches=0):
    return LocalReferenceAssessment(
        sysml_release_root="external/sysml-v2-release",
        sysml_release_fingerprint="3" * 64,
        stakeholder_part_usage_found=True,
        stakeholder_evidence_locator=(
            "sysml.library/Systems Library/SysML.sysml:364"
        ),
        stakeholder_evidence_note=(
            "ownedStakeholderParameter is PartUsage."
        ),
        trace_syntax_match_count=trace_matches,
        trace_evidence_locator=(
            "external/sysml-v2-release:repository-wide-trace-scan"
        ),
        trace_evidence_note=(
            "No formal trace syntax evidence found."
        ),
        tn003_allows_stakeholder=False,
        tn004_allows_stakeholder=False,
        target_notation_fingerprint="4" * 64,
    )


def _profile():
    return {
        "profile_id": "TURING_SYSML_V2_TARGET_MODEL",
        "profile_version": "0.1.0-draft",
        "status": "draft_template",
    }


def test_builder_creates_only_four_current_blk006_review_items():
    review = build_blk006_formulation_review(
        snapshot=_snapshot(),
        assessment=_assessment(),
        target_model_profile=_profile(),
        review_id="TFR-000001",
        created_at="2026-08-25T13:45:00Z",
    )

    assert len(review.items) == 4
    assert {
        (item.subject_kind, item.authority_subject_id)
        for item in review.items
    } == {
        ("element", "IME-000001"),
        ("element", "IME-000003"),
        ("relationship", "IMR-000001"),
        ("relationship", "IMR-000003"),
    }


def test_stakeholder_candidates_remain_unresolved_without_authorized_target_notation():
    review = build_blk006_formulation_review(
        snapshot=_snapshot(),
        assessment=_assessment(),
        target_model_profile=_profile(),
        review_id="TFR-000001",
        created_at="2026-08-25T13:45:00Z",
    )

    stakeholder = next(
        item for item in review.items
        if item.authority_subject_id == "IME-000001"
    )
    candidate = stakeholder.candidates[0]

    assert candidate.relevance_outcome == "unresolved_human_review"
    assert candidate.target_model_pattern_id is None
    assert candidate.target_notation_construct_id is None
    assert "Part Definition" in candidate.unresolved_questions[0]
    assert "Part Usage" in candidate.unresolved_questions[0]


def test_traces_to_candidates_are_intentionally_not_materialized_when_no_syntax_exists():
    review = build_blk006_formulation_review(
        snapshot=_snapshot(),
        assessment=_assessment(trace_matches=0),
        target_model_profile=_profile(),
        review_id="TFR-000001",
        created_at="2026-08-25T13:45:00Z",
    )

    trace = next(
        item for item in review.items
        if item.authority_subject_id == "IMR-000001"
    )
    candidate = trace.candidates[0]

    assert (
        candidate.relevance_outcome
        == "intentionally_not_materialized"
    )
    assert candidate.target_model_pattern_id is None
    assert candidate.target_notation_construct_id is None
    assert "dependency" in candidate.rationale
    assert "satisfy" in candidate.rationale


def test_dependency_is_not_reopened_by_the_bridge():
    review = build_blk006_formulation_review(
        snapshot=_snapshot(),
        assessment=_assessment(),
        target_model_profile=_profile(),
        review_id="TFR-000001",
        created_at="2026-08-25T13:45:00Z",
    )

    assert all(
        item.authority_subject_id != "IMR-000002"
        for item in review.items
    )


def test_trace_lexical_matches_fail_closed_to_human_review():
    review = build_blk006_formulation_review(
        snapshot=_snapshot(),
        assessment=_assessment(trace_matches=2),
        target_model_profile=_profile(),
        review_id="TFR-000001",
        created_at="2026-08-25T13:45:00Z",
    )

    trace = next(
        item for item in review.items
        if item.authority_subject_id == "IMR-000001"
    )
    assert (
        trace.candidates[0].relevance_outcome
        == "unresolved_human_review"
    )


def test_validated_stakeholder_policy_proposes_formal_tn003_part_definition():
    snapshot = _snapshot()
    snapshot.elements[0].name = "microscope operator"
    snapshot.elements[2].name = "remote specialist"

    assessment = replace(
        _assessment(),
        tn003_allows_stakeholder=True,
        stakeholder_fixture_validated=True,
        stakeholder_fixture_id="SFX-C6C3-001",
        stakeholder_fixture_locator=(
            "context/sysml/fixtures/c6c3/"
            "stakeholder_role_part_definition.sysml"
        ),
        stakeholder_fixture_status=(
            "passed_with_nonblocking_warning"
        ),
    )

    review = build_blk006_formulation_review(
        snapshot=snapshot,
        assessment=assessment,
        target_model_profile=_profile(),
        review_id="TFR-000001",
        created_at="2026-08-25T13:45:00Z",
    )

    stakeholder = next(
        item for item in review.items
        if item.authority_subject_id == "IME-000001"
    )
    candidate = stakeholder.candidates[0]

    assert candidate.relevance_outcome == "materialize_formally"
    assert candidate.target_model_pattern_id == (
        "standalone_reusable_stakeholder_role_part_definition"
    )
    assert candidate.target_notation_construct_id == "TN_003"
    assert candidate.formulation_text == (
        "part def 'microscope operator';"
    )
    assert {
        evidence.role for evidence in candidate.reference_evidence
    } >= {
        "primary_language_and_syntax_reference",
        "validated_syntax_fixture",
        "non_normative_modeling_pattern_reference",
        "project_modeling_context_reference",
        "target_model_formulation_guidance",
    }
    assert "No HumanRole supertype" in candidate.rationale


def test_tn003_without_validated_fixture_still_fails_closed():
    assessment = replace(
        _assessment(),
        tn003_allows_stakeholder=True,
        stakeholder_fixture_validated=False,
    )

    review = build_blk006_formulation_review(
        snapshot=_snapshot(),
        assessment=assessment,
        target_model_profile=_profile(),
        review_id="TFR-000001",
        created_at="2026-08-25T13:45:00Z",
    )

    stakeholder = next(
        item for item in review.items
        if item.authority_subject_id == "IME-000001"
    )
    assert (
        stakeholder.candidates[0].relevance_outcome
        == "unresolved_human_review"
    )
