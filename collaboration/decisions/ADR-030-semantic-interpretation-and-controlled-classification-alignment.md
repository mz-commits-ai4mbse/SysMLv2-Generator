# ADR-030

Semantic Interpretation and Controlled Classification Alignment

Status

Accepted

Date

2026-08-26

## Context

Cross-source processing tests exposed a recurring semantic-contract failure
that is distinct from source grounding and from system integrity.

An LLM may return a professionally meaningful classification expression such
as `architecture`, `condition` or `classification` even when ADR-011 defines a
closed internal `information_type` vocabulary. Treating every such expression
as a failed interpretation couples two responsibilities that should remain
separate:

1. understanding what the Engineering Source means; and
2. representing that meaning with the repository's controlled vocabulary.

The observed terms are test vectors, not mapping rules. This ADR does not
authorize hard-coded aliases such as `architecture -> logical_element` or
`condition -> constraint`; those mappings are context-dependent.

## Decision

The semantic workflow shall explicitly separate professional interpretation
from controlled representation:

```text
Engineering Source
    -> LLM professional interpretation
    -> controlled classification alignment
    -> strict internal semantic contract
    -> consensus / Human Engineering Review
```

An LLM-produced classification expression is a semantic proposal, not an
authoritative internal enum value.

### Controlled classification alignment

Before an interpretation enters the strict internal semantic contract, any
out-of-vocabulary required classification expression shall be aligned to the
accepted controlled vocabulary.

The alignment input retains at least immutable item identity (`EVD-*` or
`SUBJ-*`), field name, raw LLM expression, interpreted statement, relevant
source-grounded context when available and the complete allowed target
vocabulary.

The alignment may change only the explicitly identified classification field.
It may not change item identity or population, interpreted statements, source
grounding, rationale, uncertainty, missing-evidence content, relationships or
already-valid fields.

A value already contained in the controlled vocabulary passes through
unchanged. Pure case/whitespace normalization to one unique controlled token
may be performed deterministically.

If semantic inference is required, exactly one bounded alignment LLM request
may translate the raw expression to the controlled vocabulary using context.
The mapper reports `mapped`, `ambiguous` or `unmapped`.

For `information_type`, `ambiguous` and `unmapped` normalize to the already
accepted neutral value `unclassified`. If the mapper itself violates its
contract, `information_type` may likewise fail safely to `unclassified` rather
than inventing a more specific meaning. A classification dimension without an
accepted neutral value remains fail-closed if alignment cannot produce a valid
controlled target.

The original LLM output remains immutable. Every non-identity alignment is
retained as an auditable record containing item identity, field name, raw
value, normalized value, mapping status, concise rationale/fallback reason,
mapper response identity when applicable and a deterministic fingerprint.
Only normalized controlled values may enter downstream semantic processing.

### Boundary to ontology mapping

Controlled Classification Alignment is not ADR-011 P4.3 Terminology and
Ontology Candidate Mapping. It maps an interpreted classification expression
to the existing engineering classification vocabulary. Project Glossary,
Turing Core, IOF Core and BFO mapping remain downstream and may not become
accidental `information_type` values.

### No source-specific aliases

No source-specific or example-specific semantic alias table is permitted. The
system shall not contain hard-coded translations for the terms observed in the
current test sources.

### Validation boundary

Strict deterministic parsing remains mandatory after alignment. Classification
alignment shall not repair malformed JSON, missing or duplicate item
identities, changed item population, invalid source references, malformed
relationships or system-owned integrity corruption.

The existing bounded R4c classification repair is superseded as the primary
handling of out-of-vocabulary classification expressions. A compatibility
projection may temporarily remain, but the architectural authority is the
explicit alignment artifact.

## Consequences

Semantically reasonable wording no longer fails only because the LLM did not
reproduce one exact internal token. Downstream stages receive normalized
controlled values and unresolved precision becomes visible as `unclassified`
instead of a technical processing failure.

An additional LLM call may be required for persona outputs containing
out-of-vocabulary classifications. Raw and normalized semantics remain fully
traceable.

## Acceptance Criteria

1. Valid controlled classifications pass without an alignment LLM call.
2. Lexical-only normalization is deterministic.
3. Out-of-vocabulary Information Types can be contextually mapped by one
   bounded alignment call.
4. Ambiguous/unmapped Information Types become `unclassified`.
5. An invalid mapper response cannot inject an uncontrolled value.
6. Raw LLM output remains unchanged and alignment provenance is auditable.
7. Structural/identity/integrity failures remain fail-closed.
8. The same alignment service is reusable by Evidence and Subject
   interpretation.
9. No source-specific alias for observed test expressions is introduced.
