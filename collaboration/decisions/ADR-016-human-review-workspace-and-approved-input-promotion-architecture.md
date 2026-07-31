# ADR-016

Human Review Workspace and Approved Input Promotion Architecture

Status

Accepted

Date

2026-07-31

## Context

Phase P established the project-oriented processing and evidence architecture of
the Turing Generator.

The relevant existing capabilities are:

- project-isolated Source registration;
- immutable Processing Runs and Processing Events;
- immutable run-owned Agent Outputs, Consensus Reports, Review Reports and Run
  Summaries;
- source projections and independently reviewable Information Units;
- terminology and Framework Assignment Candidates;
- immutable Human Review Decisions bound to exact content and validation
  fingerprints;
- project-level Processing and evidence presentation;
- project-bound Agentic Ingestion ending in `awaiting_review`.

A completed Processing Run produces authoritative evidence of what the system
processed and generated. It does not produce approved engineering information.

The authoritative CATIA model assigns the required behavior to:

```text
SF_007 Support Human Review and Approval
```

and to the Logical Component:

```text
LC_05 Candidate and Review Governance
```

The primary applicable System Requirements include:

```text
SYSR_014 Provide Generated Interpretations for Expert Review
SYSR_015 Require Review Before Subsequent Engineering Use
SYSR_016 Support Human Resolution of Conflicting Interpretations
SYSR_017 Record Human Conflict Resolution
SYSR_038 Capture Human Review Decision
SYSR_095 Bind Review Decision to Reviewed Content
SYSR_096 Require New Review after Content Change
SYSR_097 Retain Review Decision Accountability
SYSR_098 Distinguish Engineering Information Authority State
SYSR_099 Promote Approved Engineering Information
SYSR_100 Prevent Unauthorized Engineering Use
SYSR_101 Prevent Automated Approval Substitution
```

The applicable SysML v2 representation requirements include:

```text
SYSR_024 Generate SysML v2 Textual Representation
SYSR_072 Validate SysML v2 Textual Conformance
```

The current Phase F/P review artifacts may contain dozens of detected engineering
items. Different agents may produce equivalent, competing, partially overlapping
or differently classified proposals.

A useful Human Review workflow therefore cannot treat a complete report as one
binary approval target.

The user must be able to:

- review all agent proposals for the same detected subject;
- accept one proposal with one click;
- automatically mark competing variants as not selected;
- edit a proposal inline;
- combine content from multiple proposals;
- reject one proposal or the complete detected subject;
- apply document-level classification decisions where a document is homogeneous;
- override document-level decisions for individual items;
- apply focused decisions to a visible filtered result set;
- review elements and relationships separately;
- resolve open questions without losing overview;
- inspect rejected content;
- compare the original machine-generated report with the human-reviewed version;
- continue editing until the review is explicitly finalized;
- reopen a finalized document only by creating a documented successor version.

The original Source, Agent Outputs, Consensus Reports and Review Reports must
remain immutable.

A human-reviewed document has higher engineering authority than its original
machine-generated report only after explicit finalization and an exact persisted
Human Review Decision.

Phase G must create the authoritative bridge:

```text
Processing Evidence
→ Human Review Workspace
→ Finalized Reviewed Document
→ Approved Input
```

Phase G shall not generate model candidates, an internal engineering model or
SysML v2 architecture artifacts.

## Decision

### 1. Implement Phase G as the concrete realization of SF_007

Phase G shall implement and decompose:

```text
SF_007 Support Human Review and Approval
```

inside the accepted responsibility of:

```text
LC_05 Candidate and Review Governance
```

No new top-level System Function or Logical Component is introduced by this
decision.

The Phase G implementation shall provide:

1. a versioned Human Review Workspace;
2. exact preservation of machine-generated review evidence;
3. document-, filtered-set- and item-level review operations;
4. explicit finalization of one reviewed document version;
5. exact Human Review Decision binding;
6. Approved Input promotion for accepted review items;
7. Approved Input invalidation, revocation and supersession;
8. a stable Approved Input read contract for Phase H.

### 2. Preserve an explicit authority hierarchy

The authority hierarchy for Phase G shall be:

```text
Original Source
    immutable source authority

Agent Outputs and Consensus Reports
    immutable processing evidence

Original Review Report
    immutable machine-generated review presentation

Draft Review Version
    human working state, not approved engineering information

Finalized Reviewed Document Version
    immutable human-reviewed result

Approved Input
    authoritative project-local input for subsequent engineering processing
```

No higher level may overwrite a lower level.

Human review shall create additional versioned artifacts and references. It
shall never modify the original Source, processing artifacts, prior finalized
review versions, prior Human Review Decisions, Approved Input manifests or
Approved Input lifecycle events.

### 3. Introduce Human Review Workspace identities

Phase G shall introduce the following project-local identities:

```text
RVD-000001  Review Document
RVV-000001  Review Document Version
RVR-000001  Review Revision
RIT-000001  Review Item
SRA-000001  Scoped Review Action
AIN-000001  Approved Input
AIE-000001  Approved Input Event
```

Identifiers are project-local, sequential, immutable and never reused.

#### Review Document

A Review Document identifies one review workspace created from one exact eligible
evidence set.

It binds at least:

```text
project_id
review_document_id
source_id
source_sha256
processing_run_id
attempt_id
primary_review_artifact_reference
supporting_artifact_references
framework_template_reference
semantic_reference_versions
created_at
content_fingerprint
```

#### Review Document Version

A Review Document Version is one human-review version of a Review Document.

It binds at least:

```text
review_document_version_id
review_document_id
version_number
predecessor_version_id
reopen_reason
opened_by
opened_at
version_state
head_revision_id
finalized_revision_id
finalized_at
finalization_decision_id
content_fingerprint
```

Allowed version states are:

```text
draft
finalized
```

A finalized version is immutable.

#### Review Revision

A Review Revision is one immutable saved snapshot of a draft Review Document
Version.

The user experience may present one continuously editable working copy. The
persistence model shall remain append-only:

```text
save draft
→ create next immutable Review Revision
→ preserve all previous revisions
```

The current draft state is the latest valid revision derived from repository
history. A mutable authoritative `current.json` file shall not be introduced.

#### Review Item

A Review Item represents one independently reviewable subject.

Allowed Review Item kinds are:

```text
element
relationship
open_question
```

`rejected_content` is a presentation view derived from item decisions. It is not
a separate source item kind.

One Review Item may contain multiple Agent Proposal References.

A Review Item shall preserve at least:

```text
review_item_id
review_item_kind
stable_subject_key
section
original_report_locator
proposal_references
source_evidence_references
consensus_evidence_references
current_human_content
current_classification
current_framework_assignment
current_terminology_assignment
current_source_assignments
current_relationship_representation
effective_review_outcome
item_content_fingerprint
```

The `stable_subject_key` supports continuity across document versions.

The system shall support explicit human correction when automatic grouping is
wrong:

```text
split Review Item
merge selected Review Items
```

Split and merge operations shall preserve all original proposal references and
shall be represented in Review Revision history.

#### Scoped Review Action

A Scoped Review Action represents one draft decision applied to more than one
Review Item or to one review dimension.

It shall bind:

```text
scoped_review_action_id
review_document_version_id
action_scope
decision_dimension
selected_value
filter_definition
materialized_review_item_ids
materialized_item_fingerprints
created_by
created_at
rationale
action_fingerprint
```

Allowed action scopes are:

```text
document_default
filtered_set
explicit_selection
```

A filtered action shall store both the filter definition shown to the user and
the exact Review Item IDs and fingerprints matched at action time.

It shall never remain a dynamic query that silently changes its effect when later
Review Items are added, removed or edited.

### 4. Create Review Documents from exact eligible evidence

Phase G shall support Review Documents derived from eligible P4 and P9 evidence.

#### P4 evidence

Eligible P4 review sources include:

```text
Information Units
Terminology Mapping Candidates
Framework Assignment Candidates
associated reference validations
associated Human Review evidence
```

An Information Unit remains the smallest independently understandable and
reviewable source-derived claim.

Terminology and Framework Assignment Candidates are supporting classifications.
They do not automatically become standalone Approved Inputs.

#### P9 evidence

Eligible P9 review sources include one exact active project-bound evidence set:

```text
primary deterministic Review Report
underlying Agent Outputs
Consensus Reports
Run Summary
Processing Artifact References
Processing Run and Attempt identity
```

The system shall construct Review Items from structured evidence. It shall not
depend on free-form Markdown parsing as the sole source of Review Item identity.

The original Markdown Review Report remains the immutable human-readable source
view.

The Review Workspace shall render structured Review Items inside a report-like
document view so that editing feels local to the relevant report section.

A complete report shall never become one Approved Input.

One accepted Review Item may become one Approved Input.

#### Non-promotable evidence

The following are evidence or review-control information and shall not directly
become Approved Input:

```text
Agent confidence
Consensus level
variance indication
model buildability assessment
general recommendation
gap
risk
ambiguity
unanswered review question
run summary
processing completion
artifact publication
```

An answer to an open question may become promotable only when the reviewer
explicitly converts it into a reviewed engineering statement.

### 5. Present all Agent proposals without losing evidence

For each Review Item, the user interface shall present all associated Agent
Proposal References.

The UI may visually consolidate materially equivalent variants. It shall retain
exact access to every original proposal.

Each proposal view shall expose at least:

```text
agent identity
persona identity
candidate identity
proposed content
proposed classification
proposed Framework Assignment
proposed source assignments
rationale
confidence
generation-readiness statement
supporting and missing evidence
artifact reference
content fingerprint
```

The following quick actions are required for each proposal:

```text
Accept proposal
Edit and accept
Reject proposal
```

The following item-level actions are required:

```text
Combine proposals
Reject all proposals for this Review Item
Defer Review Item
Mark Review Item out of scope
Split Review Item
Merge selected Review Items
```

Selecting one proposal shall mark competing proposals for the same Review Item
as:

```text
not_selected_due_to_human_selection
```

This state is distinct from a finding that a competing proposal is factually
incorrect.

Proposal-selection actions remain draft operations until document finalization.

### 6. Support inline editing through human revisions

The Review Workspace shall allow direct inline editing of the current reviewed
content.

The UI shall make the edited block appear in the position of the corresponding
Review Item in the report-like document view.

Technically, the system shall create human-authored content in a new Review
Revision. It shall not modify the original Agent Proposal.

Editable review dimensions include:

```text
name
engineering statement
description
classification
information type
modality
epistemic status
Framework Assignment
terminology assignment
source assignments
human rationale
human confidence assessment
relationship representation
```

Agent-generated fields remain immutable evidence. Human-edited values are
explicit overrides.

A human revision shall preserve:

```text
derived_from_proposal_ids
derived_from_review_item_ids
original content fingerprints
revised content fingerprint
changed fields
reviewer identity
change time
optional change rationale
```

A rationale is mandatory when:

- a finalized document is reopened;
- a proposal or complete Review Item is rejected;
- a previous Approved Input is revoked;
- a selected SysML v2 relationship construct differs materially from all
  proposed constructs;
- a blocking finding is overridden where an override is permitted.

### 7. Separate review dimensions and define precedence

Review decisions shall not collapse all aspects of one Review Item into one
undifferentiated state.

The system shall support independent review dimensions, including:

```text
content
classification
Framework Assignment
terminology assignment
source assignment
relationship representation
review outcome
```

A document-level decision may set a default for one dimension without approving
all content.

Example:

```text
Document default:
Framework Assignment = System Requirements
```

This does not automatically approve all Requirement statements.

Effective decision precedence is:

```text
item override
> explicit-selection or materialized filtered-set action
> document default
> selected Agent proposal
```

The UI shall show the origin of every effective value.

Recommended compact indicators are:

```text
E  item-level explicit decision
F  materialized filtered-set or explicit-selection decision
D  document default
A  Agent proposal
```

A scoped action shall not overwrite an existing higher-precedence decision
unless the user explicitly requests that overwrite and confirms a preview of the
affected Review Items.

### 8. Use filters as focused review tools

Required filter dimensions include at least:

```text
review status
Review Item kind
proposed classification
effective classification
proposed Framework Assignment
effective Framework Assignment
Agent identity
confidence
Consensus state
Agent disagreement
human modification state
Source identity
evidence sufficiency
relationship validation status
```

Every scoped action shall visibly state whether it applies to:

```text
the complete document
the currently materialized filtered result
an explicit manual selection
one Review Item
```

Before applying a scoped action, the UI shall show:

```text
number of affected Review Items
number with existing item overrides
number excluded because of higher-precedence decisions
number that would be overwritten after explicit confirmation
```

Dangerous bulk rejection shall not be implemented as an unqualified one-click
action.

A rejection affecting more than one Review Item requires a materialized target
list, an impact preview, explicit confirmation and a rationale.

### 9. Use four primary review sections

The Human Review Workspace shall use:

```text
Elements
Relationships
Open Questions
Rejected Content
```

#### Elements

The Elements section presents detected engineering-element proposals.

It shall support grouping and filtering by applicable model area, information
type and classification.

The section shall not imply that Phase G has generated final model elements. It
presents reviewed engineering information and modeling suggestions.

#### Relationships

The Relationships section presents only explicit relationship proposals already
contained in eligible evidence.

Phase G shall not invent missing relationships.

The section may be empty when the source evidence does not contain an explicit
relationship proposal.

Relationship proposals remain separately reviewable from element proposals.

#### Open Questions

The Open Questions section presents:

```text
gaps
ambiguities
risks requiring a decision
missing evidence
review questions
unresolved classifications
unresolved relationship constructs
```

An open question may be answered, closed as not relevant, deferred, marked out
of scope, linked to Review Items or converted into a human-authored engineering
statement.

#### Rejected Content

Rejected Content is an auditable view, not a deletion area.

It shall show the rejected proposal or item, original Agent and artifact
reference, rejection rationale, replacement where applicable, document version,
reviewer and time.

### 10. Require SysML v2 target-notation conformance for relationships

The Relationship review interface shall use only constructs defined by the
applicable versioned SysML v2 target-notation profile of the Turing Generator.

The UI shall not expose generic MBSE relationship labels or SysML v1 relationship
names as authoritative relationship types.

The allowed construct vocabulary shall be loaded from the selected versioned
target-notation profile. It shall not be maintained as an independent hard-coded
UI list.

A relationship proposal shall preserve at least:

```text
source Review Item or referenced element
target Review Item or referenced element
relationship semantic intent
selected SysML v2 construct
construct-specific properties
target-notation profile ID
target-notation profile version
textual-notation preview
supporting evidence
alternative proposed constructs
profile-validation status
profile-validation fingerprint
human review status
```

A textual preview shall use the applicable SysML v2 notation.

Example for an applicable dependency construct:

```sysml
dependency from 'Source Element' to 'Target Element';
```

The exact syntax shall be produced and validated by the applicable target
notation profile, not by free-form UI concatenation.

When no supported construct can be selected, the item state shall be:

```text
unresolved_relationship_candidate
```

An unresolved relationship candidate remains visible, may be edited, deferred,
marked out of scope or rejected, and shall not become Approved Input for
model-generation use.

This decision does not move SysML v2 artifact generation into Phase G.

Phase G reviews an existing relationship proposal and its intended applicable
construct. Phases H to J remain responsible for model candidate creation,
internal model representation and final SysML v2 artifact generation.

### 11. Keep draft actions reversible until explicit finalization

The following actions modify only the current draft version:

```text
accept proposal
edit proposal
combine proposals
reject proposal
reject Review Item
change classification
change Framework Assignment
change terminology assignment
change source assignment
change relationship representation
answer question
defer
mark out of scope
split
merge
apply document default
apply materialized filtered-set action
```

These actions shall be automatically saved through immutable Review Revisions.
They are reversible while the version remains `draft`.

They do not create Approved Input or an authoritative final Human Review
Decision.

### 12. Finalize one exact reviewed document version

The user finalizes a draft through an explicit operation conceptually labeled:

```text
Review abschließen und freigeben
```

Before finalization, the system shall present a summary including at least:

```text
total Review Items
accepted as generated
accepted with human modification
combined
rejected
deferred
out of scope
unresolved
relationship validation results
open questions
changed items compared with predecessor version
```

Finalization shall fail closed when:

- the Project, Source, Run or Artifact binding is invalid;
- an authoritative evidence fingerprint has changed;
- the selected Review Revision is not the current head revision;
- a Review Item has no explicit or effective review outcome;
- an unresolved item is not explicitly `deferred` or `out_of_scope`;
- a relationship selected for approval is not valid under the applicable SysML
  v2 target-notation profile;
- a blocking evidence or integrity issue exists;
- a cross-project reference exists;
- a required supporting artifact is unavailable, superseded or invalidated;
- a predecessor-version relation is inconsistent.

Finalization shall create:

```text
immutable Finalized Reviewed Document manifest
immutable rendered Reviewed Report
immutable effective decision set
exact content fingerprint
exact validation fingerprint
```

The rendered Reviewed Report is the primary human-readable reviewed artifact.
The effective decision set is the primary machine-readable record.

The finalization target shall be added to the Human Review target vocabulary:

```text
target_type: review_document_finalization
target_id: RVV-000001
```

Finalization requires an exact persisted decision:

```text
decision: confirm
review_mode: detailed_review
```

The Human Review Decision shall bind the exact Review Document Version content
fingerprint, validation fingerprint, reviewer identity, decision time and
outcome.

Consensus, confidence, processing completion and artifact publication cannot
substitute this decision.

### 13. Reopen finalized documents only through a successor version

A finalized Review Document Version shall never become editable again.

A user may reopen the Review Document only by creating a successor Review
Document Version.

Reopening requires a rationale and records:

```text
predecessor version
reopen reason
opened by
opened at
baseline item fingerprints
baseline effective decisions
```

The successor draft is initialized from the finalized predecessor.

The UI shall provide:

```text
Review Copy
Original Report
Changes to Original
Changes to Predecessor Version
Version History
```

A later finalized version shall not rewrite or delete its predecessor.

### 14. Define Approved Input as one approved Review Item

One Approved Input represents one independently reviewable and approved
engineering-information item.

Allowed initial Approved Input kinds are:

```text
element_statement
relationship_statement
human_clarification
```

An Approved Input Manifest shall bind at least:

```text
schema_version
project_id
approved_input_id
approved_input_kind
authority_state
canonical_content
selected_classification
selected_framework_assignment
selected_terminology_assignment
selected_source_assignments
selected_relationship_representation
review_document_id
review_document_version_id
review_revision_id
review_item_id
review_item_fingerprint
finalization_decision_id
finalization_decision_fingerprint
finalization_validation_fingerprint
source_id
source_sha256
processing_run_id
attempt_id
primary_artifact_reference
supporting_artifact_references
proposal_references
created_at
content_fingerprint
```

One finalized Reviewed Document Version may create zero, one or many Approved
Inputs.

No Approved Input is created for an item whose effective outcome is:

```text
rejected
deferred
out_of_scope
unresolved
```

An open question creates no Approved Input unless the reviewer explicitly
converts its answer into an approved clarification or engineering statement.

### 15. Define Approved Input authority and lifecycle

Approved Input manifests are immutable. Lifecycle changes are represented by
immutable Approved Input Events.

Allowed derived Authority States are:

```text
active
invalidated
revoked
superseded
```

#### Active

The Approved Input is valid for subsequent engineering use.

#### Invalidated

The Approved Input has lost technical or upstream integrity.

Examples include Source or artifact fingerprint mismatch, invalid Run binding,
invalid finalization decision binding, relationship-profile validation failure
or project-isolation failure.

Invalidation is system- or integrity-driven.

#### Revoked

A human-reviewed successor version explicitly withdraws the authority of a
previous Approved Input without approving a replacement.

Examples include a previously accepted item that is now rejected, out of scope
or explicitly withdrawn.

Revocation requires a rationale and reviewer accountability.

#### Superseded

A newer active Approved Input explicitly replaces an older Approved Input for the
same stable review subject.

The old Approved Input remains immutable and traceable.

`rejected` is not an Approved Input lifecycle state. Rejected Review Items do not
create Approved Inputs.

### 16. Reconcile successor versions item by item

When a successor Review Document Version is finalized, the system shall compare
stable Review Item identities and fingerprints with the predecessor version.

Required behavior:

```text
unchanged accepted item
→ retain existing active Approved Input

changed item accepted again
→ create new Approved Input
→ mark previous Approved Input superseded

previously accepted item now rejected
→ revoke previous Approved Input

previously accepted item now out of scope
→ revoke previous Approved Input

new accepted item
→ create new Approved Input

upstream integrity failure
→ invalidate affected Approved Input
```

Unchanged items shall not receive new Approved Input IDs merely because the
containing document received a new version.

### 17. Extend the existing Human Review repository

The existing Human Review Decision repository remains authoritative for final
Human Review Decisions.

Phase G shall extend it with:

```text
review_document_finalization
```

It shall not introduce a parallel incompatible decision repository.

Existing target types remain valid:

```text
information_unit_publication
terminology_mapping_candidate
framework_assignment_candidate
```

The existing exact-confirmation principle remains:

```text
target ID matches
target content fingerprint matches
validation fingerprint matches
latest exact decision is confirm
target validation is not invalid
```

A stale Human Review Decision cannot authorize finalization or promotion of
changed content.

### 18. Define promotion eligibility

A finalized Review Item is eligible for Approved Input promotion only when all of
the following are true:

```text
Project exists and matches all references
Source exists and exact SHA-256 matches
Processing Run exists and matches Source and Project
Processing Run is valid for promotion
primary artifact reference is active
supporting artifact references are valid
Review Document Version is finalized
exact finalization Human Review Decision exists
exact finalization fingerprints match
effective item outcome is accepted
Review Item fingerprint is included in finalized version
no blocking evidence issue applies
required Framework and terminology references are valid
relationship representation is profile-valid where applicable
no cross-project reference exists
no newer lifecycle event blocks the item
```

Eligibility shall be recalculated immediately before promotion.

A previously calculated eligibility result is advisory unless it is bound into
the finalization validation fingerprint and revalidated at promotion time.

### 19. Define project-local persistence

The conceptual project-local structure shall be:

```text
data/projects/<project_id>/
├── reviews/
│   └── RVD-000001/
│       ├── review_document_manifest.json
│       └── versions/
│           ├── RVV-000001/
│           │   ├── review_version_manifest.json
│           │   ├── revisions/
│           │   │   ├── RVR-000001.json
│           │   │   └── RVR-000002.json
│           │   ├── scoped_actions/
│           │   │   └── SRA-000001.json
│           │   └── finalized/
│           │       ├── reviewed_document.json
│           │       ├── effective_decisions.json
│           │       └── reviewed_report.md
│           └── RVV-000002/
│               └── ...
├── semantics/
│   └── human_reviews/
│       └── HRD-000001.json
└── approved_inputs/
    ├── manifests/
    │   └── AIN-000001.json
    └── events/
        └── AIN-000001/
            ├── AIE-000001.json
            └── AIE-000002.json
```

The exact internal file split may be refined during implementation.

Mandatory boundaries are:

- original run-owned artifacts stay under the Processing Run;
- review artifacts are project-local;
- Human Review Decisions stay in the existing repository;
- Approved Inputs have one dedicated project-local repository;
- persisted paths are repository-relative;
- symbolic links and path traversal are rejected;
- no operation may silently cross a Project boundary.

### 20. Define public application contracts

The Human Review Workspace shall expose conceptual public operations equivalent
to:

```python
ReviewWorkspaceService.open_review_document(...)
ReviewWorkspaceService.create_review_document(...)
ReviewWorkspaceService.save_revision(...)
ReviewWorkspaceService.apply_scoped_action(...)
ReviewWorkspaceService.split_review_item(...)
ReviewWorkspaceService.merge_review_items(...)
ReviewWorkspaceService.finalize_version(...)
ReviewWorkspaceService.reopen_finalized_version(...)
```

Repository operations shall conceptually include:

```python
ReviewWorkspaceRepository.load_document(...)
ReviewWorkspaceRepository.load_version(...)
ReviewWorkspaceRepository.load_revision(...)
ReviewWorkspaceRepository.list_versions(...)
ReviewWorkspaceRepository.scan(...)
```

Approved Input operations shall conceptually include:

```python
ApprovedInputPromotionService.assess_eligibility(...)
ApprovedInputPromotionService.promote_finalized_version(...)
ApprovedInputLifecycleService.invalidate(...)
ApprovedInputLifecycleService.revoke(...)
ApprovedInputLifecycleService.supersede(...)
```

The stable Phase H read contract shall be:

```python
ApprovedInputRepository.list_active_approved_inputs(
    project_id,
) -> tuple[ApprovedInputManifest, ...]
```

Phase H shall not read mutable draft Review Revisions, original Review Reports as
model-generation authority, Agent confidence or Consensus as approval authority,
Human Review UI state, or inactive Approved Inputs.

### 21. Define finalization and promotion failure behavior

Finalization and promotion cannot be one filesystem-atomic transaction across all
repositories.

The required sequence is:

```text
1. validate current Review Revision
2. persist immutable finalized Review Document artifacts
3. record exact Human Review Decision
4. revalidate promotion eligibility
5. create Approved Input manifests
6. append required lifecycle events
7. report complete or recovery-required status
```

No Approved Input may be created before the exact finalization Human Review
Decision exists.

If finalization artifacts exist but the Human Review Decision cannot be recorded,
the document is not treated as approved, no Approved Input is created and
recovery is required.

If the Human Review Decision exists but promotion is only partially completed,
existing promoted items remain traceable, the operation is not reported as fully
successful and deterministic recovery resumes idempotently.

Promotion idempotence shall be based on at least:

```text
project_id
review_document_version_id
review_item_id
review_item_fingerprint
finalization_decision_fingerprint
```

Equivalent duplicate promotion shall not create a second active Approved Input.

### 22. Define the required Human Review user experience

The Review Workspace is a critical engineering interface.

Its default layout shall preserve overview through:

```text
left:
document outline, item list, filters and status counts

center:
report-like reviewed document with inline item editing

right:
all Agent proposals, comparison, evidence and original content
```

The interface shall provide:

```text
Elements
Relationships
Open Questions
Rejected Content
```

The active Project, Source, Processing Run, Review Document and version shall
remain visible.

The UI shall provide:

```text
Review Copy
Original Report
Diff to Original
Diff to Predecessor
Version History
```

Required status counts include:

```text
open
accepted as generated
accepted with modification
combined
rejected
deferred
out of scope
unresolved
```

The UI shall offer one-click item operations where safe.

One-click draft actions shall not be confused with final document approval. The
final approval operation shall be visually distinct and shall always show a
complete impact summary.

### 23. Preserve review and rework loops

Human Review may determine that information must return to an earlier processing
capability.

The workspace shall support explicit outcomes conceptually equivalent to:

```text
request source-information rework
request semantic-governance rework
request candidate-regeneration
```

These outcomes remain traceable to the affected Review Items and do not create
Approved Input.

The exact Processing Run successor or retry behavior remains governed by the
accepted Processing architecture.

### 24. Define implementation sequence

Phase G shall proceed in the following steps:

```text
G1
ADR-016 and Phase G contract acceptance

G2
Human Review Workspace identifiers, immutable types, manifests and repositories

G3
P4/P9 evidence adapters and deterministic Review Item construction

G4
Draft revisions, scoped actions, version finalization and reopening

G5
Approved Input manifests, repository, eligibility, promotion and lifecycle

G6
Human Review Workspace UI with Elements, Relationships, Open Questions and
Rejected Content

G7
Project-bound integration, recovery behavior, manual acceptance audit and full
regression
```

The first executable implementation step after ADR-016 shall define contracts and
tests before UI implementation.

## Consequences

### Positive consequences

- The original machine-generated evidence remains permanently available.
- The user can edit a report naturally without weakening traceability.
- One large report can produce many independently reviewed Approved Inputs.
- All Agent proposals remain visible and attributable.
- One-click selection remains possible without making draft clicks immediately
  authoritative.
- Document-level decisions reduce repetitive review effort.
- Item-level overrides support mixed documents.
- Materialized filter actions provide focused review without dynamic-scope risk.
- Elements and relationships remain visually separated.
- Open questions remain visible instead of disappearing into report prose.
- Rejected content remains auditable.
- Finalized documents are immutable.
- Reopening creates an explicit successor version.
- Unchanged Approved Inputs remain stable across document versions.
- Changed Approved Inputs are superseded rather than overwritten.
- Human withdrawal is distinguishable from technical invalidation.
- Relationship review uses the applicable SysML v2 target notation instead of
  generic or obsolete relationship labels.
- Phase H receives one stable, project-local Approved Input contract.

### Negative consequences

- The Phase G persistence model is more complex than a mutable edited Markdown
  file.
- The UI requires structured Review Items and cannot rely only on Markdown.
- Proposal grouping, split and merge behavior require deterministic identities
  and careful testing.
- Document defaults and item overrides require transparent precedence rules.
- Version finalization and Approved Input promotion require recovery handling.
- SysML v2 relationship review depends on an available versioned target-notation
  profile.
- A complete review can produce many immutable manifests and events.

### Accepted complexity

The additional complexity is accepted because the Human Review Workspace is an
engineering authority boundary.

A simpler mutable-report design would not provide sufficient decision binding,
version accountability, item-level approval, Agent-evidence preservation,
project isolation, stale-decision prevention, relationship-notation conformance,
Approved Input lifecycle or downstream traceability.

## Rejected alternatives

### Edit the original Review Report in place

Rejected because it would destroy the immutable record of machine-generated
evidence and make exact decision reconstruction unreliable.

### Copy and edit one unstructured Markdown document only

Rejected because item identities, proposal variants, scoped decisions,
fingerprints and downstream Approved Input promotion would be unreliable.

### Approve or reject the complete report as one target

Rejected because reports may contain dozens of independently correct, incorrect
or incomplete items.

### Require one manual click for every classification in every document

Rejected because homogeneous documents require efficient document-level
decisions.

### Apply document-level decisions without item overrides

Rejected because mixed documents require explicit exceptions.

### Keep filter actions as dynamic saved queries

Rejected because later content changes could silently change the set affected by
an earlier decision.

### Treat unselected Agent proposals as factually rejected

Rejected because choosing one variant does not necessarily prove all alternatives
incorrect.

### Let Agent confidence or Consensus authorize approval

Rejected because automated evidence cannot replace explicit human approval.

### Store one mutable current review state

Rejected because it would weaken history reconstruction and recovery.

### Reopen and modify a finalized version directly

Rejected because it would invalidate the meaning of the original finalization
decision.

### Use generic relationship types in the UI

Rejected because relationship review must use the applicable SysML v2
target-notation profile and remain compatible with later validated textual
generation.

### Generate model candidates in Phase G

Rejected because model candidate generation belongs to Phase H and must consume
Approved Input through the stable read contract.

## Acceptance

The project owner explicitly accepted:

- immutable original reports;
- editable draft Review Copies;
- immutable finalized reviewed versions;
- documented reopening through successor versions;
- inline element editing;
- all Agent proposals in one item-centered review view;
- one-click proposal selection;
- automatic non-selection of competing variants;
- document-level and item-level decisions;
- focused materialized filter actions;
- separate Elements, Relationships, Open Questions and Rejected Content sections;
- dangerous bulk rejection only with preview, confirmation and rationale;
- versioned Approved Input promotion;
- invalidation, revocation and supersession behavior;
- mandatory use of applicable SysML v2 target notation for relationship review;
- the complete Phase G architecture documented in this ADR.
