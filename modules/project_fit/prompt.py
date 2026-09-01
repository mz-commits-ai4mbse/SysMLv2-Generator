"""Bounded prompt contract for Project Fit assessment."""

from __future__ import annotations

import json

from .errors import ProjectFitValidationError
from .types import ProjectFitContextReference


PROJECT_FIT_PROMPT_SCHEMA_VERSION = "1.0.0"
PROJECT_FIT_MAX_INPUT_CHARACTERS = 200_000


def build_project_fit_instructions() -> str:
    """Return the strict Project Fit task instructions."""

    return """Assess whether the candidate source plausibly belongs to the product/system represented by the project.

This is a PROJECT-FIT assessment, not an engineering truth decision.

Rules:
1. Low lexical overlap alone is NOT evidence that a source belongs to another project.
2. Different document types and abstraction levels may be complementary (for example user needs, requirements, BOMs, interfaces, and subsystem descriptions).
3. Use 'likely_out_of_scope' only when there is positive evidence of product, system, or domain incompatibility.
4. If evidence is insufficient or materially ambiguous, use 'uncertain'.
5. Context-only documents provide product/domain understanding; they are not engineering authority.
6. Do not rank sources by age, order, type, frequency, or apparent confidence.
7. Do not decide which engineering claim is correct.
8. Copy supporting_context_refs only from the exact reference IDs supplied in the input.
9. Return JSON only, with exactly this schema:
{
  "outcome": "plausible_in_scope | uncertain | likely_out_of_scope",
  "rationale": "non-empty explanation",
  "matched_concepts": ["zero or more concise concepts"],
  "incompatible_concepts": ["zero or more concise concepts"],
  "supporting_context_refs": ["zero or more exact supplied reference IDs"]
}

For 'plausible_in_scope', provide at least one matched concept and at least one supporting context reference.
For 'likely_out_of_scope', provide at least one incompatible concept and at least one supporting context reference.
Do not use absence of overlap as an incompatible concept.
"""


def build_project_fit_input(
    *,
    project_id: str,
    display_name: str,
    description: str,
    candidate_metadata: dict[str, str],
    candidate_content: str,
    context_references: tuple[ProjectFitContextReference, ...],
    context_content_by_ref: dict[str, str],
) -> str:
    """Build deterministic bounded JSON input for one Project Fit call."""

    context_values = []
    for reference in context_references:
        if reference.reference_kind != "source_projection":
            continue
        content = context_content_by_ref.get(reference.reference_id)
        if content is None:
            raise ProjectFitValidationError(
                "Every source-projection context reference requires exact content."
            )
        context_values.append(
            {
                "reference_id": reference.reference_id,
                "source_id": reference.source_id,
                "source_role": reference.source_role,
                "content": content,
            }
        )

    payload = {
        "project": {
            "reference_id": f"project_manifest:{project_id}",
            "project_id": project_id,
            "display_name": display_name,
            "description": description,
        },
        "candidate_source": {
            **candidate_metadata,
            "content": candidate_content,
        },
        "project_context_sources": context_values,
    }

    text = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    if len(text) > PROJECT_FIT_MAX_INPUT_CHARACTERS:
        raise ProjectFitValidationError(
            "Project Fit input exceeds the bounded input contract; "
            "an explicit context-reduction strategy is required."
        )
    return text
