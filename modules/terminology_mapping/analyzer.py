"""Deterministic multi-persona terminology mapping consensus."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import json
import unicodedata
from typing import Any

from modules.information_units.types import InformationUnit

from .agent_manifest import (
    validate_terminology_mapping_agent_result,
)
from .errors import (
    DuplicateTerminologyMappingAgentResultError,
    IncomparableTerminologyMappingClusterError,
    TerminologyMappingComparisonError,
    TerminologyMappingConfigurationError,
    TerminologyMappingReferenceError,
    TerminologyMappingValidationError,
)
from .types import (
    TerminologyMappingAgentCandidate,
    TerminologyMappingAgentCandidateReference,
    TerminologyMappingAgentResult,
    TerminologyMappingConsensusOutcome,
    TerminologyMappingIssue,
    TerminologyMappingProposal,
    TerminologyMappingValueDistribution,
    TerminologyOccurrence,
)


TERMINOLOGY_MAPPING_CONSENSUS_SCHEMA_VERSION = "1.0.0"
TERMINOLOGY_MAPPING_NORMALIZATION_ID = (
    "unicode_nfkc_whitespace_casefold"
)
TERMINOLOGY_MAPPING_NORMALIZATION_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class TerminologyMappingConsensusResult:
    """Auditable deterministic consensus for one Information Unit."""

    schema_version: str
    project_id: str
    source_id: str
    source_projection_id: str
    information_unit_id: str
    team_id: str
    required_personas: tuple[str, ...]
    persona_run_expectations: tuple[tuple[str, int], ...]
    llm_provider: str
    llm_model: str
    prompt_schema_version: str
    ontology_registry_version: str
    reference_concept_index_version: str
    turing_core_version: str
    project_glossary_revision: int
    outcomes: tuple[TerminologyMappingConsensusOutcome, ...]
    issues: tuple[TerminologyMappingIssue, ...]
    created_at: str


@dataclass(frozen=True, slots=True)
class _CandidateOccurrence:
    """Internal candidate occurrence with its persona-run provenance."""

    result: TerminologyMappingAgentResult
    candidate: TerminologyMappingAgentCandidate


@dataclass(frozen=True, slots=True)
class _PersonaVote:
    """One collapsed vote and stability state for one persona."""

    persona_id: str
    candidate: TerminologyMappingAgentCandidate | None
    references: tuple[
        TerminologyMappingAgentCandidateReference,
        ...
    ]
    stability: str
    omitted_run_indices: tuple[int, ...]


def analyze_terminology_mapping_consensus(
    *,
    agent_results: Iterable[TerminologyMappingAgentResult],
    required_personas: Iterable[str],
    expected_runs_per_persona: Mapping[str, int],
    information_unit: InformationUnit,
    timestamp: str,
) -> TerminologyMappingConsensusResult:
    """Derive deterministic consensus without LLM self-confidence."""

    results = _require_agent_results(agent_results)
    personas = _require_required_personas(required_personas)
    expectations = _require_run_expectations(
        expected_runs_per_persona,
        personas,
    )
    _require_information_unit(information_unit)
    _validate_result_configuration(
        results,
        personas=personas,
        expectations=expectations,
        information_unit=information_unit,
    )
    created_at = _require_timestamp(timestamp)

    issues = list(
        _team_issues(
            results,
            personas=personas,
            expectations=expectations,
            project_id=information_unit.project_id,
        )
    )
    buckets = _collect_occurrence_buckets(results)
    outcomes: list[TerminologyMappingConsensusOutcome] = []

    for occurrence_key in sorted(buckets):
        outcome, outcome_issues = _analyze_occurrence_bucket(
            buckets[occurrence_key],
            all_results=results,
            personas=personas,
            expectations=expectations,
            project_id=information_unit.project_id,
        )
        outcomes.append(outcome)
        issues.extend(outcome_issues)

    if not outcomes:
        issues.append(
            TerminologyMappingIssue(
                project_id=information_unit.project_id,
                code="no_terminology_mapping_candidates",
                message=(
                    "No persona produced a terminology mapping "
                    "candidate."
                ),
                issue_level="warning",
                information_unit_id=(
                    information_unit.information_unit_id
                ),
            )
        )

    first = results[0]
    return TerminologyMappingConsensusResult(
        schema_version=(
            TERMINOLOGY_MAPPING_CONSENSUS_SCHEMA_VERSION
        ),
        project_id=information_unit.project_id,
        source_id=information_unit.source_id,
        source_projection_id=(
            information_unit.source_projection_id
        ),
        information_unit_id=(
            information_unit.information_unit_id
        ),
        team_id=first.team_id,
        required_personas=personas,
        persona_run_expectations=tuple(
            (persona_id, expectations[persona_id])
            for persona_id in personas
        ),
        llm_provider=first.llm_provider,
        llm_model=first.llm_model,
        prompt_schema_version=first.prompt_schema_version,
        ontology_registry_version=(
            first.ontology_registry_version
        ),
        reference_concept_index_version=(
            first.reference_concept_index_version
        ),
        turing_core_version=first.turing_core_version,
        project_glossary_revision=(
            first.project_glossary_revision
        ),
        outcomes=tuple(outcomes),
        issues=tuple(sorted(issues, key=_issue_sort_key)),
        created_at=created_at,
    )


def terminology_occurrence_key(
    occurrence: TerminologyOccurrence,
) -> tuple[str, int, int, str]:
    """Return the exact evidence key used to align occurrences."""

    if not isinstance(occurrence, TerminologyOccurrence):
        raise TerminologyMappingComparisonError(
            "occurrence must be a TerminologyOccurrence."
        )
    return (
        occurrence.text_field,
        occurrence.start_offset,
        occurrence.end_offset,
        occurrence.term_text,
    )


def terminology_mapping_signature(
    candidate: TerminologyMappingAgentCandidate,
) -> str:
    """Return the canonical professional mapping signature."""

    if not isinstance(
        candidate,
        TerminologyMappingAgentCandidate,
    ):
        raise TerminologyMappingComparisonError(
            "candidate must be a "
            "TerminologyMappingAgentCandidate."
        )
    proposals = sorted(
        (
            {
                "mapping_relation": proposal.mapping_relation,
                "target": _target_signature_payload(
                    proposal.target
                ),
                "mapping_bases": sorted(
                    (
                        {
                            "basis_type": basis.basis_type,
                            "reference_id": basis.reference_id,
                            "reference_version": (
                                basis.reference_version
                            ),
                        }
                        for basis in proposal.mapping_bases
                    ),
                    key=_canonical_json,
                ),
            }
            for proposal in candidate.proposals
        ),
        key=_canonical_json,
    )
    return _canonical_json(
        {
            "mapping_status": candidate.mapping_status,
            "proposals": proposals,
        }
    )


def normalize_terminology_mapping_text(value: object) -> str:
    """Apply lexical normalization without semantic inference."""

    if not isinstance(value, str):
        raise TerminologyMappingComparisonError(
            "Mapping comparison text must be a string."
        )
    normalized = unicodedata.normalize("NFKC", value)
    normalized = " ".join(normalized.split()).casefold()
    if not normalized:
        raise TerminologyMappingComparisonError(
            "Mapping comparison text must not be empty."
        )
    return normalized


def _require_agent_results(
    values: Iterable[TerminologyMappingAgentResult],
) -> tuple[TerminologyMappingAgentResult, ...]:
    if isinstance(values, (str, bytes)):
        raise TerminologyMappingValidationError(
            "agent_results must be an iterable of results."
        )
    try:
        results = tuple(values)
    except TypeError as exc:
        raise TerminologyMappingValidationError(
            "agent_results must be iterable."
        ) from exc
    if not results:
        raise TerminologyMappingConfigurationError(
            "At least one mapping agent result is required."
        )
    if any(
        not isinstance(result, TerminologyMappingAgentResult)
        for result in results
    ):
        raise TerminologyMappingValidationError(
            "agent_results must contain only "
            "TerminologyMappingAgentResult values."
        )
    keys = tuple(
        (
            result.persona_id,
            result.persona_run_index,
        )
        for result in results
    )
    if len(keys) != len(set(keys)):
        raise DuplicateTerminologyMappingAgentResultError(
            "Duplicate persona-run mapping results are not "
            "allowed."
        )
    return tuple(
        sorted(
            results,
            key=lambda result: (
                result.persona_id,
                result.persona_run_index,
                result.agent_id,
            ),
        )
    )


def _require_required_personas(
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TerminologyMappingConfigurationError(
            "required_personas must be an iterable of strings."
        )
    try:
        personas = tuple(values)
    except TypeError as exc:
        raise TerminologyMappingConfigurationError(
            "required_personas must be iterable."
        ) from exc
    if not personas:
        raise TerminologyMappingConfigurationError(
            "required_personas must not be empty."
        )
    if any(
        not isinstance(persona, str)
        or not persona
        or persona != persona.strip()
        for persona in personas
    ):
        raise TerminologyMappingConfigurationError(
            "required_personas must contain trimmed strings."
        )
    if len(personas) != len(set(personas)):
        raise TerminologyMappingConfigurationError(
            "required_personas must not contain duplicates."
        )
    return tuple(sorted(personas))


def _require_run_expectations(
    values: Mapping[str, int],
    personas: tuple[str, ...],
) -> dict[str, int]:
    if not isinstance(values, Mapping):
        raise TerminologyMappingConfigurationError(
            "expected_runs_per_persona must be a mapping."
        )
    if set(values) != set(personas):
        raise TerminologyMappingConfigurationError(
            "expected_runs_per_persona keys must exactly match "
            "required_personas."
        )
    expectations: dict[str, int] = {}
    for persona_id in personas:
        count = values[persona_id]
        if (
            isinstance(count, bool)
            or not isinstance(count, int)
            or count < 1
        ):
            raise TerminologyMappingConfigurationError(
                "Every expected persona run count must be a "
                "positive integer."
            )
        expectations[persona_id] = count
    return expectations


def _require_information_unit(value: object) -> InformationUnit:
    if not isinstance(value, InformationUnit):
        raise TerminologyMappingValidationError(
            "information_unit must be an InformationUnit."
        )
    return value


def _validate_result_configuration(
    results: tuple[TerminologyMappingAgentResult, ...],
    *,
    personas: tuple[str, ...],
    expectations: Mapping[str, int],
    information_unit: InformationUnit,
) -> None:
    first = results[0]
    fields = (
        "project_id",
        "source_id",
        "source_projection_id",
        "information_unit_id",
        "team_id",
        "llm_provider",
        "llm_model",
        "prompt_schema_version",
        "ontology_registry_version",
        "reference_concept_index_version",
        "turing_core_version",
        "project_glossary_revision",
    )
    for result in results:
        validate_terminology_mapping_agent_result(
            result,
            information_unit=information_unit,
        )
        if result.persona_id not in personas:
            raise TerminologyMappingConfigurationError(
                "Agent result persona_id is not a required "
                f"persona: {result.persona_id!r}."
            )
        if (
            result.persona_run_index
            > expectations[result.persona_id]
        ):
            raise TerminologyMappingConfigurationError(
                "persona_run_index exceeds its configured "
                "expected run count."
            )
        for field_name in fields:
            if getattr(result, field_name) != getattr(
                first,
                field_name,
            ):
                raise TerminologyMappingConfigurationError(
                    "Mapping agent results disagree on "
                    f"{field_name}."
                )

    for field_name in (
        "project_id",
        "source_id",
        "source_projection_id",
        "information_unit_id",
    ):
        if getattr(first, field_name) != getattr(
            information_unit,
            field_name,
        ):
            raise TerminologyMappingReferenceError(
                "Mapping results do not match the supplied "
                f"Information Unit {field_name}."
            )

    fingerprints: dict[str, set[str]] = defaultdict(set)
    for result in results:
        fingerprints[result.persona_id].add(
            result.persona_configuration_fingerprint
        )
    unstable_configuration = tuple(
        persona_id
        for persona_id, values in fingerprints.items()
        if len(values) != 1
    )
    if unstable_configuration:
        raise TerminologyMappingConfigurationError(
            "One persona uses multiple configuration "
            "fingerprints: "
            + ", ".join(sorted(unstable_configuration))
            + "."
        )


def _team_issues(
    results: tuple[TerminologyMappingAgentResult, ...],
    *,
    personas: tuple[str, ...],
    expectations: Mapping[str, int],
    project_id: str,
) -> tuple[TerminologyMappingIssue, ...]:
    observed: dict[str, set[int]] = defaultdict(set)
    for result in results:
        observed[result.persona_id].add(
            result.persona_run_index
        )
    issues = []
    for persona_id in personas:
        expected_indices = set(
            range(1, expectations[persona_id] + 1)
        )
        missing = tuple(
            sorted(expected_indices - observed[persona_id])
        )
        if missing:
            issues.append(
                TerminologyMappingIssue(
                    project_id=project_id,
                    code="missing_persona_run",
                    message=(
                        f"Persona {persona_id!r} is missing runs "
                        f"{missing}."
                    ),
                    issue_level="blocking",
                    persona_id=persona_id,
                )
            )
    return tuple(issues)


def _collect_occurrence_buckets(
    results: tuple[TerminologyMappingAgentResult, ...],
) -> dict[
    tuple[str, int, int, str],
    tuple[_CandidateOccurrence, ...],
]:
    buckets: dict[
        tuple[str, int, int, str],
        list[_CandidateOccurrence],
    ] = defaultdict(list)
    for result in results:
        for candidate in result.candidates:
            buckets[
                terminology_occurrence_key(candidate.occurrence)
            ].append(
                _CandidateOccurrence(
                    result=result,
                    candidate=candidate,
                )
            )
    return {
        key: tuple(
            sorted(
                occurrences,
                key=lambda item: (
                    item.result.persona_id,
                    item.result.persona_run_index,
                    item.candidate.terminology_mapping_agent_candidate_id,
                ),
            )
        )
        for key, occurrences in buckets.items()
    }


def _analyze_occurrence_bucket(
    occurrences: tuple[_CandidateOccurrence, ...],
    *,
    all_results: tuple[TerminologyMappingAgentResult, ...],
    personas: tuple[str, ...],
    expectations: Mapping[str, int],
    project_id: str,
) -> tuple[
    TerminologyMappingConsensusOutcome,
    tuple[TerminologyMappingIssue, ...],
]:
    if not occurrences:
        raise IncomparableTerminologyMappingClusterError(
            "An occurrence bucket must not be empty."
        )
    reference_occurrence = occurrences[0].candidate.occurrence
    votes, issues = _collapse_persona_runs(
        occurrences,
        all_results=all_results,
        personas=personas,
        expectations=expectations,
        project_id=project_id,
        information_unit_id=(
            reference_occurrence.information_unit_id
        ),
    )
    available_votes = tuple(
        vote for vote in votes if vote.candidate is not None
    )
    distribution = _signature_distribution(available_votes)
    selected_signature = _select_unique_mode(distribution)

    incomplete = any(
        vote.stability in {"incomplete", "indeterminate"}
        for vote in votes
    )
    unstable = any(
        vote.stability == "unstable"
        for vote in votes
    )
    supporting_personas: tuple[str, ...] = ()
    dissenting_personas: tuple[str, ...] = ()
    omitting_personas = tuple(
        vote.persona_id
        for vote in votes
        if vote.candidate is None
    )
    selected_candidate: (
        TerminologyMappingAgentCandidate | None
    ) = None

    if selected_signature is not None:
        supporting_personas = tuple(
            vote.persona_id
            for vote in available_votes
            if terminology_mapping_signature(vote.candidate)
            == selected_signature
        )
        dissenting_personas = tuple(
            vote.persona_id
            for vote in available_votes
            if terminology_mapping_signature(vote.candidate)
            != selected_signature
        )
        selected_candidate = _representative_candidate(
            available_votes,
            selected_signature,
        )

    total = len(personas)
    support = len(supporting_personas)
    if incomplete or omitting_personas:
        consensus_level = "incomplete"
        variance_level = "high"
        confidence = "low"
    elif selected_signature is None:
        consensus_level = "incomparable"
        variance_level = "high"
        confidence = "low"
    elif support == total:
        consensus_level = "unanimous"
        variance_level = "low"
        confidence = "medium" if unstable else "high"
    elif support > total / 2:
        consensus_level = "majority"
        variance_level = "medium"
        confidence = "medium"
    elif support == 1:
        consensus_level = "single"
        variance_level = "high"
        confidence = "low"
    else:
        consensus_level = "incomparable"
        variance_level = "high"
        confidence = "low"

    status = (
        "unmapped"
        if selected_candidate is None
        else selected_candidate.mapping_status
    )
    selected_proposals = (
        ()
        if selected_candidate is None
        else selected_candidate.proposals
    )
    detailed_status = status in {"ambiguous", "conflict"}
    review_required = confidence != "high" or detailed_status
    review_mode = (
        "detailed_review"
        if review_required
        else "quick_confirmation"
    )
    persistence_eligible = selected_candidate is not None
    all_references = tuple(
        reference
        for vote in votes
        for reference in vote.references
    )

    outcome = TerminologyMappingConsensusOutcome(
        occurrence=reference_occurrence,
        mapping_status=status,
        selected_proposals=selected_proposals,
        candidate_references=tuple(
            sorted(all_references, key=_reference_sort_key)
        ),
        value_distribution=tuple(
            TerminologyMappingValueDistribution(
                canonical_value=signature,
                display_value=_mapping_display_value(
                    _representative_candidate(
                        available_votes,
                        signature,
                    )
                ),
                supporting_personas=tuple(
                    vote.persona_id
                    for vote in available_votes
                    if terminology_mapping_signature(
                        vote.candidate
                    )
                    == signature
                ),
                candidate_references=tuple(
                    sorted(
                        (
                            reference
                            for vote in available_votes
                            if terminology_mapping_signature(
                                vote.candidate
                            )
                            == signature
                            for reference in vote.references
                        ),
                        key=_reference_sort_key,
                    )
                ),
            )
            for signature in sorted(distribution)
        ),
        consensus_level=consensus_level,
        variance_level=variance_level,
        confidence=confidence,
        total_personas=total,
        supporting_personas=supporting_personas,
        dissenting_personas=dissenting_personas,
        omitting_personas=omitting_personas,
        confirmation_required=True,
        review_required=review_required,
        recommended_review_mode=review_mode,
        persistence_eligible=persistence_eligible,
        confidence_rationale=_confidence_rationale(
            consensus_level=consensus_level,
            confidence=confidence,
            support=support,
            total=total,
            unstable=unstable,
            status=status,
        ),
    )
    return outcome, issues


def _collapse_persona_runs(
    occurrences: tuple[_CandidateOccurrence, ...],
    *,
    all_results: tuple[TerminologyMappingAgentResult, ...],
    personas: tuple[str, ...],
    expectations: Mapping[str, int],
    project_id: str,
    information_unit_id: str,
) -> tuple[
    tuple[_PersonaVote, ...],
    tuple[TerminologyMappingIssue, ...],
]:
    occurrence_by_run = {
        (
            item.result.persona_id,
            item.result.persona_run_index,
        ): item.candidate
        for item in occurrences
    }
    observed_runs: dict[str, set[int]] = defaultdict(set)
    for result in all_results:
        observed_runs[result.persona_id].add(
            result.persona_run_index
        )

    votes = []
    issues = []
    for persona_id in personas:
        expected_indices = tuple(
            range(1, expectations[persona_id] + 1)
        )
        missing_runs = tuple(
            index
            for index in expected_indices
            if index not in observed_runs[persona_id]
        )
        run_candidates = tuple(
            occurrence_by_run.get((persona_id, index))
            for index in expected_indices
            if index in observed_runs[persona_id]
        )
        candidate_values = tuple(
            value
            for value in run_candidates
            if value is not None
        )
        omitted_indices = tuple(
            index
            for index in expected_indices
            if (
                index in observed_runs[persona_id]
                and occurrence_by_run.get(
                    (persona_id, index)
                )
                is None
            )
        )

        selected: TerminologyMappingAgentCandidate | None
        stability: str
        if missing_runs:
            selected = None
            stability = "incomplete"
        elif not candidate_values:
            selected = None
            stability = "stable"
        else:
            signatures = tuple(
                terminology_mapping_signature(value)
                for value in candidate_values
            )
            counts = Counter(signatures)
            highest = max(counts.values())
            modes = tuple(
                signature
                for signature, count in counts.items()
                if count == highest
            )
            omission_count = len(omitted_indices)
            if omission_count > highest:
                selected = None
                stability = "unstable"
            elif omission_count == highest and omission_count:
                selected = None
                stability = "indeterminate"
            elif len(modes) != 1:
                selected = None
                stability = "indeterminate"
            else:
                selected = next(
                    value
                    for value in candidate_values
                    if terminology_mapping_signature(value)
                    == modes[0]
                )
                stability = (
                    "stable"
                    if len(counts) == 1
                    and not omitted_indices
                    else "unstable"
                )

        references = tuple(
            _candidate_reference(item)
            for item in occurrences
            if item.result.persona_id == persona_id
        )
        votes.append(
            _PersonaVote(
                persona_id=persona_id,
                candidate=selected,
                references=references,
                stability=stability,
                omitted_run_indices=omitted_indices,
            )
        )
        if stability in {"unstable", "indeterminate"}:
            issues.append(
                TerminologyMappingIssue(
                    project_id=project_id,
                    code=(
                        "unstable_persona_mapping"
                        if stability == "unstable"
                        else "indeterminate_persona_mapping"
                    ),
                    message=(
                        f"Persona {persona_id!r} mapping result "
                        f"is {stability} for this occurrence."
                    ),
                    issue_level=(
                        "warning"
                        if stability == "unstable"
                        else "blocking"
                    ),
                    information_unit_id=information_unit_id,
                    persona_id=persona_id,
                )
            )
    return tuple(votes), tuple(issues)


def _signature_distribution(
    votes: tuple[_PersonaVote, ...],
) -> dict[str, int]:
    return dict(
        Counter(
            terminology_mapping_signature(vote.candidate)
            for vote in votes
        )
    )


def _select_unique_mode(
    distribution: Mapping[str, int],
) -> str | None:
    if not distribution:
        return None
    highest = max(distribution.values())
    modes = tuple(
        signature
        for signature, count in distribution.items()
        if count == highest
    )
    return modes[0] if len(modes) == 1 else None


def _representative_candidate(
    votes: tuple[_PersonaVote, ...],
    signature: str,
) -> TerminologyMappingAgentCandidate:
    matches = tuple(
        vote.candidate
        for vote in votes
        if terminology_mapping_signature(vote.candidate)
        == signature
    )
    if not matches:
        raise IncomparableTerminologyMappingClusterError(
            "No representative candidate matches the selected "
            "mapping signature."
        )
    return sorted(
        matches,
        key=lambda candidate: (
            candidate.terminology_mapping_agent_candidate_id,
            candidate.rationale,
        ),
    )[0]


def _candidate_reference(
    occurrence: _CandidateOccurrence,
) -> TerminologyMappingAgentCandidateReference:
    return TerminologyMappingAgentCandidateReference(
        persona_id=occurrence.result.persona_id,
        agent_id=occurrence.result.agent_id,
        persona_run_index=(
            occurrence.result.persona_run_index
        ),
        terminology_mapping_agent_candidate_id=(
            occurrence.candidate
            .terminology_mapping_agent_candidate_id
        ),
    )


def _target_signature_payload(
    target: object,
) -> dict[str, Any] | None:
    if target is None:
        return None
    return {
        "target_kind": target.target_kind,
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


def _mapping_display_value(
    candidate: TerminologyMappingAgentCandidate,
) -> str:
    if not candidate.proposals:
        return candidate.mapping_status
    targets = tuple(
        (
            proposal.mapping_relation
            if proposal.target is None
            else (
                f"{proposal.mapping_relation}:"
                f"{proposal.target.display_label}"
            )
        )
        for proposal in candidate.proposals
    )
    return f"{candidate.mapping_status} [{', '.join(targets)}]"


def _confidence_rationale(
    *,
    consensus_level: str,
    confidence: str,
    support: int,
    total: int,
    unstable: bool,
    status: str,
) -> str:
    details = (
        f"{support} of {total} required personas support the "
        f"selected {status} mapping; consensus is "
        f"{consensus_level}; deterministic confidence is "
        f"{confidence}."
    )
    if unstable:
        details += (
            " Repeated runs reveal intra-persona instability, "
            "which caps confidence."
        )
    if status in {"ambiguous", "conflict"}:
        details += (
            " The mapping status requires detailed human review "
            "regardless of agreement."
        )
    return details


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise TerminologyMappingComparisonError(
            "Mapping value is not canonically serializable."
        ) from exc


def _require_timestamp(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or not value.endswith("Z")
        or "T" not in value
    ):
        raise TerminologyMappingValidationError(
            "timestamp must be a trimmed ISO 8601 UTC value."
        )
    return value


def _reference_sort_key(
    value: TerminologyMappingAgentCandidateReference,
) -> tuple[str, int, str, str]:
    return (
        value.persona_id,
        value.persona_run_index,
        value.agent_id,
        value.terminology_mapping_agent_candidate_id,
    )


def _issue_sort_key(
    value: TerminologyMappingIssue,
) -> tuple[str, str, str, int]:
    return (
        value.code,
        value.persona_id or "",
        value.agent_id or "",
        value.persona_run_index or 0,
    )