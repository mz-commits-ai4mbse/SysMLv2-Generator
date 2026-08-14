"""Normative Final Human release gate for one exact Final Model Review revision."""

from __future__ import annotations

from dataclasses import asdict, replace

from .errors import (
    FinalModelReviewIntegrityError,
    FinalModelReviewReleaseGateError,
)
from .fingerprints import calculate_json_fingerprint
from .types import (
    FINAL_MODEL_REVIEW_RELEASE_STATUSES,
    FinalModelReviewReleaseBlocker,
    FinalModelReviewReleaseGateResult,
)


def evaluate_final_model_review_release_gate(
    repository,
    project_id: str,
    final_model_review_id: str,
    final_model_review_revision_id: str,
) -> FinalModelReviewReleaseGateResult:
    """Evaluate release readiness without selecting a revision implicitly.

    Mandatory review items and Human change proposals are immutable evidence
    against the exact FRV. Their resolution is represented by a successor FRV,
    never by mutating or deleting the original evidence.
    """

    bundle = repository.load_revision(
        project_id,
        final_model_review_id,
        final_model_review_revision_id,
    )
    revision = bundle.revision

    revisions = repository.list_revisions(
        project_id,
        final_model_review_id,
    )
    items = repository.list_items(
        project_id,
        final_model_review_id,
        final_model_review_revision_id,
    )
    change_proposals = repository.list_change_proposals(
        project_id,
        final_model_review_id,
        final_model_review_revision_id,
    )
    decisions = tuple(
        item
        for item in repository.list_decisions(
            project_id,
            final_model_review_id,
        )
        if item.target.final_model_review_revision_id
        == final_model_review_revision_id
    )

    blockers: list[FinalModelReviewReleaseBlocker] = []

    if (
        revision.validation_status != "valid"
        or revision.publication_gate != "passed"
    ):
        blockers.append(
            FinalModelReviewReleaseBlocker(
                code="validation_not_passed",
                message=(
                    "Final release requires the exact review revision to bind "
                    "a Phase-K result with validation_status=valid and "
                    "publication_gate=passed."
                ),
                reference_ids=(
                    revision.validation_result_fingerprint,
                ),
            )
        )

    mandatory_items = tuple(
        sorted(
            (
                item
                for item in items
                if item.mandatory
            ),
            key=lambda item: item.final_model_review_item_id,
        )
    )
    if mandatory_items:
        blockers.append(
            FinalModelReviewReleaseBlocker(
                code="mandatory_review_items_unresolved",
                message=(
                    "Mandatory Final Model Review items remain on this exact "
                    "revision. Resolve them through the owning authority and "
                    "create a successor review revision."
                ),
                reference_ids=tuple(
                    item.final_model_review_item_id
                    for item in mandatory_items
                ),
            )
        )

    if change_proposals:
        blockers.append(
            FinalModelReviewReleaseBlocker(
                code="change_proposals_unresolved",
                message=(
                    "Human change proposal(s) are bound to this exact review "
                    "revision. Resolve them and create the appropriate successor "
                    "review revision before release."
                ),
                reference_ids=tuple(
                    item.final_model_review_change_proposal_id
                    for item in change_proposals
                ),
            )
        )

    prior_nonapproval = tuple(
        item
        for item in decisions
        if item.decision in {"changes_requested", "rejected"}
    )
    if prior_nonapproval:
        blockers.append(
            FinalModelReviewReleaseBlocker(
                code="prior_nonapproval_decision",
                message=(
                    "This exact review revision already has a Human "
                    "changes-requested or rejected decision. It cannot later be "
                    "re-authorized; use a successor revision."
                ),
                reference_ids=tuple(
                    item.final_model_review_decision_id
                    for item in prior_nonapproval
                ),
            )
        )

    successor_revisions = _successor_revisions(
        revisions,
        final_model_review_revision_id,
    )
    if successor_revisions:
        blockers.append(
            FinalModelReviewReleaseBlocker(
                code="revision_superseded",
                message=(
                    "A successor Final Model Review revision exists. The "
                    "explicitly addressed older revision is superseded and is "
                    "not eligible for release."
                ),
                reference_ids=tuple(
                    item.revision.final_model_review_revision_id
                    for item in successor_revisions
                ),
            )
        )

    approvals = tuple(
        item
        for item in decisions
        if item.decision == "approved_for_publication"
    )
    if len(approvals) > 1:
        raise FinalModelReviewIntegrityError(
            "More than one publication approval exists for the exact Final "
            "Model Review revision."
        )

    approval_decision_id = (
        approvals[0].final_model_review_decision_id
        if approvals
        else None
    )

    if blockers:
        release_status = "blocked"
    elif approval_decision_id is not None:
        release_status = "approved_for_publication"
    else:
        release_status = "ready_for_approval"

    if release_status not in FINAL_MODEL_REVIEW_RELEASE_STATUSES:
        raise FinalModelReviewIntegrityError(
            "Final Model Review release status is internally inconsistent."
        )

    provisional = FinalModelReviewReleaseGateResult(
        project_id=project_id,
        final_model_review_id=final_model_review_id,
        final_model_review_revision_id=final_model_review_revision_id,
        revision_content_fingerprint=revision.content_fingerprint,
        review_subject_fingerprint=revision.review_subject_fingerprint,
        generated_artifact_set_fingerprint=(
            revision.generated_artifact_set_fingerprint
        ),
        validation_result_fingerprint=revision.validation_result_fingerprint,
        validation_status=revision.validation_status,
        publication_gate=revision.publication_gate,
        release_status=release_status,
        approval_decision_id=approval_decision_id,
        blockers=tuple(blockers),
        evaluation_fingerprint="0" * 64,
    )
    return replace(
        provisional,
        evaluation_fingerprint=(
            calculate_final_model_review_release_gate_fingerprint(
                provisional,
                items=items,
                change_proposals=change_proposals,
                decisions=decisions,
                successor_revisions=successor_revisions,
            )
        ),
    )


def require_final_model_review_ready_for_approval(
    repository,
    project_id: str,
    final_model_review_id: str,
    final_model_review_revision_id: str,
) -> FinalModelReviewReleaseGateResult:
    """Return the gate only when a new Human approval may be recorded."""

    gate = evaluate_final_model_review_release_gate(
        repository,
        project_id,
        final_model_review_id,
        final_model_review_revision_id,
    )
    if gate.release_status != "ready_for_approval":
        reason = (
            gate.blockers[0].message
            if gate.blockers
            else "The exact review revision already has release approval."
        )
        raise FinalModelReviewReleaseGateError(reason)
    return gate


def require_final_model_review_approved_for_publication(
    repository,
    project_id: str,
    final_model_review_id: str,
    final_model_review_revision_id: str,
) -> FinalModelReviewReleaseGateResult:
    """Return the current gate only when the exact FRV remains publishable."""

    gate = evaluate_final_model_review_release_gate(
        repository,
        project_id,
        final_model_review_id,
        final_model_review_revision_id,
    )
    if gate.release_status != "approved_for_publication":
        reason = (
            gate.blockers[0].message
            if gate.blockers
            else "The exact review revision has no Human publication approval."
        )
        raise FinalModelReviewReleaseGateError(reason)
    return gate


def calculate_final_model_review_release_gate_fingerprint(
    gate: FinalModelReviewReleaseGateResult,
    *,
    items,
    change_proposals,
    decisions,
    successor_revisions,
) -> str:
    """Fingerprint the exact approval-relevant state used by one evaluation."""

    payload = asdict(gate)
    payload.pop("evaluation_fingerprint")
    payload["review_item_fingerprints"] = [
        item.content_fingerprint
        for item in sorted(
            items,
            key=lambda item: item.final_model_review_item_id,
        )
    ]
    payload["change_proposal_fingerprints"] = [
        item.content_fingerprint
        for item in sorted(
            change_proposals,
            key=lambda item: item.final_model_review_change_proposal_id,
        )
    ]
    payload["review_decision_fingerprints"] = [
        item.decision_fingerprint
        for item in sorted(
            decisions,
            key=lambda item: item.final_model_review_decision_id,
        )
    ]
    payload["successor_revision_fingerprints"] = [
        item.revision.content_fingerprint
        for item in successor_revisions
    ]
    return calculate_json_fingerprint(payload)


def _successor_revisions(revisions, revision_id):
    """Return every persisted successor after the explicitly addressed FRV."""

    ids = tuple(
        item.revision.final_model_review_revision_id
        for item in revisions
    )
    try:
        index = ids.index(revision_id)
    except ValueError as exc:
        raise FinalModelReviewIntegrityError(
            "Explicit Final Model Review revision is absent from its review."
        ) from exc
    return tuple(revisions[index + 1 :])
