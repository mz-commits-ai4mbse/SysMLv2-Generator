"""Persistent and project-isolated Project Glossary operations.

This P4 repository owns validated semantic persistence below one existing
Project Workspace. It does not create projects and does not grant Engineering
Approval.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import replace
from datetime import datetime, timezone
import errno
import os
from pathlib import Path
import re
from typing import Any

from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.errors import (
    ProjectNotFoundError,
    ProjectWorkspaceError,
)
from modules.project_workspace.identifiers import (
    is_valid_project_id,
)
from modules.project_workspace.workspace import (
    DEFAULT_PROJECTS_ROOT,
)

from .decision_manifest import (
    TERMINOLOGY_DECISIONS_DIRECTORY_NAME,
    create_terminology_decision,
    terminology_decision_filename,
    terminology_decision_from_json,
    terminology_decision_to_json,
)
from .errors import (
    AmbiguityGroupNotFoundError,
    InvalidTerminologyLifecycleTransitionError,
    ProjectConceptNotFoundError,
    ProjectGlossaryError,
    ProjectGlossaryIntegrityError,
    ProjectGlossaryNotFoundError,
    ProjectGlossaryPersistenceError,
    ProjectGlossaryValidationError,
    TerminologyDecisionError,
    UnsafeProjectGlossaryPathError,
)
from .identifiers import (
    allocate_next_ambiguity_group_id,
    allocate_next_project_concept_id,
    allocate_next_terminology_decision_id,
    is_valid_ambiguity_group_id,
    is_valid_project_concept_id,
    is_valid_terminology_decision_id,
)
from .manifest import (
    PROJECT_GLOSSARY_FILENAME,
    create_project_glossary,
    project_glossary_from_json,
    project_glossary_to_json,
)
from .types import (
    AmbiguityGroup,
    LocalizedGlossaryText,
    ProjectConcept,
    ProjectConceptProvenance,
    ProjectConceptRevision,
    ProjectExternalOntologyMapping,
    ProjectGlossary,
    ProjectGlossaryIssue,
    ProjectGlossaryScanResult,
    TerminologyDecision,
    TuringCoreConceptMapping,
)


SEMANTICS_DIRECTORY_NAME = "semantics"

_TERMINOLOGY_DECISION_FILE_PATTERN = re.compile(
    r"^(TD-[0-9]{6})\.json$"
)


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class ProjectGlossaryRepository:
    """Persist and load one isolated Project Glossary per project."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self.root = Path(root)
        self._clock = clock
        self._workspace = ProjectWorkspace(
            root=self.root,
            clock=clock,
        )

    def initialize_glossary(
        self,
        project_id: str,
        *,
        default_language: str,
    ) -> ProjectGlossary:
        """Create and atomically publish a project's first glossary."""

        project_path = self._project_path(project_id)
        semantics_path = self._semantics_path(
            project_id,
            project_path=project_path,
        )
        glossary_path = self._glossary_path(
            project_id,
            project_path=project_path,
        )
        decisions_path = self._terminology_decisions_path(
            project_id,
            project_path=project_path,
        )

        self._ensure_directory(
            semantics_path,
            label="Project semantics directory",
        )
        self._ensure_directory(
            decisions_path,
            label="Terminology Decisions directory",
        )

        if glossary_path.exists() or glossary_path.is_symlink():
            raise ProjectGlossaryPersistenceError(
                "Project Glossary already exists and must not be "
                f"silently overwritten: {glossary_path}."
            )

        glossary = create_project_glossary(
            project_id,
            default_language=default_language,
            timestamp=self._current_utc_timestamp(),
        )
        serialized = project_glossary_to_json(glossary)

        self._publish_new_validated_file(
            glossary_path,
            serialized,
            expected_value=glossary,
            parser=lambda text: project_glossary_from_json(
                text,
                expected_project_id=project_id,
            ),
            label="Project Glossary",
        )

        return self.load_glossary(project_id)

    def load_glossary(
        self,
        project_id: str,
    ) -> ProjectGlossary:
        """Load and validate one project's persisted glossary."""

        project_path = self._project_path(project_id)
        glossary_path = self._glossary_path(
            project_id,
            project_path=project_path,
        )

        self._require_regular_file(
            glossary_path,
            not_found_error=ProjectGlossaryNotFoundError(
                f"Project Glossary was not found: {glossary_path}."
            ),
            label="Project Glossary",
        )

        try:
            text = glossary_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ProjectGlossaryPersistenceError(
                f"Unable to read Project Glossary "
                f"{glossary_path}: {exc}"
            ) from exc

        return project_glossary_from_json(
            text,
            expected_project_id=project_id,
        )

    def load_project_concept(
        self,
        project_id: str,
        project_concept_id: str,
    ) -> ProjectConcept:
        """Load one Project Concept by its stable project-local ID."""

        validated_concept_id = (
            self._require_project_concept_id(
                project_concept_id
            )
        )
        glossary = self.load_glossary(project_id)

        for concept in glossary.concepts:
            if (
                concept.project_concept_id
                == validated_concept_id
            ):
                return concept

        raise ProjectConceptNotFoundError(
            f"Project Concept {validated_concept_id!r} "
            f"was not found in project {project_id!r}."
        )

    def create_candidate_concept(
        self,
        project_id: str,
        *,
        preferred_labels: Iterable[
            LocalizedGlossaryText
        ],
        definitions: Iterable[LocalizedGlossaryText],
        provenance: Iterable[
            ProjectConceptProvenance
        ],
        rationale: str,
        alternative_labels: Iterable[
            LocalizedGlossaryText
        ] = (),
        broader_project_concept_ids: Iterable[str] = (),
        related_project_concept_ids: Iterable[str] = (),
        turing_core_mappings: Iterable[
            TuringCoreConceptMapping
        ] = (),
        external_ontology_mappings: Iterable[
            ProjectExternalOntologyMapping
        ] = (),
    ) -> ProjectConcept:
        """Create one new Project Concept in candidate state."""

        current = self.load_glossary(project_id)
        project_concept_id = (
            allocate_next_project_concept_id(
                concept.project_concept_id
                for concept in current.concepts
            )
        )
        timestamp = self._current_utc_timestamp()
        concept = ProjectConcept(
            project_concept_id=project_concept_id,
            latest_revision=1,
            revisions=(
                ProjectConceptRevision(
                    revision=1,
                    lifecycle_status="candidate",
                    preferred_labels=self._tuple_of_instances(
                        preferred_labels,
                        LocalizedGlossaryText,
                        "preferred_labels",
                    ),
                    alternative_labels=(
                        self._tuple_of_instances(
                            alternative_labels,
                            LocalizedGlossaryText,
                            "alternative_labels",
                        )
                    ),
                    definitions=self._tuple_of_instances(
                        definitions,
                        LocalizedGlossaryText,
                        "definitions",
                    ),
                    broader_project_concept_ids=(
                        self._sorted_identifier_tuple(
                            broader_project_concept_ids,
                            "broader_project_concept_ids",
                        )
                    ),
                    related_project_concept_ids=(
                        self._sorted_identifier_tuple(
                            related_project_concept_ids,
                            "related_project_concept_ids",
                        )
                    ),
                    turing_core_mappings=(
                        self._tuple_of_instances(
                            turing_core_mappings,
                            TuringCoreConceptMapping,
                            "turing_core_mappings",
                        )
                    ),
                    external_ontology_mappings=(
                        self._tuple_of_instances(
                            external_ontology_mappings,
                            ProjectExternalOntologyMapping,
                            "external_ontology_mappings",
                        )
                    ),
                    provenance=self._tuple_of_instances(
                        provenance,
                        ProjectConceptProvenance,
                        "provenance",
                    ),
                    rationale=rationale,
                    created_at=timestamp,
                ),
            ),
        )
        updated = replace(
            current,
            glossary_revision=(
                current.glossary_revision + 1
            ),
            updated_at=timestamp,
            concepts=tuple(
                sorted(
                    current.concepts + (concept,),
                    key=lambda item: (
                        item.project_concept_id
                    ),
                )
            ),
        )

        self._replace_glossary(updated)
        return self.load_project_concept(
            project_id,
            project_concept_id,
        )

    def create_candidate_revision(
        self,
        project_id: str,
        project_concept_id: str,
        *,
        provenance: Iterable[
            ProjectConceptProvenance
        ],
        rationale: str,
        preferred_labels: (
            Iterable[LocalizedGlossaryText] | None
        ) = None,
        alternative_labels: (
            Iterable[LocalizedGlossaryText] | None
        ) = None,
        definitions: (
            Iterable[LocalizedGlossaryText] | None
        ) = None,
        broader_project_concept_ids: (
            Iterable[str] | None
        ) = None,
        related_project_concept_ids: (
            Iterable[str] | None
        ) = None,
        turing_core_mappings: (
            Iterable[TuringCoreConceptMapping] | None
        ) = None,
        external_ontology_mappings: (
            Iterable[ProjectExternalOntologyMapping] | None
        ) = None,
    ) -> ProjectConcept:
        """Append a candidate revision without mutating prior content."""

        validated_concept_id = (
            self._require_project_concept_id(
                project_concept_id
            )
        )
        current = self.load_glossary(project_id)
        existing = self._find_project_concept(
            current,
            validated_concept_id,
        )
        previous = existing.revisions[-1]
        timestamp = self._current_utc_timestamp()
        candidate_revision = ProjectConceptRevision(
            revision=existing.latest_revision + 1,
            lifecycle_status="candidate",
            preferred_labels=(
                previous.preferred_labels
                if preferred_labels is None
                else self._tuple_of_instances(
                    preferred_labels,
                    LocalizedGlossaryText,
                    "preferred_labels",
                )
            ),
            alternative_labels=(
                previous.alternative_labels
                if alternative_labels is None
                else self._tuple_of_instances(
                    alternative_labels,
                    LocalizedGlossaryText,
                    "alternative_labels",
                )
            ),
            definitions=(
                previous.definitions
                if definitions is None
                else self._tuple_of_instances(
                    definitions,
                    LocalizedGlossaryText,
                    "definitions",
                )
            ),
            broader_project_concept_ids=(
                previous.broader_project_concept_ids
                if broader_project_concept_ids is None
                else self._sorted_identifier_tuple(
                    broader_project_concept_ids,
                    "broader_project_concept_ids",
                )
            ),
            related_project_concept_ids=(
                previous.related_project_concept_ids
                if related_project_concept_ids is None
                else self._sorted_identifier_tuple(
                    related_project_concept_ids,
                    "related_project_concept_ids",
                )
            ),
            turing_core_mappings=(
                previous.turing_core_mappings
                if turing_core_mappings is None
                else self._tuple_of_instances(
                    turing_core_mappings,
                    TuringCoreConceptMapping,
                    "turing_core_mappings",
                )
            ),
            external_ontology_mappings=(
                previous.external_ontology_mappings
                if external_ontology_mappings is None
                else self._tuple_of_instances(
                    external_ontology_mappings,
                    ProjectExternalOntologyMapping,
                    "external_ontology_mappings",
                )
            ),
            provenance=self._tuple_of_instances(
                provenance,
                ProjectConceptProvenance,
                "provenance",
            ),
            rationale=rationale,
            created_at=timestamp,
        )
        revised_concept = replace(
            existing,
            latest_revision=candidate_revision.revision,
            revisions=(
                existing.revisions
                + (candidate_revision,)
            ),
        )
        updated = replace(
            current,
            glossary_revision=(
                current.glossary_revision + 1
            ),
            updated_at=timestamp,
            concepts=tuple(
                revised_concept
                if (
                    concept.project_concept_id
                    == validated_concept_id
                )
                else concept
                for concept in current.concepts
            ),
        )

        self._replace_glossary(updated)
        return self.load_project_concept(
            project_id,
            validated_concept_id,
        )

    def record_terminology_decision(
        self,
        project_id: str,
        project_concept_id: str,
        project_concept_revision: int,
        *,
        decision: str,
        reviewer_identity: str,
        rationale: str,
    ) -> TerminologyDecision:
        """Record a human decision and apply its lifecycle transition."""

        validated_concept_id = (
            self._require_project_concept_id(
                project_concept_id
            )
        )
        current = self.load_glossary(project_id)
        concept = self._find_project_concept(
            current,
            validated_concept_id,
        )
        target_revision = self._find_concept_revision(
            concept,
            project_concept_revision,
        )
        existing_decisions = (
            self.list_terminology_decisions(project_id)
        )
        terminology_decision_id = (
            allocate_next_terminology_decision_id(
                item.terminology_decision_id
                for item in existing_decisions
            )
        )
        timestamp = self._current_utc_timestamp()
        terminology_decision = (
            create_terminology_decision(
                project_id,
                terminology_decision_id,
                validated_concept_id,
                project_concept_revision,
                decision=decision,
                previous_lifecycle_status=(
                    target_revision.lifecycle_status
                ),
                reviewer_identity=reviewer_identity,
                decided_at=timestamp,
                rationale=rationale,
            )
        )
        transitioned_revision = replace(
            target_revision,
            lifecycle_status=(
                terminology_decision
                .resulting_lifecycle_status
            ),
        )
        transitioned_concept = replace(
            concept,
            revisions=tuple(
                transitioned_revision
                if (
                    revision.revision
                    == project_concept_revision
                )
                else revision
                for revision in concept.revisions
            ),
        )
        updated = replace(
            current,
            glossary_revision=(
                current.glossary_revision + 1
            ),
            updated_at=timestamp,
            concepts=tuple(
                transitioned_concept
                if (
                    item.project_concept_id
                    == validated_concept_id
                )
                else item
                for item in current.concepts
            ),
        )

        # Validate the future glossary state before publishing the
        # immutable Decision. This prevents known domain conflicts from
        # creating an orphaned Decision record.
        project_glossary_to_json(updated)

        self._publish_terminology_decision(
            terminology_decision
        )
        self._replace_glossary(updated)

        return self.load_terminology_decision(
            project_id,
            terminology_decision_id,
        )

    def list_terminology_decisions(
        self,
        project_id: str,
    ) -> tuple[TerminologyDecision, ...]:
        """Load all valid immutable Decisions in ID order."""

        decisions_path = self.terminology_decisions_path(
            project_id
        )

        if not decisions_path.exists():
            return ()

        if not decisions_path.is_dir():
            raise UnsafeProjectGlossaryPathError(
                "Terminology Decisions path is not a directory: "
                f"{decisions_path}."
            )

        try:
            entries = sorted(
                decisions_path.iterdir(),
                key=lambda path: path.name,
            )
        except OSError as exc:
            raise ProjectGlossaryPersistenceError(
                "Unable to inspect Terminology Decisions "
                f"directory {decisions_path}: {exc}"
            ) from exc

        decisions: list[TerminologyDecision] = []

        for entry in entries:
            if entry.name.startswith("."):
                continue

            match = _TERMINOLOGY_DECISION_FILE_PATTERN.fullmatch(
                entry.name
            )

            if (
                match is None
                or not is_valid_terminology_decision_id(
                    match.group(1)
                )
            ):
                raise TerminologyDecisionError(
                    "Visible Terminology Decision filenames must "
                    "match TD-000001.json through "
                    f"TD-999999.json: {entry}."
                )

            if entry.is_symlink() or not entry.is_file():
                raise UnsafeProjectGlossaryPathError(
                    "Terminology Decision entries must be regular "
                    f"non-symlink files: {entry}."
                )

            decisions.append(
                self.load_terminology_decision(
                    project_id,
                    match.group(1),
                )
            )

        return tuple(decisions)

    def load_ambiguity_group(
        self,
        project_id: str,
        ambiguity_group_id: str,
    ) -> AmbiguityGroup:
        """Load one Ambiguity Group from the Project Glossary."""

        validated_group_id = self._require_ambiguity_group_id(
            ambiguity_group_id
        )
        glossary = self.load_glossary(project_id)

        for group in glossary.ambiguity_groups:
            if (
                group.ambiguity_group_id
                == validated_group_id
            ):
                return group

        raise AmbiguityGroupNotFoundError(
            f"Ambiguity Group {validated_group_id!r} "
            f"was not found in project {project_id!r}."
        )

    def create_ambiguity_group(
        self,
        project_id: str,
        *,
        label: str,
        language: str,
        candidate_project_concept_ids: Iterable[str],
        rationale: str,
    ) -> AmbiguityGroup:
        """Create one explicit context-required Ambiguity Group."""

        current = self.load_glossary(project_id)
        ambiguity_group_id = (
            allocate_next_ambiguity_group_id(
                group.ambiguity_group_id
                for group in current.ambiguity_groups
            )
        )
        candidate_ids = self._sorted_identifier_tuple(
            candidate_project_concept_ids,
            "candidate_project_concept_ids",
        )
        timestamp = self._current_utc_timestamp()
        group = AmbiguityGroup(
            ambiguity_group_id=ambiguity_group_id,
            label=label,
            language=language,
            candidate_project_concept_ids=candidate_ids,
            resolution_rule="context_required",
            rationale=rationale,
            created_at=timestamp,
        )
        updated = replace(
            current,
            glossary_revision=(
                current.glossary_revision + 1
            ),
            updated_at=timestamp,
            ambiguity_groups=tuple(
                sorted(
                    current.ambiguity_groups + (group,),
                    key=lambda item: (
                        item.ambiguity_group_id
                    ),
                )
            ),
        )

        self._replace_glossary(updated)
        return self.load_ambiguity_group(
            project_id,
            ambiguity_group_id,
        )

    def scan_project_glossary(
        self,
        project_id: str,
    ) -> ProjectGlossaryScanResult:
        """Return valid semantic state and deterministic issues."""

        issues: list[ProjectGlossaryIssue] = []
        glossary: ProjectGlossary | None = None
        decisions: tuple[TerminologyDecision, ...] = ()

        try:
            glossary = self.load_glossary(project_id)
        except ProjectGlossaryError as exc:
            try:
                issue_path = self.glossary_path(project_id)
            except ProjectGlossaryError:
                issue_path = self.root / project_id

            issues.append(
                ProjectGlossaryIssue(
                    project_id=project_id,
                    code="invalid_project_glossary",
                    message=str(exc),
                    path=issue_path,
                )
            )

        decision_results, decision_issues = (
            self._scan_terminology_decisions(project_id)
        )
        decisions = decision_results
        issues.extend(decision_issues)

        if glossary is not None:
            issues.extend(
                self._decision_chain_issues(
                    glossary,
                    decisions,
                )
            )

        issues.sort(
            key=lambda issue: (
                str(issue.path),
                issue.code,
                issue.project_concept_id or "",
                issue.terminology_decision_id or "",
                issue.ambiguity_group_id or "",
            )
        )

        return ProjectGlossaryScanResult(
            glossary=glossary,
            terminology_decisions=decisions,
            issues=tuple(issues),
        )

    def load_terminology_decision(
        self,
        project_id: str,
        terminology_decision_id: str,
    ) -> TerminologyDecision:
        """Load one immutable Terminology Decision by identifier."""

        project_path = self._project_path(project_id)
        decision_path = self._terminology_decision_path(
            project_id,
            terminology_decision_id,
            project_path=project_path,
        )

        self._require_regular_file(
            decision_path,
            not_found_error=TerminologyDecisionError(
                "Terminology Decision was not found: "
                f"{decision_path}."
            ),
            label="Terminology Decision",
        )

        try:
            text = decision_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ProjectGlossaryPersistenceError(
                "Unable to read Terminology Decision "
                f"{decision_path}: {exc}"
            ) from exc

        return terminology_decision_from_json(
            text,
            expected_project_id=project_id,
            expected_terminology_decision_id=(
                terminology_decision_id
            ),
        )

    def glossary_path(
        self,
        project_id: str,
    ) -> Path:
        """Return the validated path of one project's glossary."""

        project_path = self._project_path(project_id)
        return self._glossary_path(
            project_id,
            project_path=project_path,
        )

    def terminology_decisions_path(
        self,
        project_id: str,
    ) -> Path:
        """Return the validated Decision directory path."""

        project_path = self._project_path(project_id)
        return self._terminology_decisions_path(
            project_id,
            project_path=project_path,
        )

    def terminology_decision_path(
        self,
        project_id: str,
        terminology_decision_id: str,
    ) -> Path:
        """Return the validated path of one Terminology Decision."""

        project_path = self._project_path(project_id)
        return self._terminology_decision_path(
            project_id,
            terminology_decision_id,
            project_path=project_path,
        )

    def _replace_glossary(
        self,
        glossary: ProjectGlossary,
    ) -> ProjectGlossary:
        """Atomically replace an explicitly versioned glossary.

        This private operation is used only by validated P4/16 domain
        mutations. It is intentionally not an unrestricted public save API.
        """

        if not isinstance(glossary, ProjectGlossary):
            raise ProjectGlossaryValidationError(
                "glossary must be a ProjectGlossary instance."
            )

        current = self.load_glossary(glossary.project_id)

        if glossary.glossary_revision != (
            current.glossary_revision + 1
        ):
            raise ProjectGlossaryPersistenceError(
                "A glossary replacement must increment "
                "glossary_revision by exactly one."
            )

        if glossary.created_at != current.created_at:
            raise ProjectGlossaryPersistenceError(
                "A glossary replacement must preserve created_at."
            )

        glossary_path = self.glossary_path(
            glossary.project_id
        )
        serialized = project_glossary_to_json(glossary)

        self._replace_validated_file(
            glossary_path,
            serialized,
            expected_value=glossary,
            parser=lambda text: project_glossary_from_json(
                text,
                expected_project_id=glossary.project_id,
            ),
            label="Project Glossary",
        )

        return self.load_glossary(glossary.project_id)

    def _publish_terminology_decision(
        self,
        terminology_decision: TerminologyDecision,
    ) -> TerminologyDecision:
        """Atomically publish one new immutable Decision record."""

        if not isinstance(
            terminology_decision,
            TerminologyDecision,
        ):
            raise TerminologyDecisionError(
                "terminology_decision must be a "
                "TerminologyDecision instance."
            )

        decision_path = self.terminology_decision_path(
            terminology_decision.project_id,
            terminology_decision.terminology_decision_id,
        )
        decisions_path = decision_path.parent

        self._ensure_directory(
            decisions_path,
            label="Terminology Decisions directory",
        )

        serialized = terminology_decision_to_json(
            terminology_decision
        )

        self._publish_new_validated_file(
            decision_path,
            serialized,
            expected_value=terminology_decision,
            parser=lambda text: terminology_decision_from_json(
                text,
                expected_project_id=(
                    terminology_decision.project_id
                ),
                expected_terminology_decision_id=(
                    terminology_decision
                    .terminology_decision_id
                ),
            ),
            label="Terminology Decision",
        )

        return self.load_terminology_decision(
            terminology_decision.project_id,
            terminology_decision.terminology_decision_id,
        )

    def _publish_new_validated_file(
        self,
        target_path: Path,
        serialized: str,
        *,
        expected_value: Any,
        parser: Callable[[str], Any],
        label: str,
    ) -> None:
        """Publish a complete new file without replacing a target."""

        temporary_path = self._temporary_path(target_path)
        self._reject_existing_temporary_path(
            temporary_path,
            label=label,
        )

        if target_path.exists() or target_path.is_symlink():
            raise ProjectGlossaryPersistenceError(
                f"{label} already exists and must not be "
                f"overwritten: {target_path}."
            )

        self._write_and_validate_temporary_file(
            temporary_path,
            serialized,
            expected_value=expected_value,
            parser=parser,
            label=label,
        )

        try:
            os.link(temporary_path, target_path)
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                raise ProjectGlossaryPersistenceError(
                    f"{label} appeared during publication and was "
                    f"not overwritten: {target_path}."
                ) from exc

            raise ProjectGlossaryPersistenceError(
                f"Unable to publish {label} at "
                f"{target_path}: {exc}"
            ) from exc
        finally:
            self._remove_temporary_file(
                temporary_path,
                label=label,
            )

    def _replace_validated_file(
        self,
        target_path: Path,
        serialized: str,
        *,
        expected_value: Any,
        parser: Callable[[str], Any],
        label: str,
    ) -> None:
        """Atomically replace one explicitly mutable versioned file."""

        self._require_regular_file(
            target_path,
            not_found_error=ProjectGlossaryNotFoundError(
                f"{label} was not found: {target_path}."
            ),
            label=label,
        )
        temporary_path = self._temporary_path(target_path)
        self._reject_existing_temporary_path(
            temporary_path,
            label=label,
        )
        self._write_and_validate_temporary_file(
            temporary_path,
            serialized,
            expected_value=expected_value,
            parser=parser,
            label=label,
        )

        try:
            os.replace(temporary_path, target_path)
        except OSError as exc:
            raise ProjectGlossaryPersistenceError(
                f"Unable to atomically replace {label} at "
                f"{target_path}: {exc}"
            ) from exc
        finally:
            if temporary_path.exists():
                self._remove_temporary_file(
                    temporary_path,
                    label=label,
                )

    def _write_and_validate_temporary_file(
        self,
        temporary_path: Path,
        serialized: str,
        *,
        expected_value: Any,
        parser: Callable[[str], Any],
        label: str,
    ) -> None:
        if not isinstance(serialized, str):
            raise ProjectGlossaryPersistenceError(
                f"Serialized {label} content must be a string."
            )

        try:
            with temporary_path.open(
                "x",
                encoding="utf-8",
                newline="\n",
            ) as output:
                output.write(serialized)
                output.flush()
                os.fsync(output.fileno())

            persisted_text = temporary_path.read_text(
                encoding="utf-8"
            )
            persisted_value = parser(persisted_text)
        except (OSError, UnicodeError) as exc:
            self._remove_temporary_file(
                temporary_path,
                label=label,
                suppress_missing=True,
            )
            raise ProjectGlossaryPersistenceError(
                f"Unable to prepare temporary {label} file "
                f"{temporary_path}: {exc}"
            ) from exc
        except Exception:
            self._remove_temporary_file(
                temporary_path,
                label=label,
                suppress_missing=True,
            )
            raise

        if persisted_value != expected_value:
            self._remove_temporary_file(
                temporary_path,
                label=label,
                suppress_missing=True,
            )
            raise ProjectGlossaryIntegrityError(
                f"Persisted temporary {label} differs from its "
                "validated value."
            )

    def _scan_terminology_decisions(
        self,
        project_id: str,
    ) -> tuple[
        tuple[TerminologyDecision, ...],
        list[ProjectGlossaryIssue],
    ]:
        project_path = self._project_path(project_id)
        decisions_path = (
            project_path
            / SEMANTICS_DIRECTORY_NAME
            / TERMINOLOGY_DECISIONS_DIRECTORY_NAME
        )
        issues: list[ProjectGlossaryIssue] = []

        if decisions_path.is_symlink():
            return (
                (),
                [
                    ProjectGlossaryIssue(
                        project_id=project_id,
                        code=(
                            "unsafe_terminology_decisions_path"
                        ),
                        message=(
                            "Symbolic-link Terminology Decisions "
                            "directories are rejected."
                        ),
                        path=decisions_path,
                    )
                ],
            )

        self._assert_path_within(
            decisions_path,
            project_path,
        )

        if not decisions_path.exists():
            return (
                (),
                [
                    ProjectGlossaryIssue(
                        project_id=project_id,
                        code=(
                            "missing_terminology_decisions_path"
                        ),
                        message=(
                            "Terminology Decisions directory is "
                            "missing."
                        ),
                        path=decisions_path,
                    )
                ],
            )

        if not decisions_path.is_dir():
            return (
                (),
                [
                    ProjectGlossaryIssue(
                        project_id=project_id,
                        code=(
                            "invalid_terminology_decisions_path"
                        ),
                        message=(
                            "Terminology Decisions path is not a "
                            "directory."
                        ),
                        path=decisions_path,
                    )
                ],
            )

        try:
            entries = sorted(
                decisions_path.iterdir(),
                key=lambda path: path.name,
            )
        except OSError as exc:
            return (
                (),
                [
                    ProjectGlossaryIssue(
                        project_id=project_id,
                        code=(
                            "terminology_decisions_read_error"
                        ),
                        message=(
                            "Unable to inspect Terminology "
                            f"Decisions directory: {exc}"
                        ),
                        path=decisions_path,
                    )
                ],
            )

        decisions: list[TerminologyDecision] = []

        for entry in entries:
            if entry.name.startswith("."):
                continue

            match = _TERMINOLOGY_DECISION_FILE_PATTERN.fullmatch(
                entry.name
            )
            candidate_decision_id = (
                match.group(1)
                if (
                    match is not None
                    and is_valid_terminology_decision_id(
                        match.group(1)
                    )
                )
                else None
            )

            if entry.is_symlink():
                issues.append(
                    ProjectGlossaryIssue(
                        project_id=project_id,
                        code=(
                            "unsafe_terminology_decision_path"
                        ),
                        message=(
                            "Symbolic-link Terminology Decision "
                            "entries are rejected."
                        ),
                        path=entry,
                        terminology_decision_id=(
                            candidate_decision_id
                        ),
                    )
                )
                continue

            if candidate_decision_id is None:
                issues.append(
                    ProjectGlossaryIssue(
                        project_id=project_id,
                        code=(
                            "invalid_terminology_decision_entry"
                        ),
                        message=(
                            "Visible Terminology Decision "
                            "filenames must match "
                            "TD-000001.json through "
                            "TD-999999.json."
                        ),
                        path=entry,
                    )
                )
                continue

            if not entry.is_file():
                issues.append(
                    ProjectGlossaryIssue(
                        project_id=project_id,
                        code=(
                            "invalid_terminology_decision_entry"
                        ),
                        message=(
                            "Terminology Decision entry is not a "
                            "regular file."
                        ),
                        path=entry,
                        terminology_decision_id=(
                            candidate_decision_id
                        ),
                    )
                )
                continue

            try:
                decision = self.load_terminology_decision(
                    project_id,
                    candidate_decision_id,
                )
            except ProjectGlossaryError as exc:
                issues.append(
                    ProjectGlossaryIssue(
                        project_id=project_id,
                        code=(
                            "invalid_terminology_decision"
                        ),
                        message=str(exc),
                        path=entry,
                        terminology_decision_id=(
                            candidate_decision_id
                        ),
                    )
                )
                continue

            decisions.append(decision)

        decisions.sort(
            key=lambda item: item.terminology_decision_id
        )
        return tuple(decisions), issues

    def _decision_chain_issues(
        self,
        glossary: ProjectGlossary,
        decisions: tuple[TerminologyDecision, ...],
    ) -> list[ProjectGlossaryIssue]:
        issues: list[ProjectGlossaryIssue] = []
        concepts = {
            concept.project_concept_id: concept
            for concept in glossary.concepts
        }
        decisions_by_revision: dict[
            tuple[str, int],
            list[TerminologyDecision],
        ] = {}

        for decision in decisions:
            concept = concepts.get(
                decision.project_concept_id
            )
            decision_path = (
                self.terminology_decision_path(
                    glossary.project_id,
                    decision.terminology_decision_id,
                )
            )

            if concept is None:
                issues.append(
                    ProjectGlossaryIssue(
                        project_id=glossary.project_id,
                        code="unknown_decision_concept",
                        message=(
                            "Terminology Decision references an "
                            "unknown Project Concept."
                        ),
                        path=decision_path,
                        project_concept_id=(
                            decision.project_concept_id
                        ),
                        terminology_decision_id=(
                            decision.terminology_decision_id
                        ),
                    )
                )
                continue

            if not any(
                revision.revision
                == decision.project_concept_revision
                for revision in concept.revisions
            ):
                issues.append(
                    ProjectGlossaryIssue(
                        project_id=glossary.project_id,
                        code="unknown_decision_revision",
                        message=(
                            "Terminology Decision references an "
                            "unknown Project Concept revision."
                        ),
                        path=decision_path,
                        project_concept_id=(
                            decision.project_concept_id
                        ),
                        terminology_decision_id=(
                            decision.terminology_decision_id
                        ),
                    )
                )
                continue

            key = (
                decision.project_concept_id,
                decision.project_concept_revision,
            )
            decisions_by_revision.setdefault(
                key,
                [],
            ).append(decision)

        glossary_path = self.glossary_path(
            glossary.project_id
        )

        for concept in glossary.concepts:
            for revision in concept.revisions:
                key = (
                    concept.project_concept_id,
                    revision.revision,
                )
                chain = sorted(
                    decisions_by_revision.get(key, []),
                    key=lambda item: (
                        item.terminology_decision_id
                    ),
                )
                replayed_status = "candidate"
                chain_valid = True

                for decision in chain:
                    if (
                        decision.previous_lifecycle_status
                        != replayed_status
                    ):
                        issues.append(
                            ProjectGlossaryIssue(
                                project_id=(
                                    glossary.project_id
                                ),
                                code=(
                                    "invalid_decision_chain"
                                ),
                                message=(
                                    "Terminology Decision "
                                    "previous status does not "
                                    "match the replayed lifecycle "
                                    "status."
                                ),
                                path=(
                                    self
                                    .terminology_decision_path(
                                        glossary.project_id,
                                        decision
                                        .terminology_decision_id,
                                    )
                                ),
                                project_concept_id=(
                                    concept.project_concept_id
                                ),
                                terminology_decision_id=(
                                    decision
                                    .terminology_decision_id
                                ),
                            )
                        )
                        chain_valid = False
                        break

                    replayed_status = (
                        decision.resulting_lifecycle_status
                    )

                if (
                    chain_valid
                    and replayed_status
                    != revision.lifecycle_status
                ):
                    issues.append(
                        ProjectGlossaryIssue(
                            project_id=glossary.project_id,
                            code="decision_state_mismatch",
                            message=(
                                "Persisted lifecycle status does "
                                "not match the replayed human "
                                "Terminology Decisions."
                            ),
                            path=glossary_path,
                            project_concept_id=(
                                concept.project_concept_id
                            ),
                        )
                    )

        return issues

    def _project_path(
        self,
        project_id: str,
    ) -> Path:
        if not is_valid_project_id(project_id):
            raise UnsafeProjectGlossaryPathError(
                "project_id must contain exactly six digits."
            )

        try:
            project = self._workspace.load_project(project_id)
        except ProjectNotFoundError:
            raise
        except ProjectWorkspaceError as exc:
            raise ProjectGlossaryPersistenceError(
                f"Unable to validate project {project_id!r}: {exc}"
            ) from exc

        project_path = self.root / project.project_id
        self._assert_path_within(
            project_path,
            self.root,
        )

        if project_path.is_symlink():
            raise UnsafeProjectGlossaryPathError(
                "Symbolic-link project directories are rejected: "
                f"{project_path}."
            )

        return project_path

    def _find_project_concept(
        self,
        glossary: ProjectGlossary,
        project_concept_id: str,
    ) -> ProjectConcept:
        for concept in glossary.concepts:
            if (
                concept.project_concept_id
                == project_concept_id
            ):
                return concept

        raise ProjectConceptNotFoundError(
            f"Project Concept {project_concept_id!r} "
            f"was not found in project "
            f"{glossary.project_id!r}."
        )

    def _find_concept_revision(
        self,
        concept: ProjectConcept,
        revision_number: object,
    ) -> ProjectConceptRevision:
        if (
            isinstance(revision_number, bool)
            or not isinstance(revision_number, int)
            or revision_number < 1
        ):
            raise InvalidTerminologyLifecycleTransitionError(
                "project_concept_revision must be a positive "
                "integer."
            )

        for revision in concept.revisions:
            if revision.revision == revision_number:
                return revision

        raise InvalidTerminologyLifecycleTransitionError(
            f"Project Concept {concept.project_concept_id!r} "
            f"has no revision {revision_number}."
        )

    def _require_project_concept_id(
        self,
        value: object,
    ) -> str:
        if not is_valid_project_concept_id(value):
            raise UnsafeProjectGlossaryPathError(
                "project_concept_id must match "
                "^PC-[0-9]{6}$ and must not use "
                "sequence 000000."
            )

        return value

    def _require_ambiguity_group_id(
        self,
        value: object,
    ) -> str:
        if not is_valid_ambiguity_group_id(value):
            raise UnsafeProjectGlossaryPathError(
                "ambiguity_group_id must match "
                "^AG-[0-9]{6}$ and must not use "
                "sequence 000000."
            )

        return value

    def _tuple_of_instances(
        self,
        values: Iterable[Any],
        expected_type: type[Any],
        label: str,
    ) -> tuple[Any, ...]:
        if isinstance(values, (str, bytes)):
            raise ProjectGlossaryValidationError(
                f"{label} must be an iterable of "
                f"{expected_type.__name__} instances."
            )

        try:
            result = tuple(values)
        except TypeError as exc:
            raise ProjectGlossaryValidationError(
                f"{label} must be iterable."
            ) from exc

        if not all(
            isinstance(value, expected_type)
            for value in result
        ):
            raise ProjectGlossaryValidationError(
                f"{label} must contain only "
                f"{expected_type.__name__} instances."
            )

        return result

    def _sorted_identifier_tuple(
        self,
        values: Iterable[str],
        label: str,
    ) -> tuple[str, ...]:
        identifiers = self._tuple_of_instances(
            values,
            str,
            label,
        )

        for identifier in identifiers:
            self._require_project_concept_id(identifier)

        if len(identifiers) != len(set(identifiers)):
            raise ProjectGlossaryValidationError(
                f"{label} must not contain duplicates."
            )

        return tuple(sorted(identifiers))

    def _semantics_path(
        self,
        project_id: str,
        *,
        project_path: Path | None = None,
    ) -> Path:
        validated_project_path = (
            self._project_path(project_id)
            if project_path is None
            else project_path
        )
        semantics_path = (
            validated_project_path
            / SEMANTICS_DIRECTORY_NAME
        )
        self._assert_path_within(
            semantics_path,
            validated_project_path,
        )
        self._reject_symlink(
            semantics_path,
            label="Project semantics directory",
        )
        return semantics_path

    def _glossary_path(
        self,
        project_id: str,
        *,
        project_path: Path | None = None,
    ) -> Path:
        semantics_path = self._semantics_path(
            project_id,
            project_path=project_path,
        )
        glossary_path = (
            semantics_path / PROJECT_GLOSSARY_FILENAME
        )
        self._assert_path_within(
            glossary_path,
            semantics_path,
        )
        self._reject_symlink(
            glossary_path,
            label="Project Glossary",
        )
        return glossary_path

    def _terminology_decisions_path(
        self,
        project_id: str,
        *,
        project_path: Path | None = None,
    ) -> Path:
        semantics_path = self._semantics_path(
            project_id,
            project_path=project_path,
        )
        decisions_path = (
            semantics_path
            / TERMINOLOGY_DECISIONS_DIRECTORY_NAME
        )
        self._assert_path_within(
            decisions_path,
            semantics_path,
        )
        self._reject_symlink(
            decisions_path,
            label="Terminology Decisions directory",
        )
        return decisions_path

    def _terminology_decision_path(
        self,
        project_id: str,
        terminology_decision_id: str,
        *,
        project_path: Path | None = None,
    ) -> Path:
        decisions_path = self._terminology_decisions_path(
            project_id,
            project_path=project_path,
        )
        filename = terminology_decision_filename(
            terminology_decision_id
        )
        decision_path = decisions_path / filename
        self._assert_path_within(
            decision_path,
            decisions_path,
        )
        self._reject_symlink(
            decision_path,
            label="Terminology Decision",
        )
        return decision_path

    def _ensure_directory(
        self,
        path: Path,
        *,
        label: str,
    ) -> None:
        self._reject_symlink(path, label=label)

        if path.exists() and not path.is_dir():
            raise UnsafeProjectGlossaryPathError(
                f"{label} is not a directory: {path}."
            )

        try:
            path.mkdir(
                parents=True,
                exist_ok=True,
            )
        except OSError as exc:
            raise ProjectGlossaryPersistenceError(
                f"Unable to create {label} {path}: {exc}"
            ) from exc

        self._reject_symlink(path, label=label)

    def _require_regular_file(
        self,
        path: Path,
        *,
        not_found_error: Exception,
        label: str,
    ) -> None:
        self._reject_symlink(path, label=label)

        if not path.exists():
            raise not_found_error

        if not path.is_file():
            raise UnsafeProjectGlossaryPathError(
                f"{label} is not a regular file: {path}."
            )

    def _reject_symlink(
        self,
        path: Path,
        *,
        label: str,
    ) -> None:
        if path.is_symlink():
            raise UnsafeProjectGlossaryPathError(
                f"Symbolic-link {label} paths are rejected: {path}."
            )

    def _assert_path_within(
        self,
        path: Path,
        parent: Path,
    ) -> None:
        try:
            path.resolve(strict=False).relative_to(
                parent.resolve(strict=False)
            )
        except ValueError as exc:
            raise UnsafeProjectGlossaryPathError(
                f"Path escapes its permitted parent: {path}."
            ) from exc

    def _temporary_path(
        self,
        target_path: Path,
    ) -> Path:
        temporary_path = target_path.parent / (
            f".{target_path.name}.tmp"
        )
        self._assert_path_within(
            temporary_path,
            target_path.parent,
        )
        return temporary_path

    def _reject_existing_temporary_path(
        self,
        temporary_path: Path,
        *,
        label: str,
    ) -> None:
        if (
            temporary_path.exists()
            or temporary_path.is_symlink()
        ):
            raise ProjectGlossaryPersistenceError(
                f"Temporary {label} path already exists: "
                f"{temporary_path}."
            )

    def _remove_temporary_file(
        self,
        temporary_path: Path,
        *,
        label: str,
        suppress_missing: bool = False,
    ) -> None:
        try:
            temporary_path.unlink(
                missing_ok=suppress_missing,
            )
        except OSError as exc:
            raise ProjectGlossaryPersistenceError(
                f"Unable to remove temporary {label} file "
                f"{temporary_path}: {exc}"
            ) from exc

    def _current_utc_timestamp(self) -> str:
        value = self._clock()

        if not isinstance(value, datetime):
            raise ProjectGlossaryPersistenceError(
                "Project Glossary Repository clock must return "
                "a datetime."
            )

        if value.tzinfo is None or value.utcoffset() is None:
            raise ProjectGlossaryPersistenceError(
                "Project Glossary Repository clock must return "
                "a timezone-aware datetime."
            )

        utc_value = value.astimezone(timezone.utc)
        return (
            utc_value.isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )