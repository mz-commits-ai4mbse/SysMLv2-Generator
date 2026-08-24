"""R4c.5c must not change legacy finalization read behavior."""

from types import SimpleNamespace

from modules.review_workspace.workflow_service import (
    ReviewApprovalWorkflowService,
)


def test_legacy_revision_short_circuits_before_processing_read():
    class ProcessingRepository:
        def load_run(self, *args):
            raise AssertionError(
                "Legacy finalization must not load Processing history."
            )

    service = object.__new__(ReviewApprovalWorkflowService)
    service._processing_repository = ProcessingRepository()

    revision = SimpleNamespace(
        review_items=(
            SimpleNamespace(
                original_report_locator="legacy:/elements/0",
            ),
        )
    )

    assert service._subject_relationship_finalization_issue_codes(
        SimpleNamespace(
            project_id="123456",
            processing_run_id="PRN-000001",
        ),
        SimpleNamespace(
            review_document_version_id="RVV-000001",
        ),
        revision,
    ) == ()
