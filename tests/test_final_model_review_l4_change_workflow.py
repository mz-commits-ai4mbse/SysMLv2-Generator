from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from modules.final_model_review import (
    FinalModelReviewAgentProposalView,
    FinalModelReviewChangeService,
    FinalModelReviewChangeTarget,
    FinalModelReviewIntegrityError,
    FinalModelReviewReadService,
    FinalModelReviewValidationError,
    create_evidence_reference,
    create_final_model_review_change_proposal,
    create_final_model_review_decision,
    create_final_model_review_decision_target,
    create_final_model_review_revision,
    create_generated_unit_reference,
    final_model_review_change_proposal_from_json,
    final_model_review_change_proposal_to_json,
    format_final_model_review_change_proposal_id,
    next_final_model_review_change_proposal_id,
    validate_final_model_review_change_proposal,
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


def _clock():
    return datetime(2026, 8, 14, 12, 0, 0, tzinfo=timezone.utc)


def _revision():
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
        validation_status="valid",
        publication_gate="passed",
        generated_units=(unit,),
        evidence_references=(),
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
                "generated_symbol_ids": ["IME_000001", "IMR_000001"],
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
                "approved_input_references": [{"approved_input_id": "AI-000001"}],
                "review_decision_reference": {
                    "model_candidate_review_decision_id": "MCD-000001"
                },
                "accepted_exception_reference": None,
            },
            {
                "generated_unit_id": "GSU-000001",
                "generated_symbol_id": "IMR_000001",
                "generated_location": {"start_line": 8, "end_line": 8},
                "source_internal_engineering_model_id": "IEM-000001",
                "source_internal_model_element_id": None,
                "source_internal_model_relationship_id": "IMR-000001",
                "source_model_candidate_id": "MCR-000001",
                "approved_input_references": [{"approved_input_id": "AI-000002"}],
                "review_decision_reference": {
                    "model_candidate_review_decision_id": "MCD-000002"
                },
                "accepted_exception_reference": None,
            },
        ],
    }


def _validation_snapshot():
    return {
        "project_id": "000001",
        "source_internal_engineering_model_id": "IEM-000001",
        "source_artifact_set_fingerprint": FP_C,
        "content_fingerprint": FP_D,
        "validation_status": "valid",
        "publication_gate": "passed",
        "findings": [
            {
                "code": "K_EXTERNAL_WARNING",
                "category": "external_warning",
                "severity": "warning",
                "blocking": False,
                "message": "Review warning.",
                "generated_unit_id": "GSU-000001",
                "generated_symbol_id": "IME_000001",
                "generated_location": None,
                "validator_id": "syside",
                "validator_rule_id": None,
            }
        ],
    }


def _bundle():
    return FinalModelReviewRevisionBundle(
        revision=_revision(),
        storage_manifest=SimpleNamespace(),
        artifact_set_snapshot=_artifact_snapshot(),
        validation_result_snapshot=_validation_snapshot(),
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
    def __init__(self, bundle=None, proposals=(), decisions=(), items=()):
        self.bundle = bundle or _bundle()
        self.proposals = list(proposals)
        self.decisions = decisions
        self.items = items

    def load_revision(self, project_id, review_id, revision_id):
        return self.bundle

    def list_change_proposals(self, project_id, review_id=None, revision_id=None):
        values = self.proposals
        if review_id is not None:
            values = [v for v in values if v.final_model_review_id == review_id]
        if revision_id is not None:
            values = [v for v in values if v.final_model_review_revision_id == revision_id]
        return tuple(values)

    def persist_change_proposal(self, proposal):
        if any(p.content_fingerprint == proposal.content_fingerprint for p in self.proposals):
            raise FinalModelReviewIntegrityError("duplicate")
        self.proposals.append(proposal)
        return proposal

    def list_decisions(self, project_id, review_id):
        return self.decisions

    def scan(self, project_id):
        return FinalModelReviewRepositoryScanResult(
            items=self.items,
            change_proposals=tuple(self.proposals),
            issues=(),
        )


class AgentAdapterStub:
    def __init__(self):
        self.requests = []

    def submit_reproposal_request(self, request):
        self.requests.append(request)


def _service(repo=None, adapter=None):
    return FinalModelReviewChangeService(
        repository=repo or RepoStub(),
        clock=_clock,
        agent_reproposal_adapter=adapter,
    )


def test_l4_fcp_identifier_contract_and_allocation():
    assert format_final_model_review_change_proposal_id(7) == "FCP-000007"
    assert next_final_model_review_change_proposal_id(
        ("FCP-000001", "FCP-000003")
    ) == "FCP-000004"


@pytest.mark.parametrize(
    ("classification", "route"),
    [
        ("engineering_semantics", "phase_h_candidate_review"),
        ("generated_representation", "phase_j_generation"),
        ("validation_policy_or_tool", "phase_k_validation"),
        ("review_presentation_only", "phase_l_presentation"),
    ],
)
def test_l4_classification_has_deterministic_authority_route(classification, route):
    assert _service().route_for_classification(classification).authority_route == route


def test_l4_sysml_code_edit_is_persisted_as_change_proposal_not_mutation():
    repo = RepoStub()
    submission = _service(repo).submit_change(
        "000001",
        "FMR-000001",
        "FRV-000001",
        surface="sysml_code",
        classification="generated_representation",
        reviewer_feedback="Use the correct deterministic rendering.",
        created_by="moritz",
        generated_unit_id="GSU-000001",
        generated_symbol_id="IME_000001",
        original_text="part old;",
        proposed_text="part new;",
    )
    assert submission.proposal.final_model_review_change_proposal_id == "FCP-000001"
    assert submission.proposal.target.generated_unit_content_fingerprint == FP_B
    assert submission.route.authority_route == "phase_j_generation"
    assert submission.route.requires_regeneration is True
    assert repo.bundle.generated_units[0].content == "package GeneratedModel {}\n"


def test_l4_material_sysml_edit_cannot_be_presentation_only():
    with pytest.raises(FinalModelReviewValidationError):
        _service().submit_change(
            "000001",
            "FMR-000001",
            "FRV-000001",
            surface="sysml_code",
            classification="review_presentation_only",
            reviewer_feedback="Change model code.",
            created_by="moritz",
            generated_unit_id="GSU-000001",
            original_text="a",
            proposed_text="b",
        )


def test_l4_diagram_semantic_change_routes_to_candidate_review():
    submission = _service().submit_change(
        "000001",
        "FMR-000001",
        "FRV-000001",
        surface="diagram",
        classification="engineering_semantics",
        reviewer_feedback="Allocate the function to another logical component.",
        created_by="moritz",
        internal_model_element_id="IME-000001",
    )
    assert submission.route.authority_route == "phase_h_candidate_review"
    assert submission.route.requires_candidate_review is True
    assert submission.route.requires_new_review_revision is True


def test_l4_validation_finding_change_routes_to_phase_k():
    submission = _service().submit_change(
        "000001",
        "FMR-000001",
        "FRV-000001",
        surface="validation_finding",
        classification="validation_policy_or_tool",
        reviewer_feedback="Investigate this validator finding.",
        created_by="moritz",
        validation_finding_code="K_EXTERNAL_WARNING",
    )
    assert submission.route.authority_route == "phase_k_validation"
    assert submission.route.requires_regeneration is False
    assert submission.route.requires_revalidation is True


def test_l4_rejects_validation_finding_outside_revision():
    with pytest.raises(FinalModelReviewIntegrityError):
        _service().submit_change(
            "000001",
            "FMR-000001",
            "FRV-000001",
            surface="validation_finding",
            classification="validation_policy_or_tool",
            reviewer_feedback="Investigate.",
            created_by="moritz",
            validation_finding_code="NOT_PRESENT",
        )


def test_l4_rejects_generated_symbol_outside_revision():
    with pytest.raises(FinalModelReviewIntegrityError):
        _service().submit_change(
            "000001",
            "FMR-000001",
            "FRV-000001",
            surface="sysml_code",
            classification="generated_representation",
            reviewer_feedback="Change.",
            created_by="moritz",
            generated_unit_id="GSU-000001",
            generated_symbol_id="IME_999999",
            original_text="a",
            proposed_text="b",
        )


def test_l4_rejects_iem_target_outside_exact_review_subject():
    with pytest.raises(FinalModelReviewIntegrityError):
        _service().submit_change(
            "000001",
            "FMR-000001",
            "FRV-000001",
            surface="diagram",
            classification="engineering_semantics",
            reviewer_feedback="Change.",
            created_by="moritz",
            internal_model_element_id="IME-999999",
        )


def test_l4_optional_agent_reproposal_preserves_human_feedback_and_candidate():
    adapter = AgentAdapterStub()
    submission = _service(adapter=adapter).submit_change(
        "000001",
        "FMR-000001",
        "FRV-000001",
        surface="diagram",
        classification="engineering_semantics",
        reviewer_feedback="Split this function and compare alternatives.",
        created_by="moritz",
        internal_model_element_id="IME-000001",
        request_agent_reproposal=True,
        requested_agent_personalities=("requirements_engineer", "systems_engineer"),
    )
    request = submission.agent_reproposal_request
    assert request is not None
    assert request.source_model_candidate_ids == ("MCE-000001",)
    assert request.reviewer_feedback.startswith("Split this function")
    assert adapter.requests == [request]


def test_l4_agent_reproposal_cannot_be_requested_for_presentation_only_change():
    with pytest.raises(FinalModelReviewValidationError):
        _service().submit_change(
            "000001",
            "FMR-000001",
            "FRV-000001",
            surface="diagram",
            classification="review_presentation_only",
            reviewer_feedback="Rename a UI label only.",
            created_by="moritz",
            internal_model_element_id="IME-000001",
            request_agent_reproposal=True,
        )


def test_l4_change_proposal_json_round_trip_and_fingerprint():
    target = FinalModelReviewChangeTarget(
        generated_unit_id="GSU-000001",
        generated_unit_content_fingerprint=FP_B,
        generated_symbol_id="IME_000001",
        internal_model_element_id="IME-000001",
        internal_model_relationship_id=None,
        validation_finding_code=None,
    )
    proposal = create_final_model_review_change_proposal(
        project_id="000001",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id="FRV-000001",
        final_model_review_change_proposal_id="FCP-000001",
        base_revision_content_fingerprint=_revision().content_fingerprint,
        base_review_subject_fingerprint=_revision().review_subject_fingerprint,
        surface="sysml_code",
        classification="generated_representation",
        target=target,
        original_text="a",
        proposed_text="b",
        reviewer_feedback="Change rendering.",
        request_agent_reproposal=False,
        created_by="moritz",
        created_at="2026-08-14T12:00:00Z",
    )
    loaded = final_model_review_change_proposal_from_json(
        final_model_review_change_proposal_to_json(proposal),
        expected_project_id="000001",
        expected_review_id="FMR-000001",
        expected_change_proposal_id="FCP-000001",
    )
    assert loaded == proposal
    validate_final_model_review_change_proposal(loaded)


def test_l4_change_proposal_detects_tampering():
    submission = _service().submit_change(
        "000001", "FMR-000001", "FRV-000001",
        surface="diagram",
        classification="engineering_semantics",
        reviewer_feedback="Change allocation.",
        created_by="moritz",
        internal_model_element_id="IME-000001",
    )
    tampered = replace(submission.proposal, reviewer_feedback="Different")
    with pytest.raises(FinalModelReviewIntegrityError):
        validate_final_model_review_change_proposal(tampered)


def test_l4_equivalent_duplicate_proposal_is_rejected():
    repo = RepoStub()
    service = _service(repo)
    kwargs = dict(
        surface="diagram",
        classification="engineering_semantics",
        reviewer_feedback="Change allocation.",
        created_by="moritz",
        internal_model_element_id="IME-000001",
    )
    service.submit_change("000001", "FMR-000001", "FRV-000001", **kwargs)
    with pytest.raises(FinalModelReviewIntegrityError):
        service.submit_change("000001", "FMR-000001", "FRV-000001", **kwargs)


# L3 projection regression: an explicit proposal must block approval presentation.
class IEMStub:
    def load_phase_j_input(self, project_id, iem_id):
        element = SimpleNamespace(
            internal_model_element_id="IME-000001",
            name="Capture image",
            description=None,
            model_area="functional",
            element_type="function",
            framework_assignment="System/Functional",
            source_model_element_candidate_id="MCE-000001",
            review_decision_reference=SimpleNamespace(
                model_candidate_review_decision_id="MCD-000001"
            ),
        )
        relationship = SimpleNamespace(
            internal_model_relationship_id="IMR-000001",
            source_internal_model_element_id="IME-000001",
            target_internal_model_element_id="IME-000001",
            relationship_family="dependency",
            semantic_intent="depends_on",
            directionality="directed",
            source_model_relationship_candidate_id="MCR-000001",
            review_decision_reference=SimpleNamespace(
                model_candidate_review_decision_id="MCD-000002"
            ),
        )
        return SimpleNamespace(
            manifest=SimpleNamespace(
                project_id="000001",
                internal_engineering_model_id="IEM-000001",
                content_fingerprint=FP_E,
                candidate_set_id="MCS-000001",
                candidate_set_content_fingerprint=FP_A,
            ),
            elements=(element,),
            relationships=(relationship,),
        )


class ProposalStub:
    def load_model_proposal(self, project_id, candidate_set_id):
        return SimpleNamespace(
            candidate_set_content_fingerprint=FP_A,
            summary="proposal",
        )


def _read_service(repo):
    return FinalModelReviewReadService(
        repository=repo,
        internal_model_read_service=IEMStub(),
        model_proposal_read_service=ProposalStub(),
    )


def test_l4_read_model_projects_change_proposal_and_regeneration_required():
    repo = RepoStub()
    proposal = _service(repo).submit_change(
        "000001", "FMR-000001", "FRV-000001",
        surface="diagram",
        classification="engineering_semantics",
        reviewer_feedback="Change allocation.",
        created_by="moritz",
        internal_model_element_id="IME-000001",
    ).proposal
    view = _read_service(repo).load_view(
        "000001", "FMR-000001", "FRV-000001"
    )
    assert view.change_proposals == (proposal,)
    assert view.review_state == "regeneration_required"
    assert "phase_h_candidate_review" in view.required_human_actions[0]


def test_l4_validation_only_change_projects_changes_requested_not_regeneration():
    repo = RepoStub()
    _service(repo).submit_change(
        "000001", "FMR-000001", "FRV-000001",
        surface="validation_finding",
        classification="validation_policy_or_tool",
        reviewer_feedback="Recheck validator policy.",
        created_by="moritz",
        validation_finding_code="K_EXTERNAL_WARNING",
    )
    view = _read_service(repo).load_view(
        "000001", "FMR-000001", "FRV-000001"
    )
    assert view.review_state == "changes_requested"


def test_l4_change_proposal_after_approval_overrides_publication_ready_view():
    revision = _revision()
    approved = create_final_model_review_decision(
        project_id="000001",
        final_model_review_decision_id="FRD-000001",
        target=create_final_model_review_decision_target(revision),
        decision="approved_for_publication",
        reviewer_identity="moritz",
        rationale="Approved.",
        reviewed_at="2026-08-14T12:05:00Z",
    )
    repo = RepoStub(decisions=(approved,))
    _service(repo).submit_change(
        "000001", "FMR-000001", "FRV-000001",
        surface="diagram",
        classification="engineering_semantics",
        reviewer_feedback="Late change request.",
        created_by="moritz",
        internal_model_element_id="IME-000001",
    )
    view = _read_service(repo).load_view(
        "000001", "FMR-000001", "FRV-000001"
    )
    assert view.review_state == "regeneration_required"

# Filesystem regression for L2/L4 sidecar persistence.
from dataclasses import dataclass
import hashlib
from modules.final_model_review import FinalModelReviewRepository, create_final_model_review_item


class WorkspaceStub:
    def load_project(self, project_id):
        if project_id != "000001":
            raise RuntimeError("Project not found")
        return object()


@dataclass(frozen=True)
class FsUnit:
    unit_id: str
    relative_path: str
    content: str
    content_fingerprint: str
    generated_symbol_ids: tuple[str, ...]
    source_internal_model_element_ids: tuple[str, ...] = ()
    source_internal_model_relationship_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class FsArtifact:
    project_id: str
    source_internal_engineering_model_id: str
    content_fingerprint: str
    units: tuple[FsUnit, ...]
    traceability_entries: tuple[object, ...] = ()


@dataclass(frozen=True)
class FsValidation:
    project_id: str
    source_internal_engineering_model_id: str
    source_artifact_set_fingerprint: str
    content_fingerprint: str
    validation_status: str
    publication_gate: str
    findings: tuple[object, ...] = ()


def _fs_repo(tmp_path):
    return FinalModelReviewRepository(
        root=tmp_path,
        workspace=WorkspaceStub(),
        clock=_clock,
        artifact_validator=lambda value: None,
        validation_result_validator=lambda value: None,
    )


def _fs_inputs():
    content = "package GeneratedModel {}\n"
    unit = FsUnit(
        unit_id="GSU-000001",
        relative_path="generated_model.sysml",
        content=content,
        content_fingerprint=hashlib.sha256(content.encode()).hexdigest(),
        generated_symbol_ids=("IME_000001",),
    )
    artifact = FsArtifact(
        project_id="000001",
        source_internal_engineering_model_id="IEM-000001",
        content_fingerprint=FP_C,
        units=(unit,),
    )
    validation = FsValidation(
        project_id="000001",
        source_internal_engineering_model_id="IEM-000001",
        source_artifact_set_fingerprint=FP_C,
        content_fingerprint=FP_D,
        validation_status="valid",
        publication_gate="passed",
    )
    return artifact, validation


def test_l4_item_sidecar_does_not_mutate_or_break_immutable_revision_bundle(tmp_path):
    repo = _fs_repo(tmp_path)
    repo.create_review("000001")
    artifact, validation = _fs_inputs()
    bundle = repo.append_revision(
        "000001", "FMR-000001",
        artifact_set=artifact,
        validation_result=validation,
    )
    item = create_final_model_review_item(
        project_id="000001",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id="FRV-000001",
        final_model_review_item_id="FRI-000001",
        item_kind="generated_symbol",
        summary="Review symbol.",
        detail=None,
        mandatory=True,
        generated_unit_id="GSU-000001",
        generated_symbol_id="IME_000001",
    )
    repo.persist_item(item)
    reloaded = repo.load_revision(
        "000001", "FMR-000001", "FRV-000001"
    )
    assert reloaded.revision.content_fingerprint == bundle.revision.content_fingerprint


def test_l4_repository_persists_change_proposal_as_sidecar_and_scans_clean(tmp_path):
    repo = _fs_repo(tmp_path)
    repo.create_review("000001")
    artifact, validation = _fs_inputs()
    bundle = repo.append_revision(
        "000001", "FMR-000001",
        artifact_set=artifact,
        validation_result=validation,
    )
    proposal = create_final_model_review_change_proposal(
        project_id="000001",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id="FRV-000001",
        final_model_review_change_proposal_id="FCP-000001",
        base_revision_content_fingerprint=bundle.revision.content_fingerprint,
        base_review_subject_fingerprint=bundle.revision.review_subject_fingerprint,
        surface="sysml_code",
        classification="generated_representation",
        target=FinalModelReviewChangeTarget(
            generated_unit_id="GSU-000001",
            generated_unit_content_fingerprint=artifact.units[0].content_fingerprint,
            generated_symbol_id="IME_000001",
            internal_model_element_id=None,
            internal_model_relationship_id=None,
            validation_finding_code=None,
        ),
        original_text="a",
        proposed_text="b",
        reviewer_feedback="Change rendering.",
        request_agent_reproposal=False,
        created_by="moritz",
        created_at="2026-08-14T12:00:00Z",
    )
    assert repo.persist_change_proposal(proposal) == proposal
    assert repo.list_change_proposals("000001") == (proposal,)
    scan = repo.scan("000001")
    assert scan.change_proposals == (proposal,)
    assert scan.issues == ()


def test_l4_repository_rejects_change_proposal_bound_to_stale_revision(tmp_path):
    repo = _fs_repo(tmp_path)
    repo.create_review("000001")
    artifact, validation = _fs_inputs()
    repo.append_revision(
        "000001", "FMR-000001",
        artifact_set=artifact,
        validation_result=validation,
    )
    target = FinalModelReviewChangeTarget(
        generated_unit_id="GSU-000001",
        generated_unit_content_fingerprint=artifact.units[0].content_fingerprint,
        generated_symbol_id="IME_000001",
        internal_model_element_id=None,
        internal_model_relationship_id=None,
        validation_finding_code=None,
    )
    proposal = create_final_model_review_change_proposal(
        project_id="000001",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id="FRV-000001",
        final_model_review_change_proposal_id="FCP-000001",
        base_revision_content_fingerprint=FP_A,
        base_review_subject_fingerprint=FP_B,
        surface="sysml_code",
        classification="generated_representation",
        target=target,
        original_text="a",
        proposed_text="b",
        reviewer_feedback="Change rendering.",
        request_agent_reproposal=False,
        created_by="moritz",
        created_at="2026-08-14T12:00:00Z",
    )
    with pytest.raises(FinalModelReviewIntegrityError):
        repo.persist_change_proposal(proposal)
