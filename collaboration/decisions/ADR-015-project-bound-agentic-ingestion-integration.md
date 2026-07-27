# ADR-015

Project-bound Agentic Ingestion Integration Architecture

Status

Accepted

Date

2026-07-27

## Context

Phase F implemented a working Team Agentic Ingestion pipeline and a standalone
execution-oriented Streamlit interface.

Phase P introduced the project-oriented engineering workspace:

- P1 implemented the versioned Turing RFLP Framework Template.
- P2 implemented persistent Project Workspaces and six-digit Project IDs.
- P3 implemented immutable registered Sources with mandatory Project assignment
  and explicit Source roles.
- P4 implemented project-local source projections, Information Units, semantic
  candidates, terminology mappings, Framework Assignment Candidates and Human
  Review Decisions.
- P5 implemented immutable Processing Runs, Processing Events, Processing
  Decisions, artifact lifecycle, retry, supersession, recovery diagnostics and
  project-level Processing aggregation.
- P6 implemented deterministic Preliminary Coverage and potential model-support
  assessment.
- P7 implemented the read-only Project Dashboard with evidence navigation and a
  constrained Project Workspace creation action.
- P8 verified the P1-P7 implementation baseline and confirmed that the existing
  public contracts can support a project-bound ingestion integration without a
  parallel project or processing architecture.

The existing Phase F ingestion pipeline currently operates with repository-global
execution paths and is not bound to a selected Project Workspace, registered
Source or P5 Processing Run.

A navigation link between the Project Dashboard and the existing ingestion UI
would not be sufficient. A real integration must bind the uploaded Source,
Processing Run, Attempts, generated reports and agent outputs to the selected
Project Workspace and make their current state visible through the existing P5
and P7 authorities.

The integration must preserve the following accepted boundaries:

- Project identity is owned by P2.
- Source registration and Source integrity are owned by P3.
- Processing identity, lifecycle, artifact references, retry, supersession and
  recovery are owned by P5.
- Preliminary Coverage and potential model support are owned by P6.
- Project presentation is owned by P7.
- Phase F remains the execution engine for Team Agentic Ingestion.
- CATIA remains the authoritative engineering model.
- A completed ingestion execution does not imply approved engineering knowledge,
  Preliminary Coverage, Approved Generation Readiness or model generation.

## Decision

### 1. Introduce a dedicated project-bound ingestion integration layer

P9 shall introduce a narrow orchestration and publication layer:

```text
modules/project_ingestion/
├── __init__.py
├── errors.py
├── types.py
├── configuration.py
├── publisher.py
└── service.py
```

The central public contract shall be exposed by:

```python
ProjectBoundIngestionService
```

Its primary execution operation shall conceptually provide:

```python
ProjectBoundIngestionService.execute(
    project_id,
    source_path,
    source_role,
    ingestion_configuration,
) -> ProjectBoundIngestionResult
```

The exact Python signature may be refined during implementation, but it shall
preserve the following responsibilities:

1. require one valid selected Project ID;
2. register the uploaded Source through P3;
3. use the registered project-local Source content as execution input;
4. create one P5 Processing Run;
5. create one Processing Attempt for project-bound agentic ingestion;
6. execute the existing Phase F Team Agentic Ingestion pipeline;
7. validate and fingerprint the complete publishable output set;
8. publish artifacts into the P5 run-owned artifact structure;
9. append immutable P5 Processing Events;
10. return a project-bound result containing stable identities and evidence
    references.

The integration layer shall not replace, fork or duplicate the P2, P3, P5, P6 or
P7 authorities.

### 2. Add a common Turing Generator application shell

P9 shall introduce:

```text
app/turing_generator_app.py
```

The application shell shall provide at least:

```text
Project Dashboard
Agentic Ingestion
```

The Project Dashboard remains the P7 read-only inspection interface.

The Agentic Ingestion view is the P9 execution interface.

Navigation shall carry stable application identities and state only:

```text
project_id
return_view
optional selected entity identity
```

Navigation shall not carry unrestricted filesystem paths.

The selected six-digit Project ID is mandatory for P9 execution. The application
shall fail closed when no valid project binding exists. It shall not silently use
a global, unassigned or different project.

### 3. Preserve the existing Phase F pipeline as the execution engine

The existing Team Agentic Ingestion implementation shall remain the execution
engine.

P9 may add a backward-compatible output-root or execution-root option to the
pipeline.

The default behavior shall remain unchanged:

```text
no project-bound execution root supplied
→ existing Phase F global demo behavior
```

Project-bound behavior shall be explicit:

```text
project-bound execution root supplied
→ execution occurs inside the selected P5 Processing Run work directory
```

Existing Phase F tests and the standalone Phase F demo shall remain operational.

The project-bound integration shall invoke the pipeline with the validated
project-local Source content path returned by P3. The original temporary upload
path shall not remain the authoritative execution input after registration.

### 4. Source registration boundary

The Source shall be registered through:

```python
ProjectSourceRegistry.register_source(...)
```

The registration result shall provide the authoritative:

```text
project_id
source_id
source_role
source_sha256
stored filename
registered content path
```

Source registration is durable and precedes Processing Run creation.

If Source registration succeeds but Processing Run creation does not, the Source
remains a valid registered Source and is presented as not started.

Duplicate Source content within the same project shall continue to be rejected by
the P3 duplicate-content contract.

P9 shall not bypass Source integrity, Source role validation or project-local
storage.

### 5. Processing Run contract

P9 shall create Processing Runs through the existing P5 public contracts.

A new run shall bind at least:

```text
project_id
processing_run_id
source_id
source_sha256
source_role_snapshot
workflow_profile
configuration_fingerprint
framework_template_id
framework_template_version
semantic_reference_versions
created_at
optional supersedes_run_id
```

The Processing Run Manifest shall remain immutable.

The configuration fingerprint shall cover all material execution settings that
affect reproducibility, including at least:

```text
recipe ID
provider
model
dry-run mode
team-member limit
runs per member
relevant pipeline configuration version
```

Secrets such as API keys shall never be persisted or included in fingerprints,
reports, events or result objects.

### 6. Add the agentic ingestion Processing Stage

P5 currently models the downstream engineering-processing stages.

P9 shall add:

```text
agentic_ingestion
```

to the canonical Processing Stage vocabulary.

This stage represents the existing Phase F team-based analysis and review-report
generation.

It shall not be mislabeled as:

```text
source_projection
semantic_extraction
semantic_consensus
terminology_mapping
framework_assignment
human_review
publication
```

A successful P9 execution shall initially end with:

```text
run_state:
awaiting_review

processing_stage:
agentic_ingestion
```

### 7. Extend run-owned artifact kinds

P5 currently supports run-owned Agent Outputs and Consensus Reports.

P9 shall extend the canonical run-owned artifact kinds to include:

```text
agent_outputs
consensus_reports
review_reports
run_summaries
```

The canonical structure shall be:

```text
data/projects/<project_id>/runs/<processing_run_id>/
├── run_manifest.json
├── events/
├── artifacts/
│   ├── agent_outputs/
│   │   └── agentic_ingestion/<attempt_id>/
│   ├── consensus_reports/
│   │   └── agentic_ingestion/<attempt_id>/
│   ├── review_reports/
│   │   └── agentic_ingestion/<attempt_id>/
│   └── run_summaries/
│       └── agentic_ingestion/<attempt_id>/
└── work/
```

The work directory is temporary and non-authoritative.

Published artifacts are immutable and shall be referenced by exact P5
`ProcessingArtifactReference` values containing:

```text
artifact_type
artifact_id
content_fingerprint
repository_relative_path
```

The artifact type shall reflect the actual artifact semantics. Review reports and
run summaries shall not be mislabeled as consensus reports or agent outputs.

### 8. Processing Event sequence

A normal first execution shall produce the following conceptual event sequence:

```text
EVT-000001
event_type: run_created
previous_state: null
next_state: created

EVT-000002
event_type: stage_started
previous_state: created
next_state: running
processing_stage: agentic_ingestion
attempt_id: ATT-000001

EVT-000003
event_type: artifact_published
previous_state: running
next_state: running
processing_stage: agentic_ingestion
attempt_id: ATT-000001
artifact_references:
  - Agent Outputs
  - Consensus Reports
  - Review Report
  - Run Summaries

EVT-000004
event_type: review_requested
previous_state: running
next_state: awaiting_review
processing_stage: agentic_ingestion
attempt_id: ATT-000001
```

Event IDs, sequences, fingerprints and previous-event fingerprints remain owned
by P5.

P9 shall not persist mutable current-state files. Current state shall continue to
be derived from the immutable Event History.

### 9. Output validation and publication transaction

Pipeline output generation and authoritative artifact publication are separate
steps.

The Phase F pipeline shall initially write into the run-owned temporary work
directory.

Before publication, P9 shall validate the complete required output set.

Validation shall include at least:

```text
all required files exist
all required files are regular files
no symbolic-link output is accepted
all output paths remain within the run work directory
all output files are readable
all published contents receive SHA-256 fingerprints
artifact identifiers are deterministic and valid
repository-relative target paths are safe
```

No `artifact_published` event shall be appended before the complete required
output set has been validated and copied into its final immutable artifact
directories.

If output generation is incomplete or validation fails:

```text
no generated output is treated as published evidence
```

Temporary work content may remain available for explicit recovery diagnostics,
but it shall not be interpreted by P5, P6 or P7 as active published evidence.

### 10. Failure and recovery behavior

The workflow cannot be one filesystem-atomic transaction because Source
registration, Processing Run persistence, external LLM execution and artifact
publication are separate durable operations.

The following behavior is required.

#### Source registered, Run not created

```text
Source remains registered
Source Processing State remains not_started
No Processing Run is inferred
```

#### Run created, ingestion execution fails

P9 shall append:

```text
event_type: run_failed
next_state: failed
reason_code: team_agentic_ingestion_failed
```

No unvalidated output shall be published.

#### Output validation fails

P9 shall append a failed or blocked transition with a stable reason code.

No `artifact_published` event shall be written.

#### Artifact files published, publication event fails

This is a recovery-requiring partial transaction.

P9 shall raise or persist a recovery-required condition. It shall not report
success.

The next scan shall expose the inconsistency as a blocking issue until recovery is
completed.

#### Publication event succeeds, review-request event fails

The artifacts remain published and traceable.

The run shall not be reported as successfully awaiting review.

A recovery path shall append the missing valid transition or explicitly fail the
run according to the accepted P5 transition rules.

#### Unexpected exception

Internal exception details shall not be exposed as authoritative user-facing
state.

The integration result and UI shall report a safe failure summary while retaining
technical diagnostics in appropriate developer logs or recovery evidence.

### 11. Retry and successor rules

An unchanged material run binding shall use a retry within the same Processing
Run.

A retry shall create a new attempt:

```text
ATT-000002
ATT-000003
...
```

and shall use the existing P5 retry operation.

Material changes require a successor Processing Run.

Material bindings include:

```text
source_id
source_sha256
source_role_snapshot
workflow_profile
configuration_fingerprint
framework_template_id
framework_template_version
semantic_reference_versions
```

Examples:

```text
same Source and same configuration
→ retry in existing Run

changed model, recipe, team scope or runs per member
→ successor Run

changed Source role
→ successor Run

changed Source content
→ newly registered Source and new Run

changed Framework Template or semantic-reference version
→ successor Run
```

P9 shall not create multiple concurrent current Runs for the same Source without
an explicit valid supersession relationship.

### 12. Human Review boundary

A successful P9 execution requests review but does not itself create an approved
engineering decision.

The P9 result remains:

```text
unreviewed
awaiting_review
```

P9 shall not automatically create:

```text
Approved Input
approved Human Review Decisions
approved terminology mappings
approved Framework Assignments
Approved Generation Readiness
model candidates
SysML v2
CATIA changes
```

Existing and later Human Review contracts remain authoritative.

### 13. Coverage boundary

P9 Processing visibility and P6 Preliminary Coverage are separate.

A successful project-bound ingestion run does not create Preliminary Coverage
unless valid P4 artifacts required by P6 actually exist, including the required
Information Units, Framework Assignment Candidates, reference validations and
Human Review Decisions.

The Project Dashboard may therefore legitimately show:

```text
Processing State:
awaiting_review

Preliminary Coverage:
uncovered

Potential Model Support:
not_supported
```

This is not an inconsistency.

### 14. Dashboard return and refresh

After returning from Agentic Ingestion, the application shall discard stale P7
presentation state for the affected project.

The dashboard shall regenerate its view from the P2-P6 authorities.

The P9 result object shall not become presentation truth.

The application may preserve stable navigation state such as:

```text
selected project
return view
selected Source or Processing Run identity
```

It shall clear open Evidence References that belong to a different project.

### 15. Project isolation and path safety

Every P9 operation shall be explicitly project-bound.

The integration shall reject:

```text
invalid Project IDs
unavailable Project Workspaces
cross-project Source references
cross-project Processing Run references
absolute published paths
parent traversal
symbolic-link escapes
repository escapes
artifact paths outside the selected project and run
```

No P9 operation may silently fall back to repository-global Phase F folders when
project-bound execution was requested.

### 16. Result contract

The project-bound result shall be immutable and contain stable identities and
safe evidence references.

It shall include at least:

```text
project_id
source_id
processing_run_id
attempt_id
run_state
processing_stage
dry_run
published artifact references
safe failure or recovery status
```

It shall not contain:

```text
API keys
unrestricted filesystem paths
mutable Streamlit objects
raw exception objects as persisted state
```

### 17. UI behavior

The P9 execution interface shall make the active Project visible.

The intended demonstrator flow is:

```text
Create or select Project
→ open Agentic Ingestion
→ upload legacy Source
→ select Source role
→ configure execution
→ register Source
→ start Processing Run
→ execute Team Agentic Ingestion
→ inspect execution result
→ return to Project Dashboard
→ inspect Source, Run, state and published evidence
```

Real LLM execution shall continue to require explicit human confirmation.

Dry-run mode shall remain available and shall be visibly distinguished from an
engineering assessment.

### 18. No Project Lifecycle Management in P9

P9 shall not add:

```text
Project display-name editing
Project description editing
Project deletion
Project archival
project-wide destructive lifecycle operations
```

These capabilities require a separate Project Lifecycle Management decision and
are not required for the P9 demonstrator.

## Implementation Sequence

P9 shall proceed in six steps:

```text
P9 Step 1 of 6
Integration Architecture and ADR-015

P9 Step 2 of 6
Common Turing Generator Navigation

P9 Step 3 of 6
Project-bound Source Upload and Source Registration

P9 Step 4 of 6
Bridge between Phase F Ingestion and P5 Processing Runs

P9 Step 5 of 6
Project-bound Artifacts, Dashboard Return and Refresh

P9 Step 6 of 6
End-to-End Demonstration, Full Regression and Phase-P Completion Review
```

Implementation shall not proceed by creating a second Project Manifest, Source
Registry, Processing State model or dashboard authority.

## Consequences

### Positive consequences

- The existing Phase F capability becomes demonstrable inside a real Project
  Workspace.
- P2-P7 remain authoritative.
- The integration is narrow and testable.
- Source, Run, Attempt and artifact identities become fully traceable.
- Existing Phase F behavior remains backward compatible.
- Failures remain visible rather than being converted into false success.
- The Project Dashboard can inspect project-bound ingestion evidence without
  becoming writable.
- Processing visibility remains semantically separate from engineering approval
  and model readiness.
- Retry and supersession use the existing P5 lifecycle.
- The implementation can later be extended toward P4 artifact production without
  replacing the P9 project-binding layer.

### Negative consequences

- The integration spans several durable operations and cannot be completely
  filesystem-atomic.
- Explicit recovery handling is required for partial publication failures.
- P5 Processing Stage and artifact-kind vocabularies must be extended.
- The Phase F pipeline requires a backward-compatible execution-root adaptation.
- A common application shell adds navigation and session-state complexity.
- The first P9 demonstrator may show successful ingestion while Preliminary
  Coverage remains uncovered.
- Project metadata editing and deletion remain unavailable.

## Rejected Alternatives

### Add only a link between the two existing Streamlit apps

Rejected because navigation alone would not bind Sources, Processing Runs,
Attempts or generated artifacts to the selected Project Workspace.

### Move all P5 Processing logic into the Streamlit UI

Rejected because UI code must not become the owner of Processing lifecycle,
persistence or recovery rules.

### Write project-bound artifacts directly into global Phase F folders

Rejected because global folders cannot provide project isolation or authoritative
P5 artifact ownership.

### Treat Phase F run directories as P5 Processing Runs

Rejected because Phase F run identity and P5 Processing Run identity have
different contracts and lifecycle semantics.

### Copy outputs directly into final artifact directories during pipeline execution

Rejected because partially generated output could appear as published evidence
before the complete output set has been validated.

### Mark a successful ingestion run as completed

Rejected because the generated reports and agent outputs remain unreviewed. The
correct initial terminal state is `awaiting_review`.

### Treat successful ingestion as Preliminary Coverage

Rejected because P6 requires specific valid P4 evidence and Human Review
contracts.

### Start a new Run for every technical retry

Rejected because unchanged material bindings are handled by P5 Attempts within
the same Run.

### Reuse the same Run after material configuration changes

Rejected because the immutable Run Manifest must preserve reproducibility.
Material changes require a successor Run.

### Store API keys in the Run Manifest or configuration fingerprint

Rejected because secrets must never be persisted as project evidence.

### Implement Project editing and deletion in P9

Rejected because Project Lifecycle Management is separate from project-bound
ingestion integration and destructive deletion requires its own safety,
transaction and audit decision.

## Acceptance Criteria

ADR-015 is satisfied when:

1. a common application shell exposes Project Dashboard and project-bound Agentic
   Ingestion views;
2. every P9 execution requires one valid selected six-digit Project ID;
3. uploaded content is registered through P3 before processing;
4. the registered project-local Source content is the authoritative pipeline
   input;
5. one P5 Processing Run is created with immutable material bindings;
6. `agentic_ingestion` is a canonical Processing Stage;
7. Agent Outputs, Consensus Reports, Review Reports and Run Summaries have
   distinct run-owned artifact kinds;
8. the Phase F pipeline remains backward compatible when no project execution
   root is supplied;
9. project-bound execution uses the selected Run work directory;
10. a complete first execution produces created, running, artifact-published and
    review-requested lifecycle evidence;
11. a successful execution ends in `awaiting_review`;
12. failed execution produces a visible P5 failure state;
13. incomplete or invalid output is never published;
14. every published artifact has an exact fingerprinted
    `ProcessingArtifactReference`;
15. partial publication failures produce explicit recovery behavior rather than
    false success;
16. unchanged material bindings use a retry Attempt in the same Run;
17. material binding changes use a valid successor Run;
18. P9 does not create Approved Input, Approved Generation Readiness, model
    candidates or SysML v2;
19. P9 execution does not imply Preliminary Coverage;
20. returning to the dashboard regenerates P7 views from P2-P6 authorities;
21. cross-project references and unsafe paths are rejected;
22. API keys and unrestricted filesystem paths are not persisted;
23. core integration behavior is testable without Streamlit;
24. the existing Phase F regression remains green;
25. the complete repository regression remains green;
26. an end-to-end dry-run demonstrator can execute the intended project-bound
    flow;
27. Project metadata editing and Project deletion remain outside P9.
