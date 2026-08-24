"""Immutable Subject-centric Human Review contracts."""

from __future__ import annotations

from dataclasses import dataclass


SUBJECT_REVIEW_SCHEMA_VERSION = "1.0.0"
SUBJECT_REVIEW_DECISION_SCHEMA_VERSION = "1.0.0"

SUBJECT_REVIEW_OUTCOMES = frozenset(
    {
        "accepted",
        "accepted_with_modification",
        "rejected",
    }
)
RELATIONSHIP_REVIEW_OUTCOMES = frozenset(
    {
        "accepted",
        "rejected",
        "deferred",
    }
)


@dataclass(frozen=True, slots=True)
class SubjectReviewMention:
    mention_id: str
    exact_text: str
    source_evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SubjectReviewValueDistribution:
    value: str
    supporting_personas: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SubjectReviewField:
    field_name: str
    selected_value: str | None
    consensus_level: str
    confidence: str
    value_distribution: tuple[SubjectReviewValueDistribution, ...]
    supporting_personas: tuple[str, ...]
    dissenting_personas: tuple[str, ...]
    unstable_personas: tuple[str, ...]
    review_attention_required: bool


@dataclass(frozen=True, slots=True)
class SubjectReviewPersonaInterpretation:
    persona_id: str
    interpreted_statements: tuple[str, ...]
    information_types: tuple[str, ...]
    statement_modalities: tuple[str, ...]
    epistemic_classes: tuple[str, ...]
    uncertainties: tuple[str, ...]
    missing_evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SubjectReviewRelationship:
    source_subject_id: str
    relationship_kind: str
    target_subject_id: str
    direction: str
    other_subject_id: str
    consensus_level: str
    confidence: str
    supporting_personas: tuple[str, ...]
    omitting_personas: tuple[str, ...]
    unstable_personas: tuple[str, ...]
    statement_variants: tuple[tuple[str, tuple[str, ...]], ...]
    review_attention_required: bool


@dataclass(frozen=True, slots=True)
class SubjectReviewCard:
    canonical_subject_id: str
    canonical_label: str
    mentions: tuple[SubjectReviewMention, ...]
    information_type: SubjectReviewField
    statement_modality: SubjectReviewField
    epistemic_class: SubjectReviewField
    persona_interpretations: tuple[SubjectReviewPersonaInterpretation, ...]
    relationships: tuple[SubjectReviewRelationship, ...]
    classification_review_attention_required: bool
    relationship_review_attention_required: bool
    review_attention_required: bool
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class SubjectReviewBundle:
    schema_version: str
    project_id: str
    source_id: str
    source_projection_id: str
    canonical_subject_ids: tuple[str, ...]
    cards: tuple[SubjectReviewCard, ...]
    human_review_required: bool
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class RelationshipReviewDecision:
    source_subject_id: str
    relationship_kind: str
    target_subject_id: str
    outcome: str
    rationale: str | None


@dataclass(frozen=True, slots=True)
class SubjectReviewDecision:
    schema_version: str
    canonical_subject_id: str
    expected_review_card_fingerprint: str
    outcome: str
    reviewed_statement: str | None
    information_type: str | None
    statement_modality: str | None
    epistemic_class: str | None
    relationship_decisions: tuple[RelationshipReviewDecision, ...]
    rationale: str | None
    reviewer_identity: str
    content_fingerprint: str
