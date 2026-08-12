# Phase G Manual Acceptance Findings

**Phase:** G7.3 — Manual Acceptance
**Initial execution:** 2026-08-10
**Closed / verified:** 2026-08-12
**Status:** CLOSED — all implementation findings corrected and verified
**Purpose:** Preserve reproducible implementation findings from real end-to-end use of the Phase-G application for engineering review and thesis evaluation.

---

## 1. Test Context

The findings below were discovered during manual end-to-end acceptance of the real Streamlit application rather than through isolated unit tests.

The acceptance path covered:

```text
Project / Source registration
→ live Agentic Ingestion
→ retry / recovery behavior
→ Human Review & Approval
→ Finalization
→ Approved Input Promotion
→ Reopen successor lifecycle
→ Scoped Action
→ running-state execution guard
```

The manual acceptance run was started only after substantial automated verification had already passed, including:

```text
G6 focused regression: 145 passed
G7.1 persisted Phase-G end-to-end integration: 1 passed
G7.2 successor lifecycle integration: 6 passed
```

The findings therefore represent integration, lifecycle and usability defects exposed by real application use rather than synthetic unit-test failures.

---

## 2. G7.3-F01 — Streamlit widget-owned Session State was overwritten

### Observed behavior

Opening `Human Review & Approval` raised a `StreamlitAPIException` because the application wrote to a keyed widget-owned Session State entry after widget instantiation.

### Technical cause

The reviewer identity input used:

```text
human_review_approval.reviewer_identity
```

as a keyed Streamlit widget and the same render cycle then assigned the returned value directly back to that Session State key.

The real framework rejects this pattern, while the original test double did not reproduce that runtime rule.

### Impact

```text
Severity: blocking UI defect
Affected boundary: Human Review entry
Data integrity impact: none observed
Usability impact: Human Review could not be opened
```

### Correction

The redundant post-widget assignment was removed. The keyed Streamlit widget remains the owner of its Session State entry.

The regression coverage was strengthened to represent the relevant Streamlit state rule.

### Verification / status

```text
Manual Human Review UI entry: PASS
G7.3 continuing acceptance: PASS
Status: CLOSED
```

### Thesis relevance

This finding demonstrates that test doubles can preserve green unit tests while omitting framework-specific runtime semantics. Realistic integration testing remains necessary at framework boundaries.

---

## 3. G7.3-F02 — Failed Agentic Ingestion Run could not be retried

### Observed behavior

The first live Agentic Ingestion attempt failed because invalid API credentials were used. The failed Source could not initially be retried through the project-bound application even though the lower-level Processing lifecycle already supported immutable Attempts.

### Architectural mismatch

The lower-level Processing contract supported:

```text
failed
→ retry_started
→ running
```

with a new Attempt in the same Processing Run.

The project-bound ingestion service originally exposed only a current-run guard and therefore made the lower-level retry lifecycle unreachable.

### Accepted / implemented behavior

For unchanged material Run bindings:

```text
failed retryable Run
→ Retry Agentic Ingestion
→ same RUN ID
→ next ATT ID
```

For changed material Run bindings:

```text
material configuration changed
→ retry is not allowed as the same Run
→ explicit successor lifecycle is required
```

API credentials are not persisted as material Run bindings and therefore do not change the Run configuration fingerprint.

### Impact

```text
Severity: blocking recovery/workflow defect
Affected boundary: project-bound Processing recovery
Data corruption observed: no
```

### Correction

Project-bound Agentic Ingestion was integrated with the existing Processing retry lifecycle. Retry preserves the failed Run identity and creates a new immutable Attempt.

The UI also validates that the current material configuration matches the failed Run before exposing a valid retry write path.

### Verification / status

```text
Same-Run retry semantics exercised during G7.3
Changed material configuration correctly blocks same-Run retry
Status: CLOSED
```

### Thesis relevance

This is a system-level integration defect where a correct lower-level lifecycle capability existed but was not reachable through the application workflow. It illustrates why component correctness alone is insufficient.

---

## 4. G7.3-F03 — Running Agentic Ingestion feedback and write-action guard

### Initial observed behavior

A long-running live Agentic Ingestion initially lacked sufficiently clear persisted execution identity and operational feedback.

After the first correction, the application displayed:

```text
RUN ID
ATTEMPT ID
state = running
stage = agentic_ingestion
```

but one remaining defect was exposed during manual acceptance: in the same synchronous Streamlit render that started or retried execution, the already-rendered Run/Retry button remained visible while the execution observer displayed the new `running` state.

This produced the unsafe visual combination:

```text
Retry Agentic Ingestion
+
Agentic Ingestion is running
```

even though backend lifecycle guards prevented a duplicate current Run.

### Technical cause

The project-bound ingestion call executes synchronously inside the Streamlit button handler.

The persisted-state guard for a later rerender was already correct:

```text
run_state = running
→ render current execution state
→ return before Run/Retry action
```

The remaining problem existed only inside the active render cycle: the button had already been materialized before the observer reported the new running Attempt.

### Correction

The Run/Retry write control is now rendered through a Streamlit placeholder.

After the user clicks the write action:

```text
click Run/Retry
→ remove action placeholder immediately
→ mark local execution in progress
→ start synchronous service call
→ observer renders persisted RUN / ATT / stage
```

Therefore no second write control remains visible while the operation is running.

The persisted-state early-return guard remains authoritative for later rerenders.

### Verification

Focused automated regression:

```text
tests/test_turing_generator_ingestion_running_action.py
2 passed in 1.09s

git diff --check
PASS
```

Manual acceptance with a fresh Source:

```text
RUN-000004
ATT-000001
state = running
stage = agentic_ingestion
```

During `running`, no `Run Agentic Ingestion` or `Retry Agentic Ingestion` button was visible.

The same Run then completed:

```text
State             awaiting_review
Mode              Live LLM
Published files   15
```

### Impact

```text
Severity: significant usability / operational safety defect
Data integrity impact: duplicate current Run was already backend-blocked
User impact before correction: ambiguous repeated-action affordance
```

### Status

```text
CLOSED — automated and manual verification PASS
```

### Thesis relevance

The finding demonstrates that safe workflow operation depends on both authoritative lifecycle state and the user-facing affordances shown while a costly synchronous operation is active.

---

## 5. G7.3-F04 — Agentic Ingestion failure diagnosis was too generic

### Observed behavior

The original project-bound failure handling reduced pipeline failures to a generic ingestion failure, requiring external diagnosis to distinguish credential, provider, timeout or other failures.

### Required distinction

The UI must not expose secrets, raw stack traces or provider-internal sensitive data. However, the system still needs safe provider-neutral failure classification.

### Correction

Safe failure classes were introduced for relevant LLM/provider failure modes, including:

```text
llm_authentication_failed
llm_permission_denied
llm_rate_limited
llm_timeout
llm_connection_failed
llm_request_rejected
llm_provider_unavailable
```

Unknown failures continue to fall back to a generic safe ingestion failure message.

The user-facing layer maps these classifications to concise recovery guidance without exposing credentials or raw exception details.

### Impact

```text
Severity: diagnostic / recovery defect
Data integrity impact: none observed
Operational impact before correction: unnecessary troubleshooting
```

### Verification / status

```text
Provider-neutral failure classification exercised during G7.3
Safe UI messages preserved
Status: CLOSED
```

### Thesis relevance

This finding demonstrates the distinction between safe abstraction and insufficient observability. Sensitive technical details can remain hidden while retaining actionable, provider-neutral recovery information.

---

## 6. G7.3-F05 — Failed pre-publication Attempt identity was reused

### Observed behavior

A failed Agentic Ingestion Attempt was already present in immutable Processing Event History but had no artifact directory because it failed before publication.

The original `next_attempt_id()` implementation derived occupied Attempt identities only from artifact directories and could therefore return the already-used identity again.

### Invalid assumption

The implementation implicitly assumed:

```text
Attempt exists
⇔
Attempt has persisted artifacts
```

This is false for Attempts that fail before publication.

### Correction

Attempt identity allocation now derives occupied IDs from:

```text
immutable Processing Events
+
persisted artifact directories
```

The immutable event history is the primary lifecycle record; artifact directories provide an additional recovery signal.

### Verification

```text
Focused retry / Processing regression:
27 passed

Extended G7.3 ingestion / retry / UI regression:
28 passed

git diff --check:
PASS
```

### Impact

```text
Severity: processing identity / traceability defect
Affected boundary: Processing retry
Data corruption observed: no
Traceability risk before correction: duplicate Attempt identity within one Run
```

### Status

```text
CLOSED
```

### Thesis relevance

Persistent identity allocation must be derived from the authoritative lifecycle record rather than downstream artifacts that may legitimately be absent after an early failure.

---

## 7. G7.3-F06 — Review semantic-reference validation was stricter than Processing contract

### Observed behavior

The deterministic Human Review fixture could not be assembled although its semantic references were valid according to the Processing contract.

Processing accepts non-empty, trimmed semantic reference identifiers such as:

```text
BFO_2020/2020
IOF_CORE_202602/202602
TURING_CORE_VOCABULARY/1.0.0
```

The Review document manifest independently required a SemVer-style representation and therefore rejected references that Processing had already accepted.

### Technical cause

Two architectural layers implemented different validation rules for the same semantic-reference concept:

```text
Processing contract
→ non-empty trimmed semantic reference

Review manifest
→ stricter SemVer assumption
```

The Review layer therefore introduced an incompatible downstream interpretation of an already-established upstream contract.

### Correct behavior

Review must validate semantic-reference values according to the same authoritative Processing contract rather than inventing a second format constraint.

### Correction

`modules/review_workspace/document_manifest.py` was changed to delegate semantic-reference validation to the Processing-level contract.

### Verification

```text
Focused semantic-reference / Review regression:
24 passed in 0.27s

git diff --check:
PASS

Deterministic Human Review fixture assembly:
PASS
```

### Impact

```text
Severity: integration / contract consistency defect
Affected boundary: Processing → Human Review
Data integrity impact: none observed
Operational impact before correction: valid Processing evidence could not enter Review
```

### Status

```text
CLOSED
```

### Thesis relevance

The finding demonstrates the need for one authoritative validation contract for information crossing architectural boundaries. Duplicate validation logic can create false incompatibilities even when both components are individually deterministic.

---

## 8. Cross-Finding Interpretation

The G7.3 findings expose six distinct integration failure classes:

| Finding | Failure class | Main lesson |
|---|---|---|
| G7.3-F01 | Framework integration | Test doubles must reproduce relevant runtime semantics |
| G7.3-F02 | Architectural orchestration | Existing lifecycle capabilities must be reachable through application workflows |
| G7.3-F03 | Human-system interaction | Long-running operations require state feedback and safe write affordances |
| G7.3-F04 | Observability / recovery | Safe error abstraction must still preserve actionable diagnosis |
| G7.3-F05 | Identity / persistence | Identity allocation must use the authoritative lifecycle record |
| G7.3-F06 | Cross-layer contract consistency | Shared concepts require one authoritative validation contract |

All six findings emerged while exercising the application as a complete system.

The resulting verification strategy is:

```text
unit / component verification
→ focused integration tests
→ persisted end-to-end tests
→ real manual application acceptance
```

Manual acceptance is therefore not redundant with automated testing. It verifies real framework semantics, cross-layer orchestration, failure paths and human interaction that isolated tests can fail to represent.

---

## 9. Remaining UX Findings

The following observations remain intentional follow-up candidates rather than Phase-G acceptance blockers.

### UX-01 — Write-action feedback

A Human Review write action was accidentally triggered twice because the Streamlit rerender did not make the write lifecycle sufficiently visible.

Desired behavior:

```text
click
→ disable action
→ visible saving state
→ explicit success feedback
→ enable next action
```

### UX-02 — Actionable relationship validation feedback

A blocked unresolved relationship currently produces a generic validation/integrity error. The primary user view should show the actionable reason directly.

### UX-03 — Information density / progressive disclosure

The current Human Review page exposes too much engineering and traceability detail simultaneously.

The later UX architecture shall follow:

```text
simple by default
explainable on demand
fully traceable underneath
```

These items belong to the later guided-workflow / UX simplification work and do not change the completed Phase-G authority contracts.

---

## 10. Final G7.3 Finding Status

```text
G7.3-F01  CLOSED
G7.3-F02  CLOSED
G7.3-F03  CLOSED
G7.3-F04  CLOSED
G7.3-F05  CLOSED
G7.3-F06  CLOSED
```

No finding in this document changes CATIA engineering authority automatically.

Any observation that implies an engineering-model change remains a Model Element Change Candidate until engineering review and explicit acceptance.

**G7.3 implementation finding closure result: PASS.**
