# Turing Generator — Processing Robustness Adjustment Evaluation Report

**Date:** 2026-08-26
**Scope:** Project `000116`, `RUN-000004`, robustness hardening and live verification through `ATT-000005`
**Working branch:** `feature/processing-semantic-normalization`
**Status:** Robustness behavior verified; UI consolidation still under test; no commit acceptance yet.

## 1. Why this report exists

During live revalidation of long-running Processing feedback, repeated Processing attempts exposed several contract failures that were not caused by missing engineering content, but by small variations in otherwise usable LLM outputs. The implementation was hardened incrementally while preserving the project principles:

- no silent semantic invention;
- Human Review remains authoritative;
- raw LLM output remains auditable;
- deterministic repair is preferred when no semantic choice is necessary;
- ambiguous semantic cases fail closed or use a bounded semantic alignment call;
- robustness must not be achieved by reducing persona count, subject coverage, or relationship extraction.

This report documents what was changed and, importantly, what was measured to establish that robustness did not reduce semantic coverage.

## 2. Finding / triage relationship

The work began in the **Post-Golden UX quick-win branch**, specifically the long-running Processing feedback cluster:

- `OBS-007` — Long Processing feedback
- `OBS-017` — Long-running Processing feedback / performance

The triage requires immediate acknowledgement, truthful current stage/running state, and explicit completion/failure, without invented percentages.

`OBS-030` belongs to the same UX-B cluster but concerns **Model Proposal generation** and is not the Processing path validated in this report.

The semantic robustness defects discovered while exercising the Processing path are **not currently a separately numbered BLK/SEM/OBS finding in the accepted post-golden triage**. They are a derived implementation-hardening slice discovered while revalidating `OBS-007/OBS-017`.

They should therefore not be confused with:

- `BLK-002` — Multi-Source Processing Artifact Identity, which remains a separate strategic blocker;
- `SEM-011/SEM-015` — target-model construct coverage/formulation;
- `SEM-013/OBS-031` — Model Placement ambiguity and interaction.

If a permanent finding ID is desired, it should be assigned explicitly rather than invented retroactively.

## 3. Are the comparisons based on metrics already in the code?

**Partly.**

There are two different layers:

### 3.1 Existing deterministic comparison / consensus logic in the code

The current Subject pipeline already contains a deterministic `modules/subject_consensus/analyzer.py`. It does not call an LLM and does not use semantic similarity. It evaluates the fixed Subject population and Persona outputs structurally.

For every canonical Subject it compares the structured fields:

- `information_type`
- `statement_modality`
- `epistemic_class`

For these fields it records:

- selected consensus value, where one exists;
- `unanimous`, `majority`, `divergent`, or `indeterminate`;
- confidence (`high`, `medium`, `low`);
- supporting Personas;
- dissenting Personas;
- Personas unstable across repeated runs;
- value distribution;
- whether Human Review attention is required.

It additionally retains Persona-level variants for:

- interpreted statements;
- uncertainties;
- missing evidence.

For Relationships, comparison identity is the structured tuple:

`(source_subject_id, relationship_kind, target_subject_id)`

For every such relationship it evaluates:

- supporting Personas;
- omitting Personas;
- unstable Personas across repeated runs;
- statement variants;
- consensus level;
- confidence;
- Human Review attention.

The analyzer also performs hard integrity checks before consensus is accepted:

- exact required Persona/run population;
- every Persona run covers the exact canonical Subject set;
- exactly one interpretation per Subject per Persona run;
- Relationship endpoints may reference only Subjects in the fixed population.

Repeated executions of the **same Persona** are explicitly treated as stability measurements and do not create additional independent votes.

### 3.2 Older generic consensus / variance infrastructure

The repository also contains the older generic `modules/consensus/` layer. Its intent is to compare multiple agent outputs and identify full agreement, majority agreement, minority interpretations, conflict, uncertainty, and review-required cases.

This is the “vor Jahrzehnten ;)” comparison infrastructure in spirit. However, the current R4c Subject path has a more specific and stronger Subject-level analyzer with explicit Subject IDs, structured fields, Relationship keys, and Persona/run integrity.

### 3.3 What was *not* already a first-class metric

The live robustness audit in this work also used several **read-only diagnostic metrics derived directly from persisted artifacts**. These were calculated by temporary audit scripts; they are not currently persisted as one formal cross-attempt evaluation report.

These include:

- raw Subject Discovery proposal count;
- duplicate canonical-label count;
- materialized canonical Subject count;
- total Mention count;
- Persona output file count;
- interpretation count per Persona;
- missing/unexpected/duplicate Subject IDs per Persona;
- raw Relationship count per Persona;
- Relationship-kind distribution per Persona;
- invalid Relationship source/target references;
- number of Classification Alignment artifacts;
- number of Semantic Consistency Alignment artifacts;
- cross-attempt comparison of Relationship counts/distributions;
- prompt character counts;
- provider token usage.

So the data and much of the comparison logic already exist in the system, but the **ATT-000002 vs ATT-000005 robustness comparison was assembled as an explicit evaluation audit**, not produced by one existing “robustness metrics” command.

## 4. Metrics used in this robustness evaluation

### 4.1 Execution completeness

Purpose: prove that successful execution did not skip required semantic work.

Measured:

- number of required Persona outputs;
- number of interpretations per Persona;
- number of unique Subject IDs;
- missing Subject IDs;
- unexpected Subject IDs;
- duplicate Subject IDs.

Acceptance criterion used:

- all required Personas execute;
- every Persona covers the complete canonical Subject population exactly once;
- no unexpected Subjects;
- no duplicate Subject interpretations.

### 4.2 Subject Discovery population

Purpose: detect whether robustness was achieved by shrinking or silently altering the discovery population.

Measured:

- raw LLM Subject proposal count;
- duplicate canonical labels;
- canonical Subject count after contract processing;
- Mention count;
- specific provenance retention for repaired duplicates.

Observed example:

`ATT-000004` raw output contained 24 proposals. Two proposals had the identical label `Active collaboration session`, the same `subject_form=condition`, and the same `identity_status=resolved`, but different source Mentions.

The deterministic duplicate-consolidation rule merged only this compatible case and retained both Mentions. Replay produced 23 canonical Subjects and passed materialization.

No additional LLM interpretation was introduced.

### 4.3 Structured semantic alignment usage

Purpose: distinguish normal controlled classification from robustness interventions.

Measured:

- Classification Alignment artifact count;
- Semantic Consistency Alignment artifact count;
- raw value;
- normalized controlled value;
- mapping status;
- affected Subject / Persona;
- mapper response provenance where applicable.

Observed in `ATT-000005`:

- one Classification Alignment decision;
- zero Semantic Consistency Alignment decisions.

The observed classification decision mapped:

`condition` → `constraint`

for `SUBJ-000010` in the skeptical Persona output.

Zero Semantic Consistency Alignment artifacts means that this successful attempt did not reproduce the earlier coupled `epistemic_class` / `missing_evidence` inconsistency. It does **not** mean that C3.3 was removed or bypassed.

### 4.4 Relationship extraction coverage

Purpose: ensure that successful robustness handling did not suppress relational semantics.

Measured per Persona:

- total Relationship proposals;
- distribution by `relationship_kind`;
- invalid source Subject references;
- invalid target Subject references.

Relationship counts are **not** treated as a truth score. A Persona is allowed to propose fewer, more, or different relationships. The metric is used comparatively to detect gross semantic collapse, not to force a target count.

### 4.5 Persona diversity

Purpose: ensure robustness did not homogenize the Persona outputs.

Measured indirectly through:

- different Relationship-kind distributions;
- different Relationship counts;
- structured-field consensus/dissent in the existing Subject Consensus layer;
- statement/uncertainty/missing-evidence variants.

A healthy result is not “all Personas return the same thing”. Persona divergence is expected and is explicitly represented for Human Review.

### 4.6 Cross-attempt stability / non-regression

Purpose: compare a prior semantically rich attempt with the successful hardened attempt.

Reference comparison:

| Metric | ATT-000002 | ATT-000005 |
|---|---:|---:|
| Canonical Subject interpretations per Persona | 20 | 20 |
| Literal Relationships | 10 | 12 |
| Skeptical Relationships | 12 | 12 |
| Systems Engineering Relationships | 12 | 12 |
| Invalid Relationship source refs | 0 | 0 |
| Invalid Relationship target refs | 0 | 0 |
| Required Personas | 3/3 | 3/3 |

Relationship-kind distributions remained Persona-specific in both attempts.

Examples for `ATT-000005`:

- Literal: `constrains`, `controls`, `observes`, `performs`, `related_to`, `requires`
- Skeptical: `constrains`, `controls`, `depends_on`, `observes`, `provides`, `related_to`, `requires`, `uses`
- Systems Engineering: `constrains`, `controls`, `observes`, `performs`, `related_to`, `requires`

This is positive evidence that semantic perspectives were not collapsed by the robustness changes.

### 4.7 Prompt / token-size sanity check

Purpose: detect accidental prompt truncation or major reduction of semantic input.

Compared between `ATT-000002` and `ATT-000005`:

- instruction character count;
- input character count;
- estimated input tokens;
- actual provider input/output token usage.

The values were very similar between attempts. Differences were small and consistent with the slightly different Subject Discovery population.

These are execution-size diagnostics, **not engineering-quality scores**.

## 5. Robustness changes evaluated

### C1 — Generic Subject Grounding Recovery

Introduced structured grounding violations and one bounded repair attempt for LLM-repairable grounding failures.

Examples include:

- unknown Source Span;
- context-only positive Mention;
- unknown token;
- token outside claimed Span;
- reversed token range.

System integrity failures remain separate and are not silently repaired.

### C2 — Precise Processing failure boundaries

Replaced a broad generic Subject-processing failure with explicit categories:

- `subject_discovery_grounding_failed`
- `subject_discovery_validation_failed`
- `subject_discovery_integrity_failed`
- `subject_discovery_execution_failed`
- `subject_interpretation_failed`
- `subject_consensus_failed`
- `subject_review_artifact_failed`

This was essential for diagnosing later attempts correctly.

### C3 — Controlled Classification Alignment

LLM classification text is treated as a semantic proposal, not as an authoritative enum.

Behavior:

- valid controlled values pass unchanged;
- deterministic case/whitespace normalization where unique;
- out-of-vocabulary values may receive one bounded contextual mapping call;
- unresolved `information_type` can fall back to neutral `unclassified`;
- fields without a safe neutral value fail closed;
- raw LLM output remains immutable and alignment provenance is retained.

### C3.3 — Semantic Field Consistency Alignment

Added bounded handling for the coupled fields:

`epistemic_class + missing_evidence`

This addressed an earlier real failure where the classification could be normalized but the coupled field shape remained contract-invalid.

### Subject Discovery raw-response observability

Every completed Subject Discovery response is now retained before parsing/materialization.

Persisted diagnostic payloads are explicitly:

- `diagnostic_only=true`
- `engineering_authority=false`

This made the `ATT-000004` failure reproducible without another LLM call.

### Deterministic compatible duplicate-Subject consolidation

A repeated canonical label is merged only when all semantic classification fields relevant at this boundary already agree:

- same case-insensitive canonical label;
- same `subject_form`;
- same `identity_status`.

Mentions are unioned deterministically and exact repeated Mentions are deduplicated.

If `subject_form` or `identity_status` conflicts, processing still fails closed.

## 6. Attempt history used as evaluation evidence

### ATT-000002

Reached Subject Interpretation but failed there before later robustness changes.

Its persisted raw outputs nevertheless provided a useful semantic comparison baseline:

- 20 interpretations per Persona;
- 10 / 12 / 12 Relationships.

### ATT-000003

Failed with:

`subject_discovery_validation_failed`

The raw Subject Discovery response had not yet been persisted, so the exact invalid output could not be reconstructed.

### ATT-000004

Failed with:

`subject_discovery_validation_failed`

After raw-response observability was added, the exact output was retained.

Diagnosis:

- 24 raw Subject proposals;
- duplicate canonical label: `Active collaboration session`;
- both duplicate proposals:
  - `subject_form=condition`
  - `identity_status=resolved`
  - different valid source Mentions.

Replay after deterministic consolidation:

- parse PASS;
- 23 canonical proposals;
- materialization PASS;
- both source Mentions retained in the merged Subject.

This establishes that the failure was caused by a deterministically repairable grouping duplication rather than missing engineering semantics.

### ATT-000005

Live execution completed successfully:

- status: Ready for Human Review;
- 20 canonical Subjects;
- 19 Mentions;
- 20/20 unique Subject IDs;
- 3/3 Persona outputs;
- 20/20 interpretations for every Persona;
- no missing/unexpected/duplicate Subject IDs;
- 12 Relationships for each Persona;
- no invalid Relationship endpoints;
- one Classification Alignment artifact;
- complete consensus/review artifact set.

## 7. Evaluation conclusion

The robustness changes passed the acceptance principle:

> Robustness must not be achieved by reducing semantic perspectives or coverage.

Evidence supporting this conclusion:

1. all three required Personas still executed;
2. every Persona covered the full canonical Subject population exactly once;
3. Relationship extraction remained present and semantically diverse;
4. no invalid Relationship endpoints were introduced;
5. prompt/input sizes remained comparable to the earlier attempt;
6. raw LLM outputs remain preserved where diagnostic recovery is needed;
7. deterministic repair was used only where no semantic choice was required;
8. ambiguous cases remain bounded or fail closed;
9. Human Review remains mandatory.

The comparison does **not** claim that ATT-000005 is semantically “more correct” than ATT-000002. The metrics establish structural completeness, non-collapse, provenance, and controlled variance. Engineering truth remains subject to Human Review.

## 8. Important distinction: metrics vs quality judgement

The following must not be conflated:

- **Completeness metric:** did all expected Subjects/Personas/Relationships structurally survive?
- **Consensus metric:** how many independent Personas support the same structured value or Relationship?
- **Stability metric:** does one Persona produce the same structured result across repeated runs?
- **Diagnostic metric:** how many repair/alignment paths were invoked?
- **Engineering correctness:** is the interpretation actually correct for the intended model?

The first four can be computed deterministically. The last one cannot be inferred from agreement counts alone and remains under Human authority.

## 9. Recommended next improvement to evaluation tooling

The current evaluation demonstrates that the necessary data already exists, but the cross-attempt robustness comparison was assembled manually.

A useful later engineering slice would be a deterministic, read-only **Processing Robustness Evaluation Report** that consumes persisted attempts and produces:

- Subject population delta;
- Persona/run completeness;
- field-consensus distributions;
- Relationship count and kind distributions;
- Relationship consensus distributions;
- invalid-reference count;
- alignment/repair invocation counts;
- prompt/token diagnostic deltas;
- explicit warnings for semantic-dimension collapse;
- no automatic engineering approval.

This should reuse `subject_consensus` rather than create a competing consensus model.

## 10. Current status after this evaluation

Semantic robustness verification: **PASS**

Current remaining work on this branch:

- finish UI consolidation for `OBS-007` / `OBS-017`;
- rerun focused and full regression;
- perform a short UI sanity check;
- review diff;
- only then decide whether the whole branch is commit-ready.

`BLK-002` remains separate and unresolved.
