"""Immutable contracts for Phase-L final output publication."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


OUTPUT_FILE_ROLES = (
    "generation_summary",
    "sysml_unit",
    "traceability",
    "validation_report",
    "validation_result",
)


@dataclass(frozen=True, slots=True)
class OutputPublicationProfileReference:
    """Pinned identity of the publication policy used by one OUT package."""

    profile_id: str
    profile_version: str
    profile_fingerprint: str


@dataclass(frozen=True, slots=True)
class OutputPublicationProfile:
    """Versioned deterministic publication policy."""

    schema_version: str
    profile_id: str
    profile_version: str
    name: str
    status: str
    output_root: str
    package_id_pattern: str
    required_file_roles: tuple[str, ...]
    generated_unit_placement: str
    manifest_filename: str
    idempotence_policy: str
    archive_policy: str
    profile_fingerprint: str


@dataclass(frozen=True, slots=True)
class PublishedOutputFileReference:
    """One immutable file entry inside a published output package."""

    relative_path: str
    role: str
    content_fingerprint: str
    source_generated_unit_id: str | None = None


@dataclass(frozen=True, slots=True)
class PublishedOutputManifest:
    """Authoritative immutable index for one published output package."""

    schema_version: str
    project_id: str
    output_package_id: str
    source_internal_engineering_model_id: str
    source_artifact_set_fingerprint: str
    validation_result_fingerprint: str
    final_model_review_id: str
    final_model_review_revision_id: str
    final_review_revision_fingerprint: str
    final_review_decision_id: str
    final_review_decision_fingerprint: str
    final_release_gate_fingerprint: str
    output_profile_reference: OutputPublicationProfileReference
    publication_input_fingerprint: str
    files: tuple[PublishedOutputFileReference, ...]
    published_at: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class PublishedOutputPackage:
    """One validated published output plus its local package location."""

    manifest: PublishedOutputManifest
    package_path: Path


@dataclass(frozen=True, slots=True)
class OutputPublicationRepositoryIssue:
    """One deterministic final-output persistence or integrity issue."""

    project_id: str
    code: str
    message: str
    issue_level: str
    path: Path | None = None
    output_package_id: str | None = None


@dataclass(frozen=True, slots=True)
class OutputPublicationRepositoryScanResult:
    """Validated published outputs plus explicit repository diagnostics."""

    packages: tuple[PublishedOutputPackage, ...] = ()
    issues: tuple[OutputPublicationRepositoryIssue, ...] = ()
