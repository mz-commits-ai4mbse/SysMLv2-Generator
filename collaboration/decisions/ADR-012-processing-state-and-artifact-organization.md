# ADR-012

Processing State and Artifact Organization

Status

Accepted

Date

2026-07-25

Context

Phase P introduces project-oriented processing around the completed Phase F
agentic ingestion pipeline.

P1 implemented the versioned Turing RFLP Framework.

P2 implemented the persistent Project Workspace.

P3 implemented mandatory project assignment, immutable registered sources and
explicit source roles.

P4 implemented deterministic Source Projections, source-traceable Information
Units, semantic consensus, terminology mappings, Framework Assignments and
Human Review Decisions.

The P1 through P4 repositories persist their individual artifacts
independently. They do not yet provide:

- project-local Processing Run identity
- a canonical operational processing state
- an auditable state-transition history
- project-local organization of agent outputs and Consensus Reports
- retry, resumption and recovery behavior
- supersession and invalidation behavior
- source-level and project-level processing aggregation

P5 shall introduce these capabilities without replacing or duplicating the
authority of existing Project, Source or Semantic Manifests.

P5 shall not perform Approved Input Promotion, model-candidate generation,
internal model generation or SysML v2 generation.

Decision

## Source-bound Processing Runs

A Source Processing Run processes exactly one primary registered source within
exactly one project.

A Processing Run is not equivalent to one LLM invocation.

One Processing Run may contain:

- multiple processing stages
- multiple agent executions
- multiple persona runs
- multiple LLM invocations
- deterministic consensus calculations
- Human Review waits
- technical retries

Every Information Unit remains traceable to exactly one registered engineering
source.

P5 shall not synthesize one Information Unit from multiple sources.

Equivalent, overlapping or contradictory statements from different sources
remain separate, source-traceable Information Units.

Project-level comparison may later reference the results of multiple Source
Processing Runs while preserving every individual source reference.

P5 provides the operational and traceability foundation for that comparison.

Project-wide coverage, overlap and conflict analysis belongs to P6.

The human decision concerning which reviewed information becomes Approved Input
belongs to Phase G.

## Source Processing Disposition

P5 introduces explicit project-local Processing Decisions for operational
source treatment.

Supported Source Processing Dispositions are:

```text
in_scope
context_only
out_of_scope
```

`in_scope` identifies a source that remains eligible for processing according
to its registered source role.

`context_only` restricts a source to contextual and terminology use.

An effectively context-only source shall not create:

- engineering Information Units
- Framework Assignments
- preliminary engineering coverage
- approved readiness
- model-generation input

`out_of_scope` identifies a registered source that does not belong to the
currently processed system or project scope.

Out-of-scope sources remain registered and auditable. They are not deleted or
silently ignored.

A Processing Decision is an operational Human-in-the-Loop decision.

It is not:

- Engineering Approval
- Approved Input Promotion
- a framework assignment
- a terminology acceptance decision
- model-generation authority

The existing P3 Source Manifest remains authoritative for the registered source
and its stored source role.

A Processing Decision does not silently rewrite the Source Manifest.

## Processing Run Identity

Every Processing Run receives an immutable project-local identifier named
`processing_run_id`.

The identifier:

- matches `^RUN-[0-9]{6}$`
- is unique within one project
- is allocated sequentially
- is not reused
- remains unchanged for the lifetime of the run

The globally unambiguous reference is:

```text
<project_id>/<processing_run_id>
```

Example:

```text
318604/RUN-000001
```

## Run Manifest

Every Processing Run contains an immutable `run_manifest.json`.

The Run Manifest binds the run to at least:

```text
schema_version
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
supersedes_run_id
```

`supersedes_run_id` is absent when the run has no predecessor.

The Run Manifest contains identity, scope and reproducibility bindings.

It does not contain a mutable current-state field.

## Workflow Profiles

The required stages of one Processing Run are determined by an explicit,
versioned workflow profile.

An engineering-source workflow may include:

```text
source_projection
semantic_extraction
semantic_consensus
terminology_mapping
framework_assignment
human_review
publication
```

A context-only workflow may omit engineering Information Unit extraction and
Framework Assignment.

A run shall not be considered incomplete merely because a stage that is
ineligible for its workflow profile was not executed.

## Event History

The authoritative operational state of a Processing Run is represented by an
immutable Event History.

Every state transition creates a new event.

Existing events shall not be overwritten, reordered or deleted.

Event identifiers:

- match `^EVT-[0-9]{6}$`
- are unique within one Processing Run
- are allocated sequentially
- are not reused

An event records at least:

```text
schema_version
project_id
processing_run_id
event_id
event_sequence
previous_state
next_state
processing_stage
event_type
attempt_id
reason_code
artifact_references
occurred_at
previous_event_fingerprint
event_fingerprint
```

The fingerprint chain makes missing, reordered or modified events detectable.

An artifact reference contains only the information required to identify and
validate the referenced artifact, including:

```text
artifact_type
artifact_id
content_fingerprint
repository_relative_path
```

The event does not duplicate the professional content of the referenced
artifact.

## Current-state Projection

The current Processing Run state is derived deterministically from the valid
Event History.

The derived current-state view is not an independent authority.

It may be calculated during project loading or exposed through a regenerable
derived index.

A derived index may be deleted and regenerated without loss of authoritative
processing information.

## Run States

The canonical Processing Run states are:

```text
created
running
awaiting_review
blocked
failed
completed
superseded
```

`created` means that the run has been persistently created but processing has
not started.

`running` means that an allowed processing stage is being executed.

`awaiting_review` means that an exact Human Review decision is required before
processing may continue.

`blocked` means that a known deterministic prerequisite is missing or invalid.

Examples include:

- unavailable Source Projection
- required context exceeding the token budget
- invalid mandatory references
- unresolved processing disposition
- incomplete publication recovery
- inconsistent Event History

`failed` means that a technical execution or artifact-validation failure
occurred.

`completed` means that the complete workflow required by the selected workflow
profile has been resolved.

`completed` does not mean:

- Engineering Approval
- Approved Input
- generation readiness
- model acceptance

A completely reviewed rejection may result in a completed run without
publication.

`superseded` means that an explicitly linked successor run replaces the run for
current operational use.

A superseded run remains fully available for traceability.

## Processing Stages

Run state and active Processing Stage are separate dimensions.

Supported P5 stages include:

```text
source_projection
semantic_extraction
semantic_consensus
terminology_mapping
framework_assignment
human_review
publication
```

This separation prevents stage-specific combinations from becoming independent
state values.

## Allowed State Transitions

The allowed core transitions are:

```text
created
→ running
→ blocked
→ failed
→ superseded

running
→ awaiting_review
→ blocked
→ failed
→ completed
→ superseded

awaiting_review
→ running
→ completed
→ blocked
→ superseded

blocked
→ running
→ failed
→ superseded

failed
→ running
→ superseded

completed
→ superseded

superseded
→ no further transition
```

Every transition requires an explicit reason and valid transition evidence.

## Human Review Transitions

Human Review controls operational continuation but does not replace Phase G
Engineering Approval.

The supported behavior is:

```text
confirm
→ continue processing or publication

reject
→ do not publish the rejected target
→ complete the run when all required targets are resolved

request_changes
→ return to the required processing stage
→ create a new attempt when the run bindings remain unchanged
→ create a successor run when the bindings changed
```

Only an exact decision bound to the current target and validation fingerprints
may control the corresponding transition.

Consensus, confidence and variance remain review evidence.

They shall not create an automatic state transition that bypasses Human Review.

## Project-local Artifact Organization

P5 introduces:

```text
data/projects/<project_id>/
├── runs/
│   └── RUN-000001/
│       ├── run_manifest.json
│       ├── events/
│       │   ├── EVT-000001.json
│       │   └── EVT-000002.json
│       ├── artifacts/
│       │   ├── agent_outputs/
│       │   └── consensus_reports/
│       └── work/
└── processing_decisions/
    └── PD-000001.json
```

The directories are created only when required.

## Existing Artifact Authority

Existing P2 through P4 repositories remain authoritative for their own domain
records.

These include:

```text
project_manifest.json
sources/<source_id>/source_manifest.json
sources/<source_id>/content.<suffix>
semantics/source_projections/
semantics/information_units/
semantics/project_glossary.json
semantics/terminology_decisions/
semantics/terminology_mappings/
semantics/framework_assignments/
semantics/human_reviews/
```

P5 shall not:

- move these artifacts into Processing Run directories
- copy them into Processing Run directories as a second maintained record
- rewrite their professional content
- replace their identifiers
- replace their fingerprints
- weaken their individual validation contracts

P5 references these artifacts through stable identifiers and fingerprints.

## Run-owned Artifacts

`artifacts/agent_outputs/` stores immutable technical outputs of individual
agent and persona executions.

`artifacts/consensus_reports/` stores deterministic consensus and variance
evidence.

Run-owned artifacts remain traceable to:

- project
- Processing Run
- primary source
- processing stage
- attempt
- team
- agent
- persona
- provider and model
- prompt and schema version

These technical artifacts are execution evidence.

They are not authoritative engineering information.

## Temporary Work Artifacts

`work/` contains incomplete and non-authoritative processing artifacts.

Temporary work artifacts shall not:

- satisfy run completion
- create preliminary coverage
- pass a publication gate
- be treated as published semantic records

Temporary artifacts may be retained for failure diagnosis.

They shall not be silently promoted.

## Phase F Run Boundary

Existing Phase F artifacts under:

```text
data/team_runs/
```

remain available for existing demonstrations, regression evidence and Phase F
inspection.

They do not become authoritative Project Workspace state.

New project-oriented P5 Processing Runs are stored only below their containing
project.

P5 shall not require destructive migration or deletion of existing Phase F
artifacts.

## Attempt Identity

Every retry attempt receives an immutable attempt identifier matching:

```text
^ATT-[0-9]{6}$
```

Attempts are ordered within their Processing Run and stage.

Attempt artifacts are stored separately.

Example:

```text
artifacts/agent_outputs/
└── semantic_extraction/
    ├── ATT-000001/
    └── ATT-000002/
```

No retry overwrites output from an earlier attempt.

## Retry Behavior

A retry may remain within the same Processing Run only when all material run
bindings remain unchanged.

These bindings include:

```text
source_id
source_sha256
source_role_snapshot
workflow_profile
adapter configuration
prompt and schema versions
framework-template version
semantic reference versions
```

A retry creates:

- a new Attempt
- new technical artifacts
- new state-transition events
- explicit retry rationale

A retry shall not replace or edit earlier attempts.

## Successor Runs

A material change to a run binding requires a new Processing Run.

Examples include:

- changed source content
- changed source identity
- changed effective source role
- changed workflow profile
- changed adapter configuration
- changed prompt or output schema
- changed framework-template version
- changed semantic reference version

The new Run Manifest references its predecessor through
`supersedes_run_id`.

A completed run is never reopened for a material change.

## Supersession

Supersession follows this order:

1. validate the predecessor
2. create and validate the successor Run Manifest
3. persist the successor run
4. append the supersession event to the predecessor
5. validate the complete relationship

An interrupted supersession is detected during project reopening.

It is not silently completed or ignored.

A run marked as superseded remains immutable and available.

## Artifact Lifecycle

P5 may derive the following operational lifecycle states for existing immutable
artifacts:

```text
active
superseded
invalidated
```

Lifecycle state remains separate from artifact content.

Supersession or invalidation:

- does not delete the artifact
- does not alter its content
- does not alter its original Human Review Decision
- does not turn a rejected artifact into an accepted artifact
- does not create Approved Input

A lifecycle event references the exact artifact identity and fingerprint.

## Source-disposition Changes

A Processing Decision that changes the effective treatment of a source requires
dependency analysis.

When a source becomes effectively `context_only` or `out_of_scope`, dependent
engineering runs and their use in later P6 processing are invalidated.

The affected records remain available for traceability.

A source-disposition change shall not silently reinterpret existing artifacts.

## Project Reopening

Project reopening validates at least:

- Project Manifest
- Source Manifests
- Run Manifests
- Event identities and sequences
- event fingerprint chains
- allowed state transitions
- Attempt identities
- artifact references and fingerprints
- Processing Decisions
- supersession relationships
- incomplete publication conditions

A valid history is reconstructed deterministically.

No project state is reconstructed from filenames alone.

## Recovery Behavior

Recovery is explicit and fail-closed.

A consistent history produces the derived current state.

A recoverable interrupted operation produces:

```text
blocked
```

together with an explicit recovery diagnostic.

A technical execution failure produces:

```text
failed
```

An inconsistent, incomplete or manipulated Event History produces:

```text
blocked
```

and shall not be silently repaired.

A published artifact that exists without the expected completion event is
reported as an incomplete publication.

An explicit recovery operation may validate the exact existing artifact and
complete the Event History.

Recovery shall not create a duplicate artifact.

## Source-level Aggregation

For each source, P5 identifies the current non-superseded Processing Run.

The source-processing view includes at least:

```text
processing disposition
current processing run
current run state
current processing stage
latest attempt
blocking issues
failure issues
pending Human Review
superseded runs
invalidated artifacts
```

## Project-level Aggregation

Project Processing State is derived from validated project, source, run, event
and Processing Decision records.

The supported project states are:

```text
empty
not_started
in_progress
awaiting_review
attention_required
partially_processed
processed
```

`empty` means that the project contains no registered sources.

`not_started` means that relevant sources exist but no active processing has
started.

`in_progress` means that one or more active Processing Runs are being executed.

`awaiting_review` means that an active run requires Human Review.

`attention_required` means that one or more relevant sources are blocked,
failed or inconsistent.

`partially_processed` means that some relevant sources are completed while
others remain unprocessed.

`processed` means that all relevant source-processing workflows have reached
resolved terminal outcomes.

Out-of-scope sources remain visible but do not prevent a project from becoming
processed.

## Aggregation Counts

The project aggregation exposes separate counts for at least:

```text
total sources
in-scope sources
context-only sources
out-of-scope sources
not-started sources
running sources
sources awaiting review
blocked sources
failed sources
completed sources
superseded runs
invalidated artifacts
```

A headline Project Processing State shall never hide its underlying counts and
issues.

## Aggregation Authority Boundary

Project Processing State is an operational and dashboard-oriented view.

It is not:

- preliminary coverage
- Approved Input
- approved readiness
- Engineering Approval
- generation readiness
- model-generation authority

P6 calculates Preliminary Coverage from eligible P4 records that P5 identifies
as operationally usable.

Phase G performs Approved Input Promotion using exact Human Review evidence.

## P5 Scope Boundary

P5 includes:

- Source Processing Run identity
- immutable Run Manifests
- immutable Event History
- deterministic current-state derivation
- project-local agent-output organization
- project-local Consensus Report organization
- Processing Decisions
- retry and Attempt organization
- supersession and invalidation
- reopening and explicit recovery behavior
- source-level processing aggregation
- project-level processing aggregation

P5 does not include:

- automatic multi-source Information Unit synthesis
- Approved Input Promotion
- Engineering Approval
- coverage calculation
- model-candidate creation
- internal model generation
- SysML v2 generation
- CATIA updates

Consequences

Positive consequences:

- Every processing transition remains auditable.
- Current state can be reconstructed deterministically.
- Multiple LLM and persona executions remain grouped within one source-bound
  workflow.
- Multiple sources remain independently traceable.
- Overlap and contradictions can later be compared without merging source
  authority.
- Existing P2 through P4 repositories remain stable.
- Retry does not destroy earlier execution evidence.
- Material changes produce explicit successor runs.
- Failed and interrupted processing can be diagnosed safely.
- Out-of-scope sources remain visible without blocking project progress.
- Project processing state can support the future dashboard.
- Processing completion remains separate from Engineering Approval.

Trade-offs:

- Event persistence introduces additional artifacts.
- Current-state reconstruction requires deterministic event validation.
- Retry and supersession require strict fingerprint comparison.
- Run-owned technical artifacts increase project storage.
- Recovery requires explicit operator action.
- Project aggregation must preserve detailed counts and issues.
- Source-disposition changes require dependency analysis.

Alternatives Considered

Treating one Processing Run as one LLM invocation was rejected because one
source workflow requires multiple stages, personas and deterministic analyses.

Creating multi-source Information Units was rejected because it would weaken
source traceability and make contradictory evidence difficult to review.

Storing only a mutable current-state file was rejected because it would destroy
transition, retry and recovery history.

Using only an Event History without a derived current-state view was rejected
because project reopening and the future dashboard require efficient state
access.

Copying existing semantic artifacts into Run directories was rejected because
it would duplicate authority and create synchronization risk.

Moving existing P4 artifacts into Run directories was rejected because it would
break established repositories and public contracts.

Using `data/team_runs/` as Project Workspace authority was rejected because
those artifacts are not project-isolated.

Overwriting earlier Agent Outputs during retry was rejected because it would
destroy reproducibility evidence.

Reopening a completed run for material changes was rejected because it would
make previous review and publication evidence ambiguous.

Automatically repairing invalid Event Histories was rejected because recovery
must remain explicit and auditable.

Using Project Processing State as approval or generation authority was rejected
because operational completion and Engineering Approval are separate concerns.

Affected Components

- future P5 processing-state modules
- `data/projects/<project_id>/runs/`
- `data/projects/<project_id>/processing_decisions/`
- existing P2 through P4 repositories as referenced dependencies
- future P6 coverage processing
- future P7 Project Dashboard
- P5 automated tests and phase review

Implementation Constraints

P5 implementation shall:

- preserve P2 project isolation
- preserve P3 source identity and source immutability
- preserve P4 artifact immutability
- reject cross-project run and artifact references
- reject invalid identifiers
- reject invalid state transitions
- reject broken event sequences
- reject invalid fingerprint chains
- reject silent artifact overwrite
- preserve earlier attempts
- preserve superseded and invalidated artifacts
- separate processing completion from Engineering Approval
- remain compatible with existing Phase F behavior
- avoid destructive migration of existing Phase F artifacts

Verification Criteria

P5 is not complete until automated tests demonstrate at least:

- project-local Processing Run identifier allocation
- strict Run Manifest validation
- exactly one primary source per Source Processing Run
- multiple Agent and LLM executions within one run
- workflow-profile validation
- immutable Event persistence
- deterministic event ordering
- event fingerprint-chain validation
- rejection of invalid state transitions
- deterministic current-state reconstruction
- Processing Decision validation
- source-disposition behavior
- separate Attempt persistence
- retry with unchanged bindings
- rejection of same-run retry with changed bindings
- successor-run creation for changed bindings
- supersession validation
- artifact invalidation without deletion
- recovery from incomplete publication
- blocking of inconsistent Event Histories
- source-level aggregation
- project-level aggregation
- out-of-scope exclusion from project-progress blocking
- separation of Project Processing State and approval
- preservation of P1 through P4 tests
- complete project test-suite compatibility

Supersedes

None

Related Roadmap Phase

P5 — Processing State and Artifact Organization

Related Decisions

- ADR-005 — Project Workspace Architecture
- ADR-009 — Textual Source Processing Boundary
- ADR-010 — Project Source Registry Architecture
- ADR-011 — Semantic Information Unit and Ontology Boundary

Related Implementation

Not yet implemented.

Implementation shall begin only after this accepted ADR has been committed and
pushed by the project owner.