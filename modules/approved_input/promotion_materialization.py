"""Materialize exact Approved Input manifests from finalized Review Items."""

from __future__ import annotations

from modules.review_workspace.finalized_artifact_set import (
    FinalizedReviewArtifactSet,
)
from modules.review_workspace.types import ReviewDocument, ReviewItem

from .eligibility import ApprovedInputPromotionItemAssessment
from .errors import ApprovedInputIntegrityError
from .manifest import create_approved_input_manifest
from .types import (
    ApprovedInputCanonicalContent,
    ApprovedInputManifest,
    ApprovedInputRelationshipProperty,
    ApprovedInputRelationshipRepresentation,
)


def create_manifest_from_review_item(
    document: ReviewDocument,
    artifact_set: FinalizedReviewArtifactSet,
    item_assessment: ApprovedInputPromotionItemAssessment,
    item: ReviewItem,
    *,
    approved_input_id: str,
    created_at: str,
) -> ApprovedInputManifest:
    """Project one exact promotable Review Item into one manifest."""

    if item_assessment.approved_input_kind is None:
        raise ApprovedInputIntegrityError(
            "Promotable Review Item requires an Approved Input kind."
        )

    content = item.current_content
    canonical_content = ApprovedInputCanonicalContent(
        title=content.title,
        primary_text=content.primary_text,
        description=content.description,
        information_type=content.information_type,
        modality=content.modality,
        epistemic_status=content.epistemic_status,
    )

    return create_approved_input_manifest(
        project_id=document.project_id,
        approved_input_id=approved_input_id,
        approved_input_kind=(
            item_assessment.approved_input_kind
        ),
        canonical_content=canonical_content,
        selected_classification=_single_dimension_value(
            item,
            "classification",
        ),
        selected_framework_assignment=_single_dimension_value(
            item,
            "framework_assignment",
        ),
        selected_terminology_assignment=_single_dimension_value(
            item,
            "terminology_assignment",
        ),
        selected_source_assignments=_dimension_values(
            item,
            "source_assignment",
        ),
        selected_relationship_representation=(
            _approved_relationship(item)
        ),
        stable_subject_key=item.stable_subject_key,
        review_document_id=document.review_document_id,
        review_document_version_id=(
            artifact_set.reviewed_document.review_document_version_id
        ),
        review_revision_id=(
            artifact_set.reviewed_document.review_revision_id
        ),
        review_item_id=item.review_item_id,
        review_item_kind=item.review_item_kind,
        review_item_fingerprint=item.item_content_fingerprint,
        finalized_artifact_set_fingerprint=(
            artifact_set.artifact_set_fingerprint
        ),
        finalization_decision_id=(
            artifact_set.reviewed_document.finalization_decision_id
        ),
        finalization_decision_fingerprint=(
            artifact_set.reviewed_document
            .finalization_decision_fingerprint
        ),
        finalization_validation_fingerprint=(
            artifact_set.reviewed_document
            .finalization_validation_fingerprint
        ),
        source_id=document.source_id,
        source_sha256=document.source_sha256,
        processing_run_id=document.processing_run_id,
        attempt_id=document.attempt_id,
        primary_artifact_reference=(
            document.primary_review_artifact_reference
        ),
        supporting_artifact_references=(
            document.supporting_artifact_references
        ),
        proposal_references=tuple(
            sorted(
                _proposal_reference_token(reference)
                for reference in item.proposal_references
            )
        ),
        created_at=created_at,
    )


def _approved_relationship(
    item: ReviewItem,
) -> ApprovedInputRelationshipRepresentation | None:
    if item.review_item_kind != "relationship":
        return None

    relationship = item.current_content.relationship_representation

    if relationship is None:
        raise ApprovedInputIntegrityError(
            "Promotable relationship requires a relationship "
            "representation."
        )

    if (
        relationship.validation_status != "valid"
        or relationship.sysml_v2_construct is None
        or relationship.textual_notation_preview is None
        or relationship.validation_fingerprint is None
    ):
        raise ApprovedInputIntegrityError(
            "Promotable relationship requires an exact profile-valid "
            "representation."
        )

    return ApprovedInputRelationshipRepresentation(
        source_subject_key=relationship.source_subject_key,
        target_subject_key=relationship.target_subject_key,
        semantic_intent=relationship.semantic_intent,
        sysml_v2_construct=relationship.sysml_v2_construct,
        construct_properties=tuple(
            ApprovedInputRelationshipProperty(
                name=prop.name,
                value=prop.value,
            )
            for prop in relationship.construct_properties
        ),
        target_notation_profile_id=(
            relationship.target_notation_profile_id
        ),
        target_notation_profile_version=(
            relationship.target_notation_profile_version
        ),
        textual_notation_preview=(
            relationship.textual_notation_preview
        ),
        profile_validation_status=relationship.validation_status,
        profile_validation_fingerprint=(
            relationship.validation_fingerprint
        ),
    )


def _dimension_values(
    item: ReviewItem,
    dimension: str,
) -> tuple[str, ...]:
    selection = next(
        (
            value
            for value in item.dimension_selections
            if value.dimension == dimension
        ),
        None,
    )

    if selection is None:
        return ()

    return selection.selected_values


def _single_dimension_value(
    item: ReviewItem,
    dimension: str,
) -> str | None:
    values = _dimension_values(item, dimension)

    if not values:
        return None

    if len(values) != 1:
        raise ApprovedInputIntegrityError(
            f"Review dimension {dimension!r} requires exactly one "
            "effective value for Approved Input promotion."
        )

    return values[0]


def _proposal_reference_token(reference) -> str:
    return (
        f"{reference.artifact_reference.artifact_id}:"
        f"{reference.proposal_id}:"
        f"{reference.proposal_content_fingerprint}"
    )
