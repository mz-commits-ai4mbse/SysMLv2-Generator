"""Tests for G6.5 Approved Input promotion and traceability UI."""

from __future__ import annotations

from types import SimpleNamespace

from app.human_review_promotion_ui import (
    render_approved_input_promotion_ui,
)


class FakeStreamlit:
    def __init__(
        self,
        *,
        clicked_keys=(),
        checkbox_values=None,
    ):
        self.clicked_keys = set(clicked_keys)
        self.checkbox_values = dict(
            checkbox_values or {}
        )
        self.calls = []

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


def _workspace(*, state="finalized"):
    return SimpleNamespace(
        document=SimpleNamespace(
            review_document_id="RVD-000001",
        ),
        version=SimpleNamespace(
            review_document_version_id="RVV-000001",
            version_state=state,
        ),
    )


def _assessment(*, eligible=True):
    return SimpleNamespace(
        project_id="123456",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        finalized_artifact_set_fingerprint="a" * 64,
        finalization_decision_id="HRD-000001",
        finalization_decision_fingerprint="b" * 64,
        finalization_validation_fingerprint="c" * 64,
        item_assessments=(
            SimpleNamespace(
                review_item_id="RIT-000001",
                review_item_kind="element",
                effective_review_outcome=(
                    "accepted_with_modification"
                ),
                approved_input_kind="element_statement",
                eligible_for_promotion=True,
                reason_codes=(),
                review_item_fingerprint="d" * 64,
            ),
        ),
        blocking_issue_codes=(
            ()
            if eligible
            else ("source_fingerprint_mismatch",)
        ),
        eligible_for_promotion=eligible,
        promotable_item_ids=(
            ("RIT-000001",)
            if eligible
            else ()
        ),
    )


def _event():
    return SimpleNamespace(
        approved_input_event_id="AIE-000001",
        approved_input_id="AIN-000001",
        event_type="superseded",
        previous_authority_state="active",
        next_authority_state="superseded",
        reason_code="review_successor_changed",
        rationale=None,
        actor_identity="promotion-service",
        successor_approved_input_id="AIN-000002",
        causal_review_document_version_id="RVV-000002",
        causal_review_revision_id="RVR-000002",
        causal_finalization_decision_id="HRD-000002",
        occurred_at="2026-08-08T14:00:00Z",
        event_fingerprint="e" * 64,
    )


def _trace(
    approved_input_id="AIN-000001",
    *,
    authority_state="active",
    events=(),
):
    return SimpleNamespace(
        approved_input_id=approved_input_id,
        authority_state=authority_state,
        approved_input_kind="element_statement",
        stable_subject_key="requirement:traceability",
        canonical_title="Preserve traceability",
        canonical_primary_text="The system shall preserve traceability.",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        review_item_id="RIT-000001",
        review_item_fingerprint="f" * 64,
        finalized_artifact_set_fingerprint="a" * 64,
        finalization_decision_id="HRD-000001",
        finalization_decision_fingerprint="b" * 64,
        finalization_validation_fingerprint="c" * 64,
        source_id="SRC-000001",
        processing_run_id="RUN-000001",
        attempt_id="ATT-000001",
        primary_artifact_id="ART-000001",
        supporting_artifact_ids=("ART-000002",),
        proposal_references=("AGENT-001:CAND-001",),
        created_at="2026-08-08T13:00:00Z",
        manifest_content_fingerprint="1" * 64,
        latest_event_fingerprint=(
            events[-1].event_fingerprint
            if events
            else None
        ),
        lifecycle_events=tuple(events),
        is_active=(authority_state == "active"),
    )


class FakeService:
    def __init__(
        self,
        *,
        assessment=None,
        traceability=None,
        promotion_result=None,
    ):
        self.assessment = (
            assessment
            if assessment is not None
            else _assessment()
        )
        self.traceability = tuple(
            traceability
            if traceability is not None
            else (_trace(),)
        )
        self.promotion_result = promotion_result
        self.promote_calls = []

    def promotion_preview(self, *args):
        return self.assessment

    def approved_input_traceability(self, *args):
        return self.traceability

    def promote_review_version(self, *args):
        self.promote_calls.append(args)
        return self.promotion_result


def test_draft_workspace_does_not_offer_promotion():
    st = FakeStreamlit()
    service = FakeService()

    render_approved_input_promotion_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_workspace(state="draft"),
    )

    assert st.calls == []


def test_blocked_promotion_shows_reason_and_no_promote_button():
    st = FakeStreamlit()
    service = FakeService(
        assessment=_assessment(
            eligible=False,
        )
    )

    render_approved_input_promotion_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_workspace(),
    )

    assert any(
        call[0] == "table"
        and call[1]
        and call[1][0].get(
            "Promotion blocking finding"
        )
        == "source_fingerprint_mismatch"
        for call in st.calls
    )

    promote_buttons = [
        call
        for call in st.calls
        if (
            call[0] == "button"
            and call[1] == "Promote to Approved Inputs"
        )
    ]
    assert promote_buttons == []


def test_promotion_requires_explicit_confirmation():
    st = FakeStreamlit(
        clicked_keys={
            "human_review_promotion.promote.RVV-000001"
        }
    )
    service = FakeService()

    render_approved_input_promotion_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_workspace(),
    )

    assert service.promote_calls == []
    assert any(
        call[0] == "error"
        and "explicitly confirmed" in call[1]
        for call in st.calls
    )


def test_successful_promotion_shows_created_reused_skipped_and_events():
    event = _event()
    trace = (
        _trace(
            authority_state="superseded",
            events=(event,),
        ),
        _trace(
            approved_input_id="AIN-000002",
            authority_state="active",
        ),
    )
    result = SimpleNamespace(
        created_approved_input_ids=("AIN-000002",),
        reused_approved_input_ids=("AIN-000003",),
        skipped_review_item_ids=("RIT-000004",),
        lifecycle_event_ids=("AIE-000001",),
        traceability=trace,
    )
    st = FakeStreamlit(
        clicked_keys={
            "human_review_promotion.promote.RVV-000001"
        },
        checkbox_values={
            "human_review_promotion.confirm.RVV-000001": True,
        },
    )
    service = FakeService(
        promotion_result=result,
    )

    render_approved_input_promotion_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_workspace(),
    )

    assert service.promote_calls == [
        (
            "123456",
            "RVD-000001",
            "RVV-000001",
        )
    ]

    result_rows = [
        row
        for call in st.calls
        if call[0] == "table"
        for row in call[1]
        if "Result" in row
    ]

    assert {
        (row["Result"], row["Identity"])
        for row in result_rows
    } == {
        ("Created Approved Input", "AIN-000002"),
        ("Reused Approved Input", "AIN-000003"),
        ("Skipped Review Item", "RIT-000004"),
        ("Lifecycle Event", "AIE-000001"),
    }


def test_authority_view_exposes_phase_h_active_state_and_event_lineage():
    event = _event()
    st = FakeStreamlit()
    service = FakeService(
        traceability=(
            _trace(
                authority_state="superseded",
                events=(event,),
            ),
            _trace(
                approved_input_id="AIN-000002",
                authority_state="active",
            ),
        )
    )

    render_approved_input_promotion_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_workspace(),
    )

    assert (
        "caption",
        "Phase H authoritative inputs: AIN-000002",
    ) in st.calls

    event_rows = [
        row
        for call in st.calls
        if call[0] == "table"
        for row in call[1]
        if "Event" in row
    ]

    assert event_rows == [
        {
            "Event": "AIE-000001",
            "Approved Input": "AIN-000001",
            "Transition": "active → superseded",
            "Type": "superseded",
            "Reason": "review_successor_changed",
            "Rationale": "",
            "Actor": "promotion-service",
            "Successor": "AIN-000002",
            "Causal Review Version": "RVV-000002",
            "Causal Review Revision": "RVR-000002",
            "Causal Finalization Decision": "HRD-000002",
            "Occurred": "2026-08-08T14:00:00Z",
            "Event fingerprint": "e" * 64,
        }
    ]
