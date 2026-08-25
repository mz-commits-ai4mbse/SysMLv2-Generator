"""Engineer-facing detail workspaces for Guided Workflow stages."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.guided_workflow_actions import (
    render_final_review_actions,
    render_model_proposal_actions,
)
from app.human_model_placement_review_ui import (
    render_model_placement_review,
)
from app.presentation_preferences import technical_details_enabled
from app.turing_generator_navigation import (
    SESSION_SELECTED_ENTITY_ID,
    read_navigation_state,
)
from modules.model_candidates import (
    ECO_DETERMINISTIC_MODE,
    LLM_ASSISTED_MODE,
)
from modules.guided_workflow import (
    GuidedWorkflowDetailReadService,
    GuidedWorkflowValidationError,
    GuidedWorkflowWriteError,
    GuidedWorkflowWriteService,
    build_model_proposal_presentation,
)


def render_model_proposal_ui(
    project_root: Path,
    *,
    streamlit_module: Any,
    detail_service: GuidedWorkflowDetailReadService | None = None,
    write_service: GuidedWorkflowWriteService | None = None,
) -> None:
    """Render one exact Model Proposal without changing Candidate authority."""

    st = streamlit_module
    root = Path(project_root)
    navigation = read_navigation_state(st.session_state)
    technical = technical_details_enabled(st.session_state)
    service = (
        GuidedWorkflowDetailReadService(root)
        if detail_service is None
        else detail_service
    )
    writes = (
        GuidedWorkflowWriteService(root)
        if write_service is None
        else write_service
    )

    st.header("Model Proposal")
    st.caption(
        "Review the proposed architecture, resolve material alternatives "
        "and prepare the exact Candidate Set for engineering-model assembly."
    )

    if navigation.project_id is None:
        st.info("Select a Project in the application header.")
        return

    selected_id = _selected_entity(
        navigation.selected_entity_id,
        "MCS-",
    )

    try:
        detail = service.load_model_proposal(
            navigation.project_id,
            selected_id,
        )
    except GuidedWorkflowValidationError:
        st.error(
            "The Model Proposal cannot be reconstructed safely from "
            "the current authoritative Project state."
        )
        return
    except Exception:
        st.error("The Model Proposal is currently unavailable.")
        return

    if detail.status == "not_available":
        placement_loader = getattr(
            writes,
            "list_model_placement_comparisons",
            None,
        )
        if callable(placement_loader):
            try:
                placement_comparisons = placement_loader(
                    navigation.project_id
                )
            except GuidedWorkflowWriteError:
                st.error(
                    "Model Placement Review state could not be loaded safely."
                )
                return
        else:
            # Compatibility for injected legacy/test write services.
            placement_comparisons = ()

        if placement_comparisons:
            comparison = (
                placement_comparisons[0]
                if len(placement_comparisons) == 1
                else st.selectbox(
                    "Model Placement review bundle",
                    options=placement_comparisons,
                    format_func=lambda value: (
                        value.content_fingerprint[:12]
                    ),
                    key="guided_model_placement.comparison",
                )
            )
            render_model_placement_review(
                st,
                project_root=root,
                project_id=navigation.project_id,
                comparison=comparison,
                write_service=writes,
                technical=technical,
            )
            return

        st.info(
            "No Model Proposal is available yet. "
            "Model Placement must be resolved before model assembly."
        )
        _render_initial_model_derivation(
            st,
            project_id=navigation.project_id,
            write_service=writes,
            technical=technical,
        )
        return

    if detail.status == "selection_required":
        _render_explicit_selection(
            st,
            detail.options,
            label="Model Proposal",
            key="guided_detail.model_proposal",
            technical=technical,
        )
        return

    proposal = detail.proposal
    if proposal is None:
        st.error("The selected Model Proposal could not be resolved.")
        return

    try:
        presentation = build_model_proposal_presentation(proposal)
    except GuidedWorkflowValidationError:
        st.error(
            "The Model Proposal presentation cannot be reconstructed safely "
            "from the exact Candidate Set."
        )
        return

    st.write(presentation.summary)

    readiness = presentation.readiness
    columns = st.columns(4)
    columns[0].metric(
        "Candidates reviewed",
        f"{readiness.reviewed_candidates} / {readiness.total_candidates}",
    )
    columns[1].metric(
        "Accepted",
        readiness.accepted_candidates,
    )
    columns[2].metric(
        "Decisions required",
        readiness.decisions_required,
    )
    columns[3].metric(
        "Blocking issues",
        readiness.blocking_issues,
    )

    _render_model_readiness(st, readiness)

    st.subheader("Architecture proposal")
    _render_architecture_proposal(
        st,
        presentation,
        technical=technical,
    )

    if presentation.relationship_choices:
        st.subheader("Relationship alternatives")
        for choice in presentation.relationship_choices:
            _render_relationship_choice(
                st,
                choice,
                presentation.architecture_edges,
                technical=technical,
            )

    render_model_proposal_actions(
        st,
        project_id=navigation.project_id,
        proposal=proposal,
        write_service=writes,
        technical=technical,
        presentation=presentation,
    )

    _render_model_review_regeneration(
        st,
        project_id=navigation.project_id,
        proposal=proposal,
        write_service=writes,
        technical=technical,
    )

    if presentation.deviations:
        st.subheader("Structural attention")
        for deviation in presentation.deviations:
            with st.container(border=True):
                st.markdown(f"**{deviation.title}**")
                st.caption(
                    f"{_humanize(deviation.conformance_status)} · "
                    f"{_humanize(deviation.review_status)}"
                )
                if deviation.rationale:
                    st.write(deviation.rationale)
                if technical:
                    st.caption(f"Candidate: {deviation.candidate_id}")
                    if deviation.finding_ids:
                        st.caption(
                            "Findings: "
                            + ", ".join(deviation.finding_ids)
                        )
                    if deviation.deviation_ids:
                        st.caption(
                            "Deviations: "
                            + ", ".join(deviation.deviation_ids)
                        )

    st.subheader("Structural comparability")
    comparison = presentation.comparability
    if comparison.semantic == "positive":
        st.success(comparison.label)
    elif comparison.semantic == "attention":
        st.warning(comparison.label)
    else:
        st.info(comparison.label)

    if technical:
        columns = st.columns(4)
        columns[0].metric("Improves", comparison.improves_count)
        columns[1].metric("Neutral", comparison.neutral_count)
        columns[2].metric("Reduces", comparison.reduces_count)
        columns[3].metric("Unknown", comparison.unknown_count)

    st.subheader("Next engineering step")
    st.info(presentation.next_action)

    if technical:
        with st.expander("Technical details"):
            st.caption(
                f"Candidate Set: {presentation.candidate_set_id}"
            )
            st.caption(
                "Candidate Set fingerprint: "
                f"{presentation.candidate_set_content_fingerprint}"
            )
            st.caption(
                f"Assembly gate: {readiness.phase_i_gate_status}"
            )
            st.write(presentation.generation_rationale_summary)

            _render_model_proposal_traceability(
                st,
                presentation,
            )

            if proposal.blocking_issues:
                st.markdown("**Blocking diagnostics**")
                for issue in proposal.blocking_issues:
                    st.caption(
                        f"{issue.code}: {issue.message}"
                    )



_MODEL_DERIVATION_LABELS = {
    ECO_DETERMINISTIC_MODE: "Eco / deterministic — no LLM",
    LLM_ASSISTED_MODE: "LLM-assisted — modeling personas",
}
_MODELING_MODEL_OPTIONS = (
    "gpt-5.4-mini",
    "gpt-5-mini",
    "gpt-4.1-mini",
    "gpt-4o-mini",
)


def _render_initial_model_derivation(
    st: Any,
    *,
    project_id: str,
    write_service,
    technical: bool,
) -> None:
    """Render advisory strategy plus explicit initial Phase-H action."""

    try:
        assessment = write_service.assess_model_derivation(project_id)
    except GuidedWorkflowWriteError:
        st.error(
            "Model derivation readiness could not be assessed safely."
        )
        return

    total = (
        assessment.mapped_count
        + assessment.ambiguous_count
        + assessment.unmapped_count
        + assessment.intentionally_not_projected_count
    )
    if total == 0:
        st.info(
            "No approved engineering information is available for "
            "model derivation yet."
        )
        return

    st.subheader("Choose derivation strategy")
    if assessment.recommended_mode == ECO_DETERMINISTIC_MODE:
        st.success(
            "Recommendation: Eco / deterministic. "
            "All projectable approved information is resolved by the "
            "deterministic profile."
        )
    else:
        st.warning(
            "Recommendation: LLM-assisted. Deterministic projection "
            "contains unresolved or ambiguous target mappings."
        )

    subject_count = getattr(
        assessment,
        "approved_subject_count",
        0,
    )
    relationship_count = getattr(
        assessment,
        "semantic_relationship_count",
        0,
    )

    if subject_count or relationship_count:
        st.markdown("**Approved Subjects**")
        subject_columns = st.columns(4)
        subject_columns[0].metric("Total", subject_count)
        subject_columns[1].metric(
            "Mapped",
            assessment.approved_subject_mapped_count,
        )
        subject_columns[2].metric(
            "Ambiguous",
            assessment.approved_subject_ambiguous_count,
        )
        subject_columns[3].metric(
            "Unmapped",
            assessment.approved_subject_unmapped_count,
        )

        st.markdown("**Accepted semantic Relationships**")
        relationship_columns = st.columns(5)
        relationship_columns[0].metric(
            "Total",
            relationship_count,
        )
        relationship_columns[1].metric(
            "Mapped",
            assessment.semantic_relationship_mapped_count,
        )
        relationship_columns[2].metric(
            "Ambiguous",
            assessment.semantic_relationship_ambiguous_count,
        )
        relationship_columns[3].metric(
            "Unmapped",
            assessment.semantic_relationship_unmapped_count,
        )
        relationship_columns[4].metric(
            "Not projected",
            (
                assessment
                .semantic_relationship_intentionally_not_projected_count
            ),
        )
        if (
            assessment
            .semantic_relationship_intentionally_not_projected_count
        ):
            st.caption(
                "Not projected Relationships remain part of the approved "
                "engineering authority but currently reference at least one "
                "accepted Open Question that is intentionally not "
                "model-promotable."
            )
    else:
        # Compatibility fallback for older/legacy assessment providers.
        columns = st.columns(4)
        columns[0].metric("Mapped", assessment.mapped_count)
        columns[1].metric("Ambiguous", assessment.ambiguous_count)
        columns[2].metric("Unmapped", assessment.unmapped_count)
        columns[3].metric(
            "Not projected",
            assessment.intentionally_not_projected_count,
        )

    if technical:
        st.caption(assessment.rationale)

    modes = (ECO_DETERMINISTIC_MODE, LLM_ASSISTED_MODE)
    selected_mode = st.selectbox(
        "Derivation mode",
        options=modes,
        index=modes.index(assessment.recommended_mode),
        format_func=lambda value: _MODEL_DERIVATION_LABELS[value],
        key="guided_model.derivation_mode",
    )

    model, api_key = _render_modeling_llm_configuration(
        st,
        enabled=(selected_mode == LLM_ASSISTED_MODE),
        key_prefix="guided_model.initial",
        technical=technical,
    )

    if st.button(
        "Generate model placement proposals",
        key="guided_model.generate",
    ):
        if (
            selected_mode == LLM_ASSISTED_MODE
            and os.getenv("OPENAI_API_KEY") is None
            and api_key is None
        ):
            st.error(
                "LLM-assisted generation requires an OpenAI API key."
            )
            return

        placement_generator = getattr(
            write_service,
            "generate_model_placement_review",
            None,
        )
        if callable(placement_generator):
            try:
                spinner = getattr(st, "spinner", None)
                if callable(spinner):
                    with spinner(
                        "Running Model Placement — sorting approved "
                        "engineering information before assembly..."
                    ):
                        placement_generator(
                            project_id,
                            mode=selected_mode,
                            provider="openai",
                            model=model,
                            api_key=api_key,
                        )
                else:
                    placement_generator(
                        project_id,
                        mode=selected_mode,
                        provider="openai",
                        model=model,
                        api_key=api_key,
                    )
            except GuidedWorkflowWriteError:
                st.error(
                    "Model Placement generation failed safely. "
                    "No Model Candidate Set was created."
                )
                return

            st.success(
                "Model Placement proposals generated. "
                "Human placement decisions are required before assembly."
            )
            _rerun(st)
            return

        # Compatibility fallback for injected legacy/test write services.
        try:
            snapshot = write_service.generate_model_proposal(
                project_id,
                mode=selected_mode,
                provider="openai",
                model=model,
                api_key=api_key,
            )
        except GuidedWorkflowWriteError:
            st.error(
                "Model Proposal generation failed safely. "
                "No Candidate Set was treated as approved."
            )
            return

        st.session_state[SESSION_SELECTED_ENTITY_ID] = (
            snapshot.manifest.candidate_set_id
        )
        st.success("Model Proposal generated.")
        _rerun(st)


def _render_model_review_regeneration(
    st: Any,
    *,
    project_id: str,
    proposal,
    write_service,
    technical: bool,
) -> None:
    """Offer LLM escalation only after an actual Candidate rejection."""

    candidate_states = tuple(
        item.review_state.status
        for item in (
            tuple(proposal.proposed_elements)
            + tuple(proposal.proposed_relationships)
        )
    )
    if "rejected" not in candidate_states:
        return

    try:
        assessment = write_service.assess_model_derivation(
            project_id,
            predecessor_candidate_set_id=proposal.candidate_set_id,
        )
    except GuidedWorkflowWriteError:
        st.error(
            "Regeneration readiness could not be assessed safely."
        )
        return

    if not assessment.rejected_predecessor_candidate_ids:
        return

    st.subheader("Regenerate rejected model proposal")
    st.warning(
        "Human Model Review rejected Candidate content. "
        "You can regenerate a successor Candidate Set with the "
        "three modeling personas."
    )
    if technical:
        st.caption(
            "Rejected Candidates: "
            + ", ".join(
                assessment.rejected_predecessor_candidate_ids
            )
        )
        st.caption(
            "Escalated Approved Inputs: "
            + ", ".join(
                assessment.escalated_approved_input_ids
            )
        )

    reason = st.text_area(
        "Why should the model projection be reconsidered?",
        key="guided_model.regeneration_reason",
        placeholder=(
            "Describe what was wrong with the rejected model mapping."
        ),
    )
    model, api_key = _render_modeling_llm_configuration(
        st,
        enabled=True,
        key_prefix="guided_model.regeneration",
        technical=technical,
    )

    if st.button(
        "Regenerate with LLM",
        key="guided_model.regenerate_llm",
    ):
        reason_value = reason.strip()
        if not reason_value:
            st.error(
                "Provide a regeneration reason from the Human Model Review."
            )
            return
        if (
            os.getenv("OPENAI_API_KEY") is None
            and api_key is None
        ):
            st.error(
                "LLM-assisted regeneration requires an OpenAI API key."
            )
            return

        try:
            snapshot = write_service.generate_model_proposal(
                project_id,
                mode=LLM_ASSISTED_MODE,
                provider="openai",
                model=model,
                api_key=api_key,
                predecessor_candidate_set_id=(
                    proposal.candidate_set_id
                ),
                human_regeneration_reason=reason_value,
            )
        except GuidedWorkflowWriteError:
            st.error(
                "LLM-assisted regeneration failed safely. "
                "The predecessor Candidate Set remains unchanged."
            )
            return

        st.session_state[SESSION_SELECTED_ENTITY_ID] = (
            snapshot.manifest.candidate_set_id
        )
        st.success("Successor Model Proposal generated.")
        _rerun(st)


def _render_modeling_llm_configuration(
    st: Any,
    *,
    enabled: bool,
    key_prefix: str,
    technical: bool,
) -> tuple[str, str | None]:
    if not enabled:
        return _MODELING_MODEL_OPTIONS[0], None

    model = st.selectbox(
        "Model",
        options=_MODELING_MODEL_OPTIONS,
        index=0,
        format_func=lambda value: value,
        key=f"{key_prefix}.model",
    )

    if os.getenv("OPENAI_API_KEY"):
        if technical:
            st.caption(
                "OPENAI_API_KEY is available from the process environment."
            )
        return model, None

    entered = st.text_input(
        "OpenAI API key for this model-generation run",
        key=f"{key_prefix}.api_key",
        type="password",
    )
    return model, entered.strip() or None


def _render_model_readiness(st: Any, readiness) -> None:
    if readiness.semantic == "positive":
        st.success(readiness.status_label)
    elif readiness.semantic == "blocking":
        st.error(readiness.status_label)
    else:
        st.warning(readiness.status_label)


def _render_architecture_proposal(
    st: Any,
    presentation,
    *,
    technical: bool,
) -> None:
    nodes_by_area = {}
    for node in presentation.architecture_nodes:
        nodes_by_area.setdefault(node.model_area, []).append(node)

    if not nodes_by_area:
        st.info("No model elements are proposed.")
    else:
        for model_area in sorted(nodes_by_area):
            st.markdown(f"**{_humanize(model_area)}**")
            for node in nodes_by_area[model_area]:
                with st.container(border=True):
                    st.markdown(f"**{node.name}**")
                    st.caption(
                        f"{_humanize(node.element_type)} · "
                        f"{_humanize(node.support_level)} · "
                        f"Review: {_humanize(node.review_status)}"
                    )
                    if node.missing_information:
                        st.warning(
                            "Missing information: "
                            + "; ".join(node.missing_information)
                        )
                    if technical:
                        st.caption(
                            f"Candidate: {node.candidate_id} · "
                            f"Conformance: {node.conformance_status}"
                        )
                        if node.approved_input_ids:
                            st.caption(
                                "Approved Input: "
                                + ", ".join(node.approved_input_ids)
                            )
                        if node.rationale:
                            st.caption(f"Rationale: {node.rationale}")

    st.markdown("**Relationships**")
    if not presentation.architecture_edges:
        st.info("No model relationships are proposed.")
        return

    for edge in presentation.architecture_edges:
        with st.container(border=True):
            st.markdown(
                f"**{edge.source} → "
                f"{_humanize(edge.relationship)} → {edge.target}**"
            )
            st.caption(
                f"{_humanize(edge.relationship_family)} · "
                f"{_humanize(edge.priority_class)} · "
                f"{_humanize(edge.resolution_status)} · "
                f"Review: {_humanize(edge.review_status)}"
            )
            if edge.missing_information:
                st.warning(
                    "Missing information: "
                    + "; ".join(edge.missing_information)
                )
            if technical:
                st.caption(
                    f"Candidate: {edge.candidate_id} · "
                    f"Conformance: {edge.conformance_status} · "
                    f"Comparability: {edge.comparability_impact}"
                )
                if edge.approved_input_ids:
                    st.caption(
                        "Approved Input: "
                        + ", ".join(edge.approved_input_ids)
                    )
                if edge.rationale:
                    st.caption(f"Rationale: {edge.rationale}")


def _render_relationship_choice(
    st: Any,
    choice,
    architecture_edges,
    *,
    technical: bool,
) -> None:
    edge_by_id = {
        edge.candidate_id: edge
        for edge in architecture_edges
    }

    with st.container(border=True):
        if choice.review_required:
            st.warning(choice.label)
        elif choice.semantic == "positive":
            st.success(choice.label)
        else:
            st.info(choice.label)

        for candidate_id in choice.candidate_ids:
            edge = edge_by_id[candidate_id]
            markers = []
            if candidate_id in choice.preferred_candidate_ids:
                markers.append("Preferred")
            if candidate_id in choice.accepted_candidate_ids:
                markers.append("Accepted")
            status = (
                " · ".join(markers)
                if markers
                else "Alternative"
            )
            st.markdown(
                f"**{status}: {edge.source} → "
                f"{_humanize(edge.relationship)} → {edge.target}**"
            )
            st.caption(
                f"Review: {_humanize(edge.review_status)} · "
                f"Comparability: {_humanize(edge.comparability_impact)}"
            )
            if technical:
                st.caption(f"Candidate: {candidate_id}")


def _render_model_proposal_traceability(
    st: Any,
    presentation,
) -> None:
    st.markdown("**Candidate traceability**")

    rows = []
    for node in presentation.architecture_nodes:
        rows.append(
            {
                "Candidate": node.candidate_id,
                "Kind": "Element",
                "Engineering content": node.name,
                "Review": node.review_status,
                "Approved Input": ", ".join(node.approved_input_ids),
            }
        )

    for edge in presentation.architecture_edges:
        rows.append(
            {
                "Candidate": edge.candidate_id,
                "Kind": "Relationship",
                "Engineering content": (
                    f"{edge.source} → {edge.relationship} → {edge.target}"
                ),
                "Review": edge.review_status,
                "Approved Input": ", ".join(edge.approved_input_ids),
            }
        )

    if rows:
        st.table(rows)

    if presentation.comparability.comparison_anchor_ids:
        st.caption(
            "Comparison anchors: "
            + ", ".join(
                presentation.comparability.comparison_anchor_ids
            )
        )

    if presentation.comparability.deviation_ids:
        st.caption(
            "Comparability deviations: "
            + ", ".join(
                presentation.comparability.deviation_ids
            )
        )


def render_final_model_review_ui(
    project_root: Path,
    *,
    streamlit_module: Any,
    detail_service: GuidedWorkflowDetailReadService | None = None,
    write_service: GuidedWorkflowWriteService | None = None,
) -> None:
    """Render one exact Final Model Review revision without release writes."""

    st = streamlit_module
    root = Path(project_root)
    navigation = read_navigation_state(st.session_state)
    technical = technical_details_enabled(st.session_state)
    service = (
        GuidedWorkflowDetailReadService(root)
        if detail_service is None
        else detail_service
    )
    writes = (
        GuidedWorkflowWriteService(root)
        if write_service is None
        else write_service
    )

    st.header("Final Model Review")
    st.caption(
        "Inspect the generated SysML v2 model, validation evidence and "
        "remaining Human review work before controlled publication."
    )

    if navigation.project_id is None:
        st.info("Select a Project in the application header.")
        return

    selected_id = _selected_entity(
        navigation.selected_entity_id,
        "FRV-",
    )

    try:
        detail = service.load_final_model_review(
            navigation.project_id,
            selected_id,
        )
    except GuidedWorkflowValidationError:
        st.error(
            "Final Model Review cannot be reconstructed safely from "
            "the current authoritative Project state."
        )
        return
    except Exception:
        st.error("Final Model Review is currently unavailable.")
        return

    if detail.status == "not_available":
        candidate_loader = getattr(
            writes,
            "list_phase_l_review_subject_candidates",
            None,
        )
        if not callable(candidate_loader):
            st.info(
                "No Final Model Review revision is available yet. "
                "Generation and validation must produce a review subject first."
            )
            return

        try:
            candidates = candidate_loader(navigation.project_id)
        except Exception:
            st.error(
                "Generated SysML candidates for Final Model Review "
                "cannot be reconstructed safely."
            )
            return

        if not candidates:
            st.info(
                "No Final Model Review revision is available yet. "
                "Generate SysML v2 before starting Final Model Review."
            )
            return

        st.warning(
            "Generated SysML v2 is available, but no Final Model Review "
            "exists yet."
        )
        st.caption(
            "Select the exact generated Internal Model to start Final Model "
            "Review. The exact generated SysML v2 is validated with the "
            "configured external validator and the result is bound immutably "
            "to the review revision. Publication approval remains a separate "
            "Human decision."
        )

        by_id = {
            item["internal_engineering_model_id"]: item
            for item in candidates
        }
        selected_iem = st.selectbox(
            "Generated Internal Model",
            options=tuple(by_id),
            key="guided_detail.final_review.create_subject.iem",
        )
        candidate = by_id[selected_iem]

        st.caption(
            f"Generated artifact: {candidate['artifact_fingerprint']} · "
            f"{candidate['unit_count']} unit(s)"
        )

        preview_key = (
            "guided_final_model.current_validation_preview."
            f"{candidate['artifact_fingerprint']}"
        )
        cached_validation = st.session_state.get(preview_key)
        if cached_validation is not None:
            st.caption(
                "A current validation result for this exact artifact is "
                "available in the app session and will be used."
            )

        label = "Start Final Model Review"
        if st.button(
            label,
            key="guided_detail.final_review.create_subject",
        ):
            creator = getattr(
                writes,
                "create_phase_l_final_model_review",
                None,
            )
            if not callable(creator):
                st.error(
                    "Final Model Review creation is unavailable."
                )
                return
            try:
                bundle = creator(
                    navigation.project_id,
                    selected_iem,
                    validation_result=cached_validation,
                )
            except Exception:
                st.error(
                    "Final Model Review subject creation failed safely. "
                    "No release or publication authority was created."
                )
                return

            st.success(
                "Final Model Review created: "
                f"{bundle.revision.final_model_review_id} · "
                f"{bundle.revision.final_model_review_revision_id}"
            )
            rerun = getattr(st, "rerun", None)
            if callable(rerun):
                rerun()
        return

    if detail.status == "selection_required":
        _render_explicit_selection(
            st,
            detail.options,
            label="Final Model Review",
            key="guided_detail.final_review",
            technical=technical,
        )
        return

    view = detail.review
    gate = detail.release_gate

    if view is None or gate is None:
        st.error("The selected Final Model Review could not be resolved.")
        return

    st.subheader("Review overview")
    st.write(view.summary)

    blocking_findings = sum(
        1
        for finding in view.validation_findings
        if finding.blocking
    )

    columns = st.columns(4)
    columns[0].metric(
        "Generated units",
        len(view.code_units),
    )
    columns[1].metric(
        "Validation findings",
        len(view.validation_findings),
    )
    columns[2].metric(
        "Blocking findings",
        blocking_findings,
    )
    columns[3].metric(
        "Human actions",
        len(view.required_human_actions),
    )

    _render_release_state(st, gate.release_status)

    external_evidence = getattr(
        view,
        "external_validator_evidence",
        (),
    )
    if external_evidence:
        st.subheader("External SysML v2 validation")
        for evidence in external_evidence:
            passed = (
                evidence.execution_status == "completed"
                and evidence.exit_code == 0
                and evidence.normalized_diagnostic_count == 0
            )
            if passed:
                st.success("SYSIDE validation: PASSED")
            elif evidence.execution_status == "completed":
                st.error("SYSIDE validation: FAILED")
            else:
                st.warning("SYSIDE validation: INCOMPLETE")

            columns = st.columns(3)
            columns[0].metric(
                "SYSIDE",
                "PASS" if passed else "NOT PASS",
            )
            columns[1].metric(
                "Diagnostics",
                evidence.normalized_diagnostic_count,
            )
            columns[2].metric(
                "Exit code",
                "—" if evidence.exit_code is None else evidence.exit_code,
            )
            validator_label = f"Validator: {evidence.tool_name}"
            if evidence.tool_version:
                validator_label += f" · {evidence.tool_version}"
            else:
                validator_label += " · version unavailable"
            st.caption(validator_label)
        st.caption(
            "Quality dimension: external SysML v2 conformance / tool "
            "compatibility. Engineering content approval remains a separate "
            "Human review decision."
        )

    if view.required_human_actions:
        st.subheader("Your review work")
        for action in view.required_human_actions:
            st.warning(action)

    st.subheader("Generated SysML v2")

    if not view.code_units:
        st.info("No generated SysML v2 unit is available.")
    else:
        for unit in view.code_units:
            with st.expander(unit.relative_path):
                st.code(unit.content, language="text")

                if technical:
                    st.caption(
                        f"Generated unit: {unit.generated_unit_id}"
                    )
                    st.caption(
                        f"Fingerprint: {unit.content_fingerprint}"
                    )

    st.subheader("Model structure")

    if view.diagram.nodes:
        st.markdown("**Elements**")
        st.table(
            [
                {
                    "Name": node.label,
                    "Model area": _humanize(node.model_area),
                    "Type": _humanize(node.element_type),
                    "Framework": (
                        node.framework_assignment
                        or "Not assigned"
                    ),
                }
                for node in view.diagram.nodes
            ]
        )

    if view.diagram.edges:
        st.markdown("**Relationships**")
        node_names = {
            node.internal_model_element_id: node.label
            for node in view.diagram.nodes
        }
        st.table(
            [
                {
                    "Source": node_names.get(
                        edge.source_internal_model_element_id,
                        edge.source_internal_model_element_id,
                    ),
                    "Relationship": _humanize(
                        edge.semantic_intent
                    ),
                    "Target": node_names.get(
                        edge.target_internal_model_element_id,
                        edge.target_internal_model_element_id,
                    ),
                    "Family": _humanize(
                        edge.relationship_family
                    ),
                }
                for edge in view.diagram.edges
            ]
        )

    st.subheader("Validation")

    if not view.validation_findings:
        st.success("No validation findings are present.")
    else:
        st.table(
            [
                {
                    "Severity": _humanize(finding.severity),
                    "Finding": finding.message,
                    "Blocking": (
                        "Yes" if finding.blocking else "No"
                    ),
                }
                for finding in view.validation_findings
            ]
        )

    if view.agent_proposals:
        st.subheader("Agent proposal evidence")
        st.table(
            [
                {
                    "Persona": (
                        proposal.personality
                        or proposal.agent_identity
                        or "Agent"
                    ),
                    "Proposal": (
                        proposal.proposal_summary
                        or "No summary"
                    ),
                    "Confidence": (
                        proposal.confidence
                        or "Not stated"
                    ),
                    "Resolution": _humanize(
                        proposal.resolution_status
                    ),
                }
                for proposal in view.agent_proposals
            ]
        )

    render_final_review_actions(
        st,
        project_id=navigation.project_id,
        detail=detail,
        write_service=writes,
        technical=technical,
    )

    st.subheader("Next engineering step")
    st.info(view.next_action)

    if technical:
        with st.expander("Technical details"):
            st.caption(
                f"Final Model Review: {view.final_model_review_id}"
            )
            st.caption(
                "Revision: "
                f"{view.final_model_review_revision_id}"
            )
            st.caption(
                "Source Internal Engineering Model: "
                f"{view.source_internal_engineering_model_id}"
            )
            st.caption(
                "Generated artifact fingerprint: "
                f"{view.generated_artifact_set_fingerprint}"
            )
            st.caption(
                "Validation fingerprint: "
                f"{view.validation_result_fingerprint}"
            )
            st.caption(
                f"Validation status: {view.validation_status}"
            )
            st.caption(
                f"Publication gate: {view.publication_gate}"
            )
            st.caption(
                f"Release status: {gate.release_status}"
            )

            if gate.blockers:
                st.markdown("**Release blockers**")
                for blocker in gate.blockers:
                    st.caption(
                        f"{blocker.code}: {blocker.message}"
                    )

            if view.traceability:
                st.markdown("**Generated traceability**")
                st.table(
                    [
                        {
                            "Generated unit": item.generated_unit_id,
                            "Symbol": item.generated_symbol_id,
                            "Model candidate": (
                                item.source_model_candidate_id
                            ),
                            "Review decision": (
                                item.review_decision_id
                            ),
                        }
                        for item in view.traceability
                    ]
                )


def render_published_output_ui(
    project_root: Path,
    *,
    streamlit_module: Any,
    detail_service: GuidedWorkflowDetailReadService | None = None,
) -> None:
    """Render immutable published output without publication writes."""

    st = streamlit_module
    root = Path(project_root)
    navigation = read_navigation_state(st.session_state)
    technical = technical_details_enabled(st.session_state)
    service = (
        GuidedWorkflowDetailReadService(root)
        if detail_service is None
        else detail_service
    )

    st.header("Published Output")
    st.caption(
        "Inspect the immutable, Human-approved and validation-bound "
        "SysML v2 publication package."
    )

    if navigation.project_id is None:
        st.info("Select a Project in the application header.")
        return

    selected_id = _selected_entity(
        navigation.selected_entity_id,
        "OUT-",
    )

    try:
        detail = service.load_published_output(
            navigation.project_id,
            selected_id,
        )
    except GuidedWorkflowValidationError:
        st.error(
            "Published Output cannot be reconstructed safely from "
            "the current authoritative Project state."
        )
        return
    except Exception:
        st.error("Published Output is currently unavailable.")
        return

    if detail.status == "not_available":
        st.info(
            "No Published Output exists yet. "
            "A Final Model Review must be approved before publication."
        )
        return

    if detail.status == "selection_required":
        _render_explicit_selection(
            st,
            detail.options,
            label="Published Output",
            key="guided_detail.output",
            technical=technical,
        )
        return

    package = detail.package
    if package is None:
        st.error("The selected Published Output could not be resolved.")
        return

    manifest = package.manifest
    sysml_files = tuple(
        item
        for item in manifest.files
        if item.role == "sysml_unit"
    )

    st.subheader("Published model")
    st.success(
        "This package is an immutable published engineering output."
    )
    st.caption(f"Published {manifest.published_at}")

    columns = st.columns(3)
    columns[0].metric(
        "SysML units",
        len(sysml_files),
    )
    columns[1].metric(
        "Package files",
        len(manifest.files),
    )
    columns[2].metric(
        "Publication state",
        "Published",
    )

    st.subheader("Package contents")
    st.table(
        [
            {
                "File": item.relative_path,
                "Role": _humanize(item.role),
            }
            for item in manifest.files
        ]
    )

    if sysml_files:
        st.subheader("Published SysML v2")

        for file_reference in sysml_files:
            with st.expander(file_reference.relative_path):
                try:
                    raw = service.read_published_output_file(
                        navigation.project_id,
                        manifest.output_package_id,
                        file_reference.relative_path,
                    )
                except GuidedWorkflowValidationError:
                    st.error(
                        "This published file could not be read safely."
                    )
                    continue

                try:
                    content = raw.decode("utf-8")
                except UnicodeDecodeError:
                    st.info(
                        "This published file is not UTF-8 text."
                    )
                else:
                    st.code(content, language="text")

    if technical:
        with st.expander("Technical details"):
            st.caption(
                f"Output package: {manifest.output_package_id}"
            )
            st.caption(
                "Source Internal Engineering Model: "
                f"{manifest.source_internal_engineering_model_id}"
            )
            st.caption(
                "Source artifact fingerprint: "
                f"{manifest.source_artifact_set_fingerprint}"
            )
            st.caption(
                "Validation fingerprint: "
                f"{manifest.validation_result_fingerprint}"
            )
            st.caption(
                f"Final Model Review: {manifest.final_model_review_id}"
            )
            st.caption(
                "Final review revision: "
                f"{manifest.final_model_review_revision_id}"
            )
            st.caption(
                "Final review decision: "
                f"{manifest.final_review_decision_id}"
            )
            st.caption(
                "Publication profile: "
                f"{manifest.output_profile_reference.profile_id} "
                f"v{manifest.output_profile_reference.profile_version}"
            )

            st.markdown("**File fingerprints**")
            for item in manifest.files:
                st.caption(
                    f"{item.relative_path} · "
                    f"{item.content_fingerprint}"
                )


def _render_explicit_selection(
    st: Any,
    options,
    *,
    label: str,
    key: str,
    technical: bool,
) -> None:
    """Require an explicit display choice where no unique head exists."""

    option_by_id = {
        item.entity_id: item
        for item in options
    }
    ids = tuple(option_by_id)

    st.warning(
        f"Multiple current {label} alternatives are available. "
        "Select the one you want to inspect."
    )

    selected = st.selectbox(
        label,
        options=(None, *ids),
        index=0,
        format_func=lambda entity_id: (
            f"Select {label}…"
            if entity_id is None
            else (
                f"{option_by_id[entity_id].label} · {entity_id}"
                if technical
                else option_by_id[entity_id].label
            )
        ),
        key=key,
    )

    if selected is None:
        return

    st.session_state[SESSION_SELECTED_ENTITY_ID] = selected
    _rerun(st)


def _render_release_state(st: Any, status: str) -> None:
    if status == "approved_for_publication":
        st.success("Human release approval is recorded.")
    elif status == "ready_for_approval":
        st.warning(
            "The exact validated revision is ready for Human "
            "publication approval."
        )
    else:
        st.error(
            "Publication is currently blocked. Review the remaining "
            "actions and findings below."
        )


def _selected_entity(
    value: str | None,
    prefix: str,
) -> str | None:
    if value is None or not value.startswith(prefix):
        return None
    return value


def _humanize(value: str) -> str:
    return value.replace("_", " ").strip().capitalize()


def _rerun(st: Any) -> None:
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()
