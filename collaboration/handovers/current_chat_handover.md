# Current Chat Handover

## Purpose

This document is the starting point for the next implementation chat.

It contains the current accepted project context and intentionally does not rely
on previous chat history.

---

# Project

Project

Turing Generator

Repository

`mz-commits-ai4mbse/SysMLv2-Generator`

Branch

`main`

Verified Implementation Commit

`82b5cbbe9bedac77a4b02928a596ea8fbdacc873`

Current Phase

P – Project Workspace

Current Status

P1 Completed — P2 Architecture Definition Not Started

Architecture Version

0.9

Knowledge Base Version

1.2

Implementation Version

0.6

Roadmap Version

1.2

---

# Read Before Starting

Read the Collaboration Knowledge Base in this order:

1. `collaboration/current_state.md`
2. `collaboration/roadmap.md`
3. `collaboration/working_rules.md`
4. `collaboration/model_registry.json`
5. `collaboration/decisions/`

Then inspect the committed repository implementation relevant to P2.

Do not use previous chat history as a source of truth.

---

# Source Authority

1. The CATIA SysML v2 model is authoritative for engineering knowledge.
2. The committed GitHub repository is authoritative for implementation
   reality.
3. The Collaboration Knowledge Base is authoritative for roadmap, status,
   accepted decisions and working rules.
4. Chat history and generated artifacts are non-authoritative.

If required engineering information is unavailable in CATIA, the temporary
shadow model under `model/` may supplement it until Phase N.

The shadow model shall never override or contradict CATIA.

---

# Repository Collaboration Workflow

GitHub repositories and repository links are used passively by AI assistants.

AI assistants shall not:

- directly modify GitHub repository content
- create or update remote branches
- commit or push changes
- open or merge pull requests
- use GitHub write APIs
- stage files in the project owner's working tree
- destructively clean the project owner's working tree

Repository changes are:

1. proposed by the AI assistant with exact repository-relative file paths,
2. applied locally by the project owner in VS Code,
3. reviewed and tested locally,
4. staged explicitly by file path,
5. committed and pushed by the project owner,
6. verified passively after the push.

The AI assistant acts as an implementation guide.

Unless the project owner explicitly requests grouped changes, modifications
shall be presented one file at a time.

Broad staging commands shall not be used when unrelated working-tree changes
exist.

---

---

# SSOT Update Cadence

A complete SSOT UPDATE is performed after completion of a major roadmap phase,
not after every internal work step.

For the current Phase P:

- P1 through P8 are tracked through implementation commits and test evidence.
- Accepted architecture decisions are documented in committed ADRs.
- ADR-005 shall be committed before P2 implementation depends on it.
- A separate full SSOT UPDATE is not required after P2 or the other internal
  Phase P steps.
- The next regular full SSOT UPDATE shall be performed after P8 and completion
  of Phase P.

An earlier SSOT UPDATE requires an explicit project-owner request or a critical
handover need.

# Completed Baseline

## Phase F — Agentic Ingestion UI

Phase F is complete and verified at:

`adce9ec65ca3e36b89686b55d397a34dd382fdb1`

Completed capabilities include:

- team-based agentic ingestion
- memory pipeline and consensus reports
- deterministic engineering review report
- traceable gaps, risks, questions and source references
- Streamlit ingestion UI
- artifact browser
- Dry Run and LLM execution paths

The existing Phase F pipeline shall remain operational while Phase P adds
project-oriented processing around it.

## P1 — Framework Template Definition

P1 is complete and verified at:

`82b5cbbe9bedac77a4b02928a596ea8fbdacc873`

Completed P1 deliverables:

- reviewed Apollo 11 structural reference
- explicit accepted and rejected reference patterns
- versioned framework template
- stable framework level and node identifiers
- 3 framework levels
- 12 information-unit mapping targets
- zero-to-many framework assignments
- rejection of unknown framework targets
- exclusion of `context_only` sources from framework mapping
- separate preliminary coverage and approved readiness semantics
- deterministic framework-template validator
- automated framework-template tests
- framework documentation

Framework template:

`context/frameworks/turing_rflp_framework.json`

Template ID:

`TURING_RFLP_FRAMEWORK`

Template Version:

`1.0.0`

Verification:

- P1 framework tests: 9 passed
- complete automated test suite: 18 passed
- `git diff --check`: passed

---

# Accepted Phase P Scope

## Framework

The implemented framework is:

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

Additional framework templates remain post-MVP scope.

The Apollo 11 repository was reviewed only for transferable structuring,
naming and hierarchy patterns.

Apollo 11 remains non-normative. Its CoSMA framework, package layout,
engineering content and identifiers were not transferred.

## Projects and Sources

- Every new upload must be assigned to exactly one selected project.
- No permanent unassigned source pool is allowed.
- A project may contain multiple individually processed sources.
- Every source, run and artifact must remain traceable to its project.
- Cross-project mixing must be prevented.

## Information Units

One engineering source may yield multiple heterogeneous, traceable information
units.

An information unit may map to zero, one or multiple valid framework nodes.

The intended minimum semantics include:

- stable identity
- project reference
- source reference
- source location
- information type
- original statement
- normalized statement
- framework assignments
- confidence
- review status
- traceability

The exact Information Unit schema remains assigned to P4.

## Source Roles

### Engineering Source

An `engineering_source` may:

- create source-traceable engineering information units
- create framework assignments
- contribute to clearly marked preliminary coverage
- contribute to readiness or generation only after human approval

### Context-only Source

A `context_only` source may explain terminology or product context.

It shall not:

- create engineering information units
- create framework assignments
- satisfy preliminary coverage
- satisfy approved readiness
- contribute to model generation

## Coverage and Later Generation

Preliminary coverage may use unreviewed engineering information only when
clearly marked as preliminary.

Approved generation readiness is separate and may use only human-approved
engineering information.

Approved readiness remains unavailable during Phase P.

Phase P may display disabled controls for:

- `Generate Project-wide Model`
- `Generate Selected SubModel`

These controls shall not execute during Phase P.

Approved Input Promotion belongs to Phase G. Candidate creation and actual
model generation belong to Phases H–J.

---

# Phase P Work Breakdown

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

---

# P2 Architecture Boundary

P2 shall define:

- project identity
- required project metadata
- Project Manifest contract
- Project Workspace directory structure
- persistence boundaries
- reopening behavior
- project isolation
- references from later sources, runs and artifacts to their project

The concrete architecture is not yet accepted.

Before P2 implementation begins:

1. inspect existing implementation structures relevant to persistence,
2. propose architecture alternatives,
3. discuss consequences and trade-offs,
4. obtain explicit project-owner acceptance,
5. document the accepted architecture in ADR-005,
6. review, commit and push ADR-005 locally,
7. begin implementation only after ADR-005 is committed on the authoritative
   branch.

Creating and committing ADR-005 is a scoped architecture-decision update. It
does not trigger a complete SSOT UPDATE.

The complete Collaboration Knowledge Base will be synchronized after P8 and
completion of Phase P.

Do not infer a persistence layout from this handover.

Do not begin P2 implementation before ADR-005 has been discussed and explicitly
accepted.

---

# Next Implementation Step

Start the P2 architecture discussion.

The first decision shall define the Project Manifest and Workspace persistence
boundaries without pulling forward:

- P3 source-registry implementation
- P4 Information Unit storage
- Phase G human approval
- Phases H–J model generation

---

# Starting Prompt for the Next Chat

Continue the Turing Generator in repository
`mz-commits-ai4mbse/SysMLv2-Generator`, branch `main`.

Use GitHub repositories passively. Do not commit, push or directly modify
repository content.

Begin by reading the Collaboration Knowledge Base and verifying the committed
implementation baseline.

Summarize:

- current roadmap phase
- completed implementation
- architecture version
- next implementation step

Do not use previous chat history as a source of truth.

Then begin the P2 architecture discussion for the Project Manifest and
Workspace Structure.

Do not start P2 implementation before the proposed architecture has been
explicitly accepted and recorded in ADR-005.