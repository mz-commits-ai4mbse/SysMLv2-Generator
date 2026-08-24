"""R4c.5a.1 tests for separate Subject-vs-relationship review attention."""

from modules.subject_review.types import (
    SubjectReviewCard,
    SubjectReviewField,
)


def _field(name, *, attention=False):
    return SubjectReviewField(
        field_name=name,
        selected_value="actor",
        consensus_level="unanimous" if not attention else "majority",
        confidence="high" if not attention else "medium",
        value_distribution=(),
        supporting_personas=("P1", "P2", "P3"),
        dissenting_personas=(),
        unstable_personas=(),
        review_attention_required=attention,
    )


def test_review_card_exposes_separate_attention_dimensions():
    card = SubjectReviewCard(
        canonical_subject_id="SUBJ-000001",
        canonical_label="Role",
        mentions=(),
        information_type=_field("information_type"),
        statement_modality=_field("statement_modality"),
        epistemic_class=_field("epistemic_class"),
        persona_interpretations=(),
        relationships=(),
        classification_review_attention_required=False,
        relationship_review_attention_required=True,
        review_attention_required=True,
        content_fingerprint="a" * 64,
    )

    assert card.classification_review_attention_required is False
    assert card.relationship_review_attention_required is True
    assert card.review_attention_required is True
