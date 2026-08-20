# ADR-025 — Semantic Proposal Consolidation and Persona-Aware Consensus

## Status

Accepted

## Date

2026-08-17

## Context

The WP-12 controlled multi-document dry run exposed a structural mismatch between
the ingestion proposal layer and the Human Review experience.

The current review projection can materialize several independent Review Items for
Agent proposals that refer to the same engineering concept but use different
wording or a different proposed element classification. This creates excessive
Human decisions and can hide the most useful form of variance: different Persona
interpretations of one semantic subject.

The same problem exists for relationships. Syntactically different predicates can
express the same engineering relation, while current identity and consensus paths
do not provide a stable semantic relationship subject.

This is not a reason to make Agent output contract-perfect before Human Review.
Reviewable semantic uncertainty remains legitimate processing output. The Human
Review boundary exists to resolve modeling ambiguity, classification variance,
relationship ambiguity, and other engineering uncertainty. Hard authority and
integrity failures remain fail-closed.

The architecture therefore needs a derived, immutable layer that answers one
limited question before Human Review:

> Which exact existing Agent proposals appear to refer to the same engineering
> subject?

That layer must never invent a new engineering statement, silently discard source
evidence, convert agreement into Human approval, or make uncertain equivalence
authoritative.

## Decision

Introduce a **Semantic Proposal Consolidation** layer between structured derivation
proposals and the Persona-aware consensus / Human Review projection.

The target flow is:

```text
Exact immutable Agent Proposals
+ exact Source Evidence
        ↓
Semantic Consolidation
        │
        ├─ Elements
        │   group by engineering meaning,
        │   not by exact name or element_type
        │
        ├─ Relationships
        │   group by consolidated endpoint subjects
        │   and semantic predicate meaning
        │
        └─ comparison outcomes
            equivalent | distinct | uncertain
        ↓
Immutable Semantic Consolidation Artifact
        ↓
Persona-aware Consensus Projection
        ↓
one Engineering Review subject per semantic subject
        ↓
Human Review
```

Semantic consolidation executes during Processing, after structured derivation
proposals exist and before the Processing Run reaches `awaiting_review`.
Opening Human Review reconstructs persisted results and does not initiate a new
semantic-model call.

## Authority boundary

The Semantic Consolidation Artifact is **derived processing evidence**. It is not
an Approved Input, Model Candidate, Internal Engineering Model, or Human approval.

The consolidator may only classify relations among already-existing exact
proposals. It must not:

- create a new engineering claim;
- overwrite an Agent proposal;
- mutate source evidence;
- silently select an element classification;
- silently resolve an uncertain relationship endpoint;
- turn Persona agreement into Human approval;
- infer that two proposals are equivalent when the comparison result is
  `uncertain` or unavailable.

Every semantic subject remains traceable to the exact immutable proposal,
Agent/Persona/run, upstream artifact fingerprint, and source-evidence references
from which it was derived.

## Merge authority

A semantic merge is permitted only when explicit consolidation evidence classifies
the relevant proposals as `equivalent`.

The contract is fail-closed **against merge authority**:

```text
equivalent
→ may support one semantic subject

distinct
→ must remain separate

uncertain
→ must remain separate and remain visible for Human reasoning

missing / malformed comparison
→ cannot authorize a merge
```

A multi-proposal semantic subject must therefore be connected by explicit
`equivalent` comparison evidence. A `distinct` or `uncertain` comparison inside
one semantic subject is an integrity failure. An `equivalent` comparison across
two different subjects is also an integrity failure.

This rule allows safe degradation toward singleton semantic subjects without
inventing equivalence.

## Element identity

`element_type` is explicitly **not** part of semantic-subject identity.

Different Personas may recognize the same engineering concept while proposing
different modeling classifications. Such disagreement must become visible
classification variance on one Review subject.

Example:

```text
"separate client application"

Persona A → interface
Persona B → system
Persona C → system

Recognition:
3 / 3 Personas

Classification:
2 × system
1 × interface

→ one semantic subject
→ visible variance
→ explicit Human decision
```

## Relationship identity

Relationship consolidation is based on:

1. already consolidated semantic source subject;
2. already consolidated semantic target subject; and
3. semantic meaning of the relationship predicate.

Surface wording alone is not relationship identity. For example, `retain`,
`retains`, and `should retain` may represent one semantic relationship when
comparison evidence supports equivalence.

Relationship consolidation must not silently repair unresolved endpoints.
Reviewable endpoint uncertainty remains eligible for Human Review under the
existing Human-in-the-Loop boundary.

## Persona-aware consensus

Consensus is counted by **Persona perspective**, not by raw Agent run.

Multiple runs of one Persona do not create multiple votes:

```text
Persona A / Run 1 ─┐
Persona A / Run 2 ─┴→ one Persona perspective

Persona B / Run 1 ─┐
Persona B / Run 2 ─┴→ one Persona perspective
```

Divergence between repeated runs of one Persona is retained as
**intra-Persona instability**. It is evidence, not additional voting weight.

Full Persona agreement remains a processing observation only and never constitutes
Human approval.

## Semantic comparator

A later implementation slice may use a semantic model for comparisons. The
comparison context must remain bounded to the minimum information needed for
semantic equivalence assessment, for example:

- exact proposal reference;
- candidate / relationship wording;
- proposed classification where relevant;
- concise proposal description;
- exact source-evidence reference / statement.

The entire legacy document, unrelated Agent rationale, or unrelated project
context must not be resent by default.

Deterministic pre-filtering may reduce the number of semantic comparisons, but it
must not authorize a semantic merge unless the resulting consolidation contract
contains explicit valid equivalence evidence.

## C1 — Immutable consolidation contract

The first implementation slice introduces only the artifact contract and its
architecture tests. C1 performs no LLM call and no production clustering.

The artifact binds:

- exact Project ID;
- exact Processing Run ID;
- immutable upstream artifact references and fingerprints;
- exact proposal references;
- proposal kind;
- Agent ID;
- Persona ID;
- run index;
- exact source-evidence references;
- semantic subjects and their exact member proposal references;
- explicit pairwise comparison outcomes and comparison provenance;
- an input-set fingerprint; and
- an artifact fingerprint.

The C1 contract requires:

- deterministic ordering;
- unique upstream artifact references;
- unique proposal references;
- every proposal to belong to exactly one semantic subject;
- no proposal to occur in more than one semantic subject;
- proposal kind to match semantic-subject kind;
- unique unordered comparison pairs;
- no self-comparison;
- comparison references to resolve to known proposals of the same kind;
- multi-member subjects to have a connected graph of explicit `equivalent`
  comparisons;
- no `distinct` or `uncertain` comparison within one subject;
- no `equivalent` comparison across different subjects;
- exact fingerprint validation on deserialization.

Repeated proposals from the same Persona with different run indexes are valid
input. C1 deliberately does not count them as independent votes.

## Implementation slices

```text
C1  SemanticConsolidationArtifact + fail-closed contracts
C2  Element semantic clustering + Persona-aware consensus
C3  Relationship semantic clustering + consensus
C4  Review projection/cards + empirical before/after test
```

C2–C4 must be reviewed against the persisted C1 contract and existing Human
Review authority before integration.

## Acceptance criteria

The completed architecture is accepted when:

- semantically equivalent wordings become one Review subject;
- different element classifications of the same concept remain one subject with
  visible variance;
- repeated runs of one Persona do not add votes;
- truly distinct engineering concepts remain separate;
- uncertain equivalence is never silently merged;
- relationships receive semantic consolidation and Persona-aware consensus;
- every original proposal and its source evidence remain inspectable;
- the Human can split an incorrect semantic cluster before approval; and
- full semantic agreement never implies Human approval.

No fixed target number of Review decisions is an acceptance criterion. The
solution must not be optimized to the current WP-12 synthetic dataset.

## WP-12 evaluation use

The existing WP-12 retest state with 68 Human decisions is retained as immutable
before-evidence. After C1–C4 are accepted, a new isolated Processing Run shall use
the same source / Persona / run configuration for an empirical before/after
comparison.

No additional live LLM test is required for C1.

## Consequences

### Positive

- Human Review operates on engineering subjects rather than duplicated strings.
- Classification variance becomes visible instead of fragmenting identity.
- Persona consensus becomes independent of repeated-run count.
- Relationship consensus gains a defined semantic basis.
- Semantic grouping remains traceable, reversible, and subordinate to Human
  authority.
- The architecture can degrade safely toward non-merge instead of inventing
  equivalence.

### Negative / cost

- Processing gains an additional derived artifact and later a semantic comparison
  step.
- Semantic comparison can add latency and token cost when a model is used.
- The UI must later expose grouping evidence and support a Human split action.
- Stability of semantic grouping becomes an additional property that requires
  testing.

## Rejected alternatives

### Exact normalized name + element type as identity

Rejected because it fragments one engineering concept when Personas disagree on
classification and therefore hides useful variance.

### Exact normalized name only

Rejected because wording variation still creates duplicates and homonyms may be
incorrectly merged.

### Fuzzy string matching as merge authority

Rejected because lexical similarity is not sufficient engineering evidence for
semantic identity and may silently merge distinct concepts.

### Make the Agent output contract-perfect before Human Review

Rejected because semantic uncertainty is legitimate Human-in-the-Loop input.
Only hard authority and integrity corruption should block review construction.

### Run semantic consolidation when Human Review is opened

Rejected because review opening would incur new model cost, could produce
different grouping on repeated opens, and would make Human Review availability
depend on a live external call.
