# ADR-026 — Source-Anchored Multi-Persona Interpretation and Cross-Unit Semantic Synthesis

## Status

Accepted

## Date

2026-08-18

## Context

WP12-E2E-DRY-001 exposed a structural limitation in the current Phase-F
multi-agent interpretation and Human Review path.

The original BLK-003 finding showed that semantically equivalent Agent proposals
could become separate Human Review subjects because identity and grouping were
primarily derived after independent broad-context Agent execution.

ADR-025 introduced semantic proposal consolidation, persona-aware consensus,
relationship consolidation, and semantic Human Review projection.

The subsequent BLK-003.1 corrections improved processing robustness:

- exact source-evidence statements no longer collide solely because they share
  one Agent-local source-information identifier,
- unresolved or ambiguous relationship endpoints are preserved for Human Review
  instead of terminating Processing,
- non-recoverable semantic processing errors are classified more precisely at
  the Project Ingestion service boundary.

These corrections resolved the observed hard Processing failure, but the
controlled POST-BLK-003.1 empirical retest exposed a deeper architectural
problem.

### WP12 empirical evidence

Controlled retest:

- Project: `887027`
- Processing Run: `RUN-000001`
- Source: `01_product_overview.md`
- Personas: 3
- Runs per Persona: 2
- Processing result: `awaiting_review`

Observed semantic consolidation result:

- 66 raw Element proposals,
- 66 Element semantic subjects,
- Element consolidation degraded to singletons,
- warning: `semantic_comparator_unavailable`,
- 46 raw Relationship proposals,
- 46 Relationship semantic subjects,
- Relationship consolidation degraded to singletons,
- warning: `relationship_semantic_comparator_invalid`,
- 112 resulting Human Review items.

The LLM calls themselves completed, but their global consolidation outputs were
not safely consumable:

- the Element comparator response was syntactically invalid and could not be
  parsed under the strict contract,
- the Relationship comparator response violated the required complete,
  non-overlapping proposal partition,
- safe fallback behavior therefore retained every proposal as an independent
  singleton subject.

The fallback preserved evidence and authority boundaries, but the resulting
Human Review workload was unacceptable.

### Architectural finding

The live Phase-F workflow currently gives a team-wide stage input to all Agent
personas. Each persona independently derives candidates from broad source
context, and semantic identity is established only afterwards.

Source references therefore provide provenance, but they do not necessarily
provide an explicit orchestration contract that says:

> These Persona outputs are independent interpretations of the same canonical
> source analysis unit.

This turns semantic consolidation into a large global clustering and partitioning
problem.

For the controlled retest, 66 Element proposals and 46 Relationship proposals
had to be reconciled after broad-context derivation. A failure of Element
consolidation also reduces the ability of downstream Relationship consolidation
to identify common endpoints.

### Existing reusable architecture

The repository already contains several compatible upstream concepts.

`SourceProjection` provides deterministic source content, ordered persisted
segments, source locators, segment identifiers, and exact offsets.

`InformationUnitSourceAnchor` provides exact source ranges within persisted
Source Projection segments.

`semantic_extraction` provides persona/run-bound candidate representations with
exact source anchors and excerpts.

`semantic_consensus` already models:

- required Personas,
- repeated Persona runs,
- intra-Persona stability,
- distinct-Persona voting,
- exact source-evidence grouping,
- field variance,
- Human Review requirements,
- and proposed Information Unit drafts.

These concepts shall be reused where compatible.

The existing `InformationUnit` concept shall not be repurposed as the
pre-interpretation orchestration anchor. An Information Unit is already an
interpreted, independently reviewable semantic claim with classification,
epistemic state, extraction provenance, confidence, and content fingerprint.

A separate source-level orchestration identity is therefore required.

---

## Decision

### 1. Introduce canonical Source Analysis Units

Phase F shall introduce an immutable source-level orchestration artifact:

`SourceAnalysisUnit`

Proposed identifier form:

`SAU-000001`

A Source Analysis Unit answers only:

> Which exact portion of the original projected source are the Personas being
> asked to interpret together?

It is not an engineering interpretation and does not itself assert a model
element, requirement, function, relationship, or other semantic meaning.

Each Source Analysis Unit shall bind at least:

- project identity,
- source identity,
- source projection identity,
- source analysis unit identity,
- exact Source Projection segment/range anchors,
- exact source excerpt,
- deterministic source-order information,
- segmentation-profile/version reference,
- immutable content fingerprint.

Source Analysis Units shall remain persona-independent.

No Agent may create or redefine the identity of the Source Analysis Unit it is
asked to assess.

---

### 2. Initial Source Analysis Unit segmentation

For the first implementation, the deterministic persisted Source Projection
segments are the default Source Analysis Unit boundaries.

For text and Markdown sources, the existing Source Projection adapter currently
creates ordered non-empty blank-line blocks.

This default is intentionally conservative:

- it already has deterministic identity and source locations,
- it avoids introducing another LLM-controlled segmentation authority,
- it keeps all Personas on the same bounded source context,
- and it is sufficient for the WP12 controlled source fixtures.

A later versioned segmentation profile may deterministically subdivide Source
Projection segments where evidence shows that smaller analysis units materially
improve comparison quality.

Such subdivision must preserve exact source anchors and must not depend on the
interpretation of an individual Persona.

---

### 3. Source-anchored Persona execution

All configured Personas for a semantic/derivation team shall assess the same
Source Analysis Unit.

Conceptually:

```text
SourceAnalysisUnit SAU-000003
        |
        +-- Persona A / Run 1
        +-- Persona A / Run 2
        +-- Persona B / Run 1
        +-- Persona B / Run 2
        +-- Persona C / Run 1
        +-- Persona C / Run 2
```

Every produced proposal shall retain:

- `source_analysis_unit_id`,
- exact Agent identity,
- Persona identity,
- Persona run index,
- exact source evidence,
- exact Agent wording,
- confidence and rationale,
- and existing immutable provenance.

The Source Analysis Unit identity is the comparison scope, not the semantic
identity of the proposed engineering subject.

One Source Analysis Unit may legitimately produce zero, one, or many proposed
engineering subjects.

---

### 4. Local source-anchored semantic consolidation

Semantic consolidation shall first operate inside one Source Analysis Unit.

The local comparator receives only proposals produced for that Source Analysis
Unit.

Its task is to identify which proposals represent the same local engineering
subject and which remain distinct or uncertain.

Conceptually:

```text
SAU-000003
    |
    +-- Persona A: "remote expert"
    +-- Persona B: "external expert"
    +-- Persona C: "remote specialist"
    |
    +--> Local Subject: Remote Expert
```

The local result shall preserve:

- every exact Agent proposal,
- Persona/run provenance,
- recognition consensus,
- classification variance,
- intra-Persona instability,
- evidence,
- and unresolved semantic differences.

Semantic uncertainty shall remain reviewable.

It shall not be converted into a technical Processing failure merely because the
system cannot safely merge proposals.

---

### 5. Persona voting and repeated runs

A Persona contributes at most one recognition vote to one local engineering
subject.

Repeated runs of the same Persona measure stability and shall not create
additional independent votes.

The existing semantic-consensus principles for distinct-Persona voting and
intra-Persona stability shall be reused where compatible.

---

### 6. Cross-Unit Semantic Synthesis

After all Source Analysis Units of the applicable source scope have been
processed, the locally consolidated engineering subjects shall be synthesized
across Source Analysis Units.

The purpose is to establish project/source-level semantic continuity.

Conceptually:

```text
SAU-000003 / "remote expert"
SAU-000007 / "expert"
SAU-000011 / "remote specialist"
              |
              +--> Engineering Subject: Remote Expert
```

Cross-unit synthesis operates on locally consolidated subjects rather than on
the complete pool of raw Agent proposals.

This substantially reduces comparison scope while preserving all contributing
source and Agent provenance.

Cross-unit synthesis shall be conservative:

- explicit equivalence may consolidate subjects,
- explicit distinction keeps subjects separate,
- uncertainty does not authorize automatic merging,
- unresolved cases remain available to Human Review.

---

### 7. Relationship synthesis and endpoint rebinding

Relationships are first derived with exact source-local proposal provenance.

After cross-unit Element synthesis, Relationship endpoints shall be rebound to
the resulting synthesized Element subjects where exactly resolvable.

Unresolved or ambiguous endpoint bindings remain explicit Human Review findings.

Relationship synthesis shall not invent an endpoint or relationship merely to
complete a graph.

A degraded or uncertain Relationship interpretation shall remain reviewable
provided source evidence and provenance remain trustworthy.

Actual provenance, identity, or artifact-integrity corruption remains a hard
Processing failure.

---

### 8. Compiled Human Review

Human Review shall operate on compiled Engineering Subjects rather than raw
Agent proposals.

The primary review subject shall expose, as applicable:

- synthesized Engineering Subject,
- all contributing Source Analysis Units,
- exact source excerpts,
- all contributing Persona interpretations,
- Persona recognition consensus,
- classification variance,
- intra-Persona instability,
- relationship findings,
- open questions,
- and exact immutable provenance.

The reviewer shall not be forced to accept or reject each independent Agent
proposal when multiple proposals are merely alternative interpretations of the
same engineering subject.

Human Review remains the engineering authorization boundary.

---

### 9. Separation of identities

The following identities represent different concepts and shall not be
collapsed:

`SourceAnalysisUnit`
- Which exact source context is being jointly assessed?

`EvidenceReference`
- Which exact source statement or evidence occurrence supports a proposal?

`AgentProposal`
- What did one exact Persona run propose?

`LocalSemanticSubject`
- Which engineering subject is recognized within one Source Analysis Unit?

`SynthesizedEngineeringSubject`
- Which engineering subject persists across Source Analysis Units?

`InformationUnit`
- Which reviewed semantic claim is eligible for downstream engineering use?

Review workspace identity remains separate from synthesized engineering-subject
identity.

`SES-......` and `SRS-......` remain D4 synthesized-domain identifiers and
shall be preserved in Cross-Unit Synthesis artifacts and exact evidence
locators.

The existing Review Workspace and Approved Input `stable_subject_key` contract
remains lower-case and namespaced. D5 therefore maps synthesized identities
deterministically and one-to-one:

```text
SES-000001 -> semantic:element:ses-000001
SRS-000001 -> semantic:relationship:srs-000001
```

This mapping does not create a new semantic subject and does not replace the
D4 synthesized identifier. It is the downstream Review/Approved-Input identity
representation of the same synthesized authority subject.

This separation is required for traceability, comparability, and safe
Human-in-the-Loop processing.

---

### 10. Comparator failure behavior

Comparator execution remains advisory semantic processing.

A malformed, unavailable, incomplete, or contract-invalid comparator response
shall never authorize an unsafe merge.

Fallback behavior must preserve proposals and evidence.

However, a comparator fallback that would create an unacceptably large Human
Review workload shall be surfaced as a processing-quality finding rather than
silently treated as successful semantic consolidation.

The workflow may still reach Human Review when integrity is preserved, but the
result shall remain visibly degraded.

---

### 11. Implementation slices

Implementation shall proceed in controlled slices.

#### D1 — Source Analysis Unit contract

Introduce:

- immutable Source Analysis Unit type,
- deterministic identifiers,
- source-anchor validation,
- Source Projection binding,
- deterministic fingerprint,
- read/persistence contract,
- focused tests.

No Agent orchestration changes occur in D1.

#### D2 — Unit-bound Persona execution

Change Phase-F orchestration so all configured Persona runs process one explicit
Source Analysis Unit at a time.

Persist the Source Analysis Unit binding in every relevant Agent result.

#### D3 — Source-anchored local semantic consolidation

Consolidate Element and Relationship proposals inside one Source Analysis Unit.

Reuse existing semantic-extraction and semantic-consensus contracts where
compatible.

#### D4 — Cross-unit synthesis and relationship rebinding

Synthesize local subjects across Source Analysis Units and rebind Relationship
endpoints conservatively.

#### D5 — Human Review integration and empirical retest

Project synthesized Engineering Subjects into the existing Human Review
workflow.

Repeat the controlled WP12 Source-01 empirical test and compare:

- raw Agent proposals,
- local subjects,
- cross-unit synthesized subjects,
- Human Review items,
- Persona comparison coverage,
- retained evidence/provenance.

---

## Consequences

### Positive consequences

- Personas are explicitly aligned on the same source context.
- Source provenance becomes an orchestration input rather than only a
  post-hoc traceability attribute.
- Semantic comparison becomes bounded and local before project-wide synthesis.
- Global LLM partition problems are materially reduced.
- Persona consensus becomes easier to interpret.
- Repeated Persona runs remain stability evidence rather than extra votes.
- Human Review operates on engineering subjects rather than raw Agent outputs.
- Exact Agent wording and source evidence remain fully traceable.
- Existing Source Projection, semantic extraction, semantic consensus, and
  Human Review concepts can be reused.
- Comparator degradation no longer automatically explodes the primary review
  model without an explicit quality signal.

### Trade-offs

- Phase-F orchestration becomes more granular.
- More execution records are created because Agent runs are bound to Source
  Analysis Units.
- Cross-unit synthesis introduces an additional explicit semantic layer.
- Runtime and LLM call count may increase if every unit is processed
  independently.
- Batching and caching may be required later for performance, but they must not
  weaken source-unit identity or Persona comparability.
- Existing broad-context prompts and reports require adaptation.

---

## Rejected alternatives

### Only repair the global semantic comparator

Rejected as the sole solution.

The WP12 retest showed concrete parser and partition failures, but even a
technically valid global comparator would still have to reconcile a large pool
of independently generated broad-context proposals after semantic alignment had
already been lost.

Comparator robustness should still improve, but it is not sufficient as the
primary architecture.

### Use `InformationUnit` as the pre-Agent source unit

Rejected.

An Information Unit is already an interpreted semantic claim with engineering
classification, epistemic state, extraction provenance, confidence, and
review-oriented semantics.

Using it as the pre-interpretation orchestration anchor would conflate source
identity with engineering interpretation.

### Let each Persona create its own source-unit identifiers

Rejected.

This recreates the observed problem because identical identifier strings from
different Agent outputs do not establish shared source identity.

Source Analysis Unit identity must be created before Persona interpretation and
must be persona-independent.

### Human Review after every Source Analysis Unit

Rejected as the default workflow.

It would create excessive interaction overhead and prevent a coherent compiled
review of cross-unit semantic continuity.

Human Review occurs after local consolidation and cross-unit synthesis.

### Pure string matching as semantic identity

Rejected.

Lexical normalization is useful evidence but cannot establish semantic
equivalence across legitimate wording variation.

### Unrestricted embedding or LLM similarity as automatic authority

Rejected.

Similarity may support semantic comparison, but uncertainty must not silently
authorize merges or replace Human Review.

---

## Related decisions

- ADR-016 — Human Review Workspace and Approved Input Promotion Architecture
- ADR-017 — Simple-by-Default Interaction and Progressive Disclosure
- ADR-025 — Semantic Proposal Consolidation and Persona-Aware Consensus

---

## WP12 test status impact

ADR-026 does not mark BLK-003 as closed.

Current interpretation:

```text
BLK-003.1 processing robustness
PASS at focused test / controlled processing level

BLK-003 semantic consolidation effectiveness
OPEN

POST-BLK-003.1 empirical result
Processing reached Human Review
but semantic consolidation degraded to singletons
and produced 112 Review Items
```

WP12-E2E-DRY-001 remains the same interrupted controlled dry run.

The run shall not be restarted solely to hide the observed findings.

After implementation and focused validation of D1-D5, the affected Source-01
processing path shall be empirically retested before WP12 continues through the
remaining blocked stages.

---

## Implementation note

No D1-D5 production implementation shall precede acceptance of this ADR.

The implementation shall reuse existing Source Projection, source-anchor,
semantic extraction, semantic consensus, project isolation, fingerprint,
Human Review, and immutable provenance contracts where compatible.

The architecture shall preserve the distinction between:

- deterministic source segmentation,
- Agent interpretation,
- semantic consolidation,
- Human Review,
- and downstream engineering authority.
