"""Project-local read service for deterministic Processing State summaries."""

from __future__ import annotations

from pathlib import Path

from modules.project_sources import (
    ProjectSourceRegistry,
    SourceScanResult,
)
from modules.project_sources.identifiers import validate_source_id

from .aggregation import (
    derive_project_processing_summary,
    derive_source_processing_summaries,
)
from .errors import ProcessingReferenceError
from .operations import ProjectProcessingOperations
from .repository import DEFAULT_PROJECTS_ROOT
from .types import (
    ProcessingScanResult,
    ProjectProcessingSummary,
    SourceProcessingSummary,
)


class ProjectProcessingSummaryService:
    """Compose source and processing scans into regenerable summaries."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        source_registry: ProjectSourceRegistry | None = None,
        processing_operations: ProjectProcessingOperations | None = None,
    ) -> None:
        self.root = Path(root)
        self.source_registry = (
            source_registry
            if source_registry is not None
            else ProjectSourceRegistry(root=self.root)
        )
        self.processing_operations = (
            processing_operations
            if processing_operations is not None
            else ProjectProcessingOperations(root=self.root)
        )

    def collect_scans(
        self,
        project_id: str,
    ) -> tuple[SourceScanResult, ProcessingScanResult]:
        """Collect the authoritative source and processing scan inputs."""

        source_scan = self.source_registry.scan_sources(project_id)
        processing_scan = self.processing_operations.scan_project(project_id)
        return source_scan, processing_scan

    def project_summary(
        self,
        project_id: str,
    ) -> ProjectProcessingSummary:
        """Derive the canonical project-level Processing State projection."""

        source_scan, processing_scan = self.collect_scans(project_id)
        return derive_project_processing_summary(
            project_id,
            source_scan,
            processing_scan,
        )

    def source_summaries(
        self,
        project_id: str,
    ) -> tuple[SourceProcessingSummary, ...]:
        """Derive one deterministic summary per registered source."""

        source_scan, processing_scan = self.collect_scans(project_id)
        return derive_source_processing_summaries(
            project_id,
            source_scan,
            processing_scan,
        )

    def source_summary(
        self,
        project_id: str,
        source_id: str,
    ) -> SourceProcessingSummary:
        """Return one exact source summary or fail explicitly."""

        validated_source_id = validate_source_id(source_id)

        for summary in self.source_summaries(project_id):
            if summary.source_id == validated_source_id:
                return summary

        raise ProcessingReferenceError(
            "Registered source is not present in the project processing "
            f"summary: {project_id}/{validated_source_id}."
        )