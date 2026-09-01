"""ADR-033 S3B one-Case semantic assessment prompt contract."""

from __future__ import annotations

import json


PROJECT_RECONCILIATION_CASE_PROMPT_SCHEMA_VERSION = "1.0.0"


def build_project_reconciliation_case_instructions() -> str:
    """Return one singular bounded Case-assessment task."""

    return """
Assess exactly one Reconciliation Case representing one shared engineering concern.

This task creates NON-AUTHORITATIVE CASE EVIDENCE ONLY. It does not decide
Engineering Authority, Source priority, model representation, merge semantics,
or which Source is correct.

Allowed outcomes:
- equivalent: all Case members express substantially the same engineering meaning.
- complementary: Case members concern the same topic and provide compatible,
  non-competing information, viewpoints, abstraction levels, or refinements.
- potential_conflict: Case members contain materially incompatible claims about
  the same engineering concern.
- distinct: the supplied Case was over-grouped; its members do not belong to one
  shared engineering concern.
- uncertain: the relationship among the Case members cannot safely be determined.

Rules:
1. Assess the supplied Case AS A WHOLE; do not return pairwise relations.
2. Every supplied subject_ref is an opaque transport identifier with exact form SUBJ-NNNN.
3. Never invent, infer, normalize, shorten, expand, or modify a subject_ref.
4. Never rank Sources by age, order, document type, frequency, confidence, or Persona consensus.
5. Never choose which Source is correct.
6. Never merge or replace source-local Subjects.
7. potential_conflict requires explicit claim_groups that partition every supplied subject_ref.
8. claim_groups describe materially different variants only; they are not Engineering Authority.
9. Do not return outcome unique. unique is derived deterministically only for Singleton Cases.
10. Return JSON only, with exactly this schema:
{
  "shared_concern": "concise shared engineering concern",
  "outcome": "equivalent | complementary | potential_conflict | distinct | uncertain",
  "summary": "non-empty Case-level explanation",
  "shared_concepts": ["zero or more concise concepts"],
  "material_differences": ["zero or more concise differences"],
  "claim_groups": [
    {
      "summary": "concise claim/variant summary",
      "supported_by_subject_refs": ["SUBJ-NNNN", "..."]
    }
  ]
}

Evidence requirements:
- equivalent requires at least one shared_concept.
- complementary requires at least one shared_concept and at least one material_difference.
- potential_conflict requires at least one shared_concept, at least one
  material_difference, and at least two claim_groups partitioning all Case members.
- distinct requires at least one material_difference.
""".strip()


def build_project_reconciliation_case_input(
    *,
    project_id: str,
    case_id: str,
    case_label: str,
    subjects: tuple[object, ...],
    max_characters: int,
) -> str:
    """Build deterministic bounded JSON input for exactly one Case."""

    payload = {
        "project_id": project_id,
        "case_id": case_id,
        "case_label": case_label,
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
            "Project reconciliation Case input exceeds the bounded "
            "contract; an explicit Case reduction strategy is required."
        )
    return text
