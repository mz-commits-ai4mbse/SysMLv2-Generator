# Working Rules

## Purpose

This document defines the mandatory engineering rules for developing the Turing Generator.

These rules are binding for all future development work, regardless of whether implementation is performed by a human developer or an AI assistant.

The goal is to ensure architectural consistency, reproducibility and traceability throughout the project.

---

# 1. Single Source of Truth

The following priority always applies.

1. CATIA SysML v2 model
2. Repository source code
3. Collaboration Knowledge Base
4. Chat conversations

Chat conversations are never authoritative.

CATIA is always authoritative for engineering knowledge. If required engineering information is not yet available in CATIA, the temporary shadow model under `model/` may supplement it until Phase N. The shadow model shall never override or contradict CATIA.

The committed repository source on the authoritative branch represents implementation reality. Local uncommitted changes are not authoritative implementation state.

No architectural decision becomes valid until it has been transferred into the Collaboration Knowledge Base using the SSOT UPDATE process.

---

# 2. Problem Space vs. Solution Space

The project strictly separates the problem space from the solution space.

## Problem Space

Maintained exclusively inside the SysML v2 model.

Includes:

- Stakeholders
- User Needs
- Stakeholder Requirements
- Use Cases
- System Architecture

These elements shall never be duplicated manually inside repository documentation.

## Solution Space

Implemented inside the repository.

Includes:

- Agent Teams
- Recipes
- Memory Artifacts
- Consensus Mechanisms
- UI
- Model Generation
- Validation
- Reports

---

# 3. Single Responsibility

Every module, agent and processing stage shall have exactly one clearly defined responsibility.

Responsibilities shall never overlap.

Whenever a component starts solving multiple independent problems, it shall be split into separate modules.

---

# 4. Pipeline Architecture

The pipeline consists of independent processing stages.

A stage may only communicate through explicitly defined artifacts.

Direct access to previous agent outputs is forbidden unless explicitly required by the architecture.

---

# 5. Memory-Based Communication

Agent teams communicate exclusively through Memory Artifacts.

Example:

Interpretation Team

↓

Interpretation Memory

↓

Evidence Team

↓

Evidence Memory

↓

Derivation Team

↓

Derivation Memory

↓

Completeness Team

↓

Completeness Memory

The complete conversation history of previous agents must never be forwarded.

---

# 6. Human in the Loop

The system shall never silently invent engineering information.

Whenever insufficient evidence exists:

- uncertainty shall be preserved
- ambiguity shall be reported
- missing information shall be documented
- human review shall be requested

---

# 7. Explainability

Every generated artifact shall be explainable.

Every engineering statement shall be traceable back to its originating source.

---

# 8. Deterministic Components

Whenever deterministic processing is sufficient, deterministic implementations shall be preferred over LLM calls.

Examples include:

- report generation
- file handling
- artifact conversion
- formatting
- validation
- persistence

LLMs shall only be used where semantic reasoning is actually required.

---

# 9. Architecture Changes

Architectural changes shall never be introduced implicitly.

Every accepted architecture change requires

- discussion
- explicit agreement
- SSOT UPDATE

before becoming part of the project.

---

# 10. Project Knowledge

The Collaboration Knowledge Base documents

- current project status
- accepted decisions
- roadmap
- working rules
- project handovers

It shall never duplicate the SysML model.

Whenever possible, it references model element IDs instead of copying model content.

---

# 11. Development Workflow

Each major development phase follows the same process.

Implementation

↓

Testing

↓

Review

↓

SSOT UPDATE

↓

Next Development Phase

Development continues only after the SSOT has been updated.

---

# 12. Refactoring

Temporary implementations are discouraged.

Whenever feasible, components shall be implemented directly according to the target architecture.

Large temporary implementations that require later restructuring should be avoided.

---

# 13. Repository Philosophy

The repository shall remain modular.

Large monolithic files should be avoided.

Each folder should represent a clearly identifiable architectural responsibility.

---

# 14. Current Development Roadmap

The official roadmap is maintained in

roadmap.md

This file shall not contain roadmap information.

---

# 15. Rule Changes

Changes to this document require

- explicit discussion
- explicit agreement
- SSOT UPDATE

before becoming valid.

# 16. SSOT UPDATE

SSOT UPDATE is the official synchronization process of the Collaboration Knowledge Base.

Its purpose is to transfer accepted engineering knowledge from implementation work into the authoritative project documentation.

An SSOT UPDATE shall perform the following steps.

1. Review the completed work.

2. Identify accepted engineering decisions.

3. Ignore rejected ideas and brainstorming results.

4. Determine the current implementation status.

5. Check whether the roadmap has changed.

6. Identify affected Collaboration Knowledge Base documents.

7. Update the affected documents.

8. Update version numbers where required.

9. Update the project change log.

10. Generate a new current_chat_handover.md.

Only explicitly accepted decisions may become part of the Collaboration Knowledge Base.

Chat conversations alone never change the SSOT.

The Collaboration Knowledge Base should normally be updated through an explicit SSOT UPDATE.

Direct manual modifications are permitted when intentionally performed by the project owner.

During an SSOT UPDATE, the assistant shall generate explicit modifications for every affected Collaboration Knowledge Base file.

For every Collaboration file exactly one of the following outcomes shall be produced:

- No changes required.
- Apply the following modifications.

An SSOT UPDATE is complete only after all affected files have been processed accordingly.

## Repository Synchronization

After every SSOT UPDATE, the project owner shall be reminded to commit and push
all relevant local changes to the authoritative GitHub repository.

After the changes have been pushed, the repository shall be checked to verify that

- the Collaboration Knowledge Base reflects the committed repository state,
- referenced implementation changes are present,
- obsolete implementation descriptions have been removed,
- the repository is synchronized with the current SSOT.

Local uncommitted files shall never be assumed to represent the authoritative implementation state.

---

# 17. Project Sources and Information Roles

Every source ingested by the Project Workspace shall be assigned to exactly one project. A permanent unassigned source pool is not permitted.

Project data shall use explicit source roles.

## Engineering Source

An engineering source may produce source-traceable information units and may contribute to clearly marked preliminary framework coverage.

It may contribute to generation readiness or model generation only after the relevant information has been reviewed and approved by a human through the Phase G workflow.

## Context-only Source

A context-only source may explain product context, terminology or interpretation. It shall not

- create engineering evidence for model generation,
- satisfy framework coverage,
- satisfy readiness criteria,
- or contribute model content.

Context-only information shall remain visibly distinguishable and traceable to its source.

## Coverage and Readiness

Preliminary coverage may describe what unreviewed engineering information appears to support, but it shall always be labelled as preliminary.

Approved readiness is a separate state and shall be calculated only from human-approved engineering information.

No UI state, generated report or consensus result may silently promote unreviewed information into approved model-generation input.
