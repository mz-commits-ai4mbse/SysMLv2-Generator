"""Exact read models for P9 Agent proposals in Human Review."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
)
from .p9_proposal_adapter import (
    P9ElementProposal,
    P9RelationshipProposal,
    P9StructuredProposalSet,
)
from .types import (
    ReviewItem,
    ReviewItemContent,
    ReviewProposalReference,
    ReviewRelationshipRepresentation,
)
from .workflow_editing import proposal_selection_key


@dataclass(frozen=True, slots=True)
class ReviewProposalSourceAssignmentDetail:
    """One exact source assignment exposed to the reviewer."""

    source_info_id: str
    source_statement: str
    assignment_type: str
    confidence: str


@dataclass(frozen=True, slots=True)
class ReviewProposalDetail:
    """One exact Agent proposal reconstructed from immutable P9 evidence."""

    review_item_id: str
    stable_subject_key: str
    proposal_key: str
    proposal_kind: str
    agent_id: str
    persona_id: str
    proposal_id: str
    review_state: str
    proposed_title: str
    proposed_primary_text: str
    proposed_description: str
    proposed_information_type: str
    framework_assignment_values: tuple[str, ...]
    source_assignments: tuple[
        ReviewProposalSourceAssignmentDetail,
        ...,
    ]
    rationale: str
    confidence: str
    generation_readiness: str | None
    supporting_evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    artifact_id: str
    artifact_content_fingerprint: str
    proposal_content_fingerprint: str
    source_subject_key: str | None = None
    target_subject_key: str | None = None
    semantic_intent: str | None = None


def build_review_proposal_details(
    item: ReviewItem,
    structured_proposals: P9StructuredProposalSet,
) -> tuple[ReviewProposalDetail, ...]:
    """Reconstruct every immutable Agent proposal referenced by one item."""

    if not isinstance(item, ReviewItem):
        raise ReviewValidationError(
            "item must be a ReviewItem."
        )

    if not isinstance(
        structured_proposals,
        P9StructuredProposalSet,
    ):
        raise ReviewValidationError(
            "structured_proposals must be a P9StructuredProposalSet."
        )

    if item.project_id != structured_proposals.project_id:
        raise ReviewIntegrityError(
            "Review Item and P9 proposals belong to different Projects."
        )

    candidates = (
        *structured_proposals.element_proposals,
        *structured_proposals.relationship_proposals,
    )

    by_key = {}
    for proposal in candidates:
        key = proposal_selection_key(
            proposal.proposal_reference
        )
        if key in by_key:
            raise ReviewIntegrityError(
                "P9 proposal keys must be unique."
            )
        by_key[key] = proposal

    element_titles = {
        proposal.stable_subject_key: proposal.candidate_name
        for proposal in structured_proposals.element_proposals
    }

    details = []

    for reference in item.proposal_references:
        key = proposal_selection_key(reference)
        proposal = by_key.get(key)

        if proposal is None:
            raise ReviewReferenceError(
                "A Review Item proposal reference cannot be reconstructed "
                "from the exact P9 evidence set."
            )

        if (
            proposal.stable_subject_key != item.stable_subject_key
            and item.lineage_operation not in {"split", "merge"}
        ):
            raise ReviewIntegrityError(
                "The P9 proposal stable subject does not match the Review Item."
            )

        _validate_reference_identity(
            reference,
            proposal.proposal_reference,
        )

        if isinstance(proposal, P9ElementProposal):
            details.append(
                ReviewProposalDetail(
                    review_item_id=item.review_item_id,
                    stable_subject_key=item.stable_subject_key,
                    proposal_key=key,
                    proposal_kind="element",
                    agent_id=reference.agent_id,
                    persona_id=reference.persona_id,
                    proposal_id=reference.proposal_id,
                    review_state=reference.review_state,
                    proposed_title=proposal.candidate_name,
                    proposed_primary_text=proposal.description,
                    proposed_description=proposal.rationale_summary,
                    proposed_information_type=proposal.element_type,
                    framework_assignment_values=(),
                    source_assignments=tuple(
                        ReviewProposalSourceAssignmentDetail(
                            source_info_id=assignment.source_info_id,
                            source_statement=assignment.source_statement,
                            assignment_type=assignment.assignment_type,
                            confidence=assignment.confidence,
                        )
                        for assignment in proposal.source_assignments
                    ),
                    rationale=proposal.rationale_summary,
                    confidence=proposal.confidence,
                    generation_readiness=(
                        proposal.generation_readiness
                    ),
                    supporting_evidence=proposal.source_basis,
                    missing_evidence=proposal.missing_information,
                    artifact_id=(
                        reference.artifact_reference.artifact_id
                    ),
                    artifact_content_fingerprint=(
                        reference.artifact_reference
                        .content_fingerprint
                    ),
                    proposal_content_fingerprint=(
                        reference.proposal_content_fingerprint
                    ),
                )
            )
            continue

        if not isinstance(proposal, P9RelationshipProposal):
            raise ReviewIntegrityError(
                "Unsupported P9 proposal type."
            )

        try:
            source_title = element_titles[
                proposal.source_subject_key
            ]
            target_title = element_titles[
                proposal.target_subject_key
            ]
        except KeyError as exc:
            raise ReviewReferenceError(
                "Relationship proposal endpoints cannot be resolved "
                "to exact P9 element proposals."
            ) from exc

        details.append(
            ReviewProposalDetail(
                review_item_id=item.review_item_id,
                stable_subject_key=item.stable_subject_key,
                proposal_key=key,
                proposal_kind="relationship",
                agent_id=reference.agent_id,
                persona_id=reference.persona_id,
                proposal_id=reference.proposal_id,
                review_state=reference.review_state,
                proposed_title=(
                    f"{source_title} {proposal.link_type} "
                    f"{target_title}"
                ),
                proposed_primary_text=proposal.source_statement,
                proposed_description=proposal.rationale_summary,
                proposed_information_type="relationship",
                framework_assignment_values=(),
                source_assignments=(),
                rationale=proposal.rationale_summary,
                confidence=proposal.confidence,
                generation_readiness=None,
                supporting_evidence=proposal.source_basis,
                missing_evidence=(),
                artifact_id=(
                    reference.artifact_reference.artifact_id
                ),
                artifact_content_fingerprint=(
                    reference.artifact_reference
                    .content_fingerprint
                ),
                proposal_content_fingerprint=(
                    reference.proposal_content_fingerprint
                ),
                source_subject_key=proposal.source_subject_key,
                target_subject_key=proposal.target_subject_key,
                semantic_intent=proposal.link_type,
            )
        )

    return tuple(details)


def proposal_detail_to_content(
    detail: ReviewProposalDetail,
    *,
    relationship_representation: (
        ReviewRelationshipRepresentation | None
    ) = None,
    human_rationale: str | None = None,
) -> ReviewItemContent:
    """Materialize exact proposal content for a Review Item decision."""

    if not isinstance(detail, ReviewProposalDetail):
        raise ReviewValidationError(
            "detail must be a ReviewProposalDetail."
        )

    if detail.proposal_kind == "element":
        if relationship_representation is not None:
            raise ReviewIntegrityError(
                "Element proposals must not contain a relationship "
                "representation."
            )

        return ReviewItemContent(
            title=detail.proposed_title,
            primary_text=detail.proposed_primary_text,
            description=detail.proposed_description,
            information_type=detail.proposed_information_type,
            modality=None,
            epistemic_status=None,
            human_rationale=human_rationale,
            human_confidence=None,
            relationship_representation=None,
        )

    if detail.proposal_kind != "relationship":
        raise ReviewIntegrityError(
            "Unsupported proposal kind."
        )

    if relationship_representation is None:
        raise ReviewIntegrityError(
            "A relationship proposal requires an exact relationship "
            "representation."
        )

    if (
        relationship_representation.source_subject_key
        != detail.source_subject_key
        or relationship_representation.target_subject_key
        != detail.target_subject_key
        or relationship_representation.semantic_intent
        != detail.semantic_intent
    ):
        raise ReviewIntegrityError(
            "The relationship representation does not match the "
            "selected Agent proposal."
        )

    return ReviewItemContent(
        title=detail.proposed_title,
        primary_text=detail.proposed_primary_text,
        description=detail.proposed_description,
        information_type="relationship",
        modality=None,
        epistemic_status=None,
        human_rationale=human_rationale,
        human_confidence=None,
        relationship_representation=relationship_representation,
    )


def _validate_reference_identity(
    current: ReviewProposalReference,
    source: ReviewProposalReference,
) -> None:
    if (
        current.artifact_reference != source.artifact_reference
        or current.agent_id != source.agent_id
        or current.persona_id != source.persona_id
        or current.proposal_id != source.proposal_id
        or (
            current.proposal_content_fingerprint
            != source.proposal_content_fingerprint
        )
        or (
            current.original_report_locator
            != source.original_report_locator
        )
    ):
        raise ReviewIntegrityError(
            "Review Proposal Reference identity differs from the "
            "reconstructed P9 proposal."
        )
