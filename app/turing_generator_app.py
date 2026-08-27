"""Primary Streamlit application for the Turing Generator."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.turing_generator_ui import render_turing_generator_ui
from app.version import (
    TURING_GENERATOR_VERSION,
    local_build_label,
)


def main() -> None:
    st.set_page_config(
        page_title=f"Turing Generator · v{TURING_GENERATOR_VERSION}",
        layout="wide",
    )
    st.title(f"Turing Generator · v{TURING_GENERATOR_VERSION}")
    st.caption(f"Build: {local_build_label(PROJECT_ROOT)}")
    render_turing_generator_ui(PROJECT_ROOT)


if __name__ == "__main__":
    main()
