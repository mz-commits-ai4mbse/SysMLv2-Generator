"""Deterministic CSV and TSV Source Projection adapters."""

from __future__ import annotations

import csv
from io import StringIO
import json

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


TABLE_ADAPTER_VERSION = "1.0.0"

CSV_ADAPTER_ID = "csv"
TSV_ADAPTER_ID = "tsv"

CSV_FORMAT = "csv"
TSV_FORMAT = "tsv"

SUPPORTED_TABLE_FORMATS = frozenset(
    {
        CSV_FORMAT,
        TSV_FORMAT,
    }
)

_DELIMITER_BY_FORMAT = {
    CSV_FORMAT: ",",
    TSV_FORMAT: "\t",
}

_UTF8_BOM = b"\xef\xbb\xbf"


def project_csv(content: bytes) -> SourceProjectionDraft:
    """Project UTF-8 RFC-4180-compatible CSV bytes."""

    return project_delimited_text(
        content,
        source_format=CSV_FORMAT,
    )


def project_tsv(content: bytes) -> SourceProjectionDraft:
    """Project UTF-8 tab-separated bytes."""

    return project_delimited_text(
        content,
        source_format=TSV_FORMAT,
    )


def project_delimited_text(
    content: bytes,
    *,
    source_format: str,
) -> SourceProjectionDraft:
    """Project a fixed-delimiter tabular source."""

    if not isinstance(content, bytes):
        raise SourceAdapterError(
            "Table adapter content must be bytes."
        )

    if source_format not in SUPPORTED_TABLE_FORMATS:
        allowed_formats = ", ".join(
            sorted(SUPPORTED_TABLE_FORMATS)
        )
        raise UnsupportedSourceFormatError(
            "Unsupported table source_format: "
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
            "Table source must use UTF-8 or UTF-8 with BOM."
        ) from exc

    normalized_text = _normalize_line_endings(
        decoded_text
    )
    delimiter = _DELIMITER_BY_FORMAT[source_format]

    rows = _parse_rows(
        normalized_text,
        delimiter=delimiter,
    )

    adapter_id = (
        CSV_ADAPTER_ID
        if source_format == CSV_FORMAT
        else TSV_ADAPTER_ID
    )

    adapter_configuration = (
        ("encoding", "utf-8"),
        (
            "leading_utf8_bom",
            "removed" if has_utf8_bom else "absent",
        ),
        ("line_endings", "lf"),
        ("delimiter", delimiter),
        ("dialect_sniffing", False),
        ("header_inference", False),
        ("parser_strict", True),
        ("segmentation", "logical_cells"),
    )

    if not rows:
        return SourceProjectionDraft(
            adapter_id=adapter_id,
            adapter_version=TABLE_ADAPTER_VERSION,
            adapter_configuration=adapter_configuration,
            projection_result="unavailable",
            segments=(),
            issues=(
                ProjectionIssue(
                    code="NO_TABLE_ROWS",
                    message=(
                        "The source contains no logical table rows."
                    ),
                    issue_level="error",
                ),
            ),
        )

    segments = _create_table_segments(rows)

    return SourceProjectionDraft(
        adapter_id=adapter_id,
        adapter_version=TABLE_ADAPTER_VERSION,
        adapter_configuration=adapter_configuration,
        projection_result="complete",
        segments=segments,
    )


def _normalize_line_endings(text: str) -> str:
    """Normalize CRLF and CR line endings to LF."""

    return text.replace("\r\n", "\n").replace("\r", "\n")


def _parse_rows(
    text: str,
    *,
    delimiter: str,
) -> tuple[tuple[str, ...], ...]:
    """Parse logical rows using one fixed strict dialect."""

    stream = StringIO(
        text,
        newline="",
    )
    reader = csv.reader(
        stream,
        delimiter=delimiter,
        quotechar='"',
        doublequote=True,
        skipinitialspace=False,
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
        strict=True,
    )

    try:
        return tuple(
            tuple(cell for cell in row)
            for row in reader
        )
    except csv.Error as exc:
        raise SourceAdapterError(
            f"Tabular source is malformed: {exc}."
        ) from exc


def _create_table_segments(
    rows: tuple[tuple[str, ...], ...],
) -> tuple[ProjectionSegmentDraft, ...]:
    """Create source-located segments in row and column order."""

    segments: list[ProjectionSegmentDraft] = []

    for row_number, row in enumerate(
        rows,
        start=1,
    ):
        if not row:
            locator = SourceLocator(
                locator_type="table_row",
                coordinates=(
                    ("row", row_number),
                ),
            )
            segments.append(
                ProjectionSegmentDraft(
                    segment_type="table_empty_row",
                    text=f"row {row_number} = <empty>",
                    source_locators=(locator,),
                )
            )
            continue

        for column_number, cell in enumerate(
            row,
            start=1,
        ):
            locator = SourceLocator(
                locator_type="table_cell",
                coordinates=(
                    ("row", row_number),
                    ("column", column_number),
                ),
            )
            rendered_cell = json.dumps(
                cell,
                ensure_ascii=False,
            )
            segments.append(
                ProjectionSegmentDraft(
                    segment_type="table_cell",
                    text=(
                        f"row {row_number}, "
                        f"column {column_number} = "
                        f"{rendered_cell}"
                    ),
                    source_locators=(locator,),
                )
            )

    return tuple(segments)