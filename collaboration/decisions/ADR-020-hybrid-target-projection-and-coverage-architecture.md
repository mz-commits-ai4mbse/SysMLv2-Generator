# ADR-020 — Hybrid Target Projection and Coverage Architecture

## Status

Accepted

## Date

2026-08-13

## Context

Phase H derives target-model Candidates from reviewed Approved Inputs.

The existing `ProfileDrivenModelCandidateDeriver` is intentionally conservative
and deterministic. It maps reviewed information only when the selected Model
Structure Profile supports the mapping and fails closed when no supported
mapping exists or a mapping is ambiguous.

This behavior is valuable as a fast, reproducible projection path, but it is
not sufficient as the only target-projection strategy for heterogeneous
engineering information. A selected modeling framework must not force valid
engineering information into an unsuitable target-model shape, and information
that cannot be projected must not disappear silently.

The Phase-H orchestration already depends on the `ModelCandidateDeriver`
protocol rather than one concrete derivation implementation. This allows the
existing deterministic strategy to remain available while a second,
LLM-assisted strategy is introduced without changing the Phase-H → Phase-I
authority boundary.

Phase I remains responsible only for assembling human-authorized Model
Candidates into the Internal Engineering Model. Phase I shall not be reopened
for target-projection reasoning.

The executable prototype schedule requires a bounded extension. The existing
deterministic path shall therefore be preserved and reused as the first stage
of the hybrid path.

CATIA requirement/function reconciliation is intentionally deferred to Phase
N2, where capabilities and architecture decisions introduced during Phases
G–L are reconciled as one coherent model update.

---

## Decision

### H9-01 — Preserve strict deterministic projection

`ProfileDrivenModelCandidateDeriver` remains a supported target-projection
strategy.

It shall continue to:

- use only the pinned Framework Template, Model Structure Profile and
  derivation rules,
- derive only profile-supported Candidate semantics,
- fail closed on ambiguous or unsupported target mappings,
- and require no LLM execution.

This path is the fast / reproducible projection option and may be used for
quick checks, dry runs and inputs that are already sufficiently classified.

---

### H9-02 — Explicit projection dispositions

Every active Approved Input considered for target projection shall receive
exactly one projection disposition:

- `mapped`
- `ambiguous`
- `unmapped`
- `intentionally_not_projected`

`human_clarification` Approved Inputs remain reviewed context and are
`intentionally_not_projected` unless a later accepted architecture explicitly
changes that rule.

---

### H9-03 — Complete projection coverage

Projection coverage shall account for the complete active Approved-Input
snapshot.

The invariant is:

```text
mapped
+ ambiguous
+ unmapped
+ intentionally_not_projected
= total Approved Inputs considered
```

No Approved Input may disappear silently because it does not fit the selected
Framework or Model Structure Profile.

`unmapped` describes a limitation of the selected target projection, not a
rejection of the underlying approved engineering information.

---

### H9-04 — Shared deterministic profile resolver

The profile-matching logic shall be factored into one reusable deterministic
resolver.

Both strict deterministic projection and later LLM-assisted projection shall
use this resolver.

The system shall not maintain separate deterministic mapping semantics for the
two modes.

---

### H9-05 — Deterministic-first hybrid projection

The LLM-assisted strategy shall execute deterministic profile resolution first.

Inputs resolved uniquely by the deterministic resolver shall not be sent to
the LLM in the normal hybrid path.

Only inputs classified as `ambiguous` or `unmapped` are eligible for
LLM-assisted target-projection reasoning.

This limits token use, request rate and unnecessary semantic reinterpretation.

---

### H9-06 — LLM output remains Candidate-level modeling

The LLM-assisted mapper shall not generate normative SysML v2 text.

It may propose structured target-model semantics such as target model area,
element type, framework assignment, relationship semantic intent, rationale,
alternatives, or an explicit `unmapped` result.

Generated proposals remain Phase-H Candidate information.

---

### H9-07 — No forced mapping

The LLM-assisted path is not required to map every Approved Input.

If the selected Framework/Profile has no defensible representation, the result
shall remain explicitly `unmapped`.

The LLM shall not invent an engineering meaning merely to achieve target
coverage.

---

### H9-08 — Existing Human Review authority remains unchanged

LLM-assisted projections do not become approved engineering information merely
because a model produced them.

They shall pass the same Candidate validation and Human Review authority
boundary as deterministic Model Candidates.

The sole Phase-H → Phase-I boundary remains:

`ModelCandidateReadService.load_phase_i_input(project_id, candidate_set_id)`

No Phase-I contract change is required by H9.

---

### H9-09 — Projection provenance

The derivation path shall remain traceable through
`ModelCandidateGenerationProvenance`.

For LLM-assisted projection, provenance shall identify at least the applicable
derivation method, model reference, recipe and/or agent reference where
applicable, and context fingerprint.

Per-input LLM projection evidence shall remain attributable to the affected
Approved Input.

---

### H9-10 — Token and request-rate protection

The normal LLM-assisted path shall minimize model traffic by design.

It shall:

- perform deterministic resolution first,
- send only unresolved inputs,
- avoid resending complete source documents when bounded Approved-Input content
  is sufficient,
- send only relevant target-profile context,
- support bounded batching where appropriate,
- avoid reinterpreting uniquely mapped deterministic results,
- and avoid unbounded automatic retry loops.

Correctness and explicit uncertainty remain more important than forcing a
mapping.

---

### H9-11 — Phase J remains deterministic serialization

H9 changes target-model projection in Phase H.

It does not move semantic interpretation into Phase J.

Phase J continues to receive a validated Internal Engineering Model and
serialize already accepted model semantics to the selected SysML v2 target
notation.

---

### H9-12 — CATIA reconciliation is deferred to Phase N2

H9 may introduce capabilities that require requirement/function reconciliation,
including selectable deterministic and LLM-assisted target projection,
projection coverage assessment, explicit ambiguous/unmapped preservation,
deterministic-first LLM routing, and LLM projection provenance.

These are reconciliation candidates only.

No CATIA Requirement or Function shall be added or modified as part of the H9
implementation closeout. Final coverage assessment and model changes belong to
Phase N2.

---

## Initial implementation decomposition

```text
H9.1  Projection disposition and coverage model
H9.2  Shared deterministic profile resolver
H9.3  Strict deterministic deriver migrated to shared resolver
H9.4  Structured LLM projection contract
H9.5  Token-conscious HybridModelCandidateDeriver
H9.6  Merge, validation and provenance
H9.7  Human Review / Phase-I compatibility regression
H9.8  SSOT closeout and Phase-N2 reconciliation candidate recording
```

H9.1–H9.3 require no LLM request.

---

## Consequences

### Positive

- deterministic projection remains available and fast,
- framework limitations become visible instead of silently losing information,
- LLM usage is concentrated on cases that actually require semantic reasoning,
- Phase I remains stable,
- Human Review authority remains stable,
- the architecture supports future alternative Framework/Profile combinations,
- and Phase J can remain reproducible.

### Trade-offs

- Phase H gains an additional projection-coverage concept,
- hybrid execution will require explicit LLM response validation,
- unresolved information can legitimately remain unmapped,
- and final CATIA capability reconciliation is deferred until Phase N2.

---

## Acceptance

Accepted by the project owner on 2026-08-13 before H9 implementation.
