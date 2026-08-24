"""R4c.5b.3 routing test for the primary Human Review editor."""

from types import SimpleNamespace

import app.human_review_item_editor_ui as editor


def test_subject_review_payload_routes_before_legacy_editor(monkeypatch):
    calls = []

    class Service:
        def subject_review_bundle_payload(self, *args):
            return {
                "canonical_subject_ids": [],
                "cards": [],
            }

    def fake_renderer(*args, **kwargs):
        calls.append(kwargs["payload"])

    monkeypatch.setattr(
        editor,
        "render_subject_review_editor",
        fake_renderer,
    )

    st = SimpleNamespace(session_state={})
    workspace = SimpleNamespace(
        version=SimpleNamespace(
            version_state="draft",
            review_document_version_id="RVV-000001",
        ),
        document=SimpleNamespace(
            review_document_id="RVD-000001",
        ),
        revision=SimpleNamespace(
            review_items=(),
        ),
    )

    editor.render_review_item_editor(
        st,
        service=Service(),
        project_id="396272",
        workspace_view=workspace,
        reviewer_identity="reviewer",
    )

    assert len(calls) == 1
