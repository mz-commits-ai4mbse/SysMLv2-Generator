"""Tests for the immutable Source Analysis Unit manifest."""

from dataclasses import FrozenInstanceError, replace
import json

import pytest

from modules.source_analysis_units.errors import (
    SourceAnalysisUnitAnchorError,
    SourceAnalysisUnitValidationError,
)
from modules.source_analysis_units.manifest import (
    calculate_source_analysis_unit_content_fingerprint,
    create_source_analysis_unit,
    source_analysis_unit_from_json,
    source_analysis_unit_to_json,
)
from modules.source_analysis_units.types import (
    SourceAnalysisUnitAnchor,
)


PROJECT_ID = "318604"
SOURCE_ID = "SRC-000001"
PROJECTION_ID = "SP-000001"
TIMESTAMP = "2026-08-18T20:00:00Z"


def anchor() -> SourceAnalysisUnitAnchor:
    return SourceAnalysisUnitAnchor(
        segment_id="SEG-000001",
        start_offset=0,
        end_offset=5,
    )


def unit(**changes: object) -> object:
    values: dict[str, object] = {
        "project_id": PROJECT_ID,
        "source_id": SOURCE_ID,
        "source_projection_id": PROJECTION_ID,
        "source_analysis_unit_id": "SAU-000001",
        "source_projection_fingerprint": "a" * 64,
        "source_anchors": (anchor(),),
        "source_excerpt": "Alpha",
        "source_order_index": 1,
        "segmentation_profile_id": (
            "source_projection_segments"
        ),
        "segmentation_profile_version": "1.0.0",
        "timestamp": TIMESTAMP,
    }
    values.update(changes)
    return create_source_analysis_unit(**values)


def test_source_analysis_unit_is_immutable() -> None:
    value = unit()
    with pytest.raises(FrozenInstanceError):
        value.source_excerpt = "Changed"  # type: ignore[misc]


def test_json_round_trip_is_deterministic() -> None:
    value = unit()
    serialized = source_analysis_unit_to_json(value)

    assert source_analysis_unit_from_json(
        serialized
    ) == value
    assert source_analysis_unit_to_json(
        source_analysis_unit_from_json(serialized)
    ) == serialized


def test_fingerprint_excludes_identity_and_creation_time() -> None:
    first = unit()
    second = unit(
        source_analysis_unit_id="SAU-000002",
        timestamp="2026-08-18T20:01:00Z",
    )

    assert (
        first.content_fingerprint
        == second.content_fingerprint
    )


def test_fingerprint_changes_with_source_scope() -> None:
    first = unit()
    second = unit(source_excerpt="Alpha!")
    assert (
        first.content_fingerprint
        != second.content_fingerprint
    )


def test_tampered_fingerprint_is_rejected() -> None:
    payload = json.loads(
        source_analysis_unit_to_json(unit())
    )
    payload["source_excerpt"] = "Tampered"

    with pytest.raises(
        SourceAnalysisUnitValidationError
    ):
        source_analysis_unit_from_json(
            json.dumps(payload)
        )


def test_anchor_must_use_nonempty_range() -> None:
    with pytest.raises(SourceAnalysisUnitAnchorError):
        unit(
            source_anchors=(
                SourceAnalysisUnitAnchor(
                    segment_id="SEG-000001",
                    start_offset=0,
                    end_offset=0,
                ),
            )
        )


def test_fingerprint_function_matches_manifest() -> None:
    value = unit()
    assert value.content_fingerprint == (
        calculate_source_analysis_unit_content_fingerprint(
            project_id=PROJECT_ID,
            source_id=SOURCE_ID,
            source_projection_id=PROJECTION_ID,
            source_projection_fingerprint="a" * 64,
            source_anchors=(anchor(),),
            source_excerpt="Alpha",
            source_order_index=1,
            segmentation_profile_id=(
                "source_projection_segments"
            ),
            segmentation_profile_version="1.0.0",
        )
    )
