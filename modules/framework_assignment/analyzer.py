"""Deterministic multi-persona framework-assignment consensus."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import json
from typing import Any

from modules.information_units.types import InformationUnit

from .agent_manifest import (
    validate_framework_assignment_agent_result,
)
from .errors import (
    DuplicateFrameworkAssignmentAgentResultError,
    FrameworkAssignmentComparisonError,
    FrameworkAssignmentConfigurationError,
    FrameworkAssignmentReferenceError,
    FrameworkAssignmentValidationError,
    IncomparableFrameworkAssignmentClusterError,
)
from .types import (
    FrameworkAssignmentAgentCandidate,
    FrameworkAssignmentAgentCandidateReference,
    FrameworkAssignmentAgentResult,
    FrameworkAssignmentConsensusOutcome,
    FrameworkAssignmentIssue,
    FrameworkAssignmentProposal,
    FrameworkAssignmentValueDistribution,
)


FRAMEWORK_ASSIGNMENT_CONSENSUS_SCHEMA_VERSION = "1.0.0"
FRAMEWORK_ASSIGNMENT_SIGNATURE_ID = (
    "assignment_status_and_framework_node_set"
)
FRAMEWORK_ASSIGNMENT_SIGNATURE_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class FrameworkAssignmentConsensusResult:
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
    framework_template_id: str
    framework_template_version: str
    turing_core_version: str
    project_glossary_revision: int
    terminology_mapping_candidate_ids: tuple[str, ...]
    outcomes: tuple[FrameworkAssignmentConsensusOutcome, ...]
    issues: tuple[FrameworkAssignmentIssue, ...]
    created_at: str


@dataclass(frozen=True, slots=True)
class _PersonaVote:
    """One collapsed persona vote and its repeated-run stability."""

    persona_id: str
    candidate: FrameworkAssignmentAgentCandidate | None
    references: tuple[
        FrameworkAssignmentAgentCandidateReference,
        ...
    ]
    stability: str


def analyze_framework_assignment_consensus(
    *,
    agent_results: Iterable[FrameworkAssignmentAgentResult],
    required_personas: Iterable[str],
    expected_runs_per_persona: Mapping[str, int],
    information_unit: InformationUnit,
    timestamp: str,
) -> FrameworkAssignmentConsensusResult:
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
            information_unit_id=(
                information_unit.information_unit_id
            ),
        )
    )
    votes, vote_issues = _collapse_persona_runs(
        results,
        personas=personas,
        expectations=expectations,
        project_id=information_unit.project_id,
        information_unit_id=(
            information_unit.information_unit_id
        ),
    )
    issues.extend(vote_issues)

    outcome = _analyze_votes(
        votes,
        project_id=information_unit.project_id,
        information_unit_id=(
            information_unit.information_unit_id
        ),
    )
    outcomes = () if outcome is None else (outcome,)
    if outcome is None:
        issues.append(
            FrameworkAssignmentIssue(
                project_id=information_unit.project_id,
                code="no_framework_assignment_candidates",
                message=(
                    "No persona produced a framework-assignment "
                    "candidate."
                ),
                issue_level="warning",
                information_unit_id=(
                    information_unit.information_unit_id
                ),
            )
        )

    first = results[0]
    return FrameworkAssignmentConsensusResult(
        schema_version=(
            FRAMEWORK_ASSIGNMENT_CONSENSUS_SCHEMA_VERSION
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
        framework_template_id=first.framework_template_id,
        framework_template_version=(
            first.framework_template_version
        ),
        turing_core_version=first.turing_core_version,
        project_glossary_revision=(
            first.project_glossary_revision
        ),
        terminology_mapping_candidate_ids=(
            first.terminology_mapping_candidate_ids
        ),
        outcomes=outcomes,
        issues=tuple(sorted(issues, key=_issue_sort_key)),
        created_at=created_at,
    )


def framework_assignment_signature(
    candidate: FrameworkAssignmentAgentCandidate,
) -> str:
    """Return the canonical professional assignment signature."""

    if not isinstance(
        candidate,
        FrameworkAssignmentAgentCandidate,
    ):
        raise FrameworkAssignmentComparisonError(
            "candidate must be a FrameworkAssignmentAgentCandidate."
        )
    return _canonical_json(
        {
            "assignment_status": candidate.assignment_status,
            "framework_node_ids": sorted(
                proposal.framework_node_id
                for proposal in candidate.proposals
            ),
        }
    )


def _require_agent_results(
    values: Iterable[FrameworkAssignmentAgentResult],
) -> tuple[FrameworkAssignmentAgentResult, ...]:
    if isinstance(values, (str, bytes)):
        raise FrameworkAssignmentValidationError(
            "agent_results must be an iterable of results."
        )
    try:
        results = tuple(values)
    except TypeError as exc:
        raise FrameworkAssignmentValidationError(
            "agent_results must be iterable."
        ) from exc
    if not results:
        raise FrameworkAssignmentConfigurationError(
            "At least one framework-assignment agent result is "
            "required."
        )
    for result in results:
        if not isinstance(result, FrameworkAssignmentAgentResult):
            raise FrameworkAssignmentValidationError(
                "agent_results must contain only "
                "FrameworkAssignmentAgentResult values."
            )
        validate_framework_assignment_agent_result(result)
    keys = tuple(
        (
            result.persona_id,
            result.persona_run_index,
        )
        for result in results
    )
    if len(keys) != len(set(keys)):
        raise DuplicateFrameworkAssignmentAgentResultError(
            "Duplicate persona run results are not allowed."
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
        raise FrameworkAssignmentConfigurationError(
            "required_personas must be an iterable of persona IDs."
        )
    try:
        personas = tuple(values)
    except TypeError as exc:
        raise FrameworkAssignmentConfigurationError(
            "required_personas must be iterable."
        ) from exc
    if not personas:
        raise FrameworkAssignmentConfigurationError(
            "At least one required persona is needed."
        )
    if not all(
        isinstance(persona, str)
        and persona
        and persona == persona.strip()
        for persona in personas
    ):
        raise FrameworkAssignmentConfigurationError(
            "required_personas must contain trimmed non-empty IDs."
        )
    if len(personas) != len(set(personas)):
        raise FrameworkAssignmentConfigurationError(
            "required_personas must not contain duplicates."
        )
    return personas


def _require_run_expectations(
    values: Mapping[str, int],
    personas: tuple[str, ...],
) -> dict[str, int]:
    if not isinstance(values, Mapping):
        raise FrameworkAssignmentConfigurationError(
            "expected_runs_per_persona must be a mapping."
        )
    if set(values) != set(personas):
        raise FrameworkAssignmentConfigurationError(
            "expected_runs_per_persona keys must exactly match "
            "required_personas."
        )
    expectations: dict[str, int] = {}
    for persona_id in personas:
        count = values[persona_id]
        if isinstance(count, bool) or not isinstance(count, int):
            raise FrameworkAssignmentConfigurationError(
                "Expected run counts must be integers."
            )
        if count < 1:
            raise FrameworkAssignmentConfigurationError(
                "Expected run counts must be greater than zero."
            )
        expectations[persona_id] = count
    return expectations


def _require_information_unit(value: object) -> InformationUnit:
    if not isinstance(value, InformationUnit):
        raise FrameworkAssignmentValidationError(
            "information_unit must be an InformationUnit."
        )
    return value


def _validate_result_configuration(
    results: tuple[FrameworkAssignmentAgentResult, ...],
    *,
    personas: tuple[str, ...],
    expectations: Mapping[str, int],
    information_unit: InformationUnit,
) -> None:
    first = results[0]
    common_fields = (
        "project_id",
        "source_id",
        "source_projection_id",
        "information_unit_id",
        "team_id",
        "llm_provider",
        "llm_model",
        "prompt_schema_version",
        "framework_template_id",
        "framework_template_version",
        "turing_core_version",
        "project_glossary_revision",
        "terminology_mapping_candidate_ids",
    )
    for result in results:
        mismatches = tuple(
            field_name
            for field_name in common_fields
            if getattr(result, field_name)
            != getattr(first, field_name)
        )
        if mismatches:
            raise FrameworkAssignmentConfigurationError(
                "Agent results have inconsistent configuration: "
                + ", ".join(mismatches)
                + "."
            )
        if result.persona_id not in personas:
            raise FrameworkAssignmentConfigurationError(
                f"Unexpected persona {result.persona_id!r}."
            )
        if (
            result.persona_run_index
            > expectations[result.persona_id]
        ):
            raise FrameworkAssignmentConfigurationError(
                f"Persona {result.persona_id!r} run index "
                f"{result.persona_run_index} exceeds expectation."
            )
    expected_bindings = (
        ("project_id", information_unit.project_id),
        ("source_id", information_unit.source_id),
        (
            "source_projection_id",
            information_unit.source_projection_id,
        ),
        (
            "information_unit_id",
            information_unit.information_unit_id,
        ),
    )
    mismatches = tuple(
        field_name
        for field_name, expected in expected_bindings
        if getattr(first, field_name) != expected
    )
    if mismatches:
        raise FrameworkAssignmentReferenceError(
            "Agent results do not reference the supplied Information "
            "Unit: "
            + ", ".join(mismatches)
            + "."
        )


def _team_issues(
    results: tuple[FrameworkAssignmentAgentResult, ...],
    *,
    personas: tuple[str, ...],
    expectations: Mapping[str, int],
    project_id: str,
    information_unit_id: str,
) -> tuple[FrameworkAssignmentIssue, ...]:
    observed: dict[str, set[int]] = defaultdict(set)
    for result in results:
        observed[result.persona_id].add(
            result.persona_run_index
        )
    issues = []
    for persona_id in personas:
        missing = tuple(
            run_index
            for run_index in range(
                1,
                expectations[persona_id] + 1,
            )
            if run_index not in observed[persona_id]
        )
        if missing:
            issues.append(
                FrameworkAssignmentIssue(
                    project_id=project_id,
                    code="missing_persona_runs",
                    message=(
                        f"Persona {persona_id!r} is missing expected "
                        f"runs {missing!r}."
                    ),
                    issue_level="blocking",
                    information_unit_id=information_unit_id,
                    persona_id=persona_id,
                )
            )
    return tuple(issues)


def _collapse_persona_runs(
    results: tuple[FrameworkAssignmentAgentResult, ...],
    *,
    personas: tuple[str, ...],
    expectations: Mapping[str, int],
    project_id: str,
    information_unit_id: str,
) -> tuple[
    tuple[_PersonaVote, ...],
    tuple[FrameworkAssignmentIssue, ...],
]:
    result_by_run = {
        (result.persona_id, result.persona_run_index): result
        for result in results
    }
    votes = []
    issues = []
    for persona_id in personas:
        expected_indices = tuple(
            range(1, expectations[persona_id] + 1)
        )
        run_results = tuple(
            result_by_run.get((persona_id, run_index))
            for run_index in expected_indices
        )
        if any(result is None for result in run_results):
            votes.append(
                _PersonaVote(
                    persona_id=persona_id,
                    candidate=None,
                    references=(),
                    stability="incomplete",
                )
            )
            continue

        candidates = tuple(
            result.candidates[0]
            if result is not None and result.candidates
            else None
            for result in run_results
        )
        candidate_values = tuple(
            candidate
            for candidate in candidates
            if candidate is not None
        )
        omission_count = sum(
            candidate is None
            for candidate in candidates
        )
        references = tuple(
            FrameworkAssignmentAgentCandidateReference(
                persona_id=result.persona_id,
                agent_id=result.agent_id,
                persona_run_index=result.persona_run_index,
                framework_assignment_agent_candidate_id=(
                    result.candidates[0]
                    .framework_assignment_agent_candidate_id
                ),
            )
            for result in run_results
            if result is not None and result.candidates
        )

        selected: FrameworkAssignmentAgentCandidate | None
        stability: str
        if not candidate_values:
            selected = None
            stability = "stable"
        else:
            counts = Counter(
                framework_assignment_signature(candidate)
                for candidate in candidate_values
            )
            highest = max(counts.values())
            modes = tuple(
                signature
                for signature, count in counts.items()
                if count == highest
            )
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
                    candidate
                    for candidate in candidate_values
                    if framework_assignment_signature(candidate)
                    == modes[0]
                )
                stability = (
                    "stable"
                    if len(counts) == 1
                    and omission_count == 0
                    else "unstable"
                )
        votes.append(
            _PersonaVote(
                persona_id=persona_id,
                candidate=selected,
                references=references,
                stability=stability,
            )
        )
        if stability in {"unstable", "indeterminate"}:
            issues.append(
                FrameworkAssignmentIssue(
                    project_id=project_id,
                    code=(
                        "unstable_persona_assignment"
                        if stability == "unstable"
                        else "indeterminate_persona_assignment"
                    ),
                    message=(
                        f"Persona {persona_id!r} framework assignment "
                        f"is {stability} across repeated runs."
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


def _analyze_votes(
    votes: tuple[_PersonaVote, ...],
    *,
    project_id: str,
    information_unit_id: str,
) -> FrameworkAssignmentConsensusOutcome | None:
    available = tuple(
        vote for vote in votes if vote.candidate is not None
    )
    if not available:
        return None
    distribution = dict(
        Counter(
            framework_assignment_signature(vote.candidate)
            for vote in available
        )
    )
    selected_signature = _select_unique_mode(distribution)
    incomplete = any(
        vote.stability in {"incomplete", "indeterminate"}
        for vote in votes
    )
    unstable = any(
        vote.stability == "unstable"
        for vote in votes
    )
    omitting_personas = tuple(
        vote.persona_id
        for vote in votes
        if vote.candidate is None
    )
    supporting_personas: tuple[str, ...] = ()
    dissenting_personas: tuple[str, ...] = ()
    selected_candidate: FrameworkAssignmentAgentCandidate | None = None
    if selected_signature is not None:
        supporting_personas = tuple(
            vote.persona_id
            for vote in available
            if framework_assignment_signature(vote.candidate)
            == selected_signature
        )
        dissenting_personas = tuple(
            vote.persona_id
            for vote in available
            if framework_assignment_signature(vote.candidate)
            != selected_signature
        )
        selected_candidate = _representative_candidate(
            available,
            selected_signature,
        )

    total = len(votes)
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
        "unassigned"
        if selected_candidate is None
        else selected_candidate.assignment_status
    )
    selected_proposals = (
        ()
        if selected_candidate is None
        else selected_candidate.proposals
    )
    detailed_status = status in {"ambiguous", "conflict"}
    review_required = confidence != "high" or detailed_status
    references = tuple(
        reference
        for vote in votes
        for reference in vote.references
    )
    return FrameworkAssignmentConsensusOutcome(
        information_unit_id=information_unit_id,
        assignment_status=status,
        selected_proposals=selected_proposals,
        candidate_references=tuple(
            sorted(references, key=_reference_sort_key)
        ),
        value_distribution=tuple(
            FrameworkAssignmentValueDistribution(
                canonical_value=signature,
                display_value=_display_value(
                    _representative_candidate(
                        available,
                        signature,
                    )
                ),
                supporting_personas=tuple(
                    vote.persona_id
                    for vote in available
                    if framework_assignment_signature(
                        vote.candidate
                    )
                    == signature
                ),
                candidate_references=tuple(
                    sorted(
                        (
                            reference
                            for vote in available
                            if framework_assignment_signature(
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
        recommended_review_mode=(
            "detailed_review"
            if review_required
            else "quick_confirmation"
        ),
        persistence_eligible=selected_candidate is not None,
        confidence_rationale=_confidence_rationale(
            consensus_level=consensus_level,
            confidence=confidence,
            support=support,
            total=total,
            unstable=unstable,
            status=status,
        ),
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
) -> FrameworkAssignmentAgentCandidate:
    matches = tuple(
        vote.candidate
        for vote in votes
        if framework_assignment_signature(vote.candidate)
        == signature
    )
    if not matches:
        raise IncomparableFrameworkAssignmentClusterError(
            "No representative candidate matches the selected "
            "assignment signature."
        )
    return sorted(
        matches,
        key=lambda candidate: (
            candidate.framework_assignment_agent_candidate_id,
            candidate.rationale,
        ),
    )[0]


def _display_value(
    candidate: FrameworkAssignmentAgentCandidate,
) -> str:
    node_ids = sorted(
        proposal.framework_node_id
        for proposal in candidate.proposals
    )
    if not node_ids:
        return candidate.assignment_status
    return (
        f"{candidate.assignment_status} "
        f"[{', '.join(node_ids)}]"
    )


def _confidence_rationale(
    *,
    consensus_level: str,
    confidence: str,
    support: int,
    total: int,
    unstable: bool,
    status: str,
) -> str:
    rationale = (
        f"{support} of {total} required personas support the "
        f"selected {status} framework assignment; consensus is "
        f"{consensus_level}; deterministic confidence is "
        f"{confidence}."
    )
    if unstable:
        rationale += (
            " Repeated runs reveal intra-persona instability, "
            "which caps confidence."
        )
    if status in {"ambiguous", "conflict"}:
        rationale += (
            " The assignment status requires detailed human review "
            "regardless of agreement."
        )
    return rationale


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise FrameworkAssignmentComparisonError(
            "Assignment value is not canonically serializable."
        ) from exc


def _require_timestamp(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or not value.endswith("Z")
        or "T" not in value
    ):
        raise FrameworkAssignmentValidationError(
            "timestamp must be a trimmed ISO 8601 UTC value."
        )
    return value


def _reference_sort_key(
    value: FrameworkAssignmentAgentCandidateReference,
) -> tuple[str, int, str, str]:
    return (
        value.persona_id,
        value.persona_run_index,
        value.agent_id,
        value.framework_assignment_agent_candidate_id,
    )


def _issue_sort_key(
    value: FrameworkAssignmentIssue,
) -> tuple[str, str, str, str]:
    return (
        value.issue_level,
        value.code,
        value.persona_id or "",
        value.message,
    )