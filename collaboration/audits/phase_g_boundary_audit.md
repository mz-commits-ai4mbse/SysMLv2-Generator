# Phase G Boundary and Recovery Audit Matrix

## Purpose

This audit maps the accepted Phase-G authority boundaries to concrete
implementation and automated verification evidence.

It does not redefine engineering authority. CATIA remains authoritative for
engineering requirements; the committed repository remains authoritative for
implementation reality.

G7.1 and G7.2 add end-to-end integration evidence. G7.3 will add manual UI
acceptance evidence. Final pass/fail results and the Phase-G completion decision
are recorded during G7.5.

## Boundary Matrix

| Boundary | Verification evidence | Coverage type |
|---|---|---|
| Unreviewed processing evidence cannot become Approved Input | `tests/test_approved_input_promotion_eligibility.py`, `tests/test_approved_input_promotion_service.py` | Automated |
| P9 is the Review Document anchor; P4 cannot independently establish a Review Document authority chain | `modules/review_workspace/review_document_assembly.py`, `tests/test_review_workspace_review_document_assembly.py` | Contract + automated |
| Consensus and confidence are evidence only and cannot authorize finalization or promotion | `modules/review_workspace/finalization_authorization.py`, `modules/approved_input/eligibility.py` | Contract + automated |
| Stale Review state cannot authorize a changed target | `tests/test_review_approval_item_editing_service.py`, `tests/test_review_workspace_finalization_authorization.py` | Automated |
| Finalization requires exact detailed Human Review confirmation | `tests/test_review_workspace_finalization_authorization.py`, `tests/test_review_approval_finalization_service.py` | Automated |
| Fingerprint mismatch blocks finalized authority | `tests/test_review_workspace_finalization_validation.py`, `tests/test_finalized_artifact_loading.py` | Automated |
| Source, Processing Run, Attempt and published artifacts are revalidated before promotion | `tests/test_approved_input_promotion_eligibility.py`, `tests/test_approved_input_promotion_service.py` | Automated |
| Published P9 evidence is immutable and fingerprint-bound | `tests/test_review_workspace_evidence_adapter.py` | Automated |
| Finalized authority consists of exactly three mutually consistent immutable artifacts | `tests/test_finalized_artifact_loading.py`, `tests/test_finalized_artifact_persistence.py` | Automated |
| Interrupted finalized publication/loading requires explicit recovery | `tests/test_finalized_artifact_loading.py`, `tests/test_finalized_artifact_recovery.py` | Automated |
| Tampered finalized artifacts fail closed | `tests/test_finalized_artifact_loading.py`, `tests/test_phase_g_successor_lifecycle_integration.py` | Automated + G7.2 integration |
| Reopening never mutates the finalized predecessor | `tests/test_review_workspace_reopening.py`, `tests/test_phase_g_successor_lifecycle_integration.py` | Automated + G7.2 integration |
| Review Version history remains linear and successor identities are fresh | `tests/test_review_workspace_reopening.py`, `tests/test_phase_g_successor_lifecycle_integration.py` | Automated + G7.2 integration |
| Unchanged accepted successor retains the existing active AIN | `tests/test_approved_input_successor_reconciliation.py`, `tests/test_phase_g_successor_lifecycle_integration.py` | Automated + G7.2 integration |
| Materially changed accepted successor creates a new AIN and supersedes the predecessor | `tests/test_approved_input_g5_integration.py`, `tests/test_phase_g_successor_lifecycle_integration.py` | Automated + G7.2 integration |
| Rejected or out-of-scope successor revokes the active predecessor | `modules/approved_input/lifecycle_service.py`, `tests/test_phase_g_successor_lifecycle_integration.py` | Contract + G7.2 integration |
| Deferred successor does not silently revoke existing authority | `modules/approved_input/lifecycle_service.py`, `tests/test_phase_g_successor_lifecycle_integration.py` | Contract + G7.2 integration |
| Inactive AINs are excluded from the stable Phase-H read contract | `tests/test_approved_input_g5_integration.py`, `tests/test_phase_g_successor_lifecycle_integration.py` | Automated + G7.2 integration |
| Project boundaries are fail-closed across Source, Processing, Review and Approved Input | project-isolation tests in `tests/test_project_source_registry.py`, `tests/test_review_workspace_evidence_adapter.py`, and Approved Input repository/lifecycle tests | Automated |
| G6 UI does not derive authority from session state and presents safe generic errors | `tests/test_human_review_approval_ui.py`, `tests/test_human_review_finalization_ui.py`, `tests/test_human_review_promotion_ui.py` | Automated; manual presentation check in G7.3 |
| Phase G ends at active Approved Inputs and does not generate Model Candidates or SysML v2 | ADR-016, `collaboration/roadmap.md`, `tests/test_phase_g_end_to_end_integration.py` | Architecture + G7.1 integration |

## G7 Integration Evidence

### G7.1

Target chain:

```text
Project
→ Engineering Source
→ Processing Run
→ published P9 evidence
→ Human Review Workspace
→ accepted Review Item
→ exact Human Review finalization
→ Finalized Artifact Set
→ Approved Input promotion
→ active-only Phase-H read contract
```

Automated evidence:

`tests/test_phase_g_end_to_end_integration.py`

### G7.2

Successor and recovery matrix:

```text
unchanged accepted successor
→ reuse active AIN

changed accepted successor
→ create successor AIN
→ supersede predecessor

rejected / out_of_scope successor
→ revoke predecessor

deferred successor
→ retain existing authority

tampered finalized predecessor
→ reopening blocked
→ no successor version created
```

Automated evidence:

`tests/test_phase_g_successor_lifecycle_integration.py`

## Remaining G7 Evidence

G7.3:

- manual Human Review and promotion UI acceptance
- visible authority/lifecycle distinction
- visible finalized artifact presentation
- reopening flow
- no repository paths or internal exception details in user-facing error states

G7.4:

- complete repository regression
- `git diff --check`

G7.5:

- Phase-G completion decision
- SSOT synchronization
- Model Element Change Candidate review
