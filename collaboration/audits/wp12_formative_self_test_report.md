# WP-12 Formative Self-Test Report — Thesis Evaluation Record

## 1. Purpose and status

This document consolidates the WP-12 verification and formative self-evaluation
evidence into one thesis-usable evaluation record.

WP-12 was not executed as a one-shot acceptance test. It became an iterative,
task-based formative self-test in which connected end-to-end execution exposed
architecture, semantic, governance, integration and UX defects that were not
visible from isolated regression tests alone.

Current result:

```text
Single-source Golden E2E: PASS
Multi-source formal Stage-A: FAILED WITH BLOCKER — BLK-002
Known-Good implementation commit:
924bf27d2ee4ca07c1d04da2c777ce31b7632e97
Known-Good tag:
wp12-golden-e2e-2026-08-25
```

The successful single-source result does not close or weaken the formal
multi-source blocker.

## 2. Evaluation design

### 2.1 Evaluation type

The evaluation is a formative, task-based self-evaluation performed by the
developer / Systems Engineer while operating the demonstrator.

It combines:

- connected end-to-end technical verification,
- semantic/model-quality inspection,
- Human-in-the-Loop authority checks,
- formative UX observation,
- bounded defect correction,
- same-gate retesting,
- automated regression,
- external SysML v2 validation.

This is qualitative design evidence. It is not an independent usability study and
does not support statistically representative usability claims.

### 2.2 Original test design

The original formal WP-12 Stage-A design used four controlled synthetic legacy
documents and required a complete multi-document path before release to more
representative data.

Formal test:

```text
WP12-E2E-DRY-001
Project 308131
```

The multi-source path exposed `BLK-002` and therefore remained:

```text
FAILED WITH BLOCKER
```

### 2.3 Recovery / formative evaluation path

Because the multi-source identity defect was orthogonal to several architectural and
semantic questions, the evaluation continued with a separately identified
single-source recovery path:

```text
Project 120412 — WP12 R4c Live E2E
```

This path is not retrospectively classified as a successful formal multi-source
Stage-A run. It is additional formative and single-source E2E evidence.

## 3. Evaluation questions

The connected test evaluated whether the prototype could:

1. preserve Engineering Source provenance and source-grounded evidence,
2. separate processing/reference context from positive Engineering Information,
3. form stable Engineering Subjects without Persona-driven multiplication,
4. preserve semantic uncertainty for Human Review,
5. promote only explicitly Human-approved engineering information,
6. separate Engineering Meaning from target-model placement and formulation,
7. preserve Human authority during model placement and relationship resolution,
8. assemble the accepted model deterministically,
9. generate SysML v2 without inventing unsupported semantics,
10. validate the exact generated artifact with an external SysML v2 tool,
11. require explicit Final Model Review and Human publication approval,
12. publish an immutable artifact bound to the reviewed and validated revision,
13. keep the connected workflow understandable enough for an engineer to operate.

## 4. Formative test-and-repair path

The implementation path itself is a central test result.

### Iteration 1 — Multi-source execution exposed identity/provenance risk

The controlled multi-document path exposed `BLK-002`: Processing Artifact identity
was not sufficiently bound to Source/Run context.

Result:

```text
multi-source acceptance blocked
single-source claims kept separate
```

The finding demonstrated that apparent processing success is insufficient when
artifact identity and provenance are not unambiguous.

### Iteration 2 — Semantic effectiveness exposed responsibility-boundary problems

Early connected runs reached Human Review technically but produced source
contamination, generic process/artifact concepts and Persona-driven Subject
multiplication.

This produced the BLK-003 / SEM-001..SEM-005 recovery direction:

```text
Engineering Source
→ deterministic/source-grounded Evidence
→ shared Canonical Subjects
→ Persona Interpretation
→ Human Engineering Review
```

The key architectural result was that Persona variation must interpret shared
source-grounded subjects rather than create independent subject populations.

### Iteration 3 — R4c live path exposed authority handoff defects

Project `120412` validated the recovered semantic path and then exposed two new
connected-boundary failures:

```text
BLK-004 — R4c classification could not be promoted by the legacy scalar
          Approved Input promotion contract.

BLK-005 — accepted semantic Relationships were not part of the authoritative
          Approved Engineering Information → model-derivation handoff.
```

Both defects were corrected and retested in the same recovery context.

This showed that a semantically improved upstream pipeline is not sufficient if
downstream authority contracts still encode an older information model.

### Iteration 4 — Model generation exposed a missing target-model responsibility

The next connected failure initially appeared as `BLK-006`. Diagnosis showed that
the system moved too directly from approved Engineering Meaning toward target-model
representation / serialization.

The test therefore produced the architectural distinction later captured by
SEM-012..SEM-015:

```text
Engineering Meaning
≠ Target-Model Placement / Representation
≠ Target-Model Formulation
≠ SysML v2 Serialization
```

A separate Human Model Placement Review and a type-specific Target-Model
Formulation / model-quality refinement step were introduced.

### Iteration 5 — Assembly exposed a Human/LLM responsibility violation

During the same downstream recovery, `BLK-007` showed that Model Assembly was
calling Model Placement personas for Relationship representation.

The correction established:

```text
Model Assembly = deterministic

exact authorized relationship semantics
→ deterministic mapping

unresolved relationship semantics
→ explicit Human Final Model Review
```

This finding sharpened the boundary between advisory LLM reasoning and authoritative
model construction.

### Iteration 6 — Target formulation and quality review became explicit

SEM-015 was implemented for the single-source PoC as:

```text
Human-reviewed placement / classification
→ type-specific LLM model-quality refinement
→ Human Model Quality Review 2
→ successor Internal Engineering Model
```

The refinement step may improve model-facing wording but may not:

- reclassify the element,
- move it to a different model area,
- invent missing engineering content,
- silently resolve unsupported semantics.

The accepted successor was `IEM-000002`.

### Iteration 7 — Deterministic SysML generation and external validation

The accepted successor model generated SysML v2 deterministically.

Two `traces_to` relationships were intentionally not materialized because no
locally validated faithful target syntax had been accepted. One `dependency`
relationship was materialized.

Stakeholder roles were activated through the locally SYSIDE-validated `TN_003`
Part Definition pattern.

External validation:

```text
SYSIDE Modeler CLI
version 0.10.3
exit code 0
diagnostics 0
All checks passed
```

This is evidence of generated textual-model conformance/tool compatibility, not a
substitute for Human engineering approval.

### Iteration 8 — Final Review integration exposed a legacy authority mismatch

The first post-generation Final Model Review handoff failed because the downstream
repository accepted only the legacy Candidate-based generated-artifact contract.

The authority-backed artifact instead bound:

```text
element authority:
Approved Input + Model Placement Decision

relationship authority:
Semantic Relationship Decision + Final Assembly Decision
```

The correction extended the existing Final Model Review / release / publication
path natively. It did not synthesize legacy Candidate authority or create a second
compatibility artifact.

A successor Final Review revision was then created and accepted.

### Iteration 9 — Human release and immutable publication

Final accepted chain:

```text
IEM-000002
→ generated artifact
→ SYSIDE-valid validation result
→ FMR-000001 / FRV-000002
→ Human release FRD-000001
→ OUT-000001
```

Published package:

```text
data/output/120412/OUT-000001/
```

Published SysML:

```text
generated_model.sysml
```

The package is immutable and fingerprint-bound to the exact source model,
validation evidence and Human release decision.

## 5. Final single-source acceptance evidence

```text
Project:                 120412
Successor IEM:           IEM-000002
Final Model Review:      FMR-000001
Accepted review revision:FRV-000002
Human release decision:  FRD-000001
Published Output:        OUT-000001
```

External validation:

```text
SYSIDE 0.10.3
completed
exit code 0
diagnostics 0
validation valid
publication gate passed
```

Automated verification:

```text
focused TN_003 synchronization: 29 passed
complete repository regression: 6046 passed in 16.57s
git diff --check: PASS
```

Known-Good baseline:

```text
commit 924bf27d2ee4ca07c1d04da2c777ce31b7632e97
tag    wp12-golden-e2e-2026-08-25
```

## 6. Principal formative findings

### 6.1 Architecture and semantic findings

The strongest findings were not isolated coding defects but responsibility-boundary
problems:

- source/reference context must not become Engineering Evidence,
- Subject identity must exist before Persona interpretation,
- uncertainty is legitimate Human Review input and not automatically a failure,
- Approved Engineering Information must include accepted semantic Relationships,
- Engineering Meaning does not uniquely determine a target-model construct,
- target-model placement and target-model formulation require explicit authority,
- deterministic assembly/generation must not silently invoke semantic fallback,
- post-generation review must bind the exact authority-backed artifact.

### 6.2 Human-in-the-Loop findings

The test confirmed that Human authority is needed at materially different points:

```text
Engineering Review
Model Placement Review
Model Quality / Formulation Review
Relationship resolution / Assembly Final Review
Final Model Review
Human publication release
```

The evaluation also showed that Human authority can become unnecessarily expensive
if consensus, shared ambiguity and true Persona variance are not distinguished
clearly in the UI.

### 6.3 UX findings

The formative run exposed, among others:

- long-running processing feedback gaps,
- state/presentation inconsistencies,
- relationship-review discoverability problems,
- overly ID-centric relationship presentation,
- excessive Model Placement interaction,
- difficulty distinguishing historical from current validation evidence,
- missing deterministic review-report export.

These are retained as findings even though they do not invalidate the accepted
single-source E2E.

## 7. Interpretation

The most important WP-12 result is not only that the final single-source path
passed. The test demonstrated that connected execution can expose architectural
defects that are invisible when components are evaluated only in isolation.

The resulting implementation path is therefore itself an evaluation outcome:

```text
observed connected failure
→ identify violated responsibility / authority boundary
→ bounded architectural correction
→ focused verification
→ same-gate live retest
→ repository regression
→ continue the E2E
```

This iterative process is consistent with a formative prototype evaluation: findings
were deliberately used to improve the artifact while preserving the observed
failure and its disposition as evidence.

## 8. Limitations and threats to validity

The following limitations must be stated in the thesis:

1. The formative evaluator was also the developer / Systems Engineer; the
   evaluation is therefore not independent.
2. The test is qualitative and task-based; no statistical usability claim is made.
3. The final Golden E2E is single-source and does not validate multi-source
   processing. `BLK-002` remains open.
4. The system was changed during the evaluation. This is intentional for formative
   evaluation but means WP-12 is not a fixed-build summative benchmark.
5. LLM-assisted stages may vary between runs. Human authority, immutable artifacts,
   explicit identities and fingerprints are used to preserve auditability.
6. External SYSIDE success demonstrates accepted syntax/tool compatibility; it does
   not prove semantic model quality.
7. The source used for the Golden path is a bounded demonstrator input and does not
   establish general performance for arbitrary industrial legacy repositories.
8. Runtime/performance and independent usability were not systematically measured.

## 9. Thesis-use conclusion

A defensible thesis statement is:

> The formative end-to-end self-test demonstrated the feasibility of the
> authority-preserving single-source transformation chain and, more importantly,
> exposed several architectural and semantic responsibility-boundary defects. The
> iterative correction and same-gate retesting of these findings led to a
> source-grounded, Human-reviewed and externally SysML-v2-validated prototype
> baseline. Multi-source processing remained explicitly unvalidated because of an
> unresolved cross-source artifact-identity blocker.

This result should be presented as formative prototype evaluation and technical
verification, not as independent usability validation.

<!-- BEGIN SEM015 COMPLETENESS NOTE -->
## SEM-015 completeness qualification

SEM-015 was a major formative finding and shall not be described as fully complete
merely because the Golden single-source E2E passed.

The accepted architecture is implemented and validated for the Golden-E2E scope:

```text
Engineering Meaning
→ Human-reviewed target classification / placement
→ bounded Target-Model Formulation authority
→ type-specific model-quality refinement
→ Human Review 2
→ successor Internal Engineering Model
→ deterministic SysML v2 generation
```

However, the current Target-Model Formulation proposal builder remains deliberately
bounded to the BLK-006 recovery population:

```text
element:       stakeholder
relationship:  traces_to
```

The model-quality refinement layer already supports a broader set of element types,
including requirements, functions/actions, use cases, logical/physical components
and information items, with a conservative fallback for unknown types.

Therefore the correct status is:

```text
SEM-015 architecture:                 IMPLEMENTED
Golden-E2E SEM-015 scope:             VALIDATED
general target-type formulation:      OPEN / PARTIAL
dependency-aware selective rerun F01: DEFERRED
```

General SEM-015 completion is coupled to SEM-011: every newly supported target-model
construct (for example State Machine, State, Transition, Interface, Port or Item)
must receive explicit formulation policy, Human-review behavior and deterministic
downstream mapping rather than being added only as a taxonomy string.
<!-- END SEM015 COMPLETENESS NOTE -->

## 10. Canonical evidence

- `collaboration/audits/wp12_multi_document_dry_run_test_protocol.md`
- `collaboration/audits/wp12_test_release_workflow.md`
- `collaboration/audits/wp12_findings.md`
- `collaboration/ux/wp12_formative_self_evaluation_log.md`
- `collaboration/checkpoints/2026-08-24_wp12_r4c_live_e2e_ssot.md`
- `collaboration/checkpoints/2026-08-25_wp12_c6_sysml_generation_ssot.md`
- `collaboration/checkpoints/2026-08-25_wp12_golden_e2e_known_good_baseline.md`
- `data/output/120412/OUT-000001/`
- Known-Good commit `924bf27d2ee4ca07c1d04da2c777ce31b7632e97`
- tag `wp12-golden-e2e-2026-08-25`
