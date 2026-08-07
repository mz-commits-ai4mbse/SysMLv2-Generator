"""Tests for the Approved Input Manifest public API."""

import modules.approved_input as approved_input


def test_manifest_symbols_are_public() -> None:
    expected = {
        "APPROVED_INPUT_MANIFEST_SCHEMA_VERSION",
        "ApprovedInputCanonicalContent",
        "ApprovedInputManifest",
        "ApprovedInputRelationshipProperty",
        "ApprovedInputRelationshipRepresentation",
        "approved_input_manifest_from_json",
        "approved_input_manifest_to_dict",
        "approved_input_manifest_to_json",
        "calculate_approved_input_manifest_fingerprint",
        "create_approved_input_manifest",
        "parse_approved_input_manifest",
        "validate_approved_input_manifest",
    }

    assert expected.issubset(set(approved_input.__all__))
