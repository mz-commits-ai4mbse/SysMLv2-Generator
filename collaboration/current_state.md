# Current Project State

## Purpose

This document describes the current implementation reality of the Turing Generator. It is updated during every `SSOT UPDATE` and shall not redefine engineering knowledge contained in the authoritative CATIA SysML v2 model.

---

# Project

Project

Turing Generator

Repository

`mz-commits-ai4mbse/SysMLv2-Generator`

Current Branch

`main`

Verified Implementation Commit

`adce9ec65ca3e36b89686b55d397a34dd382fdb1`

Architecture Version

0.9

Knowledge Base Version

1.1

Implementation Version

0.5

Current Roadmap Version

1.1

Current Development Phase

P – Project Workspace

Current Status

Scope Defined — Implementation Not Started

Last SSOT Update

2026-07-21

---

# Current Objective

Implement a project-oriented workspace around the completed agentic ingestion pipeline.

Current focus:

- define the Stakeholder/System/Subsystem framework template
- define project identity, metadata and source assignment
- represent multiple heterogeneous, traceable information units from each source
- prepare project coverage and preliminary readiness views
- prepare a project dashboard without implementing approval or model generation early

---

# Current Engineering Priorities

Priority 1

Complete P1 — Framework Template Definition.

Priority 2

Define the Project Workspace architecture and persistence boundaries for P2. Record the accepted architecture in ADR-005 before implementation depends on it.

Priority 3

Implement project assignment, project artifacts, coverage and the Project Dashboard in the remaining Phase P steps.

No work shall begin on Phase G or later phases before Phase P has been completed and an SSOT UPDATE has been performed.

---

# Implemented Baseline

Phase F is complete at commit `adce9ec65ca3e36b89686b55d397a34dd382fdb1`.

Implemented and verified:

- modular agent and team execution architecture
- memory-based ingestion pipeline
- consensus framework
- deterministic engineering review report
- traceable gaps, ambiguities, risks and independent review questions
- Streamlit Agentic Ingestion UI
- Dry Run and LLM execution paths
- report, run-summary, consensus, agent-output and artifact browsing
- automated test suite with 9 passing tests

The current pipeline remains:

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

---

# Active Phase P Scope

Phase P will add a Project Workspace around the existing ingestion pipeline.

## Project and Source Rules

- Every new upload must be assigned to a selected project.
- There is no permanent unassigned source pool.
- A project may contain multiple sources that are processed individually and aggregated deterministically.
- Each ingestion run and resulting artifact must remain traceable to its project and source.
- Sources must not be mixed across projects.

## Information Units

A single engineering source may yield multiple heterogeneous, source-traceable information units. Information units may map to more than one framework node.

Context-only project documents may explain terminology or product context, but shall not create engineering evidence, satisfy coverage or readiness, or contribute to model generation.

## Framework

The initial framework has three levels:

- Stakeholder Level: Stakeholders, User Needs, Stakeholder Requirements, Use Cases
- System Level: Requirements, Functional, Logical, Physical
- Subsystem Level: Requirements, Functional, Logical, Physical

The Apollo 11 reference is non-normative and has not yet been reviewed. P1 shall curate the framework template without copying the Apollo package layout unchanged. Additional framework templates are post-MVP scope.

## Dashboard and Generation Boundary

The dashboard shall display project metadata, source inventory, processing state, framework coverage and preliminary model support.

Preliminary coverage based on unreviewed engineering information must be clearly marked as preliminary. Approved generation readiness must be separate and may use only human-approved information.

Phase P may show disabled controls for a Project-wide Model and selected SubModels. Phase P shall not execute model generation. Later generation shall create only models whose approved data is sufficient; unsupported models remain disabled and their gaps remain visible.

---

# Not Yet Implemented

- Project Workspace persistence and dashboard
- source registry and mandatory project assignment
- framework-mapped information-unit repository
- persisted human review decisions
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
- The initial framework template still requires P1 review and definition.
- The Apollo 11 reference remains non-normative and unreviewed.
- Full-team LLM execution still requires performance and token optimization.

## Controlled by Design

- Unreviewed information cannot be treated as approved generation input.
- Context-only documents cannot satisfy coverage or readiness.
- CATIA remains authoritative and the temporary shadow model cannot override it.

---

# Next Milestone

P1 — Framework Template Definition

Expected outcome:

- a versioned, machine-readable framework template
- stable identifiers for every framework node
- explicit mapping targets for heterogeneous information units
- documented distinction between preliminary coverage and approved readiness
- tests for template validity and identifiers

The detailed Project Workspace persistence layout is intentionally deferred until it is discussed and accepted for P2.

---

# Reference Documents

- Roadmap: `roadmap.md`
- Working Rules: `working_rules.md`
- Architecture Decisions: `decisions/`
- Model Registry: `model_registry.json`
- Handover: `handovers/current_chat_handover.md`
