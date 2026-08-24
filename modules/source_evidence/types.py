"""Immutable types for persona-independent source-grounded Evidence."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceEvidenceAnchor:
    """One segment-local, zero-based, end-exclusive source range."""

    segment_id: str
    start_offset: int
    end_offset: int


@dataclass(frozen=True, slots=True)
class SourceEvidence:
    """One immutable source-grounded Evidence identity.

    SourceEvidence contains no persona interpretation and no model semantics.
    Its identity is established entirely from Project/Source/Projection binding
    plus exact source anchors and the unchanged source excerpt.
    """

    schema_version: str
    project_id: str
    source_id: str
    source_projection_id: str
    source_evidence_id: str
    source_projection_fingerprint: str
    source_anchors: tuple[SourceEvidenceAnchor, ...]
    source_excerpt: str
    content_fingerprint: str
    created_at: str
