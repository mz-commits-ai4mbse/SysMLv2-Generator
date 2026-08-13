"""Tests for atomic Phase-H Candidate Set persistence."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from modules.model_candidates import (
    ModelCandidateApprovedInputReference,
    ModelCandidateGenerationProvenance,
    ModelCandidateIntegrityError,
    ModelCandidatePersistenceError,
    ModelCandidateRecoveryRequiredError,
    ModelCandidateReferenceError,
    ModelCandidateRepository,
    ModelCandidateSetSnapshot,
    ModelCandidateNotFoundError,
    ModelDerivationRulesReference,
    ModelRelationshipEndpoint,
    ModelStructureProfileReference,
    RelationshipPriorityAssessment,
    RelationshipPriorityCriterionResult,
    StructuralComparabilityAssessment,
    StructuralProfileConformance,
    create_model_candidate_set_manifest,
    create_model_element_candidate,
    create_model_relationship_candidate,
)
from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.types import FrameworkTemplateReference


A = "a" * 64
B = "b" * 64
C = "c" * 64


def _clock():
    return datetime(2026, 8, 13, 6, 30, tzinfo=timezone.utc)


def _create_project(root: Path, project_id: str):
    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: project_id,
        clock=_clock,
    )
    workspace.create_project(f"Candidate Test {project_id}")


def _approved_ref():
    return ModelCandidateApprovedInputReference(
        approved_input_id="AIN-000001",
        content_fingerprint=A,
        stable_subject_key="subject.session",
        provenance_role="direct_support",
    )


def _conformance():
    return StructuralProfileConformance(
        status="conformant",
        finding_ids=(),
        conformance_fingerprint=B,
    )


def _bundle(
    *,
    project_id="000042",
    set_id="MCS-000001",
    element_id="MCE-000001",
    relationship_id="MCR-000001",
):
    element = create_model_element_candidate(
        project_id=project_id,
        candidate_set_id=set_id,
        model_element_candidate_id=element_id,
        candidate_subject_key="subject.session",
        comparison_anchor_id="system.functional.session",
        proposed_name="Manage Session",
        description=None,
        model_area="system_functional",
        element_type="function",
        framework_assignment=None,
        terminology_assignment=None,
        attributes=(),
        approved_input_references=(_approved_ref(),),
        derivation_rationale="Direct Approved Input support.",
        support_level="supported",
        assumptions=(),
        missing_information=(),
        structure_profile_conformance=_conformance(),
        predecessor_candidate_ids=(),
        created_at="2026-08-13T06:30:00Z",
    )
    relationship = create_model_relationship_candidate(
        project_id=project_id,
        candidate_set_id=set_id,
        model_relationship_candidate_id=relationship_id,
        relationship_choice_key=None,
        source=ModelRelationshipEndpoint(
            candidate_subject_key="subject.session",
            resolution_status="resolved",
            resolved_model_element_candidate_id=element_id,
            candidate_model_element_ids=(element_id,),
        ),
        target=ModelRelationshipEndpoint(
            candidate_subject_key="subject.session",
            resolution_status="resolved",
            resolved_model_element_candidate_id=element_id,
            candidate_model_element_ids=(element_id,),
        ),
        relationship_family="dependency",
        semantic_intent="self_test_dependency",
        directionality="source_to_target",
        approved_input_references=(_approved_ref(),),
        derivation_rationale="Persistence fixture.",
        supporting_evidence=("AIN-000001",),
        assumptions=(),
        missing_information=(),
        priority_assessment=RelationshipPriorityAssessment(
            priority_class="preferred",
            criterion_results=(
                RelationshipPriorityCriterionResult(
                    criterion="evidence_directness",
                    result="explicit",
                    rationale="Fixture evidence.",
                ),
            ),
            rationale="Fixture priority.",
        ),
        comparability_assessment=StructuralComparabilityAssessment(
            impact="neutral",
            comparison_anchor_ids=(),
            canonical_pattern_match=None,
            deviation_ids=(),
            rationale="Fixture comparability.",
        ),
        structure_profile_conformance=_conformance(),
        upstream_relationship_representation=None,
        predecessor_candidate_ids=(),
        created_at="2026-08-13T06:30:00Z",
    )
    manifest = create_model_candidate_set_manifest(
        project_id=project_id,
        candidate_set_id=set_id,
        predecessor_candidate_set_id=None,
        regeneration_reason=None,
        approved_input_references=(_approved_ref(),),
        framework_template_reference=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        model_structure_profile_reference=ModelStructureProfileReference(
            profile_id="TURING_MODEL_STRUCTURE",
            profile_version="1.0.0",
            profile_fingerprint=B,
        ),
        derivation_rules_reference=ModelDerivationRulesReference(
            context_id="CTX_SYSML_MODEL_DERIVATION_RULES",
            context_version="0.1.0",
            context_fingerprint=C,
        ),
        generation_provenance=ModelCandidateGenerationProvenance(
            method="deterministic_test",
            recipe_reference=None,
            agent_reference=None,
            model_reference=None,
            context_fingerprint=None,
        ),
        element_candidate_ids=(element_id,),
        relationship_candidate_ids=(relationship_id,),
        created_at="2026-08-13T06:30:00Z",
    )
    return manifest, (element,), (relationship,)


def test_persist_candidate_set_is_atomic_and_roundtrips(tmp_path):
    _create_project(tmp_path, "000042")
    repository = ModelCandidateRepository(root=tmp_path)
    manifest, elements, relationships = _bundle()

    persisted = repository.persist_candidate_set(
        manifest,
        element_candidates=elements,
        relationship_candidates=relationships,
    )

    assert persisted == ModelCandidateSetSnapshot(
        manifest=manifest,
        element_candidates=elements,
        relationship_candidates=relationships,
    )
    assert repository.load_candidate_set(
        "000042",
        "MCS-000001",
    ) == persisted
    assert repository.list_candidate_sets("000042") == (persisted,)
    sets_root = (
        tmp_path / "000042" / "model_candidates" / "sets"
    )
    assert not any(
        item.name.startswith(".create-")
        for item in sets_root.iterdir()
    )


def test_repository_allocates_project_local_ids(tmp_path):
    _create_project(tmp_path, "000042")
    repository = ModelCandidateRepository(root=tmp_path)
    assert repository.next_candidate_set_id("000042") == "MCS-000001"
    assert repository.next_element_candidate_id("000042") == "MCE-000001"
    assert (
        repository.next_relationship_candidate_id("000042")
        == "MCR-000001"
    )

    manifest, elements, relationships = _bundle()
    repository.persist_candidate_set(
        manifest,
        element_candidates=elements,
        relationship_candidates=relationships,
    )
    assert repository.next_candidate_set_id("000042") == "MCS-000002"
    assert repository.next_element_candidate_id("000042") == "MCE-000002"
    assert (
        repository.next_relationship_candidate_id("000042")
        == "MCR-000002"
    )


def test_same_ids_are_allowed_in_different_projects(tmp_path):
    _create_project(tmp_path, "000042")
    _create_project(tmp_path, "000043")
    repository = ModelCandidateRepository(root=tmp_path)

    for project_id in ("000042", "000043"):
        manifest, elements, relationships = _bundle(
            project_id=project_id
        )
        repository.persist_candidate_set(
            manifest,
            element_candidates=elements,
            relationship_candidates=relationships,
        )

    assert len(repository.list_candidate_sets("000042")) == 1
    assert len(repository.list_candidate_sets("000043")) == 1


def test_manifest_must_match_exact_persisted_children(tmp_path):
    _create_project(tmp_path, "000042")
    repository = ModelCandidateRepository(root=tmp_path)
    manifest, elements, relationships = _bundle()

    with pytest.raises(ModelCandidateIntegrityError):
        repository.persist_candidate_set(
            manifest,
            element_candidates=(),
            relationship_candidates=relationships,
        )
    assert not (
        tmp_path
        / "000042"
        / "model_candidates"
        / "sets"
        / "MCS-000001"
    ).exists()


def test_relationship_endpoints_must_resolve_inside_same_set(tmp_path):
    _create_project(tmp_path, "000042")
    repository = ModelCandidateRepository(root=tmp_path)
    manifest, elements, relationships = _bundle()
    bad_relationship = create_model_relationship_candidate(
        project_id="000042",
        candidate_set_id="MCS-000001",
        model_relationship_candidate_id="MCR-000001",
        relationship_choice_key=None,
        source=ModelRelationshipEndpoint(
            candidate_subject_key="subject.missing",
            resolution_status="resolved",
            resolved_model_element_candidate_id="MCE-000999",
            candidate_model_element_ids=("MCE-000999",),
        ),
        target=relationships[0].target,
        relationship_family="dependency",
        semantic_intent="bad_reference",
        directionality="source_to_target",
        approved_input_references=(_approved_ref(),),
        derivation_rationale="Bad fixture.",
        supporting_evidence=("AIN-000001",),
        assumptions=(),
        missing_information=(),
        priority_assessment=relationships[0].priority_assessment,
        comparability_assessment=relationships[0].comparability_assessment,
        structure_profile_conformance=_conformance(),
        upstream_relationship_representation=None,
        predecessor_candidate_ids=(),
        created_at="2026-08-13T06:30:00Z",
    )

    with pytest.raises(ModelCandidateReferenceError):
        repository.persist_candidate_set(
            manifest,
            element_candidates=elements,
            relationship_candidates=(bad_relationship,),
        )


def test_endpoint_subject_key_must_match_resolved_element(tmp_path):
    _create_project(tmp_path, "000042")
    repository = ModelCandidateRepository(root=tmp_path)
    manifest, elements, relationships = _bundle()
    bad_relationship = create_model_relationship_candidate(
        project_id="000042",
        candidate_set_id="MCS-000001",
        model_relationship_candidate_id="MCR-000001",
        relationship_choice_key=None,
        source=ModelRelationshipEndpoint(
            candidate_subject_key="subject.other",
            resolution_status="resolved",
            resolved_model_element_candidate_id="MCE-000001",
            candidate_model_element_ids=("MCE-000001",),
        ),
        target=relationships[0].target,
        relationship_family="dependency",
        semantic_intent="bad_subject",
        directionality="source_to_target",
        approved_input_references=(_approved_ref(),),
        derivation_rationale="Bad fixture.",
        supporting_evidence=("AIN-000001",),
        assumptions=(),
        missing_information=(),
        priority_assessment=relationships[0].priority_assessment,
        comparability_assessment=relationships[0].comparability_assessment,
        structure_profile_conformance=_conformance(),
        upstream_relationship_representation=None,
        predecessor_candidate_ids=(),
        created_at="2026-08-13T06:30:00Z",
    )

    with pytest.raises(ModelCandidateIntegrityError):
        repository.persist_candidate_set(
            manifest,
            element_candidates=elements,
            relationship_candidates=(bad_relationship,),
        )


def test_project_wide_candidate_ids_are_not_reused(tmp_path):
    _create_project(tmp_path, "000042")
    repository = ModelCandidateRepository(root=tmp_path)

    first = _bundle()
    repository.persist_candidate_set(
        first[0],
        element_candidates=first[1],
        relationship_candidates=first[2],
    )

    second = _bundle(
        set_id="MCS-000002",
        element_id="MCE-000001",
        relationship_id="MCR-000002",
    )
    with pytest.raises(ModelCandidateIntegrityError):
        repository.persist_candidate_set(
            second[0],
            element_candidates=second[1],
            relationship_candidates=second[2],
        )


def test_existing_set_is_immutable(tmp_path):
    _create_project(tmp_path, "000042")
    repository = ModelCandidateRepository(root=tmp_path)
    bundle = _bundle()
    repository.persist_candidate_set(
        bundle[0],
        element_candidates=bundle[1],
        relationship_candidates=bundle[2],
    )

    with pytest.raises(ModelCandidatePersistenceError):
        repository.persist_candidate_set(
            bundle[0],
            element_candidates=bundle[1],
            relationship_candidates=bundle[2],
        )


def test_load_missing_candidate_set_is_explicit(tmp_path):
    _create_project(tmp_path, "000042")
    repository = ModelCandidateRepository(root=tmp_path)

    with pytest.raises(ModelCandidateNotFoundError):
        repository.load_candidate_set(
            "000042",
            "MCS-000001",
        )


def test_interrupted_temporary_set_blocks_repository(tmp_path):
    _create_project(tmp_path, "000042")
    repository = ModelCandidateRepository(root=tmp_path)
    sets_root = (
        tmp_path / "000042" / "model_candidates" / "sets"
    )
    sets_root.mkdir(parents=True)
    (sets_root / ".create-MCS-000001.tmp").mkdir()

    result = repository.scan_project("000042")
    assert result.issues[0].code == (
        "model_candidate_persistence_interrupted"
    )
    with pytest.raises(ModelCandidateRecoveryRequiredError):
        repository.next_candidate_set_id("000042")
