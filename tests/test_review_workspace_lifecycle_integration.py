"""End-to-end integration test for the complete G4 lifecycle."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from modules.human_review import (
    HumanReviewRepository,
)
from modules.review_workspace.effective_decisions_manifest import (
    create_effective_review_decision_set,
)
from modules.review_workspace.finalization_authorization import (
    authorize_persisted_review_document_finalization,
)
from modules.review_workspace.finalization_validation import (
    assess_review_document_finalization,
    create_review_document_finalization_target,
)
from modules.review_workspace.finalized_artifact_set import (
    create_finalized_review_artifact_set,
)
from modules.review_workspace.paths import (
    finalized_review_path,
)
from modules.review_workspace.reviewed_document_manifest import (
    create_finalized_reviewed_document,
)
from modules.review_workspace.reviewed_report_renderer import (
    create_rendered_reviewed_report,
)
from modules.review_workspace.revision_manifest import (
    create_review_revision,
)

from tests.test_finalized_artifact_loading import (
    _persisted_artifact_set,
)


def _second_decision_clock() -> datetime:
    return datetime(
        2026,
        8,
        6,
        19,
        15,
        tzinfo=timezone.utc,
    )


def test_complete_finalize_reopen_refinalize_lifecycle(
    tmp_path: Path,
) -> None:
    root, repository, first_artifact_set = (
        _persisted_artifact_set(tmp_path)
    )

    first_finalized_directory = finalized_review_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    first_artifact_bytes_before = {
        path.name: path.read_bytes()
        for path in first_finalized_directory.iterdir()
    }

    first_version_before = repository.load_version(
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    first_revision_before = repository.load_revision(
        "000001",
        "RVD-000001",
        "RVV-000001",
        "RVR-000001",
    )

    reopened = repository.reopen_finalized_version(
        "000001",
        "RVD-000001",
        "RVV-000001",
        reopen_reason=(
            "Clarify and reconfirm the reviewed "
            "engineering statement."
        ),
        opened_by="reviewer@example.com",
        timestamp="2026-08-06T18:30:00Z",
    )

    assert (
        reopened.version.review_document_version_id
        == "RVV-000002"
    )
    assert reopened.version.version_state == "draft"
    assert (
        reopened.version.predecessor_version_id
        == "RVV-000001"
    )
    assert (
        reopened.initial_revision.review_revision_id
        == "RVR-000002"
    )
    assert (
        reopened.initial_revision
        .scoped_review_action_ids
        == ()
    )

    carried_item = (
        reopened.initial_revision.review_items[0]
    )

    assert (
        carried_item.lineage_operation
        == "carried_forward"
    )
    assert (
        carried_item.derived_from_review_item_ids
        == ("RIT-000001",)
    )
    assert (
        carried_item.stable_subject_key
        == first_revision_before
        .review_items[0]
        .stable_subject_key
    )

    next_revision = create_review_revision(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000002",
        review_revision_id="RVR-000003",
        revision_sequence=2,
        predecessor_revision_id="RVR-000002",
        review_items=(
            reopened.initial_revision.review_items
        ),
        scoped_review_action_ids=(),
        created_by="reviewer@example.com",
        timestamp="2026-08-06T19:00:00Z",
    )

    (
        successor_draft_version,
        persisted_successor_revision,
    ) = repository.append_revision(next_revision)

    assert (
        successor_draft_version.head_revision_id
        == "RVR-000003"
    )
    assert (
        persisted_successor_revision
        == next_revision
    )

    document = repository.load_document(
        "000001",
        "RVD-000001",
    )

    assessment = assess_review_document_finalization(
        document,
        successor_draft_version,
        persisted_successor_revision,
    )
    target = (
        create_review_document_finalization_target(
            assessment
        )
    )

    human_review_repository = HumanReviewRepository(
        root=root,
        clock=_second_decision_clock,
    )
    second_decision = (
        human_review_repository.record_decision(
            "000001",
            target,
            review_mode="detailed_review",
            decision="confirm",
            reviewer_identity="moritz",
        )
    )

    authorized = (
        authorize_persisted_review_document_finalization(
            successor_draft_version,
            persisted_successor_revision,
            assessment,
            human_review_repository,
            timestamp="2026-08-06T19:20:00Z",
        )
    )

    second_finalized_version = (
        repository.persist_authorized_finalization(
            authorized
        )
    )

    assert (
        second_finalized_version.version_state
        == "finalized"
    )
    assert (
        second_finalized_version
        .finalized_revision_id
        == "RVR-000003"
    )
    assert (
        second_finalized_version
        .finalization_decision_id
        == second_decision
        .human_review_decision_id
    )

    second_reviewed_document = (
        create_finalized_reviewed_document(
            document,
            second_finalized_version,
            persisted_successor_revision,
            authorized.authorization,
        )
    )
    second_effective_decisions = (
        create_effective_review_decision_set(
            second_reviewed_document,
            persisted_successor_revision,
        )
    )
    second_reviewed_report = (
        create_rendered_reviewed_report(
            second_reviewed_document,
            second_effective_decisions,
        )
    )
    second_artifact_set = (
        create_finalized_review_artifact_set(
            second_reviewed_document,
            second_effective_decisions,
            second_reviewed_report,
        )
    )

    persisted_second_artifact_set = (
        repository.persist_finalized_artifact_set(
            second_artifact_set
        )
    )
    loaded_second_artifact_set = (
        repository.load_finalized_artifact_set(
            "000001",
            "RVD-000001",
            "RVV-000002",
        )
    )

    assert (
        persisted_second_artifact_set
        == second_artifact_set
    )
    assert (
        loaded_second_artifact_set
        == second_artifact_set
    )
    assert (
        second_artifact_set
        .artifact_set_fingerprint
        != first_artifact_set
        .artifact_set_fingerprint
    )

    loaded_first_artifact_set = (
        repository.load_finalized_artifact_set(
            "000001",
            "RVD-000001",
            "RVV-000001",
        )
    )
    first_version_after = repository.load_version(
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    first_revision_after = repository.load_revision(
        "000001",
        "RVD-000001",
        "RVV-000001",
        "RVR-000001",
    )
    first_artifact_bytes_after = {
        path.name: path.read_bytes()
        for path in first_finalized_directory.iterdir()
    }

    assert (
        loaded_first_artifact_set
        == first_artifact_set
    )
    assert first_version_after == first_version_before
    assert (
        first_revision_after
        == first_revision_before
    )
    assert (
        first_artifact_bytes_after
        == first_artifact_bytes_before
    )

    scan = repository.scan_project("000001")

    assert scan.issues == ()
    assert tuple(
        (
            version.review_document_version_id,
            version.version_number,
            version.version_state,
            version.predecessor_version_id,
        )
        for version in scan.versions
    ) == (
        (
            "RVV-000001",
            1,
            "finalized",
            None,
        ),
        (
            "RVV-000002",
            2,
            "finalized",
            "RVV-000001",
        ),
    )
    assert tuple(
        (
            revision.review_document_version_id,
            revision.review_revision_id,
            revision.revision_sequence,
        )
        for revision in scan.revisions
    ) == (
        (
            "RVV-000001",
            "RVR-000001",
            1,
        ),
        (
            "RVV-000002",
            "RVR-000002",
            1,
        ),
        (
            "RVV-000002",
            "RVR-000003",
            2,
        ),
    )
