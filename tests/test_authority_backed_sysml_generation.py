from modules.framework import load_framework_template
from modules.model_candidates.structure_profile import (
    load_model_structure_profile,
)
from modules.sysml_generation.authority_backed import (
    AuthorityBackedSysMLArtifactBuilder,
)
from modules.sysml_generation.generation_profile import (
    load_generation_profile,
)

from tests.test_authority_backed_internal_model import (
    _final,
)
from modules.internal_model.authority_backed import (
    build_authority_backed_internal_model,
)


def _source_model():
    template = load_framework_template()
    profile = load_model_structure_profile(
        framework_template=template,
    )
    generation = load_generation_profile()

    supported = next(
        item
        for item in generation["element_mappings"]
        if item["mapping_status"] == "supported"
    )
    area = next(
        item
        for item in profile.model_areas
        if item.model_area_id == supported["model_area"]
        and supported["element_type"] in item.permitted_element_types
    )

    class Element:
        approved_input_id = "AIN-000001"
        stable_subject_key = "subject:test"
        title = "Generated Test Element"
        primary_text = "Generated from approved engineering information."
        selected_rule_id = "TEST"
        model_area = area.model_area_id
        element_type = supported["element_type"]
        framework_assignment = area.framework_node_id
        placement_decision_id = "MPD-000001"
        placement_decision_fingerprint = "b" * 64

    class Draft:
        project_id = "120412"
        comparison_fingerprint = "1" * 64
        content_fingerprint = "2" * 64
        approved_placement_set_fingerprint = "3" * 64
        approved_engineering_information_fingerprint = "4" * 64
        profile_id = profile.profile_id
        profile_version = profile.profile_version
        profile_fingerprint = profile.profile_fingerprint
        elements = (Element(),)
        relationships = ()

    class Final:
        project_id = "120412"
        comparison_fingerprint = "1" * 64
        assembly_draft_fingerprint = "2" * 64
        approved_placement_set_fingerprint = "3" * 64
        approved_engineering_information_fingerprint = "4" * 64
        final_assembly_decision_id = "FAD-000001"
        decision_fingerprint = "6" * 64
        decision = "approved"
        relationship_resolutions = ()

    snapshot = build_authority_backed_internal_model(
        draft=Draft(),
        final_decision=Final(),
        profile=profile,
        framework_template=template,
        internal_engineering_model_id="IEM-000001",
        created_at="2026-08-24T20:00:00Z",
    )
    return snapshot


def test_authority_backed_generation_reuses_phase_j_policy_without_mcd():
    artifact = AuthorityBackedSysMLArtifactBuilder().build(
        _source_model()
    )

    assert len(artifact.units) == 1
    assert "package " in artifact.units[0].content
    assert "MCD-" not in artifact.units[0].content
    assert len(artifact.traceability_entries) == 1
    trace = artifact.traceability_entries[0]
    assert trace.authority_references[0].authority_id == "MPD-000001"
    assert trace.approved_input_id == "AIN-000001"
