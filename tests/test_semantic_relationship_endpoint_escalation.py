from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from modules.semantic_consolidation.processing_adapter import (
    build_phase_f_relationship_semantic_input,
)


def _wrapper_path(repository_root: Path) -> Path:
    return (
        repository_root
        / "data/projects/123456/runs/RUN-000001"
        / "work/agentic_ingestion/ATT-000001/phase_f"
        / "agent_outputs/03_derivation_assessment"
        / "team_derivation_assessment/agent_test"
        / "agent_test_run_01.json"
    )


def _write_wrapper(
    repository_root: Path,
    *,
    elements: list[dict[str, object]],
    links: list[dict[str, object]],
) -> Path:
    path = _wrapper_path(repository_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    wrapper = {
        "agent_id": "AGENT_TEST",
        "persona_id": "PERSONA_TEST",
        "run_index": 1,
        "output_text": json.dumps(
            {
                "candidate_model_elements": elements,
                "explicit_source_links": links,
            }
        ),
    }
    path.write_text(
        json.dumps(wrapper, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _element(candidate_id: str, candidate_name: str) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
    }


def _element_artifact(
    repository_root: Path,
    output_path: Path,
    *,
    subjects: dict[str, str],
):
    artifact_ref = output_path.relative_to(repository_root).as_posix()

    grouped: dict[str, list[str]] = {}
    for candidate_id, semantic_subject_id in subjects.items():
        grouped.setdefault(semantic_subject_id, []).append(
            f"{artifact_ref}#element:{candidate_id}"
        )

    return SimpleNamespace(
        subjects=tuple(
            SimpleNamespace(
                proposal_kind="element",
                semantic_subject_id=subject_id,
                member_proposal_refs=tuple(sorted(member_refs)),
            )
            for subject_id, member_refs in sorted(grouped.items())
        )
    )


def _phase_f_result(output_path: Path):
    return SimpleNamespace(
        agent_results=[
            SimpleNamespace(output_path=output_path)
        ]
    )


def test_unknown_relationship_endpoint_becomes_human_review_binding(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    output_path = _write_wrapper(
        repository_root,
        elements=[
            _element("ELEM_001", "microscope workstation"),
            _element("ELEM_002", "remote expert"),
        ],
        links=[
            {
                "link_id": "LINK_001",
                "source_element_candidate": "external pathologist",
                "target_element_candidate": "ELEM_001",
                "link_type": "association",
                "source_statement": (
                    "An external pathologist observes the workstation."
                ),
            }
        ],
    )
    artifact = _element_artifact(
        repository_root,
        output_path,
        subjects={
            "ELEM_001": "semantic:element:workstation",
            "ELEM_002": "semantic:element:remote-expert",
        },
    )

    result = build_phase_f_relationship_semantic_input(
        phase_f_result=_phase_f_result(output_path),
        repository_root=repository_root,
        element_artifact=artifact,
    )

    assert len(result.proposals) == 1
    proposal = result.proposals[0]

    assert proposal.proposal_ref.endswith("#relationship:LINK_001")
    assert (
        "#relationship-endpoint:LINK_001:source:unresolved:"
        in proposal.source_element_proposal_ref
    )
    assert proposal.source_semantic_subject_id.startswith(
        "semantic:unresolved-element-endpoint:"
    )
    assert proposal.target_semantic_subject_id == (
        "semantic:element:workstation"
    )

    assert result.warning_codes == (
        "relationship_endpoint_unresolved_human_review_required",
    )
    assert len(result.endpoint_resolution_findings) == 1
    finding = result.endpoint_resolution_findings[0]
    assert finding.endpoint_role == "source"
    assert finding.endpoint_token == "external pathologist"
    assert finding.resolution_status == "unresolved"
    assert finding.candidate_proposal_refs == ()

    assert len(result.evidence) == 1
    assert result.evidence[0].statement == (
        "An external pathologist observes the workstation."
    )
    assert proposal.evidence_refs == (
        result.evidence[0].evidence_ref,
    )


def test_ambiguous_relationship_endpoint_becomes_human_review_binding(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    output_path = _write_wrapper(
        repository_root,
        elements=[
            _element("ELEM_001", "remote expert"),
            _element("ELEM_002", "Remote   Expert"),
            _element("ELEM_003", "microscope workstation"),
        ],
        links=[
            {
                "link_id": "LINK_001",
                "source_element_candidate": "REMOTE EXPERT",
                "target_element_candidate": "ELEM_003",
                "link_type": "association",
                "source_statement": (
                    "The remote expert observes the workstation."
                ),
            }
        ],
    )
    artifact = _element_artifact(
        repository_root,
        output_path,
        subjects={
            "ELEM_001": "semantic:element:expert-a",
            "ELEM_002": "semantic:element:expert-b",
            "ELEM_003": "semantic:element:workstation",
        },
    )

    result = build_phase_f_relationship_semantic_input(
        phase_f_result=_phase_f_result(output_path),
        repository_root=repository_root,
        element_artifact=artifact,
    )

    assert len(result.proposals) == 1
    proposal = result.proposals[0]
    assert (
        "#relationship-endpoint:LINK_001:source:ambiguous:"
        in proposal.source_element_proposal_ref
    )
    assert proposal.source_semantic_subject_id.startswith(
        "semantic:unresolved-element-endpoint:"
    )
    assert result.warning_codes == (
        "relationship_endpoint_ambiguous_human_review_required",
    )

    finding = result.endpoint_resolution_findings[0]
    assert finding.resolution_status == "ambiguous"
    assert finding.endpoint_role == "source"
    assert finding.endpoint_token == "REMOTE EXPERT"
    assert len(finding.candidate_proposal_refs) == 2


def test_exact_relationship_endpoints_remain_exact_and_warning_free(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    output_path = _write_wrapper(
        repository_root,
        elements=[
            _element("ELEM_001", "remote expert"),
            _element("ELEM_002", "microscope workstation"),
        ],
        links=[
            {
                "link_id": "LINK_001",
                "source_element_candidate": "ELEM_001",
                "target_element_candidate": "microscope workstation",
                "link_type": "association",
                "source_statement": (
                    "The remote expert observes the workstation."
                ),
            }
        ],
    )
    artifact = _element_artifact(
        repository_root,
        output_path,
        subjects={
            "ELEM_001": "semantic:element:expert",
            "ELEM_002": "semantic:element:workstation",
        },
    )

    result = build_phase_f_relationship_semantic_input(
        phase_f_result=_phase_f_result(output_path),
        repository_root=repository_root,
        element_artifact=artifact,
    )

    proposal = result.proposals[0]
    artifact_ref = output_path.relative_to(repository_root).as_posix()

    assert proposal.source_element_proposal_ref == (
        f"{artifact_ref}#element:ELEM_001"
    )
    assert proposal.target_element_proposal_ref == (
        f"{artifact_ref}#element:ELEM_002"
    )
    assert proposal.source_semantic_subject_id == (
        "semantic:element:expert"
    )
    assert proposal.target_semantic_subject_id == (
        "semantic:element:workstation"
    )
    assert result.warning_codes == ()
    assert result.endpoint_resolution_findings == ()
