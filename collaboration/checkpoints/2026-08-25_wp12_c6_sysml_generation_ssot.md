# WP-12 C6 / SysML Generation SSOT — 2026-08-25

## Post-checkpoint execution update — Target Model templates applied

After this checkpoint was created, the prepared context-template patch was applied
successfully.

Created and validated:

```text
context/requirements/requirements_authoring_profile.json
context/sysml/sysml_v2_target_model_profile.json
```

Therefore any earlier statement in this checkpoint saying that these files have not
yet been created is historical and superseded by this update.

This remains scaffolding only. `SEM-015` is still an open MAJOR finding and is not
to be fully implemented before the current WP-12 E2E is completed.

Immediate next technical task:

```text
continue BLK-006
→ SAME Project 120412 / IEM-000001
→ Target Model + Target Notation assessment
→ minimum bounded C6c.x correction
```


## Purpose

This checkpoint is the canonical coordination state for continuing WP-12 after the
R4c semantic recovery, Model Placement / Assembly recovery, Final Model Review,
authority-backed Internal Model materialization and the current SysML v2 generation
preflight failure.

It supersedes older WP-12 coordination statements where they conflict with this
checkpoint. Historical test evidence and blocker history remain valid.

## Formal status

```text
WP-12: FAILED WITH BLOCKER

Active:
BLK-002  Cross-Source Processing Artifact Identity Collision
BLK-006  Single-source E2E has not yet passed SysML v2 generation/validation
```

Resolved/retested in the current recovery chain:

```text
BLK-004 -> CORRECTED -> RETEST PASS
BLK-005 -> CORRECTED -> RETEST PASS WITH FINDINGS
BLK-007 -> CORRECTED -> RETEST PASS
```

BLK-003 semantic/source-grounding recovery is implemented and live validated through
the current single-source downstream chain. Formal closure still waits for the
complete E2E.

Formal multi-source Stage-A evidence remains:

```text
WP12-E2E-DRY-001
Project 308131
FAILED WITH BLOCKER — BLK-002
```

Current single-source recovery/live-E2E Project:

```text
Project 120412
WP12 R4c Live E2E
Source: legacy/demo/wp12/01_product_overview.md
```

## Repository / local implementation state

Repository:

```text
mz-commits-ai4mbse/SysMLv2-Generator
branch: main
```

Last known committed recovery checkpoint:

```text
9691b5a9fc300a97eff8871088d9feabe165a215
Complete WP12 R4c recovery and record live E2E checkpoint
```

The C1-C6 Model Placement / Assembly / Final Review / authority-backed Internal
Model / SysML generation work and BLK-007 correction were developed after that
checkpoint and are expected to still be local/uncommitted unless the user has
explicitly committed them since.

The next chat MUST verify local reality first:

```bash
git status --short
git log -1 --oneline
git diff --check
```

Latest known full regression after BLK-007:

```text
5972 passed, 1 skipped in 33.43s
git diff --check PASS
```

No staging/commit was authorized for the current local work at this checkpoint.

## Accepted semantic recovery architecture

Canonical finding:

```text
Detection of relevant source-grounded information and interpretation must be separate.
```

Accepted lifecycle:

```text
Source Registration
→ Source Preparation
→ deterministic Source Projection / SAUs
→ specialized persona-independent Evidence Detection
→ persisted SourceEvidence (EVD-*)
→ shared Mention Discovery over coherent context
→ Cross-Mention Subject Consolidation
→ Canonical Engineering Subjects (SUBJ-*)
→ professional Persona Interpretation over the SAME canonical subject
→ field-level Semantic Consensus / Variance
→ Human Engineering Review
→ Approved Engineering Information
→ Model Representation + Placement / Allocation
→ Human Model Placement Review
→ Approved Model Placement Set
→ Model Assembly
→ Final Model Review over the assembled whole model
→ authority-backed Internal Model
→ SysML v2 generation
→ validation / publication review
```

Hard principles:

```text
REFERENCE KNOWLEDGE ≠ ENGINEERING EVIDENCE
LLM CONTEXT ≠ PROVENANCE UNIT

Mentions are many.
Engineering Subjects are unique.
Interpretation occurs once per Canonical Engineering Subject and Persona.

Human decisions create authority.
Agent consensus does not.
```

## R4c live Project 120412

Human Review:

```text
24 Canonical Subjects
RVD-000001
RVV-000001
final Review Revision: RVR-000062
finalization: HRD-000001
reviewer: MZ
```

Disposition:

```text
22 accepted_with_modification
2 rejected
17 model-promotable element RITs
7 open_question
17 active Approved Inputs
```

Approved Engineering Information contains:

```text
17 approved Subjects
21 accepted semantic Relationships
```

The Phase-H handoff now binds both Subjects and Relationships as Human-approved
Engineering Information. Open Questions remain outside model promotion.

## Model Placement / Sorting

Accepted architecture:

```text
Approved Engineering Information
→ Model Representation / Placement proposals
→ 3 dedicated placement personas
→ Comparison / Variance
→ HUMAN MODEL PLACEMENT REVIEW
→ Approved Model Placement Set
→ deterministic Model Assembly
→ FINAL MODEL REVIEW
→ authority-backed Internal Model
→ deterministic SysML v2 serialization
```

Placement personas:

```text
1. SysML/Profile Modeler
2. System Architecture Modeler
3. Conservative Modeling Reviewer
```

Live outcome:

```text
17/17 decided
13 accepted
4 rejected
0 pending

Accepted distribution:
Stakeholder 8
System      3
Subsystem   2
```

Rejected placements:

```text
Remote Microscope Collaboration capability
live microscope view
collaboration session
session information
```

Important semantic correction:

```text
Engineering information classification ≠ target-model representation.
```

A source-grounded Constraint may legitimately materialize as a target Requirement
while preserving the original Engineering Information classification.

## Model Assembly / BLK-007

The first live Assembly attempt failed because the service reused the Model Placement
team for target-relationship representation.

Canonical blocker:

```text
BLK-007 — Model Assembly invokes the Model Placement Team for
target-relationship representation.
```

Accepted correction:

```text
Model Assembly is deterministic.

Exact accepted engineering relationship semantic matching an authorized target
profile rule may be retained.

Non-exact accepted relationship semantics remain unresolved for Human Final Model
Review.

No LLM/persona relationship projection occurs during Model Assembly.
```

Live retest:

```text
Model Assembly Preview: SUCCESS
13 elements
3 relationships
relationship variance: 0
unmapped relationships: 3
```

Disposition:

```text
BLK-007 -> BLOCKER RESOLVED -> RETEST PASS
```

## Final Model Review

Human target-relationship decisions:

```text
SRD-000008
microscope workstation -> related_to -> microscope operator
selected: relationship:traces_to

SRD-000009
microscope workstation -> uses -> separate client application
selected: relationship:dependency

SRD-000017
understand who currently controls the microscope
-> related_to ->
take temporary control of the microscope
selected: relationship:traces_to
```

Shared rationale:

```text
Conservative target representation based on the accepted engineering semantics.
Generic related_to relationships are represented as traces_to to avoid introducing
stronger semantics; uses is represented as a dependency without asserting a stronger
depends_on relationship.
```

Final Review:

```text
FAD-000001
APPROVED
Reviewer: MZ
```

## Authority-backed Internal Model v2

Materialization succeeded:

```text
IEM-000001
13 elements
3 relationships
fingerprint:
1e64637cc7762d3fb915aa4ee86c1eae8ecd3129a5d740ad84a7354c6a99e75b
```

Authority chain:

```text
Element engineering meaning -> Approved Engineering Information / Approved Input
Element placement           -> Human Model Placement Decision (MPD)
Relationship meaning        -> accepted semantic Relationship (SRD)
Relationship representation -> Final Model Review decision (FAD)
```

No legacy Candidate Review decision is synthesized.

## Current SysML v2 generation failure

The UI `Generate SysML v2` call fails safely and leaves the Internal Model unchanged.

Direct builder diagnostics proved the failure is before persistence, inside the
existing Phase-J generation preflight:

```text
SysMLGenerationBlockedError:
Phase-J generation preflight is blocked by 4 finding(s).
```

Exact blockers:

```text
1. IME-000001
   stakeholder.stakeholders / stakeholder
   UNSUPPORTED_ELEMENT_MAPPING
   J2_ELEMENT_001

2. IME-000003
   stakeholder.stakeholders / stakeholder
   UNSUPPORTED_ELEMENT_MAPPING
   J2_ELEMENT_001

3. IMR-000001
   traceability / traces_to / source_to_target
   UNSUPPORTED_RELATIONSHIP_MAPPING
   J2_REL_009

4. IMR-000003
   traceability / traces_to / source_to_target
   UNSUPPORTED_RELATIONSHIP_MAPPING
   J2_REL_009
```

The third assembled Relationship, resolved as `dependency`, passes.

Therefore:

```text
renderer crash: NO
repository-write failure: NO
preflight mapping coverage blocker: YES
```

No `generated_sysml_v2` artifact is persisted because the builder blocks before
repository persistence.

BLK-006 remains active until generation + authority-backed validation complete the
same-Project E2E or reach a correctly classified external validation limitation.

## SysML v2 Target Model vs Target Notation

Use these terms:

```text
SysML v2 Target Model
→ how approved Engineering Information should be represented and formulated
  as a coherent target model

SysML v2 Target Notation
→ which concrete SysML v2 syntax is valid/authorized for deterministic serialization
```

Internal example/reference model names must never become user-facing modeling
concepts in the application.

## Reference-model usage

The repository contains the complete non-normative SysML v2 example-model reference:

```text
external/apollo11-sysml-v2/
```

Pinned/reviewed source:

```text
airbus/apollo-11-sysml-v2
main @ 6e9c93f
```

Its role is modeling-pattern / structure / style reference only.

Operational principle:

```text
Engineering Sources
→ determine WHAT is true for the current system

Human Review
→ determines WHAT is accepted

reviewed Target Model / reference patterns
→ guide HOW comparable concepts are modeled

SysML v2 specification/release + validated fixtures
→ determine whether textual syntax is valid
```

Observed useful patterns include Stakeholders via part definitions/usages,
Requirements via requirement definitions/usages, Functions via action
definitions/usages, logical/physical Parts, and explicit relationship semantics.

Do not copy reference-domain content, identifiers, CoSMA taxonomy, requirements or
package hierarchy. The accepted Turing Stakeholder/System/Subsystem RFLP remains
the placement framework.

## Stakeholder syntax evidence

Local SysML v2 grammar shows the textual keywords `actor` and `stakeholder` as
specialized usages in Requirement/Case bodies. This is not evidence for blindly
serializing a free-standing package-level `stakeholder IME_xxxxxx;`.

The reference model provides a more appropriate standalone Stakeholder pattern using
part definitions/usages with a Stakeholder base concept.

Therefore the two stakeholder blockers require a reviewed Target Model pattern plus
valid Target Notation, not a blind profile switch.

## `traces_to` evidence

A local search of the available SysML v2 release source + textual grammar found no
usable textual `trace` / `traces` / `traceability` syntax evidence for the current
MVP notation.

Therefore:

```text
Do NOT simply set J2_REL_009 to supported.
Do NOT map generic related_to to dependency merely to make the test green.
```

Possible legitimate outcomes after Target Model analysis include a supported formal
relationship pattern, a richer model structure, intentional non-materialization
while retaining provenance, or a new Human decision.

No final correction has yet been accepted for the current two `traces_to` cases.

## SEM-015 — MAJOR

Canonical finding:

```text
SEM-015 — MAJOR
Target-Model Formulation is missing as an explicit processing stage.
```

Scope:

```text
ALL model representations
not only Requirements
```

Required distinction:

```text
Engineering Meaning
≠ Target-Model Representation
≠ Target-Model Formulation
≠ SysML v2 Serialization
```

Examples:

```text
Requirement
→ well-formed requirement statement

Function
→ model-appropriate function/action formulation and name

Stakeholder
→ appropriate target-model stakeholder representation

Logical / Physical Element
→ appropriate reusable definition / usage / naming formulation

Use Case
→ appropriate target-model use-case formulation

Relationship
→ exact supported semantic representation or explicit non-materialization
```

Also accepted:

```text
Relevant/extracted information ≠ automatically model-worthy information.
```

Engineering/context information may remain useful for interpretation, provenance or
later decisions without being formally materialized.

The current WP-12 product-overview source is intentionally retained as a difficult
mixed/context-heavy boundary case.

SEM-015 is a major architecture finding but is NOT to be implemented before the
current WP-12 E2E is finished.

## Requirements Authoring reference

The user supplied a personally purchased copy of:

```text
International Council on Systems Engineering (INCOSE)
Requirements Working Group
Guide to Writing Requirements
Rev 4
1 July 2023
Document No.: INCOSE-TP-2010-006-04
ISBN: 978-1-93707-05-4
Principal authors: Michael Ryan, Lou Wheatcraft
```

No DOI was identified in the publication.

Usage boundary:

```text
Use the purchased document only to derive/lock down Requirements Authoring rules.
Do not distribute or commit the purchased PDF.
Do not load the whole copyrighted document into routine project prompts.
```

The Guide contains C1-C15 characteristics, R1-R42 writing rules and structured
natural-language patterns. It is intended to become the basis of a curated,
traceable Requirements Authoring Profile after WP-12 closeout.

## Prepared but NOT applied SEM-015 template patch

A prior chat prepared:

```text
wp12_sem015_target_model_context_templates_patch.py
```

It would create:

```text
context/requirements/requirements_authoring_profile.json
context/sysml/sysml_v2_target_model_profile.json
```

IMPORTANT:

```text
THE USER HAS NOT APPLIED THIS PATCH.
DO NOT ASSUME THESE FILES EXIST.
```

It must not be silently recreated/applied as part of the current generation fix.

## Other findings to preserve

Semantic:

```text
SEM-009  equivalent relationship hypotheses not consolidated across predicate variants
SEM-010  relationship lifecycle not auto-aligned with rejected Subject
SEM-011  relevant SysML element-type coverage incomplete
SEM-012  Engineering information type vs target representation insufficiently separated
SEM-013  shared ambiguity conflated with actual Persona variance
SEM-014  unresolved target Relationship representation must require explicit Human selection
SEM-015  MAJOR Target-Model Formulation missing for all representations
```

UX:

```text
OBS-019 Discovery over-generation
OBS-023 Relationship review navigation/blocker visibility
OBS-024 relationship review is too ID-centric across all review stages
OBS-027 no explicit finalized report export/download
OBS-028 SUBJ -> RIT identity transition insufficiently explained
OBS-029 same-render stale status after promotion
OBS-030 initial lack of visible processing state during proposal generation
OBS-031 Human Model Placement Review requires excessive interaction
```

Do not create a separate Final-Review ID-centric finding; it is covered by OBS-024.

## Immediate next technical objective

Do not start SEM-015 implementation yet.

Continue the SAME Project `120412` from `IEM-000001`.

Immediate work:

```text
1. Treat the four preflight findings as Target Model / Target Notation coverage
   evidence, not as a reason to bypass the preflight.

2. Inspect stored SysML v2 reference/modeling patterns relevant to the CURRENT
   13 elements + 3 Relationships.

3. Build an explicit mapping assessment for:
   - stakeholder
   - stakeholder requirement
   - use case
   - function
   - logical component
   - physical component
   - dependency
   - generic related_to / current Human-selected traces_to

4. For each answer:
   a) accepted Engineering Meaning
   b) legitimate Target Model pattern
   c) valid Target Notation construct/syntax
   d) whether additional Human authority is required
   e) whether intentional non-materialization is preferable

5. Propose the minimum bounded C6c.x correction needed to complete WP-12.

6. Only after user acceptance:
   patch -> focused tests -> full regression -> git diff --check
   -> same-Project SysML generation retest

7. Then run authority-backed validation.

8. Close the single-source E2E and update WP-12 status.

9. Only after E2E closeout:
   Findings triage -> quick/high-value corrections -> SEM-015 major work separately
```

Do not discard Project 120412 and do not regenerate upstream Human decisions merely
to avoid the current generation findings.

## Working rules

GitHub is passive/read-only for implementation work unless explicitly authorized.

Use exact local patches/commands.

Never:

```text
git add .
git add -A
git add --all
```

Do not stage/commit before explicit acceptance.

Unrelated dirty files such as `.DS_Store`, `__pycache__`, old generated reports,
run artifacts, ZIPs or local patches must not be staged.

The user typically applies patches from `~/Downloads/`.

## Fresh-chat startup

Read:

```text
collaboration/checkpoints/2026-08-25_wp12_c6_sysml_generation_ssot.md
collaboration/handovers/current_chat_handover.md
collaboration/audits/wp12_findings.md
collaboration/current_state.md
collaboration/roadmap.md
collaboration/checkpoints/2026-08-24_wp12_r4c_live_e2e_ssot.md
```

Then verify local Git state and continue only from the current C6 SysML-generation
gate.
