"""Validate and serialize deterministic semantic consensus results.

Human confirmation decisions are deliberately excluded. A consensus result
may recommend a quick confirmation or detailed review, but it cannot record
that a person confirmed publication.
"""

from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any

from modules.information_units.types import (
    EPISTEMIC_CLASSES,
    INFORMATION_TYPES,
    SEMANTIC_CONFIDENCE_LEVELS,
    STATEMENT_MODALITIES,
    InformationUnitSourceAnchor,
)
from modules.project_sources.identifiers import validate_source_id
from modules.project_workspace.identifiers import is_valid_project_id
from modules.semantic_extraction.identifiers import (
    validate_information_unit_candidate_id,
)
from modules.semantic_extraction.manifest import (
    parse_information_unit_candidate,
)
from modules.source_projection.identifiers import (
    segment_id_sequence,
    validate_source_projection_id,
)

from .errors import (
    DuplicateAgentCandidateReferenceError,
    SemanticConsensusIntegrityError,
    SemanticConsensusValidationError,
)
from .identifiers import (
    format_semantic_consensus_candidate_id,
    validate_semantic_consensus_candidate_id,
)
from .types import (
    PERSONA_STABILITY_LEVELS,
    SEMANTIC_CONSENSUS_FIELD_NAMES,
    SEMANTIC_CONSENSUS_ISSUE_LEVELS,
    SEMANTIC_CONSENSUS_LEVELS,
    SEMANTIC_REVIEW_MODES,
    SEMANTIC_VARIANCE_LEVELS,
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


SEMANTIC_CONSENSUS_SCHEMA_VERSION = "1.0.0"

_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)
_SEMANTIC_VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+$"
)

_RESULT_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "source_id",
        "source_projection_id",
        "team_id",
        "consensus_report_id",
        "required_personas",
        "persona_run_expectations",
        "llm_provider",
        "llm_model",
        "prompt_schema_version",
        "outcomes",
        "issues",
        "created_at",
    }
)
_RUN_EXPECTATION_FIELDS = frozenset(
    {
        "persona_id",
        "expected_run_count",
    }
)
_AGENT_REFERENCE_FIELDS = frozenset(
    {
        "persona_id",
        "agent_id",
        "persona_run_index",
        "candidate_id",
    }
)
_STABILITY_FIELDS = frozenset(
    {
        "persona_id",
        "expected_run_count",
        "observed_run_indices",
        "omitted_run_indices",
        "stability_level",
        "candidate_references",
        "rationale",
    }
)
_VALUE_DISTRIBUTION_FIELDS = frozenset(
    {
        "canonical_value",
        "display_value",
        "supporting_personas",
        "candidate_references",
    }
)
_FIELD_ASSESSMENT_FIELDS = frozenset(
    {
        "field_name",
        "selected_value",
        "consensus_level",
        "variance_level",
        "confidence",
        "total_personas",
        "supporting_personas",
        "dissenting_personas",
        "omitting_personas",
        "value_distribution",
        "review_required",
        "rationale",
    }
)
_DRAFT_FIELDS = frozenset(
    {
        "source_anchors",
        "source_excerpt",
        "interpreted_statement",
        "information_type",
        "statement_modality",
        "epistemic_class",
        "supporting_information_unit_ids",
        "derivation_rationale",
        "missing_evidence",
    }
)
_OUTCOME_FIELDS = frozenset(
    {
        "consensus_candidate_id",
        "source_anchors",
        "source_excerpt",
        "candidate_references",
        "persona_stability",
        "field_assessments",
        "proposed_information_unit",
        "consensus_level",
        "variance_level",
        "confidence",
        "total_personas",
        "supporting_personas",
        "dissenting_personas",
        "omitting_personas",
        "confirmation_required",
        "review_required",
        "recommended_review_mode",
        "publication_eligible",
        "confidence_rationale",
    }
)
_ISSUE_FIELDS = frozenset(
    {
        "code",
        "message",
        "issue_level",
        "persona_id",
        "agent_id",
        "persona_run_index",
    }
)

_FIELD_ORDER = (
    "existence",
    "interpreted_statement",
    "information_type",
    "statement_modality",
    "epistemic_class",
    "semantic_evidence",
)


def parse_semantic_consensus_result(
    payload: Any,
    *,
    expected_project_id: str | None = None,
    expected_source_id: str | None = None,
    expected_source_projection_id: str | None = None,
    expected_team_id: str | None = None,
    expected_consensus_report_id: str | None = None,
) -> SemanticConsensusResult:
    """Parse and validate one strict consensus-result payload."""

    item = _require_exact_object(
        payload,
        _RESULT_FIELDS,
        "Semantic Consensus Result",
    )
    schema_version = item["schema_version"]

    if schema_version != SEMANTIC_CONSENSUS_SCHEMA_VERSION:
        raise SemanticConsensusValidationError(
            "Unsupported Semantic Consensus schema_version: "
            f"{schema_version!r}."
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
    consensus_report_id = _require_stored_text(
        item["consensus_report_id"],
        "consensus_report_id",
    )
    required_personas = _parse_required_personas(
        item["required_personas"]
    )
    persona_run_expectations = _parse_run_expectations(
        item["persona_run_expectations"],
        required_personas=required_personas,
    )
    expectation_by_persona = {
        expectation.persona_id: (
            expectation.expected_run_count
        )
        for expectation in persona_run_expectations
    }
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
    outcomes = tuple(
        _parse_outcome(
            value,
            required_personas=required_personas,
            expectation_by_persona=expectation_by_persona,
            expected_candidate_id=(
                format_semantic_consensus_candidate_id(
                    index
                )
            ),
        )
        for index, value in enumerate(
            _require_list(item["outcomes"], "outcomes"),
            start=1,
        )
    )
    issues = tuple(
        _parse_issue(
            value,
            required_personas=required_personas,
            expectation_by_persona=expectation_by_persona,
        )
        for value in _require_list(
            item["issues"],
            "issues",
        )
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
        consensus_report_id,
        expected_consensus_report_id,
        _require_stored_text,
        "consensus_report_id",
    )
    _validate_outcome_collection(outcomes)
    _validate_issue_collection(issues)
    _validate_global_candidate_references(outcomes)

    return SemanticConsensusResult(
        schema_version=schema_version,
        project_id=project_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        team_id=team_id,
        consensus_report_id=consensus_report_id,
        required_personas=required_personas,
        persona_run_expectations=(
            persona_run_expectations
        ),
        llm_provider=llm_provider,
        llm_model=llm_model,
        prompt_schema_version=prompt_schema_version,
        outcomes=outcomes,
        issues=issues,
        created_at=created_at,
    )


def semantic_consensus_result_from_json(
    text: str,
    *,
    expected_project_id: str | None = None,
    expected_source_id: str | None = None,
    expected_source_projection_id: str | None = None,
    expected_team_id: str | None = None,
    expected_consensus_report_id: str | None = None,
) -> SemanticConsensusResult:
    """Parse one strict Semantic Consensus Result JSON string."""

    if not isinstance(text, str):
        raise SemanticConsensusValidationError(
            "Semantic Consensus Result JSON input must be a "
            "string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except SemanticConsensusValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise SemanticConsensusValidationError(
            "Semantic Consensus Result contains invalid JSON: "
            f"{exc}."
        ) from exc

    return parse_semantic_consensus_result(
        payload,
        expected_project_id=expected_project_id,
        expected_source_id=expected_source_id,
        expected_source_projection_id=(
            expected_source_projection_id
        ),
        expected_team_id=expected_team_id,
        expected_consensus_report_id=(
            expected_consensus_report_id
        ),
    )


def validate_semantic_consensus_result(
    result: SemanticConsensusResult,
) -> None:
    """Validate one immutable Semantic Consensus Result."""

    semantic_consensus_result_to_dict(result)


def semantic_consensus_result_to_dict(
    result: SemanticConsensusResult,
) -> dict[str, Any]:
    """Return the canonical JSON-compatible representation."""

    if not isinstance(result, SemanticConsensusResult):
        raise SemanticConsensusValidationError(
            "result must be a SemanticConsensusResult instance."
        )

    payload = _result_payload(result)
    validated = parse_semantic_consensus_result(payload)
    return _result_payload(validated)


def semantic_consensus_result_to_json(
    result: SemanticConsensusResult,
) -> str:
    """Serialize one Semantic Consensus Result deterministically."""

    return (
        json.dumps(
            semantic_consensus_result_to_dict(result),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def _parse_required_personas(
    value: Any,
) -> tuple[str, ...]:
    personas = tuple(
        _require_stored_text(
            persona_id,
            f"required_personas[{index}]",
        )
        for index, persona_id in enumerate(
            _require_list(
                value,
                "required_personas",
            )
        )
    )

    if len(personas) < 2:
        raise SemanticConsensusValidationError(
            "required_personas must contain at least two "
            "personas."
        )

    if len(personas) != len(set(personas)):
        raise SemanticConsensusValidationError(
            "required_personas must not contain duplicates."
        )

    if personas != tuple(sorted(personas)):
        raise SemanticConsensusValidationError(
            "required_personas must be ordered by persona ID."
        )

    return personas


def _parse_run_expectations(
    value: Any,
    *,
    required_personas: tuple[str, ...],
) -> tuple[PersonaRunExpectation, ...]:
    expectations: list[PersonaRunExpectation] = []

    for index, raw in enumerate(
        _require_list(
            value,
            "persona_run_expectations",
        )
    ):
        label = f"persona_run_expectations[{index}]"
        item = _require_exact_object(
            raw,
            _RUN_EXPECTATION_FIELDS,
            label,
        )
        expectations.append(
            PersonaRunExpectation(
                persona_id=_require_stored_text(
                    item["persona_id"],
                    f"{label}.persona_id",
                ),
                expected_run_count=_require_positive_integer(
                    item["expected_run_count"],
                    f"{label}.expected_run_count",
                ),
            )
        )

    persona_ids = tuple(
        expectation.persona_id
        for expectation in expectations
    )

    if persona_ids != required_personas:
        raise SemanticConsensusValidationError(
            "persona_run_expectations must contain exactly one "
            "entry for each required persona in persona order."
        )

    return tuple(expectations)


def _parse_outcome(
    value: Any,
    *,
    required_personas: tuple[str, ...],
    expectation_by_persona: dict[str, int],
    expected_candidate_id: str,
) -> SemanticConsensusOutcome:
    item = _require_exact_object(
        value,
        _OUTCOME_FIELDS,
        "Semantic Consensus Outcome",
    )
    consensus_candidate_id = _require_consensus_candidate_id(
        item["consensus_candidate_id"],
        "consensus_candidate_id",
    )

    if consensus_candidate_id != expected_candidate_id:
        raise SemanticConsensusValidationError(
            "consensus_candidate_id values must start at "
            "SCC-000001 and remain gapless in outcome order."
        )

    source_anchors, source_excerpt = (
        _parse_source_evidence(
            item["source_anchors"],
            item["source_excerpt"],
        )
    )
    candidate_references = _parse_agent_references(
        item["candidate_references"],
        label="candidate_references",
        required_personas=required_personas,
        expectation_by_persona=expectation_by_persona,
    )
    persona_stability = _parse_persona_stability(
        item["persona_stability"],
        required_personas=required_personas,
        expectation_by_persona=expectation_by_persona,
    )
    field_assessments = _parse_field_assessments(
        item["field_assessments"],
        required_personas=required_personas,
        expectation_by_persona=expectation_by_persona,
    )
    proposed_information_unit = _parse_optional_draft(
        item["proposed_information_unit"]
    )
    consensus_level = _require_choice(
        item["consensus_level"],
        SEMANTIC_CONSENSUS_LEVELS,
        "consensus_level",
    )
    variance_level = _require_choice(
        item["variance_level"],
        SEMANTIC_VARIANCE_LEVELS,
        "variance_level",
    )
    confidence = _require_choice(
        item["confidence"],
        SEMANTIC_CONFIDENCE_LEVELS,
        "confidence",
    )
    total_personas = _require_positive_integer(
        item["total_personas"],
        "total_personas",
    )

    if total_personas != len(required_personas):
        raise SemanticConsensusValidationError(
            "total_personas must equal the number of required "
            "personas."
        )

    supporting_personas = _parse_persona_subset(
        item["supporting_personas"],
        "supporting_personas",
        required_personas,
    )
    dissenting_personas = _parse_persona_subset(
        item["dissenting_personas"],
        "dissenting_personas",
        required_personas,
    )
    omitting_personas = _parse_persona_subset(
        item["omitting_personas"],
        "omitting_personas",
        required_personas,
    )
    _validate_persona_partition(
        supporting_personas,
        dissenting_personas,
        omitting_personas,
        required_personas=required_personas,
        label="Semantic Consensus Outcome",
    )
    confirmation_required = _require_boolean(
        item["confirmation_required"],
        "confirmation_required",
    )
    review_required = _require_boolean(
        item["review_required"],
        "review_required",
    )
    recommended_review_mode = _require_choice(
        item["recommended_review_mode"],
        SEMANTIC_REVIEW_MODES,
        "recommended_review_mode",
    )
    publication_eligible = _require_boolean(
        item["publication_eligible"],
        "publication_eligible",
    )
    confidence_rationale = _require_stored_text(
        item["confidence_rationale"],
        "confidence_rationale",
    )

    if confirmation_required is not True:
        raise SemanticConsensusValidationError(
            "confirmation_required must always be true."
        )

    expected_review_mode = (
        "detailed_review"
        if review_required
        else "quick_confirmation"
    )

    if recommended_review_mode != expected_review_mode:
        raise SemanticConsensusValidationError(
            "recommended_review_mode does not match "
            "review_required."
        )

    _validate_confidence_variance(
        confidence=confidence,
        variance_level=variance_level,
        label="Semantic Consensus Outcome",
    )

    if confidence == "high" and consensus_level != "unanimous":
        raise SemanticConsensusValidationError(
            "High-confidence consensus must be unanimous."
        )

    if proposed_information_unit is not None:
        if (
            proposed_information_unit.source_anchors
            != source_anchors
            or proposed_information_unit.source_excerpt
            != source_excerpt
        ):
            raise SemanticConsensusIntegrityError(
                "Proposed Information Unit evidence must equal "
                "its consensus outcome evidence."
            )

        if (
            proposed_information_unit.epistemic_class
            == "assumption"
            and not review_required
        ):
            raise SemanticConsensusValidationError(
                "An assumption requires detailed Human Review."
            )

    if publication_eligible:
        if proposed_information_unit is None:
            raise SemanticConsensusValidationError(
                "publication_eligible requires a proposed "
                "Information Unit."
            )

        if (
            confidence != "high"
            or consensus_level != "unanimous"
            or review_required
            or recommended_review_mode
            != "quick_confirmation"
        ):
            raise SemanticConsensusValidationError(
                "publication_eligible requires unanimous high "
                "confidence and quick human confirmation."
            )

    return SemanticConsensusOutcome(
        consensus_candidate_id=consensus_candidate_id,
        source_anchors=source_anchors,
        source_excerpt=source_excerpt,
        candidate_references=candidate_references,
        persona_stability=persona_stability,
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
        confirmation_required=confirmation_required,
        review_required=review_required,
        recommended_review_mode=recommended_review_mode,
        publication_eligible=publication_eligible,
        confidence_rationale=confidence_rationale,
    )


def _parse_persona_stability(
    value: Any,
    *,
    required_personas: tuple[str, ...],
    expectation_by_persona: dict[str, int],
) -> tuple[PersonaStabilityAssessment, ...]:
    assessments: list[PersonaStabilityAssessment] = []

    for index, raw in enumerate(
        _require_list(value, "persona_stability")
    ):
        label = f"persona_stability[{index}]"
        item = _require_exact_object(
            raw,
            _STABILITY_FIELDS,
            label,
        )
        persona_id = _require_stored_text(
            item["persona_id"],
            f"{label}.persona_id",
        )

        if persona_id not in expectation_by_persona:
            raise SemanticConsensusValidationError(
                f"{label}.persona_id is not required."
            )

        expected_run_count = _require_positive_integer(
            item["expected_run_count"],
            f"{label}.expected_run_count",
        )

        if (
            expected_run_count
            != expectation_by_persona[persona_id]
        ):
            raise SemanticConsensusValidationError(
                f"{label}.expected_run_count does not match "
                "the persona-run expectation."
            )

        observed = _parse_run_indices(
            item["observed_run_indices"],
            f"{label}.observed_run_indices",
            expected_run_count,
        )
        omitted = _parse_run_indices(
            item["omitted_run_indices"],
            f"{label}.omitted_run_indices",
            expected_run_count,
        )

        if not set(omitted).issubset(observed):
            raise SemanticConsensusValidationError(
                f"{label}.omitted_run_indices must be a subset "
                "of observed_run_indices."
            )

        stability_level = _require_choice(
            item["stability_level"],
            PERSONA_STABILITY_LEVELS,
            f"{label}.stability_level",
        )
        references = _parse_agent_references(
            item["candidate_references"],
            label=f"{label}.candidate_references",
            required_personas=required_personas,
            expectation_by_persona=expectation_by_persona,
        )

        if any(
            reference.persona_id != persona_id
            for reference in references
        ):
            raise SemanticConsensusValidationError(
                f"{label}.candidate_references must belong to "
                "the assessed persona."
            )

        rationale = _require_stored_text(
            item["rationale"],
            f"{label}.rationale",
        )
        assessments.append(
            PersonaStabilityAssessment(
                persona_id=persona_id,
                expected_run_count=expected_run_count,
                observed_run_indices=observed,
                omitted_run_indices=omitted,
                stability_level=stability_level,
                candidate_references=references,
                rationale=rationale,
            )
        )

    persona_ids = tuple(
        assessment.persona_id
        for assessment in assessments
    )

    if persona_ids != required_personas:
        raise SemanticConsensusValidationError(
            "persona_stability must contain exactly one "
            "assessment per required persona in persona order."
        )

    return tuple(assessments)


def _parse_field_assessments(
    value: Any,
    *,
    required_personas: tuple[str, ...],
    expectation_by_persona: dict[str, int],
) -> tuple[FieldConsensusAssessment, ...]:
    assessments: list[FieldConsensusAssessment] = []

    for index, raw in enumerate(
        _require_list(value, "field_assessments")
    ):
        label = f"field_assessments[{index}]"
        item = _require_exact_object(
            raw,
            _FIELD_ASSESSMENT_FIELDS,
            label,
        )
        field_name = _require_choice(
            item["field_name"],
            SEMANTIC_CONSENSUS_FIELD_NAMES,
            f"{label}.field_name",
        )
        selected_value = _require_optional_text(
            item["selected_value"],
            f"{label}.selected_value",
        )
        consensus_level = _require_choice(
            item["consensus_level"],
            SEMANTIC_CONSENSUS_LEVELS,
            f"{label}.consensus_level",
        )
        variance_level = _require_choice(
            item["variance_level"],
            SEMANTIC_VARIANCE_LEVELS,
            f"{label}.variance_level",
        )
        confidence = _require_choice(
            item["confidence"],
            SEMANTIC_CONFIDENCE_LEVELS,
            f"{label}.confidence",
        )
        total_personas = _require_positive_integer(
            item["total_personas"],
            f"{label}.total_personas",
        )

        if total_personas != len(required_personas):
            raise SemanticConsensusValidationError(
                f"{label}.total_personas must equal the number "
                "of required personas."
            )

        supporting = _parse_persona_subset(
            item["supporting_personas"],
            f"{label}.supporting_personas",
            required_personas,
        )
        dissenting = _parse_persona_subset(
            item["dissenting_personas"],
            f"{label}.dissenting_personas",
            required_personas,
        )
        omitting = _parse_persona_subset(
            item["omitting_personas"],
            f"{label}.omitting_personas",
            required_personas,
        )
        _validate_persona_partition(
            supporting,
            dissenting,
            omitting,
            required_personas=required_personas,
            label=label,
        )
        distributions = _parse_value_distribution(
            item["value_distribution"],
            label=f"{label}.value_distribution",
            required_personas=required_personas,
            expectation_by_persona=expectation_by_persona,
        )
        review_required = _require_boolean(
            item["review_required"],
            f"{label}.review_required",
        )
        rationale = _require_stored_text(
            item["rationale"],
            f"{label}.rationale",
        )
        _validate_confidence_variance(
            confidence=confidence,
            variance_level=variance_level,
            label=label,
        )

        if (
            selected_value is not None
            and selected_value
            not in {
                distribution.canonical_value
                for distribution in distributions
            }
        ):
            raise SemanticConsensusIntegrityError(
                f"{label}.selected_value is absent from its "
                "value_distribution."
            )

        assessments.append(
            FieldConsensusAssessment(
                field_name=field_name,
                selected_value=selected_value,
                consensus_level=consensus_level,
                variance_level=variance_level,
                confidence=confidence,
                total_personas=total_personas,
                supporting_personas=supporting,
                dissenting_personas=dissenting,
                omitting_personas=omitting,
                value_distribution=distributions,
                review_required=review_required,
                rationale=rationale,
            )
        )

    if tuple(
        assessment.field_name
        for assessment in assessments
    ) != _FIELD_ORDER:
        raise SemanticConsensusValidationError(
            "field_assessments must contain each critical field "
            "exactly once in the defined order."
        )

    return tuple(assessments)


def _parse_value_distribution(
    value: Any,
    *,
    label: str,
    required_personas: tuple[str, ...],
    expectation_by_persona: dict[str, int],
) -> tuple[ConsensusValueDistribution, ...]:
    distributions: list[ConsensusValueDistribution] = []

    for index, raw in enumerate(
        _require_list(value, label)
    ):
        item_label = f"{label}[{index}]"
        item = _require_exact_object(
            raw,
            _VALUE_DISTRIBUTION_FIELDS,
            item_label,
        )
        distributions.append(
            ConsensusValueDistribution(
                canonical_value=_require_stored_text(
                    item["canonical_value"],
                    f"{item_label}.canonical_value",
                ),
                display_value=_require_stored_text(
                    item["display_value"],
                    f"{item_label}.display_value",
                ),
                supporting_personas=_parse_persona_subset(
                    item["supporting_personas"],
                    f"{item_label}.supporting_personas",
                    required_personas,
                ),
                candidate_references=_parse_agent_references(
                    item["candidate_references"],
                    label=(
                        f"{item_label}.candidate_references"
                    ),
                    required_personas=required_personas,
                    expectation_by_persona=(
                        expectation_by_persona
                    ),
                ),
            )
        )

    canonical_values = tuple(
        distribution.canonical_value
        for distribution in distributions
    )

    if len(canonical_values) != len(set(canonical_values)):
        raise SemanticConsensusIntegrityError(
            f"{label} contains duplicate canonical values."
        )

    if canonical_values != tuple(sorted(canonical_values)):
        raise SemanticConsensusValidationError(
            f"{label} must be ordered by canonical_value."
        )

    return tuple(distributions)


def _parse_optional_draft(
    value: Any,
) -> ConsensusInformationUnitDraft | None:
    if value is None:
        return None

    item = _require_exact_object(
        value,
        _DRAFT_FIELDS,
        "proposed_information_unit",
    )
    parsed = parse_information_unit_candidate(
        {
            "candidate_id": "IUC-000001",
            "source_anchors": item["source_anchors"],
            "source_excerpt": item["source_excerpt"],
            "interpreted_statement": (
                item["interpreted_statement"]
            ),
            "information_type": item["information_type"],
            "statement_modality": (
                item["statement_modality"]
            ),
            "epistemic_class": item["epistemic_class"],
            "supporting_information_unit_ids": (
                item["supporting_information_unit_ids"]
            ),
            "derivation_rationale": (
                item["derivation_rationale"]
            ),
            "missing_evidence": item["missing_evidence"],
            "extraction_rationale": (
                "Consensus draft structural validation."
            ),
            "uncertainties": [],
        }
    )
    return ConsensusInformationUnitDraft(
        source_anchors=parsed.source_anchors,
        source_excerpt=parsed.source_excerpt,
        interpreted_statement=parsed.interpreted_statement,
        information_type=parsed.information_type,
        statement_modality=parsed.statement_modality,
        epistemic_class=parsed.epistemic_class,
        supporting_information_unit_ids=(
            parsed.supporting_information_unit_ids
        ),
        derivation_rationale=parsed.derivation_rationale,
        missing_evidence=parsed.missing_evidence,
    )


def _parse_source_evidence(
    anchors: Any,
    excerpt: Any,
) -> tuple[
    tuple[InformationUnitSourceAnchor, ...],
    str,
]:
    parsed = parse_information_unit_candidate(
        {
            "candidate_id": "IUC-000001",
            "source_anchors": anchors,
            "source_excerpt": excerpt,
            "interpreted_statement": (
                "Consensus evidence cluster."
            ),
            "information_type": "unclassified",
            "statement_modality": "descriptive",
            "epistemic_class": "explicit",
            "supporting_information_unit_ids": [],
            "derivation_rationale": None,
            "missing_evidence": None,
            "extraction_rationale": (
                "Consensus evidence structural validation."
            ),
            "uncertainties": [],
        }
    )
    return parsed.source_anchors, parsed.source_excerpt


def _parse_agent_references(
    value: Any,
    *,
    label: str,
    required_personas: tuple[str, ...],
    expectation_by_persona: dict[str, int],
) -> tuple[AgentCandidateReference, ...]:
    references: list[AgentCandidateReference] = []

    for index, raw in enumerate(
        _require_list(value, label)
    ):
        item_label = f"{label}[{index}]"
        item = _require_exact_object(
            raw,
            _AGENT_REFERENCE_FIELDS,
            item_label,
        )
        persona_id = _require_stored_text(
            item["persona_id"],
            f"{item_label}.persona_id",
        )

        if persona_id not in required_personas:
            raise SemanticConsensusValidationError(
                f"{item_label}.persona_id is not required."
            )

        run_index = _require_positive_integer(
            item["persona_run_index"],
            f"{item_label}.persona_run_index",
        )

        if run_index > expectation_by_persona[persona_id]:
            raise SemanticConsensusValidationError(
                f"{item_label}.persona_run_index exceeds its "
                "configured expectation."
            )

        references.append(
            AgentCandidateReference(
                persona_id=persona_id,
                agent_id=_require_stored_text(
                    item["agent_id"],
                    f"{item_label}.agent_id",
                ),
                persona_run_index=run_index,
                candidate_id=_require_agent_candidate_id(
                    item["candidate_id"],
                    f"{item_label}.candidate_id",
                ),
            )
        )

    keys = tuple(
        _reference_key(reference)
        for reference in references
    )

    if len(keys) != len(set(keys)):
        raise DuplicateAgentCandidateReferenceError(
            f"{label} contains duplicate agent-candidate "
            "references."
        )

    if keys != tuple(sorted(keys)):
        raise SemanticConsensusValidationError(
            f"{label} must be deterministically ordered."
        )

    return tuple(references)


def _parse_issue(
    value: Any,
    *,
    required_personas: tuple[str, ...],
    expectation_by_persona: dict[str, int],
) -> SemanticConsensusIssue:
    item = _require_exact_object(
        value,
        _ISSUE_FIELDS,
        "Semantic Consensus Issue",
    )
    persona_id = _require_optional_text(
        item["persona_id"],
        "issue.persona_id",
    )

    if (
        persona_id is not None
        and persona_id not in required_personas
    ):
        raise SemanticConsensusValidationError(
            "issue.persona_id is not a required persona."
        )

    agent_id = _require_optional_text(
        item["agent_id"],
        "issue.agent_id",
    )
    run_index = _require_optional_positive_integer(
        item["persona_run_index"],
        "issue.persona_run_index",
    )

    if run_index is not None:
        if persona_id is None:
            raise SemanticConsensusValidationError(
                "issue.persona_run_index requires persona_id."
            )

        if run_index > expectation_by_persona[persona_id]:
            raise SemanticConsensusValidationError(
                "issue.persona_run_index exceeds its configured "
                "expectation."
            )

    if agent_id is not None and persona_id is None:
        raise SemanticConsensusValidationError(
            "issue.agent_id requires persona_id."
        )

    return SemanticConsensusIssue(
        code=_require_identifier_text(
            item["code"],
            "issue.code",
        ),
        message=_require_stored_text(
            item["message"],
            "issue.message",
        ),
        issue_level=_require_choice(
            item["issue_level"],
            SEMANTIC_CONSENSUS_ISSUE_LEVELS,
            "issue.issue_level",
        ),
        persona_id=persona_id,
        agent_id=agent_id,
        persona_run_index=run_index,
    )


def _parse_persona_subset(
    value: Any,
    label: str,
    required_personas: tuple[str, ...],
) -> tuple[str, ...]:
    personas = tuple(
        _require_stored_text(
            persona_id,
            f"{label}[{index}]",
        )
        for index, persona_id in enumerate(
            _require_list(value, label)
        )
    )

    if len(personas) != len(set(personas)):
        raise SemanticConsensusValidationError(
            f"{label} must not contain duplicates."
        )

    if personas != tuple(sorted(personas)):
        raise SemanticConsensusValidationError(
            f"{label} must be ordered by persona ID."
        )

    if not set(personas).issubset(required_personas):
        raise SemanticConsensusValidationError(
            f"{label} contains a persona that is not required."
        )

    return personas


def _parse_run_indices(
    value: Any,
    label: str,
    expected_run_count: int,
) -> tuple[int, ...]:
    indices = tuple(
        _require_positive_integer(
            index,
            f"{label}[{position}]",
        )
        for position, index in enumerate(
            _require_list(value, label)
        )
    )

    if len(indices) != len(set(indices)):
        raise SemanticConsensusValidationError(
            f"{label} must not contain duplicates."
        )

    if indices != tuple(sorted(indices)):
        raise SemanticConsensusValidationError(
            f"{label} must be ordered."
        )

    if any(
        index > expected_run_count
        for index in indices
    ):
        raise SemanticConsensusValidationError(
            f"{label} exceeds expected_run_count."
        )

    return indices


def _validate_persona_partition(
    supporting: tuple[str, ...],
    dissenting: tuple[str, ...],
    omitting: tuple[str, ...],
    *,
    required_personas: tuple[str, ...],
    label: str,
) -> None:
    combined = supporting + dissenting + omitting

    if len(combined) != len(set(combined)):
        raise SemanticConsensusIntegrityError(
            f"{label} persona groups must be disjoint."
        )

    if set(combined) != set(required_personas):
        raise SemanticConsensusIntegrityError(
            f"{label} persona groups must partition all "
            "required personas."
        )


def _validate_confidence_variance(
    *,
    confidence: str,
    variance_level: str,
    label: str,
) -> None:
    expected = {
        "high": "low",
        "medium": "medium",
        "low": "high",
    }[confidence]

    if variance_level != expected:
        raise SemanticConsensusValidationError(
            f"{label} variance_level must be {expected!r} for "
            f"confidence {confidence!r}."
        )


def _validate_outcome_collection(
    outcomes: tuple[SemanticConsensusOutcome, ...],
) -> None:
    order_keys = tuple(
        (
            tuple(
                (
                    segment_id_sequence(anchor.segment_id),
                    anchor.start_offset,
                    anchor.end_offset,
                )
                for anchor in outcome.source_anchors
            ),
            outcome.source_excerpt,
        )
        for outcome in outcomes
    )

    if order_keys != tuple(sorted(order_keys)):
        raise SemanticConsensusValidationError(
            "outcomes must be ordered by exact source evidence."
        )


def _validate_issue_collection(
    issues: tuple[SemanticConsensusIssue, ...],
) -> None:
    keys = tuple(_issue_key(issue) for issue in issues)

    if keys != tuple(sorted(keys)):
        raise SemanticConsensusValidationError(
            "issues must be deterministically ordered."
        )

    if len(keys) != len(set(keys)):
        raise SemanticConsensusIntegrityError(
            "issues must not contain duplicate records."
        )


def _validate_global_candidate_references(
    outcomes: tuple[SemanticConsensusOutcome, ...],
) -> None:
    ownership: dict[
        tuple[str, int, str, str],
        str,
    ] = {}

    for outcome in outcomes:
        for reference in outcome.candidate_references:
            key = _reference_key(reference)
            existing = ownership.get(key)

            if existing is not None:
                raise DuplicateAgentCandidateReferenceError(
                    "Agent candidate reference is shared by "
                    f"{existing} and "
                    f"{outcome.consensus_candidate_id}."
                )

            ownership[key] = outcome.consensus_candidate_id


def _result_payload(
    result: SemanticConsensusResult,
) -> dict[str, Any]:
    return {
        "schema_version": result.schema_version,
        "project_id": result.project_id,
        "source_id": result.source_id,
        "source_projection_id": result.source_projection_id,
        "team_id": result.team_id,
        "consensus_report_id": result.consensus_report_id,
        "required_personas": list(result.required_personas),
        "persona_run_expectations": [
            _run_expectation_payload(expectation)
            for expectation in result.persona_run_expectations
        ],
        "llm_provider": result.llm_provider,
        "llm_model": result.llm_model,
        "prompt_schema_version": result.prompt_schema_version,
        "outcomes": [
            _outcome_payload(outcome)
            for outcome in result.outcomes
        ],
        "issues": [
            _issue_payload(issue)
            for issue in result.issues
        ],
        "created_at": result.created_at,
    }


def _run_expectation_payload(
    expectation: PersonaRunExpectation,
) -> dict[str, Any]:
    if not isinstance(expectation, PersonaRunExpectation):
        raise SemanticConsensusValidationError(
            "persona_run_expectations must contain "
            "PersonaRunExpectation instances."
        )

    return {
        "persona_id": expectation.persona_id,
        "expected_run_count": expectation.expected_run_count,
    }


def _outcome_payload(
    outcome: SemanticConsensusOutcome,
) -> dict[str, Any]:
    if not isinstance(outcome, SemanticConsensusOutcome):
        raise SemanticConsensusValidationError(
            "outcomes must contain SemanticConsensusOutcome "
            "instances."
        )

    return {
        "consensus_candidate_id": (
            outcome.consensus_candidate_id
        ),
        "source_anchors": [
            _anchor_payload(anchor)
            for anchor in outcome.source_anchors
        ],
        "source_excerpt": outcome.source_excerpt,
        "candidate_references": [
            _reference_payload(reference)
            for reference in outcome.candidate_references
        ],
        "persona_stability": [
            _stability_payload(assessment)
            for assessment in outcome.persona_stability
        ],
        "field_assessments": [
            _field_assessment_payload(assessment)
            for assessment in outcome.field_assessments
        ],
        "proposed_information_unit": (
            _draft_payload(outcome.proposed_information_unit)
            if outcome.proposed_information_unit is not None
            else None
        ),
        "consensus_level": outcome.consensus_level,
        "variance_level": outcome.variance_level,
        "confidence": outcome.confidence,
        "total_personas": outcome.total_personas,
        "supporting_personas": list(
            outcome.supporting_personas
        ),
        "dissenting_personas": list(
            outcome.dissenting_personas
        ),
        "omitting_personas": list(
            outcome.omitting_personas
        ),
        "confirmation_required": (
            outcome.confirmation_required
        ),
        "review_required": outcome.review_required,
        "recommended_review_mode": (
            outcome.recommended_review_mode
        ),
        "publication_eligible": (
            outcome.publication_eligible
        ),
        "confidence_rationale": (
            outcome.confidence_rationale
        ),
    }


def _stability_payload(
    assessment: PersonaStabilityAssessment,
) -> dict[str, Any]:
    if not isinstance(
        assessment,
        PersonaStabilityAssessment,
    ):
        raise SemanticConsensusValidationError(
            "persona_stability must contain "
            "PersonaStabilityAssessment instances."
        )

    return {
        "persona_id": assessment.persona_id,
        "expected_run_count": assessment.expected_run_count,
        "observed_run_indices": list(
            assessment.observed_run_indices
        ),
        "omitted_run_indices": list(
            assessment.omitted_run_indices
        ),
        "stability_level": assessment.stability_level,
        "candidate_references": [
            _reference_payload(reference)
            for reference in assessment.candidate_references
        ],
        "rationale": assessment.rationale,
    }


def _field_assessment_payload(
    assessment: FieldConsensusAssessment,
) -> dict[str, Any]:
    if not isinstance(
        assessment,
        FieldConsensusAssessment,
    ):
        raise SemanticConsensusValidationError(
            "field_assessments must contain "
            "FieldConsensusAssessment instances."
        )

    return {
        "field_name": assessment.field_name,
        "selected_value": assessment.selected_value,
        "consensus_level": assessment.consensus_level,
        "variance_level": assessment.variance_level,
        "confidence": assessment.confidence,
        "total_personas": assessment.total_personas,
        "supporting_personas": list(
            assessment.supporting_personas
        ),
        "dissenting_personas": list(
            assessment.dissenting_personas
        ),
        "omitting_personas": list(
            assessment.omitting_personas
        ),
        "value_distribution": [
            _value_distribution_payload(distribution)
            for distribution in assessment.value_distribution
        ],
        "review_required": assessment.review_required,
        "rationale": assessment.rationale,
    }


def _value_distribution_payload(
    distribution: ConsensusValueDistribution,
) -> dict[str, Any]:
    if not isinstance(
        distribution,
        ConsensusValueDistribution,
    ):
        raise SemanticConsensusValidationError(
            "value_distribution must contain "
            "ConsensusValueDistribution instances."
        )

    return {
        "canonical_value": distribution.canonical_value,
        "display_value": distribution.display_value,
        "supporting_personas": list(
            distribution.supporting_personas
        ),
        "candidate_references": [
            _reference_payload(reference)
            for reference in distribution.candidate_references
        ],
    }


def _draft_payload(
    draft: ConsensusInformationUnitDraft,
) -> dict[str, Any]:
    if not isinstance(draft, ConsensusInformationUnitDraft):
        raise SemanticConsensusValidationError(
            "proposed_information_unit must be a "
            "ConsensusInformationUnitDraft instance."
        )

    return {
        "source_anchors": [
            _anchor_payload(anchor)
            for anchor in draft.source_anchors
        ],
        "source_excerpt": draft.source_excerpt,
        "interpreted_statement": draft.interpreted_statement,
        "information_type": draft.information_type,
        "statement_modality": draft.statement_modality,
        "epistemic_class": draft.epistemic_class,
        "supporting_information_unit_ids": list(
            draft.supporting_information_unit_ids
        ),
        "derivation_rationale": draft.derivation_rationale,
        "missing_evidence": draft.missing_evidence,
    }


def _reference_payload(
    reference: AgentCandidateReference,
) -> dict[str, Any]:
    if not isinstance(reference, AgentCandidateReference):
        raise SemanticConsensusValidationError(
            "candidate references must be "
            "AgentCandidateReference instances."
        )

    return {
        "persona_id": reference.persona_id,
        "agent_id": reference.agent_id,
        "persona_run_index": reference.persona_run_index,
        "candidate_id": reference.candidate_id,
    }


def _issue_payload(
    issue: SemanticConsensusIssue,
) -> dict[str, Any]:
    if not isinstance(issue, SemanticConsensusIssue):
        raise SemanticConsensusValidationError(
            "issues must contain SemanticConsensusIssue "
            "instances."
        )

    return {
        "code": issue.code,
        "message": issue.message,
        "issue_level": issue.issue_level,
        "persona_id": issue.persona_id,
        "agent_id": issue.agent_id,
        "persona_run_index": issue.persona_run_index,
    }


def _anchor_payload(
    anchor: InformationUnitSourceAnchor,
) -> dict[str, Any]:
    if not isinstance(anchor, InformationUnitSourceAnchor):
        raise SemanticConsensusValidationError(
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
        raise SemanticConsensusValidationError(
            f"Semantic Consensus Result {label} does not match "
            f"its expected context: {actual!r} != "
            f"{validated_expected!r}."
        )


def _require_project_id(
    value: Any,
    label: str,
) -> str:
    if not is_valid_project_id(value):
        raise SemanticConsensusValidationError(
            f"{label} must contain exactly six digits."
        )

    return value


def _require_source_id(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_source_id(value)
    except Exception as exc:
        raise SemanticConsensusValidationError(
            f"{label} must be a valid Source ID."
        ) from exc


def _require_source_projection_id(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_source_projection_id(value)
    except Exception as exc:
        raise SemanticConsensusValidationError(
            f"{label} must be a valid Source Projection ID."
        ) from exc


def _require_consensus_candidate_id(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_semantic_consensus_candidate_id(value)
    except Exception as exc:
        raise SemanticConsensusValidationError(
            f"{label} must be a valid Semantic Consensus "
            "Candidate ID."
        ) from exc


def _require_agent_candidate_id(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_information_unit_candidate_id(value)
    except Exception as exc:
        raise SemanticConsensusValidationError(
            f"{label} must be a valid Information Unit "
            "Candidate ID."
        ) from exc


def _require_choice(
    value: Any,
    allowed: frozenset[str],
    label: str,
) -> str:
    text = _require_stored_text(value, label)

    if text not in allowed:
        raise SemanticConsensusValidationError(
            f"{label} must be one of: "
            f"{', '.join(sorted(allowed))}."
        )

    return text


def _require_stored_text(
    value: Any,
    label: str,
) -> str:
    if not isinstance(value, str):
        raise SemanticConsensusValidationError(
            f"{label} must be a string."
        )

    if not value.strip():
        raise SemanticConsensusValidationError(
            f"{label} must not be empty."
        )

    if value != value.strip():
        raise SemanticConsensusValidationError(
            f"{label} must not have leading or trailing "
            "whitespace."
        )

    if "\x00" in value or "\r" in value:
        raise SemanticConsensusValidationError(
            f"{label} contains unsupported control characters."
        )

    return value


def _require_identifier_text(
    value: Any,
    label: str,
) -> str:
    text = _require_stored_text(value, label)

    if re.fullmatch(r"[a-z][a-z0-9_]*", text) is None:
        raise SemanticConsensusValidationError(
            f"{label} must use lower_snake_case."
        )

    return text


def _require_optional_text(
    value: Any,
    label: str,
) -> str | None:
    if value is None:
        return None

    return _require_stored_text(value, label)


def _require_positive_integer(
    value: Any,
    label: str,
) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 1
    ):
        raise SemanticConsensusValidationError(
            f"{label} must be a positive integer."
        )

    return value


def _require_optional_positive_integer(
    value: Any,
    label: str,
) -> int | None:
    if value is None:
        return None

    return _require_positive_integer(value, label)


def _require_boolean(
    value: Any,
    label: str,
) -> bool:
    if not isinstance(value, bool):
        raise SemanticConsensusValidationError(
            f"{label} must be a boolean."
        )

    return value


def _require_semantic_version(
    value: Any,
    label: str,
) -> str:
    text = _require_stored_text(value, label)

    if _SEMANTIC_VERSION_PATTERN.fullmatch(text) is None:
        raise SemanticConsensusValidationError(
            f"{label} must use MAJOR.MINOR.PATCH versioning."
        )

    return text


def _require_utc_timestamp(
    value: Any,
    label: str,
) -> str:
    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None
    ):
        raise SemanticConsensusValidationError(
            f"{label} must be an ISO 8601 UTC timestamp "
            "ending in Z."
        )

    try:
        parsed = datetime.fromisoformat(
            value.removesuffix("Z") + "+00:00"
        )
    except ValueError as exc:
        raise SemanticConsensusValidationError(
            f"{label} must be a valid UTC timestamp."
        ) from exc

    if parsed.utcoffset() is None:
        raise SemanticConsensusValidationError(
            f"{label} must contain UTC timezone information."
        )

    return value


def _require_exact_object(
    value: Any,
    fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SemanticConsensusValidationError(
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
        raise SemanticConsensusValidationError(
            f"{label} fields are invalid: "
            f"{'; '.join(problems)}."
        )

    return value


def _require_list(
    value: Any,
    label: str,
) -> list[Any]:
    if not isinstance(value, list):
        raise SemanticConsensusValidationError(
            f"{label} must be a JSON list."
        )

    return value


def _reference_key(
    reference: AgentCandidateReference,
) -> tuple[str, int, str, str]:
    return (
        reference.persona_id,
        reference.persona_run_index,
        reference.agent_id,
        reference.candidate_id,
    )


def _issue_key(
    issue: SemanticConsensusIssue,
) -> tuple[str, str, int, str, str]:
    return (
        issue.persona_id or "",
        issue.agent_id or "",
        issue.persona_run_index or 0,
        issue.code,
        issue.message,
    )


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise SemanticConsensusValidationError(
                f"Duplicate JSON field: {key!r}."
            )

        result[key] = value

    return result