
from __future__ import annotations

from types import SimpleNamespace

from modules.guided_workflow import GuidedWorkflowReadService


class DashboardFake:
    def __init__(self, source_view):
        self.source_view = source_view

    def project_overview(self, project_id):
        return SimpleNamespace(project_id=project_id)

    def source_processing_view(self, project_id):
        return self.source_view


class ReviewFake:
    def __init__(self, project_view, facts=()):
        self._project_view = project_view
        self._facts = tuple(facts)

    def project_view(self, project_id):
        return self._project_view

    def review_filter_facts(
        self,
        project_id,
        review_document_id,
        review_document_version_id,
    ):
        return self._facts


class CandidateFake:
    def __init__(self, candidate_sets=(), issues=()):
        self.result = SimpleNamespace(
            candidate_sets=tuple(candidate_sets),
            issues=tuple(issues),
        )

    def scan_project(self, project_id):
        return self.result


class ProposalFake:
    def __init__(self, proposals=None):
        self.proposals = proposals or {}

    def load_model_proposal(self, project_id, candidate_set_id):
        return self.proposals[candidate_set_id]


class FinalReviewFake:
    def __init__(self, revisions=(), issues=()):
        self.result = SimpleNamespace(
            revisions=tuple(revisions),
            issues=tuple(issues),
        )

    def scan(self, project_id):
        return self.result


class FinalReleaseFake:
    def __init__(self, gates=None):
        self.gates = gates or {}

    def evaluate(self, project_id, review_id, revision_id):
        return self.gates[revision_id]


class OutputFake:
    def __init__(self, packages=(), issues=()):
        self.result = SimpleNamespace(
            packages=tuple(packages),
            issues=tuple(issues),
        )

    def scan_project(self, project_id):
        return self.result


def _source_view(*rows, issues=()):
    return SimpleNamespace(
        sources=tuple(rows),
        issues=tuple(issues),
    )


def _source(
    *,
    state=None,
    blockers=(),
    failures=(),
):
    return SimpleNamespace(
        run_state=state,
        blocking_issue_codes=tuple(blockers),
        failure_issue_codes=tuple(failures),
    )


def _review_item(
    *,
    workflow_status="draft_review",
    outcomes=(("open", 1),),
    active=(),
    document_id="RVD-000001",
    version_id="RVV-000001",
):
    return SimpleNamespace(
        workflow_status=workflow_status,
        review_outcome_counts=tuple(outcomes),
        active_approved_input_ids=tuple(active),
        review_document_id=document_id,
        review_document_version_id=version_id,
    )


def _review_view(*items, issues=()):
    return SimpleNamespace(
        items=tuple(items),
        issues=tuple(issues),
    )


def _candidate_set(
    candidate_set_id,
    predecessor=None,
):
    return SimpleNamespace(
        manifest=SimpleNamespace(
            candidate_set_id=candidate_set_id,
            predecessor_candidate_set_id=predecessor,
        )
    )


def _proposal(
    *,
    decisions=0,
    blockers=0,
    gate="not_ready",
):
    return SimpleNamespace(
        required_human_decisions=tuple(
            SimpleNamespace()
            for _ in range(decisions)
        ),
        blocking_issues=tuple(
            SimpleNamespace()
            for _ in range(blockers)
        ),
        phase_i_gate_status=gate,
    )


def _revision_bundle(
    revision_id,
    *,
    review_id="FMR-000001",
    predecessor=None,
):
    return SimpleNamespace(
        revision=SimpleNamespace(
            final_model_review_id=review_id,
            final_model_review_revision_id=revision_id,
            predecessor_revision_id=predecessor,
        )
    )


def _gate(status, *blocker_codes):
    return SimpleNamespace(
        release_status=status,
        blockers=tuple(
            SimpleNamespace(code=code)
            for code in blocker_codes
        ),
    )


def _output(output_id):
    return SimpleNamespace(
        manifest=SimpleNamespace(
            output_package_id=output_id,
        )
    )


def _service(
    *,
    source_view=None,
    review_view=None,
    facts=(),
    candidate_sets=(),
    proposals=None,
    final_revisions=(),
    gates=None,
    outputs=(),
):
    return GuidedWorkflowReadService(
        project_root=".",
        dashboard_service=DashboardFake(
            source_view or _source_view()
        ),
        review_service=ReviewFake(
            review_view or _review_view(),
            facts=facts,
        ),
        candidate_repository=CandidateFake(
            candidate_sets=candidate_sets,
        ),
        model_proposal_service=ProposalFake(
            proposals=proposals,
        ),
        final_review_repository=FinalReviewFake(
            revisions=final_revisions,
        ),
        final_release_service=FinalReleaseFake(
            gates=gates,
        ),
        output_repository=OutputFake(
            packages=outputs,
        ),
    )


def test_empty_project_prioritizes_first_source():
    view = _service().load_view("000001")

    assert view.stages[0].presentation_status == "action_required"
    assert view.stages[1].presentation_status == "not_started"
    assert view.next_stage_id == "project_sources"
    assert view.next_action == "Add first source"


def test_human_decisions_are_prioritized_over_ordinary_navigation():
    review = _review_item(
        outcomes=(("open", 2),),
    )
    service = _service(
        source_view=_source_view(
            _source(state="awaiting_review")
        ),
        review_view=_review_view(review),
    )

    view = service.load_view("000001")
    human = view.stages[2]

    assert human.decision_count == 2
    assert human.presentation_status == "action_required"
    assert view.next_stage_id == "human_review"
    assert view.next_action == "Resolve 2 Human decisions"


def test_deferred_human_review_remains_required_work():
    review = _review_item(
        outcomes=(("deferred", 1),),
    )
    service = _service(
        source_view=_source_view(
            _source(state="awaiting_review")
        ),
        review_view=_review_view(review),
    )

    view = service.load_view("000001")
    human = view.stages[2]

    assert human.decision_count == 1
    assert human.presentation_status == "action_required"
    assert view.next_stage_id == "human_review"


def test_review_variance_is_derived_from_existing_consensus_facts():
    review = _review_item()
    facts = (
        SimpleNamespace(
            agent_disagreement_state="none"
        ),
        SimpleNamespace(
            agent_disagreement_state="majority_with_disagreement"
        ),
        SimpleNamespace(
            agent_disagreement_state="conflict"
        ),
    )
    service = _service(
        source_view=_source_view(
            _source(state="awaiting_review")
        ),
        review_view=_review_view(review),
        facts=facts,
    )

    view = service.load_view("000001")

    assert view.stages[2].variance_attention_count == 2
    assert view.work_summary.variance_attention_count == 2


def test_candidate_lineage_uses_head_for_display_not_implicit_latest():
    old = _candidate_set("MCS-000001")
    head = _candidate_set(
        "MCS-000002",
        predecessor="MCS-000001",
    )

    service = _service(
        candidate_sets=(old, head),
        proposals={
            "MCS-000002": _proposal(
                decisions=3,
            )
        },
    )

    view = service.load_view("000001")
    model_stage = view.stages[3]

    assert model_stage.target_entity_id == "MCS-000002"
    assert model_stage.decision_count == 3


def test_multiple_candidate_heads_do_not_select_write_target_implicitly():
    first = _candidate_set("MCS-000001")
    second = _candidate_set("MCS-000002")

    service = _service(
        candidate_sets=(first, second),
        proposals={
            "MCS-000001": _proposal(),
            "MCS-000002": _proposal(),
        },
    )

    view = service.load_view("000001")

    assert view.stages[3].target_entity_id is None


def test_ready_final_release_makes_human_release_next_action():
    revision = _revision_bundle("FRV-000001")

    service = _service(
        source_view=_source_view(
            _source(state="completed")
        ),
        review_view=_review_view(
            _review_item(
                workflow_status="approved_input_available",
                outcomes=(("accepted_as_generated", 1),),
                active=("AIN-000001",),
            )
        ),
        final_revisions=(revision,),
        gates={
            "FRV-000001": _gate(
                "ready_for_approval"
            )
        },
    )

    view = service.load_view("000001")
    final_stage = view.stages[4]

    assert final_stage.presentation_status == "action_required"
    assert final_stage.decision_count == 1


def test_approved_final_revision_makes_publication_ready():
    revision = _revision_bundle("FRV-000001")

    service = _service(
        final_revisions=(revision,),
        gates={
            "FRV-000001": _gate(
                "approved_for_publication"
            )
        },
    )

    view = service.load_view("000001")

    assert view.stages[4].presentation_status == "complete"
    assert view.stages[5].presentation_status == "ready"


def test_published_output_is_complete_and_explicitly_addressed():
    service = _service(
        outputs=(_output("OUT-000001"),),
    )

    view = service.load_view("000001")
    output_stage = view.stages[5]

    assert output_stage.presentation_status == "complete"
    assert output_stage.target_entity_id == "OUT-000001"
