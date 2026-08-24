"""Build readable source context with system-owned mention addresses."""

from __future__ import annotations

import json
import re

from modules.source_evidence.types import SourceEvidence
from modules.source_projection.identifiers import segment_id_sequence
from modules.source_projection.types import (
    ProjectionSegment,
    SourceProjectionArtifact,
)

from .errors import (
    EngineeringSubjectConfigurationError,
    EngineeringSubjectIntegrityError,
)
from .identifiers import (
    format_source_span_id,
    format_source_token_id,
)
from .types import (
    DiscoverySourceSpan,
    DiscoverySourceToken,
)


_BOUNDARY_PATTERN = re.compile(r"(?<=[.!?])(?=\s+)")
_TOKEN_PATTERN = re.compile(
    r"\w+(?:[-'][\w]+)*|[^\w\s]",
    re.UNICODE,
)


def build_discovery_source_spans(
    source_projection: SourceProjectionArtifact,
    source_evidence: tuple[SourceEvidence, ...],
) -> tuple[DiscoverySourceSpan, ...]:
    """Build readable spans plus exact system-owned token addresses."""

    if not isinstance(source_projection, SourceProjectionArtifact):
        raise EngineeringSubjectConfigurationError(
            "source_projection must be a SourceProjectionArtifact."
        )
    if source_projection.manifest.projection_result == "unavailable":
        raise EngineeringSubjectConfigurationError(
            "Unavailable Source Projection cannot enter subject discovery."
        )
    if not isinstance(source_evidence, tuple):
        raise EngineeringSubjectConfigurationError(
            "source_evidence must be a tuple."
        )

    _validate_evidence_binding(source_projection, source_evidence)

    segments = tuple(
        sorted(
            source_projection.manifest.segments,
            key=lambda value: segment_id_sequence(value.segment_id),
        )
    )

    span_drafts = []
    for segment in segments:
        segment_text = _segment_text(source_projection, segment)
        for start, end in _split_segment(segment_text):
            exact_text = segment_text[start:end]
            evidence_ids = _overlapping_evidence_ids(
                source_evidence,
                segment_id=segment.segment_id,
                start_offset=start,
                end_offset=end,
            )
            if _is_markdown_heading(exact_text):
                evidence_ids = ()
            span_drafts.append(
                (
                    segment.segment_id,
                    start,
                    end,
                    exact_text,
                    evidence_ids,
                )
            )

    if not span_drafts:
        raise EngineeringSubjectConfigurationError(
            "Subject discovery requires at least one non-empty source span."
        )

    spans = []
    token_sequence = 1

    for span_sequence, draft in enumerate(span_drafts, start=1):
        segment_id, start, end, exact_text, evidence_ids = draft
        span_id = format_source_span_id(span_sequence)
        tokens = []

        for match in _TOKEN_PATTERN.finditer(exact_text):
            token_start = start + match.start()
            token_end = start + match.end()
            tokens.append(
                DiscoverySourceToken(
                    token_id=format_source_token_id(token_sequence),
                    source_span_id=span_id,
                    segment_id=segment_id,
                    start_offset=token_start,
                    end_offset=token_end,
                    exact_text=match.group(0),
                )
            )
            token_sequence += 1

        if not tokens:
            raise EngineeringSubjectIntegrityError(
                f"Source Span {span_id} contains no addressable tokens."
            )

        spans.append(
            DiscoverySourceSpan(
                span_id=span_id,
                segment_id=segment_id,
                start_offset=start,
                end_offset=end,
                exact_text=exact_text,
                source_evidence_ids=evidence_ids,
                source_tokens=tuple(tokens),
            )
        )

    return tuple(spans)


def build_context_preserving_source_input(
    source_projection: SourceProjectionArtifact,
    spans: tuple[DiscoverySourceSpan, ...],
) -> str:
    """Render intact readable source plus separate system-owned token map."""

    if not spans:
        raise EngineeringSubjectConfigurationError(
            "spans must not be empty."
        )

    lines = [
        "BEGIN_ENGINEERING_SOURCE_CONTEXT",
        (
            "The text below is the registered Engineering Source. "
            "SPAN-* and TOK-* labels are system-owned addresses, "
            "not source content."
        ),
        (
            "Only spans marked EVIDENCE may establish positive mentions. "
            "Other spans are context only."
        ),
        (
            "Read the SOURCE TEXT normally. Use the TOKEN MAP only to "
            "address exact mention boundaries in your JSON."
        ),
        "",
    ]

    current_segment = None

    for span in spans:
        if span.segment_id != current_segment:
            if current_segment is not None:
                lines.append("")
            lines.append(f"--- {span.segment_id} ---")
            current_segment = span.segment_id

        evidence_label = (
            ",".join(span.source_evidence_ids)
            if span.source_evidence_ids
            else "context_only"
        )

        token_map = " | ".join(
            f"{token.token_id}={json.dumps(token.exact_text, ensure_ascii=False)}"
            for token in span.source_tokens
        )

        lines.extend(
            [
                f"[{span.span_id} | {evidence_label}]",
                "SOURCE TEXT:",
                span.exact_text,
                "TOKEN MAP:",
                token_map,
                "",
            ]
        )

    lines.append("END_ENGINEERING_SOURCE_CONTEXT")
    return "\n".join(lines)


def _is_markdown_heading(text: str) -> bool:
    """Return True only for a Markdown ATX heading source span."""

    return bool(re.match(r"^#{1,6}(?:\s|$)", text.lstrip()))


def _split_segment(text: str) -> tuple[tuple[int, int], ...]:
    """Return exact non-whitespace sentence/bullet/heading ranges."""

    ranges = []
    block_start = 0

    for match in re.finditer(r"\n\s*\n", text):
        ranges.extend(_split_block(text, block_start, match.start()))
        block_start = match.end()

    ranges.extend(_split_block(text, block_start, len(text)))

    return tuple(
        value
        for value in ranges
        if value[0] < value[1]
    )


def _split_block(
    text: str,
    raw_start: int,
    raw_end: int,
) -> tuple[tuple[int, int], ...]:
    start, end = _trim_range(text, raw_start, raw_end)

    if start >= end:
        return ()

    block = text[start:end]
    stripped = block.lstrip()

    if (
        stripped.startswith("#")
        or stripped.startswith("- ")
        or stripped.startswith("* ")
        or re.match(r"^[0-9]+[.)]\s", stripped)
    ):
        return ((start, end),)

    ranges = []
    local_start = 0

    for match in _BOUNDARY_PATTERN.finditer(block):
        local_end = match.start()
        item_start, item_end = _trim_range(
            block,
            local_start,
            local_end,
        )
        if item_start < item_end:
            ranges.append(
                (start + item_start, start + item_end)
            )
        local_start = match.end()

    item_start, item_end = _trim_range(
        block,
        local_start,
        len(block),
    )
    if item_start < item_end:
        ranges.append((start + item_start, start + item_end))

    return tuple(ranges)


def _trim_range(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _segment_text(
    projection: SourceProjectionArtifact,
    segment: ProjectionSegment,
) -> str:
    text = projection.content[segment.start_offset:segment.end_offset]
    if not text:
        raise EngineeringSubjectIntegrityError(
            f"Projection segment {segment.segment_id} is empty."
        )
    return text


def _validate_evidence_binding(
    projection: SourceProjectionArtifact,
    evidence: tuple[SourceEvidence, ...],
) -> None:
    seen_ids = set()

    for item in evidence:
        if not isinstance(item, SourceEvidence):
            raise EngineeringSubjectConfigurationError(
                "source_evidence entries must be SourceEvidence objects."
            )

        if (
            item.project_id != projection.manifest.project_id
            or item.source_id != projection.manifest.source_id
            or item.source_projection_id
            != projection.manifest.source_projection_id
            or item.source_projection_fingerprint
            != projection.manifest.projection_fingerprint
        ):
            raise EngineeringSubjectIntegrityError(
                "Source Evidence does not bind the supplied Source Projection."
            )

        if item.source_evidence_id in seen_ids:
            raise EngineeringSubjectIntegrityError(
                "Source Evidence IDs must be unique."
            )

        seen_ids.add(item.source_evidence_id)


def _overlapping_evidence_ids(
    evidence: tuple[SourceEvidence, ...],
    *,
    segment_id: str,
    start_offset: int,
    end_offset: int,
) -> tuple[str, ...]:
    ids = []

    for item in evidence:
        if any(
            anchor.segment_id == segment_id
            and anchor.start_offset < end_offset
            and start_offset < anchor.end_offset
            for anchor in item.source_anchors
        ):
            ids.append(item.source_evidence_id)

    return tuple(sorted(ids))
