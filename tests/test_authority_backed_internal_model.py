from types import SimpleNamespace

import pytest

from modules.internal_model.authority_backed import (
    build_authority_backed_internal_model,
)
from modules.model_placement.errors import ModelPlacementContractError


def _profile():
    return SimpleNamespace(
        profile_id="TURING_MODEL_STRUCTURE",
        profile_version="1.0.0",
        profile_fingerprint="a" * 64,
        model_areas=(
            SimpleNamespace(
                model_area_id="system.functional",
                framework_node_id="FW_SYSTEM_FUNCTIONAL",
                permitted_element_types=("function",),
            ),
            SimpleNamespace(
                model_area_id="subsystem.functional",
                framework_node_id="FW_SUBSYSTEM_FUNCTIONAL",
                permitted_element_types=("function",),
            ),
        ),
        relationship_semantics=(
            SimpleNamespace(
                semantic_intent="dependency",
                relationship_family="dependency",
                directionality="source_to_target",
            ),
        ),
    )


def _template():
    return {
        "template_id": "TURING_RFLP_FRAMEWORK",
        "template_version": "1.0.0",
        "nodes": [
            {
                "node_id": "FW_SYSTEM_FUNCTIONAL",
                "mapping_key": "system.functional",
                "name": "System Functional",
                "node_type": "functional",
                "parent_node_id": None,
                "order": 1,
            },
            {
                "node_id": "FW_SUBSYSTEM_FUNCTIONAL",
                "mapping_key": "subsystem.functional",
                "name": "Subsystem Functional",
                "node_type": "functional",
                "parent_node_id": "FW_SYSTEM_FUNCTIONAL",
                "order": 2,
            },
        ],
    }


def _element(aid, key, area, framework, mpd):
    return SimpleNamespace(
        approved_input_id=aid,
        stable_subject_key=key,
        title=aid,
        primary_text=f"statement {aid}",
        selected_rule_id="RULE",
        model_area=area,
        element_type="function",
        framework_assignment=framework,
        placement_decision_id=mpd,
        placement_decision_fingerprint="b" * 64,
    )


def _relationship():
    return SimpleNamespace(
        relationship_decision_id="SRD-000001",
        relationship_decision_fingerprint="c" * 64,
        source_subject_key="subject:one",
        target_subject_key="subject:two",
    )


def _draft():
    return SimpleNamespace(
        project_id="120412",
        comparison_fingerprint="1" * 64,
        content_fingerprint="2" * 64,
        approved_placement_set_fingerprint="3" * 64,
        approved_engineering_information_fingerprint="4" * 64,
        profile_id="TURING_MODEL_STRUCTURE",
        profile_version="1.0.0",
        profile_fingerprint="a" * 64,
        elements=(
            _element(
                "AIN-000001",
                "subject:one",
                "system.functional",
                "FW_SYSTEM_FUNCTIONAL",
                "MPD-000001",
            ),
            _element(
                "AIN-000002",
                "subject:two",
                "subsystem.functional",
                "FW_SUBSYSTEM_FUNCTIONAL",
                "MPD-000002",
            ),
        ),
        relationships=(_relationship(),),
    )


def _final(decision="approved"):
    resolution = SimpleNamespace(
        relationship_decision_id="SRD-000001",
        selected_rule_id="relationship:dependency",
        resolution_source="human_resolved_final_review",
        content_fingerprint="5" * 64,
    )
    return SimpleNamespace(
        project_id="120412",
        comparison_fingerprint="1" * 64,
        assembly_draft_fingerprint="2" * 64,
        approved_placement_set_fingerprint="3" * 64,
        approved_engineering_information_fingerprint="4" * 64,
        final_assembly_decision_id="FAD-000001",
        decision_fingerprint="6" * 64,
        decision=decision,
        relationship_resolutions=(resolution,),
    )


def test_materialization_preserves_real_human_authorities_without_mcd():
    model = build_authority_backed_internal_model(
        draft=_draft(),
        final_decision=_final(),
        profile=_profile(),
        framework_template=_template(),
        internal_engineering_model_id="IEM-000001",
        created_at="2026-08-24T20:00:00Z",
    )

    assert model.elements[0].placement_authority.authority_id == (
        "MPD-000001"
    )
    assert model.relationships[0].engineering_relationship_authority.authority_id == (
        "SRD-000001"
    )
    assert model.relationships[0].final_representation_authority.authority_id == (
        "FAD-000001"
    )
    assert model.relationships[0].semantic_intent == "dependency"


def test_nonapproved_final_review_blocks_internal_model():
    with pytest.raises(ModelPlacementContractError, match="approved"):
        build_authority_backed_internal_model(
            draft=_draft(),
            final_decision=_final("changes_requested"),
            profile=_profile(),
            framework_template=_template(),
            internal_engineering_model_id="IEM-000001",
        )
