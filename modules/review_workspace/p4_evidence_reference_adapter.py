"""Bind validated P4 evidence to exact persisted project artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath

from modules.framework_assignment import (
    FrameworkAssignmentCandidate,
    FrameworkAssignmentError,
    framework_assignment_candidate_to_json,
)
from modules.human_review import (
    HumanReviewDecision,
    HumanReviewError,
    human_review_decision_to_json,
)
from modules.information_units import (
    InformationUnit,
    InformationUnitError,
    information_unit_to_json,
)
from modules.project_processing import (
    ProcessingArtifactReference,
    ProcessingValidationError,
    create_processing_artifact_reference,
)
from modules.terminology_mapping import (
    TerminologyMappingCandidate,
    TerminologyMappingError,
    terminology_mapping_candidate_to_json,
)

from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
)
from .p4_evidence_adapter import (
    P4ReviewEvidenceRecord,
    P4ReviewEvidenceSet,
)
from .types import ReviewEvidenceReference


P4_INFORMATION_UNIT_EVIDENCE_ROLE = (
    "p4_information_unit"
)
P4_TERMINOLOGY_MAPPING_EVIDENCE_ROLE = (
    "p4_terminology_mapping"
)
P4_FRAMEWORK_ASSIGNMENT_EVIDENCE_ROLE = (
    "p4_framework_assignment"
)
P4_HUMAN_REVIEW_EVIDENCE_ROLE = (
    "p4_human_review_decision"
)

P4_INFORMATION_UNIT_ARTIFACT_TYPE = (
    "information_units"
)
P4_TERMINOLOGY_MAPPING_ARTIFACT_TYPE = (
    "terminology_mapping_candidates"
)
P4_FRAMEWORK_ASSIGNMENT_ARTIFACT_TYPE = (
    "framework_assignment_candidates"
)
P4_HUMAN_REVIEW_ARTIFACT_TYPE = (
    "human_review_decisions"
)


@dataclass(frozen=True, slots=True)
class P4InformationUnitEvidenceReferences:
    """Exact persisted P4 evidence for one Information Unit."""

    information_unit_id: str
    information_unit_reference: ReviewEvidenceReference
    terminology_mapping_references: tuple[
        ReviewEvidenceReference,
        ...,
    ]
    framework_assignment_references: tuple[
        ReviewEvidenceReference,
        ...,
    ]
    human_review_references: tuple[
        ReviewEvidenceReference,
        ...,
    ]

    @property
    def all_evidence_references(
        self,
    ) -> tuple[ReviewEvidenceReference, ...]:
        """Return all P4 evidence references in stable order."""

        return (
            (self.information_unit_reference,)
            + self.terminology_mapping_references
            + self.framework_assignment_references
            + self.human_review_references
        )


@dataclass(frozen=True, slots=True)
class P4StructuredEvidenceReferenceSet:
    """Exact persisted P4 references for one selected Source."""

    project_id: str
    source_id: str
    records: tuple[
        P4InformationUnitEvidenceReferences,
        ...,
    ]

    def evidence_for_information_unit(
        self,
        information_unit_id: str,
    ) -> P4InformationUnitEvidenceReferences:
        """Return exact evidence for one Information Unit."""

        matches = tuple(
            record
            for record in self.records
            if record.information_unit_id
            == information_unit_id
        )

        if not matches:
            raise ReviewReferenceError(
                "No P4 evidence references exist for "
                f"Information Unit {information_unit_id!r}."
            )

        if len(matches) != 1:
            raise ReviewIntegrityError(
                "P4 Information Unit evidence identities "
                "must be unique."
            )

        return matches[0]


def construct_p4_evidence_references(
    p4_evidence: object,
    *,
    repository_root: Path | str,
) -> P4StructuredEvidenceReferenceSet:
    """Bind validated P4 evidence to exact persisted JSON files.

    The operation is deterministic and read-only. It does not infer
    any relationship between P4 Information Units and P9 subjects.
    """

    if not isinstance(
        p4_evidence,
        P4ReviewEvidenceSet,
    ):
        raise ReviewValidationError(
            "p4_evidence must be a "
            "P4ReviewEvidenceSet."
        )

    root = _validated_repository_root(
        repository_root
    )

    records = tuple(
        sorted(
            p4_evidence.records,
            key=lambda item: (
                item.information_unit
                .information_unit_id
            ),
        )
    )

    information_unit_ids: set[str] = set()
    global_artifact_keys: set[
        tuple[str, str]
    ] = set()
    bound_records: list[
        P4InformationUnitEvidenceReferences
    ] = []

    for record in records:
        if not isinstance(
            record,
            P4ReviewEvidenceRecord,
        ):
            raise ReviewValidationError(
                "P4 evidence records must be "
                "P4ReviewEvidenceRecord values."
            )

        _validate_record_binding(
            record,
            project_id=p4_evidence.project_id,
            source_id=p4_evidence.source_id,
        )

        information_unit_id = (
            record.information_unit
            .information_unit_id
        )

        if information_unit_id in information_unit_ids:
            raise ReviewIntegrityError(
                "P4 evidence records must contain unique "
                "Information Unit identities."
            )

        information_unit_ids.add(
            information_unit_id
        )

        information_unit_reference = (
            _bind_information_unit(
                record.information_unit,
                repository_root=root,
                global_artifact_keys=(
                    global_artifact_keys
                ),
            )
        )

        terminology_references = tuple(
            _bind_terminology_mapping_candidate(
                candidate,
                repository_root=root,
                global_artifact_keys=(
                    global_artifact_keys
                ),
            )
            for candidate in sorted(
                record.terminology_mapping_candidates,
                key=lambda item: (
                    item
                    .terminology_mapping_candidate_id
                ),
            )
        )

        framework_references = tuple(
            _bind_framework_assignment_candidate(
                candidate,
                repository_root=root,
                global_artifact_keys=(
                    global_artifact_keys
                ),
            )
            for candidate in sorted(
                record.framework_assignment_candidates,
                key=lambda item: (
                    item
                    .framework_assignment_candidate_id
                ),
            )
        )

        human_review_references = tuple(
            _bind_human_review_decision(
                decision,
                repository_root=root,
                global_artifact_keys=(
                    global_artifact_keys
                ),
            )
            for decision in sorted(
                record.human_review_decisions,
                key=lambda item: (
                    item.human_review_decision_id
                ),
            )
        )

        bound_records.append(
            P4InformationUnitEvidenceReferences(
                information_unit_id=(
                    information_unit_id
                ),
                information_unit_reference=(
                    information_unit_reference
                ),
                terminology_mapping_references=(
                    terminology_references
                ),
                framework_assignment_references=(
                    framework_references
                ),
                human_review_references=(
                    human_review_references
                ),
            )
        )

    return P4StructuredEvidenceReferenceSet(
        project_id=p4_evidence.project_id,
        source_id=p4_evidence.source_id,
        records=tuple(bound_records),
    )


def _validate_record_binding(
    record: P4ReviewEvidenceRecord,
    *,
    project_id: str,
    source_id: str,
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

    if information_unit.project_id != project_id:
        raise ReviewIntegrityError(
            "P4 Information Unit does not belong to "
            "the selected Project."
        )

    if information_unit.source_id != source_id:
        raise ReviewIntegrityError(
            "P4 Information Unit does not belong to "
            "the selected Source."
        )

    candidate_target_keys: set[
        tuple[str, str]
    ] = {
        (
            "information_unit_publication",
            information_unit.information_unit_id,
        ),
    }

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

        _validate_candidate_binding(
            candidate,
            information_unit=information_unit,
            label="Terminology Mapping Candidate",
        )

        candidate_target_keys.add(
            (
                "terminology_mapping_candidate",
                candidate
                .terminology_mapping_candidate_id,
            )
        )

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

        _validate_candidate_binding(
            candidate,
            information_unit=information_unit,
            label="Framework Assignment Candidate",
        )

        candidate_target_keys.add(
            (
                "framework_assignment_candidate",
                candidate
                .framework_assignment_candidate_id,
            )
        )

    for decision in record.human_review_decisions:
        if not isinstance(
            decision,
            HumanReviewDecision,
        ):
            raise ReviewValidationError(
                "P4 review entries must be "
                "HumanReviewDecision values."
            )

        if decision.project_id != project_id:
            raise ReviewIntegrityError(
                "P4 Human Review Decision does not "
                "belong to the selected Project."
            )

        target_key = (
            decision.target.target_type,
            decision.target.target_id,
        )

        if target_key not in candidate_target_keys:
            raise ReviewReferenceError(
                "P4 Human Review Decision is not "
                "associated with its containing "
                "Information Unit record."
            )


def _validate_candidate_binding(
    candidate: (
        TerminologyMappingCandidate
        | FrameworkAssignmentCandidate
    ),
    *,
    information_unit: InformationUnit,
    label: str,
) -> None:
    for field_name in (
        "project_id",
        "source_id",
        "source_projection_id",
        "information_unit_id",
    ):
        if getattr(candidate, field_name) != getattr(
            information_unit,
            field_name,
        ):
            raise ReviewIntegrityError(
                f"{label} disagrees with its "
                f"Information Unit on {field_name}."
            )


def _bind_information_unit(
    value: InformationUnit,
    *,
    repository_root: Path,
    global_artifact_keys: set[
        tuple[str, str]
    ],
) -> ReviewEvidenceReference:
    try:
        serialized = information_unit_to_json(
            value
        )
    except InformationUnitError as exc:
        raise ReviewValidationError(
            "Unable to serialize selected "
            "Information Unit."
        ) from exc

    relative_path = PurePosixPath(
        "data",
        "projects",
        value.project_id,
        "semantics",
        "information_units",
        f"{value.information_unit_id}.json",
    )

    return _bind_persisted_artifact(
        repository_root=repository_root,
        relative_path=relative_path,
        serialized=serialized,
        artifact_type=(
            P4_INFORMATION_UNIT_ARTIFACT_TYPE
        ),
        artifact_id=value.information_unit_id,
        evidence_role=(
            P4_INFORMATION_UNIT_EVIDENCE_ROLE
        ),
        evidence_content_fingerprint=(
            value.content_fingerprint
        ),
        global_artifact_keys=global_artifact_keys,
    )


def _bind_terminology_mapping_candidate(
    value: TerminologyMappingCandidate,
    *,
    repository_root: Path,
    global_artifact_keys: set[
        tuple[str, str]
    ],
) -> ReviewEvidenceReference:
    try:
        serialized = (
            terminology_mapping_candidate_to_json(
                value
            )
        )
    except TerminologyMappingError as exc:
        raise ReviewValidationError(
            "Unable to serialize selected Terminology "
            "Mapping Candidate."
        ) from exc

    relative_path = PurePosixPath(
        "data",
        "projects",
        value.project_id,
        "semantics",
        "terminology_mappings",
        (
            f"{value.terminology_mapping_candidate_id}"
            ".json"
        ),
    )

    return _bind_persisted_artifact(
        repository_root=repository_root,
        relative_path=relative_path,
        serialized=serialized,
        artifact_type=(
            P4_TERMINOLOGY_MAPPING_ARTIFACT_TYPE
        ),
        artifact_id=(
            value.terminology_mapping_candidate_id
        ),
        evidence_role=(
            P4_TERMINOLOGY_MAPPING_EVIDENCE_ROLE
        ),
        evidence_content_fingerprint=(
            value.content_fingerprint
        ),
        global_artifact_keys=global_artifact_keys,
    )


def _bind_framework_assignment_candidate(
    value: FrameworkAssignmentCandidate,
    *,
    repository_root: Path,
    global_artifact_keys: set[
        tuple[str, str]
    ],
) -> ReviewEvidenceReference:
    try:
        serialized = (
            framework_assignment_candidate_to_json(
                value
            )
        )
    except FrameworkAssignmentError as exc:
        raise ReviewValidationError(
            "Unable to serialize selected Framework "
            "Assignment Candidate."
        ) from exc

    relative_path = PurePosixPath(
        "data",
        "projects",
        value.project_id,
        "semantics",
        "framework_assignments",
        (
            f"{value.framework_assignment_candidate_id}"
            ".json"
        ),
    )

    return _bind_persisted_artifact(
        repository_root=repository_root,
        relative_path=relative_path,
        serialized=serialized,
        artifact_type=(
            P4_FRAMEWORK_ASSIGNMENT_ARTIFACT_TYPE
        ),
        artifact_id=(
            value.framework_assignment_candidate_id
        ),
        evidence_role=(
            P4_FRAMEWORK_ASSIGNMENT_EVIDENCE_ROLE
        ),
        evidence_content_fingerprint=(
            value.content_fingerprint
        ),
        global_artifact_keys=global_artifact_keys,
    )


def _bind_human_review_decision(
    value: HumanReviewDecision,
    *,
    repository_root: Path,
    global_artifact_keys: set[
        tuple[str, str]
    ],
) -> ReviewEvidenceReference:
    try:
        serialized = (
            human_review_decision_to_json(value)
        )
    except HumanReviewError as exc:
        raise ReviewValidationError(
            "Unable to serialize selected Human "
            "Review Decision."
        ) from exc

    relative_path = PurePosixPath(
        "data",
        "projects",
        value.project_id,
        "semantics",
        "human_reviews",
        f"{value.human_review_decision_id}.json",
    )

    return _bind_persisted_artifact(
        repository_root=repository_root,
        relative_path=relative_path,
        serialized=serialized,
        artifact_type=(
            P4_HUMAN_REVIEW_ARTIFACT_TYPE
        ),
        artifact_id=(
            value.human_review_decision_id
        ),
        evidence_role=(
            P4_HUMAN_REVIEW_EVIDENCE_ROLE
        ),
        evidence_content_fingerprint=(
            value.decision_fingerprint
        ),
        global_artifact_keys=global_artifact_keys,
    )


def _bind_persisted_artifact(
    *,
    repository_root: Path,
    relative_path: PurePosixPath,
    serialized: str,
    artifact_type: str,
    artifact_id: str,
    evidence_role: str,
    evidence_content_fingerprint: str,
    global_artifact_keys: set[
        tuple[str, str]
    ],
) -> ReviewEvidenceReference:
    artifact_key = (
        artifact_type,
        artifact_id,
    )

    if artifact_key in global_artifact_keys:
        raise ReviewIntegrityError(
            "P4 artifacts must not be bound more "
            f"than once: {artifact_type}/{artifact_id}."
        )

    target = repository_root.joinpath(
        *relative_path.parts
    )

    _validate_regular_project_file(
        target,
        repository_root=repository_root,
        artifact_id=artifact_id,
    )

    try:
        content = target.read_bytes()
    except OSError as exc:
        raise ReviewReferenceError(
            "Unable to read persisted P4 artifact: "
            f"{artifact_id}."
        ) from exc

    if not content:
        raise ReviewIntegrityError(
            "Persisted P4 artifact must not be empty: "
            f"{artifact_id}."
        )

    try:
        persisted_text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReviewReferenceError(
            "Persisted P4 artifact is not valid UTF-8: "
            f"{artifact_id}."
        ) from exc

    if persisted_text != serialized:
        raise ReviewIntegrityError(
            "Persisted P4 artifact does not match its "
            f"validated canonical value: {artifact_id}."
        )

    file_fingerprint = hashlib.sha256(
        content
    ).hexdigest()

    try:
        artifact_reference = (
            create_processing_artifact_reference(
                artifact_type=artifact_type,
                artifact_id=artifact_id,
                content_fingerprint=(
                    file_fingerprint
                ),
                repository_relative_path=(
                    relative_path.as_posix()
                ),
            )
        )
    except ProcessingValidationError as exc:
        raise ReviewValidationError(
            "Unable to create a valid Processing "
            "Artifact Reference for P4 evidence."
        ) from exc

    global_artifact_keys.add(artifact_key)

    return ReviewEvidenceReference(
        artifact_reference=artifact_reference,
        evidence_role=evidence_role,
        evidence_locator="/",
        evidence_content_fingerprint=(
            evidence_content_fingerprint
        ),
    )


def _validate_regular_project_file(
    target: Path,
    *,
    repository_root: Path,
    artifact_id: str,
) -> None:
    current = repository_root

    try:
        relative_parts = target.relative_to(
            repository_root
        ).parts
    except ValueError as exc:
        raise ReviewReferenceError(
            "P4 artifact path escapes repository_root: "
            f"{artifact_id}."
        ) from exc

    for part in relative_parts:
        current = current / part

        if current.is_symlink():
            raise ReviewReferenceError(
                "P4 artifact path must not contain "
                f"symbolic links: {artifact_id}."
            )

    try:
        resolved_root = repository_root.resolve(
            strict=True
        )
        resolved_target = target.resolve(
            strict=True
        )
        resolved_target.relative_to(resolved_root)
    except FileNotFoundError as exc:
        raise ReviewReferenceError(
            "Persisted P4 artifact does not exist: "
            f"{artifact_id}."
        ) from exc
    except ValueError as exc:
        raise ReviewReferenceError(
            "P4 artifact path escapes repository_root: "
            f"{artifact_id}."
        ) from exc
    except OSError as exc:
        raise ReviewReferenceError(
            "Persisted P4 artifact cannot be resolved: "
            f"{artifact_id}."
        ) from exc

    if not target.is_file():
        raise ReviewReferenceError(
            "Persisted P4 artifact is not a regular "
            f"file: {artifact_id}."
        )


def _validated_repository_root(
    repository_root: Path | str,
) -> Path:
    try:
        root = Path(repository_root)
    except TypeError as exc:
        raise ReviewValidationError(
            "repository_root must be a filesystem path."
        ) from exc

    if root.is_symlink():
        raise ReviewReferenceError(
            "repository_root must not be a symbolic link."
        )

    if not root.exists() or not root.is_dir():
        raise ReviewReferenceError(
            "repository_root must be an existing directory."
        )

    return root
