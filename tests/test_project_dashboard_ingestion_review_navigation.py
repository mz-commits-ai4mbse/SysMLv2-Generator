"""P9 dashboard navigation for the Phase-F Ingestion Review Report."""

from __future__ import annotations

from contextlib import nullcontext
from types import SimpleNamespace

from app.project_dashboard_ui import (
    render_source_evidence_sections,
    render_view_selector,
    source_evidence_sections,
)
from modules.project_dashboard.service import ProjectDashboardService
from modules.project_dashboard.types import EvidenceNavigation, EvidenceReference
from modules.project_processing.types import ProcessingArtifactReference
from modules.project_sources.types import SourceManifest


PROJECT_ID = "458990"
SOURCE_ID = "SRC-000002"
RUN_ID = "RUN-000002"
ATTEMPT_ID = "ATT-000001"
SHA = "a" * 64


def source() -> SourceManifest:
    return SourceManifest(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        source_role="engineering_source",
        original_filename="requirements.txt",
        stored_filename="content.txt",
        media_type="text/plain",
        size_bytes=100,
        sha256=SHA,
        registered_at="2026-07-27T19:00:00Z",
        updated_at="2026-07-27T19:00:00Z",
    )


def artifact(
    artifact_type: str,
    artifact_id: str,
    relative_tail: str,
) -> ProcessingArtifactReference:
    return ProcessingArtifactReference(
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        content_fingerprint=SHA,
        repository_relative_path=(
            f"data/projects/{PROJECT_ID}/runs/{RUN_ID}/artifacts/"
            f"{artifact_type}/agentic_ingestion/{ATTEMPT_ID}/"
            f"{relative_tail}"
        ),
    )


class FakeProcessingRepository:
    def __init__(self, references=()) -> None:
        self.references = tuple(references)

    def load_run(self, project_id: str, run_id: str):
        assert project_id == PROJECT_ID
        assert run_id == RUN_ID
        event = SimpleNamespace(
            event_type="artifact_published",
            attempt_id=ATTEMPT_ID,
            artifact_references=self.references,
        )
        return SimpleNamespace(events=(event,))


def service(references=()) -> ProjectDashboardService:
    return ProjectDashboardService(
        workspace=object(),
        source_registry=object(),
        processing_summary_service=object(),
        processing_repository=FakeProcessingRepository(references),
        coverage_service=object(),
        human_review_repository=object(),
    )


def summary(*, attempt_id: str = ATTEMPT_ID):
    return SimpleNamespace(
        current_processing_run_id=RUN_ID,
        latest_attempt_id=attempt_id,
        superseded_run_ids=(),
    )


def test_current_publication_adds_primary_and_supporting_artifacts():
    references = (
        artifact(
            "review_reports",
            "REVIEW-ATT-000001-0001",
            "ingestion_review_report.md",
        ),
        artifact(
            "run_summaries",
            "SUMMARY-ATT-000001-0001",
            "team_agentic_ingestion_run_summary.md",
        ),
        artifact(
            "consensus_reports",
            "CONS-ATT-000001-0001",
            "01_legacy_interpretation/team_consensus.md",
        ),
        artifact(
            "agent_outputs",
            "AGOUT-ATT-000001-0001",
            "01_legacy_interpretation/interpreter.json",
        ),
    )
    evidence = service(references)._source_processing_row_evidence(
        source(),
        summary(),
    )
    types = {item.reference_type for item in evidence}
    assert "ingestion_review_report" in types
    assert "ingestion_run_summary" in types
    assert "ingestion_consensus_report" in types
    assert "ingestion_agent_output" in types


def test_review_report_is_direct_evidence_with_friendly_label():
    reference = artifact(
        "review_reports",
        "REVIEW-ATT-000001-0001",
        "ingestion_review_report.md",
    )
    evidence = service((reference,))._source_processing_row_evidence(
        source(),
        summary(),
    )
    selected = next(
        item
        for item in evidence
        if item.reference_type == "ingestion_review_report"
    )
    assert selected.display_label == "Ingestion Review Report"
    assert selected.relationship == "requires_human_review"
    assert selected.evidence_role == "direct"
    assert selected.media_type == "text/markdown"


def test_publication_for_an_old_attempt_is_not_shown():
    reference = artifact(
        "review_reports",
        "REVIEW-ATT-000001-0001",
        "ingestion_review_report.md",
    )
    evidence = service((reference,))._source_processing_row_evidence(
        source(),
        summary(attempt_id="ATT-000002"),
    )
    assert all(
        item.reference_type != "ingestion_review_report"
        for item in evidence
    )


def evidence_reference(reference_type: str, label: str) -> EvidenceReference:
    return EvidenceReference(
        project_id=PROJECT_ID,
        reference_type=reference_type,
        reference_id=f"{reference_type}-1",
        display_label=label,
        repository_relative_path=(
            f"data/projects/{PROJECT_ID}/{reference_type}.md"
        ),
        content_fingerprint=SHA,
        media_type="text/markdown",
        source_role="engineering_source",
        relationship="supports",
        evidence_role="direct",
    )


def test_source_evidence_is_partitioned_by_user_purpose():
    navigation = EvidenceNavigation(
        mode="chooser",
        references=(
            evidence_reference(
                "ingestion_review_report",
                "Ingestion Review Report",
            ),
            evidence_reference("ingestion_run_summary", "Run Summary"),
            evidence_reference(
                "ingestion_consensus_report",
                "Consensus Report",
            ),
            evidence_reference("ingestion_agent_output", "Agent Output"),
            evidence_reference("source_manifest", "Source Manifest"),
        ),
    )
    sections = source_evidence_sections(navigation)
    assert len(sections.review_reports) == 1
    assert len(sections.run_summaries) == 1
    assert len(sections.consensus_reports) == 1
    assert len(sections.agent_outputs) == 1
    assert len(sections.technical_evidence) == 1


class FakeStreamlit:
    def __init__(self) -> None:
        self.session_state = {}
        self.calls = []

    def container(self, *, border=False):
        self.calls.append(("container", border))
        return nullcontext()

    def expander(self, label, *, expanded=False):
        self.calls.append(("expander", label, expanded))
        return nullcontext()

    def columns(self, spec):
        count = spec if isinstance(spec, int) else len(spec)
        return tuple(nullcontext() for _ in range(count))

    def markdown(self, text, **kwargs):
        self.calls.append(("markdown", text))

    def write(self, text):
        self.calls.append(("write", text))

    def caption(self, text):
        self.calls.append(("caption", text))

    def error(self, text):
        self.calls.append(("error", text))

    def button(self, label, *, key, help=None):
        self.calls.append(("button", label, key))
        return False


class UnusedViewer:
    def open(self, reference):
        raise AssertionError("Viewer must not open without a button click.")


def test_pending_review_has_one_explicit_primary_action():
    navigation = EvidenceNavigation(
        mode="chooser",
        references=(
            evidence_reference(
                "ingestion_review_report",
                "Ingestion Review Report",
            ),
            evidence_reference("ingestion_run_summary", "Run Summary"),
            evidence_reference("source_manifest", "Source Manifest"),
        ),
    )
    row = SimpleNamespace(
        pending_review=True,
        evidence=navigation,
    )
    st = FakeStreamlit()
    render_source_evidence_sections(
        st,
        row,
        UnusedViewer(),
        key_prefix="source_SRC-000002",
    )
    labels = [call[1] for call in st.calls if call[0] == "button"]
    assert labels.count("Open review report") == 1
    expanders = [call[1] for call in st.calls if call[0] == "expander"]
    assert "Supporting evidence (1)" in expanders
    assert "Technical evidence (1)" in expanders


class RadioStreamlit:
    def __init__(self) -> None:
        self.session_state = {
            "project_dashboard.active_view": "sources",
            "project_dashboard.view_selector": "sources",
        }
        self.kwargs = None

    def radio(self, label, **kwargs):
        self.kwargs = kwargs
        return self.session_state[kwargs["key"]]


def test_dashboard_selector_does_not_mix_session_state_and_index_default():
    st = RadioStreamlit()
    assert render_view_selector(st) == "sources"
    assert "index" not in st.kwargs
