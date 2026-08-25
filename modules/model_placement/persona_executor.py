"""Execute the dedicated three-persona Model Placement department."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from modules.agents.team_config import load_team_config
from modules.agents.team_runner import run_agent_team, select_team_members
from modules.model_candidates.llm_projection_contract import (
    LLMProjectionRequest,
    llm_projection_request_to_compact_json,
    parse_llm_projection_response,
)

from .comparison import compare_model_placement_personas
from .errors import ModelPlacementContractError


DEFAULT_MODEL_PLACEMENT_TEAM_FILE = Path(
    "teams/modeling/modeling_projection_team.json"
)

MODEL_PLACEMENT_TASK_INSTRUCTIONS = """Return only one JSON object. Do not use Markdown fences.

Required shape:
{"proposals":[{"approved_input_id":"AIN-000001","result":"proposed_mapping|ambiguous|unmapped","selected_rule_id":"RULE_ID or null","alternative_rule_ids":[],"rationale":"concise rationale"}]}

Task:
- This is Model Placement only: sort each already-approved engineering item into the supplied RFLP / target-framework options.
- Do not assemble a model, create hierarchy, create relationships, generate diagrams, or generate SysML v2 code.
- Return exactly one proposal for every input item and no extra proposals.
- Use only rule IDs listed in that item's allowed_target_options.
- proposed_mapping: select exactly one allowed rule; alternatives must be empty.
- ambiguous: selected_rule_id must be null; provide at least two allowed alternatives.
- unmapped: selected_rule_id must be null; alternatives must be empty.
- Treat Stakeholder / System / Subsystem level as an explicit modeling decision.
- You may use the other approved items in the same request as relative architectural context, but you may not invent new engineering meaning or relationships.
- Prefer unmapped over forcing an unsupported placement.
- Do not approve anything. Human Model Placement Review is authoritative.
- Do not expose chain-of-thought; provide only a short rationale.
""".strip()


class ModelPlacementPersonaExecutor:
    """Run all three dedicated placement personas over one coherent request."""

    def __init__(
        self,
        *,
        project_root: Path,
        provider: str = "openai",
        model: str = "gpt-5.4-mini",
        api_key: str | None = None,
        team_file: Path = DEFAULT_MODEL_PLACEMENT_TEAM_FILE,
        team_runner: Callable[..., Any] = run_agent_team,
    ) -> None:
        self.project_root = Path(project_root)
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.team_file = team_file
        self._team_runner = team_runner

    def execute(
        self,
        *,
        request: LLMProjectionRequest,
        output_dir: Path,
    ):
        if not isinstance(request, LLMProjectionRequest):
            raise ModelPlacementContractError(
                "Model Placement executor requires LLMProjectionRequest."
            )
        if not request.items:
            raise ModelPlacementContractError(
                "Model Placement executor requires at least one item."
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
            raise ModelPlacementContractError(
                "Model Placement requires exactly three configured personas."
            )

        member_by_agent = {
            member.agent_id: member
            for member in members
        }
        raw_root = output_dir / "persona_outputs"
        raw_results = tuple(
            self._team_runner(
                project_root=self.project_root,
                team_file=self.team_file,
                task_instructions=MODEL_PLACEMENT_TASK_INSTRUCTIONS,
                input_text=llm_projection_request_to_compact_json(
                    request
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

        if (
            len(raw_results) != 3
            or {item.agent_id for item in raw_results}
            != set(member_by_agent)
            or any(item.run_index != 1 for item in raw_results)
        ):
            raise ModelPlacementContractError(
                "Model Placement execution does not match the exact "
                "three-persona team contract."
            )

        persona_responses = tuple(
            sorted(
                (
                    (
                        member_by_agent[result.agent_id].persona_id,
                        parse_llm_projection_response(
                            request=request,
                            output_text=result.output_text,
                        ),
                    )
                    for result in raw_results
                ),
                key=lambda item: item[0],
            )
        )
        comparison = compare_model_placement_personas(
            request=request,
            persona_responses=persona_responses,
        )

        output_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            "schema_version": "1.0.0",
            "provider": self.provider,
            "model": self.model,
            "request_fingerprint": request.request_fingerprint,
            "comparison_fingerprint": comparison.content_fingerprint,
            "persona_ids": list(comparison.persona_ids),
            "item_count": len(comparison.items),
            "agreement_counts": {
                level: sum(
                    1
                    for item in comparison.items
                    if item.agreement_level == level
                )
                for level in (
                    "unanimous_mapping",
                    "partial_mapping_agreement",
                    "placement_variance",
                    "unresolved",
                )
            },
        }
        (output_dir / "model_placement_execution.json").write_text(
            json.dumps(
                summary,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return comparison
