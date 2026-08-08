"""Tests for G6.4b Finalization UI."""

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
        select_values=None,
        text_values=None,
        checkbox_values=None,
    ):
        self.clicked_keys = set(clicked_keys)
        self.select_values = dict(select_values or {})
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

    def selectbox(
        self,
        label,
        *,
        options,
        index,
        key,
    ):
        self.calls.append(
            ("selectbox", label, tuple(options), key)
        )
        return self.select_values.get(
            key,
            options[index],
        )

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


def _workspace(*, state="draft"):
    return SimpleNamespace(
        document=SimpleNamespace(
            review_document_id="RVD-000001",
        ),
        version=SimpleNamespace(
            review_document_version_id="RVV-000001",
            version_state=state,
        ),
    )


def _preview(
    *,
    eligible,
    confirmed=False,
    blocking=(),
):
    return SimpleNamespace(
        assessment=SimpleNamespace(
            review_revision_id="RVR-000001",
            blocking_issue_codes=tuple(blocking),
            item_snapshots=(
                SimpleNamespace(
                    review_item_id="RIT-000001",
                    review_item_kind="element",
                    effective_review_outcome=(
                        "accepted_with_modification"
                        if eligible
                        else "open"
                    ),
                    relationship_validation_status=None,
                    item_content_fingerprint="a" * 64,
                ),
            ),
            validation_fingerprint="b" * 64,
        ),
        eligible_for_confirmation=eligible,
        latest_exact_decision_id=(
            "HRD-000001" if confirmed else None
        ),
        latest_exact_decision=(
            "confirm" if confirmed else None
        ),
        exact_confirmation_decision_id=(
            "HRD-000001" if confirmed else None
        ),
        has_exact_confirmation=confirmed,
        can_finalize=(eligible and confirmed),
    )


class FakeService:
    def __init__(
        self,
        *,
        preview=None,
        artifact_set=None,
    ):
        self.preview = preview
        self.artifact_set = artifact_set
        self.record_calls = []
        self.finalize_calls = []
        self.artifact_calls = []

    def finalization_preview(self, *args):
        return self.preview

    def record_finalization_decision(
        self,
        *args,
        decision,
        reviewer_identity,
        rationale=None,
    ):
        self.record_calls.append(
            (
                args,
                decision,
                reviewer_identity,
                rationale,
            )
        )
        return SimpleNamespace(
            human_review_decision_id="HRD-000001",
        )

    def finalize_review_version(self, *args):
        self.finalize_calls.append(args)
        return SimpleNamespace(
            finalization_decision_id="HRD-000001",
        )

    def finalized_artifact_set(self, *args):
        self.artifact_calls.append(args)
        return self.artifact_set


def _artifact_set():
    artifacts = (
        SimpleNamespace(
            filename="reviewed_document.json",
            content=b'{"review":"final"}\n',
            byte_fingerprint="c" * 64,
        ),
        SimpleNamespace(
            filename="effective_decisions.json",
            content=b'{"decisions":[]}\n',
            byte_fingerprint="d" * 64,
        ),
        SimpleNamespace(
            filename="reviewed_report.md",
            content=b"# Reviewed Report\n\nFinal.\n",
            byte_fingerprint="e" * 64,
        ),
    )
    return SimpleNamespace(
        reviewed_document=SimpleNamespace(
            review_revision_id="RVR-000001",
            finalization_decision_id="HRD-000001",
            reviewer_identity="Reviewer A",
            decision_at="2026-08-08T12:00:00Z",
            finalized_at="2026-08-08T12:05:00Z",
        ),
        artifacts=artifacts,
        artifact_set_fingerprint="f" * 64,
    )


def test_blocked_draft_shows_findings_and_does_not_offer_confirm():
    st = FakeStreamlit()
    service = FakeService(
        preview=_preview(
            eligible=False,
            blocking=("review_item_open:RIT-000001",),
        )
    )

    render_review_finalization_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_workspace(),
        reviewer_identity="Reviewer A",
    )

    decision_calls = [
        call
        for call in st.calls
        if (
            call[0] == "selectbox"
            and call[1] == "Human Review Decision"
        )
    ]
    assert decision_calls[0][2] == (
        "request_changes",
        "reject",
    )
    assert any(
        call[0] == "table"
        and call[1]
        and call[1][0].get("Blocking finding")
        == "review_item_open:RIT-000001"
        for call in st.calls
    )


def test_confirm_requires_explicit_checkbox_before_recording():
    key = (
        "human_review_finalization.confirm_exact."
        "RVV-000001"
    )
    st = FakeStreamlit(
        clicked_keys={
            "human_review_finalization.record.RVV-000001"
        },
        checkbox_values={key: False},
    )
    service = FakeService(
        preview=_preview(eligible=True)
    )

    render_review_finalization_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_workspace(),
        reviewer_identity="Reviewer A",
    )

    assert service.record_calls == []
    assert any(
        call[0] == "error"
        and "explicitly checked" in call[1]
        for call in st.calls
    )


def test_explicit_confirm_records_human_review_decision_only():
    confirm_key = (
        "human_review_finalization.confirm_exact."
        "RVV-000001"
    )
    st = FakeStreamlit(
        clicked_keys={
            "human_review_finalization.record.RVV-000001"
        },
        checkbox_values={confirm_key: True},
    )
    service = FakeService(
        preview=_preview(eligible=True)
    )

    render_review_finalization_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_workspace(),
        reviewer_identity="Reviewer A",
    )

    assert len(service.record_calls) == 1
    assert service.record_calls[0][1:] == (
        "confirm",
        "Reviewer A",
        None,
    )
    assert service.finalize_calls == []
    assert st.rerun_count == 1


def test_finalization_is_separate_confirmed_action():
    finalize_key = (
        "human_review_finalization.finalize_exact."
        "RVV-000001"
    )
    st = FakeStreamlit(
        clicked_keys={
            "human_review_finalization.finalize.RVV-000001"
        },
        checkbox_values={
            "human_review_finalization.confirm_exact."
            "RVV-000001": False,
            finalize_key: True,
        },
    )
    service = FakeService(
        preview=_preview(
            eligible=True,
            confirmed=True,
        )
    )

    render_review_finalization_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_workspace(),
        reviewer_identity="Reviewer A",
    )

    assert len(service.finalize_calls) == 1
    assert service.record_calls == []
    assert st.rerun_count == 1


def test_finalized_view_loads_exact_artifact_set_and_renders_report():
    st = FakeStreamlit()
    service = FakeService(
        artifact_set=_artifact_set()
    )

    render_review_finalization_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_workspace(
            state="finalized",
        ),
        reviewer_identity="Reviewer A",
    )

    assert service.artifact_calls == [
        (
            "123456",
            "RVD-000001",
            "RVV-000001",
        )
    ]

    artifact_tables = [
        call[1]
        for call in st.calls
        if (
            call[0] == "table"
            and call[1]
            and "Artifact" in call[1][0]
        )
    ]
    assert tuple(
        row["Artifact"]
        for row in artifact_tables[0]
    ) == (
        "reviewed_document.json",
        "effective_decisions.json",
        "reviewed_report.md",
    )

    assert (
        "markdown",
        "# Reviewed Report\n\nFinal.\n",
    ) in st.calls
