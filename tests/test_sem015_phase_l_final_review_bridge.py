from types import SimpleNamespace

import pytest

from modules.guided_workflow.errors import GuidedWorkflowWriteError
from modules.guided_workflow.write_service import GuidedWorkflowWriteService


PROJECT = "120412"
IEM = "IEM-000002"
ARTIFACT_FP = "a" * 64
VALIDATION_FP = "b" * 64


class ArtifactRepo:
    def __init__(self, artifact):
        self.artifact = artifact

    def load(self, project_id, iem_id):
        assert project_id == PROJECT
        assert iem_id == IEM
        return self.artifact


class FinalReviewRepo:
    def __init__(self, *, existing=()):
        self.existing = tuple(existing)
        self.created = 0
        self.appended = []

    def scan(self, project_id):
        assert project_id == PROJECT
        manifests = (
            (SimpleNamespace(final_model_review_id="FMR-000001"),)
            if self.created or self.existing
            else ()
        )
        return SimpleNamespace(
            review_manifests=manifests,
            issues=(),
        )

    def create_review(self, project_id):
        assert project_id == PROJECT
        self.created += 1
        return SimpleNamespace(final_model_review_id="FMR-000001")

    def list_revisions(self, project_id, review_id):
        assert project_id == PROJECT
        assert review_id == "FMR-000001"
        return self.existing

    def append_revision(
        self,
        project_id,
        review_id,
        *,
        artifact_set,
        validation_result,
    ):
        self.appended.append(
            (project_id, review_id, artifact_set, validation_result)
        )
        return SimpleNamespace(
            revision=SimpleNamespace(
                final_model_review_id=review_id,
                final_model_review_revision_id="FRV-000001",
            )
        )


def artifact():
    return SimpleNamespace(
        project_id=PROJECT,
        source_internal_engineering_model_id=IEM,
        content_fingerprint=ARTIFACT_FP,
        units=(SimpleNamespace(unit_id="GSU-000001"),),
    )


def validation():
    return SimpleNamespace(
        project_id=PROJECT,
        source_internal_engineering_model_id=IEM,
        source_artifact_set_fingerprint=ARTIFACT_FP,
        content_fingerprint=VALIDATION_FP,
        validation_status="valid",
        publication_gate="passed",
    )


def service(final_repo):
    value = object.__new__(GuidedWorkflowWriteService)
    value.project_root = None
    value._authority_backed_sysml = ArtifactRepo(artifact())
    value._final_reviews = final_repo
    return value


def test_phase_l_bridge_creates_review_and_exact_revision():
    reviews = FinalReviewRepo()
    writes = service(reviews)

    result = writes.create_phase_l_final_model_review(
        PROJECT,
        IEM,
        validation_result=validation(),
    )

    assert result.revision.final_model_review_id == "FMR-000001"
    assert result.revision.final_model_review_revision_id == "FRV-000001"
    assert reviews.created == 1
    assert len(reviews.appended) == 1
    assert reviews.appended[0][2].content_fingerprint == ARTIFACT_FP
    assert reviews.appended[0][3].content_fingerprint == VALIDATION_FP


def test_phase_l_bridge_reuses_exact_existing_revision():
    existing = SimpleNamespace(
        revision=SimpleNamespace(
            source_internal_engineering_model_id=IEM,
            generated_artifact_set_fingerprint=ARTIFACT_FP,
            validation_result_fingerprint=VALIDATION_FP,
        )
    )
    reviews = FinalReviewRepo(existing=(existing,))
    writes = service(reviews)

    result = writes.create_phase_l_final_model_review(
        PROJECT,
        IEM,
        validation_result=validation(),
    )

    assert result is existing
    assert reviews.appended == []


def test_phase_l_bridge_rejects_wrong_validation_binding():
    reviews = FinalReviewRepo()
    writes = service(reviews)
    wrong = validation()
    wrong.source_artifact_set_fingerprint = "c" * 64

    with pytest.raises(
        GuidedWorkflowWriteError,
        match="exact generated artifact",
    ):
        writes.create_phase_l_final_model_review(
            PROJECT,
            IEM,
            validation_result=wrong,
        )

    assert reviews.created == 0
    assert reviews.appended == []
