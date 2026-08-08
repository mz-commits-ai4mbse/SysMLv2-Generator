"""G6 proposal actions and split/merge lineage transformations."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
    StaleReviewRevisionError,
)
from .item_manifest import create_review_item
from .proposal_detail import (
    ReviewProposalDetail,
    proposal_detail_to_content,
)
from .revision_manifest import create_review_revision
from .types import (
    ReviewDimensionSelection,
    ReviewEvidenceReference,
    ReviewItem,
    ReviewItemContent,
    ReviewProposalReference,
    ReviewRevision,
)
from .workflow_editing import proposal_selection_key


@dataclass(frozen=True, slots=True)
class ReviewProposalActionRequest:
    """One exact quick action against an Agent proposal."""

    expected_revision_id: str
    expected_item_content_fingerprint: str
    proposal_key: str
    rationale: str | None = None


@dataclass(frozen=True, slots=True)
class ReviewSplitChildSpec:
    """One explicit child produced by a Review Item split."""

    stable_subject_key: str
    current_content: ReviewItemContent
    proposal_keys: tuple[str, ...]
    source_evidence_keys: tuple[str, ...]
    consensus_evidence_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReviewSplitRequest:
    """One exact split against an immutable parent Review Item."""

    expected_revision_id: str
    expected_item_content_fingerprint: str
    children: tuple[ReviewSplitChildSpec, ...]
    rationale: str | None = None


@dataclass(frozen=True, slots=True)
class ReviewMergeRequest:
    """One exact merge of multiple Review Items."""

    expected_revision_id: str
    expected_item_fingerprints: tuple[
        tuple[str, str],
        ...,
    ]
    stable_subject_key: str
    current_content: ReviewItemContent
    rationale: str | None = None


def evidence_selection_key(
    reference: ReviewEvidenceReference,
) -> str:
    """Return a stable UI key for one exact evidence reference."""

    if not isinstance(reference, ReviewEvidenceReference):
        raise ReviewValidationError(
            "reference must be a ReviewEvidenceReference."
        )

    return (
        f"{reference.artifact_reference.artifact_id}:"
        f"{reference.evidence_role}:"
        f"{reference.evidence_locator}:"
        f"{reference.evidence_content_fingerprint}"
    )


def create_proposal_accept_revision(
    current_revision: ReviewRevision,
    *,
    review_item_id: str,
    detail: ReviewProposalDetail,
    request: ReviewProposalActionRequest,
    new_review_revision_id: str,
    actor_identity: str,
    timestamp: str,
) -> ReviewRevision:
    """Accept one exact Agent proposal without mutating Agent evidence."""

    item = _target_item(
        current_revision,
        review_item_id=review_item_id,
        expected_revision_id=request.expected_revision_id,
        expected_item_content_fingerprint=(
            request.expected_item_content_fingerprint
        ),
    )

    if detail.review_item_id != item.review_item_id:
        raise ReviewIntegrityError(
            "Proposal detail does not belong to the selected Review Item."
        )

    if detail.proposal_key != request.proposal_key:
        raise ReviewIntegrityError(
            "Proposal detail does not match the requested proposal."
        )

    if request.proposal_key not in {
        proposal_selection_key(reference)
        for reference in item.proposal_references
    }:
        raise ReviewReferenceError(
            "The requested Agent proposal is unavailable in the current "
            "Review Item."
        )

    actor = _text(actor_identity, "actor_identity")
    _text(timestamp, "timestamp")

    relationship = (
        item.current_content.relationship_representation
    )

    if detail.proposal_kind == "relationship":
        if (
            relationship is None
            or relationship.validation_status != "valid"
        ):
            raise ReviewIntegrityError(
                "A relationship proposal cannot be accepted until its "
                "SysML v2 relationship representation is valid."
            )

        if request.rationale is None:
            raise ReviewIntegrityError(
                "Accepting a relationship proposal with a human-selected "
                "SysML v2 construct requires a rationale."
            )

        content = proposal_detail_to_content(
            detail,
            relationship_representation=relationship,
            human_rationale=request.rationale,
        )
        outcome = "accepted_with_modification"
    else:
        content = proposal_detail_to_content(detail)
        outcome = "accepted_as_generated"

    proposal_references = tuple(
        replace(
            reference,
            review_state=(
                "selected"
                if proposal_selection_key(reference)
                == request.proposal_key
                else "not_selected_due_to_human_selection"
            ),
        )
        for reference in item.proposal_references
    )

    selections = _proposal_accept_selections(
        item,
        detail=detail,
        content=content,
        outcome=outcome,
        actor_identity=actor,
        timestamp=timestamp,
        rationale=request.rationale,
    )

    updated = _rebuild_item(
        item,
        proposal_references=proposal_references,
        current_content=content,
        dimension_selections=selections,
        effective_review_outcome=outcome,
    )

    return _successor_revision(
        current_revision,
        review_items=_replace_one_item(
            current_revision.review_items,
            updated,
        ),
        new_review_revision_id=new_review_revision_id,
        actor_identity=actor,
        timestamp=timestamp,
    )


def create_proposal_reject_revision(
    current_revision: ReviewRevision,
    *,
    review_item_id: str,
    request: ReviewProposalActionRequest,
    new_review_revision_id: str,
    actor_identity: str,
    timestamp: str,
) -> ReviewRevision:
    """Reject one proposal while preserving Review Item independence."""

    if request.rationale is None:
        raise ReviewIntegrityError(
            "Rejecting an Agent proposal requires a rationale."
        )

    item = _target_item(
        current_revision,
        review_item_id=review_item_id,
        expected_revision_id=request.expected_revision_id,
        expected_item_content_fingerprint=(
            request.expected_item_content_fingerprint
        ),
    )
    actor = _text(actor_identity, "actor_identity")
    _text(request.rationale, "rationale")
    _text(timestamp, "timestamp")

    references = {
        proposal_selection_key(reference): reference
        for reference in item.proposal_references
    }

    target = references.get(request.proposal_key)
    if target is None:
        raise ReviewReferenceError(
            "The requested Agent proposal is unavailable in the current "
            "Review Item."
        )

    target_was_selected = target.review_state == "selected"

    proposal_references = []
    for reference in item.proposal_references:
        key = proposal_selection_key(reference)

        if key == request.proposal_key:
            proposal_references.append(
                replace(reference, review_state="rejected")
            )
        elif target_was_selected:
            proposal_references.append(
                replace(reference, review_state="available")
            )
        else:
            proposal_references.append(reference)

    outcome = (
        "open"
        if target_was_selected
        else item.effective_review_outcome
    )

    selections = {
        selection.dimension: selection
        for selection in item.dimension_selections
    }
    selections["review_outcome"] = ReviewDimensionSelection(
        dimension="review_outcome",
        selected_values=(outcome,),
        value_origin="item_override",
        source_reference_ids=(request.proposal_key,),
        rationale=request.rationale,
        selected_by=actor,
        selected_at=timestamp,
    )

    updated = _rebuild_item(
        item,
        proposal_references=tuple(proposal_references),
        current_content=item.current_content,
        dimension_selections=tuple(
            selections[key]
            for key in sorted(selections)
        ),
        effective_review_outcome=outcome,
    )

    return _successor_revision(
        current_revision,
        review_items=_replace_one_item(
            current_revision.review_items,
            updated,
        ),
        new_review_revision_id=new_review_revision_id,
        actor_identity=actor,
        timestamp=timestamp,
    )


def create_split_revision(
    current_revision: ReviewRevision,
    *,
    review_item_id: str,
    request: ReviewSplitRequest,
    new_review_item_ids: tuple[str, ...],
    new_review_revision_id: str,
    actor_identity: str,
    timestamp: str,
) -> ReviewRevision:
    """Replace one parent with explicit split children."""

    item = _target_item(
        current_revision,
        review_item_id=review_item_id,
        expected_revision_id=request.expected_revision_id,
        expected_item_content_fingerprint=(
            request.expected_item_content_fingerprint
        ),
    )
    actor = _text(actor_identity, "actor_identity")
    _text(timestamp, "timestamp")

    if len(request.children) < 2:
        raise ReviewIntegrityError(
            "Splitting a Review Item requires at least two children."
        )

    if len(new_review_item_ids) != len(request.children):
        raise ReviewIntegrityError(
            "Split child IDs must match the number of requested children."
        )

    if len(set(new_review_item_ids)) != len(new_review_item_ids):
        raise ReviewIntegrityError(
            "Split child Review Item IDs must be unique."
        )

    child_keys = tuple(
        child.stable_subject_key
        for child in request.children
    )
    if len(set(child_keys)) != len(child_keys):
        raise ReviewIntegrityError(
            "Split child stable subject keys must be unique."
        )

    surviving_subjects = {
        candidate.stable_subject_key
        for candidate in current_revision.review_items
        if candidate.review_item_id != review_item_id
    }
    if surviving_subjects.intersection(child_keys):
        raise ReviewIntegrityError(
            "Split child subjects collide with existing Review Items."
        )

    proposal_map = {
        proposal_selection_key(reference): reference
        for reference in item.proposal_references
    }
    source_map = {
        evidence_selection_key(reference): reference
        for reference in item.source_evidence_references
    }
    consensus_map = {
        evidence_selection_key(reference): reference
        for reference in item.consensus_evidence_references
    }

    _validate_exact_partition(
        tuple(
            key
            for child in request.children
            for key in child.proposal_keys
        ),
        tuple(proposal_map),
        "proposal",
    )
    _validate_exact_partition(
        tuple(
            key
            for child in request.children
            for key in child.source_evidence_keys
        ),
        tuple(source_map),
        "source evidence",
    )
    _validate_exact_partition(
        tuple(
            key
            for child in request.children
            for key in child.consensus_evidence_keys
        ),
        tuple(consensus_map),
        "consensus evidence",
    )

    children = []

    for index, (child, child_id) in enumerate(
        zip(request.children, new_review_item_ids),
        start=1,
    ):
        if (
            not child.proposal_keys
            and not child.source_evidence_keys
            and not child.consensus_evidence_keys
        ):
            raise ReviewIntegrityError(
                "Every split child requires preserved proposal or "
                "evidence support."
            )

        child_proposals = tuple(
            replace(
                proposal_map[key],
                review_state="available",
            )
            for key in child.proposal_keys
        )
        child_source = tuple(
            source_map[key]
            for key in child.source_evidence_keys
        )
        child_consensus = tuple(
            consensus_map[key]
            for key in child.consensus_evidence_keys
        )

        children.append(
            create_review_item(
                project_id=item.project_id,
                review_document_id=item.review_document_id,
                review_document_version_id=(
                    item.review_document_version_id
                ),
                review_item_id=child_id,
                review_item_kind=item.review_item_kind,
                stable_subject_key=child.stable_subject_key,
                section=item.section,
                lineage_operation="split",
                derived_from_review_item_ids=(
                    item.review_item_id,
                ),
                original_report_locator=(
                    f"{item.original_report_locator}/split/{index}"
                ),
                proposal_references=child_proposals,
                source_evidence_references=child_source,
                consensus_evidence_references=child_consensus,
                current_content=child.current_content,
                dimension_selections=_human_open_selections(
                    child.current_content,
                    source_reference_ids=(
                        item.review_item_id,
                    ),
                    actor_identity=actor,
                    timestamp=timestamp,
                    rationale=request.rationale,
                    source_assignment_values=tuple(
                        child.source_evidence_keys
                    ),
                ),
                effective_review_outcome="open",
            )
        )

    review_items = []
    for candidate in current_revision.review_items:
        if candidate.review_item_id == item.review_item_id:
            review_items.extend(children)
        else:
            review_items.append(candidate)

    return _successor_revision(
        current_revision,
        review_items=tuple(review_items),
        new_review_revision_id=new_review_revision_id,
        actor_identity=actor,
        timestamp=timestamp,
    )


def create_merge_revision(
    current_revision: ReviewRevision,
    *,
    request: ReviewMergeRequest,
    new_review_item_id: str,
    new_review_revision_id: str,
    actor_identity: str,
    timestamp: str,
) -> ReviewRevision:
    """Replace multiple parents with one explicit merged Review Item."""

    if current_revision.review_revision_id != request.expected_revision_id:
        raise StaleReviewRevisionError(
            "The merge does not target the current Review Revision."
        )

    actor = _text(actor_identity, "actor_identity")
    _text(timestamp, "timestamp")

    expected = dict(request.expected_item_fingerprints)

    if (
        len(expected) < 2
        or len(expected) != len(
            request.expected_item_fingerprints
        )
    ):
        raise ReviewIntegrityError(
            "Merging requires at least two unique Review Item identities."
        )

    parents = tuple(
        item
        for item in current_revision.review_items
        if item.review_item_id in expected
    )

    if len(parents) != len(expected):
        raise ReviewReferenceError(
            "One or more merge parents are unavailable in the current "
            "Review Revision."
        )

    for parent in parents:
        if (
            parent.item_content_fingerprint
            != expected[parent.review_item_id]
        ):
            raise StaleReviewRevisionError(
                "A merge parent fingerprint changed after selection."
            )

    kinds = {parent.review_item_kind for parent in parents}
    sections = {parent.section for parent in parents}

    if len(kinds) != 1 or len(sections) != 1:
        raise ReviewIntegrityError(
            "Only Review Items of the same kind and section may be merged."
        )

    surviving_subjects = {
        item.stable_subject_key
        for item in current_revision.review_items
        if item.review_item_id not in expected
    }
    if request.stable_subject_key in surviving_subjects:
        raise ReviewIntegrityError(
            "Merged stable subject collides with an existing Review Item."
        )

    proposals = _deduplicated_proposals(parents)
    source_evidence = _deduplicated_evidence(
        tuple(
            reference
            for parent in parents
            for reference in parent.source_evidence_references
        )
    )
    consensus_evidence = _deduplicated_evidence(
        tuple(
            reference
            for parent in parents
            for reference in parent.consensus_evidence_references
        )
    )

    parent_ids = tuple(
        sorted(expected)
    )

    merged = create_review_item(
        project_id=current_revision.project_id,
        review_document_id=current_revision.review_document_id,
        review_document_version_id=(
            current_revision.review_document_version_id
        ),
        review_item_id=new_review_item_id,
        review_item_kind=parents[0].review_item_kind,
        stable_subject_key=request.stable_subject_key,
        section=parents[0].section,
        lineage_operation="merge",
        derived_from_review_item_ids=parent_ids,
        original_report_locator=(
            "merge:" + ",".join(parent_ids)
        ),
        proposal_references=proposals,
        source_evidence_references=source_evidence,
        consensus_evidence_references=consensus_evidence,
        current_content=request.current_content,
        dimension_selections=_human_open_selections(
            request.current_content,
            source_reference_ids=parent_ids,
            actor_identity=actor,
            timestamp=timestamp,
            rationale=request.rationale,
            source_assignment_values=tuple(
                evidence_selection_key(reference)
                for reference in source_evidence
            ),
        ),
        effective_review_outcome="open",
    )

    first_index = min(
        index
        for index, item in enumerate(
            current_revision.review_items
        )
        if item.review_item_id in expected
    )

    survivors = [
        item
        for item in current_revision.review_items
        if item.review_item_id not in expected
    ]
    survivors.insert(first_index, merged)

    return _successor_revision(
        current_revision,
        review_items=tuple(survivors),
        new_review_revision_id=new_review_revision_id,
        actor_identity=actor,
        timestamp=timestamp,
    )


def _target_item(
    revision: ReviewRevision,
    *,
    review_item_id: str,
    expected_revision_id: str,
    expected_item_content_fingerprint: str,
) -> ReviewItem:
    if revision.review_revision_id != expected_revision_id:
        raise StaleReviewRevisionError(
            "The command does not target the current Review Revision."
        )

    matches = tuple(
        item
        for item in revision.review_items
        if item.review_item_id == review_item_id
    )

    if len(matches) != 1:
        raise ReviewReferenceError(
            "The requested Review Item is unavailable in the current "
            "Review Revision."
        )

    item = matches[0]

    if (
        item.item_content_fingerprint
        != expected_item_content_fingerprint
    ):
        raise StaleReviewRevisionError(
            "The Review Item fingerprint changed after selection."
        )

    return item


def _proposal_accept_selections(
    item: ReviewItem,
    *,
    detail: ReviewProposalDetail,
    content: ReviewItemContent,
    outcome: str,
    actor_identity: str,
    timestamp: str,
    rationale: str | None,
) -> tuple[ReviewDimensionSelection, ...]:
    preserved = {
        selection.dimension: selection
        for selection in item.dimension_selections
        if selection.dimension
        not in {
            "content",
            "classification",
            "source_assignment",
            "relationship_representation",
            "review_outcome",
        }
    }

    preserved["content"] = ReviewDimensionSelection(
        dimension="content",
        selected_values=(content.primary_text,),
        value_origin="agent_proposal",
        source_reference_ids=(detail.proposal_key,),
        rationale=detail.rationale,
        selected_by=None,
        selected_at=None,
    )
    preserved["classification"] = ReviewDimensionSelection(
        dimension="classification",
        selected_values=(detail.proposed_information_type,),
        value_origin="agent_proposal",
        source_reference_ids=(detail.proposal_key,),
        rationale=detail.rationale,
        selected_by=None,
        selected_at=None,
    )

    source_values = tuple(
        assignment.source_info_id
        for assignment in detail.source_assignments
    )
    if source_values:
        preserved["source_assignment"] = ReviewDimensionSelection(
            dimension="source_assignment",
            selected_values=source_values,
            value_origin="agent_proposal",
            source_reference_ids=(detail.proposal_key,),
            rationale=detail.rationale,
            selected_by=None,
            selected_at=None,
        )

    if detail.proposal_kind == "relationship":
        relationship = content.relationship_representation
        assert relationship is not None
        preserved[
            "relationship_representation"
        ] = ReviewDimensionSelection(
            dimension="relationship_representation",
            selected_values=(
                relationship.semantic_intent,
                relationship.sysml_v2_construct,
                relationship.validation_status,
            ),
            value_origin="item_override",
            source_reference_ids=(detail.proposal_key,),
            rationale=rationale,
            selected_by=actor_identity,
            selected_at=timestamp,
        )

    preserved["review_outcome"] = ReviewDimensionSelection(
        dimension="review_outcome",
        selected_values=(outcome,),
        value_origin="item_override",
        source_reference_ids=(detail.proposal_key,),
        rationale=rationale,
        selected_by=actor_identity,
        selected_at=timestamp,
    )

    return tuple(
        preserved[key]
        for key in sorted(preserved)
    )


def _human_open_selections(
    content: ReviewItemContent,
    *,
    source_reference_ids: tuple[str, ...],
    actor_identity: str,
    timestamp: str,
    rationale: str | None,
    source_assignment_values: tuple[str, ...],
) -> tuple[ReviewDimensionSelection, ...]:
    selections = {
        "content": ReviewDimensionSelection(
            dimension="content",
            selected_values=(content.primary_text,),
            value_origin="item_override",
            source_reference_ids=source_reference_ids,
            rationale=rationale,
            selected_by=actor_identity,
            selected_at=timestamp,
        ),
        "review_outcome": ReviewDimensionSelection(
            dimension="review_outcome",
            selected_values=("open",),
            value_origin="item_override",
            source_reference_ids=source_reference_ids,
            rationale=rationale,
            selected_by=actor_identity,
            selected_at=timestamp,
        ),
    }

    classification = tuple(
        value
        for value in (
            content.information_type,
            content.modality,
            content.epistemic_status,
        )
        if value is not None
    )
    if classification:
        selections["classification"] = (
            ReviewDimensionSelection(
                dimension="classification",
                selected_values=classification,
                value_origin="item_override",
                source_reference_ids=source_reference_ids,
                rationale=rationale,
                selected_by=actor_identity,
                selected_at=timestamp,
            )
        )

    relationship = content.relationship_representation
    if relationship is not None:
        selections[
            "relationship_representation"
        ] = ReviewDimensionSelection(
            dimension="relationship_representation",
            selected_values=(
                relationship.semantic_intent,
                (
                    relationship.sysml_v2_construct
                    if relationship.sysml_v2_construct is not None
                    else "unresolved"
                ),
                relationship.validation_status,
            ),
            value_origin="item_override",
            source_reference_ids=source_reference_ids,
            rationale=rationale,
            selected_by=actor_identity,
            selected_at=timestamp,
        )

    if source_assignment_values:
        selections["source_assignment"] = (
            ReviewDimensionSelection(
                dimension="source_assignment",
                selected_values=source_assignment_values,
                value_origin="item_override",
                source_reference_ids=source_reference_ids,
                rationale=rationale,
                selected_by=actor_identity,
                selected_at=timestamp,
            )
        )

    return tuple(
        selections[key]
        for key in sorted(selections)
    )


def _rebuild_item(
    item: ReviewItem,
    *,
    proposal_references: tuple[
        ReviewProposalReference,
        ...,
    ],
    current_content: ReviewItemContent,
    dimension_selections: tuple[
        ReviewDimensionSelection,
        ...,
    ],
    effective_review_outcome: str,
) -> ReviewItem:
    return create_review_item(
        project_id=item.project_id,
        review_document_id=item.review_document_id,
        review_document_version_id=(
            item.review_document_version_id
        ),
        review_item_id=item.review_item_id,
        review_item_kind=item.review_item_kind,
        stable_subject_key=item.stable_subject_key,
        section=item.section,
        lineage_operation=item.lineage_operation,
        derived_from_review_item_ids=(
            item.derived_from_review_item_ids
        ),
        original_report_locator=item.original_report_locator,
        proposal_references=proposal_references,
        source_evidence_references=(
            item.source_evidence_references
        ),
        consensus_evidence_references=(
            item.consensus_evidence_references
        ),
        current_content=current_content,
        dimension_selections=dimension_selections,
        effective_review_outcome=effective_review_outcome,
    )


def _successor_revision(
    current: ReviewRevision,
    *,
    review_items: tuple[ReviewItem, ...],
    new_review_revision_id: str,
    actor_identity: str,
    timestamp: str,
) -> ReviewRevision:
    return create_review_revision(
        project_id=current.project_id,
        review_document_id=current.review_document_id,
        review_document_version_id=(
            current.review_document_version_id
        ),
        review_revision_id=new_review_revision_id,
        revision_sequence=current.revision_sequence + 1,
        predecessor_revision_id=current.review_revision_id,
        review_items=review_items,
        scoped_review_action_ids=(
            current.scoped_review_action_ids
        ),
        created_by=actor_identity,
        timestamp=timestamp,
    )


def _replace_one_item(
    items: tuple[ReviewItem, ...],
    updated: ReviewItem,
) -> tuple[ReviewItem, ...]:
    return tuple(
        updated
        if item.review_item_id == updated.review_item_id
        else item
        for item in items
    )


def _validate_exact_partition(
    supplied: tuple[str, ...],
    expected: tuple[str, ...],
    label: str,
) -> None:
    if (
        len(supplied) != len(set(supplied))
        or set(supplied) != set(expected)
    ):
        raise ReviewIntegrityError(
            f"Split {label} references must form one exact partition "
            "of the parent references."
        )


def _deduplicated_proposals(
    parents: tuple[ReviewItem, ...],
) -> tuple[ReviewProposalReference, ...]:
    result = {}
    for parent in parents:
        for reference in parent.proposal_references:
            key = (
                reference.artifact_reference.artifact_id,
                reference.proposal_id,
                reference.proposal_content_fingerprint,
            )
            result.setdefault(
                key,
                replace(reference, review_state="available"),
            )

    return tuple(
        result[key]
        for key in sorted(result)
    )


def _deduplicated_evidence(
    references: tuple[ReviewEvidenceReference, ...],
) -> tuple[ReviewEvidenceReference, ...]:
    result = {}
    for reference in references:
        key = evidence_selection_key(reference)
        result.setdefault(key, reference)

    return tuple(
        result[key]
        for key in sorted(result)
    )


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ReviewValidationError(
            f"{label} must be a string."
        )
    selected = value.strip()
    if (
        not selected
        or selected != value
        or "\n" in selected
        or "\r" in selected
    ):
        raise ReviewValidationError(
            f"{label} must be non-empty single-line text without "
            "surrounding whitespace."
        )
    return selected
