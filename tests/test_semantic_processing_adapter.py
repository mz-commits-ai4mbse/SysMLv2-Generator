from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from modules.semantic_consolidation.processing_adapter import (
    build_phase_f_element_semantic_input,
    consolidate_phase_f_element_proposals,
)


@dataclass
class _Run:
    output_path: Path


@dataclass
class _PhaseF:
    agent_results: list[_Run]


def _write_derivation(root: Path, *, persona: str, run_index: int, candidate_name: str) -> Path:
    path = (
        root
        / 'phase_f'
        / 'agent_outputs'
        / '03_derivation_assessment'
        / 'team_derivation_assessment'
        / persona.lower()
        / f'{persona.lower()}_run_{run_index:02d}.json'
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    output = {
        'candidate_model_elements': [
            {
                'candidate_id': 'CAND_001',
                'element_type': 'system',
                'candidate_name': candidate_name,
                'description': 'Local workstation used by the microscope operator.',
                'source_basis': ['SRC_INFO_001'],
                'assigned_source_information': [
                    {
                        'source_info_id': 'SRC_INFO_001',
                        'source_statement': 'The microscope operator works at the microscope workstation.',
                        'assignment_type': 'defines_element',
                        'confidence': 'high',
                    }
                ],
                'confidence': 'high',
                'generation_readiness': 'ready',
                'missing_information': [],
                'rationale_summary': 'Explicitly named workstation.',
            }
        ],
        'explicit_source_links': [],
        'sysml_model_buildability': {},
        'missing_information_for_model_building': [],
        'possible_but_unsupported_interpretations': [],
        'model_artifact_assessments': [],
        'cross_artifact_observations': [],
        'blocked_generation_tasks': [],
    }
    wrapper = {
        'agent_id': f'AGENT_{persona}',
        'persona_id': persona,
        'run_index': run_index,
        'output_text': json.dumps(output),
    }
    path.write_text(json.dumps(wrapper), encoding='utf-8')
    return path


def test_build_input_preserves_persona_run_and_exact_evidence(tmp_path: Path) -> None:
    a = _write_derivation(tmp_path, persona='PERSONA_A', run_index=1, candidate_name='Microscope workstation')
    b = _write_derivation(tmp_path, persona='PERSONA_B', run_index=1, candidate_name='Local microscope workstation')
    value = build_phase_f_element_semantic_input(
        phase_f_result=_PhaseF(agent_results=[_Run(a), _Run(b)]),
        repository_root=tmp_path,
    )
    assert len(value.proposals) == 2
    assert value.expected_persona_ids == ('PERSONA_A', 'PERSONA_B')
    assert len(value.upstream_artifacts) == 2
    assert all(p.evidence_refs for p in value.proposals)


def test_dry_run_persists_safe_singleton_artifact_without_llm(tmp_path: Path) -> None:
    a = _write_derivation(tmp_path, persona='PERSONA_A', run_index=1, candidate_name='Microscope workstation')
    b = _write_derivation(tmp_path, persona='PERSONA_B', run_index=1, candidate_name='Local microscope workstation')
    phase_root = tmp_path / 'phase_f'
    value = consolidate_phase_f_element_proposals(
        project_id='123456',
        processing_run_id='RUN-000001',
        created_at_utc='2026-08-17T15:00:00Z',
        phase_f_result=_PhaseF(agent_results=[_Run(a), _Run(b)]),
        phase_f_root=phase_root,
        repository_root=tmp_path,
        provider='openai',
        model='gpt-test',
        api_key=None,
        dry_run=True,
    )
    assert value.degraded_to_singletons is True
    assert value.proposal_count == 2
    assert value.semantic_subject_count == 2
    assert value.comparator_trace_path is None
    persisted = json.loads(value.artifact_path.read_text(encoding='utf-8'))
    assert persisted['execution']['warning_codes'] == ['semantic_comparator_unavailable']
