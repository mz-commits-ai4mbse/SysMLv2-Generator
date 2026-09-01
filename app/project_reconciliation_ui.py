"""Streamlit Human Project Authority workspace for BLK-002 Multi-Source."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.presentation_preferences import technical_details_enabled
from app.turing_generator_navigation import read_navigation_state
from modules.project_reconciliation.orchestration_service import (
    ProjectReconciliationOrchestrationError,
    ProjectReconciliationOrchestrationService,
    ProjectReconciliationProgressEvent,
)
from modules.project_reconciliation.workflow_service import (
    ProjectAuthorityWorkflowService,
    ProjectReconciliationWorkflowError,
)
from modules.project_workspace import ProjectWorkspace, ProjectWorkspaceError


_SESSION_REVIEWER = "project_reconciliation.reviewer_identity"

_OUTCOME_LABELS = {
    "remain_independent": "Remain independent",
    "coexist": "Coexist as valid authority",
    "supersede": "Supersede at project level",
    "unresolved": "Remain unresolved",
}


class _ProjectReconciliationProgressDisplay:
    # Live non-authoritative progress display for S2/S3 orchestration.

    def __init__(self, st: Any) -> None:
        self._st = st
        self._status = None
        self._fallback = None

        status_factory = getattr(st, "status", None)
        if callable(status_factory):
            self._status = status_factory(
                "Project Reconciliation · preparing",
                expanded=True,
            )
        else:
            empty_factory = getattr(st, "empty", None)
            if callable(empty_factory):
                self._fallback = empty_factory()

    def observe(
        self,
        event: ProjectReconciliationProgressEvent,
    ) -> None:
        label = f"Project Reconciliation · {event.message}"

        if self._status is not None:
            self._status.update(
                label=label,
                state="running",
                expanded=True,
            )
            writer = getattr(self._status, "write", None)
            if callable(writer):
                writer(event.message)
            return

        if self._fallback is not None:
            info = getattr(self._fallback, "info", None)
            if callable(info):
                info(label)

    def finish(self, *, success: bool, message: str) -> None:
        state = "complete" if success else "error"
        label = f"Project Reconciliation · {message}"

        if self._status is not None:
            self._status.update(
                label=label,
                state=state,
                expanded=True,
            )
            return

        if self._fallback is None:
            return

        renderer = getattr(
            self._fallback,
            "success" if success else "error",
            None,
        )
        if callable(renderer):
            renderer(label)



class _ProjectFitProgressDisplay:
    """Non-authoritative live display for S2-only Project Fit assessment."""

    def __init__(self, st: Any) -> None:
        self._status = None
        self._fallback = None
        status_factory = getattr(st, "status", None)
        if callable(status_factory):
            self._status = status_factory(
                "Project Fit · preparing",
                expanded=True,
            )
        else:
            empty_factory = getattr(st, "empty", None)
            if callable(empty_factory):
                self._fallback = empty_factory()

    def observe(
        self,
        event: ProjectReconciliationProgressEvent,
    ) -> None:
        label = f"Project Fit · {event.message}"
        if self._status is not None:
            self._status.update(
                label=label,
                state="running",
                expanded=True,
            )
            writer = getattr(self._status, "write", None)
            if callable(writer):
                writer(event.message)
            return
        if self._fallback is not None:
            info = getattr(self._fallback, "info", None)
            if callable(info):
                info(label)

    def finish(self, *, success: bool, message: str) -> None:
        label = f"Project Fit · {message}"
        if self._status is not None:
            self._status.update(
                label=label,
                state="complete" if success else "error",
                expanded=True,
            )
            return
        if self._fallback is not None:
            renderer = getattr(
                self._fallback,
                "success" if success else "error",
                None,
            )
            if callable(renderer):
                renderer(label)


def render_project_reconciliation_ui(
    project_root: Path,
    *,
    streamlit_module: Any,
    project_workspace: ProjectWorkspace | None = None,
    workflow_service: ProjectAuthorityWorkflowService | None = None,
    orchestration_service: (
        ProjectReconciliationOrchestrationService | None
    ) = None,
) -> None:
    """Render the active BLK-002 thesis-MVP Project Fit gate."""

    st = streamlit_module
    root = Path(project_root)
    navigation = read_navigation_state(st.session_state)
    technical = technical_details_enabled(st.session_state)

    st.header("Project Fit · Multi-Source Readiness")
    st.caption(
        "Verify that the current reviewed Engineering Sources belong to this "
        "Project before they enter one multi-source Model Proposal. "
        "Cross-source semantic reconciliation and change control are outside "
        "the thesis MVP."
    )

    if navigation.project_id is None:
        st.error("Select a Project before opening Project Fit.")
        return

    workspace = (
        ProjectWorkspace(root=root / "data" / "projects")
        if project_workspace is None
        else project_workspace
    )
    orchestrator = (
        ProjectReconciliationOrchestrationService(project_root=root)
        if orchestration_service is None
        else orchestration_service
    )

    try:
        manifest = workspace.load_project(navigation.project_id)
    except ProjectWorkspaceError:
        st.error("The selected Project Workspace is unavailable or invalid.")
        return
    except Exception:
        st.error("The selected Project Workspace could not be validated.")
        return

    if technical:
        st.caption(
            f"Project: {manifest.display_name} · {manifest.project_id}"
        )
    else:
        st.caption(f"Project: {manifest.display_name}")

    try:
        readiness = orchestrator.read_project_fit_readiness(
            manifest.project_id
        )
    except ProjectReconciliationOrchestrationError as exc:
        st.error(str(exc))
        return
    except Exception:
        st.error(
            "Project Fit readiness is unavailable. "
            "No downstream readiness was inferred."
        )
        return

    if readiness.source_count == 0:
        st.info(
            "No current reviewed Engineering Source is available for "
            "Project Fit."
        )
        return

    if readiness.source_count == 1:
        st.success(
            "Single-source project: a project-level multi-source fit gate "
            "is not required."
        )
        return

    st.subheader("Current source admissibility")
    for source in readiness.sources:
        outcome = source.outcome or "not assessed"
        st.write(
            f"**{source.source_id}** · {source.gate_state} · {outcome}"
        )
        if technical:
            details = (
                f"{source.processing_run_id} · "
                f"{source.attempt_id or 'no attempt'}"
            )
            if source.assessment_fingerprint is not None:
                details += (
                    " · fit "
                    + source.assessment_fingerprint[:12]
                    + "…"
                )
            st.caption(details)

    if readiness.all_admitted:
        st.success(
            f"Project Fit complete: all {readiness.source_count} current "
            "Engineering Sources are admitted to the Project."
        )
        st.info(
            "The active thesis-MVP gate is complete. Existing semantic "
            "reconciliation evidence remains immutable historical/prototype "
            "evidence but is not required for Model Proposal."
        )
        return

    if readiness.source_review_required_source_ids:
        st.warning(
            "Source-local Human Review must finish before Project Fit can "
            "complete: "
            + ", ".join(
                readiness.source_review_required_source_ids
            )
        )
        return

    if readiness.human_resolution_source_ids:
        st.warning(
            "Project Fit requires explicit Human resolution for: "
            + ", ".join(readiness.human_resolution_source_ids)
            + ". No machine-only override is applied."
        )

    if not readiness.assessment_required_source_ids:
        st.error(
            "Project Fit is not complete. Resolve the non-admitted source "
            "treatment before Model Proposal."
        )
        return

    st.info(
        "Missing exact Project Fit evidence for: "
        + ", ".join(readiness.assessment_required_source_ids)
    )

    model_options = (
        "gpt-5.4-mini",
        "gpt-5-mini",
        "gpt-4.1-mini",
        "gpt-4o-mini",
    )
    model = st.selectbox(
        "Project Fit model",
        options=model_options,
        index=0,
        key="project_reconciliation.model",
    )
    st.warning(
        "This action performs live LLM requests only for missing exact "
        "Project Fit assessments. It does not run S3 semantic reconciliation."
    )
    confirmed = st.checkbox(
        "I confirm this live Project Fit assessment.",
        value=False,
        key="project_reconciliation.live_confirmation",
    )

    api_key = None
    if os.getenv("OPENAI_API_KEY"):
        if technical:
            st.caption(
                "OPENAI_API_KEY is available from the process environment."
            )
    else:
        entered_key = st.text_input(
            "OpenAI API key for Project Fit",
            value="",
            type="password",
            key="project_reconciliation.api_key",
            help=(
                "Used only for this execution and never persisted in "
                "Project Fit evidence."
            ),
        )
        api_key = entered_key.strip() or None

    if st.button(
        "Assess project fit",
        key="project_reconciliation.start",
        type="primary",
    ):
        if not confirmed:
            st.error(
                "Live Project Fit assessment requires explicit confirmation."
            )
            return
        if os.getenv("OPENAI_API_KEY") is None and api_key is None:
            st.error(
                "Live OpenAI Project Fit assessment requires an API key."
            )
            return

        progress = _ProjectFitProgressDisplay(st)
        try:
            result = orchestrator.assess_project_fit_only(
                manifest.project_id,
                provider="openai",
                model=model,
                api_key=api_key,
                progress_observer=progress.observe,
            )
        except ProjectReconciliationOrchestrationError as exc:
            progress.finish(success=False, message="failed safely")
            st.error(str(exc))
            return
        except Exception:
            progress.finish(success=False, message="failed unexpectedly")
            st.error(
                "Project Fit assessment failed unexpectedly. "
                "No downstream state was inferred."
            )
            return

        progress.finish(success=True, message="assessment complete")
        if result.all_admitted:
            st.success(
                "Project Fit admits all current Engineering Sources."
            )
        else:
            st.warning(
                "Project Fit evidence is complete, but at least one Source "
                "still requires explicit Human resolution."
            )
        _rerun(st)


def _render_legacy_project_reconciliation_ui(
    project_root: Path,
    *,
    streamlit_module: Any,
    project_workspace: ProjectWorkspace | None = None,
    workflow_service: ProjectAuthorityWorkflowService | None = None,
    orchestration_service: (
        ProjectReconciliationOrchestrationService | None
    ) = None,
) -> None:
    """Render explicit Human Project Engineering Authority decisions."""

    st = streamlit_module
    root = Path(project_root)
    navigation = read_navigation_state(st.session_state)
    technical = technical_details_enabled(st.session_state)

    workspace = (
        ProjectWorkspace(root=root / "data" / "projects")
        if project_workspace is None
        else project_workspace
    )
    service = (
        ProjectAuthorityWorkflowService(project_root=root)
        if workflow_service is None
        else workflow_service
    )
    orchestrator = (
        ProjectReconciliationOrchestrationService(
            project_root=root
        )
        if orchestration_service is None
        else orchestration_service
    )

    st.header("Project Reconciliation")
    st.caption(
        "Compare source-local reviewed engineering authority, preserve "
        "cross-source differences, and make explicit project-level "
        "Human Authority decisions before model derivation."
    )

    if navigation.project_id is None:
        st.error("Select a Project before opening Project Reconciliation.")
        return

    try:
        manifest = workspace.load_project(navigation.project_id)
    except ProjectWorkspaceError:
        st.error("The selected Project Workspace is unavailable or invalid.")
        return
    except Exception:
        st.error("The selected Project Workspace could not be validated.")
        return

    if technical:
        st.caption(
            f"Project: {manifest.display_name} · {manifest.project_id}"
        )
    else:
        st.caption(f"Project: {manifest.display_name}")

    try:
        view = service.load_review(manifest.project_id)
    except ProjectReconciliationWorkflowError as exc:
        st.error(str(exc))
        return
    except Exception:
        st.error(
            "Project Reconciliation state is unavailable. "
            "No fallback authority state was inferred."
        )
        return

    if view.cycle_id is None:
        st.info(
            "No persisted cross-source semantic reconciliation cycle exists "
            "yet. Start Project Reconciliation to assess Project Fit (S2) "
            "and compare admitted source-local Subjects across Sources (S3)."
        )

        model_options = (
            "gpt-5.4-mini",
            "gpt-5-mini",
            "gpt-4.1-mini",
            "gpt-4o-mini",
        )
        model = st.selectbox(
            "Reconciliation model",
            options=model_options,
            index=0,
            key="project_reconciliation.model",
        )
        st.warning(
            "Starting Project Reconciliation performs live LLM requests "
            "for Project Fit and cross-source semantic comparison."
        )
        confirmed = st.checkbox(
            "I confirm this live LLM reconciliation.",
            value=False,
            key="project_reconciliation.live_confirmation",
        )

        api_key = None
        if os.getenv("OPENAI_API_KEY"):
            if technical:
                st.caption(
                    "OPENAI_API_KEY is available from the process environment."
                )
        else:
            entered_key = st.text_input(
                "OpenAI API key for this reconciliation",
                value="",
                type="password",
                key="project_reconciliation.api_key",
                help=(
                    "Used only for this execution and never persisted in "
                    "Project Reconciliation evidence."
                ),
            )
            api_key = entered_key.strip() or None

        if st.button(
            "Start project reconciliation",
            key="project_reconciliation.start",
            type="primary",
        ):
            if not confirmed:
                st.error(
                    "Live reconciliation requires explicit confirmation."
                )
            elif (
                os.getenv("OPENAI_API_KEY") is None
                and api_key is None
            ):
                st.error(
                    "Live OpenAI reconciliation requires an API key."
                )
            else:
                progress = _ProjectReconciliationProgressDisplay(st)
                try:
                    result = orchestrator.start(
                        manifest.project_id,
                        provider="openai",
                        model=model,
                        api_key=api_key,
                        progress_observer=progress.observe,
                    )
                except ProjectReconciliationOrchestrationError as exc:
                    progress.finish(
                        success=False,
                        message="failed safely",
                    )
                    st.error(str(exc))
                except Exception:
                    progress.finish(
                        success=False,
                        message="failed unexpectedly",
                    )
                    st.error(
                        "Project Reconciliation failed unexpectedly. "
                        "No cycle was inferred."
                    )
                else:
                    progress.finish(
                        success=True,
                        message=(
                            f"{result.reconciliation_cycle_id} ready"
                        ),
                    )
                    if result.reused_existing_cycle:
                        st.success(
                            "Existing exact Project Reconciliation cycle "
                            "reopened."
                        )
                    else:
                        st.success(
                            "Project Fit and cross-source semantic "
                            "reconciliation completed."
                        )
                    _rerun(st)
        return

    if view.reconciliation_mode == "concern_centric_cases":
        if technical:
            st.caption(
                f"Cycle {view.cycle_id} · "
                f"{len(view.source_ids)} sources · "
                f"{view.case_count} Reconciliation Cases"
            )

        st.info(
            f"Concern-centric semantic reconciliation produced "
            f"{view.case_count} Reconciliation Cases "
            f"({view.unique_case_count} unique)."
        )

        if view.regrouping_required:
            st.error(
                "S3B identified at least one Case that was grouped too "
                "broadly. Semantic regrouping is required before Human "
                "Project Authority."
            )
        else:
            if view.potential_conflicts_present:
                st.warning(
                    "Potential semantic conflicts were detected. "
                    "These are semantic evidence for Human review, not "
                    "automatic authority decisions."
                )
            else:
                st.success(
                    "No semantic conflict was detected by S3B."
                )

            if view.uncertainties_present:
                st.warning(
                    "At least one Reconciliation Case remains "
                    "semantically uncertain."
                )

        for case in view.case_reviews:
            st.markdown(
                f"**{case.case_id} · {case.group_label}**"
            )
            st.caption(
                f"{case.outcome} · {len(case.source_ids)} source"
                + ("" if len(case.source_ids) == 1 else "s")
                + f" · {len(case.member_subject_refs)} subject"
                + (
                    ""
                    if len(case.member_subject_refs) == 1
                    else "s"
                )
            )
            st.write(case.summary)

            if case.shared_concepts:
                st.caption(
                    "Shared concepts: "
                    + ", ".join(case.shared_concepts)
                )
            if case.material_differences:
                st.caption(
                    "Material differences: "
                    + " · ".join(case.material_differences)
                )
            for group in case.claim_groups:
                st.caption(
                    f"{group.claim_group_id} · {group.summary}"
                )
                if technical:
                    st.caption(
                        "Evidence: "
                        + ", ".join(
                            group.supported_by_subject_refs
                        )
                    )

        st.warning(
            "Human Project Authority is deliberately closed for "
            "concern-centric Cases until the case-aware authority "
            "workflow is available. Legacy pairwise S4 decisions "
            "cannot be applied to this cycle."
        )
        return

    if technical:
        st.caption(
            f"Cycle {view.cycle_id} · "
            f"{len(view.source_ids)} sources · "
            f"{view.required_decision_count} S3 relations"
        )

    if not view.bindings_ready:
        st.warning(
            "Source-local Approved Input / AEI authority has not yet been "
            "frozen for this exact S3 cycle."
        )
        if st.button(
            "Prepare authority bindings",
            key="project_reconciliation.prepare_bindings",
            type="primary",
        ):
            try:
                service.prepare_authority_bindings(
                    manifest.project_id,
                    view.cycle_id,
                )
            except ProjectReconciliationWorkflowError as exc:
                st.error(str(exc))
            else:
                st.success("Exact source-local authority bindings prepared.")
                _rerun(st)
        return

    reviewer = st.text_input(
        "Reviewer identity",
        value="",
        key=_SESSION_REVIEWER,
        help=(
            "Persisted as the immutable Human actor identity for each "
            "Project Authority decision."
        ),
    )

    st.subheader("Cross-source authority decisions")
    st.caption(
        f"{view.decision_count} / {view.required_decision_count} "
        "relations decided"
    )

    for index, relation in enumerate(view.relation_reviews, start=1):
        title = (
            f"{relation.left_label} ↔ {relation.right_label}"
        )
        with st.expander(
            title,
            expanded=relation.human_decision_id is None,
        ):
            st.write(
                f"Machine relation evidence: **{relation.machine_outcome}**"
            )
            st.write(relation.machine_rationale)

            if relation.shared_concepts:
                st.caption(
                    "Shared concepts: "
                    + ", ".join(relation.shared_concepts)
                )
            if relation.material_differences:
                st.caption(
                    "Material differences: "
                    + "; ".join(relation.material_differences)
                )

            if technical:
                st.caption(
                    f"{relation.left_source_id} · "
                    f"{relation.left_subject_ref} · "
                    f"{relation.left_approved_input_id or 'AIN unavailable'}"
                )
                st.caption(
                    f"{relation.right_source_id} · "
                    f"{relation.right_subject_ref} · "
                    f"{relation.right_approved_input_id or 'AIN unavailable'}"
                )

            if relation.human_decision_id is not None:
                st.success(
                    "Human Project Authority: "
                    f"{_OUTCOME_LABELS[relation.human_outcome]}"
                )
                if technical:
                    st.caption(
                        f"Decision {relation.human_decision_id}"
                        + (
                            ""
                            if relation.authority_concern_id is None
                            else f" · {relation.authority_concern_id}"
                        )
                    )
                continue

            key_base = f"project_reconciliation.relation.{index}"
            outcome = st.selectbox(
                "Project Authority decision",
                options=tuple(_OUTCOME_LABELS),
                format_func=lambda item: _OUTCOME_LABELS[item],
                key=f"{key_base}.outcome",
            )
            retained = None
            if outcome == "supersede":
                participants = tuple(
                    item
                    for item in (
                        relation.left_approved_input_id,
                        relation.right_approved_input_id,
                    )
                    if item is not None
                )
                retained = st.selectbox(
                    "Retain as active project authority",
                    options=participants,
                    key=f"{key_base}.retained",
                )

            rationale = st.text_area(
                "Human rationale",
                key=f"{key_base}.rationale",
            )
            if st.button(
                "Record immutable decision",
                key=f"{key_base}.record",
                type="primary",
            ):
                if not reviewer.strip():
                    st.error("Reviewer identity is required.")
                    continue
                if not rationale.strip():
                    st.error("Human rationale is required.")
                    continue
                try:
                    service.record_authority_decision(
                        manifest.project_id,
                        view.cycle_id,
                        left_subject_ref=relation.left_subject_ref,
                        right_subject_ref=relation.right_subject_ref,
                        outcome=outcome,
                        reviewer_identity=reviewer,
                        rationale=rationale,
                        retained_approved_input_id=retained,
                    )
                except ProjectReconciliationWorkflowError as exc:
                    st.error(str(exc))
                else:
                    st.success("Human Project Authority decision recorded.")
                    _rerun(st)

    if view.open_decision_count:
        return

    if not view.authority_state_ready:
        st.subheader("Finalize Project Engineering Authority")
        st.caption(
            "Finalization re-reads current source-local AIN/AEI authority "
            "and fails closed if it differs from the frozen binding snapshot."
        )
        if st.button(
            "Finalize project authority",
            key="project_reconciliation.finalize_authority",
            type="primary",
        ):
            try:
                state = service.finalize_authority(
                    manifest.project_id,
                    view.cycle_id,
                )
            except ProjectReconciliationWorkflowError as exc:
                st.error(str(exc))
            else:
                if state.model_impact_ready:
                    st.success("Project Engineering Authority finalized.")
                else:
                    st.warning(
                        "Project Engineering Authority finalized with "
                        "unresolved Human decisions. Model impact remains blocked."
                    )
                _rerun(st)
        return

    if not view.model_impact_ready:
        st.warning(
            view.blocking_reason
            or "Project Engineering Authority is unresolved."
        )
        return

    if not view.model_impact_persisted:
        st.subheader("Model Impact Reconciliation")
        st.caption(
            "Compare the resolved project-level engineering authority with "
            "the unique accepted authority-backed Internal Model head. "
            "This remains advisory until Human Model Review."
        )
        if st.button(
            "Reconcile model impact",
            key="project_reconciliation.model_impact",
            type="primary",
        ):
            try:
                service.reconcile_model_impact(
                    manifest.project_id,
                    view.cycle_id,
                )
            except ProjectReconciliationWorkflowError as exc:
                st.error(str(exc))
            else:
                st.success("Model Impact Reconciliation persisted.")
                _rerun(st)
        return

    st.success(
        "Project Reconciliation is complete. Model Proposal may proceed "
        "through the project-authority Phase-H handoff."
    )


def _rerun(st: Any) -> None:
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()
