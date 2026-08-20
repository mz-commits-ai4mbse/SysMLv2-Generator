"""Tests for canonical Source Analysis Unit persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from modules.project_sources import (
    ENGINEERING_SOURCE_ROLE,
    ProjectSourceRegistry,
)
from modules.project_workspace import ProjectWorkspace
from modules.source_analysis_units.errors import (
    SourceAnalysisUnitIntegrityError,
    SourceAnalysisUnitNotFoundError,
    SourceAnalysisUnitValidationError,
    UnavailableSourceAnalysisProjectionError,
)
from modules.source_analysis_units.repository import (
    DEFAULT_SEGMENTATION_PROFILE_ID,
    DEFAULT_SEGMENTATION_PROFILE_VERSION,
    SOURCE_ANALYSIS_UNITS_DIRECTORY_NAME,
    SourceAnalysisUnitRepository,
)
from modules.source_projection.repository import (
    SourceProjectionRepository,
)
from modules.source_projection.types import (
    SourceProjectionArtifact,
)


PROJECT_ID = "318604"
SOURCE_TEXT = """# Demo

The remote expert joins from a client.

The operator remains responsible.
"""


def fixed_clock() -> datetime:
    return datetime(
        2026,
        8,
        18,
        20,
        0,
        0,
        tzinfo=timezone.utc,
    )


@dataclass(frozen=True)
class Environment:
    projects_root: Path
    inputs_root: Path
    source_registry: ProjectSourceRegistry
    projection_repository: SourceProjectionRepository
    repository: SourceAnalysisUnitRepository
    source_id: str
    projection: SourceProjectionArtifact


@pytest.fixture
def environment(tmp_path: Path) -> Environment:
    projects_root = tmp_path / "projects"
    inputs_root = tmp_path / "inputs"
    inputs_root.mkdir()

    workspace = ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: PROJECT_ID,
        clock=fixed_clock,
    )
    workspace.create_project("Source Analysis Unit Test")

    input_path = inputs_root / "source.md"
    input_path.write_text(
        SOURCE_TEXT,
        encoding="utf-8",
    )

    source_registry = ProjectSourceRegistry(
        root=projects_root,
        clock=fixed_clock,
    )
    source = source_registry.register_source(
        PROJECT_ID,
        input_path,
        source_role=ENGINEERING_SOURCE_ROLE,
    )

    projection_repository = SourceProjectionRepository(
        root=projects_root,
        clock=fixed_clock,
    )
    projection = projection_repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    repository = SourceAnalysisUnitRepository(
        root=projects_root,
        clock=fixed_clock,
        source_projection_repository=(
            projection_repository
        ),
    )

    return Environment(
        projects_root=projects_root,
        inputs_root=inputs_root,
        source_registry=source_registry,
        projection_repository=projection_repository,
        repository=repository,
        source_id=source.source_id,
        projection=projection,
    )


def segment_text(
    projection: SourceProjectionArtifact,
    index: int,
) -> str:
    segment = projection.manifest.segments[index]
    return projection.content[
        segment.start_offset:segment.end_offset
    ]


def test_repository_path_is_explicit(
    environment: Environment,
) -> None:
    path = environment.repository.source_analysis_units_path(
        PROJECT_ID
    )
    assert path == (
        environment.projects_root
        / PROJECT_ID
        / "semantics"
        / SOURCE_ANALYSIS_UNITS_DIRECTORY_NAME
    )


def test_empty_repository_lists_no_units(
    environment: Environment,
) -> None:
    assert environment.repository.list_source_analysis_units(
        PROJECT_ID
    ) == ()


def test_projection_segments_become_canonical_units(
    environment: Environment,
) -> None:
    units = environment.repository.ensure_projection_units(
        PROJECT_ID,
        environment.projection.manifest.source_projection_id,
    )

    assert len(units) == len(
        environment.projection.manifest.segments
    )
    assert tuple(
        unit.source_order_index for unit in units
    ) == tuple(range(1, len(units) + 1))
    assert tuple(
        unit.source_excerpt for unit in units
    ) == tuple(
        segment_text(environment.projection, index)
        for index in range(len(units))
    )

    for index, unit in enumerate(units):
        segment = environment.projection.manifest.segments[
            index
        ]
        expected_text = segment_text(
            environment.projection,
            index,
        )
        assert (
            unit.source_projection_fingerprint
            == environment.projection.manifest
            .projection_fingerprint
        )
        assert len(unit.source_anchors) == 1
        anchor = unit.source_anchors[0]
        assert anchor.segment_id == segment.segment_id
        assert anchor.start_offset == 0
        assert anchor.end_offset == len(expected_text)
        assert unit.segmentation_profile_id == (
            DEFAULT_SEGMENTATION_PROFILE_ID
        )
        assert unit.segmentation_profile_version == (
            DEFAULT_SEGMENTATION_PROFILE_VERSION
        )


def test_ensure_projection_units_is_idempotent(
    environment: Environment,
) -> None:
    first = environment.repository.ensure_projection_units(
        PROJECT_ID,
        environment.projection.manifest.source_projection_id,
    )
    second = environment.repository.ensure_projection_units(
        PROJECT_ID,
        environment.projection.manifest.source_projection_id,
    )

    assert second == first
    assert len(
        environment.repository.list_source_analysis_units(
            PROJECT_ID
        )
    ) == len(first)


def test_units_are_persisted_under_project_semantics(
    environment: Environment,
) -> None:
    units = environment.repository.ensure_projection_units(
        PROJECT_ID,
        environment.projection.manifest.source_projection_id,
    )

    for unit in units:
        path = (
            environment.projects_root
            / PROJECT_ID
            / "semantics"
            / "source_analysis_units"
            / f"{unit.source_analysis_unit_id}.json"
        )
        assert path.is_file()


def test_load_unknown_unit_fails(
    environment: Environment,
) -> None:
    with pytest.raises(SourceAnalysisUnitNotFoundError):
        environment.repository.load_source_analysis_unit(
            PROJECT_ID,
            "SAU-000001",
        )


def test_unsupported_profile_fails_closed(
    environment: Environment,
) -> None:
    with pytest.raises(
        SourceAnalysisUnitValidationError
    ):
        environment.repository.ensure_projection_units(
            PROJECT_ID,
            environment.projection.manifest
            .source_projection_id,
            segmentation_profile_version="2.0.0",
        )


def test_unavailable_projection_cannot_create_units(
    environment: Environment,
) -> None:
    path = environment.inputs_root / "empty.md"
    # The Source Registry correctly rejects zero-byte sources.
    # Use non-empty whitespace so registration succeeds while the
    # Markdown projection still contains no non-whitespace segments.
    path.write_text("   \n", encoding="utf-8")
    source = environment.source_registry.register_source(
        PROJECT_ID,
        path,
        source_role=ENGINEERING_SOURCE_ROLE,
    )
    projection = (
        environment.projection_repository.create_projection(
            PROJECT_ID,
            source.source_id,
        )
    )
    assert projection.manifest.projection_result == (
        "unavailable"
    )

    with pytest.raises(
        UnavailableSourceAnalysisProjectionError
    ):
        environment.repository.ensure_projection_units(
            PROJECT_ID,
            projection.manifest.source_projection_id,
        )


def test_unexpected_repository_entry_is_rejected(
    environment: Environment,
) -> None:
    environment.repository.ensure_projection_units(
        PROJECT_ID,
        environment.projection.manifest.source_projection_id,
    )
    units_path = (
        environment.repository.source_analysis_units_path(
            PROJECT_ID
        )
    )
    (units_path / "unexpected.txt").write_text(
        "x",
        encoding="utf-8",
    )

    with pytest.raises(
        SourceAnalysisUnitIntegrityError
    ):
        environment.repository.list_source_analysis_units(
            PROJECT_ID
        )
