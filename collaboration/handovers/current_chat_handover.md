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

Verified Implementation Reference

`the commit containing this SSOT update`

Last Prior Committed Checkpoint

`cf3cd5f` — G4.2d finalized artifact-set integrity

Architecture Version

1.3

Knowledge Base Version

1.9

Implementation Version

0.11

Roadmap Version

1.9

Last SSOT Update

2026-08-06

Current Phase

Phase G — Approved Input Promotion

Current Status

G1 through G4 completed. G5 is next.

Verified Automated Test Baseline

4553 passing tests across the complete G4 regression and targeted stale-test
expectation correction

Remote Synchronization

Verify after the G4 completion commit and push.

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

- completed Review Workspace foundations
- P4/P9 evidence adapters and Review Document assembly
- finalization validation and authorization
- exact finalized artifact-set contracts
- finalized artifact persistence, loading and scanning
- Review Version reopening
- lifecycle integration tests
- ADR-016 Approved Input identity, promotion and lifecycle boundaries

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

- P4 and P9 evidence selection
- structured proposal and evidence references
- Review Item construction
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
- exact Version, Revision and validation binding
- Human Review finalization target
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

## G4.2a–G4.2c — Finalized Artifact Contracts

Verified implementation commit:

`782b75a94f7008de9b08fc9724480f0786e6af01`

Implemented artifacts:

```text
reviewed_document.json
effective_decisions.json
reviewed_report.md
```

Implemented:

- immutable machine-readable finalized manifests
- deterministic human-readable Reviewed Report
- exact Version, Revision, decision and validation binding
- deterministic serialization and fingerprints
- public package APIs

Verification:

```text
Focused G4.2a–G4.2c suite: 208 passed
Complete automated suite: 4463 passed
```

## G4.2d — Exact Finalized Artifact Set

Committed checkpoint:

`cf3cd5f`

Implemented:

- exact three-artifact membership
- deterministic ordering
- cross-artifact identity and fingerprint binding
- exact Review Item identity and content set
- artifact-set fingerprint
- rejection of mixed, incomplete and tampered sets

## G4.2e — Atomic Persistence

Included in the G4 completion commit containing this SSOT update.

Implemented:

- `.finalized.tmp` staging
- exact-byte write and flush
- validation before publication
- atomic rename to `finalized/`
- no finalized-directory overwrite
- unsafe-path and symbolic-link protection
- interrupted-write recovery state

## G4.2f — Load, Scan and Recovery Diagnostics

Included in the G4 completion commit containing this SSOT update.

Implemented:

- exact three-entry loading
- byte, UTF-8, fingerprint and binding validation
- deterministic regeneration comparison
- scan findings for interrupted, unsafe, unexpected, missing or invalid states
- fail-closed recovery-required reporting

## G4.3 — Reopening Finalized Review Versions

Included in the G4 completion commit containing this SSOT update.

Implemented:

- immutable finalized predecessor
- new successor Draft
- new Version, Revision and Review Item identities
- latest-finalized-only reopening
- linear version history without branching
- mandatory reason, actor and timestamp
- preserved materialized review state
- `carried_forward` one-to-one lineage
- stable subject-key preservation
- no copying of Scoped Review Actions
- atomic successor workspace creation

Verification:

```text
Focused G4.3 suite: 18 passed
Extended Review Workspace regression: 365 passed
```

## G4.4 — Integration and Regression

Verified lifecycle:

```text
finalize
→ persist exact artifact set
→ reopen
→ append successor revision
→ authorize and finalize successor
→ persist second independent artifact set
→ verify immutable predecessor
→ scan complete Review Document history
```

Verification:

```text
G4.4 lifecycle integration: 1 passed
Complete regression: 4552 passed, 1 stale vocabulary expectation
Corrected targeted vocabulary test: 1 passed
Effective verified baseline: 4553 passing tests
No production code changed after the complete regression
```

# Exact Next Work Package

## G5 — Approved Input Promotion and Lifecycle

Begin with architecture and implementation-contract inspection.

Read ADR-016 and inspect the completed G4 finalized Review contracts before
proposing implementation.

G5 shall define the exact contracts for:

- Approved Input identity
- immutable Approved Input manifest
- eligibility from one exact finalized Review Version
- exact binding to the finalized artifact set
- Approved Input repository and stable read contract
- promotion service API
- invalidation
- revocation
- supersession
- stable Phase H consumption boundary

G5 shall preserve:

- Project isolation
- exact Source, Run, Artifact and Review traceability
- Human Review authority
- immutable original processing evidence
- immutable finalized Review evidence
- deterministic fingerprints
- fail-closed validation

G5 shall not:

- promote an unfinalized Review Version
- use confidence or consensus as promotion authority
- mutate finalized Review artifacts
- generate model candidates
- generate SysML v2

Do not implement G5 before the exact contract, affected paths and test boundary
have been reviewed and explicitly accepted.

---

# Model Element Change Candidate Discipline

Implementation-derived engineering concepts must not be lost until Phase N.

## Recorded G4 Candidates

| ID | Origin | Candidate | Proposed type | Status |
|---|---|---|---|---|
| MEC-G4-001 | G4.2d | Exact Finalized Artifact Set as a three-artifact boundary | System Design Constraint | Engineering review pending |
| MEC-G4-002 | G4.2e–G4.2f | Atomic publication and explicit recovery boundary | System Design Constraint | Engineering review pending |
| MEC-G4-003 | G4.3 | `carried_forward` Review Item lineage | Logical Relationship | Engineering review pending |
| MEC-G4-004 | G4.3 | Linear Review Version succession without parallel branches | System Design Constraint | Engineering review pending |

Detailed rationale and implementation evidence are recorded in:

- `collaboration/current_state.md`
- `collaboration/model_registry.json`
- `collaboration/change_log.md`

These candidates are not accepted CATIA changes.

Required sequence:

```text
Implementation observation
→ Model Element Change Candidate
→ engineering review
→ explicit acceptance
→ CATIA update
```

## Retrospective Requirement

G1 through G4.2c still require retrospective examination before or during the
Zwischenstandspräsentation.

The four recorded candidates satisfy the continuous tracking requirement for
G4.2d through G4.4.

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
2. verify the G4 completion commit and remote synchronization
3. inspect ADR-016 and the completed G4 finalized Review contracts
4. summarize the exact Approved Input and promotion boundaries already accepted
5. propose the narrow G5 implementation contract and affected paths
6. do not implement until the G5 contract is explicitly accepted

Continue with the same exact local-souffleur workflow used throughout G4.
