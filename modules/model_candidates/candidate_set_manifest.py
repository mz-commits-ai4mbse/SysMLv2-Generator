"""Strict immutable manifest for one Phase-H Model Candidate Set."""

from __future__ import annotations

from dataclasses import fields, replace
from typing import Callable

from modules.project_workspace.types import FrameworkTemplateReference

from ._manifest_support import (
    approved_input_reference_payload,
    calculate_approved_input_snapshot_fingerprint,
    canonical_fingerprint,
    derivation_rules_reference_payload,
    deterministic_json,
    exact_object,
    framework_template_reference_payload,
    generation_provenance_payload,
    model_structure_profile_reference_payload,
    normalize_approved_input_references,
    optional_text,
    parse_approved_input_reference,
    parse_derivation_rules_reference,
    parse_framework_template_reference,
    parse_generation_provenance,
    parse_model_structure_profile_reference,
    sha256,
    strict_json_loads,
    timestamp,
    validate_project_id,
)
from .errors import (
    ModelCandidateIntegrityError,
    ModelCandidateValidationError,
)
from .identifiers import (
    validate_model_candidate_set_id,
    validate_model_element_candidate_id,
    validate_model_relationship_candidate_id,
)
from .types import (
    ModelCandidateApprovedInputReference,
    ModelCandidateGenerationProvenance,
    ModelCandidateSetManifest,
    ModelDerivationRulesReference,
    ModelStructureProfileReference,
)


MODEL_CANDIDATE_SET_SCHEMA_VERSION = "1.0.0"

_FIELDS = frozenset(
    field.name for field in fields(ModelCandidateSetManifest)
)


def create_model_candidate_set_manifest(
    *,
    project_id: str,
    candidate_set_id: str,
    predecessor_candidate_set_id: str | None,
    regeneration_reason: str | None,
    approved_input_references: tuple[
        ModelCandidateApprovedInputReference,
        ...,
    ],
    framework_template_reference: FrameworkTemplateReference,
    model_structure_profile_reference: ModelStructureProfileReference,
    derivation_rules_reference: ModelDerivationRulesReference,
    generation_provenance: ModelCandidateGenerationProvenance,
    element_candidate_ids: tuple[str, ...],
    relationship_candidate_ids: tuple[str, ...],
    created_at: str,
) -> ModelCandidateSetManifest:
    """Create one deterministic immutable Candidate Set manifest."""

    normalized_inputs = normalize_approved_input_references(
        approved_input_references
    )
    provisional = ModelCandidateSetManifest(
        schema_version=MODEL_CANDIDATE_SET_SCHEMA_VERSION,
        project_id=project_id,
        candidate_set_id=candidate_set_id,
        predecessor_candidate_set_id=predecessor_candidate_set_id,
        regeneration_reason=regeneration_reason,
        approved_input_references=normalized_inputs,
        approved_input_snapshot_fingerprint=(
            calculate_approved_input_snapshot_fingerprint(
                normalized_inputs
            )
        ),
        framework_template_reference=parse_framework_template_reference(
            framework_template_reference_payload(
                framework_template_reference
            )
        ),
        model_structure_profile_reference=(
            parse_model_structure_profile_reference(
                model_structure_profile_reference_payload(
                    model_structure_profile_reference
                )
            )
        ),
        derivation_rules_reference=parse_derivation_rules_reference(
            derivation_rules_reference_payload(
                derivation_rules_reference
            )
        ),
        generation_provenance=parse_generation_provenance(
            generation_provenance_payload(generation_provenance)
        ),
        element_candidate_ids=tuple(sorted(element_candidate_ids)),
        relationship_candidate_ids=tuple(
            sorted(relationship_candidate_ids)
        ),
        created_at=created_at,
        content_fingerprint="0" * 64,
    )
    manifest = replace(
        provisional,
        content_fingerprint=calculate_model_candidate_set_fingerprint(
            provisional
        ),
    )
    validate_model_candidate_set_manifest(manifest)
    return manifest


def calculate_model_candidate_set_fingerprint(
    manifest: ModelCandidateSetManifest,
) -> str:
    """Calculate identity-independent Candidate Set content fingerprint."""

    _validate_manifest(manifest, verify_fingerprint=False)
    payload = _payload(manifest)
    payload.pop("candidate_set_id")
    payload.pop("content_fingerprint")
    payload.pop("created_at")
    return canonical_fingerprint(payload)


def validate_model_candidate_set_manifest(
    manifest: ModelCandidateSetManifest,
) -> None:
    _validate_manifest(manifest, verify_fingerprint=True)


def model_candidate_set_manifest_to_dict(
    manifest: ModelCandidateSetManifest,
) -> dict[str, object]:
    validate_model_candidate_set_manifest(manifest)
    return _payload(manifest)


def model_candidate_set_manifest_to_json(
    manifest: ModelCandidateSetManifest,
) -> str:
    return deterministic_json(
        model_candidate_set_manifest_to_dict(manifest)
    )


def model_candidate_set_manifest_from_json(
    text_value: object,
    *,
    expected_project_id: str | None = None,
    expected_candidate_set_id: str | None = None,
) -> ModelCandidateSetManifest:
    return parse_model_candidate_set_manifest(
        strict_json_loads(
            text_value,
            label="Model Candidate Set Manifest",
        ),
        expected_project_id=expected_project_id,
        expected_candidate_set_id=expected_candidate_set_id,
    )


def parse_model_candidate_set_manifest(
    payload: object,
    *,
    expected_project_id: str | None = None,
    expected_candidate_set_id: str | None = None,
) -> ModelCandidateSetManifest:
    data = exact_object(
        payload,
        expected_fields=_FIELDS,
        label="Model Candidate Set Manifest",
    )
    for name in (
        "approved_input_references",
        "element_candidate_ids",
        "relationship_candidate_ids",
    ):
        if not isinstance(data[name], list):
            raise ModelCandidateValidationError(
                f"{name} must be a JSON array."
            )

    manifest = ModelCandidateSetManifest(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        candidate_set_id=data["candidate_set_id"],
        predecessor_candidate_set_id=data[
            "predecessor_candidate_set_id"
        ],
        regeneration_reason=data["regeneration_reason"],
        approved_input_references=tuple(
            parse_approved_input_reference(item)
            for item in data["approved_input_references"]
        ),
        approved_input_snapshot_fingerprint=data[
            "approved_input_snapshot_fingerprint"
        ],
        framework_template_reference=(
            parse_framework_template_reference(
                data["framework_template_reference"]
            )
        ),
        model_structure_profile_reference=(
            parse_model_structure_profile_reference(
                data["model_structure_profile_reference"]
            )
        ),
        derivation_rules_reference=parse_derivation_rules_reference(
            data["derivation_rules_reference"]
        ),
        generation_provenance=parse_generation_provenance(
            data["generation_provenance"]
        ),
        element_candidate_ids=tuple(data["element_candidate_ids"]),
        relationship_candidate_ids=tuple(
            data["relationship_candidate_ids"]
        ),
        created_at=data["created_at"],
        content_fingerprint=data["content_fingerprint"],
    )
    _validate_manifest(manifest, verify_fingerprint=True)

    if (
        expected_project_id is not None
        and manifest.project_id != expected_project_id
    ):
        raise ModelCandidateValidationError(
            "project_id does not match expected project."
        )
    if (
        expected_candidate_set_id is not None
        and manifest.candidate_set_id != expected_candidate_set_id
    ):
        raise ModelCandidateValidationError(
            "candidate_set_id does not match expected Candidate Set."
        )
    return manifest


def _validate_manifest(
    manifest: ModelCandidateSetManifest,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(manifest, ModelCandidateSetManifest):
        raise ModelCandidateValidationError(
            "manifest must be a ModelCandidateSetManifest."
        )
    if manifest.schema_version != MODEL_CANDIDATE_SET_SCHEMA_VERSION:
        raise ModelCandidateValidationError(
            "Invalid Model Candidate Set schema_version."
        )
    validate_project_id(manifest.project_id)
    candidate_set_id = validate_model_candidate_set_id(
        manifest.candidate_set_id
    )

    predecessor = manifest.predecessor_candidate_set_id
    reason = manifest.regeneration_reason
    if predecessor is None:
        if reason is not None:
            raise ModelCandidateIntegrityError(
                "regeneration_reason requires a predecessor Candidate Set."
            )
    else:
        predecessor = validate_model_candidate_set_id(predecessor)
        if predecessor == candidate_set_id:
            raise ModelCandidateIntegrityError(
                "A Candidate Set must not reference itself as predecessor."
            )
        if optional_text(reason, label="regeneration_reason") is None:
            raise ModelCandidateIntegrityError(
                "A regenerated Candidate Set requires regeneration_reason."
            )

    normalized_inputs = normalize_approved_input_references(
        manifest.approved_input_references
    )
    if normalized_inputs != manifest.approved_input_references:
        raise ModelCandidateValidationError(
            "approved_input_references must use deterministic ID order."
        )

    expected_snapshot = calculate_approved_input_snapshot_fingerprint(
        manifest.approved_input_references
    )
    if (
        sha256(
            manifest.approved_input_snapshot_fingerprint,
            label="approved_input_snapshot_fingerprint",
        )
        != expected_snapshot
    ):
        raise ModelCandidateIntegrityError(
            "approved_input_snapshot_fingerprint does not match references."
        )

    parse_framework_template_reference(
        framework_template_reference_payload(
            manifest.framework_template_reference
        )
    )
    parse_model_structure_profile_reference(
        model_structure_profile_reference_payload(
            manifest.model_structure_profile_reference
        )
    )
    parse_derivation_rules_reference(
        derivation_rules_reference_payload(
            manifest.derivation_rules_reference
        )
    )
    parse_generation_provenance(
        generation_provenance_payload(
            manifest.generation_provenance
        )
    )

    _validate_candidate_ids(
        manifest.element_candidate_ids,
        validator=validate_model_element_candidate_id,
        label="element_candidate_ids",
    )
    _validate_candidate_ids(
        manifest.relationship_candidate_ids,
        validator=validate_model_relationship_candidate_id,
        label="relationship_candidate_ids",
    )
    timestamp(manifest.created_at, label="created_at")
    sha256(manifest.content_fingerprint, label="content_fingerprint")

    if verify_fingerprint:
        expected = calculate_model_candidate_set_fingerprint(manifest)
        if manifest.content_fingerprint != expected:
            raise ModelCandidateIntegrityError(
                "Model Candidate Set content_fingerprint does not match."
            )


def _validate_candidate_ids(
    values: tuple[str, ...],
    *,
    validator: Callable[[object], str],
    label: str,
) -> None:
    if not isinstance(values, tuple):
        raise ModelCandidateValidationError(
            f"{label} must be a tuple."
        )
    try:
        checked = tuple(validator(item) for item in values)
    except Exception as exc:
        raise ModelCandidateValidationError(
            f"{label} contains an invalid candidate ID."
        ) from exc
    if checked != tuple(sorted(checked)):
        raise ModelCandidateValidationError(
            f"{label} must use deterministic sorted order."
        )
    if len(checked) != len(set(checked)):
        raise ModelCandidateIntegrityError(
            f"{label} must contain unique candidate IDs."
        )


def _payload(
    manifest: ModelCandidateSetManifest,
) -> dict[str, object]:
    return {
        "schema_version": manifest.schema_version,
        "project_id": manifest.project_id,
        "candidate_set_id": manifest.candidate_set_id,
        "predecessor_candidate_set_id": (
            manifest.predecessor_candidate_set_id
        ),
        "regeneration_reason": manifest.regeneration_reason,
        "approved_input_references": [
            approved_input_reference_payload(item)
            for item in manifest.approved_input_references
        ],
        "approved_input_snapshot_fingerprint": (
            manifest.approved_input_snapshot_fingerprint
        ),
        "framework_template_reference": (
            framework_template_reference_payload(
                manifest.framework_template_reference
            )
        ),
        "model_structure_profile_reference": (
            model_structure_profile_reference_payload(
                manifest.model_structure_profile_reference
            )
        ),
        "derivation_rules_reference": (
            derivation_rules_reference_payload(
                manifest.derivation_rules_reference
            )
        ),
        "generation_provenance": generation_provenance_payload(
            manifest.generation_provenance
        ),
        "element_candidate_ids": list(manifest.element_candidate_ids),
        "relationship_candidate_ids": list(
            manifest.relationship_candidate_ids
        ),
        "created_at": manifest.created_at,
        "content_fingerprint": manifest.content_fingerprint,
    }
