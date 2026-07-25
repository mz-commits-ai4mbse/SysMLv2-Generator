"""Tests for immutable Processing Run Manifests."""

from dataclasses import replace
import json

import pytest

from modules.project_processing.errors import ProcessingValidationError
from modules.project_processing.run_manifest import (
    calculate_processing_run_manifest_fingerprint,
    create_processing_run_manifest,
    create_semantic_reference_version,
    parse_processing_run_manifest,
    processing_run_manifest_from_json,
    processing_run_manifest_to_dict,
    processing_run_manifest_to_json,
    validate_processing_run_manifest,
)


PROJECT_ID = "318604"
PROCESSING_RUN_ID = "RUN-000001"
SOURCE_ID = "SRC-000001"
SOURCE_SHA256 = "a" * 64
CONFIGURATION_FINGERPRINT = "b" * 64
CREATED_AT = "2026-07-25T10:00:00Z"


def _semantic_reference_versions():
    return (
        create_semantic_reference_version(
            reference_system_id="BFO",
            reference_version="2020",
        ),
        create_semantic_reference_version(
            reference_system_id="IOF_CORE",
            reference_version="202602",
        ),
        create_semantic_reference_version(
            reference_system_id="TURING_CORE_VOCABULARY",
            reference_version="1.0.0",
        ),
    )


def _manifest(**overrides):
    values = {
        "project_id": PROJECT_ID,
        "processing_run_id": PROCESSING_RUN_ID,
        "source_id": SOURCE_ID,
        "source_sha256": SOURCE_SHA256,
        "source_role_snapshot": "engineering_source",
        "workflow_profile": "engineering_source_processing",
        "configuration_fingerprint": CONFIGURATION_FINGERPRINT,
        "framework_template_id": "TURING_RFLP_FRAMEWORK",
        "framework_template_version": "1.0.0",
        "semantic_reference_versions": _semantic_reference_versions(),
        "timestamp": CREATED_AT,
        "supersedes_run_id": None,
    }
    values.update(overrides)
    return create_processing_run_manifest(**values)


def test_create_processing_run_manifest_populates_required_fields():
    manifest = _manifest()

    assert manifest.schema_version == "1.0.0"
    assert manifest.project_id == PROJECT_ID
    assert manifest.processing_run_id == PROCESSING_RUN_ID
    assert manifest.source_id == SOURCE_ID
    assert manifest.source_sha256 == SOURCE_SHA256
    assert manifest.source_role_snapshot == "engineering_source"
    assert manifest.workflow_profile == "engineering_source_processing"
    assert (
        manifest.configuration_fingerprint
        == CONFIGURATION_FINGERPRINT
    )
    assert manifest.framework_template_id == "TURING_RFLP_FRAMEWORK"
    assert manifest.framework_template_version == "1.0.0"
    assert (
        manifest.semantic_reference_versions
        == _semantic_reference_versions()
    )
    assert manifest.created_at == CREATED_AT
    assert manifest.supersedes_run_id is None


def test_processing_run_manifest_round_trip_is_lossless():
    manifest = _manifest()

    document = processing_run_manifest_to_json(manifest)
    parsed = processing_run_manifest_from_json(document)

    assert parsed == manifest


def test_processing_run_manifest_json_is_deterministic():
    manifest = _manifest()

    first = processing_run_manifest_to_json(manifest)
    second = processing_run_manifest_to_json(manifest)

    assert first == second
    assert first.endswith("\n")


def test_processing_run_manifest_dictionary_round_trip():
    manifest = _manifest()

    payload = processing_run_manifest_to_dict(manifest)
    parsed = parse_processing_run_manifest(payload)

    assert parsed == manifest


def test_processing_run_manifest_json_contains_no_null_supersession():
    payload = processing_run_manifest_to_dict(_manifest())

    assert "supersedes_run_id" not in payload


def test_processing_run_manifest_serializes_supersession():
    manifest = _manifest(
        processing_run_id="RUN-000002",
        supersedes_run_id="RUN-000001",
    )

    payload = processing_run_manifest_to_dict(manifest)

    assert payload["supersedes_run_id"] == "RUN-000001"
    assert parse_processing_run_manifest(payload) == manifest


def test_processing_run_manifest_fingerprint_is_stable_sha256():
    manifest = _manifest()

    first = calculate_processing_run_manifest_fingerprint(manifest)
    second = calculate_processing_run_manifest_fingerprint(manifest)

    assert first == second
    assert len(first) == 64
    assert set(first) <= set("0123456789abcdef")


def test_processing_run_manifest_fingerprint_changes_with_binding():
    original = _manifest()
    changed = replace(
        original,
        configuration_fingerprint="c" * 64,
    )

    assert (
        calculate_processing_run_manifest_fingerprint(original)
        != calculate_processing_run_manifest_fingerprint(changed)
    )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("project_id", ""),
        ("project_id", "31860"),
        ("project_id", "PRJ-318604"),
        ("processing_run_id", ""),
        ("processing_run_id", "RUN-000000"),
        ("processing_run_id", "RUN-1"),
        ("processing_run_id", "run-000001"),
        ("source_id", ""),
        ("source_id", "SRC-000000"),
        ("source_id", "SRC-1"),
        ("source_id", "src-000001"),
        ("source_sha256", ""),
        ("source_sha256", "a" * 63),
        ("source_sha256", "A" * 64),
        ("source_sha256", "g" * 64),
        ("configuration_fingerprint", ""),
        ("configuration_fingerprint", "b" * 63),
        ("configuration_fingerprint", "B" * 64),
        ("configuration_fingerprint", "z" * 64),
        ("framework_template_id", ""),
        ("framework_template_id", "turing-rflp-framework"),
        ("framework_template_version", ""),
        ("framework_template_version", " 1.0.0"),
        ("created_at", ""),
        ("created_at", "2026-07-25"),
        ("created_at", "2026-07-25T10:00:00"),
        ("created_at", "not-a-timestamp"),
    ],
)
def test_processing_run_manifest_rejects_invalid_binding(
    field_name,
    invalid_value,
):
    manifest = _manifest()
    invalid_manifest = replace(
        manifest,
        **{field_name: invalid_value},
    )

    with pytest.raises(ProcessingValidationError):
        validate_processing_run_manifest(invalid_manifest)


@pytest.mark.parametrize(
    "source_role_snapshot",
    [
        "",
        "engineering",
        "reference_source",
        "ENGINEERING_SOURCE",
    ],
)
def test_processing_run_manifest_rejects_unknown_source_role(
    source_role_snapshot,
):
    with pytest.raises(ProcessingValidationError):
        _manifest(source_role_snapshot=source_role_snapshot)


@pytest.mark.parametrize(
    "workflow_profile",
    [
        "",
        "engineering",
        "context_only",
        "ENGINEERING_SOURCE_PROCESSING",
    ],
)
def test_processing_run_manifest_rejects_unknown_workflow_profile(
    workflow_profile,
):
    with pytest.raises(ProcessingValidationError):
        _manifest(workflow_profile=workflow_profile)


def test_context_only_source_requires_context_only_workflow():
    with pytest.raises(ProcessingValidationError):
        _manifest(
            source_role_snapshot="context_only",
            workflow_profile="engineering_source_processing",
        )


def test_context_only_source_accepts_context_only_workflow():
    manifest = _manifest(
        source_role_snapshot="context_only",
        workflow_profile="context_only_processing",
    )

    assert manifest.source_role_snapshot == "context_only"
    assert manifest.workflow_profile == "context_only_processing"


def test_engineering_source_accepts_context_only_workflow():
    manifest = _manifest(
        source_role_snapshot="engineering_source",
        workflow_profile="context_only_processing",
    )

    assert manifest.source_role_snapshot == "engineering_source"
    assert manifest.workflow_profile == "context_only_processing"


def test_semantic_reference_versions_must_not_be_empty():
    manifest = replace(
        _manifest(),
        semantic_reference_versions=(),
    )

    with pytest.raises(ProcessingValidationError):
        validate_processing_run_manifest(manifest)


def test_semantic_reference_versions_must_be_tuple():
    manifest = replace(
        _manifest(),
        semantic_reference_versions=list(
            _semantic_reference_versions()
        ),
    )

    with pytest.raises(ProcessingValidationError):
        validate_processing_run_manifest(manifest)


def test_semantic_reference_versions_must_contain_expected_type():
    manifest = replace(
        _manifest(),
        semantic_reference_versions=("BFO:2020",),
    )

    with pytest.raises(ProcessingValidationError):
        validate_processing_run_manifest(manifest)


def test_semantic_reference_ids_must_be_unique():
    reference = create_semantic_reference_version(
        reference_system_id="BFO",
        reference_version="2020",
    )
    manifest = replace(
        _manifest(),
        semantic_reference_versions=(reference, reference),
    )

    with pytest.raises(ProcessingValidationError):
        validate_processing_run_manifest(manifest)


@pytest.mark.parametrize(
    ("reference_id", "version"),
    [
        ("", "2020"),
        (" ", "2020"),
        ("bfo", "2020"),
        ("BFO ", "2020"),
        ("BFO", ""),
        ("BFO", " "),
        ("BFO", " 2020"),
        ("BFO", "2020 "),
    ],
)
def test_create_semantic_reference_version_rejects_invalid_values(
    reference_id,
    version,
):
    with pytest.raises(ProcessingValidationError):
        create_semantic_reference_version(
            reference_system_id=reference_id,
            reference_version=version,
        )


def test_processing_run_manifest_rejects_self_supersession():
    manifest = replace(
        _manifest(),
        supersedes_run_id=PROCESSING_RUN_ID,
    )

    with pytest.raises(ProcessingValidationError):
        validate_processing_run_manifest(manifest)


@pytest.mark.parametrize(
    "supersedes_run_id",
    [
        "",
        "RUN-000000",
        "RUN-1",
        "run-000001",
    ],
)
def test_processing_run_manifest_rejects_invalid_supersession_reference(
    supersedes_run_id,
):
    manifest = replace(
        _manifest(),
        supersedes_run_id=supersedes_run_id,
    )

    with pytest.raises(ProcessingValidationError):
        validate_processing_run_manifest(manifest)


def test_processing_run_manifest_accepts_distinct_predecessor():
    manifest = _manifest(
        processing_run_id="RUN-000002",
        supersedes_run_id="RUN-000001",
    )

    validate_processing_run_manifest(manifest)


def test_parse_processing_run_manifest_rejects_unknown_field():
    payload = processing_run_manifest_to_dict(_manifest())
    payload["unexpected_field"] = "unexpected"

    with pytest.raises(ProcessingValidationError):
        parse_processing_run_manifest(payload)


@pytest.mark.parametrize(
    "field_name",
    [
        "schema_version",
        "project_id",
        "processing_run_id",
        "source_id",
        "source_sha256",
        "source_role_snapshot",
        "workflow_profile",
        "configuration_fingerprint",
        "framework_template_id",
        "framework_template_version",
        "semantic_reference_versions",
        "created_at",
    ],
)
def test_parse_processing_run_manifest_rejects_missing_required_field(
    field_name,
):
    payload = processing_run_manifest_to_dict(_manifest())
    del payload[field_name]

    with pytest.raises(ProcessingValidationError):
        parse_processing_run_manifest(payload)


def test_parse_processing_run_manifest_rejects_wrong_schema_version():
    payload = processing_run_manifest_to_dict(_manifest())
    payload["schema_version"] = "2.0.0"

    with pytest.raises(ProcessingValidationError):
        parse_processing_run_manifest(payload)


def test_processing_run_manifest_from_json_rejects_invalid_json():
    with pytest.raises(ProcessingValidationError):
        processing_run_manifest_from_json("{not valid json}")


def test_processing_run_manifest_from_json_rejects_non_object():
    with pytest.raises(ProcessingValidationError):
        processing_run_manifest_from_json("[]")


def test_processing_run_manifest_from_json_rejects_duplicate_keys():
    payload = processing_run_manifest_to_dict(_manifest())
    document = json.dumps(payload)
    duplicate_document = (
        document[:-1]
        + f', "project_id": "{PROJECT_ID}"'
        + "}"
    )

    with pytest.raises(ProcessingValidationError):
        processing_run_manifest_from_json(duplicate_document)