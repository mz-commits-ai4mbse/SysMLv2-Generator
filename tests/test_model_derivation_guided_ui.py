"""R5c Guided Workflow UI tests for model derivation actions."""

from __future__ import annotations

from types import SimpleNamespace

from app.guided_workflow_detail_ui import render_model_proposal_ui
from app.turing_generator_navigation import (
    SESSION_PROJECT_ID,
    SESSION_SELECTED_ENTITY_ID,
)
from tests.test_guided_workflow_detail_ui import (
    FakeStreamlit,
    Service,
    proposal_view,
)


class ActionStreamlit(FakeStreamlit):
    def __init__(
        self,
        *,
        selection=None,
        clicked_keys=(),
        text_values=None,
    ):
        super().__init__(selection=selection)
        self.clicked_keys = set(clicked_keys)
        self.text_values = dict(text_values or {})

    def button(self, label, *, key):
        self.calls.append(("button", label, key))
        return key in self.clicked_keys

    def text_input(self, label, *, key, **kwargs):
        self.calls.append(("text_input", label, key))
        return self.text_values.get(key, "")

    def text_area(self, label, *, key, **kwargs):
        self.calls.append(("text_area", label, key))
        return self.text_values.get(key, "")


class DerivationWrites:
    def __init__(self, assessment):
        self.assessment = assessment
        self.assess_calls = []
        self.generate_calls = []

    def assess_model_derivation(
        self,
        project_id,
        *,
        predecessor_candidate_set_id=None,
    ):
        self.assess_calls.append(
            (project_id, predecessor_candidate_set_id)
        )
        return self.assessment

    def generate_model_proposal(self, project_id, **kwargs):
        self.generate_calls.append((project_id, kwargs))
        return SimpleNamespace(
            manifest=SimpleNamespace(candidate_set_id="MCS-000002")
        )

    def record_candidate_review_decision(self, *args, **kwargs):
        raise AssertionError("No review write expected.")


def assessment(*, rejected=()):
    return SimpleNamespace(
        recommended_mode=(
            "llm_assisted" if rejected else "eco_deterministic"
        ),
        recommendation_reason_code=(
            "llm_review_rejection_escalation"
            if rejected
            else "eco_coverage_complete"
        ),
        eco_feasible=True,
        mapped_count=1,
        ambiguous_count=0,
        unmapped_count=0,
        intentionally_not_projected_count=0,
        rejected_predecessor_candidate_ids=tuple(rejected),
        escalated_approved_input_ids=(
            ("AIN-000001",) if rejected else ()
        ),
        rationale="Recommendation rationale.",
    )


def test_model_proposal_not_available_offers_eco_generation() -> None:
    st = ActionStreamlit(
        selection="eco_deterministic",
        clicked_keys={"guided_model.generate"},
    )
    st.session_state[SESSION_PROJECT_ID] = "123456"
    writes = DerivationWrites(assessment())

    render_model_proposal_ui(
        ".",
        streamlit_module=st,
        detail_service=Service(status="not_available"),
        write_service=writes,
    )

    assert writes.assess_calls == [("123456", None)]
    assert len(writes.generate_calls) == 1
    project_id, kwargs = writes.generate_calls[0]
    assert project_id == "123456"
    assert kwargs["mode"] == "eco_deterministic"
    assert (
        st.session_state[SESSION_SELECTED_ENTITY_ID]
        == "MCS-000002"
    )
    assert st.rerun_count == 1


def test_rejected_candidate_offers_llm_regeneration() -> None:
    proposal = proposal_view()
    proposal.proposed_elements[0].review_state = SimpleNamespace(
        status="rejected"
    )

    st = ActionStreamlit(
        clicked_keys={"guided_model.regenerate_llm"},
        text_values={
            "guided_model.regeneration_reason": (
                "Reconsider the architecture mapping."
            ),
            "guided_model.regeneration.api_key": "test-key",
        },
    )
    st.session_state[SESSION_PROJECT_ID] = "123456"
    writes = DerivationWrites(
        assessment(rejected=("MCE-000001",))
    )

    render_model_proposal_ui(
        ".",
        streamlit_module=st,
        detail_service=Service(proposal=proposal),
        write_service=writes,
    )

    assert writes.assess_calls == [
        ("123456", "MCS-000001")
    ]
    assert len(writes.generate_calls) == 1
    _project_id, kwargs = writes.generate_calls[0]
    assert kwargs["mode"] == "llm_assisted"
    assert (
        kwargs["predecessor_candidate_set_id"]
        == "MCS-000001"
    )
    assert kwargs["human_regeneration_reason"] == (
        "Reconsider the architecture mapping."
    )
    assert (
        st.session_state[SESSION_SELECTED_ENTITY_ID]
        == "MCS-000002"
    )
