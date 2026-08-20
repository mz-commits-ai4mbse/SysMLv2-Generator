"""D4 processing-adapter test from D3 local subjects to cross-unit synthesis."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from modules.semantic_consolidation import processing_adapter as adapter


PROJECT_ID = "887027"
PROCESSING_RUN_ID = "RUN-000001"
TIMESTAMP = "2026-08-18T20:30:00Z"


def _write_derivation_result(
    root: Path,
    *,
    source_analysis_unit_id: str,
    agent_id: str,
    persona_id: str,
    candidate_name: str,
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
        / f"{agent_id}_run_01.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_text = json.dumps(
        {
            "candidate_model_elements": [
                {
                    "candidate_id": "ELEM_001",
                    "candidate_name": candidate_name,
                    "element_type": "actor",
                    "description": candidate_name,
                    "assigned_source_information": [
                        {
                            "source_info_id": "SRC_INFO_001",
                            "source_statement": (
                                "A remote expert participates."
                            ),
                        }
                    ],
                }
            ],
            "explicit_source_links": [],
        },
        ensure_ascii=False,
    )
    wrapper = {
        "agent_id": agent_id,
        "persona_id": persona_id,
        "run_index": 1,
        "source_analysis_unit_id": source_analysis_unit_id,
        "output_text": output_text,
    }
    output_path.write_text(
        json.dumps(wrapper, ensure_ascii=False),
        encoding="utf-8",
    )
    return SimpleNamespace(
        output_path=output_path,
        source_analysis_unit_id=source_analysis_unit_id,
    )


def test_d4_reconstructs_local_subjects_and_persists_cross_unit_result(
    tmp_path: Path,
    monkeypatch,
) -> None:
    first = _write_derivation_result(
        tmp_path,
        source_analysis_unit_id="SAU-000001",
        agent_id="agent-a",
        persona_id="persona-a",
        candidate_name="Remote Expert",
    )
    second = _write_derivation_result(
        tmp_path,
        source_analysis_unit_id="SAU-000002",
        agent_id="agent-b",
        persona_id="persona-b",
        candidate_name="External Expert",
    )
    phase_f_result = SimpleNamespace(
        agent_results=[first, second],
        source_analysis_unit_ids=(
            "SAU-000001",
            "SAU-000002",
        ),
    )
    phase_f_root = tmp_path / "phase_f"

    local = adapter.consolidate_phase_f_source_analysis_unit_proposals(
        project_id=PROJECT_ID,
        processing_run_id=PROCESSING_RUN_ID,
        created_at_utc=TIMESTAMP,
        phase_f_result=phase_f_result,
        phase_f_root=phase_f_root,
        repository_root=tmp_path,
        provider="openai",
        model="gpt-test",
        api_key=None,
        dry_run=True,
    )

    def comparator(*, payload, proposal_kind, **_kwargs):
        assert proposal_kind == "element"
        refs = tuple(
            item["local_subject_ref"]
            for item in payload["local_subjects"]
        )
        assert len(refs) == 2
        return {
            "schema_version": "1.0.0",
            "method": "semantic_model",
            "trace_ref": "trace:test",
            "groups": [{"member_refs": list(refs)}],
            "comparisons": [
                {
                    "left_ref": refs[0],
                    "right_ref": refs[1],
                    "outcome": "equivalent",
                    "rationale": "Same remote expert concept.",
                }
            ],
        }

    monkeypatch.setattr(
        adapter,
        "_run_live_cross_unit_comparator",
        comparator,
    )

    result = adapter.synthesize_phase_f_source_analysis_units(
        project_id=PROJECT_ID,
        processing_run_id=PROCESSING_RUN_ID,
        created_at_utc=TIMESTAMP,
        phase_f_result=phase_f_result,
        source_anchored_result=local,
        phase_f_root=phase_f_root,
        repository_root=tmp_path,
        provider="openai",
        model="gpt-test",
        api_key=None,
        dry_run=False,
    )

    assert result.local_element_subject_count == 2
    assert result.synthesized_element_subject_count == 1
    assert result.local_relationship_subject_count == 0
    assert result.synthesized_relationship_subject_count == 0
    assert result.element_degraded_to_singletons is False
    assert result.artifact_path.is_file()

    payload = json.loads(
        result.artifact_path.read_text(encoding="utf-8")
    )
    synthesis = payload["cross_unit_semantic_synthesis"]
    assert synthesis["source_analysis_unit_ids"] == [
        "SAU-000001",
        "SAU-000002",
    ]
    assert len(synthesis["local_element_subjects"]) == 2
    assert len(synthesis["synthesized_element_subjects"]) == 1
    assert synthesis["synthesized_element_subjects"][0][
        "source_analysis_unit_ids"
    ] == ["SAU-000001", "SAU-000002"]
