"""Immutable data types for deterministic Source Projections."""

from __future__ import annotations

from dataclasses import dataclass


LocatorValue = str | int
AdapterConfigurationValue = str | int | bool | None
AdapterConfiguration = tuple[
    tuple[str, AdapterConfigurationValue],
    ...,
]


@dataclass(frozen=True, slots=True)
class SourceLocator:
    """One machine-readable location in an original source."""

    locator_type: str
    coordinates: tuple[
        tuple[str, LocatorValue],
        ...,
    ]


@dataclass(frozen=True, slots=True)
class ProjectionIssue:
    """One deterministic issue discovered during projection."""

    code: str
    message: str
    issue_level: str
    source_locators: tuple[SourceLocator, ...] = ()


@dataclass(frozen=True, slots=True)
class ProjectionSegmentDraft:
    """One ordered adapter segment before persistent IDs are assigned."""

    segment_type: str
    text: str
    source_locators: tuple[SourceLocator, ...]


@dataclass(frozen=True, slots=True)
class SourceProjectionDraft:
    """Deterministic adapter output before repository persistence."""

    adapter_id: str
    adapter_version: str
    adapter_configuration: AdapterConfiguration
    projection_result: str
    segments: tuple[ProjectionSegmentDraft, ...]
    issues: tuple[ProjectionIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class ProjectionSegment:
    """One persisted segment within a Source Projection."""

    segment_id: str
    segment_type: str
    start_offset: int
    end_offset: int
    text_sha256: str
    source_locators: tuple[SourceLocator, ...]


@dataclass(frozen=True, slots=True)
class SourceProjectionManifest:
    """Validated metadata for one persisted Source Projection."""

    schema_version: str
    project_id: str
    source_id: str
    source_projection_id: str
    source_role: str
    source_sha256: str
    adapter_id: str
    adapter_version: str
    adapter_configuration: AdapterConfiguration
    projection_fingerprint: str
    projection_result: str
    content_sha256: str
    content_length: int
    segments: tuple[ProjectionSegment, ...]
    issues: tuple[ProjectionIssue, ...]
    created_at: str


@dataclass(frozen=True, slots=True)
class SourceProjectionArtifact:
    """One validated manifest together with its projected UTF-8 text."""

    manifest: SourceProjectionManifest
    content: str