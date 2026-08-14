from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from modules.final_model_review import (
    FinalModelReviewAgentProposalView,
    FinalModelReviewIntegrityError,
    FinalModelReviewReadService,
    FinalModelReviewView,
    create_evidence_reference,
    create_final_model_review_decision,
    create_final_model_review_decision_target,
    create_final_model_review_item,
    create_final_model_review_revision,
    create_generated_unit_reference,
    final_model_review_view_to_dict,
)
from modules.final_model_review.types import (
    FinalModelReviewRepositoryScanResult,
    FinalModelReviewRevisionBundle,
    FinalModelReviewStoredGeneratedUnit,
)


FP_A = "a" * 64
FP_B = "b" * 64
FP_C = "c" * 64
FP_D = "d" * 64
FP_E = "e" * 64


def _review_decision_ref(decision_id="MCD-000001"):
    return SimpleNamespace(
        model_candidate_review_decision_id=decision_id,
    )


def _iem_snapshot(*, iem_fp=FP_E, candidate_fp=FP_A):
    element_1 = SimpleNamespace(
        internal_model_element_id="IME-000001",
        name="Capture image",
        description="Acquire one image.",
        model_area="functional",
        element_type="function",
        framework_assignment="System/Functional",
        source_model_element_candidate_id="MCE-000001",
        review_decision_reference=_review_decision_ref("MCD-000001"),
    )
    element_2 = SimpleNamespace(
        internal_model_element_id="IME-000002",
        name="Imaging component",
        description=None,
        model_area="logical",
        element_type="logical_component",
        framework_assignment="System/Logical",
        source_model_element_candidate_id="MCE-000002",
        review_decision_reference=_review_decision_ref("MCD-000002"),
    )
    relationship = SimpleNamespace(
        internal_model_relationship_id="IMR-000001",
        source_internal_model_element_id="IME-000001",
        target_internal_model_element_id="IME-000002",
        relationship_family="allocation",
        semantic_intent="allocated_to",
        directionality="directed",
        source_model_relationship_candidate_id="MCR-000001",
        review_decision_reference=_review_decision_ref("MCD-000003"),
    )
    manifest = SimpleNamespace(
        project_id="000001",
        internal_engineering_model_id="IEM-000001",
        content_fingerprint=iem_fp,
        candidate_set_id="MCS-000001",
        candidate_set_content_fingerprint=candidate_fp,
    )
    return SimpleNamespace(
        manifest=manifest,
        elements=(element_1, element_2),
        relationships=(relationship,),
    )


def _candidate_proposal(*, candidate_fp=FP_A):
    return SimpleNamespace(
        candidate_set_id="MCS-000001",
        candidate_set_content_fingerprint=candidate_fp,
        summary="Candidate proposal with accepted and alternative content.",
    )


def _revision(*, status="valid", gate="passed", evidence=()):
    unit = create_generated_unit_reference(
        generated_unit_id="GSU-000001",
        relative_path="generated_model.sysml",
        content_fingerprint=FP_B,
    )
    return create_final_model_review_revision(
        project_id="000001",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id="FRV-000001",
        predecessor_revision_id=None,
        source_internal_engineering_model_id="IEM-000001",
        generated_artifact_set_fingerprint=FP_C,
        validation_result_fingerprint=FP_D,
        validation_status=status,
        publication_gate=gate,
        generated_units=(unit,),
        evidence_references=evidence,
        created_at="2026-08-14T12:00:00Z",
    )


def _artifact_snapshot():
    return {
        "project_id": "000001",
        "source_internal_engineering_model_id": "IEM-000001",
        "source_iem_content_fingerprint": FP_E,
        "content_fingerprint": FP_C,
        "units": [
            {
                "unit_id": "GSU-000001",
                "relative_path": "generated_model.sysml",
                "content": "package GeneratedModel {}\n",
                "content_fingerprint": FP_B,
                "generated_symbol_ids": [
                    "IME_000001",
                    "IME_000002",
                    "IMR_000001",
                ],
            }
        ],
        "traceability_entries": [
            {
                "generated_unit_id": "GSU-000001",
                "generated_symbol_id": "IME_000001",
                "generated_location": {"start_line": 3, "end_line": 5},
                "source_internal_engineering_model_id": "IEM-000001",
                "source_internal_model_element_id": "IME-000001",
                "source_internal_model_relationship_id": None,
                "source_model_candidate_id": "MCE-000001",
                "approved_input_references": [
                    {"approved_input_id": "AI-000001"}
                ],
                "review_decision_reference": {
                    "model_candidate_review_decision_id": "MCD-000001"
                },
                "accepted_exception_reference": None,
            },
            {
                "generated_unit_id": "GSU-000001",
                "generated_symbol_id": "IME_000002",
                "generated_location": {"start_line": 7, "end_line": 9},
                "source_internal_engineering_model_id": "IEM-000001",
                "source_internal_model_element_id": "IME-000002",
                "source_internal_model_relationship_id": None,
                "source_model_candidate_id": "MCE-000002",
                "approved_input_references": [
                    {"approved_input_id": "AI-000002"}
                ],
                "review_decision_reference": {
                    "model_candidate_review_decision_id": "MCD-000002"
                },
                "accepted_exception_reference": None,
            },
            {
                "generated_unit_id": "GSU-000001",
                "generated_symbol_id": "IMR_000001",
                "generated_location": {"start_line": 12, "end_line": 12},
                "source_internal_engineering_model_id": "IEM-000001",
                "source_internal_model_element_id": None,
                "source_internal_model_relationship_id": "IMR-000001",
                "source_model_candidate_id": "MCR-000001",
                "approved_input_references": [
                    {"approved_input_id": "AI-000003"}
                ],
                "review_decision_reference": {
                    "model_candidate_review_decision_id": "MCD-000003"
                },
                "accepted_exception_reference": None,
            },
        ],
    }


def _validation_snapshot(*, status="valid", gate="passed"):
    return {
        "project_id": "000001",
        "source_internal_engineering_model_id": "IEM-000001",
        "source_artifact_set_fingerprint": FP_C,
        "content_fingerprint": FP_D,
        "validation_status": status,
        "publication_gate": gate,
        "findings": [
            {
                "code": "K_EXTERNAL_WARNING",
                "category": "external_warning",
                "severity": "warning",
                "blocking": False,
                "message": "Review warning.",
                "generated_unit_id": "GSU-000001",
                "generated_symbol_id": "IME_000001",
                "generated_location": {
                    "start_line": 3,
                    "end_line": 3,
                    "start_column": 1,
                    "end_column": 5,
                },
                "validator_id": "syside",
                "validator_rule_id": None,
            }
        ],
    }


def _bundle(*, status="valid", gate="passed", evidence=()):
    revision = _revision(status=status, gate=gate, evidence=evidence)
    return FinalModelReviewRevisionBundle(
        revision=revision,
        storage_manifest=SimpleNamespace(),
        artifact_set_snapshot=_artifact_snapshot(),
        validation_result_snapshot=_validation_snapshot(
            status=status, gate=gate
        ),
        generated_units=(
            FinalModelReviewStoredGeneratedUnit(
                generated_unit_id="GSU-000001",
                relative_path="generated_model.sysml",
                content="package GeneratedModel {}\n",
                content_fingerprint=FP_B,
            ),
        ),
    )


class RepoStub:
    def __init__(self, bundle, *, items=(), decisions=()):
        self.bundle = bundle
        self.items = items
        self.decisions = decisions

    def load_revision(self, project_id, review_id, revision_id):
        return self.bundle

    def scan(self, project_id):
        return FinalModelReviewRepositoryScanResult(
            items=self.items,
            issues=(),
        )

    def list_decisions(self, project_id, review_id):
        return self.decisions


class IEMStub:
    def __init__(self, snapshot=None):
        self.snapshot = snapshot or _iem_snapshot()

    def load_phase_j_input(self, project_id, iem_id):
        return self.snapshot


class ProposalStub:
    def __init__(self, proposal=None):
        self.proposal = proposal or _candidate_proposal()

    def load_model_proposal(self, project_id, candidate_set_id):
        return self.proposal


class AgentResolverStub:
    def resolve_agent_proposal(self, project_id, reference):
        return FinalModelReviewAgentProposalView(
            reference_id=reference.reference_id,
            content_fingerprint=reference.content_fingerprint,
            resolution_status="resolved",
            agent_identity="systems_engineer",
            personality="functional_decomposition",
            proposal_summary="Keep allocation and split one function.",
            rationale="Separates acquisition from analysis.",
            confidence="high",
            alternatives=("keep current function",),
        )


def _service(bundle=None, *, items=(), decisions=(), iem=None, proposal=None, resolver=None):
    return FinalModelReviewReadService(
        repository=RepoStub(
            bundle or _bundle(),
            items=items,
            decisions=decisions,
        ),
        internal_model_read_service=IEMStub(iem),
        model_proposal_read_service=ProposalStub(proposal),
        agent_evidence_resolver=resolver,
    )


def test_l3_exposes_exact_sysml_code_without_reformatting():
    view = _service().load_view("000001", "FMR-000001", "FRV-000001")
    assert view.code_units[0].content == "package GeneratedModel {}\n"
    assert view.code_units[0].relative_path == "generated_model.sysml"


def test_l3_diagram_is_derived_from_exact_iem_not_sysml_parsing():
    view = _service().load_view("000001", "FMR-000001", "FRV-000001")
    assert [item.label for item in view.diagram.nodes] == [
        "Capture image",
        "Imaging component",
    ]
    assert view.diagram.edges[0].semantic_intent == "allocated_to"
    assert view.diagram.edges[0].source_internal_model_element_id == "IME-000001"


def test_l3_cross_links_diagram_node_to_generated_code_location():
    view = _service().load_view("000001", "FMR-000001", "FRV-000001")
    node = view.diagram.nodes[0]
    assert node.generated_symbol_id == "IME_000001"
    assert node.code_location.start_line == 3
    assert node.code_location.end_line == 5


def test_l3_cross_links_relationship_to_generated_code_location():
    view = _service().load_view("000001", "FMR-000001", "FRV-000001")
    edge = view.diagram.edges[0]
    assert edge.generated_symbol_id == "IMR_000001"
    assert edge.code_location.start_line == 12


def test_l3_projects_k_validation_findings_for_ui():
    view = _service().load_view("000001", "FMR-000001", "FRV-000001")
    finding = view.validation_findings[0]
    assert finding.category == "external_warning"
    assert finding.generated_symbol_id == "IME_000001"
    assert finding.start_line == 3


def test_l3_projects_complete_traceability_back_to_candidate_and_input():
    view = _service().load_view("000001", "FMR-000001", "FRV-000001")
    trace = next(
        item for item in view.traceability if item.generated_symbol_id == "IME_000001"
    )
    assert trace.source_model_candidate_id == "MCE-000001"
    assert trace.approved_input_ids == ("AI-000001",)
    assert trace.review_decision_id == "MCD-000001"


def test_l3_includes_existing_candidate_proposal_alternatives_projection():
    proposal = _candidate_proposal()
    view = _service(proposal=proposal).load_view(
        "000001", "FMR-000001", "FRV-000001"
    )
    assert view.candidate_proposal is proposal


def test_l3_unresolved_agent_evidence_is_visible_without_invention():
    evidence = create_evidence_reference(
        evidence_type="agent_proposal",
        reference_id="agent_run_01",
        content_fingerprint=FP_A,
    )
    view = _service(bundle=_bundle(evidence=(evidence,))).load_view(
        "000001", "FMR-000001", "FRV-000001"
    )
    proposal = view.agent_proposals[0]
    assert proposal.resolution_status == "referenced_only"
    assert proposal.proposal_summary is None


def test_l3_resolves_agent_personality_evidence_when_resolver_is_available():
    evidence = create_evidence_reference(
        evidence_type="agent_proposal",
        reference_id="agent_run_01",
        content_fingerprint=FP_A,
    )
    view = _service(
        bundle=_bundle(evidence=(evidence,)),
        resolver=AgentResolverStub(),
    ).load_view("000001", "FMR-000001", "FRV-000001")
    proposal = view.agent_proposals[0]
    assert proposal.resolution_status == "resolved"
    assert proposal.personality == "functional_decomposition"
    assert proposal.confidence == "high"


def test_l3_rejects_agent_evidence_resolver_fingerprint_mismatch():
    evidence = create_evidence_reference(
        evidence_type="agent_proposal",
        reference_id="agent_run_01",
        content_fingerprint=FP_A,
    )

    class BadResolver:
        def resolve_agent_proposal(self, project_id, reference):
            return FinalModelReviewAgentProposalView(
                reference_id=reference.reference_id,
                content_fingerprint=FP_B,
                resolution_status="resolved",
                agent_identity="x",
                personality=None,
                proposal_summary="x",
                rationale=None,
                confidence=None,
                alternatives=(),
            )

    with pytest.raises(FinalModelReviewIntegrityError):
        _service(
            bundle=_bundle(evidence=(evidence,)),
            resolver=BadResolver(),
        ).load_view("000001", "FMR-000001", "FRV-000001")


def test_l3_invalid_k_result_is_reviewable_but_state_is_validation_blocked():
    view = _service(
        bundle=_bundle(status="invalid", gate="blocked")
    ).load_view("000001", "FMR-000001", "FRV-000001")
    assert view.review_state == "validation_blocked"
    assert "validation evidence" in view.required_human_actions[0]


def test_l3_valid_passed_without_mandatory_items_is_ready_for_approval():
    view = _service().load_view("000001", "FMR-000001", "FRV-000001")
    assert view.review_state == "ready_for_approval"
    assert "Approve the exact revision" in view.required_human_actions[0]


def test_l3_mandatory_review_item_keeps_revision_review_pending():
    item = create_final_model_review_item(
        project_id="000001",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id="FRV-000001",
        final_model_review_item_id="FRI-000001",
        item_kind="general",
        summary="Check decomposition.",
        detail=None,
        mandatory=True,
    )
    view = _service(items=(item,)).load_view(
        "000001", "FMR-000001", "FRV-000001"
    )
    assert view.review_state == "review_pending"
    assert "mandatory" in view.required_human_actions[0]


def test_l3_changes_requested_decision_is_projected_as_revision_work_state():
    revision = _revision()
    decision = create_final_model_review_decision(
        project_id="000001",
        final_model_review_decision_id="FRD-000001",
        target=create_final_model_review_decision_target(revision),
        decision="changes_requested",
        reviewer_identity="moritz",
        rationale="Split the function.",
        reviewed_at="2026-08-14T12:30:00Z",
    )
    view = _service(
        bundle=_bundle(),
        decisions=(decision,),
    ).load_view("000001", "FMR-000001", "FRV-000001")
    assert view.review_state == "changes_requested"
    assert "regenerate" in view.next_action.lower()


def test_l3_approved_decision_projects_publication_next_action():
    revision = _revision()
    decision = create_final_model_review_decision(
        project_id="000001",
        final_model_review_decision_id="FRD-000001",
        target=create_final_model_review_decision_target(revision),
        decision="approved_for_publication",
        reviewer_identity="moritz",
        rationale="Reviewed complete model.",
        reviewed_at="2026-08-14T12:30:00Z",
    )
    view = _service(
        bundle=_bundle(),
        decisions=(decision,),
    ).load_view("000001", "FMR-000001", "FRV-000001")
    assert view.review_state == "approved_for_publication"
    assert "publication" in view.next_action.lower()


def test_l3_rejects_source_iem_fingerprint_mismatch():
    with pytest.raises(FinalModelReviewIntegrityError):
        _service(iem=_iem_snapshot(iem_fp=FP_A)).load_view(
            "000001", "FMR-000001", "FRV-000001"
        )


def test_l3_rejects_candidate_proposal_for_other_candidate_snapshot():
    with pytest.raises(FinalModelReviewIntegrityError):
        _service(
            proposal=_candidate_proposal(candidate_fp=FP_B)
        ).load_view("000001", "FMR-000001", "FRV-000001")


def test_l3_view_is_machine_projectable_for_focused_ui():
    view = _service().load_view("000001", "FMR-000001", "FRV-000001")
    assert isinstance(view, FinalModelReviewView)
    payload = final_model_review_view_to_dict(view)
    assert payload["review_state"] == "ready_for_approval"
    assert payload["diagram"]["nodes"][0]["label"] == "Capture image"
