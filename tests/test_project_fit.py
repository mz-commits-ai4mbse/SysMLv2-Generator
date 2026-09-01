"""Tests for ADR-032 S2 Project Fit assessment."""

from __future__ import annotations

from dataclasses import replace
import json

import pytest

from modules.llm.types import LLMResult
from modules.project_fit import (
    ProjectFitAssessmentService,
    ProjectFitIntegrityError,
    ProjectFitValidationError,
    derive_project_fit_gate_state,
    project_fit_assessment_to_json,
)
from modules.project_processing.run_manifest import (
    create_processing_run_manifest,
    create_semantic_reference_version,
)
from modules.project_sources import (
    CONTEXT_ONLY_SOURCE_ROLE,
    ENGINEERING_SOURCE_ROLE,
)
from modules.project_workspace.manifest import create_project_manifest
from modules.source_projection.manifest import create_source_projection_artifact
from modules.source_projection.text_adapter import project_plain_text


PROJECT_ID = "318604"
SOURCE_A = "SRC-000001"
SOURCE_B = "SRC-000002"
SOURCE_C = "SRC-000003"
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


class Client:
    def __init__(self, output=None, error=None):
        self.output = output
        self.error = error
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return LLMResult(
            text=json.dumps(self.output),
            provider=request.provider,
            model=request.model,
            response_id="project-fit-1",
        )


def project():
    return create_project_manifest(
        PROJECT_ID,
        "Coffee Machine Platform",
        description=(
            "Automatic coffee machine with water, heating, brewing, "
            "grinding, controls, and service functions."
        ),
        timestamp="2026-08-31T06:00:00Z",
    )


def projection(
    source_id,
    source_sha256,
    projection_id,
    content,
    *,
    role=ENGINEERING_SOURCE_ROLE,
    project_id=PROJECT_ID,
):
    draft = project_plain_text(content.encode("utf-8"))
    return create_source_projection_artifact(
        project_id=project_id,
        source_id=source_id,
        source_projection_id=projection_id,
        source_role=role,
        source_sha256=source_sha256,
        draft=draft,
        timestamp="2026-08-31T06:01:00Z",
    )


def run_manifest(
    *,
    source_id=SOURCE_A,
    source_sha256=SHA_A,
    role=ENGINEERING_SOURCE_ROLE,
):
    return create_processing_run_manifest(
        project_id=PROJECT_ID,
        processing_run_id="RUN-000001",
        source_id=source_id,
        source_sha256=source_sha256,
        source_role_snapshot=role,
        workflow_profile=(
            "context_only_processing"
            if role == CONTEXT_ONLY_SOURCE_ROLE
            else "engineering_source_processing"
        ),
        configuration_fingerprint="d" * 64,
        framework_template_id="TURING_RFLP_FRAMEWORK",
        framework_template_version="1.0.0",
        semantic_reference_versions=(
            create_semantic_reference_version(
                reference_system_id="PROJECT_GLOSSARY",
                reference_version="1.0.0",
            ),
        ),
        timestamp="2026-08-31T06:02:00Z",
    )


def plausible_output():
    return {
        "outcome": "plausible_in_scope",
        "rationale": (
            "The BOM names water, heater, grinder and brewing assemblies "
            "that match the coffee-machine product context."
        ),
        "matched_concepts": [
            "brewing assembly",
            "grinder",
            "heater",
            "water system",
        ],
        "incompatible_concepts": [],
        "supporting_context_refs": [
            f"project_manifest:{PROJECT_ID}",
            "source_projection:SP-000002",
        ],
    }


def service(client):
    return ProjectFitAssessmentService(
        client_factory=lambda provider: client
    )


def test_plausible_source_is_admitted_with_context_provenance():
    candidate = projection(
        SOURCE_A,
        SHA_A,
        "SP-000001",
        "BOM: water tank, heater, grinder, brew group, control board.",
    )
    context = projection(
        SOURCE_B,
        SHA_B,
        "SP-000002",
        (
            "Product context: automatic coffee machine. Main functions are "
            "water handling, heating, grinding, brewing and user control."
        ),
        role=CONTEXT_ONLY_SOURCE_ROLE,
    )
    client = Client(plausible_output())

    assessment = service(client).assess(
        project(),
        run_manifest(),
        candidate,
        (candidate, context),
        attempt_id="ATT-000001",
        provider="openai",
        model="gpt-test",
    )

    assert assessment.outcome == "plausible_in_scope"
    assert derive_project_fit_gate_state(assessment) == "admitted"
    assert assessment.source_id == SOURCE_A
    assert assessment.processing_run_id == "RUN-000001"
    assert assessment.attempt_id == "ATT-000001"
    assert tuple(
        reference.reference_id
        for reference in assessment.context_references
    ) == (
        f"project_manifest:{PROJECT_ID}",
        "source_projection:SP-000002",
    )
    assert len(client.requests) == 1
    request_payload = json.loads(client.requests[0].input_text)
    assert request_payload["candidate_source"]["source_id"] == SOURCE_A
    assert len(request_payload["project_context_sources"]) == 1
    assert (
        request_payload["project_context_sources"][0]["source_id"]
        == SOURCE_B
    )


def test_candidate_source_cannot_prove_its_own_fit():
    candidate = projection(
        SOURCE_A,
        SHA_A,
        "SP-000001",
        "Coffee machine control software.",
    )
    same_source = projection(
        SOURCE_A,
        SHA_A,
        "SP-000002",
        "Coffee machine control software, older projection.",
    )
    client = Client(
        {
            "outcome": "plausible_in_scope",
            "rationale": "Project description matches the candidate.",
            "matched_concepts": ["coffee machine"],
            "incompatible_concepts": [],
            "supporting_context_refs": [
                f"project_manifest:{PROJECT_ID}"
            ],
        }
    )
    assessment = service(client).assess(
        project(),
        run_manifest(),
        candidate,
        (candidate, same_source),
        attempt_id="ATT-000001",
        provider="openai",
        model="gpt-test",
    )
    assert tuple(
        reference.reference_id
        for reference in assessment.context_references
    ) == (f"project_manifest:{PROJECT_ID}",)


def test_context_only_sources_are_prioritized_before_engineering_context():
    candidate = projection(
        SOURCE_A,
        SHA_A,
        "SP-000001",
        "Coffee machine BOM.",
    )
    engineering = projection(
        SOURCE_B,
        SHA_B,
        "SP-000002",
        "Remote service requirement for the coffee machine.",
    )
    context = projection(
        SOURCE_C,
        SHA_C,
        "SP-000003",
        "Coffee machine product overview.",
        role=CONTEXT_ONLY_SOURCE_ROLE,
    )
    client = Client(
        {
            "outcome": "plausible_in_scope",
            "rationale": "The product context identifies the same product.",
            "matched_concepts": ["coffee machine"],
            "incompatible_concepts": [],
            "supporting_context_refs": [
                "source_projection:SP-000003"
            ],
        }
    )
    assessment = service(client).assess(
        project(),
        run_manifest(),
        candidate,
        (engineering, context),
        attempt_id="ATT-000001",
        provider="openai",
        model="gpt-test",
    )
    assert tuple(
        reference.reference_id
        for reference in assessment.context_references
    ) == (
        f"project_manifest:{PROJECT_ID}",
        "source_projection:SP-000003",
        "source_projection:SP-000002",
    )


def test_latest_projection_per_other_source_is_used():
    candidate = projection(
        SOURCE_A,
        SHA_A,
        "SP-000001",
        "Coffee machine BOM.",
    )
    old = projection(
        SOURCE_B,
        SHA_B,
        "SP-000002",
        "Old coffee machine context.",
    )
    new = projection(
        SOURCE_B,
        SHA_B,
        "SP-000003",
        "Current coffee machine context.",
    )
    client = Client(
        {
            "outcome": "plausible_in_scope",
            "rationale": "The current source context matches.",
            "matched_concepts": ["coffee machine"],
            "incompatible_concepts": [],
            "supporting_context_refs": [
                "source_projection:SP-000003"
            ],
        }
    )
    assessment = service(client).assess(
        project(),
        run_manifest(),
        candidate,
        (old, new),
        attempt_id="ATT-000001",
        provider="openai",
        model="gpt-test",
    )
    ids = tuple(
        reference.reference_id
        for reference in assessment.context_references
    )
    assert "source_projection:SP-000003" in ids
    assert "source_projection:SP-000002" not in ids


def test_uncertain_source_requires_human_resolution():
    candidate = projection(
        SOURCE_A,
        SHA_A,
        "SP-000001",
        "Specialized assembly with ambiguous terminology.",
    )
    client = Client(
        {
            "outcome": "uncertain",
            "rationale": (
                "The source contains too little product-identifying context "
                "to establish Project fit safely."
            ),
            "matched_concepts": [],
            "incompatible_concepts": [],
            "supporting_context_refs": [],
        }
    )
    assessment = service(client).assess(
        project(),
        run_manifest(),
        candidate,
        (),
        attempt_id="ATT-000001",
        provider="openai",
        model="gpt-test",
    )
    assert (
        derive_project_fit_gate_state(assessment)
        == "human_resolution_required"
    )


def test_positive_incompatibility_can_flag_likely_wrong_project():
    candidate = projection(
        SOURCE_A,
        SHA_A,
        "SP-000001",
        (
            "Automotive ignition BOM: spark plug, ignition coil, exhaust "
            "manifold, cylinder head."
        ),
    )
    client = Client(
        {
            "outcome": "likely_out_of_scope",
            "rationale": (
                "The candidate describes an automotive combustion-engine "
                "ignition system, incompatible with the coffee-machine product."
            ),
            "matched_concepts": [],
            "incompatible_concepts": [
                "automotive combustion engine",
                "ignition system",
            ],
            "supporting_context_refs": [
                f"project_manifest:{PROJECT_ID}"
            ],
        }
    )
    assessment = service(client).assess(
        project(),
        run_manifest(),
        candidate,
        (),
        attempt_id="ATT-000001",
        provider="openai",
        model="gpt-test",
    )
    assert assessment.outcome == "likely_out_of_scope"
    assert (
        derive_project_fit_gate_state(assessment)
        == "human_resolution_required"
    )


def test_likely_out_of_scope_requires_positive_incompatibility():
    candidate = projection(
        SOURCE_A,
        SHA_A,
        "SP-000001",
        "Unrelated wording with no direct overlap.",
    )
    client = Client(
        {
            "outcome": "likely_out_of_scope",
            "rationale": "No overlap was found.",
            "matched_concepts": [],
            "incompatible_concepts": [],
            "supporting_context_refs": [
                f"project_manifest:{PROJECT_ID}"
            ],
        }
    )
    with pytest.raises(ProjectFitValidationError):
        service(client).assess(
            project(),
            run_manifest(),
            candidate,
            (),
            attempt_id="ATT-000001",
            provider="openai",
            model="gpt-test",
        )


def test_unknown_supporting_context_reference_fails_closed():
    candidate = projection(
        SOURCE_A,
        SHA_A,
        "SP-000001",
        "Coffee machine BOM.",
    )
    client = Client(
        {
            "outcome": "plausible_in_scope",
            "rationale": "Matched.",
            "matched_concepts": ["coffee machine"],
            "incompatible_concepts": [],
            "supporting_context_refs": [
                "source_projection:SP-999999"
            ],
        }
    )
    with pytest.raises(ProjectFitValidationError):
        service(client).assess(
            project(),
            run_manifest(),
            candidate,
            (),
            attempt_id="ATT-000001",
            provider="openai",
            model="gpt-test",
        )


def test_cross_project_context_is_rejected():
    candidate = projection(
        SOURCE_A,
        SHA_A,
        "SP-000001",
        "Coffee machine BOM.",
    )
    wrong_project = projection(
        SOURCE_B,
        SHA_B,
        "SP-000002",
        "Other project.",
        project_id="481516",
    )
    with pytest.raises(ProjectFitIntegrityError):
        service(Client(plausible_output())).assess(
            project(),
            run_manifest(),
            candidate,
            (wrong_project,),
            attempt_id="ATT-000001",
            provider="openai",
            model="gpt-test",
        )


def test_run_source_binding_mismatch_is_rejected():
    candidate = projection(
        SOURCE_A,
        SHA_A,
        "SP-000001",
        "Coffee machine BOM.",
    )
    with pytest.raises(ProjectFitIntegrityError):
        service(Client(plausible_output())).assess(
            project(),
            run_manifest(
                source_id=SOURCE_B,
                source_sha256=SHA_B,
            ),
            candidate,
            (),
            attempt_id="ATT-000001",
            provider="openai",
            model="gpt-test",
        )


def test_context_only_candidate_never_enters_engineering_reconciliation():
    candidate = projection(
        SOURCE_A,
        SHA_A,
        "SP-000001",
        "Coffee machine product context.",
        role=CONTEXT_ONLY_SOURCE_ROLE,
    )
    client = Client(
        {
            "outcome": "plausible_in_scope",
            "rationale": "The context document clearly describes the project.",
            "matched_concepts": ["coffee machine"],
            "incompatible_concepts": [],
            "supporting_context_refs": [
                f"project_manifest:{PROJECT_ID}"
            ],
        }
    )
    assessment = service(client).assess(
        project(),
        run_manifest(role=CONTEXT_ONLY_SOURCE_ROLE),
        candidate,
        (),
        attempt_id="ATT-000001",
        provider="openai",
        model="gpt-test",
    )
    assert derive_project_fit_gate_state(assessment) == "context_only"


def test_provider_failure_has_no_lossy_fallback():
    candidate = projection(
        SOURCE_A,
        SHA_A,
        "SP-000001",
        "Coffee machine BOM.",
    )
    with pytest.raises(RuntimeError, match="provider down"):
        service(Client(error=RuntimeError("provider down"))).assess(
            project(),
            run_manifest(),
            candidate,
            (),
            attempt_id="ATT-000001",
            provider="openai",
            model="gpt-test",
        )


def test_assessment_serialization_preserves_exact_provenance():
    candidate = projection(
        SOURCE_A,
        SHA_A,
        "SP-000001",
        "Coffee machine BOM: grinder, heater and brew group.",
    )
    client = Client(
        {
            "outcome": "plausible_in_scope",
            "rationale": "The candidate matches the project product.",
            "matched_concepts": ["coffee machine"],
            "incompatible_concepts": [],
            "supporting_context_refs": [
                f"project_manifest:{PROJECT_ID}"
            ],
        }
    )
    assessment = service(client).assess(
        project(),
        run_manifest(),
        candidate,
        (),
        attempt_id="ATT-000001",
        provider="openai",
        model="gpt-test",
    )
    payload = json.loads(project_fit_assessment_to_json(assessment))
    assert payload["source_id"] == SOURCE_A
    assert payload["source_sha256"] == SHA_A
    assert payload["source_projection_id"] == "SP-000001"
    assert payload["processing_run_id"] == "RUN-000001"
    assert payload["attempt_id"] == "ATT-000001"
    assert payload["llm_response_id"] == "project-fit-1"
    assert len(payload["input_fingerprint"]) == 64
    assert len(payload["assessment_fingerprint"]) == 64


def test_tampered_assessment_fingerprint_is_rejected():
    candidate = projection(
        SOURCE_A,
        SHA_A,
        "SP-000001",
        "Coffee machine BOM.",
    )
    client = Client(
        {
            "outcome": "plausible_in_scope",
            "rationale": "The candidate matches.",
            "matched_concepts": ["coffee machine"],
            "incompatible_concepts": [],
            "supporting_context_refs": [
                f"project_manifest:{PROJECT_ID}"
            ],
        }
    )
    assessment = service(client).assess(
        project(),
        run_manifest(),
        candidate,
        (),
        attempt_id="ATT-000001",
        provider="openai",
        model="gpt-test",
    )
    tampered = replace(
        assessment,
        rationale="Changed after assessment.",
    )
    with pytest.raises(ProjectFitIntegrityError):
        derive_project_fit_gate_state(tampered)
