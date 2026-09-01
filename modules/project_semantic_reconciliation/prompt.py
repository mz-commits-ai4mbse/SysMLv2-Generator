"""Bounded prompt contract for cross-source semantic reconciliation."""

from __future__ import annotations

import json

from .errors import ProjectSemanticReconciliationValidationError
from .types import ProjectSemanticSubject


PROJECT_SEMANTIC_RECONCILIATION_PROMPT_SCHEMA_VERSION = "1.0.0"
PROJECT_SEMANTIC_RECONCILIATION_MAX_INPUT_CHARACTERS = 250_000


def build_project_semantic_reconciliation_instructions() -> str:
    """Return the strict project-level semantic relationship task."""

    return """Compare source-local engineering Subjects across DIFFERENT registered engineering Sources.

This task creates RELATIONSHIP EVIDENCE ONLY. It does not create Engineering Authority, model elements, or merge Subjects.

Allowed outcomes:
- equivalent: substantially the same engineering meaning.
- complementary: related engineering concern, but different non-competing information, viewpoint, abstraction level, realization detail, or refinement.
- potential_conflict: materially incompatible claims concerning the same engineering concern.
- distinct: an explicitly compared pair represents separate engineering Subjects.
- uncertain: the relationship cannot safely be determined.

Rules:
1. Never compare two Subjects from the same Source.
2. Never infer conflict merely because statements differ.
3. Different abstraction levels may be complementary rather than competing.
4. Low lexical overlap is not evidence of conflict or wrong-project membership.
5. Do not rank Sources by age, order, document type, frequency, Persona consensus, or confidence.
6. Do not select which Source is correct.
7. Do not merge or replace Subjects.
8. Every supplied subject_ref must be covered:
   - either it appears in at least one returned relation,
   - or it appears exactly once in unmatched_subject_refs.
9. A subject_ref must not be both related and unmatched.
10. Relations are sparse: return only pairs for which a meaningful comparison was made. Subjects with no meaningful cross-source relationship belong in unmatched_subject_refs.
11. Return JSON only, with exactly this schema:
{
  "relations": [
    {
      "left_subject_ref": "exact supplied subject_ref",
      "right_subject_ref": "exact supplied subject_ref",
      "outcome": "equivalent | complementary | potential_conflict | distinct | uncertain",
      "rationale": "non-empty explanation",
      "shared_concepts": ["zero or more concise concepts"],
      "material_differences": ["zero or more concise differences"]
    }
  ],
  "unmatched_subject_refs": ["exact supplied subject_ref"]
}

Evidence requirements:
- equivalent requires at least one shared_concept.
- complementary requires at least one shared_concept and at least one material_difference.
- potential_conflict requires at least one shared_concept and at least one material_difference.
- distinct requires at least one material_difference.
"""


def build_project_semantic_reconciliation_input(
    *,
    project_id: str,
    subjects: tuple[ProjectSemanticSubject, ...],
) -> str:
    """Build deterministic bounded JSON input from validated source Subjects."""

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
    if len(text) > PROJECT_SEMANTIC_RECONCILIATION_MAX_INPUT_CHARACTERS:
        raise ProjectSemanticReconciliationValidationError(
            "Project semantic reconciliation input exceeds the bounded "
            "contract; an explicit reduction strategy is required."
        )
    return text
