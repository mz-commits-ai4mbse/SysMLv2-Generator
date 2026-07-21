# Change Log

## 2026-07-21 — Phase F Completion and Phase P Scope Definition

Versions after this update:

- Architecture Version: 0.9
- Knowledge Base Version: 1.1
- Implementation Version: 0.5
- Roadmap Version: 1.1

Verified implementation baseline:

- Repository: `mz-commits-ai4mbse/SysMLv2-Generator`
- Branch: `main`
- Commit: `adce9ec65ca3e36b89686b55d397a34dd382fdb1`
- Test result: 9 passed

Accepted changes:

- Phase F is complete.
- The deterministic engineering review report and the Agentic Ingestion UI were completed and verified.
- Phase P is the active roadmap phase; its scope is defined and implementation has not started.
- Every ingested file must be assigned to a project.
- One source may yield multiple heterogeneous, traceable information units.
- The project dashboard will show project metadata, source inventory, framework coverage and preliminary model support.
- Framework coverage and preliminary support may include unreviewed engineering information only when clearly marked as preliminary.
- Generation readiness and later model generation may use only human-approved engineering information.
- Project-wide and selected SubModel generation controls may be displayed disabled in Phase P; execution remains assigned to Phases H–J.
- Context-only project documents may explain system context but shall not satisfy coverage, readiness or generation evidence.
- The initial framework contains Stakeholder, System and Subsystem levels. Additional framework templates are post-MVP scope.

Next implementation step:

- P1 — Framework Template Definition

Deferred architecture decision:

- The concrete Project Workspace persistence layout will be decided during P1/P2 and recorded in ADR-005 before implementation depends on it.
