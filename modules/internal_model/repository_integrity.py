"""Bundle-level integrity validation for Internal Engineering Model snapshots."""

from __future__ import annotations

from .element_manifest import validate_internal_model_element
from .errors import InternalModelIntegrityError, InternalModelValidationError
from .model_manifest import validate_internal_engineering_model_manifest
from .relationship_manifest import validate_internal_model_relationship
from .structure_manifest import validate_internal_model_structure
from .types import InternalEngineeringModelSnapshot


def validate_internal_engineering_model_snapshot(
    snapshot: InternalEngineeringModelSnapshot,
) -> InternalEngineeringModelSnapshot:
    """Validate one complete IEM bundle and all cross-artifact references."""

    if not isinstance(snapshot, InternalEngineeringModelSnapshot):
        raise InternalModelValidationError(
            "snapshot must be InternalEngineeringModelSnapshot."
        )

    manifest = validate_internal_engineering_model_manifest(
        snapshot.manifest
    )
    structure = validate_internal_model_structure(snapshot.structure)
    elements = tuple(
        validate_internal_model_element(item)
        for item in snapshot.elements
    )
    relationships = tuple(
        validate_internal_model_relationship(item)
        for item in snapshot.relationships
    )

    project_id = manifest.project_id
    iem_id = manifest.internal_engineering_model_id

    if (
        structure.project_id != project_id
        or structure.internal_engineering_model_id != iem_id
    ):
        raise InternalModelIntegrityError(
            "Internal Model Structure is not bound to the manifest "
            "project/IEM identity."
        )
    if (
        structure.content_fingerprint
        != manifest.structure_content_fingerprint
    ):
        raise InternalModelIntegrityError(
            "Manifest structure fingerprint does not match structure.json."
        )
    if (
        structure.framework_template_reference
        != manifest.assembly_context.framework_template_reference
    ):
        raise InternalModelIntegrityError(
            "Structure Framework Template reference does not match "
            "the IEM manifest."
        )

    element_ids = tuple(
        item.internal_model_element_id for item in elements
    )
    relationship_ids = tuple(
        item.internal_model_relationship_id for item in relationships
    )
    if element_ids != tuple(sorted(element_ids)):
        raise InternalModelIntegrityError(
            "Snapshot elements must use deterministic IME-ID order."
        )
    if relationship_ids != tuple(sorted(relationship_ids)):
        raise InternalModelIntegrityError(
            "Snapshot relationships must use deterministic IMR-ID order."
        )
    if element_ids != manifest.internal_model_element_ids:
        raise InternalModelIntegrityError(
            "Manifest IME references do not match persisted elements."
        )
    if relationship_ids != manifest.internal_model_relationship_ids:
        raise InternalModelIntegrityError(
            "Manifest IMR references do not match persisted relationships."
        )

    by_element_id = {}
    source_candidate_ids = set()
    subject_keys = set()
    for item in elements:
        if (
            item.project_id != project_id
            or item.internal_engineering_model_id != iem_id
        ):
            raise InternalModelIntegrityError(
                "IME is outside the manifest project/IEM identity."
            )
        if item.internal_model_element_id in by_element_id:
            raise InternalModelIntegrityError(
                "Duplicate IME identity in one IEM snapshot."
            )
        if item.source_model_element_candidate_id in source_candidate_ids:
            raise InternalModelIntegrityError(
                "One source MCE may map to only one IME in one snapshot."
            )
        if item.model_subject_key in subject_keys:
            raise InternalModelIntegrityError(
                "Semantic subject identities must be unique in one IEM."
            )
        by_element_id[item.internal_model_element_id] = item
        source_candidate_ids.add(item.source_model_element_candidate_id)
        subject_keys.add(item.model_subject_key)

    structure_membership = tuple(
        item
        for node in structure.nodes
        for item in node.internal_model_element_ids
    )
    if tuple(sorted(structure_membership)) != element_ids:
        raise InternalModelIntegrityError(
            "Internal Model Structure must contain every IME exactly once."
        )

    source_relationship_candidate_ids = set()
    for item in relationships:
        if (
            item.project_id != project_id
            or item.internal_engineering_model_id != iem_id
        ):
            raise InternalModelIntegrityError(
                "IMR is outside the manifest project/IEM identity."
            )
        if (
            item.source_model_relationship_candidate_id
            in source_relationship_candidate_ids
        ):
            raise InternalModelIntegrityError(
                "One source MCR may map to only one IMR in one snapshot."
            )
        source = by_element_id.get(
            item.source_internal_model_element_id
        )
        target = by_element_id.get(
            item.target_internal_model_element_id
        )
        if source is None or target is None:
            raise InternalModelIntegrityError(
                "IMR contains a dangling Internal Model Element endpoint."
            )
        if (
            source.model_subject_key != item.source_model_subject_key
            or target.model_subject_key != item.target_model_subject_key
        ):
            raise InternalModelIntegrityError(
                "IMR endpoint semantic subject keys do not match the "
                "referenced IMEs."
            )
        source_relationship_candidate_ids.add(
            item.source_model_relationship_candidate_id
        )

    exact_review_refs = tuple(
        sorted(
            (
                item.review_decision_reference
                for item in (*elements, *relationships)
            ),
            key=lambda item: item.model_candidate_review_decision_id,
        )
    )
    if exact_review_refs != manifest.review_decision_references:
        raise InternalModelIntegrityError(
            "Manifest Review Decision references do not match IME/IMR "
            "authorization references."
        )

    exact_exception_refs = tuple(
        sorted(
            (
                item.accepted_exception_reference
                for item in (*elements, *relationships)
                if item.accepted_exception_reference is not None
            ),
            key=lambda item: item.model_candidate_review_decision_id,
        )
    )
    if exact_exception_refs != manifest.accepted_exception_references:
        raise InternalModelIntegrityError(
            "Manifest accepted-exception references do not match IME/IMR "
            "exception references."
        )

    return snapshot
