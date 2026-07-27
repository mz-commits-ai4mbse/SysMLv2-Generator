"""Primary Streamlit application for the Turing Generator."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.turing_generator_ui import render_turing_generator_ui


def main() -> None:
    st.set_page_config(
        page_title="Turing Generator",
        layout="wide",
    )
    st.title("Turing Generator")
    render_turing_generator_ui(PROJECT_ROOT)


if __name__ == "__main__":
    main()
