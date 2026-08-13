"""Tests for the H9.4 structured LLM target-projection contract."""

import json

import pytest

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
from modules.model_candidates.llm_projection_contract import (
    DEFAULT_LLM_PROJECTION_BATCH_SIZE,
    LLM_PROJECTION_TASK_INSTRUCTIONS,
    build_llm_projection_request,
    llm_projection_request_to_compact_json,
    parse_llm_projection_response,
)
from modules.project_processing.types import ProcessingArtifactReference
from modules.project_workspace.types import FrameworkTemplateReference


PROJECT_ID = "318604"
A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64


def _artifact(number: int) -> ProcessingArtifactReference:
    return ProcessingArtifactReference(
        artifact_type="information_unit",
        artifact_id=f"IU-{number:06d}",
        content_fingerprint=A,
        repository_relative_path=(
            f"data/projects/{PROJECT_ID}/semantics/"
            f"information_units/IU-{number:06d}.json"
        ),
    )


def _input(
    number: int,
    *,
    subject: str,
    title: str,
    classification: str | None,
    framework: str | None,
    information_type: str | None,
):
    return create_approved_input_manifest(
        project_id=PROJECT_ID,
        approved_input_id=f"AIN-{number:06d}",
        approved_input_kind="element_statement",
        canonical_content=ApprovedInputCanonicalContent(
            title=title,
            primary_text=f"{title} source statement.",
            description=f"{title} reviewed description.",
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
        created_at="2026-08-13T19:00:00Z",
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


def _ambiguous(number=1):
    return _input(
        number,
        subject=f"subject.function.{number}",
        title="Function",
        classification="Function",
        framework=None,
        information_type="function",
    )


def _unmapped(number=2):
    return _input(
        number,
        subject=f"subject.mystery.{number}",
        title="Mystery",
        classification="Mystery",
        framework=None,
        information_type="mystery",
    )


def test_contract_instructions_forbid_forced_mapping_and_sysml_generation():
    assert "Prefer unmapped over forcing" in LLM_PROJECTION_TASK_INSTRUCTIONS
    assert "Do not generate SysML v2 code." in LLM_PROJECTION_TASK_INSTRUCTIONS
    assert "Do not expose chain-of-thought" in LLM_PROJECTION_TASK_INSTRUCTIONS


def test_request_contains_only_unresolved_inputs_and_compact_profile_options():
    profile, request, coverage = _setup(
        (_ambiguous(1), _unmapped(2))
    )

    llm_request = build_llm_projection_request(
        request=request,
        coverage=coverage,
        profile=profile,
    )

    assert tuple(
        item.approved_input_id for item in llm_request.items
    ) == ("AIN-000001", "AIN-000002")
    assert len(llm_request.request_fingerprint) == 64

    ambiguous = llm_request.items[0]
    assert ambiguous.deterministic_disposition == "ambiguous"
    assert {
        item.rule_id for item in ambiguous.allowed_target_options
    } == {
        "ELEMENT_SUBSYSTEM_FUNCTION",
        "ELEMENT_SYSTEM_FUNCTION",
    }

    unmapped = llm_request.items[1]
    assert unmapped.deterministic_disposition == "unmapped"
    assert len(unmapped.allowed_target_options) == len(
        profile.element_derivation_rules
    )

    compact = llm_projection_request_to_compact_json(llm_request)
    assert "\n" not in compact
    payload = json.loads(compact)
    assert "profile_fingerprint" not in compact
    assert len(payload["items"]) == 2


def test_mapped_input_cannot_be_sent_to_llm():
    mapped = _input(
        1,
        subject="subject.requirement",
        title="Requirement",
        classification="System Requirement",
        framework="System Requirements",
        information_type="requirement",
    )
    profile, request, coverage = _setup((mapped,))

    with pytest.raises(ModelCandidateDerivationError):
        build_llm_projection_request(
            request=request,
            coverage=coverage,
            profile=profile,
            approved_input_ids=("AIN-000001",),
        )


def test_request_batch_is_bounded_before_any_llm_call():
    inputs = tuple(_unmapped(index) for index in range(1, 10))
    profile, request, coverage = _setup(inputs)

    with pytest.raises(ModelCandidateDerivationError):
        build_llm_projection_request(
            request=request,
            coverage=coverage,
            profile=profile,
            max_batch_size=DEFAULT_LLM_PROJECTION_BATCH_SIZE,
        )


def test_valid_proposed_mapping_response_is_accepted_and_fingerprinted():
    profile, request, coverage = _setup((_ambiguous(1),))
    llm_request = build_llm_projection_request(
        request=request,
        coverage=coverage,
        profile=profile,
    )
    output = json.dumps(
        {
            "proposals": [
                {
                    "approved_input_id": "AIN-000001",
                    "result": "proposed_mapping",
                    "selected_rule_id": "ELEMENT_SYSTEM_FUNCTION",
                    "alternative_rule_ids": [],
                    "rationale": "System-level context is the best fit.",
                }
            ]
        }
    )

    response = parse_llm_projection_response(
        request=llm_request,
        output_text=output,
    )

    assert response.request_fingerprint == llm_request.request_fingerprint
    assert response.proposals[0].selected_rule_id == (
        "ELEMENT_SYSTEM_FUNCTION"
    )
    assert len(response.response_fingerprint) == 64


def test_valid_ambiguous_and_unmapped_responses_are_preserved():
    profile, request, coverage = _setup(
        (_ambiguous(1), _unmapped(2))
    )
    llm_request = build_llm_projection_request(
        request=request,
        coverage=coverage,
        profile=profile,
    )
    ambiguous_options = [
        item.rule_id
        for item in llm_request.items[0].allowed_target_options
    ]

    output = json.dumps(
        {
            "proposals": [
                {
                    "approved_input_id": "AIN-000001",
                    "result": "ambiguous",
                    "selected_rule_id": None,
                    "alternative_rule_ids": ambiguous_options,
                    "rationale": "Both offered function scopes remain plausible.",
                },
                {
                    "approved_input_id": "AIN-000002",
                    "result": "unmapped",
                    "selected_rule_id": None,
                    "alternative_rule_ids": [],
                    "rationale": "No offered target type is defensible.",
                },
            ]
        }
    )

    response = parse_llm_projection_response(
        request=llm_request,
        output_text=output,
    )
    assert tuple(item.result for item in response.proposals) == (
        "ambiguous",
        "unmapped",
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"proposals": []},
        {
            "proposals": [
                {
                    "approved_input_id": "AIN-999999",
                    "result": "unmapped",
                    "selected_rule_id": None,
                    "alternative_rule_ids": [],
                    "rationale": "Unknown input.",
                }
            ]
        },
        {
            "proposals": [
                {
                    "approved_input_id": "AIN-000001",
                    "result": "proposed_mapping",
                    "selected_rule_id": "HALLUCINATED_RULE",
                    "alternative_rule_ids": [],
                    "rationale": "Invented.",
                }
            ]
        },
        {
            "proposals": [
                {
                    "approved_input_id": "AIN-000001",
                    "result": "unmapped",
                    "selected_rule_id": "ELEMENT_SYSTEM_FUNCTION",
                    "alternative_rule_ids": [],
                    "rationale": "Invalid shape.",
                }
            ]
        },
    ],
)
def test_invalid_or_hallucinated_responses_fail_closed(payload):
    profile, request, coverage = _setup((_ambiguous(1),))
    llm_request = build_llm_projection_request(
        request=request,
        coverage=coverage,
        profile=profile,
    )

    with pytest.raises(ModelCandidateDerivationError):
        parse_llm_projection_response(
            request=llm_request,
            output_text=json.dumps(payload),
        )


def test_response_schema_rejects_markdown_or_extra_fields():
    profile, request, coverage = _setup((_ambiguous(1),))
    llm_request = build_llm_projection_request(
        request=request,
        coverage=coverage,
        profile=profile,
    )

    with pytest.raises(ModelCandidateDerivationError):
        parse_llm_projection_response(
            request=llm_request,
            output_text='```json\n{"proposals":[]}\n```',
        )

    with pytest.raises(ModelCandidateDerivationError):
        parse_llm_projection_response(
            request=llm_request,
            output_text=json.dumps(
                {
                    "proposals": [],
                    "commentary": "extra",
                }
            ),
        )
