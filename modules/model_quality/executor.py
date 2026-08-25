"""LLM execution for classification-dependent SEM-015 model-quality refinement."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any, Callable

from modules.agents.team_runner import run_agent_team

from .contract import (
    MODEL_QUALITY_TASK_INSTRUCTIONS,
    create_refinement_bundle,
    parse_refinement_response,
    refinement_request_to_compact_json,
    subset_request,
)
from .errors import ModelQualityError


DEFAULT_MODEL_QUALITY_TEAM_FILE = Path(
    "teams/modeling/model_quality_refinement_team.json"
)
DEFAULT_MODEL_QUALITY_BATCH_SIZE = 12


class ModelQualityRefinementExecutor:
    """Run a small focused LLM call after Human model classification/placement."""

    def __init__(
        self,
        *,
        project_root: Path,
        provider: str = "openai",
        model: str = "gpt-5.5",
        api_key: str | None = None,
        batch_size: int = DEFAULT_MODEL_QUALITY_BATCH_SIZE,
        team_file: Path = DEFAULT_MODEL_QUALITY_TEAM_FILE,
        team_runner: Callable[..., Any] = run_agent_team,
        clock=None,
    ) -> None:
        if not isinstance(project_root, Path):
            raise ModelQualityError("project_root must be pathlib.Path.")
        if not isinstance(batch_size, int) or isinstance(batch_size, bool):
            raise ModelQualityError("batch_size must be an integer.")
        if not 1 <= batch_size <= 32:
            raise ModelQualityError("batch_size must be between 1 and 32.")
        self.project_root = project_root
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.batch_size = batch_size
        self.team_file = team_file
        self._team_runner = team_runner
        self._clock = clock

    def execute(
        self,
        *,
        request,
        review_id: str,
        output_dir: Path,
        progress: Callable[[str], None] | None = None,
    ):
        ids = tuple(
            item.internal_model_element_id
            for item in request.elements
        )
        batches = tuple(
            ids[index : index + self.batch_size]
            for index in range(0, len(ids), self.batch_size)
        )
        proposals = []
        response_fps = []

        _progress(
            progress,
            (
                "Semantic model-quality refinement started: "
                f"{len(ids)} element(s), {len(batches)} LLM batch(es)."
            ),
        )

        for index, element_ids in enumerate(batches, start=1):
            batch = subset_request(request, element_ids)
            batch_dir = output_dir / f"batch_{index:02d}"
            _progress(
                progress,
                (
                    f"LLM batch {index}/{len(batches)}: refining "
                    f"{len(element_ids)} classified model element(s)."
                ),
            )
            results = tuple(
                self._team_runner(
                    project_root=self.project_root,
                    team_file=self.team_file,
                    task_instructions=MODEL_QUALITY_TASK_INSTRUCTIONS,
                    input_text=refinement_request_to_compact_json(batch),
                    output_dir=batch_dir,
                    provider=self.provider,
                    model=self.model,
                    api_key=self.api_key,
                    runs_per_member=1,
                    max_members=None,
                    include_alternative_members=False,
                    dry_run=False,
                )
            )
            if len(results) != 1 or results[0].run_index != 1:
                raise ModelQualityError(
                    "Model-quality refinement requires exactly one configured "
                    "LLM result per batch."
                )
            result = results[0]
            if result.provider != self.provider or result.model != self.model:
                raise ModelQualityError(
                    "Model-quality provider/model drift detected."
                )
            parsed = parse_refinement_response(
                request=batch,
                output_text=result.output_text,
            )
            proposals.extend(parsed)
            response_fps.append(
                hashlib.sha256(
                    result.output_text.encode("utf-8")
                ).hexdigest()
            )
            _progress(
                progress,
                f"LLM batch {index}/{len(batches)} validated.",
            )

        by_id = {
            item.internal_model_element_id: item
            for item in proposals
        }
        ordered = tuple(
            by_id[item.internal_model_element_id]
            for item in request.elements
        )
        bundle = create_refinement_bundle(
            request=request,
            review_id=review_id,
            provider=self.provider,
            model=self.model,
            proposals=ordered,
            supporting_response_fingerprints=tuple(response_fps),
            generated_at=self._now(),
        )
        _progress(
            progress,
            "Semantic model-quality refinement completed; Human review required.",
        )
        return bundle

    def _now(self) -> str:
        if self._clock is None:
            value = datetime.now(timezone.utc)
        else:
            value = self._clock()
        return value.astimezone(timezone.utc).isoformat().replace(
            "+00:00",
            "Z",
        )


def _progress(callback, message: str) -> None:
    if callback is not None:
        callback(message)
