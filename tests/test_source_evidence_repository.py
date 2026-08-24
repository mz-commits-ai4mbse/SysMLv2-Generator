"""Persistence tests for persona-independent source-grounded Evidence."""

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
from modules.source_evidence import (
    SOURCE_EVIDENCE_DIRECTORY_NAME,
    SourceEvidenceAnchor,
    SourceEvidenceAnchorError,
    SourceEvidenceNotFoundError,
    SourceEvidenceRepository,
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

The operator may temporarily transfer remote control.
"""


def fixed_clock() -> datetime:
    return datetime(
        2026,
        8,
        21,
        10,
        0,
        0,
        tzinfo=timezone.utc,
    )


@dataclass(frozen=True)
class Environment:
    projects_root: Path
    repository: SourceEvidenceRepository
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
    workspace.create_project("Source Evidence Test")

    input_path = inputs_root / "source.md"
    input_path.write_text(SOURCE_TEXT, encoding="utf-8")

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

    repository = SourceEvidenceRepository(
        root=projects_root,
        clock=fixed_clock,
        source_projection_repository=projection_repository,
    )

    return Environment(
        projects_root=projects_root,
        repository=repository,
        projection=projection,
    )


def anchored_excerpt(
    environment: Environment,
) -> tuple[SourceEvidenceAnchor, str]:
    projection = environment.projection
    segment = next(
        segment
        for segment in projection.manifest.segments
        if "remote control"
        in projection.content[
            segment.start_offset:segment.end_offset
        ]
    )
    segment_text = projection.content[
        segment.start_offset:segment.end_offset
    ]
    phrase = "temporarily transfer remote control"
    start = segment_text.index(phrase)
    end = start + len(phrase)

    return (
        SourceEvidenceAnchor(
            segment_id=segment.segment_id,
            start_offset=start,
            end_offset=end,
        ),
        phrase,
    )


def test_repository_path_is_explicit(
    environment: Environment,
) -> None:
    assert (
        environment.repository.source_evidence_directory_path(
            PROJECT_ID
        )
        == environment.projects_root
        / PROJECT_ID
        / "semantics"
        / SOURCE_EVIDENCE_DIRECTORY_NAME
    )


def test_empty_repository_lists_no_evidence(
    environment: Environment,
) -> None:
    assert environment.repository.list_source_evidence(
        PROJECT_ID
    ) == ()


def test_exact_source_span_is_persisted_and_reopened(
    environment: Environment,
) -> None:
    anchor, excerpt = anchored_excerpt(environment)

    item = environment.repository.create_or_reuse_evidence(
        PROJECT_ID,
        environment.projection.manifest.source_projection_id,
        source_anchors=(anchor,),
        source_excerpt=excerpt,
    )

    assert item.source_evidence_id == "EVD-000001"
    assert item.source_excerpt == excerpt
    assert item.source_anchors == (anchor,)

    path = (
        environment.projects_root
        / PROJECT_ID
        / "semantics"
        / "source_evidence"
        / "EVD-000001.json"
    )
    assert path.is_file()
    assert (
        environment.repository.load_source_evidence(
            PROJECT_ID,
            "EVD-000001",
        )
        == item
    )


def test_same_exact_source_span_reuses_evidence_identity(
    environment: Environment,
) -> None:
    anchor, excerpt = anchored_excerpt(environment)

    first = environment.repository.create_or_reuse_evidence(
        PROJECT_ID,
        environment.projection.manifest.source_projection_id,
        source_anchors=(anchor,),
        source_excerpt=excerpt,
    )
    second = environment.repository.create_or_reuse_evidence(
        PROJECT_ID,
        environment.projection.manifest.source_projection_id,
        source_anchors=(anchor,),
        source_excerpt=excerpt,
    )

    assert second == first
    assert len(
        environment.repository.list_source_evidence(PROJECT_ID)
    ) == 1


def test_excerpt_must_equal_projection_anchor(
    environment: Environment,
) -> None:
    anchor, _ = anchored_excerpt(environment)

    with pytest.raises(SourceEvidenceAnchorError):
        environment.repository.create_or_reuse_evidence(
            PROJECT_ID,
            environment.projection.manifest.source_projection_id,
            source_anchors=(anchor,),
            source_excerpt="invented project evidence",
        )


def test_unknown_evidence_fails_closed(
    environment: Environment,
) -> None:
    with pytest.raises(SourceEvidenceNotFoundError):
        environment.repository.load_source_evidence(
            PROJECT_ID,
            "EVD-000001",
        )

def test_context_only_projection_cannot_back_source_evidence(
    tmp_path: Path,
) -> None:
    projects_root = tmp_path / "projects"
    inputs_root = tmp_path / "inputs"
    inputs_root.mkdir()

    workspace = ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: PROJECT_ID,
        clock=fixed_clock,
    )
    workspace.create_project("Context Evidence Guard")

    path = inputs_root / "context.md"
    path.write_text(
        "Reference guidance only.",
        encoding="utf-8",
    )
    registry = ProjectSourceRegistry(
        root=projects_root,
        clock=fixed_clock,
    )
    source = registry.register_source(
        PROJECT_ID,
        path,
        source_role="context_only",
    )
    projection_repository = SourceProjectionRepository(
        root=projects_root,
        clock=fixed_clock,
    )
    projection = projection_repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )
    repository = SourceEvidenceRepository(
        root=projects_root,
        clock=fixed_clock,
        source_projection_repository=projection_repository,
    )
    segment = projection.manifest.segments[0]
    segment_text = projection.content[
        segment.start_offset:segment.end_offset
    ]
    anchor = SourceEvidenceAnchor(
        segment_id=segment.segment_id,
        start_offset=0,
        end_offset=len(segment_text),
    )

    from modules.source_evidence import SourceEvidenceReferenceError

    with pytest.raises(SourceEvidenceReferenceError):
        repository.create_or_reuse_evidence(
            PROJECT_ID,
            projection.manifest.source_projection_id,
            source_anchors=(anchor,),
            source_excerpt=segment_text,
        )
