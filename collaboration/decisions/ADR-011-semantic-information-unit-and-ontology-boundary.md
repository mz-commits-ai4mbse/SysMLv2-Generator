# ADR-011

Semantic Information Unit and Ontology Boundary

Status

Accepted

Date

2026-07-22

Context

Phase P introduces project-oriented processing around the completed Phase F
agentic ingestion pipeline.

P1 implemented the accepted Stakeholder, System and Subsystem framework.

P2 implemented the persistent Project Workspace.

P3 implemented the Project Source Registry with mandatory project assignment,
immutable original sources and explicit source roles.

P4 shall transform registered textual engineering sources into heterogeneous,
source-traceable Information Units and map them to valid nodes of the accepted
framework.

ADR-009 limits the MVP to textual information. Binary document containers may
be supported only when their relevant textual content can be projected
deterministically into a traceable textual representation.

ADR-010 establishes that the Source Registry remains format-neutral and does
not perform text projection, semantic interpretation, ontology mapping or LLM
processing.

P4 therefore requires explicit architecture decisions for:

- deterministic source projection
- semantic extraction
- Information Unit identity and atomicity
- information classification
- terminology and ontology references
- project-specific terminology
- framework mapping
- multiagent consensus and confidence
- immutable semantic persistence
- boundaries to P5, P6 and Phase G

No universal ontology is treated as an implicit or complete MBSE gold standard.

The selected reference architecture combines:

- SysML v2 and KerML semantics
- BFO 2020
- IOF Core
- a curated Turing Core Vocabulary
- a human-reviewed Project Glossary

External reference systems shall support semantic consistency without replacing
the accepted project framework or the authoritative engineering model.

Decision

## Semantic Processing Stages

P4 separates the semantic workflow into four stages.

### P4.1 — Deterministic Source Projection

A registered source is converted into a deterministic, traceable textual
representation.

This stage performs no semantic interpretation.

### P4.2 — LLM Semantic Extraction

Independent persona agents identify candidate Information Units from the
deterministic Source Projection.

### P4.3 — Terminology and Ontology Candidate Mapping

Extracted terminology is compared with:

- accepted Project Glossary concepts
- the Turing Core Vocabulary
- selected IOF Core and BFO concepts

All mappings remain explicit and traceable.

### P4.4 — Framework Mapping

Information Units are mapped to zero, one or multiple valid nodes of the
accepted framework template.

Framework mapping produces candidates. It does not perform Engineering
Approval.

## Artifact Separation

P4 distinguishes the following artifact types.

### Source Projection

A Source Projection is a deterministic textual representation of one registered
source.

It does not contain semantic interpretations.

### Information Unit

An Information Unit is the smallest independently understandable,
source-traceable professional statement that:

- was semantically extracted from an engineering source
- expresses one independently reviewable main claim
- can be independently classified
- can be independently reviewed
- can be independently mapped to the framework

### Terminology Concept

A Terminology Concept represents a controlled project or reference-system
meaning.

It is not an engineering statement and does not create framework coverage.

### Framework Assignment

A Framework Assignment connects exactly one Information Unit to exactly one
valid mapping target of a specific framework-template version.

These artifact types shall not be merged into one mutable record.

## Source-Role Boundary

Only a source with the role:

`engineering_source`

may create:

- engineering Information Units
- Framework Assignments
- preliminary engineering coverage

A source with the role:

`context_only`

may create:

- a Source Projection
- terminology candidates
- candidate definitions
- candidate explanations
- Project Glossary provenance

A context-only source shall not create:

- engineering Information Units
- Framework Assignments
- preliminary coverage
- approved readiness
- model-generation input

Terminology extracted from a context-only source remains visibly traceable to
that source.

## Information Unit Identity

Every Information Unit receives an immutable project-local identifier named
`information_unit_id`.

The identifier:

- is stored as a JSON string
- matches `^IU-[0-9]{6}$`
- is unique within one project
- is allocated sequentially
- is not reused
- remains unchanged for the lifetime of the Information Unit

Valid examples include:

- `IU-000001`
- `IU-004281`
- `IU-999999`

The globally unambiguous reference is the pair:

```text
<project_id>/<information_unit_id>
```

Example:

```text
318604/IU-000001
```

The two identifiers remain separate stored fields.

The display form does not replace the individual identifiers.

## Information Unit Immutability

The following Information Unit content is immutable after persistence:

- Information Unit identity
- project reference
- source reference
- Source Projection reference
- source anchors
- source excerpt
- interpreted statement
- information classification
- extraction provenance

If later processing produces a materially changed interpretation, it creates a
new Information Unit with a new identifier.

An existing Information Unit shall not be silently rewritten.

P5 may later record that one Information Unit supersedes or invalidates another.
Such lifecycle information remains separate from the immutable Information Unit.

## Information Unit Atomicity

An Information Unit contains exactly one independently reviewable main claim.

Independent obligations shall be split into separate Information Units.

Conditions, qualifiers and limits that are necessary to understand one claim
remain attached to that claim.

An Information Unit belongs to exactly one engineering source.

It may reference multiple anchors within that source.

P4 shall not synthesize one Information Unit from multiple sources.

Equivalent or overlapping claims from different sources remain separate
Information Units.

They may be linked later, but they shall not be automatically merged.

Content fingerprints may support:

- duplicate detection
- idempotence
- comparison
- reproducibility

A content fingerprint never replaces the Information Unit identifier.

## Source Excerpt and Interpreted Statement

An Information Unit distinguishes:

```text
source_excerpt
interpreted_statement
```

`source_excerpt` contains the unchanged relevant text from the deterministic
Source Projection.

`interpreted_statement` contains the semantic candidate interpretation.

The field name `normalized_statement` shall not be used for the semantic
interpretation because deterministic normalization and semantic interpretation
are separate operations.

## Source Projection Identity

Every Source Projection receives an immutable project-local identifier named
`source_projection_id`.

The identifier:

- matches `^SP-[0-9]{6}$`
- is unique within one project
- is allocated sequentially
- is not reused

Valid examples include:

- `SP-000001`
- `SP-004281`
- `SP-999999`

A Source Projection belongs to exactly one registered source.

## Source Projection Segment Identity

Every segment within one Source Projection receives a projection-local
identifier named `segment_id`.

The identifier:

- matches `^SEG-[0-9]{6}$`
- is unique within one Source Projection
- preserves deterministic source order

An Information Unit shall reference at least one segment.

All segments referenced by one Information Unit shall belong to the same Source
Projection and therefore to the same registered source.

## Deterministic Source Projection

The LLM shall not receive an original registered file directly.

Every semantic process begins with a deterministic, persistable Source
Projection.

Permitted deterministic operations include:

- deterministic UTF-8 decoding
- removal of a UTF-8 byte-order mark
- normalization of line endings
- deterministic textual extraction from a supported container
- preservation of source order
- deterministic structural segmentation
- generation of source locators
- generation of projection issues
- calculation of hashes and fingerprints

The deterministic stage shall not perform:

- spelling correction
- synonym replacement
- terminology harmonization
- unit conversion
- semantic rewriting
- summarization
- requirement rewriting
- ontology mapping
- framework mapping
- domain inference

Deterministic source projection is syntactic and structural, not semantic.

## Supported P4 Source Adapters

The P4 MVP provides explicit adapters for:

```text
.txt
.md
.json
.csv
.tsv
.pdf
```

An extension is supported only when a deterministic adapter has been
implemented and validated.

The P4 MVP does not support:

```text
.doc
.docx
.odt
.ppt
.pptx
.xls
.xlsx
.rtf
```

These formats may be added later through explicit, versioned adapters.

The P4 MVP also excludes:

- scanned PDFs
- OCR
- image interpretation
- drawing interpretation
- diagram interpretation
- geometric reasoning
- audio
- video
- handwritten information

## Text Encoding

Textual source adapters accept:

- UTF-8
- UTF-8 with byte-order mark

Encoding guessing and silent fallback decoding are prohibited.

Unsupported or invalid encodings shall produce a visible projection issue.

## JSON Projection

A JSON source is parsed deterministically.

JSON locations use JSON Pointer references.

Duplicate object keys are rejected because they would make the source meaning
and traceability ambiguous.

Semantic interpretation of JSON values remains outside the deterministic
projection step.

## CSV and TSV Projection

CSV uses:

- RFC 4180-compatible parsing
- comma as the fixed delimiter

TSV uses:

- tab as the fixed delimiter

Dialect sniffing is prohibited.

Row and column locations remain available for traceability.

## PDF Projection

PDF support uses an explicit and pinned `pypdf` dependency.

Only machine-readable text is extracted.

Page boundaries are retained as source locators.

P4 does not perform:

- OCR
- image extraction for semantic processing
- drawing interpretation
- diagram interpretation

An empty or unextractable page produces a visible projection issue.

A PDF containing both extractable text and unsupported visual information may
produce a partial Source Projection.

## Source Projection Result

A Source Projection has exactly one result:

```text
complete
partial
unavailable
```

`complete` means that the supported textual content was projected without a
known projection loss.

`partial` means that usable textual content exists, but unsupported,
unextractable or failed content was detected.

`unavailable` means that no usable deterministic textual projection could be
created.

A partial result remains visible and requires its issues to be retained.

An unavailable result shall not enter semantic extraction.

## Source Projection Fingerprint

A Source Projection fingerprint is derived from at least:

- original source SHA-256
- adapter identifier
- adapter version
- deterministic adapter configuration

The fingerprint supports reproducibility and idempotence.

It does not replace:

- `project_id`
- `source_id`
- `source_projection_id`

## Information Classification

P4 separates three classification dimensions:

- Information Type
- Statement Modality
- Epistemic Class

These dimensions shall not be collapsed into one field.

## Information Types

The accepted Information Types are:

```text
stakeholder
actor
user_need
requirement
use_case
function
logical_element
physical_element
interface
constraint
information_item
definition
rationale
decision
risk
ambiguity
gap
open_question
unclassified
```

`subsystem` is not an Information Type.

Subsystem is a framework level and shall not be confused with the semantic kind
of an Information Unit.

`unclassified` is an explicit valid result. The system shall not force an
unsupported classification.

## Statement Modalities

The accepted Statement Modalities are:

```text
descriptive
normative
definitional
interrogative
```

Statement Modality describes how the statement is expressed.

It does not determine its framework mapping or Engineering Approval.

## Epistemic Classes

The accepted Epistemic Classes are:

```text
explicit
interpretation
derivation
assumption
```

`explicit` means that the professional statement is directly expressed in the
source.

`interpretation` means that semantic interpretation is necessary, but the
statement remains grounded in the source.

`derivation` means that the statement is derived from other Information Units.

`assumption` means that information not established by the source is introduced
to make an interpretation possible or visible.

A derivation requires:

- referenced supporting Information Unit identifiers
- a derivation rationale

During P4, supporting Information Units for a derivation shall belong to the
same source.

An assumption requires:

- an explicit missing-evidence explanation
- a visible assumption classification

The source anchor of an assumption records what triggered the assumption. It
does not turn the assumption into source evidence.

## Preliminary Coverage Exclusions

The following Information Types shall never create positive preliminary
coverage:

```text
risk
ambiguity
gap
open_question
```

Information Units classified as `assumption` shall never create positive
preliminary coverage.

They may still be associated with a relevant framework node for diagnostic
traceability.

The complete deterministic coverage policy belongs to P6.

## Human Review Separation

An immutable Information Unit shall not contain a mutable Human Review status.

Human Review decisions are separate records.

Terminology acceptance and Engineering Approval are separate processes.

Engineering Approval remains assigned to Phase G.

## Semantic Confidence

An individual LLM agent shall not determine the final confidence of an
Information Unit, terminology mapping or Framework Assignment.

Final confidence is derived deterministically from the variance of independent
persona-agent results.

The accepted confidence values are:

```text
high
medium
low
```

Confidence is ordinal.

It is not:

- a statistical probability
- a truth value
- a Human Review decision
- an Engineering Approval
- a readiness decision

A confidence value requires an auditable rationale.

## Multiagent Execution

P4 reuses the existing Phase F multiagent architecture.

All required members of one semantic team receive:

- the same task
- the same structured input
- the same role
- different explicit personas or professional perspectives

Team members execute independently.

They shall not coordinate before consensus analysis.

P4 may define dedicated teams for:

- semantic extraction
- terminology and ontology mapping
- framework mapping

Existing Phase F outputs are not automatically P4 Information Units.

P4 requires P4-specific structured output schemas and validators.

## Consensus and Variance

A deterministic consensus analyzer compares structured persona results.

The analyzer shall preserve:

```text
consensus_level
variance_level
confidence
total_personas
supporting_personas
dissenting_personas
value_distribution
review_required
confidence_rationale
consensus_report_id
```

The confidence is derived according to the following policy.

### High Confidence

`high` requires agreement of all required personas on the comparable result,
without a contradictory result or unexplained omission.

This corresponds to low inter-persona variance.

### Medium Confidence

`medium` may be assigned when:

- a strict majority supports the same result and other personas omit it
- a strict majority supports the same result but a minority provides a
  differing result

A differing result requires Human Review even when a majority exists.

### Low Confidence

`low` is assigned when:

- only one persona proposes the result
- no clear majority exists
- conflicting results exist
- the team run is technically incomplete
- the result cannot be compared reliably

Low confidence requires Human Review.

## Inter-Persona and Intra-Persona Variance

Inter-persona variance measures differences between distinct professional
perspectives.

Intra-persona variance measures differences between repeated runs of the same
persona.

Repeated runs of the same persona shall not be counted as additional
independent votes.

Each persona receives at most one vote in the team consensus.

Repeated runs measure stability and may reduce confidence when the persona
produces inconsistent results.

They shall not create an artificial majority.

The persona team is intentionally heterogeneous and is not a random,
independent statistical sample.

The resulting variance is an epistemic uncertainty signal, not a statistically
calibrated probability.

## Field-Level Confidence

Consensus and variance may be calculated separately for:

- existence of an Information Unit
- semantic interpretation
- Information Type
- Statement Modality
- Epistemic Class
- terminology mapping
- ontology mapping
- framework target

A Framework Assignment receives its confidence from the agreement about its
specific target and mapping rationale.

The lowest confidence of a critical required field conservatively limits the
overall confidence of the resulting candidate.

## Semantic Reference Stack

The accepted semantic reference stack is:

1. SysML v2 and KerML
2. BFO 2020
3. IOF Core
4. Turing Core Vocabulary
5. Project Glossary
6. LLM candidate generation

These layers have distinct responsibilities.

## SysML v2 and KerML

SysML v2 and KerML define the normative target-model and target-notation
semantics.

The curated repository references remain:

```text
context/sysml/sysml_v2_spec_reference.json
context/sysml/sysml_v2_target_notation.json
```

These files constrain later model generation and valid target notation.

They are not treated as a complete industrial-domain ontology.

## BFO 2020

BFO 2020 is the selected top-level ontology reference.

It provides general distinctions for entities, processes, qualities, roles and
related foundational categories.

The selected reference corresponds to BFO 2020 and ISO/IEC 21838-2.

BFO does not directly provide the complete MBSE or project vocabulary.

## IOF Core

IOF Core is the selected industrial mid-level ontology reference.

The pinned reference version uses:

```text
versionIRI: 202602
maturity: Released
```

IOF Core provides industrial semantic structure above BFO and below
project-specific terminology.

IOF Core does not replace:

- SysML v2
- the accepted framework
- Turing Core
- the Project Glossary
- human engineering decisions

## Local Ontology Snapshots

BFO and IOF are used through pinned local snapshots.

The intended structure is:

```text
external/ontologies/bfo/2020/bfo-core.owl
external/ontologies/iof/202602/AboutIOFProd.rdf
external/ontologies/iof/202602/Core.rdf
external/ontologies/iof/202602/AnnotationVocabulary.rdf
```

The corresponding license material shall be stored with the snapshots.

P4 shall not perform:

- live ontology queries
- automatic ontology downloads
- automatic ontology updates
- remote runtime dependency resolution

Updating an ontology snapshot requires an explicit reviewed change.

## Ontology Registry

The selected ontology snapshots are registered in:

```text
context/semantics/ontology_registry.json
```

The registry records at least:

- reference-system identifier
- version
- version IRI where applicable
- local file path
- source authority
- maturity
- license reference
- enabled runtime role
- checksum

The registry is curated and versioned.

## Reference Concept Index

P4 does not require an OWL reasoner or triple store.

A deterministic generated read-only concept index is stored in:

```text
context/semantics/reference_concept_index.json
```

The index supports runtime retrieval of selected:

- concept identifiers
- IRIs
- preferred labels
- alternative labels
- definitions
- parent relationships
- source-system references
- version references

The generated index is not the ontology authority.

The pinned RDF and OWL snapshots remain the auditable external-reference
artifacts.

The index can be regenerated deterministically.

## Runtime Ontology Boundary

P4 shall not introduce:

- a triple store
- an OWL reasoner
- live SPARQL endpoints
- unrestricted ontology graph traversal
- automatic inference from the complete external ontology graph
- automatic ontology updates

Only relevant retrieved concepts are supplied to an LLM.

Complete ontology files shall not be loaded into every prompt.

## Turing Core Vocabulary

A curated Turing Core Vocabulary is stored in:

```text
context/semantics/turing_core_vocabulary.json
```

Turing Core provides the controlled bridge between:

- MBSE terminology
- the accepted RFLP-oriented framework
- SysML v2 target concepts
- selected external ontology concepts
- project-specific concepts

Turing Core concepts receive stable identifiers matching:

```text
^TC-[0-9]{6}$
```

Valid examples include:

- `TC-000001`
- `TC-004281`
- `TC-999999`

Turing Core is global to the Turing Generator.

It shall not be modified automatically from one project.

## SysDO Boundary

SysDO is retained as a non-normative research and structuring reference.

It is not the primary semantic authority because its demonstrated scope and
maturity do not satisfy the complete requirements of the Turing Generator.

In particular, it does not replace the selected combination of:

- SysML v2 and KerML
- BFO
- IOF Core
- Turing Core
- Project Glossary

SysDO remains disabled as a runtime ontology source during the P4 MVP.

Nothing is copied from SysDO without explicit review.

## External Ontology Mappings

A Turing or Project Concept may map to an external concept using one of the
following relations:

```text
exact_match
narrower_than
broader_than
related_to
no_equivalent
```

Every mapping requires:

- the referenced external concept or IRI
- the referenced ontology and version
- a mapping relation
- a rationale
- provenance

An unmapped concept is valid.

The system shall not force an `exact_match`.

External ontology mappings cannot:

- create engineering requirements
- create framework coverage
- approve engineering information
- overwrite a project meaning
- overwrite Turing Core
- alter the authoritative engineering model

## Project Glossary

Every project owns a versioned Project Glossary under:

```text
data/projects/<project_id>/semantics/project_glossary.json
```

The Project Glossary captures reviewed project-specific vocabulary.

It supplements the external reference stack.

It does not replace or overwrite BFO, IOF Core or Turing Core.

## Project Concept Identity

Every Project Concept receives a stable project-local identifier named
`project_concept_id`.

The identifier:

- matches `^PC-[0-9]{6}$`
- is unique within one project
- is allocated sequentially
- is not reused

The globally unambiguous reference is the pair:

```text
<project_id>/<project_concept_id>
```

Example:

```text
318604/PC-000001
```

Project Concept identity remains stable across revisions.

## Project Concept Content

A Project Concept may contain:

- multilingual preferred labels
- multilingual alternative labels
- multilingual definitions
- broader Project Concept references
- related Project Concept references
- Turing Core mappings
- BFO or IOF mappings
- provenance
- lifecycle status
- revision
- rationale

Each project defines a default language.

## Preferred-Label Uniqueness

Accepted preferred labels shall be unique within one project and language.

Uniqueness comparison applies:

- Unicode NFKC normalization
- whitespace trimming
- Unicode case folding

Labels that differ only through these comparison operations conflict.

For example, case-only or compatible full-width variants shall not silently
create separate accepted concepts.

## Ambiguous Alternative Labels

A true homonym may be retained as an alternative label only through an explicit
Ambiguity Group.

An Ambiguity Group records at least:

- label
- language
- candidate Project Concept identifiers
- `resolution_rule: context_required`

Ambiguous labels shall never be resolved automatically.

The user interface may display disambiguated names such as:

```text
Port (Physical Interface)
Port (Network Endpoint)
```

The display text does not replace the stable Project Concept identifiers.

## Project Concept Provenance

Every Project Concept or revision requires provenance from at least one of:

- an engineering source
- a context-only source
- an explicit human terminology decision
- a selected external reference system
- Turing Core

Context-only provenance is permitted for terminology.

It does not create engineering evidence or framework coverage.

## Project Concept Lifecycle

The accepted Project Concept lifecycle states are:

```text
candidate
accepted
rejected
deprecated
```

Concepts shall not be deleted or silently overwritten.

A concept cannot become accepted solely through an LLM result.

## Terminology Decisions

Only a human may create the authoritative decision that accepts, rejects or
later replaces a Project Concept.

Terminology Decisions receive immutable project-local identifiers matching:

```text
^TD-[0-9]{6}$
```

A Terminology Decision records at least:

- project identifier
- Terminology Decision identifier
- Project Concept identifier
- Project Concept revision
- decision
- reviewer identity
- decision timestamp
- rationale

Reviewer identity is documented for auditability.

It is not treated as cryptographic identity proof.

## Terminology and Engineering Approval

Terminology acceptance confirms the intended meaning of a Project Concept.

It does not approve an engineering statement.

Engineering Review and Approved Input Promotion remain assigned to Phase G.

A terminology-approved concept may be used consistently in later processing,
but it does not create an approved Information Unit.

## LLM Terminology Permissions

An LLM may propose:

- Project Concepts
- preferred labels
- alternative labels
- definitions
- ambiguity candidates
- Turing Core mappings
- external ontology mappings

An LLM shall not:

- accept a Project Concept
- reject a Project Concept authoritatively
- merge concepts authoritatively
- resolve a homonym silently
- declare an `exact_match` authoritatively
- overwrite an accepted concept
- promote a Project Concept into Turing Core
- share a Project Concept with another project

## Terminology Conflicts

When new source usage conflicts with an accepted Project Glossary meaning, the
system creates a visible Terminology Conflict.

The conflict shall not be resolved automatically.

A human determines whether the result requires:

- a new concept
- a new concept revision
- an additional alternative label
- an Ambiguity Group
- deprecation
- rejection of the candidate interpretation
- no glossary change

## Project Concept Revisions

A Project Concept identifier remains stable.

A material edit creates a new revision.

Revision history remains preserved.

Only accepted revisions are authoritative in later semantic processing.

Candidate revisions may be shown to an LLM and reviewer but are not
authoritative.

Rejected revisions shall not be used as positive semantic evidence.

Deprecated revisions remain available only for traceability.

P5 defines the detailed lifecycle-event and invalidation storage.

## Project Isolation

Project Concepts remain project-specific.

They shall not be automatically:

- copied to another project
- shared across projects
- promoted into Turing Core
- treated as globally authoritative

A future cross-project curation workflow requires a separate architecture
decision.

## Framework Assignment Identity

Every Framework Assignment receives an immutable project-local identifier named
`framework_assignment_id`.

The identifier:

- matches `^FA-[0-9]{6}$`
- is unique within one project
- is allocated sequentially
- is not reused

The globally unambiguous reference is the pair:

```text
<project_id>/<framework_assignment_id>
```

Example:

```text
318604/FA-000001
```

## Framework Assignment Semantics

A Framework Assignment connects:

- exactly one Information Unit
- to exactly one valid framework mapping target
- in exactly one framework-template version

An Information Unit may have:

- no Framework Assignment
- one Framework Assignment
- multiple Framework Assignments

Every individual assignment requires its own:

- identifier
- mapping rationale
- mapping basis
- confidence evidence

Multiple assignments are not represented by one ambiguous target field.

## Framework Assignment Content

A Framework Assignment records at least:

```text
schema_version
project_id
framework_assignment_id
information_unit_id
framework_template_id
framework_template_version
framework_node_id
mapping_bases
mapping_rationale
confidence
confidence_rationale
consensus_report_id
created_at
supersedes_assignment_id
```

`supersedes_assignment_id` is absent when the assignment does not supersede an
earlier assignment.

## Framework Target Validation

`framework_node_id` must identify a valid mapping target in the referenced
framework-template version.

Free-form target names are prohibited.

Unknown framework targets are rejected.

The initial accepted framework remains:

```text
TURING_RFLP_FRAMEWORK
version 1.0.0
```

## Multiple Framework Assignments

Multiple Framework Assignments are permitted only when each target is
professionally justified.

A mapping to a child node shall not automatically create a mapping to its parent.

A mapping shall not be propagated automatically to:

- another framework level
- a sibling node
- another subsystem
- another Information Unit

Framework hierarchy and semantic relevance remain separate concerns.

## Framework Mapping Bases

An assignment may reference one or multiple mapping bases:

```text
direct_semantic
structural_context
project_glossary
turing_core
external_ontology
```

Referenced concepts, Project Concept revisions and ontology IRIs remain
explicitly traceable.

Label similarity alone is not a sufficient mapping rationale.

An accepted Project Glossary concept may support a Framework Assignment.

It shall not force one.

## Framework Mapping Evaluation

The absence of a Framework Assignment is ambiguous because it could mean either:

- mapping has not been performed
- mapping was performed and no valid target was found

Every completed mapping attempt therefore creates an immutable Framework
Mapping Evaluation.

Framework Mapping Evaluation identifiers match:

```text
^FME-[0-9]{6}$
```

The accepted evaluation outcomes are:

```text
mapped
unmapped
ambiguous
failed
```

An evaluation references zero or multiple Framework Assignments.

`unmapped`, `ambiguous` and `failed` require an explicit rationale or error
description.

## Framework-Mapping Governance

The LLM may:

- propose Framework Assignments
- propose multiple possible targets
- report an ambiguous mapping
- report that no valid mapping was found
- provide concise mapping rationales

The LLM shall not:

- approve a Framework Assignment
- silently choose one target from an ambiguous result
- create a framework node
- change the framework hierarchy
- treat confidence as approval
- perform Engineering Approval

P4 produces mapping candidates.

Engineering Approval remains assigned to Phase G.

## Framework Version Binding

Every Framework Assignment remains permanently bound to the framework-template
version used during its creation.

A new framework-template version requires a new mapping evaluation.

Existing assignments shall not be silently migrated.

## Mapping Correction

A corrected mapping produces:

- a new Framework Mapping Evaluation
- new Framework Assignments where required
- explicit later supersession references

Existing assignments and evaluations remain auditable.

## Semantic Persistence Root

Project-specific semantic records are stored logically below:

```text
data/projects/<project_id>/semantics/
```

The accepted semantic areas are:

```text
data/projects/<project_id>/semantics/
├── source_projections/
├── information_units/
├── project_glossary.json
├── terminology_decisions/
├── terminology_conflicts/
└── framework_mappings/
```

The exact organization of processing runs, temporary artifacts and derived
indexes belongs to P5.

## Source Projection Persistence

A persisted Source Projection contains:

```text
source_projections/<source_projection_id>/
├── projection.json
└── content.txt
```

`projection.json` records at least:

- schema version
- project identifier
- source identifier
- Source Projection identifier
- source SHA-256
- adapter identifier
- adapter version
- adapter configuration
- projection fingerprint
- projection result
- segments
- source locators
- issues
- projected-content SHA-256
- creation timestamp

`content.txt` contains the deterministic UTF-8 textual projection.

It does not replace the immutable original source in the P3 Source Registry.

## Persistence Rules

P4 records are:

- schema-validated
- project-isolated
- written atomically
- immutable after publication unless explicitly defined as versioned
- never silently overwritten
- never silently deleted

A new record shall not reference a different project.

Derived indexes may be regenerated.

They are not authoritative.

The validated P4 records remain authoritative for the P4 semantic repository.

## Reproducibility Metadata

Semantic processing remains traceable to:

- project identifier
- source identifier
- Source Projection and fingerprint
- adapter identifier and version
- team configuration
- persona configuration
- LLM provider
- LLM model
- prompt or schema version
- Consensus Report
- Ontology Registry version
- Reference Concept Index version
- Turing Core version
- Project Glossary concept revisions
- framework-template identifier and version

BFO and IOF files are not copied into every project.

Project records reference the registered pinned versions and concept IRIs.

## Reprocessing

Reprocessing the same Source Projection creates a new Processing Run.

An identical validated result may be recognized through fingerprints.

A materially different semantic result creates a new semantic record with a new
identifier or revision.

Fingerprints support comparison and idempotence.

They do not replace semantic identities.

## P4 Responsibility

P4 owns:

- deterministic Source Projection adapters
- Source Projection validation
- Information Unit schema and validation
- semantic multiagent extraction
- terminology and ontology candidates
- Project Glossary domain rules
- Framework Assignment and Evaluation rules
- field-level consensus and variance
- confidence derivation
- persistence of validated semantic records

## P5 Boundary

P5 owns:

- Processing Run identity
- processing states
- run resumption
- organization of raw agent outputs
- Consensus Report organization
- temporary processing artifacts
- lifecycle events
- supersession
- invalidation
- derived operational indexes
- detection of incomplete publication

P5 shall not rewrite the professional content of an Information Unit,
Framework Assignment or terminology decision.

A Processing Run is complete only after its required P4 records have been
validated and published successfully.

Partial processing results shall not appear as a completed run.

## P6 Boundary

P6 reads the P4 semantic records that P5 identifies as usable.

P6 calculates:

- Preliminary Coverage
- coverage gaps
- mapping conflicts
- preliminary framework support

P6 shall not modify P4 records.

P6 does not treat an Information Unit as approved engineering input.

## Phase G Boundary

P4 records are candidates.

Phase G creates separate Human Review and Engineering Approval records.

An approval references the exact immutable record or concept revision that was
reviewed.

Approval of one version does not automatically approve:

- a successor Information Unit
- a new Framework Assignment
- a new Project Concept revision
- a remapped framework-template version

Only Phase-G-approved engineering information may enter Phases H through J.

## Phase F Integration

P4 reuses the existing Phase F infrastructure for:

- team execution
- persona instructions
- LLM-provider access
- raw agent artifacts
- deterministic consensus analysis

P4 extends this infrastructure with:

- P4-specific structured result schemas
- P4-specific teams and personas where required
- field-level consensus comparison
- inter-persona variance
- intra-persona stability
- semantic validators
- controlled creation of P4 domain records

Existing Phase F reports and agent outputs are not automatically converted into
P4 Information Units.

## Model-Generation Boundary

P4 shall not:

- create approved engineering input
- create model candidates
- generate an internal engineering model
- generate SysML v2 code
- update CATIA
- override the authoritative engineering model

Approved Input Promotion belongs to Phase G.

Model Candidate creation belongs to Phase H.

Internal model generation belongs to Phase I.

SysML v2 code generation belongs to Phase J.

Consequences

## Positive Consequences

The architecture provides:

- deterministic traceability from source bytes to semantic interpretation
- explicit separation of syntactic projection and semantic processing
- stable project-local semantic identifiers
- immutable and auditable Information Units
- visible assumptions, ambiguity and disagreement
- controlled use of external ontology references
- project-specific terminology without global contamination
- reproducible framework assignments
- multiagent variance as an auditable uncertainty signal
- separation of confidence and Engineering Approval
- clear boundaries between P4, P5, P6 and Phase G
- continued reuse of the implemented Phase F agent infrastructure
- a bounded MVP without an ontology server or multimodal interpretation

## Costs and Limitations

The architecture introduces:

- multiple semantic artifact types
- additional validators and repositories
- explicit ontology and vocabulary curation
- more storage for immutable records and revisions
- multiple LLM calls per semantic task
- increased processing cost for multiagent execution
- a Human Review requirement for terminology and ambiguous mappings
- no support for visual engineering information
- no automatic cross-source synthesis
- no statistical calibration of confidence
- no automatic ontology reasoning
- no automatic cross-project terminology reuse

These costs are accepted in exchange for traceability, auditability and
controlled semantic processing.

Alternatives Considered

## Single Universal MBSE Ontology

Rejected.

No single reference system provides the complete combination of:

- top-level semantics
- industrial concepts
- MBSE and RFLP terminology
- SysML v2 target semantics
- project-specific vocabulary

The layered reference stack is more explicit and adaptable.

## BFO or IOF as the Complete Project Vocabulary

Rejected.

BFO is too general and IOF Core is not a complete project or SysML vocabulary.

Both remain useful reference layers.

## SysDO as the Primary Runtime Ontology

Rejected.

SysDO is useful as a non-normative research and structuring reference, but its
demonstrated maturity and scope are insufficient for primary runtime authority.

## Project Glossary Without External References

Rejected.

A project-only vocabulary would improve local consistency but reduce
interoperability and make concept mappings harder to justify.

## Live Ontology Service

Rejected for the MVP.

Live services would reduce reproducibility and introduce availability,
versioning and security dependencies.

## Full OWL Reasoner or Triple Store

Rejected for the MVP.

The accepted P4 use cases require controlled concept retrieval and explicit
mapping, not unrestricted automated inference.

## Loading Complete Ontologies Into Every Prompt

Rejected.

It would increase token use and reduce prompt focus without providing a
controlled semantic guarantee.

## Direct Original-File Processing by the LLM

Rejected.

It would make text extraction provider-dependent and weaken deterministic
traceability.

## Semantic Normalization During Source Projection

Rejected.

Spelling correction, synonym replacement, unit conversion and rewriting are
semantic operations and could change source meaning.

## Mutable Information Units

Rejected.

Overwriting extracted information would destroy auditability and make existing
reviews and mappings ambiguous.

## Automatic Cross-Source Claim Merging

Rejected.

Apparently equivalent statements may have different authority, wording,
constraints or context.

They remain separate and traceable to their individual sources.

## Framework Assignment Embedded Directly in the Information Unit

Rejected.

Framework mappings have their own rationale, confidence, lifecycle and
framework-version binding.

They remain separate records.

## Automatic Parent or Level Propagation

Rejected.

A semantic mapping to one node does not automatically prove relevance to its
parent, siblings or another framework level.

## Single-Agent Confidence

Rejected.

An individual LLM self-assessment is not a sufficiently auditable confidence
basis.

Confidence is derived from independent persona results.

## Treating Repeated Runs as Independent Votes

Rejected.

Repeated runs of the same persona measure stability but do not create additional
independent professional perspectives.

## Numeric Confidence as Probability

Rejected.

The persona team is not a statistically independent random sample.

The accepted confidence is an ordinal epistemic signal.

## Automatic Terminology Acceptance

Rejected.

Terminology meaning requires explicit Human-in-the-Loop governance.

## Engineering Approval During P4

Rejected.

P4 produces semantic and framework-mapping candidates.

Engineering Approval remains a separate Phase G responsibility.

Implementation Constraints

P4 implementation shall:

- preserve all P1 framework validation rules
- preserve P2 project isolation
- preserve P3 source immutability
- enforce ADR-009 textual-modality restrictions
- reject unsupported adapter behavior
- reject cross-project semantic references
- reject unknown framework targets
- reject malformed semantic identifiers
- reject direct context-only engineering contribution
- reject silent overwrites
- retain projection and semantic issues
- retain agent disagreement
- keep confidence separate from approval
- keep terminology approval separate from Engineering Approval
- remain compatible with the existing Phase F pipeline

P4 implementation shall not begin to depend on a different architecture without
a new explicitly accepted Architecture Decision Record.

Verification Criteria

P4 is not complete until automated tests demonstrate at least:

- deterministic projection for every supported adapter
- rejection of unsupported encodings
- rejection of JSON duplicate keys
- fixed CSV and TSV parsing behavior
- PDF text-layer extraction with page traceability
- visible partial and unavailable projection results
- stable Source Projection and segment identifiers
- stable Information Unit identifiers
- Information Unit atomicity validation
- same-source anchor enforcement
- rejection of cross-source Information Unit synthesis
- rejection of context-only Information Units
- validation of all Information Types
- validation of all Statement Modalities
- validation of all Epistemic Classes
- derivation-support reference validation
- assumption missing-evidence validation
- Project Concept identifier and revision validation
- preferred-label uniqueness by language
- Ambiguity Group validation
- Terminology Decision validation
- external ontology mapping validation
- framework-template version validation
- rejection of unknown framework targets
- zero-to-many Framework Assignments
- explicit unmapped, ambiguous and failed Mapping Evaluations
- no automatic framework hierarchy propagation
- deterministic consensus classification
- separation of inter-persona and intra-persona variance
- one vote per persona
- deterministic ordinal confidence derivation
- mandatory review for conflicting or low-confidence results
- immutable semantic persistence
- atomic record publication
- rejection of cross-project semantic references
- preservation of Phase F behavior
- complete project test-suite compatibility

Related Decisions

- ADR-005 — Project Workspace Architecture
- ADR-009 — Textual Source Processing Boundary
- ADR-010 — Project Source Registry Architecture

Implementation Status

Architecture accepted.

P4 implementation not started.
