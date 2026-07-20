"""Standalone Streamlit demo app for Team Agentic Ingestion."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.team_agentic_ingestion_ui import render_team_agentic_ingestion_ui


def main() -> None:
    st.set_page_config(
        page_title="Turing Generator - Team Agentic Ingestion",
        layout="wide",
    )

    st.title("Turing Generator")
    st.caption("Demo UI for team-based agentic ingestion")

    render_team_agentic_ingestion_ui(PROJECT_ROOT)


if __name__ == "__main__":
    main()
