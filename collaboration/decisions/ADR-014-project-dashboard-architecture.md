# ADR-014

Project Dashboard Architecture and Evidence Navigation

Status

Accepted

Date

2026-07-27

Context

Phase P introduces a project-oriented engineering workspace around the completed
Phase F agentic ingestion pipeline.

P1 implemented the versioned Turing RFLP Framework.

P2 implemented persistent Project Workspaces and six-digit project identities.

P3 implemented immutable registered Sources with explicit source roles.

P4 implemented source-traceable Information Units, semantic candidates,
Framework Assignment Candidates and exact Human Review Decisions.

P5 implemented immutable Processing Runs, Event Histories, Processing Decisions,
artifact lifecycle, source disposition and project processing aggregation.

P6 implemented deterministic Preliminary Coverage and potential model-support
assessment.

P7 introduces a read-only Project Dashboard for navigating the current project
state and its supporting evidence.

The existing Team Agentic Ingestion UI remains an execution-oriented interface.
It selects legacy inputs, configures ingestion runs, starts the pipeline and
browses produced artifacts. It is not the project-level dashboard introduced by
P7.

The dashboard must answer the following questions without creating a new source
of truth:

- which project is currently selected
- which Sources are registered and how they are classified
- what the current project and source processing states are
- which framework nodes and levels have Preliminary Coverage
- which model and submodel scopes are potentially supported
- which issues require attention
- which Human Review Decisions affect the displayed state
- which exact artifacts and documents support every displayed result
- how the user can open those supporting artifacts directly from the dashboard

The dashboard shall be visually concise and shall use color only to communicate
status.

Decision

## Dashboard Authority

The Project Dashboard is a derived, read-only presentation layer.

It shall not become an authority for:

- engineering requirements
- CATIA SysML v2 model content
- project identity
- Source registration
- Processing State
- Information Units
- semantic candidates
- Framework Assignment Candidates
- Human Review Decisions
- Preliminary Coverage
- potential model support
- Approved Generation Readiness

The dashboard may be deleted and regenerated without loss of authoritative
engineering, semantic or processing information.

The dashboard shall obtain its information exclusively through the existing
P2-P6 public services, repositories and immutable data types.

The UI shall not reimplement business rules already owned by P2-P6.

## Read-only Scope

P7 shall provide navigation and presentation only.

P7 shall not:

- register or modify Sources
- start, retry, supersede or mutate Processing Runs
- create or modify Information Units
- create or modify semantic candidates
- create or modify Framework Assignment Candidates
- create or modify Human Review Decisions
- promote Approved Inputs
- calculate Approved Generation Readiness
- generate model candidates
- generate SysML v2
- mutate CATIA
- persist mutable dashboard state as project authority

The existing Team Agentic Ingestion UI remains separate and unchanged during P7.

A future navigation link may lead from the dashboard to the ingestion UI, but
the P7 dashboard itself shall remain read-only.

## Dashboard Composition

The initial Project Dashboard contains five primary views:

```text
Project Overview
Preliminary Coverage
Sources and Processing
Attention and Review
Traceability and Documents
```

The selected project remains visible across all views.

### Project Overview

The overview presents a compact project summary:

- Project display name
- six-digit Project ID
- Framework Template identifier and version
- Preliminary Support Profile identifier and version
- registered Source count
- project processing state
- project Preliminary Coverage state
- attention summary
- potential Stakeholder Model support
- potential System Model support
- potential Subsystem Model support
- explicit Approved Generation Readiness unavailability

The overview shall not display a synthetic maturity score.

Exact ratios may be displayed, for example:

```text
3 of 4 System framework nodes preliminarily covered
```

### Preliminary Coverage

The coverage view presents:

- Stakeholder, System and Subsystem framework levels
- all twelve stable framework mapping targets
- node coverage state
- level coverage state
- reviewed and unreviewed candidate counts
- eligible Source and Information Unit counts
- independent attention state
- related issue codes
- direct evidence navigation

Canonical node states remain owned by P6:

```text
uncovered
candidate_covered
reviewed_candidate_covered
```

Canonical level states remain owned by P6:

```text
uncovered
partially_covered
covered
```

Coverage and attention shall remain separate dimensions.

### Sources and Processing

The processing view presents each registered Source with:

- Source ID
- original filename
- source role
- content fingerprint
- effective processing disposition
- current Processing Run ID
- run state
- processing stage
- latest Attempt ID
- pending review state
- blocking issue codes
- failure issue codes
- superseded Run IDs
- invalidated artifact count
- direct Source Manifest and processing-history navigation

The dashboard shall not infer a processing state that is not supplied by P5.

### Attention and Review

The attention view presents:

- blocking and warning issues
- affected project, Source, Information Unit, candidate, node or support target
- Human Review target type
- Human Review decision
- decision identity
- exact target content fingerprint
- exact reference-validation fingerprint
- reviewer identity where available
- direct navigation to affected artifacts and decisions

A Human Review confirmation shown in P7 confirms only the exact reviewed target.

It shall not be presented as:

- Approved Input
- Engineering Approval
- Approved Generation Readiness
- model acceptance
- generation authorization

### Traceability and Documents

The traceability view presents the evidence chain behind dashboard results.

A typical chain is:

```text
Source
→ Processing Run and Events
→ Information Unit
→ Framework Assignment Candidate
→ Reference Validation
→ Human Review Decision
→ Preliminary Coverage
→ Potential Model Support
```

The view shall allow navigation in both directions where exact references exist.

## Smart Evidence Navigation

Every dashboard element that presents a traceable project fact shall be capable
of exposing the exact supporting artifacts.

Examples include:

- a project processing state
- a Source disposition
- a framework-node coverage state
- an attention indicator
- a support assessment
- a Human Review status
- an issue

The presenter layer shall bind such values to immutable Evidence References.

An Evidence Reference contains at least:

```text
reference_type
reference_id
display_label
repository_relative_path
content_fingerprint
media_type
source_role
relationship
```

Optional navigation metadata may include:

```text
section_anchor
line_start
line_end
json_pointer
table_row_key
```

The dashboard shall not construct arbitrary filesystem paths in the UI.

Evidence paths shall be resolved by trusted repository-aware resolvers.

Each resolved path must:

- remain within the configured repository or Project Workspace root
- reject symbolic links where the owning repository rejects them
- correspond to an existing authoritative or derived artifact
- preserve project isolation
- preserve the artifact identity and fingerprint where available

### One Supporting Artifact

When exactly one Evidence Reference supports a displayed value, activating the
navigation control shall open that artifact directly in the internal document
viewer.

### Multiple Supporting Artifacts

When multiple Evidence References support a displayed value, activating the
navigation control shall open a compact evidence chooser.

The chooser shall:

- identify the relationship of each artifact to the displayed value
- show artifact type, stable ID and concise label
- preserve deterministic ordering
- distinguish direct evidence from contextual evidence
- allow one artifact to be opened without leaving the dashboard context

The chooser shall not silently choose one artifact when several materially
contribute to the result.

### No Supporting Artifact

When a displayed value has no resolvable supporting artifact, the dashboard
shall show that evidence navigation is unavailable.

It shall not create or guess a path.

Missing expected evidence shall be visible as an issue where the responsible
P2-P6 contract classifies it as invalid or blocking.

## Internal Document Viewer

The dashboard shall use an internal document viewer rather than browser
`file://` links.

This avoids platform-specific file access, browser security restrictions and
uncontrolled navigation outside the application.

The viewer shall support at least:

```text
JSON
Markdown
plain text
CSV
```

Viewer behavior:

- JSON is displayed in formatted, readable form
- Markdown is rendered and may also be shown as source text
- plain text preserves line structure
- CSV may be displayed as a table and as raw text
- unsupported binary content shows metadata and an explicit file action
- large files use bounded previews and explicit expansion
- fingerprints and repository-relative paths remain visible
- opening a document never changes its review or approval state

Where optional navigation metadata is available, the viewer may highlight:

- a Markdown section
- a line range
- a JSON field or object
- a table row

Highlighting is a navigation aid only and does not create a new persisted
reference authority.

## Navigation Context

Opening evidence shall preserve the user's dashboard context.

The application shall retain at least:

```text
selected project
current dashboard view
selected node, source, issue or support target
opened evidence reference
```

The user shall be able to return to the previous dashboard location without
reconstructing filters manually.

Deep links may use application query parameters for navigation state.

Deep links shall contain stable project and artifact identities, not unrestricted
filesystem paths.

## Dashboard Presentation Model

A new `modules.project_dashboard` package shall separate data collection,
presentation and Streamlit rendering.

The planned package is:

```text
modules/project_dashboard/
├── __init__.py
├── errors.py
├── types.py
├── references.py
├── presenter.py
└── service.py
```

The Streamlit layer is planned as:

```text
app/project_dashboard_ui.py
app/project_dashboard_app.py
```

### Dashboard Service

The dashboard service coordinates read-only calls to P2-P6.

It shall return a complete immutable dashboard snapshot.

It shall not expose repository objects directly to the UI.

### Presenter

The presenter transforms domain records into display-ready immutable view
models.

The presenter may:

- define stable ordering
- format concise labels
- group related records
- bind Evidence References
- derive display-only counts from already validated records
- select status labels and status semantics

The presenter shall not:

- recalculate Preliminary Coverage
- recalculate potential model support
- change issue severity
- infer approval
- infer missing evidence
- change processing state

### Streamlit UI

The Streamlit UI renders the supplied view models.

The UI shall contain minimal domain logic.

UI event handlers may:

- change the selected project
- change the active dashboard view
- open an Evidence Reference
- choose among multiple Evidence References
- apply presentation filters

UI event handlers shall not mutate P2-P6 project artifacts.

## Project Selection

The dashboard shall list existing Project Workspaces.

A project option shall display:

```text
<display name> · <six-digit Project ID>
```

The six-digit ID remains the stable internal project identity.

Project selection shall be deterministic.

An invalid or unsafe Project Workspace shall not be silently presented as a
valid project.

Project scan issues shall remain visible.

## Visual Design Principles

The dashboard shall be visually concise, calm and information-dense without
being cramped.

The default visual language shall use:

- neutral backgrounds
- neutral borders
- whitespace
- typography
- hierarchy
- alignment
- concise labels
- restrained icons

Color shall be used only to communicate status.

Color shall not be used merely for decoration, section identity, navigation or
branding emphasis.

Large decorative gradients, multicolored cards and unrelated accent colors are
out of scope.

### Status Semantics

The initial status families are:

```text
neutral
informational
candidate
reviewed
attention
blocking
unavailable
```

Status presentation shall combine:

```text
text label
icon or shape
color
```

Color shall never be the only carrier of meaning.

Suggested semantic intent:

```text
neutral or unavailable
→ gray

informational or unreviewed candidate
→ blue

reviewed candidate or covered
→ green

partial coverage or attention
→ amber

blocking, rejected or invalid
→ red
```

The exact color tokens belong to the UI implementation and tests.

Status colors shall be applied only to compact status-bearing elements such as:

- badges
- small indicators
- icons
- narrow status borders
- status text

Entire cards, pages or large table regions shall not be filled with status
colors.

The dashboard shall remain understandable in monochrome and for users with
color-vision deficiencies.

## Progressive Disclosure

The dashboard shall present summary before detail.

The initial view shows concise project-level status.

Detailed records are revealed through:

- expandable sections
- filtered tables
- evidence navigation
- the internal document viewer

The dashboard shall avoid displaying all identifiers and fingerprints in the
primary summary.

Exact identifiers, fingerprints and paths remain available in detailed views.

## Status Language

The dashboard shall preserve the exact meaning of P5 and P6 states.

The UI may provide concise explanatory text, but it shall not rename a state in
a way that changes its meaning.

In particular:

```text
potentially_supported
```

shall never be displayed as:

```text
ready
approved
complete
valid
generation-ready
```

The dashboard shall visibly expose:

```text
approved_readiness_status = not_available
approved_readiness_available_from_phase = G
```

The preferred user-facing explanation is:

```text
Approved Generation Readiness is not assessed in Phase P.
It becomes available from Phase G.
```

## Determinism

Equivalent project records shall produce equivalent dashboard snapshots.

Stable ordering shall be defined for:

- projects
- framework levels
- framework nodes
- Sources
- Processing Runs
- issues
- Human Review Decisions
- support targets
- Evidence References

The dashboard shall not depend on filesystem iteration order.

## Failure Behavior

The dashboard shall fail closed.

A failure to resolve one section shall not cause another section to invent data.

Where possible, the dashboard may render a partial snapshot with explicit
issues.

Examples:

```text
Coverage assessment unavailable
Source scan available
Processing scan available
```

A section failure shall show:

- affected section
- concise error
- relevant issue code
- available evidence navigation
- no fabricated status

Unexpected exceptions shall be converted into safe presentation errors before
reaching raw Streamlit output.

## Testing Strategy

P7 shall include tests for:

- immutable dashboard types
- project selection ordering
- presenter determinism
- status-label mapping
- status-color restriction
- project isolation
- Evidence Reference validation
- safe repository-relative path resolution
- single-evidence direct navigation
- multiple-evidence chooser behavior
- missing-evidence behavior
- internal viewer selection
- section and line navigation metadata
- source and processing presentation
- coverage and support presentation
- attention and Human Review presentation
- partial failure behavior
- public API exports
- Streamlit-independent rendering contracts

Core dashboard logic shall be testable without starting Streamlit.

Streamlit tests shall focus on thin integration behavior rather than duplicate
domain tests.

## Implementation Sequence

P7 is implemented in six steps:

```text
P7 Step 1 of 6
Architecture and ADR-014

P7 Step 2 of 6
Dashboard types, Evidence References and presenter foundation

P7 Step 3 of 6
Project selection and Project Overview

P7 Step 4 of 6
Processing, Coverage and Potential Support views

P7 Step 5 of 6
Attention, Human Review, traceability and document viewer

P7 Step 6 of 6
UI integration, tests, full regression and P7 acceptance
```

Consequences

Positive consequences:

- project status becomes accessible through one coherent interface
- every relevant displayed result can lead to its supporting artifacts
- multiple evidence chains remain explicit rather than hidden
- P2-P6 remain authoritative
- the existing ingestion UI remains stable
- the visual design communicates status without decorative noise
- the dashboard remains suitable for demonstration and technical inspection
- traceability becomes directly explorable
- core behavior remains testable without Streamlit

Negative consequences:

- evidence navigation requires additional immutable view-model types
- repository-aware path resolvers add implementation effort
- the internal viewer must safely handle multiple text formats
- deep-link and navigation context require explicit UI state handling
- the dashboard cannot provide write actions during P7
- some records may initially support only artifact-level rather than exact
  line-level navigation

Rejected Alternatives

### Merge P7 directly into the existing ingestion UI

Rejected because execution configuration and project-state inspection have
different responsibilities. Merging them would create a large UI with mixed
read and write semantics.

### Use direct `file://` links

Rejected because browser restrictions, platform differences and uncontrolled
filesystem access make them unreliable and unsafe.

### Open only repository-relative paths as plain text labels

Rejected because the user must be able to navigate directly to supporting
documents rather than manually locate them.

### Automatically open the first artifact when multiple artifacts contribute

Rejected because this would hide material evidence and could imply that one
artifact alone supports the displayed result.

### Recalculate coverage in the dashboard

Rejected because P6 is the sole owner of Preliminary Coverage and potential
model-support assessment.

### Use decorative colors for dashboard sections

Rejected because color is reserved for status semantics.

### Add approval and review actions to P7

Rejected because P7 is a read-only project dashboard. Write workflows require
their own explicit architecture and authority boundaries.

Acceptance Criteria

ADR-014 is satisfied when:

1. the dashboard is a separate read-only application
2. P2-P6 remain the sole domain authorities
3. every traceable displayed value can expose Evidence References
4. one Evidence Reference opens directly
5. multiple Evidence References produce an explicit chooser
6. arbitrary filesystem paths cannot be opened
7. an internal viewer supports JSON, Markdown, text and CSV
8. project and navigation context are preserved
9. status color is used only for status-bearing elements
10. status meaning is also conveyed through text and icon or shape
11. the dashboard exposes Preliminary Coverage and potential support accurately
12. Approved Generation Readiness remains explicitly unavailable in Phase P
13. the existing Team Agentic Ingestion UI remains unchanged
14. core dashboard behavior is testable without Streamlit
15. the complete repository regression remains green
