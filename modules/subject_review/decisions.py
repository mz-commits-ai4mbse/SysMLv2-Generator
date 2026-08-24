"""Human decision contract for one immutable Subject Review card."""

from __future__ import annotations

from hashlib import sha256
import json

from modules.semantic_extraction import (
    EPISTEMIC_CLASSES,
    INFORMATION_TYPES,
    STATEMENT_MODALITIES,
)

from .errors import SubjectReviewDecisionError
from .types import (
    RELATIONSHIP_REVIEW_OUTCOMES,
    SUBJECT_REVIEW_DECISION_SCHEMA_VERSION,
    SUBJECT_REVIEW_OUTCOMES,
    RelationshipReviewDecision,
    SubjectReviewCard,
    SubjectReviewDecision,
)


def create_subject_review_decision(
    *,
    card: SubjectReviewCard,
    outcome: str,
    reviewer_identity: str,
    reviewed_statement: str | None = None,
    information_type: str | None = None,
    statement_modality: str | None = None,
    epistemic_class: str | None = None,
    relationship_decisions=(),
    rationale: str | None = None,
) -> SubjectReviewDecision:
    """Create a decision bound to the exact immutable review-card fingerprint."""

    if not isinstance(card, SubjectReviewCard):
        raise SubjectReviewDecisionError("card must be a SubjectReviewCard.")
    if outcome not in SUBJECT_REVIEW_OUTCOMES:
        raise SubjectReviewDecisionError("outcome is not allowed.")

    reviewer_identity = _required_text(reviewer_identity, "reviewer_identity")
    rationale = _optional_text(rationale, "rationale")

    relation_decisions = tuple(relationship_decisions)
    _validate_relationship_decisions(card, relation_decisions)

    if outcome == "rejected":
        if rationale is None:
            raise SubjectReviewDecisionError("Rejected Subject requires a rationale.")
        if any(
            value is not None
            for value in (
                reviewed_statement,
                information_type,
                statement_modality,
                epistemic_class,
            )
        ):
            raise SubjectReviewDecisionError(
                "Rejected Subject must not carry approved engineering fields."
            )
    else:
        reviewed_statement = _required_text(reviewed_statement, "reviewed_statement")
        if information_type not in INFORMATION_TYPES:
            raise SubjectReviewDecisionError("information_type is not allowed.")
        if statement_modality not in STATEMENT_MODALITIES:
            raise SubjectReviewDecisionError("statement_modality is not allowed.")
        if epistemic_class not in EPISTEMIC_CLASSES:
            raise SubjectReviewDecisionError("epistemic_class is not allowed.")
        if outcome == "accepted_with_modification" and rationale is None:
            raise SubjectReviewDecisionError(
                "Accepted-with-modification requires a rationale."
            )

    body = {
        "schema_version": SUBJECT_REVIEW_DECISION_SCHEMA_VERSION,
        "canonical_subject_id": card.canonical_subject_id,
        "expected_review_card_fingerprint": card.content_fingerprint,
        "outcome": outcome,
        "reviewed_statement": reviewed_statement,
        "information_type": information_type,
        "statement_modality": statement_modality,
        "epistemic_class": epistemic_class,
        "relationship_decisions": [
            {
                "source_subject_id": item.source_subject_id,
                "relationship_kind": item.relationship_kind,
                "target_subject_id": item.target_subject_id,
                "outcome": item.outcome,
                "rationale": item.rationale,
            }
            for item in relation_decisions
        ],
        "rationale": rationale,
        "reviewer_identity": reviewer_identity,
    }

    return SubjectReviewDecision(
        schema_version=SUBJECT_REVIEW_DECISION_SCHEMA_VERSION,
        canonical_subject_id=card.canonical_subject_id,
        expected_review_card_fingerprint=card.content_fingerprint,
        outcome=outcome,
        reviewed_statement=reviewed_statement,
        information_type=information_type,
        statement_modality=statement_modality,
        epistemic_class=epistemic_class,
        relationship_decisions=relation_decisions,
        rationale=rationale,
        reviewer_identity=reviewer_identity,
        content_fingerprint=_canonical_sha256(body),
    )


def create_relationship_review_decision(
    *,
    source_subject_id: str,
    relationship_kind: str,
    target_subject_id: str,
    outcome: str,
    rationale: str | None = None,
) -> RelationshipReviewDecision:
    if outcome not in RELATIONSHIP_REVIEW_OUTCOMES:
        raise SubjectReviewDecisionError("relationship outcome is not allowed.")
    if not all(
        isinstance(value, str) and value.strip()
        for value in (source_subject_id, relationship_kind, target_subject_id)
    ):
        raise SubjectReviewDecisionError("relationship key fields must be non-empty text.")
    rationale = _optional_text(rationale, "relationship rationale")
    if outcome == "rejected" and rationale is None:
        raise SubjectReviewDecisionError("Rejected relationship requires a rationale.")
    return RelationshipReviewDecision(
        source_subject_id=source_subject_id,
        relationship_kind=relationship_kind,
        target_subject_id=target_subject_id,
        outcome=outcome,
        rationale=rationale,
    )


def _validate_relationship_decisions(card, decisions):
    available = {
        (
            item.source_subject_id,
            item.relationship_kind,
            item.target_subject_id,
        )
        for item in card.relationships
    }
    seen = set()
    for decision in decisions:
        if not isinstance(decision, RelationshipReviewDecision):
            raise SubjectReviewDecisionError(
                "relationship_decisions must contain RelationshipReviewDecision values."
            )
        key = (
            decision.source_subject_id,
            decision.relationship_kind,
            decision.target_subject_id,
        )
        if key not in available:
            raise SubjectReviewDecisionError(
                "Relationship decision is not bound to a relationship visible on this Review card."
            )
        if key in seen:
            raise SubjectReviewDecisionError("Relationship decision keys must be unique.")
        seen.add(key)


def _required_text(value, field_name):
    if not isinstance(value, str) or not value.strip():
        raise SubjectReviewDecisionError(f"{field_name} must be non-empty text.")
    return value.strip()


def _optional_text(value, field_name):
    if value is None:
        return None
    if not isinstance(value, str):
        raise SubjectReviewDecisionError(f"{field_name} must be text or null.")
    value = value.strip()
    return value or None


def _canonical_sha256(value) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
