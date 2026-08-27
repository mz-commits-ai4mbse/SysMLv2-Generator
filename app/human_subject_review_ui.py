"""Subject-centric Streamlit Human Engineering Review UI."""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import replace
from typing import Any

from modules.review_workspace.errors import ReviewWorkspaceError
from modules.review_workspace.workflow_editing import ReviewItemEditRequest
from modules.semantic_extraction import (
    EPISTEMIC_CLASSES,
    INFORMATION_TYPES,
    STATEMENT_MODALITIES,
)


_ACCEPTED_OUTCOMES = frozenset(
    {
        "accepted_as_generated",
        "accepted_with_modification",
        "combined",
    }
)


def render_subject_review_editor(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    reviewer_identity: str,
    payload: dict,
    technical: bool = False,
) -> None:
    """Render persisted R4c Subject Review cards without any LLM call."""

    cards = subject_review_cards_by_id(payload)
    items = tuple(workspace_view.revision.review_items)

    if set(cards) != {
        canonical_subject_id_from_item(item)
        for item in items
    }:
        st.error(
            "Persisted Subject Review cards do not match the exact current "
            "Review Revision. No inferred fallback was rendered."
        )
        return

    try:
        relationship_decisions = tuple(
            service.subject_relationship_review_decisions(
                project_id,
                workspace_view.document.review_document_id,
                workspace_view.version.review_document_version_id,
            )
        )
    except Exception:
        st.error(
            "Relationship decision authority is unavailable. "
            "No decision state was inferred."
        )
        return

    decisions_by_key = {
        (
            decision.source_subject_id,
            decision.relationship_kind,
            decision.target_subject_id,
        ): decision
        for decision in relationship_decisions
    }
    relationship_keys = _outgoing_relationship_keys(cards.values())
    decided_relationship_keys = relationship_keys.intersection(decisions_by_key)
    pending_relationship_count = (
        len(relationship_keys) - len(decided_relationship_keys)
    )

    reviewed = sum(_subject_decided(item) for item in items)
    st.caption(
        f"Human Engineering Review · {reviewed}/{len(items)} "
        "canonical Subjects decided"
    )
    st.caption(
        "Relationship Review · "
        f"{len(decided_relationship_keys)}/{len(relationship_keys)} "
        "outgoing hypotheses decided"
    )
    if pending_relationship_count:
        st.warning(
            f"{pending_relationship_count} Relationship decision(s) still "
            "require Human Review. Use Pending Decisions to resolve them."
        )

    view_mode = st.radio(
        "Review view",
        options=(
            "pending",
            "reviewed",
            "all",
            "attention",
            "open_questions",
            "rejected",
        ),
        index=0,
        format_func={
            "pending": "Pending Decisions",
            "reviewed": "Reviewed Decisions",
            "all": "All Subjects",
            "attention": "Needs Attention",
            "open_questions": "Open Questions",
            "rejected": "Rejected",
        }.get,
        horizontal=True,
        key=(
            "human_subject_review.view."
            f"{workspace_view.document.review_document_id}"
        ),
    )

    visible = tuple(
        item
        for item in items
        if _visible_in_mode(
            item,
            cards[canonical_subject_id_from_item(item)],
            view_mode,
            relationship_decisions=decisions_by_key,
        )
    )

    if not visible:
        if view_mode == "pending":
            st.info("No pending Subject or Relationship decisions remain.")
        else:
            st.info("No canonical Subjects match the selected Review view.")
        return

    for item in visible:
        subject_id = canonical_subject_id_from_item(item)
        _render_subject_card(
            st,
            service=service,
            project_id=project_id,
            workspace_view=workspace_view,
            item=item,
            card=cards[subject_id],
            reviewer_identity=reviewer_identity,
            technical=technical,
            cards_by_id=cards,
            relationship_decisions=decisions_by_key,
            view_mode=view_mode,
        )


def subject_review_cards_by_id(payload: dict) -> dict[str, dict]:
    if not isinstance(payload, dict):
        raise ValueError("Subject Review payload must be a dictionary.")

    cards = payload.get("cards")
    subject_ids = payload.get("canonical_subject_ids")
    if not isinstance(cards, list) or not isinstance(subject_ids, list):
        raise ValueError(
            "Subject Review payload lacks canonical Subject collections."
        )

    result = {}
    for card in cards:
        if not isinstance(card, dict):
            raise ValueError("Subject Review card must be a dictionary.")
        subject_id = card.get("canonical_subject_id")
        if not isinstance(subject_id, str) or not subject_id:
            raise ValueError("Subject Review card lacks canonical_subject_id.")
        if subject_id in result:
            raise ValueError("Duplicate canonical Subject Review card.")
        result[subject_id] = card

    if tuple(result) != tuple(subject_ids):
        raise ValueError(
            "Subject Review card order/population differs from authority."
        )
    return result


def canonical_subject_id_from_item(item) -> str:
    locator = getattr(item, "original_report_locator", None)
    prefix = "subject_review:"
    if not isinstance(locator, str) or not locator.startswith(prefix):
        raise ValueError(
            "Review Item is not bound to a canonical Subject Review locator."
        )
    value = locator[len(prefix):]
    if not value.startswith("SUBJ-") or not value:
        raise ValueError(
            "Review Item canonical Subject locator is invalid."
        )
    return value


def build_subject_review_item_request(
    item,
    *,
    action: str,
    statement: str | None = None,
    information_type: str | None = None,
    statement_modality: str | None = None,
    epistemic_class: str | None = None,
    rationale: str | None = None,
) -> ReviewItemEditRequest:
    """Map one explicit Subject decision into existing immutable G6 editing."""

    rationale_value = _optional_text(rationale)

    if action == "accept":
        statement_value = _required_text(
            statement,
            "Engineering statement",
        )
        if information_type not in INFORMATION_TYPES:
            raise ValueError("Select a valid Information Type.")
        if statement_modality not in STATEMENT_MODALITIES:
            raise ValueError("Select a valid Statement Modality.")
        if epistemic_class not in EPISTEMIC_CLASSES:
            raise ValueError("Select a valid Epistemic Class.")

        updated = replace(
            item.current_content,
            primary_text=statement_value,
            information_type=information_type,
            modality=statement_modality,
            epistemic_status=epistemic_class,
            human_rationale=rationale_value,
        )
        substantive_current = replace(
            item.current_content,
            human_rationale=rationale_value,
        )
        changed = updated != substantive_current
        if changed and rationale_value is None:
            raise ValueError(
                "A rationale is required when accepted Subject content "
                "or classification is modified."
            )
        # Canonical Subject Review is proposal-free by design.
        # Persona interpretations and consensus remain immutable evidence;
        # Human acceptance authorizes the effective canonical result, not one
        # winning Agent proposal. The existing ReviewWorkspace compatibility
        # outcome for proposal-free acceptance is accepted_with_modification,
        # even when the canonical fields are accepted unchanged.
        outcome = "accepted_with_modification"

    elif action == "reject":
        if rationale_value is None:
            raise ValueError("A rationale is required to reject a Subject.")
        updated = item.current_content
        outcome = "rejected"

    elif action == "defer":
        updated = item.current_content
        outcome = "deferred"

    else:
        raise ValueError("Unsupported Subject Review action.")

    return ReviewItemEditRequest(
        expected_revision_id=item.review_document_version_id.replace(
            "RVV-", "RVR-"
        )
        if False
        else "",  # replaced by caller against the exact current Revision
        expected_item_content_fingerprint=item.item_content_fingerprint,
        updated_content=updated,
        selected_proposal_keys=(),
        review_outcome=outcome,
        rationale=rationale_value,
    )


def _request_for_current_revision(
    item,
    *,
    revision_id: str,
    action: str,
    statement: str | None,
    information_type: str | None,
    statement_modality: str | None,
    epistemic_class: str | None,
    rationale: str | None,
) -> ReviewItemEditRequest:
    draft = build_subject_review_item_request(
        item,
        action=action,
        statement=statement,
        information_type=information_type,
        statement_modality=statement_modality,
        epistemic_class=epistemic_class,
        rationale=rationale,
    )
    return replace(
        draft,
        expected_revision_id=revision_id,
    )


def _render_subject_card(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    item,
    card: dict,
    reviewer_identity: str,
    technical: bool,
    cards_by_id: dict[str, dict] | None = None,
    relationship_decisions: dict[tuple[str, str, str], Any] | None = None,
    view_mode: str = "all",
) -> None:
    context = (
        st.container(border=True)
        if callable(getattr(st, "container", None))
        else nullcontext()
    )
    with context:
        subject_id = card["canonical_subject_id"]
        if technical:
            st.subheader(f"{subject_id} · {card['canonical_label']}")
            st.caption(
                f"Review Item {item.review_item_id} · "
                f"Outcome {item.effective_review_outcome}"
            )
        else:
            st.subheader(card["canonical_label"])
            st.caption(subject_id)

        _render_attention_summary(st, card)
        _render_classification(st, card)

        with st.expander("Source evidence", expanded=False):
            for mention in card.get("mentions", ()):
                st.markdown(f'> "{mention.get("exact_text", "")}"')
                evidence_ids = mention.get("source_evidence_ids", ())
                if evidence_ids:
                    st.caption(
                        f"{mention.get('mention_id', '')} · "
                        + ", ".join(evidence_ids)
                    )

        with st.expander("Persona interpretations", expanded=False):
            for persona in card.get("persona_interpretations", ()):
                st.markdown(f"**{persona.get('persona_id', 'Persona')}**")
                for statement in persona.get(
                    "interpreted_statements",
                    (),
                ):
                    st.markdown(statement)
                uncertainties = persona.get("uncertainties", ())
                missing = persona.get("missing_evidence", ())
                if uncertainties:
                    st.caption(
                        "Uncertainty: " + " | ".join(uncertainties)
                    )
                if missing:
                    st.caption(
                        "Missing evidence: " + " | ".join(missing)
                    )

        _render_relationships(
            st,
            service=service,
            project_id=project_id,
            workspace_view=workspace_view,
            card=card,
            reviewer_identity=reviewer_identity,
            cards_by_id=cards_by_id,
            decisions_by_key=relationship_decisions,
            view_mode=view_mode,
        )

        prefix = (
            "human_subject_review."
            f"{workspace_view.document.review_document_id}."
            f"{item.review_item_id}"
        )
        edit_key = f"{prefix}.edit_mode"
        session_state = getattr(st, "session_state", {})
        edit_mode = bool(session_state.get(edit_key, False))
        decided = _subject_decided(item)

        if decided and not edit_mode:
            if item.effective_review_outcome in _ACCEPTED_OUTCOMES:
                st.success("This canonical Subject is accepted.")
                _render_active_reviewed_content(st, item)
            else:
                st.error("This canonical Subject is rejected.")

            if view_mode != "pending":
                if st.button(
                    "Reopen Subject decision",
                    key=f"{prefix}.reopen",
                    type="secondary",
                ):
                    if not _reviewer_ready(st, reviewer_identity):
                        return
                    session_state[edit_key] = True
                    rerun = getattr(st, "rerun", None)
                    if callable(rerun):
                        rerun()
            return

        st.markdown(
            "**Edit Human decision**" if edit_mode else "**Human decision**"
        )
        if edit_mode:
            st.caption(
                "A changed decision is persisted as a new immutable Review "
                "Revision; the previous decision remains in the audit history."
            )

        statement = st.text_area(
            "Reviewed engineering statement",
            value=item.current_content.primary_text,
            key=f"{prefix}.statement",
        )
        information_type = _classification_selectbox(
            st,
            "Information Type",
            INFORMATION_TYPES,
            item.current_content.information_type,
            key=f"{prefix}.information_type",
        )
        modality = _classification_selectbox(
            st,
            "Statement Modality",
            STATEMENT_MODALITIES,
            item.current_content.modality,
            key=f"{prefix}.modality",
        )
        epistemic = _classification_selectbox(
            st,
            "Epistemic Class",
            EPISTEMIC_CLASSES,
            item.current_content.epistemic_status,
            key=f"{prefix}.epistemic",
        )
        rationale = st.text_input(
            "Decision rationale",
            value="",
            key=f"{prefix}.rationale",
            help=(
                "Required when changing accepted engineering content or "
                "classification, and when rejecting the Subject."
            ),
        )

        changed = _review_fields_changed(
            item,
            statement=statement,
            information_type=information_type,
            statement_modality=modality,
            epistemic_class=epistemic,
        )

        if edit_mode:
            if st.button(
                "Cancel edit",
                key=f"{prefix}.cancel_edit",
                type="tertiary",
            ):
                session_state.pop(edit_key, None)
                rerun = getattr(st, "rerun", None)
                if callable(rerun):
                    rerun()
                return

        accept_label = "Accept with changes" if changed else "Accept"
        columns = st.columns(3)
        actions = (
            (accept_label, "accept", "primary"),
            ("Defer", "defer", "secondary"),
            ("Reject", "reject", "secondary"),
        )
        for column, (label, action, button_type) in zip(
            columns,
            actions,
        ):
            with column:
                if not st.button(
                    label,
                    key=f"{prefix}.{action}",
                    type=button_type,
                ):
                    continue
                if not _reviewer_ready(st, reviewer_identity):
                    return
                if (
                    edit_mode
                    and action == "accept"
                    and item.effective_review_outcome in _ACCEPTED_OUTCOMES
                    and not changed
                ):
                    st.error(
                        "No Subject content or classification change was made. "
                        "Use Cancel edit or choose a different disposition."
                    )
                    return
                try:
                    request = _request_for_current_revision(
                        item,
                        revision_id=(
                            workspace_view.revision.review_revision_id
                        ),
                        action=action,
                        statement=statement,
                        information_type=information_type,
                        statement_modality=modality,
                        epistemic_class=epistemic,
                        rationale=rationale,
                    )
                except ValueError as exc:
                    st.error(str(exc))
                    return

                _persist_decision(
                    st,
                    service=service,
                    project_id=project_id,
                    workspace_view=workspace_view,
                    item=item,
                    request=request,
                    reviewer_identity=reviewer_identity,
                    success_message=(
                        "Canonical Subject review decision persisted."
                    ),
                    clear_state_key=(edit_key if edit_mode else None),
                )
                return


def _render_attention_summary(st: Any, card: dict) -> None:
    classification = bool(
        card.get("classification_review_attention_required", False)
    )
    relationship = bool(
        card.get("relationship_review_attention_required", False)
    )

    if classification:
        st.warning("Classification variance requires Human attention.")
    else:
        st.caption("Classification: stable Persona agreement.")

    if relationship:
        st.caption(
            "Relationship hypotheses contain variance; review them below."
        )


def _render_classification(st: Any, card: dict) -> None:
    rows = []
    for label, key in (
        ("Information Type", "information_type"),
        ("Statement Modality", "statement_modality"),
        ("Epistemic Class", "epistemic_class"),
    ):
        field = card.get(key, {})
        selected = field.get("selected_value")
        rows.append(
            {
                "Field": label,
                "Current consensus": (
                    selected if selected is not None else "Human decision"
                ),
                "Agreement": _agreement_label(field),
                "Distribution": _distribution_label(field),
            }
        )
    st.table(rows)


def _render_relationships(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    card: dict,
    reviewer_identity: str,
    cards_by_id: dict[str, dict] | None = None,
    decisions_by_key: dict[tuple[str, str, str], Any] | None = None,
    view_mode: str = "all",
) -> None:
    relationships = tuple(card.get("relationships", ()))
    if not relationships:
        return

    if decisions_by_key is None:
        try:
            decisions = service.subject_relationship_review_decisions(
                project_id,
                workspace_view.document.review_document_id,
                workspace_view.version.review_document_version_id,
            )
        except Exception:
            st.error(
                "Relationship decision authority is unavailable. "
                "No decision state was inferred."
            )
            return
        decisions_by_key = {
            (
                item.source_subject_id,
                item.relationship_kind,
                item.target_subject_id,
            ): item
            for item in decisions
        }

    cards_by_id = cards_by_id or {
        card.get("canonical_subject_id", ""): card
    }

    if view_mode == "pending":
        relationships = tuple(
            relation
            for relation in relationships
            if relation.get("direction") == "outgoing"
            and _relation_key(relation) not in decisions_by_key
        )
    elif view_mode == "reviewed":
        relationships = tuple(
            relation
            for relation in relationships
            if relation.get("direction") == "outgoing"
            and _relation_key(relation) in decisions_by_key
        )

    if not relationships:
        return

    with st.expander(
        f"Relationship hypotheses ({len(relationships)})",
        expanded=(view_mode in {"pending", "reviewed"}),
    ):
        for relation in relationships:
            direction = relation.get("direction", "")
            source = relation.get("source_subject_id", "")
            target = relation.get("target_subject_id", "")
            kind = relation.get("relationship_kind", "")
            relation_key = (source, kind, target)
            current = decisions_by_key.get(relation_key)
            confidence = str(
                relation.get("confidence", "low")
            ).upper()
            support = len(relation.get("supporting_personas", ()))
            source_label = _subject_label(cards_by_id, source)
            target_label = _subject_label(cards_by_id, target)

            st.markdown(
                f"**{source_label} — {kind.replace('_', ' ')} → "
                f"{target_label}**"
            )
            st.caption(
                f"{source} — {kind} → {target} · "
                f"{confidence} · {support} Persona support · {direction}"
            )
            if relation.get("review_attention_required"):
                st.caption("Relationship-level Human attention required.")

            for variant in relation.get("statement_variants", ()):
                persona = variant.get("persona_id", "Persona")
                for statement in variant.get("statements", ()):
                    st.caption(f"{persona}: {statement}")

            if current is not None:
                if current.outcome == "accepted":
                    st.success("Relationship accepted.")
                elif current.outcome == "rejected":
                    st.error("Relationship rejected.")
                else:
                    st.info("Relationship decision deferred.")
                if current.rationale:
                    st.caption(f"Rationale: {current.rationale}")

            if direction != "outgoing":
                st.caption(
                    "Decision ownership: "
                    f"{source_label} ({source}) source Subject card."
                )
                continue

            prefix = (
                "human_subject_review.relationship."
                f"{workspace_view.document.review_document_id}."
                f"{source}.{kind}.{target}"
            )
            edit_key = f"{prefix}.edit_mode"
            session_state = getattr(st, "session_state", {})
            edit_mode = bool(session_state.get(edit_key, False))

            if current is not None and not edit_mode:
                if view_mode != "pending":
                    if st.button(
                        "Reopen relation decision",
                        key=f"{prefix}.reopen",
                        type="secondary",
                    ):
                        if not _reviewer_ready(st, reviewer_identity):
                            return
                        session_state[edit_key] = True
                        rerun = getattr(st, "rerun", None)
                        if callable(rerun):
                            rerun()
                continue

            if edit_mode:
                st.caption(
                    "A changed relationship decision creates an immutable "
                    "successor decision; the previous decision remains in "
                    "the audit history."
                )

            rationale = st.text_input(
                "Relationship decision rationale",
                value=(current.rationale or "") if edit_mode and current else "",
                key=f"{prefix}.rationale",
                help="Required for Reject; optional otherwise.",
            )

            if edit_mode:
                if st.button(
                    "Cancel relation edit",
                    key=f"{prefix}.cancel_edit",
                    type="tertiary",
                ):
                    session_state.pop(edit_key, None)
                    rerun = getattr(st, "rerun", None)
                    if callable(rerun):
                        rerun()
                    return

            columns = st.columns(3)
            actions = (
                ("Accept relation", "accepted", "primary"),
                ("Defer relation", "deferred", "secondary"),
                ("Reject relation", "rejected", "secondary"),
            )
            for column, (label, outcome, button_type) in zip(
                columns,
                actions,
            ):
                with column:
                    if not st.button(
                        label,
                        key=f"{prefix}.{outcome}",
                        type=button_type,
                    ):
                        continue
                    if not _reviewer_ready(st, reviewer_identity):
                        return
                    rationale_value = _optional_text(rationale)
                    if outcome == "rejected" and rationale_value is None:
                        st.error(
                            "A rationale is required to reject a relationship."
                        )
                        return
                    if (
                        edit_mode
                        and current is not None
                        and outcome == current.outcome
                        and rationale_value == current.rationale
                    ):
                        st.error(
                            "No relationship decision change was made. "
                            "Use Cancel relation edit or choose a different "
                            "decision/rationale."
                        )
                        return

                    try:
                        service.record_subject_relationship_review_decision(
                            project_id,
                            workspace_view.document.review_document_id,
                            workspace_view.version.review_document_version_id,
                            source_subject_id=source,
                            relationship_kind=kind,
                            target_subject_id=target,
                            outcome=outcome,
                            rationale=rationale_value,
                            reviewer_identity=reviewer_identity,
                        )
                    except Exception:
                        st.error(
                            "Relationship decision could not be persisted. "
                            "No successful state was inferred."
                        )
                        return

                    if edit_mode:
                        session_state.pop(edit_key, None)
                    st.success("Relationship decision persisted.")
                    rerun = getattr(st, "rerun", None)
                    if callable(rerun):
                        rerun()
                    return


def _subject_decided(item) -> bool:
    return (
        item.effective_review_outcome in _ACCEPTED_OUTCOMES
        or item.effective_review_outcome == "rejected"
    )


def _relation_key(relation: dict) -> tuple[str, str, str]:
    return (
        str(relation.get("source_subject_id", "")),
        str(relation.get("relationship_kind", "")),
        str(relation.get("target_subject_id", "")),
    )


def _outgoing_relationship_keys(cards) -> set[tuple[str, str, str]]:
    return {
        _relation_key(relation)
        for card in cards
        for relation in card.get("relationships", ())
        if relation.get("direction") == "outgoing"
    }


def _subject_label(cards_by_id: dict[str, dict], subject_id: str) -> str:
    card = cards_by_id.get(subject_id, {})
    label = card.get("canonical_label")
    return label if isinstance(label, str) and label else subject_id


def _render_active_reviewed_content(st: Any, item) -> None:
    content = item.current_content
    st.markdown("**Active reviewed engineering information**")
    st.table(
        [
            {
                "Field": "Engineering statement",
                "Value": content.primary_text,
            },
            {
                "Field": "Information Type",
                "Value": content.information_type,
            },
            {
                "Field": "Statement Modality",
                "Value": content.modality,
            },
            {
                "Field": "Epistemic Class",
                "Value": content.epistemic_status,
            },
        ]
    )
    if content.human_rationale:
        st.caption(f"Human rationale: {content.human_rationale}")


def _review_fields_changed(
    item,
    *,
    statement: str | None,
    information_type: str | None,
    statement_modality: str | None,
    epistemic_class: str | None,
) -> bool:
    statement_value = (
        statement.strip()
        if isinstance(statement, str)
        else statement
    )
    return (
        statement_value != item.current_content.primary_text
        or information_type != item.current_content.information_type
        or statement_modality != item.current_content.modality
        or epistemic_class != item.current_content.epistemic_status
    )

def _agreement_label(field: dict) -> str:
    confidence = str(field.get("confidence", "")).upper()
    consensus = str(field.get("consensus_level", ""))
    support = len(field.get("supporting_personas", ()))
    distribution = field.get("value_distribution", ())
    total = len(
        {
            persona
            for value in distribution
            for persona in value.get("supporting_personas", ())
        }
    )
    vote = f"{support}/{total}" if total else f"{support}"
    return f"{confidence} · {consensus} · {vote}"


def _distribution_label(field: dict) -> str:
    parts = []
    for value in field.get("value_distribution", ()):
        parts.append(
            f"{value.get('value')}: "
            f"{len(value.get('supporting_personas', ()))}"
        )
    return " | ".join(parts)


def _classification_selectbox(
    st: Any,
    label: str,
    allowed_values,
    current: str | None,
    *,
    key: str,
):
    values = ("— Human decision —", *tuple(sorted(allowed_values)))
    try:
        index = values.index(current) if current is not None else 0
    except ValueError:
        index = 0
    selected = st.selectbox(
        label,
        options=values,
        index=index,
        key=key,
    )
    return None if selected == values[0] else selected


def _visible_in_mode(
    item,
    card: dict,
    mode: str,
    *,
    relationship_decisions: dict[tuple[str, str, str], Any] | None = None,
) -> bool:
    relationship_decisions = relationship_decisions or {}
    outgoing = {
        _relation_key(relation)
        for relation in card.get("relationships", ())
        if relation.get("direction") == "outgoing"
    }
    has_pending_relationship = any(
        key not in relationship_decisions
        for key in outgoing
    )
    has_reviewed_relationship = any(
        key in relationship_decisions
        for key in outgoing
    )

    if mode == "pending":
        return (not _subject_decided(item)) or has_pending_relationship
    if mode == "reviewed":
        return _subject_decided(item) or has_reviewed_relationship
    if mode == "all":
        return item.effective_review_outcome != "rejected"
    if mode == "attention":
        return (
            bool(
                card.get(
                    "classification_review_attention_required",
                    False,
                )
            )
            or bool(
                card.get(
                    "relationship_review_attention_required",
                    False,
                )
            )
        ) and item.effective_review_outcome != "rejected"
    if mode == "open_questions":
        return (
            item.review_item_kind == "open_question"
            and item.effective_review_outcome != "rejected"
        )
    if mode == "rejected":
        return item.effective_review_outcome == "rejected"
    return False


def _persist_decision(
    st: Any,
    *,
    service,
    project_id: str,
    workspace_view,
    item,
    request,
    reviewer_identity: str,
    success_message: str,
    clear_state_key: str | None = None,
) -> None:
    try:
        service.save_item_review(
            project_id,
            workspace_view.document.review_document_id,
            workspace_view.version.review_document_version_id,
            item.review_item_id,
            request=request,
            actor_identity=reviewer_identity,
        )
    except ReviewWorkspaceError as exc:
        st.error(str(exc))
        return
    except Exception:
        st.error(
            "The Subject Review decision could not be persisted. "
            "No successful Review state was inferred."
        )
        return

    if clear_state_key is not None:
        session_state = getattr(st, "session_state", None)
        if session_state is not None:
            session_state.pop(clear_state_key, None)
    st.success(success_message)
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()


def _reviewer_ready(st: Any, reviewer_identity: str) -> bool:
    if isinstance(reviewer_identity, str) and reviewer_identity.strip():
        return True
    st.error("Reviewer identity is required before recording a decision.")
    return False


def _required_text(value: str | None, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required.")
    return value.strip()


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Rationale must be text.")
    stripped = value.strip()
    return stripped or None
