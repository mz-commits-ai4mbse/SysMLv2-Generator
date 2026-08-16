from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.guided_workflow import (
    GuidedWorkflowDetailReadService,
    GuidedWorkflowValidationError,
)


def candidate(
    candidate_set_id,
    predecessor=None,
    *,
    element_count=1,
    relationship_count=1,
):
    return SimpleNamespace(
        manifest=SimpleNamespace(
            candidate_set_id=candidate_set_id,
            predecessor_candidate_set_id=predecessor,
        ),
        element_candidates=tuple(
            SimpleNamespace()
            for _ in range(element_count)
        ),
        relationship_candidates=tuple(
            SimpleNamespace()
            for _ in range(relationship_count)
        ),
    )


def revision(
    review_id,
    revision_id,
    predecessor=None,
    *,
    validation_status="valid",
    created_at="2026-08-16T08:00:00Z",
):
    return SimpleNamespace(
        revision=SimpleNamespace(
            final_model_review_id=review_id,
            final_model_review_revision_id=revision_id,
            predecessor_revision_id=predecessor,
            validation_status=validation_status,
            created_at=created_at,
        )
    )


def output(
    output_package_id,
    *,
    published_at="2026-08-16T08:00:00Z",
):
    return SimpleNamespace(
        manifest=SimpleNamespace(
            output_package_id=output_package_id,
            published_at=published_at,
        )
    )


class CandidateRepository:
    def __init__(self, candidate_sets=(), issues=()):
        self.candidate_sets = tuple(candidate_sets)
        self.issues = tuple(issues)

    def scan_project(self, project_id):
        return SimpleNamespace(
            candidate_sets=self.candidate_sets,
            issues=self.issues,
        )


class ProposalService:
    def __init__(self):
        self.calls = []

    def load_model_proposal(self, project_id, candidate_set_id):
        self.calls.append((project_id, candidate_set_id))
        return SimpleNamespace(
            project_id=project_id,
            candidate_set_id=candidate_set_id,
        )


class FinalRepository:
    def __init__(self, revisions=(), issues=()):
        self.revisions = tuple(revisions)
        self.issues = tuple(issues)

    def scan(self, project_id):
        return SimpleNamespace(
            revisions=self.revisions,
            issues=self.issues,
        )


class FinalReadService:
    def __init__(self):
        self.calls = []

    def load_view(self, project_id, review_id, revision_id):
        self.calls.append(
            (project_id, review_id, revision_id)
        )
        return SimpleNamespace(
            project_id=project_id,
            final_model_review_id=review_id,
            final_model_review_revision_id=revision_id,
        )


class ReleaseService:
    def __init__(self):
        self.calls = []

    def evaluate(self, project_id, review_id, revision_id):
        self.calls.append(
            (project_id, review_id, revision_id)
        )
        return SimpleNamespace(
            release_status="ready_for_approval"
        )


class OutputRepository:
    def __init__(self, packages=(), issues=()):
        self.packages = tuple(packages)
        self.issues = tuple(issues)
        self.load_calls = []
        self.read_calls = []

    def scan_project(self, project_id):
        return SimpleNamespace(
            packages=self.packages,
            issues=self.issues,
        )

    def load_output(self, project_id, output_package_id):
        self.load_calls.append(
            (project_id, output_package_id)
        )
        return next(
            item
            for item in self.packages
            if (
                item.manifest.output_package_id
                == output_package_id
            )
        )

    def read_file(
        self,
        project_id,
        output_package_id,
        relative_path,
    ):
        self.read_calls.append(
            (
                project_id,
                output_package_id,
                relative_path,
            )
        )
        return b"package content"


def service(
    *,
    candidates=(),
    candidate_issues=(),
    revisions=(),
    final_issues=(),
    outputs=(),
    output_issues=(),
):
    proposal = ProposalService()
    final_read = FinalReadService()
    release = ReleaseService()
    output_repository = OutputRepository(
        packages=outputs,
        issues=output_issues,
    )

    instance = GuidedWorkflowDetailReadService(
        ".",
        candidate_repository=CandidateRepository(
            candidates,
            candidate_issues,
        ),
        model_proposal_service=proposal,
        final_review_repository=FinalRepository(
            revisions,
            final_issues,
        ),
        final_review_service=final_read,
        final_release_service=release,
        output_repository=output_repository,
    )

    return (
        instance,
        proposal,
        final_read,
        release,
        output_repository,
    )


def test_model_proposal_not_available_without_candidate_set():
    instance, proposal, *_ = service()

    result = instance.load_model_proposal("123456")

    assert result.status == "not_available"
    assert result.proposal is None
    assert proposal.calls == []


def test_unique_candidate_head_is_safe_display_default():
    instance, proposal, *_ = service(
        candidates=(
            candidate("MCS-000001"),
            candidate(
                "MCS-000002",
                predecessor="MCS-000001",
            ),
        )
    )

    result = instance.load_model_proposal("123456")

    assert result.status == "ready"
    assert result.selected_entity_id == "MCS-000002"
    assert proposal.calls == [
        ("123456", "MCS-000002")
    ]


def test_multiple_candidate_heads_require_explicit_selection():
    instance, proposal, *_ = service(
        candidates=(
            candidate("MCS-000001"),
            candidate("MCS-000002"),
        )
    )

    result = instance.load_model_proposal("123456")

    assert result.status == "selection_required"
    assert {
        item.entity_id
        for item in result.options
    } == {
        "MCS-000001",
        "MCS-000002",
    }
    assert proposal.calls == []


def test_explicit_historical_candidate_set_is_loaded_exactly():
    instance, proposal, *_ = service(
        candidates=(
            candidate("MCS-000001"),
            candidate(
                "MCS-000002",
                predecessor="MCS-000001",
            ),
        )
    )

    result = instance.load_model_proposal(
        "123456",
        "MCS-000001",
    )

    assert result.status == "ready"
    assert result.selected_entity_id == "MCS-000001"
    assert proposal.calls == [
        ("123456", "MCS-000001")
    ]


def test_candidate_repository_issue_fails_closed():
    instance, *_ = service(
        candidate_issues=(
            SimpleNamespace(code="broken"),
        )
    )

    with pytest.raises(GuidedWorkflowValidationError):
        instance.load_model_proposal("123456")


def test_unique_final_review_head_loads_exact_revision_and_gate():
    instance, _, final_read, release, _ = service(
        revisions=(
            revision("FMR-000001", "FRV-000001"),
            revision(
                "FMR-000001",
                "FRV-000002",
                predecessor="FRV-000001",
            ),
        )
    )

    result = instance.load_final_model_review(
        "123456"
    )

    assert result.status == "ready"
    assert result.selected_entity_id == "FRV-000002"
    assert result.final_model_review_id == "FMR-000001"
    assert final_read.calls == [
        ("123456", "FMR-000001", "FRV-000002")
    ]
    assert release.calls == [
        ("123456", "FMR-000001", "FRV-000002")
    ]


def test_multiple_final_review_heads_require_selection():
    instance, _, final_read, release, _ = service(
        revisions=(
            revision("FMR-000001", "FRV-000001"),
            revision("FMR-000002", "FRV-000002"),
        )
    )

    result = instance.load_final_model_review(
        "123456"
    )

    assert result.status == "selection_required"
    assert len(result.options) == 2
    assert final_read.calls == []
    assert release.calls == []


def test_explicit_final_review_revision_is_loaded_exactly():
    instance, _, final_read, _, _ = service(
        revisions=(
            revision("FMR-000001", "FRV-000001"),
            revision(
                "FMR-000001",
                "FRV-000002",
                predecessor="FRV-000001",
            ),
        )
    )

    result = instance.load_final_model_review(
        "123456",
        "FRV-000001",
    )

    assert result.status == "ready"
    assert result.selected_entity_id == "FRV-000001"
    assert final_read.calls == [
        ("123456", "FMR-000001", "FRV-000001")
    ]


def test_single_output_package_is_safe_display_default():
    instance, *_, output_repository = service(
        outputs=(output("OUT-000001"),)
    )

    result = instance.load_published_output(
        "123456"
    )

    assert result.status == "ready"
    assert result.selected_entity_id == "OUT-000001"
    assert output_repository.load_calls == [
        ("123456", "OUT-000001")
    ]


def test_multiple_outputs_require_explicit_selection():
    instance, *_, output_repository = service(
        outputs=(
            output("OUT-000001"),
            output("OUT-000002"),
        )
    )

    result = instance.load_published_output(
        "123456"
    )

    assert result.status == "selection_required"
    assert len(result.options) == 2
    assert output_repository.load_calls == []


def test_explicit_output_package_is_loaded_exactly():
    instance, *_, output_repository = service(
        outputs=(
            output("OUT-000001"),
            output("OUT-000002"),
        )
    )

    result = instance.load_published_output(
        "123456",
        "OUT-000002",
    )

    assert result.status == "ready"
    assert result.selected_entity_id == "OUT-000002"
    assert output_repository.load_calls == [
        ("123456", "OUT-000002")
    ]


def test_published_output_file_read_delegates_exact_identity():
    instance, *_, output_repository = service(
        outputs=(output("OUT-000001"),)
    )

    content = instance.read_published_output_file(
        "123456",
        "OUT-000001",
        "model/system.sysml",
    )

    assert content == b"package content"
    assert output_repository.read_calls == [
        (
            "123456",
            "OUT-000001",
            "model/system.sysml",
        )
    ]
