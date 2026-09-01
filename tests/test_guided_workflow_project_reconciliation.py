from __future__ import annotations

from types import SimpleNamespace

from modules.guided_workflow.presentation import (
    build_guided_workflow_view,
    create_stage_view,
)
from modules.guided_workflow.read_model import GuidedWorkflowReadService
from modules.guided_workflow.types import GUIDED_WORKFLOW_STAGE_IDS


def _human_stage(status="complete"):
    semantic = "positive" if status == "complete" else "attention"
    return create_stage_view(
        stage_id="human_review",
        presentation_status=status,
        semantic=semantic,
        summary="Human Review test state.",
    )


def _reconciliation_stage(status):
    semantic = {
        "complete": "positive",
        "ready": "informational",
        "action_required": "attention",
        "in_progress": "informational",
        "blocked": "blocking",
        "unavailable": "blocking",
        "not_started": "neutral",
    }[status]
    return create_stage_view(
        stage_id="project_reconciliation",
        presentation_status=status,
        semantic=semantic,
        summary="Project Reconciliation test state.",
    )


class _Review:
    def __init__(self, source_workflow_count):
        self._items = tuple(
            SimpleNamespace(
                workflow_status="approved_input_available",
                active_approved_input_ids=(f"AIN-{i:06d}",),
            )
            for i in range(1, source_workflow_count + 1)
        )

    def project_view(self, project_id):
        return SimpleNamespace(items=self._items)


class _Reconciliation:
    def __init__(
        self,
        *,
        cycle=None,
        relations=(),
        bindings=None,
        decisions=(),
        state=None,
        impact=None,
        fail=False,
    ):
        self.cycle = cycle
        self.relations = tuple(relations)
        self.bindings = bindings
        self.decisions = tuple(decisions)
        self.state = state
        self.impact = impact
        self.fail = fail

    def latest_cycle(self, project_id):
        if self.fail:
            raise RuntimeError("repository unavailable")
        return self.cycle

    def load_semantic_reconciliation(self, project_id, cycle_id):
        return SimpleNamespace(relations=self.relations)

    def load_authority_bindings_if_available(self, project_id, cycle_id):
        return self.bindings

    def list_authority_decisions(self, project_id, cycle_id):
        return self.decisions

    def load_authority_state_if_available(self, project_id, cycle_id):
        return self.state

    def load_model_impact_if_available(self, project_id, cycle_id):
        return self.impact


class _Candidates:
    def __init__(self, candidate_sets=(), issues=()):
        self._candidate_sets = tuple(candidate_sets)
        self._issues = tuple(issues)

    def scan_project(self, project_id):
        return SimpleNamespace(
            candidate_sets=self._candidate_sets,
            issues=self._issues,
        )


class _ModelProposals:
    def load_model_proposal(self, project_id, candidate_set_id):
        raise AssertionError(
            "Model Proposal must not be loaded before reconciliation gate."
        )


def _service(
    *,
    source_workflow_count,
    reconciliation,
    candidate_sets=(),
):
    service = object.__new__(GuidedWorkflowReadService)
    service._review = _Review(source_workflow_count)
    service._reconciliation = reconciliation
    service._candidates = _Candidates(candidate_sets)
    service._model_proposals = _ModelProposals()
    return service


def _cycle():
    return SimpleNamespace(reconciliation_cycle_id="PRC-000001")


def _relation(left, right):
    return SimpleNamespace(
        left_subject_ref=left,
        right_subject_ref=right,
    )


def _decision(left, right):
    return SimpleNamespace(
        left_subject_ref=left,
        right_subject_ref=right,
    )


def test_canonical_guided_workflow_has_project_reconciliation_stage():
    assert GUIDED_WORKFLOW_STAGE_IDS == (
        "project_sources",
        "processing",
        "human_review",
        "project_reconciliation",
        "model_proposal",
        "final_model_review",
        "published_output",
    )


def test_single_source_human_complete_bypasses_project_reconciliation():
    service = _service(
        source_workflow_count=1,
        reconciliation=_Reconciliation(),
    )
    stage = service._project_reconciliation_stage(
        "120412",
        human_stage=_human_stage(),
    )
    assert stage.presentation_status == "complete"
    assert stage.decision_count == 0

    model = service._model_proposal_stage(
        "120412",
        human_stage=_human_stage(),
        reconciliation_stage=stage,
    )
    assert model.presentation_status == "ready"
    assert model.action_label == "Create model proposal"


def test_single_source_human_incomplete_does_not_open_model_gate():
    service = _service(
        source_workflow_count=1,
        reconciliation=_Reconciliation(),
    )
    human = _human_stage("action_required")
    stage = service._project_reconciliation_stage(
        "120412",
        human_stage=human,
    )
    assert stage.presentation_status == "not_started"

    model = service._model_proposal_stage(
        "120412",
        human_stage=human,
        reconciliation_stage=stage,
    )
    assert model.presentation_status == "not_started"


def test_multi_source_complete_human_review_requires_reconciliation_cycle():
    service = _service(
        source_workflow_count=2,
        reconciliation=_Reconciliation(),
    )
    stage = service._project_reconciliation_stage(
        "120412",
        human_stage=_human_stage(),
    )
    assert stage.presentation_status == "ready"
    assert stage.action_label == "Start project reconciliation"

    model = service._model_proposal_stage(
        "120412",
        human_stage=_human_stage(),
        reconciliation_stage=stage,
    )
    assert model.presentation_status == "not_started"


def test_multi_source_missing_s4_decisions_is_action_required():
    relation_a = _relation("project_subject:src-1:a", "project_subject:src-2:b")
    relation_b = _relation("project_subject:src-1:c", "project_subject:src-2:d")
    service = _service(
        source_workflow_count=2,
        reconciliation=_Reconciliation(
            cycle=_cycle(),
            relations=(relation_a, relation_b),
            bindings=SimpleNamespace(bindings=(object(), object())),
            decisions=(
                _decision(
                    relation_a.left_subject_ref,
                    relation_a.right_subject_ref,
                ),
            ),
        ),
    )
    stage = service._project_reconciliation_stage(
        "120412",
        human_stage=_human_stage(),
    )
    assert stage.presentation_status == "action_required"
    assert stage.decision_count == 1
    assert stage.target_entity_id == "PRC-000001"


def test_multi_source_unresolved_s4_state_blocks_model_proposal():
    relation = _relation("project_subject:src-1:a", "project_subject:src-2:b")
    reconciliation = _Reconciliation(
        cycle=_cycle(),
        relations=(relation,),
        bindings=SimpleNamespace(bindings=(object(), object())),
        decisions=(
            _decision(relation.left_subject_ref, relation.right_subject_ref),
        ),
        state=SimpleNamespace(
            model_impact_ready=False,
            unresolved_decision_ids=("PEAD-000001",),
        ),
    )
    service = _service(
        source_workflow_count=2,
        reconciliation=reconciliation,
    )
    stage = service._project_reconciliation_stage(
        "120412",
        human_stage=_human_stage(),
    )
    assert stage.presentation_status == "blocked"
    assert stage.blocking_issue_count == 1

    model = service._model_proposal_stage(
        "120412",
        human_stage=_human_stage(),
        reconciliation_stage=stage,
    )
    assert model.presentation_status == "not_started"


def test_multi_source_s4_and_s5_complete_opens_model_proposal_gate():
    relation = _relation("project_subject:src-1:a", "project_subject:src-2:b")
    service = _service(
        source_workflow_count=2,
        reconciliation=_Reconciliation(
            cycle=_cycle(),
            relations=(relation,),
            bindings=SimpleNamespace(bindings=(object(), object())),
            decisions=(
                _decision(
                    relation.left_subject_ref,
                    relation.right_subject_ref,
                ),
            ),
            state=SimpleNamespace(
                model_impact_ready=True,
                unresolved_decision_ids=(),
            ),
            impact=SimpleNamespace(content_fingerprint="f" * 64),
        ),
    )
    stage = service._project_reconciliation_stage(
        "120412",
        human_stage=_human_stage(),
    )
    assert stage.presentation_status == "complete"

    model = service._model_proposal_stage(
        "120412",
        human_stage=_human_stage(),
        reconciliation_stage=stage,
    )
    assert model.presentation_status == "ready"


def test_reconciliation_repository_failure_is_unavailable_and_gate_closed():
    service = _service(
        source_workflow_count=2,
        reconciliation=_Reconciliation(fail=True),
    )
    stage = service._project_reconciliation_stage(
        "120412",
        human_stage=_human_stage(),
    )
    assert stage.presentation_status == "unavailable"
    assert stage.blocking_issue_count == 1

    model = service._model_proposal_stage(
        "120412",
        human_stage=_human_stage(),
        reconciliation_stage=stage,
    )
    assert model.presentation_status == "not_started"


def test_existing_candidate_is_blocked_when_required_reconciliation_incomplete():
    candidate = SimpleNamespace(
        manifest=SimpleNamespace(
            candidate_set_id="MCS-000001",
            predecessor_candidate_set_id=None,
        )
    )
    service = _service(
        source_workflow_count=2,
        reconciliation=_Reconciliation(),
        candidate_sets=(candidate,),
    )
    stage = service._project_reconciliation_stage(
        "120412",
        human_stage=_human_stage(),
    )
    assert stage.presentation_status == "ready"

    model = service._model_proposal_stage(
        "120412",
        human_stage=_human_stage(),
        reconciliation_stage=stage,
    )
    assert model.presentation_status == "blocked"
    assert model.blocking_issue_count >= 1
    assert model.target_entity_id == "MCS-000001"


def test_next_action_routes_to_reconciliation_before_model_proposal():
    stages = (
        create_stage_view(
            stage_id="project_sources",
            presentation_status="complete",
            semantic="positive",
            summary="Sources complete.",
        ),
        create_stage_view(
            stage_id="processing",
            presentation_status="complete",
            semantic="positive",
            summary="Processing complete.",
        ),
        create_stage_view(
            stage_id="human_review",
            presentation_status="complete",
            semantic="positive",
            summary="Human Review complete.",
        ),
        create_stage_view(
            stage_id="project_reconciliation",
            presentation_status="ready",
            semantic="informational",
            summary="Reconciliation required.",
            action_label="Start project reconciliation",
        ),
        create_stage_view(
            stage_id="model_proposal",
            presentation_status="not_started",
            semantic="neutral",
            summary="No proposal yet.",
        ),
        create_stage_view(
            stage_id="final_model_review",
            presentation_status="not_started",
            semantic="neutral",
            summary="No final review yet.",
        ),
        create_stage_view(
            stage_id="published_output",
            presentation_status="not_started",
            semantic="neutral",
            summary="No output yet.",
        ),
    )
    view = build_guided_workflow_view(
        project_id="120412",
        stages=stages,
    )
    assert view.next_stage_id == "project_reconciliation"
    assert view.next_action == "Start project reconciliation"
