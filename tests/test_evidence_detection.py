"""Tests for specialized persona-independent Evidence Detection."""

from __future__ import annotations

import pytest

from modules.evidence_detection import (
    EvidenceDetectionAgent,
    EvidenceDetectionGroundingError,
    EvidenceDetectionValidationError,
    build_candidate_spans,
    parse_detection_response,
    resolve_detection_anchors,
)
from modules.llm.types import LLMResult
from modules.source_analysis_units.types import (
    SourceAnalysisUnit,
    SourceAnalysisUnitAnchor,
)


def unit(text: str) -> SourceAnalysisUnit:
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
                end_offset=len(text),
            ),
        ),
        source_excerpt=text,
        source_order_index=1,
        segmentation_profile_id="source_projection_segments",
        segmentation_profile_version="1.0.0",
        content_fingerprint="b" * 64,
        created_at="2026-08-21T10:00:00Z",
    )


class FakeClient:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return LLMResult(
            text=self.response_text,
            provider="openai",
            model=request.model,
            response_id="resp_detector_001",
            raw_status="completed",
        )


def test_detector_selects_candidate_id_and_reconstructs_exact_source() -> None:
    text = (
        "The expert may take temporary control when the operator permits it."
    )
    fake = FakeClient(
        """{
          "detections": [{
            "candidate_span_ids": ["CAND-001"],
            "relevance": "relevant",
            "rationale": "Control and permission information."
          }],
          "no_detection_rationale": null
        }"""
    )
    detector = EvidenceDetectionAgent(
        client_factory=lambda provider: fake
    )

    result = detector.detect(
        source_analysis_unit=unit(text),
        reference_examples="REFERENCE EXAMPLE ONLY",
        provider="openai",
        model="gpt-test",
    )

    assert len(result.detections) == 1
    detection = result.detections[0]
    assert detection.candidate_span_ids == ("CAND-001",)
    assert detection.source_excerpt == text
    assert detection.source_start_offset == 0
    assert detection.source_end_offset == len(text)

    request = fake.requests[0]
    assert "REFERENCE GUIDANCE" in request.input_text
    assert "CURRENT ENGINEERING SOURCE SCOPE" in request.input_text
    assert "REFERENCE EXAMPLE ONLY" in request.input_text
    assert "[CAND-001]" in request.input_text
    assert text in request.input_text
    assert '"source_excerpt"' not in request.instructions


def test_candidate_spans_preserve_exact_wrapped_sentence_text() -> None:
    text = (
        "The remote expert shall be able to observe the live microscope image. "
        "During the\\nsession, the expert may also take temporary control of the "
        "microscope when the\\noperator permits it. The operator remains responsible "
        "for the local session and must\\nbe able to understand who currently "
        "controls the microscope."
    )
    candidates = build_candidate_spans(unit(text))

    assert tuple(
        candidate.candidate_span_id
        for candidate in candidates
    ) == ("CAND-001", "CAND-002", "CAND-003")
    assert candidates[1].source_excerpt == (
        "During the\\nsession, the expert may also take temporary control of the "
        "microscope when the\\noperator permits it."
    )
    for candidate in candidates:
        assert text[
            candidate.start_offset:candidate.end_offset
        ] == candidate.source_excerpt


def test_candidate_spans_keep_bullets_as_independent_exact_candidates() -> None:
    text = (
        "- How long should session information be retained?\n"
        "- Which connection-quality limits are acceptable?\n"
        "- Which microscope functions may be controlled remotely?"
    )

    candidates = build_candidate_spans(unit(text))

    assert len(candidates) == 3
    assert candidates[0].source_excerpt == (
        "- How long should session information be retained?"
    )
    assert candidates[2].source_excerpt == (
        "- Which microscope functions may be controlled remotely?"
    )


def test_parser_reconstructs_contiguous_multi_candidate_selection() -> None:
    scope = unit("First sentence. Second sentence. Third sentence.")
    candidates = build_candidate_spans(scope)

    detections = parse_detection_response(
        """{
          "detections": [{
            "candidate_span_ids": ["CAND-001", "CAND-002"],
            "relevance": "relevant",
            "rationale": "Adjacent information belongs together."
          }],
          "no_detection_rationale": null
        }""",
        source_analysis_unit=scope,
        candidate_spans=candidates,
    )

    assert detections[0].source_excerpt == (
        "First sentence. Second sentence."
    )
    assert detections[0].source_start_offset == 0
    assert detections[0].source_end_offset == len(
        "First sentence. Second sentence."
    )


def test_parser_rejects_unknown_candidate_id() -> None:
    scope = unit("Engineering text.")
    candidates = build_candidate_spans(scope)

    with pytest.raises(EvidenceDetectionGroundingError):
        parse_detection_response(
            """{
              "detections": [{
                "candidate_span_ids": ["CAND-999"],
                "relevance": "relevant",
                "rationale": "Unknown candidate."
              }],
              "no_detection_rationale": null
            }""",
            source_analysis_unit=scope,
            candidate_spans=candidates,
        )


def test_parser_rejects_non_contiguous_candidate_selection() -> None:
    scope = unit("First sentence. Second sentence. Third sentence.")
    candidates = build_candidate_spans(scope)

    with pytest.raises(EvidenceDetectionGroundingError):
        parse_detection_response(
            """{
              "detections": [{
                "candidate_span_ids": ["CAND-001", "CAND-003"],
                "relevance": "relevant",
                "rationale": "Invalid non-contiguous selection."
              }],
              "no_detection_rationale": null
            }""",
            source_analysis_unit=scope,
            candidate_spans=candidates,
        )


def test_parser_rejects_model_generated_source_excerpt_field() -> None:
    scope = unit("Engineering text.")
    candidates = build_candidate_spans(scope)

    with pytest.raises(EvidenceDetectionValidationError):
        parse_detection_response(
            """{
              "detections": [{
                "candidate_span_ids": ["CAND-001"],
                "source_excerpt": "Engineering text.",
                "relevance": "relevant",
                "rationale": "Must not be accepted."
              }],
              "no_detection_rationale": null
            }""",
            source_analysis_unit=scope,
            candidate_spans=candidates,
        )


def test_parser_rejects_model_content() -> None:
    scope = unit("Engineering text.")
    candidates = build_candidate_spans(scope)

    with pytest.raises(EvidenceDetectionValidationError):
        parse_detection_response(
            """{
              "detections": [],
              "no_detection_rationale": "none",
              "model_candidate": "shall not exist"
            }""",
            source_analysis_unit=scope,
            candidate_spans=candidates,
        )


def test_exact_excerpt_resolves_to_source_anchor() -> None:
    scope = unit("AAAA relevant engineering text BBBB")
    anchors = resolve_detection_anchors(
        source_analysis_unit=scope,
        detected_excerpt="relevant engineering text",
    )
    assert anchors[0].segment_id == "SEG-000001"
    assert anchors[0].start_offset == 5
    assert anchors[0].end_offset == 30


def test_explicit_offsets_allow_exact_repeated_text_without_fuzzy_matching() -> None:
    scope = unit("same text and same text")
    anchors = resolve_detection_anchors(
        source_analysis_unit=scope,
        detected_excerpt="same text",
        source_start_offset=14,
        source_end_offset=23,
    )

    assert anchors[0].start_offset == 14
    assert anchors[0].end_offset == 23


def test_explicit_offsets_fail_closed_when_exact_text_does_not_match() -> None:
    scope = unit("Engineering text.")

    with pytest.raises(EvidenceDetectionGroundingError):
        resolve_detection_anchors(
            source_analysis_unit=scope,
            detected_excerpt="Engineering text.",
            source_start_offset=1,
            source_end_offset=len("Engineering text."),
        )


def test_ambiguous_excerpt_without_offsets_fails_closed() -> None:
    with pytest.raises(EvidenceDetectionGroundingError):
        resolve_detection_anchors(
            source_analysis_unit=unit("same text and same text"),
            detected_excerpt="same text",
        )


def test_dry_run_makes_no_llm_call() -> None:
    fake = FakeClient("unused")
    detector = EvidenceDetectionAgent(
        client_factory=lambda provider: fake
    )
    result = detector.detect(
        source_analysis_unit=unit("Engineering text."),
        reference_examples="reference",
        provider="openai",
        model="gpt-test",
        dry_run=True,
    )
    assert result.raw_status == "dry_run"
    assert result.detections == ()
    assert fake.requests == []
