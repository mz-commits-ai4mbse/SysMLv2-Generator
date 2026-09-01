# ADR-032 — Project-Level Multi-Source Reconciliation and Controlled Engineering Evolution

## Status

Accepted

## Date

2026-08-31

## Context

The Turing Generator currently processes registered engineering sources through source-bound Processing Runs.

ADR-012 intentionally established this boundary:

- one Processing Run processes one primary registered source;
- Information Units and downstream processing evidence remain source-traceable;
- equivalent, overlapping, or contradictory information from different sources remains separate during source-level processing;
- project-level comparison is a later responsibility.

ADR-025 and ADR-026 subsequently introduced source-anchored semantic consolidation and Persona-aware interpretation. These capabilities improve semantic consistency inside one source-processing context but do not provide project-level reconciliation between independent registered sources.

WP-12 Multi-Source validation exposed BLK-002:

> Local Processing Artifact identities such as `IU-000001` can legitimately occur in different Processing Runs, while existing project-level lifecycle aggregation incorrectly treats `(artifact_type, artifact_id)` as a globally unique artifact identity.

Resolving this collision is necessary but not sufficient for genuine Multi-Source processing.

A project may contain:

- several engineering sources describing the same product;
- complementary documents covering different engineering viewpoints or abstraction levels;
- contradictory or materially different statements;
- context-only documents that establish product terminology and system understanding;
- accidentally registered documents that belong to another project;
- already Human-reviewed engineering information and an existing accepted model when additional sources are registered later.

The architecture must therefore distinguish:

1. source-local processing;
2. project-fit assessment;
3. cross-source semantic reconciliation;
4. Human Engineering Authority;
5. model-impact reconciliation.

The system must not force unrelated information into a common semantic subject merely because it belongs to the same Project.

Likewise, absence of semantic overlap does not imply that a source belongs to another Project. A BOM, interface specification, requirement specification and user-needs document may contain very different terminology while still describing the same product.

Context-only sources exist explicitly to provide product and domain understanding and shall be usable for this purpose without becoming Engineering Authority.

Finally, newly registered information must not automatically override already reviewed information merely because the source is newer. Existing Human-reviewed Approved Inputs remain Engineering Authority until a subsequent Human Review explicitly changes that authority.

---

## Decision

### 1. Preserve source-bound Processing

Existing source-level Processing remains source-bound.

The following conceptual flow remains unchanged:

```text
Registered Source
→ Source Projection
→ Source Analysis Units / Evidence
→ Source-local Interpretation
→ Canonical Engineering Subjects
→ Persona Interpretation / Consensus
```

No source-level Processing stage may silently merge evidence from independent registered engineering sources.

All source-derived artifacts retain exact Source, Processing Run and Attempt provenance.

---

### 2. Qualify Processing Artifact identity by Processing Run at project-wide boundaries

A `ProcessingArtifactReference` remains a run-local artifact reference and shall not be extended with additional persisted identity fields solely to resolve BLK-002.

Within one Processing Run, local artifact identity remains:

```text
(artifact_type, artifact_id)
```

At boundaries that aggregate several Processing Runs, effective artifact identity becomes:

```text
(processing_run_id, artifact_type, artifact_id)
```

Therefore:

```text
RUN-000001 / information_unit / IU-000001
RUN-000002 / information_unit / IU-000001
```

are legal independent artifacts.

Within the same Processing Run, conflicting immutable references, duplicate publication and other existing integrity violations remain fail-closed.

No historical Processing Artifact manifest migration is required.

---

### 3. Introduce a Project Fit Assessment before cross-source reconciliation

A processed source shall not automatically participate in project-level semantic reconciliation merely because it was registered inside the Project.

A new derived processing boundary shall assess:

> Is this source plausibly part of the product/system represented by this Project?

The assessment may use:

- explicit `context_only` sources;
- project/product contextual information;
- terminology and concepts derived from existing project sources;
- existing active Human-reviewed engineering information where available.

Context information is evidence for project understanding. It is not Engineering Authority merely because it is used by the Project Fit Assessment.

The Project Fit Assessment produces one of:

```text
plausible_in_scope
uncertain
likely_out_of_scope
```

The result is machine-generated processing evidence.

It does not modify:

- the Source Manifest;
- the registered Source Role;
- Engineering Authority;
- Approved Inputs;
- the engineering model.

`plausible_in_scope` permits the source to continue toward project-level reconciliation.

`uncertain` and `likely_out_of_scope` prevent the source from entering project-level engineering reconciliation until a Human Processing Decision resolves its treatment.

The source remains registered and auditable in every case.

Existing source dispositions defined by ADR-012 remain authoritative for operational source treatment:

```text
in_scope
context_only
out_of_scope
```

The Project Fit Assessment may support such a Human decision but does not replace it.

---

### 4. Introduce Project-Level Cross-Source Semantic Reconciliation

Only sources admitted to project-level engineering processing participate in Cross-Source Semantic Reconciliation.

This boundary operates after sufficiently stable source-local Engineering Subjects and Persona interpretation/consensus are available.

Its purpose is not to determine model placement.

It answers:

> How are engineering statements from different sources semantically related?

Supported semantic relations are:

```text
equivalent
complementary
potential_conflict
distinct
uncertain
```

#### Equivalent

Two or more source contributions express substantially the same engineering meaning.

They may be presented as one project-level review subject while retaining all individual source evidence.

#### Complementary

Contributions relate to the same engineering concern but provide different, non-competing information, abstraction levels, viewpoints or detail.

They shall not be collapsed into one statement merely because they overlap semantically.

#### Potential conflict

Contributions appear to make materially incompatible claims concerning the same engineering concern.

The system records the variance but does not select a winner.

#### Distinct

The contributions represent separate engineering subjects.

#### Uncertain

The semantic relationship cannot safely be determined.

Uncertain contributions remain separate and visible for Human reasoning.

---

### 5. LLM-assisted semantic comparison has no Engineering Authority

Project Fit Assessment and Cross-Source Semantic Reconciliation may use bounded LLM calls.

LLMs may propose semantic relationships and supporting reasoning evidence.

They may not authorize:

- Engineering Approval;
- source priority;
- automatic truth selection;
- automatic supersession;
- model modification;
- semantic merging without valid evidence.

The following never constitute Engineering Authority:

```text
LLM confidence
number of agreeing sources
source order
source age
source type
Persona consensus
semantic equivalence
```

Deterministic validation shall verify provenance, referenced identities and reconciliation consistency.

Missing, malformed or uncertain semantic evidence shall fail closed against automatic merge authority.

---

### 6. Preserve Human Engineering Authority before project-level reconciliation

Cross-Source Semantic Reconciliation produces review evidence only and has no Engineering Authority.

The existing Human Review, Approved Input and Approved Engineering Information contracts remain the authority boundary for source-derived engineering information. Each participating engineering Source therefore retains its existing source-local path:

```text
Source / Processing Evidence
        ↓
Human Engineering Review
        ↓
Approved Input / Approved Engineering Information
```

Cross-source semantic evidence does not bypass, replace or synthesize the result of that Human Engineering Review.

After source-local Engineering Authority exists, the Multi-Source extension introduces one common project-level Human Engineering Authority boundary. At this boundary, Human reviewers reconcile the relationship between already reviewed source-local authority using the exact Cross-Source Semantic Reconciliation evidence.

The reviewer may determine that reviewed engineering information shall:

```text
remain independent
coexist as valid information concerning the same engineering concern
supersede previously accepted project-level authority
remain unresolved
```

Existing source provenance remains attached to every reviewed result and every project-level authority decision.

The common project-level Human Engineering Authority boundary is an authority boundary, not a requirement to represent all cross-source evidence inside one physical source-bound `ReviewDocument`.

---

### 6a. Project-Level Engineering Authority Reconciliation

The existing Human Review, Approved Input and Approved Engineering Information contracts remain source-bound and shall not be migrated solely to support Multi-Source processing.

Cross-source semantic evidence shall therefore not be forced into a legacy source-bound `ReviewDocument`, and no artificial primary Source shall be assigned to engineering information derived from several independent Sources.

Existing `stable_subject_key` values shall not be interpreted as project-wide cross-source semantic identity unless such continuity has been explicitly established. Equality or inequality of source-local `stable_subject_key` values alone does not establish cross-source Engineering Authority continuity.

After source-local Human Review and Approved Input / Approved Engineering Information projection, a new project-level boundary is introduced:

```text
Source-local Approved Engineering Authority
        +
Cross-Source Semantic Reconciliation Evidence
        ↓
Project Engineering Authority Reconciliation
        ↓
Explicit Human Authority Decision
        ↓
Project Engineering Authority State
```

Project Engineering Authority Reconciliation references existing immutable source-local Approved Inputs / Approved Engineering Information and the exact Cross-Source Semantic Reconciliation evidence. It does not rewrite those artifacts.

The Human reviewer may establish whether reviewed engineering information shall:

```text
remain independent
coexist as valid information concerning the same engineering concern
supersede previously accepted project-level authority
remain unresolved
```

A project-level authority concern or continuity identity may only be established through this explicit Human decision boundary. Machine-generated semantic relationships such as `equivalent`, `complementary`, or `potential_conflict` do not create that identity and do not authorize an authority transition.

Source-local Approved Input lifecycle state and project-level Engineering Authority state are separate concepts. Cross-source reconciliation may therefore determine that an otherwise valid source-local Approved Input is no longer active project-level authority without modifying or deleting its immutable source-local authority record.

Where the existing Approved Input supersession contract can represent an accepted successor without falsifying provenance or continuity, it may be reused. Where its source-local `stable_subject_key` contract is insufficient for genuine cross-source continuity, project-level authority reconciliation remains authoritative and shall not fabricate a matching `stable_subject_key`.

If Human Review determines that the accepted engineering meaning requires a newly synthesized or materially changed engineering statement that is not represented by an existing Approved Input, the reconciliation layer shall not author that statement automatically. The new statement must pass an explicit Human Engineering Review and become new reviewed Engineering Authority before it may affect the model.

The resulting Project Engineering Authority State is the authoritative input to Model Impact Reconciliation in S5.

The phrase "one common Human Engineering Review boundary" denotes a common Human-authority boundary at project level; it does not require all cross-source evidence to be represented by one physical `ReviewDocument`.

### 7. Existing reviewed Engineering Information remains authority when new sources arrive

When additional sources are registered after engineering information has already been reviewed and modeled:

```text
existing active Approved Inputs / AEI
= current Engineering Authority

new source
= new evidence / change candidate
```

A newer source does not automatically supersede existing authority.

Cross-source reconciliation may identify semantic overlap or material variance between new source-derived information and existing active reviewed engineering information.

Human Engineering Review determines whether the accepted authority shall:

```text
remain unchanged
be extended
be replaced/superseded
coexist as separately valid information
remain unresolved
```

Existing Approved Input successor and supersession mechanisms shall be reused wherever compatible.

A changed reviewed successor creates new authority; previous authority is retained immutably and may become `superseded`.

No existing reviewed evidence is rewritten.

---

### 8. Separate Engineering Authority from Model Authority

The existing engineering model is not the primary authority for deciding whether new source information is correct.

Authority order remains:

```text
Human-reviewed Engineering Information
        ↓
Approved Input / AEI
        ↓
Accepted Engineering Model
        ↓
SysML v2 Representation
```

The model represents accepted Engineering Authority.

It does not override new evidence merely because the new evidence differs from the current model.

---

### 9. Introduce Model Impact Reconciliation after Engineering Review

Only after new Engineering Authority has been established may the system compare it with the currently accepted model.

A separate Model Impact Reconciliation boundary shall evaluate the impact of accepted engineering changes on existing model elements.

It may propose:

```text
retain
extend
modify
new
supersede
unresolved
```

Potential model impact shall be derived using:

- active Engineering Authority;
- existing model traceability;
- model classification and placement information;
- existing accepted model structure.

Model Impact Reconciliation is advisory evidence.

It shall not directly mutate the accepted model.

Human Model Review remains authoritative for model changes.

This separation prevents semantically related statements on different engineering abstraction levels from being falsely treated as competing model elements during source processing.

---

### 10. Preserve explicit product evolution and Change Control

When Human Review establishes that newly processed information replaces previously accepted engineering information:

```text
old reviewed authority
        ↓
superseded by
        ↓
new reviewed authority
```

the change shall remain explicitly traceable.

Corresponding model changes shall be represented as a subsequent accepted model state rather than rewriting historical authority or historical model evidence.

The architecture therefore supports product evolution without using document age as automatic truth.

---

## Consequences

### Positive

- Genuine Multi-Source processing becomes possible without rewriting source-level Processing.
- Sources accidentally registered in the wrong Project can be detected before project-level semantic integration.
- Context-only documents obtain a clear architectural role in establishing product understanding.
- Complementary information is preserved instead of being falsely treated as conflict.
- Cross-source conflicts remain explicit and provenance-preserving.
- Existing reviewed information remains authoritative until Human-controlled change.
- Existing Approved Input supersession mechanisms can support auditable Change Control.
- Model updates become consequences of reviewed engineering change rather than direct consequences of LLM output.
- Existing Single-Source behavior remains valid.
- No migration of persisted `ProcessingArtifactReference` contracts is required.

### Negative / Cost

- Multi-Source processing requires additional LLM-assisted reasoning boundaries.
- A project-level reconciliation contract and Human Review bridge must be introduced.
- Incremental source ingestion must consider existing active Engineering Authority.
- Model impact analysis adds an additional reasoning step before model update.
- More explicit provenance and lifecycle state must be retained across boundaries.

These costs are accepted because collapsing Source Fit, semantic reconciliation, Engineering Authority and Model Change into one step would create unsafe hidden authority and unreliable model evolution.

---

## Affected Components

Existing components retained:

```text
modules/project_sources/
modules/project_processing/
modules/source_evidence/
modules/engineering_subjects/
modules/subject_interpretation/
modules/subject_consensus/
modules/human_review/
modules/review_workspace/
modules/approved_input/
Approved Engineering Information projection
Model Candidate / Placement processing
Internal Engineering Model
SysML v2 generation
SYSIDE validation
Final Human Release
```

New or extended responsibilities are expected around:

```text
project-fit assessment
project-level cross-source semantic reconciliation
multi-source Human Review projection / bridge
engineering-authority continuity
model-impact reconciliation
```

Existing immutable Project `000116` Gate-3 evidence shall not be modified or regenerated by this work.

---

## Supersedes

None.

This ADR extends, but does not supersede:

```text
ADR-012 Processing State and Artifact Organization
ADR-016 Human Review Workspace and Approved Input Promotion Architecture
ADR-025 Semantic Proposal Consolidation and Persona-Aware Consensus
ADR-026 Source-Anchored Multi-Persona Interpretation and Cross-Unit Semantic Synthesis
ADR-029 Human-Reviewed Model Placement Before Model Assembly
ADR-023 Final Model Review and Output Publication Architecture
```

Where this ADR introduces project-level behavior, the existing source-level contracts remain valid.

---

## Related Roadmap Phase

```text
BLK-002 — Cross-Source Processing Artifact Identity Collision
WP-12 Multi-Source Acceptance
30-Day Thesis Completion Track A
Multi-Source → Safe Demo
```

---

## Related Implementation

Implementation is divided into bounded, independently testable slices.

### S1 — Contextual Processing Artifact Identity

At project-wide lifecycle and aggregation boundaries:

```text
(processing_run_id, artifact_type, artifact_id)
```

becomes effective identity.

No persisted Processing Artifact schema change.

### S2 — Project Fit / Source Admissibility

Introduce the Project Fit Assessment and its Human escalation boundary.

### S3 — Project-Level Cross-Source Semantic Reconciliation

Introduce provenance-preserving:

```text
equivalent
complementary
potential_conflict
distinct
uncertain
```

classification.

### S4 — Project-Level Engineering Authority Reconciliation

Connect source-local Approved Input / AEI authority and Cross-Source Semantic Reconciliation evidence to the explicit project-level Human Authority Decision defined by Sections 6 and 6a, without migrating or falsifying source-bound Review / Approved Input / AEI provenance.

### S5 — Model Impact Reconciliation

Compare newly accepted Engineering Authority with the existing accepted model and produce reviewable model-impact proposals.

Each implementation slice requires focused tests.

Before final acceptance:

```text
focused slice tests
full repository regression
git diff --check
real heterogeneous Multi-Source E2E
downstream deterministic SysML v2 generation
real SYSIDE validation
Final Human Release
SSOT update
```
