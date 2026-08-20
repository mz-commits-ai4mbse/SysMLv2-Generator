"""Tests for Source Analysis Unit identifiers."""

import pytest

from modules.source_analysis_units.errors import (
    SourceAnalysisUnitIdAllocationError,
    SourceAnalysisUnitValidationError,
)
from modules.source_analysis_units.identifiers import (
    format_source_analysis_unit_id,
    is_valid_source_analysis_unit_id,
    next_source_analysis_unit_id,
    source_analysis_unit_id_sequence,
    validate_source_analysis_unit_id,
)


def test_valid_identifier_contract() -> None:
    assert is_valid_source_analysis_unit_id(
        "SAU-000001"
    )
    assert validate_source_analysis_unit_id(
        "SAU-999999"
    ) == "SAU-999999"
    assert source_analysis_unit_id_sequence(
        "SAU-000042"
    ) == 42
    assert format_source_analysis_unit_id(
        42
    ) == "SAU-000042"


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "SAU-000000",
        "SAU-1",
        "sau-000001",
        "SAU-1000000",
        1,
    ],
)
def test_invalid_identifier_is_rejected(
    value: object,
) -> None:
    assert not is_valid_source_analysis_unit_id(value)
    with pytest.raises(
        SourceAnalysisUnitValidationError
    ):
        validate_source_analysis_unit_id(value)


def test_next_identifier_does_not_reuse_gaps() -> None:
    assert next_source_analysis_unit_id(
        (
            "SAU-000001",
            "SAU-000003",
        )
    ) == "SAU-000004"


def test_next_identifier_rejects_duplicates() -> None:
    with pytest.raises(
        SourceAnalysisUnitIdAllocationError
    ):
        next_source_analysis_unit_id(
            (
                "SAU-000001",
                "SAU-000001",
            )
        )
