"""Create, validate and serialize Source Projection Manifests."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
from typing import Any

from modules.project_sources.errors import ProjectSourceError
from modules.project_sources.identifiers import validate_source_id
from modules.project_sources.manifest import validate_source_role
from modules.project_workspace.identifiers import is_valid_project_id

from .errors import (
    SourceProjectionIntegrityError,
    SourceProjectionManifestError,
)
from .identifiers import (
    format_segment_id,
    validate_segment_id,
    validate_source_projection_id,
)
from .types import (
    AdapterConfiguration,
    AdapterConfigurationValue,
    ProjectionIssue,
    ProjectionSegment,
    ProjectionSegmentDraft,
    SourceLocator,
    SourceProjectionArtifact,
    SourceProjectionDraft,
    SourceProjectionManifest,
)


SOURCE_PROJECTION_SCHEMA_VERSION = "1.0.0"
SOURCE_PROJECTION_MANIFEST_FILENAME = "projection.json"
SOURCE_PROJECTION_CONTENT_FILENAME = "content.txt"

PROJECTION_RESULTS = frozenset(
    {
        "complete",
        "partial",
        "unavailable",
    }
)

ISSUE_LEVELS = frozenset(
    {
        "warning",
        "error",
    }
)

_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "source_id",
        "source_projection_id",
        "source_role",
        "source_sha256",
        "adapter_id",
        "adapter_version",
        "adapter_configuration",
        "projection_fingerprint",
        "projection_result",
        "content_sha256",
        "content_length",
        "segments",
        "issues",
        "created_at",
    }
)

_SEGMENT_FIELDS = frozenset(
    {
        "segment_id",
        "segment_type",
        "start_offset",
        "end_offset",
        "text_sha256",
        "source_locators",
    }
)

_ISSUE_FIELDS = frozenset(
    {
        "code",
        "message",
        "issue_level",
        "source_locators",
    }
)

_LOCATOR_FIELDS = frozenset(
    {
        "locator_type",
        "coordinates",
    }
)

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_LOWER_IDENTIFIER_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*$"
)
_ISSUE_CODE_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9_]*$"
)
_SEMANTIC_VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+$"
)
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)


def create_source_projection_artifact(
    *,
    project_id: str,
    source_id: str,
    source_projection_id: str,
    source_role: str,
    source_sha256: str,
    draft: SourceProjectionDraft,
    timestamp: str,
) -> SourceProjectionArtifact:
    """Create one validated immutable Source Projection artifact."""

    validated_project_id = _validate_project_id(
        project_id
    )
    validated_source_id = _validate_source_id(
        source_id
    )
    validated_projection_id = (
        validate_source_projection_id(
            source_projection_id
        )
    )
    validated_source_role = _validate_source_role(
        source_role
    )
    validated_source_sha256 = _validate_sha256(
        source_sha256,
        field_name="source_sha256",
    )
    validated_timestamp = _validate_timestamp(
        timestamp,
        field_name="timestamp",
    )

    if not isinstance(draft, SourceProjectionDraft):
        raise SourceProjectionManifestError(
            "draft must be a SourceProjectionDraft instance."
        )

    adapter_id = _validate_lower_identifier(
        draft.adapter_id,
        field_name="adapter_id",
    )
    adapter_version = _validate_semantic_version(
        draft.adapter_version,
        field_name="adapter_version",
    )
    adapter_configuration = (
        _validate_adapter_configuration(
            draft.adapter_configuration
        )
    )
    projection_result = _validate_projection_result(
        draft.projection_result
    )

    draft_segments = _validate_draft_segments(
        draft.segments
    )
    issues = _validate_issues(
        draft.issues
    )

    _validate_result_contract(
        projection_result=projection_result,
        segment_count=len(draft_segments),
        issues=issues,
    )

    content, segments = _build_content_and_segments(
        draft_segments
    )

    content_sha256 = _sha256_text(content)
    projection_fingerprint = (
        calculate_projection_fingerprint(
            source_sha256=validated_source_sha256,
            adapter_id=adapter_id,
            adapter_version=adapter_version,
            adapter_configuration=adapter_configuration,
        )
    )

    manifest = SourceProjectionManifest(
        schema_version=SOURCE_PROJECTION_SCHEMA_VERSION,
        project_id=validated_project_id,
        source_id=validated_source_id,
        source_projection_id=validated_projection_id,
        source_role=validated_source_role,
        source_sha256=validated_source_sha256,
        adapter_id=adapter_id,
        adapter_version=adapter_version,
        adapter_configuration=adapter_configuration,
        projection_fingerprint=projection_fingerprint,
        projection_result=projection_result,
        content_sha256=content_sha256,
        content_length=len(content),
        segments=segments,
        issues=issues,
        created_at=validated_timestamp,
    )

    artifact = SourceProjectionArtifact(
        manifest=manifest,
        content=content,
    )
    validate_source_projection_artifact(artifact)

    return artifact


def calculate_projection_fingerprint(
    *,
    source_sha256: str,
    adapter_id: str,
    adapter_version: str,
    adapter_configuration: AdapterConfiguration,
) -> str:
    """Calculate a deterministic adapter-application fingerprint."""

    validated_source_sha256 = _validate_sha256(
        source_sha256,
        field_name="source_sha256",
    )
    validated_adapter_id = _validate_lower_identifier(
        adapter_id,
        field_name="adapter_id",
    )
    validated_adapter_version = (
        _validate_semantic_version(
            adapter_version,
            field_name="adapter_version",
        )
    )
    validated_configuration = (
        _validate_adapter_configuration(
            adapter_configuration
        )
    )

    fingerprint_payload = {
        "source_sha256": validated_source_sha256,
        "adapter_id": validated_adapter_id,
        "adapter_version": validated_adapter_version,
        "adapter_configuration": dict(
            validated_configuration
        ),
    }

    serialized = json.dumps(
        fingerprint_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def parse_source_projection_manifest(
    payload: Any,
    *,
    expected_project_id: str | None = None,
    expected_source_id: str | None = None,
    expected_source_projection_id: str | None = None,
) -> SourceProjectionManifest:
    """Parse and validate one manifest-compatible value."""

    if not isinstance(payload, dict):
        raise SourceProjectionManifestError(
            "Source Projection Manifest must be a JSON object."
        )

    _require_exact_fields(
        payload,
        _MANIFEST_FIELDS,
        "Source Projection Manifest",
    )

    schema_version = payload["schema_version"]

    if schema_version != SOURCE_PROJECTION_SCHEMA_VERSION:
        raise SourceProjectionManifestError(
            "Unsupported Source Projection schema_version: "
            f"{schema_version!r}."
        )

    project_id = _validate_project_id(
        payload["project_id"]
    )
    source_id = _validate_source_id(
        payload["source_id"]
    )
    source_projection_id = (
        validate_source_projection_id(
            payload["source_projection_id"]
        )
    )

    _validate_expected_identity(
        actual=project_id,
        expected=expected_project_id,
        validator=_validate_project_id,
        field_name="project_id",
    )
    _validate_expected_identity(
        actual=source_id,
        expected=expected_source_id,
        validator=_validate_source_id,
        field_name="source_id",
    )
    _validate_expected_identity(
        actual=source_projection_id,
        expected=expected_source_projection_id,
        validator=validate_source_projection_id,
        field_name="source_projection_id",
    )

    source_role = _validate_source_role(
        payload["source_role"]
    )
    source_sha256 = _validate_sha256(
        payload["source_sha256"],
        field_name="source_sha256",
    )
    adapter_id = _validate_lower_identifier(
        payload["adapter_id"],
        field_name="adapter_id",
    )
    adapter_version = _validate_semantic_version(
        payload["adapter_version"],
        field_name="adapter_version",
    )
    adapter_configuration = (
        _parse_adapter_configuration(
            payload["adapter_configuration"]
        )
    )
    projection_fingerprint = _validate_sha256(
        payload["projection_fingerprint"],
        field_name="projection_fingerprint",
    )
    projection_result = _validate_projection_result(
        payload["projection_result"]
    )
    content_sha256 = _validate_sha256(
        payload["content_sha256"],
        field_name="content_sha256",
    )
    content_length = _validate_nonnegative_integer(
        payload["content_length"],
        field_name="content_length",
    )

    segments_payload = payload["segments"]

    if not isinstance(segments_payload, list):
        raise SourceProjectionManifestError(
            "segments must be a JSON array."
        )

    segments = tuple(
        _parse_segment(segment_payload)
        for segment_payload in segments_payload
    )

    issues_payload = payload["issues"]

    if not isinstance(issues_payload, list):
        raise SourceProjectionManifestError(
            "issues must be a JSON array."
        )

    issues = tuple(
        _parse_issue(issue_payload)
        for issue_payload in issues_payload
    )

    created_at = _validate_timestamp(
        payload["created_at"],
        field_name="created_at",
    )

    expected_fingerprint = (
        calculate_projection_fingerprint(
            source_sha256=source_sha256,
            adapter_id=adapter_id,
            adapter_version=adapter_version,
            adapter_configuration=adapter_configuration,
        )
    )

    if projection_fingerprint != expected_fingerprint:
        raise SourceProjectionManifestError(
            "projection_fingerprint does not match the "
            "source and adapter configuration."
        )

    manifest = SourceProjectionManifest(
        schema_version=schema_version,
        project_id=project_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        source_role=source_role,
        source_sha256=source_sha256,
        adapter_id=adapter_id,
        adapter_version=adapter_version,
        adapter_configuration=adapter_configuration,
        projection_fingerprint=projection_fingerprint,
        projection_result=projection_result,
        content_sha256=content_sha256,
        content_length=content_length,
        segments=segments,
        issues=issues,
        created_at=created_at,
    )

    validate_source_projection_manifest(manifest)

    return manifest


def source_projection_manifest_from_json(
    text: str,
    *,
    expected_project_id: str | None = None,
    expected_source_id: str | None = None,
    expected_source_projection_id: str | None = None,
) -> SourceProjectionManifest:
    """Parse and validate a Source Projection Manifest JSON string."""

    if not isinstance(text, str):
        raise SourceProjectionManifestError(
            "Source Projection Manifest JSON input "
            "must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except SourceProjectionManifestError:
        raise
    except json.JSONDecodeError as exc:
        raise SourceProjectionManifestError(
            "Source Projection Manifest contains invalid JSON: "
            f"{exc}."
        ) from exc

    return parse_source_projection_manifest(
        payload,
        expected_project_id=expected_project_id,
        expected_source_id=expected_source_id,
        expected_source_projection_id=(
            expected_source_projection_id
        ),
    )


def source_projection_artifact_from_json(
    manifest_text: str,
    content: str,
    *,
    expected_project_id: str | None = None,
    expected_source_id: str | None = None,
    expected_source_projection_id: str | None = None,
) -> SourceProjectionArtifact:
    """Load and validate one manifest and projected text pair."""

    manifest = source_projection_manifest_from_json(
        manifest_text,
        expected_project_id=expected_project_id,
        expected_source_id=expected_source_id,
        expected_source_projection_id=(
            expected_source_projection_id
        ),
    )

    artifact = SourceProjectionArtifact(
        manifest=manifest,
        content=content,
    )
    validate_source_projection_artifact(artifact)

    return artifact


def validate_source_projection_manifest(
    manifest: SourceProjectionManifest,
) -> None:
    """Validate an immutable Source Projection Manifest."""

    if not isinstance(manifest, SourceProjectionManifest):
        raise SourceProjectionManifestError(
            "manifest must be a SourceProjectionManifest instance."
        )

    _validate_project_id(manifest.project_id)
    _validate_source_id(manifest.source_id)
    validate_source_projection_id(
        manifest.source_projection_id
    )
    _validate_source_role(manifest.source_role)
    _validate_sha256(
        manifest.source_sha256,
        field_name="source_sha256",
    )
    _validate_lower_identifier(
        manifest.adapter_id,
        field_name="adapter_id",
    )
    _validate_semantic_version(
        manifest.adapter_version,
        field_name="adapter_version",
    )

    configuration = _validate_adapter_configuration(
        manifest.adapter_configuration
    )

    if configuration != manifest.adapter_configuration:
        raise SourceProjectionManifestError(
            "adapter_configuration must use canonical key order."
        )

    _validate_sha256(
        manifest.projection_fingerprint,
        field_name="projection_fingerprint",
    )
    projection_result = _validate_projection_result(
        manifest.projection_result
    )
    _validate_sha256(
        manifest.content_sha256,
        field_name="content_sha256",
    )
    content_length = _validate_nonnegative_integer(
        manifest.content_length,
        field_name="content_length",
    )
    _validate_timestamp(
        manifest.created_at,
        field_name="created_at",
    )

    expected_fingerprint = (
        calculate_projection_fingerprint(
            source_sha256=manifest.source_sha256,
            adapter_id=manifest.adapter_id,
            adapter_version=manifest.adapter_version,
            adapter_configuration=configuration,
        )
    )

    if manifest.projection_fingerprint != expected_fingerprint:
        raise SourceProjectionManifestError(
            "projection_fingerprint does not match the "
            "source and adapter configuration."
        )

    _validate_persisted_segments(
        manifest.segments,
        content_length=content_length,
    )
    issues = _validate_issues(manifest.issues)

    _validate_result_contract(
        projection_result=projection_result,
        segment_count=len(manifest.segments),
        issues=issues,
    )

    if projection_result == "unavailable":
        if content_length != 0:
            raise SourceProjectionManifestError(
                "An unavailable projection must have "
                "content_length 0."
            )
    elif content_length == 0:
        raise SourceProjectionManifestError(
            "A complete or partial projection must contain text."
        )


def validate_source_projection_artifact(
    artifact: SourceProjectionArtifact,
) -> None:
    """Validate manifest integrity against projected text."""

    if not isinstance(artifact, SourceProjectionArtifact):
        raise SourceProjectionIntegrityError(
            "artifact must be a SourceProjectionArtifact instance."
        )

    if not isinstance(artifact.content, str):
        raise SourceProjectionIntegrityError(
            "Projected content must be a string."
        )

    try:
        validate_source_projection_manifest(
            artifact.manifest
        )
    except SourceProjectionManifestError as exc:
        raise SourceProjectionIntegrityError(
            f"Source Projection Manifest is invalid: {exc}"
        ) from exc

    manifest = artifact.manifest
    content = artifact.content

    if len(content) != manifest.content_length:
        raise SourceProjectionIntegrityError(
            "Projected content length does not match "
            "the manifest."
        )

    actual_content_sha256 = _sha256_text(content)

    if actual_content_sha256 != manifest.content_sha256:
        raise SourceProjectionIntegrityError(
            "Projected content SHA-256 does not match "
            "the manifest."
        )

    for segment in manifest.segments:
        segment_text = content[
            segment.start_offset:segment.end_offset
        ]
        actual_segment_sha256 = _sha256_text(
            segment_text
        )

        if actual_segment_sha256 != segment.text_sha256:
            raise SourceProjectionIntegrityError(
                "Projected segment content does not match "
                f"{segment.segment_id}."
            )


def source_projection_manifest_to_dict(
    manifest: SourceProjectionManifest,
) -> dict[str, Any]:
    """Return a validated JSON-compatible manifest dictionary."""

    validate_source_projection_manifest(manifest)

    return {
        "schema_version": manifest.schema_version,
        "project_id": manifest.project_id,
        "source_id": manifest.source_id,
        "source_projection_id": (
            manifest.source_projection_id
        ),
        "source_role": manifest.source_role,
        "source_sha256": manifest.source_sha256,
        "adapter_id": manifest.adapter_id,
        "adapter_version": manifest.adapter_version,
        "adapter_configuration": dict(
            manifest.adapter_configuration
        ),
        "projection_fingerprint": (
            manifest.projection_fingerprint
        ),
        "projection_result": manifest.projection_result,
        "content_sha256": manifest.content_sha256,
        "content_length": manifest.content_length,
        "segments": [
            _segment_to_dict(segment)
            for segment in manifest.segments
        ],
        "issues": [
            _issue_to_dict(issue)
            for issue in manifest.issues
        ],
        "created_at": manifest.created_at,
    }


def source_projection_manifest_to_json(
    manifest: SourceProjectionManifest,
) -> str:
    """Serialize a validated manifest deterministically."""

    return json.dumps(
        source_projection_manifest_to_dict(manifest),
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def _build_content_and_segments(
    draft_segments: tuple[ProjectionSegmentDraft, ...],
) -> tuple[str, tuple[ProjectionSegment, ...]]:
    """Build canonical content and persisted segment metadata."""

    content_parts: list[str] = []
    segments: list[ProjectionSegment] = []
    current_offset = 0

    for sequence, draft_segment in enumerate(
        draft_segments,
        start=1,
    ):
        if content_parts:
            separator = "\n\n"
            content_parts.append(separator)
            current_offset += len(separator)

        start_offset = current_offset
        content_parts.append(draft_segment.text)
        current_offset += len(draft_segment.text)
        end_offset = current_offset

        segments.append(
            ProjectionSegment(
                segment_id=format_segment_id(sequence),
                segment_type=draft_segment.segment_type,
                start_offset=start_offset,
                end_offset=end_offset,
                text_sha256=_sha256_text(
                    draft_segment.text
                ),
                source_locators=(
                    draft_segment.source_locators
                ),
            )
        )

    return "".join(content_parts), tuple(segments)


def _validate_draft_segments(
    segments: Any,
) -> tuple[ProjectionSegmentDraft, ...]:
    if not isinstance(segments, tuple):
        raise SourceProjectionManifestError(
            "draft segments must be a tuple."
        )

    validated: list[ProjectionSegmentDraft] = []

    for segment in segments:
        if not isinstance(segment, ProjectionSegmentDraft):
            raise SourceProjectionManifestError(
                "Every draft segment must be a "
                "ProjectionSegmentDraft instance."
            )

        segment_type = _validate_lower_identifier(
            segment.segment_type,
            field_name="segment_type",
        )

        if not isinstance(segment.text, str):
            raise SourceProjectionManifestError(
                "Segment text must be a string."
            )

        if not segment.text.strip():
            raise SourceProjectionManifestError(
                "Segment text must contain non-whitespace text."
            )

        locators = _validate_locators(
            segment.source_locators
        )

        if not locators:
            raise SourceProjectionManifestError(
                "Every segment requires at least one "
                "source locator."
            )

        validated.append(
            ProjectionSegmentDraft(
                segment_type=segment_type,
                text=segment.text,
                source_locators=locators,
            )
        )

    return tuple(validated)


def _validate_persisted_segments(
    segments: Any,
    *,
    content_length: int,
) -> None:
    if not isinstance(segments, tuple):
        raise SourceProjectionManifestError(
            "segments must be a tuple."
        )

    expected_start_offset = 0

    for sequence, segment in enumerate(
        segments,
        start=1,
    ):
        if not isinstance(segment, ProjectionSegment):
            raise SourceProjectionManifestError(
                "Every segment must be a ProjectionSegment."
            )

        expected_segment_id = format_segment_id(
            sequence
        )
        validated_segment_id = validate_segment_id(
            segment.segment_id
        )

        if validated_segment_id != expected_segment_id:
            raise SourceProjectionManifestError(
                "Segment IDs must be sequential and ordered: "
                f"expected {expected_segment_id}, found "
                f"{validated_segment_id}."
            )

        _validate_lower_identifier(
            segment.segment_type,
            field_name="segment_type",
        )

        start_offset = _validate_nonnegative_integer(
            segment.start_offset,
            field_name="start_offset",
        )
        end_offset = _validate_nonnegative_integer(
            segment.end_offset,
            field_name="end_offset",
        )

        if start_offset != expected_start_offset:
            raise SourceProjectionManifestError(
                f"{segment.segment_id} has an unexpected "
                "start_offset."
            )

        if end_offset <= start_offset:
            raise SourceProjectionManifestError(
                f"{segment.segment_id} must have a positive "
                "text range."
            )

        if end_offset > content_length:
            raise SourceProjectionManifestError(
                f"{segment.segment_id} exceeds content_length."
            )

        _validate_sha256(
            segment.text_sha256,
            field_name="text_sha256",
        )

        locators = _validate_locators(
            segment.source_locators
        )

        if not locators:
            raise SourceProjectionManifestError(
                f"{segment.segment_id} requires at least one "
                "source locator."
            )

        expected_start_offset = end_offset + 2

    if segments:
        if segments[-1].end_offset != content_length:
            raise SourceProjectionManifestError(
                "The final segment must end at content_length."
            )
    elif content_length != 0:
        raise SourceProjectionManifestError(
            "Content without segments is not permitted."
        )


def _validate_issues(
    issues: Any,
) -> tuple[ProjectionIssue, ...]:
    if not isinstance(issues, tuple):
        raise SourceProjectionManifestError(
            "issues must be a tuple."
        )

    validated: list[ProjectionIssue] = []

    for issue in issues:
        if not isinstance(issue, ProjectionIssue):
            raise SourceProjectionManifestError(
                "Every issue must be a ProjectionIssue."
            )

        code = issue.code

        if (
            not isinstance(code, str)
            or _ISSUE_CODE_PATTERN.fullmatch(code) is None
        ):
            raise SourceProjectionManifestError(
                "Issue code must match ^[A-Z][A-Z0-9_]*$."
            )

        message = _validate_trimmed_string(
            issue.message,
            field_name="issue message",
        )

        if issue.issue_level not in ISSUE_LEVELS:
            allowed_levels = ", ".join(
                sorted(ISSUE_LEVELS)
            )
            raise SourceProjectionManifestError(
                "Unsupported issue_level: "
                f"{issue.issue_level!r}. Expected one of: "
                f"{allowed_levels}."
            )

        locators = _validate_locators(
            issue.source_locators
        )

        validated.append(
            ProjectionIssue(
                code=code,
                message=message,
                issue_level=issue.issue_level,
                source_locators=locators,
            )
        )

    return tuple(validated)


def _validate_locators(
    locators: Any,
) -> tuple[SourceLocator, ...]:
    if not isinstance(locators, tuple):
        raise SourceProjectionManifestError(
            "source_locators must be a tuple."
        )

    validated: list[SourceLocator] = []

    for locator in locators:
        if not isinstance(locator, SourceLocator):
            raise SourceProjectionManifestError(
                "Every source locator must be a "
                "SourceLocator instance."
            )

        locator_type = _validate_lower_identifier(
            locator.locator_type,
            field_name="locator_type",
        )

        if not isinstance(locator.coordinates, tuple):
            raise SourceProjectionManifestError(
                "Locator coordinates must be a tuple."
            )

        if not locator.coordinates:
            raise SourceProjectionManifestError(
                "A source locator requires coordinates."
            )

        coordinate_names: set[str] = set()
        coordinates: list[
            tuple[str, str | int]
        ] = []

        for coordinate in locator.coordinates:
            if (
                not isinstance(coordinate, tuple)
                or len(coordinate) != 2
            ):
                raise SourceProjectionManifestError(
                    "Every locator coordinate must be a "
                    "name-value pair."
                )

            name, value = coordinate
            validated_name = _validate_lower_identifier(
                name,
                field_name="coordinate name",
            )

            if validated_name in coordinate_names:
                raise SourceProjectionManifestError(
                    "Locator coordinate names must be unique."
                )

            coordinate_names.add(validated_name)

            if isinstance(value, bool) or not isinstance(
                value,
                (str, int),
            ):
                raise SourceProjectionManifestError(
                    "Locator coordinate values must be "
                    "strings or integers."
                )

            if isinstance(value, int) and value < 1:
                raise SourceProjectionManifestError(
                    "Integer locator coordinates must be "
                    "greater than zero."
                )

            coordinates.append(
                (validated_name, value)
            )

        validated.append(
            SourceLocator(
                locator_type=locator_type,
                coordinates=tuple(coordinates),
            )
        )

    return tuple(validated)


def _validate_result_contract(
    *,
    projection_result: str,
    segment_count: int,
    issues: tuple[ProjectionIssue, ...],
) -> None:
    if projection_result == "complete":
        if segment_count < 1:
            raise SourceProjectionManifestError(
                "A complete projection requires at least "
                "one segment."
            )

        if issues:
            raise SourceProjectionManifestError(
                "A complete projection must not contain issues."
            )

    elif projection_result == "partial":
        if segment_count < 1:
            raise SourceProjectionManifestError(
                "A partial projection requires at least "
                "one segment."
            )

        if not issues:
            raise SourceProjectionManifestError(
                "A partial projection requires at least "
                "one issue."
            )

    elif projection_result == "unavailable":
        if segment_count != 0:
            raise SourceProjectionManifestError(
                "An unavailable projection must not "
                "contain segments."
            )

        if not issues:
            raise SourceProjectionManifestError(
                "An unavailable projection requires at "
                "least one issue."
            )


def _parse_segment(payload: Any) -> ProjectionSegment:
    if not isinstance(payload, dict):
        raise SourceProjectionManifestError(
            "Every segment must be a JSON object."
        )

    _require_exact_fields(
        payload,
        _SEGMENT_FIELDS,
        "Projection Segment",
    )

    locators_payload = payload["source_locators"]

    if not isinstance(locators_payload, list):
        raise SourceProjectionManifestError(
            "Segment source_locators must be a JSON array."
        )

    return ProjectionSegment(
        segment_id=payload["segment_id"],
        segment_type=payload["segment_type"],
        start_offset=payload["start_offset"],
        end_offset=payload["end_offset"],
        text_sha256=payload["text_sha256"],
        source_locators=tuple(
            _parse_locator(locator_payload)
            for locator_payload in locators_payload
        ),
    )


def _parse_issue(payload: Any) -> ProjectionIssue:
    if not isinstance(payload, dict):
        raise SourceProjectionManifestError(
            "Every issue must be a JSON object."
        )

    _require_exact_fields(
        payload,
        _ISSUE_FIELDS,
        "Projection Issue",
    )

    locators_payload = payload["source_locators"]

    if not isinstance(locators_payload, list):
        raise SourceProjectionManifestError(
            "Issue source_locators must be a JSON array."
        )

    return ProjectionIssue(
        code=payload["code"],
        message=payload["message"],
        issue_level=payload["issue_level"],
        source_locators=tuple(
            _parse_locator(locator_payload)
            for locator_payload in locators_payload
        ),
    )


def _parse_locator(payload: Any) -> SourceLocator:
    if not isinstance(payload, dict):
        raise SourceProjectionManifestError(
            "Every source locator must be a JSON object."
        )

    _require_exact_fields(
        payload,
        _LOCATOR_FIELDS,
        "Source Locator",
    )

    coordinates = payload["coordinates"]

    if not isinstance(coordinates, dict):
        raise SourceProjectionManifestError(
            "Locator coordinates must be a JSON object."
        )

    return SourceLocator(
        locator_type=payload["locator_type"],
        coordinates=tuple(coordinates.items()),
    )


def _segment_to_dict(
    segment: ProjectionSegment,
) -> dict[str, Any]:
    return {
        "segment_id": segment.segment_id,
        "segment_type": segment.segment_type,
        "start_offset": segment.start_offset,
        "end_offset": segment.end_offset,
        "text_sha256": segment.text_sha256,
        "source_locators": [
            _locator_to_dict(locator)
            for locator in segment.source_locators
        ],
    }


def _issue_to_dict(
    issue: ProjectionIssue,
) -> dict[str, Any]:
    return {
        "code": issue.code,
        "message": issue.message,
        "issue_level": issue.issue_level,
        "source_locators": [
            _locator_to_dict(locator)
            for locator in issue.source_locators
        ],
    }


def _locator_to_dict(
    locator: SourceLocator,
) -> dict[str, Any]:
    return {
        "locator_type": locator.locator_type,
        "coordinates": dict(locator.coordinates),
    }


def _parse_adapter_configuration(
    value: Any,
) -> AdapterConfiguration:
    if not isinstance(value, dict):
        raise SourceProjectionManifestError(
            "adapter_configuration must be a JSON object."
        )

    return _validate_adapter_configuration(
        tuple(value.items())
    )


def _validate_adapter_configuration(
    value: Any,
) -> AdapterConfiguration:
    if not isinstance(value, tuple):
        raise SourceProjectionManifestError(
            "adapter_configuration must be a tuple."
        )

    if not value:
        raise SourceProjectionManifestError(
            "adapter_configuration must not be empty."
        )

    configuration: dict[
        str,
        AdapterConfigurationValue,
    ] = {}

    for entry in value:
        if (
            not isinstance(entry, tuple)
            or len(entry) != 2
        ):
            raise SourceProjectionManifestError(
                "Every adapter configuration entry must "
                "be a key-value pair."
            )

        key, configuration_value = entry
        validated_key = _validate_lower_identifier(
            key,
            field_name="adapter configuration key",
        )

        if validated_key in configuration:
            raise SourceProjectionManifestError(
                "Adapter configuration keys must be unique."
            )

        if isinstance(configuration_value, float) or not isinstance(
            configuration_value,
            (str, int, bool, type(None)),
        ):
            raise SourceProjectionManifestError(
                "Adapter configuration values must be "
                "strings, integers, booleans or null."
            )

        configuration[validated_key] = (
            configuration_value
        )

    return tuple(
        sorted(
            configuration.items(),
            key=lambda item: item[0],
        )
    )


def _validate_projection_result(value: Any) -> str:
    if value not in PROJECTION_RESULTS:
        allowed_results = ", ".join(
            sorted(PROJECTION_RESULTS)
        )
        raise SourceProjectionManifestError(
            "Unsupported projection_result: "
            f"{value!r}. Expected one of: "
            f"{allowed_results}."
        )

    return value


def _validate_project_id(value: Any) -> str:
    if not is_valid_project_id(value):
        raise SourceProjectionManifestError(
            "project_id must be a string containing "
            "exactly six digits."
        )

    return value


def _validate_source_id(value: Any) -> str:
    try:
        return validate_source_id(value)
    except ProjectSourceError as exc:
        raise SourceProjectionManifestError(
            f"Invalid source_id: {exc}"
        ) from exc


def _validate_source_role(value: Any) -> str:
    try:
        return validate_source_role(value)
    except ProjectSourceError as exc:
        raise SourceProjectionManifestError(
            f"Invalid source_role: {exc}"
        ) from exc


def _validate_sha256(
    value: Any,
    *,
    field_name: str,
) -> str:
    if (
        not isinstance(value, str)
        or _SHA256_PATTERN.fullmatch(value) is None
    ):
        raise SourceProjectionManifestError(
            f"{field_name} must be a lowercase "
            "64-character hexadecimal value."
        )

    return value


def _validate_lower_identifier(
    value: Any,
    *,
    field_name: str,
) -> str:
    if (
        not isinstance(value, str)
        or _LOWER_IDENTIFIER_PATTERN.fullmatch(value)
        is None
    ):
        raise SourceProjectionManifestError(
            f"{field_name} must match "
            "^[a-z][a-z0-9_]*$."
        )

    return value


def _validate_semantic_version(
    value: Any,
    *,
    field_name: str,
) -> str:
    if (
        not isinstance(value, str)
        or _SEMANTIC_VERSION_PATTERN.fullmatch(value)
        is None
    ):
        raise SourceProjectionManifestError(
            f"{field_name} must use numeric "
            "major.minor.patch format."
        )

    return value


def _validate_nonnegative_integer(
    value: Any,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SourceProjectionManifestError(
            f"{field_name} must be an integer."
        )

    if value < 0:
        raise SourceProjectionManifestError(
            f"{field_name} must not be negative."
        )

    return value


def _validate_timestamp(
    value: Any,
    *,
    field_name: str,
) -> str:
    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None
    ):
        raise SourceProjectionManifestError(
            f"{field_name} must be an ISO-8601 UTC "
            "timestamp ending in Z."
        )

    try:
        datetime.fromisoformat(
            value.removesuffix("Z") + "+00:00"
        )
    except ValueError as exc:
        raise SourceProjectionManifestError(
            f"{field_name} is not a valid UTC timestamp."
        ) from exc

    return value


def _validate_trimmed_string(
    value: Any,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise SourceProjectionManifestError(
            f"{field_name} must be a string."
        )

    if not value or value != value.strip():
        raise SourceProjectionManifestError(
            f"{field_name} must be a non-empty "
            "trimmed string."
        )

    return value


def _validate_expected_identity(
    *,
    actual: str,
    expected: Any,
    validator: Any,
    field_name: str,
) -> None:
    if expected is None:
        return

    validated_expected = validator(expected)

    if actual != validated_expected:
        raise SourceProjectionManifestError(
            f"Manifest {field_name} does not match "
            "its storage context: "
            f"{actual!r} != {validated_expected!r}."
        )


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise SourceProjectionManifestError(
                "Source Projection Manifest contains "
                f"duplicate JSON member name: {key!r}."
            )

        result[key] = value

    return result


def _sha256_text(text: str) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def _require_exact_fields(
    value: dict[str, Any],
    expected_fields: frozenset[str],
    label: str,
) -> None:
    actual_fields = set(value)
    missing_fields = sorted(
        expected_fields - actual_fields
    )
    unknown_fields = sorted(
        actual_fields - expected_fields
    )

    problems: list[str] = []

    if missing_fields:
        problems.append(
            "missing " + ", ".join(missing_fields)
        )

    if unknown_fields:
        problems.append(
            "unknown " + ", ".join(unknown_fields)
        )

    if problems:
        raise SourceProjectionManifestError(
            f"{label} fields are invalid: "
            f"{'; '.join(problems)}."
        )