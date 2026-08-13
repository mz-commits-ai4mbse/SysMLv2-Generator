from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from modules.sysml_generation import (
    GeneratedSysMLArtifactSet,
    SysMLGenerationBlockedError,
    SysMLGenerationError,
    SysMLGenerationIntegrityError,
    TargetNotationReference,
    calculate_json_fingerprint,
    calculate_text_fingerprint,
    format_generated_sysml_unit_id,
    generated_element_symbol,
    generated_relationship_symbol,
    validate_generated_sysml_symbol,
    validate_generated_sysml_unit_id,
)


def test_generation_error_hierarchy_is_fail_closed() -> None:
    assert issubclass(SysMLGenerationBlockedError, SysMLGenerationIntegrityError)
    assert issubclass(SysMLGenerationIntegrityError, SysMLGenerationError)


@pytest.mark.parametrize(
    ("sequence", "expected"),
    [
        (1, "GSU-000001"),
        (42, "GSU-000042"),
        (999_999, "GSU-999999"),
    ],
)
def test_generated_unit_identifier_format(sequence: int, expected: str) -> None:
    assert format_generated_sysml_unit_id(sequence) == expected
    assert validate_generated_sysml_unit_id(expected) == expected


@pytest.mark.parametrize(
    "bad",
    [0, -1, 1_000_000, True, "1"],
)
def test_generated_unit_identifier_rejects_invalid_sequences(bad: object) -> None:
    with pytest.raises(Exception):
        format_generated_sysml_unit_id(bad)


def test_generated_symbols_derive_only_from_immutable_internal_identity() -> None:
    assert generated_element_symbol("IME-000042") == "IME_000042"
    assert generated_relationship_symbol("IMR-000007") == "IMR_000007"


@pytest.mark.parametrize(
    "symbol",
    ["IME_000001", "IMR_999999", "_privateStableSymbol", "A1"],
)
def test_generated_symbol_subset_accepts_machine_safe_symbols(symbol: str) -> None:
    assert validate_generated_sysml_symbol(symbol) == symbol


@pytest.mark.parametrize(
    "symbol",
    ["", "IME-000001", "has space", "1startsWithDigit", "ümlaut"],
)
def test_generated_symbol_subset_rejects_unsafe_symbols(symbol: str) -> None:
    with pytest.raises(Exception):
        validate_generated_sysml_symbol(symbol)


def test_json_fingerprint_is_canonical_for_key_order() -> None:
    first = {"b": 2, "a": 1}
    second = {"a": 1, "b": 2}
    assert calculate_json_fingerprint(first) == calculate_json_fingerprint(second)


def test_text_fingerprint_is_exact_byte_sensitive() -> None:
    assert calculate_text_fingerprint("a\n") != calculate_text_fingerprint("a")


def test_generation_contracts_are_frozen() -> None:
    ref = TargetNotationReference(
        context_id="CTX_SYSML_V2_TARGET_NOTATION",
        version="0.2.0",
        content_fingerprint="0" * 64,
    )
    with pytest.raises(FrozenInstanceError):
        ref.version = "changed"  # type: ignore[misc]


def test_artifact_set_contract_is_available_before_renderer_implementation() -> None:
    assert GeneratedSysMLArtifactSet.__dataclass_params__.frozen is True
