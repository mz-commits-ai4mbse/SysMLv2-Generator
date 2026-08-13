"""H9.7 integration: Hybrid projection -> Candidate Set -> Human Review -> Phase I."""

from datetime import datetime, timezone
import json
from pathlib import Path

from modules.agents.types import AgentRunResult
from modules.approved_input.manifest import create_approved_input_manifest
from modules.approved_input.types import ApprovedInputCanonicalContent
from modules.model_candidates import (
    HybridModelCandidateDeriver,
    ModelCandidateGenerationService,
    ModelCandidateReadService,
    ModelCandidateRepository,
    ModelCandidateReviewRepository,
    load_model_derivation_rules_reference,
    load_model_structure_profile,
    model_structure_profile_reference,
)
from modules.model_candidates.llm_projection_executor import (
    LLMProjectionBatchExecutor,
)
from modules.project_processing.types import ProcessingArtifactReference
from modules.project_workspace import ProjectWorkspace


PROJECT_ID = "318604"
A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64


def _clock():
    return datetime(2026, 8, 13, 18, 0, tzinfo=timezone.utc)


def _artifact():
    return ProcessingArtifactReference(
        artifact_type="information_unit",
        artifact_id="IU-000001",
        content_fingerprint=A,
        repository_relative_path=(
            f"data/projects/{PROJECT_ID}/semantics/"
            "information_units/IU-000001.json"
        ),
    )


def _ambiguous_function():
    return create_approved_input_manifest(
        project_id=PROJECT_ID,
        approved_input_id="AIN-000001",
        approved_input_kind="element_statement",
        canonical_content=ApprovedInputCanonicalContent(
            title="Coordinate validation",
            primary_text="The system coordinates architecture validation.",
            description="Reviewed system-level behavior.",
            information_type="function",
            modality=None,
            epistemic_status="reviewed",
        ),
        selected_classification="Function",
        selected_framework_assignment=None,
        selected_terminology_assignment=None,
        selected_source_assignments=("SRC-000001",),
        selected_relationship_representation=None,
        stable_subject_key="function.coordinate_validation",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        review_item_id="RIT-000001",
        review_item_kind="element",
        review_item_fingerprint=A,
        finalized_artifact_set_fingerprint=B,
        finalization_decision_id="HRD-000001",
        finalization_decision_fingerprint=C,
        finalization_validation_fingerprint=D,
        source_id="SRC-000001",
        source_sha256=E,
        processing_run_id="RUN-000001",
        attempt_id="ATT-000001",
        primary_artifact_reference=_artifact(),
        supporting_artifact_references=(),
        proposal_references=(),
        created_at="2026-08-13T17:55:00Z",
    )


class _ActiveApprovedInputs:
    def __init__(self, items):
        self.items = tuple(items)

    def list_active_approved_inputs(self, project_id):
        assert project_id == PROJECT_ID
        return self.items


class _MappingRunner:
    def __init__(self):
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        payload = json.loads(kwargs["input_text"])
        item = payload["items"][0]
        offered = {
            option["rule_id"]
            for option in item["allowed_target_options"]
        }
        assert "ELEMENT_SYSTEM_FUNCTION" in offered

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
                            "approved_input_id": item["approved_input_id"],
                            "result": "proposed_mapping",
                            "selected_rule_id": "ELEMENT_SYSTEM_FUNCTION",
                            "alternative_rule_ids": [],
                            "rationale": (
                                "The reviewed behavior is system-level and "
                                "matches the offered system function target."
                            ),
                        }
                    ]
                }
            ),
            output_path=kwargs["output_dir"] / "fake.json",
            response_id="resp_h9_7",
            usage={"input_tokens": 111, "output_tokens": 31},
            status="completed",
        )


def test_hybrid_generation_provenance_survives_review_and_phase_i(tmp_path):
    approved = _ambiguous_function()
    active = _ActiveApprovedInputs((approved,))

    workspace = ProjectWorkspace(
        root=tmp_path,
        id_generator=lambda: PROJECT_ID,
        clock=_clock,
    )
    workspace.create_project("H9 Hybrid Integration")

    candidates = ModelCandidateRepository(root=tmp_path)
    profile = load_model_structure_profile()
    rules = load_model_derivation_rules_reference()
    runner = _MappingRunner()

    executor = LLMProjectionBatchExecutor(
        project_root=Path("."),
        provider="openai",
        model="gpt-5.5",
        batch_size=8,
        max_calls_per_run=1,
        agent_runner=runner,
    )
    deriver = HybridModelCandidateDeriver(
        profile=profile,
        derivation_rules_reference=rules,
        executor=executor,
        output_dir=tmp_path / "agent_runs",
    )
    generation = ModelCandidateGenerationService(
        root=tmp_path,
        approved_input_repository=active,
        candidate_repository=candidates,
        workspace=workspace,
        clock=_clock,
    )

    snapshot = generation.generate_candidate_set(
        PROJECT_ID,
        deriver=deriver,
        model_structure_profile_reference=(
            model_structure_profile_reference(profile)
        ),
        derivation_rules_reference=rules,
        generation_provenance=None,
    )

    assert len(runner.calls) == 1
    assert len(snapshot.element_candidates) == 1
    candidate = snapshot.element_candidates[0]
    assert candidate.element_type == "function"
    assert candidate.model_area == "system.functional"
    assert candidate.support_level == "partially_supported"

    # H9 semantic uncertainty is not a structural profile exception:
    # the LLM could only select a profile-allowed target rule.
    assert candidate.structure_profile_conformance.status == "conformant"
    assert candidate.structure_profile_conformance.finding_ids == ()

    provenance = snapshot.manifest.generation_provenance
    assert provenance.method == "llm_assisted_profile_projection"
    assert provenance.recipe_reference == "ADR-020:H9"
    assert provenance.agent_reference == "agents/target_projection_mapper.md"
    assert provenance.model_reference == "openai:gpt-5.5"
    assert provenance.context_fingerprint is not None
    assert len(provenance.context_fingerprint) == 64

    reviews = ModelCandidateReviewRepository(
        root=tmp_path,
        candidate_repository=candidates,
        clock=_clock,
    )
    reviews.record_decision(
        PROJECT_ID,
        snapshot.manifest.candidate_set_id,
        target_type="element_candidate",
        candidate_id=candidate.model_element_candidate_id,
        decision="accepted",
        reviewer_identity="moritz",
    )

    phase_i = ModelCandidateReadService(
        root=tmp_path,
        candidate_repository=candidates,
        review_repository=reviews,
        approved_input_repository=active,
    )
    assembly_input = phase_i.load_phase_i_input(
        PROJECT_ID,
        snapshot.manifest.candidate_set_id,
    )

    assert len(assembly_input.accepted_element_candidates) == 1
    assert (
        assembly_input.accepted_element_candidates[0].content_fingerprint
        == candidate.content_fingerprint
    )
    assert assembly_input.generation_provenance == provenance
    assert assembly_input.accepted_exception_decisions == ()
