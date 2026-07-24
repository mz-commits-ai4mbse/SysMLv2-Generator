"""Strict manifest for immutable terminology mapping candidates."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from hashlib import sha256
import json
import re
from typing import Any

from .agent_manifest import (
    create_terminology_mapping_agent_candidate,
    create_terminology_mapping_basis,
    create_terminology_mapping_proposal,
    create_terminology_mapping_target,
)
from .analyzer import TerminologyMappingConsensusResult
from .errors import (
    TerminologyMappingIntegrityError,
    TerminologyMappingReferenceError,
    TerminologyMappingValidationError,
)
from .identifiers import (
    validate_terminology_mapping_agent_candidate_id,
    validate_terminology_mapping_candidate_id,
)
from .types import (
    TERMINOLOGY_MAPPING_CONFIDENCE_LEVELS,
    TERMINOLOGY_MAPPING_CONSENSUS_LEVELS,
    TERMINOLOGY_MAPPING_ISSUE_LEVELS,
    TERMINOLOGY_MAPPING_REVIEW_MODES,
    TERMINOLOGY_MAPPING_STATUSES,
    TERMINOLOGY_MAPPING_VARIANCE_LEVELS,
    TerminologyMappingAgentCandidateReference,
    TerminologyMappingCandidate,
    TerminologyMappingConsensusOutcome,
    TerminologyMappingProposal,
    TerminologyOccurrence,
)


TERMINOLOGY_MAPPING_CANDIDATE_SCHEMA_VERSION = "1.0.0"

_PROJECT_ID = re.compile(r"^[0-9]{6}$")
_SOURCE_ID = re.compile(r"^SRC-[0-9]{6}$")
_PROJECTION_ID = re.compile(r"^SP-[0-9]{6}$")
_INFORMATION_UNIT_ID = re.compile(r"^IU-[0-9]{6}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_UTC = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)

_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "source_id",
        "source_projection_id",
        "information_unit_id",
        "terminology_mapping_candidate_id",
        "occurrence",
        "mapping_status",
        "proposals",
        "candidate_references",
        "team_id",
        "required_personas",
        "llm_provider",
        "llm_model",
        "prompt_schema_version",
        "ontology_registry_version",
        "reference_concept_index_version",
        "turing_core_version",
        "project_glossary_revision",
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


def create_terminology_mapping_candidate(
    *,
    consensus_result: TerminologyMappingConsensusResult,
    outcome: TerminologyMappingConsensusOutcome,
    terminology_mapping_candidate_id: str,
    timestamp: str,
) -> TerminologyMappingCandidate:
    """Create one persisted candidate from one consensus outcome."""

    if not isinstance(
        consensus_result,
        TerminologyMappingConsensusResult,
    ):
        raise TerminologyMappingValidationError(
            "consensus_result must be a "
            "TerminologyMappingConsensusResult."
        )
    if not isinstance(
        outcome,
        TerminologyMappingConsensusOutcome,
    ):
        raise TerminologyMappingValidationError(
            "outcome must be a TerminologyMappingConsensusOutcome."
        )
    if outcome not in consensus_result.outcomes:
        raise TerminologyMappingReferenceError(
            "outcome is not part of consensus_result."
        )
    if not outcome.persistence_eligible:
        raise TerminologyMappingIntegrityError(
            "Only a persistence-eligible consensus outcome can "
            "create a mapping candidate."
        )
    candidate_id = validate_terminology_mapping_candidate_id(
        terminology_mapping_candidate_id
    )

    candidate = TerminologyMappingCandidate(
        schema_version=(
            TERMINOLOGY_MAPPING_CANDIDATE_SCHEMA_VERSION
        ),
        project_id=consensus_result.project_id,
        source_id=consensus_result.source_id,
        source_projection_id=(
            consensus_result.source_projection_id
        ),
        information_unit_id=(
            consensus_result.information_unit_id
        ),
        terminology_mapping_candidate_id=candidate_id,
        occurrence=outcome.occurrence,
        mapping_status=outcome.mapping_status,
        proposals=outcome.selected_proposals,
        candidate_references=outcome.candidate_references,
        team_id=consensus_result.team_id,
        required_personas=consensus_result.required_personas,
        llm_provider=consensus_result.llm_provider,
        llm_model=consensus_result.llm_model,
        prompt_schema_version=(
            consensus_result.prompt_schema_version
        ),
        ontology_registry_version=(
            consensus_result.ontology_registry_version
        ),
        reference_concept_index_version=(
            consensus_result.reference_concept_index_version
        ),
        turing_core_version=(
            consensus_result.turing_core_version
        ),
        project_glossary_revision=(
            consensus_result.project_glossary_revision
        ),
        consensus_level=outcome.consensus_level,
        variance_level=outcome.variance_level,
        confidence=outcome.confidence,
        confidence_rationale=outcome.confidence_rationale,
        confirmation_required=outcome.confirmation_required,
        review_required=outcome.review_required,
        recommended_review_mode=(
            outcome.recommended_review_mode
        ),
        content_fingerprint="0" * 64,
        created_at=timestamp,
    )
    fingerprint = calculate_terminology_mapping_fingerprint(
        candidate
    )
    candidate = TerminologyMappingCandidate(
        **{
            **asdict(candidate),
            "occurrence": candidate.occurrence,
            "proposals": candidate.proposals,
            "candidate_references": (
                candidate.candidate_references
            ),
            "required_personas": candidate.required_personas,
            "content_fingerprint": fingerprint,
        }
    )
    validate_terminology_mapping_candidate(candidate)
    return candidate


def calculate_terminology_mapping_fingerprint(
    candidate: TerminologyMappingCandidate,
) -> str:
    """Hash professional mapping content and all authority versions."""

    payload = _payload(candidate, include_fingerprint=False)
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def validate_terminology_mapping_candidate(
    candidate: TerminologyMappingCandidate,
) -> None:
    """Validate one immutable mapping candidate."""

    terminology_mapping_candidate_to_dict(candidate)


def terminology_mapping_candidate_to_dict(
    candidate: TerminologyMappingCandidate,
) -> dict[str, Any]:
    """Return the strict canonical JSON-compatible representation."""

    if not isinstance(candidate, TerminologyMappingCandidate):
        raise TerminologyMappingValidationError(
            "candidate must be a TerminologyMappingCandidate."
        )
    validated = parse_terminology_mapping_candidate(
        _payload(candidate)
    )
    return _payload(validated)


def terminology_mapping_candidate_to_json(
    candidate: TerminologyMappingCandidate,
) -> str:
    """Serialize one candidate deterministically."""

    return (
        json.dumps(
            terminology_mapping_candidate_to_dict(candidate),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def terminology_mapping_candidate_from_json(
    text: str,
    *,
    expected_project_id: str | None = None,
    expected_information_unit_id: str | None = None,
    expected_terminology_mapping_candidate_id: str | None = None,
) -> TerminologyMappingCandidate:
    """Parse strict JSON without duplicate object keys."""

    if not isinstance(text, str):
        raise TerminologyMappingValidationError(
            "Terminology Mapping Candidate JSON must be a string."
        )
    try:
        payload = json.loads(
            text,
            object_pairs_hook=_without_duplicate_keys,
        )
    except TerminologyMappingValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise TerminologyMappingValidationError(
            f"Invalid Terminology Mapping Candidate JSON: {exc}."
        ) from exc
    return parse_terminology_mapping_candidate(
        payload,
        expected_project_id=expected_project_id,
        expected_information_unit_id=(
            expected_information_unit_id
        ),
        expected_terminology_mapping_candidate_id=(
            expected_terminology_mapping_candidate_id
        ),
    )


def parse_terminology_mapping_candidate(
    payload: Any,
    *,
    expected_project_id: str | None = None,
    expected_information_unit_id: str | None = None,
    expected_terminology_mapping_candidate_id: str | None = None,
) -> TerminologyMappingCandidate:
    """Parse and validate one exact candidate payload."""

    item = _exact_object(payload, _FIELDS, "candidate")
    if (
        item["schema_version"]
        != TERMINOLOGY_MAPPING_CANDIDATE_SCHEMA_VERSION
    ):
        raise TerminologyMappingValidationError(
            "Unsupported candidate schema_version."
        )
    project_id = _identifier(
        item["project_id"],
        _PROJECT_ID,
        "project_id",
        "000000",
    )
    source_id = _identifier(
        item["source_id"],
        _SOURCE_ID,
        "source_id",
        "SRC-000000",
    )
    projection_id = _identifier(
        item["source_projection_id"],
        _PROJECTION_ID,
        "source_projection_id",
        "SP-000000",
    )
    information_unit_id = _identifier(
        item["information_unit_id"],
        _INFORMATION_UNIT_ID,
        "information_unit_id",
        "IU-000000",
    )
    candidate_id = validate_terminology_mapping_candidate_id(
        item["terminology_mapping_candidate_id"]
    )
    occurrence = _parse_occurrence(item["occurrence"])
    if occurrence.information_unit_id != information_unit_id:
        raise TerminologyMappingIntegrityError(
            "Occurrence Information Unit does not match candidate."
        )
    status = _choice(
        item["mapping_status"],
        TERMINOLOGY_MAPPING_STATUSES,
        "mapping_status",
    )
    proposals = tuple(
        _parse_proposal(value)
        for value in _list(item["proposals"], "proposals")
    )
    references = tuple(
        _parse_reference(value)
        for value in _list(
            item["candidate_references"],
            "candidate_references",
        )
    )
    if not references:
        raise TerminologyMappingIntegrityError(
            "candidate_references must not be empty."
        )
    if len(references) != len(set(references)):
        raise TerminologyMappingIntegrityError(
            "candidate_references must not contain duplicates."
        )

    team_id = _text(item["team_id"], "team_id")
    personas = tuple(
        _text(value, "required_personas item")
        for value in _list(
            item["required_personas"],
            "required_personas",
        )
    )
    if (
        not personas
        or len(personas) != len(set(personas))
        or personas != tuple(sorted(personas))
    ):
        raise TerminologyMappingIntegrityError(
            "required_personas must be non-empty, unique and sorted."
        )
    if not {
        reference.persona_id for reference in references
    }.issubset(set(personas)):
        raise TerminologyMappingIntegrityError(
            "candidate_references contain a non-required persona."
        )
    provider = _text(item["llm_provider"], "llm_provider")
    model = _text(item["llm_model"], "llm_model")
    prompt_version = _semver(
        item["prompt_schema_version"],
        "prompt_schema_version",
    )
    registry_version = _semver(
        item["ontology_registry_version"],
        "ontology_registry_version",
    )
    index_version = _semver(
        item["reference_concept_index_version"],
        "reference_concept_index_version",
    )
    turing_version = _semver(
        item["turing_core_version"],
        "turing_core_version",
    )
    glossary_revision = _positive_int(
        item["project_glossary_revision"],
        "project_glossary_revision",
    )
    consensus = _choice(
        item["consensus_level"],
        TERMINOLOGY_MAPPING_CONSENSUS_LEVELS,
        "consensus_level",
    )
    variance = _choice(
        item["variance_level"],
        TERMINOLOGY_MAPPING_VARIANCE_LEVELS,
        "variance_level",
    )
    confidence = _choice(
        item["confidence"],
        TERMINOLOGY_MAPPING_CONFIDENCE_LEVELS,
        "confidence",
    )
    confidence_rationale = _text(
        item["confidence_rationale"],
        "confidence_rationale",
    )
    confirmation_required = _boolean(
        item["confirmation_required"],
        "confirmation_required",
    )
    review_required = _boolean(
        item["review_required"],
        "review_required",
    )
    review_mode = _choice(
        item["recommended_review_mode"],
        TERMINOLOGY_MAPPING_REVIEW_MODES,
        "recommended_review_mode",
    )
    fingerprint = _sha256(
        item["content_fingerprint"],
        "content_fingerprint",
    )
    created_at = _timestamp(item["created_at"], "created_at")

    _validate_status(status, proposals)
    if confirmation_required is not True:
        raise TerminologyMappingIntegrityError(
            "Every mapping candidate requires human confirmation."
        )
    if status in {"ambiguous", "conflict"}:
        if not review_required or review_mode != "detailed_review":
            raise TerminologyMappingIntegrityError(
                "Ambiguous and conflict candidates require "
                "detailed review."
            )
    if review_required != (review_mode == "detailed_review"):
        raise TerminologyMappingIntegrityError(
            "review_required and recommended_review_mode disagree."
        )
    if confidence == "high" and (
        consensus != "unanimous" or variance != "low"
    ):
        raise TerminologyMappingIntegrityError(
            "High confidence requires unanimous low-variance "
            "mapping consensus."
        )
    if confidence != "high" and not review_required:
        raise TerminologyMappingIntegrityError(
            "Medium and low confidence require detailed review."
        )

    candidate = TerminologyMappingCandidate(
        schema_version=item["schema_version"],
        project_id=project_id,
        source_id=source_id,
        source_projection_id=projection_id,
        information_unit_id=information_unit_id,
        terminology_mapping_candidate_id=candidate_id,
        occurrence=occurrence,
        mapping_status=status,
        proposals=proposals,
        candidate_references=references,
        team_id=team_id,
        required_personas=personas,
        llm_provider=provider,
        llm_model=model,
        prompt_schema_version=prompt_version,
        ontology_registry_version=registry_version,
        reference_concept_index_version=index_version,
        turing_core_version=turing_version,
        project_glossary_revision=glossary_revision,
        consensus_level=consensus,
        variance_level=variance,
        confidence=confidence,
        confidence_rationale=confidence_rationale,
        confirmation_required=confirmation_required,
        review_required=review_required,
        recommended_review_mode=review_mode,
        content_fingerprint=fingerprint,
        created_at=created_at,
    )
    if calculate_terminology_mapping_fingerprint(candidate) != fingerprint:
        raise TerminologyMappingIntegrityError(
            "Candidate content_fingerprint does not match content."
        )
    _expected(project_id, expected_project_id, "project_id")
    _expected(
        information_unit_id,
        expected_information_unit_id,
        "information_unit_id",
    )
    _expected(
        candidate_id,
        expected_terminology_mapping_candidate_id,
        "terminology_mapping_candidate_id",
    )
    return candidate


def _parse_occurrence(value: Any) -> TerminologyOccurrence:
    fields = frozenset(
        {
            "information_unit_id",
            "text_field",
            "start_offset",
            "end_offset",
            "term_text",
        }
    )
    item = _exact_object(value, fields, "occurrence")
    occurrence = TerminologyOccurrence(
        information_unit_id=_identifier(
            item["information_unit_id"],
            _INFORMATION_UNIT_ID,
            "occurrence.information_unit_id",
            "IU-000000",
        ),
        text_field=_choice(
            item["text_field"],
            frozenset(
                {"source_excerpt", "interpreted_statement"}
            ),
            "occurrence.text_field",
        ),
        start_offset=_non_negative_int(
            item["start_offset"],
            "occurrence.start_offset",
        ),
        end_offset=_positive_int(
            item["end_offset"],
            "occurrence.end_offset",
        ),
        term_text=_text(
            item["term_text"],
            "occurrence.term_text",
        ),
    )
    create_terminology_mapping_agent_candidate(
        terminology_mapping_agent_candidate_id="TMAC-000001",
        occurrence=occurrence,
        mapping_status="unmapped",
        proposals=(),
        rationale="Structural occurrence validation.",
    )
    return occurrence


def _parse_proposal(value: Any) -> TerminologyMappingProposal:
    item = _exact_object(
        value,
        frozenset(
            {
                "mapping_relation",
                "target",
                "mapping_bases",
                "rationale",
            }
        ),
        "proposal",
    )
    target_value = item["target"]
    target = None
    if target_value is not None:
        target_item = _exact_object(
            target_value,
            frozenset(
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
            ),
            "target",
        )
        target = create_terminology_mapping_target(**target_item)
    bases = []
    for basis_value in _list(
        item["mapping_bases"],
        "mapping_bases",
    ):
        basis_item = _exact_object(
            basis_value,
            frozenset(
                {
                    "basis_type",
                    "reference_id",
                    "reference_version",
                    "rationale",
                }
            ),
            "mapping_basis",
        )
        bases.append(
            create_terminology_mapping_basis(**basis_item)
        )
    return create_terminology_mapping_proposal(
        mapping_relation=item["mapping_relation"],
        target=target,
        mapping_bases=bases,
        rationale=item["rationale"],
    )


def _parse_reference(
    value: Any,
) -> TerminologyMappingAgentCandidateReference:
    item = _exact_object(
        value,
        frozenset(
            {
                "persona_id",
                "agent_id",
                "persona_run_index",
                "terminology_mapping_agent_candidate_id",
            }
        ),
        "candidate_reference",
    )
    return TerminologyMappingAgentCandidateReference(
        persona_id=_text(item["persona_id"], "persona_id"),
        agent_id=_text(item["agent_id"], "agent_id"),
        persona_run_index=_positive_int(
            item["persona_run_index"],
            "persona_run_index",
        ),
        terminology_mapping_agent_candidate_id=(
            validate_terminology_mapping_agent_candidate_id(
                item["terminology_mapping_agent_candidate_id"]
            )
        ),
    )


def _validate_status(
    status: str,
    proposals: tuple[TerminologyMappingProposal, ...],
) -> None:
    create_terminology_mapping_agent_candidate(
        terminology_mapping_agent_candidate_id="TMAC-000001",
        occurrence=TerminologyOccurrence(
            information_unit_id="IU-000001",
            text_field="interpreted_statement",
            start_offset=0,
            end_offset=1,
            term_text="x",
        ),
        mapping_status=status,
        proposals=proposals,
        rationale="Structural mapping-status validation.",
    )


def _payload(
    candidate: TerminologyMappingCandidate,
    *,
    include_fingerprint: bool = True,
) -> dict[str, Any]:
    if not isinstance(candidate, TerminologyMappingCandidate):
        raise TerminologyMappingValidationError(
            "candidate must be a TerminologyMappingCandidate."
        )
    value = json.loads(
        json.dumps(
            asdict(candidate),
            ensure_ascii=False,
        )
    )
    if not include_fingerprint:
        value.pop("content_fingerprint")
        value.pop("terminology_mapping_candidate_id")
        value.pop("created_at")
    return value


def _exact_object(
    value: Any,
    fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TerminologyMappingValidationError(
            f"{label} must be an object."
        )
    actual = frozenset(value)
    if actual != fields:
        raise TerminologyMappingValidationError(
            f"{label} has missing or unknown fields."
        )
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise TerminologyMappingValidationError(
            f"{label} must be a list."
        )
    return value


def _text(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(character) < 32 for character in value)
    ):
        raise TerminologyMappingValidationError(
            f"{label} must be trimmed stored text."
        )
    return value


def _identifier(
    value: Any,
    pattern: re.Pattern[str],
    label: str,
    zero: str,
) -> str:
    if (
        not isinstance(value, str)
        or pattern.fullmatch(value) is None
        or value == zero
    ):
        raise TerminologyMappingValidationError(
            f"{label} has invalid identifier format."
        )
    return value


def _positive_int(value: Any, label: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise TerminologyMappingValidationError(
            f"{label} must be a positive integer."
        )
    return value


def _non_negative_int(value: Any, label: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
    ):
        raise TerminologyMappingValidationError(
            f"{label} must be a non-negative integer."
        )
    return value


def _choice(
    value: Any,
    choices: frozenset[str],
    label: str,
) -> str:
    selected = _text(value, label)
    if selected not in choices:
        raise TerminologyMappingValidationError(
            f"{label} must be one of {sorted(choices)}."
        )
    return selected


def _semver(value: Any, label: str) -> str:
    selected = _text(value, label)
    if _SEMVER.fullmatch(selected) is None:
        raise TerminologyMappingValidationError(
            f"{label} must be a semantic version."
        )
    return selected


def _sha256(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or _SHA256.fullmatch(value) is None
    ):
        raise TerminologyMappingValidationError(
            f"{label} must be a lowercase SHA-256."
        )
    return value


def _timestamp(value: Any, label: str) -> str:
    selected = _text(value, label)
    if _UTC.fullmatch(selected) is None:
        raise TerminologyMappingValidationError(
            f"{label} must be an ISO 8601 UTC timestamp."
        )
    try:
        datetime.fromisoformat(
            selected.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise TerminologyMappingValidationError(
            f"{label} is not a valid timestamp."
        ) from exc
    return selected


def _boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise TerminologyMappingValidationError(
            f"{label} must be a boolean."
        )
    return value


def _expected(
    actual: str,
    expected: str | None,
    label: str,
) -> None:
    if expected is not None and actual != expected:
        raise TerminologyMappingReferenceError(
            f"{label} does not match expected value."
        )


def _without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise TerminologyMappingValidationError(
                f"Duplicate JSON key: {key!r}."
            )
        result[key] = value
    return result