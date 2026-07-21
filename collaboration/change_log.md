# Change Log

## 2026-07-21 — P1 Framework Template Completion

Versions after this update:

- Architecture Version: 0.9
- Knowledge Base Version: 1.2
- Implementation Version: 0.6
- Roadmap Version: 1.2

Verified implementation baseline:

- Repository: `mz-commits-ai4mbse/SysMLv2-Generator`
- Branch: `main`
- Commit: `82b5cbbe9bedac77a4b02928a596ea8fbdacc873`
- P1 framework tests: 9 passed
- Complete automated test suite: 18 passed
- Diff validation: passed

Completed implementation:

- P1 — Framework Template Definition is complete.
- The Apollo 11 SysML v2 repository was reviewed for transferable
  structuring, naming and hierarchy patterns.
- Accepted and rejected Apollo 11 patterns are documented in
  `context/examples/apollo11_structure_reference.md`.
- The versioned framework template
  `context/frameworks/turing_rflp_framework.json` was implemented.
- The template contains 3 framework levels and 12 explicit mapping targets.
- Stable framework node identifiers and mapping keys were defined.
- Zero-to-many framework assignment is supported.
- Unknown framework targets are rejected.
- `context_only` sources are excluded from framework mapping.
- Preliminary coverage and approved generation readiness are represented as
  separate concepts.
- Approved readiness remains unavailable during Phase P.
- A deterministic framework-template validator was implemented in
  `modules/framework/template.py`.
- Framework-template documentation and automated tests were added.

Accepted reference decisions:

- Apollo 11 remains a non-normative structural reference.
- The Apollo CoSMA framework was not adopted.
- The Apollo package hierarchy was not adopted.
- Apollo engineering content and identifiers were not transferred.
- The accepted Stakeholder/System/Subsystem framework remains unchanged.
- Only explicitly reviewed structural patterns may influence the Turing
  framework.

Accepted repository collaboration workflow:

- GitHub repositories and repository links are used passively by AI
  assistants.
- AI assistants shall not directly modify GitHub repository content.
- AI assistants shall not commit, push, create remote branches or open pull
  requests.
- Repository changes are applied, reviewed, tested, staged, committed and
  pushed locally by the project owner.
- AI assistants act as implementation guides and identify affected files by
  repository-relative path before proposing changes.
- Changes are normally presented one file at a time.
- Mixed working trees require explicit file-by-file staging.

Accepted SSOT update cadence:

- A complete SSOT UPDATE is normally performed after completion of a major
  roadmap phase.
- Internal work steps within a phase do not require separate full SSOT updates.
- P1 through P8 are tracked through committed implementation changes, automated
  test evidence and reviewed decisions.
- Accepted architecture decisions are documented and committed individually as
  ADRs before implementation depends on them.
- Committing an accepted ADR does not trigger a complete SSOT UPDATE.
- The current synchronization is an explicitly requested P1 alignment update.
- The next regular full SSOT UPDATE shall be performed after P8 and completion
  of Phase P.
- An earlier SSOT UPDATE requires an explicit project-owner request or a
  critical handover need.

Current Phase P status:

- P1 — Framework Template Definition: Completed
- P2 — Project Manifest and Workspace Structure: Next
- P3–P8: Planned

Next implementation step:

- Begin the P2 architecture discussion.
- Define project identity, Project Manifest, Workspace structure, persistence,
  reopening and project-isolation boundaries.
- Record the explicitly accepted architecture in ADR-005 before P2
  implementation begins.

Deferred architecture decision:

- The concrete Project Workspace persistence layout remains unaccepted.
- Architecture Version remains 0.9 until ADR-005 has been discussed and
  explicitly accepted.

---

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
