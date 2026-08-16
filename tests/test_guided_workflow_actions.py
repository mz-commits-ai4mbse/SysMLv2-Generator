from __future__ import annotations

from types import SimpleNamespace

from app.guided_workflow_actions import (
    SESSION_GUIDED_REVIEWER_IDENTITY,
    render_final_review_actions,
    render_model_proposal_actions,
)
from app.turing_generator_navigation import (
    APP_VIEW_OUTPUT,
    SESSION_PENDING_NAVIGATION,
)


class Context:
    def __init__(self, st):
        self.st = st

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def button(self, label, *, key):
        return self.st.button(label, key=key)


class FakeStreamlit:
    def __init__(
        self,
        *,
        clicked=(),
        text_values=None,
        selected_values=None,
    ):
        self.session_state = {}
        self.clicked = set(clicked)
        self.text_values = text_values or {}
        self.selected_values = selected_values or {}
        self.calls = []
        self.rerun_count = 0

    def subheader(self, value):
        self.calls.append(("subheader", value))

    def caption(self, value):
        self.calls.append(("caption", value))

    def markdown(self, value):
        self.calls.append(("markdown", value))

    def error(self, value):
        self.calls.append(("error", value))

    def success(self, value):
        self.calls.append(("success", value))

    def text_input(self, label, *, key, **kwargs):
        self.calls.append(("text_input", label, key))
        return self.text_values.get(key, "")

    def text_area(self, label, *, key, **kwargs):
        self.calls.append(("text_area", label, key))
        return self.text_values.get(key, "")

    def button(self, label, *, key):
        self.calls.append(("button", label, key))
        return key in self.clicked

    def columns(self, count):
        return tuple(Context(self) for _ in range(count))

    def container(self, *, border=False):
        return Context(self)

    def expander(self, label):
        self.calls.append(("expander", label))
        return Context(self)

    def selectbox(
        self,
        label,
        *,
        options,
        index,
        format_func,
        key,
    ):
        self.calls.append(("selectbox", label, key))
        return self.selected_values.get(key, options[index])

    def rerun(self):
        self.rerun_count += 1


class WriteService:
    def __init__(self):
        self.candidate_calls = []
        self.change_calls = []
        self.approval_calls = []
        self.publication_calls = []

    def record_candidate_review_decision(
        self,
        project_id,
        candidate_set_id,
        **kwargs,
    ):
        self.candidate_calls.append(
            (project_id, candidate_set_id, kwargs)
        )
        return SimpleNamespace(
            model_candidate_review_decision_id="MCD-000001"
        )

    def submit_final_model_change(
        self,
        project_id,
        review_id,
        revision_id,
        **kwargs,
    ):
        self.change_calls.append(
            (project_id, review_id, revision_id, kwargs)
        )
        return SimpleNamespace(
            route=SimpleNamespace(
                authority_route="phase_h_candidate_review",
                required_action="Regenerate reviewed model.",
            )
        )

    def approve_final_model_for_publication(
        self,
        project_id,
        review_id,
        revision_id,
        **kwargs,
    ):
        self.approval_calls.append(
            (project_id, review_id, revision_id, kwargs)
        )
        return SimpleNamespace(
            decision=SimpleNamespace(
                final_model_review_decision_id="FRD-000001"
            )
        )

    def publish_final_model_review_revision(
        self,
        project_id,
        review_id,
        revision_id,
    ):
        self.publication_calls.append(
            (project_id, review_id, revision_id)
        )
        return SimpleNamespace(
            manifest=SimpleNamespace(
                output_package_id="OUT-000001"
            )
        )


def element(
    *,
    conformance="conformant",
    status="pending",
):
    return SimpleNamespace(
        candidate_id="MCE-000001",
        proposed_name="System",
        conformance_status=conformance,
        review_state=SimpleNamespace(status=status),
    )


def proposal(item):
    return SimpleNamespace(
        candidate_set_id="MCS-000001",
        proposed_elements=(item,),
        proposed_relationships=(),
    )


def final_detail(status):
    return SimpleNamespace(
        review=SimpleNamespace(),
        release_gate=SimpleNamespace(
            release_status=status,
        ),
        final_model_review_id="FMR-000001",
        selected_entity_id="FRV-000001",
    )


def test_candidate_accept_delegates_exact_candidate_target():
    st = FakeStreamlit(
        clicked=("guided_candidate.accept.MCE-000001",),
        text_values={
            SESSION_GUIDED_REVIEWER_IDENTITY: "Reviewer A",
        },
    )
    writes = WriteService()

    render_model_proposal_actions(
        st,
        project_id="123456",
        proposal=proposal(element()),
        write_service=writes,
        technical=False,
    )

    assert writes.candidate_calls == [
        (
            "123456",
            "MCS-000001",
            {
                "target_type": "element_candidate",
                "candidate_id": "MCE-000001",
                "decision": "accepted",
                "reviewer_identity": "Reviewer A",
                "rationale": None,
            },
        )
    ]
    assert st.rerun_count == 1


def test_nonconformant_candidate_uses_explicit_exception_decision():
    st = FakeStreamlit(
        clicked=("guided_candidate.accept.MCE-000001",),
        text_values={
            SESSION_GUIDED_REVIEWER_IDENTITY: "Reviewer A",
            "guided_candidate.rationale.MCE-000001": (
                "Reviewed intentional deviation."
            ),
        },
    )
    writes = WriteService()

    render_model_proposal_actions(
        st,
        project_id="123456",
        proposal=proposal(
            element(conformance="deviation")
        ),
        write_service=writes,
        technical=False,
    )

    assert (
        writes.candidate_calls[0][2]["decision"]
        == "accepted_exception"
    )
    assert writes.candidate_calls[0][2]["rationale"] == (
        "Reviewed intentional deviation."
    )


def test_reject_without_rationale_does_not_write():
    st = FakeStreamlit(
        clicked=("guided_candidate.reject.MCE-000001",),
        text_values={
            SESSION_GUIDED_REVIEWER_IDENTITY: "Reviewer A",
        },
    )
    writes = WriteService()

    render_model_proposal_actions(
        st,
        project_id="123456",
        proposal=proposal(element()),
        write_service=writes,
        technical=False,
    )

    assert writes.candidate_calls == []
    assert any(
        call[0] == "error"
        and "rationale" in call[1]
        for call in st.calls
    )


def test_final_change_uses_explicit_revision_and_review_comment_surface():
    st = FakeStreamlit(
        clicked=("guided_final.submit_change",),
        text_values={
            SESSION_GUIDED_REVIEWER_IDENTITY: "Reviewer A",
            "guided_final.change_feedback": "Change the model meaning.",
        },
        selected_values={
            "guided_final.change_classification": (
                "Engineering meaning / model"
            ),
        },
    )
    writes = WriteService()

    render_final_review_actions(
        st,
        project_id="123456",
        detail=final_detail("blocked"),
        write_service=writes,
        technical=True,
    )

    assert writes.change_calls == [
        (
            "123456",
            "FMR-000001",
            "FRV-000001",
            {
                "surface": "review_comment",
                "classification": "engineering_semantics",
                "reviewer_feedback": "Change the model meaning.",
                "created_by": "Reviewer A",
            },
        )
    ]
    assert st.rerun_count == 1


def test_final_release_approval_targets_exact_revision():
    st = FakeStreamlit(
        clicked=("guided_final.approve",),
        text_values={
            SESSION_GUIDED_REVIEWER_IDENTITY: "Reviewer A",
            "guided_final.approval_rationale": "Release accepted.",
        },
    )
    writes = WriteService()

    render_final_review_actions(
        st,
        project_id="123456",
        detail=final_detail("ready_for_approval"),
        write_service=writes,
        technical=False,
    )

    assert writes.approval_calls == [
        (
            "123456",
            "FMR-000001",
            "FRV-000001",
            {
                "reviewer_identity": "Reviewer A",
                "rationale": "Release accepted.",
            },
        )
    ]
    assert st.rerun_count == 1


def test_publication_queues_exact_output_navigation():
    st = FakeStreamlit(
        clicked=("guided_final.publish",),
        text_values={
            SESSION_GUIDED_REVIEWER_IDENTITY: "Reviewer A",
        },
    )
    writes = WriteService()

    render_final_review_actions(
        st,
        project_id="123456",
        detail=final_detail("approved_for_publication"),
        write_service=writes,
        technical=False,
    )

    assert writes.publication_calls == [
        ("123456", "FMR-000001", "FRV-000001")
    ]
    assert st.session_state[SESSION_PENDING_NAVIGATION] == {
        "active_view": APP_VIEW_OUTPUT,
        "project_id": "123456",
        "dashboard_view": "overview",
        "selected_entity_id": "OUT-000001",
    }
    assert st.rerun_count == 1
