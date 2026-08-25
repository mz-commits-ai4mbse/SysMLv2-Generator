"""Whole-model Final Model Review over a persisted Assembly Draft."""

from __future__ import annotations

from app.guided_workflow_actions import SESSION_GUIDED_REVIEWER_IDENTITY
from modules.guided_workflow.errors import GuidedWorkflowWriteError
from modules.framework import load_framework_template


def render_model_final_review(
    st,
    *,
    project_id: str,
    draft,
    profile,
    write_service,
    technical: bool = False,
):
    """Render one explicit Human decision over the assembled model."""

    st.subheader("Final Model Review")
    st.caption(
        "Review the assembled model as a whole. Placement authority is "
        "already fixed; this review resolves remaining target Relationship "
        "representation and approves the complete model for materialization."
    )

    try:
        latest = write_service.load_model_final_review_decision(
            project_id,
            draft.comparison_fingerprint,
        )
    except GuidedWorkflowWriteError:
        st.error("Final Model Review state could not be loaded safely.")
        return

    if latest is not None:
        if latest.decision == "approved":
            st.success("Assembled model approved for materialization.")
        else:
            st.warning("Changes requested for the assembled model.")
        st.caption(
            f"Reviewer: {latest.reviewer_identity} · "
            f"Decision: {latest.final_assembly_decision_id}"
        )
        if latest.rationale:
            st.write(latest.rationale)
        if latest.relationship_resolutions:
            with st.expander("Final Relationship resolutions"):
                for item in latest.relationship_resolutions:
                    st.write(
                        f"• {item.relationship_decision_id}: "
                        f"{item.selected_rule_id}"
                    )
                    if technical:
                        st.caption(item.resolution_source)

        if latest.decision == "approved":
            _render_internal_model_materialization(
                st,
                project_id=project_id,
                draft=draft,
                final_decision=latest,
                profile=profile,
                write_service=write_service,
                technical=technical,
            )
        return

    try:
        options = write_service.model_final_review_options(
            draft,
            profile=profile,
        )
    except GuidedWorkflowWriteError:
        st.error(
            "Final Model Review Relationship options could not be built safely."
        )
        return

    reviewer = st.text_input(
        "Final reviewer",
        key=SESSION_GUIDED_REVIEWER_IDENTITY,
        placeholder="Reviewer name",
    )

    selected = {}
    by_id = {
        item.relationship_decision_id: item
        for item in draft.relationships
    }
    if options:
        st.markdown("**Relationship representation**")
    for relationship_id in sorted(options):
        relationship = by_id[relationship_id]
        available = options[relationship_id]
        default = _default_relationship_rule(relationship, available)
        index = available.index(default) if default in available else 0

        st.markdown(
            f"**{relationship_id} · "
            f"{relationship.relationship_kind}**"
        )
        st.caption(
            "Assembly status: "
            + _humanize(relationship.representation_status)
        )
        if relationship.candidate_rule_ids:
            st.caption(
                "Assembly proposal(s): "
                + ", ".join(relationship.candidate_rule_ids)
            )

        selected[relationship_id] = st.selectbox(
            "Target Relationship representation",
            options=available,
            index=index,
            key=(
                "guided_final_model.relationship."
                f"{draft.content_fingerprint}."
                f"{relationship_id}"
            ),
        )

    rationale = st.text_area(
        "Final review rationale",
        key=(
            "guided_final_model.rationale."
            f"{draft.content_fingerprint}"
        ),
        placeholder=(
            "Required when resolving variance/unmapped Relationships "
            "or when requesting changes."
        ),
    )

    columns = st.columns(2)
    if columns[0].button(
        "Approve assembled model",
        key=(
            "guided_final_model.approve."
            f"{draft.content_fingerprint}"
        ),
    ):
        if not reviewer.strip():
            st.error("Enter a reviewer before approving the model.")
            return
        try:
            write_service.record_model_final_review_decision(
                project_id,
                draft=draft,
                profile=profile,
                decision="approved",
                selected_relationship_rules=selected,
                reviewer_identity=reviewer.strip(),
                rationale=rationale.strip() or None,
            )
        except GuidedWorkflowWriteError:
            st.error(
                "Final Model Review approval could not be recorded safely."
            )
            return
        st.success("Assembled model approved for materialization.")
        _rerun(st)
        return

    if columns[1].button(
        "Request changes",
        key=(
            "guided_final_model.changes."
            f"{draft.content_fingerprint}"
        ),
    ):
        if not reviewer.strip():
            st.error("Enter a reviewer before requesting changes.")
            return
        if not rationale.strip():
            st.error("Provide a rationale for the requested changes.")
            return
        try:
            write_service.record_model_final_review_decision(
                project_id,
                draft=draft,
                profile=profile,
                decision="changes_requested",
                selected_relationship_rules=None,
                reviewer_identity=reviewer.strip(),
                rationale=rationale.strip(),
            )
        except GuidedWorkflowWriteError:
            st.error(
                "Final Model Review change request could not be recorded safely."
            )
            return
        st.warning("Changes requested for the assembled model.")
        _rerun(st)


def _render_internal_model_materialization(
    st,
    *,
    project_id,
    draft,
    final_decision,
    profile,
    write_service,
    technical,
):
    try:
        model = write_service.load_authority_backed_internal_model(
            project_id,
            draft.comparison_fingerprint,
        )
    except GuidedWorkflowWriteError:
        st.error("Internal Model state could not be loaded safely.")
        return

    if model is not None:
        st.success(
            "Internal Model materialized: "
            f"{model.internal_engineering_model_id}"
        )
        st.caption(
            f"{len(model.elements)} elements · "
            f"{len(model.relationships)} relationships"
        )
        if technical:
            st.caption(
                "Internal Model fingerprint: "
                f"{model.content_fingerprint}"
            )
        generation_model = _render_sem015_successor_selection(
            st,
            project_id=project_id,
            base_model=model,
            write_service=write_service,
            technical=technical,
        )
        _render_authority_backed_sysml(
            st,
            project_id=project_id,
            model=generation_model,
            write_service=write_service,
            technical=technical,
        )
        return

    st.markdown("**Internal Model materialization**")
    st.caption(
        "This creates the authority-backed Internal Model directly from "
        "approved placement and Final Model Review. No Candidate Review "
        "decision is synthesized."
    )
    if st.button(
        "Materialize Internal Model",
        key=(
            "guided_final_model.materialize."
            f"{draft.content_fingerprint}"
        ),
    ):
        try:
            template = load_framework_template()
            write_service.materialize_authority_backed_internal_model(
                project_id,
                draft=draft,
                final_decision=final_decision,
                profile=profile,
                framework_template=template,
            )
        except Exception:
            st.error(
                "Internal Model materialization failed safely. "
                "The approved Assembly authority remains unchanged."
            )
            return
        st.success("Authority-backed Internal Model materialized.")
        _rerun(st)


def _render_sem015_successor_selection(
    st,
    *,
    project_id,
    base_model,
    write_service,
    technical,
):
    try:
        successors = write_service.list_sem015_successor_internal_models(
            project_id,
            base_model.internal_engineering_model_id,
        )
    except GuidedWorkflowWriteError:
        st.error("SEM-015 successor state could not be loaded safely.")
        return base_model

    if not successors:
        st.warning(
            "No SEM-015 quality/formulation successor is available yet. "
            "Generation remains bound to the base Internal Model."
        )
        return base_model

    st.markdown("**SEM-015 approved model**")
    st.caption(
        "Select the exact Human-authorized successor used for deterministic "
        "SysML generation. No implicit latest selection is performed."
    )

    options = {
        item["internal_engineering_model_id"]: item
        for item in successors
    }
    selected_id = st.selectbox(
        "Approved Internal Model",
        options=tuple(options),
        key=(
            "guided_final_model.sem015_successor."
            f"{base_model.content_fingerprint}"
        ),
    )
    selected = options[selected_id]
    model = selected["model"]

    st.success(
        f"Using {model.internal_engineering_model_id}: "
        f"{len(model.elements)} elements · "
        f"{len(model.relationships)} formal relationships"
    )
    st.caption(
        "Human authority: "
        f"{selected['target_model_formulation_authority_set_id']} · "
        f"{selected['model_quality_authority_set_id']}"
    )
    omitted = selected[
        "intentionally_not_materialized_relationship_ids"
    ]
    if omitted:
        st.caption(
            f"{len(omitted)} relationship(s) intentionally not "
            "materialized; authority remains traceable."
        )
    if technical:
        st.caption(
            "SEM-015 successor fingerprint: "
            f"{model.content_fingerprint}"
        )
    return model


def _render_authority_backed_sysml(
    st,
    *,
    project_id,
    model,
    write_service,
    technical,
):
    try:
        artifact = write_service.load_authority_backed_sysml(
            project_id,
            model.internal_engineering_model_id,
        )
    except GuidedWorkflowWriteError:
        st.error("Generated SysML v2 state could not be loaded safely.")
        return

    if artifact is None:
        st.markdown("**SysML v2 generation**")
        st.caption(
            "Generate deterministic textual SysML v2 directly from the "
            "authority-backed Internal Model."
        )
        if st.button(
            "Generate SysML v2",
            key=(
                "guided_final_model.generate_sysml."
                f"{model.content_fingerprint}"
            ),
        ):
            try:
                write_service.generate_authority_backed_sysml(
                    project_id,
                    snapshot=model,
                )
            except GuidedWorkflowWriteError:
                st.error(
                    "SysML v2 generation failed safely. "
                    "The Internal Model remains unchanged."
                )
                return
            st.success("SysML v2 generated.")
            _rerun(st)
        return

    st.success("SysML v2 generated from the approved Internal Model.")
    for unit in artifact.units:
        st.markdown(f"**{unit.relative_path}**")
        st.code(unit.content, language="text")
    st.caption(
        f"{len(artifact.traceability_entries)} authority-backed "
        "traceability entries"
    )
    if technical:
        st.caption(
            "Generated artifact fingerprint: "
            f"{artifact.content_fingerprint}"
        )


def _syside_quality_summary(result):
    """Return one stable UI summary for external SYSIDE validation."""

    evidence_items = getattr(result, "external_validator_evidence", ())
    for evidence in evidence_items:
        identity = getattr(evidence, "validator_identity", None)
        if (
            identity is not None
            and getattr(identity, "tool_name", None) == "SYSIDE Modeler CLI"
        ):
            status = getattr(evidence, "execution_status", None)
            exit_code = getattr(evidence, "exit_code", None)
            diagnostics = getattr(evidence, "normalized_diagnostic_count", None)
            passed = status == "completed" and exit_code == 0 and diagnostics == 0
            return {
                "available": True,
                "passed": passed,
                "status": status,
                "exit_code": exit_code,
                "diagnostics": diagnostics,
                "version": getattr(identity, "tool_version", None),
            }
    return {
        "available": False,
        "passed": False,
        "status": None,
        "exit_code": None,
        "diagnostics": None,
        "version": None,
    }


def _render_syside_quality_metric(st, result, *, prefix="External"):
    summary = _syside_quality_summary(result)

    st.markdown("**External SysML v2 validation**")
    if not summary["available"]:
        st.warning("SYSIDE validation: NOT AVAILABLE")
        return

    if summary["passed"]:
        st.success("SYSIDE validation: PASSED")
    elif summary["status"] == "completed":
        st.error("SYSIDE validation: FAILED")
    else:
        st.warning("SYSIDE validation: INCOMPLETE")

    columns = st.columns(3)
    columns[0].metric("SYSIDE", "PASS" if summary["passed"] else "NOT PASS")
    columns[1].metric(
        "Diagnostics",
        str(summary["diagnostics"]) if summary["diagnostics"] is not None else "—",
    )
    columns[2].metric(
        "Exit code",
        str(summary["exit_code"]) if summary["exit_code"] is not None else "—",
    )

    if summary["version"]:
        st.caption(f"{prefix} validator: SYSIDE Modeler CLI · {summary['version']}")
    st.caption(
        "Quality dimension: external SysML v2 conformance / tool compatibility. "
        "This does not replace engineering content-quality review."
    )


def _render_authority_backed_validation(
    st,
    *,
    project_id,
    artifact,
    write_service,
    technical,
):
    try:
        result = (
            write_service.load_authority_backed_sysml_validation(
                project_id,
                artifact.source_internal_engineering_model_id,
            )
        )
    except GuidedWorkflowWriteError:
        st.error("SysML v2 validation state could not be loaded safely.")
        return

    if result is None:
        st.markdown("**SysML v2 validation**")
        st.caption(
            "Run deterministic Phase-K checks plus the required isolated "
            "SYSIDE Modeler CLI validation."
        )
        if st.button(
            "Validate SysML v2",
            key=(
                "guided_final_model.validate_sysml."
                f"{artifact.content_fingerprint}"
            ),
        ):
            try:
                spinner = getattr(st, "spinner", None)
                if callable(spinner):
                    with spinner(
                        "Validating generated SysML v2 with Phase K..."
                    ):
                        write_service.validate_authority_backed_sysml(
                            project_id,
                            artifact=artifact,
                        )
                else:
                    write_service.validate_authority_backed_sysml(
                        project_id,
                        artifact=artifact,
                    )
            except GuidedWorkflowWriteError:
                st.error(
                    "SysML v2 validation failed safely. "
                    "Generated artifacts remain unchanged."
                )
                return
            st.success("SysML v2 validation completed.")
            _rerun(st)
        return

    if (
        result.validation_status == "valid"
        and result.publication_gate == "passed"
    ):
        st.success("SysML v2 validation: VALID · publication gate PASSED")
    elif result.validation_status == "incomplete":
        st.warning(
            "SysML v2 validation: INCOMPLETE · publication gate BLOCKED"
        )
    else:
        st.error(
            "Persisted SysML v2 validation: INVALID · publication gate BLOCKED"
        )

    preview_key = (
        "guided_final_model.current_validation_preview."
        f"{artifact.content_fingerprint}"
    )
    current_preview = st.session_state.get(preview_key)

    st.markdown("**Current validator run**")
    st.caption(
        "External SYSIDE validation is started explicitly and cached for "
        "this artifact during the current app session."
    )
    if st.button(
        (
            "Run current SYSIDE validation"
            if current_preview is None
            else "Re-run current SYSIDE validation"
        ),
        key=f"{preview_key}.run",
    ):
        try:
            current_preview = (
                write_service.preview_authority_backed_sysml_validation(
                    project_id,
                    artifact=artifact,
                )
            )
            st.session_state[preview_key] = current_preview
        except GuidedWorkflowWriteError:
            st.error("Current SYSIDE validation could not be completed.")
            current_preview = None

    if (
        current_preview is not None
        and current_preview.content_fingerprint
        != result.content_fingerprint
    ):
        st.info(
            "A read-only validation with the current Phase-K implementation "
            "differs from the persisted historical result."
        )
        if current_preview.validation_status == "valid":
            st.success(
                "Current validation preview: VALID · publication gate PASSED"
            )
        elif current_preview.validation_status == "incomplete":
            st.warning(
                "Current validation preview: INCOMPLETE · "
                "publication gate BLOCKED"
            )
        else:
            st.error(
                "Current validation preview: INVALID · "
                "publication gate BLOCKED"
            )
        _render_syside_quality_metric(
            st,
            current_preview,
            prefix="Current",
        )
        if current_preview.findings:
            with st.expander(
                "Current validation preview findings "
                f"({len(current_preview.findings)})"
            ):
                for finding in current_preview.findings:
                    marker = (
                        "BLOCKING"
                        if finding.blocking
                        else finding.severity
                    )
                    st.write(
                        f"• [{marker}] {finding.code}: "
                        f"{finding.message}"
                    )

    _render_syside_quality_metric(
        st,
        result,
        prefix="Persisted",
    )

    if result.findings:
        with st.expander(
            f"Validation findings ({len(result.findings)})"
        ):
            for finding in result.findings:
                marker = "BLOCKING" if finding.blocking else finding.severity
                st.write(
                    f"• [{marker}] {finding.code}: {finding.message}"
                )
                if technical and finding.validator_id:
                    st.caption(
                        f"Validator: {finding.validator_id}"
                    )
    if technical:
        st.caption(
            "Validation result fingerprint: "
            f"{result.content_fingerprint}"
        )


def _default_relationship_rule(relationship, available):
    if len(relationship.candidate_rule_ids) == 1:
        value = relationship.candidate_rule_ids[0]
        if value in available:
            return value
    return available[0]


def _humanize(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _rerun(st):
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()
