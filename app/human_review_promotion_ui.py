"""Approved Input promotion, authority and lifecycle UI for G6."""

from __future__ import annotations

from typing import Any

from modules.review_workspace.errors import ReviewWorkspaceError


def render_approved_input_promotion_ui(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
) -> None:
    """Render fresh promotion eligibility and immutable AIN/AIE authority."""

    if workspace_view.version.version_state != "finalized":
        return

    st.subheader("Approved Input Promotion")

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
    )

    if assessment.eligible_for_promotion:
        confirmation = st.checkbox(
            (
                "Promote every currently eligible finalized Review Item "
                "using the exact current authority snapshot"
            ),
            value=False,
            key=(
                "human_review_promotion.confirm."
                f"{workspace_view.version.review_document_version_id}"
            ),
        )

        if st.button(
            "Promote to Approved Inputs",
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
                        "Approved Input promotion completed and authority "
                        "was reloaded from immutable manifests and events."
                    )
                    _render_promotion_result(
                        st,
                        result,
                    )
                    traceability = result.traceability
    else:
        st.warning(
            "Approved Input promotion is currently blocked."
        )

    _render_authority_traceability(
        st,
        traceability,
    )


def _render_promotion_assessment(
    st: Any,
    assessment,
) -> None:
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
                "Blocking findings": len(
                    assessment.blocking_issue_codes
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
) -> None:
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
) -> None:
    st.subheader("Approved Input Authority & Traceability")

    active_ids = tuple(
        item.approved_input_id
        for item in traceability
        if item.is_active
    )

    st.caption(
        "Phase H authoritative inputs: "
        + (
            ", ".join(active_ids)
            if active_ids
            else "None"
        )
    )

    if not traceability:
        st.info(
            "No Approved Input manifests are currently associated with "
            "this Review Document."
        )
        return

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
