"""Bounded LLM-assisted controlled classification alignment."""

from __future__ import annotations

from modules.llm.factory import create_llm_client
from modules.llm.progress import notify_llm_progress
from modules.llm.types import LLMRequest

from .contract import (
    apply_classification_alignment,
    fallback_unclassified_decisions,
    find_classification_alignment_needs,
    lexical_alignment_decision,
    parse_classification_alignment_response,
)
from .errors import ClassificationAlignmentValidationError
from .prompt import (
    CLASSIFICATION_ALIGNMENT_PROMPT_SCHEMA_VERSION,
    build_classification_alignment_input,
    build_classification_alignment_instructions,
)
from .types import ClassificationAlignmentResult


class ClassificationAlignmentService:
    def __init__(self, *, client_factory=create_llm_client) -> None:
        self._client_factory = client_factory

    def align_output(
        self,
        text: str,
        *,
        item_id_field: str,
        allowed_item_ids,
        context_by_item_id,
        provider: str,
        model: str,
        api_key: str | None = None,
        llm_progress_observer=None,
    ) -> ClassificationAlignmentResult:
        needs = find_classification_alignment_needs(
            text,
            item_id_field=item_id_field,
            allowed_item_ids=allowed_item_ids,
            context_by_item_id=context_by_item_id,
        )
        if not needs:
            return ClassificationAlignmentResult(text, ())

        deterministic = []
        unresolved = []
        for need in needs:
            decision = lexical_alignment_decision(need)
            (deterministic if decision is not None else unresolved).append(
                decision if decision is not None else need
            )

        mapped = ()
        response_id = None
        response_text = None
        if unresolved:
            unresolved = tuple(unresolved)
            if llm_progress_observer is not None:
                notify_llm_progress(
                    llm_progress_observer,
                    event_type="planned",
                    stage="classification_alignment",
                    request_count=1,
                )
            try:
                result = self._client_factory(provider).generate(
                    LLMRequest(
                        provider=provider,
                        model=model,
                        api_key=api_key,
                        instructions=build_classification_alignment_instructions(),
                        input_text=build_classification_alignment_input(unresolved),
                        metadata={
                            "task_name": "controlled_classification_alignment",
                            "prompt_schema_version": CLASSIFICATION_ALIGNMENT_PROMPT_SCHEMA_VERSION,
                            "alignment_request_count": len(unresolved),
                        },
                    )
                )
            except Exception:
                mapped = fallback_unclassified_decisions(
                    unresolved,
                    rationale=(
                        "Classification mapper execution failed; semantic specificity "
                        "was withheld using the existing neutral Information Type."
                    ),
                    mapper_response_id=None,
                )
            else:
                response_id = result.response_id
                response_text = result.text
                if llm_progress_observer is not None:
                    notify_llm_progress(
                        llm_progress_observer,
                        event_type="completed",
                        stage="classification_alignment",
                        request_count=1,
                    )
                try:
                    mapped = parse_classification_alignment_response(
                        result.text,
                        needs=unresolved,
                        mapper_response_id=result.response_id,
                    )
                except ClassificationAlignmentValidationError:
                    mapped = fallback_unclassified_decisions(
                        unresolved,
                        rationale=(
                            "Classification mapper response violated the alignment "
                            "contract; semantic specificity was withheld using the "
                            "existing neutral Information Type."
                        ),
                        mapper_response_id=result.response_id,
                    )

        decisions = tuple(
            sorted((*deterministic, *mapped), key=lambda d: (d.item_id, d.field_name))
        )
        return ClassificationAlignmentResult(
            normalized_output_text=apply_classification_alignment(
                text,
                item_id_field=item_id_field,
                decisions=decisions,
            ),
            decisions=decisions,
            mapper_response_id=response_id,
            mapper_output_text=response_text,
        )
