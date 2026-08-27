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
from modules.classification_alignment import (
    ClassificationAlignmentService,
    classification_alignment_result_to_json,
)
from modules.semantic_consistency_alignment import (
    SemanticConsistencyAlignmentService,
    semantic_consistency_result_to_json,
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
        classification_alignment_service: (
            ClassificationAlignmentService | None
        ) = None,
        semantic_consistency_alignment_service: (
            SemanticConsistencyAlignmentService | None
        ) = None,
    ) -> None:
        self.project_root = Path(project_root)
        self.team_file = Path(team_file)
        self._team_runner = team_runner
        self._team_member_runner = team_member_runner
        self._classification_alignment = (
            ClassificationAlignmentService()
            if classification_alignment_service is None
            else classification_alignment_service
        )
        self._semantic_consistency_alignment = (
            SemanticConsistencyAlignmentService()
            if semantic_consistency_alignment_service is None
            else semantic_consistency_alignment_service
        )

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
        alignment_output_root = execution_path / "classification_alignment"
        semantic_consistency_output_root = execution_path / "semantic_consistency_alignment"
        raw_output_root.mkdir(parents=True, exist_ok=True)
        parsed_output_root.mkdir(parents=True, exist_ok=True)
        alignment_output_root.mkdir(parents=True, exist_ok=True)

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

            alignment = self._classification_alignment.align_output(
                raw_result.output_text,
                item_id_field="canonical_subject_id",
                allowed_item_ids=tuple(
                    subject.canonical_subject_id
                    for subject in subject_set.subjects
                ),
                context_by_item_id=_subject_alignment_context(subject_set),
                provider=provider,
                model=model,
                api_key=api_key,
                llm_progress_observer=llm_progress_observer,
            )
            if alignment.decisions:
                alignment_path = (
                    alignment_output_root
                    / member.agent_id.lower()
                    / f"run_{raw_result.run_index:02d}.json"
                )
                alignment_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                alignment_path.write_text(
                    classification_alignment_result_to_json(alignment),
                    encoding="utf-8",
                )

            semantic_consistency = (
                self._semantic_consistency_alignment.align_output(
                    alignment.normalized_output_text,
                    item_id_field="canonical_subject_id",
                    allowed_item_ids=tuple(
                        subject.canonical_subject_id
                        for subject in subject_set.subjects
                    ),
                    context_by_item_id=_subject_alignment_context(subject_set),
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    llm_progress_observer=llm_progress_observer,
                )
            )
            if semantic_consistency.decisions:
                consistency_path = (
                    semantic_consistency_output_root
                    / member.agent_id.lower()
                    / f"run_{raw_result.run_index:02d}.json"
                )
                consistency_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                consistency_path.write_text(
                    semantic_consistency_result_to_json(
                        semantic_consistency
                    ),
                    encoding="utf-8",
                )

            parsed = parse_subject_interpretation_output(
                semantic_consistency.normalized_output_text,
                subject_set=subject_set,
            )
            classification_repairs = (
                _classification_alignment_compatibility_repairs(
                    alignment.decisions
                )
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



def _subject_alignment_context(
    subject_set: CanonicalSubjectSet,
) -> dict[str, str]:
    """Return source-grounded context for classification alignment only."""

    mention_by_id = {
        mention.mention_id: mention
        for mention in subject_set.mentions
    }
    result = {}
    for subject in subject_set.subjects:
        lines = [
            f"Canonical label: {subject.canonical_label}",
            f"Neutral subject form: {subject.subject_form}",
        ]
        for mention_id in subject.mention_ids:
            mention = mention_by_id.get(mention_id)
            if mention is not None:
                lines.append(f"Source mention: {mention.exact_text}")
        result[subject.canonical_subject_id] = "\n".join(lines)
    return result


def _classification_alignment_compatibility_repairs(decisions):
    """Project ADR-030 alignments into the legacy audit field temporarily."""

    from .types import PersonaClassificationRepair

    return tuple(
        PersonaClassificationRepair(
            canonical_subject_id=item.item_id,
            field_name=item.field_name,
            original_value=item.raw_value,
            repaired_value=item.normalized_value,
            content_fingerprint=item.content_fingerprint,
        )
        for item in decisions
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
