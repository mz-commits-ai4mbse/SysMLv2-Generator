# WP-12 Test and Release Workflow — Synthetic Dry Run to Real Test Data

<!-- BEGIN WP12 FORMATIVE CLOSEOUT 2026-08-25 -->
## 2026-08-25 — Methodological closeout

The original Stage-A release workflow remains valid for the formal multi-source
claim:

```text
WP12-E2E-DRY-001 / Project 308131
FAILED WITH BLOCKER — BLK-002
```

A separate single-source recovery / formative path was deliberately continued on:

```text
Project 120412
```

That path reached a complete Golden E2E and immutable publication.

This is a documented protocol deviation / additional evaluation path, not a
retroactive Stage-A PASS and not evidence that multi-source processing is verified.

The thesis shall therefore distinguish:

```text
formal controlled multi-source verification
→ blocked by BLK-002

single-source formative recovery + connected E2E verification
→ PASS through immutable publication
```

The continuation was methodologically useful because it allowed downstream
architecture, semantic, authority, SysML generation, validation, Final Review and
publication behavior to be evaluated without hiding the independent multi-source
identity defect.

Canonical synthesis:

`collaboration/audits/wp12_formative_self_test_report.md`
<!-- END WP12 FORMATIVE CLOSEOUT 2026-08-25 -->

<!-- BEGIN WP12 RELEASE STATUS 2026-08-24 -->
## 2026-08-24 — Current WP-12 release-gate status

```text
Formal Stage-A / multi-source: FAILED WITH BLOCKER — BLK-002
R4c single-source live E2E:     FAILED WITH BLOCKER — BLK-006
Overall WP-12:                  FAILED WITH BLOCKER
Stage-B / release progression:  NOT AUTHORIZED
```

Resolved blockers remain part of test history:

```text
BLK-001 corrected / verified
BLK-004 resolved -> live retest PASS
BLK-005 resolved -> live retest PASS WITH FINDINGS
```

The release gate is not reclassified until all active blockers have been corrected and
successfully retested. Remaining non-blocking findings may lead to `PASS WITH
FINDINGS`, but never to a silent bypass of Human Review, Candidate Review,
traceability, validation or publication authority.
<!-- END WP12 RELEASE STATUS 2026-08-24 -->

## Purpose

This document defines the controlled validation sequence for the WP-12 demonstrator.

The workflow deliberately separates:

1. a complete synthetic multi-document dry run using intentionally created test data,
2. an explicit release decision,
3. a subsequent test using real / representative non-synthetic test data.

The synthetic dry run is therefore not merely a demo rehearsal. It is a formal
precondition for authorizing the next evidence stage.

Current status as of 2026-08-16:

```text
Stage-A test design: ACCEPTED
Synthetic fixtures: PREPARED
Formal Stage-A execution: PENDING
Stage-B real / representative test data: NOT YET AUTHORIZED
```

## Validation stages

```text
Stage A — Synthetic multi-document dry run
        ↓
documented protocol execution
        ↓
defect / finding disposition
        ↓
automated regression
        ↓
Dry-Run Release Gate
        ↓
explicit Human release decision
        ↓
Stage B — Real test data
        ↓
same authority-preserving workflow
        ↓
separate result record
```

## Stage A — Synthetic dry run

### Objective

Verify that the complete demonstrator can process multiple controlled legacy
documents into one traceable engineering model flow while preserving all Human
authority gates.

### Input status

The WP-12 synthetic documents are intentionally authored test fixtures.

They are not production data and shall not be represented as independent evidence
that arbitrary real-world legacy data will behave identically.

### Required evidence

The Stage-A package consists of:

- the four version-controlled synthetic source documents
- `wp12_expected_engineering_contract.md`
- `wp12_multi_document_dry_run_test_protocol.md`
- `wp12_formative_self_evaluation_log.md`
- generated project-local artifacts and immutable identifiers
- automated test/regression output
- defect/finding dispositions
- the Stage-A release decision

## Dry-Run Release Gate

Release to Stage B is permitted only when the test owner explicitly records one of:

- `PASS — RELEASED FOR REAL TEST DATA`
- `PASS WITH DOCUMENTED EXTERNAL LIMITATION — RELEASED FOR REAL TEST DATA`
- `FAIL — NOT RELEASED`

### Mandatory release criteria

- [ ] All synthetic source documents registered and processed
- [ ] Human Review completed without bypassing review authority
- [ ] Relevant content promoted to Approved Input only through explicit Human action
- [ ] Cross-document Approved Inputs contribute to one Candidate/model flow
- [ ] Candidate Review remains explicit Human authority
- [ ] Internal Engineering Model is assembled only from eligible reviewed Candidates
- [ ] Generated SysML remains derived output, not engineering authority
- [ ] Validation gate remains fail-closed
- [ ] Final Model Review remains explicit
- [ ] Human release approval remains explicit
- [ ] Output publication remains immutable and fingerprint-bound where executable
- [ ] Source-to-model traceability is inspectable
- [ ] Expected Engineering Contract is satisfied or every deviation is dispositioned
- [ ] No unsupported missing fact is silently promoted as approved truth
- [ ] No open demo-critical integration defect remains
- [ ] No open demo-critical UX defect remains
- [ ] Complete repository regression passes after dry-run fixes
- [ ] `git diff --check` passes for committed implementation changes
- [ ] Formative self-evaluation is completed
- [ ] Known external limitations are documented and not bypassed

### Known SYSIDE condition

The missing local SYSIDE CLI may be recorded as an external limitation only if:

- the relevant gate continues to fail closed,
- no fake PASS is introduced,
- the limitation is clearly documented,
- and all other executable release-path evidence remains intact.

This condition does not authorize bypassing validation or publication rules.

## Stage-A release record

- Date:
- Tester / approver:
- Test specification baseline commit SHA:
- System-under-test commit SHA:
- Synthetic Project ID:
- Protocol result: PASS / CONDITIONAL PASS / FAIL
- Open critical findings:
- Known external limitations:
- Release decision:
  - [ ] PASS — RELEASED FOR REAL TEST DATA
  - [ ] PASS WITH DOCUMENTED EXTERNAL LIMITATION — RELEASED FOR REAL TEST DATA
  - [ ] FAIL — NOT RELEASED
- Rationale:
- Protocol deviations:
- Impact of deviations on result validity:
- Signature / reviewer identity:

## Stage B — Real test data

### Entry condition

Stage B shall not begin until the Stage-A release record explicitly permits it.

### Objective

Evaluate whether the same connected workflow remains usable and semantically
credible when the source content is not authored specifically for the test.

### Rules

- use a new Project or otherwise preserve unambiguous run separation
- preserve original source provenance
- do not pre-seed downstream authoritative artifacts
- apply the same Human Review and Candidate Review gates
- record deviations from the synthetic dry-run behavior
- separate product defects from source-data quality issues
- never modify the real source data merely to make the demonstrator pass

### Stage-B result categories

- PASS
- PASS WITH FINDINGS
- FAIL
- EXTERNAL BLOCKER

A Stage-B failure does not retroactively invalidate the Stage-A synthetic dry run;
it shows a limitation exposed by more representative data.

## Thesis-use framing

The recommended thesis narrative is:

```text
Functionally complete prototype
→ formative usability findings
→ Guided Workflow redesign
→ controlled synthetic multi-document dry run
→ explicit dry-run release gate
→ test with representative real test data
→ final demonstrator evaluation
```

The synthetic dry run provides controlled verification and reproducibility.

The later real-data run increases ecological realism, but neither stage shall be
described as a statistically representative usability study unless separate
independent evidence is collected.

Useful thesis distinctions:

- **Verification:** Did the implemented workflow behave according to the defined
  authority, traceability and semantic expectations?
- **Formative evaluation:** Where did the tester encounter friction, ambiguity or
  unnecessary cognitive effort?
- **Validation with more realistic data:** Does the demonstrator remain useful when
  input content is not designed specifically for the test?
- **Release gate:** Was there sufficient evidence to proceed from controlled synthetic
  fixtures to the more realistic test stage?
