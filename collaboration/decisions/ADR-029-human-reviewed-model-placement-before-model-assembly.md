# ADR-029 — Human-Reviewed Model Placement Before Model Assembly

## Status

Accepted

## Date

2026-08-24

## Context

The first live LLM-assisted Phase-H generation attempt for WP-12 Project
`120412` exposed `BLK-006`.

The three modeling personas successfully produced and persisted bounded
projection results for 14 unresolved Approved Inputs. The consolidated result
contained:

```text
proposed_mapping: 0
ambiguous:        10
unmapped:          4
```

The current hybrid deriver treats every non-`proposed_mapping` result as a
generation failure and therefore aborts before a reviewable Candidate Set can
be produced.

This behavior is inconsistent with ADR-028. Material modeling disagreement was
intended to remain explicit variance while Human Model Review remains the
authority boundary.

A second architectural issue became visible at the same time: the current
Phase-H step tries to resolve local framework placement and assemble a complete
model in one operation. This combines two materially different reasoning tasks.

The accepted recovery pattern from R4c is applicable again:

```text
local identification / interpretation
-> Human authority
-> later synthesis
```

For model creation this becomes:

```text
placement
-> Human placement authority
-> model assembly
-> Final Model Review
```

## Decision

### MPA-01 — Model placement is a separate stage

Before model assembly, every model-promotable Approved Engineering Subject shall
receive an explicit placement decision against the pinned Model Structure
Profile.

Placement answers:

> Where does this approved engineering information belong in the model
> framework?

The exact placement is expressed through a profile-controlled rule. The rule
therefore carries the target framework location, model area, element type and,
where encoded by the profile, the Stakeholder / System / Subsystem level.

### MPA-02 — Dedicated modeling personas

LLM-assisted placement uses three dedicated modeling personas:

1. SysML / Profile Modeler
2. System Architecture Modeler
3. Conservative Modeling Reviewer

They belong to the model-placement responsibility and shall not reuse the
legacy-processing / derivation-assessment persona definitions.

All three receive the same Approved Engineering Information and the same pinned
placement options.

### MPA-03 — Persona agreement is not a gate

The three personas reason independently.

Valid outcomes include:

```text
3:0 agreement
2:1 variance
1:1:1 variance
ambiguous
unmapped
```

No majority result and no unanimity requirement may silently create engineering
or model authority.

Persona agreement is advisory evidence only.

### MPA-04 — Human Model Placement Review is the authority boundary

Persona placement results are collected into a reviewable placement bundle.

The Human reviewer decides the authoritative placement for each required
Approved Subject.

The UX shall intentionally follow the already established Human Engineering
Review pattern where practical:

- Pending Decisions
- Reviewed Decisions
- All
- Needs Attention
- explicit persona proposals / variance
- immutable decision history
- explicit reopen / correction

A Human placement decision may select only a placement allowed by the pinned
profile unless a separately governed exception path is introduced.

### MPA-05 — Approved Model Placement Set precedes assembly

A complete, Human-resolved placement population forms the input authority for
model assembly.

Model assembly answers a different question:

> How do the already placed engineering building blocks form one coherent
> model?

Assembly may construct hierarchy, topology and relationships and may create
multiple coordinated model views. One source does not imply one diagram, and
one approved engineering subject does not imply one complete diagram.

### MPA-06 — Relationships remain engineering authority for later assembly

Accepted semantic Relationships from Approved Engineering Information are not
forced through the per-Subject placement decision merely to obtain a target
relationship type.

They remain authoritative engineering semantics and are consumed during the
later assembly / target-representation stage.

### MPA-07 — Preview belongs primarily after placement resolution

The placement stage may show a lightweight framework overview to communicate
where Subjects are being sorted.

Rich model preview belongs after placement decisions have been resolved and
assembly has produced a coherent model draft. That later review may expose
multiple coordinated diagrams and a textual notation view.

### MPA-08 — Candidate / model materialization follows Human placement

A complete Model Candidate Set or Internal Model shall not be created by
silently resolving modeling-persona variance.

Human-resolved placement authority must precede deterministic model
materialization / assembly.

## Relationship to ADR-028

ADR-028 remains authoritative for:

- `eco_deterministic` versus `llm_assisted`,
- advisory strategy recommendation,
- mandatory Human authority,
- review-driven LLM escalation,
- and no upstream reinterpretation.

This ADR supersedes any implementation interpretation of ADR-028 R5-09 that
treats persona unanimity as a prerequisite for successful LLM-assisted
processing. Modeling comparison preserves variance for Human resolution.

## Target lifecycle

```text
Approved Engineering Information
        |
        v
Deterministic placement coverage
        |
        v
Human-selected mode
   |                 |
   | Eco             | LLM-assisted
   v                 v
profile proposal   3 placement personas
   |                 |
   +--------+--------+
            v
Model Placement Review Bundle
            |
            v
Human Model Placement Review
            |
            v
Approved Model Placement Set
            |
            v
Model Assembly
            |
            +--> coordinated diagram view(s)
            +--> textual notation
            |
            v
Final Model Review
            |
            v
Approved downstream model
```

## Consequences

### Positive

- placement uncertainty becomes reviewable rather than fatal,
- Stakeholder / System / Subsystem assignment becomes an explicit Human
  modeling decision,
- persona disagreement becomes useful engineering evidence,
- model assembly receives cleaner, already placed building blocks,
- and the Final Model Review can focus on the assembled model rather than
  re-litigating local placement.

### Trade-offs

- Phase H gains an additional persisted Human authority boundary,
- current direct Candidate generation must be decomposed,
- and the existing Candidate Review / Final Model Review integration must be
  reconciled with the new placement stage without weakening traceability.

## Implementation slices

```text
BLK-006 C1  architecture + dedicated model-placement department
BLK-006 C2  immutable placement proposal / comparison contracts
BLK-006 C3  persisted Human Model Placement Review
BLK-006 C4  Guided Workflow UI analogous to Human Engineering Review
BLK-006 C5  placement-authoritative model assembly + Candidate materialization
BLK-006 C6  live same-project retest + downstream Final Model Review
```
