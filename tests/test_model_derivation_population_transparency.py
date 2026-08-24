from __future__ import annotations

from modules.model_candidates.derivation_strategy import (
    LLM_ASSISTED_MODE,
    assess_model_derivation_strategy,
)
from modules.model_candidates.types import (
    ModelCandidateProjectionCoverage,
    ModelCandidateProjectionDisposition,
    ModelStructureProfileReference,
)


def _entry(
    identity: str,
    *,
    kind: str,
    disposition: str,
):
    return ModelCandidateProjectionDisposition(
        approved_input_id=identity,
        approved_input_kind=kind,
        disposition=disposition,
        reason_code="test",
        selected_rule_id=(
            "rule:test" if disposition == "mapped" else None
        ),
        candidate_rule_ids=(
            ("rule:test",)
            if disposition == "mapped"
            else ()
        ),
        rationale="test",
    )


def test_strategy_assessment_exposes_subject_and_relationship_populations():
    profile = ModelStructureProfileReference(
        profile_id="TEST_PROFILE",
        profile_version="1.0.0",
        profile_fingerprint="1" * 64,
    )
    coverage = ModelCandidateProjectionCoverage(
        project_id="120412",
        model_structure_profile_reference=profile,
        entries=(
            _entry(
                "AIN-000001",
                kind="element_statement",
                disposition="mapped",
            ),
            _entry(
                "AIN-000002",
                kind="element_statement",
                disposition="ambiguous",
            ),
            _entry(
                "AIN-000003",
                kind="element_statement",
                disposition="unmapped",
            ),
            _entry(
                "SRD-000001",
                kind="semantic_relationship",
                disposition="mapped",
            ),
            _entry(
                "SRD-000002",
                kind="semantic_relationship",
                disposition="unmapped",
            ),
            _entry(
                "SRD-000003",
                kind="semantic_relationship",
                disposition="intentionally_not_projected",
            ),
        ),
    )

    assessment = assess_model_derivation_strategy(
        coverage=coverage,
        predecessor_candidate_set=None,
        predecessor_review_decisions=(),
    )

    assert assessment.recommended_mode == LLM_ASSISTED_MODE

    assert assessment.approved_subject_count == 3
    assert assessment.approved_subject_mapped_count == 1
    assert assessment.approved_subject_ambiguous_count == 1
    assert assessment.approved_subject_unmapped_count == 1
    assert (
        assessment.approved_subject_intentionally_not_projected_count
        == 0
    )

    assert assessment.semantic_relationship_count == 3
    assert assessment.semantic_relationship_mapped_count == 1
    assert assessment.semantic_relationship_ambiguous_count == 0
    assert assessment.semantic_relationship_unmapped_count == 1
    assert (
        assessment
        .semantic_relationship_intentionally_not_projected_count
        == 1
    )

    assert "approved engineering information" in assessment.rationale
