"""Bounded LLM-assisted semantic field consistency alignment."""

from __future__ import annotations

from modules.llm.factory import create_llm_client
from modules.llm.progress import notify_llm_progress
from modules.llm.types import LLMRequest

from .contract import (
    apply_semantic_consistency_alignment,
    find_semantic_consistency_needs,
    parse_semantic_consistency_response,
)
from .prompt import (
    SEMANTIC_CONSISTENCY_PROMPT_SCHEMA_VERSION,
    build_semantic_consistency_input,
    build_semantic_consistency_instructions,
)
from .types import SemanticConsistencyResult


class SemanticConsistencyAlignmentService:
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
    ) -> SemanticConsistencyResult:
        needs = find_semantic_consistency_needs(
            text,
            item_id_field=item_id_field,
            allowed_item_ids=allowed_item_ids,
            context_by_item_id=context_by_item_id,
        )
        if not needs:
            return SemanticConsistencyResult(text, ())

        if llm_progress_observer is not None:
            notify_llm_progress(
                llm_progress_observer,
                event_type="planned",
                stage="semantic_consistency_alignment",
                request_count=1,
            )

        result = self._client_factory(provider).generate(
            LLMRequest(
                provider=provider,
                model=model,
                api_key=api_key,
                instructions=build_semantic_consistency_instructions(),
                input_text=build_semantic_consistency_input(needs),
                metadata={
                    "task_name": "semantic_field_consistency_alignment",
                    "prompt_schema_version": (
                        SEMANTIC_CONSISTENCY_PROMPT_SCHEMA_VERSION
                    ),
                    "consistency_request_count": len(needs),
                },
            )
        )

        if llm_progress_observer is not None:
            notify_llm_progress(
                llm_progress_observer,
                event_type="completed",
                stage="semantic_consistency_alignment",
                request_count=1,
            )

        decisions = parse_semantic_consistency_response(
            result.text,
            needs=needs,
            mapper_response_id=result.response_id,
        )

        return SemanticConsistencyResult(
            normalized_output_text=(
                apply_semantic_consistency_alignment(
                    text,
                    item_id_field=item_id_field,
                    decisions=decisions,
                )
            ),
            decisions=decisions,
            mapper_response_id=result.response_id,
            mapper_output_text=result.text,
        )
