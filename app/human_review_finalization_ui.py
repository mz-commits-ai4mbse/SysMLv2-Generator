"""Finalization UI for G6 Human Review & Approval."""

from __future__ import annotations

from typing import Any

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

    st.table(
        [
            {
                "Review Revision": assessment.review_revision_id,
                "Eligible": preview.eligible_for_confirmation,
                "Blocking findings": len(
                    assessment.blocking_issue_codes
                ),
                "Latest exact HRD": (
                    preview.latest_exact_decision_id
                    or "None"
                ),
                "Latest exact decision": (
                    preview.latest_exact_decision
                    or "None"
                ),
                "Exact confirmation": (
                    preview.exact_confirmation_decision_id
                    or "None"
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
        st.warning(
            "Finalization is currently blocked."
        )
        st.table(
            [
                {"Blocking finding": code}
                for code in assessment.blocking_issue_codes
            ]
        )
    else:
        st.success(
            "The exact current Review Revision has no blocking "
            "finalization findings."
        )

    st.caption(
        "Validation fingerprint: "
        f"{assessment.validation_fingerprint}"
    )

    decision_options = (
        (
            "confirm",
            "request_changes",
            "reject",
        )
        if preview.eligible_for_confirmation
        else (
            "request_changes",
            "reject",
        )
    )

    decision = st.selectbox(
        "Human Review Decision",
        options=decision_options,
        index=0,
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
                "Required for request_changes and reject. "
                "Optional for confirm."
            ),
        )
    )

    explicit_confirmation = True

    if decision == "confirm":
        explicit_confirmation = st.checkbox(
            (
                "I completed the detailed review and confirm this exact "
                "Review Version and validation fingerprint"
            ),
            value=False,
            key=(
                "human_review_finalization.confirm_exact."
                f"{workspace_view.version.review_document_version_id}"
            ),
        )

    if st.button(
        "Record Human Review Decision",
        key=(
            "human_review_finalization.record."
            f"{workspace_view.version.review_document_version_id}"
        ),
    ):
        if not _reviewer_ready(
            st,
            reviewer_identity,
        ):
            return

        if decision != "confirm" and rationale is None:
            st.error(
                f"{decision} requires a reviewer rationale."
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

        st.success(
            "Human Review Decision persisted: "
            f"{result.human_review_decision_id}."
        )
        _rerun(st)
        return

    if not preview.has_exact_confirmation:
        st.info(
            "Finalization requires a persisted exact confirm decision "
            "for the current validation fingerprint."
        )
        return

    st.success(
        "An exact persisted detailed-review confirmation is available."
    )

    finalize_confirmation = st.checkbox(
        (
            "Finalize this exact confirmed Review Version and publish "
            "the immutable three-artifact set"
        ),
        value=False,
        key=(
            "human_review_finalization.finalize_exact."
            f"{workspace_view.version.review_document_version_id}"
        ),
    )

    if st.button(
        "Finalize Review Version",
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

        st.success(
            "Review Version finalized with "
            f"{result.finalization_decision_id}. "
            "The immutable Finalized Artifact Set was published."
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
        "This Review Version is finalized and immutable."
    )
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
        report_markdown = report_artifact.content.decode(
            "utf-8"
        )
    except UnicodeDecodeError:
        st.error(
            "reviewed_report.md is not valid UTF-8."
        )
        return

    st.caption("reviewed_report.md")
    st.markdown(report_markdown)

    st.subheader("Reopen finalized Review Version")
    st.info(
        "Reopening never modifies the finalized predecessor or its "
        "artifact set. It creates a new draft successor with fresh "
        "Review Version, Revision and Review Item identities."
    )

    reopen_reason = _optional_text(
        st.text_input(
            "Reopen reason",
            value="",
            key=(
                "human_review_finalization.reopen_reason."
                f"{workspace_view.version.review_document_version_id}"
            ),
            help=(
                "Required and persisted on the new draft successor."
            ),
        )
    )

    reopen_confirmation = st.checkbox(
        (
            "I confirm creation of a new draft successor while keeping "
            "the finalized predecessor immutable"
        ),
        value=False,
        key=(
            "human_review_finalization.reopen_exact."
            f"{workspace_view.version.review_document_version_id}"
        ),
    )

    if st.button(
        "Reopen as new draft version",
        key=(
            "human_review_finalization.reopen."
            f"{workspace_view.version.review_document_version_id}"
        ),
        type="primary",
    ):
        if not _reviewer_ready(
            st,
            reviewer_identity,
        ):
            return

        if reopen_reason is None:
            st.error(
                "A reopen reason is required."
            )
            return

        if not reopen_confirmation:
            st.error(
                "Reopening must be explicitly confirmed."
            )
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

        st.success(
            "Created draft successor "
            f"{bundle.version.review_document_version_id} with "
            f"{bundle.initial_revision.review_revision_id}; "
            f"{len(bundle.review_item_id_mapping)} Review Item "
            "lineage mapping(s) were persisted."
        )
        _rerun(st)


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
