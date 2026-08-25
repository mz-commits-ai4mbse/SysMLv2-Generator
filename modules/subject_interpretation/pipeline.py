"""Run all configured Personas on one fixed canonical Subject population."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from modules.agents.team_config import (
    AgentTeamConfig,
    TeamMemberConfig,
    load_team_config,
)
from modules.agents.team_runner import (
    run_agent_team,
    run_team_member,
    select_team_members,
)
from modules.engineering_subjects.types import CanonicalSubjectSet
from modules.llm.progress import (
    LLMRequestProgressObserver,
    notify_llm_progress,
)
from modules.source_projection.types import SourceProjectionArtifact

from .contract import parse_subject_interpretation_output
from .errors import (
    SubjectInterpretationConfigurationError,
    SubjectInterpretationIntegrityError,
    SubjectInterpretationValidationError,
)
from .repair import (
    apply_classification_repair_response,
    build_classification_repair_input,
    build_classification_repair_task,
    find_classification_repair_needs,
)
from .prompt import (
    SUBJECT_INTERPRETATION_PROMPT_SCHEMA_VERSION,
    build_subject_interpretation_input,
    build_subject_interpretation_task_instructions,
)
from .types import (
    SharedSubjectInterpretationResult,
    SubjectInterpretationRunResult,
)


DEFAULT_TEAM_FILE = Path(
    "teams/ingestion/source_evidence_interpretation_team.json"
)

TeamRunner = Callable[..., Any]
TeamMemberRunner = Callable[..., Any]


class SubjectInterpretationPipeline:
    """Interpret the same immutable canonical Subject set with every Persona."""

    def __init__(
        self,
        *,
        project_root: Path | str = Path("."),
        team_file: Path | str = DEFAULT_TEAM_FILE,
        team_runner: TeamRunner = run_agent_team,
        team_member_runner: TeamMemberRunner = run_team_member,
    ) -> None:
        self.project_root = Path(project_root)
        self.team_file = Path(team_file)
        self._team_runner = team_runner
        self._team_member_runner = team_member_runner

    def planned_request_count(
        self,
        *,
        runs_per_persona: int,
        max_members: int | None,
    ) -> int:
        team = load_team_config(
            project_root=self.project_root,
            team_file=self.team_file,
        )
        members = tuple(
            select_team_members(
                team_config=team,
                max_members=max_members,
                include_alternative_members=False,
            )
        )
        return len(members) * runs_per_persona

    def run(
        self,
        *,
        source_projection: SourceProjectionArtifact,
        subject_set: CanonicalSubjectSet,
        execution_root: Path | str,
        provider: str,
        model: str,
        api_key: str | None = None,
        runs_per_persona: int = 1,
        max_members: int | None = None,
        llm_progress_observer: LLMRequestProgressObserver | None = None,
    ) -> SharedSubjectInterpretationResult:
        """Run every configured Persona over the exact same Subject population."""

        _validate_binding(source_projection, subject_set)

        if (
            isinstance(runs_per_persona, bool)
            or not isinstance(runs_per_persona, int)
            or not 1 <= runs_per_persona <= 5
        ):
            raise SubjectInterpretationConfigurationError(
                "runs_per_persona must be an integer from 1 to 5."
            )

        team = load_team_config(
            project_root=self.project_root,
            team_file=self.team_file,
        )
        members = tuple(
            select_team_members(
                team_config=team,
                max_members=max_members,
                include_alternative_members=False,
            )
        )
        if len(members) < 2:
            raise SubjectInterpretationConfigurationError(
                "Subject interpretation requires at least two Personas."
            )

        task_instructions = (
            build_subject_interpretation_task_instructions()
        )
        input_text = build_subject_interpretation_input(
            source_projection,
            subject_set,
            repository_root=self.project_root,
        )

        execution_path = Path(execution_root)
        raw_output_root = execution_path / "raw_team_runs"
        parsed_output_root = execution_path / "subject_interpretation"
        repair_output_root = execution_path / "classification_repairs"
        raw_output_root.mkdir(parents=True, exist_ok=True)
        parsed_output_root.mkdir(parents=True, exist_ok=True)
        repair_output_root.mkdir(parents=True, exist_ok=True)

        runner_kwargs = {
            "project_root": self.project_root,
            "team_file": self.team_file,
            "task_instructions": task_instructions,
            "input_text": input_text,
            "output_dir": raw_output_root,
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "runs_per_member": runs_per_persona,
            "max_members": max_members,
            "include_alternative_members": False,
            "dry_run": False,
        }
        if llm_progress_observer is not None:
            runner_kwargs["result_observer"] = (
                lambda result: notify_llm_progress(
                    llm_progress_observer,
                    event_type="completed",
                    stage="subject_interpretation",
                    detail=(
                        f"{result.agent_id} · run {result.run_index}"
                    ),
                )
            )
        raw_results = tuple(self._team_runner(**runner_kwargs))

        member_by_agent = {
            member.agent_id: member
            for member in members
        }
        expected_keys = {
            (member.agent_id, run_index)
            for member in members
            for run_index in range(1, runs_per_persona + 1)
        }
        actual_keys = {
            (result.agent_id, result.run_index)
            for result in raw_results
        }
        if (
            actual_keys != expected_keys
            or len(raw_results) != len(expected_keys)
        ):
            raise SubjectInterpretationIntegrityError(
                "Team runner results do not match configured Persona/run set."
            )

        run_results = []

        for raw_result in raw_results:
            member = member_by_agent.get(raw_result.agent_id)
            if member is None:
                raise SubjectInterpretationIntegrityError(
                    "Team runner returned an unexpected agent."
                )

            classification_repairs = ()
            try:
                parsed = parse_subject_interpretation_output(
                    raw_result.output_text,
                    subject_set=subject_set,
                )
            except SubjectInterpretationValidationError as exc:
                if str(exc) not in {
                    "information_type is not an allowed value.",
                    "statement_modality is not an allowed value.",
                    "epistemic_class is not an allowed value.",
                }:
                    raise
                needs = find_classification_repair_needs(
                    raw_result.output_text,
                    subject_set=subject_set,
                )
                if not needs:
                    raise

                notify_llm_progress(
                    llm_progress_observer,
                    event_type="planned",
                    stage="subject_interpretation",
                    detail=(
                        f"classification repair · {member.agent_id} · "
                        f"run {raw_result.run_index}"
                    ),
                )
                repair_result = self._team_member_runner(
                    team_config=team,
                    member=member,
                    task_instructions=build_classification_repair_task(needs),
                    input_text=build_classification_repair_input(
                        original_subject_input=input_text,
                        raw_output=raw_result.output_text,
                        needs=needs,
                    ),
                    output_dir=repair_output_root,
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    run_index=raw_result.run_index,
                    dry_run=False,
                )
                notify_llm_progress(
                    llm_progress_observer,
                    event_type="completed",
                    stage="subject_interpretation",
                    detail=(
                        f"classification repair · {member.agent_id} · "
                        f"run {raw_result.run_index}"
                    ),
                )
                repaired_text, classification_repairs = (
                    apply_classification_repair_response(
                        raw_output=raw_result.output_text,
                        repair_output=repair_result.output_text,
                        needs=needs,
                    )
                )
                parsed = parse_subject_interpretation_output(
                    repaired_text,
                    subject_set=subject_set,
                )

            run_result = _create_run_result(
                source_projection=source_projection,
                team=team,
                member=member,
                run_index=raw_result.run_index,
                provider=provider,
                model=model,
                interpretations=parsed.interpretations,
                relationships=parsed.relationships,
                rejected_relationships=parsed.rejected_relationships,
                classification_repairs=classification_repairs,
            )
            run_results.append(run_result)

            path = (
                parsed_output_root
                / member.agent_id.lower()
                / f"run_{raw_result.run_index:02d}.json"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                subject_interpretation_run_result_to_json(run_result),
                encoding="utf-8",
            )

        ordered_results = tuple(
            sorted(
                run_results,
                key=lambda result: (
                    result.persona_id,
                    result.persona_run_index,
                ),
            )
        )
        subject_ids = tuple(
            subject.canonical_subject_id
            for subject in subject_set.subjects
        )
        required_personas = tuple(
            sorted(member.persona_id for member in members)
        )

        return SharedSubjectInterpretationResult(
            project_id=source_projection.manifest.project_id,
            source_id=source_projection.manifest.source_id,
            source_projection_id=(
                source_projection.manifest.source_projection_id
            ),
            team_id=team.team_id,
            canonical_subject_ids=subject_ids,
            required_personas=required_personas,
            runs_per_persona=runs_per_persona,
            run_results=ordered_results,
            output_root=parsed_output_root,
        )


def subject_interpretation_run_result_to_dict(
    value: SubjectInterpretationRunResult,
) -> dict[str, Any]:
    return {
        "project_id": value.project_id,
        "source_id": value.source_id,
        "source_projection_id": value.source_projection_id,
        "team_id": value.team_id,
        "agent_id": value.agent_id,
        "persona_id": value.persona_id,
        "persona_run_index": value.persona_run_index,
        "llm_provider": value.llm_provider,
        "llm_model": value.llm_model,
        "prompt_schema_version": value.prompt_schema_version,
        "interpretations": [
            {
                "canonical_subject_id": item.canonical_subject_id,
                "interpreted_statement": item.interpreted_statement,
                "information_type": item.information_type,
                "statement_modality": item.statement_modality,
                "epistemic_class": item.epistemic_class,
                "missing_evidence": item.missing_evidence,
                "rationale": item.rationale,
                "uncertainties": list(item.uncertainties),
                "content_fingerprint": item.content_fingerprint,
            }
            for item in value.interpretations
        ],
        "relationships": [
            {
                "source_subject_id": item.source_subject_id,
                "relationship_kind": item.relationship_kind,
                "target_subject_id": item.target_subject_id,
                "statement": item.statement,
                "content_fingerprint": item.content_fingerprint,
            }
            for item in value.relationships
        ],
        "classification_repairs": [
            {
                "canonical_subject_id": item.canonical_subject_id,
                "field_name": item.field_name,
                "original_value": item.original_value,
                "repaired_value": item.repaired_value,
                "content_fingerprint": item.content_fingerprint,
            }
            for item in value.classification_repairs
        ],
        "rejected_relationships": [
            {
                "source_subject_id": item.source_subject_id,
                "relationship_kind": item.relationship_kind,
                "target_subject_id": item.target_subject_id,
                "statement": item.statement,
                "reason_code": item.reason_code,
                "content_fingerprint": item.content_fingerprint,
            }
            for item in value.rejected_relationships
        ],
        "content_fingerprint": value.content_fingerprint,
    }


def subject_interpretation_run_result_to_json(
    value: SubjectInterpretationRunResult,
) -> str:
    return (
        json.dumps(
            subject_interpretation_run_result_to_dict(value),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def _create_run_result(
    *,
    source_projection: SourceProjectionArtifact,
    team: AgentTeamConfig,
    member: TeamMemberConfig,
    run_index: int,
    provider: str,
    model: str,
    interpretations,
    relationships,
    rejected_relationships=(),
    classification_repairs=(),
) -> SubjectInterpretationRunResult:
    body = {
        "project_id": source_projection.manifest.project_id,
        "source_id": source_projection.manifest.source_id,
        "source_projection_id": (
            source_projection.manifest.source_projection_id
        ),
        "team_id": team.team_id,
        "agent_id": member.agent_id,
        "persona_id": member.persona_id,
        "persona_run_index": run_index,
        "llm_provider": provider,
        "llm_model": model,
        "prompt_schema_version": (
            SUBJECT_INTERPRETATION_PROMPT_SCHEMA_VERSION
        ),
        "interpretation_fingerprints": [
            item.content_fingerprint
            for item in interpretations
        ],
        "relationship_fingerprints": [
            item.content_fingerprint
            for item in relationships
        ],
        "rejected_relationship_fingerprints": [
            item.content_fingerprint
            for item in rejected_relationships
        ],
        "classification_repair_fingerprints": [
            item.content_fingerprint
            for item in classification_repairs
        ],
    }
    fingerprint = _canonical_sha256(body)

    return SubjectInterpretationRunResult(
        project_id=body["project_id"],
        source_id=body["source_id"],
        source_projection_id=body["source_projection_id"],
        team_id=body["team_id"],
        agent_id=body["agent_id"],
        persona_id=body["persona_id"],
        persona_run_index=body["persona_run_index"],
        llm_provider=body["llm_provider"],
        llm_model=body["llm_model"],
        prompt_schema_version=body["prompt_schema_version"],
        interpretations=interpretations,
        relationships=relationships,
        content_fingerprint=fingerprint,
        rejected_relationships=tuple(rejected_relationships),
        classification_repairs=tuple(classification_repairs),
    )


def _validate_binding(
    source_projection: SourceProjectionArtifact,
    subject_set: CanonicalSubjectSet,
) -> None:
    if not isinstance(source_projection, SourceProjectionArtifact):
        raise SubjectInterpretationConfigurationError(
            "source_projection must be a SourceProjectionArtifact."
        )
    if not isinstance(subject_set, CanonicalSubjectSet):
        raise SubjectInterpretationConfigurationError(
            "subject_set must be a CanonicalSubjectSet."
        )

    manifest = source_projection.manifest
    if (
        subject_set.project_id != manifest.project_id
        or subject_set.source_id != manifest.source_id
        or subject_set.source_projection_id != manifest.source_projection_id
        or subject_set.source_projection_fingerprint
        != manifest.projection_fingerprint
    ):
        raise SubjectInterpretationIntegrityError(
            "Canonical Subject Set does not bind the supplied Source Projection."
        )


def _canonical_sha256(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
