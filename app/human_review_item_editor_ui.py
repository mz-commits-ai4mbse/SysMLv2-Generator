"""Review Item editor UI for G6 Human Review & Approval."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from modules.review_workspace.errors import ReviewWorkspaceError
from modules.review_workspace.workflow_editing import (
    ReviewItemEditRequest,
    proposal_selection_key,
)
from app.human_review_scoped_actions_ui import (
    render_scoped_review_actions_ui,
)

from modules.review_workspace.workflow_lineage import (
    ReviewMergeRequest,
    ReviewProposalActionRequest,
    ReviewSplitChildSpec,
    ReviewSplitRequest,
    evidence_selection_key,
)


_SECTION_OPTIONS = (
    "elements",
    "relationships",
    "open_questions",
    "rejected_content",
)

_SECTION_LABELS = {
    "elements": "Elements",
    "relationships": "Relationships",
    "open_questions": "Open Questions",
    "rejected_content": "Rejected Content",
}


def render_review_item_editor(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    reviewer_identity: str,
) -> None:
    """Render the draft Review Item editor over verified G6 commands."""

    revision = workspace_view.revision
    if workspace_view.version.version_state != "draft":
        st.info(
            "This Review Version is finalized and read-only. "
            "Reopen it before editing."
        )
        return

    render_scoped_review_actions_ui(
        st,
        service=service,
        project_id=project_id,
        workspace_view=workspace_view,
        reviewer_identity=reviewer_identity,
    )

    section = st.radio(
        "Review section",
        options=_SECTION_OPTIONS,
        index=0,
        format_func=lambda value: _SECTION_LABELS[value],
        horizontal=True,
        key=(
            "human_review_item_editor.section."
            f"{workspace_view.document.review_document_id}"
        ),
    )

    items = _items_for_section(
        revision.review_items,
        section,
    )

    if not items:
        st.info(
            f"No Review Items are currently shown in "
            f"{_SECTION_LABELS[section]}."
        )
        return

    for item in items:
        _render_item(
            st,
            service=service,
            project_id=project_id,
            workspace_view=workspace_view,
            item=item,
            reviewer_identity=reviewer_identity,
        )

    if section != "rejected_content":
        _render_merge_controls(
            st,
            service=service,
            project_id=project_id,
            workspace_view=workspace_view,
            items=items,
            reviewer_identity=reviewer_identity,
        )


def _items_for_section(
    review_items,
    section: str,
) -> tuple:
    if section == "rejected_content":
        return tuple(
            item
            for item in review_items
            if item.effective_review_outcome == "rejected"
        )

    return tuple(
        item
        for item in review_items
        if (
            item.section == section
            and item.effective_review_outcome != "rejected"
        )
    )


def _render_item(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    item,
    reviewer_identity: str,
) -> None:
    st.subheader(
        f"{item.review_item_id} · {item.current_content.title}"
    )
    st.caption(
        f"Kind: {item.review_item_kind} · "
        f"Outcome: {item.effective_review_outcome} · "
        f"Lineage: {item.lineage_operation}"
    )
    st.markdown(item.current_content.primary_text)

    if item.current_content.description:
        st.caption(item.current_content.description)

    _render_effective_dimensions(st, item)
    _render_evidence(st, item)

    details = ()
    if item.proposal_references:
        try:
            details = service.proposal_details(
                project_id,
                workspace_view.document.review_document_id,
                workspace_view.version.review_document_version_id,
                item.review_item_id,
            )
        except ReviewWorkspaceError:
            st.error(
                "Exact Agent proposal content could not be loaded "
                "for this Review Item."
            )
        except Exception:
            st.error(
                "Agent proposal content is unavailable. "
                "No fallback proposal state was inferred."
            )

    for detail in details:
        _render_proposal(
            st,
            service=service,
            project_id=project_id,
            workspace_view=workspace_view,
            item=item,
            detail=detail,
            reviewer_identity=reviewer_identity,
        )

    _render_item_outcome_controls(
        st,
        service=service,
        project_id=project_id,
        workspace_view=workspace_view,
        item=item,
        reviewer_identity=reviewer_identity,
    )

    _render_split_controls(
        st,
        service=service,
        project_id=project_id,
        workspace_view=workspace_view,
        item=item,
        reviewer_identity=reviewer_identity,
    )


def _render_effective_dimensions(
    st: Any,
    item,
) -> None:
    if not item.dimension_selections:
        return

    st.table(
        [
            {
                "Dimension": selection.dimension,
                "Value": ", ".join(selection.selected_values),
                "Origin": selection.value_origin,
                "Sources": ", ".join(
                    selection.source_reference_ids
                ),
            }
            for selection in item.dimension_selections
        ]
    )


def _render_evidence(
    st: Any,
    item,
) -> None:
    rows = []

    for reference in item.source_evidence_references:
        rows.append(
            {
                "Type": "Source",
                "Role": reference.evidence_role,
                "Artifact": (
                    reference.artifact_reference.artifact_id
                ),
                "Locator": reference.evidence_locator,
                "Fingerprint": (
                    reference.evidence_content_fingerprint
                ),
            }
        )

    for reference in item.consensus_evidence_references:
        rows.append(
            {
                "Type": "Consensus",
                "Role": reference.evidence_role,
                "Artifact": (
                    reference.artifact_reference.artifact_id
                ),
                "Locator": reference.evidence_locator,
                "Fingerprint": (
                    reference.evidence_content_fingerprint
                ),
            }
        )

    if rows:
        st.table(rows)


def _render_proposal(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    item,
    detail,
    reviewer_identity: str,
) -> None:
    st.caption(
        f"Proposal {detail.proposal_id} · "
        f"{detail.agent_id} / {detail.persona_id}"
    )
    st.markdown(detail.proposed_primary_text)

    st.table(
        [
            {
                "Classification": detail.proposed_information_type,
                "Confidence": detail.confidence,
                "Generation readiness": (
                    detail.generation_readiness
                    or "Not provided"
                ),
                "Framework assignment": (
                    ", ".join(
                        detail.framework_assignment_values
                    )
                    or "Not provided by P9"
                ),
                "Review state": detail.review_state,
            }
        ]
    )

    if detail.source_assignments:
        st.table(
            [
                {
                    "Source": assignment.source_info_id,
                    "Assignment": assignment.assignment_type,
                    "Confidence": assignment.confidence,
                    "Statement": assignment.source_statement,
                }
                for assignment in detail.source_assignments
            ]
        )

    rationale_key = (
        "human_review_item_editor.proposal_rationale."
        f"{item.review_item_id}.{detail.proposal_key}"
    )
    rationale = st.text_input(
        "Proposal rationale",
        value="",
        key=rationale_key,
        help=(
            "Required when rejecting a proposal and for "
            "relationship acceptance."
        ),
    )
    rationale_value = _optional_text(rationale)

    if st.button(
        f"Accept proposal · {detail.proposal_id}",
        key=(
            "human_review_item_editor.accept."
            f"{item.review_item_id}.{detail.proposal_key}"
        ),
    ):
        if not _reviewer_ready(st, reviewer_identity):
            return
        _execute(
            st,
            lambda: service.accept_proposal(
                project_id,
                workspace_view.document.review_document_id,
                workspace_view.version.review_document_version_id,
                item.review_item_id,
                request=ReviewProposalActionRequest(
                    expected_revision_id=(
                        workspace_view.revision.review_revision_id
                    ),
                    expected_item_content_fingerprint=(
                        item.item_content_fingerprint
                    ),
                    proposal_key=detail.proposal_key,
                    rationale=rationale_value,
                ),
                actor_identity=reviewer_identity,
            ),
            "Agent proposal accepted.",
        )

    _render_edit_and_accept(
        st,
        service=service,
        project_id=project_id,
        workspace_view=workspace_view,
        item=item,
        detail=detail,
        reviewer_identity=reviewer_identity,
        rationale=rationale_value,
    )

    if st.button(
        f"Reject proposal · {detail.proposal_id}",
        key=(
            "human_review_item_editor.reject_proposal."
            f"{item.review_item_id}.{detail.proposal_key}"
        ),
    ):
        if not _reviewer_ready(st, reviewer_identity):
            return
        if rationale_value is None:
            st.error(
                "A rationale is required to reject an Agent proposal."
            )
            return
        _execute(
            st,
            lambda: service.reject_proposal(
                project_id,
                workspace_view.document.review_document_id,
                workspace_view.version.review_document_version_id,
                item.review_item_id,
                request=ReviewProposalActionRequest(
                    expected_revision_id=(
                        workspace_view.revision.review_revision_id
                    ),
                    expected_item_content_fingerprint=(
                        item.item_content_fingerprint
                    ),
                    proposal_key=detail.proposal_key,
                    rationale=rationale_value,
                ),
                actor_identity=reviewer_identity,
            ),
            "Agent proposal rejected. The Review Item remains independent.",
        )


def _render_edit_and_accept(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    item,
    detail,
    reviewer_identity: str,
    rationale: str | None,
) -> None:
    prefix = (
        "human_review_item_editor.edit."
        f"{item.review_item_id}.{detail.proposal_key}"
    )

    title = st.text_input(
        "Edited title",
        value=detail.proposed_title,
        key=f"{prefix}.title",
    )
    statement = st.text_area(
        "Edited engineering statement",
        value=detail.proposed_primary_text,
        key=f"{prefix}.statement",
    )
    description = st.text_area(
        "Edited description",
        value=detail.proposed_description,
        key=f"{prefix}.description",
    )
    information_type = st.text_input(
        "Information type",
        value=detail.proposed_information_type,
        key=f"{prefix}.information_type",
    )
    framework = st.text_input(
        "Framework assignment(s), comma separated",
        value=", ".join(
            detail.framework_assignment_values
        ),
        key=f"{prefix}.framework",
    )
    terminology = st.text_input(
        "Terminology assignment(s), comma separated",
        value="",
        key=f"{prefix}.terminology",
    )
    source_assignments = st.text_input(
        "Source assignment(s), comma separated",
        value=", ".join(
            assignment.source_info_id
            for assignment in detail.source_assignments
        ),
        key=f"{prefix}.source",
    )

    if st.button(
        f"Edit and accept · {detail.proposal_id}",
        key=f"{prefix}.submit",
        type="primary",
    ):
        if not _reviewer_ready(st, reviewer_identity):
            return

        edited_content = replace(
            item.current_content,
            title=title.strip(),
            primary_text=statement.strip(),
            description=_optional_text(description),
            information_type=_optional_text(
                information_type
            ),
            human_rationale=rationale,
        )

        request = ReviewItemEditRequest(
            expected_revision_id=(
                workspace_view.revision.review_revision_id
            ),
            expected_item_content_fingerprint=(
                item.item_content_fingerprint
            ),
            updated_content=edited_content,
            selected_proposal_keys=(detail.proposal_key,),
            review_outcome="accepted_with_modification",
            framework_assignment_values=_csv_tuple(framework),
            terminology_assignment_values=_csv_tuple(terminology),
            source_assignment_values=_csv_tuple(
                source_assignments
            ),
            rationale=rationale,
        )

        _execute(
            st,
            lambda: service.save_item_review(
                project_id,
                workspace_view.document.review_document_id,
                workspace_view.version.review_document_version_id,
                item.review_item_id,
                request=request,
                actor_identity=reviewer_identity,
            ),
            "Edited Review Item accepted in a new immutable Revision.",
        )


def _render_item_outcome_controls(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    item,
    reviewer_identity: str,
) -> None:
    rationale = st.text_input(
        "Item rationale",
        value="",
        key=(
            "human_review_item_editor.item_rationale."
            f"{item.review_item_id}"
        ),
        help=(
            "Required for rejecting the complete Review Item."
        ),
    )
    rationale_value = _optional_text(rationale)

    actions = (
        (
            "Reject all proposals / Review Item",
            "rejected",
            True,
        ),
        ("Defer Review Item", "deferred", False),
        ("Mark Review Item out of scope", "out_of_scope", False),
    )

    for label, outcome, requires_rationale in actions:
        if st.button(
            label,
            key=(
                "human_review_item_editor.item_outcome."
                f"{item.review_item_id}.{outcome}"
            ),
        ):
            if not _reviewer_ready(st, reviewer_identity):
                return
            if requires_rationale and rationale_value is None:
                st.error(
                    "A rationale is required to reject the complete "
                    "Review Item."
                )
                return

            request = ReviewItemEditRequest(
                expected_revision_id=(
                    workspace_view.revision.review_revision_id
                ),
                expected_item_content_fingerprint=(
                    item.item_content_fingerprint
                ),
                updated_content=item.current_content,
                selected_proposal_keys=(),
                review_outcome=outcome,
                rationale=rationale_value,
            )

            _execute(
                st,
                lambda request=request: service.save_item_review(
                    project_id,
                    workspace_view.document.review_document_id,
                    workspace_view.version.review_document_version_id,
                    item.review_item_id,
                    request=request,
                    actor_identity=reviewer_identity,
                ),
                f"Review Item outcome set to {outcome}.",
            )


def _render_split_controls(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    item,
    reviewer_identity: str,
) -> None:
    child_count = st.selectbox(
        "Split child count",
        options=(2, 3, 4),
        index=0,
        key=(
            "human_review_item_editor.split_count."
            f"{item.review_item_id}"
        ),
    )

    child_specs = []
    child_labels = tuple(
        f"Child {index}"
        for index in range(1, child_count + 1)
    )

    child_inputs = []
    for index in range(1, child_count + 1):
        prefix = (
            "human_review_item_editor.split."
            f"{item.review_item_id}.{index}"
        )
        child_inputs.append(
            (
                st.text_input(
                    f"Child {index} stable subject key",
                    value=(
                        f"{item.stable_subject_key}:split-{index}"
                    ),
                    key=f"{prefix}.subject",
                ),
                st.text_input(
                    f"Child {index} title",
                    value=(
                        f"{item.current_content.title} {index}"
                    ),
                    key=f"{prefix}.title",
                ),
                st.text_area(
                    f"Child {index} engineering statement",
                    value=item.current_content.primary_text,
                    key=f"{prefix}.statement",
                ),
            )
        )

    proposal_assignments = {
        proposal_selection_key(reference): st.selectbox(
            f"Assign proposal {reference.proposal_id}",
            options=child_labels,
            index=0,
            key=(
                "human_review_item_editor.split_proposal."
                f"{item.review_item_id}."
                f"{proposal_selection_key(reference)}"
            ),
        )
        for reference in item.proposal_references
    }
    source_assignments = {
        evidence_selection_key(reference): st.selectbox(
            f"Assign source evidence {reference.evidence_locator}",
            options=child_labels,
            index=0,
            key=(
                "human_review_item_editor.split_source."
                f"{item.review_item_id}."
                f"{evidence_selection_key(reference)}"
            ),
        )
        for reference in item.source_evidence_references
    }
    consensus_assignments = {
        evidence_selection_key(reference): st.selectbox(
            f"Assign consensus evidence {reference.evidence_locator}",
            options=child_labels,
            index=0,
            key=(
                "human_review_item_editor.split_consensus."
                f"{item.review_item_id}."
                f"{evidence_selection_key(reference)}"
            ),
        )
        for reference in item.consensus_evidence_references
    }

    split_rationale = st.text_input(
        "Split rationale",
        value="",
        key=(
            "human_review_item_editor.split_rationale."
            f"{item.review_item_id}"
        ),
    )
    split_rationale_value = _optional_text(
        split_rationale
    )

    for index, (
        subject,
        title,
        statement,
    ) in enumerate(child_inputs, start=1):
        label = f"Child {index}"
        child_specs.append(
            ReviewSplitChildSpec(
                stable_subject_key=subject.strip(),
                current_content=replace(
                    item.current_content,
                    title=title.strip(),
                    primary_text=statement.strip(),
                    human_rationale=(
                        split_rationale_value
                    ),
                ),
                proposal_keys=tuple(
                    key
                    for key, assigned
                    in proposal_assignments.items()
                    if assigned == label
                ),
                source_evidence_keys=tuple(
                    key
                    for key, assigned
                    in source_assignments.items()
                    if assigned == label
                ),
                consensus_evidence_keys=tuple(
                    key
                    for key, assigned
                    in consensus_assignments.items()
                    if assigned == label
                ),
            )
        )

    if st.button(
        "Split Review Item",
        key=(
            "human_review_item_editor.split_submit."
            f"{item.review_item_id}"
        ),
    ):
        if not _reviewer_ready(st, reviewer_identity):
            return

        request = ReviewSplitRequest(
            expected_revision_id=(
                workspace_view.revision.review_revision_id
            ),
            expected_item_content_fingerprint=(
                item.item_content_fingerprint
            ),
            children=tuple(child_specs),
            rationale=split_rationale_value,
        )

        _execute(
            st,
            lambda: service.split_review_item(
                project_id,
                workspace_view.document.review_document_id,
                workspace_view.version.review_document_version_id,
                item.review_item_id,
                request=request,
                actor_identity=reviewer_identity,
            ),
            "Review Item split into lineage-preserving children.",
        )


def _render_merge_controls(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    items: tuple,
    reviewer_identity: str,
) -> None:
    if len(items) < 2:
        return

    st.subheader("Merge selected Review Items")
    by_id = {
        item.review_item_id: item
        for item in items
    }

    selected_ids = tuple(
        st.multiselect(
            "Review Items to merge",
            options=tuple(by_id),
            default=(),
            key=(
                "human_review_item_editor.merge_selection."
                f"{workspace_view.revision.review_revision_id}"
                f".{items[0].section}"
            ),
        )
    )

    if selected_ids:
        first = by_id[selected_ids[0]]
    else:
        first = items[0]

    subject = st.text_input(
        "Merged stable subject key",
        value=f"{first.stable_subject_key}:merged",
        key=(
            "human_review_item_editor.merge_subject."
            f"{items[0].section}"
        ),
    )
    title = st.text_input(
        "Merged title",
        value=first.current_content.title,
        key=(
            "human_review_item_editor.merge_title."
            f"{items[0].section}"
        ),
    )
    statement = st.text_area(
        "Merged engineering statement",
        value=first.current_content.primary_text,
        key=(
            "human_review_item_editor.merge_statement."
            f"{items[0].section}"
        ),
    )
    rationale = st.text_input(
        "Merge rationale",
        value="",
        key=(
            "human_review_item_editor.merge_rationale."
            f"{items[0].section}"
        ),
    )
    rationale_value = _optional_text(rationale)

    if st.button(
        "Merge selected Review Items",
        key=(
            "human_review_item_editor.merge_submit."
            f"{items[0].section}"
        ),
    ):
        if not _reviewer_ready(st, reviewer_identity):
            return
        if len(selected_ids) < 2:
            st.error(
                "Select at least two Review Items to merge."
            )
            return

        selected_items = tuple(
            by_id[item_id]
            for item_id in selected_ids
        )

        request = ReviewMergeRequest(
            expected_revision_id=(
                workspace_view.revision.review_revision_id
            ),
            expected_item_fingerprints=tuple(
                (
                    item.review_item_id,
                    item.item_content_fingerprint,
                )
                for item in selected_items
            ),
            stable_subject_key=subject.strip(),
            current_content=replace(
                selected_items[0].current_content,
                title=title.strip(),
                primary_text=statement.strip(),
                human_rationale=rationale_value,
            ),
            rationale=rationale_value,
        )

        _execute(
            st,
            lambda: service.merge_review_items(
                project_id,
                workspace_view.document.review_document_id,
                workspace_view.version.review_document_version_id,
                request=request,
                actor_identity=reviewer_identity,
            ),
            "Review Items merged into a new lineage identity.",
        )


def _reviewer_ready(
    st: Any,
    reviewer_identity: str,
) -> bool:
    if (
        not isinstance(reviewer_identity, str)
        or not reviewer_identity.strip()
    ):
        st.error(
            "Reviewer identity is required before a Human Review "
            "write action."
        )
        return False
    return True


def _execute(
    st: Any,
    command,
    success_message: str,
) -> None:
    try:
        command()
    except ReviewWorkspaceError:
        st.error(
            "The Human Review write action was blocked by validation, "
            "integrity or stale-state checks."
        )
        return
    except Exception:
        st.error(
            "The Human Review write action failed. "
            "No successful state was inferred."
        )
        return

    st.success(success_message)
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()


def _csv_tuple(value: str) -> tuple[str, ...]:
    if not isinstance(value, str):
        return ()
    result = tuple(
        part.strip()
        for part in value.split(",")
        if part.strip()
    )
    return tuple(dict.fromkeys(result))


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    selected = value.strip()
    return selected or None
