"""Assemble one initial Review Document from exact P4 and P9 evidence."""

from __future__ import annotations

from dataclasses import dataclass

from modules.project_processing import (
    ProcessingArtifactReference,
)

from .document_manifest import (
    create_review_document,
)
from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
)
from .evidence_adapter import (
    P9ReviewEvidenceSet,
)
from .item_manifest import validate_review_item
from .p4_evidence_adapter import (
    P4ReviewEvidenceSet,
)
from .p4_evidence_reference_adapter import (
    P4StructuredEvidenceReferenceSet,
)
from .p4_review_item_builder import (
    P4InitialReviewItemSet,
    construct_initial_p4_review_items,
)
from .p9_evidence_reference_adapter import (
    P9StructuredEvidenceSet,
)
from .p9_proposal_adapter import (
    P9StructuredProposalSet,
)
from .p9_review_item_builder import (
    P9InitialReviewItemSet,
    construct_initial_p9_review_items,
)
from .revision_manifest import (
    create_review_revision,
)
from .types import (
    ReviewDocument,
    ReviewDocumentVersion,
    ReviewItem,
    ReviewRevision,
)
from .version_manifest import (
    create_review_document_version,
)


_SECTION_ORDER = {
    "elements": 0,
    "relationships": 1,
    "open_questions": 2,
}


@dataclass(frozen=True, slots=True)
class ReviewDocumentEligibilityAssessment:
    """Eligibility summary for one initial Review Document."""

    eligible_for_workspace_creation: bool
    included_review_item_ids: tuple[str, ...]
    p9_review_item_ids: tuple[str, ...]
    p4_review_item_ids: tuple[str, ...]
    potentially_promotable_review_item_ids: tuple[
        str,
        ...,
    ]
    non_promotable_review_item_ids: tuple[
        str,
        ...,
    ]
    relationship_resolution_required_item_ids: tuple[
        str,
        ...,
    ]
    promotion_ready_review_item_ids: tuple[
        str,
        ...,
    ]


@dataclass(frozen=True, slots=True)
class InitialReviewDocumentAssembly:
    """Complete non-persisted bundle for one initial Review Workspace."""

    review_document: ReviewDocument
    review_document_version: ReviewDocumentVersion
    initial_revision: ReviewRevision
    p9_review_items: P9InitialReviewItemSet
    p4_review_items: P4InitialReviewItemSet
    eligibility: ReviewDocumentEligibilityAssessment

    @property
    def repository_bundle(
        self,
    ) -> tuple[
        ReviewDocument,
        ReviewDocumentVersion,
        ReviewRevision,
    ]:
        """Return arguments for create_document_workspace()."""

        return (
            self.review_document,
            self.review_document_version,
            self.initial_revision,
        )


def assemble_initial_review_document(
    *,
    p9_review_evidence: object,
    p9_structured_proposals: object,
    p9_structured_evidence: object,
    p4_review_evidence: object,
    p4_evidence_references: object,
    review_document_id: str,
    review_document_version_id: str,
    review_revision_id: str,
    opened_by: str,
    timestamp: str,
) -> InitialReviewDocumentAssembly:
    """Construct one exact initial Review Document bundle.

    P9 remains the document anchor. P4 contributes independent
    Information Unit Review Items and exact supporting evidence.
    """

    _validate_input_types(
        p9_review_evidence=p9_review_evidence,
        p9_structured_proposals=(
            p9_structured_proposals
        ),
        p9_structured_evidence=(
            p9_structured_evidence
        ),
        p4_review_evidence=p4_review_evidence,
        p4_evidence_references=(
            p4_evidence_references
        ),
    )

    _validate_input_identities(
        p9_review_evidence,
        p9_structured_proposals,
        p9_structured_evidence,
        p4_review_evidence,
        p4_evidence_references,
    )

    p9_review_items = (
        construct_initial_p9_review_items(
            p9_structured_proposals,
            p9_structured_evidence,
            review_document_id=review_document_id,
            review_document_version_id=(
                review_document_version_id
            ),
        )
    )

    occupied_review_item_ids = tuple(
        item.review_item_id
        for item in p9_review_items.review_items
    )

    p4_review_items = (
        construct_initial_p4_review_items(
            p4_review_evidence,
            p4_evidence_references,
            review_document_id=review_document_id,
            review_document_version_id=(
                review_document_version_id
            ),
            occupied_review_item_ids=(
                occupied_review_item_ids
            ),
        )
    )

    combined_items = tuple(
        sorted(
            (
                *p9_review_items.review_items,
                *p4_review_items.review_items,
            ),
            key=_review_item_sort_key,
        )
    )

    if not combined_items:
        raise ReviewReferenceError(
            "An initial Review Document requires at "
            "least one eligible P4 or P9 Review Item."
        )

    _validate_combined_items(
        combined_items,
        p9_review_items=p9_review_items,
        p4_review_items=p4_review_items,
        project_id=p9_review_evidence.project_id,
        review_document_id=review_document_id,
        review_document_version_id=(
            review_document_version_id
        ),
    )

    (
        supporting_artifacts,
        p9_artifact_keys,
        p4_artifact_keys,
    ) = _construct_supporting_artifacts(
        p9_review_evidence,
        p4_evidence_references,
    )

    _validate_item_artifact_membership(
        p9_review_items=p9_review_items,
        p4_review_items=p4_review_items,
        p9_artifact_keys=p9_artifact_keys,
        p4_artifact_keys=p4_artifact_keys,
    )

    semantic_reference_versions = tuple(
        sorted(
            p9_review_evidence
            .semantic_reference_versions,
            key=lambda item: (
                item.reference_system_id,
                item.reference_version,
            ),
        )
    )

    review_document = create_review_document(
        project_id=p9_review_evidence.project_id,
        review_document_id=review_document_id,
        source_id=p9_review_evidence.source_id,
        source_sha256=(
            p9_review_evidence.source_sha256
        ),
        processing_run_id=(
            p9_review_evidence.processing_run_id
        ),
        attempt_id=p9_review_evidence.attempt_id,
        primary_review_artifact_reference=(
            p9_review_evidence
            .primary_review_artifact_reference
        ),
        supporting_artifact_references=(
            supporting_artifacts
        ),
        framework_template=(
            p9_review_evidence.framework_template
        ),
        semantic_reference_versions=(
            semantic_reference_versions
        ),
        timestamp=timestamp,
    )

    initial_revision = create_review_revision(
        project_id=p9_review_evidence.project_id,
        review_document_id=review_document_id,
        review_document_version_id=(
            review_document_version_id
        ),
        review_revision_id=review_revision_id,
        revision_sequence=1,
        predecessor_revision_id=None,
        review_items=combined_items,
        scoped_review_action_ids=(),
        created_by=opened_by,
        timestamp=timestamp,
    )

    review_document_version = (
        create_review_document_version(
            project_id=(
                p9_review_evidence.project_id
            ),
            review_document_id=(
                review_document_id
            ),
            review_document_version_id=(
                review_document_version_id
            ),
            version_number=1,
            predecessor_version_id=None,
            reopen_reason=None,
            opened_by=opened_by,
            timestamp=timestamp,
            head_revision_id=review_revision_id,
        )
    )

    eligibility = _assess_eligibility(
        combined_items,
        p9_review_items=p9_review_items,
        p4_review_items=p4_review_items,
    )

    return InitialReviewDocumentAssembly(
        review_document=review_document,
        review_document_version=(
            review_document_version
        ),
        initial_revision=initial_revision,
        p9_review_items=p9_review_items,
        p4_review_items=p4_review_items,
        eligibility=eligibility,
    )


def _validate_input_types(
    *,
    p9_review_evidence: object,
    p9_structured_proposals: object,
    p9_structured_evidence: object,
    p4_review_evidence: object,
    p4_evidence_references: object,
) -> None:
    if not isinstance(
        p9_review_evidence,
        P9ReviewEvidenceSet,
    ):
        raise ReviewValidationError(
            "p9_review_evidence must be a "
            "P9ReviewEvidenceSet."
        )

    if not isinstance(
        p9_structured_proposals,
        P9StructuredProposalSet,
    ):
        raise ReviewValidationError(
            "p9_structured_proposals must be a "
            "P9StructuredProposalSet."
        )

    if not isinstance(
        p9_structured_evidence,
        P9StructuredEvidenceSet,
    ):
        raise ReviewValidationError(
            "p9_structured_evidence must be a "
            "P9StructuredEvidenceSet."
        )

    if not isinstance(
        p4_review_evidence,
        P4ReviewEvidenceSet,
    ):
        raise ReviewValidationError(
            "p4_review_evidence must be a "
            "P4ReviewEvidenceSet."
        )

    if not isinstance(
        p4_evidence_references,
        P4StructuredEvidenceReferenceSet,
    ):
        raise ReviewValidationError(
            "p4_evidence_references must be a "
            "P4StructuredEvidenceReferenceSet."
        )


def _validate_input_identities(
    p9_review_evidence: P9ReviewEvidenceSet,
    p9_structured_proposals: P9StructuredProposalSet,
    p9_structured_evidence: P9StructuredEvidenceSet,
    p4_review_evidence: P4ReviewEvidenceSet,
    p4_evidence_references: (
        P4StructuredEvidenceReferenceSet
    ),
) -> None:
    for value, label in (
        (
            p9_structured_proposals,
            "p9_structured_proposals",
        ),
        (
            p9_structured_evidence,
            "p9_structured_evidence",
        ),
    ):
        for field_name in (
            "project_id",
            "source_id",
            "processing_run_id",
            "attempt_id",
        ):
            if getattr(
                value,
                field_name,
            ) != getattr(
                p9_review_evidence,
                field_name,
            ):
                raise ReviewIntegrityError(
                    f"{label} disagrees with "
                    "p9_review_evidence on "
                    f"{field_name}."
                )

    for value, label in (
        (
            p4_review_evidence,
            "p4_review_evidence",
        ),
        (
            p4_evidence_references,
            "p4_evidence_references",
        ),
    ):
        for field_name in (
            "project_id",
            "source_id",
        ):
            if getattr(
                value,
                field_name,
            ) != getattr(
                p9_review_evidence,
                field_name,
            ):
                raise ReviewIntegrityError(
                    f"{label} disagrees with "
                    "p9_review_evidence on "
                    f"{field_name}."
                )


def _validate_combined_items(
    items: tuple[ReviewItem, ...],
    *,
    p9_review_items: P9InitialReviewItemSet,
    p4_review_items: P4InitialReviewItemSet,
    project_id: str,
    review_document_id: str,
    review_document_version_id: str,
) -> None:
    item_ids: set[str] = set()
    subject_keys: set[str] = set()

    p9_ids = {
        item.review_item_id
        for item in p9_review_items.review_items
    }
    p4_ids = {
        item.review_item_id
        for item in p4_review_items.review_items
    }

    if p9_ids & p4_ids:
        raise ReviewIntegrityError(
            "P4 and P9 Review Item IDs must not collide."
        )

    for item in items:
        validate_review_item(item)

        if item.project_id != project_id:
            raise ReviewIntegrityError(
                "Review Item project_id does not "
                "match the assembled Review Document."
            )

        if (
            item.review_document_id
            != review_document_id
        ):
            raise ReviewIntegrityError(
                "Review Item review_document_id does not "
                "match the assembled Review Document."
            )

        if (
            item.review_document_version_id
            != review_document_version_id
        ):
            raise ReviewIntegrityError(
                "Review Item version identity does not "
                "match the assembled Review Document."
            )

        if item.effective_review_outcome != "open":
            raise ReviewIntegrityError(
                "Initial Review Document Items must "
                "remain open."
            )

        if item.review_item_id in item_ids:
            raise ReviewIntegrityError(
                "Review Item IDs must be unique."
            )

        if item.stable_subject_key in subject_keys:
            raise ReviewIntegrityError(
                "Review Item stable subject keys "
                "must be unique."
            )

        item_ids.add(item.review_item_id)
        subject_keys.add(item.stable_subject_key)

    for item in p9_review_items.review_items:
        if not item.proposal_references:
            raise ReviewIntegrityError(
                "Initial P9 Review Items require "
                "Agent Proposal References."
            )

        if item.stable_subject_key.startswith(
            "p4:"
        ):
            raise ReviewIntegrityError(
                "P9 Review Items must not use the "
                "P4 stable-subject namespace."
            )

    for item in p4_review_items.review_items:
        if item.proposal_references:
            raise ReviewIntegrityError(
                "Independent P4 Review Items must not "
                "contain P9 Agent Proposal References."
            )

        if item.consensus_evidence_references:
            raise ReviewIntegrityError(
                "Independent P4 Review Items must not "
                "contain P9 Consensus Evidence."
            )

        if not item.stable_subject_key.startswith(
            "p4:information_unit:"
        ):
            raise ReviewIntegrityError(
                "P4 Review Items must use the P4 "
                "Information Unit subject namespace."
            )


def _construct_supporting_artifacts(
    p9_review_evidence: P9ReviewEvidenceSet,
    p4_evidence_references: (
        P4StructuredEvidenceReferenceSet
    ),
) -> tuple[
    tuple[ProcessingArtifactReference, ...],
    frozenset[tuple[str, str, str, str]],
    frozenset[tuple[str, str, str, str]],
]:
    primary = (
        p9_review_evidence
        .primary_review_artifact_reference
    )
    primary_key = _artifact_reference_key(
        primary
    )
    primary_identity = _artifact_identity_key(
        primary
    )

    exact_keys: set[
        tuple[str, str, str, str]
    ] = {
        primary_key
    }
    identities: dict[
        tuple[str, str],
        tuple[str, str, str, str],
    ] = {
        primary_identity: primary_key
    }

    supporting: list[
        ProcessingArtifactReference
    ] = []
    p9_keys: set[
        tuple[str, str, str, str]
    ] = {
        primary_key
    }
    p4_keys: set[
        tuple[str, str, str, str]
    ] = set()

    p9_references = (
        p9_review_evidence.agent_output_references
        + p9_review_evidence
        .consensus_report_references
        + p9_review_evidence.run_summary_references
    )

    for reference in p9_references:
        _register_supporting_artifact(
            reference,
            supporting=supporting,
            exact_keys=exact_keys,
            identities=identities,
        )
        p9_keys.add(
            _artifact_reference_key(reference)
        )

    for record in (
        p4_evidence_references.records
    ):
        for evidence_reference in (
            record.all_evidence_references
        ):
            reference = (
                evidence_reference
                .artifact_reference
            )

            _register_supporting_artifact(
                reference,
                supporting=supporting,
                exact_keys=exact_keys,
                identities=identities,
            )
            p4_keys.add(
                _artifact_reference_key(reference)
            )

    return (
        tuple(
            sorted(
                supporting,
                key=_artifact_sort_key,
            )
        ),
        frozenset(p9_keys),
        frozenset(p4_keys),
    )


def _register_supporting_artifact(
    reference: ProcessingArtifactReference,
    *,
    supporting: list[
        ProcessingArtifactReference
    ],
    exact_keys: set[
        tuple[str, str, str, str]
    ],
    identities: dict[
        tuple[str, str],
        tuple[str, str, str, str],
    ],
) -> None:
    exact_key = _artifact_reference_key(
        reference
    )
    identity_key = _artifact_identity_key(
        reference
    )

    if exact_key in exact_keys:
        raise ReviewIntegrityError(
            "Review Document artifact references "
            "must not be duplicated."
        )

    existing_exact_key = identities.get(
        identity_key
    )

    if (
        existing_exact_key is not None
        and existing_exact_key != exact_key
    ):
        raise ReviewIntegrityError(
            "One artifact identity is associated "
            "with conflicting content or paths."
        )

    exact_keys.add(exact_key)
    identities[identity_key] = exact_key
    supporting.append(reference)


def _validate_item_artifact_membership(
    *,
    p9_review_items: P9InitialReviewItemSet,
    p4_review_items: P4InitialReviewItemSet,
    p9_artifact_keys: frozenset[
        tuple[str, str, str, str]
    ],
    p4_artifact_keys: frozenset[
        tuple[str, str, str, str]
    ],
) -> None:
    for item in p9_review_items.review_items:
        for reference in (
            _item_artifact_references(item)
        ):
            if (
                _artifact_reference_key(reference)
                not in p9_artifact_keys
            ):
                raise ReviewReferenceError(
                    "P9 Review Item references an "
                    "artifact outside the selected "
                    "P9 evidence set."
                )

    for item in p4_review_items.review_items:
        for reference in (
            _item_artifact_references(item)
        ):
            if (
                _artifact_reference_key(reference)
                not in p4_artifact_keys
            ):
                raise ReviewReferenceError(
                    "P4 Review Item references an "
                    "artifact outside the selected "
                    "P4 evidence set."
                )


def _item_artifact_references(
    item: ReviewItem,
) -> tuple[
    ProcessingArtifactReference,
    ...,
]:
    return tuple(
        (
            *(
                reference.artifact_reference
                for reference
                in item.proposal_references
            ),
            *(
                reference.artifact_reference
                for reference
                in item.source_evidence_references
            ),
            *(
                reference.artifact_reference
                for reference
                in item.consensus_evidence_references
            ),
        )
    )


def _assess_eligibility(
    items: tuple[ReviewItem, ...],
    *,
    p9_review_items: P9InitialReviewItemSet,
    p4_review_items: P4InitialReviewItemSet,
) -> ReviewDocumentEligibilityAssessment:
    potentially_promotable: list[str] = []
    non_promotable: list[str] = []
    relationship_resolution_required: list[
        str
    ] = []

    for item in items:
        if item.review_item_kind == "open_question":
            non_promotable.append(
                item.review_item_id
            )
            continue

        potentially_promotable.append(
            item.review_item_id
        )

        if item.review_item_kind == "relationship":
            representation = (
                item.current_content
                .relationship_representation
            )

            if (
                representation is None
                or representation.validation_status
                != "valid"
            ):
                relationship_resolution_required.append(
                    item.review_item_id
                )

    return ReviewDocumentEligibilityAssessment(
        eligible_for_workspace_creation=True,
        included_review_item_ids=tuple(
            sorted(
                item.review_item_id
                for item in items
            )
        ),
        p9_review_item_ids=tuple(
            sorted(
                item.review_item_id
                for item
                in p9_review_items.review_items
            )
        ),
        p4_review_item_ids=tuple(
            sorted(
                item.review_item_id
                for item
                in p4_review_items.review_items
            )
        ),
        potentially_promotable_review_item_ids=tuple(
            sorted(potentially_promotable)
        ),
        non_promotable_review_item_ids=tuple(
            sorted(non_promotable)
        ),
        relationship_resolution_required_item_ids=tuple(
            sorted(
                relationship_resolution_required
            )
        ),
        promotion_ready_review_item_ids=(),
    )


def _review_item_sort_key(
    item: ReviewItem,
) -> tuple[int, str, str]:
    return (
        _SECTION_ORDER[item.section],
        item.stable_subject_key,
        item.review_item_id,
    )


def _artifact_sort_key(
    reference: ProcessingArtifactReference,
) -> tuple[str, str, str, str]:
    return _artifact_reference_key(reference)


def _artifact_reference_key(
    reference: ProcessingArtifactReference,
) -> tuple[str, str, str, str]:
    return (
        reference.artifact_type,
        reference.artifact_id,
        reference.content_fingerprint,
        reference.repository_relative_path,
    )


def _artifact_identity_key(
    reference: ProcessingArtifactReference,
) -> tuple[str, str]:
    return (
        reference.artifact_type,
        reference.artifact_id,
    )
