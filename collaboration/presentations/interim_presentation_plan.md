# Interim Presentation Planning Note

<!-- BEGIN SSOT UPDATE 2026-08-20 -->
## Presentation Delta — 2026-08-20

Presentation/live demo:

```text
Monday 2026-08-24
```

Narrative:

```text
KICK-OFF → ARCHITECTURE → PROTOTYPE → VERIFICATION → FINDINGS → NEXT
```

Original Kick-off flow:

```text
1 Feature Ingestion
2 Sortier Agent
3 Ontologie Anpassung
4 Muster Antizipation
5 Human in the Loop
6 Synthese / SysML-v2 generation
```

Literature framing remains:

```text
Data Layer
Process Layer
Knowledge Layer
```

CATIA Logical Architecture overview already uses the eight existing Logical Architecture part usages and should communicate:

```text
Control
Engineering Information
Evidence & Traceability
```

Target future high-level System Behavior:

```text
REFERENCE KNOWLEDGE
→ ENGINEERING SOURCE
→ Deterministic Source Projection
→ Find Source-Grounded Evidence
→ Persona Interpretation / Classification
→ Consensus / Variance
→ optional Semantic Normalization / Ontology Alignment
→ Human Review
→ Approved Engineering Information
→ Architecture Derivation
→ SysML v2
```

Do not model this new high-level behavior in CATIA until implementation alignment and ADR-027 acceptance.

Demo:

```text
start real single-source LLM Processing live
→ explain processing time
→ transparently switch to genuinely previously processed persisted state
→ Human Review live
→ Approved Input
→ Model / Architecture
→ SysML v2
```

Do not present prepared/manual data as unmodified live LLM output.
<!-- END SSOT UPDATE 2026-08-20 -->

**Status:** Working note for presentation preparation  
**Purpose:** Preserve the agreed presentation concept until the next SSOT update  
**Presentation timing:** Create the actual presentation only after implementation is completed

## 1. Presentation objective

The interim presentation shall explain the development of the Turing Generator
from the literature-derived architecture concept and Kick-off baseline to the
implemented and modeled system architecture.

The professor's last reference point is the Kick-off presentation. Therefore,
the presentation must explicitly bridge from that known baseline to the current
CATIA SysML v2 architecture and the implemented MVP.

The presentation shall remain high-level enough for a reader without detailed
knowledge of the implementation, while retaining enough engineering content to
show that the system is not a generic LLM pipeline.

## 2. Literature-derived three-layer architecture

The three-layer architecture is a central architectural objective derived from
the literature and must be explicitly presented as such:

Data Layer
Process Layer
Knowledge Layer

The presentation shall explain that the objective was not merely to draw three
technical containers, but to realize the responsibilities of these three
literature-derived layers through modular subsystems / Logical Components.

The current architecture shall therefore be presented as the concrete
operationalization of the original three-layer target architecture.

### Data Layer realization

Primary responsibilities:

source acquisition
normalization
information preparation
project/source context
coverage
evidence
traceability

Main Logical Components:

LC_02 Project and Source Context Management
LC_04 Engineering Information Processing
LC_06 Coverage Evidence and Traceability Management

### Process Layer realization

Primary responsibilities:

workflow control
processing state
candidate generation
human review
architecture derivation
architecture validation
SysML v2 artifact generation

Main Logical Components:

LC_03 Processing Orchestration and State Control
LC_05 Candidate and Review Governance
LC_07 Architecture Synthesis and Validation
LC_08 SysML v2 Artifact Generation

Supporting interaction boundary:

LC_01 User Interaction and Status Presentation

### Knowledge Layer realization

The Knowledge Layer shall be presented as a cross-cutting governance layer
rather than as one isolated technical silo.

It acts through several Logical Components, especially:

LC_04 Engineering Information Processing
LC_05 Candidate and Review Governance
LC_06 Coverage Evidence and Traceability Management
LC_07 Architecture Synthesis and Validation

Relevant knowledge and governance artifacts include, for example:

ontologies
Turing Core Vocabulary
framework templates
recipes
agent profiles
project principles
semantic reference definitions
design constraints

Key presentation message:

Literature identified three required responsibility layers.
The implementation realizes these responsibilities through modular,
traceable subsystems.

## 3. High-Level Activity Diagram

A new CATIA high-level Activity view shall explain what happens to one
engineering document from ingestion to the complete MVP output.

The diagram must strictly follow the 7 +/- 2 rule.

The agreed primary activity chunks are:

1. Register Project & Source
2. Assess & Prepare Information
3. Apply Semantic Governance
4. Agentic Candidate Generation
5. Human Review & Approval
6. Derive & Structure Architecture
7. Validate Architecture
8. Generate & Validate SysML v2

Cross-cutting governance shall be shown as one additional visual concept:

Processing Orchestration
Evidence
Traceability
Status / History

The diagram shall use existing System Functions as engineering authority and
shall not invent new top-level System Functions merely for presentation.

Existing model Item Definitions should be used for meaningful Object Flows,
for example:

Legacy Engineering Data
Project and Source Context
Prepared Engineering Information
Semantically Governed Information
Engineering Candidate Set
Human Review Decision
Approved Engineering Information
Architecture Candidate
Validated Architecture
SysML v2 Artifact Set
Validation Findings
Versioned SysML v2 Output Package

The current implementation boundary and the complete MVP target shall be
visually distinguishable.

## 4. Logical Architecture Presentation View

A second central CATIA diagram shall show the system architecture using the
existing eight Logical Components.

The view shall answer:

Which subsystem performs which responsibility?
Which engineering information is exchanged between subsystems?
How do the three literature-derived layers map to the implemented architecture?

The diagram should show meaningful information exchange via ports / item flows
rather than only generic connector names.

The eight Logical Components remain:

LC_01 User Interaction and Status Presentation
LC_02 Project and Source Context Management
LC_03 Processing Orchestration and State Control
LC_04 Engineering Information Processing
LC_05 Candidate and Review Governance
LC_06 Coverage Evidence and Traceability Management
LC_07 Architecture Synthesis and Validation
LC_08 SysML v2 Artifact Generation

LC_06 should be understandable as a cross-cutting Evidence and Traceability
backbone.

LC_01 should be understandable as the human interaction and status boundary.

## 5. Kick-off comparison

The presentation shall explicitly compare the Kick-off concept with the current
architecture.

The narrative is:

Kick-off:
6 understandable process steps
3 literature-derived architecture layers

Current architecture:
12 System Functions
8 Logical Components
explicit Processing Runs and States
Evidence and Traceability
Human Review and Authority boundaries
feedback / retry / rework paths

Central message:

No scope drift.
The original concept was operationalized into a modular, governed and
verifiable system architecture.

The existing Kick-off comparison material should be reused as evidence, but
the presentation should not reproduce the complete comparison document.

## 6. Architectural adaptability as presentation outlook

The outlook shall explicitly address that the Turing Generator architecture is
intentionally adaptable.

A substantial part of task behavior and processing context is introduced
through managed, replaceable artifacts rather than hard-coded into one fixed
processing chain.

Relevant artifact types include, for example:

.md files
.json files
recipes
agent profiles
context definitions
framework templates
semantic definitions
task descriptions

By exchanging or versioning the corresponding artifacts, different processing
tasks, domain contexts and agent behaviors can be introduced without
restructuring the complete software architecture.

This shall be presented as:

stable processing architecture
+
exchangeable versioned task / context / knowledge artifacts
=
adaptable Architecture-as-Code processing framework

Important qualification:

The presentation must not imply arbitrary uncontrolled runtime behavior.

Adaptability remains governed by:

explicit artifact purpose
versioning
validation
traceability
processing context
review / approval boundaries

The architectural adaptability point belongs in the outlook at the end of the
presentation, not in the primary architecture explanation.

## 7. Presentation sequence currently agreed

Indicative sequence:

1. Kick-off recap / research objective
2. Literature-derived three-layer architecture
3. From six-step concept to governed system architecture
4. High-Level Activity Diagram in CATIA
5. Current implementation boundary / MVP completion path
6. Logical Architecture + layer realization in CATIA
7. Evidence of architectural development / requirement coverage
8. Remaining work to complete the MVP
9. Outlook: adaptable artifact-driven architecture

The exact slide deck shall be designed only after the implementation has been
completed and the final implementation status is known.

## 8. CATIA modeling sequence before presentation creation

Before PowerPoint creation:

1. confirm Three-Layer -> Logical Component allocation
2. create / refine Logical Architecture Presentation View
3. create High-Level Activity with Object Flows
4. verify Activity -> System Function -> Logical Component traceability
5. complete implementation and final Phase-G / MVP status
6. create the actual presentation

## 9. SSOT follow-up

At the next SSOT update, preserve at least the following agreements:

- presentation is created after implementation, not before
- three-layer architecture is literature-derived and a core design objective
- current Logical Components operationalize the three-layer concept
- Knowledge Layer is cross-cutting governance, not necessarily one subsystem
- High-Level Activity must obey the 7 +/- 2 rule
- High-Level Activity covers the complete MVP
- central presentation artifacts are CATIA diagrams
- Logical Architecture should expose meaningful information flows
- architectural adaptability through replaceable/versioned .md/.json artifacts
  belongs in the presentation outlook
- Human Review UI feedback:
  compare competing proposals side-by-side
  keep detailed traceability available on demand rather than permanently
  dominating the primary review view

## 10. 2026-08-19 execution update

The earlier rule to create the actual presentation only after implementation
completion is superseded by the fixed professor/demo schedule.

Presentation preparation starts on 2026-08-20 even though WP-12 and BLK-003 are
not closed. The presentation must clearly distinguish implemented/verified,
empirically open, architecture-only, planned and blocked scope.

Current execution authority:
`collaboration/checkpoints/2026-08-19_presentation_wp12_demo_ssot.md`

The two central CATIA presentation artifacts remain:

- Logical System Architecture / three-layer realization
- High-Level Activity Diagram with meaningful Object Flows

If a credible live path is not available by the evening of 2026-08-20, the
Monday demo shall use the controlled Demo / Replay fallback described in the
checkpoint.
