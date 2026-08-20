"""Construct initial open Review Items from structured P9 proposals."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import re

from modules.project_workspace.identifiers import (
    is_valid_project_id,
)

from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
)
from .identifiers import (
    next_review_item_id,
    validate_review_document_id,
    validate_review_document_version_id,
    validate_review_item_id,
)
from .item_manifest import create_review_item
from .p9_evidence_reference_adapter import (
    CONSENSUS_EVIDENCE_ROLE,
    SOURCE_EVIDENCE_ROLE,
    P9StructuredEvidenceSet,
    P9SubjectEvidence,
)
from .p9_proposal_adapter import (
    P9ElementProposal,
    P9RelationshipProposal,
    P9ReviewQuestionProposal,
    P9StructuredProposalSet,
    create_element_stable_subject_key,
    create_relationship_stable_subject_key,
)
from .types import (
    ReviewDimensionSelection,
    ReviewEvidenceReference,
    ReviewItem,
    ReviewItemContent,
    ReviewProposalReference,
    ReviewRelationshipRepresentation,
)


DEFAULT_TARGET_NOTATION_PROFILE_ID = (
    "SYSML_V2_TARGET"
)
DEFAULT_TARGET_NOTATION_PROFILE_VERSION = "1.0.0"

_INITIAL_DRAFT_RATIONALE = (
    "Deterministic initial draft from one Agent proposal; "
    "no human selection has occurred."
)

_PROFILE_ID_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9_]*$"
)
_SEMANTIC_VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+$"
)


@dataclass(frozen=True, slots=True)
class P9InitialReviewItemSet:
    """Initial open Review Items constructed from one P9 attempt."""

    project_id: str
    source_id: str
    processing_run_id: str
    attempt_id: str
    review_document_id: str
    review_document_version_id: str
    review_items: tuple[ReviewItem, ...]

    @property
    def element_items(
        self,
    ) -> tuple[ReviewItem, ...]:
        """Return all initial element Review Items."""

        return tuple(
            item
            for item in self.review_items
            if item.review_item_kind == "element"
        )

    @property
    def relationship_items(
        self,
    ) -> tuple[ReviewItem, ...]:
        """Return all initial relationship Review Items."""

        return tuple(
            item
            for item in self.review_items
            if item.review_item_kind
            == "relationship"
        )

    @property
    def open_question_items(
        self,
    ) -> tuple[ReviewItem, ...]:
        """Return all initial Open Question Review Items."""

        return tuple(
            item
            for item in self.review_items
            if item.review_item_kind
            == "open_question"
        )

    def item_for_subject(
        self,
        stable_subject_key: str,
    ) -> ReviewItem:
        """Return the unique Review Item for one stable subject."""

        matches = tuple(
            item
            for item in self.review_items
            if item.stable_subject_key
            == stable_subject_key
        )

        if not matches:
            raise ReviewReferenceError(
                "No initial P9 Review Item exists for "
                f"stable subject {stable_subject_key!r}."
            )

        if len(matches) != 1:
            raise ReviewIntegrityError(
                "Initial P9 Review Item subjects "
                "must be unique."
            )

        return matches[0]


def construct_initial_p9_review_items(
    structured_proposals: object,
    structured_evidence: object,
    *,
    review_document_id: str,
    review_document_version_id: str,
    occupied_review_item_ids: Iterable[str] = (),
    target_notation_profile_id: str = (
        DEFAULT_TARGET_NOTATION_PROFILE_ID
    ),
    target_notation_profile_version: str = (
        DEFAULT_TARGET_NOTATION_PROFILE_VERSION
    ),
) -> P9InitialReviewItemSet:
    """Construct deterministic, open and non-persisted P9 Review Items."""

    if not isinstance(
        structured_proposals,
        P9StructuredProposalSet,
    ):
        raise ReviewValidationError(
            "structured_proposals must be a "
            "P9StructuredProposalSet."
        )

    if not isinstance(
        structured_evidence,
        P9StructuredEvidenceSet,
    ):
        raise ReviewValidationError(
            "structured_evidence must be a "
            "P9StructuredEvidenceSet."
        )

    if not is_valid_project_id(
        structured_proposals.project_id
    ):
        raise ReviewValidationError(
            "P9 proposal project_id must be a valid "
            "six-digit Project ID."
        )

    validate_review_document_id(
        review_document_id
    )
    validate_review_document_version_id(
        review_document_version_id
    )

    _validate_target_notation_profile(
        target_notation_profile_id,
        target_notation_profile_version,
    )
    _validate_input_identity(
        structured_proposals,
        structured_evidence,
    )

    occupied_ids = _validated_occupied_ids(
        occupied_review_item_ids
    )

    proposal_groups: dict[
        str,
        list[
            P9ElementProposal
            | P9RelationshipProposal
        ],
    ] = {}
    subject_kinds: dict[str, str] = {}
    global_proposal_keys: set[
        tuple[
            tuple[str, str, str, str],
            str,
            str,
        ]
    ] = set()

    for proposal in (
        structured_proposals.element_proposals
    ):
        _validate_element_proposal(proposal)
        _register_proposal(
            proposal,
            review_item_kind="element",
            proposal_groups=proposal_groups,
            subject_kinds=subject_kinds,
            global_proposal_keys=(
                global_proposal_keys
            ),
        )

    for proposal in (
        structured_proposals
        .relationship_proposals
    ):
        _validate_relationship_proposal(
            proposal
        )
        _register_proposal(
            proposal,
            review_item_kind="relationship",
            proposal_groups=proposal_groups,
            subject_kinds=subject_kinds,
            global_proposal_keys=(
                global_proposal_keys
            ),
        )

    for question in (
        structured_proposals.review_question_proposals
    ):
        _validate_review_question_proposal(
            question
        )
        _register_review_question(
            question,
            proposal_groups=proposal_groups,
            subject_kinds=subject_kinds,
        )

    evidence_by_subject = (
        _validated_evidence_by_subject(
            structured_evidence
        )
    )

    proposal_subjects = set(proposal_groups)
    evidence_subjects = set(
        evidence_by_subject
    )

    if proposal_subjects != evidence_subjects:
        raise ReviewReferenceError(
            "P9 proposal subjects and evidence subjects "
            "must match exactly; "
            f"missing_evidence={sorted(proposal_subjects - evidence_subjects)!r}, "
            f"unexpected_evidence={sorted(evidence_subjects - proposal_subjects)!r}."
        )

    element_titles = (
        _construct_element_title_map(
            proposal_groups,
            subject_kinds=subject_kinds,
        )
    )

    _validate_relationship_endpoints(
        proposal_groups,
        subject_kinds=subject_kinds,
        element_titles=element_titles,
    )

    allocated_ids = list(occupied_ids)
    review_items: list[ReviewItem] = []
    global_evidence_keys: set[
        tuple[
            tuple[str, str, str, str],
            str,
            str,
            str,
        ]
    ] = set()

    for stable_subject_key in sorted(
        proposal_groups
    ):
        review_item_id = next_review_item_id(
            allocated_ids
        )
        allocated_ids.append(review_item_id)

        proposals = tuple(
            sorted(
                proposal_groups[
                    stable_subject_key
                ],
                key=_proposal_sort_key,
            )
        )
        review_item_kind = subject_kinds[
            stable_subject_key
        ]
        evidence = evidence_by_subject[
            stable_subject_key
        ]

        _validate_subject_evidence(
            evidence,
            stable_subject_key=(
                stable_subject_key
            ),
            review_item_kind=review_item_kind,
            proposals=proposals,
            global_evidence_keys=(
                global_evidence_keys
            ),
        )

        proposal_references = tuple(
            proposal.proposal_reference
            for proposal in proposals
            if isinstance(
                proposal,
                (
                    P9ElementProposal,
                    P9RelationshipProposal,
                ),
            )
        )

        original_report_locator = (
            _review_item_original_report_locator(
                stable_subject_key=(
                    stable_subject_key
                ),
                review_item_kind=(
                    review_item_kind
                ),
            )
        )

        if review_item_kind == "element":
            element_proposals = tuple(
                proposal
                for proposal in proposals
                if isinstance(
                    proposal,
                    P9ElementProposal,
                )
            )

            if len(element_proposals) != len(
                proposals
            ):
                raise ReviewIntegrityError(
                    "Element Review Item group contains "
                    "a non-element proposal."
                )

            (
                current_content,
                dimension_selections,
            ) = _construct_element_draft(
                element_proposals
            )

            section = "elements"

        elif review_item_kind == "relationship":
            relationship_proposals = tuple(
                proposal
                for proposal in proposals
                if isinstance(
                    proposal,
                    P9RelationshipProposal,
                )
            )

            if len(
                relationship_proposals
            ) != len(proposals):
                raise ReviewIntegrityError(
                    "Relationship Review Item group "
                    "contains a non-relationship proposal."
                )

            (
                current_content,
                dimension_selections,
            ) = _construct_relationship_draft(
                relationship_proposals,
                element_titles=element_titles,
                target_notation_profile_id=(
                    target_notation_profile_id
                ),
                target_notation_profile_version=(
                    target_notation_profile_version
                ),
            )

            section = "relationships"

        elif review_item_kind == "open_question":
            question_proposals = tuple(
                proposal
                for proposal in proposals
                if isinstance(
                    proposal,
                    P9ReviewQuestionProposal,
                )
            )

            if len(question_proposals) != len(
                proposals
            ):
                raise ReviewIntegrityError(
                    "Open Question Review Item group "
                    "contains a non-question proposal."
                )

            (
                current_content,
                dimension_selections,
            ) = _construct_open_question_draft(
                question_proposals
            )

            section = "open_questions"

        else:
            raise ReviewIntegrityError(
                "Unsupported initial P9 Review Item kind."
            )

        item = create_review_item(
            project_id=(
                structured_proposals.project_id
            ),
            review_document_id=(
                review_document_id
            ),
            review_document_version_id=(
                review_document_version_id
            ),
            review_item_id=review_item_id,
            review_item_kind=review_item_kind,
            stable_subject_key=(
                stable_subject_key
            ),
            section=section,
            lineage_operation="original",
            derived_from_review_item_ids=(),
            original_report_locator=(
                original_report_locator
            ),
            proposal_references=(
                proposal_references
            ),
            source_evidence_references=tuple(
                sorted(
                    evidence
                    .source_evidence_references,
                    key=_evidence_sort_key,
                )
            ),
            consensus_evidence_references=tuple(
                sorted(
                    evidence
                    .consensus_evidence_references,
                    key=_evidence_sort_key,
                )
            ),
            current_content=current_content,
            dimension_selections=(
                dimension_selections
            ),
            effective_review_outcome="open",
        )

        review_items.append(item)

    return P9InitialReviewItemSet(
        project_id=(
            structured_proposals.project_id
        ),
        source_id=(
            structured_proposals.source_id
        ),
        processing_run_id=(
            structured_proposals.processing_run_id
        ),
        attempt_id=(
            structured_proposals.attempt_id
        ),
        review_document_id=(
            review_document_id
        ),
        review_document_version_id=(
            review_document_version_id
        ),
        review_items=tuple(review_items),
    )


def _validate_input_identity(
    proposals: P9StructuredProposalSet,
    evidence: P9StructuredEvidenceSet,
) -> None:
    for field_name in (
        "project_id",
        "source_id",
        "processing_run_id",
        "attempt_id",
    ):
        if getattr(
            proposals,
            field_name,
        ) != getattr(
            evidence,
            field_name,
        ):
            raise ReviewIntegrityError(
                "P9 proposals and evidence disagree "
                f"on {field_name}."
            )


def _validated_occupied_ids(
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ReviewValidationError(
            "occupied_review_item_ids must be "
            "an iterable of Review Item IDs."
        )

    try:
        identifiers = tuple(values)
    except TypeError as exc:
        raise ReviewValidationError(
            "occupied_review_item_ids must be iterable."
        ) from exc

    for identifier in identifiers:
        validate_review_item_id(identifier)

    if len(identifiers) != len(
        set(identifiers)
    ):
        raise ReviewIntegrityError(
            "occupied_review_item_ids must be unique."
        )

    return identifiers


def _validate_element_proposal(
    proposal: object,
) -> None:
    if not isinstance(
        proposal,
        P9ElementProposal,
    ):
        raise ReviewValidationError(
            "element_proposals must contain "
            "P9ElementProposal values."
        )

    if proposal.stable_subject_key.startswith(
        "semantic:element:ses-"
    ):
        synthesized_id = proposal.stable_subject_key.removeprefix(
            "semantic:element:"
        )
        if (
            len(synthesized_id) != len("ses-000001")
            or not synthesized_id[4:].isdigit()
            or synthesized_id == "ses-000000"
        ):
            raise ReviewIntegrityError(
                "Synthesized Element Review subject identity is invalid."
            )
        return

    if proposal.stable_subject_key.startswith(
        "semantic:element:"
    ):
        if len(proposal.stable_subject_key) <= len(
            "semantic:element:"
        ):
            raise ReviewIntegrityError(
                "Semantic Element Review subject identity is incomplete."
            )
        return

    if proposal.stable_subject_key.startswith("SES-"):
        if (
            len(proposal.stable_subject_key) != len("SES-000001")
            or not proposal.stable_subject_key[4:].isdigit()
            or proposal.stable_subject_key == "SES-000000"
        ):
            raise ReviewIntegrityError(
                "Synthesized Element Review subject identity is invalid."
            )
        return

    expected_key = (
        create_element_stable_subject_key(
            element_type=proposal.element_type,
            candidate_name=proposal.candidate_name,
        )
    )

    if (
        proposal.stable_subject_key
        != expected_key
    ):
        raise ReviewIntegrityError(
            "P9 Element Proposal stable_subject_key "
            "does not match its semantic identity."
        )


def _validate_relationship_proposal(
    proposal: object,
) -> None:
    if not isinstance(
        proposal,
        P9RelationshipProposal,
    ):
        raise ReviewValidationError(
            "relationship_proposals must contain "
            "P9RelationshipProposal values."
        )

    if proposal.stable_subject_key.startswith(
        "semantic:relationship:srs-"
    ):
        synthesized_relationship_id = (
            proposal.stable_subject_key.removeprefix(
                "semantic:relationship:"
            )
        )
        synthesized_source_id = (
            proposal.source_subject_key.removeprefix(
                "semantic:element:"
            )
            if proposal.source_subject_key.startswith(
                "semantic:element:"
            )
            else ""
        )
        synthesized_target_id = (
            proposal.target_subject_key.removeprefix(
                "semantic:element:"
            )
            if proposal.target_subject_key.startswith(
                "semantic:element:"
            )
            else ""
        )
        synthesized_relationship_id_valid = (
            len(synthesized_relationship_id) == len("srs-000001")
            and synthesized_relationship_id[4:].isdigit()
            and synthesized_relationship_id != "srs-000000"
        )
        synthesized_source_id_valid = (
            synthesized_source_id.startswith("ses-")
            and len(synthesized_source_id) == len("ses-000001")
            and synthesized_source_id[4:].isdigit()
            and synthesized_source_id != "ses-000000"
        )
        synthesized_target_id_valid = (
            synthesized_target_id.startswith("ses-")
            and len(synthesized_target_id) == len("ses-000001")
            and synthesized_target_id[4:].isdigit()
            and synthesized_target_id != "ses-000000"
        )
        if not (
            synthesized_relationship_id_valid
            and synthesized_source_id_valid
            and synthesized_target_id_valid
        ):
            raise ReviewIntegrityError(
                "Synthesized Relationship Review subject requires valid "
                "namespaced SRS identity and namespaced SES endpoints."
            )
        return

    if proposal.stable_subject_key.startswith(
        "semantic:relationship:"
    ):
        if (
            len(proposal.stable_subject_key)
            <= len("semantic:relationship:")
            or not proposal.source_subject_key.startswith(
                "semantic:element:"
            )
            or not proposal.target_subject_key.startswith(
                "semantic:element:"
            )
        ):
            raise ReviewIntegrityError(
                "Semantic Relationship Review subject requires complete "
                "semantic relationship and element endpoint identities."
            )
        return

    if proposal.stable_subject_key.startswith("SRS-"):
        synthesized_relationship_id_valid = (
            len(proposal.stable_subject_key) == len("SRS-000001")
            and proposal.stable_subject_key[4:].isdigit()
            and proposal.stable_subject_key != "SRS-000000"
        )
        synthesized_source_id_valid = (
            proposal.source_subject_key.startswith("SES-")
            and len(proposal.source_subject_key) == len("SES-000001")
            and proposal.source_subject_key[4:].isdigit()
            and proposal.source_subject_key != "SES-000000"
        )
        synthesized_target_id_valid = (
            proposal.target_subject_key.startswith("SES-")
            and len(proposal.target_subject_key) == len("SES-000001")
            and proposal.target_subject_key[4:].isdigit()
            and proposal.target_subject_key != "SES-000000"
        )
        if not (
            synthesized_relationship_id_valid
            and synthesized_source_id_valid
            and synthesized_target_id_valid
        ):
            raise ReviewIntegrityError(
                "Synthesized Relationship Review subject requires valid "
                "SRS identity and synthesized SES endpoint identities."
            )
        return

    expected_key = (
        create_relationship_stable_subject_key(
            source_subject_key=(
                proposal.source_subject_key
            ),
            link_type=proposal.link_type,
            target_subject_key=(
                proposal.target_subject_key
            ),
        )
    )

    if (
        proposal.stable_subject_key
        != expected_key
    ):
        raise ReviewIntegrityError(
            "P9 Relationship Proposal stable_subject_key "
            "does not match its semantic identity."
        )


def _validate_review_question_proposal(
    proposal: object,
) -> None:
    if not isinstance(
        proposal,
        P9ReviewQuestionProposal,
    ):
        raise ReviewValidationError(
            "review_question_proposals must contain "
            "P9ReviewQuestionProposal values."
        )

    if not proposal.stable_subject_key.startswith(
        "open_question:"
    ):
        raise ReviewIntegrityError(
            "P9 Open Question stable_subject_key must "
            "identify an open_question subject."
        )

    for value, label in (
        (proposal.question_id, "question_id"),
        (proposal.issue_code, "issue_code"),
        (proposal.title, "question title"),
        (proposal.review_question, "review_question"),
        (proposal.raw_value, "raw_value"),
        (proposal.normalized_value, "normalized_value"),
        (proposal.source_statement, "source_statement"),
        (proposal.evidence_locator, "evidence_locator"),
        (proposal.rationale_summary, "rationale_summary"),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ReviewValidationError(
                f"{label} must be non-empty text."
            )


def _register_review_question(
    proposal: P9ReviewQuestionProposal,
    *,
    proposal_groups: dict[str, list],
    subject_kinds: dict[str, str],
) -> None:
    existing_kind = subject_kinds.get(
        proposal.stable_subject_key
    )
    if (
        existing_kind is not None
        and existing_kind != "open_question"
    ):
        raise ReviewIntegrityError(
            "One stable subject cannot be both an "
            "Open Question and another Review Item kind."
        )

    subject_kinds[
        proposal.stable_subject_key
    ] = "open_question"
    proposal_groups.setdefault(
        proposal.stable_subject_key,
        [],
    ).append(proposal)


def _register_proposal(
    proposal: (
        P9ElementProposal
        | P9RelationshipProposal
    ),
    *,
    review_item_kind: str,
    proposal_groups: dict[
        str,
        list[
            P9ElementProposal
            | P9RelationshipProposal
        ],
    ],
    subject_kinds: dict[str, str],
    global_proposal_keys: set[
        tuple[
            tuple[str, str, str, str],
            str,
            str,
        ]
    ],
) -> None:
    reference = proposal.proposal_reference

    if not isinstance(
        reference,
        ReviewProposalReference,
    ):
        raise ReviewValidationError(
            "P9 Proposal must contain a "
            "ReviewProposalReference."
        )

    if reference.review_state != "available":
        raise ReviewIntegrityError(
            "Initial P9 Review Items accept only "
            "available Agent proposals."
        )

    existing_kind = subject_kinds.get(
        proposal.stable_subject_key
    )

    if (
        existing_kind is not None
        and existing_kind != review_item_kind
    ):
        raise ReviewIntegrityError(
            "One stable subject cannot be both an "
            "element and a relationship."
        )

    subject_kinds[
        proposal.stable_subject_key
    ] = review_item_kind

    key = (
        _artifact_reference_key(
            reference.artifact_reference
        ),
        reference.proposal_id,
        reference.proposal_content_fingerprint,
    )

    if key in global_proposal_keys:
        raise ReviewIntegrityError(
            "P9 Proposal References must be globally "
            "unique across initial Review Items."
        )

    global_proposal_keys.add(key)

    proposal_groups.setdefault(
        proposal.stable_subject_key,
        [],
    ).append(proposal)


def _validated_evidence_by_subject(
    evidence: P9StructuredEvidenceSet,
) -> dict[str, P9SubjectEvidence]:
    result: dict[str, P9SubjectEvidence] = {}

    for record in evidence.subject_evidence:
        if not isinstance(
            record,
            P9SubjectEvidence,
        ):
            raise ReviewValidationError(
                "subject_evidence must contain "
                "P9SubjectEvidence values."
            )

        if (
            record.stable_subject_key
            in result
        ):
            raise ReviewIntegrityError(
                "P9 Evidence subjects must be unique."
            )

        result[
            record.stable_subject_key
        ] = record

    return result


def _construct_element_title_map(
    proposal_groups: dict[
        str,
        list[
            P9ElementProposal
            | P9RelationshipProposal
        ],
    ],
    *,
    subject_kinds: dict[str, str],
) -> dict[str, str]:
    titles: dict[str, str] = {}

    for stable_subject_key in sorted(
        proposal_groups
    ):
        if (
            subject_kinds[stable_subject_key]
            != "element"
        ):
            continue

        proposals = tuple(
            sorted(
                proposal_groups[
                    stable_subject_key
                ],
                key=_proposal_sort_key,
            )
        )

        representative = proposals[0]

        if not isinstance(
            representative,
            P9ElementProposal,
        ):
            raise ReviewIntegrityError(
                "Element subject has no valid "
                "element representative."
            )

        titles[stable_subject_key] = (
            representative.candidate_name
        )

    return titles


def _validate_relationship_endpoints(
    proposal_groups: dict[
        str,
        list[
            P9ElementProposal
            | P9RelationshipProposal
        ],
    ],
    *,
    subject_kinds: dict[str, str],
    element_titles: dict[str, str],
) -> None:
    for stable_subject_key, proposals in (
        proposal_groups.items()
    ):
        if (
            subject_kinds[stable_subject_key]
            != "relationship"
        ):
            continue

        for proposal in proposals:
            if not isinstance(
                proposal,
                P9RelationshipProposal,
            ):
                raise ReviewIntegrityError(
                    "Relationship subject contains "
                    "a non-relationship proposal."
                )

            if (
                proposal.source_subject_key
                not in element_titles
            ):
                raise ReviewReferenceError(
                    "P9 Relationship Proposal references "
                    "an unavailable source element subject."
                )

            if (
                proposal.target_subject_key
                not in element_titles
            ):
                raise ReviewReferenceError(
                    "P9 Relationship Proposal references "
                    "an unavailable target element subject."
                )


def _validate_subject_evidence(
    evidence: P9SubjectEvidence,
    *,
    stable_subject_key: str,
    review_item_kind: str,
    proposals: tuple[
        P9ElementProposal
        | P9RelationshipProposal,
        ...,
    ],
    global_evidence_keys: set[
        tuple[
            tuple[str, str, str, str],
            str,
            str,
            str,
        ]
    ],
) -> None:
    if (
        evidence.stable_subject_key
        != stable_subject_key
    ):
        raise ReviewIntegrityError(
            "P9 Evidence stable subject does not "
            "match its Review Item group."
        )

    if (
        evidence.review_item_kind
        != review_item_kind
    ):
        raise ReviewIntegrityError(
            "P9 Evidence Review Item kind does not "
            "match its proposal group."
        )

    expected_source_keys: set[
        tuple[
            tuple[str, str, str, str],
            str,
        ]
    ] = set()

    for proposal in proposals:
        reference = (
            proposal.proposal_reference
            if isinstance(
                proposal,
                (
                    P9ElementProposal,
                    P9RelationshipProposal,
                ),
            )
            else None
        )

        if isinstance(
            proposal,
            P9ElementProposal,
        ):
            expected_locator = (
                "output_text:/candidate_model_elements/"
                f"{proposal.candidate_id}/source_evidence"
            )
            artifact_reference = (
                reference.artifact_reference
            )
        elif isinstance(
            proposal,
            P9RelationshipProposal,
        ):
            expected_locator = (
                "output_text:/explicit_source_links/"
                f"{proposal.link_id}/source_evidence"
            )
            artifact_reference = (
                reference.artifact_reference
            )
        elif isinstance(
            proposal,
            P9ReviewQuestionProposal,
        ):
            expected_locator = proposal.evidence_locator
            artifact_reference = (
                proposal.artifact_reference
            )
        else:
            raise ReviewIntegrityError(
                "Unsupported P9 proposal type in "
                "source-evidence validation."
            )

        expected_source_keys.add(
            (
                _artifact_reference_key(
                    artifact_reference
                ),
                expected_locator,
            )
        )

    actual_source_keys: set[
        tuple[
            tuple[str, str, str, str],
            str,
        ]
    ] = set()

    for reference in (
        evidence.source_evidence_references
    ):
        if not isinstance(
            reference,
            ReviewEvidenceReference,
        ):
            raise ReviewValidationError(
                "P9 Source Evidence entries must be "
                "ReviewEvidenceReference values."
            )

        if (
            reference.evidence_role
            != SOURCE_EVIDENCE_ROLE
        ):
            raise ReviewIntegrityError(
                "P9 Source Evidence uses an "
                "unexpected evidence role."
            )

        actual_source_keys.add(
            (
                _artifact_reference_key(
                    reference.artifact_reference
                ),
                reference.evidence_locator,
            )
        )

        _register_global_evidence(
            reference,
            global_evidence_keys=(
                global_evidence_keys
            ),
        )

    if (
        len(
            evidence.source_evidence_references
        )
        != len(proposals)
        or actual_source_keys
        != expected_source_keys
    ):
        raise ReviewReferenceError(
            "P9 Source Evidence does not map "
            "one-to-one to the grouped proposals."
        )

    consensus = (
        evidence.consensus_evidence_references
    )

    synthesized_element = (
        review_item_kind == "element"
        and stable_subject_key.startswith(
            "semantic:element:ses-"
        )
    )
    synthesized_relationship = (
        review_item_kind == "relationship"
        and stable_subject_key.startswith(
            "semantic:relationship:srs-"
        )
    )
    semantic_element = (
        review_item_kind == "element"
        and stable_subject_key.startswith(
            "semantic:element:"
        )
        and not synthesized_element
    )
    semantic_relationship = (
        review_item_kind == "relationship"
        and stable_subject_key.startswith(
            "semantic:relationship:"
        )
        and not synthesized_relationship
    )

    if review_item_kind == "element":
        if len(consensus) != 1:
            raise ReviewIntegrityError(
                "Initial P9 element Review Items require "
                "exactly one Consensus Evidence Reference."
            )
    elif semantic_relationship or synthesized_relationship:
        if len(consensus) != 1:
            raise ReviewIntegrityError(
                "Semantic relationship Review Items require "
                "exactly one semantic synthesis Evidence Reference."
            )
    elif consensus:
        raise ReviewIntegrityError(
            "Initial P9 relationship Review Items must "
            "not contain invented Consensus Evidence."
        )

    for reference in consensus:
        if not isinstance(
            reference,
            ReviewEvidenceReference,
        ):
            raise ReviewValidationError(
                "P9 Consensus Evidence entries must be "
                "ReviewEvidenceReference values."
            )

        if (
            reference.evidence_role
            != CONSENSUS_EVIDENCE_ROLE
        ):
            raise ReviewIntegrityError(
                "P9 Consensus Evidence uses an "
                "unexpected evidence role."
            )

        if semantic_element or semantic_relationship:
            expected_locator = (
                "semantic_consolidation:/subjects/"
                f"{stable_subject_key}"
            )
            if reference.evidence_locator != expected_locator:
                raise ReviewIntegrityError(
                    "Semantic Review Item Consensus Evidence does not "
                    "identify its exact C2/C3 semantic subject."
                )
        elif synthesized_element or synthesized_relationship:
            subject_kind = (
                "element"
                if synthesized_element
                else "relationship"
            )
            review_prefix = (
                "semantic:element:"
                if synthesized_element
                else "semantic:relationship:"
            )
            synthesized_subject_id = (
                stable_subject_key.removeprefix(
                    review_prefix
                ).upper()
            )
            expected_locator = (
                "cross_unit_semantic_synthesis:/"
                f"synthesized_{subject_kind}_subjects/"
                f"{synthesized_subject_id}"
            )
            if reference.evidence_locator != expected_locator:
                raise ReviewIntegrityError(
                    "Synthesized Review Item Consensus Evidence does not "
                    "identify its exact D4 semantic subject."
                )

        _register_global_evidence(
            reference,
            global_evidence_keys=(
                global_evidence_keys
            ),
        )


def _register_global_evidence(
    reference: ReviewEvidenceReference,
    *,
    global_evidence_keys: set[
        tuple[
            tuple[str, str, str, str],
            str,
            str,
            str,
        ]
    ],
) -> None:
    key = (
        _artifact_reference_key(
            reference.artifact_reference
        ),
        reference.evidence_role,
        reference.evidence_locator,
        reference.evidence_content_fingerprint,
    )

    if key in global_evidence_keys:
        raise ReviewIntegrityError(
            "One exact P9 Evidence Reference must not "
            "be reused across multiple Review Items."
        )

    global_evidence_keys.add(key)


def _construct_element_draft(
    proposals: tuple[
        P9ElementProposal,
        ...,
    ],
) -> tuple[
    ReviewItemContent,
    tuple[ReviewDimensionSelection, ...],
]:
    representative = proposals[0]
    source_reference_id = (
        _proposal_reference_id(
            representative.proposal_reference
        )
    )

    content = ReviewItemContent(
        title=representative.candidate_name,
        primary_text=representative.description,
        description=(
            representative.rationale_summary
        ),
        information_type=(
            representative.element_type
        ),
        modality=None,
        epistemic_status=None,
        human_rationale=None,
        human_confidence=None,
        relationship_representation=None,
    )

    selections = (
        ReviewDimensionSelection(
            dimension="content",
            selected_values=(
                representative.description,
            ),
            value_origin="agent_proposal",
            source_reference_ids=(
                source_reference_id,
            ),
            rationale=(
                _INITIAL_DRAFT_RATIONALE
            ),
            selected_by=None,
            selected_at=None,
        ),
        ReviewDimensionSelection(
            dimension="classification",
            selected_values=(
                representative.element_type,
            ),
            value_origin="agent_proposal",
            source_reference_ids=(
                source_reference_id,
            ),
            rationale=(
                _INITIAL_DRAFT_RATIONALE
            ),
            selected_by=None,
            selected_at=None,
        ),
    )

    return content, selections


def _construct_open_question_draft(
    proposals: tuple[
        P9ReviewQuestionProposal,
        ...,
    ],
) -> tuple[
    ReviewItemContent,
    tuple[ReviewDimensionSelection, ...],
]:
    representative = proposals[0]

    description = (
        f"{representative.rationale_summary}\n\n"
        f"Observed Agent value: {representative.raw_value}\n"
        f"Review normalization: {representative.normalized_value}\n"
        f"Exact evidence locator: {representative.evidence_locator}\n"
        f"Raw structured fragment: {representative.raw_fragment_json}"
    )

    content = ReviewItemContent(
        title=representative.title,
        primary_text=representative.review_question,
        description=description,
        information_type="open_question",
        modality=None,
        epistemic_status="uncertain",
        human_rationale=None,
        human_confidence=None,
        relationship_representation=None,
    )

    return content, ()


def _construct_relationship_draft(
    proposals: tuple[
        P9RelationshipProposal,
        ...,
    ],
    *,
    element_titles: dict[str, str],
    target_notation_profile_id: str,
    target_notation_profile_version: str,
) -> tuple[
    ReviewItemContent,
    tuple[ReviewDimensionSelection, ...],
]:
    representative = proposals[0]
    source_reference_id = (
        _proposal_reference_id(
            representative.proposal_reference
        )
    )

    source_title = element_titles[
        representative.source_subject_key
    ]
    target_title = element_titles[
        representative.target_subject_key
    ]

    representation = (
        ReviewRelationshipRepresentation(
            source_subject_key=(
                representative.source_subject_key
            ),
            target_subject_key=(
                representative.target_subject_key
            ),
            semantic_intent=(
                representative.link_type
            ),
            sysml_v2_construct=None,
            construct_properties=(),
            target_notation_profile_id=(
                target_notation_profile_id
            ),
            target_notation_profile_version=(
                target_notation_profile_version
            ),
            textual_notation_preview=None,
            validation_status="unresolved",
            validation_fingerprint=None,
        )
    )

    content = ReviewItemContent(
        title=(
            f"{source_title} "
            f"{representative.link_type} "
            f"{target_title}"
        ),
        primary_text=(
            representative.source_statement
        ),
        description=(
            representative.rationale_summary
        ),
        information_type="relationship",
        modality=None,
        epistemic_status=None,
        human_rationale=None,
        human_confidence=None,
        relationship_representation=(
            representation
        ),
    )

    selections = (
        ReviewDimensionSelection(
            dimension="content",
            selected_values=(
                representative.source_statement,
            ),
            value_origin="agent_proposal",
            source_reference_ids=(
                source_reference_id,
            ),
            rationale=(
                _INITIAL_DRAFT_RATIONALE
            ),
            selected_by=None,
            selected_at=None,
        ),
        ReviewDimensionSelection(
            dimension=(
                "relationship_representation"
            ),
            selected_values=(
                representative.link_type,
            ),
            value_origin="agent_proposal",
            source_reference_ids=(
                source_reference_id,
            ),
            rationale=(
                _INITIAL_DRAFT_RATIONALE
            ),
            selected_by=None,
            selected_at=None,
        ),
    )

    return content, selections


def _review_item_original_report_locator(
    *,
    stable_subject_key: str,
    review_item_kind: str,
) -> str:
    """Return the canonical report locator for one grouped subject."""

    if review_item_kind == "element":
        section = "recognized_elements"
    elif review_item_kind == "relationship":
        section = "explicit_source_links"
    elif review_item_kind == "open_question":
        section = "open_questions"
    else:
        raise ReviewIntegrityError(
            "Unsupported Review Item kind for "
            "original report locator construction."
        )

    return (
        f"report:{section}/"
        f"{stable_subject_key}"
    )


def _proposal_reference_id(
    reference: ReviewProposalReference,
) -> str:
    return (
        f"{reference.artifact_reference.artifact_id}:"
        f"{reference.proposal_id}"
    )


def _validate_target_notation_profile(
    profile_id: object,
    profile_version: object,
) -> None:
    if (
        not isinstance(profile_id, str)
        or _PROFILE_ID_PATTERN.fullmatch(
            profile_id
        )
        is None
    ):
        raise ReviewValidationError(
            "target_notation_profile_id must be "
            "an uppercase profile identifier."
        )

    if (
        not isinstance(profile_version, str)
        or _SEMANTIC_VERSION_PATTERN.fullmatch(
            profile_version
        )
        is None
    ):
        raise ReviewValidationError(
            "target_notation_profile_version must "
            "be a semantic version."
        )


def _proposal_sort_key(
    proposal: (
        P9ElementProposal
        | P9RelationshipProposal
        | P9ReviewQuestionProposal
    ),
) -> tuple[
    str,
    str,
    str,
    str,
    str,
]:
    if isinstance(
        proposal,
        P9ReviewQuestionProposal,
    ):
        return (
            proposal.artifact_reference.artifact_id,
            proposal.agent_id,
            proposal.persona_id,
            proposal.question_id,
            proposal.evidence_content_fingerprint,
        )

    reference = proposal.proposal_reference

    return (
        reference.artifact_reference.artifact_id,
        reference.agent_id,
        reference.persona_id,
        reference.proposal_id,
        reference.proposal_content_fingerprint,
    )


def _evidence_sort_key(
    reference: ReviewEvidenceReference,
) -> tuple[str, str, str, str]:
    return (
        reference.artifact_reference.artifact_id,
        reference.evidence_role,
        reference.evidence_locator,
        reference.evidence_content_fingerprint,
    )


def _artifact_reference_key(
    reference,
) -> tuple[str, str, str, str]:
    return (
        reference.artifact_type,
        reference.artifact_id,
        reference.content_fingerprint,
        reference.repository_relative_path,
    )
