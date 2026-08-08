"""Tests for G6.4c Reopening UI."""

from __future__ import annotations

from types import SimpleNamespace

from app.human_review_finalization_ui import (
    render_review_finalization_ui,
)


class FakeStreamlit:
    def __init__(
        self,
        *,
        clicked_keys=(),
        text_values=None,
        checkbox_values=None,
    ):
        self.clicked_keys = set(clicked_keys)
        self.text_values = dict(text_values or {})
        self.checkbox_values = dict(
            checkbox_values or {}
        )
        self.calls = []
        self.rerun_count = 0

    def subheader(self, text):
        self.calls.append(("subheader", text))

    def caption(self, text):
        self.calls.append(("caption", text))

    def info(self, text):
        self.calls.append(("info", text))

    def warning(self, text):
        self.calls.append(("warning", text))

    def error(self, text):
        self.calls.append(("error", text))

    def success(self, text):
        self.calls.append(("success", text))

    def table(self, rows):
        self.calls.append(("table", rows))

    def markdown(self, text):
        self.calls.append(("markdown", text))

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

    def checkbox(
        self,
        label,
        *,
        value,
        key,
    ):
        self.calls.append(("checkbox", label, key))
        return self.checkbox_values.get(key, value)

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


def _workspace():
    return SimpleNamespace(
        document=SimpleNamespace(
            review_document_id="RVD-000001",
        ),
        version=SimpleNamespace(
            review_document_version_id="RVV-000001",
            version_state="finalized",
        ),
    )


def _artifact_set():
    return SimpleNamespace(
        reviewed_document=SimpleNamespace(
            review_revision_id="RVR-000001",
            finalization_decision_id="HRD-000001",
            reviewer_identity="Reviewer A",
            decision_at="2026-08-08T12:00:00Z",
            finalized_at="2026-08-08T12:05:00Z",
        ),
        artifacts=(
            SimpleNamespace(
                filename="reviewed_document.json",
                content=b"{}\n",
                byte_fingerprint="a" * 64,
            ),
            SimpleNamespace(
                filename="effective_decisions.json",
                content=b"{}\n",
                byte_fingerprint="b" * 64,
            ),
            SimpleNamespace(
                filename="reviewed_report.md",
                content=b"# Final\n",
                byte_fingerprint="c" * 64,
            ),
        ),
        artifact_set_fingerprint="d" * 64,
    )


class FakeService:
    def __init__(self):
        self.reopen_calls = []

    def finalized_artifact_set(self, *args):
        return _artifact_set()

    def reopen_review_version(
        self,
        *args,
        reopen_reason,
        actor_identity,
    ):
        self.reopen_calls.append(
            (
                args,
                reopen_reason,
                actor_identity,
            )
        )
        return SimpleNamespace(
            version=SimpleNamespace(
                review_document_version_id="RVV-000002",
            ),
            initial_revision=SimpleNamespace(
                review_revision_id="RVR-000002",
            ),
            review_item_id_mapping=(
                ("RIT-000001", "RIT-000002"),
            ),
        )


def test_reopen_requires_reason_before_service_command():
    st = FakeStreamlit(
        clicked_keys={
            "human_review_finalization.reopen.RVV-000001"
        },
        checkbox_values={
            "human_review_finalization.reopen_exact."
            "RVV-000001": True,
        },
    )
    service = FakeService()

    render_review_finalization_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_workspace(),
        reviewer_identity="Reviewer A",
    )

    assert service.reopen_calls == []
    assert any(
        call[0] == "error"
        and "reason" in call[1]
        for call in st.calls
    )


def test_reopen_requires_explicit_confirmation():
    st = FakeStreamlit(
        clicked_keys={
            "human_review_finalization.reopen.RVV-000001"
        },
        text_values={
            "human_review_finalization.reopen_reason."
            "RVV-000001": "Clarify requirement.",
        },
    )
    service = FakeService()

    render_review_finalization_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_workspace(),
        reviewer_identity="Reviewer A",
    )

    assert service.reopen_calls == []
    assert any(
        call[0] == "error"
        and "explicitly confirmed" in call[1]
        for call in st.calls
    )


def test_reopen_calls_service_with_exact_predecessor_actor_and_reason():
    st = FakeStreamlit(
        clicked_keys={
            "human_review_finalization.reopen.RVV-000001"
        },
        text_values={
            "human_review_finalization.reopen_reason."
            "RVV-000001": "Clarify requirement.",
        },
        checkbox_values={
            "human_review_finalization.reopen_exact."
            "RVV-000001": True,
        },
    )
    service = FakeService()

    render_review_finalization_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_workspace(),
        reviewer_identity="Reviewer A",
    )

    assert service.reopen_calls == [
        (
            (
                "123456",
                "RVD-000001",
                "RVV-000001",
            ),
            "Clarify requirement.",
            "Reviewer A",
        )
    ]
    assert st.rerun_count == 1
    assert any(
        call[0] == "success"
        and "RVV-000002" in call[1]
        and "RVR-000002" in call[1]
        for call in st.calls
    )
