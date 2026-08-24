# Canonical Engineering Subject Contract — R4c

Status: **Accepted architecture contract; implementation pending**

Date: 2026-08-23

Authority: ADR-028

---

## Purpose

Define the minimum pre-Persona identity contract required to ensure that all Personas interpret the same engineering subjects while preserving exact Source provenance and consolidating repeated mentions.

---

## Contract Layers

### 1. Source Span Reference

A deterministic locator into one registered Engineering Source projection.

Required semantic fields:

```text
project_id
source_id
source_projection_id
span_id
start_offset
end_offset
exact_excerpt
```

The exact persistent representation may reuse existing SAU/segment/evidence anchors where possible. No second competing Source authority shall be introduced.

### 2. Engineering Mention

One exact occurrence in the Source that refers to or expresses a potentially engineering-relevant subject.

Conceptual fields:

```text
mention_id                  MNT-000001
source_span_references      1..n exact span refs
mention_text                exact source-derived text
neutral_label               optional discovery label
content_fingerprint
```

`mention_text` is reconstructed from Source authority; it is not trusted from LLM free text.

### 3. Canonical Engineering Subject

One pre-Persona identity representing all resolved mentions of the same engineering subject.

Conceptual fields:

```text
canonical_subject_id        SUBJ-000001
canonical_label
mention_ids                 1..n
subject_form                entity | behavior | assertion | question | other
identity_status             resolved | uncertain
content_fingerprint
```

The following fields are explicitly **not** part of canonical identity:

```text
semantic_kind
SysML v2 representation
framework assignment
Persona identity
professional confidence
modeling recommendation
```

Those belong downstream.

### 4. Persona Subject Interpretation

One professional interpretation of one canonical subject.

Conceptual fields:

```text
canonical_subject_id
persona_id
semantic_kind
interpreted_statement
professional_rationale
confidence
uncertainties
missing_evidence
optional relationship semantics
content_fingerprint
```

Invariant:

```text
effective (persona_id, canonical_subject_id) is unique
```

### 5. Subject Consensus

Consensus compares only interpretations bound to the same `canonical_subject_id`.

Possible field-level comparisons include:

```text
semantic_kind
interpreted_statement
relationship semantics
uncertainty
missing evidence
```

The consensus process shall never infer that two subjects are identical merely because their Persona interpretations look similar.

---


Runtime contract note: optional discovery metadata from an earlier design draft that is not represented by the implemented immutable types has been removed. The persisted runtime structures and their fingerprints are the accepted contract; ambiguous identity is handled by fail-closed non-merging and Human Review rather than speculative metadata.

## Identity and Consolidation Rules

### Mention ownership and reuse

`EngineeringMention` identity belongs to one exact source occurrence, not to a
canonical engineering subject.

Therefore:

- one exact source occurrence is materialized as exactly one `MNT-*`;
- the same `MNT-*` may be referenced by more than one `SUBJ-*` when that source
  occurrence legitimately supports multiple independently reviewable
  engineering subjects;
- identical source ranges must not create duplicate Mention objects;
- overlapping but non-identical ranges remain distinct Mention objects;
- shared Mention reuse does not merge the referenced canonical subjects.

This makes the reference relation intentionally many-to-many while preserving
one deterministic provenance identity per exact source occurrence.


### Trivial deterministic normalization

May normalize only representation-level differences such as:

```text
case
surrounding whitespace
Unicode normalization
```

### Cross-mention equivalence

A grouping such as:

```text
"Remote Expert"
"the remote expert"
"the expert"
```

may form one subject when the source context supports common reference.

The grouping decision shall be persisted or reproducibly derived and shall retain all Mentions.

### Fail closed

Do not silently merge when:

```text
referent is ambiguous
mentions occur in conflicting scopes
the grouping would rely only on semantic_kind
the grouping lacks source-grounded support
```

### Repeated mention invariant

If N source mentions resolve to the same subject:

```text
N Mentions
→ 1 Canonical Subject
→ P Persona Interpretations
```

not:

```text
N Mentions
→ N × P Persona Interpretations
```

---


### Subject self-sufficiency

A canonical engineering Subject must be independently referable and
professionally interpretable as an engineering subject.

Discovery shall not create a separate `SUBJ-*` merely for an adjective,
adverb, auxiliary/modal fragment, relational fragment or other dependent
clause fragment whose engineering meaning is incomplete without another
source expression.

This rule is semantic and generic. It shall not be implemented through
domain-specific word lists.

A smaller source span may still be a valid independent Subject when it denotes
a separately reviewable engineering entity, information item, behavior,
condition, question or assertion. Source-range containment alone is therefore
not sufficient reason to reject or merge a Subject.

The shared Discovery agent performs a final self-sufficiency pass before
returning the canonical Subject proposals. Ambiguous cases remain explicit
rather than being silently merged.

## Context Window Rules

Persona interpretation input contains:

```text
1. canonical subject identity
2. all bound Mention references
3. sufficient surrounding Engineering Source context
4. reference guidance clearly separated from source
```

The context window may contain source sentences that are not direct Mention anchors, because context and positive Evidence are different concerns.

Only bound Source spans/Mentions establish positive engineering provenance.

---

## Human Review Requirement

The default Review card shall make the MBSE decision obvious.

Example:

```text
Subject: Remote Expert

Proposed engineering meaning:
Actor

Persona assessments:
- Literal / Source-faithfulness: Actor
- Systems Engineering: External Actor
- Skeptical: Actor

Source mentions:
- "The remote expert joins from a separate client application."
- "The remote expert shall be able to observe..."
- "the expert may also take temporary control..."

Decision:
Accept | Modify | Reject | Defer | Out of scope
```

A table containing only:

```text
unclassified
descriptive
explicit
```

does not satisfy the R4c Human Review acceptance criterion.
