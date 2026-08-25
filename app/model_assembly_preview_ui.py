"""Engineer-facing preview of one persisted Model Assembly Draft."""

from __future__ import annotations


def render_model_assembly_preview(st, *, draft, technical: bool = False) -> None:
    """Render the assembled model without introducing review authority."""

    st.subheader("Model Assembly Preview")
    st.caption(
        "This preview reflects Human-approved placements plus accepted "
        "engineering Relationships. It is not yet the Final Model Review."
    )

    columns = st.columns(4)
    columns[0].metric("Elements", len(draft.elements))
    columns[1].metric("Relationships", len(draft.relationships))
    columns[2].metric(
        "Relationship variance",
        draft.relationship_variance_count,
    )
    columns[3].metric(
        "Unmapped relationships",
        draft.unresolved_relationship_count,
    )

    if (
        draft.relationship_variance_count
        or draft.unresolved_relationship_count
    ):
        st.warning(
            "The assembled model preserves unresolved Relationship "
            "representation choices for Final Model Review."
        )
    else:
        st.success(
            "All assembled Relationships currently have one target "
            "representation proposal."
        )

    st.markdown("**RFLP / model-area overview**")
    for model_area, elements in group_elements_by_model_area(draft.elements):
        st.markdown(f"**{_humanize(model_area)}**")
        for element in elements:
            st.write(f"• {element.title} — {_humanize(element.element_type)}")
            if technical:
                st.caption(
                    f"{element.approved_input_id} · "
                    f"{element.selected_rule_id} · "
                    f"{element.placement_decision_id}"
                )

    st.markdown("**Accepted engineering Relationships**")
    title_by_subject_key = {
        item.stable_subject_key: item.title
        for item in draft.elements
    }
    if not draft.relationships:
        st.info("No projectable accepted Relationships are present.")
    for relationship in draft.relationships:
        source = title_by_subject_key.get(
            relationship.source_subject_key,
            relationship.source_subject_key,
        )
        target = title_by_subject_key.get(
            relationship.target_subject_key,
            relationship.target_subject_key,
        )
        st.write(
            f"• {source} → {relationship.relationship_kind} → {target}"
        )
        st.caption(
            "Representation: "
            + _humanize(relationship.representation_status)
        )
        if relationship.candidate_rule_ids:
            st.caption(
                "Target option(s): "
                + ", ".join(relationship.candidate_rule_ids)
            )
        if technical:
            st.caption(
                f"{relationship.relationship_decision_id} · "
                f"{relationship.relationship_decision_fingerprint}"
            )

    st.markdown("**Assembly outline**")
    st.caption(
        "Readable assembly outline only — this is not SysML v2 textual notation."
    )
    st.code(
        build_model_assembly_outline(draft),
        language="text",
    )

    if technical:
        with st.expander("Assembly traceability"):
            st.caption(
                "Approved Placement Set fingerprint: "
                f"{draft.approved_placement_set_fingerprint}"
            )
            st.caption(
                "Approved Engineering Information fingerprint: "
                f"{draft.approved_engineering_information_fingerprint}"
            )
            st.caption(
                "Assembly fingerprint: "
                f"{draft.content_fingerprint}"
            )
            if draft.relationship_projection_response_fingerprints:
                st.caption(
                    "Relationship projection responses: "
                    + ", ".join(
                        draft.relationship_projection_response_fingerprints
                    )
                )


def group_elements_by_model_area(elements):
    grouped = {}
    for element in elements:
        grouped.setdefault(element.model_area, []).append(element)
    return tuple(
        (
            model_area,
            tuple(
                sorted(
                    grouped[model_area],
                    key=lambda item: (
                        item.title.lower(),
                        item.approved_input_id,
                    ),
                )
            ),
        )
        for model_area in sorted(grouped)
    )


def build_model_assembly_outline(draft) -> str:
    lines = ["model assembly"]

    for model_area, elements in group_elements_by_model_area(draft.elements):
        lines.append(f"  [{model_area}]")
        for element in elements:
            lines.append(
                f"    - {element.title} <{element.element_type}>"
            )

    if draft.relationships:
        lines.append("  [relationships]")
        title_by_subject_key = {
            item.stable_subject_key: item.title
            for item in draft.elements
        }
        for relationship in draft.relationships:
            source = title_by_subject_key.get(
                relationship.source_subject_key,
                relationship.source_subject_key,
            )
            target = title_by_subject_key.get(
                relationship.target_subject_key,
                relationship.target_subject_key,
            )
            suffix = relationship.representation_status
            if relationship.candidate_rule_ids:
                suffix += ": " + " | ".join(
                    relationship.candidate_rule_ids
                )
            lines.append(
                f"    - {source} --{relationship.relationship_kind}--> "
                f"{target} [{suffix}]"
            )

    return "\n".join(lines)


def _humanize(value: str) -> str:
    return value.replace("_", " ").replace(".", " · ").strip().title()
