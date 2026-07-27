"""Compose validated P3-P5 evidence into one regenerable P6 assessment."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields, is_dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from modules.framework import (
    DEFAULT_FRAMEWORK_TEMPLATE_PATH,
    load_framework_template,
)
from modules.framework_assignment.reference_validation import (
    FrameworkAssignmentReferenceValidationResult,
    validate_framework_assignment_references,
)
from modules.framework_assignment.repository import (
    FrameworkAssignmentRepository,
)
from modules.framework_assignment.types import (
    FrameworkAssignmentCandidate,
)
from modules.human_review.repository import HumanReviewRepository
from modules.information_units.repository import InformationUnitRepository
from modules.project_glossary.repository import ProjectGlossaryRepository
from modules.project_processing import (
    DEFAULT_PROJECTS_ROOT,
    ProjectProcessingOperations,
    derive_processing_artifact_lifecycles,
    derive_source_processing_summaries,
)
from modules.project_sources import ProjectSourceRegistry
from modules.semantics import (
    OntologyRegistry,
    ReferenceConceptIndex,
    TuringCoreVocabulary,
    generate_reference_concept_index,
    load_ontology_registry,
    load_turing_core_vocabulary,
)
from modules.terminology_mapping.reference_validation import (
    TerminologyMappingReferenceValidationResult,
    validate_terminology_mapping_references,
)
from modules.terminology_mapping.repository import (
    TerminologyMappingRepository,
)
from modules.human_review.types import HumanReviewDecision
from modules.information_units.types import InformationUnit
from modules.project_processing.types import (
    ProcessingArtifactLifecycle,
    SourceProcessingSummary,
)
from modules.project_sources.types import SourceManifest
from modules.project_workspace.identifiers import is_valid_project_id

from .coverage import (
    PRELIMINARY_COVERAGE_ALGORITHM_ID,
    PRELIMINARY_COVERAGE_ALGORITHM_VERSION,
    derive_project_preliminary_coverage,
)
from .errors import (
    CoverageAssessmentError,
    CoverageIntegrityError,
    CoverageReferenceError,
    CoverageValidationError,
    ProjectCoverageError,
)
from .evidence import (
    calculate_framework_assignment_reference_validation_fingerprint,
    derive_framework_assignment_coverage_evidence,
)
from .profile import (
    DEFAULT_PRELIMINARY_SUPPORT_PROFILE_PATH,
    calculate_preliminary_support_profile_fingerprint,
    load_preliminary_support_profile,
    validate_preliminary_support_profile_instance,
)
from .support import (
    PRELIMINARY_SUPPORT_ALGORITHM_ID,
    PRELIMINARY_SUPPORT_ALGORITHM_VERSION,
    derive_potential_support_assessments,
    potential_support_by_id,
)
from .types import (
    APPROVED_READINESS_STATUSES,
    COVERAGE_ISSUE_LEVELS,
    CoverageIssue,
    FrameworkLevelCoverage,
    FrameworkNodeCoverage,
    PotentialSupportAssessment,
    PreliminarySupportProfile,
    ProjectCoverageAssessment,
)


PROJECT_COVERAGE_ASSESSMENT_ALGORITHM_ID = (
    "TURING_PROJECT_COVERAGE_ASSESSMENT"
)
PROJECT_COVERAGE_ASSESSMENT_ALGORITHM_VERSION = "1.0.0"
APPROVED_READINESS_STATUS = "not_available"
APPROVED_READINESS_AVAILABLE_FROM_PHASE = "G"


@dataclass(frozen=True, slots=True)
class ProjectCoverageInputBundle:
    """Validated project-local inputs required for one P6 assessment."""

    framework_template: dict[str, Any]
    support_profile: PreliminarySupportProfile
    source_manifests: tuple[SourceManifest, ...]
    source_processing_summaries: tuple[SourceProcessingSummary, ...]
    information_units: tuple[InformationUnit, ...]
    framework_assignment_candidates: tuple[
        FrameworkAssignmentCandidate,
        ...,
    ]
    reference_validation_results: tuple[
        FrameworkAssignmentReferenceValidationResult,
        ...,
    ]
    human_review_decisions: tuple[HumanReviewDecision, ...]
    artifact_lifecycles: tuple[ProcessingArtifactLifecycle, ...] = ()
    issues: tuple[CoverageIssue, ...] = ()


ProjectCoverageInputProvider = Callable[
    [str],
    ProjectCoverageInputBundle,
]


@dataclass(frozen=True, slots=True)
class ProjectCoverageSemanticReferences:
    """Exact global semantic snapshots used for P4 reference validation."""

    turing_core_vocabulary: TuringCoreVocabulary
    ontology_registry: OntologyRegistry
    reference_concept_index: ReferenceConceptIndex


SemanticReferenceProvider = Callable[
    [],
    ProjectCoverageSemanticReferences,
]
FrameworkTemplateProvider = Callable[[], dict[str, Any]]
SupportProfileProvider = Callable[
    [dict[str, Any]],
    PreliminarySupportProfile,
]


class ProjectCoverageRepositoryInputProvider:
    """Collect authoritative project-local P3-P5 inputs without mutation."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        repository_root: Path | str = Path("."),
        framework_template_path: Path | str = (
            DEFAULT_FRAMEWORK_TEMPLATE_PATH
        ),
        support_profile_path: Path | str = (
            DEFAULT_PRELIMINARY_SUPPORT_PROFILE_PATH
        ),
        source_registry: object | None = None,
        processing_operations: object | None = None,
        information_unit_repository: object | None = None,
        terminology_mapping_repository: object | None = None,
        framework_assignment_repository: object | None = None,
        human_review_repository: object | None = None,
        project_glossary_repository: object | None = None,
        framework_template_provider: (
            FrameworkTemplateProvider | None
        ) = None,
        support_profile_provider: SupportProfileProvider | None = None,
        semantic_reference_provider: (
            SemanticReferenceProvider | None
        ) = None,
        terminology_reference_validator: Callable[..., object] = (
            validate_terminology_mapping_references
        ),
        framework_reference_validator: Callable[..., object] = (
            validate_framework_assignment_references
        ),
        source_summary_deriver: Callable[..., object] = (
            derive_source_processing_summaries
        ),
        artifact_lifecycle_deriver: Callable[..., object] = (
            derive_processing_artifact_lifecycles
        ),
    ) -> None:
        self.root = Path(root)
        self.repository_root = Path(repository_root)
        self.framework_template_path = Path(framework_template_path)
        self.support_profile_path = Path(support_profile_path)
        self._source_registry = (
            ProjectSourceRegistry(root=self.root)
            if source_registry is None
            else source_registry
        )
        self._processing_operations = (
            ProjectProcessingOperations(root=self.root)
            if processing_operations is None
            else processing_operations
        )
        self._information_units = (
            InformationUnitRepository(root=self.root)
            if information_unit_repository is None
            else information_unit_repository
        )
        self._terminology_mappings = (
            TerminologyMappingRepository(root=self.root)
            if terminology_mapping_repository is None
            else terminology_mapping_repository
        )
        self._framework_assignments = (
            FrameworkAssignmentRepository(root=self.root)
            if framework_assignment_repository is None
            else framework_assignment_repository
        )
        self._human_reviews = (
            HumanReviewRepository(root=self.root)
            if human_review_repository is None
            else human_review_repository
        )
        self._project_glossary = (
            ProjectGlossaryRepository(root=self.root)
            if project_glossary_repository is None
            else project_glossary_repository
        )
        self._framework_template_provider = (
            self._load_framework_template
            if framework_template_provider is None
            else framework_template_provider
        )
        self._support_profile_provider = (
            self._load_support_profile
            if support_profile_provider is None
            else support_profile_provider
        )
        self._semantic_reference_provider = (
            self._load_semantic_references
            if semantic_reference_provider is None
            else semantic_reference_provider
        )
        self._terminology_reference_validator = (
            terminology_reference_validator
        )
        self._framework_reference_validator = (
            framework_reference_validator
        )
        self._source_summary_deriver = source_summary_deriver
        self._artifact_lifecycle_deriver = artifact_lifecycle_deriver
        for value, label in (
            (self._framework_template_provider, "framework_template_provider"),
            (self._support_profile_provider, "support_profile_provider"),
            (self._semantic_reference_provider, "semantic_reference_provider"),
            (
                self._terminology_reference_validator,
                "terminology_reference_validator",
            ),
            (
                self._framework_reference_validator,
                "framework_reference_validator",
            ),
            (self._source_summary_deriver, "source_summary_deriver"),
            (
                self._artifact_lifecycle_deriver,
                "artifact_lifecycle_deriver",
            ),
        ):
            if not callable(value):
                raise CoverageValidationError(f"{label} must be callable.")

    def __call__(self, project_id: str) -> ProjectCoverageInputBundle:
        """Scan one project and assemble exact, regenerable assessment inputs."""

        validated_project_id = _validate_project_id(project_id)
        framework_template = self._framework_template_provider()
        support_profile = self._support_profile_provider(
            framework_template
        )

        source_scan = self._source_registry.scan_sources(
            validated_project_id
        )
        processing_scan = self._processing_operations.scan_project(
            validated_project_id
        )
        information_scan = self._information_units.scan_information_units(
            validated_project_id
        )
        terminology_scan = self._terminology_mappings.scan_candidates(
            validated_project_id
        )
        assignment_scan = self._framework_assignments.scan_candidates(
            validated_project_id
        )
        review_scan = self._human_reviews.scan_decisions(
            validated_project_id
        )

        issues: list[CoverageIssue] = []
        issues.extend(
            _translate_scan_issues(
                validated_project_id,
                "source_scan",
                source_scan.source_issues,
            )
        )
        issues.extend(
            _translate_scan_issues(
                validated_project_id,
                "processing_scan",
                processing_scan.issues,
            )
        )
        issues.extend(
            _translate_scan_issues(
                validated_project_id,
                "information_unit_scan",
                information_scan.issues,
            )
        )
        issues.extend(
            _translate_scan_issues(
                validated_project_id,
                "terminology_mapping_scan",
                terminology_scan.issues,
            )
        )
        issues.extend(
            _translate_scan_issues(
                validated_project_id,
                "framework_assignment_scan",
                assignment_scan.issues,
            )
        )
        issues.extend(
            _translate_scan_issues(
                validated_project_id,
                "human_review_scan",
                review_scan.issues,
            )
        )

        source_summaries = self._derive_source_summaries(
            validated_project_id,
            source_scan,
            processing_scan,
            issues,
        )
        artifact_lifecycles = self._derive_artifact_lifecycles(
            validated_project_id,
            processing_scan,
            issues,
        )
        reference_validation_results = (
            self._derive_framework_reference_validations(
                validated_project_id,
                framework_template,
                source_scan.valid_sources,
                information_scan.information_units,
                terminology_scan.candidates,
                assignment_scan.candidates,
                issues,
            )
        )

        return ProjectCoverageInputBundle(
            framework_template=framework_template,
            support_profile=support_profile,
            source_manifests=source_scan.valid_sources,
            source_processing_summaries=source_summaries,
            information_units=information_scan.information_units,
            framework_assignment_candidates=(
                assignment_scan.candidates
            ),
            reference_validation_results=(
                reference_validation_results
            ),
            human_review_decisions=review_scan.decisions,
            artifact_lifecycles=artifact_lifecycles,
            issues=_ordered_unique_issues(
                validated_project_id,
                tuple(issues),
            ),
        )

    def _derive_source_summaries(
        self,
        project_id: str,
        source_scan: object,
        processing_scan: object,
        issues: list[CoverageIssue],
    ) -> tuple[SourceProcessingSummary, ...]:
        try:
            result = self._source_summary_deriver(
                project_id,
                source_scan,
                processing_scan,
            )
        except Exception as exc:
            issues.append(
                _integration_issue(
                    project_id,
                    "source_processing_summary_failed",
                    str(exc),
                )
            )
            return ()
        if not isinstance(result, tuple) or not all(
            isinstance(item, SourceProcessingSummary) for item in result
        ):
            raise CoverageIntegrityError(
                "source_summary_deriver returned an invalid result."
            )
        return result

    def _derive_artifact_lifecycles(
        self,
        project_id: str,
        processing_scan: object,
        issues: list[CoverageIssue],
    ) -> tuple[ProcessingArtifactLifecycle, ...]:
        try:
            result = self._artifact_lifecycle_deriver(
                processing_scan.run_histories
            )
        except Exception as exc:
            issues.append(
                _integration_issue(
                    project_id,
                    "artifact_lifecycle_derivation_failed",
                    str(exc),
                )
            )
            return ()
        if not isinstance(result, tuple) or not all(
            isinstance(item, ProcessingArtifactLifecycle)
            for item in result
        ):
            raise CoverageIntegrityError(
                "artifact_lifecycle_deriver returned an invalid result."
            )
        return result

    def _derive_framework_reference_validations(
        self,
        project_id: str,
        framework_template: dict[str, Any],
        sources: tuple[SourceManifest, ...],
        information_units: tuple[InformationUnit, ...],
        terminology_candidates: tuple[object, ...],
        assignment_candidates: tuple[
            FrameworkAssignmentCandidate,
            ...,
        ],
        issues: list[CoverageIssue],
    ) -> tuple[FrameworkAssignmentReferenceValidationResult, ...]:
        if not assignment_candidates:
            return ()

        try:
            glossary = self._project_glossary.load_glossary(project_id)
        except Exception as exc:
            issues.append(
                _integration_issue(
                    project_id,
                    "project_glossary_unavailable",
                    str(exc),
                )
            )
            return ()
        try:
            semantic_references = self._semantic_reference_provider()
        except Exception as exc:
            issues.append(
                _integration_issue(
                    project_id,
                    "semantic_references_unavailable",
                    str(exc),
                )
            )
            return ()
        if not isinstance(
            semantic_references,
            ProjectCoverageSemanticReferences,
        ):
            raise CoverageIntegrityError(
                "semantic_reference_provider returned an invalid result."
            )

        terminology_results = self._derive_terminology_validations(
            project_id,
            terminology_candidates,
            glossary,
            semantic_references,
            issues,
        )
        sources_by_id = _index_repository_records(
            project_id,
            sources,
            "source_id",
            "Source Manifest",
        )
        units_by_id = _index_repository_records(
            project_id,
            information_units,
            "information_unit_id",
            "Information Unit",
        )
        results: list[FrameworkAssignmentReferenceValidationResult] = []
        for candidate in sorted(
            assignment_candidates,
            key=lambda item: item.framework_assignment_candidate_id,
        ):
            source = sources_by_id.get(candidate.source_id)
            unit = units_by_id.get(candidate.information_unit_id)
            if source is None or unit is None:
                issues.append(
                    _integration_issue(
                        project_id,
                        "framework_validation_input_missing",
                        "Framework Assignment Candidate cannot be reference-"
                        "validated because its Source Manifest or Information "
                        "Unit is unavailable.",
                        source_id=candidate.source_id,
                        information_unit_id=candidate.information_unit_id,
                        framework_assignment_candidate_id=(
                            candidate.framework_assignment_candidate_id
                        ),
                    )
                )
                continue
            try:
                result = self._framework_reference_validator(
                    candidate,
                    information_unit=unit,
                    source_manifest=source,
                    framework_template=framework_template,
                    terminology_mapping_candidates=(
                        terminology_candidates
                    ),
                    terminology_reference_validation_results=(
                        terminology_results
                    ),
                    turing_core_vocabulary=(
                        semantic_references.turing_core_vocabulary
                    ),
                    project_glossary=glossary,
                )
            except Exception as exc:
                issues.append(
                    _integration_issue(
                        project_id,
                        "framework_reference_validation_failed",
                        str(exc),
                        source_id=candidate.source_id,
                        information_unit_id=candidate.information_unit_id,
                        framework_assignment_candidate_id=(
                            candidate.framework_assignment_candidate_id
                        ),
                    )
                )
                continue
            if not isinstance(
                result,
                FrameworkAssignmentReferenceValidationResult,
            ):
                raise CoverageIntegrityError(
                    "framework_reference_validator returned an invalid result."
                )
            results.append(result)
        return tuple(results)

    def _derive_terminology_validations(
        self,
        project_id: str,
        candidates: tuple[object, ...],
        glossary: object,
        semantic_references: ProjectCoverageSemanticReferences,
        issues: list[CoverageIssue],
    ) -> tuple[TerminologyMappingReferenceValidationResult, ...]:
        results: list[TerminologyMappingReferenceValidationResult] = []
        for candidate in sorted(
            candidates,
            key=lambda item: item.terminology_mapping_candidate_id,
        ):
            try:
                result = self._terminology_reference_validator(
                    candidate,
                    project_glossary=glossary,
                    turing_core_vocabulary=(
                        semantic_references.turing_core_vocabulary
                    ),
                    ontology_registry=(
                        semantic_references.ontology_registry
                    ),
                    reference_concept_index=(
                        semantic_references.reference_concept_index
                    ),
                )
            except Exception as exc:
                issues.append(
                    _integration_issue(
                        project_id,
                        "terminology_reference_validation_failed",
                        str(exc),
                        source_id=getattr(candidate, "source_id", None),
                        information_unit_id=getattr(
                            candidate,
                            "information_unit_id",
                            None,
                        ),
                    )
                )
                continue
            if not isinstance(
                result,
                TerminologyMappingReferenceValidationResult,
            ):
                raise CoverageIntegrityError(
                    "terminology_reference_validator returned an invalid "
                    "result."
                )
            results.append(result)
        return tuple(results)

    def _load_framework_template(self) -> dict[str, Any]:
        return load_framework_template(self.framework_template_path)

    def _load_support_profile(
        self,
        framework_template: dict[str, Any],
    ) -> PreliminarySupportProfile:
        return load_preliminary_support_profile(
            self.support_profile_path,
            framework_template=framework_template,
        )

    def _load_semantic_references(
        self,
    ) -> ProjectCoverageSemanticReferences:
        registry = load_ontology_registry(
            repository_root=self.repository_root,
            verify_snapshots=True,
        )
        vocabulary = load_turing_core_vocabulary(
            repository_root=self.repository_root,
            validate_references=True,
        )
        index = generate_reference_concept_index(
            registry,
            repository_root=self.repository_root,
        )
        return ProjectCoverageSemanticReferences(
            turing_core_vocabulary=vocabulary,
            ontology_registry=registry,
            reference_concept_index=index,
        )


def _validate_project_id(value: object) -> str:
    """Return one valid six-digit project ID or fail explicitly."""

    if not is_valid_project_id(value):
        raise CoverageValidationError(
            "project_id must be a six-digit numeric string."
        )
    return value


def calculate_project_coverage_assessment_fingerprint(
    project_id: str,
    inputs: ProjectCoverageInputBundle,
) -> str:
    """Bind all authoritative and derived assessment inputs deterministically."""

    validated_project_id = _validate_project_id(project_id)
    bundle = _validate_input_bundle(validated_project_id, inputs)
    payload = {
        "assessment_algorithm": {
            "id": PROJECT_COVERAGE_ASSESSMENT_ALGORITHM_ID,
            "version": PROJECT_COVERAGE_ASSESSMENT_ALGORITHM_VERSION,
        },
        "coverage_algorithm": {
            "id": PRELIMINARY_COVERAGE_ALGORITHM_ID,
            "version": PRELIMINARY_COVERAGE_ALGORITHM_VERSION,
        },
        "support_algorithm": {
            "id": PRELIMINARY_SUPPORT_ALGORITHM_ID,
            "version": PRELIMINARY_SUPPORT_ALGORITHM_VERSION,
        },
        "project_id": validated_project_id,
        "framework_template": _canonicalize(bundle.framework_template),
        "support_profile": _canonicalize(bundle.support_profile),
        "source_manifests": [
            _canonicalize(item)
            for item in sorted(
                bundle.source_manifests,
                key=lambda item: (item.project_id, item.source_id),
            )
        ],
        "source_processing_summaries": [
            _canonicalize(item)
            for item in sorted(
                bundle.source_processing_summaries,
                key=lambda item: (item.project_id, item.source_id),
            )
        ],
        "information_units": [
            _canonicalize(item)
            for item in sorted(
                bundle.information_units,
                key=lambda item: (
                    item.project_id,
                    item.information_unit_id,
                ),
            )
        ],
        "framework_assignment_candidates": [
            _canonicalize(item)
            for item in sorted(
                bundle.framework_assignment_candidates,
                key=lambda item: (
                    item.project_id,
                    item.framework_assignment_candidate_id,
                ),
            )
        ],
        "reference_validation_results": [
            {
                "result": _canonicalize(item),
                "validation_fingerprint": (
                    calculate_framework_assignment_reference_validation_fingerprint(
                        item
                    )
                ),
            }
            for item in sorted(
                bundle.reference_validation_results,
                key=lambda item: (
                    item.project_id,
                    item.framework_assignment_candidate_id,
                ),
            )
        ],
        "human_review_decisions": [
            _canonicalize(item)
            for item in sorted(
                bundle.human_review_decisions,
                key=lambda item: (
                    item.project_id,
                    item.human_review_decision_id,
                ),
            )
        ],
        "artifact_lifecycles": [
            _canonicalize(item)
            for item in sorted(
                bundle.artifact_lifecycles,
                key=lambda item: (
                    item.artifact_reference.artifact_type,
                    item.artifact_reference.artifact_id,
                    item.artifact_reference.content_fingerprint,
                ),
            )
        ],
        "issues": [
            _canonicalize(item)
            for item in _ordered_unique_issues(
                validated_project_id,
                bundle.issues,
            )
        ],
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def assemble_project_coverage_assessment(
    project_id: str,
    inputs: ProjectCoverageInputBundle,
) -> ProjectCoverageAssessment:
    """Derive one complete immutable P6 assessment from exact input records."""

    validated_project_id = _validate_project_id(project_id)
    bundle = _validate_input_bundle(validated_project_id, inputs)
    ordered_issues = _ordered_unique_issues(
        validated_project_id,
        bundle.issues,
    )

    evidence = derive_framework_assignment_coverage_evidence(
        validated_project_id,
        framework_template=bundle.framework_template,
        source_manifests=bundle.source_manifests,
        source_processing_summaries=(
            bundle.source_processing_summaries
        ),
        information_units=bundle.information_units,
        candidates=bundle.framework_assignment_candidates,
        reference_validation_results=(
            bundle.reference_validation_results
        ),
        human_review_decisions=bundle.human_review_decisions,
        artifact_lifecycles=bundle.artifact_lifecycles,
    )
    (
        node_coverages,
        level_coverages,
        project_coverage_state,
    ) = derive_project_preliminary_coverage(
        validated_project_id,
        bundle.framework_template,
        evidence,
        ordered_issues,
    )
    support_assessments = derive_potential_support_assessments(
        validated_project_id,
        bundle.support_profile,
        node_coverages,
        ordered_issues,
    )
    fingerprint = calculate_project_coverage_assessment_fingerprint(
        validated_project_id,
        bundle,
    )

    return ProjectCoverageAssessment(
        project_id=validated_project_id,
        framework_template_id=(
            bundle.framework_template["template_id"]
        ),
        framework_template_version=(
            bundle.framework_template["template_version"]
        ),
        support_profile_id=bundle.support_profile.profile_id,
        support_profile_version=(
            bundle.support_profile.profile_version
        ),
        project_coverage_state=project_coverage_state,
        node_coverages=node_coverages,
        level_coverages=level_coverages,
        support_assessments=support_assessments,
        approved_readiness_status=APPROVED_READINESS_STATUS,
        approved_readiness_available_from_phase=(
            APPROVED_READINESS_AVAILABLE_FROM_PHASE
        ),
        assessment_algorithm_id=(
            PROJECT_COVERAGE_ASSESSMENT_ALGORITHM_ID
        ),
        assessment_algorithm_version=(
            PROJECT_COVERAGE_ASSESSMENT_ALGORITHM_VERSION
        ),
        assessment_input_fingerprint=fingerprint,
        issues=ordered_issues,
    )


_DEFAULT_INPUT_PROVIDER = object()


class ProjectCoverageService:
    """Read-only facade over one project-local P6 input provider."""

    def __init__(
        self,
        input_provider: ProjectCoverageInputProvider | object = (
            _DEFAULT_INPUT_PROVIDER
        ),
        *,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        repository_root: Path | str = Path("."),
        repository_input_provider: (
            ProjectCoverageInputProvider | None
        ) = None,
    ) -> None:
        explicit_input = input_provider is not _DEFAULT_INPUT_PROVIDER
        if explicit_input and repository_input_provider is not None:
            raise CoverageValidationError(
                "Specify either input_provider or "
                "repository_input_provider, not both."
            )
        if explicit_input:
            provider = input_provider
        elif repository_input_provider is not None:
            provider = repository_input_provider
        else:
            provider = ProjectCoverageRepositoryInputProvider(
                root=root,
                repository_root=repository_root,
            )
        if not callable(provider):
            raise CoverageValidationError(
                "input_provider must be callable."
            )
        self._input_provider = provider

    def collect_inputs(
        self,
        project_id: str,
    ) -> ProjectCoverageInputBundle:
        """Collect and validate one exact project-local input bundle."""

        validated_project_id = _validate_project_id(project_id)
        try:
            inputs = self._input_provider(validated_project_id)
        except ProjectCoverageError:
            raise
        except Exception as exc:
            raise CoverageAssessmentError(
                "Unable to collect Project Coverage inputs for "
                f"{validated_project_id}."
            ) from exc
        return _validate_input_bundle(validated_project_id, inputs)

    def assess_project(
        self,
        project_id: str,
    ) -> ProjectCoverageAssessment:
        """Return the complete regenerable P6 project assessment."""

        validated_project_id = _validate_project_id(project_id)
        return assemble_project_coverage_assessment(
            validated_project_id,
            self.collect_inputs(validated_project_id),
        )

    def node_coverages(
        self,
        project_id: str,
    ) -> tuple[FrameworkNodeCoverage, ...]:
        """Return all ordered Framework Node Coverage records."""

        return self.assess_project(project_id).node_coverages

    def level_coverages(
        self,
        project_id: str,
    ) -> tuple[FrameworkLevelCoverage, ...]:
        """Return all ordered Framework Level Coverage records."""

        return self.assess_project(project_id).level_coverages

    def support_assessments(
        self,
        project_id: str,
    ) -> tuple[PotentialSupportAssessment, ...]:
        """Return all ordered potential-support assessments."""

        return self.assess_project(project_id).support_assessments

    def support_assessment(
        self,
        project_id: str,
        support_target_id: str,
    ) -> PotentialSupportAssessment:
        """Return one exact support target assessment."""

        return potential_support_by_id(
            self.support_assessments(project_id),
            support_target_id,
        )



def _translate_scan_issues(
    project_id: str,
    domain: str,
    upstream_issues: object,
) -> tuple[CoverageIssue, ...]:
    if not isinstance(upstream_issues, tuple):
        raise CoverageIntegrityError(
            f"{domain} issues must be a tuple."
        )
    translated: list[CoverageIssue] = []
    for issue in upstream_issues:
        issue_project_id = getattr(issue, "project_id", None)
        if issue_project_id != project_id:
            raise CoverageReferenceError(
                f"{domain} contains an issue from another project."
            )
        code = getattr(issue, "code", None)
        message = getattr(issue, "message", None)
        if not isinstance(code, str) or not code:
            raise CoverageIntegrityError(
                f"{domain} issue code must be a non-empty string."
            )
        if not isinstance(message, str) or not message:
            raise CoverageIntegrityError(
                f"{domain} issue message must be a non-empty string."
            )
        issue_level = getattr(issue, "issue_level", "blocking")
        if issue_level not in COVERAGE_ISSUE_LEVELS:
            raise CoverageIntegrityError(
                f"{domain} issue has an unsupported issue_level."
            )
        target_type = getattr(issue, "target_type", None)
        target_id = getattr(issue, "target_id", None)
        assignment_candidate_id = getattr(
            issue,
            "framework_assignment_candidate_id",
            None,
        )
        if (
            assignment_candidate_id is None
            and target_type == "framework_assignment_candidate"
        ):
            assignment_candidate_id = target_id
        translated.append(
            CoverageIssue(
                project_id=project_id,
                code=f"{domain}.{code}",
                message=message,
                issue_level=issue_level,
                path=getattr(issue, "path", None),
                source_id=getattr(issue, "source_id", None),
                information_unit_id=getattr(
                    issue,
                    "information_unit_id",
                    None,
                ),
                framework_assignment_candidate_id=(
                    assignment_candidate_id
                ),
                human_review_decision_id=getattr(
                    issue,
                    "human_review_decision_id",
                    None,
                ),
            )
        )
    return tuple(translated)


def _integration_issue(
    project_id: str,
    code: str,
    message: str,
    *,
    issue_level: str = "blocking",
    path: Path | None = None,
    source_id: str | None = None,
    information_unit_id: str | None = None,
    framework_assignment_candidate_id: str | None = None,
) -> CoverageIssue:
    return CoverageIssue(
        project_id=project_id,
        code=f"repository_integration.{code}",
        message=message or code,
        issue_level=issue_level,
        path=path,
        source_id=source_id,
        information_unit_id=information_unit_id,
        framework_assignment_candidate_id=(
            framework_assignment_candidate_id
        ),
    )


def _index_repository_records(
    project_id: str,
    values: tuple[Any, ...],
    identity_field: str,
    label: str,
) -> dict[str, Any]:
    indexed: dict[str, Any] = {}
    for item in values:
        if getattr(item, "project_id", None) != project_id:
            raise CoverageReferenceError(
                f"{label} belongs to another project."
            )
        identity = getattr(item, identity_field, None)
        if not isinstance(identity, str) or not identity:
            raise CoverageIntegrityError(
                f"{label} has no valid {identity_field}."
            )
        if identity in indexed:
            raise CoverageIntegrityError(
                f"Duplicate {label} identity: {identity}."
            )
        indexed[identity] = item
    return indexed


def _validate_input_bundle(
    project_id: str,
    inputs: object,
) -> ProjectCoverageInputBundle:
    if not isinstance(inputs, ProjectCoverageInputBundle):
        raise CoverageValidationError(
            "inputs must be a ProjectCoverageInputBundle."
        )
    if not isinstance(inputs.framework_template, dict):
        raise CoverageValidationError(
            "framework_template must be a dictionary."
        )

    validate_preliminary_support_profile_instance(
        inputs.support_profile,
        framework_template=inputs.framework_template,
    )
    expected_template_id = inputs.framework_template.get(
        "template_id"
    )
    expected_template_version = inputs.framework_template.get(
        "template_version"
    )
    if (
        inputs.support_profile.framework_template_id
        != expected_template_id
        or inputs.support_profile.framework_template_version
        != expected_template_version
    ):
        raise CoverageReferenceError(
            "Preliminary Support Profile does not bind the active "
            "Framework Template."
        )
    expected_profile_fingerprint = (
        calculate_preliminary_support_profile_fingerprint(
            inputs.support_profile
        )
    )
    if (
        expected_profile_fingerprint
        != inputs.support_profile.profile_fingerprint
    ):
        raise CoverageIntegrityError(
            "Preliminary Support Profile fingerprint mismatch."
        )

    _validate_project_collection(
        project_id,
        inputs.source_manifests,
        SourceManifest,
        "source_manifests",
    )
    _validate_project_collection(
        project_id,
        inputs.source_processing_summaries,
        SourceProcessingSummary,
        "source_processing_summaries",
    )
    _validate_project_collection(
        project_id,
        inputs.information_units,
        InformationUnit,
        "information_units",
    )
    _validate_project_collection(
        project_id,
        inputs.framework_assignment_candidates,
        FrameworkAssignmentCandidate,
        "framework_assignment_candidates",
    )
    _validate_project_collection(
        project_id,
        inputs.reference_validation_results,
        FrameworkAssignmentReferenceValidationResult,
        "reference_validation_results",
    )
    _validate_project_collection(
        project_id,
        inputs.human_review_decisions,
        HumanReviewDecision,
        "human_review_decisions",
    )
    _require_tuple_of(
        inputs.artifact_lifecycles,
        ProcessingArtifactLifecycle,
        "artifact_lifecycles",
    )
    _require_tuple_of(inputs.issues, CoverageIssue, "issues")
    _ordered_unique_issues(project_id, inputs.issues)

    if APPROVED_READINESS_STATUS not in APPROVED_READINESS_STATUSES:
        raise CoverageIntegrityError(
            "Configured Approved Readiness status is not supported."
        )
    return inputs


def _validate_project_collection(
    project_id: str,
    values: object,
    data_type: type,
    label: str,
) -> None:
    _require_tuple_of(values, data_type, label)
    for item in values:
        if getattr(item, "project_id", None) != project_id:
            raise CoverageReferenceError(
                f"{label} contains a record from another project."
            )


def _require_tuple_of(
    value: object,
    data_type: type,
    label: str,
) -> None:
    if not isinstance(value, tuple) or not all(
        isinstance(item, data_type) for item in value
    ):
        raise CoverageValidationError(
            f"{label} must be a tuple of {data_type.__name__} values."
        )


def _ordered_unique_issues(
    project_id: str,
    issues: tuple[CoverageIssue, ...],
) -> tuple[CoverageIssue, ...]:
    _require_tuple_of(issues, CoverageIssue, "issues")
    seen: set[tuple[Any, ...]] = set()
    ordered: list[CoverageIssue] = []
    for issue in issues:
        if issue.project_id != project_id:
            raise CoverageReferenceError(
                "Coverage Issue belongs to another project."
            )
        if issue.issue_level not in COVERAGE_ISSUE_LEVELS:
            raise CoverageValidationError(
                "Coverage Issue has an unsupported issue_level."
            )
        identity = (
            issue.code,
            issue.message,
            issue.issue_level,
            "" if issue.path is None else str(issue.path),
            issue.source_id,
            issue.information_unit_id,
            issue.framework_node_id,
            issue.framework_assignment_candidate_id,
            issue.human_review_decision_id,
            issue.support_target_id,
        )
        if identity in seen:
            raise CoverageIntegrityError(
                "Duplicate Coverage Issue identity."
            )
        seen.add(identity)
        ordered.append(issue)
    return tuple(
        sorted(
            ordered,
            key=lambda item: (
                item.issue_level,
                item.code,
                item.message,
                "" if item.path is None else str(item.path),
                "" if item.source_id is None else item.source_id,
                ""
                if item.information_unit_id is None
                else item.information_unit_id,
                ""
                if item.framework_node_id is None
                else item.framework_node_id,
                ""
                if item.framework_assignment_candidate_id is None
                else item.framework_assignment_candidate_id,
                ""
                if item.human_review_decision_id is None
                else item.human_review_decision_id,
                ""
                if item.support_target_id is None
                else item.support_target_id,
            ),
        )
    )


def _canonicalize(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonicalize(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (tuple, list)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(
            (_canonicalize(item) for item in value),
            key=lambda item: json.dumps(
                item,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise CoverageValidationError(
        "Assessment fingerprint contains an unsupported value type: "
        f"{type(value).__name__}."
    )
