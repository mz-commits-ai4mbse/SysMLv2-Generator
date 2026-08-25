from pathlib import Path

from modules.agents.team_config import load_team_config


ROOT = Path(__file__).resolve().parents[1]
TEAM_FILE = Path("teams/modeling/modeling_projection_team.json")


def test_modeling_team_is_dedicated_model_placement_department():
    team = load_team_config(ROOT, TEAM_FILE)

    assert team.team_id == "TEAM_MODELING_PROJECTION"
    assert team.team_name == "Model Placement Team"
    assert team.consensus_required is False
    assert team.consensus_focus == [
        "selected_rule_id",
        "framework_level",
        "model_area",
        "element_type",
        "explicit_variance",
    ]

    assert len(team.members) == 3
    assert {
        member.persona_id for member in team.members
    } == {
        "PERSONA_MODELING_SYSML_PROFILE_MODELER",
        "PERSONA_MODELING_SYSTEM_ARCHITECTURE_MODELER",
        "PERSONA_MODELING_CONSERVATIVE_PLACEMENT_REVIEWER",
    }
    assert {
        member.perspective for member in team.members
    } == {
        "sysml_profile_placement",
        "architecture_level_placement",
        "conservative_placement_review",
    }

    persona_paths = {
        member.persona_file.relative_to(ROOT).as_posix()
        for member in team.members
    }
    assert persona_paths == {
        "agents/personas/modeling/sysml_profile_modeler.md",
        "agents/personas/modeling/system_architecture_modeler.md",
        "agents/personas/modeling/conservative_modeling_reviewer.md",
    }
    assert all("derivation_assessment" not in path for path in persona_paths)


def test_modeling_placement_personas_forbid_assembly_and_authority():
    team = load_team_config(ROOT, TEAM_FILE)

    for member in team.members:
        text = member.persona_file.read_text(encoding="utf-8")
        assert "Model Placement" in text
        assert "do not assemble the model" in text
        assert "do not approve a placement" in text


def test_modeling_placement_role_preserves_variance_for_human_review():
    team = load_team_config(ROOT, TEAM_FILE)
    text = team.role_file.read_text(encoding="utf-8")

    assert "placement" in text.lower()
    assert "does **not**" in text
    assert "assemble multiple placements into a model" in text
    assert "Persona agreement is advisory evidence only" in text


def test_model_placement_architecture_documents_are_present():
    adr = (
        ROOT
        / "collaboration/decisions/"
        "ADR-029-human-reviewed-model-placement-before-model-assembly.md"
    )
    contract = (
        ROOT
        / "collaboration/contracts/model_placement_review_contract.md"
    )

    adr_text = adr.read_text(encoding="utf-8")
    contract_text = contract.read_text(encoding="utf-8")

    assert "Human Model Placement Review" in adr_text
    assert "Approved Model Placement Set" in adr_text
    assert "Model Assembly" in adr_text
    assert "Consensus is not required." in contract_text
    assert "stakeholder.*" in contract_text
    assert "system.*" in contract_text
    assert "subsystem.*" in contract_text
