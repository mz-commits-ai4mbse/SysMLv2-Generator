"""Engineer-facing Human Model Placement Review UI."""

from __future__ import annotations

from contextlib import nullcontext
from typing import Any

from app.guided_workflow_actions import SESSION_GUIDED_REVIEWER_IDENTITY
from app.model_assembly_preview_ui import render_model_assembly_preview
from app.model_final_review_ui import render_model_final_review
import os
from modules.guided_workflow.errors import GuidedWorkflowWriteError
from modules.model_candidates.structure_profile import (
    DEFAULT_MODEL_STRUCTURE_PROFILE_PATH,
    load_model_structure_profile,
)
from modules.framework import DEFAULT_FRAMEWORK_TEMPLATE_PATH


_VIEW_LABELS = {
    "pending": "Pending Decisions",
    "reviewed": "Reviewed Decisions",
    "all": "All",
    "attention": "Needs Attention",
    "rejected": "Rejected",
}


def render_model_placement_review(
    st: Any,
    *,
    project_root,
    project_id: str,
    comparison,
    write_service,
    technical: bool = False,
) -> None:
    """Render Human Model Placement Review against one exact comparison."""

    try:
        state = write_service.model_placement_review_state(
            project_id,
            comparison.content_fingerprint,
        )
    except GuidedWorkflowWriteError:
        st.error(
            "Model Placement Review state could not be reconstructed safely."
        )
        return

    profile = load_model_structure_profile(
        project_root / DEFAULT_MODEL_STRUCTURE_PROFILE_PATH,
        framework_template_path=(
            project_root / DEFAULT_FRAMEWORK_TEMPLATE_PATH
        ),
    )
    labels = placement_rule_labels(profile)

    st.subheader("Human Model Placement Review")
    st.caption(
        "Sort approved engineering information into the RFLP / target "
        "framework before the model is assembled."
    )

    decided = (
        state.accepted_count
        + state.rejected_count
        + state.deferred_count
    )
    columns = st.columns(4)
    columns[0].metric("Decided", f"{decided} / {state.total_count}")
    columns[1].metric("Accepted", state.accepted_count)
    columns[2].metric("Pending", state.pending_count)
    columns[3].metric("Needs attention", _attention_count(comparison))

    _render_framework_summary(
        st,
        comparison=comparison,
        state=state,
        labels=labels,
    )

    latest = {
        item.approved_input_id: item
        for item in state.latest_decisions
    }

    view_mode = st.radio(
        "Review view",
        options=tuple(_VIEW_LABELS),
        index=0,
        format_func=_VIEW_LABELS.get,
        horizontal=True,
        key=(
            "guided_model_placement.view."
            f"{comparison.content_fingerprint}"
        ),
    )

    visible = placement_items_for_view(
        comparison.items,
        latest_decisions=latest,
        view_mode=view_mode,
    )

    if not visible:
        if view_mode == "pending":
            st.success("No pending Model Placement decisions remain.")
        else:
            st.info("No placements match the selected review view.")
        if state.is_complete:
            st.success(
                "Model Placement Review complete. "
                "The reviewed placements are ready for Model Assembly."
            )
            _render_post_placement_actions(
                st,
                project_id=project_id,
                comparison=comparison,
                profile=profile,
                write_service=write_service,
                technical=technical,
            )
        return

    reviewer = st.text_input(
        "Reviewer",
        key=SESSION_GUIDED_REVIEWER_IDENTITY,
        placeholder="Reviewer name",
    )

    for item in visible:
        _render_item(
            st,
            project_id=project_id,
            comparison=comparison,
            item=item,
            latest_decision=latest.get(item.approved_input_id),
            labels=labels,
            reviewer=reviewer,
            write_service=write_service,
            technical=technical,
        )

    if state.is_complete:
        st.success(
            "Model Placement Review complete. "
            "The reviewed placements are ready for Model Assembly."
        )
        _render_post_placement_actions(
            st,
            project_id=project_id,
            comparison=comparison,
            profile=profile,
            write_service=write_service,
            technical=technical,
        )


def placement_rule_labels(profile) -> dict[str, str]:
    """Human-readable RFLP labels from the exact pinned structure profile."""

    areas = {
        area.model_area_id: area
        for area in profile.model_areas
    }
    labels = {}
    for rule in profile.element_derivation_rules:
        area = areas[rule.model_area_id]
        level, _, area_tail = rule.model_area_id.partition(".")
        labels[rule.rule_id] = (
            f"{_humanize(level)} · "
            f"{_humanize(area_tail or rule.model_area_id)} · "
            f"{_humanize(rule.element_type)}"
        )
        if not area.framework_node_id:
            raise ValueError(
                "Model Structure Profile area lacks framework binding."
            )
    return labels


def placement_items_for_view(
    items,
    *,
    latest_decisions,
    view_mode: str,
):
    """Apply the familiar Pending/Reviewed/Attention review views."""

    if view_mode not in _VIEW_LABELS:
        raise ValueError("Unsupported Model Placement review view.")

    visible = []
    for item in items:
        decision = latest_decisions.get(item.approved_input_id)
        pending = decision is None or decision.outcome == "reopened"
        reviewed = (
            decision is not None
            and decision.outcome in {"accepted", "rejected", "deferred"}
        )

        if view_mode == "pending" and not pending:
            continue
        if view_mode == "reviewed" and not reviewed:
            continue
        if (
            view_mode == "attention"
            and not (
                item.review_attention_required
                or (
                    decision is not None
                    and decision.outcome == "reopened"
                )
            )
        ):
            continue
        if (
            view_mode == "rejected"
            and not (
                decision is not None
                and decision.outcome == "rejected"
            )
        ):
            continue
        visible.append(item)
    return tuple(visible)


def _render_post_placement_actions(
    st,
    *,
    project_id,
    comparison,
    profile,
    write_service,
    technical,
):
    try:
        placement_set = write_service.load_finalized_model_placement_set(
            project_id,
            comparison.content_fingerprint,
        )
    except GuidedWorkflowWriteError:
        st.error(
            "Finalized Model Placement authority could not be loaded safely."
        )
        return

    if placement_set is None:
        st.markdown("**Finalize placement authority**")
        st.caption(
            "Freeze the complete Human placement decisions before assembly."
        )
        if st.button(
            "Finalize model placements",
            key=(
                "guided_model_placement.finalize."
                f"{comparison.content_fingerprint}"
            ),
        ):
            try:
                write_service.finalize_model_placement_review(
                    project_id,
                    comparison.content_fingerprint,
                    profile=profile,
                )
            except GuidedWorkflowWriteError:
                st.error(
                    "Model Placement Review could not be finalized safely."
                )
                return
            st.success("Approved Model Placement Set finalized.")
            _rerun(st)
        return

    st.success("Approved Model Placement Set finalized.")

    try:
        draft = write_service.load_model_assembly_draft(
            project_id,
            comparison.content_fingerprint,
        )
    except GuidedWorkflowWriteError:
        st.error("Model Assembly Draft could not be loaded safely.")
        return

    if draft is None:
        st.markdown("**Assemble model draft**")
        st.caption(
            "Assembly preserves Human placements exactly. Exact accepted "
            "engineering Relationships are represented deterministically; "
            "non-exact Relationships remain unresolved for Human Final Model "
            "Review. No LLM is called during Model Assembly."
        )

        if st.button(
            "Assemble model draft",
            key=(
                "guided_model_placement.assemble."
                f"{comparison.content_fingerprint}"
            ),
        ):
            try:
                spinner = getattr(st, "spinner", None)
                if callable(spinner):
                    with spinner(
                        "Assembling Human-approved placements and accepted "
                        "engineering Relationships..."
                    ):
                        write_service.assemble_model_draft(
                            project_id,
                            comparison.content_fingerprint,
                        )
                else:
                    write_service.assemble_model_draft(
                        project_id,
                        comparison.content_fingerprint,
                    )
            except GuidedWorkflowWriteError:
                st.error(
                    "Model Assembly failed safely. "
                    "The approved placement authority remains unchanged."
                )
                return
            st.success("Model Assembly Draft created.")
            _rerun(st)
        return

    render_model_assembly_preview(
        st,
        draft=draft,
        technical=technical,
    )
    render_model_final_review(
        st,
        project_id=project_id,
        draft=draft,
        profile=profile,
        write_service=write_service,
        technical=technical,
    )


def _render_item(
    st,
    *,
    project_id,
    comparison,
    item,
    latest_decision,
    labels,
    reviewer,
    write_service,
    technical,
):
    context = (
        st.container(border=True)
        if callable(getattr(st, "container", None))
        else nullcontext()
    )
    with context:
        st.markdown(f"**{item.title}**")
        st.write(item.primary_text)

        info = _humanize(item.information_type or "unclassified")
        st.caption(f"Approved engineering information · {info}")
        if technical:
            st.caption(
                f"{item.approved_input_id} · "
                f"{item.stable_subject_key}"
            )

        _render_comparison_summary(st, item, labels=labels)

        if item.persona_proposals:
            with st.expander("Modeling persona proposals", expanded=False):
                for proposal in item.persona_proposals:
                    st.markdown(
                        f"**{_humanize(proposal.persona_id)}**"
                    )
                    if proposal.result == "proposed_mapping":
                        st.write(
                            labels.get(
                                proposal.selected_rule_id,
                                proposal.selected_rule_id,
                            )
                        )
                    elif proposal.result == "ambiguous":
                        st.write(
                            "Possible placements: "
                            + "; ".join(
                                labels.get(value, value)
                                for value in proposal.alternative_rule_ids
                            )
                        )
                    else:
                        st.write("No defensible placement proposed.")
                    st.caption(proposal.rationale)

        decided = (
            latest_decision is not None
            and latest_decision.outcome
            in {"accepted", "rejected", "deferred"}
        )
        if decided:
            _render_decided_item(
                st,
                project_id=project_id,
                comparison=comparison,
                item=item,
                decision=latest_decision,
                labels=labels,
                reviewer=reviewer,
                write_service=write_service,
                technical=technical,
            )
            return

        if (
            latest_decision is not None
            and latest_decision.outcome == "reopened"
        ):
            st.warning("This placement was reopened and requires a new decision.")
            if latest_decision.rationale:
                st.caption(
                    "Reopen rationale: "
                    f"{latest_decision.rationale}"
                )

        options = (None, *item.allowed_rule_ids)
        default = _default_rule(item)
        index = options.index(default) if default in options else 0
        selected_rule = st.selectbox(
            "RFLP / model placement",
            options=options,
            index=index,
            format_func=lambda value: (
                "Select placement…"
                if value is None
                else labels.get(value, value)
            ),
            key=(
                "guided_model_placement.rule."
                f"{comparison.content_fingerprint}."
                f"{item.approved_input_id}"
            ),
        )
        if selected_rule is not None:
            st.caption(
                "Selected target: "
                + labels.get(selected_rule, selected_rule)
            )

        rationale = st.text_area(
            "Rationale",
            key=(
                "guided_model_placement.rationale."
                f"{comparison.content_fingerprint}."
                f"{item.approved_input_id}"
            ),
            placeholder=(
                "Required for Reject and when resolving placement variance."
            ),
        )

        columns = st.columns(3)
        if columns[0].button(
            "Accept placement",
            key=(
                "guided_model_placement.accept."
                f"{comparison.content_fingerprint}."
                f"{item.approved_input_id}"
            ),
        ):
            if not reviewer.strip():
                st.error("Enter a reviewer before recording the decision.")
                return
            if selected_rule is None:
                st.error("Select an RFLP / model placement first.")
                return
            if item.review_attention_required and not rationale.strip():
                st.error(
                    "Provide a rationale when resolving placement variance "
                    "or uncertainty."
                )
                return
            _record(
                st,
                write_service=write_service,
                project_id=project_id,
                comparison=comparison,
                approved_input_id=item.approved_input_id,
                outcome="accepted",
                selected_rule_id=selected_rule,
                reviewer=reviewer,
                rationale=rationale,
            )
            return

        if columns[1].button(
            "Reject",
            key=(
                "guided_model_placement.reject."
                f"{comparison.content_fingerprint}."
                f"{item.approved_input_id}"
            ),
        ):
            if not reviewer.strip():
                st.error("Enter a reviewer before recording the decision.")
                return
            if not rationale.strip():
                st.error("Provide a rationale to reject this placement.")
                return
            _record(
                st,
                write_service=write_service,
                project_id=project_id,
                comparison=comparison,
                approved_input_id=item.approved_input_id,
                outcome="rejected",
                selected_rule_id=None,
                reviewer=reviewer,
                rationale=rationale,
            )
            return

        if columns[2].button(
            "Defer",
            key=(
                "guided_model_placement.defer."
                f"{comparison.content_fingerprint}."
                f"{item.approved_input_id}"
            ),
        ):
            if not reviewer.strip():
                st.error("Enter a reviewer before recording the decision.")
                return
            _record(
                st,
                write_service=write_service,
                project_id=project_id,
                comparison=comparison,
                approved_input_id=item.approved_input_id,
                outcome="deferred",
                selected_rule_id=None,
                reviewer=reviewer,
                rationale=rationale,
            )


def _render_decided_item(
    st,
    *,
    project_id,
    comparison,
    item,
    decision,
    labels,
    reviewer,
    write_service,
    technical,
):
    if decision.outcome == "accepted":
        st.success(
            "Placement accepted: "
            + labels.get(
                decision.selected_rule_id,
                decision.selected_rule_id,
            )
        )
    elif decision.outcome == "rejected":
        st.error("Placement rejected.")
    else:
        st.warning("Placement deferred.")

    if decision.rationale:
        st.caption(f"Human rationale: {decision.rationale}")
    if technical:
        st.caption(
            f"Decision: {decision.decision_id} · "
            f"{_humanize(decision.outcome)}"
        )

    reopen_rationale = st.text_area(
        "Reopen rationale",
        key=(
            "guided_model_placement.reopen_rationale."
            f"{comparison.content_fingerprint}."
            f"{item.approved_input_id}"
        ),
        placeholder="Why should this placement be reconsidered?",
    )
    if st.button(
        "Reopen decision",
        key=(
            "guided_model_placement.reopen."
            f"{comparison.content_fingerprint}."
            f"{item.approved_input_id}"
        ),
    ):
        if not reviewer.strip():
            st.error("Enter a reviewer before reopening the decision.")
            return
        if not reopen_rationale.strip():
            st.error("Provide a rationale to reopen this placement.")
            return
        try:
            write_service.reopen_model_placement_review_decision(
                project_id,
                comparison.content_fingerprint,
                approved_input_id=item.approved_input_id,
                reviewer_identity=reviewer.strip(),
                rationale=reopen_rationale.strip(),
            )
        except GuidedWorkflowWriteError:
            st.error(
                "Model Placement decision could not be reopened safely."
            )
            return
        st.success("Model Placement decision reopened.")
        _rerun(st)


def _record(
    st,
    *,
    write_service,
    project_id,
    comparison,
    approved_input_id,
    outcome,
    selected_rule_id,
    reviewer,
    rationale,
):
    try:
        write_service.record_model_placement_review_decision(
            project_id,
            comparison.content_fingerprint,
            approved_input_id=approved_input_id,
            outcome=outcome,
            selected_rule_id=selected_rule_id,
            reviewer_identity=reviewer.strip(),
            rationale=rationale.strip() or None,
        )
    except GuidedWorkflowWriteError:
        st.error(
            "Model Placement decision could not be recorded safely."
        )
        return
    st.success("Model Placement decision recorded.")
    _rerun(st)


def _render_comparison_summary(st, item, *, labels):
    if item.agreement_level == "unanimous_mapping":
        st.success(
            "Modeling personas agree: "
            + labels.get(item.unanimous_rule_id, item.unanimous_rule_id)
        )
    elif item.agreement_level == "partial_mapping_agreement":
        st.warning(
            "Partial modeling agreement — Human placement decision required."
        )
    elif item.agreement_level == "placement_variance":
        st.warning(
            "Modeling variance — multiple RFLP / model placements were proposed."
        )
    else:
        st.warning(
            "Placement unresolved — Human placement decision required."
        )

    if item.deterministic_candidate_rule_ids:
        st.caption(
            "Deterministic profile options: "
            + "; ".join(
                labels.get(value, value)
                for value in item.deterministic_candidate_rule_ids
            )
        )


def _render_framework_summary(st, *, comparison, state, labels):
    counts = {
        "Stakeholder": 0,
        "System": 0,
        "Subsystem": 0,
    }
    for decision in state.latest_decisions:
        if decision.outcome != "accepted":
            continue
        label = labels.get(decision.selected_rule_id, "")
        first = label.split(" · ", 1)[0]
        if first in counts:
            counts[first] += 1

    st.markdown("**Accepted placement overview**")
    columns = st.columns(3)
    for column, level in zip(columns, counts):
        column.metric(level, counts[level])


def _default_rule(item):
    if item.unanimous_rule_id in item.allowed_rule_ids:
        return item.unanimous_rule_id
    if (
        len(item.deterministic_candidate_rule_ids) == 1
        and item.deterministic_candidate_rule_ids[0]
        in item.allowed_rule_ids
    ):
        return item.deterministic_candidate_rule_ids[0]
    return None


def _attention_count(comparison) -> int:
    return sum(
        1 for item in comparison.items
        if item.review_attention_required
    )


def _humanize(value: str) -> str:
    return value.replace("_", " ").replace(".", " ").strip().title()


def _rerun(st) -> None:
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()
