"""SEM-015 authority-backed successor Internal Engineering Model.

This module applies already-final Human authority only:
- Model Quality Authority (MQA) supplies approved model-facing wording.
- Target-Model Formulation Authority (TFA) controls formal materialization.
No LLM call and no new engineering interpretation occurs here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import uuid

from modules.internal_model.authority_backed import (
    AuthorityBackedInternalModelElement,
    AuthorityBackedInternalModelRelationship,
    AuthorityBackedInternalModelSnapshot,
    AuthorityBackedInternalModelStructureNode,
    AuthorityBackedInternalModelRepository,
    authority_backed_internal_model_to_json,
)
from modules.model_placement.errors import ModelPlacementContractError


SEM015_SUCCESSOR_INTERNAL_MODEL_SCHEMA_VERSION = "2.1.0"
SEM015_AUTHORITY_BINDING_SCHEMA_VERSION = "1.0.0"
SEM015_AUTHORITY_MANIFEST_SCHEMA_VERSION = "1.0.0"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IEM = re.compile(r"^IEM-[0-9]{6}$")


@dataclass(frozen=True, slots=True)
class SemanticSuccessorResult:
    snapshot: AuthorityBackedInternalModelSnapshot
    authority_manifest: dict


def build_sem015_internal_model_successor(
    *,
    source: AuthorityBackedInternalModelSnapshot,
    target_model_formulation_authority: dict,
    model_quality_authority: dict,
    internal_engineering_model_id: str,
    created_at: str | None = None,
) -> SemanticSuccessorResult:
    """Apply exact Human-authorized formulation and quality decisions."""

    if not _IEM.fullmatch(internal_engineering_model_id):
        raise ModelPlacementContractError(
            "SEM-015 successor Internal Engineering Model ID is invalid."
        )
    if internal_engineering_model_id == source.internal_engineering_model_id:
        raise ModelPlacementContractError(
            "SEM-015 successor must use a new Internal Engineering Model ID."
        )
    if source.source_internal_engineering_model_id is not None:
        raise ModelPlacementContractError(
            "SEM-015 successor currently requires the reviewed base IEM as source."
        )

    tfa = _validate_authority_set(
        target_model_formulation_authority,
        expected_prefix="TFA-",
        source=source,
        label="Target-Model Formulation authority",
    )
    mqa = _validate_authority_set(
        model_quality_authority,
        expected_prefix="MQA-",
        source=source,
        label="Model Quality authority",
    )

    quality_by_element = {}
    for decision in mqa["effective_decisions"]:
        element_id = decision.get("internal_model_element_id")
        if element_id in quality_by_element:
            raise ModelPlacementContractError(
                "Model Quality authority contains duplicate element decisions."
            )
        if decision.get("decision") not in {"approved", "overridden"}:
            raise ModelPlacementContractError(
                "SEM-015 successor requires approved or overridden quality decisions."
            )
        if not isinstance(decision.get("approved_name"), str) or not decision[
            "approved_name"
        ].strip():
            raise ModelPlacementContractError(
                "Model Quality authority is missing approved model-facing wording."
            )
        quality_by_element[element_id] = decision

    source_element_ids = {
        item.internal_model_element_id for item in source.elements
    }
    if set(quality_by_element) != source_element_ids:
        raise ModelPlacementContractError(
            "Model Quality authority must cover the exact source IEM element population."
        )

    formulation_by_subject = {}
    for decision in tfa["effective_decisions"]:
        subject_id = decision.get("authority_subject_id")
        if subject_id in formulation_by_subject:
            raise ModelPlacementContractError(
                "Target-Model Formulation authority contains duplicate subjects."
            )
        formulation_by_subject[subject_id] = decision

    omitted_element_ids = {
        subject_id
        for subject_id, decision in formulation_by_subject.items()
        if decision.get("subject_kind") == "element"
        and decision.get("selected_relevance_outcome")
        in {"retain_as_context_only", "intentionally_not_materialized"}
    }

    elements = []
    retained_element_ids = set()
    for source_element in source.elements:
        element_id = source_element.internal_model_element_id
        if element_id in omitted_element_ids:
            continue
        decision = quality_by_element[element_id]
        payload = {
            "internal_model_element_id": element_id,
            "model_subject_key": source_element.model_subject_key,
            "approved_input_id": source_element.approved_input_id,
            "name": decision["approved_name"].strip(),
            "description": _optional_text(decision.get("approved_description")),
            "model_area": source_element.model_area,
            "element_type": source_element.element_type,
            "framework_assignment": source_element.framework_assignment,
            "placement_authority": _authority_payload(
                source_element.placement_authority
            ),
        }
        elements.append(
            AuthorityBackedInternalModelElement(
                internal_model_element_id=element_id,
                model_subject_key=source_element.model_subject_key,
                approved_input_id=source_element.approved_input_id,
                name=payload["name"],
                description=payload["description"],
                model_area=source_element.model_area,
                element_type=source_element.element_type,
                framework_assignment=source_element.framework_assignment,
                placement_authority=source_element.placement_authority,
                content_fingerprint=_fingerprint(payload),
            )
        )
        retained_element_ids.add(element_id)

    omitted_relationship_ids = set()
    relationships = []
    for relationship in source.relationships:
        relationship_id = relationship.internal_model_relationship_id
        formulation = formulation_by_subject.get(relationship_id)
        if (
            formulation is not None
            and formulation.get("subject_kind") == "relationship"
            and formulation.get("selected_relevance_outcome")
            in {"retain_as_context_only", "intentionally_not_materialized"}
        ):
            omitted_relationship_ids.add(relationship_id)
            continue
        if (
            relationship.source_internal_model_element_id
            not in retained_element_ids
            or relationship.target_internal_model_element_id
            not in retained_element_ids
        ):
            omitted_relationship_ids.add(relationship_id)
            continue
        relationships.append(relationship)

    structure_nodes = tuple(
        AuthorityBackedInternalModelStructureNode(
            framework_node_id=node.framework_node_id,
            mapping_key=node.mapping_key,
            name=node.name,
            node_type=node.node_type,
            parent_framework_node_id=node.parent_framework_node_id,
            order=node.order,
            internal_model_element_ids=tuple(
                element_id
                for element_id in node.internal_model_element_ids
                if element_id in retained_element_ids
            ),
        )
        for node in source.structure_nodes
    )

    tfa_decision_refs = [
        {
            "subject_kind": item["subject_kind"],
            "authority_subject_id": item["authority_subject_id"],
            "decision_id": item["decision_id"],
            "decision_fingerprint": item["content_fingerprint"],
            "relevance_outcome": item["selected_relevance_outcome"],
            "target_notation_construct_id": item.get(
                "selected_target_notation_construct_id"
            ),
        }
        for item in tfa["effective_decisions"]
    ]
    quality_decision_refs = [
        {
            "internal_model_element_id": item["internal_model_element_id"],
            "decision_id": item["decision_id"],
            "decision_fingerprint": item["content_fingerprint"],
        }
        for item in mqa["effective_decisions"]
    ]

    binding_body = {
        "schema_version": SEM015_AUTHORITY_BINDING_SCHEMA_VERSION,
        "project_id": source.project_id,
        "source_internal_engineering_model_id": (
            source.internal_engineering_model_id
        ),
        "source_internal_engineering_model_fingerprint": (
            source.content_fingerprint
        ),
        "target_model_formulation_authority_set_id": tfa["authority_set_id"],
        "target_model_formulation_authority_fingerprint": (
            tfa["content_fingerprint"]
        ),
        "model_quality_authority_set_id": mqa["authority_set_id"],
        "model_quality_authority_fingerprint": mqa["content_fingerprint"],
        "target_model_formulation_decisions": sorted(
            tfa_decision_refs,
            key=lambda item: (
                item["subject_kind"],
                item["authority_subject_id"],
            ),
        ),
        "model_quality_decisions": sorted(
            quality_decision_refs,
            key=lambda item: item["internal_model_element_id"],
        ),
        "intentionally_not_materialized_element_ids": sorted(
            omitted_element_ids
        ),
        "intentionally_not_materialized_relationship_ids": sorted(
            omitted_relationship_ids
        ),
    }
    authority_binding_fingerprint = _fingerprint(binding_body)
    created = created_at or _timestamp()

    snapshot_body = {
        "schema_version": SEM015_SUCCESSOR_INTERNAL_MODEL_SCHEMA_VERSION,
        "project_id": source.project_id,
        "internal_engineering_model_id": internal_engineering_model_id,
        "comparison_fingerprint": source.comparison_fingerprint,
        "assembly_draft_fingerprint": source.assembly_draft_fingerprint,
        "approved_placement_set_fingerprint": (
            source.approved_placement_set_fingerprint
        ),
        "approved_engineering_information_fingerprint": (
            source.approved_engineering_information_fingerprint
        ),
        "final_model_review_decision_id": (
            source.final_model_review_decision_id
        ),
        "final_model_review_decision_fingerprint": (
            source.final_model_review_decision_fingerprint
        ),
        "profile_id": source.profile_id,
        "profile_version": source.profile_version,
        "profile_fingerprint": source.profile_fingerprint,
        "framework_template_id": source.framework_template_id,
        "framework_template_version": source.framework_template_version,
        "elements": [_element_payload(item) for item in elements],
        "relationships": [
            _relationship_payload(item) for item in relationships
        ],
        "structure_nodes": [
            _structure_payload(item) for item in structure_nodes
        ],
        "created_at": created,
        "source_internal_engineering_model_id": (
            source.internal_engineering_model_id
        ),
        "source_internal_engineering_model_fingerprint": (
            source.content_fingerprint
        ),
        "semantic_successor_authority_fingerprint": (
            authority_binding_fingerprint
        ),
    }
    snapshot = AuthorityBackedInternalModelSnapshot(
        schema_version=SEM015_SUCCESSOR_INTERNAL_MODEL_SCHEMA_VERSION,
        project_id=source.project_id,
        internal_engineering_model_id=internal_engineering_model_id,
        comparison_fingerprint=source.comparison_fingerprint,
        assembly_draft_fingerprint=source.assembly_draft_fingerprint,
        approved_placement_set_fingerprint=(
            source.approved_placement_set_fingerprint
        ),
        approved_engineering_information_fingerprint=(
            source.approved_engineering_information_fingerprint
        ),
        final_model_review_decision_id=(
            source.final_model_review_decision_id
        ),
        final_model_review_decision_fingerprint=(
            source.final_model_review_decision_fingerprint
        ),
        profile_id=source.profile_id,
        profile_version=source.profile_version,
        profile_fingerprint=source.profile_fingerprint,
        framework_template_id=source.framework_template_id,
        framework_template_version=source.framework_template_version,
        elements=tuple(elements),
        relationships=tuple(relationships),
        structure_nodes=structure_nodes,
        created_at=created,
        content_fingerprint=_fingerprint(snapshot_body),
        source_internal_engineering_model_id=(
            source.internal_engineering_model_id
        ),
        source_internal_engineering_model_fingerprint=(
            source.content_fingerprint
        ),
        semantic_successor_authority_fingerprint=(
            authority_binding_fingerprint
        ),
    )

    manifest_body = {
        "schema_version": SEM015_AUTHORITY_MANIFEST_SCHEMA_VERSION,
        "project_id": source.project_id,
        "successor_internal_engineering_model_id": (
            internal_engineering_model_id
        ),
        "successor_iem_content_fingerprint": snapshot.content_fingerprint,
        "authority_binding": binding_body,
        "authority_binding_fingerprint": authority_binding_fingerprint,
        "created_at": created,
    }
    manifest = {
        **manifest_body,
        "content_fingerprint": _fingerprint(manifest_body),
    }
    return SemanticSuccessorResult(
        snapshot=snapshot,
        authority_manifest=manifest,
    )


class SEM015InternalModelSuccessorRepository:
    """Atomically persist a 2.1 successor snapshot plus its authority manifest."""

    def __init__(self, root=Path("data/projects")):
        self.root = Path(root)
        self._base = AuthorityBackedInternalModelRepository(self.root)

    def materialize(
        self,
        *,
        source,
        target_model_formulation_authority,
        model_quality_authority,
    ):
        existing = self.find_exact(
            source=source,
            target_model_formulation_authority=(
                target_model_formulation_authority
            ),
            model_quality_authority=model_quality_authority,
        )
        if existing is not None:
            return existing

        iem_id = self._next_iem_id(source.project_id)
        result = build_sem015_internal_model_successor(
            source=source,
            target_model_formulation_authority=(
                target_model_formulation_authority
            ),
            model_quality_authority=model_quality_authority,
            internal_engineering_model_id=iem_id,
        )

        parent = self.root / source.project_id / "internal_models_v2"
        directory = parent / iem_id
        parent.mkdir(parents=True, exist_ok=True)
        if directory.exists() or directory.is_symlink():
            raise ModelPlacementContractError(
                "SEM-015 successor Internal Model path is occupied."
            )
        temp = parent / f".{iem_id}.tmp-{uuid.uuid4().hex}"
        temp.mkdir()
        (temp / "snapshot.json").write_text(
            authority_backed_internal_model_to_json(result.snapshot),
            encoding="utf-8",
        )
        (temp / "semantic_authority.json").write_text(
            json.dumps(
                result.authority_manifest,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        temp.replace(directory)
        return self._base.load(source.project_id, iem_id)

    def find_exact(
        self,
        *,
        source,
        target_model_formulation_authority,
        model_quality_authority,
    ):
        directory = self.root / source.project_id / "internal_models_v2"
        if not directory.exists():
            return None
        matches = []
        for entry in sorted(directory.iterdir(), key=lambda item: item.name):
            if entry.is_symlink() or not entry.is_dir():
                raise ModelPlacementContractError(
                    "Unexpected Authority-backed Internal Model entry."
                )
            sidecar = entry / "semantic_authority.json"
            if not sidecar.is_file() or sidecar.is_symlink():
                continue
            raw = json.loads(sidecar.read_text(encoding="utf-8"))
            binding = raw.get("authority_binding", {})
            if (
                binding.get("source_internal_engineering_model_id")
                == source.internal_engineering_model_id
                and binding.get(
                    "source_internal_engineering_model_fingerprint"
                )
                == source.content_fingerprint
                and binding.get(
                    "target_model_formulation_authority_set_id"
                )
                == target_model_formulation_authority.get("authority_set_id")
                and binding.get(
                    "target_model_formulation_authority_fingerprint"
                )
                == target_model_formulation_authority.get(
                    "content_fingerprint"
                )
                and binding.get("model_quality_authority_set_id")
                == model_quality_authority.get("authority_set_id")
                and binding.get("model_quality_authority_fingerprint")
                == model_quality_authority.get("content_fingerprint")
            ):
                matches.append(self._base.load(source.project_id, entry.name))
        if len(matches) > 1:
            raise ModelPlacementContractError(
                "Multiple SEM-015 successor models bind the same exact authority."
            )
        return None if not matches else matches[0]

    def _next_iem_id(self, project_id):
        occupied = []
        for dirname in ("internal_models", "internal_models_v2"):
            directory = self.root / project_id / dirname
            if not directory.exists():
                continue
            if directory.is_symlink() or not directory.is_dir():
                raise ModelPlacementContractError(
                    "Internal Model repository root is unsafe."
                )
            for entry in directory.iterdir():
                match = _IEM.fullmatch(entry.name)
                if match is not None:
                    occupied.append(int(entry.name.split("-")[1]))
        number = max(occupied, default=0) + 1
        if number > 999999:
            raise ModelPlacementContractError(
                "Internal Engineering Model ID space exhausted."
            )
        return f"IEM-{number:06d}"


def load_authority_json(path: Path | str) -> dict:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ModelPlacementContractError(
            f"Authority artifact not found: {path}"
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ModelPlacementContractError(
            f"Authority artifact is invalid JSON: {path}"
        ) from exc


def _validate_authority_set(payload, *, expected_prefix, source, label):
    if not isinstance(payload, dict):
        raise ModelPlacementContractError(f"{label} is not an object.")
    authority_id = payload.get("authority_set_id")
    if (
        not isinstance(authority_id, str)
        or not authority_id.startswith(expected_prefix)
    ):
        raise ModelPlacementContractError(f"{label} ID is invalid.")
    if (
        payload.get("project_id") != source.project_id
        or payload.get("source_internal_engineering_model_id")
        != source.internal_engineering_model_id
        or payload.get("source_internal_engineering_model_fingerprint")
        != source.content_fingerprint
    ):
        raise ModelPlacementContractError(
            f"{label} does not bind the exact source IEM."
        )
    _verify_fingerprinted_payload(payload, label)
    decisions = payload.get("effective_decisions")
    if not isinstance(decisions, list) or not decisions:
        raise ModelPlacementContractError(
            f"{label} requires effective Human decisions."
        )
    for decision in decisions:
        _verify_fingerprinted_payload(
            decision,
            f"{label} decision",
        )
    return payload


def _verify_fingerprinted_payload(payload, label):
    if not isinstance(payload, dict):
        raise ModelPlacementContractError(f"{label} is invalid.")
    fingerprint = payload.get("content_fingerprint")
    if not isinstance(fingerprint, str) or _SHA256.fullmatch(fingerprint) is None:
        raise ModelPlacementContractError(f"{label} fingerprint is invalid.")
    body = dict(payload)
    body.pop("content_fingerprint", None)
    if _fingerprint(body) != fingerprint:
        raise ModelPlacementContractError(
            f"{label} fingerprint does not match its content."
        )


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


def _optional_text(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ModelPlacementContractError(
            "Approved model description must be text or null."
        )
    return value.strip() or None


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
