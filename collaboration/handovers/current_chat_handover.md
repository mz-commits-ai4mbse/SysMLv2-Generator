# Current Chat Handover

## Purpose

This document is the authoritative starting point for the next implementation
chat after Phase-I completion.

Use it together with the committed repository, the Collaboration Knowledge Base
and the authoritative CATIA SysML v2 model.

---

# Project

Project

Turing Generator

Repository

`mz-commits-ai4mbse/SysMLv2-Generator`

Branch

`main`

Verified Implementation Reference

`commit containing this SSOT update` — Phase I completion

Last Prior Committed Checkpoint

`ff4ee4e038942f9ee267eb2ad6a6daa600b09e6d` — ADR-019 accepted Phase-I architecture

Architecture Version

1.6

Knowledge Base Version

1.13

Implementation Version

0.15

Roadmap Version

1.13

Last SSOT Update

2026-08-13

Current Phase

Phase J — SysML v2 Code Generator

Current Status

Phase I completed and verified. Phase J is next.

Verified Automated Test Baseline

```text
Focused I1–I6 regression:
110 passed in 1.07s

Complete repository regression:
5087 passed in 26.00s

git diff --check:
PASS
```

Closed Vertical-slice Target

2026-08-14

Functional Freeze

2026-08-17

Product Demo

2026-08-18

---

# Read Before Starting

Read in this order:

1. `collaboration/current_state.md`
2. `collaboration/roadmap.md`
3. `collaboration/working_rules.md`
4. `collaboration/model_registry.json`
5. `collaboration/decisions/ADR-017-simple-by-default-interaction-and-progressive-disclosure.md`
6. `collaboration/decisions/ADR-018-model-candidate-layer-and-structural-comparability.md`
7. `collaboration/decisions/ADR-019-internal-engineering-model-assembly-architecture.md`
8. `context/sysml/sysml_v2_target_notation.json`
9. `collaboration/change_log.md`
10. this handover

Then inspect the committed Phase-I implementation and existing target-notation
configuration only as required for the Phase-J architecture discussion.

---

# Source Authority

Authority order:

1. CATIA SysML v2 model for engineering knowledge
2. committed repository for implementation reality
3. Collaboration Knowledge Base for coordination and accepted decisions
4. chat history and temporary generated artifacts

The temporary SYSIDE shadow model may supplement missing CATIA information
until Phase N.

It shall never override or contradict CATIA.

Implementation observations may become Model Element Change Candidates only.
They do not silently create normative engineering knowledge.

---

# Repository Collaboration Workflow

GitHub remains passive for the AI assistant.

The AI assistant shall not:

- directly edit GitHub content
- commit or push
- stage the local working tree
- use broad staging commands
- destructively clean unrelated files

Required workflow:

1. inspect passively
2. name exact repository-relative paths
3. provide deterministic local edits
4. Moritz applies changes locally
5. run focused tests
6. run complete regression only at a major package completion
7. inspect `git diff --check`
8. stage exact intended paths only
9. Moritz commits and pushes
10. verify `HEAD == origin/main`

Never use:

```text
git add .
git add -A
```

---

# Working-tree Caution

The local tree may contain unrelated/generated files including:

- `.DS_Store`
- `__pycache__`
- ingestion reports
- test Projects
- team-run artifacts
- local ZIP / patch files

Do not stage them unless explicitly part of the intended change.

---

# Phase H — Completed Upstream Authority

Phase H remains complete.

Sole production read boundary into Phase I:

```python
ModelCandidateReadService.load_phase_i_input(
    project_id,
    candidate_set_id,
) -> ModelCandidateAssemblyInput
```

The gate revalidates active Approved Input authority, exact Candidate review
authorization, structural-profile bindings, relationship endpoints, accepted
exceptions and project isolation.

Phase-I implementation enriched this DTO with:

```text
framework_template_reference
derivation_rules_reference
```

These references already existed in the Candidate Set manifest. The enrichment
keeps Phase I inside the sole H→I authority boundary.

---

# Phase I — Completed Baseline

Architecture decision:

`collaboration/decisions/ADR-019-internal-engineering-model-assembly-architecture.md`

Accepted architecture checkpoint:

`ff4ee4e038942f9ee267eb2ad6a6daa600b09e6d`

Completed implementation decomposition:

```text
I1  IDs + immutable Internal Model domain types
I2  manifests + fingerprints + H→I contract enrichment
I3  Framework/Profile resolution + structure materialization
I4  deterministic MCE/MCR → IME/IMR assembly
I5  repository + immutable persistence + bundle integrity
I6  explicit Phase-J read contract + regression
```

## Internal Model Identities

```text
IEM-000001  Internal Engineering Model
IME-000001  Internal Model Element
IMR-000001  Internal Model Relationship
```

Identifiers are project-local, six-digit sequential, immutable and never
gap-reused.

Candidate identity, Internal Model identity and semantic subject identity remain
separate.

## Assembly Context

Phase I pins:

```text
TURING_RFLP_FRAMEWORK 1.0.0
TURING_MODEL_STRUCTURE 1.0.0
TURING_INTERNAL_MODEL_ASSEMBLY 1.0.0
exact derivation-rules reference from H→I
```

Assembly rules:

`context/modeling/turing_internal_model_assembly_rules.json`

Normative behavior:

- deterministic assembly only
- no semantic reinterpretation
- complete configured Framework hierarchy materialized
- empty structural nodes allowed
- reviewed Phase-H assignment remains authoritative
- no invented engineering hierarchy
- exact accepted Candidate authorization required
- fail closed when new engineering judgement would be necessary

## Deterministic Assembly

Accepted MCEs become separate IMEs while preserving semantic subject identity,
source Candidate identity/fingerprint, engineering content, structural
assignment, Approved Input provenance, exact Human Review Decision and accepted
exception where applicable.

Accepted MCRs become IMRs. Their exact source and target Candidate endpoints are
rebound to IMEs in the same IEM snapshot.

Phase I preserves unchanged:

```text
relationship_family
semantic_intent
directionality
```

Phase J owns mapping those engineering semantics to concrete SysML v2 textual
constructs.

## Exact Assembly Identity

Phase I calculates a deterministic `assembly_input_fingerprint` over the exact
authority-bearing H→I state.

Exact assembly identity is:

```text
assembly_input_fingerprint
+
assembly_rules_reference
```

Reassembling the same exact identity is idempotent and returns the existing IEM.

There is no "latest wins" behavior.

## Persistence

```text
data/projects/<project_id>/internal_models/
└── IEM-000001/
    ├── manifest.json
    ├── structure.json
    ├── elements/
    │   ├── IME-000001.json
    │   └── ...
    └── relationships/
        ├── IMR-000001.json
        └── ...
```

Persistence is immutable and atomic.

The repository validates project isolation, exact path identity, symlink safety,
fingerprints, exact structure membership, IMR endpoints, subject-key consistency,
Review Decision references, accepted exceptions, project-wide ID non-reuse,
interrupted publication and duplicate exact assembly identity.

## Sole I → J Read Boundary

Phase J shall consume Phase-I output only through:

```python
InternalModelReadService.load_phase_j_input(
    project_id,
    internal_engineering_model_id,
) -> InternalEngineeringModelSnapshot
```

The service scans repository integrity, loads the explicitly requested IEM and
revalidates the complete bundle.

No implicit latest-IEM selection exists.

## Phase-I Verification

```text
I6 focused:
32 passed in 0.70s

Focused I1–I6 aggregate:
110 passed in 1.07s

Complete repository regression:
5087 passed in 26.00s

git diff --check:
PASS
```

Phase I generates no SysML v2 textual notation.

---

# Phase Boundaries

```text
H  Approved Input → reviewed Model Candidates
I  reviewed Candidates → immutable Internal Engineering Model
J  Internal Engineering Model → SysML v2 text
K  validation
L  versioned output package
```

Conceptual CATIA / implementation reconciliation:

```text
LC_07 Architecture Synthesis and Validation
├── Phase I  deterministic synthesis / assembly
└── Phase K  broader architecture/model validation

LC_08 SysML v2 Artifact Generation
└── Phase J  SysML v2 textual generation
```

Implementation phases therefore do not map one-to-one to CATIA Logical
Components.

---

# Exact Next Work Package

## WP-06 / Phase J — SysML v2 Code Generator

Objective:

Generate deterministic SysML v2 textual notation from one explicitly selected,
validated `InternalEngineeringModelSnapshot`.

Phase J must begin by inspecting:

- `InternalEngineeringModelSnapshot`
- `InternalModelElement`
- `InternalModelRelationship`
- `InternalModelStructure`
- `InternalModelReadService.load_phase_j_input(...)`
- `context/sysml/sysml_v2_target_notation.json`
- current SYSIDE-compatible syntax conventions
- CATIA textual-notation expectations relevant to generated artifacts

The Phase-J architecture discussion shall define at least:

- target-notation profile authority
- IEM element-type → SysML v2 construct mapping
- relationship-family / semantic-intent → SysML v2 relationship mapping
- package / namespace projection from Internal Model Structure
- identifier and naming policy in generated text
- deterministic ordering
- modular output-unit strategy
- unsupported construct behavior
- generation diagnostics
- exact IEM / IME / IMR traceability into generated artifacts
- target syntax version / profile binding
- explicit Phase-J → Phase-K validation boundary
- explicit prohibition on treating generated text as a replacement for CATIA
  engineering authority

Do not:

- read Model Candidates directly for generation
- bypass `InternalModelReadService`
- reinterpret rejected/deferred/unreviewed Candidate content
- invent new engineering relationships
- perform broad Phase-K validation inside J
- silently choose a latest IEM
- mutate an existing IEM

No Phase-J implementation begins before the exact Phase-J architecture contract
has been surfaced, reviewed and explicitly accepted.

---

# Remaining Demo Roadmap

```text
WP-06  Phase J — SysML v2 Code Generator
WP-07  Phase K — Validation Layer
WP-08  Phase L — Output Writer
WP-09  Guided Workflow UI
WP-10  Ingestion + Human Review UX Simplification
WP-11  Architecture / Model Proposal UX
WP-12  End-to-End Demo Hardening
WP-13  Demo Freeze + Rehearsal
WP-14  CATIA / SSOT Checkpoint
```

Schedule:

```text
2026-08-14  H–L closed vertical slice
2026-08-15  Guided Workflow UI
2026-08-16  Demo hardening
2026-08-17  Functional freeze / rehearsal
2026-08-18  Product demo
```

Quality remains non-negotiable. Save time through decomposition and targeted
testing, not weaker authority, validation or traceability.

---

# Mandatory Engineering Boundaries

- CATIA remains engineering authority.
- The committed repository remains implementation authority.
- Human Review authority cannot be replaced by confidence or consensus.
- Only active Approved Inputs may support Phase-H Candidate Sets.
- Model Candidates remain derived and non-authoritative.
- Human-accepted Model Candidates authorize Phase-I assembly only.
- `ModelCandidateReadService` remains the sole H→I production read boundary.
- Phase-I Internal Models are immutable representation-neutral snapshots.
- `InternalModelReadService` is the sole I→J production read boundary.
- No implicit latest-IEM selection is allowed.
- Phase J shall preserve accepted engineering semantics.
- Generated SysML v2 text does not replace CATIA engineering authority.
- Broader architecture/model validation remains Phase K.
- Failed required validation blocks later publication.
- Progressive disclosure may hide complexity but may not remove traceability.
- No frontend technology rewrite before the product demo.

---

# Immediate Starting Instruction for the Next Chat

Begin with the Phase-J architecture contract.

Do not implement yet.

First:

1. inspect the exact `InternalEngineeringModelSnapshot`
2. inspect the explicit I→J read service
3. inspect the existing target-notation profile
4. inspect representative current SYSIDE / CATIA textual notation
5. surface exact mapping and modularization questions
6. propose the minimal deterministic Phase-J architecture
7. define the Phase-K handoff
8. obtain explicit acceptance

Only after acceptance begin WP-06 implementation.
