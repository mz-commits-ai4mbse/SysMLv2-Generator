"""Strict three-persona projection for accepted semantic Relationships."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from modules.agents.team_config import load_team_config
from modules.agents.team_runner import run_agent_team, select_team_members

from .errors import ModelCandidateDerivationError
from .types import (
    ModelCandidateDerivationRequest,
    ModelCandidateProjectionDisposition,
    ModelStructureProfile,
)

DEFAULT_SEMANTIC_RELATIONSHIP_BATCH_SIZE = 8
MAX_SEMANTIC_RELATIONSHIP_BATCH_SIZE = 16
DEFAULT_MAX_SEMANTIC_RELATIONSHIP_BATCHES = 4
DEFAULT_MODELING_PROJECTION_TEAM_FILE = Path(
    "teams/modeling/modeling_projection_team.json"
)

SEMANTIC_RELATIONSHIP_TASK_INSTRUCTIONS = """Return only one JSON object. Do not use Markdown fences.

Required shape:
{"proposals":[{"relationship_decision_id":"SRD-000001","result":"proposed_mapping|ambiguous|unmapped","selected_rule_id":"relationship:semantic or null","alternative_rule_ids":[],"rationale":"concise rationale"}]}

Rules:
- Return exactly one proposal for every requested accepted Relationship and no extras.
- The Human-reviewed relationship_kind is engineering meaning, not a target-model construct.
- Use only rule IDs listed in allowed_target_options.
- proposed_mapping: exactly one selected rule and no alternatives.
- ambiguous: null selected rule and at least two allowed alternatives.
- unmapped: null selected rule and no alternatives.
- Prefer unmapped over forcing an unsuitable target Relationship.
- Preserve source and target direction; do not swap endpoints.
- Do not approve, reject, add or remove engineering Relationships.
- Do not generate SysML v2 code.
- Do not expose chain-of-thought; provide only a short rationale.
""".strip()


@dataclass(frozen=True, slots=True)
class SemanticRelationshipProjectionItem:
    relationship_decision_id: str
    source_subject_id: str
    source_title: str
    source_statement: str
    relationship_kind: str
    target_subject_id: str
    target_title: str
    target_statement: str
    human_rationale: str | None
    allowed_target_options: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SemanticRelationshipProjectionRequest:
    project_id: str
    approved_engineering_information_fingerprint: str
    profile_id: str
    profile_version: str
    profile_fingerprint: str
    items: tuple[SemanticRelationshipProjectionItem, ...]
    request_fingerprint: str


@dataclass(frozen=True, slots=True)
class SemanticRelationshipProjectionProposal:
    relationship_decision_id: str
    result: str
    selected_rule_id: str | None
    alternative_rule_ids: tuple[str, ...]
    rationale: str


@dataclass(frozen=True, slots=True)
class SemanticRelationshipProjectionResponse:
    request_fingerprint: str
    proposals: tuple[SemanticRelationshipProjectionProposal, ...]
    response_fingerprint: str


@dataclass(frozen=True, slots=True)
class SemanticRelationshipProjectionInvocation:
    request: SemanticRelationshipProjectionRequest
    response: SemanticRelationshipProjectionResponse
    provider: str
    model: str
    output_path: Path
    supporting_response_fingerprints: tuple[str, ...]
    supporting_agent_ids: tuple[str, ...]


class SemanticRelationshipProjectionExecutor:
    """Run the same bounded Relationship projection request across 3 personas."""

    def __init__(
        self,
        *,
        project_root: Path,
        provider: str,
        model: str,
        api_key: str | None = None,
        batch_size: int = DEFAULT_SEMANTIC_RELATIONSHIP_BATCH_SIZE,
        max_batches_per_run: int = DEFAULT_MAX_SEMANTIC_RELATIONSHIP_BATCHES,
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
            or not 1 <= batch_size <= MAX_SEMANTIC_RELATIONSHIP_BATCH_SIZE
        ):
            raise ModelCandidateDerivationError(
                "Semantic Relationship batch_size is invalid."
            )
        if (
            not isinstance(max_batches_per_run, int)
            or isinstance(max_batches_per_run, bool)
            or max_batches_per_run < 1
        ):
            raise ModelCandidateDerivationError(
                "Semantic Relationship max_batches_per_run is invalid."
            )
        self.project_root = project_root
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.batch_size = batch_size
        self.max_batches_per_run = max_batches_per_run
        self.team_file = team_file
        self._team_runner = team_runner

    def execute_semantic_relationships(
        self,
        *,
        request: ModelCandidateDerivationRequest,
        relationship_entries: tuple[ModelCandidateProjectionDisposition, ...],
        profile: ModelStructureProfile,
        output_dir: Path,
    ) -> tuple[SemanticRelationshipProjectionInvocation, ...]:
        authority = request.approved_engineering_information
        if authority is None:
            raise ModelCandidateDerivationError(
                "Semantic Relationship projection requires Approved "
                "Engineering Information."
            )
        ids = tuple(sorted(item.approved_input_id for item in relationship_entries))
        if not ids:
            return ()
        batches = tuple(
            ids[index:index + self.batch_size]
            for index in range(0, len(ids), self.batch_size)
        )
        if len(batches) > self.max_batches_per_run:
            raise ModelCandidateDerivationError(
                "Semantic Relationship projection would exceed "
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
                "Semantic Relationship projection requires exactly three "
                "configured modeling personas."
            )
        expected_agent_ids = tuple(sorted(member.agent_id for member in members))

        invocations = []
        for index, relationship_ids in enumerate(batches, start=1):
            projection_request = build_semantic_relationship_request(
                request=request,
                relationship_entries=relationship_entries,
                profile=profile,
                relationship_decision_ids=relationship_ids,
            )
            batch_root = output_dir / f"batch_{index:02d}"
            raw_root = batch_root / "persona_outputs"
            raw_results = tuple(
                self._team_runner(
                    project_root=self.project_root,
                    team_file=self.team_file,
                    task_instructions=SEMANTIC_RELATIONSHIP_TASK_INSTRUCTIONS,
                    input_text=semantic_relationship_request_to_json(
                        projection_request
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
            actual_agent_ids = tuple(sorted(item.agent_id for item in raw_results))
            if (
                actual_agent_ids != expected_agent_ids
                or len(raw_results) != len(expected_agent_ids)
                or any(item.run_index != 1 for item in raw_results)
            ):
                raise ModelCandidateDerivationError(
                    "Semantic Relationship modeling team results do not match "
                    "the configured three-persona contract."
                )

            parsed = tuple(
                sorted(
                    (
                        (
                            result.agent_id,
                            parse_semantic_relationship_response(
                                request=projection_request,
                                output_text=result.output_text,
                            ),
                        )
                        for result in raw_results
                    ),
                    key=lambda item: item[0],
                )
            )
            consolidated = consolidate_semantic_relationship_responses(
                request=projection_request,
                persona_responses=parsed,
            )

            batch_root.mkdir(parents=True, exist_ok=True)
            summary_path = batch_root / "semantic_relationship_consolidated.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "request_fingerprint": projection_request.request_fingerprint,
                        "approved_engineering_information_fingerprint": (
                            authority.content_fingerprint
                        ),
                        "persona_responses": [
                            {
                                "agent_id": agent_id,
                                "response_fingerprint": response.response_fingerprint,
                            }
                            for agent_id, response in parsed
                        ],
                        "consolidated_response_fingerprint": (
                            consolidated.response_fingerprint
                        ),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            invocations.append(
                SemanticRelationshipProjectionInvocation(
                    request=projection_request,
                    response=consolidated,
                    provider=self.provider,
                    model=self.model,
                    output_path=summary_path,
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


def build_semantic_relationship_request(
    *,
    request: ModelCandidateDerivationRequest,
    relationship_entries: tuple[ModelCandidateProjectionDisposition, ...],
    profile: ModelStructureProfile,
    relationship_decision_ids: tuple[str, ...],
) -> SemanticRelationshipProjectionRequest:
    authority = request.approved_engineering_information
    if authority is None:
        raise ModelCandidateDerivationError(
            "Approved Engineering Information is required."
        )
    relation_by_id = {
        item.relationship_decision_id: item for item in authority.relationships
    }
    subject_by_id = {
        item.canonical_subject_id: item for item in authority.subjects
    }
    entry_by_id = {
        item.approved_input_id: item for item in relationship_entries
    }
    all_options = tuple(
        sorted(
            f"relationship:{item.semantic_intent}"
            for item in profile.relationship_semantics
        )
    )
    items = []
    for relationship_id in relationship_decision_ids:
        if relationship_id not in relation_by_id:
            raise ModelCandidateDerivationError(
                "Relationship projection references a decision outside AEI."
            )
        entry = entry_by_id.get(relationship_id)
        if entry is None or entry.disposition not in {"ambiguous", "unmapped"}:
            raise ModelCandidateDerivationError(
                "Relationship projection may contain only unresolved semantic "
                "Relationships."
            )
        relationship = relation_by_id[relationship_id]
        source = subject_by_id[relationship.source_subject_id]
        target = subject_by_id[relationship.target_subject_id]
        options = (
            tuple(sorted(entry.candidate_rule_ids))
            if entry.candidate_rule_ids
            else all_options
        )
        if not options:
            raise ModelCandidateDerivationError(
                "Relationship projection has no profile-controlled options."
            )
        items.append(
            SemanticRelationshipProjectionItem(
                relationship_decision_id=relationship_id,
                source_subject_id=relationship.source_subject_id,
                source_title=source.title,
                source_statement=source.engineering_statement,
                relationship_kind=relationship.relationship_kind,
                target_subject_id=relationship.target_subject_id,
                target_title=target.title,
                target_statement=target.engineering_statement,
                human_rationale=relationship.rationale,
                allowed_target_options=options,
            )
        )
    payload = {
        "project_id": request.project_id,
        "approved_engineering_information_fingerprint": (
            authority.content_fingerprint
        ),
        "profile": {
            "id": profile.profile_id,
            "version": profile.profile_version,
            "fingerprint": profile.profile_fingerprint,
        },
        "items": [_item_payload(item) for item in items],
    }
    return SemanticRelationshipProjectionRequest(
        project_id=request.project_id,
        approved_engineering_information_fingerprint=authority.content_fingerprint,
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_fingerprint=profile.profile_fingerprint,
        items=tuple(items),
        request_fingerprint=_fingerprint(payload),
    )


def semantic_relationship_request_to_json(
    request: SemanticRelationshipProjectionRequest,
) -> str:
    return json.dumps(
        {
            "project_id": request.project_id,
            "approved_engineering_information_fingerprint": (
                request.approved_engineering_information_fingerprint
            ),
            "profile": {
                "id": request.profile_id,
                "version": request.profile_version,
            },
            "items": [_item_payload(item) for item in request.items],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def parse_semantic_relationship_response(
    *,
    request: SemanticRelationshipProjectionRequest,
    output_text: str,
) -> SemanticRelationshipProjectionResponse:
    try:
        payload = json.loads(output_text)
    except Exception as exc:
        raise ModelCandidateDerivationError(
            "Semantic Relationship projection response is not valid JSON."
        ) from exc
    if (
        not isinstance(payload, dict)
        or set(payload) != {"proposals"}
        or not isinstance(payload["proposals"], list)
    ):
        raise ModelCandidateDerivationError(
            "Semantic Relationship response must contain exactly proposals."
        )
    requested = {
        item.relationship_decision_id: item for item in request.items
    }
    proposals = tuple(
        _parse_proposal(item, requested)
        for item in payload["proposals"]
    )
    ids = tuple(item.relationship_decision_id for item in proposals)
    if len(ids) != len(set(ids)) or set(ids) != set(requested):
        raise ModelCandidateDerivationError(
            "Semantic Relationship response must cover every requested "
            "Relationship exactly once."
        )
    proposals = tuple(
        sorted(proposals, key=lambda item: item.relationship_decision_id)
    )
    response_payload = {
        "request_fingerprint": request.request_fingerprint,
        "proposals": [_proposal_payload(item) for item in proposals],
    }
    return SemanticRelationshipProjectionResponse(
        request_fingerprint=request.request_fingerprint,
        proposals=proposals,
        response_fingerprint=_fingerprint(response_payload),
    )


def consolidate_semantic_relationship_responses(
    *,
    request: SemanticRelationshipProjectionRequest,
    persona_responses,
) -> SemanticRelationshipProjectionResponse:
    if len(persona_responses) < 2:
        raise ModelCandidateDerivationError(
            "Semantic Relationship consolidation requires multiple personas."
        )
    by_agent = {}
    expected = {item.relationship_decision_id for item in request.items}
    for agent_id, response in persona_responses:
        if response.request_fingerprint != request.request_fingerprint:
            raise ModelCandidateDerivationError(
                "Semantic Relationship response does not bind the exact request."
            )
        proposals = {
            item.relationship_decision_id: item
            for item in response.proposals
        }
        if set(proposals) != expected:
            raise ModelCandidateDerivationError(
                "Each persona must cover the exact Relationship batch."
            )
        by_agent[agent_id] = proposals

    consolidated = []
    for relationship_id in sorted(expected):
        values = tuple(
            by_agent[agent_id][relationship_id]
            for agent_id in sorted(by_agent)
        )
        unanimous = (
            all(item.result == "proposed_mapping" for item in values)
            and len({item.selected_rule_id for item in values}) == 1
        )
        if unanimous:
            selected = values[0].selected_rule_id
            consolidated.append(
                {
                    "relationship_decision_id": relationship_id,
                    "result": "proposed_mapping",
                    "selected_rule_id": selected,
                    "alternative_rule_ids": [],
                    "rationale": (
                        "All modeling personas independently selected the same "
                        f"profile-controlled Relationship rule {selected}."
                    ),
                }
            )
            continue
        referenced = set()
        for item in values:
            if item.selected_rule_id is not None:
                referenced.add(item.selected_rule_id)
            referenced.update(item.alternative_rule_ids)
        if len(referenced) >= 2:
            consolidated.append(
                {
                    "relationship_decision_id": relationship_id,
                    "result": "ambiguous",
                    "selected_rule_id": None,
                    "alternative_rule_ids": sorted(referenced),
                    "rationale": (
                        "Modeling personas did not converge on one target "
                        "Relationship rule."
                    ),
                }
            )
        else:
            consolidated.append(
                {
                    "relationship_decision_id": relationship_id,
                    "result": "unmapped",
                    "selected_rule_id": None,
                    "alternative_rule_ids": [],
                    "rationale": (
                        "Modeling personas did not unanimously support one "
                        "target Relationship rule."
                    ),
                }
            )
    return parse_semantic_relationship_response(
        request=request,
        output_text=json.dumps({"proposals": consolidated}),
    )


def _parse_proposal(raw, requested):
    expected_fields = {
        "relationship_decision_id",
        "result",
        "selected_rule_id",
        "alternative_rule_ids",
        "rationale",
    }
    if not isinstance(raw, dict) or set(raw) != expected_fields:
        raise ModelCandidateDerivationError(
            "Semantic Relationship proposal has invalid fields."
        )
    relationship_id = raw["relationship_decision_id"]
    if relationship_id not in requested:
        raise ModelCandidateDerivationError(
            "Semantic Relationship proposal references an unknown decision."
        )
    result = raw["result"]
    if result not in {"proposed_mapping", "ambiguous", "unmapped"}:
        raise ModelCandidateDerivationError(
            "Semantic Relationship proposal result is invalid."
        )
    selected = raw["selected_rule_id"]
    alternatives = raw["alternative_rule_ids"]
    rationale = raw["rationale"]
    if not isinstance(alternatives, list) or len(alternatives) != len(set(alternatives)):
        raise ModelCandidateDerivationError(
            "Semantic Relationship alternatives must be a unique JSON array."
        )
    if not isinstance(rationale, str) or not rationale.strip():
        raise ModelCandidateDerivationError(
            "Semantic Relationship rationale is required."
        )
    allowed = set(requested[relationship_id].allowed_target_options)
    referenced = set(alternatives)
    if selected is not None:
        referenced.add(selected)
    if referenced - allowed:
        raise ModelCandidateDerivationError(
            "Semantic Relationship proposal references a rule outside the "
            "offered Model Structure Profile."
        )
    if result == "proposed_mapping":
        if selected is None or alternatives:
            raise ModelCandidateDerivationError(
                "proposed_mapping requires exactly one selected rule."
            )
    elif result == "ambiguous":
        if selected is not None or len(alternatives) < 2:
            raise ModelCandidateDerivationError(
                "ambiguous requires at least two alternatives."
            )
    else:
        if selected is not None or alternatives:
            raise ModelCandidateDerivationError(
                "unmapped cannot select target rules."
            )
    return SemanticRelationshipProjectionProposal(
        relationship_decision_id=relationship_id,
        result=result,
        selected_rule_id=selected,
        alternative_rule_ids=tuple(sorted(alternatives)),
        rationale=rationale.strip(),
    )


def _item_payload(item):
    return {
        "relationship_decision_id": item.relationship_decision_id,
        "source": {
            "subject_id": item.source_subject_id,
            "title": item.source_title,
            "statement": item.source_statement,
        },
        "relationship_kind": item.relationship_kind,
        "target": {
            "subject_id": item.target_subject_id,
            "title": item.target_title,
            "statement": item.target_statement,
        },
        "human_rationale": item.human_rationale,
        "allowed_target_options": list(item.allowed_target_options),
    }


def _proposal_payload(item):
    return {
        "relationship_decision_id": item.relationship_decision_id,
        "result": item.result,
        "selected_rule_id": item.selected_rule_id,
        "alternative_rule_ids": list(item.alternative_rule_ids),
        "rationale": item.rationale,
    }


def _fingerprint(payload):
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
