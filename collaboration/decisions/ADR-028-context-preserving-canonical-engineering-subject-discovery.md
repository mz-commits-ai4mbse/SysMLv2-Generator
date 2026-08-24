# ADR-028 — Context-Preserving Canonical Engineering Subject Discovery

Status

**Accepted — architecture direction approved on 2026-08-23; implementation and live validation pending.**

Date

2026-08-23

---

## Context

WP-12 recovery under ADR-027 successfully restored a shared, source-grounded Evidence population before Persona interpretation. The corrected live path demonstrated:

- deterministic Source grounding,
- stable `EVD-*` identity,
- all Personas operating on the same Evidence population,
- no multiplication of Review Subjects by Persona count,
- successful propagation into Human Review.

However, formative Human Review testing exposed a second semantic defect.

The active interpretation contract effectively maps one `SourceEvidence` object to one interpreted statement and one information type. A single Evidence block can contain multiple distinct engineering subjects and assertions. The result is therefore often a paraphrase of the Evidence block rather than an MBSE-relevant decomposition.

Example:

```text
The remote expert shall be able to observe the live microscope image.
During the session, the expert may also take temporary control of the microscope
when the operator permits it.
The operator remains responsible for the local session and must be able to
understand who currently controls the microscope.
```

This source passage contains several independently meaningful engineering subjects, for example:

```text
Remote Expert
Live Microscope Image Observation
Temporary Microscope Control
Operator Permission
Operator Responsibility
Current Controller Awareness
```

Treating the whole passage as one semantic subject loses this structure.

A second issue is context starvation. Provenance units were made deliberately small to guarantee exact source grounding. Those small units are useful for identity and traceability, but they are not necessarily the correct context window for LLM interpretation.

The architecture therefore needs to distinguish:

```text
small deterministic provenance units
from
larger context-preserving interpretation windows
```

A third issue is repeated mention. The same engineering subject can occur several times in one source. Repeated mentions shall not be interpreted independently by every Persona.

---

## Relationship to ADR-027

ADR-028 refines ADR-027; it does not reverse it.

ADR-027 remains authoritative that:

1. source-grounded identity is established before Persona variance,
2. Personas shall not independently create incomparable subject populations,
3. Reference Knowledge is guidance only,
4. Human Review precedes model derivation,
5. Persona/run counts shall not multiply engineering subjects.

ADR-028 adds one missing level between SourceEvidence and Persona interpretation:

```text
SourceEvidence / Source Spans
→ Mention Discovery
→ Canonical Engineering Subjects
→ Shared Persona Interpretation
```

ADR-027's phrase "Personas interpret the same Evidence" is therefore refined to:

> Personas interpret the same canonical engineering subjects, with all of those subjects bound to exact source-grounded Evidence and adequate surrounding source context.

---

## Decision

### 1. Provenance Unit and Interpretation Context Are Separate Concepts

The system shall not assume that the smallest deterministic source unit is also the best LLM interpretation context.

```text
Provenance unit
→ small, exact, deterministic, source-bound

Interpretation context
→ larger, readable, context-preserving, still source-only
```

For a small source document, the interpretation context may be the complete Engineering Source. For larger documents it may be a section or bounded multi-paragraph window.

Every discovered Mention and Canonical Subject shall still bind to exact deterministic source spans.

### 2. One SourceEvidence Does Not Equal One Engineering Subject

The following cardinalities are valid:

```text
1 SourceEvidence → 0..n Mentions
1 SourceEvidence → 0..n Canonical Engineering Subjects
1 Canonical Engineering Subject → 1..n Mentions
1 Canonical Engineering Subject → 1..n SourceEvidence references
```

SourceEvidence establishes that source content is engineering-relevant and provides provenance.

It is not the semantic subject identity.

### 3. Mention Discovery Precedes Professional Interpretation

A shared discovery stage shall identify source mentions of potentially MBSE-relevant engineering subjects without assigning the final professional interpretation.

Examples include mentions of:

- people or roles,
- systems or applications,
- capabilities,
- functions or behaviors,
- information or data,
- states,
- constraints,
- requirements,
- interfaces,
- relationships,
- unresolved engineering questions.

The discovery stage may propose a neutral canonical label but shall not make the final SysML v2 representation decision.

### 4. Repeated Mentions Shall Be Consolidated Before Persona Interpretation

Multiple mentions of the same engineering subject shall resolve to one Canonical Subject whenever equivalence is sufficiently established.

Example:

```text
"The remote expert"
"the expert"
"remote expert"

→ one Canonical Subject:
SUBJ-000003 Remote Expert
```

The Canonical Subject retains all supporting Mention references.

Personas shall interpret `SUBJ-000003` once each, not once per Mention.

### 5. Ambiguous Identity Shall Not Be Silently Merged

If two mentions may refer to the same subject but equivalence is uncertain, the system shall preserve that uncertainty.

Allowed:

```text
SUBJ-000010
SUBJ-000011
possible_equivalence = uncertain
```

Not allowed:

```text
silent merge based only on lexical similarity
```

Deterministic normalization may merge trivial representation variants such as case and surrounding whitespace, but semantic/coreference consolidation beyond trivial equivalence is explicit and traceable.

### 6. Canonical Subject Identity Is Established Before Persona Variance

Canonical Subject identity shall not contain the Persona's semantic classification.

For example:

```text
SUBJ-000003
canonical_label: Remote Expert
mentions: MNT-000004, MNT-000009, MNT-000014
```

Personas then independently assess the same Subject:

```text
P1 → Actor
P2 → External Actor
P3 → Actor
```

`Actor` vs `External Actor` is interpretation variance, not Subject identity variance.

### 7. Personas Receive the Same Subject Population and Adequate Context

Each configured Persona shall receive:

```text
same Canonical Subject IDs
same Mention bindings
same source-only interpretation context
same Source authority
```

Persona prompts shall ask for professional interpretation/classification of the supplied subjects.

They shall not independently rediscover the subject population.

### 8. One Persona Produces At Most One Effective Interpretation per Canonical Subject

For one effective run:

```text
(Persona ID, Canonical Subject ID) → at most one effective interpretation
```

Repeated runs remain stability evidence and shall not multiply professional votes.

### 9. Interpretation Shall Be MBSE-Relevant but Pre-Model

Persona interpretation may classify engineering meaning such as:

```text
actor
stakeholder
system
external_system
capability
function
behavior
requirement
constraint
information
interface
state
relationship
open_question
other_engineering_subject
```

The exact controlled vocabulary is an implementation contract and may evolve.

This stage shall not prematurely decide the final SysML v2 model representation where multiple valid representations remain possible.

For example:

```text
engineering meaning: Actor
```

is permitted, while an unnecessary early decision about the exact later SysML containment/package structure is not.

### 10. Assertion/Relationship Meaning May Be Separate from Entity Subjects

The system shall support engineering semantics that are not simple noun-like entities.

Example source:

```text
The expert may take temporary control when the operator permits it.
```

Possible canonical subjects include:

```text
Remote Expert
Temporary Microscope Control
Operator Permission
```

and an assertion/relationship may express:

```text
Temporary Microscope Control
is constrained by
Operator Permission
```

The implementation may represent entity-like subjects and assertion-like subjects with one shared base contract or explicit subtypes, provided identity and provenance remain deterministic.

### 11. Human Review Operates on Canonical Engineering Subjects

Human Review shall present professionally meaningful subjects, not raw Evidence blocks.

Target presentation:

```text
Remote Expert
Proposed engineering meaning: Actor

P1: Actor
P2: External Actor
P3: Actor

Source mentions:
- SENT-002: "The remote expert ..."
- SENT-007: "... the expert ..."
```

The Human may accept, modify, reject, defer, mark out of scope, split, merge or resolve uncertainty according to the Review contract.

### 12. Model Derivation Remains Downstream

The corrected sequence is:

```text
Engineering Source
→ Deterministic Source Projection / Source Spans
→ Source-Grounded Evidence Detection
→ Context-Preserving Mention Discovery
→ Cross-Mention Canonical Subject Consolidation
→ Shared Persona Interpretation
→ Field-Level Consensus / Variance
→ Human Engineering Review
→ Approved Engineering Information
→ Architecture / Model Derivation
→ SysML v2
```

No Canonical Subject becomes Approved Engineering Information without Human Review.

---

## Canonical Identity Principle

The architecture shall preserve the following invariant:

> Mentions are many; canonical engineering subjects are unique within the resolved source scope; professional interpretations are many per subject only because Personas may legitimately disagree.

Formally:

```text
Source Span
    ↓
Mention
    ↓
Canonical Engineering Subject
    ↓
Persona Interpretation
    ↓
Consensus / Variance
    ↓
Human Review
```

Identity shall be established before variance.

---

## Source Context Principle

A key lesson from WP-12 is:

> Small units are required for exact provenance; larger context is often required for correct interpretation.

The architecture shall therefore never reduce LLM context merely to mirror persistence granularity.

Source context supplied to the LLM shall remain bounded to registered Engineering Source content plus clearly separated reference guidance. Reference guidance shall never become positive engineering evidence.

---

## Expected Effect on the WP-12 Example

A context-preserving discovery of the Remote Microscope Collaboration source is expected to identify a small canonical population resembling, without prescribing as a gold standard:

```text
Remote Microscope Collaboration
Microscope Operator
Remote Expert
Microscope Workstation
Client Application
Live Microscope View Sharing
Remote Consultation
Live Image Observation
Temporary Microscope Control
Operator Permission
Operator Responsibility
Current Controller Awareness
Session Information Retention
Retention Period
Connection Quality Limits
Remotely Controllable Microscope Functions
```

The exact result remains LLM-generated and subject to Human Review.

Repeated appearances of e.g. `Remote Expert` shall contribute additional provenance Mentions to one Canonical Subject rather than create duplicate subjects.

---

## Rejected Alternatives

### A. Continue One-Evidence-to-One-Interpretation

Rejected because one Evidence block can contain multiple independent engineering subjects and assertions.

### B. Let Every Persona Rediscover Subjects Independently

Rejected because it recreates the original subject-population mismatch and makes downstream consensus compare non-equivalent populations.

### C. Match Independent Persona Outputs Only Afterward

Rejected as the primary architecture because late semantic matching recreates the exact reconciliation problem ADR-027 was introduced to avoid.

### D. Use Sentence Identity as Engineering Subject Identity

Rejected because one sentence may contain multiple engineering subjects and one engineering subject may appear across multiple sentences.

### E. Interpret Every Mention Independently

Rejected because repeated mentions of the same engineering subject would multiply work and votes without adding engineering value.

---

## Implementation Slices

### R4c.1 — Contract and deterministic identity

Introduce immutable contracts for:

```text
SourceSpanReference
EngineeringMention
CanonicalEngineeringSubject
CanonicalSubjectSet
```

including fingerprints and fail-closed validation.

### R4c.2 — Context-preserving Subject Discovery

Use a dedicated LLM task over a source-only context window to discover `0..n` Mentions and propose cross-mention subject groupings.

The system, not the LLM, binds returned span IDs to exact source text.

### R4c.3 — Canonical consolidation

Resolve trivial deterministic equivalence directly and validate LLM-proposed cross-mention grouping.

Unknown spans, impossible mention ranges, duplicate identities, unsupported merges and ungrounded subjects fail closed.

### R4c.4 — Shared Persona Interpretation

All Personas interpret the same Canonical Subject Set and return one professional interpretation per subject.

### R4c.5 — Subject-centered Consensus and Human Review

Consensus compares fields for the same `SUBJ-*`. Human Review is generated from those subjects and their Persona interpretations.

### R4c.6 — Live validation and documentation closeout

Validate on the WP-12 source, run focused/full regression, update recovery findings and SSOT, and only then stage/commit.

---

## Acceptance Criteria

R4c is successful only if the real single-source test demonstrates all of the following:

1. source context remains readable to the LLM,
2. every Canonical Subject is grounded in exact source spans,
3. one passage may yield multiple MBSE-relevant subjects,
4. repeated mentions of one subject are consolidated,
5. Personas interpret the same Subject population,
6. adding Personas does not add Subject identities,
7. Human Review displays meaningful engineering semantics,
8. no positive engineering subject is derived from instructions/reference knowledge,
9. no premature SysML v2 model structure is treated as approved fact,
10. the resulting Review is usable by a Systems Engineer.

---

## Thesis-Relevant Finding

The WP-12 recovery produced a second architectural finding:

> Provenance granularity and interpretation granularity are different concerns. Exact traceability benefits from small deterministic source units, while semantic understanding benefits from larger context windows. A robust AI4MBSE pipeline should therefore establish canonical engineering-subject identity from source-bound mentions before professional interpretation, while supplying sufficient surrounding source context to the interpreting model.

This finding complements ADR-027's earlier conclusion that source evidence detection and professional interpretation must be separated.
