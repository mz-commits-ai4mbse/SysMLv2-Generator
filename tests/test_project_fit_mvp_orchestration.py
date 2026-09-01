"""Focused active-path test for BLK-002 MVP-A orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import modules.project_reconciliation.project_fit_readiness as readiness_module
from modules.project_reconciliation.orchestration_service import (
    ProjectReconciliationOrchestrationService,
)
from modules.project_sources import ENGINEERING_SOURCE_ROLE


@dataclass(frozen=True)
class ReviewItem:
    source_id: str
    processing_run_id: str
    attempt_id: str
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


class Workspace:
    def load_project(self, project_id):
        return SimpleNamespace(project_id=project_id)


class Review:
    def project_view(self, project_id):
        return SimpleNamespace(
            has_blocking_issues=False,
            items=(
                ReviewItem(
                    "SRC-000001",
                    "RUN-000005",
                    "ATT-000001",
                ),
                ReviewItem(
                    "SRC-000002",
                    "RUN-000006",
                    "ATT-000001",
                ),
            ),
        )


class Sources:
    def load_source(self, project_id, source_id):
        return SimpleNamespace(
            source_id=source_id,
            source_role=ENGINEERING_SOURCE_ROLE,
        )


class Projections:
    def list_projections(self, project_id):
        return ()


class Repository:
    def list_project_fit(self, project_id):
        return ()


class Bomb:
    def __getattr__(self, name):
        raise AssertionError(
            f"Inactive S3/S4/S5 dependency was touched: {name}"
        )


def test_fit_only_active_orchestration_never_calls_s3_or_prc(monkeypatch):
    monkeypatch.setattr(
        readiness_module,
        "derive_project_fit_gate_state",
        lambda fit: "admitted",
    )
    monkeypatch.setattr(
        "modules.project_reconciliation.orchestration_service."
        "derive_project_fit_gate_state",
        lambda fit: "admitted",
    )

    service = object.__new__(ProjectReconciliationOrchestrationService)
    service._workspace = Workspace()
    service._review = Review()
    service._sources = Sources()
    service._projections = Projections()
    service._reconciliation = Repository()
    service._semantic_index = Bomb()
    service._case_assessment = Bomb()
    service._concern_reconciliation = Bomb()

    fits = {
        "SRC-000001": Fit(
            "308131",
            "SRC-000001",
            "RUN-000005",
            "ATT-000001",
            "plausible_in_scope",
            "1" * 64,
        ),
        "SRC-000002": Fit(
            "308131",
            "SRC-000002",
            "RUN-000006",
            "ATT-000001",
            "plausible_in_scope",
            "2" * 64,
        ),
    }

    service._source_input = lambda **kwargs: (
        object(),
        fits[kwargs["item"].source_id],
    )

    events = []
    result = service.assess_project_fit_only(
        "308131",
        provider="openai",
        model="gpt-test",
        progress_observer=events.append,
    )

    assert result.all_admitted is True
    assert result.project_fit_fingerprints == (
        "1" * 64,
        "2" * 64,
    )
    assert {event.stage for event in events} == {
        "authority_validation",
        "project_fit",
    }
    assert not any(
        event.stage in {"semantic_reconciliation", "persistence"}
        for event in events
    )
