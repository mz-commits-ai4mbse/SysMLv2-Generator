from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

import modules.project_reconciliation.workflow_service as workflow_module
from modules.project_reconciliation.workflow_service import (
    ProjectAuthorityWorkflowService,
    ProjectReconciliationWorkflowError,
)


class _Repository:
    def __init__(self):
        self.cycle = SimpleNamespace(
            reconciliation_cycle_id="PRC-000001"
        )
        self.reconciliation = SimpleNamespace(
            project_id="120412",
            source_ids=("SRC-000001", "SRC-000002"),
            subjects=(
                SimpleNamespace(
                    subject_ref="project_subject:SRC-000001:SUBJ-000001",
                    source_id="SRC-000001",
                    canonical_label="Alpha",
                ),
                SimpleNamespace(
                    subject_ref="project_subject:SRC-000002:SUBJ-000001",
                    source_id="SRC-000002",
                    canonical_label="Beta",
                ),
            ),
            relations=(
                SimpleNamespace(
                    left_subject_ref=(
                        "project_subject:SRC-000001:SUBJ-000001"
                    ),
                    right_subject_ref=(
                        "project_subject:SRC-000002:SUBJ-000001"
                    ),
                    outcome="complementary",
                    rationale="Related but not equivalent.",
                    shared_concepts=("streaming",),
                    material_differences=("different scope",),
                ),
            ),
            unmatched_subject_refs=(),
        )
        self.bindings = None
        self.decisions = []
        self.state = None
        self.impact = None
        self.recorded = None

    def latest_cycle(self, project_id):
        return self.cycle

    def load_cycle(self, project_id, cycle_id):
        return self.cycle

    def load_semantic_reconciliation(self, project_id, cycle_id):
        return self.reconciliation

    def load_authority_bindings_if_available(self, project_id, cycle_id):
        return self.bindings

    def load_authority_bindings(self, project_id, cycle_id):
        if self.bindings is None:
            raise RuntimeError("missing")
        return self.bindings

    def list_authority_decisions(self, project_id, cycle_id):
        return tuple(self.decisions)

    def load_authority_state_if_available(self, project_id, cycle_id):
        return self.state

    def load_authority_state(self, project_id, cycle_id):
        if self.state is None:
            raise RuntimeError("missing")
        return self.state

    def load_model_impact_if_available(self, project_id, cycle_id):
        return self.impact

    def publish_authority_bindings(self, project_id, cycle_id, bindings):
        self.bindings = SimpleNamespace(bindings=tuple(bindings))
        return self.bindings

    def next_authority_decision_id(self, project_id, cycle_id):
        return f"PEAD-{len(self.decisions) + 1:06d}"

    def next_authority_concern_id(self, project_id, cycle_id):
        return "PEAC-000001"

    def record_authority_decision(self, project_id, cycle_id, decision):
        self.decisions.append(decision)
        self.recorded = decision
        return decision

    def publish_authority_state(self, project_id, cycle_id, state):
        self.state = state
        return state

    def publish_model_impact(self, project_id, cycle_id, artifact):
        self.impact = artifact
        return artifact


class _Inputs:
    def list_manifests(self, project_id):
        return ("manifest",)

    def list_events(self, project_id):
        return ("event",)

    def list_active_approved_inputs(self, project_id):
        return (
            SimpleNamespace(
                source_id="SRC-000001",
                review_document_id="RVD-000001",
                review_document_version_id="RVV-000001",
            ),
            SimpleNamespace(
                source_id="SRC-000002",
                review_document_id="RVD-000002",
                review_document_version_id="RVV-000002",
            ),
        )


class _Reviews:
    def approved_engineering_information(
        self,
        project_id,
        document_id,
        version_id,
    ):
        return f"AEI:{document_id}:{version_id}"


def _binding(
    *,
    subject_ref="project_subject:SRC-000001:SUBJ-000001",
    approved_input_id="AIN-000001",
    review_document_id="RVD-000001",
    review_document_version_id="RVV-000001",
):
    return SimpleNamespace(
        subject_ref=subject_ref,
        approved_input_id=approved_input_id,
        review_document_id=review_document_id,
        review_document_version_id=review_document_version_id,
    )


def _service(repository=None, accepted_model_loader=None):
    return ProjectAuthorityWorkflowService(
        project_root=".",
        reconciliation_repository=repository or _Repository(),
        approved_input_repository=_Inputs(),
        review_workflow_service=_Reviews(),
        accepted_model_loader=(
            (lambda project_id: None)
            if accepted_model_loader is None
            else accepted_model_loader
        ),
        clock=lambda: datetime(
            2026, 8, 31, 8, 0, tzinfo=timezone.utc
        ),
    )


def test_review_before_binding_exposes_exact_machine_relation():
    service = _service()
    view = service.load_review("120412")

    assert view.cycle_id == "PRC-000001"
    assert view.workflow_status == "bindings_required"
    assert view.required_decision_count == 1
    row = view.relation_reviews[0]
    assert row.machine_outcome == "complementary"
    assert row.left_label == "Alpha"
    assert row.right_label == "Beta"
    assert row.human_decision_id is None


def test_prepare_bindings_delegates_to_s4_and_persists(monkeypatch):
    repository = _Repository()
    service = _service(repository)

    expected = (
        SimpleNamespace(
            subject_ref="left",
            approved_input_id="AIN-000001",
        ),
        SimpleNamespace(
            subject_ref="right",
            approved_input_id="AIN-000002",
        ),
    )
    captured = {}

    def fake_prepare(reconciliation, manifests, events, aeis):
        captured["reconciliation"] = reconciliation
        captured["manifests"] = manifests
        captured["events"] = events
        captured["aeis"] = aeis
        return expected

    monkeypatch.setattr(
        workflow_module,
        "prepare_project_authority_bindings",
        fake_prepare,
    )

    result = service.prepare_authority_bindings(
        "120412",
        "PRC-000001",
    )

    assert result.bindings == expected
    assert captured["manifests"] == ("manifest",)
    assert captured["events"] == ("event",)
    assert len(captured["aeis"]) == 2


def test_record_coexist_allocates_explicit_concern(monkeypatch):
    repository = _Repository()
    repository.bindings = SimpleNamespace(bindings=("binding",))
    service = _service(repository)
    captured = {}

    def fake_create(
        reconciliation,
        bindings,
        **kwargs,
    ):
        captured.update(kwargs)
        return SimpleNamespace(
            decision_id=kwargs["decision_id"],
            left_subject_ref=min(
                kwargs["left_subject_ref"],
                kwargs["right_subject_ref"],
            ),
            right_subject_ref=max(
                kwargs["left_subject_ref"],
                kwargs["right_subject_ref"],
            ),
            outcome=kwargs["outcome"],
            authority_concern_id=kwargs["authority_concern_id"],
            retained_approved_input_ids=(),
            project_superseded_approved_input_ids=(),
        )

    monkeypatch.setattr(
        workflow_module,
        "create_project_authority_decision",
        fake_create,
    )

    left = repository.reconciliation.relations[0].left_subject_ref
    right = repository.reconciliation.relations[0].right_subject_ref
    service.record_authority_decision(
        "120412",
        "PRC-000001",
        left_subject_ref=left,
        right_subject_ref=right,
        outcome="coexist",
        reviewer_identity="MZ",
        rationale="Both remain valid for the project concern.",
    )

    assert captured["decision_id"] == "PEAD-000001"
    assert captured["authority_concern_id"] == "PEAC-000001"
    assert captured["decided_at"] == "2026-08-31T08:00:00Z"


def test_record_decision_requires_identity_and_rationale():
    repository = _Repository()
    repository.bindings = SimpleNamespace(bindings=("binding",))
    service = _service(repository)
    relation = repository.reconciliation.relations[0]

    with pytest.raises(ProjectReconciliationWorkflowError):
        service.record_authority_decision(
            "120412",
            "PRC-000001",
            left_subject_ref=relation.left_subject_ref,
            right_subject_ref=relation.right_subject_ref,
            outcome="remain_independent",
            reviewer_identity="",
            rationale="Reason",
        )

    with pytest.raises(ProjectReconciliationWorkflowError):
        service.record_authority_decision(
            "120412",
            "PRC-000001",
            left_subject_ref=relation.left_subject_ref,
            right_subject_ref=relation.right_subject_ref,
            outcome="remain_independent",
            reviewer_identity="MZ",
            rationale="",
        )


def test_finalize_authority_rejects_incomplete_human_decisions():
    repository = _Repository()
    repository.bindings = SimpleNamespace(bindings=("binding",))
    service = _service(repository)

    with pytest.raises(
        ProjectReconciliationWorkflowError,
        match="Every S3 relation",
    ):
        service.finalize_authority("120412", "PRC-000001")


def test_finalize_authority_rejects_stale_binding_snapshot(monkeypatch):
    repository = _Repository()
    frozen = (_binding(),)
    repository.bindings = SimpleNamespace(bindings=frozen)
    repository.decisions = [SimpleNamespace()]
    service = _service(repository)

    monkeypatch.setattr(
        workflow_module,
        "build_project_engineering_authority_state",
        lambda *args: SimpleNamespace(
            bindings=(
                _binding(
                    approved_input_id="AIN-999999",
                ),
            ),
            model_impact_ready=True,
        ),
    )

    with pytest.raises(
        ProjectReconciliationWorkflowError,
        match="differs from the frozen",
    ):
        service.finalize_authority("120412", "PRC-000001")


def test_finalize_unresolved_authority_persists_but_blocks_s5(monkeypatch):
    repository = _Repository()
    frozen = (_binding(),)
    repository.bindings = SimpleNamespace(bindings=frozen)
    repository.decisions = [SimpleNamespace()]
    service = _service(repository)

    state = SimpleNamespace(
        bindings=frozen,
        model_impact_ready=False,
    )
    monkeypatch.setattr(
        workflow_module,
        "build_project_engineering_authority_state",
        lambda *args: state,
    )

    assert (
        service.finalize_authority("120412", "PRC-000001")
        is state
    )

    with pytest.raises(
        ProjectReconciliationWorkflowError,
        match="blocked",
    ):
        service.reconcile_model_impact("120412", "PRC-000001")


def test_s5_uses_exact_accepted_model_loader_and_persists(monkeypatch):
    repository = _Repository()
    repository.state = SimpleNamespace(model_impact_ready=True)
    accepted = object()
    service = _service(
        repository,
        accepted_model_loader=lambda project_id: accepted,
    )
    captured = {}

    class FakeModule:
        pass

    def fake_reconcile(state, model):
        captured["state"] = state
        captured["model"] = model
        return SimpleNamespace(name="impact")

    import modules.model_impact_reconciliation as mir
    monkeypatch.setattr(
        mir,
        "reconcile_model_impact",
        fake_reconcile,
    )

    artifact = service.reconcile_model_impact(
        "120412",
        "PRC-000001",
    )
    assert artifact.name == "impact"
    assert captured["state"] is repository.state
    assert captured["model"] is accepted
    assert repository.impact is artifact


def test_review_after_completion_is_read_only_projection():
    repository = _Repository()
    repository.bindings = SimpleNamespace(
        bindings=(
            SimpleNamespace(
                subject_ref=(
                    "project_subject:SRC-000001:SUBJ-000001"
                ),
                approved_input_id="AIN-000001",
            ),
            SimpleNamespace(
                subject_ref=(
                    "project_subject:SRC-000002:SUBJ-000001"
                ),
                approved_input_id="AIN-000002",
            ),
        )
    )
    relation = repository.reconciliation.relations[0]
    repository.decisions = [
        SimpleNamespace(
            decision_id="PEAD-000001",
            left_subject_ref=min(
                relation.left_subject_ref,
                relation.right_subject_ref,
            ),
            right_subject_ref=max(
                relation.left_subject_ref,
                relation.right_subject_ref,
            ),
            outcome="remain_independent",
            authority_concern_id=None,
            retained_approved_input_ids=(
                "AIN-000001",
                "AIN-000002",
            ),
            project_superseded_approved_input_ids=(),
        )
    ]
    repository.state = SimpleNamespace(model_impact_ready=True)
    repository.impact = SimpleNamespace()
    service = _service(repository)

    view = service.load_review("120412")
    assert view.workflow_status == "complete"
    assert view.open_decision_count == 0
    assert view.model_impact_persisted is True
