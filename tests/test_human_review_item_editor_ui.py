"""Tests for the G6.3b2 Review Item editor UI adapter."""

from __future__ import annotations

from types import SimpleNamespace

from modules.project_processing import ProcessingArtifactReference
from modules.review_workspace.types import (
    ReviewItemContent,
    ReviewProposalReference,
)

from app.human_review_item_editor_ui import (
    _csv_tuple,
    _items_for_section,
    render_review_item_editor,
)


class FakeStreamlit:
    def __init__(
        self,
        *,
        clicked_keys=(),
        text_values=None,
        multiselect_values=None,
    ):
        self.clicked_keys = set(clicked_keys)
        self.text_values = dict(text_values or {})
        self.multiselect_values = dict(
            multiselect_values or {}
        )
        self.calls = []
        self.rerun_count = 0

    def radio(
        self,
        label,
        *,
        options,
        index,
        format_func,
        horizontal,
        key,
    ):
        self.calls.append(("radio", label, key))
        return options[index]

    def subheader(self, text):
        self.calls.append(("subheader", text))

    def caption(self, text):
        self.calls.append(("caption", text))

    def markdown(self, text):
        self.calls.append(("markdown", text))

    def table(self, rows):
        self.calls.append(("table", rows))

    def info(self, text):
        self.calls.append(("info", text))

    def warning(self, text):
        self.calls.append(("warning", text))

    def error(self, text):
        self.calls.append(("error", text))

    def success(self, text):
        self.calls.append(("success", text))

    def text_input(
        self,
        label,
        *,
        value,
        key,
        help=None,
    ):
        self.calls.append(("text_input", label, key))
        return self.text_values.get(key, value)

    def text_area(
        self,
        label,
        *,
        value,
        key,
    ):
        self.calls.append(("text_area", label, key))
        return self.text_values.get(key, value)

    def selectbox(
        self,
        label,
        *,
        options,
        index,
        key,
    ):
        self.calls.append(("selectbox", label, key))
        return options[index]

    def multiselect(
        self,
        label,
        *,
        options,
        default,
        key,
    ):
        self.calls.append(("multiselect", label, key))
        return self.multiselect_values.get(
            key,
            tuple(default),
        )

    def button(
        self,
        label,
        *,
        key,
        type=None,
    ):
        self.calls.append(("button", label, key))
        return key in self.clicked_keys

    def rerun(self):
        self.rerun_count += 1


def _content(text="Current statement."):
    return ReviewItemContent(
        title="Current title",
        primary_text=text,
        description="Current description.",
        information_type="requirement",
        modality=None,
        epistemic_status=None,
        human_rationale=None,
        human_confidence=None,
        relationship_representation=None,
    )


def _item(
    *,
    item_id="RIT-000001",
    section="elements",
    outcome="open",
    proposals=(),
):
    return SimpleNamespace(
        review_item_id=item_id,
        review_item_kind=(
            "element"
            if section == "elements"
            else "open_question"
        ),
        stable_subject_key=f"subject:{item_id.lower()}",
        section=section,
        lineage_operation="original",
        effective_review_outcome=outcome,
        item_content_fingerprint="a" * 64,
        proposal_references=tuple(proposals),
        source_evidence_references=(),
        consensus_evidence_references=(),
        dimension_selections=(),
        current_content=_content(),
    )


def _proposal_reference():
    return ReviewProposalReference(
        artifact_reference=ProcessingArtifactReference(
            artifact_type="agent_outputs",
            artifact_id="AGENT-001",
            content_fingerprint="a" * 64,
            repository_relative_path=(
                "data/projects/123456/runs/RUN-000001/"
                "artifacts/agent_outputs/AGENT-001.json"
            ),
        ),
        agent_id="AGENT-001",
        persona_id="systems_engineer",
        proposal_id="CAND-001",
        proposal_content_fingerprint="b" * 64,
        original_report_locator=(
            "report:recognized_elements/"
            "requirement:example"
        ),
        review_state="available",
    )


def _detail():
    return SimpleNamespace(
        proposal_id="CAND-001",
        proposal_key="AGENT-001:CAND-001",
        agent_id="AGENT-001",
        persona_id="systems_engineer",
        proposed_title="Proposal title",
        proposed_primary_text="Proposal statement.",
        proposed_description="Proposal rationale.",
        proposed_information_type="requirement",
        framework_assignment_values=(),
        source_assignments=(),
        rationale="Proposal rationale.",
        confidence="high",
        generation_readiness="ready",
        review_state="available",
    )


def _view(item):
    return SimpleNamespace(
        document=SimpleNamespace(
            review_document_id="RVD-000001",
        ),
        version=SimpleNamespace(
            review_document_version_id="RVV-000001",
            version_state="draft",
        ),
        revision=SimpleNamespace(
            review_revision_id="RVR-000001",
            review_items=(item,),
        ),
    )


class FakeService:
    def __init__(self):
        self.accept_calls = []
        self.reject_calls = []
        self.save_calls = []

    def review_filter_facts(self, *args):
        return ()

    def proposal_details(self, *args):
        return (_detail(),)

    def accept_proposal(self, *args, **kwargs):
        self.accept_calls.append((args, kwargs))

    def reject_proposal(self, *args, **kwargs):
        self.reject_calls.append((args, kwargs))

    def save_item_review(self, *args, **kwargs):
        self.save_calls.append((args, kwargs))


def test_primary_sections_separate_rejected_content():
    items = (
        _item(item_id="RIT-000001", outcome="open"),
        _item(item_id="RIT-000002", outcome="rejected"),
        _item(
            item_id="RIT-000003",
            section="open_questions",
            outcome="unresolved",
        ),
    )

    assert tuple(
        item.review_item_id
        for item in _items_for_section(
            items,
            "elements",
        )
    ) == ("RIT-000001",)

    assert tuple(
        item.review_item_id
        for item in _items_for_section(
            items,
            "rejected_content",
        )
    ) == ("RIT-000002",)


def test_csv_values_are_trimmed_deduplicated_and_ordered():
    assert _csv_tuple(
        " System Requirements, source-a, "
        "System Requirements "
    ) == (
        "System Requirements",
        "source-a",
    )


def test_accept_proposal_ui_calls_only_accept_command():
    reference = _proposal_reference()
    item = _item(proposals=(reference,))
    st = FakeStreamlit(
        clicked_keys={
            "human_review_item_editor.accept."
            "RIT-000001.AGENT-001:CAND-001"
        }
    )
    service = FakeService()

    render_review_item_editor(
        st,
        service=service,
        project_id="123456",
        workspace_view=_view(item),
        reviewer_identity="Reviewer A",
    )

    assert len(service.accept_calls) == 1
    assert service.reject_calls == []
    assert service.save_calls == []
    request = service.accept_calls[0][1]["request"]
    assert request.proposal_key == "AGENT-001:CAND-001"
    assert request.expected_revision_id == "RVR-000001"
    assert st.rerun_count == 1


def test_reject_proposal_requires_rationale_before_command():
    reference = _proposal_reference()
    item = _item(proposals=(reference,))
    st = FakeStreamlit(
        clicked_keys={
            "human_review_item_editor.reject_proposal."
            "RIT-000001.AGENT-001:CAND-001"
        }
    )
    service = FakeService()

    render_review_item_editor(
        st,
        service=service,
        project_id="123456",
        workspace_view=_view(item),
        reviewer_identity="Reviewer A",
    )

    assert service.reject_calls == []
    assert any(
        call[0] == "error"
        and "rationale" in call[1]
        for call in st.calls
    )


def test_edit_and_accept_uses_item_edit_command_with_selected_proposal():
    reference = _proposal_reference()
    item = _item(proposals=(reference,))
    key = (
        "human_review_item_editor.edit."
        "RIT-000001.AGENT-001:CAND-001"
    )
    st = FakeStreamlit(
        clicked_keys={f"{key}.submit"},
        text_values={
            f"{key}.statement": "Human refined statement.",
        },
    )
    service = FakeService()

    render_review_item_editor(
        st,
        service=service,
        project_id="123456",
        workspace_view=_view(item),
        reviewer_identity="Reviewer A",
    )

    assert len(service.save_calls) == 1
    request = service.save_calls[0][1]["request"]
    assert request.review_outcome == "accepted_with_modification"
    assert request.selected_proposal_keys == (
        "AGENT-001:CAND-001",
    )
    assert (
        request.updated_content.primary_text
        == "Human refined statement."
    )
