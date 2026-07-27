# Current Chat Handover

## Purpose

This document is the authoritative starting point for the next implementation
chat.

It contains the current accepted project context and intentionally does not
rely on previous chat history.

---

# Project

Project

Turing Generator

Repository

`mz-commits-ai4mbse/SysMLv2-Generator`

Branch

`main`

Verified Implementation Commit

`26acace4d7ba2849b33c5e0dacedf838f83c7705`

Current Phase

G – Approved Input Promotion

Current Status

Phase P Completed — Phase G Next

Architecture Version

1.1

Knowledge Base Version

1.4

Implementation Version

0.8

Roadmap Version

1.4

Last SSOT Update

2026-07-27

Complete Automated Test Baseline

3808 passed

---

# Read Before Starting

Read the Collaboration Knowledge Base in this order:

1. `collaboration/current_state.md`
2. `collaboration/roadmap.md`
3. `collaboration/working_rules.md`
4. `collaboration/model_registry.json`
5. `collaboration/decisions/`
6. `collaboration/change_log.md`

Then inspect the committed implementation relevant to Phase G.

Do not use previous chat history as a source of truth.

Do not begin implementation before presenting the verified baseline summary.

---

# Required Baseline Summary

Before proposing Phase G implementation, summarize:

- current roadmap phase
- completed implementation
- architecture version
- verified implementation commit
- automated test baseline
- next implementation step
- unresolved architecture decisions relevant to Approved Input Promotion

The summary shall be based on the committed repository and Collaboration
Knowledge Base.

---

# Source Authority

1. The CATIA SysML v2 model is authoritative for engineering knowledge.
2. The committed GitHub repository is authoritative for implementation reality.
3. The Collaboration Knowledge Base is authoritative for roadmap, status,
   accepted decisions and working rules.
4. Chat history and generated temporary artifacts are non-authoritative.

If required engineering information is unavailable in CATIA, the temporary
shadow model under `model/` may supplement it until Phase N.

The shadow model shall never override or contradict CATIA.

Implementation is not automatic authority for requirements.

---

# Repository Collaboration Workflow

GitHub repositories and repository links are used passively by AI assistants.

AI assistants shall not:

- directly modify GitHub repository content
- create or update remote branches
- commit or push changes
- open or merge pull requests
- use GitHub write APIs
- stage files in the project owner's working tree
- destructively clean the working tree without explicitly resolved scope

Repository changes are:

1. proposed with exact repository-relative paths
2. applied locally by the project owner in VS Code
3. reviewed and tested locally
4. staged explicitly by path
5. committed and pushed by the project owner
6. verified passively after the push

The AI assistant acts as an implementation guide.

Broad staging commands shall not be used in a mixed working tree.

---

# Verified Completed Baseline

## Phase F — Agentic Ingestion UI

Verified at:

`adce9ec65ca3e36b89686b55d397a34dd382fdb1`

Completed capabilities include:

- team-based agentic ingestion
- memory pipeline
- consensus reports
- deterministic engineering review report
- traceable gaps, risks and questions
- Streamlit ingestion UI
- artifact browser
- Dry Run and LLM execution paths

## Phase P — Project Workspace and Project-bound Ingestion

Phase P is complete.

Final verification commit:

`26acace4d7ba2849b33c5e0dacedf838f83c7705`

Complete automated test baseline:

3808 passed

Completed steps:

| Step | Deliverable | Status |
|---|---|---|
| P1 | Framework Template Definition | Completed |
| P2 | Project Manifest and Workspace Structure | Completed |
| P3 | Source Registry and mandatory Project Assignment | Completed |
| P4 | Framework-mapped heterogeneous Information Units | Completed |
| P5 | Processing State and Artifact Organization | Completed |
| P6 | Preliminary Coverage and Potential Model Support | Completed |
| P7 | Project Dashboard | Completed |
| P8 | Tests and Integration Readiness Review | Completed |
| P9 | Project-bound Agentic Ingestion Integration | Completed |

Important architecture decisions:

- P2: `collaboration/decisions/ADR-005-project-workspace-architecture.md`
- P3: `collaboration/decisions/ADR-009-textual-source-processing-boundary.md`
- P3: `collaboration/decisions/ADR-010-project-source-registry-architecture.md`
- P4: `collaboration/decisions/ADR-011-semantic-information-unit-and-ontology-boundary.md`
- P5: `collaboration/decisions/ADR-012-processing-state-and-artifact-organization.md`
- P6: `collaboration/decisions/ADR-013-preliminary-coverage-and-potential-model-support.md`
- P7: `collaboration/decisions/ADR-014-project-dashboard-architecture.md`
- P9: `collaboration/decisions/ADR-015-project-bound-agentic-ingestion-integration.md`

---

# Accepted Phase P Framework

The implemented framework is:

- Stakeholder Level
  - Stakeholders
  - User Needs
  - Stakeholder Requirements
  - Use Cases
- System Level
  - Requirements
  - Functional
  - Logical
  - Physical
- Subsystem Level
  - Requirements
  - Functional
  - Logical
  - Physical

Additional framework templates remain post-MVP scope.

---

# Accepted Boundaries

## Textual Processing

The MVP processing boundary is textual.

Supported:

- native text
- Markdown
- JSON
- CSV
- TSV
- deterministic textual projections
- PDF text layers

Outside MVP:

- OCR
- image-only PDFs
- technical drawings
- unrestricted multimodal extraction

Text projection shall not perform semantic or ontology interpretation.

## Project and Source Authority

Every Source is assigned to exactly one Project.

Project identity and Source identity remain separate.

Registered Sources are immutable and content hash-bound.

Duplicate Source content within the same Project is rejected.

## Processing Authority

Processing Runs are event-history based.

Current state is reconstructed from immutable Processing Events.

A successful P9 execution ends in:

```text
run_state = awaiting_review
processing_stage = agentic_ingestion
```

This requests review but does not approve engineering knowledge.

## Published Artifact Boundary

P9 publishes immutable run-owned artifacts:

- agent outputs
- consensus reports
- review reports
- run summaries

Published run-owned artifacts are authoritative evidence for what the run
produced. They are not Approved Input.

## Human Review Boundary

Consensus, confidence and variance are review evidence.

They are not publication or promotion authority.

Every engineering publication or promotion target requires an explicit Human
Review Decision.

## Preliminary Coverage Boundary

Phase P Preliminary Coverage may use candidate evidence and must remain
clearly separate from Approved Generation Readiness.

Approved Generation Readiness is unavailable during Phase P and depends on
later approved engineering input.

---

# P9 Manual Acceptance Evidence

Local demo project:

`458990`

Negative case:

- `SRC-000001`
- `RUN-000001`
- state: `failed`
- reason: `source_normalization_failed`
- events: 3
- artifacts: 0

Successful dry-run case:

- `SRC-000002`
- `RUN-000002`
- attempt: `ATT-000001`
- state: `awaiting_review`
- events: 4
- artifacts: 15

Published artifact counts:

- 4 `agent_outputs`
- 8 `consensus_reports`
- 1 `review_reports`
- 2 `run_summaries`

The manual demo data under `data/projects/` is local test evidence and is not a
committed authoritative implementation artifact.

---

# Current Known Limitations

- Phase G Approved Input Promotion is not implemented.
- P9 `awaiting_review` is not Approved Input.
- No model candidates are generated.
- No SysML v2 code is generated.
- CATIA synchronization is not implemented.
- Project editing and project deletion are not implemented.
- Retry and successor handling exist in core P5/P9 boundaries but require
  further operator UI and workflow refinement.
- Full live LLM-team performance and cost measurements remain open.
- OCR and multimodal engineering extraction are outside the MVP.

---

# Next Implementation Step

Begin Phase G architecture discussion.

The first discussion shall resolve:

1. Approved Input identity and storage
2. eligible promotion sources from P4 and P9
3. required Human Review Decision target types
4. fingerprint binding for promoted content
5. promotion, rejection, revocation and supersession behavior
6. relationship between Approved Input and later model candidates
7. how Phase G avoids generating models or SysML v2 prematurely

Do not start Phase G implementation before the architecture has been explicitly
accepted.

---

# Planned Thesis Development Plan

A thesis-only Development Plan shall later document the lettered development
phases used in this project.

It shall remain separate from the feature overview and is not intended for the
intermediate presentation.
