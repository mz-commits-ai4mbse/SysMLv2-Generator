"""Strict manifest for persona-specific terminology mapping results."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
import json
import re
from typing import Any
from urllib.parse import urlparse

from modules.information_units.types import InformationUnit

from .errors import (
    DuplicateTerminologyMappingAgentCandidateError,
    TerminologyMappingIntegrityError,
    TerminologyMappingReferenceError,
    TerminologyMappingValidationError,
)
from .identifiers import (
    format_terminology_mapping_agent_candidate_id,
    validate_terminology_mapping_agent_candidate_id,
)
from .types import (
    TERMINOLOGY_MAPPING_BASIS_TYPES,
    TERMINOLOGY_MAPPING_RELATIONS,
    TERMINOLOGY_MAPPING_STATUSES,
    TERMINOLOGY_MAPPING_TARGET_KINDS,
    TERMINOLOGY_TEXT_FIELDS,
    TerminologyMappingAgentCandidate,
    TerminologyMappingAgentResult,
    TerminologyMappingBasis,
    TerminologyMappingProposal,
    TerminologyMappingTarget,
    TerminologyOccurrence,
)


TERMINOLOGY_MAPPING_AGENT_RESULT_SCHEMA_VERSION = "1.0.0"

_PROJECT_ID_PATTERN = re.compile(r"^[0-9]{6}$")
_SOURCE_ID_PATTERN = re.compile(r"^SRC-[0-9]{6}$")
_SOURCE_PROJECTION_ID_PATTERN = re.compile(
    r"^SP-[0-9]{6}$"
)
_INFORMATION_UNIT_ID_PATTERN = re.compile(
    r"^IU-[0-9]{6}$"
)
_PROJECT_CONCEPT_ID_PATTERN = re.compile(
    r"^PC-[0-9]{6}$"
)
_TURING_CORE_CONCEPT_ID_PATTERN = re.compile(
    r"^TC-[0-9]{6}$"
)
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SEMANTIC_VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+$"
)
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_RESULT_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "source_id",
        "source_projection_id",
        "information_unit_id",
        "team_id",
        "agent_id",
        "persona_id",
        "persona_run_index",
        "persona_configuration_fingerprint",
        "llm_provider",
        "llm_model",
        "prompt_schema_version",
        "ontology_registry_version",
        "reference_concept_index_version",
        "turing_core_version",
        "project_glossary_revision",
        "candidates",
        "no_candidate_rationale",
        "created_at",
    }
)
_CANDIDATE_FIELDS = frozenset(
    {
        "terminology_mapping_agent_candidate_id",
        "occurrence",
        "mapping_status",
        "proposals",
        "rationale",
        "uncertainties",
    }
)
_OCCURRENCE_FIELDS = frozenset(
    {
        "information_unit_id",
        "text_field",
        "start_offset",
        "end_offset",
        "term_text",
    }
)
_PROPOSAL_FIELDS = frozenset(
    {
        "mapping_relation",
        "target",
        "mapping_bases",
        "rationale",
    }
)
_TARGET_FIELDS = frozenset(
    {
        "target_kind",
        "display_label",
        "project_concept_id",
        "project_concept_revision",
        "turing_core_concept_id",
        "reference_system_id",
        "reference_system_version",
        "reference_concept_iri",
    }
)
_BASIS_FIELDS = frozenset(
    {
        "basis_type",
        "reference_id",
        "reference_version",
        "rationale",
    }
)


def create_terminology_occurrence(
    information_unit: InformationUnit,
    *,
    text_field: str,
    start_offset: int,
    end_offset: int,
) -> TerminologyOccurrence:
    """Create an exact, end-exclusive term occurrence from one IU field."""

    _require_information_unit(information_unit)
    selected_field = _require_choice(
        text_field,
        TERMINOLOGY_TEXT_FIELDS,
        "text_field",
    )
    start = _require_non_negative_integer(
        start_offset,
        "start_offset",
    )
    end = _require_positive_integer(
        end_offset,
        "end_offset",
    )
    text = getattr(information_unit, selected_field)

    if start >= end:
        raise TerminologyMappingValidationError(
            "Terminology occurrence start_offset must be less "
            "than end_offset."
        )
    if end > len(text):
        raise TerminologyMappingReferenceError(
            "Terminology occurrence exceeds the selected "
            "Information Unit field."
        )
    term_text = text[start:end]
    _require_stored_text(term_text, "term_text")

    return TerminologyOccurrence(
        information_unit_id=(
            information_unit.information_unit_id
        ),
        text_field=selected_field,
        start_offset=start,
        end_offset=end,
        term_text=term_text,
    )


def create_terminology_mapping_target(
    *,
    target_kind: str,
    display_label: str,
    project_concept_id: str | None = None,
    project_concept_revision: int | None = None,
    turing_core_concept_id: str | None = None,
    reference_system_id: str | None = None,
    reference_system_version: str | None = None,
    reference_concept_iri: str | None = None,
) -> TerminologyMappingTarget:
    """Create and validate one explicitly typed mapping target."""

    target = TerminologyMappingTarget(
        target_kind=target_kind,
        display_label=display_label,
        project_concept_id=project_concept_id,
        project_concept_revision=project_concept_revision,
        turing_core_concept_id=turing_core_concept_id,
        reference_system_id=reference_system_id,
        reference_system_version=reference_system_version,
        reference_concept_iri=reference_concept_iri,
    )
    return _parse_target(_target_payload(target))


def create_terminology_mapping_basis(
    *,
    basis_type: str,
    reference_id: str,
    reference_version: str | None,
    rationale: str,
) -> TerminologyMappingBasis:
    """Create one versioned evidence basis for a mapping proposal."""

    basis = TerminologyMappingBasis(
        basis_type=basis_type,
        reference_id=reference_id,
        reference_version=reference_version,
        rationale=rationale,
    )
    return _parse_basis(_basis_payload(basis))


def create_terminology_mapping_proposal(
    *,
    mapping_relation: str,
    target: TerminologyMappingTarget | None,
    mapping_bases: Iterable[TerminologyMappingBasis],
    rationale: str,
) -> TerminologyMappingProposal:
    """Create one non-authoritative mapping proposal."""

    bases = _tuple_of_instances(
        mapping_bases,
        TerminologyMappingBasis,
        "mapping_bases",
    )
    proposal = TerminologyMappingProposal(
        mapping_relation=mapping_relation,
        target=target,
        mapping_bases=bases,
        rationale=rationale,
    )
    return _parse_proposal(_proposal_payload(proposal))


def create_terminology_mapping_agent_candidate(
    *,
    terminology_mapping_agent_candidate_id: str,
    occurrence: TerminologyOccurrence,
    mapping_status: str,
    proposals: Iterable[TerminologyMappingProposal],
    rationale: str,
    uncertainties: Iterable[str] = (),
) -> TerminologyMappingAgentCandidate:
    """Create one result-local candidate without confidence or approval."""

    selected_proposals = _tuple_of_instances(
        proposals,
        TerminologyMappingProposal,
        "proposals",
    )
    selected_uncertainties = _tuple_of_text(
        uncertainties,
        "uncertainties",
    )
    candidate = TerminologyMappingAgentCandidate(
        terminology_mapping_agent_candidate_id=(
            terminology_mapping_agent_candidate_id
        ),
        occurrence=occurrence,
        mapping_status=mapping_status,
        proposals=selected_proposals,
        rationale=rationale,
        uncertainties=selected_uncertainties,
    )
    return _parse_candidate(
        _candidate_payload(candidate),
        expected_candidate_id=(
            terminology_mapping_agent_candidate_id
        ),
        expected_information_unit_id=(
            occurrence.information_unit_id
            if isinstance(occurrence, TerminologyOccurrence)
            else None
        ),
    )


def create_terminology_mapping_agent_result(
    *,
    information_unit: InformationUnit,
    team_id: str,
    agent_id: str,
    persona_id: str,
    persona_run_index: int,
    persona_configuration_fingerprint: str,
    llm_provider: str,
    llm_model: str,
    prompt_schema_version: str,
    ontology_registry_version: str,
    reference_concept_index_version: str,
    turing_core_version: str,
    project_glossary_revision: int,
    candidates: Iterable[TerminologyMappingAgentCandidate],
    no_candidate_rationale: str | None,
    timestamp: str,
) -> TerminologyMappingAgentResult:
    """Create one immutable persona-run mapping result."""

    _require_information_unit(information_unit)
    selected_candidates = _tuple_of_instances(
        candidates,
        TerminologyMappingAgentCandidate,
        "candidates",
    )
    result = TerminologyMappingAgentResult(
        schema_version=(
            TERMINOLOGY_MAPPING_AGENT_RESULT_SCHEMA_VERSION
        ),
        project_id=information_unit.project_id,
        source_id=information_unit.source_id,
        source_projection_id=(
            information_unit.source_projection_id
        ),
        information_unit_id=(
            information_unit.information_unit_id
        ),
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
        ontology_registry_version=ontology_registry_version,
        reference_concept_index_version=(
            reference_concept_index_version
        ),
        turing_core_version=turing_core_version,
        project_glossary_revision=project_glossary_revision,
        candidates=selected_candidates,
        no_candidate_rationale=no_candidate_rationale,
        created_at=timestamp,
    )
    validated = parse_terminology_mapping_agent_result(
        _result_payload(result),
        expected_project_id=information_unit.project_id,
        expected_source_id=information_unit.source_id,
        expected_source_projection_id=(
            information_unit.source_projection_id
        ),
        expected_information_unit_id=(
            information_unit.information_unit_id
        ),
    )
    _validate_occurrences_against_information_unit(
        validated,
        information_unit,
    )
    return validated


def parse_terminology_mapping_agent_result(
    payload: Any,
    *,
    expected_project_id: str | None = None,
    expected_source_id: str | None = None,
    expected_source_projection_id: str | None = None,
    expected_information_unit_id: str | None = None,
    expected_team_id: str | None = None,
    expected_agent_id: str | None = None,
    expected_persona_id: str | None = None,
) -> TerminologyMappingAgentResult:
    """Parse and strictly validate one mapping-agent result payload."""

    item = _require_exact_object(
        payload,
        _RESULT_FIELDS,
        "Terminology Mapping Agent Result",
    )
    schema_version = item["schema_version"]
    if (
        schema_version
        != TERMINOLOGY_MAPPING_AGENT_RESULT_SCHEMA_VERSION
    ):
        raise TerminologyMappingValidationError(
            "Unsupported Terminology Mapping Agent Result "
            f"schema_version: {schema_version!r}."
        )

    project_id = _require_pattern_identifier(
        item["project_id"],
        _PROJECT_ID_PATTERN,
        "project_id",
        "000000",
    )
    source_id = _require_pattern_identifier(
        item["source_id"],
        _SOURCE_ID_PATTERN,
        "source_id",
        "SRC-000000",
    )
    source_projection_id = _require_pattern_identifier(
        item["source_projection_id"],
        _SOURCE_PROJECTION_ID_PATTERN,
        "source_projection_id",
        "SP-000000",
    )
    information_unit_id = _require_pattern_identifier(
        item["information_unit_id"],
        _INFORMATION_UNIT_ID_PATTERN,
        "information_unit_id",
        "IU-000000",
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
    ontology_registry_version = _require_semantic_version(
        item["ontology_registry_version"],
        "ontology_registry_version",
    )
    reference_concept_index_version = (
        _require_semantic_version(
            item["reference_concept_index_version"],
            "reference_concept_index_version",
        )
    )
    turing_core_version = _require_semantic_version(
        item["turing_core_version"],
        "turing_core_version",
    )
    project_glossary_revision = _require_positive_integer(
        item["project_glossary_revision"],
        "project_glossary_revision",
    )

    candidate_payloads = _require_list(
        item["candidates"],
        "candidates",
    )
    candidates = tuple(
        _parse_candidate(
            candidate_payload,
            expected_candidate_id=(
                format_terminology_mapping_agent_candidate_id(
                    index
                )
            ),
            expected_information_unit_id=information_unit_id,
        )
        for index, candidate_payload in enumerate(
            candidate_payloads,
            start=1,
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

    _validate_candidate_collection(candidates)
    if candidates and no_candidate_rationale is not None:
        raise TerminologyMappingIntegrityError(
            "no_candidate_rationale must be null when candidates "
            "are present."
        )
    if not candidates and no_candidate_rationale is None:
        raise TerminologyMappingIntegrityError(
            "no_candidate_rationale is required when no "
            "candidates are present."
        )

    _require_expected(
        project_id,
        expected_project_id,
        "project_id",
    )
    _require_expected(
        source_id,
        expected_source_id,
        "source_id",
    )
    _require_expected(
        source_projection_id,
        expected_source_projection_id,
        "source_projection_id",
    )
    _require_expected(
        information_unit_id,
        expected_information_unit_id,
        "information_unit_id",
    )
    _require_expected(team_id, expected_team_id, "team_id")
    _require_expected(agent_id, expected_agent_id, "agent_id")
    _require_expected(
        persona_id,
        expected_persona_id,
        "persona_id",
    )

    return TerminologyMappingAgentResult(
        schema_version=schema_version,
        project_id=project_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        information_unit_id=information_unit_id,
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
        ontology_registry_version=ontology_registry_version,
        reference_concept_index_version=(
            reference_concept_index_version
        ),
        turing_core_version=turing_core_version,
        project_glossary_revision=project_glossary_revision,
        candidates=candidates,
        no_candidate_rationale=no_candidate_rationale,
        created_at=created_at,
    )


def terminology_mapping_agent_result_from_json(
    text: str,
    **expected_values: str | None,
) -> TerminologyMappingAgentResult:
    """Parse strict JSON without permitting duplicate object keys."""

    if not isinstance(text, str):
        raise TerminologyMappingValidationError(
            "Terminology Mapping Agent Result JSON input must "
            "be a string."
        )
    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except TerminologyMappingValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise TerminologyMappingValidationError(
            "Terminology Mapping Agent Result contains invalid "
            f"JSON: {exc}."
        ) from exc

    return parse_terminology_mapping_agent_result(
        payload,
        **expected_values,
    )


def validate_terminology_mapping_agent_result(
    result: TerminologyMappingAgentResult,
    *,
    information_unit: InformationUnit | None = None,
) -> None:
    """Validate one immutable result and optional IU text binding."""

    validated = parse_terminology_mapping_agent_result(
        _result_payload(result)
    )
    if information_unit is not None:
        _validate_occurrences_against_information_unit(
            validated,
            information_unit,
        )


def terminology_mapping_agent_result_to_dict(
    result: TerminologyMappingAgentResult,
) -> dict[str, Any]:
    """Return the canonical JSON-compatible representation."""

    if not isinstance(result, TerminologyMappingAgentResult):
        raise TerminologyMappingValidationError(
            "result must be a TerminologyMappingAgentResult."
        )
    validated = parse_terminology_mapping_agent_result(
        _result_payload(result)
    )
    return _result_payload(validated)


def terminology_mapping_agent_result_to_json(
    result: TerminologyMappingAgentResult,
) -> str:
    """Serialize one result deterministically."""

    return (
        json.dumps(
            terminology_mapping_agent_result_to_dict(result),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def _parse_candidate(
    payload: Any,
    *,
    expected_candidate_id: str,
    expected_information_unit_id: str | None,
) -> TerminologyMappingAgentCandidate:
    item = _require_exact_object(
        payload,
        _CANDIDATE_FIELDS,
        "Terminology Mapping Agent Candidate",
    )
    candidate_id = (
        validate_terminology_mapping_agent_candidate_id(
            item["terminology_mapping_agent_candidate_id"]
        )
    )
    if candidate_id != expected_candidate_id:
        raise TerminologyMappingIntegrityError(
            "Agent candidate identifiers must be sequential "
            f"without gaps; expected {expected_candidate_id!r}."
        )
    occurrence = _parse_occurrence(
        item["occurrence"],
        expected_information_unit_id=(
            expected_information_unit_id
        ),
    )
    mapping_status = _require_choice(
        item["mapping_status"],
        TERMINOLOGY_MAPPING_STATUSES,
        "mapping_status",
    )
    proposals = tuple(
        _parse_proposal(value)
        for value in _require_list(
            item["proposals"],
            "proposals",
        )
    )
    rationale = _require_stored_text(
        item["rationale"],
        "rationale",
    )
    uncertainties = _parse_text_tuple(
        item["uncertainties"],
        "uncertainties",
    )
    _validate_status_proposals(mapping_status, proposals)

    return TerminologyMappingAgentCandidate(
        terminology_mapping_agent_candidate_id=candidate_id,
        occurrence=occurrence,
        mapping_status=mapping_status,
        proposals=proposals,
        rationale=rationale,
        uncertainties=uncertainties,
    )


def _parse_occurrence(
    payload: Any,
    *,
    expected_information_unit_id: str | None,
) -> TerminologyOccurrence:
    item = _require_exact_object(
        payload,
        _OCCURRENCE_FIELDS,
        "Terminology Occurrence",
    )
    information_unit_id = _require_pattern_identifier(
        item["information_unit_id"],
        _INFORMATION_UNIT_ID_PATTERN,
        "occurrence.information_unit_id",
        "IU-000000",
    )
    _require_expected(
        information_unit_id,
        expected_information_unit_id,
        "occurrence.information_unit_id",
    )
    text_field = _require_choice(
        item["text_field"],
        TERMINOLOGY_TEXT_FIELDS,
        "occurrence.text_field",
    )
    start_offset = _require_non_negative_integer(
        item["start_offset"],
        "occurrence.start_offset",
    )
    end_offset = _require_positive_integer(
        item["end_offset"],
        "occurrence.end_offset",
    )
    if start_offset >= end_offset:
        raise TerminologyMappingValidationError(
            "Occurrence start_offset must be less than "
            "end_offset."
        )
    term_text = _require_stored_text(
        item["term_text"],
        "occurrence.term_text",
    )
    if len(term_text) != end_offset - start_offset:
        raise TerminologyMappingIntegrityError(
            "Occurrence term_text length must equal its offset "
            "range."
        )
    return TerminologyOccurrence(
        information_unit_id=information_unit_id,
        text_field=text_field,
        start_offset=start_offset,
        end_offset=end_offset,
        term_text=term_text,
    )


def _parse_proposal(payload: Any) -> TerminologyMappingProposal:
    item = _require_exact_object(
        payload,
        _PROPOSAL_FIELDS,
        "Terminology Mapping Proposal",
    )
    relation = _require_choice(
        item["mapping_relation"],
        TERMINOLOGY_MAPPING_RELATIONS,
        "mapping_relation",
    )
    target = (
        None
        if item["target"] is None
        else _parse_target(item["target"])
    )
    bases = tuple(
        _parse_basis(value)
        for value in _require_list(
            item["mapping_bases"],
            "mapping_bases",
        )
    )
    rationale = _require_stored_text(
        item["rationale"],
        "proposal.rationale",
    )

    if relation == "no_equivalent":
        if target is not None:
            raise TerminologyMappingIntegrityError(
                "A no_equivalent proposal must not contain a "
                "mapping target."
            )
    elif target is None:
        raise TerminologyMappingIntegrityError(
            "A mapped proposal must contain a mapping target."
        )

    if not bases:
        raise TerminologyMappingIntegrityError(
            "Every mapping proposal requires at least one "
            "mapping basis."
        )
    if len(bases) != len(set(bases)):
        raise TerminologyMappingIntegrityError(
            "Duplicate mapping bases are not allowed."
        )
    _validate_target_basis(target, relation, bases)

    return TerminologyMappingProposal(
        mapping_relation=relation,
        target=target,
        mapping_bases=bases,
        rationale=rationale,
    )


def _parse_target(payload: Any) -> TerminologyMappingTarget:
    item = _require_exact_object(
        payload,
        _TARGET_FIELDS,
        "Terminology Mapping Target",
    )
    target_kind = _require_choice(
        item["target_kind"],
        TERMINOLOGY_MAPPING_TARGET_KINDS,
        "target_kind",
    )
    display_label = _require_stored_text(
        item["display_label"],
        "display_label",
    )
    project_concept_id = _require_optional_pattern_identifier(
        item["project_concept_id"],
        _PROJECT_CONCEPT_ID_PATTERN,
        "project_concept_id",
        "PC-000000",
    )
    project_concept_revision = _require_optional_positive_integer(
        item["project_concept_revision"],
        "project_concept_revision",
    )
    turing_core_concept_id = (
        _require_optional_pattern_identifier(
            item["turing_core_concept_id"],
            _TURING_CORE_CONCEPT_ID_PATTERN,
            "turing_core_concept_id",
            "TC-000000",
        )
    )
    reference_system_id = _require_optional_text(
        item["reference_system_id"],
        "reference_system_id",
    )
    reference_system_version = _require_optional_text(
        item["reference_system_version"],
        "reference_system_version",
    )
    reference_concept_iri = _require_optional_iri(
        item["reference_concept_iri"],
        "reference_concept_iri",
    )

    project_values = (
        project_concept_id,
        project_concept_revision,
    )
    turing_values = (turing_core_concept_id,)
    external_values = (
        reference_system_id,
        reference_system_version,
        reference_concept_iri,
    )
    groups = {
        "project_concept": project_values,
        "turing_core_concept": turing_values,
        "external_reference_concept": external_values,
    }
    for kind, values in groups.items():
        if kind == target_kind:
            if any(value is None for value in values):
                raise TerminologyMappingIntegrityError(
                    f"{target_kind} target is incomplete."
                )
        elif any(value is not None for value in values):
            raise TerminologyMappingIntegrityError(
                f"{target_kind} target contains fields belonging "
                f"to {kind}."
            )

    return TerminologyMappingTarget(
        target_kind=target_kind,
        display_label=display_label,
        project_concept_id=project_concept_id,
        project_concept_revision=project_concept_revision,
        turing_core_concept_id=turing_core_concept_id,
        reference_system_id=reference_system_id,
        reference_system_version=reference_system_version,
        reference_concept_iri=reference_concept_iri,
    )


def _parse_basis(payload: Any) -> TerminologyMappingBasis:
    item = _require_exact_object(
        payload,
        _BASIS_FIELDS,
        "Terminology Mapping Basis",
    )
    basis_type = _require_choice(
        item["basis_type"],
        TERMINOLOGY_MAPPING_BASIS_TYPES,
        "basis_type",
    )
    reference_id = _require_stored_text(
        item["reference_id"],
        "basis.reference_id",
    )
    reference_version = _require_optional_text(
        item["reference_version"],
        "basis.reference_version",
    )
    rationale = _require_stored_text(
        item["rationale"],
        "basis.rationale",
    )
    if (
        basis_type != "semantic_interpretation"
        and reference_version is None
    ):
        raise TerminologyMappingIntegrityError(
            f"{basis_type} basis requires reference_version."
        )
    return TerminologyMappingBasis(
        basis_type=basis_type,
        reference_id=reference_id,
        reference_version=reference_version,
        rationale=rationale,
    )


def _validate_status_proposals(
    status: str,
    proposals: tuple[TerminologyMappingProposal, ...],
) -> None:
    if status == "unmapped" and proposals:
        raise TerminologyMappingIntegrityError(
            "An unmapped candidate must not contain proposals."
        )
    if status == "no_equivalent":
        if (
            len(proposals) != 1
            or proposals[0].mapping_relation != "no_equivalent"
        ):
            raise TerminologyMappingIntegrityError(
                "A no_equivalent candidate requires exactly one "
                "no_equivalent proposal."
            )
    if status == "mapped":
        if not proposals or any(
            proposal.mapping_relation == "no_equivalent"
            for proposal in proposals
        ):
            raise TerminologyMappingIntegrityError(
                "A mapped candidate requires one or more target "
                "proposals."
            )
    if status == "ambiguous" and len(proposals) < 2:
        raise TerminologyMappingIntegrityError(
            "An ambiguous candidate requires at least two "
            "proposals."
        )
    if status == "conflict" and not proposals:
        raise TerminologyMappingIntegrityError(
            "A conflict candidate requires at least one "
            "conflicting proposal."
        )
    if status not in {"unmapped", "no_equivalent"} and len(
        proposals
    ) != len(set(proposals)):
        raise TerminologyMappingIntegrityError(
            "Duplicate mapping proposals are not allowed."
        )


def _validate_target_basis(
    target: TerminologyMappingTarget | None,
    relation: str,
    bases: tuple[TerminologyMappingBasis, ...],
) -> None:
    basis_types = {basis.basis_type for basis in bases}
    if relation == "no_equivalent":
        return
    assert target is not None
    required_basis = {
        "project_concept": "accepted_project_glossary",
        "turing_core_concept": "turing_core",
        "external_reference_concept": (
            "reference_concept_index"
        ),
    }[target.target_kind]
    if required_basis not in basis_types:
        raise TerminologyMappingIntegrityError(
            f"{target.target_kind} target requires a "
            f"{required_basis} mapping basis."
        )


def _validate_candidate_collection(
    candidates: tuple[TerminologyMappingAgentCandidate, ...],
) -> None:
    identifiers = tuple(
        candidate.terminology_mapping_agent_candidate_id
        for candidate in candidates
    )
    if len(identifiers) != len(set(identifiers)):
        raise DuplicateTerminologyMappingAgentCandidateError(
            "Duplicate mapping agent candidate IDs are not "
            "allowed."
        )
    occurrence_keys = tuple(
        _occurrence_key(candidate.occurrence)
        for candidate in candidates
    )
    if len(occurrence_keys) != len(set(occurrence_keys)):
        raise DuplicateTerminologyMappingAgentCandidateError(
            "One persona run must not emit multiple candidates "
            "for the same terminology occurrence."
        )


def _validate_occurrences_against_information_unit(
    result: TerminologyMappingAgentResult,
    information_unit: InformationUnit,
) -> None:
    _require_information_unit(information_unit)
    bindings = (
        (
            "project_id",
            information_unit.project_id,
            result.project_id,
        ),
        (
            "source_id",
            information_unit.source_id,
            result.source_id,
        ),
        (
            "source_projection_id",
            information_unit.source_projection_id,
            result.source_projection_id,
        ),
        (
            "information_unit_id",
            information_unit.information_unit_id,
            result.information_unit_id,
        ),
    )
    mismatches = tuple(
        label
        for label, expected, actual in bindings
        if expected != actual
    )
    if mismatches:
        raise TerminologyMappingReferenceError(
            "Mapping result does not reference the supplied "
            "Information Unit; mismatched fields: "
            + ", ".join(mismatches)
            + "."
        )
    for candidate in result.candidates:
        occurrence = candidate.occurrence
        field_text = getattr(
            information_unit,
            occurrence.text_field,
        )
        if occurrence.end_offset > len(field_text):
            raise TerminologyMappingReferenceError(
                "Terminology occurrence exceeds its Information "
                "Unit field."
            )
        actual = field_text[
            occurrence.start_offset : occurrence.end_offset
        ]
        if actual != occurrence.term_text:
            raise TerminologyMappingReferenceError(
                "Terminology occurrence term_text does not match "
                "the referenced Information Unit field."
            )


def _result_payload(
    result: TerminologyMappingAgentResult,
) -> dict[str, Any]:
    if not isinstance(result, TerminologyMappingAgentResult):
        raise TerminologyMappingValidationError(
            "result must be a TerminologyMappingAgentResult."
        )
    return {
        "schema_version": result.schema_version,
        "project_id": result.project_id,
        "source_id": result.source_id,
        "source_projection_id": result.source_projection_id,
        "information_unit_id": result.information_unit_id,
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
        "ontology_registry_version": (
            result.ontology_registry_version
        ),
        "reference_concept_index_version": (
            result.reference_concept_index_version
        ),
        "turing_core_version": result.turing_core_version,
        "project_glossary_revision": (
            result.project_glossary_revision
        ),
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
    candidate: TerminologyMappingAgentCandidate,
) -> dict[str, Any]:
    if not isinstance(
        candidate,
        TerminologyMappingAgentCandidate,
    ):
        raise TerminologyMappingValidationError(
            "candidate must be a "
            "TerminologyMappingAgentCandidate."
        )
    return {
        "terminology_mapping_agent_candidate_id": (
            candidate.terminology_mapping_agent_candidate_id
        ),
        "occurrence": _occurrence_payload(
            candidate.occurrence
        ),
        "mapping_status": candidate.mapping_status,
        "proposals": [
            _proposal_payload(proposal)
            for proposal in candidate.proposals
        ],
        "rationale": candidate.rationale,
        "uncertainties": list(candidate.uncertainties),
    }


def _occurrence_payload(
    occurrence: TerminologyOccurrence,
) -> dict[str, Any]:
    if not isinstance(occurrence, TerminologyOccurrence):
        raise TerminologyMappingValidationError(
            "occurrence must be a TerminologyOccurrence."
        )
    return {
        "information_unit_id": occurrence.information_unit_id,
        "text_field": occurrence.text_field,
        "start_offset": occurrence.start_offset,
        "end_offset": occurrence.end_offset,
        "term_text": occurrence.term_text,
    }


def _proposal_payload(
    proposal: TerminologyMappingProposal,
) -> dict[str, Any]:
    if not isinstance(proposal, TerminologyMappingProposal):
        raise TerminologyMappingValidationError(
            "proposal must be a TerminologyMappingProposal."
        )
    return {
        "mapping_relation": proposal.mapping_relation,
        "target": (
            None
            if proposal.target is None
            else _target_payload(proposal.target)
        ),
        "mapping_bases": [
            _basis_payload(basis)
            for basis in proposal.mapping_bases
        ],
        "rationale": proposal.rationale,
    }


def _target_payload(
    target: TerminologyMappingTarget,
) -> dict[str, Any]:
    if not isinstance(target, TerminologyMappingTarget):
        raise TerminologyMappingValidationError(
            "target must be a TerminologyMappingTarget."
        )
    return {
        "target_kind": target.target_kind,
        "display_label": target.display_label,
        "project_concept_id": target.project_concept_id,
        "project_concept_revision": (
            target.project_concept_revision
        ),
        "turing_core_concept_id": (
            target.turing_core_concept_id
        ),
        "reference_system_id": target.reference_system_id,
        "reference_system_version": (
            target.reference_system_version
        ),
        "reference_concept_iri": target.reference_concept_iri,
    }


def _basis_payload(
    basis: TerminologyMappingBasis,
) -> dict[str, Any]:
    if not isinstance(basis, TerminologyMappingBasis):
        raise TerminologyMappingValidationError(
            "basis must be a TerminologyMappingBasis."
        )
    return {
        "basis_type": basis.basis_type,
        "reference_id": basis.reference_id,
        "reference_version": basis.reference_version,
        "rationale": basis.rationale,
    }


def _require_information_unit(value: object) -> InformationUnit:
    if not isinstance(value, InformationUnit):
        raise TerminologyMappingValidationError(
            "information_unit must be an InformationUnit."
        )
    return value


def _require_exact_object(
    value: Any,
    fields: frozenset[str],
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TerminologyMappingValidationError(
            f"{label} must be an object."
        )
    actual = frozenset(value.keys())
    if actual != fields:
        missing = sorted(fields - actual)
        unknown = sorted(actual - fields)
        details = []
        if missing:
            details.append(f"missing fields: {missing}")
        if unknown:
            details.append(f"unknown fields: {unknown}")
        raise TerminologyMappingValidationError(
            f"{label} structure is invalid; "
            + "; ".join(details)
            + "."
        )
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise TerminologyMappingValidationError(
            f"{label} must be a list."
        )
    return value


def _require_stored_text(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(character) < 32 for character in value)
    ):
        raise TerminologyMappingValidationError(
            f"{label} must be non-empty, trimmed stored text."
        )
    return value


def _require_optional_text(
    value: Any,
    label: str,
) -> str | None:
    if value is None:
        return None
    return _require_stored_text(value, label)


def _require_choice(
    value: Any,
    choices: frozenset[str],
    label: str,
) -> str:
    selected = _require_stored_text(value, label)
    if selected not in choices:
        raise TerminologyMappingValidationError(
            f"{label} must be one of {sorted(choices)}."
        )
    return selected


def _require_positive_integer(value: Any, label: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise TerminologyMappingValidationError(
            f"{label} must be a positive integer."
        )
    return value


def _require_non_negative_integer(
    value: Any,
    label: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
    ):
        raise TerminologyMappingValidationError(
            f"{label} must be a non-negative integer."
        )
    return value


def _require_optional_positive_integer(
    value: Any,
    label: str,
) -> int | None:
    if value is None:
        return None
    return _require_positive_integer(value, label)


def _require_pattern_identifier(
    value: Any,
    pattern: re.Pattern[str],
    label: str,
    zero_value: str,
) -> str:
    if (
        not isinstance(value, str)
        or pattern.fullmatch(value) is None
        or value == zero_value
    ):
        raise TerminologyMappingValidationError(
            f"{label} has an invalid identifier format."
        )
    return value


def _require_optional_pattern_identifier(
    value: Any,
    pattern: re.Pattern[str],
    label: str,
    zero_value: str,
) -> str | None:
    if value is None:
        return None
    return _require_pattern_identifier(
        value,
        pattern,
        label,
        zero_value,
    )


def _require_semantic_version(
    value: Any,
    label: str,
) -> str:
    text = _require_stored_text(value, label)
    if _SEMANTIC_VERSION_PATTERN.fullmatch(text) is None:
        raise TerminologyMappingValidationError(
            f"{label} must be a semantic version."
        )
    return text


def _require_sha256(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or _SHA256_PATTERN.fullmatch(value) is None
    ):
        raise TerminologyMappingValidationError(
            f"{label} must be a lowercase SHA-256 value."
        )
    return value


def _require_utc_timestamp(value: Any, label: str) -> str:
    text = _require_stored_text(value, label)
    if _UTC_TIMESTAMP_PATTERN.fullmatch(text) is None:
        raise TerminologyMappingValidationError(
            f"{label} must be an ISO 8601 UTC timestamp."
        )
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TerminologyMappingValidationError(
            f"{label} is not a valid timestamp."
        ) from exc
    return text


def _require_optional_iri(
    value: Any,
    label: str,
) -> str | None:
    if value is None:
        return None
    iri = _require_stored_text(value, label)
    parsed = urlparse(iri)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise TerminologyMappingValidationError(
            f"{label} must be an absolute HTTP(S) IRI."
        )
    return iri


def _require_expected(
    actual: str,
    expected: str | None,
    label: str,
) -> None:
    if expected is not None and actual != expected:
        raise TerminologyMappingReferenceError(
            f"{label} does not match the expected value."
        )


def _tuple_of_instances(
    values: Iterable[Any],
    expected_type: type[Any],
    label: str,
) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)):
        raise TerminologyMappingValidationError(
            f"{label} must be an iterable of "
            f"{expected_type.__name__} values."
        )
    try:
        selected = tuple(values)
    except TypeError as exc:
        raise TerminologyMappingValidationError(
            f"{label} must be iterable."
        ) from exc
    if any(
        not isinstance(value, expected_type)
        for value in selected
    ):
        raise TerminologyMappingValidationError(
            f"{label} must contain only "
            f"{expected_type.__name__} values."
        )
    return selected


def _tuple_of_text(
    values: Iterable[str],
    label: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TerminologyMappingValidationError(
            f"{label} must be an iterable of strings."
        )
    try:
        selected = tuple(
            _require_stored_text(value, f"{label} item")
            for value in values
        )
    except TypeError as exc:
        raise TerminologyMappingValidationError(
            f"{label} must be iterable."
        ) from exc
    if len(selected) != len(set(selected)):
        raise TerminologyMappingIntegrityError(
            f"{label} must not contain duplicates."
        )
    return selected


def _parse_text_tuple(
    value: Any,
    label: str,
) -> tuple[str, ...]:
    return _tuple_of_text(
        _require_list(value, label),
        label,
    )


def _occurrence_key(
    occurrence: TerminologyOccurrence,
) -> tuple[str, str, int, int]:
    return (
        occurrence.information_unit_id,
        occurrence.text_field,
        occurrence.start_offset,
        occurrence.end_offset,
    )


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise TerminologyMappingValidationError(
                f"Duplicate JSON object key: {key!r}."
            )
        result[key] = value
    return result