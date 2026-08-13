"""Strict immutable manifest contract for Internal Model Structure."""

from __future__ import annotations

from ._manifest_support import (
    canonical_fingerprint,
    deterministic_json,
    exact_object,
    framework_template_reference_payload,
    identifier,
    parse_framework_template_reference,
    sha256,
    strict_json_loads,
    text,
    validate_project_id,
)
from .errors import InternalModelIntegrityError, InternalModelValidationError
from .identifiers import (
    validate_internal_engineering_model_id,
    validate_internal_model_element_id,
)
from .types import InternalModelStructure, InternalModelStructureNode


INTERNAL_MODEL_STRUCTURE_SCHEMA_VERSION = "1.0.0"


def create_internal_model_structure(
    *,
    project_id: str,
    internal_engineering_model_id: str,
    framework_template_reference,
    nodes,
) -> InternalModelStructure:
    provisional = InternalModelStructure(
        schema_version=INTERNAL_MODEL_STRUCTURE_SCHEMA_VERSION,
        project_id=project_id,
        internal_engineering_model_id=internal_engineering_model_id,
        framework_template_reference=framework_template_reference,
        nodes=tuple(nodes),
        content_fingerprint="0" * 64,
    )
    checked = _validated_without_fingerprint(provisional)
    result = InternalModelStructure(
        schema_version=checked.schema_version,
        project_id=checked.project_id,
        internal_engineering_model_id=checked.internal_engineering_model_id,
        framework_template_reference=checked.framework_template_reference,
        nodes=checked.nodes,
        content_fingerprint=calculate_internal_model_structure_fingerprint(
            checked
        ),
    )
    return validate_internal_model_structure(result)


def calculate_internal_model_structure_fingerprint(
    value: InternalModelStructure,
) -> str:
    return canonical_fingerprint(_payload(value, include_fingerprint=False))


def validate_internal_model_structure(
    value: InternalModelStructure,
) -> InternalModelStructure:
    checked = _validated_without_fingerprint(value)
    fingerprint = sha256(
        value.content_fingerprint,
        label="content_fingerprint",
    )
    if fingerprint != calculate_internal_model_structure_fingerprint(checked):
        raise InternalModelIntegrityError(
            "Internal Model Structure content_fingerprint mismatch."
        )
    return value


def internal_model_structure_to_dict(
    value: InternalModelStructure,
) -> dict[str, object]:
    validate_internal_model_structure(value)
    return _payload(value, include_fingerprint=True)


def internal_model_structure_to_json(
    value: InternalModelStructure,
) -> str:
    return deterministic_json(internal_model_structure_to_dict(value))


def internal_model_structure_from_json(
    text_value: object,
) -> InternalModelStructure:
    return parse_internal_model_structure(
        strict_json_loads(text_value, label="Internal Model Structure")
    )


def parse_internal_model_structure(value: object) -> InternalModelStructure:
    data = exact_object(
        value,
        expected_fields=frozenset(
            InternalModelStructure.__dataclass_fields__
        ),
        label="Internal Model Structure",
    )
    raw_nodes = data["nodes"]
    if not isinstance(raw_nodes, list):
        raise InternalModelValidationError(
            "nodes must be a JSON array."
        )
    result = InternalModelStructure(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        internal_engineering_model_id=data["internal_engineering_model_id"],
        framework_template_reference=parse_framework_template_reference(
            data["framework_template_reference"]
        ),
        nodes=tuple(_parse_node(item) for item in raw_nodes),
        content_fingerprint=data["content_fingerprint"],
    )
    return validate_internal_model_structure(result)


def _validated_without_fingerprint(
    value: InternalModelStructure,
) -> InternalModelStructure:
    if not isinstance(value, InternalModelStructure):
        raise InternalModelValidationError(
            "value must be InternalModelStructure."
        )
    if value.schema_version != INTERNAL_MODEL_STRUCTURE_SCHEMA_VERSION:
        raise InternalModelValidationError(
            "Unsupported Internal Model Structure schema_version."
        )
    validate_project_id(value.project_id)
    validate_internal_engineering_model_id(
        value.internal_engineering_model_id
    )
    template = parse_framework_template_reference(
        framework_template_reference_payload(
            value.framework_template_reference
        )
    )

    node_ids = []
    all_element_ids = []
    for node in value.nodes:
        _validate_node(node)
        node_ids.append(node.framework_node_id)
        all_element_ids.extend(node.internal_model_element_ids)
    if len(node_ids) != len(set(node_ids)):
        raise InternalModelIntegrityError(
            "Structure framework_node_id values must be unique."
        )

    known = set(node_ids)
    for node in value.nodes:
        parent = node.parent_framework_node_id
        if parent is not None and parent not in known:
            raise InternalModelIntegrityError(
                f"Structure node has unknown parent: {parent}."
            )
        if parent == node.framework_node_id:
            raise InternalModelIntegrityError(
                "Structure node cannot be its own parent."
            )

    if len(all_element_ids) != len(set(all_element_ids)):
        raise InternalModelIntegrityError(
            "An IME may belong to only one structure node."
        )

    return InternalModelStructure(
        schema_version=value.schema_version,
        project_id=value.project_id,
        internal_engineering_model_id=value.internal_engineering_model_id,
        framework_template_reference=template,
        nodes=value.nodes,
        content_fingerprint=value.content_fingerprint,
    )


def _validate_node(node: InternalModelStructureNode) -> None:
    if not isinstance(node, InternalModelStructureNode):
        raise InternalModelValidationError(
            "nodes must contain InternalModelStructureNode values."
        )
    identifier(node.framework_node_id, label="framework_node_id")
    identifier(node.mapping_key, label="mapping_key")
    text(node.name, label="structure node name")
    identifier(node.node_type, label="node_type")
    if node.parent_framework_node_id is not None:
        identifier(
            node.parent_framework_node_id,
            label="parent_framework_node_id",
        )
    if isinstance(node.order, bool) or not isinstance(node.order, int):
        raise InternalModelValidationError(
            "structure node order must be an integer."
        )
    if node.order < 1:
        raise InternalModelValidationError(
            "structure node order must be positive."
        )

    ids = tuple(
        validate_internal_model_element_id(item)
        for item in node.internal_model_element_ids
    )
    if ids != tuple(sorted(ids)):
        raise InternalModelValidationError(
            "structure node IME IDs must use deterministic sorted order."
        )
    if len(ids) != len(set(ids)):
        raise InternalModelIntegrityError(
            "structure node IME IDs must be unique."
        )


def _node_payload(node: InternalModelStructureNode) -> dict[str, object]:
    return {
        "framework_node_id": node.framework_node_id,
        "mapping_key": node.mapping_key,
        "name": node.name,
        "node_type": node.node_type,
        "parent_framework_node_id": node.parent_framework_node_id,
        "order": node.order,
        "internal_model_element_ids": list(
            node.internal_model_element_ids
        ),
    }


def _parse_node(value: object) -> InternalModelStructureNode:
    data = exact_object(
        value,
        expected_fields=frozenset(
            InternalModelStructureNode.__dataclass_fields__
        ),
        label="Internal Model Structure Node",
    )
    raw_ids = data["internal_model_element_ids"]
    if not isinstance(raw_ids, list):
        raise InternalModelValidationError(
            "internal_model_element_ids must be a JSON array."
        )
    node = InternalModelStructureNode(
        framework_node_id=data["framework_node_id"],
        mapping_key=data["mapping_key"],
        name=data["name"],
        node_type=data["node_type"],
        parent_framework_node_id=data["parent_framework_node_id"],
        order=data["order"],
        internal_model_element_ids=tuple(raw_ids),
    )
    _validate_node(node)
    return node


def _payload(
    value: InternalModelStructure,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    payload = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "internal_engineering_model_id": value.internal_engineering_model_id,
        "framework_template_reference": (
            framework_template_reference_payload(
                value.framework_template_reference
            )
        ),
        "nodes": [_node_payload(node) for node in value.nodes],
    }
    if include_fingerprint:
        payload["content_fingerprint"] = value.content_fingerprint
    return payload
