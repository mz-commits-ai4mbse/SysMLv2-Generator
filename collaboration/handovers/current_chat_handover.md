# Current Chat Handover

## Purpose

This document is the authoritative starting point for the next implementation
chat after Phase-G completion.

Use it together with the committed repository, the remaining Collaboration
Knowledge Base and the authoritative CATIA SysML v2 model.

---

# Project

Project

Turing Generator

Repository

`mz-commits-ai4mbse/SysMLv2-Generator`

Branch

`main`

Verified Implementation Reference

`b598bf04770b08738bbce5c15f2f7dfb671aab01` — Phase G completion

Last Prior Committed Checkpoint

`7209f17a610d3adb359e8b672a28020b71c03333` — G6 completion

Architecture Version

1.4

Knowledge Base Version

1.11

Implementation Version

0.13

Roadmap Version

1.11

Last SSOT Update

2026-08-12

Current Phase

Phase H — Model Candidate Layer

Current Status

Phase G completed and verified. Phase H architecture contract is next.

Verified Automated Test Baseline

```text
G7.4 focused completion regression:
65 passed in 8.95s

Complete repository regression:
4818 passed in 24.50s

git diff --check:
PASS
```

Phase-G Manual Acceptance

PASS

Closed Vertical-slice Target

2026-08-14

Functional Freeze

2026-08-17

Product Demo

2026-08-18

---

# Read Before Starting

Read in this order:

1. `collaboration/current_state.md`
2. `collaboration/roadmap.md`
3. `collaboration/working_rules.md`
4. `collaboration/model_registry.json`
5. `collaboration/decisions/ADR-016-human-review-workspace-and-approved-input-promotion-architecture.md`
6. `collaboration/decisions/ADR-017-simple-by-default-interaction-and-progressive-disclosure.md`
7. `collaboration/audits/phase_g_manual_acceptance_test_report.md`
8. `collaboration/audits/phase_g_manual_acceptance_findings.md`
9. `collaboration/change_log.md`
10. this handover

Then inspect the committed implementation only as required for the Phase-H
architecture discussion.

---

# Source Authority

Authority order:

1. CATIA SysML v2 model for engineering knowledge
2. committed repository for implementation reality
3. Collaboration Knowledge Base for coordination and accepted decisions
4. chat history and temporary generated artifacts

The temporary SYSIDE shadow model may supplement missing CATIA information
until Phase N.

It shall never override or contradict CATIA.

Implementation observations may become Model Element Change Candidates only.
They do not silently create normative engineering knowledge.

---

# Repository Collaboration Workflow

GitHub remains passive for the AI assistant.

The AI assistant shall not:

- directly edit GitHub content
- commit or push
- stage the local working tree
- use broad staging commands
- destructively clean unrelated files

Required workflow:

1. inspect passively
2. name exact repository-relative paths
3. provide deterministic local edits
4. Moritz applies changes locally
5. run focused tests
6. run complete regression only at a major package completion
7. inspect `git diff --check`
8. stage exact intended paths only
9. Moritz commits and pushes
10. verify `HEAD == origin/main`

Never use:

```text
git add .
git add -A
```

---

# Current Working-tree Caution

The local tree may contain unrelated/generated files including:

- `.DS_Store`
- `__pycache__`
- ingestion reports
- test Projects
- team-run artifacts
- local ZIP / patch files

Do not stage them unless explicitly part of the intended change.

---

# Phase G — Completed Baseline

Phase G is complete.

Authority chain:

```text
Original Source
→ Processing Evidence
→ Human Review Workspace
→ Finalized Reviewed Document
→ Approved Input
```

G5 checkpoint:

`865cbab24dfb5bb1f5150ff9336a55d00299a035`

G6 checkpoint:

`7209f17a610d3adb359e8b672a28020b71c03333`

Completed:

- G1 architecture
- G2 Review Workspace foundations
- G3 evidence adapters / Review Item construction
- G4 finalization / finalized artifacts / reopening
- G5 Approved Input promotion and lifecycle
- G6 Human Review and promotion UI
- G7 integration, audit, manual acceptance and regression

G7.3 manual acceptance result:

```text
PASS
```

G7.4 final verification:

```text
65 focused tests passed
4818 complete repository tests passed
git diff --check passed
```

Phase G does not create Model Candidates or SysML v2.

---

# Phase-G Manual Acceptance Highlights

Verified:

- immutable Review Revision chain
- exact detailed Human Review confirmation
- exact finalization binding
- exact three-artifact finalized set
- promotion eligibility filtering
- AIN promotion and exact authority traceability
- reopen successor version and fresh Review Item lineage
- byte-identical finalized predecessor after reopen
- Scoped Action + Impact Preview
- fail-closed unresolved relationships
- safe Agentic Ingestion retry/recovery
- no second Run/Retry write action while `running`

Closed findings:

```text
F01 Streamlit Session State runtime rule
F02 failed-Run retry integration
F03 running-state UI write-action guard
F04 provider-neutral failure diagnosis
F05 Attempt identity reuse
F06 semantic-reference contract mismatch
```

---

# Accepted Interaction Architecture

ADR:

`collaboration/decisions/ADR-017-simple-by-default-interaction-and-progressive-disclosure.md`

Principle:

```text
Simple by default.
Explainable on demand.
Fully traceable underneath.
```

Apply this to every agentic step.

Presentation levels:

1. primary workflow
   - engineering result
   - material uncertainty
   - required decision
   - next action
2. explanation
   - rationale
   - alternative proposals
   - relevant source evidence
   - confidence / disagreement where useful
3. audit / traceability
   - Run / Attempt IDs
   - fingerprints
   - provenance
   - revisions
   - validation evidence

Task-oriented interaction and audit-oriented inspection are separate concerns.

Backend evidence remains complete and immutable even when the default UI hides
technical detail.

Streamlit remains the prototype UI technology through the demo.

Do not start a React, Vue or FastAPI rewrite before the demo.

---

# Exact Next Work Package

## WP-04 / Phase H — Model Candidate Layer

Phase H is next.

The stable upstream authority boundary is:

```python
ApprovedInputRepository.list_active_approved_inputs(
    project_id,
) -> tuple[ApprovedInputManifest, ...]
```

Phase H must not derive authority from:

- Draft Review state
- original Review Reports
- Agent confidence
- Consensus
- inactive Approved Inputs
- UI state

Required Phase-H architecture discussion shall cover at least:

- Model Candidate identity and immutable manifest boundaries
- element candidates versus relationship candidates
- source / target identity semantics
- relationship type and semantic intent
- relationship priority
- prioritization rationale
- structural-comparability impact
- profile conformance
- Human Review status
- exact Approved Input provenance
- lifecycle / supersession expectations
- repository and read contracts
- boundary to Phase I

No Phase-H implementation begins before the exact architecture contract has
been reviewed and explicitly accepted.

---

# Remaining Demo Roadmap

```text
WP-04  Phase H — Model Candidate Layer
WP-05  Phase I — Model Generation Agent / Internal Engineering Model
WP-06  Phase J — SysML v2 Code Generator
WP-07  Phase K — Validation Layer
WP-08  Phase L — Output Writer
WP-09  Guided Workflow UI
WP-10  Ingestion + Human Review UX Simplification
WP-11  Architecture / Model Proposal UX
WP-12  End-to-End Demo Hardening
WP-13  Demo Freeze + Rehearsal
WP-14  CATIA / SSOT Checkpoint
```

Schedule:

```text
2026-08-14  H–L closed vertical slice
2026-08-15  Guided Workflow UI
2026-08-16  Demo hardening
2026-08-17  Functional freeze
2026-08-18  Product demo
```

Quality is non-negotiable. Save time through decomposition and targeted testing,
not through weaker contracts.

---

# Presentation Position

The Zwischenstandspräsentation is prepared after implementation and no longer
blocks Phase H.

Preserve this presentation logic:

```text
literature:
Data Layer
Process Layer
Knowledge Layer

implementation:
8 Logical Components operationalize those responsibilities
```

Knowledge is cross-cutting governance.

Use one high-level activity view with approximately 7±2 primary activities.

Outlook:

Versioned replaceable `.md` / `.json` artifacts, recipes, profiles, context,
framework and semantic definitions allow controlled architectural adaptability
around a stable processing architecture.

---

# Mandatory Engineering Boundaries

- CATIA remains engineering authority.
- The committed repository remains implementation authority.
- Human Review authority cannot be replaced by confidence or consensus.
- Original Processing evidence remains immutable.
- Finalized Review evidence remains exact and mutually bound.
- Only active Approved Inputs cross into Phase H.
- Phase H creates non-authoritative Model Candidates.
- SysML v2 generation belongs to Phase J, not Phase H.
- Failed required validation blocks publication.
- Progressive disclosure may hide complexity but may not remove traceability.
- No frontend technology rewrite before the product demo.

---

# Immediate Starting Instruction for the Next Chat

Begin with the Phase-H architecture contract.

Do not implement yet.

First:

1. inspect the active Approved Input contract and relevant Phase-H planned
   requirements
2. surface the exact Model Candidate architecture questions
3. propose a clean, modular target architecture
4. define affected repository paths
5. obtain explicit acceptance

Only after acceptance begin WP-04 implementation.
