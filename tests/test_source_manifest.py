"""Tests for Source IDs and the Source Manifest contract."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import json

import pytest

from modules.project_sources.errors import (
    SourceIdExhaustedError,
    SourceManifestError,
    UnsupportedSourceRoleError,
)
from modules.project_sources.identifiers import (
    format_source_id,
    next_source_id,
    source_id_sequence,
    validate_source_id,
)
from modules.project_sources.manifest import (
    CONTEXT_ONLY_SOURCE_ROLE,
    ENGINEERING_SOURCE_ROLE,
    SOURCE_MANIFEST_SCHEMA_VERSION,
    SOURCE_ROLES,
    create_source_manifest,
    parse_source_manifest,
    source_manifest_from_json,
    source_manifest_to_dict,
    source_manifest_to_json,
    source_storage_metadata,
    update_source_role_manifest,
    validate_source_manifest,
    validate_source_role,
)
from modules.project_sources.types import SourceManifest


REGISTERED_AT = "2026-07-22T10:30:00Z"
UPDATED_AT = "2026-07-22T11:30:00Z"


def valid_payload(**overrides):
    """Return one valid JSON-compatible Source Manifest payload."""

    payload = {
        "schema_version": SOURCE_MANIFEST_SCHEMA_VERSION,
        "project_id": "318604",
        "source_id": "SRC-000001",
        "source_role": ENGINEERING_SOURCE_ROLE,
        "original_filename": "System Requirements.pdf",
        "stored_filename": "content.pdf",
        "media_type": "application/pdf",
        "size_bytes": 42,
        "sha256": "a" * 64,
        "registered_at": REGISTERED_AT,
        "updated_at": REGISTERED_AT,
    }
    payload.update(overrides)
    return payload


def valid_manifest() -> SourceManifest:
    """Return one validated SourceManifest instance."""

    return create_source_manifest(
        "318604",
        "SRC-000001",
        ENGINEERING_SOURCE_ROLE,
        "System Requirements.pdf",
        size_bytes=42,
        sha256="a" * 64,
        timestamp=REGISTERED_AT,
    )


@pytest.mark.parametrize(
    "source_id",
    [
        "SRC-000001",
        "SRC-000042",
        "SRC-318604",
        "SRC-999999",
    ],
)
def test_validate_source_id_accepts_valid_identifiers(
    source_id,
):
    assert validate_source_id(source_id) == source_id


@pytest.mark.parametrize(
    "source_id",
    [
        None,
        1,
        True,
        "",
        "SRC-000000",
        "SRC-00001",
        "SRC-0000000",
        "SRC-1000000",
        "src-000001",
        "SOURCE-000001",
        "SRC_000001",
        "SRC-ABCDEF",
        " SRC-000001",
        "SRC-000001 ",
    ],
)
def test_validate_source_id_rejects_invalid_identifiers(
    source_id,
):
    with pytest.raises(SourceManifestError):
        validate_source_id(source_id)


def test_source_id_sequence_returns_numeric_value():
    assert source_id_sequence("SRC-004281") == 4281


@pytest.mark.parametrize(
    ("sequence", "expected"),
    [
        (1, "SRC-000001"),
        (42, "SRC-000042"),
        (318604, "SRC-318604"),
        (999999, "SRC-999999"),
    ],
)
def test_format_source_id_formats_valid_sequences(
    sequence,
    expected,
):
    assert format_source_id(sequence) == expected


@pytest.mark.parametrize(
    "sequence",
    [
        None,
        True,
        False,
        "1",
        1.0,
        0,
        -1,
        1000000,
    ],
)
def test_format_source_id_rejects_invalid_sequences(
    sequence,
):
    with pytest.raises(SourceManifestError):
        format_source_id(sequence)


def test_next_source_id_starts_at_one():
    assert next_source_id([]) == "SRC-000001"


def test_next_source_id_uses_highest_sequence_without_reusing_gaps():
    assert next_source_id(
        [
            "SRC-000001",
            "SRC-000004",
            "SRC-000002",
        ]
    ) == "SRC-000005"


def test_next_source_id_accepts_duplicate_occupied_values():
    assert next_source_id(
        [
            "SRC-000001",
            "SRC-000001",
        ]
    ) == "SRC-000002"


@pytest.mark.parametrize(
    "occupied",
    [
        "SRC-000001",
        b"SRC-000001",
    ],
)
def test_next_source_id_rejects_scalar_string_inputs(
    occupied,
):
    with pytest.raises(SourceManifestError):
        next_source_id(occupied)


def test_next_source_id_rejects_invalid_occupied_identifier():
    with pytest.raises(SourceManifestError):
        next_source_id(["invalid"])


def test_next_source_id_reports_exhaustion():
    with pytest.raises(SourceIdExhaustedError):
        next_source_id(["SRC-999999"])


@pytest.mark.parametrize(
    ("original_filename", "expected"),
    [
        (
            "requirements.txt",
            ("content.txt", "text/plain"),
        ),
        (
            "requirements.MD",
            ("content.md", "text/markdown"),
        ),
        (
            "requirements.JSON",
            ("content.json", "application/json"),
        ),
        (
            "requirements.csv",
            ("content.csv", "text/csv"),
        ),
        (
            "requirements.PDF",
            ("content.pdf", "application/pdf"),
        ),
        (
            "requirements.docx",
            (
                "content.docx",
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document",
            ),
        ),
        (
            "requirements.xlsx",
            (
                "content.xlsx",
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet",
            ),
        ),
    ],
)
def test_source_storage_metadata_maps_recognized_suffixes(
    original_filename,
    expected,
):
    assert source_storage_metadata(original_filename) == expected


@pytest.mark.parametrize(
    "original_filename",
    [
        "requirements",
        "requirements.custom",
        ".hidden",
        "archive.tar.gz",
    ],
)
def test_source_storage_metadata_maps_unknown_suffix_to_bin(
    original_filename,
):
    assert source_storage_metadata(original_filename) == (
        "content.bin",
        "application/octet-stream",
    )


@pytest.mark.parametrize(
    "source_role",
    sorted(SOURCE_ROLES),
)
def test_validate_source_role_accepts_permitted_roles(
    source_role,
):
    assert validate_source_role(source_role) == source_role


@pytest.mark.parametrize(
    "source_role",
    [
        None,
        1,
        "",
        "engineering",
        "context",
        "Engineering_Source",
        " engineering_source",
        "context_only ",
    ],
)
def test_validate_source_role_rejects_unsupported_roles(
    source_role,
):
    with pytest.raises(UnsupportedSourceRoleError):
        validate_source_role(source_role)


def test_create_source_manifest_creates_expected_manifest():
    manifest = valid_manifest()

    assert manifest.schema_version == "1.0.0"
    assert manifest.project_id == "318604"
    assert manifest.source_id == "SRC-000001"
    assert manifest.source_role == ENGINEERING_SOURCE_ROLE
    assert (
        manifest.original_filename
        == "System Requirements.pdf"
    )
    assert manifest.stored_filename == "content.pdf"
    assert manifest.media_type == "application/pdf"
    assert manifest.size_bytes == 42
    assert manifest.sha256 == "a" * 64
    assert manifest.registered_at == REGISTERED_AT
    assert manifest.updated_at == REGISTERED_AT


def test_source_manifest_is_immutable():
    manifest = valid_manifest()

    with pytest.raises(FrozenInstanceError):
        manifest.source_role = CONTEXT_ONLY_SOURCE_ROLE


def test_source_manifest_json_round_trip():
    manifest = valid_manifest()

    serialized = source_manifest_to_json(manifest)

    reloaded = source_manifest_from_json(
        serialized,
        expected_project_id="318604",
        expected_source_id="SRC-000001",
    )

    assert reloaded == manifest


def test_source_manifest_serialization_is_deterministic():
    manifest = create_source_manifest(
        "318604",
        "SRC-000001",
        ENGINEERING_SOURCE_ROLE,
        "Anforderungen_ä.pdf",
        size_bytes=42,
        sha256="a" * 64,
        timestamp=REGISTERED_AT,
    )

    first = source_manifest_to_json(manifest)
    second = source_manifest_to_json(manifest)

    assert first == second
    assert first.endswith("\n")
    assert "Anforderungen_ä.pdf" in first
    assert json.loads(first)["source_id"] == "SRC-000001"


def test_source_manifest_to_dict_returns_json_compatible_payload():
    manifest = valid_manifest()

    payload = source_manifest_to_dict(manifest)

    assert payload == valid_payload()
    assert payload is not source_manifest_to_dict(manifest)


def test_validate_source_manifest_accepts_valid_instance():
    assert validate_source_manifest(
        valid_manifest(),
        expected_project_id="318604",
        expected_source_id="SRC-000001",
    ) is None


@pytest.mark.parametrize(
    "invalid_manifest",
    [
        None,
        {},
        "manifest",
        42,
    ],
)
def test_manifest_serializers_reject_non_manifest_instances(
    invalid_manifest,
):
    with pytest.raises(SourceManifestError):
        source_manifest_to_dict(invalid_manifest)

    with pytest.raises(SourceManifestError):
        validate_source_manifest(invalid_manifest)


def test_parse_source_manifest_rejects_non_object():
    with pytest.raises(SourceManifestError):
        parse_source_manifest([])


@pytest.mark.parametrize(
    "missing_field",
    sorted(valid_payload()),
)
def test_parse_source_manifest_rejects_missing_fields(
    missing_field,
):
    payload = valid_payload()
    del payload[missing_field]

    with pytest.raises(SourceManifestError):
        parse_source_manifest(payload)


def test_parse_source_manifest_rejects_unknown_fields():
    payload = valid_payload(unexpected=True)

    with pytest.raises(SourceManifestError):
        parse_source_manifest(payload)


@pytest.mark.parametrize(
    "schema_version",
    [
        None,
        "",
        "0.9.0",
        "1.0",
        "2.0.0",
    ],
)
def test_parse_source_manifest_rejects_schema_versions(
    schema_version,
):
    with pytest.raises(SourceManifestError):
        parse_source_manifest(
            valid_payload(schema_version=schema_version)
        )


@pytest.mark.parametrize(
    "project_id",
    [
        None,
        318604,
        "",
        "12345",
        "1234567",
        "ABCDEF",
        " 318604",
        "318604 ",
    ],
)
def test_parse_source_manifest_rejects_invalid_project_ids(
    project_id,
):
    with pytest.raises(SourceManifestError):
        parse_source_manifest(
            valid_payload(project_id=project_id)
        )


def test_parse_source_manifest_rejects_project_directory_mismatch():
    with pytest.raises(SourceManifestError):
        parse_source_manifest(
            valid_payload(),
            expected_project_id="123456",
        )


def test_parse_source_manifest_rejects_invalid_expected_project_id():
    with pytest.raises(SourceManifestError):
        parse_source_manifest(
            valid_payload(),
            expected_project_id="invalid",
        )


@pytest.mark.parametrize(
    "source_id",
    [
        None,
        1,
        "",
        "SRC-000000",
        "SRC-00001",
        "SRC-1000000",
        "source-000001",
    ],
)
def test_parse_source_manifest_rejects_invalid_source_ids(
    source_id,
):
    with pytest.raises(SourceManifestError):
        parse_source_manifest(
            valid_payload(source_id=source_id)
        )


def test_parse_source_manifest_rejects_source_directory_mismatch():
    with pytest.raises(SourceManifestError):
        parse_source_manifest(
            valid_payload(),
            expected_source_id="SRC-000002",
        )


def test_parse_source_manifest_rejects_invalid_expected_source_id():
    with pytest.raises(SourceManifestError):
        parse_source_manifest(
            valid_payload(),
            expected_source_id="invalid",
        )


@pytest.mark.parametrize(
    "source_role",
    [
        None,
        "",
        "engineering",
        "context",
        "approved",
    ],
)
def test_parse_source_manifest_rejects_invalid_source_roles(
    source_role,
):
    with pytest.raises(UnsupportedSourceRoleError):
        parse_source_manifest(
            valid_payload(source_role=source_role)
        )


@pytest.mark.parametrize(
    "original_filename",
    [
        None,
        "",
        "   ",
        ".",
        "..",
        "../requirements.pdf",
        "folder/requirements.pdf",
        r"folder\requirements.pdf",
        "requirements\n.pdf",
        "requirements\x00.pdf",
    ],
)
def test_parse_source_manifest_rejects_invalid_original_filenames(
    original_filename,
):
    with pytest.raises(SourceManifestError):
        parse_source_manifest(
            valid_payload(
                original_filename=original_filename
            )
        )


@pytest.mark.parametrize(
    "stored_filename",
    [
        None,
        "",
        "content",
        "source.pdf",
        "content.PDF",
        "../content.pdf",
        "folder/content.pdf",
        "content.verylongsuffix",
    ],
)
def test_parse_source_manifest_rejects_invalid_stored_filenames(
    stored_filename,
):
    with pytest.raises(SourceManifestError):
        parse_source_manifest(
            valid_payload(stored_filename=stored_filename)
        )


def test_parse_source_manifest_rejects_stored_filename_mismatch():
    with pytest.raises(SourceManifestError):
        parse_source_manifest(
            valid_payload(stored_filename="content.txt")
        )


@pytest.mark.parametrize(
    "media_type",
    [
        None,
        "",
        " ",
        " application/pdf",
        "application/pdf ",
        42,
    ],
)
def test_parse_source_manifest_rejects_invalid_media_types(
    media_type,
):
    with pytest.raises(SourceManifestError):
        parse_source_manifest(
            valid_payload(media_type=media_type)
        )


def test_parse_source_manifest_rejects_media_type_mismatch():
    with pytest.raises(SourceManifestError):
        parse_source_manifest(
            valid_payload(media_type="text/plain")
        )


@pytest.mark.parametrize(
    "size_bytes",
    [
        None,
        True,
        False,
        "42",
        42.0,
        0,
        -1,
    ],
)
def test_parse_source_manifest_rejects_invalid_sizes(
    size_bytes,
):
    with pytest.raises(SourceManifestError):
        parse_source_manifest(
            valid_payload(size_bytes=size_bytes)
        )


@pytest.mark.parametrize(
    "sha256",
    [
        None,
        42,
        "",
        "a" * 63,
        "a" * 65,
        "A" * 64,
        "g" * 64,
    ],
)
def test_parse_source_manifest_rejects_invalid_sha256(
    sha256,
):
    with pytest.raises(SourceManifestError):
        parse_source_manifest(
            valid_payload(sha256=sha256)
        )


@pytest.mark.parametrize(
    ("field_name", "timestamp"),
    [
        ("registered_at", None),
        ("registered_at", ""),
        ("registered_at", "2026-07-22"),
        ("registered_at", "2026-07-22T10:30:00"),
        (
            "registered_at",
            "2026-07-22T10:30:00+00:00",
        ),
        ("registered_at", "2026-13-22T10:30:00Z"),
        ("updated_at", None),
        ("updated_at", ""),
        ("updated_at", "2026-07-22T11:30:00"),
        ("updated_at", "not-a-timestamp"),
    ],
)
def test_parse_source_manifest_rejects_invalid_timestamps(
    field_name,
    timestamp,
):
    payload = valid_payload()
    payload[field_name] = timestamp

    with pytest.raises(SourceManifestError):
        parse_source_manifest(payload)


def test_parse_source_manifest_accepts_fractional_utc_timestamp():
    manifest = parse_source_manifest(
        valid_payload(
            registered_at="2026-07-22T10:30:00.123456Z",
            updated_at="2026-07-22T10:30:00.123456Z",
        )
    )

    assert (
        manifest.registered_at
        == "2026-07-22T10:30:00.123456Z"
    )


def test_parse_source_manifest_rejects_updated_before_registered():
    with pytest.raises(SourceManifestError):
        parse_source_manifest(
            valid_payload(
                registered_at="2026-07-22T10:30:00Z",
                updated_at="2026-07-22T10:29:59Z",
            )
        )


def test_source_manifest_from_json_rejects_non_string_input():
    with pytest.raises(SourceManifestError):
        source_manifest_from_json(None)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "{",
        "[] trailing",
        '{"source_id": }',
    ],
)
def test_source_manifest_from_json_rejects_invalid_json(
    text,
):
    with pytest.raises(SourceManifestError):
        source_manifest_from_json(text)


def test_source_manifest_from_json_rejects_json_array():
    with pytest.raises(SourceManifestError):
        source_manifest_from_json("[]")


def test_update_source_role_manifest_preserves_immutable_values():
    manifest = valid_manifest()

    updated = update_source_role_manifest(
        manifest,
        CONTEXT_ONLY_SOURCE_ROLE,
        timestamp=UPDATED_AT,
    )

    assert updated.source_role == CONTEXT_ONLY_SOURCE_ROLE
    assert updated.updated_at == UPDATED_AT
    assert updated.schema_version == manifest.schema_version
    assert updated.project_id == manifest.project_id
    assert updated.source_id == manifest.source_id
    assert (
        updated.original_filename
        == manifest.original_filename
    )
    assert updated.stored_filename == manifest.stored_filename
    assert updated.media_type == manifest.media_type
    assert updated.size_bytes == manifest.size_bytes
    assert updated.sha256 == manifest.sha256
    assert updated.registered_at == manifest.registered_at


def test_update_source_role_manifest_rejects_unsupported_role():
    with pytest.raises(UnsupportedSourceRoleError):
        update_source_role_manifest(
            valid_manifest(),
            "unsupported",
            timestamp=UPDATED_AT,
        )


def test_update_source_role_manifest_rejects_earlier_timestamp():
    with pytest.raises(SourceManifestError):
        update_source_role_manifest(
            valid_manifest(),
            CONTEXT_ONLY_SOURCE_ROLE,
            timestamp="2026-07-22T10:29:59Z",
        )


def test_validation_detects_invalid_replaced_manifest():
    invalid = replace(
        valid_manifest(),
        size_bytes=0,
    )

    with pytest.raises(SourceManifestError):
        validate_source_manifest(invalid)