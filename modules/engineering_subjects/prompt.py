"""Prompt contract for shared pre-persona engineering-subject discovery."""


ENGINEERING_SUBJECT_DISCOVERY_PROMPT_SCHEMA_VERSION = "1.3.1"


def build_engineering_subject_discovery_instructions() -> str:
    """Return the strict shared subject-discovery task."""

    return """
Return only JSON. Do not wrap the JSON in Markdown fences.

You are performing ONE shared, persona-independent discovery step before
professional MBSE interpretation.

Goal:
Identify the distinct engineering subjects that are actually present in the
registered Engineering Source. A subject is something that later MBSE personas
can interpret or classify, such as a role/person, system/application, behavior,
capability-like activity, condition, information concept, engineering assertion,
or explicit engineering question.

Critical architecture rules:
- Do NOT classify subjects as Actor, Requirement, Function, SysML element, etc.
  That professional interpretation happens later.
- Do NOT create SysML v2 model structure.
- Do NOT summarize an entire evidence passage into one subject when it contains
  several independently meaningful engineering subjects.
- Perform a SECOND COVERAGE PASS over every EVIDENCE-marked span before
  returning JSON. Look specifically for independently reviewable engineering
  meaning expressed as:
  * participants, roles, systems, components, applications or information;
  * capabilities, actions, behaviors, functions or state changes;
  * permissions, enabling conditions, guards, limits or constraints;
  * responsibilities, ownership or accountability;
  * required awareness, visibility, observability or feedback;
  * normative, modal or conditional statements such as shall, should, must,
    may, only if, when, unless or remains responsible;
  * explicit unknowns, unresolved decisions, missing definitions or questions.
- In sentences with conjunctions or conditions, create separate subjects when
  the clauses express independently reviewable engineering meaning.
  Generic example: "A may perform B when C permits it" normally contains at
  least the behavior B and the enabling condition C; do not collapse both into
  one paraphrased subject.
- Do not invent semantics that are not supported by the Source.
- Consolidate repeated mentions of the SAME subject into ONE subject entry.
- Perform a final SELF-SUFFICIENCY PASS over every proposed canonical Subject.
  A canonical Subject must be independently referable and professionally
  interpretable as engineering information.
- Do not create a separate canonical Subject for an adjective, adverb,
  auxiliary/modal fragment, relational fragment or other dependent clause
  fragment whose meaning is incomplete without another Source expression.
- A nested or shorter span MAY still be its own Subject when it denotes a
  separately reviewable entity, information item, behavior, condition,
  question or assertion. Source-range containment alone is not a reason to
  reject or merge it.
- Do not use domain-specific word lists for this decision. Judge whether the
  proposed Subject can stand on its own as an engineering review object.
- If a dependent fragment only qualifies, modifies or completes another
  already proposed Subject, keep that meaning with the complete Subject and
  omit the fragment as a separate canonical Subject.
- Example: "the service specialist", "service specialist", and later "the specialist" should
  be one subject when the source context makes the common referent clear.
- If identity is genuinely ambiguous, keep subjects separate and use
  identity_status="uncertain".
- Every positive mention MUST use a SPAN-* marked with at least one EVD-* ID.
- Context-only spans may help resolve pronouns/coreference but MUST NOT become
  positive mention anchors.
- Headings are context only and are not valid positive mention anchors. A concept
  named in a heading may still become a subject when it is supported by a
  separate EVIDENCE-marked non-heading span.
- Do not return copied source text as a locator.
- The system owns exact provenance through TOK-* IDs.
- For every mention, select the first and last TOK-* IDs that bound the exact
  words expressing that mention.
- start_token_id and end_token_id MUST belong to the claimed source_span_id.
- start_token_id must not occur after end_token_id.
- Do not include surrounding punctuation unless it is semantically part of the
  mention.
- Re-check every token range against the TOKEN MAP before returning JSON.
- Do not expose chain-of-thought. Use no rationale field.

Required JSON shape:

{
  "subjects": [
    {
      "canonical_label": "Service Specialist",
      "subject_form": "entity | behavior | assertion | question | information | condition | other",
      "identity_status": "resolved | uncertain",
      "mentions": [
        {
          "source_span_id": "SPAN-000001",
          "start_token_id": "TOK-000001",
          "end_token_id": "TOK-000002"
        }
      ]
    }
  ]
}

Return zero subjects only if the supplied Evidence contains no meaningful
engineering subject.
""".strip()
