"""Tests for the public G5.6 Approved Input lifecycle API."""

import modules.approved_input as approved_input


def test_lifecycle_symbols_are_public() -> None:
    expected = {
        "APPROVED_INPUT_EVENT_SCHEMA_VERSION",
        "APPROVED_INPUT_EVENT_TYPES",
        "ApprovedInputAuthoritySnapshot",
        "ApprovedInputEvent",
        "ApprovedInputLifecycleService",
        "active_approved_input_manifests",
        "approved_input_event_from_json",
        "approved_input_event_to_json",
        "calculate_approved_input_event_fingerprint",
        "calculate_promotion_equivalence_fingerprint",
        "create_approved_input_event",
        "derive_approved_input_authority_states",
        "validate_approved_input_event",
    }

    assert expected.issubset(set(approved_input.__all__))
