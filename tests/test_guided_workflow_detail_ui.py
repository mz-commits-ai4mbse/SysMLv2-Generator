from __future__ import annotations

from types import SimpleNamespace

from app.guided_workflow_detail_ui import (
    render_final_model_review_ui,
    render_model_proposal_ui,
    render_published_output_ui,
)
from app.presentation_preferences import (
    SESSION_SHOW_TECHNICAL_DETAILS,
)
from app.turing_generator_navigation import (
    SESSION_PROJECT_ID,
    SESSION_SELECTED_ENTITY_ID,
)


class Context:
    def __init__(self, st):
        self.st = st

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def metric(self, label, value):
        self.st.calls.append(("metric", label, value))

    def button(self, label, *, key):
        self.st.calls.append(("button", label, key))
        return False


class FakeStreamlit:
    def __init__(self, *, selection=None):
        self.session_state = {}
        self.selection = selection
        self.calls = []
        self.rerun_count = 0

    def header(self, value):
        self.calls.append(("header", value))

    def subheader(self, value):
        self.calls.append(("subheader", value))

    def caption(self, value):
        self.calls.append(("caption", value))

    def write(self, value):
        self.calls.append(("write", value))

    def markdown(self, value, **kwargs):
        self.calls.append(("markdown", value))

    def info(self, value):
        self.calls.append(("info", value))

    def warning(self, value):
        self.calls.append(("warning", value))

    def error(self, value):
        self.calls.append(("error", value))

    def success(self, value):
        self.calls.append(("success", value))

    def table(self, value):
        self.calls.append(("table", value))

    def code(self, value, *, language):
        self.calls.append(("code", value, language))

    def columns(self, spec):
        count = spec if isinstance(spec, int) else len(spec)
        return tuple(Context(self) for _ in range(count))

    def container(self, *, border=False):
        self.calls.append(("container", border))
        return Context(self)

    def expander(self, label, *, expanded=False):
        self.calls.append(("expander", label, expanded))
        return Context(self)

    def selectbox(
        self,
        label,
        *,
        options,
        index,
        format_func,
        key,
    ):
        self.calls.append(
            ("selectbox", label, tuple(options), key)
        )
        return (
            self.selection
            if self.selection in options
            else options[index]
        )

    def text_input(self, label, *, key, **kwargs):
        self.calls.append(("text_input", label, key))
        return ""

    def text_area(self, label, *, key, **kwargs):
        self.calls.append(("text_area", label, key))
        return ""

    def button(self, label, *, key):
        self.calls.append(("button", label, key))
        return False

    def rerun(self):
        self.rerun_count += 1


def proposal_view():
    return SimpleNamespace(
        candidate_set_id="MCS-000001",
        candidate_set_content_fingerprint="a" * 64,
        summary="3 proposed engineering objects.",
        proposed_elements=(
            SimpleNamespace(
                candidate_id="MCE-000001",
                proposed_name="System",
                model_area="system_logical",
                element_type="part_definition",
                support_level="supported",
                conformance_status="conformant",
                review_state=SimpleNamespace(
                    status="pending"
                ),
            ),
        ),
        proposed_relationships=(
            SimpleNamespace(
                candidate_id="MCR-000001",
                source_subject_key="system",
                semantic_intent="contains",
                target_subject_key="component",
                priority_class="preferred",
                conformance_status="conformant",
                review_state=SimpleNamespace(
                    status="pending"
                ),
            ),
        ),
        required_human_decisions=(
            SimpleNamespace(
                target_type="element_candidate",
                target_ids=("MCE-000001",),
                reason="Candidate requires Human review.",
                recommended_action="Review this element.",
            ),
        ),
        blocking_issues=(),
        comparability_summary=SimpleNamespace(
            improves_count=1,
            neutral_count=0,
            reduces_count=0,
            unknown_count=0,
        ),
        profile_deviations=(),
        next_action="Review the remaining candidate.",
        phase_i_gate_status="not_ready",
        generation_rationale_summary="Derived from Approved Input.",
    )


def final_review_view():
    return SimpleNamespace(
        summary="Generated model ready for Human review.",
        code_units=(
            SimpleNamespace(
                relative_path="model/system.sysml",
                content="package System {}",
                generated_unit_id="GEN-000001",
                content_fingerprint="b" * 64,
            ),
        ),
        validation_findings=(),
        required_human_actions=("Approve the final revision.",),
        diagram=SimpleNamespace(
            nodes=(
                SimpleNamespace(
                    internal_model_element_id="IEME-000001",
                    label="System",
                    model_area="system_logical",
                    element_type="part_definition",
                    framework_assignment="SL-LOG",
                ),
            ),
            edges=(),
        ),
        agent_proposals=(),
        next_action="Approve the exact validated revision.",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id="FRV-000001",
        source_internal_engineering_model_id="IEM-000001",
        generated_artifact_set_fingerprint="c" * 64,
        validation_result_fingerprint="d" * 64,
        validation_status="valid",
        publication_gate="passed",
        traceability=(),
    )


def output_package():
    manifest = SimpleNamespace(
        output_package_id="OUT-000001",
        published_at="2026-08-16T08:00:00Z",
        files=(
            SimpleNamespace(
                relative_path="model/system.sysml",
                role="sysml_unit",
                content_fingerprint="e" * 64,
            ),
            SimpleNamespace(
                relative_path="validation.json",
                role="validation_result",
                content_fingerprint="f" * 64,
            ),
        ),
        source_internal_engineering_model_id="IEM-000001",
        source_artifact_set_fingerprint="1" * 64,
        validation_result_fingerprint="2" * 64,
        final_model_review_id="FMR-000001",
        final_model_review_revision_id="FRV-000001",
        final_review_decision_id="FRD-000001",
        output_profile_reference=SimpleNamespace(
            profile_id="TURING_SYSML_V2_OUTPUT",
            profile_version="1.0.0",
        ),
    )
    return SimpleNamespace(manifest=manifest)


class Service:
    def __init__(
        self,
        *,
        proposal=None,
        final_review=None,
        release_gate=None,
        package=None,
        status="ready",
        options=(),
    ):
        self.proposal = proposal
        self.final_review = final_review
        self.release_gate = release_gate
        self.package = package
        self.status = status
        self.options = tuple(options)
        self.file_reads = []

    def load_model_proposal(self, project_id, candidate_set_id=None):
        return SimpleNamespace(
            status=self.status,
            options=self.options,
            selected_entity_id=candidate_set_id,
            proposal=self.proposal,
        )

    def load_final_model_review(
        self,
        project_id,
        final_model_review_revision_id=None,
    ):
        return SimpleNamespace(
            status=self.status,
            options=self.options,
            selected_entity_id=final_model_review_revision_id,
            final_model_review_id="FMR-000001",
            review=self.final_review,
            release_gate=self.release_gate,
        )

    def load_published_output(
        self,
        project_id,
        output_package_id=None,
    ):
        return SimpleNamespace(
            status=self.status,
            options=self.options,
            selected_entity_id=output_package_id,
            package=self.package,
        )

    def read_published_output_file(
        self,
        project_id,
        output_package_id,
        relative_path,
    ):
        self.file_reads.append(
            (project_id, output_package_id, relative_path)
        )
        return b"package System {}"


def test_model_proposal_focused_view_prioritizes_engineering_content():
    st = FakeStreamlit()
    st.session_state[SESSION_PROJECT_ID] = "123456"

    render_model_proposal_ui(
        ".",
        streamlit_module=st,
        detail_service=Service(
            proposal=proposal_view(),
        ),
    )

    assert ("header", "Model Proposal") in st.calls
    assert any(
        call[0] == "table"
        and call[1][0]["Name"] == "System"
        for call in st.calls
    )
    assert not any(
        call[0] == "caption"
        and "MCS-000001" in str(call[1])
        for call in st.calls
    )


def test_model_proposal_technical_view_exposes_exact_identity():
    st = FakeStreamlit()
    st.session_state[SESSION_PROJECT_ID] = "123456"
    st.session_state[
        SESSION_SHOW_TECHNICAL_DETAILS
    ] = True

    render_model_proposal_ui(
        ".",
        streamlit_module=st,
        detail_service=Service(
            proposal=proposal_view(),
        ),
    )

    assert any(
        call[0] == "caption"
        and "MCS-000001" in str(call[1])
        for call in st.calls
    )


def test_selection_required_sets_only_display_target():
    option = SimpleNamespace(
        entity_id="MCS-000002",
        label="Model Proposal — 2 elements",
    )
    st = FakeStreamlit(selection="MCS-000002")
    st.session_state[SESSION_PROJECT_ID] = "123456"

    render_model_proposal_ui(
        ".",
        streamlit_module=st,
        detail_service=Service(
            status="selection_required",
            options=(option,),
        ),
    )

    assert (
        st.session_state[SESSION_SELECTED_ENTITY_ID]
        == "MCS-000002"
    )
    assert st.rerun_count == 1


def test_final_review_displays_exact_generated_sysml_and_release_state():
    st = FakeStreamlit()
    st.session_state[SESSION_PROJECT_ID] = "123456"

    render_final_model_review_ui(
        ".",
        streamlit_module=st,
        detail_service=Service(
            final_review=final_review_view(),
            release_gate=SimpleNamespace(
                release_status="ready_for_approval",
                blockers=(),
            ),
        ),
    )

    assert (
        "code",
        "package System {}",
        "text",
    ) in st.calls
    assert any(
        call[0] == "warning"
        and "ready for Human" in call[1]
        for call in st.calls
    )


def test_published_output_reads_manifest_authorized_sysml_unit():
    st = FakeStreamlit()
    st.session_state[SESSION_PROJECT_ID] = "123456"
    service = Service(package=output_package())

    render_published_output_ui(
        ".",
        streamlit_module=st,
        detail_service=service,
    )

    assert service.file_reads == [
        (
            "123456",
            "OUT-000001",
            "model/system.sysml",
        )
    ]
    assert (
        "code",
        "package System {}",
        "text",
    ) in st.calls


def test_detail_views_fail_closed_without_project():
    st = FakeStreamlit()

    render_model_proposal_ui(
        ".",
        streamlit_module=st,
        detail_service=Service(
            proposal=proposal_view(),
        ),
    )

    assert any(
        call[0] == "info"
        and "Select a Project" in call[1]
        for call in st.calls
    )
