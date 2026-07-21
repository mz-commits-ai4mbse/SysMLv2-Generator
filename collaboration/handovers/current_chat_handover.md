# Current Chat Handover

## Purpose

This document is the starting point for the next implementation chat. It contains the current accepted project context and intentionally does not rely on previous chat history.

---

# Project

Project

Turing Generator

Repository

`mz-commits-ai4mbse/SysMLv2-Generator`

Branch

`main`

Verified Implementation Commit

`adce9ec65ca3e36b89686b55d397a34dd382fdb1`

Current Phase

P – Project Workspace

Current Status

Scope Defined — Implementation Not Started

Architecture Version

0.9

Knowledge Base Version

1.1

Implementation Version

0.5

Roadmap Version

1.1

---

# Read Before Starting

Read the Collaboration Knowledge Base in this order:

1. `collaboration/current_state.md`
2. `collaboration/roadmap.md`
3. `collaboration/working_rules.md`
4. `collaboration/model_registry.json`
5. `collaboration/decisions/`

Then inspect the committed repository implementation relevant to Phase P.

Do not use previous chat history as a source of truth.

---

# Source Authority

1. The CATIA SysML v2 model is authoritative for engineering knowledge.
2. The committed GitHub repository is authoritative for implementation reality.
3. The Collaboration Knowledge Base is authoritative for roadmap, status, accepted decisions and working rules.
4. Chat history and generated artifacts are non-authoritative.

If required engineering information is not yet available in CATIA, the temporary shadow model under `model/` may supplement it until Phase N. It shall never override or contradict CATIA.

---

# Completed Baseline

Phase F is complete and verified at commit `adce9ec65ca3e36b89686b55d397a34dd382fdb1`.

Completed capabilities include:

- team-based agentic ingestion
- memory pipeline and consensus reports
- deterministic engineering review report
- traceable gaps, risks, questions and source references
- Streamlit ingestion UI
- artifact browser with five result tabs
- Dry Run and LLM execution paths
- automated test suite with 9 passing tests

The existing Phase F pipeline shall remain operational while Phase P adds project-oriented processing around it.

---

# Accepted Phase P Scope

## Framework

The initial framework is:

- Stakeholder Level: Stakeholders, User Needs, Stakeholder Requirements, Use Cases
- System Level: Requirements, Functional, Logical, Physical
- Subsystem Level: Requirements, Functional, Logical, Physical

The actual Apollo 11 package layout shall not be copied unchanged. `context/examples/apollo11_structure_reference.md` is a non-normative, currently unreviewed reference. Additional framework templates are post-MVP scope.

## Projects and Sources

- Every new upload must be assigned to exactly one selected project.
- No permanent unassigned source pool is allowed.
- A project may contain multiple individually processed sources.
- Every run and artifact must remain traceable to its project and source.
- Cross-project mixing must be prevented.

## Information Units

One engineering source may yield multiple heterogeneous, traceable information units. An information unit may map to multiple framework nodes.

The intended minimum semantics include identity, project and source references, source location, information type, original and normalized statement, framework assignments, confidence, review status and traceability. The exact schema is an implementation decision within Phase P.

## Source Roles

- `engineering_source`: may contribute to clearly marked preliminary coverage; it may contribute to readiness or generation only after human approval.
- `context_only`: may explain product context or terminology, but shall not create generation evidence or satisfy coverage or readiness.

Optional context-document upload during project creation is not required for Phase P UI completion, but the data-role distinction must be supported by the architecture.

## Dashboard and Later Generation

The Project Dashboard shall display project metadata, source inventory, processing state, framework coverage, ingestion runs and reports.

It shall distinguish:

- preliminary support based on unreviewed engineering information
- approved generation readiness based only on human-approved information

Phase P may display disabled controls for `Generate Project-wide Model` and `Generate Selected SubModel`. They shall not execute in Phase P. Approved Input Promotion belongs to Phase G; candidate creation and actual model generation belong to Phases H–J.

Later Project-wide generation shall generate only sufficiently supported models. Unsupported models remain disabled and show their information gaps.

---

# Phase P Work Breakdown

1. P1 — Framework Template Definition
2. P2 — Project Manifest and Workspace Structure
3. P3 — Source Registry and mandatory Project Assignment
4. P4 — Framework-mapped heterogeneous Information Units
5. P5 — Processing State and Artifact Organization
6. P6 — Coverage and Preliminary Readiness Engine
7. P7 — Project Dashboard
8. P8 — Tests and Phase Review

---

# Next Implementation Step

Start P1 — Framework Template Definition.

Before writing code:

- verify the authoritative repository commit and working tree context
- inspect existing mapping, context and ingestion structures relevant to P1
- review the non-normative Apollo 11 reference
- propose a versioned, machine-readable framework-template contract with stable node identifiers
- discuss any architecture decision that would constrain P2 persistence

The concrete Project Workspace persistence layout is not yet accepted. ADR-005 shall be created when the architecture is discussed and explicitly approved; do not infer it from this handover.

---

# Starting Prompt for the Next Chat

Continue the implementation of the Turing Generator in repository `mz-commits-ai4mbse/SysMLv2-Generator`, branch `main`.

Begin by reading the Collaboration Knowledge Base. Then verify the committed implementation baseline and summarize:

- current roadmap phase
- current implementation status
- current architecture version
- next implementation step

Do not use previous chat history as a source of truth. Do not start implementation before presenting the summary.

After the summary, begin P1 — Framework Template Definition, using the accepted Phase P scope and source-authority rules.
