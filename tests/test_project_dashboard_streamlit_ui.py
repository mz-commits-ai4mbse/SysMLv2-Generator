"""Tests for the thin P7 Streamlit Project Dashboard integration."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import FrozenInstanceError

import pytest

from app.project_dashboard_ui import (
    EvidenceControl,
    choose_project_id,
    compact_identifiers,
    dashboard_css,
    document_table_rows,
    evidence_controls,
    evidence_reference_detail,
    format_file_size,
    normalize_active_view,
    render_document_preview,
    render_evidence_navigation,
    safe_widget_key,
    status_badge_html,
)
from modules.project_dashboard.types import (
    DashboardDocumentPreview,
    DashboardProjectOption,
    DashboardStatus,
    EvidenceLocation,
    EvidenceNavigation,
    EvidenceReference,
)


SHA_A = "a" * 64


def status(
    *,
    state: str = "covered",
    label: str = "Covered",
    semantic: str = "reviewed",
    icon: str = "✓",
    explanation: str | None = "Exact explanation",
) -> DashboardStatus:
    return DashboardStatus(
        state=state,
        label=label,
        semantic=semantic,
        icon=icon,
        explanation=explanation,
    )


def reference(
    *,
    reference_id: str = "IU-000001",
    reference_type: str = "information_unit",
    path: str = (
        "data/projects/123456/semantics/"
        "information_units/IU-000001.json"
    ),
    evidence_role: str = "direct",
    relationship: str = "supports",
    display_label: str = "Information Unit IU-000001",
    source_role: str | None = "engineering_source",
    location: EvidenceLocation | None = None,
) -> EvidenceReference:
    return EvidenceReference(
        project_id="123456",
        reference_type=reference_type,
        reference_id=reference_id,
        display_label=display_label,
        repository_relative_path=path,
        content_fingerprint=SHA_A,
        media_type="application/json",
        source_role=source_role,
        relationship=relationship,
        evidence_role=evidence_role,
        location=location,
    )


def project(
    project_id: str,
    display_name: str,
) -> DashboardProjectOption:
    return DashboardProjectOption(
        project_id=project_id,
        display_name=display_name,
        description="",
        label=f"{display_name} · {project_id}",
        framework_template_id="TURING_RFLP_FRAMEWORK",
        framework_template_version="1.0.0",
        evidence=EvidenceNavigation(
            mode="direct",
            references=(
                reference(
                    reference_id=project_id,
                    reference_type="project_manifest",
                    path=(
                        f"data/projects/{project_id}/"
                        "project_manifest.json"
                    ),
                    display_label="Project Manifest",
                    source_role=None,
                ),
            ),
        ),
    )


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeStreamlit:
    def __init__(self, *, clicked_keys=()):
        self.session_state = {}
        self.clicked_keys = set(clicked_keys)
        self.calls = []

    def button(self, label, *, key, help=None):
        self.calls.append(("button", label, key, help))
        return key in self.clicked_keys

    def caption(self, text):
        self.calls.append(("caption", text))

    def expander(self, label, *, expanded=False):
        self.calls.append(("expander", label, expanded))
        return _Context()

    def columns(self, spec):
        count = spec if isinstance(spec, int) else len(spec)
        self.calls.append(("columns", spec))
        return tuple(_Context() for _ in range(count))

    def markdown(self, text, **kwargs):
        self.calls.append(("markdown", text, kwargs))

    def code(self, text, language=None):
        self.calls.append(("code", text, language))

    def table(self, rows):
        self.calls.append(("table", rows))

    def info(self, text):
        self.calls.append(("info", text))

    def warning(self, text):
        self.calls.append(("warning", text))

    def write(self, text):
        self.calls.append(("write", text))


def preview(
    *,
    render_mode: str = "text",
    content_text: str | None = "content",
    highlighted_text: str | None = None,
    columns=(),
    rows=(),
    issue: str | None = None,
    truncated: bool = False,
) -> DashboardDocumentPreview:
    ref = reference()
    return DashboardDocumentPreview(
        project_id="123456",
        reference=ref,
        repository_relative_path=ref.repository_relative_path,
        title="Document",
        media_type=ref.media_type,
        file_size_bytes=7,
        actual_sha256=SHA_A,
        fingerprint_status="verified",
        render_mode=render_mode,
        content_text=content_text,
        highlighted_text=highlighted_text,
        table_columns=tuple(columns),
        table_rows=tuple(tuple(item for item in row) for row in rows),
        selected_json_pointer=None,
        selected_table_row_key=None,
        truncated=truncated,
        issue=issue,
    )


def test_evidence_control_is_immutable():
    control = EvidenceControl(
        key="key",
        label="label",
        detail="detail",
        reference=reference(),
    )
    with pytest.raises(FrozenInstanceError):
        control.label = "changed"


@pytest.mark.parametrize(
    ("semantic", "expected"),
    [
        ("neutral", 'data-semantic="neutral"'),
        ("informational", 'data-semantic="informational"'),
        ("candidate", 'data-semantic="candidate"'),
        ("reviewed", 'data-semantic="reviewed"'),
        ("attention", 'data-semantic="attention"'),
        ("blocking", 'data-semantic="blocking"'),
        ("unavailable", 'data-semantic="unavailable"'),
    ],
)
def test_status_badge_uses_supported_semantic(semantic, expected):
    html = status_badge_html(status(semantic=semantic))
    assert expected in html


def test_status_badge_falls_back_to_neutral():
    html = status_badge_html(status(semantic="decorative"))
    assert 'data-semantic="neutral"' in html
    assert "decorative" not in html


def test_status_badge_escapes_label_icon_and_explanation():
    html = status_badge_html(
        status(
            label="<script>",
            icon="<",
            explanation='"unsafe"',
        )
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;" in html
    assert "&quot;unsafe&quot;" in html


def test_status_badge_contains_text_and_icon():
    html = status_badge_html(status())
    assert "Covered" in html
    assert "✓" in html


def test_dashboard_css_has_no_gradient():
    assert "gradient" not in dashboard_css().lower()


@pytest.mark.parametrize(
    "semantic",
    [
        "neutral",
        "informational",
        "candidate",
        "reviewed",
        "attention",
        "blocking",
        "unavailable",
    ],
)
def test_dashboard_css_defines_only_status_semantic_rule(semantic):
    css = dashboard_css()
    assert (
        f'.turing-status[data-semantic="{semantic}"]'
        in css
    )


def test_dashboard_css_has_no_page_or_card_background_rule():
    css = dashboard_css()
    assert ".stApp" not in css
    assert ".dashboard-card" not in css


def test_evidence_controls_unavailable():
    navigation = EvidenceNavigation(
        mode="unavailable",
        references=(),
    )
    assert evidence_controls(navigation) == ()


def test_evidence_controls_rejects_unavailable_with_reference():
    navigation = EvidenceNavigation(
        mode="unavailable",
        references=(reference(),),
    )
    with pytest.raises(ValueError):
        evidence_controls(navigation)


def test_evidence_controls_direct():
    ref = reference()
    controls = evidence_controls(
        EvidenceNavigation(
            mode="direct",
            references=(ref,),
        )
    )
    assert len(controls) == 1
    assert controls[0].reference is ref


def test_evidence_controls_rejects_invalid_direct_count():
    navigation = EvidenceNavigation(
        mode="direct",
        references=(),
    )
    with pytest.raises(ValueError):
        evidence_controls(navigation)


def test_evidence_controls_chooser_preserves_order():
    first = reference(reference_id="IU-000001")
    second = reference(
        reference_id="FAC-000001",
        reference_type="framework_assignment_candidate",
        path=(
            "data/projects/123456/semantics/"
            "framework_assignments/FAC-000001.json"
        ),
    )
    controls = evidence_controls(
        EvidenceNavigation(
            mode="chooser",
            references=(first, second),
        )
    )
    assert tuple(item.reference for item in controls) == (
        first,
        second,
    )


def test_evidence_controls_rejects_single_chooser_reference():
    navigation = EvidenceNavigation(
        mode="chooser",
        references=(reference(),),
    )
    with pytest.raises(ValueError):
        evidence_controls(navigation)


def test_evidence_controls_rejects_unknown_mode():
    navigation = EvidenceNavigation(
        mode="external",
        references=(reference(),),
    )
    with pytest.raises(ValueError):
        evidence_controls(navigation)


def test_evidence_reference_detail_identifies_direct_evidence():
    detail = evidence_reference_detail(reference())
    assert detail.startswith("Direct evidence")
    assert "supports" in detail
    assert "engineering_source" in detail


def test_evidence_reference_detail_identifies_context():
    detail = evidence_reference_detail(
        reference(
            evidence_role="contextual",
            source_role=None,
        )
    )
    assert detail.startswith("Context")
    assert "engineering_source" not in detail


def test_choose_project_id_preserves_valid_current_project():
    projects = (
        project("000001", "Alpha"),
        project("000002", "Beta"),
    )
    assert choose_project_id(projects, "000002") == "000002"


@pytest.mark.parametrize(
    "current",
    [None, "", "999999", 2, object()],
)
def test_choose_project_id_falls_back_to_first(current):
    projects = (
        project("000001", "Alpha"),
        project("000002", "Beta"),
    )
    assert choose_project_id(projects, current) == "000001"


def test_choose_project_id_rejects_empty_options():
    with pytest.raises(ValueError):
        choose_project_id((), None)


@pytest.mark.parametrize(
    "value",
    ["overview", "sources", "coverage", "attention", "traceability"],
)
def test_normalize_active_view_preserves_supported_value(value):
    assert normalize_active_view(value) == value


@pytest.mark.parametrize(
    "value",
    [None, "", "unknown", 1, object()],
)
def test_normalize_active_view_defaults_to_overview(value):
    assert normalize_active_view(value) == "overview"


def test_safe_widget_key_is_deterministic():
    assert safe_widget_key("a", 1) == safe_widget_key("a", 1)


def test_safe_widget_key_changes_with_payload():
    assert safe_widget_key("a", 1) != safe_widget_key("a", 2)


def test_safe_widget_key_has_bounded_shape():
    key = safe_widget_key("a" * 1000)
    assert key.startswith("project_dashboard.")
    assert len(key) == len("project_dashboard.") + 20


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (0, "0 B"),
        (1, "1 B"),
        (1023, "1023 B"),
        (1024, "1.0 KiB"),
        (1536, "1.5 KiB"),
        (1024**2, "1.0 MiB"),
        (1024**3, "1.0 GiB"),
    ],
)
def test_format_file_size(size, expected):
    assert format_file_size(size) == expected


@pytest.mark.parametrize("value", [-1, -100])
def test_format_file_size_rejects_negative(value):
    with pytest.raises(ValueError):
        format_file_size(value)


@pytest.mark.parametrize("value", [True, 1.2, "1"])
def test_format_file_size_rejects_non_integer(value):
    with pytest.raises(TypeError):
        format_file_size(value)


def test_compact_identifiers_empty():
    assert compact_identifiers(()) == "—"


def test_compact_identifiers_within_limit():
    assert compact_identifiers(("A", "B")) == "A, B"


def test_compact_identifiers_bounded():
    assert compact_identifiers(
        ("A", "B", "C"),
        limit=2,
    ) == "A, B · +1 more"


def test_compact_identifiers_rejects_invalid_limit():
    with pytest.raises(ValueError):
        compact_identifiers(("A",), limit=0)


def test_document_table_rows_maps_columns():
    rows = document_table_rows(
        preview(
            render_mode="table",
            columns=("id", "name"),
            rows=(("1", "Alpha"), ("2", "Beta")),
        )
    )
    assert rows == [
        {"id": "1", "name": "Alpha"},
        {"id": "2", "name": "Beta"},
    ]


def test_document_table_rows_fills_short_rows():
    rows = document_table_rows(
        preview(
            render_mode="table",
            columns=("id", "name"),
            rows=(("1",),),
        )
    )
    assert rows == [{"id": "1", "name": ""}]


def test_render_unavailable_navigation_uses_caption():
    st = FakeStreamlit()
    render_evidence_navigation(
        st,
        EvidenceNavigation(
            mode="unavailable",
            references=(),
        ),
        key_prefix="x",
    )
    assert any(
        call[0] == "caption" and "No linked evidence" in call[1]
        for call in st.calls
    )


def test_render_direct_navigation_opens_reference():
    ref = reference()
    navigation = EvidenceNavigation(
        mode="direct",
        references=(ref,),
    )
    control = evidence_controls(navigation)[0]
    button_key = safe_widget_key("direct", control.key)
    st = FakeStreamlit(clicked_keys=(button_key,))
    render_evidence_navigation(
        st,
        navigation,
        key_prefix="direct",
    )
    assert (
        st.session_state["project_dashboard.open_reference"]
        is ref
    )


def test_render_chooser_opens_selected_reference():
    first = reference(reference_id="IU-000001")
    second = reference(
        reference_id="IU-000002",
        path=(
            "data/projects/123456/semantics/"
            "information_units/IU-000002.json"
        ),
    )
    navigation = EvidenceNavigation(
        mode="chooser",
        references=(first, second),
    )
    second_control = evidence_controls(navigation)[1]
    button_key = safe_widget_key("chooser", second_control.key)
    st = FakeStreamlit(clicked_keys=(button_key,))
    render_evidence_navigation(
        st,
        navigation,
        key_prefix="chooser",
    )
    assert (
        st.session_state["project_dashboard.open_reference"]
        is second
    )


@pytest.mark.parametrize(
    ("mode", "call_type"),
    [
        ("json", "code"),
        ("text", "code"),
        ("table", "table"),
        ("metadata", "info"),
    ],
)
def test_render_document_preview_modes(mode, call_type):
    kwargs = {}
    if mode == "table":
        kwargs = {
            "columns": ("id",),
            "rows": (("1",),),
        }
    st = FakeStreamlit()
    render_document_preview(
        st,
        preview(render_mode=mode, **kwargs),
    )
    assert any(call[0] == call_type for call in st.calls)


def test_render_markdown_preview_renders_and_shows_source():
    st = FakeStreamlit()
    render_document_preview(
        st,
        preview(
            render_mode="markdown",
            content_text="# Heading",
        ),
    )
    assert any(
        call[0] == "markdown" and call[1] == "# Heading"
        for call in st.calls
    )
    assert any(
        call[0] == "code" and call[2] == "markdown"
        for call in st.calls
    )


def test_render_document_preview_shows_highlight():
    st = FakeStreamlit()
    render_document_preview(
        st,
        preview(highlighted_text="selected"),
    )
    assert any(
        call[0] == "code" and call[1] == "selected"
        for call in st.calls
    )


def test_render_document_preview_shows_issue_and_truncation():
    st = FakeStreamlit()
    render_document_preview(
        st,
        preview(
            issue="viewer issue",
            truncated=True,
        ),
    )
    warnings = [
        call[1]
        for call in st.calls
        if call[0] == "warning"
    ]
    assert "viewer issue" in warnings
    assert any("bounded" in item for item in warnings)
