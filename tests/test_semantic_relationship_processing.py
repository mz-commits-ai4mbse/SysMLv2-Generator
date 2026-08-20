"""Processing integration tests for C3 relationship consolidation."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import json

from modules.semantic_consolidation.processing_adapter import (
    consolidate_phase_f_element_proposals,
)


def _write_derivation(
    root: Path,
    *,
    persona: str,
    run_index: int,
    elements: list[dict[str, object]],
    links: list[dict[str, object]],
) -> Path:
    path = (
        root
        / "agent_outputs"
        / "03_derivation_assessment"
        / f"{persona}_{run_index}.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "candidate_model_elements": elements,
        "explicit_source_links": links,
    }
    wrapper = {
        "team_id": "team-1",
        "agent_id": f"agent-{persona}",
        "persona_id": persona,
        "run_index": run_index,
        "status": "complete",
        "output_text": json.dumps(output),
    }
    path.write_text(
        json.dumps(wrapper),
        encoding="utf-8",
    )
    return path


def test_dry_run_persists_relationship_singleton_artifact(tmp_path: Path):
    repository_root = tmp_path / "repo"
    phase_root = repository_root / "phase-f"
    first = _write_derivation(
        phase_root,
        persona="A",
        run_index=1,
        elements=[
            {
                "candidate_id": "E1",
                "candidate_name": "operator",
                "element_type": "actor",
                "description": "Microscope operator",
                "assigned_source_information": [
                    {
                        "source_info_id": "S1",
                        "source_statement": "An operator uses the system.",
                    }
                ],
            },
            {
                "candidate_id": "E2",
                "candidate_name": "live image",
                "element_type": "item",
                "description": "Live microscope image",
                "assigned_source_information": [
                    {
                        "source_info_id": "S2",
                        "source_statement": "The system provides a live image.",
                    }
                ],
            },
        ],
        links=[
            {
                "link_id": "L1",
                "source_element_candidate": "E1",
                "link_type": "observes",
                "target_element_candidate": "live image",
                "source_basis": ["S1", "S2"],
                "source_statement": (
                    "The operator observes the live microscope image."
                ),
                "confidence": "high",
                "rationale_summary": "Directly supported by source.",
            }
        ],
    )
    phase_f_result = SimpleNamespace(
        run_id="phase-f-run",
        agent_results=[
            SimpleNamespace(output_path=first),
        ],
    )

    result = consolidate_phase_f_element_proposals(
        project_id="123456",
        processing_run_id="RUN-000001",
        created_at_utc="2026-08-18T00:00:00Z",
        phase_f_result=phase_f_result,
        phase_f_root=phase_root,
        repository_root=repository_root,
        provider="openai",
        model="gpt-test",
        api_key=None,
        dry_run=True,
    )

    assert result.relationship_artifact_path is not None
    assert result.relationship_artifact_path.is_file()
    assert result.relationship_comparator_trace_path is None
    assert result.relationship_degraded_to_singletons is True
    assert result.relationship_proposal_count == 1
    assert result.relationship_semantic_subject_count == 1

    payload = json.loads(
        result.relationship_artifact_path.read_text(
            encoding="utf-8"
        )
    )
    artifact = payload["semantic_consolidation"]
    assert artifact["proposals"][0]["proposal_kind"] == "relationship"
    assert artifact["subjects"][0]["proposal_kind"] == "relationship"
    assert payload["execution"]["proposal_count"] == 1
    assert payload["execution"][
        "element_semantic_artifact_fingerprint"
    ]


def test_unresolved_relationship_endpoint_is_persisted_for_human_review(
    tmp_path: Path,
):
    repository_root = tmp_path / "repo"
    phase_root = repository_root / "phase-f"
    first = _write_derivation(
        phase_root,
        persona="A",
        run_index=1,
        elements=[
            {
                "candidate_id": "E1",
                "candidate_name": "operator",
                "element_type": "actor",
                "description": "Microscope operator",
                "assigned_source_information": [
                    {
                        "source_info_id": "S1",
                        "source_statement": "An operator uses the system.",
                    }
                ],
            }
        ],
        links=[
            {
                "link_id": "L1",
                "source_element_candidate": "E1",
                "link_type": "observes",
                "target_element_candidate": "missing element",
                "source_basis": ["S1"],
                "source_statement": "Operator observes something.",
                "confidence": "medium",
                "rationale_summary": "Incomplete endpoint.",
            }
        ],
    )
    phase_f_result = SimpleNamespace(
        run_id="phase-f-run",
        agent_results=[SimpleNamespace(output_path=first)],
    )

    result = consolidate_phase_f_element_proposals(
        project_id="123456",
        processing_run_id="RUN-000001",
        created_at_utc="2026-08-18T00:00:00Z",
        phase_f_result=phase_f_result,
        phase_f_root=phase_root,
        repository_root=repository_root,
        provider="openai",
        model="gpt-test",
        api_key=None,
        dry_run=True,
    )

    assert result.relationship_artifact_path is not None
    assert result.relationship_artifact_path.exists()
    assert result.relationship_proposal_count == 1
    assert (
        "relationship_endpoint_unresolved_human_review_required"
        in result.relationship_warning_codes
    )

    payload = json.loads(
        result.relationship_artifact_path.read_text(encoding="utf-8")
    )
    execution = payload["execution"]

    assert (
        "relationship_endpoint_unresolved_human_review_required"
        in execution["warning_codes"]
    )

    findings = execution["endpoint_resolution_findings"]
    assert len(findings) == 1

    finding = findings[0]
    assert finding["relationship_proposal_ref"].endswith(
        "#relationship:L1"
    )
    assert finding["endpoint_role"] == "target"
    assert finding["endpoint_token"] == "missing element"
    assert finding["resolution_status"] == "unresolved"
    assert finding["candidate_proposal_refs"] == []

