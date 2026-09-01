"""ADR-033 deterministic contracts for concern-centric reconciliation."""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
import re

from .case_types import (
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
    ReconciliationClaimGroupProposal,
    SemanticIndexGroupProposal,
)
from .errors import (
    ProjectSemanticReconciliationIntegrityError,
    ProjectSemanticReconciliationValidationError,
)


_CASE_ID_RE = re.compile(r"^CASE-[0-9]{6}$")
_CLAIM_GROUP_ID_RE = re.compile(r"^CLAIM-[0-9]{3}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _required_text(value, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectSemanticReconciliationValidationError(
            f"{field_name} must be non-empty text."
        )
    return value.strip()


def _validate_sha256(value: str, field_name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ProjectSemanticReconciliationValidationError(
            f"{field_name} must be a lowercase SHA-256 fingerprint."
        )
    return value


def _sha(value) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def _subject_map(subjects) -> dict[str, object]:
    result = {}
    for subject in subjects:
        subject_ref = _required_text(
            getattr(subject, "subject_ref", None),
            "subject_ref",
        )
        source_id = _required_text(
            getattr(subject, "source_id", None),
            "source_id",
        )
        if subject_ref in result:
            raise ProjectSemanticReconciliationIntegrityError(
                "Project semantic Subjects are not unique."
            )
        result[subject_ref] = subject

    if not result:
        raise ProjectSemanticReconciliationValidationError(
            "Project semantic indexing requires at least one Subject."
        )
    return result


def create_project_semantic_index_artifact(
    *,
    project_id: str,
    input_fingerprint: str,
    subjects: tuple[object, ...],
    group_proposals: tuple[SemanticIndexGroupProposal, ...],
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_response_id: str | None = None,
    llm_output_fingerprint: str | None = None,
) -> ProjectSemanticIndexArtifact:
    """Validate complete S3A coverage and assign deterministic Case identity."""

    project_id = _required_text(project_id, "project_id")
    input_fingerprint = _validate_sha256(
        input_fingerprint,
        "input_fingerprint",
    )
    subject_by_ref = _subject_map(subjects)
    known_refs = set(subject_by_ref)

    provenance_values = (
        llm_provider,
        llm_model,
        llm_response_id,
        llm_output_fingerprint,
    )
    has_provenance = any(value is not None for value in provenance_values)
    if has_provenance:
        llm_provider = _required_text(llm_provider, "llm_provider")
        llm_model = _required_text(llm_model, "llm_model")
        if llm_response_id is not None:
            llm_response_id = _required_text(
                llm_response_id,
                "llm_response_id",
            )
        llm_output_fingerprint = _validate_sha256(
            llm_output_fingerprint,
            "llm_output_fingerprint",
        )

    if not group_proposals:
        raise ProjectSemanticReconciliationValidationError(
            "Semantic indexing must return at least one group."
        )

    normalized = []
    globally_seen = set()

    for proposal in group_proposals:
        label = _required_text(proposal.group_label, "group_label")
        refs = tuple(
            sorted(
                _required_text(value, "member_subject_ref")
                for value in proposal.member_subject_refs
            )
        )
        if not refs:
            raise ProjectSemanticReconciliationValidationError(
                "A semantic index group must contain at least one Subject."
            )
        if len(set(refs)) != len(refs):
            raise ProjectSemanticReconciliationIntegrityError(
                "A semantic index group contains duplicate Subjects."
            )
        if not set(refs) <= known_refs:
            raise ProjectSemanticReconciliationIntegrityError(
                "A semantic index group references an unknown Subject."
            )
        overlap = globally_seen & set(refs)
        if overlap:
            raise ProjectSemanticReconciliationIntegrityError(
                "A Subject may belong to exactly one Reconciliation Case."
            )
        globally_seen.update(refs)

        source_ids = tuple(
            sorted(
                {
                    _required_text(
                        getattr(subject_by_ref[ref], "source_id", None),
                        "source_id",
                    )
                    for ref in refs
                }
            )
        )
        normalized.append((refs, label, source_ids))

    if globally_seen != known_refs:
        missing = tuple(sorted(known_refs - globally_seen))
        raise ProjectSemanticReconciliationIntegrityError(
            "Semantic indexing must explicitly cover every Subject; "
            f"missing: {missing}."
        )

    normalized.sort(key=lambda item: item[0])

    cases = []
    for index, (refs, label, source_ids) in enumerate(
        normalized,
        start=1,
    ):
        case_id = f"CASE-{index:06d}"
        fingerprint = _sha(
            {
                "project_id": project_id,
                "input_fingerprint": input_fingerprint,
                "member_subject_refs": list(refs),
            }
        )
        cases.append(
            ProjectReconciliationCase(
                case_id=case_id,
                group_label=label,
                member_subject_refs=refs,
                source_ids=source_ids,
                singleton=len(refs) == 1,
                case_fingerprint=fingerprint,
            )
        )

    subject_refs = tuple(sorted(known_refs))
    source_ids = tuple(
        sorted(
            {
                _required_text(
                    getattr(subject, "source_id", None),
                    "source_id",
                )
                for subject in subjects
            }
        )
    )

    schema_version = (
        PROJECT_SEMANTIC_INDEX_PROVENANCE_SCHEMA_VERSION
        if has_provenance
        else PROJECT_SEMANTIC_INDEX_SCHEMA_VERSION
    )
    body = {
        "schema_version": schema_version,
        "project_id": project_id,
        "input_fingerprint": input_fingerprint,
        "subject_refs": list(subject_refs),
        "source_ids": list(source_ids),
        "cases": [asdict(case) for case in cases],
        "human_review_required": any(not case.singleton for case in cases),
    }
    if has_provenance:
        body.update(
            {
                "llm_provider": llm_provider,
                "llm_model": llm_model,
                "llm_response_id": llm_response_id,
                "llm_output_fingerprint": llm_output_fingerprint,
            }
        )

    return ProjectSemanticIndexArtifact(
        schema_version=schema_version,
        project_id=project_id,
        input_fingerprint=input_fingerprint,
        subject_refs=subject_refs,
        source_ids=source_ids,
        cases=tuple(cases),
        human_review_required=body["human_review_required"],
        content_fingerprint=_sha(body),
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_response_id=llm_response_id,
        llm_output_fingerprint=llm_output_fingerprint,
    )


def _case_by_id(
    semantic_index: ProjectSemanticIndexArtifact,
    case_id: str,
) -> ProjectReconciliationCase:
    _required_text(case_id, "case_id")
    if _CASE_ID_RE.fullmatch(case_id) is None:
        raise ProjectSemanticReconciliationValidationError(
            "case_id must use CASE-NNNNNN format."
        )
    matches = [
        case
        for case in semantic_index.cases
        if case.case_id == case_id
    ]
    if len(matches) != 1:
        raise ProjectSemanticReconciliationIntegrityError(
            "Reconciliation Case cannot be resolved exactly."
        )
    return matches[0]


def _create_claim_groups(
    case: ProjectReconciliationCase,
    proposals: tuple[ReconciliationClaimGroupProposal, ...],
) -> tuple[ReconciliationClaimGroup, ...]:
    if not proposals:
        return ()

    known_refs = set(case.member_subject_refs)
    normalized = []
    seen = set()

    for proposal in proposals:
        summary = _required_text(proposal.summary, "claim_group.summary")
        refs = tuple(
            sorted(
                _required_text(value, "claim_group.subject_ref")
                for value in proposal.supported_by_subject_refs
            )
        )
        if not refs:
            raise ProjectSemanticReconciliationValidationError(
                "A claim group must reference at least one Case member."
            )
        if len(set(refs)) != len(refs):
            raise ProjectSemanticReconciliationIntegrityError(
                "A claim group contains duplicate Case members."
            )
        if not set(refs) <= known_refs:
            raise ProjectSemanticReconciliationIntegrityError(
                "A claim group references a Subject outside its Case."
            )
        if seen & set(refs):
            raise ProjectSemanticReconciliationIntegrityError(
                "A Case member may belong to only one claim group."
            )
        seen.update(refs)
        normalized.append((refs, summary))

    if seen != known_refs:
        raise ProjectSemanticReconciliationIntegrityError(
            "When claim groups are supplied they must partition all "
            "Reconciliation Case members."
        )

    normalized.sort(key=lambda item: item[0])

    return tuple(
        ReconciliationClaimGroup(
            claim_group_id=f"CLAIM-{index:03d}",
            summary=summary,
            supported_by_subject_refs=refs,
        )
        for index, (refs, summary) in enumerate(normalized, start=1)
    )


def create_project_reconciliation_case_assessment(
    *,
    semantic_index: ProjectSemanticIndexArtifact,
    case_id: str,
    shared_concern: str,
    outcome: str,
    summary: str,
    shared_concepts: tuple[str, ...] = (),
    material_differences: tuple[str, ...] = (),
    claim_group_proposals: tuple[
        ReconciliationClaimGroupProposal, ...
    ] = (),
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_response_id: str | None = None,
) -> ProjectReconciliationCaseAssessment:
    """Create one complete non-authoritative S3B Case assessment."""

    case = _case_by_id(semantic_index, case_id)
    shared_concern = _required_text(shared_concern, "shared_concern")
    outcome = _required_text(outcome, "outcome")
    summary = _required_text(summary, "summary")

    if outcome not in PROJECT_RECONCILIATION_CASE_OUTCOMES:
        raise ProjectSemanticReconciliationValidationError(
            "Case assessment outcome is unsupported."
        )

    shared_concepts = tuple(
        _required_text(value, "shared_concept")
        for value in shared_concepts
    )
    material_differences = tuple(
        _required_text(value, "material_difference")
        for value in material_differences
    )

    if case.singleton:
        if outcome != "unique":
            raise ProjectSemanticReconciliationValidationError(
                "A Singleton Case must use deterministic outcome unique."
            )
        if any(
            value is not None
            for value in (llm_provider, llm_model, llm_response_id)
        ):
            raise ProjectSemanticReconciliationIntegrityError(
                "A Singleton Case must not claim LLM assessment provenance."
            )
        if claim_group_proposals:
            raise ProjectSemanticReconciliationValidationError(
                "A Singleton Case must not create claim groups."
            )
        claim_groups = ()
        human_review_required = False
    else:
        if outcome == "unique":
            raise ProjectSemanticReconciliationValidationError(
                "unique is reserved for Singleton Cases."
            )
        llm_provider = _required_text(llm_provider, "llm_provider")
        llm_model = _required_text(llm_model, "llm_model")
        if llm_response_id is not None:
            llm_response_id = _required_text(
                llm_response_id,
                "llm_response_id",
            )
        claim_groups = _create_claim_groups(
            case,
            claim_group_proposals,
        )
        human_review_required = True

    if outcome == "equivalent" and not shared_concepts:
        raise ProjectSemanticReconciliationValidationError(
            "equivalent requires positive shared semantic evidence."
        )
    if outcome == "complementary":
        if not shared_concepts or not material_differences:
            raise ProjectSemanticReconciliationValidationError(
                "complementary requires shared concepts and material "
                "differences."
            )
    if outcome == "potential_conflict":
        if not shared_concepts or not material_differences:
            raise ProjectSemanticReconciliationValidationError(
                "potential_conflict requires shared concepts and material "
                "differences."
            )
        if len(claim_groups) < 2:
            raise ProjectSemanticReconciliationValidationError(
                "potential_conflict requires at least two explicit "
                "claim groups."
            )
    if outcome == "distinct" and not material_differences:
        raise ProjectSemanticReconciliationValidationError(
            "distinct requires explicit material differences."
        )

    body = {
        "schema_version": (
            PROJECT_RECONCILIATION_CASE_ASSESSMENT_SCHEMA_VERSION
        ),
        "project_id": semantic_index.project_id,
        "case_id": case.case_id,
        "case_fingerprint": case.case_fingerprint,
        "member_subject_refs": list(case.member_subject_refs),
        "source_ids": list(case.source_ids),
        "shared_concern": shared_concern,
        "outcome": outcome,
        "summary": summary,
        "shared_concepts": list(shared_concepts),
        "material_differences": list(material_differences),
        "claim_groups": [asdict(group) for group in claim_groups],
        "llm_provider": llm_provider,
        "llm_model": llm_model,
        "llm_response_id": llm_response_id,
        "human_review_required": human_review_required,
    }

    return ProjectReconciliationCaseAssessment(
        schema_version=body["schema_version"],
        project_id=body["project_id"],
        case_id=case.case_id,
        case_fingerprint=case.case_fingerprint,
        member_subject_refs=case.member_subject_refs,
        source_ids=case.source_ids,
        shared_concern=shared_concern,
        outcome=outcome,
        summary=summary,
        shared_concepts=shared_concepts,
        material_differences=material_differences,
        claim_groups=claim_groups,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_response_id=llm_response_id,
        human_review_required=human_review_required,
        content_fingerprint=_sha(body),
    )


def derive_project_reconciliation_summary(
    *,
    semantic_index: ProjectSemanticIndexArtifact,
    assessments: tuple[ProjectReconciliationCaseAssessment, ...],
) -> ProjectReconciliationSummary:
    """Derive global compatibility/conflict signals without an LLM call."""

    expected = {case.case_id: case for case in semantic_index.cases}
    actual = {}

    for assessment in assessments:
        if assessment.case_id in actual:
            raise ProjectSemanticReconciliationIntegrityError(
                "A Reconciliation Case may have only one assessment."
            )
        case = expected.get(assessment.case_id)
        if case is None:
            raise ProjectSemanticReconciliationIntegrityError(
                "Case assessment references an unknown Reconciliation Case."
            )
        if (
            assessment.project_id != semantic_index.project_id
            or assessment.case_fingerprint != case.case_fingerprint
            or assessment.member_subject_refs != case.member_subject_refs
        ):
            raise ProjectSemanticReconciliationIntegrityError(
                "Case assessment does not bind the exact indexed Case."
            )
        actual[assessment.case_id] = assessment

    if set(actual) != set(expected):
        missing = tuple(sorted(set(expected) - set(actual)))
        raise ProjectSemanticReconciliationIntegrityError(
            "Project reconciliation summary requires one exact assessment "
            f"for every Case; missing: {missing}."
        )

    counts = {
        outcome: 0
        for outcome in sorted(PROJECT_RECONCILIATION_CASE_OUTCOMES)
    }
    for assessment in actual.values():
        counts[assessment.outcome] += 1

    outcome_counts = tuple(
        (outcome, count)
        for outcome, count in sorted(counts.items())
        if count
    )

    body = {
        "schema_version": PROJECT_RECONCILIATION_SUMMARY_SCHEMA_VERSION,
        "project_id": semantic_index.project_id,
        "semantic_index_fingerprint": semantic_index.content_fingerprint,
        "case_count": len(expected),
        "outcome_counts": [list(item) for item in outcome_counts],
        "potential_conflicts_present": counts["potential_conflict"] > 0,
        "uncertainties_present": counts["uncertain"] > 0,
        "regrouping_required": counts["distinct"] > 0,
        "human_project_authority_required": any(
            assessment.human_review_required
            for assessment in actual.values()
        ),
    }

    return ProjectReconciliationSummary(
        schema_version=body["schema_version"],
        project_id=body["project_id"],
        semantic_index_fingerprint=semantic_index.content_fingerprint,
        case_count=body["case_count"],
        outcome_counts=outcome_counts,
        potential_conflicts_present=body[
            "potential_conflicts_present"
        ],
        uncertainties_present=body["uncertainties_present"],
        regrouping_required=body["regrouping_required"],
        human_project_authority_required=body[
            "human_project_authority_required"
        ],
        content_fingerprint=_sha(body),
    )
