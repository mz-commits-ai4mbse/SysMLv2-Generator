"""Generic recovery tests for LLM Subject-grounding contract failures."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import modules.engineering_subjects.discovery as discovery_module
from modules.engineering_subjects import (
    ENGINEERING_SUBJECT_GROUNDING_REPAIR_SCHEMA_VERSION,
    DiscoveryMentionProposal,
    DiscoverySourceSpan,
    DiscoverySourceToken,
    DiscoverySubjectProposal,
    EngineeringSubjectDiscoveryAgent,
    EngineeringSubjectGroundingError,
    EngineeringSubjectIntegrityError,
    build_engineering_subject_grounding_repair_instructions,
    validate_subject_discovery_grounding,
)
from modules.llm.types import LLMResult


def _token(
    token_id: str,
    span_id: str,
    *,
    start_offset: int,
    text: str,
) -> DiscoverySourceToken:
    return DiscoverySourceToken(
        token_id=token_id,
        source_span_id=span_id,
        segment_id="SEG-000001",
        start_offset=start_offset,
        end_offset=start_offset + len(text),
        exact_text=text,
    )


def _spans() -> tuple[DiscoverySourceSpan, ...]:
    return (
        DiscoverySourceSpan(
            span_id="SPAN-000001",
            segment_id="SEG-000001",
            start_offset=0,
            end_offset=15,
            exact_text="Context heading",
            source_evidence_ids=(),
            source_tokens=(
                _token(
                    "TOK-000001",
                    "SPAN-000001",
                    start_offset=0,
                    text="Context",
                ),
                _token(
                    "TOK-000002",
                    "SPAN-000001",
                    start_offset=8,
                    text="heading",
                ),
            ),
        ),
        DiscoverySourceSpan(
            span_id="SPAN-000002",
            segment_id="SEG-000001",
            start_offset=20,
            end_offset=36,
            exact_text="Primary behavior",
            source_evidence_ids=("EVD-000001",),
            source_tokens=(
                _token(
                    "TOK-000003",
                    "SPAN-000002",
                    start_offset=20,
                    text="Primary",
                ),
                _token(
                    "TOK-000004",
                    "SPAN-000002",
                    start_offset=28,
                    text="behavior",
                ),
            ),
        ),
        DiscoverySourceSpan(
            span_id="SPAN-000003",
            segment_id="SEG-000001",
            start_offset=40,
            end_offset=59,
            exact_text="Secondary condition",
            source_evidence_ids=("EVD-000002",),
            source_tokens=(
                _token(
                    "TOK-000005",
                    "SPAN-000003",
                    start_offset=40,
                    text="Secondary",
                ),
                _token(
                    "TOK-000006",
                    "SPAN-000003",
                    start_offset=50,
                    text="condition",
                ),
            ),
        ),
    )


def _subject(
    label: str,
    span_id: str,
    start_token_id: str,
    end_token_id: str,
) -> DiscoverySubjectProposal:
    return DiscoverySubjectProposal(
        canonical_label=label,
        subject_form="other",
        identity_status="resolved",
        mentions=(
            DiscoveryMentionProposal(
                source_span_id=span_id,
                start_token_id=start_token_id,
                end_token_id=end_token_id,
            ),
        ),
    )


def _violating_proposals() -> tuple[DiscoverySubjectProposal, ...]:
    return (
        _subject(
            "Unknown Span",
            "SPAN-999999",
            "TOK-000003",
            "TOK-000004",
        ),
        _subject(
            "Context Only",
            "SPAN-000001",
            "TOK-000001",
            "TOK-000002",
        ),
        _subject(
            "Unknown Token",
            "SPAN-000002",
            "TOK-999999",
            "TOK-000004",
        ),
        _subject(
            "Wrong Span Token",
            "SPAN-000002",
            "TOK-000005",
            "TOK-000004",
        ),
        _subject(
            "Reversed Range",
            "SPAN-000002",
            "TOK-000004",
            "TOK-000003",
        ),
    )


def test_validator_collects_generic_grounding_violation_matrix():
    with pytest.raises(EngineeringSubjectGroundingError) as captured:
        validate_subject_discovery_grounding(
            source_spans=_spans(),
            proposals=_violating_proposals(),
        )

    error = captured.value
    assert isinstance(error, EngineeringSubjectIntegrityError)
    assert tuple(item.code for item in error.violations) == (
        "unknown_source_span",
        "context_only_positive_mention",
        "unknown_token",
        "token_not_in_claimed_span",
        "reversed_token_range",
    )
    assert error.violations[3].token_role == "start"
    assert error.violations[3].actual_source_span_id == "SPAN-000003"


def test_system_owned_duplicate_token_ids_are_not_llm_repair_errors():
    spans = _spans()
    duplicate = DiscoverySourceToken(
        token_id="TOK-000003",
        source_span_id="SPAN-000003",
        segment_id="SEG-000001",
        start_offset=40,
        end_offset=49,
        exact_text="Secondary",
    )
    broken = (
        spans[0],
        spans[1],
        DiscoverySourceSpan(
            span_id=spans[2].span_id,
            segment_id=spans[2].segment_id,
            start_offset=spans[2].start_offset,
            end_offset=spans[2].end_offset,
            exact_text=spans[2].exact_text,
            source_evidence_ids=spans[2].source_evidence_ids,
            source_tokens=(duplicate, spans[2].source_tokens[1]),
        ),
    )

    with pytest.raises(EngineeringSubjectIntegrityError) as captured:
        validate_subject_discovery_grounding(
            source_spans=broken,
            proposals=(),
        )

    assert not isinstance(
        captured.value,
        EngineeringSubjectGroundingError,
    )


def test_repair_guidance_is_generic_and_validator_driven():
    with pytest.raises(EngineeringSubjectGroundingError) as captured:
        validate_subject_discovery_grounding(
            source_spans=_spans(),
            proposals=_violating_proposals(),
        )

    instructions = (
        build_engineering_subject_grounding_repair_instructions(
            base_instructions="BASE CONTRACT",
            error=captured.value,
        )
    )

    assert ENGINEERING_SUBJECT_GROUNDING_REPAIR_SCHEMA_VERSION == "1.0.0"
    for code in (
        "unknown_source_span",
        "context_only_positive_mention",
        "unknown_token",
        "token_not_in_claimed_span",
        "reversed_token_range",
    ):
        assert code in instructions
    assert (
        "Do not move a mention to an unrelated Evidence span"
        in instructions
    )
    assert "microscope" not in instructions.lower()
    assert "workstation" not in instructions.lower()


class _SequenceClient:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        if not self.outputs:
            raise AssertionError("Unexpected extra LLM request.")
        return LLMResult(
            text=json.dumps(self.outputs.pop(0)),
            provider="openai",
            model=request.model,
            response_id=f"resp-{len(self.requests)}",
            raw_status="completed",
        )


def _projection():
    return SimpleNamespace(
        manifest=SimpleNamespace(
            project_id="396272",
            source_id="SRC-000001",
            source_projection_id="SP-000001",
            projection_fingerprint="a" * 64,
        )
    )


def _invalid_context_only_output():
    return {
        "subjects": [
            {
                "canonical_label": "Unsupported Context Subject",
                "subject_form": "other",
                "identity_status": "resolved",
                "mentions": [
                    {
                        "source_span_id": "SPAN-000001",
                        "start_token_id": "TOK-000001",
                        "end_token_id": "TOK-000002",
                    }
                ],
            }
        ]
    }


def _valid_output():
    return {
        "subjects": [
            {
                "canonical_label": "Primary Behavior",
                "subject_form": "behavior",
                "identity_status": "resolved",
                "mentions": [
                    {
                        "source_span_id": "SPAN-000002",
                        "start_token_id": "TOK-000003",
                        "end_token_id": "TOK-000004",
                    }
                ],
            }
        ]
    }


def _prepare_discovery(monkeypatch, client):
    monkeypatch.setattr(
        discovery_module,
        "build_discovery_source_spans",
        lambda source_projection, source_evidence: _spans(),
    )
    monkeypatch.setattr(
        discovery_module,
        "build_context_preserving_source_input",
        lambda source_projection, spans: "SOURCE CONTEXT",
    )
    return EngineeringSubjectDiscoveryAgent(
        client_factory=lambda provider: client,
    )


def test_discovery_performs_exactly_one_bounded_grounding_repair(
    monkeypatch,
):
    client = _SequenceClient(
        (_invalid_context_only_output(), _valid_output())
    )
    agent = _prepare_discovery(monkeypatch, client)

    result = agent.discover(
        source_projection=_projection(),
        source_evidence=(),
        provider="openai",
        model="gpt-test",
    )

    assert len(client.requests) == 2
    assert (
        client.requests[0].metadata["grounding_correction_retry"]
        is False
    )
    assert (
        client.requests[1].metadata["grounding_correction_retry"]
        is True
    )
    assert (
        client.requests[1].metadata["grounding_repair_schema_version"]
        == ENGINEERING_SUBJECT_GROUNDING_REPAIR_SCHEMA_VERSION
    )
    assert (
        "context_only_positive_mention"
        in client.requests[1].instructions
    )
    assert (
        "PREVIOUS_INVALID_DISCOVERY_OUTPUT"
        in client.requests[1].input_text
    )
    assert tuple(
        item.canonical_label
        for item in result.canonical_subject_set.subjects
    ) == ("Primary Behavior",)


def test_discovery_fails_closed_after_second_grounding_violation(
    monkeypatch,
):
    client = _SequenceClient(
        (
            _invalid_context_only_output(),
            _invalid_context_only_output(),
            _valid_output(),
        )
    )
    agent = _prepare_discovery(monkeypatch, client)

    with pytest.raises(EngineeringSubjectGroundingError):
        agent.discover(
            source_projection=_projection(),
            source_evidence=(),
            provider="openai",
            model="gpt-test",
        )

    assert len(client.requests) == 2


def test_non_repairable_integrity_error_does_not_trigger_llm_retry(
    monkeypatch,
):
    client = _SequenceClient(({"subjects": []}, {"subjects": []}))
    agent = _prepare_discovery(monkeypatch, client)

    def fail_internal_integrity(**kwargs):
        raise EngineeringSubjectIntegrityError(
            "System-owned grounding map is inconsistent."
        )

    monkeypatch.setattr(
        discovery_module,
        "materialize_canonical_subject_set",
        fail_internal_integrity,
    )

    with pytest.raises(EngineeringSubjectIntegrityError):
        agent.discover(
            source_projection=_projection(),
            source_evidence=(),
            provider="openai",
            model="gpt-test",
        )

    assert len(client.requests) == 1
