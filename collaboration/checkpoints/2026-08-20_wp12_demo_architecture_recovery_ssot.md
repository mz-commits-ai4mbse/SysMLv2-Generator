# Checkpoint — WP-12 Demo Readiness, Presentation and Architecture Recovery

Date: 2026-08-20

## Purpose

Authoritative working-state summary for the remainder of WP-12 and the Monday 2026-08-24 presentation/live demonstration.

This checkpoint supersedes older schedule assumptions that referred to a 2026-08-18 product demo.

---

# 1. Immediate Priority

```text
WP-12 Demo Readiness
→ recover source-grounded semantic processing
→ obtain one credible real single-source run
→ exercise Human Review → Approved Input → Model → SysML v2
→ freeze a reproducible Monday demo path
→ continue PowerPoint preparation on Monday
```

Do not spend time on presentation polish while the demo path is not credible.

Do not run repeated LLM tests before the architecture/root-cause audit identifies what will be materially different from the previous poor run.

---

# 2. WP-12 Formal Test Status

```text
WP12-E2E-DRY-001
Project 308131
IN PROGRESS / INTERRUPTED FOR BLOCKING DEFECT CORRECTION
```

It is not FAILED, RESTARTED or COMPLETED.

### BLK-001 — Derivation producer contract

```text
CORRECTED
focused validation passed
```

### BLK-002 — Cross-source Processing Artifact identity collision

```text
OPEN / BLOCKING
```

Consequences:

- no multi-document live path for Monday,
- no claim of multi-source end-to-end acceptance,
- formal WP-12 run remains interrupted.

### BLK-003 — Semantic effectiveness / engineering-subject quality

```text
OPEN / ACTIVE RECOVERY
```

Observed issues:

- source purity regression,
- model relevance regression,
- ineffective subject consolidation,
- persona-driven subject multiplication,
- Human Review content too far removed from the simple source-grounded engineering task.

BLK-003 is now treated primarily as an architectural responsibility-boundary problem, not as prompt tuning or Review Item count reduction.

---

# 3. Empirical Single-Source Run

```text
Project 877791
RUN-000001
3 personas × 1 run
real LLM
single source
```

Observed:

```text
93 element proposals
41 relationship proposals
134 raw

D3:
70 local element subjects
39 local relationship subjects
109 total

D4:
70 synthesized elements
39 synthesized relationships
109 total

Human Review:
110 Review Items
70 Elements
39 Relationships
1 Open Question
```

Conclusion:

```text
D4 → Human Review routing works technically.
Semantic quality is not accepted.
```

Review Item count is diagnostic only.

---

# 4. Architecture Recovery Direction

Accepted decision:

```text
collaboration/decisions/
ADR-027-source-grounded-evidence-detection-and-persona-interpretation-architecture.md
```

Accepted on 2026-08-21 after the Source-to-first-Human-Review responsibility audit.

Core target:

```text
REFERENCE KNOWLEDGE
examples / SysML v2 / Modeling Guidance
        │ guidance only
        ▼
ENGINEERING SOURCE
        ↓
Register Source
        ↓
Prepare Source
        ↓
Deterministic Source Projection
        ↓
Specialized Evidence Detection Agent
        ↓
Source-Grounded Evidence
"digital text marker"
        ↓
 ┌──────┼──────┐
 ▼      ▼      ▼
P1     P2     P3
Interpret / Classify the SAME Evidence
 └──────┼──────┘
        ↓
Consensus / Variance
        ↓
Optional Semantic Normalization / Ontology Alignment
        ↓
Human Engineering Review
        ↓
Approved Engineering Information
        ↓
 ┌──────┼──────┐
 ▼      ▼      ▼
Model  Model  Model
Persona Persona Persona
 └──────┼──────┘
        ↓
Architecture / Model Candidate Derivation
        ↓
Candidate Consolidation
        ↓
Model Candidate Review
        ↓
Approved Internal Model
        ↓
SysML v2
```

Critical invariants:

```text
Reference Knowledge ≠ Engineering Evidence
Source Registration ≠ LLM Source Preparation.
Evidence Detection ≠ Persona Interpretation.
Evidence identity exists before persona branching.
Personas interpret common source evidence.
Personas/runs shall not multiply Engineering Subjects.
Review Item count is a diagnostic, not an optimization objective.
Ontology/terminology alignment is a supporting service.
AI-generated interpretation ≠ Approved Engineering Information.
Architecture Derivation follows Human Engineering Review/Approval.
Model derivation may use a second persona branch after approval.
The exact downstream modeling personas remain an implementation/evaluation decision.
```

P9/D3/D4 shall be audited by legitimate responsibility:

```text
KEEP
MOVE
REDUCE
BYPASS
REMOVE / RETIRE
```

---

# 5. Existing Architecture Worth Reusing

ADR-011 already contains useful foundations:

- deterministic Source Projection,
- source anchors and exact excerpts,
- `engineering_source` versus `context_only`,
- source-traceable Information Units,
- semantic extraction,
- epistemic classification,
- deterministic consensus/variance,
- repeated runs as stability evidence rather than votes,
- explicit terminology/ontology boundary,
- Human Review separation.

Existing semantic consensus code already groups candidate discussion by exact source evidence (anchors + excerpt) and gives one effective vote per persona. This is close to the intended "same highlighted passage, different professional interpretations" workflow.

---

# 6. External Qualitative Benchmark

Source:

```text
legacy/demo/wp12/01_product_overview.md
```

A simple external Gemini test, with a strict instruction that only the supplied Legacy Source is engineering evidence, returned eight major source-grounded findings around:

1. collaboration capability / actors / live microscope view,
2. microscope workstation and remote client context,
3. remote-consultation purpose,
4. live-image observation requirement,
5. temporary remote control with operator permission,
6. operator responsibility / controller transparency,
7. session-information retention and open retention detail,
8. explicitly unspecified protocol/deployment/performance/latency/regulatory content and open product questions.

Interpretation:

```text
The core LLM task is feasible.
The current Turing pipeline likely overcomplicates or mis-bounds it.
```

Caution: Gemini already made some early model-structure suggestions. The result is a qualitative diagnostic benchmark, not a gold standard or Project authority.

---

# 7. Monday Demo Strategy

Date:

```text
Monday 2026-08-24
```

The demo is announced as a real live demonstration.

Preferred sequence:

```text
1. Open/create the demo Project.
2. Show the real Source and Processing configuration.
3. Start the real LLM Processing path live.
4. Demonstrate that actual Processing is running.
5. Avoid waiting several minutes for the full agent chain.
6. Transparently switch to a Project/Run genuinely processed earlier.
7. Continue live from persisted awaiting-review state.
8. Perform Human Review live.
9. Promote Approved Engineering Information.
10. Continue through Model/Architecture/SysML v2 as far as gates allow.
```

Recommended spoken transition:

```text
"I'll start the processing step once live so you can see how the workflow is
actually triggered. Since the agent processing can take several minutes
depending on the model, I'll continue with a previously processed state of the
same workflow so that we can inspect the downstream engineering steps."
```

This is an honest live demo, not a fake replay.

Due BLK-002:

```text
Monday live demo = single-source path.
```

---

# 8. Acceptance Criteria for the Next Real LLM Test

Do not trigger the next real run until the active path has been audited and at least one material path correction has been made.

Evaluate:

```text
1. Source Purity
2. Model Relevance
3. Exact Source Grounding
4. Persona behavior on shared evidence
5. Useful Consensus / Variance
6. Human Review usability
7. Subject / Review count as diagnostic only
```

If credible:

```text
freeze that persisted Run as the preferred Monday reference
```

Then immediately test:

```text
awaiting_review
→ Human Review
→ Approved Input
→ Model Candidate
→ Candidate Review
→ Internal Model
→ SysML v2
→ Validation
→ Final Review / Release where available
```

---

# 9. Presentation Status

PowerPoint work resumes on Monday.

Original Kick-off workflow:

```text
1 Feature Ingestion
2 Sortier Agent
3 Ontologie Anpassung
4 Muster Antizipation
5 Human in the Loop
6 Synthese / SysML-v2 generation
```

Literature framing:

```text
Data Layer
Process Layer
Knowledge Layer
```

Presentation narrative:

```text
KICK-OFF
"That was the idea."
↓
ARCHITECTURE
"That is how I operationalized it as systems engineering."
↓
PROTOTYPE
"That is what is implemented."
↓
VERIFICATION
"That is what is being tested."
↓
FINDINGS
"Testing exposed real architecture/semantic issues."
↓
NEXT
"Those findings drive bounded next steps."
```

BLK-003 is a legitimate formative engineering finding and should not be hidden.

---

# 10. CATIA Status

## Logical Architecture

A presentation-oriented Interconnection View has been created from the existing eight Logical Architecture part usages:

```text
LC_01 User Interaction and Status Presentation
LC_02 Project and Source Context Management
LC_03 Processing Orchestration and State Control
LC_04 Engineering Information Processing
LC_05 Candidate and Review Governance
LC_06 Coverage Evidence and Traceability Management
LC_07 Architecture Synthesis and Validation
LC_08 SysML v2 Artifact Generation
```

The view uses existing model elements, not presentation-only semantic components.

Interface labels/endpoint clutter were hidden for readability while retaining the connections. `LC_06` should read visually as cross-cutting, not as a sequential stage.

## Detailed Behavior

Existing:

```text
SFB_002 Engineering Transformation Lifecycle
```

remains the detailed control-oriented lifecycle with gates, review and targeted rework.

## High-Level Behavior

The new source-grounded lifecycle in ADR-027 is intended to become a legitimate high-level System Behavior above the detailed lifecycle.

```text
DO NOT add it to CATIA yet.
```

Model it only after the implementation follows the clarified architecture and ADR-027 is accepted. Do not change the model merely for presentation convenience.

---

# 11. UX Findings

Authoritative log:

```text
collaboration/ux/wp12_formative_self_evaluation_log.md
```

OBS-001..018 cover, among other things:

- project/global state consistency,
- Source-add and Project-creation interaction,
- scalable row actions,
- long Processing feedback/cancellation,
- live state after Source changes,
- Streamlit page-run coupling,
- misleading pre-review queue state,
- reviewer identity,
- reprocessing behavior,
- persona presentation,
- processing feedback/performance.

UX cleanup is secondary to BLK-003 recovery on the demo critical path.

---

# 12. Exact Next Action

The Source-to-first-Human-Review responsibility audit is complete and the
resulting ADR-027 architecture is accepted.

Implementation proceeds in bounded recovery slices:

```text
R1  Architecture/Thesis documentation alignment
R2  Source-grounded Evidence contract + persistence
R3  Specialized Evidence Detection Agent + Source Preparation integration
R4  Shared-Evidence persona interpretation + evidence-centered consensus/review
R5  Post-approval model derivation + downstream persona evaluation
```

Immediate implementation rule:

```text
Source Registry remains pure Source authority.
Source Preparation owns Source Projection + Evidence Detection.
The UI may combine registration/preparation for convenience.
The detector is one specialized persona-independent LLM task.
Interpretation personas consume the same persisted Evidence IDs.
No pre-review model derivation is allowed on the corrected active path.
```

Do not trigger another real LLM improvement run until R3/R4 materially change
the active Source-to-Human-Review path.

---

# 13. Repository Collaboration Rules

GitHub is passive for the assistant.

```text
inspect
→ propose
→ user review/acceptance
→ deterministic local patch
→ focused tests
→ regression where appropriate
→ git diff --check
→ exact staging only
→ user commit/push
→ verify HEAD == origin/main
```

Never use:

```text
git add .
git add -A
```
