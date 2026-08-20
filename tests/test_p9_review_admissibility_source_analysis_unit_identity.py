"""Regression tests for SAU-aware P9 derivation execution identity."""

import pytest

from modules.review_workspace.errors import ReviewValidationError
from modules.review_workspace.p9_proposal_adapter import (
    _source_analysis_unit_id_from_wrapper,
)
from modules.review_workspace.p9_review_admissibility_adapter import (
    _derivation_execution_identity,
)


def _wrapper(
    *,
    source_analysis_unit_id: str | None,
    run_index: int = 1,
) -> dict[str, object]:
    wrapper: dict[str, object] = {
        "agent_id": "AGENT_DERIVATION_ARCHITECTURE_FOCUSED_ASSESSOR",
        "persona_id": "architecture_focused_assessor",
        "run_index": run_index,
    }
    if source_analysis_unit_id is not None:
        wrapper["source_analysis_unit_id"] = source_analysis_unit_id
    return wrapper


def test_same_agent_run_is_distinct_across_source_analysis_units() -> None:
    first = _derivation_execution_identity(
        _wrapper(source_analysis_unit_id="SAU-000001")
    )
    second = _derivation_execution_identity(
        _wrapper(source_analysis_unit_id="SAU-000002")
    )

    assert first != second


def test_same_agent_run_is_duplicate_within_same_source_analysis_unit() -> None:
    first = _derivation_execution_identity(
        _wrapper(source_analysis_unit_id="SAU-000001")
    )
    duplicate = _derivation_execution_identity(
        _wrapper(source_analysis_unit_id="SAU-000001")
    )

    assert first == duplicate


def test_legacy_non_sau_execution_preserves_previous_identity_semantics() -> None:
    first = _derivation_execution_identity(
        _wrapper(source_analysis_unit_id=None)
    )
    duplicate = _derivation_execution_identity(
        _wrapper(source_analysis_unit_id=None)
    )

    assert first == duplicate
    assert first[0] is None

def test_p9_loader_helper_preserves_source_analysis_unit_binding() -> None:
    assert _source_analysis_unit_id_from_wrapper(
        {"source_analysis_unit_id": "SAU-000007"}
    ) == "SAU-000007"


def test_p9_loader_helper_allows_legacy_wrapper_without_sau() -> None:
    assert _source_analysis_unit_id_from_wrapper({}) is None


def test_p9_loader_helper_rejects_malformed_sau_identity() -> None:
    with pytest.raises(
        ReviewValidationError,
        match="source_analysis_unit_id",
    ):
        _source_analysis_unit_id_from_wrapper(
            {"source_analysis_unit_id": "SAU-7"}
        )
