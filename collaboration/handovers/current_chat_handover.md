# Current Chat Handover

## Purpose

This document is the authoritative starting point for the next implementation
chat after Phase J — SysML v2 Code Generator completion.

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

`commit containing this SSOT update` — Phase J completion

Last Prior Committed Checkpoint

`af6953486a71c3073c0169ef5052dbcabb49c4fc` — accepted Phase-J architecture checkpoint

Architecture Version

1.8

Knowledge Base Version

1.15

Implementation Version

0.17

Roadmap Version

1.15

Last SSOT Update

2026-08-13

Current Phase

Phase K — Validation Layer

Current Status

Phase J is completed and verified. Phase K is next.

Verified Automated Test Baseline

```text
Targeted Turing Core synchronization regression:
191 passed in 0.19s

Complete repository regression:
5239 passed in 13.77s

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
5. `collaboration/decisions/ADR-019-internal-engineering-model-assembly-architecture.md`
6. `collaboration/decisions/ADR-020-hybrid-target-projection-and-coverage-architecture.md`
7. `collaboration/decisions/ADR-021-syside-compatible-sysml-v2-generation-architecture.md`
8. `context/sysml/sysml_v2_target_notation.json`
9. `context/sysml/turing_sysml_v2_generation_profile.json`
10. `context/sysml/turing_sysml_v2_artifact_structure.json`
11. `context/sysml/turing_sysml_v2_generator_rules.json`
12. `collaboration/change_log.md`
13. this handover

Then inspect the committed Phase-J implementation only as required for Phase-K
architecture and validation work.

---

# Source Authority

Authority order:

1. CATIA SysML v2 model for engineering knowledge
2. committed repository for implementation reality
3. Collaboration Knowledge Base for coordination and accepted decisions
4. chat history and temporary generated artifacts

Generated SysML v2 output is a derived implementation artifact. It does not
replace CATIA engineering authority.

Implementation observations may become Phase-N2 reconciliation candidates only.
They do not silently create normative engineering knowledge.

---

# Repository Collaboration Workflow

GitHub remains passive for the AI assistant.

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

The local tree may contain unrelated/generated files. Do not stage or clean
those unless explicitly part of the intended change.

---

# Phase I — Upstream Internal Engineering Model Authority

Phase I remains completed.

Sole I→J production read boundary:

```python
InternalModelReadService.load_phase_j_input(
    project_id,
    internal_engineering_model_id,
) -> InternalEngineeringModelSnapshot
```

There is no implicit latest-IEM selection.

The IEM preserves accepted engineering semantics as immutable IMEs and IMRs,
including exact Candidate, Approved Input, Human Review and accepted-exception
traceability.

---

# Phase J — Completed SysML v2 Code Generator

Architecture decision:

`collaboration/decisions/ADR-021-syside-compatible-sysml-v2-generation-architecture.md`

Accepted architecture checkpoint:

`af6953486a71c3073c0169ef5052dbcabb49c4fc`

## Completed decomposition

```text
J1  Generation foundation + Target Notation 0.2.0 + SYSIDE syntax evidence
J2  Generation Profile + Artifact Structure Profile + deterministic preflight
J3  package/symbol/safe-text/canonical-order projection
J4  deterministic element renderer
J5  deterministic relationship renderer + endpoint-role integration
J6  GeneratedSysMLArtifactSet + traceability + fingerprints/idempotence
J7  explicit Phase-J service boundary + regression + SSOT closeout
```

## Pinned generation policy

```text
CTX_SYSML_V2_TARGET_NOTATION 0.2.0
TURING_SYSML_V2_GENERATION 1.0.0
TURING_SYSML_V2_ARTIFACT_STRUCTURE 1.0.0
TURING_SYSML_V2_GENERATOR_RULES 1.0.0
```

The SysML v2 Release repository remains the primary language/syntax reference.
SYSIDE remains the selected target validation environment. Apollo 11 remains
non-normative.

## Supported element generation

Production-authorized mappings include:

```text
stakeholder_requirement  → requirement usage
system_requirement       → requirement usage
subsystem_requirement    → requirement usage
use_case                 → use case definition
function                 → action usage / Feature
logical_component        → part usage / Feature
physical_component       → part usage / Feature
```

`stakeholder` and `user_need` remain explicitly unsupported rather than
force-fitted into an unrelated SysML construct.

## Supported relationship generation

Production-authorized relationships include:

```text
allocated_to  → allocate SOURCE to TARGET;
dependency    → dependency from SOURCE to TARGET;
depends_on    → dependency from SOURCE to TARGET;
satisfies     → satisfy TARGET by SOURCE;
```

The `satisfies` transformation preserves the IEM semantic convention
`source satisfies target` while adapting only the SysML textual endpoint order.

Unsupported relationship semantics remain fail-closed. No generic dependency
fallback is permitted.

## Feature endpoint correction

SYSIDE integration exposed that `allocate` requires Feature endpoints.

The production representation was therefore corrected from reusable
`ActionDefinition` / `PartDefinition` declarations to individual
`ActionUsage` / `PartUsage` Features for IEM functions and components.

Preflight now validates both:

- endpoint element kind
- exact endpoint target construct where required

This prevents invalid allocation or satisfaction combinations before rendering.

## SYSIDE evidence

Controlled SYSIDE checks confirmed:

- Requirement Usage
- Action Usage / Definition experiments as applicable during J development
- Part Usage / Definition experiments as applicable during J development
- Use Case Definition
- Dependency
- Allocation
- Satisfaction

The accepted production forms are the usage/feature forms pinned by the current
Generation Profile.

## Generated artifact contract

Phase J builds one immutable validation-ready:

`GeneratedSysMLArtifactSet`

MVP unit:

```text
generated_model.sysml
```

Root package:

```text
GeneratedModel
```

The complete configured Framework hierarchy is projected deterministically to
nested packages, including configured empty packages.

Relationships are emitted without inventing engineering containment and use
deterministic qualified references to exact generated endpoints.

## Traceability

Every generated IME/IMR representation retains machine-readable traceability to:

```text
Generated unit/location
→ IEM
→ IME or IMR
→ MCE or MCR
→ Approved Input
→ Human Review Decision
→ accepted exception where applicable
```

Generated line locations are one-based and inclusive.

## Identity and idempotence

Phase J pins:

- source IEM content fingerprint
- Target Notation reference/fingerprint
- Generation Profile reference/fingerprint
- Artifact Structure reference/fingerprint
- Generator Rules reference/fingerprint

The exact generation input receives a deterministic fingerprint.

Unit content and complete artifact-set content also receive SHA-256
fingerprints. Identical authority/configuration input produces byte-identical
generated text and identical fingerprints.

## Complete J orchestration boundary

```python
SysMLGenerationService.generate(
    project_id,
    internal_engineering_model_id,
) -> GeneratedSysMLArtifactSet
```

The service delegates authority loading only to
`InternalModelReadService.load_phase_j_input(...)`.

It does not:

- choose a latest IEM
- read Phase-H Candidates directly
- perform Phase-K validation
- publish into `data/output/`

---

# Phase-J Verification

Final verification:

```text
Targeted Turing Core synchronization regression:
191 passed in 0.19s

Complete repository regression:
5239 passed in 13.77s

git diff --check:
PASS
```

During final regression the Turing Core Vocabulary correctly detected that its
Target Notation reference still pinned version `0.1.0` after J1 had introduced
Target Notation `0.2.0`.

The stale reference was synchronized to `0.2.0` in both the source reference and
the Turing Core SysML mapping policy. No weakening of reference validation was
introduced.

---

# Phase Boundaries

```text
H  Approved Input → reviewed Model Candidates
I  reviewed Candidates → immutable Internal Engineering Model
J  explicit IEM → deterministic GeneratedSysMLArtifactSet
K  generated artifact set → validation result
L  validated artifact set → versioned published output
```

Phase J does not own full syntax/model validation or publication.

---

# Phase-N2 Reconciliation Candidates from J

Phase J records capability/change evidence only. It does not create or modify
CATIA Requirements, Functions or Logical Components.

Reconcile during Phase N2:

1. deterministic SysML v2 generation from an explicitly selected validated IEM
2. SYSIDE-compatible, versioned Target Notation generation
3. separate versioned semantic mapping, artifact structure and generator rules
4. fail-closed unsupported-semantics and endpoint-compatibility handling
5. deterministic generated identity, fingerprints and idempotence
6. machine-readable generated-output traceability back to approved engineering evidence
7. explicit separation of generation, validation and publication across J/K/L

Exact CATIA element types, wording and allocations remain deferred to N2.

---

# Exact Next Work Package

## WP-07 / Phase K — Validation Layer

Objective:

Validate the complete `GeneratedSysMLArtifactSet` before publication.

Phase K shall start from the Phase-J result and shall not regenerate or
reinterpret engineering semantics.

The architecture discussion shall define at least:

- exact `SysMLValidationService` boundary
- syntax validation strategy and SYSIDE integration boundary
- Target Notation validation
- Artifact Structure validation
- relationship and endpoint consistency validation
- traceability validation
- deterministic validation findings/report
- validation identity/fingerprint
- fail-closed publication gate into Phase L
- handling of unavailable external validator infrastructure
- distinction between deterministic internal checks and external parser/tool
  compatibility checks

Do not:

- mutate the source IEM
- silently rewrite generated text during validation
- use validation to invent missing engineering semantics
- publish invalid output
- bypass the Phase-J artifact-set contract
- collapse Phase K into Phase L

No Phase-K implementation begins before the Phase-K architecture contract is
surfaced, reviewed and explicitly accepted.

---

# Remaining Demo Roadmap

```text
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

# Immediate Starting Instruction for the Next Chat

Begin with the Phase-K validation architecture contract.

First inspect:

1. `GeneratedSysMLArtifactSet`
2. `GeneratedSysMLUnit`
3. `GeneratedSysMLTraceabilityEntry`
4. `SysMLGenerationService`
5. Target Notation / Generation / Artifact Structure / Generator Rules profiles
6. current SYSIDE validation options and existing deterministic validators
7. Phase-L publication expectations only enough to define the K→L gate

Then propose the minimal deterministic Phase-K architecture and obtain explicit
acceptance before implementation.
