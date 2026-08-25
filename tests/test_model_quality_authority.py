from types import SimpleNamespace
import json

import pytest

from modules.model_quality.authority import (
    create_quality_authority_set,
    create_quality_decision,
)
from modules.model_quality.contract import (
    build_refinement_request,
    create_refinement_bundle,
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
    "element_profiles": {"*": {"rule_ids": ["GENERAL_MEANING"]}},
}


def _snapshot():
    elements = []
    for index in range(1, 3):
        elements.append(
            SimpleNamespace(
                internal_model_element_id=f"IME-{index:06d}",
                approved_input_id=f"AEI-{index:06d}",
                model_subject_key=f"s-{index}",
                name=f"name {index}",
                description=f"description {index}",
                element_type="function",
                model_area="functional",
                framework_assignment="FUN",
                content_fingerprint=f"{index}" * 64,
            )
        )
    return SimpleNamespace(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
        content_fingerprint="a" * 64,
        elements=tuple(elements),
    )


def _bundle():
    request = build_refinement_request(
        snapshot=_snapshot(),
        quality_profile=PROFILE,
    )
    response = {
        "proposals": [
            {
                "internal_model_element_id": item.internal_model_element_id,
                "refined_name": f"Perform function {index}",
                "refined_description": item.original_description,
                "quality_findings": [],
                "applied_rule_ids": ["GENERAL_MEANING"],
                "meaning_preserved": True,
                "unsupported_information_added": False,
                "requires_human_attention": False,
                "rationale": "Meaning preserved.",
            }
            for index, item in enumerate(request.elements, start=1)
        ]
    }
    proposals = parse_refinement_response(
        request=request,
        output_text=json.dumps(response),
    )
    return create_refinement_bundle(
        request=request,
        review_id="MQR-000001",
        provider="openai",
        model="gpt-test",
        proposals=proposals,
        supporting_response_fingerprints=("b" * 64,),
        generated_at="2026-08-25T16:00:00Z",
    )


def test_human_approval_uses_exact_proposed_wording():
    bundle = _bundle()
    decision = create_quality_decision(
        bundle=bundle,
        decision_id="MQD-000001",
        internal_model_element_id="IME-000001",
        decision="approved",
        reviewer_identity="MZ",
        rationale="Reviewed.",
        decided_at="2026-08-25T16:10:00Z",
    )
    assert decision.approved_name == bundle.proposals[0].refined_name


def test_human_override_is_explicit_authority():
    bundle = _bundle()
    decision = create_quality_decision(
        bundle=bundle,
        decision_id="MQD-000001",
        internal_model_element_id="IME-000001",
        decision="overridden",
        approved_name="Control microscope",
        approved_description="Control the microscope remotely.",
        reviewer_identity="MZ",
        rationale="Use clearer action wording.",
        decided_at="2026-08-25T16:10:00Z",
    )
    assert decision.approved_name == "Control microscope"


def test_reject_blocks_complete_authority():
    bundle = _bundle()
    decisions = (
        create_quality_decision(
            bundle=bundle,
            decision_id="MQD-000001",
            internal_model_element_id="IME-000001",
            decision="rejected",
            reviewer_identity="MZ",
            rationale="Wrong classification.",
            decided_at="2026-08-25T16:10:00Z",
        ),
        create_quality_decision(
            bundle=bundle,
            decision_id="MQD-000002",
            internal_model_element_id="IME-000002",
            decision="approved",
            reviewer_identity="MZ",
            rationale="Reviewed.",
            decided_at="2026-08-25T16:11:00Z",
        ),
    )
    with pytest.raises(ModelQualityError, match="Rejected"):
        create_quality_authority_set(
            bundle=bundle,
            authority_set_id="MQA-000001",
            effective_decisions=decisions,
            created_at="2026-08-25T16:20:00Z",
        )
