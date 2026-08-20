"""D3 tests for Source Analysis Unit-local semantic consolidation."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from modules.semantic_consolidation.errors import (
    SemanticConsolidationIntegrityError,
)
from modules.semantic_consolidation import processing_adapter as adapter


PROJECT_ID = "887027"
PROCESSING_RUN_ID = "RUN-000001"
TIMESTAMP = "2026-08-18T20:30:00Z"


def _candidate(
    candidate_id: str,
    name: str,
    statement: str,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "candidate_name": name,
        "element_type": "actor",
        "description": f"Candidate {name}",
        "assigned_source_information": [
            {
                "source_info_id": "SRC_INFO_001",
                "source_statement": statement,
            }
        ],
    }


def _write_derivation_result(
    root: Path,
    *,
    source_analysis_unit_id: str,
    agent_id: str,
    persona_id: str,
    run_index: int,
    candidates: list[dict[str, object]],
    links: list[dict[str, object]] | None = None,
    result_source_analysis_unit_id: str | None = None,
    wrapper_source_analysis_unit_id: str | None = None,
) -> object:
    output_path = (
        root
        / "data"
        / "projects"
        / PROJECT_ID
        / "runs"
        / PROCESSING_RUN_ID
        / "work"
        / "phase_f"
        / "agent_outputs"
        / adapter.DERIVATION_STAGE_DIRECTORY
        / source_analysis_unit_id
        / "team_derivation_assessment"
        / agent_id
        / f"{agent_id}_run_{run_index:02d}.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_text = json.dumps(
        {
            "candidate_model_elements": candidates,
            "explicit_source_links": links or [],
        },
        ensure_ascii=False,
    )
    wrapper = {
        "agent_id": agent_id,
        "persona_id": persona_id,
        "run_index": run_index,
        "source_analysis_unit_id": (
            source_analysis_unit_id
            if wrapper_source_analysis_unit_id is None
            else wrapper_source_analysis_unit_id
        ),
        "output_text": output_text,
    }
    output_path.write_text(
        json.dumps(wrapper, ensure_ascii=False),
        encoding="utf-8",
    )

    return SimpleNamespace(
        output_path=output_path,
        source_analysis_unit_id=(
            source_analysis_unit_id
            if result_source_analysis_unit_id is None
            else result_source_analysis_unit_id
        ),
    )


def _phase_f_result(
    results: list[object],
    ids: tuple[str, ...],
) -> object:
    return SimpleNamespace(
        agent_results=results,
        source_analysis_unit_ids=ids,
    )


def _all_strings(value: object) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            found.extend(_all_strings(key))
            found.extend(_all_strings(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            found.extend(_all_strings(item))
    return found


def test_element_input_is_strictly_scoped_to_one_source_analysis_unit(
    tmp_path: Path,
) -> None:
    first = _write_derivation_result(
        tmp_path,
        source_analysis_unit_id="SAU-000001",
        agent_id="agent-a",
        persona_id="persona-a",
        run_index=1,
        candidates=[
            _candidate(
                "ELEM_001",
                "Remote Expert",
                "A remote expert joins.",
            )
        ],
    )
    second = _write_derivation_result(
        tmp_path,
        source_analysis_unit_id="SAU-000002",
        agent_id="agent-b",
        persona_id="persona-b",
        run_index=1,
        candidates=[
            _candidate(
                "ELEM_001",
                "Microscope Operator",
                "The operator remains responsible.",
            )
        ],
    )

    inputs = adapter.build_phase_f_element_semantic_input(
        phase_f_result=_phase_f_result(
            [first, second],
            ("SAU-000001", "SAU-000002"),
        ),
        repository_root=tmp_path,
        source_analysis_unit_id="SAU-000001",
    )

    assert inputs.source_analysis_unit_id == "SAU-000001"
    assert len(inputs.proposals) == 1
    assert "SAU-000001" in inputs.proposals[0].proposal_ref
    assert "SAU-000002" not in inputs.proposals[0].proposal_ref
    assert inputs.expected_persona_ids == ("persona-a",)
    assert len(inputs.upstream_artifacts) == 1


def test_scope_binding_mismatch_is_integrity_failure(
    tmp_path: Path,
) -> None:
    result = _write_derivation_result(
        tmp_path,
        source_analysis_unit_id="SAU-000001",
        agent_id="agent-a",
        persona_id="persona-a",
        run_index=1,
        candidates=[
            _candidate(
                "ELEM_001",
                "Remote Expert",
                "A remote expert joins.",
            )
        ],
        wrapper_source_analysis_unit_id="SAU-000002",
    )

    with pytest.raises(SemanticConsolidationIntegrityError):
        adapter.build_phase_f_element_semantic_input(
            phase_f_result=_phase_f_result(
                [result],
                ("SAU-000001",),
            ),
            repository_root=tmp_path,
            source_analysis_unit_id="SAU-000001",
        )


def test_zero_proposal_unit_is_valid_and_persisted_explicitly(
    tmp_path: Path,
) -> None:
    result = _write_derivation_result(
        tmp_path,
        source_analysis_unit_id="SAU-000001",
        agent_id="agent-a",
        persona_id="persona-a",
        run_index=1,
        candidates=[],
    )
    phase_root = tmp_path / "phase_f"

    consolidated = (
        adapter.consolidate_phase_f_source_analysis_unit_proposals(
            project_id=PROJECT_ID,
            processing_run_id=PROCESSING_RUN_ID,
            created_at_utc=TIMESTAMP,
            phase_f_result=_phase_f_result(
                [result],
                ("SAU-000001",),
            ),
            phase_f_root=phase_root,
            repository_root=tmp_path,
            provider="openai",
            model="test-model",
            api_key=None,
            dry_run=True,
        )
    )

    assert consolidated.element_proposal_count == 0
    assert consolidated.element_semantic_subject_count == 0
    unit_result = consolidated.unit_results[0]
    assert unit_result.source_analysis_unit_id == "SAU-000001"
    payload = json.loads(
        unit_result.artifact_path.read_text(encoding="utf-8")
    )
    assert payload["semantic_consolidation"] is None
    assert payload["execution"]["no_element_proposals"] is True
    assert payload["execution"]["source_analysis_unit_id"] == (
        "SAU-000001"
    )


def test_live_element_comparator_is_invoked_once_per_unit_not_globally(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _write_derivation_result(
        tmp_path,
        source_analysis_unit_id="SAU-000001",
        agent_id="agent-a",
        persona_id="persona-a",
        run_index=1,
        candidates=[
            _candidate(
                "ELEM_001",
                "Remote Expert",
                "A remote expert joins.",
            )
        ],
    )
    second = _write_derivation_result(
        tmp_path,
        source_analysis_unit_id="SAU-000002",
        agent_id="agent-b",
        persona_id="persona-b",
        run_index=1,
        candidates=[
            _candidate(
                "ELEM_001",
                "Microscope Operator",
                "The operator remains responsible.",
            )
        ],
    )
    calls: list[tuple[Path, tuple[str, ...]]] = []

    def fake_live_comparator(
        *,
        payload: dict[str, object],
        provider: str,
        model: str,
        api_key: str | None,
        trace_path: Path,
    ) -> dict[str, object]:
        del provider, model, api_key
        refs = tuple(
            sorted(
                {
                    value
                    for value in _all_strings(payload)
                    if "#element:" in value
                }
            )
        )
        calls.append((trace_path, refs))
        return {
            "comparisons": [],
            "groups": [
                {"member_proposal_refs": [ref]}
                for ref in refs
            ],
            "method": "semantic_model",
            "trace_ref": "llm-response:d3-test",
        }

    monkeypatch.setattr(
        adapter,
        "_run_live_comparator",
        fake_live_comparator,
    )

    phase_root = tmp_path / "phase_f"
    consolidated = (
        adapter.consolidate_phase_f_source_analysis_unit_proposals(
            project_id=PROJECT_ID,
            processing_run_id=PROCESSING_RUN_ID,
            created_at_utc=TIMESTAMP,
            phase_f_result=_phase_f_result(
                [first, second],
                ("SAU-000001", "SAU-000002"),
            ),
            phase_f_root=phase_root,
            repository_root=tmp_path,
            provider="openai",
            model="test-model",
            api_key=None,
            dry_run=False,
        )
    )

    assert consolidated.element_proposal_count == 2
    assert len(calls) == 2
    assert all(len(refs) == 1 for _, refs in calls)
    assert "SAU-000001" in calls[0][0].parts
    assert "SAU-000002" in calls[1][0].parts
    assert "SAU-000002" not in calls[0][1][0]
    assert "SAU-000001" not in calls[1][1][0]
    assert not (
        phase_root
        / "consensus_reports"
        / adapter.SEMANTIC_CONSOLIDATION_ARTIFACT_FILENAME
    ).exists()


def test_relationship_consolidation_is_persisted_inside_same_unit_scope(
    tmp_path: Path,
) -> None:
    result = _write_derivation_result(
        tmp_path,
        source_analysis_unit_id="SAU-000001",
        agent_id="agent-a",
        persona_id="persona-a",
        run_index=1,
        candidates=[
            _candidate(
                "ELEM_001",
                "Operator",
                "The operator controls the microscope.",
            ),
            _candidate(
                "ELEM_002",
                "Microscope",
                "The operator controls the microscope.",
            ),
        ],
        links=[
            {
                "link_id": "LINK_001",
                "source_element_candidate": "ELEM_001",
                "target_element_candidate": "ELEM_002",
                "link_type": "controls",
                "source_statement": (
                    "The operator controls the microscope."
                ),
            }
        ],
    )
    phase_root = tmp_path / "phase_f"

    consolidated = (
        adapter.consolidate_phase_f_source_analysis_unit_proposals(
            project_id=PROJECT_ID,
            processing_run_id=PROCESSING_RUN_ID,
            created_at_utc=TIMESTAMP,
            phase_f_result=_phase_f_result(
                [result],
                ("SAU-000001",),
            ),
            phase_f_root=phase_root,
            repository_root=tmp_path,
            provider="openai",
            model="test-model",
            api_key=None,
            dry_run=True,
        )
    )

    unit_result = consolidated.unit_results[0]
    assert unit_result.relationship_proposal_count == 1
    assert unit_result.relationship_artifact_path is not None
    assert "SAU-000001" in (
        unit_result.relationship_artifact_path.parts
    )
    payload = json.loads(
        unit_result.relationship_artifact_path.read_text(
            encoding="utf-8"
        )
    )
    assert payload["execution"]["source_analysis_unit_id"] == (
        "SAU-000001"
    )
    assert payload["execution"]["proposal_count"] == 1
