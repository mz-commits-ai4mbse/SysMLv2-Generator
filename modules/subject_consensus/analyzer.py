"""Deterministic field-level consensus over canonical Subject interpretations.

No LLM call and no semantic-similarity inference occur here.

Every distinct Persona receives at most one vote for one structured field or
one relationship key. Repeated runs of the same Persona measure stability only
and can never create additional independent votes.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json

from modules.subject_interpretation.types import (
    PersonaSubjectInterpretation,
    SubjectInterpretationRunResult,
    SharedSubjectInterpretationResult,
)

from .errors import (
    SubjectConsensusConfigurationError,
    SubjectConsensusIntegrityError,
)
from .types import (
    SUBJECT_CONSENSUS_SCHEMA_VERSION,
    ConsensusValueDistribution,
    FieldConsensusAssessment,
    PersonaDiagnosticVariant,
    PersonaStatementVariant,
    RelationshipConsensusOutcome,
    SharedSubjectConsensusResult,
    SubjectConsensusOutcome,
)


_STRUCTURED_FIELDS = (
    "information_type",
    "statement_modality",
    "epistemic_class",
)


def analyze_subject_consensus(
    value: SharedSubjectInterpretationResult,
) -> SharedSubjectConsensusResult:
    """Analyze structured field and relationship agreement deterministically."""

    _validate_input(value)

    runs_by_persona: dict[str, list[SubjectInterpretationRunResult]] = (
        defaultdict(list)
    )
    for run in value.run_results:
        runs_by_persona[run.persona_id].append(run)

    ordered_runs_by_persona = {
        persona_id: tuple(
            sorted(
                runs_by_persona[persona_id],
                key=lambda run: run.persona_run_index,
            )
        )
        for persona_id in value.required_personas
    }

    subject_outcomes = tuple(
        _analyze_subject(
            canonical_subject_id=subject_id,
            required_personas=value.required_personas,
            runs_by_persona=ordered_runs_by_persona,
        )
        for subject_id in value.canonical_subject_ids
    )

    relationship_outcomes = _analyze_relationships(
        required_personas=value.required_personas,
        runs_by_persona=ordered_runs_by_persona,
    )

    fingerprint_body = {
        "schema_version": SUBJECT_CONSENSUS_SCHEMA_VERSION,
        "project_id": value.project_id,
        "source_id": value.source_id,
        "source_projection_id": value.source_projection_id,
        "team_id": value.team_id,
        "required_personas": list(value.required_personas),
        "runs_per_persona": value.runs_per_persona,
        "canonical_subject_ids": list(value.canonical_subject_ids),
        "subject_outcomes": [
            _subject_outcome_to_dict(outcome)
            for outcome in subject_outcomes
        ],
        "relationship_outcomes": [
            _relationship_outcome_to_dict(outcome)
            for outcome in relationship_outcomes
        ],
        "human_review_required": True,
    }

    return SharedSubjectConsensusResult(
        schema_version=SUBJECT_CONSENSUS_SCHEMA_VERSION,
        project_id=value.project_id,
        source_id=value.source_id,
        source_projection_id=value.source_projection_id,
        team_id=value.team_id,
        required_personas=value.required_personas,
        runs_per_persona=value.runs_per_persona,
        canonical_subject_ids=value.canonical_subject_ids,
        subject_outcomes=subject_outcomes,
        relationship_outcomes=relationship_outcomes,
        human_review_required=True,
        content_fingerprint=_canonical_sha256(fingerprint_body),
    )


def _analyze_subject(
    *,
    canonical_subject_id: str,
    required_personas: tuple[str, ...],
    runs_by_persona: dict[str, tuple[SubjectInterpretationRunResult, ...]],
) -> SubjectConsensusOutcome:
    interpretations_by_persona = {
        persona_id: tuple(
            _interpretation_for_subject(
                run,
                canonical_subject_id,
            )
            for run in runs_by_persona[persona_id]
        )
        for persona_id in required_personas
    }

    field_assessments = {
        field_name: _assess_structured_field(
            field_name=field_name,
            required_personas=required_personas,
            interpretations_by_persona=interpretations_by_persona,
        )
        for field_name in _STRUCTURED_FIELDS
    }

    statement_variants = tuple(
        _statement_variant(
            persona_id,
            interpretations_by_persona[persona_id],
        )
        for persona_id in required_personas
    )
    uncertainty_variants = tuple(
        _diagnostic_variant(
            persona_id,
            tuple(
                uncertainty
                for interpretation in interpretations_by_persona[persona_id]
                for uncertainty in interpretation.uncertainties
            ),
        )
        for persona_id in required_personas
    )
    missing_evidence_variants = tuple(
        _diagnostic_variant(
            persona_id,
            tuple(
                interpretation.missing_evidence
                for interpretation in interpretations_by_persona[persona_id]
                if interpretation.missing_evidence is not None
            ),
        )
        for persona_id in required_personas
    )

    attention = (
        any(
            assessment.review_attention_required
            for assessment in field_assessments.values()
        )
        or any(
            variant.values
            for variant in uncertainty_variants
        )
        or any(
            variant.values
            for variant in missing_evidence_variants
        )
        or any(
            not variant.stable_across_runs
            for variant in statement_variants
        )
    )

    return SubjectConsensusOutcome(
        canonical_subject_id=canonical_subject_id,
        information_type=field_assessments["information_type"],
        statement_modality=field_assessments["statement_modality"],
        epistemic_class=field_assessments["epistemic_class"],
        statement_variants=statement_variants,
        uncertainty_variants=uncertainty_variants,
        missing_evidence_variants=missing_evidence_variants,
        review_attention_required=attention,
    )


def _assess_structured_field(
    *,
    field_name: str,
    required_personas: tuple[str, ...],
    interpretations_by_persona: dict[
        str,
        tuple[PersonaSubjectInterpretation, ...],
    ],
) -> FieldConsensusAssessment:
    stable_votes: dict[str, str] = {}
    unstable_personas = []

    for persona_id in required_personas:
        values = tuple(
            getattr(interpretation, field_name)
            for interpretation in interpretations_by_persona[persona_id]
        )
        unique_values = tuple(dict.fromkeys(values))
        if len(unique_values) == 1:
            stable_votes[persona_id] = unique_values[0]
        else:
            unstable_personas.append(persona_id)

    distribution_map: dict[str, list[str]] = defaultdict(list)
    for persona_id, field_value in stable_votes.items():
        distribution_map[field_value].append(persona_id)

    distribution = tuple(
        ConsensusValueDistribution(
            value=field_value,
            supporting_personas=tuple(sorted(personas)),
        )
        for field_value, personas in sorted(distribution_map.items())
    )

    selected_value, level, confidence, supporters = _classify_distribution(
        stable_votes=stable_votes,
        required_personas=required_personas,
    )

    dissenters = tuple(
        persona_id
        for persona_id in required_personas
        if persona_id not in supporters
        and persona_id not in unstable_personas
    )

    return FieldConsensusAssessment(
        field_name=field_name,
        consensus_level=level,
        confidence=confidence,
        selected_value=selected_value,
        total_personas=len(required_personas),
        supporting_personas=tuple(sorted(supporters)),
        dissenting_personas=dissenters,
        unstable_personas=tuple(sorted(unstable_personas)),
        value_distribution=distribution,
        review_attention_required=(confidence != "high"),
    )


def _classify_distribution(
    *,
    stable_votes: dict[str, str],
    required_personas: tuple[str, ...],
) -> tuple[str | None, str, str, tuple[str, ...]]:
    total = len(required_personas)

    if not stable_votes:
        return None, "indeterminate", "low", ()

    counts = Counter(stable_votes.values())
    highest = max(counts.values())
    winners = tuple(
        sorted(
            value
            for value, count in counts.items()
            if count == highest
        )
    )

    if (
        len(stable_votes) == total
        and len(winners) == 1
        and highest == total
    ):
        selected = winners[0]
        supporters = tuple(
            persona_id
            for persona_id in required_personas
            if stable_votes.get(persona_id) == selected
        )
        return selected, "unanimous", "high", supporters

    if len(winners) == 1 and highest > total / 2:
        selected = winners[0]
        supporters = tuple(
            persona_id
            for persona_id in required_personas
            if stable_votes.get(persona_id) == selected
        )
        return selected, "majority", "medium", supporters

    return None, "divergent", "low", ()


def _statement_variant(
    persona_id: str,
    interpretations: tuple[PersonaSubjectInterpretation, ...],
) -> PersonaStatementVariant:
    values = _ordered_unique(
        interpretation.interpreted_statement
        for interpretation in interpretations
    )
    return PersonaStatementVariant(
        persona_id=persona_id,
        statements=values,
        stable_across_runs=(len(values) == 1),
    )


def _diagnostic_variant(
    persona_id: str,
    values,
) -> PersonaDiagnosticVariant:
    unique = _ordered_unique(values)
    return PersonaDiagnosticVariant(
        persona_id=persona_id,
        values=unique,
        stable_across_runs=(len(unique) <= 1),
    )


def _analyze_relationships(
    *,
    required_personas: tuple[str, ...],
    runs_by_persona: dict[str, tuple[SubjectInterpretationRunResult, ...]],
) -> tuple[RelationshipConsensusOutcome, ...]:
    all_keys = set()

    per_persona_run_maps = {}
    for persona_id in required_personas:
        run_maps = []
        for run in runs_by_persona[persona_id]:
            relation_map = defaultdict(list)
            for relation in run.relationships:
                key = (
                    relation.source_subject_id,
                    relation.relationship_kind,
                    relation.target_subject_id,
                )
                relation_map[key].append(relation.statement)
                all_keys.add(key)
            run_maps.append(dict(relation_map))
        per_persona_run_maps[persona_id] = tuple(run_maps)

    outcomes = []
    for key in sorted(all_keys):
        supporters = []
        omitting = []
        unstable = []
        statement_variants = []

        for persona_id in required_personas:
            run_maps = per_persona_run_maps[persona_id]
            present = tuple(key in run_map for run_map in run_maps)

            statements = _ordered_unique(
                statement
                for run_map in run_maps
                for statement in run_map.get(key, ())
            )
            if statements:
                statement_variants.append(
                    PersonaStatementVariant(
                        persona_id=persona_id,
                        statements=statements,
                        stable_across_runs=(
                            all(present)
                            and len(statements) == 1
                        ),
                    )
                )

            if all(present):
                supporters.append(persona_id)
            elif not any(present):
                omitting.append(persona_id)
            else:
                unstable.append(persona_id)

        count = len(supporters)
        total = len(required_personas)
        if count == total:
            level = "unanimous"
            confidence = "high"
        elif count > total / 2:
            level = "majority"
            confidence = "medium"
        else:
            level = "divergent"
            confidence = "low"

        outcomes.append(
            RelationshipConsensusOutcome(
                source_subject_id=key[0],
                relationship_kind=key[1],
                target_subject_id=key[2],
                consensus_level=level,
                confidence=confidence,
                total_personas=total,
                supporting_personas=tuple(sorted(supporters)),
                omitting_personas=tuple(sorted(omitting)),
                unstable_personas=tuple(sorted(unstable)),
                statement_variants=tuple(
                    sorted(
                        statement_variants,
                        key=lambda item: item.persona_id,
                    )
                ),
                review_attention_required=(confidence != "high"),
            )
        )

    return tuple(outcomes)


def _interpretation_for_subject(
    run: SubjectInterpretationRunResult,
    canonical_subject_id: str,
) -> PersonaSubjectInterpretation:
    matches = tuple(
        interpretation
        for interpretation in run.interpretations
        if interpretation.canonical_subject_id == canonical_subject_id
    )
    if len(matches) != 1:
        raise SubjectConsensusIntegrityError(
            "Every Persona run must contain exactly one interpretation "
            f"for {canonical_subject_id}."
        )
    return matches[0]


def _validate_input(
    value: SharedSubjectInterpretationResult,
) -> None:
    if not isinstance(value, SharedSubjectInterpretationResult):
        raise SubjectConsensusConfigurationError(
            "value must be a SharedSubjectInterpretationResult."
        )

    personas = value.required_personas
    if not personas or len(personas) != len(set(personas)):
        raise SubjectConsensusConfigurationError(
            "required_personas must be non-empty and unique."
        )
    if not value.canonical_subject_ids:
        raise SubjectConsensusConfigurationError(
            "canonical_subject_ids must be non-empty."
        )

    expected_keys = {
        (persona_id, run_index)
        for persona_id in personas
        for run_index in range(1, value.runs_per_persona + 1)
    }
    actual_keys = {
        (run.persona_id, run.persona_run_index)
        for run in value.run_results
    }
    if (
        actual_keys != expected_keys
        or len(value.run_results) != len(expected_keys)
    ):
        raise SubjectConsensusIntegrityError(
            "Persona/run population does not match the interpretation result."
        )

    expected_subjects = value.canonical_subject_ids
    expected_subject_set = set(expected_subjects)

    for run in value.run_results:
        if (
            run.project_id != value.project_id
            or run.source_id != value.source_id
            or run.source_projection_id != value.source_projection_id
            or run.team_id != value.team_id
        ):
            raise SubjectConsensusIntegrityError(
                "Persona run context does not match shared interpretation result."
            )

        actual_subjects = tuple(
            interpretation.canonical_subject_id
            for interpretation in run.interpretations
        )
        if (
            len(actual_subjects) != len(expected_subjects)
            or set(actual_subjects) != expected_subject_set
        ):
            raise SubjectConsensusIntegrityError(
                "Persona run does not cover the exact canonical Subject set."
            )

        for relation in run.relationships:
            if (
                relation.source_subject_id not in expected_subject_set
                or relation.target_subject_id not in expected_subject_set
            ):
                raise SubjectConsensusIntegrityError(
                    "Relationship references Subject outside fixed population."
                )


def subject_consensus_result_to_dict(
    value: SharedSubjectConsensusResult,
) -> dict:
    """Return deterministic JSON-compatible representation."""

    return {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "source_id": value.source_id,
        "source_projection_id": value.source_projection_id,
        "team_id": value.team_id,
        "required_personas": list(value.required_personas),
        "runs_per_persona": value.runs_per_persona,
        "canonical_subject_ids": list(value.canonical_subject_ids),
        "subject_outcomes": [
            _subject_outcome_to_dict(outcome)
            for outcome in value.subject_outcomes
        ],
        "relationship_outcomes": [
            _relationship_outcome_to_dict(outcome)
            for outcome in value.relationship_outcomes
        ],
        "human_review_required": value.human_review_required,
        "content_fingerprint": value.content_fingerprint,
    }


def subject_consensus_result_to_json(
    value: SharedSubjectConsensusResult,
) -> str:
    return (
        json.dumps(
            subject_consensus_result_to_dict(value),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def _subject_outcome_to_dict(
    value: SubjectConsensusOutcome,
) -> dict:
    return {
        "canonical_subject_id": value.canonical_subject_id,
        "information_type": _field_to_dict(value.information_type),
        "statement_modality": _field_to_dict(value.statement_modality),
        "epistemic_class": _field_to_dict(value.epistemic_class),
        "statement_variants": [
            _statement_variant_to_dict(item)
            for item in value.statement_variants
        ],
        "uncertainty_variants": [
            _diagnostic_variant_to_dict(item)
            for item in value.uncertainty_variants
        ],
        "missing_evidence_variants": [
            _diagnostic_variant_to_dict(item)
            for item in value.missing_evidence_variants
        ],
        "review_attention_required": value.review_attention_required,
    }


def _relationship_outcome_to_dict(
    value: RelationshipConsensusOutcome,
) -> dict:
    return {
        "source_subject_id": value.source_subject_id,
        "relationship_kind": value.relationship_kind,
        "target_subject_id": value.target_subject_id,
        "consensus_level": value.consensus_level,
        "confidence": value.confidence,
        "total_personas": value.total_personas,
        "supporting_personas": list(value.supporting_personas),
        "omitting_personas": list(value.omitting_personas),
        "unstable_personas": list(value.unstable_personas),
        "statement_variants": [
            _statement_variant_to_dict(item)
            for item in value.statement_variants
        ],
        "review_attention_required": value.review_attention_required,
    }


def _field_to_dict(
    value: FieldConsensusAssessment,
) -> dict:
    return {
        "field_name": value.field_name,
        "consensus_level": value.consensus_level,
        "confidence": value.confidence,
        "selected_value": value.selected_value,
        "total_personas": value.total_personas,
        "supporting_personas": list(value.supporting_personas),
        "dissenting_personas": list(value.dissenting_personas),
        "unstable_personas": list(value.unstable_personas),
        "value_distribution": [
            {
                "value": item.value,
                "supporting_personas": list(item.supporting_personas),
            }
            for item in value.value_distribution
        ],
        "review_attention_required": value.review_attention_required,
    }


def _statement_variant_to_dict(
    value: PersonaStatementVariant,
) -> dict:
    return {
        "persona_id": value.persona_id,
        "statements": list(value.statements),
        "stable_across_runs": value.stable_across_runs,
    }


def _diagnostic_variant_to_dict(
    value: PersonaDiagnosticVariant,
) -> dict:
    return {
        "persona_id": value.persona_id,
        "values": list(value.values),
        "stable_across_runs": value.stable_across_runs,
    }


def _ordered_unique(values) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _canonical_sha256(value) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
