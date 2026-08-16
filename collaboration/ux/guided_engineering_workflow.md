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

The existing functional UI is not replaced wholesale. Existing Dashboard,
Processing and Human Review capabilities are retained where useful and are
progressively adapted to the shared engineer-centered interaction model.

---

## Presentation depth

The interface supports two presentation depths over the same authoritative state.

### Focused View

Default for daily engineering work.

Prioritizes:

- engineering content,
- Agent / Persona results,
- variance and consensus,
- Human decisions,
- accepted results,
- blocking engineering issues,
- next action.

### Technical View

Explicitly enabled by the engineer when deeper information is required.

May additionally expose:

- stable internal identities,
- processing Run / Attempt information,
- artifact references,
- fingerprints,
- provenance,
- lifecycle information,
- diagnostic findings,
- complete traceability.

The presentation-depth setting has no engineering authority.

```text
Focused ≠ reduced evidence
Focused = reduced visible complexity

Technical ≠ separate workflow
Technical = deeper presentation of the same workflow
```

---

## Global application context

Project selection and presentation depth belong to the application shell rather
than to an individual working surface.

The intended persistent header is:

```text
Project
[ Engineering Project ▼ ]                Technical details  [ toggle ]
+ Create new project
```

Project selection represents application context.

Project creation is a separate explicit action and is therefore presented next to
the selector rather than as a pseudo-option inside the Project list.

This header remains available while navigating between:

- Engineering Workspace,
- Project Dashboard,
- Processing,
- Human Review,
- Model Proposal,
- Final Model Review,
- Published Output.

The selected Project defines the current UI working context.

Changing Project clears stale entity-level navigation but does not modify any
persisted engineering authority.

The Focused / Technical toggle changes presentation depth only.

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

The stages do not imply that all work must occur on one screen.

Separate LLM-backed processing and review surfaces remain appropriate where they
reduce information density and make engineering comparison easier.

The Engineering Workspace answers:

```text
What requires my attention or decision now?
```

The Project Dashboard answers:

```text
Which engineering / model information is already available?
```

Individual Processing and Review views answer:

```text
What did this processing step derive and what must I decide here?
```

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
