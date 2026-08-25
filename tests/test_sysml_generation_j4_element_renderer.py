from __future__ import annotations

import pytest

from modules.sysml_generation import (
    SysMLElementProjection,
    SysMLElementRenderer,
    SysMLGenerationBlockedError,
)


def _projection(
    *,
    target_construct_id: str,
    element_id: str = "IME-000001",
    symbol: str = "IME_000001",
    name: str = "Engineering Name",
    description: str | None = "Engineering description.",
) -> SysMLElementProjection:
    return SysMLElementProjection(
        internal_model_element_id=element_id,
        generated_symbol=symbol,
        framework_node_id="FW_SYSTEM_REQUIREMENTS",
        package_name="Requirements",
        model_area="system.requirements",
        element_type="system_requirement",
        engineering_name=name,
        engineering_description=description,
        generation_rule_id="J2_ELEMENT_TEST",
        target_construct_id=target_construct_id,
    )


@pytest.mark.parametrize(
    ("construct_id", "prefix"),
    [
        ("TN_004", "part"),
        ("TN_006", "action"),
        ("TN_008", "requirement"),
        ("TN_012", "use case def"),
    ],
)
def test_j4_renders_exact_supported_construct_family(
    construct_id: str,
    prefix: str,
) -> None:
    rendered = SysMLElementRenderer().render(
        _projection(target_construct_id=construct_id)
    )
    assert rendered.content.startswith(f"{prefix} IME_000001 {{\n")
    assert rendered.content.endswith("}")
    assert "Engineering name: Engineering Name" in rendered.content


def test_renderer_technical_identity_is_stable_symbol_not_engineering_name() -> None:
    rendered = SysMLElementRenderer().render(
        _projection(
            target_construct_id="TN_008",
            name="Requirement with spaces",
        )
    )
    first_line = rendered.content.splitlines()[0]
    assert first_line == "requirement IME_000001 {"
    assert "Requirement with spaces" not in first_line


def test_part_and_action_are_usages_not_definitions() -> None:
    part = SysMLElementRenderer().render(
        _projection(target_construct_id="TN_004")
    )
    action = SysMLElementRenderer().render(
        _projection(target_construct_id="TN_006")
    )
    assert part.content.startswith("part IME_000001 {")
    assert "part def" not in part.content
    assert action.content.startswith("action IME_000001 {")
    assert "action def" not in action.content


def test_renderer_without_description_still_preserves_engineering_name() -> None:
    rendered = SysMLElementRenderer().render(
        _projection(
            target_construct_id="TN_004",
            description=None,
        )
    )
    assert rendered.content == (
        "part IME_000001 {\n"
        "    doc /* Engineering name: Engineering Name */\n"
        "}"
    )


def test_renderer_does_not_emit_generic_iem_attributes() -> None:
    rendered = SysMLElementRenderer().render(
        _projection(target_construct_id="TN_008")
    )
    assert "attribute " not in rendered.content


def test_stakeholder_definition_construct_renders_part_definition() -> None:
    rendered = SysMLElementRenderer().render(
        _projection(target_construct_id="TN_003")
    )
    assert rendered.content.startswith("part def IME_000001 {")
    assert "Engineering name: Engineering Name" in rendered.content
