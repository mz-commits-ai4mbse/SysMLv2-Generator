# R4c.4 Field-Level Canonical Subject Consensus Contract

## Purpose

R4c.4 deterministically compares professional Persona interpretations of the
same canonical `SUBJ-*` population.

It does not rediscover evidence, Mentions or Subjects and performs no LLM call.

## Identity Invariant

Every outcome is keyed by an existing `canonical_subject_id`.

Consensus is valid only when every required Persona run covers the exact same
canonical Subject population.

## One Persona, One Vote

A distinct Persona receives at most one independent vote for one structured
field or one relationship key.

Repeated runs of the same Persona measure intra-Persona stability only.

They shall never be counted as additional independent votes.

For a structured field:

- if all runs of one Persona return the same value, that Persona has one stable
  vote;
- if repeated runs disagree, that Persona is marked `unstable` for that field
  and casts no independent value vote for that field.

For a relationship key:

- presence in all runs gives one supporting Persona vote;
- absence in all runs is an omission;
- mixed presence across repeated runs is intra-Persona instability.

## Structured Field Consensus

Consensus is calculated independently for:

- `information_type`;
- `statement_modality`;
- `epistemic_class`.

The levels are:

- `unanimous` / `high`: all required Personas stably support the same value;
- `majority` / `medium`: one value has a strict majority of all required
  Personas, but unanimity is absent;
- `divergent` / `low`: no value has a strict majority;
- `indeterminate` / `low`: no stable Persona vote exists.

A medium or low field requires explicit review attention.

## Interpreted Statement

`interpreted_statement` is not compared through exact-string voting and is not
passed through a hidden semantic-similarity algorithm.

Persona wording variants are preserved verbatim.

This prevents paraphrase differences from being mistaken for engineering
disagreement while also preventing deterministic code from claiming semantic
equivalence it cannot establish.

Human Review receives the variants together with the structured field
consensus.

## Uncertainty and Missing Evidence

Persona `uncertainties` and `missing_evidence` are preserved as diagnostic
variants.

They do not become additional votes.

Their presence causes the Subject to be marked for review attention even when
the structured classification fields are unanimous.

## Relationship Consensus

Relationship comparison uses the canonical directed key:

```text
(source_subject_id, relationship_kind, target_subject_id)
```

Relationship wording is preserved as Persona statement variants.

Support levels follow the same independent-Persona principle:

- all Personas support the key: `unanimous` / `high`;
- strict majority supports it: `majority` / `medium`;
- otherwise: `divergent` / `low`.

A relationship hint remains pre-model semantics. Consensus does not turn it
into an ontology relation or SysML relationship.

## Human Review Boundary

`human_review_required` is always `true`.

Consensus is decision support, not Engineering Approval.

`review_attention_required` distinguishes fields/Subjects/relationships where
variance or diagnostic uncertainty deserves additional reviewer attention. High
consensus never bypasses the Human Engineering Review stage.

## Information Type Boundary

`information_type` classifies the engineering information expressed about a
canonical Subject.

It does not define the ontological nature or eventual SysML v2 representation
of that Subject.

Turing Core / BFO / IOF mapping and SysML model derivation remain downstream.
