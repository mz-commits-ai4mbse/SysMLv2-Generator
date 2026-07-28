# Roadmap

## Purpose

This roadmap defines the official development phases of the Turing Generator.

Each phase represents a major engineering milestone.

A phase is considered complete only after:

- implementation
- testing
- review
- SSOT UPDATE

have been successfully completed.

---

# Project Status

Architecture Version

1.1

Knowledge Base Version

1.5

Implementation Version

0.8

Roadmap Version

1.5

Last SSOT Update

2026-07-28

Current Phase

**Post-Phase-P Reconciliation Gate**

Current Status

Phase P Completed — Prototype Presentation and CATIA Reconciliation Next

Verified Implementation Commit

`26acace4d7ba2849b33c5e0dacedf838f83c7705`

Complete Automated Test Baseline

3808 passed

---

# Phase F – Agentic Ingestion UI

## Objective

Provide a functional user interface for the complete agentic ingestion workflow.

## Deliverables

- Legacy data upload
- Team configuration
- Dry Run
- LLM execution
- Memory-based pipeline
- Deterministic review report
- Improved engineering review report
- Artifact browser

## Exit Criteria

- complete ingestion workflow operational
- review report suitable for engineering review
- memory pipeline fully integrated
- stable demonstration UI

## Status

Completed

Verified in:

`adce9ec65ca3e36b89686b55d397a34dd382fdb1`

---

# Phase P – Project Workspace and Project-bound Ingestion

## Objective

Introduce project-oriented processing around the completed Phase F ingestion
pipeline.

Multiple individually ingested sources shall produce heterogeneous, traceable
information units and project-bound Processing Runs that can later support
Approved Input Promotion and framework-specific SubModels.

## Framework Template

The Phase P project framework is:

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

The Apollo 11 reference was reviewed during P1 for transferable structuring,
naming and hierarchy patterns.

It remains non-normative. Its CoSMA framework, package layout, engineering
content and identifiers were not transferred.

The initial framework is implemented as:

`context/frameworks/turing_rflp_framework.json`

Additional framework templates remain a post-MVP extension.

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

P1 was completed and verified in:

`82b5cbbe9bedac77a4b02928a596ea8fbdacc873`

Implemented deliverables:

- reviewed non-normative Apollo 11 structural reference
- versioned framework template `TURING_RFLP_FRAMEWORK`
- stable identifiers for 3 levels and 12 mapping targets
- zero-to-many information-unit mapping contract
- deterministic framework-template validation

## P2 Completion

P2 architecture is documented in:

`collaboration/decisions/ADR-005-project-workspace-architecture.md`

P2 implementation is verified through:

`36184a2d90db349555ac3bd64ccd5c27ecb68cec`

Implemented deliverables:

- project identity and display-name rules
- strict Project Manifest contract
- project workspace persistence
- safe reopening and project isolation
- public Project Workspace API

## P3 Completion

P3 architecture is documented in:

- `collaboration/decisions/ADR-009-textual-source-processing-boundary.md`
- `collaboration/decisions/ADR-010-project-source-registry-architecture.md`

P3 implementation is verified through:

`55cc4f104082ecfef70b3dcdeb8f28406ed95105`

Implemented deliverables:

- mandatory project assignment
- immutable project-local source manifests
- separate project and source identities
- `engineering_source` and `context_only` roles
- duplicate-content protection
- safe source persistence and scanning

## P4 Completion

P4 architecture is documented in:

`collaboration/decisions/ADR-011-semantic-information-unit-and-ontology-boundary.md`

P4 implementation is verified in:

`0c8ba428e7e6469e410b541c114d7a5a9474321c`

Verification:

- complete automated test suite: 2594 passed
- own-source diff validation: passed
- pinned external ontology integrity validation: passed
- `HEAD == origin/main`

Implemented deliverables:

- deterministic source projections
- text, Markdown, JSON, CSV, TSV and PDF text-layer adapters
- source-projection manifests and repositories
- pinned BFO 2020 and IOF Core 202602 snapshots
- ontology registry and deterministic reference-concept index
- Turing Core Vocabulary
- project-specific glossary and terminology decisions
- source-traceable Information Units
- semantic extraction candidate contracts
- multi-agent semantic consensus and variance
- terminology-mapping candidates
- framework-assignment candidates
- reference validation
- immutable Human Review Decisions
- exact publication gates
- deterministic token budgeting
- fail-closed required-context handling

## P5 Completion

P5 architecture is documented in:

`collaboration/decisions/ADR-012-processing-state-and-artifact-organization.md`

P5 implementation is verified through:

`9a9ef8bd7c08c354c638d4b0e072e308e7c02516`

Implemented deliverables:

- Processing Run, Event and Decision manifests
- event-history based current-state reconstruction
- run work and artifact directories
- retry, supersession, invalidation and recovery behavior
- Source and Project Processing aggregation
- fail-closed issue reporting

## P6 Completion

P6 architecture is documented in:

`collaboration/decisions/ADR-013-preliminary-coverage-and-potential-model-support.md`

P6 implementation is verified through:

`f921b216d66ee359dea7cf116cfea03acb1e3510`

Implemented deliverables:

- deterministic Preliminary Coverage assessment
- potential model-support assessment
- support profile
- source and framework evidence binding
- explicit attention and missing-coverage states
- Approved Generation Readiness remains unavailable in Phase P

## P7 Completion

P7 architecture is documented in:

`collaboration/decisions/ADR-014-project-dashboard-architecture.md`

P7 implementation is verified through:

`d8a3bc9bb55a4b7ab0fa6e999b74b8541bf224b6`

P7 project-creation fixes were completed through:

`fe0fd24`

Implemented deliverables:

- Project Dashboard
- project selection and constrained project creation
- Sources & Processing view
- Coverage & Support view
- Attention & Review view
- Traceability view
- evidence navigation and document preview
- read-only dashboard boundary

## P8 Completion

P8 confirmed P1–P7 integration readiness and the need for a separate P9
project-bound ingestion integration boundary.

Implemented deliverables:

- integration readiness review
- dashboard execution-boundary clarification
- confirmation that no parallel project or processing architecture was needed
- P9 added as the project-bound ingestion integration step

## P9 Completion

P9 architecture is documented in:

`collaboration/decisions/ADR-015-project-bound-agentic-ingestion-integration.md`

P9 implementation is verified through:

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
- `artifact_published` and `review_requested` event sequence
- final state `awaiting_review`
- Execution UI
- Dashboard return and review-report navigation

Verification:

- complete automated test suite: 3808 passed
- manual P9 acceptance audit: PASS
- `HEAD == origin/main`

## Phase P Exit Criteria

- a project can be created, persisted and reopened
- multiple sources can be assigned and processed independently
- every artifact remains traceable to project and source
- project source registry and processing state persist
- semantic candidates and decisions remain project-isolated
- preliminary coverage is distinct from approved readiness
- cross-project data mixing is prevented
- Human Review gates cannot be bypassed
- Project Dashboard shows the accepted Phase P information
- project-bound ingestion reaches `awaiting_review`
- automated tests and UI smoke tests pass
- SSOT UPDATE complete

## Status

Completed

---

# Post-Phase-P Reconciliation Gate

## Purpose

Create a deliberate cut after the completed prototype before further feature
implementation.

The gate preserves the presentation baseline and reconciles the implementation
reality from Phases F and P with the authoritative CATIA SysML v2 model.

## Deliverables

- stable prototype presentation baseline
- complete inventory of Phase F/P capabilities and accepted ADRs
- mapping of each capability to CATIA requirements, use cases and model elements
- identified missing, outdated, incomplete and conflicting requirements
- traceable requirement and model-change candidates
- Human Review of every proposed CATIA change
- accepted CATIA requirement and model updates
- Feature and Requirement Coverage Matrix
- explicit decision on the next implementation phase

## Feature and Requirement Coverage Matrix

Required columns:

| Column | Required content |
|---|---|
| Capability / Feature | Stable capability name |
| CATIA Requirement ID | Existing or proposed requirement reference |
| Implementation Status | Implemented, partial, architecture-only or planned |
| Test / Evidence | Test, commit, artifact or manual evidence |
| ADR | Accepted architecture-decision reference |
| Presentation Readiness | Ready, limited or not demonstrable |
| Remaining Roadmap | Missing implementation or later phase |

Implementation status values:

- `implemented_and_verified`
- `partially_implemented`
- `architecture_only`
- `planned`
- `not_planned_for_mvp`

Requirement coverage values:

- `covered`
- `partially_covered`
- `missing`
- `outdated`
- `conflicting`

## Rules

- implementation reality is evidence, not automatic normative authority
- no requirement is created silently from code
- CATIA remains authoritative
- every proposed CATIA change requires Human Review
- existing identifiers and accepted semantics are preserved unless a reviewed
  change requires otherwise
- no new feature phase begins before explicit gate closure

## Exit Criteria

- prototype presentation baseline is stable
- every relevant Phase F/P capability is inventoried
- every capability has CATIA coverage or an explicit coverage gap
- requirement and model-change candidates have been reviewed
- accepted CATIA changes have been applied
- Feature and Requirement Coverage Matrix is complete
- next implementation phase is explicitly selected

## Status

Active

Depends on:

Phase P — Satisfied

---

# Phase G – Approved Input Promotion

## Objective

Separate reviewed engineering knowledge from raw Source material, unreviewed
agent outputs, consensus reports and pending review reports.

Phase G shall define how accepted Human Review Decisions promote eligible
P4/P9 evidence into Approved Input.

## Deliverables

- Approved Input identity and repository
- promotion workflow using persisted Human Review Decisions
- promotion traceability to Source, Run, Artifact and Review Decision
- eligibility rules for reviewed Information Units and P9 review outcomes
- revocation, invalidation and supersession behavior
- clear separation from Preliminary Coverage and P9 run evidence

## Exit Criteria

- only exactly confirmed engineering information can become Approved Input
- every promotion remains traceable to source, candidate, run artifact and
  review decision
- Approved Input can be used by later model-candidate phases
- unreviewed P9 artifacts cannot be treated as approved engineering knowledge

## Status

Planned after the Post-Phase-P Reconciliation Gate

Depends on:

Post-Phase-P Reconciliation Gate

## First Architecture Questions

1. What is the minimal Approved Input object?
2. Which P4 and P9 artifacts are eligible promotion sources?
3. Which Human Review Decision target types are required?
4. How are content fingerprints, run fingerprints and review fingerprints bound?
5. How are rejected, superseded and invalidated promotions represented?
6. How does Approved Input support later model-candidate generation without
   generating models in Phase G?

Phase G is not automatically the next implementation activity. Its start
requires completion of the reconciliation gate and an explicit project-owner
decision.

# Phase H – Model Candidate Layer

## Objective

Generate validated model candidates from Approved Input.

## Deliverables

- candidate model elements
- candidate relationships
- candidate metadata
- full traceability

## Exit Criteria

- candidate layer generated without producing SysML v2 code

## Status

Planned

Depends on:

Phase G

---

# Phase I – Model Generation Agent

## Objective

Create an internal engineering model from approved model candidates.

## Deliverables

- Model Generation Agent
- internal model assembly
- structural consistency

## Exit Criteria

- internal model representation successfully generated

## Status

Planned

Depends on:

Phase H

---

# Phase J – SysML v2 Code Generator

## Objective

Generate valid SysML v2 textual notation.

## Deliverables

- SysML v2 code generator
- SYSIDE compatibility
- CATIA compatibility

## Exit Criteria

- valid SysML v2 textual model generated

## Status

Planned

Depends on:

Phase I

---

# Phase K – Validation Layer

## Objective

Validate generated engineering models before export.

## Deliverables

- syntax validation
- structural validation
- traceability validation
- engineering-rule validation

## Exit Criteria

- invalid models detected automatically

## Status

Planned

Depends on:

Phase J

---

# Phase L – Output Writer

## Objective

Export validated engineering artifacts.

## Deliverables

- SysML v2 output files
- versioned output structure
- export package

## Exit Criteria

- complete export package generated automatically

## Status

Planned

Depends on:

Phase K

---

# Phase N – CATIA Shadow-model Migration and Final Reconciliation

## Objective

Replace the temporary SYSIDE shadow model with the authoritative CATIA Magic
model and perform the final whole-system reconciliation after the later
implementation phases.

## Work Package N1 — Shadow-model Migration

Deliverables:

- migration of the shadow model
- synchronization with the repository
- updated model registry
- removal of duplicated maintained model authority

## Work Package N2 — Final Architecture-to-Requirements Reconciliation

The first reconciliation pass for Phases F and P is performed earlier in the
Post-Phase-P Reconciliation Gate.

Phase N performs the final reconciliation for architecture decisions and
capabilities introduced or changed after that gate.

Deliverables:

- final architecture-decision inventory
- final mapping from decisions and capabilities to authoritative model elements
- updated Requirement Coverage Matrix
- resolution or explicit deferral of remaining requirement gaps
- traceability from accepted CATIA elements to decision and implementation
  evidence
- confirmation that CATIA is the only maintained engineering model

Rules:

- implementation reality is evidence, not automatic normative authority
- no requirement is created silently from code
- CATIA changes require explicit Human Review
- the accepted derivation chain remains mandatory

## Exit Criteria

- CATIA Magic is the only maintained engineering model
- every accepted architecture decision is mapped to model coverage
- remaining missing requirements are resolved or explicitly deferred
- every accepted model addition has derivation and source traceability

## Status

Planned

Depends on:

Phase L and project-owner decision

# Phase Q – Thesis Architecture Documentation

## Objective

Document the architecture and development rationale for the thesis.

## Deliverables

- architecture decision inventory
- phase and development-plan documentation
- decision context, alternatives, rationale and consequences
- requirement and implementation traceability
- BFO and IOF selection and justification
- semantic and Human Review architecture
- deterministic token budgeting
- literature and standard sources

## Development Plan Note

A thesis-only Development Plan shall document the lettered development phases
used in the project. It shall remain separate from the feature overview and is
not intended for the intermediate presentation.

## Status

Planned

Depends on:

Phase N and project-owner decision
