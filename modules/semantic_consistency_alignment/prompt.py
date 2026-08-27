"""Prompt contract for semantic field consistency alignment."""

from __future__ import annotations

import json


SEMANTIC_CONSISTENCY_PROMPT_SCHEMA_VERSION = "1.0.0"


def build_semantic_consistency_instructions() -> str:
    return """Return only JSON. Do not use Markdown fences.

You are performing SEMANTIC FIELD CONSISTENCY ALIGNMENT after a professional
engineering interpretation and after controlled classification alignment.

Resolve only the coupled fields epistemic_class and missing_evidence for the
explicitly requested items. Preserve the interpreted engineering meaning.

Allowed normalized pairs are exactly:
- explicit + null
- interpretation + null
- assumption + non-empty trimmed textual missing_evidence

If the raw missing_evidence content represents a genuine evidence gap that is
required to support the interpreted statement, normalize to assumption and
preserve that gap as concise text.

If the raw missing_evidence content is commentary, formatting spillover,
classification commentary, or otherwise not a genuine evidence gap, use
explicit or interpretation as justified by the statement/context and set
missing_evidence to null.

Do not rewrite item identity, interpreted statement, information_type,
statement_modality, rationale, uncertainties, relationships, source grounding
or item population.

Do not force validity by discarding genuine missing-evidence meaning.

Return exactly:
{"resolutions":[{"item_id":"SUBJ-000001","normalized_epistemic_class":"explicit","normalized_missing_evidence":null,"rationale":"Concise semantic rationale."}]}

Return exactly one resolution per requested item and no others."""


def build_semantic_consistency_input(needs) -> str:
    return json.dumps(
        {
            "schema_version": SEMANTIC_CONSISTENCY_PROMPT_SCHEMA_VERSION,
            "consistency_requests": [
                {
                    "item_id": item.item_id,
                    "interpreted_statement": item.interpreted_statement,
                    "raw_epistemic_class": item.raw_epistemic_class,
                    "raw_missing_evidence": item.raw_missing_evidence,
                    "context": item.context,
                }
                for item in needs
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
