"""Immutable types for specialized source-grounded Evidence Detection."""

from __future__ import annotations

from dataclasses import dataclass


EVIDENCE_RELEVANCE_VALUES = frozenset(
    {"relevant", "uncertain", "not_relevant"}
)


@dataclass(frozen=True, slots=True)
class EvidenceCandidateSpan:
    """One deterministic, non-persistent source span selectable by the detector."""

    candidate_span_id: str
    start_offset: int
    end_offset: int
    source_excerpt: str


@dataclass(frozen=True, slots=True)
class DetectedEvidenceSpan:
    """One detector selection resolved deterministically back to exact source."""

    candidate_span_ids: tuple[str, ...]
    source_excerpt: str
    source_start_offset: int
    source_end_offset: int
    relevance: str
    rationale: str


@dataclass(frozen=True, slots=True)
class EvidenceDetectionResult:
    """One persona-independent detector result for one Source Analysis Unit."""

    source_analysis_unit_id: str
    provider: str
    model: str
    prompt_schema_version: str
    reference_examples_sha256: str
    detections: tuple[DetectedEvidenceSpan, ...]
    response_id: str | None
    raw_status: str | None
