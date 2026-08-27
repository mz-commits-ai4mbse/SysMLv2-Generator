# Turing Generator — Gate 3 Validation / Handover SSOT

Date: 2026-08-27
Active branch: `feature/processing-semantic-normalization`
Implementation target: `v0.3.0`


<!-- GATE3-CLOSEOUT-2026-08-27 -->

# 0. Gate 3 Validation Closeout — authoritative end state

Status: **COMPLETED for the Project `000116` Lead-Source single-source validation path**

This section is the authoritative continuation point after completion of the live
Gate-3 validation on 2026-08-27.

Where later sections of this handover still describe an intermediate state
(for example MQR `2 / 11`, OBS-033 under live retest, missing SYSIDE validation,
or publication as a future action), this closeout section supersedes those
instructions while preserving them as historical execution evidence.

The required execution order is now:

1. Gate-3 Project `000116` validation — **completed**
2. Professor presentation using the existing presentation plan — **next**
3. Safe Demo preparation using the agreed "Kochshow" strategy — **after presentation**

No restart or regeneration of Project `000116` is required.

---

## 0.1 Final repository / verification state

Active branch:

`feature/processing-semantic-normalization`

Implementation target:

`v0.3.0`

Latest complete local regression after all Gate-3 corrective work:

`6100 passed in 17.87s`

Latest focused Target-Model Formulation regression:

`20 passed`

`git diff --check` produced no findings in the final verification runs.

The final validation was performed against the real application workflow and not
only against unit/integration tests.

---

## 0.2 Project `000116` — final Gate-3 status

Lead Source:

`SRC-000002 / 01_product_overview.md`

The complete governed path was executed successfully through:

Engineering Source
→ Processing
→ Human Engineering Review
→ Review Finalization
→ Approved Input
→ Model Placement
→ Model Assembly Review
→ Base Internal Engineering Model
→ Target-Model Formulation
→ Human Model Quality Review
→ Human-authorized successor Internal Engineering Model
→ deterministic SysML v2 generation
→ authority-backed external SYSIDE validation
→ Final Model Review
→ Human publication approval
→ immutable Published Output

This validates the single-source Lead-Source path.

It does **not** establish a true Multi-Source Processing claim.
`BLK-002` remains authoritative for that limitation.

---

## 0.3 Base Internal Engineering Model

Base IEM:

`IEM-000001`

Contents:

- 11 elements
- 2 relationships

Fingerprint:

`71050fc9bc834b7520e76c4d7d7f18593f8e5c32d6241267ca3e34af6ff4df47`

The base model remained immutable throughout downstream corrective work.

---

## 0.4 Human Model Quality Review

Review:

`MQR-000001`

Final state:

`11 / 11 elements reviewed`

A malformed earlier Remote Expert override was corrected through an immutable
Human decision revision rather than by mutating persisted history.

Corrective decision:

`MQD-000017`

It supersedes:

`MQD-000002`

Approved Remote Expert description:

`Person who joins from a separate client application and can observe the live microscope image, with temporary control possible when permitted.`

The final Human Model Quality Authority is:

`MQA-000002`

Fingerprint:

`5d229fd98380cc44916541231d8344701bb289190ca9be61e627357a5717fb97`

---

## 0.5 Relationship / Target-Model compatibility finding

The first corrected successor exposed a genuine Phase-J generation guard:

`RELATIONSHIP_ENDPOINT_CONSTRUCT_MISMATCH`

Affected relationship:

`IMR-000001`

Engineering meaning:

Remote Expert → Client Application dependency

The issue was not that the engineering relationship itself was invalid.

The Target-Model Formulation changed the effective SysML representation of the
Remote Expert to `TN_003`, while the already existing dependency relationship
was not re-evaluated against the Phase-J relationship endpoint constraints.

Phase J correctly blocked generation rather than silently emitting unsupported
SysML.

The correction was implemented generically:

- determine the effective post-formulation construct for relationship endpoints;
- re-evaluate already-supported relationships against the actual Phase-J
  endpoint construct constraints;
- leave compatible relationships untouched;
- reopen only relationships whose effective endpoints become incompatible;
- require explicit Human Target-Model authority;
- preserve the engineering relationship even when no supported formal SysML
  representation is currently authorized;
- do not weaken the Phase-J generation guard;
- do not add project-specific aliases or Project `000116` special cases.

The Phase-J source endpoint whitelist was **not** broadened merely to make the
example pass.

---

## 0.6 Immutable Target-Model Formulation revision

Original formulation history remains preserved:

`TFR-000001 / TFA-000001`

A new explicit immutable revision was created:

`TFR-000002`

The revised review contained exactly three affected subjects:

- `IME-000001` → materialize formally as `TN_003`
- `IME-000002` → materialize formally as `TN_003`
- `IMR-000001` → intentionally not materialized

Final formulation authority:

`TFA-000002`

The unaffected compatible relationship was not reopened.

Repository behavior was extended to support immutable Target-Model review
revisions for the same exact source IEM while retaining all prior review history.

---

## 0.7 Final approved successor Internal Engineering Model

Approved successor:

`IEM-000003`

Contents:

- 11 elements
- 1 formally materialized relationship

Fingerprint:

`f86d753d4f1bf69f2f69158bd326313f3bcbea70762e28fadc11879bcad2b7ad`

Exact semantic authority binding:

- source: `IEM-000001`
- Target-Model authority: `TFA-000002`
- Model Quality authority: `MQA-000002`
- intentionally omitted relationship: `IMR-000001`

The omission is explicit and auditable.
The engineering information was not deleted.

The remaining formally materialized relationship is the compatible dependency
between temporary microscope control and operator permission.

---

## 0.8 Deterministic SysML v2 generation

SysML generation from `IEM-000003` completed successfully.

Generated artifact fingerprint:

`7b5babbe048f941d9875a345e34a03e1c249061a93e03ade3c9dcfb971f4ddb1`

Authority-backed traceability entries:

`12`

This corresponds to:

- 11 generated model elements
- 1 generated relationship

`IMR-000001` is intentionally absent from formal SysML generation and remains
traceable through Human Target-Model authority.

The original `RELATIONSHIP_ENDPOINT_CONSTRUCT_MISMATCH` no longer occurs.

---

## 0.9 External SYSIDE validation

The first post-generation external validation attempt was incomplete because the
Streamlit process could not resolve the bundled SYSIDE Modeler CLI from its
environment.

This was an infrastructure/path issue, not a SysML conformance failure.

Bundled validator used for the successful run:

`SYSIDE Modeler CLI · syside 0.10.3`

Successful external validation:

- execution: completed
- SYSIDE: PASS
- diagnostics: 0
- exit code: 0
- validation status: VALID
- publication gate: PASSED

Validation fingerprint:

`0e8998e6fe2d4b717cbee6464cdca1b060ad21601dd92389706240b38387ea67`

The application was corrected so a persisted historical incomplete validation
does not need to be deleted or overwritten.

The actual Final Model Review UI can now:

1. run the currently available SYSIDE validator as a read-only preview;
2. preserve the historical validation result;
3. compare the current validation fingerprint with persisted review evidence;
4. explicitly create a new immutable Final Model Review revision when the
   current result is VALID / PASSED.

No historical validation evidence is mutated.

---

## 0.10 Final Model Review and Human release authority

Final Model Review:

`FMR-000001`

Successful validation-bound revision:

`FRV-000002`

Human publication decision:

`FRD-000001`

The final review state reached:

`ready_for_approval`

with:

- validation findings: 0
- blocking findings: 0
- SYSIDE validation: PASSED

Human publication approval was explicitly recorded before publication.

The previously incomplete Final Model Review / validation history remains
preserved.

---

## 0.11 Published Output

Published package:

`OUT-000001`

Published:

`2026-08-27T20:51:18Z`

Publication state:

`Published`

Source IEM:

`IEM-000003`

Source generated-artifact fingerprint:

`7b5babbe048f941d9875a345e34a03e1c249061a93e03ade3c9dcfb971f4ddb1`

Validation fingerprint:

`0e8998e6fe2d4b717cbee6464cdca1b060ad21601dd92389706240b38387ea67`

Final Model Review:

`FMR-000001`

Final review revision:

`FRV-000002`

Final Human review decision:

`FRD-000001`

Publication profile:

`TURING_SYSML_V2_OUTPUT v1.0.0`

Immutable package contents:

1. `generated_model.sysml`
2. `generation_summary.json`
3. `traceability.json`
4. `validation_report.md`
5. `validation_result.json`

The complete real Lead-Source workflow therefore reached controlled publication.

---

## 0.12 OBS-033 disposition

`OBS-033 — app Model Refinement integration`

Gate-3 disposition:

**CLOSED / PASS for the validated v0.3.0 scope**

Validated corrections include:

- dedicated Model Refinement application path;
- incomplete refinement no longer dereferences a missing successor model;
- Human Model Quality Review resumes persisted decisions without unnecessarily
  rerunning the LLM;
- Human-authorized refined successor materialization;
- dataclass authority normalization for SEM-015 materialization;
- immutable Target-Model Formulation revisions;
- current external SYSIDE validation retry from the actual guided-workflow
  Final Model Review;
- immutable Final Model Review revision creation after successful retry;
- successful real publication from the corrected path.

---

## 0.13 Generation-profile path ownership hardening

During final code review, Target-Model Formulation was found to load the Phase-J
generation profile through the process working directory.

This worked in the normal repository-root launch and in the live Gate-3 run but
was unnecessarily dependent on current working directory.

The live Target-Model Formulation service now resolves:

`context/sysml/turing_sysml_v2_generation_profile.json`

from its explicit `repo_root` and injects the loaded generation profile into the
proposal builder.

The proposal builder remains backwards-compatible for direct callers.

Test repositories were updated to include the Generation Profile as part of
their isolated repository fixture.

Final regression after this hardening:

`6100 passed`

---

## 0.14 Remaining open items

The following remain open and must not be reinterpreted as solved by this
single-source Gate-3 pass:

- `BLK-002` — Multi-Source Processing Artifact Identity / provenance blocker
- `SEM-011` — broader SysML target construct coverage
- `SEM-013` — shared placement ambiguity vs actual Persona variance
- `SEM-014` — explicit Human relationship representation selection / broader UI revalidation
- `SEM-015-F01` — broader dependency-aware selective regeneration remains deferred
- `OBS-032` — ambiguous naming of Model Assembly Review vs Final Model Review
- `OBS-DASH-001` — dashboard does not yet represent the full authoritative workflow state

The successfully corrected relationship-compatibility re-evaluation must not be
overstated as general dependency-aware regeneration.

---

## 0.15 Validation claim boundary

The validated claim is:

> The Turing Generator v0.3.0 prototype successfully executed one real
> single-source governed workflow from Engineering Source through Human review,
> approved model refinement, deterministic SysML v2 generation, external SYSIDE
> validation, Human release approval and immutable publication.

The validation does not establish:

- true Multi-Source Processing;
- complete SysML v2 semantic coverage;
- full production readiness;
- absence of all workflow UX findings.

Four separate Sources previously reached successful Processing, but this remains
independent single-source evidence until `BLK-002` is resolved and explicitly
revalidated.

---

## 0.16 Next active objective

Gate-3 validation on Project `000116` is complete.

The next active work item is the professor presentation.

Primary basis:

`collaboration/presentations/interim_presentation_plan.md`

Preserved presentation/demo checkpoint:

`collaboration/checkpoints/2026-08-19_presentation_wp12_demo_ssot.md`

Do not invent a new presentation structure from scratch.

After the presentation is prepared, continue with the Safe Demo using the agreed
"Kochshow" strategy.

---

## 0.17 Git / staging boundary

This closeout belongs to the accepted v0.3.0 implementation delta.

Stage intended:

- accepted Processing robustness implementation;
- semantic/classification alignment implementation;
- application and Human Review integration;
- Model Refinement / Target-Model Formulation corrections;
- Final Model Review validation retry/revision support;
- corresponding tests;
- accepted ADRs/contracts/evaluation documentation;
- this canonical checkpoint SSOT.

Do not stage:

- `data/projects/`
- `data/output/`
- runtime Team Runs
- generated ingestion reports
- caches / `__pycache__`
- `.DS_Store`
- diagnostic ZIPs
- helper patch scripts
- unrelated tracked runtime/report files

Do not use:

- `git add .`
- `git add -A`
- `git add --all`

---


## 1. Purpose

This checkpoint preserves the exact continuation point before moving to a fresh ChatGPT conversation.

Required execution order:

1. Continue and complete validation on Project `000116`.
2. Only after validation is stable, prepare the professor presentation using the existing collaboration presentation plan as the basis.
3. After the presentation, prepare the Safe Demo using the previously agreed "Kochshow" strategy.

Do not restart Project `000116`, discard persisted Human decisions, or regenerate upstream authority merely to simplify downstream testing.

---

# 2. Git / repository state

## Known repository anchors

Known-good Golden baseline:

- Golden baseline commit: `924bf27d2ee4ca07c1d04da2c777ce31b7632e97`
- Golden tag: `wp12-golden-e2e-2026-08-25`
- Golden baseline regression: `6046 passed`
- Golden single-source Project: `120412`

Later accepted documentation:

- commit `d183974c2cc9231a1b006eb8979fb5851f8b665b`
- message: `Document WP12 formative evaluation and post-golden triage`

Later accepted UX implementation:

- local commit `9f2ae07`
- message: `Improve processing feedback and preserve project selection`
- local `main` advanced to this commit.
- Last known `origin/main` remained at `d183974`; do not push unless explicitly approved.

Current working branch:

`feature/processing-semantic-normalization`

The branch contains substantial intended but currently uncommitted implementation work.

## Git rule

Do not use:

- `git add .`
- `git add -A`
- `git add --all`

Do not stage runtime data, caches, `.DS_Store`, diagnostic ZIPs, generated reports, patch helper scripts, or `data/projects/`.

Do not stage the unrelated tracked report:

`data/ingestion_reports/task_ingest_example_legacy_model_description_team_agentic_ingestion_report_dry_run.md`

---

# 3. Current intended uncommitted implementation scope

The authoritative exact live Git list is appended at the bottom of this SSOT by the local snapshot command. The following is the known intended scope from the implementation work in this conversation.

## Application / UI

- `app/turing_generator_app.py`
- `app/turing_generator_ui.py`
- `app/version.py`
- `app/human_subject_review_ui.py`
- `app/model_final_review_ui.py`
- `app/model_refinement_review_ui.py`

## Contracts / ADR / evaluation evidence

- `collaboration/contracts/r4c_persona_subject_interpretation_contract.md`
- `collaboration/contracts/r4c_subject_centric_human_review_contract.md`
- `collaboration/decisions/ADR-030-semantic-interpretation-and-controlled-classification-alignment.md`
- `collaboration/decisions/ADR-031-semantic-field-consistency-alignment.md`
- `collaboration/audits/processing_robustness_adjustment_evaluation_2026-08-26.md`

## Engineering Subject / processing robustness

- `modules/engineering_subjects/__init__.py`
- `modules/engineering_subjects/contract.py`
- `modules/engineering_subjects/discovery.py`
- `modules/engineering_subjects/errors.py`
- `modules/engineering_subjects/grounding.py`
- `modules/project_ingestion/service.py`
- `modules/llm/progress.py`

## Semantic interpretation / normalization

- `modules/evidence_interpretation/pipeline.py`
- `modules/subject_interpretation/pipeline.py`

Classification Alignment package:

- `modules/classification_alignment/__init__.py`
- `modules/classification_alignment/errors.py`
- `modules/classification_alignment/types.py`
- `modules/classification_alignment/contract.py`
- `modules/classification_alignment/prompt.py`
- `modules/classification_alignment/service.py`
- `modules/classification_alignment/serialization.py`

Semantic Consistency Alignment package:

- `modules/semantic_consistency_alignment/__init__.py`
- `modules/semantic_consistency_alignment/errors.py`
- `modules/semantic_consistency_alignment/types.py`
- `modules/semantic_consistency_alignment/contract.py`
- `modules/semantic_consistency_alignment/prompt.py`
- `modules/semantic_consistency_alignment/service.py`
- `modules/semantic_consistency_alignment/serialization.py`

## Downstream Model Refinement integration

- `modules/guided_workflow/write_service.py`

## Known intended tests

- `tests/test_engineering_subject_grounding_recovery.py`
- `tests/test_project_ingestion_subject_failure_classification.py`
- `tests/test_subject_discovery_raw_observability.py`
- `tests/test_engineering_subject_duplicate_consolidation.py`
- `tests/test_classification_alignment.py`
- `tests/test_semantic_consistency_alignment.py`
- `tests/test_shared_evidence_interpretation_pipeline.py`
- `tests/test_subject_interpretation_pipeline.py`
- `tests/test_turing_generator_ingestion_running_action.py`
- `tests/test_turing_generator_retry_ui.py`
- `tests/test_human_subject_review_decision_lifecycle.py`
- `tests/test_human_subject_review_ui.py`
- `tests/test_model_refinement_review_ui.py`

The local Git snapshot appended below is authoritative if it contains additional intended files from the same accepted work.

---

# 4. Implemented robustness / semantic changes on the current branch

## C1 — Generic Subject Grounding Recovery

Implemented:

- structured grounding violations;
- one bounded repair attempt for LLM-repairable grounding failures;
- source-span/token validation;
- context-only spans cannot establish positive mentions;
- system integrity failures remain separate;
- raw/source identity remains authoritative.

Supported grounding violations include:

- `unknown_source_span`
- `context_only_positive_mention`
- `unknown_token`
- `token_not_in_claimed_span`
- `reversed_token_range`

## C2 — Precise Processing Failure Boundaries

Implemented reason codes:

- `subject_discovery_grounding_failed`
- `subject_discovery_validation_failed`
- `subject_discovery_integrity_failed`
- `subject_discovery_execution_failed`
- `subject_interpretation_failed`
- `subject_consensus_failed`
- `subject_review_artifact_failed`

## C3 — Controlled Classification Alignment

Accepted flow:

Engineering Source
→ professional LLM interpretation
→ Controlled Classification Alignment
→ strict internal semantic contract
→ consensus / Human Engineering Review

Principles:

- LLM classification text is a semantic proposal, not authority.
- valid values pass unchanged;
- deterministic case/whitespace normalization where unique;
- OOV values receive at most one bounded contextual mapping call;
- unresolved `information_type` may fall back to `unclassified`;
- unresolved fields without a safe neutral value fail closed;
- raw output remains immutable;
- alignment provenance is persisted;
- no source-specific aliases;
- this is not downstream BFO/IOF/Turing Core ontology mapping.

## C3.3 — Semantic Field Consistency Alignment

Implemented for:

`epistemic_class + missing_evidence`

Allowed coupled states:

- `explicit` + `null`
- `interpretation` + `null`
- `assumption` + non-empty text

The mapper may change only the coupled pair. Structural failures remain fail-closed.

## Raw Subject Discovery observability

Persisted diagnostic responses:

- `raw_responses/initial.json`
- `raw_responses/grounding_correction.json`

These are diagnostic only and not engineering authority.

## Deterministic duplicate Subject consolidation

Compatible duplicates merge only when:

- `canonical_label.casefold()` agrees;
- `subject_form` agrees;
- `identity_status` agrees.

Mentions are unioned deterministically and exact duplicate mentions are removed.

Conflicting form/status still fails closed.

## Processing UI / version

- v0.3.0 UI/build labeling implemented.
- Processing status consolidated into a cleaner transient status line.
- Technical IDs remain available under Technical Details.
- Compilation phase is explicitly surfaced.
- Yellow previous-attempt warning remains.

## Gate 3C canonical Subject acceptance semantics

Canonical Subject acceptance no longer requires selecting a winning Agent proposal.

Human review authorizes the consolidated engineering result.

Consensus may prefill a value, but Human acceptance remains the authority.

The generic G6 proposal contract was not globally weakened.

---

# 5. Project 000116 — validation state

Project `000116` is the active v0.3.0 real validation project.

Successful Processing paths currently preserved:

- `SRC-000001` — `04_technical_architecture_notes.md`
- `SRC-000002` — `01_product_overview.md`
- `SRC-000003` — `02_user_workflow.md`
- `SRC-000004` — `03_system_requirements.md`

`SRC-000005` has no successful attempt and is outside the current validation set.

Important claim boundary:

Four separate real Source paths reaching successful Processing do **not** prove true Multi-Source Processing. `BLK-002` remains the blocker for a multi-source processing claim.

Lead E2E Source:

`SRC-000002 / 01_product_overview.md`

---

# 6. Lead Source Gate 3 status

## PASS — Human Engineering Review

19 canonical Subjects reviewed.

Accepted semantic Relationships: 9.

Explicit Human changes included:

- session: descriptive → definitional / definition
- client application: information type → logical element

## PASS — Review Finalization

- `RVD-000001`
- `RVV-000001`
- `RVR-000039`
- `HRD-000001`
- blocking findings: 0
- eligible: true

## PASS — Approved Input promotion

14 promotable Review Items → `AIN-000001 ... AIN-000014`

Open Questions / gaps were not promoted as formal model inputs.

## PASS — Model Placement

Final Human placement decisions:

- AIN1 capability → Reject placement
- AIN2 operator → Stakeholder
- AIN3 live view → Reject placement
- AIN4 remote expert → Stakeholder
- AIN5 session → Reject placement
- AIN6 workstation → Subsystem / Physical / Physical Component
- AIN7 client app → Subsystem / Logical / Logical Component
- AIN8 remote consultation → Stakeholder / Use Cases / Use Case
- AIN9 observe live image → System / Functional / Function
- AIN10 temporary control → System / Functional / Function
- AIN11 operator permits it → Stakeholder Requirement
- AIN12 operator responsible → Stakeholder Requirement
- AIN13 current controller awareness → Stakeholder Requirement
- AIN14 retain session information → System Requirement

Accepted placements: 11.

## PASS — Model Assembly / Assembly Review

Assembly:

- 11 elements
- 2 relationships

Human relationship resolutions:

- `remote expert --uses--> client application` → `dependency`
- `take temporary control --requires--> operator permits it` → `dependency`

Assembly Human decision:

`FAD-000001`

## PASS — Base Internal Model

Base model:

`IEM-000001`

- 11 elements
- 2 relationships
- fingerprint:
  `71050fc9bc834b7520e76c4d7d7f18593f8e5c32d6241267ca3e34af6ff4df47`

---

# 7. OBS-032 / OBS-033

## OBS-032 — accepted wording

`OBS-032 — Ambiguous naming of two distinct model review gates`

Current:

- pre-materialization assembly review is labeled `Final Model Review`
- post-generation/revalidation workspace is also labeled `Final Model Review`

Expected:

- pre-materialization gate: `Model Assembly Review`
- post-generation gate: `Final Model Review`

Disposition:

UX terminology cleanup after Gate-3 validation. No architecture change required.

## OBS-033 — current integration work

Observed defect:

After Base IEM materialization, the app previously exposed development terminology and allowed the UI path to proceed too directly toward SysML generation instead of presenting the already implemented Model Refinement / Human Model Quality Review workflow.

Desired app path:

Base Internal Model
→ Model Refinement
→ Target-Model Formulation where required
→ Human Model Quality Review
→ Human-authorized successor IEM
→ deterministic SysML v2 generation

OBS-033 integration patch added a dedicated Model Refinement UI and bridges the existing backend authority path into the application.

---

# 8. Model Refinement — current live state

## Target-Model Formulation

Completed:

- Review: `TFR-000001`
- Authority: `TFA-000001`
- 2 / 2 formulation decisions reviewed

The two formulation items are the two Stakeholder elements.

## Human Model Quality Review

Review:

`MQR-000001`

Current persisted review count observed in the app:

`2 / 11 elements reviewed`

Decisions observed:

### IME-000001 — Microscope Operator

Decision:

`MQD-000001`

Outcome:

Accepted

### IME-000002 — Remote Expert

Decision:

`MQD-000002`

Outcome:

Modified

Human reason recorded:

`can observe beschreibt eine Fähigkeit/Berechtigung, während to observe eher einen Zweck des Beitritts formuliert. Das ist zwar nah dran, aber unnötig stärker interpretiert.`

Do not reconstruct the final approved text from memory if it matters. Read the persisted MQD decision from Project `000116`.

Next undecided model-quality item:

`IME-000003 — Microscope Workstation`

Then continue through all remaining elements.

---

# 9. Current OBS-033 runtime/test defect — exact continuation point

After the first OBS-033 integration pass:

Focused integration tests:

`20 passed in 1.45s`

Full regression:

`6091 passed, 1 skipped in 16.49s`

`git diff --check`:

PASS

During the first live UI validation after that green suite, an additional integration bug was exposed:

When Model Quality Review was incomplete, the refinement renderer returned no successor model, but the old downstream SysML wrapper still dereferenced the returned value.

Observed runtime failure:

`AttributeError: 'NoneType' object has no attribute 'internal_engineering_model_id'`

Trace ended in:

`app/model_final_review_ui.py`
→ `_render_authority_backed_sysml`
→ `model.internal_engineering_model_id`

A guard has now been added in the current local code:

```python
if model is None:
    return
```

inside `_render_authority_backed_sysml`.

Current code also passes:

```python
generation_model = _render_sem015_successor_selection(...)
_render_authority_backed_sysml(..., model=generation_model, ...)
```

The newest focused test currently fails, but the failure is in the **test implementation**, not proof that the runtime guard is wrong:

```text
FAILED
test_final_model_generation_wrapper_stops_when_refinement_has_no_successor
```

The test currently performs a global source-string comparison:

```python
assert text.index(guard) < text.index(dereference)
```

This is invalid because `model.internal_engineering_model_id` occurs elsewhere earlier in the file, outside the guarded helper.

Latest focused result:

`1 failed, 9 passed in 0.69s`

Therefore the exact next technical action is:

1. Correct this test so it scopes the assertion to `_render_authority_backed_sysml` or, preferably, tests function behavior with `model=None`.
2. Run the focused suite.
3. Run `git diff --check`.
4. Run full regression.
5. Reopen the app and verify that an incomplete Model Quality Review no longer produces a traceback.
6. Confirm `MQR-000001` resumes at 2 / 11 without a new LLM refinement run.
7. Continue Human Model Quality Review.

Do not mark OBS-033 closed before the live retest passes.

---

# 10. Gate 3 continuation after the guard retest

Continue Project `000116`, Lead Source `SRC-000002`.

Required sequence:

1. Complete Human Model Quality Review for IME-000003 ... IME-000011.
2. Finalize Model Quality Authority.
3. Record resulting `MQA-*`.
4. Materialize Human-authorized successor Internal Model.
5. Confirm successor IEM is bound to exact:
   - base IEM
   - TFA authority
   - MQA authority
6. Generate SysML v2 deterministically from successor only.
7. Run authority-backed validation.
8. Complete the actual post-generation Final Model Review.
9. Human release / publication.
10. Record exact IDs, fingerprints, paths and validation result for thesis evidence.

No direct generation from the base IEM should be used as the normal app happy path.

After the Lead Source reaches publication, determine whether to pull the other three already successfully processed Sources through the same downstream single-source path for additional 0.3.0 validation coverage.

Even if all four are validated independently, do not call that true Multi-Source Processing. `BLK-002` remains separate until explicitly audited/fixed/retested.

---

# 11. Gate 3 thesis documentation — later, not during live execution

After empirical validation, create the Gate 3 thesis record.

It must include:

- Project / Source / SHA
- Processing Run / Attempt
- each workflow gate
- Human decisions
- downstream IDs
- LLM/alignment behavior
- failures and bounded fixes
- Gate 3C canonical acceptance mismatch
- OBS-032 terminology ambiguity
- OBS-033 missing app refinement integration + repair/retest
- SysML generation
- external validation
- Final Model Review
- Human release / publication
- distinction between independent single-source validation and real multi-source validation

---

# 12. Presentation — only after validation

Primary basis:

`collaboration/presentations/interim_presentation_plan.md`

Preserved presentation/demo checkpoint:

`collaboration/checkpoints/2026-08-19_presentation_wp12_demo_ssot.md`

Use the existing plan as the structure, not a new presentation invented from scratch.

Current intended narrative:

1. Kick-off / research objective
2. Literature-derived three-layer architecture
3. Original six-step concept → governed executable system
4. High-level activity / CATIA context
5. Implementation boundary / MVP
6. Logical architecture and layer realization
7. Architecture development / requirement coverage
8. Verification and observed findings
9. Remaining MVP / limitations
10. Outlook

Presentation status language must distinguish:

- IMPLEMENTED + VERIFIED
- IMPLEMENTED / EFFECTIVENESS OPEN
- ARCHITECTURE ONLY
- PLANNED NEXT
- BLOCKED

Important presentation story:

Idea
→ Systems Engineering architecture
→ Prototype implementation
→ Verification
→ real findings exposed by testing
→ bounded architecture / semantic corrections
→ remaining work

The presentation should explicitly show the incoming-data processing graph, including the Persona split and Human Review, because this is a central part of the implementation and thesis learning.

---

# 13. Safe Demo — after presentation

Use the agreed "Kochshow" strategy.

Principles:

- start a real LLM call live;
- show that the actual workflow was genuinely triggered;
- do not wait several minutes for completion;
- transparently switch to a prepared persisted state produced by the same real pipeline;
- continue live until the next expensive LLM boundary;
- trigger it, then switch to the next prepared persisted state;
- never present manually fabricated content as live Agent output;
- checkpoints must preserve coherent Project/Source/Run/Artifact/Review identities and provenance;
- final deterministic SysML generation and validation can be executed live if stable;
- use single-source demo states while `BLK-002` remains open.

Potential prepared stages may use checkpoint Projects conceptually like:

- DEMO-00 — Project / Source ready
- DEMO-10 — Processing completed
- DEMO-20 — Human Engineering Review ready
- DEMO-30 — Approved Engineering Information / placement ready
- DEMO-40 — Model Refinement ready
- DEMO-50 — approved successor / generation ready

Exact checkpoint Project IDs should be created only from genuine pipeline states and documented before the demo.

Suggested transparent transition language:

"I'll start the processing step once live so you can see how the workflow is actually triggered. Since the agent processing can take several minutes, I'll continue with a previously processed state from the same pipeline so that we can inspect the downstream engineering steps."

Do not hide this switch.

---

# 14. Open strategic items after validation / presentation / safe-demo preparation

Preserve:

- `BLK-002` — Multi-Source Processing Artifact Identity collision / provenance blocker
- `SEM-011` — broader SysML target construct coverage
- `SEM-013` — shared placement ambiguity vs actual Persona variance
- `SEM-014` — explicit Human relationship representation selection / UI revalidation
- `SEM-015-F01` — dependency-aware selective regeneration, deferred
- `OBS-032` — two review gates have ambiguous naming
- `OBS-033` — app Model Refinement integration; currently under live retest

Dashboard finding:

`OBS-DASH-001 — Project Dashboard no longer represents current authoritative workflow state.`

Disposition:

Do not repair for current 0.3.0 Gate-3 validation unless it blocks the workflow. Do not use the dashboard as authoritative demo state.

---

# 15. Next-chat starting instruction

Start with this exact objective:

> Continue Turing Generator v0.3.0 Gate 3 validation on branch `feature/processing-semantic-normalization`, Project `000116`, without restarting or regenerating upstream authority. First fix the faulty OBS-033 guard test, rerun focused + full regression, then live-retest the app. Resume `MQR-000001` at the persisted state and complete the Human Model Quality Review, successor IEM, deterministic SysML generation, validation, Final Model Review and publication. Only after validation move to the presentation using `collaboration/presentations/interim_presentation_plan.md`, then prepare the Safe Demo using the agreed Kochshow strategy. Do not stage/commit until the current validation work is reviewed and accepted.

---

# 16. LIVE LOCAL GIT SNAPSHOT

The commands used to install this SSOT shall append the current local Git state below this line. That appended output is authoritative for the exact current uncommitted/staged file list.

```text
Captured: 2026-08-27 13:10:52 +0200
BRANCH: feature/processing-semantic-normalization
HEAD: 9f2ae071c51aa3d605e6b81b28f16ce975bf4b14
ORIGIN_MAIN: d183974c2cc9231a1b006eb8979fb5851f8b665b

=== git status --short ===
 M .DS_Store
 M app/__pycache__/team_agentic_ingestion_ui.cpython-313.pyc
 M app/human_subject_review_ui.py
 M app/model_final_review_ui.py
 M app/turing_generator_app.py
 M app/turing_generator_ui.py
 M collaboration/contracts/r4c_persona_subject_interpretation_contract.md
 M collaboration/contracts/r4c_subject_centric_human_review_contract.md
 M data/ingestion_reports/task_ingest_example_legacy_model_description_team_agentic_ingestion_report_dry_run.md
 M external/.DS_Store
 M modules/agents/__pycache__/team_runner.cpython-313.pyc
 M modules/agents/__pycache__/types.cpython-313.pyc
 M modules/engineering_subjects/__init__.py
 M modules/engineering_subjects/contract.py
 M modules/engineering_subjects/discovery.py
 M modules/engineering_subjects/errors.py
 M modules/evidence_interpretation/pipeline.py
 M modules/guided_workflow/write_service.py
 M modules/ingestion/__pycache__/agent_inputs.cpython-313.pyc
 M modules/ingestion/__pycache__/agent_tasks.cpython-313.pyc
 M modules/ingestion/__pycache__/review_report.cpython-313.pyc
 M modules/ingestion/__pycache__/run_summary.cpython-313.pyc
 M modules/ingestion/__pycache__/team_agentic_pipeline.cpython-313.pyc
 M modules/llm/progress.py
 M modules/project_ingestion/service.py
 M modules/subject_interpretation/pipeline.py
 M tests/test_human_subject_review_decision_lifecycle.py
 M tests/test_human_subject_review_ui.py
 M tests/test_shared_evidence_interpretation_pipeline.py
 M tests/test_subject_interpretation_pipeline.py
 M tests/test_turing_generator_ingestion_running_action.py
 M tests/test_turing_generator_retry_ui.py
?? app/__pycache__/global_controls.cpython-313.pyc
?? app/__pycache__/guided_workflow_actions.cpython-313.pyc
?? app/__pycache__/guided_workflow_detail_ui.cpython-313.pyc
?? app/__pycache__/guided_workflow_ui.cpython-313.pyc
?? app/__pycache__/human_model_placement_review_ui.cpython-313.pyc
?? app/__pycache__/human_review_approval_ui.cpython-313.pyc
?? app/__pycache__/human_review_finalization_ui.cpython-313.pyc
?? app/__pycache__/human_review_item_editor_ui.cpython-313.pyc
?? app/__pycache__/human_review_promotion_ui.cpython-313.pyc
?? app/__pycache__/human_review_scoped_actions_ui.cpython-313.pyc
?? app/__pycache__/human_subject_review_ui.cpython-313.pyc
?? app/__pycache__/model_assembly_preview_ui.cpython-313.pyc
?? app/__pycache__/model_final_review_ui.cpython-313.pyc
?? app/__pycache__/model_refinement_review_ui.cpython-313.pyc
?? app/__pycache__/presentation_preferences.cpython-313.pyc
?? app/__pycache__/project_dashboard_ui.cpython-313.pyc
?? app/__pycache__/turing_generator_app.cpython-313.pyc
?? app/__pycache__/turing_generator_navigation.cpython-313.pyc
?? app/__pycache__/turing_generator_ui.cpython-313.pyc
?? app/__pycache__/version.cpython-313.pyc
?? app/model_refinement_review_ui.py
?? app/version.py
?? collaboration/.DS_Store
?? collaboration/2026-08-27_gate3_validation_handover_ssot.md
?? collaboration/audits/processing_robustness_adjustment_evaluation_2026-08-26.md
?? collaboration/checkpoints/2026-08-27_gate3_validation_handover_ssot.md
?? collaboration/decisions/ADR-030-semantic-interpretation-and-controlled-classification-alignment.md
?? collaboration/decisions/ADR-031-semantic-field-consistency-alignment.md
?? collaboration_ssot_input.zip
?? data/.DS_Store
?? data/ingestion_reports/task_001_ingest_example_model_team_agentic_ingestion_report_dry_run.md
?? data/ingestion_reports/task_001_team_agentic_ingestion_report_f1_test.md
?? data/projects/
?? data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260721T094243Z/
?? data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T095140Z/
?? data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T113937Z/
?? f1_1_update.patch
?? f2_ui_polish.patch
?? f2_ui_polish_ui_only.patch
?? g2_ssot_update.patch
?? g7_failed_run_diagnostic.zip
?? legacy/.DS_Store
?? legacy/demo/.DS_Store
?? modules/.DS_Store
?? modules/approved_engineering_information/__pycache__/
?? modules/approved_input/__pycache__/
?? modules/classification_alignment/
?? modules/engineering_subjects/__pycache__/
?? modules/engineering_subjects/grounding.py
?? modules/evidence_detection/__pycache__/
?? modules/evidence_interpretation/__pycache__/
?? modules/final_model_review/__pycache__/
?? modules/framework/__pycache__/
?? modules/framework_assignment/__pycache__/
?? modules/guided_workflow/__pycache__/
?? modules/human_review/__pycache__/
?? modules/information_units/__pycache__/
?? modules/ingestion/.DS_Store
?? modules/internal_model/__pycache__/
?? modules/llm/__pycache__/progress.cpython-313.pyc
?? modules/model_assembly/__pycache__/
?? modules/model_candidates/__pycache__/
?? modules/model_placement/__pycache__/
?? modules/model_quality/__pycache__/
?? modules/output_publication/__pycache__/
?? modules/project_coverage/__pycache__/
?? modules/project_dashboard/__pycache__/
?? modules/project_glossary/__pycache__/
?? modules/project_ingestion/__pycache__/
?? modules/project_processing/__pycache__/
?? modules/project_sources/__pycache__/
?? modules/project_workspace/__pycache__/
?? modules/review_workspace/__pycache__/
?? modules/semantic_consensus/__pycache__/
?? modules/semantic_consistency_alignment/
?? modules/semantic_consolidation/__pycache__/
?? modules/semantic_extraction/__pycache__/
?? modules/semantics/__pycache__/
?? modules/source_analysis_units/__pycache__/
?? modules/source_evidence/__pycache__/
?? modules/source_preparation/__pycache__/
?? modules/source_projection/__pycache__/
?? modules/subject_consensus/__pycache__/
?? modules/subject_interpretation/__pycache__/
?? modules/subject_review/__pycache__/
?? modules/sysml_generation/__pycache__/
?? modules/sysml_validation/__pycache__/
?? modules/target_model_formulation/__pycache__/
?? modules/terminology_mapping/__pycache__/
?? scripts/__pycache__/regenerate_review_report_f1_test.cpython-313-pytest-9.1.1.pyc
?? scripts/__pycache__/test_consensus_dry_run.cpython-313-pytest-9.1.1.pyc
?? scripts/__pycache__/test_consensus_synthetic.cpython-313-pytest-9.1.1.pyc
?? scripts/__pycache__/test_evidence_memory.cpython-313-pytest-9.1.1.pyc
?? scripts/__pycache__/test_interpretation_memory.cpython-313-pytest-9.1.1.pyc
?? scripts/__pycache__/test_team_agentic_ingestion_dry_run.cpython-313-pytest-9.1.1.pyc
?? scripts/__pycache__/test_team_runner_dry_run.cpython-313-pytest-9.1.1.pyc
?? tests/__pycache__/
?? tests/test_classification_alignment.py
?? tests/test_engineering_subject_duplicate_consolidation.py
?? tests/test_engineering_subject_grounding_recovery.py
?? tests/test_model_refinement_review_ui.py
?? tests/test_processing_phase_progress.py
?? tests/test_project_ingestion_subject_failure_classification.py
?? tests/test_semantic_consistency_alignment.py
?? tests/test_subject_discovery_raw_observability.py
?? wp12_blk001_b1ab_resolution_core_patch.py
?? wp12_blk001_b1c_card_ui_patch.py
?? wp12_blk001_subslice_a_patch.py
?? wp12_blk001_subslice_a_patch_v2.py
?? wp12_blk001_subslice_b_patch.py
?? wp12_blk006_c6c3a_reference_grounded_formulation_contract_patch.py

=== TRACKED UNSTAGED ===
.DS_Store
app/__pycache__/team_agentic_ingestion_ui.cpython-313.pyc
app/human_subject_review_ui.py
app/model_final_review_ui.py
app/turing_generator_app.py
app/turing_generator_ui.py
collaboration/contracts/r4c_persona_subject_interpretation_contract.md
collaboration/contracts/r4c_subject_centric_human_review_contract.md
data/ingestion_reports/task_ingest_example_legacy_model_description_team_agentic_ingestion_report_dry_run.md
external/.DS_Store
modules/agents/__pycache__/team_runner.cpython-313.pyc
modules/agents/__pycache__/types.cpython-313.pyc
modules/engineering_subjects/__init__.py
modules/engineering_subjects/contract.py
modules/engineering_subjects/discovery.py
modules/engineering_subjects/errors.py
modules/evidence_interpretation/pipeline.py
modules/guided_workflow/write_service.py
modules/ingestion/__pycache__/agent_inputs.cpython-313.pyc
modules/ingestion/__pycache__/agent_tasks.cpython-313.pyc
modules/ingestion/__pycache__/review_report.cpython-313.pyc
modules/ingestion/__pycache__/run_summary.cpython-313.pyc
modules/ingestion/__pycache__/team_agentic_pipeline.cpython-313.pyc
modules/llm/progress.py
modules/project_ingestion/service.py
modules/subject_interpretation/pipeline.py
tests/test_human_subject_review_decision_lifecycle.py
tests/test_human_subject_review_ui.py
tests/test_shared_evidence_interpretation_pipeline.py
tests/test_subject_interpretation_pipeline.py
tests/test_turing_generator_ingestion_running_action.py
tests/test_turing_generator_retry_ui.py

=== UNTRACKED ===
app/__pycache__/global_controls.cpython-313.pyc
app/__pycache__/guided_workflow_actions.cpython-313.pyc
app/__pycache__/guided_workflow_detail_ui.cpython-313.pyc
app/__pycache__/guided_workflow_ui.cpython-313.pyc
app/__pycache__/human_model_placement_review_ui.cpython-313.pyc
app/__pycache__/human_review_approval_ui.cpython-313.pyc
app/__pycache__/human_review_finalization_ui.cpython-313.pyc
app/__pycache__/human_review_item_editor_ui.cpython-313.pyc
app/__pycache__/human_review_promotion_ui.cpython-313.pyc
app/__pycache__/human_review_scoped_actions_ui.cpython-313.pyc
app/__pycache__/human_subject_review_ui.cpython-313.pyc
app/__pycache__/model_assembly_preview_ui.cpython-313.pyc
app/__pycache__/model_final_review_ui.cpython-313.pyc
app/__pycache__/model_refinement_review_ui.cpython-313.pyc
app/__pycache__/presentation_preferences.cpython-313.pyc
app/__pycache__/project_dashboard_ui.cpython-313.pyc
app/__pycache__/turing_generator_app.cpython-313.pyc
app/__pycache__/turing_generator_navigation.cpython-313.pyc
app/__pycache__/turing_generator_ui.cpython-313.pyc
app/__pycache__/version.cpython-313.pyc
app/model_refinement_review_ui.py
app/version.py
collaboration/.DS_Store
collaboration/2026-08-27_gate3_validation_handover_ssot.md
collaboration/audits/processing_robustness_adjustment_evaluation_2026-08-26.md
collaboration/checkpoints/2026-08-27_gate3_validation_handover_ssot.md
collaboration/decisions/ADR-030-semantic-interpretation-and-controlled-classification-alignment.md
collaboration/decisions/ADR-031-semantic-field-consistency-alignment.md
collaboration_ssot_input.zip
data/.DS_Store
data/ingestion_reports/task_001_ingest_example_model_team_agentic_ingestion_report_dry_run.md
data/ingestion_reports/task_001_team_agentic_ingestion_report_f1_test.md
data/projects/000116/approved_inputs/manifests/AIN-000001.json
data/projects/000116/approved_inputs/manifests/AIN-000002.json
data/projects/000116/approved_inputs/manifests/AIN-000003.json
data/projects/000116/approved_inputs/manifests/AIN-000004.json
data/projects/000116/approved_inputs/manifests/AIN-000005.json
data/projects/000116/approved_inputs/manifests/AIN-000006.json
data/projects/000116/approved_inputs/manifests/AIN-000007.json
data/projects/000116/approved_inputs/manifests/AIN-000008.json
data/projects/000116/approved_inputs/manifests/AIN-000009.json
data/projects/000116/approved_inputs/manifests/AIN-000010.json
data/projects/000116/approved_inputs/manifests/AIN-000011.json
data/projects/000116/approved_inputs/manifests/AIN-000012.json
data/projects/000116/approved_inputs/manifests/AIN-000013.json
data/projects/000116/approved_inputs/manifests/AIN-000014.json
data/projects/000116/internal_models_v2/IEM-000001/snapshot.json
data/projects/000116/model_assemblies/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/assembly_draft.json
data/projects/000116/model_assemblies/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/final_review/decisions/FAD-000001.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/approved_placement_set.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/comparison.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/decisions/MPD-000001.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/decisions/MPD-000002.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/decisions/MPD-000003.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/decisions/MPD-000004.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/decisions/MPD-000005.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/decisions/MPD-000006.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/decisions/MPD-000007.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/decisions/MPD-000008.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/decisions/MPD-000009.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/decisions/MPD-000010.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/decisions/MPD-000011.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/decisions/MPD-000012.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/decisions/MPD-000013.json
data/projects/000116/model_placement_reviews/d17c91967fa201092d49c868597e17dfe2998042e61bf8710a68f2b506d4c486/decisions/MPD-000014.json
data/projects/000116/model_quality/decisions/MQD-000001.json
data/projects/000116/model_quality/decisions/MQD-000002.json
data/projects/000116/model_quality/reviews/MQR-000001/bundle.json
data/projects/000116/model_quality/reviews/MQR-000001/request.json
data/projects/000116/model_quality/runs/MQR-000001/batch_01/team_model_quality_refinement/agent_model_quality_refiner/agent_model_quality_refiner_run_01.json
data/projects/000116/project_manifest.json
data/projects/000116/reviews/RVD-000001/review_document_manifest.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/finalized/effective_decisions.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/finalized/reviewed_document.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/finalized/reviewed_report.md
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/review_version_manifest.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000001.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000002.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000003.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000004.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000005.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000006.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000007.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000008.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000009.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000010.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000011.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000012.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000013.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000014.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000015.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000016.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000017.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000018.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000019.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000020.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000021.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000022.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000023.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000024.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000025.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000026.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000027.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000028.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000029.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000030.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000031.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000032.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000033.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000034.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000035.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000036.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000037.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000038.json
data/projects/000116/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000039.json
data/projects/000116/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000002/classification_alignment/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000002/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000002/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000002/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000002/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000002/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000002/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000002/source_preparation_result.json
data/projects/000116/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000002/canonical_subject_set.json
data/projects/000116/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000002/shared_evidence_binding_summary.json
data/projects/000116/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000002/shared_evidence_review_input.json
data/projects/000116/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000002/shared_evidence_semantic_consensus.json
data/projects/000116/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000002/subject_consensus.json
data/projects/000116/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000002/subject_interpretations.json
data/projects/000116/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000002/subject_review_bundle.json
data/projects/000116/runs/RUN-000001/artifacts/review_reports/agentic_ingestion/ATT-000002/ingestion_review_report.md
data/projects/000116/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000002/team_agentic_ingestion_run_summary.json
data/projects/000116/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000002/team_agentic_ingestion_run_summary.md
data/projects/000116/runs/RUN-000001/events/EVT-000001.json
data/projects/000116/runs/RUN-000001/events/EVT-000002.json
data/projects/000116/runs/RUN-000001/events/EVT-000003.json
data/projects/000116/runs/RUN-000001/events/EVT-000004.json
data/projects/000116/runs/RUN-000001/events/EVT-000005.json
data/projects/000116/runs/RUN-000001/events/EVT-000006.json
data/projects/000116/runs/RUN-000001/run_manifest.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/ingestion_review_report.md
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/classification_alignment/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/source_preparation_result.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/canonical_subject_set.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/shared_evidence_binding_summary.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/shared_evidence_review_input.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/shared_evidence_semantic_consensus.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/subject_consensus.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/subject_interpretations.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/subject_review_bundle.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/team_agentic_ingestion_run_summary.json
data/projects/000116/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/team_agentic_ingestion_run_summary.md
data/projects/000116/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/source_preparation_result.json
data/projects/000116/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/canonical_subject_set.json
data/projects/000116/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/shared_evidence_binding_summary.json
data/projects/000116/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/shared_evidence_review_input.json
data/projects/000116/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/shared_evidence_semantic_consensus.json
data/projects/000116/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/subject_consensus.json
data/projects/000116/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/subject_interpretations.json
data/projects/000116/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/subject_review_bundle.json
data/projects/000116/runs/RUN-000002/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/000116/runs/RUN-000002/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/000116/runs/RUN-000002/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/000116/runs/RUN-000002/events/EVT-000001.json
data/projects/000116/runs/RUN-000002/events/EVT-000002.json
data/projects/000116/runs/RUN-000002/events/EVT-000003.json
data/projects/000116/runs/RUN-000002/events/EVT-000004.json
data/projects/000116/runs/RUN-000002/run_manifest.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/source_preparation_result.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/canonical_subject_set.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_binding_summary.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_review_input.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_semantic_consensus.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/subject_consensus.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/subject_interpretations.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/subject_review_bundle.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/000116/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/000116/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000003/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000003/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000003/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000003/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000003/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000003/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000003/source_preparation_result.json
data/projects/000116/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000003/canonical_subject_set.json
data/projects/000116/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000003/shared_evidence_binding_summary.json
data/projects/000116/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000003/shared_evidence_review_input.json
data/projects/000116/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000003/shared_evidence_semantic_consensus.json
data/projects/000116/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000003/subject_consensus.json
data/projects/000116/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000003/subject_interpretations.json
data/projects/000116/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000003/subject_review_bundle.json
data/projects/000116/runs/RUN-000003/artifacts/review_reports/agentic_ingestion/ATT-000003/ingestion_review_report.md
data/projects/000116/runs/RUN-000003/artifacts/run_summaries/agentic_ingestion/ATT-000003/team_agentic_ingestion_run_summary.json
data/projects/000116/runs/RUN-000003/artifacts/run_summaries/agentic_ingestion/ATT-000003/team_agentic_ingestion_run_summary.md
data/projects/000116/runs/RUN-000003/events/EVT-000001.json
data/projects/000116/runs/RUN-000003/events/EVT-000002.json
data/projects/000116/runs/RUN-000003/events/EVT-000003.json
data/projects/000116/runs/RUN-000003/events/EVT-000004.json
data/projects/000116/runs/RUN-000003/events/EVT-000005.json
data/projects/000116/runs/RUN-000003/events/EVT-000006.json
data/projects/000116/runs/RUN-000003/events/EVT-000007.json
data/projects/000116/runs/RUN-000003/events/EVT-000008.json
data/projects/000116/runs/RUN-000003/run_manifest.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/source_preparation_result.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_binding_summary.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_review_input.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_semantic_consensus.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/ingestion_review_report.md
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/source_preparation_result.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/shared_evidence_binding_summary.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/shared_evidence_review_input.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/shared_evidence_semantic_consensus.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/classification_repairs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/team_agentic_ingestion_run_summary.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000002/phase_f/team_agentic_ingestion_run_summary.md
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/ingestion_review_report.md
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/source_preparation_result.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/canonical_subject_set.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/shared_evidence_binding_summary.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/shared_evidence_review_input.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/shared_evidence_semantic_consensus.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/subject_consensus.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/subject_interpretations.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/subject_review_bundle.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/team_agentic_ingestion_run_summary.json
data/projects/000116/runs/RUN-000003/work/agentic_ingestion/ATT-000003/phase_f/team_agentic_ingestion_run_summary.md
data/projects/000116/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000005/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000005/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000005/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000005/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000005/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000005/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000005/source_preparation_result.json
data/projects/000116/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000005/subject_discovery/raw_responses/initial.json
data/projects/000116/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000005/canonical_subject_set.json
data/projects/000116/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000005/shared_evidence_binding_summary.json
data/projects/000116/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000005/shared_evidence_review_input.json
data/projects/000116/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000005/shared_evidence_semantic_consensus.json
data/projects/000116/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000005/subject_consensus.json
data/projects/000116/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000005/subject_interpretations.json
data/projects/000116/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000005/subject_review_bundle.json
data/projects/000116/runs/RUN-000004/artifacts/review_reports/agentic_ingestion/ATT-000005/ingestion_review_report.md
data/projects/000116/runs/RUN-000004/artifacts/run_summaries/agentic_ingestion/ATT-000005/team_agentic_ingestion_run_summary.json
data/projects/000116/runs/RUN-000004/artifacts/run_summaries/agentic_ingestion/ATT-000005/team_agentic_ingestion_run_summary.md
data/projects/000116/runs/RUN-000004/events/EVT-000001.json
data/projects/000116/runs/RUN-000004/events/EVT-000002.json
data/projects/000116/runs/RUN-000004/events/EVT-000003.json
data/projects/000116/runs/RUN-000004/events/EVT-000004.json
data/projects/000116/runs/RUN-000004/events/EVT-000005.json
data/projects/000116/runs/RUN-000004/events/EVT-000006.json
data/projects/000116/runs/RUN-000004/events/EVT-000007.json
data/projects/000116/runs/RUN-000004/events/EVT-000008.json
data/projects/000116/runs/RUN-000004/events/EVT-000009.json
data/projects/000116/runs/RUN-000004/events/EVT-000010.json
data/projects/000116/runs/RUN-000004/events/EVT-000011.json
data/projects/000116/runs/RUN-000004/events/EVT-000012.json
data/projects/000116/runs/RUN-000004/run_manifest.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/source_preparation_result.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_binding_summary.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_review_input.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_semantic_consensus.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/classification_repairs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/ingestion_review_report.md
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/source_preparation_result.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/shared_evidence_binding_summary.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/shared_evidence_review_input.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/shared_evidence_semantic_consensus.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/classification_alignment/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/classification_alignment/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/team_agentic_ingestion_run_summary.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000002/phase_f/team_agentic_ingestion_run_summary.md
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000003/ingestion_review_report.md
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/source_preparation_result.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/shared_evidence_binding_summary.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/shared_evidence_review_input.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/shared_evidence_semantic_consensus.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000003/phase_f/team_agentic_ingestion_run_summary.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000003/phase_f/team_agentic_ingestion_run_summary.md
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000004/ingestion_review_report.md
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000004/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000004/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000004/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000004/phase_f/agent_outputs/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000004/phase_f/agent_outputs/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000004/phase_f/agent_outputs/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000004/phase_f/agent_outputs/source_preparation_result.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000004/phase_f/agent_outputs/subject_discovery/raw_responses/initial.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000004/phase_f/consensus_reports/shared_evidence_binding_summary.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000004/phase_f/consensus_reports/shared_evidence_review_input.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000004/phase_f/consensus_reports/shared_evidence_semantic_consensus.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000004/phase_f/team_agentic_ingestion_run_summary.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000004/phase_f/team_agentic_ingestion_run_summary.md
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/ingestion_review_report.md
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/agent_outputs/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/agent_outputs/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/agent_outputs/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/agent_outputs/source_preparation_result.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/agent_outputs/subject_discovery/raw_responses/initial.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/consensus_reports/canonical_subject_set.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/consensus_reports/shared_evidence_binding_summary.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/consensus_reports/shared_evidence_review_input.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/consensus_reports/shared_evidence_semantic_consensus.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/consensus_reports/subject_consensus.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/consensus_reports/subject_interpretations.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/consensus_reports/subject_review_bundle.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/r4c_subject_interpretation/classification_alignment/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_literal_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/team_agentic_ingestion_run_summary.json
data/projects/000116/runs/RUN-000004/work/agentic_ingestion/ATT-000005/phase_f/team_agentic_ingestion_run_summary.md
data/projects/000116/runs/RUN-000005/events/EVT-000001.json
data/projects/000116/runs/RUN-000005/events/EVT-000002.json
data/projects/000116/runs/RUN-000005/events/EVT-000003.json
data/projects/000116/runs/RUN-000005/events/EVT-000004.json
data/projects/000116/runs/RUN-000005/events/EVT-000005.json
data/projects/000116/runs/RUN-000005/run_manifest.json
data/projects/000116/semantics/human_reviews/HRD-000001.json
data/projects/000116/semantics/source_analysis_units/SAU-000001.json
data/projects/000116/semantics/source_analysis_units/SAU-000002.json
data/projects/000116/semantics/source_analysis_units/SAU-000003.json
data/projects/000116/semantics/source_analysis_units/SAU-000004.json
data/projects/000116/semantics/source_analysis_units/SAU-000005.json
data/projects/000116/semantics/source_analysis_units/SAU-000006.json
data/projects/000116/semantics/source_analysis_units/SAU-000007.json
data/projects/000116/semantics/source_analysis_units/SAU-000008.json
data/projects/000116/semantics/source_analysis_units/SAU-000009.json
data/projects/000116/semantics/source_analysis_units/SAU-000010.json
data/projects/000116/semantics/source_analysis_units/SAU-000011.json
data/projects/000116/semantics/source_analysis_units/SAU-000012.json
data/projects/000116/semantics/source_analysis_units/SAU-000013.json
data/projects/000116/semantics/source_analysis_units/SAU-000014.json
data/projects/000116/semantics/source_analysis_units/SAU-000015.json
data/projects/000116/semantics/source_analysis_units/SAU-000016.json
data/projects/000116/semantics/source_analysis_units/SAU-000017.json
data/projects/000116/semantics/source_analysis_units/SAU-000018.json
data/projects/000116/semantics/source_analysis_units/SAU-000019.json
data/projects/000116/semantics/source_analysis_units/SAU-000020.json
data/projects/000116/semantics/source_analysis_units/SAU-000021.json
data/projects/000116/semantics/source_analysis_units/SAU-000022.json
data/projects/000116/semantics/source_analysis_units/SAU-000023.json
data/projects/000116/semantics/source_analysis_units/SAU-000024.json
data/projects/000116/semantics/source_analysis_units/SAU-000025.json
data/projects/000116/semantics/source_analysis_units/SAU-000026.json
data/projects/000116/semantics/source_analysis_units/SAU-000027.json
data/projects/000116/semantics/source_analysis_units/SAU-000028.json
data/projects/000116/semantics/source_analysis_units/SAU-000029.json
data/projects/000116/semantics/source_analysis_units/SAU-000030.json
data/projects/000116/semantics/source_analysis_units/SAU-000031.json
data/projects/000116/semantics/source_analysis_units/SAU-000032.json
data/projects/000116/semantics/source_analysis_units/SAU-000033.json
data/projects/000116/semantics/source_analysis_units/SAU-000034.json
data/projects/000116/semantics/source_analysis_units/SAU-000035.json
data/projects/000116/semantics/source_analysis_units/SAU-000036.json
data/projects/000116/semantics/source_analysis_units/SAU-000037.json
data/projects/000116/semantics/source_analysis_units/SAU-000038.json
data/projects/000116/semantics/source_analysis_units/SAU-000039.json
data/projects/000116/semantics/source_analysis_units/SAU-000040.json
data/projects/000116/semantics/source_analysis_units/SAU-000041.json
data/projects/000116/semantics/source_analysis_units/SAU-000042.json
data/projects/000116/semantics/source_analysis_units/SAU-000043.json
data/projects/000116/semantics/source_analysis_units/SAU-000044.json
data/projects/000116/semantics/source_analysis_units/SAU-000045.json
data/projects/000116/semantics/source_analysis_units/SAU-000046.json
data/projects/000116/semantics/source_analysis_units/SAU-000047.json
data/projects/000116/semantics/source_analysis_units/SAU-000048.json
data/projects/000116/semantics/source_analysis_units/SAU-000049.json
data/projects/000116/semantics/source_analysis_units/SAU-000050.json
data/projects/000116/semantics/source_analysis_units/SAU-000051.json
data/projects/000116/semantics/source_analysis_units/SAU-000052.json
data/projects/000116/semantics/source_analysis_units/SAU-000053.json
data/projects/000116/semantics/source_analysis_units/SAU-000054.json
data/projects/000116/semantics/source_analysis_units/SAU-000055.json
data/projects/000116/semantics/source_analysis_units/SAU-000056.json
data/projects/000116/semantics/source_analysis_units/SAU-000057.json
data/projects/000116/semantics/source_evidence/EVD-000001.json
data/projects/000116/semantics/source_evidence/EVD-000002.json
data/projects/000116/semantics/source_evidence/EVD-000003.json
data/projects/000116/semantics/source_evidence/EVD-000004.json
data/projects/000116/semantics/source_evidence/EVD-000005.json
data/projects/000116/semantics/source_evidence/EVD-000006.json
data/projects/000116/semantics/source_evidence/EVD-000007.json
data/projects/000116/semantics/source_evidence/EVD-000008.json
data/projects/000116/semantics/source_evidence/EVD-000009.json
data/projects/000116/semantics/source_evidence/EVD-000010.json
data/projects/000116/semantics/source_evidence/EVD-000011.json
data/projects/000116/semantics/source_evidence/EVD-000012.json
data/projects/000116/semantics/source_evidence/EVD-000013.json
data/projects/000116/semantics/source_evidence/EVD-000014.json
data/projects/000116/semantics/source_evidence/EVD-000015.json
data/projects/000116/semantics/source_evidence/EVD-000016.json
data/projects/000116/semantics/source_evidence/EVD-000017.json
data/projects/000116/semantics/source_evidence/EVD-000018.json
data/projects/000116/semantics/source_evidence/EVD-000019.json
data/projects/000116/semantics/source_evidence/EVD-000020.json
data/projects/000116/semantics/source_evidence/EVD-000021.json
data/projects/000116/semantics/source_evidence/EVD-000022.json
data/projects/000116/semantics/source_evidence/EVD-000023.json
data/projects/000116/semantics/source_evidence/EVD-000024.json
data/projects/000116/semantics/source_evidence/EVD-000025.json
data/projects/000116/semantics/source_evidence/EVD-000026.json
data/projects/000116/semantics/source_evidence/EVD-000027.json
data/projects/000116/semantics/source_evidence/EVD-000028.json
data/projects/000116/semantics/source_evidence/EVD-000029.json
data/projects/000116/semantics/source_evidence/EVD-000030.json
data/projects/000116/semantics/source_evidence/EVD-000031.json
data/projects/000116/semantics/source_evidence/EVD-000032.json
data/projects/000116/semantics/source_evidence/EVD-000033.json
data/projects/000116/semantics/source_evidence/EVD-000034.json
data/projects/000116/semantics/source_evidence/EVD-000035.json
data/projects/000116/semantics/source_evidence/EVD-000036.json
data/projects/000116/semantics/source_evidence/EVD-000037.json
data/projects/000116/semantics/source_evidence/EVD-000038.json
data/projects/000116/semantics/source_evidence/EVD-000039.json
data/projects/000116/semantics/source_evidence/EVD-000040.json
data/projects/000116/semantics/source_evidence/EVD-000041.json
data/projects/000116/semantics/source_evidence/EVD-000042.json
data/projects/000116/semantics/source_evidence/EVD-000043.json
data/projects/000116/semantics/source_evidence/EVD-000044.json
data/projects/000116/semantics/source_evidence/EVD-000045.json
data/projects/000116/semantics/source_evidence/EVD-000046.json
data/projects/000116/semantics/source_evidence/EVD-000047.json
data/projects/000116/semantics/source_evidence/EVD-000048.json
data/projects/000116/semantics/source_evidence/EVD-000049.json
data/projects/000116/semantics/source_evidence/EVD-000050.json
data/projects/000116/semantics/source_evidence/EVD-000051.json
data/projects/000116/semantics/source_evidence/EVD-000052.json
data/projects/000116/semantics/source_evidence/EVD-000053.json
data/projects/000116/semantics/source_evidence/EVD-000054.json
data/projects/000116/semantics/source_evidence/EVD-000055.json
data/projects/000116/semantics/source_evidence/EVD-000056.json
data/projects/000116/semantics/source_evidence/EVD-000057.json
data/projects/000116/semantics/source_evidence/EVD-000058.json
data/projects/000116/semantics/source_evidence/EVD-000059.json
data/projects/000116/semantics/source_preparation/SP-000001/afdedea0281a7e20ee66407a9232dbf9f0f60651a743d342e5d2e36fab816b8b.json
data/projects/000116/semantics/source_preparation/SP-000002/b68e41df380e202dea36fdf2db2325fd1ce40711e58bdd27f778a8fa26181ca9.json
data/projects/000116/semantics/source_preparation/SP-000003/deb7b179ce38b030e46cbcbb3f79bcc545ae34d68d4797cbe80f91366120f41c.json
data/projects/000116/semantics/source_preparation/SP-000004/0f70efc35ad7e57a30190b88a0a856d365a5da4712250516e9055fde5fe8f03e.json
data/projects/000116/semantics/source_projections/SP-000001/content.txt
data/projects/000116/semantics/source_projections/SP-000001/projection.json
data/projects/000116/semantics/source_projections/SP-000002/content.txt
data/projects/000116/semantics/source_projections/SP-000002/projection.json
data/projects/000116/semantics/source_projections/SP-000003/content.txt
data/projects/000116/semantics/source_projections/SP-000003/projection.json
data/projects/000116/semantics/source_projections/SP-000004/content.txt
data/projects/000116/semantics/source_projections/SP-000004/projection.json
data/projects/000116/sources/SRC-000001/content.md
data/projects/000116/sources/SRC-000001/source_manifest.json
data/projects/000116/sources/SRC-000002/content.md
data/projects/000116/sources/SRC-000002/source_manifest.json
data/projects/000116/sources/SRC-000003/content.md
data/projects/000116/sources/SRC-000003/source_manifest.json
data/projects/000116/sources/SRC-000004/content.md
data/projects/000116/sources/SRC-000004/source_manifest.json
data/projects/000116/sources/SRC-000005/content.csv
data/projects/000116/sources/SRC-000005/source_manifest.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000001.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000002.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000003.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000004.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000005.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000006.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000007.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000008.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000009.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000010.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000011.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000012.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000013.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000014.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000015.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000016.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000017.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000018.json
data/projects/000116/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000019.json
data/projects/000116/target_model_formulation/authority_sets/TFA-000001.json
data/projects/000116/target_model_formulation/decisions/TFD-000001.json
data/projects/000116/target_model_formulation/decisions/TFD-000002.json
data/projects/000116/target_model_formulation/reviews/TFR-000001.json
data/projects/000116/work/model_placement_generation/placement_2iel5s42/model_placement_execution.json
data/projects/000116/work/model_placement_generation/placement_2iel5s42/persona_outputs/team_modeling_projection/agent_modeling_architecture_focused_advisor/agent_modeling_architecture_focused_advisor_run_01.json
data/projects/000116/work/model_placement_generation/placement_2iel5s42/persona_outputs/team_modeling_projection/agent_modeling_conservative_reviewer/agent_modeling_conservative_reviewer_run_01.json
data/projects/000116/work/model_placement_generation/placement_2iel5s42/persona_outputs/team_modeling_projection/agent_modeling_rules_focused_advisor/agent_modeling_rules_focused_advisor_run_01.json
data/projects/081082/project_manifest.json
data/projects/081082/runs/RUN-000001/events/EVT-000001.json
data/projects/081082/runs/RUN-000001/events/EVT-000002.json
data/projects/081082/runs/RUN-000001/events/EVT-000003.json
data/projects/081082/runs/RUN-000001/events/EVT-000004.json
data/projects/081082/runs/RUN-000001/events/EVT-000005.json
data/projects/081082/runs/RUN-000001/run_manifest.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/ingestion_review_report.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/01_legacy_interpretation/SAU-000001/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/01_legacy_interpretation/SAU-000002/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/01_legacy_interpretation/SAU-000003/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/01_legacy_interpretation/SAU-000004/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/01_legacy_interpretation/SAU-000005/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/01_legacy_interpretation/SAU-000006/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/01_legacy_interpretation/SAU-000007/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/01_legacy_interpretation/SAU-000008/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/01_legacy_interpretation/SAU-000009/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/01_legacy_interpretation/SAU-000010/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/01_legacy_interpretation/SAU-000011/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/01_legacy_interpretation/SAU-000012/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/01_legacy_interpretation/SAU-000013/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/02_evidence_classification/SAU-000001/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/02_evidence_classification/SAU-000002/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/02_evidence_classification/SAU-000003/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/02_evidence_classification/SAU-000004/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/02_evidence_classification/SAU-000005/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/02_evidence_classification/SAU-000006/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/02_evidence_classification/SAU-000007/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/02_evidence_classification/SAU-000008/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/02_evidence_classification/SAU-000009/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/02_evidence_classification/SAU-000010/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/02_evidence_classification/SAU-000011/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/02_evidence_classification/SAU-000012/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/02_evidence_classification/SAU-000013/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/03_derivation_assessment/SAU-000001/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/03_derivation_assessment/SAU-000002/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/03_derivation_assessment/SAU-000003/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/03_derivation_assessment/SAU-000004/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/03_derivation_assessment/SAU-000005/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/03_derivation_assessment/SAU-000006/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/03_derivation_assessment/SAU-000007/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/03_derivation_assessment/SAU-000008/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/03_derivation_assessment/SAU-000009/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/03_derivation_assessment/SAU-000010/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/03_derivation_assessment/SAU-000011/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/03_derivation_assessment/SAU-000012/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/03_derivation_assessment/SAU-000013/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/05_semantic_consolidation/SAU-000003/semantic_element_comparator_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/05_semantic_consolidation/SAU-000006/semantic_element_comparator_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/05_semantic_consolidation/SAU-000006/semantic_relationship_comparator_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/05_semantic_consolidation/SAU-000007/semantic_element_comparator_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/05_semantic_consolidation/SAU-000007/semantic_relationship_comparator_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/05_semantic_consolidation/SAU-000008/semantic_element_comparator_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/05_semantic_consolidation/SAU-000009/semantic_element_comparator_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/05_semantic_consolidation/SAU-000009/semantic_relationship_comparator_run_01.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000001/team_legacy_interpretation_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000001/team_legacy_interpretation_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000002/team_legacy_interpretation_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000002/team_legacy_interpretation_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000003/team_legacy_interpretation_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000003/team_legacy_interpretation_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000004/team_legacy_interpretation_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000004/team_legacy_interpretation_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000005/team_legacy_interpretation_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000005/team_legacy_interpretation_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000006/team_legacy_interpretation_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000006/team_legacy_interpretation_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000007/team_legacy_interpretation_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000007/team_legacy_interpretation_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000008/team_legacy_interpretation_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000008/team_legacy_interpretation_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000009/team_legacy_interpretation_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000009/team_legacy_interpretation_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000010/team_legacy_interpretation_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000010/team_legacy_interpretation_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000011/team_legacy_interpretation_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000011/team_legacy_interpretation_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000012/team_legacy_interpretation_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000012/team_legacy_interpretation_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000013/team_legacy_interpretation_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/SAU-000013/team_legacy_interpretation_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000001/team_evidence_classification_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000001/team_evidence_classification_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000002/team_evidence_classification_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000002/team_evidence_classification_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000003/team_evidence_classification_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000003/team_evidence_classification_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000004/team_evidence_classification_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000004/team_evidence_classification_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000005/team_evidence_classification_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000005/team_evidence_classification_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000006/team_evidence_classification_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000006/team_evidence_classification_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000007/team_evidence_classification_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000007/team_evidence_classification_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000008/team_evidence_classification_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000008/team_evidence_classification_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000009/team_evidence_classification_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000009/team_evidence_classification_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000010/team_evidence_classification_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000010/team_evidence_classification_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000011/team_evidence_classification_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000011/team_evidence_classification_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000012/team_evidence_classification_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000012/team_evidence_classification_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000013/team_evidence_classification_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/SAU-000013/team_evidence_classification_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000001/team_derivation_assessment_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000001/team_derivation_assessment_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000002/team_derivation_assessment_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000002/team_derivation_assessment_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000003/team_derivation_assessment_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000003/team_derivation_assessment_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000004/team_derivation_assessment_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000004/team_derivation_assessment_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000005/team_derivation_assessment_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000005/team_derivation_assessment_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000006/team_derivation_assessment_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000006/team_derivation_assessment_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000007/team_derivation_assessment_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000007/team_derivation_assessment_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000008/team_derivation_assessment_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000008/team_derivation_assessment_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000009/team_derivation_assessment_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000009/team_derivation_assessment_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000010/team_derivation_assessment_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000010/team_derivation_assessment_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000011/team_derivation_assessment_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000011/team_derivation_assessment_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000012/team_derivation_assessment_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000012/team_derivation_assessment_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000013/team_derivation_assessment_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/03_derivation_assessment/SAU-000013/team_derivation_assessment_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/05_semantic_consolidation/SAU-000001/semantic_element_consolidation.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/05_semantic_consolidation/SAU-000002/semantic_element_consolidation.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/05_semantic_consolidation/SAU-000003/semantic_element_consolidation.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/05_semantic_consolidation/SAU-000004/semantic_element_consolidation.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/05_semantic_consolidation/SAU-000005/semantic_element_consolidation.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/05_semantic_consolidation/SAU-000006/semantic_element_consolidation.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/05_semantic_consolidation/SAU-000006/semantic_relationship_consolidation.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/05_semantic_consolidation/SAU-000007/semantic_element_consolidation.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/05_semantic_consolidation/SAU-000007/semantic_relationship_consolidation.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/05_semantic_consolidation/SAU-000008/semantic_element_consolidation.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/05_semantic_consolidation/SAU-000009/semantic_element_consolidation.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/05_semantic_consolidation/SAU-000009/semantic_relationship_consolidation.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/team_agentic_ingestion_run_summary.json
data/projects/081082/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/team_agentic_ingestion_run_summary.md
data/projects/081082/runs/RUN-000002/events/EVT-000001.json
data/projects/081082/runs/RUN-000002/events/EVT-000002.json
data/projects/081082/runs/RUN-000002/events/EVT-000003.json
data/projects/081082/runs/RUN-000002/run_manifest.json
data/projects/081082/runs/RUN-000002/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/081082/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/081082/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/081082/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/081082/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/081082/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/081082/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/source_preparation_result.json
data/projects/081082/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/subject_discovery/raw_responses/grounding_correction.json
data/projects/081082/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/subject_discovery/raw_responses/initial.json
data/projects/081082/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_binding_summary.json
data/projects/081082/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_review_input.json
data/projects/081082/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_semantic_consensus.json
data/projects/081082/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/081082/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/081082/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/081082/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/081082/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/081082/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/081082/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/081082/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/source_preparation_result.json
data/projects/081082/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/subject_discovery/raw_responses/initial.json
data/projects/081082/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/canonical_subject_set.json
data/projects/081082/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/shared_evidence_binding_summary.json
data/projects/081082/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/shared_evidence_review_input.json
data/projects/081082/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/shared_evidence_semantic_consensus.json
data/projects/081082/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/subject_consensus.json
data/projects/081082/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/subject_interpretations.json
data/projects/081082/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/subject_review_bundle.json
data/projects/081082/runs/RUN-000003/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/081082/runs/RUN-000003/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/081082/runs/RUN-000003/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/081082/runs/RUN-000003/events/EVT-000001.json
data/projects/081082/runs/RUN-000003/events/EVT-000002.json
data/projects/081082/runs/RUN-000003/events/EVT-000003.json
data/projects/081082/runs/RUN-000003/events/EVT-000004.json
data/projects/081082/runs/RUN-000003/run_manifest.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/source_preparation_result.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/subject_discovery/raw_responses/initial.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/canonical_subject_set.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_binding_summary.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_review_input.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_semantic_consensus.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/subject_consensus.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/subject_interpretations.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/subject_review_bundle.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_literal_interpreter/run_01.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/081082/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/081082/semantics/source_analysis_units/SAU-000001.json
data/projects/081082/semantics/source_analysis_units/SAU-000002.json
data/projects/081082/semantics/source_analysis_units/SAU-000003.json
data/projects/081082/semantics/source_analysis_units/SAU-000004.json
data/projects/081082/semantics/source_analysis_units/SAU-000005.json
data/projects/081082/semantics/source_analysis_units/SAU-000006.json
data/projects/081082/semantics/source_analysis_units/SAU-000007.json
data/projects/081082/semantics/source_analysis_units/SAU-000008.json
data/projects/081082/semantics/source_analysis_units/SAU-000009.json
data/projects/081082/semantics/source_analysis_units/SAU-000010.json
data/projects/081082/semantics/source_analysis_units/SAU-000011.json
data/projects/081082/semantics/source_analysis_units/SAU-000012.json
data/projects/081082/semantics/source_analysis_units/SAU-000013.json
data/projects/081082/semantics/source_analysis_units/SAU-000014.json
data/projects/081082/semantics/source_analysis_units/SAU-000015.json
data/projects/081082/semantics/source_analysis_units/SAU-000016.json
data/projects/081082/semantics/source_analysis_units/SAU-000017.json
data/projects/081082/semantics/source_analysis_units/SAU-000018.json
data/projects/081082/semantics/source_analysis_units/SAU-000019.json
data/projects/081082/semantics/source_analysis_units/SAU-000020.json
data/projects/081082/semantics/source_analysis_units/SAU-000021.json
data/projects/081082/semantics/source_analysis_units/SAU-000022.json
data/projects/081082/semantics/source_analysis_units/SAU-000023.json
data/projects/081082/semantics/source_analysis_units/SAU-000024.json
data/projects/081082/semantics/source_analysis_units/SAU-000025.json
data/projects/081082/semantics/source_analysis_units/SAU-000026.json
data/projects/081082/semantics/source_analysis_units/SAU-000027.json
data/projects/081082/semantics/source_analysis_units/SAU-000028.json
data/projects/081082/semantics/source_analysis_units/SAU-000029.json
data/projects/081082/semantics/source_analysis_units/SAU-000030.json
data/projects/081082/semantics/source_analysis_units/SAU-000031.json
data/projects/081082/semantics/source_analysis_units/SAU-000032.json
data/projects/081082/semantics/source_analysis_units/SAU-000033.json
data/projects/081082/semantics/source_analysis_units/SAU-000034.json
data/projects/081082/semantics/source_analysis_units/SAU-000035.json
data/projects/081082/semantics/source_analysis_units/SAU-000036.json
data/projects/081082/semantics/source_analysis_units/SAU-000037.json
data/projects/081082/semantics/source_analysis_units/SAU-000038.json
data/projects/081082/semantics/source_analysis_units/SAU-000039.json
data/projects/081082/semantics/source_analysis_units/SAU-000040.json
data/projects/081082/semantics/source_analysis_units/SAU-000041.json
data/projects/081082/semantics/source_evidence/EVD-000001.json
data/projects/081082/semantics/source_evidence/EVD-000002.json
data/projects/081082/semantics/source_evidence/EVD-000003.json
data/projects/081082/semantics/source_evidence/EVD-000004.json
data/projects/081082/semantics/source_evidence/EVD-000005.json
data/projects/081082/semantics/source_evidence/EVD-000006.json
data/projects/081082/semantics/source_evidence/EVD-000007.json
data/projects/081082/semantics/source_evidence/EVD-000008.json
data/projects/081082/semantics/source_evidence/EVD-000009.json
data/projects/081082/semantics/source_evidence/EVD-000010.json
data/projects/081082/semantics/source_evidence/EVD-000011.json
data/projects/081082/semantics/source_evidence/EVD-000012.json
data/projects/081082/semantics/source_evidence/EVD-000013.json
data/projects/081082/semantics/source_evidence/EVD-000014.json
data/projects/081082/semantics/source_evidence/EVD-000015.json
data/projects/081082/semantics/source_evidence/EVD-000016.json
data/projects/081082/semantics/source_evidence/EVD-000017.json
data/projects/081082/semantics/source_evidence/EVD-000018.json
data/projects/081082/semantics/source_evidence/EVD-000019.json
data/projects/081082/semantics/source_evidence/EVD-000020.json
data/projects/081082/semantics/source_evidence/EVD-000021.json
data/projects/081082/semantics/source_evidence/EVD-000022.json
data/projects/081082/semantics/source_evidence/EVD-000023.json
data/projects/081082/semantics/source_evidence/EVD-000024.json
data/projects/081082/semantics/source_evidence/EVD-000025.json
data/projects/081082/semantics/source_evidence/EVD-000026.json
data/projects/081082/semantics/source_evidence/EVD-000027.json
data/projects/081082/semantics/source_evidence/EVD-000028.json
data/projects/081082/semantics/source_preparation/SP-000002/0f70efc35ad7e57a30190b88a0a856d365a5da4712250516e9055fde5fe8f03e.json
data/projects/081082/semantics/source_preparation/SP-000003/b68e41df380e202dea36fdf2db2325fd1ce40711e58bdd27f778a8fa26181ca9.json
data/projects/081082/semantics/source_projections/SP-000001/content.txt
data/projects/081082/semantics/source_projections/SP-000001/projection.json
data/projects/081082/semantics/source_projections/SP-000002/content.txt
data/projects/081082/semantics/source_projections/SP-000002/projection.json
data/projects/081082/semantics/source_projections/SP-000003/content.txt
data/projects/081082/semantics/source_projections/SP-000003/projection.json
data/projects/081082/sources/SRC-000001/content.md
data/projects/081082/sources/SRC-000001/source_manifest.json
data/projects/081082/sources/SRC-000002/content.md
data/projects/081082/sources/SRC-000002/source_manifest.json
data/projects/081082/sources/SRC-000003/content.md
data/projects/081082/sources/SRC-000003/source_manifest.json
data/projects/120412/approved_inputs/manifests/AIN-000001.json
data/projects/120412/approved_inputs/manifests/AIN-000002.json
data/projects/120412/approved_inputs/manifests/AIN-000003.json
data/projects/120412/approved_inputs/manifests/AIN-000004.json
data/projects/120412/approved_inputs/manifests/AIN-000005.json
data/projects/120412/approved_inputs/manifests/AIN-000006.json
data/projects/120412/approved_inputs/manifests/AIN-000007.json
data/projects/120412/approved_inputs/manifests/AIN-000008.json
data/projects/120412/approved_inputs/manifests/AIN-000009.json
data/projects/120412/approved_inputs/manifests/AIN-000010.json
data/projects/120412/approved_inputs/manifests/AIN-000011.json
data/projects/120412/approved_inputs/manifests/AIN-000012.json
data/projects/120412/approved_inputs/manifests/AIN-000013.json
data/projects/120412/approved_inputs/manifests/AIN-000014.json
data/projects/120412/approved_inputs/manifests/AIN-000015.json
data/projects/120412/approved_inputs/manifests/AIN-000016.json
data/projects/120412/approved_inputs/manifests/AIN-000017.json
data/projects/120412/final_model_reviews/FMR-000001/decisions/FRD-000001.json
data/projects/120412/final_model_reviews/FMR-000001/manifest.json
data/projects/120412/final_model_reviews/FMR-000001/revisions/FRV-000001/artifact_set.json
data/projects/120412/final_model_reviews/FMR-000001/revisions/FRV-000001/generated/generated_model.sysml
data/projects/120412/final_model_reviews/FMR-000001/revisions/FRV-000001/revision.json
data/projects/120412/final_model_reviews/FMR-000001/revisions/FRV-000001/storage_manifest.json
data/projects/120412/final_model_reviews/FMR-000001/revisions/FRV-000001/validation_result.json
data/projects/120412/final_model_reviews/FMR-000001/revisions/FRV-000002/artifact_set.json
data/projects/120412/final_model_reviews/FMR-000001/revisions/FRV-000002/generated/generated_model.sysml
data/projects/120412/final_model_reviews/FMR-000001/revisions/FRV-000002/revision.json
data/projects/120412/final_model_reviews/FMR-000001/revisions/FRV-000002/storage_manifest.json
data/projects/120412/final_model_reviews/FMR-000001/revisions/FRV-000002/validation_result.json
data/projects/120412/generated_sysml_v2/IEM-000002/artifact_set.json
data/projects/120412/generated_sysml_v2/IEM-000002/generated/generated_model.sysml
data/projects/120412/internal_models_v2/IEM-000001/snapshot.json
data/projects/120412/internal_models_v2/IEM-000002/semantic_authority.json
data/projects/120412/internal_models_v2/IEM-000002/snapshot.json
data/projects/120412/model_assemblies/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/assembly_draft.json
data/projects/120412/model_assemblies/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/final_review/decisions/FAD-000001.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/approved_placement_set.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/comparison.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000001.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000002.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000003.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000004.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000005.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000006.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000007.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000008.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000009.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000010.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000011.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000012.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000013.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000014.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000015.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000016.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000017.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000018.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000019.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000020.json
data/projects/120412/model_placement_reviews/7105f23c2a534760137eb4dd0d775df8ae38c03b6b3419c5b702c1172ff8c1a8/decisions/MPD-000021.json
data/projects/120412/model_quality/authority_sets/MQA-000001.json
data/projects/120412/model_quality/decisions/MQD-000001.json
data/projects/120412/model_quality/decisions/MQD-000002.json
data/projects/120412/model_quality/decisions/MQD-000003.json
data/projects/120412/model_quality/decisions/MQD-000004.json
data/projects/120412/model_quality/decisions/MQD-000005.json
data/projects/120412/model_quality/decisions/MQD-000006.json
data/projects/120412/model_quality/decisions/MQD-000007.json
data/projects/120412/model_quality/decisions/MQD-000008.json
data/projects/120412/model_quality/decisions/MQD-000009.json
data/projects/120412/model_quality/decisions/MQD-000010.json
data/projects/120412/model_quality/decisions/MQD-000011.json
data/projects/120412/model_quality/decisions/MQD-000012.json
data/projects/120412/model_quality/decisions/MQD-000013.json
data/projects/120412/model_quality/reviews/MQR-000001/bundle.json
data/projects/120412/model_quality/reviews/MQR-000001/request.json
data/projects/120412/model_quality/runs/MQR-000001/batch_01/team_model_quality_refinement/agent_model_quality_refiner/agent_model_quality_refiner_run_01.json
data/projects/120412/model_quality/runs/MQR-000001/batch_02/team_model_quality_refinement/agent_model_quality_refiner/agent_model_quality_refiner_run_01.json
data/projects/120412/project_manifest.json
data/projects/120412/reviews/RVD-000001/review_document_manifest.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/finalized/effective_decisions.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/finalized/reviewed_document.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/finalized/reviewed_report.md
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/review_version_manifest.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000001.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000002.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000003.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000004.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000005.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000006.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000007.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000008.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000009.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000010.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000011.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000012.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000013.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000014.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000015.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000016.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000017.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000018.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000019.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000020.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000021.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000022.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000023.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000024.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000025.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000026.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000027.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000028.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000029.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000030.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000031.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000032.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000033.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000034.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000035.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000036.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000037.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000038.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000039.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000040.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000041.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000042.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000043.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000044.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000045.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000046.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000047.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000048.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000049.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000050.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000051.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000052.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000053.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000054.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000055.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000056.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000057.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000058.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000059.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000060.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000061.json
data/projects/120412/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000062.json
data/projects/120412/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/120412/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/120412/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/120412/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/120412/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/120412/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/120412/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/source_preparation_result.json
data/projects/120412/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/canonical_subject_set.json
data/projects/120412/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/shared_evidence_binding_summary.json
data/projects/120412/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/shared_evidence_review_input.json
data/projects/120412/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/shared_evidence_semantic_consensus.json
data/projects/120412/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/subject_consensus.json
data/projects/120412/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/subject_interpretations.json
data/projects/120412/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/subject_review_bundle.json
data/projects/120412/runs/RUN-000001/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/120412/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/120412/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/120412/runs/RUN-000001/events/EVT-000001.json
data/projects/120412/runs/RUN-000001/events/EVT-000002.json
data/projects/120412/runs/RUN-000001/events/EVT-000003.json
data/projects/120412/runs/RUN-000001/events/EVT-000004.json
data/projects/120412/runs/RUN-000001/run_manifest.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/source_preparation_result.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/canonical_subject_set.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_binding_summary.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_review_input.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_semantic_consensus.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/subject_consensus.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/subject_interpretations.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/subject_review_bundle.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_literal_interpreter/run_01.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/r4c_subject_interpretation/subject_interpretation/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/120412/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/120412/runs/RUN-000002/events/EVT-000001.json
data/projects/120412/runs/RUN-000002/events/EVT-000002.json
data/projects/120412/runs/RUN-000002/events/EVT-000003.json
data/projects/120412/runs/RUN-000002/run_manifest.json
data/projects/120412/runs/RUN-000002/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/120412/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/120412/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/120412/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/120412/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/120412/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/120412/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/120412/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/source_preparation_result.json
data/projects/120412/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_binding_summary.json
data/projects/120412/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_review_input.json
data/projects/120412/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/shared_evidence_semantic_consensus.json
data/projects/120412/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/120412/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/120412/semantics/human_reviews/HRD-000001.json
data/projects/120412/semantics/source_analysis_units/SAU-000001.json
data/projects/120412/semantics/source_analysis_units/SAU-000002.json
data/projects/120412/semantics/source_analysis_units/SAU-000003.json
data/projects/120412/semantics/source_analysis_units/SAU-000004.json
data/projects/120412/semantics/source_analysis_units/SAU-000005.json
data/projects/120412/semantics/source_analysis_units/SAU-000006.json
data/projects/120412/semantics/source_analysis_units/SAU-000007.json
data/projects/120412/semantics/source_analysis_units/SAU-000008.json
data/projects/120412/semantics/source_analysis_units/SAU-000009.json
data/projects/120412/semantics/source_analysis_units/SAU-000010.json
data/projects/120412/semantics/source_analysis_units/SAU-000011.json
data/projects/120412/semantics/source_analysis_units/SAU-000012.json
data/projects/120412/semantics/source_analysis_units/SAU-000013.json
data/projects/120412/semantics/source_analysis_units/SAU-000014.json
data/projects/120412/semantics/source_analysis_units/SAU-000015.json
data/projects/120412/semantics/source_analysis_units/SAU-000016.json
data/projects/120412/semantics/source_analysis_units/SAU-000017.json
data/projects/120412/semantics/source_analysis_units/SAU-000018.json
data/projects/120412/semantics/source_analysis_units/SAU-000019.json
data/projects/120412/semantics/source_analysis_units/SAU-000020.json
data/projects/120412/semantics/source_analysis_units/SAU-000021.json
data/projects/120412/semantics/source_analysis_units/SAU-000022.json
data/projects/120412/semantics/source_analysis_units/SAU-000023.json
data/projects/120412/semantics/source_analysis_units/SAU-000024.json
data/projects/120412/semantics/source_analysis_units/SAU-000025.json
data/projects/120412/semantics/source_analysis_units/SAU-000026.json
data/projects/120412/semantics/source_analysis_units/SAU-000027.json
data/projects/120412/semantics/source_analysis_units/SAU-000028.json
data/projects/120412/semantics/source_evidence/EVD-000001.json
data/projects/120412/semantics/source_evidence/EVD-000002.json
data/projects/120412/semantics/source_evidence/EVD-000003.json
data/projects/120412/semantics/source_evidence/EVD-000004.json
data/projects/120412/semantics/source_evidence/EVD-000005.json
data/projects/120412/semantics/source_evidence/EVD-000006.json
data/projects/120412/semantics/source_evidence/EVD-000007.json
data/projects/120412/semantics/source_evidence/EVD-000008.json
data/projects/120412/semantics/source_evidence/EVD-000009.json
data/projects/120412/semantics/source_evidence/EVD-000010.json
data/projects/120412/semantics/source_evidence/EVD-000011.json
data/projects/120412/semantics/source_evidence/EVD-000012.json
data/projects/120412/semantics/source_evidence/EVD-000013.json
data/projects/120412/semantics/source_evidence/EVD-000014.json
data/projects/120412/semantics/source_evidence/EVD-000015.json
data/projects/120412/semantics/source_evidence/EVD-000016.json
data/projects/120412/semantics/source_evidence/EVD-000017.json
data/projects/120412/semantics/source_evidence/EVD-000018.json
data/projects/120412/semantics/source_evidence/EVD-000019.json
data/projects/120412/semantics/source_evidence/EVD-000020.json
data/projects/120412/semantics/source_evidence/EVD-000021.json
data/projects/120412/semantics/source_evidence/EVD-000022.json
data/projects/120412/semantics/source_evidence/EVD-000023.json
data/projects/120412/semantics/source_evidence/EVD-000024.json
data/projects/120412/semantics/source_evidence/EVD-000025.json
data/projects/120412/semantics/source_evidence/EVD-000026.json
data/projects/120412/semantics/source_evidence/EVD-000027.json
data/projects/120412/semantics/source_evidence/EVD-000028.json
data/projects/120412/semantics/source_evidence/EVD-000029.json
data/projects/120412/semantics/source_evidence/EVD-000030.json
data/projects/120412/semantics/source_preparation/SP-000001/b68e41df380e202dea36fdf2db2325fd1ce40711e58bdd27f778a8fa26181ca9.json
data/projects/120412/semantics/source_preparation/SP-000002/0f70efc35ad7e57a30190b88a0a856d365a5da4712250516e9055fde5fe8f03e.json
data/projects/120412/semantics/source_projections/SP-000001/content.txt
data/projects/120412/semantics/source_projections/SP-000001/projection.json
data/projects/120412/semantics/source_projections/SP-000002/content.txt
data/projects/120412/semantics/source_projections/SP-000002/projection.json
data/projects/120412/sources/SRC-000001/content.md
data/projects/120412/sources/SRC-000001/source_manifest.json
data/projects/120412/sources/SRC-000002/content.md
data/projects/120412/sources/SRC-000002/source_manifest.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000001.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000002.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000003.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000004.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000005.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000006.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000007.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000008.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000009.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000010.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000011.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000012.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000013.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000014.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000015.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000016.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000017.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000018.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000019.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000020.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000021.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000022.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000023.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000024.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000025.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000026.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000027.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000028.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000029.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000030.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000031.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000032.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000033.json
data/projects/120412/subject_review_relationship_decisions/RVD-000001/RVV-000001/SRD-000034.json
data/projects/120412/sysml_validation_v2/IEM-000002/validation_result.json
data/projects/120412/target_model_formulation/authority_sets/TFA-000001.json
data/projects/120412/target_model_formulation/authority_sets/TFA-000002.json
data/projects/120412/target_model_formulation/authority_sets/TFA-000003.json
data/projects/120412/target_model_formulation/decisions/TFD-000001.json
data/projects/120412/target_model_formulation/decisions/TFD-000002.json
data/projects/120412/target_model_formulation/decisions/TFD-000003.json
data/projects/120412/target_model_formulation/decisions/TFD-000004.json
data/projects/120412/target_model_formulation/decisions/TFD-000005.json
data/projects/120412/target_model_formulation/decisions/TFD-000006.json
data/projects/120412/target_model_formulation/decisions/TFD-000007.json
data/projects/120412/target_model_formulation/decisions/TFD-000008.json
data/projects/120412/target_model_formulation/decisions/TFD-000009.json
data/projects/120412/target_model_formulation/decisions/TFD-000010.json
data/projects/120412/target_model_formulation/reviews/TFR-000001.json
data/projects/120412/work/model_assembly_generation/assembly_9nh9qn1c/relationship_projection/batch_01/persona_outputs/team_modeling_projection/agent_modeling_architecture_focused_advisor/agent_modeling_architecture_focused_advisor_run_01.json
data/projects/120412/work/model_assembly_generation/assembly_9nh9qn1c/relationship_projection/batch_01/persona_outputs/team_modeling_projection/agent_modeling_conservative_reviewer/agent_modeling_conservative_reviewer_run_01.json
data/projects/120412/work/model_assembly_generation/assembly_9nh9qn1c/relationship_projection/batch_01/persona_outputs/team_modeling_projection/agent_modeling_rules_focused_advisor/agent_modeling_rules_focused_advisor_run_01.json
data/projects/120412/work/model_candidate_generation/llm_assisted_b_2e53yz/batch_01/modeling_persona_consolidated.json
data/projects/120412/work/model_candidate_generation/llm_assisted_b_2e53yz/batch_01/persona_outputs/team_modeling_projection/agent_modeling_architecture_focused_advisor/agent_modeling_architecture_focused_advisor_run_01.json
data/projects/120412/work/model_candidate_generation/llm_assisted_b_2e53yz/batch_01/persona_outputs/team_modeling_projection/agent_modeling_conservative_reviewer/agent_modeling_conservative_reviewer_run_01.json
data/projects/120412/work/model_candidate_generation/llm_assisted_b_2e53yz/batch_01/persona_outputs/team_modeling_projection/agent_modeling_rules_focused_advisor/agent_modeling_rules_focused_advisor_run_01.json
data/projects/120412/work/model_candidate_generation/llm_assisted_b_2e53yz/batch_02/modeling_persona_consolidated.json
data/projects/120412/work/model_candidate_generation/llm_assisted_b_2e53yz/batch_02/persona_outputs/team_modeling_projection/agent_modeling_architecture_focused_advisor/agent_modeling_architecture_focused_advisor_run_01.json
data/projects/120412/work/model_candidate_generation/llm_assisted_b_2e53yz/batch_02/persona_outputs/team_modeling_projection/agent_modeling_conservative_reviewer/agent_modeling_conservative_reviewer_run_01.json
data/projects/120412/work/model_candidate_generation/llm_assisted_b_2e53yz/batch_02/persona_outputs/team_modeling_projection/agent_modeling_rules_focused_advisor/agent_modeling_rules_focused_advisor_run_01.json
data/projects/120412/work/model_placement_generation/placement_hkbx60r6/model_placement_execution.json
data/projects/120412/work/model_placement_generation/placement_hkbx60r6/persona_outputs/team_modeling_projection/agent_modeling_architecture_focused_advisor/agent_modeling_architecture_focused_advisor_run_01.json
data/projects/120412/work/model_placement_generation/placement_hkbx60r6/persona_outputs/team_modeling_projection/agent_modeling_conservative_reviewer/agent_modeling_conservative_reviewer_run_01.json
data/projects/120412/work/model_placement_generation/placement_hkbx60r6/persona_outputs/team_modeling_projection/agent_modeling_rules_focused_advisor/agent_modeling_rules_focused_advisor_run_01.json
data/projects/159161/project_manifest.json
data/projects/159161/runs/RUN-000001/events/EVT-000001.json
data/projects/159161/runs/RUN-000001/events/EVT-000002.json
data/projects/159161/runs/RUN-000001/events/EVT-000003.json
data/projects/159161/runs/RUN-000001/run_manifest.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_02.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_02.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_02.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/159161/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/159161/semantics/source_projections/SP-000001/content.txt
data/projects/159161/semantics/source_projections/SP-000001/projection.json
data/projects/159161/sources/SRC-000001/content.md
data/projects/159161/sources/SRC-000001/source_manifest.json
data/projects/203871/project_manifest.json
data/projects/203871/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/203871/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/203871/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/203871/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/203871/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/203871/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/203871/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/203871/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/203871/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/203871/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/203871/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/203871/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/203871/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/203871/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/203871/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/203871/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/203871/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/203871/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/203871/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.json
data/projects/203871/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.md
data/projects/203871/runs/RUN-000001/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/203871/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/203871/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/203871/runs/RUN-000001/events/EVT-000001.json
data/projects/203871/runs/RUN-000001/events/EVT-000002.json
data/projects/203871/runs/RUN-000001/events/EVT-000003.json
data/projects/203871/runs/RUN-000001/events/EVT-000004.json
data/projects/203871/runs/RUN-000001/run_manifest.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/203871/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/203871/semantics/source_projections/SP-000001/content.txt
data/projects/203871/semantics/source_projections/SP-000001/projection.json
data/projects/203871/sources/SRC-000001/content.pdf
data/projects/203871/sources/SRC-000001/source_manifest.json
data/projects/204530/project_manifest.json
data/projects/308131/project_manifest.json
data/projects/308131/reviews/RVD-000001/review_document_manifest.json
data/projects/308131/reviews/RVD-000001/versions/RVV-000001/review_version_manifest.json
data/projects/308131/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000001.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_02.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_02.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/308131/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_02.json
data/projects/308131/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/308131/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/308131/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/308131/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/308131/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/308131/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/308131/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.json
data/projects/308131/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.md
data/projects/308131/runs/RUN-000001/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/308131/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/308131/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/308131/runs/RUN-000001/events/EVT-000001.json
data/projects/308131/runs/RUN-000001/events/EVT-000002.json
data/projects/308131/runs/RUN-000001/events/EVT-000003.json
data/projects/308131/runs/RUN-000001/events/EVT-000004.json
data/projects/308131/runs/RUN-000001/run_manifest.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_02.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_02.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_02.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/308131/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/308131/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/308131/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/308131/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/308131/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/308131/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/308131/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/308131/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/308131/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/308131/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/308131/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/308131/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/308131/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/308131/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/308131/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/308131/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/308131/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/308131/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.json
data/projects/308131/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.md
data/projects/308131/runs/RUN-000002/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/308131/runs/RUN-000002/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/308131/runs/RUN-000002/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/308131/runs/RUN-000002/events/EVT-000001.json
data/projects/308131/runs/RUN-000002/events/EVT-000002.json
data/projects/308131/runs/RUN-000002/events/EVT-000003.json
data/projects/308131/runs/RUN-000002/events/EVT-000004.json
data/projects/308131/runs/RUN-000002/run_manifest.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/308131/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/308131/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/308131/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/308131/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/308131/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/308131/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/308131/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/308131/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/308131/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/308131/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/308131/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/308131/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/308131/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/308131/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/308131/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/308131/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/308131/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/308131/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.json
data/projects/308131/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.md
data/projects/308131/runs/RUN-000003/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/308131/runs/RUN-000003/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/308131/runs/RUN-000003/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/308131/runs/RUN-000003/events/EVT-000001.json
data/projects/308131/runs/RUN-000003/events/EVT-000002.json
data/projects/308131/runs/RUN-000003/events/EVT-000003.json
data/projects/308131/runs/RUN-000003/events/EVT-000004.json
data/projects/308131/runs/RUN-000003/run_manifest.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/308131/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/308131/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/308131/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/308131/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/308131/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/308131/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/308131/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/308131/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/308131/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/308131/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/308131/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/308131/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/308131/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/308131/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/308131/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/308131/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/308131/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/308131/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.json
data/projects/308131/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.md
data/projects/308131/runs/RUN-000004/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/308131/runs/RUN-000004/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/308131/runs/RUN-000004/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/308131/runs/RUN-000004/events/EVT-000001.json
data/projects/308131/runs/RUN-000004/events/EVT-000002.json
data/projects/308131/runs/RUN-000004/events/EVT-000003.json
data/projects/308131/runs/RUN-000004/events/EVT-000004.json
data/projects/308131/runs/RUN-000004/run_manifest.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/308131/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/308131/semantics/source_projections/SP-000001/content.txt
data/projects/308131/semantics/source_projections/SP-000001/projection.json
data/projects/308131/semantics/source_projections/SP-000002/content.txt
data/projects/308131/semantics/source_projections/SP-000002/projection.json
data/projects/308131/semantics/source_projections/SP-000003/content.txt
data/projects/308131/semantics/source_projections/SP-000003/projection.json
data/projects/308131/semantics/source_projections/SP-000004/content.txt
data/projects/308131/semantics/source_projections/SP-000004/projection.json
data/projects/308131/sources/SRC-000001/content.md
data/projects/308131/sources/SRC-000001/source_manifest.json
data/projects/308131/sources/SRC-000002/content.md
data/projects/308131/sources/SRC-000002/source_manifest.json
data/projects/308131/sources/SRC-000003/content.md
data/projects/308131/sources/SRC-000003/source_manifest.json
data/projects/308131/sources/SRC-000004/content.md
data/projects/308131/sources/SRC-000004/source_manifest.json
data/projects/334441/approved_inputs/manifests/AIN-000001.json
data/projects/334441/approved_inputs/manifests/AIN-000002.json
data/projects/334441/project_manifest.json
data/projects/334441/reviews/RVD-000001/review_document_manifest.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000001/finalized/effective_decisions.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000001/finalized/reviewed_document.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000001/finalized/reviewed_report.md
data/projects/334441/reviews/RVD-000001/versions/RVV-000001/review_version_manifest.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000001.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000002.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000003.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000004.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000005.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000006.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000007.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000008.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000002/review_version_manifest.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000002/revisions/RVR-000009.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000002/revisions/RVR-000010.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000002/revisions/RVR-000011.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000002/revisions/RVR-000012.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000002/revisions/RVR-000013.json
data/projects/334441/reviews/RVD-000001/versions/RVV-000002/scoped_actions/SRA-000001.json
data/projects/334441/reviews/RVD-000002/review_document_manifest.json
data/projects/334441/reviews/RVD-000002/versions/RVV-000001/review_version_manifest.json
data/projects/334441/reviews/RVD-000002/versions/RVV-000001/revisions/RVR-000001.json
data/projects/334441/reviews/RVD-000003/review_document_manifest.json
data/projects/334441/reviews/RVD-000003/versions/RVV-000001/review_version_manifest.json
data/projects/334441/reviews/RVD-000003/versions/RVV-000001/revisions/RVR-000001.json
data/projects/334441/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000003/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/334441/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000003/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/334441/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000003/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/334441/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000003/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/334441/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000003/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/334441/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000003/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/334441/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000003/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/334441/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000003/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/334441/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000003/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/334441/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000003/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/334441/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000003/04_completeness_review/team_completeness_review_consensus.json
data/projects/334441/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000003/04_completeness_review/team_completeness_review_consensus.md
data/projects/334441/runs/RUN-000001/artifacts/review_reports/agentic_ingestion/ATT-000003/ingestion_review_report.md
data/projects/334441/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000003/team_agentic_ingestion_run_summary.json
data/projects/334441/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000003/team_agentic_ingestion_run_summary.md
data/projects/334441/runs/RUN-000001/events/EVT-000001.json
data/projects/334441/runs/RUN-000001/events/EVT-000002.json
data/projects/334441/runs/RUN-000001/events/EVT-000003.json
data/projects/334441/runs/RUN-000001/events/EVT-000004.json
data/projects/334441/runs/RUN-000001/events/EVT-000005.json
data/projects/334441/runs/RUN-000001/events/EVT-000006.json
data/projects/334441/runs/RUN-000001/events/EVT-000007.json
data/projects/334441/runs/RUN-000001/events/EVT-000008.json
data/projects/334441/runs/RUN-000001/run_manifest.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000002/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000003/ingestion_review_report.md
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/team_agentic_ingestion_run_summary.json
data/projects/334441/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/team_agentic_ingestion_run_summary.md
data/projects/334441/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_a/agent_01.json
data/projects/334441/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_b/agent_01.json
data/projects/334441/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/consensus.json
data/projects/334441/runs/RUN-000002/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/334441/runs/RUN-000002/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/334441/runs/RUN-000002/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/334441/runs/RUN-000002/events/EVT-000001.json
data/projects/334441/runs/RUN-000002/events/EVT-000002.json
data/projects/334441/runs/RUN-000002/events/EVT-000003.json
data/projects/334441/runs/RUN-000002/events/EVT-000004.json
data/projects/334441/runs/RUN-000002/run_manifest.json
data/projects/334441/runs/RUN-000002/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/334441/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_a/agent_01.json
data/projects/334441/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_b/agent_01.json
data/projects/334441/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment/consensus.json
data/projects/334441/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/334441/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/334441/runs/RUN-000003/events/EVT-000001.json
data/projects/334441/runs/RUN-000003/events/EVT-000002.json
data/projects/334441/runs/RUN-000003/events/EVT-000003.json
data/projects/334441/runs/RUN-000003/run_manifest.json
data/projects/334441/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/334441/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/334441/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/334441/runs/RUN-000004/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/334441/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/334441/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/334441/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/334441/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/334441/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/334441/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/334441/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.json
data/projects/334441/runs/RUN-000004/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.md
data/projects/334441/runs/RUN-000004/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/334441/runs/RUN-000004/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/334441/runs/RUN-000004/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/334441/runs/RUN-000004/events/EVT-000001.json
data/projects/334441/runs/RUN-000004/events/EVT-000002.json
data/projects/334441/runs/RUN-000004/events/EVT-000003.json
data/projects/334441/runs/RUN-000004/events/EVT-000004.json
data/projects/334441/runs/RUN-000004/run_manifest.json
data/projects/334441/runs/RUN-000004/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/334441/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/334441/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/334441/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/334441/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/334441/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/334441/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/334441/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/334441/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/334441/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/334441/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/334441/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/projects/334441/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/projects/334441/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/334441/runs/RUN-000004/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/334441/semantics/human_reviews/HRD-000001.json
data/projects/334441/semantics/source_projections/SP-000001/content.txt
data/projects/334441/semantics/source_projections/SP-000001/projection.json
data/projects/334441/semantics/source_projections/SP-000002/content.txt
data/projects/334441/semantics/source_projections/SP-000002/projection.json
data/projects/334441/semantics/source_projections/SP-000003/content.txt
data/projects/334441/semantics/source_projections/SP-000003/projection.json
data/projects/334441/sources/SRC-000001/content.md
data/projects/334441/sources/SRC-000001/source_manifest.json
data/projects/334441/sources/SRC-000002/content.md
data/projects/334441/sources/SRC-000002/source_manifest.json
data/projects/334441/sources/SRC-000003/content.csv
data/projects/334441/sources/SRC-000003/source_manifest.json
data/projects/334441/sources/SRC-000004/content.md
data/projects/334441/sources/SRC-000004/source_manifest.json
data/projects/396272/project_manifest.json
data/projects/396272/reviews/RVD-000001/review_document_manifest.json
data/projects/396272/reviews/RVD-000001/versions/RVV-000001/review_version_manifest.json
data/projects/396272/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000001.json
data/projects/396272/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000003/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/396272/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000003/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/396272/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000003/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/396272/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000003/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/396272/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000003/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/396272/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000003/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/396272/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000003/source_preparation_result.json
data/projects/396272/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000003/shared_evidence_binding_summary.json
data/projects/396272/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000003/shared_evidence_review_input.json
data/projects/396272/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000003/shared_evidence_semantic_consensus.json
data/projects/396272/runs/RUN-000001/artifacts/review_reports/agentic_ingestion/ATT-000003/ingestion_review_report.md
data/projects/396272/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000003/team_agentic_ingestion_run_summary.json
data/projects/396272/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000003/team_agentic_ingestion_run_summary.md
data/projects/396272/runs/RUN-000001/events/EVT-000001.json
data/projects/396272/runs/RUN-000001/events/EVT-000002.json
data/projects/396272/runs/RUN-000001/events/EVT-000003.json
data/projects/396272/runs/RUN-000001/events/EVT-000004.json
data/projects/396272/runs/RUN-000001/events/EVT-000005.json
data/projects/396272/runs/RUN-000001/events/EVT-000006.json
data/projects/396272/runs/RUN-000001/events/EVT-000007.json
data/projects/396272/runs/RUN-000001/events/EVT-000008.json
data/projects/396272/runs/RUN-000001/run_manifest.json
data/projects/396272/runs/RUN-000001/work/agentic_ingestion/ATT-000003/ingestion_review_report.md
data/projects/396272/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/396272/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/396272/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/raw_team_runs/team_source_evidence_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/396272/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/semantic_extraction/agent_legacy_literal_interpreter/run_01.json
data/projects/396272/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/semantic_extraction/agent_legacy_skeptical_ambiguity_interpreter/run_01.json
data/projects/396272/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/semantic_extraction/agent_legacy_systems_engineering_interpreter/run_01.json
data/projects/396272/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/agent_outputs/source_preparation_result.json
data/projects/396272/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/shared_evidence_binding_summary.json
data/projects/396272/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/shared_evidence_review_input.json
data/projects/396272/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/consensus_reports/shared_evidence_semantic_consensus.json
data/projects/396272/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/team_agentic_ingestion_run_summary.json
data/projects/396272/runs/RUN-000001/work/agentic_ingestion/ATT-000003/phase_f/team_agentic_ingestion_run_summary.md
data/projects/396272/semantics/source_analysis_units/SAU-000001.json
data/projects/396272/semantics/source_analysis_units/SAU-000002.json
data/projects/396272/semantics/source_analysis_units/SAU-000003.json
data/projects/396272/semantics/source_analysis_units/SAU-000004.json
data/projects/396272/semantics/source_analysis_units/SAU-000005.json
data/projects/396272/semantics/source_analysis_units/SAU-000006.json
data/projects/396272/semantics/source_analysis_units/SAU-000007.json
data/projects/396272/semantics/source_analysis_units/SAU-000008.json
data/projects/396272/semantics/source_analysis_units/SAU-000009.json
data/projects/396272/semantics/source_analysis_units/SAU-000010.json
data/projects/396272/semantics/source_analysis_units/SAU-000011.json
data/projects/396272/semantics/source_evidence/EVD-000001.json
data/projects/396272/semantics/source_evidence/EVD-000002.json
data/projects/396272/semantics/source_evidence/EVD-000003.json
data/projects/396272/semantics/source_evidence/EVD-000004.json
data/projects/396272/semantics/source_evidence/EVD-000005.json
data/projects/396272/semantics/source_evidence/EVD-000006.json
data/projects/396272/semantics/source_evidence/EVD-000007.json
data/projects/396272/semantics/source_evidence/EVD-000008.json
data/projects/396272/semantics/source_evidence/EVD-000009.json
data/projects/396272/semantics/source_evidence/EVD-000010.json
data/projects/396272/semantics/source_preparation/SP-000001/b68e41df380e202dea36fdf2db2325fd1ce40711e58bdd27f778a8fa26181ca9.json
data/projects/396272/semantics/source_projections/SP-000001/content.txt
data/projects/396272/semantics/source_projections/SP-000001/projection.json
data/projects/396272/sources/SRC-000001/content.md
data/projects/396272/sources/SRC-000001/source_manifest.json
data/projects/458990/project_manifest.json
data/projects/458990/runs/RUN-000001/events/EVT-000001.json
data/projects/458990/runs/RUN-000001/events/EVT-000002.json
data/projects/458990/runs/RUN-000001/events/EVT-000003.json
data/projects/458990/runs/RUN-000001/run_manifest.json
data/projects/458990/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/458990/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/458990/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/458990/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/458990/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/458990/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/458990/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/458990/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/458990/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/458990/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/458990/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.json
data/projects/458990/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.md
data/projects/458990/runs/RUN-000002/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/458990/runs/RUN-000002/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/458990/runs/RUN-000002/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/458990/runs/RUN-000002/events/EVT-000001.json
data/projects/458990/runs/RUN-000002/events/EVT-000002.json
data/projects/458990/runs/RUN-000002/events/EVT-000003.json
data/projects/458990/runs/RUN-000002/events/EVT-000004.json
data/projects/458990/runs/RUN-000002/run_manifest.json
data/projects/458990/runs/RUN-000002/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/458990/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/458990/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/458990/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/458990/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/458990/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/458990/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/458990/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/458990/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/458990/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/458990/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/458990/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/projects/458990/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/projects/458990/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/458990/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/458990/semantics/source_projections/SP-000001/content.txt
data/projects/458990/semantics/source_projections/SP-000001/projection.json
data/projects/458990/sources/SRC-000001/content.csv
data/projects/458990/sources/SRC-000001/source_manifest.json
data/projects/458990/sources/SRC-000002/content.txt
data/projects/458990/sources/SRC-000002/source_manifest.json
data/projects/691616/project_manifest.json
data/projects/691616/runs/RUN-000001/events/EVT-000001.json
data/projects/691616/runs/RUN-000001/events/EVT-000002.json
data/projects/691616/runs/RUN-000001/events/EVT-000003.json
data/projects/691616/runs/RUN-000001/run_manifest.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000001/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000001/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000001/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000001/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000001/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000001/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000002/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000002/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000002/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000002/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000002/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000002/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000003/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000003/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000003/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000003/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000003/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000003/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000004/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000004/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000004/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000004/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000004/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000004/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000005/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000005/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000005/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000005/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000005/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000005/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000006/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000006/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000006/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000006/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000006/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000006/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000007/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000007/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000007/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000007/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000007/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000007/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000008/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000008/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000008/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000008/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000008/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000008/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000009/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000009/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000009/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000009/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000009/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000009/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000010/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000010/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000010/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000010/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000010/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000010/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000011/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000011/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000011/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000011/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000011/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000011/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000001/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000001/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000001/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000001/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000001/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000001/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000002/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000002/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000002/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000002/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000002/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000002/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000003/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000003/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000003/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000003/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000003/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000003/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000004/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000004/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000004/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000004/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000004/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000004/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000005/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000005/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000005/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000005/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000005/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000005/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000006/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000006/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000006/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000006/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000006/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000006/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000007/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000007/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000007/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000007/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000007/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000007/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000008/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000008/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000008/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000008/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000008/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000008/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000009/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000009/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000009/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000009/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000009/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000009/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000010/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000010/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000010/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000010/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000010/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000010/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000011/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000011/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000011/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000011/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000011/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000011/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000001/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000001/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000001/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000001/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000001/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000001/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000002/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000002/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000002/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000002/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000002/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000002/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000003/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000003/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000003/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000003/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000003/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000003/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000004/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000004/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000004/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000004/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000004/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000004/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000005/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000005/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000005/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000005/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000005/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000005/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000006/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000006/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000006/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000006/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000006/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000006/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000007/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000007/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000007/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000007/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000007/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000007/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000008/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000008/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000008/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000008/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000008/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000008/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000009/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000009/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000009/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000009/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000009/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000009/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000010/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000010/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000010/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000010/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000010/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000010/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000011/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000011/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000011/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000011/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000011/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000011/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000001/team_legacy_interpretation_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000001/team_legacy_interpretation_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000002/team_legacy_interpretation_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000002/team_legacy_interpretation_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000003/team_legacy_interpretation_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000003/team_legacy_interpretation_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000004/team_legacy_interpretation_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000004/team_legacy_interpretation_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000005/team_legacy_interpretation_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000005/team_legacy_interpretation_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000006/team_legacy_interpretation_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000006/team_legacy_interpretation_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000007/team_legacy_interpretation_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000007/team_legacy_interpretation_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000008/team_legacy_interpretation_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000008/team_legacy_interpretation_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000009/team_legacy_interpretation_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000009/team_legacy_interpretation_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000010/team_legacy_interpretation_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000010/team_legacy_interpretation_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000011/team_legacy_interpretation_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000011/team_legacy_interpretation_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000001/team_evidence_classification_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000001/team_evidence_classification_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000002/team_evidence_classification_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000002/team_evidence_classification_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000003/team_evidence_classification_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000003/team_evidence_classification_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000004/team_evidence_classification_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000004/team_evidence_classification_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000005/team_evidence_classification_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000005/team_evidence_classification_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000006/team_evidence_classification_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000006/team_evidence_classification_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000007/team_evidence_classification_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000007/team_evidence_classification_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000008/team_evidence_classification_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000008/team_evidence_classification_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000009/team_evidence_classification_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000009/team_evidence_classification_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000010/team_evidence_classification_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000010/team_evidence_classification_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000011/team_evidence_classification_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000011/team_evidence_classification_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000001/team_derivation_assessment_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000001/team_derivation_assessment_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000002/team_derivation_assessment_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000002/team_derivation_assessment_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000003/team_derivation_assessment_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000003/team_derivation_assessment_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000004/team_derivation_assessment_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000004/team_derivation_assessment_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000005/team_derivation_assessment_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000005/team_derivation_assessment_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000006/team_derivation_assessment_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000006/team_derivation_assessment_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000007/team_derivation_assessment_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000007/team_derivation_assessment_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000008/team_derivation_assessment_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000008/team_derivation_assessment_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000009/team_derivation_assessment_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000009/team_derivation_assessment_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000010/team_derivation_assessment_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000010/team_derivation_assessment_consensus.md
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000011/team_derivation_assessment_consensus.json
data/projects/691616/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000011/team_derivation_assessment_consensus.md
data/projects/691616/semantics/source_analysis_units/SAU-000001.json
data/projects/691616/semantics/source_analysis_units/SAU-000002.json
data/projects/691616/semantics/source_analysis_units/SAU-000003.json
data/projects/691616/semantics/source_analysis_units/SAU-000004.json
data/projects/691616/semantics/source_analysis_units/SAU-000005.json
data/projects/691616/semantics/source_analysis_units/SAU-000006.json
data/projects/691616/semantics/source_analysis_units/SAU-000007.json
data/projects/691616/semantics/source_analysis_units/SAU-000008.json
data/projects/691616/semantics/source_analysis_units/SAU-000009.json
data/projects/691616/semantics/source_analysis_units/SAU-000010.json
data/projects/691616/semantics/source_analysis_units/SAU-000011.json
data/projects/691616/semantics/source_projections/SP-000001/content.txt
data/projects/691616/semantics/source_projections/SP-000001/projection.json
data/projects/691616/sources/SRC-000001/content.md
data/projects/691616/sources/SRC-000001/source_manifest.json
data/projects/856871/project_manifest.json
data/projects/856871/sources/SRC-000001/content.csv
data/projects/856871/sources/SRC-000001/source_manifest.json
data/projects/876577/project_manifest.json
data/projects/876577/reviews/RVD-000001/review_document_manifest.json
data/projects/876577/reviews/RVD-000001/versions/RVV-000001/review_version_manifest.json
data/projects/876577/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000001.json
data/projects/876577/runs/RUN-000001/events/EVT-000001.json
data/projects/876577/runs/RUN-000001/events/EVT-000002.json
data/projects/876577/runs/RUN-000001/events/EVT-000003.json
data/projects/876577/runs/RUN-000001/run_manifest.json
data/projects/876577/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/876577/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/876577/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/876577/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/876577/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/876577/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/876577/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/876577/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/876577/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/876577/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/876577/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/876577/runs/RUN-000002/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/876577/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/876577/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/876577/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/876577/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/876577/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/876577/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/876577/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.json
data/projects/876577/runs/RUN-000002/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.md
data/projects/876577/runs/RUN-000002/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/876577/runs/RUN-000002/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/876577/runs/RUN-000002/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/876577/runs/RUN-000002/events/EVT-000001.json
data/projects/876577/runs/RUN-000002/events/EVT-000002.json
data/projects/876577/runs/RUN-000002/events/EVT-000003.json
data/projects/876577/runs/RUN-000002/events/EVT-000004.json
data/projects/876577/runs/RUN-000002/run_manifest.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/876577/runs/RUN-000002/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/876577/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/876577/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/876577/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/876577/runs/RUN-000003/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/876577/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/876577/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/876577/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/876577/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/876577/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/876577/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/876577/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.json
data/projects/876577/runs/RUN-000003/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.md
data/projects/876577/runs/RUN-000003/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/876577/runs/RUN-000003/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/876577/runs/RUN-000003/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/876577/runs/RUN-000003/events/EVT-000001.json
data/projects/876577/runs/RUN-000003/events/EVT-000002.json
data/projects/876577/runs/RUN-000003/events/EVT-000003.json
data/projects/876577/runs/RUN-000003/events/EVT-000004.json
data/projects/876577/runs/RUN-000003/run_manifest.json
data/projects/876577/runs/RUN-000003/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/876577/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/876577/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/876577/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/876577/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/876577/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/876577/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/876577/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/876577/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/876577/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/876577/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/876577/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/projects/876577/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/projects/876577/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/876577/runs/RUN-000003/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/876577/semantics/source_projections/SP-000001/content.txt
data/projects/876577/semantics/source_projections/SP-000001/projection.json
data/projects/876577/semantics/source_projections/SP-000002/content.txt
data/projects/876577/semantics/source_projections/SP-000002/projection.json
data/projects/876577/sources/SRC-000001/content.csv
data/projects/876577/sources/SRC-000001/source_manifest.json
data/projects/876577/sources/SRC-000002/content.txt
data/projects/876577/sources/SRC-000002/source_manifest.json
data/projects/876577/sources/SRC-000003/content.pdf
data/projects/876577/sources/SRC-000003/source_manifest.json
data/projects/877791/project_manifest.json
data/projects/877791/reviews/RVD-000001/review_document_manifest.json
data/projects/877791/reviews/RVD-000001/versions/RVV-000001/review_version_manifest.json
data/projects/877791/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000001.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000001/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000001/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000001/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000002/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000002/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000002/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000003/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000003/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000003/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000004/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000004/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000004/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000005/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000005/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000005/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000006/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000006/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000006/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000007/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000007/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000007/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000008/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000008/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000008/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000009/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000009/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000009/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000010/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000010/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000010/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000011/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000011/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000011/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000001/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000001/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000001/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000002/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000002/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000002/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000003/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000003/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000003/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000004/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000004/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000004/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000005/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000005/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000005/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000006/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000006/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000006/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000007/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000007/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000007/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000008/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000008/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000008/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000009/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000009/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000009/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000010/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000010/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000010/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000011/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000011/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000011/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000001/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000001/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000001/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000002/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000002/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000002/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000003/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000003/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000003/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000004/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000004/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000004/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000005/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000005/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000005/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000006/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000006/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000006/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000007/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000007/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000007/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000008/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000008/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000008/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000009/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000009/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000009/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000010/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000010/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000010/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000011/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000011/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000011/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000001/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000002/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000002/semantic_relationship_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000003/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000004/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000005/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000005/semantic_relationship_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000006/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000006/semantic_relationship_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000007/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000007/semantic_relationship_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000008/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000008/semantic_relationship_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000010/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000011/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/06_cross_unit_synthesis/cross_unit_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/06_cross_unit_synthesis/cross_unit_relationship_comparator_run_01.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000001/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000001/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000002/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000002/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000003/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000003/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000004/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000004/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000005/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000005/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000006/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000006/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000007/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000007/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000008/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000008/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000009/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000009/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000010/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000010/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000011/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/SAU-000011/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000001/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000001/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000002/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000002/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000003/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000003/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000004/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000004/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000005/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000005/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000006/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000006/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000007/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000007/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000008/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000008/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000009/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000009/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000010/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000010/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000011/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/SAU-000011/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000001/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000001/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000002/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000002/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000003/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000003/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000004/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000004/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000005/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000005/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000006/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000006/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000007/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000007/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000008/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000008/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000009/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000009/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000010/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000010/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000011/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/SAU-000011/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.md
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000001/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000002/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000002/semantic_relationship_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000003/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000004/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000005/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000005/semantic_relationship_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000006/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000006/semantic_relationship_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000007/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000007/semantic_relationship_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000008/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000008/semantic_relationship_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000009/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000010/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/05_semantic_consolidation/SAU-000011/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/06_cross_unit_synthesis/cross_unit_semantic_synthesis.json
data/projects/877791/runs/RUN-000001/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/877791/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/877791/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/877791/runs/RUN-000001/events/EVT-000001.json
data/projects/877791/runs/RUN-000001/events/EVT-000002.json
data/projects/877791/runs/RUN-000001/events/EVT-000003.json
data/projects/877791/runs/RUN-000001/events/EVT-000004.json
data/projects/877791/runs/RUN-000001/run_manifest.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000001/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000001/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000001/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000002/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000002/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000002/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000003/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000003/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000003/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000004/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000004/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000004/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000005/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000005/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000005/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000006/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000006/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000006/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000007/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000007/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000007/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000008/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000008/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000008/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000009/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000009/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000009/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000010/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000010/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000010/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000011/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000011/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/SAU-000011/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000001/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000001/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000001/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000002/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000002/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000002/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000003/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000003/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000003/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000004/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000004/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000004/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000005/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000005/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000005/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000006/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000006/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000006/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000007/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000007/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000007/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000008/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000008/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000008/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000009/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000009/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000009/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000010/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000010/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000010/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000011/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000011/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/SAU-000011/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000001/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000001/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000001/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000002/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000002/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000002/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000003/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000003/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000003/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000004/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000004/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000004/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000005/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000005/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000005/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000006/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000006/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000006/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000007/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000007/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000007/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000008/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000008/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000008/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000009/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000009/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000009/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000010/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000010/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000010/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000011/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000011/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/SAU-000011/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/SAU-000001/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/SAU-000002/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/SAU-000002/semantic_relationship_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/SAU-000003/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/SAU-000004/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/SAU-000005/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/SAU-000005/semantic_relationship_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/SAU-000006/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/SAU-000006/semantic_relationship_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/SAU-000007/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/SAU-000007/semantic_relationship_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/SAU-000008/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/SAU-000008/semantic_relationship_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/SAU-000010/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/SAU-000011/semantic_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/06_cross_unit_synthesis/cross_unit_element_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/06_cross_unit_synthesis/cross_unit_relationship_comparator_run_01.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000001/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000001/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000002/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000002/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000003/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000003/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000004/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000004/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000005/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000005/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000006/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000006/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000007/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000007/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000008/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000008/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000009/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000009/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000010/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000010/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000011/team_legacy_interpretation_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/SAU-000011/team_legacy_interpretation_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000001/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000001/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000002/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000002/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000003/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000003/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000004/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000004/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000005/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000005/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000006/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000006/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000007/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000007/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000008/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000008/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000009/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000009/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000010/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000010/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000011/team_evidence_classification_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/SAU-000011/team_evidence_classification_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000001/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000001/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000002/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000002/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000003/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000003/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000004/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000004/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000005/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000005/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000006/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000006/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000007/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000007/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000008/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000008/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000009/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000009/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000010/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000010/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000011/team_derivation_assessment_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/SAU-000011/team_derivation_assessment_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000001/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000002/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000002/semantic_relationship_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000003/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000004/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000005/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000005/semantic_relationship_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000006/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000006/semantic_relationship_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000007/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000007/semantic_relationship_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000008/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000008/semantic_relationship_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000009/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000010/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/05_semantic_consolidation/SAU-000011/semantic_element_consolidation.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/06_cross_unit_synthesis/cross_unit_semantic_synthesis.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/877791/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/877791/semantics/source_analysis_units/SAU-000001.json
data/projects/877791/semantics/source_analysis_units/SAU-000002.json
data/projects/877791/semantics/source_analysis_units/SAU-000003.json
data/projects/877791/semantics/source_analysis_units/SAU-000004.json
data/projects/877791/semantics/source_analysis_units/SAU-000005.json
data/projects/877791/semantics/source_analysis_units/SAU-000006.json
data/projects/877791/semantics/source_analysis_units/SAU-000007.json
data/projects/877791/semantics/source_analysis_units/SAU-000008.json
data/projects/877791/semantics/source_analysis_units/SAU-000009.json
data/projects/877791/semantics/source_analysis_units/SAU-000010.json
data/projects/877791/semantics/source_analysis_units/SAU-000011.json
data/projects/877791/semantics/source_projections/SP-000001/content.txt
data/projects/877791/semantics/source_projections/SP-000001/projection.json
data/projects/877791/sources/SRC-000001/content.md
data/projects/877791/sources/SRC-000001/source_manifest.json
data/projects/887027/project_manifest.json
data/projects/887027/reviews/RVD-000001/review_document_manifest.json
data/projects/887027/reviews/RVD-000001/versions/RVV-000001/review_version_manifest.json
data/projects/887027/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000001.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_02.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_02.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_02.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/semantic_element_comparator_run_01.json
data/projects/887027/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/05_semantic_consolidation/semantic_relationship_comparator_run_01.json
data/projects/887027/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/887027/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/887027/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/887027/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/887027/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/887027/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/887027/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.json
data/projects/887027/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.md
data/projects/887027/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/semantic_element_consolidation.json
data/projects/887027/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/semantic_relationship_consolidation.json
data/projects/887027/runs/RUN-000001/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/887027/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/887027/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/887027/runs/RUN-000001/events/EVT-000001.json
data/projects/887027/runs/RUN-000001/events/EVT-000002.json
data/projects/887027/runs/RUN-000001/events/EVT-000003.json
data/projects/887027/runs/RUN-000001/events/EVT-000004.json
data/projects/887027/runs/RUN-000001/run_manifest.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_02.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_02.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_02.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/semantic_element_comparator_run_01.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/05_semantic_consolidation/semantic_relationship_comparator_run_01.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/semantic_element_consolidation.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/semantic_relationship_consolidation.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/887027/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/887027/semantics/source_projections/SP-000001/content.txt
data/projects/887027/semantics/source_projections/SP-000001/projection.json
data/projects/887027/sources/SRC-000001/content.md
data/projects/887027/sources/SRC-000001/source_manifest.json
data/projects/965294/project_manifest.json
data/projects/965294/reviews/RVD-000001/review_document_manifest.json
data/projects/965294/reviews/RVD-000001/versions/RVV-000001/review_version_manifest.json
data/projects/965294/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000001.json
data/projects/965294/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000002.json
data/projects/965294/reviews/RVD-000001/versions/RVV-000001/revisions/RVR-000003.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_02.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_02.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/965294/runs/RUN-000001/artifacts/agent_outputs/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_02.json
data/projects/965294/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/965294/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/965294/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/965294/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/965294/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/965294/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/965294/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.json
data/projects/965294/runs/RUN-000001/artifacts/consensus_reports/agentic_ingestion/ATT-000001/04_completeness_review/team_completeness_review_consensus.md
data/projects/965294/runs/RUN-000001/artifacts/review_reports/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/965294/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.json
data/projects/965294/runs/RUN-000001/artifacts/run_summaries/agentic_ingestion/ATT-000001/team_agentic_ingestion_run_summary.md
data/projects/965294/runs/RUN-000001/events/EVT-000001.json
data/projects/965294/runs/RUN-000001/events/EVT-000002.json
data/projects/965294/runs/RUN-000001/events/EVT-000003.json
data/projects/965294/runs/RUN-000001/events/EVT-000004.json
data/projects/965294/runs/RUN-000001/run_manifest.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/ingestion_review_report.md
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_02.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_02.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_02.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_02.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_02.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_02.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_02.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_02.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_02.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_02.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_02.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_02.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.json
data/projects/965294/runs/RUN-000001/work/agentic_ingestion/ATT-000001/phase_f/team_agentic_ingestion_run_summary.md
data/projects/965294/semantics/source_projections/SP-000001/content.txt
data/projects/965294/semantics/source_projections/SP-000001/projection.json
data/projects/965294/sources/SRC-000001/content.md
data/projects/965294/sources/SRC-000001/source_manifest.json
data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260721T094243Z/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260721T094243Z/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260721T094243Z/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260721T094243Z/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260721T094243Z/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260721T094243Z/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260721T094243Z/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260721T094243Z/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260721T094243Z/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260721T094243Z/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260721T094243Z/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260721T094243Z/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260721T094243Z/team_agentic_ingestion_run_summary.json
data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260721T094243Z/team_agentic_ingestion_run_summary.md
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T095140Z/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T095140Z/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T095140Z/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T095140Z/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T095140Z/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T095140Z/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T095140Z/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T095140Z/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T095140Z/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T095140Z/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T095140Z/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T095140Z/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T095140Z/team_agentic_ingestion_run_summary.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T095140Z/team_agentic_ingestion_run_summary.md
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T113937Z/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T113937Z/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T113937Z/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T113937Z/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T113937Z/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T113937Z/consensus_reports/01_legacy_interpretation/team_legacy_interpretation_consensus.md
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T113937Z/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T113937Z/consensus_reports/02_evidence_classification/team_evidence_classification_consensus.md
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T113937Z/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T113937Z/consensus_reports/03_derivation_assessment/team_derivation_assessment_consensus.md
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T113937Z/consensus_reports/04_completeness_review/team_completeness_review_consensus.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T113937Z/consensus_reports/04_completeness_review/team_completeness_review_consensus.md
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T113937Z/team_agentic_ingestion_run_summary.json
data/team_runs/TASK_INGEST_EXAMPLE_LEGACY_MODEL_DESCRIPTION/20260721T113937Z/team_agentic_ingestion_run_summary.md
f1_1_update.patch
f2_ui_polish.patch
f2_ui_polish_ui_only.patch
g2_ssot_update.patch
g7_failed_run_diagnostic.zip
legacy/.DS_Store
legacy/demo/.DS_Store
modules/.DS_Store
modules/approved_engineering_information/__pycache__/__init__.cpython-313.pyc
modules/approved_engineering_information/__pycache__/projection.cpython-313.pyc
modules/approved_input/__pycache__/__init__.cpython-313.pyc
modules/approved_input/__pycache__/eligibility.cpython-313.pyc
modules/approved_input/__pycache__/errors.cpython-313.pyc
modules/approved_input/__pycache__/event_manifest.cpython-313.pyc
modules/approved_input/__pycache__/identifiers.cpython-313.pyc
modules/approved_input/__pycache__/lifecycle.cpython-313.pyc
modules/approved_input/__pycache__/lifecycle_service.cpython-313.pyc
modules/approved_input/__pycache__/manifest.cpython-313.pyc
modules/approved_input/__pycache__/paths.cpython-313.pyc
modules/approved_input/__pycache__/promotion_materialization.cpython-313.pyc
modules/approved_input/__pycache__/promotion_plan.cpython-313.pyc
modules/approved_input/__pycache__/promotion_service.cpython-313.pyc
modules/approved_input/__pycache__/repository.cpython-313.pyc
modules/approved_input/__pycache__/repository_scan.cpython-313.pyc
modules/approved_input/__pycache__/types.cpython-313.pyc
modules/classification_alignment/__init__.py
modules/classification_alignment/__pycache__/__init__.cpython-313.pyc
modules/classification_alignment/__pycache__/contract.cpython-313.pyc
modules/classification_alignment/__pycache__/errors.cpython-313.pyc
modules/classification_alignment/__pycache__/prompt.cpython-313.pyc
modules/classification_alignment/__pycache__/serialization.cpython-313.pyc
modules/classification_alignment/__pycache__/service.cpython-313.pyc
modules/classification_alignment/__pycache__/types.cpython-313.pyc
modules/classification_alignment/contract.py
modules/classification_alignment/errors.py
modules/classification_alignment/prompt.py
modules/classification_alignment/serialization.py
modules/classification_alignment/service.py
modules/classification_alignment/types.py
modules/engineering_subjects/__pycache__/__init__.cpython-313.pyc
modules/engineering_subjects/__pycache__/context.cpython-313.pyc
modules/engineering_subjects/__pycache__/contract.cpython-313.pyc
modules/engineering_subjects/__pycache__/discovery.cpython-313.pyc
modules/engineering_subjects/__pycache__/errors.cpython-313.pyc
modules/engineering_subjects/__pycache__/grounding.cpython-313.pyc
modules/engineering_subjects/__pycache__/identifiers.cpython-313.pyc
modules/engineering_subjects/__pycache__/prompt.cpython-313.pyc
modules/engineering_subjects/__pycache__/types.cpython-313.pyc
modules/engineering_subjects/grounding.py
modules/evidence_detection/__pycache__/__init__.cpython-313.pyc
modules/evidence_detection/__pycache__/candidate_spans.cpython-313.pyc
modules/evidence_detection/__pycache__/detector.cpython-313.pyc
modules/evidence_detection/__pycache__/errors.cpython-313.pyc
modules/evidence_detection/__pycache__/prompt.cpython-313.pyc
modules/evidence_detection/__pycache__/types.cpython-313.pyc
modules/evidence_interpretation/__pycache__/__init__.cpython-313.pyc
modules/evidence_interpretation/__pycache__/contract.cpython-313.pyc
modules/evidence_interpretation/__pycache__/errors.cpython-313.pyc
modules/evidence_interpretation/__pycache__/pipeline.cpython-313.pyc
modules/evidence_interpretation/__pycache__/prompt.cpython-313.pyc
modules/evidence_interpretation/__pycache__/review_input.cpython-313.pyc
modules/evidence_interpretation/__pycache__/types.cpython-313.pyc
modules/final_model_review/__pycache__/__init__.cpython-313.pyc
modules/final_model_review/__pycache__/change_proposal.cpython-313.pyc
modules/final_model_review/__pycache__/change_workflow.cpython-313.pyc
modules/final_model_review/__pycache__/contracts.cpython-313.pyc
modules/final_model_review/__pycache__/errors.cpython-313.pyc
modules/final_model_review/__pycache__/fingerprints.cpython-313.pyc
modules/final_model_review/__pycache__/identifiers.cpython-313.pyc
modules/final_model_review/__pycache__/paths.cpython-313.pyc
modules/final_model_review/__pycache__/read_model.cpython-313.pyc
modules/final_model_review/__pycache__/release_gate.cpython-313.pyc
modules/final_model_review/__pycache__/release_service.cpython-313.pyc
modules/final_model_review/__pycache__/repository.cpython-313.pyc
modules/final_model_review/__pycache__/serialization.cpython-313.pyc
modules/final_model_review/__pycache__/types.cpython-313.pyc
modules/framework/__pycache__/__init__.cpython-313.pyc
modules/framework/__pycache__/template.cpython-313.pyc
modules/framework_assignment/__pycache__/__init__.cpython-313.pyc
modules/framework_assignment/__pycache__/agent_manifest.cpython-313.pyc
modules/framework_assignment/__pycache__/analyzer.cpython-313.pyc
modules/framework_assignment/__pycache__/candidate_manifest.cpython-313.pyc
modules/framework_assignment/__pycache__/errors.cpython-313.pyc
modules/framework_assignment/__pycache__/identifiers.cpython-313.pyc
modules/framework_assignment/__pycache__/reference_validation.cpython-313.pyc
modules/framework_assignment/__pycache__/repository.cpython-313.pyc
modules/framework_assignment/__pycache__/types.cpython-313.pyc
modules/guided_workflow/__pycache__/__init__.cpython-313.pyc
modules/guided_workflow/__pycache__/detail_read_model.cpython-313.pyc
modules/guided_workflow/__pycache__/errors.cpython-313.pyc
modules/guided_workflow/__pycache__/model_proposal_presentation.cpython-313.pyc
modules/guided_workflow/__pycache__/presentation.cpython-313.pyc
modules/guided_workflow/__pycache__/processing_review_presentation.cpython-313.pyc
modules/guided_workflow/__pycache__/read_model.cpython-313.pyc
modules/guided_workflow/__pycache__/types.cpython-313.pyc
modules/guided_workflow/__pycache__/write_service.cpython-313.pyc
modules/human_review/__pycache__/__init__.cpython-313.pyc
modules/human_review/__pycache__/errors.cpython-313.pyc
modules/human_review/__pycache__/identifiers.cpython-313.pyc
modules/human_review/__pycache__/manifest.cpython-313.pyc
modules/human_review/__pycache__/repository.cpython-313.pyc
modules/human_review/__pycache__/token_budget.cpython-313.pyc
modules/human_review/__pycache__/types.cpython-313.pyc
modules/information_units/__pycache__/__init__.cpython-313.pyc
modules/information_units/__pycache__/errors.cpython-313.pyc
modules/information_units/__pycache__/identifiers.cpython-313.pyc
modules/information_units/__pycache__/manifest.cpython-313.pyc
modules/information_units/__pycache__/repository.cpython-313.pyc
modules/information_units/__pycache__/types.cpython-313.pyc
modules/ingestion/.DS_Store
modules/internal_model/__pycache__/__init__.cpython-313.pyc
modules/internal_model/__pycache__/_manifest_support.cpython-313.pyc
modules/internal_model/__pycache__/assembly.cpython-313.pyc
modules/internal_model/__pycache__/assembly_input.cpython-313.pyc
modules/internal_model/__pycache__/assembly_rules.cpython-313.pyc
modules/internal_model/__pycache__/authority_backed.cpython-313.pyc
modules/internal_model/__pycache__/element_manifest.cpython-313.pyc
modules/internal_model/__pycache__/errors.cpython-313.pyc
modules/internal_model/__pycache__/identifiers.cpython-313.pyc
modules/internal_model/__pycache__/model_manifest.cpython-313.pyc
modules/internal_model/__pycache__/paths.cpython-313.pyc
modules/internal_model/__pycache__/persistence_service.cpython-313.pyc
modules/internal_model/__pycache__/phase_j_read_service.cpython-313.pyc
modules/internal_model/__pycache__/relationship_manifest.cpython-313.pyc
modules/internal_model/__pycache__/repository.cpython-313.pyc
modules/internal_model/__pycache__/repository_errors.cpython-313.pyc
modules/internal_model/__pycache__/repository_integrity.cpython-313.pyc
modules/internal_model/__pycache__/repository_scan.cpython-313.pyc
modules/internal_model/__pycache__/repository_types.cpython-313.pyc
modules/internal_model/__pycache__/semantic_successor.cpython-313.pyc
modules/internal_model/__pycache__/structure_manifest.cpython-313.pyc
modules/internal_model/__pycache__/structure_materialization.cpython-313.pyc
modules/internal_model/__pycache__/types.cpython-313.pyc
modules/llm/__pycache__/progress.cpython-313.pyc
modules/model_assembly/__pycache__/__init__.cpython-313.pyc
modules/model_assembly/__pycache__/builder.cpython-313.pyc
modules/model_assembly/__pycache__/final_review.cpython-313.pyc
modules/model_assembly/__pycache__/repository.cpython-313.pyc
modules/model_assembly/__pycache__/types.cpython-313.pyc
modules/model_candidates/__pycache__/__init__.cpython-313.pyc
modules/model_candidates/__pycache__/_manifest_support.cpython-313.pyc
modules/model_candidates/__pycache__/approved_engineering_deriver.cpython-313.pyc
modules/model_candidates/__pycache__/candidate_review_identifiers.cpython-313.pyc
modules/model_candidates/__pycache__/candidate_review_manifest.cpython-313.pyc
modules/model_candidates/__pycache__/candidate_review_paths.cpython-313.pyc
modules/model_candidates/__pycache__/candidate_review_repository.cpython-313.pyc
modules/model_candidates/__pycache__/candidate_set_manifest.cpython-313.pyc
modules/model_candidates/__pycache__/derivation_context.cpython-313.pyc
modules/model_candidates/__pycache__/derivation_strategy.cpython-313.pyc
modules/model_candidates/__pycache__/derivation_workflow.cpython-313.pyc
modules/model_candidates/__pycache__/element_manifest.cpython-313.pyc
modules/model_candidates/__pycache__/errors.cpython-313.pyc
modules/model_candidates/__pycache__/generation.cpython-313.pyc
modules/model_candidates/__pycache__/hybrid_deriver.cpython-313.pyc
modules/model_candidates/__pycache__/identifiers.cpython-313.pyc
modules/model_candidates/__pycache__/llm_projection_contract.cpython-313.pyc
modules/model_candidates/__pycache__/llm_projection_executor.cpython-313.pyc
modules/model_candidates/__pycache__/model_proposal.cpython-313.pyc
modules/model_candidates/__pycache__/modeling_persona_executor.cpython-313.pyc
modules/model_candidates/__pycache__/paths.cpython-313.pyc
modules/model_candidates/__pycache__/phase_i_read_service.cpython-313.pyc
modules/model_candidates/__pycache__/profile_deriver.cpython-313.pyc
modules/model_candidates/__pycache__/projection_resolver.cpython-313.pyc
modules/model_candidates/__pycache__/relationship_manifest.cpython-313.pyc
modules/model_candidates/__pycache__/repository.cpython-313.pyc
modules/model_candidates/__pycache__/repository_scan.cpython-313.pyc
modules/model_candidates/__pycache__/semantic_relationship_projection.cpython-313.pyc
modules/model_candidates/__pycache__/structure_profile.cpython-313.pyc
modules/model_candidates/__pycache__/types.cpython-313.pyc
modules/model_placement/__pycache__/__init__.cpython-313.pyc
modules/model_placement/__pycache__/approved_set.cpython-313.pyc
modules/model_placement/__pycache__/comparison.cpython-313.pyc
modules/model_placement/__pycache__/errors.cpython-313.pyc
modules/model_placement/__pycache__/persona_executor.cpython-313.pyc
modules/model_placement/__pycache__/request_builder.cpython-313.pyc
modules/model_placement/__pycache__/review_identifiers.cpython-313.pyc
modules/model_placement/__pycache__/review_repository.cpython-313.pyc
modules/model_placement/__pycache__/review_serialization.cpython-313.pyc
modules/model_placement/__pycache__/review_types.cpython-313.pyc
modules/model_placement/__pycache__/types.cpython-313.pyc
modules/model_quality/__pycache__/__init__.cpython-313.pyc
modules/model_quality/__pycache__/authority.cpython-313.pyc
modules/model_quality/__pycache__/contract.cpython-313.pyc
modules/model_quality/__pycache__/errors.cpython-313.pyc
modules/model_quality/__pycache__/executor.cpython-313.pyc
modules/model_quality/__pycache__/repository.cpython-313.pyc
modules/model_quality/__pycache__/serde.cpython-313.pyc
modules/model_quality/__pycache__/service.cpython-313.pyc
modules/model_quality/__pycache__/types.cpython-313.pyc
modules/output_publication/__pycache__/__init__.cpython-313.pyc
modules/output_publication/__pycache__/errors.cpython-313.pyc
modules/output_publication/__pycache__/final_review_publication.cpython-313.pyc
modules/output_publication/__pycache__/identifiers.cpython-313.pyc
modules/output_publication/__pycache__/manifest.cpython-313.pyc
modules/output_publication/__pycache__/output_profile.cpython-313.pyc
modules/output_publication/__pycache__/paths.cpython-313.pyc
modules/output_publication/__pycache__/repository.cpython-313.pyc
modules/output_publication/__pycache__/types.cpython-313.pyc
modules/output_publication/__pycache__/writer.cpython-313.pyc
modules/project_coverage/__pycache__/__init__.cpython-313.pyc
modules/project_coverage/__pycache__/coverage.cpython-313.pyc
modules/project_coverage/__pycache__/errors.cpython-313.pyc
modules/project_coverage/__pycache__/evidence.cpython-313.pyc
modules/project_coverage/__pycache__/profile.cpython-313.pyc
modules/project_coverage/__pycache__/service.cpython-313.pyc
modules/project_coverage/__pycache__/support.cpython-313.pyc
modules/project_coverage/__pycache__/types.cpython-313.pyc
modules/project_dashboard/__pycache__/__init__.cpython-313.pyc
modules/project_dashboard/__pycache__/errors.cpython-313.pyc
modules/project_dashboard/__pycache__/presenter.cpython-313.pyc
modules/project_dashboard/__pycache__/references.cpython-313.pyc
modules/project_dashboard/__pycache__/service.cpython-313.pyc
modules/project_dashboard/__pycache__/types.cpython-313.pyc
modules/project_dashboard/__pycache__/viewer.cpython-313.pyc
modules/project_glossary/__pycache__/__init__.cpython-313.pyc
modules/project_glossary/__pycache__/decision_manifest.cpython-313.pyc
modules/project_glossary/__pycache__/errors.cpython-313.pyc
modules/project_glossary/__pycache__/identifiers.cpython-313.pyc
modules/project_glossary/__pycache__/manifest.cpython-313.pyc
modules/project_glossary/__pycache__/normalization.cpython-313.pyc
modules/project_glossary/__pycache__/repository.cpython-313.pyc
modules/project_glossary/__pycache__/types.cpython-313.pyc
modules/project_ingestion/__pycache__/__init__.cpython-313.pyc
modules/project_ingestion/__pycache__/configuration.cpython-313.pyc
modules/project_ingestion/__pycache__/errors.cpython-313.pyc
modules/project_ingestion/__pycache__/failure_classification.cpython-313.pyc
modules/project_ingestion/__pycache__/publisher.cpython-313.pyc
modules/project_ingestion/__pycache__/service.cpython-313.pyc
modules/project_ingestion/__pycache__/types.cpython-313.pyc
modules/project_processing/__pycache__/__init__.cpython-313.pyc
modules/project_processing/__pycache__/aggregation.cpython-313.pyc
modules/project_processing/__pycache__/artifact_lifecycle.cpython-313.pyc
modules/project_processing/__pycache__/decision_manifest.cpython-313.pyc
modules/project_processing/__pycache__/errors.cpython-313.pyc
modules/project_processing/__pycache__/event_manifest.cpython-313.pyc
modules/project_processing/__pycache__/history.cpython-313.pyc
modules/project_processing/__pycache__/identifiers.cpython-313.pyc
modules/project_processing/__pycache__/operations.cpython-313.pyc
modules/project_processing/__pycache__/paths.cpython-313.pyc
modules/project_processing/__pycache__/repository.cpython-313.pyc
modules/project_processing/__pycache__/run_lifecycle.cpython-313.pyc
modules/project_processing/__pycache__/run_manifest.cpython-313.pyc
modules/project_processing/__pycache__/service.cpython-313.pyc
modules/project_processing/__pycache__/types.cpython-313.pyc
modules/project_sources/__pycache__/__init__.cpython-313.pyc
modules/project_sources/__pycache__/errors.cpython-313.pyc
modules/project_sources/__pycache__/identifiers.cpython-313.pyc
modules/project_sources/__pycache__/manifest.cpython-313.pyc
modules/project_sources/__pycache__/registry.cpython-313.pyc
modules/project_sources/__pycache__/types.cpython-313.pyc
modules/project_workspace/__pycache__/__init__.cpython-313.pyc
modules/project_workspace/__pycache__/errors.cpython-313.pyc
modules/project_workspace/__pycache__/identifiers.cpython-313.pyc
modules/project_workspace/__pycache__/manifest.cpython-313.pyc
modules/project_workspace/__pycache__/types.cpython-313.pyc
modules/project_workspace/__pycache__/workspace.cpython-313.pyc
modules/review_workspace/__pycache__/__init__.cpython-313.pyc
modules/review_workspace/__pycache__/document_manifest.cpython-313.pyc
modules/review_workspace/__pycache__/effective_decisions_manifest.cpython-313.pyc
modules/review_workspace/__pycache__/errors.cpython-313.pyc
modules/review_workspace/__pycache__/evidence_adapter.cpython-313.pyc
modules/review_workspace/__pycache__/finalization_authorization.cpython-313.pyc
modules/review_workspace/__pycache__/finalization_validation.cpython-313.pyc
modules/review_workspace/__pycache__/finalization_workflow.cpython-313.pyc
modules/review_workspace/__pycache__/finalized_artifact_set.cpython-313.pyc
modules/review_workspace/__pycache__/identifiers.cpython-313.pyc
modules/review_workspace/__pycache__/item_manifest.cpython-313.pyc
modules/review_workspace/__pycache__/open_question_resolution.cpython-313.pyc
modules/review_workspace/__pycache__/p4_evidence_adapter.cpython-313.pyc
modules/review_workspace/__pycache__/p4_evidence_reference_adapter.cpython-313.pyc
modules/review_workspace/__pycache__/p4_review_item_builder.cpython-313.pyc
modules/review_workspace/__pycache__/p9_evidence_reference_adapter.cpython-313.pyc
modules/review_workspace/__pycache__/p9_proposal_adapter.cpython-313.pyc
modules/review_workspace/__pycache__/p9_review_admissibility_adapter.cpython-313.pyc
modules/review_workspace/__pycache__/p9_review_item_builder.cpython-313.pyc
modules/review_workspace/__pycache__/paths.cpython-313.pyc
modules/review_workspace/__pycache__/promotion_workflow.cpython-313.pyc
modules/review_workspace/__pycache__/proposal_detail.cpython-313.pyc
modules/review_workspace/__pycache__/reopening.cpython-313.pyc
modules/review_workspace/__pycache__/repository.cpython-313.pyc
modules/review_workspace/__pycache__/resolution_candidates.cpython-313.pyc
modules/review_workspace/__pycache__/review_document_assembly.cpython-313.pyc
modules/review_workspace/__pycache__/reviewed_document_manifest.cpython-313.pyc
modules/review_workspace/__pycache__/reviewed_report_renderer.cpython-313.pyc
modules/review_workspace/__pycache__/revision_manifest.cpython-313.pyc
modules/review_workspace/__pycache__/scoped_action_manifest.cpython-313.pyc
modules/review_workspace/__pycache__/scoped_workflow.cpython-313.pyc
modules/review_workspace/__pycache__/semantic_review_projection.cpython-313.pyc
modules/review_workspace/__pycache__/shared_evidence_review_adapter.cpython-313.pyc
modules/review_workspace/__pycache__/subject_review_artifact_adapter.cpython-313.pyc
modules/review_workspace/__pycache__/types.cpython-313.pyc
modules/review_workspace/__pycache__/version_manifest.cpython-313.pyc
modules/review_workspace/__pycache__/workflow_editing.cpython-313.pyc
modules/review_workspace/__pycache__/workflow_lineage.cpython-313.pyc
modules/review_workspace/__pycache__/workflow_service.cpython-313.pyc
modules/review_workspace/__pycache__/workflow_types.cpython-313.pyc
modules/semantic_consensus/__pycache__/__init__.cpython-313.pyc
modules/semantic_consensus/__pycache__/analyzer.cpython-313.pyc
modules/semantic_consensus/__pycache__/errors.cpython-313.pyc
modules/semantic_consensus/__pycache__/identifiers.cpython-313.pyc
modules/semantic_consensus/__pycache__/manifest.cpython-313.pyc
modules/semantic_consensus/__pycache__/normalization.cpython-313.pyc
modules/semantic_consensus/__pycache__/publication.cpython-313.pyc
modules/semantic_consensus/__pycache__/types.cpython-313.pyc
modules/semantic_consistency_alignment/__init__.py
modules/semantic_consistency_alignment/__pycache__/__init__.cpython-313.pyc
modules/semantic_consistency_alignment/__pycache__/contract.cpython-313.pyc
modules/semantic_consistency_alignment/__pycache__/errors.cpython-313.pyc
modules/semantic_consistency_alignment/__pycache__/prompt.cpython-313.pyc
modules/semantic_consistency_alignment/__pycache__/serialization.cpython-313.pyc
modules/semantic_consistency_alignment/__pycache__/service.cpython-313.pyc
modules/semantic_consistency_alignment/__pycache__/types.cpython-313.pyc
modules/semantic_consistency_alignment/contract.py
modules/semantic_consistency_alignment/errors.py
modules/semantic_consistency_alignment/prompt.py
modules/semantic_consistency_alignment/serialization.py
modules/semantic_consistency_alignment/service.py
modules/semantic_consistency_alignment/types.py
modules/semantic_consolidation/__pycache__/__init__.cpython-313.pyc
modules/semantic_consolidation/__pycache__/artifact.cpython-313.pyc
modules/semantic_consolidation/__pycache__/cross_unit_synthesis.cpython-313.pyc
modules/semantic_consolidation/__pycache__/element_clustering.cpython-313.pyc
modules/semantic_consolidation/__pycache__/errors.cpython-313.pyc
modules/semantic_consolidation/__pycache__/processing_adapter.cpython-313.pyc
modules/semantic_consolidation/__pycache__/relationship_clustering.cpython-313.pyc
modules/semantic_consolidation/__pycache__/types.cpython-313.pyc
modules/semantic_extraction/__pycache__/__init__.cpython-313.pyc
modules/semantic_extraction/__pycache__/errors.cpython-313.pyc
modules/semantic_extraction/__pycache__/identifiers.cpython-313.pyc
modules/semantic_extraction/__pycache__/manifest.cpython-313.pyc
modules/semantic_extraction/__pycache__/types.cpython-313.pyc
modules/semantics/__pycache__/__init__.cpython-313.pyc
modules/semantics/__pycache__/errors.cpython-313.pyc
modules/semantics/__pycache__/reference_index.cpython-313.pyc
modules/semantics/__pycache__/registry.cpython-313.pyc
modules/semantics/__pycache__/turing_core.cpython-313.pyc
modules/semantics/__pycache__/types.cpython-313.pyc
modules/semantics/__pycache__/validation.cpython-313.pyc
modules/source_analysis_units/__pycache__/__init__.cpython-313.pyc
modules/source_analysis_units/__pycache__/errors.cpython-313.pyc
modules/source_analysis_units/__pycache__/identifiers.cpython-313.pyc
modules/source_analysis_units/__pycache__/manifest.cpython-313.pyc
modules/source_analysis_units/__pycache__/repository.cpython-313.pyc
modules/source_analysis_units/__pycache__/types.cpython-313.pyc
modules/source_evidence/__pycache__/__init__.cpython-313.pyc
modules/source_evidence/__pycache__/errors.cpython-313.pyc
modules/source_evidence/__pycache__/identifiers.cpython-313.pyc
modules/source_evidence/__pycache__/manifest.cpython-313.pyc
modules/source_evidence/__pycache__/repository.cpython-313.pyc
modules/source_evidence/__pycache__/types.cpython-313.pyc
modules/source_preparation/__pycache__/__init__.cpython-313.pyc
modules/source_preparation/__pycache__/service.cpython-313.pyc
modules/source_preparation/__pycache__/types.cpython-313.pyc
modules/source_projection/__pycache__/errors.cpython-313.pyc
modules/source_projection/__pycache__/identifiers.cpython-313.pyc
modules/source_projection/__pycache__/json_adapter.cpython-313.pyc
modules/source_projection/__pycache__/manifest.cpython-313.pyc
modules/source_projection/__pycache__/pdf_adapter.cpython-313.pyc
modules/source_projection/__pycache__/repository.cpython-313.pyc
modules/source_projection/__pycache__/table_adapter.cpython-313.pyc
modules/source_projection/__pycache__/text_adapter.cpython-313.pyc
modules/source_projection/__pycache__/types.cpython-313.pyc
modules/subject_consensus/__pycache__/__init__.cpython-313.pyc
modules/subject_consensus/__pycache__/analyzer.cpython-313.pyc
modules/subject_consensus/__pycache__/errors.cpython-313.pyc
modules/subject_consensus/__pycache__/types.cpython-313.pyc
modules/subject_interpretation/__pycache__/__init__.cpython-313.pyc
modules/subject_interpretation/__pycache__/contract.cpython-313.pyc
modules/subject_interpretation/__pycache__/errors.cpython-313.pyc
modules/subject_interpretation/__pycache__/pipeline.cpython-313.pyc
modules/subject_interpretation/__pycache__/prompt.cpython-313.pyc
modules/subject_interpretation/__pycache__/reference_context.cpython-313.pyc
modules/subject_interpretation/__pycache__/repair.cpython-313.pyc
modules/subject_interpretation/__pycache__/types.cpython-313.pyc
modules/subject_review/__pycache__/__init__.cpython-313.pyc
modules/subject_review/__pycache__/artifacts.cpython-313.pyc
modules/subject_review/__pycache__/decisions.cpython-313.pyc
modules/subject_review/__pycache__/errors.cpython-313.pyc
modules/subject_review/__pycache__/governance.cpython-313.pyc
modules/subject_review/__pycache__/projection.cpython-313.pyc
modules/subject_review/__pycache__/relationship_decisions.cpython-313.pyc
modules/subject_review/__pycache__/types.cpython-313.pyc
modules/sysml_generation/__pycache__/__init__.cpython-313.pyc
modules/sysml_generation/__pycache__/artifact_builder.cpython-313.pyc
modules/sysml_generation/__pycache__/artifact_structure.cpython-313.pyc
modules/sysml_generation/__pycache__/authority_backed.cpython-313.pyc
modules/sysml_generation/__pycache__/element_renderer.cpython-313.pyc
modules/sysml_generation/__pycache__/errors.cpython-313.pyc
modules/sysml_generation/__pycache__/fingerprints.cpython-313.pyc
modules/sysml_generation/__pycache__/generation_profile.cpython-313.pyc
modules/sysml_generation/__pycache__/generator_rules.cpython-313.pyc
modules/sysml_generation/__pycache__/identifiers.cpython-313.pyc
modules/sysml_generation/__pycache__/preflight.cpython-313.pyc
modules/sysml_generation/__pycache__/profile_support.cpython-313.pyc
modules/sysml_generation/__pycache__/projection.cpython-313.pyc
modules/sysml_generation/__pycache__/projection_types.cpython-313.pyc
modules/sysml_generation/__pycache__/relationship_renderer.cpython-313.pyc
modules/sysml_generation/__pycache__/service.cpython-313.pyc
modules/sysml_generation/__pycache__/target_notation.cpython-313.pyc
modules/sysml_generation/__pycache__/text_safety.cpython-313.pyc
modules/sysml_generation/__pycache__/types.cpython-313.pyc
modules/sysml_validation/__pycache__/__init__.cpython-313.pyc
modules/sysml_validation/__pycache__/artifact_integrity.cpython-313.pyc
modules/sysml_validation/__pycache__/artifact_structure_validator.cpython-313.pyc
modules/sysml_validation/__pycache__/authority_backed.cpython-313.pyc
modules/sysml_validation/__pycache__/errors.cpython-313.pyc
modules/sysml_validation/__pycache__/external_validator.cpython-313.pyc
modules/sysml_validation/__pycache__/finding_support.cpython-313.pyc
modules/sysml_validation/__pycache__/fingerprints.cpython-313.pyc
modules/sysml_validation/__pycache__/phase_l_gate.cpython-313.pyc
modules/sysml_validation/__pycache__/relationship_validator.cpython-313.pyc
modules/sysml_validation/__pycache__/service.cpython-313.pyc
modules/sysml_validation/__pycache__/syside_cli.cpython-313.pyc
modules/sysml_validation/__pycache__/target_notation_validator.cpython-313.pyc
modules/sysml_validation/__pycache__/traceability.cpython-313.pyc
modules/sysml_validation/__pycache__/types.cpython-313.pyc
modules/sysml_validation/__pycache__/validation_context.cpython-313.pyc
modules/sysml_validation/__pycache__/validation_profile.cpython-313.pyc
modules/target_model_formulation/__pycache__/__init__.cpython-313.pyc
modules/target_model_formulation/__pycache__/authority.cpython-313.pyc
modules/target_model_formulation/__pycache__/contract.cpython-313.pyc
modules/target_model_formulation/__pycache__/errors.cpython-313.pyc
modules/target_model_formulation/__pycache__/evidence.cpython-313.pyc
modules/target_model_formulation/__pycache__/live_review.cpython-313.pyc
modules/target_model_formulation/__pycache__/proposals.cpython-313.pyc
modules/target_model_formulation/__pycache__/repository.cpython-313.pyc
modules/target_model_formulation/__pycache__/types.cpython-313.pyc
modules/terminology_mapping/__pycache__/__init__.cpython-313.pyc
modules/terminology_mapping/__pycache__/agent_manifest.cpython-313.pyc
modules/terminology_mapping/__pycache__/analyzer.cpython-313.pyc
modules/terminology_mapping/__pycache__/candidate_manifest.cpython-313.pyc
modules/terminology_mapping/__pycache__/errors.cpython-313.pyc
modules/terminology_mapping/__pycache__/identifiers.cpython-313.pyc
modules/terminology_mapping/__pycache__/reference_validation.cpython-313.pyc
modules/terminology_mapping/__pycache__/repository.cpython-313.pyc
modules/terminology_mapping/__pycache__/types.cpython-313.pyc
scripts/__pycache__/regenerate_review_report_f1_test.cpython-313-pytest-9.1.1.pyc
scripts/__pycache__/test_consensus_dry_run.cpython-313-pytest-9.1.1.pyc
scripts/__pycache__/test_consensus_synthetic.cpython-313-pytest-9.1.1.pyc
scripts/__pycache__/test_evidence_memory.cpython-313-pytest-9.1.1.pyc
scripts/__pycache__/test_interpretation_memory.cpython-313-pytest-9.1.1.pyc
scripts/__pycache__/test_team_agentic_ingestion_dry_run.cpython-313-pytest-9.1.1.pyc
scripts/__pycache__/test_team_runner_dry_run.cpython-313-pytest-9.1.1.pyc
tests/__pycache__/__init__.cpython-313.pyc
tests/__pycache__/test_authority_backed_internal_model.cpython-313.pyc
tests/__pycache__/test_authority_backed_sysml_generation.cpython-313.pyc
tests/__pycache__/test_authority_backed_sysml_validation.cpython-313.pyc
tests/__pycache__/test_classification_alignment.cpython-313.pyc
tests/__pycache__/test_derivation_assessor.cpython-313-pytest-9.1.1.pyc
tests/__pycache__/test_effective_review_decisions_manifest.cpython-313.pyc
tests/__pycache__/test_effective_review_decisions_public_api.cpython-313.pyc
tests/__pycache__/test_engineering_subject_duplicate_consolidation.cpython-313.pyc
tests/__pycache__/test_engineering_subject_grounding_recovery.cpython-313.pyc
tests/__pycache__/test_final_review_publication_bridge.cpython-313.pyc
tests/__pycache__/test_finalized_artifact_loading.cpython-313.pyc
tests/__pycache__/test_finalized_artifact_persistence.cpython-313.pyc
tests/__pycache__/test_finalized_artifact_set.cpython-313.pyc
tests/__pycache__/test_finalized_reviewed_document_manifest.cpython-313.pyc
tests/__pycache__/test_finalized_reviewed_document_public_api.cpython-313.pyc
tests/__pycache__/test_guided_workflow_actions.cpython-313.pyc
tests/__pycache__/test_guided_workflow_detail_ui.cpython-313.pyc
tests/__pycache__/test_guided_workflow_model_proposal_presentation.cpython-313.pyc
tests/__pycache__/test_guided_workflow_processing_review_presentation.cpython-313.pyc
tests/__pycache__/test_human_review_approval_ui.cpython-313.pyc
tests/__pycache__/test_human_review_document_finalization.cpython-313.pyc
tests/__pycache__/test_human_review_finalization_ui.cpython-313.pyc
tests/__pycache__/test_human_review_foundation.cpython-313.pyc
tests/__pycache__/test_human_review_item_editor_ui.cpython-313.pyc
tests/__pycache__/test_human_review_promotion_ui.cpython-313.pyc
tests/__pycache__/test_human_review_public_api.cpython-313.pyc
tests/__pycache__/test_human_review_reopening_ui.cpython-313.pyc
tests/__pycache__/test_open_question_resolution_card_ui.cpython-313.pyc
tests/__pycache__/test_processing_event_manifest.cpython-313-pytest-9.1.1.pyc
tests/__pycache__/test_processing_phase_progress.cpython-313.pyc
tests/__pycache__/test_processing_run_manifest.cpython-313-pytest-9.1.1.pyc
tests/__pycache__/test_project_dashboard_ingestion_review_navigation.cpython-313.pyc
tests/__pycache__/test_project_ingestion_processing_bridge.cpython-313.pyc
tests/__pycache__/test_project_ingestion_subject_failure_classification.cpython-313.pyc
tests/__pycache__/test_project_processing_foundation.cpython-313-pytest-9.1.1.pyc
tests/__pycache__/test_review_document_manifest.cpython-313.pyc
tests/__pycache__/test_review_document_version_manifest.cpython-313.pyc
tests/__pycache__/test_review_item_manifest.cpython-313.pyc
tests/__pycache__/test_review_report.cpython-313-pytest-9.1.1.pyc
tests/__pycache__/test_review_revision_manifest.cpython-313.pyc
tests/__pycache__/test_review_workspace_evidence_adapter.cpython-313.pyc
tests/__pycache__/test_review_workspace_evidence_adapter_public_api.cpython-313.pyc
tests/__pycache__/test_review_workspace_finalization_authorization.cpython-313.pyc
tests/__pycache__/test_review_workspace_finalization_authorization_public_api.cpython-313.pyc
tests/__pycache__/test_review_workspace_finalization_persistence.cpython-313.pyc
tests/__pycache__/test_review_workspace_finalization_validation.cpython-313.pyc
tests/__pycache__/test_review_workspace_finalization_validation_public_api.cpython-313.pyc
tests/__pycache__/test_review_workspace_foundation.cpython-313.pyc
tests/__pycache__/test_review_workspace_p4_evidence_adapter.cpython-313.pyc
tests/__pycache__/test_review_workspace_p4_evidence_adapter_public_api.cpython-313.pyc
tests/__pycache__/test_review_workspace_p4_evidence_reference_adapter.cpython-313.pyc
tests/__pycache__/test_review_workspace_p4_evidence_reference_adapter_public_api.cpython-313.pyc
tests/__pycache__/test_review_workspace_p4_review_item_builder.cpython-313.pyc
tests/__pycache__/test_review_workspace_p4_review_item_builder_public_api.cpython-313.pyc
tests/__pycache__/test_review_workspace_p9_evidence_reference_adapter.cpython-313.pyc
tests/__pycache__/test_review_workspace_p9_evidence_reference_adapter_public_api.cpython-313.pyc
tests/__pycache__/test_review_workspace_p9_proposal_adapter.cpython-313.pyc
tests/__pycache__/test_review_workspace_p9_proposal_adapter_public_api.cpython-313.pyc
tests/__pycache__/test_review_workspace_p9_review_item_builder.cpython-313.pyc
tests/__pycache__/test_review_workspace_p9_review_item_builder_public_api.cpython-313.pyc
tests/__pycache__/test_review_workspace_paths.cpython-313.pyc
tests/__pycache__/test_review_workspace_repository.cpython-313.pyc
tests/__pycache__/test_review_workspace_repository_identifiers.cpython-313.pyc
tests/__pycache__/test_review_workspace_repository_mutations.cpython-313.pyc
tests/__pycache__/test_review_workspace_repository_scan.cpython-313.pyc
tests/__pycache__/test_review_workspace_review_document_assembly.cpython-313.pyc
tests/__pycache__/test_review_workspace_review_document_assembly_public_api.cpython-313.pyc
tests/__pycache__/test_review_workspace_types.cpython-313.pyc
tests/__pycache__/test_reviewed_report_renderer.cpython-313.pyc
tests/__pycache__/test_reviewed_report_renderer_public_api.cpython-313.pyc
tests/__pycache__/test_scoped_review_action_manifest.cpython-313.pyc
tests/__pycache__/test_sem015_authority_backed_final_review_handoff.cpython-313.pyc
tests/__pycache__/test_subject_discovery_raw_observability.cpython-313.pyc
tests/__pycache__/test_turing_generator_execution_ui.cpython-313.pyc
tests/__pycache__/test_turing_generator_ingestion_running_action.cpython-313.pyc
tests/__pycache__/test_turing_generator_navigation.cpython-313.pyc
tests/__pycache__/test_turing_generator_retry_ui.cpython-313.pyc
tests/test_classification_alignment.py
tests/test_engineering_subject_duplicate_consolidation.py
tests/test_engineering_subject_grounding_recovery.py
tests/test_model_refinement_review_ui.py
tests/test_processing_phase_progress.py
tests/test_project_ingestion_subject_failure_classification.py
tests/test_semantic_consistency_alignment.py
tests/test_subject_discovery_raw_observability.py
wp12_blk001_b1ab_resolution_core_patch.py
wp12_blk001_b1c_card_ui_patch.py
wp12_blk001_subslice_a_patch.py
wp12_blk001_subslice_a_patch_v2.py
wp12_blk001_subslice_b_patch.py
wp12_blk006_c6c3a_reference_grounded_formulation_contract_patch.py

=== STAGED ===
```
