"""Pure G6 item-level editing over immutable Review Revisions."""

from __future__ import annotations

from dataclasses import dataclass, replace
import re

from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
    StaleReviewRevisionError,
)
from .item_manifest import create_review_item
from .revision_manifest import create_review_revision
from .types import (
    REVIEW_ITEM_OUTCOMES,
    ReviewDimensionSelection,
    ReviewItem,
    ReviewItemContent,
    ReviewProposalReference,
    ReviewRevision,
)


_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

_ACCEPTED_OUTCOMES = frozenset(
    {
        "accepted_as_generated",
        "accepted_with_modification",
        "combined",
    }
)

_NON_ACCEPTED_OUTCOMES = frozenset(
    {
        "open",
        "rejected",
        "deferred",
        "out_of_scope",
        "unresolved",
    }
)


@dataclass(frozen=True, slots=True)
class ReviewItemEditRequest:
    """One explicit edit against an exact immutable Review Revision."""

    expected_revision_id: str
    expected_item_content_fingerprint: str
    updated_content: ReviewItemContent
    selected_proposal_keys: tuple[str, ...]
    review_outcome: str
    framework_assignment_values: tuple[str, ...] | None = None
    terminology_assignment_values: tuple[str, ...] | None = None
    source_assignment_values: tuple[str, ...] | None = None
    rationale: str | None = None


def proposal_selection_key(
    reference: ReviewProposalReference,
) -> str:
    """Return the stable UI key for one exact Agent proposal."""

    if not isinstance(reference, ReviewProposalReference):
        raise ReviewValidationError(
            "reference must be a ReviewProposalReference."
        )

    return (
        f"{reference.artifact_reference.artifact_id}:"
        f"{reference.proposal_id}"
    )


def create_item_edit_revision(
    current_revision: ReviewRevision,
    *,
    review_item_id: str,
    request: ReviewItemEditRequest,
    new_review_revision_id: str,
    actor_identity: str,
    timestamp: str,
) -> ReviewRevision:
    """Create the next immutable Revision for one item-level edit."""

    if not isinstance(current_revision, ReviewRevision):
        raise ReviewValidationError(
            "current_revision must be a ReviewRevision."
        )

    _validate_request(request)
    actor = _single_line_text(
        actor_identity,
        "actor_identity",
    )
    _utc_timestamp(timestamp)

    if (
        current_revision.review_revision_id
        != request.expected_revision_id
    ):
        raise StaleReviewRevisionError(
            "The item edit does not target the current Review Revision."
        )

    matches = tuple(
        item
        for item in current_revision.review_items
        if item.review_item_id == review_item_id
    )

    if not matches:
        raise ReviewReferenceError(
            "The requested Review Item is unavailable in the current Revision."
        )

    if len(matches) != 1:
        raise ReviewIntegrityError(
            "Review Item identities must be unique in one Revision."
        )

    current_item = matches[0]

    if (
        current_item.item_content_fingerprint
        != request.expected_item_content_fingerprint
    ):
        raise StaleReviewRevisionError(
            "The Review Item fingerprint changed after the edit was opened."
        )

    selected_keys = _selected_proposal_keys(
        current_item,
        request.selected_proposal_keys,
    )

    _validate_outcome_contract(
        current_item,
        request,
        selected_keys,
    )

    updated_item = create_review_item(
        project_id=current_item.project_id,
        review_document_id=current_item.review_document_id,
        review_document_version_id=(
            current_item.review_document_version_id
        ),
        review_item_id=current_item.review_item_id,
        review_item_kind=current_item.review_item_kind,
        stable_subject_key=current_item.stable_subject_key,
        section=current_item.section,
        lineage_operation=current_item.lineage_operation,
        derived_from_review_item_ids=(
            current_item.derived_from_review_item_ids
        ),
        original_report_locator=(
            current_item.original_report_locator
        ),
        proposal_references=_proposal_states(
            current_item.proposal_references,
            review_outcome=request.review_outcome,
            selected_keys=selected_keys,
        ),
        source_evidence_references=(
            current_item.source_evidence_references
        ),
        consensus_evidence_references=(
            current_item.consensus_evidence_references
        ),
        current_content=request.updated_content,
        dimension_selections=_dimension_selections(
            current_item,
            request=request,
            selected_keys=selected_keys,
            actor_identity=actor,
            timestamp=timestamp,
        ),
        effective_review_outcome=request.review_outcome,
    )

    return create_review_revision(
        project_id=current_revision.project_id,
        review_document_id=current_revision.review_document_id,
        review_document_version_id=(
            current_revision.review_document_version_id
        ),
        review_revision_id=new_review_revision_id,
        revision_sequence=current_revision.revision_sequence + 1,
        predecessor_revision_id=current_revision.review_revision_id,
        review_items=tuple(
            updated_item
            if item.review_item_id == review_item_id
            else item
            for item in current_revision.review_items
        ),
        scoped_review_action_ids=(
            current_revision.scoped_review_action_ids
        ),
        created_by=actor,
        timestamp=timestamp,
    )


def _validate_request(
    request: ReviewItemEditRequest,
) -> None:
    if not isinstance(request, ReviewItemEditRequest):
        raise ReviewValidationError(
            "request must be a ReviewItemEditRequest."
        )

    _single_line_text(
        request.expected_revision_id,
        "expected_revision_id",
    )

    if (
        not isinstance(
            request.expected_item_content_fingerprint,
            str,
        )
        or _SHA256_PATTERN.fullmatch(
            request.expected_item_content_fingerprint
        )
        is None
    ):
        raise ReviewValidationError(
            "expected_item_content_fingerprint must be a lowercase SHA-256."
        )

    if not isinstance(
        request.updated_content,
        ReviewItemContent,
    ):
        raise ReviewValidationError(
            "updated_content must be ReviewItemContent."
        )

    if request.review_outcome not in REVIEW_ITEM_OUTCOMES:
        raise ReviewValidationError(
            "review_outcome is not supported."
        )

    _text_tuple(
        request.selected_proposal_keys,
        "selected_proposal_keys",
    )

    for label, values in (
        (
            "framework_assignment_values",
            request.framework_assignment_values,
        ),
        (
            "terminology_assignment_values",
            request.terminology_assignment_values,
        ),
        (
            "source_assignment_values",
            request.source_assignment_values,
        ),
    ):
        if values is not None:
            _text_tuple(values, label)

    if request.rationale is not None:
        _single_line_text(
            request.rationale,
            "rationale",
        )


def _selected_proposal_keys(
    item: ReviewItem,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    available = {
        proposal_selection_key(reference)
        for reference in item.proposal_references
    }

    unknown = set(values) - available

    if unknown:
        raise ReviewReferenceError(
            "The item edit selects unavailable Agent proposals."
        )

    return values


def _validate_outcome_contract(
    item: ReviewItem,
    request: ReviewItemEditRequest,
    selected_keys: tuple[str, ...],
) -> None:
    proposal_count = len(item.proposal_references)
    selected_count = len(selected_keys)
    outcome = request.review_outcome

    if outcome == "accepted_as_generated":
        if proposal_count == 0 or selected_count != 1:
            raise ReviewIntegrityError(
                "accepted_as_generated requires exactly one selected "
                "Agent proposal."
            )

        if request.updated_content != item.current_content:
            raise ReviewIntegrityError(
                "accepted_as_generated must not contain human-edited content."
            )

        content_selection = next(
            (
                selection
                for selection in item.dimension_selections
                if (
                    selection.dimension == "content"
                    and selection.value_origin == "agent_proposal"
                )
            ),
            None,
        )

        if (
            content_selection is None
            or selected_keys[0]
            not in content_selection.source_reference_ids
        ):
            raise ReviewIntegrityError(
                "accepted_as_generated must select the exact Agent proposal "
                "supplying the current generated content."
            )

    elif outcome == "accepted_with_modification":
        expected_selected = 1 if proposal_count else 0

        if selected_count != expected_selected:
            raise ReviewIntegrityError(
                "accepted_with_modification requires one selected Agent "
                "proposal when proposals exist and none for evidence-only "
                "Review Items."
            )

    elif outcome == "combined":
        if proposal_count < 2 or selected_count < 2:
            raise ReviewIntegrityError(
                "combined requires at least two selected Agent proposals."
            )

    elif outcome in _NON_ACCEPTED_OUTCOMES:
        if selected_count:
            raise ReviewIntegrityError(
                "Non-accepted outcomes must not retain selected Agent "
                "proposals."
            )

    else:
        raise ReviewValidationError(
            "Unsupported Review Item outcome."
        )

    if (
        outcome == "rejected"
        and request.rationale is None
    ):
        raise ReviewIntegrityError(
            "Rejecting a Review Item requires a rationale."
        )


def _proposal_states(
    proposals: tuple[ReviewProposalReference, ...],
    *,
    review_outcome: str,
    selected_keys: tuple[str, ...],
) -> tuple[ReviewProposalReference, ...]:
    selected = set(selected_keys)

    if review_outcome == "rejected":
        return tuple(
            replace(reference, review_state="rejected")
            for reference in proposals
        )

    if review_outcome in _ACCEPTED_OUTCOMES:
        return tuple(
            replace(
                reference,
                review_state=(
                    "selected"
                    if proposal_selection_key(reference)
                    in selected
                    else "not_selected_due_to_human_selection"
                ),
            )
            for reference in proposals
        )

    return tuple(
        replace(reference, review_state="available")
        for reference in proposals
    )


def _dimension_selections(
    item: ReviewItem,
    *,
    request: ReviewItemEditRequest,
    selected_keys: tuple[str, ...],
    actor_identity: str,
    timestamp: str,
) -> tuple[ReviewDimensionSelection, ...]:
    selections = {
        selection.dimension: selection
        for selection in item.dimension_selections
    }

    if request.updated_content != item.current_content:
        selections["content"] = _human_selection(
            "content",
            (request.updated_content.primary_text,),
            selected_keys,
            request.rationale,
            actor_identity,
            timestamp,
        )

    old_classification = _classification(
        item.current_content
    )
    new_classification = _classification(
        request.updated_content
    )

    if old_classification != new_classification:
        selections["classification"] = _human_selection(
            "classification",
            new_classification,
            selected_keys,
            request.rationale,
            actor_identity,
            timestamp,
        )

    old_relationship = (
        item.current_content.relationship_representation
    )
    new_relationship = (
        request.updated_content.relationship_representation
    )

    if old_relationship != new_relationship:
        if new_relationship is None:
            raise ReviewIntegrityError(
                "A relationship representation cannot be cleared "
                "by an item-level edit."
            )

        selections[
            "relationship_representation"
        ] = _human_selection(
            "relationship_representation",
            _relationship_values(new_relationship),
            selected_keys,
            request.rationale,
            actor_identity,
            timestamp,
        )

    _apply_assignment(
        selections,
        "framework_assignment",
        request.framework_assignment_values,
        selected_keys,
        request.rationale,
        actor_identity,
        timestamp,
    )
    _apply_assignment(
        selections,
        "terminology_assignment",
        request.terminology_assignment_values,
        selected_keys,
        request.rationale,
        actor_identity,
        timestamp,
    )
    _apply_assignment(
        selections,
        "source_assignment",
        request.source_assignment_values,
        selected_keys,
        request.rationale,
        actor_identity,
        timestamp,
    )

    selections["review_outcome"] = _human_selection(
        "review_outcome",
        (request.review_outcome,),
        selected_keys,
        request.rationale,
        actor_identity,
        timestamp,
    )

    return tuple(
        selections[dimension]
        for dimension in sorted(selections)
    )


def _apply_assignment(
    selections: dict[str, ReviewDimensionSelection],
    dimension: str,
    values: tuple[str, ...] | None,
    source_reference_ids: tuple[str, ...],
    rationale: str | None,
    actor_identity: str,
    timestamp: str,
) -> None:
    if values is None:
        return

    if not values:
        selections.pop(dimension, None)
        return

    selections[dimension] = _human_selection(
        dimension,
        values,
        source_reference_ids,
        rationale,
        actor_identity,
        timestamp,
    )


def _human_selection(
    dimension: str,
    selected_values: tuple[str, ...],
    source_reference_ids: tuple[str, ...],
    rationale: str | None,
    actor_identity: str,
    timestamp: str,
) -> ReviewDimensionSelection:
    if not selected_values:
        raise ReviewValidationError(
            "A human Review selection must contain at least one value."
        )

    return ReviewDimensionSelection(
        dimension=dimension,
        selected_values=selected_values,
        value_origin="item_override",
        source_reference_ids=source_reference_ids,
        rationale=rationale,
        selected_by=actor_identity,
        selected_at=timestamp,
    )


def _classification(
    content: ReviewItemContent,
) -> tuple[str, ...]:
    values = tuple(
        value
        for value in (
            content.information_type,
            content.modality,
            content.epistemic_status,
        )
        if value is not None
    )

    if not values:
        raise ReviewIntegrityError(
            "Review Item classification must contain at least one value."
        )

    return values


def _relationship_values(
    relationship,
) -> tuple[str, ...]:
    return (
        relationship.semantic_intent,
        (
            relationship.sysml_v2_construct
            if relationship.sysml_v2_construct is not None
            else "unresolved"
        ),
        relationship.validation_status,
    )


def _text_tuple(
    values: object,
    label: str,
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ReviewValidationError(
            f"{label} must be a tuple."
        )

    result = []

    for value in values:
        selected = _single_line_text(
            value,
            f"{label} entry",
        )
        result.append(selected)

    if len(result) != len(set(result)):
        raise ReviewIntegrityError(
            f"{label} entries must be unique."
        )

    return tuple(result)


def _single_line_text(
    value: object,
    label: str,
) -> str:
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
            f"{label} must be non-empty single-line text "
            "without surrounding whitespace."
        )

    return selected


def _utc_timestamp(value: object) -> str:
    selected = _single_line_text(
        value,
        "timestamp",
    )

    if not selected.endswith("Z"):
        raise ReviewValidationError(
            "timestamp must be a UTC timestamp."
        )

    return selected
