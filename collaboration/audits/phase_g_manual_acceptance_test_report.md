# Phase G Manual Acceptance Test Procedure and Report

**Artifact type:** Integration / manual acceptance test record
**Scope:** Phase G — Human Review, Finalization, Approved Input Promotion, Reopen lifecycle, Scoped Actions and running-state execution guard
**Status:** PASS — G7.3 manual acceptance complete
**Execution date:** 2026-08-12
**Test project:** `334441 · G Acceptance`

---

## 1. Purpose

This test verifies the complete Phase-G acceptance path through the real Streamlit application and persisted project repositories.

The test demonstrates that:

1. Agent outputs and consensus remain evidence rather than approval authority.
2. Human review decisions create immutable Review Revisions.
3. Open Review Items block finalization.
4. Accepted, rejected and deferred outcomes are handled according to contract.
5. Unresolved relationships cannot be accepted as valid model relationships.
6. Finalization requires an exact persisted Human Review Decision.
7. Finalization produces the exact immutable three-artifact authority set.
8. Only eligible finalized Review Items can be promoted to Approved Inputs.
9. Approved Input authority remains traceable to the exact finalized Review.
10. Reopening creates a new draft successor without modifying the finalized predecessor.
11. Scoped Actions require a materialized impact preview before a write and affect only the selected Review Items.
12. A running Agentic Ingestion does not expose a second Run/Retry write action.

---

## 2. Test Basis

Primary deterministic Human Review fixture:

```text
Project              334441 · G Acceptance
Source               SRC-000002
Filename             g7_human_review_fixture.md
Processing Run       RUN-000002
Attempt              ATT-000001
Review Document      RVD-000001
Review Version       RVV-000001
Initial Revision     RVR-000001
Reviewer             MD
```

Fixture scope:

```text
5 Review Items
3 element items
2 relationship items
2 Agent derivation perspectives
structured Source Evidence
Consensus Evidence where available
```

No external LLM call was required for this deterministic fixture.

A separate live Source was registered only for the final running-state UI acceptance check:

```text
Filename             g7_f03_retry_guard_fixture.md
Processing Run       RUN-000004
Attempt              ATT-000001
Mode                 Live LLM
Final state          awaiting_review
Published files      15
```

---

## 3. Test Procedure and Results

| ID | Procedure | Expected Result | Observed Result | Status |
|---|---|---|---|---|
| G7-MA-01 | Open initial Human Review Workspace. | Review is draft; 5 items open; finalization and promotion blocked. | Initial workspace created with `RVD-000001`, `RVV-000001`, `RVR-000001`; finalization and promotion blocked. | PASS |
| G7-MA-02 | Perform an item-level human edit and accept action. | A new immutable Review Revision is created; predecessor remains unchanged. | `RVR-000002` created from `RVR-000001` with `accepted_with_modification`. An accidental repeated UI action created `RVR-000003` from `RVR-000002`, confirming append-only revision behavior. | PASS |
| G7-MA-03 | Accept element proposals as generated. | New Revision; item outcome becomes `accepted_as_generated`. | `RIT-000001` and `RIT-000002` recorded as `accepted_as_generated`. | PASS |
| G7-MA-04 | Reject one complete Review Item with human rationale. | New Revision; rejected item is no longer open and cannot be promoted. | `RIT-000003` recorded as `rejected`. | PASS |
| G7-MA-05 | Attempt to accept an unresolved relationship proposal. | Acceptance is blocked until its SysML v2 relationship representation is valid. | Acceptance of `RIT-000004` / `LINK_001` was blocked while `validation_status = unresolved` and `sysml_v2_construct = None`. | PASS |
| G7-MA-06 | Defer unresolved relationship items. | Deferred unresolved relationships do not represent accepted model authority and no longer block finalization. | `RIT-000004` and `RIT-000005` recorded as `deferred`; both remain `unresolved`. | PASS |
| G7-MA-07 | Complete all Review Item decisions. | Current Revision becomes eligible for confirmation with zero blocking findings. | `RVR-000008`: `Eligible = true`, `Blocking findings = 0`. | PASS |
| G7-MA-08 | Record exact detailed Human Review confirmation. | Persisted HRD binds the exact current Review Revision and validation fingerprint. | `HRD-000001`, decision `confirm`, recorded for `RVR-000008` and its exact validation fingerprint. | PASS |
| G7-MA-09 | Finalize the exact confirmed Review Version. | Version becomes finalized and immutable; finalization remains bound to exact Revision and HRD. | `RVV-000001` finalized on `RVR-000008` using `HRD-000001`. | PASS |
| G7-MA-10 | Inspect Finalized Artifact Set. | Exactly three immutable artifacts exist. | `reviewed_document.json`, `effective_decisions.json`, `reviewed_report.md` persisted with one artifact-set fingerprint. | PASS |
| G7-MA-11 | Inspect promotion eligibility. | Only promotable finalized Review Items are eligible. | 2 of 5 items eligible; rejected and deferred items correctly excluded. | PASS |
| G7-MA-12 | Promote eligible finalized items to Approved Inputs. | Approved Input manifests/events are created only from exact finalized authority. | `AIN-000001` and `AIN-000002` created. `RIT-000003`, `RIT-000004` and `RIT-000005` were skipped. | PASS |
| G7-MA-13 | Inspect Approved Input authority and traceability. | Active AIN authority references exact Review Document, Version, Revision, Review Item, finalization decision, Source, Run and Attempt. | Both active AIN manifests reference `RVD-000001`, `RVV-000001`, `RVR-000008`, `HRD-000001`, `SRC-000002`, `RUN-000002`, `ATT-000001` and the exact finalized artifact-set fingerprint. | PASS |
| G7-MA-14 | Reopen finalized Review Version. | Finalized predecessor remains immutable; new draft Version, Revision and fresh Review Item identities are created with lineage. | `RVV-000002` created as draft with `predecessor_version_id = RVV-000001`; initial successor `RVR-000009`; fresh `RIT-000006` … `RIT-000010` each reference the corresponding predecessor Review Item. | PASS |
| G7-MA-15 | Re-check predecessor hashes / artifacts after successor creation. | Finalized predecessor and artifact set remain byte-identical. | Whole-tree SHA-256 baseline of `RVV-000001` compared before and after Reopen with no diff. | PASS |
| G7-MA-16 | Preview and apply an explicit Scoped Action to exactly one Review Item. | Preview materializes only the selected target; write creates a new immutable Revision and leaves other items unchanged. | Explicit selection of `RIT-000006` produced `Materialized = 1`, `Affected now = 1`, no precedence/exclusion conflicts. Apply created `RVR-000010`, `SRA-000001`, and `epistemic_status = confirmed` only for `RIT-000006`. Other Review Item fingerprints remained unchanged. | PASS |
| G7-MA-17 | Start live Agentic Ingestion and inspect UI while persisted state is `running`. | Running identity is visible and no second Run/Retry write action remains available. | During `RUN-000004` / `ATT-000001`, UI displayed `running · agentic_ingestion` and the Run/Retry write button was absent. The Run subsequently completed to `awaiting_review` with 15 published files. | PASS |

---

## 4. Finalized Review State Observed

| Review Item | Kind | Outcome | Relationship validation | Promotion eligibility |
|---|---|---|---|---|
| `RIT-000001` | element | `accepted_as_generated` | not applicable | eligible |
| `RIT-000002` | element | `accepted_as_generated` | not applicable | eligible |
| `RIT-000003` | element | `rejected` | not applicable | not promotable |
| `RIT-000004` | relationship | `deferred` | `unresolved` | not promotable |
| `RIT-000005` | relationship | `deferred` | `unresolved` | not promotable |

Finalization authority:

```text
Review Document           RVD-000001
Review Version            RVV-000001
Finalized Revision        RVR-000008
Human Review Decision     HRD-000001
Decision                  confirm
Reviewer                  MD
Decision time             2026-08-12T07:54:52Z
Finalized at              2026-08-12T07:57:03Z
Artifact-set fingerprint  5c1a76198221f94f0fd205af8b1c80554d19cec337d733215ff19e29353d4f51
```

Exact finalized artifacts:

```text
reviewed_document.json
effective_decisions.json
reviewed_report.md
```

Observed artifact SHA-256 values:

```text
reviewed_document.json
3d1985c26f2b9586bb76069b79d75a8fa714d746f8aad69b65377fcc8ae412bc

effective_decisions.json
095f14bafbd89d21e047f3b59eb29e26359f14f6d3bc6f40da5f7f79a738c78f

reviewed_report.md
88a4fc3568c0e0b709655b479b65c4c9ebd9fa4734ed74e65b95cff7ac8b9026
```

---

## 5. Approved Input Authority Evidence

Promotion produced exactly two active Approved Inputs:

```text
AIN-000001
  Review Item                RIT-000001
  kind                       element_statement
  authority_state            active
  Review Document            RVD-000001
  Review Version             RVV-000001
  Review Revision            RVR-000008
  Human Review Decision      HRD-000001
  Source                     SRC-000002
  Processing Run             RUN-000002
  Attempt                    ATT-000001

AIN-000002
  Review Item                RIT-000002
  kind                       element_statement
  authority_state            active
  Review Document            RVD-000001
  Review Version             RVV-000001
  Review Revision            RVR-000008
  Human Review Decision      HRD-000001
  Source                     SRC-000002
  Processing Run             RUN-000002
  Attempt                    ATT-000001
```

Both manifests reference the exact finalized artifact-set fingerprint:

```text
5c1a76198221f94f0fd205af8b1c80554d19cec337d733215ff19e29353d4f51
```

No rejected or deferred Review Item was promoted.

---

## 6. Reopen and Lineage Evidence

The finalized predecessor was reopened into a new draft successor:

```text
RVV-000001 finalized
    ↓ reopen
RVV-000002 draft
predecessor_version_id = RVV-000001

RVR-000009
predecessor_revision_id = None
```

The initial successor Review Items received fresh identities while preserving explicit lineage:

```text
RIT-000006 ← RIT-000001
RIT-000007 ← RIT-000002
RIT-000008 ← RIT-000003
RIT-000009 ← RIT-000004
RIT-000010 ← RIT-000005
```

The whole `RVV-000001` subtree was hashed before and after Reopen. The comparison produced no output, confirming byte-identical predecessor persistence.

---

## 7. Scoped Action Evidence

A first impact preview using the complete-document scope intentionally demonstrated that the preview exposes an incorrect target set before the write:

```text
Materialized    5
Affected now    5
```

The scope was then corrected to:

```text
Explicit manual selection
Review Item     RIT-000006
Dimension       Classification
Field           epistemic_status
Operation       set
Value           confirmed
```

The required new preview showed:

```text
Materialized                       1
Affected now                       1
Item overrides                     0
Higher precedence                  0
Excluded                           0
Would overwrite after confirmation 0
```

After Apply:

```text
Review Version       RVV-000002
New Revision         RVR-000010
Scoped Actions       1
Scoped Action ID     SRA-000001
RIT-000006           epistemic_status=confirmed
Origin               explicit_selection
```

The remaining Review Items retained their previous content fingerprints.

---

## 8. Running-State Write-Action Guard

The final F03 correction was verified automatically and manually.

Focused automated regression:

```text
tests/test_turing_generator_ingestion_running_action.py
2 passed in 1.09s

git diff --check
PASS
```

Manual acceptance used a fresh registered Source. During the synchronous live execution the UI displayed:

```text
Starting Agentic Ingestion…

Agentic Ingestion is running · RUN-000004 · ATT-000001 · agentic_ingestion.
```

At that point no second `Run Agentic Ingestion` or `Retry Agentic Ingestion` write action was visible.

The same Run then completed normally:

```text
RUN-000004
ATT-000001
State             awaiting_review
Stage             agentic_ingestion
Mode              Live LLM
Published files   15
```

This closes G7.3-F03.

---

## 9. Fail-Closed Relationship Behavior

Observed relationship representation before the blocked accept action:

```text
semantic_intent            is_subject_of
sysml_v2_construct         None
target_notation_profile    SYSML_V2_TARGET 1.0.0
validation_status          unresolved
validation_fingerprint     None
```

The Human Review workflow correctly blocked acceptance.

This confirms that a plausible natural-language relationship does not become accepted model authority merely because an Agent proposed it.

---

## 10. Usability Findings

### UX-01 — Write action feedback

A Review action was accidentally triggered twice because the Streamlit rerender was not sufficiently visible.

Desired behavior:

```text
click
→ disable write action
→ visible processing / saving state
→ explicit success feedback
→ enable next action
```

### UX-02 — Generic relationship validation error

Blocked relationship acceptance currently produces a generic message covering validation, integrity and stale-state checks.

The default user view should instead expose the actionable reason, for example that the relationship representation is not yet validated.

### UX-03 — Information density

The current Human Review page exposes proposal details, evidence, fingerprints, traceability and edit controls simultaneously.

The later UX architecture shall preserve all information while applying:

```text
simple by default
explainable on demand
fully traceable underneath
```

These are usability improvement candidates. They do not invalidate the Phase-G authority or lifecycle acceptance result.

---

## 11. Evidence

Manual evidence captured during the acceptance run includes:

```text
- finalized RVV-000001 / RVR-000008
- HRD-000001
- finalization and artifact-set fingerprints
- exact three-artifact Finalized Artifact Set
- promotion completion and AIN authority
- Reopen RVV-000002 / RVR-000009 and item lineage
- Scoped Action preview and RVR-000010 result
- running-state UI without a second Run/Retry write action
- successful completion of RUN-000004
```

Recommended repository evidence location:

```text
collaboration/audits/evidence/phase_g/
```

The final evidence package may be copied there during the Phase-G documentation / SSOT closeout.

---

## 12. Thesis-Relevant Interpretation

This manual integration test demonstrates:

```text
Agent proposal
≠
authoritative engineering information
```

Agent outputs and consensus provide evidence and candidate interpretations. Authority is established only through an explicit, traceable Human Review workflow.

The tested authority chain is:

```text
Source
→ Processing Run / Attempt
→ Agent evidence
→ Human Review
→ immutable Review Revisions
→ exact Human Review Decision
→ immutable Finalized Artifact Set
→ Approved Input authority
```

The test additionally demonstrates that:

```text
recovery / successor lifecycle
and
human interaction safety
```

are part of end-to-end correctness. Reopen preserves immutable predecessor evidence, Scoped Actions require explicit impact materialization, and long-running ingestion does not leave a second write action available.

---

## 13. Exit Criterion

```text
[PASS] Human Review item actions
[PASS] immutable revision behavior
[PASS] fail-closed relationship acceptance
[PASS] finalization eligibility
[PASS] exact Human Review confirmation
[PASS] exact three-artifact finalization
[PASS] promotion eligibility filtering
[PASS] Approved Input promotion
[PASS] Approved Input authority / traceability
[PASS] Reopen successor lifecycle
[PASS] predecessor immutability after Reopen
[PASS] Scoped Action + Impact Preview
[PASS] running-state write-action guard
```

**Final result: PASS — G7.3 manual acceptance complete.**
