import json
from pathlib import Path
from types import SimpleNamespace

from modules.model_candidates.llm_projection_contract import (
    LLMProjectionInputItem,
    LLMProjectionRequest,
    LLMProjectionTargetOption,
)
from modules.model_placement.persona_executor import (
    ModelPlacementPersonaExecutor,
)


def _request():
    options = (
        LLMProjectionTargetOption(
            rule_id="ELEMENT_SYSTEM_FUNCTION",
            target_kind="element",
            model_area="system.functional",
            element_type="function",
            framework_assignment="FW_SYSTEM_FUNCTIONAL",
            relationship_family=None,
            semantic_intent=None,
            directionality=None,
        ),
        LLMProjectionTargetOption(
            rule_id="ELEMENT_SUBSYSTEM_FUNCTION",
            target_kind="element",
            model_area="subsystem.functional",
            element_type="function",
            framework_assignment="FW_SUBSYSTEM_FUNCTIONAL",
            relationship_family=None,
            semantic_intent=None,
            directionality=None,
        ),
    )
    item = LLMProjectionInputItem(
        approved_input_id="AIN-000001",
        approved_input_kind="element_statement",
        stable_subject_key="subject:subj-001",
        title="Share live view",
        primary_text="Share live view.",
        description=None,
        information_type="function",
        reviewed_classification=None,
        reviewed_framework_assignment=None,
        deterministic_disposition="ambiguous",
        deterministic_reason_code="multiple",
        deterministic_candidate_rule_ids=(
            "ELEMENT_SYSTEM_FUNCTION",
            "ELEMENT_SUBSYSTEM_FUNCTION",
        ),
        review_escalation=False,
        allowed_target_options=options,
    )
    return LLMProjectionRequest(
        project_id="120412",
        profile_id="TURING_MODEL_STRUCTURE",
        profile_version="1.0.0",
        profile_fingerprint="a" * 64,
        items=(item,),
        request_fingerprint="b" * 64,
    )


def _runner(**kwargs):
    payloads = {
        "AGENT_MODELING_RULES_FOCUSED_ADVISOR": {
            "result": "proposed_mapping",
            "selected_rule_id": "ELEMENT_SYSTEM_FUNCTION",
            "alternative_rule_ids": [],
        },
        "AGENT_MODELING_ARCHITECTURE_FOCUSED_ADVISOR": {
            "result": "proposed_mapping",
            "selected_rule_id": "ELEMENT_SUBSYSTEM_FUNCTION",
            "alternative_rule_ids": [],
        },
        "AGENT_MODELING_CONSERVATIVE_REVIEWER": {
            "result": "unmapped",
            "selected_rule_id": None,
            "alternative_rule_ids": [],
        },
    }
    return tuple(
        SimpleNamespace(
            agent_id=agent_id,
            run_index=1,
            output_text=json.dumps(
                {
                    "proposals": [
                        {
                            "approved_input_id": "AIN-000001",
                            **values,
                            "rationale": "bounded placement rationale",
                        }
                    ]
                }
            ),
        )
        for agent_id, values in payloads.items()
    )


def test_executor_preserves_three_persona_variance_for_human_review(tmp_path):
    executor = ModelPlacementPersonaExecutor(
        project_root=Path("."),
        team_runner=_runner,
    )

    comparison = executor.execute(
        request=_request(),
        output_dir=tmp_path,
    )

    assert comparison.human_review_required is True
    assert comparison.items[0].agreement_level == "placement_variance"
    assert comparison.items[0].unanimous_rule_id is None
    assert len(comparison.items[0].persona_proposals) == 3
    assert (tmp_path / "model_placement_execution.json").is_file()
