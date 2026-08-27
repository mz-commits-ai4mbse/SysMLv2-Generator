from __future__ import annotations

import json

import pytest

from modules.engineering_subjects.contract import parse_subject_discovery_output
from modules.engineering_subjects.errors import EngineeringSubjectValidationError


def _mention(span_id: str, start_token_id: str, end_token_id: str) -> dict[str, str]:
    return {
        "source_span_id": span_id,
        "start_token_id": start_token_id,
        "end_token_id": end_token_id,
    }


def _subject(*, label: str, form: str = "condition", status: str = "resolved", mentions):
    return {
        "canonical_label": label,
        "subject_form": form,
        "identity_status": status,
        "mentions": mentions,
    }


def _parse(subjects):
    return parse_subject_discovery_output(json.dumps({"subjects": subjects}))


def test_compatible_duplicate_labels_merge_mentions_deterministically():
    proposals = _parse([
        _subject(
            label="Active collaboration session",
            mentions=[_mention("SPAN-000010", "TOK-000116", "TOK-000120")],
        ),
        _subject(
            label="Active collaboration session",
            mentions=[_mention("SPAN-000016", "TOK-000206", "TOK-000210")],
        ),
    ])

    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal.canonical_label == "Active collaboration session"
    assert proposal.subject_form == "condition"
    assert proposal.identity_status == "resolved"
    assert tuple(
        (m.source_span_id, m.start_token_id, m.end_token_id)
        for m in proposal.mentions
    ) == (
        ("SPAN-000010", "TOK-000116", "TOK-000120"),
        ("SPAN-000016", "TOK-000206", "TOK-000210"),
    )


def test_case_variant_duplicate_preserves_first_canonical_label():
    proposals = _parse([
        _subject(
            label="Active Collaboration Session",
            mentions=[_mention("SPAN-000010", "TOK-000116", "TOK-000120")],
        ),
        _subject(
            label="active collaboration session",
            mentions=[_mention("SPAN-000016", "TOK-000206", "TOK-000210")],
        ),
    ])

    assert len(proposals) == 1
    assert proposals[0].canonical_label == "Active Collaboration Session"
    assert len(proposals[0].mentions) == 2


def test_identical_duplicate_mentions_are_not_repeated():
    mention = _mention("SPAN-000010", "TOK-000116", "TOK-000120")
    proposals = _parse([
        _subject(label="Active collaboration session", mentions=[mention]),
        _subject(label="Active collaboration session", mentions=[mention]),
    ])

    assert len(proposals) == 1
    assert len(proposals[0].mentions) == 1


def test_duplicate_label_with_conflicting_subject_form_fails_closed():
    with pytest.raises(
        EngineeringSubjectValidationError,
        match="cannot be consolidated deterministically",
    ):
        _parse([
            _subject(
                label="Active collaboration session",
                form="condition",
                mentions=[_mention("SPAN-000010", "TOK-000116", "TOK-000120")],
            ),
            _subject(
                label="Active collaboration session",
                form="assertion",
                mentions=[_mention("SPAN-000016", "TOK-000206", "TOK-000210")],
            ),
        ])


def test_duplicate_label_with_conflicting_identity_status_fails_closed():
    with pytest.raises(
        EngineeringSubjectValidationError,
        match="cannot be consolidated deterministically",
    ):
        _parse([
            _subject(
                label="Active collaboration session",
                status="resolved",
                mentions=[_mention("SPAN-000010", "TOK-000116", "TOK-000120")],
            ),
            _subject(
                label="Active collaboration session",
                status="uncertain",
                mentions=[_mention("SPAN-000016", "TOK-000206", "TOK-000210")],
            ),
        ])
