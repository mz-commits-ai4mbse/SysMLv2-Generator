"""Deterministic consensus analysis for semantic persona results.

The analyzer performs no LLM call and no semantic-similarity inference.
Distinct personas receive at most one vote per source-evidence cluster.
Repeated runs measure intra-persona stability only.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from modules.information_units.types import (
    InformationUnit,
)
from modules.semantic_extraction.manifest import (
    validate_semantic_extraction_agent_result,
    validate_semantic_extraction_agent_result_context,
)
from modules.semantic_extraction.types import (
    InformationUnitCandidate,
    SemanticExtractionAgentResult,
)
from modules.source_projection.identifiers import (
    segment_id_sequence,
)
from modules.source_projection.types import (
    SourceProjectionArtifact,
)

from .errors import (
    DuplicateSemanticAgentResultError,
    SemanticConsensusConfigurationError,
    SemanticConsensusReferenceError,
    SemanticConsensusValidationError,
)
from .identifiers import (
    format_semantic_consensus_candidate_id,
)
from .manifest import (
    SEMANTIC_CONSENSUS_SCHEMA_VERSION,
    validate_semantic_consensus_result,
)
from .normalization import (
    canonical_consensus_json,
    normalize_consensus_text,
)
from .types import (
    AgentCandidateReference,
    ConsensusInformationUnitDraft,
    ConsensusValueDistribution,
    FieldConsensusAssessment,
    PersonaRunExpectation,
    PersonaStabilityAssessment,
    SemanticConsensusIssue,
    SemanticConsensusOutcome,
    SemanticConsensusResult,
)

_FIELD_ORDER = (
    "existence",
    "interpreted_statement",
    "information_type",
    "statement_modality",
    "epistemic_class",
    "semantic_evidence",
)

_STATE_CANDIDATE = "candidate"
_STATE_OMISSION = "omission"
_STATE_INDETERMINATE = "indeterminate"
_STATE_INCOMPLETE = "incomplete"

EvidenceKey = tuple[
    tuple[tuple[int, int, int], ...],
    str,
]


@dataclass(frozen=True, slots=True)
class _CandidateOccurrence:
    """One candidate with its exact run reference."""

    result: SemanticExtractionAgentResult
    candidate: InformationUnitCandidate
    reference: AgentCandidateReference
    professional_signature: str


@dataclass(frozen=True, slots=True)
class _PersonaVote:
    """One collapsed persona vote for one evidence cluster."""

    persona_id: str
    state: str
    selected_candidate: InformationUnitCandidate | None
    selected_signature: str | None
    selected_references: tuple[AgentCandidateReference, ...]
    assessment: PersonaStabilityAssessment
    has_uncertainty: bool


def analyze_semantic_consensus(
    *,
    agent_results: Iterable[
        SemanticExtractionAgentResult
    ],
    required_personas: Iterable[str],
    expected_runs_per_persona: Mapping[str, int],
    source_projection: SourceProjectionArtifact,
    supporting_information_units: Iterable[
        InformationUnit
    ] = (),
    consensus_report_id: str,
    timestamp: str,
) -> SemanticConsensusResult:
    """Analyze one configured semantic team deterministically."""

    results = _require_agent_results(agent_results)
    personas = _require_required_personas(required_personas)
    expectations = _require_run_expectations(
        personas,
        expected_runs_per_persona,
    )
    supporting_units = _require_supporting_units(
        supporting_information_units
    )
    _validate_result_configuration(
        results,
        personas=personas,
        expectations=expectations,
        source_projection=source_projection,
        supporting_information_units=supporting_units,
    )

    reference_result = results[0]
    result_by_persona_and_run = {
        (
            result.persona_id,
            result.persona_run_index,
        ): result
        for result in results
    }
    issues = list(
        _team_issues(
            result_by_persona_and_run,
            expectations,
        )
    )
    evidence_buckets = _collect_evidence_buckets(results)
    outcomes: list[SemanticConsensusOutcome] = []

    for outcome_index, evidence_key in enumerate(
        sorted(
            evidence_buckets,
            key=_evidence_sort_key,
        ),
        start=1,
    ):
        occurrences = evidence_buckets[evidence_key]
        outcome, outcome_issues = _analyze_evidence_bucket(
            consensus_candidate_id=(
                format_semantic_consensus_candidate_id(
                    outcome_index
                )
            ),
            evidence_key=evidence_key,
            occurrences=occurrences,
            personas=personas,
            expectations=expectations,
            result_by_persona_and_run=(
                result_by_persona_and_run
            ),
        )
        outcomes.append(outcome)
        issues.extend(outcome_issues)

    if not outcomes:
        rationales = sorted(
            {
                result.no_candidate_rationale
                for result in results
                if result.no_candidate_rationale is not None
            }
        )
        suffix = (
            " Reported rationales: "
            + " | ".join(rationales)
            if rationales
            else ""
        )
        issues.append(
            SemanticConsensusIssue(
                code="no_consensus_candidates",
                message=(
                    "No persona run produced an Information "
                    f"Unit Candidate.{suffix}"
                ),
                issue_level="warning",
            )
        )

    result = SemanticConsensusResult(
        schema_version=SEMANTIC_CONSENSUS_SCHEMA_VERSION,
        project_id=reference_result.project_id,
        source_id=reference_result.source_id,
        source_projection_id=(
            reference_result.source_projection_id
        ),
        team_id=reference_result.team_id,
        consensus_report_id=consensus_report_id,
        required_personas=personas,
        persona_run_expectations=tuple(
            PersonaRunExpectation(
                persona_id=persona_id,
                expected_run_count=expectations[persona_id],
            )
            for persona_id in personas
        ),
        llm_provider=reference_result.llm_provider,
        llm_model=reference_result.llm_model,
        prompt_schema_version=(
            reference_result.prompt_schema_version
        ),
        outcomes=tuple(outcomes),
        issues=tuple(
            sorted(
                issues,
                key=_issue_sort_key,
            )
        ),
        created_at=timestamp,
    )
    validate_semantic_consensus_result(result)
    return result


def candidate_evidence_key(
    candidate: InformationUnitCandidate,
) -> EvidenceKey:
    """Return exact source evidence used for candidate clustering."""

    if not isinstance(candidate, InformationUnitCandidate):
        raise SemanticConsensusValidationError(
            "candidate must be an InformationUnitCandidate "
            "instance."
        )

    return (
        tuple(
            (
                segment_id_sequence(anchor.segment_id),
                anchor.start_offset,
                anchor.end_offset,
            )
            for anchor in candidate.source_anchors
        ),
        candidate.source_excerpt,
    )


def candidate_professional_signature(
    candidate: InformationUnitCandidate,
) -> str:
    """Return the exact deterministic comparison signature."""

    if not isinstance(candidate, InformationUnitCandidate):
        raise SemanticConsensusValidationError(
            "candidate must be an InformationUnitCandidate "
            "instance."
        )

    return canonical_consensus_json(
        {
            "interpreted_statement": normalize_consensus_text(
                candidate.interpreted_statement
            ),
            "information_type": candidate.information_type,
            "statement_modality": (
                candidate.statement_modality
            ),
            "epistemic_class": candidate.epistemic_class,
            "semantic_evidence": _semantic_evidence_value(
                candidate
            ),
        }
    )


def _require_agent_results(
    values: Iterable[SemanticExtractionAgentResult],
) -> tuple[SemanticExtractionAgentResult, ...]:
    if isinstance(values, (str, bytes)):
        raise SemanticConsensusConfigurationError(
            "agent_results must be an iterable of "
            "SemanticExtractionAgentResult instances."
        )

    try:
        results = tuple(values)
    except TypeError as exc:
        raise SemanticConsensusConfigurationError(
            "agent_results must be iterable."
        ) from exc

    if not results:
        raise SemanticConsensusConfigurationError(
            "agent_results must contain at least one result."
        )

    for result in results:
        if not isinstance(
            result,
            SemanticExtractionAgentResult,
        ):
            raise SemanticConsensusConfigurationError(
                "agent_results must contain "
                "SemanticExtractionAgentResult instances."
            )

        validate_semantic_extraction_agent_result(result)

    ordered = tuple(
        sorted(
            results,
            key=lambda result: (
                result.persona_id,
                result.persona_run_index,
                result.agent_id,
            ),
        )
    )
    run_keys = tuple(
        (
            result.persona_id,
            result.persona_run_index,
        )
        for result in ordered
    )

    if len(run_keys) != len(set(run_keys)):
        raise DuplicateSemanticAgentResultError(
            "A semantic team may contain only one result per "
            "persona_id and persona_run_index."
        )

    return ordered


def _require_required_personas(
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise SemanticConsensusConfigurationError(
            "required_personas must be an iterable of "
            "persona IDs."
        )

    try:
        personas = tuple(values)
    except TypeError as exc:
        raise SemanticConsensusConfigurationError(
            "required_personas must be iterable."
        ) from exc

    if len(personas) < 2:
        raise SemanticConsensusConfigurationError(
            "Semantic consensus requires at least two "
            "distinct personas."
        )

    for persona_id in personas:
        if (
            not isinstance(persona_id, str)
            or not persona_id.strip()
            or persona_id != persona_id.strip()
        ):
            raise SemanticConsensusConfigurationError(
                "required_personas must contain non-empty "
                "trimmed strings."
            )

    if len(personas) != len(set(personas)):
        raise SemanticConsensusConfigurationError(
            "required_personas must not contain duplicates."
        )

    return tuple(sorted(personas))


def _require_run_expectations(
    personas: tuple[str, ...],
    values: Mapping[str, int],
) -> dict[str, int]:
    if not isinstance(values, Mapping):
        raise SemanticConsensusConfigurationError(
            "expected_runs_per_persona must be a mapping."
        )

    if set(values) != set(personas):
        raise SemanticConsensusConfigurationError(
            "expected_runs_per_persona keys must equal the "
            "required persona IDs."
        )

    expectations: dict[str, int] = {}

    for persona_id in personas:
        count = values[persona_id]

        if (
            not isinstance(count, int)
            or isinstance(count, bool)
            or count < 1
        ):
            raise SemanticConsensusConfigurationError(
                "Expected persona run counts must be positive "
                "integers."
            )

        expectations[persona_id] = count

    return expectations


def _require_supporting_units(
    values: Iterable[InformationUnit],
) -> tuple[InformationUnit, ...]:
    if isinstance(values, (str, bytes)):
        raise SemanticConsensusReferenceError(
            "supporting_information_units must be an iterable "
            "of InformationUnit instances."
        )

    try:
        units = tuple(values)
    except TypeError as exc:
        raise SemanticConsensusReferenceError(
            "supporting_information_units must be iterable."
        ) from exc

    return units


def _validate_result_configuration(
    results: tuple[SemanticExtractionAgentResult, ...],
    *,
    personas: tuple[str, ...],
    expectations: dict[str, int],
    source_projection: SourceProjectionArtifact,
    supporting_information_units: tuple[
        InformationUnit,
        ...
    ],
) -> None:
    reference = results[0]
    comparable_fields = (
        "project_id",
        "source_id",
        "source_projection_id",
        "team_id",
        "llm_provider",
        "llm_model",
        "prompt_schema_version",
    )
    agent_by_persona: dict[str, str] = {}
    fingerprint_by_persona: dict[str, str] = {}

    for result in results:
        if result.persona_id not in personas:
            raise SemanticConsensusConfigurationError(
                "Agent result belongs to a persona that is "
                f"not required: {result.persona_id!r}."
            )

        for field_name in comparable_fields:
            if getattr(result, field_name) != getattr(
                reference,
                field_name,
            ):
                raise SemanticConsensusConfigurationError(
                    "Semantic agent results disagree on "
                    f"{field_name}."
                )

        expected_count = expectations[result.persona_id]

        if result.persona_run_index > expected_count:
            raise SemanticConsensusConfigurationError(
                "persona_run_index exceeds the configured run "
                f"count for {result.persona_id!r}."
            )

        existing_agent = agent_by_persona.setdefault(
            result.persona_id,
            result.agent_id,
        )

        if existing_agent != result.agent_id:
            raise SemanticConsensusConfigurationError(
                "agent_id must remain stable across repeated "
                f"runs of persona {result.persona_id!r}."
            )

        existing_fingerprint = (
            fingerprint_by_persona.setdefault(
                result.persona_id,
                result.persona_configuration_fingerprint,
            )
        )

        if (
            existing_fingerprint
            != result.persona_configuration_fingerprint
        ):
            raise SemanticConsensusConfigurationError(
                "persona_configuration_fingerprint must remain "
                "stable across repeated runs of persona "
                f"{result.persona_id!r}."
            )

        try:
            validate_semantic_extraction_agent_result_context(
                result,
                source_projection=source_projection,
                supporting_information_units=(
                    supporting_information_units
                ),
            )
        except Exception as exc:
            raise SemanticConsensusReferenceError(
                "Semantic agent result failed source-context "
                f"validation for {result.persona_id!r} run "
                f"{result.persona_run_index}: {exc}"
            ) from exc


def _team_issues(
    result_by_persona_and_run: dict[
        tuple[str, int],
        SemanticExtractionAgentResult,
    ],
    expectations: dict[str, int],
) -> tuple[SemanticConsensusIssue, ...]:
    issues: list[SemanticConsensusIssue] = []

    for persona_id in sorted(expectations):
        for run_index in range(
            1,
            expectations[persona_id] + 1,
        ):
            if (
                persona_id,
                run_index,
            ) not in result_by_persona_and_run:
                issues.append(
                    SemanticConsensusIssue(
                        code="missing_persona_run",
                        message=(
                            "Required semantic persona run is "
                            f"missing: {persona_id} run "
                            f"{run_index}."
                        ),
                        issue_level="blocking",
                        persona_id=persona_id,
                        persona_run_index=run_index,
                    )
                )

    return tuple(issues)


def _collect_evidence_buckets(
    results: tuple[SemanticExtractionAgentResult, ...],
) -> dict[EvidenceKey, tuple[_CandidateOccurrence, ...]]:
    buckets: dict[
        EvidenceKey,
        list[_CandidateOccurrence],
    ] = defaultdict(list)

    for result in results:
        for candidate in result.candidates:
            reference = AgentCandidateReference(
                persona_id=result.persona_id,
                agent_id=result.agent_id,
                persona_run_index=result.persona_run_index,
                candidate_id=candidate.candidate_id,
            )
            buckets[candidate_evidence_key(candidate)].append(
                _CandidateOccurrence(
                    result=result,
                    candidate=candidate,
                    reference=reference,
                    professional_signature=(
                        candidate_professional_signature(
                            candidate
                        )
                    ),
                )
            )

    return {
        key: tuple(
            sorted(
                occurrences,
                key=lambda occurrence: (
                    occurrence.reference.persona_id,
                    occurrence.reference.persona_run_index,
                    occurrence.reference.agent_id,
                    occurrence.reference.candidate_id,
                ),
            )
        )
        for key, occurrences in buckets.items()
    }


def _analyze_evidence_bucket(
    *,
    consensus_candidate_id: str,
    evidence_key: EvidenceKey,
    occurrences: tuple[_CandidateOccurrence, ...],
    personas: tuple[str, ...],
    expectations: dict[str, int],
    result_by_persona_and_run: dict[
        tuple[str, int],
        SemanticExtractionAgentResult,
    ],
) -> tuple[
    SemanticConsensusOutcome,
    tuple[SemanticConsensusIssue, ...],
]:
    occurrences_by_run: dict[
        tuple[str, int],
        list[_CandidateOccurrence],
    ] = defaultdict(list)

    for occurrence in occurrences:
        occurrences_by_run[
            (
                occurrence.reference.persona_id,
                occurrence.reference.persona_run_index,
            )
        ].append(occurrence)

    votes: list[_PersonaVote] = []
    issues: list[SemanticConsensusIssue] = []

    for persona_id in personas:
        vote, vote_issues = _collapse_persona_runs(
            persona_id=persona_id,
            expected_run_count=expectations[persona_id],
            result_by_persona_and_run=(
                result_by_persona_and_run
            ),
            occurrences_by_run=occurrences_by_run,
        )
        votes.append(vote)
        issues.extend(vote_issues)

    total_personas = len(personas)
    full_signature_distribution = _signature_distribution(
        votes
    )
    selected_signature, selected_count = _select_unique_mode(
        full_signature_distribution
    )
    supporting_personas = tuple(
        vote.persona_id
        for vote in votes
        if (
            vote.state == _STATE_CANDIDATE
            and vote.selected_signature == selected_signature
            and selected_signature is not None
        )
    )
    omitting_personas = tuple(
        vote.persona_id
        for vote in votes
        if vote.state == _STATE_OMISSION
    )
    dissenting_personas = tuple(
        vote.persona_id
        for vote in votes
        if (
            vote.persona_id not in supporting_personas
            and vote.persona_id not in omitting_personas
        )
    )
    has_incomplete = any(
        vote.state == _STATE_INCOMPLETE
        for vote in votes
    )
    has_indeterminate = any(
        vote.state == _STATE_INDETERMINATE
        for vote in votes
    )
    has_instability = any(
        vote.assessment.stability_level == "unstable"
        for vote in votes
    )
    has_uncertainty = any(
        vote.has_uncertainty
        for vote in votes
    )
    strict_majority = (
        selected_signature is not None
        and selected_count > total_personas / 2
    )
    unanimous = (
        selected_signature is not None
        and selected_count == total_personas
    )

    if has_incomplete:
        consensus_level = "incomplete"
    elif has_indeterminate:
        consensus_level = "incomparable"
    elif unanimous:
        consensus_level = "unanimous"
    elif strict_majority:
        consensus_level = "majority"
    elif (
        selected_signature is None
        and full_signature_distribution
    ):
        consensus_level = "incomparable"
    elif selected_count == 1:
        consensus_level = "single"
    elif selected_count == 0:
        consensus_level = "none"
    else:
        consensus_level = "incomparable"

    representative = _representative_candidate(
        votes,
        selected_signature,
    )
    field_assessments = tuple(
        _assess_field(
            field_name,
            votes=votes,
            total_personas=total_personas,
            has_incomplete=has_incomplete,
            has_indeterminate=has_indeterminate,
            has_instability=has_instability,
            has_uncertainty=has_uncertainty,
        )
        for field_name in _FIELD_ORDER
    )

    if has_incomplete or has_indeterminate:
        confidence = "low"
    elif unanimous and not (
        has_instability or has_uncertainty
    ):
        confidence = "high"
    elif strict_majority:
        confidence = "medium"
    else:
        confidence = "low"

    if confidence == "high":
        variance_level = "low"
    elif confidence == "medium":
        variance_level = "medium"
    else:
        variance_level = "high"

    proposed_information_unit = (
        _information_unit_draft(representative)
        if strict_majority and representative is not None
        else None
    )
    is_assumption = (
        proposed_information_unit is not None
        and proposed_information_unit.epistemic_class
        == "assumption"
    )
    review_required = (
        confidence != "high"
        or has_instability
        or has_uncertainty
        or is_assumption
    )
    recommended_review_mode = (
        "quick_confirmation"
        if not review_required
        else "detailed_review"
    )
    publication_eligible = (
        proposed_information_unit is not None
        and confidence == "high"
        and not review_required
    )
    confidence_rationale = _confidence_rationale(
        total_personas=total_personas,
        supporting_count=len(supporting_personas),
        dissenting_count=len(dissenting_personas),
        omitting_count=len(omitting_personas),
        has_incomplete=has_incomplete,
        has_indeterminate=has_indeterminate,
        has_instability=has_instability,
        has_uncertainty=has_uncertainty,
        is_assumption=is_assumption,
        confidence=confidence,
    )

    if has_uncertainty:
        issues.append(
            SemanticConsensusIssue(
                code="explicit_agent_uncertainty",
                message=(
                    "At least one supporting persona run "
                    "reported explicit uncertainty for "
                    f"{consensus_candidate_id}."
                ),
                issue_level="warning",
            )
        )

    anchor_coordinates, source_excerpt = evidence_key
    anchor_by_coordinates = {
        (
            segment_id_sequence(anchor.segment_id),
            anchor.start_offset,
            anchor.end_offset,
        ): anchor
        for occurrence in occurrences
        for anchor in occurrence.candidate.source_anchors
    }
    source_anchors = tuple(
        anchor_by_coordinates[coordinates]
        for coordinates in anchor_coordinates
    )

    outcome = SemanticConsensusOutcome(
        consensus_candidate_id=consensus_candidate_id,
        source_anchors=source_anchors,
        source_excerpt=source_excerpt,
        candidate_references=tuple(
            occurrence.reference
            for occurrence in occurrences
        ),
        persona_stability=tuple(
            vote.assessment
            for vote in votes
        ),
        field_assessments=field_assessments,
        proposed_information_unit=(
            proposed_information_unit
        ),
        consensus_level=consensus_level,
        variance_level=variance_level,
        confidence=confidence,
        total_personas=total_personas,
        supporting_personas=supporting_personas,
        dissenting_personas=dissenting_personas,
        omitting_personas=omitting_personas,
        confirmation_required=True,
        review_required=review_required,
        recommended_review_mode=recommended_review_mode,
        publication_eligible=publication_eligible,
        confidence_rationale=confidence_rationale,
    )
    return outcome, tuple(issues)


def _collapse_persona_runs(
    *,
    persona_id: str,
    expected_run_count: int,
    result_by_persona_and_run: dict[
        tuple[str, int],
        SemanticExtractionAgentResult,
    ],
    occurrences_by_run: dict[
        tuple[str, int],
        list[_CandidateOccurrence],
    ],
) -> tuple[_PersonaVote, tuple[SemanticConsensusIssue, ...]]:
    observed_indices: list[int] = []
    omitted_indices: list[int] = []
    missing_indices: list[int] = []
    all_references: list[AgentCandidateReference] = []
    state_by_run: dict[
        int,
        tuple[str | None, _CandidateOccurrence | None],
    ] = {}
    issues: list[SemanticConsensusIssue] = []

    for run_index in range(1, expected_run_count + 1):
        result = result_by_persona_and_run.get(
            (persona_id, run_index)
        )

        if result is None:
            missing_indices.append(run_index)
            continue

        observed_indices.append(run_index)
        run_occurrences = occurrences_by_run.get(
            (persona_id, run_index),
            [],
        )
        all_references.extend(
            occurrence.reference
            for occurrence in run_occurrences
        )

        if not run_occurrences:
            omitted_indices.append(run_index)
            state_by_run[run_index] = (None, None)
            continue

        if len(run_occurrences) > 1:
            state_by_run[run_index] = (
                "__ambiguous__",
                None,
            )
            issues.append(
                SemanticConsensusIssue(
                    code="ambiguous_persona_evidence_bucket",
                    message=(
                        "One persona run produced multiple "
                        "candidates for the same exact source "
                        "evidence."
                    ),
                    issue_level="blocking",
                    persona_id=persona_id,
                    agent_id=result.agent_id,
                    persona_run_index=run_index,
                )
            )
            continue

        occurrence = run_occurrences[0]
        state_by_run[run_index] = (
            occurrence.professional_signature,
            occurrence,
        )

    base_assessment = {
        "persona_id": persona_id,
        "expected_run_count": expected_run_count,
        "observed_run_indices": tuple(observed_indices),
        "omitted_run_indices": tuple(omitted_indices),
        "candidate_references": tuple(
            sorted(
                all_references,
                key=_reference_sort_key,
            )
        ),
    }

    if missing_indices:
        assessment = PersonaStabilityAssessment(
            **base_assessment,
            stability_level="incomplete",
            rationale=(
                "Required run indices are missing: "
                + ", ".join(
                    str(index)
                    for index in missing_indices
                )
                + "."
            ),
        )
        return (
            _PersonaVote(
                persona_id=persona_id,
                state=_STATE_INCOMPLETE,
                selected_candidate=None,
                selected_signature=None,
                selected_references=(),
                assessment=assessment,
                has_uncertainty=False,
            ),
            tuple(issues),
        )

    if any(
        signature == "__ambiguous__"
        for signature, _ in state_by_run.values()
    ):
        assessment = PersonaStabilityAssessment(
            **base_assessment,
            stability_level="indeterminate",
            rationale=(
                "At least one run contains multiple candidates "
                "for the same exact source evidence."
            ),
        )
        return (
            _PersonaVote(
                persona_id=persona_id,
                state=_STATE_INDETERMINATE,
                selected_candidate=None,
                selected_signature=None,
                selected_references=(),
                assessment=assessment,
                has_uncertainty=False,
            ),
            tuple(issues),
        )

    signatures = tuple(
        signature
        for _, (
            signature,
            _,
        ) in sorted(state_by_run.items())
    )
    counts = Counter(signatures)
    selected_signature, selected_count = _select_unique_mode(
        counts
    )

    if selected_signature is None and len(counts) > 1:
        assessment = PersonaStabilityAssessment(
            **base_assessment,
            stability_level="indeterminate",
            rationale=(
                "Repeated runs have no unique modal outcome."
            ),
        )
        issues.append(
            SemanticConsensusIssue(
                code="indeterminate_persona_stability",
                message=(
                    "Repeated runs have no unique modal "
                    "candidate or omission."
                ),
                issue_level="blocking",
                persona_id=persona_id,
            )
        )
        return (
            _PersonaVote(
                persona_id=persona_id,
                state=_STATE_INDETERMINATE,
                selected_candidate=None,
                selected_signature=None,
                selected_references=(),
                assessment=assessment,
                has_uncertainty=False,
            ),
            tuple(issues),
        )

    stability_level = (
        "not_measured"
        if expected_run_count == 1
        else (
            "stable"
            if selected_count == expected_run_count
            else "unstable"
        )
    )

    if stability_level == "unstable":
        issues.append(
            SemanticConsensusIssue(
                code="unstable_persona_result",
                message=(
                    "Repeated runs produced different outcomes; "
                    "the unique modal outcome supplies only one "
                    "unstable persona vote."
                ),
                issue_level="warning",
                persona_id=persona_id,
            )
        )

    if selected_signature is None:
        assessment = PersonaStabilityAssessment(
            **base_assessment,
            stability_level=stability_level,
            rationale=(
                "The persona omitted this evidence cluster in "
                f"{selected_count} of {expected_run_count} runs."
            ),
        )
        return (
            _PersonaVote(
                persona_id=persona_id,
                state=_STATE_OMISSION,
                selected_candidate=None,
                selected_signature=None,
                selected_references=(),
                assessment=assessment,
                has_uncertainty=False,
            ),
            tuple(issues),
        )

    selected_occurrences = tuple(
        occurrence
        for signature, occurrence in state_by_run.values()
        if (
            signature == selected_signature
            and occurrence is not None
        )
    )
    representative = min(
        selected_occurrences,
        key=lambda occurrence: _reference_sort_key(
            occurrence.reference
        ),
    )
    assessment = PersonaStabilityAssessment(
        **base_assessment,
        stability_level=stability_level,
        rationale=(
            "The selected candidate signature occurred in "
            f"{selected_count} of {expected_run_count} runs."
        ),
    )
    return (
        _PersonaVote(
            persona_id=persona_id,
            state=_STATE_CANDIDATE,
            selected_candidate=representative.candidate,
            selected_signature=selected_signature,
            selected_references=tuple(
                occurrence.reference
                for occurrence in selected_occurrences
            ),
            assessment=assessment,
            has_uncertainty=any(
                occurrence.candidate.uncertainties
                for occurrence in selected_occurrences
            ),
        ),
        tuple(issues),
    )


def _signature_distribution(
    votes: list[_PersonaVote],
) -> Counter[str]:
    return Counter(
        vote.selected_signature
        for vote in votes
        if (
            vote.state == _STATE_CANDIDATE
            and vote.selected_signature is not None
        )
    )


def _select_unique_mode(
    counts: Mapping[Any, int],
) -> tuple[Any | None, int]:
    if not counts:
        return None, 0

    highest_count = max(counts.values())
    winners = sorted(
        (
            value
            for value, count in counts.items()
            if count == highest_count
        ),
        key=lambda value: (
            value is not None,
            "" if value is None else str(value),
        ),
    )

    if len(winners) != 1:
        return None, highest_count

    return winners[0], highest_count


def _representative_candidate(
    votes: list[_PersonaVote],
    selected_signature: str | None,
) -> InformationUnitCandidate | None:
    matching = [
        vote
        for vote in votes
        if (
            vote.state == _STATE_CANDIDATE
            and vote.selected_signature == selected_signature
            and vote.selected_candidate is not None
        )
    ]

    if not matching:
        return None

    selected_vote = min(
        matching,
        key=lambda vote: (
            vote.persona_id,
            _reference_sort_key(
                vote.selected_references[0]
            ),
        ),
    )
    return selected_vote.selected_candidate


def _assess_field(
    field_name: str,
    *,
    votes: list[_PersonaVote],
    total_personas: int,
    has_incomplete: bool,
    has_indeterminate: bool,
    has_instability: bool,
    has_uncertainty: bool,
) -> FieldConsensusAssessment:
    value_by_persona: dict[
        str,
        tuple[str, str, tuple[AgentCandidateReference, ...]],
    ] = {}
    omitting_personas = (
        ()
        if field_name == "existence"
        else tuple(
            vote.persona_id
            for vote in votes
            if vote.state == _STATE_OMISSION
        )
    )

    if field_name == "existence":
        for vote in votes:
            if vote.state == _STATE_CANDIDATE:
                value_by_persona[vote.persona_id] = (
                    "true",
                    "true",
                    vote.selected_references,
                )
            elif vote.state == _STATE_OMISSION:
                value_by_persona[vote.persona_id] = (
                    "false",
                    "false",
                    (),
                )
    else:
        for vote in votes:
            candidate = vote.selected_candidate

            if (
                vote.state != _STATE_CANDIDATE
                or candidate is None
            ):
                continue

            canonical, display = _candidate_field_value(
                candidate,
                field_name,
            )
            value_by_persona[vote.persona_id] = (
                canonical,
                display,
                vote.selected_references,
            )

    distribution_map: dict[
        str,
        dict[str, Any],
    ] = {}

    for persona_id, (
        canonical,
        display,
        references,
    ) in value_by_persona.items():
        bucket = distribution_map.setdefault(
            canonical,
            {
                "display": display,
                "personas": [],
                "references": [],
            },
        )
        bucket["personas"].append(persona_id)
        bucket["references"].extend(references)

    distributions = tuple(
        ConsensusValueDistribution(
            canonical_value=canonical,
            display_value=distribution_map[canonical][
                "display"
            ],
            supporting_personas=tuple(
                sorted(
                    distribution_map[canonical]["personas"]
                )
            ),
            candidate_references=tuple(
                sorted(
                    distribution_map[canonical]["references"],
                    key=_reference_sort_key,
                )
            ),
        )
        for canonical in sorted(distribution_map)
    )
    counts = {
        distribution.canonical_value: len(
            distribution.supporting_personas
        )
        for distribution in distributions
    }
    selected_value, selected_count = _select_unique_mode(
        counts
    )
    supporting_personas = tuple(
        sorted(
            (
                distribution.supporting_personas
                for distribution in distributions
                if (
                    distribution.canonical_value
                    == selected_value
                )
            ),
            key=lambda values: values,
        )[0]
        if selected_value is not None
        else ()
    )
    dissenting_personas = tuple(
        sorted(
            set(vote.persona_id for vote in votes)
            - set(supporting_personas)
            - set(omitting_personas)
        )
    )

    if has_incomplete:
        consensus_level = "incomplete"
    elif has_indeterminate:
        consensus_level = "incomparable"
    elif selected_count == total_personas:
        consensus_level = "unanimous"
    elif selected_count > total_personas / 2:
        consensus_level = "majority"
    elif selected_value is None and counts:
        consensus_level = "incomparable"
    elif selected_count == 1:
        consensus_level = "single"
    elif selected_count == 0:
        consensus_level = "none"
    else:
        consensus_level = "incomparable"

    if (
        consensus_level == "unanimous"
        and not has_instability
        and not has_uncertainty
    ):
        confidence = "high"
        variance_level = "low"
    elif consensus_level in {"unanimous", "majority"}:
        confidence = "medium"
        variance_level = "medium"
    else:
        confidence = "low"
        variance_level = "high"

    review_required = (
        confidence != "high"
        or has_instability
        or has_uncertainty
    )
    rationale = (
        f"{field_name}: {selected_count} of "
        f"{total_personas} required personas support the "
        f"selected canonical value; "
        f"{len(dissenting_personas)} dissent and "
        f"{len(omitting_personas)} omit it."
    )

    return FieldConsensusAssessment(
        field_name=field_name,
        selected_value=(
            str(selected_value)
            if selected_value is not None
            else None
        ),
        consensus_level=consensus_level,
        variance_level=variance_level,
        confidence=confidence,
        total_personas=total_personas,
        supporting_personas=supporting_personas,
        dissenting_personas=dissenting_personas,
        omitting_personas=omitting_personas,
        value_distribution=distributions,
        review_required=review_required,
        rationale=rationale,
    )


def _candidate_field_value(
    candidate: InformationUnitCandidate,
    field_name: str,
) -> tuple[str, str]:
    if field_name == "interpreted_statement":
        return (
            normalize_consensus_text(
                candidate.interpreted_statement
            ),
            candidate.interpreted_statement,
        )

    if field_name == "information_type":
        return candidate.information_type, candidate.information_type

    if field_name == "statement_modality":
        return (
            candidate.statement_modality,
            candidate.statement_modality,
        )

    if field_name == "epistemic_class":
        return candidate.epistemic_class, candidate.epistemic_class

    if field_name == "semantic_evidence":
        value = _semantic_evidence_value(candidate)
        canonical = canonical_consensus_json(value)
        return canonical, canonical

    raise SemanticConsensusValidationError(
        f"Unsupported consensus field: {field_name!r}."
    )


def _semantic_evidence_value(
    candidate: InformationUnitCandidate,
) -> dict[str, Any]:
    return {
        "supporting_information_unit_ids": list(
            candidate.supporting_information_unit_ids
        ),
        "derivation_rationale": (
            normalize_consensus_text(
                candidate.derivation_rationale
            )
            if candidate.derivation_rationale is not None
            else None
        ),
        "missing_evidence": (
            normalize_consensus_text(
                candidate.missing_evidence
            )
            if candidate.missing_evidence is not None
            else None
        ),
    }


def _information_unit_draft(
    candidate: InformationUnitCandidate,
) -> ConsensusInformationUnitDraft:
    return ConsensusInformationUnitDraft(
        source_anchors=candidate.source_anchors,
        source_excerpt=candidate.source_excerpt,
        interpreted_statement=candidate.interpreted_statement,
        information_type=candidate.information_type,
        statement_modality=candidate.statement_modality,
        epistemic_class=candidate.epistemic_class,
        supporting_information_unit_ids=(
            candidate.supporting_information_unit_ids
        ),
        derivation_rationale=candidate.derivation_rationale,
        missing_evidence=candidate.missing_evidence,
    )


def _confidence_rationale(
    *,
    total_personas: int,
    supporting_count: int,
    dissenting_count: int,
    omitting_count: int,
    has_incomplete: bool,
    has_indeterminate: bool,
    has_instability: bool,
    has_uncertainty: bool,
    is_assumption: bool,
    confidence: str,
) -> str:
    flags: list[str] = []

    if has_incomplete:
        flags.append("technical team execution is incomplete")

    if has_indeterminate:
        flags.append("at least one persona vote is indeterminate")

    if has_instability:
        flags.append("repeated persona runs are unstable")

    if has_uncertainty:
        flags.append("agent uncertainty is explicit")

    if is_assumption:
        flags.append("the selected statement is an assumption")

    flag_text = (
        "; ".join(flags)
        if flags
        else "no confidence-limiting flag is present"
    )
    return (
        f"Ordinal confidence {confidence}: "
        f"{supporting_count} of {total_personas} required "
        f"personas support the selected complete candidate; "
        f"{dissenting_count} dissent and {omitting_count} "
        f"omit it; {flag_text}."
    )


def _evidence_sort_key(
    evidence_key: EvidenceKey,
) -> tuple[Any, ...]:
    anchor_coordinates, source_excerpt = evidence_key
    return (
        anchor_coordinates,
        source_excerpt,
    )


def _reference_sort_key(
    reference: AgentCandidateReference,
) -> tuple[str, int, str, str]:
    return (
        reference.persona_id,
        reference.persona_run_index,
        reference.agent_id,
        reference.candidate_id,
    )


def _issue_sort_key(
    issue: SemanticConsensusIssue,
) -> tuple[str, str, int, str, str]:
    return (
        issue.persona_id or "",
        issue.agent_id or "",
        issue.persona_run_index or 0,
        issue.code,
        issue.message,
    )