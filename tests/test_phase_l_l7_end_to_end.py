from __future__ import annotations

from datetime import datetime, timezone
import shutil

import pytest

from modules.framework import load_framework_template
from modules.final_model_review import (
    FinalModelReviewReleaseGateError,
    FinalModelReviewReleaseService,
    FinalModelReviewRepository,
)
from modules.internal_model import (
    InternalEngineeringModelSnapshot,
    InternalModelAssemblyContext,
    InternalModelAssemblyProvenance,
    InternalModelAssemblyRulesReference,
    InternalModelReadService,
    InternalModelRepositoryScanResult,
    InternalModelStructureNode,
    create_internal_engineering_model_manifest,
    create_internal_model_structure,
)
from modules.model_candidates.structure_profile import (
    load_model_structure_profile,
)
from modules.model_candidates.types import (
    ModelDerivationRulesReference,
    ModelStructureProfileReference,
)
from modules.output_publication import (
    OutputPublicationRepository,
    OutputWriter,
)
from modules.project_workspace.types import FrameworkTemplateReference
from modules.sysml_generation import SysMLGenerationService
from modules.sysml_validation import (
    EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID,
    EXPECTED_EXTERNAL_TOOL_NAME,
    EXPECTED_EXTERNAL_VALIDATOR_ID,
    SYSIDE_CHECK_COMMAND_CONFIGURATION,
    SysMLExternalValidationEvidence,
    SysMLExternalValidationRun,
    SysMLExternalValidatorIdentity,
    SysMLValidationFinding,
    SysMLValidationService,
    calculate_json_fingerprint,
)


PROJECT_ID = "000042"
IEM_ID = "IEM-000007"


def _clock() -> datetime:
    return datetime(2026, 8, 14, 12, 0, 0, tzinfo=timezone.utc)


class _WorkspaceStub:
    def load_project(self, project_id: str):
        if project_id != PROJECT_ID:
            raise RuntimeError("Project not found.")
        return object()


class _InternalModelRepositoryStub:
    def __init__(self, snapshot: InternalEngineeringModelSnapshot) -> None:
        self.snapshot = snapshot

    def scan_project(self, project_id: str):
        assert project_id == PROJECT_ID
        return InternalModelRepositoryScanResult(
            snapshots=(self.snapshot,),
            issues=(),
        )

    def load_snapshot(
        self,
        project_id: str,
        internal_engineering_model_id: str,
    ):
        assert (project_id, internal_engineering_model_id) == (
            PROJECT_ID,
            IEM_ID,
        )
        return self.snapshot


class _ExternalValidator:
    """Deterministic Phase-K adapter used only by the automated L7 test."""

    def __init__(self, *, execution_status: str = "completed") -> None:
        self.execution_status = execution_status
        self.identity = SysMLExternalValidatorIdentity(
            validator_id=EXPECTED_EXTERNAL_VALIDATOR_ID,
            tool_name=EXPECTED_EXTERNAL_TOOL_NAME,
            tool_version="L7 deterministic acceptance adapter",
            command_contract_id=EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID,
            configuration_fingerprint=calculate_json_fingerprint(
                SYSIDE_CHECK_COMMAND_CONFIGURATION
            ),
        )

    def validate(self, _artifact_set):
        findings = ()
        if self.execution_status != "completed":
            findings = (
                SysMLValidationFinding(
                    code="K_L7_EXTERNAL_VALIDATOR_INCOMPLETE",
                    category="validator_infrastructure",
                    severity="error",
                    blocking=True,
                    message=(
                        "Required external validation did not complete in "
                        "the L7 fail-closed acceptance path."
                    ),
                    validator_id=self.identity.validator_id,
                ),
            )
        return SysMLExternalValidationRun(
            evidence=SysMLExternalValidationEvidence(
                validator_identity=self.identity,
                execution_status=self.execution_status,
                exit_code=(
                    0 if self.execution_status == "completed" else None
                ),
                normalized_diagnostic_count=0,
            ),
            findings=findings,
        )


def _ordered_framework_nodes(template):
    roots = sorted(
        (
            node
            for node in template["nodes"]
            if node["parent_node_id"] is None
        ),
        key=lambda item: (item["order"], item["node_id"]),
    )
    children = {}
    for node in template["nodes"]:
        parent = node["parent_node_id"]
        if parent is not None:
            children.setdefault(parent, []).append(node)

    result = []
    for root in roots:
        result.append(root)
        result.extend(
            sorted(
                children.get(root["node_id"], ()),
                key=lambda item: (item["order"], item["node_id"]),
            )
        )
    assert len(result) == len(template["nodes"])
    return tuple(result)


def _empty_valid_iem() -> InternalEngineeringModelSnapshot:
    template = load_framework_template()
    profile = load_model_structure_profile(
        framework_template=template,
    )
    framework_reference = FrameworkTemplateReference(
        template_id=template["template_id"],
        template_version=template["template_version"],
    )
    context = InternalModelAssemblyContext(
        framework_template_reference=framework_reference,
        model_structure_profile_reference=ModelStructureProfileReference(
            profile_id=profile.profile_id,
            profile_version=profile.profile_version,
            profile_fingerprint=profile.profile_fingerprint,
        ),
        derivation_rules_reference=ModelDerivationRulesReference(
            context_id="CTX_SYSML_MODEL_DERIVATION_RULES",
            context_version="0.1.0",
            context_fingerprint="b" * 64,
        ),
        assembly_rules_reference=InternalModelAssemblyRulesReference(
            rules_id="TURING_INTERNAL_MODEL_ASSEMBLY",
            rules_version="1.0.0",
            rules_fingerprint="c" * 64,
        ),
    )
    nodes = tuple(
        InternalModelStructureNode(
            framework_node_id=node["node_id"],
            mapping_key=node["mapping_key"],
            name=node["name"],
            node_type=node["node_type"],
            parent_framework_node_id=node["parent_node_id"],
            order=node["order"],
            internal_model_element_ids=(),
        )
        for node in _ordered_framework_nodes(template)
    )
    structure = create_internal_model_structure(
        project_id=PROJECT_ID,
        internal_engineering_model_id=IEM_ID,
        framework_template_reference=framework_reference,
        nodes=nodes,
    )
    manifest = create_internal_engineering_model_manifest(
        project_id=PROJECT_ID,
        internal_engineering_model_id=IEM_ID,
        assembly_input_fingerprint="d" * 64,
        candidate_set_id="MCS-000001",
        candidate_set_content_fingerprint="e" * 64,
        approved_input_snapshot_fingerprint="f" * 64,
        assembly_context=context,
        assembly_provenance=InternalModelAssemblyProvenance(
            method="deterministic",
            implementation_reference="L7-integration-test",
            recipe_reference=None,
            context_fingerprint=None,
        ),
        structure_content_fingerprint=structure.content_fingerprint,
        internal_model_element_ids=(),
        internal_model_relationship_ids=(),
        review_decision_references=(),
        accepted_exception_references=(),
        created_at="2026-08-14T12:00:00Z",
    )
    return InternalEngineeringModelSnapshot(
        manifest=manifest,
        structure=structure,
        elements=(),
        relationships=(),
    )


def _generate_artifact():
    snapshot = _empty_valid_iem()
    reader = InternalModelReadService(
        repository=_InternalModelRepositoryStub(snapshot)
    )
    return SysMLGenerationService(
        read_service=reader
    ).generate(PROJECT_ID, IEM_ID)


def _review_repository(tmp_path):
    return FinalModelReviewRepository(
        root=tmp_path / "projects",
        workspace=_WorkspaceStub(),
        clock=_clock,
    )


def test_l7_real_iem_to_j_to_k_to_human_release_to_out(tmp_path):
    artifact = _generate_artifact()

    assert artifact.project_id == PROJECT_ID
    assert artifact.source_internal_engineering_model_id == IEM_ID
    assert len(artifact.units) == 1
    assert artifact.units[0].relative_path == "generated_model.sysml"
    assert artifact.units[0].content.startswith("package GeneratedModel {")

    validation = SysMLValidationService(
        external_validator=_ExternalValidator()
    ).validate(artifact)

    assert validation.validation_status == "valid"
    assert validation.publication_gate == "passed"
    assert validation.source_artifact_set_fingerprint == (
        artifact.content_fingerprint
    )

    reviews = _review_repository(tmp_path)
    review = reviews.create_review(PROJECT_ID)
    revision_bundle = reviews.append_revision(
        PROJECT_ID,
        review.final_model_review_id,
        artifact_set=artifact,
        validation_result=validation,
    )

    release = FinalModelReviewReleaseService(
        repository=reviews,
        clock=_clock,
    ).approve_for_publication(
        PROJECT_ID,
        review.final_model_review_id,
        revision_bundle.revision.final_model_review_revision_id,
        reviewer_identity="l7-human-reviewer",
        rationale=(
            "Automated L7 fixture represents an explicit Human release "
            "decision after inspection of the exact validated revision."
        ),
    )

    assert release.gate.release_status == "approved_for_publication"
    assert release.decision.decision == "approved_for_publication"

    output_root = tmp_path / "output"
    output_repository = OutputPublicationRepository(
        output_root=output_root
    )
    writer = OutputWriter(
        output_root=output_root,
        project_root=tmp_path / "projects",
        output_repository=output_repository,
        final_review_repository=reviews,
        clock=_clock,
    )
    published = writer.publish(
        artifact,
        validation,
        release.decision,
    )

    assert published.manifest.output_package_id == "OUT-000001"
    assert published.manifest.project_id == PROJECT_ID
    assert published.manifest.source_internal_engineering_model_id == IEM_ID
    assert published.manifest.source_artifact_set_fingerprint == (
        artifact.content_fingerprint
    )
    assert published.manifest.validation_result_fingerprint == (
        validation.content_fingerprint
    )
    assert published.manifest.final_model_review_id == (
        review.final_model_review_id
    )
    assert published.manifest.final_model_review_revision_id == (
        revision_bundle.revision.final_model_review_revision_id
    )
    assert published.manifest.final_review_decision_id == (
        release.decision.final_model_review_decision_id
    )
    assert output_repository.read_file(
        PROJECT_ID,
        "OUT-000001",
        artifact.units[0].relative_path,
    ) == artifact.units[0].content.encode("utf-8")

    package_files = {
        item.relative_path for item in published.manifest.files
    }
    assert package_files == {
        "generated_model.sysml",
        "generation_summary.json",
        "traceability.json",
        "validation_report.md",
        "validation_result.json",
    }

    # Exact re-publication is idempotent.
    again = writer.publish(
        artifact,
        validation,
        release.decision,
    )
    assert again.manifest == published.manifest
    assert len(output_repository.list_outputs(PROJECT_ID)) == 1


def test_l7_incomplete_external_validation_is_reviewable_but_not_releasable(
    tmp_path,
):
    artifact = _generate_artifact()
    validation = SysMLValidationService(
        external_validator=_ExternalValidator(
            execution_status="unavailable"
        )
    ).validate(artifact)

    assert validation.validation_status == "incomplete"
    assert validation.publication_gate == "blocked"

    reviews = _review_repository(tmp_path)
    review = reviews.create_review(PROJECT_ID)
    revision_bundle = reviews.append_revision(
        PROJECT_ID,
        review.final_model_review_id,
        artifact_set=artifact,
        validation_result=validation,
    )

    assert revision_bundle.revision.validation_status == "incomplete"
    assert revision_bundle.revision.publication_gate == "blocked"

    release_service = FinalModelReviewReleaseService(
        repository=reviews,
        clock=_clock,
    )
    gate = release_service.evaluate(
        PROJECT_ID,
        review.final_model_review_id,
        revision_bundle.revision.final_model_review_revision_id,
    )
    assert gate.release_status == "blocked"
    assert any(
        blocker.code == "validation_not_passed"
        for blocker in gate.blockers
    )

    with pytest.raises(FinalModelReviewReleaseGateError):
        release_service.approve_for_publication(
            PROJECT_ID,
            review.final_model_review_id,
            revision_bundle.revision.final_model_review_revision_id,
            reviewer_identity="l7-human-reviewer",
        )

    output_repository = OutputPublicationRepository(
        output_root=tmp_path / "output"
    )
    assert output_repository.list_outputs(PROJECT_ID) == ()


def test_l7_services_keep_explicit_authority_boundaries():
    assert not hasattr(SysMLGenerationService, "publish")
    assert not hasattr(SysMLValidationService, "publish")
    assert not hasattr(FinalModelReviewReleaseService, "publish")
    assert callable(OutputWriter.publish)


def test_l7_no_implicit_latest_api_exists_on_release_or_output_boundary():
    for cls in (
        FinalModelReviewReleaseService,
        OutputWriter,
        OutputPublicationRepository,
    ):
        assert not hasattr(cls, "latest")
        assert not hasattr(cls, "publish_latest")
        assert not hasattr(cls, "approve_latest")


def test_l7_live_syside_vertical_slice_if_cli_is_available(tmp_path):
    if shutil.which("syside") is None:
        pytest.skip(
            "SYSIDE CLI is unavailable; live Phase-L acceptance remains blocked."
        )

    artifact = _generate_artifact()
    validation = SysMLValidationService().validate(artifact)

    assert validation.validation_status == "valid"
    assert validation.publication_gate == "passed"
    assert (
        validation.external_validator_evidence[0].execution_status
        == "completed"
    )

    reviews = _review_repository(tmp_path)
    review = reviews.create_review(PROJECT_ID)
    revision_bundle = reviews.append_revision(
        PROJECT_ID,
        review.final_model_review_id,
        artifact_set=artifact,
        validation_result=validation,
    )
    release = FinalModelReviewReleaseService(
        repository=reviews,
        clock=_clock,
    ).approve_for_publication(
        PROJECT_ID,
        review.final_model_review_id,
        revision_bundle.revision.final_model_review_revision_id,
        reviewer_identity="l7-live-human-acceptance",
        rationale="Live SYSIDE L7 acceptance of the exact validated revision.",
    )

    output_root = tmp_path / "output"
    repository = OutputPublicationRepository(output_root=output_root)
    published = OutputWriter(
        output_root=output_root,
        project_root=tmp_path / "projects",
        output_repository=repository,
        final_review_repository=reviews,
        clock=_clock,
    ).publish(
        artifact,
        validation,
        release.decision,
    )

    assert published.manifest.output_package_id == "OUT-000001"
    assert repository.read_file(
        PROJECT_ID,
        "OUT-000001",
        "generated_model.sysml",
    ) == artifact.units[0].content.encode("utf-8")
