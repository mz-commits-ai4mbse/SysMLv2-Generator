from types import SimpleNamespace

from app.model_assembly_preview_ui import (
    build_model_assembly_outline,
    group_elements_by_model_area,
)


def _element(aid, title, area):
    return SimpleNamespace(
        approved_input_id=aid,
        stable_subject_key=f"subject:{aid}",
        title=title,
        element_type="function",
        model_area=area,
    )


def test_grouping_is_deterministic_by_area_and_title():
    elements = (
        _element("AIN-000002", "Zulu", "system.functional"),
        _element("AIN-000001", "Alpha", "system.functional"),
        _element("AIN-000003", "Beta", "subsystem.functional"),
    )

    grouped = group_elements_by_model_area(elements)

    assert tuple(item[0] for item in grouped) == (
        "subsystem.functional",
        "system.functional",
    )
    assert tuple(item.title for item in grouped[1][1]) == (
        "Alpha",
        "Zulu",
    )


def test_outline_marks_relationship_variance_without_calling_it_sysml():
    elements = (
        _element("AIN-000001", "Source", "system.functional"),
        _element("AIN-000002", "Target", "subsystem.functional"),
    )
    relationship = SimpleNamespace(
        source_subject_key="subject:AIN-000001",
        relationship_kind="related_to",
        target_subject_key="subject:AIN-000002",
        representation_status="persona_variance",
        candidate_rule_ids=(
            "relationship:dependency",
            "relationship:traces_to",
        ),
    )
    draft = SimpleNamespace(
        elements=elements,
        relationships=(relationship,),
    )

    outline = build_model_assembly_outline(draft)

    assert "persona_variance" in outline
    assert "relationship:dependency | relationship:traces_to" in outline
    assert "SysML" not in outline
