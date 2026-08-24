"""R4c.5a Human Subject Review decision tests."""

import pytest

from modules.subject_review import (
    SubjectReviewCard,
    SubjectReviewDecisionError,
    SubjectReviewField,
    create_subject_review_decision,
)


def _field(name, selected="actor"):
    return SubjectReviewField(
        field_name=name,
        selected_value=selected,
        consensus_level="unanimous",
        confidence="high",
        value_distribution=(),
        supporting_personas=("P1", "P2"),
        dissenting_personas=(),
        unstable_personas=(),
        review_attention_required=False,
    )


def _card():
    return SubjectReviewCard(
        canonical_subject_id="SUBJ-000001",
        canonical_label="Operator",
        mentions=(),
        information_type=_field("information_type"),
        statement_modality=_field("statement_modality", "descriptive"),
        epistemic_class=_field("epistemic_class", "explicit"),
        persona_interpretations=(),
        relationships=(),
        classification_review_attention_required=False,
        relationship_review_attention_required=False,
        review_attention_required=False,
        content_fingerprint="a" * 64,
    )


def test_accept_requires_explicit_human_reviewed_statement_and_fields():
    with pytest.raises(SubjectReviewDecisionError):
        create_subject_review_decision(
            card=_card(),
            outcome="accepted",
            reviewer_identity="reviewer",
        )

    value = create_subject_review_decision(
        card=_card(),
        outcome="accepted",
        reviewer_identity="reviewer",
        reviewed_statement="The operator is an interacting role.",
        information_type="actor",
        statement_modality="descriptive",
        epistemic_class="explicit",
    )
    assert value.outcome == "accepted"
    assert value.expected_review_card_fingerprint == "a" * 64


def test_modified_and_rejected_decisions_require_rationale():
    with pytest.raises(SubjectReviewDecisionError):
        create_subject_review_decision(
            card=_card(),
            outcome="accepted_with_modification",
            reviewer_identity="reviewer",
            reviewed_statement="Statement.",
            information_type="actor",
            statement_modality="descriptive",
            epistemic_class="explicit",
        )

    with pytest.raises(SubjectReviewDecisionError):
        create_subject_review_decision(
            card=_card(),
            outcome="rejected",
            reviewer_identity="reviewer",
        )


def test_rejected_subject_cannot_carry_approved_fields():
    with pytest.raises(SubjectReviewDecisionError):
        create_subject_review_decision(
            card=_card(),
            outcome="rejected",
            reviewer_identity="reviewer",
            rationale="Not valid engineering information.",
            reviewed_statement="Should not be here.",
        )
