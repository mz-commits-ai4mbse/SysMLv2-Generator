"""Standalone Streamlit application for the P7 Project Dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.project_dashboard_ui import render_project_dashboard_ui


def main() -> None:
    st.set_page_config(
        page_title="Turing Generator - Project Dashboard",
        layout="wide",
    )
    st.title("Turing Generator")
    render_project_dashboard_ui(PROJECT_ROOT)


if __name__ == "__main__":
    main()
