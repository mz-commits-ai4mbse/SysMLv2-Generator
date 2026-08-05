"""Select exact active P9 evidence for Review Workspace construction."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath

from modules.project_processing import (
    ProcessingArtifactReference,
    ProcessingRunHistory,
    ProjectProcessingError,
    SemanticReferenceVersion,
    derive_processing_artifact_lifecycles,
    derive_processing_run_state,
    validate_processing_artifact_reference,
    validate_processing_run_history,
)
from modules.project_workspace.types import (
    FrameworkTemplateReference,
)

from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
)


AGENTIC_INGESTION_STAGE = "agentic_ingestion"

P9_REVIEW_ARTIFACT_TYPES = frozenset(
    {
        "agent_outputs",
        "consensus_reports",
        "review_reports",
        "run_summaries",
    }
)


@dataclass(frozen=True, slots=True)
class P9ReviewEvidenceSet:
    """One exact active P9 evidence set eligible for review construction."""

    project_id: str
    source_id: str
    source_sha256: str
    processing_run_id: str
    attempt_id: str
    framework_template: FrameworkTemplateReference
    semantic_reference_versions: tuple[
        SemanticReferenceVersion,
        ...,
    ]
    primary_review_artifact_reference: (
        ProcessingArtifactReference
    )
    agent_output_references: tuple[
        ProcessingArtifactReference,
        ...,
    ]
    consensus_report_references: tuple[
        ProcessingArtifactReference,
        ...,
    ]
    run_summary_references: tuple[
        ProcessingArtifactReference,
        ...,
    ]

    @property
    def supporting_artifact_references(
        self,
    ) -> tuple[ProcessingArtifactReference, ...]:
        """Return all non-primary references in deterministic order."""

        return (
            self.agent_output_references
            + self.consensus_report_references
            + self.run_summary_references
        )


def select_p9_review_evidence_set(
    history: object,
    *,
    repository_root: Path | str,
) -> P9ReviewEvidenceSet:
    """Select and verify one complete active P9 evidence set.

    The operation is read-only and fail-closed. It does not create a
    Review Document and does not modify Processing evidence.
    """

    validated_history = _validated_history(history)
    root = _validated_repository_root(repository_root)
    state = derive_processing_run_state(validated_history)
    manifest = validated_history.manifest

    if (
        manifest.source_role_snapshot != "engineering_source"
        or manifest.workflow_profile
        != "engineering_source_processing"
    ):
        raise ReviewIntegrityError(
            "Only an engineering-source Processing Run may "
            "create a P9 Review Evidence Set."
        )

    if (
        state.run_state != "awaiting_review"
        or state.processing_stage
        != AGENTIC_INGESTION_STAGE
        or not state.pending_review
        or state.latest_attempt_id is None
    ):
        raise ReviewIntegrityError(
            "P9 Review Evidence requires an agentic-ingestion "
            "Run currently awaiting review."
        )

    latest_event = validated_history.events[-1]

    if (
        latest_event.event_type != "review_requested"
        or latest_event.attempt_id
        != state.latest_attempt_id
    ):
        raise ReviewIntegrityError(
            "The latest Processing Event must be the exact "
            "P9 review request."
        )

    publication_events = tuple(
        event
        for event in validated_history.events
        if (
            event.event_type == "artifact_published"
            and event.processing_stage
            == AGENTIC_INGESTION_STAGE
            and event.attempt_id
            == state.latest_attempt_id
        )
    )

    if len(publication_events) != 1:
        raise ReviewIntegrityError(
            "P9 Review Evidence requires exactly one matching "
            "artifact publication event."
        )

    publication_event = publication_events[0]

    if (
        publication_event.event_sequence + 1
        != latest_event.event_sequence
    ):
        raise ReviewIntegrityError(
            "The P9 review request must directly follow its "
            "artifact publication event."
        )

    references = publication_event.artifact_references

    _require_active_references(
        validated_history,
        references,
    )

    grouped = _group_references(references)

    for reference in references:
        _verify_reference_file(
            reference,
            repository_root=root,
            project_id=manifest.project_id,
            processing_run_id=(
                manifest.processing_run_id
            ),
            attempt_id=state.latest_attempt_id,
        )

    return P9ReviewEvidenceSet(
        project_id=manifest.project_id,
        source_id=manifest.source_id,
        source_sha256=manifest.source_sha256,
        processing_run_id=manifest.processing_run_id,
        attempt_id=state.latest_attempt_id,
        framework_template=FrameworkTemplateReference(
            template_id=manifest.framework_template_id,
            template_version=(
                manifest.framework_template_version
            ),
        ),
        semantic_reference_versions=(
            manifest.semantic_reference_versions
        ),
        primary_review_artifact_reference=(
            grouped["review_reports"][0]
        ),
        agent_output_references=grouped[
            "agent_outputs"
        ],
        consensus_report_references=grouped[
            "consensus_reports"
        ],
        run_summary_references=grouped[
            "run_summaries"
        ],
    )


def _validated_history(
    history: object,
) -> ProcessingRunHistory:
    try:
        return validate_processing_run_history(history)
    except ProjectProcessingError as exc:
        raise ReviewValidationError(
            "history must be one valid Processing Run history."
        ) from exc


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


def _require_active_references(
    history: ProcessingRunHistory,
    references: tuple[ProcessingArtifactReference, ...],
) -> None:
    try:
        lifecycles = derive_processing_artifact_lifecycles(
            (history,)
        )
    except ProjectProcessingError as exc:
        raise ReviewIntegrityError(
            "P9 artifact lifecycle could not be derived."
        ) from exc

    lifecycle_by_reference = {
        _reference_key(lifecycle.artifact_reference): lifecycle
        for lifecycle in lifecycles
    }

    for reference in references:
        lifecycle = lifecycle_by_reference.get(
            _reference_key(reference)
        )

        if (
            lifecycle is None
            or lifecycle.lifecycle_state != "active"
        ):
            raise ReviewIntegrityError(
                "Every P9 Review Evidence artifact must remain "
                f"active: {reference.artifact_id}."
            )


def _group_references(
    references: tuple[ProcessingArtifactReference, ...],
) -> dict[
    str,
    tuple[ProcessingArtifactReference, ...],
]:
    if not isinstance(references, tuple):
        raise ReviewValidationError(
            "P9 artifact references must be a tuple."
        )

    reference_keys: set[
        tuple[str, str, str, str]
    ] = set()
    grouped_lists = {
        artifact_type: []
        for artifact_type in P9_REVIEW_ARTIFACT_TYPES
    }

    for reference in references:
        try:
            validate_processing_artifact_reference(
                reference
            )
        except ProjectProcessingError as exc:
            raise ReviewValidationError(
                "P9 contains an invalid artifact reference."
            ) from exc

        key = _reference_key(reference)

        if key in reference_keys:
            raise ReviewIntegrityError(
                "P9 artifact references must be unique."
            )

        reference_keys.add(key)

        if (
            reference.artifact_type
            not in P9_REVIEW_ARTIFACT_TYPES
        ):
            raise ReviewIntegrityError(
                "P9 Review Evidence contains an unsupported "
                f"artifact type: {reference.artifact_type!r}."
            )

        grouped_lists[
            reference.artifact_type
        ].append(reference)

    if len(grouped_lists["review_reports"]) != 1:
        raise ReviewIntegrityError(
            "P9 Review Evidence requires exactly one "
            "Review Report."
        )

    required_nonempty = (
        ("agent_outputs", "Agent Output"),
        ("consensus_reports", "Consensus Report"),
        ("run_summaries", "Run Summary"),
    )

    for artifact_type, label in required_nonempty:
        if not grouped_lists[artifact_type]:
            raise ReviewIntegrityError(
                "P9 Review Evidence requires at least one "
                f"{label}."
            )

    return {
        artifact_type: tuple(
            sorted(
                items,
                key=_reference_key,
            )
        )
        for artifact_type, items
        in grouped_lists.items()
    }


def _verify_reference_file(
    reference: ProcessingArtifactReference,
    *,
    repository_root: Path,
    project_id: str,
    processing_run_id: str,
    attempt_id: str,
) -> None:
    try:
        validate_processing_artifact_reference(reference)
    except ProjectProcessingError as exc:
        raise ReviewValidationError(
            "P9 contains an invalid artifact reference."
        ) from exc

    relative_path = PurePosixPath(
        reference.repository_relative_path
    )

    expected_prefix = (
        "data",
        "projects",
        project_id,
        "runs",
        processing_run_id,
        "artifacts",
        reference.artifact_type,
        AGENTIC_INGESTION_STAGE,
        attempt_id,
    )

    if (
        relative_path.parts[: len(expected_prefix)]
        != expected_prefix
    ):
        raise ReviewIntegrityError(
            "P9 artifact path does not match its Project, "
            "Run, type, stage and Attempt binding."
        )

    target = repository_root.joinpath(
        *relative_path.parts
    )

    current = repository_root

    for part in relative_path.parts:
        current = current / part

        if current.is_symlink():
            raise ReviewReferenceError(
                "P9 Review Evidence must not contain "
                f"symbolic-link paths: {reference.artifact_id}."
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
            "Referenced P9 artifact does not exist: "
            f"{reference.artifact_id}."
        ) from exc
    except ValueError as exc:
        raise ReviewReferenceError(
            "Referenced P9 artifact escapes repository_root: "
            f"{reference.artifact_id}."
        ) from exc
    except OSError as exc:
        raise ReviewReferenceError(
            "Referenced P9 artifact path cannot be resolved: "
            f"{reference.artifact_id}."
        ) from exc

    if not target.is_file():
        raise ReviewReferenceError(
            "Referenced P9 artifact is not a regular file: "
            f"{reference.artifact_id}."
        )

    try:
        content = target.read_bytes()
    except OSError as exc:
        raise ReviewReferenceError(
            "Referenced P9 artifact cannot be read: "
            f"{reference.artifact_id}."
        ) from exc

    if not content:
        raise ReviewIntegrityError(
            "Referenced P9 artifact must not be empty: "
            f"{reference.artifact_id}."
        )

    actual_fingerprint = hashlib.sha256(
        content
    ).hexdigest()

    if (
        actual_fingerprint
        != reference.content_fingerprint
    ):
        raise ReviewIntegrityError(
            "Referenced P9 artifact fingerprint does not "
            f"match persisted content: {reference.artifact_id}."
        )


def _reference_key(
    reference: ProcessingArtifactReference,
) -> tuple[str, str, str, str]:
    return (
        reference.artifact_type,
        reference.artifact_id,
        reference.content_fingerprint,
        reference.repository_relative_path,
    )
