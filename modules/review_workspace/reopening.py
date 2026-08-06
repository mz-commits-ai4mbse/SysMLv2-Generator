"""Create one documented successor of a finalized review version."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import (
    InvalidReviewVersionTransitionError,
    ReviewIntegrityError,
    ReviewValidationError,
)
from .identifiers import (
    validate_review_document_version_id,
    validate_review_item_id,
    validate_review_revision_id,
)
from .item_manifest import create_review_item
from .revision_manifest import (
    create_review_revision,
    validate_review_revision,
)
from .types import (
    ReviewDocumentVersion,
    ReviewRevision,
)
from .version_manifest import (
    create_review_document_version,
    validate_review_document_version,
)


@dataclass(frozen=True, slots=True)
class ReopenedReviewVersionBundle:
    """One validated successor version and its initial revision."""

    predecessor_version_id: str
    predecessor_revision_id: str
    version: ReviewDocumentVersion
    initial_revision: ReviewRevision
    review_item_id_mapping: tuple[
        tuple[str, str],
        ...,
    ]


def create_reopened_review_version_bundle(
    predecessor_version: ReviewDocumentVersion,
    predecessor_revision: ReviewRevision,
    *,
    review_document_version_id: str,
    review_revision_id: str,
    review_item_ids: tuple[str, ...],
    reopen_reason: str,
    opened_by: str,
    timestamp: str,
) -> ReopenedReviewVersionBundle:
    """Create one deterministic draft successor version."""

    validate_review_document_version(
        predecessor_version
    )
    validate_review_revision(
        predecessor_revision
    )

    if predecessor_version.version_state != "finalized":
        raise InvalidReviewVersionTransitionError(
            "Only a finalized Review Document Version "
            "can be reopened."
        )

    if (
        predecessor_revision.project_id
        != predecessor_version.project_id
    ):
        raise ReviewIntegrityError(
            "Predecessor Review Revision project_id does "
            "not match the finalized predecessor version."
        )

    if (
        predecessor_revision.review_document_id
        != predecessor_version.review_document_id
    ):
        raise ReviewIntegrityError(
            "Predecessor Review Revision does not belong "
            "to the finalized predecessor Review Document."
        )

    if (
        predecessor_revision.review_document_version_id
        != predecessor_version.review_document_version_id
    ):
        raise ReviewIntegrityError(
            "Predecessor Review Revision does not belong "
            "to the finalized predecessor version."
        )

    if (
        predecessor_revision.review_revision_id
        != predecessor_version.finalized_revision_id
    ):
        raise ReviewIntegrityError(
            "Predecessor Review Revision is not the exact "
            "finalized revision of its version."
        )

    if (
        predecessor_revision.review_revision_id
        != predecessor_version.head_revision_id
    ):
        raise ReviewIntegrityError(
            "Finalized predecessor head does not match "
            "its predecessor Review Revision."
        )

    new_version_id = (
        validate_review_document_version_id(
            review_document_version_id
        )
    )
    new_revision_id = validate_review_revision_id(
        review_revision_id
    )

    if (
        new_version_id
        == predecessor_version
        .review_document_version_id
    ):
        raise ReviewIntegrityError(
            "A reopened Review Document Version requires "
            "a new version identity."
        )

    if (
        new_revision_id
        == predecessor_revision.review_revision_id
    ):
        raise ReviewIntegrityError(
            "A reopened Review Document Version requires "
            "a new initial Review Revision identity."
        )

    reason = _text(
        reopen_reason,
        "reopen_reason",
    )
    reviewer = _text(
        opened_by,
        "opened_by",
    )
    opened_at = _text(
        timestamp,
        "timestamp",
    )

    if not isinstance(review_item_ids, tuple):
        raise ReviewValidationError(
            "review_item_ids must be a tuple."
        )

    predecessor_items = (
        predecessor_revision.review_items
    )

    if len(review_item_ids) != len(
        predecessor_items
    ):
        raise ReviewIntegrityError(
            "Reopening requires exactly one new Review "
            "Item ID for every predecessor Review Item."
        )

    validated_item_ids = tuple(
        validate_review_item_id(value)
        for value in review_item_ids
    )

    if len(validated_item_ids) != len(
        set(validated_item_ids)
    ):
        raise ReviewIntegrityError(
            "Reopened Review Item IDs must be unique."
        )

    predecessor_item_ids = {
        item.review_item_id
        for item in predecessor_items
    }

    if predecessor_item_ids.intersection(
        validated_item_ids
    ):
        raise ReviewIntegrityError(
            "Reopened Review Item IDs must not reuse "
            "predecessor Review Item identities."
        )

    item_mapping = tuple(
        (
            predecessor_item.review_item_id,
            new_item_id,
        )
        for predecessor_item, new_item_id in zip(
            predecessor_items,
            validated_item_ids,
            strict=True,
        )
    )

    carried_items = tuple(
        create_review_item(
            project_id=predecessor_item.project_id,
            review_document_id=(
                predecessor_item.review_document_id
            ),
            review_document_version_id=(
                new_version_id
            ),
            review_item_id=new_item_id,
            review_item_kind=(
                predecessor_item.review_item_kind
            ),
            stable_subject_key=(
                predecessor_item.stable_subject_key
            ),
            section=predecessor_item.section,
            lineage_operation="carried_forward",
            derived_from_review_item_ids=(
                predecessor_item.review_item_id,
            ),
            original_report_locator=(
                predecessor_item
                .original_report_locator
            ),
            proposal_references=(
                predecessor_item.proposal_references
            ),
            source_evidence_references=(
                predecessor_item
                .source_evidence_references
            ),
            consensus_evidence_references=(
                predecessor_item
                .consensus_evidence_references
            ),
            current_content=(
                predecessor_item.current_content
            ),
            dimension_selections=(
                predecessor_item.dimension_selections
            ),
            effective_review_outcome=(
                predecessor_item
                .effective_review_outcome
            ),
        )
        for predecessor_item, new_item_id in zip(
            predecessor_items,
            validated_item_ids,
            strict=True,
        )
    )

    initial_revision = create_review_revision(
        project_id=predecessor_version.project_id,
        review_document_id=(
            predecessor_version.review_document_id
        ),
        review_document_version_id=new_version_id,
        review_revision_id=new_revision_id,
        revision_sequence=1,
        predecessor_revision_id=None,
        review_items=carried_items,
        scoped_review_action_ids=(),
        created_by=reviewer,
        timestamp=opened_at,
    )

    version = create_review_document_version(
        project_id=predecessor_version.project_id,
        review_document_id=(
            predecessor_version.review_document_id
        ),
        review_document_version_id=new_version_id,
        version_number=(
            predecessor_version.version_number + 1
        ),
        predecessor_version_id=(
            predecessor_version
            .review_document_version_id
        ),
        reopen_reason=reason,
        opened_by=reviewer,
        timestamp=opened_at,
        head_revision_id=new_revision_id,
    )

    bundle = ReopenedReviewVersionBundle(
        predecessor_version_id=(
            predecessor_version
            .review_document_version_id
        ),
        predecessor_revision_id=(
            predecessor_revision.review_revision_id
        ),
        version=version,
        initial_revision=initial_revision,
        review_item_id_mapping=item_mapping,
    )

    validate_reopened_review_version_bundle(
        bundle,
        predecessor_version=predecessor_version,
        predecessor_revision=predecessor_revision,
    )

    return bundle


def validate_reopened_review_version_bundle(
    bundle: ReopenedReviewVersionBundle,
    *,
    predecessor_version: ReviewDocumentVersion,
    predecessor_revision: ReviewRevision,
) -> None:
    """Validate one complete in-memory reopening result."""

    if not isinstance(
        bundle,
        ReopenedReviewVersionBundle,
    ):
        raise ReviewValidationError(
            "bundle must be a "
            "ReopenedReviewVersionBundle."
        )

    validate_review_document_version(
        predecessor_version
    )
    validate_review_revision(
        predecessor_revision
    )
    validate_review_document_version(
        bundle.version
    )
    validate_review_revision(
        bundle.initial_revision
    )

    version = bundle.version
    revision = bundle.initial_revision

    if (
        bundle.predecessor_version_id
        != predecessor_version
        .review_document_version_id
    ):
        raise ReviewIntegrityError(
            "Reopening bundle predecessor version "
            "binding is invalid."
        )

    if (
        bundle.predecessor_revision_id
        != predecessor_revision.review_revision_id
    ):
        raise ReviewIntegrityError(
            "Reopening bundle predecessor revision "
            "binding is invalid."
        )

    if version.version_state != "draft":
        raise ReviewIntegrityError(
            "A reopened Review Document Version must "
            "start in draft state."
        )

    if (
        version.predecessor_version_id
        != predecessor_version
        .review_document_version_id
    ):
        raise ReviewIntegrityError(
            "Reopened Review Document Version does not "
            "identify its exact predecessor."
        )

    if (
        version.version_number
        != predecessor_version.version_number + 1
    ):
        raise ReviewIntegrityError(
            "Reopened Review Document Version number "
            "must immediately follow its predecessor."
        )

    if (
        version.head_revision_id
        != revision.review_revision_id
    ):
        raise ReviewIntegrityError(
            "Reopened Review Document Version head does "
            "not identify its initial revision."
        )

    if revision.revision_sequence != 1:
        raise ReviewIntegrityError(
            "The initial reopened Review Revision must "
            "use revision_sequence 1."
        )

    if revision.predecessor_revision_id is not None:
        raise ReviewIntegrityError(
            "The first revision of a reopened version "
            "must not have a revision predecessor."
        )

    if revision.scoped_review_action_ids:
        raise ReviewIntegrityError(
            "The first revision of a reopened version "
            "must not copy Scoped Review Action IDs."
        )

    if (
        revision.project_id
        != version.project_id
        or revision.review_document_id
        != version.review_document_id
        or revision.review_document_version_id
        != version.review_document_version_id
    ):
        raise ReviewIntegrityError(
            "Reopened version and initial revision "
            "identity bindings are inconsistent."
        )

    expected_mapping = tuple(
        (
            old_item.review_item_id,
            new_item.review_item_id,
        )
        for old_item, new_item in zip(
            predecessor_revision.review_items,
            revision.review_items,
            strict=True,
        )
    )

    if bundle.review_item_id_mapping != expected_mapping:
        raise ReviewIntegrityError(
            "Reopening bundle Review Item identity "
            "mapping is invalid."
        )

    for predecessor_item, carried_item in zip(
        predecessor_revision.review_items,
        revision.review_items,
        strict=True,
    ):
        if (
            carried_item.lineage_operation
            != "carried_forward"
        ):
            raise ReviewIntegrityError(
                "Reopened Review Items must use "
                "carried_forward lineage."
            )

        if (
            carried_item
            .derived_from_review_item_ids
            != (
                predecessor_item.review_item_id,
            )
        ):
            raise ReviewIntegrityError(
                "Reopened Review Item does not identify "
                "its exact predecessor Review Item."
            )

        preserved_values = (
            (
                carried_item.stable_subject_key,
                predecessor_item.stable_subject_key,
                "stable_subject_key",
            ),
            (
                carried_item.review_item_kind,
                predecessor_item.review_item_kind,
                "review_item_kind",
            ),
            (
                carried_item.section,
                predecessor_item.section,
                "section",
            ),
            (
                carried_item.original_report_locator,
                predecessor_item
                .original_report_locator,
                "original_report_locator",
            ),
            (
                carried_item.proposal_references,
                predecessor_item.proposal_references,
                "proposal_references",
            ),
            (
                carried_item
                .source_evidence_references,
                predecessor_item
                .source_evidence_references,
                "source_evidence_references",
            ),
            (
                carried_item
                .consensus_evidence_references,
                predecessor_item
                .consensus_evidence_references,
                "consensus_evidence_references",
            ),
            (
                carried_item.current_content,
                predecessor_item.current_content,
                "current_content",
            ),
            (
                carried_item.dimension_selections,
                predecessor_item.dimension_selections,
                "dimension_selections",
            ),
            (
                carried_item
                .effective_review_outcome,
                predecessor_item
                .effective_review_outcome,
                "effective_review_outcome",
            ),
        )

        for actual, expected, label in (
            preserved_values
        ):
            if actual != expected:
                raise ReviewIntegrityError(
                    "Reopened Review Item does not "
                    f"preserve predecessor {label}."
                )


def _text(
    value: object,
    label: str,
) -> str:
    if not isinstance(value, str) or not value:
        raise ReviewValidationError(
            f"{label} must be a non-empty string."
        )

    if value != value.strip():
        raise ReviewValidationError(
            f"{label} must not contain surrounding "
            "whitespace."
        )

    return value
