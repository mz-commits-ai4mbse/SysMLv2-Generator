"""Regression tests for strict Evidence Detection prompt boundaries."""

from modules.evidence_detection.prompt import (
    EVIDENCE_DETECTION_INSTRUCTIONS,
    EVIDENCE_DETECTION_PROMPT_SCHEMA_VERSION,
    build_evidence_detection_input,
)
from modules.source_analysis_units.types import (
    SourceAnalysisUnit,
    SourceAnalysisUnitAnchor,
)


_BEGIN = "<<<BEGIN_CURRENT_ENGINEERING_SOURCE_SCOPE>>>"
_END = "<<<END_CURRENT_ENGINEERING_SOURCE_SCOPE>>>"


def _unit(source_excerpt: str) -> SourceAnalysisUnit:
    return SourceAnalysisUnit(
        schema_version="1.0.0",
        project_id="318604",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        source_analysis_unit_id="SAU-000001",
        source_projection_fingerprint="a" * 64,
        source_anchors=(
            SourceAnalysisUnitAnchor(
                segment_id="SEG-000001",
                start_offset=0,
                end_offset=len(source_excerpt),
            ),
        ),
        source_excerpt=source_excerpt,
        source_order_index=1,
        segmentation_profile_id="source_projection_segments",
        segmentation_profile_version="1.0.0",
        content_fingerprint="b" * 64,
        created_at="2026-08-21T10:00:00Z",
    )


def test_prompt_schema_version_bumped_for_candidate_id_contract():
    assert EVIDENCE_DETECTION_PROMPT_SCHEMA_VERSION == "1.1.0"


def test_current_engineering_source_is_strictly_bounded_at_end_of_input():
    source_excerpt = "# Remote Microscope Collaboration — Product Overview"
    prompt = build_evidence_detection_input(
        source_analysis_unit=_unit(source_excerpt),
        reference_examples="Context-only example.",
    )

    assert prompt.count(_BEGIN) == 2
    assert prompt.count(_END) == 2

    begin = prompt.rfind(_BEGIN)
    end = prompt.rfind(_END)

    assert prompt.index("# TASK") < begin
    assert prompt.index("Context-only example.") < begin
    assert begin < end
    assert prompt[end + len(_END):].strip() == ""

    source_region = prompt[begin + len(_BEGIN):end]
    assert source_excerpt in source_region
    assert "[CAND-001]" in source_region
    assert "# TASK" not in source_region
    assert "Context-only example." not in source_region


def test_prompt_requires_ids_and_forbids_model_generated_source_text():
    prompt = build_evidence_detection_input(
        source_analysis_unit=_unit(
            "Line 1\nLine 2 — exact punctuation\nLine 3"
        ),
        reference_examples="Reference guidance.",
    )

    assert '"candidate_span_ids"' in EVIDENCE_DETECTION_INSTRUCTIONS
    assert '"source_excerpt"' not in EVIDENCE_DETECTION_INSTRUCTIONS
    assert "Do not copy source text into the response." in prompt
