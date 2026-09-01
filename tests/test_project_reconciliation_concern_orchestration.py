"""Focused tests for I2D.5D2A concern-centric S3 orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

import modules.project_reconciliation.orchestration_service as module
from modules.project_reconciliation.errors import (
    ProjectReconciliationPersistenceIntegrityError,
)
from modules.project_reconciliation.orchestration_service import (
    ProjectReconciliationOrchestrationError,
    ProjectReconciliationOrchestrationService,
)
from modules.project_semantic_reconciliation.errors import (
    ProjectSemanticReconciliationIntegrityError,
)


@dataclass(frozen=True)
class ReviewItem:
    source_id: str
    is_current_processing_run: bool = True
    workflow_status: str = "approved_input_available"


class Workspace:
    def load_project(self, project_id):
        return SimpleNamespace(project_id=project_id)


class Review:
    def project_view(self, project_id):
        return SimpleNamespace(
            has_blocking_issues=False,
            items=(
                ReviewItem("SRC-000001"),
                ReviewItem("SRC-000002"),
            ),
        )


class Sources:
    def load_source(self, project_id, source_id):
        return SimpleNamespace(
            source_id=source_id,
            source_role=module.ENGINEERING_SOURCE_ROLE,
        )


class Projections:
    def list_projections(self, project_id):
        return ()


class LegacyRepo:
    pass


class ConcernRepo:
    def __init__(self):
        self.existing = None
        self.started = []
        self.index = None
        self.summary = None

    def find_cycle_by_input_fingerprint(
        self,
        project_id,
        input_fingerprint,
    ):
        return self.existing

    def load_semantic_index(self, project_id, cycle_id):
        return self.index

    def load_reconciliation_summary(self, project_id, cycle_id):
        return self.summary

    def start_cycle(self, **kwargs):
        self.started.append(kwargs)
        return SimpleNamespace(
            reconciliation_cycle_id="PRC-000001",
            project_fit_fingerprints=("1" * 64, "2" * 64),
        )


class SemanticIndexService:
    def __init__(self, artifact=None, error=None):
        self.artifact = artifact
        self.error = error
        self.calls = []

    def index(self, source_inputs, **kwargs):
        self.calls.append((source_inputs, kwargs))
        if self.error is not None:
            raise self.error
        return self.artifact


class CaseService:
    def __init__(self, assessments=(), summary=None, error=None):
        self.assessments = assessments
        self.summary = summary
        self.error = error
        self.calls = []

    def assess_all(self, **kwargs):
        self.calls.append(kwargs)
        observer = kwargs.get("case_progress_observer")
        if observer is not None:
            observer(
                SimpleNamespace(
                    event_type="started",
                    case_index=1,
                    total_cases=2,
                    case_id="CASE-000001",
                    case_label="Remote client",
                    singleton=False,
                )
            )
            observer(
                SimpleNamespace(
                    event_type="completed",
                    case_index=1,
                    total_cases=2,
                    case_id="CASE-000001",
                    case_label="Remote client",
                    singleton=False,
                )
            )
            observer(
                SimpleNamespace(
                    event_type="started",
                    case_index=2,
                    total_cases=2,
                    case_id="CASE-000002",
                    case_label="Audio",
                    singleton=True,
                )
            )
            observer(
                SimpleNamespace(
                    event_type="completed",
                    case_index=2,
                    total_cases=2,
                    case_id="CASE-000002",
                    case_label="Audio",
                    singleton=True,
                )
            )
        if self.error is not None:
            raise self.error
        return self.assessments, self.summary


def fit(source_id, fingerprint):
    return SimpleNamespace(
        project_id="308131",
        source_id=source_id,
        outcome="plausible_in_scope",
        assessment_fingerprint=fingerprint,
    )


def semantic_subject(ref, source_id):
    return SimpleNamespace(
        subject_ref=ref,
        source_id=source_id,
    )


def semantic_index():
    return SimpleNamespace(
        project_id="308131",
        source_ids=("SRC-000001", "SRC-000002"),
        input_fingerprint="a" * 64,
        content_fingerprint="b" * 64,
        cases=(
            SimpleNamespace(
                case_id="CASE-000001",
                group_label="Remote client",
                singleton=False,
            ),
            SimpleNamespace(
                case_id="CASE-000002",
                group_label="Audio",
                singleton=True,
            ),
        ),
    )


def summary():
    return SimpleNamespace(
        project_id="308131",
        semantic_index_fingerprint="b" * 64,
        content_fingerprint="c" * 64,
        case_count=2,
        potential_conflicts_present=True,
        uncertainties_present=False,
        regrouping_required=False,
    )


def build_service(
    monkeypatch,
    *,
    concern=None,
    index_service=None,
    case_service=None,
):
    concern = concern or ConcernRepo()
    index_service = index_service or SemanticIndexService(
        artifact=semantic_index()
    )
    case_service = case_service or CaseService(
        assessments=("A1", "A2"),
        summary=summary(),
    )

    service = ProjectReconciliationOrchestrationService(
        project_root=".",
        workspace=Workspace(),
        source_registry=Sources(),
        processing_repository=SimpleNamespace(),
        source_projection_repository=Projections(),
        review_workflow_service=Review(),
        reconciliation_repository=LegacyRepo(),
        project_fit_service=SimpleNamespace(),
        semantic_index_service=index_service,
        case_assessment_service=case_service,
        concern_reconciliation_repository=concern,
    )

    inputs = {
        "SRC-000001": ("INPUT-1", fit("SRC-000001", "1" * 64)),
        "SRC-000002": ("INPUT-2", fit("SRC-000002", "2" * 64)),
    }
    monkeypatch.setattr(
        service,
        "_source_input",
        lambda **kwargs: inputs[kwargs["item"].source_id],
    )
    monkeypatch.setattr(
        module,
        "derive_project_fit_gate_state",
        lambda value: "admitted",
    )

    subjects = (
        semantic_subject(
            "project_subject:SRC-000001:SP-000001:CSUB-000001",
            "SRC-000001",
        ),
        semantic_subject(
            "project_subject:SRC-000002:SP-000002:CSUB-000002",
            "SRC-000002",
        ),
    )
    monkeypatch.setattr(
        module,
        "prepare_project_semantic_subjects",
        lambda source_inputs: ("308131", subjects, "a" * 64),
    )
    return service, concern, index_service, case_service, subjects


def test_active_runtime_calls_s3a_then_s3b_then_v2_persistence(monkeypatch):
    service, concern, index_service, case_service, subjects = build_service(
        monkeypatch
    )

    result = service.start(
        "308131",
        provider="openai",
        model="gpt-test",
    )

    assert len(index_service.calls) == 1
    assert len(case_service.calls) == 1
    assert case_service.calls[0]["subjects"] == subjects
    assert len(concern.started) == 1
    persisted = concern.started[0]
    assert persisted["semantic_index"].content_fingerprint == "b" * 64
    assert persisted["case_assessments"] == ("A1", "A2")
    assert persisted["reconciliation_summary"].content_fingerprint == "c" * 64
    assert tuple(item.assessment_fingerprint for item in persisted["project_fit_assessments"]) == (
        "1" * 64,
        "2" * 64,
    )
    assert result.reconciliation_cycle_id == "PRC-000001"


def test_result_does_not_repurpose_legacy_semantic_fingerprint(monkeypatch):
    service, _, _, _, _ = build_service(monkeypatch)

    result = service.start(
        "308131",
        provider="openai",
        model="gpt-test",
    )

    assert result.semantic_reconciliation_fingerprint is None
    assert result.semantic_index_fingerprint == "b" * 64
    assert result.reconciliation_summary_fingerprint == "c" * 64
    assert result.case_count == 2
    assert result.potential_conflicts_present is True


def test_exact_existing_v2_input_reuses_without_llm(monkeypatch):
    concern = ConcernRepo()
    concern.existing = SimpleNamespace(
        reconciliation_cycle_id="PRC-000007",
        project_fit_fingerprints=("1" * 64, "2" * 64),
    )
    concern.index = semantic_index()
    concern.summary = summary()
    index_service = SemanticIndexService(artifact=semantic_index())
    case_service = CaseService(summary=summary())

    service, _, _, _, _ = build_service(
        monkeypatch,
        concern=concern,
        index_service=index_service,
        case_service=case_service,
    )

    result = service.start(
        "308131",
        provider="openai",
        model="gpt-test",
    )

    assert result.reconciliation_cycle_id == "PRC-000007"
    assert result.reused_existing_cycle is True
    assert index_service.calls == []
    assert case_service.calls == []
    assert concern.started == []


def test_s3a_integrity_failure_stops_before_s3b_and_persistence(monkeypatch):
    error = ProjectSemanticReconciliationIntegrityError(
        "semantic index coverage invalid"
    )
    index_service = SemanticIndexService(error=error)
    case_service = CaseService(summary=summary())
    service, concern, _, _, _ = build_service(
        monkeypatch,
        index_service=index_service,
        case_service=case_service,
    )

    with pytest.raises(
        ProjectReconciliationOrchestrationError,
        match="S3A response integrity failed",
    ):
        service.start(
            "308131",
            provider="openai",
            model="gpt-test",
        )

    assert case_service.calls == []
    assert concern.started == []


def test_s3b_failure_stops_before_persistence(monkeypatch):
    case_service = CaseService(
        error=ProjectSemanticReconciliationIntegrityError(
            "Case evidence invalid"
        )
    )
    service, concern, _, _, _ = build_service(
        monkeypatch,
        case_service=case_service,
    )

    with pytest.raises(
        ProjectReconciliationOrchestrationError,
        match="S3B response integrity failed",
    ):
        service.start(
            "308131",
            provider="openai",
            model="gpt-test",
        )

    assert concern.started == []


def test_v2_persistence_failure_is_separate_stage(monkeypatch):
    class BrokenConcernRepo(ConcernRepo):
        def start_cycle(self, **kwargs):
            raise ProjectReconciliationPersistenceIntegrityError(
                "disk evidence mismatch"
            )

    service, _, _, _, _ = build_service(
        monkeypatch,
        concern=BrokenConcernRepo(),
    )

    with pytest.raises(
        ProjectReconciliationOrchestrationError,
        match="PRC persistence failed",
    ):
        service.start(
            "308131",
            provider="openai",
            model="gpt-test",
        )


def test_progress_reports_global_index_and_case_assessment(monkeypatch):
    service, _, _, _, _ = build_service(monkeypatch)
    events = []

    service.start(
        "308131",
        provider="openai",
        model="gpt-test",
        progress_observer=events.append,
    )

    messages = [event.message for event in events]
    assert any("S3A · Global semantic indexing" in item for item in messages)
    assert any("S3A · 2 Reconciliation Cases identified" in item for item in messages)
    assert any("S3B · Case 1/2" in item for item in messages)
    assert any("CASE-000001" in item for item in messages)
    assert any("unique · no LLM" in item for item in messages)
    assert any("PRC-000001 persisted" in item for item in messages)


def test_s3a_input_fingerprint_must_match_prepared_subject_set(monkeypatch):
    wrong = semantic_index()
    wrong = SimpleNamespace(
        **{
            **wrong.__dict__,
            "input_fingerprint": "d" * 64,
        }
    )
    service, concern, _, case_service, _ = build_service(
        monkeypatch,
        index_service=SemanticIndexService(artifact=wrong),
    )

    with pytest.raises(
        ProjectReconciliationOrchestrationError,
        match="S3A artifact does not bind",
    ):
        service.start(
            "308131",
            provider="openai",
            model="gpt-test",
        )

    assert case_service.calls == []
    assert concern.started == []
