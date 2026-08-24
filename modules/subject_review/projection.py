"""Build one content-first Human Review card per canonical engineering Subject."""

from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import json

from modules.engineering_subjects.types import CanonicalSubjectSet
from modules.subject_consensus.types import SharedSubjectConsensusResult
from modules.subject_interpretation.types import SharedSubjectInterpretationResult

from .errors import SubjectReviewConfigurationError, SubjectReviewIntegrityError
from .types import (
    SUBJECT_REVIEW_SCHEMA_VERSION,
    SubjectReviewBundle,
    SubjectReviewCard,
    SubjectReviewField,
    SubjectReviewMention,
    SubjectReviewPersonaInterpretation,
    SubjectReviewRelationship,
    SubjectReviewValueDistribution,
)


def build_subject_review_bundle(
    *,
    subject_set: CanonicalSubjectSet,
    interpretations: SharedSubjectInterpretationResult,
    consensus: SharedSubjectConsensusResult,
) -> SubjectReviewBundle:
    """Project exact R4c.1-R4c.4 outputs into one card per fixed SUBJ-* identity."""

    _validate_inputs(subject_set, interpretations, consensus)

    mention_by_id = {mention.mention_id: mention for mention in subject_set.mentions}
    consensus_by_id = {
        outcome.canonical_subject_id: outcome
        for outcome in consensus.subject_outcomes
    }

    runs_by_persona = defaultdict(list)
    for run in interpretations.run_results:
        runs_by_persona[run.persona_id].append(run)

    relationships_by_subject = defaultdict(list)
    for relation in consensus.relationship_outcomes:
        relationships_by_subject[relation.source_subject_id].append(("outgoing", relation))
        relationships_by_subject[relation.target_subject_id].append(("incoming", relation))

    cards = []
    for subject in subject_set.subjects:
        subject_id = subject.canonical_subject_id
        outcome = consensus_by_id[subject_id]

        mentions = tuple(
            SubjectReviewMention(
                mention_id=mention_by_id[mention_id].mention_id,
                exact_text=mention_by_id[mention_id].exact_text,
                source_evidence_ids=mention_by_id[mention_id].source_evidence_ids,
            )
            for mention_id in subject.mention_ids
        )

        persona_views = tuple(
            _persona_view(
                persona_id,
                tuple(sorted(runs_by_persona[persona_id], key=lambda run: run.persona_run_index)),
                subject_id,
            )
            for persona_id in interpretations.required_personas
        )

        relation_views = tuple(
            _relationship_view(direction, relation, subject_id)
            for direction, relation in sorted(
                relationships_by_subject.get(subject_id, ()),
                key=lambda item: (
                    item[0],
                    item[1].source_subject_id,
                    item[1].relationship_kind,
                    item[1].target_subject_id,
                ),
            )
        )

        fields = (
            _field_view(outcome.information_type),
            _field_view(outcome.statement_modality),
            _field_view(outcome.epistemic_class),
        )

        classification_attention = outcome.review_attention_required
        relationship_attention = any(
            relation.review_attention_required
            for relation in relation_views
        )
        aggregate_attention = (
            classification_attention
            or relationship_attention
        )

        card_body = {
            "canonical_subject_id": subject_id,
            "canonical_label": subject.canonical_label,
            "mentions": [
                {
                    "mention_id": item.mention_id,
                    "exact_text": item.exact_text,
                    "source_evidence_ids": list(item.source_evidence_ids),
                }
                for item in mentions
            ],
            "fields": [_field_dict(item) for item in fields],
            "persona_interpretations": [
                _persona_dict(item)
                for item in persona_views
            ],
            "relationships": [
                _relationship_dict(item)
                for item in relation_views
            ],
            "classification_review_attention_required": (
                classification_attention
            ),
            "relationship_review_attention_required": (
                relationship_attention
            ),
            "review_attention_required": aggregate_attention,
        }

        cards.append(
            SubjectReviewCard(
                canonical_subject_id=subject_id,
                canonical_label=subject.canonical_label,
                mentions=mentions,
                information_type=fields[0],
                statement_modality=fields[1],
                epistemic_class=fields[2],
                persona_interpretations=persona_views,
                relationships=relation_views,
                classification_review_attention_required=(
                    classification_attention
                ),
                relationship_review_attention_required=(
                    relationship_attention
                ),
                review_attention_required=aggregate_attention,
                content_fingerprint=_canonical_sha256(card_body),
            )
        )

    bundle_body = {
        "schema_version": SUBJECT_REVIEW_SCHEMA_VERSION,
        "project_id": subject_set.project_id,
        "source_id": subject_set.source_id,
        "source_projection_id": subject_set.source_projection_id,
        "canonical_subject_ids": list(interpretations.canonical_subject_ids),
        "card_fingerprints": [card.content_fingerprint for card in cards],
        "human_review_required": True,
    }

    return SubjectReviewBundle(
        schema_version=SUBJECT_REVIEW_SCHEMA_VERSION,
        project_id=subject_set.project_id,
        source_id=subject_set.source_id,
        source_projection_id=subject_set.source_projection_id,
        canonical_subject_ids=interpretations.canonical_subject_ids,
        cards=tuple(cards),
        human_review_required=True,
        content_fingerprint=_canonical_sha256(bundle_body),
    )


def _persona_view(persona_id, runs, subject_id):
    values = []
    for run in runs:
        matches = tuple(
            item
            for item in run.interpretations
            if item.canonical_subject_id == subject_id
        )
        if len(matches) != 1:
            raise SubjectReviewIntegrityError(
                f"Persona {persona_id} does not contain exactly one interpretation for {subject_id}."
            )
        values.append(matches[0])

    return SubjectReviewPersonaInterpretation(
        persona_id=persona_id,
        interpreted_statements=_ordered_unique(item.interpreted_statement for item in values),
        information_types=_ordered_unique(item.information_type for item in values),
        statement_modalities=_ordered_unique(item.statement_modality for item in values),
        epistemic_classes=_ordered_unique(item.epistemic_class for item in values),
        uncertainties=_ordered_unique(
            uncertainty
            for item in values
            for uncertainty in item.uncertainties
        ),
        missing_evidence=_ordered_unique(
            item.missing_evidence
            for item in values
            if item.missing_evidence is not None
        ),
    )


def _field_view(value):
    return SubjectReviewField(
        field_name=value.field_name,
        selected_value=value.selected_value,
        consensus_level=value.consensus_level,
        confidence=value.confidence,
        value_distribution=tuple(
            SubjectReviewValueDistribution(
                value=item.value,
                supporting_personas=item.supporting_personas,
            )
            for item in value.value_distribution
        ),
        supporting_personas=value.supporting_personas,
        dissenting_personas=value.dissenting_personas,
        unstable_personas=value.unstable_personas,
        review_attention_required=value.review_attention_required,
    )


def _relationship_view(direction, value, current_subject_id):
    other = (
        value.target_subject_id
        if direction == "outgoing"
        else value.source_subject_id
    )
    return SubjectReviewRelationship(
        source_subject_id=value.source_subject_id,
        relationship_kind=value.relationship_kind,
        target_subject_id=value.target_subject_id,
        direction=direction,
        other_subject_id=other,
        consensus_level=value.consensus_level,
        confidence=value.confidence,
        supporting_personas=value.supporting_personas,
        omitting_personas=value.omitting_personas,
        unstable_personas=value.unstable_personas,
        statement_variants=tuple(
            (variant.persona_id, variant.statements)
            for variant in value.statement_variants
        ),
        review_attention_required=value.review_attention_required,
    )


def _validate_inputs(subject_set, interpretations, consensus):
    if not isinstance(subject_set, CanonicalSubjectSet):
        raise SubjectReviewConfigurationError("subject_set must be CanonicalSubjectSet.")
    if not isinstance(interpretations, SharedSubjectInterpretationResult):
        raise SubjectReviewConfigurationError(
            "interpretations must be SharedSubjectInterpretationResult."
        )
    if not isinstance(consensus, SharedSubjectConsensusResult):
        raise SubjectReviewConfigurationError(
            "consensus must be SharedSubjectConsensusResult."
        )

    context = (
        subject_set.project_id,
        subject_set.source_id,
        subject_set.source_projection_id,
    )
    if context != (
        interpretations.project_id,
        interpretations.source_id,
        interpretations.source_projection_id,
    ) or context != (
        consensus.project_id,
        consensus.source_id,
        consensus.source_projection_id,
    ):
        raise SubjectReviewIntegrityError("Subject Review inputs do not bind the same source context.")

    subject_ids = tuple(subject.canonical_subject_id for subject in subject_set.subjects)
    if subject_ids != interpretations.canonical_subject_ids:
        raise SubjectReviewIntegrityError(
            "Interpretation Subject population does not match CanonicalSubjectSet order."
        )
    if subject_ids != consensus.canonical_subject_ids:
        raise SubjectReviewIntegrityError(
            "Consensus Subject population does not match CanonicalSubjectSet order."
        )
    if tuple(outcome.canonical_subject_id for outcome in consensus.subject_outcomes) != subject_ids:
        raise SubjectReviewIntegrityError(
            "Consensus outcomes must contain exactly one ordered outcome per Subject."
        )


def subject_review_bundle_to_dict(value: SubjectReviewBundle) -> dict:
    return {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "source_id": value.source_id,
        "source_projection_id": value.source_projection_id,
        "canonical_subject_ids": list(value.canonical_subject_ids),
        "cards": [
            {
                "canonical_subject_id": card.canonical_subject_id,
                "canonical_label": card.canonical_label,
                "mentions": [
                    {
                        "mention_id": mention.mention_id,
                        "exact_text": mention.exact_text,
                        "source_evidence_ids": list(mention.source_evidence_ids),
                    }
                    for mention in card.mentions
                ],
                "information_type": _field_dict(card.information_type),
                "statement_modality": _field_dict(card.statement_modality),
                "epistemic_class": _field_dict(card.epistemic_class),
                "persona_interpretations": [
                    _persona_dict(item)
                    for item in card.persona_interpretations
                ],
                "relationships": [
                    _relationship_dict(item)
                    for item in card.relationships
                ],
                "classification_review_attention_required": (
                    card.classification_review_attention_required
                ),
                "relationship_review_attention_required": (
                    card.relationship_review_attention_required
                ),
                "review_attention_required": card.review_attention_required,
                "content_fingerprint": card.content_fingerprint,
            }
            for card in value.cards
        ],
        "human_review_required": value.human_review_required,
        "content_fingerprint": value.content_fingerprint,
    }


def _field_dict(value):
    return {
        "field_name": value.field_name,
        "selected_value": value.selected_value,
        "consensus_level": value.consensus_level,
        "confidence": value.confidence,
        "value_distribution": [
            {
                "value": item.value,
                "supporting_personas": list(item.supporting_personas),
            }
            for item in value.value_distribution
        ],
        "supporting_personas": list(value.supporting_personas),
        "dissenting_personas": list(value.dissenting_personas),
        "unstable_personas": list(value.unstable_personas),
        "review_attention_required": value.review_attention_required,
    }


def _persona_dict(value):
    return {
        "persona_id": value.persona_id,
        "interpreted_statements": list(value.interpreted_statements),
        "information_types": list(value.information_types),
        "statement_modalities": list(value.statement_modalities),
        "epistemic_classes": list(value.epistemic_classes),
        "uncertainties": list(value.uncertainties),
        "missing_evidence": list(value.missing_evidence),
    }


def _relationship_dict(value):
    return {
        "source_subject_id": value.source_subject_id,
        "relationship_kind": value.relationship_kind,
        "target_subject_id": value.target_subject_id,
        "direction": value.direction,
        "other_subject_id": value.other_subject_id,
        "consensus_level": value.consensus_level,
        "confidence": value.confidence,
        "supporting_personas": list(value.supporting_personas),
        "omitting_personas": list(value.omitting_personas),
        "unstable_personas": list(value.unstable_personas),
        "statement_variants": [
            {"persona_id": persona_id, "statements": list(statements)}
            for persona_id, statements in value.statement_variants
        ],
        "review_attention_required": value.review_attention_required,
    }


def _ordered_unique(values):
    return tuple(dict.fromkeys(values))


def _canonical_sha256(value) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
