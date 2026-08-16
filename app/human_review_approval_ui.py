"""Streamlit adapter for G6 Human Review and Approval."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.human_review_finalization_ui import (
    render_review_finalization_ui,
)
from app.human_review_promotion_ui import (
    render_approved_input_promotion_ui,
)
from app.human_review_item_editor_ui import (
    render_review_item_editor,
)
from app.presentation_preferences import technical_details_enabled
from app.turing_generator_navigation import (
    APP_VIEW_DASHBOARD,
    SESSION_SELECTED_ENTITY_ID,
    queue_app_view,
    read_navigation_state,
)
from modules.guided_workflow import (
    GuidedWorkflowValidationError,
    build_review_queue_item_view,
)
from modules.project_workspace import (
    ProjectWorkspace,
    ProjectWorkspaceError,
)
from modules.review_workspace import (
    ReviewApprovalWorkflowService,
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
    ReviewWorkspaceError,
)


_SESSION_REVIEWER_IDENTITY = "human_review_approval.reviewer_identity"


def render_human_review_approval_ui(
    project_root: Path,
    *,
    streamlit_module: Any,
    project_workspace: ProjectWorkspace | None = None,
    workflow_service: ReviewApprovalWorkflowService | None = None,
) -> None:
    """Render the project-bound Human Review workspace."""

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
        ReviewApprovalWorkflowService(
            root=root / "data" / "projects",
            repository_root=root,
        )
        if workflow_service is None
        else workflow_service
    )

    st.header("Human Review")

    if navigation.project_id is None:
        st.error(
            "No valid Project is selected. Select a Project before "
            "starting Human Review."
        )
        _render_dashboard_return(
            st,
            project_id=None,
            return_view=navigation.return_view,
        )
        return

    try:
        manifest = workspace.load_project(navigation.project_id)
    except ProjectWorkspaceError:
        st.error(
            "The selected Project Workspace is unavailable or invalid. "
            "No fallback Project was selected."
        )
        _render_dashboard_return(
            st,
            project_id=None,
            return_view=navigation.return_view,
        )
        return
    except Exception:
        st.error(
            "The selected Project Workspace could not be validated. "
            "No fallback Project was selected."
        )
        _render_dashboard_return(
            st,
            project_id=None,
            return_view=navigation.return_view,
        )
        return

    if technical:
        st.caption(
            f"Project: {manifest.display_name} · {manifest.project_id}"
        )
    else:
        st.caption(f"Project: {manifest.display_name}")

    st.caption(
        "Compare the independent engineering interpretations, resolve "
        "open decisions and prepare reviewed content for Approved Input."
    )

    try:
        project_view = service.project_view(manifest.project_id)
    except ReviewWorkspaceError:
        st.error(
            "Human Review state could not be validated for this Project."
        )
        _render_dashboard_return(
            st,
            project_id=manifest.project_id,
            return_view=navigation.return_view,
        )
        return
    except Exception:
        st.error(
            "Human Review state is unavailable. No fallback state "
            "was inferred."
        )
        _render_dashboard_return(
            st,
            project_id=manifest.project_id,
            return_view=navigation.return_view,
        )
        return

    _render_project_issues(
        st,
        project_view,
        technical=technical,
    )
    reviewer_identity = _render_review_queue(
        st,
        service=service,
        project_view=project_view,
        project_id=manifest.project_id,
        technical=technical,
    )

    selected_document_id = st.session_state.get(
        SESSION_SELECTED_ENTITY_ID
    )
    if (
        isinstance(selected_document_id, str)
        and selected_document_id.startswith("RVD-")
    ):
        queue_item = next(
            (
                item
                for item in project_view.items
                if item.review_document_id == selected_document_id
            ),
            None,
        )
        _render_selected_workspace(
            st,
            service=service,
            project_id=manifest.project_id,
            review_document_id=selected_document_id,
            reviewer_identity=reviewer_identity,
            queue_item=queue_item,
            technical=technical,
        )

    _render_dashboard_return(
        st,
        project_id=manifest.project_id,
        return_view=navigation.return_view,
    )


def _render_project_issues(
    st: Any,
    project_view,
    *,
    technical: bool,
) -> None:
    if not project_view.issues:
        return

    blocking = tuple(
        issue
        for issue in project_view.issues
        if issue.issue_level == "blocking"
    )
    if blocking:
        st.warning(
            f"{len(blocking)} blocking Human Review workflow issue(s) "
            "require attention. Write actions remain fail-closed."
        )
    else:
        st.info(
            f"{len(project_view.issues)} Human Review workflow warning(s) "
            "are present."
        )

    if not technical:
        return

    st.table(
        [
            {
                "Level": issue.issue_level,
                "Domain": issue.source_domain,
                "Code": issue.code,
                "Message": issue.message,
            }
            for issue in project_view.issues
        ]
    )


def _render_review_queue(
    st: Any,
    *,
    service: ReviewApprovalWorkflowService,
    project_view,
    project_id: str,
    technical: bool = False,
) -> str:
    st.subheader("Review Queue")

    reviewer_identity = st.text_input(
        "Reviewer identity",
        value="",
        key=_SESSION_REVIEWER_IDENTITY,
        help=(
            "Used as the immutable actor identity for Human Review "
            "write actions."
        ),
    )

    if not project_view.items:
        st.info("No Human Review work is currently available.")
        return reviewer_identity

    queue_views = []
    try:
        for item in project_view.items:
            queue_views.append(
                (item, build_review_queue_item_view(item))
            )
    except GuidedWorkflowValidationError:
        st.error(
            "Human Review queue presentation could not be reconstructed "
            "from the authoritative workflow state."
        )
        return reviewer_identity

    rows = []
    for item, view in queue_views:
        row = {
            "Source": view.source_filename,
            "Status": view.status_label,
            "Decisions required": view.decisions_required,
            "Review items": view.review_item_count,
            "Approved inputs": view.active_approved_input_count,
        }
        if technical:
            row.update(
                {
                    "Source ID": view.source_id,
                    "Processing Run": view.processing_run_id,
                    "Run state": view.run_state or "Unavailable",
                    "Review Document": (
                        view.review_document_id or "Not created"
                    ),
                    "Review Version": (
                        view.review_document_version_id or "Not created"
                    ),
                    "Workflow": view.workflow_status,
                }
            )
        rows.append(row)

    st.table(rows)

    for item, view in queue_views:
        if item.review_document_id is None:
            if st.button(
                f"Start review · {view.source_filename}",
                key=(
                    "human_review_approval.create."
                    f"{item.processing_run_id}"
                ),
                type="primary",
            ):
                if not reviewer_identity.strip():
                    st.error(
                        "Reviewer identity is required before creating "
                        "an initial Review Workspace."
                    )
                    continue
                try:
                    result = service.open_or_create_review(
                        project_id,
                        item.processing_run_id,
                        opened_by=reviewer_identity,
                    )
                except (
                    ReviewIntegrityError,
                    ReviewReferenceError,
                    ReviewValidationError,
                ):
                    st.error(
                        "Initial Review Workspace creation was blocked "
                        "by validation, integrity or evidence checks."
                    )
                except Exception:
                    st.error(
                        "Initial Review Workspace creation failed. "
                        "No success state was inferred."
                    )
                else:
                    st.session_state[
                        SESSION_SELECTED_ENTITY_ID
                    ] = result.review_document_id
                    st.success(
                        "Human Review started."
                        if result.created
                        else "Existing Human Review opened."
                    )
                    _rerun(st)
            continue

        if st.button(
            f"Open review · {view.source_filename}",
            key=(
                "human_review_approval.open."
                f"{item.review_document_id}"
            ),
            type=(
                "primary"
                if view.decisions_required > 0
                else None
            ),
        ):
            st.session_state[
                SESSION_SELECTED_ENTITY_ID
            ] = item.review_document_id
            _rerun(st)

    return reviewer_identity


def _render_selected_workspace(
    st: Any,
    *,
    service: ReviewApprovalWorkflowService,
    project_id: str,
    review_document_id: str,
    reviewer_identity: str,
    queue_item,
    technical: bool,
) -> None:
    try:
        view = service.workspace_view(
            project_id,
            review_document_id,
        )
    except (ReviewIntegrityError, ReviewReferenceError):
        st.error(
            "The selected Review Workspace could not be resolved "
            "to one exact current state."
        )
        return
    except Exception:
        st.error(
            "The selected Review Workspace is unavailable. "
            "No replacement state was inferred."
        )
        return

    source_label = (
        queue_item.original_filename
        if queue_item is not None
        else "Selected source"
    )
    st.subheader(f"Review · {source_label}")

    if technical:
        st.caption(
            f"{view.document.review_document_id} · "
            f"Version {view.version.version_number} / "
            f"{view.version.review_document_version_id} · "
            f"{view.version.version_state} · "
            f"Revision {view.revision.review_revision_id}"
        )

    outcome_counts = {}
    for item in view.revision.review_items:
        outcome_counts[item.effective_review_outcome] = (
            outcome_counts.get(item.effective_review_outcome, 0) + 1
        )

    decisions_required = sum(
        outcome_counts.get(outcome, 0)
        for outcome in ("open", "deferred", "unresolved")
    )
    if view.version.version_state == "finalized":
        status = "Review finalized"
    elif decisions_required:
        status = "Human decisions required"
    elif view.can_finalize:
        status = "Ready to finalize"
    else:
        status = "Review ready for completion"

    summary = {
        "Status": status,
        "Decisions required": decisions_required,
        "Review items": len(view.revision.review_items),
        "Approved inputs": len(view.active_approved_input_ids),
    }
    if technical:
        summary.update(
            {
                "Scoped actions": len(view.scoped_actions),
                "Can finalize": view.can_finalize,
                "Can promote": view.can_promote,
                "Outcomes": ", ".join(
                    f"{key}: {value}"
                    for key, value in sorted(outcome_counts.items())
                ),
            }
        )
    st.table([summary])

    if view.has_blocking_issues:
        st.warning(
            "Blocking integrity issues apply to this Review Workspace."
        )

    render_review_item_editor(
        st,
        service=service,
        project_id=project_id,
        workspace_view=view,
        reviewer_identity=reviewer_identity,
    )

    if view.version.version_state == "finalized":
        render_approved_input_promotion_ui(
            st,
            service=service,
            project_id=project_id,
            workspace_view=view,
        )

    render_review_finalization_ui(
        st,
        service=service,
        project_id=project_id,
        workspace_view=view,
        reviewer_identity=reviewer_identity,
    )


def _render_dashboard_return(
    st: Any,
    *,
    project_id: str | None,
    return_view: str,
) -> None:
    if st.button(
        "Return to Project Dashboard",
        key="human_review_approval.return_to_dashboard",
    ):
        queue_app_view(
            st.session_state,
            active_view=APP_VIEW_DASHBOARD,
            project_id=project_id,
            dashboard_view=return_view,
        )
        _rerun(st)


def _rerun(st: Any) -> None:
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()
