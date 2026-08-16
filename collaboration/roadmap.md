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

1.13

Knowledge Base Version

1.20

Implementation Version

0.22

Roadmap Version

1.20

Last SSOT Update

2026-08-16

Current Phase

**WP-12 — End-to-End Demo Hardening**

Current Status

WP-11 Architecture / Model Proposal UX is completed and verified. WP-12
End-to-End Demo Hardening is active. The multi-document synthetic Stage-A test
specification and fixtures are prepared and accepted; formal execution is pending
for 2026-08-17. Stage B with representative non-synthetic test data remains gated
by an explicit successful Stage-A release decision. Live real-SYSIDE publication
acceptance remains blocked because the verification workstation has no SYSIDE CLI;
this remains fail-closed and does not weaken the implemented release path.

Verified Implementation Reference

`commit containing this SSOT update` — WP-11 Architecture / Model Proposal UX completion

Last Prior Committed Checkpoint

`63b911dbf5da9b4a2be7013553fd8d47f4e30db4` — WP-10 final formatting checkpoint

Verified Automated Test Baseline

5577 passed, 1 skipped in 14.19s in the complete repository regression after WP-11.

WP-11 Focused Regression

40 passed in 0.52s.

WP-09 Focused Regression

111 passed in 0.63s.

Phase-L Focused Regression

147 passed, 1 skipped in 1.63s.

Phase-K Focused Regression

65 passed in 1.41s.

Phase-G Focused Completion Regression

65 passed in 8.95s.

Phase-G Manual Acceptance

PASS

Closed Vertical-slice Target

2026-08-14

Functional Freeze

2026-08-17

Product Demo

2026-08-18

---

# End-to-End Prototype Critical Path

The accepted executable prototype path remains:

```text
Source
→ Processing Run
→ Human Review
→ Approved Input
→ Model Candidates
→ Internal Engineering Model
→ SysML v2 Generation
→ Validation
→ Final Model Human Review
→ Human Release Approval
→ Versioned Output Package
```

Phases G, H, I, J, K, L, WP-09, WP-10 and WP-11 are complete. The controlled
H9 extension is also complete. The automated technical vertical slice reaches
immutable published output and the engineer-facing global workflow shell is now
operational. Live real-SYSIDE acceptance remains blocked only by the missing CLI.

The remaining demo hardening sequence is:

```text
WP-09 Guided Workflow UI                     COMPLETE
→ WP-10 Ingestion + Human Review UX Simplification COMPLETE
→ WP-11 Architecture / Model Proposal UX          COMPLETE
→ WP-12 End-to-End Demo Hardening                  ACTIVE
   Stage-A specification / fixtures                ACCEPTED + PREPARED
   formal Stage-A execution                        PENDING
→ WP-13 Functional Freeze + Rehearsal
→ WP-14 CATIA / SSOT Checkpoint
→ Product Demo 2026-08-18
```

The Zwischenstandspräsentation no longer blocks Phase H. It is prepared after
implementation so it can show the completed architecture and evidence.

Target dates:

```text
2026-08-14  H–L closed vertical slice
2026-08-16  WP-09→WP-11 complete; WP-12 Stage-A test prepared and accepted
2026-08-17  WP-12 formal dry run + WP-13 rehearsal/freeze + WP-14 CATIA/SSOT
2026-08-18  Product demo
```

Quality shall not be reduced to save time. Time is saved through decomposition,
focused verification and deferral of non-critical refinements rather than by
weakening authority, validation or traceability.

---

# WP-09 — Guided Workflow UI

## Objective

Expose the already implemented engineering authority chain through one
engineer-centered, deterministic Guided Engineering Workflow without introducing
a second workflow state machine or weakening traceability.

## Architecture

`collaboration/decisions/ADR-024-guided-engineering-workflow-and-ux-projection-architecture.md`

## Completed Deliverables

- Guided Workflow presentation and read models
- Engineer Home with `Your work` and `Next action`
- global Project selector and constrained Project creation
- global Focused / Technical presentation depth
- common navigation across seven engineering workspaces
- Model Proposal detail workspace
- Final Model Review detail workspace
- Published Output detail workspace
- explicit Candidate Review writes
- immutable Final Review Change Proposal submission
- explicit Human release approval
- exact FRV-to-Output publication bridge
- fail-closed write delegation to existing domain authority services
- read-side reconstruction after every persisted write
- deferred Human Review retained as unresolved work
- primary application entry point clarified as `app/turing_generator_app.py`

## Verification

```text
Focused WP-09 regression:
111 passed in 0.63s

Complete repository regression:
5542 passed, 1 skipped in 13.36s

git diff --check:
PASS
```

Manual smoke acceptance verified the common shell, Project selection, Technical
toggle, all seven workspaces, navigation and empty states.

Live Candidate / Final Review / Publication actions with a fully populated Project
are deferred to the prepared end-to-end demo Project in WP-12. Automated tests
cover the exact write paths.

## Status

Completed on 2026-08-16

---

# WP-10 — Ingestion + Human Review UX Simplification

## Objective

Apply the accepted Guided Engineering Workflow principles to the Processing and
Human Review surfaces while preserving all existing Processing and Human
authority contracts.

## Completed Deliverables

- UX-16 Processing and Human Review projection contract in ADR-024
- deterministic Processing presentation model
- deterministic Human Review queue / item / Persona / variance presentation
- filename-first Source inventory and Processing interaction
- Focused / Technical Processing projection
- direct Processing → Human Review next action
- engineering-content-first Human Review Queue and Review Item presentation
- Persona grouping and side-by-side comparison
- consensus / variance display without invented agreement
- one-Persona agreement guard
- progressive disclosure of evidence, scoped actions, split / merge and
  technical traceability
- clearer Finalization / Human confirmation lifecycle
- clearer Approved Input Promotion and active-authority presentation
- immutable Reopen-as-successor interaction retained
- single Session State authority for the top-level Workspace widget

## Verification

```text
Complete repository regression:
5563 passed, 1 skipped in 13.91s

Final targeted shell / Human Review regression:
43 passed in 0.53s

git diff --check:
PASS
```

Manual live acceptance covered Focused Processing, a live LLM Processing result,
direct Human Review continuation, Human Review Queue / Review Items and
Finalization state.

The available acceptance fixture exposed one Persona for the inspected Review
Items. Multi-Persona visual acceptance remains part of the populated WP-12 demo
project; automated tests already cover Persona grouping and side-by-side layout.

## Status

Completed on 2026-08-16

---

# WP-11 — Architecture / Model Proposal UX

## Objective

Refine Model Proposal and Architecture interaction so that the engineer can
understand proposed model structure, alternatives, variance, review state and
next action without weakening Candidate, Approved Input or Internal Engineering
Model authority.

## Architecture

`collaboration/decisions/ADR-024-guided-engineering-workflow-and-ux-projection-architecture.md`

UX-17 defines the Model Proposal projection contract.

## Completed Deliverables

- deterministic immutable Model Proposal presentation projection
- architecture-first Model Proposal workspace
- model-area grouping of proposed elements
- readable proposed relationship structure
- Relationship Choice Groups shown as explicit alternatives
- preferred / accepted relationship alternatives retained from persisted state
- structural / profile deviation and comparability presentation
- Candidate Review progress and authoritative Phase-I readiness projection
- decision-first Candidate Review workspace
- exact Candidate Set / Candidate write binding
- Focused / Technical dual-layer presentation
- progressive technical traceability to Approved Input and Candidate identity
- ready Candidate Set presentation without redundant write controls

## Verification

```text
WP-11 focused regression:
40 passed in 0.52s

Complete repository regression:
5577 passed, 1 skipped in 14.19s

git diff --check:
PASS
```

A populated live Model Proposal test is intentionally deferred to WP-12 because
no representative Model Candidate data exists yet. WP-12 will execute the real
demo Project through Model Proposal and Candidate Review and use that connected
run as a formative task-based self-evaluation.

## Status

Completed on 2026-08-16

---

# WP-12 — End-to-End Demo Hardening

## Objective

Exercise one representative Project through the complete implemented workflow,
identify and correct demo-critical integration / usability defects, and retain a
reproducible demonstrator state for the product demo.

The target path is:

```text
Source
→ Processing
→ Human Review
→ Approved Input
→ Model Candidates
→ Candidate Human Review
→ Internal Engineering Model
→ SysML v2 Generation
→ Validation
→ Final Model Human Review
→ Human Release Approval
→ Versioned Output Package
```

WP-12 also performs a formative task-based self-evaluation of the connected
demonstrator. The evaluation records concrete workflow observations, their
engineering / usability impact and any bounded resolution. It is qualitative
design evidence and shall not be represented as an independent quantitative
usability study.

## Status

Active

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

Create the authoritative bridge from reviewed Processing evidence to Approved
Input and expose that authority through a safe Human Review and promotion
workflow.

## Architecture Decisions

- `collaboration/decisions/ADR-016-human-review-workspace-and-approved-input-promotion-architecture.md`
- `collaboration/decisions/ADR-017-simple-by-default-interaction-and-progressive-disclosure.md`

Status:

Accepted

## Work Breakdown

| Step | Deliverable | Status |
|---|---|---|
| G1 | Human Review Workspace and Approved Input architecture | Completed |
| G2 | Review Workspace foundations | Completed |
| G3 | P4/P9 evidence adapters and Review Item construction | Completed |
| G4 | Review editing, finalization and reopening | Completed |
| G5 | Approved Input promotion and lifecycle | Completed |
| G6 | Human Review and promotion UI | Completed |
| G7 | Integration, audit, manual acceptance and end-to-end regression | Completed |

## Completion Evidence

G5 checkpoint:

```text
865cbab24dfb5bb1f5150ff9336a55d00299a035
```

G6 checkpoint:

```text
7209f17a610d3adb359e8b672a28020b71c03333
```

G6 verification:

```text
Focused regression: 145 passed
git diff --check: PASS
```

G7.3 manual acceptance:

```text
PASS
```

Evidence:

- `collaboration/audits/phase_g_manual_acceptance_test_report.md`
- `collaboration/audits/phase_g_manual_acceptance_findings.md`

The acceptance verified:

- exact Human Review authority
- immutable revision behavior
- fail-closed unresolved relationships
- exact finalization and three-artifact publication
- Approved Input promotion and AIN traceability
- reopen successor lifecycle and byte-identical predecessor preservation
- Scoped Action + Impact Preview
- safe running-state Agentic Ingestion write behavior

G7.4 verification:

```text
Focused Phase-G completion regression:
65 passed in 8.95s

Complete repository regression:
4818 passed in 24.50s

git diff --check:
PASS
```

## Stable Phase-H Boundary

```python
ApprovedInputRepository.list_active_approved_inputs(
    project_id,
) -> tuple[ApprovedInputManifest, ...]
```

Phase H receives only currently active Approved Inputs.

## Phase-G Exit Criteria

- architecture accepted
- Review Workspace implemented
- finalization implemented
- Approved Input promotion implemented
- lifecycle implemented
- Human Review / Promotion UI implemented
- manual acceptance passed
- final focused regression passed
- complete repository regression passed
- SSOT synchronized

## Status

Completed on 2026-08-12

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
| MEC-G5-001 | G5.6 | Approved Input authority derived from immutable manifest plus append-only lifecycle events | System Design Constraint | Recorded; engineering review pending |
| MEC-G5-002 | G5.6 | Promotion Equivalence retains materially unchanged accepted subjects across successor Review Versions | System Design Constraint | Recorded; engineering review pending |
| MEC-G5-003 | G5.7 | Phase H consumes only active Approved Inputs through the stable repository read contract | System Design Constraint | Recorded; engineering review pending |

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

Planned after implementation; no longer a blocking gate before Phase H.

## Objective

Present the completed implementation and literature-derived architecture to the
supervising professor, then capture feedback for final CATIA and thesis
reconciliation.

## Deliverables

- completed phases and architecture decisions
- executable end-to-end workflow
- automated and manual verification evidence
- traceability and authority chain
- CATIA architecture coverage
- Model Element Change Candidate inventory
- Data / Process / Knowledge layer framing
- mapping to the eight Logical Components
- high-level activity view with approximately 7±2 primary activities
- open risks, limitations and technical debt
- artifact-driven architectural adaptability outlook

## Exit Criteria

- presentation prepared after implementation
- feedback documented
- architecture effects evaluated
- roadmap effects evaluated
- required decisions recorded
- CATIA / SSOT effects reconciled as appropriate

Status:

Planned after implementation

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

## Implementation Verification

Architecture:

`collaboration/decisions/ADR-018-model-candidate-layer-and-structural-comparability.md`

Completed implementation slices:

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

Verification:

```text
Focused H1–H8 regression:
168 passed in 1.63s

Complete repository regression:
4986 passed in 25.80s

git diff --check:
PASS
```

Technical Phase-H output includes persisted Model Candidate Sets, explicit
Element and Relationship Candidates, structural-comparability evidence,
Candidate Human Review, the validated Phase-I read boundary and a deterministic
non-authoritative Model Proposal projection.

The polished Architecture / Model Proposal UX remains WP-11.

## Status

Completed

Depends on:

Phase G — Satisfied

---

# Phase H9 — Hybrid Target Projection Extension

## Objective

Extend the completed Phase-H Candidate Layer so heterogeneous Approved Inputs
are not silently lost or forced into the selected Framework when deterministic
profile projection is ambiguous or unsupported.

## Architecture Decision

`collaboration/decisions/ADR-020-hybrid-target-projection-and-coverage-architecture.md`

## Work Breakdown

| Step | Deliverable | Status |
|---|---|---|
| H9.1 | Projection disposition and complete coverage model | Completed |
| H9.2 | Shared deterministic profile resolver | Completed |
| H9.3 | Strict deterministic deriver migrated to resolver | Completed |
| H9.4 | Structured LLM projection contract | Completed |
| H9.5 | Bounded unresolved-only LLM executor | Completed |
| H9.6 | Hybrid Model Candidate Deriver | Completed |
| H9.7 | Generation provenance and H→I integration regression | Completed |
| H9.8 | SSOT closeout and Phase-N2 reconciliation candidate recording | Completed |

## Verified Behavior

- deterministic projection remains the quick / reproducible path
- every active Approved Input receives an explicit projection disposition
- no silent omission is permitted
- only `ambiguous` / `unmapped` cases may reach the LLM
- requests use compact Approved-Input and profile context
- LLM output is structured Candidate-level modeling, never SysML v2 text
- only profile-offered target rules are accepted
- `unmapped` remains an allowed result; no forced mapping
- Human Review and the H→I authority boundary remain unchanged
- LLM usage and semantic request/response provenance remain traceable
- Phase J remains deterministic serialization

## Verification

```text
Focused H9 regression:
61 passed in 0.69s

Complete repository regression:
5120 passed in 13.12s

git diff --check:
PASS

Bounded live LLM smoke:
PASS
calls: 1
retries: 0
model: gpt-5-mini
total_tokens: 1345
```

## Phase-N2 Reconciliation Candidates

H9 records these capabilities for final CATIA reconciliation in N2 without
creating preliminary SYSR/SF elements now:

1. selectable deterministic and LLM-assisted target projection
2. complete projection-coverage assessment with explicit unresolved states
3. deterministic-first unresolved-only AI routing
4. profile-controlled AI proposal validation and no-forced-fit behavior
5. AI projection provenance with unchanged Human Review authority

Exact CATIA model elements and wording are determined only during N2.

## Status

Completed on 2026-08-13

Depends on:

Phase H — Satisfied

---

# Phase I — Model Generation Agent / Internal Engineering Model

## Objective

Create an immutable, deterministic Internal Engineering Model from the exact
reviewed model-candidate selection authorized by Phase H.

## Architecture Decision

`collaboration/decisions/ADR-019-internal-engineering-model-assembly-architecture.md`

Accepted architecture checkpoint:

`ff4ee4e038942f9ee267eb2ad6a6daa600b09e6d`

## Completed Implementation Slices

```text
I1  IDs + immutable Internal Model domain types
I2  manifests + fingerprints + H→I contract enrichment
I3  Framework/Profile resolution + structure materialization
I4  deterministic MCE/MCR → IME/IMR assembly
I5  repository + immutable persistence + bundle integrity
I6  explicit Phase-J read contract + regression
```

## Implemented Deliverables

- deterministic Internal Model assembly service
- immutable `IEM`, `IME` and `IMR` identities and manifests
- exact H→I authority fingerprint
- pinned Framework Template, Model Structure Profile, derivation rules and
  assembly rules
- complete configured framework hierarchy materialization
- deterministic model-element assembly
- deterministic relationship assembly with exact IME endpoint rebinding
- preserved relationship family, semantic intent and directionality
- accepted-exception preservation
- source / Approved Input traceability
- Model Candidate and Human Review traceability
- immutable project-local IEM repository
- atomic publication and recovery diagnostics
- project-wide IEM/IME/IMR no-reuse checks
- exact reassembly idempotence
- complete bundle-integrity validation
- explicit Phase-J read boundary:
  `InternalModelReadService.load_phase_j_input(...)`
- representation-neutral Internal Engineering Model; no SysML v2 text

## Verification

```text
Focused I1–I6 regression:
110 passed in 1.07s

Complete repository regression:
5087 passed in 26.00s

git diff --check:
PASS
```

## Exit Criteria

- reviewed candidates are assembled into an internal model — satisfied
- selected relationship semantics are preserved — satisfied
- structural consistency checks pass — satisfied
- complete traceability remains available — satisfied
- no SysML v2 serialization occurs before Phase J — satisfied
- automated tests pass — satisfied
- SSOT synchronized — satisfied by the Phase-I completion commit

## Status

Completed on 2026-08-13

Depends on:

Phase H — Satisfied

---

# Phase J — SysML v2 Code Generator

## Objective

Generate deterministic SYSIDE-compatible SysML v2 textual notation from one
explicitly selected, validated Internal Engineering Model snapshot.

## Architecture Decision

`collaboration/decisions/ADR-021-syside-compatible-sysml-v2-generation-architecture.md`

Accepted architecture checkpoint:

`af6953486a71c3073c0169ef5052dbcabb49c4fc`

## Completed Work Breakdown

| Step | Deliverable | Status |
|---|---|---|
| J1 | Generation foundation, Target Notation 0.2.0 and SYSIDE syntax evidence | Completed |
| J2 | Generation Profile, Artifact Structure Profile and preflight | Completed |
| J3 | Package, symbol, safe-text and canonical-order projection | Completed |
| J4 | Deterministic element renderer | Completed |
| J5 | Deterministic relationship renderer and endpoint-role integration | Completed |
| J6 | Artifact set, traceability, fingerprints and idempotence | Completed |
| J7 | Explicit service boundary, regression and SSOT closeout | Completed |

## Implemented Deliverables

- explicit I→J authority boundary through `InternalModelReadService`
- deterministic `SysMLGenerationService`
- versioned Target Notation 0.2.0
- versioned Generation Profile 1.0.0
- versioned Artifact Structure Profile 1.0.0
- versioned Generator Rules 1.0.0
- deterministic generation preflight
- Framework hierarchy → package projection
- stable generated technical symbols
- requirement, use-case, action-usage and part-usage rendering
- dependency, allocation and satisfaction rendering
- exact relationship endpoint-role/construct checks
- fail-closed unsupported semantic handling
- deterministic canonical formatting
- immutable `GeneratedSysMLArtifactSet`
- machine-readable IME/IMR → Candidate → Approved Input → Review traceability
- exact generated line locations
- generation-input, unit and artifact-set SHA-256 fingerprints
- deterministic idempotence
- explicit Phase-K handoff
- no Phase-L publication inside Phase J

## Verification

```text
Targeted Turing Core synchronization regression:
191 passed in 0.19s

Complete repository regression:
5239 passed in 13.77s

git diff --check:
PASS
```

## Phase-N2 Reconciliation Candidates

Record for final CATIA reconciliation without creating preliminary SYSR/SF
elements during Phase J:

1. deterministic SysML v2 generation from validated explicit IEM input
2. SYSIDE-compatible versioned target-notation generation
3. separate semantic mapping, artifact-structure and generator-rule policies
4. fail-closed unsupported semantics and endpoint compatibility
5. deterministic generated identity, fingerprints and idempotence
6. machine-readable generated-output traceability
7. explicit generation / validation / publication separation across J/K/L

Exact CATIA element types and wording are decided only in N2.

## Exit Criteria

- internal model can be serialized as SysML v2 text — satisfied
- notation conforms to selected generation policy — satisfied
- artifact structure conforms to selected target structure — satisfied
- output remains traceable to IEM and Approved Input — satisfied
- unsupported semantics fail closed — satisfied
- deterministic idempotence verified — satisfied
- automated tests pass — satisfied
- Phase-K boundary explicit — satisfied
- SSOT synchronized — satisfied by the Phase-J completion commit

## Status

Completed on 2026-08-13

Depends on:

Phase I — Satisfied

---

# Phase K — Validation Layer

## Objective

Validate the exact immutable `GeneratedSysMLArtifactSet` before publication
without regenerating, repairing or semantically reinterpreting the source model.

## Architecture Decision

`collaboration/decisions/ADR-022-sysml-v2-validation-layer-architecture.md`

Accepted architecture checkpoint:

`601b2134fcb227b114b4c50ad14d09ca920c81c5`

## Completed Work Breakdown

| Step | Deliverable | Status |
|---|---|---|
| K1 | Validation domain foundation + Validation Profile | Completed |
| K2 | Artifact/context/Target-Notation/Structure/Traceability validators | Completed |
| K3 | Relationship + endpoint consistency validator | Completed |
| K4 | SYSIDE CLI adapter + deterministic diagnostic normalization | Completed |
| K5 | Validation service + status/gate/fingerprint assembly | Completed |
| K6 | J→K→L boundary regression + hardening + closeout | Completed |

## Implemented Deliverables

- immutable deterministic validation result
- versioned Validation Profile 1.0.0
- exact generation-policy resolution
- standalone artifact-set integrity checks
- Target Notation and Artifact Structure validation
- relationship/endpoint target-model validation
- traceability and comparability-policy validation
- isolated non-mutating SYSIDE CLI adapter
- deterministic diagnostic normalization
- `valid` / `invalid` / `incomplete` status model
- fail-closed publication gate
- deterministic validation fingerprints
- exact fingerprint-bound K→L handoff contract

## Verification

```text
Focused K1–K6 regression:
65 passed in 1.41s

Complete repository regression:
5304 passed in 25.97s

git diff --check:
PASS

Verification workstation SYSIDE runtime:
unavailable
```

The missing CLI is treated as required-validator infrastructure unavailability:
`incomplete / blocked`, never as PASS and never as model invalidity. A live
external validation run remains required before Phase-L operational acceptance.

## Exit Criteria

- invalid generated artifacts are detected deterministically — satisfied
- findings remain traceable to generated symbols and evidence — satisfied
- relationship conflicts are reported — satisfied
- comparability/profile consistency is validated without Candidate reinterpretation — satisfied
- failed or incomplete validation blocks publication — satisfied
- automated tests pass — satisfied
- live external-validator availability on verification workstation — pending environment setup

## Status

Implementation completed on 2026-08-14.

Depends on:

Phase J — Satisfied

---

# Phase L — Final Model Review and Output Publication

## Objective

Provide an explicit Human-in-the-Loop release boundary over the actual generated
SysML v2 result and publish only the exact validated, Human-approved revision as
an immutable versioned project output.

## Architecture Decision

`collaboration/decisions/ADR-023-final-model-review-and-output-publication-architecture.md`

Accepted at:

`72974bb63c92c37baac5eef6b740ee91bacedd01`

## Work Breakdown

| Step | Deliverable | Status |
|---|---|---|
| L1 | Final Model Review domain foundation | Completed |
| L2 | project-local immutable Review Repository | Completed |
| L3 | Review read model / UI projection | Completed |
| L4 | Change Proposal + revision / agent-reproposal loop | Completed |
| L5 | Final Human release gate | Completed |
| L6 | Output Publication repository + OutputWriter | Completed |
| L7 | end-to-end integration and acceptance | Implementation completed; live SYSIDE acceptance blocked by environment |

## Implemented Deliverables

- persisted generated-but-not-approved `.sysml` as project-local review evidence
- immutable `FMR` / `FRV` / `FRI` / `FRD` review contracts
- exact code/model/validation/traceability/proposal review projection
- immutable Human Change Proposals and authority-aware routing
- optional bounded agent/LLM re-proposal without AI release authority
- exact fingerprint-bound Human release approval
- stale/superseded review rejection
- versioned `TURING_SYSML_V2_OUTPUT 1.0.0` Output Profile
- immutable project-local `OUT-xxxxxx` publication identities
- byte-identical SysML publication
- deterministic generation/validation/traceability package projections
- atomic fail-closed persistence, integrity scanning and recovery
- idempotent exact re-publication
- explicit read boundary for Guided Workflow UI

## Verification

```text
Focused L1–L7:
147 passed, 1 skipped in 1.63s

Complete repository:
5451 passed, 1 skipped in 26.84s

git diff --check:
PASS
```

The skip is the deliberate real-SYSIDE L7 acceptance test.

Runtime verification:

```text
SYSIDE CLI: unavailable
```

The automated vertical slice with a deterministic completed external-validator
test adapter passes from IEM through J, K, Final Model Review, explicit Human
release and `OUT-000001`.

A real SYSIDE-backed `valid / passed → Human approval → OUT-000001` run remains
pending environment setup and shall continue to fail closed until `syside` is
installed, licensed and executable.

## Exit Status

```text
Architecture: COMPLETE
Implementation: COMPLETE
Automated integration: COMPLETE
Live external-validator operational acceptance: BLOCKED — missing SYSIDE CLI
```

## Status

Implementation completed on 2026-08-14.

WP-09 Guided Workflow UI may proceed without weakening the unresolved live
SYSIDE acceptance prerequisite.

Depends on:

Phase K — Satisfied

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

The technical closed vertical slice is targeted for 2026-08-14.

The product-demo schedule is:

```text
2026-08-14  H–L closed vertical slice
2026-08-15  Guided Workflow UI
2026-08-16  End-to-End Demo Hardening
2026-08-17  Functional Freeze + Rehearsal
2026-08-18  Product Demo
```

Streamlit remains the prototype UI technology through the demo.

A frontend/backend technology rewrite is not part of this critical path.

Non-critical refinements may be deferred, but the following shall not be
weakened:

- traceability
- validation
- Human Review
- project isolation
- publication gates
- model consistency
- explicit artifact contracts

---

# Immediate Next Step

Begin Phase H architecture definition.

Execution sequence:

```text
inspect active Approved Input read contract
→ define Model Candidate identity and immutable contracts
→ define element and relationship candidate semantics
→ define relationship priority and comparability evidence
→ define Human Review / authority boundary
→ identify affected repository paths
→ review exact architecture contract
→ obtain explicit project-owner acceptance
→ implement incrementally
```

No Phase-H production implementation begins before explicit acceptance of the
architecture contract.
