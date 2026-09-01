"""ADR-032 S4 project-level Engineering Authority reconciliation contract."""

from __future__ import annotations

from dataclasses import asdict, replace
from hashlib import sha256
import json
import re
from typing import Any

from modules.approved_engineering_information.projection import (
    APPROVED_ENGINEERING_INFORMATION_SCHEMA_VERSION,
    ApprovedEngineeringInformationSet,
)
from modules.approved_input.lifecycle import (
    derive_approved_input_authority_states,
)
from modules.approved_input.manifest import validate_approved_input_manifest
from modules.approved_input.types import ApprovedInputManifest
from modules.project_semantic_reconciliation import (
    ProjectSemanticReconciliationArtifact,
    validate_project_semantic_reconciliation_artifact,
)

from .errors import (
    ProjectEngineeringAuthorityIntegrityError,
    ProjectEngineeringAuthorityValidationError,
)
from .types import (
    PROJECT_AUTHORITY_DECISION_OUTCOMES,
    PROJECT_AUTHORITY_STATES,
    ProjectAuthorityDecision,
    ProjectAuthorityEntry,
    ProjectAuthoritySubjectBinding,
    ProjectEngineeringAuthorityState,
)


PROJECT_ENGINEERING_AUTHORITY_SCHEMA_VERSION = "1.0.0"

_DECISION_ID = re.compile(r"^PEAD-([0-9]{6})$")
_CONCERN_ID = re.compile(r"^PEAC-([0-9]{6})$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_UTC_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)


def prepare_project_authority_bindings(
    reconciliation: ProjectSemanticReconciliationArtifact,
    approved_input_manifests: object,
    approved_input_events: object,
    approved_engineering_information: object,
) -> tuple[ProjectAuthoritySubjectBinding, ...]:
    """Bind every S3 Subject to exact current source-local Human authority."""

    validate_project_semantic_reconciliation_artifact(reconciliation)

    if not isinstance(approved_input_manifests, tuple):
        raise ProjectEngineeringAuthorityValidationError(
            "approved_input_manifests must be a tuple."
        )
    if not isinstance(approved_input_events, tuple):
        raise ProjectEngineeringAuthorityValidationError(
            "approved_input_events must be a tuple."
        )
    if not isinstance(approved_engineering_information, tuple):
        raise ProjectEngineeringAuthorityValidationError(
            "approved_engineering_information must be a tuple."
        )

    try:
        snapshots = derive_approved_input_authority_states(
            approved_input_manifests,
            approved_input_events,
        )
    except Exception as exc:
        raise ProjectEngineeringAuthorityValidationError(
            "Approved Input authority lifecycle is invalid."
        ) from exc

    active_by_id = {
        snapshot.manifest.approved_input_id: snapshot.manifest
        for snapshot in snapshots
        if snapshot.authority_state == "active"
    }
    all_by_id = {
        snapshot.manifest.approved_input_id: snapshot.manifest
        for snapshot in snapshots
    }

    authority_candidates: dict[
        tuple[str, str],
        tuple[ApprovedInputManifest, ApprovedEngineeringInformationSet],
    ] = {}

    for aei in approved_engineering_information:
        _validate_aei_set(aei)
        if aei.project_id != reconciliation.project_id:
            raise ProjectEngineeringAuthorityIntegrityError(
                "Approved Engineering Information crosses the Project boundary."
            )

        for subject in aei.subjects:
            manifest = all_by_id.get(subject.approved_input_id)
            if manifest is None:
                raise ProjectEngineeringAuthorityIntegrityError(
                    "AEI references an unavailable Approved Input."
                )
            if manifest.approved_input_id not in active_by_id:
                raise ProjectEngineeringAuthorityIntegrityError(
                    "AEI references an Approved Input that is not currently active."
                )
            _validate_aei_subject_binding(aei, subject, manifest)

            key = (manifest.source_id, subject.canonical_subject_id)
            existing = authority_candidates.get(key)
            if existing is not None:
                existing_manifest, _ = existing
                if (
                    existing_manifest.approved_input_id
                    != manifest.approved_input_id
                ):
                    raise ProjectEngineeringAuthorityIntegrityError(
                        "More than one active Approved Input is available for "
                        "the same source-local canonical Subject."
                    )
            authority_candidates[key] = (manifest, aei)

    bindings = []
    seen_approved_input_subject_pairs = set()
    for subject in reconciliation.subjects:
        candidate = authority_candidates.get(
            (subject.source_id, subject.canonical_subject_id)
        )
        if candidate is None:
            raise ProjectEngineeringAuthorityIntegrityError(
                "Every S3 Subject must resolve to current source-local "
                "Approved Engineering Information before S4."
            )

        manifest, aei = candidate
        pair = (manifest.approved_input_id, subject.subject_ref)
        if pair in seen_approved_input_subject_pairs:
            raise ProjectEngineeringAuthorityIntegrityError(
                "Duplicate S3 Subject to Approved Input binding."
            )
        seen_approved_input_subject_pairs.add(pair)

        body = {
            "subject_ref": subject.subject_ref,
            "canonical_subject_id": subject.canonical_subject_id,
            "source_id": subject.source_id,
            "approved_input_id": manifest.approved_input_id,
            "approved_input_fingerprint": manifest.content_fingerprint,
            "stable_subject_key": manifest.stable_subject_key,
            "review_document_id": manifest.review_document_id,
            "review_document_version_id": (
                manifest.review_document_version_id
            ),
            "review_revision_id": manifest.review_revision_id,
            "aei_content_fingerprint": aei.content_fingerprint,
        }
        bindings.append(
            ProjectAuthoritySubjectBinding(
                **body,
                content_fingerprint=_sha(body),
            )
        )

    normalized = tuple(
        sorted(bindings, key=lambda item: item.subject_ref)
    )
    _validate_bindings_against_reconciliation(
        reconciliation,
        normalized,
    )
    return normalized


def create_project_authority_decision(
    reconciliation: ProjectSemanticReconciliationArtifact,
    bindings: tuple[ProjectAuthoritySubjectBinding, ...],
    *,
    decision_id: str,
    left_subject_ref: str,
    right_subject_ref: str,
    outcome: str,
    reviewer_identity: str,
    rationale: str,
    decided_at: str,
    authority_concern_id: str | None = None,
    retained_approved_input_id: str | None = None,
) -> ProjectAuthorityDecision:
    """Create one explicit Human authority decision for one S3 relation."""

    validate_project_semantic_reconciliation_artifact(reconciliation)
    _validate_bindings_against_reconciliation(reconciliation, bindings)
    _validate_identifier(decision_id, _DECISION_ID, "decision_id")
    if outcome not in PROJECT_AUTHORITY_DECISION_OUTCOMES:
        raise ProjectEngineeringAuthorityValidationError(
            "Unsupported project authority decision outcome."
        )
    _required_text(reviewer_identity, "reviewer_identity")
    _required_text(rationale, "rationale")
    _validate_timestamp(decided_at)

    relation = _find_relation(
        reconciliation,
        left_subject_ref,
        right_subject_ref,
    )
    left_ref, right_ref = sorted(
        (relation.left_subject_ref, relation.right_subject_ref)
    )
    binding_by_ref = {
        item.subject_ref: item
        for item in bindings
    }
    participants = tuple(
        sorted(
            {
                binding_by_ref[left_ref].approved_input_id,
                binding_by_ref[right_ref].approved_input_id,
            }
        )
    )
    if len(participants) != 2:
        raise ProjectEngineeringAuthorityIntegrityError(
            "A cross-source authority decision must bind two distinct "
            "Approved Inputs."
        )

    concern = _normalize_optional_concern(authority_concern_id)

    if outcome in {"remain_independent", "unresolved"}:
        if concern is not None:
            raise ProjectEngineeringAuthorityValidationError(
                f"{outcome} must not establish an authority_concern_id."
            )
    else:
        if concern is None:
            raise ProjectEngineeringAuthorityValidationError(
                f"{outcome} requires an explicit Human authority_concern_id."
            )

    if outcome == "supersede":
        if retained_approved_input_id not in participants:
            raise ProjectEngineeringAuthorityValidationError(
                "supersede requires exactly one retained participant "
                "Approved Input."
            )
        retained = (retained_approved_input_id,)
        project_superseded = tuple(
            item
            for item in participants
            if item != retained_approved_input_id
        )
    elif outcome == "unresolved":
        if retained_approved_input_id is not None:
            raise ProjectEngineeringAuthorityValidationError(
                "unresolved must not select a retained Approved Input."
            )
        retained = ()
        project_superseded = ()
    else:
        if retained_approved_input_id is not None:
            raise ProjectEngineeringAuthorityValidationError(
                f"{outcome} does not accept retained_approved_input_id."
            )
        retained = participants
        project_superseded = ()

    body = {
        "schema_version": PROJECT_ENGINEERING_AUTHORITY_SCHEMA_VERSION,
        "project_id": reconciliation.project_id,
        "decision_id": decision_id,
        "reconciliation_fingerprint": (
            reconciliation.content_fingerprint
        ),
        "relation_fingerprint": _sha(asdict(relation)),
        "left_subject_ref": left_ref,
        "right_subject_ref": right_ref,
        "machine_relation_outcome": relation.outcome,
        "outcome": outcome,
        "authority_concern_id": concern,
        "retained_approved_input_ids": retained,
        "project_superseded_approved_input_ids": project_superseded,
        "reviewer_identity": reviewer_identity,
        "rationale": rationale,
        "decided_at": decided_at,
    }
    decision = ProjectAuthorityDecision(
        **body,
        decision_fingerprint=_sha(body),
    )
    validate_project_authority_decision(
        decision,
        reconciliation,
        bindings,
    )
    return decision


def validate_project_authority_decision(
    decision: ProjectAuthorityDecision,
    reconciliation: ProjectSemanticReconciliationArtifact,
    bindings: tuple[ProjectAuthoritySubjectBinding, ...],
) -> None:
    """Validate one Human decision against exact S3 evidence and AIN bindings."""

    if not isinstance(decision, ProjectAuthorityDecision):
        raise ProjectEngineeringAuthorityValidationError(
            "decision must be a ProjectAuthorityDecision."
        )
    validate_project_semantic_reconciliation_artifact(reconciliation)
    _validate_bindings_against_reconciliation(reconciliation, bindings)
    _validate_identifier(decision.decision_id, _DECISION_ID, "decision_id")

    if decision.schema_version != PROJECT_ENGINEERING_AUTHORITY_SCHEMA_VERSION:
        raise ProjectEngineeringAuthorityValidationError(
            "Unsupported Project Authority Decision schema_version."
        )
    if decision.project_id != reconciliation.project_id:
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority Decision crosses a Project boundary."
        )
    if (
        decision.reconciliation_fingerprint
        != reconciliation.content_fingerprint
    ):
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority Decision does not bind the exact S3 artifact."
        )
    if decision.outcome not in PROJECT_AUTHORITY_DECISION_OUTCOMES:
        raise ProjectEngineeringAuthorityValidationError(
            "Project Authority Decision outcome is invalid."
        )
    _required_text(decision.reviewer_identity, "reviewer_identity")
    _required_text(decision.rationale, "rationale")
    _validate_timestamp(decision.decided_at)

    relation = _find_relation(
        reconciliation,
        decision.left_subject_ref,
        decision.right_subject_ref,
    )
    expected_pair = tuple(
        sorted((relation.left_subject_ref, relation.right_subject_ref))
    )
    if (
        decision.left_subject_ref,
        decision.right_subject_ref,
    ) != expected_pair:
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority Decision Subject pair is not canonical."
        )
    if decision.machine_relation_outcome != relation.outcome:
        raise ProjectEngineeringAuthorityIntegrityError(
            "Machine relation outcome was not preserved exactly."
        )
    if decision.relation_fingerprint != _sha(asdict(relation)):
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority Decision relation fingerprint is stale."
        )

    binding_by_ref = {
        item.subject_ref: item
        for item in bindings
    }
    participants = tuple(
        sorted(
            {
                binding_by_ref[expected_pair[0]].approved_input_id,
                binding_by_ref[expected_pair[1]].approved_input_id,
            }
        )
    )
    if len(participants) != 2:
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority Decision does not bind two distinct AINs."
        )

    concern = decision.authority_concern_id
    if decision.outcome in {"remain_independent", "unresolved"}:
        if concern is not None:
            raise ProjectEngineeringAuthorityIntegrityError(
                "This outcome must not establish project concern identity."
            )
    else:
        _validate_identifier(
            concern,
            _CONCERN_ID,
            "authority_concern_id",
        )

    retained = decision.retained_approved_input_ids
    superseded = decision.project_superseded_approved_input_ids
    _sorted_unique_tuple(retained, "retained_approved_input_ids")
    _sorted_unique_tuple(
        superseded,
        "project_superseded_approved_input_ids",
    )

    if decision.outcome == "supersede":
        if (
            len(retained) != 1
            or len(superseded) != 1
            or set(retained) | set(superseded) != set(participants)
            or set(retained) & set(superseded)
        ):
            raise ProjectEngineeringAuthorityIntegrityError(
                "supersede must retain exactly one participant and mark "
                "the other as project-level superseded."
            )
    elif decision.outcome == "unresolved":
        if retained or superseded:
            raise ProjectEngineeringAuthorityIntegrityError(
                "unresolved must not select project-level authority."
            )
    else:
        if retained != participants or superseded:
            raise ProjectEngineeringAuthorityIntegrityError(
                f"{decision.outcome} must retain both source-local AINs."
            )

    _validate_sha(decision.decision_fingerprint, "decision_fingerprint")
    body = {
        key: value
        for key, value in asdict(decision).items()
        if key != "decision_fingerprint"
    }
    if decision.decision_fingerprint != _sha(body):
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority Decision fingerprint does not match content."
        )


def build_project_engineering_authority_state(
    reconciliation: ProjectSemanticReconciliationArtifact,
    approved_input_manifests: object,
    approved_input_events: object,
    approved_engineering_information: object,
    decisions: object,
) -> ProjectEngineeringAuthorityState:
    """Derive Human-authorized project state without mutating source authority."""

    bindings = prepare_project_authority_bindings(
        reconciliation,
        approved_input_manifests,
        approved_input_events,
        approved_engineering_information,
    )
    if not isinstance(decisions, tuple):
        raise ProjectEngineeringAuthorityValidationError(
            "decisions must be a tuple."
        )

    relation_pairs = {
        tuple(
            sorted((relation.left_subject_ref, relation.right_subject_ref))
        )
        for relation in reconciliation.relations
    }
    decision_by_pair = {}
    seen_decision_ids = set()
    normalized_decisions = []

    for decision in decisions:
        validate_project_authority_decision(
            decision,
            reconciliation,
            bindings,
        )
        if decision.decision_id in seen_decision_ids:
            raise ProjectEngineeringAuthorityIntegrityError(
                "Project Authority Decision IDs must be unique."
            )
        seen_decision_ids.add(decision.decision_id)

        pair = (
            decision.left_subject_ref,
            decision.right_subject_ref,
        )
        if pair in decision_by_pair:
            raise ProjectEngineeringAuthorityIntegrityError(
                "Each S3 relation may receive exactly one Human "
                "Project Authority Decision."
            )
        decision_by_pair[pair] = decision
        normalized_decisions.append(decision)

    if set(decision_by_pair) != relation_pairs:
        missing = sorted(relation_pairs - set(decision_by_pair))
        extra = sorted(set(decision_by_pair) - relation_pairs)
        raise ProjectEngineeringAuthorityIntegrityError(
            "Every S3 semantic relation requires exactly one Human "
            "Project Authority Decision before S4 can produce authority; "
            f"missing={missing}, extra={extra}."
        )

    normalized_decisions = tuple(
        sorted(
            normalized_decisions,
            key=lambda item: item.decision_id,
        )
    )
    entries = _derive_entries(bindings, normalized_decisions)
    unresolved = tuple(
        decision.decision_id
        for decision in normalized_decisions
        if decision.outcome == "unresolved"
    )

    body = {
        "schema_version": PROJECT_ENGINEERING_AUTHORITY_SCHEMA_VERSION,
        "project_id": reconciliation.project_id,
        "reconciliation_fingerprint": (
            reconciliation.content_fingerprint
        ),
        "bindings": bindings,
        "decisions": normalized_decisions,
        "entries": entries,
        "unresolved_decision_ids": unresolved,
        "model_impact_ready": not unresolved,
    }
    fingerprint_body = _jsonable(body)
    state = ProjectEngineeringAuthorityState(
        **body,
        content_fingerprint=_sha(fingerprint_body),
    )
    validate_project_engineering_authority_state(state)
    return state


def validate_project_engineering_authority_state(
    state: ProjectEngineeringAuthorityState,
) -> None:
    """Validate the self-contained immutable S4 authority state."""

    if not isinstance(state, ProjectEngineeringAuthorityState):
        raise ProjectEngineeringAuthorityValidationError(
            "state must be a ProjectEngineeringAuthorityState."
        )
    if state.schema_version != PROJECT_ENGINEERING_AUTHORITY_SCHEMA_VERSION:
        raise ProjectEngineeringAuthorityValidationError(
            "Unsupported Project Engineering Authority schema_version."
        )
    _required_text(state.project_id, "project_id")
    _validate_sha(
        state.reconciliation_fingerprint,
        "reconciliation_fingerprint",
    )

    if not isinstance(state.bindings, tuple) or not state.bindings:
        raise ProjectEngineeringAuthorityValidationError(
            "bindings must be a non-empty tuple."
        )
    if not isinstance(state.decisions, tuple):
        raise ProjectEngineeringAuthorityValidationError(
            "decisions must be a tuple."
        )
    if not isinstance(state.entries, tuple) or not state.entries:
        raise ProjectEngineeringAuthorityValidationError(
            "entries must be a non-empty tuple."
        )

    refs = []
    for binding in state.bindings:
        _validate_binding(binding)
        refs.append(binding.subject_ref)
    if tuple(refs) != tuple(sorted(refs)) or len(refs) != len(set(refs)):
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority bindings must use unique deterministic "
            "subject_ref order."
        )

    decision_ids = []
    pairs = []
    for decision in state.decisions:
        _validate_decision_self_contained(decision, state)
        decision_ids.append(decision.decision_id)
        pairs.append(
            (decision.left_subject_ref, decision.right_subject_ref)
        )
    if (
        tuple(decision_ids) != tuple(sorted(decision_ids))
        or len(decision_ids) != len(set(decision_ids))
    ):
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority Decisions must use unique deterministic IDs."
        )
    if len(pairs) != len(set(pairs)):
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority State contains duplicate relation decisions."
        )

    expected_entries = _derive_entries(
        state.bindings,
        state.decisions,
    )
    if expected_entries != state.entries:
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority entries do not match Human decisions."
        )

    expected_unresolved = tuple(
        decision.decision_id
        for decision in state.decisions
        if decision.outcome == "unresolved"
    )
    if state.unresolved_decision_ids != expected_unresolved:
        raise ProjectEngineeringAuthorityIntegrityError(
            "unresolved_decision_ids do not match Human decisions."
        )
    if state.model_impact_ready is not (not expected_unresolved):
        raise ProjectEngineeringAuthorityIntegrityError(
            "model_impact_ready does not match unresolved authority state."
        )

    _validate_sha(state.content_fingerprint, "content_fingerprint")
    body = {
        key: value
        for key, value in asdict(state).items()
        if key != "content_fingerprint"
    }
    if state.content_fingerprint != _sha(body):
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Engineering Authority fingerprint does not match content."
        )


def project_engineering_authority_to_dict(
    state: ProjectEngineeringAuthorityState,
) -> dict[str, Any]:
    """Return validated JSON-compatible S4 authority."""

    validate_project_engineering_authority_state(state)
    return asdict(state)


def project_engineering_authority_to_json(
    state: ProjectEngineeringAuthorityState,
) -> str:
    """Serialize S4 authority deterministically."""

    return json.dumps(
        project_engineering_authority_to_dict(state),
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def _derive_entries(
    bindings: tuple[ProjectAuthoritySubjectBinding, ...],
    decisions: tuple[ProjectAuthorityDecision, ...],
) -> tuple[ProjectAuthorityEntry, ...]:
    binding_by_ref = {
        item.subject_ref: item
        for item in bindings
    }
    binding_groups: dict[str, list[ProjectAuthoritySubjectBinding]] = {}
    for binding in bindings:
        binding_groups.setdefault(
            binding.approved_input_id,
            [],
        ).append(binding)

    state_intents: dict[str, set[str]] = {
        approved_input_id: set()
        for approved_input_id in binding_groups
    }
    concerns: dict[str, set[str]] = {
        approved_input_id: set()
        for approved_input_id in binding_groups
    }
    decision_ids: dict[str, set[str]] = {
        approved_input_id: set()
        for approved_input_id in binding_groups
    }

    # Active is the default only for AINs untouched by cross-source
    # decisions. Every explicit Human decision contributes one state intent;
    # incompatible intents fail closed instead of silently overriding.
    for decision in decisions:
        participants = {
            binding_by_ref[decision.left_subject_ref].approved_input_id,
            binding_by_ref[decision.right_subject_ref].approved_input_id,
        }
        for approved_input_id in participants:
            decision_ids[approved_input_id].add(decision.decision_id)
            if decision.authority_concern_id is not None:
                concerns[approved_input_id].add(
                    decision.authority_concern_id
                )

        if decision.outcome == "unresolved":
            desired = {
                approved_input_id: "unresolved"
                for approved_input_id in participants
            }
        elif decision.outcome == "supersede":
            desired = {
                approved_input_id: (
                    "superseded"
                    if approved_input_id
                    in decision.project_superseded_approved_input_ids
                    else "active"
                )
                for approved_input_id in participants
            }
        else:
            desired = {
                approved_input_id: "active"
                for approved_input_id in participants
            }

        for approved_input_id, authority_state in desired.items():
            state_intents[approved_input_id].add(authority_state)

    entries = []
    for approved_input_id in sorted(binding_groups):
        intents = state_intents[approved_input_id]
        if not intents:
            intents = {"active"}
        if len(intents) != 1:
            raise ProjectEngineeringAuthorityIntegrityError(
                "Human Project Authority Decisions assign conflicting "
                f"states to {approved_input_id}: {sorted(intents)}."
            )
        authority_state = next(iter(intents))
        if authority_state not in PROJECT_AUTHORITY_STATES:
            raise ProjectEngineeringAuthorityIntegrityError(
                "Derived Project Authority state is unsupported."
            )

        group = tuple(
            sorted(
                binding_groups[approved_input_id],
                key=lambda item: item.subject_ref,
            )
        )
        first = group[0]
        if any(
            item.source_id != first.source_id
            or item.approved_input_fingerprint
            != first.approved_input_fingerprint
            or item.stable_subject_key != first.stable_subject_key
            for item in group
        ):
            raise ProjectEngineeringAuthorityIntegrityError(
                "One Approved Input has inconsistent Subject bindings."
            )

        body = {
            "approved_input_id": approved_input_id,
            "source_id": first.source_id,
            "subject_refs": tuple(
                item.subject_ref
                for item in group
            ),
            "approved_input_fingerprint": (
                first.approved_input_fingerprint
            ),
            "stable_subject_key": first.stable_subject_key,
            "project_authority_state": authority_state,
            "authority_concern_ids": tuple(
                sorted(concerns[approved_input_id])
            ),
            "decision_ids": tuple(
                sorted(decision_ids[approved_input_id])
            ),
        }
        entries.append(
            ProjectAuthorityEntry(
                **body,
                content_fingerprint=_sha(body),
            )
        )

    return tuple(entries)


def _validate_bindings_against_reconciliation(
    reconciliation: ProjectSemanticReconciliationArtifact,
    bindings: object,
) -> None:
    if not isinstance(bindings, tuple):
        raise ProjectEngineeringAuthorityValidationError(
            "bindings must be a tuple."
        )
    expected = {
        subject.subject_ref: subject
        for subject in reconciliation.subjects
    }
    actual = {}
    for binding in bindings:
        _validate_binding(binding)
        if binding.subject_ref in actual:
            raise ProjectEngineeringAuthorityIntegrityError(
                "Duplicate Project Authority subject_ref binding."
            )
        actual[binding.subject_ref] = binding

    if set(actual) != set(expected):
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority bindings must cover the exact S3 Subject set."
        )
    for subject_ref, binding in actual.items():
        subject = expected[subject_ref]
        if (
            binding.canonical_subject_id
            != subject.canonical_subject_id
            or binding.source_id != subject.source_id
        ):
            raise ProjectEngineeringAuthorityIntegrityError(
                "Project Authority binding does not match S3 Subject "
                "source identity."
            )


def _validate_binding(binding: ProjectAuthoritySubjectBinding) -> None:
    if not isinstance(binding, ProjectAuthoritySubjectBinding):
        raise ProjectEngineeringAuthorityValidationError(
            "bindings contains an invalid value."
        )
    for label, value in (
        ("subject_ref", binding.subject_ref),
        ("canonical_subject_id", binding.canonical_subject_id),
        ("source_id", binding.source_id),
        ("approved_input_id", binding.approved_input_id),
        ("stable_subject_key", binding.stable_subject_key),
        ("review_document_id", binding.review_document_id),
        (
            "review_document_version_id",
            binding.review_document_version_id,
        ),
        ("review_revision_id", binding.review_revision_id),
    ):
        _required_text(value, label)
    for label, value in (
        (
            "approved_input_fingerprint",
            binding.approved_input_fingerprint,
        ),
        ("aei_content_fingerprint", binding.aei_content_fingerprint),
        ("content_fingerprint", binding.content_fingerprint),
    ):
        _validate_sha(value, label)

    body = {
        key: value
        for key, value in asdict(binding).items()
        if key != "content_fingerprint"
    }
    if binding.content_fingerprint != _sha(body):
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority Subject binding fingerprint does not match."
        )


def _validate_decision_self_contained(
    decision: ProjectAuthorityDecision,
    state: ProjectEngineeringAuthorityState,
) -> None:
    if not isinstance(decision, ProjectAuthorityDecision):
        raise ProjectEngineeringAuthorityValidationError(
            "decisions contains an invalid value."
        )
    if decision.schema_version != PROJECT_ENGINEERING_AUTHORITY_SCHEMA_VERSION:
        raise ProjectEngineeringAuthorityValidationError(
            "Project Authority Decision schema_version is invalid."
        )
    if decision.project_id != state.project_id:
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority Decision crosses state Project boundary."
        )
    if (
        decision.reconciliation_fingerprint
        != state.reconciliation_fingerprint
    ):
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority Decision binds another reconciliation artifact."
        )
    _validate_identifier(decision.decision_id, _DECISION_ID, "decision_id")
    _validate_sha(decision.relation_fingerprint, "relation_fingerprint")
    if decision.outcome not in PROJECT_AUTHORITY_DECISION_OUTCOMES:
        raise ProjectEngineeringAuthorityValidationError(
            "Project Authority Decision outcome is invalid."
        )
    _required_text(
        decision.machine_relation_outcome,
        "machine_relation_outcome",
    )
    _required_text(decision.left_subject_ref, "left_subject_ref")
    _required_text(decision.right_subject_ref, "right_subject_ref")
    if decision.left_subject_ref >= decision.right_subject_ref:
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority Decision Subject refs must be canonical."
        )
    _required_text(decision.reviewer_identity, "reviewer_identity")
    _required_text(decision.rationale, "rationale")
    _validate_timestamp(decision.decided_at)

    binding_by_ref = {
        item.subject_ref: item
        for item in state.bindings
    }
    if (
        decision.left_subject_ref not in binding_by_ref
        or decision.right_subject_ref not in binding_by_ref
    ):
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority Decision references an unavailable Subject."
        )
    participants = tuple(
        sorted(
            {
                binding_by_ref[
                    decision.left_subject_ref
                ].approved_input_id,
                binding_by_ref[
                    decision.right_subject_ref
                ].approved_input_id,
            }
        )
    )
    if len(participants) != 2:
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority Decision must bind two distinct AINs."
        )

    if decision.outcome in {"remain_independent", "unresolved"}:
        if decision.authority_concern_id is not None:
            raise ProjectEngineeringAuthorityIntegrityError(
                "This decision outcome must not establish concern identity."
            )
    else:
        _validate_identifier(
            decision.authority_concern_id,
            _CONCERN_ID,
            "authority_concern_id",
        )

    if decision.outcome == "supersede":
        if (
            len(decision.retained_approved_input_ids) != 1
            or len(
                decision.project_superseded_approved_input_ids
            )
            != 1
            or set(decision.retained_approved_input_ids)
            | set(decision.project_superseded_approved_input_ids)
            != set(participants)
        ):
            raise ProjectEngineeringAuthorityIntegrityError(
                "Self-contained supersede decision is inconsistent."
            )
    elif decision.outcome == "unresolved":
        if (
            decision.retained_approved_input_ids
            or decision.project_superseded_approved_input_ids
        ):
            raise ProjectEngineeringAuthorityIntegrityError(
                "Self-contained unresolved decision is inconsistent."
            )
    else:
        if (
            decision.retained_approved_input_ids != participants
            or decision.project_superseded_approved_input_ids
        ):
            raise ProjectEngineeringAuthorityIntegrityError(
                "Self-contained retained authority is inconsistent."
            )

    _validate_sha(decision.decision_fingerprint, "decision_fingerprint")
    body = {
        key: value
        for key, value in asdict(decision).items()
        if key != "decision_fingerprint"
    }
    if decision.decision_fingerprint != _sha(body):
        raise ProjectEngineeringAuthorityIntegrityError(
            "Project Authority Decision fingerprint does not match."
        )


def _validate_aei_set(aei: object) -> None:
    if not isinstance(aei, ApprovedEngineeringInformationSet):
        raise ProjectEngineeringAuthorityValidationError(
            "approved_engineering_information contains an invalid value."
        )
    if (
        aei.schema_version
        != APPROVED_ENGINEERING_INFORMATION_SCHEMA_VERSION
    ):
        raise ProjectEngineeringAuthorityValidationError(
            "Unsupported Approved Engineering Information schema_version."
        )
    for label, value in (
        ("project_id", aei.project_id),
        ("review_document_id", aei.review_document_id),
        (
            "review_document_version_id",
            aei.review_document_version_id,
        ),
        ("review_revision_id", aei.review_revision_id),
    ):
        _required_text(value, label)

    _validate_sha(
        aei.relationship_decision_authority_fingerprint,
        "relationship_decision_authority_fingerprint",
    )
    _validate_sha(aei.content_fingerprint, "AEI content_fingerprint")

    body = {
        "schema_version": aei.schema_version,
        "project_id": aei.project_id,
        "review_document_id": aei.review_document_id,
        "review_document_version_id": (
            aei.review_document_version_id
        ),
        "review_revision_id": aei.review_revision_id,
        "subjects": [
            asdict(item)
            for item in aei.subjects
        ],
        "relationships": [
            asdict(item)
            for item in aei.relationships
        ],
        "non_promotable_subject_ids": list(
            aei.non_promotable_subject_ids
        ),
        "non_projectable_relationship_decision_ids": list(
            aei.non_projectable_relationship_decision_ids
        ),
        "relationship_decision_authority_fingerprint": (
            aei.relationship_decision_authority_fingerprint
        ),
    }
    if aei.content_fingerprint != _sha(body):
        raise ProjectEngineeringAuthorityIntegrityError(
            "Approved Engineering Information fingerprint does not match."
        )


def _validate_aei_subject_binding(
    aei: ApprovedEngineeringInformationSet,
    subject,
    manifest: ApprovedInputManifest,
) -> None:
    try:
        validate_approved_input_manifest(manifest)
    except Exception as exc:
        raise ProjectEngineeringAuthorityValidationError(
            "Approved Input Manifest is invalid."
        ) from exc

    if manifest.project_id != aei.project_id:
        raise ProjectEngineeringAuthorityIntegrityError(
            "Approved Input and AEI cross a Project boundary."
        )
    if (
        manifest.review_document_id != aei.review_document_id
        or manifest.review_document_version_id
        != aei.review_document_version_id
        or manifest.review_revision_id != aei.review_revision_id
    ):
        raise ProjectEngineeringAuthorityIntegrityError(
            "AEI does not bind the exact Approved Input Review authority."
        )
    if subject.approved_input_id != manifest.approved_input_id:
        raise ProjectEngineeringAuthorityIntegrityError(
            "AEI approved_input_id binding is inconsistent."
        )
    if (
        subject.approved_input_fingerprint
        != manifest.content_fingerprint
    ):
        raise ProjectEngineeringAuthorityIntegrityError(
            "AEI Approved Input fingerprint is stale."
        )
    if subject.stable_subject_key != manifest.stable_subject_key:
        raise ProjectEngineeringAuthorityIntegrityError(
            "AEI stable_subject_key does not match Approved Input."
        )
    if (
        subject.review_item_id != manifest.review_item_id
        or subject.review_item_fingerprint
        != manifest.review_item_fingerprint
    ):
        raise ProjectEngineeringAuthorityIntegrityError(
            "AEI Review Item binding does not match Approved Input."
        )

    content = manifest.canonical_content
    if (
        subject.title != content.title
        or subject.engineering_statement != content.primary_text
        or subject.information_type != content.information_type
        or subject.statement_modality != content.modality
        or subject.epistemic_class != content.epistemic_status
    ):
        raise ProjectEngineeringAuthorityIntegrityError(
            "AEI reviewed engineering content does not match Approved Input."
        )


def _find_relation(
    reconciliation: ProjectSemanticReconciliationArtifact,
    left_subject_ref: str,
    right_subject_ref: str,
):
    requested = tuple(
        sorted(
            (
                _required_text(left_subject_ref, "left_subject_ref"),
                _required_text(right_subject_ref, "right_subject_ref"),
            )
        )
    )
    for relation in reconciliation.relations:
        pair = tuple(
            sorted(
                (
                    relation.left_subject_ref,
                    relation.right_subject_ref,
                )
            )
        )
        if pair == requested:
            return relation
    raise ProjectEngineeringAuthorityIntegrityError(
        "Human Project Authority Decision must reference one exact "
        "S3 semantic relation."
    )


def _normalize_optional_concern(value: object) -> str | None:
    if value is None:
        return None
    return _validate_identifier(
        value,
        _CONCERN_ID,
        "authority_concern_id",
    )


def _validate_identifier(
    value: object,
    pattern: re.Pattern[str],
    label: str,
) -> str:
    if not isinstance(value, str):
        raise ProjectEngineeringAuthorityValidationError(
            f"{label} must be a string."
        )
    match = pattern.fullmatch(value)
    if match is None or int(match.group(1)) == 0:
        raise ProjectEngineeringAuthorityValidationError(
            f"{label} has invalid identifier syntax."
        )
    return value


def _required_text(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
    ):
        raise ProjectEngineeringAuthorityValidationError(
            f"{label} must be a non-empty trimmed string."
        )
    return value


def _validate_timestamp(value: object) -> str:
    if not isinstance(value, str) or _UTC_TIMESTAMP.fullmatch(value) is None:
        raise ProjectEngineeringAuthorityValidationError(
            "decided_at must be a UTC ISO-8601 timestamp ending in Z."
        )
    return value


def _validate_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ProjectEngineeringAuthorityValidationError(
            f"{label} must be a lowercase SHA-256 string."
        )
    return value


def _sorted_unique_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ProjectEngineeringAuthorityValidationError(
            f"{label} must be a tuple."
        )
    if tuple(sorted(value)) != value or len(value) != len(set(value)):
        raise ProjectEngineeringAuthorityIntegrityError(
            f"{label} must be sorted and unique."
        )
    for item in value:
        _required_text(item, label)
    return value


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _jsonable(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [
            _jsonable(item)
            for item in value
        ]
    if hasattr(value, "__dataclass_fields__"):
        return _jsonable(asdict(value))
    return value


def _sha(value: Any) -> str:
    canonical = json.dumps(
        _jsonable(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
