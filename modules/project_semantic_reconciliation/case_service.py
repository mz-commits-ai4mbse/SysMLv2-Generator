"""ADR-033 S3B one-Case semantic assessment service."""

from __future__ import annotations

import dataclasses
import json

from modules.llm.factory import create_llm_client
from modules.llm.progress import notify_llm_progress
from modules.llm.types import LLMRequest

from .case_contract import (
    create_project_reconciliation_case_assessment,
    derive_project_reconciliation_summary,
)
from .case_prompt import (
    PROJECT_RECONCILIATION_CASE_PROMPT_SCHEMA_VERSION,
    build_project_reconciliation_case_input,
    build_project_reconciliation_case_instructions,
)
from .case_types import (
    ProjectReconciliationCaseAssessment,
    ProjectReconciliationSummary,
    ProjectSemanticIndexArtifact,
    ReconciliationClaimGroupProposal,
)
from .errors import (
    ProjectSemanticReconciliationIntegrityError,
    ProjectSemanticReconciliationValidationError,
)
from .prompt import PROJECT_SEMANTIC_RECONCILIATION_MAX_INPUT_CHARACTERS


_PROJECT_RECONCILIATION_CASE_TRANSPORT_ALIAS_LIMIT = 9999


@dataclasses.dataclass(frozen=True, slots=True)
class ProjectReconciliationCaseProgressEvent:
    event_type: str
    case_index: int
    total_cases: int
    case_id: str
    case_label: str
    singleton: bool


def _notify_case_progress(
    observer,
    *,
    event_type: str,
    case_index: int,
    total_cases: int,
    case_id: str,
    case_label: str,
    singleton: bool,
) -> None:
    if observer is None:
        return
    observer(
        ProjectReconciliationCaseProgressEvent(
            event_type=event_type,
            case_index=case_index,
            total_cases=total_cases,
            case_id=case_id,
            case_label=case_label,
            singleton=singleton,
        )
    )


def _prepare_case_transport(
    subjects: tuple[object, ...],
) -> tuple[
    tuple[object, ...],
    dict[str, str],
]:
    """Assign deterministic transient refs local to one Case call."""

    if len(subjects) > _PROJECT_RECONCILIATION_CASE_TRANSPORT_ALIAS_LIMIT:
        raise ProjectSemanticReconciliationValidationError(
            "Reconciliation Case exceeds the transient SUBJ-NNNN "
            "transport alias space."
        )

    transport_subjects = []
    transport_to_real = {}
    seen_real = set()

    for index, subject in enumerate(subjects, start=1):
        real_ref = subject.subject_ref
        if real_ref in seen_real:
            raise ProjectSemanticReconciliationIntegrityError(
                "Reconciliation Case contains duplicate Subjects."
            )
        seen_real.add(real_ref)

        alias = f"SUBJ-{index:04d}"
        transport_to_real[alias] = real_ref
        transport_subjects.append(
            dataclasses.replace(subject, subject_ref=alias)
        )

    return tuple(transport_subjects), transport_to_real


def parse_project_reconciliation_case_response(
    text: str,
    *,
    transport_subject_refs: tuple[str, ...],
) -> dict:
    """Parse one exact Case-level response without pairwise relations."""

    try:
        payload = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ProjectSemanticReconciliationValidationError(
            "Project reconciliation Case output must be valid JSON."
        ) from exc

    expected = {
        "shared_concern",
        "outcome",
        "summary",
        "shared_concepts",
        "material_differences",
        "claim_groups",
    }
    if not isinstance(payload, dict) or frozenset(payload) != expected:
        raise ProjectSemanticReconciliationValidationError(
            "Project reconciliation Case output fields do not match schema."
        )

    for field in ("shared_concern", "outcome", "summary"):
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise ProjectSemanticReconciliationValidationError(
                f"{field} must be non-empty text."
            )

    for field in ("shared_concepts", "material_differences"):
        values = payload[field]
        if not isinstance(values, list):
            raise ProjectSemanticReconciliationValidationError(
                f"{field} must be a JSON array."
            )
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ProjectSemanticReconciliationValidationError(
                f"{field} must contain non-empty text."
            )

    groups = payload["claim_groups"]
    if not isinstance(groups, list):
        raise ProjectSemanticReconciliationValidationError(
            "claim_groups must be a JSON array."
        )

    known = set(transport_subject_refs)
    seen = set()
    parsed_groups = []

    for raw in groups:
        if (
            not isinstance(raw, dict)
            or frozenset(raw)
            != {"summary", "supported_by_subject_refs"}
        ):
            raise ProjectSemanticReconciliationValidationError(
                "One claim group has invalid fields."
            )

        summary = raw["summary"]
        refs = raw["supported_by_subject_refs"]

        if not isinstance(summary, str) or not summary.strip():
            raise ProjectSemanticReconciliationValidationError(
                "claim group summary must be non-empty text."
            )
        if not isinstance(refs, list) or not refs:
            raise ProjectSemanticReconciliationValidationError(
                "supported_by_subject_refs must be a non-empty JSON array."
            )
        if any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            raise ProjectSemanticReconciliationValidationError(
                "supported_by_subject_refs must contain non-empty text."
            )

        normalized = tuple(sorted(ref.strip() for ref in refs))
        if len(set(normalized)) != len(normalized):
            raise ProjectSemanticReconciliationIntegrityError(
                "A claim group contains duplicate subject_ref values."
            )
        if not set(normalized) <= known:
            raise ProjectSemanticReconciliationIntegrityError(
                "A claim group references an unknown subject_ref."
            )
        if seen & set(normalized):
            raise ProjectSemanticReconciliationIntegrityError(
                "A Case Subject may belong to only one claim group."
            )

        seen.update(normalized)
        parsed_groups.append(
            {
                "summary": summary.strip(),
                "supported_by_subject_refs": normalized,
            }
        )

    if payload["outcome"].strip() == "potential_conflict":
        if seen != known:
            raise ProjectSemanticReconciliationIntegrityError(
                "potential_conflict claim groups must partition every "
                "Case Subject."
            )

    return {
        "shared_concern": payload["shared_concern"].strip(),
        "outcome": payload["outcome"].strip(),
        "summary": payload["summary"].strip(),
        "shared_concepts": tuple(
            value.strip()
            for value in payload["shared_concepts"]
        ),
        "material_differences": tuple(
            value.strip()
            for value in payload["material_differences"]
        ),
        "claim_groups": tuple(parsed_groups),
    }


class ProjectReconciliationCaseAssessmentService:
    """Assess non-singleton Cases one at a time and derive one summary."""

    def __init__(self, client_factory=create_llm_client):
        self._client_factory = client_factory

    def assess_all(
        self,
        *,
        semantic_index: ProjectSemanticIndexArtifact,
        subjects: tuple[object, ...],
        provider: str,
        model: str,
        api_key: str | None = None,
        llm_progress_observer=None,
        case_progress_observer=None,
    ) -> tuple[
        tuple[ProjectReconciliationCaseAssessment, ...],
        ProjectReconciliationSummary,
    ]:
        subject_by_ref = {}
        for subject in subjects:
            if subject.subject_ref in subject_by_ref:
                raise ProjectSemanticReconciliationIntegrityError(
                    "Project semantic Subjects are not unique."
                )
            subject_by_ref[subject.subject_ref] = subject

        if set(subject_by_ref) != set(semantic_index.subject_refs):
            raise ProjectSemanticReconciliationIntegrityError(
                "S3B Subjects do not match the exact S3A semantic index."
            )

        non_singletons = tuple(
            case
            for case in semantic_index.cases
            if not case.singleton
        )

        if llm_progress_observer is not None:
            notify_llm_progress(
                llm_progress_observer,
                event_type="planned",
                stage="project_reconciliation_case_assessment",
                request_count=len(non_singletons),
            )

        assessments = []
        total_cases = len(semantic_index.cases)

        for case_index, case in enumerate(
            semantic_index.cases,
            start=1,
        ):
            _notify_case_progress(
                case_progress_observer,
                event_type="started",
                case_index=case_index,
                total_cases=total_cases,
                case_id=case.case_id,
                case_label=case.group_label,
                singleton=case.singleton,
            )

            if case.singleton:
                assessment = (
                    create_project_reconciliation_case_assessment(
                        semantic_index=semantic_index,
                        case_id=case.case_id,
                        shared_concern=case.group_label,
                        outcome="unique",
                        summary=(
                            "No semantic counterpart was indexed "
                            "for this Subject."
                        ),
                    )
                )
            else:
                real_subjects = tuple(
                    subject_by_ref[ref]
                    for ref in case.member_subject_refs
                )
                (
                    transport_subjects,
                    transport_to_real,
                ) = _prepare_case_transport(real_subjects)

                input_text = build_project_reconciliation_case_input(
                    project_id=semantic_index.project_id,
                    case_id=case.case_id,
                    case_label=case.group_label,
                    subjects=transport_subjects,
                    max_characters=(
                        PROJECT_SEMANTIC_RECONCILIATION_MAX_INPUT_CHARACTERS
                    ),
                )

                result = self._client_factory(provider).generate(
                    LLMRequest(
                        provider=provider,
                        model=model,
                        api_key=api_key,
                        instructions=(
                            build_project_reconciliation_case_instructions()
                        ),
                        input_text=input_text,
                        metadata={
                            "task_name": (
                                "project_reconciliation_case_assessment"
                            ),
                            "prompt_schema_version": (
                                PROJECT_RECONCILIATION_CASE_PROMPT_SCHEMA_VERSION
                            ),
                            "project_id": semantic_index.project_id,
                            "case_id": case.case_id,
                            "case_index": case_index,
                            "case_count": total_cases,
                            "subject_count": len(real_subjects),
                            "source_count": len(case.source_ids),
                        },
                    )
                )

                parsed = parse_project_reconciliation_case_response(
                    result.text,
                    transport_subject_refs=tuple(
                        subject.subject_ref
                        for subject in transport_subjects
                    ),
                )

                claim_group_proposals = tuple(
                    ReconciliationClaimGroupProposal(
                        summary=group["summary"],
                        supported_by_subject_refs=tuple(
                            sorted(
                                transport_to_real[ref]
                                for ref in group[
                                    "supported_by_subject_refs"
                                ]
                            )
                        ),
                    )
                    for group in parsed["claim_groups"]
                )

                assessment = (
                    create_project_reconciliation_case_assessment(
                        semantic_index=semantic_index,
                        case_id=case.case_id,
                        shared_concern=parsed["shared_concern"],
                        outcome=parsed["outcome"],
                        summary=parsed["summary"],
                        shared_concepts=parsed["shared_concepts"],
                        material_differences=(
                            parsed["material_differences"]
                        ),
                        claim_group_proposals=claim_group_proposals,
                        llm_provider=result.provider,
                        llm_model=result.model,
                        llm_response_id=result.response_id,
                    )
                )

            assessments.append(assessment)

            _notify_case_progress(
                case_progress_observer,
                event_type="completed",
                case_index=case_index,
                total_cases=total_cases,
                case_id=case.case_id,
                case_label=case.group_label,
                singleton=case.singleton,
            )

        if llm_progress_observer is not None:
            notify_llm_progress(
                llm_progress_observer,
                event_type="completed",
                stage="project_reconciliation_case_assessment",
                request_count=len(non_singletons),
            )

        assessments = tuple(assessments)
        summary = derive_project_reconciliation_summary(
            semantic_index=semantic_index,
            assessments=assessments,
        )
        return assessments, summary
