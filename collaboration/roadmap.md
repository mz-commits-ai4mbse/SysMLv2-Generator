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

Current Architecture Version

0.9

Current Roadmap Version

1.0

Last SSOT Update

2026-07-20

Current Phase

**F – Agentic Ingestion UI**

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

In Progress

---

# Phase P – Project Workspace

## Objective

Introduce project-oriented processing instead of isolated document processing.

## Deliverables

- Project structure
- Multiple source documents
- Context management
- Framework coverage overview
- Processing state tracking
- Report organization

## Exit Criteria

- Complete project workspace implemented
- Sources assigned to projects
- Project dashboard operational

## Status

Planned

Depends on

Phase F

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

The roadmap may only be changed after

- discussion
- explicit agreement
- SSOT UPDATE

Roadmap changes become effective only after the Collaboration Knowledge Base has been updated.