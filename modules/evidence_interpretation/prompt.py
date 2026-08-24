"""Prompt contract for interpretation of already fixed Source Evidence."""

from __future__ import annotations

from modules.source_evidence.types import SourceEvidence


EVIDENCE_INTERPRETATION_PROMPT_SCHEMA_VERSION = "2.0.0"


def build_evidence_interpretation_task_instructions() -> str:
    """Return the strict persona task for shared Evidence interpretation."""

    return """
Return only JSON. Do not wrap the JSON in Markdown fences.

You are interpreting source-grounded Evidence that has ALREADY been detected
and assigned stable EVD-* identities.

Critical boundary:
- Do NOT detect new evidence.
- Do NOT omit supplied Evidence.
- Do NOT merge or split Evidence.
- Do NOT create source excerpts or source anchors.
- Do NOT create model elements, architecture, relationships or SysML.
- Interpret and classify EACH supplied EVD-* exactly once.
- The same EVD-* set is supplied to every persona.
- Differences should reflect your professional perspective only.

Required JSON shape:

{
  "interpretations": [
    {
      "source_evidence_id": "EVD-000001",
      "interpreted_statement": "concise professional interpretation",
      "information_type": "stakeholder | actor | user_need | requirement | use_case | function | logical_element | physical_element | interface | constraint | information_item | definition | rationale | decision | risk | ambiguity | gap | open_question | unclassified",
      "statement_modality": "descriptive | normative | definitional | interrogative",
      "epistemic_class": "explicit | interpretation | assumption",
      "missing_evidence": null,
      "extraction_rationale": "concise rationale summary",
      "uncertainties": []
    }
  ]
}

Rules:
1. Return one and only one interpretation for every supplied EVD-* ID.
2. Return no EVD-* ID that was not supplied.
3. `epistemic_class = derivation` is forbidden before Human Engineering Review.
4. For `assumption`, `missing_evidence` must explain what evidence is missing.
5. For `explicit` or `interpretation`, `missing_evidence` must be null.
6. Preserve uncertainty instead of silently resolving it.
7. Do not expose chain-of-thought; use concise rationale summaries only.
""".strip()


def build_evidence_interpretation_input(
    evidence: tuple[SourceEvidence, ...],
) -> str:
    """Build one common Evidence input shared by every persona."""

    sections = [
        "# FIXED SOURCE-GROUNDED EVIDENCE",
        "",
        (
            "Every persona receives this identical Evidence set. "
            "EVD identities, anchors and excerpts are system-owned and immutable."
        ),
        "",
    ]

    for item in evidence:
        sections.extend(
            [
                f"## {item.source_evidence_id}",
                "",
                "Exact Engineering Source evidence:",
                "<<<SOURCE_EVIDENCE",
                item.source_excerpt,
                "SOURCE_EVIDENCE",
                "",
            ]
        )

    sections.extend(
        [
            "# TASK",
            "",
            (
                "Interpret and classify every EVD identity exactly once. "
                "Return JSON only."
            ),
        ]
    )

    return "\n".join(sections)
