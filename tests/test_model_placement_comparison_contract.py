import pytest

from modules.model_candidates.llm_projection_contract import (
    LLMProjectionInputItem,
    LLMProjectionProposal,
    LLMProjectionRequest,
    LLMProjectionResponse,
    LLMProjectionTargetOption,
)
from modules.model_placement import (
    ModelPlacementContractError,
    compare_model_placement_personas,
)


def _option(rule_id):
    is_system = rule_id == "ELEMENT_SYSTEM_FUNCTION"
    return LLMProjectionTargetOption(
        rule_id=rule_id,
        target_kind="element",
        model_area=(
            "system.functional"
            if is_system
            else "subsystem.functional"
        ),
        element_type="function",
        framework_assignment=(
            "FW_SYSTEM_FUNCTIONAL"
            if is_system
            else "FW_SUBSYSTEM_FUNCTIONAL"
        ),
        relationship_family=None,
        semantic_intent=None,
        directionality=None,
    )


def _request():
    options = (
        _option("ELEMENT_SYSTEM_FUNCTION"),
        _option("ELEMENT_SUBSYSTEM_FUNCTION"),
    )
    item = LLMProjectionInputItem(
        approved_input_id="AIN-000001",
        approved_input_kind="element_statement",
        stable_subject_key="subject:subj-001",
        title="Share live view",
        primary_text="The system shares the live microscope view.",
        description=None,
        information_type="function",
        reviewed_classification=None,
        reviewed_framework_assignment=None,
        deterministic_disposition="ambiguous",
        deterministic_reason_code="multiple_profile_rules",
        deterministic_candidate_rule_ids=(
            "ELEMENT_SYSTEM_FUNCTION",
            "ELEMENT_SUBSYSTEM_FUNCTION",
        ),
        review_escalation=False,
        allowed_target_options=options,
    )
    return LLMProjectionRequest(
        project_id="120412",
        profile_id="TURING_MODEL_STRUCTURE",
        profile_version="1.0.0",
        profile_fingerprint="a" * 64,
        items=(item,),
        request_fingerprint="b" * 64,
    )


def _response(request, result, selected=None, alternatives=()):
    proposal = LLMProjectionProposal(
        approved_input_id="AIN-000001",
        result=result,
        selected_rule_id=selected,
        alternative_rule_ids=alternatives,
        rationale="bounded placement rationale",
    )
    return LLMProjectionResponse(
        request_fingerprint=request.request_fingerprint,
        proposals=(proposal,),
        response_fingerprint="c" * 64,
    )


def test_unanimous_mapping_is_reviewable_but_not_authoritative():
    request = _request()
    responses = tuple(
        (
            persona,
            _response(
                request,
                "proposed_mapping",
                selected="ELEMENT_SYSTEM_FUNCTION",
            ),
        )
        for persona in ("P1", "P2", "P3")
    )

    bundle = compare_model_placement_personas(
        request=request,
        persona_responses=responses,
    )

    item = bundle.items[0]
    assert bundle.human_review_required is True
    assert item.agreement_level == "unanimous_mapping"
    assert item.unanimous_rule_id == "ELEMENT_SYSTEM_FUNCTION"
    assert item.review_attention_required is False
    assert item.rule_support[0].supporting_personas == ("P1", "P2", "P3")


def test_two_to_one_is_preserved_as_variance_not_majority_authority():
    request = _request()
    responses = (
        (
            "P1",
            _response(
                request,
                "proposed_mapping",
                selected="ELEMENT_SYSTEM_FUNCTION",
            ),
        ),
        (
            "P2",
            _response(
                request,
                "proposed_mapping",
                selected="ELEMENT_SYSTEM_FUNCTION",
            ),
        ),
        (
            "P3",
            _response(
                request,
                "proposed_mapping",
                selected="ELEMENT_SUBSYSTEM_FUNCTION",
            ),
        ),
    )

    bundle = compare_model_placement_personas(
        request=request,
        persona_responses=responses,
    )

    item = bundle.items[0]
    assert item.agreement_level == "placement_variance"
    assert item.unanimous_rule_id is None
    assert item.review_attention_required is True
    assert {
        support.rule_id: support.supporting_personas
        for support in item.rule_support
    } == {
        "ELEMENT_SUBSYSTEM_FUNCTION": ("P3",),
        "ELEMENT_SYSTEM_FUNCTION": ("P1", "P2"),
    }


def test_ambiguous_and_unmapped_personas_are_preserved_for_human_review():
    request = _request()
    responses = (
        (
            "P1",
            _response(
                request,
                "ambiguous",
                alternatives=(
                    "ELEMENT_SYSTEM_FUNCTION",
                    "ELEMENT_SUBSYSTEM_FUNCTION",
                ),
            ),
        ),
        ("P2", _response(request, "unmapped")),
        (
            "P3",
            _response(
                request,
                "proposed_mapping",
                selected="ELEMENT_SYSTEM_FUNCTION",
            ),
        ),
    )

    item = compare_model_placement_personas(
        request=request,
        persona_responses=responses,
    ).items[0]

    assert item.agreement_level == "placement_variance"
    assert item.review_attention_required is True
    assert tuple(p.result for p in item.persona_proposals) == (
        "ambiguous",
        "unmapped",
        "proposed_mapping",
    )


def test_partial_mapping_agreement_does_not_become_authority():
    request = _request()
    responses = (
        (
            "P1",
            _response(
                request,
                "proposed_mapping",
                selected="ELEMENT_SYSTEM_FUNCTION",
            ),
        ),
        (
            "P2",
            _response(
                request,
                "proposed_mapping",
                selected="ELEMENT_SYSTEM_FUNCTION",
            ),
        ),
        ("P3", _response(request, "unmapped")),
    )

    item = compare_model_placement_personas(
        request=request,
        persona_responses=responses,
    ).items[0]

    assert item.agreement_level == "partial_mapping_agreement"
    assert item.unanimous_rule_id is None
    assert item.review_attention_required is True


def test_comparison_is_deterministic_across_persona_input_order():
    request = _request()
    responses = (
        (
            "P1",
            _response(
                request,
                "proposed_mapping",
                selected="ELEMENT_SYSTEM_FUNCTION",
            ),
        ),
        (
            "P2",
            _response(
                request,
                "proposed_mapping",
                selected="ELEMENT_SUBSYSTEM_FUNCTION",
            ),
        ),
        ("P3", _response(request, "unmapped")),
    )

    first = compare_model_placement_personas(
        request=request,
        persona_responses=responses,
    )
    second = compare_model_placement_personas(
        request=request,
        persona_responses=tuple(reversed(responses)),
    )

    assert first == second
    assert first.content_fingerprint == second.content_fingerprint


def test_response_from_other_request_fails_closed():
    request = _request()
    bad = LLMProjectionResponse(
        request_fingerprint="d" * 64,
        proposals=(
            LLMProjectionProposal(
                approved_input_id="AIN-000001",
                result="unmapped",
                selected_rule_id=None,
                alternative_rule_ids=(),
                rationale="bounded placement rationale",
            ),
        ),
        response_fingerprint="e" * 64,
    )

    with pytest.raises(
        ModelPlacementContractError,
        match="exact request",
    ):
        compare_model_placement_personas(
            request=request,
            persona_responses=(
                ("P1", bad),
                ("P2", bad),
            ),
        )
