"""Focused tests for I2D.5D1 concern-centric PRC persistence."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import pytest
import modules.project_reconciliation.concern_repository as module
from modules.project_reconciliation.concern_repository import ConcernCentricProjectReconciliationRepository
from modules.project_reconciliation.repository import ProjectReconciliationRepository
from modules.project_reconciliation.errors import ProjectReconciliationPersistenceIntegrityError
from modules.project_semantic_reconciliation.case_contract import create_project_reconciliation_case_assessment, create_project_semantic_index_artifact, derive_project_reconciliation_summary
from modules.project_semantic_reconciliation.case_types import ReconciliationClaimGroupProposal, SemanticIndexGroupProposal

@dataclass(frozen=True)
class Subject: subject_ref:str; source_id:str
@dataclass(frozen=True)
class Fit: project_id:str; source_id:str; assessment_fingerprint:str
class FitRepository:
    def __init__(self): self.values={}
    def publish_project_fit(self,fit): self.values[fit.assessment_fingerprint]=fit; return fit
    def load_project_fit(self,project_id,fp):
        fit=self.values[fp]
        if fit.project_id!=project_id: raise RuntimeError('bad project')
        return fit

def clock(): return datetime(2026,8,31,20,30,tzinfo=timezone.utc)
def evidence():
    left=Subject('project_subject:SRC-000001:SP-000001:CSUB-000001','SRC-000001'); right=Subject('project_subject:SRC-000002:SP-000002:CSUB-000002','SRC-000002'); unique=Subject('project_subject:SRC-000003:SP-000003:CSUB-000003','SRC-000003')
    idx=create_project_semantic_index_artifact(project_id='308131',input_fingerprint='a'*64,subjects=(left,right,unique),group_proposals=(SemanticIndexGroupProposal('Remote client',(left.subject_ref,right.subject_ref)),SemanticIndexGroupProposal('Audio',(unique.subject_ref,))))
    multi=next(c for c in idx.cases if not c.singleton); single=next(c for c in idx.cases if c.singleton)
    conflict=create_project_reconciliation_case_assessment(semantic_index=idx,case_id=multi.case_id,shared_concern='Remote client classification',outcome='potential_conflict',summary='Sources classify the remote client differently.',shared_concepts=('remote client',),material_differences=('actor versus logical element',),claim_group_proposals=(ReconciliationClaimGroupProposal('actor',(multi.member_subject_refs[0],)),ReconciliationClaimGroupProposal('logical element',(multi.member_subject_refs[1],))),llm_provider='openai',llm_model='gpt-test',llm_response_id='resp-1')
    one=create_project_reconciliation_case_assessment(semantic_index=idx,case_id=single.case_id,shared_concern=single.group_label,outcome='unique',summary='No cross-source counterpart.')
    assessments=tuple(sorted((conflict,one),key=lambda a:a.case_id)); summary=derive_project_reconciliation_summary(semantic_index=idx,assessments=assessments)
    fits=(Fit('308131','SRC-000001','1'*64),Fit('308131','SRC-000002','2'*64),Fit('308131','SRC-000003','3'*64))
    return idx,assessments,summary,fits
@pytest.fixture(autouse=True)
def patch_fit(monkeypatch):
    monkeypatch.setattr(module,'validate_project_fit_assessment',lambda fit:None); monkeypatch.setattr(module,'derive_project_fit_gate_state',lambda fit:'admitted')
def repository(tmp_path): return ConcernCentricProjectReconciliationRepository(root=tmp_path,clock=clock,fit_repository=FitRepository())

def test_v2_cycle_persists_exact_concern_centric_bundle(tmp_path):
    repo=repository(tmp_path); idx,assessments,summary,fits=evidence(); m=repo.start_cycle(semantic_index=idx,case_assessments=assessments,reconciliation_summary=summary,project_fit_assessments=fits)
    assert m.schema_version=='2.0.0'; assert repo.load_semantic_index('308131','PRC-000001')==idx; assert repo.load_case_assessments('308131','PRC-000001')==assessments; assert repo.load_reconciliation_summary('308131','PRC-000001')==summary
    cycle=tmp_path/'308131'/'project_reconciliation'/'cycles'/'PRC-000001'; assert (cycle/'semantic_index.json').is_file(); assert (cycle/'reconciliation_summary.json').is_file(); assert not (cycle/'semantic_reconciliation.json').exists()
def test_same_exact_input_and_evidence_is_idempotent(tmp_path):
    repo=repository(tmp_path); idx,a,s,f=evidence(); first=repo.start_cycle(semantic_index=idx,case_assessments=a,reconciliation_summary=s,project_fit_assessments=f); second=repo.start_cycle(semantic_index=idx,case_assessments=a,reconciliation_summary=s,project_fit_assessments=f); assert first==second
    assert [p.name for p in (tmp_path/'308131'/'project_reconciliation'/'cycles').iterdir()]==['PRC-000001']
def test_same_input_with_different_semantic_evidence_fails_closed(tmp_path):
    repo=repository(tmp_path); idx,a,s,f=evidence(); repo.start_cycle(semantic_index=idx,case_assessments=a,reconciliation_summary=s,project_fit_assessments=f)
    subjects=(Subject(idx.subject_refs[0],'SRC-000001'),Subject(idx.subject_refs[1],'SRC-000002'),Subject(idx.subject_refs[2],'SRC-000003'))
    altered=create_project_semantic_index_artifact(project_id=idx.project_id,input_fingerprint=idx.input_fingerprint,subjects=subjects,group_proposals=tuple(SemanticIndexGroupProposal('renamed '+c.group_label,c.member_subject_refs) for c in idx.cases))
    altered_summary=derive_project_reconciliation_summary(semantic_index=altered,assessments=a)
    with pytest.raises(ProjectReconciliationPersistenceIntegrityError,match='different semantic evidence'): repo.start_cycle(semantic_index=altered,case_assessments=a,reconciliation_summary=altered_summary,project_fit_assessments=f)
def test_tampered_semantic_index_fails_closed(tmp_path):
    repo=repository(tmp_path); idx,a,s,f=evidence(); repo.start_cycle(semantic_index=idx,case_assessments=a,reconciliation_summary=s,project_fit_assessments=f); p=tmp_path/'308131'/'project_reconciliation'/'cycles'/'PRC-000001'/'semantic_index.json'; p.write_text(p.read_text().replace('Remote client','Tampered concern'))
    with pytest.raises(ProjectReconciliationPersistenceIntegrityError,match='content fingerprint'): repo.load_semantic_index('308131','PRC-000001')
def test_fit_sources_must_exactly_match_semantic_index(tmp_path):
    repo=repository(tmp_path); idx,a,s,f=evidence()
    with pytest.raises(ProjectReconciliationPersistenceIntegrityError,match='Sources differ'): repo.start_cycle(semantic_index=idx,case_assessments=a,reconciliation_summary=s,project_fit_assessments=f[:2])
def test_legacy_repository_can_list_v2_manifest_but_not_fake_s3(tmp_path):
    repo=repository(tmp_path); idx,a,s,f=evidence(); repo.start_cycle(semantic_index=idx,case_assessments=a,reconciliation_summary=s,project_fit_assessments=f); legacy=ProjectReconciliationRepository(root=tmp_path); latest=legacy.latest_cycle('308131'); assert latest.schema_version=='2.0.0'; assert latest.reconciliation_mode=='concern_centric_cases'
    with pytest.raises(ProjectReconciliationPersistenceIntegrityError,match='has no legacy semantic_reconciliation'): legacy.load_semantic_reconciliation('308131','PRC-000001')
def test_case_assessment_population_tampering_fails_closed(tmp_path):
    repo=repository(tmp_path); idx,a,s,f=evidence(); repo.start_cycle(semantic_index=idx,case_assessments=a,reconciliation_summary=s,project_fit_assessments=f); d=tmp_path/'308131'/'project_reconciliation'/'cycles'/'PRC-000001'/'case_assessments'; (d/'CASE-999999.json').write_text('{}')
    with pytest.raises(ProjectReconciliationPersistenceIntegrityError,match='population is invalid'): repo.load_case_assessments('308131','PRC-000001')
