# Working Rules

## Purpose

This document defines the mandatory engineering rules for developing the
Turing Generator.

These rules are binding for all future development work, regardless of whether
implementation is performed by a human developer or an AI assistant.

The goal is to ensure architectural consistency, reproducibility and
traceability throughout the project.

---

# 1. Single Source of Truth

The following authority hierarchy always applies:

1. CATIA SysML v2 model for engineering knowledge
2. committed repository for implementation reality
3. Collaboration Knowledge Base for coordination and accepted decisions
4. chat conversations and generated temporary artifacts

Chat conversations are never authoritative.

If required engineering information is unavailable in CATIA, the temporary
shadow model under `model/` may supplement it until Phase N.

The shadow model shall never override or contradict CATIA.

Local uncommitted changes are not authoritative implementation state.

No architecture decision becomes accepted project knowledge until it has been
documented in an Architecture Decision Record and transferred into the
Collaboration Knowledge Base through the SSOT process.

---

# 2. Problem Space vs. Solution Space

The project strictly separates the problem space from the solution space.

## Problem Space

Maintained in the authoritative SysML v2 model.

Includes:

- Stakeholders
- User Needs
- Stakeholder Requirements
- Use Cases
- System Requirements
- System Architecture
- Model Relationships

## Solution Space

Implemented in the repository.

Includes:

- Agent Teams
- Recipes
- Memory Artifacts
- Consensus Mechanisms
- Semantic Processing
- Persistence
- UI
- Model Generation
- Validation
- Reports

Repository implementation shall not silently redefine authoritative
requirements.

---

# 3. Single Responsibility

Every module, agent and processing stage shall have exactly one clearly defined
responsibility.

Whenever a component starts solving multiple independent problems, it shall be
split into separate modules.

---

# 4. Pipeline Architecture

The pipeline consists of independent processing stages.

A stage may communicate only through explicitly defined, validated artifacts.

Direct access to previous agent conversations or undeclared intermediate state
is forbidden unless explicitly required by an accepted architecture decision.

---

# 5. Memory-Based Communication

Agent teams communicate through versioned Memory Artifacts.

The complete conversation history of previous agents shall not be forwarded.

Only the relevant, traceable and budgeted context required by the next stage
may be provided.

---

# 6. Human in the Loop

The system shall never silently invent or authorize engineering information.

Whenever insufficient evidence exists:

- uncertainty shall be preserved
- ambiguity shall be reported
- missing information shall be documented
- conflicts shall remain explicit
- Human Review shall be requested

Multi-agent agreement, confidence and low variance are review evidence. They
are not publication authority.

Every publication target requires an explicit persisted Human Review Decision.

The reviewer shall always retain the option to enter detailed review, including
when quick confirmation is offered.

Only an exact `confirm` decision bound to the current target-content and
reference-validation fingerprints may pass a publication gate.

---

# 7. Explainability and Traceability

Every generated artifact shall be explainable.

Every engineering statement shall be traceable to:

- its project
- its source
- its source location
- the relevant source projection
- its extraction or derivation provenance
- applicable semantic and framework mappings
- its Human Review Decision where required

Traceability shall not be reconstructed from filenames or chat history.

---

# 8. Deterministic Components

Whenever deterministic processing is sufficient, deterministic
implementations shall be preferred over LLM calls.

Examples include:

- report generation
- file handling
- text projection
- identifier allocation
- artifact conversion
- formatting
- validation
- persistence
- hashing
- prompt-context selection

LLMs shall be used only where semantic interpretation or reasoning is required.

---

# 9. Architecture Changes

Architecture changes shall never be introduced implicitly.

Every accepted architecture change requires:

- discussion
- explicit agreement by the project owner
- documentation in an Architecture Decision Record
- local review
- commit and push by the project owner

The accepted ADR shall be committed before implementation depends on the
architecture decision.

A complete synchronization of the Collaboration Knowledge Base is performed
during the next scheduled SSOT UPDATE.

A separate full SSOT UPDATE is not required for every internal roadmap step.

---

# 10. Project Knowledge

The Collaboration Knowledge Base documents:

- current project status
- accepted decisions
- roadmap
- working rules
- source authority
- project handovers
- change history

It shall reference authoritative model elements rather than duplicating
engineering-model content whenever possible.

---

# 11. Development Workflow

Each major development phase follows:

Implementation

↓

Testing

↓

Review

↓

SSOT UPDATE

↓

Next Development Phase

Internal work steps may proceed without a complete SSOT UPDATE when:

- their architecture is already accepted or documented in an ADR
- their implementation is tested and committed
- no critical handover would become unreliable

---

# 12. Refactoring

Temporary implementations are discouraged.

Whenever feasible, components shall be implemented directly according to the
accepted target architecture.

When consecutive work steps modify the same file and can be safely implemented
and reviewed together, they should be grouped to avoid unnecessary replacement
cycles.

Intermediate increments remain appropriate when they establish an independently
testable contract, reduce implementation risk or enable meaningful Human
Review.

---

# 13. Repository Philosophy

The repository shall remain modular.

Large monolithic files should be avoided where decomposition preserves a clear
public contract.

Each folder shall represent a clearly identifiable architectural
responsibility.

---

# 14. Current Development Roadmap

The official roadmap is maintained in:

`collaboration/roadmap.md`

This file defines working rules and shall not independently redefine roadmap
status.

---

# 15. Rule Changes

Changes to this document require:

- explicit discussion
- explicit agreement
- SSOT UPDATE

before becoming valid.

---

# 16. SSOT UPDATE

SSOT UPDATE is the official synchronization process of the Collaboration
Knowledge Base.

Its purpose is to transfer accepted project knowledge and verified
implementation status into authoritative coordination documents.

An SSOT UPDATE shall:

1. review the completed work
2. identify accepted decisions
3. ignore rejected ideas and brainstorming results
4. verify the committed implementation status
5. check whether the roadmap changed
6. identify affected Collaboration Knowledge Base documents
7. update every affected document
8. update version numbers where required
9. update the project change log
10. generate a new `current_chat_handover.md`
11. validate all changed files
12. commit, push and verify the synchronization

Only explicitly accepted decisions may become part of the Collaboration
Knowledge Base.

Chat conversations alone never change the SSOT.

For every Collaboration file, exactly one outcome shall be produced:

- no changes required
- apply the following modifications

## Update Cadence

A regular SSOT UPDATE is performed after completion of a complete major roadmap
phase.

Internal work steps within a phase do not normally require their own full SSOT
UPDATE.

An earlier SSOT UPDATE may be performed when:

- explicitly requested by the project owner
- a substantial architecture baseline has been completed
- chat or handover performance would make continuation unreliable
- a critical handover is required

For the current Phase P:

- P1–P4 are completed and synchronized through the 2026-07-24 update
- P5–P8 remain
- the next regular SSOT UPDATE remains due after P8

## Repository Synchronization

After every SSOT UPDATE, the project owner shall commit and push all relevant
local changes.

After the push, the repository shall be checked to verify:

- the Collaboration Knowledge Base reflects committed implementation
- referenced commits exist
- obsolete implementation descriptions were removed
- `HEAD` and `origin/main` are synchronized

---

# 17. Project Sources and Information Roles

Every ingested source shall be assigned to exactly one project.

A permanent unassigned source pool is not permitted.

Project identity and source identity shall remain separate.

## Engineering Source

An `engineering_source` may:

- create source-traceable engineering Information Units
- create terminology and framework-mapping candidates
- contribute to clearly marked preliminary coverage
- contribute to later generation only after the responsible review and
  promotion gates

## Context-only Source

A `context_only` source may explain product context, terminology or
interpretation.

It shall not:

- create engineering Information Units
- create framework assignments
- satisfy coverage
- satisfy readiness
- contribute model content

## Coverage and Readiness

Preliminary coverage may describe what unreviewed engineering information
appears to support, but it shall always be labelled as preliminary.

Approved readiness is separate and shall be calculated only from
human-approved engineering information.

No UI state, report, confidence or consensus result may silently promote
unreviewed information.

---

# 18. Repository Collaboration Workflow

GitHub repositories and repository links are used passively by AI assistants.

Permitted passive actions include:

- reading repository files
- inspecting branches and committed revisions
- reviewing public reference repositories
- comparing committed implementation states
- verifying a commit after the project owner pushes it

AI assistants shall not:

- directly modify GitHub repository content
- create or update remote branches
- commit or push changes
- open or merge pull requests
- use GitHub write APIs
- stage files in the project owner's working tree
- perform destructive cleanup without explicit, resolved scope

All repository changes shall be:

1. proposed with affected repository-relative paths
2. applied locally by the project owner
3. reviewed locally
4. tested locally
5. staged explicitly by path
6. committed locally by the project owner
7. pushed by the project owner
8. verified passively after the push

Unless the project owner explicitly requests a grouped change, modifications
shall be presented one file at a time.

Broad staging commands such as `git add .` or `git add -A` shall not be
proposed for a mixed working tree.

External repositories remain non-authoritative unless their role and authority
are explicitly registered.

The project owner retains final authority over every modification, commit and
push.

---

# 19. Textual Source-processing Boundary

The MVP semantic-processing boundary is textual information.

Permitted inputs include:

- native textual sources
- deterministic textual projections
- PDF files with extractable text layers

The following remain outside the MVP:

- OCR
- image-only PDF interpretation
- technical-drawing interpretation
- unrestricted multimodal engineering extraction

Support for additional media requires its own accepted architecture,
validation and Human Review design.

Deterministic text projection shall preserve content and source location. It
shall not perform semantic normalization or ontology interpretation.

---

# 20. Semantic Authority and Ontology Use

The semantic authority hierarchy is:

1. authoritative project engineering knowledge
2. accepted project terminology decisions
3. Turing Core Vocabulary
4. curated external reference concepts

BFO 2020 and IOF Core 202602 are registered reference systems.

They shall not override project engineering authority.

External ontology mappings are explicit candidates until reviewed.

Live ontology queries, automatic ontology updates and unrestricted runtime
graph traversal are not permitted in the MVP.

Complete ontology snapshots shall not be loaded into prompts.

Project glossary changes shall not be performed automatically.

---

# 21. Multi-agent Consensus and Confidence

Semantic confidence shall be based on explicit agent-result agreement and
disagreement evidence, including variance where applicable.

Agent personalities may contribute independent perspectives but shall not
receive publication authority.

The system shall preserve:

- individual agent results
- run completeness
- consensus level
- disagreement
- variance
- review recommendation

High confidence, unanimous consensus or low variance shall not bypass Human
Review.

---

# 22. Prompt and Token Budgeting

LLM prompts shall use deterministic, relevant context slices.

The complete codebase, complete ontology snapshots and unrelated project
artifacts shall not be loaded automatically.

Every prompt budget shall reserve capacity for:

- system instructions
- expected output
- safety margin

Required context shall be included completely or the LLM invocation shall be
blocked.

Required context shall never be silently truncated.

Optional context shall be selected deterministically according to the accepted
priority policy.

Selected and omitted references shall remain auditable.

---

# 23. Architecture-to-Requirements Reconciliation

Phase N shall reconcile all accepted architecture decisions and implemented
and planned capabilities with the authoritative engineering model.

The reconciliation shall:

- inventory all accepted architecture decisions
- map decisions and capabilities to model elements
- identify missing, outdated and conflicting requirements
- create traceable requirement and model-change candidates
- distinguish stakeholder need, requirement, design constraint and
  implementation detail
- preserve the accepted derivation chain
- require Human Review before CATIA changes

Implementation is evidence for reconciliation. It is not automatic requirement
authority.

No existing feature shall silently become a normative requirement merely
because it has already been implemented.

---

# 24. Thesis Architecture Documentation

Phase Q shall document:

- every architecture decision from Phases A–P
- every architecture decision accepted after Phase P
- decision context and alternatives
- rationale and consequences
- requirement and implementation traceability
- relevant literature, standards and ontology sources
- limitations and deferred work

The thesis documentation shall be based on the reconciled authoritative model
after Phase N.

Architecture decisions shall remain documented even when their implementation
is later superseded, with status and consequences made explicit.