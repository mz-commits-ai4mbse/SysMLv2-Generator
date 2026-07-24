# Current Project State

## Purpose

This document describes the current committed implementation reality of the
Turing Generator. It is updated during every `SSOT UPDATE` and shall not
redefine engineering knowledge contained in the authoritative CATIA SysML v2
model.

---

# Project

Project

Turing Generator

Repository

`mz-commits-ai4mbse/SysMLv2-Generator`

Current Branch

`main`

Verified Implementation Commit

`0c8ba428e7e6469e410b541c114d7a5a9474321c`

Architecture Version

1.0

Knowledge Base Version

1.3

Implementation Version

0.7

Current Roadmap Version

1.3

Current Development Phase

P – Project Workspace

Current Status

P1–P4 Completed — P5 Next

Last SSOT Update

2026-07-24

---

# Current Objective

Continue the project-oriented processing architecture around the completed
agentic ingestion pipeline.

P1 through P4 established the framework, project workspace, source registry
and semantic information-processing foundation.

The immediate focus is:

P5 — Processing State and Artifact Organization

Phase P remains active. Approved Input Promotion, model candidates, model
generation and SysML v2 code generation remain assigned to later phases.

---

# Current Engineering Priorities

Priority 1

Define the P5 processing-state model and artifact-organization boundaries
before implementation depends on them.

Priority 2

Integrate the completed project, source, projection, semantic, review and
mapping artifacts into explicit project processing states without weakening
their existing traceability or authority boundaries.

Priority 3

Continue through P6 coverage, P7 dashboard and P8 phase review before leaving
Phase P.

Priority 4

Preserve the mandatory Human-in-the-Loop boundary. Agent consensus, confidence
or low variance shall never independently authorize publication or model
generation.

---

# Verified Implementation Baseline

## Phase F — Agentic Ingestion UI

Phase F remains complete and verified at:

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

## P1 — Framework Template Definition

P1 is complete and verified at:

`82b5cbbe9bedac77a4b02928a596ea8fbdacc873`

Implemented capabilities include:

- reviewed non-normative Apollo 11 structural reference
- explicit accepted and rejected reference patterns
- versioned framework template `TURING_RFLP_FRAMEWORK`
- stable identifiers for 3 framework levels and 12 mapping targets
- zero-to-many framework assignments
- rejection of unknown framework targets
- exclusion of `context_only` sources from framework mapping
- deterministic framework-template validation

## P2 — Project Manifest and Workspace Structure

P2 architecture is documented in:

`collaboration/decisions/ADR-005-project-workspace-architecture.md`

P2 implementation is verified through:

`36184a2d90db349555ac3bd64ccd5c27ecb68cec`

Implemented capabilities include:

- six-digit project identities
- project display-name uniqueness
- explicit separation of internal project ID and display name
- immutable framework-template reference
- strict Project Manifest validation
- project creation, loading, scanning and isolation
- safe project paths and symlink rejection
- deterministic project reopening

## P3 — Project Source Registry

P3 architecture is documented in:

`collaboration/decisions/ADR-010-project-source-registry-architecture.md`

The textual processing boundary is documented in:

`collaboration/decisions/ADR-009-textual-source-processing-boundary.md`

P3 implementation is verified through:

`55cc4f104082ecfef70b3dcdeb8f28406ed95105`

Implemented capabilities include:

- mandatory project assignment for every source
- project-local six-digit source identifiers
- immutable source manifests
- exact content hashes and source metadata
- `engineering_source` and `context_only` roles
- duplicate-content rejection
- safe source persistence and deterministic scans
- strict separation of project identity and source identity

## P4 — Framework-mapped Heterogeneous Information Units

P4 semantic architecture is documented in:

`collaboration/decisions/ADR-011-semantic-information-unit-and-ontology-boundary.md`

P4 is complete and verified at:

`0c8ba428e7e6469e410b541c114d7a5a9474321c`

Verification:

- complete automated test suite: 2594 passed
- staged implementation scope: 111 files
- own-source diff validation: passed
- pinned external ontology integrity validation: passed
- branch synchronization: `HEAD == origin/main`

Implemented P4 capabilities include:

- deterministic source projections for text, Markdown, JSON, CSV, TSV and PDF
  text layers
- strict projection manifests, locators and project-local repositories
- pinned BFO 2020 and IOF Core 202602 ontology snapshots
- explicit ontology registry and deterministic derived reference-concept index
- 236 indexed external reference concepts
- Turing Core Vocabulary with explicit authority boundaries
- project-specific glossary candidates and terminology decisions
- immutable, source-traceable Information Units
- semantic extraction candidate contracts
- multi-agent semantic consensus with explicit disagreement and variance
- terminology-mapping candidates with reference validation
- framework-assignment candidates with reference validation
- immutable Human Review Decisions
- exact target-content and validation-fingerprint binding
- project-local review persistence and publication gates
- deterministic, auditable token budgeting
- fail-closed behavior when required context cannot fit

---

# Current Architecture Baseline

## Engineering Authority

The CATIA SysML v2 model remains authoritative for:

- stakeholders
- user needs
- stakeholder requirements
- use cases
- system architecture
- model relationships

The temporary SYSIDE shadow model may supplement missing information until
Phase N. It shall never override or contradict CATIA.

The committed repository is authoritative for implementation reality.

The Collaboration Knowledge Base is authoritative for roadmap, coordination,
accepted decisions and working rules.

## Accepted Framework

The framework contains:

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

Apollo 11 remains a non-normative reference. Its CoSMA framework, package
layout, engineering content and identifiers were not transferred.

## Source-processing Boundary

The supported MVP engineering-processing boundary is textual information.

Native textual files and deterministic text projections may enter semantic
processing.

PDF processing is limited to extractable text layers. OCR, image understanding,
technical-drawing interpretation and unrestricted multimodal extraction remain
outside the MVP.

Supporting additional non-textual engineering media requires a separate,
explicit architecture and validation decision.

## Semantic Authority

The semantic authority hierarchy is:

1. authoritative project engineering knowledge in CATIA
2. explicitly accepted project terminology decisions
3. Turing Core Vocabulary
4. curated external reference concepts from registered ontology snapshots

BFO and IOF are reference systems. They do not override project engineering
authority and are not loaded completely into prompts.

External ontology mappings remain explicit, reviewable candidates until
accepted.

## Human Review Boundary

Multi-agent agreement, confidence level and variance are evidence for review,
not publication authority.

Every publication target requires an explicit Human Review Decision.

Quick confirmation is permitted only for eligible, reference-valid targets.
The user shall always retain the option to enter detailed review.

Medium or low confidence, disagreement, ambiguity, conflict, invalid
references and incomplete agent runs require detailed review.

Only an exact `confirm` decision bound to the current target-content and
validation fingerprints may pass a publication gate.

## Token-budget Boundary

LLM prompts shall use deterministic relevant context slices.

The system shall not automatically load:

- the complete codebase
- complete ontology snapshots
- unrelated project artifacts

System instructions, output capacity and a safety margin are reserved before
context allocation.

Required context is either included completely or the LLM call is blocked.
Required context shall never be silently truncated.

Optional context is selected deterministically and every omission remains
auditable.

---

# Phase P Work Breakdown

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

---

# Not Yet Implemented

- unified project processing-state model
- consolidated artifact organization across the P1–P4 repositories
- framework coverage and preliminary readiness calculation
- Project Dashboard
- Approved Input Promotion
- Model Candidate Layer
- model generation
- SysML v2 code generation
- validation and export
- CATIA synchronization
- systematic requirements reconciliation against accepted architecture
  decisions

---

# Current Known Limitations and Risks

## Active

- P1–P4 artifacts are individually persisted but not yet unified through a
  project-wide processing-state model.
- Full-team LLM execution still requires operational performance and token
  measurements beyond deterministic budgeting.
- The authoritative CATIA model does not yet contain requirements for every
  accepted and planned capability introduced through architecture decisions.

## Controlled by Design

- projects and sources use separate identities
- source and artifact content is hash-bound
- cross-project mixing is rejected
- unknown framework and ontology references are rejected
- context-only sources cannot create engineering evidence
- semantic candidates remain non-authoritative until human review
- consensus and confidence cannot bypass human approval
- required prompt context cannot be silently truncated
- external ontology snapshots are pinned and integrity-checked
- CATIA remains authoritative for engineering knowledge

---

# Planned Phase N Model Reconciliation

Phase N shall include a dedicated work package:

Architecture-to-Requirements Reconciliation

Purpose:

Reconcile the authoritative engineering model with all accepted architecture
decisions and the implemented and planned system capabilities.

The work package shall:

1. inventory all accepted architecture decisions from the complete project
   history
2. map each decision and capability to existing Stakeholder Requirements,
   System Requirements, Use Cases and downstream model elements
3. identify uncovered or outdated requirements
4. create traceable requirement and model-change candidates
5. distinguish stakeholder need, requirement, design constraint and
   implementation detail
6. review every candidate with the project owner
7. update CATIA only after explicit acceptance
8. record traceability from accepted model elements back to their decision and
   implementation evidence

The implemented system is evidence for the reconciliation. It is not
automatically normative and shall not silently create requirements.

---

# Next Milestone

P5 — Processing State and Artifact Organization

Before implementation:

- inspect the committed P1–P4 artifact repositories
- define canonical processing states and allowed transitions
- define project-level aggregation without duplicating artifact authority
- define failure, retry, supersession and reopening behavior
- preserve exact project, source, projection, information-unit and review
  traceability
- discuss alternatives and consequences
- record the accepted architecture before implementation depends on it

---

# Repository Collaboration Workflow

External GitHub repositories and repository links are used passively for
inspection only.

AI assistants shall not commit, push or directly modify GitHub repository
content.

Repository changes are applied, reviewed, committed and pushed locally by the
project owner.

AI assistants act as implementation guides and identify every affected file by
its repository-relative path before proposing a change.

---

# SSOT Update Cadence

A complete SSOT UPDATE is normally performed after completion of a major
roadmap phase.

This update is an explicitly requested intermediate synchronization after P4
because P4 introduced a substantial semantic architecture baseline and a new
handover is required.

The next regular SSOT UPDATE remains due after P8 and completion of Phase P,
unless the project owner explicitly requests an earlier update or a critical
handover need arises.

---

# Reference Documents

- Roadmap: `roadmap.md`
- Working Rules: `working_rules.md`
- Architecture Decisions: `decisions/`
- Model Registry: `model_registry.json`
- Handover: `handovers/current_chat_handover.md`
- Framework Template: `../context/frameworks/turing_rflp_framework.json`
- Ontology Registry: `../context/semantics/ontology_registry.json`
- Turing Core Vocabulary:
  `../context/semantics/turing_core_vocabulary.json`