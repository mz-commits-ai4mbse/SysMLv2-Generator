"""Strict parsing and deterministic grounding for canonical subjects."""

from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any

from .errors import (
    EngineeringSubjectIntegrityError,
    EngineeringSubjectValidationError,
)
from .grounding import validate_subject_discovery_grounding
from .identifiers import (
    format_canonical_subject_id,
    format_engineering_mention_id,
    validate_source_span_id,
    validate_source_token_id,
)
from .types import (
    CANONICAL_SUBJECT_SET_SCHEMA_VERSION,
    IDENTITY_STATUSES,
    SUBJECT_FORMS,
    CanonicalEngineeringSubject,
    CanonicalSubjectSet,
    DiscoveryMentionProposal,
    DiscoverySourceSpan,
    DiscoverySubjectProposal,
    EngineeringMention,
)


_ROOT_FIELDS = frozenset({"subjects"})
_SUBJECT_FIELDS = frozenset(
    {
        "canonical_label",
        "subject_form",
        "identity_status",
        "mentions",
    }
)
_MENTION_FIELDS = frozenset(
    {
        "source_span_id",
        "start_token_id",
        "end_token_id",
    }
)
_JSON_FENCE_PATTERN = re.compile(
    r"^\s*```(?:json)?\s*(.*?)\s*```\s*$",
    re.DOTALL | re.IGNORECASE,
)


def parse_subject_discovery_output(
    text: str,
) -> tuple[DiscoverySubjectProposal, ...]:
    """Parse strict subject-grouping JSON without trusting source grounding."""

    if not isinstance(text, str) or not text.strip():
        raise EngineeringSubjectValidationError(
            "Subject discovery output must be non-empty JSON text."
        )

    normalized = _strip_optional_json_fence(text)
    try:
        payload = json.loads(
            normalized,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except EngineeringSubjectValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise EngineeringSubjectValidationError(
            f"Subject discovery output is not valid JSON: {exc}."
        ) from exc

    root = _require_exact_object(
        payload,
        _ROOT_FIELDS,
        "Subject discovery result",
    )
    values = root["subjects"]
    if not isinstance(values, list):
        raise EngineeringSubjectValidationError(
            "subjects must be a JSON array."
        )

    proposals = tuple(_parse_subject(value) for value in values)
    return _consolidate_compatible_duplicate_subjects(proposals)


def _consolidate_compatible_duplicate_subjects(
    proposals: tuple[DiscoverySubjectProposal, ...],
) -> tuple[DiscoverySubjectProposal, ...]:
    """Merge duplicate labels only when no semantic choice is required."""

    ordered: list[DiscoverySubjectProposal] = []
    index_by_label: dict[str, int] = {}

    for proposal in proposals:
        label_key = proposal.canonical_label.casefold()
        existing_index = index_by_label.get(label_key)

        if existing_index is None:
            index_by_label[label_key] = len(ordered)
            ordered.append(proposal)
            continue

        existing = ordered[existing_index]
        if (
            existing.subject_form != proposal.subject_form
            or existing.identity_status != proposal.identity_status
        ):
            raise EngineeringSubjectValidationError(
                "Repeated canonical labels with conflicting subject_form or "
                "identity_status cannot be consolidated deterministically."
            )

        merged_mentions = list(existing.mentions)
        known_mentions = {
            (
                mention.source_span_id,
                mention.start_token_id,
                mention.end_token_id,
            )
            for mention in merged_mentions
        }

        for mention in proposal.mentions:
            mention_key = (
                mention.source_span_id,
                mention.start_token_id,
                mention.end_token_id,
            )
            if mention_key in known_mentions:
                continue
            known_mentions.add(mention_key)
            merged_mentions.append(mention)

        ordered[existing_index] = DiscoverySubjectProposal(
            canonical_label=existing.canonical_label,
            subject_form=existing.subject_form,
            identity_status=existing.identity_status,
            mentions=tuple(merged_mentions),
        )

    return tuple(ordered)


def materialize_canonical_subject_set(
    *,
    project_id: str,
    source_id: str,
    source_projection_id: str,
    source_projection_fingerprint: str,
    source_spans: tuple[DiscoverySourceSpan, ...],
    proposals: tuple[DiscoverySubjectProposal, ...],
) -> CanonicalSubjectSet:
    """Bind LLM proposals to exact system-owned token ranges and stable IDs."""

    if not source_spans:
        raise EngineeringSubjectValidationError(
            "source_spans must not be empty."
        )

    span_by_id = {
        span.span_id: span
        for span in source_spans
    }
    if len(span_by_id) != len(source_spans):
        raise EngineeringSubjectIntegrityError(
            "source_span_ids must be unique."
        )

    validate_subject_discovery_grounding(
        source_spans=source_spans,
        proposals=proposals,
    )

    resolved_subjects = []

    for proposal in proposals:
        resolved_mentions = []

        for mention in proposal.mentions:
            span = span_by_id.get(mention.source_span_id)
            if span is None:
                raise EngineeringSubjectIntegrityError(
                    "Subject discovery referenced an unknown Source Span."
                )

            if not span.source_evidence_ids:
                raise EngineeringSubjectIntegrityError(
                    "Context-only Source Spans cannot establish positive mentions."
                )

            absolute_start, absolute_end, exact_source_text = (
                _resolve_system_owned_token_range(
                    span,
                    start_token_id=mention.start_token_id,
                    end_token_id=mention.end_token_id,
                )
            )

            resolved_mentions.append(
                (
                    span,
                    absolute_start,
                    absolute_end,
                    exact_source_text,
                )
            )

        unique_mentions = {
            (
                value[0].segment_id,
                value[1],
                value[2],
                value[3],
            ): value
            for value in resolved_mentions
        }
        if len(unique_mentions) != len(resolved_mentions):
            raise EngineeringSubjectValidationError(
                "One canonical subject contains duplicate source mentions."
            )

        ordered_mentions = tuple(
            sorted(
                unique_mentions.values(),
                key=lambda value: (
                    value[0].segment_id,
                    value[1],
                    value[2],
                    value[3].casefold(),
                ),
            )
        )
        resolved_subjects.append((proposal, ordered_mentions))

    resolved_subjects.sort(
        key=lambda value: (
            _subject_first_position(value[1]),
            value[0].canonical_label.casefold(),
        )
    )

    # Mention identity belongs to the exact Source occurrence, not to a
    # canonical Subject. Identical source ranges are therefore materialized
    # exactly once and may be referenced by multiple SUBJ-* identities.
    unique_source_mentions = {}

    for _, values in resolved_subjects:
        for value in values:
            span, start_offset, end_offset, exact_text = value
            mention_key = (
                span.segment_id,
                start_offset,
                end_offset,
            )

            existing = unique_source_mentions.get(mention_key)
            if existing is not None:
                existing_span, _, _, existing_text = existing
                if (
                    existing_span.span_id != span.span_id
                    or existing_text != exact_text
                    or existing_span.source_evidence_ids
                    != span.source_evidence_ids
                ):
                    raise EngineeringSubjectIntegrityError(
                        "One exact Source occurrence resolved inconsistently."
                    )
                continue

            unique_source_mentions[mention_key] = value

    ordered_source_mentions = tuple(
        sorted(
            unique_source_mentions.values(),
            key=lambda value: (
                value[0].segment_id,
                value[1],
                value[2],
                value[3].casefold(),
            ),
        )
    )

    mentions = []
    mention_id_by_key = {}

    for value in ordered_source_mentions:
        span, start_offset, end_offset, exact_text = value
        mention_id = format_engineering_mention_id(
            len(mentions) + 1
        )
        mention_key = (
            span.segment_id,
            start_offset,
            end_offset,
        )

        mention_fp = _canonical_sha256(
            {
                "project_id": project_id,
                "source_id": source_id,
                "source_projection_id": source_projection_id,
                "source_projection_fingerprint": (
                    source_projection_fingerprint
                ),
                "source_span_id": span.span_id,
                "segment_id": span.segment_id,
                "start_offset": start_offset,
                "end_offset": end_offset,
                "exact_text": exact_text,
                "source_evidence_ids": list(
                    span.source_evidence_ids
                ),
            }
        )

        mentions.append(
            EngineeringMention(
                mention_id=mention_id,
                source_span_id=span.span_id,
                segment_id=span.segment_id,
                start_offset=start_offset,
                end_offset=end_offset,
                exact_text=exact_text,
                source_evidence_ids=span.source_evidence_ids,
                content_fingerprint=mention_fp,
            )
        )
        mention_id_by_key[mention_key] = mention_id

    mention_by_id = {
        item.mention_id: item
        for item in mentions
    }

    subjects = []

    for subject_index, (proposal, values) in enumerate(
        resolved_subjects,
        start=1,
    ):
        subject_mention_ids = tuple(
            mention_id_by_key[
                (
                    value[0].segment_id,
                    value[1],
                    value[2],
                )
            ]
            for value in values
        )

        subject_id = format_canonical_subject_id(subject_index)
        subject_fp = _canonical_sha256(
            {
                "project_id": project_id,
                "source_id": source_id,
                "source_projection_id": source_projection_id,
                "canonical_label": proposal.canonical_label,
                "subject_form": proposal.subject_form,
                "identity_status": proposal.identity_status,
                "mention_fingerprints": [
                    mention_by_id[mention_id].content_fingerprint
                    for mention_id in subject_mention_ids
                ],
            }
        )

        subjects.append(
            CanonicalEngineeringSubject(
                canonical_subject_id=subject_id,
                canonical_label=proposal.canonical_label,
                subject_form=proposal.subject_form,
                identity_status=proposal.identity_status,
                mention_ids=subject_mention_ids,
                content_fingerprint=subject_fp,
            )
        )

    body = {
        "schema_version": CANONICAL_SUBJECT_SET_SCHEMA_VERSION,
        "project_id": project_id,
        "source_id": source_id,
        "source_projection_id": source_projection_id,
        "source_projection_fingerprint": source_projection_fingerprint,
        "mentions": [
            _mention_payload(item)
            for item in mentions
        ],
        "subjects": [
            _subject_payload(item)
            for item in subjects
        ],
    }

    return CanonicalSubjectSet(
        schema_version=CANONICAL_SUBJECT_SET_SCHEMA_VERSION,
        project_id=project_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        source_projection_fingerprint=source_projection_fingerprint,
        mentions=tuple(mentions),
        subjects=tuple(subjects),
        content_fingerprint=_canonical_sha256(body),
    )


def canonical_subject_set_to_dict(
    value: CanonicalSubjectSet,
) -> dict[str, Any]:
    """Return a deterministic JSON-compatible debug/persistence payload."""

    body = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "source_id": value.source_id,
        "source_projection_id": value.source_projection_id,
        "source_projection_fingerprint": (
            value.source_projection_fingerprint
        ),
        "mentions": [
            _mention_payload(item)
            for item in value.mentions
        ],
        "subjects": [
            _subject_payload(item)
            for item in value.subjects
        ],
    }
    expected = _canonical_sha256(body)

    if value.content_fingerprint != expected:
        raise EngineeringSubjectIntegrityError(
            "Canonical Subject Set fingerprint does not match content."
        )

    return {
        **body,
        "content_fingerprint": value.content_fingerprint,
    }


def canonical_subject_set_to_json(
    value: CanonicalSubjectSet,
) -> str:
    return (
        json.dumps(
            canonical_subject_set_to_dict(value),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def _parse_subject(value: Any) -> DiscoverySubjectProposal:
    item = _require_exact_object(
        value,
        _SUBJECT_FIELDS,
        "Subject discovery item",
    )
    label = _require_text(
        item["canonical_label"],
        "canonical_label",
    )
    form = _require_choice(
        item["subject_form"],
        SUBJECT_FORMS,
        "subject_form",
    )
    status = _require_choice(
        item["identity_status"],
        IDENTITY_STATUSES,
        "identity_status",
    )

    raw_mentions = item["mentions"]
    if not isinstance(raw_mentions, list) or not raw_mentions:
        raise EngineeringSubjectValidationError(
            "Every canonical subject requires at least one mention."
        )

    mentions = tuple(
        _parse_mention(value)
        for value in raw_mentions
    )

    return DiscoverySubjectProposal(
        canonical_label=label,
        subject_form=form,
        identity_status=status,
        mentions=mentions,
    )


def _parse_mention(value: Any) -> DiscoveryMentionProposal:
    item = _require_exact_object(
        value,
        _MENTION_FIELDS,
        "Subject mention",
    )

    return DiscoveryMentionProposal(
        source_span_id=validate_source_span_id(
            item["source_span_id"]
        ),
        start_token_id=validate_source_token_id(
            item["start_token_id"]
        ),
        end_token_id=validate_source_token_id(
            item["end_token_id"]
        ),
    )


def _resolve_system_owned_token_range(
    span: DiscoverySourceSpan,
    *,
    start_token_id: str,
    end_token_id: str,
) -> tuple[int, int, str]:
    """Resolve an LLM-selected token range to exact system-owned source text."""

    token_index = {
        token.token_id: index
        for index, token in enumerate(span.source_tokens)
    }

    if len(token_index) != len(span.source_tokens):
        raise EngineeringSubjectIntegrityError(
            "Source Span contains duplicate token IDs."
        )

    start_index = token_index.get(start_token_id)
    end_index = token_index.get(end_token_id)

    if start_index is None or end_index is None:
        raise EngineeringSubjectIntegrityError(
            "Mention token IDs must belong to the claimed Source Span."
        )

    if start_index > end_index:
        raise EngineeringSubjectIntegrityError(
            "Mention start_token_id must not occur after end_token_id."
        )

    start_token = span.source_tokens[start_index]
    end_token = span.source_tokens[end_index]

    if (
        start_token.source_span_id != span.span_id
        or end_token.source_span_id != span.span_id
        or start_token.segment_id != span.segment_id
        or end_token.segment_id != span.segment_id
    ):
        raise EngineeringSubjectIntegrityError(
            "Mention tokens are not bound to the claimed Source Span."
        )

    absolute_start = start_token.start_offset
    absolute_end = end_token.end_offset
    relative_start = absolute_start - span.start_offset
    relative_end = absolute_end - span.start_offset

    if (
        relative_start < 0
        or relative_end > len(span.exact_text)
        or relative_start >= relative_end
    ):
        raise EngineeringSubjectIntegrityError(
            "Mention token range falls outside the claimed Source Span."
        )

    exact_text = span.exact_text[relative_start:relative_end]

    if not exact_text:
        raise EngineeringSubjectIntegrityError(
            "Resolved mention text must not be empty."
        )

    return absolute_start, absolute_end, exact_text


def _subject_first_position(values) -> tuple:
    if not values:
        return ("", 0, 0)

    first = values[0]
    return (
        first[0].segment_id,
        first[1],
        first[2],
    )


def _mention_payload(item: EngineeringMention) -> dict[str, Any]:
    return {
        "mention_id": item.mention_id,
        "source_span_id": item.source_span_id,
        "segment_id": item.segment_id,
        "start_offset": item.start_offset,
        "end_offset": item.end_offset,
        "exact_text": item.exact_text,
        "source_evidence_ids": list(item.source_evidence_ids),
        "content_fingerprint": item.content_fingerprint,
    }


def _subject_payload(
    item: CanonicalEngineeringSubject,
) -> dict[str, Any]:
    return {
        "canonical_subject_id": item.canonical_subject_id,
        "canonical_label": item.canonical_label,
        "subject_form": item.subject_form,
        "identity_status": item.identity_status,
        "mention_ids": list(item.mention_ids),
        "content_fingerprint": item.content_fingerprint,
    }


def _canonical_sha256(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_exact_object(
    value: Any,
    fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise EngineeringSubjectValidationError(
            f"{label} fields do not match schema."
        )
    return value


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EngineeringSubjectValidationError(
            f"{label} must be non-empty text."
        )
    return value.strip()


def _require_choice(
    value: Any,
    choices: frozenset[str],
    label: str,
) -> str:
    text = _require_text(value, label)
    if text not in choices:
        raise EngineeringSubjectValidationError(
            f"{label} has unsupported value {text!r}."
        )
    return text


def _object_without_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EngineeringSubjectValidationError(
                f"Duplicate JSON field: {key!r}."
            )
        result[key] = value
    return result


def _strip_optional_json_fence(text: str) -> str:
    match = _JSON_FENCE_PATTERN.fullmatch(text)
    return match.group(1) if match is not None else text
