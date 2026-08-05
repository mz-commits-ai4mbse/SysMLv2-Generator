# Current Chat Handover

## Purpose

This document is the authoritative starting point for the next implementation
chat.

It is intentionally self-contained and does not depend on previous chat
history.

The next chat shall begin from:

1. this handover
2. the committed repository
3. the remaining Collaboration Knowledge Base
4. the authoritative CATIA SysML v2 model

---

# Project

Project

Turing Generator

Repository

`mz-commits-ai4mbse/SysMLv2-Generator`

Branch

`main`

Verified Implementation Commit

`782b75a94f7008de9b08fc9724480f0786e6af01`

Architecture Version

1.3

Knowledge Base Version

1.8

Implementation Version

0.10

Roadmap Version

1.8

Last SSOT Update

2026-08-05

Current Phase

Phase G — Approved Input Promotion

Current Status

G1 through G3 completed. G4 active. G4.1 and G4.2a through G4.2c completed.
G4.2d is next.

Complete Automated Test Baseline

4463 passed

Remote Synchronization

`HEAD == origin/main`

Executable Prototype Target

2026-08-14

---

# Read Before Starting

Read in this order:

1. `collaboration/current_state.md`
2. `collaboration/roadmap.md`
3. `collaboration/working_rules.md`
4. `collaboration/model_registry.json`
5. `collaboration/decisions/ADR-016-human-review-workspace-and-approved-input-promotion-architecture.md`
6. `collaboration/change_log.md`
7. this handover

Then inspect the committed implementation for:

- Review Workspace foundations
- G3 P4/P9 evidence adapters
- G3 Review Item builders
- Review Document assembly
- G4.1 finalization validation
- G4.1 finalization authorization
- G4.2 finalized artifact contracts
- existing tests for those modules

Do not use previous chat history as the source of truth.

---

# Source Authority

The authority hierarchy is:

1. CATIA SysML v2 model for engineering knowledge
2. committed repository for implementation reality
3. Collaboration Knowledge Base for coordination and accepted decisions
4. chat history and temporary generated artifacts

The temporary SYSIDE shadow model may supplement missing CATIA information
until Phase N.

It shall never override or contradict CATIA.

Implementation evidence may identify Model Element Change Candidates.

It shall not silently create normative engineering knowledge.

---

# Repository Collaboration Workflow

GitHub is used passively by the AI assistant.

The AI assistant shall not:

- directly edit GitHub content
- create commits
- push branches
- open or merge pull requests
- stage files in the owner's local working tree
- use broad staging commands
- destructively clean local files

The required workflow is:

1. inspect the committed repository passively
2. propose exact repository-relative paths
3. provide complete local code or commands
4. Moritz applies changes locally
5. run focused tests
6. run complete regression when the subphase is complete
7. inspect `git diff --check`
8. stage exact intended paths only
9. Moritz commits and pushes
10. verify `HEAD == origin/main`

Never use:

```text
git add .
git add -A
```

Use explicit file paths only.

---

# Response and Implementation Style

Use German for communication.

Technical commands, complete files and structured technical content shall be
shown in fenced code blocks.

Work one controlled step at a time.

For each implementation step:

- state the exact objective
- name every affected path
- provide complete code or deterministic edit commands
- distinguish focused tests from complete regression
- do not claim success before Moritz posts the output
- diagnose the exact failure before changing code
- do not weaken integrity validation to make tests pass

The repository remains passive.

Moritz performs all local changes, commits and pushes.

---

# Current Working-tree Caution

The local working tree contains unrelated and generated files including:

- `.DS_Store`
- `__pycache__`
- generated ingestion reports
- demo projects
- team-run artifacts
- patch files
- local ZIP files

These files are not part of the current implementation or SSOT scope.

Do not stage them.

Only exact intended paths may be staged.

---

# Verified Phase-G Implementation

## G1 — Architecture

Architecture decision:

`collaboration/decisions/ADR-016-human-review-workspace-and-approved-input-promotion-architecture.md`

Accepted authority chain:

```text
Original Source
→ Processing Evidence
→ Human Review Workspace
→ Finalized Reviewed Document
→ Approved Input
```

## G2 — Review Workspace Foundations

Verified implementation commit:

`c61841789ed08b383e4cfc244d31f559125e6edb`

Implemented:

- RVD, RVV, RVR, RIT and SRA identifiers
- immutable domain types
- strict manifests
- deterministic fingerprints
- canonical project-local paths
- repository operations
- append-only revisions
- immutable Scoped Review Actions
- scanning and recovery diagnostics
- project isolation
- public API

Verification:

```text
Focused G2 suite: 398 passed
Complete automated suite: 4206 passed
```

## G3 — Evidence Adapters and Review Document Assembly

Verified implementation commit:

`53bf6046b931af7c7b5189cd78822fd7cf7d51ef`

Implemented:

- P4 evidence selection and references
- P4 Review Item construction
- P9 Review evidence selection
- P9 proposal adaptation
- P9 source and consensus evidence adaptation
- P9 Review Item construction
- stable subject keys
- original Review Report locators
- deterministic Review Document assembly
- exact Project, Source, Run, Attempt and Artifact traceability
- explicit element, relationship and open-question separation

Mandatory boundaries:

- do not heuristically merge P4 and P9 evidence
- do not construct a P4-only Review Document
- P9 Review Report remains the primary Review Document anchor
- original processing evidence remains immutable

## G4.1 — Finalization Validation and Authorization

Verified implementation commit:

`4cedfb10f81e08a3bbea7cdb2fee5d9a1235ddd5`

Implemented:

- finalization eligibility assessment
- open and unresolved item blocking
- exact version and revision binding
- validation fingerprint binding
- Human Review target type `review_document_finalization`
- detailed-review confirmation
- stale-decision rejection
- exact decision fingerprint binding
- immutable authorization
- atomic finalized-version transition

Verification:

```text
Focused G4.1 suite: 314 passed
Complete automated suite: 4402 passed
```

## G4.2a — Finalized Reviewed Document

Implemented module:

`modules/review_workspace/reviewed_document_manifest.py`

Implemented tests:

- `tests/test_finalized_reviewed_document_manifest.py`
- `tests/test_finalized_reviewed_document_public_api.py`

Artifact:

`reviewed_document.json`

## G4.2b — Effective Review Decisions

Implemented module:

`modules/review_workspace/effective_decisions_manifest.py`

Implemented tests:

- `tests/test_effective_review_decisions_manifest.py`
- `tests/test_effective_review_decisions_public_api.py`

Artifact:

`effective_decisions.json`

## G4.2c — Reviewed Report

Implemented module:

`modules/review_workspace/reviewed_report_renderer.py`

Implemented tests:

- `tests/test_reviewed_report_renderer.py`
- `tests/test_reviewed_report_renderer_public_api.py`

Artifact:

`reviewed_report.md`

Verified implementation commit for G4.2a through G4.2c:

`782b75a94f7008de9b08fc9724480f0786e6af01`

Verification:

```text
Focused G4.2a–G4.2c suite: 208 passed
Complete automated suite: 4463 passed
HEAD equals origin/main
```

---

# Exact Next Work Package

## G4.2d — Cross-artifact Consistency and Fingerprint Binding

Begin with inspection.

Do not implement before verifying the current files and contracts.

The three finalized artifacts are:

```text
reviewed_document.json
effective_decisions.json
reviewed_report.md
```

G4.2d shall define and implement one exact artifact-set contract that verifies:

- same Project ID
- same Review Document ID
- same Review Document Version ID
- same Review Revision ID
- same finalized timestamp
- exact Review Revision fingerprint
- exact finalization decision ID
- exact finalization decision fingerprint
- exact finalization validation fingerprint
- exact `reviewed_document.json` fingerprint
- exact `effective_decisions.json` fingerprint
- exact `reviewed_report.md` byte fingerprint
- exact Review Item identity and content set
- deterministic artifact ordering
- rejection of any mixed or tampered artifact set

G4.2d shall not yet:

- persist the final artifact set
- implement load, scan or recovery
- reopen a finalized Review Version
- create Approved Input
- generate model candidates
- generate SysML v2

After G4.2d:

```text
G4.2e — atomic persistence under finalized/
G4.2f — load, scan and recovery
G4.3 — reopening
G4.4 — integration and complete regression
```

---

# Model Element Change Candidate Discipline

Implementation-derived engineering concepts must not be lost until Phase N.

## Retrospective Requirement

Review all completed work from:

```text
G1
G2
G3
G4.1
G4.2a
G4.2b
G4.2c
```

Identify newly introduced or materially refined:

- requirements
- constraints
- functions
- Logical Components
- logical relationships
- allocations
- possible subsystem boundaries
- Subsystem Requirements
- Subsystem Functions
- Subsystem Logical Architecture
- Subsystem Physical Architecture

The retrospective inventory is required before or during the
Zwischenstandspräsentation.

## Ongoing Requirement

Beginning with G4.2d, every implementation phase shall continuously identify
Model Element Change Candidates.

Each phase-completion review shall explicitly assess whether new or refined
model elements arose.

## Authority Boundary

A candidate is not an accepted CATIA change.

Required sequence:

```text
Implementation observation
→ Model Element Change Candidate
→ engineering review
→ explicit acceptance
→ CATIA update
```

Phase N shall use the reviewed candidate inventory.

It shall not depend on complete reverse engineering of Phases G through L.

---

# Zwischenstandspräsentation

The roadmap order is:

```text
Phase G
→ Zwischenstandspräsentation
→ Phase H
```

The presentation is for the supervising professor.

It shall include:

- completed phases
- accepted architecture decisions
- executable workflow through Approved Input
- test and traceability evidence
- current CATIA architecture coverage
- retrospective Phase-G Model Element Change Candidates
- open risks and limitations
- planned Phases H through L

Before Phase H begins:

- feedback must be documented
- architecture and roadmap effects must be evaluated
- required decisions must be recorded
- the SSOT must be synchronized

---

# Mandatory Engineering Boundaries

- CATIA remains the engineering authority.
- The repository remains implementation authority.
- P4 evidence alone cannot create a Review Document.
- P9 Review Report remains the primary Review Document anchor.
- Consensus cannot authorize finalization or promotion.
- Confidence cannot authorize finalization or promotion.
- Stale Human Review Decisions cannot authorize changed targets.
- Fingerprint mismatch blocks finalization and promotion.
- Original processing artifacts remain immutable.
- Finalized review artifacts must remain mutually consistent.
- No Approved Input is created before G5.
- No Phase H implementation begins before Phase G and the
  Zwischenstandspräsentation are complete.
- Phase G does not generate model candidates.
- Phase G does not generate SysML v2.

---

# Immediate Starting Instruction for the Next Chat

First:

1. read the SSOT files
2. verify the local and remote commit
3. inspect the three G4.2 artifact modules and their tests
4. summarize the exact existing contracts
5. propose the narrow G4.2d artifact-set contract
6. do not implement until the contract and affected paths are clear

Continue with the same exact local-souffleur workflow used for G4.1 and
G4.2a–G4.2c.
