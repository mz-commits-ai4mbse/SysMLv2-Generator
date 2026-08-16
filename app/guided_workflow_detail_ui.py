"""Engineer-facing detail workspaces for Guided Workflow stages."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.guided_workflow_actions import (
    render_final_review_actions,
    render_model_proposal_actions,
)
from app.presentation_preferences import technical_details_enabled
from app.turing_generator_navigation import (
    SESSION_SELECTED_ENTITY_ID,
    read_navigation_state,
)
from modules.guided_workflow import (
    GuidedWorkflowDetailReadService,
    GuidedWorkflowValidationError,
    GuidedWorkflowWriteService,
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
        "Review the proposed engineering model structure before "
        "authoritative engineering-model assembly."
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
        st.info(
            "No Model Proposal is available yet. "
            "Creating one requires an explicit engineering action."
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

    st.subheader("Proposal overview")
    st.write(proposal.summary)

    columns = st.columns(4)
    columns[0].metric(
        "Elements",
        len(proposal.proposed_elements),
    )
    columns[1].metric(
        "Relationships",
        len(proposal.proposed_relationships),
    )
    columns[2].metric(
        "Human decisions",
        len(proposal.required_human_decisions),
    )
    columns[3].metric(
        "Blocking issues",
        len(proposal.blocking_issues),
    )

    if proposal.blocking_issues:
        st.error(
            f"{len(proposal.blocking_issues)} blocking issue"
            + ("" if len(proposal.blocking_issues) == 1 else "s")
            + " prevent progression."
        )

    if proposal.required_human_decisions:
        st.warning(
            f"{len(proposal.required_human_decisions)} Human decision"
            + (
                ""
                if len(proposal.required_human_decisions) == 1
                else "s"
            )
            + " required."
        )
        for decision in proposal.required_human_decisions:
            with st.container(border=True):
                st.markdown(
                    f"**{_humanize(decision.target_type)}**"
                )
                st.write(decision.reason)
                st.caption(decision.recommended_action)

                if technical:
                    st.caption(
                        "Targets: "
                        + ", ".join(decision.target_ids)
                    )

    st.subheader("Proposed model elements")

    if proposal.proposed_elements:
        st.table(
            [
                {
                    "Name": item.proposed_name,
                    "Model area": _humanize(item.model_area),
                    "Type": _humanize(item.element_type),
                    "Support": _humanize(item.support_level),
                    "Review": _humanize(
                        item.review_state.status
                    ),
                }
                for item in proposal.proposed_elements
            ]
        )
    else:
        st.info("No model elements are proposed.")

    st.subheader("Proposed relationships")

    if proposal.proposed_relationships:
        st.table(
            [
                {
                    "Source": item.source_subject_key,
                    "Relationship": _humanize(
                        item.semantic_intent
                    ),
                    "Target": item.target_subject_key,
                    "Priority": _humanize(
                        item.priority_class
                    ),
                    "Review": _humanize(
                        item.review_state.status
                    ),
                }
                for item in proposal.proposed_relationships
            ]
        )
    else:
        st.info("No model relationships are proposed.")

    render_model_proposal_actions(
        st,
        project_id=navigation.project_id,
        proposal=proposal,
        write_service=writes,
        technical=technical,
    )

    st.subheader("Structural comparability")
    comparison = proposal.comparability_summary
    columns = st.columns(4)
    columns[0].metric("Improves", comparison.improves_count)
    columns[1].metric("Neutral", comparison.neutral_count)
    columns[2].metric("Reduces", comparison.reduces_count)
    columns[3].metric("Unknown", comparison.unknown_count)

    if proposal.profile_deviations:
        st.warning(
            f"{len(proposal.profile_deviations)} structural/profile "
            "deviation"
            + (
                ""
                if len(proposal.profile_deviations) == 1
                else "s"
            )
            + " require attention."
        )

    st.subheader("Next engineering step")
    st.info(proposal.next_action)

    if technical:
        with st.expander("Technical details"):
            st.caption(
                f"Candidate Set: {proposal.candidate_set_id}"
            )
            st.caption(
                "Candidate Set fingerprint: "
                f"{proposal.candidate_set_content_fingerprint}"
            )
            st.caption(
                f"Assembly gate: {proposal.phase_i_gate_status}"
            )
            st.write(proposal.generation_rationale_summary)

            if proposal.blocking_issues:
                st.markdown("**Blocking diagnostics**")
                for issue in proposal.blocking_issues:
                    st.caption(
                        f"{issue.code}: {issue.message}"
                    )

            if proposal.profile_deviations:
                st.markdown("**Profile deviations**")
                for deviation in proposal.profile_deviations:
                    st.caption(
                        f"{deviation.candidate_id} · "
                        f"{deviation.conformance_status} · "
                        f"{deviation.rationale}"
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
        st.info(
            "No Final Model Review revision is available yet. "
            "Generation and validation must produce a review subject first."
        )
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
