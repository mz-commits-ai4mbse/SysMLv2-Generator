"""Strict JSON round-trips for accepted S2-S5 reconciliation contracts."""

from __future__ import annotations

from dataclasses import asdict, fields
from hashlib import sha256
import json
import re
from typing import Any

from modules.model_impact_reconciliation import (
    ModelImpactProposal,
    ModelImpactReconciliationArtifact,
    validate_model_impact_reconciliation_artifact,
)
from modules.project_engineering_authority import (
    ProjectAuthorityDecision,
    ProjectAuthorityEntry,
    ProjectAuthoritySubjectBinding,
    ProjectEngineeringAuthorityState,
    validate_project_authority_decision,
    validate_project_engineering_authority_state,
)
from modules.project_fit import (
    ProjectFitAssessment,
    ProjectFitContextReference,
    validate_project_fit_assessment,
)
from modules.project_semantic_reconciliation import (
    ProjectSemanticFieldEvidence,
    ProjectSemanticMentionEvidence,
    ProjectSemanticReconciliationArtifact,
    ProjectSemanticRelation,
    ProjectSemanticStatementEvidence,
    ProjectSemanticSubject,
    validate_project_semantic_reconciliation_artifact,
)

from .errors import (
    ProjectReconciliationPersistenceIntegrityError,
    ProjectReconciliationPersistenceValidationError,
)
from .types import (
    PROJECT_AUTHORITY_BINDING_SNAPSHOT_SCHEMA_VERSION,
    PROJECT_RECONCILIATION_CYCLE_SCHEMA_VERSION,
    ProjectAuthorityBindingSnapshot,
    ProjectReconciliationCycleManifest,
)


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CYCLE_ID = re.compile(r"^PRC-[0-9]{6}$")
_TIMESTAMP = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?Z$"
)


def project_fit_assessment_from_json(text: str) -> ProjectFitAssessment:
    raw = _object(text, "Project Fit assessment")
    _exact_fields(raw, ProjectFitAssessment, "Project Fit assessment")
    refs = tuple(
        _construct_exact(
            ProjectFitContextReference,
            item,
            "Project Fit context reference",
        )
        for item in _list(raw["context_references"], "context_references")
    )
    value = ProjectFitAssessment(
        schema_version=raw["schema_version"],
        project_id=raw["project_id"],
        source_id=raw["source_id"],
        source_role=raw["source_role"],
        source_sha256=raw["source_sha256"],
        source_projection_id=raw["source_projection_id"],
        candidate_projection_fingerprint=raw[
            "candidate_projection_fingerprint"
        ],
        candidate_content_sha256=raw["candidate_content_sha256"],
        processing_run_id=raw["processing_run_id"],
        attempt_id=raw["attempt_id"],
        outcome=raw["outcome"],
        rationale=raw["rationale"],
        matched_concepts=tuple(raw["matched_concepts"]),
        incompatible_concepts=tuple(raw["incompatible_concepts"]),
        supporting_context_refs=tuple(raw["supporting_context_refs"]),
        context_references=refs,
        prompt_schema_version=raw["prompt_schema_version"],
        llm_provider=raw["llm_provider"],
        llm_model=raw["llm_model"],
        llm_response_id=raw["llm_response_id"],
        input_fingerprint=raw["input_fingerprint"],
        assessment_fingerprint=raw["assessment_fingerprint"],
    )
    validate_project_fit_assessment(value)
    return value


def project_semantic_reconciliation_from_json(
    text: str,
) -> ProjectSemanticReconciliationArtifact:
    raw = _object(text, "Project Semantic Reconciliation")
    _exact_fields(
        raw,
        ProjectSemanticReconciliationArtifact,
        "Project Semantic Reconciliation",
    )

    subjects = []
    for item in _list(raw["subjects"], "subjects"):
        _exact_fields(
            item,
            ProjectSemanticSubject,
            "Project Semantic Subject",
        )
        mention_evidence = tuple(
            ProjectSemanticMentionEvidence(
                mention_id=e["mention_id"],
                exact_text=e["exact_text"],
                source_evidence_ids=tuple(e["source_evidence_ids"]),
                mention_fingerprint=e["mention_fingerprint"],
            )
            for e in _checked_items(
                item["mention_evidence"],
                ProjectSemanticMentionEvidence,
                "Project Semantic mention evidence",
            )
        )
        statement_evidence = tuple(
            ProjectSemanticStatementEvidence(
                persona_id=e["persona_id"],
                statements=tuple(e["statements"]),
                stable_across_runs=e["stable_across_runs"],
            )
            for e in _checked_items(
                item["statement_evidence"],
                ProjectSemanticStatementEvidence,
                "Project Semantic statement evidence",
            )
        )
        field_evidence = tuple(
            _construct_exact(
                ProjectSemanticFieldEvidence,
                e,
                "Project Semantic field evidence",
            )
            for e in _list(item["field_evidence"], "field_evidence")
        )
        subjects.append(
            ProjectSemanticSubject(
                subject_ref=item["subject_ref"],
                project_id=item["project_id"],
                source_id=item["source_id"],
                source_projection_id=item["source_projection_id"],
                canonical_subject_id=item["canonical_subject_id"],
                canonical_label=item["canonical_label"],
                subject_form=item["subject_form"],
                identity_status=item["identity_status"],
                canonical_subject_fingerprint=item[
                    "canonical_subject_fingerprint"
                ],
                canonical_subject_set_fingerprint=item[
                    "canonical_subject_set_fingerprint"
                ],
                subject_consensus_fingerprint=item[
                    "subject_consensus_fingerprint"
                ],
                project_fit_fingerprint=item["project_fit_fingerprint"],
                mention_evidence=mention_evidence,
                statement_evidence=statement_evidence,
                field_evidence=field_evidence,
                source_review_attention_required=item[
                    "source_review_attention_required"
                ],
                content_fingerprint=item["content_fingerprint"],
            )
        )

    relations = tuple(
        ProjectSemanticRelation(
            left_subject_ref=item["left_subject_ref"],
            right_subject_ref=item["right_subject_ref"],
            outcome=item["outcome"],
            rationale=item["rationale"],
            shared_concepts=tuple(item["shared_concepts"]),
            material_differences=tuple(item["material_differences"]),
        )
        for item in _checked_items(
            raw["relations"],
            ProjectSemanticRelation,
            "Project Semantic relation",
        )
    )

    value = ProjectSemanticReconciliationArtifact(
        schema_version=raw["schema_version"],
        project_id=raw["project_id"],
        source_ids=tuple(raw["source_ids"]),
        subjects=tuple(subjects),
        relations=relations,
        unmatched_subject_refs=tuple(raw["unmatched_subject_refs"]),
        prompt_schema_version=raw["prompt_schema_version"],
        llm_provider=raw["llm_provider"],
        llm_model=raw["llm_model"],
        llm_response_id=raw["llm_response_id"],
        input_fingerprint=raw["input_fingerprint"],
        human_review_required=raw["human_review_required"],
        content_fingerprint=raw["content_fingerprint"],
    )
    validate_project_semantic_reconciliation_artifact(value)
    return value


def project_authority_decision_to_json(
    value: ProjectAuthorityDecision,
    reconciliation: ProjectSemanticReconciliationArtifact,
    bindings: tuple[ProjectAuthoritySubjectBinding, ...],
) -> str:
    validate_project_authority_decision(
        value,
        reconciliation,
        bindings,
    )
    return _json(asdict(value))


def project_authority_decision_from_json(
    text: str,
    reconciliation: ProjectSemanticReconciliationArtifact,
    bindings: tuple[ProjectAuthoritySubjectBinding, ...],
) -> ProjectAuthorityDecision:
    raw = _object(text, "Project Authority Decision")
    _exact_fields(raw, ProjectAuthorityDecision, "Project Authority Decision")
    value = ProjectAuthorityDecision(
        schema_version=raw["schema_version"],
        project_id=raw["project_id"],
        decision_id=raw["decision_id"],
        reconciliation_fingerprint=raw["reconciliation_fingerprint"],
        relation_fingerprint=raw["relation_fingerprint"],
        left_subject_ref=raw["left_subject_ref"],
        right_subject_ref=raw["right_subject_ref"],
        machine_relation_outcome=raw["machine_relation_outcome"],
        outcome=raw["outcome"],
        authority_concern_id=raw["authority_concern_id"],
        retained_approved_input_ids=tuple(
            raw["retained_approved_input_ids"]
        ),
        project_superseded_approved_input_ids=tuple(
            raw["project_superseded_approved_input_ids"]
        ),
        reviewer_identity=raw["reviewer_identity"],
        rationale=raw["rationale"],
        decided_at=raw["decided_at"],
        decision_fingerprint=raw["decision_fingerprint"],
    )
    validate_project_authority_decision(
        value,
        reconciliation,
        bindings,
    )
    return value


def project_engineering_authority_state_from_json(
    text: str,
) -> ProjectEngineeringAuthorityState:
    raw = _object(text, "Project Engineering Authority State")
    _exact_fields(
        raw,
        ProjectEngineeringAuthorityState,
        "Project Engineering Authority State",
    )
    bindings = tuple(
        _construct_exact(
            ProjectAuthoritySubjectBinding,
            item,
            "Project Authority Subject Binding",
        )
        for item in _list(raw["bindings"], "bindings")
    )
    decisions = tuple(
        ProjectAuthorityDecision(
            schema_version=item["schema_version"],
            project_id=item["project_id"],
            decision_id=item["decision_id"],
            reconciliation_fingerprint=item[
                "reconciliation_fingerprint"
            ],
            relation_fingerprint=item["relation_fingerprint"],
            left_subject_ref=item["left_subject_ref"],
            right_subject_ref=item["right_subject_ref"],
            machine_relation_outcome=item["machine_relation_outcome"],
            outcome=item["outcome"],
            authority_concern_id=item["authority_concern_id"],
            retained_approved_input_ids=tuple(
                item["retained_approved_input_ids"]
            ),
            project_superseded_approved_input_ids=tuple(
                item["project_superseded_approved_input_ids"]
            ),
            reviewer_identity=item["reviewer_identity"],
            rationale=item["rationale"],
            decided_at=item["decided_at"],
            decision_fingerprint=item["decision_fingerprint"],
        )
        for item in _checked_items(
            raw["decisions"],
            ProjectAuthorityDecision,
            "Project Authority Decision",
        )
    )
    entries = tuple(
        ProjectAuthorityEntry(
            approved_input_id=item["approved_input_id"],
            source_id=item["source_id"],
            subject_refs=tuple(item["subject_refs"]),
            approved_input_fingerprint=item["approved_input_fingerprint"],
            stable_subject_key=item["stable_subject_key"],
            project_authority_state=item["project_authority_state"],
            authority_concern_ids=tuple(item["authority_concern_ids"]),
            decision_ids=tuple(item["decision_ids"]),
            content_fingerprint=item["content_fingerprint"],
        )
        for item in _checked_items(
            raw["entries"],
            ProjectAuthorityEntry,
            "Project Authority Entry",
        )
    )
    value = ProjectEngineeringAuthorityState(
        schema_version=raw["schema_version"],
        project_id=raw["project_id"],
        reconciliation_fingerprint=raw["reconciliation_fingerprint"],
        bindings=bindings,
        decisions=decisions,
        entries=entries,
        unresolved_decision_ids=tuple(raw["unresolved_decision_ids"]),
        model_impact_ready=raw["model_impact_ready"],
        content_fingerprint=raw["content_fingerprint"],
    )
    validate_project_engineering_authority_state(value)
    return value


def model_impact_reconciliation_from_json(
    text: str,
) -> ModelImpactReconciliationArtifact:
    raw = _object(text, "Model Impact Reconciliation")
    _exact_fields(
        raw,
        ModelImpactReconciliationArtifact,
        "Model Impact Reconciliation",
    )
    proposals = tuple(
        ModelImpactProposal(
            approved_input_id=item["approved_input_id"],
            source_id=item["source_id"],
            stable_subject_key=item["stable_subject_key"],
            project_authority_state=item["project_authority_state"],
            authority_concern_ids=tuple(item["authority_concern_ids"]),
            outcome=item["outcome"],
            current_model_element_ids=tuple(
                item["current_model_element_ids"]
            ),
            related_model_element_ids=tuple(
                item["related_model_element_ids"]
            ),
            impacted_relationship_ids=tuple(
                item["impacted_relationship_ids"]
            ),
            model_change_required=item["model_change_required"],
            rationale_code=item["rationale_code"],
            content_fingerprint=item["content_fingerprint"],
        )
        for item in _checked_items(
            raw["proposals"],
            ModelImpactProposal,
            "Model Impact Proposal",
        )
    )
    value = ModelImpactReconciliationArtifact(
        schema_version=raw["schema_version"],
        project_id=raw["project_id"],
        project_authority_fingerprint=raw[
            "project_authority_fingerprint"
        ],
        accepted_model_id=raw["accepted_model_id"],
        accepted_model_fingerprint=raw["accepted_model_fingerprint"],
        accepted_model_final_review_decision_id=raw[
            "accepted_model_final_review_decision_id"
        ],
        accepted_model_final_review_decision_fingerprint=raw[
            "accepted_model_final_review_decision_fingerprint"
        ],
        accepted_model_profile_id=raw["accepted_model_profile_id"],
        accepted_model_profile_version=raw[
            "accepted_model_profile_version"
        ],
        accepted_model_profile_fingerprint=raw[
            "accepted_model_profile_fingerprint"
        ],
        proposals=proposals,
        unaffected_model_element_ids=tuple(
            raw["unaffected_model_element_ids"]
        ),
        unaffected_model_relationship_ids=tuple(
            raw["unaffected_model_relationship_ids"]
        ),
        unresolved_approved_input_ids=tuple(
            raw["unresolved_approved_input_ids"]
        ),
        model_change_required=raw["model_change_required"],
        human_model_review_required=raw[
            "human_model_review_required"
        ],
        content_fingerprint=raw["content_fingerprint"],
    )
    validate_model_impact_reconciliation_artifact(value)
    return value


def create_cycle_manifest(
    *,
    project_id: str,
    reconciliation_cycle_id: str,
    source_ids: tuple[str, ...],
    project_fit_fingerprints: tuple[str, ...],
    semantic_reconciliation_fingerprint: str,
    created_at: str,
) -> ProjectReconciliationCycleManifest:
    body = {
        "schema_version": PROJECT_RECONCILIATION_CYCLE_SCHEMA_VERSION,
        "project_id": project_id,
        "reconciliation_cycle_id": reconciliation_cycle_id,
        "source_ids": source_ids,
        "project_fit_fingerprints": project_fit_fingerprints,
        "semantic_reconciliation_fingerprint": (
            semantic_reconciliation_fingerprint
        ),
        "created_at": created_at,
    }
    value = ProjectReconciliationCycleManifest(
        **body,
        content_fingerprint=_fingerprint(body),
    )
    validate_cycle_manifest(value)
    return value


def validate_cycle_manifest(
    value: ProjectReconciliationCycleManifest,
) -> None:
    if not isinstance(value, ProjectReconciliationCycleManifest):
        raise ProjectReconciliationPersistenceValidationError(
            "cycle manifest must use ProjectReconciliationCycleManifest."
        )
    if value.schema_version != PROJECT_RECONCILIATION_CYCLE_SCHEMA_VERSION:
        raise ProjectReconciliationPersistenceValidationError(
            "Unsupported Project Reconciliation cycle schema_version."
        )
    if not value.project_id:
        raise ProjectReconciliationPersistenceValidationError(
            "Project Reconciliation cycle requires project_id."
        )
    if _CYCLE_ID.fullmatch(value.reconciliation_cycle_id) is None:
        raise ProjectReconciliationPersistenceValidationError(
            "Project Reconciliation cycle ID is invalid."
        )
    if (
        not value.source_ids
        or value.source_ids != tuple(sorted(value.source_ids))
        or len(value.source_ids) != len(set(value.source_ids))
    ):
        raise ProjectReconciliationPersistenceValidationError(
            "Project Reconciliation source_ids must be sorted and unique."
        )
    if (
        not value.project_fit_fingerprints
        or value.project_fit_fingerprints
        != tuple(sorted(value.project_fit_fingerprints))
        or len(value.project_fit_fingerprints)
        != len(set(value.project_fit_fingerprints))
    ):
        raise ProjectReconciliationPersistenceValidationError(
            "Project Fit fingerprints must be sorted and unique."
        )
    for item in (
        *value.project_fit_fingerprints,
        value.semantic_reconciliation_fingerprint,
        value.content_fingerprint,
    ):
        _sha(item)
    if _TIMESTAMP.fullmatch(value.created_at) is None:
        raise ProjectReconciliationPersistenceValidationError(
            "Project Reconciliation created_at must be UTC ISO-8601."
        )
    body = {
        key: item
        for key, item in asdict(value).items()
        if key != "content_fingerprint"
    }
    if value.content_fingerprint != _fingerprint(body):
        raise ProjectReconciliationPersistenceIntegrityError(
            "Project Reconciliation cycle fingerprint is invalid."
        )


def cycle_manifest_to_json(
    value: ProjectReconciliationCycleManifest,
) -> str:
    validate_cycle_manifest(value)
    return _json(asdict(value))


def cycle_manifest_from_json(
    text: str,
) -> ProjectReconciliationCycleManifest:
    raw = _object(text, "Project Reconciliation cycle")
    _exact_fields(
        raw,
        ProjectReconciliationCycleManifest,
        "Project Reconciliation cycle",
    )
    value = ProjectReconciliationCycleManifest(
        schema_version=raw["schema_version"],
        project_id=raw["project_id"],
        reconciliation_cycle_id=raw["reconciliation_cycle_id"],
        source_ids=tuple(raw["source_ids"]),
        project_fit_fingerprints=tuple(
            raw["project_fit_fingerprints"]
        ),
        semantic_reconciliation_fingerprint=raw[
            "semantic_reconciliation_fingerprint"
        ],
        created_at=raw["created_at"],
        content_fingerprint=raw["content_fingerprint"],
    )
    validate_cycle_manifest(value)
    return value


def create_binding_snapshot(
    reconciliation: ProjectSemanticReconciliationArtifact,
    bindings: tuple[ProjectAuthoritySubjectBinding, ...],
) -> ProjectAuthorityBindingSnapshot:
    validate_project_semantic_reconciliation_artifact(reconciliation)
    normalized = _validate_bindings(reconciliation, bindings)
    body = {
        "schema_version": (
            PROJECT_AUTHORITY_BINDING_SNAPSHOT_SCHEMA_VERSION
        ),
        "project_id": reconciliation.project_id,
        "reconciliation_fingerprint": reconciliation.content_fingerprint,
        "bindings": normalized,
    }
    value = ProjectAuthorityBindingSnapshot(
        **body,
        content_fingerprint=_fingerprint(
            {
                **body,
                "bindings": [asdict(item) for item in normalized],
            }
        ),
    )
    validate_binding_snapshot(value, reconciliation)
    return value


def validate_binding_snapshot(
    value: ProjectAuthorityBindingSnapshot,
    reconciliation: ProjectSemanticReconciliationArtifact,
) -> None:
    if not isinstance(value, ProjectAuthorityBindingSnapshot):
        raise ProjectReconciliationPersistenceValidationError(
            "binding snapshot must use ProjectAuthorityBindingSnapshot."
        )
    validate_project_semantic_reconciliation_artifact(reconciliation)
    if (
        value.schema_version
        != PROJECT_AUTHORITY_BINDING_SNAPSHOT_SCHEMA_VERSION
    ):
        raise ProjectReconciliationPersistenceValidationError(
            "Unsupported Project Authority binding snapshot schema_version."
        )
    if (
        value.project_id != reconciliation.project_id
        or value.reconciliation_fingerprint
        != reconciliation.content_fingerprint
    ):
        raise ProjectReconciliationPersistenceIntegrityError(
            "Project Authority binding snapshot does not bind exact S3 evidence."
        )
    normalized = _validate_bindings(reconciliation, value.bindings)
    if normalized != value.bindings:
        raise ProjectReconciliationPersistenceIntegrityError(
            "Project Authority bindings are not deterministically ordered."
        )
    body = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "reconciliation_fingerprint": value.reconciliation_fingerprint,
        "bindings": [asdict(item) for item in value.bindings],
    }
    if value.content_fingerprint != _fingerprint(body):
        raise ProjectReconciliationPersistenceIntegrityError(
            "Project Authority binding snapshot fingerprint is invalid."
        )


def binding_snapshot_to_json(
    value: ProjectAuthorityBindingSnapshot,
    reconciliation: ProjectSemanticReconciliationArtifact,
) -> str:
    validate_binding_snapshot(value, reconciliation)
    return _json(asdict(value))


def binding_snapshot_from_json(
    text: str,
    reconciliation: ProjectSemanticReconciliationArtifact,
) -> ProjectAuthorityBindingSnapshot:
    raw = _object(text, "Project Authority binding snapshot")
    _exact_fields(
        raw,
        ProjectAuthorityBindingSnapshot,
        "Project Authority binding snapshot",
    )
    bindings = tuple(
        _construct_exact(
            ProjectAuthoritySubjectBinding,
            item,
            "Project Authority Subject Binding",
        )
        for item in _list(raw["bindings"], "bindings")
    )
    value = ProjectAuthorityBindingSnapshot(
        schema_version=raw["schema_version"],
        project_id=raw["project_id"],
        reconciliation_fingerprint=raw["reconciliation_fingerprint"],
        bindings=bindings,
        content_fingerprint=raw["content_fingerprint"],
    )
    validate_binding_snapshot(value, reconciliation)
    return value


def _validate_bindings(
    reconciliation: ProjectSemanticReconciliationArtifact,
    bindings: tuple[ProjectAuthoritySubjectBinding, ...],
) -> tuple[ProjectAuthoritySubjectBinding, ...]:
    if not isinstance(bindings, tuple) or not bindings:
        raise ProjectReconciliationPersistenceValidationError(
            "Project Authority bindings must be a non-empty tuple."
        )
    normalized = tuple(sorted(bindings, key=lambda item: item.subject_ref))
    if normalized != bindings:
        raise ProjectReconciliationPersistenceValidationError(
            "Project Authority bindings must use subject_ref order."
        )

    subject_by_ref = {
        subject.subject_ref: subject
        for subject in reconciliation.subjects
    }
    if tuple(item.subject_ref for item in bindings) != tuple(
        subject.subject_ref for subject in reconciliation.subjects
    ):
        raise ProjectReconciliationPersistenceIntegrityError(
            "Project Authority bindings must cover the exact S3 Subject set."
        )

    for binding in bindings:
        if not isinstance(binding, ProjectAuthoritySubjectBinding):
            raise ProjectReconciliationPersistenceValidationError(
                "Project Authority binding has invalid type."
            )
        subject = subject_by_ref.get(binding.subject_ref)
        if subject is None:
            raise ProjectReconciliationPersistenceIntegrityError(
                "Project Authority binding references unknown S3 Subject."
            )
        if (
            binding.source_id != subject.source_id
            or binding.canonical_subject_id
            != subject.canonical_subject_id
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Project Authority binding source-local Subject differs from S3."
            )
        body = {
            key: item
            for key, item in asdict(binding).items()
            if key != "content_fingerprint"
        }
        if binding.content_fingerprint != _fingerprint(body):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Project Authority binding fingerprint is invalid."
            )
    return normalized


def _checked_items(value, cls, label):
    items = _list(value, label)
    for item in items:
        _exact_fields(item, cls, label)
    return items


def _construct_exact(cls, raw, label):
    _exact_fields(raw, cls, label)
    return cls(**raw)


def _exact_fields(raw, cls, label):
    if not isinstance(raw, dict):
        raise ProjectReconciliationPersistenceValidationError(
            f"{label} must be a JSON object."
        )
    expected = {item.name for item in fields(cls)}
    if set(raw) != expected:
        raise ProjectReconciliationPersistenceValidationError(
            f"{label} fields do not match the exact contract."
        )


def _list(value, label):
    if not isinstance(value, list):
        raise ProjectReconciliationPersistenceValidationError(
            f"{label} must be a JSON array."
        )
    return value


def _object(text, label):
    try:
        raw = json.loads(text)
    except Exception as exc:
        raise ProjectReconciliationPersistenceValidationError(
            f"{label} JSON is invalid."
        ) from exc
    if not isinstance(raw, dict):
        raise ProjectReconciliationPersistenceValidationError(
            f"{label} JSON must contain one object."
        )
    return raw


def _json(payload):
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def _fingerprint(payload):
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _json_default(value):
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f"Unsupported fingerprint value: {type(value)!r}")


def _sha(value):
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ProjectReconciliationPersistenceValidationError(
            "Expected SHA-256 fingerprint."
        )
