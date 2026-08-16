"""Transient presentation-depth preferences for the Turing Generator UI."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SESSION_SHOW_TECHNICAL_DETAILS = (
    "turing_generator.show_technical_details"
)


def technical_details_enabled(
    session_state: Mapping[str, Any],
) -> bool:
    """Return presentation depth without creating engineering authority."""

    return (
        session_state.get(
            SESSION_SHOW_TECHNICAL_DETAILS,
            False,
        )
        is True
    )
