"""Immutable types for source-anchored multi-persona analysis."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceAnalysisUnitAnchor:
    """One segment-local, zero-based, end-exclusive source range."""

    segment_id: str
    start_offset: int
    end_offset: int


@dataclass(frozen=True, slots=True)
class SourceAnalysisUnit:
    """One immutable persona-independent source analysis scope."""

    schema_version: str
    project_id: str
    source_id: str
    source_projection_id: str
    source_analysis_unit_id: str
    source_projection_fingerprint: str
    source_anchors: tuple[SourceAnalysisUnitAnchor, ...]
    source_excerpt: str
    source_order_index: int
    segmentation_profile_id: str
    segmentation_profile_version: str
    content_fingerprint: str
    created_at: str
