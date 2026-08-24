"""Structured, token-conscious LLM target-projection contract for Phase H9."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .errors import ModelCandidateDerivationError
from .structure_profile import model_structure_profile_reference
from .types import (
    ModelCandidateDerivationRequest,
    ModelCandidateProjectionCoverage,
    ModelCandidateProjectionDisposition,
    ModelStructureProfile,
)


LLM_PROJECTION_RESULTS = frozenset(
    {"proposed_mapping", "ambiguous", "unmapped"}
)

DEFAULT_LLM_PROJECTION_BATCH_SIZE = 8
MAX_LLM_PROJECTION_BATCH_SIZE = 16

LLM_PROJECTION_TASK_INSTRUCTIONS = """Return only one JSON object. Do not use Markdown fences.

Required shape:
{"proposals":[{"approved_input_id":"AIN-000001","result":"proposed_mapping|ambiguous|unmapped","selected_rule_id":"RULE_ID or null","alternative_rule_ids":[],"rationale":"concise rationale"}]}

Rules:
- Return exactly one proposal for every input item and no extra proposals.
- Use only rule IDs listed in that item's allowed_target_options.
- proposed_mapping: select exactly one allowed rule; alternatives must be empty.
- ambiguous: selected_rule_id must be null; provide at least two allowed alternatives.
- unmapped: selected_rule_id must be null; alternatives must be empty.
- Prefer unmapped over forcing engineering information into an unsuitable target type.
- `review_escalation=true` means Human Model Review rejected a prior Candidate;
  reconsider the mapping using only the supplied target options.
- A prior deterministic mapping is not authoritative during explicit review escalation.
- Do not approve anything.
- Do not generate SysML v2 code.
- Do not expose chain-of-thought; provide only a short rationale.
""".strip()


@dataclass(frozen=True, slots=True)
class LLMProjectionTargetOption:
    rule_id: str
    target_kind: str
    model_area: str | None
    element_type: str | None
    framework_assignment: str | None
    relationship_family: str | None
    semantic_intent: str | None
    directionality: str | None


@dataclass(frozen=True, slots=True)
class LLMProjectionInputItem:
    approved_input_id: str
    approved_input_kind: str
    stable_subject_key: str
    title: str
    primary_text: str
    description: str | None
    information_type: str | None
    reviewed_classification: str | None
    reviewed_framework_assignment: str | None
    deterministic_disposition: str
    deterministic_reason_code: str
    deterministic_candidate_rule_ids: tuple[str, ...]
    review_escalation: bool
    allowed_target_options: tuple[LLMProjectionTargetOption, ...]


@dataclass(frozen=True, slots=True)
class LLMProjectionRequest:
    project_id: str
    profile_id: str
    profile_version: str
    profile_fingerprint: str
    items: tuple[LLMProjectionInputItem, ...]
    request_fingerprint: str


@dataclass(frozen=True, slots=True)
class LLMProjectionProposal:
    approved_input_id: str
    result: str
    selected_rule_id: str | None
    alternative_rule_ids: tuple[str, ...]
    rationale: str


@dataclass(frozen=True, slots=True)
class LLMProjectionResponse:
    request_fingerprint: str
    proposals: tuple[LLMProjectionProposal, ...]
    response_fingerprint: str


def build_llm_projection_request(
    *,
    request: ModelCandidateDerivationRequest,
    coverage: ModelCandidateProjectionCoverage,
    profile: ModelStructureProfile,
    approved_input_ids: tuple[str, ...] | None = None,
    explicit_escalation_approved_input_ids: tuple[str, ...] = (),
    max_batch_size: int = DEFAULT_LLM_PROJECTION_BATCH_SIZE,
) -> LLMProjectionRequest:
    _validate_profile_binding(request, coverage, profile)
    _validate_batch_size(max_batch_size)

    escalation_ids = _validate_explicit_escalation_ids(
        request=request,
        coverage=coverage,
        values=explicit_escalation_approved_input_ids,
    )
    eligible_ids = tuple(
        sorted(
            set(coverage.unresolved_approved_input_ids)
            | set(escalation_ids)
        )
    )
    selected_ids = (
        eligible_ids
        if approved_input_ids is None
        else approved_input_ids
    )

    if not isinstance(selected_ids, tuple):
        raise ModelCandidateDerivationError(
            "LLM projection approved_input_ids must be a tuple."
        )
    if not selected_ids:
        raise ModelCandidateDerivationError(
            "LLM projection request requires at least one eligible input."
        )
    if len(selected_ids) > max_batch_size:
        raise ModelCandidateDerivationError(
            "LLM projection request exceeds configured batch size."
        )
    if len(selected_ids) != len(set(selected_ids)):
        raise ModelCandidateDerivationError(
            "LLM projection request contains duplicate Approved Input IDs."
        )

    outside = set(selected_ids) - set(eligible_ids)
    if outside:
        raise ModelCandidateDerivationError(
            "LLM projection request may contain only ambiguous/unmapped "
            "Approved Inputs or explicit Human-review escalation targets: "
            f"{sorted(outside)}."
        )

    input_by_id = {
        item.approved_input_id: item
        for item in request.approved_inputs
    }
    coverage_by_id = {
        item.approved_input_id: item
        for item in coverage.entries
    }

    items = tuple(
        _build_input_item(
            approved_input=input_by_id[approved_input_id],
            disposition=coverage_by_id[approved_input_id],
            profile=profile,
            review_escalation=(
                approved_input_id in set(escalation_ids)
            ),
        )
        for approved_input_id in sorted(selected_ids)
    )

    payload = {
        "project_id": request.project_id,
        "profile": {
            "id": profile.profile_id,
            "version": profile.profile_version,
            "fingerprint": profile.profile_fingerprint,
        },
        "items": [_input_item_to_dict(item) for item in items],
    }

    return LLMProjectionRequest(
        project_id=request.project_id,
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_fingerprint=profile.profile_fingerprint,
        items=items,
        request_fingerprint=_fingerprint(payload),
    )


def llm_projection_request_to_compact_json(
    request: LLMProjectionRequest,
) -> str:
    payload = {
        "project_id": request.project_id,
        "profile": {
            "id": request.profile_id,
            "version": request.profile_version,
        },
        "items": [_input_item_to_dict(item) for item in request.items],
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def parse_llm_projection_response(
    *,
    request: LLMProjectionRequest,
    output_text: str,
) -> LLMProjectionResponse:
    if not isinstance(output_text, str) or not output_text.strip():
        raise ModelCandidateDerivationError(
            "LLM projection response must be non-empty JSON text."
        )
    try:
        payload = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise ModelCandidateDerivationError(
            "LLM projection response is not valid JSON."
        ) from exc

    if not isinstance(payload, dict) or set(payload) != {"proposals"}:
        raise ModelCandidateDerivationError(
            "LLM projection response must contain exactly 'proposals'."
        )
    raw_proposals = payload["proposals"]
    if not isinstance(raw_proposals, list):
        raise ModelCandidateDerivationError(
            "LLM projection proposals must be a JSON array."
        )

    requested_by_id = {item.approved_input_id: item for item in request.items}
    requested_ids = tuple(sorted(requested_by_id))

    proposals = tuple(
        _parse_proposal(raw, requested_by_id=requested_by_id)
        for raw in raw_proposals
    )
    proposal_ids = tuple(item.approved_input_id for item in proposals)

    if len(proposal_ids) != len(set(proposal_ids)):
        raise ModelCandidateDerivationError(
            "LLM projection response contains duplicate Approved Input IDs."
        )
    if tuple(sorted(proposal_ids)) != requested_ids:
        raise ModelCandidateDerivationError(
            "LLM projection response must cover every requested input exactly "
            "once and may not contain extra inputs."
        )

    proposals = tuple(sorted(proposals, key=lambda item: item.approved_input_id))
    response_payload = {
        "request_fingerprint": request.request_fingerprint,
        "proposals": [_proposal_to_dict(item) for item in proposals],
    }
    return LLMProjectionResponse(
        request_fingerprint=request.request_fingerprint,
        proposals=proposals,
        response_fingerprint=_fingerprint(response_payload),
    )


def _build_input_item(
    *,
    approved_input,
    disposition,
    profile,
    review_escalation,
):
    if (
        disposition.disposition not in {"ambiguous", "unmapped"}
        and not (
            review_escalation
            and disposition.disposition == "mapped"
        )
    ):
        raise ModelCandidateDerivationError(
            "Only ambiguous/unmapped inputs or explicit mapped "
            "review-escalation targets may enter the LLM contract."
        )

    options = _allowed_target_options(
        approved_input_kind=approved_input.approved_input_kind,
        disposition=disposition,
        profile=profile,
        review_escalation=review_escalation,
    )
    if not options:
        raise ModelCandidateDerivationError(
            "LLM projection requires at least one profile-controlled target "
            f"option for {approved_input.approved_input_id}."
        )

    content = approved_input.canonical_content
    return LLMProjectionInputItem(
        approved_input_id=approved_input.approved_input_id,
        approved_input_kind=approved_input.approved_input_kind,
        stable_subject_key=approved_input.stable_subject_key,
        title=content.title,
        primary_text=content.primary_text,
        description=content.description,
        information_type=content.information_type,
        reviewed_classification=approved_input.selected_classification,
        reviewed_framework_assignment=approved_input.selected_framework_assignment,
        deterministic_disposition=disposition.disposition,
        deterministic_reason_code=disposition.reason_code,
        deterministic_candidate_rule_ids=tuple(
            sorted(
                set(disposition.candidate_rule_ids)
                | (
                    {disposition.selected_rule_id}
                    if (
                        review_escalation
                        and disposition.selected_rule_id is not None
                    )
                    else set()
                )
            )
        ),
        review_escalation=review_escalation,
        allowed_target_options=options,
    )


def _allowed_target_options(
    *,
    approved_input_kind,
    disposition,
    profile,
    review_escalation,
):
    if approved_input_kind == "element_statement":
        areas = {item.model_area_id: item for item in profile.model_areas}
        all_rules = {
            item.rule_id: item for item in profile.element_derivation_rules
        }
        rule_ids = (
            tuple(sorted(all_rules))
            if review_escalation
            else (
                disposition.candidate_rule_ids
                if disposition.disposition == "ambiguous"
                and disposition.candidate_rule_ids
                else tuple(sorted(all_rules))
            )
        )
        options = []
        for rule_id in rule_ids:
            rule = all_rules.get(rule_id)
            if rule is None:
                raise ModelCandidateDerivationError(
                    "Deterministic candidate rule is outside the selected "
                    f"profile: {rule_id}."
                )
            area = areas[rule.model_area_id]
            options.append(
                LLMProjectionTargetOption(
                    rule_id=rule.rule_id,
                    target_kind="element",
                    model_area=rule.model_area_id,
                    element_type=rule.element_type,
                    framework_assignment=area.framework_node_id,
                    relationship_family=None,
                    semantic_intent=None,
                    directionality=None,
                )
            )
        return tuple(sorted(options, key=lambda item: item.rule_id))

    if approved_input_kind == "relationship_statement":
        return tuple(
            sorted(
                (
                    LLMProjectionTargetOption(
                        rule_id=f"relationship:{rule.semantic_intent}",
                        target_kind="relationship",
                        model_area=None,
                        element_type=None,
                        framework_assignment=None,
                        relationship_family=rule.relationship_family,
                        semantic_intent=rule.semantic_intent,
                        directionality=rule.directionality,
                    )
                    for rule in profile.relationship_semantics
                ),
                key=lambda item: item.rule_id,
            )
        )

    raise ModelCandidateDerivationError(
        "LLM target projection supports only element_statement and "
        "relationship_statement Approved Inputs."
    )


def _parse_proposal(raw, *, requested_by_id):
    expected_keys = {
        "approved_input_id",
        "result",
        "selected_rule_id",
        "alternative_rule_ids",
        "rationale",
    }
    if not isinstance(raw, dict) or set(raw) != expected_keys:
        raise ModelCandidateDerivationError(
            "Each LLM projection proposal must use the exact response schema."
        )

    approved_input_id = raw["approved_input_id"]
    if approved_input_id not in requested_by_id:
        raise ModelCandidateDerivationError(
            "LLM projection response references an input that was not requested."
        )

    result = raw["result"]
    if result not in LLM_PROJECTION_RESULTS:
        raise ModelCandidateDerivationError(
            f"Unsupported LLM projection result: {result!r}."
        )

    selected_rule_id = raw["selected_rule_id"]
    if selected_rule_id is not None and (
        not isinstance(selected_rule_id, str)
        or not selected_rule_id.strip()
        or selected_rule_id != selected_rule_id.strip()
    ):
        raise ModelCandidateDerivationError(
            "selected_rule_id must be null or a non-empty trimmed string."
        )

    raw_alternatives = raw["alternative_rule_ids"]
    if (
        not isinstance(raw_alternatives, list)
        or not all(
            isinstance(item, str)
            and item.strip()
            and item == item.strip()
            for item in raw_alternatives
        )
    ):
        raise ModelCandidateDerivationError(
            "alternative_rule_ids must be a JSON array of trimmed strings."
        )
    alternative_rule_ids = tuple(raw_alternatives)
    if len(alternative_rule_ids) != len(set(alternative_rule_ids)):
        raise ModelCandidateDerivationError(
            "alternative_rule_ids must be unique."
        )

    rationale = raw["rationale"]
    if (
        not isinstance(rationale, str)
        or not rationale.strip()
        or rationale != rationale.strip()
        or len(rationale) > 800
    ):
        raise ModelCandidateDerivationError(
            "LLM projection rationale must be a trimmed non-empty string "
            "of at most 800 characters."
        )

    allowed = {
        item.rule_id
        for item in requested_by_id[approved_input_id].allowed_target_options
    }
    referenced = set(alternative_rule_ids)
    if selected_rule_id is not None:
        referenced.add(selected_rule_id)
    outside = referenced - allowed
    if outside:
        raise ModelCandidateDerivationError(
            "LLM projection proposal references target rules not offered "
            f"to the model: {sorted(outside)}."
        )

    if result == "proposed_mapping":
        if selected_rule_id is None or alternative_rule_ids:
            raise ModelCandidateDerivationError(
                "proposed_mapping requires exactly one selected_rule_id and "
                "no alternatives."
            )
    elif result == "ambiguous":
        if selected_rule_id is not None or len(alternative_rule_ids) < 2:
            raise ModelCandidateDerivationError(
                "ambiguous requires null selected_rule_id and at least two "
                "allowed alternative_rule_ids."
            )
    else:
        if selected_rule_id is not None or alternative_rule_ids:
            raise ModelCandidateDerivationError(
                "unmapped requires null selected_rule_id and no alternatives."
            )

    return LLMProjectionProposal(
        approved_input_id=approved_input_id,
        result=result,
        selected_rule_id=selected_rule_id,
        alternative_rule_ids=tuple(sorted(alternative_rule_ids)),
        rationale=rationale,
    )


def _validate_profile_binding(request, coverage, profile):
    expected = model_structure_profile_reference(profile)
    if request.model_structure_profile_reference != expected:
        raise ModelCandidateDerivationError(
            "LLM projection request profile does not match derivation request."
        )
    if coverage.model_structure_profile_reference != expected:
        raise ModelCandidateDerivationError(
            "LLM projection coverage profile does not match selected profile."
        )
    if coverage.project_id != request.project_id:
        raise ModelCandidateDerivationError(
            "LLM projection coverage belongs to another project."
        )

    request_ids = {item.approved_input_id for item in request.approved_inputs}
    coverage_ids = {item.approved_input_id for item in coverage.entries}
    if request_ids != coverage_ids:
        raise ModelCandidateDerivationError(
            "LLM projection coverage must correspond to the complete "
            "derivation request snapshot."
        )


def _validate_explicit_escalation_ids(
    *,
    request,
    coverage,
    values,
):
    if not isinstance(values, tuple):
        raise ModelCandidateDerivationError(
            "explicit_escalation_approved_input_ids must be a tuple."
        )
    if len(values) != len(set(values)):
        raise ModelCandidateDerivationError(
            "explicit_escalation_approved_input_ids must be unique."
        )

    request_ids = {
        item.approved_input_id
        for item in request.approved_inputs
    }
    coverage_by_id = {
        item.approved_input_id: item
        for item in coverage.entries
    }

    outside = set(values) - request_ids
    if outside:
        raise ModelCandidateDerivationError(
            "Explicit review escalation references Approved Inputs "
            f"outside the derivation snapshot: {sorted(outside)}."
        )

    invalid = tuple(
        sorted(
            value
            for value in values
            if coverage_by_id[value].disposition != "mapped"
        )
    )
    if invalid:
        raise ModelCandidateDerivationError(
            "Explicit review escalation may add only deterministically "
            f"mapped Approved Inputs: {list(invalid)}."
        )

    return tuple(sorted(values))


def _validate_batch_size(value):
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 1
        or value > MAX_LLM_PROJECTION_BATCH_SIZE
    ):
        raise ModelCandidateDerivationError(
            "LLM projection batch size must be between 1 and "
            f"{MAX_LLM_PROJECTION_BATCH_SIZE}."
        )


def _input_item_to_dict(item):
    return {
        "approved_input_id": item.approved_input_id,
        "kind": item.approved_input_kind,
        "subject": item.stable_subject_key,
        "title": item.title,
        "text": item.primary_text,
        "description": item.description,
        "information_type": item.information_type,
        "classification": item.reviewed_classification,
        "framework": item.reviewed_framework_assignment,
        "deterministic": {
            "disposition": item.deterministic_disposition,
            "reason": item.deterministic_reason_code,
            "candidate_rule_ids": list(item.deterministic_candidate_rule_ids),
        },
        "review_escalation": item.review_escalation,
        "allowed_target_options": [
            _target_option_to_dict(option)
            for option in item.allowed_target_options
        ],
    }


def _target_option_to_dict(option):
    if option.target_kind == "element":
        return {
            "rule_id": option.rule_id,
            "kind": "element",
            "area": option.model_area,
            "type": option.element_type,
            "framework_node": option.framework_assignment,
        }
    return {
        "rule_id": option.rule_id,
        "kind": "relationship",
        "family": option.relationship_family,
        "intent": option.semantic_intent,
        "direction": option.directionality,
    }


def _proposal_to_dict(proposal):
    return {
        "approved_input_id": proposal.approved_input_id,
        "result": proposal.result,
        "selected_rule_id": proposal.selected_rule_id,
        "alternative_rule_ids": list(proposal.alternative_rule_ids),
        "rationale": proposal.rationale,
    }


def _fingerprint(payload):
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
