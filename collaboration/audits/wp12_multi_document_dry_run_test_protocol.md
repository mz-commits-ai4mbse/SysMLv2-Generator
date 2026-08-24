# WP-12 Multi-Document End-to-End Dry-Run Test Protocol

<!-- BEGIN WP12 EXECUTION STATUS 2026-08-24 -->
## 2026-08-24 — Formal execution / recovery status

### Result semantics

The WP-12 test uses the following result vocabulary from this checkpoint onward:

```text
PASS
PASS WITH FINDINGS
FAILED WITH BLOCKER
BLOCKER RESOLVED -> RETEST -> PASS / PASS WITH FINDINGS
```

Blockers are part of the test evidence. The affected Project/Run is not restarted
merely to erase the failure; after correction, the affected gate is retested and the
blocker remains documented.

### Formal Stage-A result

```text
Test:    WP12-E2E-DRY-001
Project: 308131
Result:  FAILED WITH BLOCKER
Blocker: BLK-002 — Cross-Source Processing Artifact Identity Collision
```

The earlier wording `IN PROGRESS / INTERRUPTED FOR BLOCKING DEFECT CORRECTION`
remains historical evidence but is superseded as the current result classification.

### R4c Single-Source recovery / live E2E evidence

```text
Project: 120412
Run:     RUN-000001
Attempt: ATT-000001
```

Gate history:

| Gate | Initial result | Current result |
|---|---|---|
| Processing -> Human Review | PASS WITH FINDINGS | PASS WITH FINDINGS |
| Subject + Relationship Review | PASS WITH FINDINGS | PASS WITH FINDINGS |
| Finalization | PASS WITH FINDINGS | PASS WITH FINDINGS |
| Approved Input Promotion | FAILED WITH BLOCKER — BLK-004 | PASS — blocker resolved |
| Approved Engineering Information -> Phase H | FAILED WITH BLOCKER — BLK-005 | PASS WITH FINDINGS — blocker resolved |
| Phase-H Readiness / Coverage | PASS WITH FINDINGS | PASS WITH FINDINGS |
| LLM-assisted Model Proposal generation | FAILED WITH BLOCKER — BLK-006 | FAILED WITH BLOCKER |

Current overall WP-12 result:

```text
FAILED WITH BLOCKER
active: BLK-002, BLK-006
```

Canonical finding register:

`collaboration/audits/wp12_findings.md`

Current register coverage:

```text
BLK-001 .. BLK-006
SEM-001 .. SEM-011
OBS-001 .. OBS-030
PASS-001 .. PASS-010
```

A future WP-12 closeout may be `PASS WITH FINDINGS` once all blocking gates have
passed while non-blocking findings remain explicitly documented.
<!-- END WP12 EXECUTION STATUS 2026-08-24 -->

## 1. Test identification

**Test ID:** WP12-E2E-DRY-001
**Test type:** Controlled synthetic multi-document end-to-end dry run
**Purpose:** Formal pre-release verification before testing with real test data
**Execution mode:** Manual guided workflow + automated regression
**Primary application:** `streamlit run app/turing_generator_app.py`
**Test-design status:** ACCEPTED FOR EXECUTION on 2026-08-16

Related documents:

- `collaboration/audits/wp12_expected_engineering_contract.md`
- `collaboration/audits/wp12_test_release_workflow.md`
- `collaboration/ux/wp12_formative_self_evaluation_log.md`

Synthetic source fixtures:

- `legacy/demo/wp12/01_product_overview.md`
- `legacy/demo/wp12/02_user_workflow.md`
- `legacy/demo/wp12/03_system_requirements.md`
- `legacy/demo/wp12/04_technical_architecture_notes.md`

---

## 2. Test objective

Verify, with controlled synthetic data, that four separate legacy documents can be
registered, processed, Human-reviewed, promoted to Approved Input, synthesized into
one Candidate/model flow and carried through the implemented downstream authority
chain without silent loss of provenance or bypass of Human gates.

The dry run also records formative UX observations.

A successful dry run is a prerequisite for explicit release to a later real-test-data
run.

---

## 3. Test environment record

Complete before execution.

- [x] Repository is on intended branch
- [x] `HEAD == origin/main`
- [x] Working-tree noise is understood and unrelated to the test
- [x] Python virtual environment active
- [ ] Streamlit application starts
- [ ] Required LLM credentials/configuration available
- [x] Known external SYSIDE CLI status recorded

Record:

| Field | Value |
|---|---|
| Date / time | 2026-08-17 09:52 CEST |
| Tester | Moritz |
| Git branch | main |
| Test specification baseline commit SHA | d8ddf7e01b59a796492697bdd8cc88500eb3df56 |
| System-under-test commit SHA | d8ddf7e01b59a796492697bdd8cc88500eb3df56 |
| Python version | 3.13.5 |
| Streamlit version | 1.59.0 |
| LLM provider | |
| LLM model | |
| Application command | `streamlit run app/turing_generator_app.py` |
| SYSIDE CLI available? | NO — known external blocker, fail-closed |
| New test Project name | |
| New test Project ID | |

### Pre-test automated baseline

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q
git diff --check
```

Expected:

- [x] Complete repository regression PASS
- [x] Only deliberate/known skip(s)
- [x] `git diff --check` PASS

Evidence / output reference:

- Terminal baseline execution 2026-08-17 09:52 CEST: 5577 passed, 1 skipped in 13.92s; git diff --check PASS; HEAD == origin/main == d8ddf7e01b59a796492697bdd8cc88500eb3df56.

If baseline fails: **STOP. Do not start the formal dry run.**

---

# 4. Phase A — Project creation and source registration

## TC-A01 — Create isolated dry-run Project

Action:

1. Open the primary application.
2. Create a new Project dedicated to this dry run.
3. Do not reuse an old Project with existing downstream model state.

Expected:

- [ ] New Project is created explicitly
- [ ] New Project becomes current Project context
- [ ] No previous Project entity remains selected
- [ ] Project has no pre-seeded Candidate / IEM / Final Review / OUT authority

Evidence:

- Project ID:
- Screenshot/reference:
- Notes:

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

---

## TC-A02 — Register all four synthetic documents separately

Register:

1. `01_product_overview.md`
2. `02_user_workflow.md`
3. `03_system_requirements.md`
4. `04_technical_architecture_notes.md`

Expected for each source:

- [ ] Source appears separately in Source inventory
- [ ] Original filename is preserved
- [ ] Source is bound to the current Project
- [ ] Source identity / hash is available in Technical View
- [ ] Registering one source does not overwrite another

Record:

| File | Source ID | Registered? | Hash visible? | Notes |
|---|---|---:|---:|---|
| 01_product_overview.md | | [ ] | [ ] | |
| 02_user_workflow.md | | [ ] | [ ] | |
| 03_system_requirements.md | | [ ] | [ ] | |
| 04_technical_architecture_notes.md | | [ ] | [ ] | |

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

Formative checkpoint:

- [ ] It was obvious which sources belong to the Project
- [ ] I did not need internal IDs to distinguish normal working content
- [ ] Technical traceability remained available on demand

Observation IDs:

-

---

# 5. Phase B — Processing each source

Repeat TC-B01 for all four sources.

## TC-B01 — Execute Processing

Action:

1. Select one source by filename.
2. Run normal Processing.
3. Do not manually copy output from another source.
4. Wait for authoritative run completion.
5. Record run result before moving to the next source.

Expected:

- [ ] Processing targets the selected exact Source
- [ ] Processing status is understandable in Focused View
- [ ] Run/Attempt identities are available in Technical View
- [ ] Result is routed to Human Review rather than auto-approved
- [ ] Failure/retry state, if encountered, is explicit and does not silently create approved content

Record:

| Source | Processing status | Run ID | Attempt ID | Published review outputs | Result |
|---|---|---|---|---:|---|
| 01 | | | | | PASS / FAIL |
| 02 | | | | | PASS / FAIL |
| 03 | | | | | PASS / FAIL |
| 04 | | | | | PASS / FAIL |

Cross-source expected behavior:

- [ ] Results remain attributable to their original Source
- [ ] Processing Source 2 does not replace Source 1 evidence
- [ ] All four sources can coexist in the same Project

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

Observation IDs:

-

---

# 6. Phase C — Human Review of each source

## TC-C01 — Open Human Review Queue

Expected:

- [ ] All processed sources requiring review are visible
- [ ] Queue is understandable by filename / engineering context
- [ ] Decisions required are visible without inspecting raw IDs
- [ ] Technical IDs remain available when requested

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

---

## TC-C02 — Review engineering content source by source

For each source:

1. Open the correct Review.
2. Inspect engineering statements/proposals.
3. Inspect Persona alternatives where available.
4. Accept, edit, reject or defer based on source evidence.
5. Do not optimize decisions merely to force the expected final model.

Expected:

- [ ] Engineering content is primary
- [ ] Proposal rationale/evidence is inspectable
- [ ] Human decision is explicit
- [ ] No proposal becomes Approved Input merely because Agents agree
- [ ] Repeated Persona runs are not misrepresented as independent votes
- [ ] Single-Persona result is not presented as inter-Persona unanimity
- [ ] Source evidence remains linked to the correct document

Per-source record:

| Source | Review Document | Review Version | Items | Human decisions complete? | Key finding |
|---|---|---|---:|---:|---|
| 01 | | | | [ ] | |
| 02 | | | | [ ] | |
| 03 | | | | [ ] | |
| 04 | | | | [ ] | |

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

Observation IDs:

-

---

## TC-C03 — Check controlled semantic tension

Inspect evidence related to:

- explicit operator decision for normal control transfer
- automatic remote-authority revocation on connection loss

Expected:

- [ ] They are not silently collapsed into one identical rule
- [ ] They are not incorrectly normalized as a contradiction without context
- [ ] If ambiguity remains, it is surfaced for Human review
- [ ] Human can preserve a distinction between normal transfer and recovery behavior

Actual behavior:

-

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

---

## TC-C04 — Check missing-information discipline

Search Review output for unsupported claims concerning:

- quantitative latency
- bandwidth
- exact retention period
- concrete deployment topology
- network protocol / port
- database/persistence product
- cybersecurity target

Expected:

- [ ] No unsupported value is promoted as source fact
- [ ] Missing information may be identified explicitly
- [ ] Supported engineering content remains reviewable despite those gaps

Unexpected invented facts:

-

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

---

# 7. Phase D — Finalize reviews and promote Approved Input

## TC-D01 — Finalize each review

Expected:

- [ ] Finalization remains blocked while required Human work is unresolved
- [ ] Finalization requires explicit Human confirmation
- [ ] Finalized reviewed version becomes immutable
- [ ] Reopen, if needed, creates a successor rather than mutating the predecessor

Record:

| Source | Finalized? | Finalization decision ID | Blocking findings resolved? |
|---|---:|---|---:|
| 01 | [ ] | | [ ] |
| 02 | [ ] | | [ ] |
| 03 | [ ] | | [ ] |
| 04 | [ ] | | [ ] |

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

---

## TC-D02 — Promote selected results to Approved Input

Expected:

- [ ] Promotion is explicit
- [ ] Only eligible finalized reviewed content is promotable
- [ ] Approved Inputs retain source/review provenance
- [ ] Multiple sources contribute active Approved Inputs to one Project
- [ ] No raw Source or unreviewed proposal is treated as Approved Input

Record active Approved Inputs:

| Approved Input ID | Source | Stable subject / title | Information type | Active? |
|---|---|---|---|---:|
| | | | | [ ] |
| | | | | [ ] |
| | | | | [ ] |
| | | | | [ ] |

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

Formative checkpoint:

- [ ] It is clear what has become authoritative Approved Input
- [ ] It is clear which source/review produced each Approved Input
- [ ] Cross-document content can coexist without losing origin

Observation IDs:

-

---

# 8. Phase E — Cross-document Model Candidate generation

## TC-E01 — Generate one Candidate Set from the active Approved-Input snapshot

Precondition:

- [ ] Active Approved Inputs exist from more than one source

Action:

Trigger the normative Candidate-generation path exposed by the demonstrator.

Expected:

- [ ] Generation consumes the active Approved-Input snapshot
- [ ] One new explicit Candidate Set is created
- [ ] Candidate Set retains exact Approved-Input references
- [ ] No Candidate is silently Human-approved
- [ ] Candidate generation does not use raw Sources directly as authority
- [ ] Model Proposal becomes available for the exact Candidate Set

Record:

- Candidate Set ID:
- Candidate Set fingerprint:
- Active Approved Input count:
- Element Candidate count:
- Relationship Candidate count:
- Generation provenance:

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

If no UI bridge exists:

- classify as `INTEGRATION`
- record exact missing action
- stop at this point
- implement only the authority-preserving bridge
- rerun focused tests
- continue with the same formal protocol after correction

Observation / defect ID:

-

---

## TC-E02 — Verify cross-document synthesis

Compare the Model Proposal to `wp12_expected_engineering_contract.md`.

### Minimum semantic checks

Roles:

- [ ] microscope operator represented or otherwise preserved as relevant external/user concept
- [ ] remote expert represented or otherwise preserved as relevant external/user concept

Capabilities / behaviors:

- [ ] collaboration/streaming session
- [ ] remote participation/join
- [ ] live microscope viewing
- [ ] request control
- [ ] explicit normal transfer decision
- [ ] remote microscope adjustment/control
- [ ] connection-loss revocation / safe return
- [ ] session/control-event traceability

Constraints:

- [ ] single active controller
- [ ] current controller visibility
- [ ] explicit normal transfer
- [ ] connection-loss authority revocation
- [ ] session lifecycle/control changes recorded

Technical meaning:

- [ ] microscope workstation
- [ ] remote client
- [ ] streaming responsibility
- [ ] control responsibility
- [ ] session/audit responsibility

The exact model shape may differ.

For every unchecked item record:

- Is the concept absent?
- Is it represented under another abstraction?
- Was it intentionally rejected during Human Review?
- Is it an expected Human modeling decision?
- Is it a defect?

Result: [ ] PASS [ ] PASS WITH FINDINGS [ ] FAIL [ ] BLOCKED

---

## TC-E03 — Verify overlap and provenance

Choose at least one concept supported by more than one source, preferably remote
viewing or control.

Expected:

- [ ] The combined proposal does not require duplicate model meaning merely because wording differs
- [ ] Contributing Approved Inputs remain traceable
- [ ] Source provenance remains inspectable through the Candidate / technical evidence
- [ ] Consolidation does not erase disagreement or unique source meaning

Evidence:

-

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

---

## TC-E04 — Verify Relationship Choice / ambiguity behavior

If multiple Candidate alternatives exist:

Expected:

- [ ] Alternatives are presented together
- [ ] Preferred status, if persisted, is visible
- [ ] Alternatives are not presented as Persona votes
- [ ] Human decision remains required
- [ ] Accepting one alternative targets that exact Candidate

If no alternative is generated:

- [ ] Record `NOT EXERCISED` rather than inventing one

Result: [ ] PASS [ ] NOT EXERCISED [ ] FAIL [ ] BLOCKED

---

# 9. Phase F — Candidate Human Review and Phase-I readiness

## TC-F01 — Review Model Candidates

Expected:

- [ ] Open Candidate decisions are obvious
- [ ] Accept / Reject / Defer acts on exact Candidate identity
- [ ] Nonconformant accepted Candidate requires exception path/rationale
- [ ] UI refresh reconstructs persisted Candidate Review state
- [ ] No session-state approval authority exists

Record significant decisions:

| Candidate | Type | Human decision | Rationale required? | Decision ID |
|---|---|---|---:|---|
| | | | | |
| | | | | |
| | | | | |

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

---

## TC-F02 — Phase-I readiness

Expected:

- [ ] Candidate Set remains not ready while required decisions exist
- [ ] Blocking profile/repository issues prevent progression
- [ ] Ready state appears only from authoritative Phase-I gate
- [ ] When ready, redundant Candidate write controls disappear

Phase-I status:

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

---

# 10. Phase G — Internal Engineering Model

## TC-G01 — Assemble / persist IEM from exact reviewed Candidate Set

Expected:

- [ ] Exact Phase-I-ready Candidate Set is used
- [ ] Only eligible accepted Candidates enter the IEM
- [ ] Rejected/deferred Candidates do not silently enter
- [ ] Accepted exceptions remain identifiable
- [ ] IEM provenance points back to Candidate / Approved Input evidence
- [ ] IEM assembly is deterministic for the same accepted input

Record:

- IEM ID/version:
- Source Candidate Set:
- Element count:
- Relationship count:

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

If no Guided UI execution bridge exists:

- [ ] classify as INTEGRATION
- [ ] do not manually fake an authoritative IEM
- [ ] implement the minimal authority-preserving bridge
- [ ] regression-test before continuing

---

# 11. Phase H — SysML v2 generation

## TC-H01 — Generate SysML v2 from exact IEM

Expected:

- [ ] Generation targets exact IEM
- [ ] Generated SysML is derived artifact, not CATIA authority
- [ ] Generated artifact set has immutable identity/fingerprint
- [ ] Traceability to IEM is retained
- [ ] No direct hand-edit is required to make the workflow progress

Record:

- Generated artifact set ID:
- Fingerprint:
- Generated file(s):
- Syntax/profile:

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

---

# 12. Phase I — Validation

## TC-I01 — Validate exact generated artifact set

Expected:

- [ ] Validation result binds exact generated artifact fingerprint
- [ ] Invalid/incomplete validation remains fail-closed
- [ ] No UI action converts missing validation into PASS
- [ ] Findings are understandable in Final Review preparation

Record:

- Validation result ID:
- Artifact fingerprint binding:
- Validation status:
- Publication gate:
- SYSIDE CLI used? YES / NO

Result: [ ] PASS [ ] FAIL [ ] EXTERNAL BLOCKER

### SYSIDE-specific evidence

If CLI unavailable:

- [ ] absence recorded
- [ ] dedicated live acceptance remains blocked/skipped
- [ ] no bypass introduced
- [ ] automated non-live validation evidence retained

---

# 13. Phase J — Final Model Review

## TC-J01 — Create/open exact Final Model Review

Expected:

- [ ] Review binds exact generated artifact + exact validation result
- [ ] Generated model/code is inspectable
- [ ] Validation and traceability are inspectable
- [ ] Change requests create immutable proposals/revisions
- [ ] Change interaction does not mutate generated SysML directly

Record:

- Final Model Review ID:
- Revision ID:
- Validation status shown:
- Blocking findings:

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

---

# 14. Phase K — Human release approval

## TC-K01 — Approve exact validated Final Review revision

Expected:

- [ ] Release requires explicit reviewer identity
- [ ] Release targets exact Final Review revision
- [ ] Stale/non-ready revision cannot be approved
- [ ] Approval is persisted as immutable Human decision
- [ ] Approval is distinct from validation success

Record:

- Release decision ID:
- Reviewer:
- Revision:

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

---

# 15. Phase L — Publication

## TC-L01 — Publish exact approved revision

Expected:

- [ ] Only exact approved revision is eligible
- [ ] Publication rechecks validation/release gates
- [ ] Output package is immutable/versioned
- [ ] Published SysML bytes match reviewed eligible bytes
- [ ] Package retains traceability and fingerprints
- [ ] Repeating exact publication input is idempotent where specified

Record:

- Output Package ID:
- Output path:
- Package fingerprint:
- Published SysML fingerprint:

Result: [ ] PASS [ ] FAIL [ ] EXTERNAL BLOCKER

---

# 16. End-to-end traceability audit

Select at least three final model concepts:

1. remote viewing/streaming
2. control authority / transfer
3. session traceability

For each, trace backwards as far as available:

```text
Published / generated model
← IEM
← Candidate
← Approved Input
← Human Review Item / Decision
← Processing artifact
← Source
```

| Concept | Final model ref | Candidate | Approved Input | Review item | Source(s) | Trace complete? |
|---|---|---|---|---|---|---:|
| Remote viewing | | | | | | [ ] |
| Control authority | | | | | | [ ] |
| Session traceability | | | | | | [ ] |

Expected:

- [ ] No selected concept loses all source provenance
- [ ] Cross-document concept may reference more than one Approved Input/source
- [ ] Technical View exposes evidence without making IDs necessary for normal work

Result: [ ] PASS [ ] FAIL [ ] BLOCKED

---

# 17. Formative self-evaluation completion

Complete:

`collaboration/ux/wp12_formative_self_evaluation_log.md`

Mandatory:

- [ ] Material UX observations recorded
- [ ] Material integration observations recorded
- [ ] Expected Human decisions distinguished from defects
- [ ] External blockers distinguished from implementation defects
- [ ] Every demo-critical finding has a disposition
- [ ] No finding is silently ignored because the demo is imminent

Result: [ ] PASS [ ] FAIL

---

# 18. Post-fix automated regression

After all bounded dry-run fixes:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q
git diff --check
```

Expected:

- [ ] Complete repository regression PASS
- [ ] Only deliberate documented skip(s)
- [ ] `git diff --check` PASS

Record:

- Passed:
- Skipped:
- Duration:
- Commit / worktree reference:

Result: [ ] PASS [ ] FAIL

---

# 19. Dry-Run Release Gate

Evaluate every criterion in:

`collaboration/audits/wp12_test_release_workflow.md`

## Critical result summary

| Area | Result |
|---|---|
| Multi-source registration | PASS / FAIL / BLOCKED |
| Processing | PASS / FAIL / BLOCKED |
| Human Review | PASS / FAIL / BLOCKED |
| Approved Input | PASS / FAIL / BLOCKED |
| Cross-document synthesis | PASS / FAIL / BLOCKED |
| Candidate Review | PASS / FAIL / BLOCKED |
| IEM | PASS / FAIL / BLOCKED |
| SysML generation | PASS / FAIL / BLOCKED |
| Validation | PASS / FAIL / EXTERNAL BLOCKER |
| Final Model Review | PASS / FAIL / BLOCKED |
| Human release | PASS / FAIL / BLOCKED |
| Publication | PASS / FAIL / EXTERNAL BLOCKER |
| Traceability | PASS / FAIL / BLOCKED |
| Formative self-evaluation | PASS / FAIL |
| Full regression | PASS / FAIL |

## Final protocol decision

- [ ] **PASS — RELEASED FOR REAL TEST DATA**
- [ ] **PASS WITH DOCUMENTED EXTERNAL LIMITATION — RELEASED FOR REAL TEST DATA**
- [ ] **FAIL — NOT RELEASED**

Release rationale:

-

Protocol deviations:

- None / describe every deviation from the accepted baseline protocol.

Impact of protocol deviations on result validity:

-

Open non-critical findings:

-

Known external limitations:

-

Tester / release approver:

Date:

Repository commit:

---

# 20. Stage-B handoff

Only complete if release is granted.

- [ ] New real-data test Project will be isolated from synthetic dry-run Project
- [ ] Real source files selected
- [ ] Original files preserved unchanged
- [ ] Stage-B objective documented
- [ ] Same Human authority gates retained
- [ ] No downstream authoritative artifacts pre-seeded
- [ ] Separate observation/result record prepared

**Stage B authorized:** YES / NO
