"""ADR-033 S3A global semantic-index prompt contract."""

from __future__ import annotations

import json


PROJECT_SEMANTIC_INDEX_PROMPT_SCHEMA_VERSION = "1.1.0"


def build_project_semantic_index_instructions() -> str:
    """Return the singular bounded S3A semantic-indexing task."""

    return """
Group the supplied source-local engineering Subjects by shared engineering concern.

This task performs SEMANTIC INDEXING ONLY. It does not assess compatibility,
conflict, correctness, authority, model representation, or Source priority.

Rules:
1. Every supplied subject_ref is an opaque transport identifier with exact form SUBJ-NNNN.
2. Every supplied subject_ref must appear at least once across all returned groups.
3. Never invent, infer, normalize, shorten, expand, or modify a subject_ref.
4. Never omit a Subject.
5. Prefer one group per Subject. A Subject may appear in more than one proposed group only when it genuinely bridges overlapping engineering concerns; overlapping proposals are normalized deterministically into one final Case.
6. Group Subjects only when they concern the same engineering topic or decision space.
7. source_id is provenance only and must not constrain semantic grouping.
8. A multi-member group may contain Subjects from the same Source, from different Sources, or both.
9. Different wording, abstraction level, or implementation detail may still concern the same topic.
10. Do not decide whether grouped statements agree or conflict.
11. Do not rank Sources by age, order, document type, frequency, confidence, or Persona consensus.
12. Do not merge Subjects and do not create Engineering Authority.
13. A Subject with no semantic counterpart must be returned as a one-member group.
14. Return JSON only, with exactly this schema:
{
  "groups": [
    {
      "group_label": "concise engineering concern label",
      "member_subject_refs": ["SUBJ-NNNN", "..."]
    }
  ]
}
""".strip()


def build_project_semantic_index_input(
    *,
    project_id: str,
    subjects: tuple[object, ...],
    max_characters: int,
) -> str:
    """Build deterministic bounded JSON input over transient Subject refs."""

    payload = {
        "project_id": project_id,
        "subjects": [
            {
                "subject_ref": subject.subject_ref,
                "source_id": subject.source_id,
                "source_projection_id": subject.source_projection_id,
                "canonical_subject_id": subject.canonical_subject_id,
                "canonical_label": subject.canonical_label,
                "subject_form": subject.subject_form,
                "identity_status": subject.identity_status,
                "source_review_attention_required": (
                    subject.source_review_attention_required
                ),
                "mentions": [
                    {
                        "mention_id": item.mention_id,
                        "exact_text": item.exact_text,
                        "source_evidence_ids": list(item.source_evidence_ids),
                    }
                    for item in subject.mention_evidence
                ],
                "persona_statement_evidence": [
                    {
                        "persona_id": item.persona_id,
                        "statements": list(item.statements),
                        "stable_across_runs": item.stable_across_runs,
                    }
                    for item in subject.statement_evidence
                ],
                "consensus_fields": [
                    {
                        "field_name": item.field_name,
                        "selected_value": item.selected_value,
                        "consensus_level": item.consensus_level,
                        "confidence": item.confidence,
                        "review_attention_required": (
                            item.review_attention_required
                        ),
                    }
                    for item in subject.field_evidence
                ],
            }
            for subject in subjects
        ],
    }

    text = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    if len(text) > max_characters:
        from .errors import ProjectSemanticReconciliationValidationError

        raise ProjectSemanticReconciliationValidationError(
            "Project semantic index input exceeds the bounded contract; "
            "an explicit indexing reduction strategy is required."
        )
    return text
