"""Tests for the curated Ontology Registry contract."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from modules.semantics.errors import (
    OntologyRegistryError,
    OntologySnapshotIntegrityError,
    OntologySnapshotNotFoundError,
    UnsafeOntologyPathError,
    UnsupportedOntologySerializationError,
)
from modules.semantics.registry import (
    DEFAULT_ONTOLOGY_REGISTRY_PATH,
    ONTOLOGY_REGISTRY_SCHEMA_VERSION,
    load_ontology_registry,
    ontology_artifacts_for_index,
    parse_ontology_registry,
    verify_ontology_snapshots,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = (
    REPOSITORY_ROOT / DEFAULT_ONTOLOGY_REGISTRY_PATH
)


def registry_payload() -> dict[str, object]:
    """Return one independent copy of the accepted payload."""

    return json.loads(
        REGISTRY_PATH.read_text(encoding="utf-8")
    )


def load_registry():
    """Load the accepted registry from the repository root."""

    return load_ontology_registry(
        repository_root=REPOSITORY_ROOT,
    )


def create_registered_license_files(
    root: Path,
    registry,
) -> None:
    """Create only the registered license paths."""

    for system in registry.reference_systems:
        path = root / system.license.local_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("license", encoding="utf-8")


def test_loads_and_verifies_accepted_registry() -> None:
    registry = load_registry()

    assert registry.schema_version == "1.0.0"
    assert registry.registry_id == "TURING_ONTOLOGY_REGISTRY"
    assert registry.registry_version == "1.0.0"
    assert registry.status == "active"


def test_registry_schema_constant_matches_payload() -> None:
    assert ONTOLOGY_REGISTRY_SCHEMA_VERSION == "1.0.0"
    assert (
        registry_payload()["schema_version"]
        == ONTOLOGY_REGISTRY_SCHEMA_VERSION
    )


def test_reference_systems_are_pinned_and_enabled() -> None:
    registry = load_registry()

    assert [
        system.reference_system_id
        for system in registry.reference_systems
    ] == [
        "BFO_2020",
        "IOF_CORE_202602",
    ]
    assert all(
        system.runtime_enabled
        for system in registry.reference_systems
    )
    assert all(
        system.maturity == "released"
        for system in registry.reference_systems
    )


def test_reference_system_authorities_are_pinned() -> None:
    registry = load_registry()
    bfo, iof = registry.reference_systems

    assert bfo.source_authority.reference_type == "commit"
    assert bfo.source_authority.reference == (
        "dd89f4a193038b66ef0e891d546c05a5b477f40f"
    )
    assert iof.source_authority.reference_type == (
        "release_tag"
    )
    assert iof.source_authority.reference == "Release_202602"


def test_registry_preserves_engineering_authority_boundary() -> None:
    registry = load_registry()

    assert registry.authority.registry_role == (
        "curated_reference_metadata"
    )
    assert registry.authority.ontology_snapshot_role == (
        "auditable_external_semantic_reference"
    )
    assert registry.authority.reference_concept_index_role == (
        "derived_non_authoritative"
    )
    assert registry.authority.engineering_authority == (
        "CATIA Magic Systems of Systems Architect"
    )


@pytest.mark.parametrize(
    "field",
    [
        "live_ontology_queries",
        "automatic_downloads",
        "automatic_updates",
        "remote_runtime_dependency_resolution",
        "owl_reasoner",
        "triple_store",
        "unrestricted_graph_traversal",
        "complete_ontology_prompt_loading",
    ],
)
def test_runtime_capabilities_are_disabled(field: str) -> None:
    registry = load_registry()

    assert getattr(registry.runtime_boundary, field) is False


def test_snapshot_update_requires_reviewed_change() -> None:
    registry = load_registry()

    assert registry.runtime_boundary.snapshot_update_policy == (
        "explicit_reviewed_change_only"
    )


def test_all_registered_artifacts_have_unique_identity() -> None:
    registry = load_registry()
    artifacts = [
        artifact
        for system in registry.reference_systems
        for artifact in system.artifacts
    ]

    assert len(artifacts) == 4
    assert len(
        {artifact.artifact_id for artifact in artifacts}
    ) == 4
    assert len(
        {artifact.local_path for artifact in artifacts}
    ) == 4


def test_only_ontology_artifacts_feed_reference_index() -> None:
    selected = ontology_artifacts_for_index(
        load_registry()
    )

    assert [
        artifact.artifact_id
        for _, artifact in selected
    ] == [
        "BFO_CORE_2020",
        "IOF_CORE_202602",
    ]


@pytest.mark.parametrize(
    "payload",
    [None, [], "registry", 1, True],
)
def test_rejects_non_object_registry(payload: object) -> None:
    with pytest.raises(OntologyRegistryError):
        parse_ontology_registry(payload)


def test_rejects_missing_top_level_field() -> None:
    payload = registry_payload()
    del payload["authority"]

    with pytest.raises(
        OntologyRegistryError,
        match="missing fields",
    ):
        parse_ontology_registry(payload)


def test_rejects_unknown_top_level_field() -> None:
    payload = registry_payload()
    payload["unexpected"] = True

    with pytest.raises(
        OntologyRegistryError,
        match="unknown fields",
    ):
        parse_ontology_registry(payload)


@pytest.mark.parametrize(
    "schema_version",
    ["1", "1.0", "2.0.0", 1, None],
)
def test_rejects_unsupported_schema_version(
    schema_version: object,
) -> None:
    payload = registry_payload()
    payload["schema_version"] = schema_version

    with pytest.raises(OntologyRegistryError):
        parse_ontology_registry(payload)


@pytest.mark.parametrize(
    "status",
    ["draft", "retired", "", None, True],
)
def test_rejects_non_active_registry(status: object) -> None:
    payload = registry_payload()
    payload["status"] = status

    with pytest.raises(OntologyRegistryError):
        parse_ontology_registry(payload)


@pytest.mark.parametrize(
    "field",
    [
        "live_ontology_queries",
        "automatic_downloads",
        "automatic_updates",
        "remote_runtime_dependency_resolution",
        "owl_reasoner",
        "triple_store",
        "unrestricted_graph_traversal",
        "complete_ontology_prompt_loading",
    ],
)
def test_rejects_enabled_runtime_capability(field: str) -> None:
    payload = registry_payload()
    payload["runtime_boundary"][field] = True

    with pytest.raises(OntologyRegistryError):
        parse_ontology_registry(payload)


def test_rejects_automatic_snapshot_update_policy() -> None:
    payload = registry_payload()
    payload["runtime_boundary"][
        "snapshot_update_policy"
    ] = "automatic"

    with pytest.raises(OntologyRegistryError):
        parse_ontology_registry(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("registry_role", "authority"),
        ("ontology_snapshot_role", "engineering_model"),
        ("reference_concept_index_role", "authoritative"),
    ],
)
def test_rejects_changed_authority_roles(
    field: str,
    value: str,
) -> None:
    payload = registry_payload()
    payload["authority"][field] = value

    with pytest.raises(OntologyRegistryError):
        parse_ontology_registry(payload)


def test_rejects_duplicate_reference_system_id() -> None:
    payload = registry_payload()
    payload["reference_systems"].append(
        deepcopy(payload["reference_systems"][0])
    )

    with pytest.raises(
        OntologyRegistryError,
        match="Duplicate reference_system_id",
    ):
        parse_ontology_registry(payload)


def test_rejects_duplicate_artifact_id() -> None:
    payload = registry_payload()
    duplicate = deepcopy(
        payload["reference_systems"][0]["artifacts"][0]
    )
    duplicate["local_path"] = (
        "external/ontologies/bfo/2020/duplicate.owl"
    )
    payload["reference_systems"][1]["artifacts"].append(
        duplicate
    )

    with pytest.raises(
        OntologyRegistryError,
        match="Duplicate artifact_id",
    ):
        parse_ontology_registry(payload)


def test_rejects_runtime_enabled_draft_system() -> None:
    payload = registry_payload()
    payload["reference_systems"][0]["maturity"] = "draft"

    with pytest.raises(OntologyRegistryError):
        parse_ontology_registry(payload)


@pytest.mark.parametrize(
    "local_path",
    [
        "/tmp/bfo.owl",
        "../bfo.owl",
        "external/../bfo.owl",
        "context/semantics/bfo.owl",
        r"external\ontologies\bfo.owl",
    ],
)
def test_rejects_unsafe_artifact_path(
    local_path: str,
) -> None:
    payload = registry_payload()
    payload["reference_systems"][0]["artifacts"][0][
        "local_path"
    ] = local_path

    with pytest.raises(OntologyRegistryError):
        parse_ontology_registry(payload)


@pytest.mark.parametrize(
    "checksum",
    ["", "a" * 63, "a" * 65, "A" * 64, 1, None],
)
def test_rejects_invalid_sha256(checksum: object) -> None:
    payload = registry_payload()
    payload["reference_systems"][0]["artifacts"][0][
        "checksum"
    ]["value"] = checksum

    with pytest.raises(OntologyRegistryError):
        parse_ontology_registry(payload)


@pytest.mark.parametrize(
    "size_bytes",
    [0, -1, True, "98418", None],
)
def test_rejects_invalid_size(size_bytes: object) -> None:
    payload = registry_payload()
    payload["reference_systems"][0]["artifacts"][0][
        "size_bytes"
    ] = size_bytes

    with pytest.raises(OntologyRegistryError):
        parse_ontology_registry(payload)


def test_rejects_index_source_system_mismatch() -> None:
    payload = registry_payload()
    payload["reference_concept_index"][
        "source_reference_system_ids"
    ] = ["BFO_2020"]

    with pytest.raises(OntologyRegistryError):
        parse_ontology_registry(payload)


def test_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "ontology_registry.json"
    path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(OntologyRegistryError):
        load_ontology_registry(
            path,
            repository_root=tmp_path,
            verify_snapshots=False,
        )


def test_rejects_duplicate_json_key(tmp_path: Path) -> None:
    path = tmp_path / "ontology_registry.json"
    path.write_text(
        '{"registry_id":"A","registry_id":"B"}',
        encoding="utf-8",
    )

    with pytest.raises(
        OntologyRegistryError,
        match="Duplicate JSON field",
    ):
        load_ontology_registry(
            path,
            repository_root=tmp_path,
            verify_snapshots=False,
        )


def test_rejects_registry_path_outside_root(
    tmp_path: Path,
) -> None:
    outside = tmp_path.parent / "outside-registry.json"

    with pytest.raises(UnsafeOntologyPathError):
        load_ontology_registry(
            outside,
            repository_root=tmp_path,
            verify_snapshots=False,
        )


def test_rejects_missing_license(tmp_path: Path) -> None:
    registry = parse_ontology_registry(registry_payload())

    with pytest.raises(OntologySnapshotNotFoundError):
        verify_ontology_snapshots(
            registry,
            repository_root=tmp_path,
        )


def test_rejects_missing_artifact(tmp_path: Path) -> None:
    registry = parse_ontology_registry(registry_payload())
    create_registered_license_files(tmp_path, registry)

    with pytest.raises(OntologySnapshotNotFoundError):
        verify_ontology_snapshots(
            registry,
            repository_root=tmp_path,
        )


def test_rejects_snapshot_size_mismatch(
    tmp_path: Path,
) -> None:
    registry = parse_ontology_registry(registry_payload())
    create_registered_license_files(tmp_path, registry)
    artifact = registry.reference_systems[0].artifacts[0]
    artifact_path = tmp_path / artifact.local_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(b"not the registered snapshot")

    with pytest.raises(
        OntologySnapshotIntegrityError,
        match="Size mismatch",
    ):
        verify_ontology_snapshots(
            registry,
            repository_root=tmp_path,
        )


def test_rejects_snapshot_checksum_mismatch(
    tmp_path: Path,
) -> None:
    registry = parse_ontology_registry(registry_payload())
    create_registered_license_files(tmp_path, registry)
    artifact = registry.reference_systems[0].artifacts[0]
    artifact_path = tmp_path / artifact.local_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(b"x" * artifact.size_bytes)

    with pytest.raises(
        OntologySnapshotIntegrityError,
        match="SHA-256 mismatch",
    ):
        verify_ontology_snapshots(
            registry,
            repository_root=tmp_path,
        )


def test_rejects_unsupported_index_serialization() -> None:
    registry = load_registry()
    system = registry.reference_systems[0]
    changed_artifact = replace(
        system.artifacts[0],
        serialization="Turtle",
    )
    changed_system = replace(
        system,
        artifacts=(changed_artifact,),
    )
    changed_registry = replace(
        registry,
        reference_systems=(
            changed_system,
            *registry.reference_systems[1:],
        ),
    )

    with pytest.raises(
        UnsupportedOntologySerializationError
    ):
        ontology_artifacts_for_index(changed_registry)