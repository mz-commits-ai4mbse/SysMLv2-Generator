# Roadmap

## Purpose

This roadmap defines the official development phases of the Turing Generator.

Each phase represents a major engineering milestone.

A phase is considered complete only after:

- architecture acceptance where required
- implementation
- testing
- review
- SSOT UPDATE or an explicitly accepted milestone synchronization

have been completed.

---

# Project Status

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

**Phase G — Approved Input Promotion**

Current Status

Phase G Active — G1 through G4 Completed; G5 Next

Verified Implementation Reference

`the commit containing this SSOT update`

Last Prior Committed Checkpoint

`cf3cd5f` — G4.2d finalized artifact-set integrity

Verified Automated Test Baseline

4553 passing tests across the complete G4 regression and targeted stale-test
expectation correction

Manual P9 Acceptance Audit

PASS

End-to-End Prototype Target

2026-08-14

---

# End-to-End Prototype Critical Path

The accepted executable prototype path is:

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

The critical implementation phases are:

```text
Phase G
→ Zwischenstandspräsentation
→ Phase H
→ Phase I
→ Phase J
→ Phase K
→ Phase L
```

The prototype target date applies to Phases G through L.

Phase N and later phases do not block the executable prototype target unless
they are required to resolve a critical implementation defect.

---

# Phase F — Agentic Ingestion UI

## Objective

Provide a functional user interface for the complete agentic ingestion workflow.

## Deliverables

- Legacy data upload
- Team configuration
- Dry Run
- LLM execution
- memory-based ingestion pipeline
- deterministic engineering review report
- traceable gaps, ambiguities, risks and review questions
- artifact browser
- report and run-summary navigation

## Exit Criteria

- complete ingestion workflow operational
- review report suitable for engineering review
- memory pipeline fully integrated
- stable demonstration UI
- automated tests pass

## Status

Completed

Verified in:

`adce9ec65ca3e36b89686b55d397a34dd382fdb1`

---

# Phase P — Project Workspace and Project-bound Ingestion

## Objective

Introduce project-oriented processing around the completed Phase F ingestion
pipeline.

Multiple individually ingested Sources shall produce heterogeneous, traceable
Information Units and project-bound Processing Runs that can later support
Approved Input Promotion and model generation.

## Accepted Framework

The Phase P framework is:

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

The implemented framework template is:

`context/frameworks/turing_rflp_framework.json`

Apollo 11 remains a non-normative structuring reference.

Its engineering content, CoSMA framework and package layout were not
transferred.

## Work Breakdown

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

## P1 Completion

Verified in:

`82b5cbbe9bedac77a4b02928a596ea8fbdacc873`

Implemented deliverables:

- versioned `TURING_RFLP_FRAMEWORK`
- stable identifiers for 3 framework levels and 12 mapping targets
- zero-to-many framework assignments
- deterministic framework validation
- rejection of unknown framework targets
- exclusion of `context_only` Sources from framework mapping

## P2 Completion

Architecture decision:

`collaboration/decisions/ADR-005-project-workspace-architecture.md`

Verified through:

`36184a2d90db349555ac3bd64ccd5c27ecb68cec`

Implemented deliverables:

- six-digit project identity
- separation of project identity and display name
- strict Project Manifest contract
- project creation and persistence
- safe reopening
- project isolation
- public Project Workspace API

## P3 Completion

Architecture decisions:

- `collaboration/decisions/ADR-009-textual-source-processing-boundary.md`
- `collaboration/decisions/ADR-010-project-source-registry-architecture.md`

Verified through:

`55cc4f104082ecfef70b3dcdeb8f28406ed95105`

Implemented deliverables:

- mandatory project assignment
- immutable project-local Source Manifests
- separate Project and Source identities
- `engineering_source` and `context_only` roles
- duplicate-content protection
- safe source persistence and scanning

## P4 Completion

Architecture decision:

`collaboration/decisions/ADR-011-semantic-information-unit-and-ontology-boundary.md`

Verified through:

`0c8ba428e7e6469e410b541c114d7a5a9474321c`

Implemented deliverables:

- deterministic source projections
- text, Markdown, JSON, CSV, TSV and PDF text-layer adapters
- source-traceable Information Units
- pinned BFO 2020 and IOF Core 202602 references
- ontology registry and reference-concept index
- Turing Core Vocabulary
- project glossary candidates and terminology decisions
- semantic extraction candidates
- multi-agent consensus, disagreement and variance
- terminology-mapping candidates
- framework-assignment candidates
- immutable Human Review Decisions
- exact fingerprint-bound publication gates
- deterministic token budgeting
- fail-closed required-context handling

## P5 Completion

Architecture decision:

`collaboration/decisions/ADR-012-processing-state-and-artifact-organization.md`

Verified through:

`9a9ef8bd7c08c354c638d4b0e072e308e7c02516`

Implemented deliverables:

- Processing Run, Event and Decision Manifests
- event-history based current-state reconstruction
- run-owned work and artifact directories
- retry, supersession, invalidation and recovery behavior
- Source-level and Project-level processing aggregation
- fail-closed issue reporting

## P6 Completion

Architecture decision:

`collaboration/decisions/ADR-013-preliminary-coverage-and-potential-model-support.md`

Verified through:

`f921b216d66ee359dea7cf116cfea03acb1e3510`

Implemented deliverables:

- deterministic Preliminary Coverage assessment
- potential model-support assessment
- support profile
- source and framework evidence binding
- explicit attention and missing-coverage states
- separation of Preliminary Coverage from Approved Generation Readiness

## P7 Completion

Architecture decision:

`collaboration/decisions/ADR-014-project-dashboard-architecture.md`

Verified through:

`d8a3bc9bb55a4b7ab0fa6e999b74b8541bf224b6`

Project-creation fixes:

`fe0fd24`

Implemented deliverables:

- Project Dashboard
- project selection and constrained project creation
- Sources & Processing view
- Coverage & Support view
- Attention & Review view
- Traceability view
- evidence navigation and document preview
- read-only dashboard boundary except for constrained project creation

## P8 Completion

P8 confirmed:

- P1–P7 integration readiness
- no need for a parallel project or processing architecture
- need for a separate P9 project-bound ingestion integration boundary
- preservation of dashboard execution boundaries

## P9 Completion

Architecture decision:

`collaboration/decisions/ADR-015-project-bound-agentic-ingestion-integration.md`

Verified through:

`26acace4d7ba2849b33c5e0dacedf838f83c7705`

Implemented deliverables:

- common Turing Generator application shell
- project-bound Source upload and registration
- Source Projection before Phase F execution
- P5 Processing Run bridge
- `agentic_ingestion` Processing Stage
- project-bound Phase F execution root
- work-output validation
- immutable publication of run-owned artifacts
- `ProcessingArtifactReference` generation
- `artifact_published` and `review_requested` events
- final state `awaiting_review`
- Execution UI
- Dashboard return and review-report navigation

Verification:

- complete automated test suite: 3808 passed
- manual P9 acceptance audit: PASS
- remote synchronization: `HEAD == origin/main`

## Phase P Exit Criteria

- a Project can be created, persisted and reopened
- multiple Sources can be assigned and processed independently
- every artifact remains traceable to Project and Source
- project source registry and processing state persist
- semantic candidates and decisions remain project-isolated
- Preliminary Coverage remains distinct from Approved Generation Readiness
- cross-project data mixing is prevented
- Human Review gates cannot be bypassed
- Project Dashboard shows accepted Phase P information
- project-bound ingestion reaches `awaiting_review`
- automated tests and manual acceptance checks pass
- SSOT update complete

## Status

Completed

---

# Post-Phase-P Reconciliation Gate

## Purpose

Create a deliberate cut after the completed Phase F/P prototype before further
feature implementation.

The gate preserves the demonstrable baseline and reconciles implementation
reality with the authoritative CATIA SysML v2 model.

## Completed Deliverables

- Phase F/P prototype presented
- verified implementation baseline preserved
- Phase F/P capability inventory completed
- accepted architecture decisions reviewed
- first Architecture-to-Requirements Reconciliation completed
- accepted CATIA System Requirements baseline created
- accepted CATIA System Design Constraint baseline created
- accepted System Function baseline created
- accepted System Logical Architecture baseline created
- Feature and Requirement Coverage Matrix created
- implementation status distinguished from requirement coverage
- Phase G selected as the next implementation phase

## Accepted CATIA Baseline

- 39 Stakeholder Requirements
- 102 System Requirements
- 30 active System Design Constraints
- 12 System Functions
- 8 Logical Components
- System Function interaction network
- Logical interconnection view
- all 39 Stakeholder Requirements covered through System Functions

The accepted derivation chain is:

```text
Stakeholder Requirements
→ System Requirements
→ System Functions
→ Logical Components
→ implementation evidence
```

System Physical Architecture and Subsystem R/F/L/P remain deferred.

## Phase N Scope Brought Forward

Completed early during the reconciliation gate:

- first Architecture-to-Requirements Reconciliation
- accepted System Requirement update
- accepted System Function modeling
- accepted System Logical Architecture modeling
- initial feature and requirement coverage baseline

Retained in Phase N:

- shadow-model migration
- final reconciliation after Phases G–L
- removal of duplicated maintained model authority
- final CATIA synchronization
- confirmation of CATIA-only maintained model authority

## Exit Criteria

- prototype presentation completed
- every relevant Phase F/P capability inventoried
- CATIA coverage or explicit gap established
- accepted CATIA updates applied
- Feature and Requirement Coverage Matrix complete
- next implementation phase selected

## Status

Completed on 2026-07-31

Depends on:

Phase P — Satisfied

---

# Phase G — Approved Input Promotion

## Objective

Create the authoritative bridge from reviewed processing evidence to Approved
Input.

Phase G defines how eligible P4 and P9 evidence becomes approved engineering
input through exact Human Review Decisions.

## Architecture Decision

`collaboration/decisions/ADR-016-human-review-workspace-and-approved-input-promotion-architecture.md`

Status:

Accepted

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

## G4 Breakdown

| Step | Deliverable | Status |
|---|---|---|
| G4.1 | Finalization validation and Human Review authorization | Completed |
| G4.2a | Immutable `reviewed_document.json` contract | Completed |
| G4.2b | Immutable `effective_decisions.json` contract | Completed |
| G4.2c | Deterministic `reviewed_report.md` renderer | Completed |
| G4.2d | Cross-artifact consistency and fingerprint binding | Completed |
| G4.2e | Atomic persistence under `finalized/` | Completed |
| G4.2f | Load, scan and recovery | Completed |
| G4.3 | Reopening finalized Review Versions | Completed |
| G4.4 | Integration and complete regression | Completed |

## Verified Implementation

### G2

Commit:

`c61841789ed08b383e4cfc244d31f559125e6edb`

Verification:

```text
Focused G2 suite: 398 passed
Complete automated suite: 4206 passed
```

### G3

Commit:

`53bf6046b931af7c7b5189cd78822fd7cf7d51ef`

Implemented:

- eligible P4/P9 evidence selection
- structured proposal and evidence references
- stable Review Item construction
- deterministic Review Document assembly
- element, relationship and open-question separation
- exact source, run, attempt and artifact traceability

### G4.1

Commit:

`4cedfb10f81e08a3bbea7cdb2fee5d9a1235ddd5`

Implemented:

- finalization eligibility assessment
- exact revision and validation binding
- Human Review finalization authorization
- stale-decision rejection
- atomic finalized-version transition

Verification:

```text
Focused G4.1 suite: 314 passed
Complete automated suite: 4402 passed
```

### G4.2a–G4.2c

Commit:

`782b75a94f7008de9b08fc9724480f0786e6af01`

Implemented:

- immutable Finalized Reviewed Document manifest
- immutable Effective Review Decision Set
- deterministic Reviewed Report renderer
- exact decision, revision and validation binding
- deterministic serialization and fingerprints
- public package APIs

Verification:

```text
Focused G4.2a–G4.2c suite: 208 passed
Complete automated suite: 4463 passed
```

### G4.2d

Committed checkpoint:

`cf3cd5f`

Implemented:

- one exact immutable finalized artifact-set contract
- exact three-artifact membership
- cross-artifact identity, revision, decision and validation binding
- deterministic artifact ordering
- artifact-set fingerprinting
- rejection of mixed, incomplete or tampered sets

### G4.2e–G4.2f

Included in the G4 completion commit containing this SSOT update.

Implemented:

- exact-byte persistence under `finalized/`
- temporary `.finalized.tmp` staging
- write, flush, validation and atomic publication
- immutable finalized-directory protection
- strict finalized artifact-set loading
- scan diagnostics for interrupted, unsafe, incomplete or invalid states
- fail-closed recovery boundary

### G4.3

Included in the G4 completion commit containing this SSOT update.

Implemented:

- reopening only through a new successor Review Version
- linear Review Version history without branching
- exact predecessor finalization and artifact-set validation
- new Version, Revision and Review Item identities
- `carried_forward` one-to-one Review Item lineage
- preservation of materialized review state
- no copying of Scoped Review Actions
- atomic successor Draft creation

Verification:

```text
Focused G4.3 suite: 18 passed
Extended Review Workspace regression: 365 passed
```

### G4.4

Included in the G4 completion commit containing this SSOT update.

Verified lifecycle:

```text
finalize
→ persist exact finalized artifact set
→ reopen
→ append successor revision
→ authorize and finalize successor
→ persist second independent artifact set
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

## Immediate Next Activity

```text
G5 — Approved Input promotion and lifecycle
```

G5 shall define and implement the exact promotion boundary from a valid
finalized Review Version and its immutable artifact set to Approved Input.

## Remaining Deliverables

- Approved Input identity and manifest
- Approved Input repository and stable read contract
- promotion eligibility
- promotion service
- invalidation, revocation and supersession
- stable Phase H read contract
- focused Review and promotion UI
- complete end-to-end integration and manual acceptance

## Mandatory Boundaries

- unreviewed artifacts cannot become Approved Input
- P4-only evidence cannot create a Review Document
- consensus cannot authorize promotion
- confidence cannot authorize promotion
- stale decisions cannot authorize changed targets
- fingerprint mismatch blocks finalization and promotion
- original processing evidence remains immutable
- finalized artifacts must remain mutually consistent
- reopening never mutates a finalized predecessor
- Phase G shall not generate model candidates
- Phase G shall not generate SysML v2

---

# Cross-phase Model Element Change Candidate Discipline

## Objective

Prevent Phase N from having to reverse-engineer all engineering and architecture
concepts that emerged during implementation.

## Retrospective Scope

The first inventory shall examine all completed Phase-G work from G1 through
G4.2c.

It shall identify newly introduced or materially refined:

- requirements
- constraints
- functions
- Logical Components
- logical relationships and allocations
- possible subsystem boundaries
- Subsystem Requirements
- Subsystem Functions
- Subsystem Logical or Physical Architecture elements

## Ongoing Scope

Beginning with G4.2d, each implementation phase shall continuously record Model
Element Change Candidates.

Each phase-completion review shall explicitly determine whether implementation
created or materially refined engineering model content.

## G4 Recorded Candidates

| ID | Origin | Candidate | Proposed model element type | Status |
|---|---|---|---|---|
| MEC-G4-001 | G4.2d | Exact Finalized Artifact Set as a three-artifact boundary | System Design Constraint | Recorded; engineering review pending |
| MEC-G4-002 | G4.2e–G4.2f | Atomic publication and explicit recovery boundary | System Design Constraint | Recorded; engineering review pending |
| MEC-G4-003 | G4.3 | `carried_forward` lineage between predecessor and successor Review Items | Logical Relationship | Recorded; engineering review pending |
| MEC-G4-004 | G4.3 | Linear Review Version succession without parallel branches | System Design Constraint | Recorded; engineering review pending |

These candidates are implementation observations only.

They do not change CATIA until engineering review, explicit acceptance and a
separate CATIA model update have occurred.

## Authority Boundary

A candidate is not an accepted CATIA model change.

The sequence remains:

```text
Implementation observation
→ Model Element Change Candidate
→ engineering review
→ explicit acceptance
→ CATIA model update
```

The candidate inventory becomes a formal input to the
Zwischenstandspräsentation and Phase N.

---

# Zwischenstandspräsentation

## Position

After Phase G and before Phase H.

## Objective

Present the complete implemented workflow through Approved Input to the
supervising professor and establish a reviewed transition into model-candidate
generation.

## Deliverables

- presentation of completed phases and decisions
- executable demonstration through Approved Input
- current test and traceability evidence
- current CATIA architecture coverage
- retrospective Phase-G Model Element Change Candidate inventory
- open risks, limits and technical debt
- planned Phases H through L
- documented professor feedback

## Exit Criteria

- presentation performed
- feedback documented
- architecture and roadmap effects evaluated
- required decisions recorded
- retrospective candidate inventory reviewed
- SSOT synchronized before Phase H

Status:

Planned after Phase G

---

# Phase H — Model Candidate Layer

## Objective

Generate traceable model-element and relationship candidates from Approved
Input without generating SysML v2 code.

## Deliverables

- candidate model elements
- candidate attributes and metadata
- candidate relationships
- relationship source and target references
- canonical relationship semantics
- relationship priority
- prioritization rationale
- comparability impact
- structural-profile reference
- structural-profile conformance assessment
- alternative relationship candidates where meaning is ambiguous
- Human Review workflow for candidate selection
- persisted candidate and review evidence

## Relationship Prioritization and Comparability

Phase H shall explicitly address relationships whose intended meanings are
often used inconsistently, interchangeably or near-synonymously.

Relevant concepts include:

- dependency
- allocation
- flow
- refinement-related relationships
- derivation-related relationships
- framework-specific relationship concepts

The system shall not select a relationship only because it appears plausible.

The system shall also assess whether the selection supports a consistent model
structure across:

- related products
- product variants
- independently generated models
- repeated generation runs

A versioned Model Structure and Comparability Profile shall define:

- preferred element structure
- canonical relationship choices
- required comparison anchors
- allowed structural variation
- prioritization criteria
- permitted exceptions
- review requirements for deviations

Automated prioritization remains advisory.

Human Review shall authorize accepted relationship candidates and exceptions.

## Exit Criteria

- model-element candidates can be generated from Approved Input
- relationship candidates are explicit and traceable
- competing relationship semantics remain visible
- relationship priorities and rationales are persisted
- comparability-profile conformance is assessable
- Human Review selects or rejects candidates
- no SysML v2 code is generated
- automated tests pass

## Status

Planned

Depends on:

Phase G

---

# Phase I — Model Generation Agent

## Objective

Create an internal engineering model from reviewed model candidates.

## Deliverables

- Model Generation Agent
- internal model representation
- model-element assembly
- relationship assembly
- structural-profile application
- accepted exception handling
- source and Approved Input traceability
- candidate and Human Review traceability
- deterministic model serialization contract

## Exit Criteria

- reviewed candidates are assembled into an internal model
- selected relationship semantics are preserved
- structural consistency checks pass
- complete traceability remains available
- no SysML v2 serialization occurs before Phase J
- automated tests pass

## Status

Planned

Depends on:

Phase H

---

# Phase J — SysML v2 Code Generator

## Objective

Generate valid SysML v2 textual notation from the internal engineering model.

## Deliverables

- SysML v2 code generator
- versioned target-notation profile
- versioned target-artifact structure
- stable identifier and naming rules
- SYSIDE-compatible textual output
- CATIA-compatible textual output where supported
- generation diagnostics
- source-to-output traceability references

## Exit Criteria

- the internal model can be serialized as SysML v2 text
- generated notation conforms to the selected profile
- generated artifact structure conforms to the selected target structure
- output remains traceable to the internal model and Approved Input
- automated tests pass

## Status

Planned

Depends on:

Phase I

---

# Phase K — Validation Layer

## Objective

Validate generated engineering models before publication and export.

## Deliverables

- syntax validation
- target-notation validation
- target-artifact structure validation
- structural validation
- relationship consistency validation
- relationship semantic validation
- constraint validation
- traceability validation
- comparability-profile validation
- larger-context compatibility checks where available
- deterministic validation report
- fail-closed publication gate

## Exit Criteria

- invalid models are detected automatically
- validation findings are traceable to model elements and generation evidence
- relationship conflicts and semantic inconsistencies are reported
- comparability-profile deviations are reported
- failed validation blocks publication
- automated tests pass

## Status

Planned

Depends on:

Phase J

---

# Phase L — Output Writer

## Objective

Publish validated engineering artifacts as a complete versioned output package.

## Deliverables

- SysML v2 output files
- versioned output directory
- validation report
- generation summary
- traceability package
- export metadata
- artifact fingerprints
- immutable published output references
- downloadable or inspectable output package

## Exit Criteria

- a complete versioned output package is generated automatically
- only validated output can be published
- every output file is fingerprinted
- every output remains traceable to Project, Source, Approved Input and decisions
- the package can be inspected through the application
- automated tests and end-to-end manual acceptance pass

## Status

Planned

Depends on:

Phase K

---

# Phase N — CATIA Shadow-model Migration and Final Reconciliation

## Objective

Replace the temporary SYSIDE shadow model with the authoritative CATIA Magic
model and perform final whole-system reconciliation after the executable
prototype is complete.

## Work Package N1 — Shadow-model Migration

Deliverables:

- migration of remaining shadow-model information
- synchronization with CATIA
- updated model registry
- removal of duplicated maintained model authority

## Work Package N2 — Final Architecture-to-Requirements Reconciliation

The first reconciliation pass was completed during the Post-Phase-P
Reconciliation Gate.

Phase N performs the final reconciliation for capabilities and architecture
decisions introduced or changed during Phases G–L.

Deliverables:

- final architecture-decision inventory
- final capability-to-requirement mapping
- final Requirement Coverage Matrix
- resolution or explicit deferral of remaining gaps
- traceability from CATIA elements to decisions and implementation evidence
- confirmation that CATIA is the only maintained engineering model

## Exit Criteria

- CATIA Magic is the only maintained engineering model
- remaining shadow-model content is migrated or explicitly retired
- every accepted architecture decision is mapped to model coverage
- remaining requirement gaps are resolved or explicitly deferred
- final CATIA synchronization is complete

## Status

Planned after Phase L

Depends on:

Phase L and project-owner decision

---

# Phase Q — Thesis Architecture Documentation

## Objective

Document the final architecture, development rationale and evaluation evidence
for the thesis.

## Deliverables

- development-phase documentation
- architecture-decision inventory
- decision context and alternatives
- rationale and consequences
- requirement and implementation traceability
- semantic and ontology architecture
- Human Review architecture
- processing and evidence architecture
- model-candidate and relationship-prioritization architecture
- model-comparability approach
- SysML v2 generation and validation architecture
- limitations and deferred work
- literature and standard references
- thesis-only Development Plan

## Exit Criteria

- every accepted architecture decision is documented
- the final system architecture matches the authoritative CATIA model
- implementation evidence is traceable to architecture and requirements
- evaluation results are included
- limitations and deferred scope are explicit

## Status

Planned after Phase N

Depends on:

Phase N and project-owner decision

---

# Phase R — Task Profile Portability Evaluation

## Objective

Evaluate the thesis that the reusable Turing Generator core can be adapted
quickly to a different engineering task by replacing a bounded set of
task-specific artifacts.

## Reusable Core Candidate

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

## Task-specific Artifact Candidate Set

The evaluation shall inspect at least:

- `context/project/*.json`
- `context/frameworks/*.json`
- `context/semantics/*.json`
- `agents/*.md`
- `recipes/**/*.recipe.md`
- `tasks/*.md`
- validation rules
- output contracts
- review criteria

## Required Deliverable

A Task Profile Replacement Manifest shall record:

- artifact path
- artifact role
- core or task-specific classification
- unchanged, adapted or replaced status
- dependencies
- required validation
- required code changes
- reused tests
- new tests

## Alternate Test Task

Requirements Quality and Completeness Analysis.

The alternate task shall assess:

- requirement formulation against an explicitly selected standard or rule set
- requirement completeness
- requirement atomicity
- ambiguity
- contradictions between requirements
- missing information
- proposed corrections
- proposed additions
- Human Review of proposed changes

## Evaluation Measures

- number of changed files
- share of unchanged core modules
- implementation time
- reused tests
- new validation rules
- required code changes
- achieved functional coverage
- limitations of the reuse claim

## Exit Criteria

- the alternate task runs through the reusable core
- the replacement manifest is complete
- required changes are measured
- reused and task-specific parts are distinguishable
- the portability thesis is supported, limited or rejected using evidence

## Status

Planned after Phase Q

Depends on:

Phase Q and project-owner decision

---

# Phase S — Project Affinity Recommendation

## Priority

Low.

This phase is intentionally scheduled after Phase R.

## Objective

Recommend existing Projects that may fit newly selected data before the Source
is persistently registered.

## Deliverables

- temporary pre-registration content analysis
- Project Affinity Candidate
- ranked project recommendations
- recommendation rationale
- confidence or evidence summary
- explicit user confirmation or override
- no automatic persistence before selection

## Recommendation Inputs

The recommendation may consider:

- project description
- framework template
- existing Sources
- accepted project vocabulary
- framework coverage
- semantic similarity

## Mandatory Boundaries

- recommendation remains advisory
- the system shall not assign a Project automatically
- the user confirms or overrides the recommendation
- persistent Source registration occurs only after Project selection
- no permanent unassigned Source pool is introduced
- every persisted Source remains assigned to exactly one Project

## Exit Criteria

- recommendations are generated without persistent registration
- ranked rationale is visible
- user confirmation controls assignment
- existing Project and Source authority rules remain unchanged
- automated tests pass

## Status

Planned after Phase R — Low Priority

Depends on:

Phase R and project-owner decision

---

# Cross-phase Rules

## Authority

- CATIA is authoritative for engineering knowledge
- the committed repository is authoritative for implementation reality
- the Collaboration Knowledge Base is authoritative for roadmap and accepted decisions
- temporary artifacts and chat history are non-authoritative

## Human Review

- candidates remain non-authoritative until Human Review
- consensus, confidence and low variance cannot authorize publication
- stale decisions cannot pass a gate
- exact target-content and validation fingerprints control approval

## Traceability

Every generated engineering artifact shall remain traceable to:

- Project
- Source
- source location
- Source Projection
- Processing Run
- processing artifacts
- candidate or Approved Input
- applicable profile and validation
- Human Review Decision where required

## Determinism

Deterministic implementations shall be preferred for:

- identifiers
- persistence
- hashing
- validation
- report generation
- artifact serialization
- state reconstruction
- context selection
- output packaging

## Prototype Schedule

The 2026-08-14 target is binding for the executable prototype.

Scope shall be reduced through non-critical refinements before weakening:

- traceability
- validation
- Human Review
- project isolation
- publication gates
- model consistency

---

# Immediate Next Step

Begin Phase G architecture discussion.

Execution sequence:

```text
Phase G architecture questions
→ explicit project-owner acceptance
→ Phase G ADR
→ implementation
→ tests
→ manual review
→ completion decision
```

No Phase H implementation begins before Phase G exposes a stable Approved Input
contract.
