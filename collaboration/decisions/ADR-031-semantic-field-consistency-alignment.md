# ADR-031

Semantic Field Consistency Alignment

Status

Accepted

Date

2026-08-26

## Context

ADR-030 separates professional semantic interpretation from controlled
classification vocabulary. Cross-source retry RUN-000004 then exposed a
different failure class after classification alignment had succeeded.

The LLM returned a valid controlled `epistemic_class="explicit"` together with
a non-null object-valued `missing_evidence`. The object contained explanatory
semantic text, but the strict internal contract requires the coupled invariant:

- `assumption` -> non-empty textual `missing_evidence`
- `explicit` / `interpretation` -> `missing_evidence=null`

This is not a classification-vocabulary problem. It is a semantic consistency
problem between two coupled fields.

Blindly coercing every non-null value to null would be unsafe because a
non-null value may represent a genuine evidence gap and therefore justify
`epistemic_class="assumption"` instead. The system must preserve meaning rather
than merely force schema validity.

The same coupled invariant exists in both Evidence Interpretation and Subject
Interpretation.

## Decision

A reusable Semantic Field Consistency Alignment step shall run after
Controlled Classification Alignment and before the strict interpretation
parser:

```text
LLM professional interpretation
    -> Controlled Classification Alignment
    -> Semantic Field Consistency Alignment
    -> strict deterministic interpretation contract
    -> downstream consensus / Human Engineering Review
```

The first supported coupled field set is:

```text
epistemic_class + missing_evidence
```

### Trigger

No additional LLM request is made when the pair already satisfies the internal
contract.

A consistency-alignment need is created only when:

- `epistemic_class` is one of the accepted pre-review values; and
- the coupled `missing_evidence` value violates the deterministic pair
  invariant.

Malformed item identity, changed population, malformed JSON, invalid
relationships and other structural failures remain outside this recovery
mechanism.

### Bounded contextual resolution

All inconsistent pairs in one persona output are batched into exactly one
bounded mapper request.

For each requested item the mapper sees immutable item identity, interpreted
statement, raw epistemic class, raw `missing_evidence`, and source-grounded
context when available.

The mapper may change only:

- `epistemic_class`
- `missing_evidence`

It may not change identity, population, interpreted statement, information
type, modality, rationale, uncertainties, relationships or source grounding.

The normalized pair must satisfy exactly one of:

- `explicit` + `null`
- `interpretation` + `null`
- `assumption` + non-empty trimmed text

If the raw non-null content represents a genuine evidence gap, the mapper may
normalize to `assumption` and preserve that meaning as concise textual
`missing_evidence`. If it does not represent a genuine evidence gap, the
mapper may retain/choose `explicit` or `interpretation` and normalize
`missing_evidence` to null.

There is no automatic neutral fallback for an unresolved pair. Mapper
execution or contract failure remains fail-closed because silently discarding
possible missing-evidence meaning would reduce semantic quality.

### Auditability

The raw LLM output remains immutable.

Every non-identity consistency decision is persisted with raw and normalized
pair values, rationale, mapper response identity and deterministic
fingerprint. Only the normalized output enters the strict parser.

### Boundary to ADR-030

ADR-030 remains authoritative for controlled classification vocabulary and
continues to prohibit Classification Alignment from modifying
`missing_evidence`.

ADR-031 is a separate downstream consistency layer for semantically coupled
fields and does not weaken ADR-030's field authority.

## Acceptance Criteria

1. Already-consistent pairs pass without an additional LLM request.
2. Inconsistent pairs are batched into one bounded request per persona output.
3. The mapper may modify only `epistemic_class` and `missing_evidence`.
4. Every normalized pair satisfies the deterministic pair invariant.
5. Genuine evidence-gap meaning can be retained by normalizing to
   `assumption` plus textual `missing_evidence`.
6. No automatic nulling or other lossy fallback is permitted on mapper
   execution/validation failure.
7. Raw outputs remain immutable and decisions are auditable.
8. The service is reusable by Evidence and Subject Interpretation.
9. Structural, identity and relationship failures remain fail-closed.
