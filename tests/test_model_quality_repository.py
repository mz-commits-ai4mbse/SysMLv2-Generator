from types import SimpleNamespace
import json

import pytest

from modules.model_quality.contract import (
    build_refinement_request,
    create_refinement_bundle,
    parse_refinement_response,
)
from modules.model_quality.errors import ModelQualityError
from modules.model_quality.repository import ModelQualityRepository


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
    "element_profiles": {"function": {"rule_ids": ["GENERAL_MEANING"]}},
}


def _artifacts():
    element = SimpleNamespace(
        internal_model_element_id="IME-000001",
        approved_input_id="AEI-000001",
        model_subject_key="s-1",
        name="remote control",
        description="The remote expert may control the microscope.",
        element_type="function",
        model_area="functional",
        framework_assignment="FUN",
        content_fingerprint="1" * 64,
    )
    snapshot = SimpleNamespace(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
        content_fingerprint="2" * 64,
        elements=(element,),
    )
    request = build_refinement_request(
        snapshot=snapshot,
        quality_profile=PROFILE,
    )
    output = json.dumps(
        {
            "proposals": [
                {
                    "internal_model_element_id": "IME-000001",
                    "refined_name": "Control microscope remotely",
                    "refined_description": element.description,
                    "quality_findings": [],
                    "applied_rule_ids": ["GENERAL_MEANING"],
                    "meaning_preserved": True,
                    "unsupported_information_added": False,
                    "requires_human_attention": False,
                    "rationale": "Verb-object wording.",
                }
            ]
        }
    )
    proposals = parse_refinement_response(
        request=request,
        output_text=output,
    )
    bundle = create_refinement_bundle(
        request=request,
        review_id="MQR-000001",
        provider="openai",
        model="gpt-test",
        proposals=proposals,
        supporting_response_fingerprints=("a" * 64,),
        generated_at="2026-08-25T16:00:00Z",
    )
    return request, bundle


def test_review_decision_and_authority_persist_immutably(tmp_path):
    request, bundle = _artifacts()
    repo = ModelQualityRepository(tmp_path)
    repo.record_review(request=request, bundle=bundle)
    decision = repo.record_decision(
        bundle=bundle,
        internal_model_element_id="IME-000001",
        decision="approved",
        reviewer_identity="MZ",
        rationale="Reviewed.",
        decided_at="2026-08-25T16:10:00Z",
    )
    authority = repo.finalize(
        bundle=bundle,
        created_at="2026-08-25T16:20:00Z",
    )
    assert decision.decision_id == "MQD-000001"
    assert authority.authority_set_id == "MQA-000001"


def test_successor_decision_preserves_history(tmp_path):
    request, bundle = _artifacts()
    repo = ModelQualityRepository(tmp_path)
    repo.record_review(request=request, bundle=bundle)
    first = repo.record_decision(
        bundle=bundle,
        internal_model_element_id="IME-000001",
        decision="approved",
        reviewer_identity="MZ",
        rationale="First.",
        decided_at="2026-08-25T16:10:00Z",
    )
    second = repo.record_decision(
        bundle=bundle,
        internal_model_element_id="IME-000001",
        decision="overridden",
        approved_name="Control microscope",
        approved_description="The remote expert may control the microscope.",
        reviewer_identity="MZ",
        rationale="Cleaner wording.",
        decided_at="2026-08-25T16:11:00Z",
    )
    assert second.supersedes_decision_id == first.decision_id
    assert repo.effective_decisions(bundle) == (second,)


def test_review_directory_is_immutable(tmp_path):
    request, bundle = _artifacts()
    repo = ModelQualityRepository(tmp_path)
    repo.record_review(request=request, bundle=bundle)
    with pytest.raises(ModelQualityError, match="immutable"):
        repo.record_review(request=request, bundle=bundle)
