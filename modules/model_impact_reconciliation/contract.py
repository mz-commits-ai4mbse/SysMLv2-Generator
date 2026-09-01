"""ADR-032 S5 deterministic Model Impact Reconciliation contract."""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
import re
from typing import Any

from modules.internal_model.authority_backed import (
    AuthorityBackedInternalModelSnapshot,
    authority_backed_internal_model_from_json,
    authority_backed_internal_model_to_json,
)
from modules.project_engineering_authority import (
    ProjectEngineeringAuthorityState,
    validate_project_engineering_authority_state,
)

from .errors import (
    ModelImpactReconciliationIntegrityError,
    ModelImpactReconciliationValidationError,
)
from .types import (
    MODEL_IMPACT_OUTCOMES,
    ModelImpactProposal,
    ModelImpactReconciliationArtifact,
)


MODEL_IMPACT_RECONCILIATION_SCHEMA_VERSION = "1.0.0"

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_RATIONALE_CODE = re.compile(r"^[a-z][a-z0-9_]{0,119}$")


def reconcile_model_impact(
    project_authority: ProjectEngineeringAuthorityState,
    accepted_model: AuthorityBackedInternalModelSnapshot | None,
) -> ModelImpactReconciliationArtifact:
    """Compare Human-authorized S4 state with one accepted model snapshot."""

    try:
        validate_project_engineering_authority_state(project_authority)
    except Exception as exc:
        raise ModelImpactReconciliationValidationError(
            "Project Engineering Authority State is invalid."
        ) from exc

    if not project_authority.model_impact_ready:
        raise ModelImpactReconciliationIntegrityError(
            "S5 is blocked while Project Engineering Authority contains "
            "unresolved Human decisions."
        )

    model = _validate_accepted_model(
        accepted_model,
        project_id=project_authority.project_id,
    )

    model_element_by_ain = {}
    model_element_by_subject_key = {}
    element_by_id = {}
    relationships = ()
    if model is not None:
        relationships = model.relationships
        for element in model.elements:
            if element.internal_model_element_id in element_by_id:
                raise ModelImpactReconciliationIntegrityError(
                    "Accepted model contains duplicate element identity."
                )
            element_by_id[element.internal_model_element_id] = element

            existing = model_element_by_ain.get(element.approved_input_id)
            if existing is not None:
                raise ModelImpactReconciliationIntegrityError(
                    "Accepted model materializes one Approved Input more than "
                    "once; S5 cannot infer a unique impact target."
                )
            model_element_by_ain[element.approved_input_id] = element

            existing_subject = model_element_by_subject_key.get(
                element.model_subject_key
            )
            if existing_subject is not None:
                raise ModelImpactReconciliationIntegrityError(
                    "Accepted model materializes one model_subject_key more "
                    "than once; S5 cannot infer unique subject context."
                )
            model_element_by_subject_key[element.model_subject_key] = element

    entry_by_ain = {
        entry.approved_input_id: entry
        for entry in project_authority.entries
    }
    if len(entry_by_ain) != len(project_authority.entries):
        raise ModelImpactReconciliationIntegrityError(
            "Project Authority entries contain duplicate Approved Input IDs."
        )

    concern_members: dict[str, set[str]] = {}
    concern_outcomes: dict[str, set[str]] = {}
    for entry in project_authority.entries:
        for concern_id in entry.authority_concern_ids:
            concern_members.setdefault(concern_id, set()).add(
                entry.approved_input_id
            )

    for decision in project_authority.decisions:
        if decision.authority_concern_id is None:
            continue
        concern_outcomes.setdefault(
            decision.authority_concern_id,
            set(),
        ).add(decision.outcome)

    for concern_id, outcomes in concern_outcomes.items():
        if len(outcomes) != 1:
            raise ModelImpactReconciliationIntegrityError(
                "One project authority concern is governed by conflicting "
                "Human decision outcomes."
            )
        if next(iter(outcomes)) not in {"coexist", "supersede"}:
            raise ModelImpactReconciliationIntegrityError(
                "Project authority concern uses an unsupported S5 outcome."
            )

    proposals = []
    touched_element_ids = set()
    touched_relationship_ids = set()

    for entry in project_authority.entries:
        current_element = model_element_by_ain.get(
            entry.approved_input_id
        )
        if current_element is not None:
            if current_element.model_subject_key != entry.stable_subject_key:
                raise ModelImpactReconciliationIntegrityError(
                    "Accepted model Approved Input traceability disagrees "
                    "with the current stable_subject_key."
                )
            current_ids = (
                current_element.internal_model_element_id,
            )
        else:
            current_ids = ()

        concern_related_ids = _related_model_element_ids(
            entry=entry,
            concern_members=concern_members,
            entry_by_ain=entry_by_ain,
            model_element_by_ain=model_element_by_ain,
        )

        collision_ids = ()
        if current_element is None:
            same_key_element = model_element_by_subject_key.get(
                entry.stable_subject_key
            )
            if (
                same_key_element is not None
                and same_key_element.approved_input_id
                != entry.approved_input_id
            ):
                collision_ids = (
                    same_key_element.internal_model_element_id,
                )

        related_ids = tuple(
            sorted(set(concern_related_ids) | set(collision_ids))
        )

        outcome, change_required, rationale_code = _derive_impact(
            entry=entry,
            current_model_element_ids=current_ids,
            related_model_element_ids=concern_related_ids,
            stable_subject_collision_ids=collision_ids,
            concern_outcomes=concern_outcomes,
        )

        context_element_ids = tuple(
            sorted(set(current_ids) | set(related_ids))
        )
        impacted_relationship_ids = _relationship_ids_touching(
            relationships,
            set(context_element_ids),
        )

        touched_element_ids.update(context_element_ids)
        touched_relationship_ids.update(impacted_relationship_ids)

        body = {
            "approved_input_id": entry.approved_input_id,
            "source_id": entry.source_id,
            "stable_subject_key": entry.stable_subject_key,
            "project_authority_state": (
                entry.project_authority_state
            ),
            "authority_concern_ids": entry.authority_concern_ids,
            "outcome": outcome,
            "current_model_element_ids": current_ids,
            "related_model_element_ids": related_ids,
            "impacted_relationship_ids": impacted_relationship_ids,
            "model_change_required": change_required,
            "rationale_code": rationale_code,
        }
        proposals.append(
            ModelImpactProposal(
                **body,
                content_fingerprint=_sha(body),
            )
        )

    normalized_proposals = tuple(
        sorted(proposals, key=lambda item: item.approved_input_id)
    )
    unresolved = tuple(
        proposal.approved_input_id
        for proposal in normalized_proposals
        if proposal.outcome == "unresolved"
    )

    all_element_ids = set(element_by_id)
    all_relationship_ids = {
        relationship.internal_model_relationship_id
        for relationship in relationships
    }
    unaffected_elements = tuple(
        sorted(all_element_ids - touched_element_ids)
    )
    unaffected_relationships = tuple(
        sorted(all_relationship_ids - touched_relationship_ids)
    )

    body = {
        "schema_version": MODEL_IMPACT_RECONCILIATION_SCHEMA_VERSION,
        "project_id": project_authority.project_id,
        "project_authority_fingerprint": (
            project_authority.content_fingerprint
        ),
        "accepted_model_id": (
            None
            if model is None
            else model.internal_engineering_model_id
        ),
        "accepted_model_fingerprint": (
            None
            if model is None
            else model.content_fingerprint
        ),
        "accepted_model_final_review_decision_id": (
            None
            if model is None
            else model.final_model_review_decision_id
        ),
        "accepted_model_final_review_decision_fingerprint": (
            None
            if model is None
            else model.final_model_review_decision_fingerprint
        ),
        "accepted_model_profile_id": (
            None if model is None else model.profile_id
        ),
        "accepted_model_profile_version": (
            None if model is None else model.profile_version
        ),
        "accepted_model_profile_fingerprint": (
            None if model is None else model.profile_fingerprint
        ),
        "proposals": normalized_proposals,
        "unaffected_model_element_ids": unaffected_elements,
        "unaffected_model_relationship_ids": unaffected_relationships,
        "unresolved_approved_input_ids": unresolved,
        "model_change_required": any(
            proposal.model_change_required
            for proposal in normalized_proposals
        ),
        "human_model_review_required": True,
    }
    artifact = ModelImpactReconciliationArtifact(
        **body,
        content_fingerprint=_sha(body),
    )
    validate_model_impact_reconciliation_artifact(artifact)
    return artifact


def validate_model_impact_reconciliation_artifact(
    artifact: ModelImpactReconciliationArtifact,
) -> None:
    """Validate one self-contained immutable S5 advisory artifact."""

    if not isinstance(artifact, ModelImpactReconciliationArtifact):
        raise ModelImpactReconciliationValidationError(
            "artifact must be a ModelImpactReconciliationArtifact."
        )
    if artifact.schema_version != MODEL_IMPACT_RECONCILIATION_SCHEMA_VERSION:
        raise ModelImpactReconciliationValidationError(
            "Unsupported Model Impact Reconciliation schema_version."
        )
    _required_text(artifact.project_id, "project_id")
    _validate_sha(
        artifact.project_authority_fingerprint,
        "project_authority_fingerprint",
    )

    model_values = (
        artifact.accepted_model_id,
        artifact.accepted_model_fingerprint,
        artifact.accepted_model_final_review_decision_id,
        artifact.accepted_model_final_review_decision_fingerprint,
        artifact.accepted_model_profile_id,
        artifact.accepted_model_profile_version,
        artifact.accepted_model_profile_fingerprint,
    )
    if all(value is None for value in model_values):
        pass
    elif any(value is None for value in model_values):
        raise ModelImpactReconciliationIntegrityError(
            "Accepted model authority metadata must be all present or all absent."
        )
    else:
        _required_text(artifact.accepted_model_id, "accepted_model_id")
        _validate_sha(
            artifact.accepted_model_fingerprint,
            "accepted_model_fingerprint",
        )
        _required_text(
            artifact.accepted_model_final_review_decision_id,
            "accepted_model_final_review_decision_id",
        )
        _validate_sha(
            artifact.accepted_model_final_review_decision_fingerprint,
            "accepted_model_final_review_decision_fingerprint",
        )
        _required_text(
            artifact.accepted_model_profile_id,
            "accepted_model_profile_id",
        )
        _required_text(
            artifact.accepted_model_profile_version,
            "accepted_model_profile_version",
        )
        _validate_sha(
            artifact.accepted_model_profile_fingerprint,
            "accepted_model_profile_fingerprint",
        )

    if not isinstance(artifact.proposals, tuple) or not artifact.proposals:
        raise ModelImpactReconciliationValidationError(
            "proposals must be a non-empty tuple."
        )

    proposal_ids = []
    for proposal in artifact.proposals:
        _validate_proposal(proposal)
        proposal_ids.append(proposal.approved_input_id)
    if (
        tuple(proposal_ids) != tuple(sorted(proposal_ids))
        or len(proposal_ids) != len(set(proposal_ids))
    ):
        raise ModelImpactReconciliationIntegrityError(
            "S5 proposals must use unique deterministic Approved Input order."
        )

    _sorted_unique_tuple(
        artifact.unaffected_model_element_ids,
        "unaffected_model_element_ids",
    )
    _sorted_unique_tuple(
        artifact.unaffected_model_relationship_ids,
        "unaffected_model_relationship_ids",
    )
    _sorted_unique_tuple(
        artifact.unresolved_approved_input_ids,
        "unresolved_approved_input_ids",
    )

    expected_unresolved = tuple(
        proposal.approved_input_id
        for proposal in artifact.proposals
        if proposal.outcome == "unresolved"
    )
    if artifact.unresolved_approved_input_ids != expected_unresolved:
        raise ModelImpactReconciliationIntegrityError(
            "unresolved_approved_input_ids do not match S5 proposals."
        )

    expected_change = any(
        proposal.model_change_required
        for proposal in artifact.proposals
    )
    if artifact.model_change_required is not expected_change:
        raise ModelImpactReconciliationIntegrityError(
            "model_change_required does not match S5 proposals."
        )
    if artifact.human_model_review_required is not True:
        raise ModelImpactReconciliationIntegrityError(
            "Model Impact Reconciliation can never waive Human Model Review."
        )

    _validate_sha(artifact.content_fingerprint, "content_fingerprint")
    body = {
        key: value
        for key, value in asdict(artifact).items()
        if key != "content_fingerprint"
    }
    if artifact.content_fingerprint != _sha(body):
        raise ModelImpactReconciliationIntegrityError(
            "Model Impact Reconciliation fingerprint does not match content."
        )


def model_impact_reconciliation_to_dict(
    artifact: ModelImpactReconciliationArtifact,
) -> dict[str, Any]:
    """Return validated JSON-compatible S5 evidence."""

    validate_model_impact_reconciliation_artifact(artifact)
    return asdict(artifact)


def model_impact_reconciliation_to_json(
    artifact: ModelImpactReconciliationArtifact,
) -> str:
    """Serialize S5 evidence deterministically."""

    return json.dumps(
        model_impact_reconciliation_to_dict(artifact),
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def _derive_impact(
    *,
    entry,
    current_model_element_ids: tuple[str, ...],
    related_model_element_ids: tuple[str, ...],
    stable_subject_collision_ids: tuple[str, ...],
    concern_outcomes: dict[str, set[str]],
) -> tuple[str, bool, str]:
    if entry.project_authority_state == "unresolved":
        return (
            "unresolved",
            False,
            "project_authority_unresolved",
        )

    if entry.project_authority_state == "superseded":
        return (
            "supersede",
            bool(current_model_element_ids),
            (
                "project_superseded_authority_is_materialized"
                if current_model_element_ids
                else "project_superseded_authority_not_materialized"
            ),
        )

    if entry.project_authority_state != "active":
        raise ModelImpactReconciliationIntegrityError(
            "S5 received unsupported Project Authority state."
        )

    if current_model_element_ids:
        return (
            "retain",
            False,
            "active_authority_already_materialized",
        )

    if stable_subject_collision_ids:
        return (
            "unresolved",
            False,
            "stable_subject_key_collision_requires_human_model_review",
        )

    represented_concern_intents = set()
    if related_model_element_ids:
        for concern_id in entry.authority_concern_ids:
            outcomes = concern_outcomes.get(concern_id, set())
            represented_concern_intents.update(outcomes)

    if represented_concern_intents == {"supersede"}:
        return (
            "modify",
            True,
            "accepted_successor_modifies_existing_concern",
        )
    if represented_concern_intents == {"coexist"}:
        return (
            "extend",
            True,
            "coexisting_authority_extends_existing_concern",
        )
    if len(represented_concern_intents) > 1:
        return (
            "unresolved",
            False,
            "conflicting_project_concern_model_impacts",
        )

    return (
        "new",
        True,
        "active_authority_not_materialized",
    )


def _related_model_element_ids(
    *,
    entry,
    concern_members: dict[str, set[str]],
    entry_by_ain: dict[str, Any],
    model_element_by_ain: dict[str, Any],
) -> tuple[str, ...]:
    values = set()
    for concern_id in entry.authority_concern_ids:
        for approved_input_id in concern_members.get(concern_id, set()):
            if approved_input_id == entry.approved_input_id:
                continue
            if approved_input_id not in entry_by_ain:
                raise ModelImpactReconciliationIntegrityError(
                    "Project authority concern references an unavailable "
                    "Authority Entry."
                )
            element = model_element_by_ain.get(approved_input_id)
            if element is not None:
                values.add(element.internal_model_element_id)
    return tuple(sorted(values))


def _relationship_ids_touching(
    relationships: object,
    element_ids: set[str],
) -> tuple[str, ...]:
    if not element_ids:
        return ()
    return tuple(
        sorted(
            relationship.internal_model_relationship_id
            for relationship in relationships
            if (
                relationship.source_internal_model_element_id in element_ids
                or relationship.target_internal_model_element_id in element_ids
            )
        )
    )


def _validate_accepted_model(
    value: AuthorityBackedInternalModelSnapshot | None,
    *,
    project_id: str,
) -> AuthorityBackedInternalModelSnapshot | None:
    if value is None:
        return None
    if not isinstance(value, AuthorityBackedInternalModelSnapshot):
        raise ModelImpactReconciliationValidationError(
            "accepted_model must be an AuthorityBackedInternalModelSnapshot "
            "or None."
        )
    try:
        round_trip = authority_backed_internal_model_from_json(
            authority_backed_internal_model_to_json(value)
        )
    except Exception as exc:
        raise ModelImpactReconciliationValidationError(
            "Accepted authority-backed Internal Model is invalid."
        ) from exc
    if round_trip != value:
        raise ModelImpactReconciliationIntegrityError(
            "Accepted Internal Model does not round-trip exactly."
        )
    if value.project_id != project_id:
        raise ModelImpactReconciliationIntegrityError(
            "Accepted Internal Model crosses the Project boundary."
        )
    return value


def _validate_proposal(proposal: ModelImpactProposal) -> None:
    if not isinstance(proposal, ModelImpactProposal):
        raise ModelImpactReconciliationValidationError(
            "proposals contains an invalid value."
        )
    for label, value in (
        ("approved_input_id", proposal.approved_input_id),
        ("source_id", proposal.source_id),
        ("stable_subject_key", proposal.stable_subject_key),
        ("project_authority_state", proposal.project_authority_state),
        ("rationale_code", proposal.rationale_code),
    ):
        _required_text(value, label)

    if proposal.outcome not in MODEL_IMPACT_OUTCOMES:
        raise ModelImpactReconciliationValidationError(
            "Model Impact outcome is unsupported."
        )
    if _RATIONALE_CODE.fullmatch(proposal.rationale_code) is None:
        raise ModelImpactReconciliationValidationError(
            "rationale_code must be a lowercase deterministic identifier."
        )

    for label, value in (
        ("authority_concern_ids", proposal.authority_concern_ids),
        ("current_model_element_ids", proposal.current_model_element_ids),
        ("related_model_element_ids", proposal.related_model_element_ids),
        ("impacted_relationship_ids", proposal.impacted_relationship_ids),
    ):
        _sorted_unique_tuple(value, label)

    if set(proposal.current_model_element_ids) & set(
        proposal.related_model_element_ids
    ):
        raise ModelImpactReconciliationIntegrityError(
            "Current and related Model Element targets must be disjoint."
        )

    if proposal.outcome == "retain":
        if not proposal.current_model_element_ids:
            raise ModelImpactReconciliationIntegrityError(
                "retain requires an existing exact model representation."
            )
        if proposal.model_change_required:
            raise ModelImpactReconciliationIntegrityError(
                "retain must not require a model change."
            )
    elif proposal.outcome in {"extend", "modify", "new"}:
        if not proposal.model_change_required:
            raise ModelImpactReconciliationIntegrityError(
                f"{proposal.outcome} must require Human-reviewed model change."
            )
        if proposal.current_model_element_ids:
            raise ModelImpactReconciliationIntegrityError(
                f"{proposal.outcome} is for authority not already exactly "
                "materialized."
            )
        if proposal.outcome in {"extend", "modify"} and not (
            proposal.related_model_element_ids
        ):
            raise ModelImpactReconciliationIntegrityError(
                f"{proposal.outcome} requires existing related model context."
            )
    elif proposal.outcome == "supersede":
        if proposal.model_change_required is not bool(
            proposal.current_model_element_ids
        ):
            raise ModelImpactReconciliationIntegrityError(
                "supersede model-change requirement must match whether the "
                "superseded authority is materialized."
            )
    elif proposal.outcome == "unresolved":
        if proposal.model_change_required:
            raise ModelImpactReconciliationIntegrityError(
                "unresolved must not authorize a model change."
            )

    _validate_sha(proposal.content_fingerprint, "content_fingerprint")
    body = {
        key: value
        for key, value in asdict(proposal).items()
        if key != "content_fingerprint"
    }
    if proposal.content_fingerprint != _sha(body):
        raise ModelImpactReconciliationIntegrityError(
            "Model Impact Proposal fingerprint does not match content."
        )


def _required_text(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
    ):
        raise ModelImpactReconciliationValidationError(
            f"{label} must be a non-empty trimmed string."
        )
    return value


def _validate_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ModelImpactReconciliationValidationError(
            f"{label} must be a lowercase SHA-256 string."
        )
    return value


def _sorted_unique_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ModelImpactReconciliationValidationError(
            f"{label} must be a tuple."
        )
    if tuple(sorted(value)) != value or len(value) != len(set(value)):
        raise ModelImpactReconciliationIntegrityError(
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
