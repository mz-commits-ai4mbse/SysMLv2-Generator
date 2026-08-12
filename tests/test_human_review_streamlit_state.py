"""Regression for Streamlit widget-owned reviewer identity state."""

from __future__ import annotations

from types import SimpleNamespace

from app.human_review_approval_ui import _render_review_queue


class StrictWidgetSessionState(dict):
    """Emulate Streamlit's prohibition on post-instantiation widget writes."""

    def __init__(self) -> None:
        super().__init__()
        self._locked_widget_keys: set[str] = set()

    def __setitem__(self, key, value) -> None:
        if key in self._locked_widget_keys:
            raise RuntimeError(
                f"widget-owned session state cannot be reassigned: {key}"
            )
        super().__setitem__(key, value)

    def instantiate_widget(self, key: str, value: object) -> None:
        super().__setitem__(key, value)
        self._locked_widget_keys.add(key)


class StrictStreamlit:
    def __init__(self) -> None:
        self.session_state = StrictWidgetSessionState()
        self.calls = []

    def subheader(self, text):
        self.calls.append(("subheader", text))

    def info(self, text):
        self.calls.append(("info", text))

    def text_input(
        self,
        label,
        *,
        value,
        key,
        help=None,
    ):
        self.calls.append(("text_input", label, key))
        self.session_state.instantiate_widget(
            key,
            "Reviewer A",
        )
        return self.session_state[key]


def test_reviewer_identity_widget_owns_its_session_state_key():
    st = StrictStreamlit()

    reviewer = _render_review_queue(
        st,
        service=SimpleNamespace(),
        project_view=SimpleNamespace(items=()),
        project_id="123456",
    )

    assert reviewer == "Reviewer A"
    assert (
        st.session_state[
            "human_review_approval.reviewer_identity"
        ]
        == "Reviewer A"
    )
