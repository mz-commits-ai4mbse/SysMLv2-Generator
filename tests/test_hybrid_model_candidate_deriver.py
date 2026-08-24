"""Tests for H9.6 HybridModelCandidateDeriver."""

import json
from pathlib import Path

import pytest

from modules.agents.types import AgentRunResult
from modules.approved_input.manifest import create_approved_input_manifest
from modules.approved_input.types import (
    ApprovedInputCanonicalContent,
    ApprovedInputRelationshipProperty,
    ApprovedInputRelationshipRepresentation,
)
from modules.model_candidates import (
    ModelCandidateDerivationError,
    ModelCandidateDerivationRequest,
    load_model_derivation_rules_reference,
    load_model_structure_profile,
    model_structure_profile_reference,
)
from modules.model_candidates.hybrid_deriver import (
    HybridModelCandidateDeriver,
)
from modules.model_candidates.llm_projection_executor import (
    LLMProjectionBatchExecutor,
)
from modules.model_candidates.modeling_persona_executor import (
    ModelingPersonaProjectionExecutor,
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


def _element(
    number,
    *,
    subject,
    title,
    classification,
    framework,
    information_type,
):
    return create_approved_input_manifest(
        project_id=PROJECT_ID,
        approved_input_id=f"AIN-{number:06d}",
        approved_input_kind="element_statement",
        canonical_content=ApprovedInputCanonicalContent(
            title=title,
            primary_text=f"{title} engineering statement.",
            description=f"{title} description.",
            information_type=information_type,
            modality=None,
            epistemic_status="reviewed",
        ),
        selected_classification=classification,
        selected_framework_assignment=framework,
        selected_terminology_assignment=None,
        selected_source_assignments=("SRC-000001",),
        selected_relationship_representation=None,
        stable_subject_key=subject,
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
        created_at="2026-08-13T20:00:00Z",
    )


def _relationship(number, *, intent="dependency"):
    relationship = ApprovedInputRelationshipRepresentation(
        source_subject_key="subject.source",
        target_subject_key="subject.target",
        semantic_intent=intent,
        sysml_v2_construct="dependency",
        construct_properties=(
            ApprovedInputRelationshipProperty(
                name="direction",
                value="source_to_target",
            ),
        ),
        target_notation_profile_id="SYSIDE_SYSML_V2",
        target_notation_profile_version="1.0.0",
        textual_notation_preview="relationship preview",
        profile_validation_status="valid",
        profile_validation_fingerprint=E,
    )
    return create_approved_input_manifest(
        project_id=PROJECT_ID,
        approved_input_id=f"AIN-{number:06d}",
        approved_input_kind="relationship_statement",
        canonical_content=ApprovedInputCanonicalContent(
            title="Relationship",
            primary_text="Source relates to target.",
            description=None,
            information_type="relationship",
            modality=None,
            epistemic_status="reviewed",
        ),
        selected_classification=None,
        selected_framework_assignment=None,
        selected_terminology_assignment=None,
        selected_source_assignments=("SRC-000001",),
        selected_relationship_representation=relationship,
        stable_subject_key=f"relationship.{number}",
        review_document_id=f"RVD-{number:06d}",
        review_document_version_id=f"RVV-{number:06d}",
        review_revision_id=f"RVR-{number:06d}",
        review_item_id=f"RIT-{number:06d}",
        review_item_kind="relationship",
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
        created_at="2026-08-13T20:00:00Z",
    )


def _request(inputs):
    profile = load_model_structure_profile()
    rules = load_model_derivation_rules_reference()
    return (
        profile,
        rules,
        ModelCandidateDerivationRequest(
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
        ),
    )


class MappingRunner:
    def __init__(self, *, unmapped_ids=()):
        self.calls = []
        self.unmapped_ids = set(unmapped_ids)

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        payload = json.loads(kwargs["input_text"])
        proposals = []
        for item in payload["items"]:
            input_id = item["approved_input_id"]
            options = item["allowed_target_options"]
            if input_id in self.unmapped_ids:
                proposal = {
                    "approved_input_id": input_id,
                    "result": "unmapped",
                    "selected_rule_id": None,
                    "alternative_rule_ids": [],
                    "rationale": "No defensible target mapping.",
                }
            elif any(
                option["rule_id"] == "relationship:dependency"
                for option in options
            ):
                selected = "relationship:dependency"
                proposal = {
                    "approved_input_id": input_id,
                    "result": "proposed_mapping",
                    "selected_rule_id": selected,
                    "alternative_rule_ids": [],
                    "rationale": "Dependency is the best supplied semantic.",
                }
            else:
                selected = options[0]["rule_id"]
                proposal = {
                    "approved_input_id": input_id,
                    "result": "proposed_mapping",
                    "selected_rule_id": selected,
                    "alternative_rule_ids": [],
                    "rationale": "Selected from the supplied target options.",
                }
            proposals.append(proposal)

        return AgentRunResult(
            agent_id=kwargs["agent_id"],
            task_name=kwargs["task_name"],
            run_index=1,
            provider=kwargs["provider"],
            model=kwargs["model"],
            output_text=json.dumps({"proposals": proposals}),
            output_path=kwargs["output_dir"] / "fake.json",
            response_id="resp_hybrid",
            usage={"input_tokens": 100, "output_tokens": 20},
            status="completed",
        )


def _hybrid(profile, rules, runner, tmp_path):
    executor = LLMProjectionBatchExecutor(
        project_root=Path("."),
        batch_size=8,
        agent_runner=runner,
    )
    return HybridModelCandidateDeriver(
        profile=profile,
        derivation_rules_reference=rules,
        executor=executor,
        output_dir=tmp_path,
    )


def test_all_deterministic_snapshot_uses_zero_llm_calls(tmp_path):
    source = _element(
        1,
        subject="subject.source",
        title="Requirement",
        classification="System Requirement",
        framework="System Requirements",
        information_type="requirement",
    )
    profile, rules, request = _request((source,))
    runner = MappingRunner()
    deriver = _hybrid(profile, rules, runner, tmp_path)

    plan = deriver.derive(request)

    assert len(plan.element_drafts) == 1
    assert runner.calls == []
    assert deriver.last_invocations == ()


def test_ambiguous_element_is_mapped_by_llm_but_keeps_original_evidence(tmp_path):
    item = _element(
        1,
        subject="subject.function",
        title="Function",
        classification="Function",
        framework=None,
        information_type="function",
    )
    profile, rules, request = _request((item,))
    runner = MappingRunner()
    deriver = _hybrid(profile, rules, runner, tmp_path)

    plan = deriver.derive(request)

    assert len(runner.calls) == 1
    assert len(plan.element_drafts) == 1
    draft = plan.element_drafts[0]
    assert draft.support_level == "partially_supported"
    assert draft.structure_profile_conformance.status == "conformant"
    assert draft.structure_profile_conformance.finding_ids == ()
    attributes = {item.name: item.value for item in draft.attributes}
    assert attributes["source_classification"] == "Function"
    assert "source_framework_assignment" not in attributes
    assert "LLM-assisted target projection" in draft.derivation_rationale


def test_llm_unmapped_result_blocks_candidate_generation_without_forcing(tmp_path):
    item = _element(
        1,
        subject="subject.mystery",
        title="Mystery",
        classification="Mystery",
        framework=None,
        information_type="mystery",
    )
    profile, rules, request = _request((item,))
    runner = MappingRunner(unmapped_ids=("AIN-000001",))
    deriver = _hybrid(profile, rules, runner, tmp_path)

    with pytest.raises(
        ModelCandidateDerivationError,
        match="preserved unresolved engineering information",
    ):
        deriver.derive(request)


def test_relationship_is_recomputed_after_llm_element_mapping(tmp_path):
    source = _element(
        1,
        subject="subject.source",
        title="Requirement",
        classification="System Requirement",
        framework="System Requirements",
        information_type="requirement",
    )
    target = _element(
        2,
        subject="subject.target",
        title="Function",
        classification="Function",
        framework=None,
        information_type="function",
    )
    relationship = _relationship(3, intent="dependency")
    profile, rules, request = _request((source, target, relationship))
    runner = MappingRunner()
    deriver = _hybrid(profile, rules, runner, tmp_path)

    plan = deriver.derive(request)

    assert len(plan.relationship_drafts) == 1
    draft = plan.relationship_drafts[0]
    assert draft.semantic_intent == "dependency"
    assert draft.missing_information == ()


def test_unknown_relationship_semantic_can_be_projected_without_overwriting_upstream(tmp_path):
    source = _element(
        1,
        subject="subject.source",
        title="Requirement",
        classification="System Requirement",
        framework="System Requirements",
        information_type="requirement",
    )
    target = _element(
        2,
        subject="subject.target",
        title="Component",
        classification="Logical Component",
        framework="System Logical",
        information_type="component",
    )
    relationship = _relationship(3, intent="mystery_relation")
    original = relationship.selected_relationship_representation
    profile, rules, request = _request((source, target, relationship))
    runner = MappingRunner()
    deriver = _hybrid(profile, rules, runner, tmp_path)

    plan = deriver.derive(request)

    assert len(plan.relationship_drafts) == 1
    draft = plan.relationship_drafts[0]
    assert draft.semantic_intent == "dependency"
    assert draft.priority_assessment.priority_class == "supported_alternative"
    assert draft.structure_profile_conformance.status == "conformant"
    assert draft.upstream_relationship_representation == original
    assert (
        draft.upstream_relationship_representation.semantic_intent
        == "mystery_relation"
    )
    assert "LLM-assisted target projection" in draft.derivation_rationale


class PersonaProjectionRunner:
    def __init__(self, *, divergent_agent_id=None):
        self.calls = []
        self.divergent_agent_id = divergent_agent_id

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        payload = json.loads(kwargs["input_text"])
        agent_ids = (
            "AGENT_MODELING_RULES_FOCUSED_ADVISOR",
            "AGENT_MODELING_ARCHITECTURE_FOCUSED_ADVISOR",
            "AGENT_MODELING_CONSERVATIVE_REVIEWER",
        )
        results = []

        for index, agent_id in enumerate(agent_ids, start=1):
            proposals = []
            for item in payload["items"]:
                options = item["allowed_target_options"]
                selected_index = 0
                if (
                    agent_id == self.divergent_agent_id
                    and len(options) > 1
                ):
                    selected_index = 1

                proposals.append(
                    {
                        "approved_input_id": item["approved_input_id"],
                        "result": "proposed_mapping",
                        "selected_rule_id": (
                            options[selected_index]["rule_id"]
                        ),
                        "alternative_rule_ids": [],
                        "rationale": (
                            "Selected from identical profile-controlled "
                            "target options."
                        ),
                    }
                )

            results.append(
                AgentRunResult(
                    agent_id=agent_id,
                    task_name=(
                        "Assess target-model projection of "
                        "Approved Engineering Information"
                    ),
                    run_index=1,
                    provider=kwargs["provider"],
                    model=kwargs["model"],
                    output_text=json.dumps(
                        {"proposals": proposals}
                    ),
                    output_path=(
                        kwargs["output_dir"]
                        / f"persona_{index}.json"
                    ),
                    response_id=f"resp_persona_{index}",
                    usage={
                        "input_tokens": 50,
                        "output_tokens": 10,
                    },
                    status="completed",
                )
            )

        return results


def _persona_hybrid(
    profile,
    rules,
    runner,
    tmp_path,
    *,
    escalation_ids=(),
):
    executor = ModelingPersonaProjectionExecutor(
        project_root=Path("."),
        batch_size=8,
        team_runner=runner,
    )
    return HybridModelCandidateDeriver(
        profile=profile,
        derivation_rules_reference=rules,
        executor=executor,
        output_dir=tmp_path,
        review_escalation_approved_input_ids=(
            escalation_ids
        ),
    )


def test_modeling_personas_unanimous_mapping_generates_candidate(tmp_path):
    item = _element(
        1,
        subject="subject.function",
        title="Function",
        classification="Function",
        framework=None,
        information_type="function",
    )
    profile, rules, request = _request((item,))
    runner = PersonaProjectionRunner()
    deriver = _persona_hybrid(
        profile,
        rules,
        runner,
        tmp_path,
    )

    plan = deriver.derive(request)

    assert len(runner.calls) == 1
    assert len(plan.element_drafts) == 1
    assert len(deriver.last_invocations) == 1
    invocation = deriver.last_invocations[0]
    assert len(invocation.supporting_agent_ids) == 3
    assert len(invocation.supporting_response_fingerprints) == 3
    assert (
        invocation.response.proposals[0].result
        == "proposed_mapping"
    )


def test_modeling_persona_variance_remains_unresolved(tmp_path):
    item = _element(
        1,
        subject="subject.mystery",
        title="Mystery",
        classification="Mystery",
        framework=None,
        information_type="mystery",
    )
    profile, rules, request = _request((item,))
    runner = PersonaProjectionRunner(
        divergent_agent_id=(
            "AGENT_MODELING_ARCHITECTURE_FOCUSED_ADVISOR"
        )
    )
    deriver = _persona_hybrid(
        profile,
        rules,
        runner,
        tmp_path,
    )

    with pytest.raises(
        ModelCandidateDerivationError,
        match="preserved unresolved engineering information",
    ):
        deriver.derive(request)

    assert len(runner.calls) == 1
    proposal = (
        deriver.last_invocations[0].response.proposals[0]
    )
    assert proposal.result == "ambiguous"
    assert len(proposal.alternative_rule_ids) >= 2


def test_review_escalation_reconsiders_mapped_input_with_personas(
    tmp_path,
):
    item = _element(
        1,
        subject="subject.requirement",
        title="Requirement",
        classification="System Requirement",
        framework="System Requirements",
        information_type="requirement",
    )
    profile, rules, request = _request((item,))
    runner = PersonaProjectionRunner()
    deriver = _persona_hybrid(
        profile,
        rules,
        runner,
        tmp_path,
        escalation_ids=("AIN-000001",),
    )

    plan = deriver.derive(request)

    assert len(plan.element_drafts) == 1
    assert len(runner.calls) == 1

    payload = json.loads(runner.calls[0]["input_text"])
    sent = payload["items"][0]
    assert sent["approved_input_id"] == "AIN-000001"
    assert sent["review_escalation"] is True
    assert sent["deterministic"]["disposition"] == "mapped"
    assert len(sent["allowed_target_options"]) > 1
    assert (
        "LLM-assisted target projection"
        in plan.element_drafts[0].derivation_rationale
    )
