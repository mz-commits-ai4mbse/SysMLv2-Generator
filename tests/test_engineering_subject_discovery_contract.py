"""R4c.1/R4c.2 tests for canonical engineering-subject discovery."""

from __future__ import annotations

import json

import pytest

from modules.engineering_subjects import (
    EngineeringSubjectDiscoveryAgent,
    EngineeringSubjectIntegrityError,
    canonical_subject_set_to_dict,
)
from modules.llm.types import LLMResult
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
    "# Product context\n\n"
    "The microscope operator works at the microscope workstation. "
    "The remote expert joins from a separate client application.\n\n"
    "The remote expert shall be able to observe the live microscope image. "
    "During the session, the expert may also take temporary control of the "
    "microscope when the operator permits it."
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


def _evidence():
    operator_start = _CONTENT.index("The microscope operator")
    second_start = _CONTENT.index("The remote expert shall")
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
                    start_offset=operator_start,
                    end_offset=second_start - 2,
                ),
            ),
            source_excerpt=_CONTENT[
                operator_start:second_start - 2
            ],
            content_fingerprint="b" * 64,
            created_at="2026-08-24T00:00:00Z",
        ),
        SourceEvidence(
            schema_version="1.0.0",
            project_id="396272",
            source_id="SRC-000001",
            source_projection_id="SP-000001",
            source_evidence_id="EVD-000002",
            source_projection_fingerprint=_SHA,
            source_anchors=(
                SourceEvidenceAnchor(
                    segment_id="SEG-000001",
                    start_offset=second_start,
                    end_offset=len(_CONTENT),
                ),
            ),
            source_excerpt=_CONTENT[second_start:],
            content_fingerprint="c" * 64,
            created_at="2026-08-24T00:00:00Z",
        ),
    )


class _Client:
    def __init__(self, output):
        self.output = output
        self.request = None

    def generate(self, request):
        self.request = request
        return LLMResult(
            text=json.dumps(self.output),
            provider="openai",
            model="gpt-test",
            response_id="resp-test",
        )


def _run(output):
    client = _Client(output)
    agent = EngineeringSubjectDiscoveryAgent(
        client_factory=lambda provider: client,
    )
    result = agent.discover(
        source_projection=_projection(),
        source_evidence=_evidence(),
        provider="openai",
        model="gpt-test",
    )
    return result, client


def _mention(span, start, end):
    return {
        "source_span_id": span,
        "start_token_id": start,
        "end_token_id": end,
    }


def test_context_is_readable_and_has_separate_token_addresses():
    result, client = _run({"subjects": []})

    assert len(result.source_spans) == 5
    assert "# Product context" in client.request.input_text
    assert "SOURCE TEXT:" in client.request.input_text
    assert "TOKEN MAP:" in client.request.input_text
    assert 'TOK-000024="remote"' in client.request.input_text

    heading = result.source_spans[0]
    assert heading.exact_text == "# Product context"
    assert heading.source_evidence_ids == ()


def test_repeated_remote_expert_mentions_become_one_subject():
    result, _ = _run(
        {
            "subjects": [
                {
                    "canonical_label": "Remote Expert",
                    "subject_form": "entity",
                    "identity_status": "resolved",
                    "mentions": [
                        _mention(
                            "SPAN-000003",
                            "TOK-000014",
                            "TOK-000015",
                        ),
                        _mention(
                            "SPAN-000004",
                            "TOK-000024",
                            "TOK-000025",
                        ),
                        _mention(
                            "SPAN-000005",
                            "TOK-000040",
                            "TOK-000041",
                        ),
                    ],
                }
            ]
        }
    )

    subject_set = result.canonical_subject_set
    assert len(subject_set.subjects) == 1
    assert subject_set.subjects[0].canonical_label == "Remote Expert"
    assert len(subject_set.mentions) == 3
    assert tuple(
        mention.exact_text
        for mention in subject_set.mentions
    ) == (
        "remote expert",
        "remote expert",
        "the expert",
    )


def test_one_evidence_passage_can_yield_multiple_subjects():
    result, _ = _run(
        {
            "subjects": [
                {
                    "canonical_label": "Remote Expert",
                    "subject_form": "entity",
                    "identity_status": "resolved",
                    "mentions": [
                        _mention(
                            "SPAN-000004",
                            "TOK-000024",
                            "TOK-000025",
                        )
                    ],
                },
                {
                    "canonical_label": "Live Microscope Image Observation",
                    "subject_form": "behavior",
                    "identity_status": "resolved",
                    "mentions": [
                        _mention(
                            "SPAN-000004",
                            "TOK-000030",
                            "TOK-000034",
                        )
                    ],
                },
                {
                    "canonical_label": "Temporary Microscope Control",
                    "subject_form": "behavior",
                    "identity_status": "resolved",
                    "mentions": [
                        _mention(
                            "SPAN-000005",
                            "TOK-000045",
                            "TOK-000049",
                        )
                    ],
                },
                {
                    "canonical_label": "Operator Permission",
                    "subject_form": "condition",
                    "identity_status": "resolved",
                    "mentions": [
                        _mention(
                            "SPAN-000005",
                            "TOK-000051",
                            "TOK-000054",
                        )
                    ],
                },
            ]
        }
    )

    labels = {
        subject.canonical_label
        for subject in result.canonical_subject_set.subjects
    }
    assert labels == {
        "Remote Expert",
        "Live Microscope Image Observation",
        "Temporary Microscope Control",
        "Operator Permission",
    }


def test_context_only_span_cannot_create_positive_subject():
    with pytest.raises(EngineeringSubjectIntegrityError):
        _run(
            {
                "subjects": [
                    {
                        "canonical_label": "Product context",
                        "subject_form": "other",
                        "identity_status": "resolved",
                        "mentions": [
                            _mention(
                                "SPAN-000001",
                                "TOK-000002",
                                "TOK-000003",
                            )
                        ],
                    }
                ]
            }
        )


def test_materialized_set_has_stable_fingerprints_and_source_binding():
    result, _ = _run(
        {
            "subjects": [
                {
                    "canonical_label": "Microscope Operator",
                    "subject_form": "entity",
                    "identity_status": "resolved",
                    "mentions": [
                        _mention(
                            "SPAN-000002",
                            "TOK-000005",
                            "TOK-000006",
                        )
                    ],
                }
            ]
        }
    )

    payload = canonical_subject_set_to_dict(
        result.canonical_subject_set
    )
    assert payload["project_id"] == "396272"
    assert payload["subjects"][0]["canonical_subject_id"] == "SUBJ-000001"
    assert payload["mentions"][0]["exact_text"] == "microscope operator"
    assert len(payload["subjects"][0]["content_fingerprint"]) == 64
    assert len(payload["mentions"][0]["content_fingerprint"]) == 64
