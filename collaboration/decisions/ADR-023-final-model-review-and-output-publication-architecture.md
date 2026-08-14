# ADR-023 — Final Model Review and Output Publication Architecture

## Status

Accepted

## Date

2026-08-14

## Context

Phase J and Phase K are completed and provide an explicit generated-model and
validation boundary:

```text
Internal Engineering Model
→ Phase J — deterministic SysML v2 generation
→ GeneratedSysMLArtifactSet
→ Phase K — deterministic + external validation
→ SysMLValidationResult
```

Phase J produces concrete `.sysml` units together with deterministic generation
identity, fingerprints and machine-readable traceability.

Phase K validates the exact generated artifact without modifying it. It produces
an immutable `SysMLValidationResult` with the normative states:

```text
valid
invalid
incomplete
```

and the publication gate:

```text
passed
blocked
```

ADR-022 already defines the exact fingerprint-bound K→L publication condition
and Phase K implements:

```python
validate_phase_l_handoff(
    artifact_set: GeneratedSysMLArtifactSet,
    validation_result: SysMLValidationResult,
) -> None
```

That gate correctly prevents publication unless the validation result:

- belongs to the same Project,
- belongs to the same source IEM,
- covers the exact generated artifact fingerprint,
- has `validation_status == "valid"`,
- and has `publication_gate == "passed"`.

However, automated validation alone does not constitute final engineering
release authority.

The generated SysML v2 is the first point in the workflow where a human can
inspect the complete resulting model representation as:

- generated SysML v2 code,
- structural/model diagrams,
- generated relationships,
- validation findings,
- traceability,
- upstream model-candidate evidence,
- generation rationales,
- and available agent/personality proposals.

A final Human-in-the-Loop review is therefore required before generated output
becomes an authoritative published project output.

The user shall be able to:

- inspect the generated model directly in the UI,
- inspect the exact generated `.sysml` code,
- inspect a diagrammatic model projection,
- navigate between model elements and generated code,
- inspect validation findings and their locations,
- inspect upstream agent/personality proposals and rationales where available,
- accept or reject the generated result,
- request changes,
- propose changes through code or diagram interaction,
- provide structured feedback,
- optionally request another bounded LLM/agent proposal loop,
- and explicitly approve one exact reviewed revision for final publication.

Generated-but-not-approved model results must therefore be persisted as
project-local review evidence before final publication.

Only after explicit Human approval may an output become a final versioned
project result under `data/output/`.

This ADR refines the original Phase-L concept from a pure "Output Writer" into
a controlled:

```text
Final Model Review
+
Human Release Gate
+
Output Publication
```

architecture.

---

## Decision

### L-01 — Phase-L responsibility

Phase L owns the final model review and controlled publication boundary.

The accepted end-to-end flow is:

```text
Approved Input
→ Model Candidates
→ Candidate Human Review
→ Internal Engineering Model
→ deterministic SysML v2 generation
→ automated validation
→ Final Model Human Review
→ explicit Human release approval
→ immutable versioned publication
```

Phase L shall not replace or weaken the earlier Human Review gate in Phase H.

The two review gates have different purposes:

```text
Phase H
candidate-level engineering approval
before authoritative Internal Engineering Model assembly

Phase L
complete generated-model review and release approval
before final project publication
```

Both are required.

---

### L-02 — Review entry is distinct from publication eligibility

A Phase-L review workspace may be created for an exact:

```text
GeneratedSysMLArtifactSet
+
SysMLValidationResult
```

even when the K result is:

```text
invalid / blocked
```

or:

```text
incomplete / blocked
```

This is intentional because validation findings are useful Human Review
evidence and may drive a correction loop.

Review entry shall still require exact integrity and binding:

- artifact-set integrity,
- validation-result integrity,
- same Project,
- same source IEM,
- exact artifact-set fingerprint binding.

The existing:

```python
validate_phase_l_handoff(...)
```

remains the normative **final publication gate**.

It shall not be weakened merely to allow review of invalid or incomplete
results.

A separate Phase-L review-subject boundary may validate exact subject binding
without requiring `valid + passed`.

---

### L-03 — Generated-but-not-approved output is review evidence, not published output

Generated `.sysml` files that have not received final Human release approval
shall not be treated as final published model output.

They shall be persisted in a project-local Final Model Review workspace.

Conceptually:

```text
data/projects/<project_id>/
└── final_model_reviews/
    └── FMR-000001/
        ├── manifest.json
        ├── revisions/
        │   ├── FRV-000001/
        │   └── FRV-000002/
        └── decisions/
```

These artifacts are:

- project-bound,
- inspectable,
- immutable once a review revision is created,
- traceable,
- and non-authoritative for final publication.

The legacy global principle:

```text
generated SysML v2 output → data/output/
```

is refined as follows:

```text
generated SysML under review
→ project-local Final Model Review workspace

Human-approved published SysML
→ data/output/<project_id>/OUT-xxxxxx/
```

This refinement preserves `data/output/` as the location of final generated
output while preventing unreleased drafts from being mistaken for published
project results.

---

### L-04 — Stable project-local Final Model Review identities

Phase L shall introduce explicit project-local identities using the established
six-digit identifier policy.

Initial identity families are:

```text
FMR-000001  Final Model Review
FRV-000001  Final Model Review Revision
FRI-000001  Final Model Review Item
FRD-000001  Final Model Review Decision
OUT-000001  Published Output Package
```

Identifiers are:

- project-local,
- monotonically increasing,
- immutable,
- never gap-reused after publication/persistence,
- and independent from display names.

Exact identifier modules and allocation mechanics belong to implementation but
shall follow the existing repository-wide deterministic identifier pattern.

---

### L-05 — Immutable review revisions

A Final Model Review is a long-lived review container.

Each concrete review subject is an immutable Final Model Review Revision.

One revision binds exactly:

- Project ID,
- source IEM ID,
- `GeneratedSysMLArtifactSet.content_fingerprint`,
- `SysMLValidationResult.content_fingerprint`,
- generated units and their fingerprints,
- generation-policy references,
- Validation Profile reference,
- validation status and publication gate,
- traceability references,
- applicable upstream Candidate/Review evidence references,
- applicable agent/personality proposal evidence,
- and the deterministic review-view fingerprint.

A revision shall never be edited in place.

If generated content or validation evidence changes, a new revision is created.

Conceptually:

```text
FMR-000001
├── FRV-000001  generated + reviewed, changes requested
├── FRV-000002  regenerated + revalidated, changes requested
└── FRV-000003  regenerated + revalidated, approved
```

Earlier revisions remain immutable evidence.

---

### L-06 — Final Model Review UI projection

Phase L shall provide a deterministic non-authoritative review projection for
the focused UI.

Conceptually:

```python
FinalModelReviewView
```

It shall present at least:

- review identity and revision,
- current review state,
- model summary,
- diagrammatic structural view,
- exact generated SysML v2 code,
- generated-unit selection where multiple units exist,
- generated symbols,
- relationship views,
- validation status,
- blocking findings,
- warnings,
- traceability,
- upstream Candidate decisions,
- generation rationale,
- available agent/personality proposals,
- unresolved review items,
- required Human decisions,
- and the next action.

The view is a projection over immutable evidence.

It shall not itself become engineering or publication authority.

---

### L-07 — Diagram and SysML code are linked review surfaces

The UI shall support both:

```text
diagram / model view
```

and:

```text
exact generated `.sysml` code
```

as first-class review surfaces.

Where possible, selection shall be cross-linked through existing generated
identity and traceability:

```text
diagram element / relationship
→ generated_symbol_id
→ GeneratedSysMLTraceabilityEntry
→ generated unit + line location
→ exact SysML code
```

and conversely:

```text
generated code location
→ generated symbol
→ model element / relationship
→ upstream traceability
```

The UI shall not reconstruct engineering authority by reverse-parsing the
generated SysML.

Diagrammatic views shall preferentially use the authoritative upstream model
structure and existing traceability while the code view displays the exact
Phase-J output.

---

### L-08 — Direct UI edits create change proposals, not silent authoritative mutations

The user may interactively modify or annotate:

- generated SysML code,
- diagram relationships,
- model structure,
- attributes represented in the review UI,
- and review comments.

However, an edit shall not silently mutate:

- the source IEM,
- the existing `GeneratedSysMLArtifactSet`,
- the existing `SysMLValidationResult`,
- or a published output.

A UI edit shall create explicit review evidence such as a change proposal or
structured change request bound to the current review revision.

For code editing, the UI may provide an editor experience conceptually similar
to:

```text
edit generated_model.sysml
→ inspect diff
→ save as change proposal
```

The saved proposal shall preserve at least:

- exact base artifact fingerprint,
- affected unit,
- affected generated symbols where resolvable,
- original content or location reference,
- proposed content/diff,
- reviewer identity,
- reviewer rationale,
- and change classification.

A proposed edit is not publishable generated output.

---

### L-09 — Change requests are routed to the owning authority boundary

Phase L shall not use manual final-code editing to bypass the Internal
Engineering Model.

A requested change shall be classified by its likely resolution boundary.

At minimum:

```text
engineering_semantics
→ Phase H / Candidate Review / IEM revision path

generated_representation
→ Phase J generation policy / generator correction

validation_policy_or_tool
→ Phase K validation policy / validator correction

review_presentation_only
→ Phase-L UI/read-model correction without changing model authority
```

Examples:

```text
"Function A belongs to another Logical Component."
→ engineering_semantics

"The correct accepted relationship should be satisfaction, not allocation."
→ engineering_semantics

"The model is correct but the generator emitted the wrong target syntax."
→ generated_representation

"SYSIDE rejects a construct that the Turing validator considered valid."
→ generation / Target Notation / validation investigation

"The diagram label is misleading but the underlying model is correct."
→ review_presentation_only
```

The correction shall occur at the owning layer and then re-enter the downstream
pipeline.

Phase L shall not invent a hidden third engineering authority in edited SysML
text.

---

### L-10 — Optional bounded LLM/agent revision loop

A Human reviewer may request another agent/LLM-assisted model proposal cycle
from Final Model Review.

The request shall be explicit and shall preserve the Human feedback that
triggered it.

Conceptually:

```text
Final Model Review
→ Human change request / feedback
→ optional bounded agent/LLM re-proposal
→ proposed Candidate changes / alternatives
→ existing Candidate Human Review
→ new authoritative IEM
→ deterministic J generation
→ K validation
→ new Final Model Review Revision
```

LLM or agent execution may:

- propose alternative model elements,
- propose alternative relationships,
- explain tradeoffs,
- identify gaps,
- compare candidate structures,
- and respond to reviewer feedback.

It shall not:

- directly rewrite final published SysML,
- approve its own proposals,
- bypass Candidate Human Review,
- bypass IEM assembly,
- bypass deterministic Phase J,
- bypass Phase K,
- or create final release authority.

The normative chain remains:

```text
agent/LLM proposal
→ Human decision
→ authoritative model state
→ deterministic generation
→ validation
→ final Human release approval
```

---

### L-11 — Agent/personality evidence is visible but non-authoritative

Final Model Review shall surface available proposal evidence from different
agent roles or modeling personalities where such evidence exists.

The review projection should preserve, where available:

- agent/personality identity,
- proposal,
- rationale,
- confidence/support information,
- alternatives,
- semantic uncertainty,
- source evidence,
- generation provenance,
- and prior Human decision.

The UI may present multiple perspectives side by side.

Example:

```text
Current accepted model relation:
allocated_to

Systems Engineer perspective:
allocated_to
rationale: ...

Architecture Reviewer perspective:
dependency
rationale: ...

Human options:
keep current
request change
request another proposal cycle
inspect upstream evidence
```

Selecting or favoring an alternative does not directly modify the final model.

It creates or contributes to a Human-reviewed upstream change request.

Agent agreement shall remain review evidence, not approval authority.

---

### L-12 — Every material revision must be regenerated and revalidated

Any material change affecting engineering content or generated SysML requires a
new downstream artifact chain.

The required loop is:

```text
change accepted at owning authority boundary
→ new/updated authoritative model state
→ deterministic Phase-J generation
→ new GeneratedSysMLArtifactSet fingerprint
→ Phase-K validation
→ new SysMLValidationResult fingerprint
→ new Final Model Review Revision
```

A prior K result never authorizes changed content.

A prior Final Model Review approval never authorizes changed content.

No "validation carry-over" is permitted across a changed artifact fingerprint.

---

### L-13 — Final Human release approval is mandatory

Final publication requires an explicit immutable Human decision bound to one
exact Final Model Review Revision.

Conceptually:

```python
FinalModelReviewDecision(
    final_model_review_id=...,
    final_model_review_revision_id=...,
    decision="approved_for_publication",
    generated_artifact_set_fingerprint=...,
    validation_result_fingerprint=...,
    reviewer_identity=...,
    rationale=...,
    content_fingerprint=...,
)
```

Final approval shall be possible only if:

- the review revision is internally complete,
- the exact artifact-set integrity is valid,
- the exact validation-result integrity is valid,
- `validation_status == "valid"`,
- `publication_gate == "passed"`,
- the validation result covers the exact artifact-set fingerprint,
- no mandatory review item remains unresolved,
- no accepted change request is waiting for regeneration,
- and the reviewer explicitly approves the revision for publication.

Final release approval is a Human authority action.

It shall not be inferred from:

- absence of findings,
- agent consensus,
- LLM confidence,
- SYSIDE success alone,
- UI navigation state,
- or elapsed time.

---

### L-14 — Final approval becomes stale on any subject change

A Final Model Review Decision is valid only for the exact fingerprints it
authorizes.

If any of the following changes:

- generated unit content,
- artifact-set fingerprint,
- validation-result fingerprint,
- required validation evidence,
- review revision subject,
- or an approval-relevant policy reference,

the previous approval shall not authorize publication of the changed result.

No post-approval content mutation is permitted.

---

### L-15 — Final publication service boundary

Only after successful automated validation and explicit Human release approval
may publication occur.

The Phase-L publication service boundary becomes conceptually:

```python
OutputWriter.publish(
    artifact_set: GeneratedSysMLArtifactSet,
    validation_result: SysMLValidationResult,
    final_review_decision: FinalModelReviewDecision,
) -> PublishedOutputPackage
```

Before writing any final output, the service shall:

1. validate artifact-set integrity,
2. validate validation-result integrity,
3. execute the existing `validate_phase_l_handoff(...)`,
4. validate Final Model Review Decision integrity,
5. confirm exact Project binding,
6. confirm exact review-revision binding,
7. confirm exact artifact-set fingerprint binding,
8. confirm exact validation-result fingerprint binding,
9. require `approved_for_publication`,
10. and reject stale or mismatched Human approval.

Phase L shall never implicitly select:

- latest artifact,
- latest validation result,
- latest review revision,
- or latest Human decision.

All publication inputs are explicit.

---

### L-16 — Final output location

Final Human-approved output shall be published under:

```text
data/output/<project_id>/<output_package_id>/
```

Example:

```text
data/output/
└── 000001/
    └── OUT-000001/
        ├── manifest.json
        ├── generated_model.sysml
        ├── generation_summary.json
        ├── validation_result.json
        ├── validation_report.md
        └── traceability.json
```

If Phase J later produces multiple generated units, their configured relative
paths shall be preserved within the output package.

Only final approved packages belong in this publication namespace.

---

### L-17 — Published output identity and version model

Final outputs use project-local immutable sequential IDs:

```text
OUT-000001
OUT-000002
OUT-000003
```

The OUT sequence represents publication identity and ordering.

It is not semantic versioning.

A later OUT ID does not inherently mean a semantic major/minor/patch change.

Engineering and validation identity remains fingerprint-based.

OUT IDs shall be:

- project-local,
- sequential,
- immutable,
- never reused,
- and stable after publication.

---

### L-18 — Versioned Output Publication Profile

Phase L shall introduce a small versioned publication policy artifact:

```text
context/sysml/turing_sysml_v2_output_profile.json
```

Initial identity:

```text
profile_id:      TURING_SYSML_V2_OUTPUT
profile_version: 1.0.0
```

The Output Profile shall define publication concerns only, including:

- output root,
- required package file roles,
- unit placement rules,
- manifest schema expectations,
- fingerprint policy,
- idempotence policy,
- and derived archive/download policy.

It shall not redefine:

- engineering semantics,
- Candidate Review rules,
- IEM assembly,
- Target Notation,
- Generation Profile mappings,
- validation semantics,
- or Human release authority.

Human approval remains an architectural gate, not a configurable bypass.

---

### L-19 — Authoritative published package contents

The MVP authoritative output package shall contain at least:

```text
manifest.json
<all GeneratedSysMLUnit relative paths>
generation_summary.json
validation_result.json
validation_report.md
traceability.json
```

#### Generated SysML units

Published `.sysml` units shall be byte-for-byte identical to the exact
Human-approved `GeneratedSysMLArtifactSet`.

Phase L shall not:

- reformat,
- rewrite,
- normalize,
- reorder,
- rename,
- repair,
- or regenerate

the SysML content during publication.

#### validation_result.json

This is the machine-readable authoritative Phase-K validation evidence.

#### validation_report.md

This is a deterministic Human-readable projection of the validation result.

It is not independent validation authority.

#### traceability.json

This preserves the generated-output traceability needed to navigate from final
output back through:

```text
generated symbol / location
→ IEM element or relationship
→ Model Candidate
→ Approved Input
→ Human Review Decision
→ accepted exception where applicable
```

#### generation_summary.json

This records deterministic generation context and provenance required to
understand the published artifact, without creating new engineering semantics.

#### manifest.json

This is the authoritative package index and integrity boundary.

---

### L-20 — Published output manifest

Conceptually:

```python
PublishedOutputManifest(
    schema_version=...,
    project_id=...,
    output_package_id=...,
    source_internal_engineering_model_id=...,
    source_artifact_set_fingerprint=...,
    validation_result_fingerprint=...,
    final_model_review_id=...,
    final_model_review_revision_id=...,
    final_review_decision_id=...,
    final_review_decision_fingerprint=...,
    output_profile_reference=...,
    publication_input_fingerprint=...,
    files=(...),
    content_fingerprint=...,
)
```

Every persisted package file shall have:

- relative path,
- controlled file role,
- content fingerprint,
- and source/generated reference where applicable.

The complete output package shall have one deterministic content fingerprint.

---

### L-21 — Publication input fingerprint and idempotence

Phase L shall calculate a deterministic publication-input fingerprint covering
at least:

- exact `GeneratedSysMLArtifactSet.content_fingerprint`,
- exact `SysMLValidationResult.content_fingerprint`,
- exact Final Model Review Decision fingerprint,
- exact Final Model Review Revision fingerprint,
- exact Output Profile reference and fingerprint.

Conceptually:

```text
publication_input_fingerprint =
SHA256(
    artifact-set identity
  + validation identity
  + Human release identity
  + publication policy identity
)
```

Publishing the exact same authorized input repeatedly shall return the same
existing published output package rather than allocate new OUT IDs.

Example:

```text
same exact authorized publication input
→ OUT-000001

same exact authorized publication input again
→ OUT-000001
```

A materially different approved publication input receives a new OUT ID.

---

### L-22 — Atomic immutable publication

Final publication shall be fail-closed and atomic.

Conceptually:

```text
allocate OUT-000001
→ create hidden temporary package
→ write all files
→ verify file fingerprints
→ verify manifest
→ verify complete package integrity
→ atomic rename
→ OUT-000001 becomes visible
```

A visible final output directory shall always represent a complete validated
publication.

Interrupted or incomplete temporary publication state shall never be treated as
a valid published output.

---

### L-23 — Recovery and integrity scanning

The Output Repository shall detect at least:

- incomplete temporary publication directories,
- malformed OUT identities,
- missing manifest,
- missing required files,
- unexpected files where prohibited by profile,
- file fingerprint mismatch,
- manifest fingerprint mismatch,
- unsafe paths,
- symlink/path escape,
- duplicate publication-input fingerprints,
- and project/OUT identity mismatch.

Recovery diagnostics shall be explicit and fail-closed.

Interrupted publication evidence shall not be silently deleted during normal
reads.

---

### L-24 — Directory package is publication authority; archive is derived

The authoritative final output is the immutable directory package plus its
manifest.

A ZIP or other archive may be produced for download convenience.

Such an archive is a derived transport representation.

It shall not replace the directory package as publication authority.

Archive metadata such as timestamps or compression differences shall not alter
the identity of the authoritative publication.

---

### L-25 — Final project-output association occurs only after approval and publication

Final Model Review artifacts are project-local review evidence but shall not be
listed as released project outputs.

Only successfully published:

```text
OUT-xxxxxx
```

packages become final project outputs.

The Project Dashboard / Guided Workflow UI shall distinguish at least:

```text
Generated / under review
Changes requested
Validation blocked
Ready for Human approval
Approved for publication
Published
```

A generated model shall not appear as a final project model merely because J or
K completed successfully.

---

### L-26 — Read boundary for UI and downstream presentation

Publication persistence shall expose explicit read services conceptually like:

```python
OutputRepository.list_outputs(
    project_id,
) -> tuple[PublishedOutputManifest, ...]
```

and:

```python
OutputRepository.load_output(
    project_id,
    output_package_id,
) -> PublishedOutputPackage
```

Final Model Review shall expose separate project-bound review read services.

The later Guided Workflow UI shall consume these read boundaries.

The UI shall not infer publication authority directly from filesystem presence
or session state.

---

### L-27 — SYSIDE unavailability blocks approval/publication, not review

The current verification workstation may not have the SYSIDE CLI available.

This does not prevent:

- Phase-L architecture,
- review-workspace implementation,
- review UI implementation,
- review of generated code,
- review of diagrams,
- review of agent proposals,
- change requests,
- or deterministic unit testing.

It does prevent final Human release approval and final publication of a real
model because the required K state cannot become:

```text
valid / passed
```

without required external validation.

An `incomplete / blocked` result may be reviewed, but shall not be approved for
publication.

---

### L-28 — Human authority is not delegated to LLMs or agents

No LLM or agent is normative final release authority.

Agents may support:

- proposal generation,
- alternative generation,
- completeness review,
- relationship analysis,
- rationale generation,
- and response to Human feedback.

Only an explicit Human decision may authorize final publication.

The final gate is therefore:

```text
automated validation PASS
+
explicit Human release approval
=
eligible for publication
```

not:

```text
agent consensus
=
publication
```

---

### L-29 — Complete revision loop

The normative Phase-L correction loop is:

```text
J GeneratedSysMLArtifactSet
        ↓
K SysMLValidationResult
        ↓
Final Model Review Revision
        ↓
Human inspection:
  diagram
  code
  validation
  traceability
  agent/personality evidence
        ↓
        ├── approve
        │      ↓
        │   Human release decision
        │      ↓
        │   OutputWriter.publish(...)
        │      ↓
        │   OUT-xxxxxx
        │
        └── request changes
               ↓
            explicit change proposal
               ↓
            owning authority boundary
               ↓
        optional bounded LLM/agent proposal
               ↓
            Human review/acceptance
               ↓
          new authoritative model state
               ↓
        deterministic regeneration
               ↓
             validation
               ↓
       new Final Model Review Revision
```

Every loop iteration remains traceable.

---

### L-30 — Non-goals and prohibited shortcuts

Phase L shall not:

- treat generated SysML as final before Human release approval,
- mutate a prior immutable review revision,
- silently change validated generated content,
- publish `invalid` or `incomplete` results,
- publish without exact K fingerprint binding,
- publish without exact Human approval binding,
- use manually edited final SysML as a second engineering authority,
- let an LLM directly rewrite and publish final output,
- bypass Candidate Human Review for semantic changes,
- bypass IEM assembly,
- bypass deterministic Phase-J generation,
- carry old validation across changed content,
- carry old Human approval across changed content,
- infer publication from "latest" artifacts,
- or collapse review evidence and final published output into one storage state.

---

## Final Model Review state model

The initial controlled review lifecycle shall support at least:

```text
generated
validation_blocked
review_pending
changes_requested
regeneration_required
ready_for_approval
approved_for_publication
published
```

These are workflow/read-model states.

Normative authority remains in immutable artifacts and Human decisions rather
than in a mutable status string alone.

A review is `ready_for_approval` only when the exact review revision has:

- complete subject integrity,
- `valid / passed` K evidence,
- no unresolved mandatory review items,
- and no outstanding accepted change request.

---

## Publication package authority chain

A final published package shall be able to prove:

```text
OUT-xxxxxx
→ PublishedOutputManifest
→ exact Final Model Review Decision
→ exact Final Model Review Revision
→ exact SysMLValidationResult
→ exact GeneratedSysMLArtifactSet
→ exact IEM
→ reviewed Model Candidates
→ Approved Input
→ Human Review evidence
```

This chain is required for auditability and for later Project Dashboard /
Guided Workflow presentation.

---

## UI interaction principle

The established interaction principle remains:

```text
Simple by default.
Explainable on demand.
Fully traceable underneath.
```

The default Final Model Review UI should emphasize:

1. what model was generated,
2. whether automated validation passed,
3. what requires Human attention,
4. relevant alternative proposals,
5. the current diagram/model structure,
6. the exact SysML code on demand,
7. and the next Human action.

Detailed IDs, fingerprints, policy references, evidence chains and diagnostics
remain available through progressive disclosure.

The UI shall support direct review interaction without weakening the immutable
authority model underneath.

---

## Implementation decomposition

Phase L shall be implemented in the following controlled slices.

### L1 — Final Model Review domain foundation

- identifiers,
- immutable review/revision/item/decision types,
- validation,
- fingerprints,
- lifecycle vocabulary.

### L2 — Final Model Review repository

- project-local review workspace,
- immutable revisions,
- decision persistence,
- safe paths,
- integrity,
- scanning,
- recovery.

### L3 — Final Model Review read model and UI projection

- deterministic `FinalModelReviewView`,
- diagram/model projection,
- exact SysML code projection,
- validation findings,
- traceability,
- upstream Candidate evidence,
- agent/personality proposal evidence,
- required decisions,
- next action.

### L4 — Change proposal and revision loop

- code-edit proposals,
- diagram/model change proposals,
- structured Human feedback,
- change classification,
- owning-boundary routing,
- optional bounded LLM/agent re-proposal,
- regeneration/revalidation handoff,
- successor review revision creation.

### L5 — Final Human release gate

- exact revision binding,
- exact artifact fingerprint binding,
- exact validation fingerprint binding,
- unresolved-item checks,
- `approved_for_publication`,
- stale approval rejection.

### L6 — Output publication repository and OutputWriter

- Output Profile,
- OUT identity,
- deterministic package projections,
- publication-input fingerprint,
- idempotence,
- atomic publication,
- bundle integrity,
- read service,
- derived download/archive support.

### L7 — End-to-end integration and acceptance

- J→K→Final Review→Publication integration,
- real SYSIDE validation environment,
- real `valid / passed` result,
- Human Review acceptance,
- real `OUT-000001` publication,
- review/change loop evidence,
- focused regression,
- complete repository regression,
- `git diff --check`,
- manual acceptance,
- SSOT closeout.

No implementation slice may weaken the Human Review, fingerprint, project
isolation, deterministic generation, validation or publication boundaries
defined by this ADR.

---

## Consequences

### Positive

- the final generated model receives an explicit Human release gate,
- Human Review can evaluate the actual generated `.sysml` result rather than
  only upstream abstract Candidates,
- validation results become visible review evidence,
- generated code and model diagrams can be reviewed together,
- agent/personality alternatives remain visible and comparable,
- Human feedback can trigger controlled revision loops,
- LLM assistance remains useful without becoming authority,
- direct UI editing remains possible without creating a hidden engineering
  source of truth,
- every revision remains auditable,
- final output is clearly separated from generated-but-unreleased work,
- only fully validated and explicitly approved results enter `data/output/`,
- and the final Project output can be traced through the complete engineering
  workflow.

### Tradeoffs

- Phase L becomes larger than a simple filesystem Output Writer,
- corrections may require returning to earlier phases rather than patching final
  code directly,
- every material revision requires regeneration and validation,
- the UI needs clear distinction between proposed edits and authoritative
  changes,
- and a live external validator remains necessary before real publication.

These costs are accepted because they preserve engineering authority,
traceability and Human control.

---

## Relationship to prior ADRs

This ADR complements and does not replace:

- ADR-016 — Human Review Workspace and Approved Input Promotion Architecture,
- ADR-017 — Simple-by-Default Interaction and Progressive Disclosure,
- ADR-018 — Model Candidate Layer and Structural Comparability,
- ADR-019 — Internal Engineering Model Assembly Architecture,
- ADR-020 — Hybrid Target Projection and Coverage Architecture,
- ADR-021 — SYSIDE-Compatible SysML v2 Generation Architecture,
- ADR-022 — SysML v2 Validation Layer Architecture.

ADR-022 K-21 remains normative for final publication.

This ADR clarifies that the K→L `valid + passed` gate is a **publication gate**,
not a prohibition against reviewing invalid or incomplete generated models.

This ADR also refines the previous workspace rule for generated SysML:

```text
review-stage generated SysML
→ project-local Final Model Review workspace

final Human-approved generated SysML
→ data/output/
```

CATIA remains authoritative for Turing Generator engineering knowledge and is
not replaced by generated project output.

---

## Decision summary

The accepted final prototype path is:

```text
Source
→ Processing Run
→ Human Review
→ Approved Input
→ Model Candidates
→ Candidate Human Review
→ Internal Engineering Model
→ deterministic SysML v2 generation
→ automated validation
→ Final Model Human Review
→ optional controlled revision / LLM-agent loop
→ explicit Human release approval
→ immutable versioned Published Output Package
```

The core release rule is:

```text
Generated
≠ Final

Validated
≠ Final

Human-approved exact validated revision
= eligible for final publication
```

Phase L shall implement this rule without weakening the established deterministic
generation, validation, traceability or Human Review architecture.
