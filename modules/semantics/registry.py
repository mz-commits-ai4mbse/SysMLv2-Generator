"""Load and validate the curated Ontology Registry.

The registry points only to reviewed local snapshots. This module performs no
network access, ontology download, semantic inference or automatic update.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from modules.semantics.errors import (
    OntologyRegistryError,
    OntologySnapshotIntegrityError,
    OntologySnapshotNotFoundError,
    UnsupportedOntologySerializationError,
)
from modules.semantics.types import (
    Checksum,
    LicenseReference,
    OntologyArtifact,
    OntologyReferenceSystem,
    OntologyRegistry,
    ReferenceConceptIndexConfiguration,
    RegistryAuthority,
    RuntimeBoundary,
    SourceAuthority,
)
from modules.semantics.validation import (
    calculate_file_sha256,
    object_without_duplicate_keys,
    require_boolean,
    require_exact_object,
    require_git_sha,
    require_http_url,
    require_identifier,
    require_list,
    require_positive_integer,
    require_repository_path,
    require_semantic_version,
    require_sha256,
    require_source_path,
    require_string,
    require_unique,
    resolve_repository_path,
)


DEFAULT_ONTOLOGY_REGISTRY_PATH = Path(
    "context/semantics/ontology_registry.json"
)

ONTOLOGY_REGISTRY_SCHEMA_VERSION = "1.0.0"


def _fields(text: str) -> frozenset[str]:
    return frozenset(text.split())


_TOP_LEVEL_FIELDS = _fields(
    """
    schema_version registry_id registry_version status authority
    runtime_boundary reference_systems reference_concept_index
    """
)

_AUTHORITY_FIELDS = _fields(
    """
    registry_role ontology_snapshot_role reference_concept_index_role
    engineering_authority engineering_authority_rule
    """
)

_RUNTIME_BOOLEAN_FIELDS = (
    "live_ontology_queries",
    "automatic_downloads",
    "automatic_updates",
    "remote_runtime_dependency_resolution",
    "owl_reasoner",
    "triple_store",
    "unrestricted_graph_traversal",
    "complete_ontology_prompt_loading",
)

_RUNTIME_FIELDS = frozenset(
    (*_RUNTIME_BOOLEAN_FIELDS, "snapshot_update_policy")
)

_REFERENCE_SYSTEM_FIELDS = _fields(
    """
    reference_system_id name reference_role version version_iri maturity
    runtime_enabled enabled_runtime_role source_authority license artifacts
    """
)

_SOURCE_AUTHORITY_FIELDS = _fields(
    "provider repository reference_type reference"
)

_LICENSE_FIELDS = _fields(
    "identifier name url local_path"
)

_ARTIFACT_REQUIRED_FIELDS = _fields(
    """
    artifact_id artifact_role serialization media_type local_path
    source_path git_blob_sha size_bytes checksum
    """
)

_ARTIFACT_OPTIONAL_FIELDS = _fields(
    "version_iri declared_version_info"
)

_CHECKSUM_FIELDS = _fields("algorithm value")

_INDEX_FIELDS = _fields(
    """
    schema_version path status authority deterministic
    source_reference_system_ids runtime_usage
    complete_ontology_prompt_loading
    """
)

_ARTIFACT_ROLES = frozenset(
    {
        "ontology",
        "production_descriptor",
        "annotation_vocabulary",
    }
)

_REFERENCE_TYPES = frozenset(
    {
        "commit",
        "release_tag",
    }
)


def load_ontology_registry(
    path: Path = DEFAULT_ONTOLOGY_REGISTRY_PATH,
    *,
    repository_root: Path = Path("."),
    verify_snapshots: bool = True,
) -> OntologyRegistry:
    """Load the registry and optionally verify every local snapshot."""

    root = repository_root.resolve()
    registry_path = resolve_repository_path(
        root,
        path,
        "Ontology Registry path",
    )

    try:
        text = registry_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OntologyRegistryError(
            "Unable to read Ontology Registry from "
            f"{registry_path}: {exc}."
        ) from exc

    try:
        payload = json.loads(
            text,
            object_pairs_hook=object_without_duplicate_keys,
        )
    except json.JSONDecodeError as exc:
        raise OntologyRegistryError(
            f"Ontology Registry contains invalid JSON: {exc}."
        ) from exc

    registry = parse_ontology_registry(payload)

    if verify_snapshots:
        verify_ontology_snapshots(
            registry,
            repository_root=root,
        )

    return registry


def parse_ontology_registry(payload: Any) -> OntologyRegistry:
    """Parse and strictly validate one registry payload."""

    data = require_exact_object(
        payload,
        _TOP_LEVEL_FIELDS,
        "Ontology Registry",
    )
    schema_version = require_semantic_version(
        data["schema_version"],
        "schema_version",
    )

    if schema_version != ONTOLOGY_REGISTRY_SCHEMA_VERSION:
        raise OntologyRegistryError(
            "Unsupported Ontology Registry schema_version: "
            f"{schema_version!r}."
        )

    registry_id = require_identifier(
        data["registry_id"],
        "registry_id",
    )
    registry_version = require_semantic_version(
        data["registry_version"],
        "registry_version",
    )
    status = require_string(data["status"], "status")

    if status != "active":
        raise OntologyRegistryError(
            "Ontology Registry status must be 'active'."
        )

    systems_payload = require_list(
        data["reference_systems"],
        "reference_systems",
    )

    if not systems_payload:
        raise OntologyRegistryError(
            "reference_systems must not be empty."
        )

    systems = tuple(
        _parse_reference_system(item)
        for item in systems_payload
    )

    require_unique(
        (item.reference_system_id for item in systems),
        "reference_system_id",
    )
    require_unique(
        (
            artifact.artifact_id
            for system in systems
            for artifact in system.artifacts
        ),
        "artifact_id",
    )
    require_unique(
        (
            artifact.local_path.as_posix()
            for system in systems
            for artifact in system.artifacts
        ),
        "artifact local_path",
    )

    index_configuration = _parse_index_configuration(
        data["reference_concept_index"]
    )
    enabled_system_ids = {
        system.reference_system_id
        for system in systems
        if system.runtime_enabled
    }
    configured_system_ids = set(
        index_configuration.source_reference_system_ids
    )

    if configured_system_ids != enabled_system_ids:
        raise OntologyRegistryError(
            "Reference Concept Index source systems must equal "
            "the runtime-enabled reference systems."
        )

    return OntologyRegistry(
        schema_version=schema_version,
        registry_id=registry_id,
        registry_version=registry_version,
        status=status,
        authority=_parse_authority(data["authority"]),
        runtime_boundary=_parse_runtime_boundary(
            data["runtime_boundary"]
        ),
        reference_systems=systems,
        reference_concept_index=index_configuration,
    )


def verify_ontology_snapshots(
    registry: OntologyRegistry,
    *,
    repository_root: Path = Path("."),
) -> None:
    """Verify licenses, sizes and checksums without network access."""

    root = repository_root.resolve()

    for system in registry.reference_systems:
        license_path = resolve_repository_path(
            root,
            system.license.local_path,
            f"license path for {system.reference_system_id}",
        )

        if not license_path.is_file():
            raise OntologySnapshotNotFoundError(
                "Registered license file does not exist: "
                f"{license_path}."
            )

        for artifact in system.artifacts:
            artifact_path = resolve_repository_path(
                root,
                artifact.local_path,
                f"artifact path for {artifact.artifact_id}",
            )

            if not artifact_path.is_file():
                raise OntologySnapshotNotFoundError(
                    "Registered ontology artifact does not exist: "
                    f"{artifact_path}."
                )

            actual_size = artifact_path.stat().st_size

            if actual_size != artifact.size_bytes:
                raise OntologySnapshotIntegrityError(
                    f"Size mismatch for {artifact.artifact_id}: "
                    f"{actual_size} != {artifact.size_bytes}."
                )

            actual_checksum = calculate_file_sha256(
                artifact_path
            )

            if actual_checksum != artifact.checksum.value:
                raise OntologySnapshotIntegrityError(
                    f"SHA-256 mismatch for {artifact.artifact_id}: "
                    f"{actual_checksum} != "
                    f"{artifact.checksum.value}."
                )


def ontology_artifacts_for_index(
    registry: OntologyRegistry,
) -> tuple[
    tuple[OntologyReferenceSystem, OntologyArtifact],
    ...,
]:
    """Return enabled ontology artifacts in deterministic order."""

    configured_ids = set(
        registry.reference_concept_index.source_reference_system_ids
    )
    selected: list[
        tuple[OntologyReferenceSystem, OntologyArtifact]
    ] = []

    for system in registry.reference_systems:
        if (
            not system.runtime_enabled
            or system.reference_system_id not in configured_ids
        ):
            continue

        for artifact in system.artifacts:
            if artifact.artifact_role != "ontology":
                continue

            if artifact.serialization != "RDF/XML":
                raise UnsupportedOntologySerializationError(
                    "Indexed ontology artifacts must use RDF/XML: "
                    f"{artifact.artifact_id}."
                )

            selected.append((system, artifact))

    if not selected:
        raise OntologyRegistryError(
            "No runtime-enabled ontology artifacts are configured "
            "for the Reference Concept Index."
        )

    return tuple(
        sorted(
            selected,
            key=lambda item: (
                item[0].reference_system_id,
                item[1].artifact_id,
            ),
        )
    )


def _parse_authority(payload: Any) -> RegistryAuthority:
    data = require_exact_object(
        payload,
        _AUTHORITY_FIELDS,
        "authority",
    )
    values = {
        field: require_string(
            data[field],
            f"authority.{field}",
        )
        for field in _AUTHORITY_FIELDS
    }
    authority = RegistryAuthority(**values)
    expected = {
        "registry_role": "curated_reference_metadata",
        "ontology_snapshot_role": (
            "auditable_external_semantic_reference"
        ),
        "reference_concept_index_role": (
            "derived_non_authoritative"
        ),
    }

    for field, expected_value in expected.items():
        if getattr(authority, field) != expected_value:
            raise OntologyRegistryError(
                f"authority.{field} must be "
                f"{expected_value!r}."
            )

    return authority


def _parse_runtime_boundary(payload: Any) -> RuntimeBoundary:
    data = require_exact_object(
        payload,
        _RUNTIME_FIELDS,
        "runtime_boundary",
    )
    values = {
        field: require_boolean(
            data[field],
            f"runtime_boundary.{field}",
        )
        for field in _RUNTIME_BOOLEAN_FIELDS
    }

    for field, value in values.items():
        if value:
            raise OntologyRegistryError(
                f"runtime_boundary.{field} must be false in P4."
            )

    update_policy = require_string(
        data["snapshot_update_policy"],
        "runtime_boundary.snapshot_update_policy",
    )

    if update_policy != "explicit_reviewed_change_only":
        raise OntologyRegistryError(
            "snapshot_update_policy must be "
            "'explicit_reviewed_change_only'."
        )

    return RuntimeBoundary(
        **values,
        snapshot_update_policy=update_policy,
    )


def _parse_reference_system(
    payload: Any,
) -> OntologyReferenceSystem:
    data = require_exact_object(
        payload,
        _REFERENCE_SYSTEM_FIELDS,
        "reference system",
    )
    system_id = require_identifier(
        data["reference_system_id"],
        "reference_system_id",
    )
    maturity = require_string(data["maturity"], "maturity")
    runtime_enabled = require_boolean(
        data["runtime_enabled"],
        "runtime_enabled",
    )

    if runtime_enabled and maturity != "released":
        raise OntologyRegistryError(
            "Runtime-enabled reference systems must have "
            "maturity 'released'."
        )

    artifacts_payload = require_list(
        data["artifacts"],
        f"{system_id}.artifacts",
    )

    if not artifacts_payload:
        raise OntologyRegistryError(
            f"{system_id} must register at least one artifact."
        )

    artifacts = tuple(
        _parse_artifact(item)
        for item in artifacts_payload
    )
    require_unique(
        (artifact.artifact_id for artifact in artifacts),
        f"artifact_id in {system_id}",
    )

    return OntologyReferenceSystem(
        reference_system_id=system_id,
        name=require_string(data["name"], "name"),
        reference_role=require_string(
            data["reference_role"],
            "reference_role",
        ),
        version=require_string(data["version"], "version"),
        version_iri=require_http_url(
            data["version_iri"],
            "version_iri",
        ),
        maturity=maturity,
        runtime_enabled=runtime_enabled,
        enabled_runtime_role=require_string(
            data["enabled_runtime_role"],
            "enabled_runtime_role",
        ),
        source_authority=_parse_source_authority(
            data["source_authority"]
        ),
        license=_parse_license(data["license"]),
        artifacts=artifacts,
    )


def _parse_source_authority(payload: Any) -> SourceAuthority:
    data = require_exact_object(
        payload,
        _SOURCE_AUTHORITY_FIELDS,
        "source_authority",
    )
    reference_type = require_string(
        data["reference_type"],
        "source_authority.reference_type",
    )
    reference = require_string(
        data["reference"],
        "source_authority.reference",
    )

    if reference_type not in _REFERENCE_TYPES:
        raise OntologyRegistryError(
            "source_authority.reference_type must be one of: "
            f"{', '.join(sorted(_REFERENCE_TYPES))}."
        )

    if reference_type == "commit":
        reference = require_git_sha(
            reference,
            "source_authority.reference",
        )

    return SourceAuthority(
        provider=require_string(
            data["provider"],
            "source_authority.provider",
        ),
        repository=require_http_url(
            data["repository"],
            "source_authority.repository",
        ),
        reference_type=reference_type,
        reference=reference,
    )


def _parse_license(payload: Any) -> LicenseReference:
    data = require_exact_object(
        payload,
        _LICENSE_FIELDS,
        "license",
    )

    return LicenseReference(
        identifier=require_string(
            data["identifier"],
            "license.identifier",
        ),
        name=require_string(data["name"], "license.name"),
        url=require_http_url(data["url"], "license.url"),
        local_path=require_repository_path(
            data["local_path"],
            "license.local_path",
            required_prefix=("external", "ontologies"),
        ),
    )


def _parse_artifact(payload: Any) -> OntologyArtifact:
    data = require_exact_object(
        payload,
        _ARTIFACT_REQUIRED_FIELDS,
        "ontology artifact",
        optional_fields=_ARTIFACT_OPTIONAL_FIELDS,
    )
    artifact_id = require_identifier(
        data["artifact_id"],
        "artifact_id",
    )
    role = require_string(
        data["artifact_role"],
        f"{artifact_id}.artifact_role",
    )

    if role not in _ARTIFACT_ROLES:
        raise OntologyRegistryError(
            f"Unsupported artifact_role for {artifact_id}: {role!r}."
        )

    serialization = require_string(
        data["serialization"],
        f"{artifact_id}.serialization",
    )
    media_type = require_string(
        data["media_type"],
        f"{artifact_id}.media_type",
    )

    if serialization != "RDF/XML":
        raise OntologyRegistryError(
            f"{artifact_id} serialization must be 'RDF/XML'."
        )

    if media_type != "application/rdf+xml":
        raise OntologyRegistryError(
            f"{artifact_id} media_type must be "
            "'application/rdf+xml'."
        )

    version_iri = data.get("version_iri")
    declared_version_info = data.get("declared_version_info")

    if version_iri is not None:
        version_iri = require_http_url(
            version_iri,
            f"{artifact_id}.version_iri",
        )

    if declared_version_info is not None:
        declared_version_info = require_string(
            declared_version_info,
            f"{artifact_id}.declared_version_info",
        )

    return OntologyArtifact(
        artifact_id=artifact_id,
        artifact_role=role,
        serialization=serialization,
        media_type=media_type,
        local_path=require_repository_path(
            data["local_path"],
            f"{artifact_id}.local_path",
            required_prefix=("external", "ontologies"),
        ),
        source_path=require_source_path(
            data["source_path"],
            f"{artifact_id}.source_path",
        ),
        git_blob_sha=require_git_sha(
            data["git_blob_sha"],
            f"{artifact_id}.git_blob_sha",
        ),
        size_bytes=require_positive_integer(
            data["size_bytes"],
            f"{artifact_id}.size_bytes",
        ),
        checksum=_parse_checksum(data["checksum"], artifact_id),
        version_iri=version_iri,
        declared_version_info=declared_version_info,
    )


def _parse_checksum(payload: Any, label: str) -> Checksum:
    data = require_exact_object(
        payload,
        _CHECKSUM_FIELDS,
        f"{label}.checksum",
    )
    algorithm = require_string(
        data["algorithm"],
        f"{label}.checksum.algorithm",
    )

    if algorithm != "sha256":
        raise OntologyRegistryError(
            f"{label} checksum algorithm must be 'sha256'."
        )

    return Checksum(
        algorithm=algorithm,
        value=require_sha256(
            data["value"],
            f"{label}.checksum.value",
        ),
    )


def _parse_index_configuration(
    payload: Any,
) -> ReferenceConceptIndexConfiguration:
    data = require_exact_object(
        payload,
        _INDEX_FIELDS,
        "reference_concept_index",
    )
    schema_version = require_semantic_version(
        data["schema_version"],
        "reference_concept_index.schema_version",
    )

    if schema_version != "1.0.0":
        raise OntologyRegistryError(
            "Unsupported Reference Concept Index schema_version: "
            f"{schema_version!r}."
        )

    status = require_string(
        data["status"],
        "reference_concept_index.status",
    )
    authority = require_string(
        data["authority"],
        "reference_concept_index.authority",
    )
    deterministic = require_boolean(
        data["deterministic"],
        "reference_concept_index.deterministic",
    )
    runtime_usage = require_string(
        data["runtime_usage"],
        "reference_concept_index.runtime_usage",
    )
    complete_loading = require_boolean(
        data["complete_ontology_prompt_loading"],
        "reference_concept_index.complete_ontology_prompt_loading",
    )

    expected_values = {
        "status": (status, "generated_read_only"),
        "authority": (authority, "derived_non_authoritative"),
        "runtime_usage": (
            runtime_usage,
            "retrieve_relevant_concepts_only",
        ),
    }

    for field, (actual, expected) in expected_values.items():
        if actual != expected:
            raise OntologyRegistryError(
                f"reference_concept_index.{field} must be "
                f"{expected!r}."
            )

    if not deterministic:
        raise OntologyRegistryError(
            "Reference Concept Index generation must be deterministic."
        )

    if complete_loading:
        raise OntologyRegistryError(
            "Complete ontology prompt loading must be disabled."
        )

    source_ids = tuple(
        require_identifier(
            item,
            "Reference Concept Index source system ID",
        )
        for item in require_list(
            data["source_reference_system_ids"],
            "reference_concept_index.source_reference_system_ids",
        )
    )

    if not source_ids:
        raise OntologyRegistryError(
            "Reference Concept Index source systems must not be empty."
        )

    require_unique(
        source_ids,
        "Reference Concept Index source system ID",
    )
    index_path = require_repository_path(
        data["path"],
        "reference_concept_index.path",
        required_prefix=("context", "semantics"),
    )

    if index_path != Path(
        "context/semantics/reference_concept_index.json"
    ):
        raise OntologyRegistryError(
            "Reference Concept Index path must be "
            "context/semantics/reference_concept_index.json."
        )

    return ReferenceConceptIndexConfiguration(
        schema_version=schema_version,
        path=index_path,
        status=status,
        authority=authority,
        deterministic=deterministic,
        source_reference_system_ids=source_ids,
        runtime_usage=runtime_usage,
        complete_ontology_prompt_loading=complete_loading,
    )