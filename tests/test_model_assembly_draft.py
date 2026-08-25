from types import SimpleNamespace

from modules.model_assembly.builder import build_model_assembly_draft


def _profile():
    return SimpleNamespace(
        profile_id="TURING_MODEL_STRUCTURE",
        profile_version="1.0.0",
        profile_fingerprint="a" * 64,
        relationship_semantics=(
            SimpleNamespace(semantic_intent="dependency"),
            SimpleNamespace(semantic_intent="traces_to"),
        ),
    )


def _manifest(aid, key):
    return SimpleNamespace(
        approved_input_id=aid,
        approved_input_kind="element_statement",
        stable_subject_key=key,
        canonical_content=SimpleNamespace(
            title=aid,
            primary_text=f"statement {aid}",
        ),
    )


def _placement(aid, key, rule, area):
    return SimpleNamespace(
        approved_input_id=aid,
        stable_subject_key=key,
        selected_rule_id=rule,
        model_area=area,
        element_type="function",
        framework_assignment="FW",
        review_decision_id=f"MPD-{aid[-6:]}",
        review_decision_fingerprint="b" * 64,
    )


def _subject(sid, aid, key):
    return SimpleNamespace(
        canonical_subject_id=sid,
        approved_input_id=aid,
        stable_subject_key=key,
    )


def _relationship(kind="dependency"):
    return SimpleNamespace(
        source_subject_id="SUBJ-001",
        relationship_kind=kind,
        target_subject_id="SUBJ-002",
        relationship_decision_id="SRD-000001",
        relationship_decision_fingerprint="c" * 64,
        rationale="accepted relationship",
    )


def _request(kind="dependency"):
    authority = SimpleNamespace(
        project_id="120412",
        content_fingerprint="d" * 64,
        subjects=(
            _subject("SUBJ-001", "AIN-000001", "subject:subj-001"),
            _subject("SUBJ-002", "AIN-000002", "subject:subj-002"),
        ),
        relationships=(_relationship(kind),),
        non_projectable_relationship_decision_ids=(),
    )
    return SimpleNamespace(
        project_id="120412",
        approved_inputs=(
            _manifest("AIN-000001", "subject:subj-001"),
            _manifest("AIN-000002", "subject:subj-002"),
        ),
        approved_engineering_information=authority,
    )


def _placement_set():
    return SimpleNamespace(
        project_id="120412",
        comparison_fingerprint="e" * 64,
        content_fingerprint="f" * 64,
        profile_id="TURING_MODEL_STRUCTURE",
        profile_version="1.0.0",
        profile_fingerprint="a" * 64,
        placements=(
            _placement(
                "AIN-000001",
                "subject:subj-001",
                "ELEMENT_SYSTEM_FUNCTION",
                "system.functional",
            ),
            _placement(
                "AIN-000002",
                "subject:subj-002",
                "ELEMENT_SUBSYSTEM_FUNCTION",
                "subsystem.functional",
            ),
        ),
        explicitly_not_materialized_approved_input_ids=(),
    )


def test_human_placement_is_not_reinterpreted_during_assembly():
    draft = build_model_assembly_draft(
        request=_request(),
        approved_placement_set=_placement_set(),
        profile=_profile(),
    )

    assert tuple(
        item.selected_rule_id for item in draft.elements
    ) == (
        "ELEMENT_SYSTEM_FUNCTION",
        "ELEMENT_SUBSYSTEM_FUNCTION",
    )
    assert tuple(item.model_area for item in draft.elements) == (
        "system.functional",
        "subsystem.functional",
    )


def test_exact_relationship_semantic_assembles_without_llm():
    draft = build_model_assembly_draft(
        request=_request("dependency"),
        approved_placement_set=_placement_set(),
        profile=_profile(),
    )

    relationship = draft.relationships[0]
    assert relationship.representation_status == "exact_profile_match"
    assert relationship.candidate_rule_ids == (
        "relationship:dependency",
    )


class _VarianceExecutor:
    def execute_semantic_relationships(self, **kwargs):
        proposal = SimpleNamespace(
            relationship_decision_id="SRD-000001",
            result="ambiguous",
            selected_rule_id=None,
            alternative_rule_ids=(
                "relationship:dependency",
                "relationship:traces_to",
            ),
            rationale="personas disagree",
        )
        response = SimpleNamespace(
            proposals=(proposal,),
            response_fingerprint="9" * 64,
        )
        return (SimpleNamespace(response=response),)


def test_relationship_persona_disagreement_becomes_draft_variance(tmp_path):
    draft = build_model_assembly_draft(
        request=_request("related_to"),
        approved_placement_set=_placement_set(),
        profile=_profile(),
        relationship_executor=_VarianceExecutor(),
        output_dir=tmp_path,
        provider="openai",
        model="gpt-test",
    )

    relationship = draft.relationships[0]
    assert relationship.representation_status == "persona_variance"
    assert relationship.candidate_rule_ids == (
        "relationship:dependency",
        "relationship:traces_to",
    )
    assert draft.relationship_variance_count == 1
    assert draft.unresolved_relationship_count == 0


class _UnmappedExecutor:
    def execute_semantic_relationships(self, **kwargs):
        proposal = SimpleNamespace(
            relationship_decision_id="SRD-000001",
            result="unmapped",
            selected_rule_id=None,
            alternative_rule_ids=(),
            rationale="no defensible target representation",
        )
        response = SimpleNamespace(
            proposals=(proposal,),
            response_fingerprint="8" * 64,
        )
        return (SimpleNamespace(response=response),)


def test_unmapped_relationship_is_preserved_without_generation_failure(tmp_path):
    draft = build_model_assembly_draft(
        request=_request("related_to"),
        approved_placement_set=_placement_set(),
        profile=_profile(),
        relationship_executor=_UnmappedExecutor(),
        output_dir=tmp_path,
        provider="openai",
        model="gpt-test",
    )

    relationship = draft.relationships[0]
    assert relationship.representation_status == "unmapped"
    assert relationship.candidate_rule_ids == ()
    assert draft.unresolved_relationship_count == 1
