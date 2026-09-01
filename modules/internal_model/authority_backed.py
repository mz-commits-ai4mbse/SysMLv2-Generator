"""Authority-backed Internal Engineering Model v2.

This path materializes an approved Model Assembly Draft directly from
Human Model Placement + whole-model Final Review authority. It deliberately
does not synthesize legacy Model Candidate Review decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import uuid

from modules.model_placement.errors import ModelPlacementContractError


AUTHORITY_BACKED_INTERNAL_MODEL_SCHEMA_VERSION = "2.0.0"
AUTHORITY_BACKED_PROJECT_AUTHORITY_SCHEMA_VERSION = "2.2.0"
_IEM = re.compile(r"^IEM-([0-9]{6})$")
_IME = re.compile(r"^IME-[0-9]{6}$")
_IMR = re.compile(r"^IMR-[0-9]{6}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class InternalModelAuthorityReference:
    authority_type: str
    authority_id: str
    authority_fingerprint: str


@dataclass(frozen=True, slots=True)
class AuthorityBackedInternalModelElement:
    internal_model_element_id: str
    model_subject_key: str
    approved_input_id: str
    name: str
    description: str | None
    model_area: str
    element_type: str
    framework_assignment: str
    placement_authority: InternalModelAuthorityReference
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class AuthorityBackedInternalModelRelationship:
    internal_model_relationship_id: str
    source_internal_model_element_id: str
    target_internal_model_element_id: str
    source_model_subject_key: str
    target_model_subject_key: str
    semantic_intent: str
    relationship_family: str
    directionality: str
    engineering_relationship_authority: InternalModelAuthorityReference
    final_representation_authority: InternalModelAuthorityReference
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class AuthorityBackedInternalModelStructureNode:
    framework_node_id: str
    mapping_key: str
    name: str
    node_type: str
    parent_framework_node_id: str | None
    order: int
    internal_model_element_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AuthorityBackedInternalModelSnapshot:
    schema_version: str
    project_id: str
    internal_engineering_model_id: str
    comparison_fingerprint: str
    assembly_draft_fingerprint: str
    approved_placement_set_fingerprint: str
    approved_engineering_information_fingerprint: str | None
    final_model_review_decision_id: str
    final_model_review_decision_fingerprint: str
    profile_id: str
    profile_version: str
    profile_fingerprint: str
    framework_template_id: str
    framework_template_version: str
    elements: tuple[AuthorityBackedInternalModelElement, ...]
    relationships: tuple[AuthorityBackedInternalModelRelationship, ...]
    structure_nodes: tuple[AuthorityBackedInternalModelStructureNode, ...]
    created_at: str
    content_fingerprint: str
    source_internal_engineering_model_id: str | None = None
    source_internal_engineering_model_fingerprint: str | None = None
    semantic_successor_authority_fingerprint: str | None = None
    project_authority_handoff_fingerprint: str | None = None
    project_engineering_authority_fingerprint: str | None = None
    model_impact_reconciliation_fingerprint: str | None = None
    source_approved_engineering_information_fingerprints: tuple[str, ...] = ()


def build_authority_backed_internal_model(
    *,
    draft,
    final_decision,
    profile,
    framework_template,
    internal_engineering_model_id: str,
    created_at: str | None = None,
) -> AuthorityBackedInternalModelSnapshot:
    """Materialize exact Human authority without Candidate Review synthesis."""

    _validate_iem_id(internal_engineering_model_id)
    _validate_authority_binding(
        draft=draft,
        final_decision=final_decision,
        profile=profile,
    )

    template_id = framework_template.get("template_id")
    template_version = framework_template.get("template_version")
    nodes = framework_template.get("nodes")
    if (
        not isinstance(template_id, str)
        or not isinstance(template_version, str)
        or not isinstance(nodes, list)
    ):
        raise ModelPlacementContractError(
            "Framework Template is invalid for Internal Model materialization."
        )

    profile_area_by_id = {
        item.model_area_id: item
        for item in profile.model_areas
    }
    template_node_ids = {
        item["node_id"]
        for item in nodes
        if isinstance(item, dict) and "node_id" in item
    }

    element_id_by_subject_key = {}
    elements = []
    membership = {}
    for index, element in enumerate(
        sorted(
            draft.elements,
            key=lambda item: (
                item.approved_input_id,
                item.stable_subject_key,
            ),
        ),
        start=1,
    ):
        internal_id = f"IME-{index:06d}"
        area = profile_area_by_id.get(element.model_area)
        if area is None:
            raise ModelPlacementContractError(
                "Assembly element references an unknown profile model area."
            )
        if element.framework_assignment != area.framework_node_id:
            raise ModelPlacementContractError(
                "Assembly element framework assignment conflicts with profile."
            )
        if element.framework_assignment not in template_node_ids:
            raise ModelPlacementContractError(
                "Assembly element framework assignment is absent from template."
            )
        if element.element_type not in area.permitted_element_types:
            raise ModelPlacementContractError(
                "Assembly element type is not permitted in its profile area."
            )
        if element.stable_subject_key in element_id_by_subject_key:
            raise ModelPlacementContractError(
                "Internal Model requires unique materialized Subject identity."
            )

        placement_authority = InternalModelAuthorityReference(
            authority_type="model_placement_decision",
            authority_id=element.placement_decision_id,
            authority_fingerprint=(
                element.placement_decision_fingerprint
            ),
        )
        payload = {
            "internal_model_element_id": internal_id,
            "model_subject_key": element.stable_subject_key,
            "approved_input_id": element.approved_input_id,
            "name": element.title,
            "description": element.primary_text,
            "model_area": element.model_area,
            "element_type": element.element_type,
            "framework_assignment": element.framework_assignment,
            "placement_authority": _authority_payload(
                placement_authority
            ),
        }
        elements.append(
            AuthorityBackedInternalModelElement(
                internal_model_element_id=internal_id,
                model_subject_key=element.stable_subject_key,
                approved_input_id=element.approved_input_id,
                name=element.title,
                description=element.primary_text,
                model_area=element.model_area,
                element_type=element.element_type,
                framework_assignment=element.framework_assignment,
                placement_authority=placement_authority,
                content_fingerprint=_fingerprint(payload),
            )
        )
        element_id_by_subject_key[
            element.stable_subject_key
        ] = internal_id
        membership.setdefault(
            element.framework_assignment,
            [],
        ).append(internal_id)

    resolution_by_relationship = {
        item.relationship_decision_id: item
        for item in final_decision.relationship_resolutions
    }
    if len(resolution_by_relationship) != len(
        final_decision.relationship_resolutions
    ):
        raise ModelPlacementContractError(
            "Final Model Review contains duplicate Relationship resolutions."
        )
    draft_relationship_ids = {
        item.relationship_decision_id
        for item in draft.relationships
    }
    if set(resolution_by_relationship) != draft_relationship_ids:
        raise ModelPlacementContractError(
            "Final Model Review does not resolve the exact assembled "
            "Relationship population."
        )

    semantic_by_rule = {
        f"relationship:{item.semantic_intent}": item
        for item in profile.relationship_semantics
    }
    relationships = []
    for index, relationship in enumerate(
        sorted(
            draft.relationships,
            key=lambda item: item.relationship_decision_id,
        ),
        start=1,
    ):
        resolution = resolution_by_relationship[
            relationship.relationship_decision_id
        ]
        semantic = semantic_by_rule.get(
            resolution.selected_rule_id
        )
        if semantic is None:
            raise ModelPlacementContractError(
                "Final Relationship resolution is outside the pinned profile."
            )
        source_id = element_id_by_subject_key.get(
            relationship.source_subject_key
        )
        target_id = element_id_by_subject_key.get(
            relationship.target_subject_key
        )
        if source_id is None or target_id is None:
            raise ModelPlacementContractError(
                "Final Relationship endpoint is not materialized."
            )

        engineering_authority = InternalModelAuthorityReference(
            authority_type="engineering_relationship_decision",
            authority_id=relationship.relationship_decision_id,
            authority_fingerprint=(
                relationship.relationship_decision_fingerprint
            ),
        )
        final_authority = InternalModelAuthorityReference(
            authority_type="final_model_relationship_resolution",
            authority_id=final_decision.final_assembly_decision_id,
            authority_fingerprint=resolution.content_fingerprint,
        )
        internal_id = f"IMR-{index:06d}"
        payload = {
            "internal_model_relationship_id": internal_id,
            "source_internal_model_element_id": source_id,
            "target_internal_model_element_id": target_id,
            "source_model_subject_key": (
                relationship.source_subject_key
            ),
            "target_model_subject_key": (
                relationship.target_subject_key
            ),
            "semantic_intent": semantic.semantic_intent,
            "relationship_family": semantic.relationship_family,
            "directionality": semantic.directionality,
            "engineering_relationship_authority": _authority_payload(
                engineering_authority
            ),
            "final_representation_authority": _authority_payload(
                final_authority
            ),
        }
        relationships.append(
            AuthorityBackedInternalModelRelationship(
                internal_model_relationship_id=internal_id,
                source_internal_model_element_id=source_id,
                target_internal_model_element_id=target_id,
                source_model_subject_key=(
                    relationship.source_subject_key
                ),
                target_model_subject_key=(
                    relationship.target_subject_key
                ),
                semantic_intent=semantic.semantic_intent,
                relationship_family=semantic.relationship_family,
                directionality=semantic.directionality,
                engineering_relationship_authority=(
                    engineering_authority
                ),
                final_representation_authority=final_authority,
                content_fingerprint=_fingerprint(payload),
            )
        )

    structure_nodes = []
    for node in sorted(
        nodes,
        key=lambda item: (
            item.get("order", 0),
            item.get("node_id", ""),
        ),
    ):
        required = {
            "node_id",
            "mapping_key",
            "name",
            "node_type",
            "parent_node_id",
            "order",
        }
        if not isinstance(node, dict) or not required <= set(node):
            raise ModelPlacementContractError(
                "Framework Template node is invalid."
            )
        structure_nodes.append(
            AuthorityBackedInternalModelStructureNode(
                framework_node_id=node["node_id"],
                mapping_key=node["mapping_key"],
                name=node["name"],
                node_type=node["node_type"],
                parent_framework_node_id=node["parent_node_id"],
                order=node["order"],
                internal_model_element_ids=tuple(
                    sorted(membership.get(node["node_id"], ()))
                ),
            )
        )

    created = created_at or _timestamp()
    schema_version = (
        AUTHORITY_BACKED_PROJECT_AUTHORITY_SCHEMA_VERSION
        if getattr(
            draft,
            "project_authority_handoff_fingerprint",
            None,
        ) is not None
        else AUTHORITY_BACKED_INTERNAL_MODEL_SCHEMA_VERSION
    )
    body = {
        "schema_version": schema_version,
        "project_id": draft.project_id,
        "internal_engineering_model_id": internal_engineering_model_id,
        "comparison_fingerprint": draft.comparison_fingerprint,
        "assembly_draft_fingerprint": draft.content_fingerprint,
        "approved_placement_set_fingerprint": (
            draft.approved_placement_set_fingerprint
        ),
        "approved_engineering_information_fingerprint": (
            draft.approved_engineering_information_fingerprint
        ),
        "final_model_review_decision_id": (
            final_decision.final_assembly_decision_id
        ),
        "final_model_review_decision_fingerprint": (
            final_decision.decision_fingerprint
        ),
        "profile_id": profile.profile_id,
        "profile_version": profile.profile_version,
        "profile_fingerprint": profile.profile_fingerprint,
        "framework_template_id": template_id,
        "framework_template_version": template_version,
        "elements": [
            _element_payload(item)
            for item in elements
        ],
        "relationships": [
            _relationship_payload(item)
            for item in relationships
        ],
        "structure_nodes": [
            _structure_payload(item)
            for item in structure_nodes
        ],
        "created_at": created,
    }
    _add_project_authority_binding_to_payload(body, draft)
    return AuthorityBackedInternalModelSnapshot(
        schema_version=schema_version,
        project_id=draft.project_id,
        internal_engineering_model_id=internal_engineering_model_id,
        comparison_fingerprint=draft.comparison_fingerprint,
        assembly_draft_fingerprint=draft.content_fingerprint,
        approved_placement_set_fingerprint=(
            draft.approved_placement_set_fingerprint
        ),
        approved_engineering_information_fingerprint=(
            draft.approved_engineering_information_fingerprint
        ),
        final_model_review_decision_id=(
            final_decision.final_assembly_decision_id
        ),
        final_model_review_decision_fingerprint=(
            final_decision.decision_fingerprint
        ),
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_fingerprint=profile.profile_fingerprint,
        framework_template_id=template_id,
        framework_template_version=template_version,
        elements=tuple(elements),
        relationships=tuple(relationships),
        structure_nodes=tuple(structure_nodes),
        created_at=created,
        content_fingerprint=_fingerprint(body),
        project_authority_handoff_fingerprint=getattr(
            draft,
            "project_authority_handoff_fingerprint",
            None,
        ),
        project_engineering_authority_fingerprint=getattr(
            draft,
            "project_engineering_authority_fingerprint",
            None,
        ),
        model_impact_reconciliation_fingerprint=getattr(
            draft,
            "model_impact_reconciliation_fingerprint",
            None,
        ),
        source_approved_engineering_information_fingerprints=getattr(
            draft,
            "source_approved_engineering_information_fingerprints",
            (),
        ),
    )


class AuthorityBackedInternalModelRepository:
    """Persist Internal Engineering Model v2 snapshots separately from legacy IEM."""

    def __init__(self, root=Path("data/projects")):
        self.root = Path(root)

    def materialize(
        self,
        *,
        draft,
        final_decision,
        profile,
        framework_template,
    ):
        existing = self.find_by_comparison(
            draft.project_id,
            draft.comparison_fingerprint,
        )
        if existing is not None:
            return existing

        iem_id = self._next_iem_id(draft.project_id)
        snapshot = build_authority_backed_internal_model(
            draft=draft,
            final_decision=final_decision,
            profile=profile,
            framework_template=framework_template,
            internal_engineering_model_id=iem_id,
        )
        directory = (
            self.root
            / draft.project_id
            / "internal_models_v2"
            / iem_id
        )
        directory.parent.mkdir(parents=True, exist_ok=True)
        if directory.exists() or directory.is_symlink():
            raise ModelPlacementContractError(
                "Authority-backed Internal Model path is occupied."
            )
        temp = directory.parent / (
            f".{iem_id}.tmp-{uuid.uuid4().hex}"
        )
        temp.mkdir()
        (temp / "snapshot.json").write_text(
            authority_backed_internal_model_to_json(snapshot),
            encoding="utf-8",
        )
        temp.replace(directory)
        loaded = self.load(draft.project_id, iem_id)
        if loaded != snapshot:
            raise ModelPlacementContractError(
                "Persisted Internal Model differs from materialized source."
            )
        return loaded

    def load(self, project_id: str, iem_id: str):
        _validate_iem_id(iem_id)
        path = (
            self.root
            / project_id
            / "internal_models_v2"
            / iem_id
            / "snapshot.json"
        )
        if path.is_symlink() or not path.is_file():
            raise ModelPlacementContractError(
                "Authority-backed Internal Model not found."
            )
        value = authority_backed_internal_model_from_json(
            path.read_text(encoding="utf-8")
        )
        if (
            value.project_id != project_id
            or value.internal_engineering_model_id != iem_id
        ):
            raise ModelPlacementContractError(
                "Authority-backed Internal Model binding is invalid."
            )
        if value.semantic_successor_authority_fingerprint is not None:
            self._validate_semantic_successor_sidecar(value)
        return value

    def _validate_semantic_successor_sidecar(self, value):
        path = (
            self.root
            / value.project_id
            / "internal_models_v2"
            / value.internal_engineering_model_id
            / "semantic_authority.json"
        )
        if path.is_symlink() or not path.is_file():
            raise ModelPlacementContractError(
                "SEM-015 successor authority manifest is missing."
            )
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            received = raw["content_fingerprint"]
            body = dict(raw)
            body.pop("content_fingerprint")
        except Exception as exc:
            raise ModelPlacementContractError(
                "SEM-015 successor authority manifest is invalid."
            ) from exc
        if _fingerprint(body) != received:
            raise ModelPlacementContractError(
                "SEM-015 successor authority manifest fingerprint is invalid."
            )
        if (
            raw.get("project_id") != value.project_id
            or raw.get("successor_internal_engineering_model_id")
            != value.internal_engineering_model_id
            or raw.get("successor_iem_content_fingerprint")
            != value.content_fingerprint
            or raw.get("authority_binding_fingerprint")
            != value.semantic_successor_authority_fingerprint
        ):
            raise ModelPlacementContractError(
                "SEM-015 successor authority manifest does not bind the exact IEM."
            )
        binding = raw.get("authority_binding")
        if (
            not isinstance(binding, dict)
            or _fingerprint(binding)
            != value.semantic_successor_authority_fingerprint
        ):
            raise ModelPlacementContractError(
                "SEM-015 successor authority binding fingerprint is invalid."
            )

    def find_by_comparison(
        self,
        project_id: str,
        comparison_fingerprint: str,
    ):
        directory = (
            self.root
            / project_id
            / "internal_models_v2"
        )
        if not directory.exists():
            return None
        if directory.is_symlink() or not directory.is_dir():
            raise ModelPlacementContractError(
                "Authority-backed Internal Model root is unsafe."
            )
        matches = []
        for entry in sorted(directory.iterdir(), key=lambda item: item.name):
            if not entry.is_dir() or entry.is_symlink():
                raise ModelPlacementContractError(
                    "Unexpected Authority-backed Internal Model entry."
                )
            value = self.load(project_id, entry.name)
            if (
                value.comparison_fingerprint == comparison_fingerprint
                and value.source_internal_engineering_model_id is None
            ):
                matches.append(value)
        if len(matches) > 1:
            raise ModelPlacementContractError(
                "Multiple Internal Models bind the same placement comparison."
            )
        return None if not matches else matches[0]

    def _next_iem_id(self, project_id: str):
        occupied = []
        for directory_name in ("internal_models", "internal_models_v2"):
            directory = self.root / project_id / directory_name
            if not directory.exists():
                continue
            if directory.is_symlink() or not directory.is_dir():
                raise ModelPlacementContractError(
                    "Internal Model repository root is unsafe."
                )
            for entry in directory.iterdir():
                match = _IEM.fullmatch(entry.name)
                if match is not None:
                    occupied.append(int(match.group(1)))
        sequence = 1 if not occupied else max(occupied) + 1
        if sequence > 999999:
            raise ModelPlacementContractError(
                "Internal Engineering Model ID space exhausted."
            )
        return f"IEM-{sequence:06d}"


def authority_backed_internal_model_to_json(value) -> str:
    payload = _snapshot_payload(value, include_fingerprint=True)
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def authority_backed_internal_model_from_json(text: str):
    try:
        raw = json.loads(text)
        elements = tuple(
            AuthorityBackedInternalModelElement(
                internal_model_element_id=item[
                    "internal_model_element_id"
                ],
                model_subject_key=item["model_subject_key"],
                approved_input_id=item["approved_input_id"],
                name=item["name"],
                description=item["description"],
                model_area=item["model_area"],
                element_type=item["element_type"],
                framework_assignment=item["framework_assignment"],
                placement_authority=InternalModelAuthorityReference(
                    **item["placement_authority"]
                ),
                content_fingerprint=item["content_fingerprint"],
            )
            for item in raw["elements"]
        )
        relationships = tuple(
            AuthorityBackedInternalModelRelationship(
                internal_model_relationship_id=item[
                    "internal_model_relationship_id"
                ],
                source_internal_model_element_id=item[
                    "source_internal_model_element_id"
                ],
                target_internal_model_element_id=item[
                    "target_internal_model_element_id"
                ],
                source_model_subject_key=item[
                    "source_model_subject_key"
                ],
                target_model_subject_key=item[
                    "target_model_subject_key"
                ],
                semantic_intent=item["semantic_intent"],
                relationship_family=item["relationship_family"],
                directionality=item["directionality"],
                engineering_relationship_authority=(
                    InternalModelAuthorityReference(
                        **item[
                            "engineering_relationship_authority"
                        ]
                    )
                ),
                final_representation_authority=(
                    InternalModelAuthorityReference(
                        **item[
                            "final_representation_authority"
                        ]
                    )
                ),
                content_fingerprint=item["content_fingerprint"],
            )
            for item in raw["relationships"]
        )
        structure_nodes = tuple(
            AuthorityBackedInternalModelStructureNode(
                framework_node_id=item["framework_node_id"],
                mapping_key=item["mapping_key"],
                name=item["name"],
                node_type=item["node_type"],
                parent_framework_node_id=item[
                    "parent_framework_node_id"
                ],
                order=item["order"],
                internal_model_element_ids=tuple(
                    item["internal_model_element_ids"]
                ),
            )
            for item in raw["structure_nodes"]
        )
        value = AuthorityBackedInternalModelSnapshot(
            schema_version=raw["schema_version"],
            project_id=raw["project_id"],
            internal_engineering_model_id=raw[
                "internal_engineering_model_id"
            ],
            comparison_fingerprint=raw["comparison_fingerprint"],
            assembly_draft_fingerprint=raw[
                "assembly_draft_fingerprint"
            ],
            approved_placement_set_fingerprint=raw[
                "approved_placement_set_fingerprint"
            ],
            approved_engineering_information_fingerprint=raw[
                "approved_engineering_information_fingerprint"
            ],
            final_model_review_decision_id=raw[
                "final_model_review_decision_id"
            ],
            final_model_review_decision_fingerprint=raw[
                "final_model_review_decision_fingerprint"
            ],
            profile_id=raw["profile_id"],
            profile_version=raw["profile_version"],
            profile_fingerprint=raw["profile_fingerprint"],
            framework_template_id=raw["framework_template_id"],
            framework_template_version=raw[
                "framework_template_version"
            ],
            elements=elements,
            relationships=relationships,
            structure_nodes=structure_nodes,
            created_at=raw["created_at"],
            content_fingerprint=raw["content_fingerprint"],
            source_internal_engineering_model_id=raw.get(
                "source_internal_engineering_model_id"
            ),
            source_internal_engineering_model_fingerprint=raw.get(
                "source_internal_engineering_model_fingerprint"
            ),
            semantic_successor_authority_fingerprint=raw.get(
                "semantic_successor_authority_fingerprint"
            ),
            project_authority_handoff_fingerprint=raw.get(
                "project_authority_handoff_fingerprint"
            ),
            project_engineering_authority_fingerprint=raw.get(
                "project_engineering_authority_fingerprint"
            ),
            model_impact_reconciliation_fingerprint=raw.get(
                "model_impact_reconciliation_fingerprint"
            ),
            source_approved_engineering_information_fingerprints=tuple(
                raw.get(
                    "source_approved_engineering_information_fingerprints",
                    (),
                )
            ),
        )
    except Exception as exc:
        raise ModelPlacementContractError(
            "Authority-backed Internal Model JSON violates the contract."
        ) from exc

    _validate_snapshot(value)
    return value


def _validate_authority_binding(*, draft, final_decision, profile):
    if final_decision.decision != "approved":
        raise ModelPlacementContractError(
            "Internal Model materialization requires approved Final Model Review."
        )
    if final_decision.project_id != draft.project_id:
        raise ModelPlacementContractError(
            "Final Model Review Project binding is invalid."
        )
    if (
        final_decision.comparison_fingerprint
        != draft.comparison_fingerprint
        or final_decision.assembly_draft_fingerprint
        != draft.content_fingerprint
        or final_decision.approved_placement_set_fingerprint
        != draft.approved_placement_set_fingerprint
        or final_decision.approved_engineering_information_fingerprint
        != draft.approved_engineering_information_fingerprint
        or getattr(final_decision, "project_authority_handoff_fingerprint", None)
        != getattr(draft, "project_authority_handoff_fingerprint", None)
        or getattr(final_decision, "project_engineering_authority_fingerprint", None)
        != getattr(draft, "project_engineering_authority_fingerprint", None)
        or getattr(final_decision, "model_impact_reconciliation_fingerprint", None)
        != getattr(draft, "model_impact_reconciliation_fingerprint", None)
        or getattr(final_decision, "source_approved_engineering_information_fingerprints", ())
        != getattr(draft, "source_approved_engineering_information_fingerprints", ())
    ):
        raise ModelPlacementContractError(
            "Final Model Review does not authorize the exact Assembly Draft."
        )
    if (
        profile.profile_id != draft.profile_id
        or profile.profile_version != draft.profile_version
        or profile.profile_fingerprint != draft.profile_fingerprint
    ):
        raise ModelPlacementContractError(
            "Internal Model materialization profile binding is invalid."
        )


def _validate_snapshot(value):
    if value.schema_version not in {
        AUTHORITY_BACKED_INTERNAL_MODEL_SCHEMA_VERSION,
        "2.1.0",
        AUTHORITY_BACKED_PROJECT_AUTHORITY_SCHEMA_VERSION,
    }:
        raise ModelPlacementContractError(
            "Authority-backed Internal Model schema version is unsupported."
        )
    _validate_iem_id(value.internal_engineering_model_id)
    successor_values = (
        value.source_internal_engineering_model_id,
        value.source_internal_engineering_model_fingerprint,
        value.semantic_successor_authority_fingerprint,
    )
    if value.schema_version == AUTHORITY_BACKED_INTERNAL_MODEL_SCHEMA_VERSION:
        if any(item is not None for item in successor_values):
            raise ModelPlacementContractError(
                "Base Internal Model schema must not contain SEM-015 successor authority."
            )
        _validate_project_authority_snapshot_binding(value, expected=False)
    elif value.schema_version == AUTHORITY_BACKED_PROJECT_AUTHORITY_SCHEMA_VERSION:
        if any(item is not None for item in successor_values):
            raise ModelPlacementContractError(
                "Project-authority Internal Model must not also claim SEM-015 "
                "successor authority."
            )
        _validate_project_authority_snapshot_binding(value, expected=True)
    else:
        _validate_project_authority_snapshot_binding(value, expected=False)
        if any(item is None for item in successor_values):
            raise ModelPlacementContractError(
                "SEM-015 successor Internal Model requires complete authority binding."
            )
        _validate_iem_id(value.source_internal_engineering_model_id)
        if value.source_internal_engineering_model_id == value.internal_engineering_model_id:
            raise ModelPlacementContractError(
                "SEM-015 successor cannot reference itself as source."
            )
        if (
            _SHA256.fullmatch(value.source_internal_engineering_model_fingerprint) is None
            or _SHA256.fullmatch(value.semantic_successor_authority_fingerprint) is None
        ):
            raise ModelPlacementContractError(
                "SEM-015 successor authority fingerprint is invalid."
            )
    if any(
        _IME.fullmatch(item.internal_model_element_id) is None
        for item in value.elements
    ):
        raise ModelPlacementContractError(
            "Authority-backed Internal Model Element ID is invalid."
        )
    if any(
        _IMR.fullmatch(item.internal_model_relationship_id) is None
        for item in value.relationships
    ):
        raise ModelPlacementContractError(
            "Authority-backed Internal Model Relationship ID is invalid."
        )
    body = _snapshot_payload(value, include_fingerprint=False)
    if _fingerprint(body) != value.content_fingerprint:
        raise ModelPlacementContractError(
            "Authority-backed Internal Model fingerprint is invalid."
        )
    for item in value.elements:
        payload = _element_payload(item)
        fingerprint = payload.pop("content_fingerprint")
        if _fingerprint(payload) != fingerprint:
            raise ModelPlacementContractError(
                "Authority-backed Internal Model Element fingerprint is invalid."
            )
    for item in value.relationships:
        payload = _relationship_payload(item)
        fingerprint = payload.pop("content_fingerprint")
        if _fingerprint(payload) != fingerprint:
            raise ModelPlacementContractError(
                "Authority-backed Internal Model Relationship fingerprint is invalid."
            )



def _add_project_authority_binding_to_payload(payload, value):
    handoff_fingerprint = getattr(
        value,
        "project_authority_handoff_fingerprint",
        None,
    )
    if handoff_fingerprint is None:
        return
    payload["project_authority_handoff_fingerprint"] = (
        handoff_fingerprint
    )
    payload["project_engineering_authority_fingerprint"] = (
        value.project_engineering_authority_fingerprint
    )
    payload["model_impact_reconciliation_fingerprint"] = (
        value.model_impact_reconciliation_fingerprint
    )
    payload["source_approved_engineering_information_fingerprints"] = list(
        value.source_approved_engineering_information_fingerprints
    )


def _validate_project_authority_snapshot_binding(value, *, expected):
    fields = (
        value.project_authority_handoff_fingerprint,
        value.project_engineering_authority_fingerprint,
        value.model_impact_reconciliation_fingerprint,
    )
    sources = value.source_approved_engineering_information_fingerprints
    if not expected:
        if any(item is not None for item in fields) or sources:
            raise ModelPlacementContractError(
                "This Internal Model schema must not contain Project "
                "Engineering Authority binding."
            )
        if value.approved_engineering_information_fingerprint is None:
            raise ModelPlacementContractError(
                "Legacy Internal Model requires one AEI fingerprint."
            )
        return

    if value.approved_engineering_information_fingerprint is not None:
        raise ModelPlacementContractError(
            "Project-authority Internal Model must not claim one AEI."
        )
    if any(
        not isinstance(item, str) or _SHA256.fullmatch(item) is None
        for item in fields
    ):
        raise ModelPlacementContractError(
            "Project-authority Internal Model binding is incomplete."
        )
    if (
        not sources
        or sources != tuple(sorted(sources))
        or len(sources) != len(set(sources))
        or any(
            not isinstance(item, str) or _SHA256.fullmatch(item) is None
            for item in sources
        )
    ):
        raise ModelPlacementContractError(
            "Project-authority source AEI fingerprint set is invalid."
        )

def _snapshot_payload(value, *, include_fingerprint):
    payload = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "internal_engineering_model_id": (
            value.internal_engineering_model_id
        ),
        "comparison_fingerprint": value.comparison_fingerprint,
        "assembly_draft_fingerprint": value.assembly_draft_fingerprint,
        "approved_placement_set_fingerprint": (
            value.approved_placement_set_fingerprint
        ),
        "approved_engineering_information_fingerprint": (
            value.approved_engineering_information_fingerprint
        ),
        "final_model_review_decision_id": (
            value.final_model_review_decision_id
        ),
        "final_model_review_decision_fingerprint": (
            value.final_model_review_decision_fingerprint
        ),
        "profile_id": value.profile_id,
        "profile_version": value.profile_version,
        "profile_fingerprint": value.profile_fingerprint,
        "framework_template_id": value.framework_template_id,
        "framework_template_version": value.framework_template_version,
        "elements": [
            _element_payload(item)
            for item in value.elements
        ],
        "relationships": [
            _relationship_payload(item)
            for item in value.relationships
        ],
        "structure_nodes": [
            _structure_payload(item)
            for item in value.structure_nodes
        ],
        "created_at": value.created_at,
    }
    _add_project_authority_binding_to_payload(payload, value)
    if value.source_internal_engineering_model_id is not None:
        payload["source_internal_engineering_model_id"] = (
            value.source_internal_engineering_model_id
        )
        payload["source_internal_engineering_model_fingerprint"] = (
            value.source_internal_engineering_model_fingerprint
        )
        payload["semantic_successor_authority_fingerprint"] = (
            value.semantic_successor_authority_fingerprint
        )
    if include_fingerprint:
        payload["content_fingerprint"] = value.content_fingerprint
    return payload


def _authority_payload(value):
    return {
        "authority_type": value.authority_type,
        "authority_id": value.authority_id,
        "authority_fingerprint": value.authority_fingerprint,
    }


def _element_payload(value):
    return {
        "internal_model_element_id": value.internal_model_element_id,
        "model_subject_key": value.model_subject_key,
        "approved_input_id": value.approved_input_id,
        "name": value.name,
        "description": value.description,
        "model_area": value.model_area,
        "element_type": value.element_type,
        "framework_assignment": value.framework_assignment,
        "placement_authority": _authority_payload(
            value.placement_authority
        ),
        "content_fingerprint": value.content_fingerprint,
    }


def _relationship_payload(value):
    return {
        "internal_model_relationship_id": (
            value.internal_model_relationship_id
        ),
        "source_internal_model_element_id": (
            value.source_internal_model_element_id
        ),
        "target_internal_model_element_id": (
            value.target_internal_model_element_id
        ),
        "source_model_subject_key": value.source_model_subject_key,
        "target_model_subject_key": value.target_model_subject_key,
        "semantic_intent": value.semantic_intent,
        "relationship_family": value.relationship_family,
        "directionality": value.directionality,
        "engineering_relationship_authority": _authority_payload(
            value.engineering_relationship_authority
        ),
        "final_representation_authority": _authority_payload(
            value.final_representation_authority
        ),
        "content_fingerprint": value.content_fingerprint,
    }


def _structure_payload(value):
    return {
        "framework_node_id": value.framework_node_id,
        "mapping_key": value.mapping_key,
        "name": value.name,
        "node_type": value.node_type,
        "parent_framework_node_id": value.parent_framework_node_id,
        "order": value.order,
        "internal_model_element_ids": list(
            value.internal_model_element_ids
        ),
    }


def _validate_iem_id(value):
    if _IEM.fullmatch(value) is None:
        raise ModelPlacementContractError(
            "Internal Engineering Model ID is invalid."
        )


def _timestamp():
    return datetime.now(timezone.utc).isoformat().replace(
        "+00:00",
        "Z",
    )


def _fingerprint(payload):
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
