from __future__ import annotations

from dataclasses import replace

import pytest

from modules.final_model_review import (
    FINAL_MODEL_REVIEW_DECISIONS,
    FINAL_MODEL_REVIEW_LIFECYCLE_STATES,
    FinalModelReviewIntegrityError,
    FinalModelReviewValidationError,
    create_evidence_reference,
    create_final_model_review_decision,
    create_final_model_review_decision_target,
    create_final_model_review_item,
    create_final_model_review_manifest,
    create_final_model_review_revision,
    create_generated_unit_reference,
    final_model_review_id_sequence,
    format_final_model_review_decision_id,
    format_final_model_review_id,
    format_final_model_review_item_id,
    format_final_model_review_revision_id,
    next_final_model_review_decision_id,
    next_final_model_review_id,
    next_final_model_review_item_id,
    next_final_model_review_revision_id,
    validate_final_model_review_decision,
    validate_final_model_review_id,
    validate_final_model_review_item,
    validate_final_model_review_manifest,
    validate_final_model_review_revision,
)


FP_A = "a" * 64
FP_B = "b" * 64
FP_C = "c" * 64
FP_D = "d" * 64


def _unit():
    return create_generated_unit_reference(
        generated_unit_id="GSU-000001",
        relative_path="generated_model.sysml",
        content_fingerprint=FP_A,
    )


def _evidence():
    return create_evidence_reference(
        evidence_type="agent_proposal",
        reference_id="agent_systems_engineer_run_01",
        content_fingerprint=FP_B,
    )


def _revision(*, status="valid", gate="passed", revision_id="FRV-000001"):
    return create_final_model_review_revision(
        project_id="000001",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id=revision_id,
        predecessor_revision_id=None,
        source_internal_engineering_model_id="IEM-000001",
        generated_artifact_set_fingerprint=FP_C,
        validation_result_fingerprint=FP_D,
        validation_status=status,
        publication_gate=gate,
        generated_units=(_unit(),),
        evidence_references=(_evidence(),),
        created_at="2026-08-14T10:00:00Z",
    )


def test_l1_identifier_contracts_and_sequencing():
    assert validate_final_model_review_id("FMR-000001") == "FMR-000001"
    assert final_model_review_id_sequence("FMR-000123") == 123
    assert format_final_model_review_id(7) == "FMR-000007"
    assert format_final_model_review_revision_id(7) == "FRV-000007"
    assert format_final_model_review_item_id(7) == "FRI-000007"
    assert format_final_model_review_decision_id(7) == "FRD-000007"


def test_l1_next_ids_follow_highest_and_do_not_gap_reuse():
    assert next_final_model_review_id(("FMR-000001", "FMR-000003")) == "FMR-000004"
    assert next_final_model_review_revision_id(("FRV-000002",)) == "FRV-000003"
    assert next_final_model_review_item_id(("FRI-000010",)) == "FRI-000011"
    assert next_final_model_review_decision_id(("FRD-000099",)) == "FRD-000100"


@pytest.mark.parametrize(
    "value",
    ["FMR-000000", "FMR-1", "FRV-000001", None, 1],
)
def test_l1_rejects_invalid_fmr_ids(value):
    with pytest.raises(FinalModelReviewValidationError):
        validate_final_model_review_id(value)


def test_l1_lifecycle_and_decision_vocabularies_are_explicit():
    assert FINAL_MODEL_REVIEW_LIFECYCLE_STATES == (
        "generated",
        "validation_blocked",
        "review_pending",
        "changes_requested",
        "regeneration_required",
        "ready_for_approval",
        "approved_for_publication",
        "published",
    )
    assert FINAL_MODEL_REVIEW_DECISIONS == (
        "approved_for_publication",
        "changes_requested",
        "rejected",
    )


def test_l1_manifest_is_frozen_and_fingerprint_valid():
    manifest = create_final_model_review_manifest(
        project_id="000001",
        final_model_review_id="FMR-000001",
        created_at="2026-08-14T10:00:00Z",
    )
    validate_final_model_review_manifest(manifest)
    assert len(manifest.content_fingerprint) == 64


def test_l1_manifest_detects_tampering():
    manifest = create_final_model_review_manifest(
        project_id="000001",
        final_model_review_id="FMR-000001",
        created_at="2026-08-14T10:00:00Z",
    )
    tampered = replace(manifest, project_id="000002")
    with pytest.raises(FinalModelReviewIntegrityError):
        validate_final_model_review_manifest(tampered)


def test_l1_revision_binds_generated_and_validation_subject():
    revision = _revision()
    validate_final_model_review_revision(revision)
    assert revision.generated_artifact_set_fingerprint == FP_C
    assert revision.validation_result_fingerprint == FP_D
    assert revision.validation_status == "valid"
    assert revision.publication_gate == "passed"
    assert len(revision.review_subject_fingerprint) == 64
    assert len(revision.content_fingerprint) == 64


def test_l1_same_subject_has_same_subject_fingerprint_across_revision_identity():
    first = _revision(revision_id="FRV-000001")
    second = _revision(revision_id="FRV-000002")
    assert first.review_subject_fingerprint == second.review_subject_fingerprint
    assert first.content_fingerprint != second.content_fingerprint


@pytest.mark.parametrize(
    ("status", "gate"),
    [
        ("valid", "blocked"),
        ("invalid", "passed"),
        ("incomplete", "passed"),
    ],
)
def test_l1_rejects_invalid_k_status_gate_pairs(status, gate):
    with pytest.raises(FinalModelReviewValidationError):
        _revision(status=status, gate=gate)


def test_l1_review_revision_may_bind_incomplete_blocked_for_review():
    revision = _revision(status="incomplete", gate="blocked")
    validate_final_model_review_revision(revision)
    assert revision.validation_status == "incomplete"
    assert revision.publication_gate == "blocked"


def test_l1_review_revision_may_bind_invalid_blocked_for_review():
    revision = _revision(status="invalid", gate="blocked")
    validate_final_model_review_revision(revision)
    assert revision.validation_status == "invalid"


def test_l1_generated_units_require_canonical_order_and_unique_paths():
    unit_1 = _unit()
    unit_2 = create_generated_unit_reference(
        generated_unit_id="GSU-000002",
        relative_path="other.sysml",
        content_fingerprint=FP_B,
    )
    with pytest.raises(FinalModelReviewValidationError):
        create_final_model_review_revision(
            project_id="000001",
            final_model_review_id="FMR-000001",
            final_model_review_revision_id="FRV-000001",
            predecessor_revision_id=None,
            source_internal_engineering_model_id="IEM-000001",
            generated_artifact_set_fingerprint=FP_C,
            validation_result_fingerprint=FP_D,
            validation_status="valid",
            publication_gate="passed",
            generated_units=(unit_2, unit_1),
            created_at="2026-08-14T10:00:00Z",
        )


def test_l1_generated_unit_rejects_unsafe_path():
    with pytest.raises(FinalModelReviewValidationError):
        create_generated_unit_reference(
            generated_unit_id="GSU-000001",
            relative_path="../generated_model.sysml",
            content_fingerprint=FP_A,
        )


def test_l1_evidence_references_require_canonical_order():
    first = create_evidence_reference(
        evidence_type="agent_proposal",
        reference_id="A",
        content_fingerprint=FP_A,
    )
    second = create_evidence_reference(
        evidence_type="candidate_review_decision",
        reference_id="MCD-000001",
        content_fingerprint=FP_B,
    )
    with pytest.raises(FinalModelReviewValidationError):
        create_final_model_review_revision(
            project_id="000001",
            final_model_review_id="FMR-000001",
            final_model_review_revision_id="FRV-000001",
            predecessor_revision_id=None,
            source_internal_engineering_model_id="IEM-000001",
            generated_artifact_set_fingerprint=FP_C,
            validation_result_fingerprint=FP_D,
            validation_status="valid",
            publication_gate="passed",
            generated_units=(_unit(),),
            evidence_references=(second, first),
            created_at="2026-08-14T10:00:00Z",
        )


def test_l1_item_is_immutable_fingerprint_bound_review_attention():
    item = create_final_model_review_item(
        project_id="000001",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id="FRV-000001",
        final_model_review_item_id="FRI-000001",
        item_kind="validation_finding",
        summary="Review SYSIDE warning.",
        detail="Warning is visible but nonblocking.",
        mandatory=False,
        generated_unit_id="GSU-000001",
        generated_symbol_id="IME_000001",
        evidence_references=(_evidence(),),
    )
    validate_final_model_review_item(item)
    assert item.generated_symbol_id == "IME_000001"


def test_l1_symbol_target_requires_unit_target():
    with pytest.raises(FinalModelReviewValidationError):
        create_final_model_review_item(
            project_id="000001",
            final_model_review_id="FMR-000001",
            final_model_review_revision_id="FRV-000001",
            final_model_review_item_id="FRI-000001",
            item_kind="generated_symbol",
            summary="Review symbol.",
            detail=None,
            mandatory=True,
            generated_symbol_id="IME_000001",
        )


def test_l1_decision_target_is_exact_revision_snapshot():
    revision = _revision()
    target = create_final_model_review_decision_target(revision)
    assert target.revision_content_fingerprint == revision.content_fingerprint
    assert target.review_subject_fingerprint == revision.review_subject_fingerprint
    assert target.generated_artifact_set_fingerprint == FP_C
    assert target.validation_result_fingerprint == FP_D


def test_l1_human_can_approve_exact_valid_passed_revision():
    target = create_final_model_review_decision_target(_revision())
    decision = create_final_model_review_decision(
        project_id="000001",
        final_model_review_decision_id="FRD-000001",
        target=target,
        decision="approved_for_publication",
        reviewer_identity="moritz",
        rationale="Reviewed generated model and validation evidence.",
        reviewed_at="2026-08-14T10:15:00Z",
    )
    validate_final_model_review_decision(decision)
    assert decision.decision == "approved_for_publication"


@pytest.mark.parametrize("status", ["invalid", "incomplete"])
def test_l1_human_cannot_approve_blocked_k_result(status):
    target = create_final_model_review_decision_target(
        _revision(status=status, gate="blocked")
    )
    with pytest.raises(FinalModelReviewValidationError):
        create_final_model_review_decision(
            project_id="000001",
            final_model_review_decision_id="FRD-000001",
            target=target,
            decision="approved_for_publication",
            reviewer_identity="moritz",
            rationale=None,
            reviewed_at="2026-08-14T10:15:00Z",
        )


def test_l1_changes_requested_is_allowed_for_incomplete_revision():
    target = create_final_model_review_decision_target(
        _revision(status="incomplete", gate="blocked")
    )
    decision = create_final_model_review_decision(
        project_id="000001",
        final_model_review_decision_id="FRD-000001",
        target=target,
        decision="changes_requested",
        reviewer_identity="moritz",
        rationale="External validation must be completed.",
        reviewed_at="2026-08-14T10:15:00Z",
    )
    validate_final_model_review_decision(decision)


def test_l1_decision_fingerprint_is_human_authority_content_not_id_or_time():
    target = create_final_model_review_decision_target(_revision())
    first = create_final_model_review_decision(
        project_id="000001",
        final_model_review_decision_id="FRD-000001",
        target=target,
        decision="changes_requested",
        reviewer_identity="moritz",
        rationale="Please revise.",
        reviewed_at="2026-08-14T10:15:00Z",
    )
    second = create_final_model_review_decision(
        project_id="000001",
        final_model_review_decision_id="FRD-000002",
        target=target,
        decision="changes_requested",
        reviewer_identity="moritz",
        rationale="Please revise.",
        reviewed_at="2026-08-14T11:00:00Z",
    )
    assert first.decision_fingerprint == second.decision_fingerprint


def test_l1_revision_detects_artifact_fingerprint_tampering():
    revision = _revision()
    tampered = replace(
        revision,
        generated_artifact_set_fingerprint="e" * 64,
    )
    with pytest.raises(FinalModelReviewIntegrityError):
        validate_final_model_review_revision(tampered)


def test_l1_decision_detects_target_tampering():
    decision = create_final_model_review_decision(
        project_id="000001",
        final_model_review_decision_id="FRD-000001",
        target=create_final_model_review_decision_target(_revision()),
        decision="changes_requested",
        reviewer_identity="moritz",
        rationale="Please revise.",
        reviewed_at="2026-08-14T10:15:00Z",
    )
    tampered_target = replace(
        decision.target,
        validation_result_fingerprint="e" * 64,
    )
    tampered = replace(decision, target=tampered_target)
    with pytest.raises(FinalModelReviewIntegrityError):
        validate_final_model_review_decision(tampered)
