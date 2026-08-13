from __future__ import annotations

import pytest

from modules.sysml_generation import (
    SysMLGenerationValidationError,
    normalize_engineering_text,
    normalize_optional_engineering_text,
)


def test_engineering_text_preserves_content_and_normalizes_line_endings() -> None:
    assert normalize_engineering_text(
        "Line 1\r\nLine 2\rLine 3",
        label="text",
        allow_empty=False,
    ) == "Line 1\nLine 2\nLine 3"


@pytest.mark.parametrize(
    "unsafe",
    [
        "unsafe */ injected",
        "unsafe /* nested",
    ],
)
def test_engineering_text_rejects_block_comment_delimiters(unsafe: str) -> None:
    with pytest.raises(SysMLGenerationValidationError):
        normalize_engineering_text(
            unsafe,
            label="text",
            allow_empty=False,
        )


def test_engineering_text_rejects_nul() -> None:
    with pytest.raises(SysMLGenerationValidationError):
        normalize_engineering_text(
            "unsafe\x00text",
            label="text",
            allow_empty=False,
        )


def test_required_engineering_name_cannot_be_empty() -> None:
    with pytest.raises(SysMLGenerationValidationError):
        normalize_engineering_text(
            "   ",
            label="name",
            allow_empty=False,
        )


def test_optional_text_preserves_none() -> None:
    assert normalize_optional_engineering_text(
        None,
        label="description",
    ) is None
