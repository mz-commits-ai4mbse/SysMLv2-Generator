# Working Rules

<!-- BEGIN WORKING RULE 2026-08-25 FEATURE BRANCH POLICY -->
## Feature-branch policy — effective after WP-12 Golden E2E closeout

The closeout commit containing the 2026-08-25 Golden E2E checkpoint establishes
`main` as the Known-Good fallback branch.

From that point onward:

1. Do not implement new features directly on `main`.
2. Create every bounded implementation scope from current verified `main`.
3. Use a dedicated branch, normally `feature/<finding-or-scope>`.
4. Keep the branch tied to one coherent BLK / SEM / ODS scope where practical.
5. Run focused tests during implementation.
6. Before merge, run the appropriate regression and `git diff --check`.
7. Merge only after explicit Human review / acceptance.
8. Verify `main` after merge.
9. Preserve the ability to return to the Golden E2E baseline at all times.
10. Never use broad staging commands such as `git add .`, `git add -A` or
    `git add --all`.

Recommended baseline tag after the closeout commit:

```text
wp12-golden-e2e-2026-08-25
```

Branch examples:

```text
feature/blk-002-multi-source
feature/sem-015-follow-up
feature/ods-<id>-<short-name>
```
<!-- END WORKING RULE 2026-08-25 FEATURE BRANCH POLICY -->

## Purpose

This document defines the mandatory engineering and collaboration rules for
developing the Turing Generator.

These rules are binding for all future development work, regardless of whether
implementation is performed by a human developer or an AI assistant.

The goal is to ensure:

- architectural consistency
- reproducibility
- traceability
- explicit Human Review authority
- safe reuse of the modular system core
- controlled progress toward the executable prototype

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

No architecture decision becomes accepted project knowledge until it has been:

- discussed
- explicitly accepted by the project owner
- documented in an Architecture Decision Record where required
- transferred into the Collaboration Knowledge Base through the SSOT process

---

# 2. Problem Space vs. Solution Space

The project strictly separates the problem space from the solution space.

## Problem Space

Maintained in the authoritative CATIA SysML v2 model.

Includes:

- Stakeholders
- User Needs
- Stakeholder Requirements
- Use Cases
- System Requirements
- System Functions
- Logical Architecture
- System Design Constraints
- Model Relationships

## Solution Space

Implemented in the repository.

Includes:

- Agent Teams
- Recipes
- Memory Artifacts
- Semantic Processing
- Persistence
- Human Review
- UI
- Model Candidates
- Model Generation
- SysML v2 Generation
- Validation
- Reports
- Output Packages

Repository implementation shall not silently redefine authoritative
requirements.

Implementation evidence may trigger reconciliation work.

It shall not automatically create or change normative engineering knowledge.

---

# 3. Single Responsibility

Every module, agent, recipe and processing stage shall have exactly one clearly
defined responsibility.

Whenever a component starts solving multiple independent problems, it shall be
split into separate modules or explicit subcomponents.

Shared utilities shall not become hidden orchestration layers.

---

# 4. Pipeline Architecture

The pipeline consists of independent processing stages.

A stage may communicate only through explicitly defined and validated artifacts.

Direct access to previous agent conversations or undeclared intermediate state
is forbidden unless explicitly required by an accepted architecture decision.

Every stage shall define:

- input contract
- output contract
- validation behavior
- failure behavior
- traceability behavior
- authority of its output

No stage may silently upgrade a non-authoritative artifact into authoritative
engineering knowledge.

---

# 5. Memory-based Communication

Agent teams communicate through versioned Memory Artifacts.

The complete conversation history of previous agents shall not be forwarded.

Only the relevant, traceable and budgeted context required by the next stage
may be provided.

Memory Artifacts shall preserve:

- source references
- processing provenance
- agent identity or role
- applicable context selection
- confidence or disagreement evidence where relevant
- validation status

---

# 6. Human in the Loop

The system shall never silently invent, approve or authorize engineering
information.

Whenever insufficient evidence exists:

- uncertainty shall be preserved
- ambiguity shall be reported
- missing information shall be documented
- conflicts shall remain explicit
- Human Review shall be requested

Multi-agent agreement, confidence and low variance are review evidence.

They are not publication or promotion authority.

Every publication, promotion or authoritative selection target requires an
explicit persisted Human Review Decision.

The reviewer shall always retain the option to enter detailed review, including
when quick confirmation is offered.

Only an exact `confirm` decision bound to the current target content and all
required validation fingerprints may pass a gate.

A stale decision shall not authorize a changed target.

Automated prioritization or recommendation shall remain advisory until accepted
by the responsible human reviewer.

---

# 7. Explainability and Traceability

Every generated artifact shall be explainable.

Every engineering statement shall be traceable, where applicable, to:

- its Project
- its Source
- its source location
- the relevant Source Projection
- its extraction or derivation provenance
- the relevant Processing Run
- applicable semantic and framework mappings
- candidate and prioritization evidence
- its Human Review Decision
- the resulting Approved Input
- generated model elements and relationships
- validation findings
- published output artifacts

Traceability shall not be reconstructed from filenames, directory names or chat
history.

Traceability references shall use explicit identifiers and validated manifests.

---

# 8. Deterministic Components

Whenever deterministic processing is sufficient, deterministic implementations
shall be preferred over LLM calls.

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
- state reconstruction
- relationship-profile evaluation
- artifact packaging

LLMs shall be used only where semantic interpretation, synthesis or engineering
reasoning is required.

LLM output shall remain subject to deterministic validation and Human Review
where authority is affected.

---

# 9. Architecture Changes

Architecture changes shall never be introduced implicitly.

Every accepted architecture change requires:

- discussion
- explicit agreement by the project owner
- documentation in an Architecture Decision Record where required
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
- project change history
- completed reconciliation milestones
- deferred work

It shall reference authoritative CATIA model elements rather than duplicating
engineering-model content whenever possible.

Feature matrices, temporary reports and presentation artifacts remain
supporting evidence unless explicitly registered as authoritative project
artifacts.

---

# 11. Development Workflow

Each major development phase follows:

```text
Architecture discussion
→ explicit acceptance
→ ADR where required
→ implementation
→ testing
→ review
→ SSOT UPDATE or accepted milestone synchronization
→ next development phase
```

Internal work steps may proceed without a complete SSOT UPDATE when:

- their architecture is already accepted or documented in an ADR
- their implementation is tested and committed
- no critical handover would become unreliable
- no authority boundary is changed implicitly

No later phase may depend on an undefined or unreviewed public contract from an
earlier phase.

---

# 12. Refactoring

Temporary implementations are discouraged.

Whenever feasible, components shall be implemented directly according to the
accepted target architecture.

When consecutive work steps modify the same file and can be safely implemented
and reviewed together, they should be grouped to avoid unnecessary replacement
cycles.

Intermediate increments remain appropriate when they:

- establish an independently testable contract
- reduce implementation risk
- preserve a stable handover point
- enable meaningful Human Review
- prevent later destructive refactoring

Refactoring shall preserve public contracts unless a reviewed architecture
change explicitly replaces them.

---

# 13. Repository Philosophy

The repository shall remain modular.

Large monolithic files should be avoided where decomposition preserves a clear
public contract.

Each folder shall represent a clearly identifiable architectural
responsibility.

The reusable system core and task-specific configuration shall remain
distinguishable.

Task-specific knowledge shall not be hard-coded into shared infrastructure when
it can be represented through validated configuration, recipes, profiles or
agent definitions.

---

# 14. Current Development Roadmap

The official roadmap is maintained in:

`collaboration/roadmap.md`

This file defines working rules and shall not independently redefine roadmap
status.

The current executable prototype critical path is:

```text
Phase G
→ Phase H
→ Phase I
→ Phase J
→ Phase K
→ Phase L
```

The target date for the complete executable prototype is:

`2026-08-14`

Phase status, dates and ordering shall be taken from the roadmap.

---

# 15. Rule Changes

Changes to this document require:

- explicit discussion
- explicit agreement
- SSOT UPDATE

before becoming valid.

A roadmap decision does not automatically change a working rule.

A working-rule change shall be stated explicitly.

---

# 16. SSOT UPDATE

SSOT UPDATE is the official synchronization process of the Collaboration
Knowledge Base.

Its purpose is to transfer accepted project knowledge and verified
implementation status into authoritative coordination documents.

An SSOT UPDATE shall:

1. review the completed work
2. identify accepted decisions
3. ignore rejected ideas and unaccepted brainstorming results
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

An earlier SSOT UPDATE may be performed when:

- explicitly requested by the project owner
- a substantial architecture baseline has been completed
- a presentation or external review creates accepted project feedback
- chat or handover performance would make continuation unreliable
- a critical handover is required

Current synchronization status:

- Phase F is completed and synchronized
- Phase P is completed and synchronized
- the Post-Phase-P Reconciliation Gate is completed and synchronized
- Phase G is the active phase
- the next update is due after a major implementation milestone or critical
  handover need

## Repository Synchronization

After every SSOT UPDATE, the project owner shall commit and push all relevant
local changes.

After the push, the repository shall be checked to verify:

- the Collaboration Knowledge Base reflects committed implementation
- referenced commits exist
- obsolete implementation descriptions were removed
- version numbers are consistent
- `HEAD` and `origin/main` are synchronized

---

# 17. Project Sources and Information Roles

Every persisted Source shall be assigned to exactly one Project.

A permanent unassigned Source pool is not permitted.

Project identity and Source identity shall remain separate.

## Engineering Source

An `engineering_source` may:

- create source-traceable engineering Information Units
- create terminology and framework-mapping candidates
- contribute to clearly marked Preliminary Coverage
- contribute to later generation only after the responsible review and
  promotion gates

## Context-only Source

A `context_only` Source may explain product context, terminology or
interpretation.

It shall not:

- create engineering Information Units
- create framework assignments
- satisfy coverage
- satisfy readiness
- contribute model content

## Coverage and Readiness

Preliminary Coverage may describe what unreviewed engineering information
appears to support.

It shall always be labelled as preliminary.

Approved Generation Readiness is separate.

It shall be calculated only from eligible Approved Input and applicable
reviewed evidence.

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

Broad staging commands such as `git add .` or `git add -A` shall not be proposed
for a mixed working tree.

External repositories remain non-authoritative unless their role and authority
are explicitly registered.

The project owner retains final authority over every modification, commit and
push.

---

# 19. Textual Source-processing Boundary

The MVP semantic-processing boundary is textual information.

Permitted inputs include:

- native textual Sources
- deterministic textual projections
- PDF files with extractable text layers

The following remain outside the executable prototype:

- OCR
- image-only PDF interpretation
- technical-drawing interpretation
- unrestricted multimodal engineering extraction

Support for additional media requires its own accepted architecture,
validation and Human Review design.

Deterministic text projection shall preserve content and source location.

It shall not perform semantic normalization or ontology interpretation.

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

Live ontology queries, automatic ontology updates and unrestricted runtime graph
traversal are not permitted in the MVP.

Complete ontology snapshots shall not be loaded into prompts.

Project glossary changes shall not be performed automatically.

The same normalized term shall not silently represent multiple accepted
meanings within the same project context.

---

# 21. Multi-agent Consensus and Confidence

Semantic confidence shall be based on explicit agent-result agreement and
disagreement evidence, including variance where applicable.

Agent personalities may contribute independent perspectives.

They shall not receive publication or promotion authority.

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

The first Architecture-to-Requirements Reconciliation was completed during the
Post-Phase-P Reconciliation Gate.

That reconciliation established the accepted System-level baseline:

- System Requirements
- System Design Constraints
- System Functions
- Logical Components
- feature and requirement coverage

Phase N retains the final reconciliation after Phases G through L.

The final reconciliation shall:

- inventory architecture decisions introduced after the first reconciliation
- map decisions and capabilities to authoritative CATIA elements
- identify missing, outdated and conflicting requirements
- create traceable requirement and model-change candidates
- distinguish stakeholder need, requirement, design constraint and
  implementation detail
- preserve the accepted derivation chain
- require Human Review before CATIA changes
- confirm CATIA as the only maintained engineering model

Implementation is evidence for reconciliation.

It is not automatic requirement authority.

No implemented feature shall silently become a normative requirement merely
because it exists in code.

---

# 24. Thesis Architecture Documentation

Phase Q shall document:

- the complete development-phase sequence
- every architecture decision from earlier and later phases
- decision context and alternatives
- rationale and consequences
- requirement and implementation traceability
- semantic and ontology architecture
- Human Review architecture
- Approved Input architecture
- model-candidate architecture
- relationship prioritization and model comparability
- SysML v2 generation and validation
- portability evaluation
- relevant literature and standards
- limitations and deferred work

The thesis documentation shall be based on the reconciled authoritative model
after Phase N.

Architecture decisions shall remain documented even when their implementation
is later superseded.

Their status and consequences shall remain explicit.

---

# 25. Approved Input Authority

Approved Input is the only eligible authoritative engineering input for later
model-candidate generation.

Run-owned P9 artifacts, candidate Information Units, consensus reports and
review reports are not Approved Input.

An artifact may become Approved Input only when:

- its source and project references are valid
- its content fingerprint matches the reviewed target
- all required validation fingerprints match
- an eligible Human Review Decision confirms the exact target
- the promotion operation succeeds through the accepted Phase G contract

Approved Input shall preserve traceability to:

- Project
- Source
- Source Projection
- Information Unit or run-owned artifact
- Processing Run where applicable
- Human Review Decision
- validation evidence
- promotion record

Revoked, invalidated or superseded Approved Input shall not remain eligible for
new model-candidate generation.

Phase G shall not generate model candidates or SysML v2.

---

# 26. Model Relationship Semantics and Comparability

Model relationships shall be treated as explicit engineering decisions.

The system shall not silently collapse distinct relationship semantics into a
generic link.

Relevant relationship concepts include:

- dependency
- allocation
- flow
- refinement-related relationships
- derivation-related relationships
- framework-specific relationships

Where multiple relationship types appear plausible or are used
near-synonymously, the system shall preserve alternatives and provide:

- candidate relationship type
- source and target
- semantic intent
- supporting evidence
- priority
- prioritization rationale
- comparability impact
- profile-conformance result
- Human Review status

A versioned Model Structure and Comparability Profile shall define:

- preferred model structure
- canonical relationship choices
- required comparison anchors
- allowed structural variation
- prioritization criteria
- permitted exceptions
- review requirements for deviations

Relationship prioritization remains advisory.

Human Review shall authorize the accepted relationship choice and any accepted
exception.

The purpose is to support meaningful comparison between:

- related products
- product variants
- independently generated models
- repeated generation runs

Validation shall report inconsistent or unsupported relationship semantics.

---

# 27. Task Profile Portability

The system shall distinguish reusable core infrastructure from task-specific
engineering configuration.

Reusable core candidates include:

- Project Workspace
- Source Registry
- Processing Runs
- artifact persistence
- Human Review
- evidence and traceability
- dashboard
- agent execution
- publication gates

Task-specific candidates include:

- project context files
- framework templates
- support profiles
- semantic vocabularies
- agent profiles
- recipes
- task definitions
- validation rules
- output contracts
- review criteria

Phase R shall evaluate portability through a Task Profile Replacement Manifest.

The manifest shall identify for every relevant artifact:

- path
- role
- core or task-specific classification
- unchanged, adapted or replaced status
- dependencies
- required validation
- required code changes
- reused and new tests

The alternate evaluation task is Requirements Quality and Completeness
Analysis.

The portability claim shall be evaluated using measured implementation evidence.

It shall not be asserted solely from architectural intention.

---

# 28. Project Affinity Recommendation

Project Affinity Recommendation is a low-priority post-Phase-R capability.

Before persistent Source registration, the system may temporarily analyze
selected data and recommend Projects that appear suitable.

The recommendation may consider:

- project description
- framework template
- existing Sources
- accepted project vocabulary
- framework coverage
- semantic similarity

The recommendation shall:

- remain advisory
- provide a ranked result
- provide a rationale or evidence summary
- allow explicit user confirmation or override
- avoid persistent Source registration before Project selection

The system shall not assign a Project automatically.

The feature shall not introduce a permanent unassigned Source pool.

Every persisted Source shall remain assigned to exactly one Project.

---

# 29. Prototype Delivery Integrity

The executable prototype target is 2026-08-14.

Schedule pressure shall not justify weakening:

- Human Review authority
- traceability
- project isolation
- deterministic validation
- publication gates
- model consistency
- explicit artifact contracts

When scope reduction is necessary, non-critical refinements shall be deferred
before core integrity controls are weakened.

Deferred refinements shall be documented explicitly.

A phase may be declared complete only when its accepted exit criteria have been
met or explicitly revised by the project owner.
