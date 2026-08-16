from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.guided_workflow import (
    GuidedWorkflowWriteError,
    GuidedWorkflowWriteService,
)


class CandidateReviews:
    def __init__(self, *, error=None):
        self.calls = []
        self.error = error

    def record_decision(
        self,
        project_id,
        candidate_set_id,
        *,
        target_type,
        candidate_id,
        decision,
        reviewer_identity,
        rationale=None,
    ):
        self.calls.append(
            {
                "project_id": project_id,
                "candidate_set_id": candidate_set_id,
                "target_type": target_type,
                "candidate_id": candidate_id,
                "decision": decision,
                "reviewer_identity": reviewer_identity,
                "rationale": rationale,
            }
        )

        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            model_candidate_review_decision_id="MCD-000001",
            decision=decision,
        )


class FinalChanges:
    def __init__(self, *, error=None):
        self.calls = []
        self.error = error

    def submit_change(
        self,
        project_id,
        final_model_review_id,
        final_model_review_revision_id,
        **kwargs,
    ):
        self.calls.append(
            (
                project_id,
                final_model_review_id,
                final_model_review_revision_id,
                kwargs,
            )
        )

        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            proposal=SimpleNamespace(
                final_model_review_change_proposal_id="FCP-000001"
            ),
            route=SimpleNamespace(
                authority_route="phase_h_candidate_review"
            ),
        )


class FinalPublication:
    def __init__(self, *, error=None):
        self.calls = []
        self.error = error

    def publish_revision(
        self,
        project_id,
        final_model_review_id,
        final_model_review_revision_id,
    ):
        self.calls.append(
            (
                project_id,
                final_model_review_id,
                final_model_review_revision_id,
            )
        )

        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            manifest=SimpleNamespace(
                output_package_id="OUT-000001"
            )
        )


class FinalRelease:
    def __init__(self, *, error=None):
        self.calls = []
        self.error = error

    def approve_for_publication(
        self,
        project_id,
        final_model_review_id,
        final_model_review_revision_id,
        *,
        reviewer_identity,
        rationale=None,
    ):
        self.calls.append(
            {
                "project_id": project_id,
                "final_model_review_id": final_model_review_id,
                "final_model_review_revision_id": (
                    final_model_review_revision_id
                ),
                "reviewer_identity": reviewer_identity,
                "rationale": rationale,
            }
        )

        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            gate=SimpleNamespace(
                release_status="approved_for_publication"
            ),
            decision=SimpleNamespace(
                final_model_review_decision_id="FRD-000001"
            ),
        )


def service(
    *,
    candidate_reviews=None,
    final_changes=None,
    final_release=None,
    final_publication=None,
):
    return GuidedWorkflowWriteService(
        ".",
        candidate_review_repository=(
            CandidateReviews()
            if candidate_reviews is None
            else candidate_reviews
        ),
        final_review_repository=SimpleNamespace(),
        final_change_service=(
            FinalChanges()
            if final_changes is None
            else final_changes
        ),
        final_release_service=(
            FinalRelease()
            if final_release is None
            else final_release
        ),
        final_publication_service=(
            FinalPublication()
            if final_publication is None
            else final_publication
        ),
    )


def test_candidate_review_delegates_exact_explicit_target():
    repository = CandidateReviews()
    instance = service(candidate_reviews=repository)

    result = instance.record_candidate_review_decision(
        "123456",
        "MCS-000004",
        target_type="element_candidate",
        candidate_id="MCE-000019",
        decision="accepted",
        reviewer_identity="Reviewer A",
    )

    assert result.model_candidate_review_decision_id == "MCD-000001"
    assert repository.calls == [
        {
            "project_id": "123456",
            "candidate_set_id": "MCS-000004",
            "target_type": "element_candidate",
            "candidate_id": "MCE-000019",
            "decision": "accepted",
            "reviewer_identity": "Reviewer A",
            "rationale": None,
        }
    ]


def test_candidate_review_preserves_explicit_exception_rationale():
    repository = CandidateReviews()
    instance = service(candidate_reviews=repository)

    instance.record_candidate_review_decision(
        "123456",
        "MCS-000004",
        target_type="relationship_candidate",
        candidate_id="MCR-000011",
        decision="accepted_exception",
        reviewer_identity="Reviewer A",
        rationale="Intentional structural deviation.",
    )

    assert repository.calls[0]["decision"] == "accepted_exception"
    assert repository.calls[0]["rationale"] == (
        "Intentional structural deviation."
    )


def test_final_change_delegates_exact_review_revision_and_route_input():
    changes = FinalChanges()
    instance = service(final_changes=changes)

    result = instance.submit_final_model_change(
        "123456",
        "FMR-000003",
        "FRV-000008",
        surface="diagram",
        classification="engineering_semantics",
        reviewer_feedback="The dependency direction is incorrect.",
        created_by="Reviewer A",
        internal_model_relationship_id="IEMR-000007",
        request_agent_reproposal=True,
        requested_agent_personalities=("systems_engineer",),
    )

    assert (
        result.proposal.final_model_review_change_proposal_id
        == "FCP-000001"
    )

    project_id, review_id, revision_id, kwargs = changes.calls[0]

    assert project_id == "123456"
    assert review_id == "FMR-000003"
    assert revision_id == "FRV-000008"
    assert kwargs["surface"] == "diagram"
    assert kwargs["classification"] == "engineering_semantics"
    assert kwargs["internal_model_relationship_id"] == "IEMR-000007"
    assert kwargs["request_agent_reproposal"] is True
    assert kwargs["requested_agent_personalities"] == (
        "systems_engineer",
    )


def test_publication_delegates_exact_approved_revision():
    publication = FinalPublication()
    instance = service(final_publication=publication)

    result = instance.publish_final_model_review_revision(
        "123456",
        "FMR-000003",
        "FRV-000008",
    )

    assert result.manifest.output_package_id == "OUT-000001"
    assert publication.calls == [
        (
            "123456",
            "FMR-000003",
            "FRV-000008",
        )
    ]


def test_publication_failures_are_fail_closed():
    error = RuntimeError("publication failed")
    publication = FinalPublication(error=error)
    instance = service(final_publication=publication)

    with pytest.raises(GuidedWorkflowWriteError) as caught:
        instance.publish_final_model_review_revision(
            "123456",
            "FMR-000003",
            "FRV-000008",
        )

    assert caught.value.__cause__ is error


def test_release_approval_delegates_exact_review_revision():
    release = FinalRelease()
    instance = service(final_release=release)

    result = instance.approve_final_model_for_publication(
        "123456",
        "FMR-000003",
        "FRV-000008",
        reviewer_identity="Reviewer A",
        rationale="Validated model accepted for release.",
    )

    assert (
        result.gate.release_status
        == "approved_for_publication"
    )

    assert release.calls == [
        {
            "project_id": "123456",
            "final_model_review_id": "FMR-000003",
            "final_model_review_revision_id": "FRV-000008",
            "reviewer_identity": "Reviewer A",
            "rationale": "Validated model accepted for release.",
        }
    ]


@pytest.mark.parametrize(
    ("dependency_name", "call"),
    (
        (
            "candidate",
            lambda instance: instance.record_candidate_review_decision(
                "123456",
                "MCS-000001",
                target_type="element_candidate",
                candidate_id="MCE-000001",
                decision="accepted",
                reviewer_identity="Reviewer A",
            ),
        ),
        (
            "change",
            lambda instance: instance.submit_final_model_change(
                "123456",
                "FMR-000001",
                "FRV-000001",
                surface="diagram",
                classification="engineering_semantics",
                reviewer_feedback="Change requested.",
                created_by="Reviewer A",
            ),
        ),
        (
            "release",
            lambda instance: instance.approve_final_model_for_publication(
                "123456",
                "FMR-000001",
                "FRV-000001",
                reviewer_identity="Reviewer A",
            ),
        ),
    ),
)
def test_domain_write_failures_are_fail_closed(
    dependency_name,
    call,
):
    error = RuntimeError("domain write failed")

    candidate = CandidateReviews(
        error=error if dependency_name == "candidate" else None
    )
    changes = FinalChanges(
        error=error if dependency_name == "change" else None
    )
    release = FinalRelease(
        error=error if dependency_name == "release" else None
    )

    instance = service(
        candidate_reviews=candidate,
        final_changes=changes,
        final_release=release,
    )

    with pytest.raises(GuidedWorkflowWriteError) as caught:
        call(instance)

    assert caught.value.__cause__ is error


def test_write_service_exposes_only_explicit_revision_publication():
    instance = service()

    assert hasattr(
        instance,
        "publish_final_model_review_revision",
    )
    assert not hasattr(instance, "publish")
    assert not hasattr(instance, "publish_latest")
