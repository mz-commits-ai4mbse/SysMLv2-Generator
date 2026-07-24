"""Tests for Source Projection identifiers and manifests."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json

import pytest

from modules.source_projection.errors import (
    SegmentIdExhaustedError,
    SourceProjectionIdExhaustedError,
    SourceProjectionIntegrityError,
    SourceProjectionManifestError,
)
from modules.source_projection.identifiers import (
    format_segment_id,
    format_source_projection_id,
    next_segment_id,
    next_source_projection_id,
    segment_id_sequence,
    source_projection_id_sequence,
    validate_segment_id,
    validate_source_projection_id,
)
from modules.source_projection.manifest import (
    SOURCE_PROJECTION_SCHEMA_VERSION,
    calculate_projection_fingerprint,
    create_source_projection_artifact,
    parse_source_projection_manifest,
    source_projection_artifact_from_json,
    source_projection_manifest_from_json,
    source_projection_manifest_to_dict,
    source_projection_manifest_to_json,
    validate_source_projection_artifact,
    validate_source_projection_manifest,
)
from modules.source_projection.text_adapter import (
    project_plain_text,
)
from modules.source_projection.types import (
    ProjectionIssue,
    ProjectionSegmentDraft,
    SourceLocator,
    SourceProjectionArtifact,
    SourceProjectionDraft,
)


PROJECT_ID = "318604"
SOURCE_ID = "SRC-000001"
SOURCE_PROJECTION_ID = "SP-000001"
TIMESTAMP = "2026-07-22T15:00:00Z"

SOURCE_CONTENT = (
    b"The system shall preserve traceability.\n\n"
    b"The system shall report failures."
)
SOURCE_SHA256 = hashlib.sha256(
    SOURCE_CONTENT
).hexdigest()


def create_test_artifact(
    *,
    draft: SourceProjectionDraft | None = None,
    project_id: str = PROJECT_ID,
    source_id: str = SOURCE_ID,
    source_projection_id: str = SOURCE_PROJECTION_ID,
    source_role: str = "engineering_source",
    source_sha256: str = SOURCE_SHA256,
    timestamp: str = TIMESTAMP,
) -> SourceProjectionArtifact:
    """Create one valid test artifact."""

    if draft is None:
        draft = project_plain_text(
            SOURCE_CONTENT
        )

    return create_source_projection_artifact(
        project_id=project_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        source_role=source_role,
        source_sha256=source_sha256,
        draft=draft,
        timestamp=timestamp,
    )


@pytest.mark.parametrize(
    "source_projection_id",
    [
        "SP-000001",
        "SP-000002",
        "SP-123456",
        "SP-999999",
    ],
)
def test_validate_source_projection_id_accepts_valid_ids(
    source_projection_id: str,
) -> None:
    assert validate_source_projection_id(
        source_projection_id
    ) == source_projection_id


@pytest.mark.parametrize(
    "source_projection_id",
    [
        "",
        "SP-1",
        "SP-000000",
        "SP-1000000",
        "sp-000001",
        "SP_000001",
        " SP-000001",
        "SP-000001 ",
        "../SP-000001",
        None,
        1,
        True,
    ],
)
def test_validate_source_projection_id_rejects_invalid_ids(
    source_projection_id: object,
) -> None:
    with pytest.raises(
        SourceProjectionManifestError
    ):
        validate_source_projection_id(
            source_projection_id
        )


@pytest.mark.parametrize(
    ("source_projection_id", "expected"),
    [
        ("SP-000001", 1),
        ("SP-004281", 4281),
        ("SP-999999", 999999),
    ],
)
def test_source_projection_id_sequence(
    source_projection_id: str,
    expected: int,
) -> None:
    assert source_projection_id_sequence(
        source_projection_id
    ) == expected


@pytest.mark.parametrize(
    ("sequence", "expected"),
    [
        (1, "SP-000001"),
        (4281, "SP-004281"),
        (999999, "SP-999999"),
    ],
)
def test_format_source_projection_id(
    sequence: int,
    expected: str,
) -> None:
    assert format_source_projection_id(
        sequence
    ) == expected


@pytest.mark.parametrize(
    "sequence",
    [
        0,
        -1,
        1000000,
        True,
        1.0,
        "1",
        None,
    ],
)
def test_format_source_projection_id_rejects_invalid_sequence(
    sequence: object,
) -> None:
    with pytest.raises(
        SourceProjectionManifestError
    ):
        format_source_projection_id(sequence)


def test_next_source_projection_id_starts_at_one() -> None:
    assert next_source_projection_id(
        []
    ) == "SP-000001"


def test_next_source_projection_id_does_not_reuse_gaps() -> None:
    assert next_source_projection_id(
        [
            "SP-000001",
            "SP-000004",
            "SP-000002",
        ]
    ) == "SP-000005"


def test_next_source_projection_id_rejects_string_iterable() -> None:
    with pytest.raises(
        SourceProjectionManifestError
    ):
        next_source_projection_id(
            "SP-000001"
        )


def test_next_source_projection_id_reports_exhaustion() -> None:
    with pytest.raises(
        SourceProjectionIdExhaustedError
    ):
        next_source_projection_id(
            ["SP-999999"]
        )


@pytest.mark.parametrize(
    "segment_id",
    [
        "SEG-000001",
        "SEG-000002",
        "SEG-123456",
        "SEG-999999",
    ],
)
def test_validate_segment_id_accepts_valid_ids(
    segment_id: str,
) -> None:
    assert validate_segment_id(
        segment_id
    ) == segment_id


@pytest.mark.parametrize(
    "segment_id",
    [
        "",
        "SEG-1",
        "SEG-000000",
        "SEG-1000000",
        "seg-000001",
        "SEG_000001",
        " SEG-000001",
        "SEG-000001 ",
        "../SEG-000001",
        None,
        1,
        True,
    ],
)
def test_validate_segment_id_rejects_invalid_ids(
    segment_id: object,
) -> None:
    with pytest.raises(
        SourceProjectionManifestError
    ):
        validate_segment_id(segment_id)


@pytest.mark.parametrize(
    ("segment_id", "expected"),
    [
        ("SEG-000001", 1),
        ("SEG-004281", 4281),
        ("SEG-999999", 999999),
    ],
)
def test_segment_id_sequence(
    segment_id: str,
    expected: int,
) -> None:
    assert segment_id_sequence(
        segment_id
    ) == expected


@pytest.mark.parametrize(
    ("sequence", "expected"),
    [
        (1, "SEG-000001"),
        (4281, "SEG-004281"),
        (999999, "SEG-999999"),
    ],
)
def test_format_segment_id(
    sequence: int,
    expected: str,
) -> None:
    assert format_segment_id(sequence) == expected


@pytest.mark.parametrize(
    "sequence",
    [
        0,
        -1,
        1000000,
        True,
        1.0,
        "1",
        None,
    ],
)
def test_format_segment_id_rejects_invalid_sequence(
    sequence: object,
) -> None:
    with pytest.raises(
        SourceProjectionManifestError
    ):
        format_segment_id(sequence)


def test_next_segment_id_starts_at_one() -> None:
    assert next_segment_id([]) == "SEG-000001"


def test_next_segment_id_does_not_reuse_gaps() -> None:
    assert next_segment_id(
        [
            "SEG-000001",
            "SEG-000004",
            "SEG-000002",
        ]
    ) == "SEG-000005"


def test_next_segment_id_rejects_string_iterable() -> None:
    with pytest.raises(
        SourceProjectionManifestError
    ):
        next_segment_id("SEG-000001")


def test_next_segment_id_reports_exhaustion() -> None:
    with pytest.raises(
        SegmentIdExhaustedError
    ):
        next_segment_id(["SEG-999999"])


def test_create_projection_artifact_assigns_identity() -> None:
    artifact = create_test_artifact()

    assert artifact.manifest.schema_version == (
        SOURCE_PROJECTION_SCHEMA_VERSION
    )
    assert artifact.manifest.project_id == PROJECT_ID
    assert artifact.manifest.source_id == SOURCE_ID
    assert artifact.manifest.source_projection_id == (
        SOURCE_PROJECTION_ID
    )
    assert artifact.manifest.source_role == (
        "engineering_source"
    )
    assert artifact.manifest.source_sha256 == (
        SOURCE_SHA256
    )
    assert artifact.manifest.created_at == TIMESTAMP


def test_create_projection_artifact_builds_content() -> None:
    artifact = create_test_artifact()

    assert artifact.content == (
        "The system shall preserve traceability.\n\n"
        "The system shall report failures."
    )
    assert artifact.manifest.content_length == len(
        artifact.content
    )
    assert artifact.manifest.content_sha256 == (
        hashlib.sha256(
            artifact.content.encode("utf-8")
        ).hexdigest()
    )


def test_create_projection_artifact_assigns_ordered_segments() -> None:
    artifact = create_test_artifact()
    first, second = artifact.manifest.segments

    assert first.segment_id == "SEG-000001"
    assert second.segment_id == "SEG-000002"

    assert first.start_offset == 0
    assert first.end_offset == len(
        "The system shall preserve traceability."
    )
    assert second.start_offset == (
        first.end_offset + 2
    )
    assert second.end_offset == len(
        artifact.content
    )

    assert artifact.content[
        first.start_offset:first.end_offset
    ] == "The system shall preserve traceability."

    assert artifact.content[
        second.start_offset:second.end_offset
    ] == "The system shall report failures."


def test_segment_hashes_match_segment_text() -> None:
    artifact = create_test_artifact()

    for segment in artifact.manifest.segments:
        segment_text = artifact.content[
            segment.start_offset:segment.end_offset
        ]
        expected_hash = hashlib.sha256(
            segment_text.encode("utf-8")
        ).hexdigest()

        assert segment.text_sha256 == expected_hash


def test_content_length_uses_character_offsets() -> None:
    content = "Fähigkeit.\n\nGröße."
    source_bytes = content.encode("utf-8")
    artifact = create_test_artifact(
        draft=project_plain_text(source_bytes),
        source_sha256=hashlib.sha256(
            source_bytes
        ).hexdigest(),
    )

    assert artifact.manifest.content_length == len(
        content
    )
    assert artifact.manifest.content_length != len(
        source_bytes
    )
    assert artifact.content == content


def test_adapter_configuration_is_canonicalized() -> None:
    artifact = create_test_artifact()
    keys = tuple(
        key
        for key, _ in (
            artifact.manifest.adapter_configuration
        )
    )

    assert keys == tuple(sorted(keys))


def test_projection_fingerprint_is_deterministic() -> None:
    first = calculate_projection_fingerprint(
        source_sha256=SOURCE_SHA256,
        adapter_id="plain_text",
        adapter_version="1.0.0",
        adapter_configuration=(
            ("encoding", "utf-8"),
            ("line_endings", "lf"),
        ),
    )
    second = calculate_projection_fingerprint(
        source_sha256=SOURCE_SHA256,
        adapter_id="plain_text",
        adapter_version="1.0.0",
        adapter_configuration=(
            ("line_endings", "lf"),
            ("encoding", "utf-8"),
        ),
    )

    assert first == second


@pytest.mark.parametrize(
    "changed_value",
    [
        "source",
        "adapter",
        "version",
        "configuration",
    ],
)
def test_projection_fingerprint_changes_with_input(
    changed_value: str,
) -> None:
    base = calculate_projection_fingerprint(
        source_sha256=SOURCE_SHA256,
        adapter_id="plain_text",
        adapter_version="1.0.0",
        adapter_configuration=(
            ("encoding", "utf-8"),
        ),
    )

    kwargs = {
        "source_sha256": SOURCE_SHA256,
        "adapter_id": "plain_text",
        "adapter_version": "1.0.0",
        "adapter_configuration": (
            ("encoding", "utf-8"),
        ),
    }

    if changed_value == "source":
        kwargs["source_sha256"] = "b" * 64
    elif changed_value == "adapter":
        kwargs["adapter_id"] = "markdown"
    elif changed_value == "version":
        kwargs["adapter_version"] = "1.0.1"
    else:
        kwargs["adapter_configuration"] = (
            ("encoding", "utf-8"),
            ("mode", "different"),
        )

    changed = calculate_projection_fingerprint(
        **kwargs
    )

    assert changed != base


def test_complete_projection_rejects_issues() -> None:
    original = project_plain_text(SOURCE_CONTENT)
    invalid = replace(
        original,
        issues=(
            ProjectionIssue(
                code="UNEXPECTED",
                message="Unexpected issue.",
                issue_level="warning",
            ),
        ),
    )

    with pytest.raises(
        SourceProjectionManifestError,
        match="complete projection must not contain issues",
    ):
        create_test_artifact(draft=invalid)


def test_partial_projection_requires_segments() -> None:
    draft = SourceProjectionDraft(
        adapter_id="test_adapter",
        adapter_version="1.0.0",
        adapter_configuration=(
            ("mode", "test"),
        ),
        projection_result="partial",
        segments=(),
        issues=(
            ProjectionIssue(
                code="PARTIAL",
                message="Partial result.",
                issue_level="warning",
            ),
        ),
    )

    with pytest.raises(
        SourceProjectionManifestError,
        match="partial projection requires at least one segment",
    ):
        create_test_artifact(draft=draft)


def test_partial_projection_requires_issue() -> None:
    original = project_plain_text(SOURCE_CONTENT)
    invalid = replace(
        original,
        projection_result="partial",
    )

    with pytest.raises(
        SourceProjectionManifestError,
        match="partial projection requires at least one issue",
    ):
        create_test_artifact(draft=invalid)


def test_valid_partial_projection_is_created() -> None:
    original = project_plain_text(SOURCE_CONTENT)
    partial = replace(
        original,
        projection_result="partial",
        issues=(
            ProjectionIssue(
                code="UNSUPPORTED_CONTENT",
                message="Unsupported content was omitted.",
                issue_level="warning",
            ),
        ),
    )

    artifact = create_test_artifact(
        draft=partial
    )

    assert artifact.manifest.projection_result == (
        "partial"
    )
    assert len(artifact.manifest.segments) == 2
    assert len(artifact.manifest.issues) == 1


def test_unavailable_projection_requires_no_segments() -> None:
    original = project_plain_text(SOURCE_CONTENT)
    invalid = replace(
        original,
        projection_result="unavailable",
        issues=(
            ProjectionIssue(
                code="UNAVAILABLE",
                message="Projection unavailable.",
                issue_level="error",
            ),
        ),
    )

    with pytest.raises(
        SourceProjectionManifestError,
        match="must not contain segments",
    ):
        create_test_artifact(draft=invalid)


def test_unavailable_projection_requires_issue() -> None:
    draft = SourceProjectionDraft(
        adapter_id="test_adapter",
        adapter_version="1.0.0",
        adapter_configuration=(
            ("mode", "test"),
        ),
        projection_result="unavailable",
        segments=(),
    )

    with pytest.raises(
        SourceProjectionManifestError,
        match="requires at least one issue",
    ):
        create_test_artifact(draft=draft)


def test_valid_unavailable_projection_has_empty_content() -> None:
    draft = SourceProjectionDraft(
        adapter_id="test_adapter",
        adapter_version="1.0.0",
        adapter_configuration=(
            ("mode", "test"),
        ),
        projection_result="unavailable",
        segments=(),
        issues=(
            ProjectionIssue(
                code="NO_CONTENT",
                message="No content available.",
                issue_level="error",
            ),
        ),
    )

    artifact = create_test_artifact(draft=draft)

    assert artifact.content == ""
    assert artifact.manifest.content_length == 0
    assert artifact.manifest.segments == ()


@pytest.mark.parametrize(
    "project_id",
    [
        "",
        "12345",
        "1234567",
        "ABCDEF",
        "../318604",
    ],
)
def test_create_rejects_invalid_project_id(
    project_id: str,
) -> None:
    with pytest.raises(
        SourceProjectionManifestError
    ):
        create_test_artifact(
            project_id=project_id
        )


@pytest.mark.parametrize(
    "source_id",
    [
        "",
        "SRC-000000",
        "SRC-1000000",
        "src-000001",
    ],
)
def test_create_rejects_invalid_source_id(
    source_id: str,
) -> None:
    with pytest.raises(
        SourceProjectionManifestError
    ):
        create_test_artifact(
            source_id=source_id
        )


@pytest.mark.parametrize(
    "source_role",
    [
        "",
        "reference",
        "ENGINEERING_SOURCE",
    ],
)
def test_create_rejects_invalid_source_role(
    source_role: str,
) -> None:
    with pytest.raises(
        SourceProjectionManifestError
    ):
        create_test_artifact(
            source_role=source_role
        )


def test_context_only_projection_is_valid() -> None:
    artifact = create_test_artifact(
        source_role="context_only"
    )

    assert artifact.manifest.source_role == (
        "context_only"
    )


@pytest.mark.parametrize(
    "source_sha256",
    [
        "",
        "a" * 63,
        "A" * 64,
        "g" * 64,
    ],
)
def test_create_rejects_invalid_source_sha256(
    source_sha256: str,
) -> None:
    with pytest.raises(
        SourceProjectionManifestError
    ):
        create_test_artifact(
            source_sha256=source_sha256
        )


@pytest.mark.parametrize(
    "timestamp",
    [
        "",
        "2026-07-22",
        "2026-07-22T15:00:00",
        "2026-13-22T15:00:00Z",
        "2026-07-22T25:00:00Z",
    ],
)
def test_create_rejects_invalid_timestamp(
    timestamp: str,
) -> None:
    with pytest.raises(
        SourceProjectionManifestError
    ):
        create_test_artifact(
            timestamp=timestamp
        )


def test_create_rejects_non_draft() -> None:
    with pytest.raises(
        SourceProjectionManifestError,
        match="SourceProjectionDraft",
    ):
        create_test_artifact(
            draft="draft",  # type: ignore[arg-type]
        )


def test_create_rejects_empty_adapter_configuration() -> None:
    original = project_plain_text(SOURCE_CONTENT)
    invalid = replace(
        original,
        adapter_configuration=(),
    )

    with pytest.raises(
        SourceProjectionManifestError
    ):
        create_test_artifact(draft=invalid)


def test_create_rejects_duplicate_configuration_keys() -> None:
    original = project_plain_text(SOURCE_CONTENT)
    invalid = replace(
        original,
        adapter_configuration=(
            ("encoding", "utf-8"),
            ("encoding", "utf-8"),
        ),
    )

    with pytest.raises(
        SourceProjectionManifestError,
        match="must be unique",
    ):
        create_test_artifact(draft=invalid)


@pytest.mark.parametrize(
    "configuration_value",
    [
        1.5,
        [],
        {},
        object(),
    ],
)
def test_create_rejects_invalid_configuration_value(
    configuration_value: object,
) -> None:
    original = project_plain_text(SOURCE_CONTENT)
    invalid = replace(
        original,
        adapter_configuration=(
            ("value", configuration_value),
        ),
    )

    with pytest.raises(
        SourceProjectionManifestError
    ):
        create_test_artifact(draft=invalid)


def test_create_rejects_empty_segment_text() -> None:
    locator = SourceLocator(
        locator_type="line_range",
        coordinates=(
            ("line_start", 1),
            ("line_end", 1),
        ),
    )
    draft = SourceProjectionDraft(
        adapter_id="test_adapter",
        adapter_version="1.0.0",
        adapter_configuration=(
            ("mode", "test"),
        ),
        projection_result="complete",
        segments=(
            ProjectionSegmentDraft(
                segment_type="text_block",
                text="   ",
                source_locators=(locator,),
            ),
        ),
    )

    with pytest.raises(
        SourceProjectionManifestError,
        match="non-whitespace",
    ):
        create_test_artifact(draft=draft)


def test_create_rejects_segment_without_locator() -> None:
    draft = SourceProjectionDraft(
        adapter_id="test_adapter",
        adapter_version="1.0.0",
        adapter_configuration=(
            ("mode", "test"),
        ),
        projection_result="complete",
        segments=(
            ProjectionSegmentDraft(
                segment_type="text_block",
                text="Statement.",
                source_locators=(),
            ),
        ),
    )

    with pytest.raises(
        SourceProjectionManifestError,
        match="requires at least one source locator",
    ):
        create_test_artifact(draft=draft)


def test_root_json_pointer_locator_allows_empty_value() -> None:
    locator = SourceLocator(
        locator_type="json_pointer",
        coordinates=(
            ("pointer", ""),
        ),
    )
    draft = SourceProjectionDraft(
        adapter_id="test_adapter",
        adapter_version="1.0.0",
        adapter_configuration=(
            ("mode", "test"),
        ),
        projection_result="complete",
        segments=(
            ProjectionSegmentDraft(
                segment_type="json_value",
                text="<root> = null",
                source_locators=(locator,),
            ),
        ),
    )

    artifact = create_test_artifact(draft=draft)

    assert artifact.manifest.segments[
        0
    ].source_locators[0] == locator


def test_create_rejects_duplicate_coordinate_names() -> None:
    locator = SourceLocator(
        locator_type="line_range",
        coordinates=(
            ("line_start", 1),
            ("line_start", 2),
        ),
    )
    draft = SourceProjectionDraft(
        adapter_id="test_adapter",
        adapter_version="1.0.0",
        adapter_configuration=(
            ("mode", "test"),
        ),
        projection_result="complete",
        segments=(
            ProjectionSegmentDraft(
                segment_type="text_block",
                text="Statement.",
                source_locators=(locator,),
            ),
        ),
    )

    with pytest.raises(
        SourceProjectionManifestError,
        match="must be unique",
    ):
        create_test_artifact(draft=draft)


@pytest.mark.parametrize(
    "coordinate_value",
    [
        0,
        -1,
        True,
        1.5,
        None,
    ],
)
def test_create_rejects_invalid_locator_coordinate(
    coordinate_value: object,
) -> None:
    locator = SourceLocator(
        locator_type="pdf_page",
        coordinates=(
            ("page", coordinate_value),  # type: ignore[arg-type]
        ),
    )
    draft = SourceProjectionDraft(
        adapter_id="test_adapter",
        adapter_version="1.0.0",
        adapter_configuration=(
            ("mode", "test"),
        ),
        projection_result="complete",
        segments=(
            ProjectionSegmentDraft(
                segment_type="pdf_page_text",
                text="Statement.",
                source_locators=(locator,),
            ),
        ),
    )

    with pytest.raises(
        SourceProjectionManifestError
    ):
        create_test_artifact(draft=draft)


@pytest.mark.parametrize(
    ("code", "message", "level"),
    [
        ("invalid-code", "Message.", "warning"),
        ("VALID_CODE", " Message.", "warning"),
        ("VALID_CODE", "", "warning"),
        ("VALID_CODE", "Message.", "info"),
    ],
)
def test_create_rejects_invalid_issue(
    code: str,
    message: str,
    level: str,
) -> None:
    original = project_plain_text(SOURCE_CONTENT)
    invalid = replace(
        original,
        projection_result="partial",
        issues=(
            ProjectionIssue(
                code=code,
                message=message,
                issue_level=level,
            ),
        ),
    )

    with pytest.raises(
        SourceProjectionManifestError
    ):
        create_test_artifact(draft=invalid)


def test_manifest_serialization_is_deterministic() -> None:
    artifact = create_test_artifact()

    first = source_projection_manifest_to_json(
        artifact.manifest
    )
    second = source_projection_manifest_to_json(
        artifact.manifest
    )

    assert first == second
    assert first.endswith("\n")


def test_manifest_round_trip_preserves_artifact() -> None:
    artifact = create_test_artifact()
    serialized = source_projection_manifest_to_json(
        artifact.manifest
    )

    reloaded = source_projection_artifact_from_json(
        serialized,
        artifact.content,
        expected_project_id=PROJECT_ID,
        expected_source_id=SOURCE_ID,
        expected_source_projection_id=(
            SOURCE_PROJECTION_ID
        ),
    )

    assert reloaded == artifact


def test_manifest_dict_round_trip() -> None:
    artifact = create_test_artifact()
    payload = source_projection_manifest_to_dict(
        artifact.manifest
    )

    parsed = parse_source_projection_manifest(
        payload,
        expected_project_id=PROJECT_ID,
        expected_source_id=SOURCE_ID,
        expected_source_projection_id=(
            SOURCE_PROJECTION_ID
        ),
    )

    assert parsed == artifact.manifest


@pytest.mark.parametrize(
    ("field_name", "expected_value"),
    [
        ("project_id", "999999"),
        ("source_id", "SRC-000002"),
        ("source_projection_id", "SP-000002"),
    ],
)
def test_manifest_rejects_expected_identity_mismatch(
    field_name: str,
    expected_value: str,
) -> None:
    artifact = create_test_artifact()
    kwargs = {
        "expected_project_id": PROJECT_ID,
        "expected_source_id": SOURCE_ID,
        "expected_source_projection_id": (
            SOURCE_PROJECTION_ID
        ),
    }
    kwargs[f"expected_{field_name}"] = expected_value

    with pytest.raises(
        SourceProjectionManifestError,
        match="does not match",
    ):
        source_projection_manifest_from_json(
            source_projection_manifest_to_json(
                artifact.manifest
            ),
            **kwargs,
        )


def test_manifest_rejects_missing_field() -> None:
    artifact = create_test_artifact()
    payload = source_projection_manifest_to_dict(
        artifact.manifest
    )
    del payload["adapter_id"]

    with pytest.raises(
        SourceProjectionManifestError,
        match="missing adapter_id",
    ):
        parse_source_projection_manifest(payload)


def test_manifest_rejects_unknown_field() -> None:
    artifact = create_test_artifact()
    payload = source_projection_manifest_to_dict(
        artifact.manifest
    )
    payload["unexpected"] = True

    with pytest.raises(
        SourceProjectionManifestError,
        match="unknown unexpected",
    ):
        parse_source_projection_manifest(payload)


def test_manifest_rejects_unknown_nested_segment_field() -> None:
    artifact = create_test_artifact()
    payload = source_projection_manifest_to_dict(
        artifact.manifest
    )
    payload["segments"][0]["unexpected"] = True

    with pytest.raises(
        SourceProjectionManifestError,
        match="unknown unexpected",
    ):
        parse_source_projection_manifest(payload)


def test_manifest_rejects_duplicate_json_key() -> None:
    artifact = create_test_artifact()
    serialized = source_projection_manifest_to_json(
        artifact.manifest
    )
    duplicated = serialized.replace(
        '"schema_version": "1.0.0",',
        (
            '"schema_version": "1.0.0",\n'
            '  "schema_version": "1.0.0",'
        ),
        1,
    )

    with pytest.raises(
        SourceProjectionManifestError,
        match="duplicate JSON member",
    ):
        source_projection_manifest_from_json(
            duplicated
        )


def test_manifest_rejects_invalid_json() -> None:
    with pytest.raises(
        SourceProjectionManifestError,
        match="invalid JSON",
    ):
        source_projection_manifest_from_json(
            "{invalid"
        )


def test_manifest_json_input_must_be_string() -> None:
    with pytest.raises(
        SourceProjectionManifestError,
        match="must be a string",
    ):
        source_projection_manifest_from_json(  # type: ignore[arg-type]
            {}
        )


def test_manifest_rejects_changed_fingerprint() -> None:
    artifact = create_test_artifact()
    payload = source_projection_manifest_to_dict(
        artifact.manifest
    )
    payload["projection_fingerprint"] = "a" * 64

    with pytest.raises(
        SourceProjectionManifestError,
        match="projection_fingerprint",
    ):
        parse_source_projection_manifest(payload)


def test_manifest_rejects_changed_configuration() -> None:
    artifact = create_test_artifact()
    payload = source_projection_manifest_to_dict(
        artifact.manifest
    )
    payload["adapter_configuration"]["encoding"] = (
        "different"
    )

    with pytest.raises(
        SourceProjectionManifestError,
        match="projection_fingerprint",
    ):
        parse_source_projection_manifest(payload)


def test_manifest_rejects_nonsequential_segment_ids() -> None:
    artifact = create_test_artifact()
    invalid_manifest = replace(
        artifact.manifest,
        segments=(
            replace(
                artifact.manifest.segments[0],
                segment_id="SEG-000002",
            ),
            artifact.manifest.segments[1],
        ),
    )

    with pytest.raises(
        SourceProjectionManifestError,
        match="sequential and ordered",
    ):
        validate_source_projection_manifest(
            invalid_manifest
        )


def test_manifest_rejects_invalid_segment_offsets() -> None:
    artifact = create_test_artifact()
    invalid_manifest = replace(
        artifact.manifest,
        segments=(
            artifact.manifest.segments[0],
            replace(
                artifact.manifest.segments[1],
                start_offset=(
                    artifact.manifest.segments[
                        1
                    ].start_offset
                    + 1
                ),
            ),
        ),
    )

    with pytest.raises(
        SourceProjectionManifestError,
        match="unexpected start_offset",
    ):
        validate_source_projection_manifest(
            invalid_manifest
        )


def test_artifact_rejects_modified_content() -> None:
    artifact = create_test_artifact()
    tampered = SourceProjectionArtifact(
        manifest=artifact.manifest,
        content=artifact.content + " altered",
    )

    with pytest.raises(
        SourceProjectionIntegrityError,
        match="length",
    ):
        validate_source_projection_artifact(
            tampered
        )


def test_artifact_rejects_same_length_content_change() -> None:
    artifact = create_test_artifact()
    tampered_content = (
        "X" + artifact.content[1:]
    )
    tampered = SourceProjectionArtifact(
        manifest=artifact.manifest,
        content=tampered_content,
    )

    with pytest.raises(
        SourceProjectionIntegrityError,
        match="SHA-256",
    ):
        validate_source_projection_artifact(
            tampered
        )


def test_artifact_rejects_modified_segment_hash() -> None:
    artifact = create_test_artifact()
    invalid_manifest = replace(
        artifact.manifest,
        segments=(
            replace(
                artifact.manifest.segments[0],
                text_sha256="a" * 64,
            ),
            artifact.manifest.segments[1],
        ),
    )
    tampered = SourceProjectionArtifact(
        manifest=invalid_manifest,
        content=artifact.content,
    )

    with pytest.raises(
        SourceProjectionIntegrityError
    ):
        validate_source_projection_artifact(
            tampered
        )


def test_validate_manifest_rejects_wrong_type() -> None:
    with pytest.raises(
        SourceProjectionManifestError
    ):
        validate_source_projection_manifest(  # type: ignore[arg-type]
            {}
        )


def test_validate_artifact_rejects_wrong_type() -> None:
    with pytest.raises(
        SourceProjectionIntegrityError
    ):
        validate_source_projection_artifact(  # type: ignore[arg-type]
            {}
        )


def test_manifest_value_objects_are_immutable() -> None:
    artifact = create_test_artifact()

    with pytest.raises(AttributeError):
        artifact.manifest.project_id = (  # type: ignore[misc]
            "999999"
        )

    with pytest.raises(AttributeError):
        artifact.manifest.segments[
            0
        ].segment_id = "SEG-000002"  # type: ignore[misc]