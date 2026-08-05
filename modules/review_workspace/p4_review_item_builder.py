"""Construct independent initial Review Items from validated P4 evidence."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from modules.framework_assignment import (
    FrameworkAssignmentCandidate,
    FrameworkAssignmentError,
    validate_framework_assignment_candidate,
)
from modules.human_review import (
    HumanReviewDecision,
    HumanReviewError,
    validate_human_review_decision,
)
from modules.information_units import (
    InformationUnit,
    InformationUnitError,
    validate_information_unit,
    validate_information_unit_id,
)
from modules.project_workspace.identifiers import (
    is_valid_project_id,
)
from modules.terminology_mapping import (
    TerminologyMappingCandidate,
    TerminologyMappingError,
    validate_terminology_mapping_candidate,
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
from .p4_evidence_adapter import (
    P4ReviewEvidenceRecord,
    P4ReviewEvidenceSet,
)
from .p4_evidence_reference_adapter import (
    P4_FRAMEWORK_ASSIGNMENT_ARTIFACT_TYPE,
    P4_FRAMEWORK_ASSIGNMENT_EVIDENCE_ROLE,
    P4_HUMAN_REVIEW_ARTIFACT_TYPE,
    P4_HUMAN_REVIEW_EVIDENCE_ROLE,
    P4_INFORMATION_UNIT_ARTIFACT_TYPE,
    P4_INFORMATION_UNIT_EVIDENCE_ROLE,
    P4_TERMINOLOGY_MAPPING_ARTIFACT_TYPE,
    P4_TERMINOLOGY_MAPPING_EVIDENCE_ROLE,
    P4InformationUnitEvidenceReferences,
    P4StructuredEvidenceReferenceSet,
)
from .types import (
    ReviewDimensionSelection,
    ReviewEvidenceReference,
    ReviewItem,
    ReviewItemContent,
)


P4_OPEN_QUESTION_INFORMATION_TYPES = frozenset(
    {
        "open_question",
        "gap",
        "ambiguity",
        "risk",
        "unclassified",
    }
)

_INITIAL_P4_DRAFT_RATIONALE = (
    "Deterministic initial draft from one validated P4 "
    "Information Unit; no Review Workspace selection has occurred."
)


@dataclass(frozen=True, slots=True)
class P4InitialReviewItemSet:
    """Initial independent Review Items for selected P4 Information Units."""

    project_id: str
    source_id: str
    review_document_id: str
    review_document_version_id: str
    review_items: tuple[ReviewItem, ...]

    @property
    def element_items(
        self,
    ) -> tuple[ReviewItem, ...]:
        """Return P4 items represented in the elements section."""

        return tuple(
            item
            for item in self.review_items
            if item.review_item_kind == "element"
        )

    @property
    def open_question_items(
        self,
    ) -> tuple[ReviewItem, ...]:
        """Return P4 issues and questions requiring explicit attention."""

        return tuple(
            item
            for item in self.review_items
            if item.review_item_kind
            == "open_question"
        )

    def item_for_information_unit(
        self,
        information_unit_id: str,
    ) -> ReviewItem:
        """Return the unique item for one P4 Information Unit."""

        stable_subject_key = (
            create_p4_information_unit_stable_subject_key(
                information_unit_id
            )
        )

        matches = tuple(
            item
            for item in self.review_items
            if item.stable_subject_key
            == stable_subject_key
        )

        if not matches:
            raise ReviewReferenceError(
                "No initial P4 Review Item exists for "
                f"Information Unit {information_unit_id!r}."
            )

        if len(matches) != 1:
            raise ReviewIntegrityError(
                "Initial P4 Review Item subjects "
                "must be unique."
            )

        return matches[0]


def create_p4_information_unit_stable_subject_key(
    information_unit_id: object,
) -> str:
    """Return the stable Review Workspace subject for one P4 unit."""

    validated_id = validate_information_unit_id(
        information_unit_id
    )

    return (
        "p4:information_unit:"
        f"{validated_id.lower()}"
    )


def construct_initial_p4_review_items(
    p4_evidence: object,
    p4_evidence_references: object,
    *,
    review_document_id: str,
    review_document_version_id: str,
    occupied_review_item_ids: Iterable[str] = (),
) -> P4InitialReviewItemSet:
    """Construct deterministic open Review Items from independent P4 units."""

    if not isinstance(
        p4_evidence,
        P4ReviewEvidenceSet,
    ):
        raise ReviewValidationError(
            "p4_evidence must be a "
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

    if not is_valid_project_id(
        p4_evidence.project_id
    ):
        raise ReviewValidationError(
            "P4 project_id must be a valid "
            "six-digit Project ID."
        )

    validate_review_document_id(
        review_document_id
    )
    validate_review_document_version_id(
        review_document_version_id
    )

    _validate_input_identity(
        p4_evidence,
        p4_evidence_references,
    )

    records_by_id = _records_by_information_unit_id(
        p4_evidence.records
    )
    references_by_id = (
        _reference_records_by_information_unit_id(
            p4_evidence_references.records
        )
    )

    record_ids = set(records_by_id)
    reference_ids = set(references_by_id)

    if record_ids != reference_ids:
        raise ReviewReferenceError(
            "P4 evidence and persisted-reference subjects "
            "must match exactly; "
            f"missing_references={sorted(record_ids - reference_ids)!r}, "
            f"unexpected_references={sorted(reference_ids - record_ids)!r}."
        )

    allocated_ids = list(
        _validated_occupied_ids(
            occupied_review_item_ids
        )
    )
    review_items: list[ReviewItem] = []
    global_evidence_keys: set[
        tuple[
            tuple[str, str, str, str],
            str,
            str,
            str,
        ]
    ] = set()

    for information_unit_id in sorted(
        records_by_id
    ):
        record = records_by_id[
            information_unit_id
        ]
        reference_record = references_by_id[
            information_unit_id
        ]

        _validate_p4_record_objects(record)

        evidence_references = (
            _validated_record_evidence_references(
                record,
                reference_record,
            )
        )

        for reference in evidence_references:
            evidence_key = _evidence_reference_key(
                reference
            )

            if evidence_key in global_evidence_keys:
                raise ReviewIntegrityError(
                    "One exact P4 Evidence Reference must "
                    "not be reused across Review Items."
                )

            global_evidence_keys.add(
                evidence_key
            )

        review_item_id = next_review_item_id(
            allocated_ids
        )
        allocated_ids.append(review_item_id)

        information_unit = (
            record.information_unit
        )
        review_item_kind = (
            _review_item_kind_for_information_type(
                information_unit.information_type
            )
        )
        section = (
            "open_questions"
            if review_item_kind == "open_question"
            else "elements"
        )

        item = create_review_item(
            project_id=p4_evidence.project_id,
            review_document_id=review_document_id,
            review_document_version_id=(
                review_document_version_id
            ),
            review_item_id=review_item_id,
            review_item_kind=review_item_kind,
            stable_subject_key=(
                create_p4_information_unit_stable_subject_key(
                    information_unit_id
                )
            ),
            section=section,
            lineage_operation="original",
            derived_from_review_item_ids=(),
            original_report_locator=(
                "p4:information_units/"
                f"{information_unit_id}"
            ),
            proposal_references=(),
            source_evidence_references=tuple(
                sorted(
                    evidence_references,
                    key=_evidence_sort_key,
                )
            ),
            consensus_evidence_references=(),
            current_content=(
                _construct_information_unit_content(
                    information_unit
                )
            ),
            dimension_selections=(
                _construct_information_unit_selections(
                    information_unit
                )
            ),
            effective_review_outcome="open",
        )

        review_items.append(item)

    return P4InitialReviewItemSet(
        project_id=p4_evidence.project_id,
        source_id=p4_evidence.source_id,
        review_document_id=review_document_id,
        review_document_version_id=(
            review_document_version_id
        ),
        review_items=tuple(review_items),
    )


def _validate_input_identity(
    evidence: P4ReviewEvidenceSet,
    references: P4StructuredEvidenceReferenceSet,
) -> None:
    for field_name in (
        "project_id",
        "source_id",
    ):
        if getattr(
            evidence,
            field_name,
        ) != getattr(
            references,
            field_name,
        ):
            raise ReviewIntegrityError(
                "P4 evidence and persisted references "
                f"disagree on {field_name}."
            )


def _records_by_information_unit_id(
    records: tuple[P4ReviewEvidenceRecord, ...],
) -> dict[str, P4ReviewEvidenceRecord]:
    result: dict[
        str,
        P4ReviewEvidenceRecord,
    ] = {}

    for record in records:
        if not isinstance(
            record,
            P4ReviewEvidenceRecord,
        ):
            raise ReviewValidationError(
                "P4 records must contain "
                "P4ReviewEvidenceRecord values."
            )

        information_unit_id = (
            record.information_unit
            .information_unit_id
        )

        if information_unit_id in result:
            raise ReviewIntegrityError(
                "P4 Review Evidence records must "
                "contain unique Information Unit IDs."
            )

        result[information_unit_id] = record

    return result


def _reference_records_by_information_unit_id(
    records: tuple[
        P4InformationUnitEvidenceReferences,
        ...,
    ],
) -> dict[
    str,
    P4InformationUnitEvidenceReferences,
]:
    result: dict[
        str,
        P4InformationUnitEvidenceReferences,
    ] = {}

    for record in records:
        if not isinstance(
            record,
            P4InformationUnitEvidenceReferences,
        ):
            raise ReviewValidationError(
                "P4 reference records must contain "
                "P4InformationUnitEvidenceReferences values."
            )

        if record.information_unit_id in result:
            raise ReviewIntegrityError(
                "P4 persisted-reference records must "
                "contain unique Information Unit IDs."
            )

        result[
            record.information_unit_id
        ] = record

    return result


def _validate_p4_record_objects(
    record: P4ReviewEvidenceRecord,
) -> None:
    information_unit = record.information_unit

    if not isinstance(
        information_unit,
        InformationUnit,
    ):
        raise ReviewValidationError(
            "P4 record information_unit must be "
            "an InformationUnit."
        )

    try:
        validate_information_unit(
            information_unit
        )
    except InformationUnitError as exc:
        raise ReviewValidationError(
            "P4 Information Unit is invalid."
        ) from exc

    for candidate in (
        record.terminology_mapping_candidates
    ):
        if not isinstance(
            candidate,
            TerminologyMappingCandidate,
        ):
            raise ReviewValidationError(
                "P4 terminology entries must be "
                "TerminologyMappingCandidate values."
            )

        try:
            validate_terminology_mapping_candidate(
                candidate
            )
        except TerminologyMappingError as exc:
            raise ReviewValidationError(
                "P4 Terminology Mapping Candidate "
                "is invalid."
            ) from exc

    for candidate in (
        record.framework_assignment_candidates
    ):
        if not isinstance(
            candidate,
            FrameworkAssignmentCandidate,
        ):
            raise ReviewValidationError(
                "P4 framework entries must be "
                "FrameworkAssignmentCandidate values."
            )

        try:
            validate_framework_assignment_candidate(
                candidate
            )
        except FrameworkAssignmentError as exc:
            raise ReviewValidationError(
                "P4 Framework Assignment Candidate "
                "is invalid."
            ) from exc

    for decision in record.human_review_decisions:
        if not isinstance(
            decision,
            HumanReviewDecision,
        ):
            raise ReviewValidationError(
                "P4 decision entries must be "
                "HumanReviewDecision values."
            )

        try:
            validate_human_review_decision(
                decision
            )
        except HumanReviewError as exc:
            raise ReviewValidationError(
                "P4 Human Review Decision is invalid."
            ) from exc


def _validated_record_evidence_references(
    record: P4ReviewEvidenceRecord,
    references: P4InformationUnitEvidenceReferences,
) -> tuple[ReviewEvidenceReference, ...]:
    information_unit_id = (
        record.information_unit
        .information_unit_id
    )

    if (
        references.information_unit_id
        != information_unit_id
    ):
        raise ReviewIntegrityError(
            "P4 reference record does not match "
            "its Information Unit."
        )

    expected = _expected_evidence_contracts(
        record
    )
    actual_references = (
        references.all_evidence_references
    )

    actual_by_id: dict[
        str,
        ReviewEvidenceReference,
    ] = {}

    for reference in actual_references:
        if not isinstance(
            reference,
            ReviewEvidenceReference,
        ):
            raise ReviewValidationError(
                "P4 evidence entries must be "
                "ReviewEvidenceReference values."
            )

        artifact_id = (
            reference.artifact_reference
            .artifact_id
        )

        if artifact_id in actual_by_id:
            raise ReviewIntegrityError(
                "P4 evidence artifact IDs must be "
                "unique within one Review Item."
            )

        actual_by_id[artifact_id] = reference

    expected_ids = set(expected)
    actual_ids = set(actual_by_id)

    if expected_ids != actual_ids:
        raise ReviewReferenceError(
            "P4 persisted evidence does not match "
            "the selected record; "
            f"missing={sorted(expected_ids - actual_ids)!r}, "
            f"unexpected={sorted(actual_ids - expected_ids)!r}."
        )

    for artifact_id, contract in expected.items():
        (
            expected_artifact_type,
            expected_role,
            expected_fingerprint,
        ) = contract
        reference = actual_by_id[artifact_id]

        if (
            reference.artifact_reference
            .artifact_type
            != expected_artifact_type
        ):
            raise ReviewIntegrityError(
                "P4 evidence artifact type does not "
                f"match {artifact_id}."
            )

        if (
            reference.evidence_role
            != expected_role
        ):
            raise ReviewIntegrityError(
                "P4 evidence role does not match "
                f"{artifact_id}."
            )

        if reference.evidence_locator != "/":
            raise ReviewIntegrityError(
                "P4 persisted artifact evidence must "
                "use the root locator '/'."
            )

        if (
            reference
            .evidence_content_fingerprint
            != expected_fingerprint
        ):
            raise ReviewIntegrityError(
                "P4 evidence content fingerprint does "
                f"not match {artifact_id}."
            )

    return actual_references


def _expected_evidence_contracts(
    record: P4ReviewEvidenceRecord,
) -> dict[str, tuple[str, str, str]]:
    information_unit = record.information_unit

    result = {
        information_unit.information_unit_id: (
            P4_INFORMATION_UNIT_ARTIFACT_TYPE,
            P4_INFORMATION_UNIT_EVIDENCE_ROLE,
            information_unit.content_fingerprint,
        )
    }

    for candidate in (
        record.terminology_mapping_candidates
    ):
        result[
            candidate
            .terminology_mapping_candidate_id
        ] = (
            P4_TERMINOLOGY_MAPPING_ARTIFACT_TYPE,
            P4_TERMINOLOGY_MAPPING_EVIDENCE_ROLE,
            candidate.content_fingerprint,
        )

    for candidate in (
        record.framework_assignment_candidates
    ):
        result[
            candidate
            .framework_assignment_candidate_id
        ] = (
            P4_FRAMEWORK_ASSIGNMENT_ARTIFACT_TYPE,
            P4_FRAMEWORK_ASSIGNMENT_EVIDENCE_ROLE,
            candidate.content_fingerprint,
        )

    for decision in record.human_review_decisions:
        result[
            decision.human_review_decision_id
        ] = (
            P4_HUMAN_REVIEW_ARTIFACT_TYPE,
            P4_HUMAN_REVIEW_EVIDENCE_ROLE,
            decision.decision_fingerprint,
        )

    expected_count = (
        1
        + len(
            record.terminology_mapping_candidates
        )
        + len(
            record.framework_assignment_candidates
        )
        + len(record.human_review_decisions)
    )

    if len(result) != expected_count:
        raise ReviewIntegrityError(
            "P4 artifact identities must be globally "
            "unique within one Information Unit record."
        )

    return result


def _construct_information_unit_content(
    information_unit: InformationUnit,
) -> ReviewItemContent:
    return ReviewItemContent(
        title=(
            f"{_display_information_type(information_unit.information_type)} "
            f"{information_unit.information_unit_id}"
        ),
        primary_text=(
            information_unit.interpreted_statement
        ),
        description=(
            _information_unit_description(
                information_unit
            )
        ),
        information_type=(
            information_unit.information_type
        ),
        modality=(
            information_unit.statement_modality
        ),
        epistemic_status=(
            information_unit.epistemic_class
        ),
        human_rationale=None,
        human_confidence=None,
        relationship_representation=None,
    )


def _construct_information_unit_selections(
    information_unit: InformationUnit,
) -> tuple[ReviewDimensionSelection, ...]:
    source_reference_ids = (
        information_unit.information_unit_id,
    )

    source_values = _unique_preserving_order(
        (
            information_unit.source_id,
            information_unit.source_projection_id,
            *(
                (
                    f"{anchor.segment_id}:"
                    f"{anchor.start_offset}-"
                    f"{anchor.end_offset}"
                )
                for anchor
                in information_unit.source_anchors
            ),
        )
    )

    return (
        ReviewDimensionSelection(
            dimension="content",
            selected_values=(
                information_unit
                .interpreted_statement,
            ),
            value_origin="agent_proposal",
            source_reference_ids=(
                source_reference_ids
            ),
            rationale=(
                _INITIAL_P4_DRAFT_RATIONALE
            ),
            selected_by=None,
            selected_at=None,
        ),
        ReviewDimensionSelection(
            dimension="classification",
            selected_values=(
                information_unit.information_type,
                information_unit.statement_modality,
                information_unit.epistemic_class,
            ),
            value_origin="agent_proposal",
            source_reference_ids=(
                source_reference_ids
            ),
            rationale=(
                _INITIAL_P4_DRAFT_RATIONALE
            ),
            selected_by=None,
            selected_at=None,
        ),
        ReviewDimensionSelection(
            dimension="source_assignment",
            selected_values=source_values,
            value_origin="agent_proposal",
            source_reference_ids=(
                source_reference_ids
            ),
            rationale=(
                _INITIAL_P4_DRAFT_RATIONALE
            ),
            selected_by=None,
            selected_at=None,
        ),
    )


def _information_unit_description(
    information_unit: InformationUnit,
) -> str:
    parts = [
        (
            "Extraction confidence "
            f"{information_unit.confidence}: "
            f"{information_unit.confidence_rationale}"
        )
    ]

    if (
        information_unit.derivation_rationale
        is not None
    ):
        parts.append(
            "Derivation rationale: "
            f"{information_unit.derivation_rationale}"
        )

    if information_unit.missing_evidence is not None:
        parts.append(
            "Missing evidence: "
            f"{information_unit.missing_evidence}"
        )

    return " ".join(parts)


def _review_item_kind_for_information_type(
    information_type: str,
) -> str:
    if (
        information_type
        in P4_OPEN_QUESTION_INFORMATION_TYPES
    ):
        return "open_question"

    return "element"


def _display_information_type(
    information_type: str,
) -> str:
    return information_type.replace(
        "_",
        " ",
    ).title()


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


def _unique_preserving_order(
    values: Iterable[str],
) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return tuple(result)


def _evidence_sort_key(
    reference: ReviewEvidenceReference,
) -> tuple[str, str, str, str]:
    return (
        reference.artifact_reference.artifact_id,
        reference.evidence_role,
        reference.evidence_locator,
        reference.evidence_content_fingerprint,
    )


def _evidence_reference_key(
    reference: ReviewEvidenceReference,
) -> tuple[
    tuple[str, str, str, str],
    str,
    str,
    str,
]:
    artifact = reference.artifact_reference

    return (
        (
            artifact.artifact_type,
            artifact.artifact_id,
            artifact.content_fingerprint,
            artifact.repository_relative_path,
        ),
        reference.evidence_role,
        reference.evidence_locator,
        reference.evidence_content_fingerprint,
    )
