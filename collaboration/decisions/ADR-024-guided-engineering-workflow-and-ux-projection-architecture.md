# ADR-024 — Guided Engineering Workflow and UX Projection Architecture

## Status

Accepted

## Date

2026-08-16

## Context

The Turing Generator has reached a functionally complete prototype baseline through
Phase L.

Baseline implementation reference:

```text
0fce9928a04e047e4b39484b421632fb64ed905f
Complete Phase L final model review and output publication
```

At this baseline, the implemented workflow covers:

```text
Source
→ Processing
→ Human Review
→ Approved Input
→ Model Candidates
→ Candidate Human Review
→ Internal Engineering Model
→ SysML v2 Generation
→ Validation
→ Final Model Human Review
→ Human Release Approval
→ Published Output
```

The technical architecture provides immutable evidence, explicit Human authority,
deterministic read models, validation gates and end-to-end traceability.

However, formative usability evaluation of the functional prototype showed that
the existing user interface remains too strongly oriented around technical
artifacts, workflow metadata and implementation structure.

The functionality is available, but the engineer has to spend unnecessary effort
finding:

- what engineering information was ingested,
- which processing result is relevant,
- where Human action is required,
- where multiple Agent / Persona results agree,
- where they differ,
- which alternatives are available,
- why an Agent proposed a result,
- and what the next engineering decision should be.

The issue is therefore not missing processing capability.

The issue is the mapping between the implemented processing architecture and the
daily engineering task.

This ADR defines the UX architecture for WP-09 through WP-12.

---

## Decision

### UX-01 — Engineer-centered interaction

The primary UI shall be organized around the engineer's work rather than the
internal implementation structure.

The default questions answered by the UI are:

```text
What was provided?
What did the system derive?
Do the independent perspectives agree?
Where do I need to decide?
What happens next?
```

Technical metadata shall remain available but shall not dominate the primary
working surface.

---

### UX-02 — Guided Workflow is a projection, not authority

The Guided Engineering Workflow shall not create another authoritative workflow
state machine.

It is a deterministic projection of existing persisted authoritative state.

Conceptually:

```text
authoritative repositories / read services
                ↓
      GuidedWorkflowReadService
                ↓
        GuidedWorkflowView
                ↓
             Streamlit
```

The UI may maintain transient navigation state.

It shall not duplicate engineering, review, validation, release or publication
authority inside Streamlit session state.

---

### UX-03 — Engineering Content before Metadata

Primary views shall present engineering content first.

Examples include:

- source content,
- extracted engineering statements,
- proposed elements,
- proposed relationships,
- engineering classifications,
- model structure,
- validation findings,
- generated SysML.

Implementation metadata such as:

- internal IDs,
- hashes,
- fingerprints,
- artifact paths,
- processing-run identifiers,
- manifest versions,

shall remain available through progressive disclosure for traceability and audit.

The intended hierarchy is:

```text
Primary layer
→ What is this?

Decision layer
→ What do I need to decide?

Explanation layer
→ Why was this proposed?

Traceability layer
→ Where exactly did it come from?
```

---

### UX-04 — Decision-Centered Interaction

Open Human decisions are first-class UI objects.

The Guided Workflow shall prioritize:

```text
action required
→ relevant engineering content
→ alternatives
→ supporting rationale
→ Human decision
```

The engineer shall not have to inspect technical processing state to discover
that a decision is required.

The project entry view should therefore prioritize work such as:

```text
Your work

4 decisions required
2 results contain relevant variance
11 results are confirmed / ready

Next action
→ Review extracted engineering information
```

The exact counts are derived from authoritative persisted state.

---

### UX-05 — Variance is first-class engineering information

Whenever a processing step contains redundant LLM / Agent / Persona execution,
the UI shall expose the resulting variance explicitly.

Existing consensus concepts shall be reused.

Examples include:

```text
unanimous
majority
single
none
incomparable
incomplete
```

and:

```text
low
medium
high
```

variance.

Persona stability and incomplete Agent evidence shall remain distinguishable from
inter-Persona disagreement.

Repeated executions of one Persona shall not be presented as additional
independent votes.

---

### UX-06 — Side-by-Side before Aggregation

When multiple Agent / Persona results exist for the same engineering subject,
the preferred presentation is side-by-side comparison.

Conceptually:

```text
┌────────────────┬────────────────┬────────────────┐
│ Persona A      │ Persona B      │ Persona C      │
│                │                │                │
│ Proposal A     │ Proposal A     │ Proposal B     │
│ rationale ▾    │ rationale ▾    │ rationale ▾    │
└────────────────┴────────────────┴────────────────┘

2 / 3 → Proposal A
1 / 3 → Proposal B

Human decision required
```

Consensus summaries complement this comparison.

They shall not hide the individual Agent / Persona results.

---

### UX-07 — Visual consensus language

Agreement and variance shall be visually recognizable at a glance.

The semantic presentation shall follow:

```text
GREEN
unanimous / low variance

AMBER
majority / medium variance

RED
high variance / no consensus / blocking Human decision

NEUTRAL
incomplete / unavailable / not yet processed
```

Color alone shall never carry the meaning.

Every visual state shall also contain an explicit textual label, for example:

```text
Unanimous · 3 / 3 Personas agree
Majority · 2 / 3 Personas agree
High variance · Human decision required
```

Green means agreement between independent perspectives.

Green does not mean Human approval.

---

### UX-08 — Recurring interaction pattern

The same interaction pattern shall be reused across processing stages:

```text
INPUT
↓
PROPOSED RESULT(S)
↓
VARIANCE / CONFIDENCE
↓
HUMAN DECISION — where required
↓
ACCEPTED RESULT
```

This applies to:

- ingestion interpretation,
- semantic extraction,
- classification,
- Human Review,
- Model Candidate review,
- architecture / Model Proposal review,
- Final Model Review.

This consistency is intended to reduce cognitive switching between phases.

---

### UX-09 — Guided workflow stages

The engineer-facing workflow shall expose the following conceptual stages:

```text
1  Project & Sources
2  Processing
3  Human Review & Approved Input
4  Model Proposal & Candidate Review
5  Final Model Review
6  Published Output
```

These stages are presentation concepts.

They do not replace existing Phase/domain authority.

---

### UX-10 — Simple by default, explainable on demand

ADR-017 remains the primary presentation principle:

```text
Simple by default.
Explainable on demand.
Fully traceable underneath.
```

Default views shall show only information necessary for the current engineering
task.

Rationale, evidence, technical metadata and complete traceability remain reachable
without changing authority or losing auditability.

---

### UX-11 — No implicit latest authority

The UI may identify useful display defaults.

It shall not silently select a latest artifact as authority for a write action.

Candidate decisions, review decisions, change proposals, release decisions and
publication actions must remain bound to explicit immutable artifact identities.

Display convenience shall never weaken authority binding.

---

### UX-12 — Existing services remain normative

The Guided Workflow shall delegate write actions to the already established
domain services.

Examples include:

```text
ReviewApprovalWorkflowService
ModelCandidateReviewRepository
FinalModelReviewChangeService
FinalModelReviewReleaseService
OutputWriter
```

The UI shall not reproduce their validation or authority rules.

---

### UX-13 — Dual-layer presentation

Existing functional views shall not be discarded merely because their current
presentation is technically dense.

Where useful, engineer-facing workflow surfaces shall support two presentation
depths over the same authoritative state:

```text
Focused View
→ engineering content
→ Agent / Persona alternatives
→ consensus and variance
→ open Human decisions
→ accepted / approved engineering results
→ next engineering action

Technical View
→ processing identities
→ run / attempt state
→ artifact references
→ fingerprints
→ provenance
→ traceability
→ diagnostic and lifecycle information
```

The default presentation shall be the Focused View.

The engineer may explicitly enable technical details when deeper analysis,
diagnosis or auditability is required.

Conceptually:

```text
same authoritative state
          │
          ├── Focused presentation
          │     └── task-oriented engineering information
          │
          └── Technical presentation
                └── deeper processing and traceability information
```

The presentation-depth setting is UI state only.

It may be stored transiently in Streamlit session state because switching the
presentation depth does not modify:

- engineering content,
- Agent evidence,
- Human decisions,
- Candidate authority,
- validation state,
- Final Model Review state,
- publication eligibility,
- or published output.

The following distinction is normative:

```text
Focused ≠ reduced evidence
Focused = reduced visible complexity

Technical ≠ separate workflow
Technical = deeper presentation of the same workflow
```

Views that already provide useful functionality, including Project Dashboard,
Processing and Human Review, shall therefore be adapted progressively to this
dual-layer interaction model rather than replaced unnecessarily.

The Project Dashboard retains the distinct engineering purpose:

```text
Which engineering / model information is already available?
```

The Guided Engineering Workspace retains the distinct purpose:

```text
What requires my attention or decision now?
```

Individual LLM-backed processing steps may remain separate working surfaces when
this improves clarity. They shall reuse the same content-first, variance-aware and
Human-decision-centered interaction language.

---

### UX-14 — Global application context

Project selection and presentation depth are application-level context.

They shall therefore remain directly accessible independently of the currently
selected working surface.

The common application shell shall expose:

```text
Project
→ explicit currently selected Project

Technical details
→ Focused / Technical presentation depth
```

Conceptually:

```text
APPLICATION CONTEXT
Project: [ selected Project ]
Technical details: [ on / off ]

        ↓ shared by all views

Engineering Workspace
Project Dashboard
Processing
Human Review
Model Proposal
Final Model Review
Published Output
```

The engineer shall not have to navigate to the Project Dashboard merely to change
the current Project.

Likewise, the engineer shall not have to return to the Engineering Workspace to
change presentation depth.

Project selection changes UI working context.

It shall not modify persisted engineering state.

Changing the selected Project shall clear stale entity-level UI navigation from
the previously selected Project.

No Project shall be silently selected merely because it is the newest or only
recently used Project when no valid explicit selection exists.

Project creation remains a Project Workspace management function but shall be
directly accessible from the global application context.

The Project selector and the Project creation action shall therefore be colocated
in the common application shell:

```text
Project
[ Selected Project ▼ ]
+ Create new project
```

Project creation is an explicit action and shall not be represented as a
pseudo-Project inside the Project selection list.

After successful creation, the newly created Project becomes the explicitly
selected Project context.

The Project Dashboard shall not duplicate the creation control when it is rendered
inside the common application shell.

The presentation-depth control shall use a persistent application-level toggle
and shall affect all engineer-facing views progressively as WP-09 through WP-11
adopt the dual-layer presentation architecture.

---

### UX-15 — Authority-preserving write interaction

The Guided Engineering Workflow may initiate authoritative actions.

It shall never become engineering or workflow authority itself.

Every write initiated from an engineer-facing UI surface shall follow:

```text
explicit immutable target
+
explicit Human action
+
existing domain authority service
+
immutable authoritative persistence
+
read-side reconstruction after the write
```

Conceptually:

```text
Streamlit interaction
        ↓
GuidedWorkflowWriteService
        ↓
existing normative domain service
        ↓
authoritative immutable persistence
        ↓
existing read service / repository
        ↓
reconstructed UI state
```

`GuidedWorkflowWriteService` is an application-level delegation boundary only.

It shall not:

- reproduce Candidate Review rules,
- reproduce Final Model Review routing rules,
- reproduce release-gate logic,
- infer engineering approval,
- infer a latest authoritative target,
- mutate generated SysML directly,
- or store authoritative decisions in Streamlit session state.

The following domain services remain normative:

```text
ModelCandidateReviewRepository
FinalModelReviewChangeService
FinalModelReviewReleaseService
OutputWriter
```

Candidate Review writes shall require an explicit:

```text
Project
Candidate Set
Candidate type
Candidate identity
Human decision
Reviewer identity
```

Final Model Review change requests shall require an explicit:

```text
Project
Final Model Review
Final Model Review revision
affected review surface
change classification
Human feedback
reviewer identity
```

Final release approval shall require an explicit:

```text
Project
Final Model Review
Final Model Review revision
reviewer identity
```

The UI may simplify labels and interaction controls.

It shall not simplify or weaken the underlying authority contract.

After a successful write, the UI shall discard transient assumptions and
reconstruct the visible state from persisted authoritative evidence.

---

## Formative usability evaluation

The UX redesign follows a formative evaluation of the functionally complete
prototype.

The evaluation is treated as formative engineering feedback, not as a controlled
quantitative usability study unless separate evidence supports such a claim.

Observed findings and resulting design responses are maintained in:

```text
collaboration/ux/usability_findings.md
```

The implemented baseline and redesigned UI are intentionally retained as separate
development stages for later thesis documentation.

---

## Thesis evidence

The UX iteration shall be documented so that the development process can later be
reconstructed as:

```text
technical feasibility
→ functionally complete prototype
→ formative usability evaluation
→ identified usability findings
→ UX requirements
→ wireframes
→ redesigned Guided Engineering Workflow
→ final demonstrator
```

Stable wireframe identifiers shall be maintained under:

```text
collaboration/ux/wireframes/
```

The intended initial set is:

```text
WF-01  Engineer Home / Your Work
WF-02  Ingested Engineering Content
WF-03  Unanimous Persona Results
WF-04  Variant Persona Results
WF-05  Human Decision
WF-06  Model Proposal Review
WF-07  Final Model Review
```

Final thesis figures may be derived from these documented wireframes and from
before/after screenshots of the actual prototype.

---

## Work-package mapping

### WP-09 — Guided Workflow UI

Establish:

- Guided Engineering Workflow projection,
- shared navigation,
- shared Decision presentation,
- shared Variance presentation,
- progressive disclosure,
- reusable side-by-side result comparison.

### WP-10 — Ingestion + Human Review UX Simplification

Apply the UX architecture to:

- Source presentation,
- processing results,
- redundant Agent / Persona outputs,
- Human Review decisions.

### WP-11 — Architecture / Model Proposal UX

Apply the same interaction model to:

- Model Candidate proposals,
- structural comparison,
- architecture/model representation,
- candidate Human decisions.

### WP-12 — End-to-End Demo Hardening

Integrate and harden the complete engineer-facing workflow without weakening any
existing authority, validation or traceability contract.

---

## Consequences

Positive:

- the UI is organized around daily engineering work,
- Human decisions become immediately visible,
- Agent variance becomes useful information instead of hidden processing detail,
- redundant Agent results can be compared quickly,
- existing functional views can be retained and progressively improved,
- focused and technical work can use the same authoritative backend,
- technical traceability remains fully available,
- the same interaction language is reused across phases,
- UX evolution is reproducibly documented for the thesis.

Trade-offs:

- presentation read models become more important,
- some technical metadata moves behind additional interaction,
- visual consensus representations require careful accessibility semantics,
- responsive side-by-side layouts require deliberate UI design.

These trade-offs are accepted.

---

## Prohibited shortcuts

The following are explicitly prohibited:

- replacing engineering authority with UI state,
- treating consensus as Human approval,
- hiding dissenting Agent / Persona results behind an aggregate score,
- counting repeated runs of one Persona as independent votes,
- presenting color without textual meaning,
- direct mutation of generated SysML from the UI,
- implicit latest-artifact authority,
- bypassing Human Review,
- bypassing Validation,
- bypassing Final Human release approval,
- removing traceability merely to simplify the visible UI,
- maintaining separate engineering authority for Focused and Technical views,
- changing engineering state merely by switching presentation depth.

---

## Final principle

The UI shall minimize the engineer's effort to understand and decide.

It shall not minimize the engineering evidence available to justify that decision.
