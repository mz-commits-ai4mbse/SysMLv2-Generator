"""Tests for Source Analysis Unit orchestration in Phase F."""

from __future__ import annotations

from pathlib import Path

from modules.ingestion.team_agentic_pipeline import (
    run_team_agentic_ingestion,
)
from modules.source_analysis_units.types import (
    SourceAnalysisUnit,
    SourceAnalysisUnitAnchor,
)


def unit(
    unit_id: str,
    order: int,
    excerpt: str,
) -> SourceAnalysisUnit:
    return SourceAnalysisUnit(
        schema_version='1.0.0',
        project_id='123456',
        source_id='SRC-000001',
        source_projection_id='SP-000001',
        source_analysis_unit_id=unit_id,
        source_projection_fingerprint='a' * 64,
        source_anchors=(
            SourceAnalysisUnitAnchor(
                segment_id=f'SEG-{order:06d}',
                start_offset=0,
                end_offset=len(excerpt),
            ),
        ),
        source_excerpt=excerpt,
        source_order_index=order,
        segmentation_profile_id='source_projection_segments',
        segmentation_profile_version='1.0.0',
        content_fingerprint=str(order) * 64,
        created_at='2026-08-18T20:00:00Z',
    )


def test_semantic_stages_run_per_source_analysis_unit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_stage(**kwargs):
        calls.append(dict(kwargs))
        source_analysis_unit_id = kwargs.get(
            'source_analysis_unit_id'
        )
        report = {
            'team_id': kwargs['stage_name'],
            'task_name': kwargs['stage_name'],
            'summary': {},
        }
        if source_analysis_unit_id is not None:
            report['source_analysis_unit_id'] = (
                source_analysis_unit_id
            )
        return [], report

    def fake_report(**kwargs):
        output = kwargs['report_output_path']
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text('# Report\n', encoding='utf-8')

    def fake_summaries(**kwargs):
        return {}

    monkeypatch.setattr(
        'modules.ingestion.team_agentic_pipeline.'
        'run_stage_with_consensus',
        fake_stage,
    )
    monkeypatch.setattr(
        'modules.ingestion.team_agentic_pipeline.'
        'write_ingestion_review_report',
        fake_report,
    )
    monkeypatch.setattr(
        'modules.ingestion.team_agentic_pipeline.'
        'write_run_summaries',
        fake_summaries,
    )

    raw_input = tmp_path / 'projection.txt'
    raw_input.write_text(
        'First source unit.\n\nSecond source unit.',
        encoding='utf-8',
    )
    report = tmp_path / 'report.md'
    units = (
        unit('SAU-000001', 1, 'First source unit.'),
        unit('SAU-000002', 2, 'Second source unit.'),
    )

    result = run_team_agentic_ingestion(
        project_root=tmp_path,
        task_id='TASK_SOURCE_ANCHORED',
        recipe_id='REC_INGESTION_001',
        raw_input_path=raw_input,
        report_output_path=report,
        source_analysis_units=units,
        dry_run=True,
    )

    assert result.source_analysis_unit_ids == (
        'SAU-000001',
        'SAU-000002',
    )

    semantic_calls = calls[:6]
    assert tuple(
        call['stage_name'] for call in semantic_calls
    ) == (
        '01_legacy_interpretation',
        '02_evidence_classification',
        '03_derivation_assessment',
        '01_legacy_interpretation',
        '02_evidence_classification',
        '03_derivation_assessment',
    )
    assert tuple(
        call['source_analysis_unit_id']
        for call in semantic_calls
    ) == (
        'SAU-000001',
        'SAU-000001',
        'SAU-000001',
        'SAU-000002',
        'SAU-000002',
        'SAU-000002',
    )

    for call in semantic_calls[:3]:
        assert 'SAU-000001' in str(call['input_text'])
        assert 'First source unit.' in str(call['input_text'])
        assert 'Second source unit.' not in str(call['input_text'])

    for call in semantic_calls[3:]:
        assert 'SAU-000002' in str(call['input_text'])
        assert 'Second source unit.' in str(call['input_text'])
        assert 'First source unit.' not in str(call['input_text'])

    assert calls[6]['stage_name'] == '04_completeness_review'
    assert calls[6].get('source_analysis_unit_id') is None
