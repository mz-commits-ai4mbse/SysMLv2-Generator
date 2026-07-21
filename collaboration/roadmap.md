# Roadmap

## Purpose

This roadmap defines the official development phases of the Turing Generator.

Each phase represents a major engineering milestone.

A phase is considered complete only after

- implementation
- testing
- review
- SSOT UPDATE

have been successfully completed.

---

# Project Status

Architecture Version

0.9

Knowledge Base Version

1.2

Implementation Version

0.6

Roadmap Version

1.2

Last SSOT Update

2026-07-21

Current Phase

**P – Project Workspace**

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

- Complete ingestion workflow operational
- Review report suitable for engineering review
- Memory pipeline fully integrated
- Stable demonstration UI

## Status

Completed

Verified in

`adce9ec65ca3e36b89686b55d397a34dd382fdb1`

Verification

- Complete automated test suite: 9 passed
- Agentic Ingestion UI smoke test: passed
- Engineering review report regression: passed

---

# Phase P – Project Workspace

## Objective

Introduce project-oriented processing around the completed Phase F ingestion pipeline. Multiple individually ingested sources shall produce heterogeneous, traceable information units that can later support framework-specific SubModels.

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

The initial framework is implemented as the versioned, machine-readable
template:

`context/frameworks/turing_rflp_framework.json`

Additional framework templates remain a post-MVP extension.

## Work Breakdown

| Step | Deliverable | Status |
|---|---|---|
| P1 | Framework Template Definition | Completed |
| P2 | Project Manifest and Workspace Structure | Next |
| P3 | Source Registry and mandatory Project Assignment | Planned |
| P4 | Framework-mapped heterogeneous Information Units | Planned |
| P5 | Processing State and Artifact Organization | Planned |
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
- exclusion of `context_only` sources from framework mapping
- explicit separation of preliminary coverage and approved readiness
- deterministic framework-template validation
- automated P1 tests

Verification:

- P1 framework tests: 9 passed
- complete automated test suite: 18 passed
- `git diff --check`: passed

## Data and Review Boundaries

- Every new upload must be assigned to exactly one project. No permanent unassigned source pool is permitted.
- One source may yield multiple source-traceable information units, and one information unit may map to multiple framework nodes.
- Engineering sources may contribute to preliminary coverage. Only human-approved engineering information may later contribute to generation readiness and model generation.
- Context-only sources may explain terminology and system context, but shall not satisfy coverage, readiness or model-generation evidence.
- Preliminary coverage and approved readiness shall be displayed separately.

## Dashboard Scope

The Project Dashboard shall provide:

- project metadata
- source inventory and processing state
- graphical framework coverage
- preliminary indication of potentially supported models and SubModels
- separate approved readiness, which remains unavailable until Phase G supplies approved inputs
- disabled controls for future Project-wide Model and selected SubModel generation

Phase P does not generate models. The disabled controls communicate later capability only. Actual candidate creation and model generation remain assigned to Phases H–J.

## Exit Criteria

- A project can be created, persisted and reopened.
- At least two source files can be assigned to one project and processed through the Phase F pipeline.
- Every source, ingestion run, information unit, report and artifact remains traceable to its project and source.
- Project source registry and processing state persist across application restarts.
- The dashboard displays project metadata, source inventory, processing state, framework coverage, runs and reports.
- Preliminary coverage is visibly distinct from approved readiness.
- Cross-project data mixing is prevented and tested.
- Human approval from Phase G and model generation from Phases H–J are not pulled forward.
- Automated tests and a UI smoke test pass.

## Status

In Progress — P1 Completed, P2 Architecture Definition Not Started

Verified P1 Implementation

`82b5cbbe9bedac77a4b02928a596ea8fbdacc873`

Next Step

P2 — Project Manifest and Workspace Structure

Before P2 implementation begins, the Project Workspace architecture and
persistence boundaries shall be discussed, explicitly accepted and recorded in
ADR-005.

Depends on

Phase F — Satisfied

---

# Phase G – Approved Input Promotion

## Objective

Separate reviewed engineering knowledge from raw ingestion results.

## Deliverables

- Human review workflow
- Approval decisions
- Approved Input repository
- Review persistence

## Exit Criteria

- Approved engineering information available for downstream model generation

## Status

Planned

Depends on

Phase P

---

# Phase H – Model Candidate Layer

## Objective

Generate validated model candidates from approved engineering information.

## Deliverables

- Candidate model elements
- Candidate relationships
- Candidate metadata
- Full traceability

## Exit Criteria

- Candidate layer generated without producing SysML v2 code

## Status

Planned

Depends on

Phase G

---

# Phase I – Model Generation Agent

## Objective

Create an internal engineering model from approved model candidates.

## Deliverables

- Model generation agent
- Internal model assembly
- Structural consistency

## Exit Criteria

- Internal model representation successfully generated

## Status

Planned

Depends on

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

- Valid SysML v2 textual model generated

## Status

Planned

Depends on

Phase I

---

# Phase K – Validation Layer

## Objective

Validate generated engineering models before export.

## Deliverables

- Syntax validation
- Structural validation
- Traceability validation
- Engineering rule validation

## Exit Criteria

- Invalid models detected automatically

## Status

Planned

Depends on

Phase J

---

# Phase L – Output Writer

## Objective

Export validated engineering artifacts.

## Deliverables

- SysML v2 output files
- Versioned output structure
- Export package

## Exit Criteria

- Complete export package generated automatically

## Status

Planned

Depends on

Phase K

---

# Phase N – CATIA Migration

## Objective

Replace the temporary SYSIDE shadow model with the authoritative CATIA Magic model.

## Deliverables

- Migration of the shadow model
- Synchronization with repository
- Updated model registry

## Exit Criteria

- CATIA Magic becomes the only maintained engineering model

## Status

Planned

Depends on

Phase L

---

# Phase M – Evaluation

## Objective

Evaluate the completed MVP against the original project objectives.

## Deliverables

- Feature release matrix
- Stakeholder Requirement coverage
- Comparison with the Kickoff presentation
- Integration of professor feedback
- MVP evaluation report

## Exit Criteria

- MVP formally evaluated
- Remaining gaps documented
- Roadmap for future work established

## Status

Planned

Depends on

Phase N

---

# Phase O – Thesis & Demonstration

## Objective

Prepare the final research prototype and thesis.

## Deliverables

- Thesis figures
- Demonstration material
- Repository cleanup
- Documentation review
- Final presentation

## Exit Criteria

- Prototype ready for submission
- Demonstration ready
- Thesis complete

## Status

Planned

Depends on

Phase M

---

# Development Workflow

Every phase follows the same engineering process.

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

# Change Management

Roadmap changes require:

- explicit discussion
- explicit agreement by the project owner
- an SSOT UPDATE
- repository commit, push and verification

Ideas and future options shall not be recorded as committed roadmap scope until they have been explicitly accepted.

The roadmap may only be changed after

- discussion
- explicit agreement
- SSOT UPDATE

Roadmap changes become effective only after the Collaboration Knowledge Base has been updated.
