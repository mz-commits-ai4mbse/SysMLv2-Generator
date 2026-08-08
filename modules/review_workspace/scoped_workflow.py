"""G6 scoped filtering, impact preview and immutable action application."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json

from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
    StaleReviewRevisionError,
)
from .item_manifest import create_review_item
from .proposal_detail import ReviewProposalDetail
from .revision_manifest import create_review_revision
from .scoped_action_manifest import create_scoped_review_action
from .types import (
    MaterializedReviewItemReference,
    ReviewDimensionSelection,
    ReviewItem,
    ReviewRevision,
    ScopedReviewAction,
)


SCOPED_ACTION_DECISION_DIMENSIONS = frozenset(
    {
        "classification",
        "framework_assignment",
        "terminology_assignment",
        "source_assignment",
        "review_outcome",
    }
)

SCOPED_REVIEW_OUTCOMES = frozenset(
    {
        "open",
        "rejected",
        "deferred",
        "out_of_scope",
        "unresolved",
    }
)

_PRECEDENCE = {
    "agent_proposal": 0,
    "document_default": 1,
    "filtered_set": 2,
    "explicit_selection": 2,
    "item_override": 3,
}

_DISAGREEMENT_LEVELS = frozenset(
    {
        "majority_with_disagreement",
        "minority_interpretation",
        "conflict",
    }
)


@dataclass(frozen=True, slots=True)
class ReviewConsensusFilterFact:
    """Exact consensus fact reconstructed from one immutable evidence fragment."""

    artifact_id: str
    evidence_locator: str
    evidence_content_fingerprint: str
    agreement_level: str
    review_required: bool


@dataclass(frozen=True, slots=True)
class ReviewItemFilterFact:
    """Filterable exact facts for one current Review Item."""

    review_item_id: str
    item_content_fingerprint: str
    review_status: str
    review_item_kind: str
    proposed_classifications: tuple[str, ...]
    effective_classifications: tuple[str, ...]
    proposed_framework_assignments: tuple[str, ...]
    effective_framework_assignments: tuple[str, ...]
    agent_identities: tuple[str, ...]
    confidence_levels: tuple[str, ...]
    consensus_states: tuple[str, ...]
    agent_disagreement_state: str
    human_modification_state: str
    source_identities: tuple[str, ...]
    evidence_sufficiency_state: str
    relationship_validation_status: str


@dataclass(frozen=True, slots=True)
class ReviewFilterSpec:
    """Conjunctive filter; values within one field are OR alternatives."""

    review_status: tuple[str, ...] = ()
    review_item_kind: tuple[str, ...] = ()
    proposed_classification: tuple[str, ...] = ()
    effective_classification: tuple[str, ...] = ()
    proposed_framework_assignment: tuple[str, ...] = ()
    effective_framework_assignment: tuple[str, ...] = ()
    agent_identity: tuple[str, ...] = ()
    confidence: tuple[str, ...] = ()
    consensus_state: tuple[str, ...] = ()
    agent_disagreement: tuple[str, ...] = ()
    human_modification_state: tuple[str, ...] = ()
    source_identity: tuple[str, ...] = ()
    evidence_sufficiency: tuple[str, ...] = ()
    relationship_validation_status: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ScopedReviewActionRequest:
    """One G6 scoped action request against an exact Review Revision."""

    expected_revision_id: str
    action_scope: str
    decision_dimension: str
    selected_values: tuple[str, ...]
    filter_spec: ReviewFilterSpec | None = None
    explicit_review_item_ids: tuple[str, ...] = ()
    rationale: str | None = None
    confirm_higher_precedence_overwrite: bool = False
    confirm_bulk_rejection: bool = False


@dataclass(frozen=True, slots=True)
class ScopedReviewActionImpactPreview:
    """Exact impact preview shown before one scoped action is persisted."""

    review_revision_id: str
    action_scope: str
    decision_dimension: str
    selected_values: tuple[str, ...]
    filter_definition: str | None
    matched_items: tuple[MaterializedReviewItemReference, ...]
    affected_review_item_ids: tuple[str, ...]
    item_override_review_item_ids: tuple[str, ...]
    higher_precedence_review_item_ids: tuple[str, ...]
    excluded_review_item_ids: tuple[str, ...]
    would_overwrite_review_item_ids: tuple[str, ...]
    requires_bulk_rejection_confirmation: bool

    @property
    def matched_count(self) -> int:
        return len(self.matched_items)

    @property
    def affected_count(self) -> int:
        return len(self.affected_review_item_ids)

    @property
    def item_override_count(self) -> int:
        return len(self.item_override_review_item_ids)

    @property
    def excluded_count(self) -> int:
        return len(self.excluded_review_item_ids)

    @property
    def overwrite_count(self) -> int:
        return len(self.would_overwrite_review_item_ids)


@dataclass(frozen=True, slots=True)
class ScopedReviewActionMutation:
    """One immutable Scoped Review Action plus its successor Revision."""

    action: ScopedReviewAction
    revision: ReviewRevision
    preview: ScopedReviewActionImpactPreview


def build_review_item_filter_fact(
    item: ReviewItem,
    *,
    proposal_details: tuple[ReviewProposalDetail, ...],
    source_id: str,
    consensus_facts: tuple[ReviewConsensusFilterFact, ...] = (),
) -> ReviewItemFilterFact:
    """Build all ADR-required filter dimensions without inventing evidence."""

    if not isinstance(item, ReviewItem):
        raise ReviewValidationError(
            "item must be a ReviewItem."
        )

    details = tuple(proposal_details)

    proposed_classifications = {
        detail.proposed_information_type
        for detail in details
        if detail.proposed_information_type
    }
    proposed_framework = {
        value
        for detail in details
        for value in detail.framework_assignment_values
    }

    for selection in item.dimension_selections:
        if selection.value_origin != "agent_proposal":
            continue
        if selection.dimension == "classification":
            proposed_classifications.update(
                selection.selected_values
            )
        elif selection.dimension == "framework_assignment":
            proposed_framework.update(
                selection.selected_values
            )

    effective_classifications = tuple(
        value
        for value in (
            item.current_content.information_type,
            item.current_content.modality,
            item.current_content.epistemic_status,
        )
        if value is not None
    )

    effective_framework = _selection_values(
        item,
        "framework_assignment",
    )

    agent_ids = tuple(
        sorted(
            {
                reference.agent_id
                for reference in item.proposal_references
            }
        )
    )
    confidence = tuple(
        sorted(
            {
                detail.confidence
                for detail in details
                if detail.confidence
            }
        )
    )

    consensus_states = tuple(
        sorted(
            {
                fact.agreement_level
                for fact in consensus_facts
            }
        )
    )
    if consensus_states:
        disagreement = (
            "present"
            if any(
                state in _DISAGREEMENT_LEVELS
                for state in consensus_states
            )
            else "absent"
        )
    else:
        consensus_states = ("not_available",)
        disagreement = "not_available"

    modification = (
        "modified"
        if (
            item.lineage_operation
            in {"split", "merge", "human_created"}
            or any(
                selection.value_origin != "agent_proposal"
                for selection in item.dimension_selections
            )
        )
        else "unmodified"
    )

    readiness_values = tuple(
        detail.generation_readiness
        for detail in details
        if detail.generation_readiness is not None
    )
    has_missing = any(
        detail.missing_evidence
        for detail in details
    )

    if not details or not readiness_values:
        evidence_sufficiency = "not_assessed"
    elif (
        not has_missing
        and all(
            value == "ready"
            for value in readiness_values
        )
    ):
        evidence_sufficiency = "sufficient"
    else:
        evidence_sufficiency = "insufficient"

    relationship = (
        item.current_content.relationship_representation
    )
    relationship_status = (
        "not_applicable"
        if relationship is None
        else relationship.validation_status
    )

    return ReviewItemFilterFact(
        review_item_id=item.review_item_id,
        item_content_fingerprint=(
            item.item_content_fingerprint
        ),
        review_status=item.effective_review_outcome,
        review_item_kind=item.review_item_kind,
        proposed_classifications=tuple(
            sorted(proposed_classifications)
        ),
        effective_classifications=tuple(
            sorted(set(effective_classifications))
        ),
        proposed_framework_assignments=tuple(
            sorted(proposed_framework)
        ),
        effective_framework_assignments=tuple(
            sorted(set(effective_framework))
        ),
        agent_identities=agent_ids,
        confidence_levels=confidence,
        consensus_states=consensus_states,
        agent_disagreement_state=disagreement,
        human_modification_state=modification,
        source_identities=(source_id,),
        evidence_sufficiency_state=(
            evidence_sufficiency
        ),
        relationship_validation_status=(
            relationship_status
        ),
    )


def filter_review_items(
    revision: ReviewRevision,
    facts: tuple[ReviewItemFilterFact, ...],
    spec: ReviewFilterSpec,
) -> tuple[MaterializedReviewItemReference, ...]:
    """Materialize one filter to exact current IDs and fingerprints."""

    _validate_fact_binding(revision, facts)
    _validate_filter_spec(spec)

    fact_by_id = {
        fact.review_item_id: fact
        for fact in facts
    }

    selected = []
    for item in revision.review_items:
        fact = fact_by_id[item.review_item_id]
        if _matches(spec, fact):
            selected.append(
                MaterializedReviewItemReference(
                    review_item_id=item.review_item_id,
                    item_content_fingerprint=(
                        item.item_content_fingerprint
                    ),
                )
            )

    return tuple(selected)


def review_filter_definition(
    spec: ReviewFilterSpec,
) -> str:
    """Return deterministic human-visible/persisted JSON filter definition."""

    _validate_filter_spec(spec)
    payload = {
        name: list(getattr(spec, name))
        for name in _FILTER_FIELDS
        if getattr(spec, name)
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def preview_scoped_review_action(
    revision: ReviewRevision,
    facts: tuple[ReviewItemFilterFact, ...],
    request: ScopedReviewActionRequest,
) -> ScopedReviewActionImpactPreview:
    """Preview exact scope and precedence before a scoped write."""

    _validate_request(request)

    if revision.review_revision_id != request.expected_revision_id:
        raise StaleReviewRevisionError(
            "The scoped action does not target the current Review Revision."
        )

    _validate_fact_binding(revision, facts)

    if request.action_scope == "document_default":
        matched = tuple(
            MaterializedReviewItemReference(
                review_item_id=item.review_item_id,
                item_content_fingerprint=(
                    item.item_content_fingerprint
                ),
            )
            for item in revision.review_items
        )
        filter_definition = None

    elif request.action_scope == "filtered_set":
        assert request.filter_spec is not None
        matched = filter_review_items(
            revision,
            facts,
            request.filter_spec,
        )
        if not matched:
            raise ReviewReferenceError(
                "The current filter materializes no Review Items."
            )
        filter_definition = review_filter_definition(
            request.filter_spec
        )

    else:
        ids = request.explicit_review_item_ids
        by_id = {
            item.review_item_id: item
            for item in revision.review_items
        }
        unknown = tuple(
            item_id
            for item_id in ids
            if item_id not in by_id
        )
        if unknown:
            raise ReviewReferenceError(
                "The explicit selection references unavailable Review Items."
            )
        matched = tuple(
            MaterializedReviewItemReference(
                review_item_id=item_id,
                item_content_fingerprint=(
                    by_id[item_id].item_content_fingerprint
                ),
            )
            for item_id in ids
        )
        filter_definition = None

    incoming_rank = _incoming_rank(
        request.action_scope
    )
    by_id = {
        item.review_item_id: item
        for item in revision.review_items
    }

    item_overrides = []
    higher = []

    for reference in matched:
        item = by_id[reference.review_item_id]
        origin = _dimension_origin(
            item,
            request.decision_dimension,
        )

        if origin == "item_override":
            item_overrides.append(
                item.review_item_id
            )

        if (
            origin is not None
            and _PRECEDENCE[origin] > incoming_rank
        ):
            higher.append(
                item.review_item_id
            )

    higher_tuple = tuple(higher)
    excluded = (
        ()
        if request.confirm_higher_precedence_overwrite
        else higher_tuple
    )
    affected = tuple(
        reference.review_item_id
        for reference in matched
        if reference.review_item_id not in excluded
    )

    bulk_rejection = (
        request.decision_dimension == "review_outcome"
        and request.selected_values == ("rejected",)
        and len(matched) > 1
    )

    return ScopedReviewActionImpactPreview(
        review_revision_id=revision.review_revision_id,
        action_scope=request.action_scope,
        decision_dimension=request.decision_dimension,
        selected_values=request.selected_values,
        filter_definition=filter_definition,
        matched_items=matched,
        affected_review_item_ids=affected,
        item_override_review_item_ids=tuple(
            item_overrides
        ),
        higher_precedence_review_item_ids=(
            higher_tuple
        ),
        excluded_review_item_ids=excluded,
        would_overwrite_review_item_ids=(
            higher_tuple
        ),
        requires_bulk_rejection_confirmation=(
            bulk_rejection
        ),
    )


def create_scoped_review_action_mutation(
    revision: ReviewRevision,
    *,
    facts: tuple[ReviewItemFilterFact, ...],
    request: ScopedReviewActionRequest,
    scoped_review_action_id: str,
    new_review_revision_id: str,
    actor_identity: str,
    timestamp: str,
) -> ScopedReviewActionMutation:
    """Create one immutable action and its materialized successor Revision."""

    preview = preview_scoped_review_action(
        revision,
        facts,
        request,
    )

    if (
        preview.requires_bulk_rejection_confirmation
        and not request.confirm_bulk_rejection
    ):
        raise ReviewIntegrityError(
            "Bulk rejection requires explicit confirmation after impact preview."
        )

    if (
        request.decision_dimension == "review_outcome"
        and request.selected_values == ("rejected",)
        and request.rationale is None
    ):
        raise ReviewIntegrityError(
            "Rejecting Review Items requires a rationale."
        )

    actor = _text(actor_identity, "actor_identity")
    _text(timestamp, "timestamp")

    action = create_scoped_review_action(
        project_id=revision.project_id,
        review_document_id=revision.review_document_id,
        review_document_version_id=(
            revision.review_document_version_id
        ),
        scoped_review_action_id=(
            scoped_review_action_id
        ),
        action_scope=request.action_scope,
        decision_dimension=request.decision_dimension,
        selected_values=request.selected_values,
        filter_definition=preview.filter_definition,
        materialized_items=(
            ()
            if request.action_scope == "document_default"
            else preview.matched_items
        ),
        created_by=actor,
        timestamp=timestamp,
        rationale=request.rationale,
    )

    affected = set(
        preview.affected_review_item_ids
    )
    updated_items = tuple(
        _apply_dimension(
            item,
            request=request,
            action_id=scoped_review_action_id,
            actor_identity=actor,
            timestamp=timestamp,
        )
        if item.review_item_id in affected
        else item
        for item in revision.review_items
    )

    successor = create_review_revision(
        project_id=revision.project_id,
        review_document_id=revision.review_document_id,
        review_document_version_id=(
            revision.review_document_version_id
        ),
        review_revision_id=new_review_revision_id,
        revision_sequence=revision.revision_sequence + 1,
        predecessor_revision_id=revision.review_revision_id,
        review_items=updated_items,
        scoped_review_action_ids=(
            *revision.scoped_review_action_ids,
            scoped_review_action_id,
        ),
        created_by=actor,
        timestamp=timestamp,
    )

    return ScopedReviewActionMutation(
        action=action,
        revision=successor,
        preview=preview,
    )


_FILTER_FIELDS = (
    "review_status",
    "review_item_kind",
    "proposed_classification",
    "effective_classification",
    "proposed_framework_assignment",
    "effective_framework_assignment",
    "agent_identity",
    "confidence",
    "consensus_state",
    "agent_disagreement",
    "human_modification_state",
    "source_identity",
    "evidence_sufficiency",
    "relationship_validation_status",
)


def _validate_filter_spec(
    spec: ReviewFilterSpec,
) -> None:
    if not isinstance(spec, ReviewFilterSpec):
        raise ReviewValidationError(
            "filter spec must be a ReviewFilterSpec."
        )

    for field in _FILTER_FIELDS:
        _string_tuple(
            getattr(spec, field),
            field,
            allow_empty=True,
        )


def _validate_request(
    request: ScopedReviewActionRequest,
) -> None:
    if not isinstance(request, ScopedReviewActionRequest):
        raise ReviewValidationError(
            "request must be a ScopedReviewActionRequest."
        )

    _text(
        request.expected_revision_id,
        "expected_revision_id",
    )

    if request.action_scope not in {
        "document_default",
        "filtered_set",
        "explicit_selection",
    }:
        raise ReviewValidationError(
            "Unsupported scoped Review action scope."
        )

    if (
        request.decision_dimension
        not in SCOPED_ACTION_DECISION_DIMENSIONS
    ):
        raise ReviewValidationError(
            "This Review dimension is not safe for scoped bulk application."
        )

    _string_tuple(
        request.selected_values,
        "selected_values",
        allow_empty=False,
    )

    if request.decision_dimension == "review_outcome":
        if (
            len(request.selected_values) != 1
            or request.selected_values[0]
            not in SCOPED_REVIEW_OUTCOMES
        ):
            raise ReviewValidationError(
                "Scoped review_outcome requires one supported non-approval "
                "outcome."
            )

    if request.decision_dimension == "classification":
        _parse_classification_values(
            request.selected_values
        )

    if request.action_scope == "document_default":
        if request.filter_spec is not None:
            raise ReviewIntegrityError(
                "document_default must not contain a filter."
            )
        if request.explicit_review_item_ids:
            raise ReviewIntegrityError(
                "document_default must not contain explicit Review Item IDs."
            )
        if request.decision_dimension == "review_outcome":
            raise ReviewIntegrityError(
                "document_default must not set review_outcome."
            )

    elif request.action_scope == "filtered_set":
        if request.filter_spec is None:
            raise ReviewIntegrityError(
                "filtered_set requires an explicit ReviewFilterSpec."
            )
        if request.explicit_review_item_ids:
            raise ReviewIntegrityError(
                "filtered_set must not contain explicit Review Item IDs."
            )

    else:
        if request.filter_spec is not None:
            raise ReviewIntegrityError(
                "explicit_selection must not contain a filter."
            )
        _string_tuple(
            request.explicit_review_item_ids,
            "explicit_review_item_ids",
            allow_empty=False,
        )

    if request.rationale is not None:
        _text(request.rationale, "rationale")


def _validate_fact_binding(
    revision: ReviewRevision,
    facts: tuple[ReviewItemFilterFact, ...],
) -> None:
    if not isinstance(facts, tuple):
        raise ReviewValidationError(
            "facts must be a tuple."
        )

    expected = {
        item.review_item_id: item.item_content_fingerprint
        for item in revision.review_items
    }
    actual = {
        fact.review_item_id: fact.item_content_fingerprint
        for fact in facts
    }

    if (
        len(actual) != len(facts)
        or actual != expected
    ):
        raise ReviewIntegrityError(
            "Review filter facts do not bind the exact current Review Revision."
        )


def _matches(
    spec: ReviewFilterSpec,
    fact: ReviewItemFilterFact,
) -> bool:
    fields = (
        (
            spec.review_status,
            (fact.review_status,),
        ),
        (
            spec.review_item_kind,
            (fact.review_item_kind,),
        ),
        (
            spec.proposed_classification,
            fact.proposed_classifications,
        ),
        (
            spec.effective_classification,
            fact.effective_classifications,
        ),
        (
            spec.proposed_framework_assignment,
            fact.proposed_framework_assignments,
        ),
        (
            spec.effective_framework_assignment,
            fact.effective_framework_assignments,
        ),
        (
            spec.agent_identity,
            fact.agent_identities,
        ),
        (
            spec.confidence,
            fact.confidence_levels,
        ),
        (
            spec.consensus_state,
            fact.consensus_states,
        ),
        (
            spec.agent_disagreement,
            (fact.agent_disagreement_state,),
        ),
        (
            spec.human_modification_state,
            (fact.human_modification_state,),
        ),
        (
            spec.source_identity,
            fact.source_identities,
        ),
        (
            spec.evidence_sufficiency,
            (fact.evidence_sufficiency_state,),
        ),
        (
            spec.relationship_validation_status,
            (fact.relationship_validation_status,),
        ),
    )

    return all(
        not requested
        or bool(
            set(requested).intersection(values)
        )
        for requested, values in fields
    )


def _selection_values(
    item: ReviewItem,
    dimension: str,
) -> tuple[str, ...]:
    matches = tuple(
        selection
        for selection in item.dimension_selections
        if selection.dimension == dimension
    )
    if not matches:
        return ()
    if len(matches) != 1:
        raise ReviewIntegrityError(
            "Review Item contains duplicate dimension selections."
        )
    return matches[0].selected_values


def _dimension_origin(
    item: ReviewItem,
    dimension: str,
) -> str | None:
    matches = tuple(
        selection
        for selection in item.dimension_selections
        if selection.dimension == dimension
    )
    if not matches:
        return None
    if len(matches) != 1:
        raise ReviewIntegrityError(
            "Review Item contains duplicate dimension selections."
        )
    origin = matches[0].value_origin
    if origin not in _PRECEDENCE:
        raise ReviewIntegrityError(
            "Review Item contains an unsupported effective value origin."
        )
    return origin


def _incoming_rank(
    action_scope: str,
) -> int:
    return _PRECEDENCE[action_scope]


def _apply_dimension(
    item: ReviewItem,
    *,
    request: ScopedReviewActionRequest,
    action_id: str,
    actor_identity: str,
    timestamp: str,
) -> ReviewItem:
    selections = {
        selection.dimension: selection
        for selection in item.dimension_selections
    }

    values = request.selected_values
    dimension = request.decision_dimension
    content = item.current_content
    proposals = item.proposal_references
    outcome = item.effective_review_outcome

    if dimension == "classification":
        updates = _parse_classification_values(
            values
        )
        content = replace(
            content,
            information_type=updates.get(
                "information_type",
                content.information_type,
            ),
            modality=updates.get(
                "modality",
                content.modality,
            ),
            epistemic_status=updates.get(
                "epistemic_status",
                content.epistemic_status,
            ),
        )

    elif dimension == "review_outcome":
        outcome = values[0]
        proposals = tuple(
            replace(
                reference,
                review_state=(
                    "rejected"
                    if outcome == "rejected"
                    else "available"
                ),
            )
            for reference in proposals
        )

    selections[dimension] = (
        ReviewDimensionSelection(
            dimension=dimension,
            selected_values=values,
            value_origin=request.action_scope,
            source_reference_ids=(action_id,),
            rationale=request.rationale,
            selected_by=actor_identity,
            selected_at=timestamp,
        )
    )

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
        proposal_references=proposals,
        source_evidence_references=(
            item.source_evidence_references
        ),
        consensus_evidence_references=(
            item.consensus_evidence_references
        ),
        current_content=content,
        dimension_selections=tuple(
            selections[key]
            for key in sorted(selections)
        ),
        effective_review_outcome=outcome,
    )


def _parse_classification_values(
    values: tuple[str, ...],
) -> dict[str, str | None]:
    allowed = {
        "information_type",
        "modality",
        "epistemic_status",
    }
    result: dict[str, str | None] = {}

    for entry in values:
        if "=" not in entry:
            raise ReviewValidationError(
                "Classification values must use field=value."
            )
        field, value = entry.split("=", 1)
        if field not in allowed or field in result:
            raise ReviewValidationError(
                "Classification fields must be unique supported fields."
            )
        if value == "<none>":
            result[field] = None
        else:
            result[field] = _text(
                value,
                f"classification {field}",
            )

    if not result:
        raise ReviewValidationError(
            "Classification action requires at least one field."
        )

    return result


def _string_tuple(
    values: object,
    label: str,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ReviewValidationError(
            f"{label} must be a tuple."
        )
    if not allow_empty and not values:
        raise ReviewValidationError(
            f"{label} must not be empty."
        )

    result = tuple(
        _text(value, f"{label} entry")
        for value in values
    )

    if len(result) != len(set(result)):
        raise ReviewIntegrityError(
            f"{label} entries must be unique."
        )

    return result


def _text(
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
            f"{label} must be non-empty single-line text without "
            "surrounding whitespace."
        )
    return selected
