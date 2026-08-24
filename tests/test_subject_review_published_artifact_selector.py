"""R4c.5b.1 selector tests for published Subject Review authority."""

from types import SimpleNamespace

import pytest

from modules.review_workspace.errors import ReviewIntegrityError
from modules.review_workspace.subject_review_artifact_adapter import (
    select_subject_review_artifacts,
)


def _ref(name, artifact_type="consensus_reports"):
    return SimpleNamespace(
        artifact_type=artifact_type,
        artifact_id=f"ART-{name}",
        repository_relative_path=f"data/final/{name}",
        content_fingerprint="a" * 64,
    )


def _history(*, complete_latest=True):
    old = SimpleNamespace(
        event_type="artifact_published",
        attempt_id="ATT-000001",
        artifact_references=(
            _ref("subject_review_bundle.json"),
        ),
    )

    refs = [
        _ref("canonical_subject_set.json"),
        _ref("subject_interpretations.json"),
        _ref("subject_consensus.json"),
        _ref("subject_review_bundle.json"),
        _ref(
            "ingestion_review_report.md",
            artifact_type="review_reports",
        ),
    ]
    if not complete_latest:
        refs = [
            item
            for item in refs
            if not item.repository_relative_path.endswith(
                "subject_consensus.json"
            )
        ]

    latest = SimpleNamespace(
        event_type="artifact_published",
        attempt_id="ATT-000003",
        artifact_references=tuple(refs),
    )
    return SimpleNamespace(events=(old, latest))


def test_selector_uses_complete_latest_attempt_only():
    result = select_subject_review_artifacts(_history())

    assert result is not None
    assert result.attempt_id == "ATT-000003"
    assert result.subject_review_bundle.repository_relative_path.endswith(
        "subject_review_bundle.json"
    )


def test_incomplete_latest_subject_review_chain_fails_closed():
    with pytest.raises(ReviewIntegrityError):
        select_subject_review_artifacts(
            _history(complete_latest=False)
        )


def test_no_subject_review_bundle_preserves_legacy_fallback():
    history = SimpleNamespace(
        events=(
            SimpleNamespace(
                event_type="artifact_published",
                attempt_id="ATT-000003",
                artifact_references=(
                    _ref("shared_evidence_review_input.json"),
                ),
            ),
        )
    )

    assert select_subject_review_artifacts(history) is None
