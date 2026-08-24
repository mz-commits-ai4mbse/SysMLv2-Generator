# WP-12 Architecture Finding — Evidence Detection vs Persona Interpretation

Date: 2026-08-21

Status: **Accepted formative architecture finding**

Related decision:

```text
ADR-027 — Source-Grounded Evidence Detection and Persona Interpretation Architecture
```

## 1. Why this finding exists

WP-12 formative end-to-end testing demonstrated that the implementation can
technically progress from a registered Engineering Source to Human Review while
still producing engineering review content that is not practically usable.

The representative real single-source run was:

```text
Project 877791 / RUN-000001
3 personas × 1 run

93 element proposals
41 relationship proposals
134 raw proposals

D3: 70 elements + 39 relationships = 109 subjects
D4: 70 elements + 39 relationships = 109 subjects
Human Review: 110 items
```

The numbers are not a quality target. They exposed a responsibility-ordering
problem.

## 2. Previous architecture behavior

The active pre-review flow effectively allowed each persona to perform several
responsibilities at once:

```text
Source scope
   ↓
Persona-specific evidence selection
   ↓
Persona-specific interpretation/classification
   ↓
Persona-specific model candidate derivation
   ↓
Downstream semantic consolidation
   ↓
Human Review
```

Each persona could independently decide which source information was meaningful,
assign persona-local identities and then contribute model-oriented candidates.

As a result, persona outputs did not necessarily represent different
professional interpretations of the same evidence.

## 3. Root cause

The architecture mixed two distinct questions:

```text
DETECTION
"Which source passages contain potentially relevant engineering information?"

INTERPRETATION
"What does this already identified source-grounded information mean?"
```

Because detection happened inside the persona-specific path, the system had no
stable common evidence identity before persona branching.

Therefore:

```text
difference between persona outputs
```

could mean either:

```text
a) genuine professional interpretation variance
```

or:

```text
b) different evidence selection / segmentation / abstraction / naming
```

Those two cases were not distinguishable reliably downstream.

## 4. Consequences observed in the prototype

### 4.1 Persona-driven subject multiplication

Adding personas could create more engineering/model subjects rather than more
views on the same subject.

### 4.2 Unstable subject identity

Downstream logic had to infer common subjects from AI-generated candidate names,
types and semantic similarity instead of starting from one shared source-grounded
Evidence identity.

### 4.3 Ambiguous consensus and variance

A consensus mechanism is only meaningful if the compared agents are answering
the same underlying question about the same evidence. That precondition was not
guaranteed.

### 4.4 Excessive downstream repair

D3/D4 had to recover common subject structure after independent persona/model
candidate populations had already been created.

### 4.5 Premature model derivation

Architecture/model proposals were produced before Human Engineering Review had
approved the interpreted engineering information.

### 4.6 Human Review overload

The reviewer received model-oriented candidate populations rather than a small,
source-grounded engineering evidence space with transparent interpretation
variance.

### 4.7 Technical correctness without engineering effectiveness

The pipeline could satisfy technical contracts and reach `awaiting_review`
while the resulting engineering content remained unsuitable for meaningful
review.

## 5. Corrected responsibility sequence

The corrected architecture introduces a shared evidence boundary before persona
branching:

```text
Engineering Source
        ↓
Register Source
        ↓
Prepare Source
        ↓
Deterministic Source Projection
        ↓
Specialized Evidence Detection Agent
        ↓
Source-Grounded Evidence
        ↓
 ┌──────┼──────┐
 ▼      ▼      ▼
P1     P2     P3
Interpret the SAME Evidence
 └──────┼──────┘
        ↓
Consensus / Variance
        ↓
Human Engineering Review
        ↓
Approved Engineering Information
```

Every accepted Evidence object is source-grounded through at least:

```text
project_id
source_id
source_projection_id
source_anchor(s)
exact source_excerpt
```

Evidence identity is established before persona execution.

## 6. Role of the Evidence Detection Agent

The Evidence Detection Agent is a specialized, persona-independent LLM task.
Its job is to find potentially model-relevant engineering passages and return
exactly source-verifiable spans.

It may use repository examples and engineering/modeling guidance as reference
knowledge.

Reference knowledge answers:

```text
"What kinds of information should I look for?"
```

Only the registered Engineering Source answers:

```text
"What information exists in this Project?"
```

The detector does not create model elements and does not perform architecture
derivation.

## 7. Why personas remain important

The correction does not remove persona-based reasoning.

Before Human Engineering Review:

```text
Personas = different professional interpretations of the SAME Evidence
```

After approval, a second persona phase may be used for architecture/model
derivation:

```text
Approved Engineering Information
        ↓
Modeling Personas
        ↓
Architecture / Model Candidates
        ↓
Candidate Consolidation
        ↓
Model Candidate Review
```

Whether the downstream phase reuses existing personas or introduces
task-specific modeling personas remains intentionally open until that stage is
implemented and evaluated.

## 8. Thesis significance

The prototype produced a genuine architecture-level insight:

> Source grounding alone is insufficient for reliable multi-persona semantic
> processing when evidence detection and persona-specific interpretation share
> the same responsibility boundary. A common evidence identity must be
> established before persona variance can be interpreted as engineering
> variance.

This finding shall be documented in the thesis as:

```text
Observed Failure
→ Root Cause
→ Architectural Correction
→ Evaluation of the Corrected Path
```

The relevant success criteria for the corrected implementation are:

1. Source Purity
2. Exact Source Grounding
3. Model Relevance
4. Stable Evidence identity independent of persona/run count
5. Meaningful persona consensus/variance
6. Human Review usability
7. No pre-review model derivation on the corrected path

Review-item count remains a diagnostic only.
