# UX Wireframe Registry

## Purpose

Stable wireframe identifiers for implementation guidance, presentation material
and later thesis figures.

Wireframes are design evidence.

They are not authoritative engineering artifacts.

---

## Baseline

Functional prototype baseline:

```text
0fce9928a04e047e4b39484b421632fb64ed905f
```

Before the Guided Engineering Workflow replaces the current presentation, retain
representative screenshots of the functional baseline where possible.

Suggested baseline evidence:

```text
BASE-01  Project Dashboard
BASE-02  Agentic Ingestion
BASE-03  Human Review / proposal inspection
```

These screenshots document the pre-redesign interaction model.

---

## Wireframe registry

### WF-01 — Engineer Home / Your Work

Purpose:

Prioritize open engineering work and next action above technical workflow state.

Key content:

- decisions required,
- variance requiring attention,
- blocking issues,
- next action,
- compact workflow orientation.

Status:

```text
specified
```

---

### WF-02 — Ingested Engineering Content

Purpose:

Show what was actually ingested without exposing unnecessary technical metadata
in the default view.

Key content:

- human-readable source,
- extracted engineering content,
- content preview,
- optional traceability details.

Status:

```text
specified
```

---

### WF-03 — Unanimous Persona Results

Purpose:

Make strong agreement between independent Persona perspectives immediately
visible.

Key content:

- side-by-side proposals,
- Persona identity,
- matching result,
- explicit unanimous label,
- low variance,
- rationale on demand.

Status:

```text
specified
```

---

### WF-04 — Variant Persona Results

Purpose:

Expose disagreement without hiding individual proposals behind an aggregate.

Key content:

- side-by-side alternatives,
- majority distribution,
- dissenting Persona,
- variance state,
- Human decision.

Status:

```text
specified
```

---

### WF-05 — Human Decision

Purpose:

Provide one clear engineering decision surface.

Key content:

- engineering subject,
- alternatives,
- supporting rationale,
- select / modify action,
- explicit Human confirmation.

Status:

```text
specified
```

---

### WF-06 — Model Proposal Review

Purpose:

Apply the same interaction model to Model Candidate / architecture review.

Key content:

- structural model view,
- proposed elements,
- proposed relationships,
- alternatives,
- review state,
- required Human decisions.

Status:

```text
specified
```

---

### WF-07 — Final Model Review

Purpose:

Support final engineering inspection before release.

Key content:

- model / diagram,
- exact SysML,
- validation,
- traceability,
- change feedback,
- release readiness,
- explicit Human release decision.

Status:

```text
specified
```

---

## Figure lifecycle

Wireframes should progress through:

```text
specified
→ drafted
→ implemented
→ thesis-ready
```

When a visual wireframe is created, retain the stable `WF-xx` identifier even if
the drawing is revised.

This allows thesis text, ADRs and implementation notes to refer to the same design
concept throughout development.
