# Turing Generator — Presentation, WP-12 and Demo SSOT Checkpoint

**Checkpoint date:** 2026-08-19  
**Status:** AUTHORITATIVE EXECUTION CHECKPOINT until superseded  
**Purpose:** Preserve the immediate work order, presentation plan, WP-12 evidence status, open findings/blockers, additional test plan, demo fallback strategy, and the deferred architectural recovery work.

---

## 1. Immediate priority order

The work order is intentionally changed because the professor demo is mandatory on Monday, 2026-08-24.

```text
NEXT
2026-08-20 — Presentation preparation during ICE travel
              + CATIA presentation-model preparation where possible offline

THEN
2026-08-20 evening → 2026-08-23
              — establish a reliable Monday demo path
              — prefer a real single-source path if semantically credible
              — otherwise prepare and validate Demo / Replay without LLM calls

OVER-NEXT
after presentation/demo path is secured
              — BLK-003 Architectural Recovery
              — restore model relevance and source purity before further
                semantic-consolidation optimization
```

No additional tactical BLK-003 implementation patch shall be started before the presentation/demo work unless it is strictly necessary to obtain a credible demo path.

---

## 2. Presentation preparation — governing concept

The existing presentation concept remains the starting point:

`collaboration/presentations/interim_presentation_plan.md`

The professor's last reference point is the original Kick-off presentation. The presentation shall therefore explicitly bridge from the original six-step process and the literature-derived three-layer architecture to the current governed architecture.

The original Kick-off reference is:

`KickOff_MasterArbeit_MZ_18032026.pptx`, especially slides 9 and 10.

### 2.1 Original Kick-off process

```text
1. Feature Ingestion
2. Sortier Agent
3. Ontologie Anpassung
4. Muster Antizipation
5. Human in the Loop
6. Synthese / SysML-v2 generation
```

### 2.2 Original architecture concept

```text
Data Layer
Process Layer
Knowledge Layer
```

The current architecture shall be presented as an operationalization and refinement of this baseline, not as an unrelated redesign.

### 2.3 Current presentation narrative

Use the following sequence as the presentation backbone:

```text
1. Kick-off recap / research objective
2. Literature-derived three-layer architecture
3. From six-step concept to governed system architecture
4. High-Level Activity Diagram in CATIA
5. Current implementation boundary / MVP completion path
6. Logical Architecture + layer realization in CATIA
7. Evidence of architectural development / requirement coverage
8. Current WP-12 verification status and honest open findings
9. Remaining work to complete the MVP
10. Outlook: adaptable artifact-driven Architecture-as-Code framework
```

The previous planning rule "create the actual presentation only after implementation is completed" is superseded by this checkpoint. Presentation preparation starts on 2026-08-20 because of the fixed professor/demo schedule. The deck must therefore distinguish clearly between:

```text
IMPLEMENTED + VERIFIED
IMPLEMENTED, EMPIRICAL EFFECTIVENESS OPEN
ARCHITECTURE / MODEL ONLY
PLANNED / NEXT
BLOCKED BY EXTERNAL OR KNOWN DEFECT
```

No slide shall imply product maturity or verified behavior that has not been demonstrated.

---

## 3. CATIA presentation models

Two CATIA views remain the central presentation artifacts.

### 3.1 High-Level Activity Diagram

Purpose: explain the complete intended MVP flow from one engineering source to validated SysML-v2 output.

Target top-level activities, obeying the 7 +/- 2 rule:

```text
1. Register Project & Source
2. Assess & Prepare Information
3. Apply Semantic Governance
4. Agentic Candidate Generation
5. Human Review & Approval
6. Derive & Structure Architecture
7. Validate Architecture
8. Generate & Validate SysML v2
```

Cross-cutting concepts to show without turning them into additional top-level activities:

```text
Processing Orchestration
Evidence
Traceability
Status / History
```

Meaningful Object Flows should use existing modeled Item Definitions where available, including:

```text
Legacy Engineering Data
Project and Source Context
Prepared Engineering Information
Semantically Governed Information
Engineering Candidate Set
Human Review Decision
Approved Engineering Information
Architecture Candidate
Validated Architecture
SysML v2 Artifact Set
Validation Findings
Versioned SysML v2 Output Package
```

The current implementation boundary and the complete MVP target must be visually distinguishable.

### 3.2 Logical System Architecture

Purpose: show how the literature-derived layers are realized by the current Logical Components.

Existing Logical Components:

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

Presentation mapping:

```text
Data Layer:
  LC_02
  LC_04
  LC_06

Process Layer:
  LC_01
  LC_03
  LC_05
  LC_07
  LC_08

Knowledge Layer:
  cross-cutting governance across especially
  LC_04 / LC_05 / LC_06 / LC_07
```

The Knowledge Layer shall not be forced into one artificial subsystem.

The Logical Architecture view should expose meaningful information exchanges, not only generic connectors.

---

## 4. WP-12 formal test status

Formal test:

```text
WP12-E2E-DRY-001
Project: 308131
Test type: controlled synthetic multi-document end-to-end dry run
```

Status:

```text
IN PROGRESS / INTERRUPTED FOR BLOCKING DEFECT CORRECTION
```

It is explicitly:

```text
NOT failed
NOT restarted
NOT completed
```

The formal project and its evidence shall remain untouched. The run shall not be restarted merely to hide or replace observed findings.

Stage B with representative non-synthetic data remains unauthorized until the Stage-A release gate can be passed on valid evidence.

Authoritative audit material remains:

```text
collaboration/audits/wp12_multi_document_dry_run_test_protocol.md
collaboration/audits/wp12_expected_engineering_contract.md
collaboration/audits/wp12_test_release_workflow.md
collaboration/ux/wp12_formative_self_evaluation_log.md
```

---

## 5. WP-12 blocker and finding register

### BLK-001 — Derivation Producer Contract

**Status:** CORRECTED / focused validation passed.

Observed issue:
the producer contract was too permissive for the strict downstream adapter.

Disposition:
bounded correction implemented and strict adaptation verified.

This remains evidence of test-driven hardening, not an active blocker.

### BLK-002 — Cross-Source Processing Artifact Identity Collision

**Status:** OPEN / BLOCKING.

Observed issue:
one Processing Artifact identity can be referenced across multiple source runs in the multi-document path.

Impact:

```text
multi-document processing cannot currently be accepted
formal WP-12 progression remains blocked
do not use multi-document live processing in the Monday demo
```

### BLK-003 — Semantic effectiveness / engineering-subject quality

**Status:** OPEN — ARCHITECTURAL RECOVERY REQUIRED.

#### BLK-003.1 robustness corrections

Implemented and focused-test validated:

```text
BLK-003.1A evidence identity correction
BLK-003.1B Human escalation for unresolved relationship endpoints
BLK-003.1C service failure taxonomy
```

Principle preserved:

```text
semantic uncertainty != integrity failure

unable to decide
→ Human Review

unable to trust identity / evidence / provenance
→ Processing Failure
```

#### ADR-026 / D1-D5 implementation status

```text
D1 Source Analysis Unit contract                     PASS
D2 Source-anchored Persona execution                PASS
D3 Local semantic consolidation                     PASS
D4 Cross-unit synthesis + endpoint rebinding        PASS by focused tests
D5 Human Review integration                         PASS technically
```

Focused D4-first Review routing and filter corrections are now validated by the focused suite:

```text
15 passed
git diff --check PASS
```

The existing real run reached Review Workspace persistence successfully.

#### Current empirical BLK-003 result

Retest:

```text
Project 877791
Run RUN-000001
Source 01_product_overview.md
3 Personas x 1 run
real LLM processing
```

Observed counts:

```text
Raw proposals:
  Elements       93
  Relationships  41
  Total         134

D3 local subjects:
  Elements       70
  Relationships  39
  Total         109

D4 synthesized subjects:
  Elements       70
  Relationships  39
  Total         109

Human Review:
  Element items       70
  Relationship items  39
  Open Questions       1
  Total              110
```

The additional Open Question is a legitimate classification uncertainty for `microscope workstation`.

Technical D4 → Human Review routing is therefore working.

Semantic effectiveness is not acceptable.

#### Current qualitative BLK-003 failures

1. **Source purity regression**

Orchestration/task/process information is being interpreted as positive engineering content.

Observed examples include:

```text
raw input artifact path
Markdown ingestion report
Document status heading
structured placeholder feedback file
traceability record or placeholder
task file content completeness constraint
project traceability and human review constraint
```

These do not represent the intended Remote Microscope system model and must not become normal engineering subjects merely because they occur in orchestration context.

2. **Model relevance regression**

Candidate generation no longer consistently answers:

```text
What concrete SysML-v2-relevant engineering concept is being proposed?
```

The system is currently producing overly generic artifact/process subjects instead of consistently proposing model-relevant actors, parts, items, requirements, constraints, interfaces, capabilities and relationships.

3. **Cross-unit consolidation ineffective**

D4 produced:

```text
109 local subjects
→ 109 synthesized subjects
```

Visible near-duplicate engineering statements nevertheless remain separate.

Therefore zero cross-unit compression is not accepted as a valid semantic outcome for this run.

4. **Human Review usability / Agent proposal cards**

The individual Agent cards remain too text-heavy and do not make the proposed model content sufficiently explicit.

A review card must make the following obvious without reading rationale prose first:

```text
Proposed model kind / classification
Proposed name
Concrete engineering meaning
Source statement
Agent / Persona
Confidence
```

Example target:

```text
Type: Actor
Name: Microscope Operator
Meaning: Local operator responsible for the microscope session
Source: "..."
Persona: Architecture Focused Assessor
Confidence: high
```

5. **Review-item count is not an optimization target by itself**

The architecture shall no longer be optimized primarily for reducing Review Item count.

Correct objective:

```text
preserve all distinct, model-relevant engineering meaning
+
merge genuinely equivalent interpretations
+
escalate real uncertainty
```

Twenty-five distinct valid subjects may legitimately produce twenty-five Review Items.

Three Personas identifying the same twenty-five subjects shall not produce seventy-five independent Review Items.

---

## 6. Preserved empirical evidence

Do not delete or overwrite these projects/runs merely because later behavior changes:

```text
308131
  formal WP12-E2E-DRY-001 project
  must remain untouched

887027
  earlier BLK-003 POST evidence
  112 Review Items / singleton-degradation evidence

159161
  PRE BLK-003.1A/1B failure evidence

691616
  expensive 3 Personas x 2 runs evidence
  198 successful Stage-01..03 LLM responses
  source-wide completeness request exceeded practical prompt size
  preserved for repetition/stability evidence

877791
  current 3 Personas x 1 run
  bounded completeness successful
  D4 reached
  D4-first Review Workspace successfully materialized
  110 Review Items
  source-purity/model-relevance/cross-unit-effectiveness regression evidence
```

Do not make Human Review approval decisions in 877791 before the evidence has been fully characterized.

---

## 7. WP-12 formative UX / integration observation register

The following observations remain recorded. Unless a later explicit retest closes them, treat them as OPEN / NOT YET REVALIDATED.

```text
OBS-001  Project selection lost on toggle
OBS-002  Add-first-source route / discoverability
OBS-003  Duplicate Create Project interaction
OBS-004  Multi-file visual plus / affordance
OBS-005  Drag-and-drop first-click behavior
OBS-006  Row-action selection scalability — MUST
OBS-007  Long Processing feedback — MUST
OBS-008  Processing cancellation architecture — SHOULD
OBS-009  Optional tips / guidance
OBS-010  Agent scope label clarity
OBS-011  Live state inconsistent after source change
OBS-012  Processing coupled to active Streamlit page run
OBS-013  Review Queue misleading zero before workspace materialization
OBS-014  Reviewer identity confirmation
OBS-015  No explicit reprocessing of an already processed Source
OBS-016  Persona configuration presentation
OBS-017  Long-running Processing feedback / performance
OBS-018  Global Project Selector session-state conflict
```

Progress UX requirement remains:

```text
show work packages / units of work
not elapsed time or invented ETA

PENDING → RUNNING → COMPLETED
                  → SKIPPED
                  → FAILED
```

If a progress bar is used:

```text
(COMPLETED + SKIPPED) / TOTAL PLANNED WORK UNITS
```

Retries/provider calls are nested evidence, not top-level progress units.

---

## 8. Additional planned verification

The following test families are required in addition to completion/resumption of the formal WP-12 protocol.

### 8.1 SOURCE-PURITY / MODEL-RELEVANCE acceptance test

Must be added before BLK-003 can close.

Purpose:

```text
prove that orchestration metadata cannot become positive engineering evidence
prove that generated candidates are relevant to the intended system model
```

Acceptance examples:

```text
FAIL:
local repository path becomes a System Element
recipe output file becomes a domain element
prompt/task instruction becomes a Requirement
orchestration heading becomes a modeled domain concept

PASS:
microscope operator
remote expert
live microscope image
temporary control capability
operator-permission constraint
source-supported relationships
```

### 8.2 STABILITY test

Working configuration:

```text
3 Personas x 2 repetitions
same fixed Source
same model/provider/configuration
```

Purpose:
measure intra-Persona repeatability without turning repeated runs into additional votes.

Rule:

```text
one Persona = at most one recognition vote per source-evidence cluster
repeated runs = stability evidence only
```

Measure at least:

```text
candidate identity stability
classification stability
source-evidence stability
semantic grouping stability
relationship endpoint stability
Review Subject stability
```

This test shall be executed only after the architectural recovery has restored source purity and model relevance. The preserved 691616 run may be used as historical repetition evidence but does not by itself prove the corrected architecture.

### 8.3 DASH test — dashboard/state presentation

Working definition:
a deterministic dashboard and workflow-state consistency test across the Guided Workflow.

Verify:

```text
project selection remains stable
source counts/status remain consistent
Processing state is identical across dashboard and Processing view
work-package progress is monotonic and work-based
awaiting_review / review-in-progress transitions are represented correctly
Review Item / decision counts are not misleading
navigation does not silently mutate or lose current project/run context
stale UI state does not overwrite authoritative persisted state
```

This test shall explicitly cover OBS-001, OBS-011, OBS-012, OBS-013, OBS-017 and OBS-018.

### 8.4 Demo / Replay validation

Before Monday, validate the exact fallback path from a clean app start.

Verify:

```text
no LLM/network call required
prepared run/data loads deterministically
UI clearly labels replay/prepared processing
same Human Review / Approval authority boundaries are used downstream
no prepared AI output is silently presented as freshly generated live output
all required files are available locally/offline
rehearsal succeeds after app restart
```

### 8.5 Full regression

Before a demo freeze or formal WP-12 release decision:

```text
focused corrected suites
+ relevant workflow regression
+ complete repository regression
+ git diff --check
```

No release claim may be based only on focused tests.

---

## 9. Monday demo strategy

**Mandatory demo date:** Monday, 2026-08-24.

The demo objective is:

```text
show a traceable AI-assisted Engineering workflow
with explicit Human authority
```

It is not:

```text
pretend that the prototype is production-ready
```

### Mode A — Live Golden Path

Use only if a fresh single-source run is semantically credible and operationally reliable by the evening of 2026-08-20.

Recommended live configuration:

```text
1 Source
3 Personas
1 run per Persona
real LLM
```

Do not use the multi-document path while BLK-002 is open.

### Mode B — Demo / Replay — REQUIRED FALLBACK

Trigger:

```text
If the system is not demonstrably credible by the evening of 2026-08-20,
Demo / Replay becomes the primary Monday plan.
```

Replay characteristics:

```text
no LLM calls
no dependency on train/mobile internet
prepared representative processing data
deterministic project/run identity
normal downstream navigation
normal Human Review / Approval mechanism
explicit label that processing results are replayed/prepared
```

This is a controlled simulation, not a deceptive fake-live run.

Preferred implementation concept:

```text
Processing Mode

○ Live Processing
  actual Agent / LLM execution

○ Demo / Replay
  load a stored accepted reference run

[Advanced]
□ Dry Run
  technical deterministic pipeline test
```

Do not silently copy arbitrary artifacts between existing project identities. Demo data must be prepared with coherent project/source/run identity and provenance.

### Mode C — Controlled Walkthrough

If even Replay cannot be made reliable, use stable UI/screens/persisted evidence and CATIA models to explain the architecture and authority boundaries.

The presentation and CATIA models must make this fallback credible without requiring live LLM execution.

### Demo freeze

Once one demo path is verified, freeze it.

During the Monday demo:

```text
no code changes
no cleanup
no experimental reruns
no multi-document live test
no SYSIDE-CLI bypass
```

---

## 10. Architectural Recovery — over-next work item

This work starts only after the presentation and Monday demo path are secured.

Status:

```text
BLK-003 — ARCHITECTURAL RECOVERY REQUIRED
```

Do not resume by patching the next P9 exception or comparator symptom.

### 10.1 Re-establish the system mission

The productive flow must return to:

```text
Legacy engineering source
→ source-bound interpretation
→ SysML-v2-relevant engineering candidates
→ semantic equivalence / consolidation
→ Human Review of engineering subjects
→ Approved Input
→ architecture/model candidate
→ SysML v2
```

### 10.2 Mandatory invariants

#### Source purity

Only engineering meaning supported by the intended Source may become positive Engineering Evidence.

Recipe/task/run/file-path/prompt/orchestration metadata is not domain evidence.

#### Model relevance

Every productive proposal must say what it represents in the intended downstream engineering model.

#### Explicit typing

Proposals shall expose a meaningful classification, for example:

```text
Actor
Part
Item
Requirement
Constraint
Interface
Capability
Relationship
classification unresolved
```

The exact vocabulary shall be reconciled with the modeled SysML-v2 target contracts.

#### Consolidation is not abstraction

Consolidation may merge equivalent interpretations.

It shall not remove useful model semantics merely to reduce Review Item count.

#### Human Review reviews engineering

The Human reviewer shall decide on engineering subjects, not reconstruct model meaning from Agent prose or review ingestion/orchestration artifacts.

### 10.3 Architecture inventory

Review the current productive chain and classify each responsibility:

```text
KEEP
CHANGE
REPLACE
REMOVE FROM PRODUCTIVE PATH
```

Inventory:

```text
Source Projection / SourceAnalysisUnit
Agent input contract
Agent output schema
P9 proposal/admissibility layer
D3 local semantic consolidation
D4 cross-unit synthesis
D5 Review projection
generic Human Review Workspace
Approved Input promotion
Agent-card / Review UI
```

### 10.4 P9 question

The architectural question is:

```text
What responsibility does P9 still legitimately own in the new architecture?
```

Not:

```text
How can every new architecture stage be made compatible with P9?
```

Potential outcome to evaluate, not pre-decide:

```text
P9 compatibility / provenance layer only
SES/SRS or successor engineering-subject contract as productive Review input
generic Review infrastructure retained
```

### 10.5 Regression comparison

Explicitly compare the current system against the pre-BLK-003 behavior.

Identify where changes improved:

```text
identity
provenance
Human escalation
review routing
```

and where they regressed:

```text
engineering/model relevance
source purity
proposal clarity
semantic usefulness
```

No existing layer is protected merely because substantial implementation effort has already been invested.

---

## 11. Immediate starting instruction for the next work session

### If working offline / on the ICE on 2026-08-20

Start with presentation work, not implementation.

```text
1. Open collaboration/presentations/interim_presentation_plan.md
2. Use the Kick-off 6-step / 3-layer comparison as the narrative anchor
3. Draft the slide storyline
4. Define the two CATIA diagrams:
   - Logical System Architecture
   - High-Level Activity Diagram with Object Flows
5. Mark implementation status honestly on every relevant slide
6. Prepare the WP-12 findings / limitations slide
7. Prepare the Demo / Replay explanation as contingency
```

### When stable development access is available again

```text
1. Decide whether Mode A live demo is still credible.
2. If not credible by 2026-08-20 evening:
   commit to Mode B Demo / Replay.
3. Prepare and verify the replay dataset/path.
4. Rehearse from a clean app restart.
5. Freeze the demo path before Monday.
6. After demo readiness is secured:
   begin BLK-003 Architectural Recovery.
```

---

## 12. Checkpoint acceptance rule

This checkpoint does not close WP-12, BLK-002 or BLK-003.

It freezes the immediate work order and prevents further local bug-fixing from displacing the two time-critical objectives:

```text
1. professor presentation
2. reliable Monday demo
```

Only after these are secured does architectural recovery resume.
