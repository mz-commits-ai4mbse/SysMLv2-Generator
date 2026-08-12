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
from app.turing_generator_navigation import (
    APP_VIEW_DASHBOARD,
    SESSION_SELECTED_ENTITY_ID,
    queue_app_view,
    read_navigation_state,
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
    """Render the project-bound Human Review and Approval workspace."""

    st = streamlit_module
    root = Path(project_root)
    navigation = read_navigation_state(st.session_state)
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

    st.header("Human Review & Approval")

    if navigation.project_id is None:
        st.error(
            "No valid Project is selected. Open the Project Dashboard "
            "and select a Project before starting Human Review."
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

    st.caption(
        f"Selected Project: {manifest.display_name} · {manifest.project_id}"
    )
    st.caption(
        "Human Review creates immutable Review Revisions and explicit "
        "approval evidence. Agent Outputs and Consensus remain evidence, "
        "not approval authority."
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

    _render_project_issues(st, project_view)
    reviewer_identity = _render_review_queue(
        st,
        service=service,
        project_view=project_view,
        project_id=manifest.project_id,
    )

    selected_document_id = st.session_state.get(
        SESSION_SELECTED_ENTITY_ID
    )
    if (
        isinstance(selected_document_id, str)
        and selected_document_id.startswith("RVD-")
    ):
        _render_selected_workspace(
            st,
            service=service,
            project_id=manifest.project_id,
            review_document_id=selected_document_id,
            reviewer_identity=reviewer_identity,
        )

    _render_dashboard_return(
        st,
        project_id=manifest.project_id,
        return_view=navigation.return_view,
    )


def _render_project_issues(st: Any, project_view) -> None:
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

    st.table(
        [
            {
                "Source": item.source_id,
                "Filename": item.original_filename,
                "Processing Run": item.processing_run_id,
                "Run state": item.run_state or "Unavailable",
                "Review Document": item.review_document_id or "Not created",
                "Review Version": (
                    item.review_document_version_id or "Not created"
                ),
                "Review items": item.review_item_count,
                "Workflow": item.workflow_status,
                "Active Approved Inputs": len(
                    item.active_approved_input_ids
                ),
            }
            for item in project_view.items
        ]
    )

    for item in project_view.items:
        if item.review_document_id is None:
            if st.button(
                f"Create Review for {item.processing_run_id}",
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
                        "Initial Review Workspace created."
                        if result.created
                        else "Existing Review Workspace opened."
                    )
                    _rerun(st)
            continue

        if st.button(
            f"Open {item.review_document_id}",
            key=(
                "human_review_approval.open."
                f"{item.review_document_id}"
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

    st.subheader(f"Selected Review · {view.document.review_document_id}")
    st.caption(
        f"Version {view.version.version_number} · "
        f"{view.version.review_document_version_id} · "
        f"{view.version.version_state} · "
        f"Revision {view.revision.review_revision_id}"
    )

    outcome_counts = {}
    for item in view.revision.review_items:
        outcome_counts[item.effective_review_outcome] = (
            outcome_counts.get(item.effective_review_outcome, 0) + 1
        )

    st.table(
        [
            {
                "Review items": len(view.revision.review_items),
                "Scoped actions": len(view.scoped_actions),
                "Can finalize": view.can_finalize,
                "Can promote": view.can_promote,
                "Active Approved Inputs": len(
                    view.active_approved_input_ids
                ),
                "Outcomes": ", ".join(
                    f"{key}: {value}"
                    for key, value in sorted(outcome_counts.items())
                ),
            }
        ]
    )

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
