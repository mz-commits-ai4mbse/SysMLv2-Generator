# ADR-022 — SysML v2 Validation Layer Architecture

## Status

Accepted

## Date

2026-08-14

## Context

Phase J is completed and provides one deterministic, immutable validation-ready
`GeneratedSysMLArtifactSet`.

The accepted end-to-end boundary is:

```text
Internal Engineering Model
→ Phase J — deterministic SysML v2 generation
→ GeneratedSysMLArtifactSet
→ Phase K — validation
→ SysMLValidationResult
→ Phase L — versioned publication
```

Phase J already guarantees generation-time integrity including deterministic
serialization, exact generation-policy references, generated unit fingerprints,
artifact-set fingerprints, complete IME/IMR coverage, generated locations and
machine-readable traceability.

Phase K has a different responsibility.

It shall validate the complete generated artifact before publication without:

- regenerating SysML v2,
- changing generated text,
- reinterpreting engineering semantics,
- bypassing the Phase-J artifact contract,
- or publishing output itself.

The roadmap requires Phase K to cover:

- syntax validation,
- Target Notation validation,
- Artifact Structure validation,
- relationship and endpoint consistency,
- traceability,
- comparability/profile consistency,
- deterministic findings,
- and a fail-closed Phase-L publication gate.

The current Phase-J syntax evidence was established through small controlled
SYSIDE fixtures. Those checks authorize supported syntax patterns but do not
constitute validation of a complete generated target model.

Phase K therefore requires both deterministic Turing-specific validation and an
explicit external SysML v2 compatibility-validation boundary.

---

## Decision

### K-01 — Sole upstream validation subject

The sole normative Phase-K input is one explicit immutable:

`GeneratedSysMLArtifactSet`

The service boundary is:

```python
SysMLValidationService.validate(
    artifact_set: GeneratedSysMLArtifactSet,
) -> SysMLValidationResult
```

Phase K shall not independently reload:

- Approved Inputs,
- Model Candidates,
- Candidate Review persistence,
- raw Processing evidence,
- UI state,
- or the source IEM for semantic reinterpretation

in order to determine whether the generated model is valid.

There is no implicit latest-artifact selection.

The exact validation subject is bound by
`GeneratedSysMLArtifactSet.content_fingerprint`.

---

### K-02 — Validation is observational and never repairs

Phase K shall never silently modify generated content in order to make validation
pass.

Invalid content shall produce explicit findings and block publication.

Phase K shall not:

- rename generated symbols,
- reorder generated packages,
- alter relationship endpoints,
- substitute target constructs,
- normalize engineering descriptions,
- auto-format and replace generated content,
- or invoke Phase J to silently regenerate corrected output.

Resolution belongs to the phase, policy artifact or implementation responsible
for the finding.

---

### K-03 — Two-layer validation architecture

Phase K shall contain two intentionally separate validation layers.

#### Deterministic internal validation

Implemented inside the Turing Generator.

It validates Turing-specific generated-artifact invariants including:

- artifact identity and fingerprint integrity,
- generation-context integrity,
- Target Notation reference integrity,
- Generation Profile reference integrity,
- Artifact Structure reference integrity,
- Generator Rules reference integrity,
- generated-unit structure,
- target-subset conformance,
- package and artifact-layout rules,
- relationship and endpoint consistency,
- traceability integrity,
- accepted-exception preservation,
- and publication-policy invariants.

These checks require no external modeling tool.

#### External SysML v2 compatibility validation

Implemented through an explicit external-validator adapter.

The MVP target validator is the SYSIDE Modeler CLI using its non-mutating
validation/check capability.

External validation establishes parser/tool compatibility for the actual
complete generated artifact set.

Internal deterministic validation shall not attempt to become a complete SysML
v2 parser.

External validation shall not replace Turing-specific deterministic contract
validation.

Both layers are required for a publication-ready PASS.

---

### K-04 — Separate versioned Validation Profile

Phase K introduces:

```text
context/sysml/turing_sysml_v2_validation_profile.json
```

Initial identity:

```text
profile_id:      TURING_SYSML_V2_VALIDATION
profile_version: 1.0.0
```

The Validation Profile defines:

> Which validation checks are required, how findings are classified, which
> external validator is required, and what constitutes a Phase-K publication
> PASS.

It shall define at least:

- required internal validators,
- required external validator,
- external-validator availability policy,
- diagnostic severity policy,
- publication-blocking policy,
- diagnostic normalization policy,
- and validation-result fingerprint policy.

It shall not redefine:

- SysML v2 target syntax,
- IEM → SysML semantic mappings,
- package organization,
- generator formatting,
- or engineering semantics.

Those responsibilities remain with the existing Target Notation, Generation
Profile, Artifact Structure Profile, Generator Rules and Model Structure /
Comparability Profile.

---

### K-05 — Exact generation-policy resolution

`GeneratedSysMLArtifactSet.generation_context` contains exact references and
fingerprints for:

- Target Notation,
- Generation Profile,
- Artifact Structure Profile,
- Generator Rules.

Phase K shall resolve these exact referenced policy artifacts and require exact
fingerprint agreement.

Conceptually:

```text
artifact-set pinned reference
        │
        ▼
resolve exact policy artifact
        │
        ▼
validate policy artifact
        │
        ▼
recalculate fingerprint
        │
        ├── exact match → continue
        └── mismatch / unavailable → blocking finding
```

Phase K shall not silently substitute a newer policy version.

The Phase-J generation baseline is:

```text
CTX_SYSML_V2_TARGET_NOTATION        0.2.0
TURING_SYSML_V2_GENERATION         1.0.0
TURING_SYSML_V2_ARTIFACT_STRUCTURE 1.0.0
TURING_SYSML_V2_GENERATOR_RULES    1.0.0
```

A generated artifact whose exact generation policy cannot be resolved shall not
be publishable.

---

### K-06 — Standalone artifact-set boundary validation

Phase K shall independently validate the received Phase-J artifact contract
without requiring the original IEM snapshot.

Checks shall include at least:

- `GeneratedSysMLArtifactSet` content fingerprint,
- generated-unit content fingerprints,
- generation-input fingerprint,
- unit identity uniqueness,
- unit path uniqueness,
- safe relative paths,
- generated-symbol uniqueness,
- traceability-entry uniqueness,
- traceability unit references,
- traceability generated-symbol references,
- traceability line ranges,
- source-IEM identity consistency,
- element/relationship trace coverage consistency,
- controlled line-ending invariants,
- and textual-unit integrity.

This is a boundary check of received evidence.

It does not remove Phase J's responsibility to build correct artifacts.

---

### K-07 — Target Notation validation

Phase K shall confirm that generated output remains inside the exact permitted
Target Notation subset.

The internal validator shall validate the deliberately constrained Turing
Generator output forms rather than implement the complete SysML v2 grammar.

The MVP production subset currently includes generated forms for:

- Package,
- Documentation block,
- Requirement Usage,
- Use Case Definition,
- Action Usage,
- Part Usage,
- Dependency,
- Allocation,
- Satisfaction,
- and qualified references.

A generated construct outside the resolved Target Notation contract is blocking.

Full syntax/model interpretation remains the responsibility of external SYSIDE
validation.

---

### K-08 — Artifact Structure validation

The generated artifact set shall be checked against the exact resolved Artifact
Structure Profile.

For the current MVP this includes at least:

```text
one generated unit
unit id GSU-000001
relative path generated_model.sysml
root package GeneratedModel
complete configured Framework package hierarchy
configured empty packages retained
canonical Framework ordering
canonical element ordering
canonical relationship ordering
relationships placed at the configured root location
safe relative output paths
```

Phase K validates generated structure.

It shall not infer additional engineering containment.

---

### K-09 — Relationship and endpoint validation

Phase K shall validate generated relationship consistency independently of
Phase-J rendering.

For every generated relationship it shall validate, where deterministically
observable:

- the relationship construct is permitted,
- both referenced endpoints resolve,
- endpoint resolution is unambiguous,
- endpoint target constructs are compatible,
- endpoint element kinds are compatible,
- qualified endpoint references are valid,
- and required endpoint rendering/order is preserved.

The active production rules include:

```text
allocation
  source: Feature
  target: Feature

dependency / depends_on
  source: Feature or Definition
  target: Feature or Definition

satisfaction
  IEM semantic: source satisfies target
  generated form: satisfy TARGET by SOURCE
  source: PartUsage or ActionUsage Feature
  target: RequirementUsage Feature
```

Phase K validates generated-model consistency.

It shall not reinterpret the original IMR semantic intent.

The reviewed IEM semantic → target-construct mapping remains a Phase-J
generation responsibility.

---

### K-10 — Scope of semantic, constraint and comparability validation

The roadmap terms:

- relationship semantic validation,
- constraint validation,
- comparability-profile validation

shall be interpreted according to the accepted Phase-H/I/J authority boundaries.

Phase K validates publication-relevant generated-model consistency.

It shall not rerun Phase-H semantic interpretation or Human Review.

For the MVP:

#### Relationship semantic validation

Means confirming that the generated relationship is permitted by the pinned
Generation Profile and that endpoint roles are compatible with the target
construct.

#### Constraint validation

Means deterministic generated-artifact and target-policy constraints applicable
to publication.

It does not mean executing arbitrary product-design constraints or simulating
engineering behavior.

#### Comparability-profile validation

Means validating consistency of the pinned generation-policy chain with the
expected Model Structure / Comparability Profile and preservation of reviewed
exception traceability.

Candidate-level comparability decisions shall not be recomputed in Phase K.

---

### K-11 — Traceability validation

Every generated engineering representation must remain traceable.

Phase K shall validate that the transferred chain remains structurally complete:

```text
generated location
→ GeneratedSysMLTraceabilityEntry
→ source IEM
→ IME or IMR
→ Model Candidate
→ Approved Input
→ Human Review Decision
→ accepted exception where applicable
```

Every generated element and relationship representation shall have exactly one
applicable traceability entry.

Generated line locations remain one-based and inclusive.

A finding associated with a generated element or relationship shall reference
the existing Phase-J traceability key:

```text
generated_unit_id
+
generated_symbol_id
```

Findings applying to complete units or package structure may reference the unit
and generated location only.

---

### K-12 — Immutable normalized validation findings

Phase K shall produce immutable normalized findings.

Conceptually:

```python
SysMLValidationFinding(
    code=...,
    category=...,
    severity=...,
    blocking=...,
    message=...,
    generated_unit_id=...,
    generated_symbol_id=...,
    generated_location=...,
    validator_id=...,
    validator_rule_id=...,
)
```

Finding categories shall distinguish at least:

```text
artifact_integrity
validation_context
target_notation
artifact_structure
relationship_consistency
traceability
external_syntax
external_semantics
external_warning
validator_infrastructure
```

Severity shall use a controlled vocabulary:

```text
info
warning
error
```

`blocking` is explicit and controlled by the Validation Profile.

Findings shall have deterministic canonical ordering.

Recommended ordering:

```text
blocking first
→ category
→ generated unit
→ line
→ column where available
→ code
→ message
```

---

### K-13 — SYSIDE external-validator adapter

SYSIDE shall be integrated through a dedicated adapter rather than directly into
the Phase-K orchestration service.

Conceptually:

```text
SysMLExternalValidator
        ▲
        │
SysideCliValidator
```

The adapter shall receive the exact generated units and materialize an isolated
ephemeral validation workspace.

Generated units shall be written there byte-for-byte using their configured
relative paths.

The workspace shall contain no unrelated project models.

The adapter shall then execute a controlled, non-mutating SYSIDE validation
operation conceptually equivalent to:

```text
syside check
```

The concrete invocation shall use deterministic/noninteractive settings where
supported.

Temporary absolute filesystem paths shall not become part of deterministic
validation identity.

External diagnostics shall be normalized to generated-unit-relative locations.

---

### K-14 — External validator identity

Every external validation execution shall record the actual validator identity.

At least:

- validator ID,
- tool name,
- tool version,
- validation command contract,
- validator configuration fingerprint.

For SYSIDE, the installed version shall be discovered at execution time and
recorded.

The external-validator identity participates in the validation execution
fingerprint.

A different SYSIDE version therefore represents a materially different
validation environment.

---

### K-15 — Unavailable external validator is incomplete, never PASS

External validator infrastructure may be unavailable because, for example:

- SYSIDE CLI is not installed,
- required licensing is unavailable,
- the executable cannot start,
- the validator version is unsupported,
- execution crashes or times out,
- required standard-library context is unavailable.

Such states shall not be reported as `invalid`.

They shall also never be reported as `valid`.

Instead:

```text
validation_status = incomplete
publication_gate = blocked
```

with an explicit blocking `validator_infrastructure` finding.

This preserves the distinction between:

```text
invalid model
```

and:

```text
required validation could not be completed
```

while remaining fail-closed.

---

### K-16 — Three-state validation result

`SysMLValidationResult` shall support exactly three normative overall statuses:

```text
valid
invalid
incomplete
```

#### valid

All required internal checks completed.

All required external validators completed.

No blocking findings exist.

```text
publication_gate = passed
```

#### invalid

Validation completed sufficiently to establish one or more actual blocking
model/artifact defects.

```text
publication_gate = blocked
```

#### incomplete

A required validator or validation context could not be resolved or executed
sufficiently to establish validity.

```text
publication_gate = blocked
```

Only:

```text
validation_status == valid
AND
publication_gate == passed
```

is eligible for Phase L.

---

### K-17 — Warning policy

Internal and external warnings shall remain visible.

Warnings are not automatically equivalent to errors.

The Validation Profile determines whether a warning category or specific
validator rule blocks publication.

The MVP default policy is:

```text
SYSIDE warning
→ severity = warning
→ blocking = false
```

unless an explicit Turing validation rule elevates the finding.

Errors remain blocking.

The MVP shall therefore not globally use a
`warnings-as-errors` publication policy.

---

### K-18 — Deterministic validation identity and fingerprints

Phase K shall calculate an exact validation-input fingerprint from at least:

- `GeneratedSysMLArtifactSet.content_fingerprint`,
- Validation Profile reference and fingerprint,
- resolved external-validator identity/version,
- external-validator configuration fingerprint,
- validation command-contract identifier.

Conceptually:

```text
validation_input_fingerprint =
SHA256(
    artifact-set fingerprint
  + validation policy
  + resolved validator environment
)
```

If a required validator is unavailable, the resolved environment shall contain
an explicit unavailable state rather than omit validator identity.

The final `SysMLValidationResult.content_fingerprint` shall cover deterministic
result content including:

- validation-input fingerprint,
- validation status,
- publication gate,
- normalized findings,
- external-validator evidence,
- artifact-set reference,
- Validation Profile reference.

Deterministic validation identity shall not include:

- wall-clock timestamps,
- temporary workspace paths,
- execution duration,
- ANSI formatting,
- machine-specific absolute paths.

For identical artifact, validation policy, validator version/configuration and
normalized validation result, the same validation-result fingerprint shall be
produced.

---

### K-19 — No separate Phase-K persistence authority required for the MVP

Phase K does not require a separate mutable validation repository merely to
perform validation.

The normative Phase-K result is the immutable:

```text
SysMLValidationResult
```

Its cryptographic fingerprint is the validation-result identity transferred to
Phase L.

Phase L may persist the validation result/report together with the published
versioned output package.

A future validation-history repository may be added without changing the Phase-K
service boundary.

---

### K-20 — Deterministic human-readable validation report

The machine-readable `SysMLValidationResult` is the authoritative Phase-K
output.

A human-readable validation report may be projected deterministically from that
result.

It shall summarize at least:

- project identity,
- source IEM identity,
- source GeneratedSysMLArtifactSet fingerprint,
- Validation Profile identity,
- SYSIDE validator identity/version,
- internal validation status,
- external validation status,
- blocking findings,
- warnings,
- publication-gate result,
- traceability references.

The human-readable report is a projection.

It is not separate validation authority.

---

### K-21 — Exact fingerprint-bound Phase-L publication gate

Phase L shall accept only the exact artifact set covered by the successful
validation result.

Conceptually:

```python
OutputWriter.publish(
    artifact_set: GeneratedSysMLArtifactSet,
    validation_result: SysMLValidationResult,
)
```

Phase L must verify:

```text
validation_result.source_artifact_set_fingerprint
==
artifact_set.content_fingerprint
```

and:

```text
validation_result.validation_status == "valid"
validation_result.publication_gate == "passed"
```

A validation result for another artifact set shall never authorize publication.

Any modification of generated content invalidates the publication gate through
the artifact-set fingerprint.

---

### K-22 — Findings report likely resolution ownership

Validation findings may identify their likely resolution boundary without
automatically changing that boundary.

Examples:

```text
artifact fingerprint mismatch
→ corrupted/invalid Phase-J artifact transfer

Target Notation reference mismatch
→ generation-policy/reference issue

unsupported generated target form
→ Target Notation / Generation Profile / generator issue

package-layout mismatch
→ Artifact Structure / generator issue

unresolved relationship endpoint
→ generator / generated-artifact consistency issue

SYSIDE syntax error
→ generator or Target Notation syntax issue

SYSIDE semantic/type error
→ Generation Profile / endpoint mapping / generator issue

traceability mismatch
→ Phase-J artifact assembly issue

SYSIDE unavailable
→ validation infrastructure issue
```

Phase K reports the issue.

It does not repair engineering content.

---

### K-23 — Controlled larger-context compatibility

The MVP external validation workspace shall validate exactly the generated
artifact set plus the validator's controlled SysML standard-library context.

No unrelated repository model shall be loaded implicitly.

Future compatibility validation against additional target-model libraries or
larger engineering contexts may be added through versioned Validation Profile
configuration.

Additional context shall be explicitly pinned and fingerprinted.

Ambient filesystem discovery is not permitted as hidden validation authority.

---

### K-24 — No LLM in the normative validation path

The normative Phase-K path is deterministic/tool-based.

No LLM is required to:

- decide whether syntax is valid,
- determine endpoint compatibility,
- decide publication eligibility,
- repair invalid models,
- or reinterpret validation findings.

An LLM may later explain findings in a UI.

Such explanation remains non-authoritative and cannot alter the validation
result or publication gate.

---

## Phase-K Output Contract

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class SysMLValidationResult:
    schema_version: str

    project_id: str
    source_internal_engineering_model_id: str
    source_artifact_set_fingerprint: str

    validation_profile_reference: SysMLValidationProfileReference
    validation_input_fingerprint: str

    external_validator_evidence: (
        tuple[SysMLExternalValidationEvidence, ...]
    )

    findings: tuple[SysMLValidationFinding, ...]

    validation_status: str
    publication_gate: str

    content_fingerprint: str
```

A wall-clock timestamp is not required in the deterministic domain contract.

Operational publication/run metadata may record time independently without
changing validation identity.

---

## Normative Phase-K Flow

```text
GeneratedSysMLArtifactSet
        │
        ▼
Artifact-set boundary integrity
        │
        ▼
Resolve exact generation policy references
        │
        ▼
Resolve Validation Profile
        │
        ▼
Deterministic internal validation
        │
        ├── target notation
        ├── artifact structure
        ├── relationship/endpoints
        └── traceability
        │
        ▼
Materialize isolated temporary validation workspace
        │
        ▼
SYSIDE CLI adapter
        │
        ▼
Normalize external diagnostics
        │
        ▼
Merge + canonical-order findings
        │
        ▼
validation status
        │
        ├── valid
        ├── invalid
        └── incomplete
        │
        ▼
publication gate
        │
        ├── passed
        └── blocked
        │
        ▼
Immutable SysMLValidationResult
        │
        ▼
Phase L
```

---

## Initial Implementation Decomposition

After acceptance, the initial implementation decomposition is:

```text
K1  Validation domain foundation + Validation Profile
K2  Artifact/context/Target-Notation/Structure/Traceability validators
K3  Relationship + endpoint consistency validator
K4  SYSIDE CLI adapter + deterministic diagnostic normalization
K5  SysMLValidationService + status/gate/fingerprint assembly
K6  J→K→L boundary regression + Phase-K closeout
```

The SYSIDE integration path shall be tested separately from the fast
deterministic unit-test suite.

---

## Phase Boundaries

### Phase J owns

- IEM semantic → SysML construct mapping,
- rendering,
- escaping,
- package projection,
- canonical textual generation,
- generated traceability,
- `GeneratedSysMLArtifactSet` assembly.

### Phase K owns

- received artifact integrity,
- target-policy conformance,
- generated-model consistency,
- external SYSIDE compatibility,
- validation findings,
- validation identity,
- publication gate.

### Phase L owns

- version allocation,
- `data/output/` persistence,
- published package manifest,
- persisted validation evidence,
- immutable output references,
- downloadable/inspectable packaging.

---

## Explicit Non-Goals

Phase K shall not:

- reload Candidates to reinterpret them,
- change Human Review authority,
- mutate the IEM,
- regenerate SysML v2,
- repair generated text,
- run formatting that replaces generated content,
- invent missing model semantics,
- publish files,
- create implicit latest-artifact selection,
- silently skip external validation,
- treat validator unavailability as success,
- load ambient unrelated model context,
- replace SYSIDE with an ad-hoc regex implementation of the full SysML grammar.

---

## Consequences

### Positive

- Phase J, K and L remain cleanly separated.
- Validation is reproducible and fail-closed.
- External validator unavailability cannot accidentally authorize publication.
- Turing-specific invariants remain deterministic.
- Complete generated models receive actual SYSIDE compatibility validation.
- Validation findings remain exactly traceable to generated engineering
  evidence.
- Warning policy remains explicit rather than tool-dependent.
- The K→L gate is cryptographically bound to the exact validated artifact set.
- No semantic Human Review authority is reopened during validation.
- A future alternative external validator can be introduced behind the same
  adapter contract.

### Trade-offs

- Phase K gains its own versioned Validation Profile.
- External validation depends on available SYSIDE infrastructure.
- A valid internal result is insufficient for publication when required external
  validation cannot run.
- Validator versions become part of reproducibility evidence.
- Diagnostic normalization requires an explicit adapter layer.

---

## Acceptance

Accepted by the project owner on 2026-08-14 before Phase-K implementation.

The accepted key decisions are:

1. `GeneratedSysMLArtifactSet` is the sole normative Phase-K input.
2. Phase K combines deterministic internal checks with external SYSIDE
   validation.
3. Phase K introduces a separate versioned Validation Profile.
4. SYSIDE CLI is the MVP external-validation boundary.
5. Validation has `valid`, `invalid` and `incomplete` overall states.
6. Required-validator unavailability means `incomplete` and blocks publication.
7. Warnings remain visible but are not automatically publication-blocking.
8. Phase K does not reinterpret source-IEM or Candidate semantics.
9. Phase-L publication authority is fingerprint-bound to the exact successfully
   validated artifact set.
10. No separate Phase-K persistence layer is required for the MVP.
