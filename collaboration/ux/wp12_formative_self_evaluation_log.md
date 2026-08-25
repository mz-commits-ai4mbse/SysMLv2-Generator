# WP-12 Formative Self-Evaluation Log

## Method status

This is a formative, task-based self-evaluation performed by the developer /
Systems Engineer while executing the WP-12 demonstrator workflow.

It is qualitative design evidence. It is not an independent usability study and
shall not be used to claim statistically validated usability improvement.

## Run metadata

- Date:
- Tester:
- Repository commit:
- Project ID:
- Application entry point: `streamlit run app/turing_generator_app.py`
- LLM provider/model:
- Technical details mode at start: Focused / Technical
- Test-data stage: Synthetic dry run / Real test data
- Related protocol: `collaboration/audits/wp12_multi_document_dry_run_test_protocol.md`

## Observation scale

For each material observation, record one disposition:

- `PASS` — behavior is clear and acceptable
- `UX` — interaction/presentation friction
- `INTEGRATION` — connected workflow defect or missing bridge
- `ENGINEERING` — semantic/modeling concern requiring engineering review
- `EXPECTED_HUMAN_DECISION` — appropriate Human-in-the-Loop work
- `EXTERNAL_BLOCKER` — external dependency prevents completion
- `DEFERRED` — accepted for later work

## Observation record

| ID | Workflow step | User goal | Expectation | Observation | Friction / risk | Authority clear? | Next action clear? | Classification | Resolution |
|---|---|---|---|---|---|---|---|---|---|
| OBS-001 |  |  |  |  |  |  |  |  |  |
| OBS-002 |  |  |  |  |  |  |  |  |  |
| OBS-003 |  |  |  |  |  |  |  |  |  |
| OBS-004 |  |  |  |  |  |  |  |  |  |
| OBS-005 |  |  |  |  |  |  |  |  |  |
| OBS-006 |  |  |  |  |  |  |  |  |  |
| OBS-007 |  |  |  |  |  |  |  |  |  |
| OBS-008 |  |  |  |  |  |  |  |  |  |
| OBS-009 |  |  |  |  |  |  |  |  |  |
| OBS-010 |  |  |  |  |  |  |  |  |  |

## Step-level reflection prompts

At each major Human interaction point ask:

1. What was I trying to achieve?
2. Was the relevant engineering content visible before technical metadata?
3. Did I understand what the system had derived?
4. Were differences, uncertainty and alternatives visible?
5. Did I know which decision I was being asked to make?
6. Was it clear what would become authoritative after my action?
7. Could I inspect the source evidence when needed?
8. Did the UI make the next action obvious?
9. Did I need to understand internal IDs to proceed?
10. Did the system preserve information from all relevant source documents?

## End-of-run synthesis

### What worked well

-

### Most important UX findings

-

### Most important integration findings

-

### Engineering/modeling findings

-

### Findings that were expected Human decisions rather than defects

-

### External blockers

-

### Changes implemented during the dry run

-

### Deferred changes

-

### Overall formative conclusion

- [ ] Workflow understandable end to end
- [ ] Engineering content inspectable at each Human gate
- [ ] Cross-document synthesis understandable
- [ ] Authority boundaries understandable
- [ ] Traceability understandable on demand
- [ ] Next actions generally clear
- [ ] No demo-critical UX defect remains

---

## 2026-08-25 — SEM-015 single-source app acceptance

Project: `120412` — `WP12 R4c Live E2E`

### Verified acceptance results

| Check | Result | Observation |
|---|---|---|
| AC-01 Project context | PASS | Correct WP-12 project selected. |
| AC-02 Model Placement / Assembly authority | PASS | Human placement decisions and assembly state available. |
| AC-03 Assembly Final Review | PASS | `FAD-000001`, reviewer `MZ`, base `IEM-000001`. |
| AC-04 SEM-015 successor binding | PASS | Explicit `IEM-000002`, authority `TFA-000003` + `MQA-000001`; no implicit latest selection. |
| AC-05 Deterministic SysML generation | PASS | 13 elements, 1 formal relationship; two trace relationships intentionally not materialized. |
| AC-06 External SYSIDE validation | PASS | SYSIDE Modeler CLI 0.10.3, exit code 0, diagnostics 0. |
| AC-07 Streamlit validation cache | PASS | Navigation did not re-run SYSIDE or request Keychain access again. |
| AC-08 Phase-L Final Model Review handoff | FAIL / BLOCKING | Generated + validated `IEM-000002` had no `final_model_reviews/` workspace. |

### Blocking integration finding

`WP12-BLK-SEM015-L-001`

```text
IEM-000002
→ deterministic SysML generation       PASS
→ internal Phase-K validation          PASS
→ SYSIDE 0.10.3                        PASS
→ Phase-L Final Model Review           MISSING
→ Human release                        BLOCKED
→ Published Output                     BLOCKED
```

Confirmed persisted state before remediation:

```text
data/projects/120412/generated_sysml_v2/IEM-000002/artifact_set.json
data/projects/120412/generated_sysml_v2/IEM-000002/generated/generated_model.sysml
data/projects/120412/sysml_validation_v2/IEM-000002/validation_result.json

data/projects/120412/final_model_reviews/
MISSING
```

Disposition: blocking integration defect. The existing Phase-L authority model,
Human release gate and publication service remain normative. Remediation shall
only bridge the exact generated artifact and exact validation result into an
immutable `FMR` / `FRV` review subject; it shall not infer Human release or
publication authority.

### Additional observations

- The old persisted validation result for `IEM-000002` remains immutable and can
  differ from a current read-only validator run after validator implementation
  changes.
- Current and historical validation states are visually easy to confuse and
  remain a UI-quality finding.
- SYSIDE Keychain authentication occurred only when explicitly starting the
  external validation and did not repeat during normal navigation.

### 2026-08-25 — AC-08 authority-backed downstream remediation

The first Final Model Review start attempt created the authoritative container
`FMR-000001` but failed before `FRV-000001`.

Observed root cause:

```text
AuthorityBackedGeneratedSysMLArtifactSet
→ legacy FinalModelReviewRepository artifact validator
→ GeneratedSysMLArtifactSet-only integrity contract
→ FAIL
```

The authority-backed artifact intentionally replaces legacy Candidate-based
traceability with exact Human authority:

```text
element:
Approved Input + MPD

relationship:
SRD + FAD
```

Disposition:

- retain and reuse `FMR-000001`
- do not synthesize MCE/MCR/MCD or any legacy Candidate authority
- do not create a second compatibility artifact with a different fingerprint
- extend the existing Final Model Review / Human release / publication path to
  accept the exact authority-backed generated artifact
- retain explicit Human publication approval
- move visible external SYSIDE validation from Model Proposal to Final Model
  Review
- remove internal `Phase-L` terminology from engineer-facing UI

UX finding `WP12-UX-VAL-003`:

External SYSIDE validation belongs to Final Model Review rather than Model
Proposal. Starting Final Model Review may execute SYSIDE for the exact selected
artifact; the resulting evidence is then shown inside Final Model Review before
explicit Human publication approval.
