"""Immutable persistent manifest for framework-assignment candidates."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .agent_manifest import (
    create_framework_assignment_basis,
    create_framework_assignment_proposal,
)
from .analyzer import FrameworkAssignmentConsensusResult
from .errors import (
    FrameworkAssignmentIntegrityError,
    FrameworkAssignmentReferenceError,
    FrameworkAssignmentValidationError,
)
from .identifiers import (
    validate_framework_assignment_agent_candidate_id,
    validate_framework_assignment_candidate_id,
)
from .types import (
    FRAMEWORK_ASSIGNMENT_CONFIDENCE_LEVELS,
    FRAMEWORK_ASSIGNMENT_CONSENSUS_LEVELS,
    FRAMEWORK_ASSIGNMENT_REVIEW_MODES,
    FRAMEWORK_ASSIGNMENT_STATUSES,
    FRAMEWORK_ASSIGNMENT_VARIANCE_LEVELS,
    FrameworkAssignmentAgentCandidateReference,
    FrameworkAssignmentCandidate,
    FrameworkAssignmentConsensusOutcome,
    FrameworkAssignmentProposal,
)


FRAMEWORK_ASSIGNMENT_CANDIDATE_SCHEMA_VERSION = "1.0.0"

_GENERAL_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*$"
)
_UPPER_IDENTIFIER_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
_INFORMATION_UNIT_ID_PATTERN = re.compile(r"^IU-[0-9]{6}$")
_TERMINOLOGY_MAPPING_CANDIDATE_ID_PATTERN = re.compile(
    r"^TMC-[0-9]{6}$"
)
_SEMANTIC_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)

_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "source_id",
        "source_projection_id",
        "information_unit_id",
        "framework_assignment_candidate_id",
        "assignment_status",
        "proposals",
        "candidate_references",
        "team_id",
        "required_personas",
        "llm_provider",
        "llm_model",
        "prompt_schema_version",
        "framework_template_id",
        "framework_template_version",
        "turing_core_version",
        "project_glossary_revision",
        "terminology_mapping_candidate_ids",
        "consensus_level",
        "variance_level",
        "confidence",
        "confidence_rationale",
        "confirmation_required",
        "review_required",
        "recommended_review_mode",
        "content_fingerprint",
        "created_at",
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
_REFERENCE_FIELDS = frozenset(
    {
        "persona_id",
        "agent_id",
        "persona_run_index",
        "framework_assignment_agent_candidate_id",
    }
)


def create_framework_assignment_candidate(
    *,
    consensus_result: FrameworkAssignmentConsensusResult,
    outcome: FrameworkAssignmentConsensusOutcome,
    framework_assignment_candidate_id: str,
    timestamp: str,
) -> FrameworkAssignmentCandidate:
    """Create one persistent non-authoritative consensus candidate."""

    if not isinstance(
        consensus_result,
        FrameworkAssignmentConsensusResult,
    ):
        raise FrameworkAssignmentValidationError(
            "consensus_result must be a "
            "FrameworkAssignmentConsensusResult."
        )
    if not isinstance(outcome, FrameworkAssignmentConsensusOutcome):
        raise FrameworkAssignmentValidationError(
            "outcome must be a FrameworkAssignmentConsensusOutcome."
        )
    if outcome not in consensus_result.outcomes:
        raise FrameworkAssignmentReferenceError(
            "outcome must belong to consensus_result."
        )
    if (
        outcome.information_unit_id
        != consensus_result.information_unit_id
    ):
        raise FrameworkAssignmentReferenceError(
            "outcome Information Unit does not match consensus_result."
        )
    if not outcome.persistence_eligible:
        raise FrameworkAssignmentIntegrityError(
            "Only persistence-eligible consensus outcomes may create "
            "Framework Assignment Candidates."
        )
    if not outcome.confirmation_required:
        raise FrameworkAssignmentIntegrityError(
            "A Framework Assignment Candidate must require human "
            "confirmation."
        )

    candidate = FrameworkAssignmentCandidate(
        schema_version=(
            FRAMEWORK_ASSIGNMENT_CANDIDATE_SCHEMA_VERSION
        ),
        project_id=consensus_result.project_id,
        source_id=consensus_result.source_id,
        source_projection_id=(
            consensus_result.source_projection_id
        ),
        information_unit_id=(
            consensus_result.information_unit_id
        ),
        framework_assignment_candidate_id=(
            framework_assignment_candidate_id
        ),
        assignment_status=outcome.assignment_status,
        proposals=outcome.selected_proposals,
        candidate_references=outcome.candidate_references,
        team_id=consensus_result.team_id,
        required_personas=consensus_result.required_personas,
        llm_provider=consensus_result.llm_provider,
        llm_model=consensus_result.llm_model,
        prompt_schema_version=(
            consensus_result.prompt_schema_version
        ),
        framework_template_id=(
            consensus_result.framework_template_id
        ),
        framework_template_version=(
            consensus_result.framework_template_version
        ),
        turing_core_version=(
            consensus_result.turing_core_version
        ),
        project_glossary_revision=(
            consensus_result.project_glossary_revision
        ),
        terminology_mapping_candidate_ids=(
            consensus_result.terminology_mapping_candidate_ids
        ),
        consensus_level=outcome.consensus_level,
        variance_level=outcome.variance_level,
        confidence=outcome.confidence,
        confidence_rationale=outcome.confidence_rationale,
        confirmation_required=True,
        review_required=outcome.review_required,
        recommended_review_mode=(
            outcome.recommended_review_mode
        ),
        content_fingerprint="0" * 64,
        created_at=timestamp,
    )
    fingerprint = calculate_framework_assignment_fingerprint(
        candidate
    )
    return parse_framework_assignment_candidate(
        {
            **_payload(candidate),
            "content_fingerprint": fingerprint,
        },
        expected_project_id=consensus_result.project_id,
        expected_information_unit_id=(
            consensus_result.information_unit_id
        ),
        expected_framework_assignment_candidate_id=(
            framework_assignment_candidate_id
        ),
    )


def calculate_framework_assignment_fingerprint(
    candidate: FrameworkAssignmentCandidate,
) -> str:
    """Calculate identity-independent candidate content fingerprint."""

    data = _payload(candidate)
    data.pop("framework_assignment_candidate_id")
    data.pop("content_fingerprint")
    data.pop("created_at")
    canonical = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def validate_framework_assignment_candidate(
    candidate: FrameworkAssignmentCandidate,
) -> None:
    """Validate one in-memory persistent candidate."""

    framework_assignment_candidate_to_dict(candidate)


def framework_assignment_candidate_to_dict(
    candidate: FrameworkAssignmentCandidate,
) -> dict[str, Any]:
    """Return one validated JSON-compatible candidate object."""

    parsed = parse_framework_assignment_candidate(
        _payload(candidate)
    )
    return _payload(parsed)


def framework_assignment_candidate_to_json(
    candidate: FrameworkAssignmentCandidate,
) -> str:
    """Serialize one candidate deterministically."""

    return (
        json.dumps(
            framework_assignment_candidate_to_dict(candidate),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def framework_assignment_candidate_from_json(
    text: str,
    *,
    expected_project_id: str | None = None,
    expected_information_unit_id: str | None = None,
    expected_framework_assignment_candidate_id: str | None = None,
) -> FrameworkAssignmentCandidate:
    """Parse strict JSON into one validated persistent candidate."""

    if not isinstance(text, str):
        raise FrameworkAssignmentValidationError(
            "Framework Assignment Candidate JSON must be a string."
        )
    try:
        payload = json.loads(
            text,
            object_pairs_hook=_without_duplicate_keys,
        )
    except FrameworkAssignmentValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise FrameworkAssignmentValidationError(
            f"Framework Assignment Candidate contains invalid JSON: "
            f"{exc}."
        ) from exc
    return parse_framework_assignment_candidate(
        payload,
        expected_project_id=expected_project_id,
        expected_information_unit_id=expected_information_unit_id,
        expected_framework_assignment_candidate_id=(
            expected_framework_assignment_candidate_id
        ),
    )


def parse_framework_assignment_candidate(
    payload: Any,
    *,
    expected_project_id: str | None = None,
    expected_information_unit_id: str | None = None,
    expected_framework_assignment_candidate_id: str | None = None,
) -> FrameworkAssignmentCandidate:
    """Parse and strictly validate one candidate object."""

    data = _exact_object(
        payload,
        _FIELDS,
        "Framework Assignment Candidate",
    )
    project_id = _identifier(
        data["project_id"],
        _GENERAL_IDENTIFIER_PATTERN,
        "project_id",
    )
    information_unit_id = _identifier(
        data["information_unit_id"],
        _INFORMATION_UNIT_ID_PATTERN,
        "information_unit_id",
    )
    candidate_id = validate_framework_assignment_candidate_id(
        data["framework_assignment_candidate_id"]
    )
    _expected_optional(
        project_id,
        expected_project_id,
        "project_id",
    )
    _expected_optional(
        information_unit_id,
        expected_information_unit_id,
        "information_unit_id",
    )
    _expected_optional(
        candidate_id,
        expected_framework_assignment_candidate_id,
        "framework_assignment_candidate_id",
    )

    proposals = tuple(
        _parse_proposal(value)
        for value in _list(data["proposals"], "proposals")
    )
    status = _choice(
        data["assignment_status"],
        FRAMEWORK_ASSIGNMENT_STATUSES,
        "assignment_status",
    )
    _validate_status(status, proposals)
    references = tuple(
        _parse_reference(value)
        for value in _list(
            data["candidate_references"],
            "candidate_references",
        )
    )
    if not references:
        raise FrameworkAssignmentIntegrityError(
            "A persistent candidate requires persona-run references."
        )
    if len(references) != len(set(references)):
        raise FrameworkAssignmentIntegrityError(
            "Duplicate persona-run candidate references are not "
            "allowed."
        )
    required_personas = _text_tuple(
        data["required_personas"],
        "required_personas",
    )
    terminology_ids = _identifier_tuple(
        data["terminology_mapping_candidate_ids"],
        _TERMINOLOGY_MAPPING_CANDIDATE_ID_PATTERN,
        "terminology_mapping_candidate_ids",
    )
    confirmation_required = _boolean(
        data["confirmation_required"],
        "confirmation_required",
    )
    if confirmation_required is not True:
        raise FrameworkAssignmentIntegrityError(
            "Framework Assignment Candidates must require human "
            "confirmation."
        )
    review_required = _boolean(
        data["review_required"],
        "review_required",
    )
    review_mode = _choice(
        data["recommended_review_mode"],
        FRAMEWORK_ASSIGNMENT_REVIEW_MODES,
        "recommended_review_mode",
    )
    if review_required != (review_mode == "detailed_review"):
        raise FrameworkAssignmentIntegrityError(
            "review_required and recommended_review_mode disagree."
        )

    candidate = FrameworkAssignmentCandidate(
        schema_version=_expected(
            data["schema_version"],
            FRAMEWORK_ASSIGNMENT_CANDIDATE_SCHEMA_VERSION,
            "schema_version",
        ),
        project_id=project_id,
        source_id=_identifier(
            data["source_id"],
            _GENERAL_IDENTIFIER_PATTERN,
            "source_id",
        ),
        source_projection_id=_identifier(
            data["source_projection_id"],
            _GENERAL_IDENTIFIER_PATTERN,
            "source_projection_id",
        ),
        information_unit_id=information_unit_id,
        framework_assignment_candidate_id=candidate_id,
        assignment_status=status,
        proposals=proposals,
        candidate_references=references,
        team_id=_identifier(
            data["team_id"],
            _GENERAL_IDENTIFIER_PATTERN,
            "team_id",
        ),
        required_personas=required_personas,
        llm_provider=_text(data["llm_provider"], "llm_provider"),
        llm_model=_text(data["llm_model"], "llm_model"),
        prompt_schema_version=_semver(
            data["prompt_schema_version"],
            "prompt_schema_version",
        ),
        framework_template_id=_identifier(
            data["framework_template_id"],
            _UPPER_IDENTIFIER_PATTERN,
            "framework_template_id",
        ),
        framework_template_version=_semver(
            data["framework_template_version"],
            "framework_template_version",
        ),
        turing_core_version=_semver(
            data["turing_core_version"],
            "turing_core_version",
        ),
        project_glossary_revision=_positive_int(
            data["project_glossary_revision"],
            "project_glossary_revision",
        ),
        terminology_mapping_candidate_ids=terminology_ids,
        consensus_level=_choice(
            data["consensus_level"],
            FRAMEWORK_ASSIGNMENT_CONSENSUS_LEVELS,
            "consensus_level",
        ),
        variance_level=_choice(
            data["variance_level"],
            FRAMEWORK_ASSIGNMENT_VARIANCE_LEVELS,
            "variance_level",
        ),
        confidence=_choice(
            data["confidence"],
            FRAMEWORK_ASSIGNMENT_CONFIDENCE_LEVELS,
            "confidence",
        ),
        confidence_rationale=_text(
            data["confidence_rationale"],
            "confidence_rationale",
        ),
        confirmation_required=confirmation_required,
        review_required=review_required,
        recommended_review_mode=review_mode,
        content_fingerprint=_sha256(
            data["content_fingerprint"],
            "content_fingerprint",
        ),
        created_at=_timestamp(data["created_at"], "created_at"),
    )
    expected_fingerprint = (
        calculate_framework_assignment_fingerprint(candidate)
    )
    if candidate.content_fingerprint != expected_fingerprint:
        raise FrameworkAssignmentIntegrityError(
            "Framework Assignment Candidate content_fingerprint "
            "does not match its content."
        )
    return candidate


def _parse_proposal(value: Any) -> FrameworkAssignmentProposal:
    data = _exact_object(
        value,
        _PROPOSAL_FIELDS,
        "Framework Assignment Proposal",
    )
    bases = tuple(
        create_framework_assignment_basis(
            basis_type=basis["basis_type"],
            reference_id=basis["reference_id"],
            reference_version=basis["reference_version"],
            rationale=basis["rationale"],
        )
        for basis in (
            _exact_object(
                item,
                _BASIS_FIELDS,
                "Framework Assignment Basis",
            )
            for item in _list(
                data["assignment_bases"],
                "assignment_bases",
            )
        )
    )
    return create_framework_assignment_proposal(
        framework_node_id=data["framework_node_id"],
        assignment_bases=bases,
        rationale=data["rationale"],
    )


def _parse_reference(
    value: Any,
) -> FrameworkAssignmentAgentCandidateReference:
    data = _exact_object(
        value,
        _REFERENCE_FIELDS,
        "Framework Assignment Agent Candidate Reference",
    )
    return FrameworkAssignmentAgentCandidateReference(
        persona_id=_identifier(
            data["persona_id"],
            _GENERAL_IDENTIFIER_PATTERN,
            "reference.persona_id",
        ),
        agent_id=_identifier(
            data["agent_id"],
            _GENERAL_IDENTIFIER_PATTERN,
            "reference.agent_id",
        ),
        persona_run_index=_positive_int(
            data["persona_run_index"],
            "reference.persona_run_index",
        ),
        framework_assignment_agent_candidate_id=(
            validate_framework_assignment_agent_candidate_id(
                data[
                    "framework_assignment_agent_candidate_id"
                ]
            )
        ),
    )


def _validate_status(
    status: str,
    proposals: tuple[FrameworkAssignmentProposal, ...],
) -> None:
    if status == "unassigned" and proposals:
        raise FrameworkAssignmentIntegrityError(
            "An unassigned candidate must not contain proposals."
        )
    if status == "assigned" and not proposals:
        raise FrameworkAssignmentIntegrityError(
            "An assigned candidate requires proposals."
        )
    if status in {"ambiguous", "conflict"} and len(proposals) < 2:
        raise FrameworkAssignmentIntegrityError(
            f"A {status} candidate requires at least two proposals."
        )
    if len(proposals) != len(set(proposals)):
        raise FrameworkAssignmentIntegrityError(
            "Duplicate proposals are not allowed."
        )
    node_ids = tuple(
        proposal.framework_node_id
        for proposal in proposals
    )
    if len(node_ids) != len(set(node_ids)):
        raise FrameworkAssignmentIntegrityError(
            "A candidate must not repeat a framework node."
        )


def _payload(
    candidate: FrameworkAssignmentCandidate,
) -> dict[str, Any]:
    if not isinstance(candidate, FrameworkAssignmentCandidate):
        raise FrameworkAssignmentValidationError(
            "candidate must be a FrameworkAssignmentCandidate."
        )
    return {
        "schema_version": candidate.schema_version,
        "project_id": candidate.project_id,
        "source_id": candidate.source_id,
        "source_projection_id": candidate.source_projection_id,
        "information_unit_id": candidate.information_unit_id,
        "framework_assignment_candidate_id": (
            candidate.framework_assignment_candidate_id
        ),
        "assignment_status": candidate.assignment_status,
        "proposals": [
            {
                "framework_node_id": proposal.framework_node_id,
                "assignment_bases": [
                    {
                        "basis_type": basis.basis_type,
                        "reference_id": basis.reference_id,
                        "reference_version": basis.reference_version,
                        "rationale": basis.rationale,
                    }
                    for basis in proposal.assignment_bases
                ],
                "rationale": proposal.rationale,
            }
            for proposal in candidate.proposals
        ],
        "candidate_references": [
            {
                "persona_id": reference.persona_id,
                "agent_id": reference.agent_id,
                "persona_run_index": reference.persona_run_index,
                "framework_assignment_agent_candidate_id": (
                    reference
                    .framework_assignment_agent_candidate_id
                ),
            }
            for reference in candidate.candidate_references
        ],
        "team_id": candidate.team_id,
        "required_personas": list(candidate.required_personas),
        "llm_provider": candidate.llm_provider,
        "llm_model": candidate.llm_model,
        "prompt_schema_version": candidate.prompt_schema_version,
        "framework_template_id": candidate.framework_template_id,
        "framework_template_version": (
            candidate.framework_template_version
        ),
        "turing_core_version": candidate.turing_core_version,
        "project_glossary_revision": (
            candidate.project_glossary_revision
        ),
        "terminology_mapping_candidate_ids": list(
            candidate.terminology_mapping_candidate_ids
        ),
        "consensus_level": candidate.consensus_level,
        "variance_level": candidate.variance_level,
        "confidence": candidate.confidence,
        "confidence_rationale": candidate.confidence_rationale,
        "confirmation_required": candidate.confirmation_required,
        "review_required": candidate.review_required,
        "recommended_review_mode": (
            candidate.recommended_review_mode
        ),
        "content_fingerprint": candidate.content_fingerprint,
        "created_at": candidate.created_at,
    }


def _exact_object(
    value: Any,
    expected: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FrameworkAssignmentValidationError(
            f"{label} must be an object."
        )
    actual = frozenset(value)
    if actual != expected:
        raise FrameworkAssignmentValidationError(
            f"{label} has invalid fields; "
            f"missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}."
        )
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise FrameworkAssignmentValidationError(
            f"{label} must be a list."
        )
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FrameworkAssignmentValidationError(
            f"{label} must be a non-empty string."
        )
    if value != value.strip():
        raise FrameworkAssignmentValidationError(
            f"{label} must not contain surrounding whitespace."
        )
    return value


def _identifier(
    value: Any,
    pattern: re.Pattern[str],
    label: str,
) -> str:
    selected = _text(value, label)
    if pattern.fullmatch(selected) is None:
        raise FrameworkAssignmentValidationError(
            f"{label} has invalid identifier syntax."
        )
    return selected


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise FrameworkAssignmentValidationError(
            f"{label} must be an integer."
        )
    if value < 1:
        raise FrameworkAssignmentValidationError(
            f"{label} must be greater than zero."
        )
    return value


def _choice(
    value: Any,
    choices: frozenset[str],
    label: str,
) -> str:
    selected = _text(value, label)
    if selected not in choices:
        raise FrameworkAssignmentValidationError(
            f"{label} must be one of {sorted(choices)!r}."
        )
    return selected


def _semver(value: Any, label: str) -> str:
    return _identifier(value, _SEMANTIC_VERSION_PATTERN, label)


def _sha256(value: Any, label: str) -> str:
    return _identifier(value, _SHA256_PATTERN, label)


def _timestamp(value: Any, label: str) -> str:
    return _identifier(value, _UTC_TIMESTAMP_PATTERN, label)


def _boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise FrameworkAssignmentValidationError(
            f"{label} must be a boolean."
        )
    return value


def _expected(value: Any, expected: str, label: str) -> str:
    if value != expected:
        raise FrameworkAssignmentValidationError(
            f"{label} must be {expected!r}."
        )
    return expected


def _expected_optional(
    actual: str,
    expected: str | None,
    label: str,
) -> None:
    if expected is not None and actual != expected:
        raise FrameworkAssignmentReferenceError(
            f"{label} must be {expected!r}, got {actual!r}."
        )


def _text_tuple(value: Any, label: str) -> tuple[str, ...]:
    selected = tuple(
        _text(item, label)
        for item in _list(value, label)
    )
    if not selected:
        raise FrameworkAssignmentIntegrityError(
            f"{label} must not be empty."
        )
    if len(selected) != len(set(selected)):
        raise FrameworkAssignmentIntegrityError(
            f"{label} must not contain duplicates."
        )
    return selected


def _identifier_tuple(
    value: Any,
    pattern: re.Pattern[str],
    label: str,
) -> tuple[str, ...]:
    selected = tuple(
        _identifier(item, pattern, label)
        for item in _list(value, label)
    )
    if len(selected) != len(set(selected)):
        raise FrameworkAssignmentIntegrityError(
            f"{label} must not contain duplicates."
        )
    return selected


def _without_duplicate_keys(
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