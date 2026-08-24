"""R4c.2b tests for subject coverage and heading exclusion."""

from __future__ import annotations

from modules.engineering_subjects.context import (
    build_discovery_source_spans,
)
from modules.engineering_subjects.prompt import (
    ENGINEERING_SUBJECT_DISCOVERY_PROMPT_SCHEMA_VERSION,
    build_engineering_subject_discovery_instructions,
)
from modules.source_evidence.types import (
    SourceEvidence,
    SourceEvidenceAnchor,
)
from modules.source_projection.types import (
    ProjectionSegment,
    SourceProjectionArtifact,
    SourceProjectionManifest,
)


_SHA = "a" * 64
_CONTENT = (
    "# Product questions\n\n"
    "A controller may perform an action when another role permits it. "
    "The local operator remains responsible and must understand "
    "who currently has control."
)


def _projection():
    segment = ProjectionSegment(
        segment_id="SEG-000001",
        segment_type="text",
        start_offset=0,
        end_offset=len(_CONTENT),
        text_sha256=_SHA,
        source_locators=(),
    )
    manifest = SourceProjectionManifest(
        schema_version="1.0.0",
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        source_role="engineering_source",
        source_sha256=_SHA,
        adapter_id="test",
        adapter_version="1.0.0",
        adapter_configuration=(),
        projection_fingerprint=_SHA,
        projection_result="available",
        content_sha256=_SHA,
        content_length=len(_CONTENT),
        segments=(segment,),
        issues=(),
        created_at="2026-08-24T00:00:00Z",
    )
    return SourceProjectionArtifact(
        manifest=manifest,
        content=_CONTENT,
    )


def _evidence_covering_whole_source():
    return (
        SourceEvidence(
            schema_version="1.0.0",
            project_id="396272",
            source_id="SRC-000001",
            source_projection_id="SP-000001",
            source_evidence_id="EVD-000001",
            source_projection_fingerprint=_SHA,
            source_anchors=(
                SourceEvidenceAnchor(
                    segment_id="SEG-000001",
                    start_offset=0,
                    end_offset=len(_CONTENT),
                ),
            ),
            source_excerpt=_CONTENT,
            content_fingerprint="b" * 64,
            created_at="2026-08-24T00:00:00Z",
        ),
    )


def test_heading_is_context_only_even_when_evidence_overlaps_it():
    spans = build_discovery_source_spans(
        _projection(),
        _evidence_covering_whole_source(),
    )

    heading = next(
        span
        for span in spans
        if span.exact_text == "# Product questions"
    )
    body = tuple(
        span
        for span in spans
        if not span.exact_text.startswith("#")
    )

    assert heading.source_evidence_ids == ()
    assert body
    assert all(span.source_evidence_ids for span in body)


def test_prompt_requires_generic_second_coverage_pass():
    instructions = build_engineering_subject_discovery_instructions()

    assert ENGINEERING_SUBJECT_DISCOVERY_PROMPT_SCHEMA_VERSION == "1.3.1"
    assert "SECOND COVERAGE PASS" in instructions
    assert "permissions, enabling conditions" in instructions
    assert "responsibilities, ownership or accountability" in instructions
    assert "awareness, visibility, observability" in instructions
    assert '"A may perform B when C permits it"' in instructions


def test_prompt_keeps_sysml_classification_downstream():
    instructions = build_engineering_subject_discovery_instructions()

    assert "Do NOT classify subjects as Actor" in instructions
    assert "Do NOT create SysML v2 model structure" in instructions
