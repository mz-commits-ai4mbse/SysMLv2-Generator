"""Deterministic Subject grounding validation and bounded repair guidance."""

from __future__ import annotations

import json

from .errors import (
    EngineeringSubjectGroundingError,
    EngineeringSubjectGroundingViolation,
    EngineeringSubjectIntegrityError,
)
from .types import DiscoverySourceSpan, DiscoverySubjectProposal


ENGINEERING_SUBJECT_GROUNDING_REPAIR_SCHEMA_VERSION = "1.0.0"


def validate_subject_discovery_grounding(
    *,
    source_spans: tuple[DiscoverySourceSpan, ...],
    proposals: tuple[DiscoverySubjectProposal, ...],
) -> None:
    """Validate all LLM-owned mention addresses against system-owned spans."""

    span_by_id = {span.span_id: span for span in source_spans}
    if len(span_by_id) != len(source_spans):
        raise EngineeringSubjectIntegrityError(
            "source_span_ids must be unique."
        )

    token_owner: dict[str, tuple[str, int]] = {}
    for span in source_spans:
        for token_index, token in enumerate(span.source_tokens):
            if token.token_id in token_owner:
                raise EngineeringSubjectIntegrityError(
                    "Source token IDs must be globally unique."
                )
            token_owner[token.token_id] = (span.span_id, token_index)

    violations: list[EngineeringSubjectGroundingViolation] = []

    for subject_index, proposal in enumerate(proposals, start=1):
        for mention_index, mention in enumerate(
            proposal.mentions,
            start=1,
        ):
            span = span_by_id.get(mention.source_span_id)

            if span is None:
                violations.append(
                    EngineeringSubjectGroundingViolation(
                        code="unknown_source_span",
                        subject_index=subject_index,
                        mention_index=mention_index,
                        source_span_id=mention.source_span_id,
                        start_token_id=mention.start_token_id,
                        end_token_id=mention.end_token_id,
                    )
                )
                continue

            if not span.source_evidence_ids:
                violations.append(
                    EngineeringSubjectGroundingViolation(
                        code="context_only_positive_mention",
                        subject_index=subject_index,
                        mention_index=mention_index,
                        source_span_id=mention.source_span_id,
                        start_token_id=mention.start_token_id,
                        end_token_id=mention.end_token_id,
                    )
                )
                continue

            token_problem = False
            mention_token_indices: dict[str, int] = {}

            for token_role, token_id in (
                ("start", mention.start_token_id),
                ("end", mention.end_token_id),
            ):
                owner = token_owner.get(token_id)

                if owner is None:
                    violations.append(
                        EngineeringSubjectGroundingViolation(
                            code="unknown_token",
                            subject_index=subject_index,
                            mention_index=mention_index,
                            source_span_id=mention.source_span_id,
                            start_token_id=mention.start_token_id,
                            end_token_id=mention.end_token_id,
                            token_role=token_role,
                        )
                    )
                    token_problem = True
                    continue

                owner_span_id, owner_index = owner
                if owner_span_id != span.span_id:
                    violations.append(
                        EngineeringSubjectGroundingViolation(
                            code="token_not_in_claimed_span",
                            subject_index=subject_index,
                            mention_index=mention_index,
                            source_span_id=mention.source_span_id,
                            start_token_id=mention.start_token_id,
                            end_token_id=mention.end_token_id,
                            token_role=token_role,
                            actual_source_span_id=owner_span_id,
                        )
                    )
                    token_problem = True
                    continue

                mention_token_indices[token_role] = owner_index

            if token_problem:
                continue

            if (
                mention_token_indices["start"]
                > mention_token_indices["end"]
            ):
                violations.append(
                    EngineeringSubjectGroundingViolation(
                        code="reversed_token_range",
                        subject_index=subject_index,
                        mention_index=mention_index,
                        source_span_id=mention.source_span_id,
                        start_token_id=mention.start_token_id,
                        end_token_id=mention.end_token_id,
                    )
                )

    if violations:
        raise EngineeringSubjectGroundingError(tuple(violations))


def build_engineering_subject_grounding_repair_instructions(
    *,
    base_instructions: str,
    error: EngineeringSubjectGroundingError,
) -> str:
    """Build one generic repair contract from deterministic validator facts."""

    codes = {violation.code for violation in error.violations}
    rules = [
        (
            "Return the COMPLETE discovery JSON again; do not return a patch "
            "or explanation."
        ),
        (
            "Treat the structured violations below as system-owned validator "
            "facts, not as Source content."
        ),
        (
            "Every positive mention must use a visible SPAN-* that is marked "
            "with at least one EVD-* ID in the supplied Source context."
        ),
        "Never invent, renumber, or relabel SPAN-* or TOK-* IDs.",
        (
            "Do not move a mention to an unrelated Evidence span merely to "
            "satisfy validation."
        ),
        (
            "If a proposed Subject has no exact Evidence-supported positive "
            "mention, omit that unsupported Subject instead of fabricating "
            "grounding."
        ),
    ]

    if "unknown_source_span" in codes:
        rules.append(
            "For unknown_source_span, choose only a SPAN-* that actually "
            "exists in the supplied Source context."
        )
    if "context_only_positive_mention" in codes:
        rules.append(
            "For context_only_positive_mention, the claimed span is forbidden "
            "as a positive anchor; context-only spans may be used only for "
            "interpretation or coreference."
        )
    if "unknown_token" in codes:
        rules.append(
            "For unknown_token, choose only TOK-* IDs present in the TOKEN MAP."
        )
    if "token_not_in_claimed_span" in codes:
        rules.append(
            "For token_not_in_claimed_span, start_token_id and end_token_id "
            "must both belong to the claimed source_span_id."
        )
    if "reversed_token_range" in codes:
        rules.append(
            "For reversed_token_range, start_token_id must occur at or before "
            "end_token_id inside the claimed Source Span."
        )

    repair_payload = {
        "schema_version": (
            ENGINEERING_SUBJECT_GROUNDING_REPAIR_SCHEMA_VERSION
        ),
        "violations": [
            violation.to_dict()
            for violation in error.violations
        ],
    }

    rule_text = "\n".join(f"- {rule}" for rule in rules)
    payload_text = json.dumps(
        repair_payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )

    return (
        base_instructions
        + "\n\nGROUNDING CORRECTION RETRY:\n"
        + rule_text
        + "\n\nSTRUCTURED_GROUNDING_VIOLATIONS:\n"
        + payload_text
        + "\nEND_STRUCTURED_GROUNDING_VIOLATIONS"
    )
