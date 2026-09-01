# ADR-033 — Concern-Centric Project Reconciliation and Coherent Model Handoff

- **Status:** Accepted
- **Date:** 2026-08-31
- **Decision scope:** BLK-002 project-level multi-source reconciliation
- **Refines:** ADR-032
- **Replaces:** pair-centric S3 orchestration introduced experimentally by I2D.4
- **Does not replace:** source-local Human Review / Approved Input authority, S4 Human Project Authority, S5 Model Impact authority boundaries, or Human Final Model Review

## Context

BLK-002 must reconcile multiple independent Engineering Sources without collapsing
their provenance or allowing an LLM to become Engineering Authority.

The first S3 implementation asked one LLM call to reason across all supplied
Subjects and to construct arbitrary cross-source relations. A later experiment
constrained each call to one Source pair. Both approaches remained relation-centric:
the LLM still had to choose which Subjects should be compared.

Real E2E execution showed that this is the wrong abstraction. The engineering
question is not primarily "which pair of Subjects relates to which other pair?".
It is:

1. Do the Sources belong to the same Project/System context?
2. Which source-local Subjects concern the same engineering topic?
3. For each such topic, are the statements compatible, complementary,
   conflicting, distinct, or uncertain?
4. Which engineering meaning is accepted by Human Project Authority?
5. How does the complete accepted project-level meaning become one coherent
   Model Candidate Set?

The useful analogy is a collection of stickers:
Project Fit determines whether a sticker belongs to the same album/tournament;
semantic indexing groups stickers by the number/topic they concern; only then are
all stickers of that topic assessed together.

## Decision

Project reconciliation is **concern-centric, not pair-centric**.

### S2 — Project Fit

S2 remains unchanged.

Its question is whether each Engineering Source is plausibly in scope for the
current Project/System. Only Sources with an admitted Project Fit gate state may
enter project-level semantic reconciliation.

S2 answers the "same tournament/album?" question. It does not establish semantic
identity between Subjects and does not create Engineering Authority.

### S3A — Global Project Semantic Index

S3A receives all admitted, source-bound Project semantic Subjects in one bounded
semantic-indexing task.

Its single task is:

> Group supplied Subjects by shared engineering concern.

S3A does **not**:
- decide which Source is correct;
- decide conflict or compatibility;
- merge Subjects;
- create model elements;
- create Engineering Authority;
- rank Sources;
- create persisted Case identity.

The LLM sees only transient opaque Subject transport identifiers such as
`SUBJ-0001`. Real `project_subject:...` identity remains application-controlled.

The deterministic application layer validates:
- every supplied Subject appears exactly once;
- no unknown Subject reference is accepted;
- no Subject appears in more than one group;
- no Subject is silently dropped;
- a multi-member Case contains Subjects from at least two different Sources;
- Subjects without a cross-source counterpart become Singleton Cases.

After successful validation, application code deterministically orders Cases and
assigns `CASE-000001`, `CASE-000002`, ... . LLM-generated labels are descriptive
only and never Case identity.

Case identity is fingerprint-bound to:
- Project ID;
- exact global S3 input fingerprint;
- sorted real member `project_subject:...` references.

### S3B — Reconciliation Case Assessment

S3B processes one non-singleton Reconciliation Case per LLM call.

Its single task is:

> Assess how all statements belonging to this one engineering concern fit together.

Allowed outcomes are:
- `equivalent`
- `complementary`
- `potential_conflict`
- `distinct`
- `uncertain`

`unique` is reserved for Singleton Cases and is derived deterministically without
an LLM call.

S3B assesses the Case **as a whole**. It does not expand the Case into a graph of
pairwise relations.

For example, if three Sources state viewer limits of 2, 2 and 5, the result is one
Case with two claim groups and `potential_conflict`, not three pairwise relations.

Claim groups are non-authoritative evidence describing materially different
variants within one Case. For `potential_conflict`, claim groups must partition
all Case members into at least two explicit competing groups.

S3B remains relationship/meaning evidence only. Human Project Authority remains
required for every non-singleton Case.

### Deterministic Project Reconciliation Summary

After every Case has an assessment, application code derives the global Project
Reconciliation summary without an additional LLM call.

The summary may state:
- number of Cases by outcome;
- whether potential cross-source conflicts were detected;
- whether uncertainty exists;
- whether regrouping is required because a Case was assessed as `distinct`;
- whether Human Project Authority is required.

The system must say "no cross-source conflict detected" rather than claiming the
Project is objectively contradiction-free.

### S4 — Human Project Authority

S4 operates on Reconciliation Cases, not synthetic pairwise relations.

S4 may establish that source-bound engineering meaning:
- remains independently active;
- coexists with other source-bound meaning;
- is superseded by explicitly selected source-bound meaning;
- remains unresolved.

No synthetic merged Approved Engineering Input is created.

Singleton Cases retain their existing source-local authority and do not require
an additional semantic LLM assessment.

### Project Engineering State and coherent downstream model handoff

The end product of project reconciliation is **not a list of isolated Cases**.

Resolved Cases, unique retained Subjects, exact source-local authority bindings,
and explicit Human Project decisions together form the Project Engineering State.

That state is handed to the downstream model derivation pipeline as one coherent
project-level engineering handoff.

The downstream model derivation outcome is one coherent **Model Candidate Set**
which may contain, together:
- model elements;
- relationships;
- properties / attributes;
- constraints;
- allocations / usages;
- other required structural model constructs.

Cases are not written into the model one by one.

S3/S4 establish approved engineering meaning. The model-candidate / Phase-H layer
decides how that meaning is represented structurally in SysML v2.

The complete Model Candidate Set is then compared with the accepted model state,
processed through Model Impact / model proposal logic, reviewed by Human Model
Authority, and only then released to the model.

### LLM design principle

For project reconciliation:

> LLMs perform bounded semantic judgments. Deterministic application logic owns
> identity, coverage, orchestration, aggregation, and authority boundaries.

And:

> A singular LLM task does not necessarily mean a tiny input. S3A may see the
> complete bounded Subject set because its task is only semantic indexing. S3B
> sees one Case because its task is only Case assessment.

If the bounded S3A input is ever too large, the system must fail closed until an
explicit indexing reduction/hierarchy architecture is accepted. It must not
silently chunk and infer global grouping equivalence.

## Consequences

### Positive

- Reconciliation matches the actual engineering question rather than creating
  O(n²) relation evidence.
- Conflicts are represented once per engineering concern.
- Human review sees coherent topics and variants rather than redundant pairwise
  edges.
- Source provenance remains intact.
- The LLM no longer controls identity or pair construction.
- The downstream model receives one coherent approved project meaning rather
  than Case-by-Case model mutations.

### Trade-offs

- S3A is a global semantic indexing task and therefore requires an explicit
  bounded-input contract.
- Existing S4 relation-oriented implementation must be adapted to Case-oriented
  authority in a later slice.
- Existing pairwise I2D.4 runtime code must be removed/replaced before the next
  live Project Reconciliation execution.
- Persisted project-reconciliation schema changes, if required, must be additive
  and separately accepted.

## Migration / implementation plan

1. **I2D.5A** — freeze ADR-033 and additive in-memory Case contracts.
2. **I2D.5B** — implement S3A global semantic indexing with transient Subject refs.
3. **I2D.5C** — implement S3B one-Case assessment and deterministic project summary.
4. **I2D.5D** — replace I2D.4 runtime orchestration and define additive persistence.
5. **I2D.5E** — adapt S4 Human Project Authority from relation decisions to Case decisions.
6. Reconnect S5 / I1 project-level handoff so all resolved/unique meaning enters
   one coherent Model Candidate Set.
7. Resume Project 308131 E2E only after the pairwise runtime path has been removed
   and the Case path is green.

No immutable accepted evidence is rewritten by this ADR.
