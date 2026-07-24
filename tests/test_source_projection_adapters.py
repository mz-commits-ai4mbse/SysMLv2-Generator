"""Tests for deterministic Source Projection adapters."""

from __future__ import annotations

from io import BytesIO

import pytest
from pypdf import PdfReader, PdfWriter

from modules.source_projection.errors import (
    DuplicateJsonKeyError,
    SourceAdapterError,
    UnsupportedSourceFormatError,
    UnsupportedTextEncodingError,
)
from modules.source_projection.json_adapter import (
    project_json,
)
from modules.source_projection.pdf_adapter import (
    PINNED_PYPDF_VERSION,
    project_pdf,
)
from modules.source_projection.table_adapter import (
    project_csv,
    project_delimited_text,
    project_tsv,
)
from modules.source_projection.text_adapter import (
    project_markdown,
    project_plain_text,
    project_text_bytes,
)


def build_text_pdf(text: str) -> bytes:
    """Build a minimal one-page PDF with a text layer."""

    escaped_text = (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )
    content_stream = (
        "BT\n"
        "/F1 12 Tf\n"
        "72 720 Td\n"
        f"({escaped_text}) Tj\n"
        "ET\n"
    ).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        (
            b"<< /Type /Pages /Kids [3 0 R] "
            b"/Count 1 >>"
        ),
        (
            b"<< /Type /Page /Parent 2 0 R "
            b"/MediaBox [0 0 612 792] "
            b"/Resources << /Font << "
            b"/F1 4 0 R >> >> "
            b"/Contents 5 0 R >>"
        ),
        (
            b"<< /Type /Font /Subtype /Type1 "
            b"/BaseFont /Helvetica >>"
        ),
        (
            b"<< /Length "
            + str(len(content_stream)).encode("ascii")
            + b" >>\nstream\n"
            + content_stream
            + b"endstream"
        ),
    ]

    result = bytearray(
        b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    )
    offsets = [0]

    for object_number, object_content in enumerate(
        objects,
        start=1,
    ):
        offsets.append(len(result))
        result.extend(
            f"{object_number} 0 obj\n".encode("ascii")
        )
        result.extend(object_content)
        result.extend(b"\nendobj\n")

    xref_offset = len(result)
    result.extend(
        f"xref\n0 {len(objects) + 1}\n".encode(
            "ascii"
        )
    )
    result.extend(b"0000000000 65535 f \n")

    for offset in offsets[1:]:
        result.extend(
            f"{offset:010d} 00000 n \n".encode(
                "ascii"
            )
        )

    result.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} "
            "/Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )

    return bytes(result)


def build_blank_pdf(
    *,
    page_count: int = 1,
    encrypted: bool = False,
) -> bytes:
    """Build a valid PDF containing blank pages."""

    stream = BytesIO()
    writer = PdfWriter()

    for _ in range(page_count):
        writer.add_blank_page(
            width=72,
            height=72,
        )

    if encrypted:
        writer.encrypt("test-password")

    writer.write(stream)
    return stream.getvalue()


def build_mixed_pdf(text: str) -> bytes:
    """Build a PDF with one text page and one blank page."""

    source_reader = PdfReader(
        BytesIO(build_text_pdf(text))
    )
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_page(source_reader.pages[0])
    writer.add_blank_page(
        width=72,
        height=72,
    )
    writer.write(stream)

    return stream.getvalue()


@pytest.mark.parametrize(
    ("content", "expected_first", "expected_second"),
    [
        (
            b"First line.\nSecond line.\n\nThird.",
            "First line.\nSecond line.",
            "Third.",
        ),
        (
            b"First line.\r\nSecond line.\r\n\r\nThird.",
            "First line.\nSecond line.",
            "Third.",
        ),
        (
            b"First line.\rSecond line.\r\rThird.",
            "First line.\nSecond line.",
            "Third.",
        ),
    ],
)
def test_plain_text_normalizes_line_endings(
    content: bytes,
    expected_first: str,
    expected_second: str,
) -> None:
    projected = project_plain_text(content)

    assert projected.projection_result == "complete"
    assert tuple(
        segment.text
        for segment in projected.segments
    ) == (
        expected_first,
        expected_second,
    )


def test_plain_text_removes_only_leading_utf8_bom() -> None:
    projected = project_plain_text(
        b"\xef\xbb\xbfStatement."
    )

    assert projected.segments[0].text == "Statement."
    assert (
        "leading_utf8_bom",
        "removed",
    ) in projected.adapter_configuration


def test_plain_text_preserves_nonblank_line_content() -> None:
    projected = project_plain_text(
        b"  indented text  \nnext line"
    )

    assert projected.segments[0].text == (
        "  indented text  \nnext line"
    )


def test_plain_text_records_original_line_ranges() -> None:
    projected = project_plain_text(
        b"\nFirst.\nSecond.\n\n\nThird.\n"
    )

    assert projected.segments[
        0
    ].source_locators[0].coordinates == (
        ("line_start", 2),
        ("line_end", 3),
    )
    assert projected.segments[
        1
    ].source_locators[0].coordinates == (
        ("line_start", 6),
        ("line_end", 6),
    )


def test_plain_text_whitespace_only_is_unavailable() -> None:
    projected = project_plain_text(
        b" \n\t\n"
    )

    assert projected.projection_result == "unavailable"
    assert projected.segments == ()
    assert projected.issues[0].code == (
        "NO_TEXT_CONTENT"
    )


def test_markdown_uses_markdown_adapter_identity() -> None:
    projected = project_markdown(
        b"# System\n\nDescription."
    )

    assert projected.adapter_id == "markdown"
    assert tuple(
        segment.segment_type
        for segment in projected.segments
    ) == (
        "markdown_block",
        "markdown_block",
    )


@pytest.mark.parametrize(
    "projector",
    [
        project_plain_text,
        project_markdown,
    ],
)
def test_text_adapters_reject_invalid_utf8(
    projector,
) -> None:
    with pytest.raises(
        UnsupportedTextEncodingError
    ):
        projector(b"\xff\xfe")


def test_text_adapter_rejects_non_bytes() -> None:
    with pytest.raises(
        SourceAdapterError,
        match="must be bytes",
    ):
        project_plain_text(  # type: ignore[arg-type]
            "text"
        )


def test_text_adapter_rejects_unknown_format() -> None:
    with pytest.raises(
        UnsupportedSourceFormatError
    ):
        project_text_bytes(
            b"text",
            source_format="html",
        )


def test_json_projects_scalar_leaves_in_source_order() -> None:
    projected = project_json(
        (
            b'{'
            b'"name":"Turing",'
            b'"active":true,'
            b'"count":2,'
            b'"value":null'
            b'}'
        )
    )

    assert tuple(
        segment.text
        for segment in projected.segments
    ) == (
        '/name = "Turing"',
        "/active = true",
        "/count = 2",
        "/value = null",
    )


def test_json_projects_root_scalar() -> None:
    projected = project_json(b'"root value"')

    assert len(projected.segments) == 1
    assert projected.segments[0].text == (
        '<root> = "root value"'
    )
    assert projected.segments[
        0
    ].source_locators[0].coordinates == (
        ("pointer", ""),
    )


def test_json_projects_nested_arrays() -> None:
    projected = project_json(
        b'{"items":[{"id":"A"},{"id":"B"}]}'
    )

    assert tuple(
        segment.text
        for segment in projected.segments
    ) == (
        '/items/0/id = "A"',
        '/items/1/id = "B"',
    )


def test_json_escapes_pointer_tokens() -> None:
    projected = project_json(
        b'{"a/b":{"c~d":"value"}}'
    )

    assert projected.segments[0].text == (
        '/a~1b/c~0d = "value"'
    )
    assert projected.segments[
        0
    ].source_locators[0].coordinates == (
        ("pointer", "/a~1b/c~0d"),
    )


@pytest.mark.parametrize(
    ("content", "expected_type", "expected_text"),
    [
        (
            b"{}",
            "json_empty_object",
            "<root> = {}",
        ),
        (
            b"[]",
            "json_empty_array",
            "<root> = []",
        ),
        (
            b'{"empty":{}}',
            "json_empty_object",
            "/empty = {}",
        ),
        (
            b'{"empty":[]}',
            "json_empty_array",
            "/empty = []",
        ),
    ],
)
def test_json_preserves_empty_containers(
    content: bytes,
    expected_type: str,
    expected_text: str,
) -> None:
    projected = project_json(content)

    assert len(projected.segments) == 1
    assert projected.segments[0].segment_type == (
        expected_type
    )
    assert projected.segments[0].text == expected_text


def test_json_supports_utf8_bom_and_unicode() -> None:
    projected = project_json(
        b'\xef\xbb\xbf{"name":"T\xc3\xbcring"}'
    )

    assert projected.segments[0].text == (
        '/name = "Türing"'
    )


@pytest.mark.parametrize(
    "content",
    [
        b'{"name":"first","name":"second"}',
        b'{"outer":{"id":1,"id":2}}',
    ],
)
def test_json_rejects_duplicate_member_names(
    content: bytes,
) -> None:
    with pytest.raises(DuplicateJsonKeyError):
        project_json(content)


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"{",
        b'{"missing":}',
        b'{"value":NaN}',
        b'{"value":Infinity}',
        b'{"value":-Infinity}',
    ],
)
def test_json_rejects_invalid_or_nonstandard_json(
    content: bytes,
) -> None:
    with pytest.raises(SourceAdapterError):
        project_json(content)


def test_json_rejects_invalid_utf8() -> None:
    with pytest.raises(
        UnsupportedTextEncodingError
    ):
        project_json(b'{"name":"\xff"}')


def test_json_rejects_non_bytes() -> None:
    with pytest.raises(
        SourceAdapterError,
        match="must be bytes",
    ):
        project_json(  # type: ignore[arg-type]
            "{}"
        )


def test_csv_projects_cells_in_row_column_order() -> None:
    projected = project_csv(
        b"id,value\nA,First\nB,Second"
    )

    assert tuple(
        segment.text
        for segment in projected.segments
    ) == (
        'row 1, column 1 = "id"',
        'row 1, column 2 = "value"',
        'row 2, column 1 = "A"',
        'row 2, column 2 = "First"',
        'row 3, column 1 = "B"',
        'row 3, column 2 = "Second"',
    )


def test_csv_preserves_empty_cells() -> None:
    projected = project_csv(
        b"A,,C"
    )

    assert projected.segments[1].text == (
        'row 1, column 2 = ""'
    )


def test_csv_preserves_quoted_multiline_cell() -> None:
    projected = project_csv(
        b'id,text\r\nA,"First\r\nSecond"\r\n'
    )

    assert projected.segments[3].text == (
        'row 2, column 2 = "First\\nSecond"'
    )


def test_csv_does_not_sniff_semicolon_delimiter() -> None:
    projected = project_csv(
        b"left;right\nA;B"
    )

    assert len(projected.segments) == 2
    assert projected.segments[0].text == (
        'row 1, column 1 = "left;right"'
    )


def test_tsv_uses_fixed_tab_delimiter() -> None:
    projected = project_tsv(
        b"left\tright\nA\tB"
    )

    assert tuple(
        segment.text
        for segment in projected.segments
    ) == (
        'row 1, column 1 = "left"',
        'row 1, column 2 = "right"',
        'row 2, column 1 = "A"',
        'row 2, column 2 = "B"',
    )


def test_table_adapter_preserves_empty_row() -> None:
    projected = project_csv(b"\n")

    assert len(projected.segments) == 1
    assert projected.segments[0].segment_type == (
        "table_empty_row"
    )
    assert projected.segments[0].text == (
        "row 1 = <empty>"
    )


def test_empty_table_source_is_unavailable() -> None:
    projected = project_csv(b"")

    assert projected.projection_result == "unavailable"
    assert projected.segments == ()
    assert projected.issues[0].code == (
        "NO_TABLE_ROWS"
    )


@pytest.mark.parametrize(
    "projector",
    [
        project_csv,
        project_tsv,
    ],
)
def test_table_adapters_support_utf8_bom(
    projector,
) -> None:
    projected = projector(
        b"\xef\xbb\xbfA,B"
        if projector is project_csv
        else b"\xef\xbb\xbfA\tB"
    )

    assert projected.segments[0].text == (
        'row 1, column 1 = "A"'
    )


def test_table_adapter_rejects_malformed_quotes() -> None:
    with pytest.raises(SourceAdapterError):
        project_csv(b'"unterminated')


def test_table_adapter_rejects_invalid_utf8() -> None:
    with pytest.raises(
        UnsupportedTextEncodingError
    ):
        project_tsv(b"\xff\xfe")


def test_table_adapter_rejects_non_bytes() -> None:
    with pytest.raises(
        SourceAdapterError,
        match="must be bytes",
    ):
        project_csv(  # type: ignore[arg-type]
            "A,B"
        )


def test_table_adapter_rejects_unknown_format() -> None:
    with pytest.raises(
        UnsupportedSourceFormatError
    ):
        project_delimited_text(
            b"A|B",
            source_format="pipe",
        )


def test_pdf_adapter_uses_pinned_library_version() -> None:
    assert PINNED_PYPDF_VERSION == "6.14.2"


def test_pdf_projects_machine_readable_text() -> None:
    projected = project_pdf(
        build_text_pdf(
            "The system shall operate."
        )
    )

    assert projected.projection_result == "complete"
    assert len(projected.segments) == 1
    assert projected.segments[0].text == (
        "The system shall operate."
    )
    assert projected.segments[
        0
    ].source_locators[0].coordinates == (
        ("page", 1),
    )


def test_pdf_blank_page_is_unavailable() -> None:
    projected = project_pdf(
        build_blank_pdf()
    )

    assert projected.projection_result == "unavailable"
    assert projected.segments == ()
    assert projected.issues[0].code == (
        "PDF_PAGE_WITHOUT_EXTRACTABLE_TEXT"
    )
    assert projected.issues[
        0
    ].source_locators[0].coordinates == (
        ("page", 1),
    )


def test_pdf_mixed_text_and_blank_pages_is_partial() -> None:
    projected = project_pdf(
        build_mixed_pdf(
            "Extractable page."
        )
    )

    assert projected.projection_result == "partial"
    assert len(projected.segments) == 1
    assert projected.segments[0].text == (
        "Extractable page."
    )
    assert len(projected.issues) == 1
    assert projected.issues[0].code == (
        "PDF_PAGE_WITHOUT_EXTRACTABLE_TEXT"
    )
    assert projected.issues[
        0
    ].source_locators[0].coordinates == (
        ("page", 2),
    )


def test_pdf_reports_every_blank_page() -> None:
    projected = project_pdf(
        build_blank_pdf(page_count=2)
    )

    assert projected.projection_result == "unavailable"
    assert tuple(
        issue.source_locators[0].coordinates
        for issue in projected.issues
    ) == (
        (("page", 1),),
        (("page", 2),),
    )


def test_pdf_without_pages_is_unavailable() -> None:
    projected = project_pdf(
        build_blank_pdf(page_count=0)
    )

    assert projected.projection_result == "unavailable"
    assert projected.issues[0].code == (
        "PDF_HAS_NO_PAGES"
    )


def test_encrypted_pdf_is_unavailable() -> None:
    projected = project_pdf(
        build_blank_pdf(
            encrypted=True
        )
    )

    assert projected.projection_result == "unavailable"
    assert projected.segments == ()
    assert projected.issues[0].code == (
        "PDF_ENCRYPTED"
    )


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"not a PDF",
        b" PDF-1.4",
    ],
)
def test_pdf_rejects_missing_pdf_header(
    content: bytes,
) -> None:
    with pytest.raises(
        SourceAdapterError,
        match="%PDF-",
    ):
        project_pdf(content)


def test_pdf_rejects_non_bytes() -> None:
    with pytest.raises(
        SourceAdapterError,
        match="must be bytes",
    ):
        project_pdf(  # type: ignore[arg-type]
            "%PDF-1.4"
        )


def test_pdf_rejects_unreviewed_library_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "modules.source_projection.pdf_adapter."
        "pypdf.__version__",
        "99.0.0",
    )

    with pytest.raises(
        SourceAdapterError,
        match="requires pypdf 6.14.2",
    ):
        project_pdf(build_blank_pdf())