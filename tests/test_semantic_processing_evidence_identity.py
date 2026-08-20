# Regression tests for BLK-003.1 semantic evidence identity.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from modules.semantic_consolidation.processing_adapter import (
    build_phase_f_element_semantic_input,
)


def _write_derivation_wrapper(
    repository_root: Path,
    *,
    elements: list[dict[str, object]],
) -> Path:
    path = (
        repository_root
        / "data"
        / "projects"
        / "123456"
        / "runs"
        / "RUN-000001"
        / "work"
        / "agentic_ingestion"
        / "ATT-000001"
        / "phase_f"
        / "agent_outputs"
        / "03_derivation_assessment"
        / "team_derivation_assessment"
        / "agent_test"
        / "agent_test_run_01.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "candidate_model_elements": elements,
        "explicit_source_links": [],
    }
    wrapper = {
        "agent_id": "AGENT_TEST",
        "persona_id": "PERSONA_TEST",
        "run_index": 1,
        "output_text": json.dumps(output),
    }
    path.write_text(
        json.dumps(wrapper, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _element(
    candidate_id: str,
    candidate_name: str,
    statement: str,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "element_type": "part",
        "description": f"Candidate {candidate_name}",
        "assigned_source_information": [
            {
                "source_info_id": "SRC_INFO_003",
                "source_statement": statement,
            }
        ],
    }


def _build(repository_root: Path, output_path: Path):
    phase_f_result = SimpleNamespace(
        agent_results=[
            SimpleNamespace(output_path=output_path)
        ]
    )
    return build_phase_f_element_semantic_input(
        phase_f_result=phase_f_result,
        repository_root=repository_root,
    )


def test_same_source_info_with_different_statements_is_distinct_evidence(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    first = (
        "The microscope operator works at the microscope workstation."
    )
    second = (
        "The remote expert joins from a separate client application."
    )
    output_path = _write_derivation_wrapper(
        repository_root,
        elements=[
            _element("ELEM_001", "microscope operator", first),
            _element("ELEM_002", "remote expert", second),
        ],
    )

    result = _build(repository_root, output_path)

    assert len(result.proposals) == 2
    assert len(result.evidence) == 2

    evidence_by_statement = {
        item.statement: item.evidence_ref
        for item in result.evidence
    }
    assert set(evidence_by_statement) == {first, second}
    assert (
        evidence_by_statement[first]
        != evidence_by_statement[second]
    )

    for statement, evidence_ref in evidence_by_statement.items():
        assert "#source-info:SRC_INFO_003:statement-sha256:" in evidence_ref
        assert evidence_ref.endswith(
            hashlib.sha256(
                statement.encode("utf-8")
            ).hexdigest()
        )

    referenced = {
        ref
        for proposal in result.proposals
        for ref in proposal.evidence_refs
    }
    assert referenced == set(evidence_by_statement.values())


def test_identical_statement_for_same_source_info_deduplicates_evidence(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    statement = (
        "The remote expert joins from a separate client application."
    )
    output_path = _write_derivation_wrapper(
        repository_root,
        elements=[
            _element("ELEM_001", "remote expert", statement),
            _element(
                "ELEM_002",
                "separate client application",
                statement,
            ),
        ],
    )

    result = _build(repository_root, output_path)

    assert len(result.proposals) == 2
    assert len(result.evidence) == 1

    evidence_ref = result.evidence[0].evidence_ref
    assert all(
        proposal.evidence_refs == (evidence_ref,)
        for proposal in result.proposals
    )
