"""Tests for the Approved Input repository public API."""

import modules.approved_input as approved_input


def test_repository_symbols_are_public() -> None:
    expected = {
        "APPROVED_INPUT_REPOSITORY_ISSUE_LEVELS",
        "ApprovedInputRepository",
        "ApprovedInputRepositoryIssue",
        "ApprovedInputRepositoryScanResult",
        "DEFAULT_PROJECTS_ROOT",
    }

    assert expected.issubset(set(approved_input.__all__))
