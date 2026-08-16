# Guided Engineering Workflow — UX Design Record

## Status

Accepted design direction.

## Related decision

```text
ADR-024 — Guided Engineering Workflow and UX Projection Architecture
```

## Functional baseline

```text
0fce9928a04e047e4b39484b421632fb64ed905f
```

---

## Design objective

The Turing Generator UI shall help an engineer answer four questions quickly:

```text
1. What engineering information do I have?
2. What did the system propose?
3. Where do the independent perspectives differ?
4. What do I need to decide?
```

Everything else is secondary presentation information.

---

## Information hierarchy

### Level 1 — Engineering task

Visible by default.

Examples:

- Source document / engineering statement
- proposed Requirement
- proposed Function
- proposed relationship
- model element
- validation problem
- required Human decision

### Level 2 — Alternative interpretation

Visible whenever relevant.

Examples:

- Persona A proposal
- Persona B proposal
- Persona C proposal
- consensus distribution
- variance classification

### Level 3 — Explanation

Visible on demand.

Examples:

- rationale
- confidence
- supporting evidence
- missing evidence
- Agent explanation

### Level 4 — Audit / traceability

Available but collapsed by default.

Examples:

- internal IDs
- fingerprints
- artifact references
- source anchors
- processing-run identity
- immutable decision identity

---

## Shared result-comparison pattern

```text
┌─────────────────────────────────────────────────────────────┐
│ Engineering subject                         CONSENSUS STATE │
│ Human-readable source / context              variance       │
├──────────────────┬──────────────────┬───────────────────────┤
│ Persona A        │ Persona B        │ Persona C             │
│                  │                  │                       │
│ Proposal         │ Proposal         │ Proposal              │
│                  │                  │                       │
│ Confidence       │ Confidence       │ Confidence            │
│ Why? ▾           │ Why? ▾           │ Why? ▾                │
├──────────────────┴──────────────────┴───────────────────────┤
│ Distribution / disagreement summary                        │
│                                                             │
│ Human decision                                              │
│ [ Alternative A ] [ Alternative B ] [ Modify ]             │
└─────────────────────────────────────────────────────────────┘
```

---

## Shared unanimous pattern

```text
● Unanimous · all independent Personas agree
Variance: low
```

The UI may use green visual emphasis.

The result still follows the applicable Human Review contract.

Consensus is not approval.

---

## Shared disagreement pattern

```text
● Majority · 2 / 3 Personas agree
Variance: medium

Systems Engineer       → Requirement
Critical Reviewer      → Requirement
Completeness Reviewer  → Constraint

Human decision required
```

The complete individual proposals remain visible.

---

## Engineer home

Primary section:

```text
Your work
```

Preferred information:

```text
decisions required
results with relevant variance
blocking findings
next engineering action
```

Secondary section:

```text
Engineering flow
```

This provides orientation but shall not dominate the page.

---

## Guided workflow

```text
Project & Sources
        ↓
Processing
        ↓
Human Review & Approved Input
        ↓
Model Proposal & Candidate Review
        ↓
Final Model Review
        ↓
Published Output
```

The stages are UI projections only.

---

## Responsive behavior

Side-by-side comparison is preferred on sufficiently wide screens.

Where available width is insufficient, proposals may stack vertically while
preserving:

- identical ordering,
- Persona identity,
- proposal boundaries,
- consensus summary,
- Human decision visibility.

Information must not disappear merely because layout changes.

---

## Accessibility

Consensus state shall never rely on color alone.

Every state has:

```text
color
+
label
+
short explanation
```

Example:

```text
GREEN
Unanimous · 3 / 3 Personas agree
```

---

## Thesis use

This design record is intended to support later thesis reconstruction of:

```text
finding
→ design principle
→ wireframe
→ implementation
```

Wireframe identities are maintained in:

```text
collaboration/ux/wireframes/README.md
```
