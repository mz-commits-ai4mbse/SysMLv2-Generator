"""Validate and publish project-bound Phase-F work as immutable P5 artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from modules.project_processing import (
    ProcessingArtifactReference,
    ProjectProcessingRepository,
    create_processing_artifact_reference,
    derive_processing_run_state,
)
from modules.project_processing.paths import attempt_artifact_path

from .errors import (
    ProjectIngestionOutputValidationError,
    ProjectIngestionPublicationError,
    ProjectIngestionRecoveryRequiredError,
)


AGENTIC_INGESTION_STAGE = "agentic_ingestion"

_ARTIFACT_PREFIXES = {
    "agent_outputs": "AGOUT",
    "consensus_reports": "CONS",
    "review_reports": "REVIEW",
    "run_summaries": "SUMMARY",
}


@dataclass(frozen=True, slots=True)
class _PublishableFile:
    """One validated work file before immutable publication."""

    artifact_type: str
    source_path: Path
    relative_target: Path
    content: bytes
    fingerprint: str


class ProjectIngestionPublisher:
    """Publish a complete validated work result into P5 artifact storage."""

    def __init__(
        self,
        *,
        root: Path | str,
        repository_root: Path | str,
        processing_repository: ProjectProcessingRepository,
    ) -> None:
        self.root = Path(root)
        self.repository_root = Path(repository_root)
        self._processing = processing_repository

    def publish_attempt_outputs(
        self,
        project_id: str,
        processing_run_id: str,
        attempt_id: str,
    ) -> tuple[ProcessingArtifactReference, ...]:
        """Validate every required output before publishing any final file."""

        history = self._processing.load_run(
            project_id,
            processing_run_id,
        )
        state = derive_processing_run_state(history)

        if (
            state.run_state != "running"
            or state.processing_stage != AGENTIC_INGESTION_STAGE
            or state.latest_attempt_id != attempt_id
        ):
            raise ProjectIngestionOutputValidationError(
                "Only the current running agentic-ingestion Attempt "
                "may publish artifacts."
            )

        work_root = self._processing.work_directory(
            project_id,
            processing_run_id,
            create=False,
        )
        attempt_work = (
            work_root / AGENTIC_INGESTION_STAGE / attempt_id
        )
        self._assert_safe_directory(
            attempt_work,
            boundary=work_root,
            label="Processing Attempt work directory",
        )

        files = self._collect_publishable_files(attempt_work)
        self._require_unused_targets(
            project_id=project_id,
            processing_run_id=processing_run_id,
            attempt_id=attempt_id,
        )

        created_directories: list[Path] = []
        references: list[ProcessingArtifactReference] = []

        try:
            grouped = {
                artifact_type: tuple(
                    item
                    for item in files
                    if item.artifact_type == artifact_type
                )
                for artifact_type in _ARTIFACT_PREFIXES
            }

            for artifact_type in _ARTIFACT_PREFIXES:
                target_root = (
                    self._processing.prepare_attempt_directory(
                        project_id,
                        processing_run_id,
                        artifact_kind=artifact_type,
                        processing_stage=AGENTIC_INGESTION_STAGE,
                        attempt_id=attempt_id,
                    )
                )
                created_directories.append(target_root)

                for index, item in enumerate(
                    grouped[artifact_type],
                    start=1,
                ):
                    target = target_root / item.relative_target
                    self._assert_target_within(
                        target,
                        target_root,
                    )
                    target.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    if target.exists() or target.is_symlink():
                        raise ProjectIngestionPublicationError(
                            "Published artifact target already exists."
                        )

                    with target.open("xb") as output:
                        output.write(item.content)

                    persisted_fingerprint = hashlib.sha256(
                        target.read_bytes()
                    ).hexdigest()
                    if persisted_fingerprint != item.fingerprint:
                        raise ProjectIngestionPublicationError(
                            "Published artifact fingerprint differs "
                            "from the validated work output."
                        )

                    references.append(
                        create_processing_artifact_reference(
                            artifact_type=artifact_type,
                            artifact_id=(
                                f"{_ARTIFACT_PREFIXES[artifact_type]}-"
                                f"{attempt_id}-{index:04d}"
                            ),
                            content_fingerprint=item.fingerprint,
                            repository_relative_path=(
                                self._repository_relative_posix(
                                    target
                                )
                            ),
                        )
                    )
        except Exception as exc:
            if created_directories:
                raise ProjectIngestionRecoveryRequiredError(
                    "Artifact publication was interrupted after final "
                    "artifact directories were created."
                ) from exc
            if isinstance(
                exc,
                (
                    ProjectIngestionPublicationError,
                    ProjectIngestionOutputValidationError,
                    ProjectIngestionRecoveryRequiredError,
                ),
            ):
                raise
            raise ProjectIngestionPublicationError(
                "Artifact publication could not be started."
            ) from exc

        return tuple(references)

    def _collect_publishable_files(
        self,
        attempt_work: Path,
    ) -> tuple[_PublishableFile, ...]:
        phase_f_root = attempt_work / "phase_f"
        self._assert_safe_directory(
            phase_f_root,
            boundary=attempt_work,
            label="Phase-F execution root",
        )

        grouped_paths: dict[
            str,
            tuple[tuple[Path, Path], ...],
        ] = {
            "agent_outputs": self._collect_tree(
                phase_f_root / "agent_outputs",
                boundary=attempt_work,
                label="Agent Outputs",
            ),
            "consensus_reports": self._collect_tree(
                phase_f_root / "consensus_reports",
                boundary=attempt_work,
                label="Consensus Reports",
            ),
            "review_reports": (
                (
                    attempt_work / "ingestion_review_report.md",
                    Path("ingestion_review_report.md"),
                ),
            ),
            "run_summaries": (
                (
                    phase_f_root
                    / "team_agentic_ingestion_run_summary.json",
                    Path(
                        "team_agentic_ingestion_run_summary.json"
                    ),
                ),
                (
                    phase_f_root
                    / "team_agentic_ingestion_run_summary.md",
                    Path(
                        "team_agentic_ingestion_run_summary.md"
                    ),
                ),
            ),
        }

        publishable: list[_PublishableFile] = []

        for artifact_type, entries in grouped_paths.items():
            if not entries:
                raise ProjectIngestionOutputValidationError(
                    f"{artifact_type} contains no publishable files."
                )

            for source_path, relative_target in entries:
                content = self._read_validated_file(
                    source_path,
                    boundary=attempt_work,
                    label=artifact_type,
                )
                publishable.append(
                    _PublishableFile(
                        artifact_type=artifact_type,
                        source_path=source_path,
                        relative_target=relative_target,
                        content=content,
                        fingerprint=hashlib.sha256(
                            content
                        ).hexdigest(),
                    )
                )

        return tuple(publishable)

    def _collect_tree(
        self,
        root: Path,
        *,
        boundary: Path,
        label: str,
    ) -> tuple[tuple[Path, Path], ...]:
        self._assert_safe_directory(
            root,
            boundary=boundary,
            label=label,
        )

        entries: list[tuple[Path, Path]] = []

        try:
            candidates = sorted(
                root.rglob("*"),
                key=lambda item: item.as_posix(),
            )
        except OSError as exc:
            raise ProjectIngestionOutputValidationError(
                f"{label} could not be inspected."
            ) from exc

        for candidate in candidates:
            if candidate.is_symlink():
                raise ProjectIngestionOutputValidationError(
                    f"{label} contains a symbolic link."
                )
            if candidate.is_dir():
                continue
            if not candidate.is_file():
                raise ProjectIngestionOutputValidationError(
                    f"{label} contains a non-file entry."
                )

            relative = candidate.relative_to(root)
            if any(
                part.startswith(".")
                for part in relative.parts
            ):
                raise ProjectIngestionOutputValidationError(
                    f"{label} contains a hidden output entry."
                )
            entries.append((candidate, relative))

        return tuple(entries)

    def _read_validated_file(
        self,
        path: Path,
        *,
        boundary: Path,
        label: str,
    ) -> bytes:
        self._assert_path_within(path, boundary)

        current = path
        while current != boundary:
            if current.is_symlink():
                raise ProjectIngestionOutputValidationError(
                    f"{label} contains a symbolic-link path."
                )
            current = current.parent

        if not path.exists() or not path.is_file():
            raise ProjectIngestionOutputValidationError(
                f"Required {label} output is missing."
            )

        try:
            content = path.read_bytes()
        except OSError as exc:
            raise ProjectIngestionOutputValidationError(
                f"Required {label} output is unreadable."
            ) from exc

        if not content:
            raise ProjectIngestionOutputValidationError(
                f"Required {label} output is empty."
            )

        return content

    def _require_unused_targets(
        self,
        *,
        project_id: str,
        processing_run_id: str,
        attempt_id: str,
    ) -> None:
        for artifact_type in _ARTIFACT_PREFIXES:
            target = attempt_artifact_path(
                self.root,
                project_id,
                processing_run_id,
                artifact_kind=artifact_type,
                processing_stage=AGENTIC_INGESTION_STAGE,
                attempt_id=attempt_id,
            )
            if target.exists() or target.is_symlink():
                raise ProjectIngestionRecoveryRequiredError(
                    "The Processing Attempt already contains final "
                    "artifact storage and requires recovery."
                )

    def _assert_safe_directory(
        self,
        path: Path,
        *,
        boundary: Path,
        label: str,
    ) -> None:
        self._assert_path_within(path, boundary)
        if path.is_symlink():
            raise ProjectIngestionOutputValidationError(
                f"{label} must not be a symbolic link."
            )
        if not path.exists() or not path.is_dir():
            raise ProjectIngestionOutputValidationError(
                f"{label} is missing."
            )

    @staticmethod
    def _assert_path_within(
        path: Path,
        boundary: Path,
    ) -> None:
        try:
            path.resolve().relative_to(
                boundary.resolve()
            )
        except ValueError as exc:
            raise ProjectIngestionOutputValidationError(
                "Publishable output escaped its work boundary."
            ) from exc

    @staticmethod
    def _assert_target_within(
        path: Path,
        boundary: Path,
    ) -> None:
        try:
            path.resolve().relative_to(
                boundary.resolve()
            )
        except ValueError as exc:
            raise ProjectIngestionPublicationError(
                "Published artifact target escaped its directory."
            ) from exc

    def _repository_relative_posix(
        self,
        path: Path,
    ) -> str:
        try:
            relative = path.resolve().relative_to(
                self.repository_root.resolve()
            )
        except ValueError as exc:
            raise ProjectIngestionPublicationError(
                "Published artifact escaped the repository root."
            ) from exc

        return relative.as_posix()
