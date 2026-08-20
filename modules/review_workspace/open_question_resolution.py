"""Pure Human commands for resolving retained P9 Open Questions."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
    StaleReviewRevisionError,
)
from .item_manifest import create_review_item, validate_review_item
from .p9_proposal_adapter import (
    create_element_stable_subject_key,
    create_relationship_stable_subject_key,
)
from .p9_review_item_builder import (
    DEFAULT_TARGET_NOTATION_PROFILE_ID,
    DEFAULT_TARGET_NOTATION_PROFILE_VERSION,
)
from .revision_manifest import create_review_revision, validate_review_revision
from .types import (
    ReviewDimensionSelection,
    ReviewItem,
    ReviewItemContent,
    ReviewRelationshipRepresentation,
    ReviewRevision,
)


@dataclass(frozen=True, slots=True)
class CreateElementFromOpenQuestionRequest:
    """Explicit Human creation of one source-supported element."""

    expected_revision_id: str
    expected_question_fingerprint: str
    element_name: str
    element_type: str
    primary_text: str
    description: str | None
    rationale: str


@dataclass(frozen=True, slots=True)
class ResolveRelationshipEndpointsRequest:
    """Explicit Human binding of an unresolved relationship to element subjects."""

    expected_revision_id: str
    expected_question_fingerprint: str
    source_subject_key: str
    target_subject_key: str
    semantic_intent: str
    relationship_title: str
    relationship_primary_text: str
    rationale: str


def create_element_from_open_question_revision(
    current_revision: object,
    *,
    open_question_item_id: str,
    request: object,
    new_review_item_id: str,
    new_review_revision_id: str,
    actor_identity: str,
    timestamp: str,
) -> ReviewRevision:
    """Create one Human-authored element while keeping the question unresolved."""

    revision = _validated_revision(current_revision)
    if not isinstance(request, CreateElementFromOpenQuestionRequest):
        raise ReviewValidationError(
            "request must be a CreateElementFromOpenQuestionRequest."
        )

    question = _target_open_question(
        revision,
        review_item_id=open_question_item_id,
        expected_revision_id=request.expected_revision_id,
        expected_fingerprint=request.expected_question_fingerprint,
    )
    _require_question_evidence(question)

    element_name = _text(request.element_name, "element_name")
    element_type = _text(request.element_type, "element_type")
    primary_text = _text(request.primary_text, "primary_text")
    rationale = _text(request.rationale, "rationale")
    description = _optional_text(request.description, "description")

    stable_subject_key = create_element_stable_subject_key(
        element_type=element_type,
        candidate_name=element_name,
    )
    _require_new_subject(
        revision,
        stable_subject_key=stable_subject_key,
        new_review_item_id=new_review_item_id,
    )

    new_item = create_review_item(
        project_id=revision.project_id,
        review_document_id=revision.review_document_id,
        review_document_version_id=revision.review_document_version_id,
        review_item_id=new_review_item_id,
        review_item_kind="element",
        stable_subject_key=stable_subject_key,
        section="elements",
        lineage_operation="human_created",
        derived_from_review_item_ids=(),
        original_report_locator=(
            "human_resolution:"
            f"{question.review_item_id}:create_element"
        ),
        proposal_references=(),
        source_evidence_references=question.source_evidence_references,
        consensus_evidence_references=(),
        current_content=ReviewItemContent(
            title=element_name,
            primary_text=primary_text,
            description=description,
            information_type=element_type,
            modality=None,
            epistemic_status="human_created",
            human_rationale=rationale,
            human_confidence=None,
            relationship_representation=None,
        ),
        dimension_selections=(),
        effective_review_outcome="open",
    )

    return _successor_revision(
        revision,
        review_items=revision.review_items + (new_item,),
        new_review_revision_id=new_review_revision_id,
        actor_identity=actor_identity,
        timestamp=timestamp,
    )


def create_relationship_endpoint_resolution_revision(
    current_revision: object,
    *,
    open_question_item_id: str,
    request: object,
    new_relationship_review_item_id: str,
    new_review_revision_id: str,
    actor_identity: str,
    timestamp: str,
    target_notation_profile_id: str = DEFAULT_TARGET_NOTATION_PROFILE_ID,
    target_notation_profile_version: str = DEFAULT_TARGET_NOTATION_PROFILE_VERSION,
) -> ReviewRevision:
    """Resolve endpoint identity explicitly and create an open relationship item."""

    revision = _validated_revision(current_revision)
    if not isinstance(request, ResolveRelationshipEndpointsRequest):
        raise ReviewValidationError(
            "request must be a ResolveRelationshipEndpointsRequest."
        )

    question = _target_open_question(
        revision,
        review_item_id=open_question_item_id,
        expected_revision_id=request.expected_revision_id,
        expected_fingerprint=request.expected_question_fingerprint,
    )
    _require_question_evidence(question)

    source_item = _element_subject(
        revision,
        request.source_subject_key,
        label="source_subject_key",
    )
    target_item = _element_subject(
        revision,
        request.target_subject_key,
        label="target_subject_key",
    )

    semantic_intent = _text(request.semantic_intent, "semantic_intent")
    relationship_title = _text(
        request.relationship_title,
        "relationship_title",
    )
    relationship_primary_text = _text(
        request.relationship_primary_text,
        "relationship_primary_text",
    )
    rationale = _text(request.rationale, "rationale")

    stable_subject_key = create_relationship_stable_subject_key(
        source_subject_key=source_item.stable_subject_key,
        link_type=semantic_intent,
        target_subject_key=target_item.stable_subject_key,
    )
    _require_new_subject(
        revision,
        stable_subject_key=stable_subject_key,
        new_review_item_id=new_relationship_review_item_id,
    )

    relationship = create_review_item(
        project_id=revision.project_id,
        review_document_id=revision.review_document_id,
        review_document_version_id=revision.review_document_version_id,
        review_item_id=new_relationship_review_item_id,
        review_item_kind="relationship",
        stable_subject_key=stable_subject_key,
        section="relationships",
        lineage_operation="human_created",
        derived_from_review_item_ids=(),
        original_report_locator=(
            "human_resolution:"
            f"{question.review_item_id}:relationship"
        ),
        proposal_references=(),
        source_evidence_references=question.source_evidence_references,
        consensus_evidence_references=(),
        current_content=ReviewItemContent(
            title=relationship_title,
            primary_text=relationship_primary_text,
            description=(
                "Human-resolved relationship endpoint binding. "
                f"Resolution rationale: {rationale}"
            ),
            information_type="relationship",
            modality=None,
            epistemic_status="human_resolved_endpoints",
            human_rationale=rationale,
            human_confidence=None,
            relationship_representation=ReviewRelationshipRepresentation(
                source_subject_key=source_item.stable_subject_key,
                target_subject_key=target_item.stable_subject_key,
                semantic_intent=semantic_intent,
                sysml_v2_construct=None,
                construct_properties=(),
                target_notation_profile_id=target_notation_profile_id,
                target_notation_profile_version=target_notation_profile_version,
                textual_notation_preview=None,
                validation_status="unresolved",
                validation_fingerprint=None,
            ),
        ),
        dimension_selections=(),
        effective_review_outcome="open",
    )

    resolved_question = _resolved_question_item(
        question,
        relationship_review_item_id=new_relationship_review_item_id,
        rationale=rationale,
        actor_identity=actor_identity,
        timestamp=timestamp,
    )

    items = tuple(
        resolved_question
        if item.review_item_id == question.review_item_id
        else item
        for item in revision.review_items
    ) + (relationship,)

    return _successor_revision(
        revision,
        review_items=items,
        new_review_revision_id=new_review_revision_id,
        actor_identity=actor_identity,
        timestamp=timestamp,
    )


def _resolved_question_item(
    question: ReviewItem,
    *,
    relationship_review_item_id: str,
    rationale: str,
    actor_identity: str,
    timestamp: str,
) -> ReviewItem:
    content = replace(
        question.current_content,
        description=(
            (question.current_content.description or "")
            + "\n\nHuman resolution materialized as Review Item "
            + relationship_review_item_id
            + "."
        ).strip(),
        human_rationale=rationale,
    )

    selections = {
        selection.dimension: selection
        for selection in question.dimension_selections
    }
    selections["review_outcome"] = ReviewDimensionSelection(
        dimension="review_outcome",
        selected_values=("accepted_with_modification",),
        value_origin="item_override",
        source_reference_ids=(relationship_review_item_id,),
        rationale=rationale,
        selected_by=_text(actor_identity, "actor_identity"),
        selected_at=_text(timestamp, "timestamp"),
    )

    return create_review_item(
        project_id=question.project_id,
        review_document_id=question.review_document_id,
        review_document_version_id=question.review_document_version_id,
        review_item_id=question.review_item_id,
        review_item_kind=question.review_item_kind,
        stable_subject_key=question.stable_subject_key,
        section=question.section,
        lineage_operation=question.lineage_operation,
        derived_from_review_item_ids=question.derived_from_review_item_ids,
        original_report_locator=question.original_report_locator,
        proposal_references=question.proposal_references,
        source_evidence_references=question.source_evidence_references,
        consensus_evidence_references=question.consensus_evidence_references,
        current_content=content,
        dimension_selections=tuple(
            selections[key] for key in sorted(selections)
        ),
        effective_review_outcome="accepted_with_modification",
    )


def _target_open_question(
    revision: ReviewRevision,
    *,
    review_item_id: str,
    expected_revision_id: str,
    expected_fingerprint: str,
) -> ReviewItem:
    if revision.review_revision_id != expected_revision_id:
        raise StaleReviewRevisionError(
            "The resolution does not target the current Review Revision."
        )

    matches = tuple(
        item
        for item in revision.review_items
        if item.review_item_id == review_item_id
    )
    if not matches:
        raise ReviewReferenceError(
            "The requested Open Question is unavailable."
        )
    if len(matches) != 1:
        raise ReviewIntegrityError(
            "Review Item identities must be unique in one Revision."
        )

    question = matches[0]
    if question.review_item_kind != "open_question":
        raise ReviewIntegrityError(
            "Endpoint resolution must target an Open Question."
        )
    if question.item_content_fingerprint != expected_fingerprint:
        raise StaleReviewRevisionError(
            "The Open Question changed after the resolution was opened."
        )
    if question.effective_review_outcome not in {
        "open",
        "unresolved",
        "deferred",
    }:
        raise ReviewIntegrityError(
            "Only an unresolved Open Question may be resolved."
        )

    return question


def _element_subject(
    revision: ReviewRevision,
    stable_subject_key: str,
    *,
    label: str,
) -> ReviewItem:
    key = _text(stable_subject_key, label)
    matches = tuple(
        item
        for item in revision.review_items
        if item.stable_subject_key == key
    )
    if not matches:
        raise ReviewReferenceError(
            f"{label} does not identify an existing Review element."
        )
    if len(matches) != 1:
        raise ReviewIntegrityError(
            "Stable Review subject identities must be unique."
        )

    item = matches[0]
    if item.review_item_kind != "element":
        raise ReviewIntegrityError(
            f"{label} must identify an element Review Item."
        )
    if item.effective_review_outcome in {"rejected", "out_of_scope"}:
        raise ReviewIntegrityError(
            f"{label} identifies an element that is not eligible "
            "for endpoint selection."
        )

    return item


def _require_question_evidence(question: ReviewItem) -> None:
    if not question.source_evidence_references:
        raise ReviewIntegrityError(
            "Open Question resolution requires exact Source Evidence."
        )


def _require_new_subject(
    revision: ReviewRevision,
    *,
    stable_subject_key: str,
    new_review_item_id: str,
) -> None:
    if any(
        item.review_item_id == new_review_item_id
        for item in revision.review_items
    ):
        raise ReviewIntegrityError(
            "The new Review Item ID is already occupied."
        )
    if any(
        item.stable_subject_key == stable_subject_key
        for item in revision.review_items
    ):
        raise ReviewIntegrityError(
            "The resolved Review subject already exists."
        )


def _successor_revision(
    current_revision: ReviewRevision,
    *,
    review_items: tuple[ReviewItem, ...],
    new_review_revision_id: str,
    actor_identity: str,
    timestamp: str,
) -> ReviewRevision:
    return create_review_revision(
        project_id=current_revision.project_id,
        review_document_id=current_revision.review_document_id,
        review_document_version_id=current_revision.review_document_version_id,
        review_revision_id=new_review_revision_id,
        revision_sequence=current_revision.revision_sequence + 1,
        predecessor_revision_id=current_revision.review_revision_id,
        review_items=review_items,
        scoped_review_action_ids=current_revision.scoped_review_action_ids,
        created_by=_text(actor_identity, "actor_identity"),
        timestamp=_text(timestamp, "timestamp"),
    )


def _validated_revision(value: object) -> ReviewRevision:
    if not isinstance(value, ReviewRevision):
        raise ReviewValidationError(
            "current_revision must be a ReviewRevision."
        )
    validate_review_revision(value)
    for item in value.review_items:
        validate_review_item(item)
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewValidationError(f"{label} must be non-empty text.")
    return value.strip()


def _optional_text(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _text(value, label)
