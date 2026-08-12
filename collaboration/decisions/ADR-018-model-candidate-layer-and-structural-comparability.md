# ADR-018 — Model Candidate Layer and Structural Comparability

## Status

Accepted

## Date

2026-08-12

## Context

Phase G establishes the authoritative promotion boundary from reviewed project
information to immutable Approved Inputs.

Phase H consumes those Approved Inputs and creates a coherent proposal for the
target engineering model.

The Phase-H layer must support:

- joint interpretation of all active Approved Inputs of a project,
- candidate model-element derivation,
- candidate relationship derivation,
- explicit relationship semantics and alternatives,
- advisory relationship prioritization,
- structural comparability across related models,
- versioned structural modeling guidance,
- Human Review,
- complete provenance,
- deterministic downstream consumption by Phase I,
- and a comprehensible user-facing model proposal.

Phase H shall not generate SysML v2 textual notation and shall not create a new
engineering authority source.

The system-wide interaction principle defined by ADR-017 applies:

> Simple by default. Explainable on demand. Fully traceable underneath.

A user shall therefore primarily see a coherent model proposition rather than
individual technical candidate artifacts.

---

## Decision

### 1. Phase-H authority boundary

Phase H consumes engineering authority exclusively through:

`ApprovedInputRepository.list_active_approved_inputs(project_id)`

Draft Review State, Agent Confidence, Consensus data, inactive Approved Inputs,
UI state, and original Review Reports shall not act as direct Phase-H authority
sources.

Approved Inputs remain unchanged.

Phase H creates derived Model Candidates based on the exact active Approved-Input
snapshot.

Model Candidates are not equivalent to Approved Inputs and are not equivalent
to the authoritative CATIA engineering model.

Human acceptance of a Model Candidate authorizes its use for Phase-I model
assembly only.

---

### 2. Model Candidate Set

Each Phase-H execution creates an immutable Model Candidate Set.

Proposed identifier form:

`MCS-000001`

A Candidate Set represents a reproducible snapshot of the complete Phase-H model
proposal for one project.

It shall bind at least:

- project identity,
- Candidate Set identity,
- predecessor Candidate Set where applicable,
- regeneration reason where applicable,
- exact Approved-Input references and fingerprints,
- Approved-Input snapshot fingerprint,
- framework-template reference,
- Model Structure and Comparability Profile reference,
- derivation-rules reference,
- generation provenance,
- Element Candidate references,
- Relationship Candidate references,
- creation timestamp,
- content fingerprint.

There shall be no implicit "latest Candidate Set wins" behavior.

Downstream consumers must explicitly select a Candidate Set.

---

### 3. Element Candidates

Candidate model elements are represented as immutable Element Candidates.

Proposed identifier form:

`MCE-000001`

Element Candidate instance identity is distinct from semantic continuity.

Each Element Candidate shall support at least:

- immutable candidate identity,
- candidate subject key,
- comparison anchor where applicable,
- proposed name and description,
- model area,
- profile-defined element type,
- framework assignment,
- terminology assignment,
- attributes,
- exact Approved-Input provenance,
- derivation rationale,
- support level,
- assumptions,
- missing information,
- structural-profile conformance,
- predecessor candidate references,
- immutable content fingerprint.

Where possible, a one-to-one derivation should retain continuity with the
Approved Input stable subject key.

Aggregation or decomposition may create new candidate subject identities while
preserving all contributing provenance.

---

### 4. Relationship Candidates

Relationships are independent immutable Candidate artifacts.

Proposed identifier form:

`MCR-000001`

Relationships shall not be embedded implicitly in Element Candidates.

Every Relationship Candidate shall support at least:

- immutable relationship candidate identity,
- Candidate Set identity,
- relationship choice key where alternatives belong to the same decision,
- exact source Element Candidate reference,
- exact target Element Candidate reference,
- source and target semantic subject keys,
- relationship family,
- semantic intent,
- directionality,
- exact Approved-Input provenance,
- derivation rationale,
- supporting evidence,
- assumptions,
- missing information,
- priority assessment,
- structural-comparability assessment,
- structural-profile conformance,
- upstream Approved-Input relationship representation where applicable,
- predecessor candidate references,
- immutable content fingerprint.

Every relationship eligible for Phase I must resolve its source and target to
exact Element Candidates within the same Candidate Set.

Zero matching endpoints are unresolved.

More than one matching endpoint is ambiguous.

Exactly one matching endpoint is resolved.

---

### 5. Relationship semantics

Relationship family, engineering semantic intent, and eventual SysML v2
serialization are separate concepts.

Relationship families may include, among others:

- dependency,
- allocation,
- flow,
- refinement-related,
- derivation-related,
- framework-specific relationships.

The actual controlled vocabulary shall be defined by versioned configuration or
profile data and shall not be silently hardcoded into processing logic.

Distinct semantic meanings shall never be silently collapsed into a generic
relationship.

Where multiple materially different interpretations remain plausible, separate
Relationship Candidates shall be created and grouped through one relationship
choice key.

Existing Approved-Input relationship representations may be carried forward as
evidence.

Phase H shall not silently override an explicit Approved-Input relationship
interpretation.

Any changed interpretation requires explicit rationale and traceability.

Final semantic-to-SysML-v2 serialization belongs to Phase J.

Formal SysML-v2 validation belongs to Phase K.

---

### 6. Relationship prioritization

Automated relationship prioritization is advisory only.

No automated priority shall constitute engineering approval.

The default priority classes are:

- preferred,
- supported_alternative,
- exception_candidate.

Prioritization shall record machine-readable criterion results and a
human-readable rationale.

The prioritization criteria are evaluated in the following conceptual order:

1. evidence directness,
2. semantic fit,
3. endpoint certainty,
4. structural-profile preference,
5. structural-comparability impact,
6. assumption burden,
7. conformance.

An explicit Approved-Input relationship normally has stronger evidence
directness than a relationship inferred solely from separate Approved Inputs.

Human Review remains the authorization boundary.

---

### 7. Model Structure and Comparability Profile

Phase H introduces a versioned Model Structure and Comparability Profile.

This profile is separate from the SysML v2 Target Notation Profile.

The Model Structure and Comparability Profile defines, at minimum:

- preferred model areas,
- permitted element types,
- comparison anchors,
- canonical structural patterns,
- canonical relationship semantics,
- relationship preferences,
- permitted structural variation,
- prioritization criteria,
- exception rules,
- review requirements.

The purpose of the profile is to improve structural comparability between:

- related products,
- product variants,
- independently generated models,
- repeated model-generation executions.

The guiding principle is:

Where engineering meaning and modeling context are equivalent, the same
structural representation should be preferred.

Different engineering meaning may justify different structures.

Intentional deviations remain possible but require explicit rationale and Human
Review.

---

### 8. Structural-comparability assessment

Candidates may record structural-comparability effects including:

- improves,
- neutral,
- reduces,
- unknown.

The assessment may include:

- affected comparison anchors,
- canonical-pattern match,
- structural deviations,
- rationale.

Comparability findings are advisory evidence for Human Review and shall not
replace engineering judgment.

---

### 9. Human Review

Model Candidate content is immutable.

Human Review decisions are persisted separately and are bound to the exact
Candidate content fingerprint.

Supported decision concepts include:

- accepted,
- rejected,
- deferred,
- accepted_exception.

An accepted exception requires explicit rationale.

Human Review shall bind at least:

- project identity,
- Candidate Set identity,
- Candidate identity or explicitly defined Candidate Set selection scope,
- exact content fingerprint,
- reviewer identity,
- review timestamp,
- decision,
- rationale where required,
- structural-profile reference,
- relevant conformance fingerprint,
- Approved-Input snapshot fingerprint,
- immutable decision fingerprint.

Existing generic Human Review infrastructure shall be reused where compatible
rather than duplicated.

The exact review granularity may support review-by-exception, provided that every
authoritative Phase-I selection remains explicitly persisted and bound to exact
candidate content.

---

### 10. Lifecycle and regeneration

Candidate artifacts and review decisions remain immutable.

If any material Approved Input referenced by a Candidate Set later becomes
inactive, the historical Candidate Set remains preserved but becomes ineligible
for new Phase-I assembly.

A new analysis creates a new Candidate Set.

Regeneration shall:

- create a new Candidate Set identity,
- create new Candidate instance identities,
- preserve predecessor references,
- preserve semantic subject continuity where applicable,
- preserve complete provenance.

Historical Candidate Sets are never silently replaced.

---

### 11. Phase-I read contract

Phase I shall consume Phase-H output only through an explicit validated read
contract.

Conceptually:

`ModelCandidateReadService.load_phase_i_input(project_id, candidate_set_id)`

The read boundary shall verify at least:

- Candidate Set integrity,
- project isolation,
- immutable fingerprints,
- current activity of material Approved Inputs,
- exact Human Review decisions,
- absence of stale decisions,
- endpoint resolution,
- acceptance of required Element Candidates,
- acceptance of required Relationship Candidates,
- absence of blocking unresolved relationships,
- structural-profile conformance or an explicitly accepted exception.

The resulting Phase-I input shall contain only explicitly authorized Candidate
content and relevant provenance.

Phase I may assemble accepted Candidates into the Internal Engineering Model.

Phase I shall not invent new engineering semantics from unaccepted Phase-H
Candidates.

---

### 12. User-facing Model Proposal

The primary user-facing Phase-H result is a coherent Model Proposal rather than
a collection of technical manifests.

The Model Proposal is a deterministic projection of one explicit Candidate Set.

It is not an independent authority source.

Conceptually, the presentation contract is:

`ModelProposalView`

It shall support at least:

- Candidate Set identity,
- proposal summary,
- proposed model elements,
- proposed relationships,
- structural overview,
- relationship choice groups,
- structural-comparability summary,
- profile deviations,
- required Human Review decisions,
- summarized rationale,
- next action.

All displayed information must resolve back to immutable Candidate artifacts and
review evidence.

---

### 13. Visual model projections

The Model Proposal may and should use visual model projections where they
improve comprehension.

Examples include:

- structural overview diagrams,
- UML-like component views,
- SysML-like block views,
- requirement-to-function views,
- function-to-logical-component allocation views,
- relationship networks,
- alternative relationship visualizations.

These visualizations are explanatory projections of Candidate data.

They are not themselves the machine-readable model authority.

A visual relationship may therefore replace verbose technical relationship
descriptions in the primary UI while retaining the complete technical
relationship representation underneath.

The default user interaction shall prefer:

1. understandable graphical/model result,
2. material uncertainty,
3. required human decision,
4. next action.

Detailed rationale and alternatives shall be available on demand.

Complete provenance and audit information shall remain accessible underneath.

The Phase-H visualization does not have to constitute formally valid SysML v2
notation.

Formal model assembly belongs to Phase I.

Formal SysML v2 textual generation belongs to Phase J.

---

### 14. Optional Model Proposal report

A human-readable or exportable Model Proposal Summary may be generated from an
explicit Candidate Set.

Such a report may be retained as presentation, thesis, or audit evidence.

It shall remain a reproducible projection and shall never replace the Candidate
Set as the machine-readable source of truth.

---

### 15. Phase boundaries

Phase H:

- jointly interprets active Approved Inputs,
- proposes model elements,
- proposes relationships,
- represents alternatives,
- prioritizes relationships advisorially,
- assesses structural comparability,
- performs Candidate Human Review,
- exposes the Model Proposal View.

Phase I:

- assembles explicitly accepted Candidates into the Internal Engineering Model.

Phase J:

- generates SysML v2 textual notation from the Internal Engineering Model.

Phase K:

- validates syntax, semantics, structure, target-profile conformance, and
  applicable comparability constraints.

---

## Consequences

### Positive consequences

- Project information is synthesized into one coherent model proposal.
- Approved Inputs remain immutable and authoritative within their existing scope.
- Model derivation remains completely traceable.
- Alternative modeling interpretations remain explicit.
- Relationship semantics are not silently flattened.
- Structural comparability becomes a first-class modeling concern.
- Human Review remains the engineering authorization boundary.
- The default UX can remain simple despite detailed underlying traceability.
- Visual diagrams can communicate architecture considerably more efficiently
  than raw relationship manifests.
- Phase H remains independent from final SysML v2 textual serialization.
- Phase I receives a deterministic and validated input contract.

### Trade-offs

- Candidate Set lifecycle introduces additional persistent identities.
- Candidate review and regeneration require explicit lifecycle handling.
- Structural comparability requires a maintained versioned profile.
- Visual proposal rendering introduces a presentation layer that must remain
  strictly derived from machine-readable Candidate data.
- Relationship alternatives increase artifact count but prevent semantic
  information loss.

---

## Rejected alternatives

### Generate SysML v2 directly from Approved Inputs in Phase H

Rejected because this would collapse modeling synthesis, engineering-model
assembly, serialization, and validation into one stage and would bypass the
planned Phase-I architecture boundary.

### Treat the visual diagram as the authoritative model

Rejected because graphical layout is a presentation concern and must remain
reproducible from structured Candidate data.

### Require users to review every technical Candidate manifest directly

Rejected because this conflicts with ADR-017 and would create unnecessary UX
complexity.

### Collapse all relationship semantics into generic links

Rejected because semantic distinctions are relevant for engineering correctness,
structural comparability, and later SysML v2 generation.

### Automatically accept the highest-ranked relationship

Rejected because prioritization is advisory and may not substitute explicit
Human Review.

---

## Related decisions

- ADR-016 — Human Review Workspace and Approved Input Promotion Architecture
- ADR-017 — Simple-by-Default Interaction and Progressive Disclosure

---

## Implementation note

No Phase-H production implementation shall precede acceptance and persistence of
this ADR.

Implementation shall reuse existing repository, Human Review, validation,
identifier, fingerprint, and project-isolation contracts where applicable rather
than duplicating upstream logic.