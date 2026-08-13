"""Tests for strict immutable Candidate Review Decision manifests."""

from dataclasses import replace

import pytest

from modules.model_candidates import (
    ModelCandidateIntegrityError,
    ModelCandidateValidationError,
    ModelStructureProfileReference,
    calculate_model_candidate_review_decision_fingerprint,
    create_model_candidate_review_decision,
    create_model_candidate_review_target_snapshot,
    model_candidate_review_decision_from_json,
    model_candidate_review_decision_to_json,
)


A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64


def _target(status="conformant"):
    return create_model_candidate_review_target_snapshot(
        candidate_set_id="MCS-000001",
        candidate_set_content_fingerprint=A,
        target_type="element_candidate",
        candidate_id="MCE-000001",
        candidate_content_fingerprint=B,
        model_structure_profile_reference=ModelStructureProfileReference(
            profile_id="TURING_MODEL_STRUCTURE",
            profile_version="1.0.0",
            profile_fingerprint=C,
        ),
        structure_profile_conformance_status=status,
        structure_profile_conformance_fingerprint=D,
        approved_input_snapshot_fingerprint=E,
    )


def _decision(decision="accepted", rationale=None, status="conformant"):
    return create_model_candidate_review_decision(
        project_id="318604",
        model_candidate_review_decision_id="MCD-000001",
        target=_target(status),
        decision=decision,
        reviewer_identity="reviewer@example.com",
        rationale=rationale,
        reviewed_at="2026-08-13T07:15:00Z",
    )


def test_candidate_review_roundtrip_is_deterministic():
    item = _decision()
    text = model_candidate_review_decision_to_json(item)
    assert model_candidate_review_decision_from_json(text) == item
    assert (
        calculate_model_candidate_review_decision_fingerprint(item)
        == item.decision_fingerprint
    )


def test_rejected_deferred_and_exception_require_rationale():
    for selected in ("rejected", "deferred"):
        with pytest.raises(ModelCandidateIntegrityError):
            _decision(selected)
    with pytest.raises(ModelCandidateIntegrityError):
        _decision("accepted_exception", status="exception_required")


def test_nonconformant_content_requires_accepted_exception():
    with pytest.raises(ModelCandidateIntegrityError):
        _decision("accepted", status="review_required")
    item = _decision(
        "accepted_exception",
        rationale="Reviewed and intentionally accepted.",
        status="review_required",
    )
    assert item.decision == "accepted_exception"


def test_accepted_exception_is_not_used_for_conformant_content():
    with pytest.raises(ModelCandidateIntegrityError):
        _decision(
            "accepted_exception",
            rationale="Not actually an exception.",
            status="conformant",
        )


def test_tampered_decision_fingerprint_is_rejected():
    item = replace(_decision(), decision_fingerprint=A)
    with pytest.raises(ModelCandidateIntegrityError):
        model_candidate_review_decision_to_json(item)


def test_target_type_and_candidate_id_must_match():
    with pytest.raises(ModelCandidateValidationError):
        create_model_candidate_review_target_snapshot(
            candidate_set_id="MCS-000001",
            candidate_set_content_fingerprint=A,
            target_type="element_candidate",
            candidate_id="MCR-000001",
            candidate_content_fingerprint=B,
            model_structure_profile_reference=ModelStructureProfileReference(
                profile_id="TURING_MODEL_STRUCTURE",
                profile_version="1.0.0",
                profile_fingerprint=C,
            ),
            structure_profile_conformance_status="conformant",
            structure_profile_conformance_fingerprint=D,
            approved_input_snapshot_fingerprint=E,
        )
