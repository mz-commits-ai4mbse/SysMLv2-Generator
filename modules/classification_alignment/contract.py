"""Deterministic controlled-classification alignment contract."""

from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Mapping

from modules.semantic_extraction import (
    EPISTEMIC_CLASSES,
    INFORMATION_TYPES,
    STATEMENT_MODALITIES,
)

from .errors import (
    ClassificationAlignmentIntegrityError,
    ClassificationAlignmentValidationError,
)
from .types import ClassificationAlignmentDecision, ClassificationAlignmentNeed


CONTROLLED_CLASSIFICATION_VALUES = {
    "information_type": frozenset(INFORMATION_TYPES),
    "statement_modality": frozenset(STATEMENT_MODALITIES),
    "epistemic_class": frozenset(
        value for value in EPISTEMIC_CLASSES if value != "derivation"
    ),
}
NEUTRAL_CLASSIFICATION_FALLBACKS = {"information_type": "unclassified"}
_JSON_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.S | re.I)
_ALIGNMENT_FIELDS = frozenset(
    {"item_id", "field_name", "normalized_value", "mapping_status", "rationale"}
)


def find_classification_alignment_needs(
    text: str,
    *,
    item_id_field: str,
    allowed_item_ids,
    context_by_item_id: Mapping[str, str] | None = None,
) -> tuple[ClassificationAlignmentNeed, ...]:
    payload = _decode_object(text)
    if payload is None or not isinstance(payload.get("interpretations"), list):
        return ()
    allowed_ids = frozenset(allowed_item_ids)
    context = context_by_item_id or {}
    needs = []
    for item in payload["interpretations"]:
        if not isinstance(item, dict):
            continue
        item_id = item.get(item_id_field)
        if not isinstance(item_id, str) or item_id not in allowed_ids:
            continue
        statement = item.get("interpreted_statement")
        if not isinstance(statement, str):
            statement = "<unavailable>"
        for field_name, allowed in CONTROLLED_CLASSIFICATION_VALUES.items():
            raw = item.get(field_name)
            if isinstance(raw, str) and raw not in allowed:
                needs.append(
                    ClassificationAlignmentNeed(
                        item_id=item_id,
                        field_name=field_name,
                        raw_value=raw,
                        interpreted_statement=statement,
                        context=context.get(item_id),
                    )
                )
    return tuple(sorted(needs, key=lambda x: (x.item_id, x.field_name)))


def lexical_alignment_decision(need: ClassificationAlignmentNeed):
    allowed = CONTROLLED_CLASSIFICATION_VALUES[need.field_name]
    normalized = " ".join(need.raw_value.split()).casefold()
    matches = tuple(value for value in allowed if value.casefold() == normalized)
    if len(matches) != 1:
        return None
    return _decision(
        need,
        matches[0],
        "lexical",
        "Deterministic lexical normalization matched one controlled value.",
        None,
    )


def parse_classification_alignment_response(
    text: str,
    *,
    needs: tuple[ClassificationAlignmentNeed, ...],
    mapper_response_id: str | None,
) -> tuple[ClassificationAlignmentDecision, ...]:
    payload = _require_object(text, "Classification alignment output")
    if frozenset(payload) != {"alignments"}:
        raise ClassificationAlignmentValidationError(
            "Classification alignment output must contain only 'alignments'."
        )
    values = payload["alignments"]
    if not isinstance(values, list):
        raise ClassificationAlignmentValidationError("alignments must be an array.")
    expected = {(n.item_id, n.field_name): n for n in needs}
    decisions = {}
    for raw in values:
        if not isinstance(raw, dict) or frozenset(raw) != _ALIGNMENT_FIELDS:
            raise ClassificationAlignmentValidationError(
                "Classification alignment fields do not match schema."
            )
        key = (raw["item_id"], raw["field_name"])
        if key not in expected or key in decisions:
            raise ClassificationAlignmentValidationError(
                "Classification alignment target set is invalid."
            )
        status = raw["mapping_status"]
        target = raw["normalized_value"]
        rationale = raw["rationale"]
        if status not in {"mapped", "ambiguous", "unmapped"}:
            raise ClassificationAlignmentValidationError("mapping_status is invalid.")
        allowed = CONTROLLED_CLASSIFICATION_VALUES[key[1]]
        if not isinstance(target, str) or target not in allowed:
            raise ClassificationAlignmentValidationError(
                "Classification alignment target is not controlled."
            )
        if not isinstance(rationale, str) or not rationale.strip():
            raise ClassificationAlignmentValidationError("rationale is required.")
        if status in {"ambiguous", "unmapped"}:
            fallback = NEUTRAL_CLASSIFICATION_FALLBACKS.get(key[1])
            if fallback is None or target != fallback:
                raise ClassificationAlignmentValidationError(
                    "Unresolved classification must use its neutral controlled value."
                )
        decisions[key] = _decision(
            expected[key], target, status, rationale.strip(), mapper_response_id
        )
    if set(decisions) != set(expected):
        raise ClassificationAlignmentValidationError(
            "Classification alignment did not cover the exact requested set."
        )
    return tuple(decisions[key] for key in sorted(decisions))


def fallback_unclassified_decisions(
    needs: tuple[ClassificationAlignmentNeed, ...],
    *,
    rationale: str,
    mapper_response_id: str | None,
):
    result = []
    for need in needs:
        fallback = NEUTRAL_CLASSIFICATION_FALLBACKS.get(need.field_name)
        if fallback is None:
            raise ClassificationAlignmentValidationError(
                f"No neutral controlled fallback exists for {need.field_name!r}."
            )
        result.append(
            _decision(
                need,
                fallback,
                "fallback_unclassified",
                rationale,
                mapper_response_id,
            )
        )
    return tuple(result)


def apply_classification_alignment(
    text: str,
    *,
    item_id_field: str,
    decisions: tuple[ClassificationAlignmentDecision, ...],
) -> str:
    if not decisions:
        return text
    payload = _require_object(text, "Original interpretation output")
    items = payload.get("interpretations")
    if not isinstance(items, list):
        raise ClassificationAlignmentValidationError(
            "Original interpretations must be an array."
        )
    by_key = {(d.item_id, d.field_name): d for d in decisions}
    if len(by_key) != len(decisions):
        raise ClassificationAlignmentValidationError("Alignment decisions must be unique.")
    applied = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = item.get(item_id_field)
        for field in CONTROLLED_CLASSIFICATION_VALUES:
            key = (item_id, field)
            decision = by_key.get(key)
            if decision is None:
                continue
            if item.get(field) != decision.raw_value:
                raise ClassificationAlignmentIntegrityError(
                    "Raw classification changed before alignment."
                )
            item[field] = decision.normalized_value
            applied.add(key)
    if applied != set(by_key):
        raise ClassificationAlignmentIntegrityError(
            "Could not locate every alignment target in original output."
        )
    return json.dumps(payload, ensure_ascii=False)


def _decision(need, target, status, rationale, response_id):
    body = {
        "item_id": need.item_id,
        "field_name": need.field_name,
        "raw_value": need.raw_value,
        "normalized_value": target,
        "mapping_status": status,
        "rationale": rationale,
        "mapper_response_id": response_id,
    }
    return ClassificationAlignmentDecision(
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
        raise ClassificationAlignmentValidationError(f"{label} must be JSON object text.")
    return value


def _sha(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()
