# ADR-034 — Source Provenance Does Not Constrain Concern Grouping

**Status:** Accepted refinement of ADR-033
**Scope:** BLK-002 / I2D.5D4

## Context

ADR-033 replaced pair-centric cross-source reconciliation with concern-centric
Project Reconciliation Cases. During the first live Project 308131 run, S3A
returned a multi-member semantic group whose Subjects all originated from one
Source. The existing Case contract rejected that group because a multi-member
Case was required to span at least two Sources.

That restriction carries forward source-pair semantics into a concern-centric
architecture. It is especially inappropriate for well-separated engineering
documents, where several Subjects from one document may legitimately address
the same engineering concern.

The source of a Subject remains important for provenance, traceability, source-
local Human Authority, and later project-level authority. It is not semantic
evidence that determines whether Subjects concern the same topic.

## Decision

Reconciliation Case membership is determined solely by shared engineering
concern.

`source_id` is provenance only and SHALL NOT constrain semantic concern
grouping.

Therefore:

- A one-member group becomes a Singleton Case.
- A multi-member Case MAY contain Subjects from one Source or multiple Sources.
- `unique` is defined by one Subject, not by one Source.
- Every real source binding remains preserved on every Subject and Case.
- Same-source multi-member Cases remain non-singleton Cases and therefore
  receive the normal S3B bounded semantic assessment.
- No automatic cross-group merging, source balancing, or source-based splitting
  is permitted.
- Exact Subject coverage, no duplicates, known references, deterministic Case
  identity, and immutable provenance remain fail-closed constraints.

## Rationale

The concern-centric architecture separates semantics from provenance:

> Semantic meaning decides grouping. Source provenance records where evidence
> came from.

This is analogous to grouping Panini stickers by motif regardless of the kiosk
where a packet was purchased. The purchase location is traceability metadata,
not part of the motif identity.

## Consequences

The former invariant

`multi-member Case => at least two Sources`

is removed from the S3A Case contract and persistence validation.

Case identity remains unchanged and continues to bind:

- project identity,
- exact semantic input fingerprint,
- exact sorted Subject references.

No persisted PRC cycle schema changes. Existing semantic-index schema 1.0.0
remains readable, and provenance-bearing semantic-index schema 1.1.0 remains
the live S3A format.

Human Project Authority remains Case-aware and is still a later gate. This ADR
does not create authority and does not alter source-local Approved Engineering
Input.
