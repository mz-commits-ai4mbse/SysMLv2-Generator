"""Validate, parse and serialize immutable Information Units.

This module validates the deterministic JSON contract. It does not decide
semantic atomicity, query project persistence or perform Human Review.
Cross-artifact validation belongs to the Information Unit repository.
"""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
import re
from typing import Any

from modules.project_sources.identifiers import validate_source_id
from modules.project_workspace.identifiers import is_valid_project_id
from modules.source_projection.identifiers import (
    segment_id_sequence,
    validate_segment_id,
    validate_source_projection_id,
)

from .errors import (
    InformationUnitAnchorError,
    InformationUnitAssumptionError,
    InformationUnitDerivationError,
    InformationUnitValidationError,
)
from .identifiers import validate_information_unit_id
from .types import (
    EPISTEMIC_CLASSES,
    INFORMATION_TYPES,
    SEMANTIC_CONFIDENCE_LEVELS,
    STATEMENT_MODALITIES,
    InformationUnit,
    InformationUnitExtractionProvenance,
    InformationUnitSourceAnchor,
)


INFORMATION_UNIT_SCHEMA_VERSION = "1.0.0"

_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)
_SEMANTIC_VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+$"
)
_SHA256_PATTERN = re.compile(
    r"^[0-9a-f]{64}$"
)

_INFORMATION_UNIT_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "information_unit_id",
        "source_id",
        "source_projection_id",
        "source_anchors",
        "source_excerpt",
        "interpreted_statement",
        "information_type",
        "statement_modality",
        "epistemic_class",
        "supporting_information_unit_ids",
        "derivation_rationale",
        "missing_evidence",
        "extraction_provenance",
        "confidence",
        "confidence_rationale",
        "content_fingerprint",
        "created_at",
    }
)
_SOURCE_ANCHOR_FIELDS = frozenset(
    {
        "segment_id",
        "start_offset",
        "end_offset",
    }
)
_EXTRACTION_PROVENANCE_FIELDS = frozenset(
    {
        "team_id",
        "persona_ids",
        "llm_provider",
        "llm_model",
        "prompt_schema_version",
        "consensus_report_id",
    }
)


def create_information_unit(
    *,
    project_id: str,
    information_unit_id: str,
    source_id: str,
    source_projection_id: str,
    source_anchors: tuple[
        InformationUnitSourceAnchor,
        ...
    ],
    source_excerpt: str,
    interpreted_statement: str,
    information_type: str,
    statement_modality: str,
    epistemic_class: str,
    extraction_provenance: InformationUnitExtractionProvenance,
    confidence: str,
    confidence_rationale: str,
    timestamp: str,
    supporting_information_unit_ids: tuple[str, ...] = (),
    derivation_rationale: str | None = None,
    missing_evidence: str | None = None,
) -> InformationUnit:
    """Create one validated immutable Information Unit."""

    content_fingerprint = (
        calculate_information_unit_content_fingerprint(
            project_id=project_id,
            source_id=source_id,
            source_projection_id=source_projection_id,
            source_anchors=source_anchors,
            source_excerpt=source_excerpt,
            interpreted_statement=interpreted_statement,
            information_type=information_type,
            statement_modality=statement_modality,
            epistemic_class=epistemic_class,
            supporting_information_unit_ids=(
                supporting_information_unit_ids
            ),
            derivation_rationale=derivation_rationale,
            missing_evidence=missing_evidence,
        )
    )

    return parse_information_unit(
        {
            "schema_version": INFORMATION_UNIT_SCHEMA_VERSION,
            "project_id": project_id,
            "information_unit_id": information_unit_id,
            "source_id": source_id,
            "source_projection_id": source_projection_id,
            "source_anchors": [
                _source_anchor_payload(anchor)
                for anchor in source_anchors
            ],
            "source_excerpt": source_excerpt,
            "interpreted_statement": interpreted_statement,
            "information_type": information_type,
            "statement_modality": statement_modality,
            "epistemic_class": epistemic_class,
            "supporting_information_unit_ids": list(
                supporting_information_unit_ids
            ),
            "derivation_rationale": derivation_rationale,
            "missing_evidence": missing_evidence,
            "extraction_provenance": (
                _extraction_provenance_payload(
                    extraction_provenance
                )
            ),
            "confidence": confidence,
            "confidence_rationale": confidence_rationale,
            "content_fingerprint": content_fingerprint,
            "created_at": timestamp,
        },
        expected_project_id=project_id,
        expected_information_unit_id=information_unit_id,
        expected_source_id=source_id,
        expected_source_projection_id=source_projection_id,
    )


def parse_information_unit(
    payload: Any,
    *,
    expected_project_id: str | None = None,
    expected_information_unit_id: str | None = None,
    expected_source_id: str | None = None,
    expected_source_projection_id: str | None = None,
) -> InformationUnit:
    """Parse and validate one Information Unit payload."""

    item = _require_exact_object(
        payload,
        _INFORMATION_UNIT_FIELDS,
        "Information Unit",
    )

    schema_version = item["schema_version"]

    if schema_version != INFORMATION_UNIT_SCHEMA_VERSION:
        raise InformationUnitValidationError(
            "Unsupported Information Unit schema_version: "
            f"{schema_version!r}."
        )

    project_id = _require_project_id(
        item["project_id"],
        "project_id",
    )
    information_unit_id = _require_information_unit_id(
        item["information_unit_id"],
        "information_unit_id",
    )
    source_id = _require_source_id(
        item["source_id"],
        "source_id",
    )
    source_projection_id = _require_source_projection_id(
        item["source_projection_id"],
        "source_projection_id",
    )

    _require_expected_value(
        project_id,
        expected_project_id,
        _require_project_id,
        "project_id",
    )
    _require_expected_value(
        information_unit_id,
        expected_information_unit_id,
        _require_information_unit_id,
        "information_unit_id",
    )
    _require_expected_value(
        source_id,
        expected_source_id,
        _require_source_id,
        "source_id",
    )
    _require_expected_value(
        source_projection_id,
        expected_source_projection_id,
        _require_source_projection_id,
        "source_projection_id",
    )

    source_anchors = _parse_source_anchors(
        item["source_anchors"]
    )
    source_excerpt = _require_source_excerpt(
        item["source_excerpt"]
    )
    interpreted_statement = _require_stored_text(
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
    supporting_information_unit_ids = (
        _parse_supporting_information_unit_ids(
            item["supporting_information_unit_ids"],
            information_unit_id,
        )
    )
    derivation_rationale = _require_optional_text(
        item["derivation_rationale"],
        "derivation_rationale",
    )
    missing_evidence = _require_optional_text(
        item["missing_evidence"],
        "missing_evidence",
    )

    _validate_epistemic_evidence(
        epistemic_class=epistemic_class,
        supporting_information_unit_ids=(
            supporting_information_unit_ids
        ),
        derivation_rationale=derivation_rationale,
        missing_evidence=missing_evidence,
    )

    extraction_provenance = _parse_extraction_provenance(
        item["extraction_provenance"]
    )
    confidence = _require_choice(
        item["confidence"],
        SEMANTIC_CONFIDENCE_LEVELS,
        "confidence",
    )
    confidence_rationale = _require_stored_text(
        item["confidence_rationale"],
        "confidence_rationale",
    )
    content_fingerprint = _require_sha256(
        item["content_fingerprint"],
        "content_fingerprint",
    )
    created_at = _require_utc_timestamp(
        item["created_at"],
        "created_at",
    )

    expected_fingerprint = (
        calculate_information_unit_content_fingerprint(
            project_id=project_id,
            source_id=source_id,
            source_projection_id=source_projection_id,
            source_anchors=source_anchors,
            source_excerpt=source_excerpt,
            interpreted_statement=interpreted_statement,
            information_type=information_type,
            statement_modality=statement_modality,
            epistemic_class=epistemic_class,
            supporting_information_unit_ids=(
                supporting_information_unit_ids
            ),
            derivation_rationale=derivation_rationale,
            missing_evidence=missing_evidence,
        )
    )

    if content_fingerprint != expected_fingerprint:
        raise InformationUnitValidationError(
            "content_fingerprint does not match the "
            "Information Unit professional content."
        )

    return InformationUnit(
        schema_version=schema_version,
        project_id=project_id,
        information_unit_id=information_unit_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        source_anchors=source_anchors,
        source_excerpt=source_excerpt,
        interpreted_statement=interpreted_statement,
        information_type=information_type,
        statement_modality=statement_modality,
        epistemic_class=epistemic_class,
        supporting_information_unit_ids=(
            supporting_information_unit_ids
        ),
        derivation_rationale=derivation_rationale,
        missing_evidence=missing_evidence,
        extraction_provenance=extraction_provenance,
        confidence=confidence,
        confidence_rationale=confidence_rationale,
        content_fingerprint=content_fingerprint,
        created_at=created_at,
    )


def information_unit_from_json(
    text: str,
    *,
    expected_project_id: str | None = None,
    expected_information_unit_id: str | None = None,
    expected_source_id: str | None = None,
    expected_source_projection_id: str | None = None,
) -> InformationUnit:
    """Parse and validate one Information Unit JSON string."""

    if not isinstance(text, str):
        raise InformationUnitValidationError(
            "Information Unit JSON input must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except InformationUnitValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise InformationUnitValidationError(
            "Information Unit contains invalid JSON: "
            f"{exc}."
        ) from exc

    return parse_information_unit(
        payload,
        expected_project_id=expected_project_id,
        expected_information_unit_id=(
            expected_information_unit_id
        ),
        expected_source_id=expected_source_id,
        expected_source_projection_id=(
            expected_source_projection_id
        ),
    )


def validate_information_unit(
    information_unit: InformationUnit,
) -> None:
    """Validate one immutable Information Unit instance."""

    information_unit_to_dict(information_unit)


def information_unit_to_dict(
    information_unit: InformationUnit,
) -> dict[str, Any]:
    """Return the canonical JSON-compatible representation."""

    if not isinstance(information_unit, InformationUnit):
        raise InformationUnitValidationError(
            "information_unit must be an InformationUnit "
            "instance."
        )

    payload = _information_unit_payload(information_unit)
    validated = parse_information_unit(payload)
    return _information_unit_payload(validated)


def information_unit_to_json(
    information_unit: InformationUnit,
) -> str:
    """Serialize one Information Unit deterministically."""

    return (
        json.dumps(
            information_unit_to_dict(information_unit),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def calculate_information_unit_content_fingerprint(
    *,
    project_id: str,
    source_id: str,
    source_projection_id: str,
    source_anchors: tuple[
        InformationUnitSourceAnchor,
        ...
    ],
    source_excerpt: str,
    interpreted_statement: str,
    information_type: str,
    statement_modality: str,
    epistemic_class: str,
    supporting_information_unit_ids: tuple[str, ...] = (),
    derivation_rationale: str | None = None,
    missing_evidence: str | None = None,
) -> str:
    """Hash stable professional content, excluding identity and run data."""

    validated_project_id = _require_project_id(
        project_id,
        "project_id",
    )
    validated_source_id = _require_source_id(
        source_id,
        "source_id",
    )
    validated_source_projection_id = (
        _require_source_projection_id(
            source_projection_id,
            "source_projection_id",
        )
    )

    if not isinstance(source_anchors, tuple):
        raise InformationUnitAnchorError(
            "source_anchors must be a tuple of "
            "InformationUnitSourceAnchor instances."
        )

    validated_source_anchors = _parse_source_anchors(
        [
            _source_anchor_payload(anchor)
            for anchor in source_anchors
        ]
    )
    validated_source_excerpt = _require_source_excerpt(
        source_excerpt
    )
    validated_interpreted_statement = _require_stored_text(
        interpreted_statement,
        "interpreted_statement",
    )
    validated_information_type = _require_choice(
        information_type,
        INFORMATION_TYPES,
        "information_type",
    )
    validated_statement_modality = _require_choice(
        statement_modality,
        STATEMENT_MODALITIES,
        "statement_modality",
    )
    validated_epistemic_class = _require_choice(
        epistemic_class,
        EPISTEMIC_CLASSES,
        "epistemic_class",
    )

    if not isinstance(
        supporting_information_unit_ids,
        tuple,
    ):
        raise InformationUnitValidationError(
            "supporting_information_unit_ids must be a tuple."
        )

    validated_supporting_ids = (
        _parse_supporting_information_unit_ids(
            list(supporting_information_unit_ids),
            None,
        )
    )
    validated_derivation_rationale = _require_optional_text(
        derivation_rationale,
        "derivation_rationale",
    )
    validated_missing_evidence = _require_optional_text(
        missing_evidence,
        "missing_evidence",
    )

    _validate_epistemic_evidence(
        epistemic_class=validated_epistemic_class,
        supporting_information_unit_ids=(
            validated_supporting_ids
        ),
        derivation_rationale=(
            validated_derivation_rationale
        ),
        missing_evidence=validated_missing_evidence,
    )

    fingerprint_payload = {
        "project_id": validated_project_id,
        "source_id": validated_source_id,
        "source_projection_id": (
            validated_source_projection_id
        ),
        "source_anchors": [
            _source_anchor_payload(anchor)
            for anchor in validated_source_anchors
        ],
        "source_excerpt": validated_source_excerpt,
        "interpreted_statement": (
            validated_interpreted_statement
        ),
        "information_type": validated_information_type,
        "statement_modality": (
            validated_statement_modality
        ),
        "epistemic_class": validated_epistemic_class,
        "supporting_information_unit_ids": list(
            validated_supporting_ids
        ),
        "derivation_rationale": (
            validated_derivation_rationale
        ),
        "missing_evidence": validated_missing_evidence,
    }
    canonical = json.dumps(
        fingerprint_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def _parse_source_anchors(
    value: Any,
) -> tuple[InformationUnitSourceAnchor, ...]:
    items = _require_list(value, "source_anchors")

    if not items:
        raise InformationUnitAnchorError(
            "source_anchors must contain at least one anchor."
        )

    anchors: list[InformationUnitSourceAnchor] = []

    for index, item in enumerate(items):
        label = f"source_anchors[{index}]"
        anchor = _require_exact_object(
            item,
            _SOURCE_ANCHOR_FIELDS,
            label,
        )
        segment_id = _require_segment_id(
            anchor["segment_id"],
            f"{label}.segment_id",
        )
        start_offset = _require_non_negative_integer(
            anchor["start_offset"],
            f"{label}.start_offset",
        )
        end_offset = _require_positive_integer(
            anchor["end_offset"],
            f"{label}.end_offset",
        )

        if end_offset <= start_offset:
            raise InformationUnitAnchorError(
                f"{label}.end_offset must be greater than "
                "start_offset."
            )

        anchors.append(
            InformationUnitSourceAnchor(
                segment_id=segment_id,
                start_offset=start_offset,
                end_offset=end_offset,
            )
        )

    order_keys = tuple(
        (
            segment_id_sequence(anchor.segment_id),
            anchor.start_offset,
            anchor.end_offset,
        )
        for anchor in anchors
    )

    if order_keys != tuple(sorted(order_keys)):
        raise InformationUnitAnchorError(
            "source_anchors must be ordered by segment and "
            "character range."
        )

    previous_end_by_segment: dict[str, int] = {}

    for anchor in anchors:
        previous_end = previous_end_by_segment.get(
            anchor.segment_id
        )

        if (
            previous_end is not None
            and anchor.start_offset < previous_end
        ):
            raise InformationUnitAnchorError(
                "source_anchors must not overlap within "
                f"segment {anchor.segment_id}."
            )

        previous_end_by_segment[anchor.segment_id] = (
            anchor.end_offset
        )

    return tuple(anchors)


def _parse_extraction_provenance(
    value: Any,
) -> InformationUnitExtractionProvenance:
    item = _require_exact_object(
        value,
        _EXTRACTION_PROVENANCE_FIELDS,
        "extraction_provenance",
    )
    team_id = _require_stored_text(
        item["team_id"],
        "extraction_provenance.team_id",
    )
    persona_ids = tuple(
        _require_stored_text(
            persona_id,
            f"extraction_provenance.persona_ids[{index}]",
        )
        for index, persona_id in enumerate(
            _require_list(
                item["persona_ids"],
                "extraction_provenance.persona_ids",
            )
        )
    )

    if not persona_ids:
        raise InformationUnitValidationError(
            "extraction_provenance.persona_ids must contain "
            "at least one persona."
        )

    if len(persona_ids) != len(set(persona_ids)):
        raise InformationUnitValidationError(
            "extraction_provenance.persona_ids must not "
            "contain duplicates."
        )

    if persona_ids != tuple(sorted(persona_ids)):
        raise InformationUnitValidationError(
            "extraction_provenance.persona_ids must be "
            "ordered by persona ID."
        )

    llm_provider = _require_stored_text(
        item["llm_provider"],
        "extraction_provenance.llm_provider",
    )
    llm_model = _require_stored_text(
        item["llm_model"],
        "extraction_provenance.llm_model",
    )
    prompt_schema_version = _require_semantic_version(
        item["prompt_schema_version"],
        "extraction_provenance.prompt_schema_version",
    )
    consensus_report_id = _require_stored_text(
        item["consensus_report_id"],
        "extraction_provenance.consensus_report_id",
    )

    return InformationUnitExtractionProvenance(
        team_id=team_id,
        persona_ids=persona_ids,
        llm_provider=llm_provider,
        llm_model=llm_model,
        prompt_schema_version=prompt_schema_version,
        consensus_report_id=consensus_report_id,
    )


def _parse_supporting_information_unit_ids(
    value: Any,
    information_unit_id: str | None,
) -> tuple[str, ...]:
    identifiers = tuple(
        _require_information_unit_id(
            item,
            f"supporting_information_unit_ids[{index}]",
        )
        for index, item in enumerate(
            _require_list(
                value,
                "supporting_information_unit_ids",
            )
        )
    )

    if len(identifiers) != len(set(identifiers)):
        raise InformationUnitDerivationError(
            "supporting_information_unit_ids must not "
            "contain duplicates."
        )

    if identifiers != tuple(sorted(identifiers)):
        raise InformationUnitDerivationError(
            "supporting_information_unit_ids must be "
            "ordered by Information Unit ID."
        )

    if (
        information_unit_id is not None
        and information_unit_id in identifiers
    ):
        raise InformationUnitDerivationError(
            "An Information Unit must not support itself."
        )

    return identifiers


def _validate_epistemic_evidence(
    *,
    epistemic_class: str,
    supporting_information_unit_ids: tuple[str, ...],
    derivation_rationale: str | None,
    missing_evidence: str | None,
) -> None:
    if epistemic_class == "derivation":
        if not supporting_information_unit_ids:
            raise InformationUnitDerivationError(
                "A derivation requires at least one supporting "
                "Information Unit ID."
            )

        if derivation_rationale is None:
            raise InformationUnitDerivationError(
                "A derivation requires derivation_rationale."
            )

        if missing_evidence is not None:
            raise InformationUnitDerivationError(
                "A derivation must not declare missing_evidence."
            )

        return

    if epistemic_class == "assumption":
        if missing_evidence is None:
            raise InformationUnitAssumptionError(
                "An assumption requires missing_evidence."
            )

        if supporting_information_unit_ids:
            raise InformationUnitAssumptionError(
                "An assumption must not use derivation support."
            )

        if derivation_rationale is not None:
            raise InformationUnitAssumptionError(
                "An assumption must not declare "
                "derivation_rationale."
            )

        return

    if supporting_information_unit_ids:
        raise InformationUnitDerivationError(
            f"{epistemic_class!r} must not use derivation "
            "support."
        )

    if derivation_rationale is not None:
        raise InformationUnitDerivationError(
            f"{epistemic_class!r} must not declare "
            "derivation_rationale."
        )

    if missing_evidence is not None:
        raise InformationUnitAssumptionError(
            f"{epistemic_class!r} must not declare "
            "missing_evidence."
        )


def _information_unit_payload(
    information_unit: InformationUnit,
) -> dict[str, Any]:
    return {
        "schema_version": information_unit.schema_version,
        "project_id": information_unit.project_id,
        "information_unit_id": (
            information_unit.information_unit_id
        ),
        "source_id": information_unit.source_id,
        "source_projection_id": (
            information_unit.source_projection_id
        ),
        "source_anchors": [
            _source_anchor_payload(anchor)
            for anchor in information_unit.source_anchors
        ],
        "source_excerpt": information_unit.source_excerpt,
        "interpreted_statement": (
            information_unit.interpreted_statement
        ),
        "information_type": information_unit.information_type,
        "statement_modality": (
            information_unit.statement_modality
        ),
        "epistemic_class": information_unit.epistemic_class,
        "supporting_information_unit_ids": list(
            information_unit.supporting_information_unit_ids
        ),
        "derivation_rationale": (
            information_unit.derivation_rationale
        ),
        "missing_evidence": information_unit.missing_evidence,
        "extraction_provenance": (
            _extraction_provenance_payload(
                information_unit.extraction_provenance
            )
        ),
        "confidence": information_unit.confidence,
        "confidence_rationale": (
            information_unit.confidence_rationale
        ),
        "content_fingerprint": (
            information_unit.content_fingerprint
        ),
        "created_at": information_unit.created_at,
    }


def _source_anchor_payload(
    anchor: InformationUnitSourceAnchor,
) -> dict[str, Any]:
    if not isinstance(anchor, InformationUnitSourceAnchor):
        raise InformationUnitAnchorError(
            "source_anchors must contain "
            "InformationUnitSourceAnchor instances."
        )

    return {
        "segment_id": anchor.segment_id,
        "start_offset": anchor.start_offset,
        "end_offset": anchor.end_offset,
    }


def _extraction_provenance_payload(
    provenance: InformationUnitExtractionProvenance,
) -> dict[str, Any]:
    if not isinstance(
        provenance,
        InformationUnitExtractionProvenance,
    ):
        raise InformationUnitValidationError(
            "extraction_provenance must be an "
            "InformationUnitExtractionProvenance instance."
        )

    return {
        "team_id": provenance.team_id,
        "persona_ids": list(provenance.persona_ids),
        "llm_provider": provenance.llm_provider,
        "llm_model": provenance.llm_model,
        "prompt_schema_version": (
            provenance.prompt_schema_version
        ),
        "consensus_report_id": provenance.consensus_report_id,
    }


def _require_expected_value(
    actual: str,
    expected: str | None,
    validator: Any,
    label: str,
) -> None:
    if expected is None:
        return

    validated_expected = validator(
        expected,
        f"expected_{label}",
    )

    if actual != validated_expected:
        raise InformationUnitValidationError(
            f"Information Unit {label} does not match its "
            f"expected context: {actual!r} != "
            f"{validated_expected!r}."
        )


def _require_project_id(
    value: Any,
    label: str,
) -> str:
    if not is_valid_project_id(value):
        raise InformationUnitValidationError(
            f"{label} must contain exactly six digits."
        )

    return value


def _require_information_unit_id(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_information_unit_id(value)
    except Exception as exc:
        raise InformationUnitValidationError(
            f"{label} must be a valid Information Unit ID."
        ) from exc


def _require_source_id(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_source_id(value)
    except Exception as exc:
        raise InformationUnitValidationError(
            f"{label} must be a valid Source ID."
        ) from exc


def _require_source_projection_id(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_source_projection_id(value)
    except Exception as exc:
        raise InformationUnitValidationError(
            f"{label} must be a valid Source Projection ID."
        ) from exc


def _require_segment_id(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_segment_id(value)
    except Exception as exc:
        raise InformationUnitAnchorError(
            f"{label} must be a valid Segment ID."
        ) from exc


def _require_choice(
    value: Any,
    allowed: frozenset[str],
    label: str,
) -> str:
    text = _require_stored_text(value, label)

    if text not in allowed:
        raise InformationUnitValidationError(
            f"{label} must be one of: "
            f"{', '.join(sorted(allowed))}."
        )

    return text


def _require_stored_text(
    value: Any,
    label: str,
) -> str:
    if not isinstance(value, str):
        raise InformationUnitValidationError(
            f"{label} must be a string."
        )

    if not value.strip():
        raise InformationUnitValidationError(
            f"{label} must not be empty."
        )

    if value != value.strip():
        raise InformationUnitValidationError(
            f"{label} must not have leading or trailing "
            "whitespace."
        )

    if "\x00" in value or "\r" in value:
        raise InformationUnitValidationError(
            f"{label} contains unsupported control characters."
        )

    return value


def _require_source_excerpt(value: Any) -> str:
    if not isinstance(value, str):
        raise InformationUnitValidationError(
            "source_excerpt must be a string."
        )

    if not value.strip():
        raise InformationUnitValidationError(
            "source_excerpt must contain visible source text."
        )

    if "\x00" in value or "\r" in value:
        raise InformationUnitValidationError(
            "source_excerpt contains unsupported control "
            "characters."
        )

    return value


def _require_optional_text(
    value: Any,
    label: str,
) -> str | None:
    if value is None:
        return None

    return _require_stored_text(value, label)


def _require_semantic_version(
    value: Any,
    label: str,
) -> str:
    text = _require_stored_text(value, label)

    if _SEMANTIC_VERSION_PATTERN.fullmatch(text) is None:
        raise InformationUnitValidationError(
            f"{label} must use MAJOR.MINOR.PATCH versioning."
        )

    return text


def _require_sha256(
    value: Any,
    label: str,
) -> str:
    if (
        not isinstance(value, str)
        or _SHA256_PATTERN.fullmatch(value) is None
    ):
        raise InformationUnitValidationError(
            f"{label} must contain a lowercase SHA-256 digest."
        )

    return value


def _require_non_negative_integer(
    value: Any,
    label: str,
) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
    ):
        raise InformationUnitAnchorError(
            f"{label} must be a non-negative integer."
        )

    return value


def _require_positive_integer(
    value: Any,
    label: str,
) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 1
    ):
        raise InformationUnitAnchorError(
            f"{label} must be a positive integer."
        )

    return value


def _require_utc_timestamp(
    value: Any,
    label: str,
) -> str:
    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None
    ):
        raise InformationUnitValidationError(
            f"{label} must be an ISO 8601 UTC timestamp "
            "ending in Z."
        )

    try:
        parsed = datetime.fromisoformat(
            value.removesuffix("Z") + "+00:00"
        )
    except ValueError as exc:
        raise InformationUnitValidationError(
            f"{label} must be a valid UTC timestamp."
        ) from exc

    if parsed.utcoffset() is None:
        raise InformationUnitValidationError(
            f"{label} must contain UTC timezone information."
        )

    return value


def _require_exact_object(
    value: Any,
    fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InformationUnitValidationError(
            f"{label} must be a JSON object."
        )

    actual = set(value)
    missing = sorted(fields - actual)
    unknown = sorted(actual - fields)
    problems: list[str] = []

    if missing:
        problems.append(
            "missing " + ", ".join(missing)
        )

    if unknown:
        problems.append(
            "unknown " + ", ".join(unknown)
        )

    if problems:
        raise InformationUnitValidationError(
            f"{label} fields are invalid: "
            f"{'; '.join(problems)}."
        )

    return value


def _require_list(
    value: Any,
    label: str,
) -> list[Any]:
    if not isinstance(value, list):
        raise InformationUnitValidationError(
            f"{label} must be a JSON list."
        )

    return value


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise InformationUnitValidationError(
                f"Duplicate JSON field: {key!r}."
            )

        result[key] = value

    return result