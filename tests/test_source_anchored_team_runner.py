"""Tests for Source Analysis Unit binding in Agent execution evidence."""

from __future__ import annotations

import json
from pathlib import Path

from modules.agents.team_runner import run_agent_team


def test_source_analysis_unit_binding_is_persisted(
    tmp_path: Path,
) -> None:
    repository_root = Path('.').resolve()

    results = run_agent_team(
        project_root=repository_root,
        team_file=(
            repository_root
            / 'teams'
            / 'ingestion'
            / 'derivation_assessment_team.json'
        ),
        task_instructions='Return deterministic dry-run output.',
        input_text='Source Analysis Unit ID: SAU-000003',
        output_dir=tmp_path / 'outputs',
        provider='openai',
        model='test-model',
        runs_per_member=1,
        max_members=1,
        dry_run=True,
        source_analysis_unit_id='SAU-000003',
    )

    assert len(results) == 1
    result = results[0]
    assert result.source_analysis_unit_id == 'SAU-000003'

    wrapper = json.loads(
        result.output_path.read_text(encoding='utf-8')
    )
    assert wrapper['source_analysis_unit_id'] == 'SAU-000003'

    output = json.loads(wrapper['output_text'])
    assert output['source_analysis_unit_id'] == 'SAU-000003'
