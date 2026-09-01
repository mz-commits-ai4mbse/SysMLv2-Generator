"""ADR-033 S3A global concern-centric semantic indexing service."""

from __future__ import annotations

import dataclasses
from hashlib import sha256
import json

from modules.llm.factory import create_llm_client
from modules.llm.progress import notify_llm_progress
from modules.llm.types import LLMRequest

from .case_contract import create_project_semantic_index_artifact
from .case_types import (
    ProjectSemanticIndexArtifact,
    SemanticIndexGroupProposal,
)
from .contract import prepare_project_semantic_subjects
from .errors import (
    ProjectSemanticReconciliationIntegrityError,
    ProjectSemanticReconciliationValidationError,
)
from .prompt import PROJECT_SEMANTIC_RECONCILIATION_MAX_INPUT_CHARACTERS
from .semantic_index_prompt import (
    PROJECT_SEMANTIC_INDEX_PROMPT_SCHEMA_VERSION,
    build_project_semantic_index_input,
    build_project_semantic_index_instructions,
)
from .types import ProjectSemanticSourceInput


_PROJECT_SEMANTIC_INDEX_TRANSPORT_ALIAS_LIMIT = 9999


def _prepare_semantic_index_transport(
    subjects: tuple[object, ...],
) -> tuple[
    tuple[object, ...],
    dict[str, str],
]:
    """Assign deterministic transient SUBJ-NNNN refs for one S3A call."""

    if len(subjects) > _PROJECT_SEMANTIC_INDEX_TRANSPORT_ALIAS_LIMIT:
        raise ProjectSemanticReconciliationValidationError(
            "Project semantic indexing exceeds the transient SUBJ-NNNN "
            "transport alias space."
        )

    transport_subjects = []
    transport_to_real: dict[str, str] = {}
    seen_real = set()

    for index, subject in enumerate(subjects, start=1):
        real_ref = subject.subject_ref
        if real_ref in seen_real:
            raise ProjectSemanticReconciliationIntegrityError(
                "Input Project semantic Subjects are not unique."
            )
        seen_real.add(real_ref)

        alias = f"SUBJ-{index:04d}"
        transport_to_real[alias] = real_ref
        transport_subjects.append(
            dataclasses.replace(subject, subject_ref=alias)
        )

    return tuple(transport_subjects), transport_to_real


def parse_project_semantic_index_response(
    text: str,
    *,
    transport_subject_refs: tuple[str, ...],
) -> tuple[SemanticIndexGroupProposal, ...]:
    """Parse exact S3A grouping with complete one-time Subject coverage."""

    try:
        payload = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ProjectSemanticReconciliationValidationError(
            "Project semantic index output must be valid JSON."
        ) from exc

    if not isinstance(payload, dict) or frozenset(payload) != {"groups"}:
        raise ProjectSemanticReconciliationValidationError(
            "Project semantic index output fields do not match schema."
        )

    groups = payload["groups"]
    if not isinstance(groups, list) or not groups:
        raise ProjectSemanticReconciliationValidationError(
            "Project semantic index groups must be a non-empty JSON array."
        )

    known = set(transport_subject_refs)
    if len(known) != len(transport_subject_refs):
        raise ProjectSemanticReconciliationIntegrityError(
            "Transient semantic-index Subject refs are not unique."
        )

    proposals = []

    for raw_group in groups:
        if (
            not isinstance(raw_group, dict)
            or frozenset(raw_group)
            != {"group_label", "member_subject_refs"}
        ):
            raise ProjectSemanticReconciliationValidationError(
                "One semantic index group has invalid fields."
            )

        label = raw_group["group_label"]
        if not isinstance(label, str) or not label.strip():
            raise ProjectSemanticReconciliationValidationError(
                "group_label must be non-empty text."
            )

        refs = raw_group["member_subject_refs"]
        if not isinstance(refs, list) or not refs:
            raise ProjectSemanticReconciliationValidationError(
                "member_subject_refs must be a non-empty JSON array."
            )
        if any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            raise ProjectSemanticReconciliationValidationError(
                "member_subject_refs must contain non-empty text."
            )

        normalized = tuple(sorted(ref.strip() for ref in refs))
        if len(set(normalized)) != len(normalized):
            raise ProjectSemanticReconciliationIntegrityError(
                "A semantic index group contains duplicate Subject refs."
            )
        if not set(normalized) <= known:
            raise ProjectSemanticReconciliationIntegrityError(
                "Semantic index output references an unknown subject_ref."
            )
        proposals.append(
            SemanticIndexGroupProposal(
                group_label=label.strip(),
                member_subject_refs=normalized,
            )
        )

    seen = {
        ref
        for proposal in proposals
        for ref in proposal.member_subject_refs
    }
    if seen != known:
        missing = tuple(sorted(known - seen))
        raise ProjectSemanticReconciliationIntegrityError(
            "Semantic indexing must explicitly cover every Subject; "
            f"missing: {missing}."
        )

    return _normalize_overlapping_semantic_index_groups(
        tuple(proposals)
    )


def _validate_llm_completion(result) -> None:
    """Reject provider-reported incomplete or abnormal S3A responses."""

    status = getattr(result, "raw_status", None)
    if status is None:
        return
    if not isinstance(status, str) or not status.strip():
        raise ProjectSemanticReconciliationIntegrityError(
            "Project semantic indexing LLM returned an invalid response status."
        )

    normalized = status.strip().lower()
    if normalized == "completed":
        return

    if normalized == "incomplete":
        reason = getattr(result, "incomplete_reason", None)
        if isinstance(reason, str) and reason.strip():
            detail = f" Reason: {reason.strip()}."
        else:
            detail = " No incomplete reason was reported."
        raise ProjectSemanticReconciliationIntegrityError(
            "Project semantic indexing LLM response was incomplete."
            + detail
        )

    raise ProjectSemanticReconciliationIntegrityError(
        "Project semantic indexing LLM returned a non-completed "
        f"response status: {status.strip()}."
    )


def _normalize_overlapping_semantic_index_groups(
    proposals: tuple[SemanticIndexGroupProposal, ...],
) -> tuple[SemanticIndexGroupProposal, ...]:
    """Collapse overlapping raw LLM groups into disjoint concern components."""

    if not proposals:
        raise ProjectSemanticReconciliationValidationError(
            "Semantic indexing must return at least one group."
        )

    parent = list(range(len(proposals)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        if left_root < right_root:
            parent[right_root] = left_root
        else:
            parent[left_root] = right_root

    first_group_by_ref: dict[str, int] = {}
    for group_index, proposal in enumerate(proposals):
        for ref in proposal.member_subject_refs:
            prior = first_group_by_ref.get(ref)
            if prior is None:
                first_group_by_ref[ref] = group_index
            else:
                union(prior, group_index)

    members_by_root: dict[int, set[str]] = {}
    labels_by_root: dict[int, set[str]] = {}

    for group_index, proposal in enumerate(proposals):
        root = find(group_index)
        members_by_root.setdefault(root, set()).update(
            proposal.member_subject_refs
        )
        labels_by_root.setdefault(root, set()).add(
            proposal.group_label
        )

    normalized = []
    for root in sorted(members_by_root):
        members = tuple(sorted(members_by_root[root]))
        labels = tuple(sorted(labels_by_root[root]))
        normalized.append(
            SemanticIndexGroupProposal(
                group_label=" / ".join(labels),
                member_subject_refs=members,
            )
        )

    normalized.sort(key=lambda item: item.member_subject_refs)
    return tuple(normalized)


class ProjectSemanticIndexService:
    """Run one bounded global S3A semantic-indexing judgment."""

    def __init__(self, client_factory=create_llm_client):
        self._client_factory = client_factory

    def index(
        self,
        source_inputs: tuple[ProjectSemanticSourceInput, ...],
        *,
        provider: str,
        model: str,
        api_key: str | None = None,
        llm_progress_observer=None,
    ) -> ProjectSemanticIndexArtifact:
        project_id, subjects, input_fingerprint = (
            prepare_project_semantic_subjects(source_inputs)
        )
        transport_subjects, transport_to_real = (
            _prepare_semantic_index_transport(subjects)
        )

        input_text = build_project_semantic_index_input(
            project_id=project_id,
            subjects=transport_subjects,
            max_characters=(
                PROJECT_SEMANTIC_RECONCILIATION_MAX_INPUT_CHARACTERS
            ),
        )

        if llm_progress_observer is not None:
            notify_llm_progress(
                llm_progress_observer,
                event_type="planned",
                stage="project_semantic_index",
                request_count=1,
            )

        result = self._client_factory(provider).generate(
            LLMRequest(
                provider=provider,
                model=model,
                api_key=api_key,
                instructions=build_project_semantic_index_instructions(),
                input_text=input_text,
                metadata={
                    "task_name": "project_semantic_index",
                    "prompt_schema_version": (
                        PROJECT_SEMANTIC_INDEX_PROMPT_SCHEMA_VERSION
                    ),
                    "project_id": project_id,
                    "source_count": len(
                        {subject.source_id for subject in subjects}
                    ),
                    "subject_count": len(subjects),
                },
            )
        )

        _validate_llm_completion(result)

        if llm_progress_observer is not None:
            notify_llm_progress(
                llm_progress_observer,
                event_type="completed",
                stage="project_semantic_index",
                request_count=1,
            )

        transport_proposals = parse_project_semantic_index_response(
            result.text,
            transport_subject_refs=tuple(
                subject.subject_ref
                for subject in transport_subjects
            ),
        )

        real_proposals = tuple(
            SemanticIndexGroupProposal(
                group_label=proposal.group_label,
                member_subject_refs=tuple(
                    sorted(
                        transport_to_real[ref]
                        for ref in proposal.member_subject_refs
                    )
                ),
            )
            for proposal in transport_proposals
        )

        output_fingerprint = sha256(
            result.text.encode("utf-8")
        ).hexdigest()

        return create_project_semantic_index_artifact(
            project_id=project_id,
            input_fingerprint=input_fingerprint,
            subjects=subjects,
            group_proposals=real_proposals,
            llm_provider=result.provider,
            llm_model=result.model,
            llm_response_id=result.response_id,
            llm_output_fingerprint=output_fingerprint,
        )
