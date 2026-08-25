"""Identifiers for Human Model Placement Review decisions."""

from __future__ import annotations

import re

from .errors import ModelPlacementContractError


_PATTERN = re.compile(r"^MPD-([0-9]{6})$")


def validate_model_placement_decision_id(value: str) -> str:
    if not isinstance(value, str) or _PATTERN.fullmatch(value) is None:
        raise ModelPlacementContractError(
            "Model Placement decision ID must match MPD-000001."
        )
    return value


def next_model_placement_decision_id(values) -> str:
    numbers = []
    for value in values:
        validated = validate_model_placement_decision_id(value)
        numbers.append(int(_PATTERN.fullmatch(validated).group(1)))
    number = max(numbers, default=0) + 1
    if number > 999999:
        raise ModelPlacementContractError(
            "Model Placement decision ID space exhausted."
        )
    return f"MPD-{number:06d}"
