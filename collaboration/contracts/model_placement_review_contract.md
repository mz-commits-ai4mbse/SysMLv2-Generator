# Model Placement Review Contract

## Purpose

Define the authority boundary between Approved Engineering Information and model
assembly.

Model Placement Review answers only:

> Where does each model-promotable Approved Engineering Subject belong in the
> pinned target framework?

It does not assemble the model.

## Inputs

The placement stage consumes:

- one exact Project,
- the active Approved Engineering Information authority,
- the model-promotable Approved Subjects / Approved Inputs,
- the pinned Framework Template,
- the pinned Model Structure Profile,
- deterministic placement coverage,
- and, in LLM-assisted mode, the same bounded placement options for all three
  dedicated modeling personas.

Accepted semantic Relationships remain authoritative context for later assembly
but are not converted into per-Subject placement decisions.

## Profile-controlled placement

One authoritative placement is represented by one pinned profile rule.

A rule binds:

```text
framework node
model area
permitted element type
RFLP / abstraction level where encoded by the profile
```

For the current Turing profile this makes the distinction between, for example:

```text
stakeholder.*
system.*
subsystem.*
```

explicit and reviewable.

## Persona output

Each modeling persona independently returns, for each requested Approved Input:

```text
proposed_mapping
  selected_rule_id = exactly one allowed rule

ambiguous
  selected_rule_id = null
  alternative_rule_ids = two or more allowed rules

unmapped
  selected_rule_id = null
  alternative_rule_ids = empty
```

All outputs bind the exact Approved Input identity and exact request
fingerprint.

## Comparison semantics

Comparison is required.

Consensus is not required.

The comparison layer shall preserve:

- which persona proposed which rule,
- which rules were proposed,
- whether all personas agreed,
- whether multiple variants exist,
- and which personas explicitly remained unmapped.

The comparison layer shall not:

- majority-vote a rule into authority,
- discard minority proposals,
- reinterpret Approved Engineering Information,
- or fail solely because personas disagree.

## Human Model Placement Review

The Human reviewer sees the Approved Engineering Information first and the
persona proposals second.

The review experience should mirror Human Engineering Review where practical:

```text
Pending Decisions
Reviewed Decisions
All
Needs Attention
```

`Needs Attention` includes at least:

- persona variance,
- ambiguity,
- unmapped proposals,
- and deterministic/persona disagreement.

The Human may select one profile-controlled placement, reject/defer placement,
or reopen an earlier decision according to the immutable decision lifecycle
defined by the implementation slice.

## Output authority

Only Human-resolved placements enter the Approved Model Placement Set.

The Approved Model Placement Set must retain:

- Approved Input / Subject identity,
- exact Approved Engineering Information binding,
- selected profile rule,
- framework node / model area / element type derived from that rule,
- Human reviewer identity,
- decision rationale where required,
- immutable decision identity and fingerprint,
- and full persona-comparison provenance.

## Assembly boundary

Model assembly is downstream and separate.

It may:

- combine placed Subjects,
- organize hierarchy and structure,
- use accepted semantic Relationships,
- determine target relationship representation,
- and create multiple coordinated views of one coherent model.

It shall not silently change a Human-approved placement.

## Preview boundary

Placement Review may provide a lightweight RFLP/framework placement overview.

Diagram and textual-model previews belong primarily to the downstream assembled
model because visualization before placement authority would mix sorting and
assembly responsibilities.
