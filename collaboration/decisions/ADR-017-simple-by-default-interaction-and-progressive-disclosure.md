# ADR-017 — Simple-by-Default Interaction and Progressive Disclosure

**Status:** Accepted
**Date:** 2026-08-12
**Decision scope:** System-wide user interaction architecture for the Turing Generator prototype

## Context

The Turing Generator intentionally preserves a rich internal architecture for
authority, evidence, traceability, immutable revision history, validation and
recovery.

Phase-G manual acceptance demonstrated that exposing this complete internal
detail simultaneously in the primary Streamlit workflow creates unnecessary
interaction cost.

The direct-prompt benchmark is relevant: a user can upload legacy engineering
content to a general LLM and quickly receive plausible SysML-like output.

The Turing Generator therefore creates value only when its additional
governance, reproducibility, traceability, Human Review authority and validation
are preserved **without requiring the user to operate the audit architecture as
the default interaction model**.

This decision does not reduce backend evidence, validation or authority.

## Decision

The system shall apply the following interaction principle:

```text
Simple by default.
Explainable on demand.
Fully traceable underneath.
```

The interaction architecture separates three presentation levels.

### Level 1 — Primary Task-oriented Workflow

Default views shall emphasize:

- engineering result
- material uncertainty or unresolved issue
- required human decision
- next action

The primary workflow shall not require the user to interpret internal IDs,
fingerprints, persistence paths or complete provenance graphs unless they are
material to the immediate task.

### Level 2 — Explanation on Demand

The user shall be able to inspect relevant explanation including:

- rationale
- alternative proposals
- relevant source evidence
- disagreement / consensus where useful
- confidence where useful
- validation reason
- material impact of a decision

Explanation is not authority by itself.

### Level 3 — Audit and Traceability

Complete technical evidence remains inspectable, including:

- Project / Source identity
- Processing Run / Attempt identity
- artifact references
- immutable revision lineage
- Human Review Decision binding
- fingerprints
- validation evidence
- Approved Input authority state
- provenance and lifecycle events

This information remains persisted according to the owning contracts even when
it is not shown by default.

## System-wide Scope

The principle applies to:

- Source registration and Agentic Ingestion
- semantic processing
- Human Review
- Approved Input promotion
- Architecture / Model Candidate interaction
- Internal Engineering Model generation
- validation
- SysML v2 generation and result presentation

## Interaction Boundary

Task-oriented interaction and audit-oriented inspection are separate concerns.

A user shall not need to navigate audit-oriented information merely to continue
a normal engineering workflow.

Human interaction should be exception-driven where possible.

Examples:

```text
normal:
result + next action

uncertain:
result + material uncertainty + required decision

audit:
explicitly opened evidence / provenance / fingerprint detail
```

## Human Review UX Consequences

The current Human Review implementation remains valid as a Phase-G authority
implementation.

A later guided-workflow pass should:

- place competing proposals side by side where useful
- make the selected engineering statement and required decision primary
- collapse detailed evidence by default
- expose actionable relationship-validation reasons
- provide clear write-action lifecycle feedback
- keep complete traceability available on demand

No Phase-G authority contract is weakened to achieve this.

## Agentic Ingestion UX Consequences

The default ingestion result should prefer:

- what was processed
- whether the run succeeded
- material findings / uncertainty
- whether Human Review is required
- the next action

Technical Run / Attempt / artifact detail remains available but need not dominate
the default view.

## Architecture / Model Proposal UX Consequences

Phase H and later proposal workflows should default to:

- proposed engineering content
- relationships and structural implications
- material alternatives
- why the proposal matters
- required human decision

Complete provenance remains expandable.

## SysML v2 Result UX Consequences

The final workflow should present:

- model result
- validation status
- publication status
- concise generation summary

Textual notation, full validation detail, fingerprints and traceability remain
available on demand.

## Technology Decision for the Demo

Streamlit remains the prototype UI technology through the 2026-08-18 product
demo.

The following are explicitly not part of the demo critical path:

- React rewrite
- Vue rewrite
- separate FastAPI backend migration solely for UI restructuring

The current application may continue to call Python application services
directly.

A future frontend/backend separation remains possible without changing the
domain/service architecture.

## Consequences

Positive:

- lower interaction burden
- clearer engineering decisions
- stronger contrast to direct ungoverned prompt-based generation
- auditability remains intact
- backend architecture remains reusable
- UX can evolve independently from authority contracts

Trade-offs:

- the prototype must maintain both concise default views and deeper inspection
- progressive disclosure requires deliberate information hierarchy
- some existing Streamlit pages remain information-dense until the later UX pass

## Non-goals

This ADR does not:

- remove persisted evidence
- remove fingerprints
- remove immutable history
- weaken Human Review
- make confidence or consensus authoritative
- replace CATIA authority
- redefine Phase-H Model Candidate architecture
- mandate a production frontend framework

## Presentation Implication

The architecture should be communicated as:

```text
simple interaction surface
over
explicit governed engineering services
over
complete persisted evidence and traceability
```

This supports the literature-derived Data / Process / Knowledge framing while
keeping Knowledge and governance cross-cutting rather than forcing them into a
single UI or deployment component.
