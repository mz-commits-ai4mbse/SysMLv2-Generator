"""Deterministic semantic field consistency contract."""

from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Mapping

from modules.semantic_extraction import EPISTEMIC_CLASSES

from .errors import (
    SemanticConsistencyAlignmentIntegrityError,
    SemanticConsistencyAlignmentValidationError,
)
from .types import (
    SemanticConsistencyDecision,
    SemanticConsistencyNeed,
)


PRE_REVIEW_EPISTEMIC_CLASSES = frozenset(
    value
    for value in EPISTEMIC_CLASSES
    if value != "derivation"
)

_JSON_FENCE = re.compile(
    r"^\s*```(?:json)?\s*(.*?)\s*```\s*$",
    re.S | re.I,
)

_DECISION_FIELDS = frozenset(
    {
        "item_id",
        "normalized_epistemic_class",
        "normalized_missing_evidence",
        "rationale",
    }
)


def pair_is_consistent(
    epistemic_class: Any,
    missing_evidence: Any,
) -> bool:
    if epistemic_class not in PRE_REVIEW_EPISTEMIC_CLASSES:
        return False
    if epistemic_class == "assumption":
        return (
            isinstance(missing_evidence, str)
            and bool(missing_evidence.strip())
            and missing_evidence == missing_evidence.strip()
        )
    return missing_evidence is None


def find_semantic_consistency_needs(
    text: str,
    *,
    item_id_field: str,
    allowed_item_ids,
    context_by_item_id: Mapping[str, str] | None = None,
) -> tuple[SemanticConsistencyNeed, ...]:
    """Find only coupled-field inconsistencies that are safe to align."""

    payload = _decode_object(text)
    if payload is None:
        return ()

    values = payload.get("interpretations")
    if not isinstance(values, list):
        return ()

    allowed_ids = frozenset(allowed_item_ids)
    context = context_by_item_id or {}
    needs = []

    for item in values:
        if not isinstance(item, dict):
            continue

        item_id = item.get(item_id_field)
        if not isinstance(item_id, str) or item_id not in allowed_ids:
            continue

        epistemic = item.get("epistemic_class")
        if epistemic not in PRE_REVIEW_EPISTEMIC_CLASSES:
            # Classification alignment owns out-of-vocabulary epistemic values.
            continue

        missing = item.get("missing_evidence")
        if pair_is_consistent(epistemic, missing):
            continue

        statement = item.get("interpreted_statement")
        if not isinstance(statement, str):
            statement = "<unavailable>"

        needs.append(
            SemanticConsistencyNeed(
                item_id=item_id,
                interpreted_statement=statement,
                raw_epistemic_class=epistemic,
                raw_missing_evidence=missing,
                context=context.get(item_id),
            )
        )

    return tuple(sorted(needs, key=lambda item: item.item_id))


def parse_semantic_consistency_response(
    text: str,
    *,
    needs: tuple[SemanticConsistencyNeed, ...],
    mapper_response_id: str | None,
) -> tuple[SemanticConsistencyDecision, ...]:
    payload = _require_object(
        text,
        "Semantic consistency alignment output",
    )
    if frozenset(payload) != {"resolutions"}:
        raise SemanticConsistencyAlignmentValidationError(
            "Semantic consistency output must contain only 'resolutions'."
        )

    raw_values = payload["resolutions"]
    if not isinstance(raw_values, list):
        raise SemanticConsistencyAlignmentValidationError(
            "resolutions must be an array."
        )

    expected = {need.item_id: need for need in needs}
    decisions = {}

    for raw in raw_values:
        if not isinstance(raw, dict) or frozenset(raw) != _DECISION_FIELDS:
            raise SemanticConsistencyAlignmentValidationError(
                "Semantic consistency resolution fields do not match schema."
            )

        item_id = raw["item_id"]
        if item_id not in expected or item_id in decisions:
            raise SemanticConsistencyAlignmentValidationError(
                "Semantic consistency target set is invalid."
            )

        epistemic = raw["normalized_epistemic_class"]
        missing = raw["normalized_missing_evidence"]
        rationale = raw["rationale"]

        if not pair_is_consistent(epistemic, missing):
            raise SemanticConsistencyAlignmentValidationError(
                "Normalized epistemic/missing-evidence pair is inconsistent."
            )

        if not isinstance(rationale, str) or not rationale.strip():
            raise SemanticConsistencyAlignmentValidationError(
                "rationale is required."
            )

        need = expected[item_id]
        decisions[item_id] = _decision(
            need,
            normalized_epistemic_class=epistemic,
            normalized_missing_evidence=missing,
            rationale=rationale.strip(),
            mapper_response_id=mapper_response_id,
        )

    if set(decisions) != set(expected):
        raise SemanticConsistencyAlignmentValidationError(
            "Semantic consistency alignment did not cover the exact requested set."
        )

    return tuple(decisions[item_id] for item_id in sorted(decisions))


def apply_semantic_consistency_alignment(
    text: str,
    *,
    item_id_field: str,
    decisions: tuple[SemanticConsistencyDecision, ...],
) -> str:
    if not decisions:
        return text

    payload = _require_object(text, "Original interpretation output")
    values = payload.get("interpretations")
    if not isinstance(values, list):
        raise SemanticConsistencyAlignmentValidationError(
            "Original interpretations must be an array."
        )

    by_id = {item.item_id: item for item in decisions}
    if len(by_id) != len(decisions):
        raise SemanticConsistencyAlignmentValidationError(
            "Semantic consistency decisions must be unique."
        )

    applied = set()

    for item in values:
        if not isinstance(item, dict):
            continue

        item_id = item.get(item_id_field)
        decision = by_id.get(item_id)
        if decision is None:
            continue

        if (
            item.get("epistemic_class")
            != decision.raw_epistemic_class
            or item.get("missing_evidence")
            != decision.raw_missing_evidence
        ):
            raise SemanticConsistencyAlignmentIntegrityError(
                "Raw semantic pair changed before consistency alignment."
            )

        item["epistemic_class"] = (
            decision.normalized_epistemic_class
        )
        item["missing_evidence"] = (
            decision.normalized_missing_evidence
        )
        applied.add(item_id)

    if applied != set(by_id):
        raise SemanticConsistencyAlignmentIntegrityError(
            "Could not locate every semantic consistency target."
        )

    return json.dumps(payload, ensure_ascii=False)


def _decision(
    need: SemanticConsistencyNeed,
    *,
    normalized_epistemic_class: str,
    normalized_missing_evidence: str | None,
    rationale: str,
    mapper_response_id: str | None,
) -> SemanticConsistencyDecision:
    body = {
        "item_id": need.item_id,
        "raw_epistemic_class": need.raw_epistemic_class,
        "raw_missing_evidence": need.raw_missing_evidence,
        "normalized_epistemic_class": normalized_epistemic_class,
        "normalized_missing_evidence": normalized_missing_evidence,
        "rationale": rationale,
        "mapper_response_id": mapper_response_id,
    }
    return SemanticConsistencyDecision(
        **body,
        content_fingerprint=_sha(body),
    )


def _decode_object(text: str):
    if not isinstance(text, str) or not text.strip():
        return None
    match = _JSON_FENCE.fullmatch(text)
    normalized = match.group(1) if match else text.strip()
    try:
        value = json.loads(normalized)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _require_object(text: str, label: str):
    value = _decode_object(text)
    if value is None:
        raise SemanticConsistencyAlignmentValidationError(
            f"{label} must be JSON object text."
        )
    return value


def _sha(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
