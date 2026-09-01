"""ADR-032 transient Project Engineering Authority -> Phase-H handoff."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
import re
from typing import Any, TYPE_CHECKING

from modules.approved_engineering_information.projection import (
    APPROVED_ENGINEERING_INFORMATION_SCHEMA_VERSION,
    ApprovedEngineeringInformationSet,
)
from modules.approved_input.manifest import validate_approved_input_manifest
from modules.approved_input.types import ApprovedInputManifest
if TYPE_CHECKING:
    from modules.model_impact_reconciliation import (
        ModelImpactReconciliationArtifact,
    )
from modules.project_engineering_authority import (
    ProjectEngineeringAuthorityState,
    validate_project_engineering_authority_state,
)

from .errors import (
    ModelCandidateGenerationBlockedError,
    ModelCandidateIntegrityError,
    ModelCandidateReferenceError,
)
from .types import ModelCandidateGenerationProvenance


PROJECT_AUTHORITY_PHASE_H_HANDOFF_SCHEMA_VERSION = "1.0.0"
PROJECT_AUTHORITY_SUBJECT_KEY_MODES = frozenset(
    {"source_local", "source_scoped"}
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class ProjectAuthorityPhaseHAEIReference:
    source_id: str
    review_document_id: str
    review_document_version_id: str
    review_revision_id: str
    content_fingerprint: str
    reference_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProjectAuthorityPhaseHSubject:
    project_subject_ref: str
    canonical_subject_id: str
    approved_input_id: str
    approved_input_fingerprint: str
    source_id: str
    source_aei_fingerprint: str
    stable_subject_key: str
    phase_h_subject_key: str
    project_authority_state: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProjectAuthorityPhaseHRelationship:
    relationship_ref: str
    source_id: str
    source_aei_fingerprint: str
    relationship_decision_id: str
    relationship_decision_fingerprint: str
    source_subject_ref: str
    source_approved_input_id: str
    source_phase_h_subject_key: str
    relationship_kind: str
    target_subject_ref: str
    target_approved_input_id: str
    target_phase_h_subject_key: str
    rationale: str | None
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProjectAuthorityPhaseHNonProjectableRelationship:
    relationship_ref: str
    source_id: str
    source_aei_fingerprint: str
    relationship_decision_id: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProjectAuthorityPhaseHHandoff:
    schema_version: str
    project_id: str
    project_authority_fingerprint: str
    model_impact_fingerprint: str
    source_aei_references: tuple[ProjectAuthorityPhaseHAEIReference, ...]
    subject_key_mode: str
    subjects: tuple[ProjectAuthorityPhaseHSubject, ...]
    relationships: tuple[ProjectAuthorityPhaseHRelationship, ...]
    non_projectable_relationships: tuple[
        ProjectAuthorityPhaseHNonProjectableRelationship, ...
    ]
    content_fingerprint: str


def create_project_authority_phase_h_handoff(
    *,
    project_authority: ProjectEngineeringAuthorityState,
    model_impact: ModelImpactReconciliationArtifact,
    approved_input_manifests: tuple[ApprovedInputManifest, ...],
    approved_engineering_information_sets: tuple[
        ApprovedEngineeringInformationSet, ...
    ],
) -> ProjectAuthorityPhaseHHandoff:
    try:
        validate_project_engineering_authority_state(project_authority)
    except Exception as exc:
        raise ModelCandidateGenerationBlockedError(
            "Project Engineering Authority is invalid for Phase-H handoff."
        ) from exc
    from modules.model_impact_reconciliation import (
        validate_model_impact_reconciliation_artifact,
    )

    try:
        validate_model_impact_reconciliation_artifact(model_impact)
    except Exception as exc:
        raise ModelCandidateGenerationBlockedError(
            "Model Impact Reconciliation is invalid for Phase-H handoff."
        ) from exc

    if not project_authority.model_impact_ready:
        raise ModelCandidateGenerationBlockedError(
            "Unresolved Project Engineering Authority cannot enter Phase H."
        )
    if model_impact.project_id != project_authority.project_id:
        raise ModelCandidateReferenceError(
            "Model Impact Reconciliation crosses the Project boundary."
        )
    if (
        model_impact.project_authority_fingerprint
        != project_authority.content_fingerprint
    ):
        raise ModelCandidateReferenceError(
            "Model Impact Reconciliation does not bind the exact Project "
            "Engineering Authority."
        )

    manifests = _manifest_snapshot(
        project_authority,
        approved_input_manifests,
    )
    aeis, aei_refs = _aei_snapshot(
        project_authority,
        approved_engineering_information_sets,
    )
    aei_by_fp = {item.content_fingerprint: item for item in aeis}

    bindings_by_ain = {}
    for binding in project_authority.bindings:
        bindings_by_ain.setdefault(
            binding.approved_input_id,
            [],
        ).append(binding)

    mode = (
        "source_scoped"
        if len({item.source_id for item in project_authority.entries}) > 1
        else "source_local"
    )

    subjects = []
    for entry in project_authority.entries:
        binding_values = tuple(
            bindings_by_ain.get(entry.approved_input_id, ())
        )
        if len(binding_values) != 1:
            raise ModelCandidateIntegrityError(
                "Phase-H requires one unambiguous S4 Subject binding per "
                "Approved Input."
            )
        binding = binding_values[0]
        manifest = manifests[entry.approved_input_id]
        aei = aei_by_fp.get(binding.aei_content_fingerprint)
        if aei is None:
            raise ModelCandidateReferenceError(
                "S4 references unavailable source-local AEI."
            )
        matches = tuple(
            item
            for item in aei.subjects
            if item.approved_input_id == entry.approved_input_id
        )
        if len(matches) != 1:
            raise ModelCandidateIntegrityError(
                "Source-local AEI Subject binding is ambiguous."
            )
        subject = matches[0]
        if (
            subject.canonical_subject_id != binding.canonical_subject_id
            or subject.stable_subject_key != manifest.stable_subject_key
            or subject.approved_input_fingerprint
            != manifest.content_fingerprint
        ):
            raise ModelCandidateReferenceError(
                "S4 / AEI / Approved Input Subject binding is stale."
            )

        body = {
            "project_subject_ref": binding.subject_ref,
            "canonical_subject_id": binding.canonical_subject_id,
            "approved_input_id": manifest.approved_input_id,
            "approved_input_fingerprint": manifest.content_fingerprint,
            "source_id": manifest.source_id,
            "source_aei_fingerprint": aei.content_fingerprint,
            "stable_subject_key": manifest.stable_subject_key,
            "phase_h_subject_key": _subject_key(
                manifest.source_id,
                manifest.stable_subject_key,
                mode,
            ),
            "project_authority_state": entry.project_authority_state,
        }
        subjects.append(
            ProjectAuthorityPhaseHSubject(
                **body,
                content_fingerprint=_fingerprint(body),
            )
        )

    subjects = tuple(
        sorted(subjects, key=lambda item: item.approved_input_id)
    )
    subject_by_endpoint = {
        (item.source_aei_fingerprint, item.canonical_subject_id): item
        for item in subjects
    }
    if len(subject_by_endpoint) != len(subjects):
        raise ModelCandidateIntegrityError(
            "Project Phase-H Subject identity is ambiguous."
        )

    active_ids = {
        item.approved_input_id
        for item in subjects
        if item.project_authority_state == "active"
    }

    relationships = []
    non_projectable = []
    project_relationship_refs = set()

    for aei in aeis:
        source_id = aei_refs[aei.content_fingerprint].source_id
        decision_ids = tuple(
            item.relationship_decision_id
            for item in aei.relationships
        )
        if len(decision_ids) != len(set(decision_ids)):
            raise ModelCandidateIntegrityError(
                "Source-local AEI contains duplicate Relationship IDs."
            )

        for relationship in aei.relationships:
            source = subject_by_endpoint.get(
                (
                    aei.content_fingerprint,
                    relationship.source_subject_id,
                )
            )
            target = subject_by_endpoint.get(
                (
                    aei.content_fingerprint,
                    relationship.target_subject_id,
                )
            )
            if source is None or target is None:
                raise ModelCandidateReferenceError(
                    "AEI Relationship endpoint is outside S4 authority."
                )

            # Source-local evidence remains immutable. A Relationship touching
            # project-superseded information is simply not current Project
            # Model authority.
            if (
                source.approved_input_id not in active_ids
                or target.approved_input_id not in active_ids
            ):
                continue

            relationship_ref = _relationship_ref(
                source_id,
                aei.review_document_id,
                relationship.relationship_decision_id,
            )
            if relationship_ref in project_relationship_refs:
                raise ModelCandidateIntegrityError(
                    "Project Relationship identity is not unique."
                )
            project_relationship_refs.add(relationship_ref)

            body = {
                "relationship_ref": relationship_ref,
                "source_id": source_id,
                "source_aei_fingerprint": aei.content_fingerprint,
                "relationship_decision_id": (
                    relationship.relationship_decision_id
                ),
                "relationship_decision_fingerprint": (
                    relationship.relationship_decision_fingerprint
                ),
                "source_subject_ref": source.project_subject_ref,
                "source_approved_input_id": source.approved_input_id,
                "source_phase_h_subject_key": source.phase_h_subject_key,
                "relationship_kind": relationship.relationship_kind,
                "target_subject_ref": target.project_subject_ref,
                "target_approved_input_id": target.approved_input_id,
                "target_phase_h_subject_key": target.phase_h_subject_key,
                "rationale": relationship.rationale,
            }
            relationships.append(
                ProjectAuthorityPhaseHRelationship(
                    **body,
                    content_fingerprint=_fingerprint(body),
                )
            )

        non_projectable_ids = tuple(
            aei.non_projectable_relationship_decision_ids
        )
        if len(non_projectable_ids) != len(set(non_projectable_ids)):
            raise ModelCandidateIntegrityError(
                "Source-local AEI contains duplicate non-projectable "
                "Relationship IDs."
            )
        for relationship_decision_id in non_projectable_ids:
            relationship_ref = _relationship_ref(
                source_id,
                aei.review_document_id,
                relationship_decision_id,
            )
            if relationship_ref in project_relationship_refs:
                raise ModelCandidateIntegrityError(
                    "Project Relationship identity collision."
                )
            project_relationship_refs.add(relationship_ref)
            body = {
                "relationship_ref": relationship_ref,
                "source_id": source_id,
                "source_aei_fingerprint": aei.content_fingerprint,
                "relationship_decision_id": relationship_decision_id,
            }
            non_projectable.append(
                ProjectAuthorityPhaseHNonProjectableRelationship(
                    **body,
                    content_fingerprint=_fingerprint(body),
                )
            )

    body = {
        "schema_version": PROJECT_AUTHORITY_PHASE_H_HANDOFF_SCHEMA_VERSION,
        "project_id": project_authority.project_id,
        "project_authority_fingerprint": (
            project_authority.content_fingerprint
        ),
        "model_impact_fingerprint": model_impact.content_fingerprint,
        "source_aei_references": tuple(
            sorted(
                aei_refs.values(),
                key=lambda item: (
                    item.source_id,
                    item.review_document_id,
                    item.review_document_version_id,
                    item.content_fingerprint,
                ),
            )
        ),
        "subject_key_mode": mode,
        "subjects": subjects,
        "relationships": tuple(
            sorted(
                relationships,
                key=lambda item: item.relationship_ref,
            )
        ),
        "non_projectable_relationships": tuple(
            sorted(
                non_projectable,
                key=lambda item: item.relationship_ref,
            )
        ),
    }
    handoff = ProjectAuthorityPhaseHHandoff(
        **body,
        content_fingerprint=_fingerprint(body),
    )
    validate_project_authority_phase_h_handoff(handoff)
    return handoff


def validate_project_authority_phase_h_handoff(
    handoff: ProjectAuthorityPhaseHHandoff,
) -> None:
    if not isinstance(handoff, ProjectAuthorityPhaseHHandoff):
        raise ModelCandidateReferenceError(
            "Invalid Project Authority Phase-H handoff."
        )
    if (
        handoff.schema_version
        != PROJECT_AUTHORITY_PHASE_H_HANDOFF_SCHEMA_VERSION
    ):
        raise ModelCandidateReferenceError(
            "Unsupported Project Authority handoff schema_version."
        )
    if handoff.subject_key_mode not in PROJECT_AUTHORITY_SUBJECT_KEY_MODES:
        raise ModelCandidateReferenceError(
            "Invalid Project Authority Subject identity mode."
        )
    _required_text(handoff.project_id, "project_id")
    _validate_sha(
        handoff.project_authority_fingerprint,
        "project_authority_fingerprint",
    )
    _validate_sha(
        handoff.model_impact_fingerprint,
        "model_impact_fingerprint",
    )
    if not handoff.source_aei_references or not handoff.subjects:
        raise ModelCandidateReferenceError(
            "Project Authority handoff requires AEI references and Subjects."
        )

    aei_fingerprints = set()
    aei_sources = set()
    for item in handoff.source_aei_references:
        for label, value in (
            ("source_id", item.source_id),
            ("review_document_id", item.review_document_id),
            (
                "review_document_version_id",
                item.review_document_version_id,
            ),
            ("review_revision_id", item.review_revision_id),
        ):
            _required_text(value, label)
        _validate_sha(
            item.content_fingerprint,
            "AEI content_fingerprint",
        )
        _validate_sha(
            item.reference_fingerprint,
            "AEI reference_fingerprint",
        )
        payload = {
            key: value
            for key, value in asdict(item).items()
            if key != "reference_fingerprint"
        }
        if item.reference_fingerprint != _fingerprint(payload):
            raise ModelCandidateIntegrityError(
                "AEI reference fingerprint mismatch."
            )
        if item.content_fingerprint in aei_fingerprints:
            raise ModelCandidateIntegrityError(
                "Source-local AEI fingerprints must be unique."
            )
        aei_fingerprints.add(item.content_fingerprint)
        aei_sources.add(item.source_id)

    approved_input_ids = []
    active_subject_keys = []
    subject_by_ref = {}
    for item in handoff.subjects:
        if item.project_authority_state not in {"active", "superseded"}:
            raise ModelCandidateIntegrityError(
                "Unresolved Project Authority cannot enter Phase H."
            )
        _validate_sha(
            item.approved_input_fingerprint,
            "approved_input_fingerprint",
        )
        _validate_sha(
            item.source_aei_fingerprint,
            "source_aei_fingerprint",
        )
        _validate_sha(
            item.content_fingerprint,
            "Subject content_fingerprint",
        )
        if item.source_aei_fingerprint not in aei_fingerprints:
            raise ModelCandidateReferenceError(
                "Phase-H Subject references unavailable source-local AEI."
            )
        expected_key = _subject_key(
            item.source_id,
            item.stable_subject_key,
            handoff.subject_key_mode,
        )
        if item.phase_h_subject_key != expected_key:
            raise ModelCandidateIntegrityError(
                "Phase-H Subject key violates handoff identity mode."
            )
        payload = {
            key: value
            for key, value in asdict(item).items()
            if key != "content_fingerprint"
        }
        if item.content_fingerprint != _fingerprint(payload):
            raise ModelCandidateIntegrityError(
                "Phase-H Subject fingerprint mismatch."
            )
        approved_input_ids.append(item.approved_input_id)
        subject_by_ref[item.project_subject_ref] = item
        if item.project_authority_state == "active":
            active_subject_keys.append(item.phase_h_subject_key)

    if len(approved_input_ids) != len(set(approved_input_ids)):
        raise ModelCandidateIntegrityError(
            "Duplicate Approved Input identity in handoff."
        )
    if not active_subject_keys:
        raise ModelCandidateGenerationBlockedError(
            "Project Authority handoff has no active engineering authority."
        )
    if len(active_subject_keys) != len(set(active_subject_keys)):
        raise ModelCandidateIntegrityError(
            "Active Project Model Subject identity is ambiguous."
        )
    if (
        handoff.subject_key_mode == "source_local"
        and len(aei_sources) > 1
    ):
        raise ModelCandidateIntegrityError(
            "Multi-source handoff must use source-scoped Subject identity."
        )

    relationship_refs = set()
    for item in handoff.relationships:
        if item.relationship_ref in relationship_refs:
            raise ModelCandidateIntegrityError(
                "Project Relationship refs must be unique."
            )
        relationship_refs.add(item.relationship_ref)
        _validate_sha(
            item.relationship_decision_fingerprint,
            "relationship_decision_fingerprint",
        )
        _validate_sha(
            item.source_aei_fingerprint,
            "source_aei_fingerprint",
        )
        _validate_sha(
            item.content_fingerprint,
            "Relationship content_fingerprint",
        )
        source = subject_by_ref.get(item.source_subject_ref)
        target = subject_by_ref.get(item.target_subject_ref)
        if source is None or target is None:
            raise ModelCandidateReferenceError(
                "Project Relationship endpoint is unavailable."
            )
        if (
            source.project_authority_state != "active"
            or target.project_authority_state != "active"
        ):
            raise ModelCandidateIntegrityError(
                "Project Relationship touches non-active authority."
            )
        if (
            item.source_id != source.source_id
            or item.source_id != target.source_id
            or item.source_aei_fingerprint
            != source.source_aei_fingerprint
            or item.source_aei_fingerprint
            != target.source_aei_fingerprint
        ):
            raise ModelCandidateIntegrityError(
                "Source-local Relationship crosses source/AEI boundary."
            )
        if (
            item.source_approved_input_id != source.approved_input_id
            or item.target_approved_input_id != target.approved_input_id
            or item.source_phase_h_subject_key
            != source.phase_h_subject_key
            or item.target_phase_h_subject_key
            != target.phase_h_subject_key
        ):
            raise ModelCandidateIntegrityError(
                "Project Relationship endpoint binding is inconsistent."
            )
        payload = {
            key: value
            for key, value in asdict(item).items()
            if key != "content_fingerprint"
        }
        if item.content_fingerprint != _fingerprint(payload):
            raise ModelCandidateIntegrityError(
                "Project Relationship fingerprint mismatch."
            )

    for item in handoff.non_projectable_relationships:
        if item.relationship_ref in relationship_refs:
            raise ModelCandidateIntegrityError(
                "Project Relationship ref collision."
            )
        relationship_refs.add(item.relationship_ref)
        _validate_sha(
            item.source_aei_fingerprint,
            "source_aei_fingerprint",
        )
        _validate_sha(item.content_fingerprint, "content_fingerprint")
        payload = {
            key: value
            for key, value in asdict(item).items()
            if key != "content_fingerprint"
        }
        if item.content_fingerprint != _fingerprint(payload):
            raise ModelCandidateIntegrityError(
                "Non-projectable Relationship fingerprint mismatch."
            )

    _validate_sha(handoff.content_fingerprint, "content_fingerprint")
    body = {
        key: value
        for key, value in asdict(handoff).items()
        if key != "content_fingerprint"
    }
    if handoff.content_fingerprint != _fingerprint(body):
        raise ModelCandidateIntegrityError(
            "Project Authority handoff fingerprint mismatch."
        )


def select_project_authority_active_inputs(
    values: tuple[ApprovedInputManifest, ...],
    handoff: ProjectAuthorityPhaseHHandoff,
) -> tuple[ApprovedInputManifest, ...]:
    validate_project_authority_phase_h_handoff(handoff)
    if not isinstance(values, tuple):
        raise ModelCandidateGenerationBlockedError(
            "Approved Input snapshot must be a tuple."
        )

    by_id = {}
    for manifest in values:
        try:
            validate_approved_input_manifest(manifest)
        except Exception as exc:
            raise ModelCandidateGenerationBlockedError(
                "Approved Input snapshot contains invalid authority."
            ) from exc
        if manifest.approved_input_id in by_id:
            raise ModelCandidateIntegrityError(
                "Approved Input snapshot contains duplicate identities."
            )
        by_id[manifest.approved_input_id] = manifest

    expected = {
        item.approved_input_id: item
        for item in handoff.subjects
    }
    if set(by_id) != set(expected):
        raise ModelCandidateGenerationBlockedError(
            "Source-local active Approved Input snapshot does not match "
            "the exact S4 authority population."
        )

    for approved_input_id, subject in expected.items():
        manifest = by_id[approved_input_id]
        if (
            manifest.project_id != handoff.project_id
            or manifest.content_fingerprint
            != subject.approved_input_fingerprint
            or manifest.source_id != subject.source_id
            or manifest.stable_subject_key != subject.stable_subject_key
        ):
            raise ModelCandidateReferenceError(
                "Project Authority Approved Input binding is stale."
            )

    return tuple(
        sorted(
            (
                by_id[item.approved_input_id]
                for item in handoff.subjects
                if item.project_authority_state == "active"
            ),
            key=lambda item: item.approved_input_id,
        )
    )


def validate_project_authority_phase_h_request(request) -> None:
    handoff = getattr(request, "project_authority_handoff", None)
    if handoff is None:
        return
    validate_project_authority_phase_h_handoff(handoff)
    if request.project_id != handoff.project_id:
        raise ModelCandidateReferenceError(
            "Phase-H request crosses Project Authority boundary."
        )
    if request.approved_engineering_information is not None:
        raise ModelCandidateReferenceError(
            "Project Authority Phase-H request must not attach one synthetic "
            "merged ApprovedEngineeringInformationSet."
        )

    expected = {
        item.approved_input_id: item
        for item in handoff.subjects
        if item.project_authority_state == "active"
    }
    actual = {
        item.approved_input_id: item
        for item in request.approved_inputs
    }
    if set(actual) != set(expected):
        raise ModelCandidateReferenceError(
            "Phase-H request does not contain the exact active Project "
            "Engineering Authority population."
        )
    for approved_input_id, subject in expected.items():
        manifest = actual[approved_input_id]
        if (
            manifest.content_fingerprint
            != subject.approved_input_fingerprint
            or manifest.source_id != subject.source_id
            or manifest.stable_subject_key != subject.stable_subject_key
        ):
            raise ModelCandidateReferenceError(
                "Phase-H Approved Input authority binding is stale."
            )


def phase_h_subject_key(
    request,
    approved_input: ApprovedInputManifest,
) -> str:
    handoff = getattr(request, "project_authority_handoff", None)
    fit_handoff = getattr(request, "project_fit_handoff", None)

    if handoff is not None and fit_handoff is not None:
        raise ModelCandidateReferenceError(
            "Project Authority and Project Fit Phase-H handoffs are "
            "mutually exclusive."
        )

    if fit_handoff is not None:
        from .project_fit_handoff import (
            project_fit_phase_h_subject_key,
        )
        return project_fit_phase_h_subject_key(
            request,
            approved_input,
        )

    if handoff is None:
        return approved_input.stable_subject_key

    validate_project_authority_phase_h_request(request)
    matches = tuple(
        item
        for item in handoff.subjects
        if (
            item.project_authority_state == "active"
            and item.approved_input_id == approved_input.approved_input_id
        )
    )
    if len(matches) != 1:
        raise ModelCandidateReferenceError(
            "Approved Input has no unique active Project Authority Subject."
        )
    return matches[0].phase_h_subject_key


def phase_h_subject_key_for_source(
    request,
    *,
    source_id: str,
    stable_subject_key: str,
) -> str:
    handoff = getattr(request, "project_authority_handoff", None)
    fit_handoff = getattr(request, "project_fit_handoff", None)

    if handoff is not None and fit_handoff is not None:
        raise ModelCandidateReferenceError(
            "Project Authority and Project Fit Phase-H handoffs are "
            "mutually exclusive."
        )

    if fit_handoff is not None:
        from .project_fit_handoff import (
            project_fit_phase_h_subject_key_for_source,
        )
        return project_fit_phase_h_subject_key_for_source(
            request,
            source_id=source_id,
            stable_subject_key=stable_subject_key,
        )

    if handoff is None:
        return stable_subject_key

    validate_project_authority_phase_h_request(request)
    matches = tuple(
        item
        for item in handoff.subjects
        if (
            item.project_authority_state == "active"
            and item.source_id == source_id
            and item.stable_subject_key == stable_subject_key
        )
    )
    if len(matches) != 1:
        raise ModelCandidateReferenceError(
            "Source-local Subject key is not uniquely project-resolvable."
        )
    return matches[0].phase_h_subject_key


def bind_generation_provenance_to_project_authority_handoff(
    provenance: ModelCandidateGenerationProvenance,
    handoff: ProjectAuthorityPhaseHHandoff | None,
) -> ModelCandidateGenerationProvenance:
    if handoff is None:
        return provenance
    validate_project_authority_phase_h_handoff(handoff)
    if not isinstance(provenance, ModelCandidateGenerationProvenance):
        raise ModelCandidateReferenceError(
            "Generation provenance has invalid type."
        )
    body = {
        "base_context_fingerprint": provenance.context_fingerprint,
        "project_authority_handoff_fingerprint": (
            handoff.content_fingerprint
        ),
        "project_engineering_authority_fingerprint": (
            handoff.project_authority_fingerprint
        ),
        "model_impact_reconciliation_fingerprint": (
            handoff.model_impact_fingerprint
        ),
        "source_approved_engineering_information_fingerprints": [
            item.content_fingerprint
            for item in handoff.source_aei_references
        ],
    }
    return replace(
        provenance,
        context_fingerprint=_fingerprint(body),
    )


def _manifest_snapshot(authority, values):
    if not isinstance(values, tuple):
        raise ModelCandidateGenerationBlockedError(
            "approved_input_manifests must be a tuple."
        )
    by_id = {}
    for item in values:
        try:
            validate_approved_input_manifest(item)
        except Exception as exc:
            raise ModelCandidateGenerationBlockedError(
                "Invalid source-local Approved Input authority."
            ) from exc
        if item.approved_input_id in by_id:
            raise ModelCandidateIntegrityError(
                "Duplicate Approved Input identity."
            )
        by_id[item.approved_input_id] = item

    expected = {
        item.approved_input_id: item
        for item in authority.entries
    }
    if set(by_id) != set(expected):
        raise ModelCandidateGenerationBlockedError(
            "S4 does not bind the exact source-local active Approved Input "
            "snapshot."
        )
    for approved_input_id, entry in expected.items():
        item = by_id[approved_input_id]
        if (
            item.project_id != authority.project_id
            or item.source_id != entry.source_id
            or item.content_fingerprint
            != entry.approved_input_fingerprint
            or item.stable_subject_key != entry.stable_subject_key
        ):
            raise ModelCandidateReferenceError(
                "Stale S4 Approved Input binding."
            )
    return by_id


def _aei_snapshot(authority, values):
    if not isinstance(values, tuple) or not values:
        raise ModelCandidateGenerationBlockedError(
            "Source-local Approved Engineering Information sets are required."
        )

    expected = {
        item.aei_content_fingerprint
        for item in authority.bindings
    }
    by_fingerprint = {}
    references = {}

    for item in values:
        _validate_aei(item)
        if item.project_id != authority.project_id:
            raise ModelCandidateReferenceError(
                "Source-local AEI crosses the Project boundary."
            )
        if item.content_fingerprint in by_fingerprint:
            raise ModelCandidateIntegrityError(
                "Duplicate source-local AEI fingerprint."
            )

        related = tuple(
            binding
            for binding in authority.bindings
            if (
                binding.aei_content_fingerprint
                == item.content_fingerprint
            )
        )
        if not related:
            raise ModelCandidateReferenceError(
                "Provided AEI is outside S4 authority."
            )
        sources = {binding.source_id for binding in related}
        if len(sources) != 1:
            raise ModelCandidateIntegrityError(
                "One source-local AEI cannot represent multiple Sources."
            )
        for binding in related:
            if (
                binding.review_document_id != item.review_document_id
                or binding.review_document_version_id
                != item.review_document_version_id
                or binding.review_revision_id
                != item.review_revision_id
            ):
                raise ModelCandidateReferenceError(
                    "Stale S4 AEI Review authority binding."
                )

        source_id = next(iter(sources))
        body = {
            "source_id": source_id,
            "review_document_id": item.review_document_id,
            "review_document_version_id": (
                item.review_document_version_id
            ),
            "review_revision_id": item.review_revision_id,
            "content_fingerprint": item.content_fingerprint,
        }
        references[item.content_fingerprint] = (
            ProjectAuthorityPhaseHAEIReference(
                **body,
                reference_fingerprint=_fingerprint(body),
            )
        )
        by_fingerprint[item.content_fingerprint] = item

    if set(by_fingerprint) != expected:
        raise ModelCandidateGenerationBlockedError(
            "Phase-H handoff AEI population does not match S4."
        )

    return (
        tuple(
            sorted(
                by_fingerprint.values(),
                key=lambda item: (
                    references[item.content_fingerprint].source_id,
                    item.review_document_id,
                    item.review_document_version_id,
                    item.content_fingerprint,
                ),
            )
        ),
        references,
    )


def _validate_aei(value):
    if (
        not isinstance(value, ApprovedEngineeringInformationSet)
        or value.schema_version
        != APPROVED_ENGINEERING_INFORMATION_SCHEMA_VERSION
    ):
        raise ModelCandidateReferenceError(
            "Invalid source-local Approved Engineering Information."
        )
    body = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "review_document_id": value.review_document_id,
        "review_document_version_id": value.review_document_version_id,
        "review_revision_id": value.review_revision_id,
        "subjects": [asdict(item) for item in value.subjects],
        "relationships": [
            asdict(item) for item in value.relationships
        ],
        "non_promotable_subject_ids": list(
            value.non_promotable_subject_ids
        ),
        "non_projectable_relationship_decision_ids": list(
            value.non_projectable_relationship_decision_ids
        ),
        "relationship_decision_authority_fingerprint": (
            value.relationship_decision_authority_fingerprint
        ),
    }
    if value.content_fingerprint != _fingerprint(body):
        raise ModelCandidateIntegrityError(
            "Approved Engineering Information fingerprint mismatch."
        )


def _subject_key(source_id, stable_subject_key, mode):
    if mode == "source_local":
        return stable_subject_key
    if mode == "source_scoped":
        # Phase-H stable-subject-key syntax is intentionally lowercase.
        # Preserve the canonical Source ID separately in provenance and use
        # a deterministic lowercase encoding only for the persisted Model
        # Subject key.
        return (
            f"project_subject:{source_id.lower()}:{stable_subject_key}"
        )
    raise ModelCandidateReferenceError(
        "Unsupported Project Model Subject identity mode."
    )


def _relationship_ref(
    source_id,
    review_document_id,
    relationship_decision_id,
):
    return (
        f"project_relationship:{source_id}:"
        f"{review_document_id}:{relationship_decision_id}"
    )


def _required_text(value, label):
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
    ):
        raise ModelCandidateReferenceError(
            f"{label} must be a non-empty trimmed string."
        )
    return value


def _validate_sha(value, label):
    if (
        not isinstance(value, str)
        or _SHA256.fullmatch(value) is None
    ):
        raise ModelCandidateReferenceError(
            f"{label} must be a lowercase SHA-256 string."
        )
    return value


def _jsonable(value: Any):
    if isinstance(value, dict):
        return {
            key: _jsonable(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return _jsonable(asdict(value))
    return value


def _fingerprint(value):
    return sha256(
        json.dumps(
            _jsonable(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
