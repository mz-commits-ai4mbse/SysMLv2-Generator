"""Reusable Source Preparation with specialized Evidence Detection."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from modules.evidence_detection import (
    EVIDENCE_DETECTION_PROMPT_SCHEMA_VERSION,
    EvidenceDetectionAgent,
    EvidenceDetectionReferenceError,
    resolve_detection_anchors,
)
from modules.project_sources import (
    CONTEXT_ONLY_SOURCE_ROLE,
    ENGINEERING_SOURCE_ROLE,
    ProjectSourceRegistry,
)
from modules.project_workspace import ProjectWorkspace
from modules.source_analysis_units import SourceAnalysisUnitRepository
from modules.source_evidence import SourceEvidenceRepository
from modules.source_projection.repository import (
    SourceProjectionRepository,
)

from .types import (
    SOURCE_PREPARATION_SCHEMA_VERSION,
    SOURCE_PREPARATION_STATUSES,
    SourcePreparationResult,
)


DEFAULT_PROJECTS_ROOT = Path("data/projects")
DEFAULT_REFERENCE_EXAMPLES_PATH = Path(
    "context/evidence_detection/source_grounding_examples.md"
)
SEMANTICS_DIRECTORY_NAME = "semantics"
SOURCE_PREPARATION_DIRECTORY_NAME = "source_preparation"


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class SourcePreparationService:
    """Prepare one registered Source for later persona interpretation."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        repository_root: Path | str = Path("."),
        clock: Callable[[], datetime] = _default_clock,
        source_registry: ProjectSourceRegistry | None = None,
        source_projection_repository: SourceProjectionRepository | None = None,
        source_analysis_unit_repository: SourceAnalysisUnitRepository | None = None,
        source_evidence_repository: SourceEvidenceRepository | None = None,
        detector: EvidenceDetectionAgent | None = None,
        reference_examples_path: Path | str = DEFAULT_REFERENCE_EXAMPLES_PATH,
    ) -> None:
        self.root = Path(root)
        self.repository_root = Path(repository_root)
        self._clock = clock
        self._workspace = ProjectWorkspace(root=self.root, clock=clock)
        self._source_registry = (
            ProjectSourceRegistry(root=self.root, clock=clock)
            if source_registry is None
            else source_registry
        )
        self._source_projections = (
            SourceProjectionRepository(root=self.root, clock=clock)
            if source_projection_repository is None
            else source_projection_repository
        )
        self._source_analysis_units = (
            SourceAnalysisUnitRepository(
                root=self.root,
                clock=clock,
                source_projection_repository=self._source_projections,
            )
            if source_analysis_unit_repository is None
            else source_analysis_unit_repository
        )
        self._source_evidence = (
            SourceEvidenceRepository(
                root=self.root,
                clock=clock,
                source_projection_repository=self._source_projections,
            )
            if source_evidence_repository is None
            else source_evidence_repository
        )
        self._detector = (
            EvidenceDetectionAgent()
            if detector is None
            else detector
        )
        self._reference_examples_path = Path(reference_examples_path)

    def prepare_registered_source(
        self,
        project_id: str,
        source_id: str,
        *,
        provider: str,
        model: str,
        api_key: str | None = None,
        dry_run: bool = False,
    ) -> SourcePreparationResult:
        """Prepare one Source once per material detector configuration."""

        self._workspace.load_project(project_id)
        source = self._source_registry.load_source(project_id, source_id)
        projection = self._source_projections.create_projection(
            project_id,
            source_id,
        )
        units = self._source_analysis_units.ensure_projection_units(
            project_id,
            projection.manifest.source_projection_id,
        )
        reference_examples = self._load_reference_examples()
        reference_sha = sha256(
            reference_examples.encode("utf-8")
        ).hexdigest()

        fingerprint = calculate_source_preparation_fingerprint(
            source_projection_fingerprint=(
                projection.manifest.projection_fingerprint
            ),
            provider=provider,
            model=model,
            prompt_schema_version=(
                EVIDENCE_DETECTION_PROMPT_SCHEMA_VERSION
            ),
            reference_examples_sha256=reference_sha,
            dry_run=dry_run,
        )

        existing = self._load_existing(
            project_id,
            projection.manifest.source_projection_id,
            fingerprint,
        )
        if existing is not None:
            return existing

        if source.source_role == CONTEXT_ONLY_SOURCE_ROLE:
            result = self._result(
                project_id=project_id,
                source_id=source_id,
                projection=projection,
                provider=provider,
                model=model,
                reference_sha=reference_sha,
                dry_run=dry_run,
                unit_ids=tuple(
                    unit.source_analysis_unit_id for unit in units
                ),
                evidence_ids=(),
                response_ids=(),
                status="skipped_context_only",
                fingerprint=fingerprint,
            )
            self._persist(result)
            return result

        if source.source_role != ENGINEERING_SOURCE_ROLE:
            raise EvidenceDetectionReferenceError(
                "Only engineering_source may enter Evidence Detection."
            )

        evidence_ids: list[str] = []
        response_ids: list[str | None] = []

        for unit in units:
            detected = self._detector.detect(
                source_analysis_unit=unit,
                reference_examples=reference_examples,
                provider=provider,
                model=model,
                api_key=api_key,
                dry_run=dry_run,
            )
            response_ids.append(detected.response_id)

            for finding in detected.detections:
                if finding.relevance == "not_relevant":
                    continue
                anchors = resolve_detection_anchors(
                    source_analysis_unit=unit,
                    detected_excerpt=finding.source_excerpt,
                    source_start_offset=finding.source_start_offset,
                    source_end_offset=finding.source_end_offset,
                )
                evidence = self._source_evidence.create_or_reuse_evidence(
                    project_id,
                    projection.manifest.source_projection_id,
                    source_anchors=anchors,
                    source_excerpt=finding.source_excerpt,
                )
                if evidence.source_evidence_id not in evidence_ids:
                    evidence_ids.append(evidence.source_evidence_id)

        result = self._result(
            project_id=project_id,
            source_id=source_id,
            projection=projection,
            provider=provider,
            model=model,
            reference_sha=reference_sha,
            dry_run=dry_run,
            unit_ids=tuple(
                unit.source_analysis_unit_id for unit in units
            ),
            evidence_ids=tuple(evidence_ids),
            response_ids=tuple(response_ids),
            status="dry_run" if dry_run else "prepared",
            fingerprint=fingerprint,
        )
        self._persist(result)
        return result

    def _result(
        self,
        *,
        project_id: str,
        source_id: str,
        projection: Any,
        provider: str,
        model: str,
        reference_sha: str,
        dry_run: bool,
        unit_ids: tuple[str, ...],
        evidence_ids: tuple[str, ...],
        response_ids: tuple[str | None, ...],
        status: str,
        fingerprint: str,
    ) -> SourcePreparationResult:
        if status not in SOURCE_PREPARATION_STATUSES:
            raise EvidenceDetectionReferenceError(
                f"Unsupported Source Preparation status: {status}"
            )
        return SourcePreparationResult(
            schema_version=SOURCE_PREPARATION_SCHEMA_VERSION,
            project_id=project_id,
            source_id=source_id,
            source_projection_id=(
                projection.manifest.source_projection_id
            ),
            source_projection_fingerprint=(
                projection.manifest.projection_fingerprint
            ),
            provider=provider,
            model=model,
            prompt_schema_version=(
                EVIDENCE_DETECTION_PROMPT_SCHEMA_VERSION
            ),
            reference_examples_sha256=reference_sha,
            dry_run=dry_run,
            source_analysis_unit_ids=unit_ids,
            source_evidence_ids=evidence_ids,
            detector_response_ids=response_ids,
            status=status,
            preparation_fingerprint=fingerprint,
            created_at=self._timestamp(),
        )

    def _load_reference_examples(self) -> str:
        path = self._reference_examples_path
        if not path.is_absolute():
            path = self.repository_root / path
        if not path.is_file():
            raise EvidenceDetectionReferenceError(
                f"Evidence Detection reference examples not found: {path}"
            )
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise EvidenceDetectionReferenceError(
                f"Unable to read Evidence Detection examples: {path}"
            ) from exc
        if not text.strip():
            raise EvidenceDetectionReferenceError(
                "Evidence Detection reference examples must not be empty."
            )
        return text

    def _path(
        self,
        project_id: str,
        source_projection_id: str,
        fingerprint: str,
    ) -> Path:
        self._workspace.load_project(project_id)
        return (
            self.root
            / project_id
            / SEMANTICS_DIRECTORY_NAME
            / SOURCE_PREPARATION_DIRECTORY_NAME
            / source_projection_id
            / f"{fingerprint}.json"
        )

    def _load_existing(
        self,
        project_id: str,
        source_projection_id: str,
        fingerprint: str,
    ) -> SourcePreparationResult | None:
        path = self._path(
            project_id,
            source_projection_id,
            fingerprint,
        )
        if not path.exists():
            return None
        if path.is_symlink() or not path.is_file():
            raise EvidenceDetectionReferenceError(
                f"Unsafe Source Preparation result path: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise EvidenceDetectionReferenceError(
                f"Invalid Source Preparation result: {path}"
            ) from exc
        result = source_preparation_result_from_dict(payload)
        if (
            result.project_id != project_id
            or result.source_projection_id != source_projection_id
            or result.preparation_fingerprint != fingerprint
        ):
            raise EvidenceDetectionReferenceError(
                "Persisted Source Preparation binding is inconsistent."
            )
        return result

    def _persist(self, result: SourcePreparationResult) -> None:
        path = self._path(
            result.project_id,
            result.source_projection_id,
            result.preparation_fingerprint,
        )
        if path.exists() or path.is_symlink():
            raise EvidenceDetectionReferenceError(
                "Source Preparation result already exists unexpectedly."
            )
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    source_preparation_result_to_dict(result),
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            raise EvidenceDetectionReferenceError(
                f"Unable to persist Source Preparation result: {path}"
            ) from exc

    def _timestamp(self) -> str:
        value = self._clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return (
            value.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )


def calculate_source_preparation_fingerprint(
    *,
    source_projection_fingerprint: str,
    provider: str,
    model: str,
    prompt_schema_version: str,
    reference_examples_sha256: str,
    dry_run: bool,
) -> str:
    """Fingerprint material Source Preparation inputs without secrets."""

    canonical = json.dumps(
        {
            "dry_run": dry_run,
            "model": model,
            "prompt_schema_version": prompt_schema_version,
            "provider": provider,
            "reference_examples_sha256": reference_examples_sha256,
            "source_projection_fingerprint": (
                source_projection_fingerprint
            ),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def source_preparation_result_to_dict(
    result: SourcePreparationResult,
) -> dict[str, Any]:
    return {
        "schema_version": result.schema_version,
        "project_id": result.project_id,
        "source_id": result.source_id,
        "source_projection_id": result.source_projection_id,
        "source_projection_fingerprint": (
            result.source_projection_fingerprint
        ),
        "provider": result.provider,
        "model": result.model,
        "prompt_schema_version": result.prompt_schema_version,
        "reference_examples_sha256": (
            result.reference_examples_sha256
        ),
        "dry_run": result.dry_run,
        "source_analysis_unit_ids": list(
            result.source_analysis_unit_ids
        ),
        "source_evidence_ids": list(result.source_evidence_ids),
        "detector_response_ids": list(
            result.detector_response_ids
        ),
        "status": result.status,
        "preparation_fingerprint": (
            result.preparation_fingerprint
        ),
        "created_at": result.created_at,
    }


def source_preparation_result_from_dict(
    payload: Any,
) -> SourcePreparationResult:
    expected = {
        "schema_version",
        "project_id",
        "source_id",
        "source_projection_id",
        "source_projection_fingerprint",
        "provider",
        "model",
        "prompt_schema_version",
        "reference_examples_sha256",
        "dry_run",
        "source_analysis_unit_ids",
        "source_evidence_ids",
        "detector_response_ids",
        "status",
        "preparation_fingerprint",
        "created_at",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise EvidenceDetectionReferenceError(
            "Source Preparation result fields do not match schema."
        )
    if payload["schema_version"] != SOURCE_PREPARATION_SCHEMA_VERSION:
        raise EvidenceDetectionReferenceError(
            "Unsupported Source Preparation schema_version."
        )
    if payload["status"] not in SOURCE_PREPARATION_STATUSES:
        raise EvidenceDetectionReferenceError(
            "Unsupported Source Preparation status."
        )
    for name in (
        "source_analysis_unit_ids",
        "source_evidence_ids",
        "detector_response_ids",
    ):
        if not isinstance(payload[name], list):
            raise EvidenceDetectionReferenceError(
                f"{name} must be a list."
            )

    return SourcePreparationResult(
        schema_version=payload["schema_version"],
        project_id=payload["project_id"],
        source_id=payload["source_id"],
        source_projection_id=payload["source_projection_id"],
        source_projection_fingerprint=(
            payload["source_projection_fingerprint"]
        ),
        provider=payload["provider"],
        model=payload["model"],
        prompt_schema_version=payload["prompt_schema_version"],
        reference_examples_sha256=(
            payload["reference_examples_sha256"]
        ),
        dry_run=payload["dry_run"],
        source_analysis_unit_ids=tuple(
            payload["source_analysis_unit_ids"]
        ),
        source_evidence_ids=tuple(payload["source_evidence_ids"]),
        detector_response_ids=tuple(
            payload["detector_response_ids"]
        ),
        status=payload["status"],
        preparation_fingerprint=(
            payload["preparation_fingerprint"]
        ),
        created_at=payload["created_at"],
    )
