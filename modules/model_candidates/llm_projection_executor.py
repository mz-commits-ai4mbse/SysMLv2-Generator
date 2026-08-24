"""Bounded execution adapter for H9 LLM-assisted target projection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from modules.agents.runner import run_llm_agent
from modules.agents.types import AgentRunResult

from .errors import ModelCandidateDerivationError
from .llm_projection_contract import (
    DEFAULT_LLM_PROJECTION_BATCH_SIZE,
    LLM_PROJECTION_TASK_INSTRUCTIONS,
    LLMProjectionRequest,
    LLMProjectionResponse,
    build_llm_projection_request,
    llm_projection_request_to_compact_json,
    parse_llm_projection_response,
)
from .types import (
    ModelCandidateDerivationRequest,
    ModelCandidateProjectionCoverage,
    ModelStructureProfile,
)


TARGET_PROJECTION_AGENT_ID = "AGENT_TARGET_PROJECTION_MAPPER"
TARGET_PROJECTION_TASK_NAME = "Resolve target-model projection"
DEFAULT_MAX_LLM_PROJECTION_CALLS_PER_RUN = 4


@dataclass(frozen=True, slots=True)
class LLMProjectionInvocation:
    """One validated LLM projection call with provider execution evidence."""

    request: LLMProjectionRequest
    response: LLMProjectionResponse
    provider: str
    model: str
    response_id: str | None
    usage: dict
    output_path: Path
    status: str | None
    supporting_response_fingerprints: tuple[str, ...] = ()
    supporting_agent_ids: tuple[str, ...] = ()


class LLMProjectionBatchExecutor:
    """Execute unresolved target-projection work serially and without retries."""

    agent_reference = "agents/target_projection_mapper.md"

    def __init__(
        self,
        *,
        project_root: Path,
        provider: str = "openai",
        model: str = "gpt-5.5",
        api_key: str | None = None,
        batch_size: int = DEFAULT_LLM_PROJECTION_BATCH_SIZE,
        max_calls_per_run: int = DEFAULT_MAX_LLM_PROJECTION_CALLS_PER_RUN,
        agent_runner: Callable[..., AgentRunResult] = run_llm_agent,
    ) -> None:
        if not isinstance(project_root, Path):
            raise ModelCandidateDerivationError(
                "project_root must be a pathlib.Path."
            )
        if not isinstance(batch_size, int) or isinstance(batch_size, bool):
            raise ModelCandidateDerivationError(
                "batch_size must be an integer."
            )
        if batch_size < 1 or batch_size > 16:
            raise ModelCandidateDerivationError(
                "batch_size must be between 1 and 16."
            )
        if (
            not isinstance(max_calls_per_run, int)
            or isinstance(max_calls_per_run, bool)
            or max_calls_per_run < 1
        ):
            raise ModelCandidateDerivationError(
                "max_calls_per_run must be a positive integer."
            )
        if not callable(agent_runner):
            raise ModelCandidateDerivationError(
                "agent_runner must be callable."
            )

        self.project_root = project_root
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.batch_size = batch_size
        self.max_calls_per_run = max_calls_per_run
        self._agent_runner = agent_runner

    def execute(
        self,
        *,
        request: ModelCandidateDerivationRequest,
        coverage: ModelCandidateProjectionCoverage,
        profile: ModelStructureProfile,
        output_dir: Path,
        explicit_escalation_approved_input_ids: tuple[str, ...] = (),
    ) -> tuple[LLMProjectionInvocation, ...]:
        """Execute eligible target-projection work in bounded serial batches."""

        eligible_ids = tuple(
            sorted(
                set(coverage.unresolved_approved_input_ids)
                | set(explicit_escalation_approved_input_ids)
            )
        )
        if not eligible_ids:
            return ()

        batches = tuple(
            eligible_ids[index : index + self.batch_size]
            for index in range(0, len(eligible_ids), self.batch_size)
        )
        if len(batches) > self.max_calls_per_run:
            raise ModelCandidateDerivationError(
                "LLM projection would exceed max_calls_per_run before "
                "execution."
            )

        personality_file = (
            self.project_root / "agents" / "target_projection_mapper.md"
        )
        if not personality_file.is_file():
            raise ModelCandidateDerivationError(
                "Target projection agent personality file is missing."
            )
        if not isinstance(output_dir, Path):
            raise ModelCandidateDerivationError(
                "output_dir must be a pathlib.Path."
            )

        invocations = []
        for index, approved_input_ids in enumerate(batches, start=1):
            llm_request = build_llm_projection_request(
                request=request,
                coverage=coverage,
                profile=profile,
                approved_input_ids=approved_input_ids,
                explicit_escalation_approved_input_ids=(
                    explicit_escalation_approved_input_ids
                ),
                max_batch_size=self.batch_size,
            )
            input_text = llm_projection_request_to_compact_json(llm_request)

            try:
                agent_result = self._agent_runner(
                    agent_id=TARGET_PROJECTION_AGENT_ID,
                    personality_file=personality_file,
                    task_name=TARGET_PROJECTION_TASK_NAME,
                    task_instructions=LLM_PROJECTION_TASK_INSTRUCTIONS,
                    input_text=input_text,
                    output_dir=output_dir / f"batch_{index:02d}",
                    provider=self.provider,
                    model=self.model,
                    api_key=self.api_key,
                    run_index=1,
                )
            except Exception as exc:
                raise ModelCandidateDerivationError(
                    "LLM target-projection execution failed; no automatic "
                    "retry was attempted."
                ) from exc

            if not isinstance(agent_result, AgentRunResult):
                raise ModelCandidateDerivationError(
                    "Target projection agent runner returned an invalid result."
                )

            response = parse_llm_projection_response(
                request=llm_request,
                output_text=agent_result.output_text,
            )
            invocations.append(
                LLMProjectionInvocation(
                    request=llm_request,
                    response=response,
                    provider=agent_result.provider,
                    model=agent_result.model,
                    response_id=agent_result.response_id,
                    usage=dict(agent_result.usage),
                    output_path=agent_result.output_path,
                    status=agent_result.status,
                )
            )

        return tuple(invocations)
