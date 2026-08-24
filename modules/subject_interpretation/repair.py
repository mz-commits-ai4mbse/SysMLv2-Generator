"""Bounded repair for required Persona classification enum violations.

The original Persona output remains authoritative for every valid field.
A repair call may replace only explicitly identified invalid required
classification values. The system applies the replacements deterministically
and re-runs the strict parser.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any

from modules.engineering_subjects.types import CanonicalSubjectSet
from modules.semantic_extraction import (
    EPISTEMIC_CLASSES,
    INFORMATION_TYPES,
    STATEMENT_MODALITIES,
)

from .errors import SubjectInterpretationValidationError
from .types import PersonaClassificationRepair


CLASSIFICATION_REPAIR_SCHEMA_VERSION = "1.0.0"

_PRE_REVIEW_EPISTEMIC_CLASSES = frozenset(
    value
    for value in EPISTEMIC_CLASSES
    if value != "derivation"
)
_FIELD_ALLOWED_VALUES = {
    "information_type": frozenset(INFORMATION_TYPES),
    "statement_modality": frozenset(STATEMENT_MODALITIES),
    "epistemic_class": _PRE_REVIEW_EPISTEMIC_CLASSES,
}
_JSON_FENCE_PATTERN = re.compile(
    r"^\s*```(?:json)?\s*(.*?)\s*```\s*$",
    re.DOTALL | re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ClassificationRepairNeed:
    canonical_subject_id: str
    field_name: str
    invalid_value: str


def find_classification_repair_needs(
    text: str,
    *,
    subject_set: CanonicalSubjectSet,
) -> tuple[ClassificationRepairNeed, ...]:
    """Return only invalid required enum values from otherwise JSON-like output.

    This function intentionally does not repair malformed JSON, missing fields,
    duplicate Subject identities or population problems. Those remain hard
    parser failures.
    """

    payload = _decode_json_object(text)
    if payload is None:
        return ()

    raw_interpretations = payload.get("interpretations")
    if not isinstance(raw_interpretations, list):
        return ()

    allowed_subject_ids = {
        subject.canonical_subject_id
        for subject in subject_set.subjects
    }
    needs = []

    for item in raw_interpretations:
        if not isinstance(item, dict):
            continue
        subject_id = item.get("canonical_subject_id")
        if (
            not isinstance(subject_id, str)
            or subject_id not in allowed_subject_ids
        ):
            continue

        for field_name, allowed_values in _FIELD_ALLOWED_VALUES.items():
            value = item.get(field_name)
            if isinstance(value, str) and value not in allowed_values:
                needs.append(
                    ClassificationRepairNeed(
                        canonical_subject_id=subject_id,
                        field_name=field_name,
                        invalid_value=value,
                    )
                )

    return tuple(needs)


def build_classification_repair_task(
    needs: tuple[ClassificationRepairNeed, ...],
) -> str:
    if not needs:
        raise SubjectInterpretationValidationError(
            "Classification repair requires at least one invalid enum field."
        )

    return f"""
Return only JSON. Do not wrap the JSON in Markdown fences.

This is a BOUNDED SCHEMA REPAIR of your immediately preceding Persona output.

You are NOT re-interpreting the engineering source.
You are NOT allowed to:
- create, omit, merge, split or rename any SUBJ-*;
- change any interpreted_statement;
- change any rationale, uncertainty or missing-evidence content;
- change any valid classification field;
- add, remove or change relationships;
- introduce new taxonomy terms.

Only the invalid required classification fields listed in the input may be
replaced.

Allowed information_type values:
{" | ".join(sorted(INFORMATION_TYPES))}

Allowed statement_modality values:
{" | ".join(sorted(STATEMENT_MODALITIES))}

Allowed pre-review epistemic_class values:
{" | ".join(sorted(_PRE_REVIEW_EPISTEMIC_CLASSES))}

For every listed invalid field return exactly one repair object.
Do not return repairs for any other field.

Required JSON shape:
{{
  "repairs": [
    {{
      "canonical_subject_id": "SUBJ-000001",
      "field_name": "information_type",
      "value": "unclassified"
    }}
  ]
}}
""".strip()


def build_classification_repair_input(
    *,
    original_subject_input: str,
    raw_output: str,
    needs: tuple[ClassificationRepairNeed, ...],
) -> str:
    payload = _decode_json_object(raw_output)
    if payload is None:
        raise SubjectInterpretationValidationError(
            "Classification repair cannot operate on malformed JSON."
        )

    interpretation_by_id = {}
    raw_interpretations = payload.get("interpretations", [])
    if isinstance(raw_interpretations, list):
        for item in raw_interpretations:
            if isinstance(item, dict):
                subject_id = item.get("canonical_subject_id")
                if isinstance(subject_id, str):
                    interpretation_by_id[subject_id] = item

    sections = [
        original_subject_input,
        "",
        "# REQUIRED CLASSIFICATION REPAIRS",
        "",
        (
            "Choose an allowed replacement only for each field below. "
            "All other original output content is immutable."
        ),
        "",
    ]

    for need in needs:
        item = interpretation_by_id.get(need.canonical_subject_id, {})
        statement = item.get("interpreted_statement")
        sections.extend(
            [
                (
                    f"- {need.canonical_subject_id} | "
                    f"{need.field_name}={need.invalid_value!r}"
                ),
                (
                    f"  current interpreted_statement: {statement!r}"
                    if isinstance(statement, str)
                    else "  current interpreted_statement: <unavailable>"
                ),
            ]
        )

    return "\n".join(sections)


def apply_classification_repair_response(
    *,
    raw_output: str,
    repair_output: str,
    needs: tuple[ClassificationRepairNeed, ...],
) -> tuple[str, tuple[PersonaClassificationRepair, ...]]:
    """Patch only exact invalid enum fields and return strict-parser input."""

    original = _require_json_object(raw_output, "Original Persona output")
    repair_payload = _require_json_object(
        repair_output,
        "Classification repair output",
    )

    if frozenset(repair_payload) != frozenset({"repairs"}):
        raise SubjectInterpretationValidationError(
            "Classification repair output must contain only 'repairs'."
        )

    raw_repairs = repair_payload["repairs"]
    if not isinstance(raw_repairs, list):
        raise SubjectInterpretationValidationError(
            "Classification repair 'repairs' must be a JSON array."
        )

    expected = {
        (need.canonical_subject_id, need.field_name): need
        for need in needs
    }
    if len(expected) != len(needs):
        raise SubjectInterpretationValidationError(
            "Classification repair needs must be unique."
        )

    replacements = {}
    for item in raw_repairs:
        if not isinstance(item, dict):
            raise SubjectInterpretationValidationError(
                "Each classification repair must be a JSON object."
            )
        if frozenset(item) != frozenset(
            {"canonical_subject_id", "field_name", "value"}
        ):
            raise SubjectInterpretationValidationError(
                "Classification repair fields do not match schema."
            )

        subject_id = item["canonical_subject_id"]
        field_name = item["field_name"]
        value = item["value"]
        key = (subject_id, field_name)

        if key not in expected:
            raise SubjectInterpretationValidationError(
                "Classification repair attempted to modify a field "
                "that was not identified as invalid."
            )
        if key in replacements:
            raise SubjectInterpretationValidationError(
                "Classification repair contains a duplicate field repair."
            )
        if (
            not isinstance(value, str)
            or value not in _FIELD_ALLOWED_VALUES[field_name]
        ):
            raise SubjectInterpretationValidationError(
                "Classification repair replacement is not an allowed value."
            )

        replacements[key] = value

    if set(replacements) != set(expected):
        missing = sorted(set(expected) - set(replacements))
        raise SubjectInterpretationValidationError(
            f"Classification repair did not cover all invalid fields: {missing!r}."
        )

    interpretations = original.get("interpretations")
    if not isinstance(interpretations, list):
        raise SubjectInterpretationValidationError(
            "Original Persona output interpretations must be an array."
        )

    repairs = []
    applied = set()

    for item in interpretations:
        if not isinstance(item, dict):
            continue
        subject_id = item.get("canonical_subject_id")
        for field_name in _FIELD_ALLOWED_VALUES:
            key = (subject_id, field_name)
            if key not in replacements:
                continue

            expected_need = expected[key]
            if item.get(field_name) != expected_need.invalid_value:
                raise SubjectInterpretationValidationError(
                    "Original invalid classification value changed before repair."
                )

            repaired_value = replacements[key]
            item[field_name] = repaired_value
            applied.add(key)

            fingerprint = _canonical_sha256(
                {
                    "canonical_subject_id": subject_id,
                    "field_name": field_name,
                    "original_value": expected_need.invalid_value,
                    "repaired_value": repaired_value,
                }
            )
            repairs.append(
                PersonaClassificationRepair(
                    canonical_subject_id=subject_id,
                    field_name=field_name,
                    original_value=expected_need.invalid_value,
                    repaired_value=repaired_value,
                    content_fingerprint=fingerprint,
                )
            )

    if applied != set(expected):
        raise SubjectInterpretationValidationError(
            "Classification repair could not locate every invalid field "
            "in the original output."
        )

    return (
        json.dumps(original, ensure_ascii=False),
        tuple(
            sorted(
                repairs,
                key=lambda value: (
                    value.canonical_subject_id,
                    value.field_name,
                ),
            )
        ),
    )


def _decode_json_object(text: str) -> dict[str, Any] | None:
    if not isinstance(text, str) or not text.strip():
        return None
    match = _JSON_FENCE_PATTERN.fullmatch(text)
    normalized = match.group(1) if match else text.strip()
    try:
        payload = json.loads(normalized)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _require_json_object(text: str, label: str) -> dict[str, Any]:
    value = _decode_json_object(text)
    if value is None:
        raise SubjectInterpretationValidationError(
            f"{label} must be valid JSON object text."
        )
    return value


def _canonical_sha256(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
