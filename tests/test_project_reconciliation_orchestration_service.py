from types import SimpleNamespace
import pytest

# Research/prototype regression evidence. The accepted BLK-002 MVP uses
# source-local authority + Project Fit and does not execute S3 automatically.
pytestmark = pytest.mark.skip(
    reason=(
        "Concern-centric S3 project reconciliation is retained as "
        "prototype/research evidence only; automatic cross-source semantic "
        "reconciliation is outside the accepted BLK-002 thesis MVP."
    )
)

import modules.project_reconciliation.orchestration_service as module
from modules.project_reconciliation.orchestration_service import (
    ProjectReconciliationOrchestrationError,
    ProjectReconciliationOrchestrationService,
)


class Workspace:
    def load_project(self, project_id):
        return SimpleNamespace(project_id=project_id, display_name="Example")


class Sources:
    def __init__(self, roles=None):
        self.roles = roles or {}
    def load_source(self, project_id, source_id):
        return SimpleNamespace(
            source_id=source_id,
            source_role=self.roles.get(source_id, "engineering_source"),
        )


class Review:
    def __init__(self, items, blocking=False):
        self.view = SimpleNamespace(
            items=tuple(items),
            has_blocking_issues=blocking,
        )
    def project_view(self, project_id):
        return self.view


class Projections:
    def list_projections(self, project_id):
        return ("context",)


class Repo:
    def __init__(self, cycles=()):
        self.cycles = tuple(cycles)
    def list_cycles(self, project_id):
        return self.cycles
    def load_semantic_reconciliation(self, project_id, cycle_id):
        return self.artifact
    def start_cycle(self, reconciliation, fits):
        return SimpleNamespace(
            reconciliation_cycle_id="PRC-000001",
            project_fit_fingerprints=tuple(
                fit.assessment_fingerprint for fit in fits
            ),
        )


class Semantic:
    def reconcile(self, source_inputs, **kwargs):
        self.calls = getattr(self, "calls", 0) + 1
        return SimpleNamespace(
            source_ids=tuple(i.project_fit.source_id for i in source_inputs),
            content_fingerprint="c" * 64,
        )


def item(
    source_id,
    run_id,
    status="approved_input_available",
    *,
    current=True,
):
    return SimpleNamespace(
        source_id=source_id,
        processing_run_id=run_id,
        attempt_id="ATT-000001",
        workflow_status=status,
        is_current_processing_run=current,
    )


def service(items, roles=None, repo=None, semantic=None):
    return ProjectReconciliationOrchestrationService(
        project_root=".",
        workspace=Workspace(),
        source_registry=Sources(roles),
        processing_repository=object(),
        source_projection_repository=Projections(),
        review_workflow_service=Review(items),
        reconciliation_repository=repo or Repo(),
        project_fit_service=object(),
        semantic_reconciliation_service=semantic or Semantic(),
    )


def test_requires_two_reviewed_engineering_sources():
    s = service((item("SRC-000001", "RUN-000001"),))
    with pytest.raises(ProjectReconciliationOrchestrationError, match="at least two"):
        s.start("120412", provider="openai", model="gpt-5.4-mini")


def test_context_only_does_not_count_for_s3():
    s = service(
        (item("SRC-000001", "RUN-000001"), item("SRC-000002", "RUN-000002")),
        roles={"SRC-000002": "context_only"},
    )
    with pytest.raises(ProjectReconciliationOrchestrationError, match="at least two"):
        s.start("120412", provider="openai", model="gpt-5.4-mini")


def test_incomplete_human_review_blocks_before_s2():
    s = service((
        item("SRC-000001", "RUN-000001"),
        item("SRC-000002", "RUN-000002", status="ready_to_promote"),
    ))
    with pytest.raises(
        ProjectReconciliationOrchestrationError,
        match="complete source-local Human Review",
    ):
        s.start("120412", provider="openai", model="gpt-5.4-mini")


def test_non_admitted_fit_blocks_s3(monkeypatch):
    s = service((
        item("SRC-000001", "RUN-000001"),
        item("SRC-000002", "RUN-000002"),
    ))
    fits = iter((
        SimpleNamespace(source_id="SRC-000001", outcome="plausible_in_scope", assessment_fingerprint="a"*64),
        SimpleNamespace(source_id="SRC-000002", outcome="uncertain", assessment_fingerprint="b"*64),
    ))
    monkeypatch.setattr(s, "_source_input", lambda **kwargs: (SimpleNamespace(), next(fits)))
    monkeypatch.setattr(
        module,
        "derive_project_fit_gate_state",
        lambda fit: "admitted" if fit.outcome == "plausible_in_scope" else "human_resolution_required",
    )
    with pytest.raises(ProjectReconciliationOrchestrationError, match="explicit Human resolution"):
        s.start("120412", provider="openai", model="gpt-5.4-mini")


def test_existing_exact_input_reuses_cycle_without_s3_call(monkeypatch):
    cycle = SimpleNamespace(
        reconciliation_cycle_id="PRC-000007",
        project_fit_fingerprints=("a"*64, "b"*64),
    )
    repo = Repo((cycle,))
    repo.artifact = SimpleNamespace(
        input_fingerprint="i"*64,
        source_ids=("SRC-000001", "SRC-000002"),
        content_fingerprint="c"*64,
    )
    semantic = Semantic()
    s = service((
        item("SRC-000001", "RUN-000001"),
        item("SRC-000002", "RUN-000002"),
    ), repo=repo, semantic=semantic)
    values = iter((
        (SimpleNamespace(), SimpleNamespace(source_id="SRC-000001", outcome="plausible_in_scope", assessment_fingerprint="a"*64)),
        (SimpleNamespace(), SimpleNamespace(source_id="SRC-000002", outcome="plausible_in_scope", assessment_fingerprint="b"*64)),
    ))
    monkeypatch.setattr(s, "_source_input", lambda **kwargs: next(values))
    monkeypatch.setattr(module, "derive_project_fit_gate_state", lambda fit: "admitted")
    monkeypatch.setattr(module, "prepare_project_semantic_subjects", lambda values: ("120412", (), "i"*64))
    result = s.start("120412", provider="openai", model="gpt-5.4-mini")
    assert result.reused_existing_cycle is True
    assert result.reconciliation_cycle_id == "PRC-000007"
    assert getattr(semantic, "calls", 0) == 0


def test_new_input_calls_s3_and_starts_cycle(monkeypatch):
    repo = Repo()
    semantic = Semantic()
    s = service((
        item("SRC-000001", "RUN-000001"),
        item("SRC-000002", "RUN-000002"),
    ), repo=repo, semantic=semantic)
    values = iter((
        (SimpleNamespace(project_fit=SimpleNamespace(source_id="SRC-000001")), SimpleNamespace(source_id="SRC-000001", outcome="plausible_in_scope", assessment_fingerprint="a"*64)),
        (SimpleNamespace(project_fit=SimpleNamespace(source_id="SRC-000002")), SimpleNamespace(source_id="SRC-000002", outcome="plausible_in_scope", assessment_fingerprint="b"*64)),
    ))
    monkeypatch.setattr(s, "_source_input", lambda **kwargs: next(values))
    monkeypatch.setattr(module, "derive_project_fit_gate_state", lambda fit: "admitted")
    monkeypatch.setattr(module, "prepare_project_semantic_subjects", lambda values: ("120412", (), "i"*64))
    result = s.start("120412", provider="openai", model="gpt-5.4-mini")
    assert result.reused_existing_cycle is False
    assert semantic.calls == 1


def test_duplicate_cycles_same_input_fail_closed(monkeypatch):
    cycles = (
        SimpleNamespace(reconciliation_cycle_id="PRC-000001", project_fit_fingerprints=()),
        SimpleNamespace(reconciliation_cycle_id="PRC-000002", project_fit_fingerprints=()),
    )
    repo = Repo(cycles)
    repo.artifact = SimpleNamespace(
        input_fingerprint="i"*64,
        source_ids=("SRC-000001", "SRC-000002"),
        content_fingerprint="c"*64,
    )
    s = service((
        item("SRC-000001", "RUN-000001"),
        item("SRC-000002", "RUN-000002"),
    ), repo=repo)
    fits = iter((
        SimpleNamespace(source_id="SRC-000001", outcome="plausible_in_scope", assessment_fingerprint="a"*64),
        SimpleNamespace(source_id="SRC-000002", outcome="plausible_in_scope", assessment_fingerprint="b"*64),
    ))
    monkeypatch.setattr(s, "_source_input", lambda **kwargs: (SimpleNamespace(), next(fits)))
    monkeypatch.setattr(module, "derive_project_fit_gate_state", lambda fit: "admitted")
    monkeypatch.setattr(module, "prepare_project_semantic_subjects", lambda values: ("120412", (), "i"*64))
    with pytest.raises(ProjectReconciliationOrchestrationError, match="Multiple immutable"):
        s.start("120412", provider="openai", model="gpt-5.4-mini")

def test_superseded_legacy_review_does_not_block_current_source_authority(
    monkeypatch,
):
    repo = Repo()
    semantic = Semantic()
    s = service(
        (
            item(
                "SRC-000001",
                "RUN-000001",
                status="draft_review",
                current=False,
            ),
            item("SRC-000001", "RUN-000005"),
            item("SRC-000002", "RUN-000006"),
        ),
        repo=repo,
        semantic=semantic,
    )

    seen_runs = []
    values = iter(
        (
            (
                SimpleNamespace(
                    project_fit=SimpleNamespace(source_id="SRC-000001")
                ),
                SimpleNamespace(
                    source_id="SRC-000001",
                    outcome="plausible_in_scope",
                    assessment_fingerprint="a" * 64,
                ),
            ),
            (
                SimpleNamespace(
                    project_fit=SimpleNamespace(source_id="SRC-000002")
                ),
                SimpleNamespace(
                    source_id="SRC-000002",
                    outcome="plausible_in_scope",
                    assessment_fingerprint="b" * 64,
                ),
            ),
        )
    )

    def fake_source_input(**kwargs):
        seen_runs.append(kwargs["item"].processing_run_id)
        return next(values)

    monkeypatch.setattr(s, "_source_input", fake_source_input)
    monkeypatch.setattr(
        module,
        "derive_project_fit_gate_state",
        lambda fit: "admitted",
    )
    monkeypatch.setattr(
        module,
        "prepare_project_semantic_subjects",
        lambda values: ("120412", (), "i" * 64),
    )

    result = s.start(
        "120412",
        provider="openai",
        model="gpt-5.4-mini",
    )

    assert result.reused_existing_cycle is False
    assert semantic.calls == 1
    assert seen_runs == ["RUN-000005", "RUN-000006"]

def test_progress_reports_authority_fit_s3_and_persistence(monkeypatch):
    repo = Repo()
    semantic = Semantic()
    s = service(
        (
            item("SRC-000001", "RUN-000005"),
            item("SRC-000002", "RUN-000006"),
        ),
        repo=repo,
        semantic=semantic,
    )
    values = iter(
        (
            (
                SimpleNamespace(
                    project_fit=SimpleNamespace(source_id="SRC-000001")
                ),
                SimpleNamespace(
                    source_id="SRC-000001",
                    outcome="plausible_in_scope",
                    assessment_fingerprint="a" * 64,
                ),
            ),
            (
                SimpleNamespace(
                    project_fit=SimpleNamespace(source_id="SRC-000002")
                ),
                SimpleNamespace(
                    source_id="SRC-000002",
                    outcome="plausible_in_scope",
                    assessment_fingerprint="b" * 64,
                ),
            ),
        )
    )
    monkeypatch.setattr(s, "_source_input", lambda **kwargs: next(values))
    monkeypatch.setattr(
        module,
        "derive_project_fit_gate_state",
        lambda fit: "admitted",
    )
    monkeypatch.setattr(
        module,
        "prepare_project_semantic_subjects",
        lambda values: ("120412", (), "i" * 64),
    )

    events = []
    result = s.start(
        "120412",
        provider="openai",
        model="gpt-5.4-mini",
        progress_observer=events.append,
    )

    assert result.reconciliation_cycle_id == "PRC-000001"
    assert [event.stage for event in events] == [
        "authority_validation",
        "authority_validation",
        "project_fit",
        "project_fit",
        "project_fit",
        "project_fit",
        "semantic_reconciliation",
        "semantic_reconciliation",
        "persistence",
        "persistence",
    ]
    assert events[3].completed == 1
    assert events[5].completed == 2
    assert events[-1].message == "PRC-000001 persisted"


def test_s3_validation_failure_reports_exact_stage(monkeypatch):
    class InvalidSemantic:
        def reconcile(self, source_inputs, **kwargs):
            raise module.ProjectSemanticReconciliationValidationError(
                "Semantic relation outcome is unsupported."
            )

    s = service(
        (
            item("SRC-000001", "RUN-000005"),
            item("SRC-000002", "RUN-000006"),
        ),
        semantic=InvalidSemantic(),
    )
    values = iter(
        (
            (
                SimpleNamespace(),
                SimpleNamespace(
                    source_id="SRC-000001",
                    outcome="plausible_in_scope",
                    assessment_fingerprint="a" * 64,
                ),
            ),
            (
                SimpleNamespace(),
                SimpleNamespace(
                    source_id="SRC-000002",
                    outcome="plausible_in_scope",
                    assessment_fingerprint="b" * 64,
                ),
            ),
        )
    )
    monkeypatch.setattr(s, "_source_input", lambda **kwargs: next(values))
    monkeypatch.setattr(
        module,
        "derive_project_fit_gate_state",
        lambda fit: "admitted",
    )
    monkeypatch.setattr(
        module,
        "prepare_project_semantic_subjects",
        lambda values: ("120412", (), "i" * 64),
    )

    events = []
    with pytest.raises(
        ProjectReconciliationOrchestrationError,
        match="S3 response validation failed",
    ):
        s.start(
            "120412",
            provider="openai",
            model="gpt-5.4-mini",
            progress_observer=events.append,
        )

    assert events[-1].stage == "semantic_reconciliation"
    assert events[-1].event_type == "failed"


def test_persistence_failure_reports_separate_stage(monkeypatch):
    class FailingRepo(Repo):
        def start_cycle(self, reconciliation, fits):
            raise module.ProjectReconciliationPersistenceError(
                "Project Reconciliation cycle path is occupied."
            )

    repo = FailingRepo()
    semantic = Semantic()
    s = service(
        (
            item("SRC-000001", "RUN-000005"),
            item("SRC-000002", "RUN-000006"),
        ),
        repo=repo,
        semantic=semantic,
    )
    values = iter(
        (
            (
                SimpleNamespace(
                    project_fit=SimpleNamespace(source_id="SRC-000001")
                ),
                SimpleNamespace(
                    source_id="SRC-000001",
                    outcome="plausible_in_scope",
                    assessment_fingerprint="a" * 64,
                ),
            ),
            (
                SimpleNamespace(
                    project_fit=SimpleNamespace(source_id="SRC-000002")
                ),
                SimpleNamespace(
                    source_id="SRC-000002",
                    outcome="plausible_in_scope",
                    assessment_fingerprint="b" * 64,
                ),
            ),
        )
    )
    monkeypatch.setattr(s, "_source_input", lambda **kwargs: next(values))
    monkeypatch.setattr(
        module,
        "derive_project_fit_gate_state",
        lambda fit: "admitted",
    )
    monkeypatch.setattr(
        module,
        "prepare_project_semantic_subjects",
        lambda values: ("120412", (), "i" * 64),
    )

    events = []
    with pytest.raises(
        ProjectReconciliationOrchestrationError,
        match="PRC persistence failed",
    ):
        s.start(
            "120412",
            provider="openai",
            model="gpt-5.4-mini",
            progress_observer=events.append,
        )

    assert events[-1].stage == "persistence"
    assert events[-1].event_type == "failed"
