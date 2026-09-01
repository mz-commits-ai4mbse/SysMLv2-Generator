"""Atomic immutable repository for ADR-033 concern-centric PRC cycles."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import shutil
import uuid
from modules.project_fit import derive_project_fit_gate_state, validate_project_fit_assessment
from .case_persistence import (
    ConcernCentricProjectReconciliationCycleManifest,
    case_assessment_from_json, case_assessment_to_json,
    case_cycle_manifest_from_json, case_cycle_manifest_to_json,
    create_case_cycle_manifest,
    reconciliation_summary_from_json, reconciliation_summary_to_json,
    semantic_index_from_json, semantic_index_to_json,
    validate_case_assessment, validate_reconciliation_summary,
    validate_semantic_index_artifact,
)
from .errors import ProjectReconciliationPersistenceIntegrityError, ProjectReconciliationPersistenceValidationError
from .repository import ProjectReconciliationRepository

def _default_clock(): return datetime.now(timezone.utc)

class ConcernCentricProjectReconciliationRepository:
    def __init__(self, root=Path('data/projects'), *, clock=_default_clock, fit_repository=None):
        self.root=Path(root); self._clock=clock
        self._legacy=ProjectReconciliationRepository(root=self.root, clock=clock) if fit_repository is None else fit_repository

    def start_cycle(self, *, semantic_index, case_assessments: tuple, reconciliation_summary, project_fit_assessments: tuple):
        validate_semantic_index_artifact(semantic_index); validate_reconciliation_summary(reconciliation_summary)
        if reconciliation_summary.project_id!=semantic_index.project_id or reconciliation_summary.semantic_index_fingerprint!=semantic_index.content_fingerprint:
            raise ProjectReconciliationPersistenceIntegrityError('Summary does not bind the exact semantic index.')
        by_id={}
        for a in tuple(case_assessments):
            validate_case_assessment(a)
            if a.case_id in by_id: raise ProjectReconciliationPersistenceIntegrityError('Case assessment IDs are not unique.')
            by_id[a.case_id]=a
        expected=tuple(c.case_id for c in semantic_index.cases)
        if tuple(sorted(by_id))!=expected: raise ProjectReconciliationPersistenceIntegrityError('Case assessment population differs from semantic index.')
        assessments=tuple(by_id[i] for i in expected)
        for c,a in zip(semantic_index.cases,assessments):
            if a.project_id!=semantic_index.project_id or a.case_fingerprint!=c.case_fingerprint or a.member_subject_refs!=c.member_subject_refs or a.source_ids!=c.source_ids:
                raise ProjectReconciliationPersistenceIntegrityError('Case assessment does not bind its exact indexed Case.')
        fits=self._validate_fit_bindings(semantic_index, project_fit_assessments)
        existing=self.find_cycle_by_input_fingerprint(semantic_index.project_id, semantic_index.input_fingerprint)
        if existing is not None:
            if existing.semantic_index_fingerprint!=semantic_index.content_fingerprint or existing.case_assessment_fingerprints!=tuple(a.content_fingerprint for a in assessments) or existing.reconciliation_summary_fingerprint!=reconciliation_summary.content_fingerprint:
                raise ProjectReconciliationPersistenceIntegrityError('An immutable concern-centric cycle already binds the same exact S3 input with different semantic evidence.')
            return existing
        for fit in fits: self._legacy.publish_project_fit(fit)
        cycle_id=self._next_cycle_id(semantic_index.project_id)
        manifest=create_case_cycle_manifest(project_id=semantic_index.project_id,reconciliation_cycle_id=cycle_id,source_ids=semantic_index.source_ids,project_fit_fingerprints=tuple(sorted(f.assessment_fingerprint for f in fits)),semantic_input_fingerprint=semantic_index.input_fingerprint,semantic_index_fingerprint=semantic_index.content_fingerprint,case_assessment_fingerprints=tuple(a.content_fingerprint for a in assessments),reconciliation_summary_fingerprint=reconciliation_summary.content_fingerprint,created_at=self._timestamp())
        directory=self._cycle_dir(semantic_index.project_id,cycle_id)
        if directory.exists() or directory.is_symlink(): raise ProjectReconciliationPersistenceIntegrityError('Project Reconciliation cycle path is occupied.')
        directory.parent.mkdir(parents=True,exist_ok=True); temp=directory.parent/f'.{cycle_id}.tmp-{uuid.uuid4().hex}'
        if temp.exists() or temp.is_symlink(): raise ProjectReconciliationPersistenceIntegrityError('Temporary Project Reconciliation cycle path is occupied.')
        temp.mkdir()
        try:
            (temp/'manifest.json').write_text(case_cycle_manifest_to_json(manifest),encoding='utf-8')
            (temp/'semantic_index.json').write_text(semantic_index_to_json(semantic_index),encoding='utf-8')
            ad=temp/'case_assessments'; ad.mkdir()
            for a in assessments: (ad/f'{a.case_id}.json').write_text(case_assessment_to_json(a),encoding='utf-8')
            (temp/'reconciliation_summary.json').write_text(reconciliation_summary_to_json(reconciliation_summary),encoding='utf-8')
            temp.replace(directory)
        finally:
            if temp.exists(): shutil.rmtree(temp)
        if self.load_cycle(semantic_index.project_id,cycle_id)!=manifest or self.load_semantic_index(semantic_index.project_id,cycle_id)!=semantic_index or self.load_case_assessments(semantic_index.project_id,cycle_id)!=assessments or self.load_reconciliation_summary(semantic_index.project_id,cycle_id)!=reconciliation_summary:
            raise ProjectReconciliationPersistenceIntegrityError('Persisted concern-centric PRC differs from source.')
        return manifest

    def load_cycle(self, project_id, cycle_id):
        p=self._cycle_dir(project_id,cycle_id)/'manifest.json'; self._require_file(p,'concern-centric cycle manifest'); v=case_cycle_manifest_from_json(p.read_text(encoding='utf-8'))
        if v.project_id!=project_id or v.reconciliation_cycle_id!=cycle_id: raise ProjectReconciliationPersistenceIntegrityError('Concern-centric cycle manifest binding is invalid.')
        return v

    def load_semantic_index(self, project_id, cycle_id):
        m=self.load_cycle(project_id,cycle_id); p=self._cycle_dir(project_id,cycle_id)/'semantic_index.json'; self._require_file(p,'semantic index'); v=semantic_index_from_json(p.read_text(encoding='utf-8'))
        if v.project_id!=project_id or v.input_fingerprint!=m.semantic_input_fingerprint or v.content_fingerprint!=m.semantic_index_fingerprint or v.source_ids!=m.source_ids: raise ProjectReconciliationPersistenceIntegrityError('Persisted semantic index does not bind its cycle.')
        loaded_fits=[]
        for fp in m.project_fit_fingerprints:
            fit=self._legacy.load_project_fit(project_id,fp); validate_project_fit_assessment(fit)
            if derive_project_fit_gate_state(fit)!='admitted': raise ProjectReconciliationPersistenceIntegrityError('Persisted Project Fit is no longer an admitted exact binding.')
            loaded_fits.append(fit)
        if tuple(sorted(f.source_id for f in loaded_fits))!=m.source_ids: raise ProjectReconciliationPersistenceIntegrityError('Persisted Project Fit Sources differ from semantic index Sources.')
        return v

    def load_case_assessments(self, project_id, cycle_id):
        m=self.load_cycle(project_id,cycle_id); idx=self.load_semantic_index(project_id,cycle_id); d=self._cycle_dir(project_id,cycle_id)/'case_assessments'
        if not d.exists() or not d.is_dir() or d.is_symlink(): raise ProjectReconciliationPersistenceIntegrityError('Case assessment directory is unavailable.')
        paths=sorted(d.iterdir(),key=lambda p:p.name); expected=[f'{c.case_id}.json' for c in idx.cases]
        if [p.name for p in paths]!=expected or any(not p.is_file() or p.is_symlink() for p in paths): raise ProjectReconciliationPersistenceIntegrityError('Case assessment repository population is invalid.')
        vals=tuple(case_assessment_from_json(p.read_text(encoding='utf-8')) for p in paths)
        if tuple(v.content_fingerprint for v in vals)!=m.case_assessment_fingerprints: raise ProjectReconciliationPersistenceIntegrityError('Case assessment fingerprints differ from cycle manifest.')
        for c,v in zip(idx.cases,vals):
            if v.case_id!=c.case_id or v.case_fingerprint!=c.case_fingerprint or v.member_subject_refs!=c.member_subject_refs or v.source_ids!=c.source_ids: raise ProjectReconciliationPersistenceIntegrityError('Persisted Case assessment binding is invalid.')
        return vals

    def load_reconciliation_summary(self, project_id, cycle_id):
        m=self.load_cycle(project_id,cycle_id); idx=self.load_semantic_index(project_id,cycle_id); vals=self.load_case_assessments(project_id,cycle_id); p=self._cycle_dir(project_id,cycle_id)/'reconciliation_summary.json'; self._require_file(p,'reconciliation summary'); v=reconciliation_summary_from_json(p.read_text(encoding='utf-8'))
        if v.project_id!=project_id or v.semantic_index_fingerprint!=idx.content_fingerprint or v.content_fingerprint!=m.reconciliation_summary_fingerprint or v.case_count!=len(vals): raise ProjectReconciliationPersistenceIntegrityError('Persisted reconciliation summary binding is invalid.')
        return v

    def find_cycle_by_input_fingerprint(self, project_id, input_fingerprint):
        d=self.root/project_id/'project_reconciliation'/'cycles'
        if not d.exists(): return None
        matches=[]
        for path in sorted(d.iterdir(),key=lambda p:p.name):
            mp=path/'manifest.json'
            if not path.is_dir() or path.is_symlink() or not mp.is_file(): continue
            try: m=case_cycle_manifest_from_json(mp.read_text(encoding='utf-8'))
            except ProjectReconciliationPersistenceValidationError: continue
            if m.semantic_input_fingerprint==input_fingerprint: matches.append(m)
        if len(matches)>1: raise ProjectReconciliationPersistenceIntegrityError('Multiple concern-centric cycles bind the same exact S3 input.')
        return None if not matches else matches[0]

    def _validate_fit_bindings(self, idx, fits):
        by={}
        for fit in tuple(fits):
            validate_project_fit_assessment(fit)
            if fit.project_id!=idx.project_id or derive_project_fit_gate_state(fit)!='admitted': raise ProjectReconciliationPersistenceValidationError('Only admitted Project Fit for this Project may enter concern-centric S3.')
            if fit.source_id in by: raise ProjectReconciliationPersistenceIntegrityError('More than one Project Fit binds one Engineering Source.')
            by[fit.source_id]=fit
        if tuple(sorted(by))!=idx.source_ids: raise ProjectReconciliationPersistenceIntegrityError('Project Fit Sources differ from semantic index Sources.')
        return tuple(by[s] for s in sorted(by))

    def _next_cycle_id(self, project_id):
        d=self.root/project_id/'project_reconciliation'/'cycles'; occupied=[]
        if d.exists():
            for p in d.iterdir():
                if p.is_dir() and not p.is_symlink() and len(p.name)==10 and p.name.startswith('PRC-') and p.name[4:].isdigit(): occupied.append(int(p.name[4:]))
        n=1 if not occupied else max(occupied)+1
        if n>999999: raise ProjectReconciliationPersistenceValidationError('Project Reconciliation cycle ID space exhausted.')
        return f'PRC-{n:06d}'
    def _cycle_dir(self, project_id, cycle_id):
        if len(cycle_id)!=10 or not cycle_id.startswith('PRC-') or not cycle_id[4:].isdigit(): raise ProjectReconciliationPersistenceValidationError('Project Reconciliation cycle ID is invalid.')
        return self.root/project_id/'project_reconciliation'/'cycles'/cycle_id
    @staticmethod
    def _require_file(path,label):
        if not path.exists() or not path.is_file() or path.is_symlink(): raise ProjectReconciliationPersistenceIntegrityError(f'{label} is unavailable.')
    def _timestamp(self):
        v=self._clock(); v=v if v.tzinfo is not None else v.replace(tzinfo=timezone.utc); return v.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
