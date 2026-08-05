"""Associate validated P4 semantic evidence with one P9 review set."""

from __future__ import annotations

from dataclasses import dataclass

from modules.framework_assignment import (
    FrameworkAssignmentCandidate,
    FrameworkAssignmentError,
    FrameworkAssignmentScanResult,
    validate_framework_assignment_candidate,
)
from modules.human_review import (
    HumanReviewDecision,
    HumanReviewError,
    HumanReviewScanResult,
    validate_human_review_decision,
)
from modules.information_units import (
    InformationUnit,
    InformationUnitError,
    InformationUnitScanResult,
    validate_information_unit,
)
from modules.terminology_mapping import (
    TerminologyMappingCandidate,
    TerminologyMappingError,
    TerminologyMappingScanResult,
    validate_terminology_mapping_candidate,
)

from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
)
from .evidence_adapter import P9ReviewEvidenceSet


@dataclass(frozen=True, slots=True)
class P4ReviewEvidenceRecord:
    """P4 evidence associated with one Information Unit."""

    information_unit: InformationUnit
    terminology_mapping_candidates: tuple[
        TerminologyMappingCandidate,
        ...,
    ]
    framework_assignment_candidates: tuple[
        FrameworkAssignmentCandidate,
        ...,
    ]
    human_review_decisions: tuple[
        HumanReviewDecision,
        ...,
    ]


@dataclass(frozen=True, slots=True)
class P4ReviewEvidenceSet:
    """Deterministic P4 enrichment for one P9 Review Evidence Set."""

    project_id: str
    source_id: str
    records: tuple[P4ReviewEvidenceRecord, ...]

    @property
    def information_units(
        self,
    ) -> tuple[InformationUnit, ...]:
        """Return associated Information Units in stable order."""

        return tuple(
            record.information_unit
            for record in self.records
        )


def select_p4_review_evidence_set(
    p9_evidence: object,
    *,
    information_unit_scan: object,
    terminology_mapping_scan: object,
    framework_assignment_scan: object,
    human_review_scan: object,
) -> P4ReviewEvidenceSet:
    """Associate clean P4 evidence with the selected P9 Source.

    P4 evidence enriches Review Items. It does not replace the P9
    Processing Run, Attempt or primary Review Report binding.
    """

    if not isinstance(p9_evidence, P9ReviewEvidenceSet):
        raise ReviewValidationError(
            "p9_evidence must be a P9ReviewEvidenceSet."
        )

    information_scan = _require_scan_type(
        information_unit_scan,
        InformationUnitScanResult,
        "information_unit_scan",
    )
    terminology_scan = _require_scan_type(
        terminology_mapping_scan,
        TerminologyMappingScanResult,
        "terminology_mapping_scan",
    )
    framework_scan = _require_scan_type(
        framework_assignment_scan,
        FrameworkAssignmentScanResult,
        "framework_assignment_scan",
    )
    review_scan = _require_scan_type(
        human_review_scan,
        HumanReviewScanResult,
        "human_review_scan",
    )

    _require_clean_scan(
        "Information Unit",
        information_scan.issues,
    )
    _require_clean_scan(
        "Terminology Mapping",
        terminology_scan.issues,
    )
    _require_clean_scan(
        "Framework Assignment",
        framework_scan.issues,
    )
    _require_clean_scan(
        "P4 Human Review",
        review_scan.issues,
    )

    information_units = _validated_information_units(
        information_scan.information_units,
        project_id=p9_evidence.project_id,
    )
    terminology_candidates = (
        _validated_terminology_candidates(
            terminology_scan.candidates,
            project_id=p9_evidence.project_id,
        )
    )
    framework_candidates = (
        _validated_framework_candidates(
            framework_scan.candidates,
            project_id=p9_evidence.project_id,
        )
    )
    decisions = _validated_decisions(
        review_scan.decisions,
        project_id=p9_evidence.project_id,
    )

    information_units_by_id = {
        item.information_unit_id: item
        for item in information_units
    }

    terminology_by_id = {
        item.terminology_mapping_candidate_id: item
        for item in terminology_candidates
    }

    framework_by_id = {
        item.framework_assignment_candidate_id: item
        for item in framework_candidates
    }

    _validate_candidate_information_unit_bindings(
        information_units_by_id,
        terminology_candidates,
        framework_candidates,
    )

    _validate_framework_terminology_bindings(
        terminology_by_id,
        framework_candidates,
    )

    target_fingerprints = _target_fingerprint_index(
        information_units,
        terminology_candidates,
        framework_candidates,
    )

    _validate_decision_targets(
        decisions,
        target_fingerprints,
    )

    selected_information_units = tuple(
        item
        for item in information_units
        if item.source_id == p9_evidence.source_id
    )

    selected_information_unit_ids = {
        item.information_unit_id
        for item in selected_information_units
    }

    selected_terminology = tuple(
        item
        for item in terminology_candidates
        if item.information_unit_id
        in selected_information_unit_ids
    )

    selected_framework = tuple(
        item
        for item in framework_candidates
        if item.information_unit_id
        in selected_information_unit_ids
    )

    for candidate in selected_framework:
        if (
            candidate.framework_template_id
            != p9_evidence.framework_template.template_id
            or candidate.framework_template_version
            != p9_evidence.framework_template.template_version
        ):
            raise ReviewIntegrityError(
                "A selected P4 Framework Assignment Candidate "
                "does not match the P9 framework template."
            )

    terminology_by_information_unit = _group_by_information_unit(
        selected_terminology,
    )
    framework_by_information_unit = _group_by_information_unit(
        selected_framework,
    )

    selected_target_keys = {
        (
            "information_unit_publication",
            item.information_unit_id,
        )
        for item in selected_information_units
    }
    selected_target_keys.update(
        (
            "terminology_mapping_candidate",
            item.terminology_mapping_candidate_id,
        )
        for item in selected_terminology
    )
    selected_target_keys.update(
        (
            "framework_assignment_candidate",
            item.framework_assignment_candidate_id,
        )
        for item in selected_framework
    )

    decisions_by_target: dict[
        tuple[str, str],
        list[HumanReviewDecision],
    ] = {}

    for decision in decisions:
        key = (
            decision.target.target_type,
            decision.target.target_id,
        )

        if key not in selected_target_keys:
            continue

        decisions_by_target.setdefault(
            key,
            [],
        ).append(decision)

    records: list[P4ReviewEvidenceRecord] = []

    for information_unit in selected_information_units:
        information_unit_id = (
            information_unit.information_unit_id
        )

        terminology = terminology_by_information_unit.get(
            information_unit_id,
            (),
        )
        framework = framework_by_information_unit.get(
            information_unit_id,
            (),
        )

        target_keys = [
            (
                "information_unit_publication",
                information_unit_id,
            ),
        ]
        target_keys.extend(
            (
                "terminology_mapping_candidate",
                candidate.terminology_mapping_candidate_id,
            )
            for candidate in terminology
        )
        target_keys.extend(
            (
                "framework_assignment_candidate",
                candidate.framework_assignment_candidate_id,
            )
            for candidate in framework
        )

        associated_decisions = tuple(
            sorted(
                (
                    decision
                    for key in target_keys
                    for decision in decisions_by_target.get(
                        key,
                        (),
                    )
                ),
                key=lambda item: (
                    item.human_review_decision_id
                ),
            )
        )

        records.append(
            P4ReviewEvidenceRecord(
                information_unit=information_unit,
                terminology_mapping_candidates=terminology,
                framework_assignment_candidates=framework,
                human_review_decisions=(
                    associated_decisions
                ),
            )
        )

    return P4ReviewEvidenceSet(
        project_id=p9_evidence.project_id,
        source_id=p9_evidence.source_id,
        records=tuple(records),
    )


def _require_scan_type(
    value: object,
    expected_type: type,
    label: str,
):
    if not isinstance(value, expected_type):
        raise ReviewValidationError(
            f"{label} must be a "
            f"{expected_type.__name__}."
        )

    return value


def _require_clean_scan(
    label: str,
    issues: object,
) -> None:
    if not isinstance(issues, tuple):
        raise ReviewValidationError(
            f"{label} scan issues must be a tuple."
        )

    if not issues:
        return

    first = issues[0]
    code = getattr(first, "code", "unknown_issue")

    raise ReviewIntegrityError(
        f"{label} scan contains {len(issues)} issue(s); "
        f"first issue: {code}."
    )


def _validated_information_units(
    values: object,
    *,
    project_id: str,
) -> tuple[InformationUnit, ...]:
    if not isinstance(values, tuple):
        raise ReviewValidationError(
            "Information Units must be a tuple."
        )

    validated: list[InformationUnit] = []

    for value in values:
        try:
            validate_information_unit(value)
        except InformationUnitError as exc:
            raise ReviewValidationError(
                "P4 contains an invalid Information Unit."
            ) from exc

        if value.project_id != project_id:
            raise ReviewIntegrityError(
                "P4 Information Units must remain in the "
                "selected Project."
            )

        validated.append(value)

    _require_unique_identity_and_fingerprint(
        validated,
        identity_attribute="information_unit_id",
        fingerprint_attribute="content_fingerprint",
        label="Information Unit",
    )

    return tuple(
        sorted(
            validated,
            key=lambda item: item.information_unit_id,
        )
    )


def _validated_terminology_candidates(
    values: object,
    *,
    project_id: str,
) -> tuple[TerminologyMappingCandidate, ...]:
    if not isinstance(values, tuple):
        raise ReviewValidationError(
            "Terminology Mapping Candidates must be a tuple."
        )

    validated: list[TerminologyMappingCandidate] = []

    for value in values:
        try:
            validate_terminology_mapping_candidate(value)
        except TerminologyMappingError as exc:
            raise ReviewValidationError(
                "P4 contains an invalid Terminology "
                "Mapping Candidate."
            ) from exc

        if value.project_id != project_id:
            raise ReviewIntegrityError(
                "P4 Terminology Mapping Candidates must "
                "remain in the selected Project."
            )

        validated.append(value)

    _require_unique_identity_and_fingerprint(
        validated,
        identity_attribute=(
            "terminology_mapping_candidate_id"
        ),
        fingerprint_attribute="content_fingerprint",
        label="Terminology Mapping Candidate",
    )

    return tuple(
        sorted(
            validated,
            key=lambda item: (
                item.terminology_mapping_candidate_id
            ),
        )
    )


def _validated_framework_candidates(
    values: object,
    *,
    project_id: str,
) -> tuple[FrameworkAssignmentCandidate, ...]:
    if not isinstance(values, tuple):
        raise ReviewValidationError(
            "Framework Assignment Candidates must be "
            "a tuple."
        )

    validated: list[FrameworkAssignmentCandidate] = []

    for value in values:
        try:
            validate_framework_assignment_candidate(
                value
            )
        except FrameworkAssignmentError as exc:
            raise ReviewValidationError(
                "P4 contains an invalid Framework "
                "Assignment Candidate."
            ) from exc

        if value.project_id != project_id:
            raise ReviewIntegrityError(
                "P4 Framework Assignment Candidates "
                "must remain in the selected Project."
            )

        validated.append(value)

    _require_unique_identity_and_fingerprint(
        validated,
        identity_attribute=(
            "framework_assignment_candidate_id"
        ),
        fingerprint_attribute="content_fingerprint",
        label="Framework Assignment Candidate",
    )

    return tuple(
        sorted(
            validated,
            key=lambda item: (
                item.framework_assignment_candidate_id
            ),
        )
    )


def _validated_decisions(
    values: object,
    *,
    project_id: str,
) -> tuple[HumanReviewDecision, ...]:
    if not isinstance(values, tuple):
        raise ReviewValidationError(
            "P4 Human Review Decisions must be a tuple."
        )

    validated: list[HumanReviewDecision] = []

    for value in values:
        try:
            validate_human_review_decision(value)
        except HumanReviewError as exc:
            raise ReviewValidationError(
                "P4 contains an invalid Human Review "
                "Decision."
            ) from exc

        if value.project_id != project_id:
            raise ReviewIntegrityError(
                "P4 Human Review Decisions must remain "
                "in the selected Project."
            )

        validated.append(value)

    _require_unique_identity_and_fingerprint(
        validated,
        identity_attribute=(
            "human_review_decision_id"
        ),
        fingerprint_attribute="decision_fingerprint",
        label="Human Review Decision",
    )

    return tuple(
        sorted(
            validated,
            key=lambda item: (
                item.human_review_decision_id
            ),
        )
    )


def _validate_candidate_information_unit_bindings(
    information_units_by_id: dict[str, InformationUnit],
    terminology_candidates: tuple[
        TerminologyMappingCandidate,
        ...,
    ],
    framework_candidates: tuple[
        FrameworkAssignmentCandidate,
        ...,
    ],
) -> None:
    for candidate in (
        terminology_candidates
        + framework_candidates
    ):
        information_unit = information_units_by_id.get(
            candidate.information_unit_id
        )

        if information_unit is None:
            raise ReviewReferenceError(
                "A P4 Candidate references an unavailable "
                f"Information Unit: "
                f"{candidate.information_unit_id}."
            )

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
                    "A P4 Candidate disagrees with its "
                    f"Information Unit on {field_name}."
                )


def _validate_framework_terminology_bindings(
    terminology_by_id: dict[
        str,
        TerminologyMappingCandidate,
    ],
    framework_candidates: tuple[
        FrameworkAssignmentCandidate,
        ...,
    ],
) -> None:
    for framework_candidate in framework_candidates:
        for terminology_id in (
            framework_candidate
            .terminology_mapping_candidate_ids
        ):
            terminology_candidate = (
                terminology_by_id.get(terminology_id)
            )

            if terminology_candidate is None:
                raise ReviewReferenceError(
                    "A Framework Assignment Candidate "
                    "references an unavailable Terminology "
                    f"Mapping Candidate: {terminology_id}."
                )

            if (
                terminology_candidate.information_unit_id
                != framework_candidate.information_unit_id
            ):
                raise ReviewIntegrityError(
                    "A Framework Assignment Candidate and "
                    "its Terminology Mapping Candidate must "
                    "refer to the same Information Unit."
                )


def _target_fingerprint_index(
    information_units: tuple[InformationUnit, ...],
    terminology_candidates: tuple[
        TerminologyMappingCandidate,
        ...,
    ],
    framework_candidates: tuple[
        FrameworkAssignmentCandidate,
        ...,
    ],
) -> dict[tuple[str, str], str]:
    result = {
        (
            "information_unit_publication",
            item.information_unit_id,
        ): item.content_fingerprint
        for item in information_units
    }

    result.update(
        {
            (
                "terminology_mapping_candidate",
                item.terminology_mapping_candidate_id,
            ): item.content_fingerprint
            for item in terminology_candidates
        }
    )

    result.update(
        {
            (
                "framework_assignment_candidate",
                item.framework_assignment_candidate_id,
            ): item.content_fingerprint
            for item in framework_candidates
        }
    )

    return result


def _validate_decision_targets(
    decisions: tuple[HumanReviewDecision, ...],
    target_fingerprints: dict[
        tuple[str, str],
        str,
    ],
) -> None:
    for decision in decisions:
        key = (
            decision.target.target_type,
            decision.target.target_id,
        )
        expected_fingerprint = (
            target_fingerprints.get(key)
        )

        if expected_fingerprint is None:
            raise ReviewReferenceError(
                "A P4 Human Review Decision references "
                "an unavailable target: "
                f"{decision.target.target_type}/"
                f"{decision.target.target_id}."
            )

        if (
            decision.target.target_content_fingerprint
            != expected_fingerprint
        ):
            raise ReviewIntegrityError(
                "A P4 Human Review Decision does not bind "
                "the current immutable target fingerprint."
            )


def _group_by_information_unit(
    values: tuple,
) -> dict[str, tuple]:
    grouped: dict[str, list] = {}

    for value in values:
        grouped.setdefault(
            value.information_unit_id,
            [],
        ).append(value)

    return {
        information_unit_id: tuple(items)
        for information_unit_id, items
        in grouped.items()
    }


def _require_unique_identity_and_fingerprint(
    values: list,
    *,
    identity_attribute: str,
    fingerprint_attribute: str,
    label: str,
) -> None:
    identities: set[str] = set()
    fingerprints: set[str] = set()

    for value in values:
        identity = getattr(
            value,
            identity_attribute,
        )
        fingerprint = getattr(
            value,
            fingerprint_attribute,
        )

        if identity in identities:
            raise ReviewIntegrityError(
                f"{label} identities must be unique."
            )

        if fingerprint in fingerprints:
            raise ReviewIntegrityError(
                f"{label} fingerprints must be unique."
            )

        identities.add(identity)
        fingerprints.add(fingerprint)
