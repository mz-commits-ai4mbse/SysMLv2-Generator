"""Run personas on the same fixed Source Evidence and analyze consensus."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from modules.agents.team_config import (
    AgentTeamConfig,
    TeamMemberConfig,
    load_team_config,
)
from modules.classification_alignment import (
    ClassificationAlignmentService,
    classification_alignment_result_to_json,
)
from modules.semantic_consistency_alignment import (
    SemanticConsistencyAlignmentService,
    semantic_consistency_result_to_json,
)
from modules.agents.team_runner import (
    run_agent_team,
    select_team_members,
)
from modules.llm.progress import (
    LLMRequestProgressObserver,
    notify_llm_progress,
)
from modules.semantic_consensus import (
    analyze_semantic_consensus,
    semantic_consensus_result_to_json,
)
from modules.semantic_extraction import (
    create_semantic_extraction_agent_result,
    semantic_extraction_agent_result_to_json,
)
from modules.source_evidence.types import SourceEvidence
from modules.source_projection.identifiers import segment_id_sequence
from modules.source_projection.types import SourceProjectionArtifact

from .contract import (
    materialize_information_unit_candidates,
    parse_evidence_interpretation_output,
)
from .errors import (
    EvidenceInterpretationConfigurationError,
    EvidenceInterpretationIntegrityError,
)
from .prompt import (
    EVIDENCE_INTERPRETATION_PROMPT_SCHEMA_VERSION,
    build_evidence_interpretation_input,
    build_evidence_interpretation_task_instructions,
)
from .types import (
    EvidenceInterpretationValue,
    SharedEvidenceInterpretationResult,
)


DEFAULT_TEAM_FILE = Path(
    "teams/ingestion/source_evidence_interpretation_team.json"
)
SEMANTIC_CONSENSUS_REPORT_ID = "CONS-SHARED-EVIDENCE-001"
BINDING_SUMMARY_SCHEMA_VERSION = "1.0.0"

TeamRunner = Callable[..., Any]


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class SharedEvidenceInterpretationPipeline:
    """Execute interpretation personas only after Evidence identity is fixed."""

    def __init__(
        self,
        *,
        project_root: Path | str = Path("."),
        team_file: Path | str = DEFAULT_TEAM_FILE,
        team_runner: TeamRunner = run_agent_team,
        clock: Callable[[], datetime] = _default_clock,
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
        self._clock = clock
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
        source_evidence: tuple[SourceEvidence, ...],
        execution_root: Path | str,
        provider: str,
        model: str,
        api_key: str | None = None,
        runs_per_persona: int = 1,
        max_members: int | None = None,
        dry_run: bool = False,
        llm_progress_observer: LLMRequestProgressObserver | None = None,
    ) -> SharedEvidenceInterpretationResult:
        """Interpret exactly one common Evidence set and calculate consensus."""

        projection = _require_projection(source_projection)
        evidence = _validated_and_sorted_evidence(
            source_evidence,
            projection=projection,
        )
        if not evidence:
            raise EvidenceInterpretationConfigurationError(
                "Shared-Evidence interpretation requires at least one "
                "persisted Source Evidence object."
            )
        if (
            isinstance(runs_per_persona, bool)
            or not isinstance(runs_per_persona, int)
            or not 1 <= runs_per_persona <= 5
        ):
            raise EvidenceInterpretationConfigurationError(
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
            raise EvidenceInterpretationConfigurationError(
                "Shared-Evidence semantic consensus requires at least "
                "two interpretation personas."
            )

        execution_path = Path(execution_root)
        agent_output_root = execution_path / "agent_outputs"
        consensus_output_root = execution_path / "consensus_reports"
        classification_alignment_output_root = (
            agent_output_root / "classification_alignment"
        )
        semantic_consistency_output_root = (
            agent_output_root / "semantic_consistency_alignment"
        )
        agent_output_root.mkdir(parents=True, exist_ok=True)
        consensus_output_root.mkdir(parents=True, exist_ok=True)

        expected_ids = tuple(
            item.source_evidence_id for item in evidence
        )
        input_text = build_evidence_interpretation_input(evidence)
        task_instructions = (
            build_evidence_interpretation_task_instructions()
        )

        if dry_run:
            semantic_results = self._dry_run_results(
                team=team,
                members=members,
                evidence=evidence,
                provider=provider,
                model=model,
                runs_per_persona=runs_per_persona,
            )
        else:
            runner_kwargs = {
                "project_root": self.project_root,
                "team_file": self.team_file,
                "task_instructions": task_instructions,
                "input_text": input_text,
                "output_dir": agent_output_root / "raw_team_runs",
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
                        stage="evidence_interpretation",
                        detail=(
                            f"{result.agent_id} · run {result.run_index}"
                        ),
                    )
                )
            raw_results = self._team_runner(**runner_kwargs)
            semantic_results = self._materialize_live_results(
                team=team,
                members=members,
                evidence=evidence,
                expected_ids=expected_ids,
                raw_results=tuple(raw_results),
                provider=provider,
                model=model,
                api_key=api_key,
                classification_alignment_output_root=(
                    classification_alignment_output_root
                ),
                semantic_consistency_output_root=(
                    semantic_consistency_output_root
                ),
                llm_progress_observer=llm_progress_observer,
                runs_per_persona=runs_per_persona,
            )

        for result in semantic_results:
            path = (
                agent_output_root
                / "semantic_extraction"
                / result.agent_id.lower()
                / f"run_{result.persona_run_index:02d}.json"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                semantic_extraction_agent_result_to_json(result),
                encoding="utf-8",
            )

        required_personas = tuple(
            sorted(member.persona_id for member in members)
        )
        expectations = {
            persona_id: runs_per_persona
            for persona_id in required_personas
        }
        consensus = analyze_semantic_consensus(
            agent_results=semantic_results,
            required_personas=required_personas,
            expected_runs_per_persona=expectations,
            source_projection=projection,
            supporting_information_units=(),
            consensus_report_id=SEMANTIC_CONSENSUS_REPORT_ID,
            timestamp=self._timestamp(),
        )

        consensus_path = (
            consensus_output_root
            / "shared_evidence_semantic_consensus.json"
        )
        consensus_path.write_text(
            semantic_consensus_result_to_json(consensus),
            encoding="utf-8",
        )

        summary = _build_binding_summary(
            evidence=evidence,
            consensus=consensus,
        )
        binding_summary_path = (
            consensus_output_root
            / "shared_evidence_binding_summary.json"
        )
        binding_summary_path.write_text(
            json.dumps(
                summary,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        return SharedEvidenceInterpretationResult(
            project_id=projection.manifest.project_id,
            source_id=projection.manifest.source_id,
            source_projection_id=(
                projection.manifest.source_projection_id
            ),
            team_id=team.team_id,
            source_evidence_ids=expected_ids,
            required_personas=required_personas,
            runs_per_persona=runs_per_persona,
            agent_results=semantic_results,
            consensus_result=consensus,
            binding_summary_path=binding_summary_path,
            consensus_result_path=consensus_path,
        )

    def _materialize_live_results(
        self,
        *,
        team: AgentTeamConfig,
        members: tuple[TeamMemberConfig, ...],
        evidence: tuple[SourceEvidence, ...],
        expected_ids: tuple[str, ...],
        raw_results: tuple[Any, ...],
        provider: str,
        model: str,
        api_key: str | None,
        classification_alignment_output_root: Path,
        semantic_consistency_output_root: Path,
        llm_progress_observer: LLMRequestProgressObserver | None,
        runs_per_persona: int,
    ):
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
        if actual_keys != expected_keys or len(raw_results) != len(expected_keys):
            raise EvidenceInterpretationIntegrityError(
                "Team runner results do not match configured persona/run set."
            )

        results = []
        for raw_result in raw_results:
            member = member_by_agent.get(raw_result.agent_id)
            if member is None:
                raise EvidenceInterpretationIntegrityError(
                    "Team runner returned an unexpected agent."
                )

            alignment = self._classification_alignment.align_output(
                raw_result.output_text,
                item_id_field="source_evidence_id",
                allowed_item_ids=expected_ids,
                context_by_item_id={
                    item.source_evidence_id: item.source_excerpt
                    for item in evidence
                },
                provider=provider,
                model=model,
                api_key=api_key,
                llm_progress_observer=llm_progress_observer,
            )
            if alignment.decisions:
                alignment_path = (
                    classification_alignment_output_root
                    / raw_result.agent_id.lower()
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
                    item_id_field="source_evidence_id",
                    allowed_item_ids=expected_ids,
                    context_by_item_id={
                        item.source_evidence_id: item.source_excerpt
                        for item in evidence
                    },
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    llm_progress_observer=llm_progress_observer,
                )
            )
            if semantic_consistency.decisions:
                consistency_path = (
                    semantic_consistency_output_root
                    / raw_result.agent_id.lower()
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

            interpretations = parse_evidence_interpretation_output(
                semantic_consistency.normalized_output_text,
                expected_source_evidence_ids=expected_ids,
            )
            candidates = materialize_information_unit_candidates(
                evidence=evidence,
                interpretations=interpretations,
            )
            results.append(
                create_semantic_extraction_agent_result(
                    project_id=evidence[0].project_id,
                    source_id=evidence[0].source_id,
                    source_projection_id=evidence[0].source_projection_id,
                    team_id=team.team_id,
                    agent_id=member.agent_id,
                    persona_id=member.persona_id,
                    persona_run_index=raw_result.run_index,
                    persona_configuration_fingerprint=(
                        _persona_configuration_fingerprint(
                            team=team,
                            member=member,
                        )
                    ),
                    llm_provider=provider,
                    llm_model=model,
                    prompt_schema_version=(
                        EVIDENCE_INTERPRETATION_PROMPT_SCHEMA_VERSION
                    ),
                    candidates=candidates,
                    no_candidate_rationale=None,
                    timestamp=self._timestamp(),
                )
            )

        return tuple(
            sorted(
                results,
                key=lambda result: (
                    result.persona_id,
                    result.persona_run_index,
                ),
            )
        )

    def _dry_run_results(
        self,
        *,
        team: AgentTeamConfig,
        members: tuple[TeamMemberConfig, ...],
        evidence: tuple[SourceEvidence, ...],
        provider: str,
        model: str,
        runs_per_persona: int,
    ):
        results = []

        for member in members:
            for run_index in range(1, runs_per_persona + 1):
                interpretations = tuple(
                    EvidenceInterpretationValue(
                        source_evidence_id=item.source_evidence_id,
                        interpreted_statement=item.source_excerpt,
                        information_type="unclassified",
                        statement_modality="descriptive",
                        epistemic_class="explicit",
                        missing_evidence=None,
                        extraction_rationale=(
                            "Deterministic dry-run source-preserving "
                            "interpretation; no LLM call was made."
                        ),
                        uncertainties=(),
                    )
                    for item in evidence
                )
                candidates = materialize_information_unit_candidates(
                    evidence=evidence,
                    interpretations=interpretations,
                )
                results.append(
                    create_semantic_extraction_agent_result(
                        project_id=evidence[0].project_id,
                        source_id=evidence[0].source_id,
                        source_projection_id=(
                            evidence[0].source_projection_id
                        ),
                        team_id=team.team_id,
                        agent_id=member.agent_id,
                        persona_id=member.persona_id,
                        persona_run_index=run_index,
                        persona_configuration_fingerprint=(
                            _persona_configuration_fingerprint(
                                team=team,
                                member=member,
                            )
                        ),
                        llm_provider=provider,
                        llm_model=model,
                        prompt_schema_version=(
                            EVIDENCE_INTERPRETATION_PROMPT_SCHEMA_VERSION
                        ),
                        candidates=candidates,
                        no_candidate_rationale=None,
                        timestamp=self._timestamp(),
                    )
                )

        return tuple(
            sorted(
                results,
                key=lambda result: (
                    result.persona_id,
                    result.persona_run_index,
                ),
            )
        )

    def _timestamp(self) -> str:
        value = self._clock()
        if not isinstance(value, datetime):
            raise EvidenceInterpretationConfigurationError(
                "clock must return datetime."
            )
        if value.tzinfo is None or value.utcoffset() is None:
            raise EvidenceInterpretationConfigurationError(
                "clock must return timezone-aware datetime."
            )
        return (
            value.astimezone(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )


def _persona_configuration_fingerprint(
    *,
    team: AgentTeamConfig,
    member: TeamMemberConfig,
) -> str:
    payload = {
        "team_id": team.team_id,
        "role_id": team.role_id,
        "role_text": team.role_file.read_text(encoding="utf-8"),
        "member_id": member.member_id,
        "agent_id": member.agent_id,
        "persona_id": member.persona_id,
        "perspective": member.perspective,
        "persona_text": member.persona_file.read_text(encoding="utf-8"),
        "prompt_schema_version": (
            EVIDENCE_INTERPRETATION_PROMPT_SCHEMA_VERSION
        ),
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_projection(
    value: SourceProjectionArtifact,
) -> SourceProjectionArtifact:
    if not isinstance(value, SourceProjectionArtifact):
        raise EvidenceInterpretationConfigurationError(
            "source_projection must be a SourceProjectionArtifact."
        )
    if value.manifest.projection_result == "unavailable":
        raise EvidenceInterpretationConfigurationError(
            "Unavailable Source Projection cannot be interpreted."
        )
    return value


def _validated_and_sorted_evidence(
    values: tuple[SourceEvidence, ...],
    *,
    projection: SourceProjectionArtifact,
) -> tuple[SourceEvidence, ...]:
    if not isinstance(values, tuple):
        raise EvidenceInterpretationConfigurationError(
            "source_evidence must be a tuple."
        )

    seen_ids: set[str] = set()
    seen_fingerprints: set[str] = set()
    result = []

    for item in values:
        if not isinstance(item, SourceEvidence):
            raise EvidenceInterpretationConfigurationError(
                "source_evidence entries must be SourceEvidence objects."
            )
        if (
            item.project_id != projection.manifest.project_id
            or item.source_id != projection.manifest.source_id
            or item.source_projection_id
            != projection.manifest.source_projection_id
            or item.source_projection_fingerprint
            != projection.manifest.projection_fingerprint
        ):
            raise EvidenceInterpretationIntegrityError(
                "Source Evidence does not bind the supplied Source Projection."
            )
        if item.source_evidence_id in seen_ids:
            raise EvidenceInterpretationIntegrityError(
                "Source Evidence IDs must be unique."
            )
        if item.content_fingerprint in seen_fingerprints:
            raise EvidenceInterpretationIntegrityError(
                "Source Evidence content fingerprints must be unique."
            )
        seen_ids.add(item.source_evidence_id)
        seen_fingerprints.add(item.content_fingerprint)
        result.append(item)

    return tuple(sorted(result, key=_evidence_sort_key))


def _evidence_sort_key(item: SourceEvidence):
    first = item.source_anchors[0]
    return (
        segment_id_sequence(first.segment_id),
        first.start_offset,
        first.end_offset,
        item.source_evidence_id,
    )


def _build_binding_summary(
    *,
    evidence: tuple[SourceEvidence, ...],
    consensus,
) -> dict[str, Any]:
    outcome_by_key = {
        (
            tuple(
                (
                    anchor.segment_id,
                    anchor.start_offset,
                    anchor.end_offset,
                )
                for anchor in outcome.source_anchors
            ),
            outcome.source_excerpt,
        ): outcome
        for outcome in consensus.outcomes
    }

    bindings = []
    for item in evidence:
        key = (
            tuple(
                (
                    anchor.segment_id,
                    anchor.start_offset,
                    anchor.end_offset,
                )
                for anchor in item.source_anchors
            ),
            item.source_excerpt,
        )
        outcome = outcome_by_key.get(key)
        if outcome is None:
            raise EvidenceInterpretationIntegrityError(
                "Semantic consensus did not preserve one required "
                f"Evidence subject: {item.source_evidence_id}."
            )
        bindings.append(
            {
                "source_evidence_id": item.source_evidence_id,
                "source_evidence_content_fingerprint": (
                    item.content_fingerprint
                ),
                "consensus_candidate_id": (
                    outcome.consensus_candidate_id
                ),
            }
        )

    if len(bindings) != len(consensus.outcomes):
        raise EvidenceInterpretationIntegrityError(
            "Consensus outcome cardinality differs from fixed Evidence "
            "cardinality."
        )

    return {
        "schema_version": BINDING_SUMMARY_SCHEMA_VERSION,
        "project_id": evidence[0].project_id,
        "source_id": evidence[0].source_id,
        "source_projection_id": evidence[0].source_projection_id,
        "team_id": consensus.team_id,
        "consensus_report_id": consensus.consensus_report_id,
        "bindings": bindings,
    }
