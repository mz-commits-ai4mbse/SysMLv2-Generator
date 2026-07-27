"""Safe internal document previews for P7 Evidence References."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

from modules.project_dashboard.errors import (
    DashboardDocumentError,
    DashboardIntegrityError,
)
from modules.project_dashboard.presenter import make_document_preview
from modules.project_dashboard.references import (
    resolve_evidence_path,
    validate_evidence_reference,
)
from modules.project_dashboard.types import (
    DashboardDocumentPreview,
    EvidenceLocation,
    EvidenceReference,
)


DEFAULT_MAX_PREVIEW_BYTES = 256 * 1024
DEFAULT_MAX_TABLE_ROWS = 200

_JSON_MEDIA_TYPES = frozenset(
    {
        "application/json",
        "application/ld+json",
    }
)
_MARKDOWN_MEDIA_TYPES = frozenset(
    {
        "text/markdown",
        "text/x-markdown",
    }
)
_TEXT_MEDIA_TYPES = frozenset(
    {
        "text/plain",
        "text/x-python",
        "text/yaml",
        "application/yaml",
        "application/xml",
        "text/xml",
    }
)
_CSV_MEDIA_TYPES = frozenset(
    {
        "text/csv",
        "application/csv",
        "text/tab-separated-values",
    }
)


class DashboardDocumentViewer:
    """Open safe repository artifacts as immutable viewer payloads."""

    def __init__(
        self,
        repository_root: Path | str = Path("."),
        *,
        max_preview_bytes: int = DEFAULT_MAX_PREVIEW_BYTES,
        max_table_rows: int = DEFAULT_MAX_TABLE_ROWS,
    ) -> None:
        self.repository_root = Path(repository_root)
        if (
            not isinstance(max_preview_bytes, int)
            or isinstance(max_preview_bytes, bool)
            or max_preview_bytes < 1024
        ):
            raise DashboardDocumentError(
                "max_preview_bytes must be an integer of at least 1024."
            )
        if (
            not isinstance(max_table_rows, int)
            or isinstance(max_table_rows, bool)
            or max_table_rows < 1
        ):
            raise DashboardDocumentError(
                "max_table_rows must be a positive integer."
            )
        self.max_preview_bytes = max_preview_bytes
        self.max_table_rows = max_table_rows

    def open(
        self,
        reference: EvidenceReference,
    ) -> DashboardDocumentPreview:
        """Open one exact Evidence Reference without leaving the dashboard."""

        validated = validate_evidence_reference(reference)
        path = resolve_evidence_path(
            validated,
            repository_root=self.repository_root,
            require_exists=True,
        )
        try:
            stat = path.stat()
        except OSError as exc:
            raise DashboardDocumentError(
                "Unable to inspect the referenced document."
            ) from exc
        if not path.is_file() or path.is_symlink():
            raise DashboardDocumentError(
                "Referenced document must be a regular file."
            )

        actual_sha256 = _hash_file(path)
        if (
            validated.content_fingerprint is not None
            and validated.content_fingerprint != actual_sha256
        ):
            raise DashboardIntegrityError(
                "Referenced document fingerprint does not match the "
                "Evidence Reference."
            )
        fingerprint_status = (
            "verified"
            if validated.content_fingerprint is not None
            else "not_provided"
        )

        media_type = validated.media_type
        if media_type in _JSON_MEDIA_TYPES:
            return self._open_json(
                validated,
                path,
                stat.st_size,
                actual_sha256,
                fingerprint_status,
            )
        if media_type in _MARKDOWN_MEDIA_TYPES:
            return self._open_text(
                validated,
                path,
                stat.st_size,
                actual_sha256,
                fingerprint_status,
                render_mode="markdown",
            )
        if media_type in _TEXT_MEDIA_TYPES or media_type.startswith("text/"):
            if media_type in _CSV_MEDIA_TYPES:
                return self._open_table(
                    validated,
                    path,
                    stat.st_size,
                    actual_sha256,
                    fingerprint_status,
                )
            return self._open_text(
                validated,
                path,
                stat.st_size,
                actual_sha256,
                fingerprint_status,
                render_mode="text",
            )
        if media_type in _CSV_MEDIA_TYPES:
            return self._open_table(
                validated,
                path,
                stat.st_size,
                actual_sha256,
                fingerprint_status,
            )

        return make_document_preview(
            project_id=validated.project_id,
            reference=validated,
            repository_relative_path=validated.repository_relative_path,
            title=validated.display_label,
            media_type=media_type,
            file_size_bytes=stat.st_size,
            actual_sha256=actual_sha256,
            fingerprint_status=fingerprint_status,
            render_mode="metadata",
            content_text=None,
            highlighted_text=None,
            truncated=False,
            issue=(
                "This media type is not rendered inline. "
                "Metadata and the verified repository path remain available."
            ),
        )

    def _open_json(
        self,
        reference: EvidenceReference,
        path: Path,
        size: int,
        actual_sha256: str,
        fingerprint_status: str,
    ) -> DashboardDocumentPreview:
        if size > self.max_preview_bytes:
            return make_document_preview(
                project_id=reference.project_id,
                reference=reference,
                repository_relative_path=reference.repository_relative_path,
                title=reference.display_label,
                media_type=reference.media_type,
                file_size_bytes=size,
                actual_sha256=actual_sha256,
                fingerprint_status=fingerprint_status,
                render_mode="metadata",
                content_text=None,
                highlighted_text=None,
                selected_json_pointer=(
                    None
                    if reference.location is None
                    else reference.location.json_pointer
                ),
                truncated=True,
                issue=(
                    "JSON document exceeds the bounded preview size. "
                    "Inline parsing is intentionally unavailable."
                ),
            )
        text = _read_utf8(path)
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise DashboardDocumentError(
                "Referenced JSON document is invalid."
            ) from exc
        formatted = json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        pointer = (
            None
            if reference.location is None
            else reference.location.json_pointer
        )
        highlighted = None
        if pointer is not None:
            selected = _resolve_json_pointer(value, pointer)
            highlighted = json.dumps(
                selected,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        return make_document_preview(
            project_id=reference.project_id,
            reference=reference,
            repository_relative_path=reference.repository_relative_path,
            title=reference.display_label,
            media_type=reference.media_type,
            file_size_bytes=size,
            actual_sha256=actual_sha256,
            fingerprint_status=fingerprint_status,
            render_mode="json",
            content_text=formatted,
            highlighted_text=highlighted,
            selected_json_pointer=pointer,
            truncated=False,
        )

    def _open_text(
        self,
        reference: EvidenceReference,
        path: Path,
        size: int,
        actual_sha256: str,
        fingerprint_status: str,
        *,
        render_mode: str,
    ) -> DashboardDocumentPreview:
        raw, truncated = _read_bounded(path, self.max_preview_bytes)
        text = _decode_bounded_utf8(raw, truncated=truncated)
        highlighted = _highlight_text(
            text,
            reference.location,
            markdown=render_mode == "markdown",
        )
        return make_document_preview(
            project_id=reference.project_id,
            reference=reference,
            repository_relative_path=reference.repository_relative_path,
            title=reference.display_label,
            media_type=reference.media_type,
            file_size_bytes=size,
            actual_sha256=actual_sha256,
            fingerprint_status=fingerprint_status,
            render_mode=render_mode,
            content_text=text,
            highlighted_text=highlighted,
            truncated=truncated,
            issue=(
                "Preview is bounded; the document continues beyond the "
                "displayed content."
                if truncated
                else None
            ),
        )

    def _open_table(
        self,
        reference: EvidenceReference,
        path: Path,
        size: int,
        actual_sha256: str,
        fingerprint_status: str,
    ) -> DashboardDocumentPreview:
        raw, byte_truncated = _read_bounded(
            path,
            self.max_preview_bytes,
        )
        text = _decode_bounded_utf8(raw, truncated=byte_truncated)
        delimiter = "\t" if (
            reference.media_type == "text/tab-separated-values"
            or path.suffix.lower() == ".tsv"
        ) else ","
        try:
            rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
        except csv.Error as exc:
            raise DashboardDocumentError(
                "Referenced table document cannot be parsed."
            ) from exc
        if not rows:
            columns = ("Column 1",)
            body: list[list[str]] = []
        else:
            width = max(1, max(len(row) for row in rows))
            header = list(rows[0])
            columns = tuple(
                (
                    header[index].strip()
                    if index < len(header) and header[index].strip()
                    else f"Column {index + 1}"
                )
                for index in range(width)
            )
            body = [
                list(row) + [""] * (width - len(row))
                for row in rows[1:]
            ]

        row_truncated = len(body) > self.max_table_rows
        selected_key = (
            None
            if reference.location is None
            else reference.location.table_row_key
        )
        selected_row: tuple[str, ...] | None = None
        if selected_key is not None:
            selected_row = next(
                (
                    tuple(row)
                    for row in body
                    if row and row[0] == selected_key
                ),
                None,
            )
            if selected_row is None:
                raise DashboardDocumentError(
                    "table_row_key was not found in the first table column."
                )

        displayed = tuple(
            tuple(row)
            for row in body[: self.max_table_rows]
        )
        highlighted = (
            None
            if selected_row is None
            else " | ".join(selected_row)
        )
        return make_document_preview(
            project_id=reference.project_id,
            reference=reference,
            repository_relative_path=reference.repository_relative_path,
            title=reference.display_label,
            media_type=reference.media_type,
            file_size_bytes=size,
            actual_sha256=actual_sha256,
            fingerprint_status=fingerprint_status,
            render_mode="table",
            content_text=None,
            highlighted_text=highlighted,
            table_columns=columns,
            table_rows=displayed,
            selected_table_row_key=selected_key,
            truncated=byte_truncated or row_truncated,
            issue=(
                "Table preview is bounded."
                if byte_truncated or row_truncated
                else None
            ),
        )


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise DashboardDocumentError(
            "Unable to hash the referenced document."
        ) from exc
    return digest.hexdigest()


def _read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise DashboardDocumentError(
            "Referenced document is not valid UTF-8."
        ) from exc
    except OSError as exc:
        raise DashboardDocumentError(
            "Unable to read the referenced document."
        ) from exc


def _read_bounded(path: Path, limit: int) -> tuple[bytes, bool]:
    try:
        with path.open("rb") as handle:
            raw = handle.read(limit + 1)
    except OSError as exc:
        raise DashboardDocumentError(
            "Unable to read the referenced document."
        ) from exc
    return raw[:limit], len(raw) > limit


def _decode_bounded_utf8(raw: bytes, *, truncated: bool) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        if truncated and exc.end == len(raw):
            return raw[: exc.start].decode("utf-8")
        raise DashboardDocumentError(
            "Referenced document is not valid UTF-8."
        ) from exc


def _highlight_text(
    text: str,
    location: EvidenceLocation | None,
    *,
    markdown: bool,
) -> str | None:
    if location is None:
        return None
    if location.line_start is not None:
        lines = text.splitlines()
        end = (
            location.line_end
            if location.line_end is not None
            else location.line_start
        )
        if location.line_start > len(lines):
            raise DashboardDocumentError(
                "Requested line range is outside the document preview."
            )
        return "\n".join(lines[location.line_start - 1 : end])
    if location.section_anchor is not None:
        if not markdown:
            raise DashboardDocumentError(
                "section_anchor navigation requires Markdown."
            )
        return _markdown_section(text, location.section_anchor)
    return None


def _markdown_section(text: str, anchor: str) -> str:
    lines = text.splitlines()
    normalized_anchor = _slug(anchor)
    start = None
    start_level = None
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped.startswith("#"):
            continue
        level = len(stripped) - len(stripped.lstrip("#"))
        title = stripped[level:].strip()
        if _slug(title) == normalized_anchor:
            start = index
            start_level = level
            break
    if start is None or start_level is None:
        raise DashboardDocumentError(
            "Markdown section anchor was not found."
        )
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].lstrip()
        if not stripped.startswith("#"):
            continue
        level = len(stripped) - len(stripped.lstrip("#"))
        if level <= start_level:
            end = index
            break
    return "\n".join(lines[start:end])


def _slug(value: str) -> str:
    lowered = value.strip().casefold()
    result = []
    previous_dash = False
    for character in lowered:
        if character.isalnum():
            result.append(character)
            previous_dash = False
        elif not previous_dash:
            result.append("-")
            previous_dash = True
    return "".join(result).strip("-")


def _resolve_json_pointer(value: Any, pointer: str) -> Any:
    if pointer == "":
        return value
    current = value
    for encoded in pointer.split("/")[1:]:
        token = encoded.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            if not token.isdigit():
                raise DashboardDocumentError(
                    "JSON pointer list token must be a non-negative index."
                )
            index = int(token)
            if index >= len(current):
                raise DashboardDocumentError(
                    "JSON pointer index is outside the document."
                )
            current = current[index]
        elif isinstance(current, dict):
            if token not in current:
                raise DashboardDocumentError(
                    "JSON pointer key was not found."
                )
            current = current[token]
        else:
            raise DashboardDocumentError(
                "JSON pointer traverses a scalar value."
            )
    return current
