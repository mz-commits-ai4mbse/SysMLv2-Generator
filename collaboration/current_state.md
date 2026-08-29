# Current Project State

<!-- BEGIN SSOT UPDATE 2026-08-29 MULTISOURCE DEMO TRANSITION -->
## 2026-08-29 — Presentation pause / Multi-Source demo transition

This block supersedes older immediate-next-action wording where it conflicts.

Accepted implementation baseline:

```text
main / origin/main: 6d9a600dfa1883d5d6b57f40bfb870ebf6e4cdd6
version:            v0.3.0
Project 000116 single-source Gate 3: PASS
real SYSIDE validation:               PASS
Human release / immutable publication: PASS
complete regression:                  6100 passed
```

The current interim-presentation draft and CATIA presentation diagrams are good
enough for now. Final slide polishing is intentionally deferred until closer to
the presentation date.

Latest working master deck outside the repository:

`AbschlussPräse_MasterArbeit_MZ_29082026(3).pptx`

The authoritative CATIA model was updated with the current presentation model
code. The user-maintained textual snapshot is `CATIAMSOSA_TextualNotation.txt`.

Current CATIA presentation artifacts:

```text
SFB_004 Engineering Data Transformation Flow
SFB_005 Engineering Information Processing Flow
Logical Architecture presentation view
Three-Layer Architecture Mapping
```

### BLK-002 decision

`BLK-002 — Cross-Source Processing Artifact Identity Collision` remains
`OPEN / BLOCKING`, but is now explicitly classified:

```text
THESIS-CRITICAL
DEMO-CRITICAL
NEXT TECHNICAL WORK
```

True Multi-Source is required before the intended Safe Demo. The PoC shall show
that multiple heterogeneous legacy Sources contribute to one governed
project-level engineering result, not merely several independent single-source
runs.

Target principles:

- no a-priori Source hierarchy;
- all eligible Sources are considered;
- exact Source / Run / Attempt / Artifact provenance is preserved;
- semantically equivalent information may consolidate across Sources;
- Source-unique information survives;
- contradictions / material variance remain explicit for Human Review;
- Human authority remains unchanged;
- no Project-specific shortcut or automatic truth arbitration.

Safety rule:

```text
clean Known-Good main
→ dedicated disposable feature/blk-002-multi-source branch
→ read-only audit first
→ bounded correction
→ focused tests
→ complete regression
→ real Multi-Source E2E
→ explicit Human acceptance
→ only then consider integration
```

Do not mutate / regenerate accepted Project `000116` merely to simplify
Multi-Source work.

Detailed authority:

`collaboration/checkpoints/2026-08-29_presentation_demo_multisource_handover_ssot.md`

Future learning concept retained separately:

`collaboration/checkpoints/Thesis_Outlook_Adaptive_Human_Feedback_Learning.md`
<!-- END SSOT UPDATE 2026-08-29 MULTISOURCE DEMO TRANSITION -->

<!-- BEGIN THESIS COMPLETION STRATEGY 2026-08-27 -->
## Thesis completion strategy — accepted 2026-08-27

The successful Project `000116` Gate-3 run changes the role of further
implementation work.

The validated single-source vertical prototype is now the empirical baseline
for the remainder of the thesis.

The governing principle for all remaining development is:

> Further implementation after Gate 3 is justified only where it is required
> to substantiate an open thesis claim, close a thesis-critical validation gap,
> or establish the final prototype baseline. Open implementation findings are
> not automatically remaining thesis scope.

This explicitly prevents the remaining thesis work from becoming an
open-ended backlog-completion exercise.

Current thesis-oriented execution sequence:

```text
1. Professor presentation
2. Safe Demo / Kochshow preparation
3. Gate-3 thesis evaluation record
4. Thesis Scope Gate
5. Explicit BLK-002 decision
6. Final targeted validation
7. CATIA / architecture synchronization
8. Prototype implementation freeze and final baseline
9. Thesis Results / Discussion / Limitations finalization
10. Final claim / traceability / consistency audit
11. Thesis completion / submission
```

### Immediate next work

```text
NOW:
Professor presentation

THEN:
Safe Demo preparation

THEN:
freeze and document Gate-3 empirical evidence
```

The presentation and Safe Demo are not additional prototype feature phases.
They communicate and demonstrate the currently validated system.

### Thesis Scope Gate

After the Gate-3 evaluation record has been prepared, all remaining open
technical findings shall be classified explicitly as one of:

```text
THESIS-CRITICAL
→ must be resolved and revalidated

VALIDATION-USEFUL
→ perform only where evidence gain justifies effort

LIMITATION / FUTURE WORK
→ document explicitly; do not implement for the thesis

PRODUCT / UX / TECHNICAL DEBT
→ outside remaining thesis implementation scope unless it blocks evidence
```

Open BLK / SEM / OBS findings therefore do not automatically become work
packages.

### BLK-002 decision

`BLK-002 — Multi-Source Processing Artifact Identity / provenance`

requires an explicit thesis-scope decision.

Decision alternatives:

```text
A. Multi-Source is required to substantiate the research claim
   → resolve BLK-002
   → focused verification
   → real joint Multi-Source E2E
   → downstream validation

B. Single-Source proof is sufficient for the bounded prototype claim
   → retain BLK-002 as explicit limitation / Future Work
   → do not spend thesis time implementing it
```

This decision shall be based on the research question and thesis claim, not on
the mere existence of the blocker.

### Final architecture synchronization

After the last thesis-critical implementation change, synchronize the
authoritative CATIA / architecture representation with the final implemented
prototype.

The final state shall align:

```text
research architecture
↔ CATIA engineering model
↔ implemented prototype
↔ thesis description
↔ empirical claims
```

### Final implementation freeze

After final validation and CATIA synchronization:

```text
complete regression
→ manual / real acceptance where required
→ SSOT synchronization
→ final implementation commit / integration
→ verified baseline
→ implementation freeze
```

After the freeze, new feature work requires a demonstrated thesis-critical
reason.

### Thesis finalization

Results, Discussion and Limitations shall be finalized against the frozen
prototype evidence.

The final thesis audit must specifically verify that claims do not exceed the
demonstrated evidence regarding:

- Multi-Source Processing;
- degree of automation;
- Human vs. AI authority;
- SysML v2 construct coverage;
- external validation;
- generalizability;
- production readiness.

Current project principle:

```text
The thesis now drives implementation.
Implementation no longer defines the thesis scope.
```
<!-- END THESIS COMPLETION STRATEGY 2026-08-27 -->


<!-- BEGIN SSOT UPDATE 2026-08-27 V0.3.0 GATE3 CLOSEOUT -->
## v0.3.0 Gate-3 real validation closeout — 2026-08-27

This delta supersedes older current-status and next-action statements below
where they conflict with this section.

Current accepted state:

```text
Active branch: feature/processing-semantic-normalization
Target build:  v0.3.0

Project 000116 Lead-Source Gate 3: COMPLETE / PASS
Real SYSIDE validation:              PASS
Human publication approval:          PASS
Immutable Published Output:          PASS
Complete repository regression:      6100 passed
git diff --check:                    PASS
```

Validated Lead Source:

```text
Project:              000116
Lead Source:          SRC-000002 / 01_product_overview.md
Base IEM:             IEM-000001
Target authority:     TFA-000002
Quality authority:    MQA-000002
Approved successor:   IEM-000003
Final Model Review:   FMR-000001
Accepted revision:    FRV-000002
Human release:        FRD-000001
Published Output:     OUT-000001
```

The governed real workflow reached:

```text
Engineering Source
→ Processing
→ Human Engineering Review
→ Approved Input
→ Model Placement
→ Model Assembly Review
→ Base Internal Engineering Model
→ Target-Model Formulation
→ Human Model Quality Review
→ Human-authorized successor IEM
→ deterministic SysML v2 generation
→ external SYSIDE validation
→ Final Model Review
→ Human release approval
→ immutable publication
```

Final generated-artifact fingerprint:

`7b5babbe048f941d9875a345e34a03e1c249061a93e03ade3c9dcfb971f4ddb1`

Final validation fingerprint:

`0e8998e6fe2d4b717cbee6464cdca1b060ad21601dd92389706240b38387ea67`

External validation:

```text
SYSIDE Modeler CLI 0.10.3
execution completed
exit code 0
diagnostics 0
validation VALID
publication gate PASSED
```

Final complete regression:

```text
6100 passed in 17.87s
```

### Gate-3 findings resolved during the real run

The real validation exposed and corrected bounded implementation gaps rather
than weakening downstream validation:

1. incomplete Model Refinement could reach a downstream wrapper without a
   successor IEM;
2. SEM-015 materialization required normalization of dataclass Human-authority
   structures;
3. Target-Model Formulation did not re-evaluate an existing relationship after
   an endpoint's effective SysML construct changed;
4. immutable formulation revision support was required;
5. the actual Guided Workflow Final Model Review lacked a safe retry path for a
   historical incomplete SYSIDE infrastructure result;
6. the Target-Model Formulation Generation Profile path depended unnecessarily
   on process CWD and was hardened to explicit `repo_root` ownership.

The Phase-J generation guard remained fail-closed throughout.

### Relationship compatibility finding

`IMR-000001` remained valid engineering information but became incompatible
with the effective formal endpoint constructs authorized for SysML generation.

The generic correction now:

- re-evaluates supported relationships against effective post-formulation
  endpoint constructs;
- leaves compatible relationships untouched;
- reopens only incompatible relationships for Human Target-Model authority;
- preserves the engineering relationship when no supported formal notation is
  currently authorized;
- does not add Project-specific exceptions.

For Project `000116`, Human authority explicitly selected
`intentionally_not_materialized` for `IMR-000001`.

### Claim boundary

This is successful **single-source** end-to-end validation.

It does not resolve or weaken:

`BLK-002 — Multi-Source Processing Artifact Identity / provenance blocker`

Four independently successful Source paths do not establish true Multi-Source
Processing.

### Current next activity

```text
Professor presentation
→ use collaboration/presentations/interim_presentation_plan.md
→ then prepare Safe Demo with agreed Kochshow strategy
```

Do not restart or regenerate Project `000116` merely to simplify presentation
or demo preparation.

Detailed authority:

`collaboration/checkpoints/2026-08-27_gate3_validation_handover_ssot.md`
<!-- END SSOT UPDATE 2026-08-27 V0.3.0 GATE3 CLOSEOUT -->


<!-- BEGIN SSOT UPDATE 2026-08-25 WP12 GOLDEN E2E CLOSEOUT -->
## WP-12 Golden E2E Known-Good baseline — 2026-08-25

Current accepted status:

```text
WP-12 single-source Golden E2E: PASS
Demo-ready: YES
WP-12 remaining blocker: BLK-002 Multi-Source
```

Project `120412` completed the Human-authority-backed path through `IEM-000002`,
successful real SYSIDE validation, `FMR-000001 / FRV-000002`, Human release
`FRD-000001` and immutable publication `OUT-000001`.

Published SysML:

`data/output/120412/OUT-000001/generated_model.sysml`

Verification baseline:

```text
focused TN_003 synchronization: 29 passed
complete repository regression: 6046 passed
git diff --check: PASS
SYSIDE: completed / exit 0 / diagnostics 0
```

Canonical detailed checkpoint:

`collaboration/checkpoints/2026-08-25_wp12_golden_e2e_known_good_baseline.md`

The closeout commit containing this checkpoint establishes `main` as the Known-Good
fallback. New implementation work must use dedicated feature branches.

Exact next activity:

```text
BLK + SEM + ODS cross-register triage
→ prioritize
→ select bounded feature branch
```

No new feature implementation shall be started as part of this SSOT closeout.
<!-- END SSOT UPDATE 2026-08-25 WP12 GOLDEN E2E CLOSEOUT -->

<!-- BEGIN SSOT UPDATE 2026-08-20 -->
## SSOT Delta — 2026-08-20: WP-12 Demo Readiness and Architecture Recovery

This delta supersedes older WP-12 schedule/status statements below where they conflict with the current state.

Current objective:

```text
WP-12 Demo Readiness
→ BLK-003 source-grounding / semantic recovery
→ one credible real single-source run
→ downstream live workflow rehearsal
→ Monday 2026-08-24 presentation/live demo
```

Formal status:

```text
WP12-E2E-DRY-001
Project 308131
IN PROGRESS / INTERRUPTED FOR BLOCKING DEFECT CORRECTION
```

Blockers:

```text
BLK-001 corrected / focused validation passed
BLK-002 OPEN / BLOCKING cross-source identity collision
BLK-003 OPEN / ACTIVE semantic/source-grounding recovery
```

Representative real run:

```text
Project 877791 / RUN-000001
3 personas × 1 run
93 element + 41 relationship proposals = 134 raw
D3 = 109 subjects
D4 = 109 subjects
Human Review = 110 items
```

Technical D4→Review routing works; semantic quality is not accepted.

Proposed architecture recovery:

`collaboration/decisions/ADR-027-source-grounded-evidence-detection-and-persona-interpretation-architecture.md`

Core:

```text
Engineering Source
→ deterministic Source Projection
→ source-grounded Evidence Detection
→ personas interpret the SAME evidence
→ consensus / variance
→ optional terminology / ontology alignment
→ Human Review
→ Approved Engineering Information
→ Architecture Derivation
→ SysML v2
```

Review Item count is diagnostic, not an optimization objective. Personas and repeated runs must not multiply Engineering Subjects.

P9/D3/D4 responsibilities shall be audited as:

```text
KEEP / MOVE / REDUCE / BYPASS / REMOVE
```

No new real LLM run is warranted until the active Source→Human-Review path has been audited and at least one material correction has been made.

Monday demo strategy:

- start the real single-source LLM Processing path live,
- transparently switch to a genuinely previously processed persisted state if waiting time would interrupt the demo,
- continue Human Review → Approved Input → Model → SysML live,
- use single-source because BLK-002 remains open.

The clarified high-level source-grounded lifecycle is intended for CATIA only after implementation alignment and ADR-027 acceptance.

Canonical checkpoint:

`collaboration/checkpoints/2026-08-20_wp12_demo_architecture_recovery_ssot.md`
<!-- END SSOT UPDATE 2026-08-20 -->

## Purpose

This document describes the current accepted project status, the committed
implementation reality and the active development objective of the Turing
Generator.

It is updated during every `SSOT UPDATE`.

It shall not redefine engineering knowledge contained in the authoritative
CATIA SysML v2 model.

---

# Project

Project

Turing Generator

Repository

`mz-commits-ai4mbse/SysMLv2-Generator`

Current Branch

`main`

Verified Implementation Reference

`commit containing this SSOT update` — WP-11 Architecture / Model Proposal UX completion

Last Prior Committed Checkpoint

`63b911dbf5da9b4a2be7013553fd8d47f4e30db4` — WP-10 final formatting checkpoint

Architecture Version

1.13

Knowledge Base Version

1.20

Implementation Version

0.22

Current Roadmap Version

1.20

Current Development Phase

WP-12 — End-to-End Demo Hardening

Current Status

WP-11 Architecture / Model Proposal UX is completed and verified. WP-12
End-to-End Demo Hardening is active. The controlled multi-document Stage-A dry-run
test design, synthetic source fixtures, expected Engineering Contract, detailed
test protocol, formative self-evaluation log and Stage-A→Stage-B release workflow
are prepared and explicitly accepted for execution. Formal Stage-A execution is
scheduled for 2026-08-17; Stage B remains unauthorized until the Dry-Run Release
Gate is explicitly passed.

Verified Automated Test Baseline

5577 passed, 1 skipped in 14.19s in the complete repository regression after WP-11.

WP-11 Focused Regression

40 passed in 0.52s.

WP-09 Focused Regression

111 passed in 0.63s.

Phase-L Focused Regression

147 passed, 1 skipped in 1.63s.

Phase-K Focused Regression

65 passed in 1.41s.

Phase-H9 Focused Regression

61 passed in 0.69s.

Phase-H9 Live LLM Smoke Test

PASS — one bounded OpenAI call using `gpt-5-mini`.

Observed usage:

```text
input_tokens: 711
output_tokens: 634
reasoning_tokens: 512
total_tokens: 1345
```

The live result selected `ELEMENT_SYSTEM_FUNCTION`, producing
`system.functional` / `function` with `partially_supported` semantic support.
No retry and no Candidate Set persistence were used.

Phase-G Focused Completion Regression

65 passed in 8.95s.

Phase-G Manual Acceptance

PASS

Closed Vertical-slice Target

2026-08-14

Functional Freeze

2026-08-17

Product Demo

2026-08-18

Last SSOT Update

2026-08-16

---

# Current Objective

Execute WP-12 End-to-End Demo Hardening without weakening the already closed
engineering authority chain. WP-11 is complete. WP-12 now prepares one connected
demo Project, exercises the complete Source→OUT workflow and records a formative
task-based self-evaluation before the product demo on 2026-08-18.

The accepted executable path remains:

```text
Source
→ Processing Run
→ Human Review
→ Approved Input
→ Model Candidates
→ Internal Engineering Model
→ SysML v2 Generation
→ Validation
→ Final Model Human Review
→ Human Release Approval
→ Versioned Output Package
```

The implementation sequence is now:

```text
WP-09 — Guided Workflow UI                     COMPLETE
→ WP-10 Ingestion + Human Review UX Simplification COMPLETE
→ WP-11 Architecture / Model Proposal UX          COMPLETE
→ WP-12 End-to-End Demo Hardening                  ACTIVE
   test specification / fixtures                   ACCEPTED + PREPARED
   formal Stage-A dry run                          PENDING 2026-08-17
→ WP-13 Functional Freeze + Rehearsal
→ WP-14 CATIA / SSOT Checkpoint
→ product demo
```

The Zwischenstandspräsentation no longer blocks Phase H. It is prepared after
the implementation work so that it can present the complete implemented
architecture and evidence.

---

# Current Engineering Priorities

Priority 1

Execute WP-12 End-to-End Demo Hardening with one representative Project and a
formative task-based self-evaluation while preserving all Source, Human Review,
Candidate, IEM, validation, release and publication authority boundaries.

Phase L shall accept only an explicit `GeneratedSysMLArtifactSet` together with
the exact `SysMLValidationResult` covering that artifact fingerprint.

Publication remains blocked unless:

```text
validation_status == valid
publication_gate == passed
validation_result.source_artifact_set_fingerprint == artifact_set.content_fingerprint
```

No implicit latest artifact selection and no publication of `incomplete` or
`invalid` validation results is allowed.

Priority 2

Complete the H–L closed vertical slice without reducing quality or weakening:

- Human Review authority
- project isolation
- source and artifact traceability
- deterministic validation
- immutable published evidence
- CATIA engineering authority
- explicit artifact contracts

Priority 3

Use the system-wide interaction principle accepted in ADR-017:

```text
Simple by default.
Explainable on demand.
Fully traceable underneath.
```

Primary workflow views shall emphasize the engineering result, material
uncertainty, required human decision and next action. Detailed rationale,
evidence and audit identifiers remain available through progressive disclosure.

Priority 4

Keep Streamlit as the prototype UI technology through the 2026-08-18 product
demo. No React, Vue or FastAPI rewrite is part of the demo critical path.

Priority 5

After H–L closes the technical vertical slice, perform a targeted guided-workflow
UX pass covering Agentic Ingestion, Human Review, model proposal interaction and
final SysML v2 result presentation.

Priority 6

Preserve the literature-derived presentation framing:

```text
Data Layer
Process Layer
Knowledge Layer
```

The eight Logical Components operationalize these responsibilities. The
Knowledge Layer is cross-cutting governance rather than a forced single
subsystem.

Priority 7

Preserve artifact-driven architectural adaptability as an explicit outlook:
stable processing architecture plus versioned replaceable recipes, profiles,
context, framework and semantic artifacts shall allow controlled adaptation
without uncontrolled runtime behavior.

Priority 8

Continue Model Element Change Candidate tracking. CATIA remains the engineering
authority and no implementation observation becomes an accepted CATIA change
without explicit engineering review.

---

# WP-09 — Guided Workflow UI

WP-09 is completed and verified.

Architecture decision:

`collaboration/decisions/ADR-024-guided-engineering-workflow-and-ux-projection-architecture.md`

Accepted interaction principles:

```text
Engineering Content before Metadata
Decision-Centered Interaction
Variance is First-Class Information
Side-by-Side before Aggregation
Simple by default.
Explainable on demand.
Fully traceable underneath.
```

Completed slices:

```text
WP-09.1  Guided Engineering View + presentation models
WP-09.2  global shell, navigation, Engineer Home and Next Action
WP-09.3  Model Proposal, Final Model Review and Published Output detail views
WP-09.4  authority-preserving Human write actions and exact publication bridge
```

Implemented capabilities include:

- one common Project context across the application
- global Focused / Technical presentation depth
- engineer-centered `Your work` and `Next action`
- deterministic Guided Workflow read model with no parallel authority state
- explicit selection when multiple Candidate / Review / Output heads exist
- Model Proposal detail workspace
- Final Model Review detail workspace with exact generated SysML
- Published Output detail workspace
- Candidate `Accept`, `Reject`, `Defer` and `Accept as exception`
- immutable Final Model Review Change Proposal submission
- exact Human release approval
- exact FRV-to-publication bridge through persisted J/K snapshots
- publication only through the existing `OutputWriter`
- authoritative read-side reconstruction after writes
- deferred Human Review outcomes retained as unresolved Human work

Verification:

```text
WP-09 focused regression:
111 passed in 0.63s

Complete repository regression:
5542 passed, 1 skipped in 13.36s

git diff --check:
PASS
```

Manual live UI smoke acceptance verified:

- common application shell
- Project selection
- Technical-details toggle
- all seven workspaces reachable
- understandable empty states
- responsive navigation without loss of access

The selected smoke-test Project did not contain downstream Candidate, Final Review
or Published Output data. Therefore live interaction with Candidate decisions,
Final Release and Publication is intentionally deferred to the prepared end-to-end
demo Project in WP-12. Those write paths are covered by automated tests and this
deferral is not an open WP-09 implementation defect.

Primary application entry point:

```bash
streamlit run app/turing_generator_app.py
```

`app/ui_app.py` remains only the legacy early-MVP two-tab ingestion skeleton.

# WP-10 — Ingestion + Human Review UX Simplification

WP-10 is completed and verified.

Architecture:

`collaboration/decisions/ADR-024-guided-engineering-workflow-and-ux-projection-architecture.md`

WP-10 extends ADR-024 with UX-16 while preserving the existing Processing and
Human Review authority boundaries.

Completed work:

```text
WP-10.1  Processing + Human Review presentation foundation
WP-10.2  filename-first Processing UX and direct Human Review transition
WP-10.3  engineering-content-first Human Review with Persona comparison
WP-10.4  Review lifecycle, Finalization, Reopen and Approved Input UX
WP-10.5  visual acceptance, semantic polish and closeout verification
```

Implemented capabilities include:

- deterministic read-side Processing and Human Review presentation adapters
- Focused Processing centered on filename, Source role, status and next action
- Technical Processing retaining Source / Run / Attempt identities, hashes and
  diagnostics on demand
- optional Processing configuration through progressive disclosure
- direct `Continue to Human Review` transition after Processing
- Human Review Queue centered on Source, required decisions and lifecycle status
- engineering statement before technical metadata
- Persona proposals grouped by Persona and shown side-by-side where available
- repeated runs under one Persona do not become independent votes
- consensus / variance projected only from persisted consensus evidence
- one-Persona results explicitly reported as not sufficient to assess
  inter-Persona agreement
- exact proposal / evidence / fingerprint bindings retained underneath Focused
  presentation
- advanced scoped actions, split / merge and evidence retained through
  progressive disclosure
- clearer Finalization, Human confirmation, Approved Input Promotion and Reopen
  lifecycle presentation
- Reopen remains successor creation; finalized predecessors remain immutable
- Approved Input authority and lifecycle details remain available in Technical
  View
- top-level Streamlit navigation uses one Session State authority rather than a
  competing widget default

Verification:

```text
WP-10 final repository regression:
5563 passed, 1 skipped in 13.91s

Final shell / Human Review targeted regression:
43 passed in 0.53s

git diff --check:
PASS
```

Manual live acceptance verified:

- filename-first Processing inventory
- readable Ready-to-process and Ready-for-Human-Review states
- live LLM Processing completion with 15 published unreviewed outputs
- direct Processing → Human Review continuation
- Human Review Queue focused on engineering work
- engineering-content-first Review Items
- progressive disclosure of technical and advanced Review information
- understandable Finalization blocking / confirmation state

The available acceptance fixture contained only one Persona for the inspected
Review Items. Therefore a visual multi-Persona side-by-side acceptance case is
intentionally exercised with the prepared end-to-end demo data in WP-12.
Automated presentation tests cover Persona grouping and side-by-side behavior.

No Processing, Human Review, Approved Input or CATIA authority was moved into UI
session state during WP-10.

---

# WP-11 — Architecture / Model Proposal UX

WP-11 is completed and verified.

Architecture:

`collaboration/decisions/ADR-024-guided-engineering-workflow-and-ux-projection-architecture.md`

WP-11 extends ADR-024 with UX-17 while preserving the existing Candidate,
Approved Input and Internal Engineering Model authority boundaries.

Completed work:

```text
WP-11.1  Model Proposal presentation foundation
WP-11.2  architecture-first Model Proposal workspace
WP-11.3  decision-first Candidate Review interaction
WP-11.4  automated acceptance and closeout
```

Implemented capabilities include:

- deterministic immutable `GuidedModelProposalPresentation`
- architecture-first projection of Model Elements and Relationships
- engineer-readable grouping by model area
- Relationship Choice Groups presented as alternatives rather than votes
- persisted preferred / accepted relationship alternatives retained
- material profile / comparability deviations surfaced explicitly
- Human Candidate decisions colocated with the affected engineering content
- exact Candidate Set and Candidate identities retained for every write
- `Accept`, `Reject`, `Defer` and `Accept as exception` unchanged as normative
  Candidate Review decisions
- repeated UI presentation does not create Candidate, Review or Model authority
- Phase-I readiness projected only from the existing authoritative gate
- ready Candidate Sets show no unnecessary Candidate write controls
- Focused View prioritizes architecture, decisions, readiness and next action
- Technical View retains Candidate identities, fingerprints, Approved Input
  references, conformance, comparability and traceability

Verification:

```text
WP-11 focused regression:
40 passed in 0.52s

Complete repository regression:
5577 passed, 1 skipped in 14.19s

git diff --check:
PASS
```

A populated live Model Proposal acceptance case was not executed during WP-11
because no representative Model Candidate data exists yet in the local demo
Project. This is intentionally deferred to WP-12, where the full end-to-end demo
Project will exercise Model Proposal, Candidate Review and downstream model
generation as one connected workflow.

WP-12 will use that run as a formative task-based self-evaluation of the
demonstrator. Observations may drive bounded UX fixes, but the evaluation is
qualitative design evidence rather than an independent quantitative usability
study.

No Candidate, Approved Input, Internal Engineering Model or CATIA authority was
transferred to the UI during WP-11.

---

# Phase L — Final Model Review and Output Publication

Phase L implementation is completed and verified.

Architecture decision:

`collaboration/decisions/ADR-023-final-model-review-and-output-publication-architecture.md`

Accepted architecture checkpoint:

`72974bb63c92c37baac5eef6b740ee91bacedd01`

Completed implementation slices:

```text
L1  Final Model Review domain foundation
L2  project-local immutable Final Model Review repository
L3  Final Model Review read model and UI projection
L4  immutable Change Proposal and controlled revision / agent-reproposal loop
L5  exact Human release gate
L6  atomic idempotent Output Publication repository and OutputWriter
L7  J→K→Final Review→Human Release→OUT end-to-end integration
```

Implemented authority path:

```text
IEM
→ deterministic GeneratedSysMLArtifactSet
→ SysMLValidationResult
→ immutable Final Model Review Revision
→ Human review of model/code/validation/traceability/proposals
→ explicit fingerprint-bound Human release approval
→ immutable versioned OUT package
```

Generated but unreleased `.sysml` remains project-local review evidence. Only
the exact Human-approved `valid / passed` revision may enter:

```text
data/output/<project_id>/OUT-xxxxxx/
```

Implemented capabilities include:

- project-local `FMR`, `FRV`, `FRI`, `FRD` review identities
- immutable review revisions containing exact generated SysML and K evidence
- deterministic review read model for model structure, exact SysML code,
  validation findings, traceability and available proposal/agent evidence
- explicit code/diagram edits as immutable Change Proposals rather than direct
  mutation of generated or authoritative model state
- deterministic change routing to Phase H, J, K or L presentation ownership
- optional bounded agent/LLM re-proposal request without AI approval authority
- stale-review and successor-revision protection
- mandatory exact Human release approval
- publication re-check of the current K and Human release gates
- versioned `TURING_SYSML_V2_OUTPUT 1.0.0` Output Profile
- project-local immutable sequential `OUT-xxxxxx` identities
- exact byte preservation of Human-reviewed Phase-J SysML during publication
- deterministic generation summary, validation result/report and traceability
  package projections
- package/file fingerprints and publication-input fingerprint
- idempotent exact re-publication
- atomic fail-closed publication and recovery diagnostics
- no implicit latest-artifact/revision selection

Phase-L focused verification:

```text
147 passed, 1 skipped in 1.63s
git diff --check: PASS
```

Complete repository verification:

```text
5451 passed, 1 skipped in 26.84s
```

The single skip is the intentional live SYSIDE vertical-slice acceptance test.

Runtime probe:

```text
command -v syside
→ unavailable

syside --version
→ command not found
```

Therefore:

```text
Phase L implementation: COMPLETE
Automated J→K→Human Review→Human Release→OUT vertical slice: PASS
Live real-SYSIDE publication acceptance: BLOCKED by missing SYSIDE CLI
WP-09 Guided Workflow UI: COMPLETE
Next work package: WP-10 Ingestion + Human Review UX Simplification
```

The unavailable SYSIDE CLI does not weaken or bypass the release gate. A real
publication continues to fail closed until external validation can complete as
`valid / passed`.

---

# Verified Implementation Baseline

## Phase F — Agentic Ingestion UI

Phase F remains complete and verified at:

`adce9ec65ca3e36b89686b55d397a34dd382fdb1`

Implemented capabilities include:

- modular agent and team execution architecture
- memory-based ingestion pipeline
- consensus framework
- deterministic engineering review report
- traceable gaps, ambiguities, risks and independent review questions
- Streamlit Agentic Ingestion UI
- Dry Run and LLM execution paths
- report, run-summary, consensus, agent-output and artifact browsing

## Phase P — Project Workspace and Project-bound Ingestion

Phase P is complete.

Final implementation verification commit:

`26acace4d7ba2849b33c5e0dacedf838f83c7705`

Complete automated test baseline:

3808 passed

Manual P9 acceptance audit:

PASS

Completed steps:

| Step | Deliverable | Status |
|---|---|---|
| P1 | Framework Template Definition | Completed |
| P2 | Project Manifest and Workspace Structure | Completed |
| P3 | Source Registry and mandatory Project Assignment | Completed |
| P4 | Framework-mapped heterogeneous Information Units | Completed |
| P5 | Processing State and Artifact Organization | Completed |
| P6 | Preliminary Coverage and Potential Model Support | Completed |
| P7 | Project Dashboard | Completed |
| P8 | Tests and Integration Readiness Review | Completed |
| P9 | Project-bound Agentic Ingestion Integration | Completed |

### P1 — Framework Template Definition

Verified at:

`82b5cbbe9bedac77a4b02928a596ea8fbdacc873`

Implemented capabilities include:

- versioned `TURING_RFLP_FRAMEWORK`
- 3 framework levels and 12 mapping targets
- stable framework identifiers
- zero-to-many framework assignments
- rejection of unknown mapping targets
- exclusion of `context_only` sources from framework mapping
- deterministic framework-template validation

### P2 — Project Manifest and Workspace Structure

Architecture decision:

`collaboration/decisions/ADR-005-project-workspace-architecture.md`

Verified through:

`36184a2d90db349555ac3bd64ccd5c27ecb68cec`

Implemented capabilities include:

- six-digit project identities
- separation of project identity and display name
- project display-name uniqueness
- strict Project Manifest validation
- project creation, loading, scanning and isolation
- safe project paths and symlink rejection
- deterministic project reopening

### P3 — Project Source Registry

Architecture decisions:

- `collaboration/decisions/ADR-009-textual-source-processing-boundary.md`
- `collaboration/decisions/ADR-010-project-source-registry-architecture.md`

Verified through:

`55cc4f104082ecfef70b3dcdeb8f28406ed95105`

Implemented capabilities include:

- mandatory project assignment for every persisted Source
- project-local Source identifiers
- immutable Source Manifests
- source content hashes and metadata
- `engineering_source` and `context_only` roles
- duplicate-content rejection within a project
- safe project-local source persistence
- strict separation of project and Source identity

### P4 — Framework-mapped Heterogeneous Information Units

Architecture decision:

`collaboration/decisions/ADR-011-semantic-information-unit-and-ontology-boundary.md`

Verified at:

`0c8ba428e7e6469e410b541c114d7a5a9474321c`

Implemented capabilities include:

- deterministic projections for text, Markdown, JSON, CSV, TSV and PDF text layers
- projection manifests and source locators
- pinned BFO 2020 and IOF Core 202602 reference snapshots
- ontology registry and deterministic reference-concept index
- Turing Core Vocabulary
- project glossary candidates and terminology decisions
- immutable source-traceable Information Units
- semantic extraction candidate contracts
- multi-agent semantic consensus, disagreement and variance
- terminology-mapping candidates
- framework-assignment candidates
- immutable Human Review Decisions
- exact target-content and validation-fingerprint binding
- deterministic token budgeting
- fail-closed required-context handling

### P5 — Processing State and Artifact Organization

Architecture decision:

`collaboration/decisions/ADR-012-processing-state-and-artifact-organization.md`

Verified through:

`9a9ef8bd7c08c354c638d4b0e072e308e7c02516`

Implemented capabilities include:

- immutable Processing Run Manifests
- immutable Processing Event Manifests
- immutable Processing Decision Manifests
- event-chain validation
- current-state reconstruction
- source-bound Processing Runs
- attempt identifiers
- run work and artifact directories
- retry, supersession, invalidation and recovery diagnostics
- Source-level and Project-level aggregation
- fail-closed state reporting

### P6 — Preliminary Coverage and Potential Model Support

Architecture decision:

`collaboration/decisions/ADR-013-preliminary-coverage-and-potential-model-support.md`

Verified through:

`f921b216d66ee359dea7cf116cfea03acb1e3510`

Implemented capabilities include:

- deterministic Preliminary Coverage assessment
- explicit support profile
- project-local coverage evidence
- covered, uncovered and attention-required states
- potential support assessment for future model scopes
- strict separation of Preliminary Coverage and Approved Generation Readiness

### P7 — Project Dashboard

Architecture decision:

`collaboration/decisions/ADR-014-project-dashboard-architecture.md`

Verified through:

`d8a3bc9bb55a4b7ab0fa6e999b74b8541bf224b6`

Project-creation fixes:

`fe0fd24`

Implemented capabilities include:

- common Project Dashboard
- Overview view
- Sources & Processing view
- Coverage & Support view
- Attention & Review view
- Traceability view
- project selection and constrained project creation
- evidence navigation
- safe document preview
- read-only dashboard boundary except for constrained project creation

### P8 — Tests and Integration Readiness Review

P8 confirmed:

- P1–P7 integration readiness
- no need for a parallel project or processing architecture
- need for a separate P9 project-bound ingestion integration boundary
- preservation of dashboard execution boundaries

### P9 — Project-bound Agentic Ingestion Integration

Architecture decision:

`collaboration/decisions/ADR-015-project-bound-agentic-ingestion-integration.md`

Verified through:

`26acace4d7ba2849b33c5e0dacedf838f83c7705`

Implemented capabilities include:

- common Turing Generator application shell
- project-bound Source upload and registration
- Source Projection before Phase F execution
- P5 Processing Run creation
- `agentic_ingestion` Processing Stage
- execution inside a run-owned work directory
- validation before publication
- immutable publication of run-owned artifacts
- `ProcessingArtifactReference` generation
- `artifact_published` and `review_requested` events
- successful final state `awaiting_review`
- Execution UI
- Dashboard return and review-report navigation

Manual acceptance evidence includes:

- negative processing case ending in `failed`
- successful dry-run case ending in `awaiting_review`
- 15 published artifact references
- all published artifact fingerprints verified
- no API-key fields persisted

Local demo data under `data/projects/` remains non-authoritative test evidence.

---

# Post-Phase-P Reconciliation Gate

## Status

Completed on 2026-07-31.

## Completed Deliverables

The completed gate includes:

- presentation of the Phase F/P prototype
- preservation of the verified implementation baseline
- inventory of implemented Phase F/P capabilities
- review of accepted architecture decisions
- first Architecture-to-Requirements Reconciliation against CATIA
- accepted CATIA System Requirements baseline
- accepted CATIA System Design Constraint baseline
- accepted System Function baseline
- accepted System Logical Architecture baseline
- feature and requirement coverage analysis
- explicit selection of Phase G as the next implementation phase

## Accepted CATIA System Baseline

The authoritative CATIA model now contains the accepted System-level baseline:

- 39 Stakeholder Requirements
- 102 System Requirements
- 30 active System Design Constraints
- 12 System Functions
- 8 Logical Components
- System Function interaction network
- Logical interconnection view
- complete Stakeholder Requirement coverage through System Functions

The 102 System Requirements are grouped into topical packages for navigation
and documentation only.

The grouping shall not be interpreted as:

- pre-allocation to Logical Components
- subsystem boundaries
- proof of implementation
- a replacement for the accepted derivation chain

The accepted derivation chain remains:

```text
Stakeholder Requirements
→ System Requirements
→ System Functions
→ Logical Components
→ implementation evidence
```

System Physical Architecture and Subsystem R/F/L/P remain deferred.

## Feature and Requirement Coverage

The completed reconciliation confirms:

- all 39 Stakeholder Requirements are covered by at least one System Function
- every System Requirement has one primary System Function allocation
- implementation status remains distinct from requirement coverage
- current runtime implementation is strongest in ingestion, processing,
  evidence, traceability and status presentation
- architecture derivation, model validation and SysML v2 generation remain the
  primary open prototype capabilities

## Phase N Scope Brought Forward

The Post-Phase-P Reconciliation Gate performed part of the originally planned
Phase N scope early.

Completed early:

- first Architecture-to-Requirements Reconciliation
- accepted System Requirement update
- accepted System Function modeling
- accepted System Logical Architecture modeling
- initial feature and requirement coverage baseline

Still retained in Phase N:

- migration of the temporary SYSIDE shadow model
- removal of duplicated maintained model authority
- final reconciliation after Phases G–L
- final synchronization with CATIA
- confirmation that CATIA is the only maintained engineering model

Phase N is therefore not complete.

---

# Phase G — Current Implementation Status

Phase G is completed.

The implemented authority path is:

```text
Original Source
→ Processing Evidence
→ Human Review Workspace
→ Finalized Reviewed Document
→ Approved Input
```

Completed work packages:

```text
G1  Architecture
G2  Review Workspace foundations
G3  P4/P9 evidence adapters and Review Item construction
G4  Review editing, finalization and reopening
G5  Approved Input promotion and lifecycle
G6  Human Review and promotion UI
G7  Integration, audit, manual acceptance and final regression
```

Verified checkpoints:

```text
G5 completion commit:
865cbab24dfb5bb1f5150ff9336a55d00299a035

G6 completion commit:
7209f17a610d3adb359e8b672a28020b71c03333

G6 focused regression:
145 passed

G7.3 manual acceptance:
PASS

G7.4 focused completion regression:
65 passed in 8.95s

G7.4 complete repository regression:
4818 passed in 24.50s

git diff --check:
PASS
```

Primary G7.3 evidence is recorded in:

- `collaboration/audits/phase_g_manual_acceptance_test_report.md`
- `collaboration/audits/phase_g_manual_acceptance_findings.md`

The manual acceptance verified:

- immutable Review Revisions
- exact Human Review Decision binding
- exact three-artifact finalization
- Approved Input promotion
- exact AIN authority and traceability
- reopen successor lineage
- byte-identical finalized predecessor preservation
- Scoped Action impact preview and exact materialization
- fail-closed unresolved relationship behavior
- no second Agentic Ingestion write action while a Run is `running`

Phase G does not generate Model Candidates or SysML v2.

---

# Phase H — Model Candidate Layer

Phase H is completed and verified.

Architecture decision:

`collaboration/decisions/ADR-018-model-candidate-layer-and-structural-comparability.md`

Accepted and committed architecture checkpoint:

`884d658726d9a5a2ac9f86786ded30db7fe38c68`

Implemented work packages:

```text
H1  Identifiers and error foundation
H2  Immutable domain types
H3  Manifests, validation and fingerprints
H4  Repository, paths and immutable persistence
H5  Approved Input → Candidate generation pipeline
H6  Model Structure / Comparability Profile and relationship logic
H7  Candidate Human Review and Phase-I gate
H8  deterministic ModelProposalView and presentation projection
```

Implemented authority path:

```text
ApprovedInputRepository.list_active_approved_inputs(project_id)
→ immutable Model Candidate Set
→ Model Element Candidates / Model Relationship Candidates
→ exact Candidate Human Review Decisions
→ ModelCandidateReadService.load_phase_i_input(...)
→ ModelCandidateAssemblyInput
```

Implemented capabilities include:

- immutable project-local `MCS`, `MCE`, `MCR` identities
- exact Approved Input snapshot and fingerprint binding
- separate Element and Relationship Candidate manifests
- same-set exact Relationship endpoint resolution
- explicit relationship family, semantic intent and later-serialization separation
- versioned Model Structure and Comparability Profile
- profile-driven conservative candidate derivation
- advisory relationship priority using ADR-018 P1–P7 criteria
- structural-comparability impact and explicit deviations
- immutable Candidate Review Decisions (`MCD`)
- `accepted`, `rejected`, `deferred` and `accepted_exception` decisions
- exact Candidate / Candidate Set / profile / Approved Input fingerprint binding
- stale-decision detection
- active-Approved-Input revalidation before Phase-I handoff
- fail-closed unresolved or ambiguous accepted relationships
- accepted-relationship endpoint authorization checks
- explicit relationship-choice conflict checks
- sole validated H→I read contract through `ModelCandidateReadService`
- deterministic, non-authoritative `ModelProposalView`
- lightweight structural overview suitable for later UML-/SysML-like UI projection
- relationship choice groups, comparability summary and profile deviations
- concise required-human-decision and next-action projection
- deterministic JSON and Markdown proposal projections
- no SysML v2 textual generation in Phase H

Phase-H verification:

```text
Focused H1–H8 regression:
168 passed in 1.63s

Complete repository regression:
4986 passed in 25.80s

git diff --check:
PASS
```

The technical Model Proposal read model is implemented, but the polished
Architecture / Model Proposal UX remains WP-11.

Phase H does not assemble the Internal Engineering Model and does not generate
SysML v2 text.

# Phase H9 — Hybrid Target Projection Extension

H9 is completed and verified as a controlled extension of the completed
Phase-H Model Candidate Layer.

Architecture decision:

`collaboration/decisions/ADR-020-hybrid-target-projection-and-coverage-architecture.md`

The H9 projection architecture is:

```text
Approved Input snapshot
→ deterministic profile-resolution coverage
→ mapped / ambiguous / unmapped / intentionally_not_projected
→ strict deterministic path OR unresolved-only LLM assistance
→ profile-controlled structured proposal validation
→ merged Model Candidate drafts
→ existing Candidate Human Review
→ unchanged Phase-I gate
```

Implemented capabilities include:

- complete explicit projection coverage for every active Approved Input
- strict deterministic quick/dry-run projection retained
- shared deterministic profile resolver
- deterministic-first hybrid routing
- LLM execution only for `ambiguous` / `unmapped` inputs
- compact profile-controlled request context
- bounded serial batching with a configured call ceiling
- no automatic LLM retry loop
- structured `proposed_mapping` / `ambiguous` / `unmapped` response contract
- fail-closed rejection of hallucinated or non-offered target rules
- no forced framework mapping
- no SysML v2 generation by the H9 LLM
- preserved original Approved-Input evidence
- LLM-assisted Candidates remain subject to the existing Human Review boundary
- hybrid generation provenance with provider/model and semantic
  request/response fingerprints
- unchanged sole H→I production boundary
- Phase J remains deterministic serialization of accepted Internal Model
  semantics

Verification:

```text
Focused H9 regression:
61 passed in 0.69s

Complete repository regression:
5120 passed in 13.12s

git diff --check:
PASS

Live bounded LLM smoke:
PASS
provider: openai
model: gpt-5-mini
calls: 1
retries: 0
total_tokens: 1345
selected_rule_id: ELEMENT_SYSTEM_FUNCTION
candidate_model_area: system.functional
candidate_element_type: function
support_level: partially_supported
```

The live smoke was intentionally non-persistent and used one unresolved input,
`batch_size=1` and `max_calls_per_run=1`.

## Phase-N2 Reconciliation Candidates from H9

H9 records capability/change evidence only. It does not create or modify CATIA
Requirements or Functions.

The following capabilities shall be reconciled during Phase N2:

- selectable strict deterministic and LLM-assisted target projection
- complete target-projection coverage with explicit unresolved states
- deterministic-first routing that limits AI execution to unresolved cases
- profile-controlled LLM proposals with explicit no-forced-fit behavior
- traceable LLM target-projection provenance while preserving Human Review
  authority

Exact CATIA element types, Requirement wording, Function wording and allocation
remain explicitly deferred to Phase N2.

---

# Phase I — Internal Engineering Model

Phase I is completed and verified.

Architecture decision:

`collaboration/decisions/ADR-019-internal-engineering-model-assembly-architecture.md`

Accepted and committed architecture checkpoint:

`ff4ee4e038942f9ee267eb2ad6a6daa600b09e6d`

Implemented work packages:

```text
I1  IDs + immutable Internal Model domain types
I2  manifests + fingerprints + H→I contract enrichment
I3  Framework/Profile resolution + structure materialization
I4  deterministic MCE/MCR → IME/IMR assembly
I5  repository + immutable persistence + bundle integrity
I6  explicit Phase-J read contract + regression
```

Implemented authority path:

```text
ModelCandidateReadService.load_phase_i_input(...)
→ validated ModelCandidateAssemblyInput
→ deterministic InternalModelAssemblyService
→ immutable InternalEngineeringModelSnapshot
→ atomic InternalModelRepository persistence
→ InternalModelReadService.load_phase_j_input(...)
```

Implemented identities:

```text
IEM-000001  Internal Engineering Model
IME-000001  Internal Model Element
IMR-000001  Internal Model Relationship
```

IDs are project-local, sequential, immutable and never gap-reused.

Persistence:

```text
data/projects/<project_id>/internal_models/
└── IEM-000001/
    ├── manifest.json
    ├── structure.json
    ├── elements/
    │   └── IME-000001.json
    └── relationships/
        └── IMR-000001.json
```

Implemented capabilities include:

- enriched sole H→I transfer with exact Framework Template and derivation-rules references
- deterministic `assembly_input_fingerprint` over the authorized H→I state
- immutable IEM, IME and IMR contracts with deterministic fingerprints
- explicit assembly-rules artifact `TURING_INTERNAL_MODEL_ASSEMBLY 1.0.0`
- exact Framework Template and Model Structure Profile resolution
- materialization of the complete configured framework hierarchy
- exact IME placement from reviewed Phase-H `model_area`, `element_type` and
  `framework_assignment`
- no inferred engineering containment beyond explicit reviewed semantics
- deterministic accepted MCE → IME assembly
- deterministic accepted MCR → IMR assembly
- exact relationship endpoint rebinding to same-snapshot IMEs
- preservation of relationship family, semantic intent and directionality
- exact Approved Input, Candidate and Human Review traceability
- explicit preservation of `accepted_exception`
- fail-closed behavior where deterministic assembly would require new semantics
- immutable project-local persistence with safe-path and symlink rejection
- complete bundle-integrity validation across manifest, structure, IMEs and IMRs
- project-wide no-reuse checks for IEM/IME/IMR identities
- interrupted-publication diagnostics and atomic temporary publication
- idempotent exact reassembly for identical assembly input plus assembly rules
- explicit Phase-I → Phase-J read contract through `InternalModelReadService`
- no implicit latest-IEM selection
- no SysML v2 textual serialization in Phase I

Phase-I verification:

```text
Focused I1–I6 regression:
110 passed in 1.07s

Complete repository regression:
5087 passed in 26.00s

git diff --check:
PASS
```

Phase I corresponds to the deterministic synthesis / assembly portion of the
CATIA architecture-derivation responsibility. It does not replace broader Phase-K
validation and does not generate SysML v2 textual notation.

Immediate next phase:

```text
Phase J — SysML v2 Code Generator
```

---

# Phase J — SysML v2 Code Generator

Phase J is completed and verified.

Architecture decision:

`collaboration/decisions/ADR-021-syside-compatible-sysml-v2-generation-architecture.md`

Accepted architecture checkpoint:

`af6953486a71c3073c0169ef5052dbcabb49c4fc`

Completed implementation slices:

```text
J1  generation foundation + Target Notation 0.2.0 + controlled SYSIDE syntax evidence
J2  Generation Profile + Artifact Structure Profile + deterministic preflight
J3  package/symbol/safe-text/canonical-order projection
J4  deterministic element rendering
J5  deterministic relationship rendering + endpoint-role integration
J6  GeneratedSysMLArtifactSet + traceability + fingerprints/idempotence
J7  explicit generation service boundary + regression + SSOT closeout
```

Pinned generation policy:

```text
CTX_SYSML_V2_TARGET_NOTATION 0.2.0
TURING_SYSML_V2_GENERATION 1.0.0
TURING_SYSML_V2_ARTIFACT_STRUCTURE 1.0.0
TURING_SYSML_V2_GENERATOR_RULES 1.0.0
```

Implemented capabilities include:

- sole I→J authority loading through `InternalModelReadService.load_phase_j_input(...)`
- explicit `SysMLGenerationService.generate(project_id, internal_engineering_model_id)`
- no implicit latest-IEM selection
- deterministic preflight before any rendering
- exact model-area / element-type → SysML construct mapping
- requirement usages for reviewed requirements
- use-case definitions for reviewed use cases
- action usages / Features for reviewed functions
- part usages / Features for reviewed logical and physical components
- explicit fail-closed `stakeholder` and `user_need` handling
- explicit dependency, allocation and satisfaction relationship generation
- deterministic `source satisfies target` → `satisfy TARGET by SOURCE` textual projection
- endpoint kind and target-construct compatibility checks
- no generic relationship fallback
- deterministic Framework hierarchy → package projection
- stable generated IME/IMR technical symbols separate from engineering names
- safe documentation text handling without raw semantic injection
- canonical ordering and formatting
- one validation-ready `generated_model.sysml` unit under root package `GeneratedModel`
- qualified relationship references without invented engineering containment
- immutable `GeneratedSysMLArtifactSet`
- exact generated-unit/location → IEM → IME/IMR → Candidate → Approved Input → Review traceability
- accepted-exception traceability preservation
- generation-input, unit-content and artifact-set SHA-256 fingerprints
- byte-identical deterministic idempotence
- strict separation from Phase-K validation and Phase-L publication
- no direct publication to `data/output/`

Controlled SYSIDE integration checks verified the production-relevant element and
relationship forms. An early allocation experiment exposed invalid Definition
endpoints; the final mapping correctly uses ActionUsage / PartUsage Features and
preflight now blocks incompatible endpoint forms before rendering.

Final verification:

```text
Targeted Turing Core synchronization regression:
191 passed in 0.19s

Complete repository regression:
5239 passed in 13.77s

git diff --check:
PASS
```

The final regression also detected a stale Turing Core reference to Target
Notation `0.1.0`. The source reference and SysML mapping-policy pin were
synchronized to `0.2.0`; strict reference validation was preserved.

## Phase-N2 Reconciliation Candidates from J

Phase J records capability/change evidence only. It does not create or modify
CATIA Requirements, Functions or Logical Components.

Reconcile during Phase N2:

- deterministic SysML v2 generation from an explicitly selected validated IEM
- versioned SYSIDE-compatible Target Notation
- separate versioned semantic mapping, artifact structure and generator rules
- fail-closed unsupported semantics and relationship endpoint compatibility
- deterministic generated identity, fingerprints and idempotence
- machine-readable generated-output traceability to approved engineering evidence
- explicit J/K/L separation of generation, validation and publication

Exact CATIA element types, wording and allocations remain deferred to Phase N2.

# Phase K — Validation Layer

Phase K implementation is completed and verified.

Architecture decision:

`collaboration/decisions/ADR-022-sysml-v2-validation-layer-architecture.md`

Accepted architecture checkpoint:

`601b2134fcb227b114b4c50ad14d09ca920c81c5`

Completed implementation slices:

```text
K1  Validation domain foundation + Validation Profile
K2  Artifact/context/Target-Notation/Structure/Traceability validators
K3  Relationship + endpoint consistency validator
K4  SYSIDE CLI adapter + deterministic diagnostic normalization
K5  SysMLValidationService + status/gate/fingerprint assembly
K6  J→K→L boundary regression + status hardening + closeout
```

Implemented capabilities include:

- immutable `SysMLValidationResult`
- versioned `TURING_SYSML_V2_VALIDATION 1.0.0` Validation Profile
- exact Phase-J generation-policy reference and fingerprint resolution
- standalone GeneratedSysMLArtifactSet integrity validation
- deterministic Target Notation subset validation
- deterministic Artifact Structure validation
- generated relationship and endpoint consistency validation
- exact generated traceability validation
- Model Structure / Comparability policy-chain consistency validation
- isolated non-mutating SYSIDE CLI adapter
- runtime SYSIDE version/identity discovery
- deterministic external diagnostic normalization
- explicit `valid` / `invalid` / `incomplete` status model
- fail-closed `passed` / `blocked` publication gate
- unavailable external validator represented as `incomplete / blocked`
- infrastructure findings remain publication-blocking without being
  misclassified as model invalidity
- deterministic validation-input and result fingerprints
- exact artifact-fingerprint-bound K→L handoff validation
- no IEM/Candidate semantic reinterpretation in Phase K
- no generated-text repair, mutation, regeneration or publication in Phase K

Verification:

```text
Focused K1–K6 regression:
65 passed in 1.41s

Complete repository regression:
5304 passed in 25.97s

git diff --check:
PASS
```

Runtime external-validator readiness on the verification workstation:

```text
SYSIDE CLI: unavailable
```

This is not a Phase-K unit/regression failure. The implemented fail-closed
runtime behavior therefore produces `incomplete / blocked` until the required
SYSIDE Modeler CLI is installed and executable. A live `valid / passed`
publication-ready run remains a prerequisite for Phase-L operational
acceptance.

Immediate next phase:

```text
Phase L — Output Writer
```

---

# Current Architecture Baseline

## Engineering Authority

The authority hierarchy is:

1. CATIA SysML v2 model for engineering knowledge
2. committed repository for implementation reality
3. Collaboration Knowledge Base for roadmap, coordination and accepted decisions
4. chat history and temporary generated artifacts

The temporary SYSIDE shadow model may supplement missing CATIA information
until Phase N.

It shall never override or contradict CATIA.

Implementation evidence shall not silently create normative requirements.

## Accepted Framework

The implemented framework contains:

- Stakeholder Level
  - Stakeholders
  - User Needs
  - Stakeholder Requirements
  - Use Cases
- System Level
  - Requirements
  - Functional
  - Logical
  - Physical
- Subsystem Level
  - Requirements
  - Functional
  - Logical
  - Physical

Apollo 11 remains a non-normative structuring reference.

Its engineering content, CoSMA framework and package layout were not
transferred.

## Modular Artifact-oriented Architecture

The Turing Generator uses a modular, recipe-driven and artifact-oriented
architecture.

Important explicit artifacts include:

- project principles
- project scope context
- framework templates
- support profiles
- ontology registries
- vocabularies
- recipes
- agent profiles
- task definitions
- source manifests
- processing manifests
- events and decisions
- review reports
- run summaries
- generated output artifacts

The core infrastructure is intended to remain reusable while task-specific
profiles and artifacts are exchanged.

## Source-processing Boundary

The MVP processing boundary remains textual information.

Supported:

- text
- Markdown
- JSON
- CSV
- TSV
- deterministic textual projections
- PDF text layers

Outside the MVP:

- OCR
- image-only document interpretation
- technical-drawing interpretation
- unrestricted multimodal engineering extraction

## Processing and Publication Boundary

A successful P9 execution:

- validates Source Projection
- executes Phase F
- publishes immutable run-owned artifacts
- requests Human Review
- reaches `awaiting_review`

It does not:

- create Approved Input
- create approved engineering knowledge
- satisfy Approved Generation Readiness
- generate model candidates
- generate SysML v2

Published run-owned artifacts are authoritative evidence for what the run
produced.

They are not authoritative engineering knowledge until an accepted promotion
workflow approves them.

## Human Review Boundary

Consensus, confidence and variance are review evidence.

They are not approval or publication authority.

Every promotion or engineering-publication target requires an explicit
persisted Human Review Decision bound to the current target content and
applicable validation fingerprints.

## Model Comparability Boundary

Model comparability is an explicit target for Phase H and Phase K.

Related models, including product variants, shall be generated using a
consistent structural profile so that meaningful comparison remains possible.

The profile shall address:

- preferred model-element structure
- preferred relationship semantics
- canonical relationship choices
- required comparison anchors
- allowed structural variation
- relationship prioritization criteria
- reviewable exceptions

Automated prioritization remains advisory.

Human Review shall authorize accepted relationship candidates and exceptions.

---

# Phase G — Completed Implementation Baseline

## Status

Completed and verified on 2026-08-12.

## Accepted Architecture

Primary authority architecture:

`collaboration/decisions/ADR-016-human-review-workspace-and-approved-input-promotion-architecture.md`

Accepted interaction architecture:

`collaboration/decisions/ADR-017-simple-by-default-interaction-and-progressive-disclosure.md`

ADR-016 defines the engineering authority chain:

```text
Processing Evidence
→ Human Review Workspace
→ Finalized Reviewed Document
→ Approved Input
```

ADR-017 defines how this complexity is presented to a user without weakening
the underlying authority, evidence or traceability contracts.

## Work Breakdown

| Step | Deliverable | Status |
|---|---|---|
| G1 | Human Review Workspace and Approved Input architecture | Completed |
| G2 | Review Workspace foundations | Completed |
| G3 | P4/P9 evidence adapters and Review Item construction | Completed |
| G4 | Review editing, finalization and reopening | Completed |
| G5 | Approved Input promotion and lifecycle | Completed |
| G6 | Human Review and promotion UI | Completed |
| G7 | Integration, audit, manual acceptance and regression | Completed |

## G5 — Approved Input Promotion and Lifecycle

Implemented:

- project-local immutable `AIN` and `AIE` identities
- immutable Approved Input Manifest
- project-local Approved Input repository
- deterministic Promotion Eligibility
- idempotent Promotion Service
- invalidation, revocation and supersession
- successor reconciliation using stable subject and Promotion Equivalence
- stable active-only Phase H read contract
- exact Project, Source, Run, Artifact, Review and Human Decision traceability

Verified G5 checkpoint:

`865cbab24dfb5bb1f5150ff9336a55d00299a035`

## G6 — Human Review and Promotion UI

Implemented:

- project-bound Human Review queue and workspace
- clear proposal and evidence presentation
- immutable item-level review operations
- Scoped Review Action preview and write path
- exact Human Review Decision confirmation
- finalization as a distinct action
- exact promotion from finalized authority
- active Approved Input visibility
- reopen workflow
- safe project-bound Agentic Ingestion retry/recovery interaction
- safe provider-neutral failure feedback

Verified G6 checkpoint:

`7209f17a610d3adb359e8b672a28020b71c03333`

Focused G6 regression:

```text
145 passed
git diff --check: PASS
```

## G7 — Integration, Audit and Acceptance

G7 intentionally introduced no parallel authority model. Defects found during
manual acceptance were corrected at their owning G2–G6 abstractions.

Recorded implementation findings:

```text
F01 Streamlit widget-owned Session State
F02 project-bound failed-Run retry integration
F03 running-state feedback / duplicate write affordance
F04 safe provider-neutral failure diagnosis
F05 pre-publication Attempt identity reuse
F06 cross-layer semantic-reference validation mismatch
```

All six findings are closed and documented.

Manual acceptance evidence includes:

```text
RVD-000001
RVV-000001 finalized on RVR-000008
HRD-000001
AIN-000001
AIN-000002
RVV-000002 successor draft
RVR-000009 initial successor revision
RIT-000006 … RIT-000010 carried-forward lineage
RVR-000010 after explicit Scoped Action
RUN-000004 / ATT-000001 running-state UI verification
```

Final verification:

```text
G7.4 focused Phase-G completion regression:
65 passed in 8.95s

Complete repository regression:
4818 passed in 24.50s

git diff --check:
PASS
```

## Phase-H Boundary

The stable authority read contract remains:

```python
ApprovedInputRepository.list_active_approved_inputs(
    project_id,
) -> tuple[ApprovedInputManifest, ...]
```

Phase H shall consume only active Approved Inputs. It shall not infer authority
from Draft Review state, Agent confidence, Consensus, UI state, inactive AINs
or original Review Reports.

## Phase-G Exit Decision

Phase G exit criteria are satisfied.

Next:

```text
Phase H — Model Candidate Layer
→ architecture contract
→ explicit acceptance
→ implementation
```

No Phase-H production implementation shall begin before that contract is
explicitly accepted.

---

# Cross-phase Model Element Change Candidates

## Purpose

Implementation shall not create a second hidden engineering architecture that
must be reverse-engineered during Phase N.

New or materially refined engineering and architecture concepts arising during
implementation shall therefore be recorded as Model Element Change Candidates
for later reconciliation with the authoritative CATIA SysML v2 model.

A Model Element Change Candidate is not an accepted CATIA model change.

CATIA remains the authoritative engineering model.

The accepted sequence is:

```text
Implementation observation
→ Model Element Change Candidate
→ engineering review
→ explicit acceptance
→ CATIA model update
```

## Candidate Scope

Candidates may concern:

- Stakeholder Requirements
- System Requirements
- System Design Constraints
- System Functions
- Logical Components
- logical relationships and allocations
- Physical Architecture decisions
- Subsystem Requirements
- Subsystem Functions
- Subsystem Logical Architecture
- Subsystem Physical Architecture
- relevant cross-level dependencies and allocations

Each candidate shall preserve at least:

- originating implementation phase
- affected model area
- proposed element type
- reason and engineering rationale
- implementation evidence
- known relationships
- review status
- CATIA transfer status

## G4 Candidate Inventory

### MEC-G4-001 — Exact Finalized Artifact Set

Originating implementation phase:

`G4.2d`

Affected model area:

Human Review Workspace and finalized Review artifacts.

Proposed element type:

System Design Constraint.

Engineering rationale:

A finalized Review result is valid only as the exact immutable set of
`reviewed_document.json`, `effective_decisions.json` and `reviewed_report.md`.
Mixed, incomplete, additional or fingerprint-inconsistent artifacts shall not
form a valid finalized Review result.

Implementation evidence:

- `modules/review_workspace/finalized_artifact_set.py`
- finalized artifact-set manifest and binding tests

Known relationships:

- constrains Review finalization output
- provides the integrity boundary consumed by G5 promotion
- binds one finalized Review Version and one exact Review Revision

Review status:

Recorded; engineering review pending.

CATIA transfer status:

Not started.

### MEC-G4-002 — Atomic Publication and Recovery Boundary

Originating implementation phase:

`G4.2e–G4.2f`

Affected model area:

Finalized Review persistence, loading, scanning and recovery.

Proposed element type:

System Design Constraint.

Engineering rationale:

A finalized artifact set shall become visible only through a validated atomic
publication. Interrupted, unsafe, incomplete or altered states shall fail
closed and shall be reported as requiring recovery rather than being treated as
valid finalized evidence.

Implementation evidence:

- `modules/review_workspace/repository.py`
- finalized artifact persistence, loading and scan tests

Known relationships:

- constrains finalized artifact persistence
- constrains repository recovery behavior
- protects the G5 promotion eligibility boundary

Review status:

Recorded; engineering review pending.

CATIA transfer status:

Not started.

### MEC-G4-003 — Carried-forward Review Item Lineage

Originating implementation phase:

`G4.3`

Affected model area:

Review Item lineage across Review Document Versions.

Proposed element type:

Logical Relationship.

Engineering rationale:

A Review Item copied into a reopened successor version requires explicit
one-to-one lineage to exactly one predecessor Review Item while preserving its
stable subject key. The relation is distinct from split, merge and original
creation.

Implementation evidence:

- `modules/review_workspace/types.py`
- `modules/review_workspace/item_manifest.py`
- `modules/review_workspace/reopening.py`
- Review reopening tests

Known relationships:

- `lineage_operation = carried_forward`
- exactly one `derived_from_review_item_ids` entry
- stable subject key remains unchanged
- materialized review state is preserved

Review status:

Recorded; engineering review pending.

CATIA transfer status:

Not started.

### MEC-G4-004 — Linear Review Version Succession

Originating implementation phase:

`G4.3`

Affected model area:

Review Document Version lifecycle.

Proposed element type:

System Design Constraint.

Engineering rationale:

Only the latest finalized Review Version may be reopened. Reopening creates one
new successor Draft, preserves the finalized predecessor and prohibits parallel
successor branches or reopening when a later Draft or finalized version exists.

Implementation evidence:

- `modules/review_workspace/reopening.py`
- `modules/review_workspace/repository.py`
- Review reopening and lifecycle integration tests

Known relationships:

- constrains the Review reopening function
- defines predecessor and successor version lineage
- preserves immutable historical review evidence
- prevents ambiguous promotion ancestry

Review status:

Recorded; engineering review pending.

CATIA transfer status:

Not started.

## G5 Candidate Inventory

### MEC-G5-001 — Event-sourced Approved Input Authority

Originating implementation phase:

`G5.6`

Implementation observation:

Approved Input manifests remain immutable at their initial authority state.
Current authority is derived from the immutable manifest plus an append-only
Approved Input Event history.

Proposed model element type:

System Design Constraint.

Review status:

Engineering review pending.

CATIA transfer status:

Not started.

### MEC-G5-002 — Promotion Equivalence Across Review Versions

Originating implementation phase:

`G5.6`

Implementation observation:

An accepted successor Review Item with the same stable subject and materially
equivalent authority-relevant engineering content and evidence retains the
existing active Approved Input. Review Version, Review Revision and Review Item
identity changes alone do not require a new Approved Input.

Proposed model element type:

System Design Constraint.

Review status:

Engineering review pending.

CATIA transfer status:

Not started.

### MEC-G5-003 — Active-only Phase H Consumption Boundary

Originating implementation phase:

`G5.7`

Implementation observation:

Subsequent engineering processing consumes Approved Inputs only through the
stable active-only repository read contract. Invalidated, revoked and superseded
Approved Inputs remain traceable but are excluded from active engineering use.

Proposed model element type:

System Design Constraint.

Review status:

Engineering review pending.

CATIA transfer status:

Not started.

## G6 Candidate Inventory

### MEC-G6-001 — Task-oriented Interaction with Progressive Disclosure

Originating implementation phase:

`G6 / Phase-G UX reconciliation`

Implementation observation:

The internal authority and traceability architecture is intentionally richer
than the primary user workflow. Presenting all audit evidence, identifiers and
technical detail simultaneously increases interaction cost without improving
engineering authority.

Proposed model element type:

System Design Constraint.

Engineering rationale:

The primary workflow should expose the engineering result, material uncertainty,
required human decision and next action. Explanation evidence shall be
available on demand, while complete traceability and audit detail remain
persisted and inspectable underneath.

Architecture evidence:

- `collaboration/decisions/ADR-017-simple-by-default-interaction-and-progressive-disclosure.md`
- Phase-G manual acceptance UX findings

Review status:

Engineering review pending.

CATIA transfer status:

Not started.

## Retrospective Requirement

G1 through G4.2c still require retrospective examination during the later
Zwischenstandspräsentation / CATIA reconciliation activity.

The G4.2d through G6 candidates above satisfy the continuous tracking rule
for the implementation-derived concepts explicitly identified during Phase G.

## Ongoing Rule

Candidate identification remains mandatory during every subsequent
implementation phase.

Phase completion review shall include an explicit check for newly created or
materially refined Model Element Change Candidates.

Phase N shall use the accumulated and reviewed candidate inventory as an input
to final Architecture-to-Requirements Reconciliation.

Phase N shall not rely on complete retrospective reverse engineering of Phases
G through L.

---

# Zwischenstandspräsentation

## Position

The Zwischenstandspräsentation is no longer a blocking gate between Phase G and
Phase H.

It is prepared after the implementation work so that the supervising professor
can review the complete implemented vertical slice rather than a partial
mid-build state.

## Purpose

Present the implemented architecture from Source ingestion through validated
SysML v2 output, explain the literature-derived architecture framing and
capture professor feedback for the final CATIA and thesis reconciliation.

## Required Content

- completed development phases
- accepted architecture decisions
- executable end-to-end workflow
- automated test and manual acceptance evidence
- current CATIA architecture coverage
- Phase-G and later Model Element Change Candidates
- open risks, limitations and technical debt
- literature-derived Data / Process / Knowledge architecture
- mapping from those layers to the eight Logical Components
- one high-level activity view with approximately 7±2 primary activities
- artifact-driven architectural adaptability as an outlook

Presentation architecture framing:

```text
Data Layer
Process Layer
Knowledge Layer
```

The Knowledge Layer is cross-cutting governance. It shall not be forced into one
artificial deployment component merely for presentation convenience.

## Exit Criteria

- presentation prepared after implementation
- professor feedback documented
- architecture and roadmap effects evaluated
- required decisions recorded
- Model Element Change Candidate inventory reviewed
- CATIA / SSOT effects reconciled as appropriate

The presentation does not itself change CATIA authority.

---

# Planned Prototype Phases and Demo Work Packages

The remaining implementation sequence is:

| WP | Phase / Deliverable | Target |
|---|---|---|
| WP-04 | Phase H — Model Candidate Layer | next |
| WP-05 | Phase I — Model Generation Agent / Internal Engineering Model | after H |
| WP-06 | Phase J — SysML v2 Code Generator | after I |
| WP-07 | Phase K — Validation Layer | after J |
| WP-08 | Phase L — Output Writer | after K |
| WP-09 | Guided Workflow UI | after H–L vertical slice |
| WP-10 | Ingestion + Human Review UX simplification | after H–L |
| WP-11 | Architecture / Model Proposal UX | after H–L |
| WP-12 | End-to-End Demo Hardening | 2026-08-16 |
| WP-13 | Demo Freeze + Rehearsal | 2026-08-17 |
| WP-14 | CATIA / SSOT Checkpoint | after demo / before final reconciliation |

## Phase H — Model Candidate Layer

Consume only active Approved Inputs and create explicit non-authoritative Model
Candidates with relationship semantics, prioritization, rationale,
comparability impact and Human Review status.

## Phase I — Model Generation Agent

Assemble reviewed Model Candidates into an internal engineering model without
yet treating textual SysML v2 as the internal source of engineering authority.

## Phase J — SysML v2 Code Generator

Generate deterministic, versioned target textual notation from the internal
engineering model.

## Phase K — Validation Layer

Validate syntax, target notation, structure, relationship semantics,
constraints, traceability and comparability. Failed required validation blocks
publication.

## Phase L — Output Writer

Publish the versioned output package containing SysML v2 files, validation
evidence, generation summary, traceability and artifact fingerprints.

## Demo UX Sequence

After H–L:

```text
Guided Workflow UI
→ Ingestion / Human Review simplification
→ Architecture / Model Proposal UX
→ end-to-end hardening
→ functional freeze
→ product demo
```

Streamlit remains the UI technology through the demo.

---

# Post-prototype Phases

## Phase N — CATIA Shadow-model Migration and Final Reconciliation

Phase N retains:

- SYSIDE shadow-model migration
- final synchronization with CATIA
- removal of duplicated maintained model authority
- final reconciliation after Phases G–L
- final requirement and architecture coverage
- confirmation of CATIA-only maintained model authority

## Phase Q — Thesis Architecture Documentation

Phase Q shall document:

- development phases
- architecture decisions
- alternatives and rationale
- consequences
- requirement traceability
- implementation traceability
- ontology and semantic architecture
- Human Review architecture
- validation architecture
- model-comparability approach
- limitations and deferred work

## Phase R — Task Profile Portability Evaluation

Phase R shall evaluate the thesis that the core Turing Generator architecture
can be adapted quickly to a different engineering task by replacing a bounded
set of task-specific artifacts.

The reusable core is expected to include:

- Project Workspace
- Source Registry
- Processing Runs
- artifact persistence
- Human Review
- evidence and traceability
- dashboard
- agent execution
- publication gates

The evaluation shall produce a Task Profile Replacement Manifest that records:

- artifact path
- artifact role
- core or task-specific classification
- unchanged, adapted or replaced status
- dependencies
- required validation
- required code changes

The initial alternate task shall be Requirements Quality and Completeness
Analysis.

It shall assess:

- requirement formulation against an explicitly selected standard or rule set
- requirement completeness
- requirement atomicity
- ambiguity
- contradictions between requirements
- missing information
- proposed corrections
- proposed additions
- Human Review of proposed changes

The evaluation shall measure:

- number of changed files
- share of unchanged core modules
- implementation time
- reused tests
- new validation rules
- required code changes
- achieved functional coverage

## Phase S — Project Affinity Recommendation

Phase S is a low-priority post-Phase-R enhancement.

When a user selects new data for upload, the system may analyze the data before
persistent Source registration and recommend existing projects that appear to
fit.

The recommendation may consider:

- project description
- framework template
- existing Sources
- accepted project vocabulary
- framework coverage
- semantic similarity

The result shall be a ranked recommendation.

It shall not automatically assign or persist the Source.

The user shall confirm or override the project selection before registration.

This preserves the accepted rule that every persisted Source belongs to exactly
one Project and that no permanent unassigned Source pool exists.

---

# Not Yet Implemented

The following capabilities are not yet implemented:

- Approved Input Promotion
- Approved Input repository and API
- end-to-end review-to-promotion workflow
- model candidate layer
- relationship candidate prioritization
- canonical relationship-selection profile
- model comparability profile
- internal model generation
- SysML v2 code generation
- generated-model validation
- versioned export package
- CATIA synchronization
- final shadow-model migration
- task-profile portability evaluation
- alternate Requirements Quality and Completeness task
- project-affinity recommendation
- project editing after creation
- project deletion including assigned data
- refined retry and successor UI
- operational live-team performance measurements
- OCR and unrestricted multimodal extraction

---

# Current Known Limitations and Risks

## Active

- the end-to-end prototype schedule is compressed to 2026-08-14
- Approved Input identity, repository and promotion lifecycle remain open in G5
- P9 ends in `awaiting_review`, not Approved Input
- no model candidates are generated
- no internal engineering model is generated
- no SysML v2 code is generated
- no generated-model validation or export exists
- final relationship semantics and comparability rules are not yet defined
- full live-team performance and cost measurements remain open
- project editing and deletion remain open
- local demo data remains non-authoritative

## Controlled by Design

- project and Source identities remain separate
- every persisted Source belongs to one Project
- Source and artifact content is hash-bound
- cross-project mixing is rejected
- unknown framework and ontology references are rejected
- `context_only` Sources cannot create engineering evidence
- candidates remain non-authoritative until Human Review
- consensus and confidence cannot bypass Human Review
- required prompt context cannot be silently truncated
- ontology snapshots are pinned and integrity-checked
- CATIA remains authoritative for engineering knowledge
- P9 artifacts remain processing evidence until promotion
- relationship prioritization will remain advisory until Human Review
- project-affinity recommendations will remain advisory until user confirmation

---

# Next Milestone

Phase H — Model Candidate Layer

Execution order:

```text
inspect active Approved Input boundary
→ surface exact Phase-H architecture questions
→ define Model Candidate contracts and ownership
→ define relationship candidate / comparability semantics
→ review the architecture contract
→ obtain explicit acceptance
→ implement incrementally
```

The first Phase-H step is architecture definition, not implementation.

No production code for Model Candidates shall be added before the contract is
explicitly accepted.

---

# Repository Collaboration Workflow

External GitHub repositories and repository links are used passively for
inspection only.

AI assistants shall not commit, push or directly modify GitHub repository
content.

Repository changes are applied, reviewed, committed and pushed locally by the
project owner.

AI assistants act as implementation guides and identify every affected file by
repository-relative path before proposing a change.

Broad staging commands shall not be used in a mixed working tree.

---

# SSOT Update Cadence

This update closes Phase G and activates Phase H as the next implementation
phase.

It records:

- G6 Human Review and promotion UI completion
- G7 manual acceptance and implementation findings F01–F06
- Approved Input promotion and authority evidence
- reopen and immutable-predecessor evidence
- Scoped Action impact-preview evidence
- running-state write-action guard
- G7.4 focused and complete regression evidence
- ADR-017 simple-by-default / progressive-disclosure interaction architecture
- the non-blocking post-implementation presentation position
- the H–L closed vertical-slice roadmap
- guided-workflow and UX work after H–L
- 2026-08-17 functional freeze
- 2026-08-18 product demo
- Streamlit retention through the demo
- artifact-driven architecture adaptability as an explicit outlook

The next SSOT update is due after Phase H completion or earlier if a material
architecture decision changes the accepted roadmap or authority boundary.

---

# Reference Documents

- Roadmap: `roadmap.md`
- Working Rules: `working_rules.md`
- Architecture Decisions: `decisions/`
- Model Registry: `model_registry.json`
- Change Log: `change_log.md`
- Handover: `handovers/current_chat_handover.md`
- Framework Template: `../context/frameworks/turing_rflp_framework.json`
- Support Profile: `../context/frameworks/turing_preliminary_support_profile.json`
- Ontology Registry: `../context/semantics/ontology_registry.json`
- Turing Core Vocabulary: `../context/semantics/turing_core_vocabulary.json`
