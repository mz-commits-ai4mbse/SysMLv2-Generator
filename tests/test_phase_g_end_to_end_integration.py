"""G7.1 real persisted Phase-G end-to-end integration."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

from modules.approved_input.promotion_service import (
    ApprovedInputPromotionService,
)
from modules.approved_input.repository import (
    ApprovedInputRepository,
)
from modules.human_review import HumanReviewRepository
from modules.project_processing import (
    create_processing_artifact_reference,
    create_processing_event,
    create_processing_run_manifest,
    create_semantic_reference_version,
    derive_processing_run_state,
)
from modules.project_processing.repository import (
    ProjectProcessingRepository,
)
from modules.project_sources import (
    ENGINEERING_SOURCE_ROLE,
    ProjectSourceRegistry,
)
from modules.project_workspace import ProjectWorkspace
from modules.review_workspace.repository import (
    ReviewWorkspaceRepository,
)
from modules.review_workspace.workflow_lineage import (
    ReviewProposalActionRequest,
)
from modules.review_workspace.workflow_service import (
    ReviewApprovalWorkflowService,
)


PROJECT_ID = "123456"
RUN_ID = "RUN-000001"
ATTEMPT_ID = "ATT-000001"
REVIEWER = "reviewer@example.com"

AGENT_A = "AGENT_DERIVATION_A"
AGENT_B = "AGENT_DERIVATION_B"
PERSONA_A = "PERSONA_DERIVATION_A"
PERSONA_B = "PERSONA_DERIVATION_B"


class DeterministicClock:
    """Return increasing UTC datetimes for real repository timestamps."""

    def __init__(self) -> None:
        self._value = datetime(
            2026,
            8,
            8,
            14,
            0,
            0,
            tzinfo=timezone.utc,
        )

    def __call__(self) -> datetime:
        current = self._value
        self._value = self._value + timedelta(seconds=1)
        return current


def _candidate(
    candidate_id: str,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "element_type": "system",
        "candidate_name": "Traceability System",
        "description": (
            "System responsible for preserving engineering traceability."
        ),
        "source_basis": ["SRC_INFO_001"],
        "assigned_source_information": [
            {
                "source_info_id": "SRC_INFO_001",
                "source_statement": (
                    "The system shall preserve source traceability."
                ),
                "assignment_type": "defines_element",
                "confidence": "high",
            }
        ],
        "confidence": "high",
        "generation_readiness": "ready",
        "missing_information": [],
        "rationale_summary": (
            "The element is directly supported by the source."
        ),
    }


def _derivation_output(
    candidate_id: str,
) -> dict[str, object]:
    return {
        "candidate_model_elements": [
            _candidate(candidate_id),
        ],
        "explicit_source_links": [],
        "sysml_model_buildability": [],
        "missing_information_for_model_building": [],
        "possible_but_unsupported_interpretations": [],
        "model_artifact_assessments": [],
        "cross_artifact_observations": [],
        "blocked_generation_tasks": [],
    }


def _agent_wrapper(
    *,
    agent_id: str,
    persona_id: str,
    candidate_id: str,
) -> bytes:
    wrapper = {
        "team_id": "TEAM_DERIVATION_ASSESSMENT",
        "agent_id": agent_id,
        "persona_id": persona_id,
        "run_index": 1,
        "status": "completed",
        "output_text": json.dumps(
            _derivation_output(candidate_id),
            ensure_ascii=False,
        ),
    }
    return json.dumps(
        wrapper,
        indent=2,
        ensure_ascii=False,
    ).encode("utf-8")


def _consensus_report() -> bytes:
    group = {
        "group_key": (
            "candidate_model_element::system::"
            "traceability system"
        ),
        "item_type": "candidate_model_element",
        "agreement_level": "full_agreement",
        "total_agents": 2,
        "supporting_agents": [
            AGENT_A,
            AGENT_B,
        ],
        "value_distribution": {
            "ready": [
                AGENT_A,
                AGENT_B,
            ]
        },
        "representative_value": (
            "Traceability System is ready for review."
        ),
        "review_required": False,
        "reason": (
            "Both derivation agents identify the same stable subject."
        ),
        "agent_values": {
            AGENT_A: "Traceability System.",
            AGENT_B: "Traceability System.",
        },
    }
    report = {
        "consensus_report_id": (
            "CONSENSUS_TEAM_DERIVATION_G7_001"
        ),
        "team_id": "TEAM_DERIVATION_ASSESSMENT",
        "task_name": (
            "Assess downstream model derivation support"
        ),
        "created_at": "2026-08-08T12:10:00+00:00",
        "total_agents": 2,
        "agent_ids": [
            AGENT_A,
            AGENT_B,
        ],
        "agent_labels": {
            AGENT_A: PERSONA_A,
            AGENT_B: PERSONA_B,
        },
        "summary": {
            "total_groups": 1,
            "full_agreement": 1,
            "majority_agreement": 0,
            "majority_with_disagreement": 0,
            "minority_interpretation": 0,
            "conflict": 0,
            "review_required": 0,
        },
        "groups": [group],
    }
    return json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
    ).encode("utf-8")


def _persist_artifact(
    repository_root: Path,
    *,
    artifact_type: str,
    artifact_id: str,
    relative_tail: Path,
    content: bytes,
):
    relative_path = (
        Path("data")
        / "projects"
        / PROJECT_ID
        / "runs"
        / RUN_ID
        / "artifacts"
        / artifact_type
        / "agentic_ingestion"
        / ATTEMPT_ID
        / relative_tail
    )
    target = repository_root / relative_path
    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    target.write_bytes(content)

    return create_processing_artifact_reference(
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        content_fingerprint=hashlib.sha256(
            content
        ).hexdigest(),
        repository_relative_path=relative_path.as_posix(),
    )


def _published_artifacts(
    repository_root: Path,
):
    agent_a = _persist_artifact(
        repository_root,
        artifact_type="agent_outputs",
        artifact_id="AGOUT-ATT-000001-0001",
        relative_tail=(
            Path("03_derivation_assessment")
            / "team_derivation_assessment"
            / AGENT_A.lower()
            / "agent_01.json"
        ),
        content=_agent_wrapper(
            agent_id=AGENT_A,
            persona_id=PERSONA_A,
            candidate_id="ELEM_001",
        ),
    )
    agent_b = _persist_artifact(
        repository_root,
        artifact_type="agent_outputs",
        artifact_id="AGOUT-ATT-000001-0002",
        relative_tail=(
            Path("03_derivation_assessment")
            / "team_derivation_assessment"
            / AGENT_B.lower()
            / "agent_01.json"
        ),
        content=_agent_wrapper(
            agent_id=AGENT_B,
            persona_id=PERSONA_B,
            candidate_id="ELEM_101",
        ),
    )
    consensus = _persist_artifact(
        repository_root,
        artifact_type="consensus_reports",
        artifact_id="CONS-ATT-000001-0001",
        relative_tail=(
            Path("03_derivation_assessment")
            / "team_derivation_assessment_consensus_1.json"
        ),
        content=_consensus_report(),
    )
    review = _persist_artifact(
        repository_root,
        artifact_type="review_reports",
        artifact_id="REVIEW-ATT-000001-0001",
        relative_tail=Path("ingestion_review_report.md"),
        content=(
            b"# Ingestion Review\n\n"
            b"One traceable model candidate is ready for human review.\n"
        ),
    )
    summary = _persist_artifact(
        repository_root,
        artifact_type="run_summaries",
        artifact_id="SUMMARY-ATT-000001-0001",
        relative_tail=Path("run_summary.json"),
        content=json.dumps(
            {
                "run_id": RUN_ID,
                "attempt_id": ATTEMPT_ID,
                "state": "awaiting_review",
            },
            indent=2,
        ).encode("utf-8"),
    )
    return (
        agent_a,
        agent_b,
        consensus,
        review,
        summary,
    )


def _persist_processing_run(
    *,
    repository_root: Path,
    projects_root: Path,
    source_manifest,
):
    repository = ProjectProcessingRepository(
        root=projects_root
    )
    semantic_version = (
        create_semantic_reference_version(
            reference_system_id="TURING_CORE_VOCABULARY",
            reference_version="1.0.0",
        )
    )
    manifest = create_processing_run_manifest(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        source_id=source_manifest.source_id,
        source_sha256=source_manifest.sha256,
        source_role_snapshot=source_manifest.source_role,
        workflow_profile="engineering_source_processing",
        configuration_fingerprint="b" * 64,
        framework_template_id="TURING_RFLP_FRAMEWORK",
        framework_template_version="1.0.0",
        semantic_reference_versions=(semantic_version,),
        timestamp="2026-08-08T12:00:00Z",
    )
    created = create_processing_event(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        event_id="EVT-000001",
        event_sequence=1,
        previous_state=None,
        next_state="created",
        processing_stage=None,
        event_type="run_created",
        attempt_id=None,
        reason_code="run_created",
        artifact_references=(),
        timestamp="2026-08-08T12:00:01Z",
        previous_event_fingerprint=None,
    )
    repository.create_run(
        manifest,
        created,
    )

    started = create_processing_event(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        event_id="EVT-000002",
        event_sequence=2,
        previous_state="created",
        next_state="running",
        processing_stage="agentic_ingestion",
        event_type="stage_started",
        attempt_id=ATTEMPT_ID,
        reason_code="agentic_ingestion_started",
        artifact_references=(),
        timestamp="2026-08-08T12:00:02Z",
        previous_event_fingerprint=created.event_fingerprint,
    )
    repository.append_event(started)

    references = _published_artifacts(
        repository_root
    )
    published = create_processing_event(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        event_id="EVT-000003",
        event_sequence=3,
        previous_state="running",
        next_state="running",
        processing_stage="agentic_ingestion",
        event_type="artifact_published",
        attempt_id=ATTEMPT_ID,
        reason_code=(
            "agentic_ingestion_artifacts_published"
        ),
        artifact_references=references,
        timestamp="2026-08-08T12:00:03Z",
        previous_event_fingerprint=started.event_fingerprint,
    )
    repository.append_event(published)

    requested = create_processing_event(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        event_id="EVT-000004",
        event_sequence=4,
        previous_state="running",
        next_state="awaiting_review",
        processing_stage="agentic_ingestion",
        event_type="review_requested",
        attempt_id=ATTEMPT_ID,
        reason_code="agentic_ingestion_review_requested",
        artifact_references=(),
        timestamp="2026-08-08T12:00:04Z",
        previous_event_fingerprint=(
            published.event_fingerprint
        ),
    )
    history = repository.append_event(
        requested
    )

    return repository, history


def test_real_persisted_phase_g_reaches_active_phase_h_boundary(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    projects_root = (
        repository_root
        / "data"
        / "projects"
    )
    projects_root.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    clock = DeterministicClock()

    ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: PROJECT_ID,
        clock=clock,
    ).create_project(
        "G7 Phase G End-to-End"
    )

    source_path = tmp_path / "requirements.md"
    source_path.write_text(
        "# Requirements\n\n"
        "The system shall preserve source traceability.\n",
        encoding="utf-8",
    )
    source_registry = ProjectSourceRegistry(
        root=projects_root,
        clock=clock,
    )
    source_manifest = source_registry.register_source(
        PROJECT_ID,
        source_path,
        source_role=ENGINEERING_SOURCE_ROLE,
    )

    processing_repository, processing_history = (
        _persist_processing_run(
            repository_root=repository_root,
            projects_root=projects_root,
            source_manifest=source_manifest,
        )
    )
    processing_state = derive_processing_run_state(
        processing_history
    )
    assert processing_state.run_state == "awaiting_review"
    assert (
        processing_state.latest_attempt_id
        == ATTEMPT_ID
    )

    review_repository = ReviewWorkspaceRepository(
        root=projects_root
    )
    human_review_repository = HumanReviewRepository(
        root=projects_root,
        clock=clock,
    )
    approved_input_repository = (
        ApprovedInputRepository(
            root=projects_root
        )
    )
    promotion_service = ApprovedInputPromotionService(
        root=projects_root,
        clock=clock,
        review_repository=review_repository,
        source_registry=source_registry,
        processing_repository=processing_repository,
        human_review_repository=human_review_repository,
        approved_input_repository=(
            approved_input_repository
        ),
    )
    service = ReviewApprovalWorkflowService(
        root=projects_root,
        repository_root=repository_root,
        clock=clock,
        source_registry=source_registry,
        processing_repository=processing_repository,
        review_repository=review_repository,
        human_review_repository=(
            human_review_repository
        ),
        approved_input_repository=(
            approved_input_repository
        ),
        promotion_service=promotion_service,
    )

    opened = service.open_or_create_review(
        PROJECT_ID,
        RUN_ID,
        opened_by=REVIEWER,
    )
    assert opened.created is True

    workspace = opened.workspace
    assert (
        workspace.document.project_id
        == PROJECT_ID
    )
    assert (
        workspace.document.source_id
        == source_manifest.source_id
    )
    assert (
        workspace.document.source_sha256
        == source_manifest.sha256
    )
    assert (
        workspace.document.processing_run_id
        == RUN_ID
    )
    assert workspace.document.attempt_id == ATTEMPT_ID
    assert workspace.version.version_state == "draft"
    assert len(workspace.revision.review_items) == 1

    item = workspace.revision.review_items[0]
    assert item.review_item_kind == "element"
    assert item.effective_review_outcome == "open"
    assert len(item.proposal_references) == 2

    details = service.proposal_details(
        PROJECT_ID,
        workspace.document.review_document_id,
        workspace.version.review_document_version_id,
        item.review_item_id,
    )
    assert len(details) == 2

    accepted = service.accept_proposal(
        PROJECT_ID,
        workspace.document.review_document_id,
        workspace.version.review_document_version_id,
        item.review_item_id,
        request=ReviewProposalActionRequest(
            expected_revision_id=(
                workspace.revision.review_revision_id
            ),
            expected_item_content_fingerprint=(
                item.item_content_fingerprint
            ),
            proposal_key=details[0].proposal_key,
        ),
        actor_identity=REVIEWER,
    )
    accepted_item = accepted.revision.review_items[0]
    assert (
        accepted_item.effective_review_outcome
        == "accepted_as_generated"
    )
    assert tuple(
        reference.review_state
        for reference
        in accepted_item.proposal_references
    ).count("selected") == 1

    finalization_preview = service.finalization_preview(
        PROJECT_ID,
        accepted.document.review_document_id,
        accepted.version.review_document_version_id,
    )
    assert (
        finalization_preview
        .eligible_for_confirmation
        is True
    )
    assert (
        finalization_preview
        .blocking_issue_codes
        == ()
    )

    decision = service.record_finalization_decision(
        PROJECT_ID,
        accepted.document.review_document_id,
        accepted.version.review_document_version_id,
        decision="confirm",
        reviewer_identity=REVIEWER,
        rationale=(
            "G7 end-to-end detailed review completed."
        ),
    )
    assert decision.decision == "confirm"
    assert decision.review_mode == "detailed_review"

    confirmed = service.finalization_preview(
        PROJECT_ID,
        accepted.document.review_document_id,
        accepted.version.review_document_version_id,
    )
    assert confirmed.has_exact_confirmation is True
    assert confirmed.can_finalize is True

    finalized = service.finalize_review_version(
        PROJECT_ID,
        accepted.document.review_document_id,
        accepted.version.review_document_version_id,
    )
    assert (
        finalized.workspace.version.version_state
        == "finalized"
    )
    assert finalized.artifact_filenames == (
        "reviewed_document.json",
        "effective_decisions.json",
        "reviewed_report.md",
    )

    promotion_preview = service.promotion_preview(
        PROJECT_ID,
        accepted.document.review_document_id,
        accepted.version.review_document_version_id,
    )
    assert promotion_preview.eligible_for_promotion is True
    assert promotion_preview.blocking_issue_codes == ()
    assert promotion_preview.promotable_item_ids == (
        accepted_item.review_item_id,
    )

    promoted = service.promote_review_version(
        PROJECT_ID,
        accepted.document.review_document_id,
        accepted.version.review_document_version_id,
    )
    assert promoted.created_approved_input_ids == (
        "AIN-000001",
    )
    assert promoted.reused_approved_input_ids == ()
    assert promoted.lifecycle_event_ids == ()

    active = (
        approved_input_repository
        .list_active_approved_inputs(PROJECT_ID)
    )
    assert len(active) == 1

    approved = active[0]
    assert approved.approved_input_id == "AIN-000001"
    assert approved.authority_state == "active"
    assert approved.source_id == source_manifest.source_id
    assert approved.source_sha256 == source_manifest.sha256
    assert approved.processing_run_id == RUN_ID
    assert approved.attempt_id == ATTEMPT_ID
    assert (
        approved.review_document_id
        == accepted.document.review_document_id
    )
    assert (
        approved.review_document_version_id
        == accepted.version.review_document_version_id
    )
    assert (
        approved.review_revision_id
        == accepted.revision.review_revision_id
    )
    assert approved.review_item_id == accepted_item.review_item_id
    assert (
        approved.finalization_decision_id
        == decision.human_review_decision_id
    )
    assert (
        approved.finalized_artifact_set_fingerprint
        == finalized.artifact_set.artifact_set_fingerprint
    )

    traceability = service.approved_input_traceability(
        PROJECT_ID,
        accepted.document.review_document_id,
    )
    assert len(traceability) == 1
    assert traceability[0].approved_input_id == "AIN-000001"
    assert traceability[0].authority_state == "active"
    assert traceability[0].is_active is True

    assert (
        review_repository
        .scan_project(PROJECT_ID)
        .issues
        == ()
    )
    assert (
        approved_input_repository
        .scan_project(PROJECT_ID)
        .issues
        == ()
    )
