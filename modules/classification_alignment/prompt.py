"""Prompt contract for controlled classification alignment."""

from __future__ import annotations

import json

from .contract import CONTROLLED_CLASSIFICATION_VALUES


CLASSIFICATION_ALIGNMENT_PROMPT_SCHEMA_VERSION = "1.0.0"

_INFO_GUIDANCE = {
    "actor": "an interacting role",
    "ambiguity": "an ambiguity",
    "constraint": "a limit, guard, condition, permission or other constraint",
    "decision": "an engineering or design decision",
    "definition": "a definition",
    "function": "behavior or function",
    "gap": "missing engineering information",
    "information_item": "information, data or an information concept",
    "interface": "an interface or interaction boundary",
    "logical_element": "a logical architecture element",
    "open_question": "an unresolved question",
    "physical_element": "a physical architecture element",
    "rationale": "reasoning or justification",
    "requirement": "required system or engineering behavior/property",
    "risk": "a risk",
    "stakeholder": "a concern-holder",
    "unclassified": "no accepted Information Type is sufficiently supported",
    "use_case": "a usage scenario or interaction goal",
    "user_need": "a stakeholder or user need",
}


def build_classification_alignment_instructions() -> str:
    info = "\n".join(f"- {k}: {_INFO_GUIDANCE[k]}" for k in sorted(_INFO_GUIDANCE))
    modality = " | ".join(sorted(CONTROLLED_CLASSIFICATION_VALUES["statement_modality"]))
    epistemic = " | ".join(sorted(CONTROLLED_CLASSIFICATION_VALUES["epistemic_class"]))
    return f"""Return only JSON. Do not use Markdown fences.

You are performing CONTROLLED CLASSIFICATION ALIGNMENT. A preceding LLM has
already interpreted the engineering content. Translate only the explicitly
listed raw classification expressions into this system's controlled
classification vocabulary.

Do not rewrite statements, identities, rationale, uncertainty, relationships
or source meaning. Do not perform SysML derivation, BFO/IOF/Turing Core mapping
or Project Glossary ontology mapping. Do not invent controlled tokens.

A raw term may be a synonym, broader/narrower term, dialect or domain term.
Choose a target from semantic context, not string similarity alone.

Controlled information_type meanings:
{info}

Controlled statement_modality values:
{modality}

Controlled pre-review epistemic_class values:
{epistemic}

mapping_status is mapped, ambiguous or unmapped. For information_type,
ambiguous/unmapped MUST use normalized_value="unclassified". Do not force a
more specific target when the context does not justify it.

Return exactly:
{{"alignments":[{{"item_id":"SUBJ-000001","field_name":"information_type","normalized_value":"constraint","mapping_status":"mapped","rationale":"Concise semantic rationale."}}]}}

Return exactly one alignment per requested item/field pair and no others."""


def build_classification_alignment_input(needs) -> str:
    return json.dumps(
        {
            "schema_version": CLASSIFICATION_ALIGNMENT_PROMPT_SCHEMA_VERSION,
            "alignment_requests": [
                {
                    "item_id": n.item_id,
                    "field_name": n.field_name,
                    "raw_value": n.raw_value,
                    "interpreted_statement": n.interpreted_statement,
                    "context": n.context,
                }
                for n in needs
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
