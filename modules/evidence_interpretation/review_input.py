"""Canonical Human-Review input for the corrected shared-Evidence path."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from modules.semantic_extraction import (
    calculate_information_unit_candidate_fingerprint,
)
from modules.source_evidence.types import SourceEvidence

from .errors import (
    EvidenceInterpretationIntegrityError,
    EvidenceInterpretationValidationError,
)
from .types import SharedEvidenceInterpretationResult


SHARED_EVIDENCE_REVIEW_INPUT_SCHEMA_VERSION = "1.0.0"


def build_shared_evidence_review_input(
    *,
    source_sha256: str,
    processing_run_id: str,
    attempt_id: str,
    source_evidence: tuple[SourceEvidence, ...],
    interpretation_result: SharedEvidenceInterpretationResult,
) -> dict[str, Any]:
    """Build one deterministic, self-contained review input."""

    if not source_evidence:
        raise EvidenceInterpretationValidationError(
            "source_evidence must not be empty for Human Review."
        )
    if not isinstance(
        interpretation_result,
        SharedEvidenceInterpretationResult,
    ):
        raise EvidenceInterpretationValidationError(
            "interpretation_result must be SharedEvidenceInterpretationResult."
        )

    evidence_by_key = {
        _evidence_key_from_evidence(item): item
        for item in source_evidence
    }
    if len(evidence_by_key) != len(source_evidence):
        raise EvidenceInterpretationIntegrityError(
            "Source Evidence keys must be unique."
        )

    outcome_by_key = {
        _evidence_key_from_outcome(outcome): outcome
        for outcome in interpretation_result.consensus_result.outcomes
    }
    if set(evidence_by_key) != set(outcome_by_key):
        raise EvidenceInterpretationIntegrityError(
            "Consensus outcomes must preserve the exact Source Evidence set."
        )

    subjects = []
    for item in sorted(
        source_evidence,
        key=lambda value: value.source_evidence_id,
    ):
        key = _evidence_key_from_evidence(item)
        outcome = outcome_by_key[key]

        interpretations = []
        for result in interpretation_result.agent_results:
            matches = tuple(
                candidate
                for candidate in result.candidates
                if _evidence_key_from_candidate(candidate) == key
            )
            if len(matches) != 1:
                raise EvidenceInterpretationIntegrityError(
                    "Each persona run must contain exactly one candidate "
                    f"for {item.source_evidence_id}."
                )

            candidate = matches[0]
            interpretations.append(
                {
                    "persona_id": result.persona_id,
                    "agent_id": result.agent_id,
                    "persona_run_index": result.persona_run_index,
                    "candidate_id": candidate.candidate_id,
                    "candidate_content_fingerprint": (
                        calculate_information_unit_candidate_fingerprint(
                            candidate
                        )
                    ),
                    "interpreted_statement": (
                        candidate.interpreted_statement
                    ),
                    "information_type": candidate.information_type,
                    "statement_modality": (
                        candidate.statement_modality
                    ),
                    "epistemic_class": candidate.epistemic_class,
                    "missing_evidence": candidate.missing_evidence,
                    "extraction_rationale": (
                        candidate.extraction_rationale
                    ),
                    "uncertainties": list(candidate.uncertainties),
                }
            )

        consensus_payload = {
            "consensus_candidate_id": outcome.consensus_candidate_id,
            "consensus_level": outcome.consensus_level,
            "variance_level": outcome.variance_level,
            "confidence": outcome.confidence,
            "supporting_personas": list(outcome.supporting_personas),
            "dissenting_personas": list(outcome.dissenting_personas),
            "omitting_personas": list(outcome.omitting_personas),
            "confirmation_required": outcome.confirmation_required,
            "review_required": outcome.review_required,
            "recommended_review_mode": outcome.recommended_review_mode,
            "publication_eligible": outcome.publication_eligible,
            "confidence_rationale": outcome.confidence_rationale,
            "proposed_information_unit": (
                _draft_payload(outcome.proposed_information_unit)
                if outcome.proposed_information_unit is not None
                else None
            ),
        }

        subjects.append(
            {
                "source_evidence_id": item.source_evidence_id,
                "source_evidence_content_fingerprint": (
                    item.content_fingerprint
                ),
                "source_anchors": [
                    {
                        "segment_id": anchor.segment_id,
                        "start_offset": anchor.start_offset,
                        "end_offset": anchor.end_offset,
                    }
                    for anchor in item.source_anchors
                ],
                "source_excerpt": item.source_excerpt,
                "consensus": consensus_payload,
                "consensus_content_fingerprint": (
                    _canonical_sha256(consensus_payload)
                ),
                "persona_interpretations": sorted(
                    interpretations,
                    key=lambda value: (
                        value["persona_id"],
                        value["persona_run_index"],
                    ),
                ),
            }
        )

    body = {
        "schema_version": SHARED_EVIDENCE_REVIEW_INPUT_SCHEMA_VERSION,
        "project_id": interpretation_result.project_id,
        "source_id": interpretation_result.source_id,
        "source_sha256": source_sha256,
        "source_projection_id": (
            interpretation_result.source_projection_id
        ),
        "processing_run_id": processing_run_id,
        "attempt_id": attempt_id,
        "team_id": interpretation_result.team_id,
        "required_personas": list(
            interpretation_result.required_personas
        ),
        "runs_per_persona": interpretation_result.runs_per_persona,
        "consensus_report_id": (
            interpretation_result.consensus_result.consensus_report_id
        ),
        "subjects": subjects,
    }
    return {
        **body,
        "content_fingerprint": _canonical_sha256(body),
    }


def shared_evidence_review_input_to_json(
    payload: dict[str, Any],
) -> str:
    """Validate and serialize one corrected Human-Review input."""

    validate_shared_evidence_review_input(payload)
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def shared_evidence_review_input_from_json(
    text: str,
) -> dict[str, Any]:
    """Parse one corrected Human-Review input."""

    if not isinstance(text, str):
        raise EvidenceInterpretationValidationError(
            "Shared-Evidence review input must be JSON text."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except EvidenceInterpretationValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise EvidenceInterpretationValidationError(
            "Shared-Evidence review input is invalid JSON."
        ) from exc

    validate_shared_evidence_review_input(payload)
    return payload


def validate_shared_evidence_review_input(
    payload: Any,
) -> None:
    """Fail closed on identity, subject and fingerprint drift."""

    required_fields = {
        "schema_version",
        "project_id",
        "source_id",
        "source_sha256",
        "source_projection_id",
        "processing_run_id",
        "attempt_id",
        "team_id",
        "required_personas",
        "runs_per_persona",
        "consensus_report_id",
        "subjects",
        "content_fingerprint",
    }
    if not isinstance(payload, dict) or set(payload) != required_fields:
        raise EvidenceInterpretationValidationError(
            "Shared-Evidence review input fields do not match schema."
        )

    if (
        payload["schema_version"]
        != SHARED_EVIDENCE_REVIEW_INPUT_SCHEMA_VERSION
    ):
        raise EvidenceInterpretationValidationError(
            "Unsupported Shared-Evidence review input schema_version."
        )

    for field_name in (
        "project_id",
        "source_id",
        "source_sha256",
        "source_projection_id",
        "processing_run_id",
        "attempt_id",
        "team_id",
        "consensus_report_id",
        "content_fingerprint",
    ):
        value = payload[field_name]
        if not isinstance(value, str) or not value:
            raise EvidenceInterpretationValidationError(
                f"{field_name} must be non-empty text."
            )

    personas = payload["required_personas"]
    if not isinstance(personas, list) or len(personas) < 2:
        raise EvidenceInterpretationValidationError(
            "required_personas must contain at least two personas."
        )
    if any(
        not isinstance(value, str) or not value
        for value in personas
    ):
        raise EvidenceInterpretationValidationError(
            "required_personas entries must be non-empty strings."
        )
    if len(personas) != len(set(personas)):
        raise EvidenceInterpretationValidationError(
            "required_personas must be unique."
        )

    runs = payload["runs_per_persona"]
    if (
        isinstance(runs, bool)
        or not isinstance(runs, int)
        or not 1 <= runs <= 5
    ):
        raise EvidenceInterpretationValidationError(
            "runs_per_persona must be an integer from 1 to 5."
        )

    subjects = payload["subjects"]
    if not isinstance(subjects, list) or not subjects:
        raise EvidenceInterpretationValidationError(
            "subjects must be a non-empty JSON array."
        )

    seen = set()
    for subject in subjects:
        _validate_subject(subject)
        evidence_id = subject["source_evidence_id"]
        if evidence_id in seen:
            raise EvidenceInterpretationValidationError(
                "source_evidence_id values must be unique."
            )
        seen.add(evidence_id)

    body = dict(payload)
    fingerprint = body.pop("content_fingerprint")
    if fingerprint != _canonical_sha256(body):
        raise EvidenceInterpretationIntegrityError(
            "Shared-Evidence review input fingerprint mismatch."
        )


def _validate_subject(subject: Any) -> None:
    fields = {
        "source_evidence_id",
        "source_evidence_content_fingerprint",
        "source_anchors",
        "source_excerpt",
        "consensus",
        "consensus_content_fingerprint",
        "persona_interpretations",
    }
    if not isinstance(subject, dict) or set(subject) != fields:
        raise EvidenceInterpretationValidationError(
            "Shared-Evidence subject fields do not match schema."
        )

    for name in (
        "source_evidence_id",
        "source_evidence_content_fingerprint",
        "source_excerpt",
        "consensus_content_fingerprint",
    ):
        if not isinstance(subject[name], str) or not subject[name]:
            raise EvidenceInterpretationValidationError(
                f"Subject field {name} must be non-empty text."
            )

    if not isinstance(subject["source_anchors"], list):
        raise EvidenceInterpretationValidationError(
            "source_anchors must be a JSON array."
        )
    if not isinstance(subject["consensus"], dict):
        raise EvidenceInterpretationValidationError(
            "consensus must be a JSON object."
        )
    if (
        subject["consensus_content_fingerprint"]
        != _canonical_sha256(subject["consensus"])
    ):
        raise EvidenceInterpretationIntegrityError(
            "Consensus subject fingerprint mismatch."
        )
    if not isinstance(subject["persona_interpretations"], list):
        raise EvidenceInterpretationValidationError(
            "persona_interpretations must be a JSON array."
        )


def _draft_payload(draft) -> dict[str, Any]:
    return {
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


def _evidence_key_from_evidence(item: SourceEvidence):
    return (
        tuple(
            (
                anchor.segment_id,
                anchor.start_offset,
                anchor.end_offset,
            )
            for anchor in item.source_anchors
        ),
        item.source_excerpt,
    )


def _evidence_key_from_candidate(candidate):
    return (
        tuple(
            (
                anchor.segment_id,
                anchor.start_offset,
                anchor.end_offset,
            )
            for anchor in candidate.source_anchors
        ),
        candidate.source_excerpt,
    )


def _evidence_key_from_outcome(outcome):
    return (
        tuple(
            (
                anchor.segment_id,
                anchor.start_offset,
                anchor.end_offset,
            )
            for anchor in outcome.source_anchors
        ),
        outcome.source_excerpt,
    )


def _canonical_sha256(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceInterpretationValidationError(
                f"Duplicate JSON field is not allowed: {key!r}."
            )
        result[key] = value
    return result
