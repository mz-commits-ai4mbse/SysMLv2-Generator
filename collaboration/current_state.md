# Current Project State

## Purpose

This document describes the current accepted project status, the committed
implementation reality and the active development objective of the Turing
Generator.

It is updated during every `SSOT UPDATE`.

It shall not redefine engineering knowledge contained in the authoritative
CATIA SysML v2 model.

---

# Project

Project

Turing Generator

Repository

`mz-commits-ai4mbse/SysMLv2-Generator`

Current Branch

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

Current Roadmap Version

1.9

Current Development Phase

Phase G — Approved Input Promotion

Current Status

Phase G Active — G1 through G4 Completed; G5 Next

Verified Automated Test Baseline

4553 passing tests across the complete G4 regression and targeted stale-test
expectation correction

End-to-End Prototype Target

2026-08-14

Last SSOT Update

2026-08-06

---

# Current Objective

Complete the executable end-to-end Turing Generator prototype no later than
2026-08-14.

The accepted prototype path is:

```text
Source
→ Processing Run
→ Human Review
→ Approved Input
→ Model Candidates
→ Internal Engineering Model
→ SysML v2 Generation
→ Validation
→ Versioned Output Package
```

The required implementation phases are:

```text
Phase G — Approved Input Promotion
→ Zwischenstandspräsentation
→ Phase H — Model Candidate Layer
→ Phase I — Model Generation Agent
→ Phase J — SysML v2 Code Generator
→ Phase K — Validation Layer
→ Phase L — Output Writer
```

Phase N and Phase Q follow after the executable prototype:

```text
Phase N — CATIA Shadow-model Migration and Final Reconciliation
→ Phase Q — Thesis Architecture Documentation
```

Post-prototype portability evaluation and low-priority enhancements follow
after Phase Q:

```text
Phase R — Task Profile Portability Evaluation
→ Phase S — Project Affinity Recommendation
```

---

# Current Engineering Priorities

Priority 1

Continue Phase G with G5 — Approved Input promotion and lifecycle.

Phase G shall establish the exact boundary between:

- raw Sources
- run-owned processing evidence
- Human Review Decisions
- Approved Input
- later model-candidate generation

Priority 2

Complete Phases G through L by 2026-08-14 without weakening:

- Human Review authority
- project isolation
- source and artifact traceability
- deterministic validation
- immutable published evidence
- CATIA engineering authority

Priority 3

Preserve the verified Phase F/P prototype baseline at:

`26acace4d7ba2849b33c5e0dacedf838f83c7705`

with:

- 3808 passing automated tests
- completed P9 manual acceptance audit
- successful project-bound ingestion ending in `awaiting_review`

Priority 4

Implement Phase H so that model relationship candidates are not treated as an
undifferentiated set.

The system shall support:

- explicit relationship candidates
- relationship type and semantic intent
- relationship priority
- prioritization rationale
- structural-comparability impact
- Human Review before acceptance

The prioritization shall address relationships whose intended meanings are
often used inconsistently or near-synonymously in source material or modeling
practice, including:

- dependency
- allocation
- flow
- refinement-related relationships
- derivation-related relationships
- other framework-specific relationship concepts

The objective is not merely to select plausible links.

The objective is to support comparable model structures across related
products, product variants and independently generated models.

Priority 5

Maintain complete feature, requirement and implementation traceability while
the prototype is completed.

The authoritative CATIA model remains the source of engineering requirements.

The committed repository remains the source of implementation reality.

Priority 6

Defer the following work until after the executable prototype unless required
to remove a blocker:

- Phase N final CATIA migration and reconciliation
- Phase Q thesis architecture documentation
- Phase R portability evaluation
- Phase S project-affinity recommendation
- project editing and deletion refinements
- OCR and unrestricted multimodal extraction

---

# Verified Implementation Baseline

## Phase F — Agentic Ingestion UI

Phase F remains complete and verified at:

`adce9ec65ca3e36b89686b55d397a34dd382fdb1`

Implemented capabilities include:

- modular agent and team execution architecture
- memory-based ingestion pipeline
- consensus framework
- deterministic engineering review report
- traceable gaps, ambiguities, risks and independent review questions
- Streamlit Agentic Ingestion UI
- Dry Run and LLM execution paths
- report, run-summary, consensus, agent-output and artifact browsing

## Phase P — Project Workspace and Project-bound Ingestion

Phase P is complete.

Final implementation verification commit:

`26acace4d7ba2849b33c5e0dacedf838f83c7705`

Complete automated test baseline:

3808 passed

Manual P9 acceptance audit:

PASS

Completed steps:

| Step | Deliverable | Status |
|---|---|---|
| P1 | Framework Template Definition | Completed |
| P2 | Project Manifest and Workspace Structure | Completed |
| P3 | Source Registry and mandatory Project Assignment | Completed |
| P4 | Framework-mapped heterogeneous Information Units | Completed |
| P5 | Processing State and Artifact Organization | Completed |
| P6 | Preliminary Coverage and Potential Model Support | Completed |
| P7 | Project Dashboard | Completed |
| P8 | Tests and Integration Readiness Review | Completed |
| P9 | Project-bound Agentic Ingestion Integration | Completed |

### P1 — Framework Template Definition

Verified at:

`82b5cbbe9bedac77a4b02928a596ea8fbdacc873`

Implemented capabilities include:

- versioned `TURING_RFLP_FRAMEWORK`
- 3 framework levels and 12 mapping targets
- stable framework identifiers
- zero-to-many framework assignments
- rejection of unknown mapping targets
- exclusion of `context_only` sources from framework mapping
- deterministic framework-template validation

### P2 — Project Manifest and Workspace Structure

Architecture decision:

`collaboration/decisions/ADR-005-project-workspace-architecture.md`

Verified through:

`36184a2d90db349555ac3bd64ccd5c27ecb68cec`

Implemented capabilities include:

- six-digit project identities
- separation of project identity and display name
- project display-name uniqueness
- strict Project Manifest validation
- project creation, loading, scanning and isolation
- safe project paths and symlink rejection
- deterministic project reopening

### P3 — Project Source Registry

Architecture decisions:

- `collaboration/decisions/ADR-009-textual-source-processing-boundary.md`
- `collaboration/decisions/ADR-010-project-source-registry-architecture.md`

Verified through:

`55cc4f104082ecfef70b3dcdeb8f28406ed95105`

Implemented capabilities include:

- mandatory project assignment for every persisted Source
- project-local Source identifiers
- immutable Source Manifests
- source content hashes and metadata
- `engineering_source` and `context_only` roles
- duplicate-content rejection within a project
- safe project-local source persistence
- strict separation of project and Source identity

### P4 — Framework-mapped Heterogeneous Information Units

Architecture decision:

`collaboration/decisions/ADR-011-semantic-information-unit-and-ontology-boundary.md`

Verified at:

`0c8ba428e7e6469e410b541c114d7a5a9474321c`

Implemented capabilities include:

- deterministic projections for text, Markdown, JSON, CSV, TSV and PDF text layers
- projection manifests and source locators
- pinned BFO 2020 and IOF Core 202602 reference snapshots
- ontology registry and deterministic reference-concept index
- Turing Core Vocabulary
- project glossary candidates and terminology decisions
- immutable source-traceable Information Units
- semantic extraction candidate contracts
- multi-agent semantic consensus, disagreement and variance
- terminology-mapping candidates
- framework-assignment candidates
- immutable Human Review Decisions
- exact target-content and validation-fingerprint binding
- deterministic token budgeting
- fail-closed required-context handling

### P5 — Processing State and Artifact Organization

Architecture decision:

`collaboration/decisions/ADR-012-processing-state-and-artifact-organization.md`

Verified through:

`9a9ef8bd7c08c354c638d4b0e072e308e7c02516`

Implemented capabilities include:

- immutable Processing Run Manifests
- immutable Processing Event Manifests
- immutable Processing Decision Manifests
- event-chain validation
- current-state reconstruction
- source-bound Processing Runs
- attempt identifiers
- run work and artifact directories
- retry, supersession, invalidation and recovery diagnostics
- Source-level and Project-level aggregation
- fail-closed state reporting

### P6 — Preliminary Coverage and Potential Model Support

Architecture decision:

`collaboration/decisions/ADR-013-preliminary-coverage-and-potential-model-support.md`

Verified through:

`f921b216d66ee359dea7cf116cfea03acb1e3510`

Implemented capabilities include:

- deterministic Preliminary Coverage assessment
- explicit support profile
- project-local coverage evidence
- covered, uncovered and attention-required states
- potential support assessment for future model scopes
- strict separation of Preliminary Coverage and Approved Generation Readiness

### P7 — Project Dashboard

Architecture decision:

`collaboration/decisions/ADR-014-project-dashboard-architecture.md`

Verified through:

`d8a3bc9bb55a4b7ab0fa6e999b74b8541bf224b6`

Project-creation fixes:

`fe0fd24`

Implemented capabilities include:

- common Project Dashboard
- Overview view
- Sources & Processing view
- Coverage & Support view
- Attention & Review view
- Traceability view
- project selection and constrained project creation
- evidence navigation
- safe document preview
- read-only dashboard boundary except for constrained project creation

### P8 — Tests and Integration Readiness Review

P8 confirmed:

- P1–P7 integration readiness
- no need for a parallel project or processing architecture
- need for a separate P9 project-bound ingestion integration boundary
- preservation of dashboard execution boundaries

### P9 — Project-bound Agentic Ingestion Integration

Architecture decision:

`collaboration/decisions/ADR-015-project-bound-agentic-ingestion-integration.md`

Verified through:

`26acace4d7ba2849b33c5e0dacedf838f83c7705`

Implemented capabilities include:

- common Turing Generator application shell
- project-bound Source upload and registration
- Source Projection before Phase F execution
- P5 Processing Run creation
- `agentic_ingestion` Processing Stage
- execution inside a run-owned work directory
- validation before publication
- immutable publication of run-owned artifacts
- `ProcessingArtifactReference` generation
- `artifact_published` and `review_requested` events
- successful final state `awaiting_review`
- Execution UI
- Dashboard return and review-report navigation

Manual acceptance evidence includes:

- negative processing case ending in `failed`
- successful dry-run case ending in `awaiting_review`
- 15 published artifact references
- all published artifact fingerprints verified
- no API-key fields persisted

Local demo data under `data/projects/` remains non-authoritative test evidence.

---

# Post-Phase-P Reconciliation Gate

## Status

Completed on 2026-07-31.

## Completed Deliverables

The completed gate includes:

- presentation of the Phase F/P prototype
- preservation of the verified implementation baseline
- inventory of implemented Phase F/P capabilities
- review of accepted architecture decisions
- first Architecture-to-Requirements Reconciliation against CATIA
- accepted CATIA System Requirements baseline
- accepted CATIA System Design Constraint baseline
- accepted System Function baseline
- accepted System Logical Architecture baseline
- feature and requirement coverage analysis
- explicit selection of Phase G as the next implementation phase

## Accepted CATIA System Baseline

The authoritative CATIA model now contains the accepted System-level baseline:

- 39 Stakeholder Requirements
- 102 System Requirements
- 30 active System Design Constraints
- 12 System Functions
- 8 Logical Components
- System Function interaction network
- Logical interconnection view
- complete Stakeholder Requirement coverage through System Functions

The 102 System Requirements are grouped into topical packages for navigation
and documentation only.

The grouping shall not be interpreted as:

- pre-allocation to Logical Components
- subsystem boundaries
- proof of implementation
- a replacement for the accepted derivation chain

The accepted derivation chain remains:

```text
Stakeholder Requirements
→ System Requirements
→ System Functions
→ Logical Components
→ implementation evidence
```

System Physical Architecture and Subsystem R/F/L/P remain deferred.

## Feature and Requirement Coverage

The completed reconciliation confirms:

- all 39 Stakeholder Requirements are covered by at least one System Function
- every System Requirement has one primary System Function allocation
- implementation status remains distinct from requirement coverage
- current runtime implementation is strongest in ingestion, processing,
  evidence, traceability and status presentation
- architecture derivation, model validation and SysML v2 generation remain the
  primary open prototype capabilities

## Phase N Scope Brought Forward

The Post-Phase-P Reconciliation Gate performed part of the originally planned
Phase N scope early.

Completed early:

- first Architecture-to-Requirements Reconciliation
- accepted System Requirement update
- accepted System Function modeling
- accepted System Logical Architecture modeling
- initial feature and requirement coverage baseline

Still retained in Phase N:

- migration of the temporary SYSIDE shadow model
- removal of duplicated maintained model authority
- final reconciliation after Phases G–L
- final synchronization with CATIA
- confirmation that CATIA is the only maintained engineering model

Phase N is therefore not complete.

---

# Current Architecture Baseline

## Engineering Authority

The authority hierarchy is:

1. CATIA SysML v2 model for engineering knowledge
2. committed repository for implementation reality
3. Collaboration Knowledge Base for roadmap, coordination and accepted decisions
4. chat history and temporary generated artifacts

The temporary SYSIDE shadow model may supplement missing CATIA information
until Phase N.

It shall never override or contradict CATIA.

Implementation evidence shall not silently create normative requirements.

## Accepted Framework

The implemented framework contains:

- Stakeholder Level
  - Stakeholders
  - User Needs
  - Stakeholder Requirements
  - Use Cases
- System Level
  - Requirements
  - Functional
  - Logical
  - Physical
- Subsystem Level
  - Requirements
  - Functional
  - Logical
  - Physical

Apollo 11 remains a non-normative structuring reference.

Its engineering content, CoSMA framework and package layout were not
transferred.

## Modular Artifact-oriented Architecture

The Turing Generator uses a modular, recipe-driven and artifact-oriented
architecture.

Important explicit artifacts include:

- project principles
- project scope context
- framework templates
- support profiles
- ontology registries
- vocabularies
- recipes
- agent profiles
- task definitions
- source manifests
- processing manifests
- events and decisions
- review reports
- run summaries
- generated output artifacts

The core infrastructure is intended to remain reusable while task-specific
profiles and artifacts are exchanged.

## Source-processing Boundary

The MVP processing boundary remains textual information.

Supported:

- text
- Markdown
- JSON
- CSV
- TSV
- deterministic textual projections
- PDF text layers

Outside the MVP:

- OCR
- image-only document interpretation
- technical-drawing interpretation
- unrestricted multimodal engineering extraction

## Processing and Publication Boundary

A successful P9 execution:

- validates Source Projection
- executes Phase F
- publishes immutable run-owned artifacts
- requests Human Review
- reaches `awaiting_review`

It does not:

- create Approved Input
- create approved engineering knowledge
- satisfy Approved Generation Readiness
- generate model candidates
- generate SysML v2

Published run-owned artifacts are authoritative evidence for what the run
produced.

They are not authoritative engineering knowledge until an accepted promotion
workflow approves them.

## Human Review Boundary

Consensus, confidence and variance are review evidence.

They are not approval or publication authority.

Every promotion or engineering-publication target requires an explicit
persisted Human Review Decision bound to the current target content and
applicable validation fingerprints.

## Model Comparability Boundary

Model comparability is an explicit target for Phase H and Phase K.

Related models, including product variants, shall be generated using a
consistent structural profile so that meaningful comparison remains possible.

The profile shall address:

- preferred model-element structure
- preferred relationship semantics
- canonical relationship choices
- required comparison anchors
- allowed structural variation
- relationship prioritization criteria
- reviewable exceptions

Automated prioritization remains advisory.

Human Review shall authorize accepted relationship candidates and exceptions.

---

# Active Phase G — Approved Input Promotion

## Status

Phase G remains active.

Completed:

- G1 — Human Review Workspace and Approved Input architecture
- G2 — Review Workspace foundations
- G3 — P4/P9 evidence adapters and Review Item construction
- G4.1 — Review finalization validation and authorization
- G4.2a — immutable `reviewed_document.json` contract
- G4.2b — immutable `effective_decisions.json` contract
- G4.2c — deterministic `reviewed_report.md` renderer
- G4.2d — exact finalized artifact-set integrity
- G4.2e — atomic finalized artifact persistence
- G4.2f — finalized artifact loading, scanning and recovery diagnostics
- G4.3 — controlled reopening of finalized Review Versions
- G4.4 — lifecycle integration and complete regression

Next:

- G5 — Approved Input promotion and lifecycle

Phase G as a whole is not complete.

## Accepted Architecture

Architecture decision:

`collaboration/decisions/ADR-016-human-review-workspace-and-approved-input-promotion-architecture.md`

ADR-016 defines the authority chain:

```text
Processing Evidence
→ Human Review Workspace
→ Finalized Reviewed Document
→ Approved Input
```

The following architecture topics remain accepted:

- Approved Input granularity and identity
- eligible P4/P9 evidence boundaries
- Review Target architecture
- fingerprint binding
- lifecycle architecture
- stable Phase H read boundary

## Work Breakdown

| Step | Deliverable | Status |
|---|---|---|
| G1 | Human Review Workspace and Approved Input architecture | Completed |
| G2 | Review Workspace foundations | Completed |
| G3 | P4/P9 evidence adapters and Review Item construction | Completed |
| G4 | Review editing, finalization and reopening | Completed |
| G5 | Approved Input promotion and lifecycle | Next |
| G6 | Human Review and promotion UI | Planned |
| G7 | Integration, audit and end-to-end regression | Planned |

## G3 — Evidence Adapters and Review Document Assembly

Verified implementation commit:

`53bf6046b931af7c7b5189cd78822fd7cf7d51ef`

Implemented capabilities include:

- deterministic selection of eligible P9 Review evidence
- explicit separation of P9 Agent proposals, consensus evidence and Review Reports
- deterministic P4 evidence selection
- structured P4 evidence references
- P4 Review Item construction
- P9 proposal and evidence adaptation
- P9 Review Item construction
- stable subject keys
- original Review Report locators
- element, relationship and open-question separation
- deterministic initial Review Document assembly
- exact Project, Source, Processing Run, Attempt and Artifact binding
- preservation of original immutable processing evidence
- explicit rejection of heuristic P4/P9 evidence merging
- prohibition of P4-only Review Document construction

G3 does not finalize reviews and does not create Approved Input.

## G4.1 — Review Finalization Authorization

Verified implementation commit:

`4cedfb10f81e08a3bbea7cdb2fee5d9a1235ddd5`

Implemented capabilities include:

- deterministic finalization eligibility assessment
- blocking of open and unresolved Review Items
- exact Review Document Version and Review Revision binding
- exact validation-fingerprint binding
- Human Review target type `review_document_finalization`
- exact persisted `confirm` authorization
- detailed-review requirement
- stale-decision rejection
- exact decision-fingerprint binding
- immutable authorization record
- atomic transition of the Review Document Version to `finalized`

Verification:

```text
Focused G4.1 suite: 314 passed
Complete automated suite after G4.1: 4402 passed
```

## G4.2 — Immutable Finalized Review Artifacts

### G4.2a–G4.2c — Artifact Contracts

Verified implementation commit:

`782b75a94f7008de9b08fc9724480f0786e6af01`

Implemented:

- immutable `reviewed_document.json`
- immutable `effective_decisions.json`
- deterministic `reviewed_report.md`
- exact Review Version, Revision, decision and validation binding
- deterministic serialization and artifact fingerprints
- public package APIs

Verification:

```text
Focused G4.2a–G4.2c suite: 208 passed
Complete automated suite: 4463 passed
```

### G4.2d — Exact Artifact-set Integrity

Committed checkpoint:

`cf3cd5f`

Implemented:

- exact three-artifact membership
- deterministic artifact ordering
- cross-artifact Project, Document, Version and Revision identity
- exact finalization decision and validation binding
- exact Review Item identity and content set
- artifact-set fingerprinting
- rejection of mixed, incomplete or tampered sets

### G4.2e — Atomic Persistence

Included in the G4 completion commit containing this SSOT update.

Implemented:

- exact-byte staging under `.finalized.tmp`
- write and flush before validation
- validation before publication
- atomic rename to `finalized/`
- no overwrite of an existing finalized directory
- protection against unsafe paths and symbolic links
- source-change detection during persistence
- fail-closed interrupted-write state

### G4.2f — Load, Scan and Recovery Diagnostics

Included in the G4 completion commit containing this SSOT update.

Implemented:

- exact three-entry loading
- UTF-8 and byte-fingerprint validation
- regeneration and binding comparison
- scan findings for interrupted publication
- scan findings for unsafe, unexpected, missing or invalid finalized content
- explicit recovery-required states

## G4.3 — Reopening Finalized Review Versions

Included in the G4 completion commit containing this SSOT update.

Implemented:

- immutable finalized predecessor
- successor Draft with a new Review Version identity
- new initial Review Revision and Review Item identities
- exact predecessor finalization and artifact-set validation
- reopening only from the latest finalized version
- linear version history without branching
- mandatory reopen reason and actor metadata
- preservation of materialized review state
- `carried_forward` one-to-one lineage
- unchanged stable subject keys
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
finalize initial Review Version
→ persist and load exact finalized artifact set
→ reopen as successor Draft
→ append successor revision
→ authorize and finalize successor
→ persist and load second independent artifact set
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

## Current Development Objective

Continue with:

```text
G5 — Approved Input promotion and lifecycle
```

G5 shall define and implement:

- Approved Input identity and immutable manifest
- exact promotion eligibility from a finalized Review Version
- exact binding to the finalized artifact set
- Approved Input repository and stable read contract
- promotion service
- invalidation, revocation and supersession
- stable Phase H consumption boundary

G5 shall not generate model candidates or SysML v2.

## Development-plan Position

Completed Architecture items:

```text
[x] Approved-Input-Granularität / Identität
[x] P4/P9-Quellen + Review Targets
[x] Fingerprints, Lifecycle, Phase-H-Vertrag
```

Completed Promotion item:

```text
[x] Decision-/Fingerprint-Bindung
```

Still open:

```text
Domain
[ ] IDs, Typen, Manifest
[ ] Repository + Read Contract
[ ] Validation + Fehlerhierarchie

Promotion
[ ] Eligibility aus P4/P9
[ ] promote / invalidate / revoke / supersede

Abschluss
[ ] Vollständige Traceability
[ ] Review-/Promotion-UI
[ ] Tests + Manual Acceptance
```

The Review Workspace portions of the Domain work are implemented.

The Domain checkboxes remain open until the complete Approved Input domain,
repository, validation boundary and stable Phase H read contract are available.

## Mandatory Boundaries

- unreviewed P9 artifacts cannot become Approved Input
- P4 evidence alone cannot create a Review Document
- consensus cannot authorize finalization or promotion
- confidence cannot authorize finalization or promotion
- stale Human Review Decisions cannot authorize a changed target
- fingerprint mismatch blocks finalization and promotion
- original processing artifacts remain immutable
- finalized review artifacts must remain mutually consistent
- reopening never mutates a finalized predecessor
- Preliminary Coverage remains separate from Approved Generation Readiness
- Phase G shall not generate model candidates
- Phase G shall not generate SysML v2

---

# Cross-phase Model Element Change Candidates

## Purpose

Implementation shall not create a second hidden engineering architecture that
must be reverse-engineered during Phase N.

New or materially refined engineering and architecture concepts arising during
implementation shall therefore be recorded as Model Element Change Candidates
for later reconciliation with the authoritative CATIA SysML v2 model.

A Model Element Change Candidate is not an accepted CATIA model change.

CATIA remains the authoritative engineering model.

The accepted sequence is:

```text
Implementation observation
→ Model Element Change Candidate
→ engineering review
→ explicit acceptance
→ CATIA model update
```

## Candidate Scope

Candidates may concern:

- Stakeholder Requirements
- System Requirements
- System Design Constraints
- System Functions
- Logical Components
- logical relationships and allocations
- Physical Architecture decisions
- Subsystem Requirements
- Subsystem Functions
- Subsystem Logical Architecture
- Subsystem Physical Architecture
- relevant cross-level dependencies and allocations

Each candidate shall preserve at least:

- originating implementation phase
- affected model area
- proposed element type
- reason and engineering rationale
- implementation evidence
- known relationships
- review status
- CATIA transfer status

## G4 Candidate Inventory

### MEC-G4-001 — Exact Finalized Artifact Set

Originating implementation phase:

`G4.2d`

Affected model area:

Human Review Workspace and finalized Review artifacts.

Proposed element type:

System Design Constraint.

Engineering rationale:

A finalized Review result is valid only as the exact immutable set of
`reviewed_document.json`, `effective_decisions.json` and `reviewed_report.md`.
Mixed, incomplete, additional or fingerprint-inconsistent artifacts shall not
form a valid finalized Review result.

Implementation evidence:

- `modules/review_workspace/finalized_artifact_set.py`
- finalized artifact-set manifest and binding tests

Known relationships:

- constrains Review finalization output
- provides the integrity boundary consumed by G5 promotion
- binds one finalized Review Version and one exact Review Revision

Review status:

Recorded; engineering review pending.

CATIA transfer status:

Not started.

### MEC-G4-002 — Atomic Publication and Recovery Boundary

Originating implementation phase:

`G4.2e–G4.2f`

Affected model area:

Finalized Review persistence, loading, scanning and recovery.

Proposed element type:

System Design Constraint.

Engineering rationale:

A finalized artifact set shall become visible only through a validated atomic
publication. Interrupted, unsafe, incomplete or altered states shall fail
closed and shall be reported as requiring recovery rather than being treated as
valid finalized evidence.

Implementation evidence:

- `modules/review_workspace/repository.py`
- finalized artifact persistence, loading and scan tests

Known relationships:

- constrains finalized artifact persistence
- constrains repository recovery behavior
- protects the G5 promotion eligibility boundary

Review status:

Recorded; engineering review pending.

CATIA transfer status:

Not started.

### MEC-G4-003 — Carried-forward Review Item Lineage

Originating implementation phase:

`G4.3`

Affected model area:

Review Item lineage across Review Document Versions.

Proposed element type:

Logical Relationship.

Engineering rationale:

A Review Item copied into a reopened successor version requires explicit
one-to-one lineage to exactly one predecessor Review Item while preserving its
stable subject key. The relation is distinct from split, merge and original
creation.

Implementation evidence:

- `modules/review_workspace/types.py`
- `modules/review_workspace/item_manifest.py`
- `modules/review_workspace/reopening.py`
- Review reopening tests

Known relationships:

- `lineage_operation = carried_forward`
- exactly one `derived_from_review_item_ids` entry
- stable subject key remains unchanged
- materialized review state is preserved

Review status:

Recorded; engineering review pending.

CATIA transfer status:

Not started.

### MEC-G4-004 — Linear Review Version Succession

Originating implementation phase:

`G4.3`

Affected model area:

Review Document Version lifecycle.

Proposed element type:

System Design Constraint.

Engineering rationale:

Only the latest finalized Review Version may be reopened. Reopening creates one
new successor Draft, preserves the finalized predecessor and prohibits parallel
successor branches or reopening when a later Draft or finalized version exists.

Implementation evidence:

- `modules/review_workspace/reopening.py`
- `modules/review_workspace/repository.py`
- Review reopening and lifecycle integration tests

Known relationships:

- constrains the Review reopening function
- defines predecessor and successor version lineage
- preserves immutable historical review evidence
- prevents ambiguous promotion ancestry

Review status:

Recorded; engineering review pending.

CATIA transfer status:

Not started.

## Retrospective Requirement

G1 through G4.2c still require retrospective examination before or during the
Zwischenstandspräsentation.

The G4.2d through G4.4 candidates above satisfy the continuous tracking rule
for the completed G4 work package.

## Ongoing Rule

Candidate identification remains mandatory during every subsequent
implementation phase.

Phase completion review shall include an explicit check for newly created or
materially refined Model Element Change Candidates.

Phase N shall use the accumulated and reviewed candidate inventory as an input
to final Architecture-to-Requirements Reconciliation.

Phase N shall not rely on complete retrospective reverse engineering of Phases
G through L.

---

# Zwischenstandspräsentation

## Position

The Zwischenstandspräsentation takes place after completion of Phase G and
before the start of Phase H.

## Purpose

Present the implemented path from Source processing through Human Review to
Approved Input to the supervising professor.

## Required Content

- completed development phases
- accepted architecture decisions
- executable workflow through Approved Input
- current automated-test and traceability evidence
- current CATIA architecture coverage
- retrospective Phase-G Model Element Change Candidates
- open risks, limitations and technical debt
- planned Phases H through L

## Exit Criteria

- presentation completed
- professor feedback documented
- architecture and roadmap effects evaluated
- required decisions recorded in the Collaboration Knowledge Base
- Phase-G Model Element Change Candidate inventory reviewed
- SSOT synchronized before Phase H begins

The presentation does not by itself change the authoritative CATIA model.

Explicit review and acceptance remain required.

# Planned Prototype Phases

## Phase H — Model Candidate Layer

Phase H shall create traceable model-element and relationship candidates from
Approved Input without generating SysML v2 code.

In addition to model-element candidates, Phase H shall implement:

- relationship candidates
- canonical relationship semantics
- relationship priority
- prioritization rationale
- comparability impact
- structural-profile conformance
- Human Review of selected relationships
- explicit handling of alternative or near-synonymous relationship concepts

The accepted relationship set shall support comparable structures across
related models and product variants.

## Phase I — Model Generation Agent

Phase I shall assemble reviewed candidates into an internal engineering model.

It shall preserve:

- source traceability
- Approved Input traceability
- candidate traceability
- relationship decisions
- structural-profile references
- Human Review Decisions

## Phase J — SysML v2 Code Generator

Phase J shall generate valid SysML v2 textual notation from the internal model.

The generator shall target the accepted versioned notation and artifact
structure profiles.

## Phase K — Validation Layer

Phase K shall validate:

- syntax
- target-notation conformance
- target-artifact structure
- model structure
- relationship consistency
- relationship semantic consistency
- constraint conformance
- traceability
- comparability-profile conformance
- larger-context compatibility where available

## Phase L — Output Writer

Phase L shall publish:

- versioned SysML v2 output files
- validation reports
- traceability artifacts
- generation summaries
- export metadata
- a complete versioned output package

---

# Post-prototype Phases

## Phase N — CATIA Shadow-model Migration and Final Reconciliation

Phase N retains:

- SYSIDE shadow-model migration
- final synchronization with CATIA
- removal of duplicated maintained model authority
- final reconciliation after Phases G–L
- final requirement and architecture coverage
- confirmation of CATIA-only maintained model authority

## Phase Q — Thesis Architecture Documentation

Phase Q shall document:

- development phases
- architecture decisions
- alternatives and rationale
- consequences
- requirement traceability
- implementation traceability
- ontology and semantic architecture
- Human Review architecture
- validation architecture
- model-comparability approach
- limitations and deferred work

## Phase R — Task Profile Portability Evaluation

Phase R shall evaluate the thesis that the core Turing Generator architecture
can be adapted quickly to a different engineering task by replacing a bounded
set of task-specific artifacts.

The reusable core is expected to include:

- Project Workspace
- Source Registry
- Processing Runs
- artifact persistence
- Human Review
- evidence and traceability
- dashboard
- agent execution
- publication gates

The evaluation shall produce a Task Profile Replacement Manifest that records:

- artifact path
- artifact role
- core or task-specific classification
- unchanged, adapted or replaced status
- dependencies
- required validation
- required code changes

The initial alternate task shall be Requirements Quality and Completeness
Analysis.

It shall assess:

- requirement formulation against an explicitly selected standard or rule set
- requirement completeness
- requirement atomicity
- ambiguity
- contradictions between requirements
- missing information
- proposed corrections
- proposed additions
- Human Review of proposed changes

The evaluation shall measure:

- number of changed files
- share of unchanged core modules
- implementation time
- reused tests
- new validation rules
- required code changes
- achieved functional coverage

## Phase S — Project Affinity Recommendation

Phase S is a low-priority post-Phase-R enhancement.

When a user selects new data for upload, the system may analyze the data before
persistent Source registration and recommend existing projects that appear to
fit.

The recommendation may consider:

- project description
- framework template
- existing Sources
- accepted project vocabulary
- framework coverage
- semantic similarity

The result shall be a ranked recommendation.

It shall not automatically assign or persist the Source.

The user shall confirm or override the project selection before registration.

This preserves the accepted rule that every persisted Source belongs to exactly
one Project and that no permanent unassigned Source pool exists.

---

# Not Yet Implemented

The following capabilities are not yet implemented:

- Approved Input Promotion
- Approved Input repository and API
- end-to-end review-to-promotion workflow
- model candidate layer
- relationship candidate prioritization
- canonical relationship-selection profile
- model comparability profile
- internal model generation
- SysML v2 code generation
- generated-model validation
- versioned export package
- CATIA synchronization
- final shadow-model migration
- task-profile portability evaluation
- alternate Requirements Quality and Completeness task
- project-affinity recommendation
- project editing after creation
- project deletion including assigned data
- refined retry and successor UI
- operational live-team performance measurements
- OCR and unrestricted multimodal extraction

---

# Current Known Limitations and Risks

## Active

- the end-to-end prototype schedule is compressed to 2026-08-14
- Approved Input identity, repository and promotion lifecycle remain open in G5
- P9 ends in `awaiting_review`, not Approved Input
- no model candidates are generated
- no internal engineering model is generated
- no SysML v2 code is generated
- no generated-model validation or export exists
- final relationship semantics and comparability rules are not yet defined
- full live-team performance and cost measurements remain open
- project editing and deletion remain open
- local demo data remains non-authoritative

## Controlled by Design

- project and Source identities remain separate
- every persisted Source belongs to one Project
- Source and artifact content is hash-bound
- cross-project mixing is rejected
- unknown framework and ontology references are rejected
- `context_only` Sources cannot create engineering evidence
- candidates remain non-authoritative until Human Review
- consensus and confidence cannot bypass Human Review
- required prompt context cannot be silently truncated
- ontology snapshots are pinned and integrity-checked
- CATIA remains authoritative for engineering knowledge
- P9 artifacts remain processing evidence until promotion
- relationship prioritization will remain advisory until Human Review
- project-affinity recommendations will remain advisory until user confirmation

---

# Next Milestone

G5 — Approved Input Promotion and Lifecycle

Execution order:

```text
G5 implementation contract
→ explicit contract acceptance
→ implementation
→ focused tests
→ review
→ G5 completion decision
```

The immediate next work item is the exact G5 Approved Input identity,
repository, eligibility and lifecycle contract.

No Phase H implementation shall begin until Phase G provides a stable,
reviewed Approved Input contract.

---

# Repository Collaboration Workflow

External GitHub repositories and repository links are used passively for
inspection only.

AI assistants shall not commit, push or directly modify GitHub repository
content.

Repository changes are applied, reviewed, committed and pushed locally by the
project owner.

AI assistants act as implementation guides and identify every affected file by
repository-relative path before proposing a change.

Broad staging commands shall not be used in a mixed working tree.

---

# SSOT Update Cadence

This update completes G4 and activates G5 as the next Phase-G work package.

It records:

- exact finalized artifact-set integrity
- atomic finalized artifact persistence
- finalized artifact loading, scanning and recovery diagnostics
- controlled reopening with immutable predecessor preservation
- lifecycle integration and regression evidence
- four G4 Model Element Change Candidates
- the transition to Approved Input promotion and lifecycle

The next SSOT update is due after G5 completion or when a critical handover
requires synchronization.

---

# Reference Documents

- Roadmap: `roadmap.md`
- Working Rules: `working_rules.md`
- Architecture Decisions: `decisions/`
- Model Registry: `model_registry.json`
- Change Log: `change_log.md`
- Handover: `handovers/current_chat_handover.md`
- Framework Template: `../context/frameworks/turing_rflp_framework.json`
- Support Profile: `../context/frameworks/turing_preliminary_support_profile.json`
- Ontology Registry: `../context/semantics/ontology_registry.json`
- Turing Core Vocabulary: `../context/semantics/turing_core_vocabulary.json`
