from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import json

from modules.model_quality.contract import build_refinement_request
from modules.model_quality.executor import ModelQualityRefinementExecutor


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
        "function": {"rule_ids": ["GENERAL_MEANING", "FUNCTION_VERBAL"]}
    },
}


def _request():
    elements = tuple(
        SimpleNamespace(
            internal_model_element_id=f"IME-{index:06d}",
            approved_input_id=f"AEI-{index:06d}",
            model_subject_key=f"s-{index}",
            name=f"function {index}",
            description=f"do thing {index}",
            element_type="function",
            model_area="functional",
            framework_assignment="FUN",
            content_fingerprint=(str(index) * 64)[:64],
        )
        for index in range(1, 4)
    )
    snapshot = SimpleNamespace(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
        content_fingerprint="a" * 64,
        elements=elements,
    )
    return build_refinement_request(
        snapshot=snapshot,
        quality_profile=PROFILE,
    )


def _runner(**kwargs):
    data = json.loads(kwargs["input_text"])
    proposals = []
    for item in data["elements"]:
        proposals.append(
            {
                "internal_model_element_id": item["internal_model_element_id"],
                "refined_name": "Perform " + item["engineering_meaning"]["name"],
                "refined_description": item["engineering_meaning"]["description"],
                "quality_findings": ["Action wording normalized."],
                "applied_rule_ids": ["GENERAL_MEANING", "FUNCTION_VERBAL"],
                "meaning_preserved": True,
                "unsupported_information_added": False,
                "requires_human_attention": False,
                "rationale": "Preserves meaning.",
            }
        )
    return (
        SimpleNamespace(
            agent_id="AGENT_MODEL_QUALITY_REFINER",
            run_index=1,
            provider=kwargs["provider"],
            model=kwargs["model"],
            output_text=json.dumps({"proposals": proposals}),
        ),
    )


def _clock():
    return datetime(2026, 8, 25, 16, 0, tzinfo=timezone.utc)


def test_executor_batches_and_reports_visible_progress(tmp_path):
    progress = []
    executor = ModelQualityRefinementExecutor(
        project_root=tmp_path,
        provider="openai",
        model="gpt-test",
        batch_size=2,
        team_runner=_runner,
        clock=_clock,
    )
    bundle = executor.execute(
        request=_request(),
        review_id="MQR-000001",
        output_dir=tmp_path / "run",
        progress=progress.append,
    )
    assert len(bundle.proposals) == 3
    assert len(bundle.supporting_response_fingerprints) == 2
    assert any("batch 1/2" in item.lower() for item in progress)
    assert progress[-1].endswith("Human review required.")
