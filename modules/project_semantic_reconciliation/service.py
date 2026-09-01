"""LLM-assisted ADR-032 cross-source semantic reconciliation service."""

from __future__ import annotations
import dataclasses

from modules.llm.factory import create_llm_client
from modules.llm.progress import notify_llm_progress
from modules.llm.types import LLMRequest

from .contract import (
    create_project_semantic_reconciliation_artifact,
    parse_project_semantic_reconciliation_response,
    prepare_project_semantic_subjects,
)
from .errors import (
    ProjectSemanticReconciliationIntegrityError,
    ProjectSemanticReconciliationValidationError,
)
from .prompt import (
    PROJECT_SEMANTIC_RECONCILIATION_PROMPT_SCHEMA_VERSION,
    build_project_semantic_reconciliation_input,
    build_project_semantic_reconciliation_instructions,
)
from .types import (
    ProjectSemanticReconciliationArtifact,
    ProjectSemanticSourceInput,
)


_PROJECT_SEMANTIC_TRANSPORT_ALIAS_LIMIT = 9999

_PROJECT_SEMANTIC_TRANSPORT_INSTRUCTIONS = (
    "Transport identifier rules:\n"
    "- subject_ref values are opaque transport identifiers.\n"
    "- Every supplied subject_ref has the exact form SUBJ-NNNN.\n"
    "- Copy only identifiers that were supplied in the input.\n"
    "- Never construct, infer, shorten, expand, normalize, or otherwise modify an identifier.\n"
    "- An unknown or modified identifier is invalid and must never be substituted with a guessed value."
)


def _prepare_project_semantic_transport_subjects(
    subjects: tuple[ProjectSemanticSubject, ...],
) -> tuple[
    tuple[ProjectSemanticSubject, ...],
    dict[str, str],
]:
    if len(subjects) > _PROJECT_SEMANTIC_TRANSPORT_ALIAS_LIMIT:
        raise ProjectSemanticReconciliationValidationError(
            "Project semantic reconciliation exceeds the transient "
            "SUBJ-NNNN transport alias space."
        )

    transport_subjects = []
    transport_to_subject_ref: dict[str, str] = {}
    seen_subject_refs = set()

    for index, subject in enumerate(subjects, start=1):
        subject_ref = subject.subject_ref
        if subject_ref in seen_subject_refs:
            raise ProjectSemanticReconciliationIntegrityError(
                "Input Project semantic Subjects are not unique."
            )
        seen_subject_refs.add(subject_ref)

        transport_ref = f"SUBJ-{index:04d}"
        if transport_ref in transport_to_subject_ref:
            raise ProjectSemanticReconciliationIntegrityError(
                "Transient Project semantic transport identifiers "
                "are not unique."
            )

        transport_to_subject_ref[transport_ref] = subject_ref
        transport_subjects.append(
            dataclasses.replace(subject, subject_ref=transport_ref)
        )

    return tuple(transport_subjects), transport_to_subject_ref


def _restore_project_semantic_subject_refs(
    relations: tuple[ProjectSemanticRelation, ...],
    unmatched_subject_refs: tuple[str, ...],
    *,
    transport_to_subject_ref: dict[str, str],
) -> tuple[
    tuple[ProjectSemanticRelation, ...],
    tuple[str, ...],
]:
    def restore(value: str) -> str:
        try:
            return transport_to_subject_ref[value]
        except KeyError as exc:
            raise ProjectSemanticReconciliationIntegrityError(
                "Semantic reconciliation references an unknown transient "
                "subject_ref."
            ) from exc

    restored_relations = tuple(
        dataclasses.replace(
            relation,
            left_subject_ref=restore(relation.left_subject_ref),
            right_subject_ref=restore(relation.right_subject_ref),
        )
        for relation in relations
    )
    restored_unmatched = tuple(
        restore(subject_ref)
        for subject_ref in unmatched_subject_refs
    )
    return restored_relations, restored_unmatched


_PROJECT_SEMANTIC_PAIR_INSTRUCTIONS = (
    "This request contains Subjects from exactly two registered Engineering "
    "Sources. Compare only Subjects across these two Sources. Never create a "
    "relation between two Subjects from the same Source. The deterministic "
    "application layer controls Source-pair orchestration; this LLM request "
    "performs only the bounded semantic comparison for the supplied pair."
)


@dataclasses.dataclass(frozen=True, slots=True)
class ProjectSemanticPairProgressEvent:
    event_type: str
    pair_index: int
    total_pairs: int
    left_source_id: str
    right_source_id: str


def _prepare_project_semantic_source_pairs(
    subjects: tuple[ProjectSemanticSubject, ...],
) -> tuple[
    tuple[str, str, tuple[ProjectSemanticSubject, ...]],
    ...,
]:
    source_ids = tuple(
        sorted({subject.source_id for subject in subjects})
    )
    if len(source_ids) < 2:
        raise ProjectSemanticReconciliationValidationError(
            "Project semantic reconciliation requires Subjects from at "
            "least two different Sources."
        )

    by_source = {
        source_id: tuple(
            subject
            for subject in subjects
            if subject.source_id == source_id
        )
        for source_id in source_ids
    }

    pairs = []
    for left_index, left_source_id in enumerate(source_ids):
        for right_source_id in source_ids[left_index + 1:]:
            pair_subjects = (
                by_source[left_source_id]
                + by_source[right_source_id]
            )
            pairs.append(
                (
                    left_source_id,
                    right_source_id,
                    pair_subjects,
                )
            )

    return tuple(pairs)


def _notify_project_semantic_pair_progress(
    observer,
    *,
    event_type: str,
    pair_index: int,
    total_pairs: int,
    left_source_id: str,
    right_source_id: str,
) -> None:
    if observer is None:
        return
    observer(
        ProjectSemanticPairProgressEvent(
            event_type=event_type,
            pair_index=pair_index,
            total_pairs=total_pairs,
            left_source_id=left_source_id,
            right_source_id=right_source_id,
        )
    )


class ProjectSemanticReconciliationService:
    """Produce non-authoritative cross-source Subject relationship evidence."""

    def __init__(self, *, client_factory=create_llm_client) -> None:
        self._client_factory = client_factory


    def reconcile(
        self,
        source_inputs: tuple[ProjectSemanticSourceInput, ...],
        *,
        provider: str,
        model: str,
        api_key: str | None = None,
        llm_progress_observer=None,
        pair_progress_observer=None,
    ) -> ProjectSemanticReconciliationArtifact:
        project_id, subjects, input_fingerprint = (
            prepare_project_semantic_subjects(source_inputs)
        )
        source_pairs = _prepare_project_semantic_source_pairs(subjects)
        pair_count = len(source_pairs)

        if llm_progress_observer is not None:
            notify_llm_progress(
                llm_progress_observer,
                event_type="planned",
                stage="project_semantic_reconciliation",
                request_count=pair_count,
            )

        all_relations = []
        globally_related_refs = set()
        results = []

        for pair_index, (
            left_source_id,
            right_source_id,
            pair_subjects,
        ) in enumerate(source_pairs, start=1):
            (
                transport_subjects,
                transport_to_subject_ref,
            ) = _prepare_project_semantic_transport_subjects(
                pair_subjects
            )
            input_text = build_project_semantic_reconciliation_input(
                project_id=project_id,
                subjects=transport_subjects,
            )

            _notify_project_semantic_pair_progress(
                pair_progress_observer,
                event_type="started",
                pair_index=pair_index,
                total_pairs=pair_count,
                left_source_id=left_source_id,
                right_source_id=right_source_id,
            )

            try:
                result = self._client_factory(provider).generate(
                    LLMRequest(
                        provider=provider,
                        model=model,
                        api_key=api_key,
                        instructions=(
                            build_project_semantic_reconciliation_instructions()
                            + "\n\n"
                            + _PROJECT_SEMANTIC_TRANSPORT_INSTRUCTIONS
                            + "\n\n"
                            + _PROJECT_SEMANTIC_PAIR_INSTRUCTIONS
                        ),
                        input_text=input_text,
                        metadata={
                            "task_name": (
                                "project_semantic_reconciliation"
                            ),
                            "prompt_schema_version": (
                                PROJECT_SEMANTIC_RECONCILIATION_PROMPT_SCHEMA_VERSION
                            ),
                            "project_id": project_id,
                            "source_count": 2,
                            "subject_count": len(pair_subjects),
                            "source_pair_index": pair_index,
                            "source_pair_count": pair_count,
                            "left_source_id": left_source_id,
                            "right_source_id": right_source_id,
                        },
                    )
                )

                transport_relations, _ = (
                    parse_project_semantic_reconciliation_response(
                        result.text,
                        subjects=transport_subjects,
                    )
                )
                relations, _ = (
                    _restore_project_semantic_subject_refs(
                        transport_relations,
                        (),
                        transport_to_subject_ref=(
                            transport_to_subject_ref
                        ),
                    )
                )
            except Exception:
                _notify_project_semantic_pair_progress(
                    pair_progress_observer,
                    event_type="failed",
                    pair_index=pair_index,
                    total_pairs=pair_count,
                    left_source_id=left_source_id,
                    right_source_id=right_source_id,
                )
                raise

            results.append(result)
            all_relations.extend(relations)

            for relation in relations:
                globally_related_refs.update(
                    (
                        relation.left_subject_ref,
                        relation.right_subject_ref,
                    )
                )

            _notify_project_semantic_pair_progress(
                pair_progress_observer,
                event_type="completed",
                pair_index=pair_index,
                total_pairs=pair_count,
                left_source_id=left_source_id,
                right_source_id=right_source_id,
            )

        if llm_progress_observer is not None:
            notify_llm_progress(
                llm_progress_observer,
                event_type="completed",
                stage="project_semantic_reconciliation",
                request_count=pair_count,
            )

        providers = {result.provider for result in results}
        models = {result.model for result in results}
        if len(providers) != 1 or len(models) != 1:
            raise ProjectSemanticReconciliationIntegrityError(
                "Pairwise S3 LLM results do not share one exact "
                "provider/model binding."
            )

        unmatched = tuple(
            subject.subject_ref
            for subject in subjects
            if subject.subject_ref not in globally_related_refs
        )

        llm_response_id = (
            results[0].response_id
            if len(results) == 1
            else None
        )

        return create_project_semantic_reconciliation_artifact(
            project_id=project_id,
            subjects=subjects,
            input_fingerprint=input_fingerprint,
            relations=tuple(all_relations),
            unmatched_subject_refs=unmatched,
            llm_provider=next(iter(providers)),
            llm_model=next(iter(models)),
            llm_response_id=llm_response_id,
        )
