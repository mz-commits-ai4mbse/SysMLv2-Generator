"""Strict manifest contract for persona-local framework assignments."""

from __future__ import annotations

from collections.abc import Iterable
import json
import re
from typing import Any

from modules.information_units.types import InformationUnit
from modules.framework_assignment.errors import (
    DuplicateFrameworkAssignmentAgentCandidateError,
    FrameworkAssignmentIntegrityError,
    FrameworkAssignmentReferenceError,
    FrameworkAssignmentValidationError,
)
from modules.framework_assignment.identifiers import (
    validate_framework_assignment_agent_candidate_id,
)
from modules.framework_assignment.types import (
    FRAMEWORK_ASSIGNMENT_BASIS_TYPES,
    FRAMEWORK_ASSIGNMENT_STATUSES,
    FrameworkAssignmentAgentCandidate,
    FrameworkAssignmentAgentResult,
    FrameworkAssignmentBasis,
    FrameworkAssignmentProposal,
)


FRAMEWORK_ASSIGNMENT_AGENT_RESULT_SCHEMA_VERSION = "1.0.0"

_FRAMEWORK_NODE_ID_PATTERN = re.compile(r"^FW_[A-Z0-9_]+$")
_INFORMATION_UNIT_ID_PATTERN = re.compile(r"^IU-[0-9]{6}$")
_TERMINOLOGY_MAPPING_CANDIDATE_ID_PATTERN = re.compile(
    r"^TMC-[0-9]{6}$"
)
_GENERAL_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*$"
)
_UPPER_IDENTIFIER_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
_SEMANTIC_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
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
        "framework_template_id",
        "framework_template_version",
        "turing_core_version",
        "project_glossary_revision",
        "terminology_mapping_candidate_ids",
        "candidates",
        "no_candidate_rationale",
        "created_at",
    }
)
_CANDIDATE_FIELDS = frozenset(
    {
        "framework_assignment_agent_candidate_id",
        "information_unit_id",
        "assignment_status",
        "proposals",
        "rationale",
        "uncertainties",
    }
)
_PROPOSAL_FIELDS = frozenset(
    {
        "framework_node_id",
        "assignment_bases",
        "rationale",
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


def create_framework_assignment_basis(
    *,
    basis_type: str,
    reference_id: str,
    reference_version: str | None,
    rationale: str,
) -> FrameworkAssignmentBasis:
    """Create one versioned assignment-evidence reference."""

    return _parse_basis(
        {
            "basis_type": basis_type,
            "reference_id": reference_id,
            "reference_version": reference_version,
            "rationale": rationale,
        }
    )


def create_framework_assignment_proposal(
    *,
    framework_node_id: str,
    assignment_bases: Iterable[FrameworkAssignmentBasis],
    rationale: str,
) -> FrameworkAssignmentProposal:
    """Create one non-authoritative proposal for one stable node."""

    bases = _tuple_of_instances(
        assignment_bases,
        FrameworkAssignmentBasis,
        "assignment_bases",
    )
    return _parse_proposal(
        {
            "framework_node_id": framework_node_id,
            "assignment_bases": [
                _basis_payload(basis)
                for basis in bases
            ],
            "rationale": rationale,
        }
    )


def create_framework_assignment_agent_candidate(
    *,
    framework_assignment_agent_candidate_id: str,
    information_unit_id: str,
    assignment_status: str,
    proposals: Iterable[FrameworkAssignmentProposal],
    rationale: str,
    uncertainties: Iterable[str] = (),
) -> FrameworkAssignmentAgentCandidate:
    """Create one result-local candidate without confidence or approval."""

    selected_proposals = _tuple_of_instances(
        proposals,
        FrameworkAssignmentProposal,
        "proposals",
    )
    selected_uncertainties = _tuple_of_text(
        uncertainties,
        "uncertainties",
    )
    return _parse_candidate(
        {
            "framework_assignment_agent_candidate_id": (
                framework_assignment_agent_candidate_id
            ),
            "information_unit_id": information_unit_id,
            "assignment_status": assignment_status,
            "proposals": [
                _proposal_payload(proposal)
                for proposal in selected_proposals
            ],
            "rationale": rationale,
            "uncertainties": list(selected_uncertainties),
        },
        expected_candidate_id=(
            framework_assignment_agent_candidate_id
        ),
        expected_information_unit_id=information_unit_id,
    )


def create_framework_assignment_agent_result(
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
    framework_template_id: str,
    framework_template_version: str,
    turing_core_version: str,
    project_glossary_revision: int,
    terminology_mapping_candidate_ids: Iterable[str],
    candidates: Iterable[FrameworkAssignmentAgentCandidate],
    no_candidate_rationale: str | None,
    timestamp: str,
) -> FrameworkAssignmentAgentResult:
    """Create one immutable persona-run framework-assignment result."""

    _require_information_unit(information_unit)
    selected_candidate_ids = _tuple_of_text(
        terminology_mapping_candidate_ids,
        "terminology_mapping_candidate_ids",
    )
    selected_candidates = _tuple_of_instances(
        candidates,
        FrameworkAssignmentAgentCandidate,
        "candidates",
    )
    result = FrameworkAssignmentAgentResult(
        schema_version=(
            FRAMEWORK_ASSIGNMENT_AGENT_RESULT_SCHEMA_VERSION
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
        framework_template_id=framework_template_id,
        framework_template_version=framework_template_version,
        turing_core_version=turing_core_version,
        project_glossary_revision=project_glossary_revision,
        terminology_mapping_candidate_ids=(
            selected_candidate_ids
        ),
        candidates=selected_candidates,
        no_candidate_rationale=no_candidate_rationale,
        created_at=timestamp,
    )
    validated = parse_framework_assignment_agent_result(
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
    _validate_against_information_unit(
        validated,
        information_unit,
    )
    return validated


def parse_framework_assignment_agent_result(
    payload: Any,
    *,
    expected_project_id: str | None = None,
    expected_source_id: str | None = None,
    expected_source_projection_id: str | None = None,
    expected_information_unit_id: str | None = None,
) -> FrameworkAssignmentAgentResult:
    """Parse and strictly validate a persona-run result object."""

    data = _require_exact_object(
        payload,
        _RESULT_FIELDS,
        "Framework Assignment Agent Result",
    )
    schema_version = _require_expected(
        data["schema_version"],
        FRAMEWORK_ASSIGNMENT_AGENT_RESULT_SCHEMA_VERSION,
        "schema_version",
    )
    project_id = _require_general_identifier(
        data["project_id"],
        "project_id",
    )
    source_id = _require_general_identifier(
        data["source_id"],
        "source_id",
    )
    source_projection_id = _require_general_identifier(
        data["source_projection_id"],
        "source_projection_id",
    )
    information_unit_id = _require_pattern_identifier(
        data["information_unit_id"],
        _INFORMATION_UNIT_ID_PATTERN,
        "information_unit_id",
    )
    _require_optional_expected(
        project_id,
        expected_project_id,
        "project_id",
    )
    _require_optional_expected(
        source_id,
        expected_source_id,
        "source_id",
    )
    _require_optional_expected(
        source_projection_id,
        expected_source_projection_id,
        "source_projection_id",
    )
    _require_optional_expected(
        information_unit_id,
        expected_information_unit_id,
        "information_unit_id",
    )

    terminology_ids = _parse_identifier_list(
        data["terminology_mapping_candidate_ids"],
        pattern=_TERMINOLOGY_MAPPING_CANDIDATE_ID_PATTERN,
        label="terminology_mapping_candidate_ids",
    )
    candidates = tuple(
        _parse_candidate(
            item,
            expected_information_unit_id=information_unit_id,
        )
        for item in _require_list(
            data["candidates"],
            "candidates",
        )
    )
    _validate_candidate_collection(candidates)
    no_candidate_rationale = _require_optional_text(
        data["no_candidate_rationale"],
        "no_candidate_rationale",
    )
    if bool(candidates) == bool(no_candidate_rationale):
        raise FrameworkAssignmentIntegrityError(
            "A result must contain exactly one candidate or one "
            "no_candidate_rationale."
        )
    if len(candidates) > 1:
        raise FrameworkAssignmentIntegrityError(
            "One persona run may emit at most one framework-assignment "
            "candidate for one Information Unit."
        )

    result = FrameworkAssignmentAgentResult(
        schema_version=schema_version,
        project_id=project_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        information_unit_id=information_unit_id,
        team_id=_require_general_identifier(
            data["team_id"],
            "team_id",
        ),
        agent_id=_require_general_identifier(
            data["agent_id"],
            "agent_id",
        ),
        persona_id=_require_general_identifier(
            data["persona_id"],
            "persona_id",
        ),
        persona_run_index=_require_positive_integer(
            data["persona_run_index"],
            "persona_run_index",
        ),
        persona_configuration_fingerprint=_require_sha256(
            data["persona_configuration_fingerprint"],
            "persona_configuration_fingerprint",
        ),
        llm_provider=_require_stored_text(
            data["llm_provider"],
            "llm_provider",
        ),
        llm_model=_require_stored_text(
            data["llm_model"],
            "llm_model",
        ),
        prompt_schema_version=_require_semantic_version(
            data["prompt_schema_version"],
            "prompt_schema_version",
        ),
        framework_template_id=_require_pattern_identifier(
            data["framework_template_id"],
            _UPPER_IDENTIFIER_PATTERN,
            "framework_template_id",
        ),
        framework_template_version=_require_semantic_version(
            data["framework_template_version"],
            "framework_template_version",
        ),
        turing_core_version=_require_semantic_version(
            data["turing_core_version"],
            "turing_core_version",
        ),
        project_glossary_revision=_require_positive_integer(
            data["project_glossary_revision"],
            "project_glossary_revision",
        ),
        terminology_mapping_candidate_ids=terminology_ids,
        candidates=candidates,
        no_candidate_rationale=no_candidate_rationale,
        created_at=_require_utc_timestamp(
            data["created_at"],
            "created_at",
        ),
    )
    _validate_result_bases(result)
    return result


def framework_assignment_agent_result_from_json(
    text: str,
    *,
    expected_project_id: str | None = None,
    expected_source_id: str | None = None,
    expected_source_projection_id: str | None = None,
    expected_information_unit_id: str | None = None,
) -> FrameworkAssignmentAgentResult:
    """Parse strict JSON into one validated persona-run result."""

    if not isinstance(text, str):
        raise FrameworkAssignmentValidationError(
            "Framework Assignment Agent Result JSON must be a string."
        )
    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except FrameworkAssignmentValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise FrameworkAssignmentValidationError(
            f"Framework Assignment Agent Result contains invalid JSON: "
            f"{exc}."
        ) from exc
    return parse_framework_assignment_agent_result(
        payload,
        expected_project_id=expected_project_id,
        expected_source_id=expected_source_id,
        expected_source_projection_id=expected_source_projection_id,
        expected_information_unit_id=expected_information_unit_id,
    )


def validate_framework_assignment_agent_result(
    result: FrameworkAssignmentAgentResult,
) -> None:
    """Validate one in-memory persona-run result."""

    framework_assignment_agent_result_to_dict(result)


def framework_assignment_agent_result_to_dict(
    result: FrameworkAssignmentAgentResult,
) -> dict[str, Any]:
    """Return a validated JSON-compatible result object."""

    parsed = parse_framework_assignment_agent_result(
        _result_payload(result)
    )
    return _result_payload(parsed)


def framework_assignment_agent_result_to_json(
    result: FrameworkAssignmentAgentResult,
) -> str:
    """Serialize one result deterministically."""

    return (
        json.dumps(
            framework_assignment_agent_result_to_dict(result),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _parse_candidate(
    payload: Any,
    *,
    expected_candidate_id: str | None = None,
    expected_information_unit_id: str | None = None,
) -> FrameworkAssignmentAgentCandidate:
    data = _require_exact_object(
        payload,
        _CANDIDATE_FIELDS,
        "Framework Assignment Agent Candidate",
    )
    candidate_id = (
        validate_framework_assignment_agent_candidate_id(
            data["framework_assignment_agent_candidate_id"]
        )
    )
    _require_optional_expected(
        candidate_id,
        expected_candidate_id,
        "framework_assignment_agent_candidate_id",
    )
    information_unit_id = _require_pattern_identifier(
        data["information_unit_id"],
        _INFORMATION_UNIT_ID_PATTERN,
        "candidate.information_unit_id",
    )
    _require_optional_expected(
        information_unit_id,
        expected_information_unit_id,
        "candidate.information_unit_id",
    )
    status = _require_choice(
        data["assignment_status"],
        FRAMEWORK_ASSIGNMENT_STATUSES,
        "assignment_status",
    )
    proposals = tuple(
        _parse_proposal(item)
        for item in _require_list(
            data["proposals"],
            "proposals",
        )
    )
    _validate_status_proposals(status, proposals)
    return FrameworkAssignmentAgentCandidate(
        framework_assignment_agent_candidate_id=candidate_id,
        information_unit_id=information_unit_id,
        assignment_status=status,
        proposals=proposals,
        rationale=_require_stored_text(
            data["rationale"],
            "candidate.rationale",
        ),
        uncertainties=_parse_text_list(
            data["uncertainties"],
            "uncertainties",
        ),
    )


def _parse_proposal(payload: Any) -> FrameworkAssignmentProposal:
    data = _require_exact_object(
        payload,
        _PROPOSAL_FIELDS,
        "Framework Assignment Proposal",
    )
    bases = tuple(
        _parse_basis(item)
        for item in _require_list(
            data["assignment_bases"],
            "assignment_bases",
        )
    )
    if not bases:
        raise FrameworkAssignmentIntegrityError(
            "A framework-assignment proposal requires evidence."
        )
    if len(bases) != len(set(bases)):
        raise FrameworkAssignmentIntegrityError(
            "Duplicate assignment bases are not allowed."
        )
    if not any(
        basis.basis_type == "information_unit"
        for basis in bases
    ):
        raise FrameworkAssignmentIntegrityError(
            "Every framework-assignment proposal requires an "
            "information_unit basis."
        )
    return FrameworkAssignmentProposal(
        framework_node_id=_require_pattern_identifier(
            data["framework_node_id"],
            _FRAMEWORK_NODE_ID_PATTERN,
            "framework_node_id",
        ),
        assignment_bases=bases,
        rationale=_require_stored_text(
            data["rationale"],
            "proposal.rationale",
        ),
    )


def _parse_basis(payload: Any) -> FrameworkAssignmentBasis:
    data = _require_exact_object(
        payload,
        _BASIS_FIELDS,
        "Framework Assignment Basis",
    )
    basis_type = _require_choice(
        data["basis_type"],
        FRAMEWORK_ASSIGNMENT_BASIS_TYPES,
        "basis_type",
    )
    reference_id = _require_stored_text(
        data["reference_id"],
        "basis.reference_id",
    )
    reference_version = _require_optional_text(
        data["reference_version"],
        "basis.reference_version",
    )
    if basis_type == "information_unit":
        _require_pattern_identifier(
            reference_id,
            _INFORMATION_UNIT_ID_PATTERN,
            "information_unit basis reference_id",
        )
        _require_sha256(
            reference_version,
            "information_unit basis reference_version",
        )
    elif basis_type == "terminology_mapping_candidate":
        _require_pattern_identifier(
            reference_id,
            _TERMINOLOGY_MAPPING_CANDIDATE_ID_PATTERN,
            "terminology basis reference_id",
        )
        _require_sha256(
            reference_version,
            "terminology basis reference_version",
        )
    elif basis_type == "turing_core_concept":
        if re.fullmatch(r"^TC-[0-9]{6}$", reference_id) is None:
            raise FrameworkAssignmentValidationError(
                "Turing Core basis reference_id must match "
                "^TC-[0-9]{6}$."
            )
        _require_semantic_version(
            reference_version,
            "Turing Core basis reference_version",
        )
    elif reference_version is not None:
        raise FrameworkAssignmentIntegrityError(
            "semantic_interpretation basis must not declare "
            "reference_version."
        )
    return FrameworkAssignmentBasis(
        basis_type=basis_type,
        reference_id=reference_id,
        reference_version=reference_version,
        rationale=_require_stored_text(
            data["rationale"],
            "basis.rationale",
        ),
    )


def _validate_status_proposals(
    status: str,
    proposals: tuple[FrameworkAssignmentProposal, ...],
) -> None:
    if status == "unassigned" and proposals:
        raise FrameworkAssignmentIntegrityError(
            "An unassigned candidate must not contain proposals."
        )
    if status == "assigned" and not proposals:
        raise FrameworkAssignmentIntegrityError(
            "An assigned candidate requires one or more proposals."
        )
    if status in {"ambiguous", "conflict"} and len(proposals) < 2:
        raise FrameworkAssignmentIntegrityError(
            f"A {status} candidate requires at least two proposals."
        )
    if len(proposals) != len(set(proposals)):
        raise FrameworkAssignmentIntegrityError(
            "Duplicate framework-assignment proposals are not allowed."
        )
    node_ids = tuple(
        proposal.framework_node_id
        for proposal in proposals
    )
    if len(node_ids) != len(set(node_ids)):
        raise FrameworkAssignmentIntegrityError(
            "One candidate must not repeat a framework node."
        )


def _validate_candidate_collection(
    candidates: tuple[FrameworkAssignmentAgentCandidate, ...],
) -> None:
    identifiers = tuple(
        candidate.framework_assignment_agent_candidate_id
        for candidate in candidates
    )
    if len(identifiers) != len(set(identifiers)):
        raise DuplicateFrameworkAssignmentAgentCandidateError(
            "Duplicate framework-assignment agent candidate IDs are "
            "not allowed."
        )


def _validate_result_bases(
    result: FrameworkAssignmentAgentResult,
) -> None:
    permitted_terminology_ids = set(
        result.terminology_mapping_candidate_ids
    )
    for candidate in result.candidates:
        for proposal in candidate.proposals:
            for basis in proposal.assignment_bases:
                if basis.basis_type == "information_unit":
                    if (
                        basis.reference_id
                        != result.information_unit_id
                    ):
                        raise FrameworkAssignmentReferenceError(
                            "Information Unit basis does not match "
                            "the result Information Unit."
                        )
                elif (
                    basis.basis_type
                    == "terminology_mapping_candidate"
                    and basis.reference_id
                    not in permitted_terminology_ids
                ):
                    raise FrameworkAssignmentReferenceError(
                        "Terminology Mapping Candidate basis is not "
                        "declared by the result."
                    )
                elif (
                    basis.basis_type == "turing_core_concept"
                    and basis.reference_version
                    != result.turing_core_version
                ):
                    raise FrameworkAssignmentReferenceError(
                        "Turing Core basis version does not match "
                        "the result configuration."
                    )


def _validate_against_information_unit(
    result: FrameworkAssignmentAgentResult,
    information_unit: InformationUnit,
) -> None:
    bindings = (
        ("project_id", information_unit.project_id, result.project_id),
        ("source_id", information_unit.source_id, result.source_id),
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
        raise FrameworkAssignmentReferenceError(
            "Framework-assignment result does not reference the "
            "supplied Information Unit; mismatched fields: "
            + ", ".join(mismatches)
            + "."
        )
    for candidate in result.candidates:
        for proposal in candidate.proposals:
            information_bases = tuple(
                basis
                for basis in proposal.assignment_bases
                if basis.basis_type == "information_unit"
            )
            if not any(
                basis.reference_id
                == information_unit.information_unit_id
                and basis.reference_version
                == information_unit.content_fingerprint
                for basis in information_bases
            ):
                raise FrameworkAssignmentReferenceError(
                    "Information Unit basis must bind the exact "
                    "Information Unit content fingerprint."
                )


def _result_payload(
    result: FrameworkAssignmentAgentResult,
) -> dict[str, Any]:
    if not isinstance(result, FrameworkAssignmentAgentResult):
        raise FrameworkAssignmentValidationError(
            "result must be a FrameworkAssignmentAgentResult."
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
        "framework_template_id": result.framework_template_id,
        "framework_template_version": (
            result.framework_template_version
        ),
        "turing_core_version": result.turing_core_version,
        "project_glossary_revision": (
            result.project_glossary_revision
        ),
        "terminology_mapping_candidate_ids": list(
            result.terminology_mapping_candidate_ids
        ),
        "candidates": [
            _candidate_payload(candidate)
            for candidate in result.candidates
        ],
        "no_candidate_rationale": result.no_candidate_rationale,
        "created_at": result.created_at,
    }


def _candidate_payload(
    candidate: FrameworkAssignmentAgentCandidate,
) -> dict[str, Any]:
    if not isinstance(
        candidate,
        FrameworkAssignmentAgentCandidate,
    ):
        raise FrameworkAssignmentValidationError(
            "candidate must be a FrameworkAssignmentAgentCandidate."
        )
    return {
        "framework_assignment_agent_candidate_id": (
            candidate.framework_assignment_agent_candidate_id
        ),
        "information_unit_id": candidate.information_unit_id,
        "assignment_status": candidate.assignment_status,
        "proposals": [
            _proposal_payload(proposal)
            for proposal in candidate.proposals
        ],
        "rationale": candidate.rationale,
        "uncertainties": list(candidate.uncertainties),
    }


def _proposal_payload(
    proposal: FrameworkAssignmentProposal,
) -> dict[str, Any]:
    if not isinstance(proposal, FrameworkAssignmentProposal):
        raise FrameworkAssignmentValidationError(
            "proposal must be a FrameworkAssignmentProposal."
        )
    return {
        "framework_node_id": proposal.framework_node_id,
        "assignment_bases": [
            _basis_payload(basis)
            for basis in proposal.assignment_bases
        ],
        "rationale": proposal.rationale,
    }


def _basis_payload(
    basis: FrameworkAssignmentBasis,
) -> dict[str, Any]:
    if not isinstance(basis, FrameworkAssignmentBasis):
        raise FrameworkAssignmentValidationError(
            "basis must be a FrameworkAssignmentBasis."
        )
    return {
        "basis_type": basis.basis_type,
        "reference_id": basis.reference_id,
        "reference_version": basis.reference_version,
        "rationale": basis.rationale,
    }


def _require_information_unit(value: object) -> InformationUnit:
    if not isinstance(value, InformationUnit):
        raise FrameworkAssignmentValidationError(
            "information_unit must be an InformationUnit."
        )
    return value


def _require_exact_object(
    value: Any,
    expected_fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FrameworkAssignmentValidationError(
            f"{label} must be an object."
        )
    actual_fields = frozenset(value)
    if actual_fields != expected_fields:
        missing = sorted(expected_fields - actual_fields)
        unknown = sorted(actual_fields - expected_fields)
        raise FrameworkAssignmentValidationError(
            f"{label} has invalid fields; missing={missing}, "
            f"unknown={unknown}."
        )
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise FrameworkAssignmentValidationError(
            f"{label} must be a list."
        )
    return value


def _require_stored_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FrameworkAssignmentValidationError(
            f"{label} must be a non-empty string."
        )
    if value != value.strip():
        raise FrameworkAssignmentValidationError(
            f"{label} must not contain surrounding whitespace."
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
        raise FrameworkAssignmentValidationError(
            f"{label} must be one of {sorted(choices)!r}."
        )
    return selected


def _require_positive_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise FrameworkAssignmentValidationError(
            f"{label} must be an integer."
        )
    if value < 1:
        raise FrameworkAssignmentValidationError(
            f"{label} must be greater than zero."
        )
    return value


def _require_pattern_identifier(
    value: Any,
    pattern: re.Pattern[str],
    label: str,
) -> str:
    selected = _require_stored_text(value, label)
    if pattern.fullmatch(selected) is None:
        raise FrameworkAssignmentValidationError(
            f"{label} has invalid identifier syntax."
        )
    return selected


def _require_general_identifier(value: Any, label: str) -> str:
    return _require_pattern_identifier(
        value,
        _GENERAL_IDENTIFIER_PATTERN,
        label,
    )


def _require_semantic_version(value: Any, label: str) -> str:
    return _require_pattern_identifier(
        value,
        _SEMANTIC_VERSION_PATTERN,
        label,
    )


def _require_sha256(value: Any, label: str) -> str:
    return _require_pattern_identifier(
        value,
        _SHA256_PATTERN,
        label,
    )


def _require_utc_timestamp(value: Any, label: str) -> str:
    return _require_pattern_identifier(
        value,
        _UTC_TIMESTAMP_PATTERN,
        label,
    )


def _require_expected(
    value: Any,
    expected: str,
    label: str,
) -> str:
    if value != expected:
        raise FrameworkAssignmentValidationError(
            f"{label} must be {expected!r}."
        )
    return expected


def _require_optional_expected(
    actual: str,
    expected: str | None,
    label: str,
) -> None:
    if expected is not None and actual != expected:
        raise FrameworkAssignmentReferenceError(
            f"{label} must be {expected!r}, got {actual!r}."
        )


def _tuple_of_instances(
    values: Iterable[Any],
    expected_type: type,
    label: str,
) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)):
        raise FrameworkAssignmentValidationError(
            f"{label} must be an iterable of "
            f"{expected_type.__name__} values."
        )
    try:
        selected = tuple(values)
    except TypeError as exc:
        raise FrameworkAssignmentValidationError(
            f"{label} must be iterable."
        ) from exc
    if not all(
        isinstance(value, expected_type)
        for value in selected
    ):
        raise FrameworkAssignmentValidationError(
            f"{label} must contain only "
            f"{expected_type.__name__} values."
        )
    return selected


def _tuple_of_text(
    values: Iterable[str],
    label: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise FrameworkAssignmentValidationError(
            f"{label} must be an iterable of strings."
        )
    try:
        selected = tuple(
            _require_stored_text(value, label)
            for value in values
        )
    except TypeError as exc:
        raise FrameworkAssignmentValidationError(
            f"{label} must be iterable."
        ) from exc
    if len(selected) != len(set(selected)):
        raise FrameworkAssignmentIntegrityError(
            f"{label} must not contain duplicates."
        )
    return selected


def _parse_text_list(
    value: Any,
    label: str,
) -> tuple[str, ...]:
    return _tuple_of_text(
        _require_list(value, label),
        label,
    )


def _parse_identifier_list(
    value: Any,
    *,
    pattern: re.Pattern[str],
    label: str,
) -> tuple[str, ...]:
    identifiers = tuple(
        _require_pattern_identifier(item, pattern, label)
        for item in _require_list(value, label)
    )
    if len(identifiers) != len(set(identifiers)):
        raise FrameworkAssignmentIntegrityError(
            f"{label} must not contain duplicates."
        )
    return identifiers


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise FrameworkAssignmentValidationError(
                f"Duplicate JSON object key: {key!r}."
            )
        result[key] = value
    return result