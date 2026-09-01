"""Immutable ADR-033 concern-centric PRC persistence contracts."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import re

from modules.project_semantic_reconciliation.case_types import (
    PROJECT_RECONCILIATION_CASE_ASSESSMENT_SCHEMA_VERSION,
    PROJECT_RECONCILIATION_CASE_OUTCOMES,
    PROJECT_RECONCILIATION_SUMMARY_SCHEMA_VERSION,
    PROJECT_SEMANTIC_INDEX_SCHEMA_VERSION,
    PROJECT_SEMANTIC_INDEX_PROVENANCE_SCHEMA_VERSION,
    ProjectReconciliationCase,
    ProjectReconciliationCaseAssessment,
    ProjectReconciliationSummary,
    ProjectSemanticIndexArtifact,
    ReconciliationClaimGroup,
)
from .errors import (
    ProjectReconciliationPersistenceIntegrityError,
    ProjectReconciliationPersistenceValidationError,
)

PROJECT_RECONCILIATION_CASE_CYCLE_SCHEMA_VERSION = "2.0.0"
PROJECT_RECONCILIATION_CASE_CYCLE_MODE = "concern_centric_cases"
_CYCLE = re.compile(r"^PRC-[0-9]{6}$")
_CASE = re.compile(r"^CASE-[0-9]{6}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_TIMESTAMP = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z$")

@dataclass(frozen=True, slots=True)
class ConcernCentricProjectReconciliationCycleManifest:
    schema_version: str
    reconciliation_mode: str
    project_id: str
    reconciliation_cycle_id: str
    source_ids: tuple[str, ...]
    project_fit_fingerprints: tuple[str, ...]
    semantic_input_fingerprint: str
    semantic_index_fingerprint: str
    case_assessment_fingerprints: tuple[str, ...]
    reconciliation_summary_fingerprint: str
    created_at: str
    content_fingerprint: str

def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def _fp(value) -> str:
    return sha256(_json(value).encode('utf-8')).hexdigest()

def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ProjectReconciliationPersistenceValidationError(f"{name} must be non-empty text.")
    return value.strip()

def _sha(value, name):
    if not isinstance(value, str) or _SHA.fullmatch(value) is None:
        raise ProjectReconciliationPersistenceValidationError(f"{name} must be a lowercase SHA-256 fingerprint.")
    return value

def _object(text, label):
    try: raw = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ProjectReconciliationPersistenceValidationError(f"{label} must be valid JSON.") from exc
    if not isinstance(raw, dict):
        raise ProjectReconciliationPersistenceValidationError(f"{label} must be a JSON object.")
    return raw

def _exact(raw, fields, label):
    if set(raw) != set(fields):
        raise ProjectReconciliationPersistenceValidationError(f"{label} fields do not match schema.")

def validate_semantic_index_artifact(value):
    if not isinstance(value, ProjectSemanticIndexArtifact):
        raise ProjectReconciliationPersistenceValidationError(
            "semantic index type is invalid."
        )
    if value.schema_version not in {
        PROJECT_SEMANTIC_INDEX_SCHEMA_VERSION,
        PROJECT_SEMANTIC_INDEX_PROVENANCE_SCHEMA_VERSION,
    }:
        raise ProjectReconciliationPersistenceValidationError(
            "Unsupported semantic index schema_version."
        )

    _text(value.project_id, "semantic index project_id")
    _sha(value.input_fingerprint, "semantic index input_fingerprint")
    _sha(value.content_fingerprint, "semantic index content_fingerprint")

    if (
        not value.subject_refs
        or value.subject_refs != tuple(sorted(value.subject_refs))
        or len(value.subject_refs) != len(set(value.subject_refs))
    ):
        raise ProjectReconciliationPersistenceValidationError(
            "semantic index subject_refs must be sorted and unique."
        )
    if (
        not value.source_ids
        or value.source_ids != tuple(sorted(value.source_ids))
        or len(value.source_ids) != len(set(value.source_ids))
    ):
        raise ProjectReconciliationPersistenceValidationError(
            "semantic index source_ids must be sorted and unique."
        )
    if not value.cases:
        raise ProjectReconciliationPersistenceValidationError(
            "semantic index requires at least one Case."
        )
    if tuple(
        case.member_subject_refs for case in value.cases
    ) != tuple(
        sorted(case.member_subject_refs for case in value.cases)
    ):
        raise ProjectReconciliationPersistenceIntegrityError(
            "semantic index Case ordering is not deterministic."
        )

    seen = set()
    cases_body = []
    for index, case in enumerate(value.cases, 1):
        if (
            not isinstance(case, ProjectReconciliationCase)
            or case.case_id != f"CASE-{index:06d}"
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "semantic index Case IDs are not deterministic."
            )
        _text(case.group_label, "Case group_label")
        if (
            not case.member_subject_refs
            or case.member_subject_refs
            != tuple(sorted(case.member_subject_refs))
            or len(case.member_subject_refs)
            != len(set(case.member_subject_refs))
        ):
            raise ProjectReconciliationPersistenceValidationError(
                "Case member_subject_refs must be sorted and unique."
            )
        refs = set(case.member_subject_refs)
        if not refs <= set(value.subject_refs) or seen & refs:
            raise ProjectReconciliationPersistenceIntegrityError(
                "Semantic index Case coverage is invalid."
            )
        seen.update(refs)

        if (
            not case.source_ids
            or case.source_ids != tuple(sorted(case.source_ids))
            or len(case.source_ids) != len(set(case.source_ids))
            or not set(case.source_ids) <= set(value.source_ids)
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Case source_ids are invalid."
            )
        if case.singleton != (len(case.member_subject_refs) == 1):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Case singleton binding is inconsistent."
            )

        expected = _fp(
            {
                "project_id": value.project_id,
                "input_fingerprint": value.input_fingerprint,
                "member_subject_refs": list(case.member_subject_refs),
            }
        )
        if case.case_fingerprint != expected:
            raise ProjectReconciliationPersistenceIntegrityError(
                "Case fingerprint is invalid."
            )
        cases_body.append(asdict(case))

    if seen != set(value.subject_refs):
        raise ProjectReconciliationPersistenceIntegrityError(
            "Semantic index Cases do not cover every Subject."
        )
    if value.human_review_required != any(
        not case.singleton for case in value.cases
    ):
        raise ProjectReconciliationPersistenceIntegrityError(
            "semantic index human_review_required is inconsistent."
        )

    body = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "input_fingerprint": value.input_fingerprint,
        "subject_refs": list(value.subject_refs),
        "source_ids": list(value.source_ids),
        "cases": cases_body,
        "human_review_required": value.human_review_required,
    }

    if value.schema_version == PROJECT_SEMANTIC_INDEX_SCHEMA_VERSION:
        if any(
            item is not None
            for item in (
                value.llm_provider,
                value.llm_model,
                value.llm_response_id,
                value.llm_output_fingerprint,
            )
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Legacy semantic index cannot contain LLM provenance."
            )
    else:
        _text(value.llm_provider, "semantic index llm_provider")
        _text(value.llm_model, "semantic index llm_model")
        if value.llm_response_id is not None:
            _text(
                value.llm_response_id,
                "semantic index llm_response_id",
            )
        _sha(
            value.llm_output_fingerprint,
            "semantic index llm_output_fingerprint",
        )
        body.update(
            {
                "llm_provider": value.llm_provider,
                "llm_model": value.llm_model,
                "llm_response_id": value.llm_response_id,
                "llm_output_fingerprint": (
                    value.llm_output_fingerprint
                ),
            }
        )

    if value.content_fingerprint != _fp(body):
        raise ProjectReconciliationPersistenceIntegrityError(
            "semantic index content fingerprint is invalid."
        )


def semantic_index_to_json(value):
    validate_semantic_index_artifact(value)
    payload = asdict(value)
    if value.schema_version == PROJECT_SEMANTIC_INDEX_SCHEMA_VERSION:
        for field in (
            "llm_provider",
            "llm_model",
            "llm_response_id",
            "llm_output_fingerprint",
        ):
            payload.pop(field, None)
    return _json(payload)


def semantic_index_from_json(text):
    raw = _object(text, "semantic index")
    schema_version = raw.get("schema_version")

    legacy_fields = {
        "schema_version",
        "project_id",
        "input_fingerprint",
        "subject_refs",
        "source_ids",
        "cases",
        "human_review_required",
        "content_fingerprint",
    }
    provenance_fields = legacy_fields | {
        "llm_provider",
        "llm_model",
        "llm_response_id",
        "llm_output_fingerprint",
    }

    if schema_version == PROJECT_SEMANTIC_INDEX_SCHEMA_VERSION:
        _exact(raw, legacy_fields, "semantic index")
    elif (
        schema_version
        == PROJECT_SEMANTIC_INDEX_PROVENANCE_SCHEMA_VERSION
    ):
        _exact(raw, provenance_fields, "semantic index")
    else:
        raise ProjectReconciliationPersistenceValidationError(
            "Unsupported semantic index schema_version."
        )

    cases = []
    for item in raw["cases"]:
        if not isinstance(item, dict):
            raise ProjectReconciliationPersistenceValidationError(
                "semantic index Case must be a JSON object."
            )
        _exact(
            item,
            {
                "case_id",
                "group_label",
                "member_subject_refs",
                "source_ids",
                "singleton",
                "case_fingerprint",
            },
            "semantic index Case",
        )
        cases.append(
            ProjectReconciliationCase(
                item["case_id"],
                item["group_label"],
                tuple(item["member_subject_refs"]),
                tuple(item["source_ids"]),
                item["singleton"],
                item["case_fingerprint"],
            )
        )

    value = ProjectSemanticIndexArtifact(
        schema_version=raw["schema_version"],
        project_id=raw["project_id"],
        input_fingerprint=raw["input_fingerprint"],
        subject_refs=tuple(raw["subject_refs"]),
        source_ids=tuple(raw["source_ids"]),
        cases=tuple(cases),
        human_review_required=raw["human_review_required"],
        content_fingerprint=raw["content_fingerprint"],
        llm_provider=raw.get("llm_provider"),
        llm_model=raw.get("llm_model"),
        llm_response_id=raw.get("llm_response_id"),
        llm_output_fingerprint=raw.get("llm_output_fingerprint"),
    )
    validate_semantic_index_artifact(value)
    return value


def validate_case_assessment(value):
    if not isinstance(value, ProjectReconciliationCaseAssessment) or value.schema_version != PROJECT_RECONCILIATION_CASE_ASSESSMENT_SCHEMA_VERSION:
        raise ProjectReconciliationPersistenceValidationError("Case assessment type/schema is invalid.")
    _text(value.project_id,'Case assessment project_id'); _sha(value.case_fingerprint,'case_fingerprint'); _sha(value.content_fingerprint,'content_fingerprint')
    if _CASE.fullmatch(value.case_id) is None or value.outcome not in PROJECT_RECONCILIATION_CASE_OUTCOMES:
        raise ProjectReconciliationPersistenceValidationError("Case assessment ID/outcome is invalid.")
    _text(value.shared_concern,'shared_concern'); _text(value.summary,'summary')
    if not value.member_subject_refs or value.member_subject_refs != tuple(sorted(value.member_subject_refs)) or len(value.member_subject_refs) != len(set(value.member_subject_refs)):
        raise ProjectReconciliationPersistenceValidationError("Case assessment member_subject_refs must be sorted and unique.")
    if not value.source_ids or value.source_ids != tuple(sorted(value.source_ids)) or len(value.source_ids) != len(set(value.source_ids)):
        raise ProjectReconciliationPersistenceValidationError("Case assessment source_ids must be sorted and unique.")
    for x in value.shared_concepts: _text(x,'shared_concept')
    for x in value.material_differences: _text(x,'material_difference')
    seen=set(); groups=[]
    for i,g in enumerate(value.claim_groups,1):
        if not isinstance(g, ReconciliationClaimGroup) or g.claim_group_id != f"CLAIM-{i:03d}": raise ProjectReconciliationPersistenceIntegrityError("claim group IDs are not deterministic.")
        _text(g.summary,'claim group summary')
        if not g.supported_by_subject_refs or g.supported_by_subject_refs != tuple(sorted(g.supported_by_subject_refs)) or len(g.supported_by_subject_refs) != len(set(g.supported_by_subject_refs)):
            raise ProjectReconciliationPersistenceValidationError("claim group Subject refs must be sorted and unique.")
        refs=set(g.supported_by_subject_refs)
        if not refs <= set(value.member_subject_refs) or seen & refs: raise ProjectReconciliationPersistenceIntegrityError("claim group Subject binding is invalid.")
        seen.update(refs); groups.append(asdict(g))
    if value.outcome == 'unique':
        if len(value.member_subject_refs)!=1 or value.llm_provider is not None or value.llm_model is not None or value.llm_response_id is not None or value.claim_groups or value.human_review_required:
            raise ProjectReconciliationPersistenceIntegrityError("unique assessment must remain deterministic and non-LLM.")
    else:
        _text(value.llm_provider,'llm_provider'); _text(value.llm_model,'llm_model')
        if not value.human_review_required: raise ProjectReconciliationPersistenceIntegrityError("Non-singleton assessment requires Human review.")
    if value.outcome=='equivalent' and not value.shared_concepts: raise ProjectReconciliationPersistenceValidationError("equivalent requires shared concepts.")
    if value.outcome=='complementary' and (not value.shared_concepts or not value.material_differences): raise ProjectReconciliationPersistenceValidationError("complementary requires shared concepts and differences.")
    if value.outcome=='potential_conflict':
        if not value.shared_concepts or not value.material_differences or len(value.claim_groups)<2: raise ProjectReconciliationPersistenceValidationError("potential_conflict evidence is incomplete.")
        if seen != set(value.member_subject_refs): raise ProjectReconciliationPersistenceIntegrityError("potential_conflict claim groups must partition the Case.")
    if value.outcome=='distinct' and not value.material_differences: raise ProjectReconciliationPersistenceValidationError("distinct requires material differences.")
    body={'schema_version':value.schema_version,'project_id':value.project_id,'case_id':value.case_id,'case_fingerprint':value.case_fingerprint,'member_subject_refs':list(value.member_subject_refs),'source_ids':list(value.source_ids),'shared_concern':value.shared_concern,'outcome':value.outcome,'summary':value.summary,'shared_concepts':list(value.shared_concepts),'material_differences':list(value.material_differences),'claim_groups':groups,'llm_provider':value.llm_provider,'llm_model':value.llm_model,'llm_response_id':value.llm_response_id,'human_review_required':value.human_review_required}
    if value.content_fingerprint != _fp(body): raise ProjectReconciliationPersistenceIntegrityError("Case assessment content fingerprint is invalid.")

def case_assessment_to_json(value): validate_case_assessment(value); return _json(asdict(value))
def case_assessment_from_json(text):
    raw=_object(text,'Case assessment'); _exact(raw, {'schema_version','project_id','case_id','case_fingerprint','member_subject_refs','source_ids','shared_concern','outcome','summary','shared_concepts','material_differences','claim_groups','llm_provider','llm_model','llm_response_id','human_review_required','content_fingerprint'}, 'Case assessment')
    groups=[]
    for item in raw['claim_groups']:
        if not isinstance(item,dict): raise ProjectReconciliationPersistenceValidationError("claim group must be a JSON object.")
        _exact(item, {'claim_group_id','summary','supported_by_subject_refs'}, 'claim group')
        groups.append(ReconciliationClaimGroup(item['claim_group_id'], item['summary'], tuple(item['supported_by_subject_refs'])))
    value=ProjectReconciliationCaseAssessment(raw['schema_version'],raw['project_id'],raw['case_id'],raw['case_fingerprint'],tuple(raw['member_subject_refs']),tuple(raw['source_ids']),raw['shared_concern'],raw['outcome'],raw['summary'],tuple(raw['shared_concepts']),tuple(raw['material_differences']),tuple(groups),raw['llm_provider'],raw['llm_model'],raw['llm_response_id'],raw['human_review_required'],raw['content_fingerprint'])
    validate_case_assessment(value); return value

def validate_reconciliation_summary(value):
    if not isinstance(value, ProjectReconciliationSummary) or value.schema_version != PROJECT_RECONCILIATION_SUMMARY_SCHEMA_VERSION: raise ProjectReconciliationPersistenceValidationError("reconciliation summary type/schema is invalid.")
    _text(value.project_id,'summary project_id'); _sha(value.semantic_index_fingerprint,'summary semantic_index_fingerprint'); _sha(value.content_fingerprint,'summary content_fingerprint')
    if not isinstance(value.case_count,int) or value.case_count<1: raise ProjectReconciliationPersistenceValidationError("summary case_count must be positive.")
    counts={}
    for outcome,count in value.outcome_counts:
        if outcome not in PROJECT_RECONCILIATION_CASE_OUTCOMES or outcome in counts or not isinstance(count,int) or count<1: raise ProjectReconciliationPersistenceValidationError("summary outcome counts are invalid.")
        counts[outcome]=count
    if sum(counts.values()) != value.case_count: raise ProjectReconciliationPersistenceIntegrityError("summary outcome counts do not equal case_count.")
    if value.potential_conflicts_present != (counts.get('potential_conflict',0)>0) or value.uncertainties_present != (counts.get('uncertain',0)>0) or value.regrouping_required != (counts.get('distinct',0)>0): raise ProjectReconciliationPersistenceIntegrityError("summary derived signals are inconsistent.")
    if value.human_project_authority_required != any(outcome != 'unique' for outcome in counts): raise ProjectReconciliationPersistenceIntegrityError("summary Human authority signal is inconsistent.")
    body={'schema_version':value.schema_version,'project_id':value.project_id,'semantic_index_fingerprint':value.semantic_index_fingerprint,'case_count':value.case_count,'outcome_counts':[list(i) for i in value.outcome_counts],'potential_conflicts_present':value.potential_conflicts_present,'uncertainties_present':value.uncertainties_present,'regrouping_required':value.regrouping_required,'human_project_authority_required':value.human_project_authority_required}
    if value.content_fingerprint != _fp(body): raise ProjectReconciliationPersistenceIntegrityError("reconciliation summary content fingerprint is invalid.")

def reconciliation_summary_to_json(value): validate_reconciliation_summary(value); return _json(asdict(value))
def reconciliation_summary_from_json(text):
    raw=_object(text,'reconciliation summary'); _exact(raw, {'schema_version','project_id','semantic_index_fingerprint','case_count','outcome_counts','potential_conflicts_present','uncertainties_present','regrouping_required','human_project_authority_required','content_fingerprint'}, 'reconciliation summary')
    value=ProjectReconciliationSummary(raw['schema_version'],raw['project_id'],raw['semantic_index_fingerprint'],raw['case_count'],tuple((i[0],i[1]) for i in raw['outcome_counts']),raw['potential_conflicts_present'],raw['uncertainties_present'],raw['regrouping_required'],raw['human_project_authority_required'],raw['content_fingerprint'])
    validate_reconciliation_summary(value); return value

def create_case_cycle_manifest(*, project_id, reconciliation_cycle_id, source_ids, project_fit_fingerprints, semantic_input_fingerprint, semantic_index_fingerprint, case_assessment_fingerprints, reconciliation_summary_fingerprint, created_at):
    body={'schema_version':PROJECT_RECONCILIATION_CASE_CYCLE_SCHEMA_VERSION,'reconciliation_mode':PROJECT_RECONCILIATION_CASE_CYCLE_MODE,'project_id':project_id,'reconciliation_cycle_id':reconciliation_cycle_id,'source_ids':source_ids,'project_fit_fingerprints':project_fit_fingerprints,'semantic_input_fingerprint':semantic_input_fingerprint,'semantic_index_fingerprint':semantic_index_fingerprint,'case_assessment_fingerprints':case_assessment_fingerprints,'reconciliation_summary_fingerprint':reconciliation_summary_fingerprint,'created_at':created_at}
    value=ConcernCentricProjectReconciliationCycleManifest(**body, content_fingerprint=_fp(body)); validate_case_cycle_manifest(value); return value

def validate_case_cycle_manifest(value):
    if not isinstance(value,ConcernCentricProjectReconciliationCycleManifest) or value.schema_version!=PROJECT_RECONCILIATION_CASE_CYCLE_SCHEMA_VERSION or value.reconciliation_mode!=PROJECT_RECONCILIATION_CASE_CYCLE_MODE: raise ProjectReconciliationPersistenceValidationError("Unsupported concern-centric cycle manifest.")
    _text(value.project_id,'cycle project_id')
    if _CYCLE.fullmatch(value.reconciliation_cycle_id) is None: raise ProjectReconciliationPersistenceValidationError("cycle reconciliation_cycle_id is invalid.")
    if not value.source_ids or value.source_ids!=tuple(sorted(value.source_ids)) or len(value.source_ids)!=len(set(value.source_ids)): raise ProjectReconciliationPersistenceValidationError("cycle source_ids must be sorted and unique.")
    if not value.project_fit_fingerprints or value.project_fit_fingerprints!=tuple(sorted(value.project_fit_fingerprints)) or len(value.project_fit_fingerprints)!=len(set(value.project_fit_fingerprints)) or len(value.project_fit_fingerprints)!=len(value.source_ids): raise ProjectReconciliationPersistenceValidationError("cycle Project Fit fingerprints must be one-per-Source, sorted and unique.")
    if not value.case_assessment_fingerprints: raise ProjectReconciliationPersistenceValidationError("cycle requires Case assessment fingerprints.")
    for x in (*value.project_fit_fingerprints,value.semantic_input_fingerprint,value.semantic_index_fingerprint,*value.case_assessment_fingerprints,value.reconciliation_summary_fingerprint,value.content_fingerprint): _sha(x,'cycle fingerprint')
    if _TIMESTAMP.fullmatch(value.created_at) is None: raise ProjectReconciliationPersistenceValidationError("cycle created_at must be UTC ISO-8601.")
    body={k:v for k,v in asdict(value).items() if k!='content_fingerprint'}
    if value.content_fingerprint!=_fp(body): raise ProjectReconciliationPersistenceIntegrityError("concern-centric cycle manifest fingerprint is invalid.")

def case_cycle_manifest_to_json(value): validate_case_cycle_manifest(value); return _json(asdict(value))
def case_cycle_manifest_from_json(text):
    raw=_object(text,'concern-centric cycle manifest'); _exact(raw, {'schema_version','reconciliation_mode','project_id','reconciliation_cycle_id','source_ids','project_fit_fingerprints','semantic_input_fingerprint','semantic_index_fingerprint','case_assessment_fingerprints','reconciliation_summary_fingerprint','created_at','content_fingerprint'}, 'concern-centric cycle manifest')
    value=ConcernCentricProjectReconciliationCycleManifest(raw['schema_version'],raw['reconciliation_mode'],raw['project_id'],raw['reconciliation_cycle_id'],tuple(raw['source_ids']),tuple(raw['project_fit_fingerprints']),raw['semantic_input_fingerprint'],raw['semantic_index_fingerprint'],tuple(raw['case_assessment_fingerprints']),raw['reconciliation_summary_fingerprint'],raw['created_at'],raw['content_fingerprint'])
    validate_case_cycle_manifest(value); return value
