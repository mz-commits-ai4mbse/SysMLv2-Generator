"""Read-only candidate projection for Human Review relationship resolution."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import unicodedata

from .errors import ReviewIntegrityError, ReviewValidationError
from .p9_proposal_adapter import P9ReviewQuestionProposal
from .types import ReviewItem


_RELATIONSHIP_REQUIRED_FIELDS = frozenset(
    {
        "link_id",
        "source_element_candidate",
        "link_type",
        "target_element_candidate",
        "source_statement",
    }
)


@dataclass(frozen=True, slots=True)
class ReviewResolutionCandidateCard:
    """One exact existing Review element that can be chosen by a Human."""

    review_item_id: str
    stable_subject_key: str
    title: str
    information_type: str | None
    primary_text: str
    effective_review_outcome: str
    source_evidence_count: int
    proposal_count: int


@dataclass(frozen=True, slots=True)
class RelationshipResolutionCandidateProjection:
    """Read-only resolution choices for one unresolved relationship question."""

    question_id: str
    question_stable_subject_key: str
    source_endpoint: str
    target_endpoint: str
    semantic_intent: str
    source_statement: str
    source_candidates: tuple[ReviewResolutionCandidateCard, ...]
    target_candidates: tuple[ReviewResolutionCandidateCard, ...]


def project_relationship_resolution_candidates(
    question: object,
    review_items: object,
) -> RelationshipResolutionCandidateProjection:
    """Project exact-name element cards without creating engineering authority."""

    if not isinstance(question, P9ReviewQuestionProposal):
        raise ReviewValidationError(
            "question must be a P9ReviewQuestionProposal."
        )

    if question.issue_code != "unresolved_relationship_endpoint":
        raise ReviewValidationError(
            "Only unresolved relationship endpoint questions are supported."
        )

    items = _validated_review_items(review_items)
    raw_link = _parse_raw_relationship(question.raw_fragment_json)

    source_endpoint = _required_text(
        raw_link["source_element_candidate"],
        "source_element_candidate",
    )
    target_endpoint = _required_text(
        raw_link["target_element_candidate"],
        "target_element_candidate",
    )
    semantic_intent = _required_text(raw_link["link_type"], "link_type")
    source_statement = _required_text(
        raw_link["source_statement"],
        "source_statement",
    )

    return RelationshipResolutionCandidateProjection(
        question_id=question.question_id,
        question_stable_subject_key=question.stable_subject_key,
        source_endpoint=source_endpoint,
        target_endpoint=target_endpoint,
        semantic_intent=semantic_intent,
        source_statement=source_statement,
        source_candidates=_cards_for_endpoint(source_endpoint, items),
        target_candidates=_cards_for_endpoint(target_endpoint, items),
    )


def _cards_for_endpoint(
    endpoint: str,
    review_items: tuple[ReviewItem, ...],
) -> tuple[ReviewResolutionCandidateCard, ...]:
    normalized_endpoint = _normalize_exact_text(endpoint)

    cards = []
    for item in review_items:
        if item.review_item_kind != "element":
            continue
        if item.effective_review_outcome in {"rejected", "out_of_scope"}:
            continue
        if (
            _normalize_exact_text(item.current_content.title)
            != normalized_endpoint
        ):
            continue

        cards.append(
            ReviewResolutionCandidateCard(
                review_item_id=item.review_item_id,
                stable_subject_key=item.stable_subject_key,
                title=item.current_content.title,
                information_type=item.current_content.information_type,
                primary_text=item.current_content.primary_text,
                effective_review_outcome=item.effective_review_outcome,
                source_evidence_count=len(item.source_evidence_references),
                proposal_count=len(item.proposal_references),
            )
        )

    return tuple(
        sorted(
            cards,
            key=lambda card: (
                card.title.casefold(),
                card.information_type or "",
                card.stable_subject_key,
                card.review_item_id,
            ),
        )
    )


def _validated_review_items(value: object) -> tuple[ReviewItem, ...]:
    if not isinstance(value, tuple):
        raise ReviewValidationError("review_items must be a tuple.")

    for item in value:
        if not isinstance(item, ReviewItem):
            raise ReviewValidationError(
                "review_items must contain ReviewItem values."
            )

    stable_keys = [item.stable_subject_key for item in value]
    if len(stable_keys) != len(set(stable_keys)):
        raise ReviewIntegrityError(
            "Review Items must have unique stable subject keys."
        )

    return value


def _parse_raw_relationship(text: object) -> dict[str, object]:
    if not isinstance(text, str) or not text.strip():
        raise ReviewValidationError(
            "raw_fragment_json must be non-empty JSON text."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except ReviewValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ReviewValidationError(
            "raw_fragment_json is not valid JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise ReviewValidationError(
            "raw relationship fragment must be a JSON object."
        )

    missing = _RELATIONSHIP_REQUIRED_FIELDS - set(payload)
    if missing:
        raise ReviewValidationError(
            "raw relationship fragment is missing fields: "
            f"{sorted(missing)!r}."
        )

    return payload


def _object_without_duplicate_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ReviewValidationError(
                "raw relationship fragment contains duplicate JSON keys."
            )
        result[key] = value
    return result


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewValidationError(f"{label} must be non-empty text.")
    return value.strip()


def _normalize_exact_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.casefold()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()
