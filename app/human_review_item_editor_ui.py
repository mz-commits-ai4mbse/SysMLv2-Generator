"""Review Item editor UI for G6 Human Review & Approval."""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import replace
from typing import Any

from app.presentation_preferences import technical_details_enabled
from app.human_subject_review_ui import render_subject_review_editor
from modules.guided_workflow import (
    GuidedWorkflowValidationError,
    build_review_item_view,
)
from modules.review_workspace.errors import ReviewWorkspaceError
from modules.review_workspace.open_question_resolution import (
    CreateElementFromOpenQuestionRequest,
    ResolveRelationshipEndpointsRequest,
)
from modules.review_workspace.p9_proposal_adapter import P9_ELEMENT_TYPES
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
    """Render content-first Human Review over verified G6 commands."""

    revision = workspace_view.revision
    technical = technical_details_enabled(
        getattr(st, "session_state", {})
    )

    if workspace_view.version.version_state != "draft":
        st.info(
            "This Review Version is finalized and read-only. "
            "Reopen it before editing."
        )
        return

    subject_payload_loader = getattr(
        service,
        "subject_review_bundle_payload",
        None,
    )
    if callable(subject_payload_loader):
        try:
            subject_payload = subject_payload_loader(
                project_id,
                workspace_view.document.review_document_id,
                workspace_view.version.review_document_version_id,
            )
        except ReviewWorkspaceError:
            st.error(
                "Persisted Subject Review authority could not be "
                "reconstructed for this Review Workspace."
            )
            return
        except Exception:
            st.error(
                "Subject-centric Human Review is unavailable. "
                "No legacy fallback was inferred for this bound Workspace."
            )
            return

        if subject_payload is not None:
            render_subject_review_editor(
                st,
                service=service,
                project_id=project_id,
                workspace_view=workspace_view,
                reviewer_identity=reviewer_identity,
                payload=subject_payload,
                technical=technical,
            )
            return

    with _expander(
        st,
        "Advanced review actions",
        expanded=technical,
    ):
        render_scoped_review_actions_ui(
            st,
            service=service,
            project_id=project_id,
            workspace_view=workspace_view,
            reviewer_identity=reviewer_identity,
        )

    try:
        facts = service.review_filter_facts(
            project_id,
            workspace_view.document.review_document_id,
            workspace_view.version.review_document_version_id,
        )
    except ReviewWorkspaceError:
        st.error(
            "Human Review comparison facts could not be reconstructed "
            "from the exact current Review Revision."
        )
        return
    except Exception:
        st.error(
            "Human Review comparison facts are unavailable. "
            "No fallback interpretation was inferred."
        )
        return

    fact_by_id = {
        fact.review_item_id: fact
        for fact in facts
    }

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
        fact = fact_by_id.get(item.review_item_id)
        if fact is None:
            st.error(
                "The current Review Item is missing its exact comparison "
                "facts. The item is not rendered as an inferred fallback."
            )
            continue

        _render_item(
            st,
            service=service,
            project_id=project_id,
            workspace_view=workspace_view,
            item=item,
            reviewer_identity=reviewer_identity,
            filter_fact=fact,
            technical=technical,
        )

    if section != "rejected_content" and len(items) >= 2:
        with _expander(
            st,
            "Advanced merge operation",
            expanded=False,
        ):
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

    if section == "open_questions":
        return tuple(
            item
            for item in review_items
            if (
                item.section == "open_questions"
                and item.effective_review_outcome
                in {"open", "unresolved", "deferred"}
            )
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
    filter_fact,
    technical: bool,
) -> None:
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
            return
        except Exception:
            st.error(
                "Agent proposal content is unavailable. "
                "No fallback proposal state was inferred."
            )
            return

    try:
        presentation = build_review_item_view(
            item,
            proposal_details=details,
            filter_fact=filter_fact,
        )
    except GuidedWorkflowValidationError:
        st.error(
            "This Review Item could not be projected from its exact "
            "content, proposal and consensus bindings."
        )
        return

    if (
        item.review_item_kind == "open_question"
        and _render_relationship_resolution_card(
            st,
            service=service,
            project_id=project_id,
            workspace_view=workspace_view,
            item=item,
            reviewer_identity=reviewer_identity,
            technical=technical,
        )
    ):
        return

    if technical:
        st.subheader(
            f"{item.review_item_id} · {presentation.subject.title}"
        )
        st.caption(
            f"Kind: {item.review_item_kind} · "
            f"Outcome: {item.effective_review_outcome} · "
            f"Lineage: {item.lineage_operation}"
        )
    else:
        st.subheader(presentation.subject.title)

    _render_variance_summary(
        st,
        presentation,
    )

    st.markdown(presentation.subject.primary_text)
    if presentation.subject.secondary_text:
        st.caption(presentation.subject.secondary_text)

    with _expander(
        st,
        "Engineering details",
        expanded=False,
    ):
        _render_effective_dimensions(st, item)

    with _expander(
        st,
        "Source evidence",
        expanded=False,
    ):
        _render_evidence(
            st,
            item,
            technical=technical,
        )

    if details:
        st.markdown("**Independent perspectives**")
        _render_persona_proposals(
            st,
            service=service,
            project_id=project_id,
            workspace_view=workspace_view,
            item=item,
            details=details,
            reviewer_identity=reviewer_identity,
            technical=technical,
        )
    else:
        st.info(
            "No independent Agent proposals are attached to this "
            "Review Item."
        )

    _render_item_outcome_controls(
        st,
        service=service,
        project_id=project_id,
        workspace_view=workspace_view,
        item=item,
        reviewer_identity=reviewer_identity,
    )

    with _expander(
        st,
        "Advanced item operations",
        expanded=False,
    ):
        _render_split_controls(
            st,
            service=service,
            project_id=project_id,
            workspace_view=workspace_view,
            item=item,
            reviewer_identity=reviewer_identity,
        )



def _render_relationship_resolution_card(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    item,
    reviewer_identity: str,
    technical: bool,
) -> bool:
    """Render one concise decision card for an unresolved relationship."""

    try:
        projections = service.relationship_resolution_candidates(
            project_id,
            workspace_view.document.review_document_id,
            workspace_view.version.review_document_version_id,
            item.review_item_id,
        )
    except ReviewWorkspaceError:
        st.error(
            "Relationship resolution candidates could not be reconstructed "
            "from exact Review evidence."
        )
        return True
    except Exception:
        st.error(
            "Relationship resolution candidates are unavailable. "
            "No fallback endpoint was inferred."
        )
        return True

    if not projections:
        return False

    projection = projections[0]
    source_statements = tuple(
        dict.fromkeys(
            candidate.source_statement
            for candidate in projections
        )
    )

    st.subheader("Relationship needs resolution")
    st.warning(
        "Human decision required. Select the engineering elements that "
        "the source-supported relationship should bind."
    )
    st.markdown(
        f"**{projection.source_endpoint}** "
        f"— *{projection.semantic_intent}* → "
        f"**{projection.target_endpoint}**"
    )

    if len(source_statements) == 1:
        st.caption(f'Source: "{source_statements[0]}"')
    else:
        st.caption(
            f"{len(source_statements)} source statements support this "
            "grouped relationship question."
        )

    if len(projections) > 1:
        st.caption(
            f"{len(projections)} Agent occurrences are grouped under "
            "this Human decision."
        )

    source_key = (
        "human_review_item_editor.endpoint.source."
        f"{item.review_item_id}"
    )
    target_key = (
        "human_review_item_editor.endpoint.target."
        f"{item.review_item_id}"
    )

    st.markdown("**Source element**")
    selected_source = _render_resolution_candidate_cards(
        st,
        cards=projection.source_candidates,
        selection_key=source_key,
        endpoint_role="source",
    )
    _render_create_element_from_evidence(
        st,
        service=service,
        project_id=project_id,
        workspace_view=workspace_view,
        item=item,
        endpoint_name=projection.source_endpoint,
        endpoint_role="source",
        source_statement=source_statements[0],
        reviewer_identity=reviewer_identity,
        show_by_default=not projection.source_candidates,
    )

    st.markdown("**Target element**")
    selected_target = _render_resolution_candidate_cards(
        st,
        cards=projection.target_candidates,
        selection_key=target_key,
        endpoint_role="target",
    )
    _render_create_element_from_evidence(
        st,
        service=service,
        project_id=project_id,
        workspace_view=workspace_view,
        item=item,
        endpoint_name=projection.target_endpoint,
        endpoint_role="target",
        source_statement=source_statements[0],
        reviewer_identity=reviewer_identity,
        show_by_default=not projection.target_candidates,
    )

    if selected_source is not None and selected_target is not None:
        rationale_key = (
            "human_review_item_editor.resolve_relationship.rationale."
            f"{item.review_item_id}"
        )
        rationale = st.text_input(
            "Resolution rationale",
            value="",
            key=rationale_key,
            help=(
                "Required. Explain why the selected elements represent "
                "the source-supported relationship endpoints."
            ),
        )
        rationale_value = _optional_text(rationale)

        if st.button(
            "Resolve relationship with selected elements",
            key=(
                "human_review_item_editor.resolve_relationship.submit."
                f"{item.review_item_id}"
            ),
            type="primary",
        ):
            if not _reviewer_ready(st, reviewer_identity):
                return True
            if rationale_value is None:
                st.error(
                    "A rationale is required to resolve the relationship."
                )
                return True

            _execute(
                st,
                lambda: service.resolve_relationship_open_question(
                    project_id,
                    workspace_view.document.review_document_id,
                    workspace_view.version.review_document_version_id,
                    item.review_item_id,
                    request=ResolveRelationshipEndpointsRequest(
                        expected_revision_id=(
                            workspace_view.revision.review_revision_id
                        ),
                        expected_question_fingerprint=(
                            item.item_content_fingerprint
                        ),
                        source_subject_key=(
                            selected_source.stable_subject_key
                        ),
                        target_subject_key=(
                            selected_target.stable_subject_key
                        ),
                        semantic_intent=projection.semantic_intent,
                        relationship_title=(
                            f"{selected_source.title} "
                            f"{projection.semantic_intent} "
                            f"{selected_target.title}"
                        ),
                        relationship_primary_text=source_statements[0],
                        rationale=rationale_value,
                    ),
                    actor_identity=reviewer_identity,
                ),
                "Relationship endpoints resolved. "
                "The relationship remains open for representation review.",
            )
    else:
        st.info(
            "Select one source element and one target element before "
            "resolving the relationship."
        )

    with _expander(
        st,
        "Other review decisions",
        expanded=False,
    ):
        _render_item_outcome_controls(
            st,
            service=service,
            project_id=project_id,
            workspace_view=workspace_view,
            item=item,
            reviewer_identity=reviewer_identity,
        )

    if technical:
        with _expander(
            st,
            "Technical resolution details",
            expanded=False,
        ):
            st.markdown(item.current_content.primary_text)
            if item.current_content.description:
                st.caption(item.current_content.description)
            _render_evidence(
                st,
                item,
                technical=True,
            )

    return True


def _render_resolution_candidate_cards(
    st: Any,
    *,
    cards,
    selection_key: str,
    endpoint_role: str,
):
    """Render exact existing element subjects as selectable engineering cards."""

    if not cards:
        st.warning(
            "No exact existing element candidate matches this endpoint."
        )
        return None

    session_state = getattr(st, "session_state", {})
    selected_key = session_state.get(selection_key)

    valid_keys = {
        card.stable_subject_key
        for card in cards
    }
    if selected_key not in valid_keys:
        selected_key = None
        if selection_key in session_state:
            del session_state[selection_key]

    for card in cards:
        selected = card.stable_subject_key == selected_key
        container_factory = getattr(st, "container", None)
        context = (
            container_factory(border=True)
            if callable(container_factory)
            else nullcontext()
        )
        with context:
            st.markdown(f"**{card.title}**")
            st.caption(
                f"{card.information_type or 'Unclassified'} · "
                f"{card.proposal_count} Agent proposal(s) · "
                f"{card.source_evidence_count} evidence reference(s)"
            )
            st.markdown(card.primary_text)

            if selected:
                st.success(
                    f"Selected as {endpoint_role} endpoint."
                )
            elif st.button(
                f"Use as {endpoint_role} endpoint",
                key=_resolution_candidate_button_key(
                    selection_key=selection_key,
                    endpoint_role=endpoint_role,
                    review_item_id=card.review_item_id,
                ),
            ):
                session_state[selection_key] = (
                    card.stable_subject_key
                )
                selected_key = card.stable_subject_key

    return next(
        (
            card
            for card in cards
            if card.stable_subject_key == selected_key
        ),
        None,
    )


def _resolution_candidate_button_key(
    *,
    selection_key: str,
    endpoint_role: str,
    review_item_id: str,
) -> str:
    """Return one widget key scoped to the exact Open Question."""

    return (
        "human_review_item_editor.endpoint.select."
        f"{selection_key}.{endpoint_role}.{review_item_id}"
    )


def _render_create_element_from_evidence(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    item,
    endpoint_name: str,
    endpoint_role: str,
    source_statement: str,
    reviewer_identity: str,
    show_by_default: bool,
) -> None:
    label = (
        "Create element from source evidence"
        if show_by_default
        else "Create alternative element from source evidence"
    )
    with _expander(
        st,
        label,
        expanded=show_by_default,
    ):
        prefix = (
            "human_review_item_editor.create_endpoint."
            f"{item.review_item_id}.{endpoint_role}"
        )

        name = st.text_input(
            "Element name",
            value=endpoint_name,
            key=f"{prefix}.name",
        )

        element_types = (
            "other",
            *tuple(
                value
                for value in sorted(P9_ELEMENT_TYPES)
                if value != "other"
            ),
        )
        element_type = st.selectbox(
            "Element type",
            options=element_types,
            index=0,
            key=f"{prefix}.type",
        )

        primary_text = st.text_area(
            "Engineering statement",
            value=f"Source-supported element: {endpoint_name}.",
            key=f"{prefix}.statement",
        )
        description = st.text_area(
            "Description",
            value=(
                "Explicitly referenced by the source statement: "
                f"{source_statement}"
            ),
            key=f"{prefix}.description",
        )
        rationale = st.text_input(
            "Creation rationale",
            value="",
            key=f"{prefix}.rationale",
            help=(
                "Required. Creating an element is an explicit Human "
                "engineering decision."
            ),
        )
        rationale_value = _optional_text(rationale)

        if st.button(
            "Create element",
            key=f"{prefix}.submit",
        ):
            if not _reviewer_ready(st, reviewer_identity):
                return
            if rationale_value is None:
                st.error(
                    "A rationale is required to create an element."
                )
                return

            _execute(
                st,
                lambda: service.create_element_from_open_question(
                    project_id,
                    workspace_view.document.review_document_id,
                    workspace_view.version.review_document_version_id,
                    item.review_item_id,
                    request=CreateElementFromOpenQuestionRequest(
                        expected_revision_id=(
                            workspace_view.revision.review_revision_id
                        ),
                        expected_question_fingerprint=(
                            item.item_content_fingerprint
                        ),
                        element_name=name.strip(),
                        element_type=element_type,
                        primary_text=primary_text.strip(),
                        description=_optional_text(description),
                        rationale=rationale_value,
                    ),
                    actor_identity=reviewer_identity,
                ),
                "Element created from exact source evidence. "
                "The relationship question remains open until endpoints "
                "are explicitly bound.",
            )



def _render_effective_dimensions(
    st: Any,
    item,
) -> None:
    """Render current engineering meaning plus persisted Human selections."""

    content = item.current_content
    rows = [
        {
            "Dimension": "information_type",
            "Value": content.information_type or "not_classified",
            "Origin": "current_review_content",
            "Sources": "",
        },
        {
            "Dimension": "modality",
            "Value": content.modality or "not_specified",
            "Origin": "current_review_content",
            "Sources": "",
        },
        {
            "Dimension": "epistemic_status",
            "Value": content.epistemic_status or "not_specified",
            "Origin": "current_review_content",
            "Sources": "",
        },
    ]

    relationship = content.relationship_representation
    if relationship is not None:
        rows.append(
            {
                "Dimension": "relationship_validation_status",
                "Value": relationship.validation_status,
                "Origin": "current_review_content",
                "Sources": "",
            }
        )

    rows.extend(
        {
            "Dimension": selection.dimension,
            "Value": ", ".join(selection.selected_values),
            "Origin": selection.value_origin,
            "Sources": ", ".join(
                selection.source_reference_ids
            ),
        }
        for selection in item.dimension_selections
    )

    st.table(rows)


def _render_evidence(
    st: Any,
    item,
    *,
    technical: bool,
) -> None:
    source_count = len(item.source_evidence_references)
    consensus_count = len(item.consensus_evidence_references)

    st.caption(
        f"{source_count} source evidence reference(s) · "
        f"{consensus_count} consensus evidence reference(s)"
    )

    if not technical:
        return

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
    technical: bool = False,
) -> None:
    if technical:
        st.caption(
            f"Proposal {detail.proposal_id} · "
            f"{detail.agent_id} / {detail.persona_id}"
        )

    st.markdown(detail.proposed_primary_text)

    confidence = getattr(detail, "confidence", None)
    if confidence:
        st.caption(f"Confidence: {confidence}")

    with _expander(
        st,
        "Why this proposal?",
        expanded=False,
    ):
        if detail.rationale:
            st.markdown(detail.rationale)
        supporting = len(
            tuple(getattr(detail, "supporting_evidence", ()))
        )
        missing = len(
            tuple(getattr(detail, "missing_evidence", ()))
        )
        st.caption(
            f"{supporting} supporting evidence item(s) · "
            f"{missing} missing evidence item(s)"
        )

        if technical:
            st.table(
                [
                    {
                        "Proposal ID": detail.proposal_id,
                        "Agent": detail.agent_id,
                        "Persona": detail.persona_id,
                        "Classification": (
                            detail.proposed_information_type
                        ),
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
        "Decision rationale",
        value="",
        key=rationale_key,
        help=(
            "Required when rejecting a proposal and for "
            "relationship acceptance."
        ),
    )
    rationale_value = _optional_text(rationale)

    actions = _columns(st, 2)
    with actions[0]:
        if st.button(
            "Accept",
            key=(
                "human_review_item_editor.accept."
                f"{item.review_item_id}.{detail.proposal_key}"
            ),
            type="primary",
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

    with actions[1]:
        if st.button(
            "Reject",
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

    with _expander(
        st,
        "Edit before accepting",
        expanded=False,
    ):
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
    st.markdown("**Review item decision**")

    accepted_outcomes = {
        "accepted_as_generated",
        "accepted_with_modification",
        "combined",
    }
    if item.effective_review_outcome in accepted_outcomes:
        st.success("This Review Item is accepted.")
        return

    if not item.proposal_references:
        if st.button(
            "Accept reviewed information",
            key=(
                "human_review_item_editor.accept_evidence_only."
                f"{item.review_item_id}"
            ),
            type="primary",
        ):
            if not _reviewer_ready(st, reviewer_identity):
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
                review_outcome="accepted_with_modification",
                rationale=None,
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
                "Reviewed source-grounded information accepted.",
            )

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
        ("Defer", "deferred", False),
        ("Reject item", "rejected", True),
        ("Out of scope", "out_of_scope", False),
    )
    columns = _columns(st, len(actions))

    for column, (
        label,
        outcome,
        requires_rationale,
    ) in zip(columns, actions):
        with column:
            if not st.button(
                label,
                key=(
                    "human_review_item_editor.item_outcome."
                    f"{item.review_item_id}.{outcome}"
                ),
            ):
                continue

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


def _render_variance_summary(
    st: Any,
    presentation,
) -> None:
    label = presentation.variance.label
    decision = presentation.decision_label

    if presentation.variance.semantic == "positive":
        st.success(
            f"Agreement: {label}. {decision}."
        )
    elif presentation.variance.semantic == "attention":
        st.warning(
            f"Variance: {label}. {decision}."
        )
    elif presentation.variance.semantic == "blocking":
        st.error(
            f"Variance: {label}. {decision}."
        )
    else:
        st.info(
            f"Consensus: {label}. {decision}."
        )


def _render_persona_proposals(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    item,
    details,
    reviewer_identity: str,
    technical: bool,
) -> None:
    grouped = {}
    for detail in details:
        grouped.setdefault(detail.persona_id, []).append(detail)

    persona_ids = tuple(sorted(grouped))
    for offset in range(0, len(persona_ids), 3):
        batch = persona_ids[offset:offset + 3]
        columns = _columns(st, len(batch))

        for column, persona_id in zip(columns, batch):
            with column:
                st.markdown(
                    f"**{_humanize_identifier(persona_id)}**"
                )
                persona_details = sorted(
                    grouped[persona_id],
                    key=lambda value: (
                        value.proposal_id,
                        value.proposal_key,
                    ),
                )
                if len(persona_details) > 1:
                    st.caption(
                        f"{len(persona_details)} runs grouped under "
                        "this Persona"
                    )

                for index, detail in enumerate(
                    persona_details,
                    start=1,
                ):
                    if len(persona_details) > 1:
                        st.caption(f"Run {index}")
                    _render_proposal(
                        st,
                        service=service,
                        project_id=project_id,
                        workspace_view=workspace_view,
                        item=item,
                        detail=detail,
                        reviewer_identity=reviewer_identity,
                        technical=technical,
                    )


def _columns(st: Any, count: int):
    factory = getattr(st, "columns", None)
    if callable(factory):
        return factory(count)
    return tuple(nullcontext() for _ in range(count))


def _expander(
    st: Any,
    label: str,
    *,
    expanded: bool,
):
    factory = getattr(st, "expander", None)
    if callable(factory):
        return factory(label, expanded=expanded)
    return nullcontext()


def _humanize_identifier(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").strip().title()


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
