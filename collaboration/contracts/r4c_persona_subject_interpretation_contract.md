# R4c Persona Subject Interpretation Contract

## Purpose

R4c.3 performs professional interpretation over the already consolidated
canonical engineering Subject population.

The invariant is:

> Every configured Persona interprets every fixed `SUBJ-*` exactly once.

Persona variance is therefore professional semantic variance over the same
engineering subject population, not variance caused by independent evidence or
subject discovery.

## Existing Semantic Architecture Is Reused

R4c.3 does not introduce a new ontology, Subject-kind taxonomy or parallel
semantic classification vocabulary.

It reuses the accepted Information Classification architecture from:

- `collaboration/decisions/ADR-011-semantic-information-unit-and-ontology-boundary.md`;
- `modules.semantic_extraction.INFORMATION_TYPES`;
- `modules.semantic_extraction.STATEMENT_MODALITIES`;
- `modules.semantic_extraction.EPISTEMIC_CLASSES`.

## Stage Boundary

ADR-011 separates Information Classification from Terminology and Ontology
Candidate Mapping.

Therefore R4c.3 Persona interpretation does **not** load or perform:

- Turing Core concept mapping;
- BFO 2020 mapping;
- IOF Core mapping;
- framework assignment;
- SysML v2 representation selection;
- model derivation.

Those existing semantic references remain available downstream through:

- `context/semantics/turing_core_vocabulary.json`;
- `context/semantics/ontology_registry.json`.

They are linked architecture assets, not R4c.3 classification prompt content.

## Existing Examples and Structural References

No new domain-specific example model is introduced for R4c.3.

The existing reviewed reference remains:

`context/examples/apollo11_structure_reference.md`

Apollo 11 remains a non-normative downstream structural/model-organization
reference. It is not loaded into the R4c.3 Persona classification prompt and is
not an Information Type or ontology authority.

## Inputs

Each Persona receives the same:

- registered Source Projection content;
- `CanonicalSubjectSet`;
- canonical `SUBJ-*` identity;
- all `MNT-*` Source occurrences for each Subject;
- neutral discovery `subject_form`;
- source-backed provenance through the Mention set.

Personas may not create, omit, merge, split or rename Subjects.

## Output per `(Persona, SUBJ-*)`

Each interpretation contains the existing ADR-011 classification dimensions:

- `canonical_subject_id`;
- `interpreted_statement`;
- `information_type`;
- `statement_modality`;
- `epistemic_class`;
- optional `missing_evidence`;
- concise `rationale`;
- `uncertainties`.

There is deliberately no `semantic_kind` field.

There is deliberately no Persona-supplied final confidence value. Confidence
is derived later from deterministic inter-Persona variance and consensus.

## Information Type

`information_type` uses the existing `INFORMATION_TYPES` contract unchanged.

`unclassified` is an explicit valid result. A Persona shall use it when no
accepted Information Type is sufficiently supported.

Terms such as `system`, `application`, `component`, `capability`, `entity` or
`responsibility` shall not be invented as new Information Types.

Where appropriate, their engineering meaning may later be represented by an
accepted Information Type, by a source-supported pre-model relation, or by
downstream Turing Core / ontology candidate mapping.

`information_type` classifies the engineering information expressed about a canonical Subject. It does not define the ontological nature or eventual SysML v2 representation of that Subject.

Turing Core / BFO / IOF mapping and SysML model derivation remain downstream.

## Statement Modality

`statement_modality` uses the existing `STATEMENT_MODALITIES` contract
unchanged.

## Epistemic Class

`epistemic_class` reuses the existing `EPISTEMIC_CLASSES` contract.

R4c.3 pre-review Persona interpretation permits:

- `explicit`;
- `interpretation`;
- `assumption`.

`derivation` remains outside this contract because R4c.3 does not create a
supporting-Subject derivation artifact.

## Downstream Semantic References

Turing Core, BFO and IOF remain part of the accepted semantic reference stack.

They are deliberately not injected into the R4c.3 classification prompt.
Terminology and ontology candidate mapping occurs after Information
Classification so that ontology concepts cannot become accidental
`information_type` values.

## Pre-Model Relationship Hints

Relationship hints are a separate Persona-level relation set over the fixed
canonical Subject population.

They are a bounded comparison vocabulary, not an ontology.

Each relation has explicit directed endpoints:

- `source_subject_id`;
- `relationship_kind`;
- `target_subject_id`;
- source-supported `statement`.

Relationship hints may point only to canonical Subjects in the same fixed
Subject population. They are advisory pre-model semantics and must not create
new Subject identity, ontology mappings or SysML structure.

## Controlled Classification Alignment

Information Type, Statement Modality and Epistemic Class remain controlled
internal dimensions. An LLM-produced classification expression is treated as a
semantic proposal, not as an authoritative enum value.

Before strict parsing, any out-of-vocabulary classification expression is
handled by the controlled alignment defined in ADR-030. Already valid values
pass unchanged; pure lexical normalization may be deterministic; semantic
translation uses one bounded contextual alignment call.

The alignment may modify only the identified classification field. It may not
change Subject identity/population, interpreted statements, rationales,
uncertainties, missing evidence, relationships or already-valid fields.

For `information_type`, ambiguous/unmapped semantics and mapper-contract
failure normalize to the existing neutral value `unclassified`. This withholds
unsupported specificity rather than inventing semantics. No source-specific
alias mapping is permitted.

The original Persona output remains immutable and every non-identity alignment
is retained with raw value, normalized value, mapping status, rationale,
mapper-response identity when applicable and deterministic fingerprint.

Strict parsing still follows alignment. Malformed JSON, population/identity
errors, malformed relationships and system-integrity failures remain hard
failures.

This step is not Turing Core, BFO, IOF or Project Glossary ontology mapping;
those remain downstream under ADR-011.

## Unsupported Relationship Hints

Relationship hints are optional candidate semantics.

An unsupported `relationship_kind` does not justify extending or weakening the
closed comparison vocabulary. It is rejected as a relationship candidate,
retained transparently in `rejected_relationships` with reason
`unsupported_relationship_kind`, and excluded from downstream consensus.

No alias mapping, automatic inversion or fallback to `related_to` is performed.

This is fail-closed at candidate level: invalid optional relationship semantics
cannot enter the accepted relationship set, while otherwise valid Subject
interpretations remain available.

Invalid Subject identities, unknown endpoints, self-relationships, malformed
JSON and malformed relationship objects remain hard validation failures.

## Exact-Population Invariant

For one Persona run:

```text
expected SUBJ-* set == returned SUBJ-* set
```

Missing Subjects, additional Subjects and duplicate interpretations fail
closed.

## Separation from Model Derivation

R4c.3 answers:

> What does this already identified engineering Subject mean from this
> professional perspective, using the accepted Information Classification
> dimensions?

It does not answer:

> Which ontology concept, framework node or SysML v2 representation should be
> selected?

Those remain downstream concerns.
