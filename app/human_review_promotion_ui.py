"""Approved Input promotion, authority and lifecycle UI for G6."""

from __future__ import annotations

from typing import Any

from app.presentation_preferences import technical_details_enabled
from modules.review_workspace.errors import ReviewWorkspaceError


def render_approved_input_promotion_ui(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
) -> None:
    """Render focused Approved Input promotion over exact persisted authority."""

    if workspace_view.version.version_state != "finalized":
        return

    technical = technical_details_enabled(
        getattr(st, "session_state", {})
    )
    st.subheader("Approved Input")

    try:
        assessment = service.promotion_preview(
            project_id,
            workspace_view.document.review_document_id,
            workspace_view.version.review_document_version_id,
        )
        traceability = service.approved_input_traceability(
            project_id,
            workspace_view.document.review_document_id,
        )
    except ReviewWorkspaceError:
        st.error(
            "Approved Input authority is unavailable because validation, "
            "integrity or repository checks failed."
        )
        return
    except Exception:
        st.error(
            "Approved Input authority is unavailable. "
            "No promotion or lifecycle state was inferred."
        )
        return

    _render_promotion_assessment(
        st,
        assessment,
        technical=technical,
    )

    if assessment.eligible_for_promotion:
        st.success(
            f"{len(assessment.promotable_item_ids)} finalized Review Item(s) "
            "are ready to become Approved Input."
        )
        confirmation = st.checkbox(
            "Promote every currently eligible finalized Review Item.",
            value=False,
            key=(
                "human_review_promotion.confirm."
                f"{workspace_view.version.review_document_version_id}"
            ),
        )

        if st.button(
            "Promote to Approved Input",
            key=(
                "human_review_promotion.promote."
                f"{workspace_view.version.review_document_version_id}"
            ),
            type="primary",
        ):
            if not confirmation:
                st.error(
                    "Approved Input promotion must be explicitly confirmed."
                )
            else:
                try:
                    result = service.promote_review_version(
                        project_id,
                        workspace_view.document.review_document_id,
                        workspace_view.version.review_document_version_id,
                    )
                except ReviewWorkspaceError:
                    st.error(
                        "Approved Input promotion was blocked by validation, "
                        "integrity or stale-authority checks."
                    )
                except Exception:
                    st.error(
                        "Approved Input promotion did not complete. "
                        "No successful publication state was inferred."
                    )
                else:
                    st.success(
                        "Approved Input promotion completed. "
                        "Authority was reloaded from immutable evidence."
                    )
                    _render_promotion_result(
                        st,
                        result,
                        technical=technical,
                    )
                    traceability = result.traceability
    else:
        st.warning(
            "Approved Input promotion is currently blocked."
        )

    _render_authority_traceability(
        st,
        traceability,
        technical=technical,
    )


def _render_promotion_assessment(
    st: Any,
    assessment,
    *,
    technical: bool,
) -> None:
    st.table(
        [
            {
                "Status": (
                    "Ready for promotion"
                    if assessment.eligible_for_promotion
                    else "Promotion blocked"
                ),
                "Eligible items": len(
                    assessment.promotable_item_ids
                ),
                "Blocking findings": len(
                    assessment.blocking_issue_codes
                ),
            }
        ]
    )

    if not technical:
        return

    st.table(
        [
            {
                "Finalized Review Version": (
                    assessment.review_document_version_id
                ),
                "Finalized Revision": assessment.review_revision_id,
                "Eligible": assessment.eligible_for_promotion,
                "Promotable Items": len(
                    assessment.promotable_item_ids
                ),
                "Finalization Decision": (
                    assessment.finalization_decision_id
                ),
                "Artifact Set fingerprint": (
                    assessment.finalized_artifact_set_fingerprint
                ),
            }
        ]
    )

    if assessment.item_assessments:
        st.table(
            [
                {
                    "Review Item": item.review_item_id,
                    "Kind": item.review_item_kind,
                    "Outcome": item.effective_review_outcome,
                    "Eligible": item.eligible_for_promotion,
                    "Approved Input kind": (
                        item.approved_input_kind
                        or "Not promotable"
                    ),
                    "Reason codes": (
                        ", ".join(item.reason_codes)
                        or "None"
                    ),
                    "Review Item fingerprint": (
                        item.review_item_fingerprint
                    ),
                }
                for item in assessment.item_assessments
            ]
        )

    if assessment.blocking_issue_codes:
        st.table(
            [
                {"Promotion blocking finding": code}
                for code in assessment.blocking_issue_codes
            ]
        )


def _render_promotion_result(
    st: Any,
    result,
    *,
    technical: bool,
) -> None:
    if not technical:
        st.table(
            [
                {
                    "Created": len(result.created_approved_input_ids),
                    "Reused": len(result.reused_approved_input_ids),
                    "Skipped": len(result.skipped_review_item_ids),
                    "Lifecycle events": len(result.lifecycle_event_ids),
                }
            ]
        )
        return

    rows = []

    for approved_input_id in result.created_approved_input_ids:
        rows.append(
            {
                "Result": "Created Approved Input",
                "Identity": approved_input_id,
            }
        )

    for approved_input_id in result.reused_approved_input_ids:
        rows.append(
            {
                "Result": "Reused Approved Input",
                "Identity": approved_input_id,
            }
        )

    for review_item_id in result.skipped_review_item_ids:
        rows.append(
            {
                "Result": "Skipped Review Item",
                "Identity": review_item_id,
            }
        )

    for event_id in result.lifecycle_event_ids:
        rows.append(
            {
                "Result": "Lifecycle Event",
                "Identity": event_id,
            }
        )

    if rows:
        st.table(rows)
    else:
        st.info(
            "Promotion completed without creating, reusing, skipping "
            "or reconciling additional lifecycle records."
        )


def _render_authority_traceability(
    st: Any,
    traceability,
    *,
    technical: bool,
) -> None:
    st.subheader("Approved engineering input")

    active = tuple(
        item
        for item in traceability
        if item.is_active
    )

    if not traceability:
        st.info(
            "No Approved Input is currently associated with this Review."
        )
        return

    if active:
        st.success(
            f"{len(active)} active Approved Input item(s) are available "
            "for downstream model proposal work."
        )
        st.table(
            [
                {
                    "Title": item.canonical_title,
                    "Kind": item.approved_input_kind,
                    "Authority": item.authority_state,
                }
                for item in active
            ]
        )
    else:
        st.info(
            "No active Approved Input remains for this Review."
        )

    if not technical:
        return

    st.caption(
        "Phase H authoritative inputs: "
        + (
            ", ".join(
                item.approved_input_id
                for item in active
            )
            if active
            else "None"
        )
    )

    st.table(
        [
            {
                "Approved Input": item.approved_input_id,
                "Authority": item.authority_state,
                "Kind": item.approved_input_kind,
                "Subject": item.stable_subject_key,
                "Title": item.canonical_title,
                "Review Version": (
                    item.review_document_version_id
                ),
                "Review Revision": item.review_revision_id,
                "Review Item": item.review_item_id,
                "Finalization Decision": (
                    item.finalization_decision_id
                ),
                "Source": item.source_id,
                "Processing Run": item.processing_run_id,
                "Attempt": item.attempt_id,
                "Primary Artifact": item.primary_artifact_id,
                "Created": item.created_at,
            }
            for item in traceability
        ]
    )

    st.caption("Manifest lineage and fingerprints")
    st.table(
        [
            {
                "Approved Input": item.approved_input_id,
                "Review Item fingerprint": (
                    item.review_item_fingerprint
                ),
                "Artifact Set fingerprint": (
                    item.finalized_artifact_set_fingerprint
                ),
                "Finalization Decision fingerprint": (
                    item.finalization_decision_fingerprint
                ),
                "Validation fingerprint": (
                    item.finalization_validation_fingerprint
                ),
                "Manifest fingerprint": (
                    item.manifest_content_fingerprint
                ),
                "Latest Event fingerprint": (
                    item.latest_event_fingerprint
                    or "None"
                ),
                "Supporting Artifacts": (
                    ", ".join(item.supporting_artifact_ids)
                    or "None"
                ),
                "Proposal References": (
                    ", ".join(item.proposal_references)
                    or "None"
                ),
            }
            for item in traceability
        ]
    )

    events = tuple(
        event
        for item in traceability
        for event in item.lifecycle_events
    )

    st.caption("Immutable Approved Input lifecycle events")

    if not events:
        st.info(
            "No Approved Input lifecycle events are recorded for "
            "this Review Document."
        )
        return

    st.table(
        [
            {
                "Event": event.approved_input_event_id,
                "Approved Input": event.approved_input_id,
                "Transition": (
                    f"{event.previous_authority_state} → "
                    f"{event.next_authority_state}"
                ),
                "Type": event.event_type,
                "Reason": event.reason_code,
                "Rationale": event.rationale or "",
                "Actor": event.actor_identity,
                "Successor": (
                    event.successor_approved_input_id
                    or ""
                ),
                "Causal Review Version": (
                    event.causal_review_document_version_id
                    or ""
                ),
                "Causal Review Revision": (
                    event.causal_review_revision_id
                    or ""
                ),
                "Causal Finalization Decision": (
                    event.causal_finalization_decision_id
                    or ""
                ),
                "Occurred": event.occurred_at,
                "Event fingerprint": event.event_fingerprint,
            }
            for event in events
        ]
    )
