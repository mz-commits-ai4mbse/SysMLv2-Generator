"""Prompt contract for the persona-independent Evidence Detection Agent."""

from __future__ import annotations

from modules.source_analysis_units.types import SourceAnalysisUnit

from .candidate_spans import build_candidate_spans
from .types import EvidenceCandidateSpan


EVIDENCE_DETECTION_PROMPT_SCHEMA_VERSION = "1.1.0"

EVIDENCE_DETECTION_INSTRUCTIONS = """
You are the Source-Grounded Evidence Detection Agent in the Turing Generator.

Your one responsibility is to identify which deterministic candidate spans in
the CURRENT ENGINEERING SOURCE scope potentially contain model-relevant
engineering information.

Architectural rules:
- Detection answers WHICH source candidate spans are potentially relevant.
- Do not perform final engineering interpretation.
- Do not create requirements, actors, functions, interfaces, architecture,
  model candidates, or SysML.
- Reference examples and guidance are context_only and NEVER Project evidence.
- Only candidate IDs listed in CURRENT ENGINEERING SOURCE SCOPE may provide
  positive evidence.
- Never reproduce, quote, paraphrase or invent source text in the JSON output.
- Return candidate_span_ids only. Exact source text and source anchors are
  reconstructed deterministically by the system after your selection.
- A detection may select one candidate ID or multiple adjacent candidate IDs
  when one engineering evidence item genuinely spans adjacent candidates.
- Candidate IDs in one detection must be unique, contiguous and in source order.
- Mark unresolved but engineering-relevant information as uncertain.
- Do not expose chain-of-thought; use only a short rationale summary.

Return JSON only with exactly this shape:
{
  "detections": [
    {
      "candidate_span_ids": ["CAND-001"],
      "relevance": "relevant|uncertain|not_relevant",
      "rationale": "short reason"
    }
  ],
  "no_detection_rationale": null
}

If nothing is potentially relevant, return an empty detections array and a
non-null no_detection_rationale.
""".strip()


def build_evidence_detection_input(
    *,
    source_analysis_unit: SourceAnalysisUnit,
    reference_examples: str,
    candidate_spans: tuple[EvidenceCandidateSpan, ...] | None = None,
) -> str:
    """Build one explicitly separated detector input."""

    spans = (
        build_candidate_spans(source_analysis_unit)
        if candidate_spans is None
        else candidate_spans
    )
    rendered_spans = "\n\n".join(
        (
            f"[{candidate.candidate_span_id}]\n"
            f"{candidate.source_excerpt}"
        )
        for candidate in spans
    )

    return f"""
# REFERENCE GUIDANCE — CONTEXT ONLY, NEVER PROJECT EVIDENCE

{reference_examples}

# TASK

Select only candidate span IDs from CURRENT ENGINEERING SOURCE SCOPE that
potentially contain engineering-relevant information. Return JSON only.

Do not copy source text into the response. The system will reconstruct exact
source excerpts and anchors from the selected candidate IDs.

Only candidate IDs located strictly between
<<<BEGIN_CURRENT_ENGINEERING_SOURCE_SCOPE>>> and
<<<END_CURRENT_ENGINEERING_SOURCE_SCOPE>>>
are eligible.

# CURRENT ENGINEERING SOURCE SCOPE — ONLY POSITIVE EVIDENCE AUTHORITY

Source Analysis Unit ID:
{source_analysis_unit.source_analysis_unit_id}

<<<BEGIN_CURRENT_ENGINEERING_SOURCE_SCOPE>>>
{rendered_spans}
<<<END_CURRENT_ENGINEERING_SOURCE_SCOPE>>>
""".strip()
