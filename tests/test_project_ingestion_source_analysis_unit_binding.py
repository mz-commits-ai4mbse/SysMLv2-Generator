"""Project-bound integration tests for Source Analysis Unit orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from modules.project_ingestion.configuration import (
    ProjectIngestionConfiguration,
)
from modules.project_ingestion.service import (
    ProjectBoundIngestionService,
)
from modules.project_sources import (
    ENGINEERING_SOURCE_ROLE,
    ProjectSourceRegistry,
)
from modules.project_workspace import ProjectWorkspace


PROJECT_ID = '614209'


class FixedClock:
    def __init__(self) -> None:
        self.second = 0

    def __call__(self) -> datetime:
        self.second += 1
        return datetime(
            2026,
            8,
            18,
            20,
            0,
            self.second,
            tzinfo=timezone.utc,
        )


class CapturingPipeline:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs):
        self.calls.append(dict(kwargs))
        return SimpleNamespace(run_id='20260818T200000Z')


def no_op_semantic_consolidator(**kwargs):
    return None


def test_project_bound_pipeline_receives_canonical_source_units(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / 'repository'
    projects_root = repository_root / 'data' / 'projects'
    projects_root.parent.mkdir(parents=True)
    clock = FixedClock()

    workspace = ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: PROJECT_ID,
        clock=clock,
    )
    workspace.create_project('Source Unit Binding Test')

    source_path = tmp_path / 'source.md'
    source_path.write_text(
        '# Context\n\nFirst statement.\n\nSecond statement.',
        encoding='utf-8',
    )
    source = ProjectSourceRegistry(
        root=projects_root,
        clock=clock,
    ).register_source(
        PROJECT_ID,
        source_path,
        source_role=ENGINEERING_SOURCE_ROLE,
    )

    pipeline = CapturingPipeline()
    service = ProjectBoundIngestionService(
        root=projects_root,
        repository_root=repository_root,
        pipeline_runner=pipeline,
        semantic_consolidator=no_op_semantic_consolidator,
        clock=clock,
    )

    result = service.execute_registered_source_to_work(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(
            dry_run=True,
        ),
    )

    assert result.run_state == 'running'
    assert len(pipeline.calls) == 1

    units = pipeline.calls[0]['source_analysis_units']
    assert tuple(
        unit.source_analysis_unit_id for unit in units
    ) == (
        'SAU-000001',
        'SAU-000002',
        'SAU-000003',
    )
    assert tuple(unit.source_excerpt for unit in units) == (
        '# Context',
        'First statement.',
        'Second statement.',
    )
    assert len(
        {
            unit.source_projection_fingerprint
            for unit in units
        }
    ) == 1

    persisted = (
        projects_root
        / PROJECT_ID
        / 'semantics'
        / 'source_analysis_units'
    )
    assert tuple(
        path.name for path in sorted(persisted.glob('SAU-*.json'))
    ) == (
        'SAU-000001.json',
        'SAU-000002.json',
        'SAU-000003.json',
    )
