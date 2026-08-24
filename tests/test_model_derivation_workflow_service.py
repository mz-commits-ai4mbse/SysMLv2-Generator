"""R5c tests for Human-controlled Phase-H derivation orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from modules.approved_input import ApprovedInputRepository
from modules.model_candidates import (
    ECO_DETERMINISTIC_MODE,
    LLM_ASSISTED_MODE,
    ModelCandidateReviewRepository,
    ModelDerivationWorkflowService,
)
from modules.project_workspace import ProjectWorkspace
from tests.test_hybrid_model_candidate_deriver import _element


PROJECT_ID = "318604"


def fixed_clock() -> datetime:
    return datetime(
        2026,
        8,
        21,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )


def _setup(tmp_path: Path):
    project_root = tmp_path / "repo"
    projects_root = project_root / "data" / "projects"

    workspace = ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: PROJECT_ID,
        clock=fixed_clock,
    )
    workspace.create_project("R5c Workflow")

    approved = ApprovedInputRepository(root=projects_root)
    approved.persist_manifest(
        _element(
            1,
            subject="subject.requirement",
            title="Requirement",
            classification="System Requirement",
            framework="System Requirements",
            information_type="requirement",
        )
    )

    service = ModelDerivationWorkflowService(
        project_root=project_root,
        approved_input_repository=approved,
        workspace=workspace,
    )
    return project_root, service


def test_assessment_recommends_eco_for_complete_mapping(
    tmp_path: Path,
) -> None:
    _root, service = _setup(tmp_path)

    assessment = service.assess(PROJECT_ID)

    assert assessment.recommended_mode == ECO_DETERMINISTIC_MODE
    assert assessment.eco_feasible is True
    assert assessment.mapped_count == 1


def test_eco_generation_persists_candidate_without_llm(
    tmp_path: Path,
) -> None:
    _root, service = _setup(tmp_path)

    snapshot = service.generate(
        PROJECT_ID,
        mode=ECO_DETERMINISTIC_MODE,
    )

    assert snapshot.manifest.candidate_set_id == "MCS-000001"
    assert snapshot.manifest.predecessor_candidate_set_id is None
    assert (
        snapshot.manifest.generation_provenance.method
        == "deterministic_profile_projection"
    )


def test_rejected_eco_candidate_recommends_llm_regeneration(
    tmp_path: Path,
) -> None:
    project_root, service = _setup(tmp_path)
    snapshot = service.generate(
        PROJECT_ID,
        mode=ECO_DETERMINISTIC_MODE,
    )

    reviews = ModelCandidateReviewRepository(
        root=project_root / "data" / "projects",
    )
    reviews.record_decision(
        PROJECT_ID,
        snapshot.manifest.candidate_set_id,
        target_type="element_candidate",
        candidate_id=(
            snapshot.element_candidates[0].model_element_candidate_id
        ),
        decision="rejected",
        reviewer_identity="reviewer",
        rationale="Try a different target-model projection.",
    )

    assessment = service.assess(
        PROJECT_ID,
        predecessor_candidate_set_id=snapshot.manifest.candidate_set_id,
    )

    assert assessment.recommended_mode == LLM_ASSISTED_MODE
    assert assessment.escalated_approved_input_ids == ("AIN-000001",)
