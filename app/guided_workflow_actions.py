"""Human write interactions for Guided Engineering Workflow detail views."""

from __future__ import annotations

from contextlib import nullcontext
from types import SimpleNamespace
from typing import Any

from app.turing_generator_navigation import (
    APP_VIEW_OUTPUT,
    queue_app_view,
)
from modules.guided_workflow.errors import GuidedWorkflowWriteError


SESSION_GUIDED_REVIEWER_IDENTITY = "guided_workflow.reviewer_identity"

_ACTIONABLE_CANDIDATE_STATES = frozenset(
    {
        "pending",
        "deferred",
        "stale",
    }
)

_CHANGE_CLASSIFICATIONS = {
    "Engineering meaning / model": "engineering_semantics",
    "Generated SysML representation": "generated_representation",
    "Validation result / validation tooling": "validation_policy_or_tool",
    "Review presentation only": "review_presentation_only",
}


def render_model_proposal_actions(
    st: Any,
    *,
    project_id: str,
    proposal,
    write_service,
    technical: bool,
    presentation=None,
) -> None:
    """Render decision-first Candidate Review against one exact Candidate Set."""

    element_by_id = {
        item.candidate_id: ("element_candidate", item)
        for item in proposal.proposed_elements
    }
    relationship_by_id = {
        item.candidate_id: ("relationship_candidate", item)
        for item in proposal.proposed_relationships
    }
    candidate_by_id = {
        **element_by_id,
        **relationship_by_id,
    }

    actionable = {
        candidate_id: (target_type, item)
        for candidate_id, (target_type, item) in candidate_by_id.items()
        if item.review_state.status in _ACTIONABLE_CANDIDATE_STATES
    }

    if presentation is not None:
        decisions = tuple(presentation.required_decisions)
        readiness = presentation.readiness
    else:
        decisions = tuple(
            SimpleNamespace(
                decision_key=f"{target_type}:{candidate_id}",
                target_type=target_type,
                target_ids=(candidate_id,),
                title=_candidate_title(target_type, item),
                reason="Candidate requires Human review.",
                recommended_action="Review this Candidate.",
            )
            for candidate_id, (target_type, item) in actionable.items()
        )
        readiness = None

    if not decisions:
        if readiness is not None and readiness.can_assemble:
            st.success(
                "Candidate review complete. The exact Candidate Set is ready "
                "for engineering-model assembly."
            )
        elif not actionable:
            st.success("No open Candidate Review decisions remain.")
        return

    st.subheader("Needs your decision")
    st.caption(
        "Decisions are recorded against the exact Candidate Set shown above. "
        "The visible state is reconstructed after every write."
    )

    reviewer = st.text_input(
        "Reviewer",
        key=SESSION_GUIDED_REVIEWER_IDENTITY,
        placeholder="Reviewer name",
    )

    for decision in decisions:
        targets = _decision_targets(
            decision,
            actionable=actionable,
            candidate_by_id=candidate_by_id,
        )

        with st.container(border=True):
            st.markdown(f"**{decision.title}**")
            st.caption(decision.reason)
            st.caption(decision.recommended_action)

            if decision.target_type == "relationship_choice_group":
                st.caption(
                    "Resolve the alternatives explicitly. Exactly one "
                    "relationship must ultimately be accepted."
                )

            if technical:
                st.caption(
                    "Exact targets: " + ", ".join(decision.target_ids)
                )

            if not targets:
                st.caption(
                    "This decision has no currently actionable Candidate. "
                    "Refresh the authoritative proposal state."
                )
                continue

            columns = (
                st.columns(min(3, len(targets)))
                if len(targets) > 1
                else (None,)
            )

            for index, (target_type, item) in enumerate(targets):
                context = (
                    nullcontext()
                    if columns[index % len(columns)] is None
                    else columns[index % len(columns)]
                )
                with context:
                    if _render_candidate_action_card(
                        st,
                        project_id=project_id,
                        proposal=proposal,
                        target_type=target_type,
                        item=item,
                        reviewer=reviewer,
                        write_service=write_service,
                        technical=technical,
                    ):
                        return


def _decision_targets(
    decision,
    *,
    actionable,
    candidate_by_id,
):
    targets = []
    for candidate_id in decision.target_ids:
        if candidate_id not in candidate_by_id:
            target_type = getattr(decision, "target_type", "unknown")
            raise GuidedWorkflowWriteError(
                "Candidate Review presentation references an unavailable "
                f"{target_type} target."
            )
        if candidate_id in actionable:
            targets.append(actionable[candidate_id])
    return tuple(targets)


def _render_candidate_action_card(
    st: Any,
    *,
    project_id: str,
    proposal,
    target_type: str,
    item,
    reviewer: str,
    write_service,
    technical: bool,
) -> bool:
    candidate_id = item.candidate_id
    conformance = item.conformance_status
    accept_decision = (
        "accepted"
        if conformance == "conformant"
        else "accepted_exception"
    )
    accept_label = (
        "Accept"
        if accept_decision == "accepted"
        else "Accept as exception"
    )

    st.markdown(f"**{_candidate_title(target_type, item)}**")
    st.caption(
        f"{_humanize(target_type)} · "
        f"{_humanize(item.review_state.status)}"
    )

    if target_type == "relationship_candidate":
        priority = getattr(item, "priority_class", None)
        if isinstance(priority, str) and priority:
            st.caption(f"Priority: {_humanize(priority)}")

    if technical:
        st.caption(
            f"Candidate: {candidate_id} · "
            f"Conformance: {conformance}"
        )

    rationale = st.text_area(
        "Rationale",
        key=f"guided_candidate.rationale.{candidate_id}",
        placeholder=(
            "Required for Reject, Defer, or acceptance as exception."
        ),
    )

    columns = st.columns(3)
    selected_decision = None

    if columns[0].button(
        accept_label,
        key=f"guided_candidate.accept.{candidate_id}",
    ):
        selected_decision = accept_decision

    if columns[1].button(
        "Reject",
        key=f"guided_candidate.reject.{candidate_id}",
    ):
        selected_decision = "rejected"

    if columns[2].button(
        "Defer",
        key=f"guided_candidate.defer.{candidate_id}",
    ):
        selected_decision = "deferred"

    if selected_decision is None:
        return False

    reviewer_value = reviewer.strip()
    rationale_value = rationale.strip()

    if not reviewer_value:
        st.error(
            "Enter the reviewer identity before recording a decision."
        )
        return True

    if (
        selected_decision
        in {
            "rejected",
            "deferred",
            "accepted_exception",
        }
        and not rationale_value
    ):
        st.error(
            "Provide a rationale for Reject, Defer, or acceptance "
            "as exception."
        )
        return True

    try:
        decision = write_service.record_candidate_review_decision(
            project_id,
            proposal.candidate_set_id,
            target_type=target_type,
            candidate_id=candidate_id,
            decision=selected_decision,
            reviewer_identity=reviewer_value,
            rationale=(
                rationale_value
                if rationale_value
                else None
            ),
        )
    except GuidedWorkflowWriteError:
        st.error(
            "The Candidate Review decision could not be recorded "
            "safely. No UI state was treated as authority."
        )
        return True

    st.success("Candidate Review decision recorded.")

    if technical:
        st.caption(
            "Decision: "
            f"{decision.model_candidate_review_decision_id}"
        )

    _rerun(st)
    return True


def render_final_review_actions(
    st: Any,
    *,
    project_id: str,
    detail,
    write_service,
    technical: bool,
) -> None:
    """Render change, release and publication actions for one exact FRV."""

    view = detail.review
    gate = detail.release_gate
    review_id = detail.final_model_review_id
    revision_id = detail.selected_entity_id

    if (
        view is None
        or gate is None
        or review_id is None
        or revision_id is None
    ):
        return

    st.subheader("Human actions")

    reviewer = st.text_input(
        "Reviewer",
        key=SESSION_GUIDED_REVIEWER_IDENTITY,
        placeholder="Reviewer name",
    )

    with st.expander("Request changes"):
        labels = tuple(_CHANGE_CLASSIFICATIONS)

        selected_label = st.selectbox(
            "What is affected?",
            options=labels,
            index=0,
            format_func=lambda value: value,
            key="guided_final.change_classification",
        )
        classification = _CHANGE_CLASSIFICATIONS[selected_label]

        feedback = st.text_area(
            "Feedback",
            key="guided_final.change_feedback",
            placeholder="Describe what should change and why.",
        )

        if st.button(
            "Submit change request",
            key="guided_final.submit_change",
        ):
            reviewer_value = reviewer.strip()
            feedback_value = feedback.strip()

            if not reviewer_value:
                st.error(
                    "Enter the reviewer identity before submitting a change request."
                )
                return

            if not feedback_value:
                st.error("Describe the requested change before submitting it.")
                return

            try:
                submission = write_service.submit_final_model_change(
                    project_id,
                    review_id,
                    revision_id,
                    surface="review_comment",
                    classification=classification,
                    reviewer_feedback=feedback_value,
                    created_by=reviewer_value,
                )
            except GuidedWorkflowWriteError:
                st.error(
                    "The change request could not be recorded safely. "
                    "The reviewed model was not mutated."
                )
                return

            st.success("Change request recorded.")

            if technical:
                st.caption(
                    "Authority route: "
                    f"{submission.route.authority_route}"
                )
                st.caption(submission.route.required_action)

            _rerun(st)
            return

    if gate.release_status == "ready_for_approval":
        st.markdown("**Ready for publication approval**")
        st.caption(
            "Validation and review gates are satisfied. "
            "Approval remains an explicit Human decision."
        )

        rationale = st.text_area(
            "Approval rationale (optional)",
            key="guided_final.approval_rationale",
        )

        if st.button(
            "Approve for publication",
            key="guided_final.approve",
        ):
            reviewer_value = reviewer.strip()

            if not reviewer_value:
                st.error(
                    "Enter the reviewer identity before approving publication."
                )
                return

            rationale_value = rationale.strip()

            try:
                approval = (
                    write_service.approve_final_model_for_publication(
                        project_id,
                        review_id,
                        revision_id,
                        reviewer_identity=reviewer_value,
                        rationale=(
                            rationale_value
                            if rationale_value
                            else None
                        ),
                    )
                )
            except GuidedWorkflowWriteError:
                st.error(
                    "Publication approval could not be recorded safely."
                )
                return

            st.success("Human publication approval recorded.")

            if technical:
                st.caption(
                    "Decision: "
                    f"{approval.decision.final_model_review_decision_id}"
                )

            _rerun(st)
            return

    elif gate.release_status == "approved_for_publication":
        st.success("Human release approval is recorded.")
        st.caption(
            "This exact approved revision can now be published."
        )

        if st.button(
            "Publish approved model",
            key="guided_final.publish",
        ):
            try:
                package = (
                    write_service.publish_final_model_review_revision(
                        project_id,
                        review_id,
                        revision_id,
                    )
                )
            except GuidedWorkflowWriteError:
                st.error(
                    "The approved model could not be published safely."
                )
                return

            output_id = package.manifest.output_package_id

            queue_app_view(
                st.session_state,
                active_view=APP_VIEW_OUTPUT,
                project_id=project_id,
                selected_entity_id=output_id,
            )

            st.success("Published Output created.")

            if technical:
                st.caption(f"Output package: {output_id}")

            _rerun(st)
            return

    else:
        st.caption(
            "Publication approval becomes available when the exact review "
            "revision satisfies the release gate."
        )


def _candidate_title(target_type: str, item) -> str:
    if target_type == "element_candidate":
        return item.proposed_name

    return (
        f"{item.source_subject_key} → "
        f"{item.target_subject_key}"
    )


def _humanize(value: str) -> str:
    return value.replace("_", " ").strip().capitalize()


def _rerun(st: Any) -> None:
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()
