"""Strict parsing and deterministic SourceEvidence-to-candidate binding."""

from __future__ import annotations

import json
import re
from typing import Any

from modules.semantic_extraction import (
    EPISTEMIC_CLASSES,
    INFORMATION_TYPES,
    STATEMENT_MODALITIES,
    InformationUnitSourceAnchor,
    create_information_unit_candidate,
    format_information_unit_candidate_id,
)
from modules.source_evidence.identifiers import (
    validate_source_evidence_id,
)
from modules.source_evidence.types import SourceEvidence

from .errors import (
    EvidenceInterpretationIntegrityError,
    EvidenceInterpretationValidationError,
)
from .types import EvidenceInterpretationValue


_RESULT_FIELDS = frozenset({"interpretations"})
_INTERPRETATION_FIELDS = frozenset(
    {
        "source_evidence_id",
        "interpreted_statement",
        "information_type",
        "statement_modality",
        "epistemic_class",
        "missing_evidence",
        "extraction_rationale",
        "uncertainties",
    }
)
_JSON_FENCE_PATTERN = re.compile(
    r"^\s*```(?:json)?\s*(.*?)\s*```\s*$",
    re.DOTALL | re.IGNORECASE,
)
_ALLOWED_PRE_REVIEW_EPISTEMIC_CLASSES = frozenset(
    {
        "explicit",
        "interpretation",
        "assumption",
    }
)


def parse_evidence_interpretation_output(
    text: str,
    *,
    expected_source_evidence_ids: tuple[str, ...],
) -> tuple[EvidenceInterpretationValue, ...]:
    """Parse strict JSON and require exactly the supplied Evidence identities."""

    if not isinstance(text, str) or not text.strip():
        raise EvidenceInterpretationValidationError(
            "Evidence interpretation output must be non-empty JSON text."
        )

    expected_ids = _validated_expected_ids(
        expected_source_evidence_ids
    )
    normalized = _strip_optional_json_fence(text)

    try:
        payload = json.loads(
            normalized,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except EvidenceInterpretationValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise EvidenceInterpretationValidationError(
            f"Evidence interpretation output is not valid JSON: {exc}."
        ) from exc

    root = _require_exact_object(
        payload,
        _RESULT_FIELDS,
        "Evidence interpretation result",
    )
    raw_values = root["interpretations"]
    if not isinstance(raw_values, list):
        raise EvidenceInterpretationValidationError(
            "interpretations must be a JSON array."
        )

    parsed: dict[str, EvidenceInterpretationValue] = {}
    for raw_value in raw_values:
        value = _parse_value(raw_value)
        if value.source_evidence_id in parsed:
            raise EvidenceInterpretationValidationError(
                "Each source_evidence_id must appear exactly once."
            )
        parsed[value.source_evidence_id] = value

    actual_ids = set(parsed)
    expected_id_set = set(expected_ids)
    if actual_ids != expected_id_set:
        raise EvidenceInterpretationValidationError(
            "Persona interpretation must cover the exact supplied Evidence set; "
            f"missing={sorted(expected_id_set - actual_ids)!r}, "
            f"unexpected={sorted(actual_ids - expected_id_set)!r}."
        )

    return tuple(parsed[source_evidence_id] for source_evidence_id in expected_ids)


def materialize_information_unit_candidates(
    *,
    evidence: tuple[SourceEvidence, ...],
    interpretations: tuple[EvidenceInterpretationValue, ...],
):
    """Bind persona semantics to system-owned Evidence anchors and excerpts."""

    if len(evidence) != len(interpretations):
        raise EvidenceInterpretationIntegrityError(
            "Evidence and interpretation cardinality must match exactly."
        )

    interpretation_by_id = {
        value.source_evidence_id: value
        for value in interpretations
    }
    if len(interpretation_by_id) != len(interpretations):
        raise EvidenceInterpretationIntegrityError(
            "Interpretation Evidence identities must be unique."
        )

    candidates = []
    for index, item in enumerate(evidence, start=1):
        value = interpretation_by_id.get(item.source_evidence_id)
        if value is None:
            raise EvidenceInterpretationIntegrityError(
                "Interpretation is missing a required Source Evidence identity: "
                f"{item.source_evidence_id}."
            )

        anchors = tuple(
            InformationUnitSourceAnchor(
                segment_id=anchor.segment_id,
                start_offset=anchor.start_offset,
                end_offset=anchor.end_offset,
            )
            for anchor in item.source_anchors
        )

        candidates.append(
            create_information_unit_candidate(
                candidate_id=format_information_unit_candidate_id(index),
                source_anchors=anchors,
                source_excerpt=item.source_excerpt,
                interpreted_statement=value.interpreted_statement,
                information_type=value.information_type,
                statement_modality=value.statement_modality,
                epistemic_class=value.epistemic_class,
                extraction_rationale=value.extraction_rationale,
                supporting_information_unit_ids=(),
                derivation_rationale=None,
                missing_evidence=value.missing_evidence,
                uncertainties=value.uncertainties,
            )
        )

    return tuple(candidates)


def _parse_value(value: Any) -> EvidenceInterpretationValue:
    item = _require_exact_object(
        value,
        _INTERPRETATION_FIELDS,
        "Evidence interpretation item",
    )

    try:
        source_evidence_id = validate_source_evidence_id(
            item["source_evidence_id"]
        )
    except Exception as exc:
        raise EvidenceInterpretationValidationError(
            "source_evidence_id is invalid."
        ) from exc

    interpreted_statement = _require_text(
        item["interpreted_statement"],
        "interpreted_statement",
    )
    information_type = _require_choice(
        item["information_type"],
        INFORMATION_TYPES,
        "information_type",
    )
    statement_modality = _require_choice(
        item["statement_modality"],
        STATEMENT_MODALITIES,
        "statement_modality",
    )
    epistemic_class = _require_choice(
        item["epistemic_class"],
        EPISTEMIC_CLASSES,
        "epistemic_class",
    )
    if epistemic_class not in _ALLOWED_PRE_REVIEW_EPISTEMIC_CLASSES:
        raise EvidenceInterpretationValidationError(
            "Pre-review Evidence interpretation forbids epistemic_class "
            f"{epistemic_class!r}."
        )

    missing_evidence = item["missing_evidence"]
    if missing_evidence is not None:
        missing_evidence = _require_text(
            missing_evidence,
            "missing_evidence",
        )

    if epistemic_class == "assumption":
        if missing_evidence is None:
            raise EvidenceInterpretationValidationError(
                "assumption requires non-null missing_evidence."
            )
    elif missing_evidence is not None:
        raise EvidenceInterpretationValidationError(
            "explicit/interpretation must use null missing_evidence."
        )

    extraction_rationale = _require_text(
        item["extraction_rationale"],
        "extraction_rationale",
    )
    uncertainties = _require_text_list(
        item["uncertainties"],
        "uncertainties",
    )

    return EvidenceInterpretationValue(
        source_evidence_id=source_evidence_id,
        interpreted_statement=interpreted_statement,
        information_type=information_type,
        statement_modality=statement_modality,
        epistemic_class=epistemic_class,
        missing_evidence=missing_evidence,
        extraction_rationale=extraction_rationale,
        uncertainties=uncertainties,
    )


def _validated_expected_ids(
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(values, tuple) or not values:
        raise EvidenceInterpretationValidationError(
            "expected_source_evidence_ids must be a non-empty tuple."
        )

    result = []
    for value in values:
        try:
            result.append(validate_source_evidence_id(value))
        except Exception as exc:
            raise EvidenceInterpretationValidationError(
                "expected_source_evidence_ids contains an invalid ID."
            ) from exc

    if len(result) != len(set(result)):
        raise EvidenceInterpretationValidationError(
            "expected_source_evidence_ids must be unique."
        )
    return tuple(result)


def _require_exact_object(
    value: Any,
    expected_fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceInterpretationValidationError(
            f"{label} must be a JSON object."
        )
    actual = frozenset(value)
    if actual != expected_fields:
        missing = sorted(expected_fields - actual)
        unexpected = sorted(actual - expected_fields)
        raise EvidenceInterpretationValidationError(
            f"{label} fields do not match schema; "
            f"missing={missing!r}, unexpected={unexpected!r}."
        )
    return value


def _require_text(
    value: Any,
    field_name: str,
) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
    ):
        raise EvidenceInterpretationValidationError(
            f"{field_name} must be non-empty trimmed text."
        )
    return value


def _require_choice(
    value: Any,
    allowed,
    field_name: str,
) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise EvidenceInterpretationValidationError(
            f"{field_name} is not an allowed value."
        )
    return value


def _require_text_list(
    value: Any,
    field_name: str,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise EvidenceInterpretationValidationError(
            f"{field_name} must be a JSON array."
        )
    result = tuple(
        _require_text(item, f"{field_name}[{index}]")
        for index, item in enumerate(value)
    )
    if len(result) != len(set(result)):
        raise EvidenceInterpretationValidationError(
            f"{field_name} must not contain duplicates."
        )
    return result


def _strip_optional_json_fence(text: str) -> str:
    match = _JSON_FENCE_PATTERN.fullmatch(text)
    return match.group(1) if match else text.strip()


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceInterpretationValidationError(
                f"Duplicate JSON field is not allowed: {key!r}."
            )
        result[key] = value
    return result
