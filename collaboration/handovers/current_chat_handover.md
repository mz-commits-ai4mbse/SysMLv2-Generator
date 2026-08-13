# Current Chat Handover

## Purpose

This document is the authoritative starting point for the next implementation
chat after Phase-H completion.

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

`commit containing this SSOT update` — Phase H completion

Last Prior Committed Checkpoint

`884d658726d9a5a2ac9f86786ded30db7fe38c68` — ADR-018 accepted Phase-H architecture

Architecture Version

1.5

Knowledge Base Version

1.12

Implementation Version

0.14

Roadmap Version

1.12

Last SSOT Update

2026-08-13

Current Phase

Phase I — Model Generation Agent / Internal Engineering Model

Current Status

Phase H completed and verified. Phase I architecture contract is next.

Verified Automated Test Baseline

```text
Phase-H focused H1–H8 regression:
168 passed in 1.63s

Complete repository regression:
4986 passed in 25.80s

git diff --check:
PASS
```

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
7. `collaboration/decisions/ADR-018-model-candidate-layer-and-structural-comparability.md`
8. `collaboration/change_log.md`
9. this handover

Then inspect the committed Phase-H implementation only as required for the
Phase-I architecture discussion.

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

# Working-tree Caution

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

Phase G remains complete.

Authority chain:

```text
Original Source
→ Processing Evidence
→ Human Review Workspace
→ Finalized Reviewed Document
→ Approved Input
```

Phase-G completion:

`b598bf04770b08738bbce5c15f2f7dfb671aab01`

Phase-G verification:

```text
G7.3 manual acceptance:
PASS

G7.4 focused completion regression:
65 passed in 8.95s

Complete Phase-G repository regression:
4818 passed in 24.50s

git diff --check:
PASS
```

---

# Phase H — Completed Baseline

Architecture decision:

`collaboration/decisions/ADR-018-model-candidate-layer-and-structural-comparability.md`

Accepted architecture checkpoint:

`884d658726d9a5a2ac9f86786ded30db7fe38c68`

Completed implementation decomposition:

```text
H1  Identifiers / Errors
H2  Immutable Domain Types
H3  Manifests / Validation / Fingerprints
H4  Repository / Paths / Persistence
H5  Approved Input → Candidate Pipeline
H6  Profile / Relationship Logic
H7  Human Review / Phase-I Gate
H8  ModelProposalView / Phase-H completion
```

Phase-H focused verification:

```text
168 passed in 1.63s
```

Complete repository verification:

```text
4986 passed in 25.80s
git diff --check: PASS
```

## Upstream Authority

Production Phase-H input is exclusively:

```python
ApprovedInputRepository.list_active_approved_inputs(
    project_id,
) -> tuple[ApprovedInputManifest, ...]
```

Phase H must not derive authority from Draft Review state, original Review
Reports, Agent confidence, Consensus, inactive Approved Inputs or UI state.

## Candidate Artifacts

Identifiers:

```text
MCS-000001  Model Candidate Set
MCE-000001  Model Element Candidate
MCR-000001  Model Relationship Candidate
MCD-000001  Model Candidate Review Decision
```

Candidate IDs are project-local, sequential and immutable. Gaps are not reused.

Persistence:

```text
data/projects/<project_id>/model_candidates/sets/
└── MCS-000001/
    ├── manifest.json
    ├── elements/
    │   └── MCE-000001.json
    └── relationships/
        └── MCR-000001.json
```

Candidate Review Decisions are separate immutable evidence:

```text
data/projects/<project_id>/semantics/model_candidate_reviews/
└── MCD-000001.json
```

## Structure and Relationship Semantics

Versioned Phase-H profile:

`context/modeling/turing_model_structure_profile.json`

Profile:

```text
TURING_MODEL_STRUCTURE 1.0.0
```

Existing derivation-rules context:

`context/mapping/sysml_model_derivation_rules.json`

Relationship family, semantic intent and later SysML v2 serialization remain
separate concerns.

Materially different relationship interpretations remain separate MCRs and may
share one `relationship_choice_key`.

Automated relationship priority is advisory only.

Priority order:

```text
P1 evidence directness
P2 semantic fit
P3 endpoint certainty
P4 structural profile preference
P5 comparability impact
P6 assumption burden
P7 conformance
```

Comparability impact:

```text
improves
neutral
reduces
unknown
```

## Candidate Human Review

Decisions:

```text
accepted
rejected
deferred
accepted_exception
```

`accepted_exception` requires explicit rationale.

Review Decisions bind the exact:

- Candidate Set
- Candidate
- Candidate fingerprint
- Model Structure Profile
- structure-profile conformance fingerprint
- Approved Input snapshot fingerprint

Stale review evidence does not authorize Phase I.

The existing Phase-G `modules/human_review` contract was not weakened or
repurposed. Phase-H Candidate Review is a separate compatible authority layer.

## Sole H → I Read Boundary

Phase I shall consume reviewed Phase-H content only through:

```python
ModelCandidateReadService.load_phase_i_input(
    project_id,
    candidate_set_id,
) -> ModelCandidateAssemblyInput
```

The gate revalidates:

- exact Candidate Set integrity
- current active Approved Input authority
- Approved Input fingerprints and stable subject keys
- exact latest Candidate Review Decisions
- profile and conformance bindings
- accepted Relationship endpoint resolution
- authorization of accepted Relationship endpoints
- relationship choice conflicts
- project isolation

Unreviewed or deferred Candidates block Phase I.

Accepted unresolved or ambiguous Relationships block Phase I.

A Relationship cannot enter Phase I when an endpoint Element is rejected or
otherwise unauthorized.

No implicit latest-Candidate-Set selection exists.

## Model Proposal Projection

Technical Phase-H presentation service:

```python
ModelProposalReadService.load_model_proposal(
    project_id,
    candidate_set_id,
) -> ModelProposalView
```

The Model Proposal is deterministic and non-authoritative.

It projects:

- proposed Elements
- proposed Relationships
- lightweight structural overview
- Relationship choice groups
- comparability summary
- profile deviations
- required Human Review decisions
- blocking issues
- generation rationale summary
- Phase-I gate state
- next action

Deterministic JSON and Markdown projections are implemented.

The Model Proposal does not replace Candidate artifacts, Human Review authority
or CATIA.

The polished Architecture / Model Proposal UX remains WP-11.

## Phase Boundaries

```text
H  Approved Input → reviewed Model Candidates
I  reviewed Candidates → Internal Engineering Model
J  Internal Engineering Model → SysML v2 text
K  validation
L  versioned output package
```

Phase H generates no SysML v2 text.

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

Primary workflow:

- engineering result
- material uncertainty
- required human decision
- next action

Detailed evidence and audit information remain available on demand.

Streamlit remains the prototype UI technology through the product demo.

No React, Vue or FastAPI rewrite is on the demo critical path.

---

# Exact Next Work Package

## WP-05 / Phase I — Model Generation Agent / Internal Engineering Model

Phase I is next.

Objective:

Create a deterministic Internal Engineering Model from the exact reviewed
Candidate selection delivered by `ModelCandidateReadService`.

The Phase-I architecture discussion shall cover at least:

- Internal Engineering Model identity
- immutable versus rebuildable model snapshot boundary
- accepted MCE → internal Element mapping
- accepted MCR → internal Relationship mapping
- model hierarchy / containment representation
- RFLP structural representation
- preservation of relationship semantic intent
- accepted-exception representation
- exact H Candidate and MCD traceability
- exact Approved Input traceability
- structural-consistency validation owned by I
- deterministic serialization of the internal representation
- repository and persistence boundaries
- handoff contract to Phase J
- explicit prohibition of SysML v2 textual serialization in Phase I

Do not derive new engineering semantics from rejected, deferred or unreviewed
Candidates.

Do not bypass:

```python
ModelCandidateReadService.load_phase_i_input(...)
```

No Phase-I implementation begins before the exact architecture contract has been
surfaced, reviewed and explicitly accepted.

---

# Remaining Demo Roadmap

```text
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
2026-08-17  Functional freeze / rehearsal
2026-08-18  Product demo
```

Quality remains non-negotiable. Save time through decomposition and targeted
testing, not weaker authority, validation or traceability.

---

# Mandatory Engineering Boundaries

- CATIA remains engineering authority.
- The committed repository remains implementation authority.
- Human Review authority cannot be replaced by confidence or consensus.
- Original Processing evidence remains immutable.
- Finalized Review evidence remains exact and mutually bound.
- Only active Approved Inputs may support Phase-H Candidate Sets.
- Model Candidates are derived and non-authoritative.
- Human-accepted Model Candidates authorize Phase-I assembly only.
- `ModelCandidateReadService` is the sole H→I production read boundary.
- Phase I must not create new semantics from rejected or unreviewed Candidates.
- SysML v2 textual generation belongs to Phase J, not Phase I.
- Failed required validation blocks later publication.
- Progressive disclosure may hide complexity but may not remove traceability.
- No frontend technology rewrite before the product demo.

---

# Immediate Starting Instruction for the Next Chat

Begin with the Phase-I architecture contract.

Do not implement yet.

First:

1. inspect `ModelCandidateAssemblyInput` and the exact H→I read contract
2. inspect accepted CATIA structural expectations relevant to Internal Model
3. surface the exact Internal Engineering Model architecture questions
4. propose the minimal modular Phase-I target architecture
5. define persistence, identity and traceability boundaries
6. define the J handoff without implementing SysML v2 serialization
7. obtain explicit acceptance

Only after acceptance begin WP-05 implementation.
