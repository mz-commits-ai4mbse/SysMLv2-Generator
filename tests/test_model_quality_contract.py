from types import SimpleNamespace
import json

import pytest

from modules.model_quality.contract import (
    build_refinement_request,
    parse_refinement_response,
)
from modules.model_quality.errors import ModelQualityError


PROFILE = {
    "profile_id": "TURING_MODEL_QUALITY",
    "profile_version": "1.0.0",
    "rules": {
        "GENERAL_MEANING": "Preserve meaning.",
        "GENERAL_CONCISE": "Use concise wording.",
        "REQ_LEVEL": "Preserve requirement level.",
        "REQ_BINDING": "Use binding requirement wording.",
        "FUNCTION_VERBAL": "Use active verb-object wording.",
    },
    "element_profiles": {
        "system_requirement": {
            "rule_ids": ["GENERAL_MEANING", "REQ_LEVEL", "REQ_BINDING"]
        },
        "function": {
            "rule_ids": ["GENERAL_MEANING", "FUNCTION_VERBAL"]
        },
        "*": {"rule_ids": ["GENERAL_MEANING"]},
    },
}


def _element(element_type="system_requirement"):
    return SimpleNamespace(
        internal_model_element_id="IME-000001",
        approved_input_id="AEI-000001",
        model_subject_key="subject-1",
        name="understand control",
        description="Users must be able to understand who controls the microscope.",
        element_type=element_type,
        model_area="system",
        framework_assignment="REQ_SYSTEM",
        content_fingerprint="1" * 64,
    )


def _snapshot(element_type="system_requirement"):
    return SimpleNamespace(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
        content_fingerprint="2" * 64,
        elements=(_element(element_type),),
    )


def test_request_binds_exact_classification_and_quality_rules():
    request = build_refinement_request(
        snapshot=_snapshot(),
        quality_profile=PROFILE,
    )
    item = request.elements[0]
    assert item.element_type == "system_requirement"
    assert item.quality_rule_ids == (
        "GENERAL_MEANING",
        "REQ_LEVEL",
        "REQ_BINDING",
    )
    assert item.quality_rule_texts == (
        "Preserve meaning.",
        "Preserve requirement level.",
        "Use binding requirement wording.",
    )


def test_classification_change_invalidates_refinement_request():
    system = build_refinement_request(
        snapshot=_snapshot("system_requirement"),
        quality_profile=PROFILE,
    )
    function = build_refinement_request(
        snapshot=_snapshot("function"),
        quality_profile=PROFILE,
    )
    assert system.request_fingerprint != function.request_fingerprint
    assert (
        system.elements[0].classification_fingerprint
        != function.elements[0].classification_fingerprint
    )


def test_response_is_exactly_bound_and_preserves_no_invention_flag():
    request = build_refinement_request(
        snapshot=_snapshot(),
        quality_profile=PROFILE,
    )
    output = json.dumps(
        {
            "proposals": [
                {
                    "internal_model_element_id": "IME-000001",
                    "refined_name": "Indicate current microscope controller",
                    "refined_description": (
                        "The system shall indicate the current microscope "
                        "controller to the user."
                    ),
                    "quality_findings": [
                        "Converted weak user-oriented wording into a binding "
                        "system-level statement without adding criteria."
                    ],
                    "applied_rule_ids": [
                        "GENERAL_MEANING",
                        "REQ_LEVEL",
                        "REQ_BINDING",
                    ],
                    "meaning_preserved": True,
                    "unsupported_information_added": False,
                    "requires_human_attention": False,
                    "rationale": "Preserves the approved system-level obligation.",
                }
            ]
        }
    )
    proposals = parse_refinement_response(
        request=request,
        output_text=output,
    )
    assert proposals[0].refined_description.startswith("The system shall")


def test_unsupported_information_must_raise_human_attention():
    request = build_refinement_request(
        snapshot=_snapshot(),
        quality_profile=PROFILE,
    )
    output = json.dumps(
        {
            "proposals": [
                {
                    "internal_model_element_id": "IME-000001",
                    "refined_name": "Indicate current controller within 100 ms",
                    "refined_description": "The system shall indicate the controller within 100 ms.",
                    "quality_findings": ["Invented performance criterion."],
                    "applied_rule_ids": ["GENERAL_MEANING"],
                    "meaning_preserved": True,
                    "unsupported_information_added": True,
                    "requires_human_attention": False,
                    "rationale": "Bad output.",
                }
            ]
        }
    )
    with pytest.raises(ModelQualityError, match="Human attention"):
        parse_refinement_response(
            request=request,
            output_text=output,
        )
