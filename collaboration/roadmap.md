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

1.0

Knowledge Base Version

1.3

Implementation Version

0.7

Roadmap Version

1.3

Last SSOT Update

2026-07-24

Current Phase

**P – Project Workspace**

Current Status

P1–P4 Completed — P5 Next

Verified Implementation Commit

`0c8ba428e7e6469e410b541c114d7a5a9474321c`

---

# Phase F – Agentic Ingestion UI

## Objective

Provide a functional user interface for the complete agentic ingestion
workflow.

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

# Phase P – Project Workspace

## Objective

Introduce project-oriented processing around the completed Phase F ingestion
pipeline.

Multiple individually ingested sources shall produce heterogeneous, traceable
information units that can later support framework-specific SubModels.

## Framework Template

The initial project framework is:

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
| P5 | Processing State and Artifact Organization | Next |
| P6 | Coverage and Preliminary Readiness Engine | Planned |
| P7 | Project Dashboard | Planned |
| P8 | Tests and Phase Review | Planned |

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

## Data and Review Boundaries

- Every source is assigned to exactly one project.
- Project identity and source identity remain separate.
- One source may yield multiple source-traceable Information Units.
- One Information Unit may map to multiple valid framework nodes.
- Context-only sources shall not create engineering Information Units.
- Context-only sources shall not satisfy coverage or readiness.
- Multi-agent consensus and confidence remain review evidence.
- No consensus result may bypass Human Review.
- Publication requires an exact human confirmation.
- Required LLM context shall not be silently truncated.

## Dashboard Scope

The Project Dashboard shall provide:

- project metadata
- source inventory and processing state
- graphical framework coverage
- preliminary indication of potentially supported models and SubModels
- separate approved readiness
- disabled controls for future Project-wide Model and selected SubModel
  generation until their responsible phases

Phase P does not generate models.

## Exit Criteria

- a project can be created, persisted and reopened
- multiple sources can be assigned and processed independently
- every artifact remains traceable to its project and source
- project source registry and processing state persist
- semantic candidates and decisions remain project-isolated
- preliminary coverage is distinct from approved readiness
- cross-project data mixing is prevented
- Human Review gates cannot be bypassed
- Project Dashboard shows the accepted Phase P information
- automated tests and UI smoke tests pass
- P8 phase review and SSOT UPDATE are complete

## Status

In Progress — P1–P4 Completed, P5 Next

## Next Step

P5 — Processing State and Artifact Organization

P5 shall define:

- canonical project processing states
- allowed state transitions
- artifact organization across the P1–P4 repositories
- failure and retry behavior
- supersession behavior
- reopening behavior
- project-level aggregation without duplicating artifact authority
- explicit traceability across state transitions

The P5 architecture shall be discussed and accepted before implementation
depends on it.

Depends on:

Phase F — Satisfied

---

# Phase G – Approved Input Promotion

## Objective

Separate reviewed engineering knowledge from raw and candidate ingestion
results.

## Deliverables

- approved engineering-information state
- promotion workflow using persisted Human Review Decisions
- Approved Input repository
- promotion traceability
- revocation and supersession behavior

## Exit Criteria

- only exactly confirmed engineering information can become Approved Input
- promotion remains traceable to source, candidate and review decision

## Status

Planned

Depends on:

Phase P

---

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

# Phase N – CATIA Migration and Model Reconciliation

## Objective

Replace the temporary SYSIDE shadow model with the authoritative CATIA Magic
model and reconcile the engineering model with the accepted system
architecture.

## Work Package N1 — Shadow-model Migration

Deliverables:

- migration of the shadow model
- synchronization with the repository
- updated model registry
- removal of duplicated maintained model authority

## Work Package N2 — Architecture-to-Requirements Reconciliation

Purpose:

The accepted architecture decisions and the implemented and planned system
capabilities contain features that are not yet completely represented by
requirements in the authoritative engineering model.

Deliverables:

- complete inventory of accepted architecture decisions
- mapping from decisions and capabilities to existing model elements
- Requirement Coverage Matrix
- identified missing, outdated and conflicting requirements
- traceable requirement and model-change candidates
- classification of stakeholder need, requirement, design constraint and
  implementation detail
- Human Review of every proposed model change
- accepted additions to Stakeholder Requirements, Use Cases, System
  Requirements and downstream model elements
- traceability from accepted model elements to architecture-decision and
  implementation evidence

Rules:

- implementation reality is evidence, not automatic normative authority
- no requirement is created silently from existing code
- the accepted derivation chain remains mandatory
- CATIA is updated only after explicit Human Review
- existing IDs and accepted model semantics are preserved unless a reviewed
  change requires otherwise

## Exit Criteria

- CATIA Magic is the only maintained engineering model
- every accepted architecture decision is mapped to model coverage
- missing requirements have been resolved or explicitly deferred
- every accepted model addition has derivation and source traceability
- implementation and authoritative requirements are reconciled without
  silently converting implementation details into requirements

## Status

Planned

Depends on:

Phase L

---

# Phase Q – Thesis Architecture Documentation

## Objective

Document and justify the complete Turing Generator architecture for the
written thesis.

Phase Q is intentionally placed after Phase N so that the documentation uses
the reconciled authoritative engineering model.

## Deliverables

- thesis-ready documentation of every architecture decision from Phases A–P
- documentation of every architecture decision accepted after Phase P
- decision context, alternatives, rationale and consequences
- mapping from architecture decisions to requirements and implementation
- explanation and justification of BFO 2020 as top-level reference
- explanation and justification of IOF Core as industrial reference
- explanation of the project-specific glossary and Turing Core Vocabulary
- explanation of semantic authority and ontology boundaries
- explanation of multi-agent consensus, variance and Human Review
- explanation of deterministic token budgeting
- source-backed literature and standard references
- thesis figures and architecture views
- open limitations and future-work boundaries

## Exit Criteria

- all accepted architecture decisions are represented in the thesis
- all claims that require literature or standards are supported by sources
- architecture, authoritative requirements and committed implementation are
  consistent
- known deviations and deferred decisions are explicit

## Status

Planned

Depends on:

Phase N

---

# Phase M – Evaluation

## Objective

Evaluate the completed MVP against the original project objectives.

## Deliverables

- feature release matrix
- Stakeholder Requirement coverage
- comparison with the Kickoff presentation
- integration of professor feedback
- MVP evaluation report

## Exit Criteria

- MVP formally evaluated
- remaining gaps documented
- roadmap for future work established

## Status

Planned

Depends on:

Phase Q

---

# Phase O – Thesis and Demonstration Completion

## Objective

Prepare the final research prototype, demonstration and thesis submission.

## Deliverables

- final thesis figures
- demonstration material
- repository cleanup
- documentation review
- final presentation
- submission-ready thesis

## Exit Criteria

- prototype ready for submission
- demonstration ready
- thesis complete

## Status

Planned

Depends on:

Phase M

---

# Development Workflow

Every phase follows the same engineering process:

Implementation

↓

Testing

↓

Review

↓

SSOT UPDATE

↓

Start Next Phase

---

# SSOT Update Cadence

A complete SSOT UPDATE is normally performed after completion of a major
roadmap phase.

This update is an explicitly requested intermediate synchronization after P4
because P4 introduced a substantial semantic architecture baseline and a new
handover is required.

The next regular complete SSOT UPDATE remains due after P8 and completion of
Phase P unless the project owner explicitly requests an earlier update or a
critical handover need arises.

---

# Change Management

Roadmap changes require:

- explicit discussion
- explicit agreement by the project owner
- an SSOT UPDATE
- repository commit, push and verification

Ideas and future options shall not be recorded as committed roadmap scope until
they have been explicitly accepted.

Roadmap changes become effective only after the Collaboration Knowledge Base
has been updated, committed, pushed and verified.