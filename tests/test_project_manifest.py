from dataclasses import replace
import json

import pytest

import modules.project_workspace.identifiers as identifiers
from modules.project_workspace.errors import ProjectManifestError
from modules.project_workspace.identifiers import (
    generate_project_id,
    is_valid_project_id,
    normalize_display_name,
)
from modules.project_workspace.manifest import (
    DESCRIPTION_MAX_LENGTH,
    DISPLAY_NAME_MAX_LENGTH,
    PROJECT_MANIFEST_SCHEMA_VERSION,
    create_project_manifest,
    parse_project_manifest,
    project_manifest_from_json,
    project_manifest_to_dict,
    project_manifest_to_json,
    validate_project_manifest,
)
from modules.project_workspace.types import FrameworkTemplateReference


TEST_TIMESTAMP = "2026-07-22T08:00:00Z"


def _valid_manifest():
    return create_project_manifest(
        "000042",
        "Example Project",
        description="Manifest test project",
        timestamp=TEST_TIMESTAMP,
    )


def _valid_payload():
    return project_manifest_to_dict(_valid_manifest())


def test_project_id_generation_is_six_digit_string(
    monkeypatch,
) -> None:
    observed_upper_bounds = []

    def fake_randbelow(upper_bound):
        observed_upper_bounds.append(upper_bound)
        return 42

    monkeypatch.setattr(
        identifiers.secrets,
        "randbelow",
        fake_randbelow,
    )

    assert generate_project_id() == "000042"
    assert observed_upper_bounds == [1_000_000]


@pytest.mark.parametrize(
    "value",
    [
        "000000",
        "000042",
        "999999",
    ],
)
def test_valid_project_ids_are_accepted(value) -> None:
    assert is_valid_project_id(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        42,
        "",
        "42",
        "12345",
        "1234567",
        "12345A",
        "../123",
    ],
)
def test_invalid_project_ids_are_rejected(value) -> None:
    assert not is_valid_project_id(value)


def test_display_name_normalization_is_deterministic() -> None:
    assert (
        normalize_display_name("  Example   Project  ")
        == "example project"
    )
    assert normalize_display_name("Straße") == "strasse"
    assert normalize_display_name("STRASSE") == "strasse"
    assert normalize_display_name("ＴＵＲＩＮＧ") == "turing"


def test_create_manifest_trims_name_and_pins_framework() -> None:
    manifest = create_project_manifest(
        "000042",
        "  Example Project  ",
        timestamp=TEST_TIMESTAMP,
    )

    assert manifest.schema_version == PROJECT_MANIFEST_SCHEMA_VERSION
    assert manifest.project_id == "000042"
    assert manifest.display_name == "Example Project"
    assert manifest.description == ""
    assert manifest.framework_template.template_id == (
        "TURING_RFLP_FRAMEWORK"
    )
    assert manifest.framework_template.template_version == "1.0.0"
    assert manifest.created_at == TEST_TIMESTAMP
    assert manifest.updated_at == TEST_TIMESTAMP


@pytest.mark.parametrize(
    "project_id",
    [
        None,
        42,
        "",
        "12345",
        "1234567",
        "12345A",
    ],
)
def test_manifest_rejects_invalid_project_id(project_id) -> None:
    payload = _valid_payload()
    payload["project_id"] = project_id

    with pytest.raises(
        ProjectManifestError,
        match="exactly six digits",
    ):
        parse_project_manifest(payload)


@pytest.mark.parametrize(
    "display_name",
    [
        None,
        "",
        "   ",
        " Example Project",
        "Example Project ",
        "X" * (DISPLAY_NAME_MAX_LENGTH + 1),
    ],
)
def test_manifest_rejects_invalid_display_name(
    display_name,
) -> None:
    payload = _valid_payload()
    payload["display_name"] = display_name

    with pytest.raises(ProjectManifestError):
        parse_project_manifest(payload)


@pytest.mark.parametrize(
    "description",
    [
        None,
        "X" * (DESCRIPTION_MAX_LENGTH + 1),
    ],
)
def test_manifest_rejects_invalid_description(
    description,
) -> None:
    payload = _valid_payload()
    payload["description"] = description

    with pytest.raises(ProjectManifestError):
        parse_project_manifest(payload)


def test_manifest_rejects_missing_and_unknown_fields() -> None:
    missing = _valid_payload()
    del missing["description"]

    with pytest.raises(
        ProjectManifestError,
        match="missing description",
    ):
        parse_project_manifest(missing)

    unknown = _valid_payload()
    unknown["source_count"] = 0

    with pytest.raises(
        ProjectManifestError,
        match="unknown source_count",
    ):
        parse_project_manifest(unknown)


def test_framework_reference_rejects_contract_changes() -> None:
    missing = _valid_payload()
    del missing["framework_template"]["template_version"]

    with pytest.raises(
        ProjectManifestError,
        match="missing template_version",
    ):
        parse_project_manifest(missing)

    unknown = _valid_payload()
    unknown["framework_template"]["automatic_upgrade"] = True

    with pytest.raises(
        ProjectManifestError,
        match="unknown automatic_upgrade",
    ):
        parse_project_manifest(unknown)


@pytest.mark.parametrize(
    ("template_id", "template_version"),
    [
        ("UNKNOWN_FRAMEWORK", "1.0.0"),
        ("TURING_RFLP_FRAMEWORK", "2.0.0"),
    ],
)
def test_manifest_rejects_unpinned_framework(
    template_id,
    template_version,
) -> None:
    payload = _valid_payload()
    payload["framework_template"] = {
        "template_id": template_id,
        "template_version": template_version,
    }

    with pytest.raises(
        ProjectManifestError,
        match="Unsupported framework template reference",
    ):
        parse_project_manifest(payload)


def test_manifest_rejects_unknown_schema_version() -> None:
    payload = _valid_payload()
    payload["schema_version"] = "2.0.0"

    with pytest.raises(
        ProjectManifestError,
        match="Unsupported project manifest schema_version",
    ):
        parse_project_manifest(payload)


@pytest.mark.parametrize(
    "timestamp",
    [
        None,
        "",
        "2026-07-22 08:00:00Z",
        "2026-07-22T08:00:00+00:00",
        "2026-07-22T08:00Z",
        "2026-02-30T08:00:00Z",
    ],
)
def test_manifest_rejects_invalid_utc_timestamp(
    timestamp,
) -> None:
    payload = _valid_payload()
    payload["created_at"] = timestamp

    with pytest.raises(ProjectManifestError):
        parse_project_manifest(payload)


def test_updated_at_cannot_precede_created_at() -> None:
    payload = _valid_payload()
    payload["created_at"] = "2026-07-22T09:00:00Z"
    payload["updated_at"] = "2026-07-22T08:00:00Z"

    with pytest.raises(
        ProjectManifestError,
        match="must not be earlier",
    ):
        parse_project_manifest(payload)


def test_manifest_project_id_must_match_directory() -> None:
    with pytest.raises(
        ProjectManifestError,
        match="does not match",
    ):
        parse_project_manifest(
            _valid_payload(),
            expected_project_id="000043",
        )


def test_manifest_json_roundtrip_is_deterministic() -> None:
    manifest = create_project_manifest(
        "000042",
        "Äußeres System",
        description="Unicode remains readable.",
        timestamp=TEST_TIMESTAMP,
    )

    first_serialization = project_manifest_to_json(manifest)
    reloaded = project_manifest_from_json(
        first_serialization,
        expected_project_id="000042",
    )
    second_serialization = project_manifest_to_json(reloaded)

    assert reloaded == manifest
    assert first_serialization == second_serialization
    assert first_serialization.endswith("\n")
    assert "Äußeres System" in first_serialization


@pytest.mark.parametrize(
    "text",
    [
        "",
        "{",
        "[]",
        "null",
    ],
)
def test_invalid_json_documents_are_rejected(text) -> None:
    with pytest.raises(ProjectManifestError):
        project_manifest_from_json(text)


def test_json_input_must_be_a_string() -> None:
    with pytest.raises(
        ProjectManifestError,
        match="must be a string",
    ):
        project_manifest_from_json(42)


def test_serialization_revalidates_manifest() -> None:
    manifest = _valid_manifest()
    invalid_manifest = replace(
        manifest,
        framework_template=FrameworkTemplateReference(
            template_id="UNKNOWN_FRAMEWORK",
            template_version="1.0.0",
        ),
    )

    with pytest.raises(ProjectManifestError):
        project_manifest_to_json(invalid_manifest)


def test_validate_manifest_accepts_valid_instance() -> None:
    validate_project_manifest(
        _valid_manifest(),
        expected_project_id="000042",
    )


def test_serialized_manifest_contains_only_contract_fields() -> None:
    payload = json.loads(
        project_manifest_to_json(_valid_manifest())
    )

    assert set(payload) == {
        "schema_version",
        "project_id",
        "display_name",
        "description",
        "framework_template",
        "created_at",
        "updated_at",
    }