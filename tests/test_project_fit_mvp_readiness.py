"""Focused tests for the BLK-002 MVP Project-Fit-only gate."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

import modules.project_reconciliation.project_fit_readiness as module
from modules.project_reconciliation.project_fit_readiness import (
    ProjectFitReadinessError,
    derive_project_fit_readiness,
)


@dataclass(frozen=True)
class ReviewItem:
    source_id: str
    processing_run_id: str
    attempt_id: str | None
    workflow_status: str = "approved_input_available"
    is_current_processing_run: bool = True


@dataclass(frozen=True)
class Fit:
    project_id: str
    source_id: str
    processing_run_id: str
    attempt_id: str
    outcome: str
    assessment_fingerprint: str


@pytest.fixture(autouse=True)
def gate_policy(monkeypatch):
    mapping = {
        "plausible_in_scope": "admitted",
        "uncertain": "human_resolution_required",
        "likely_out_of_scope": "human_resolution_required",
    }
    monkeypatch.setattr(
        module,
        "derive_project_fit_gate_state",
        lambda fit: mapping[fit.outcome],
    )


def item(source_id: str, run: int, attempt: int = 1, **kwargs):
    return ReviewItem(
        source_id=source_id,
        processing_run_id=f"RUN-{run:06d}",
        attempt_id=f"ATT-{attempt:06d}",
        **kwargs,
    )


def fit(source_id: str, run: int, outcome="plausible_in_scope"):
    return Fit(
        project_id="308131",
        source_id=source_id,
        processing_run_id=f"RUN-{run:06d}",
        attempt_id="ATT-000001",
        outcome=outcome,
        assessment_fingerprint=(str(run % 10) * 64),
    )


def test_all_current_multi_source_fits_admitted_complete_gate():
    value = derive_project_fit_readiness(
        project_id="308131",
        review_items=(
            item("SRC-000001", 5),
            item("SRC-000002", 6),
        ),
        project_fit_assessments=(
            fit("SRC-000001", 5),
            fit("SRC-000002", 6),
        ),
    )
    assert value.all_admitted is True
    assert value.admitted_source_ids == (
        "SRC-000001",
        "SRC-000002",
    )
    assert value.assessment_required_source_ids == ()
    assert value.human_resolution_source_ids == ()


def test_missing_exact_fit_requires_assessment_not_s3():
    value = derive_project_fit_readiness(
        project_id="308131",
        review_items=(
            item("SRC-000001", 5),
            item("SRC-000002", 6),
        ),
        project_fit_assessments=(fit("SRC-000001", 5),),
    )
    assert value.all_admitted is False
    assert value.assessment_required_source_ids == ("SRC-000002",)


def test_non_admitted_fit_requires_human_resolution():
    value = derive_project_fit_readiness(
        project_id="308131",
        review_items=(
            item("SRC-000001", 5),
            item("SRC-000002", 6),
        ),
        project_fit_assessments=(
            fit("SRC-000001", 5),
            fit("SRC-000002", 6, outcome="uncertain"),
        ),
    )
    assert value.all_admitted is False
    assert value.human_resolution_source_ids == ("SRC-000002",)


def test_historical_fit_does_not_satisfy_current_run_attempt():
    value = derive_project_fit_readiness(
        project_id="308131",
        review_items=(
            item("SRC-000001", 5),
            item("SRC-000002", 7),
        ),
        project_fit_assessments=(
            fit("SRC-000001", 5),
            fit("SRC-000002", 6),
        ),
    )
    assert value.assessment_required_source_ids == ("SRC-000002",)


def test_superseded_review_item_does_not_enter_active_gate():
    value = derive_project_fit_readiness(
        project_id="308131",
        review_items=(
            item("SRC-000001", 4, is_current_processing_run=False),
            item("SRC-000001", 5),
            item("SRC-000002", 6),
        ),
        project_fit_assessments=(
            fit("SRC-000001", 5),
            fit("SRC-000002", 6),
        ),
    )
    assert value.source_ids == ("SRC-000001", "SRC-000002")
    assert value.all_admitted is True


def test_duplicate_exact_fit_binding_fails_closed():
    duplicate = fit("SRC-000001", 5)
    with pytest.raises(
        ProjectFitReadinessError,
        match="More than one Project Fit assessment",
    ):
        derive_project_fit_readiness(
            project_id="308131",
            review_items=(
                item("SRC-000001", 5),
                item("SRC-000002", 6),
            ),
            project_fit_assessments=(
                duplicate,
                duplicate,
                fit("SRC-000002", 6),
            ),
        )


def test_source_local_review_must_finish_before_project_fit_gate():
    value = derive_project_fit_readiness(
        project_id="308131",
        review_items=(
            item("SRC-000001", 5),
            item(
                "SRC-000002",
                6,
                workflow_status="review_in_progress",
            ),
        ),
        project_fit_assessments=(fit("SRC-000001", 5),),
    )
    assert value.source_review_required_source_ids == ("SRC-000002",)
    assert value.all_admitted is False
