from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
from types import SimpleNamespace

import pytest

from modules.model_candidates.types import (
    ModelCandidateApprovedInputReference,
    ModelCandidateReviewDecisionReference,
)
from modules.output_publication import (
    FinalReviewPublicationService,
    OutputPublicationIntegrityError,
)
from modules.sysml_generation.artifact_builder import (
    calculate_generation_input_fingerprint,
)
from modules.sysml_generation.types import (
    GeneratedSysMLArtifactSet,
    GeneratedSysMLLocation,
    GeneratedSysMLTraceabilityEntry,
    GeneratedSysMLUnit,
    SysMLArtifactStructureReference,
    SysMLGenerationContext,
    SysMLGenerationProvenance,
    SysMLGenerationProfileReference,
    SysMLGeneratorRulesReference,
    TargetNotationReference,
)
from modules.sysml_validation.artifact_integrity import (
    calculate_received_artifact_set_fingerprint,
)
from modules.sysml_validation.service import (
    calculate_validation_result_fingerprint,
)
from modules.sysml_validation.types import (
    SysMLExternalValidationEvidence,
    SysMLExternalValidatorIdentity,
    SysMLValidationProfileReference,
    SysMLValidationResult,
)


def artifact_set():
    sha = "a" * 64

    context = SysMLGenerationContext(
        target_notation_reference=TargetNotationReference(
            context_id="TURING_SYSML_V2_TARGET",
            version="1.0.0",
            content_fingerprint=sha,
        ),
        generation_profile_reference=SysMLGenerationProfileReference(
            profile_id="GEN",
            profile_version="1.0.0",
            profile_fingerprint=sha,
        ),
        artifact_structure_reference=SysMLArtifactStructureReference(
            profile_id="STRUCT",
            profile_version="1.0.0",
            profile_fingerprint=sha,
        ),
        generator_rules_reference=SysMLGeneratorRulesReference(
            rules_id="RULES",
            rules_version="1.0.0",
            rules_fingerprint=sha,
        ),
    )

    content = "package System {}\n"

    unit = GeneratedSysMLUnit(
        unit_id="GEN-000001",
        relative_path="model/system.sysml",
        content=content,
        content_fingerprint=hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest(),
        generated_symbol_ids=("System",),
        source_internal_model_element_ids=("IME-000001",),
        source_internal_model_relationship_ids=(),
    )

    approved_input = ModelCandidateApprovedInputReference(
        approved_input_id="AIN-000001",
        content_fingerprint=sha,
        stable_subject_key="system",
        provenance_role="primary",
    )

    review_decision = ModelCandidateReviewDecisionReference(
        model_candidate_review_decision_id="MCD-000001",
        target_type="element_candidate",
        candidate_id="MCE-000001",
        decision="accepted",
        decision_fingerprint=sha,
    )

    trace = GeneratedSysMLTraceabilityEntry(
        generated_unit_id="GEN-000001",
        generated_symbol_id="System",
        generated_location=GeneratedSysMLLocation(
            start_line=1,
            end_line=1,
        ),
        source_internal_engineering_model_id="IEM-000001",
        source_internal_model_element_id="IME-000001",
        source_internal_model_relationship_id=None,
        source_model_candidate_id="MCE-000001",
        approved_input_references=(approved_input,),
        review_decision_reference=review_decision,
        accepted_exception_reference=None,
    )

    input_fingerprint = calculate_generation_input_fingerprint(
        source_iem_content_fingerprint=sha,
        generation_context=context,
    )

    provisional = GeneratedSysMLArtifactSet(
        schema_version="1.0.0",
        project_id="123456",
        source_internal_engineering_model_id="IEM-000001",
        source_iem_content_fingerprint=sha,
        generation_context=context,
        generation_input_fingerprint=input_fingerprint,
        generation_provenance=SysMLGenerationProvenance(
            method="deterministic_serialization",
            implementation_reference="test",
            context_fingerprint=sha,
        ),
        units=(unit,),
        traceability_entries=(trace,),
        nonblocking_diagnostics=(),
        content_fingerprint="0" * 64,
    )

    return replace(
        provisional,
        content_fingerprint=(
            calculate_received_artifact_set_fingerprint(provisional)
        ),
    )


def validation_result(artifact):
    sha = "b" * 64

    evidence = SysMLExternalValidationEvidence(
        validator_identity=SysMLExternalValidatorIdentity(
            validator_id="SYSIDE_CLI",
            tool_name="SYSIDE",
            tool_version="1.0",
            command_contract_id="contract",
            configuration_fingerprint=sha,
        ),
        execution_status="completed",
        exit_code=0,
        normalized_diagnostic_count=0,
    )

    provisional = SysMLValidationResult(
        schema_version="1.0.0",
        project_id=artifact.project_id,
        source_internal_engineering_model_id=(
            artifact.source_internal_engineering_model_id
        ),
        source_artifact_set_fingerprint=artifact.content_fingerprint,
        validation_profile_reference=SysMLValidationProfileReference(
            profile_id="VALIDATION",
            profile_version="1.0.0",
            profile_fingerprint=sha,
        ),
        validation_input_fingerprint=sha,
        external_validator_evidence=(evidence,),
        findings=(),
        validation_status="valid",
        publication_gate="passed",
        content_fingerprint="0" * 64,
    )

    return replace(
        provisional,
        content_fingerprint=(
            calculate_validation_result_fingerprint(provisional)
        ),
    )


def bundle_for(artifact, validation, *, stored_content=None):
    unit = artifact.units[0]

    revision = SimpleNamespace(
        project_id="123456",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id="FRV-000001",
        generated_artifact_set_fingerprint=(
            artifact.content_fingerprint
        ),
        validation_result_fingerprint=(
            validation.content_fingerprint
        ),
    )

    stored = SimpleNamespace(
        generated_unit_id=unit.unit_id,
        relative_path=unit.relative_path,
        content=(
            unit.content
            if stored_content is None
            else stored_content
        ),
        content_fingerprint=unit.content_fingerprint,
    )

    return SimpleNamespace(
        revision=revision,
        artifact_set_snapshot=asdict(artifact),
        validation_result_snapshot=asdict(validation),
        generated_units=(stored,),
    )


class Repository:
    def __init__(self, bundle, decision):
        self.bundle = bundle
        self.decision = decision
        self.load_revision_calls = []
        self.load_decision_calls = []

    def load_revision(
        self,
        project_id,
        review_id,
        revision_id,
    ):
        self.load_revision_calls.append(
            (project_id, review_id, revision_id)
        )
        return self.bundle

    def load_decision(
        self,
        project_id,
        review_id,
        decision_id,
    ):
        self.load_decision_calls.append(
            (project_id, review_id, decision_id)
        )
        return self.decision


class Writer:
    def __init__(self):
        self.calls = []

    def publish(
        self,
        artifact,
        validation,
        decision,
    ):
        self.calls.append(
            (artifact, validation, decision)
        )
        return SimpleNamespace(
            manifest=SimpleNamespace(
                output_package_id="OUT-000001"
            )
        )


def approval_decision():
    return SimpleNamespace(
        project_id="123456",
        final_model_review_decision_id="FRD-000001",
        decision="approved_for_publication",
        target=SimpleNamespace(
            final_model_review_id="FMR-000001",
            final_model_review_revision_id="FRV-000001",
        ),
    )


def approved_gate(repository, project_id, review_id, revision_id):
    return SimpleNamespace(
        release_status="approved_for_publication",
        approval_decision_id="FRD-000001",
    )


def no_op_phase_l_gate(artifact, validation):
    assert isinstance(artifact, GeneratedSysMLArtifactSet)
    assert isinstance(validation, SysMLValidationResult)


def test_exact_frv_snapshots_are_reconstructed_and_published():
    artifact = artifact_set()
    validation = validation_result(artifact)
    decision = approval_decision()
    repository = Repository(
        bundle_for(artifact, validation),
        decision,
    )
    writer = Writer()

    service = FinalReviewPublicationService(
        ".",
        final_review_repository=repository,
        output_writer=writer,
        release_gate_resolver=approved_gate,
        phase_l_gate=no_op_phase_l_gate,
    )

    package = service.publish_revision(
        "123456",
        "FMR-000001",
        "FRV-000001",
    )

    assert package.manifest.output_package_id == "OUT-000001"
    assert repository.load_revision_calls == [
        ("123456", "FMR-000001", "FRV-000001")
    ]
    assert repository.load_decision_calls == [
        ("123456", "FMR-000001", "FRD-000001")
    ]

    published_artifact, published_validation, published_decision = (
        writer.calls[0]
    )

    assert isinstance(
        published_artifact,
        GeneratedSysMLArtifactSet,
    )
    assert isinstance(
        published_validation,
        SysMLValidationResult,
    )
    assert published_artifact == artifact
    assert published_validation == validation
    assert published_decision is decision


def test_reviewed_generated_bytes_must_equal_phase_j_snapshot():
    artifact = artifact_set()
    validation = validation_result(artifact)

    repository = Repository(
        bundle_for(
            artifact,
            validation,
            stored_content="package Changed {}\n",
        ),
        approval_decision(),
    )
    writer = Writer()

    service = FinalReviewPublicationService(
        ".",
        final_review_repository=repository,
        output_writer=writer,
        release_gate_resolver=approved_gate,
        phase_l_gate=no_op_phase_l_gate,
    )

    with pytest.raises(
        OutputPublicationIntegrityError,
        match="Reviewed generated SysML bytes",
    ):
        service.publish_revision(
            "123456",
            "FMR-000001",
            "FRV-000001",
        )

    assert writer.calls == []


def test_approval_must_target_exact_selected_revision():
    artifact = artifact_set()
    validation = validation_result(artifact)

    decision = approval_decision()
    decision.target.final_model_review_revision_id = "FRV-000002"

    repository = Repository(
        bundle_for(artifact, validation),
        decision,
    )
    writer = Writer()

    service = FinalReviewPublicationService(
        ".",
        final_review_repository=repository,
        output_writer=writer,
        release_gate_resolver=approved_gate,
        phase_l_gate=no_op_phase_l_gate,
    )

    with pytest.raises(
        OutputPublicationIntegrityError,
        match="does not authorize the exact",
    ):
        service.publish_revision(
            "123456",
            "FMR-000001",
            "FRV-000001",
        )

    assert writer.calls == []


def test_snapshot_with_unexpected_field_fails_closed():
    artifact = artifact_set()
    validation = validation_result(artifact)
    bundle = bundle_for(artifact, validation)

    bundle.artifact_set_snapshot["unexpected"] = "value"

    repository = Repository(
        bundle,
        approval_decision(),
    )
    writer = Writer()

    service = FinalReviewPublicationService(
        ".",
        final_review_repository=repository,
        output_writer=writer,
        release_gate_resolver=approved_gate,
        phase_l_gate=no_op_phase_l_gate,
    )

    with pytest.raises(
        OutputPublicationIntegrityError,
        match="unexpected",
    ):
        service.publish_revision(
            "123456",
            "FMR-000001",
            "FRV-000001",
        )

    assert writer.calls == []


def test_phase_l_gate_is_reapplied_before_writer():
    artifact = artifact_set()
    validation = validation_result(artifact)
    repository = Repository(
        bundle_for(artifact, validation),
        approval_decision(),
    )
    writer = Writer()

    error = RuntimeError("gate failed")

    def failing_gate(artifact, validation):
        raise error

    service = FinalReviewPublicationService(
        ".",
        final_review_repository=repository,
        output_writer=writer,
        release_gate_resolver=approved_gate,
        phase_l_gate=failing_gate,
    )

    with pytest.raises(
        OutputPublicationIntegrityError,
        match="Phase-K -> Phase-L",
    ) as caught:
        service.publish_revision(
            "123456",
            "FMR-000001",
            "FRV-000001",
        )

    assert caught.value.__cause__ is error
    assert writer.calls == []
