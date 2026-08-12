"""G7.2 persisted successor lifecycle and recovery integration."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from modules.approved_input.promotion_service import (
    ApprovedInputPromotionService,
)
from modules.approved_input.repository import (
    ApprovedInputRepository,
)
from modules.human_review import HumanReviewRepository
from modules.project_sources import (
    ENGINEERING_SOURCE_ROLE,
    ProjectSourceRegistry,
)
from modules.project_workspace import ProjectWorkspace
from modules.review_workspace.errors import ReviewWorkspaceError
from modules.review_workspace.paths import reviewed_report_path
from modules.review_workspace.repository import (
    ReviewWorkspaceRepository,
)
from modules.review_workspace.workflow_editing import (
    ReviewItemEditRequest,
    proposal_selection_key,
)
from modules.review_workspace.workflow_lineage import (
    ReviewProposalActionRequest,
)
from modules.review_workspace.workflow_service import (
    ReviewApprovalWorkflowService,
)

from tests.test_phase_g_end_to_end_integration import (
    PROJECT_ID,
    REVIEWER,
    RUN_ID,
    DeterministicClock,
    _persist_processing_run,
)


@dataclass(frozen=True, slots=True)
class _Scenario:
    service: ReviewApprovalWorkflowService
    approved_repository: ApprovedInputRepository
    review_repository: ReviewWorkspaceRepository
    source_manifest: object
    review_document_id: str
    predecessor_version_id: str
    predecessor_revision_id: str
    predecessor_item_id: str
    predecessor_artifact_set: object


def _promoted_scenario(
    tmp_path: Path,
) -> _Scenario:
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
        "G7 Successor Lifecycle"
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

    processing_repository, _ = _persist_processing_run(
        repository_root=repository_root,
        projects_root=projects_root,
        source_manifest=source_manifest,
    )

    review_repository = ReviewWorkspaceRepository(
        root=projects_root
    )
    human_review_repository = HumanReviewRepository(
        root=projects_root,
        clock=clock,
    )
    approved_repository = ApprovedInputRepository(
        root=projects_root
    )
    promotion_service = ApprovedInputPromotionService(
        root=projects_root,
        clock=clock,
        review_repository=review_repository,
        source_registry=source_registry,
        processing_repository=processing_repository,
        human_review_repository=human_review_repository,
        approved_input_repository=approved_repository,
    )
    service = ReviewApprovalWorkflowService(
        root=projects_root,
        repository_root=repository_root,
        clock=clock,
        source_registry=source_registry,
        processing_repository=processing_repository,
        review_repository=review_repository,
        human_review_repository=human_review_repository,
        approved_input_repository=approved_repository,
        promotion_service=promotion_service,
    )

    opened = service.open_or_create_review(
        PROJECT_ID,
        RUN_ID,
        opened_by=REVIEWER,
    )
    item = opened.workspace.revision.review_items[0]
    details = service.proposal_details(
        PROJECT_ID,
        opened.review_document_id,
        opened.review_document_version_id,
        item.review_item_id,
    )
    accepted = service.accept_proposal(
        PROJECT_ID,
        opened.review_document_id,
        opened.review_document_version_id,
        item.review_item_id,
        request=ReviewProposalActionRequest(
            expected_revision_id=(
                opened.workspace.revision.review_revision_id
            ),
            expected_item_content_fingerprint=(
                item.item_content_fingerprint
            ),
            proposal_key=details[0].proposal_key,
        ),
        actor_identity=REVIEWER,
    )
    accepted_item = accepted.revision.review_items[0]

    service.record_finalization_decision(
        PROJECT_ID,
        accepted.document.review_document_id,
        accepted.version.review_document_version_id,
        decision="confirm",
        reviewer_identity=REVIEWER,
        rationale="Initial G7 lifecycle baseline accepted.",
    )
    finalized = service.finalize_review_version(
        PROJECT_ID,
        accepted.document.review_document_id,
        accepted.version.review_document_version_id,
    )
    promoted = service.promote_review_version(
        PROJECT_ID,
        accepted.document.review_document_id,
        accepted.version.review_document_version_id,
    )

    assert promoted.created_approved_input_ids == (
        "AIN-000001",
    )
    assert tuple(
        manifest.approved_input_id
        for manifest
        in approved_repository.list_active_approved_inputs(
            PROJECT_ID
        )
    ) == ("AIN-000001",)

    return _Scenario(
        service=service,
        approved_repository=approved_repository,
        review_repository=review_repository,
        source_manifest=source_manifest,
        review_document_id=(
            accepted.document.review_document_id
        ),
        predecessor_version_id=(
            accepted.version.review_document_version_id
        ),
        predecessor_revision_id=(
            accepted.revision.review_revision_id
        ),
        predecessor_item_id=accepted_item.review_item_id,
        predecessor_artifact_set=finalized.artifact_set,
    )


def _reopen(
    scenario: _Scenario,
):
    bundle = scenario.service.reopen_review_version(
        PROJECT_ID,
        scenario.review_document_id,
        scenario.predecessor_version_id,
        reopen_reason="Successor lifecycle verification.",
        actor_identity=REVIEWER,
    )
    view = scenario.service.workspace_view(
        PROJECT_ID,
        scenario.review_document_id,
        bundle.version.review_document_version_id,
    )

    assert view.version.version_state == "draft"
    assert (
        view.version.predecessor_version_id
        == scenario.predecessor_version_id
    )
    assert len(view.revision.review_items) == 1

    item = view.revision.review_items[0]
    assert item.lineage_operation == "carried_forward"
    assert item.derived_from_review_item_ids == (
        scenario.predecessor_item_id,
    )
    assert item.review_item_id != scenario.predecessor_item_id

    return view


def _finalize_and_promote(
    scenario: _Scenario,
    view,
):
    preview = scenario.service.finalization_preview(
        PROJECT_ID,
        scenario.review_document_id,
        view.version.review_document_version_id,
    )
    assert preview.eligible_for_confirmation is True
    assert preview.blocking_issue_codes == ()

    decision = scenario.service.record_finalization_decision(
        PROJECT_ID,
        scenario.review_document_id,
        view.version.review_document_version_id,
        decision="confirm",
        reviewer_identity=REVIEWER,
        rationale="Successor detailed review completed.",
    )
    finalized = scenario.service.finalize_review_version(
        PROJECT_ID,
        scenario.review_document_id,
        view.version.review_document_version_id,
    )
    promoted = scenario.service.promote_review_version(
        PROJECT_ID,
        scenario.review_document_id,
        view.version.review_document_version_id,
    )

    assert decision.decision == "confirm"
    assert finalized.workspace.version.version_state == "finalized"

    return finalized, promoted


def _active_ids(
    scenario: _Scenario,
) -> tuple[str, ...]:
    return tuple(
        manifest.approved_input_id
        for manifest
        in scenario.approved_repository.list_active_approved_inputs(
            PROJECT_ID
        )
    )


def _trace_by_id(
    scenario: _Scenario,
):
    return {
        item.approved_input_id: item
        for item
        in scenario.service.approved_input_traceability(
            PROJECT_ID,
            scenario.review_document_id,
        )
    }


def test_unchanged_successor_reuses_active_ain_and_preserves_predecessor(
    tmp_path: Path,
) -> None:
    scenario = _promoted_scenario(tmp_path)

    predecessor_before = (
        scenario.service.finalized_artifact_set(
            PROJECT_ID,
            scenario.review_document_id,
            scenario.predecessor_version_id,
        )
    )

    successor = _reopen(scenario)
    _, promoted = _finalize_and_promote(
        scenario,
        successor,
    )

    assert promoted.created_approved_input_ids == ()
    assert promoted.reused_approved_input_ids == (
        "AIN-000001",
    )
    assert promoted.lifecycle_event_ids == ()
    assert _active_ids(scenario) == ("AIN-000001",)
    assert scenario.approved_repository.list_events(
        PROJECT_ID
    ) == ()

    predecessor_after = (
        scenario.service.finalized_artifact_set(
            PROJECT_ID,
            scenario.review_document_id,
            scenario.predecessor_version_id,
        )
    )
    assert predecessor_after == predecessor_before
    assert (
        predecessor_after.artifact_set_fingerprint
        == scenario.predecessor_artifact_set
        .artifact_set_fingerprint
    )


def test_changed_successor_creates_new_ain_and_supersedes_predecessor(
    tmp_path: Path,
) -> None:
    scenario = _promoted_scenario(tmp_path)
    successor = _reopen(scenario)
    item = successor.revision.review_items[0]

    selected_keys = tuple(
        proposal_selection_key(reference)
        for reference in item.proposal_references
        if reference.review_state == "selected"
    )
    assert len(selected_keys) == 1

    updated = replace(
        item.current_content,
        primary_text=(
            item.current_content.primary_text
            + " Successor review adds a material clarification."
        ),
        human_rationale=(
            "Material successor clarification accepted."
        ),
    )

    changed = scenario.service.save_item_review(
        PROJECT_ID,
        scenario.review_document_id,
        successor.version.review_document_version_id,
        item.review_item_id,
        request=ReviewItemEditRequest(
            expected_revision_id=(
                successor.revision.review_revision_id
            ),
            expected_item_content_fingerprint=(
                item.item_content_fingerprint
            ),
            updated_content=updated,
            selected_proposal_keys=selected_keys,
            review_outcome="accepted_with_modification",
            rationale=(
                "Material successor clarification accepted."
            ),
        ),
        actor_identity=REVIEWER,
    )

    _, promoted = _finalize_and_promote(
        scenario,
        changed,
    )

    assert promoted.created_approved_input_ids == (
        "AIN-000002",
    )
    assert promoted.reused_approved_input_ids == ()
    assert promoted.lifecycle_event_ids == (
        "AIE-000001",
    )
    assert _active_ids(scenario) == ("AIN-000002",)

    event = scenario.approved_repository.list_events(
        PROJECT_ID
    )[0]
    assert event.event_type == "superseded"
    assert event.approved_input_id == "AIN-000001"
    assert event.successor_approved_input_id == "AIN-000002"

    trace = _trace_by_id(scenario)
    assert trace["AIN-000001"].authority_state == "superseded"
    assert trace["AIN-000002"].authority_state == "active"


@pytest.mark.parametrize(
    ("outcome", "reason_code"),
    (
        (
            "rejected",
            "successor_review_rejected",
        ),
        (
            "out_of_scope",
            "successor_review_out_of_scope",
        ),
    ),
)
def test_withdrawn_successor_revokes_active_predecessor(
    tmp_path: Path,
    outcome: str,
    reason_code: str,
) -> None:
    scenario = _promoted_scenario(tmp_path)
    successor = _reopen(scenario)
    item = successor.revision.review_items[0]

    rationale = (
        "The successor review explicitly withdraws this subject."
    )
    withdrawn = scenario.service.save_item_review(
        PROJECT_ID,
        scenario.review_document_id,
        successor.version.review_document_version_id,
        item.review_item_id,
        request=ReviewItemEditRequest(
            expected_revision_id=(
                successor.revision.review_revision_id
            ),
            expected_item_content_fingerprint=(
                item.item_content_fingerprint
            ),
            updated_content=replace(
                item.current_content,
                human_rationale=rationale,
            ),
            selected_proposal_keys=(),
            review_outcome=outcome,
            rationale=rationale,
        ),
        actor_identity=REVIEWER,
    )

    _, promoted = _finalize_and_promote(
        scenario,
        withdrawn,
    )

    assert promoted.created_approved_input_ids == ()
    assert promoted.reused_approved_input_ids == ()
    assert promoted.skipped_review_item_ids == (
        withdrawn.revision.review_items[0].review_item_id,
    )
    assert promoted.lifecycle_event_ids == (
        "AIE-000001",
    )
    assert _active_ids(scenario) == ()

    event = scenario.approved_repository.list_events(
        PROJECT_ID
    )[0]
    assert event.event_type == "revoked"
    assert event.reason_code == reason_code
    assert event.successor_approved_input_id is None

    trace = _trace_by_id(scenario)
    assert trace["AIN-000001"].authority_state == "revoked"


def test_deferred_successor_keeps_existing_active_authority(
    tmp_path: Path,
) -> None:
    scenario = _promoted_scenario(tmp_path)
    successor = _reopen(scenario)
    item = successor.revision.review_items[0]

    deferred = scenario.service.save_item_review(
        PROJECT_ID,
        scenario.review_document_id,
        successor.version.review_document_version_id,
        item.review_item_id,
        request=ReviewItemEditRequest(
            expected_revision_id=(
                successor.revision.review_revision_id
            ),
            expected_item_content_fingerprint=(
                item.item_content_fingerprint
            ),
            updated_content=item.current_content,
            selected_proposal_keys=(),
            review_outcome="deferred",
            rationale=None,
        ),
        actor_identity=REVIEWER,
    )

    _, promoted = _finalize_and_promote(
        scenario,
        deferred,
    )

    assert promoted.created_approved_input_ids == ()
    assert promoted.reused_approved_input_ids == ()
    assert promoted.skipped_review_item_ids == (
        deferred.revision.review_items[0].review_item_id,
    )
    assert promoted.lifecycle_event_ids == ()
    assert _active_ids(scenario) == ("AIN-000001",)
    assert scenario.approved_repository.list_events(
        PROJECT_ID
    ) == ()

    trace = _trace_by_id(scenario)
    assert trace["AIN-000001"].authority_state == "active"


def test_tampered_finalized_predecessor_blocks_reopening_without_successor(
    tmp_path: Path,
) -> None:
    scenario = _promoted_scenario(tmp_path)

    report_path = reviewed_report_path(
        scenario.review_repository.root,
        PROJECT_ID,
        scenario.review_document_id,
        scenario.predecessor_version_id,
    )
    report_path.write_text(
        report_path.read_text(encoding="utf-8")
        + "\nTampered after finalization.\n",
        encoding="utf-8",
    )

    with pytest.raises(ReviewWorkspaceError):
        scenario.service.reopen_review_version(
            PROJECT_ID,
            scenario.review_document_id,
            scenario.predecessor_version_id,
            reopen_reason=(
                "This must fail before successor creation."
            ),
            actor_identity=REVIEWER,
        )

    scan = scenario.review_repository.scan_project(
        PROJECT_ID
    )
    assert all(
        version.review_document_version_id != "RVV-000002"
        for version in scan.versions
    )
    assert _active_ids(scenario) == ("AIN-000001",)
    assert scenario.approved_repository.list_events(
        PROJECT_ID
    ) == ()
