from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

import pytest

from modules.framework import load_framework_template
from modules.internal_model import (
    InternalEngineeringModelNotFoundError,
    InternalModelAssemblyProvenance,
    InternalModelAssemblyService,
    InternalModelIntegrityError,
    InternalModelPersistenceError,
    InternalModelPersistenceService,
    InternalModelRepository,
    InternalModelRecoveryRequiredError,
    UnsafeInternalModelPathError,
    validate_internal_engineering_model_snapshot,
)
from modules.internal_model.paths import internal_models_path
from modules.model_candidates.structure_profile import (
    load_model_structure_profile,
)
from modules.model_candidates.types import (
    ModelCandidateAssemblyInput,
    ModelCandidateGenerationProvenance,
    ModelCandidateReviewDecisionReference,
    ModelDerivationRulesReference,
    ModelElementCandidate,
    ModelRelationshipCandidate,
    ModelRelationshipEndpoint,
    ModelStructureProfileReference,
    RelationshipPriorityAssessment,
    RelationshipPriorityCriterionResult,
    StructuralComparabilityAssessment,
    StructuralProfileConformance,
)
from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.types import FrameworkTemplateReference


def _clock():
    return datetime(2026, 8, 13, 10, 15, tzinfo=timezone.utc)


def _create_project(root: Path, project_id: str = "000042"):
    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: project_id,
        clock=_clock,
    )
    workspace.create_project(f"IEM Test {project_id}")


def _profile_reference() -> ModelStructureProfileReference:
    template = load_framework_template()
    profile = load_model_structure_profile(
        framework_template=template,
    )
    return ModelStructureProfileReference(
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_fingerprint=profile.profile_fingerprint,
    )


def _conformance(char: str) -> StructuralProfileConformance:
    return StructuralProfileConformance(
        status="conformant",
        finding_ids=(),
        conformance_fingerprint=char * 64,
    )


def _element(
    *,
    set_id: str,
    candidate_id: str,
    subject: str,
    model_area: str,
    element_type: str,
    framework_assignment: str,
    fingerprint_char: str,
) -> ModelElementCandidate:
    return ModelElementCandidate(
        schema_version="1.0.0",
        project_id="000042",
        candidate_set_id=set_id,
        model_element_candidate_id=candidate_id,
        candidate_subject_key=subject,
        comparison_anchor_id=f"{model_area}:{subject}",
        proposed_name=subject,
        description=None,
        model_area=model_area,
        element_type=element_type,
        framework_assignment=framework_assignment,
        terminology_assignment=None,
        attributes=(),
        approved_input_references=(),
        derivation_rationale="Persistence fixture.",
        support_level="supported",
        assumptions=(),
        missing_information=(),
        structure_profile_conformance=_conformance("a"),
        predecessor_candidate_ids=(),
        created_at="2026-08-13T10:00:00Z",
        content_fingerprint=fingerprint_char * 64,
    )


def _relationship(
    *,
    set_id: str,
    relationship_id: str,
    source_id: str,
    source_subject: str,
    target_id: str,
    target_subject: str,
    fingerprint_char: str,
) -> ModelRelationshipCandidate:
    return ModelRelationshipCandidate(
        schema_version="1.0.0",
        project_id="000042",
        candidate_set_id=set_id,
        model_relationship_candidate_id=relationship_id,
        relationship_choice_key=None,
        source=ModelRelationshipEndpoint(
            candidate_subject_key=source_subject,
            resolution_status="resolved",
            resolved_model_element_candidate_id=source_id,
            candidate_model_element_ids=(source_id,),
        ),
        target=ModelRelationshipEndpoint(
            candidate_subject_key=target_subject,
            resolution_status="resolved",
            resolved_model_element_candidate_id=target_id,
            candidate_model_element_ids=(target_id,),
        ),
        relationship_family="allocation",
        semantic_intent="allocated_to",
        directionality="source_to_target",
        approved_input_references=(),
        derivation_rationale="Persistence fixture relation.",
        supporting_evidence=(),
        assumptions=(),
        missing_information=(),
        priority_assessment=RelationshipPriorityAssessment(
            priority_class="preferred",
            criterion_results=(
                RelationshipPriorityCriterionResult(
                    criterion="semantic_fit",
                    result="strong",
                    rationale="Fixture.",
                ),
            ),
            rationale="Fixture.",
        ),
        comparability_assessment=StructuralComparabilityAssessment(
            impact="neutral",
            comparison_anchor_ids=(),
            canonical_pattern_match=True,
            deviation_ids=(),
            rationale="Fixture.",
        ),
        structure_profile_conformance=_conformance("b"),
        upstream_relationship_representation=None,
        predecessor_candidate_ids=(),
        created_at="2026-08-13T10:00:00Z",
        content_fingerprint=fingerprint_char * 64,
    )


def _review(
    *,
    decision_id: str,
    target_type: str,
    candidate_id: str,
    char: str,
) -> ModelCandidateReviewDecisionReference:
    return ModelCandidateReviewDecisionReference(
        model_candidate_review_decision_id=decision_id,
        target_type=target_type,
        candidate_id=candidate_id,
        decision="accepted",
        decision_fingerprint=char * 64,
    )


def _assembly_input(
    *,
    set_id: str = "MCS-000001",
    offset: int = 0,
) -> ModelCandidateAssemblyInput:
    template = load_framework_template()

    first_id = f"MCE-{1 + offset:06d}"
    second_id = f"MCE-{2 + offset:06d}"
    relation_id = f"MCR-{1 + offset // 2:06d}"

    first_subject = f"system.requirement.{1 + offset}"
    second_subject = f"system.controller.{1 + offset}"

    elements = (
        _element(
            set_id=set_id,
            candidate_id=first_id,
            subject=first_subject,
            model_area="system.requirements",
            element_type="system_requirement",
            framework_assignment="FW_SYSTEM_REQUIREMENTS",
            fingerprint_char="1" if offset == 0 else "7",
        ),
        _element(
            set_id=set_id,
            candidate_id=second_id,
            subject=second_subject,
            model_area="system.logical",
            element_type="logical_component",
            framework_assignment="FW_SYSTEM_LOGICAL",
            fingerprint_char="2" if offset == 0 else "8",
        ),
    )
    relationship = _relationship(
        set_id=set_id,
        relationship_id=relation_id,
        source_id=first_id,
        source_subject=first_subject,
        target_id=second_id,
        target_subject=second_subject,
        fingerprint_char="3" if offset == 0 else "9",
    )

    reviews = (
        _review(
            decision_id=f"MCD-{1 + offset:06d}",
            target_type="element_candidate",
            candidate_id=first_id,
            char="4",
        ),
        _review(
            decision_id=f"MCD-{2 + offset:06d}",
            target_type="element_candidate",
            candidate_id=second_id,
            char="5",
        ),
        _review(
            decision_id=f"MCD-{3 + offset:06d}",
            target_type="relationship_candidate",
            candidate_id=relation_id,
            char="6",
        ),
    )

    return ModelCandidateAssemblyInput(
        project_id="000042",
        candidate_set_id=set_id,
        candidate_set_content_fingerprint=(
            "c" * 64 if offset == 0 else "d" * 64
        ),
        approved_input_snapshot_fingerprint=(
            "e" * 64 if offset == 0 else "f" * 64
        ),
        approved_input_references=(),
        framework_template_reference=FrameworkTemplateReference(
            template_id=template["template_id"],
            template_version=template["template_version"],
        ),
        model_structure_profile_reference=_profile_reference(),
        derivation_rules_reference=ModelDerivationRulesReference(
            context_id="CTX_SYSML_MODEL_DERIVATION_RULES",
            context_version="0.1.0",
            context_fingerprint="a" * 64,
        ),
        generation_provenance=ModelCandidateGenerationProvenance(
            method="profile_driven",
            recipe_reference=None,
            agent_reference=None,
            model_reference=None,
            context_fingerprint=None,
        ),
        accepted_element_candidates=elements,
        accepted_relationship_candidates=(relationship,),
        accepted_exception_decisions=(),
        review_decision_references=reviews,
    )


def _provenance():
    return InternalModelAssemblyProvenance(
        method="deterministic",
        implementation_reference="I5-test",
        recipe_reference=None,
        context_fingerprint=None,
    )


def _persist_one(tmp_path: Path):
    _create_project(tmp_path)
    service = InternalModelPersistenceService(root=tmp_path)
    snapshot = service.assemble_and_persist(
        assembly_input=_assembly_input(),
        assembly_provenance=_provenance(),
        created_at="2026-08-13T10:15:00Z",
    )
    return service, snapshot


def test_atomic_persistence_roundtrips_complete_iem_bundle(tmp_path):
    service, snapshot = _persist_one(tmp_path)
    repository = service.repository

    loaded = repository.load_snapshot("000042", "IEM-000001")
    assert loaded == snapshot

    iem_dir = tmp_path / "000042" / "internal_models" / "IEM-000001"
    assert {item.name for item in iem_dir.iterdir()} == {
        "manifest.json",
        "structure.json",
        "elements",
        "relationships",
    }
    assert sorted(item.name for item in (iem_dir / "elements").iterdir()) == [
        "IME-000001.json",
        "IME-000002.json",
    ]
    assert sorted(
        item.name for item in (iem_dir / "relationships").iterdir()
    ) == ["IMR-000001.json"]


def test_exact_reassembly_is_idempotent(tmp_path):
    service, first = _persist_one(tmp_path)

    second = service.assemble_and_persist(
        assembly_input=_assembly_input(),
        assembly_provenance=replace(
            _provenance(),
            implementation_reference="different-call",
        ),
        created_at="2026-08-13T10:30:00Z",
    )

    assert second == first
    assert service.repository.list_snapshots("000042") == (first,)


def test_distinct_authorized_input_allocates_new_project_local_ids(tmp_path):
    service, first = _persist_one(tmp_path)

    second = service.assemble_and_persist(
        assembly_input=_assembly_input(
            set_id="MCS-000002",
            offset=2,
        ),
        assembly_provenance=_provenance(),
        created_at="2026-08-13T10:30:00Z",
    )

    assert first.manifest.internal_engineering_model_id == "IEM-000001"
    assert second.manifest.internal_engineering_model_id == "IEM-000002"
    assert tuple(
        item.internal_model_element_id for item in second.elements
    ) == ("IME-000003", "IME-000004")
    assert second.relationships[0].internal_model_relationship_id == (
        "IMR-000002"
    )


def test_repository_next_ids_do_not_reuse_gaps(tmp_path):
    service, _ = _persist_one(tmp_path)
    repository = service.repository

    assert repository.next_internal_engineering_model_id(
        "000042"
    ) == "IEM-000002"
    assert repository.next_internal_model_element_id(
        "000042"
    ) == "IME-000003"
    assert repository.next_internal_model_relationship_id(
        "000042"
    ) == "IMR-000002"


def test_direct_persist_rejects_project_wide_ime_and_imr_reuse(tmp_path):
    service, _ = _persist_one(tmp_path)
    repository = service.repository

    second_input = _assembly_input(
        set_id="MCS-000002",
        offset=2,
    )
    reused = InternalModelAssemblyService().assemble(
        project_id="000042",
        internal_engineering_model_id="IEM-000002",
        assembly_input=second_input,
        assembly_provenance=_provenance(),
        created_at="2026-08-13T10:30:00Z",
        occupied_internal_model_element_ids=(),
        occupied_internal_model_relationship_ids=(),
    )

    with pytest.raises(InternalModelPersistenceError):
        repository.persist_snapshot(reused)


def test_bundle_integrity_rejects_dangling_relationship_endpoint(tmp_path):
    _, snapshot = _persist_one(tmp_path)
    relationship = replace(
        snapshot.relationships[0],
        target_internal_model_element_id="IME-999999",
    )

    with pytest.raises(InternalModelIntegrityError):
        validate_internal_engineering_model_snapshot(
            replace(snapshot, relationships=(relationship,))
        )


def test_scan_reports_tampered_element_json(tmp_path):
    service, _ = _persist_one(tmp_path)
    element_path = (
        tmp_path
        / "000042"
        / "internal_models"
        / "IEM-000001"
        / "elements"
        / "IME-000001.json"
    )
    data = json.loads(element_path.read_text(encoding="utf-8"))
    data["name"] = "tampered"
    element_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = service.repository.scan_project("000042")
    assert result.snapshots == ()
    assert any(
        item.code == "invalid_internal_engineering_model"
        for item in result.issues
    )


def test_scan_reports_unexpected_iem_entry(tmp_path):
    service, _ = _persist_one(tmp_path)
    iem_dir = (
        tmp_path / "000042" / "internal_models" / "IEM-000001"
    )
    (iem_dir / "unexpected.txt").write_text("bad", encoding="utf-8")

    result = service.repository.scan_project("000042")
    assert any(
        item.code == "invalid_internal_engineering_model"
        for item in result.issues
    )


def test_scan_reports_interrupted_temp_publication(tmp_path):
    service, _ = _persist_one(tmp_path)
    temp = (
        tmp_path
        / "000042"
        / "internal_models"
        / ".create-IEM-000002.tmp"
    )
    temp.mkdir()

    result = service.repository.scan_project("000042")
    assert any(
        item.code == "internal_model_persistence_interrupted"
        for item in result.issues
    )

    with pytest.raises(InternalModelRecoveryRequiredError):
        service.repository.next_internal_engineering_model_id("000042")


def test_scan_rejects_symbolic_link_entries(tmp_path):
    service, _ = _persist_one(tmp_path)
    repository_root = tmp_path / "000042" / "internal_models"
    link = repository_root / "IEM-000999"
    try:
        link.symlink_to(repository_root / "IEM-000001", target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable on this platform")

    result = service.repository.scan_project("000042")
    assert any(
        item.code == "unexpected_internal_model_repository_entry"
        for item in result.issues
    )


def test_load_requires_explicit_existing_iem_id(tmp_path):
    service, _ = _persist_one(tmp_path)

    with pytest.raises(InternalEngineeringModelNotFoundError):
        service.repository.load_snapshot("000042", "IEM-000999")


def test_internal_models_root_symlink_is_rejected(tmp_path):
    _create_project(tmp_path)
    target = tmp_path / "outside"
    target.mkdir()
    repository_root = internal_models_path(tmp_path, "000042")
    try:
        repository_root.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable on this platform")

    repository = InternalModelRepository(root=tmp_path)
    result = repository.scan_project("000042")
    assert any(
        item.code == "unsafe_internal_model_path"
        for item in result.issues
    )


def test_list_snapshots_is_explicit_iem_order(tmp_path):
    service, first = _persist_one(tmp_path)
    second = service.assemble_and_persist(
        assembly_input=_assembly_input(
            set_id="MCS-000002",
            offset=2,
        ),
        assembly_provenance=_provenance(),
        created_at="2026-08-13T10:30:00Z",
    )

    assert service.repository.list_snapshots("000042") == (
        first,
        second,
    )
