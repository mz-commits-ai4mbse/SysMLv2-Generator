"""Immutable contracts for pre-persona canonical engineering subjects."""

from __future__ import annotations

from dataclasses import dataclass


CANONICAL_SUBJECT_SET_SCHEMA_VERSION = "1.0.0"
SUBJECT_FORMS = frozenset(
    {
        "entity",
        "behavior",
        "assertion",
        "question",
        "information",
        "condition",
        "other",
    }
)
IDENTITY_STATUSES = frozenset({"resolved", "uncertain"})


@dataclass(frozen=True, slots=True)
class DiscoverySourceToken:
    """One system-owned exact token address inside a discovery Source Span."""

    token_id: str
    source_span_id: str
    segment_id: str
    start_offset: int
    end_offset: int
    exact_text: str


@dataclass(frozen=True, slots=True)
class DiscoverySourceSpan:
    """One deterministic source span used for LLM context and grounding."""

    span_id: str
    segment_id: str
    start_offset: int
    end_offset: int
    exact_text: str
    source_evidence_ids: tuple[str, ...]
    source_tokens: tuple[DiscoverySourceToken, ...]


@dataclass(frozen=True, slots=True)
class EngineeringMention:
    """One exact source occurrence bound to a canonical engineering subject."""

    mention_id: str
    source_span_id: str
    segment_id: str
    start_offset: int
    end_offset: int
    exact_text: str
    source_evidence_ids: tuple[str, ...]
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class CanonicalEngineeringSubject:
    """One shared pre-persona subject identity with one or more mentions."""

    canonical_subject_id: str
    canonical_label: str
    subject_form: str
    identity_status: str
    mention_ids: tuple[str, ...]
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class CanonicalSubjectSet:
    """One complete shared subject population for later Persona interpretation."""

    schema_version: str
    project_id: str
    source_id: str
    source_projection_id: str
    source_projection_fingerprint: str
    mentions: tuple[EngineeringMention, ...]
    subjects: tuple[CanonicalEngineeringSubject, ...]
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class DiscoveryMentionProposal:
    """One LLM-selected system-owned token range before materialization."""

    source_span_id: str
    start_token_id: str
    end_token_id: str


@dataclass(frozen=True, slots=True)
class DiscoverySubjectProposal:
    """One LLM-proposed canonical grouping before stable IDs are assigned."""

    canonical_label: str
    subject_form: str
    identity_status: str
    mentions: tuple[DiscoveryMentionProposal, ...]


@dataclass(frozen=True, slots=True)
class EngineeringSubjectDiscoveryResult:
    """One LLM discovery response plus the system-owned canonical population."""

    source_spans: tuple[DiscoverySourceSpan, ...]
    canonical_subject_set: CanonicalSubjectSet
    provider: str
    model: str
    response_id: str | None
