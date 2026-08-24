"""Governance checks for R4c Subject relationship decisions."""

from __future__ import annotations

from hashlib import sha256
import json


_ACCEPTED_SUBJECT_OUTCOMES = frozenset(
    {
        "accepted_as_generated",
        "accepted_with_modification",
        "combined",
    }
)


def subject_relationship_finalization_issue_codes(
    *,
    subject_review_payload: dict,
    review_items,
    relationship_decisions,
) -> tuple[str, ...]:
    """Return deterministic finalization blockers for Subject relationships."""

    cards = _cards(subject_review_payload)
    items_by_subject = {}
    for item in review_items:
        subject_id = _subject_id_from_locator(
            getattr(item, "original_report_locator", None)
        )
        if subject_id is not None:
            items_by_subject[subject_id] = item

    required = set()
    card_fingerprints = {}
    for subject_id, card in cards.items():
        card_fingerprints[subject_id] = card["content_fingerprint"]
        for relation in card.get("relationships", ()):
            if relation.get("direction") != "outgoing":
                continue
            key = (
                relation.get("source_subject_id"),
                relation.get("relationship_kind"),
                relation.get("target_subject_id"),
            )
            if not all(isinstance(value, str) and value for value in key):
                raise ValueError(
                    "Outgoing Subject relationship key is invalid."
                )
            if key[0] != subject_id:
                raise ValueError(
                    "Outgoing Subject relationship is owned by wrong card."
                )
            required.add(key)

    latest = {}
    for decision in relationship_decisions:
        key = (
            decision.source_subject_id,
            decision.relationship_kind,
            decision.target_subject_id,
        )
        if key not in required:
            raise ValueError(
                "Persisted relationship decision is not part of current "
                "Subject Review authority."
            )
        expected_card_fingerprint = card_fingerprints[key[0]]
        if (
            decision.subject_review_card_fingerprint
            != expected_card_fingerprint
        ):
            raise ValueError(
                "Persisted relationship decision is bound to a stale "
                "Subject Review Card."
            )
        latest[key] = decision

    issues = []
    for key in sorted(required):
        decision = latest.get(key)
        if decision is None:
            issues.append(
                "subject_relationship_decision_missing:"
                + _key_digest(key)
            )
            continue

        if decision.outcome == "accepted":
            source_item = items_by_subject.get(key[0])
            target_item = items_by_subject.get(key[2])
            if (
                source_item is None
                or target_item is None
                or source_item.effective_review_outcome
                not in _ACCEPTED_SUBJECT_OUTCOMES
                or target_item.effective_review_outcome
                not in _ACCEPTED_SUBJECT_OUTCOMES
            ):
                issues.append(
                    "subject_relationship_endpoint_not_approved:"
                    + _key_digest(key)
                )

    return tuple(sorted(set(issues)))


def relationship_decision_authority_fingerprint(
    relationship_decisions,
) -> str:
    """Fingerprint the latest effective directed relationship decisions."""

    payload = [
        {
            "decision_id": item.decision_id,
            "predecessor_decision_id": item.predecessor_decision_id,
            "subject_review_card_fingerprint": (
                item.subject_review_card_fingerprint
            ),
            "source_subject_id": item.source_subject_id,
            "relationship_kind": item.relationship_kind,
            "target_subject_id": item.target_subject_id,
            "outcome": item.outcome,
            "rationale": item.rationale,
            "content_fingerprint": item.content_fingerprint,
        }
        for item in sorted(
            relationship_decisions,
            key=lambda value: (
                value.source_subject_id,
                value.relationship_kind,
                value.target_subject_id,
            ),
        )
    ]
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _cards(payload: dict) -> dict[str, dict]:
    if not isinstance(payload, dict):
        raise ValueError("Subject Review payload must be a dictionary.")
    cards = payload.get("cards")
    subject_ids = payload.get("canonical_subject_ids")
    if not isinstance(cards, list) or not isinstance(subject_ids, list):
        raise ValueError("Subject Review payload is incomplete.")

    result = {}
    for card in cards:
        if not isinstance(card, dict):
            raise ValueError("Subject Review card must be a dictionary.")
        subject_id = card.get("canonical_subject_id")
        if not isinstance(subject_id, str) or not subject_id:
            raise ValueError("Subject Review card lacks canonical identity.")
        if subject_id in result:
            raise ValueError("Duplicate canonical Subject Review card.")
        result[subject_id] = card

    if tuple(result) != tuple(subject_ids):
        raise ValueError(
            "Subject Review card population differs from canonical authority."
        )
    return result


def _subject_id_from_locator(locator) -> str | None:
    prefix = "subject_review:"
    if not isinstance(locator, str) or not locator.startswith(prefix):
        return None
    value = locator[len(prefix):]
    return value if value.startswith("SUBJ-") else None


def _key_digest(key: tuple[str, str, str]) -> str:
    canonical = json.dumps(
        list(key),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()[:16]
