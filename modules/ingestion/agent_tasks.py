"""Task instructions for agentic ingestion.

This module contains only task instructions.

It does not call LLMs.
It does not run agents.
It does not write files.
"""

from __future__ import annotations

from pathlib import Path


def get_interpreter_task_instructions() -> str:
    """Instructions for legacy data interpretation."""

    return """
Return only JSON. Do not wrap the JSON in Markdown fences.

Extract meaningful engineering information from the raw legacy input.

Required JSON shape:
{
  "source_information": [
    {
      "source_info_id": "SRC_INFO_001",
      "source_reference": "line or section reference",
      "extracted_information": "what the source says",
      "information_kind": "explicit | implied | assumption | uncertainty | negated | missing",
      "confidence": "high | medium | low",
      "notes": "concise rationale"
    }
  ],
  "assumptions": [],
  "ambiguities": [],
  "not_interpreted_as_positive_evidence": []
}

Focus only on interpretation and extraction.

Do not classify evidence types.
Do not assess downstream model derivation.
Do not generate SysML v2 output.
Do not approve or promote data.
""".strip()


def get_evidence_classifier_task_instructions() -> str:
    """Instructions for evidence classification."""

    return """
Return only JSON. Do not wrap the JSON in Markdown fences.

Classify the interpreted engineering information into evidence types.

Classify only positive evidence.

Do not classify missing, negated, absent or uncertain information as positive evidence.

Required JSON shape:
{
  "detected_evidence": [
    {
      "evidence_id": "EVDET_001",
      "evidence_type": "EV_FUNCTION_OR_CAPABILITY",
      "source_info_id": "SRC_INFO_001",
      "source_excerpt": "source statement",
      "interpretation": "why this is evidence",
      "confidence": "high | medium | low",
      "rationale_summary": "concise rationale"
    }
  ],
  "rejected_evidence_candidates": [
    {
      "source_info_id": "SRC_INFO_999",
      "rejected_evidence_type": "EV_VALIDATION_CRITERION",
      "reason": "why this is not positive evidence"
    }
  ],
  "evidence_gaps": []
}

Do not assess downstream model derivation.
Do not generate SysML v2 output.
Do not approve or promote data.
""".strip()


def get_derivation_assessor_task_instructions(
    derivation_rules_text: str,
) -> str:
    """Instructions for model element and buildability assessment."""

    return f"""
Return only valid JSON.
Do not wrap the JSON in Markdown fences.

Your responsibility is to identify candidate SysML model elements and assess
which model types could be generated from the available source evidence.

Core extraction rule:

- Explicitly named engineering entities must be materialized as candidate
  model elements when they are needed to represent source-supported structure.
- Do not omit an explicit entity merely because its precise downstream SysML
  classification is uncertain.
- When entity existence is explicit but classification is uncertain, use the
  least-assumptive allowed element_type, reduce confidence or use partial
  generation_readiness as appropriate, and record the classification
  uncertainty in missing_information.
- Do not invent entities, architecture, interfaces, storage, protocols or
  relationships that are not supported by the source evidence.

Relationship rule:

- Do not invent relationships merely because they are typical or plausible.
- Include a relationship only when it is explicitly stated or directly
  evidenced by the source material.
- Every source_element_candidate and target_element_candidate MUST reference
  one candidate_id that exists in candidate_model_elements in this same JSON
  output.
- Relationship endpoints MUST use candidate IDs only. Do not use candidate
  names or free text as relationship endpoints.
- If an explicit source-supported relationship mentions an entity that has
  not yet been materialized, first create a source-supported candidate element
  for that entity, then reference its candidate_id in explicit_source_links.
- If the existence of an endpoint itself is uncertain or unsupported, do not
  invent it. Record the unresolved interpretation as a review question instead.

Required JSON shape:

{{
  "candidate_model_elements": [
    {{
      "candidate_id": "ELEM_001",
      "element_type": "actor | stakeholder | system | subsystem | requirement | use_case | function | item | interface | constraint | risk | verification_case | data_object | package | other",
      "candidate_name": "concise source-based name",
      "description": "source-based description of the candidate",
      "source_basis": ["SRC_INFO_001"],
      "assigned_source_information": [
        {{
          "source_info_id": "SRC_INFO_001",
          "source_statement": "statement from the source information",
          "assignment_type": "defines_element | names_element | describes_behavior | describes_property | states_requirement | states_constraint | describes_input | describes_output | mentions_interface | describes_risk | unclear_assignment",
          "confidence": "high | medium | low"
        }}
      ],
      "confidence": "high | medium | low",
      "generation_readiness": "ready | partial | blocked",
      "missing_information": ["missing information related to this element"],
      "rationale_summary": "concise source-based rationale"
    }}
  ],
  "explicit_source_links": [
    {{
      "link_id": "LINK_001",
      "source_element_candidate": "ELEM_001",
      "link_type": "relationship wording supported by the source",
      "target_element_candidate": "ELEM_002",
      "source_basis": ["SRC_INFO_002"],
      "source_statement": "source statement that directly supports the link",
      "confidence": "high | medium | low",
      "rationale_summary": "why the link is considered explicit"
    }}
  ],
  "sysml_model_buildability": [
    {{
      "sysml_model_type": "stakeholder_model | requirements_model | use_case_model | functional_model | logical_architecture_model | physical_architecture_model | interface_model | verification_model | traceability_model",
      "support_level": "supported | partially_supported | not_supported | conflicting",
      "can_be_generated_now": true,
      "generation_scope": "complete_preliminary | partial_preliminary | review_questions_only | blocked",
      "available_information": ["information currently available"],
      "evidence_basis": ["evidence or source references"],
      "missing_information": ["information still required"],
      "reason": "concise buildability rationale",
      "recommended_action": "recommended next information or review step"
    }}
  ],
  "missing_information_for_model_building": [
    {{
      "missing_info_id": "MISS_001",
      "missing_information": "description of missing information",
      "limits_or_blocks": ["affected model or model element type"],
      "needed_for": ["specific SysML model or view"],
      "review_question": "specific question for the human reviewer"
    }}
  ],
  "possible_but_unsupported_interpretations": [
    {{
      "topic": "possible interpretation",
      "reason_not_accepted": "why source evidence is insufficient",
      "review_question": "question required to resolve it"
    }}
  ],
  "model_artifact_assessments": [
    {{
      "model_artifact_type": "model artifact type",
      "support_level": "supported | partially_supported | not_supported | conflicting",
      "evidence_basis": ["evidence reference"],
      "reason": "concise rationale",
      "missing_information": ["missing item"],
      "recommended_action": "next action"
    }}
  ],
  "cross_artifact_observations": [],
  "blocked_generation_tasks": []
}}

Compact examples:

Example 1
Source evidence:
"The technician operates the calibration station."

Correct abstraction:
- ELEM_001 = technician, element_type actor.
- ELEM_002 = calibration station. Its existence is explicit. If its precise
  model classification is uncertain, use the least-assumptive supported type
  and record that uncertainty.
- LINK_001 = ELEM_001 --operates--> ELEM_002.

Do not omit the calibration station merely because its precise model
classification is uncertain.

Example 2
Source evidence:
"The controller shall store the measurement result."

Correct abstraction:
- Materialize source-supported candidates for the controller, the measurement
  result and the source-supported storage behavior as appropriate.
- Preserve the explicit requirement/behavior and its source evidence.
- Do NOT invent a database, storage protocol, persistence technology or
  deployment architecture because none is stated.

Rules:

1. Candidate elements must be based on source information.
2. Preserve traceability through source_basis and assigned_source_information.
3. Do not convert missing information into positive evidence.
4. Do not create relationships that are merely typical or architecturally
   plausible.
5. can_be_generated_now means only that a preliminary model candidate could
   be generated for later human review.
6. It does not mean that the model is approved.
7. Do not generate SysML v2 code.
8. Do not approve or promote data.
9. Use only the exact enum values shown in the required JSON shape.
10. Emit each JSON object key exactly once.

Before returning the JSON, perform this self-check and correct the output if
necessary:

1. Every relationship source endpoint references an existing candidate_id.
2. Every relationship target endpoint references an existing candidate_id.
3. Every explicitly evidenced entity used by a relationship has a candidate.
4. Every enum value exactly matches one of the allowed values.
5. No JSON object contains duplicate keys.
6. Missing, uncertain or absent information was not converted into positive
   evidence.
7. Every relationship has explicit or direct source evidence.
8. No unsupported architecture or implementation detail was invented.

Derivation rules:

{derivation_rules_text}
""".strip()


def get_completeness_checker_task_instructions() -> str:
    """Instructions for completeness review."""

    return """
Return only JSON. Do not wrap the JSON in Markdown fences.

Check the consistency and review-readiness of the prior agent and consensus outputs.

Required JSON shape:
{
  "gaps": [
    {
      "gap_id": "GAP_001",
      "missing_information": "what is missing",
      "why_it_matters": "impact on downstream model generation",
      "suggested_human_action": "what reviewer should do"
    }
  ],
  "ambiguities_and_risks": [
    {
      "risk_id": "RISK_001",
      "topic": "topic",
      "description": "description",
      "potential_impact": "impact",
      "suggested_review_action": "action"
    }
  ],
  "review_questions": [
    {
      "question_id": "RQ_001",
      "question": "question",
      "related_artifact_or_candidate": "reference",
      "reason": "why this matters"
    }
  ],
  "recommended_review_decision": "review_required | suitable_for_review_with_minor_gaps | incomplete_but_reviewable | incomplete_and_blocking"
}

Do not approve or reject data.
Do not generate SysML v2 output.
""".strip()


def get_report_composer_task_instructions(
    *,
    task_id: str,
    recipe_id: str,
    raw_input_path: Path,
) -> str:
    """Instructions for complementary narrative report composition."""

    return f"""
Return only Markdown.

Create a concise narrative supplement for the deterministic ingestion review report.

Do not attempt to replace the structured review tables.
Do not introduce new engineering claims.
Do not invent model elements.
Do not propose relationships.

Use only information from:

- raw source data
- prior agent outputs
- consensus reports
- run metadata

Required structure:

# Narrative Ingestion Summary

## Source and Run

- Task ID: {task_id}
- Recipe ID: {recipe_id}
- Source Path: {raw_input_path}

## Executive Interpretation

Summarize what kind of system information was found.

## Strongly Supported Findings

Summarize high-confidence findings only.

## Areas Requiring Human Review

Summarize ambiguity, disagreement and missing information.

## Modeling Outlook

Summarize which preliminary SysML models appear buildable and which remain blocked.

## Evidence Limitation

State explicitly:

- No source relationships were proposed.
- Only source-supported relationships may be accepted.
- All outputs remain unreviewed.
- Human review is required before model generation input can be approved.
""".strip()

