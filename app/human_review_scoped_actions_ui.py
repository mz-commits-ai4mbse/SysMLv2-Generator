"""Scoped Review Action UI with exact materialization and impact preview."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from typing import Any

from modules.review_workspace.errors import ReviewWorkspaceError
from modules.review_workspace.scoped_workflow import (
    SCOPED_REVIEW_OUTCOMES,
    ReviewFilterSpec,
    ScopedReviewActionRequest,
)


_SESSION_PREVIEW_SIGNATURE_PREFIX = (
    "human_review_scoped.preview_signature."
)

_SCOPE_OPTIONS = (
    "document_default",
    "filtered_set",
    "explicit_selection",
)

_SCOPE_LABELS = {
    "document_default": "Complete document default",
    "filtered_set": "Current materialized filtered result",
    "explicit_selection": "Explicit manual selection",
}

_DIMENSION_OPTIONS = (
    "classification",
    "framework_assignment",
    "terminology_assignment",
    "source_assignment",
    "review_outcome",
)

_DIMENSION_LABELS = {
    "classification": "Classification",
    "framework_assignment": "Framework Assignment",
    "terminology_assignment": "Terminology Assignment",
    "source_assignment": "Source Assignment",
    "review_outcome": "Review Outcome",
}

_FILTER_WIDGETS = (
    (
        "review_status",
        "Review status",
        "review_status",
    ),
    (
        "review_item_kind",
        "Review Item kind",
        "review_item_kind",
    ),
    (
        "proposed_classification",
        "Proposed classification",
        "proposed_classifications",
    ),
    (
        "effective_classification",
        "Effective classification",
        "effective_classifications",
    ),
    (
        "proposed_framework_assignment",
        "Proposed Framework Assignment",
        "proposed_framework_assignments",
    ),
    (
        "effective_framework_assignment",
        "Effective Framework Assignment",
        "effective_framework_assignments",
    ),
    (
        "agent_identity",
        "Agent identity",
        "agent_identities",
    ),
    (
        "confidence",
        "Confidence",
        "confidence_levels",
    ),
    (
        "consensus_state",
        "Consensus state",
        "consensus_states",
    ),
    (
        "agent_disagreement",
        "Agent disagreement",
        "agent_disagreement_state",
    ),
    (
        "human_modification_state",
        "Human modification state",
        "human_modification_state",
    ),
    (
        "source_identity",
        "Source identity",
        "source_identities",
    ),
    (
        "evidence_sufficiency",
        "Evidence sufficiency",
        "evidence_sufficiency_state",
    ),
    (
        "relationship_validation_status",
        "Relationship validation status",
        "relationship_validation_status",
    ),
)


def render_scoped_review_actions_ui(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    reviewer_identity: str,
) -> None:
    """Render filter, preview and confirmed immutable scoped actions."""

    st.subheader("Scoped Review Actions")

    try:
        facts = service.review_filter_facts(
            project_id,
            workspace_view.document.review_document_id,
            workspace_view.version.review_document_version_id,
        )
    except ReviewWorkspaceError:
        st.error(
            "Scoped Review filters are unavailable because exact "
            "Review evidence or workspace integrity checks failed."
        )
        return
    except Exception:
        st.error(
            "Scoped Review filters are unavailable. "
            "No fallback target set was inferred."
        )
        return

    if not facts:
        st.info(
            "No filterable Review Items are available for scoped actions."
        )
        return

    document_id = (
        workspace_view.document.review_document_id
    )
    revision_id = (
        workspace_view.revision.review_revision_id
    )

    scope = st.selectbox(
        "Action scope",
        options=_SCOPE_OPTIONS,
        index=0,
        format_func=lambda value: _SCOPE_LABELS[value],
        key=f"human_review_scoped.scope.{document_id}",
    )

    filter_spec = None
    explicit_ids = ()

    if scope == "filtered_set":
        filter_spec = _render_filter_spec(
            st,
            facts=facts,
            document_id=document_id,
        )
    elif scope == "explicit_selection":
        explicit_ids = tuple(
            st.multiselect(
                "Review Items",
                options=tuple(
                    fact.review_item_id
                    for fact in facts
                ),
                default=(),
                key=(
                    "human_review_scoped.explicit_selection."
                    f"{document_id}"
                ),
            )
        )

    dimensions = (
        tuple(
            value
            for value in _DIMENSION_OPTIONS
            if value != "review_outcome"
        )
        if scope == "document_default"
        else _DIMENSION_OPTIONS
    )

    dimension = st.selectbox(
        "Decision dimension",
        options=dimensions,
        index=0,
        format_func=lambda value: _DIMENSION_LABELS[value],
        key=f"human_review_scoped.dimension.{document_id}",
    )

    selected_values = _render_selected_values(
        st,
        document_id=document_id,
        dimension=dimension,
    )

    rationale = _optional_text(
        st.text_input(
            "Scoped action rationale",
            value="",
            key=(
                "human_review_scoped.rationale."
                f"{document_id}"
            ),
            help=(
                "Required for rejection. It is also persisted "
                "for other scoped decisions when provided."
            ),
        )
    )

    request = ScopedReviewActionRequest(
        expected_revision_id=revision_id,
        action_scope=scope,
        decision_dimension=dimension,
        selected_values=selected_values,
        filter_spec=filter_spec,
        explicit_review_item_ids=explicit_ids,
        rationale=rationale,
    )

    signature = _request_signature(request)
    signature_key = (
        _SESSION_PREVIEW_SIGNATURE_PREFIX
        + document_id
    )

    if st.button(
        "Preview impact",
        key=f"human_review_scoped.preview.{document_id}",
    ):
        preview = _safe_preview(
            st,
            service=service,
            project_id=project_id,
            workspace_view=workspace_view,
            request=request,
        )
        if preview is not None:
            st.session_state[signature_key] = signature

    if (
        st.session_state.get(signature_key)
        != signature
    ):
        st.info(
            "Preview the current scoped action before applying it. "
            "Changing scope, filters, values or rationale requires "
            "a new preview."
        )
        return

    preview = _safe_preview(
        st,
        service=service,
        project_id=project_id,
        workspace_view=workspace_view,
        request=request,
    )
    if preview is None:
        st.session_state.pop(
            signature_key,
            None,
        )
        return

    _render_impact_preview(
        st,
        preview,
    )

    confirm_overwrite = False
    if preview.overwrite_count:
        st.warning(
            "Higher-precedence decisions are present. "
            "They remain excluded unless overwrite is explicitly confirmed."
        )
        confirm_overwrite = st.checkbox(
            (
                "Overwrite the listed higher-precedence decisions "
                "after reviewing the impact preview"
            ),
            value=False,
            key=(
                "human_review_scoped.confirm_overwrite."
                f"{document_id}.{revision_id}"
            ),
        )

    confirm_bulk_rejection = False
    if preview.requires_bulk_rejection_confirmation:
        st.warning(
            "This action rejects more than one materialized Review Item."
        )
        confirm_bulk_rejection = st.checkbox(
            (
                "I confirm rejection of the complete materialized "
                "target list shown above"
            ),
            value=False,
            key=(
                "human_review_scoped.confirm_bulk_rejection."
                f"{document_id}.{revision_id}"
            ),
        )

    final_request = replace(
        request,
        confirm_higher_precedence_overwrite=(
            confirm_overwrite
        ),
        confirm_bulk_rejection=(
            confirm_bulk_rejection
        ),
    )

    if confirm_overwrite:
        final_preview = _safe_preview(
            st,
            service=service,
            project_id=project_id,
            workspace_view=workspace_view,
            request=final_request,
        )
        if final_preview is None:
            return
        st.caption(
            "Confirmed overwrite impact"
        )
        _render_impact_counts(
            st,
            final_preview,
        )

    if st.button(
        "Apply scoped action",
        key=f"human_review_scoped.apply.{document_id}",
        type="primary",
    ):
        if not _reviewer_ready(
            st,
            reviewer_identity,
        ):
            return

        if (
            preview.requires_bulk_rejection_confirmation
            and not confirm_bulk_rejection
        ):
            st.error(
                "Bulk rejection requires explicit confirmation."
            )
            return

        if (
            dimension == "review_outcome"
            and selected_values == ("rejected",)
            and rationale is None
        ):
            st.error(
                "A rationale is required to reject Review Items."
            )
            return

        try:
            service.apply_scoped_action(
                project_id,
                workspace_view.document.review_document_id,
                workspace_view.version.review_document_version_id,
                request=final_request,
                actor_identity=reviewer_identity,
            )
        except ReviewWorkspaceError:
            st.error(
                "The scoped Review action was blocked by validation, "
                "integrity, stale-state or recovery checks."
            )
            return
        except Exception:
            st.error(
                "The scoped Review action failed. "
                "No successful state was inferred."
            )
            return

        st.session_state.pop(
            signature_key,
            None,
        )
        st.success(
            "Scoped Review Action persisted and applied in a new "
            "immutable Review Revision."
        )
        rerun = getattr(
            st,
            "rerun",
            None,
        )
        if callable(rerun):
            rerun()


def _render_filter_spec(
    st: Any,
    *,
    facts,
    document_id: str,
) -> ReviewFilterSpec:
    values = {}

    for field_name, label, fact_attribute in _FILTER_WIDGETS:
        options = _fact_options(
            facts,
            fact_attribute,
        )
        values[field_name] = tuple(
            st.multiselect(
                label,
                options=options,
                default=(),
                key=(
                    "human_review_scoped.filter."
                    f"{field_name}.{document_id}"
                ),
            )
        )

    return ReviewFilterSpec(
        **values
    )


def _fact_options(
    facts,
    attribute: str,
) -> tuple[str, ...]:
    result = set()

    for fact in facts:
        value = getattr(
            fact,
            attribute,
        )
        if isinstance(value, tuple):
            result.update(value)
        elif isinstance(value, str):
            result.add(value)

    return tuple(sorted(result))


def _render_selected_values(
    st: Any,
    *,
    document_id: str,
    dimension: str,
) -> tuple[str, ...]:
    prefix = (
        "human_review_scoped.values."
        f"{dimension}.{document_id}"
    )

    if dimension == "classification":
        field = st.selectbox(
            "Classification field",
            options=(
                "information_type",
                "modality",
                "epistemic_status",
            ),
            index=0,
            key=f"{prefix}.field",
        )
        operation = st.selectbox(
            "Classification operation",
            options=("set", "clear"),
            index=0,
            key=f"{prefix}.operation",
        )
        if operation == "clear":
            return (f"{field}=<none>",)

        value = st.text_input(
            "Classification value",
            value="",
            key=f"{prefix}.value",
        )
        selected = value.strip()
        return (
            (f"{field}={selected}",)
            if selected
            else ()
        )

    if dimension in {
        "framework_assignment",
        "terminology_assignment",
        "source_assignment",
    }:
        value = st.text_input(
            "Selected value(s), comma separated",
            value="",
            key=prefix,
        )
        return _csv_tuple(
            value
        )

    outcome_options = tuple(
        value
        for value in (
            "open",
            "deferred",
            "out_of_scope",
            "unresolved",
            "rejected",
        )
        if value in SCOPED_REVIEW_OUTCOMES
    )
    outcome = st.selectbox(
        "Review outcome",
        options=outcome_options,
        index=0,
        key=prefix,
    )
    return (outcome,)


def _safe_preview(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    request: ScopedReviewActionRequest,
):
    try:
        return service.preview_scoped_action(
            project_id,
            workspace_view.document.review_document_id,
            workspace_view.version.review_document_version_id,
            request=request,
        )
    except ReviewWorkspaceError:
        st.error(
            "Impact preview was blocked by validation, integrity "
            "or stale-state checks."
        )
    except Exception:
        st.error(
            "Impact preview failed. "
            "No target set or precedence result was inferred."
        )

    return None


def _render_impact_preview(
    st: Any,
    preview,
) -> None:
    st.caption(
        "Impact Preview"
    )
    _render_impact_counts(
        st,
        preview,
    )

    if preview.filter_definition is not None:
        st.caption(
            "Materialized filter: "
            f"{preview.filter_definition}"
        )

    st.table(
        [
            {
                "Review Item": reference.review_item_id,
                "Content fingerprint": (
                    reference.item_content_fingerprint
                ),
                "Higher precedence": (
                    "yes"
                    if reference.review_item_id
                    in preview.higher_precedence_review_item_ids
                    else "no"
                ),
                "Currently excluded": (
                    "yes"
                    if reference.review_item_id
                    in preview.excluded_review_item_ids
                    else "no"
                ),
            }
            for reference in preview.matched_items
        ]
    )


def _render_impact_counts(
    st: Any,
    preview,
) -> None:
    st.table(
        [
            {
                "Materialized": preview.matched_count,
                "Affected now": preview.affected_count,
                "Item overrides": preview.item_override_count,
                "Higher precedence": len(
                    preview.higher_precedence_review_item_ids
                ),
                "Excluded": preview.excluded_count,
                "Would overwrite after confirmation": (
                    preview.overwrite_count
                ),
            }
        ]
    )


def _request_signature(
    request: ScopedReviewActionRequest,
) -> str:
    filter_payload = None

    if request.filter_spec is not None:
        filter_payload = {
            field: list(
                getattr(
                    request.filter_spec,
                    field,
                )
            )
            for field in (
                "review_status",
                "review_item_kind",
                "proposed_classification",
                "effective_classification",
                "proposed_framework_assignment",
                "effective_framework_assignment",
                "agent_identity",
                "confidence",
                "consensus_state",
                "agent_disagreement",
                "human_modification_state",
                "source_identity",
                "evidence_sufficiency",
                "relationship_validation_status",
            )
        }

    payload = {
        "expected_revision_id": request.expected_revision_id,
        "action_scope": request.action_scope,
        "decision_dimension": request.decision_dimension,
        "selected_values": list(
            request.selected_values
        ),
        "filter_spec": filter_payload,
        "explicit_review_item_ids": list(
            request.explicit_review_item_ids
        ),
        "rationale": request.rationale,
    }

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def _reviewer_ready(
    st: Any,
    reviewer_identity: str,
) -> bool:
    if (
        not isinstance(
            reviewer_identity,
            str,
        )
        or not reviewer_identity.strip()
    ):
        st.error(
            "Reviewer identity is required before a Human Review "
            "write action."
        )
        return False

    return True


def _csv_tuple(
    value: object,
) -> tuple[str, ...]:
    if not isinstance(value, str):
        return ()

    result = tuple(
        part.strip()
        for part in value.split(",")
        if part.strip()
    )

    return tuple(
        dict.fromkeys(result)
    )


def _optional_text(
    value: object,
) -> str | None:
    if not isinstance(value, str):
        return None

    selected = value.strip()
    return selected or None
