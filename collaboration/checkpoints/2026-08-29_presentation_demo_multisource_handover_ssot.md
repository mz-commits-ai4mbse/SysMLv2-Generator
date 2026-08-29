# Turing Generator — Presentation / Demo / Multi-Source Handover SSOT

Date: 2026-08-29
Status: Accepted coordination checkpoint before BLK-002 implementation
Repository: `mz-commits-ai4mbse/SysMLv2-Generator`

## Purpose

Freeze the current coordination state after v0.3.0 Gate-3 validation, CATIA
presentation modeling, the current interim-presentation draft and the future
Human-feedback learning concept; then transition safely to BLK-002.

## Known-Good baseline / rollback point

Remote `main`:

`6d9a600dfa1883d5d6b57f40bfb870ebf6e4cdd6`

Commit:

`Complete v0.3.0 semantic hardening and Gate 3 validation`

Accepted evidence:

```text
Project 000116 Lead-Source Gate 3: PASS
real SYSIDE validation:              PASS
Human publication approval:          PASS
immutable Published Output:          PASS
complete repository regression:      6100 passed in 17.87s
git diff --check:                    PASS
```

This is the protected Known-Good single-source fallback.

Do not mutate or regenerate accepted Project `000116` merely to simplify
BLK-002 work.

## Authority order

1. accepted live CATIA SysML v2 engineering model;
2. committed repository implementation;
3. Collaboration SSOT / ADRs / checkpoints;
4. current external working artifacts;
5. chat history.

GitHub remains passive for assistant-driven work unless explicitly authorized.

## CATIA / architecture checkpoint

The user updated the current CATIA textual snapshot:

`CATIAMSOSA_TextualNotation.txt`

Current presentation-relevant model artifacts:

```text
SFB_004 Engineering Data Transformation Flow
SFB_005 Engineering Information Processing Flow
Logical Architecture presentation view
Three-Layer Architecture Mapping
```

SFB_004 is the nominal End-to-End flow. SFB_005 is the detailed processing zoom
with deterministic source preparation, LLM-supported evidence/interpretation,
configured Personas, consolidation, optional consensus/variance, semantic /
ontology governance, coverage assessment and Human Review.

The Logical Architecture retains the eight accepted Logical Components and
presentation context for Human Reviewer, LLM Inference, Semantic Reference
Knowledge, Target Model References and SysML Modeling References.

Three-layer mapping remains:

```text
Data:      LC_02 / LC_04 / LC_06
Process:   LC_01 / LC_03 / LC_05 / LC_07 / LC_08
Knowledge: LC_04 / LC_05 / LC_06 / LC_07
```

Do not model speculative Multi-Source architecture before the implementation /
contract audit establishes the real change. Reconcile CATIA after accepted
BLK-002 implementation if architecture semantics changed.

## Interim-presentation checkpoint

Latest working master deck:

`AbschlussPräse_MasterArbeit_MZ_29082026(3).pptx`

Status:

`GOOD ENOUGH FOR NOW / FINAL POLISH DEFERRED`

One master deck is retained for Kick-off, interim and final colloquium; slides
are shown / hidden per event.

Current interim story:

```text
Title
→ Motivation
→ Kick-off methodology
→ three-layer realization
→ Logical Architecture
→ E2E Engineering Workflow
→ Processing detail
→ implemented workflow + Human Authority
→ verification
→ engineering learnings
→ concrete current system boundaries
→ modularity outlook
→ next steps / discussion
```

Each complex CATIA diagram has a full-diagram slide plus a simplified essence
slide.

Key implementation message:

`Human-in-the-Loop is not one global step; Human authority accompanies multiple transformation boundaries.`

Persona processing is worth mentioning. Consensus / variance is review evidence.
Reserve the stronger `variance → Human attention → correction → future learning`
narrative mainly for Thesis Discussion / final colloquium unless explicitly
needed earlier.

BLK-002 is intentionally omitted from the current interim system-boundary slide
because it is expected to be resolved before presentation use. If it is still
open at final slide polishing, it must be restored as an explicit limitation.

## Future thesis outlook

Preserve:

`collaboration/checkpoints/Thesis_Outlook_Adaptive_Human_Feedback_Learning.md`

This is future work, not v0.3.0 and not BLK-002 scope.

Concept:

```text
Engineering task
→ Adaptive Inference Gateway
→ external LLM
→ existing processing
→ Human Review
→ persisted decision + exact delta
→ Human Feedback Learning
→ candidate learned policy
→ offline / shadow evaluation
→ governed promotion
→ Adaptive Inference Gateway
```

Potential future metrics include First-Pass Human Acceptance Rate and a Human
Intervention Profile. Acceptance must not become the sole optimization target.

## BLK-002 decision

Finding:

`BLK-002 — Cross-Source Processing Artifact Identity Collision`

Current status:

`OPEN / BLOCKING`

Current priority:

```text
THESIS-CRITICAL
DEMO-CRITICAL
NEXT TECHNICAL WORK
```

This supersedes the old sequence that deferred the BLK-002 decision until after
Safe Demo preparation.

Why: the intended legacy-data value proposition requires information distributed
across multiple heterogeneous Sources to contribute to one governed project-level
engineering result. A single-document path leaves the demonstrator materially
vulnerable to the objection that the bounded input could be handled by a direct
LLM prompt.

## Working Multi-Source contract

All eligible Sources are considered without an a-priori authority hierarchy.
Equal consideration does not mean contradictory statements are both true.

Required:

- Project / Source / Run / Attempt / Artifact provenance survives end-to-end;
- semantically equivalent information from different Sources may consolidate;
- every contributing Source remains visible in consolidated provenance;
- Source-unique information remains available;
- contradictory / materially variant information remains explicit;
- Human Review determines engineering authority;
- no source weighting / source-order winner / automatic truth arbitration;
- no Project-specific demo exception.

Out of current bounded scope:

- enterprise Source authority policies;
- automatic Source weighting;
- automatic truth resolution;
- new ontology architecture.

## BLK-002 Definition of Done

Technical:

- reproduce exact historical collision / ambiguity;
- identify under-scoped identity / provenance boundary;
- correct it generically;
- preserve single-source behavior;
- focused tests PASS;
- complete regression PASS;
- `git diff --check` PASS.

Functional:

- multiple Sources contribute to one project-level result;
- at least one equivalent cross-source information case consolidates;
- contributing Source provenance remains exact;
- at least one Source-unique item survives;
- contradictory / materially variant information can reach Human Review without
  silent collapse;
- Human decision binds exact content/evidence.

Downstream:

```text
project-level Human Review
→ Approved Engineering Information
→ model path
→ deterministic SysML v2
→ external validation
→ Final Review / Human release
```

Only then may a true Multi-Source claim be made.

## Safety / branch contract

Before implementation:

```text
verify local main / origin/main
inspect dirty + untracked state
create feature/blk-002-multi-source
```

Rules:

- no BLK-002 implementation on `main`;
- no broad staging or broad clean;
- no weakening Human authority, provenance, traceability or fail-closed behavior;
- no Project-specific shortcut;
- no integration before focused + full regression + real Multi-Source acceptance;
- explicit Human acceptance before integration.

The feature branch is deliberately disposable. If the correction expands into a
large redesign or destabilizes the Known-Good single-source system, stop and
reassess before integration.

## Safe Demo target after BLK-002

```text
multiple legacy Sources
→ source-grounded processing
→ project-level consolidation
→ preserved provenance + visible cross-source differences
→ Human Engineering Review
→ approved engineering meaning
→ model derivation / refinement
→ deterministic SysML v2
→ real SYSIDE validation
→ Human release
```

Kochshow remains valid:

```text
start genuine expensive Multi-Source processing live
→ show real execution
→ explain latency
→ transparently switch to a genuine persisted Multi-Source state
→ continue downstream live
```

Never present fabricated/manual Agent data as live system output.

## Immediate next-chat startup

Read in this order:

1. `collaboration/handovers/current_chat_handover.md`
2. `collaboration/checkpoints/2026-08-29_presentation_demo_multisource_handover_ssot.md`
3. `collaboration/audits/wp12_findings.md`
4. `collaboration/current_state.md`
5. `collaboration/roadmap.md`
6. `collaboration/presentations/interim_presentation_plan.md`
7. `collaboration/checkpoints/Thesis_Outlook_Adaptive_Human_Feedback_Learning.md`

Verify repository reality:

```bash
git log -1 --oneline
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
```

Expected remote baseline:

`6d9a600dfa1883d5d6b57f40bfb870ebf6e4cdd6`

Only when local state is safe:

```bash
git switch main
git switch -c feature/blk-002-multi-source
```

First task on the branch is READ-ONLY BLK-002 audit. Inspect the exact historical
evidence, Processing Run / Attempt / Artifact identity contracts,
`modules/project_ingestion/service.py`, project-processing repositories/manifests,
source-bound artifact repositories, semantic consolidation identity/provenance,
Human Review bundle provenance, and existing multi-document test protocol /
fixtures.

Do not implement until the next chat can answer:

1. What exact collision caused BLK-002?
2. Which identity is under-scoped?
3. Which source-bound behavior can remain unchanged?
4. What project-level artifact / consolidation boundary is missing?
5. How must provenance survive consolidation?
6. Where do cross-source conflicts reach Human Review?
7. What is the minimum generic correction?
8. What tests prove true Multi-Source without weakening single-source behavior?
