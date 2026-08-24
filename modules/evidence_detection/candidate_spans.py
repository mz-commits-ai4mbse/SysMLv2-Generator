"""Deterministic candidate spans for source-grounded Evidence Detection."""

from __future__ import annotations

import re

from modules.source_analysis_units.types import SourceAnalysisUnit

from .errors import (
    EvidenceDetectionGroundingError,
    EvidenceDetectionValidationError,
)
from .types import EvidenceCandidateSpan


_CANDIDATE_ID_PATTERN = re.compile(r"^CAND-[0-9]{3}$")
_BULLET_START = re.compile(
    r"(?m)^[ \t]*(?:[-*+]|\d+[.)])[ \t]+"
)
_SENTENCE_END = re.compile(
    r"""[.!?](?:["')\]]+)?(?=\s+|$)"""
)


def build_candidate_spans(
    source_analysis_unit: SourceAnalysisUnit,
) -> tuple[EvidenceCandidateSpan, ...]:
    """Split one SAU into deterministic, exact, non-persistent candidate spans."""

    if not isinstance(source_analysis_unit, SourceAnalysisUnit):
        raise EvidenceDetectionValidationError(
            "source_analysis_unit must be a SourceAnalysisUnit instance."
        )

    text = source_analysis_unit.source_excerpt
    if not isinstance(text, str) or not text:
        raise EvidenceDetectionValidationError(
            "Source Analysis Unit source_excerpt must be non-empty."
        )

    ranges = _candidate_ranges(text)
    if not ranges:
        raise EvidenceDetectionValidationError(
            "Source Analysis Unit produced no selectable candidate spans."
        )
    if len(ranges) > 999:
        raise EvidenceDetectionValidationError(
            "Source Analysis Unit exceeds the supported candidate span count."
        )

    result = []
    for index, (start, end) in enumerate(ranges, start=1):
        excerpt = text[start:end]
        if not excerpt:
            raise EvidenceDetectionGroundingError(
                "Candidate span resolved to empty source text."
            )
        result.append(
            EvidenceCandidateSpan(
                candidate_span_id=f"CAND-{index:03d}",
                start_offset=start,
                end_offset=end,
                source_excerpt=excerpt,
            )
        )

    return tuple(result)


def resolve_candidate_span_selection(
    *,
    source_analysis_unit: SourceAnalysisUnit,
    candidate_spans: tuple[EvidenceCandidateSpan, ...],
    candidate_span_ids: tuple[str, ...],
) -> tuple[str, int, int]:
    """Resolve ordered contiguous candidate IDs to one exact source slice."""

    if not isinstance(source_analysis_unit, SourceAnalysisUnit):
        raise EvidenceDetectionGroundingError(
            "source_analysis_unit must be a SourceAnalysisUnit instance."
        )
    if not isinstance(candidate_spans, tuple) or not candidate_spans:
        raise EvidenceDetectionGroundingError(
            "candidate_spans must be a non-empty tuple."
        )
    if not isinstance(candidate_span_ids, tuple) or not candidate_span_ids:
        raise EvidenceDetectionValidationError(
            "candidate_span_ids must be a non-empty tuple."
        )

    if len(set(candidate_span_ids)) != len(candidate_span_ids):
        raise EvidenceDetectionValidationError(
            "candidate_span_ids must not contain duplicates."
        )

    by_id = {
        candidate.candidate_span_id: (index, candidate)
        for index, candidate in enumerate(candidate_spans)
    }

    resolved = []
    for candidate_span_id in candidate_span_ids:
        if (
            not isinstance(candidate_span_id, str)
            or _CANDIDATE_ID_PATTERN.fullmatch(candidate_span_id) is None
        ):
            raise EvidenceDetectionValidationError(
                "candidate_span_ids must contain canonical CAND-NNN identifiers."
            )
        item = by_id.get(candidate_span_id)
        if item is None:
            raise EvidenceDetectionGroundingError(
                "Detector selected an unknown candidate span ID."
            )
        resolved.append(item)

    positions = [index for index, _ in resolved]
    if positions != sorted(positions):
        raise EvidenceDetectionGroundingError(
            "Detector candidate span IDs must preserve source order."
        )
    if any(
        right != left + 1
        for left, right in zip(positions, positions[1:])
    ):
        raise EvidenceDetectionGroundingError(
            "Detector candidate span IDs must form one contiguous source range."
        )

    first = resolved[0][1]
    last = resolved[-1][1]
    start = first.start_offset
    end = last.end_offset

    text = source_analysis_unit.source_excerpt
    excerpt = text[start:end]
    if not excerpt:
        raise EvidenceDetectionGroundingError(
            "Detector candidate selection resolved to empty source text."
        )

    for _, candidate in resolved:
        if text[
            candidate.start_offset:candidate.end_offset
        ] != candidate.source_excerpt:
            raise EvidenceDetectionGroundingError(
                "Candidate span no longer matches exact Source Analysis Unit text."
            )

    return excerpt, start, end


def _candidate_ranges(text: str) -> tuple[tuple[int, int], ...]:
    content_start, content_end = _trimmed_range(text, 0, len(text))
    if content_start >= content_end:
        return ()

    content = text[content_start:content_end]

    bullet_matches = tuple(_BULLET_START.finditer(content))
    if bullet_matches and bullet_matches[0].start() == 0:
        ranges = []
        for index, match in enumerate(bullet_matches):
            start = content_start + match.start()
            end = (
                content_start + bullet_matches[index + 1].start()
                if index + 1 < len(bullet_matches)
                else content_end
            )
            trimmed_start, trimmed_end = _trimmed_range(text, start, end)
            if trimmed_start < trimmed_end:
                ranges.append((trimmed_start, trimmed_end))
        if ranges:
            return tuple(ranges)

    ranges = []
    cursor = content_start
    for match in _SENTENCE_END.finditer(text, content_start, content_end):
        end = match.end()
        start, trimmed_end = _trimmed_range(text, cursor, end)
        if start < trimmed_end:
            ranges.append((start, trimmed_end))
        cursor = end

    tail_start, tail_end = _trimmed_range(text, cursor, content_end)
    if tail_start < tail_end:
        ranges.append((tail_start, tail_end))

    if not ranges:
        return ((content_start, content_end),)

    return tuple(ranges)


def _trimmed_range(
    text: str,
    start: int,
    end: int,
) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end
