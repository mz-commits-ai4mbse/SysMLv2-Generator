"""Focused contract tests for BLK-002 MVP-B1 Project-Fit Phase-H handoff."""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import SimpleNamespace

import pytest

import modules.model_candidates.project_fit_handoff as module
from modules.model_candidates.project_fit_handoff import (
    ProjectFitPhaseHHandoffError,
    create_project_fit_phase_h_handoff,
    select_project_fit_active_inputs,
    validate_project_fit_phase_h_request,
)


@dataclass(frozen=True)
class Input:
    project_id: str
    approved_input_id: str
    authority_state: str
    source_id: str
    source_sha256: str
    processing_run_id: str
    attempt_id: str
    review_document_id: str
    review_document_version_id: str
    content_fingerprint: str


@dataclass(frozen=True)
class Fit:
    project_id: str
    source_id: str
    source_sha256: str
    processing_run_id: str
    attempt_id: str
    outcome: str
    assessment_fingerprint: str


@dataclass(frozen=True)
class Subject:
    canonical_subject_id: str
    approved_input_id: str
    stable_subject_key: str


@dataclass(frozen=True)
class Relationship:
    source_subject_id: str
    relationship_kind: str
    target_subject_id: str


@dataclass(frozen=True)
class AEI:
    project_id: str
    review_document_id: str
    review_document_version_id: str
    subjects: tuple[Subject, ...]
    relationships: tuple[Relationship, ...]
    content_fingerprint: str


@pytest.fixture(autouse=True)
def validators(monkeypatch):
    monkeypatch.setattr(
        module,
        "validate_approved_input_manifest",
        lambda value: None,
    )
    monkeypatch.setattr(
        module,
        "validate_project_fit_assessment",
        lambda value: None,
    )
    monkeypatch.setattr(
        module,
        "derive_project_fit_gate_state",
        lambda value: (
            "admitted"
            if value.outcome == "plausible_in_scope"
            else "human_resolution_required"
        ),
    )


def input_(
    source: int,
    approved: int,
    subject: str = "subject",
):
    return Input(
        project_id="308131",
        approved_input_id=f"AIN-{approved:06d}",
        authority_state="active",
        source_id=f"SRC-{source:06d}",
        source_sha256=str(source) * 64,
        processing_run_id=f"RUN-{source + 4:06d}",
        attempt_id="ATT-000001",
        review_document_id=f"RVD-{source:06d}",
        review_document_version_id=f"RVV-{source:06d}",
        content_fingerprint=str(approved % 10) * 64,
    )


def fit(source: int, outcome="plausible_in_scope"):
    return Fit(
        project_id="308131",
        source_id=f"SRC-{source:06d}",
        source_sha256=str(source) * 64,
        processing_run_id=f"RUN-{source + 4:06d}",
        attempt_id="ATT-000001",
        outcome=outcome,
        assessment_fingerprint=(
            hex(source)[2:] * 64
        )[:64],
    )


def aei(source: int, approved: int):
    return AEI(
        project_id="308131",
        review_document_id=f"RVD-{source:06d}",
        review_document_version_id=f"RVV-{source:06d}",
        subjects=(
            Subject(
                canonical_subject_id="SUBJ-000001",
                approved_input_id=f"AIN-{approved:06d}",
                stable_subject_key="subject",
            ),
        ),
        relationships=(),
        content_fingerprint=(
            hex(source + 8)[2:] * 64
        )[:64],
    )


def baseline():
    inputs = (
        input_(1, 1),
        input_(2, 2),
    )
    fits = (
        fit(1),
        fit(2),
    )
    aeis = (
        aei(1, 1),
        aei(2, 2),
    )
    return inputs, fits, aeis


def test_handoff_binds_exact_two_source_population_deterministically():
    inputs, fits, aeis = baseline()

    first = create_project_fit_phase_h_handoff(
        project_fit_assessments=fits,
        approved_input_manifests=inputs,
        approved_engineering_information_sets=aeis,
    )
    second = create_project_fit_phase_h_handoff(
        project_fit_assessments=tuple(reversed(fits)),
        approved_input_manifests=tuple(reversed(inputs)),
        approved_engineering_information_sets=tuple(reversed(aeis)),
    )

    assert first.content_fingerprint == second.content_fingerprint
    assert first.source_ids == (
        "SRC-000001",
        "SRC-000002",
    )
    assert first.project_fit_fingerprints == (
        fit(1).assessment_fingerprint,
        fit(2).assessment_fingerprint,
    )


def test_non_admitted_fit_fails_closed():
    inputs, fits, aeis = baseline()

    with pytest.raises(
        ProjectFitPhaseHHandoffError,
        match="does not admit Source SRC-000002",
    ):
        create_project_fit_phase_h_handoff(
            project_fit_assessments=(
                fits[0],
                replace(
                    fits[1],
                    outcome="uncertain",
                ),
            ),
            approved_input_manifests=inputs,
            approved_engineering_information_sets=aeis,
        )


def test_stale_fit_does_not_bind_current_run():
    inputs, fits, aeis = baseline()

    with pytest.raises(
        ProjectFitPhaseHHandoffError,
        match="Exactly one admitted Project Fit",
    ):
        create_project_fit_phase_h_handoff(
            project_fit_assessments=(
                fits[0],
                replace(
                    fits[1],
                    processing_run_id="RUN-999999",
                ),
            ),
            approved_input_manifests=inputs,
            approved_engineering_information_sets=aeis,
        )


def test_duplicate_exact_fit_fails_closed():
    inputs, fits, aeis = baseline()

    with pytest.raises(
        ProjectFitPhaseHHandoffError,
        match="Exactly one admitted Project Fit",
    ):
        create_project_fit_phase_h_handoff(
            project_fit_assessments=(
                fits[0],
                fits[0],
                fits[1],
            ),
            approved_input_manifests=inputs,
            approved_engineering_information_sets=aeis,
        )


def test_aei_coverage_must_match_exact_review_workspaces():
    inputs, fits, aeis = baseline()

    with pytest.raises(
        ProjectFitPhaseHHandoffError,
        match="AEI coverage must exactly match",
    ):
        create_project_fit_phase_h_handoff(
            project_fit_assessments=fits,
            approved_input_manifests=inputs,
            approved_engineering_information_sets=(aeis[0],),
        )


def test_aei_cannot_reference_foreign_approved_input():
    inputs, fits, aeis = baseline()
    bad = replace(
        aeis[1],
        subjects=(
            replace(
                aeis[1].subjects[0],
                approved_input_id="AIN-999999",
            ),
        ),
    )

    with pytest.raises(
        ProjectFitPhaseHHandoffError,
        match="does not bind an active Approved Input",
    ):
        create_project_fit_phase_h_handoff(
            project_fit_assessments=fits,
            approved_input_manifests=inputs,
            approved_engineering_information_sets=(
                aeis[0],
                bad,
            ),
        )


def test_selection_verifies_population_but_never_filters_authority():
    inputs, fits, aeis = baseline()
    handoff = create_project_fit_phase_h_handoff(
        project_fit_assessments=fits,
        approved_input_manifests=inputs,
        approved_engineering_information_sets=aeis,
    )

    selected = select_project_fit_active_inputs(
        tuple(reversed(inputs)),
        handoff,
    )

    assert selected == inputs

    with pytest.raises(
        ProjectFitPhaseHHandoffError,
        match="do not match the exact",
    ):
        select_project_fit_active_inputs(
            (inputs[0],),
            handoff,
        )


def test_request_rejects_old_authority_handoff_and_synthetic_aei():
    inputs, fits, aeis = baseline()
    handoff = create_project_fit_phase_h_handoff(
        project_fit_assessments=fits,
        approved_input_manifests=inputs,
        approved_engineering_information_sets=aeis,
    )

    valid = SimpleNamespace(
        project_id="308131",
        approved_inputs=inputs,
        approved_engineering_information=None,
        project_authority_handoff=None,
        project_fit_handoff=handoff,
    )
    validate_project_fit_phase_h_request(valid)

    with pytest.raises(
        ProjectFitPhaseHHandoffError,
        match="mutually exclusive",
    ):
        validate_project_fit_phase_h_request(
            SimpleNamespace(
                **{
                    **valid.__dict__,
                    "project_authority_handoff": object(),
                }
            )
        )

    with pytest.raises(
        ProjectFitPhaseHHandoffError,
        match="synthetic ApprovedEngineeringInformationSet",
    ):
        validate_project_fit_phase_h_request(
            SimpleNamespace(
                **{
                    **valid.__dict__,
                    "approved_engineering_information": object(),
                }
            )
        )
