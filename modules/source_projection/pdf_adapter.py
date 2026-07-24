"""Deterministic text-layer-only PDF Source Projection adapter."""

from __future__ import annotations

from io import BytesIO

import pypdf
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from .errors import SourceAdapterError
from .types import (
    ProjectionIssue,
    ProjectionSegmentDraft,
    SourceLocator,
    SourceProjectionDraft,
)


PDF_ADAPTER_ID = "pdf_text_layer"
PDF_ADAPTER_VERSION = "1.0.0"
PINNED_PYPDF_VERSION = "6.14.2"


def project_pdf(content: bytes) -> SourceProjectionDraft:
    """Project machine-readable PDF text with page traceability."""

    if not isinstance(content, bytes):
        raise SourceAdapterError(
            "PDF adapter content must be bytes."
        )

    if not content.startswith(b"%PDF-"):
        raise SourceAdapterError(
            "PDF source must begin with a valid %PDF- header."
        )

    _require_pinned_pypdf_version()

    configuration = _adapter_configuration()

    try:
        reader = PdfReader(
            BytesIO(content),
            strict=False,
        )
    except (
        PyPdfError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        raise SourceAdapterError(
            f"PDF source could not be parsed: {exc}."
        ) from exc

    if reader.is_encrypted:
        return SourceProjectionDraft(
            adapter_id=PDF_ADAPTER_ID,
            adapter_version=PDF_ADAPTER_VERSION,
            adapter_configuration=configuration,
            projection_result="unavailable",
            segments=(),
            issues=(
                ProjectionIssue(
                    code="PDF_ENCRYPTED",
                    message=(
                        "Encrypted PDF content is not supported "
                        "by the text-layer adapter."
                    ),
                    issue_level="error",
                ),
            ),
        )

    try:
        pages = tuple(reader.pages)
    except (
        PyPdfError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise SourceAdapterError(
            f"PDF page structure could not be read: {exc}."
        ) from exc

    if not pages:
        return SourceProjectionDraft(
            adapter_id=PDF_ADAPTER_ID,
            adapter_version=PDF_ADAPTER_VERSION,
            adapter_configuration=configuration,
            projection_result="unavailable",
            segments=(),
            issues=(
                ProjectionIssue(
                    code="PDF_HAS_NO_PAGES",
                    message="The PDF contains no pages.",
                    issue_level="error",
                ),
            ),
        )

    segments: list[ProjectionSegmentDraft] = []
    issues: list[ProjectionIssue] = []

    for page_number, page in enumerate(
        pages,
        start=1,
    ):
        locator = _page_locator(page_number)

        try:
            extracted_text = page.extract_text(
                extraction_mode="plain",
            )
        except (
            PyPdfError,
            KeyError,
            TypeError,
            ValueError,
            OSError,
        ) as exc:
            issues.append(
                ProjectionIssue(
                    code="PDF_PAGE_TEXT_EXTRACTION_FAILED",
                    message=(
                        "Text extraction failed for PDF page "
                        f"{page_number}: {exc}."
                    ),
                    issue_level="error",
                    source_locators=(locator,),
                )
            )
            continue

        normalized_text = _normalize_page_text(
            extracted_text
        )

        if not normalized_text:
            issues.append(
                ProjectionIssue(
                    code="PDF_PAGE_WITHOUT_EXTRACTABLE_TEXT",
                    message=(
                        "PDF page "
                        f"{page_number} contains no extractable "
                        "machine-readable text."
                    ),
                    issue_level="warning",
                    source_locators=(locator,),
                )
            )
            continue

        segments.append(
            ProjectionSegmentDraft(
                segment_type="pdf_page_text",
                text=normalized_text,
                source_locators=(locator,),
            )
        )

    if not segments:
        projection_result = "unavailable"
    elif issues:
        projection_result = "partial"
    else:
        projection_result = "complete"

    return SourceProjectionDraft(
        adapter_id=PDF_ADAPTER_ID,
        adapter_version=PDF_ADAPTER_VERSION,
        adapter_configuration=configuration,
        projection_result=projection_result,
        segments=tuple(segments),
        issues=tuple(issues),
    )


def _require_pinned_pypdf_version() -> None:
    """Reject execution with an unreviewed pypdf version."""

    if pypdf.__version__ != PINNED_PYPDF_VERSION:
        raise SourceAdapterError(
            "PDF adapter requires pypdf "
            f"{PINNED_PYPDF_VERSION}, found "
            f"{pypdf.__version__}."
        )


def _adapter_configuration() -> tuple[
    tuple[str, str | int | bool | None],
    ...,
]:
    """Return the deterministic PDF adapter configuration."""

    return (
        ("library", "pypdf"),
        ("library_version", PINNED_PYPDF_VERSION),
        ("parser_strict", False),
        ("extraction_mode", "plain"),
        ("ocr", False),
        ("image_interpretation", False),
        ("page_boundaries", True),
        ("line_endings", "lf"),
        (
            "boundary_blank_lines",
            "removed",
        ),
    )


def _page_locator(page_number: int) -> SourceLocator:
    """Create one one-based PDF page locator."""

    return SourceLocator(
        locator_type="pdf_page",
        coordinates=(
            ("page", page_number),
        ),
    )


def _normalize_page_text(
    extracted_text: str | None,
) -> str:
    """Normalize line endings and remove boundary blank lines."""

    if extracted_text is None:
        return ""

    normalized = extracted_text.replace(
        "\r\n",
        "\n",
    ).replace(
        "\r",
        "\n",
    )

    lines = normalized.split("\n")

    while lines and not lines[0].strip():
        lines.pop(0)

    while lines and not lines[-1].strip():
        lines.pop()

    return "\n".join(lines)