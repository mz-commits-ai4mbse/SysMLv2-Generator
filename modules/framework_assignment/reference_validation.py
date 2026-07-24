"""Read-only validation of Framework Assignment Candidate references."""

from __future__ import annotations

from dataclasses import dataclass

from modules.framework import (
    FrameworkTemplateError,
    mapping_target_ids,
    validate_framework_template,
)
from modules.information_units.types import InformationUnit
from modules.project_glossary.types import ProjectGlossary
from modules.project_sources.types import SourceManifest
from modules.semantics.types import (
    TuringCoreConcept,
    TuringCoreVocabulary,
)
from modules.terminology_mapping.types import (
    TerminologyMappingCandidate,
)
from modules.terminology_mapping.reference_validation import (
    TerminologyMappingReferenceValidationResult,
)

from .errors import FrameworkAssignmentReferenceError
from .types import (
    FrameworkAssignmentCandidate,
    FrameworkAssignmentIssue,
    FrameworkAssignmentProposal,
)


@dataclass(frozen=True, slots=True)
class FrameworkAssignmentReferenceValidationResult:
    """Read-only validation result for one assignment candidate."""

    project_id: str
    framework_assignment_candidate_id: str
    checked_proposal_count: int
    references_valid: bool
    issues: tuple[FrameworkAssignmentIssue, ...]


def validate_framework_assignment_references(
    candidate: FrameworkAssignmentCandidate,
    *,
    information_unit: InformationUnit,
    source_manifest: SourceManifest,
    framework_template: dict[str, object],
    terminology_mapping_candidates: tuple[
        TerminologyMappingCandidate,
        ...,
    ],
    terminology_reference_validation_results: tuple[
        TerminologyMappingReferenceValidationResult,
        ...,
    ],
    turing_core_vocabulary: TuringCoreVocabulary,
    project_glossary: ProjectGlossary,
) -> FrameworkAssignmentReferenceValidationResult:
    """Validate assignment targets and all declared upstream snapshots."""

    _require_inputs(
        candidate,
        information_unit,
        source_manifest,
        framework_template,
        terminology_mapping_candidates,
        terminology_reference_validation_results,
        turing_core_vocabulary,
        project_glossary,
    )
    issues: list[FrameworkAssignmentIssue] = []
    try:
        validate_framework_template(framework_template)
        permitted_targets = mapping_target_ids(framework_template)
    except FrameworkTemplateError as exc:
        _issue(
            issues,
            candidate,
            "invalid_framework_template",
            f"Framework Template is invalid: {exc}",
        )
        permitted_targets = set()

    _validate_context(
        candidate,
        information_unit,
        source_manifest,
        framework_template,
        turing_core_vocabulary,
        project_glossary,
        issues,
    )
    terminology_by_id = {
        item.terminology_mapping_candidate_id: item
        for item in terminology_mapping_candidates
    }
    validation_by_id = {
        item.terminology_mapping_candidate_id: item
        for item in terminology_reference_validation_results
    }
    _validate_terminology_collection(
        candidate,
        terminology_by_id,
        validation_by_id,
        issues,
    )
    turing_by_id = {
        concept.concept_id: concept
        for concept in turing_core_vocabulary.concepts
    }

    nodes = {
        node["node_id"]: node
        for node in framework_template.get("nodes", [])
        if isinstance(node, dict)
        and isinstance(node.get("node_id"), str)
    }
    for index, proposal in enumerate(candidate.proposals, start=1):
        _validate_proposal(
            candidate,
            proposal,
            index,
            permitted_targets,
            nodes,
            information_unit,
            terminology_by_id,
            turing_by_id,
            turing_core_vocabulary,
            issues,
        )

    ordered = tuple(
        sorted(
            issues,
            key=lambda item: (
                item.issue_level,
                item.code,
                item.message,
            ),
        )
    )
    return FrameworkAssignmentReferenceValidationResult(
        project_id=candidate.project_id,
        framework_assignment_candidate_id=(
            candidate.framework_assignment_candidate_id
        ),
        checked_proposal_count=len(candidate.proposals),
        references_valid=not any(
            item.issue_level == "blocking"
            for item in ordered
        ),
        issues=ordered,
    )


def _require_inputs(
    candidate: object,
    information_unit: object,
    source_manifest: object,
    framework_template: object,
    terminology_candidates: object,
    terminology_results: object,
    vocabulary: object,
    glossary: object,
) -> None:
    expected = (
        (
            candidate,
            FrameworkAssignmentCandidate,
            "candidate",
        ),
        (
            information_unit,
            InformationUnit,
            "information_unit",
        ),
        (
            source_manifest,
            SourceManifest,
            "source_manifest",
        ),
        (
            vocabulary,
            TuringCoreVocabulary,
            "turing_core_vocabulary",
        ),
        (
            glossary,
            ProjectGlossary,
            "project_glossary",
        ),
    )
    for value, data_type, label in expected:
        if not isinstance(value, data_type):
            raise FrameworkAssignmentReferenceError(
                f"{label} must be a {data_type.__name__}."
            )
    if not isinstance(framework_template, dict):
        raise FrameworkAssignmentReferenceError(
            "framework_template must be a dictionary."
        )
    if not isinstance(terminology_candidates, tuple) or not all(
        isinstance(item, TerminologyMappingCandidate)
        for item in terminology_candidates
    ):
        raise FrameworkAssignmentReferenceError(
            "terminology_mapping_candidates must be a tuple of "
            "TerminologyMappingCandidate values."
        )
    if not isinstance(terminology_results, tuple) or not all(
        isinstance(
            item,
            TerminologyMappingReferenceValidationResult,
        )
        for item in terminology_results
    ):
        raise FrameworkAssignmentReferenceError(
            "terminology_reference_validation_results must be a tuple "
            "of TerminologyMappingReferenceValidationResult values."
        )
    terminology_ids = tuple(
        item.terminology_mapping_candidate_id
        for item in terminology_candidates
    )
    validation_ids = tuple(
        item.terminology_mapping_candidate_id
        for item in terminology_results
    )
    if len(terminology_ids) != len(set(terminology_ids)):
        raise FrameworkAssignmentReferenceError(
            "Duplicate Terminology Mapping Candidates are not allowed."
        )
    if len(validation_ids) != len(set(validation_ids)):
        raise FrameworkAssignmentReferenceError(
            "Duplicate terminology validation results are not allowed."
        )


def _validate_context(
    candidate: FrameworkAssignmentCandidate,
    unit: InformationUnit,
    source: SourceManifest,
    template: dict[str, object],
    vocabulary: TuringCoreVocabulary,
    glossary: ProjectGlossary,
    issues: list[FrameworkAssignmentIssue],
) -> None:
    bindings = (
        (
            "candidate_information_unit_project",
            candidate.project_id,
            unit.project_id,
        ),
        (
            "candidate_information_unit_source",
            candidate.source_id,
            unit.source_id,
        ),
        (
            "candidate_information_unit_projection",
            candidate.source_projection_id,
            unit.source_projection_id,
        ),
        (
            "candidate_information_unit_id",
            candidate.information_unit_id,
            unit.information_unit_id,
        ),
        (
            "source_manifest_project",
            candidate.project_id,
            source.project_id,
        ),
        (
            "source_manifest_source",
            candidate.source_id,
            source.source_id,
        ),
        (
            "project_glossary_project",
            candidate.project_id,
            glossary.project_id,
        ),
        (
            "framework_template_id",
            candidate.framework_template_id,
            template.get("template_id"),
        ),
        (
            "framework_template_version",
            candidate.framework_template_version,
            template.get("template_version"),
        ),
        (
            "turing_core_version",
            candidate.turing_core_version,
            vocabulary.vocabulary_version,
        ),
        (
            "project_glossary_revision",
            candidate.project_glossary_revision,
            glossary.glossary_revision,
        ),
    )
    for code, expected, actual in bindings:
        if expected != actual:
            _issue(
                issues,
                candidate,
                f"{code}_mismatch",
                (
                    f"{code} expected {expected!r}, but supplied "
                    f"authority contains {actual!r}."
                ),
            )

    mapping = template.get("information_unit_mapping")
    eligible_roles = (
        mapping.get("eligible_source_roles", [])
        if isinstance(mapping, dict)
        else []
    )
    if source.source_role not in eligible_roles:
        _issue(
            issues,
            candidate,
            "source_role_not_framework_eligible",
            (
                f"Source role {source.source_role!r} is not eligible "
                "for Framework Assignment."
            ),
        )
    if source.source_role == "context_only":
        _issue(
            issues,
            candidate,
            "context_only_source_assignment_forbidden",
            "context_only sources must not create Framework Assignments.",
        )


def _validate_terminology_collection(
    candidate: FrameworkAssignmentCandidate,
    candidates: dict[str, TerminologyMappingCandidate],
    results: dict[
        str,
        TerminologyMappingReferenceValidationResult,
    ],
    issues: list[FrameworkAssignmentIssue],
) -> None:
    declared = set(candidate.terminology_mapping_candidate_ids)
    supplied = set(candidates)
    if declared != supplied:
        _issue(
            issues,
            candidate,
            "terminology_candidate_collection_mismatch",
            (
                f"Declared Terminology Mapping Candidates "
                f"{sorted(declared)!r} do not match supplied "
                f"{sorted(supplied)!r}."
            ),
        )
    if declared != set(results):
        _issue(
            issues,
            candidate,
            "terminology_validation_collection_mismatch",
            "Terminology validation results do not exactly cover the "
            "declared Terminology Mapping Candidates.",
        )
    for identifier in sorted(declared & supplied):
        item = candidates[identifier]
        if (
            item.project_id != candidate.project_id
            or item.source_id != candidate.source_id
            or item.source_projection_id
            != candidate.source_projection_id
            or item.information_unit_id
            != candidate.information_unit_id
        ):
            _issue(
                issues,
                candidate,
                "terminology_candidate_context_mismatch",
                (
                    f"Terminology Mapping Candidate {identifier!r} "
                    "does not share the assignment context."
                ),
            )
        validation = results.get(identifier)
        if validation is not None and not validation.references_valid:
            _issue(
                issues,
                candidate,
                "terminology_candidate_references_invalid",
                (
                    f"Terminology Mapping Candidate {identifier!r} "
                    "has not passed reference validation."
                ),
            )


def _validate_proposal(
    candidate: FrameworkAssignmentCandidate,
    proposal: FrameworkAssignmentProposal,
    index: int,
    permitted_targets: set[str],
    nodes: dict[str, dict[str, object]],
    unit: InformationUnit,
    terminology: dict[str, TerminologyMappingCandidate],
    turing: dict[str, TuringCoreConcept],
    vocabulary: TuringCoreVocabulary,
    issues: list[FrameworkAssignmentIssue],
) -> None:
    node_id = proposal.framework_node_id
    node = nodes.get(node_id)
    if node is None:
        _issue(
            issues,
            candidate,
            "framework_node_not_found",
            f"Proposal {index} references unknown node {node_id!r}.",
        )
    elif node_id not in permitted_targets:
        _issue(
            issues,
            candidate,
            "framework_node_not_mapping_target",
            (
                f"Proposal {index} node {node_id!r} is not an "
                "approved mapping target."
            ),
        )

    information_bases = tuple(
        basis
        for basis in proposal.assignment_bases
        if basis.basis_type == "information_unit"
    )
    if not any(
        basis.reference_id == unit.information_unit_id
        and basis.reference_version == unit.content_fingerprint
        for basis in information_bases
    ):
        _issue(
            issues,
            candidate,
            "information_unit_basis_mismatch",
            (
                f"Proposal {index} does not bind the exact "
                "Information Unit fingerprint."
            ),
        )

    for basis in proposal.assignment_bases:
        if basis.basis_type == "terminology_mapping_candidate":
            mapped = terminology.get(basis.reference_id)
            if mapped is None:
                _issue(
                    issues,
                    candidate,
                    "terminology_basis_not_found",
                    (
                        f"Proposal {index} references unknown "
                        f"Terminology Mapping Candidate "
                        f"{basis.reference_id!r}."
                    ),
                )
            elif basis.reference_version != mapped.content_fingerprint:
                _issue(
                    issues,
                    candidate,
                    "terminology_basis_fingerprint_mismatch",
                    (
                        f"Proposal {index} terminology basis does not "
                        "match the candidate fingerprint."
                    ),
                )
        elif basis.basis_type == "turing_core_concept":
            concept = turing.get(basis.reference_id)
            if concept is None:
                _issue(
                    issues,
                    candidate,
                    "turing_core_basis_not_found",
                    (
                        f"Proposal {index} references unknown Turing "
                        f"Core Concept {basis.reference_id!r}."
                    ),
                )
            else:
                if basis.reference_version != (
                    vocabulary.vocabulary_version
                ):
                    _issue(
                        issues,
                        candidate,
                        "turing_core_basis_version_mismatch",
                        (
                            f"Proposal {index} Turing Core basis "
                            "version is stale."
                        ),
                    )
                if node_id not in (
                    concept.candidate_framework_node_ids
                ):
                    _issue(
                        issues,
                        candidate,
                        "turing_core_framework_target_conflict",
                        (
                            f"Turing Core Concept {concept.concept_id!r} "
                            f"does not nominate node {node_id!r} as a "
                            "candidate framework target."
                        ),
                    )


def _issue(
    issues: list[FrameworkAssignmentIssue],
    candidate: FrameworkAssignmentCandidate,
    code: str,
    message: str,
) -> None:
    issues.append(
        FrameworkAssignmentIssue(
            project_id=candidate.project_id,
            code=code,
            message=message,
            issue_level="blocking",
            information_unit_id=candidate.information_unit_id,
            framework_assignment_candidate_id=(
                candidate.framework_assignment_candidate_id
            ),
        )
    )