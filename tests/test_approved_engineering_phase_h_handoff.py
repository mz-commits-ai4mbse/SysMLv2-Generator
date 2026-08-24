from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from modules.approved_engineering_information import (
    ApprovedEngineeringInformationSet,
    ApprovedEngineeringRelationship,
    ApprovedEngineeringSubject,
)
from modules.approved_input.types import ApprovedInputCanonicalContent, ApprovedInputManifest
from modules.model_candidates.approved_engineering_deriver import (
    ApprovedEngineeringInformationDeriver,
    bind_generation_provenance_to_approved_engineering_information,
    validate_approved_engineering_information_binding,
)
from modules.model_candidates.derivation_context import load_model_derivation_rules_reference
from modules.model_candidates.profile_deriver import ProfileDrivenModelCandidateDeriver
from modules.model_candidates.structure_profile import (
    load_model_structure_profile,
    model_structure_profile_reference,
)
from modules.model_candidates.types import (
    ModelCandidateDerivationRequest,
    ModelCandidateGenerationProvenance,
)
from modules.project_workspace.types import FrameworkTemplateReference

PROJECT_ID = "120412"


def _manifest(index: int, *, stable_subject_key: str, title: str):
    digit = str(index)
    return ApprovedInputManifest(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        approved_input_id=f"AIN-{index:06d}",
        approved_input_kind="element_statement",
        authority_state="active",
        canonical_content=ApprovedInputCanonicalContent(
            title=title,
            primary_text=f"{title} statement.",
            description=None,
            information_type="actor",
            modality="descriptive",
            epistemic_status="explicit",
        ),
        selected_classification="Actor",
        selected_framework_assignment=None,
        selected_terminology_assignment=None,
        selected_source_assignments=(),
        selected_relationship_representation=None,
        stable_subject_key=stable_subject_key,
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        review_item_id=f"RIT-{index:06d}",
        review_item_kind="element",
        review_item_fingerprint=digit * 64,
        finalized_artifact_set_fingerprint="a" * 64,
        finalization_decision_id="HRD-000001",
        finalization_decision_fingerprint="b" * 64,
        finalization_validation_fingerprint="c" * 64,
        source_id="SRC-000001",
        source_sha256="d" * 64,
        processing_run_id="RUN-000001",
        attempt_id="ATT-000001",
        primary_artifact_reference=None,
        supporting_artifact_references=(),
        proposal_references=(),
        created_at="2026-08-24T12:00:00Z",
        content_fingerprint=(hex(index)[2:] * 64)[:64],
    )


def _authority(inputs, *, relationship_kind="depends_on"):
    subjects = tuple(
        ApprovedEngineeringSubject(
            canonical_subject_id=f"SUBJ-{index:06d}",
            approved_input_id=item.approved_input_id,
            stable_subject_key=item.stable_subject_key,
            title=item.canonical_content.title,
            engineering_statement=item.canonical_content.primary_text,
            information_type=item.canonical_content.information_type,
            statement_modality=item.canonical_content.modality,
            epistemic_class=item.canonical_content.epistemic_status,
            review_item_id=item.review_item_id,
            review_item_fingerprint=item.review_item_fingerprint,
            approved_input_fingerprint=item.content_fingerprint,
        )
        for index, item in enumerate(inputs, start=1)
    )
    return ApprovedEngineeringInformationSet(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        subjects=subjects,
        relationships=(
            ApprovedEngineeringRelationship(
                source_subject_id="SUBJ-000001",
                relationship_kind=relationship_kind,
                target_subject_id="SUBJ-000002",
                relationship_decision_id="SRD-000001",
                relationship_decision_fingerprint="e" * 64,
                rationale=None,
            ),
        ),
        relationship_decision_authority_fingerprint="f" * 64,
        content_fingerprint="9" * 64,
    )


def _request(*, relationship_kind="depends_on"):
    inputs = (
        _manifest(1, stable_subject_key="subject:subj-000001", title="operator"),
        _manifest(2, stable_subject_key="subject:subj-000002", title="remote expert"),
    )
    profile = load_model_structure_profile()
    rules = load_model_derivation_rules_reference()
    authority = _authority(inputs, relationship_kind=relationship_kind)
    return (
        ModelCandidateDerivationRequest(
            project_id=PROJECT_ID,
            approved_inputs=inputs,
            framework_template_reference=FrameworkTemplateReference(
                template_id=profile.framework_template_id,
                template_version=profile.framework_template_version,
            ),
            model_structure_profile_reference=model_structure_profile_reference(profile),
            derivation_rules_reference=rules,
            predecessor_candidate_set=None,
            approved_engineering_information=authority,
        ),
        profile,
        rules,
    )


def test_exact_aei_binding_and_relationship_reaches_phase_h():
    request, profile, rules = _request()
    validate_approved_engineering_information_binding(
        project_id=PROJECT_ID,
        approved_inputs=request.approved_inputs,
        approved_engineering_information=request.approved_engineering_information,
    )
    deriver = ApprovedEngineeringInformationDeriver(
        base_deriver=ProfileDrivenModelCandidateDeriver(
            profile=profile,
            derivation_rules_reference=rules,
        ),
        profile=profile,
    )
    coverage = deriver.assess_projection_coverage(request)
    assert coverage.approved_input_count == 2
    assert coverage.semantic_relationship_count == 1
    assert coverage.unresolved_semantic_relationship_ids == ()

    plan = deriver.derive(request)
    assert len(plan.element_drafts) == 2
    assert len(plan.relationship_drafts) == 1
    relationship = plan.relationship_drafts[0]
    assert relationship.semantic_intent == "depends_on"
    assert relationship.source_subject_key == "subject:subj-000001"
    assert relationship.target_subject_key == "subject:subj-000002"
    assert {
        item.approved_input_id for item in relationship.approved_input_selections
    } == {"AIN-000001", "AIN-000002"}
    assert any(
        value.startswith("SRD-000001:")
        for value in relationship.supporting_evidence
    )


class _FakeRelationshipExecutor:
    def execute_semantic_relationships(
        self,
        *,
        request,
        relationship_entries,
        profile,
        output_dir,
    ):
        proposal = SimpleNamespace(
            relationship_decision_id="SRD-000001",
            result="proposed_mapping",
            selected_rule_id="relationship:depends_on",
            alternative_rule_ids=(),
            rationale="Profile-bounded mapping.",
        )
        return (
            SimpleNamespace(
                request=SimpleNamespace(request_fingerprint="8" * 64),
                response=SimpleNamespace(
                    proposals=(proposal,),
                    response_fingerprint="7" * 64,
                ),
            ),
        )


def test_unmapped_human_relationship_is_separate_from_approved_input_ids():
    request, profile, rules = _request(relationship_kind="provides")
    deriver = ApprovedEngineeringInformationDeriver(
        base_deriver=ProfileDrivenModelCandidateDeriver(
            profile=profile,
            derivation_rules_reference=rules,
        ),
        profile=profile,
        relationship_executor=_FakeRelationshipExecutor(),
        output_dir=Path("."),
    )
    coverage = deriver.assess_projection_coverage(request)
    assert coverage.unresolved_approved_input_ids == ()
    assert coverage.unresolved_semantic_relationship_ids == ("SRD-000001",)
    assert coverage.unmapped_count == 1

    plan = deriver.derive(request)
    assert len(plan.relationship_drafts) == 1
    assert plan.relationship_drafts[0].semantic_intent == "depends_on"
    assert "LLM-projected" in plan.relationship_drafts[0].derivation_rationale


def test_generation_provenance_is_bound_to_aei_fingerprint():
    request, _profile, _rules = _request()
    base = ModelCandidateGenerationProvenance(
        method="llm_assisted_profile_projection",
        recipe_reference="ADR-028:R5-01",
        agent_reference="teams/modeling/modeling_projection_team.json",
        model_reference="openai:test",
        context_fingerprint="1" * 64,
    )
    bound = bind_generation_provenance_to_approved_engineering_information(
        base,
        request.approved_engineering_information,
    )
    assert bound.context_fingerprint != base.context_fingerprint
    assert len(bound.context_fingerprint) == 64
