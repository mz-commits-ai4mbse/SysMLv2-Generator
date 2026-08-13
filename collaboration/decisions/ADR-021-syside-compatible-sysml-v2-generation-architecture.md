# ADR-021 — SYSIDE-Compatible SysML v2 Generation Architecture

## Status

Accepted

## Date

2026-08-13

## Context

Phase H and the controlled H9 extension establish reviewed Model Candidates from
Approved Inputs.

Phase I assembles the exact human-authorized Candidate selection into one
immutable, representation-neutral Internal Engineering Model (IEM).

The current verified implementation baseline is:

`1cee49350dd2f24d6a1c80fb0aa1c0d2b5fd27fc`

Phase J now has one responsibility:

> deterministically serialize one explicitly selected, validated Internal
> Engineering Model snapshot into SysML v2 textual artifacts that are compatible
> with SYSIDE.

Phase J shall not repeat engineering interpretation.

Phase J shall not use an LLM to decide model meaning.

Phase J shall not use the CATIA model of the Turing Generator as a syntax
template for generated target models.

The Turing Generator's CATIA model describes the Turing Generator itself. It
remains the engineering authority for the product architecture and is relevant
to later Architecture-to-Requirements reconciliation, especially Phase N2. It
does not define the textual syntax that Phase J shall generate for arbitrary
target models.

The SysML v2 source/reference hierarchy for Phase J is instead:

```text
SysML v2 specification / release repository
        │
        │ primary language and syntax reference
        ▼
SYSIDE
        │
        │ target execution / validation environment
        ▼
validated local syntax experiments
        │
        │ implementation evidence for the supported subset
        ▼
Apollo 11 SysML v2 example project
        │
        │ non-normative structure / style reference only
        ▼
Turing Generator target-notation and generation profiles
```

The repository already records the local reference locations:

```text
external/sysml-v2-release/
external/apollo11-sysml-v2/
```

`context/sources/source_manifest.json` defines the SysML v2 Release repository
as the primary specification reference and Apollo 11 as a non-normative example
reference.

`context/sysml/sysml_v2_spec_reference.json` is a curated working reference. It
is intentionally not treated as the complete grammar and explicitly requires
consulting the local SysML v2 release repository and validating uncertain
syntax in the selected environment.

`context/examples/apollo11_structure_reference.md` records useful Apollo
organization and modeling patterns, but explicitly prevents Apollo from
overriding the SysML v2 specification or the Turing target notation.

The current target-notation artifact is:

`context/sysml/sysml_v2_target_notation.json`

Version:

`0.1.0`

It already constrains generation to a deliberately limited SysML v2 subset, but
its generation-state language predates the completed Phase-H/Phase-I
architecture. It still refers to `approved_model_data` as direct generation
input and associates generation directly with `data/output/`.

The accepted architecture is now:

```text
Approved Input
→ reviewed Model Candidates
→ Internal Engineering Model
→ Phase J generation
→ Phase K validation
→ Phase L publication
```

Therefore Phase J requires a clean serialization architecture that preserves
the IEM authority boundary, separates syntax policy from semantic mapping and
artifact organization, fails closed when a mapping is unsupported, and produces
an exact validation-ready artifact set for Phase K.

---

## Decision

### J-01 — Sole upstream authority

Phase J shall consume engineering-model content exclusively through:

```python
InternalModelReadService.load_phase_j_input(
    project_id,
    internal_engineering_model_id,
) -> InternalEngineeringModelSnapshot
```

The IEM shall be explicitly addressed.

No implicit "latest IEM" selection is allowed.

Phase-J generation shall not independently read Model Candidates, Approved
Inputs, Review persistence, raw ingestion artifacts or presentation state in
order to decide what model content is generated.

The Phase-I read boundary remains authoritative for the exact model snapshot
supplied to Phase J.

---

### J-02 — Deterministic serialization only

The normative Phase-J generation path shall be deterministic.

Phase J shall not use an LLM or agent to:

- reinterpret engineering meaning,
- choose between semantic alternatives,
- invent relationships,
- infer additional hierarchy,
- choose a target-model area,
- repair unsupported semantics,
- or generate free-form SysML v2 text.

Engineering interpretation occurs in Phase H/H9 and is authorized through Human
Review.

Phase I assembles that authorization without semantic reinterpretation.

Phase J is therefore a compiler/serializer from accepted internal semantics to a
controlled textual representation.

For identical:

- IEM content,
- target-notation reference,
- generation-profile reference,
- artifact-structure reference,
- and generator implementation/rule version,

the generated textual content shall be byte-identical.

---

### J-03 — Phase-J syntax and reference authority hierarchy

Phase J shall apply the following hierarchy when defining or extending generated
SysML v2 syntax:

1. local SysML v2 specification/release repository
2. successful validation in SYSIDE
3. intentionally maintained local syntax fixtures/experiments
4. Apollo 11 as a non-normative example reference
5. project-specific style preferences

The local SysML v2 release repository remains the primary language and syntax
reference.

SYSIDE is the target environment against which the generated subset shall be
validated.

Apollo 11 may inform:

- package organization,
- separation of definitions and usages,
- naming style,
- large-model structuring,
- and examples of valid modeling patterns.

Apollo 11 shall not override the specification reference or a SYSIDE validation
result.

---

### J-04 — CATIA remains separate from the Phase-J syntax authority

The CATIA model of the Turing Generator is the engineering model of the Turing
Generator product itself.

It may define or constrain what the Turing Generator shall be capable of doing.

It shall not be used as the normative textual syntax source for Phase J.

In particular:

```text
CATIA Turing Generator model
→ product requirements / functions / logical architecture
→ Phase-N2 reconciliation authority

SysML v2 specification + SYSIDE
→ generated language / syntax authority for Phase J
```

A future independent CATIA example model may be used as an interoperability test
case.

Such a model shall remain non-normative for the Phase-J syntax mapping unless a
later accepted architecture decision explicitly changes that rule.

---

### J-05 — Three separate versioned generation-policy artifacts

Phase J shall separate three concerns that are currently partially mixed.

#### Target Notation Profile

Path:

`context/sysml/sysml_v2_target_notation.json`

Responsibility:

> Which SysML v2 textual constructs are allowed to be generated?

The target notation defines the permitted language subset and syntax patterns.

It shall not decide which IEM semantic maps to which construct.

It shall not decide file/package organization.

The current `0.1.0` artifact shall be intentionally revised during J1 before it
is used as the production Phase-J target-notation contract.

The revision shall update stale pre-H/I generation-state language and preserve
the principle:

> Reduce MVP scope by limiting the generated SysML v2 subset, not by accepting
> invalid syntax.

#### Generation Profile

Proposed path:

`context/sysml/turing_sysml_v2_generation_profile.json`

Responsibility:

> How is each supported IEM semantic represented using allowed target-notation
> constructs?

It shall define explicit mappings for:

- IEM element types,
- model areas where required to disambiguate representation,
- relationship family,
- semantic intent,
- directionality,
- permitted attribute projections,
- documentation projection,
- and accepted-exception representation.

#### Artifact Structure Profile

Proposed path:

`context/sysml/turing_sysml_v2_artifact_structure.json`

Responsibility:

> How is one generated model organized into output units, packages, names and
> deterministic ordering?

It shall define at least:

- root-package policy,
- Framework-node → package projection,
- default output-unit strategy,
- package naming,
- deterministic ordering,
- relative output path rules,
- and future multi-file extensibility.

These three references shall be independently versioned and fingerprinted.

---

### J-06 — Exact generation context is pinned

Every Phase-J generation attempt shall bind the exact:

- source IEM identity and content fingerprint,
- Target Notation Profile identity/version/fingerprint,
- Generation Profile identity/version/fingerprint,
- Artifact Structure Profile identity/version/fingerprint,
- generator-rule/implementation reference where applicable.

Generation shall not silently load a newer profile after an artifact set has
been created.

The exact generation context shall be sufficient to reproduce the generated
content.

---

### J-07 — Preflight mapping completeness before rendering

Phase J shall perform deterministic generation preflight before producing a
successful artifact set.

The preflight shall verify at least:

- IEM snapshot integrity has already passed the I→J boundary,
- every materialized Framework node has a deterministic package projection,
- every used IEM `element_type` has one applicable explicit mapping rule,
- every used relationship semantic has one applicable explicit mapping rule,
- mapping rules reference only allowed target-notation constructs,
- relationship directionality is supported by the selected mapping,
- every IMR endpoint resolves to a generated IME symbol,
- generated symbols are unique,
- names and documentation can be safely serialized,
- accepted exceptions remain representable and traceable,
- and the requested artifact structure can be rendered without an implicit
  semantic choice.

Any missing or ambiguous required mapping is blocking.

Phase J shall not partially succeed by silently omitting unsupported IEM
content.

---

### J-08 — Unsupported semantics fail closed

An unsupported IEM semantic shall produce an explicit blocking generation
finding.

Examples include:

- unsupported element type,
- unsupported relationship semantic intent,
- unsupported directionality,
- target construct not allowed by the pinned Target Notation Profile,
- or a semantic mapping that would require a new engineering decision.

Phase J shall not apply a generic fallback such as:

```text
unknown relationship
→ dependency
```

merely to produce syntactically valid output.

Phase J shall not replace a required formal relationship with a documentation
note when doing so would change or discard the accepted engineering semantics.

Resolution belongs to the relevant upstream profile, modeling decision or target
notation extension.

---

### J-09 — Target-notation extension requires validated syntax evidence

A new SysML v2 construct shall not become generator output merely because a
plausible syntax pattern is known.

Before a previously unsupported construct is activated in the Target Notation
Profile, J1 shall:

1. identify the required semantic and construct,
2. inspect the local SysML v2 release/specification material,
3. create the smallest useful local syntax fixture,
4. validate the fixture in SYSIDE,
5. record the accepted syntax pattern,
6. add the construct to the Target Notation Profile,
7. add its mapping to the Generation Profile,
8. add automated regression tests.

This applies especially to currently unresolved Phase-J needs such as:

- Use Case representation,
- allocation,
- dependency variants,
- derivation,
- refinement,
- satisfaction,
- interaction,
- flow,
- and traceability relationships.

No construct shall be guessed from its English name.

---

### J-10 — Framework structure projects deterministically to package structure

The materialized `InternalModelStructure` is organizational structure already
authorized by Phase I.

Phase J may project that exact structure into SysML v2 packages without
inventing engineering hierarchy.

The default structure shall retain:

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

Package names are a textual representation of the pinned Framework structure.

They are not additional engineering elements.

Phase J shall not infer additional containment from:

- names,
- IME ordering,
- element similarity,
- relationship proximity,
- or convenience.

---

### J-11 — Empty configured structure may remain explicit

The default artifact-structure profile may render the complete configured
Framework skeleton, including empty nodes, as packages.

This supports structural comparability across generated model snapshots.

An empty package shall not be interpreted as proof that the corresponding
engineering scope is complete.

If a later Artifact Structure Profile chooses to omit empty packages, that
behavior shall be explicit, versioned and deterministic.

---

### J-12 — Default MVP output uses one SysML v2 unit

The domain contract shall permit one or more generated units.

The default MVP Artifact Structure Profile shall initially generate one `.sysml`
text unit containing the complete package hierarchy.

Reason:

- minimizes fragile cross-file references,
- provides one simple validation target,
- keeps the first closed vertical slice small,
- and preserves future extensibility through the artifact-set abstraction.

The architecture therefore supports:

```text
GeneratedSysMLArtifactSet
├── Unit 1
├── Unit 2
└── ...
```

while the initial profile selects:

```text
GeneratedSysMLArtifactSet
└── generated_model.sysml
```

A later multi-file profile shall not require redesigning the IEM or generation
domain model.

---

### J-13 — Element mapping is explicit and profile-controlled

Every generated engineering element shall originate from exactly one IEM element
and one applicable Generation Profile rule.

The profile may distinguish identical `element_type` values by `model_area`.

This is required because, for example, `function` is used for both:

- `system.functional`
- `subsystem.functional`

The generator shall not infer representation from an element name.

Likely MVP families include:

```text
requirements         → requirement constructs
functions            → action constructs
logical components   → part constructs
physical components  → part constructs
```

However, exact mappings become normative only after their Target Notation
constructs and SYSIDE syntax patterns are validated and recorded.

Stakeholders, User Needs and Use Cases shall likewise receive explicit validated
rules before production generation.

---

### J-14 — Stable generated symbols are separate from engineering names

Each generated IEM element shall receive a deterministic machine-safe generated
symbol derived from immutable internal identity, not from a potentially mutable
or colliding display name.

Conceptually:

```text
IME-000042
→ IME_000042
```

The exact textual symbol pattern shall be specified in the Artifact Structure or
Generation Profile and validated against SYSIDE identifier rules.

The engineering `name` remains a separate human-readable property.

Phase J shall not make technical identity depend solely on:

- display-name uniqueness,
- capitalization,
- whitespace,
- punctuation,
- or automatic name normalization.

This preserves stable relationship endpoint references even when engineering
names are similar.

---

### J-15 — Untrusted text is escaped and never inserted raw

IEM names, descriptions and generic attributes may originate from heterogeneous
legacy information.

Phase J shall treat them as data, not as trusted SysML v2 syntax.

The renderer shall have explicit deterministic escaping/sanitization rules for:

- generated identifiers,
- quoted names where used,
- documentation blocks,
- line breaks,
- comment delimiters,
- and other syntax-sensitive characters.

No source-provided text may inject additional SysML v2 statements through raw
string concatenation.

If text cannot be represented under the selected rule set without loss or
ambiguity, generation shall fail closed with a finding.

---

### J-16 — Generic IEM attributes are not automatically formal SysML attributes

`InternalModelElement.attributes` contains generic name/value data.

Phase J shall not blindly transform every generic pair into formal SysML v2
attribute syntax.

The Generation Profile shall distinguish:

```text
explicitly supported formal attribute
→ formal target construct

generic metadata / trace information
→ documentation and/or machine-readable traceability

unsupported semantic attribute
→ blocking finding when omission would lose engineering meaning
```

This prevents arbitrary legacy metadata from silently becoming formal model
semantics.

---

### J-17 — Relationship serialization preserves accepted semantics exactly

Every generated relationship shall originate from exactly one IEM relationship.

The renderer shall preserve the accepted distinction between:

- `relationship_family`
- `semantic_intent`
- `directionality`

The Generation Profile shall map an exact supported tuple to an exact
Target-Notation construct.

Conceptually:

```text
(
    relationship_family,
    semantic_intent,
    directionality,
)
→ one explicit rendering rule
```

A different SysML construct may not be substituted merely because it looks
similar.

Phase J shall not alter relationship direction to simplify rendering.

---

### J-18 — Accepted exceptions remain explicit

An accepted exception in the IEM remains an accepted reviewed deviation.

Phase J shall not normalize it away.

The generated artifact set shall preserve exact traceability to the associated
Human Review Decision.

Where the selected target notation supports a faithful formal representation,
the content may be rendered normally while the exception remains explicit in
traceability.

If the accepted exception cannot be represented without semantic loss, Phase J
shall fail closed.

---

### J-19 — Deterministic ordering and formatting

Generated content shall have one canonical deterministic ordering.

The default ordering shall derive only from stable configured or internal
information such as:

1. Artifact Structure Profile order
2. Framework node order
3. IEM element identity
4. IEM relationship identity

The renderer shall not depend on:

- filesystem enumeration order,
- dictionary insertion from uncontrolled input,
- current timestamp,
- random values,
- LLM response order,
- or locale-specific sorting.

Formatting shall be canonical so that exact regeneration can be compared
byte-for-byte.

---

### J-20 — Machine-readable traceability accompanies the SysML v2 text

Phase J shall produce structured traceability together with textual SysML v2.

Each generated element/relationship trace entry shall support the chain:

```text
generated unit / symbol / location
→ IME or IMR
→ source MCE or MCR
→ Approved Input reference(s)
→ Candidate Human Review Decision
→ accepted exception where applicable
```

Traceability shall not rely only on human-readable `doc` text.

The generated SysML v2 text may contain concise traceability documentation when
allowed by the profile, but the machine-readable traceability artifact remains
the exact Phase-J evidence boundary.

Where practical, trace entries may include deterministic line ranges after
rendering.

---

### J-21 — Generated artifact set is a distinct immutable domain contract

A successful Phase-J generation returns one immutable
`GeneratedSysMLArtifactSet`.

Conceptually it shall contain at least:

```text
schema_version
project_id
source_internal_engineering_model_id
source_iem_content_fingerprint

target_notation_reference
generation_profile_reference
artifact_structure_reference

generation_input_fingerprint
generation_provenance

units[]
traceability_entries[]
nonblocking_diagnostics[]

content_fingerprint
```

Each generated unit shall contain at least:

```text
unit_id
relative_path
content
content_fingerprint
generated_symbol_ids
source_ime_ids
source_imr_ids
```

The artifact-set fingerprint shall bind the complete successful generated state.

Timestamps, temporary paths and other non-semantic runtime metadata shall not
affect deterministic generation identity.

---

### J-22 — Exact generation identity and idempotence

Phase J shall calculate a deterministic `generation_input_fingerprint` covering
at least:

- exact source IEM identity and fingerprint,
- exact Target Notation Profile reference/fingerprint,
- exact Generation Profile reference/fingerprint,
- exact Artifact Structure Profile reference/fingerprint,
- exact generator rules/implementation reference required for reproducibility.

The same exact generation identity shall produce byte-identical artifact
content and artifact fingerprints.

Phase J shall not silently select newer profiles under the same prior generation
identity.

---

### J-23 — Generation findings are explicit and typed

Phase J shall expose structured generation findings rather than embedding all
errors in exception strings.

A finding shall support at least:

```text
code
message
issue_level
target_type
target_id
profile_rule_id
blocking
```

Expected finding families include:

```text
UNSUPPORTED_ELEMENT_MAPPING
UNSUPPORTED_RELATIONSHIP_MAPPING
UNSUPPORTED_DIRECTIONALITY
TARGET_CONSTRUCT_NOT_ALLOWED
UNRENDERABLE_IDENTIFIER
UNSAFE_DOCUMENTATION_CONTENT
DUPLICATE_GENERATED_SYMBOL
UNRESOLVED_GENERATED_ENDPOINT
STRUCTURE_PROJECTION_ERROR
PROFILE_REFERENCE_MISMATCH
```

A blocking finding prevents a successful `GeneratedSysMLArtifactSet`.

---

### J-24 — Phase J validates generation integrity, not full SysML correctness

Phase J owns deterministic generation-integrity checks, including:

- complete mapping coverage,
- allowed-construct use,
- symbol uniqueness,
- endpoint resolvability,
- deterministic package membership,
- canonical formatting,
- and internal traceability completeness.

Phase J does not replace Phase K.

In particular, Phase J does not claim full validation merely because the
renderer emitted text matching an expected template.

---

### J-25 — Explicit Phase-J → Phase-K boundary

The successful output of Phase J is the immutable
`GeneratedSysMLArtifactSet`.

Conceptually Phase K consumes it through:

```python
SysMLValidationService.validate(
    artifact_set: GeneratedSysMLArtifactSet,
) -> SysMLValidationResult
```

The exact Phase-K service contract may be refined in the Phase-K architecture
decision, but Phase J shall expose all data required for:

- SYSIDE syntax/parser validation,
- reference resolution,
- Target Notation Profile conformance,
- structural validation,
- semantic validation where applicable,
- traceability validation,
- and publication-blocking findings.

Phase K shall not silently rewrite generated text to make validation pass.

---

### J-26 — SYSIDE validation belongs to Phase K, while J1 provides syntax evidence

There is an intentional distinction between:

#### J1 syntax experiments

Small controlled fixtures used to establish supported generator patterns before
a mapping is activated.

and:

#### Phase K product validation

Validation of an actual complete generated artifact set.

Therefore:

- J1 may use SYSIDE to validate candidate syntax patterns.
- Phase J production does not claim an artifact is valid merely because its
  individual templates were previously validated.
- Phase K validates the actual generated result.

---

### J-27 — Phase L alone performs final publication

Phase J shall not publish final generated output directly to `data/output/`.

Phase J creates the validation-ready artifact-set contract.

Phase K validates it.

Phase L owns final versioned publication of accepted generated output.

The existing Source Manifest rule that generated SysML v2 output belongs in:

`data/output/`

remains valid for the final published product artifact.

It does not require Phase J to bypass validation and publish directly.

The closed path is:

```text
IEM
→ Phase J GeneratedSysMLArtifactSet
→ Phase K SysMLValidationResult
→ Phase L versioned data/output/ publication
```

---

### J-28 — Generated output is not the Turing Generator architecture model

Generated customer/target-model output and the engineering model of the Turing
Generator are separate artifact classes.

Phase J shall never overwrite or treat as target output:

- the CATIA model of the Turing Generator,
- its textual export,
- or the temporary SYSIDE shadow model of the Turing Generator.

Generated model output belongs to the project/output publication boundary
defined downstream.

---

### J-29 — No hidden semantic fallback through documentation

Documentation blocks are allowed for:

- descriptions,
- rationale,
- traceability,
- assumptions,
- review references,
- and metadata explicitly designated as documentation.

Documentation shall not be used as a hidden fallback to claim that an
unsupported formal semantic has been preserved.

Example:

```text
accepted IMR = satisfies
```

If the active Generation Profile requires a formal `satisfies` representation
and no validated supported target construct exists, writing:

```text
doc /* A satisfies B */
```

does not count as successful semantic serialization.

The generation is blocked until the mapping is explicitly supported or the
upstream modeling decision changes.

---

### J-30 — Quality is reduced by subset, not by semantic loss

The Phase-J MVP may support only a controlled subset of SysML v2.

It may therefore block generation of an IEM that requires unsupported constructs.

It shall not claim success by:

- dropping accepted elements,
- dropping accepted relationships,
- weakening relationship types,
- flattening engineering semantics,
- inventing equivalent-looking constructs,
- or embedding unsupported model meaning only in prose.

A smaller valid and faithful supported subset is preferred over broader
apparently successful but semantically lossy output.

---

## Initial generation-domain contracts

The following contracts are proposed for Phase J.

### TargetNotationReference

Pinned identity of the active Target Notation Profile.

At least:

```text
context_id
version
content_fingerprint
```

### SysMLGenerationProfileReference

Pinned identity of the IEM → SysML semantic mapping profile.

At least:

```text
profile_id
profile_version
profile_fingerprint
```

### SysMLArtifactStructureReference

Pinned identity of the artifact/package layout profile.

At least:

```text
profile_id
profile_version
profile_fingerprint
```

### SysMLGenerationContext

At least:

```text
target_notation_reference
generation_profile_reference
artifact_structure_reference
generator_rules_reference
```

### SysMLGenerationFinding

At least:

```text
code
message
issue_level
target_type
target_id
profile_rule_id
blocking
```

### GeneratedSysMLUnit

At least:

```text
unit_id
relative_path
content
content_fingerprint
generated_symbol_ids
source_internal_model_element_ids
source_internal_model_relationship_ids
```

### GeneratedSysMLTraceabilityEntry

At least:

```text
generated_unit_id
generated_symbol_id
generated_location

source_internal_engineering_model_id
source_internal_model_element_id | null
source_internal_model_relationship_id | null

source_model_candidate_id
approved_input_references
review_decision_reference
accepted_exception_reference | null
```

### GeneratedSysMLArtifactSet

At least:

```text
schema_version
project_id

source_internal_engineering_model_id
source_iem_content_fingerprint

generation_context
generation_input_fingerprint
generation_provenance

units
traceability_entries
nonblocking_diagnostics

content_fingerprint
```

---

## Generation flow

The normative Phase-J production flow is:

```text
InternalModelReadService
        │
        ▼
validated explicit InternalEngineeringModelSnapshot
        │
        ▼
Generation Context Resolver
        │
        ├── Target Notation Profile
        ├── Generation Profile
        └── Artifact Structure Profile
        │
        ▼
Generation Preflight
        │
        ├── mapping completeness
        ├── construct allow-list
        ├── symbol planning
        ├── escaping/renderability
        └── endpoint planning
        │
        ▼
Package Projection
        │
        ▼
Element Rendering
        │
        ▼
Relationship Rendering
        │
        ▼
Traceability Projection
        │
        ▼
Canonical Unit Formatting
        │
        ▼
Immutable GeneratedSysMLArtifactSet
        │
        ▼
Phase K validation
```

No LLM exists in this production flow.

---

## Reference and validation flow for new syntax

When Phase J requires a construct not yet supported by the active target
notation:

```text
required IEM semantic
        │
        ▼
inspect local SysML v2 release repository
        │
        ▼
smallest useful syntax fixture
        │
        ▼
validate fixture in SYSIDE
        │
   ┌────┴────┐
   │         │
 valid     invalid
   │         │
   ▼         ▼
record      do not activate
pattern     mapping
   │
   ▼
extend Target Notation Profile
   │
   ▼
extend Generation Profile
   │
   ▼
automated generator regression
```

Apollo 11 may be consulted to find representative usage patterns, but it does
not replace the specification/SYSIDE validation steps.

---

## Default artifact structure

The initial MVP profile shall target conceptually:

```text
generated_model.sysml

package GeneratedModel {
    package StakeholderLevel {
        package Stakeholders { ... }
        package UserNeeds { ... }
        package StakeholderRequirements { ... }
        package UseCases { ... }
    }

    package SystemLevel {
        package Requirements { ... }
        package Functional { ... }
        package Logical { ... }
        package Physical { ... }
    }

    package SubsystemLevel {
        package Requirements { ... }
        package Functional { ... }
        package Logical { ... }
        package Physical { ... }
    }
}
```

The example is architectural and not yet an accepted literal syntax fixture.

Exact package identifier/quoting rules shall be established through the
Target-Notation and Artifact Structure Profiles.

---

## Relationship to existing context artifacts

### `context/sources/source_manifest.json`

Continues to define:

- SysML v2 release repository as the primary specification reference,
- Apollo 11 as non-normative example reference,
- generated output as a distinct artifact class.

### `context/sysml/sysml_v2_spec_reference.json`

Remains the compact working reference for routine implementation.

It is not the complete grammar.

Uncertain or newly required constructs trigger direct reference to the local
SysML v2 release repository.

### `context/sysml/sysml_v2_target_notation.json`

Becomes the Phase-J allowed-construct contract.

J1 shall revise the current `0.1.0` profile before production generation.

### `context/examples/apollo11_structure_reference.md`

Remains a non-normative structure/style reference.

No Apollo engineering content, CoSMA framework or package hierarchy becomes
Turing output policy merely because it appears in Apollo.

### CATIA Turing Generator model

Remains the engineering authority for the Turing Generator product.

It is not a Phase-J target-syntax reference.

Any capability gaps introduced or discovered during J–L are recorded for later
Phase-N2 Architecture-to-Requirements reconciliation.

---

## Persistence and publication boundary

Phase J creates a deterministic immutable artifact-set value.

A successful Phase-J result is not yet final published output.

Diagnostic implementations may serialize temporary artifacts for tests or
run-owned evidence, but such files do not become final generated product
artifacts merely because they exist on disk.

Final product publication remains Phase L after required Phase-K validation.

`data/output/` is therefore the final published generated-output location, not a
reason to bypass the validation boundary.

---

## Phase-J implementation slices

The accepted implementation decomposition after this ADR is intended to be:

```text
J1  Generation foundation
    - errors and identifiers
    - immutable generation domain contracts
    - profile references / fingerprints
    - Target Notation 0.2 cleanup
    - controlled syntax fixtures for currently required unsupported constructs

J2  Generation profiles and preflight
    - Generation Profile
    - Artifact Structure Profile
    - deterministic profile loaders
    - mapping completeness
    - construct allow-list validation
    - blocking generation findings

J3  Package, symbol and canonical ordering projection
    - Framework structure → packages
    - stable generated symbols
    - deterministic naming / escaping
    - canonical ordering

J4  Element rendering
    - explicit element mapping rules
    - safe documentation projection
    - supported attribute projection
    - element traceability

J5  Relationship rendering
    - explicit relationship semantic mapping
    - directionality
    - exact generated endpoint binding
    - no generic fallback

J6  Artifact-set and traceability assembly
    - GeneratedSysMLUnit
    - GeneratedSysMLTraceabilityEntry
    - GeneratedSysMLArtifactSet
    - deterministic generation fingerprints
    - exact regeneration/idempotence tests

J7  Phase-K boundary and completion
    - explicit validation handoff
    - H9/I→J compatibility regression
    - full repository regression
    - SSOT update
    - Phase-N2 reconciliation candidate recording
```

The slices may be internally subdivided without changing the accepted
architecture.

---

## Phase-J acceptance criteria

Phase J is complete only when:

- one explicit validated IEM can be generated without bypassing the I→J boundary,
- generation is deterministic and requires no LLM,
- every generated construct is allowed by the pinned Target Notation Profile,
- every rendered IEM semantic is covered by one explicit Generation Profile rule,
- unsupported required semantics fail closed,
- no accepted IEM element or relationship disappears silently,
- source-provided text cannot inject SysML syntax,
- generated relationships bind exact generated endpoints,
- machine-readable IEM → generated-artifact traceability is complete,
- repeated exact generation is byte-identical,
- the artifact set is suitable for Phase-K validation,
- J does not publish final output directly,
- representative supported syntax patterns have SYSIDE validation evidence,
- focused Phase-J tests pass,
- the complete repository regression passes,
- `git diff --check` passes,
- and SSOT is synchronized.

---

## Consequences

### Positive consequences

- Human-reviewed engineering semantics remain authoritative.
- Phase J is reproducible and testable.
- LLM variability cannot alter generated syntax or model meaning.
- SYSIDE compatibility becomes an explicit target rather than an assumed
  by-product.
- SysML v2 specification authority remains separate from example-project style.
- Apollo 11 remains useful without becoming normative.
- The CATIA Turing Generator model is no longer conflated with target syntax.
- Unsupported semantics are visible instead of silently weakened.
- Target notation, semantic mapping and artifact layout can evolve independently.
- The same IEM may later be serialized using a different accepted artifact
  structure without re-running semantic interpretation.
- The generated artifact set provides a precise input to Phase K.
- Final publication remains protected by Phase K and Phase L.

### Trade-offs

- Phase J introduces additional versioned profiles.
- Not every IEM may initially be generatable with the limited MVP subset.
- New semantic constructs require explicit syntax experiments and SYSIDE
  validation.
- One-file MVP output favors robustness over immediate large-project modularity.
- Stable generated symbols may be less visually elegant than display-name-based
  identifiers but provide stronger identity and endpoint stability.
- Maintaining machine-readable traceability adds artifact volume.
- Strict failure on unsupported semantics may require target-notation/profile
  extensions before a complete model can be generated.

These trade-offs are accepted because the objective is valid, faithful,
traceable SYSIDE-compatible SysML v2 generation rather than broad but lossy
text emission.

---

## Alternatives considered

### Alternative A — LLM generates SysML v2 directly from the IEM

Rejected.

Reason:

- creates a second semantic interpretation step after Human Review,
- reduces reproducibility,
- complicates validation,
- can silently alter accepted relationship meaning,
- increases token/request use,
- and makes exact regeneration difficult.

### Alternative B — Generate directly from Model Candidates

Rejected.

Reason:

- bypasses the accepted Phase-I authority boundary,
- duplicates internal-model assembly responsibilities,
- and risks generation from content outside the exact IEM snapshot.

### Alternative C — Use Apollo 11 as the syntax template

Rejected.

Reason:

- Apollo 11 is intentionally non-normative,
- contains domain- and methodology-specific patterns,
- and shall not override the SysML v2 specification or SYSIDE validation.

### Alternative D — Use the Turing Generator CATIA model as the generator syntax template

Rejected.

Reason:

- it models the Turing Generator product,
- it is not the normative source for target-model textual syntax,
- and conflating product architecture with serialization policy would create a
  false authority relationship.

### Alternative E — Emit generic dependencies for unsupported relationships

Rejected.

Reason:

- syntactic success would hide semantic loss,
- accepted Human Review meaning would be altered downstream,
- and generated output would no longer faithfully represent the IEM.

### Alternative F — Write directly to `data/output/` in Phase J

Rejected.

Reason:

- bypasses the planned validation/publication separation,
- conflates generated work product with accepted published artifact,
- and weakens the Phase-K/Phase-L gates.

### Alternative G — Start immediately with many separate `.sysml` files

Deferred.

Reason:

- increases cross-file reference complexity before the base mapping is proven,
- broadens the first SYSIDE validation surface,
- and is unnecessary for the initial closed vertical slice.

The artifact-set contract deliberately leaves multi-file generation open for a
later Artifact Structure Profile.

---

## CATIA / Phase-N2 reconciliation

This ADR makes an implementation-architecture decision for Phase J.

It does not modify the CATIA model.

Capabilities or constraints that may require CATIA Requirement/Function
reconciliation shall be recorded during implementation and reconciled in Phase
N2 together with the other G–L architecture changes.

Potential N2 reconciliation topics introduced or made explicit by ADR-021
include:

- deterministic generation from the validated Internal Engineering Model,
- explicit SYSIDE-compatible target-notation generation,
- versioned semantic-to-SysML generation profiles,
- fail-closed unsupported semantic behavior,
- machine-readable generated-artifact traceability,
- deterministic generation identity/idempotence,
- and separation of generation, validation and publication.

No SYSR, SF, Logical Component or allocation is created or changed by this ADR.

---

## Decision state after acceptance

After explicit acceptance of ADR-021:

```text
Phase H/H9: COMPLETE
Phase I:    COMPLETE
ADR-021:    ACCEPTED
Phase J:    architecture accepted
Next:       J1 — Generation foundation and validated syntax-fixture preparation
```

No Phase-J implementation begins before explicit acceptance of this ADR.
