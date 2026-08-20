"""D5 tests for the compiled ADR-026 D3+D4 Processing boundary."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import modules.semantic_consolidation.processing_adapter as adapter
from modules.project_ingestion.service import (
    ProjectBoundIngestionService,
)


def test_compiled_source_anchored_pipeline_runs_d3_before_d4(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls: list[tuple[str, object]] = []
    d3_result = SimpleNamespace(
        source_analysis_unit_ids=(
            "SAU-000001",
            "SAU-000002",
        )
    )
    d4_result = SimpleNamespace(
        synthesized_element_subject_count=2
    )

    def fake_d3(**kwargs):
        calls.append(("d3", dict(kwargs)))
        return d3_result

    def fake_d4(**kwargs):
        calls.append(("d4", dict(kwargs)))
        assert kwargs["source_anchored_result"] is d3_result
        return d4_result

    monkeypatch.setattr(
        adapter,
        "consolidate_phase_f_source_analysis_unit_proposals",
        fake_d3,
    )
    monkeypatch.setattr(
        adapter,
        "synthesize_phase_f_source_analysis_units",
        fake_d4,
    )

    phase_f_result = SimpleNamespace(
        source_analysis_unit_ids=(
            "SAU-000001",
            "SAU-000002",
        )
    )
    result = (
        adapter.consolidate_phase_f_source_anchored_pipeline(
            project_id="123456",
            processing_run_id="RUN-000001",
            created_at_utc="2026-08-18T20:00:00Z",
            phase_f_result=phase_f_result,
            phase_f_root=tmp_path / "phase_f",
            repository_root=tmp_path,
            provider="openai",
            model="gpt-test",
            api_key="secret",
            dry_run=False,
        )
    )

    assert tuple(name for name, _ in calls) == (
        "d3",
        "d4",
    )
    assert result.source_anchored_result is d3_result
    assert result.cross_unit_result is d4_result

    for _, kwargs in calls:
        assert kwargs["project_id"] == "123456"
        assert kwargs["processing_run_id"] == "RUN-000001"
        assert kwargs["phase_f_result"] is phase_f_result
        assert kwargs["provider"] == "openai"
        assert kwargs["model"] == "gpt-test"
        assert kwargs["api_key"] == "secret"
        assert kwargs["dry_run"] is False


def test_project_ingestion_defaults_to_compiled_source_anchored_pipeline(
    tmp_path: Path,
) -> None:
    service = ProjectBoundIngestionService(
        root=tmp_path / "projects",
        repository_root=tmp_path,
        pipeline_runner=lambda **kwargs: None,
    )

    assert (
        service._semantic_consolidator
        is adapter.consolidate_phase_f_source_anchored_pipeline
    )
