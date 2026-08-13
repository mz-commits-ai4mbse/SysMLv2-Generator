from __future__ import annotations

from dataclasses import replace

import pytest

from modules.sysml_generation import (
    SysMLGenerationBlockedError,
    SysMLRelationshipProjection,
    SysMLRelationshipRenderer,
)


def _projection(
    *,
    construct_id: str,
    rule_id: str,
    relation_id: str = "IMR-000001",
    source: str = "IME_000001",
    target: str = "IME_000002",
    endpoint_rendering: str = "source_to_target",
) -> SysMLRelationshipProjection:
    return SysMLRelationshipProjection(
        internal_model_relationship_id=relation_id,
        generated_trace_symbol=relation_id.replace("-", "_"),
        source_internal_model_element_id="IME-000001",
        target_internal_model_element_id="IME-000002",
        source_generated_symbol=source,
        target_generated_symbol=target,
        relationship_family=(
            "dependency" if construct_id == "TN_013" else "allocation"
        ),
        semantic_intent=(
            "dependency" if construct_id == "TN_013" else "allocated_to"
        ),
        directionality="source_to_target",
        generation_rule_id=rule_id,
        target_construct_id=construct_id,
        endpoint_rendering=endpoint_rendering,
    )


def test_dependency_renderer_preserves_exact_source_target_direction() -> None:
    rendered = SysMLRelationshipRenderer().render(
        _projection(
            construct_id="TN_013",
            rule_id="J2_REL_002",
        )
    )
    assert rendered.content == (
        "dependency from IME_000001 to IME_000002;"
    )
    assert rendered.generated_trace_symbol == "IMR_000001"


def test_allocation_renderer_preserves_exact_source_target_direction() -> None:
    rendered = SysMLRelationshipRenderer().render(
        _projection(
            construct_id="TN_014",
            rule_id="J2_REL_001",
        )
    )
    assert rendered.content == "allocate IME_000001 to IME_000002;"


def test_relationship_identity_is_not_injected_into_unvalidated_name_position() -> None:
    rendered = SysMLRelationshipRenderer().render(
        _projection(
            construct_id="TN_013",
            rule_id="J2_REL_002",
        )
    )
    assert "IMR_000001" not in rendered.content
    assert rendered.generated_trace_symbol == "IMR_000001"


@pytest.mark.parametrize(
    "construct_id",
    ["TN_999"],
)
def test_unimplemented_relationship_construct_blocks(
    construct_id: str,
) -> None:
    projection = _projection(
        construct_id=construct_id,
        rule_id="J2_REL_TEST",
    )
    with pytest.raises(SysMLGenerationBlockedError) as exc_info:
        SysMLRelationshipRenderer().render(projection)

    assert exc_info.value.findings[0].code == (
        "UNSUPPORTED_RELATIONSHIP_RENDERER"
    )


@pytest.mark.parametrize(
    "construct_id,rule_id",
    [
        ("TN_013", "J2_REL_002"),
        ("TN_014", "J2_REL_001"),
    ],
)
def test_endpoint_rendering_mismatch_blocks(
    construct_id: str,
    rule_id: str,
) -> None:
    projection = _projection(
        construct_id=construct_id,
        rule_id=rule_id,
        endpoint_rendering="target_by_source",
    )
    with pytest.raises(SysMLGenerationBlockedError) as exc_info:
        SysMLRelationshipRenderer().render(projection)

    assert exc_info.value.findings[0].code == (
        "RELATIONSHIP_ENDPOINT_RENDERING_MISMATCH"
    )


def test_relationship_renderer_is_byte_deterministic() -> None:
    projection = _projection(
        construct_id="TN_014",
        rule_id="J2_REL_001",
    )
    renderer = SysMLRelationshipRenderer()
    assert renderer.render(projection).content == renderer.render(projection).content


def test_satisfaction_renderer_maps_iem_source_satisfies_target_to_sysml_target_by_source() -> None:
    projection = _projection(
        construct_id="TN_015",
        rule_id="J2_REL_008",
        source="IME_000002",
        target="IME_000001",
        endpoint_rendering="target_by_source",
    )
    projection = replace(
        projection,
        relationship_family="refinement",
        semantic_intent="satisfies",
    )
    rendered = SysMLRelationshipRenderer().render(projection)
    assert rendered.content == "satisfy IME_000001 by IME_000002;"


def test_satisfaction_rejects_source_to_target_textual_rendering() -> None:
    projection = _projection(
        construct_id="TN_015",
        rule_id="J2_REL_008",
        endpoint_rendering="source_to_target",
    )
    projection = replace(
        projection,
        relationship_family="refinement",
        semantic_intent="satisfies",
    )
    with pytest.raises(SysMLGenerationBlockedError) as exc_info:
        SysMLRelationshipRenderer().render(projection)
    assert exc_info.value.findings[0].code == (
        "RELATIONSHIP_ENDPOINT_RENDERING_MISMATCH"
    )
