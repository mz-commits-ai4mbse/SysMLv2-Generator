"""Deterministic plain-text and Markdown Source Projection adapters."""

from __future__ import annotations

from .errors import (
    SourceAdapterError,
    UnsupportedSourceFormatError,
    UnsupportedTextEncodingError,
)
from .types import (
    ProjectionIssue,
    ProjectionSegmentDraft,
    SourceLocator,
    SourceProjectionDraft,
)


TEXT_ADAPTER_VERSION = "1.0.0"

PLAIN_TEXT_ADAPTER_ID = "plain_text"
MARKDOWN_ADAPTER_ID = "markdown"

PLAIN_TEXT_FORMAT = "text"
MARKDOWN_FORMAT = "markdown"

SUPPORTED_TEXT_FORMATS = frozenset(
    {
        PLAIN_TEXT_FORMAT,
        MARKDOWN_FORMAT,
    }
)

_UTF8_BOM = b"\xef\xbb\xbf"


def project_plain_text(content: bytes) -> SourceProjectionDraft:
    """Project UTF-8 plain-text bytes deterministically."""

    return project_text_bytes(
        content,
        source_format=PLAIN_TEXT_FORMAT,
    )


def project_markdown(content: bytes) -> SourceProjectionDraft:
    """Project UTF-8 Markdown bytes deterministically."""

    return project_text_bytes(
        content,
        source_format=MARKDOWN_FORMAT,
    )


def project_text_bytes(
    content: bytes,
    *,
    source_format: str,
) -> SourceProjectionDraft:
    """Project accepted UTF-8 text bytes into ordered blocks."""

    if not isinstance(content, bytes):
        raise SourceAdapterError(
            "Text adapter content must be bytes."
        )

    if source_format not in SUPPORTED_TEXT_FORMATS:
        allowed_formats = ", ".join(
            sorted(SUPPORTED_TEXT_FORMATS)
        )
        raise UnsupportedSourceFormatError(
            "Unsupported text source_format: "
            f"{source_format!r}. Expected one of: "
            f"{allowed_formats}."
        )

    has_utf8_bom = content.startswith(_UTF8_BOM)

    try:
        decoded_text = content.decode(
            "utf-8-sig" if has_utf8_bom else "utf-8"
        )
    except UnicodeDecodeError as exc:
        raise UnsupportedTextEncodingError(
            "Text source must use UTF-8 or UTF-8 with BOM."
        ) from exc

    normalized_text = _normalize_line_endings(
        decoded_text
    )

    segment_type = (
        "text_block"
        if source_format == PLAIN_TEXT_FORMAT
        else "markdown_block"
    )
    adapter_id = (
        PLAIN_TEXT_ADAPTER_ID
        if source_format == PLAIN_TEXT_FORMAT
        else MARKDOWN_ADAPTER_ID
    )

    segments = _segment_nonempty_blocks(
        normalized_text,
        segment_type=segment_type,
    )

    adapter_configuration = (
        ("encoding", "utf-8"),
        (
            "leading_utf8_bom",
            "removed" if has_utf8_bom else "absent",
        ),
        ("line_endings", "lf"),
        ("segmentation", "blank_line_blocks"),
    )

    if not segments:
        return SourceProjectionDraft(
            adapter_id=adapter_id,
            adapter_version=TEXT_ADAPTER_VERSION,
            adapter_configuration=adapter_configuration,
            projection_result="unavailable",
            segments=(),
            issues=(
                ProjectionIssue(
                    code="NO_TEXT_CONTENT",
                    message=(
                        "The source contains no non-whitespace "
                        "text blocks."
                    ),
                    issue_level="error",
                ),
            ),
        )

    return SourceProjectionDraft(
        adapter_id=adapter_id,
        adapter_version=TEXT_ADAPTER_VERSION,
        adapter_configuration=adapter_configuration,
        projection_result="complete",
        segments=segments,
    )


def _normalize_line_endings(text: str) -> str:
    """Normalize CRLF and CR line endings to LF."""

    return text.replace("\r\n", "\n").replace("\r", "\n")


def _segment_nonempty_blocks(
    text: str,
    *,
    segment_type: str,
) -> tuple[ProjectionSegmentDraft, ...]:
    """Split text at blank lines while preserving block text."""

    lines = text.split("\n")
    segments: list[ProjectionSegmentDraft] = []

    block_lines: list[str] = []
    block_start_line: int | None = None

    for line_number, line in enumerate(
        lines,
        start=1,
    ):
        if line.strip():
            if block_start_line is None:
                block_start_line = line_number

            block_lines.append(line)
            continue

        if block_start_line is not None:
            segments.append(
                _create_block_segment(
                    segment_type=segment_type,
                    block_lines=block_lines,
                    start_line=block_start_line,
                    end_line=line_number - 1,
                )
            )
            block_lines = []
            block_start_line = None

    if block_start_line is not None:
        segments.append(
            _create_block_segment(
                segment_type=segment_type,
                block_lines=block_lines,
                start_line=block_start_line,
                end_line=len(lines),
            )
        )

    return tuple(segments)


def _create_block_segment(
    *,
    segment_type: str,
    block_lines: list[str],
    start_line: int,
    end_line: int,
) -> ProjectionSegmentDraft:
    """Create one source-located text block."""

    locator = SourceLocator(
        locator_type="line_range",
        coordinates=(
            ("line_start", start_line),
            ("line_end", end_line),
        ),
    )

    return ProjectionSegmentDraft(
        segment_type=segment_type,
        text="\n".join(block_lines),
        source_locators=(locator,),
    )