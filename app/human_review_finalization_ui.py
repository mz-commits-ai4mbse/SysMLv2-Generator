"""Finalization UI for G6 Human Review & Approval."""

from __future__ import annotations

from typing import Any

from app.presentation_preferences import technical_details_enabled
from modules.review_workspace.errors import ReviewWorkspaceError


def render_review_finalization_ui(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    reviewer_identity: str,
) -> None:
    """Render exact draft finalization or finalized artifact authority."""

    st.subheader("Finalization")

    if workspace_view.version.version_state == "finalized":
        _render_finalized_authority(
            st,
            service=service,
            project_id=project_id,
            workspace_view=workspace_view,
            reviewer_identity=reviewer_identity,
        )
        return

    if workspace_view.version.version_state != "draft":
        st.error(
            "The selected Review Version has an unsupported lifecycle state."
        )
        return

    _render_draft_finalization(
        st,
        service=service,
        project_id=project_id,
        workspace_view=workspace_view,
        reviewer_identity=reviewer_identity,
    )


def _render_draft_finalization(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    reviewer_identity: str,
) -> None:
    technical = technical_details_enabled(
        getattr(st, "session_state", {})
    )

    try:
        preview = service.finalization_preview(
            project_id,
            workspace_view.document.review_document_id,
            workspace_view.version.review_document_version_id,
        )
    except ReviewWorkspaceError:
        st.error(
            "Finalization assessment is blocked by validation, "
            "integrity, stale-state or recovery checks."
        )
        return
    except Exception:
        st.error(
            "Finalization assessment is unavailable. "
            "No eligible state was inferred."
        )
        return

    assessment = preview.assessment
    blocking_count = len(assessment.blocking_issue_codes)

    st.table(
        [
            {
                "Status": (
                    "Ready for final confirmation"
                    if preview.eligible_for_confirmation
                    else "Review changes required"
                ),
                "Blocking findings": blocking_count,
                "Human confirmation": (
                    "Recorded"
                    if preview.has_exact_confirmation
                    else "Required"
                ),
            }
        ]
    )

    if blocking_count:
        st.warning(
            f"Finalization is blocked by {blocking_count} finding(s). "
            "Resolve the affected Review Items or record a review decision."
        )
    elif preview.has_exact_confirmation:
        st.success(
            "The exact current Review Revision has been confirmed by a "
            "persisted Human Review Decision."
        )
    else:
        st.success(
            "The exact current Review Revision has no blocking findings."
        )

    if technical:
        st.table(
            [
                {
                    "Review Revision": assessment.review_revision_id,
                    "Eligible": preview.eligible_for_confirmation,
                    "Latest exact HRD": (
                        preview.latest_exact_decision_id or "None"
                    ),
                    "Latest exact decision": (
                        preview.latest_exact_decision or "None"
                    ),
                    "Exact confirmation": (
                        preview.exact_confirmation_decision_id or "None"
                    ),
                    "Validation fingerprint": (
                        assessment.validation_fingerprint
                    ),
                }
            ]
        )

        if assessment.item_snapshots:
            st.table(
                [
                    {
                        "Review Item": item.review_item_id,
                        "Kind": item.review_item_kind,
                        "Outcome": item.effective_review_outcome,
                        "Relationship validation": (
                            item.relationship_validation_status
                            or "not applicable"
                        ),
                        "Content fingerprint": (
                            item.item_content_fingerprint
                        ),
                    }
                    for item in assessment.item_snapshots
                ]
            )

        if assessment.blocking_issue_codes:
            st.table(
                [
                    {"Blocking finding": code}
                    for code in assessment.blocking_issue_codes
                ]
            )

    decision_options = (
        ("confirm", "request_changes", "reject")
        if preview.eligible_for_confirmation
        else ("request_changes", "reject")
    )

    st.markdown("**Human review decision**")
    decision = st.selectbox(
        "Decision",
        options=decision_options,
        index=0,
        format_func=_decision_label,
        key=(
            "human_review_finalization.decision."
            f"{workspace_view.version.review_document_version_id}"
        ),
    )

    rationale = _optional_text(
        st.text_input(
            "Decision rationale",
            value="",
            key=(
                "human_review_finalization.rationale."
                f"{workspace_view.version.review_document_version_id}"
            ),
            help=(
                "Required for request changes and reject. "
                "Optional for confirm."
            ),
        )
    )

    explicit_confirmation = True
    if decision == "confirm":
        explicit_confirmation = st.checkbox(
            "I confirm that I reviewed this exact version in detail.",
            value=False,
            key=(
                "human_review_finalization.confirm_exact."
                f"{workspace_view.version.review_document_version_id}"
            ),
        )

    if st.button(
        "Record review decision",
        key=(
            "human_review_finalization.record."
            f"{workspace_view.version.review_document_version_id}"
        ),
    ):
        if not _reviewer_ready(st, reviewer_identity):
            return

        if decision != "confirm" and rationale is None:
            st.error(
                f"{_decision_label(decision)} requires a reviewer rationale."
            )
            return

        if decision == "confirm" and not explicit_confirmation:
            st.error(
                "Exact detailed-review confirmation must be explicitly checked."
            )
            return

        try:
            result = service.record_finalization_decision(
                project_id,
                workspace_view.document.review_document_id,
                workspace_view.version.review_document_version_id,
                decision=decision,
                reviewer_identity=reviewer_identity,
                rationale=rationale,
            )
        except ReviewWorkspaceError:
            st.error(
                "The Human Review Decision was blocked by validation, "
                "integrity or stale-state checks."
            )
            return
        except Exception:
            st.error(
                "The Human Review Decision could not be persisted. "
                "No successful decision was inferred."
            )
            return

        if technical:
            st.success(
                "Review decision persisted: "
                f"{result.human_review_decision_id}."
            )
        else:
            st.success("Review decision recorded.")
        _rerun(st)
        return

    if not preview.has_exact_confirmation:
        st.info(
            "Finalize becomes available after an exact Human confirmation "
            "has been persisted for the current Review Revision."
        )
        return

    st.markdown("**Finalize reviewed content**")
    st.caption(
        "Finalization freezes this Review Version and publishes its immutable "
        "reviewed artifact set."
    )

    finalize_confirmation = st.checkbox(
        "I confirm finalization of this exact reviewed version.",
        value=False,
        key=(
            "human_review_finalization.finalize_exact."
            f"{workspace_view.version.review_document_version_id}"
        ),
    )

    if st.button(
        "Finalize reviewed content",
        key=(
            "human_review_finalization.finalize."
            f"{workspace_view.version.review_document_version_id}"
        ),
        type="primary",
    ):
        if not finalize_confirmation:
            st.error(
                "Finalization must be explicitly confirmed."
            )
            return

        try:
            result = service.finalize_review_version(
                project_id,
                workspace_view.document.review_document_id,
                workspace_view.version.review_document_version_id,
            )
        except ReviewWorkspaceError:
            st.error(
                "Finalization was blocked by validation, integrity, "
                "stale-state or recovery checks."
            )
            return
        except Exception:
            st.error(
                "Finalization failed. "
                "No finalized authority state was inferred."
            )
            return

        if technical:
            st.success(
                "Review Version finalized with "
                f"{result.finalization_decision_id}."
            )
        else:
            st.success(
                "Reviewed content finalized. The immutable reviewed "
                "artifact set is now available."
            )
        _rerun(st)


def _render_finalized_authority(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    reviewer_identity: str,
) -> None:
    technical = technical_details_enabled(
        getattr(st, "session_state", {})
    )

    try:
        artifact_set = service.finalized_artifact_set(
            project_id,
            workspace_view.document.review_document_id,
            workspace_view.version.review_document_version_id,
        )
    except ReviewWorkspaceError:
        st.error(
            "Finalized Review authority could not be loaded or validated."
        )
        return
    except Exception:
        st.error(
            "Finalized Review authority is unavailable. "
            "No artifact state was inferred."
        )
        return

    reviewed_document = artifact_set.reviewed_document

    st.success(
        "This reviewed version is finalized and immutable."
    )

    if technical:
        st.table(
            [
                {
                    "Finalized Revision": (
                        reviewed_document.review_revision_id
                    ),
                    "Decision": (
                        reviewed_document.finalization_decision_id
                    ),
                    "Reviewer": reviewed_document.reviewer_identity,
                    "Decision at": reviewed_document.decision_at,
                    "Finalized at": reviewed_document.finalized_at,
                    "Artifact set fingerprint": (
                        artifact_set.artifact_set_fingerprint
                    ),
                }
            ]
        )
        st.table(
            [
                {
                    "Artifact": artifact.filename,
                    "Bytes": len(artifact.content),
                    "SHA-256": artifact.byte_fingerprint,
                }
                for artifact in artifact_set.artifacts
            ]
        )

    report_artifact = next(
        (
            artifact
            for artifact in artifact_set.artifacts
            if artifact.filename == "reviewed_report.md"
        ),
        None,
    )

    if report_artifact is None:
        st.error(
            "The exact finalized artifact set does not contain "
            "reviewed_report.md."
        )
        return

    try:
        report_markdown = report_artifact.content.decode("utf-8")
    except UnicodeDecodeError:
        st.error("reviewed_report.md is not valid UTF-8.")
        return

    st.markdown("**Reviewed result**")
    st.markdown(report_markdown)

    st.subheader("Reopen review")
    st.info(
        "Reopening creates a new draft successor. The finalized predecessor "
        "and its reviewed artifact set remain immutable."
    )

    reopen_reason = _optional_text(
        st.text_input(
            "Reason for reopening",
            value="",
            key=(
                "human_review_finalization.reopen_reason."
                f"{workspace_view.version.review_document_version_id}"
            ),
            help="Required and persisted on the new draft successor.",
        )
    )

    reopen_confirmation = st.checkbox(
        "Create a new draft successor and keep this finalized version immutable.",
        value=False,
        key=(
            "human_review_finalization.reopen_exact."
            f"{workspace_view.version.review_document_version_id}"
        ),
    )

    if st.button(
        "Reopen as new draft",
        key=(
            "human_review_finalization.reopen."
            f"{workspace_view.version.review_document_version_id}"
        ),
        type="primary",
    ):
        if not _reviewer_ready(st, reviewer_identity):
            return

        if reopen_reason is None:
            st.error("A reopen reason is required.")
            return

        if not reopen_confirmation:
            st.error("Reopening must be explicitly confirmed.")
            return

        try:
            bundle = service.reopen_review_version(
                project_id,
                workspace_view.document.review_document_id,
                workspace_view.version.review_document_version_id,
                reopen_reason=reopen_reason,
                actor_identity=reviewer_identity,
            )
        except ReviewWorkspaceError:
            st.error(
                "Reopening was blocked by validation, integrity, "
                "history or recovery checks."
            )
            return
        except Exception:
            st.error(
                "Reopening failed. "
                "No successor Review Version was inferred."
            )
            return

        if technical:
            st.success(
                "Created draft successor "
                f"{bundle.version.review_document_version_id} with "
                f"{bundle.initial_revision.review_revision_id}; "
                f"{len(bundle.review_item_id_mapping)} Review Item "
                "lineage mapping(s) were persisted."
            )
        else:
            st.success(
                "A new draft review version was created. "
                "The finalized predecessor remains unchanged."
            )
        _rerun(st)


def _decision_label(value: str) -> str:
    labels = {
        "confirm": "Confirm review complete",
        "request_changes": "Request changes",
        "reject": "Reject reviewed version",
    }
    return labels.get(value, value)


def _reviewer_ready(
    st: Any,
    reviewer_identity: str,
) -> bool:
    if (
        not isinstance(reviewer_identity, str)
        or not reviewer_identity.strip()
    ):
        st.error(
            "Reviewer identity is required before recording "
            "a Human Review Decision."
        )
        return False

    return True


def _optional_text(
    value: object,
) -> str | None:
    if not isinstance(value, str):
        return None

    selected = value.strip()
    return selected or None


def _rerun(
    st: Any,
) -> None:
    rerun = getattr(
        st,
        "rerun",
        None,
    )
    if callable(rerun):
        rerun()
