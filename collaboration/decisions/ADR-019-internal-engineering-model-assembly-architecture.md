# ADR-019 — Internal Engineering Model Assembly Architecture

## Status

Accepted

## Date

2026-08-13

## Context

Phase H establishes the reviewed Model Candidate Layer and exposes the sole
validated Phase-H → Phase-I authority transfer through:

`ModelCandidateReadService.load_phase_i_input(project_id, candidate_set_id)`

The resulting `ModelCandidateAssemblyInput` contains only explicitly authorized
Element Candidates and Relationship Candidates together with Candidate-Set,
Approved-Input, Human-Review, exception, profile and generation provenance.

Phase I is responsible for assembling this authorized content into one coherent
Internal Engineering Model.

Phase I shall not repeat the semantic interpretation performed in Phase H.

Phase I shall not bypass Human Review.

Phase I shall not generate SysML v2 textual notation.

The Framework Template and Model Structure and Comparability Profile already
define the structural areas into which accepted Candidate content has been
classified.

The accepted Phase-H architecture requires Phase I to preserve Candidate
semantics exactly and to consume only the validated H→I read contract.

The implementation therefore requires a deterministic assembly layer that:

- materializes the selected framework hierarchy,
- maps accepted Element Candidates into that hierarchy,
- maps accepted Relationship Candidates to exact internal model elements,
- preserves Human Review and Approved-Input traceability,
- preserves accepted exceptions,
- validates internal assembly integrity,
- persists an immutable Internal Engineering Model snapshot,
- and provides an explicit read boundary for Phase J.

The CATIA engineering model describes architecture derivation/structuring and
architecture validation as related but distinct responsibilities. The
implementation roadmap separates these temporally:

- Phase I performs deterministic architecture assembly,
- Phase K performs broader model validation,
- Phase J performs SysML v2 textual serialization.

---

## Decision

### I-01 — Sole upstream authority

Phase I shall consume Phase-H engineering content exclusively through:

`ModelCandidateReadService.load_phase_i_input(project_id, candidate_set_id)`

Phase-I production assembly shall not independently read:

- raw Approved Inputs,
- Candidate Review persistence,
- unreviewed Candidate Sets,
- rejected Candidates,
- deferred Candidates,
- Model Proposal presentation state,
- or other upstream processing evidence

for the purpose of deciding which engineering content is assembled.

The H→I read contract remains the authorization boundary.

---

### I-02 — Handoff enrichment

`ModelCandidateAssemblyInput` shall be extended to include the exact:

- `framework_template_reference`
- `derivation_rules_reference`

already bound by the source Model Candidate Set.

Phase I shall not independently rediscover these references from unrelated
repository state.

This extension does not change Phase-H engineering semantics.

It strengthens the existing H→I authority transfer so Phase I receives all
required pinned assembly context through one validated contract.

---

### I-03 — Deterministic assembly

The normative Phase-I path shall be deterministic.

Phase I shall not require an LLM to reinterpret reviewed Candidate content.

The roadmap term "Model Generation Agent" is implemented architecturally as a
deterministic Internal Model Assembly capability.

Any optional future agent assistance shall remain non-authoritative and shall
not bypass this deterministic assembly contract.

---

### I-04 — Immutable Internal Engineering Model snapshot

Every materially distinct authorized assembly shall produce an immutable
Internal Engineering Model snapshot.

Identifier form:

`IEM-000001`

The Internal Engineering Model snapshot is a reproducible model-assembly
boundary.

Published IEM snapshots shall not be modified in place.

---

### I-05 — Exact authorization binding

Every IEM snapshot shall bind the exact Phase-I assembly input.

A deterministic `assembly_input_fingerprint` shall cover the authority-bearing
H→I input required to reproduce the assembly, including at least:

- project identity,
- Candidate Set identity and fingerprint,
- Approved-Input snapshot fingerprint,
- Framework Template reference,
- Model Structure Profile reference,
- derivation-rules reference,
- accepted Element Candidate identities and fingerprints,
- accepted Relationship Candidate identities and fingerprints,
- Candidate Review Decision references and fingerprints,
- accepted-exception references.

A later change in Human Review authorization therefore produces a different
assembly input even when the Candidate Set itself remains unchanged.

---

### I-06 — Idempotent exact reassembly

The combination of:

- identical `assembly_input_fingerprint`, and
- identical assembly-rule reference/version

shall be treated idempotently.

The system shall not silently create multiple semantically identical IEM
snapshots for the exact same authorized assembly state.

No implicit "latest IEM wins" behavior is permitted.

---

### I-07 — Separate Internal Model Element identity

Accepted Element Candidates shall be assembled as immutable Internal Model
Elements.

Identifier form:

`IME-000001`

The following identities remain distinct:

- Element Candidate identity (`MCE-...`)
- Internal Model Element identity (`IME-...`)
- semantic subject identity

An IME shall preserve explicit traceability to its source MCE.

---

### I-08 — Separate Internal Model Relationship identity

Accepted Relationship Candidates shall be assembled as immutable Internal Model
Relationships.

Identifier form:

`IMR-000001`

Every IMR shall:

- preserve its source MCR identity,
- reference exact source and target IMEs in the same IEM snapshot,
- preserve source and target semantic subject identities,
- preserve Approved-Input and Human-Review traceability.

---

### I-09 — Preserve accepted relationship semantics

Phase I shall preserve the accepted Candidate relationship semantics without
reinterpretation.

The following remain distinct and shall be retained:

- `relationship_family`
- `semantic_intent`
- `directionality`

Phase I shall not convert one accepted semantic intent into another.

The semantic-to-SysML-v2 serialization decision belongs to Phase J.

---

### I-10 — Template-derived structural skeleton

Phase I shall materialize the pinned Framework Template hierarchy as an
internal structural skeleton.

For the accepted Turing RFLP framework this includes:

```text
Stakeholder Level
├── Stakeholders
├── User Needs
├── Stakeholder Requirements
└── Use Cases

System Level
├── Requirements
├── Functional
├── Logical
└── Physical

Subsystem Level
├── Requirements
├── Functional
├── Logical
└── Physical
```

Internal structure nodes are organizational model structure.

They are not additional inferred engineering elements.

---

### I-11 — Deterministic containment

Every accepted IME shall be assigned to exactly one applicable Framework
Template mapping node.

The assignment shall be derived from the reviewed Candidate information already
established in Phase H, including:

- `model_area`
- `element_type`
- `framework_assignment`

Phase I shall verify this mapping against the pinned:

- Framework Template
- Model Structure and Comparability Profile

Phase I shall not semantically reclassify the element.

---

### I-12 — No invented engineering hierarchy

Phase I shall not infer additional engineering containment, decomposition or
ownership relationships merely from:

- element names,
- similarity,
- model area proximity,
- ordering,
- or structural convenience.

Any engineering hierarchy beyond the Framework Template structure requires
explicit reviewed Candidate semantics.

The Framework Template hierarchy itself may be materialized because it is
pinned configuration, not inferred engineering content.

---

### I-13 — Empty structural nodes allowed

The complete selected Framework Template structure may be materialized even
when one or more structural areas contain no accepted engineering elements.

Phase I shall not decide whether empty structural areas become explicit SysML v2
packages or other textual constructs.

That representation decision belongs downstream.

---

### I-14 — Accepted exceptions remain explicit

`accepted_exception` authorization shall remain explicit in the Internal
Engineering Model.

The affected IME or IMR shall preserve the exact associated Human Review
Decision reference.

Phase I shall not silently normalize an accepted exception into ordinary
conformance.

An accepted exception may authorize a reviewed structural deviation.

It shall not disable fundamental assembly-integrity requirements.

---

### I-15 — Fail closed on non-deterministically assemblable content

If accepted Candidate content cannot be assembled without introducing new
engineering semantics or making an unauthorized choice, Phase I shall fail
closed.

The system shall produce an explicit assembly finding/diagnostic rather than
inventing a solution.

The required resolution shall return to the applicable upstream authority,
which may include:

- Candidate interpretation,
- Human Review,
- Structure Profile,
- Framework Template,
- or architecture configuration.

---

### I-16 — Phase-I assembly-integrity validation

Phase I shall validate internal assembly integrity.

This validation includes at least:

- unique IEM / IME / IMR identities,
- project isolation,
- exact Candidate traceability,
- exact Human Review traceability,
- exact Approved-Input traceability,
- every IME assigned to a valid structural node,
- `element_type` compatibility with the selected model area/profile,
- every IMR endpoint resolving to an IME in the same IEM,
- no dangling Internal Model Relationships,
- no unauthorized Candidate content,
- preservation of accepted exceptions,
- no duplicate internal identities,
- deterministic snapshot fingerprint integrity.

Phase-I assembly validation shall not silently modify engineering content in
order to pass.

---

### I-17 — Phase I does not replace Phase K

Phase-I validation is limited to assembly and internal representation integrity.

Broader model validation remains Phase K, including applicable:

- architecture-constraint validation,
- structural-pattern validation,
- larger-context compatibility,
- interface consistency,
- relationship-semantic validation,
- target-model compatibility,
- and publication-blocking validation.

Phase I may report that content is not assemblable.

It shall not absorb the complete Phase-K validation responsibility.

---

### I-18 — No SysML v2 textual constructs in Phase I

The Internal Engineering Model remains representation-neutral with respect to
concrete SysML v2 textual syntax.

Phase I may retain engineering concepts such as:

- `system_requirement`
- `function`
- `logical_component`
- `allocated_to`
- `dependency`
- `flows_to`

Phase I shall not generate concrete textual constructs such as:

- `requirement`
- `part def`
- `action def`
- `dependency from ...`
- package serialization
- target-specific SysML v2 syntax

SysML v2 textual generation belongs to Phase J.

---

### I-19 — Explicit Phase-J read boundary

Phase J shall consume an explicitly selected Internal Engineering Model
snapshot through a validated read contract.

Conceptually:

```python
InternalModelReadService.load_phase_j_input(
    project_id,
    internal_engineering_model_id,
) -> InternalEngineeringModelSnapshot
```

There shall be no implicit latest-IEM selection.

The Phase-J read contract shall verify snapshot integrity and project isolation
before exposing the Internal Engineering Model downstream.

---

### I-20 — CATIA and logical-architecture alignment

The Internal Engineering Model corresponds conceptually to the architecture
result produced by the CATIA system behavior "Derive and Structure Architecture
Information".

The implementation separation is:

```text
LC_07 Architecture Synthesis and Validation
├── Phase I — synthesis / deterministic assembly
└── Phase K — broader architecture/model validation

LC_08 SysML v2 Artifact Generation
└── Phase J — SysML v2 textual generation
```

Implementation phases therefore do not map one-to-one to Logical Components.

This separation is intentional and shall be documented rather than treated as a
conflict between implementation and CATIA architecture.

---

## Internal Engineering Model artifacts

### Internal Engineering Model Manifest

The IEM manifest shall bind at least:

- schema version
- project identity
- IEM identity
- assembly-input fingerprint
- Candidate Set identity
- Candidate Set content fingerprint
- Approved-Input snapshot fingerprint
- Framework Template reference
- Model Structure Profile reference
- derivation-rules reference
- assembly-rules reference
- assembly provenance
- Internal Model Structure reference
- IME references
- IMR references
- Candidate Review Decision references
- accepted-exception references
- creation timestamp
- immutable content fingerprint

---

### Internal Model Element

Each IME shall support at least:

- schema version
- project identity
- IEM identity
- IME identity
- semantic subject identity
- source MCE identity
- source MCE fingerprint
- name
- description
- model area
- element type
- Framework assignment
- terminology assignment
- attributes
- comparison anchor where applicable
- Approved-Input references
- Human Review Decision reference
- accepted-exception reference where applicable
- immutable content fingerprint

---

### Internal Model Relationship

Each IMR shall support at least:

- schema version
- project identity
- IEM identity
- IMR identity
- source IME identity
- target IME identity
- source semantic subject identity
- target semantic subject identity
- relationship family
- semantic intent
- directionality
- source MCR identity
- source MCR fingerprint
- Approved-Input references
- Human Review Decision reference
- accepted-exception reference where applicable
- immutable content fingerprint

---

### Internal Model Structure

The Internal Model Structure shall contain:

- Framework Template identity
- deterministic materialized structure nodes
- parent/child structure-node relationships
- stable node ordering
- exact IME membership per structural node
- immutable structure fingerprint

The structure artifact shall not duplicate the complete engineering content of
the IME artifacts.

It represents model organization and containment.

---

## Persistence

The default project-local persistence layout is:

```text
data/projects/<project_id>/internal_models/
└── IEM-000001/
    ├── manifest.json
    ├── structure.json
    ├── elements/
    │   ├── IME-000001.json
    │   └── ...
    └── relationships/
        ├── IMR-000001.json
        └── ...
```

The complete IEM bundle shall be persisted atomically and immutably.

Partial publication shall not constitute a valid IEM snapshot.

Repository scanning shall fail closed on:

- corrupt manifests,
- missing referenced artifacts,
- unexpected artifact identities,
- cross-project references,
- fingerprint mismatch,
- symlink/path-safety violations,
- or interrupted temporary publication state.

---

## Assembly flow

The normative Phase-I flow is:

```text
ModelCandidateReadService
        │
        ▼
ModelCandidateAssemblyInput
        │
        ├── pinned Framework Template
        ├── pinned Model Structure Profile
        └── pinned assembly / derivation context
        │
        ▼
InternalModelAssemblyService
        │
        ├── materialize structural skeleton
        ├── MCE → IME
        ├── MCR → IMR
        ├── preserve exceptions
        ├── preserve traceability
        └── validate assembly integrity
        │
        ▼
Immutable InternalEngineeringModelSnapshot
        │
        ▼
InternalModelReadService
        │
        ▼
Phase J
```

---

## Human Review boundary

Phase I introduces no new normative Human Review layer for semantic
reinterpretation.

Human Review of engineering meaning occurs upstream.

If deterministic assembly cannot continue without a new engineering decision,
Phase I fails closed and surfaces the condition for upstream resolution.

Phase I shall not use an additional AI or Human Review step to silently modify
already accepted Candidate semantics.

---

## Phase boundaries

### Phase H

- interprets approved engineering information,
- proposes model elements and relationships,
- identifies alternatives,
- assesses comparability,
- performs Human Review,
- authorizes Candidate content for assembly.

### Phase I

- consumes only authorized Candidate content,
- materializes the framework structure,
- assembles Internal Model Elements,
- assembles Internal Model Relationships,
- preserves exact semantics and traceability,
- performs assembly-integrity validation,
- persists the immutable Internal Engineering Model.

### Phase J

- maps the Internal Engineering Model to supported SysML v2 constructs,
- applies the target-notation profile,
- generates SysML v2 textual notation.

### Phase K

- performs broader syntax, semantic, structural, integration, constraint,
  traceability and comparability validation as applicable.

---

## Consequences

### Positive consequences

- Phase-H Human Review remains authoritative.
- Model assembly is deterministic and reproducible.
- The Internal Engineering Model is independent of SysML v2 textual syntax.
- Framework hierarchy and engineering semantics remain separate concepts.
- Accepted exceptions remain visible.
- Every internal element and relationship retains exact upstream traceability.
- Phase J receives one coherent model rather than independent Candidate
  artifacts.
- Phase K remains a distinct validation responsibility.
- Repeated exact assembly is idempotent.
- Historical IEM snapshots remain reproducible.

### Trade-offs

- Phase I introduces IEM / IME / IMR identities.
- A separate internal structure artifact is required.
- H→I transfer must be enriched with pinned Framework Template and
  derivation-rules references.
- Repository and fingerprint validation add implementation work.
- Some accepted Candidate combinations may fail closed and require upstream
  resolution rather than automatic correction.

---

## Rejected alternatives

### Reinterpret accepted Candidates in Phase I

Rejected because this would bypass Phase-H Human Review and duplicate semantic
model derivation.

### Generate SysML v2 directly in Phase I

Rejected because model assembly and target-language serialization are separate
responsibilities and Phase J owns SysML v2 textual generation.

### Use Candidate IDs directly as final internal model identities

Rejected because Candidate identity, semantic continuity and assembled snapshot
identity have different lifecycle semantics.

### Treat the Framework Template as engineering content

Rejected because template structure is organizational configuration and does not
by itself create new engineering elements or engineering relationships.

### Automatically invent missing hierarchy

Rejected because additional engineering containment or decomposition requires
reviewed semantic evidence.

### Let Phase I perform all downstream model validation

Rejected because this would collapse assembly and validation and would conflict
with the planned Phase-K boundary.

### Select the latest Internal Engineering Model implicitly

Rejected because explicit snapshot identity is required for reproducibility and
traceability.

---

## Related decisions

- ADR-016 — Human Review Workspace and Approved Input Promotion Architecture
- ADR-017 — Simple-by-Default Interaction and Progressive Disclosure
- ADR-018 — Model Candidate Layer and Structural Comparability

---

## Initial implementation decomposition

After this ADR is committed, Phase I may proceed in the following internal
implementation slices:

```text
I1  identifiers + immutable Internal Model domain types
I2  manifests + fingerprints + H→I contract enrichment
I3  Framework/Profile resolution + structure materialization
I4  deterministic MCE/MCR → IME/IMR assembly
I5  repository + immutable persistence + assembly-integrity validation
I6  Phase-J read contract + regression + SSOT closeout
```

This decomposition is an implementation planning aid.

The official roadmap phase remains Phase I — Model Generation Agent / Internal
Engineering Model.

---

## Implementation note

No Phase-I production implementation shall precede acceptance and persistence of
this ADR.

Implementation shall reuse the existing:

- project-isolation rules,
- safe-path behavior,
- atomic-persistence patterns,
- identifier conventions,
- deterministic manifest/fingerprint patterns,
- Framework Template loader,
- Model Structure Profile loader,
- and H→I authorization contract

where applicable rather than duplicating upstream logic.
