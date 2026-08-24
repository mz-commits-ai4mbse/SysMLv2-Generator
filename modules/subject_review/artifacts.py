"""Persist R4c canonical-Subject processing outputs as immutable work artifacts."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from modules.subject_consensus import subject_consensus_result_to_dict
from modules.subject_review import subject_review_bundle_to_dict


SUBJECT_PROCESSING_ARTIFACT_SCHEMA_VERSION = "1.0.0"

CANONICAL_SUBJECT_SET_FILENAME = "canonical_subject_set.json"
SUBJECT_INTERPRETATIONS_FILENAME = "subject_interpretations.json"
SUBJECT_CONSENSUS_FILENAME = "subject_consensus.json"
SUBJECT_REVIEW_BUNDLE_FILENAME = "subject_review_bundle.json"

SUBJECT_PROCESSING_ARTIFACT_FILENAMES = (
    CANONICAL_SUBJECT_SET_FILENAME,
    SUBJECT_INTERPRETATIONS_FILENAME,
    SUBJECT_CONSENSUS_FILENAME,
    SUBJECT_REVIEW_BUNDLE_FILENAME,
)


def write_subject_processing_artifacts(
    *,
    output_root: Path | str,
    source_sha256: str,
    processing_run_id: str,
    attempt_id: str,
    subject_set,
    interpretations,
    consensus,
    review_bundle,
) -> tuple[Path, ...]:
    """Write the exact R4c authority chain into the Attempt work tree.

    Files are work outputs only. Final P5 publication remains owned by the
    existing ProjectIngestionPublisher.
    """

    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)

    _validate_bindings(
        subject_set=subject_set,
        interpretations=interpretations,
        consensus=consensus,
        review_bundle=review_bundle,
    )

    authority = {
        "project_id": subject_set.project_id,
        "source_id": subject_set.source_id,
        "source_sha256": _required_text(source_sha256, "source_sha256"),
        "source_projection_id": subject_set.source_projection_id,
        "processing_run_id": _required_text(
            processing_run_id,
            "processing_run_id",
        ),
        "attempt_id": _required_text(attempt_id, "attempt_id"),
    }

    payloads = (
        (
            CANONICAL_SUBJECT_SET_FILENAME,
            "canonical_subject_set",
            _subject_set_to_dict(subject_set),
        ),
        (
            SUBJECT_INTERPRETATIONS_FILENAME,
            "subject_interpretations",
            _interpretations_to_dict(interpretations),
        ),
        (
            SUBJECT_CONSENSUS_FILENAME,
            "subject_consensus",
            subject_consensus_result_to_dict(consensus),
        ),
        (
            SUBJECT_REVIEW_BUNDLE_FILENAME,
            "subject_review_bundle",
            subject_review_bundle_to_dict(review_bundle),
        ),
    )

    written = []
    for filename, artifact_kind, payload in payloads:
        path = root / filename
        if path.exists() or path.is_symlink():
            raise FileExistsError(
                f"Subject processing work artifact already exists: {path}"
            )

        body = {
            "schema_version": SUBJECT_PROCESSING_ARTIFACT_SCHEMA_VERSION,
            "artifact_kind": artifact_kind,
            "authority": authority,
            "payload": payload,
        }
        envelope = {
            **body,
            "content_fingerprint": _canonical_sha256(body),
        }
        text = (
            json.dumps(
                envelope,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n"
        )
        path.write_text(text, encoding="utf-8")
        written.append(path)

    return tuple(written)


def _validate_bindings(
    *,
    subject_set,
    interpretations,
    consensus,
    review_bundle,
) -> None:
    context = (
        subject_set.project_id,
        subject_set.source_id,
        subject_set.source_projection_id,
    )
    for label, value in (
        ("interpretations", interpretations),
        ("consensus", consensus),
        ("review_bundle", review_bundle),
    ):
        candidate = (
            value.project_id,
            value.source_id,
            value.source_projection_id,
        )
        if candidate != context:
            raise ValueError(
                f"{label} does not bind the CanonicalSubjectSet context."
            )

    subject_ids = tuple(
        subject.canonical_subject_id
        for subject in subject_set.subjects
    )
    if tuple(interpretations.canonical_subject_ids) != subject_ids:
        raise ValueError(
            "Subject interpretations do not bind the exact Subject population."
        )
    if tuple(consensus.canonical_subject_ids) != subject_ids:
        raise ValueError(
            "Subject consensus does not bind the exact Subject population."
        )
    if tuple(review_bundle.canonical_subject_ids) != subject_ids:
        raise ValueError(
            "Subject Review Bundle does not bind the exact Subject population."
        )


def _subject_set_to_dict(value) -> dict[str, Any]:
    return {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "source_id": value.source_id,
        "source_projection_id": value.source_projection_id,
        "source_projection_fingerprint": (
            value.source_projection_fingerprint
        ),
        "mentions": [
            {
                "mention_id": item.mention_id,
                "source_span_id": item.source_span_id,
                "segment_id": item.segment_id,
                "start_offset": item.start_offset,
                "end_offset": item.end_offset,
                "exact_text": item.exact_text,
                "source_evidence_ids": list(item.source_evidence_ids),
                "content_fingerprint": item.content_fingerprint,
            }
            for item in value.mentions
        ],
        "subjects": [
            {
                "canonical_subject_id": item.canonical_subject_id,
                "canonical_label": item.canonical_label,
                "subject_form": item.subject_form,
                "identity_status": item.identity_status,
                "mention_ids": list(item.mention_ids),
                "content_fingerprint": item.content_fingerprint,
            }
            for item in value.subjects
        ],
        "content_fingerprint": value.content_fingerprint,
    }


def _interpretations_to_dict(value) -> dict[str, Any]:
    return {
        "project_id": value.project_id,
        "source_id": value.source_id,
        "source_projection_id": value.source_projection_id,
        "team_id": value.team_id,
        "canonical_subject_ids": list(value.canonical_subject_ids),
        "required_personas": list(value.required_personas),
        "runs_per_persona": value.runs_per_persona,
        "run_results": [
            _run_result_to_dict(run)
            for run in value.run_results
        ],
    }


def _run_result_to_dict(run) -> dict[str, Any]:
    return {
        "project_id": run.project_id,
        "source_id": run.source_id,
        "source_projection_id": run.source_projection_id,
        "team_id": run.team_id,
        "agent_id": run.agent_id,
        "persona_id": run.persona_id,
        "persona_run_index": run.persona_run_index,
        "llm_provider": run.llm_provider,
        "llm_model": run.llm_model,
        "prompt_schema_version": run.prompt_schema_version,
        "interpretations": [
            {
                "canonical_subject_id": item.canonical_subject_id,
                "interpreted_statement": item.interpreted_statement,
                "information_type": item.information_type,
                "statement_modality": item.statement_modality,
                "epistemic_class": item.epistemic_class,
                "missing_evidence": item.missing_evidence,
                "rationale": item.rationale,
                "uncertainties": list(item.uncertainties),
                "content_fingerprint": item.content_fingerprint,
            }
            for item in run.interpretations
        ],
        "relationships": [
            {
                "source_subject_id": item.source_subject_id,
                "relationship_kind": item.relationship_kind,
                "target_subject_id": item.target_subject_id,
                "statement": item.statement,
                "content_fingerprint": item.content_fingerprint,
            }
            for item in run.relationships
        ],
        "rejected_relationships": [
            {
                "source_subject_id": item.source_subject_id,
                "relationship_kind": item.relationship_kind,
                "target_subject_id": item.target_subject_id,
                "statement": item.statement,
                "reason_code": item.reason_code,
                "content_fingerprint": item.content_fingerprint,
            }
            for item in getattr(run, "rejected_relationships", ())
        ],
        "classification_repairs": [
            {
                "canonical_subject_id": item.canonical_subject_id,
                "field_name": item.field_name,
                "original_value": item.original_value,
                "repaired_value": item.repaired_value,
                "content_fingerprint": item.content_fingerprint,
            }
            for item in getattr(run, "classification_repairs", ())
        ],
        "content_fingerprint": run.content_fingerprint,
    }


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be non-empty text.")
    return value.strip()


def _canonical_sha256(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
