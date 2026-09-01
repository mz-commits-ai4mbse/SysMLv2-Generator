"""Deterministic contract for ADR-032 cross-source semantic reconciliation."""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
import re
from typing import Any

from modules.engineering_subjects import canonical_subject_set_to_dict
from modules.project_fit import (
    derive_project_fit_gate_state,
    validate_project_fit_assessment,
)
from modules.subject_consensus.analyzer import subject_consensus_result_to_dict

from .errors import (
    ProjectSemanticReconciliationIntegrityError,
    ProjectSemanticReconciliationValidationError,
)
from .prompt import PROJECT_SEMANTIC_RECONCILIATION_PROMPT_SCHEMA_VERSION
from .types import (
    PROJECT_SEMANTIC_RELATION_OUTCOMES,
    ProjectSemanticFieldEvidence,
    ProjectSemanticMentionEvidence,
    ProjectSemanticReconciliationArtifact,
    ProjectSemanticRelation,
    ProjectSemanticSourceInput,
    ProjectSemanticStatementEvidence,
    ProjectSemanticSubject,
)


PROJECT_SEMANTIC_RECONCILIATION_SCHEMA_VERSION = "1.0.0"

_JSON_FENCE = re.compile(
    r"^\s*```(?:json)?\s*(.*?)\s*```\s*$",
    re.S | re.I,
)

_RESPONSE_FIELDS = frozenset(
    {
        "relations",
        "unmatched_subject_refs",
    }
)

_RELATION_FIELDS = frozenset(
    {
        "left_subject_ref",
        "right_subject_ref",
        "outcome",
        "rationale",
        "shared_concepts",
        "material_differences",
    }
)


def prepare_project_semantic_subjects(
    source_inputs: object,
) -> tuple[
    str,
    tuple[ProjectSemanticSubject, ...],
    str,
]:
    """Validate admitted source-local results and materialize project refs."""

    if not isinstance(source_inputs, tuple) or len(source_inputs) < 2:
        raise ProjectSemanticReconciliationValidationError(
            "Cross-source reconciliation requires at least two source inputs."
        )

    validated_inputs = []
    for item in source_inputs:
        if not isinstance(item, ProjectSemanticSourceInput):
            raise ProjectSemanticReconciliationValidationError(
                "source_inputs contains an invalid value."
            )
        _validate_source_input(item)
        validated_inputs.append(item)

    project_ids = {
        item.canonical_subject_set.project_id
        for item in validated_inputs
    }
    if len(project_ids) != 1:
        raise ProjectSemanticReconciliationIntegrityError(
            "Cross-source reconciliation must remain Project-local."
        )
    project_id = next(iter(project_ids))

    source_ids = tuple(
        item.canonical_subject_set.source_id
        for item in validated_inputs
    )
    if len(source_ids) != len(set(source_ids)):
        raise ProjectSemanticReconciliationIntegrityError(
            "Cross-source reconciliation requires distinct registered Sources."
        )

    subjects = []
    for item in sorted(
        validated_inputs,
        key=lambda value: value.canonical_subject_set.source_id,
    ):
        subjects.extend(_materialize_source_subjects(item))

    normalized_subjects = tuple(
        sorted(subjects, key=lambda subject: subject.subject_ref)
    )
    refs = tuple(subject.subject_ref for subject in normalized_subjects)
    if len(refs) != len(set(refs)):
        raise ProjectSemanticReconciliationIntegrityError(
            "Project semantic subject_ref values must be unique."
        )

    input_fingerprint = _sha(
        {
            "prompt_schema_version": (
                PROJECT_SEMANTIC_RECONCILIATION_PROMPT_SCHEMA_VERSION
            ),
            "project_id": project_id,
            "subjects": [
                asdict(subject)
                for subject in normalized_subjects
            ],
        }
    )
    return project_id, normalized_subjects, input_fingerprint


def parse_project_semantic_reconciliation_response(
    text: str,
    *,
    subjects: tuple[ProjectSemanticSubject, ...],
) -> tuple[
    tuple[ProjectSemanticRelation, ...],
    tuple[str, ...],
]:
    """Parse exact relation evidence with complete subject coverage."""

    payload = _require_object(text)
    if frozenset(payload) != _RESPONSE_FIELDS:
        raise ProjectSemanticReconciliationValidationError(
            "Project semantic reconciliation output fields do not match schema."
        )

    subject_by_ref = {
        subject.subject_ref: subject
        for subject in subjects
    }
    known_refs = set(subject_by_ref)
    if len(known_refs) != len(subjects):
        raise ProjectSemanticReconciliationIntegrityError(
            "Input Project semantic Subjects are not unique."
        )

    raw_relations = payload["relations"]
    if not isinstance(raw_relations, list):
        raise ProjectSemanticReconciliationValidationError(
            "relations must be a JSON array."
        )

    relations = []
    seen_pairs = set()
    related_refs = set()

    for raw in raw_relations:
        if not isinstance(raw, dict) or frozenset(raw) != _RELATION_FIELDS:
            raise ProjectSemanticReconciliationValidationError(
                "One semantic relation has invalid fields."
            )

        left = _required_text(
            raw["left_subject_ref"],
            "left_subject_ref",
        )
        right = _required_text(
            raw["right_subject_ref"],
            "right_subject_ref",
        )
        if left not in known_refs or right not in known_refs:
            raise ProjectSemanticReconciliationIntegrityError(
                "Semantic relation references an unknown subject_ref."
            )
        if left == right:
            raise ProjectSemanticReconciliationIntegrityError(
                "A semantic relation cannot self-compare one Subject."
            )

        left_subject = subject_by_ref[left]
        right_subject = subject_by_ref[right]
        if left_subject.source_id == right_subject.source_id:
            raise ProjectSemanticReconciliationIntegrityError(
                "Project semantic relations must compare different Sources."
            )

        left, right = sorted((left, right))
        pair = (left, right)
        if pair in seen_pairs:
            raise ProjectSemanticReconciliationIntegrityError(
                "One unordered cross-source Subject pair may appear only once."
            )
        seen_pairs.add(pair)

        outcome = _required_text(raw["outcome"], "outcome")
        if outcome not in PROJECT_SEMANTIC_RELATION_OUTCOMES:
            raise ProjectSemanticReconciliationValidationError(
                "Semantic relation outcome is unsupported."
            )

        rationale = _required_text(raw["rationale"], "rationale")
        shared = _string_tuple(
            raw["shared_concepts"],
            "shared_concepts",
        )
        differences = _string_tuple(
            raw["material_differences"],
            "material_differences",
        )

        if outcome == "equivalent" and not shared:
            raise ProjectSemanticReconciliationValidationError(
                "equivalent requires positive shared semantic evidence."
            )
        if outcome in {"complementary", "potential_conflict"}:
            if not shared or not differences:
                raise ProjectSemanticReconciliationValidationError(
                    f"{outcome} requires both shared concepts and "
                    "material differences."
                )
        if outcome == "distinct" and not differences:
            raise ProjectSemanticReconciliationValidationError(
                "distinct requires an explicit material difference."
            )

        relations.append(
            ProjectSemanticRelation(
                left_subject_ref=left,
                right_subject_ref=right,
                outcome=outcome,
                rationale=rationale,
                shared_concepts=shared,
                material_differences=differences,
            )
        )
        related_refs.update((left, right))

    unmatched = _string_tuple(
        payload["unmatched_subject_refs"],
        "unmatched_subject_refs",
    )
    unmatched_set = set(unmatched)
    if not unmatched_set <= known_refs:
        raise ProjectSemanticReconciliationIntegrityError(
            "unmatched_subject_refs contains an unknown subject_ref."
        )
    if related_refs & unmatched_set:
        raise ProjectSemanticReconciliationIntegrityError(
            "A Subject cannot be both related and unmatched."
        )
    if related_refs | unmatched_set != known_refs:
        missing = sorted(known_refs - related_refs - unmatched_set)
        raise ProjectSemanticReconciliationIntegrityError(
            "Semantic reconciliation must explicitly cover every Subject; "
            f"missing: {missing}."
        )

    normalized_relations = tuple(
        sorted(
            relations,
            key=lambda relation: (
                relation.left_subject_ref,
                relation.right_subject_ref,
            ),
        )
    )
    return normalized_relations, unmatched


def create_project_semantic_reconciliation_artifact(
    *,
    project_id: str,
    subjects: tuple[ProjectSemanticSubject, ...],
    input_fingerprint: str,
    relations: tuple[ProjectSemanticRelation, ...],
    unmatched_subject_refs: tuple[str, ...],
    llm_provider: str,
    llm_model: str,
    llm_response_id: str | None,
) -> ProjectSemanticReconciliationArtifact:
    """Create immutable non-authoritative relationship evidence."""

    _validate_sha256(input_fingerprint, "input_fingerprint")
    _required_text(project_id, "project_id")
    _required_text(llm_provider, "llm_provider")
    _required_text(llm_model, "llm_model")
    if llm_response_id is not None:
        _required_text(llm_response_id, "llm_response_id")

    # Re-run the complete output contract over the supplied immutable values.
    parsed_relations, parsed_unmatched = (
        parse_project_semantic_reconciliation_response(
            json.dumps(
                {
                    "relations": [
                        asdict(relation)
                        for relation in relations
                    ],
                    "unmatched_subject_refs": list(
                        unmatched_subject_refs
                    ),
                },
                ensure_ascii=False,
            ),
            subjects=subjects,
        )
    )

    source_ids = tuple(
        sorted({subject.source_id for subject in subjects})
    )
    body = {
        "schema_version": (
            PROJECT_SEMANTIC_RECONCILIATION_SCHEMA_VERSION
        ),
        "project_id": project_id,
        "source_ids": source_ids,
        "subjects": tuple(subjects),
        "relations": parsed_relations,
        "unmatched_subject_refs": parsed_unmatched,
        "prompt_schema_version": (
            PROJECT_SEMANTIC_RECONCILIATION_PROMPT_SCHEMA_VERSION
        ),
        "llm_provider": llm_provider.strip(),
        "llm_model": llm_model.strip(),
        "llm_response_id": (
            None
            if llm_response_id is None
            else llm_response_id.strip()
        ),
        "input_fingerprint": input_fingerprint,
        "human_review_required": True,
    }

    fingerprint_body = {
        **body,
        "subjects": [
            asdict(subject)
            for subject in body["subjects"]
        ],
        "relations": [
            asdict(relation)
            for relation in body["relations"]
        ],
        "unmatched_subject_refs": list(
            body["unmatched_subject_refs"]
        ),
        "source_ids": list(body["source_ids"]),
    }
    artifact = ProjectSemanticReconciliationArtifact(
        **body,
        content_fingerprint=_sha(fingerprint_body),
    )
    validate_project_semantic_reconciliation_artifact(artifact)
    return artifact


def validate_project_semantic_reconciliation_artifact(
    artifact: ProjectSemanticReconciliationArtifact,
) -> None:
    """Validate exact provenance, coverage, and content fingerprint."""

    if not isinstance(
        artifact,
        ProjectSemanticReconciliationArtifact,
    ):
        raise ProjectSemanticReconciliationValidationError(
            "artifact must be a ProjectSemanticReconciliationArtifact."
        )
    if (
        artifact.schema_version
        != PROJECT_SEMANTIC_RECONCILIATION_SCHEMA_VERSION
    ):
        raise ProjectSemanticReconciliationValidationError(
            "Unsupported project semantic reconciliation schema_version."
        )
    if artifact.human_review_required is not True:
        raise ProjectSemanticReconciliationIntegrityError(
            "Project semantic reconciliation can never waive Human Review."
        )

    for label, value in (
        ("project_id", artifact.project_id),
        ("prompt_schema_version", artifact.prompt_schema_version),
        ("llm_provider", artifact.llm_provider),
        ("llm_model", artifact.llm_model),
    ):
        _required_text(value, label)

    _validate_sha256(
        artifact.input_fingerprint,
        "input_fingerprint",
    )
    _validate_sha256(
        artifact.content_fingerprint,
        "content_fingerprint",
    )

    refs = tuple(subject.subject_ref for subject in artifact.subjects)
    if not refs or refs != tuple(sorted(refs)):
        raise ProjectSemanticReconciliationValidationError(
            "subjects must be non-empty and use deterministic subject_ref order."
        )
    if len(refs) != len(set(refs)):
        raise ProjectSemanticReconciliationIntegrityError(
            "subjects contains duplicate subject_ref values."
        )
    if any(
        subject.project_id != artifact.project_id
        for subject in artifact.subjects
    ):
        raise ProjectSemanticReconciliationIntegrityError(
            "One semantic Subject crosses the artifact Project boundary."
        )

    expected_sources = tuple(
        sorted({subject.source_id for subject in artifact.subjects})
    )
    if artifact.source_ids != expected_sources:
        raise ProjectSemanticReconciliationIntegrityError(
            "source_ids do not match semantic Subject provenance."
        )
    if len(expected_sources) < 2:
        raise ProjectSemanticReconciliationIntegrityError(
            "Cross-source reconciliation requires at least two Sources."
        )

    for subject in artifact.subjects:
        _validate_project_semantic_subject(subject)

    # Coverage and pair validation.
    parsed_relations, parsed_unmatched = (
        parse_project_semantic_reconciliation_response(
            json.dumps(
                {
                    "relations": [
                        asdict(relation)
                        for relation in artifact.relations
                    ],
                    "unmatched_subject_refs": list(
                        artifact.unmatched_subject_refs
                    ),
                },
                ensure_ascii=False,
            ),
            subjects=artifact.subjects,
        )
    )
    if (
        parsed_relations != artifact.relations
        or parsed_unmatched != artifact.unmatched_subject_refs
    ):
        raise ProjectSemanticReconciliationIntegrityError(
            "Reconciliation artifact is not in canonical relation order."
        )

    body = {
        key: value
        for key, value in asdict(artifact).items()
        if key != "content_fingerprint"
    }
    expected = _sha(body)
    if artifact.content_fingerprint != expected:
        raise ProjectSemanticReconciliationIntegrityError(
            "Project semantic reconciliation fingerprint does not match content."
        )


def project_semantic_reconciliation_to_dict(
    artifact: ProjectSemanticReconciliationArtifact,
) -> dict[str, Any]:
    """Return validated JSON-compatible reconciliation evidence."""

    validate_project_semantic_reconciliation_artifact(artifact)
    return asdict(artifact)


def project_semantic_reconciliation_to_json(
    artifact: ProjectSemanticReconciliationArtifact,
) -> str:
    """Serialize reconciliation evidence deterministically."""

    return json.dumps(
        project_semantic_reconciliation_to_dict(artifact),
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def _validate_source_input(
    item: ProjectSemanticSourceInput,
) -> None:
    try:
        validate_project_fit_assessment(item.project_fit)
    except Exception as exc:
        raise ProjectSemanticReconciliationValidationError(
            "Project Fit assessment is invalid."
        ) from exc

    if derive_project_fit_gate_state(item.project_fit) != "admitted":
        raise ProjectSemanticReconciliationIntegrityError(
            "Only Project-Fit-admitted engineering Sources may enter "
            "cross-source semantic reconciliation."
        )

    try:
        canonical_subject_set_to_dict(item.canonical_subject_set)
    except Exception as exc:
        raise ProjectSemanticReconciliationValidationError(
            "Canonical Subject Set is invalid."
        ) from exc

    _validate_subject_consensus(item.subject_consensus)

    subject_set = item.canonical_subject_set
    consensus = item.subject_consensus
    fit = item.project_fit

    bindings = (
        (subject_set.project_id, fit.project_id, "project_id"),
        (subject_set.source_id, fit.source_id, "source_id"),
        (
            subject_set.source_projection_id,
            fit.source_projection_id,
            "source_projection_id",
        ),
        (
            subject_set.source_projection_fingerprint,
            fit.candidate_projection_fingerprint,
            "source_projection_fingerprint",
        ),
        (consensus.project_id, subject_set.project_id, "consensus project_id"),
        (consensus.source_id, subject_set.source_id, "consensus source_id"),
        (
            consensus.source_projection_id,
            subject_set.source_projection_id,
            "consensus source_projection_id",
        ),
    )
    for actual, expected, label in bindings:
        if actual != expected:
            raise ProjectSemanticReconciliationIntegrityError(
                "Cross-source semantic input provenance mismatch: "
                f"{label}."
            )

    subject_ids = tuple(
        subject.canonical_subject_id
        for subject in subject_set.subjects
    )
    if tuple(consensus.canonical_subject_ids) != subject_ids:
        raise ProjectSemanticReconciliationIntegrityError(
            "Subject consensus does not cover the exact canonical Subject set "
            "in deterministic order."
        )
    outcome_ids = tuple(
        outcome.canonical_subject_id
        for outcome in consensus.subject_outcomes
    )
    if outcome_ids != subject_ids:
        raise ProjectSemanticReconciliationIntegrityError(
            "Subject consensus outcomes do not match the exact Subject set."
        )


def _validate_subject_consensus(consensus) -> None:
    try:
        payload = subject_consensus_result_to_dict(consensus)
    except Exception as exc:
        raise ProjectSemanticReconciliationValidationError(
            "Subject consensus result cannot be serialized."
        ) from exc

    fingerprint = payload.pop("content_fingerprint", None)
    _validate_sha256(
        fingerprint,
        "subject consensus content_fingerprint",
    )
    if _sha(payload) != fingerprint:
        raise ProjectSemanticReconciliationIntegrityError(
            "Subject consensus fingerprint does not match content."
        )
    if consensus.human_review_required is not True:
        raise ProjectSemanticReconciliationIntegrityError(
            "Source-level Subject consensus must retain Human Review."
        )


def _materialize_source_subjects(
    item: ProjectSemanticSourceInput,
) -> tuple[ProjectSemanticSubject, ...]:
    subject_set = item.canonical_subject_set
    consensus = item.subject_consensus
    mention_by_id = {
        mention.mention_id: mention
        for mention in subject_set.mentions
    }
    consensus_by_id = {
        outcome.canonical_subject_id: outcome
        for outcome in consensus.subject_outcomes
    }

    values = []
    for subject in subject_set.subjects:
        outcome = consensus_by_id[subject.canonical_subject_id]
        mention_evidence = tuple(
            ProjectSemanticMentionEvidence(
                mention_id=mention_by_id[mention_id].mention_id,
                exact_text=mention_by_id[mention_id].exact_text,
                source_evidence_ids=(
                    mention_by_id[mention_id].source_evidence_ids
                ),
                mention_fingerprint=(
                    mention_by_id[mention_id].content_fingerprint
                ),
            )
            for mention_id in subject.mention_ids
        )
        statement_evidence = tuple(
            ProjectSemanticStatementEvidence(
                persona_id=variant.persona_id,
                statements=variant.statements,
                stable_across_runs=variant.stable_across_runs,
            )
            for variant in outcome.statement_variants
        )
        field_evidence = tuple(
            ProjectSemanticFieldEvidence(
                field_name=field.field_name,
                selected_value=field.selected_value,
                consensus_level=field.consensus_level,
                confidence=field.confidence,
                review_attention_required=(
                    field.review_attention_required
                ),
            )
            for field in (
                outcome.information_type,
                outcome.statement_modality,
                outcome.epistemic_class,
            )
        )

        subject_ref = (
            f"project_subject:{subject_set.source_id}:"
            f"{subject_set.source_projection_id}:"
            f"{subject.canonical_subject_id}"
        )
        subject_body = {
            "subject_ref": subject_ref,
            "project_id": subject_set.project_id,
            "source_id": subject_set.source_id,
            "source_projection_id": subject_set.source_projection_id,
            "canonical_subject_id": subject.canonical_subject_id,
            "canonical_label": subject.canonical_label,
            "subject_form": subject.subject_form,
            "identity_status": subject.identity_status,
            "canonical_subject_fingerprint": subject.content_fingerprint,
            "canonical_subject_set_fingerprint": (
                subject_set.content_fingerprint
            ),
            "subject_consensus_fingerprint": (
                consensus.content_fingerprint
            ),
            "project_fit_fingerprint": (
                item.project_fit.assessment_fingerprint
            ),
            "mention_evidence": mention_evidence,
            "statement_evidence": statement_evidence,
            "field_evidence": field_evidence,
            "source_review_attention_required": (
                outcome.review_attention_required
            ),
        }
        fingerprint_body = {
            **subject_body,
            "mention_evidence": [
                asdict(value)
                for value in mention_evidence
            ],
            "statement_evidence": [
                asdict(value)
                for value in statement_evidence
            ],
            "field_evidence": [
                asdict(value)
                for value in field_evidence
            ],
        }
        values.append(
            ProjectSemanticSubject(
                **subject_body,
                content_fingerprint=_sha(fingerprint_body),
            )
        )
    return tuple(values)


def _validate_project_semantic_subject(
    subject: ProjectSemanticSubject,
) -> None:
    if not isinstance(subject, ProjectSemanticSubject):
        raise ProjectSemanticReconciliationValidationError(
            "subjects contains an invalid ProjectSemanticSubject."
        )

    for label, value in (
        ("subject_ref", subject.subject_ref),
        ("project_id", subject.project_id),
        ("source_id", subject.source_id),
        ("source_projection_id", subject.source_projection_id),
        ("canonical_subject_id", subject.canonical_subject_id),
        ("canonical_label", subject.canonical_label),
        ("subject_form", subject.subject_form),
        ("identity_status", subject.identity_status),
    ):
        _required_text(value, label)

    expected_ref = (
        f"project_subject:{subject.source_id}:"
        f"{subject.source_projection_id}:"
        f"{subject.canonical_subject_id}"
    )
    if subject.subject_ref != expected_ref:
        raise ProjectSemanticReconciliationIntegrityError(
            "Project semantic subject_ref does not match exact source identity."
        )

    for label, value in (
        (
            "canonical_subject_fingerprint",
            subject.canonical_subject_fingerprint,
        ),
        (
            "canonical_subject_set_fingerprint",
            subject.canonical_subject_set_fingerprint,
        ),
        (
            "subject_consensus_fingerprint",
            subject.subject_consensus_fingerprint,
        ),
        (
            "project_fit_fingerprint",
            subject.project_fit_fingerprint,
        ),
        ("content_fingerprint", subject.content_fingerprint),
    ):
        _validate_sha256(value, label)

    if not subject.mention_evidence:
        raise ProjectSemanticReconciliationIntegrityError(
            "Every Project semantic Subject requires grounded mention evidence."
        )
    for mention in subject.mention_evidence:
        _required_text(mention.mention_id, "mention_id")
        _required_text(mention.exact_text, "exact_text")
        _validate_sha256(
            mention.mention_fingerprint,
            "mention_fingerprint",
        )

    body = {
        key: value
        for key, value in asdict(subject).items()
        if key != "content_fingerprint"
    }
    if subject.content_fingerprint != _sha(body):
        raise ProjectSemanticReconciliationIntegrityError(
            "Project semantic Subject fingerprint does not match content."
        )


def _require_object(text: str) -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise ProjectSemanticReconciliationValidationError(
            "Project semantic reconciliation output must be non-empty JSON."
        )
    match = _JSON_FENCE.fullmatch(text)
    normalized = match.group(1) if match else text.strip()
    try:
        value = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise ProjectSemanticReconciliationValidationError(
            "Project semantic reconciliation output must be valid JSON."
        ) from exc
    if not isinstance(value, dict):
        raise ProjectSemanticReconciliationValidationError(
            "Project semantic reconciliation output must be a JSON object."
        )
    return value


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectSemanticReconciliationValidationError(
            f"{label} must be a non-empty string."
        )
    if value != value.strip():
        raise ProjectSemanticReconciliationValidationError(
            f"{label} must not contain surrounding whitespace."
        )
    return value


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)):
        raise ProjectSemanticReconciliationValidationError(
            f"{label} must be a tuple or JSON array."
        )
    checked = tuple(
        _required_text(item, label)
        for item in value
    )
    if len(checked) != len(set(checked)):
        raise ProjectSemanticReconciliationValidationError(
            f"{label} must not contain duplicates."
        )
    return tuple(sorted(checked))


def _validate_sha256(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise ProjectSemanticReconciliationValidationError(
            f"{label} must be a lowercase SHA-256 string."
        )
    return value


def _sha(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
