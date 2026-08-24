"""R4c.2c tests for shared Source mentions across canonical subjects."""

from __future__ import annotations

import json

from modules.engineering_subjects.contract import (
    materialize_canonical_subject_set,
    parse_subject_discovery_output,
)
from modules.engineering_subjects.types import (
    DiscoverySourceSpan,
    DiscoverySourceToken,
)


_SHA = "a" * 64


def _span():
    text = "The operator remains responsible for the local session."
    token_texts = (
        "The",
        "operator",
        "remains",
        "responsible",
        "for",
        "the",
        "local",
        "session",
        ".",
    )

    tokens = []
    search_from = 0

    for index, token_text in enumerate(token_texts, start=1):
        start = text.index(token_text, search_from)
        end = start + len(token_text)
        tokens.append(
            DiscoverySourceToken(
                token_id=f"TOK-{index:06d}",
                source_span_id="SPAN-000001",
                segment_id="SEG-000001",
                start_offset=start,
                end_offset=end,
                exact_text=token_text,
            )
        )
        search_from = end

    return DiscoverySourceSpan(
        span_id="SPAN-000001",
        segment_id="SEG-000001",
        start_offset=0,
        end_offset=len(text),
        exact_text=text,
        source_evidence_ids=("EVD-000001",),
        source_tokens=tuple(tokens),
    )


def _materialize(subjects):
    proposals = parse_subject_discovery_output(
        json.dumps({"subjects": subjects})
    )
    return materialize_canonical_subject_set(
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        source_projection_fingerprint=_SHA,
        source_spans=(_span(),),
        proposals=proposals,
    )


def _subject(label, form, start_token, end_token):
    return {
        "canonical_label": label,
        "subject_form": form,
        "identity_status": "resolved",
        "mentions": [
            {
                "source_span_id": "SPAN-000001",
                "start_token_id": start_token,
                "end_token_id": end_token,
            }
        ],
    }


def test_identical_source_range_is_one_shared_mention():
    result = _materialize(
        [
            _subject(
                "Microscope Operator",
                "entity",
                "TOK-000001",
                "TOK-000008",
            ),
            _subject(
                "Operator Responsibility",
                "assertion",
                "TOK-000001",
                "TOK-000008",
            ),
        ]
    )

    assert len(result.mentions) == 1
    assert len(result.subjects) == 2
    assert result.mentions[0].mention_id == "MNT-000001"
    assert all(
        subject.mention_ids == ("MNT-000001",)
        for subject in result.subjects
    )


def test_overlapping_but_non_identical_ranges_remain_distinct():
    result = _materialize(
        [
            _subject(
                "Microscope Operator",
                "entity",
                "TOK-000001",
                "TOK-000002",
            ),
            _subject(
                "Operator Responsibility",
                "assertion",
                "TOK-000001",
                "TOK-000008",
            ),
        ]
    )

    assert len(result.mentions) == 2
    mention_ids = {
        subject.canonical_label: subject.mention_ids
        for subject in result.subjects
    }
    assert (
        mention_ids["Microscope Operator"]
        != mention_ids["Operator Responsibility"]
    )


def test_shared_mention_has_one_stable_source_fingerprint():
    result = _materialize(
        [
            _subject(
                "Local Session",
                "other",
                "TOK-000006",
                "TOK-000008",
            ),
            _subject(
                "Responsibility Context",
                "assertion",
                "TOK-000006",
                "TOK-000008",
            ),
        ]
    )

    assert len(result.mentions) == 1
    shared_id = result.mentions[0].mention_id
    assert all(
        subject.mention_ids == (shared_id,)
        for subject in result.subjects
    )
    assert len(result.mentions[0].content_fingerprint) == 64
