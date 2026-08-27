# Change Log

## 2026-08-27 — Thesis-driven completion roadmap accepted

Following successful real Gate-3 validation of Project `000116`, the remaining
project roadmap was explicitly changed from implementation-backlog-driven to
thesis-driven execution.

Accepted principle:

> Further implementation after Gate 3 is justified only where it is required
> to substantiate an open thesis claim, close a thesis-critical validation gap,
> or establish the final prototype baseline. Open implementation findings are
> not automatically remaining thesis scope.

Accepted remaining sequence:

```text
Professor presentation
→ Safe Demo / Kochshow
→ Gate-3 thesis evaluation record
→ Thesis Scope Gate
→ explicit BLK-002 decision
→ only thesis-required implementation
→ final targeted validation
→ CATIA / architecture synchronization
→ prototype implementation freeze
→ Results / Discussion / Limitations finalization
→ final claim / traceability / consistency audit
→ thesis completion
```

`BLK-002` is not automatically selected for implementation.

Instead, the thesis scope must explicitly decide whether a true Multi-Source
empirical result is required by the research question.

If required:

```text
resolve BLK-002
→ real Multi-Source E2E
→ downstream validation
```

If not required:

```text
retain BLK-002 as explicit limitation / Future Work
```

The same scope discipline applies to remaining SEM / OBS findings.

The final architecture synchronization is intentionally scheduled after the
last thesis-critical implementation change, followed by a formal prototype
freeze.

This decision establishes the operating principle:

```text
The thesis drives remaining implementation.
The remaining implementation backlog does not define the thesis.
```

---


## 2026-08-27 — v0.3.0 Gate-3 real validation and publication

Project `000116`, Lead Source
`SRC-000002 / 01_product_overview.md`, completed the governed real
single-source workflow through immutable publication.

Final chain:

```text
IEM-000001
→ TFR-000002 / TFA-000002
→ MQR-000001 / MQA-000002
→ IEM-000003
→ deterministic SysML v2
→ real SYSIDE PASS
→ FMR-000001 / FRV-000002
→ FRD-000001
→ OUT-000001
```

Final validation evidence:

```text
SYSIDE Modeler CLI 0.10.3
exit code: 0
diagnostics: 0
validation: VALID
publication gate: PASSED
```

Generated artifact fingerprint:

`7b5babbe048f941d9875a345e34a03e1c249061a93e03ade3c9dcfb971f4ddb1`

Validation fingerprint:

`0e8998e6fe2d4b717cbee6464cdca1b060ad21601dd92389706240b38387ea67`

Published package:

`OUT-000001`

Final complete repository regression after all corrective work:

`6100 passed in 17.87s`

The real run exposed and drove bounded generic corrections for:

- Model Refinement incomplete-successor handling;
- SEM-015 Human-authority payload normalization;
- relationship endpoint-construct compatibility after Target-Model Formulation;
- immutable Target-Model Formulation revisions;
- current SYSIDE revalidation and immutable Final Model Review revision adoption;
- explicit Generation Profile resolution through `repo_root`.

The original Phase-J fail-closed relationship guard was retained.

No Project-`000116` special case was introduced.

`IMR-000001` remains authoritative engineering information but is explicitly
Human-authorized as intentionally not formally materialized because its
effective endpoint-construct combination lacks a currently authorized formal
representation.

The successful validation is a single-source acceptance result.
`BLK-002` remains open for true Multi-Source Processing.

Canonical closeout:

`collaboration/checkpoints/2026-08-27_gate3_validation_handover_ssot.md`

Next activity:

Professor presentation using the existing presentation plan, followed by Safe
Demo preparation using the agreed Kochshow strategy.

---


## 2026-08-25 — WP-12 Golden E2E accepted / Known-Good baseline established

The first complete Human-authority-backed single-source Turing Generator E2E was
successfully executed with project `120412`:

```text
Engineering Source
→ Processing
→ Human Engineering Review
→ Approved Engineering Information
→ Human Model Placement
→ deterministic Model Assembly
→ SEM-015 quality/refinement + Human Review 2
→ IEM-000002
→ deterministic SysML v2 generation
→ SYSIDE validation PASS
→ Final Model Review FRV-000002
→ Human release FRD-000001
→ Published Output OUT-000001
```

Published SysML:

`data/output/120412/OUT-000001/generated_model.sysml`

Verification:

```text
29 focused tests passed
6046 complete repository tests passed
git diff --check PASS
SYSIDE completed / exit 0 / diagnostics 0
```

BLK-002 remains open for Multi-Source acceptance and is not weakened by this
single-source acceptance.

This checkpoint also changes development workflow: after the closeout commit,
`main` is the Known-Good fallback and new implementation work proceeds only on
dedicated feature branches.

Next activity is BLK / SEM / ODS cross-register triage before selecting further
implementation.

Authority:

`collaboration/checkpoints/2026-08-25_wp12_golden_e2e_known_good_baseline.md`

---

## 2026-08-24 — WP-12 R4c Live E2E SSOT checkpoint

A new authoritative WP-12 verification checkpoint was recorded.

Result semantics are now explicit:

```text
PASS
PASS WITH FINDINGS
FAILED WITH BLOCKER
BLOCKER RESOLVED -> RETEST -> PASS / PASS WITH FINDINGS
```

Current overall result is `FAILED WITH BLOCKER`.

Active blockers:
- BLK-002 — Cross-Source Processing Artifact Identity Collision
- BLK-006 — LLM-assisted Model Proposal generation fails in live E2E

Resolved/live-retested blockers:
- BLK-004 — Approved Input Promotion
- BLK-005 — Approved Engineering Information -> Phase H handoff

Project `120412` has live-validated the R4c single-source path through Phase-H
readiness with 17 Approved Subjects and 21 accepted semantic Relationships.
The latest complete regression is `5889 passed, 1 skipped`; `git diff --check` passes.

Canonical evidence:
- `collaboration/checkpoints/2026-08-24_wp12_r4c_live_e2e_ssot.md`
- `collaboration/audits/wp12_findings.md`
- `collaboration/audits/wp12_multi_document_dry_run_test_protocol.md`

No version release or WP-12 closeout is claimed by this checkpoint.

---
<!-- BEGIN SSOT UPDATE 2026-08-20 -->
## 2026-08-20 — WP-12 Demo / Architecture-Recovery SSOT

- preserved formal `WP12-E2E-DRY-001` as `IN PROGRESS / INTERRUPTED FOR BLOCKING DEFECT CORRECTION`,
- preserved BLK-002 as open/blocking for cross-source identity,
- reframed BLK-003 as a source-grounding / responsibility-boundary recovery problem rather than Review Item count optimization,
- captured Project `877791` / `RUN-000001` D3/D4/Review counts,
- recorded the simple Gemini `01_product_overview.md` run as qualitative diagnostic evidence,
- proposed ADR-027 separating Evidence Detection from Persona Interpretation,
- established that personas/runs shall not multiply Engineering Subjects,
- established reference knowledge as guidance only, never Project engineering evidence,
- established ontology/terminology alignment as a supporting service,
- placed Architecture Derivation after Human-approved engineering information,
- required P9/D3/D4 audit with `KEEP / MOVE / REDUCE / BYPASS / REMOVE`,
- fixed Monday 2026-08-24 demo strategy to real single-source LLM start plus transparent switch to a genuinely persisted prior run if needed,
- recorded CATIA rule: new high-level lifecycle only after implementation alignment and ADR-027 acceptance,
- replaced `current_chat_handover.md` and embedded the exact next-chat startup prompt.
<!-- END SSOT UPDATE 2026-08-20 -->

## 2026-08-19 — Presentation / WP-12 / Demo SSOT Checkpoint

A time-critical execution checkpoint was established for the mandatory professor
demo on 2026-08-24.

Priority is now:

```text
presentation preparation
→ reliable live or Demo/Replay demo path
→ BLK-003 Architectural Recovery
```

The checkpoint records:

- the existing Kick-off-to-current presentation concept,
- the two planned CATIA presentation models,
- the interrupted WP-12 status,
- BLK-001/002/003 and the current BLK-003 empirical result,
- the formative OBS register,
- planned SOURCE-PURITY/MODEL-RELEVANCE, STABILITY, DASH and Demo/Replay tests,
- a mandatory replay fallback if the live system is not credible by the evening
  of 2026-08-20,
- and the over-next architectural recovery of the ingestion / semantic / review
  chain.

Authority:
`collaboration/checkpoints/2026-08-19_presentation_wp12_demo_ssot.md`

This checkpoint does not close WP-12, BLK-002 or BLK-003.

---

## 2026-08-16 — WP-12 Stage-A Test Design Accepted and Prepared

This is a preparation checkpoint, not WP-12 completion. Project versions remain
unchanged:

- Architecture Version: 1.13
- Knowledge Base Version: 1.20
- Implementation Version: 0.22
- Roadmap Version: 1.20

Prepared and explicitly accepted for formal execution:

- four controlled synthetic legacy source documents
- multi-document Expected Engineering Contract
- detailed `WP12-E2E-DRY-001` test protocol with expected results and checkboxes
- formative task-based self-evaluation log
- controlled Stage-A dry-run → explicit release gate → Stage-B workflow

The accepted validation strategy is:

```text
controlled synthetic multi-document dry run
→ documented findings and bounded fixes
→ full regression
→ explicit Dry-Run Release Gate
→ only then representative non-synthetic test data
```

The Stage-A specification is frozen by the preparation-baseline commit. During
execution, deviations from the accepted protocol shall be documented rather than
silently changing the expected result to match observed system behavior.

Formal Stage-A execution is scheduled for 2026-08-17 together with the remaining
demo-preparation work packages WP-13 and WP-14.

Stage B is not authorized until the explicit Stage-A release gate passes. The
known missing SYSIDE CLI remains fail-closed and may only be recorded as a
documented external limitation; it shall not be bypassed.

---

## 2026-08-16 — WP-11 Architecture / Model Proposal UX Completion

Versions after this update:

- Architecture Version: 1.13
- Knowledge Base Version: 1.20
- Implementation Version: 0.22
- Roadmap Version: 1.20

Implementation reference:

- WP-11 completion: the commit containing this SSOT update
- Prior WP-10 final checkpoint:
  `63b911dbf5da9b4a2be7013553fd8d47f4e30db4`
- Accepted / extended UX architecture:
  `collaboration/decisions/ADR-024-guided-engineering-workflow-and-ux-projection-architecture.md`

Completed WP-11 decomposition:

```text
WP-11.1  Model Proposal presentation foundation
WP-11.2  Architecture / Model Proposal workspace
WP-11.3  Candidate Decision workflow
WP-11.4  acceptance and closeout
```

Implemented capabilities:

- UX-17 Architecture / Model Proposal projection contract
- deterministic immutable `GuidedModelProposalPresentation`
- architecture-first proposed Elements and Relationships
- model-area grouping for engineer-readable structure
- Relationship Choice Groups displayed as alternatives rather than votes
- persisted preferred / accepted alternative state retained
- profile deviation and structural comparability presentation
- Candidate Review progress and authoritative Phase-I readiness projection
- Human decisions colocated with the affected Candidate content
- exact MCS + Candidate binding for every Candidate Review write
- unchanged normative Candidate decisions:
  `accepted`, `rejected`, `deferred`, `accepted_exception`
- ready Candidate Sets suppress redundant Candidate write controls
- Focused View reduces visible implementation metadata
- Technical View retains IDs, fingerprints, Approved Input references,
  conformance, comparability and traceability

Verification:

```text
WP-11 focused regression:
40 passed in 0.52s

Complete repository regression:
5577 passed, 1 skipped in 14.19s

git diff --check:
PASS
```

Live acceptance status:

```text
WP-11 implementation:         PASS
WP-11 automated acceptance:   PASS
populated Model Proposal UI:  DEFERRED → WP-12
```

The populated live case is deferred because no representative Model Candidate
data exists yet. WP-12 will create / process the connected demo Project and
exercise Model Proposal, Candidate Review and all downstream stages in context.

That connected run will also be retained as a formative task-based
self-evaluation of the demonstrator. Findings are qualitative design evidence;
they do not constitute an independent quantitative usability study.

Phase transition:

```text
WP-11 Architecture / Model Proposal UX: COMPLETE
WP-12 End-to-End Demo Hardening: ACTIVE
```

No Candidate, Approved Input, Internal Engineering Model or CATIA authority was
transferred to the UI.

---

## 2026-08-16 — WP-10 Ingestion + Human Review UX Simplification Completion

Versions after this update:

- Architecture Version: 1.12
- Knowledge Base Version: 1.19
- Implementation Version: 0.21
- Roadmap Version: 1.19

Implementation reference:

- WP-10 completion: the commit containing this SSOT update
- Prior WP-09 completion:
  `23fab6ab597a922b3c2c18d0088fa6c270e2629e`
- Accepted / extended UX architecture:
  `collaboration/decisions/ADR-024-guided-engineering-workflow-and-ux-projection-architecture.md`

Completed WP-10 decomposition:

```text
WP-10.1  presentation foundation
WP-10.2  Processing UX
WP-10.3  Human Review Workspace UX
WP-10.4  Review lifecycle + advanced actions UX
WP-10.5  visual acceptance + closeout
```

Implemented capabilities:

- UX-16 Processing and Human Review projection contract
- deterministic content-first Processing and Human Review read-side adapters
- filename-first Source inventory
- readable Processing status and direct Human Review continuation
- Focused / Technical presentation split without parallel workflow authority
- engineering-content-first Human Review Queue and Review Items
- Persona grouping and side-by-side proposal comparison
- repeated runs retained under their Persona rather than counted as new votes
- consensus / variance display sourced only from persisted consensus evidence
- one-Persona result guard preventing false inter-Persona agreement claims
- progressive disclosure of evidence and advanced Review operations
- clearer Finalization, Human confirmation, Approved Input Promotion and Reopen
  lifecycle interaction
- immutable predecessor semantics preserved during Reopen
- exact technical traceability retained on demand
- top-level Workspace widget aligned to one Session State authority

Verification:

```text
Complete repository regression:
5563 passed, 1 skipped in 13.91s

Final targeted shell / Human Review regression:
43 passed in 0.53s

git diff --check:
PASS
```

Manual live acceptance:

```text
Focused Processing: PASS
Ready-to-process state: PASS
live LLM Processing → 15 unreviewed outputs: PASS
Processing → Human Review transition: PASS
Human Review Queue / Review Items: PASS
Finalization state presentation: PASS
```

The inspected Human Review fixture exposed one Persona per inspected Review Item.
Multi-Persona visual acceptance is intentionally retained for the populated
WP-12 end-to-end demo Project; automated tests cover grouping and side-by-side
presentation.

Phase transition:

```text
WP-10 Ingestion + Human Review UX Simplification: COMPLETE
WP-11 Architecture / Model Proposal UX: ACTIVE
```

No CATIA engineering authority or normative Processing / Review / Approved Input
authority was transferred to the UI.

---

## 2026-08-16 — WP-09 Guided Workflow UI Completion

Versions after this update:

- Architecture Version: 1.11
- Knowledge Base Version: 1.18
- Implementation Version: 0.20
- Roadmap Version: 1.18

Implementation reference:

- WP-09 completion: the commit containing this SSOT update
- Prior Guided Engineering Workspace checkpoint:
  `24957252f82d8f440ba8eccb0c571c906d78a858`
- Accepted Guided Workflow architecture:
  `collaboration/decisions/ADR-024-guided-engineering-workflow-and-ux-projection-architecture.md`

Completed WP-09 decomposition:

```text
WP-09.1  Guided Engineering View + presentation models
WP-09.2  global shell, navigation, Engineer Home and Next Action
WP-09.3  downstream workflow detail workspaces
WP-09.4  authority-preserving Human writes + exact publication bridge
```

Implemented capabilities:

- deterministic `GuidedWorkflowReadService`
- engineer-centered `Your work` and `Next action`
- common global Project context
- Focused / Technical presentation modes
- Model Proposal, Final Model Review and Published Output detail views
- explicit multiple-head selection without implicit latest write targets
- Candidate `Accept`, `Reject`, `Defer` and `Accept as exception`
- immutable Human Final Review Change Proposals
- explicit exact Human publication approval
- exact persisted FRV/J/K reconstruction before publication
- final publication delegated to the existing `OutputWriter`
- fail-closed application write delegation
- read-side reconstruction after writes
- deferred Human Review outcomes counted as unresolved work
- primary Streamlit entry point clarified as `app/turing_generator_app.py`

Verification:

```text
WP-09 focused regression:
111 passed in 0.63s

Complete repository regression:
5542 passed, 1 skipped in 13.36s

git diff --check:
PASS
```

Manual live UI smoke acceptance:

```text
common application shell: PASS
Project selection: PASS
Technical-details toggle: PASS
seven workspace views reachable: PASS
empty-state presentation: PASS
navigation continuity: PASS
```

The smoke-test Project contained no downstream Candidate / Final Review /
Published Output evidence. Live exercising of Candidate writes, Final Release
and Publication is therefore intentionally assigned to the fully populated
WP-12 end-to-end demo Project. Automated tests cover the exact authority-bound
write paths.

Phase transition:

```text
WP-09 Guided Workflow UI: COMPLETE
WP-10 Ingestion + Human Review UX Simplification: ACTIVE
```

No CATIA Requirement, Function or Logical Component was silently created or
modified during WP-09 closeout.

---

## 2026-08-14 — Phase L Final Model Review and Output Publication Completion

Versions after this update:

- Architecture Version: 1.10
- Knowledge Base Version: 1.17
- Implementation Version: 0.19
- Roadmap Version: 1.17

Implementation reference:

- Phase-L completion: the commit containing this SSOT update
- Accepted Phase-L architecture:
  `72974bb63c92c37baac5eef6b740ee91bacedd01`
- Prior Phase-K completion:
  `1fec1db815997c15b83e068ffb4bd03b93106170`

Architecture decision:

`collaboration/decisions/ADR-023-final-model-review-and-output-publication-architecture.md`

Completed Phase-L decomposition:

```text
L1  Final Model Review domain foundation
L2  project-local immutable Final Model Review repository
L3  Final Model Review read model and UI projection
L4  Change Proposal and controlled revision / agent-reproposal loop
L5  exact Human release gate
L6  Output Publication repository + OutputWriter
L7  J→K→Final Review→Human Release→OUT integration
```

Implemented capabilities:

- generated-but-not-released SysML persisted as project-local review evidence
- immutable review/revision/item/Human-decision contracts
- deterministic model/code/validation/traceability/proposal review view
- Human code/diagram edits represented as immutable Change Proposals
- authority-aware change routing back to H/J/K or L presentation ownership
- optional bounded agent/LLM re-proposal with unchanged Human authority
- exact `valid / passed` + Human release gate
- stale/superseded review rejection
- versioned `TURING_SYSML_V2_OUTPUT 1.0.0`
- immutable sequential project-local `OUT-xxxxxx` packages
- byte-identical publication of the reviewed generated SysML
- generation summary, validation result/report and traceability projections
- deterministic package/file/publication-input fingerprints
- atomic fail-closed publication, recovery and integrity scanning
- exact re-publication idempotence
- no implicit latest-artifact or latest-review authority

Verification:

```text
Focused L1–L7 regression:
147 passed, 1 skipped in 1.63s

Complete repository regression:
5451 passed, 1 skipped in 26.84s

git diff --check:
PASS
```

The single skip is the intentional live real-SYSIDE L7 vertical-slice acceptance test.

Runtime probe:

```text
command -v syside
→ unavailable

syside --version
→ command not found
```

The automated IEM→J→K→Final Model Review→Human Release→OUT vertical slice is
green with a deterministic completed external-validator test adapter.

A real SYSIDE-backed publication remains fail-closed until the SYSIDE CLI is
installed, licensed and executable. This is retained as an operational
acceptance blocker, not an open Phase-L implementation defect.

The accepted project flow is now:

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

Phase transition:

```text
Phase L implementation: COMPLETE
Live SYSIDE publication acceptance: BLOCKED — missing CLI
WP-09 Guided Workflow UI: NEXT
```

No CATIA Requirement, Function or Logical Component was silently created or
modified during Phase-L closeout. Final implementation-to-CATIA reconciliation
remains deferred to the planned CATIA / SSOT checkpoint.

---

## 2026-08-14 — Phase K Validation Layer Completion

Versions after this update:

- Architecture Version: 1.9
- Knowledge Base Version: 1.16
- Implementation Version: 0.18
- Roadmap Version: 1.16

Implementation reference:

- Phase-K completion: the commit containing this SSOT update
- Accepted Phase-K architecture:
  `601b2134fcb227b114b4c50ad14d09ca920c81c5`
- Prior Phase-J completion:
  `c57945e2c93613d4f55096118d7858edc41dd7e2`

Architecture decision:

`collaboration/decisions/ADR-022-sysml-v2-validation-layer-architecture.md`

Completed Phase-K decomposition:

```text
K1  Validation domain foundation + Validation Profile
K2  Artifact/context/Target-Notation/Structure/Traceability validators
K3  Relationship + endpoint consistency validator
K4  SYSIDE CLI adapter + deterministic diagnostic normalization
K5  SysMLValidationService + status/gate/fingerprint assembly
K6  J→K→L boundary regression + status hardening + closeout
```

Implemented capabilities:

- versioned `TURING_SYSML_V2_VALIDATION 1.0.0`
- immutable `SysMLValidationResult`
- exact Phase-J generation-policy reference resolution
- standalone artifact-set and fingerprint integrity validation
- Target Notation constrained-subset validation
- Artifact Structure validation
- relationship and endpoint target-model consistency validation
- traceability and comparability-policy consistency validation
- isolated non-mutating SYSIDE CLI adapter
- runtime external-validator identity/version discovery
- deterministic diagnostic normalization
- explicit `valid`, `invalid` and `incomplete` statuses
- fail-closed `passed` / `blocked` publication gate
- infrastructure unavailability represented as `incomplete / blocked`
- deterministic validation-input and result fingerprints
- exact artifact-fingerprint-bound K→L handoff contract
- no IEM/Candidate reread for semantic reinterpretation
- no generated-text repair, regeneration or publication in K

Final verification:

```text
Focused K1–K6 regression:
65 passed in 1.41s

Complete repository regression:
5304 passed in 25.97s

git diff --check:
PASS
```

Runtime external-validator probe on the verification workstation:

```text
SYSIDE CLI: unavailable
```

The unavailable CLI is deliberately fail-closed and does not invalidate the
model. Until SYSIDE is installed and executable, validation returns
`incomplete / blocked`; a live `valid / passed` run remains required before
Phase-L operational acceptance.

Phase-N2 reconciliation candidates are recorded for:

- deterministic dual-layer generated-model validation
- explicit external-validator infrastructure boundary
- immutable validation result and validation identity
- fail-closed publication gate
- exact generated-artifact/validation fingerprint binding
- strict J/K/L responsibility separation

No CATIA Requirement, Function or Logical Component was created or modified
during Phase-K closeout.

Phase transition:

```text
Phase K implementation: COMPLETE
Phase L: NEXT — Output Writer architecture contract
Live K→L publication acceptance: BLOCKED until SYSIDE CLI is available
```

---

## 2026-08-13 — Phase J SysML v2 Code Generator Completion

Versions after this update:

- Architecture Version: 1.8
- Knowledge Base Version: 1.15
- Implementation Version: 0.17
- Roadmap Version: 1.15

Implementation reference:

- Phase-J completion: the commit containing this SSOT update
- Accepted Phase-J architecture:
  `af6953486a71c3073c0169ef5052dbcabb49c4fc`
- Prior H9 completion:
  `1cee49350dd2f24d6a1c80fb0aa1c0d2b5fd27fc`

Architecture decision:

`collaboration/decisions/ADR-021-syside-compatible-sysml-v2-generation-architecture.md`

Completed Phase-J decomposition:

```text
J1  Generation foundation + Target Notation 0.2.0 + SYSIDE syntax evidence
J2  Generation Profile + Artifact Structure Profile + deterministic preflight
J3  package/symbol/safe-text/canonical-order projection
J4  deterministic element renderer
J5  deterministic relationship renderer + endpoint-role integration
J6  GeneratedSysMLArtifactSet + traceability + fingerprints/idempotence
J7  explicit generation service boundary + regression + SSOT closeout
```

Implemented capabilities:

- explicit IEM identity as sole generation input
- deterministic serialization with no LLM production generation
- versioned Target Notation, Generation Profile, Artifact Structure and Generator Rules
- deterministic preflight and fail-closed unsupported semantics
- requirement usage, use-case definition, action usage and part usage generation
- dependency, allocation and satisfaction relationship generation
- exact endpoint-role and endpoint-construct compatibility
- corrected Feature-based allocation representation after SYSIDE integration feedback
- deterministic package projection and stable technical symbols
- safe engineering documentation handling
- canonical formatting and qualified relationship references
- immutable `GeneratedSysMLArtifactSet`
- exact source-to-generated-location traceability
- generation-input, unit-content and artifact-set SHA-256 fingerprints
- byte-identical idempotence
- explicit Phase-J→K handoff
- no publication into `data/output/` before Phase L

SYSIDE integration evidence:

- J4 element rendering PASS
- J5 dependency/allocation integration PASS after Feature-endpoint correction
- J5.2 satisfaction endpoint mapping PASS

Final verification:

```text
Targeted Turing Core synchronization regression:
191 passed in 0.19s

Complete repository regression:
5239 passed in 13.77s

git diff --check:
PASS
```

The complete regression initially exposed a stale Turing Core reference to
Target Notation `0.1.0`. Both the source-reference pin and Turing Core
`sysml_v2_mapping_policy` were synchronized to `0.2.0`. The strict reference
validation was retained unchanged.

Phase-N2 reconciliation candidates were recorded for:

- deterministic explicit-IEM SysML v2 generation
- versioned SYSIDE-compatible target notation
- separate semantic mapping / artifact structure / generator rules
- fail-closed unsupported semantics and endpoint compatibility
- deterministic generation identity, fingerprints and idempotence
- generated-output traceability to approved engineering evidence
- explicit J/K/L responsibility separation

No CATIA Requirement, Function or Logical Component was created or modified
during Phase-J closeout.

Phase transition:

```text
Phase J: COMPLETE
Phase K: NEXT — Validation Layer architecture contract
```

---

## 2026-08-13 — H9 Hybrid Target Projection Completion

Versions after this update:

- Architecture Version: 1.7
- Knowledge Base Version: 1.14
- Implementation Version: 0.16
- Roadmap Version: 1.14

Implementation reference:

- H9 completion: the commit containing this SSOT update
- Phase-I completion baseline:
  `027269e94df0ec586a8fd489e78c92fddd0a3aa5`

Architecture decision:

`collaboration/decisions/ADR-020-hybrid-target-projection-and-coverage-architecture.md`

Completed H9 decomposition:

```text
H9.1  Projection disposition and coverage model
H9.2  shared deterministic profile resolver
H9.3  strict deterministic projection on shared resolver
H9.4  structured LLM projection contract
H9.5  bounded unresolved-only LLM executor
H9.6  HybridModelCandidateDeriver
H9.7  generation provenance + Human Review / Phase-I integration
H9.8  SSOT closeout + Phase-N2 reconciliation candidate recording
```

Implemented capabilities:

- complete `mapped` / `ambiguous` / `unmapped` /
  `intentionally_not_projected` coverage
- preserved strict deterministic quick/dry-run path
- deterministic-first hybrid projection
- unresolved-only LLM routing
- compact profile-controlled LLM context
- bounded serial batching and pre-execution call limit
- no automatic retry loop
- strict JSON response validation
- rejection of hallucinated/non-offered rules
- explicit no-forced-fit behavior
- Candidate-level LLM proposals only; no SysML v2 generation
- hybrid element and relationship Candidate derivation
- preserved original Approved-Input evidence
- semantic uncertainty represented through support/rationale rather than false
  structural-profile exceptions
- generation provenance for deterministic and LLM-assisted paths
- unchanged Candidate Human Review and sole H→I read boundary
- Phase J remains deterministic serialization

Verification:

```text
Focused H9 regression:
61 passed in 0.69s

Complete repository regression:
5120 passed in 13.12s

git diff --check:
PASS
```

Bounded live LLM smoke:

```text
provider: openai
model: gpt-5-mini
calls: 1
retries: 0
input_tokens: 711
output_tokens: 634
reasoning_tokens: 512
total_tokens: 1345
result: proposed_mapping
selected_rule_id: ELEMENT_SYSTEM_FUNCTION
candidate_model_area: system.functional
candidate_element_type: function
support_level: partially_supported
```

The live smoke was non-persistent and used one unresolved Approved Input with
`batch_size=1` and `max_calls_per_run=1`.

Phase-N2 reconciliation candidates were recorded for:

- selectable deterministic / LLM-assisted projection
- complete target-projection coverage
- deterministic-first unresolved-only AI routing
- profile-controlled no-forced-fit AI proposals
- AI projection provenance under unchanged Human Review authority

No CATIA Requirement or Function was created or modified during H9. Exact model
reconciliation remains deferred to Phase N2.

Phase transition:

```text
H9 controlled extension: COMPLETE
Phase J: NEXT — SysML v2 Code Generator architecture contract
```

---

## 2026-08-13 — Phase I Completion and Phase J Transition

Versions after this update:

- Architecture Version: 1.6
- Knowledge Base Version: 1.13
- Implementation Version: 0.15
- Roadmap Version: 1.13

Implementation reference:

- Phase-I completion: the commit containing this SSOT update
- Accepted Phase-I architecture:
  `ff4ee4e038942f9ee267eb2ad6a6daa600b09e6d`
- Phase-H implementation baseline:
  `294bb5c75835f82807b88de0a779301a17e1cb2c`

Architecture decision:

`collaboration/decisions/ADR-019-internal-engineering-model-assembly-architecture.md`

Phase-I completion:

```text
I1  IDs + immutable Internal Model domain types
I2  manifests + fingerprints + H→I contract enrichment
I3  Framework/Profile resolution + structure materialization
I4  deterministic MCE/MCR → IME/IMR assembly
I5  repository + immutable persistence + bundle integrity
I6  explicit Phase-J read contract + regression
```

Implemented capabilities:

- enriched sole H→I authority transfer with Framework Template and derivation rules
- deterministic exact `assembly_input_fingerprint`
- immutable `IEM`, `IME` and `IMR` contracts
- deterministic manifest serialization and content fingerprints
- versioned `TURING_INTERNAL_MODEL_ASSEMBLY 1.0.0` rules
- exact Framework Template and Structure Profile resolution
- complete structural-skeleton materialization including empty configured nodes
- reviewed MCE → IME assembly without semantic reinterpretation
- reviewed MCR → IMR assembly with exact same-snapshot endpoint rebinding
- preserved relationship family, semantic intent and directionality
- exact Approved Input, Candidate and Human Review traceability
- explicit accepted-exception preservation
- fail-closed deterministic assembly boundary
- immutable project-local IEM persistence
- atomic temporary publication and recovery diagnostics
- safe-path / symlink rejection and project isolation
- project-wide IEM/IME/IMR identity no-reuse
- bundle-level integrity across manifest, structure, elements and relationships
- idempotent exact reassembly
- explicit I→J read contract:
  `InternalModelReadService.load_phase_j_input(...)`
- no implicit latest-IEM selection
- no SysML v2 textual generation in Phase I

Verification:

```text
Focused I1–I6 regression:
110 passed in 1.07s

Complete repository regression:
5087 passed in 26.00s

git diff --check:
PASS
```

Phase-I authority boundary:

```text
validated ModelCandidateAssemblyInput
→ deterministic Internal Engineering Model assembly
→ immutable IEM persistence
→ validated explicit InternalEngineeringModelSnapshot
```

Phase transition:

```text
Phase I: COMPLETE
Phase J: NEXT — SysML v2 Code Generator
```

No CATIA engineering element is silently changed by this implementation
closeout. ADR-019 records implementation architecture and CATIA alignment; CATIA
remains the engineering authority.

---

## 2026-08-13 — Phase H Completion and Phase I Transition

Versions after this update:

- Architecture Version: 1.5
- Knowledge Base Version: 1.12
- Implementation Version: 0.14
- Roadmap Version: 1.12

Implementation reference:

- Phase-H completion: the commit containing this SSOT update
- Accepted Phase-H architecture:
  `884d658726d9a5a2ac9f86786ded30db7fe38c68`
- Phase-G implementation baseline:
  `b598bf04770b08738bbce5c15f2f7dfb671aab01`

Architecture decision:

`collaboration/decisions/ADR-018-model-candidate-layer-and-structural-comparability.md`

Phase-H completion:

```text
H1  Identifiers and error foundation
H2  Immutable domain types
H3  Manifests, validation and fingerprints
H4  Repository, paths and immutable persistence
H5  Approved Input → Candidate generation pipeline
H6  Model Structure / Comparability Profile and relationship logic
H7  Candidate Human Review and Phase-I gate
H8  ModelProposalView and Phase-H completion
```

Implemented capabilities:

- immutable project-local MCS/MCE/MCR contracts
- exact Approved Input snapshot and provenance binding
- explicit relationship endpoints and semantic intent
- versioned Model Structure and Comparability Profile
- conservative profile-driven candidate derivation
- advisory relationship priority and comparability assessment
- immutable Candidate Human Review Decisions (`MCD`)
- exact fingerprint-bound accepted/rejected/deferred/exception decisions
- stale-decision and current-authority validation
- fail-closed Phase-I gate
- sole H→I read contract:
  `ModelCandidateReadService.load_phase_i_input(...)`
- deterministic non-authoritative `ModelProposalView`
- structural overview, relationship-choice groups, comparability summary,
  profile deviations, required decisions and next action
- deterministic JSON and Markdown proposal projections
- no Phase-H SysML v2 serialization

Verification:

```text
Focused H1–H8 regression:
168 passed in 1.63s

Complete repository regression:
4986 passed in 25.80s

git diff --check:
PASS
```

Phase-H authority boundary:

```text
Approved Input
→ Model Candidates
→ Candidate Human Review
→ validated ModelCandidateAssemblyInput
```

The Model Proposal remains a presentation projection and is not model authority.

Phase transition:

```text
Phase H: COMPLETE
Phase I: NEXT — architecture contract required before implementation
```

The polished Architecture / Model Proposal UI remains WP-11 and is not part of
the technical Phase-H completion gate.

---

## 2026-08-12 — Phase G Completion, ADR-017 and Phase H Transition

Versions after this update:

- Architecture Version: 1.4
- Knowledge Base Version: 1.11
- Implementation Version: 0.13
- Roadmap Version: 1.11

Implementation reference:

- Phase-G completion: `b598bf04770b08738bbce5c15f2f7dfb671aab01`
- Last prior committed checkpoint:
  `7209f17a610d3adb359e8b672a28020b71c03333` — G6 completion
- G5 checkpoint:
  `865cbab24dfb5bb1f5150ff9336a55d00299a035`

G6 completion:

- Human Review and promotion UI implemented
- proposal/evidence review and immutable item-level decisions implemented
- Scoped Review Actions exposed through impact preview and immutable revision writes
- exact Human Review Decision and finalization UI implemented
- Approved Input promotion and active-authority presentation implemented
- controlled Review reopening exposed
- project-bound ingestion retry/recovery semantics exposed
- safe provider-neutral failure feedback implemented

G6 verification:

```text
Focused regression: 145 passed
git diff --check: PASS
```

G7.3 manual acceptance:

- complete Human Review path verified
- unresolved relationships failed closed
- `RVV-000001` finalized on `RVR-000008`
- `HRD-000001` exact confirmation verified
- exact three-artifact finalized set verified
- `AIN-000001` and `AIN-000002` promoted
- AIN authority traced to exact Review, Source, Run and Attempt
- reopen created `RVV-000002` with fresh `RIT-000006` through `RIT-000010`
- finalized predecessor subtree remained byte-identical
- Scoped Action preview materialized one exact target and produced `RVR-000010`
- running Agentic Ingestion removed the second Run/Retry write action

Manual acceptance result:

```text
PASS
```

Recorded G7.3 findings:

```text
F01 Streamlit widget-owned Session State
F02 project-bound failed-Run retry integration
F03 running-state feedback / duplicate write affordance
F04 safe provider-neutral failure diagnosis
F05 pre-publication Attempt identity reuse
F06 cross-layer semantic-reference validation mismatch
```

All six findings are closed.

Evidence:

- `collaboration/audits/phase_g_manual_acceptance_test_report.md`
- `collaboration/audits/phase_g_manual_acceptance_findings.md`

G7.4 completion verification:

```text
Focused Phase-G completion regression:
65 passed in 8.95s

Complete repository regression:
4818 passed in 24.50s

git diff --check:
PASS
```

Architecture decision ADR-017 accepted:

`collaboration/decisions/ADR-017-simple-by-default-interaction-and-progressive-disclosure.md`

Interaction principle:

```text
Simple by default.
Explainable on demand.
Fully traceable underneath.
```

The principle applies system-wide to:

- Agentic Ingestion
- semantic processing
- Human Review
- Architecture / Model Candidates
- model generation
- validation
- SysML v2 generation

The interaction architecture distinguishes:

1. primary task-oriented workflow
2. explanation / rationale / relevant evidence
3. audit / traceability detail

Streamlit remains the prototype UI technology through the product demo.
No React, Vue or FastAPI rewrite is part of the demo critical path.

Roadmap transition:

```text
WP-04  Phase H — Model Candidate Layer
WP-05  Phase I — Model Generation Agent / Internal Engineering Model
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
2026-08-17  Functional freeze
2026-08-18  Product demo
```

The Zwischenstandspräsentation is moved after implementation and no longer
blocks Phase H.

Presentation framing to preserve:

- literature-derived Data / Process / Knowledge architecture
- eight Logical Components as implementation-level operationalization
- Knowledge Layer as cross-cutting governance
- high-level activity view with approximately 7±2 primary activities
- artifact-driven architectural adaptability as an outlook

Phase status:

```text
Phase G: COMPLETE
Phase H: NEXT — architecture contract required before implementation
```

---

## 2026-08-07 — G5 Completion and G6 Transition

Versions after this update:

- Architecture Version: 1.3
- Knowledge Base Version: 1.10
- Implementation Version: 0.12
- Roadmap Version: 1.10

Implementation reference:

- G5 completion: the commit containing this SSOT update
- Last prior committed checkpoint:
  `d472038008fdd6c8f72101037e71f9e05081acf0` — G4 completion

Verification:

```text
G5.1–G5.3 focused aggregate: 76 passed
G5.4 focused eligibility suite: 15 passed
G5.5 focused promotion-service suite: 18 passed
G5.1–G5.5 aggregate: 109 passed
G5.6 focused lifecycle and affected-boundary suite: 61 passed
Complete Approved Input package regression: 139 passed
Complete repository regression: 4692 passed in 18.33s
git diff --check: passed
No production code changed after the complete repository regression
```

G5.1 completion:

- project-local sequential immutable `AIN` and `AIE` identities were implemented
- Approved Input error, validation and allocation contracts were implemented
- initial Approved Input kinds and authority-state vocabulary were implemented

G5.2 completion:

- immutable Approved Input Manifest was implemented
- exact Project, Source, Processing Run, Review Item, finalized artifact-set,
  Human Review Decision and validation binding was implemented
- deterministic serialization and content fingerprinting were implemented
- relationship statements require valid target-notation profile evidence
- `stable_subject_key` and finalized artifact-set fingerprint are preserved

G5.3 completion:

- dedicated project-local Approved Input repository was implemented
- immutable manifest persistence, loading, listing and identifier allocation were
  implemented
- atomic no-overwrite publication and interrupted-write recovery diagnostics were
  implemented
- symbolic links, unexpected entries, tampered manifests and project-boundary
  violations fail closed

G5.4 completion:

- deterministic read-only Promotion Eligibility assessment was implemented
- current Source, Processing Run, artifact lifecycle, finalized Review evidence
  and exact Human Review Decision bindings are checked
- nonaccepted items remain non-promotable without blocking unrelated accepted
  items
- accepted relationships require valid profile evidence
- under the accepted G5.4 boundary, `open_question` remains non-promotable until
  the Review contract provides explicit conversion evidence

G5.5 completion:

- promotion materialization, planning and service responsibilities were separated
- promotion revalidates current authority snapshots before persistence
- promotion is idempotent
- partial promotion can resume deterministically without duplicating an active
  Approved Input
- one independently reviewed item produces at most one equivalent active
  Approved Input

G5.6 completion:

- Approved Input manifests remain immutable with initial state `active`
- lifecycle changes are represented only by immutable Approved Input Events
- project-local AIE identifiers are globally sequential and never reused
- derived states `invalidated`, `revoked` and `superseded` were implemented
- terminal transitions are limited to:
  `active -> invalidated`, `active -> revoked`, `active -> superseded`
- successor reconciliation retains materially unchanged accepted Approved Inputs
- changed accepted subjects create a new Approved Input and supersede the old one
- rejected or out-of-scope successor subjects revoke prior authority
- deferred or absent subjects do not silently revoke prior authority
- Promotion Equivalence is based on stable subject identity plus
  authority-relevant engineering content and evidence, not Review Version IDs

G5.7 completion:

- stable Phase H read contract was implemented:
  `ApprovedInputRepository.list_active_approved_inputs(project_id)`
- Phase H receives only currently active Approved Input manifests
- inactive Approved Inputs remain immutable and fully traceable
- complete G5 promotion, idempotence, invalidation, supersession and active-read
  integration was verified

Development-plan status:

```text
Domain
[x] IDs, Typen, Manifest
[x] Repository + Read Contract
[x] Validation + Fehlerhierarchie

Promotion
[x] Eligibility aus P4/P9
[x] Decision-/Fingerprint-Bindung
[x] promote / invalidate / revoke / supersede

Abschluss
[x] Vollständige Traceability
[ ] Review-/Promotion-UI
[ ] Tests + Manual Acceptance
```

Recorded Model Element Change Candidates:

- MEC-G5-001 — Immutable Approved Input authority derived from manifest plus
  append-only lifecycle events
- MEC-G5-002 — Promotion Equivalence and stable-subject retention across
  successor Review Versions
- MEC-G5-003 — Active-only Approved Input consumption boundary for Phase H

Candidate status:

- recorded from implementation evidence
- engineering review pending
- not accepted CATIA changes
- CATIA transfer not started

Phase G status:

- G1 through G5 completed
- G6 is next
- Phase G remains active

Immediate next activity:

```text
G6 — Human Review and promotion UI
→ surface the completed G2–G5 contracts
→ preserve exact authority and lifecycle boundaries
→ focused UI tests
→ review
→ G6 completion decision
```

No Phase H implementation begins before Phase G and the
Zwischenstandspräsentation are complete.

---

## 2026-08-06 — G4 Completion and G5 Transition

Versions after this update:

- Architecture Version: 1.3
- Knowledge Base Version: 1.9
- Implementation Version: 0.11
- Roadmap Version: 1.9

Implementation reference:

- G4 completion: the commit containing this SSOT update
- Last prior committed checkpoint:
  `cf3cd5f` — G4.2d finalized artifact-set integrity

Verification:

```text
Focused G4.3 suite: 18 passed
Extended Review Workspace regression: 365 passed
G4.4 lifecycle integration: 1 passed
Complete regression: 4552 passed, 1 stale vocabulary expectation
Corrected targeted vocabulary test: 1 passed
Effective verified baseline: 4553 passing tests
No production code changed after the complete regression
```

G4.2d completion:

- the exact immutable finalized artifact-set contract was implemented
- exact three-artifact membership was enforced
- cross-artifact identity, revision, decision and validation binding was
  implemented
- deterministic artifact ordering and artifact-set fingerprinting were
  implemented
- mixed, incomplete and tampered sets are rejected
- committed checkpoint: `cf3cd5f`

G4.2e completion:

- exact-byte staging under `.finalized.tmp` was implemented
- write, flush and validation occur before publication
- publication uses atomic rename to `finalized/`
- existing finalized content is never overwritten
- unsafe paths, symbolic links, partial writes and source changes fail closed

G4.2f completion:

- exact finalized artifact-set loading was implemented
- UTF-8, byte, fingerprint and binding validation was implemented
- deterministic regeneration comparison was implemented
- scan diagnostics identify interrupted, unsafe, unexpected, missing and
  invalid finalized states
- recovery-required states remain explicit and fail closed

G4.3 completion:

- finalized predecessors remain immutable
- reopening creates one new successor Draft
- only the latest finalized Review Version may be reopened
- parallel version branches are prohibited
- successor Version, Revision and Review Item identities are new
- materialized review state is preserved
- Scoped Review Actions are not copied
- `carried_forward` one-to-one Review Item lineage was implemented
- stable subject keys remain unchanged
- successor workspace creation is atomic

G4.4 completion:

- the complete finalize, persist, reopen, revise, refinalize and repersist
  lifecycle was verified
- predecessor Version, Revision and artifact bytes remained unchanged
- two independent finalized artifact sets were loaded successfully
- complete Review Document scanning remained clean
- G4 is complete

Recorded Model Element Change Candidates:

- MEC-G4-001 — Exact Finalized Artifact Set as a three-artifact boundary
- MEC-G4-002 — Atomic publication and explicit recovery boundary
- MEC-G4-003 — `carried_forward` Review Item lineage
- MEC-G4-004 — Linear Review Version succession without parallel branches

Candidate status:

- recorded from implementation evidence
- engineering review pending
- not accepted CATIA changes
- CATIA transfer not started

Phase G status:

- G1 through G4 completed
- G5 is next
- Phase G remains active

Immediate next activity:

```text
G5 — Approved Input promotion and lifecycle
→ exact implementation contract
→ explicit acceptance
→ implementation
→ focused tests
→ review
→ G5 completion decision
```

No Phase H implementation begins before Phase G and the
Zwischenstandspräsentation are complete.

---

## 2026-08-05 — G3 and G4.1–G4.2c Completion Checkpoint

Versions after this update:

- Architecture Version: 1.3
- Knowledge Base Version: 1.8
- Implementation Version: 0.10
- Roadmap Version: 1.8

Verified implementation:

- Repository: `mz-commits-ai4mbse/SysMLv2-Generator`
- Branch: `main`
- Verified implementation commit:
  `782b75a94f7008de9b08fc9724480f0786e6af01`
- Complete automated test suite: 4463 passed
- Remote synchronization: `HEAD == origin/main`

G3 completion:

- P4 and P9 evidence adapters were implemented.
- Structured proposal and evidence references were implemented.
- Stable Review Item construction was implemented.
- Deterministic Review Document assembly was implemented.
- Element, relationship and open-question separation was implemented.
- Exact Project, Source, Run, Attempt and Artifact traceability was preserved.
- Heuristic P4/P9 evidence merging was prohibited.
- P4-only Review Document construction was prohibited.

G3 implementation commit:

`53bf6046b931af7c7b5189cd78822fd7cf7d51ef`

G4.1 completion:

- deterministic finalization eligibility was implemented
- open and unresolved Review Items block finalization
- exact Review Version, Revision and validation binding was implemented
- Human Review target type `review_document_finalization` was implemented
- exact persisted confirmation was implemented
- stale decisions and fingerprint mismatches block finalization
- atomic finalized-version transition was implemented

G4.1 implementation commit:

`4cedfb10f81e08a3bbea7cdb2fee5d9a1235ddd5`

Verification:

```text
Focused G4.1 suite: 314 passed
Complete automated suite: 4402 passed
```

G4.2a–G4.2c completion:

- immutable `reviewed_document.json` contract implemented
- immutable `effective_decisions.json` contract implemented
- deterministic `reviewed_report.md` renderer implemented
- exact cross-source identity and fingerprint binding implemented
- deterministic serialization implemented
- public APIs implemented

Implementation commit:

`782b75a94f7008de9b08fc9724480f0786e6af01`

Verification:

```text
Focused G4.2a–G4.2c suite: 208 passed
Complete automated suite: 4463 passed
```

G4 remains active.

Immediate next activity:

```text
G4.2d — cross-artifact consistency and fingerprint binding
```

Roadmap addition:

```text
Phase G
→ Zwischenstandspräsentation
→ Phase H
```

The Zwischenstandspräsentation shall:

- demonstrate the workflow through Approved Input
- present current architecture and test evidence
- capture professor feedback
- review open risks and limitations
- review the retrospective Phase-G Model Element Change Candidate inventory
- synchronize the SSOT before Phase H

Model Element Change Candidate discipline:

- G1 through G4.2c require retrospective examination.
- Beginning with G4.2d, candidates shall be recorded continuously.
- Candidate scope includes requirements, constraints, functions, Logical
  Components, relationships, allocations and possible Subsystem Architecture.
- Candidates are not accepted CATIA model changes.
- CATIA remains the authoritative engineering model.
- Phase N shall use the reviewed candidate inventory instead of relying on
  complete reverse engineering of Phases G through L.

Development-plan status:

```text
Architektur
[x] Approved-Input-Granularität / Identität
[x] P4/P9-Quellen + Review Targets
[x] Fingerprints, Lifecycle, Phase-H-Vertrag

Promotion
[x] Decision-/Fingerprint-Bindung
```

The complete Approved Input domain, promotion lifecycle, UI and end-to-end
acceptance remain open.

---

## 2026-08-03 — Phase G G1/G2 Completion and G3 Transition

Versions after this update:

- Architecture Version: 1.3
- Knowledge Base Version: 1.7
- Implementation Version: 0.9
- Roadmap Version: 1.7

Verified implementation:

- Repository: `mz-commits-ai4mbse/SysMLv2-Generator`
- Branch: `main`
- Verified implementation commit:
  `c61841789ed08b383e4cfc244d31f559125e6edb`
- Focused G2 test suite: 398 passed
- Complete automated test suite: 4206 passed
- Remote synchronization: `HEAD == origin/main`

G1 completion:

- ADR-016 was accepted.
- The Human Review Workspace and Approved Input authority chain was defined.
- Approved Input granularity and identity were defined.
- Eligible P4/P9 evidence and Review Target boundaries were defined.
- Fingerprint binding and lifecycle architecture were defined.
- The stable Approved Input boundary for Phase H was defined.
- G1 is complete.

G2 completion:

- Review Workspace error and validation contracts were implemented.
- RVD, RVV, RVR, RIT and SRA identities were implemented.
- Immutable Review Workspace domain types were implemented.
- Strict document, version, item, revision and action manifests were
  implemented.
- Deterministic serialization and fingerprints were implemented.
- Project-local paths and persistence were implemented.
- Atomic initial workspace creation was implemented.
- Append-only revisions were implemented.
- Immutable Scoped Review Actions and exact item-fingerprint materialization
  were implemented.
- Project-local identifier allocation without reuse was implemented.
- Deterministic scanning, recovery diagnostics and unsafe-path protection were
  implemented.
- G2 is complete.

Development-plan status:

```text
Architektur
[x] Approved-Input-Granularität / Identität
[x] P4/P9-Quellen + Review Targets
[x] Fingerprints, Lifecycle, Phase-H-Vertrag

Domain
[ ] IDs, Typen, Manifest
[ ] Repository + Read Contract
[ ] Validation + Fehlerhierarchie

Promotion
[ ] Eligibility aus P4/P9
[ ] Decision-/Fingerprint-Bindung
[ ] promote / invalidate / revoke / supersede

Abschluss
[ ] Vollständige Traceability
[ ] Review-/Promotion-UI
[ ] Tests + Manual Acceptance
```

The Review Workspace portions of the Domain items are implemented, but the
checkboxes remain open until the Approved Input domain and promotion lifecycle
are complete.

Immediate next activity:

```text
G3 — P4/P9 Evidence Adapters and Review Item Construction
→ tests
→ review
→ G3 completion decision
```

Phase G remains active.

No Approved Input is created by G2.


---

## 2026-07-31 — Post-Phase-P Reconciliation Completion and Prototype Acceleration

Versions after this update:

- Architecture Version: 1.2
- Knowledge Base Version: 1.6
- Implementation Version: 0.8
- Roadmap Version: 1.6

Verified implementation baseline remains unchanged:

- Repository: `mz-commits-ai4mbse/SysMLv2-Generator`
- Branch: `main`
- Verified implementation commit: `26acace4d7ba2849b33c5e0dacedf838f83c7705`
- Complete automated test suite: 3808 passed
- Manual P9 acceptance audit: PASS

The implementation version remains `0.8` because this update records completed
presentation, modeling, reconciliation and roadmap decisions rather than new
committed runtime implementation.

Post-Phase-P Reconciliation Gate completion:

- The Phase F/P prototype was presented.
- The verified prototype baseline was preserved.
- Implemented Phase F/P capabilities and accepted architecture decisions were
  inventoried.
- The first Architecture-to-Requirements Reconciliation against the
  authoritative CATIA SysML v2 model was completed.
- Accepted CATIA System Requirements, System Design Constraints, System
  Functions and Logical Architecture were established.
- The Feature and Requirement Coverage Matrix was completed.
- Phase G — Approved Input Promotion was explicitly selected as the next
  implementation phase.
- The Post-Phase-P Reconciliation Gate is closed.

Accepted CATIA System-level baseline:

- 39 Stakeholder Requirements
- 102 System Requirements
- 30 active System Design Constraints
- 12 System Functions
- 8 Logical Components
- System Function interaction network
- Logical interconnection view
- 39 of 39 Stakeholder Requirements covered through System Functions

The accepted derivation chain is:

```text
Stakeholder Requirements
→ System Requirements
→ System Functions
→ Logical Components
→ implementation evidence
```

The System Requirement topic packages are navigation and documentation
structures.

They are not:

- Logical Component allocations
- subsystem boundaries
- implementation proof
- a replacement for the accepted derivation chain

System Physical Architecture and all Subsystem R/F/L/P levels remain deferred.

Phase N scope brought forward:

The following parts of the previously planned Phase N scope were completed
during the Post-Phase-P Reconciliation Gate:

- first Architecture-to-Requirements Reconciliation
- accepted System Requirement update
- accepted System Function modeling
- accepted System Logical Architecture modeling
- initial Feature and Requirement Coverage baseline

Phase N remains planned and retains:

- migration of the temporary SYSIDE shadow model
- final reconciliation after Phases G through L
- removal of duplicated maintained model authority
- final CATIA synchronization
- confirmation that CATIA is the only maintained engineering model

Executable prototype target:

- Target date: 2026-08-14
- Critical path: Phase G through Phase L

Accepted end-to-end path:

```text
Source
→ Processing Run
→ Human Review
→ Approved Input
→ Model Candidates
→ Internal Engineering Model
→ SysML v2 Generation
→ Validation
→ Versioned Output Package
```

The accepted implementation order is:

```text
Phase G — Approved Input Promotion
→ Phase H — Model Candidate Layer
→ Phase I — Model Generation Agent
→ Phase J — SysML v2 Code Generator
→ Phase K — Validation Layer
→ Phase L — Output Writer
```

Phase G activation:

- Phase G is now the active phase.
- The Post-Phase-P Reconciliation Gate no longer blocks implementation.
- Phase G architecture still requires explicit acceptance before implementation.
- Phase G shall create the authoritative bridge from reviewed processing
  evidence to Approved Input.
- Unreviewed P9 artifacts remain processing evidence and cannot become Approved
  Input without an exact Human Review Decision and valid fingerprints.
- Phase G shall not generate model candidates or SysML v2.

Accepted model-relationship feedback for Phase H:

- Model relationships shall be generated and reviewed as explicit engineering
  candidates.
- Relationship types whose meanings are often used inconsistently or
  near-synonymously shall remain distinguishable.
- Relevant concepts include dependency, allocation, flow, refinement-related
  relationships, derivation-related relationships and framework-specific
  relationships.
- Relationship candidates shall include priority, prioritization rationale,
  semantic intent, supporting evidence and comparability impact.
- Automated prioritization remains advisory.
- Human Review shall authorize the accepted relationship choice.
- A versioned Model Structure and Comparability Profile shall support
  consistent structures across related products, product variants,
  independently generated models and repeated generation runs.

Accepted post-prototype portability evaluation:

- Phase R — Task Profile Portability Evaluation was added after Phase Q.
- Phase R shall test whether the reusable Turing Generator core can be adapted
  quickly by replacing a bounded set of task-specific JSON, Markdown, recipe,
  agent, validation and output-contract artifacts.
- The alternate task is Requirements Quality and Completeness Analysis.
- The task shall assess formulation rules, completeness, atomicity, ambiguity,
  contradictions, missing information and proposed changes or additions.
- Proposed requirement changes remain subject to Human Review.
- A Task Profile Replacement Manifest shall distinguish unchanged core,
  adapted artifacts, replaced artifacts, dependencies, validation and code
  changes.
- The portability claim shall be evaluated using measured implementation
  evidence.

Accepted low-priority project recommendation feature:

- Phase S — Project Affinity Recommendation was added after Phase R.
- Phase S is explicitly low priority.
- Before persistent Source registration, the system may recommend existing
  Projects that appear suitable for newly selected data.
- Recommendations remain advisory.
- The user confirms or overrides the recommendation.
- No automatic Project assignment is permitted.
- No permanent unassigned Source pool is introduced.
- Every persisted Source remains assigned to exactly one Project.

Working-rule updates:

- Approved Input authority and promotion boundaries were added.
- Relationship semantics and model-comparability rules were added.
- Task Profile Portability rules were added.
- Project Affinity Recommendation boundaries were added.
- The 2026-08-14 prototype delivery target was recorded.
- Schedule pressure shall not weaken Human Review, traceability, project
  isolation, deterministic validation, publication gates or model consistency.

Immediate next activity:

```text
Phase G architecture discussion
→ explicit project-owner acceptance
→ Phase G ADR
→ implementation
→ tests
→ manual review
→ completion decision
```

No Phase H implementation begins before Phase G provides a stable Approved
Input contract.

---

## 2026-07-28 — Post-Phase-P Reconciliation Gate Correction

Versions after this correction:

- Architecture Version: 1.1
- Knowledge Base Version: 1.5
- Implementation Version: 0.8
- Roadmap Version: 1.5

Implementation baseline remains unchanged:

- Repository: `mz-commits-ai4mbse/SysMLv2-Generator`
- Branch: `main`
- Verified implementation commit: `26acace4d7ba2849b33c5e0dacedf838f83c7705`
- Complete automated test suite: 3808 passed
- Manual P9 acceptance audit: PASS

Correction:

- The SSOT update committed at `40f521c375750ae2d25c86f4b225441bab7c59b3` correctly recorded
  Phase P completion but incorrectly identified Phase G as the immediate next
  activity.
- The previously agreed cut after Phase P is restored.
- The immediate work package is the Post-Phase-P Reconciliation Gate.
- Phase G remains planned and is blocked until the gate is complete and the
  project owner explicitly selects the next implementation phase.

Immediate gate scope:

1. preserve and present the Phase F/P prototype baseline
2. inventory implemented capabilities and accepted architecture decisions
3. reconcile them with the authoritative CATIA requirements, use cases and
   model elements
4. identify missing, outdated, incomplete and conflicting requirements
5. review and apply accepted CATIA changes
6. create the Feature and Requirement Coverage Matrix
7. select the next implementation phase explicitly

Feature and Requirement Coverage Matrix:

- Capability / Feature
- CATIA Requirement ID
- Implementation Status
- Test / Evidence
- ADR / Architecture Decision
- Presentation Readiness
- Remaining Roadmap / Open Work

Accepted rules:

- implementation is evidence, not automatic normative authority
- CATIA remains authoritative
- no CATIA requirement is created or changed without explicit Human Review
- the first Architecture-to-Requirements Reconciliation pass occurs now
- Phase N retains Shadow-model Migration and final whole-system reconciliation
- no Phase G implementation begins before gate closure

---

## 2026-07-27 — Phase P Completion and Project-bound Ingestion Integration

Versions after this update:

- Architecture Version: 1.1
- Knowledge Base Version: 1.4
- Implementation Version: 0.8
- Roadmap Version: 1.4

Verified implementation baseline:

- Repository: `mz-commits-ai4mbse/SysMLv2-Generator`
- Branch: `main`
- Commit: `26acace4d7ba2849b33c5e0dacedf838f83c7705`
- Complete automated test suite: 3808 passed
- Manual P9 acceptance audit: PASS
- Remote synchronization: `HEAD == origin/main`

Current Phase P status:

- P1 — Framework Template Definition: Completed
- P2 — Project Manifest and Workspace Structure: Completed
- P3 — Source Registry and mandatory Project Assignment: Completed
- P4 — Framework-mapped heterogeneous Information Units: Completed
- P5 — Processing State and Artifact Organization: Completed
- P6 — Preliminary Coverage and Potential Model Support: Completed
- P7 — Project Dashboard: Completed
- P8 — Tests and Integration Readiness Review: Completed
- P9 — Project-bound Agentic Ingestion Integration: Completed

Completed P5 implementation:

- ADR-012 documented Processing State and Artifact Organization.
- Processing Run, Event and Decision Manifests were implemented.
- Processing Run state is reconstructed from immutable event history.
- Run-owned work and artifact organization was implemented.
- Retry, supersession, invalidation and recovery diagnostics were implemented.
- Source-level and Project-level Processing aggregation was implemented.
- P5 completion was verified at
  `9a9ef8bd7c08c354c638d4b0e072e308e7c02516`.

Completed P6 implementation:

- ADR-013 documented Preliminary Coverage and Potential Model Support.
- Deterministic Preliminary Coverage assessment was implemented.
- Potential support assessment and support-profile handling were implemented.
- Approved Generation Readiness remains unavailable during Phase P.
- P6 completion was verified at
  `f921b216d66ee359dea7cf116cfea03acb1e3510`.

Completed P7 implementation:

- ADR-014 documented the Project Dashboard architecture.
- The dashboard provides Overview, Sources & Processing, Coverage & Support,
  Attention & Review and Traceability views.
- Project selection and constrained Project Workspace creation were implemented.
- Evidence navigation and safe document preview were implemented.
- The dashboard boundary remains read-only except for constrained project
  creation.
- P7 implementation was verified at
  `d8a3bc9bb55a4b7ab0fa6e999b74b8541bf224b6`.
- Project-creation fixes were completed at `fe0fd24`.

Completed P8 review:

- P8 confirmed P1–P7 integration readiness.
- P8 established that project-bound ingestion required a separate P9 boundary.
- P8 did not introduce a parallel project or processing architecture.

Completed P9 implementation:

- ADR-015 documented Project-bound Agentic Ingestion Integration.
- The common Turing Generator application shell was implemented.
- Project-bound Source upload and registration were implemented.
- Text, Markdown, JSON, CSV, TSV and PDF text-layer Source containers are
  supported.
- Registered Sources are projected before Phase F execution.
- A P5 Processing Run and Attempt are created for the selected Source.
- Phase F executes inside a project-bound P5 work directory.
- Work outputs are validated before publication.
- Published artifacts receive immutable `ProcessingArtifactReference` values.
- `artifact_published` and `review_requested` events are appended.
- Successful project-bound ingestion ends in `awaiting_review`.
- The Execution UI and Dashboard return workflow were implemented.
- The Dashboard now highlights the Phase-F Ingestion Review Report as the
  primary review target.
- P9 implementation was completed at
  `26acace4d7ba2849b33c5e0dacedf838f83c7705`.

Manual P9 acceptance evidence:

- Demo project: `458990`
- Negative case: `SRC-000001` / `RUN-000001`
  - state: `failed`
  - reason: `source_normalization_failed`
  - events: 3
  - artifacts: 0
- Successful dry-run case: `SRC-000002` / `RUN-000002`
  - state: `awaiting_review`
  - events: 4
  - artifacts: 15
  - artifact counts: 4 agent outputs, 8 consensus reports, 1 review report,
    2 run summaries
- All published artifact fingerprints were verified.
- No API-key fields were persisted.
- A failed Source does not block a different Source in the same Project.

Accepted boundaries after Phase P:

- P9 `awaiting_review` is not Approved Input.
- Published run-owned artifacts are Processing evidence, not approved
  engineering knowledge.
- Consensus, confidence and variance remain review evidence only.
- Preliminary Coverage remains separate from Approved Generation Readiness.
- Phase G is responsible for Approved Input Promotion.
- Model candidates, model generation and SysML v2 code generation remain later
  phases.

Roadmap changes:

- Phase P is complete after this SSOT update is committed and pushed.
- Phase G — Approved Input Promotion is the next active phase.
- Phase Q now explicitly includes a thesis-only Development Plan documenting
  the lettered development phases. This plan remains separate from the feature
  overview and is not intended for the intermediate presentation.

Next implementation step:

- Begin Phase G architecture discussion.
- Define Approved Input identity and storage.
- Define eligible promotion sources from P4 and P9.
- Define required Human Review Decision target types.
- Define fingerprint binding, promotion, revocation, invalidation and
  supersession behavior.
- Do not begin Phase G implementation before the architecture is explicitly
  accepted.

---
## 2026-07-24 — P4 Semantic Architecture Completion

Versions after this update:

- Architecture Version: 1.0
- Knowledge Base Version: 1.3
- Implementation Version: 0.7
- Roadmap Version: 1.3

Verified implementation baseline:

- Repository: `mz-commits-ai4mbse/SysMLv2-Generator`
- Branch: `main`
- Commit: `0c8ba428e7e6469e410b541c114d7a5a9474321c`
- Complete automated test suite: 2594 passed
- Own-source diff validation: passed
- Pinned external ontology integrity validation: passed
- Remote synchronization: `HEAD == origin/main`

Current Phase P status:

- P1 — Framework Template Definition: Completed
- P2 — Project Manifest and Workspace Structure: Completed
- P3 — Source Registry and mandatory Project Assignment: Completed
- P4 — Framework-mapped heterogeneous Information Units: Completed
- P5 — Processing State and Artifact Organization: Next
- P6–P8: Planned

Completed P2 implementation:

- The Project Workspace architecture was documented in ADR-005.
- Six-digit numeric project identities were implemented.
- Project identity and project display name were separated.
- Project display names must remain unique.
- Project Manifest validation and persistence were implemented.
- Project creation, loading, scanning and safe reopening were implemented.
- Project isolation and symlink protection were implemented.

Completed P3 implementation:

- The textual source-processing boundary was documented in ADR-009.
- The Project Source Registry architecture was documented in ADR-010.
- Every source is assigned to exactly one project.
- Project identity and source identity remain separate.
- Immutable Source Manifests were implemented.
- Source content is hash-bound.
- `engineering_source` and `context_only` roles were implemented.
- Duplicate source content is rejected.
- Safe project-local source persistence and deterministic scans were
  implemented.

Completed P4 implementation:

- The semantic Information Unit and ontology boundary was documented in
  ADR-011.
- Deterministic source projections were implemented.
- Text, Markdown, JSON, CSV, TSV and PDF text-layer adapters were implemented.
- Source-projection locators, manifests and repositories were implemented.
- BFO 2020 and IOF Core 202602 snapshots were pinned and integrity-checked.
- License and provenance information was stored with the ontology snapshots.
- A versioned ontology registry was implemented.
- A deterministic derived index containing 236 reference concepts was
  implemented.
- The Turing Core Vocabulary was implemented.
- Project Glossary candidates and terminology decisions were implemented.
- Immutable, source-traceable Information Units were implemented.
- Semantic extraction candidate contracts were implemented.
- Multi-agent semantic consensus and variance analysis were implemented.
- Terminology-mapping candidates and reference validation were implemented.
- Framework-assignment candidates and reference validation were implemented.
- Immutable Human Review Decisions were implemented.
- Exact target-content and validation-fingerprint publication gates were
  implemented.
- Deterministic token budgeting was implemented.
- Required-context overflow blocks LLM execution.
- Required prompt context cannot be silently truncated.

Accepted textual processing boundary:

- The MVP semantic-processing boundary is textual information.
- Native text and deterministic text projections are supported.
- PDF support is limited to extractable text layers.
- OCR is outside the MVP.
- Image-only PDF interpretation is outside the MVP.
- Technical-drawing interpretation is outside the MVP.
- Unrestricted multimodal engineering extraction is outside the MVP.
- Text projection shall not perform semantic or ontology interpretation.

Accepted semantic authority:

- CATIA remains authoritative for project engineering knowledge.
- Accepted project terminology has authority within its project scope.
- The Turing Core Vocabulary provides the project semantic bridge.
- BFO and IOF remain external reference systems.
- External ontology mappings remain candidates until reviewed.
- External ontologies shall not override project engineering authority.
- Live ontology queries and automatic ontology updates are outside the MVP.
- Complete ontology snapshots shall not be loaded into prompts.

Accepted BFO and IOF role:

- BFO 2020 is the registered top-level ontology reference.
- IOF Core 202602 is the registered industrial ontology reference.
- BFO is stored under `external/ontologies/bfo/2020/`.
- IOF is stored under `external/ontologies/iof/202602/`.
- Reference-system selection, alternatives and justification shall be
  documented with literature and standards in Phase Q.

Accepted project-terminology rules:

- Project terminology is maintained through explicit glossary candidates and
  terminology decisions.
- Project glossary changes require Human Review.
- External reference systems do not automatically mutate project terminology.
- The same normalized term shall not silently represent multiple accepted
  meanings.

Accepted multi-agent and confidence rules:

- Agent personalities may provide independent semantic perspectives.
- Individual agent results remain traceable.
- Consensus, disagreement, run completeness and variance remain explicit.
- Confidence and variance are review evidence.
- High confidence is not publication authority.
- Unanimous consensus is not publication authority.
- Low variance is not publication authority.

Accepted Human Review rules:

- Every publication target requires an explicit Human Review Decision.
- Supported review targets include Information Unit publication, terminology
  mappings and framework assignments.
- Supported decisions are `confirm`, `reject` and `request_changes`.
- Quick confirmation is permitted only for eligible, reference-valid targets.
- Detailed review remains available when quick confirmation is offered.
- Invalid references cannot be confirmed.
- The latest exact decision for the current target-content and validation
  fingerprints controls the gate.
- No automatic publication path exists.

Accepted token-budget rules:

- Prompts use deterministic relevant context slices.
- The complete codebase shall not be loaded automatically.
- Complete ontology snapshots shall not be loaded automatically.
- System instructions, output capacity and safety margin are reserved.
- Required context is included completely or the LLM call is blocked.
- Required context shall never be silently truncated.
- Optional context selection follows an explicit deterministic priority.
- Selected and omitted references remain auditable.

Accepted Phase N roadmap change:

- Phase N now includes Architecture-to-Requirements Reconciliation.
- Every accepted architecture decision shall be mapped to authoritative model
  coverage.
- Missing, outdated and conflicting requirements shall be identified.
- Requirement and model-change candidates shall remain traceable to their
  decision and implementation evidence.
- Stakeholder needs, requirements, design constraints and implementation
  details shall remain distinguishable.
- Implementation is evidence and shall not automatically create normative
  requirements.
- CATIA changes require explicit Human Review.

Accepted Phase Q roadmap change:

- Phase Q — Thesis Architecture Documentation was added after Phase N.
- Phase Q shall document every architecture decision from Phases A–P.
- Phase Q shall also document every later accepted architecture decision.
- Decision context, alternatives, rationale and consequences shall be
  documented.
- Requirement and implementation traceability shall be documented.
- Literature, standards and ontology sources shall support relevant claims.
- BFO and IOF selection and use shall be explained and justified.

Accepted workflow clarifications:

- A complete SSOT UPDATE remains normally scheduled after a major phase.
- This update is an explicitly requested intermediate synchronization after
  P4.
- The intermediate update is justified by the substantial semantic
  architecture baseline and need for a reliable fresh-chat handover.
- The next regular SSOT UPDATE remains due after P8 and completion of Phase P.
- Consecutive work steps modifying the same file should be grouped when they
  can be safely implemented and reviewed together.
- Independently testable intermediate contracts remain permitted.

Next implementation step:

- Begin P5 architecture discussion.
- Define canonical processing states and allowed transitions.
- Define project-level state aggregation.
- Define artifact organization without duplicating existing manifest
  authority.
- Define failure, retry, supersession and reopening behavior.
- Preserve project, source, projection, Information Unit and review
  traceability.
- Do not pull Phase G Approved Input Promotion into P5.
- Do not begin P5 implementation before the architecture is explicitly
  accepted.

---

## 2026-07-21 — P1 Framework Template Completion

Versions after this update:

- Architecture Version: 0.9
- Knowledge Base Version: 1.2
- Implementation Version: 0.6
- Roadmap Version: 1.2

Verified implementation baseline:

- Repository: `mz-commits-ai4mbse/SysMLv2-Generator`
- Branch: `main`
- Commit: `82b5cbbe9bedac77a4b02928a596ea8fbdacc873`
- P1 framework tests: 9 passed
- Complete automated test suite: 18 passed
- Diff validation: passed

Completed implementation:

- P1 — Framework Template Definition is complete.
- The Apollo 11 SysML v2 repository was reviewed for transferable
  structuring, naming and hierarchy patterns.
- Accepted and rejected Apollo 11 patterns are documented in
  `context/examples/apollo11_structure_reference.md`.
- The versioned framework template
  `context/frameworks/turing_rflp_framework.json` was implemented.
- The template contains 3 framework levels and 12 explicit mapping targets.
- Stable framework node identifiers and mapping keys were defined.
- Zero-to-many framework assignment is supported.
- Unknown framework targets are rejected.
- `context_only` sources are excluded from framework mapping.
- Preliminary coverage and approved generation readiness are represented as
  separate concepts.
- Approved readiness remains unavailable during Phase P.
- A deterministic framework-template validator was implemented in
  `modules/framework/template.py`.
- Framework-template documentation and automated tests were added.

Accepted reference decisions:

- Apollo 11 remains a non-normative structural reference.
- The Apollo CoSMA framework was not adopted.
- The Apollo package hierarchy was not adopted.
- Apollo engineering content and identifiers were not transferred.
- The accepted Stakeholder/System/Subsystem framework remains unchanged.
- Only explicitly reviewed structural patterns may influence the Turing
  framework.

Accepted repository collaboration workflow:

- GitHub repositories and repository links are used passively by AI
  assistants.
- AI assistants shall not directly modify GitHub repository content.
- AI assistants shall not commit, push, create remote branches or open pull
  requests.
- Repository changes are applied, reviewed, tested, staged, committed and
  pushed locally by the project owner.
- AI assistants act as implementation guides and identify affected files by
  repository-relative path before proposing changes.
- Changes are normally presented one file at a time.
- Mixed working trees require explicit file-by-file staging.

Accepted SSOT update cadence:

- A complete SSOT UPDATE is normally performed after completion of a major
  roadmap phase.
- Internal work steps within a phase do not require separate full SSOT updates.
- P1 through P8 are tracked through committed implementation changes, automated
  test evidence and reviewed decisions.
- Accepted architecture decisions are documented and committed individually as
  ADRs before implementation depends on them.
- Committing an accepted ADR does not trigger a complete SSOT UPDATE.
- The current synchronization is an explicitly requested P1 alignment update.
- The next regular full SSOT UPDATE shall be performed after P8 and completion
  of Phase P.
- An earlier SSOT UPDATE requires an explicit project-owner request or a
  critical handover need.

Current Phase P status:

- P1 — Framework Template Definition: Completed
- P2 — Project Manifest and Workspace Structure: Next
- P3–P8: Planned

Next implementation step:

- Begin the P2 architecture discussion.
- Define project identity, Project Manifest, Workspace structure, persistence,
  reopening and project-isolation boundaries.
- Record the explicitly accepted architecture in ADR-005 before P2
  implementation begins.

Deferred architecture decision:

- The concrete Project Workspace persistence layout remains unaccepted.
- Architecture Version remains 0.9 until ADR-005 has been discussed and
  explicitly accepted.

---

## 2026-07-21 — Phase F Completion and Phase P Scope Definition

Versions after this update:

- Architecture Version: 0.9
- Knowledge Base Version: 1.1
- Implementation Version: 0.5
- Roadmap Version: 1.1

Verified implementation baseline:

- Repository: `mz-commits-ai4mbse/SysMLv2-Generator`
- Branch: `main`
- Commit: `adce9ec65ca3e36b89686b55d397a34dd382fdb1`
- Test result: 9 passed

Accepted changes:

- Phase F is complete.
- The deterministic engineering review report and the Agentic Ingestion UI
  were completed and verified.
- Phase P is the active roadmap phase; its scope is defined and implementation
  has not started.
- Every ingested file must be assigned to a project.
- One source may yield multiple heterogeneous, traceable information units.
- The project dashboard will show project metadata, source inventory,
  framework coverage and preliminary model support.
- Framework coverage and preliminary support may include unreviewed engineering
  information only when clearly marked as preliminary.
- Generation readiness and later model generation may use only human-approved
  engineering information.
- Project-wide and selected SubModel generation controls may be displayed
  disabled in Phase P; execution remains assigned to Phases H–J.
- Context-only project documents may explain system context but shall not
  satisfy coverage, readiness or generation evidence.
- The initial framework contains Stakeholder, System and Subsystem levels.
  Additional framework templates are post-MVP scope.

Next implementation step:

- P1 — Framework Template Definition

Deferred architecture decision:

- The concrete Project Workspace persistence layout will be decided during
  P1/P2 and recorded in ADR-005 before implementation depends on it.
