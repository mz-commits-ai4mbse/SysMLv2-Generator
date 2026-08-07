"""Integration tests across G5 promotion, lifecycle and Phase H reading."""

from pathlib import Path

from modules.approved_input.lifecycle_service import (
    ApprovedInputLifecycleService,
)
from modules.approved_input.promotion_service import (
    ApprovedInputPromotionService,
)
from modules.approved_input.repository import ApprovedInputRepository
from modules.project_workspace import ProjectWorkspace

from tests.test_approved_input_lifecycle_service import (
    _HumanReviewRepository as _LifecycleHumanReviewRepository,
)
from tests.test_approved_input_promotion_eligibility import _inputs
from tests.test_approved_input_promotion_service import (
    _HumanReviewRepository,
    _ProcessingRepository,
    _ReviewRepository,
    _SourceRegistry,
    _clock,
)
from tests.test_approved_input_successor_reconciliation import (
    _predecessor,
    _projected_manifest,
)


PROJECT_ID = "000001"
REVIEW_DOCUMENT_ID = "RVD-000001"
REVIEW_VERSION_ID = "RVV-000001"


def _repository(tmp_path: Path) -> ApprovedInputRepository:
    root = tmp_path / "projects"
    ProjectWorkspace(
        root=root,
        id_generator=lambda: PROJECT_ID,
        clock=_clock,
    ).create_project("G5 Integration")
    return ApprovedInputRepository(root=root)


def test_promote_reuse_invalidate_and_phase_h_read_are_consistent(
    tmp_path: Path,
) -> None:
    document, artifact_set, source, history, decision = _inputs()
    repository = _repository(tmp_path)
    service = ApprovedInputPromotionService(
        root=repository.root,
        clock=_clock,
        review_repository=_ReviewRepository(
            document,
            artifact_set,
        ),
        source_registry=_SourceRegistry(source),
        processing_repository=_ProcessingRepository(history),
        human_review_repository=_HumanReviewRepository(decision),
        approved_input_repository=repository,
    )

    first = service.promote_finalized_version(
        PROJECT_ID,
        REVIEW_DOCUMENT_ID,
        REVIEW_VERSION_ID,
    )
    active_after_first = repository.list_active_approved_inputs(
        PROJECT_ID
    )

    second = service.promote_finalized_version(
        PROJECT_ID,
        REVIEW_DOCUMENT_ID,
        REVIEW_VERSION_ID,
    )
    active_after_second = repository.list_active_approved_inputs(
        PROJECT_ID
    )

    assert first.created_approved_input_ids == ("AIN-000001",)
    assert second.created_approved_input_ids == ()
    assert second.reused_approved_input_ids == ("AIN-000001",)
    assert active_after_first == first.promoted_manifests
    assert active_after_second == first.promoted_manifests
    assert repository.list_events(PROJECT_ID) == ()

    lifecycle = ApprovedInputLifecycleService(
        root=repository.root,
        clock=_clock,
        approved_input_repository=repository,
        human_review_repository=(
            _LifecycleHumanReviewRepository(decision)
        ),
    )
    lifecycle.invalidate(
        PROJECT_ID,
        "AIN-000001",
        reason_code="source_integrity_failure",
        actor_identity="integrity-checker",
    )

    assert repository.list_active_approved_inputs(PROJECT_ID) == ()
    assert repository.list_manifests(PROJECT_ID) == first.promoted_manifests


def test_supersession_exposes_only_successor_to_phase_h(
    tmp_path: Path,
) -> None:
    _, artifact_set, _, _, decision = _inputs()
    repository = _repository(tmp_path)
    predecessor = _predecessor(changed=True)
    successor = _projected_manifest(
        approved_input_id="AIN-000002"
    )
    repository.persist_manifest(predecessor)
    repository.persist_manifest(successor)
    lifecycle = ApprovedInputLifecycleService(
        root=repository.root,
        clock=_clock,
        approved_input_repository=repository,
        human_review_repository=(
            _LifecycleHumanReviewRepository(decision)
        ),
    )

    events = lifecycle.reconcile_finalized_version(
        artifact_set,
        (successor,),
    )

    assert tuple(
        event.event_type for event in events
    ) == ("superseded",)
    assert repository.list_active_approved_inputs(PROJECT_ID) == (
        successor,
    )
    assert repository.list_manifests(PROJECT_ID) == (
        predecessor,
        successor,
    )
