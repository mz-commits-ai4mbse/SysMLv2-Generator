# Current Chat Handover

## Purpose

Authoritative starting point for the next Turing Generator chat after the
2026-08-20 WP-12 demo-readiness / architecture-recovery checkpoint.

Immediate deadline:

```text
Monday 2026-08-24 presentation + live demonstration
```

Repository:

```text
mz-commits-ai4mbse/SysMLv2-Generator
branch: main
```

Current Work Package:

```text
WP-12 — End-to-End Demo Hardening
```

Primary application:

```bash
streamlit run app/turing_generator_app.py
```

---

# Authority and Working Rules

Authority order:

1. CATIA SysML v2 model — accepted engineering knowledge
2. committed repository — implementation reality
3. Collaboration Knowledge Base / ADRs / checkpoints — decisions and coordination
4. chat history / temporary artifacts

GitHub is passive for the assistant.

Workflow:

```text
inspect
→ reason
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

Do not stage or commit before explicit acceptance.

---

# WP-12 Current State

Formal run:

```text
WP12-E2E-DRY-001
Project 308131
IN PROGRESS / INTERRUPTED FOR BLOCKING DEFECT CORRECTION
```

Do not describe it as failed, restarted or completed.

Blockers:

```text
BLK-001 derivation producer contract
→ corrected / focused validation passed

BLK-002 cross-source Processing Artifact identity collision
→ OPEN / BLOCKING
→ Monday demo is single-source

BLK-003 semantic effectiveness / engineering-subject quality
→ OPEN / ACTIVE ARCHITECTURE RECOVERY
```

Representative real single-source run:

```text
Project 877791
RUN-000001
3 personas × 1 run
real LLM

93 element proposals
41 relationship proposals
134 raw

D3: 70 elements + 39 relationships = 109
D4: 70 elements + 39 relationships = 109
Human Review: 110 items
```

Technical conclusion:

```text
D4 → Human Review works.
```

Engineering conclusion:

```text
source purity, model relevance and subject formation are not acceptable.
```

Review Item count is diagnostic only. Do not optimize it directly.

---

# Architecture Recovery — ADR-027

New proposed ADR:

```text
collaboration/decisions/
ADR-027-source-grounded-evidence-detection-and-persona-interpretation-architecture.md
```

Core target:

```text
REFERENCE KNOWLEDGE
Apollo 11 / SysML v2 / Modeling Guidance
        │ guidance only
        ▼
ENGINEERING SOURCE
        ↓
Deterministic Source Projection
        ↓
Find Source-Grounded Evidence
"digital text marker"
        ↓
Anchored Evidence Units
        ↓
Persona Interpretation / Classification
 P1            P2            P3
        ↓
Consensus / Variance
        ↓
Optional Semantic Normalization / Ontology Alignment
        ↓
Human Review
        ↓
Approved Engineering Information
        ↓
Architecture Derivation
        ↓
SysML v2
```

Hard rules:

```text
Reference Knowledge ≠ Engineering Evidence

Detection and Interpretation are separate responsibilities.

Personas interpret the SAME source-grounded evidence.

Personas and repeated runs shall not multiply Engineering Subjects.

Review Item count is a diagnostic, not an optimization objective.

Ontology/terminology mapping is a supporting service and shall not invent
positive Project engineering evidence.

AI-generated interpretation ≠ Approved Engineering Information.

Architecture Derivation follows Human Engineering Review / Approval.
```

P9/D3/D4 have no grandfathering protection.

Audit every material responsibility as:

```text
KEEP
MOVE
REDUCE
BYPASS
REMOVE / RETIRE
```

Ask:

```text
"What responsibility does this component legitimately own?"
```

not:

```text
"How do we keep the old component compatible?"
```

---

# ADR-011 Reuse

Do not discard ADR-011.

Still-useful foundations include:

- deterministic Source Projection,
- source anchors and exact excerpts,
- source-traceable Information Units,
- `engineering_source` vs `context_only`,
- epistemic classification,
- semantic extraction,
- deterministic consensus/variance,
- repeated runs as stability evidence rather than votes,
- terminology/ontology boundary,
- Human Review separation.

Important existing behavior to inspect:

```text
modules/semantic_consensus/analyzer.py
```

It already groups candidate discussion by exact source evidence
(anchors + source excerpt) and gives one effective vote per persona. This is
conceptually close to "same text-marker passage, different professional
interpretations".

---

# Gemini Diagnostic Benchmark

Source:

```text
legacy/demo/wp12/01_product_overview.md
```

A simple external Gemini prompt, with strict source-only evidence instructions,
returned eight major source-grounded findings covering:

1. collaboration capability / operator / remote expert / live view,
2. workstation and remote client context,
3. remote-consultation purpose,
4. live-image observation requirement,
5. temporary remote control subject to operator permission,
6. operator responsibility/controller transparency,
7. session retention and unresolved retention detail,
8. explicitly unspecified protocol/deployment/performance/latency/regulatory
   content and open questions.

Interpretation:

```text
The core LLM task is feasible.
The current Turing pipeline likely overcomplicates or mis-bounds it.
```

Caution: Gemini already made some premature model-form suggestions such as
State Machine/Guard. This output is a qualitative benchmark only, not a gold
standard and not Project authority.

---

# Exact Next Technical Work

Do NOT start another real LLM run yet.

First perform a read-only Source→first-Human-Review architecture/code-path audit.

Inspect at least:

```text
collaboration/decisions/ADR-011-semantic-information-unit-and-ontology-boundary.md
collaboration/decisions/ADR-015-project-bound-agentic-ingestion-integration.md
collaboration/decisions/ADR-027-source-grounded-evidence-detection-and-persona-interpretation-architecture.md

modules/semantic_extraction/
modules/semantic_consensus/
modules/information_units/
modules/review_workspace/p9_proposal_adapter.py
modules/review_workspace/p9_review_item_builder.py

agents/roles/legacy_data_interpreter.md
agents/roles/derivation_assessor.md
agents/personas/legacy_interpretation/
agents/personas/derivation_assessment/
teams/ingestion/
```

Also trace the actual app/service/pipeline functions connecting:

```text
registered Source
→ Source Projection
→ LLM input
→ persona outputs
→ P4/P9/D3/D4
→ Human Review materialization
```

For every material step report:

```text
component
exact input
exact output
Engineering Source vs reference/context/instruction boundary
source-anchor handling
subject-identity creation
persona responsibility
new semantic/model content created?
downstream dependency
KEEP / MOVE / REDUCE / BYPASS / REMOVE recommendation
```

Then propose the minimum corrected target path.

Do not implement until the audit is reviewed and accepted.

---

# Next Real LLM Run — Acceptance Criteria

Only after a material path correction.

Evaluate in this order:

```text
1 Source Purity
2 Model Relevance
3 Exact Source Grounding
4 Persona behavior on shared evidence
5 Useful Consensus / Variance
6 Human Review usability
7 Review Item count as diagnostic only
```

If credible, preserve that exact persisted Run immediately as the preferred
Monday reference.

Then test:

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

# Monday Demo Strategy

The demo is announced as a real live demonstration.

Preferred sequence:

```text
1. Open/create demo Project.
2. Show real Engineering Source.
3. Configure real single-source Processing.
4. Start actual LLM Processing live.
5. Let the audience see Processing genuinely running.
6. Explain the agent chain may take several minutes.
7. Switch transparently to a genuinely previously processed persisted state.
8. Continue Human Review live.
9. Approve/edit/reject as appropriate.
10. Promote Approved Engineering Information.
11. Continue Model/Architecture/SysML v2 live.
```

Recommended transition:

```text
"I'll start the processing step once live so you can see how the workflow is
actually triggered. Since the agent processing can take several minutes
depending on the model, I'll continue with a previously processed state of the
same workflow so that we can inspect the downstream engineering steps."
```

Do not represent manually curated data as unmodified live LLM output.

BLK-002 means Monday uses a single-source path.

---

# Presentation and CATIA

PowerPoint work resumes Monday.

Presentation story:

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

Original Kick-off flow:

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

CATIA logical architecture overview already exists using the eight existing
Logical Architecture part usages:

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

Existing detailed lifecycle:

```text
SFB_002 Engineering Transformation Lifecycle
```

remains authoritative.

The ADR-027 target flow is intended to become a legitimate high-level System
Behavior above SFB_002, but:

```text
DO NOT MODEL IT IN CATIA YET.
```

First implement the corrected architecture, then accept/revise ADR-027, then
update CATIA. Do not create presentation-only semantic model elements.

---

# Canonical Current Checkpoint

Read together with:

```text
collaboration/checkpoints/2026-08-20_wp12_demo_architecture_recovery_ssot.md
```

---

# New Chat Startup Prompt

Copy this into the new chat:

```text
We are continuing my Master-thesis prototype "Turing Generator"
(repository: mz-commits-ai4mbse/SysMLv2-Generator).

Please do not reconstruct the project from chat memory. Treat the repository
SSOT as authoritative coordination state.

First inspect, in this order:

1. collaboration/handovers/current_chat_handover.md
2. collaboration/checkpoints/2026-08-20_wp12_demo_architecture_recovery_ssot.md
3. collaboration/decisions/ADR-027-source-grounded-evidence-detection-and-persona-interpretation-architecture.md
4. collaboration/current_state.md
5. collaboration/roadmap.md
6. collaboration/decisions/ADR-011-semantic-information-unit-and-ontology-boundary.md

The immediate objective is WP-12 demo readiness for my Monday 2026-08-24
presentation/live demonstration.

Important current state:
- WP12-E2E-DRY-001 is IN PROGRESS / INTERRUPTED FOR BLOCKING DEFECT CORRECTION.
- BLK-002 cross-source Processing Artifact identity collision is still open;
  therefore the Monday demo path is single-source.
- BLK-003 semantic effectiveness is the active priority.
- The last real 3-persona × 1-run single-source test technically reached Human
  Review but produced source contamination, poor model relevance and subject
  multiplication.
- Do NOT start another LLM run yet.
- Do NOT optimize Review Item count directly.
- Do NOT add another semantic/post-processing contract before auditing the
  current path.
- ADR-027 captures the proposed architecture sharpening:
  deterministic Source Projection → source-grounded Evidence Detection →
  personas interpret the SAME evidence → consensus/variance → optional semantic
  normalization/ontology service → Human Review → Approved Engineering
  Information → Architecture Derivation → SysML v2.
- Reference knowledge, prompts, recipes, orchestration metadata and the Apollo 11
  reference may guide interpretation but must never become Project engineering
  evidence.
- Personas and repeated runs must not multiply Engineering Subjects.
- P9/D3/D4 responsibilities must be judged by legitimate responsibility, not
  compatibility. KEEP / MOVE / REDUCE / BYPASS / REMOVE is explicitly allowed.
- Existing ADR-011 Source Projection / Information Unit / source-role /
  source-anchor / semantic-consensus infrastructure should be reused where it
  still fits.
- A simple external Gemini benchmark on
  legacy/demo/wp12/01_product_overview.md returned eight sensible source-grounded
  findings. This is a qualitative diagnostic benchmark, not a gold standard or
  Project authority.
- The Monday demo should genuinely start the live LLM path, but may then
  transparently switch to a previously genuinely processed persisted Project
  state to avoid waiting for the LLM. The downstream Human Review → Approved
  Input → Model → SysML path should then be demonstrated live.
- PowerPoint work continues Monday. The CATIA logical architecture overview is
  already prepared. Do not model the new high-level source-grounded lifecycle in
  CATIA until it is implemented and ADR-027 is accepted.

Start with a READ-ONLY architecture/code-path audit from Engineering Source to
the first Human Engineering Review.

For every material step identify:
- exact input,
- exact output,
- which content is Engineering Source versus reference/instruction/context,
- where source anchors are created/preserved,
- where subject identity is created,
- how personas are used,
- whether the step can create new engineering/model content,
- downstream dependencies,
- recommendation: KEEP / MOVE / REDUCE / BYPASS / REMOVE.

Then propose the minimum corrected target path. Do not implement before I accept
the audit.

Repository workflow:
GitHub is passive. Give me exact repo-relative paths and deterministic local
commands/patches. Never use git add . or git add -A. Do not stage/commit before
explicit acceptance.
```
