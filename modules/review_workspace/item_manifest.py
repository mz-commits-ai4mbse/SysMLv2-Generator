"""Create, validate and serialize immutable Review Items."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import PurePosixPath
import re
from typing import Any

from modules.project_processing import (
    ProcessingArtifactReference,
    ProcessingValidationError,
    create_processing_artifact_reference,
    validate_processing_artifact_reference,
)
from modules.project_workspace.identifiers import (
    is_valid_project_id,
)

from .errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from .identifiers import (
    validate_review_document_id,
    validate_review_document_version_id,
    validate_review_item_id,
)
from .types import (
    RELATIONSHIP_PROFILE_VALIDATION_STATUSES,
    REVIEW_DECISION_DIMENSIONS,
    REVIEW_ITEM_KINDS,
    REVIEW_ITEM_LINEAGE_OPERATIONS,
    REVIEW_ITEM_OUTCOMES,
    REVIEW_ITEM_SECTIONS,
    REVIEW_PROPOSAL_STATES,
    REVIEW_VALUE_ORIGINS,
    ReviewDimensionSelection,
    ReviewEvidenceReference,
    ReviewItem,
    ReviewItemContent,
    ReviewProperty,
    ReviewProposalReference,
    ReviewRelationshipRepresentation,
)


REVIEW_ITEM_SCHEMA_VERSION = "1.0.0"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_GENERIC_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,239}$"
)
_STABLE_SUBJECT_KEY_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9._:-]{0,239}$"
)
_EVIDENCE_ROLE_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]{0,119}$"
)
_PROFILE_ID_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9_]*$"
)
_SEMANTIC_VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+$"
)
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_ITEM_SECTION_BY_KIND = {
    "element": "elements",
    "relationship": "relationships",
    "open_question": "open_questions",
}

_ACCEPTED_OUTCOMES = frozenset(
    {
        "accepted_as_generated",
        "accepted_with_modification",
        "combined",
    }
)

_REVIEW_ITEM_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "review_document_id",
        "review_document_version_id",
        "review_item_id",
        "review_item_kind",
        "stable_subject_key",
        "section",
        "lineage_operation",
        "derived_from_review_item_ids",
        "original_report_locator",
        "proposal_references",
        "source_evidence_references",
        "consensus_evidence_references",
        "current_content",
        "dimension_selections",
        "effective_review_outcome",
        "item_content_fingerprint",
    }
)

_ARTIFACT_REFERENCE_FIELDS = frozenset(
    {
        "artifact_type",
        "artifact_id",
        "content_fingerprint",
        "repository_relative_path",
    }
)

_PROPOSAL_REFERENCE_FIELDS = frozenset(
    {
        "artifact_reference",
        "agent_id",
        "persona_id",
        "proposal_id",
        "proposal_content_fingerprint",
        "original_report_locator",
        "review_state",
    }
)

_EVIDENCE_REFERENCE_FIELDS = frozenset(
    {
        "artifact_reference",
        "evidence_role",
        "evidence_locator",
        "evidence_content_fingerprint",
    }
)

_CONTENT_FIELDS = frozenset(
    {
        "title",
        "primary_text",
        "description",
        "information_type",
        "modality",
        "epistemic_status",
        "human_rationale",
        "human_confidence",
        "relationship_representation",
    }
)

_RELATIONSHIP_FIELDS = frozenset(
    {
        "source_subject_key",
        "target_subject_key",
        "semantic_intent",
        "sysml_v2_construct",
        "construct_properties",
        "target_notation_profile_id",
        "target_notation_profile_version",
        "textual_notation_preview",
        "validation_status",
        "validation_fingerprint",
    }
)

_PROPERTY_FIELDS = frozenset(
    {
        "name",
        "value",
    }
)

_DIMENSION_SELECTION_FIELDS = frozenset(
    {
        "dimension",
        "selected_values",
        "value_origin",
        "source_reference_ids",
        "rationale",
        "selected_by",
        "selected_at",
    }
)


def create_review_item(
    *,
    project_id: str,
    review_document_id: str,
    review_document_version_id: str,
    review_item_id: str,
    review_item_kind: str,
    stable_subject_key: str,
    section: str,
    lineage_operation: str,
    derived_from_review_item_ids: tuple[str, ...],
    original_report_locator: str,
    proposal_references: tuple[
        ReviewProposalReference,
        ...,
    ],
    source_evidence_references: tuple[
        ReviewEvidenceReference,
        ...,
    ],
    consensus_evidence_references: tuple[
        ReviewEvidenceReference,
        ...,
    ],
    current_content: ReviewItemContent,
    dimension_selections: tuple[
        ReviewDimensionSelection,
        ...,
    ],
    effective_review_outcome: str,
) -> ReviewItem:
    """Create one fingerprinted immutable Review Item."""

    provisional = ReviewItem(
        schema_version=REVIEW_ITEM_SCHEMA_VERSION,
        project_id=project_id,
        review_document_id=review_document_id,
        review_document_version_id=(
            review_document_version_id
        ),
        review_item_id=review_item_id,
        review_item_kind=review_item_kind,
        stable_subject_key=stable_subject_key,
        section=section,
        lineage_operation=lineage_operation,
        derived_from_review_item_ids=(
            derived_from_review_item_ids
        ),
        original_report_locator=original_report_locator,
        proposal_references=proposal_references,
        source_evidence_references=(
            source_evidence_references
        ),
        consensus_evidence_references=(
            consensus_evidence_references
        ),
        current_content=current_content,
        dimension_selections=dimension_selections,
        effective_review_outcome=effective_review_outcome,
        item_content_fingerprint="0" * 64,
    )

    _validate_review_item(
        provisional,
        verify_fingerprint=False,
    )

    item = replace(
        provisional,
        item_content_fingerprint=(
            calculate_review_item_fingerprint(provisional)
        ),
    )

    validate_review_item(item)

    return item


def parse_review_item(payload: object) -> ReviewItem:
    """Parse and validate one Review Item mapping."""

    data = _exact_object(
        payload,
        expected_fields=_REVIEW_ITEM_FIELDS,
        label="Review Item",
    )

    parent_payloads = data[
        "derived_from_review_item_ids"
    ]

    if not isinstance(parent_payloads, list):
        raise ReviewValidationError(
            "derived_from_review_item_ids must be "
            "a JSON array."
        )

    proposal_payloads = data["proposal_references"]

    if not isinstance(proposal_payloads, list):
        raise ReviewValidationError(
            "proposal_references must be a JSON array."
        )

    source_evidence_payloads = data[
        "source_evidence_references"
    ]

    if not isinstance(source_evidence_payloads, list):
        raise ReviewValidationError(
            "source_evidence_references must be "
            "a JSON array."
        )

    consensus_evidence_payloads = data[
        "consensus_evidence_references"
    ]

    if not isinstance(
        consensus_evidence_payloads,
        list,
    ):
        raise ReviewValidationError(
            "consensus_evidence_references must be "
            "a JSON array."
        )

    selection_payloads = data["dimension_selections"]

    if not isinstance(selection_payloads, list):
        raise ReviewValidationError(
            "dimension_selections must be a JSON array."
        )

    item = ReviewItem(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        review_document_id=data["review_document_id"],
        review_document_version_id=(
            data["review_document_version_id"]
        ),
        review_item_id=data["review_item_id"],
        review_item_kind=data["review_item_kind"],
        stable_subject_key=data["stable_subject_key"],
        section=data["section"],
        lineage_operation=data["lineage_operation"],
        derived_from_review_item_ids=tuple(
            parent_payloads
        ),
        original_report_locator=(
            data["original_report_locator"]
        ),
        proposal_references=tuple(
            _parse_proposal_reference(value)
            for value in proposal_payloads
        ),
        source_evidence_references=tuple(
            _parse_evidence_reference(value)
            for value in source_evidence_payloads
        ),
        consensus_evidence_references=tuple(
            _parse_evidence_reference(value)
            for value in consensus_evidence_payloads
        ),
        current_content=_parse_item_content(
            data["current_content"]
        ),
        dimension_selections=tuple(
            _parse_dimension_selection(value)
            for value in selection_payloads
        ),
        effective_review_outcome=(
            data["effective_review_outcome"]
        ),
        item_content_fingerprint=(
            data["item_content_fingerprint"]
        ),
    )

    validate_review_item(item)

    return item


def review_item_from_json(text: object) -> ReviewItem:
    """Parse one Review Item from strict JSON."""

    if not isinstance(text, str):
        raise ReviewValidationError(
            "Review Item JSON must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except ReviewValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ReviewValidationError(
            "Review Item is not valid JSON."
        ) from exc

    return parse_review_item(payload)


def review_item_to_dict(
    item: ReviewItem,
) -> dict[str, object]:
    """Serialize one validated Review Item."""

    validate_review_item(item)

    return _review_item_payload(
        item,
        include_fingerprint=True,
    )


def review_item_to_json(item: ReviewItem) -> str:
    """Serialize one Review Item deterministically."""

    return (
        json.dumps(
            review_item_to_dict(item),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def calculate_review_item_fingerprint(
    item: ReviewItem,
) -> str:
    """Calculate the deterministic Review Item fingerprint."""

    _validate_review_item(
        item,
        verify_fingerprint=False,
    )

    payload = _review_item_payload(
        item,
        include_fingerprint=False,
    )

    canonical_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()


def validate_review_item(item: ReviewItem) -> None:
    """Validate one complete Review Item."""

    _validate_review_item(
        item,
        verify_fingerprint=True,
    )


def _validate_review_item(
    item: ReviewItem,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(item, ReviewItem):
        raise ReviewValidationError(
            "item must be a ReviewItem."
        )

    if item.schema_version != REVIEW_ITEM_SCHEMA_VERSION:
        raise ReviewValidationError(
            "schema_version must be "
            f"{REVIEW_ITEM_SCHEMA_VERSION!r}."
        )

    if not is_valid_project_id(item.project_id):
        raise ReviewValidationError(
            "project_id must be a valid six-digit Project ID."
        )

    validate_review_document_id(
        item.review_document_id
    )
    validate_review_document_version_id(
        item.review_document_version_id
    )
    validate_review_item_id(item.review_item_id)

    if item.review_item_kind not in REVIEW_ITEM_KINDS:
        raise ReviewValidationError(
            "review_item_kind must be one of "
            f"{sorted(REVIEW_ITEM_KINDS)!r}."
        )

    if item.section not in REVIEW_ITEM_SECTIONS:
        raise ReviewValidationError(
            "section must be one of "
            f"{sorted(REVIEW_ITEM_SECTIONS)!r}."
        )

    expected_section = _ITEM_SECTION_BY_KIND[
        item.review_item_kind
    ]

    if item.section != expected_section:
        raise ReviewIntegrityError(
            "Review Item section does not match "
            "review_item_kind."
        )

    _identifier(
        item.stable_subject_key,
        _STABLE_SUBJECT_KEY_PATTERN,
        "stable_subject_key",
    )

    if (
        item.lineage_operation
        not in REVIEW_ITEM_LINEAGE_OPERATIONS
    ):
        raise ReviewValidationError(
            "lineage_operation must be one of "
            f"{sorted(REVIEW_ITEM_LINEAGE_OPERATIONS)!r}."
        )

    _validate_lineage(item)

    _text(
        item.original_report_locator,
        "original_report_locator",
    )

    if (
        item.effective_review_outcome
        not in REVIEW_ITEM_OUTCOMES
    ):
        raise ReviewValidationError(
            "effective_review_outcome must be one of "
            f"{sorted(REVIEW_ITEM_OUTCOMES)!r}."
        )

    _validate_proposal_references(
        item.proposal_references,
        project_id=item.project_id,
        effective_outcome=item.effective_review_outcome,
    )

    _validate_evidence_collection(
        item.source_evidence_references,
        project_id=item.project_id,
        label="source_evidence_references",
    )

    _validate_evidence_collection(
        item.consensus_evidence_references,
        project_id=item.project_id,
        label="consensus_evidence_references",
    )

    _validate_item_content(
        item.current_content,
        review_item_kind=item.review_item_kind,
        effective_outcome=item.effective_review_outcome,
    )

    _validate_dimension_selections(
        item.dimension_selections,
        effective_outcome=item.effective_review_outcome,
    )

    _sha256(
        item.item_content_fingerprint,
        "item_content_fingerprint",
    )

    if verify_fingerprint and (
        item.item_content_fingerprint
        != calculate_review_item_fingerprint(item)
    ):
        raise ReviewIntegrityError(
            "Review Item fingerprint does not match "
            "its content."
        )


def _validate_lineage(item: ReviewItem) -> None:
    if not isinstance(
        item.derived_from_review_item_ids,
        tuple,
    ):
        raise ReviewValidationError(
            "derived_from_review_item_ids must be a tuple."
        )

    parents = item.derived_from_review_item_ids

    if len(parents) != len(set(parents)):
        raise ReviewIntegrityError(
            "derived_from_review_item_ids must be unique."
        )

    for parent_id in parents:
        validate_review_item_id(parent_id)

        if parent_id == item.review_item_id:
            raise ReviewIntegrityError(
                "A Review Item must not derive from itself."
            )

    if item.lineage_operation in {
        "original",
        "human_created",
    }:
        if parents:
            raise ReviewIntegrityError(
                f"{item.lineage_operation} Review Items "
                "must not have parent Review Items."
            )

    elif item.lineage_operation == "split":
        if len(parents) != 1:
            raise ReviewIntegrityError(
                "A split Review Item requires exactly "
                "one parent Review Item."
            )

    elif item.lineage_operation == "merge":
        if len(parents) < 2:
            raise ReviewIntegrityError(
                "A merged Review Item requires at least "
                "two parent Review Items."
            )


def _validate_proposal_references(
    proposals: tuple[ReviewProposalReference, ...],
    *,
    project_id: str,
    effective_outcome: str,
) -> None:
    if not isinstance(proposals, tuple):
        raise ReviewValidationError(
            "proposal_references must be a tuple."
        )

    keys: set[tuple[str, str, str]] = set()
    selected_count = 0
    automatic_non_selection_count = 0

    for proposal in proposals:
        _validate_proposal_reference(
            proposal,
            project_id=project_id,
        )

        key = (
            proposal.artifact_reference.artifact_id,
            proposal.proposal_id,
            proposal.proposal_content_fingerprint,
        )

        if key in keys:
            raise ReviewIntegrityError(
                "proposal_references must be unique."
            )

        keys.add(key)

        if proposal.review_state == "selected":
            selected_count += 1

        if (
            proposal.review_state
            == "not_selected_due_to_human_selection"
        ):
            automatic_non_selection_count += 1

    if (
        automatic_non_selection_count > 0
        and selected_count == 0
    ):
        raise ReviewIntegrityError(
            "Automatically non-selected proposals require "
            "at least one selected proposal."
        )

    if (
        selected_count > 1
        and effective_outcome != "combined"
    ):
        raise ReviewIntegrityError(
            "Multiple selected proposals require the "
            "combined review outcome."
        )

    if effective_outcome == "accepted_as_generated":
        if selected_count != 1:
            raise ReviewIntegrityError(
                "accepted_as_generated requires exactly "
                "one selected proposal."
            )

    elif effective_outcome == "combined":
        if selected_count < 2:
            raise ReviewIntegrityError(
                "combined requires at least two selected "
                "proposals."
            )


def _validate_proposal_reference(
    proposal: ReviewProposalReference,
    *,
    project_id: str,
) -> None:
    if not isinstance(proposal, ReviewProposalReference):
        raise ReviewValidationError(
            "proposal_references entries must be "
            "ReviewProposalReference values."
        )

    _validate_artifact_reference(
        proposal.artifact_reference,
        project_id=project_id,
        label="proposal artifact reference",
    )

    _identifier(
        proposal.agent_id,
        _GENERIC_IDENTIFIER_PATTERN,
        "agent_id",
    )
    _identifier(
        proposal.persona_id,
        _GENERIC_IDENTIFIER_PATTERN,
        "persona_id",
    )
    _identifier(
        proposal.proposal_id,
        _GENERIC_IDENTIFIER_PATTERN,
        "proposal_id",
    )
    _sha256(
        proposal.proposal_content_fingerprint,
        "proposal_content_fingerprint",
    )
    _text(
        proposal.original_report_locator,
        "proposal original_report_locator",
    )

    if proposal.review_state not in REVIEW_PROPOSAL_STATES:
        raise ReviewValidationError(
            "proposal review_state must be one of "
            f"{sorted(REVIEW_PROPOSAL_STATES)!r}."
        )


def _validate_evidence_collection(
    references: tuple[ReviewEvidenceReference, ...],
    *,
    project_id: str,
    label: str,
) -> None:
    if not isinstance(references, tuple):
        raise ReviewValidationError(
            f"{label} must be a tuple."
        )

    keys: set[tuple[str, str, str]] = set()

    for reference in references:
        _validate_evidence_reference(
            reference,
            project_id=project_id,
        )

        key = (
            reference.artifact_reference.artifact_id,
            reference.evidence_locator,
            reference.evidence_content_fingerprint,
        )

        if key in keys:
            raise ReviewIntegrityError(
                f"{label} must contain unique references."
            )

        keys.add(key)


def _validate_evidence_reference(
    reference: ReviewEvidenceReference,
    *,
    project_id: str,
) -> None:
    if not isinstance(reference, ReviewEvidenceReference):
        raise ReviewValidationError(
            "Evidence entries must be "
            "ReviewEvidenceReference values."
        )

    _validate_artifact_reference(
        reference.artifact_reference,
        project_id=project_id,
        label="evidence artifact reference",
    )

    _identifier(
        reference.evidence_role,
        _EVIDENCE_ROLE_PATTERN,
        "evidence_role",
    )
    _text(
        reference.evidence_locator,
        "evidence_locator",
    )
    _sha256(
        reference.evidence_content_fingerprint,
        "evidence_content_fingerprint",
    )


def _validate_item_content(
    content: ReviewItemContent,
    *,
    review_item_kind: str,
    effective_outcome: str,
) -> None:
    if not isinstance(content, ReviewItemContent):
        raise ReviewValidationError(
            "current_content must be ReviewItemContent."
        )

    _text(content.title, "current_content.title")
    _text(
        content.primary_text,
        "current_content.primary_text",
    )

    for label, value in (
        ("description", content.description),
        ("information_type", content.information_type),
        ("modality", content.modality),
        ("epistemic_status", content.epistemic_status),
        ("human_rationale", content.human_rationale),
        ("human_confidence", content.human_confidence),
    ):
        _optional_text(
            value,
            f"current_content.{label}",
        )

    relationship = content.relationship_representation

    if review_item_kind == "relationship":
        if relationship is None:
            raise ReviewIntegrityError(
                "A relationship Review Item requires "
                "relationship_representation."
            )

        _validate_relationship_representation(
            relationship
        )

        if (
            effective_outcome in _ACCEPTED_OUTCOMES
            and relationship.validation_status != "valid"
        ):
            raise ReviewIntegrityError(
                "An accepted relationship requires a valid "
                "SysML v2 profile validation."
            )

    elif relationship is not None:
        raise ReviewIntegrityError(
            "Only relationship Review Items may contain "
            "relationship_representation."
        )


def _validate_relationship_representation(
    relationship: ReviewRelationshipRepresentation,
) -> None:
    if not isinstance(
        relationship,
        ReviewRelationshipRepresentation,
    ):
        raise ReviewValidationError(
            "relationship_representation must be a "
            "ReviewRelationshipRepresentation."
        )

    _text(
        relationship.source_subject_key,
        "relationship source_subject_key",
    )
    _text(
        relationship.target_subject_key,
        "relationship target_subject_key",
    )
    _text(
        relationship.semantic_intent,
        "relationship semantic_intent",
    )

    _identifier(
        relationship.target_notation_profile_id,
        _PROFILE_ID_PATTERN,
        "target_notation_profile_id",
    )
    _identifier(
        relationship.target_notation_profile_version,
        _SEMANTIC_VERSION_PATTERN,
        "target_notation_profile_version",
    )

    if (
        relationship.validation_status
        not in RELATIONSHIP_PROFILE_VALIDATION_STATUSES
    ):
        raise ReviewValidationError(
            "relationship validation_status must be one of "
            f"{sorted(RELATIONSHIP_PROFILE_VALIDATION_STATUSES)!r}."
        )

    if relationship.validation_status == "not_applicable":
        raise ReviewIntegrityError(
            "A relationship representation cannot use "
            "not_applicable validation."
        )

    _validate_properties(
        relationship.construct_properties
    )

    if relationship.validation_status == "unresolved":
        if relationship.sysml_v2_construct is not None:
            raise ReviewIntegrityError(
                "An unresolved relationship must not select "
                "a SysML v2 construct."
            )

        if relationship.textual_notation_preview is not None:
            raise ReviewIntegrityError(
                "An unresolved relationship must not contain "
                "a textual notation preview."
            )

        if relationship.validation_fingerprint is not None:
            raise ReviewIntegrityError(
                "An unresolved relationship must not contain "
                "a validation fingerprint."
            )

        return

    _identifier(
        relationship.sysml_v2_construct,
        _GENERIC_IDENTIFIER_PATTERN,
        "sysml_v2_construct",
    )
    _text(
        relationship.textual_notation_preview,
        "textual_notation_preview",
    )
    _sha256(
        relationship.validation_fingerprint,
        "validation_fingerprint",
    )


def _validate_properties(
    properties: tuple[ReviewProperty, ...],
) -> None:
    if not isinstance(properties, tuple):
        raise ReviewValidationError(
            "construct_properties must be a tuple."
        )

    names: set[str] = set()

    for item in properties:
        if not isinstance(item, ReviewProperty):
            raise ReviewValidationError(
                "construct_properties entries must be "
                "ReviewProperty values."
            )

        name = _identifier(
            item.name,
            _GENERIC_IDENTIFIER_PATTERN,
            "property name",
        )
        _text(item.value, "property value")

        if name in names:
            raise ReviewIntegrityError(
                "construct property names must be unique."
            )

        names.add(name)


def _validate_dimension_selections(
    selections: tuple[ReviewDimensionSelection, ...],
    *,
    effective_outcome: str,
) -> None:
    if not isinstance(selections, tuple):
        raise ReviewValidationError(
            "dimension_selections must be a tuple."
        )

    dimensions: set[str] = set()

    for selection in selections:
        _validate_dimension_selection(selection)

        if selection.dimension in dimensions:
            raise ReviewIntegrityError(
                "Only one selection per review dimension "
                "is permitted."
            )

        dimensions.add(selection.dimension)

        if selection.dimension == "review_outcome":
            if selection.selected_values != (
                effective_outcome,
            ):
                raise ReviewIntegrityError(
                    "The review_outcome dimension must match "
                    "effective_review_outcome."
                )


def _validate_dimension_selection(
    selection: ReviewDimensionSelection,
) -> None:
    if not isinstance(selection, ReviewDimensionSelection):
        raise ReviewValidationError(
            "dimension_selections entries must be "
            "ReviewDimensionSelection values."
        )

    if selection.dimension not in REVIEW_DECISION_DIMENSIONS:
        raise ReviewValidationError(
            "selection dimension must be one of "
            f"{sorted(REVIEW_DECISION_DIMENSIONS)!r}."
        )

    if selection.value_origin not in REVIEW_VALUE_ORIGINS:
        raise ReviewValidationError(
            "value_origin must be one of "
            f"{sorted(REVIEW_VALUE_ORIGINS)!r}."
        )

    _non_empty_unique_text_tuple(
        selection.selected_values,
        "selected_values",
    )
    _unique_text_tuple(
        selection.source_reference_ids,
        "source_reference_ids",
    )
    _optional_text(selection.rationale, "rationale")

    if selection.dimension == "review_outcome":
        if (
            len(selection.selected_values) != 1
            or selection.selected_values[0]
            not in REVIEW_ITEM_OUTCOMES
        ):
            raise ReviewValidationError(
                "A review_outcome selection requires exactly "
                "one valid Review Item outcome."
            )

    if selection.value_origin == "agent_proposal":
        if (
            selection.selected_by is not None
            or selection.selected_at is not None
        ):
            raise ReviewIntegrityError(
                "An Agent-proposal value must not contain "
                "human selection metadata."
            )

    else:
        _text(selection.selected_by, "selected_by")
        _utc_timestamp(
            selection.selected_at,
            "selected_at",
        )


def _review_item_payload(
    item: ReviewItem,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": item.schema_version,
        "project_id": item.project_id,
        "review_document_id": item.review_document_id,
        "review_document_version_id": (
            item.review_document_version_id
        ),
        "review_item_id": item.review_item_id,
        "review_item_kind": item.review_item_kind,
        "stable_subject_key": item.stable_subject_key,
        "section": item.section,
        "lineage_operation": item.lineage_operation,
        "derived_from_review_item_ids": list(
            item.derived_from_review_item_ids
        ),
        "original_report_locator": (
            item.original_report_locator
        ),
        "proposal_references": [
            _proposal_reference_payload(reference)
            for reference in item.proposal_references
        ],
        "source_evidence_references": [
            _evidence_reference_payload(reference)
            for reference in (
                item.source_evidence_references
            )
        ],
        "consensus_evidence_references": [
            _evidence_reference_payload(reference)
            for reference in (
                item.consensus_evidence_references
            )
        ],
        "current_content": _item_content_payload(
            item.current_content
        ),
        "dimension_selections": [
            _dimension_selection_payload(selection)
            for selection in item.dimension_selections
        ],
        "effective_review_outcome": (
            item.effective_review_outcome
        ),
    }

    if include_fingerprint:
        payload["item_content_fingerprint"] = (
            item.item_content_fingerprint
        )

    return payload


def _parse_proposal_reference(
    payload: object,
) -> ReviewProposalReference:
    data = _exact_object(
        payload,
        expected_fields=_PROPOSAL_REFERENCE_FIELDS,
        label="Review Proposal Reference",
    )

    return ReviewProposalReference(
        artifact_reference=_parse_artifact_reference(
            data["artifact_reference"]
        ),
        agent_id=data["agent_id"],
        persona_id=data["persona_id"],
        proposal_id=data["proposal_id"],
        proposal_content_fingerprint=(
            data["proposal_content_fingerprint"]
        ),
        original_report_locator=(
            data["original_report_locator"]
        ),
        review_state=data["review_state"],
    )


def _proposal_reference_payload(
    reference: ReviewProposalReference,
) -> dict[str, object]:
    return {
        "artifact_reference": _artifact_reference_payload(
            reference.artifact_reference
        ),
        "agent_id": reference.agent_id,
        "persona_id": reference.persona_id,
        "proposal_id": reference.proposal_id,
        "proposal_content_fingerprint": (
            reference.proposal_content_fingerprint
        ),
        "original_report_locator": (
            reference.original_report_locator
        ),
        "review_state": reference.review_state,
    }


def _parse_evidence_reference(
    payload: object,
) -> ReviewEvidenceReference:
    data = _exact_object(
        payload,
        expected_fields=_EVIDENCE_REFERENCE_FIELDS,
        label="Review Evidence Reference",
    )

    return ReviewEvidenceReference(
        artifact_reference=_parse_artifact_reference(
            data["artifact_reference"]
        ),
        evidence_role=data["evidence_role"],
        evidence_locator=data["evidence_locator"],
        evidence_content_fingerprint=(
            data["evidence_content_fingerprint"]
        ),
    )


def _evidence_reference_payload(
    reference: ReviewEvidenceReference,
) -> dict[str, object]:
    return {
        "artifact_reference": _artifact_reference_payload(
            reference.artifact_reference
        ),
        "evidence_role": reference.evidence_role,
        "evidence_locator": reference.evidence_locator,
        "evidence_content_fingerprint": (
            reference.evidence_content_fingerprint
        ),
    }


def _parse_item_content(
    payload: object,
) -> ReviewItemContent:
    data = _exact_object(
        payload,
        expected_fields=_CONTENT_FIELDS,
        label="Review Item Content",
    )

    relationship_payload = data[
        "relationship_representation"
    ]

    relationship = (
        None
        if relationship_payload is None
        else _parse_relationship_representation(
            relationship_payload
        )
    )

    return ReviewItemContent(
        title=data["title"],
        primary_text=data["primary_text"],
        description=data["description"],
        information_type=data["information_type"],
        modality=data["modality"],
        epistemic_status=data["epistemic_status"],
        human_rationale=data["human_rationale"],
        human_confidence=data["human_confidence"],
        relationship_representation=relationship,
    )


def _item_content_payload(
    content: ReviewItemContent,
) -> dict[str, object]:
    return {
        "title": content.title,
        "primary_text": content.primary_text,
        "description": content.description,
        "information_type": content.information_type,
        "modality": content.modality,
        "epistemic_status": content.epistemic_status,
        "human_rationale": content.human_rationale,
        "human_confidence": content.human_confidence,
        "relationship_representation": (
            None
            if content.relationship_representation is None
            else _relationship_payload(
                content.relationship_representation
            )
        ),
    }


def _parse_relationship_representation(
    payload: object,
) -> ReviewRelationshipRepresentation:
    data = _exact_object(
        payload,
        expected_fields=_RELATIONSHIP_FIELDS,
        label="Review Relationship Representation",
    )

    property_payloads = data["construct_properties"]

    if not isinstance(property_payloads, list):
        raise ReviewValidationError(
            "construct_properties must be a JSON array."
        )

    return ReviewRelationshipRepresentation(
        source_subject_key=data["source_subject_key"],
        target_subject_key=data["target_subject_key"],
        semantic_intent=data["semantic_intent"],
        sysml_v2_construct=data["sysml_v2_construct"],
        construct_properties=tuple(
            _parse_property(value)
            for value in property_payloads
        ),
        target_notation_profile_id=(
            data["target_notation_profile_id"]
        ),
        target_notation_profile_version=(
            data["target_notation_profile_version"]
        ),
        textual_notation_preview=(
            data["textual_notation_preview"]
        ),
        validation_status=data["validation_status"],
        validation_fingerprint=(
            data["validation_fingerprint"]
        ),
    )


def _relationship_payload(
    relationship: ReviewRelationshipRepresentation,
) -> dict[str, object]:
    return {
        "source_subject_key": (
            relationship.source_subject_key
        ),
        "target_subject_key": (
            relationship.target_subject_key
        ),
        "semantic_intent": relationship.semantic_intent,
        "sysml_v2_construct": (
            relationship.sysml_v2_construct
        ),
        "construct_properties": [
            {
                "name": item.name,
                "value": item.value,
            }
            for item in relationship.construct_properties
        ],
        "target_notation_profile_id": (
            relationship.target_notation_profile_id
        ),
        "target_notation_profile_version": (
            relationship.target_notation_profile_version
        ),
        "textual_notation_preview": (
            relationship.textual_notation_preview
        ),
        "validation_status": (
            relationship.validation_status
        ),
        "validation_fingerprint": (
            relationship.validation_fingerprint
        ),
    }


def _parse_property(payload: object) -> ReviewProperty:
    data = _exact_object(
        payload,
        expected_fields=_PROPERTY_FIELDS,
        label="Review Property",
    )

    return ReviewProperty(
        name=data["name"],
        value=data["value"],
    )


def _parse_dimension_selection(
    payload: object,
) -> ReviewDimensionSelection:
    data = _exact_object(
        payload,
        expected_fields=_DIMENSION_SELECTION_FIELDS,
        label="Review Dimension Selection",
    )

    selected_values = data["selected_values"]
    source_reference_ids = data["source_reference_ids"]

    if not isinstance(selected_values, list):
        raise ReviewValidationError(
            "selected_values must be a JSON array."
        )

    if not isinstance(source_reference_ids, list):
        raise ReviewValidationError(
            "source_reference_ids must be a JSON array."
        )

    return ReviewDimensionSelection(
        dimension=data["dimension"],
        selected_values=tuple(selected_values),
        value_origin=data["value_origin"],
        source_reference_ids=tuple(
            source_reference_ids
        ),
        rationale=data["rationale"],
        selected_by=data["selected_by"],
        selected_at=data["selected_at"],
    )


def _dimension_selection_payload(
    selection: ReviewDimensionSelection,
) -> dict[str, object]:
    return {
        "dimension": selection.dimension,
        "selected_values": list(
            selection.selected_values
        ),
        "value_origin": selection.value_origin,
        "source_reference_ids": list(
            selection.source_reference_ids
        ),
        "rationale": selection.rationale,
        "selected_by": selection.selected_by,
        "selected_at": selection.selected_at,
    }


def _parse_artifact_reference(
    payload: object,
) -> ProcessingArtifactReference:
    data = _exact_object(
        payload,
        expected_fields=_ARTIFACT_REFERENCE_FIELDS,
        label="Processing Artifact Reference",
    )

    try:
        return create_processing_artifact_reference(
            artifact_type=data["artifact_type"],
            artifact_id=data["artifact_id"],
            content_fingerprint=(
                data["content_fingerprint"]
            ),
            repository_relative_path=(
                data["repository_relative_path"]
            ),
        )
    except ProcessingValidationError as exc:
        raise ReviewValidationError(
            "Processing Artifact Reference is invalid."
        ) from exc


def _artifact_reference_payload(
    reference: ProcessingArtifactReference,
) -> dict[str, str]:
    return {
        "artifact_type": reference.artifact_type,
        "artifact_id": reference.artifact_id,
        "content_fingerprint": (
            reference.content_fingerprint
        ),
        "repository_relative_path": (
            reference.repository_relative_path
        ),
    }


def _validate_artifact_reference(
    reference: ProcessingArtifactReference,
    *,
    project_id: str,
    label: str,
) -> None:
    try:
        validate_processing_artifact_reference(reference)
    except ProcessingValidationError as exc:
        raise ReviewValidationError(
            f"{label} is invalid."
        ) from exc

    path = PurePosixPath(
        reference.repository_relative_path
    )

    if path.parts[:3] != (
        "data",
        "projects",
        project_id,
    ):
        raise ReviewIntegrityError(
            f"{label} must remain inside the selected Project."
        )


def _exact_object(
    value: object,
    *,
    expected_fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReviewValidationError(
            f"{label} must be a JSON object."
        )

    actual_fields = frozenset(value)

    if actual_fields != expected_fields:
        raise ReviewValidationError(
            f"{label} has invalid fields; "
            f"missing={sorted(expected_fields - actual_fields)}, "
            f"unknown={sorted(actual_fields - expected_fields)}."
        )

    return value


def _identifier(
    value: object,
    pattern: re.Pattern[str],
    label: str,
) -> str:
    selected = _text(value, label)

    if pattern.fullmatch(selected) is None:
        raise ReviewValidationError(
            f"{label} has invalid syntax."
        )

    return selected


def _sha256(value: object, label: str) -> str:
    return _identifier(
        value,
        _SHA256_PATTERN,
        label,
    )


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ReviewValidationError(
            f"{label} must be a non-empty string."
        )

    if value != value.strip():
        raise ReviewValidationError(
            f"{label} must not contain surrounding whitespace."
        )

    return value


def _optional_text(
    value: object,
    label: str,
) -> str | None:
    if value is None:
        return None

    return _text(value, label)


def _utc_timestamp(
    value: object,
    label: str,
) -> str:
    return _identifier(
        value,
        _UTC_TIMESTAMP_PATTERN,
        label,
    )


def _non_empty_unique_text_tuple(
    values: object,
    label: str,
) -> tuple[str, ...]:
    result = _unique_text_tuple(values, label)

    if not result:
        raise ReviewValidationError(
            f"{label} must not be empty."
        )

    return result


def _unique_text_tuple(
    values: object,
    label: str,
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ReviewValidationError(
            f"{label} must be a tuple."
        )

    for value in values:
        _text(value, label)

    if len(values) != len(set(values)):
        raise ReviewIntegrityError(
            f"{label} must contain unique values."
        )

    return values


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise ReviewValidationError(
                f"Duplicate JSON object key: {key!r}."
            )

        result[key] = value

    return result
