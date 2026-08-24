# ADR-027 — Source-Grounded Evidence Detection and Persona Interpretation Architecture

Status

**Accepted — responsibility-boundary recovery accepted after Source-to-Human-Review audit. Implementation remains incremental and regression-controlled.**

Accepted

2026-08-21

Date

2026-08-20

---

## Context

WP-12 end-to-end formative testing showed that the technical authority chain can reach Human Review, but the semantic quality of the review input is not yet acceptable.

Representative real single-source run:

```text
Project 877791 / RUN-000001
3 personas × 1 run

93 element proposals
41 relationship proposals
134 raw proposals

D3: 70 elements + 39 relationships = 109 subjects
D4: 70 elements + 39 relationships = 109 subjects
Human Review: 110 items = 70 Elements + 39 Relationships + 1 Open Question
```

The D4-to-Review routing is technically operational. The formative result exposed:

1. source purity regression — processing/orchestration/task metadata can become engineering subjects,
2. model relevance regression — candidate content can be generic rather than concrete model-relevant engineering information,
3. subject multiplication — persona-generated candidate identities can create parallel subject sets which later stages attempt to consolidate.

Review Item count is therefore a diagnostic symptom, not the optimization target.

A deliberately simple external benchmark on `legacy/demo/wp12/01_product_overview.md` showed that a general-purpose LLM can identify a small set of source-grounded, model-relevant passages with a direct task and strict source boundary. The benchmark returned eight major source-grounded findings. It is qualitative diagnostic evidence only; it is not a gold standard and shall not become model authority.

ADR-011 already established several still-valid foundations: deterministic Source Projection, source anchors/excerpts, source-traceable Information Units, `engineering_source` vs `context_only`, semantic extraction, persona perspectives, consensus/variance, repeated runs as stability evidence rather than votes, ontology/terminology boundaries, and Human Review separation.

The recovery shall therefore first simplify and realign the existing architecture rather than add another post-processing contract.

---

## Relationship to ADR-025 and ADR-026

ADR-025 — Semantic Proposal Consolidation and Persona-Aware Consensus and
ADR-026 — Source-Anchored Multi-Persona Interpretation and Cross-Unit Semantic
Synthesis remain accepted historical architecture decisions and document the
evolution that led to this recovery.

ADR-027 refines the upstream responsibility sequence exposed by the subsequent
empirical WP-12 test. In particular, source anchoring alone is not sufficient if
Personas can still independently create engineering-subject populations that
must later be reconciled.

ADR-027 therefore moves the common source-grounded evidence space ahead of
Persona interpretation. Existing ADR-025/ADR-026 components remain reusable only
where their responsibility is compatible with this clarified sequencing.

## Decision

### 1. Separate Evidence Detection from Persona Interpretation

```text
Evidence Detection
"Which passages of the Engineering Source contain
potentially model-relevant engineering information?"
        ↓
Persona Interpretation
"What does this already identified source-grounded
engineering information mean?"
```

Detection establishes the common source-grounded evidence space. Persona interpretation operates on that common evidence space.

### 1a. Evidence Detection Is a Specialized Persona-Independent Agent Task

Evidence Detection is an explicit LLM-backed preparation task with one narrowly
bounded responsibility:

```text
Engineering Source
+ project/source identity
+ source projection / processing scope
+ reference examples and detection guidance
        ↓
Specialized Evidence Detection Agent
        ↓
exact source-grounded evidence spans
```

The detector may use curated repository examples, modeling guidance and other
reference knowledge to learn what kinds of engineering information are worth
marking. Those inputs remain `context_only` guidance. They shall never become
positive Project evidence.

The detector shall not:

- create requirements, actors, functions, interfaces or other model elements,
- perform architecture derivation,
- assign final engineering meaning on behalf of interpretation personas,
- create multiple evidence identities merely because several personas or runs
  will later consume the evidence.

Detector output must be independently verifiable against the Source Projection.
At minimum, every accepted evidence span is bound by exact source anchors and an
exact source excerpt.

### 1b. Source Registration and Source Preparation Are Architecturally Separate

The Source Registry remains the immutable authority for Project Source identity.
LLM execution shall not be added to the Source Registry contract itself.

The system distinguishes:

```text
REGISTER SOURCE
    ↓
PREPARE SOURCE
    ↓
Source Projection
    ↓
Evidence Detection
    ↓
SOURCE READY FOR INTERPRETATION
```

The UI may present registration and preparation as one convenient user action.
That is a UX choice, not a collapse of architectural responsibilities.

Evidence Detection is version/configuration dependent. Its persisted result must
therefore remain traceable to the immutable Source version and to the detector
configuration used to create it. Changing persona configuration alone shall not
require Evidence Detection to be repeated.

### 2. Reference Knowledge Is Guidance, Never Engineering Evidence

Reference knowledge may include Apollo 11 reference material, SysML v2/KerML references, modeling guidance, framework definitions, agent roles/personas, recipes, project principles, terminology and ontology references.

It may answer:

```text
"What kinds of engineering information should I look for?"
```

It shall never answer:

```text
"What engineering information exists in this Project Source?"
```

Only a registered `engineering_source` may provide positive engineering evidence. Prompt text, task instructions, recipes, orchestration manifests, processing metadata and reference models shall never become positive Project engineering evidence merely because they were visible to an LLM.

### 3. Source-Grounded Evidence Is the Common Discussion Basis

Every detected Evidence Unit shall remain bound to the Engineering Source through at least:

```text
project_id
source_id
source_projection_id
source_anchor(s)
exact source_excerpt
```

This is the digital equivalent of a text-marker highlight. Evidence identity is source-grounded. An agent-generated candidate name shall not be the primary identity used to determine whether personas are discussing the same source information.

### 4. Personas Interpret the Same Evidence

```text
Evidence E-xxx
      │
 ┌────┼────┐
 ▼    ▼    ▼
P1   P2   P3
      │
      ▼
Consensus / Variance
```

Personas may disagree about relevance confidence, professional interpretation, information type, modality, epistemic class, terminology, model relevance, uncertainty or missing information.

Their disagreement is first-class engineering information. It shall not automatically create multiple independent Review Subjects.

### 5. Persona and Run Counts Shall Not Multiply Engineering Subjects

The number of engineering subjects shall be driven by distinct source-grounded engineering information, not by persona/run count.

```text
Review Subjects ≠ Source Subjects × Personas × Runs
```

Repeated runs measure intra-persona stability and are not additional independent votes. Each persona contributes at most one effective vote to one evidence-centered consensus assessment.

### 6. Evidence Detection May Express Uncertainty

Evidence detection may classify a passage as:

```text
relevant
not_relevant
uncertain
```

One passage may contain multiple independently reviewable claims. The key constraint is that their identities remain source-grounded and are not multiplied merely by persona execution.

### 7. Review Item Count Is a Diagnostic, Not an Optimization Objective

Evaluation shall prioritize:

1. source purity,
2. model relevance,
3. source grounding,
4. clear interpretation/classification,
5. useful consensus/variance,
6. Human Review usability.

A high Review Item count can be correct if the Source contains many independent claims. A count increase caused only by adding personas/runs indicates an architectural or consolidation defect.

### 8. Terminology and Ontology Mapping Are Supporting Services

Semantic normalization, terminology mapping and ontology alignment may improve comparability and cross-source consistency. They shall not create new positive Engineering Source evidence or new subjects without a source-grounded basis.

### 9. Human Engineering Review Precedes Architecture Derivation

```text
Engineering Source
→ Deterministic Source Projection
→ Source-Grounded Evidence Detection
→ Persona Interpretation
→ Consensus / Variance
→ optional Semantic Normalization / Ontology Alignment
→ Human Review
→ Approved Engineering Information
→ Architecture Derivation
→ SysML v2 Generation
```

AI-generated interpretation is evidence for Human Review, not Approved Engineering Information.

### 9a. Architecture Derivation May Again Use Multiple Personas

Multi-persona processing remains valuable after Human Engineering Review.
However, its responsibility changes.

Before Human Review, personas answer:

```text
"What does this same source-grounded Evidence mean?"
```

After approval, model-derivation personas may answer:

```text
"How can this Approved Engineering Information be represented
as a coherent system/model architecture?"
```

Target sequence:

```text
Approved Engineering Information
        ↓
 ┌──────┼──────┐
 ▼      ▼      ▼
Model  Model  Model
Persona Persona Persona
 └──────┼──────┘
        ↓
Architecture / Model Candidate Derivation
        ↓
Semantic Comparison / Candidate Consolidation
        ↓
Model Candidate Review
        ↓
Approved Internal Model
        ↓
SysML v2 Generation
```

Whether this downstream derivation phase shall reuse existing personas or
introduce new task-specific modeling personas is intentionally deferred until
that stage is implemented and evaluated. The architecture requires the persona
branch; it does not prematurely freeze its future persona set.

### 10. Existing P9 Responsibilities Have No Grandfathering Protection

Every material P9/D3/D4 responsibility shall be classified as:

```text
KEEP
MOVE DOWNSTREAM
REDUCE TO ADAPTER
BYPASS
RETIRE
```

A responsibility shall not be retained merely because downstream code currently expects it.

---

## Thesis-Relevant Architecture Finding

The WP-12 formative run exposed a responsibility-ordering defect rather than a
simple clustering or prompt-quality problem.

### Previous responsibility sequence

In the previous active path, each interpretation persona could independently:

1. select what it considered meaningful engineering information,
2. assign persona-local `source_info_id` identities,
3. interpret/classify that selected information,
4. feed a derivation step that created model-oriented candidate elements and
   relationships before the first Human Engineering Review.

Downstream D3/D4 semantic consolidation then attempted to determine which of
those independently created candidate populations referred to the same
engineering subject.

This caused a fundamental comparability problem:

```text
Persona A selection ≠ Persona B selection ≠ Persona C selection
```

Therefore differences between persona outputs could not be interpreted cleanly
as professional interpretation variance. A difference could instead be caused
by different source selection, segmentation, abstraction, naming or early
modeling decisions.

### Observed consequences

The architecture produced several characteristic symptoms:

- **persona-driven subject multiplication** — additional personas could create
  additional subject populations rather than additional views on one subject;
- **unstable engineering-subject identity** — candidate names/types became part
  of the mechanism used to infer common subjects;
- **false or ambiguous variance** — source-selection differences and genuine
  interpretation differences were mixed;
- **excessive downstream semantic repair** — later LLM consolidation had to
  reconstruct commonality that had not been established upstream;
- **premature model derivation** — model structure was proposed from unreviewed
  interpretation;
- **Human Review overload** — the reviewer received a large model-oriented
  subject population rather than a compact set of source-grounded engineering
  information;
- **technical success without engineering effectiveness** — the processing
  chain could reach Human Review correctly while the review content remained
  unsuitable for engineering use.

The representative real single-source run made the effect visible:

```text
3 personas × 1 run
93 element proposals
41 relationship proposals
134 raw proposals
109 D3/D4 semantic subjects
110 Human Review items
```

These counts are evidence of the symptom, not a target to optimize directly.

### Architectural correction

ADR-027 introduces an explicit boundary:

```text
DETECTION
Which source passages are potentially engineering-relevant?
        ↓
fixed source-grounded Evidence identity
        ↓
INTERPRETATION
What does this same Evidence mean from different professional perspectives?
```

Only after Evidence identity is fixed do personas branch. This makes
consensus/variance meaningful because each persona is now discussing the same
source-grounded object.

After Human Engineering Review and approval, a second persona branch may be used
for architecture/model derivation. The key change is therefore not the removal
of personas or LLM reasoning, but the placement of those responsibilities on
the correct side of the engineering approval boundary.

### Thesis interpretation

This is a first-class formative engineering result of the prototype:

> Source grounding alone is insufficient for reliable multi-persona semantic
> processing when evidence detection and persona-specific interpretation share
> the same responsibility boundary. A common evidence identity must be
> established before persona variance can be interpreted as engineering
> variance.

This finding should be carried into the thesis as an observed failure,
root-cause analysis, architectural correction and subsequent evaluation target.

---

## Relationship to ADR-011

ADR-027 does not replace ADR-011 wholesale. The following remain valid unless separately changed:

- deterministic Source Projection,
- immutable Source identity,
- source anchors/excerpts,
- Information Unit traceability,
- `engineering_source` / `context_only`,
- explicit epistemic classification,
- independent persona perspectives,
- deterministic consensus/variance,
- repeated runs as stability evidence rather than votes,
- explicit terminology/ontology mapping,
- Human Review separation.

ADR-027 sharpens the sequencing: a common source-grounded evidence space is established before persona interpretations become downstream Review Subjects.

---

## Qualitative Benchmark

The 2026-08-20 external diagnostic benchmark used exactly:

```text
legacy/demo/wp12/01_product_overview.md
```

A simple source-bounded prompt returned eight major findings around:

- remote microscope collaboration capability,
- microscope operator and remote expert,
- workstation and remote client context,
- remote consultation purpose,
- live-image observation,
- temporary remote control subject to operator permission,
- operator responsibility/controller transparency,
- session-information retention,
- explicitly unspecified protocol/deployment/performance/latency/regulatory information and open product questions.

The benchmark also showed that a general-purpose LLM can jump too early to modeling choices such as State Machine/Guard. Therefore Turing shall distinguish engineering meaning from later model-structure decisions.

The benchmark is diagnostic only and shall not become Project authority.

---

## Recovery Audit

Before implementation changes, trace the active Source-to-Human-Review path end-to-end.

For every material component classify:

```text
KEEP
MOVE
REDUCE
BYPASS
REMOVE / RETIRE
```

The audit shall answer:

1. What exact content is supplied to each LLM call?
2. Which inputs are Engineering Source vs reference/context/instruction?
3. Where are source-grounded anchors first established?
4. Where is a new subject identity first created?
5. Where do personas begin to create independent subject sets?
6. Which P4 semantic-extraction / semantic-consensus components are active in the live path?
7. Why does current P9 derivation appear before the first Engineering Human Review?
8. Which D3/D4 responsibilities remain necessary once evidence-centered subject identity is restored?
9. Which contracts are current authority, and which are legacy compatibility ballast?
10. Can the corrected path reuse existing Source Projection, Information Unit, consensus, Human Review and Approved Input infrastructure?

No new end-to-end LLM run should be used as improvement evidence until this audit identifies and corrects the source-contamination / subject-multiplication path.

---

## CATIA / Presentation Rule

Intended future high-level System Behavior:

```text
REFERENCE KNOWLEDGE
        │ guidance only
        ▼
ENGINEERING SOURCE
        ↓
Register Source
        ↓
Prepare Source
        ↓
Deterministic Source Projection
        ↓
Specialized Evidence Detection Agent
        ↓
Source-Grounded Evidence
        ↓
 ┌──────┼──────┐
 ▼      ▼      ▼
P1     P2     P3
Interpret / Classify the SAME Evidence
 └──────┼──────┘
        ↓
Consensus / Variance
        ↓
optional Semantic Normalization / Ontology Alignment
        ↓
Human Engineering Review
        ↓
Approved Engineering Information
        ↓
 ┌──────┼──────┐
 ▼      ▼      ▼
Model  Model  Model
Persona Persona Persona
 └──────┼──────┘
        ↓
Architecture / Model Candidate Derivation
        ↓
Candidate Consolidation
        ↓
Model Candidate Review
        ↓
Approved Internal Model
        ↓
SysML v2
```

Add this to the authoritative CATIA model only after the implementation is aligned and ADR-027 is accepted. Do not model it merely to improve the Monday presentation.

---

## Status and Next Decision

ADR-027 is `Accepted` as the governing architecture-recovery direction.

The completed Source-to-first-Human-Review audit established that the primary
BLK-003 root cause is the mixing of evidence detection, persona interpretation
and pre-review model derivation.

Implementation proceeds incrementally:

```text
R1  Accept/document ADR-027 and thesis finding
R2  Introduce source-grounded Evidence contract and persistence
R3  Add specialized Evidence Detection Agent and Source Preparation
R4  Make interpretation personas consume the same persisted Evidence
R5  Move model derivation behind Human Engineering Approval and evaluate
    the required downstream modeling personas
```

After at least one material corrected processing path exists:

- run focused automated tests,
- run one bounded real single-source LLM test,
- evaluate source purity, model relevance, source grounding, persona behavior
  on shared Evidence, consensus/variance and Human Review usability,
- retain a successful persisted run as the preferred Monday demo reference.
