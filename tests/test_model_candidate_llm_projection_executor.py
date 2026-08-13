"""Tests for H9.5 bounded LLM target-projection execution."""

import json
from pathlib import Path

import pytest

from modules.agents.types import AgentRunResult
from modules.approved_input.manifest import create_approved_input_manifest
from modules.approved_input.types import ApprovedInputCanonicalContent
from modules.model_candidates import (
    ModelCandidateDerivationError,
    ModelCandidateDerivationRequest,
    ProfileDrivenModelCandidateDeriver,
    load_model_derivation_rules_reference,
    load_model_structure_profile,
    model_structure_profile_reference,
)
from modules.model_candidates.llm_projection_executor import (
    LLMProjectionBatchExecutor,
)
from modules.project_processing.types import ProcessingArtifactReference
from modules.project_workspace.types import FrameworkTemplateReference


PROJECT_ID = "318604"
A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64


def _artifact(number):
    return ProcessingArtifactReference(
        artifact_type="information_unit",
        artifact_id=f"IU-{number:06d}",
        content_fingerprint=A,
        repository_relative_path=(
            f"data/projects/{PROJECT_ID}/semantics/"
            f"information_units/IU-{number:06d}.json"
        ),
    )


def _input(number, *, classification, framework, information_type):
    return create_approved_input_manifest(
        project_id=PROJECT_ID,
        approved_input_id=f"AIN-{number:06d}",
        approved_input_kind="element_statement",
        canonical_content=ApprovedInputCanonicalContent(
            title=f"Input {number}",
            primary_text=f"Engineering statement {number}.",
            description=None,
            information_type=information_type,
            modality=None,
            epistemic_status="reviewed",
        ),
        selected_classification=classification,
        selected_framework_assignment=framework,
        selected_terminology_assignment=None,
        selected_source_assignments=("SRC-000001",),
        selected_relationship_representation=None,
        stable_subject_key=f"subject.{number}",
        review_document_id=f"RVD-{number:06d}",
        review_document_version_id=f"RVV-{number:06d}",
        review_revision_id=f"RVR-{number:06d}",
        review_item_id=f"RIT-{number:06d}",
        review_item_kind="element",
        review_item_fingerprint=A,
        finalized_artifact_set_fingerprint=B,
        finalization_decision_id=f"HRD-{number:06d}",
        finalization_decision_fingerprint=C,
        finalization_validation_fingerprint=D,
        source_id="SRC-000001",
        source_sha256=E,
        processing_run_id=f"RUN-{number:06d}",
        attempt_id="ATT-000001",
        primary_artifact_reference=_artifact(number),
        supporting_artifact_references=(),
        proposal_references=(),
        created_at="2026-08-13T19:30:00Z",
    )


def _setup(inputs):
    profile = load_model_structure_profile()
    rules = load_model_derivation_rules_reference()
    deriver = ProfileDrivenModelCandidateDeriver(
        profile=profile,
        derivation_rules_reference=rules,
    )
    request = ModelCandidateDerivationRequest(
        project_id=PROJECT_ID,
        approved_inputs=tuple(inputs),
        framework_template_reference=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        model_structure_profile_reference=(
            model_structure_profile_reference(profile)
        ),
        derivation_rules_reference=rules,
        predecessor_candidate_set=None,
    )
    coverage = deriver.assess_projection_coverage(request)
    return profile, request, coverage


def _mapped(number):
    return _input(
        number,
        classification="System Requirement",
        framework="System Requirements",
        information_type="requirement",
    )


def _ambiguous(number):
    return _input(
        number,
        classification="Function",
        framework=None,
        information_type="function",
    )


def _unmapped(number):
    return _input(
        number,
        classification="Mystery",
        framework=None,
        information_type="mystery",
    )


class FakeRunner:
    def __init__(self):
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        request = json.loads(kwargs["input_text"])
        proposals = []
        for item in request["items"]:
            options = item["allowed_target_options"]
            if item["deterministic"]["disposition"] == "ambiguous":
                proposals.append(
                    {
                        "approved_input_id": item["approved_input_id"],
                        "result": "proposed_mapping",
                        "selected_rule_id": options[0]["rule_id"],
                        "alternative_rule_ids": [],
                        "rationale": "Selected from supplied target options.",
                    }
                )
            else:
                proposals.append(
                    {
                        "approved_input_id": item["approved_input_id"],
                        "result": "unmapped",
                        "selected_rule_id": None,
                        "alternative_rule_ids": [],
                        "rationale": "No supplied target option is defensible.",
                    }
                )

        output_path = kwargs["output_dir"] / "fake.json"
        return AgentRunResult(
            agent_id=kwargs["agent_id"],
            task_name=kwargs["task_name"],
            run_index=1,
            provider=kwargs["provider"],
            model=kwargs["model"],
            output_text=json.dumps({"proposals": proposals}),
            output_path=output_path,
            response_id="resp_fake",
            usage={"input_tokens": 123, "output_tokens": 45},
            status="completed",
        )


def test_executor_skips_mapped_inputs_and_calls_only_for_unresolved(tmp_path):
    profile, request, coverage = _setup(
        (_mapped(1), _ambiguous(2), _unmapped(3))
    )
    runner = FakeRunner()
    executor = LLMProjectionBatchExecutor(
        project_root=Path("."),
        batch_size=8,
        agent_runner=runner,
    )

    invocations = executor.execute(
        request=request,
        coverage=coverage,
        profile=profile,
        output_dir=tmp_path,
    )

    assert len(runner.calls) == 1
    sent = json.loads(runner.calls[0]["input_text"])
    assert [
        item["approved_input_id"] for item in sent["items"]
    ] == ["AIN-000002", "AIN-000003"]
    assert len(invocations) == 1
    assert invocations[0].response_id == "resp_fake"
    assert invocations[0].usage == {
        "input_tokens": 123,
        "output_tokens": 45,
    }


def test_executor_batches_serially_and_preserves_order(tmp_path):
    inputs = tuple(_unmapped(index) for index in range(1, 6))
    profile, request, coverage = _setup(inputs)
    runner = FakeRunner()
    executor = LLMProjectionBatchExecutor(
        project_root=Path("."),
        batch_size=2,
        max_calls_per_run=3,
        agent_runner=runner,
    )

    invocations = executor.execute(
        request=request,
        coverage=coverage,
        profile=profile,
        output_dir=tmp_path,
    )

    assert len(runner.calls) == 3
    assert len(invocations) == 3
    assert [
        [
            item["approved_input_id"]
            for item in json.loads(call["input_text"])["items"]
        ]
        for call in runner.calls
    ] == [
        ["AIN-000001", "AIN-000002"],
        ["AIN-000003", "AIN-000004"],
        ["AIN-000005"],
    ]


def test_call_limit_blocks_before_first_llm_execution(tmp_path):
    inputs = tuple(_unmapped(index) for index in range(1, 6))
    profile, request, coverage = _setup(inputs)
    runner = FakeRunner()
    executor = LLMProjectionBatchExecutor(
        project_root=Path("."),
        batch_size=2,
        max_calls_per_run=2,
        agent_runner=runner,
    )

    with pytest.raises(ModelCandidateDerivationError):
        executor.execute(
            request=request,
            coverage=coverage,
            profile=profile,
            output_dir=tmp_path,
        )

    assert runner.calls == []


def test_no_unresolved_input_means_no_llm_call(tmp_path):
    profile, request, coverage = _setup((_mapped(1),))
    runner = FakeRunner()
    executor = LLMProjectionBatchExecutor(
        project_root=Path("."),
        agent_runner=runner,
    )

    result = executor.execute(
        request=request,
        coverage=coverage,
        profile=profile,
        output_dir=tmp_path,
    )

    assert result == ()
    assert runner.calls == []


def test_invalid_llm_response_fails_closed(tmp_path):
    profile, request, coverage = _setup((_ambiguous(1),))

    def bad_runner(**kwargs):
        return AgentRunResult(
            agent_id=kwargs["agent_id"],
            task_name=kwargs["task_name"],
            run_index=1,
            provider=kwargs["provider"],
            model=kwargs["model"],
            output_text=json.dumps(
                {
                    "proposals": [
                        {
                            "approved_input_id": "AIN-000001",
                            "result": "proposed_mapping",
                            "selected_rule_id": "HALLUCINATED_RULE",
                            "alternative_rule_ids": [],
                            "rationale": "Invalid.",
                        }
                    ]
                }
            ),
            output_path=tmp_path / "bad.json",
        )

    executor = LLMProjectionBatchExecutor(
        project_root=Path("."),
        agent_runner=bad_runner,
    )

    with pytest.raises(ModelCandidateDerivationError):
        executor.execute(
            request=request,
            coverage=coverage,
            profile=profile,
            output_dir=tmp_path,
        )


def test_runner_failure_is_not_retried(tmp_path):
    profile, request, coverage = _setup((_ambiguous(1),))
    calls = []

    def failing_runner(**kwargs):
        calls.append(kwargs)
        raise RuntimeError("provider unavailable")

    executor = LLMProjectionBatchExecutor(
        project_root=Path("."),
        agent_runner=failing_runner,
    )

    with pytest.raises(ModelCandidateDerivationError, match="no automatic retry"):
        executor.execute(
            request=request,
            coverage=coverage,
            profile=profile,
            output_dir=tmp_path,
        )

    assert len(calls) == 1
