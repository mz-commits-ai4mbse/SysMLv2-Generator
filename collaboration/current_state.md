# Current Project State

## Purpose

This document describes the current implementation reality of the Turing
Generator. It is updated during every `SSOT UPDATE` and shall not redefine
engineering knowledge contained in the authoritative CATIA SysML v2 model.

---

# Project

Project

Turing Generator

Repository

`mz-commits-ai4mbse/SysMLv2-Generator`

Current Branch

`main`

Verified Implementation Commit

`82b5cbbe9bedac77a4b02928a596ea8fbdacc873`

Architecture Version

0.9

Knowledge Base Version

1.2

Implementation Version

0.6

Current Roadmap Version

1.2

Current Development Phase

P – Project Workspace

Current Status

P1 Completed — P2 Architecture Definition Not Started

Last SSOT Update

2026-07-21

---

# Current Objective

Define and implement a project-oriented workspace around the completed agentic
ingestion pipeline.

The immediate focus is P2 — Project Manifest and Workspace Structure.

Before implementation depends on a persistence layout, the Project Workspace
architecture shall be discussed, explicitly accepted and recorded in ADR-005.

---

# Current Engineering Priorities

Priority 1

Define the Project Workspace architecture and persistence boundaries for P2.

Priority 2

Record the explicitly accepted architecture in ADR-005 before implementing the
Project Manifest and Workspace Structure.

Priority 3

Continue with source assignment, information units, processing state, coverage
and the Project Dashboard through the remaining Phase P steps.

No work shall begin on Phase G or later phases before Phase P has been completed
and an SSOT UPDATE has been performed.

---

# Implemented Baseline

## Phase F — Agentic Ingestion UI

Phase F is complete and remains verified at commit:

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

The Phase F pipeline remains:

Raw Source

↓

Interpretation Team and Memory

↓

Evidence Team and Memory

↓

Derivation Team and Memory

↓

Completeness Team and Memory

↓

Deterministic Review Report

## P1 — Framework Template Definition

P1 is complete and verified at commit:

`82b5cbbe9bedac77a4b02928a596ea8fbdacc873`

Implemented and verified:

- reviewed Apollo 11 structural reference
- explicit separation of accepted and rejected reference patterns
- versioned machine-readable framework template
- stable identifiers for all framework levels and nodes
- 3 framework levels
- 12 explicit information-unit mapping targets
- zero-to-many framework assignments
- rejection of unknown framework targets
- exclusion of `context_only` sources from framework mapping
- explicit separation of preliminary coverage and approved readiness
- deterministic framework-template validator
- automated framework-template tests
- complete automated test suite with 18 passing tests

Framework template:

`context/frameworks/turing_rflp_framework.json`

Template ID:

`TURING_RFLP_FRAMEWORK`

Template Version:

`1.0.0`

---

# Active Phase P Scope

Phase P adds a Project Workspace around the existing ingestion pipeline.

## Project and Source Rules

- Every new upload must be assigned to a selected project.
- There is no permanent unassigned source pool.
- A project may contain multiple sources that are processed individually and
  aggregated deterministically.
- Each ingestion run and resulting artifact must remain traceable to its project
  and source.
- Sources must not be mixed across projects.

## Information Units

A single engineering source may yield multiple heterogeneous,
source-traceable information units.

An information unit may map to zero, one or multiple valid framework nodes.

Context-only project documents may explain terminology or product context, but
shall not create engineering evidence, satisfy coverage or readiness, or
contribute to model generation.

## Framework

The implemented initial framework has three levels:

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

The Apollo 11 repository has been reviewed for transferable structuring,
naming and hierarchy patterns.

It remains a non-normative reference. Its CoSMA framework, package layout,
engineering content and identifiers were not transferred.

Additional framework templates remain post-MVP scope.

## Coverage and Generation Boundary

Preliminary coverage may use unreviewed information from an
`engineering_source` when clearly marked as preliminary.

Approved readiness is separate and requires human-approved engineering
information. It remains unavailable during Phase P.

Phase P may show disabled controls for a Project-wide Model and selected
SubModels. Phase P shall not execute model generation.

Approved Input Promotion belongs to Phase G. Candidate creation and model
generation remain assigned to Phases H–J.

---

# Not Yet Implemented

- Project Workspace architecture and ADR-005
- Project Manifest and Workspace persistence
- source registry and mandatory project assignment
- framework-mapped information-unit repository
- persisted human review decisions
- coverage and preliminary readiness calculation
- Project Dashboard
- Approved Input Promotion
- Model Candidate Layer
- model generation
- SysML v2 code generation
- validation and export
- CATIA synchronization

---

# Current Known Limitations and Risks

## Medium

- The Project Workspace persistence architecture is not yet accepted.
- ADR-005 has not yet been created.
- Full-team LLM execution still requires performance and token optimization.

## Controlled by Design

- Framework mapping uses validated stable node identifiers.
- Unknown framework targets are rejected.
- Unreviewed information cannot be treated as approved generation input.
- Context-only documents cannot satisfy coverage or readiness.
- CATIA remains authoritative for engineering knowledge.
- The temporary shadow model cannot override or contradict CATIA.
- Apollo 11 remains a non-normative structural reference.

---

# Next Milestone

P2 — Project Manifest and Workspace Structure

Before implementation:

- define project identity and required metadata
- define the Project Manifest contract
- define the workspace directory structure
- define persistence and reopening behavior
- define project isolation boundaries
- define how later sources, runs and artifacts will reference a project
- discuss consequences and alternatives
- record the accepted decision in ADR-005

P2 implementation shall not begin before the architecture has been explicitly
accepted.

---

# Repository Collaboration Workflow

External GitHub repositories and repository links are used passively for
inspection only.

AI assistants shall not commit, push or directly modify GitHub repository
content.

Repository changes are applied, reviewed, committed and pushed locally by the
project owner.

AI assistants act as implementation guides and shall identify every affected
file by its repository-relative path before proposing a change.

---

# Reference Documents

- Roadmap: `roadmap.md`
- Working Rules: `working_rules.md`
- Architecture Decisions: `decisions/`
- Model Registry: `model_registry.json`
- Handover: `handovers/current_chat_handover.md`
- Framework Template: `../context/frameworks/turing_rflp_framework.json`
- Apollo 11 Review: `../context/examples/apollo11_structure_reference.md`