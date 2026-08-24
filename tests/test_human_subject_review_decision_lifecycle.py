from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.human_subject_review_ui import (
    _render_relationships,
    _render_subject_card,
    _visible_in_mode,
    build_subject_review_item_request,
)
from modules.review_workspace.types import ReviewItemContent


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeStreamlit:
    def __init__(self):
        self.session_state = {}
        self.calls = []
        self.rerun_count = 0

    def container(self, border=False):
        return _Context()

    def expander(self, label, expanded=False):
        self.calls.append(("expander", label, expanded))
        return _Context()

    def columns(self, count):
        return tuple(_Context() for _ in range(count))

    def subheader(self, value):
        self.calls.append(("subheader", value))

    def caption(self, value):
        self.calls.append(("caption", value))

    def markdown(self, value):
        self.calls.append(("markdown", value))

    def table(self, value):
        self.calls.append(("table", value))

    def warning(self, value):
        self.calls.append(("warning", value))

    def success(self, value):
        self.calls.append(("success", value))

    def error(self, value):
        self.calls.append(("error", value))

    def info(self, value):
        self.calls.append(("info", value))

    def button(self, label, *, key, type=None):
        self.calls.append(("button", label, key, type))
        return False

    def text_input(self, label, *, value, key, help=None):
        self.calls.append(("text_input", label, key))
        return value

    def text_area(self, label, *, value, key):
        self.calls.append(("text_area", label, key))
        return value

    def selectbox(self, label, *, options, index, key):
        self.calls.append(("selectbox", label, key))
        return options[index]

    def rerun(self):
        self.rerun_count += 1


def _content(*, information_type="interface"):
    return ReviewItemContent(
        title="Example",
        primary_text="The remote expert uses a separate client application.",
        description=None,
        information_type=information_type,
        modality="descriptive",
        epistemic_status="explicit",
        human_rationale=None,
        human_confidence=None,
        relationship_representation=None,
    )


def _item(*, outcome="open", information_type="interface"):
    return SimpleNamespace(
        review_document_version_id="RVV-000001",
        review_item_id="RIT-000001",
        item_content_fingerprint="a" * 64,
        effective_review_outcome=outcome,
        review_item_kind="element",
        current_content=_content(information_type=information_type),
    )


def _workspace_view():
    return SimpleNamespace(
        document=SimpleNamespace(review_document_id="RVD-000001"),
        version=SimpleNamespace(review_document_version_id="RVV-000001"),
        revision=SimpleNamespace(review_revision_id="RVR-000001"),
    )


def _card():
    return {
        "canonical_subject_id": "SUBJ-000007",
        "canonical_label": "separate client application",
        "classification_review_attention_required": True,
        "relationship_review_attention_required": True,
        "information_type": {
            "selected_value": "interface",
            "confidence": "medium",
            "consensus_level": "majority",
            "supporting_personas": ["p1", "p2"],
            "value_distribution": [
                {"value": "interface", "supporting_personas": ["p1", "p2"]},
                {"value": "physical_element", "supporting_personas": ["p3"]},
            ],
        },
        "statement_modality": {
            "selected_value": "descriptive",
            "confidence": "high",
            "consensus_level": "unanimous",
            "supporting_personas": ["p1", "p2", "p3"],
            "value_distribution": [
                {"value": "descriptive", "supporting_personas": ["p1", "p2", "p3"]},
            ],
        },
        "epistemic_class": {
            "selected_value": "explicit",
            "confidence": "high",
            "consensus_level": "unanimous",
            "supporting_personas": ["p1", "p2", "p3"],
            "value_distribution": [
                {"value": "explicit", "supporting_personas": ["p1", "p2", "p3"]},
            ],
        },
        "mentions": [],
        "persona_interpretations": [],
        "relationships": [],
    }


def test_plain_accept_is_accepted_as_generated():
    item = _item()
    request = build_subject_review_item_request(
        item,
        action="accept",
        statement=item.current_content.primary_text,
        information_type=item.current_content.information_type,
        statement_modality=item.current_content.modality,
        epistemic_class=item.current_content.epistemic_status,
        rationale=None,
    )
    assert request.review_outcome == "accepted_as_generated"


def test_changed_accept_requires_rationale_and_records_modification():
    item = _item()
    with pytest.raises(ValueError, match="rationale is required"):
        build_subject_review_item_request(
            item,
            action="accept",
            statement=item.current_content.primary_text,
            information_type="logical_element",
            statement_modality=item.current_content.modality,
            epistemic_class=item.current_content.epistemic_status,
            rationale=None,
        )

    request = build_subject_review_item_request(
        item,
        action="accept",
        statement=item.current_content.primary_text,
        information_type="logical_element",
        statement_modality=item.current_content.modality,
        epistemic_class=item.current_content.epistemic_status,
        rationale="Client application is treated as a logical element.",
    )
    assert request.review_outcome == "accepted_with_modification"
    assert request.updated_content.information_type == "logical_element"


def test_pending_and_reviewed_views_include_relationship_decision_state():
    item = _item(outcome="accepted_as_generated")
    card = _card()
    card["relationships"] = [
        {
            "direction": "outgoing",
            "source_subject_id": "SUBJ-000007",
            "relationship_kind": "uses",
            "target_subject_id": "SUBJ-000005",
        }
    ]
    key = ("SUBJ-000007", "uses", "SUBJ-000005")

    assert _visible_in_mode(
        item,
        card,
        "pending",
        relationship_decisions={},
    )
    assert not _visible_in_mode(
        item,
        card,
        "pending",
        relationship_decisions={key: SimpleNamespace()},
    )
    assert _visible_in_mode(
        item,
        card,
        "reviewed",
        relationship_decisions={key: SimpleNamespace()},
    )


def test_decided_subject_shows_reopen_without_live_decision_buttons():
    st = FakeStreamlit()
    item = _item(outcome="accepted_as_generated")

    _render_subject_card(
        st,
        service=SimpleNamespace(),
        project_id="120412",
        workspace_view=_workspace_view(),
        item=item,
        card=_card(),
        reviewer_identity="MZ",
        technical=False,
        cards_by_id={"SUBJ-000007": _card()},
        relationship_decisions={},
        view_mode="reviewed",
    )

    labels = [call[1] for call in st.calls if call[0] == "button"]
    assert "Reopen Subject decision" in labels
    assert "Accept" not in labels
    assert "Defer" not in labels
    assert "Reject" not in labels


def test_decided_relationship_shows_reopen_without_decision_buttons():
    st = FakeStreamlit()
    relation = {
        "direction": "outgoing",
        "source_subject_id": "SUBJ-000007",
        "relationship_kind": "uses",
        "target_subject_id": "SUBJ-000005",
        "confidence": "low",
        "supporting_personas": ["p1"],
        "review_attention_required": True,
        "statement_variants": [],
    }
    card = _card()
    card["relationships"] = [relation]
    key = ("SUBJ-000007", "uses", "SUBJ-000005")
    current = SimpleNamespace(
        source_subject_id=key[0],
        relationship_kind=key[1],
        target_subject_id=key[2],
        outcome="accepted",
        rationale=None,
    )

    _render_relationships(
        st,
        service=SimpleNamespace(),
        project_id="120412",
        workspace_view=_workspace_view(),
        card=card,
        reviewer_identity="MZ",
        cards_by_id={
            "SUBJ-000007": card,
            "SUBJ-000005": {
                "canonical_subject_id": "SUBJ-000005",
                "canonical_label": "remote expert",
            },
        },
        decisions_by_key={key: current},
        view_mode="reviewed",
    )

    labels = [call[1] for call in st.calls if call[0] == "button"]
    assert labels == ["Reopen relation decision"]
    markdown = [call[1] for call in st.calls if call[0] == "markdown"]
    assert any(
        "separate client application — uses → remote expert" in value
        for value in markdown
    )
