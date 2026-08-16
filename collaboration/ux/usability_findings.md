# Formative Usability Findings

## Purpose

This document records formative usability findings obtained after completion of
the functionally complete Turing Generator prototype.

It intentionally separates:

```text
functional capability
from
usability of that capability
```

No quantitative usability-study claims shall be inferred from this document unless
separate evaluation evidence supports them.

---

## Functional baseline

Baseline commit:

```text
0fce9928a04e047e4b39484b421632fb64ed905f
```

Baseline state:

```text
Phase L implementation complete
end-to-end technical workflow implemented
Human authority preserved
validation and publication gates implemented
traceability implemented
```

The subsequent UX work therefore represents a redesign of the interaction model,
not completion of previously missing backend functionality.

---

## Formative evaluation framing

Evaluation type:

```text
formative usability evaluation
```

Purpose:

```text
identify interaction and information-presentation problems
before final demonstrator preparation
```

Do not retrospectively invent:

- participant counts,
- participant demographics,
- completion times,
- quantitative scales,
- statistical results.

Where such evidence exists separately, it may later be referenced explicitly.

---

## UX-F-001 — Technical metadata dominates the working surface

### Observation

The prototype exposes substantial technical workflow and traceability information
directly in primary views.

Although useful for auditability, this information competes visually with the
engineering content required for the actual task.

### Engineering impact

The engineer has to distinguish important engineering content from implementation
metadata before acting.

### Design response

```text
Engineering Content before Metadata
```

Primary views show the engineering subject and decision.

IDs, fingerprints, artifact references and detailed provenance are exposed through
progressive disclosure.

---

## UX-F-002 — Required Human decisions are not sufficiently prominent

### Observation

The implemented workflow contains explicit Human authority gates, but the current
UI does not consistently make open decisions the dominant interaction object.

### Engineering impact

Users can determine system state without immediately knowing:

```text
What exactly do I need to decide now?
```

### Design response

```text
Decision-Centered Interaction
```

The Guided Workflow prioritizes:

- open decisions,
- relevant alternatives,
- rationale,
- next Human action.

---

## UX-F-003 — Redundant Agent results are difficult to compare

### Observation

Multiple Agent / Persona executions provide useful diversity and robustness, but
their results are distributed across technical evidence and review structures.

Sequential inspection creates unnecessary cognitive effort.

### Engineering impact

Differences between independent interpretations are harder to identify than
necessary.

### Design response

```text
Side-by-Side before Aggregation
```

Equivalent Agent / Persona proposals are displayed beside each other whenever
screen space permits.

The Human can compare all alternatives before selecting or modifying a result.

---

## UX-F-004 — Consensus and variance need immediate visual meaning

### Observation

The backend already provides structured consensus and variance information, but
the user interface does not yet make this information sufficiently visible.

### Engineering impact

The engineer cannot immediately distinguish:

- unanimous interpretation,
- majority interpretation,
- meaningful disagreement,
- incomplete evidence.

### Design response

Use a shared visual language:

```text
GREEN   unanimous / low variance
AMBER   majority / medium variance
RED     high variance / no consensus / action required
NEUTRAL incomplete / unavailable
```

Every state also contains a textual label.

Color never represents Human approval.

---

## UX-F-005 — The UI mirrors processing structure more than engineering workflow

### Observation

The functional prototype grew together with implementation phases and therefore
exposes parts of the technical processing structure directly.

### Engineering impact

Users have to understand the implementation sequence in order to navigate the
engineering task efficiently.

### Design response

Introduce a non-authoritative Guided Engineering Workflow:

```text
Project & Sources
→ Processing
→ Human Review & Approved Input
→ Model Proposal & Candidate Review
→ Final Model Review
→ Published Output
```

The guided workflow is derived from existing authoritative state.

---

## UX-F-006 — Detailed explanation is important but should not dominate

### Observation

Rationale, evidence, traceability and technical details are essential for
engineering confidence and auditability.

Showing all details simultaneously reduces overview.

### Design response

Apply progressive disclosure:

```text
simple by default
→ explanation on demand
→ complete traceability underneath
```

---

## Summary

The formative findings do not indicate a need to replace the technical
architecture.

Instead they motivate a change in information hierarchy and interaction design:

```text
system-centric presentation
→ engineer-centric presentation
```

while retaining:

```text
same authoritative backend
same Human authority
same validation gates
same immutable evidence
same traceability
```
