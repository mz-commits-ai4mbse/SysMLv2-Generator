"""Tests for G6.3c2 scoped Review Action UI."""

from __future__ import annotations

from types import SimpleNamespace

from app.human_review_scoped_actions_ui import (
    _FILTER_WIDGETS,
    _request_signature,
    render_scoped_review_actions_ui,
)
from modules.review_workspace.scoped_workflow import (
    ReviewFilterSpec,
    ReviewItemFilterFact,
    ScopedReviewActionImpactPreview,
    ScopedReviewActionRequest,
)
from modules.review_workspace.types import (
    MaterializedReviewItemReference,
)


class FakeStreamlit:
    def __init__(
        self,
        *,
        clicked_keys=(),
        select_values=None,
        multiselect_values=None,
        text_values=None,
        checkbox_values=None,
    ):
        self.clicked_keys = set(
            clicked_keys
        )
        self.select_values = dict(
            select_values or {}
        )
        self.multiselect_values = dict(
            multiselect_values or {}
        )
        self.text_values = dict(
            text_values or {}
        )
        self.checkbox_values = dict(
            checkbox_values or {}
        )
        self.session_state = {}
        self.calls = []
        self.rerun_count = 0

    def subheader(self, text):
        self.calls.append(
            ("subheader", text)
        )

    def caption(self, text):
        self.calls.append(
            ("caption", text)
        )

    def info(self, text):
        self.calls.append(
            ("info", text)
        )

    def warning(self, text):
        self.calls.append(
            ("warning", text)
        )

    def error(self, text):
        self.calls.append(
            ("error", text)
        )

    def success(self, text):
        self.calls.append(
            ("success", text)
        )

    def table(self, rows):
        self.calls.append(
            ("table", rows)
        )

    def selectbox(
        self,
        label,
        *,
        options,
        index,
        key,
        format_func=None,
    ):
        self.calls.append(
            (
                "selectbox",
                label,
                tuple(options),
                key,
            )
        )
        return self.select_values.get(
            key,
            options[index],
        )

    def multiselect(
        self,
        label,
        *,
        options,
        default,
        key,
    ):
        self.calls.append(
            (
                "multiselect",
                label,
                tuple(options),
                key,
            )
        )
        return self.multiselect_values.get(
            key,
            tuple(default),
        )

    def text_input(
        self,
        label,
        *,
        value,
        key,
        help=None,
    ):
        self.calls.append(
            ("text_input", label, key)
        )
        return self.text_values.get(
            key,
            value,
        )

    def checkbox(
        self,
        label,
        *,
        value,
        key,
    ):
        self.calls.append(
            ("checkbox", label, key)
        )
        return self.checkbox_values.get(
            key,
            value,
        )

    def button(
        self,
        label,
        *,
        key,
        type=None,
    ):
        self.calls.append(
            ("button", label, key)
        )
        return key in self.clicked_keys

    def rerun(self):
        self.rerun_count += 1


def _fact(
    item_id,
    *,
    status="open",
    kind="element",
):
    return ReviewItemFilterFact(
        review_item_id=item_id,
        item_content_fingerprint=(
            ("a" if item_id.endswith("1") else "b") * 64
        ),
        review_status=status,
        review_item_kind=kind,
        proposed_classifications=("requirement",),
        effective_classifications=("requirement",),
        proposed_framework_assignments=(
            "Stakeholder Requirements",
        ),
        effective_framework_assignments=(
            "System Requirements",
        ),
        agent_identities=("AGENT-001",),
        confidence_levels=("high",),
        consensus_states=("full_agreement",),
        agent_disagreement_state="absent",
        human_modification_state="unmodified",
        source_identities=("SRC-000001",),
        evidence_sufficiency_state="sufficient",
        relationship_validation_status="not_applicable",
    )


def _view():
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
        ),
    )


def _preview(
    *,
    overwrite_ids=(),
    bulk=False,
):
    matched = (
        MaterializedReviewItemReference(
            review_item_id="RIT-000001",
            item_content_fingerprint="a" * 64,
        ),
        MaterializedReviewItemReference(
            review_item_id="RIT-000002",
            item_content_fingerprint="b" * 64,
        ),
    )
    excluded = tuple(overwrite_ids)

    return ScopedReviewActionImpactPreview(
        review_revision_id="RVR-000001",
        action_scope="filtered_set",
        decision_dimension="framework_assignment",
        selected_values=("System Requirements",),
        filter_definition=(
            '{"review_status":["open"]}'
        ),
        matched_items=matched,
        affected_review_item_ids=tuple(
            reference.review_item_id
            for reference in matched
            if reference.review_item_id not in excluded
        ),
        item_override_review_item_ids=tuple(
            overwrite_ids
        ),
        higher_precedence_review_item_ids=tuple(
            overwrite_ids
        ),
        excluded_review_item_ids=excluded,
        would_overwrite_review_item_ids=tuple(
            overwrite_ids
        ),
        requires_bulk_rejection_confirmation=bulk,
    )


class FakeService:
    def __init__(
        self,
        *,
        preview=None,
        facts=None,
    ):
        self.facts = tuple(
            facts
            or (
                _fact("RIT-000001"),
                _fact(
                    "RIT-000002",
                    status="deferred",
                ),
            )
        )
        self.preview_result = (
            preview
            if preview is not None
            else _preview()
        )
        self.preview_calls = []
        self.apply_calls = []

    def review_filter_facts(self, *args):
        return self.facts

    def preview_scoped_action(
        self,
        *args,
        request,
    ):
        self.preview_calls.append(
            request
        )

        if (
            request.confirm_higher_precedence_overwrite
            and self.preview_result.overwrite_count
        ):
            return SimpleNamespace(
                **{
                    field: getattr(
                        self.preview_result,
                        field,
                    )
                    for field in (
                        "review_revision_id",
                        "action_scope",
                        "decision_dimension",
                        "selected_values",
                        "filter_definition",
                        "matched_items",
                        "item_override_review_item_ids",
                        "higher_precedence_review_item_ids",
                        "would_overwrite_review_item_ids",
                        "requires_bulk_rejection_confirmation",
                    )
                },
                affected_review_item_ids=tuple(
                    reference.review_item_id
                    for reference
                    in self.preview_result.matched_items
                ),
                excluded_review_item_ids=(),
                matched_count=(
                    self.preview_result.matched_count
                ),
                affected_count=(
                    self.preview_result.matched_count
                ),
                item_override_count=(
                    self.preview_result.item_override_count
                ),
                excluded_count=0,
                overwrite_count=(
                    self.preview_result.overwrite_count
                ),
            )

        return self.preview_result

    def apply_scoped_action(
        self,
        *args,
        request,
        actor_identity,
    ):
        self.apply_calls.append(
            (request, actor_identity)
        )


def _filtered_framework_streamlit(
    *,
    clicked_keys=(),
    checkbox_values=None,
):
    return FakeStreamlit(
        clicked_keys=clicked_keys,
        select_values={
            "human_review_scoped.scope.RVD-000001": (
                "filtered_set"
            ),
            "human_review_scoped.dimension.RVD-000001": (
                "framework_assignment"
            ),
        },
        multiselect_values={
            "human_review_scoped.filter.review_status."
            "RVD-000001": ("open",),
        },
        text_values={
            "human_review_scoped.values."
            "framework_assignment.RVD-000001": (
                "System Requirements"
            ),
        },
        checkbox_values=checkbox_values,
    )


def test_ui_exposes_every_required_filter_dimension():
    st = _filtered_framework_streamlit()
    service = FakeService()

    render_scoped_review_actions_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_view(),
        reviewer_identity="Reviewer A",
    )

    rendered_labels = {
        call[1]
        for call in st.calls
        if call[0] == "multiselect"
    }
    expected_labels = {
        label
        for _, label, _ in _FILTER_WIDGETS
    }

    assert expected_labels.issubset(
        rendered_labels
    )


def test_filtered_preview_uses_exact_filter_request_and_materialization():
    st = _filtered_framework_streamlit(
        clicked_keys={
            "human_review_scoped.preview.RVD-000001"
        }
    )
    service = FakeService()

    render_scoped_review_actions_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_view(),
        reviewer_identity="Reviewer A",
    )

    assert service.preview_calls
    request = service.preview_calls[0]
    assert request.action_scope == "filtered_set"
    assert request.filter_spec == ReviewFilterSpec(
        review_status=("open",),
    )
    assert request.decision_dimension == (
        "framework_assignment"
    )
    assert request.selected_values == (
        "System Requirements",
    )

    materialization_tables = [
        call[1]
        for call in st.calls
        if (
            call[0] == "table"
            and call[1]
            and "Review Item" in call[1][0]
        )
    ]
    assert materialization_tables[0][0][
        "Review Item"
    ] == "RIT-000001"
    assert (
        materialization_tables[0][0][
            "Content fingerprint"
        ]
        == "a" * 64
    )


def test_apply_is_blocked_until_same_request_was_previewed():
    st = _filtered_framework_streamlit(
        clicked_keys={
            "human_review_scoped.apply.RVD-000001"
        }
    )
    service = FakeService()

    render_scoped_review_actions_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_view(),
        reviewer_identity="Reviewer A",
    )

    assert service.apply_calls == []
    assert any(
        call[0] == "info"
        and "Preview" in call[1]
        for call in st.calls
    )


def test_higher_precedence_overwrite_requires_explicit_checkbox():
    st = _filtered_framework_streamlit(
        clicked_keys={
            "human_review_scoped.preview.RVD-000001"
        }
    )
    service = FakeService(
        preview=_preview(
            overwrite_ids=("RIT-000002",),
        )
    )

    render_scoped_review_actions_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_view(),
        reviewer_identity="Reviewer A",
    )

    st.clicked_keys = {
        "human_review_scoped.apply.RVD-000001"
    }
    st.checkbox_values[
        "human_review_scoped.confirm_overwrite."
        "RVD-000001.RVR-000001"
    ] = True

    render_scoped_review_actions_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_view(),
        reviewer_identity="Reviewer A",
    )

    assert len(service.apply_calls) == 1
    request, actor = service.apply_calls[0]
    assert (
        request.confirm_higher_precedence_overwrite
        is True
    )
    assert actor == "Reviewer A"


def test_bulk_rejection_requires_rationale_and_confirmation():
    st = FakeStreamlit(
        clicked_keys={
            "human_review_scoped.preview.RVD-000001"
        },
        select_values={
            "human_review_scoped.scope.RVD-000001": (
                "explicit_selection"
            ),
            "human_review_scoped.dimension.RVD-000001": (
                "review_outcome"
            ),
            "human_review_scoped.values."
            "review_outcome.RVD-000001": "rejected",
        },
        multiselect_values={
            "human_review_scoped.explicit_selection."
            "RVD-000001": (
                "RIT-000001",
                "RIT-000002",
            ),
        },
        text_values={
            "human_review_scoped.rationale.RVD-000001": (
                "Unsupported by evidence."
            ),
        },
    )
    service = FakeService(
        preview=_preview(
            bulk=True,
        )
    )

    render_scoped_review_actions_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_view(),
        reviewer_identity="Reviewer A",
    )

    st.clicked_keys = {
        "human_review_scoped.apply.RVD-000001"
    }
    st.checkbox_values[
        "human_review_scoped.confirm_bulk_rejection."
        "RVD-000001.RVR-000001"
    ] = True

    render_scoped_review_actions_ui(
        st,
        service=service,
        project_id="123456",
        workspace_view=_view(),
        reviewer_identity="Reviewer A",
    )

    assert len(service.apply_calls) == 1
    request, _ = service.apply_calls[0]
    assert request.confirm_bulk_rejection is True
    assert request.rationale == (
        "Unsupported by evidence."
    )


def test_request_signature_changes_when_rationale_changes():
    base = ScopedReviewActionRequest(
        expected_revision_id="RVR-000001",
        action_scope="document_default",
        decision_dimension="framework_assignment",
        selected_values=("System Requirements",),
    )
    changed = ScopedReviewActionRequest(
        expected_revision_id="RVR-000001",
        action_scope="document_default",
        decision_dimension="framework_assignment",
        selected_values=("System Requirements",),
        rationale="Reason.",
    )

    assert _request_signature(base) != (
        _request_signature(changed)
    )
