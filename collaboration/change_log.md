# Change Log

## 2026-07-24 — P4 Semantic Architecture Completion

Versions after this update:

- Architecture Version: 1.0
- Knowledge Base Version: 1.3
- Implementation Version: 0.7
- Roadmap Version: 1.3

Verified implementation baseline:

- Repository: `mz-commits-ai4mbse/SysMLv2-Generator`
- Branch: `main`
- Commit: `0c8ba428e7e6469e410b541c114d7a5a9474321c`
- Complete automated test suite: 2594 passed
- Own-source diff validation: passed
- Pinned external ontology integrity validation: passed
- Remote synchronization: `HEAD == origin/main`

Current Phase P status:

- P1 — Framework Template Definition: Completed
- P2 — Project Manifest and Workspace Structure: Completed
- P3 — Source Registry and mandatory Project Assignment: Completed
- P4 — Framework-mapped heterogeneous Information Units: Completed
- P5 — Processing State and Artifact Organization: Next
- P6–P8: Planned

Completed P2 implementation:

- The Project Workspace architecture was documented in ADR-005.
- Six-digit numeric project identities were implemented.
- Project identity and project display name were separated.
- Project display names must remain unique.
- Project Manifest validation and persistence were implemented.
- Project creation, loading, scanning and safe reopening were implemented.
- Project isolation and symlink protection were implemented.

Completed P3 implementation:

- The textual source-processing boundary was documented in ADR-009.
- The Project Source Registry architecture was documented in ADR-010.
- Every source is assigned to exactly one project.
- Project identity and source identity remain separate.
- Immutable Source Manifests were implemented.
- Source content is hash-bound.
- `engineering_source` and `context_only` roles were implemented.
- Duplicate source content is rejected.
- Safe project-local source persistence and deterministic scans were
  implemented.

Completed P4 implementation:

- The semantic Information Unit and ontology boundary was documented in
  ADR-011.
- Deterministic source projections were implemented.
- Text, Markdown, JSON, CSV, TSV and PDF text-layer adapters were implemented.
- Source-projection locators, manifests and repositories were implemented.
- BFO 2020 and IOF Core 202602 snapshots were pinned and integrity-checked.
- License and provenance information was stored with the ontology snapshots.
- A versioned ontology registry was implemented.
- A deterministic derived index containing 236 reference concepts was
  implemented.
- The Turing Core Vocabulary was implemented.
- Project Glossary candidates and terminology decisions were implemented.
- Immutable, source-traceable Information Units were implemented.
- Semantic extraction candidate contracts were implemented.
- Multi-agent semantic consensus and variance analysis were implemented.
- Terminology-mapping candidates and reference validation were implemented.
- Framework-assignment candidates and reference validation were implemented.
- Immutable Human Review Decisions were implemented.
- Exact target-content and validation-fingerprint publication gates were
  implemented.
- Deterministic token budgeting was implemented.
- Required-context overflow blocks LLM execution.
- Required prompt context cannot be silently truncated.

Accepted textual processing boundary:

- The MVP semantic-processing boundary is textual information.
- Native text and deterministic text projections are supported.
- PDF support is limited to extractable text layers.
- OCR is outside the MVP.
- Image-only PDF interpretation is outside the MVP.
- Technical-drawing interpretation is outside the MVP.
- Unrestricted multimodal engineering extraction is outside the MVP.
- Text projection shall not perform semantic or ontology interpretation.

Accepted semantic authority:

- CATIA remains authoritative for project engineering knowledge.
- Accepted project terminology has authority within its project scope.
- The Turing Core Vocabulary provides the project semantic bridge.
- BFO and IOF remain external reference systems.
- External ontology mappings remain candidates until reviewed.
- External ontologies shall not override project engineering authority.
- Live ontology queries and automatic ontology updates are outside the MVP.
- Complete ontology snapshots shall not be loaded into prompts.

Accepted BFO and IOF role:

- BFO 2020 is the registered top-level ontology reference.
- IOF Core 202602 is the registered industrial ontology reference.
- BFO is stored under `external/ontologies/bfo/2020/`.
- IOF is stored under `external/ontologies/iof/202602/`.
- Reference-system selection, alternatives and justification shall be
  documented with literature and standards in Phase Q.

Accepted project-terminology rules:

- Project terminology is maintained through explicit glossary candidates and
  terminology decisions.
- Project glossary changes require Human Review.
- External reference systems do not automatically mutate project terminology.
- The same normalized term shall not silently represent multiple accepted
  meanings.

Accepted multi-agent and confidence rules:

- Agent personalities may provide independent semantic perspectives.
- Individual agent results remain traceable.
- Consensus, disagreement, run completeness and variance remain explicit.
- Confidence and variance are review evidence.
- High confidence is not publication authority.
- Unanimous consensus is not publication authority.
- Low variance is not publication authority.

Accepted Human Review rules:

- Every publication target requires an explicit Human Review Decision.
- Supported review targets include Information Unit publication, terminology
  mappings and framework assignments.
- Supported decisions are `confirm`, `reject` and `request_changes`.
- Quick confirmation is permitted only for eligible, reference-valid targets.
- Detailed review remains available when quick confirmation is offered.
- Invalid references cannot be confirmed.
- The latest exact decision for the current target-content and validation
  fingerprints controls the gate.
- No automatic publication path exists.

Accepted token-budget rules:

- Prompts use deterministic relevant context slices.
- The complete codebase shall not be loaded automatically.
- Complete ontology snapshots shall not be loaded automatically.
- System instructions, output capacity and safety margin are reserved.
- Required context is included completely or the LLM call is blocked.
- Required context shall never be silently truncated.
- Optional context selection follows an explicit deterministic priority.
- Selected and omitted references remain auditable.

Accepted Phase N roadmap change:

- Phase N now includes Architecture-to-Requirements Reconciliation.
- Every accepted architecture decision shall be mapped to authoritative model
  coverage.
- Missing, outdated and conflicting requirements shall be identified.
- Requirement and model-change candidates shall remain traceable to their
  decision and implementation evidence.
- Stakeholder needs, requirements, design constraints and implementation
  details shall remain distinguishable.
- Implementation is evidence and shall not automatically create normative
  requirements.
- CATIA changes require explicit Human Review.

Accepted Phase Q roadmap change:

- Phase Q — Thesis Architecture Documentation was added after Phase N.
- Phase Q shall document every architecture decision from Phases A–P.
- Phase Q shall also document every later accepted architecture decision.
- Decision context, alternatives, rationale and consequences shall be
  documented.
- Requirement and implementation traceability shall be documented.
- Literature, standards and ontology sources shall support relevant claims.
- BFO and IOF selection and use shall be explained and justified.

Accepted workflow clarifications:

- A complete SSOT UPDATE remains normally scheduled after a major phase.
- This update is an explicitly requested intermediate synchronization after
  P4.
- The intermediate update is justified by the substantial semantic
  architecture baseline and need for a reliable fresh-chat handover.
- The next regular SSOT UPDATE remains due after P8 and completion of Phase P.
- Consecutive work steps modifying the same file should be grouped when they
  can be safely implemented and reviewed together.
- Independently testable intermediate contracts remain permitted.

Next implementation step:

- Begin P5 architecture discussion.
- Define canonical processing states and allowed transitions.
- Define project-level state aggregation.
- Define artifact organization without duplicating existing manifest
  authority.
- Define failure, retry, supersession and reopening behavior.
- Preserve project, source, projection, Information Unit and review
  traceability.
- Do not pull Phase G Approved Input Promotion into P5.
- Do not begin P5 implementation before the architecture is explicitly
  accepted.

---

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
- The deterministic engineering review report and the Agentic Ingestion UI
  were completed and verified.
- Phase P is the active roadmap phase; its scope is defined and implementation
  has not started.
- Every ingested file must be assigned to a project.
- One source may yield multiple heterogeneous, traceable information units.
- The project dashboard will show project metadata, source inventory,
  framework coverage and preliminary model support.
- Framework coverage and preliminary support may include unreviewed engineering
  information only when clearly marked as preliminary.
- Generation readiness and later model generation may use only human-approved
  engineering information.
- Project-wide and selected SubModel generation controls may be displayed
  disabled in Phase P; execution remains assigned to Phases H–J.
- Context-only project documents may explain system context but shall not
  satisfy coverage, readiness or generation evidence.
- The initial framework contains Stakeholder, System and Subsystem levels.
  Additional framework templates are post-MVP scope.

Next implementation step:

- P1 — Framework Template Definition

Deferred architecture decision:

- The concrete Project Workspace persistence layout will be decided during
  P1/P2 and recorded in ADR-005 before implementation depends on it.