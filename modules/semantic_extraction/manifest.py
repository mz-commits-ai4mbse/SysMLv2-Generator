"""Validate and serialize persona-specific semantic extraction results.

This module validates one immutable result emitted by one configured
extraction persona run. It does not calculate consensus, final confidence,
review status, terminology mappings or Framework Assignments.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from hashlib import sha256
import json
import re
from typing import Any

from modules.information_units.identifiers import (
    validate_information_unit_id,
)
from modules.information_units.types import (
    InformationUnit,
    InformationUnitSourceAnchor,
)
from modules.project_sources.identifiers import validate_source_id
from modules.project_workspace.identifiers import is_valid_project_id
from modules.source_projection.identifiers import (
    segment_id_sequence,
    validate_segment_id,
    validate_source_projection_id,
)
from modules.source_projection.types import (
    SourceProjectionArtifact,
)

from .errors import (
    DuplicateInformationUnitCandidateError,
    InformationUnitCandidateAnchorError,
    InformationUnitCandidateAssumptionError,
    InformationUnitCandidateDerivationError,
    NoCandidateRationaleError,
    SemanticExtractionReferenceError,
    SemanticExtractionValidationError,
)
from .identifiers import (
    format_information_unit_candidate_id,
    validate_information_unit_candidate_id,
)
from .types import (
    EPISTEMIC_CLASSES,
    INFORMATION_TYPES,
    STATEMENT_MODALITIES,
    InformationUnitCandidate,
    SemanticExtractionAgentResult,
)


SEMANTIC_EXTRACTION_AGENT_RESULT_SCHEMA_VERSION = "1.0.0"

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

_AGENT_RESULT_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "source_id",
        "source_projection_id",
        "team_id",
        "agent_id",
        "persona_id",
        "persona_run_index",
        "persona_configuration_fingerprint",
        "llm_provider",
        "llm_model",
        "prompt_schema_version",
        "candidates",
        "no_candidate_rationale",
        "created_at",
    }
)
_CANDIDATE_FIELDS = frozenset(
    {
        "candidate_id",
        "source_anchors",
        "source_excerpt",
        "interpreted_statement",
        "information_type",
        "statement_modality",
        "epistemic_class",
        "supporting_information_unit_ids",
        "derivation_rationale",
        "missing_evidence",
        "extraction_rationale",
        "uncertainties",
    }
)
_SOURCE_ANCHOR_FIELDS = frozenset(
    {
        "segment_id",
        "start_offset",
        "end_offset",
    }
)


def create_information_unit_candidate(
    *,
    candidate_id: str,
    source_anchors: tuple[
        InformationUnitSourceAnchor,
        ...
    ],
    source_excerpt: str,
    interpreted_statement: str,
    information_type: str,
    statement_modality: str,
    epistemic_class: str,
    extraction_rationale: str,
    supporting_information_unit_ids: tuple[str, ...] = (),
    derivation_rationale: str | None = None,
    missing_evidence: str | None = None,
    uncertainties: tuple[str, ...] = (),
) -> InformationUnitCandidate:
    """Create one structurally validated result-local candidate."""

    return parse_information_unit_candidate(
        {
            "candidate_id": candidate_id,
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
            "extraction_rationale": extraction_rationale,
            "uncertainties": list(uncertainties),
        }
    )


def create_semantic_extraction_agent_result(
    *,
    project_id: str,
    source_id: str,
    source_projection_id: str,
    team_id: str,
    agent_id: str,
    persona_id: str,
    persona_run_index: int,
    persona_configuration_fingerprint: str,
    llm_provider: str,
    llm_model: str,
    prompt_schema_version: str,
    candidates: tuple[InformationUnitCandidate, ...],
    no_candidate_rationale: str | None,
    timestamp: str,
) -> SemanticExtractionAgentResult:
    """Create one validated immutable persona-run result."""

    if not isinstance(candidates, tuple):
        raise SemanticExtractionValidationError(
            "candidates must be a tuple of "
            "InformationUnitCandidate instances."
        )

    return parse_semantic_extraction_agent_result(
        {
            "schema_version": (
                SEMANTIC_EXTRACTION_AGENT_RESULT_SCHEMA_VERSION
            ),
            "project_id": project_id,
            "source_id": source_id,
            "source_projection_id": source_projection_id,
            "team_id": team_id,
            "agent_id": agent_id,
            "persona_id": persona_id,
            "persona_run_index": persona_run_index,
            "persona_configuration_fingerprint": (
                persona_configuration_fingerprint
            ),
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "prompt_schema_version": prompt_schema_version,
            "candidates": [
                _candidate_payload(candidate)
                for candidate in candidates
            ],
            "no_candidate_rationale": no_candidate_rationale,
            "created_at": timestamp,
        },
        expected_project_id=project_id,
        expected_source_id=source_id,
        expected_source_projection_id=source_projection_id,
        expected_team_id=team_id,
        expected_agent_id=agent_id,
        expected_persona_id=persona_id,
        expected_persona_run_index=persona_run_index,
    )


def parse_information_unit_candidate(
    payload: Any,
) -> InformationUnitCandidate:
    """Parse and validate one embedded candidate payload."""

    item = _require_exact_object(
        payload,
        _CANDIDATE_FIELDS,
        "Information Unit Candidate",
    )
    candidate_id = _require_candidate_id(
        item["candidate_id"],
        "candidate_id",
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
            item["supporting_information_unit_ids"]
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
    extraction_rationale = _require_stored_text(
        item["extraction_rationale"],
        "extraction_rationale",
    )
    uncertainties = _parse_uncertainties(
        item["uncertainties"]
    )

    _validate_epistemic_evidence(
        epistemic_class=epistemic_class,
        supporting_information_unit_ids=(
            supporting_information_unit_ids
        ),
        derivation_rationale=derivation_rationale,
        missing_evidence=missing_evidence,
    )

    return InformationUnitCandidate(
        candidate_id=candidate_id,
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
        extraction_rationale=extraction_rationale,
        uncertainties=uncertainties,
    )


def parse_semantic_extraction_agent_result(
    payload: Any,
    *,
    expected_project_id: str | None = None,
    expected_source_id: str | None = None,
    expected_source_projection_id: str | None = None,
    expected_team_id: str | None = None,
    expected_agent_id: str | None = None,
    expected_persona_id: str | None = None,
    expected_persona_run_index: int | None = None,
) -> SemanticExtractionAgentResult:
    """Parse and validate one persona-specific extraction result."""

    item = _require_exact_object(
        payload,
        _AGENT_RESULT_FIELDS,
        "Semantic Extraction Agent Result",
    )
    schema_version = item["schema_version"]

    if (
        schema_version
        != SEMANTIC_EXTRACTION_AGENT_RESULT_SCHEMA_VERSION
    ):
        raise SemanticExtractionValidationError(
            "Unsupported Semantic Extraction Agent Result "
            f"schema_version: {schema_version!r}."
        )

    project_id = _require_project_id(
        item["project_id"],
        "project_id",
    )
    source_id = _require_source_id(
        item["source_id"],
        "source_id",
    )
    source_projection_id = _require_source_projection_id(
        item["source_projection_id"],
        "source_projection_id",
    )
    team_id = _require_stored_text(
        item["team_id"],
        "team_id",
    )
    agent_id = _require_stored_text(
        item["agent_id"],
        "agent_id",
    )
    persona_id = _require_stored_text(
        item["persona_id"],
        "persona_id",
    )
    persona_run_index = _require_positive_integer(
        item["persona_run_index"],
        "persona_run_index",
    )
    persona_configuration_fingerprint = _require_sha256(
        item["persona_configuration_fingerprint"],
        "persona_configuration_fingerprint",
    )
    llm_provider = _require_stored_text(
        item["llm_provider"],
        "llm_provider",
    )
    llm_model = _require_stored_text(
        item["llm_model"],
        "llm_model",
    )
    prompt_schema_version = _require_semantic_version(
        item["prompt_schema_version"],
        "prompt_schema_version",
    )
    candidates = tuple(
        parse_information_unit_candidate(candidate)
        for candidate in _require_list(
            item["candidates"],
            "candidates",
        )
    )
    no_candidate_rationale = _require_optional_text(
        item["no_candidate_rationale"],
        "no_candidate_rationale",
    )
    created_at = _require_utc_timestamp(
        item["created_at"],
        "created_at",
    )

    _require_expected_value(
        project_id,
        expected_project_id,
        _require_project_id,
        "project_id",
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
    _require_expected_value(
        team_id,
        expected_team_id,
        _require_stored_text,
        "team_id",
    )
    _require_expected_value(
        agent_id,
        expected_agent_id,
        _require_stored_text,
        "agent_id",
    )
    _require_expected_value(
        persona_id,
        expected_persona_id,
        _require_stored_text,
        "persona_id",
    )
    _require_expected_run_index(
        persona_run_index,
        expected_persona_run_index,
    )
    _validate_candidate_collection(
        candidates,
        no_candidate_rationale,
    )

    return SemanticExtractionAgentResult(
        schema_version=schema_version,
        project_id=project_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        team_id=team_id,
        agent_id=agent_id,
        persona_id=persona_id,
        persona_run_index=persona_run_index,
        persona_configuration_fingerprint=(
            persona_configuration_fingerprint
        ),
        llm_provider=llm_provider,
        llm_model=llm_model,
        prompt_schema_version=prompt_schema_version,
        candidates=candidates,
        no_candidate_rationale=no_candidate_rationale,
        created_at=created_at,
    )


def semantic_extraction_agent_result_from_json(
    text: str,
    *,
    expected_project_id: str | None = None,
    expected_source_id: str | None = None,
    expected_source_projection_id: str | None = None,
    expected_team_id: str | None = None,
    expected_agent_id: str | None = None,
    expected_persona_id: str | None = None,
    expected_persona_run_index: int | None = None,
) -> SemanticExtractionAgentResult:
    """Parse one strict Semantic Extraction Agent Result JSON string."""

    if not isinstance(text, str):
        raise SemanticExtractionValidationError(
            "Semantic Extraction Agent Result JSON input "
            "must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except SemanticExtractionValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise SemanticExtractionValidationError(
            "Semantic Extraction Agent Result contains "
            f"invalid JSON: {exc}."
        ) from exc

    return parse_semantic_extraction_agent_result(
        payload,
        expected_project_id=expected_project_id,
        expected_source_id=expected_source_id,
        expected_source_projection_id=(
            expected_source_projection_id
        ),
        expected_team_id=expected_team_id,
        expected_agent_id=expected_agent_id,
        expected_persona_id=expected_persona_id,
        expected_persona_run_index=(
            expected_persona_run_index
        ),
    )


def validate_semantic_extraction_agent_result(
    result: SemanticExtractionAgentResult,
) -> None:
    """Validate one immutable extraction result instance."""

    semantic_extraction_agent_result_to_dict(result)


def semantic_extraction_agent_result_to_dict(
    result: SemanticExtractionAgentResult,
) -> dict[str, Any]:
    """Return the canonical JSON-compatible representation."""

    if not isinstance(result, SemanticExtractionAgentResult):
        raise SemanticExtractionValidationError(
            "result must be a SemanticExtractionAgentResult "
            "instance."
        )

    payload = _agent_result_payload(result)
    validated = parse_semantic_extraction_agent_result(payload)
    return _agent_result_payload(validated)


def semantic_extraction_agent_result_to_json(
    result: SemanticExtractionAgentResult,
) -> str:
    """Serialize one extraction result deterministically."""

    return (
        json.dumps(
            semantic_extraction_agent_result_to_dict(result),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def calculate_information_unit_candidate_fingerprint(
    candidate: InformationUnitCandidate,
) -> str:
    """Hash stable professional content, excluding run-local analysis."""

    if not isinstance(candidate, InformationUnitCandidate):
        raise SemanticExtractionValidationError(
            "candidate must be an InformationUnitCandidate "
            "instance."
        )

    validated = parse_information_unit_candidate(
        _candidate_payload(candidate)
    )
    payload = {
        "source_anchors": [
            _source_anchor_payload(anchor)
            for anchor in validated.source_anchors
        ],
        "source_excerpt": validated.source_excerpt,
        "interpreted_statement": (
            validated.interpreted_statement
        ),
        "information_type": validated.information_type,
        "statement_modality": validated.statement_modality,
        "epistemic_class": validated.epistemic_class,
        "supporting_information_unit_ids": list(
            validated.supporting_information_unit_ids
        ),
        "derivation_rationale": (
            validated.derivation_rationale
        ),
        "missing_evidence": validated.missing_evidence,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def validate_semantic_extraction_agent_result_context(
    result: SemanticExtractionAgentResult,
    *,
    source_projection: SourceProjectionArtifact,
    supporting_information_units: Iterable[
        InformationUnit
    ] = (),
) -> None:
    """Validate anchors and references against resolved project artifacts."""

    validate_semantic_extraction_agent_result(result)

    if not isinstance(
        source_projection,
        SourceProjectionArtifact,
    ):
        raise SemanticExtractionReferenceError(
            "source_projection must be a "
            "SourceProjectionArtifact instance."
        )

    manifest = source_projection.manifest

    if manifest.project_id != result.project_id:
        raise SemanticExtractionReferenceError(
            "Source Projection belongs to a different project."
        )

    if manifest.source_id != result.source_id:
        raise SemanticExtractionReferenceError(
            "Source Projection belongs to a different source."
        )

    if (
        manifest.source_projection_id
        != result.source_projection_id
    ):
        raise SemanticExtractionReferenceError(
            "Source Projection ID does not match the "
            "Semantic Extraction Agent Result."
        )

    if manifest.projection_result == "unavailable":
        raise SemanticExtractionReferenceError(
            "An unavailable Source Projection cannot be used "
            "for semantic extraction."
        )

    known_units = _index_supporting_information_units(
        supporting_information_units
    )

    for candidate in result.candidates:
        _validate_candidate_source_excerpt(
            candidate,
            source_projection,
        )
        _validate_candidate_support_references(
            candidate,
            result=result,
            known_units=known_units,
        )


def _validate_candidate_collection(
    candidates: tuple[InformationUnitCandidate, ...],
    no_candidate_rationale: str | None,
) -> None:
    if candidates:
        if no_candidate_rationale is not None:
            raise NoCandidateRationaleError(
                "no_candidate_rationale must be null when "
                "candidates are present."
            )
    elif no_candidate_rationale is None:
        raise NoCandidateRationaleError(
            "A result without candidates requires "
            "no_candidate_rationale."
        )

    actual_ids = tuple(
        candidate.candidate_id
        for candidate in candidates
    )
    expected_ids = tuple(
        format_information_unit_candidate_id(index)
        for index in range(1, len(candidates) + 1)
    )

    if actual_ids != expected_ids:
        raise SemanticExtractionValidationError(
            "candidate_id values must start at IUC-000001 "
            "and remain gapless in candidate order."
        )

    source_order = tuple(
        _candidate_source_order_key(candidate)
        for candidate in candidates
    )

    if source_order != tuple(sorted(source_order)):
        raise InformationUnitCandidateAnchorError(
            "candidates must be ordered by their first "
            "Source Projection anchor."
        )

    fingerprint_owner: dict[str, str] = {}

    for candidate in candidates:
        fingerprint = (
            calculate_information_unit_candidate_fingerprint(
                candidate
            )
        )
        existing_id = fingerprint_owner.get(fingerprint)

        if existing_id is not None:
            raise DuplicateInformationUnitCandidateError(
                "Professional candidate content is duplicated "
                f"by {existing_id} and "
                f"{candidate.candidate_id}."
            )

        fingerprint_owner[fingerprint] = (
            candidate.candidate_id
        )


def _parse_source_anchors(
    value: Any,
) -> tuple[InformationUnitSourceAnchor, ...]:
    items = _require_list(value, "source_anchors")

    if not items:
        raise InformationUnitCandidateAnchorError(
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
        end_offset = _require_positive_anchor_integer(
            anchor["end_offset"],
            f"{label}.end_offset",
        )

        if end_offset <= start_offset:
            raise InformationUnitCandidateAnchorError(
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
        raise InformationUnitCandidateAnchorError(
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
            raise InformationUnitCandidateAnchorError(
                "source_anchors must not overlap within "
                f"segment {anchor.segment_id}."
            )

        previous_end_by_segment[anchor.segment_id] = (
            anchor.end_offset
        )

    return tuple(anchors)


def _parse_supporting_information_unit_ids(
    value: Any,
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
        raise InformationUnitCandidateDerivationError(
            "supporting_information_unit_ids must not "
            "contain duplicates."
        )

    if identifiers != tuple(sorted(identifiers)):
        raise InformationUnitCandidateDerivationError(
            "supporting_information_unit_ids must be "
            "ordered by Information Unit ID."
        )

    return identifiers


def _parse_uncertainties(
    value: Any,
) -> tuple[str, ...]:
    uncertainties = tuple(
        _require_stored_text(
            uncertainty,
            f"uncertainties[{index}]",
        )
        for index, uncertainty in enumerate(
            _require_list(value, "uncertainties")
        )
    )

    if len(uncertainties) != len(set(uncertainties)):
        raise SemanticExtractionValidationError(
            "uncertainties must not contain duplicates."
        )

    return uncertainties


def _validate_epistemic_evidence(
    *,
    epistemic_class: str,
    supporting_information_unit_ids: tuple[str, ...],
    derivation_rationale: str | None,
    missing_evidence: str | None,
) -> None:
    if epistemic_class == "derivation":
        if not supporting_information_unit_ids:
            raise InformationUnitCandidateDerivationError(
                "A derivation candidate requires at least one "
                "supporting Information Unit ID."
            )

        if derivation_rationale is None:
            raise InformationUnitCandidateDerivationError(
                "A derivation candidate requires "
                "derivation_rationale."
            )

        if missing_evidence is not None:
            raise InformationUnitCandidateDerivationError(
                "A derivation candidate must not declare "
                "missing_evidence."
            )

        return

    if epistemic_class == "assumption":
        if missing_evidence is None:
            raise InformationUnitCandidateAssumptionError(
                "An assumption candidate requires "
                "missing_evidence."
            )

        if supporting_information_unit_ids:
            raise InformationUnitCandidateAssumptionError(
                "An assumption candidate must not use "
                "derivation support."
            )

        if derivation_rationale is not None:
            raise InformationUnitCandidateAssumptionError(
                "An assumption candidate must not declare "
                "derivation_rationale."
            )

        return

    if supporting_information_unit_ids:
        raise InformationUnitCandidateDerivationError(
            f"{epistemic_class!r} candidates must not use "
            "derivation support."
        )

    if derivation_rationale is not None:
        raise InformationUnitCandidateDerivationError(
            f"{epistemic_class!r} candidates must not declare "
            "derivation_rationale."
        )

    if missing_evidence is not None:
        raise InformationUnitCandidateAssumptionError(
            f"{epistemic_class!r} candidates must not declare "
            "missing_evidence."
        )


def _validate_candidate_source_excerpt(
    candidate: InformationUnitCandidate,
    source_projection: SourceProjectionArtifact,
) -> None:
    segment_by_id = {
        segment.segment_id: segment
        for segment in source_projection.manifest.segments
    }
    selected_text: list[str] = []

    for anchor in candidate.source_anchors:
        segment = segment_by_id.get(anchor.segment_id)

        if segment is None:
            raise InformationUnitCandidateAnchorError(
                "Source anchor references unknown segment "
                f"{anchor.segment_id}."
            )

        segment_text = source_projection.content[
            segment.start_offset:segment.end_offset
        ]

        if anchor.end_offset > len(segment_text):
            raise InformationUnitCandidateAnchorError(
                "Source anchor range exceeds segment "
                f"{anchor.segment_id}."
            )

        selected_text.append(
            segment_text[
                anchor.start_offset:anchor.end_offset
            ]
        )

    expected_excerpt = "".join(selected_text)

    if candidate.source_excerpt != expected_excerpt:
        raise InformationUnitCandidateAnchorError(
            "source_excerpt does not equal the unchanged "
            "concatenation of its Source Projection anchors."
        )


def _index_supporting_information_units(
    values: Iterable[InformationUnit],
) -> dict[str, InformationUnit]:
    if isinstance(values, (str, bytes)):
        raise SemanticExtractionReferenceError(
            "supporting_information_units must be an iterable "
            "of InformationUnit instances."
        )

    try:
        information_units = tuple(values)
    except TypeError as exc:
        raise SemanticExtractionReferenceError(
            "supporting_information_units must be iterable."
        ) from exc

    indexed: dict[str, InformationUnit] = {}

    for information_unit in information_units:
        if not isinstance(information_unit, InformationUnit):
            raise SemanticExtractionReferenceError(
                "supporting_information_units must contain "
                "InformationUnit instances."
            )

        if information_unit.information_unit_id in indexed:
            raise SemanticExtractionReferenceError(
                "supporting_information_units must not contain "
                "duplicate Information Unit IDs."
            )

        indexed[
            information_unit.information_unit_id
        ] = information_unit

    return indexed


def _validate_candidate_support_references(
    candidate: InformationUnitCandidate,
    *,
    result: SemanticExtractionAgentResult,
    known_units: dict[str, InformationUnit],
) -> None:
    for supporting_id in (
        candidate.supporting_information_unit_ids
    ):
        supporting_unit = known_units.get(supporting_id)

        if supporting_unit is None:
            raise SemanticExtractionReferenceError(
                "Supporting Information Unit was not supplied: "
                f"{supporting_id}."
            )

        if supporting_unit.project_id != result.project_id:
            raise SemanticExtractionReferenceError(
                "Supporting Information Unit belongs to a "
                "different project."
            )

        if supporting_unit.source_id != result.source_id:
            raise SemanticExtractionReferenceError(
                "P4 derivation support must belong to the same "
                "engineering source."
            )


def _candidate_source_order_key(
    candidate: InformationUnitCandidate,
) -> tuple[int, int, int]:
    first_anchor = candidate.source_anchors[0]
    return (
        segment_id_sequence(first_anchor.segment_id),
        first_anchor.start_offset,
        first_anchor.end_offset,
    )


def _agent_result_payload(
    result: SemanticExtractionAgentResult,
) -> dict[str, Any]:
    return {
        "schema_version": result.schema_version,
        "project_id": result.project_id,
        "source_id": result.source_id,
        "source_projection_id": result.source_projection_id,
        "team_id": result.team_id,
        "agent_id": result.agent_id,
        "persona_id": result.persona_id,
        "persona_run_index": result.persona_run_index,
        "persona_configuration_fingerprint": (
            result.persona_configuration_fingerprint
        ),
        "llm_provider": result.llm_provider,
        "llm_model": result.llm_model,
        "prompt_schema_version": result.prompt_schema_version,
        "candidates": [
            _candidate_payload(candidate)
            for candidate in result.candidates
        ],
        "no_candidate_rationale": (
            result.no_candidate_rationale
        ),
        "created_at": result.created_at,
    }


def _candidate_payload(
    candidate: InformationUnitCandidate,
) -> dict[str, Any]:
    if not isinstance(candidate, InformationUnitCandidate):
        raise SemanticExtractionValidationError(
            "candidates must contain "
            "InformationUnitCandidate instances."
        )

    return {
        "candidate_id": candidate.candidate_id,
        "source_anchors": [
            _source_anchor_payload(anchor)
            for anchor in candidate.source_anchors
        ],
        "source_excerpt": candidate.source_excerpt,
        "interpreted_statement": (
            candidate.interpreted_statement
        ),
        "information_type": candidate.information_type,
        "statement_modality": candidate.statement_modality,
        "epistemic_class": candidate.epistemic_class,
        "supporting_information_unit_ids": list(
            candidate.supporting_information_unit_ids
        ),
        "derivation_rationale": (
            candidate.derivation_rationale
        ),
        "missing_evidence": candidate.missing_evidence,
        "extraction_rationale": (
            candidate.extraction_rationale
        ),
        "uncertainties": list(candidate.uncertainties),
    }


def _source_anchor_payload(
    anchor: InformationUnitSourceAnchor,
) -> dict[str, Any]:
    if not isinstance(anchor, InformationUnitSourceAnchor):
        raise InformationUnitCandidateAnchorError(
            "source_anchors must contain "
            "InformationUnitSourceAnchor instances."
        )

    return {
        "segment_id": anchor.segment_id,
        "start_offset": anchor.start_offset,
        "end_offset": anchor.end_offset,
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
        raise SemanticExtractionValidationError(
            f"Semantic Extraction Agent Result {label} does "
            "not match its expected context: "
            f"{actual!r} != {validated_expected!r}."
        )


def _require_expected_run_index(
    actual: int,
    expected: int | None,
) -> None:
    if expected is None:
        return

    validated_expected = _require_positive_integer(
        expected,
        "expected_persona_run_index",
    )

    if actual != validated_expected:
        raise SemanticExtractionValidationError(
            "Semantic Extraction Agent Result "
            "persona_run_index does not match its expected "
            f"context: {actual!r} != {validated_expected!r}."
        )


def _require_project_id(
    value: Any,
    label: str,
) -> str:
    if not is_valid_project_id(value):
        raise SemanticExtractionValidationError(
            f"{label} must contain exactly six digits."
        )

    return value


def _require_candidate_id(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_information_unit_candidate_id(value)
    except Exception as exc:
        raise SemanticExtractionValidationError(
            f"{label} must be a valid Information Unit "
            "Candidate ID."
        ) from exc


def _require_information_unit_id(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_information_unit_id(value)
    except Exception as exc:
        raise InformationUnitCandidateDerivationError(
            f"{label} must be a valid Information Unit ID."
        ) from exc


def _require_source_id(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_source_id(value)
    except Exception as exc:
        raise SemanticExtractionValidationError(
            f"{label} must be a valid Source ID."
        ) from exc


def _require_source_projection_id(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_source_projection_id(value)
    except Exception as exc:
        raise SemanticExtractionValidationError(
            f"{label} must be a valid Source Projection ID."
        ) from exc


def _require_segment_id(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_segment_id(value)
    except Exception as exc:
        raise InformationUnitCandidateAnchorError(
            f"{label} must be a valid Segment ID."
        ) from exc


def _require_choice(
    value: Any,
    allowed: frozenset[str],
    label: str,
) -> str:
    text = _require_stored_text(value, label)

    if text not in allowed:
        raise SemanticExtractionValidationError(
            f"{label} must be one of: "
            f"{', '.join(sorted(allowed))}."
        )

    return text


def _require_stored_text(
    value: Any,
    label: str,
) -> str:
    if not isinstance(value, str):
        raise SemanticExtractionValidationError(
            f"{label} must be a string."
        )

    if not value.strip():
        raise SemanticExtractionValidationError(
            f"{label} must not be empty."
        )

    if value != value.strip():
        raise SemanticExtractionValidationError(
            f"{label} must not have leading or trailing "
            "whitespace."
        )

    if "\x00" in value or "\r" in value:
        raise SemanticExtractionValidationError(
            f"{label} contains unsupported control characters."
        )

    return value


def _require_source_excerpt(
    value: Any,
) -> str:
    if not isinstance(value, str):
        raise SemanticExtractionValidationError(
            "source_excerpt must be a string."
        )

    if not value.strip():
        raise SemanticExtractionValidationError(
            "source_excerpt must contain visible source text."
        )

    if "\x00" in value or "\r" in value:
        raise SemanticExtractionValidationError(
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
        raise SemanticExtractionValidationError(
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
        raise SemanticExtractionValidationError(
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
        raise InformationUnitCandidateAnchorError(
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
        raise SemanticExtractionValidationError(
            f"{label} must be a positive integer."
        )

    return value


def _require_positive_anchor_integer(
    value: Any,
    label: str,
) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 1
    ):
        raise InformationUnitCandidateAnchorError(
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
        raise SemanticExtractionValidationError(
            f"{label} must be an ISO 8601 UTC timestamp "
            "ending in Z."
        )

    try:
        parsed = datetime.fromisoformat(
            value.removesuffix("Z") + "+00:00"
        )
    except ValueError as exc:
        raise SemanticExtractionValidationError(
            f"{label} must be a valid UTC timestamp."
        ) from exc

    if parsed.utcoffset() is None:
        raise SemanticExtractionValidationError(
            f"{label} must contain UTC timezone information."
        )

    return value


def _require_exact_object(
    value: Any,
    fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SemanticExtractionValidationError(
            f"{label} must be a JSON object."
        )

    actual = set(value)
    missing = sorted(fields - actual)
    unknown = sorted(actual - fields)
    problems: list[str] = []

    if missing:
        problems.append("missing " + ", ".join(missing))

    if unknown:
        problems.append("unknown " + ", ".join(unknown))

    if problems:
        raise SemanticExtractionValidationError(
            f"{label} fields are invalid: "
            f"{'; '.join(problems)}."
        )

    return value


def _require_list(
    value: Any,
    label: str,
) -> list[Any]:
    if not isinstance(value, list):
        raise SemanticExtractionValidationError(
            f"{label} must be a JSON list."
        )

    return value


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise SemanticExtractionValidationError(
                f"Duplicate JSON field: {key!r}."
            )

        result[key] = value

    return result