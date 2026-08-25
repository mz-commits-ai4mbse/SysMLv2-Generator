# Post-Golden Finding Triage — BLK / SEM / OBS

## Purpose

This triage turns the WP-12 formative findings into bounded implementation scopes
after the Known-Good Golden E2E baseline.

Baseline:

```text
commit 924bf27d2ee4ca07c1d04da2c777ce31b7632e97
tag    wp12-golden-e2e-2026-08-25
```

Principles:

- `main` remains Known-Good.
- implementation occurs on dedicated feature branches.
- priority considers engineering importance, thesis relevance, Human-authority /
  integrity risk, implementation effort and benefit/effort ratio.
- old observations are revalidated before implementation when the current UI may
  already have changed.
- no UI progress percentage may be invented if the backend cannot supply a
  meaningful percentage; use honest stage/status progress instead.

## 1. Immediate documentation / status reconciliation

### SEM-015

Current triage:

```text
architecture implemented
Golden-E2E scope validated
general target-type formulation partial
SEM-015-F01 selective dependency-aware rerun deferred
```

Reason: the current Target-Model Formulation proposal builder is intentionally
bounded to `stakeholder` and `traces_to`, while the model-quality refinement layer
already covers more element types.

SEM-015 generalization shall be implemented together with SEM-011 construct
coverage rather than as a separate shadow taxonomy.

## 2. High-value low-hanging UX / OBS cluster

### UX-A — Project context stability

Findings:

```text
OBS-001 Project selection lost on toggle
OBS-018 Global Project Selector session-state conflict
```

Observed critical example:

```text
turn "Technical details" off/on
→ selected Project may be lost
```

Importance: HIGH. Project context is global workflow context and should not change
because presentation depth changes.

Estimated effort: S after focused reproduction.

Implementation intent:

- one authoritative Project selection state,
- Technical Details changes presentation only,
- no Project deselection on toggle/rerun,
- no project-local navigation clearing unless the Project actually changes,
- focused regression reproducing the exact toggle case.

### UX-B — Long-running operation feedback

Findings:

```text
OBS-007 Long Processing feedback
OBS-017 Long-running Processing feedback / performance
OBS-030 No visible processing state during Model Proposal generation
```

Importance: HIGH / demo-critical.
Estimated effort: S-M.

Required behavior:

```text
trigger
→ immediate visible acknowledgement
→ current stage / running state
→ completion or explicit failure
```

Use a real progress bar only where meaningful progress information exists.
Otherwise use stage-based progress, spinner/status text and disabled duplicate
triggering. Never display a fabricated percentage.

### UX-C — Same-render / queue state clarity

Findings:

```text
OBS-013 Review Queue misleading zero before workspace materialization
OBS-029 Post-promotion same-render status stale
```

Importance: MEDIUM-HIGH.
Estimated effort: S.

Goal: visible state must distinguish `not materialized yet` from true zero and must
refresh immediately after authoritative writes.

### UX-D — Relationship review readability and blocker navigation

Findings:

```text
OBS-023 Relationship Review too hidden / blocker navigation unclear
OBS-024 Relationship review ID-centric / not human-readable enough
```

Importance: HIGH.
Estimated effort: S-M.

Goal:

- engineering labels primary,
- IDs secondary / Technical View,
- incoming vs outgoing clearly distinguished,
- finalization blocker links directly to the unresolved relationship.

### UX-E — Model Placement interaction reduction

Findings:

```text
SEM-013 Shared placement ambiguity conflated with Persona variance
OBS-031 Human Model Placement Review requires excessive interaction
```

Importance: HIGH.
Estimated effort: S-M.

Desired interaction:

```text
single consensus placement
→ one-click accept

shared ambiguity
→ Human selects among shared alternatives

real Persona variance / Human override / rejection
→ explicit decision and rationale
```

This preserves Human authority while removing unnecessary clicks.

### UX-F — Deterministic review export

Finding:

```text
OBS-027 Finalized Review Report has no explicit export/download capability
```

Importance: MEDIUM, high thesis/audit value.
Estimated effort: S.

First slice: deterministic Markdown export of exact finalized revision including
IDs/fingerprints. PDF remains optional.

### UX-G — Additional small presentation findings

Revalidate and batch where still present:

```text
OBS-002 Add-first-source discoverability
OBS-003 Duplicate Create Project interaction
OBS-004 Multi-file add affordance
OBS-005 Drag/drop first-click behavior
OBS-009 Optional guidance
OBS-010 Agent scope label clarity
OBS-014 Reviewer identity confirmation
OBS-016 Persona configuration presentation
OBS-028 Cross-layer identity explanation
```

Estimated effort: XS-S individually.

## 3. SEM-011 + SEM-015 target-model coverage program

SEM-011 shall be split into bounded slices instead of one large task.

### SEM-011A — Coverage reconciliation

Effort: XS-S.
Priority: HIGH.

Create an explicit matrix:

```text
Engineering Information type
→ Model Structure support
→ Placement support
→ Target-Model Formulation support
→ Model Quality profile
→ IEM representation
→ Target Notation construct
→ Generation mapping
→ Renderer
→ SYSIDE syntax evidence
```

### SEM-011B — Information / Item

Current upstream `information_item` and target `TN_011 Item Definition` already
exist.

Effort: S-M.
Priority: HIGH / low-hanging.

Complete the missing middle and deterministic generation path.

### SEM-011C — State Machine behavior

Priority: MUST for meaningful behavioral coverage.
Estimated effort: M.

Minimum coherent slice:

```text
State Machine
State
Transition
source state
target state
```

Then, where source-supported and profile-controlled:

```text
Trigger
Guard
Effect
```

Do not implement `state` as an isolated taxonomy value without transition /
containment semantics.

Each construct requires:

- Engineering Information / modeling semantics,
- model-area / placement policy,
- SEM-015 formulation policy,
- Human review,
- IEM representation,
- smallest SysML v2 syntax fixture,
- SYSIDE validation,
- Target Notation activation,
- Generation Profile mapping,
- renderer and regression tests.

### SEM-011D — Interface + Port

Priority: MUST/HIGH for structural interaction modeling.
Estimated effort: M.

`interface` already exists as an Engineering Information type, while advanced
ports/interfaces are currently restricted in Target Notation. The slice therefore
needs target construct selection plus SYSIDE evidence and downstream mappings.

### SEM-011E — Information / Item Flow

Priority: HIGH.
Estimated effort: M.

Introduce only after Item + Interface/Port semantics are clear enough to avoid a
generic flow fallback.

### SEM-011F — Additional occurrences / specialized constructs

Priority: later.
Estimated effort: M-L depending on construct.

Add only from concrete engineering/evaluation need.

## 4. Strategic blocker

### BLK-002 — Multi-Source Processing Artifact Identity

Importance: CRITICAL for any multi-source thesis claim.
Effort: unknown until audit; likely M-L.

First action is read-only reproduction/audit, not implementation:

```text
reproduce current two-source identity behavior
→ identify exact collision scope
→ compare project/source/run/artifact identity contract
→ confirm root cause
→ define bounded fix
```

The accepted single-source baseline remains valid while BLK-002 is open.

## 5. Open semantic/governance quality

### SEM-014 — Explicit Human Relationship representation selection

Importance: HIGH.
Estimated effort: S-M.

Backend authority already expects explicit final relationship resolution. Revalidate
whether the UI still introduces a substantive default. If yes, remove it.

### SEM-010 + OBS-023/024 — Relationship lifecycle

Importance: HIGH.
Estimated effort: M.

Rejected endpoint Subjects should invalidate affected accepted Relationships in an
auditable way rather than forcing manual rediscovery.

### SEM-009 — Predicate-variant relationship consolidation

Importance: MEDIUM.
Estimated effort: M.

Keep after authority/UX/model-coverage work because Human Review currently resolves
the redundancy safely.

### OBS-019 — Discovery abstention

Importance: MEDIUM.
Estimated effort: M.

Improve false-positive abstention after higher-value authority and coverage work.

## 6. Explicitly expensive / deferred

Do not treat these as quick wins:

```text
OBS-008 Processing cancellation architecture          L
OBS-012 Background execution / Streamlit decoupling   L-XL
OBS-015 Explicit reprocessing / supersession          M-L
SEM-015-F01 dependency-aware selective regeneration   M-L
```

They affect lifecycle/persistence semantics and have a wider regression surface.

## 7. Proposed execution order

```text
0. Finish + merge thesis evaluation documentation branch.

1. UX quick-win branch:
   Project context stability
   + long-running feedback
   + immediate stale-state fixes.

2. Model Placement UX/semantics branch:
   SEM-013 + OBS-031
   + SEM-014 revalidation/fix if still present.

3. SEM-011/SEM-015 coverage branch series:
   A Coverage matrix
   B Item
   C State Machine / State / Transition
   D Interface / Port
   E Flow

4. BLK-002 read-only audit.
   If bounded after audit, raise immediately to implementation priority.

5. Relationship lifecycle / semantic-quality improvements.

6. expensive lifecycle/runtime features only if thesis/demo need justifies them.
```

The order may change after the BLK-002 audit if the root cause proves small and
well-bounded.
