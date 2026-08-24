"""Prompt contract for Persona interpretation of fixed canonical engineering subjects."""

from __future__ import annotations

from modules.engineering_subjects.types import CanonicalSubjectSet
from modules.semantic_extraction import (
    EPISTEMIC_CLASSES,
    INFORMATION_TYPES,
    STATEMENT_MODALITIES,
)
from modules.source_projection.types import SourceProjectionArtifact

from .errors import SubjectInterpretationConfigurationError
from .types import PRE_MODEL_RELATIONSHIP_KINDS


SUBJECT_INTERPRETATION_PROMPT_SCHEMA_VERSION = "1.4.0"

_PRE_REVIEW_EPISTEMIC_CLASSES = frozenset(
    value
    for value in EPISTEMIC_CLASSES
    if value != "derivation"
)


def _choice_line(values) -> str:
    return " | ".join(sorted(values))


def build_subject_interpretation_task_instructions() -> str:
    """Return the strict professional Persona interpretation task."""

    return f"""
Return only JSON. Do not wrap the JSON in Markdown fences.

You are performing PROFESSIONAL ENGINEERING INTERPRETATION of a canonical
Subject population that has already been discovered and consolidated.

The system has already established:
- exact Engineering Source provenance;
- MNT-* Source occurrences;
- canonical SUBJ-* identity;
- repeated-mention consolidation.

Critical identity boundary:
- Do NOT detect new subjects.
- Do NOT omit supplied subjects.
- Do NOT merge, split or rename subjects.
- Do NOT create new SUBJ-* or MNT-* identities.
- Interpret EACH supplied SUBJ-* exactly once.
- Every Persona receives the exact same SUBJ-* population and Source context.
- Differences should reflect legitimate professional interpretation variance.

R4c.3 CLASSIFICATION STAGE BOUNDARY:
- This stage performs professional interpretation and the EXISTING ADR-011
  Information Classification only.
- Do NOT perform terminology mapping.
- Do NOT perform Turing Core concept mapping.
- Do NOT perform BFO or IOF ontology mapping.
- Do NOT perform framework assignment.
- Do NOT perform SysML v2 model derivation.
- Do NOT use Apollo 11 as classification input.
- Do NOT invent a new Subject-kind or ontology taxonomy.
- Do NOT return `semantic_kind`.
- Do NOT return concept labels such as `system`, `application`, `component`,
  `capability`, `entity` or `responsibility` as information_type unless that
  exact value appears in the allowed information_type list below.

Use ONLY the existing ADR-011 classification dimensions.

Allowed information_type values:
{_choice_line(INFORMATION_TYPES)}

Allowed statement_modality values:
{_choice_line(STATEMENT_MODALITIES)}

Allowed pre-review epistemic_class values:
{_choice_line(_PRE_REVIEW_EPISTEMIC_CLASSES)}

Information Type guidance:
- `actor` identifies an interacting role.
- `stakeholder` identifies a concern-holder.
- `user_need`, `requirement` and `use_case` classify the corresponding
  stakeholder/system engineering information.
- `function` classifies behavior/function information when justified.
- `logical_element` and `physical_element` classify architecture-element
  information when the Source supports that distinction.
- `interface` classifies interface information.
- `constraint` classifies limits, guards, permissions or other constraining
  engineering information when appropriate.
- `information_item` classifies information/data concepts.
- `definition`, `rationale`, `decision`, `risk`, `ambiguity`, `gap` and
  `open_question` retain their accepted ADR-011 meanings.
- `unclassified` is the correct result when no accepted Information Type is
  sufficiently supported.
- Never manufacture a new information_type to avoid `unclassified`.

Epistemic rules:
- `epistemic_class = derivation` is not allowed here because this contract does
  not create derived Subjects or supporting-Subject derivations.
- For `assumption`, `missing_evidence` must identify what is missing.
- For `explicit` or `interpretation`, `missing_evidence` must be null.
- Preserve uncertainty instead of forcing unsupported precision.
- Do not expose chain-of-thought. Use concise rationale summaries only.
- Do not output an LLM confidence score. Confidence is derived later from
  deterministic inter-Persona variance/consensus.

PRE-MODEL RELATIONSHIP HINTS:
Relationships are a separate top-level list over the same fixed Subject
population. They exist only to make source-supported semantic relations
comparable before Human Engineering Review.

Allowed relationship_kind values:
{_choice_line(PRE_MODEL_RELATIONSHIP_KINDS)}

Each relationship must use explicit directed endpoints:
- source_subject_id
- relationship_kind
- target_subject_id
- statement

Use the canonical predicate direction. Do not invent inverse or lexical
variants. `related_to` is the fallback only when no more precise allowed
predicate is justified.

Relationship hints:
- may reference ONLY supplied SUBJ-* IDs;
- must not self-reference;
- must be source-supported;
- are not ontology relations;
- are not SysML relationships;
- are not model-generation authorization.
- If no allowed relationship_kind is justified, OMIT that relationship
  entirely.
- Never emit an unsupported predicate as a placeholder, comment, diagnostic or
  "not supported" relationship object.

Required JSON shape:
{{
  "interpretations": [
    {{
      "canonical_subject_id": "SUBJ-000001",
      "interpreted_statement": "concise professional interpretation",
      "information_type": "unclassified",
      "statement_modality": "descriptive",
      "epistemic_class": "explicit",
      "missing_evidence": null,
      "rationale": "concise rationale summary",
      "uncertainties": []
    }}
  ],
  "relationships": [
    {{
      "source_subject_id": "SUBJ-000001",
      "relationship_kind": "related_to",
      "target_subject_id": "SUBJ-000002",
      "statement": "concise source-supported semantic relationship"
    }}
  ]
}}

Return one and only one interpretation for every supplied SUBJ-* ID.
Return no SUBJ-* ID that was not supplied.
""".strip()


def build_subject_interpretation_input(
    source_projection: SourceProjectionArtifact,
    subject_set: CanonicalSubjectSet,
    **_ignored,
) -> str:
    """Build identical Source + fixed Subject input, without ontology context."""

    if not isinstance(source_projection, SourceProjectionArtifact):
        raise SubjectInterpretationConfigurationError(
            "source_projection must be a SourceProjectionArtifact."
        )
    if not isinstance(subject_set, CanonicalSubjectSet):
        raise SubjectInterpretationConfigurationError(
            "subject_set must be a CanonicalSubjectSet."
        )

    manifest = source_projection.manifest
    if (
        subject_set.project_id != manifest.project_id
        or subject_set.source_id != manifest.source_id
        or subject_set.source_projection_id != manifest.source_projection_id
        or subject_set.source_projection_fingerprint
        != manifest.projection_fingerprint
    ):
        raise SubjectInterpretationConfigurationError(
            "Canonical Subject Set does not bind the supplied Source Projection."
        )

    mention_by_id = {
        mention.mention_id: mention
        for mention in subject_set.mentions
    }

    sections = [
        "# ENGINEERING SOURCE CONTEXT",
        "",
        "<<<BEGIN_SOURCE",
        source_projection.content,
        "END_SOURCE>>>",
        "",
        "# FIXED CANONICAL ENGINEERING SUBJECTS",
        "",
        (
            "SUBJ-* identity and MNT-* provenance are system-owned and immutable. "
            "Interpret every supplied Subject exactly once."
        ),
        "",
    ]

    for subject in subject_set.subjects:
        sections.extend(
            [
                f"## {subject.canonical_subject_id}",
                f"canonical_label: {subject.canonical_label}",
                f"neutral_subject_form: {subject.subject_form}",
                f"identity_status: {subject.identity_status}",
                "source_mentions:",
            ]
        )

        for mention_id in subject.mention_ids:
            mention = mention_by_id.get(mention_id)
            if mention is None:
                raise SubjectInterpretationConfigurationError(
                    "Canonical Subject references an unknown MNT-* identity."
                )
            evidence = ",".join(mention.source_evidence_ids)
            sections.append(
                f"- {mention.mention_id} | {evidence} | {mention.exact_text!r}"
            )

        sections.append("")

    sections.extend(
        [
            "# TASK",
            "",
            (
                "Interpret every fixed SUBJ-* exactly once using ONLY the "
                "existing ADR-011 Information Type, Statement Modality and "
                "Epistemic Class dimensions. Then return any source-supported "
                "directed pre-model relationship hints. Return JSON only."
            ),
        ]
    )

    return "\n".join(sections)
