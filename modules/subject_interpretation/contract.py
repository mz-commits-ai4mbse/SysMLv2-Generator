"""Strict parsing and deterministic binding for Persona Subject interpretations."""

from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any

from modules.engineering_subjects.identifiers import (
    validate_canonical_subject_id,
)
from modules.engineering_subjects.types import CanonicalSubjectSet
from modules.semantic_extraction import (
    EPISTEMIC_CLASSES,
    INFORMATION_TYPES,
    STATEMENT_MODALITIES,
)

from .errors import (
    SubjectInterpretationIntegrityError,
    SubjectInterpretationValidationError,
)
from .types import (
    PRE_MODEL_RELATIONSHIP_KINDS,
    ParsedSubjectInterpretationOutput,
    PersonaSubjectInterpretation,
    PersonaSubjectRelationship,
    RejectedPersonaRelationship,
)


_RESULT_FIELDS = frozenset({"interpretations", "relationships"})
_INTERPRETATION_FIELDS = frozenset(
    {
        "canonical_subject_id",
        "interpreted_statement",
        "information_type",
        "statement_modality",
        "epistemic_class",
        "missing_evidence",
        "rationale",
        "uncertainties",
    }
)
_RELATIONSHIP_FIELDS = frozenset(
    {
        "source_subject_id",
        "relationship_kind",
        "target_subject_id",
        "statement",
    }
)
_JSON_FENCE_PATTERN = re.compile(
    r"^\s*```(?:json)?\s*(.*?)\s*```\s*$",
    re.DOTALL | re.IGNORECASE,
)
_PRE_REVIEW_EPISTEMIC_CLASSES = frozenset(
    value
    for value in EPISTEMIC_CLASSES
    if value != "derivation"
)


def parse_subject_interpretation_output(
    text: str,
    *,
    subject_set: CanonicalSubjectSet,
) -> ParsedSubjectInterpretationOutput:
    """Require exact Subject coverage and existing semantic dimensions."""

    if not isinstance(subject_set, CanonicalSubjectSet):
        raise SubjectInterpretationValidationError(
            "subject_set must be a CanonicalSubjectSet."
        )

    expected_ids = tuple(
        subject.canonical_subject_id
        for subject in subject_set.subjects
    )
    if not expected_ids:
        raise SubjectInterpretationValidationError(
            "subject_set must contain at least one canonical Subject."
        )
    if len(expected_ids) != len(set(expected_ids)):
        raise SubjectInterpretationIntegrityError(
            "Canonical Subject IDs must be unique."
        )

    if not isinstance(text, str) or not text.strip():
        raise SubjectInterpretationValidationError(
            "Subject interpretation output must be non-empty JSON text."
        )

    normalized = _strip_optional_json_fence(text)
    try:
        payload = json.loads(
            normalized,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except SubjectInterpretationValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise SubjectInterpretationValidationError(
            f"Subject interpretation output is not valid JSON: {exc}."
        ) from exc

    root = _require_exact_object(
        payload,
        _RESULT_FIELDS,
        "Subject interpretation result",
    )

    raw_values = root["interpretations"]
    if not isinstance(raw_values, list):
        raise SubjectInterpretationValidationError(
            "interpretations must be a JSON array."
        )

    allowed_ids = frozenset(expected_ids)
    parsed = {}

    for raw_value in raw_values:
        value = _parse_interpretation(
            raw_value,
            allowed_subject_ids=allowed_ids,
        )
        if value.canonical_subject_id in parsed:
            raise SubjectInterpretationValidationError(
                "Each canonical_subject_id must appear exactly once."
            )
        parsed[value.canonical_subject_id] = value

    actual_ids = set(parsed)
    if actual_ids != set(expected_ids):
        raise SubjectInterpretationValidationError(
            "Persona interpretation must cover the exact supplied Subject set; "
            f"missing={sorted(set(expected_ids) - actual_ids)!r}, "
            f"unexpected={sorted(actual_ids - set(expected_ids))!r}."
        )

    raw_relationships = root["relationships"]
    if not isinstance(raw_relationships, list):
        raise SubjectInterpretationValidationError(
            "relationships must be a JSON array."
        )

    accepted_relationships = []
    rejected_relationships = []

    for raw in raw_relationships:
        accepted, rejected = _parse_relationship_candidate(
            raw,
            allowed_subject_ids=allowed_ids,
        )
        if accepted is not None:
            accepted_relationships.append(accepted)
        if rejected is not None:
            rejected_relationships.append(rejected)

    relationships = tuple(accepted_relationships)
    rejected_relationships = tuple(rejected_relationships)

    relationship_keys = tuple(
        (
            value.source_subject_id,
            value.relationship_kind,
            value.target_subject_id,
            value.statement,
        )
        for value in relationships
    )
    if len(relationship_keys) != len(set(relationship_keys)):
        raise SubjectInterpretationValidationError(
            "relationships must not contain duplicates."
        )

    return ParsedSubjectInterpretationOutput(
        interpretations=tuple(
            parsed[subject_id]
            for subject_id in expected_ids
        ),
        relationships=relationships,
        rejected_relationships=rejected_relationships,
    )


def _parse_interpretation(
    value: Any,
    *,
    allowed_subject_ids: frozenset[str],
) -> PersonaSubjectInterpretation:
    item = _require_exact_object(
        value,
        _INTERPRETATION_FIELDS,
        "Subject interpretation item",
    )

    subject_id = _validate_subject_id(
        item["canonical_subject_id"],
        allowed_subject_ids=allowed_subject_ids,
        field_name="canonical_subject_id",
    )
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
        _PRE_REVIEW_EPISTEMIC_CLASSES,
        "epistemic_class",
    )

    missing_evidence = item["missing_evidence"]
    if missing_evidence is not None:
        missing_evidence = _require_text(
            missing_evidence,
            "missing_evidence",
        )

    if epistemic_class == "assumption":
        if missing_evidence is None:
            raise SubjectInterpretationValidationError(
                "assumption requires non-null missing_evidence."
            )
    elif missing_evidence is not None:
        raise SubjectInterpretationValidationError(
            "explicit/interpretation must use null missing_evidence."
        )

    rationale = _require_text(
        item["rationale"],
        "rationale",
    )
    uncertainties = _require_text_list(
        item["uncertainties"],
        "uncertainties",
    )

    fingerprint = _canonical_sha256(
        {
            "canonical_subject_id": subject_id,
            "interpreted_statement": interpreted_statement,
            "information_type": information_type,
            "statement_modality": statement_modality,
            "epistemic_class": epistemic_class,
            "missing_evidence": missing_evidence,
            "rationale": rationale,
            "uncertainties": list(uncertainties),
        }
    )

    return PersonaSubjectInterpretation(
        canonical_subject_id=subject_id,
        interpreted_statement=interpreted_statement,
        information_type=information_type,
        statement_modality=statement_modality,
        epistemic_class=epistemic_class,
        missing_evidence=missing_evidence,
        rationale=rationale,
        uncertainties=uncertainties,
        content_fingerprint=fingerprint,
    )


def _parse_relationship_candidate(
    value: Any,
    *,
    allowed_subject_ids: frozenset[str],
) -> tuple[
    PersonaSubjectRelationship | None,
    RejectedPersonaRelationship | None,
]:
    """Parse one optional relationship hint.

    Subject identity, endpoint integrity and object shape remain hard
    validation boundaries. An unsupported predicate is rejected as an
    optional candidate and never admitted downstream.
    """

    item = _require_exact_object(
        value,
        _RELATIONSHIP_FIELDS,
        "Subject relationship",
    )

    source = _validate_subject_id(
        item["source_subject_id"],
        allowed_subject_ids=allowed_subject_ids,
        field_name="source_subject_id",
    )
    target = _validate_subject_id(
        item["target_subject_id"],
        allowed_subject_ids=allowed_subject_ids,
        field_name="target_subject_id",
    )
    if source == target:
        raise SubjectInterpretationValidationError(
            "Relationship endpoints must reference two different Subjects."
        )

    raw_kind = _require_text(
        item["relationship_kind"],
        "relationship_kind",
    )
    statement = _require_text(
        item["statement"],
        "relationship statement",
    )

    fingerprint = _canonical_sha256(
        {
            "source_subject_id": source,
            "relationship_kind": raw_kind,
            "target_subject_id": target,
            "statement": statement,
        }
    )

    if raw_kind not in PRE_MODEL_RELATIONSHIP_KINDS:
        return (
            None,
            RejectedPersonaRelationship(
                source_subject_id=source,
                relationship_kind=raw_kind,
                target_subject_id=target,
                statement=statement,
                reason_code="unsupported_relationship_kind",
                content_fingerprint=fingerprint,
            ),
        )

    return (
        PersonaSubjectRelationship(
            source_subject_id=source,
            relationship_kind=raw_kind,
            target_subject_id=target,
            statement=statement,
            content_fingerprint=fingerprint,
        ),
        None,
    )


def _validate_subject_id(
    value: Any,
    *,
    allowed_subject_ids: frozenset[str],
    field_name: str,
) -> str:
    try:
        subject_id = validate_canonical_subject_id(value)
    except Exception as exc:
        raise SubjectInterpretationValidationError(
            f"{field_name} is invalid."
        ) from exc

    if subject_id not in allowed_subject_ids:
        raise SubjectInterpretationValidationError(
            f"{field_name} references a Subject outside the supplied population."
        )
    return subject_id


def _require_exact_object(
    value: Any,
    expected_fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SubjectInterpretationValidationError(
            f"{label} must be a JSON object."
        )

    actual = frozenset(value)
    if actual != expected_fields:
        missing = sorted(expected_fields - actual)
        unexpected = sorted(actual - expected_fields)
        raise SubjectInterpretationValidationError(
            f"{label} fields do not match schema; "
            f"missing={missing!r}, unexpected={unexpected!r}."
        )
    return value


def _require_text(value: Any, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
    ):
        raise SubjectInterpretationValidationError(
            f"{field_name} must be non-empty trimmed text."
        )
    return value


def _require_choice(
    value: Any,
    allowed,
    field_name: str,
) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise SubjectInterpretationValidationError(
            f"{field_name} is not an allowed value."
        )
    return value


def _require_text_list(
    value: Any,
    field_name: str,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise SubjectInterpretationValidationError(
            f"{field_name} must be a JSON array."
        )

    result = tuple(
        _require_text(item, f"{field_name}[{index}]")
        for index, item in enumerate(value)
    )
    if len(result) != len(set(result)):
        raise SubjectInterpretationValidationError(
            f"{field_name} must not contain duplicates."
        )
    return result


def _canonical_sha256(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _strip_optional_json_fence(text: str) -> str:
    match = _JSON_FENCE_PATTERN.fullmatch(text)
    return match.group(1) if match else text.strip()


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise SubjectInterpretationValidationError(
                f"Duplicate JSON field is not allowed: {key!r}."
            )
        result[key] = value
    return result
