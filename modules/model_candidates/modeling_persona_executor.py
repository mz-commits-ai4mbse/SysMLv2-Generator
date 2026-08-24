"""Multi-persona executor for profile-bounded target-model projection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from modules.agents.team_config import load_team_config
from modules.agents.team_runner import (
    run_agent_team,
    select_team_members,
)

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
from .llm_projection_executor import LLMProjectionInvocation
from .types import (
    ModelCandidateDerivationRequest,
    ModelCandidateProjectionCoverage,
    ModelStructureProfile,
)


DEFAULT_MODELING_PROJECTION_TEAM_FILE = Path(
    "teams/modeling/modeling_projection_team.json"
)
DEFAULT_MAX_MODELING_BATCHES_PER_RUN = 4


def consolidate_modeling_persona_responses(
    *,
    request: LLMProjectionRequest,
    persona_responses: tuple[
        tuple[str, LLMProjectionResponse],
        ...,
    ],
) -> LLMProjectionResponse:
    """Consolidate profile-rule decisions without majority forcing."""

    if not isinstance(request, LLMProjectionRequest):
        raise ModelCandidateDerivationError(
            "request must be LLMProjectionRequest."
        )
    if (
        not isinstance(persona_responses, tuple)
        or len(persona_responses) < 2
    ):
        raise ModelCandidateDerivationError(
            "Modeling projection requires at least two persona responses."
        )

    agent_ids = tuple(item[0] for item in persona_responses)
    if (
        any(not isinstance(value, str) or not value for value in agent_ids)
        or len(agent_ids) != len(set(agent_ids))
    ):
        raise ModelCandidateDerivationError(
            "Modeling persona response agent IDs must be unique."
        )

    by_agent = {}
    for agent_id, response in persona_responses:
        if not isinstance(response, LLMProjectionResponse):
            raise ModelCandidateDerivationError(
                "Modeling persona response has invalid type."
            )
        if response.request_fingerprint != request.request_fingerprint:
            raise ModelCandidateDerivationError(
                "Modeling persona response does not bind the exact request."
            )
        by_agent[agent_id] = {
            item.approved_input_id: item
            for item in response.proposals
        }

    expected_ids = tuple(
        sorted(item.approved_input_id for item in request.items)
    )
    for agent_id, proposals in by_agent.items():
        if tuple(sorted(proposals)) != expected_ids:
            raise ModelCandidateDerivationError(
                "Each modeling persona must return exactly the requested "
                f"Approved Inputs: {agent_id}."
            )

    consolidated = []
    for approved_input_id in expected_ids:
        proposals = tuple(
            by_agent[agent_id][approved_input_id]
            for agent_id in sorted(by_agent)
        )
        consolidated.append(
            _consolidate_one(
                approved_input_id=approved_input_id,
                proposals=proposals,
            )
        )

    return parse_llm_projection_response(
        request=request,
        output_text=json.dumps(
            {"proposals": consolidated},
            ensure_ascii=False,
        ),
    )


def _consolidate_one(
    *,
    approved_input_id: str,
    proposals,
) -> dict[str, Any]:
    unanimous_mapping = (
        all(item.result == "proposed_mapping" for item in proposals)
        and len(
            {item.selected_rule_id for item in proposals}
        )
        == 1
    )

    if unanimous_mapping:
        selected_rule_id = proposals[0].selected_rule_id
        return {
            "approved_input_id": approved_input_id,
            "result": "proposed_mapping",
            "selected_rule_id": selected_rule_id,
            "alternative_rule_ids": [],
            "rationale": (
                "All modeling personas independently selected the same "
                f"profile-controlled rule {selected_rule_id}."
            ),
        }

    referenced_rules = set()
    for item in proposals:
        if item.selected_rule_id is not None:
            referenced_rules.add(item.selected_rule_id)
        referenced_rules.update(item.alternative_rule_ids)

    if len(referenced_rules) >= 2:
        return {
            "approved_input_id": approved_input_id,
            "result": "ambiguous",
            "selected_rule_id": None,
            "alternative_rule_ids": sorted(referenced_rules),
            "rationale": (
                "Modeling personas did not converge on one target rule; "
                "material profile-bounded variance is preserved."
            ),
        }

    return {
        "approved_input_id": approved_input_id,
        "result": "unmapped",
        "selected_rule_id": None,
        "alternative_rule_ids": [],
        "rationale": (
            "Modeling personas did not unanimously support one target rule. "
            "The mapping remains unresolved rather than using majority voting."
        ),
    }


class ModelingPersonaProjectionExecutor:
    """Execute three modeling personas on the same bounded projection request."""

    agent_reference = (
        "teams/modeling/modeling_projection_team.json"
    )

    def __init__(
        self,
        *,
        project_root: Path,
        provider: str = "openai",
        model: str = "gpt-5.5",
        api_key: str | None = None,
        batch_size: int = DEFAULT_LLM_PROJECTION_BATCH_SIZE,
        max_batches_per_run: int = DEFAULT_MAX_MODELING_BATCHES_PER_RUN,
        team_file: Path = DEFAULT_MODELING_PROJECTION_TEAM_FILE,
        team_runner: Callable[..., Any] = run_agent_team,
    ) -> None:
        if not isinstance(project_root, Path):
            raise ModelCandidateDerivationError(
                "project_root must be a pathlib.Path."
            )
        if (
            not isinstance(batch_size, int)
            or isinstance(batch_size, bool)
            or not 1 <= batch_size <= 16
        ):
            raise ModelCandidateDerivationError(
                "batch_size must be an integer between 1 and 16."
            )
        if (
            not isinstance(max_batches_per_run, int)
            or isinstance(max_batches_per_run, bool)
            or max_batches_per_run < 1
        ):
            raise ModelCandidateDerivationError(
                "max_batches_per_run must be a positive integer."
            )
        if not isinstance(team_file, Path):
            raise ModelCandidateDerivationError(
                "team_file must be a pathlib.Path."
            )
        if not callable(team_runner):
            raise ModelCandidateDerivationError(
                "team_runner must be callable."
            )

        self.project_root = project_root
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.batch_size = batch_size
        self.max_batches_per_run = max_batches_per_run
        self.team_file = team_file
        self._team_runner = team_runner

    def execute(
        self,
        *,
        request: ModelCandidateDerivationRequest,
        coverage: ModelCandidateProjectionCoverage,
        profile: ModelStructureProfile,
        output_dir: Path,
        explicit_escalation_approved_input_ids: tuple[str, ...] = (),
    ) -> tuple[LLMProjectionInvocation, ...]:
        """Run identical profile-bounded batches across all modeling personas."""

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
        if len(batches) > self.max_batches_per_run:
            raise ModelCandidateDerivationError(
                "Modeling persona projection would exceed "
                "max_batches_per_run before execution."
            )

        team = load_team_config(
            project_root=self.project_root,
            team_file=self.team_file,
        )
        members = tuple(
            select_team_members(
                team_config=team,
                max_members=None,
                include_alternative_members=False,
            )
        )
        if len(members) != 3:
            raise ModelCandidateDerivationError(
                "Modeling projection requires exactly three configured "
                "persona perspectives."
            )

        expected_agent_ids = tuple(
            sorted(member.agent_id for member in members)
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
            batch_root = output_dir / f"batch_{index:02d}"
            raw_root = batch_root / "persona_outputs"
            raw_results = tuple(
                self._team_runner(
                    project_root=self.project_root,
                    team_file=self.team_file,
                    task_instructions=(
                        LLM_PROJECTION_TASK_INSTRUCTIONS
                    ),
                    input_text=(
                        llm_projection_request_to_compact_json(
                            llm_request
                        )
                    ),
                    output_dir=raw_root,
                    provider=self.provider,
                    model=self.model,
                    api_key=self.api_key,
                    runs_per_member=1,
                    max_members=None,
                    include_alternative_members=False,
                    dry_run=False,
                )
            )

            actual_agent_ids = tuple(
                sorted(item.agent_id for item in raw_results)
            )
            if (
                actual_agent_ids != expected_agent_ids
                or len(raw_results) != len(expected_agent_ids)
                or any(item.run_index != 1 for item in raw_results)
            ):
                raise ModelCandidateDerivationError(
                    "Modeling team results do not match the configured "
                    "three-persona execution contract."
                )

            parsed = tuple(
                sorted(
                    (
                        (
                            result.agent_id,
                            parse_llm_projection_response(
                                request=llm_request,
                                output_text=result.output_text,
                            ),
                        )
                        for result in raw_results
                    ),
                    key=lambda item: item[0],
                )
            )
            consolidated = consolidate_modeling_persona_responses(
                request=llm_request,
                persona_responses=parsed,
            )

            batch_root.mkdir(parents=True, exist_ok=True)
            summary_path = (
                batch_root / "modeling_persona_consolidated.json"
            )
            summary_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "request_fingerprint": (
                            llm_request.request_fingerprint
                        ),
                        "persona_responses": [
                            {
                                "agent_id": agent_id,
                                "response_fingerprint": (
                                    response.response_fingerprint
                                ),
                            }
                            for agent_id, response in parsed
                        ],
                        "consolidated_response_fingerprint": (
                            consolidated.response_fingerprint
                        ),
                        "consolidated_proposals": [
                            {
                                "approved_input_id": (
                                    proposal.approved_input_id
                                ),
                                "result": proposal.result,
                                "selected_rule_id": (
                                    proposal.selected_rule_id
                                ),
                                "alternative_rule_ids": list(
                                    proposal.alternative_rule_ids
                                ),
                                "rationale": proposal.rationale,
                            }
                            for proposal in consolidated.proposals
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            providers = {item.provider for item in raw_results}
            models = {item.model for item in raw_results}
            if providers != {self.provider} or models != {self.model}:
                raise ModelCandidateDerivationError(
                    "Modeling persona provider/model drift detected."
                )

            invocations.append(
                LLMProjectionInvocation(
                    request=llm_request,
                    response=consolidated,
                    provider=self.provider,
                    model=self.model,
                    response_id=None,
                    usage=_aggregate_usage(raw_results),
                    output_path=summary_path,
                    status="modeling_persona_consolidated",
                    supporting_response_fingerprints=tuple(
                        response.response_fingerprint
                        for _agent_id, response in parsed
                    ),
                    supporting_agent_ids=tuple(
                        agent_id for agent_id, _response in parsed
                    ),
                )
            )

        return tuple(invocations)


def _aggregate_usage(results) -> dict[str, Any]:
    totals: dict[str, Any] = {}
    for result in results:
        for key, value in dict(result.usage).items():
            if isinstance(value, int) and not isinstance(value, bool):
                totals[key] = totals.get(key, 0) + value
    return totals
