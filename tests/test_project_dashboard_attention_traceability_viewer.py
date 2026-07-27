from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
from pathlib import Path
import hashlib
import json

import pytest

import modules.project_dashboard as public_api
from modules.framework_assignment.types import (
    FrameworkAssignmentCandidate,
    FrameworkAssignmentProposal,
)
from modules.human_review.types import (
    HumanReviewDecision,
    HumanReviewIssue,
    HumanReviewScanResult,
    HumanReviewTargetSnapshot,
)
from modules.information_units.types import InformationUnit
from modules.project_coverage.service import (
    ProjectCoverageInputBundle,
)
from modules.project_coverage.types import (
    CoverageIssue,
    FrameworkLevelCoverage,
    FrameworkNodeCoverage,
    PotentialSupportAssessment,
    ProjectCoverageAssessment,
)
from modules.project_dashboard import (
    DashboardAttentionReviewView,
    DashboardDocumentError,
    DashboardDocumentPreview,
    DashboardDocumentViewer,
    DashboardHumanReviewRow,
    DashboardIntegrityError,
    DashboardPresentationError,
    DashboardTraceabilityEdge,
    DashboardTraceabilityNode,
    DashboardTraceabilityView,
    DashboardValidationError,
    EvidenceLocation,
    EvidenceReference,
    ProjectDashboardService,
    make_attention_review_view,
    make_document_preview,
    make_human_review_row,
    make_issue_view,
    make_traceability_edge,
    make_traceability_node,
    make_traceability_view,
    present_status,
    validate_attention_review_view,
    validate_document_preview,
    validate_human_review_row,
    validate_traceability_edge,
    validate_traceability_node,
    validate_traceability_view,
)
from modules.project_processing.types import (
    ProcessingIssue,
    ProjectProcessingSummary,
    SourceProcessingSummary,
)
from modules.project_sources.types import SourceManifest, SourceScanResult
from modules.project_workspace.types import (
    FrameworkTemplateReference,
    ProjectManifest,
)


PROJECT_ID = "318604"
OTHER_PROJECT_ID = "318605"
FRAMEWORK_ID = "TURING_RFLP_FRAMEWORK"
FRAMEWORK_VERSION = "1.0.0"
SUPPORT_PROFILE_ID = "TURING_PRELIMINARY_SUPPORT"
SUPPORT_PROFILE_VERSION = "1.0.0"


def sha(character: str) -> str:
    return character * 64


def project_manifest() -> ProjectManifest:
    return ProjectManifest(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        display_name="Turing Demo",
        description="Traceability demo",
        framework_template=FrameworkTemplateReference(
            template_id=FRAMEWORK_ID,
            template_version=FRAMEWORK_VERSION,
        ),
        created_at="2026-07-27T08:00:00Z",
        updated_at="2026-07-27T08:00:00Z",
    )


def source() -> SourceManifest:
    return SourceManifest(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        source_id="SRC-000001",
        source_role="engineering_source",
        original_filename="requirements.md",
        stored_filename="source.md",
        media_type="text/markdown",
        size_bytes=128,
        sha256=sha("a"),
        registered_at="2026-07-27T08:00:00Z",
        updated_at="2026-07-27T08:00:00Z",
    )


def source_summary() -> SourceProcessingSummary:
    return SourceProcessingSummary(
        project_id=PROJECT_ID,
        source_id="SRC-000001",
        processing_disposition="in_scope",
        current_processing_run_id="RUN-000001",
        run_state="completed",
        processing_stage="publication",
        latest_attempt_id="ATT-000001",
        blocking_issue_codes=(),
        failure_issue_codes=(),
        pending_review=False,
        superseded_run_ids=(),
        invalidated_artifact_count=0,
    )


def processing_summary(
    issues: tuple[ProcessingIssue, ...] = (),
) -> ProjectProcessingSummary:
    return ProjectProcessingSummary(
        project_id=PROJECT_ID,
        project_state="processed",
        total_sources=1,
        in_scope_sources=1,
        context_only_sources=0,
        out_of_scope_sources=0,
        not_started_sources=0,
        running_sources=0,
        awaiting_review_sources=0,
        blocked_sources=0,
        failed_sources=0,
        completed_sources=1,
        superseded_runs=0,
        invalidated_artifacts=0,
        source_summaries=(source_summary(),),
        issues=issues,
    )


def information_unit() -> InformationUnit:
    return InformationUnit(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        information_unit_id="IU-000001",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        source_anchors=(),
        source_excerpt="The system shall record evidence.",
        interpreted_statement="The system shall record evidence.",
        information_type="requirement",
        statement_modality="normative",
        epistemic_class="explicit",
        supporting_information_unit_ids=(),
        derivation_rationale=None,
        missing_evidence=None,
        extraction_provenance=object(),
        confidence="high",
        confidence_rationale="Explicit statement.",
        content_fingerprint=sha("b"),
        created_at="2026-07-27T08:00:00Z",
    )


def assignment_candidate() -> FrameworkAssignmentCandidate:
    return FrameworkAssignmentCandidate(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        information_unit_id="IU-000001",
        framework_assignment_candidate_id="FAC-000001",
        assignment_status="assigned",
        proposals=(
            FrameworkAssignmentProposal(
                framework_node_id="FW_SYSTEM_REQUIREMENTS",
                assignment_bases=(),
                rationale="Requirement evidence.",
            ),
        ),
        candidate_references=(),
        team_id="TEAM-001",
        required_personas=("systems_engineer",),
        llm_provider="openai",
        llm_model="test",
        prompt_schema_version="1.0.0",
        framework_template_id=FRAMEWORK_ID,
        framework_template_version=FRAMEWORK_VERSION,
        turing_core_version="1.0.0",
        project_glossary_revision=1,
        terminology_mapping_candidate_ids=("TMC-000001",),
        consensus_level="unanimous",
        variance_level="low",
        confidence="high",
        confidence_rationale="Consistent evidence.",
        confirmation_required=True,
        review_required=True,
        recommended_review_mode="quick_confirmation",
        content_fingerprint=sha("c"),
        created_at="2026-07-27T08:00:00Z",
    )


def target(
    *,
    target_type: str = "framework_assignment_candidate",
    target_id: str = "FAC-000001",
    validation_status: str = "valid",
) -> HumanReviewTargetSnapshot:
    return HumanReviewTargetSnapshot(
        target_type=target_type,
        target_id=target_id,
        target_content_fingerprint=sha("c"),
        recommended_review_mode="quick_confirmation",
        confirmation_required=True,
        reference_validation_status=validation_status,
        reference_validation_fingerprint=sha("d"),
    )


def decision(
    *,
    decision_id: str = "HRD-000001",
    decision_value: str = "confirm",
    selected_target: HumanReviewTargetSnapshot | None = None,
    decided_at: str = "2026-07-27T10:00:00Z",
) -> HumanReviewDecision:
    return HumanReviewDecision(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        human_review_decision_id=decision_id,
        target=target() if selected_target is None else selected_target,
        review_mode="quick_confirmation",
        decision=decision_value,
        reviewer_identity="reviewer@example.com",
        rationale="Exact evidence reviewed.",
        decided_at=decided_at,
        decision_fingerprint=(
            sha("e") if decision_id.endswith("1") else sha("f")
        ),
    )


def node_coverage() -> FrameworkNodeCoverage:
    return FrameworkNodeCoverage(
        framework_node_id="FW_SYSTEM_REQUIREMENTS",
        mapping_key="system.requirements",
        node_name="Requirements",
        level_node_id="FW_LEVEL_SYSTEM",
        coverage_state="reviewed_candidate_covered",
        attention_required=False,
        eligible_source_count=1,
        information_unit_count=1,
        assignment_candidate_count=1,
        confirmed_candidate_count=1,
        unreviewed_candidate_count=0,
        rejected_candidate_count=0,
        ambiguous_candidate_count=0,
        conflicting_candidate_count=0,
        source_ids=("SRC-000001",),
        information_unit_ids=("IU-000001",),
        framework_assignment_candidate_ids=("FAC-000001",),
        human_review_decision_ids=("HRD-000001",),
        issue_codes=(),
    )


def level_coverage() -> FrameworkLevelCoverage:
    return FrameworkLevelCoverage(
        level_node_id="FW_LEVEL_SYSTEM",
        level_name="System Level",
        coverage_state="partially_covered",
        covered_node_count=1,
        total_node_count=4,
        candidate_covered_node_count=0,
        reviewed_candidate_covered_node_count=1,
        attention_node_count=0,
        covered_node_ids=("FW_SYSTEM_REQUIREMENTS",),
        uncovered_node_ids=(
            "FW_SYSTEM_FUNCTIONAL",
            "FW_SYSTEM_LOGICAL",
            "FW_SYSTEM_PHYSICAL",
        ),
        attention_node_ids=(),
    )


def support_assessment() -> PotentialSupportAssessment:
    return PotentialSupportAssessment(
        support_target_id="SUPPORT_SYSTEM_MODEL",
        name="System Model",
        support_target_type="model",
        support_state="partially_supported",
        required_framework_node_ids=("FW_SYSTEM_REQUIREMENTS",),
        covered_framework_node_ids=("FW_SYSTEM_REQUIREMENTS",),
        missing_framework_node_ids=(),
        required_support_target_ids=(),
        satisfied_support_target_ids=(),
        unsatisfied_support_target_ids=(),
        attention_required=False,
        issue_codes=(),
    )


def assessment(
    issues: tuple[CoverageIssue, ...] = (),
) -> ProjectCoverageAssessment:
    return ProjectCoverageAssessment(
        project_id=PROJECT_ID,
        framework_template_id=FRAMEWORK_ID,
        framework_template_version=FRAMEWORK_VERSION,
        support_profile_id=SUPPORT_PROFILE_ID,
        support_profile_version=SUPPORT_PROFILE_VERSION,
        project_coverage_state="partially_covered",
        node_coverages=(node_coverage(),),
        level_coverages=(level_coverage(),),
        support_assessments=(support_assessment(),),
        approved_readiness_status="not_available",
        approved_readiness_available_from_phase="G",
        assessment_algorithm_id="TEST",
        assessment_algorithm_version="1.0.0",
        assessment_input_fingerprint=sha("9"),
        issues=issues,
    )


@dataclass(frozen=True, slots=True)
class SupportProfile:
    profile_id: str = SUPPORT_PROFILE_ID
    profile_version: str = SUPPORT_PROFILE_VERSION


def input_bundle(
    reviews: tuple[HumanReviewDecision, ...] = (decision(),),
) -> ProjectCoverageInputBundle:
    return ProjectCoverageInputBundle(
        framework_template={
            "template_id": FRAMEWORK_ID,
            "template_version": FRAMEWORK_VERSION,
        },
        support_profile=SupportProfile(),
        source_manifests=(source(),),
        source_processing_summaries=(source_summary(),),
        information_units=(information_unit(),),
        framework_assignment_candidates=(assignment_candidate(),),
        reference_validation_results=(),
        human_review_decisions=reviews,
        artifact_lifecycles=(),
        issues=(),
    )


class Workspace:
    def load_project(self, project_id: str):
        assert project_id == PROJECT_ID
        return project_manifest()

    def scan_projects(self):
        raise AssertionError("not used")


class ProcessingService:
    def __init__(self, value=None):
        self.value = processing_summary() if value is None else value

    def project_summary(self, project_id: str):
        assert project_id == PROJECT_ID
        return self.value


class CoverageService:
    def __init__(self, *, value=None, bundle=None):
        self.value = assessment() if value is None else value
        self.bundle = input_bundle() if bundle is None else bundle

    def assess_project(self, project_id: str):
        assert project_id == PROJECT_ID
        return self.value

    def collect_inputs(self, project_id: str):
        assert project_id == PROJECT_ID
        return self.bundle


class ReviewRepository:
    def __init__(self, scan=None):
        self.scan = (
            HumanReviewScanResult(decisions=(decision(),), issues=())
            if scan is None
            else scan
        )

    def scan_decisions(self, project_id: str):
        assert project_id == PROJECT_ID
        return self.scan


def evidence(
    *,
    path: str = "data/projects/318604/semantics/item.json",
    fingerprint: str | None = None,
    media_type: str = "application/json",
    location: EvidenceLocation | None = None,
) -> EvidenceReference:
    return EvidenceReference(
        project_id=PROJECT_ID,
        reference_type="test_artifact",
        reference_id="TEST-001",
        display_label="Test artifact",
        repository_relative_path=path,
        content_fingerprint=fingerprint,
        media_type=media_type,
        source_role=None,
        relationship="supports_test",
        evidence_role="direct",
        location=location,
    )


def review_row(**overrides) -> DashboardHumanReviewRow:
    values = dict(
        project_id=PROJECT_ID,
        human_review_decision_id="HRD-000001",
        target_type="framework_assignment_candidate",
        target_id="FAC-000001",
        target_content_fingerprint=sha("c"),
        reference_validation_status="valid",
        reference_validation_fingerprint=sha("d"),
        review_mode="quick_confirmation",
        decision="confirm",
        reviewer_identity="reviewer@example.com",
        rationale="Reviewed.",
        decided_at="2026-07-27T10:00:00Z",
        decision_fingerprint=sha("e"),
        evidence_references=(evidence(),),
    )
    values.update(overrides)
    return make_human_review_row(**values)


# Human Review presenter contracts

def test_human_review_row_is_frozen_and_slotted():
    row = review_row()
    with pytest.raises(FrozenInstanceError):
        row.decision = "reject"
    assert not hasattr(row, "__dict__")


@pytest.mark.parametrize(
    ("state", "semantic"),
    [
        ("confirm", "reviewed"),
        ("reject", "blocking"),
        ("request_changes", "attention"),
    ],
)
def test_human_review_decision_status_semantics(state, semantic):
    row = review_row(decision=state)
    assert row.status.state == state
    assert row.status.semantic == semantic


def test_human_review_row_rejects_invalid_fingerprint():
    with pytest.raises(DashboardValidationError):
        review_row(target_content_fingerprint="bad")


def test_human_review_row_rejects_cross_project_evidence():
    wrong = EvidenceReference(
        project_id=OTHER_PROJECT_ID,
        reference_type="test_artifact",
        reference_id="TEST-001",
        display_label="Wrong",
        repository_relative_path=(
            "data/projects/318605/semantics/item.json"
        ),
        content_fingerprint=None,
        media_type="application/json",
        source_role=None,
        relationship="supports_test",
        evidence_role="direct",
    )
    with pytest.raises(DashboardValidationError):
        review_row(evidence_references=(wrong,))


def test_human_review_evidence_is_chooser_for_target_and_decision():
    row = review_row(
        evidence_references=(
            evidence(path="data/projects/318604/semantics/a.json"),
            EvidenceReference(
                project_id=PROJECT_ID,
                reference_type="review",
                reference_id="HRD-000001",
                display_label="Review",
                repository_relative_path=(
                    "data/projects/318604/semantics/b.json"
                ),
                content_fingerprint=None,
                media_type="application/json",
                source_role=None,
                relationship="records_review",
                evidence_role="direct",
            ),
        )
    )
    assert row.evidence.mode == "chooser"
    assert len(row.evidence.references) == 2


def test_attention_view_clear_when_only_confirmations_exist():
    view = make_attention_review_view(
        project_id=PROJECT_ID,
        reviews=(review_row(),),
        issues=(),
    )
    assert view.status.state == "clear"


def test_attention_view_attention_for_request_changes():
    view = make_attention_review_view(
        project_id=PROJECT_ID,
        reviews=(review_row(decision="request_changes"),),
        issues=(),
    )
    assert view.status.state == "attention_required"


def test_attention_view_blocking_for_rejection():
    view = make_attention_review_view(
        project_id=PROJECT_ID,
        reviews=(review_row(decision="reject"),),
        issues=(),
    )
    assert view.status.state == "blocking"


def test_attention_view_uses_latest_exact_decision():
    rejected = review_row(
        decision="reject",
        decided_at="2026-07-27T09:00:00Z",
    )
    confirmed = review_row(
        human_review_decision_id="HRD-000002",
        decision="confirm",
        decided_at="2026-07-27T10:00:00Z",
        decision_fingerprint=sha("f"),
    )
    view = make_attention_review_view(
        project_id=PROJECT_ID,
        reviews=(confirmed, rejected),
        issues=(),
    )
    assert view.status.state == "clear"


def test_attention_view_blocking_for_blocking_issue():
    issue = make_issue_view(
        issue_code="test.blocking",
        message="Blocked.",
        issue_level="blocking",
    )
    view = make_attention_review_view(
        project_id=PROJECT_ID,
        reviews=(),
        issues=(issue,),
    )
    assert view.status.state == "blocking"


def test_attention_view_orders_latest_review_first():
    older = review_row()
    newer = review_row(
        human_review_decision_id="HRD-000002",
        decided_at="2026-07-27T11:00:00Z",
        decision_fingerprint=sha("f"),
    )
    view = make_attention_review_view(
        project_id=PROJECT_ID,
        reviews=(older, newer),
        issues=(),
    )
    assert view.reviews[0].human_review_decision_id == "HRD-000002"


def test_attention_view_rejects_duplicate_review_ids():
    row = review_row()
    with pytest.raises(DashboardValidationError):
        make_attention_review_view(
            project_id=PROJECT_ID,
            reviews=(row, row),
            issues=(),
        )


# Traceability presenter contracts

def trace_node(node_type="source", node_id="SRC-000001"):
    return make_traceability_node(
        node_type=node_type,
        node_id=node_id,
        label=node_id,
        status=present_status("in_scope")
        if node_type == "source"
        else None,
        evidence_references=(evidence(),),
    )


def test_traceability_node_is_frozen_and_slotted():
    node = trace_node()
    with pytest.raises(FrozenInstanceError):
        node.label = "Changed"
    assert not hasattr(node, "__dict__")


def test_traceability_node_key_is_derived():
    node = trace_node()
    assert node.node_key == "source:SRC-000001"


def test_traceability_node_rejects_unknown_type():
    with pytest.raises(DashboardValidationError):
        make_traceability_node(
            node_type="unknown",
            node_id="X",
            label="X",
        )


def test_traceability_edge_key_is_derived():
    edge = make_traceability_edge(
        source_node_key="source:SRC-000001",
        target_node_key="information_unit:IU-000001",
        relationship="supports",
        label="Supports",
    )
    assert edge.edge_key == (
        "source:SRC-000001->supports->information_unit:IU-000001"
    )


def test_traceability_edge_rejects_self_edge():
    with pytest.raises(DashboardValidationError):
        make_traceability_edge(
            source_node_key="source:SRC-000001",
            target_node_key="source:SRC-000001",
            relationship="supports",
            label="Supports",
        )


def test_traceability_view_orders_nodes_and_edges():
    source_node = trace_node()
    unit_node = trace_node(
        node_type="information_unit",
        node_id="IU-000001",
    )
    edge = make_traceability_edge(
        source_node_key=source_node.node_key,
        target_node_key=unit_node.node_key,
        relationship="contains",
        label="Contains",
    )
    view = make_traceability_view(
        project_id=PROJECT_ID,
        nodes=(unit_node, source_node),
        edges=(edge,),
    )
    assert view.nodes[0].node_type == "information_unit"
    assert view.edges == (edge,)


def test_traceability_view_rejects_unknown_edge_endpoint():
    source_node = trace_node()
    edge = make_traceability_edge(
        source_node_key=source_node.node_key,
        target_node_key="information_unit:IU-999999",
        relationship="contains",
        label="Contains",
    )
    with pytest.raises(DashboardValidationError):
        make_traceability_view(
            project_id=PROJECT_ID,
            nodes=(source_node,),
            edges=(edge,),
        )


def test_traceability_view_rejects_duplicate_nodes():
    node = trace_node()
    with pytest.raises(DashboardValidationError):
        make_traceability_view(
            project_id=PROJECT_ID,
            nodes=(node, node),
            edges=(),
        )


# Internal document viewer contracts

def write_file(root: Path, relative: str, content: bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def with_fingerprint(reference: EvidenceReference, content: bytes):
    return EvidenceReference(
        project_id=reference.project_id,
        reference_type=reference.reference_type,
        reference_id=reference.reference_id,
        display_label=reference.display_label,
        repository_relative_path=reference.repository_relative_path,
        content_fingerprint=hashlib.sha256(content).hexdigest(),
        media_type=reference.media_type,
        source_role=reference.source_role,
        relationship=reference.relationship,
        evidence_role=reference.evidence_role,
        location=reference.location,
    )


def test_document_preview_is_frozen_and_slotted(tmp_path):
    content = b'{"a": 1}'
    ref = with_fingerprint(evidence(), content)
    write_file(tmp_path, ref.repository_relative_path, content)
    preview = DashboardDocumentViewer(tmp_path).open(ref)
    with pytest.raises(FrozenInstanceError):
        preview.title = "Changed"
    assert not hasattr(preview, "__dict__")


def test_viewer_opens_and_formats_json(tmp_path):
    content = b'{"z": 1, "a": {"b": 2}}'
    ref = with_fingerprint(evidence(), content)
    write_file(tmp_path, ref.repository_relative_path, content)
    preview = DashboardDocumentViewer(tmp_path).open(ref)
    assert preview.render_mode == "json"
    assert preview.fingerprint_status == "verified"
    assert preview.content_text.index('"a"') < preview.content_text.index('"z"')


def test_viewer_resolves_json_pointer(tmp_path):
    content = b'{"a": {"b": [1, 2]}}'
    ref = with_fingerprint(
        evidence(location=EvidenceLocation(json_pointer="/a/b/1")),
        content,
    )
    write_file(tmp_path, ref.repository_relative_path, content)
    preview = DashboardDocumentViewer(tmp_path).open(ref)
    assert preview.highlighted_text == "2"
    assert preview.selected_json_pointer == "/a/b/1"


def test_viewer_rejects_missing_json_pointer(tmp_path):
    content = b'{"a": 1}'
    ref = with_fingerprint(
        evidence(location=EvidenceLocation(json_pointer="/missing")),
        content,
    )
    write_file(tmp_path, ref.repository_relative_path, content)
    with pytest.raises(DashboardDocumentError):
        DashboardDocumentViewer(tmp_path).open(ref)


def test_viewer_opens_markdown_section(tmp_path):
    content = b"# Intro\nText\n## Details\nMore\n# End\nDone\n"
    ref = with_fingerprint(
        evidence(
            media_type="text/markdown",
            location=EvidenceLocation(section_anchor="intro"),
        ),
        content,
    )
    write_file(tmp_path, ref.repository_relative_path, content)
    preview = DashboardDocumentViewer(tmp_path).open(ref)
    assert preview.render_mode == "markdown"
    assert preview.highlighted_text == "# Intro\nText\n## Details\nMore"


def test_viewer_opens_text_line_range(tmp_path):
    content = b"one\ntwo\nthree\nfour\n"
    ref = with_fingerprint(
        evidence(
            media_type="text/plain",
            location=EvidenceLocation(line_start=2, line_end=3),
        ),
        content,
    )
    write_file(tmp_path, ref.repository_relative_path, content)
    preview = DashboardDocumentViewer(tmp_path).open(ref)
    assert preview.highlighted_text == "two\nthree"


def test_viewer_rejects_line_outside_preview(tmp_path):
    content = b"one\n"
    ref = with_fingerprint(
        evidence(
            media_type="text/plain",
            location=EvidenceLocation(line_start=2),
        ),
        content,
    )
    write_file(tmp_path, ref.repository_relative_path, content)
    with pytest.raises(DashboardDocumentError):
        DashboardDocumentViewer(tmp_path).open(ref)


def test_viewer_opens_csv_as_table(tmp_path):
    content = b"id,name\nA,Alpha\nB,Beta\n"
    ref = with_fingerprint(
        evidence(
            media_type="text/csv",
            location=EvidenceLocation(table_row_key="B"),
        ),
        content,
    )
    write_file(tmp_path, ref.repository_relative_path, content)
    preview = DashboardDocumentViewer(tmp_path).open(ref)
    assert preview.render_mode == "table"
    assert preview.table_columns == ("id", "name")
    assert preview.table_rows[1] == ("B", "Beta")
    assert preview.highlighted_text == "B | Beta"


def test_viewer_rejects_missing_table_row_key(tmp_path):
    content = b"id,name\nA,Alpha\n"
    ref = with_fingerprint(
        evidence(
            media_type="text/csv",
            location=EvidenceLocation(table_row_key="B"),
        ),
        content,
    )
    write_file(tmp_path, ref.repository_relative_path, content)
    with pytest.raises(DashboardDocumentError):
        DashboardDocumentViewer(tmp_path).open(ref)


def test_viewer_returns_metadata_for_unsupported_binary(tmp_path):
    content = b"\x00\x01\x02"
    ref = with_fingerprint(
        evidence(media_type="application/octet-stream"),
        content,
    )
    write_file(tmp_path, ref.repository_relative_path, content)
    preview = DashboardDocumentViewer(tmp_path).open(ref)
    assert preview.render_mode == "metadata"
    assert preview.content_text is None
    assert preview.issue is not None


def test_viewer_rejects_fingerprint_mismatch(tmp_path):
    content = b'{"a": 1}'
    ref = evidence(fingerprint=sha("0"))
    write_file(tmp_path, ref.repository_relative_path, content)
    with pytest.raises(DashboardIntegrityError):
        DashboardDocumentViewer(tmp_path).open(ref)


def test_viewer_reports_not_provided_fingerprint(tmp_path):
    content = b'{"a": 1}'
    ref = evidence()
    write_file(tmp_path, ref.repository_relative_path, content)
    preview = DashboardDocumentViewer(tmp_path).open(ref)
    assert preview.fingerprint_status == "not_provided"


def test_viewer_bounds_large_text_preview(tmp_path):
    content = b"a" * 3000
    ref = with_fingerprint(
        evidence(media_type="text/plain"),
        content,
    )
    write_file(tmp_path, ref.repository_relative_path, content)
    preview = DashboardDocumentViewer(
        tmp_path,
        max_preview_bytes=1024,
    ).open(ref)
    assert preview.truncated is True
    assert len(preview.content_text) == 1024


def test_viewer_does_not_parse_large_json(tmp_path):
    content = json.dumps({"a": "x" * 3000}).encode()
    ref = with_fingerprint(evidence(), content)
    write_file(tmp_path, ref.repository_relative_path, content)
    preview = DashboardDocumentViewer(
        tmp_path,
        max_preview_bytes=1024,
    ).open(ref)
    assert preview.render_mode == "metadata"
    assert preview.truncated is True


def test_viewer_rejects_invalid_utf8_text(tmp_path):
    content = b"\xff\xfe"
    ref = with_fingerprint(
        evidence(media_type="text/plain"),
        content,
    )
    write_file(tmp_path, ref.repository_relative_path, content)
    with pytest.raises(DashboardDocumentError):
        DashboardDocumentViewer(tmp_path).open(ref)


def test_viewer_rejects_invalid_json(tmp_path):
    content = b"{invalid"
    ref = with_fingerprint(evidence(), content)
    write_file(tmp_path, ref.repository_relative_path, content)
    with pytest.raises(DashboardDocumentError):
        DashboardDocumentViewer(tmp_path).open(ref)


def test_viewer_rejects_missing_file(tmp_path):
    with pytest.raises(Exception):
        DashboardDocumentViewer(tmp_path).open(evidence())


def test_document_preview_rejects_table_data_for_text_mode():
    ref = evidence(media_type="text/plain")
    with pytest.raises(DashboardValidationError):
        make_document_preview(
            project_id=PROJECT_ID,
            reference=ref,
            repository_relative_path=ref.repository_relative_path,
            title="Text",
            media_type="text/plain",
            file_size_bytes=1,
            actual_sha256=sha("1"),
            fingerprint_status="not_provided",
            render_mode="text",
            content_text="x",
            highlighted_text=None,
            table_columns=("a",),
            table_rows=(("b",),),
        )


# Service integration contracts

def dashboard_service(
    *,
    processing=None,
    coverage=None,
    reviews=None,
) -> ProjectDashboardService:
    return ProjectDashboardService(
        workspace=Workspace(),
        source_registry=object(),
        processing_summary_service=(
            ProcessingService()
            if processing is None
            else processing
        ),
        coverage_service=(
            CoverageService()
            if coverage is None
            else coverage
        ),
        human_review_repository=(
            ReviewRepository()
            if reviews is None
            else reviews
        ),
    )


def test_attention_service_collects_review_and_exact_evidence():
    view = dashboard_service().attention_review_view(PROJECT_ID)
    assert isinstance(view, DashboardAttentionReviewView)
    assert len(view.reviews) == 1
    row = view.reviews[0]
    assert row.evidence.mode == "chooser"
    assert {
        ref.reference_type for ref in row.evidence.references
    } == {
        "framework_assignment_candidate",
        "human_review_decision",
    }


def test_attention_service_combines_processing_coverage_review_issues():
    p_issue = ProcessingIssue(
        project_id=PROJECT_ID,
        code="processing.warning",
        message="Processing warning.",
        issue_level="warning",
    )
    c_issue = CoverageIssue(
        project_id=PROJECT_ID,
        code="coverage.blocking",
        message="Coverage blocked.",
        issue_level="blocking",
    )
    h_issue = HumanReviewIssue(
        project_id=PROJECT_ID,
        code="review.warning",
        message="Review warning.",
        issue_level="warning",
    )
    service = dashboard_service(
        processing=ProcessingService(processing_summary((p_issue,))),
        coverage=CoverageService(value=assessment((c_issue,))),
        reviews=ReviewRepository(
            HumanReviewScanResult(
                decisions=(decision(),),
                issues=(h_issue,),
            )
        ),
    )
    view = service.attention_review_view(PROJECT_ID)
    assert len(view.issues) == 3
    assert view.status.state == "blocking"


def test_attention_service_rejects_wrong_review_scan_type():
    class BadReview:
        def scan_decisions(self, project_id):
            return object()

    with pytest.raises(DashboardPresentationError):
        dashboard_service(reviews=BadReview()).attention_review_view(
            PROJECT_ID
        )


def test_attention_service_rejects_cross_project_decision():
    wrong = HumanReviewDecision(
        schema_version="1.0.0",
        project_id=OTHER_PROJECT_ID,
        human_review_decision_id="HRD-000001",
        target=target(),
        review_mode="quick_confirmation",
        decision="confirm",
        reviewer_identity="reviewer@example.com",
        rationale=None,
        decided_at="2026-07-27T10:00:00Z",
        decision_fingerprint=sha("e"),
    )
    service = dashboard_service(
        reviews=ReviewRepository(
            HumanReviewScanResult(decisions=(wrong,), issues=())
        )
    )
    with pytest.raises(DashboardPresentationError):
        service.attention_review_view(PROJECT_ID)


def test_traceability_service_builds_full_chain():
    view = dashboard_service().traceability_view(PROJECT_ID)
    assert isinstance(view, DashboardTraceabilityView)
    keys = {node.node_key for node in view.nodes}
    expected = {
        "source:SRC-000001",
        "processing_run:RUN-000001",
        "source_projection:SP-000001",
        "information_unit:IU-000001",
        "terminology_mapping_candidate:TMC-000001",
        "framework_assignment_candidate:FAC-000001",
        "human_review_decision:HRD-000001",
        "framework_node:FW_SYSTEM_REQUIREMENTS",
        "support_target:SUPPORT_SYSTEM_MODEL",
    }
    assert expected <= keys
    relationships = {edge.relationship for edge in view.edges}
    assert {
        "processed_by",
        "projected_as",
        "contains",
        "produced",
        "mapped_by",
        "supports",
        "assigned_by",
        "proposes",
        "reviewed_by",
        "required_by",
    } <= relationships


def test_traceability_nodes_expose_document_navigation():
    view = dashboard_service().traceability_view(PROJECT_ID)
    by_key = {node.node_key: node for node in view.nodes}
    assert by_key["source:SRC-000001"].evidence.mode == "chooser"
    assert (
        by_key["source_projection:SP-000001"].evidence.mode
        == "chooser"
    )
    assert (
        by_key["human_review_decision:HRD-000001"].evidence.mode
        == "chooser"
    )


def test_traceability_framework_candidate_uses_exact_fingerprint():
    view = dashboard_service().traceability_view(PROJECT_ID)
    candidate_node = next(
        node
        for node in view.nodes
        if node.node_key
        == "framework_assignment_candidate:FAC-000001"
    )
    reference = candidate_node.evidence.references[0]
    assert reference.content_fingerprint == sha("c")


def test_traceability_service_is_deterministic():
    service = dashboard_service()
    assert service.traceability_view(
        PROJECT_ID
    ) == service.traceability_view(PROJECT_ID)


def test_traceability_service_rejects_unknown_source():
    unit = information_unit()
    broken_unit = InformationUnit(
        schema_version=unit.schema_version,
        project_id=unit.project_id,
        information_unit_id=unit.information_unit_id,
        source_id="SRC-999999",
        source_projection_id=unit.source_projection_id,
        source_anchors=unit.source_anchors,
        source_excerpt=unit.source_excerpt,
        interpreted_statement=unit.interpreted_statement,
        information_type=unit.information_type,
        statement_modality=unit.statement_modality,
        epistemic_class=unit.epistemic_class,
        supporting_information_unit_ids=unit.supporting_information_unit_ids,
        derivation_rationale=unit.derivation_rationale,
        missing_evidence=unit.missing_evidence,
        extraction_provenance=unit.extraction_provenance,
        confidence=unit.confidence,
        confidence_rationale=unit.confidence_rationale,
        content_fingerprint=unit.content_fingerprint,
        created_at=unit.created_at,
    )
    broken_bundle = input_bundle()
    broken_bundle = ProjectCoverageInputBundle(
        framework_template=broken_bundle.framework_template,
        support_profile=broken_bundle.support_profile,
        source_manifests=broken_bundle.source_manifests,
        source_processing_summaries=broken_bundle.source_processing_summaries,
        information_units=(broken_unit,),
        framework_assignment_candidates=broken_bundle.framework_assignment_candidates,
        reference_validation_results=(),
        human_review_decisions=broken_bundle.human_review_decisions,
    )
    service = dashboard_service(
        coverage=CoverageService(bundle=broken_bundle)
    )
    with pytest.raises(DashboardPresentationError):
        service.traceability_view(PROJECT_ID)


def test_traceability_service_rejects_cross_project_source():
    wrong_source = SourceManifest(
        schema_version="1.0.0",
        project_id=OTHER_PROJECT_ID,
        source_id="SRC-000001",
        source_role="engineering_source",
        original_filename="requirements.md",
        stored_filename="source.md",
        media_type="text/markdown",
        size_bytes=1,
        sha256=sha("a"),
        registered_at="2026-07-27T08:00:00Z",
        updated_at="2026-07-27T08:00:00Z",
    )
    bundle = input_bundle()
    broken = ProjectCoverageInputBundle(
        framework_template=bundle.framework_template,
        support_profile=bundle.support_profile,
        source_manifests=(wrong_source,),
        source_processing_summaries=bundle.source_processing_summaries,
        information_units=bundle.information_units,
        framework_assignment_candidates=bundle.framework_assignment_candidates,
        reference_validation_results=(),
        human_review_decisions=bundle.human_review_decisions,
    )
    with pytest.raises(DashboardPresentationError):
        dashboard_service(
            coverage=CoverageService(bundle=broken)
        ).traceability_view(PROJECT_ID)


def test_traceability_service_creates_placeholder_for_review_only_target():
    extra = decision(
        decision_id="HRD-000002",
        selected_target=target(
            target_type="terminology_mapping_candidate",
            target_id="TMC-000999",
        ),
        decided_at="2026-07-27T11:00:00Z",
    )
    service = dashboard_service(
        reviews=ReviewRepository(
            HumanReviewScanResult(
                decisions=(decision(), extra),
                issues=(),
            )
        )
    )
    view = service.traceability_view(PROJECT_ID)
    keys = {node.node_key for node in view.nodes}
    assert "terminology_mapping_candidate:TMC-000999" in keys
    assert "human_review_decision:HRD-000002" in keys


def test_public_api_exports_step5_contracts():
    expected = {
        "DashboardAttentionReviewView",
        "DashboardDocumentPreview",
        "DashboardDocumentViewer",
        "DashboardHumanReviewRow",
        "DashboardTraceabilityEdge",
        "DashboardTraceabilityNode",
        "DashboardTraceabilityView",
        "make_attention_review_view",
        "make_document_preview",
        "make_human_review_row",
        "make_traceability_edge",
        "make_traceability_node",
        "make_traceability_view",
        "validate_attention_review_view",
        "validate_document_preview",
        "validate_human_review_row",
        "validate_traceability_edge",
        "validate_traceability_node",
        "validate_traceability_view",
    }
    assert expected <= set(public_api.__all__)