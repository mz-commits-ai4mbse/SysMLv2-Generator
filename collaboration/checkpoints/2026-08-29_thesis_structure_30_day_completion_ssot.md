# Thesis Structure / 30-Day Completion Plan — SSOT

Date: 2026-08-29
Status: Accepted thesis-completion planning checkpoint
Repository: `mz-commits-ai4mbse/SysMLv2-Generator`
Related thesis repository: `mz-commits-ai4mbse/Masterarbeit`

## 1. Purpose

This checkpoint freezes the agreed completion strategy for the remaining Master thesis work and coordinates three workstreams that now proceed in parallel:

1. close the thesis-critical Multi-Source gap (`BLK-002`) and prepare the Safe Demo;
2. complete the CATIA Magic SysML v2 engineering model to the required System and Subsystem depth;
3. restructure, populate and finalize the written thesis around the actual implemented information flow and the empirical evidence already available in the repositories.

The internal submission target is approximately 30 days from this checkpoint, i.e. around `2026-09-28`. The formal thesis deadline remains `2026-10-15`. The difference is intentional contingency reserve and shall not be consumed by unbounded feature work.

Governing completion rule:

> The remaining phase is primarily an evidence-integration, architecture-completion and scientific-writing phase, not a new open-ended product-development phase.

## 2. Current technical baseline

Current coordination baseline on `main` before this checkpoint:

`e0fd283e3be3234f16e35e000fb015cc6fb7f3a8`

Commit:

`Checkpoint presentation state and Multi-Source demo transition`

Protected implementation rollback point:

`6d9a600dfa1883d5d6b57f40bfb870ebf6e4cdd6`

Accepted single-source evidence:

```text
Project 000116 Gate 3:              PASS
real SYSIDE validation:             PASS
Human release / publication:        PASS
complete regression:                6100 passed
```

`BLK-002 — Cross-Source Processing Artifact Identity Collision` remains the next technical task and is classified:

```text
THESIS-CRITICAL
DEMO-CRITICAL
```

The Safe Demo is gated by genuine Multi-Source acceptance.

## 3. Central thesis narrative

The final thesis shall not be organized as disconnected descriptions of tools, agents or source-code modules. Its primary red thread is the actual path taken by engineering information through the implemented system:

```text
heterogeneous Legacy Sources
→ Project / Source Context
→ deterministic Source Preparation
→ source-grounded Evidence
→ Engineering Subjects
→ Persona Interpretation
→ Semantic / Cross-Source Consolidation
→ Human Engineering Review
→ Approved Engineering Information
→ Architecture / Target-Model Formulation
→ Human Model Quality Review
→ deterministic SysML v2 Generation
→ external SYSIDE Validation
→ Final Human Release / Publication
```

This same information path shall be reused with different perspectives:

- Architecture chapter: why each responsibility / boundary exists.
- Implementation chapter: how each responsibility is realized in the prototype.
- Evaluation chapter: what evidence shows that it works and which failure modes were found.

The overall scientific chain should read:

```text
research problem
→ literature-derived need
→ stakeholder / system requirements
→ R/F/L architecture
→ implemented information-processing architecture
→ empirical verification / validation
→ demonstrated limitations
→ answered research questions
→ final contribution and outlook
```

## 4. Parallel workstreams

### Track A — BLK-002 and Safe Demo

Purpose:

- close the exact Multi-Source identity / provenance blocker;
- establish genuine project-level Multi-Source processing;
- preserve source-neutral consideration and exact provenance;
- retain Human authority for contradiction / variance resolution;
- preserve the validated single-source path;
- prepare a genuine persisted Multi-Source demo state;
- rehearse the Safe Demo / Kochshow.

Execution discipline:

```text
read-only audit
→ minimal contract
→ bounded implementation slices
→ focused tests
→ complete regression
→ real Multi-Source E2E
→ downstream SysML / SYSIDE
→ Human acceptance
→ demo-state freeze
```

No additional backlog is reopened merely because it exists.

### Track B — CATIA engineering model completion

The development method remains based on RFLP as a methodological reference, but the thesis model intentionally elaborates only:

```text
Requirements
→ Functional
→ Logical
```

The Physical layer is intentionally not elaborated for the thesis scope.

Rationale:

- the investigated system is software-centric;
- physical / deployment infrastructure is not the research object;
- this does **not** claim that software systems have no physical architecture;
- hardware deployment, compute topology, runtime infrastructure, network deployment and comparable physical concerns are outside the selected system boundary.

The thesis shall therefore describe the approach accurately as a bounded `R/F/L` application of an RFLP-oriented engineering method.

#### System-level completion

Synchronize the Stakeholder and System model to the final implementation, including where required:

- System Requirements;
- System Functions;
- Logical Components;
- principal information objects and flows;
- Human authority boundaries;
- LLM / external context dependencies;
- traceability and allocation relations;
- consistency with the actual prototype workflow.

#### Subsystem-level completion

Expected scale:

`approximately 8–9 thesis-relevant subsystems`

The exact number is not a quota; decomposition quality takes precedence.

Each selected subsystem should have a bounded but meaningful set of:

- derived Subsystem Requirements;
- Subsystem Functions;
- Logical responsibilities / Logical Components;
- relevant interfaces and information flows;
- Requirement → Function traceability;
- Function → Logical allocation;
- relevant System → Subsystem derivation / allocation;
- selected relations to external contexts or neighboring subsystems.

The Subsystem model shall **not** reproduce the Python repository structure.

Explicitly not the intended modeling depth:

```text
Python package
→ module
→ class
→ function
```

The roughly 30+ implementation modules are implementation evidence, not the target SysML abstraction level.

Rule:

> The repository describes software realization. CATIA describes the engineering architecture.

#### CATIA / thesis division of responsibility

The `.mdzip` will be submitted with the thesis and is an explicit engineering artifact. The written thesis therefore need not duplicate every Requirement, Function, Logical Component, allocation, interface or trace relation.

However, the thesis must remain scientifically understandable without opening the model.

Rule:

> The thesis explains the argument and important architecture decisions. CATIA contains the complete engineering structure and detailed traceability.

Representative elements, architecture-driving relationships and key diagrams belong in the thesis. Complete populations may remain in the CATIA artifact where repetition would add little argumentative value.

### Track C — Thesis restructuring and writing

Writing starts in parallel with BLK-002 and CATIA work. It must not wait until all implementation and modeling work is finished.

The first writing task is not bulk prose generation. It is a final `Thesis Architecture` that maps:

```text
Research Question
→ thesis claim
→ evidence
→ CATIA artifact
→ repository / WP-12 evidence
→ literature support
→ figure / table
→ open work
```

This matrix shall become the writing control structure.

## 5. Recommended final thesis structure

### Chapter 1 — Introduction

Target: approximately 5–7 pages.

Topics:

- motivation;
- Brownfield / heterogeneous legacy-information problem;
- problem statement;
- objective;
- main and sub research questions;
- scope and claim boundary;
- structure of the thesis.

The introduction should explain why a governed architecture is investigated rather than treating direct LLM prompting as sufficient engineering automation.

### Chapter 2 — Foundations and State of the Art

Target: approximately 12–15 pages.

Topics:

- MBSE;
- SysML v2 / textual notation;
- Architecture as Code / Everything as Code;
- Brownfield Engineering / heterogeneous legacy information;
- LLMs and agent-based engineering approaches;
- semantic normalization / ontologies / reference knowledge;
- Human-in-the-Loop / Human authority;
- model / metamodel validation;
- SysML v2 tooling;
- synthesis of the literature search;
- resulting research gap.

Existing LSP / LSR material and the bibliography shall be reused and integrated rather than recreated. A final literature refresh is required before submission.

### Chapter 3 — Research and Development Methodology

Target: approximately 8–10 pages.

This chapter must describe the **actual** method, not only the original plan.

#### 3.1 Research method

- literature-search method;
- derivation of research gap;
- research questions;
- evidence strategy;
- evaluation logic.

#### 3.2 Architecture-development method

Method reference: `RFLP`
Bounded thesis instantiation: `R/F/L`

Topics:

- stakeholder-oriented derivation;
- Requirements → Functions → Logical Architecture;
- Zig-Zag / iterative derivation where used;
- System → Subsystem decomposition;
- traceability;
- allocation;
- rationale for leaving Physical Architecture outside scope.

#### 3.3 Prototype-development method

The implementation evolved through governed vertical slices rather than one large code-generation step:

```text
architecture / contract
→ bounded implementation slice
→ focused verification
→ finding
→ correction
→ regression
→ next slice
```

Relevant mechanisms include:

- ADRs;
- SSOT checkpoints;
- immutable manifests / fingerprints;
- fail-closed boundaries;
- Human acceptance before integration;
- feature branches;
- repository reality as implementation authority.

#### 3.4 Verification and Validation method

Verification and Validation are a methodological strand and must be introduced here before their results appear later.

Distinguish as appropriate:

- unit / contract verification;
- module verification;
- integration / workflow verification;
- repository regression;
- WP-12 controlled E2E evaluation;
- external SYSIDE validation;
- Human engineering review / validation;
- claim-boundary assessment.

### Chapter 4 — Stakeholder and System Requirements

Target: approximately 5–7 pages.

Topics:

- relevant stakeholder roles;
- User Needs;
- Stakeholder / System Requirements;
- Use Cases;
- architecture-driving constraints;
- Human-authority requirements;
- traceability from stakeholder intent to system behavior;
- representative examples.

Do not reproduce the complete CATIA requirement population in prose.

### Chapter 5 — Turing Generator System Architecture

Target: approximately 12–15 pages.

Topics:

- System Context;
- architecture principles;
- Three-Layer Architecture;
- Data / Process / Knowledge responsibilities;
- Human-in-the-Loop as architecture-wide governance principle;
- LLM inference as supporting capability without approval authority;
- Logical Architecture;
- System Functions;
- information objects;
- high-level information transformation flow;
- SFB_004;
- SFB_005;
- evidence and traceability backbone;
- source-neutral / provenance-preserving Multi-Source principle after BLK-002;
- bounded SysML v2 target-model concept.

The principal red-thread diagram should be introduced here and reused conceptually in Chapters 6–8.

### Chapter 6 — Subsystem Architecture

Target: approximately 8–12 pages.

Purpose:

Show systematic decomposition from the System level to approximately 8–9 thesis-relevant software subsystems.

Topics:

- decomposition criteria;
- subsystem responsibilities;
- derived requirements;
- subsystem functions;
- logical realization;
- interfaces / information flows;
- allocations;
- cross-subsystem traceability;
- selected detailed CATIA diagrams.

The thesis shows representative and architecture-critical content. The `.mdzip` carries the full model.

### Chapter 7 — Prototype Implementation

Target: approximately 12–15 pages.

This chapter follows the **real implemented information path**, not an outdated generic `JSON → Agent → Report → Code` sequence.

Recommended sequence:

1. Project and Source registration;
2. deterministic Source Projection / preparation;
3. analysis units;
4. source-grounded Evidence Detection;
5. Engineering Subject construction;
6. configurable Persona Interpretation;
7. consensus / variance evidence where applicable;
8. Semantic Consolidation;
9. Multi-Source project-level consolidation after BLK-002;
10. Human Engineering Review;
11. Approved Engineering Information;
12. model placement / assembly;
13. Internal Engineering Model;
14. Target-Model Formulation;
15. Human Model Quality Review;
16. deterministic SysML v2 serialization;
17. external SYSIDE validation;
18. Final Model Review / Human release / publication.

For each major stage explain purpose, architectural responsibility, key artifact / contract, Human vs. AI authority, important provenance / fingerprint behavior, and how implementation realizes architecture.

Avoid class-by-class or module-by-module code documentation.

### Chapter 8 — Verification, Validation and Evaluation

Target: approximately 10–14 pages.

This is the empirical core.

Topics:

- evaluation design;
- test hierarchy;
- WP-12 controlled dry-run logic;
- significant findings and what they revealed;
- corrective architecture / implementation changes;
- focused tests;
- repository regression;
- Golden E2E;
- Gate-3 real validation;
- real SYSIDE validation;
- Human review / release;
- BLK-002 and genuine Multi-Source result;
- Safe-Demo evidence where useful;
- claim boundaries;
- explicit answer mapping to research questions.

WP-12 shall not appear merely as a bug list. It should be presented as formative system verification that exposed architecture-relevant failure modes and drove bounded corrections.

### Chapter 9 — Discussion

Target: approximately 7–10 pages.

Topics:

- interpretation of results;
- what the PoC demonstrates;
- what it does not demonstrate;
- validity / evidence quality;
- limitations;
- bounded SysML v2 construct coverage;
- Turing-RFL target-framework dependency;
- text-oriented input boundary;
- LLM uncertainty;
- Human authority dependency;
- tool limits;
- transferability to other Brownfield scenarios;
- production-readiness boundary;
- implications of Multi-Source processing;
- threats to generalization.

Explicitly distinguish technical model validity from engineering correctness.

### Chapter 10 — Reflection on LLM-Assisted Prototype Development

Target: approximately 5–8 pages.

This is a structured methodological / engineering reflection on using an LLM as the principal coding assistant for a complex prototype where the Human author cannot independently implement the complete software system using classical programming skills.

It is **not** presented as a controlled empirical study of coding LLMs.

#### 10.1 Starting situation and roles

Human responsibilities:

- research objective;
- system intent;
- requirements;
- architecture decisions;
- scope;
- acceptance criteria;
- review;
- engineering authority.

LLM support:

- code proposal / implementation assistance;
- test construction assistance;
- repository analysis;
- refactoring suggestions;
- documentation support.

#### 10.2 Effective working patterns

Candidate learnings to document where supported by project history:

- small bounded slices were more reliable than broad implementation prompts;
- explicit contracts / ADRs improved consistency;
- persistent SSOTs reduced context drift;
- repository reality must outrank conversational memory;
- automated tests became a key communication and assurance interface;
- deterministic fingerprints / manifests reduced ambiguity;
- feature branches protected Known-Good baselines;
- explicit Human acceptance prevented silent scope drift;
- `audit → contract → implementation → test` was more robust than open-ended "fix it" prompts;
- complete regression was especially important because the Human could not manually review all implementation details.

#### 10.3 Observed failure modes

Potential categories, only where supported by evidence:

- incorrect assumptions about repository state;
- architecture drift from incomplete context;
- locally plausible code violating broader contracts;
- over-broad fixes;
- tests drifting toward observed instead of intended behavior;
- chat-history / repository mismatch;
- unintended interaction between individually reasonable changes.

#### 10.4 Quality-assurance lessons

Central observation:

> LLM-assisted coding did not remove the need for engineering authority; it shifted the Human contribution from direct code production toward architecture, specification, verification, acceptance and scope control.

A carefully bounded analogy may be discussed:

- during prototype development, the Human retained authority over the coding LLM;
- inside the Turing Generator, the Human retains authority over engineering AI transformations.

Do not overstate this analogy as empirical proof.

#### 10.5 Limits and transferability

Discuss:

- dependence on precise contracts / prompts;
- need for tests and version control;
- limited Human source-code inspection capability;
- importance of reproducible repository evidence;
- risks for safety-critical / regulated development;
- difference between a thesis PoC and production software engineering.

### Chapter 11 — Conclusion and Outlook

Target: approximately 4–6 pages.

Topics:

- concise summary;
- explicit answers to main and sub research questions;
- contribution of the architecture;
- contribution of implementation / empirical evaluation;
- important limitations;
- future work.

Future work may include:

- broader model / notation coverage;
- broader source types;
- reusable subsystem / domain adaptations;
- source-authority policies beyond the source-neutral PoC;
- productization / UX;
- Adaptive Human Feedback Learning.

Authority for the adaptive-learning concept:

`collaboration/checkpoints/Thesis_Outlook_Adaptive_Human_Feedback_Learning.md`

It remains future work and must not be claimed as implemented.

## 6. Research-question audit

The current main research question remains broadly aligned with the implemented system and should be treated as the default unless formal thesis governance requires otherwise:

> How must an information-processing architecture be designed to safely transform heterogeneous legacy information through a systematic assessment and synthesis framework into valid SysML v2 structures?

The sub-questions require an early audit against final evidence.

Special attention:

- Input Assessment claims shall not imply proof of "hallucination-free" operation;
- Human-in-the-Loop / Effective Intervention is now strongly supported by repeated authority boundaries;
- ontology / guideline claims must not overstate general Plug-and-Play guarantees;
- bounded or negative answers are scientifically acceptable where evidence does not support the original stronger formulation.

The Research Questions drive claims. Claims shall not be weakened or rewritten merely to make the implementation appear more successful.

## 7. Target length

Planning corridor for substantive main content:

`approximately 80–100 pages`

Preferred target:

`approximately 80–90 pages`

The rendered PDF will be longer after front matter, lists, bibliography and appendices.

The CATIA `.mdzip` reduces the need to reproduce complete engineering-model populations in prose, but it does not replace the need to explain the scientific argument in the thesis.

## 8. 30-day execution roadmap

The roadmap is intentionally parallel.

### Days 1–4 — BLK-002 begins / thesis architecture freeze

Track A:

- BLK-002 read-only audit;
- freeze minimal Multi-Source contract;
- begin bounded implementation if accepted;
- protect single-source Known-Good.

Track C:

- audit current thesis structure;
- freeze final chapter architecture;
- audit research questions;
- create Research Question → Claim → Evidence matrix;
- map CATIA / repo / WP-12 / Gate-3 evidence to chapters;
- identify literature-refresh gaps.

Stable writing may already begin.

### Days 3–10 — CATIA completion in parallel

Track B:

- synchronize Stakeholder / System R/F/L levels;
- complete missing System Requirements / Functions / Logical allocations;
- define Subsystem decomposition;
- elaborate approximately 8–9 Subsystems;
- derive selected Subsystem Requirements;
- define Functions;
- define Logical responsibilities;
- establish interfaces / flows / allocations / traceability;
- validate CATIA consistency;
- prepare thesis-oriented diagrams.

Do not descend into Python module or class architecture.

### Days 4–8 — Target window for BLK-002 acceptance / demo-state creation

Target sequence:

- focused Multi-Source implementation;
- regression;
- real joint Multi-Source E2E;
- downstream deterministic SysML v2;
- SYSIDE validation;
- Human acceptance;
- genuine persisted Multi-Source demo state.

If BLK-002 expands into broad redesign, stop and invoke a thesis scope decision rather than consuming the writing schedule.

### Days 6–18 — Main writing block

Primary chapters:

- Chapter 2 Foundations / State of the Art;
- Chapter 3 Methodology;
- Chapter 4 Requirements;
- Chapter 5 System Architecture;
- Chapter 6 Subsystem Architecture;
- Chapter 7 Prototype Implementation.

### Days 15–22 — Verification / evaluation block

Primary focus:

- WP-12 evidence;
- findings and bounded corrections;
- Gate-3 result;
- Multi-Source result;
- external SYSIDE evidence;
- Human authority evidence;
- research-question result mapping.

Write Chapter 8.

### Days 20–25 — Discussion and LLM-development reflection

Write:

- Chapter 9 Discussion;
- Chapter 10 LLM-assisted-development reflection.

Complete limitations, transferability, validity, system boundaries and engineering lessons.

### Days 24–27 — Final synthesis

Write / finalize:

- Chapter 1 Introduction;
- Chapter 11 Conclusion and Outlook;
- Abstract;
- explicit answers to Research Questions;
- Adaptive Human Feedback Learning outlook integration.

Internal content-complete target:

`Day 27`

### Days 28–30 — Submission QA reserve

No planned feature development.

Tasks:

- full-document consistency pass;
- terminology normalization;
- citation completeness;
- bibliography / Biber;
- figure and table quality;
- cross references;
- acronyms / notation;
- CATIA ↔ thesis consistency;
- repo evidence ↔ thesis claim consistency;
- Research Question ↔ Result ↔ Conclusion consistency;
- PDF compilation;
- `.mdzip` openability check;
- final submission package.

The final three days are contingency / quality reserve, not nominal writing capacity.

## 9. Scope guardrails

### Allowed technical work

- BLK-002 because it is thesis-critical and demo-critical;
- corrections required for genuine Multi-Source acceptance;
- defects that block accepted thesis evidence;
- CATIA synchronization to accepted implementation;
- bounded demo stabilization;
- documentation / evidence extraction.

### Not automatically allowed

- unrelated BLK / SEM / OBS backlog;
- broad UX redesign;
- new ontology architecture;
- Adaptive Human Feedback Learning implementation;
- production hardening unrelated to evidence;
- broad SysML notation expansion;
- modeling all Python modules;
- speculative CATIA architecture;
- non-thesis product features.

Governing question:

> Does this work materially improve a required thesis claim, required empirical evidence, final architecture consistency or submission quality?

If not, defer it.

## 10. Freeze strategy

### Technical feature freeze

After:

```text
BLK-002 accepted
→ real Multi-Source E2E
→ Safe-Demo state
→ complete regression
```

No new thesis-unnecessary prototype features.

### CATIA architecture freeze

After:

```text
final System R/F/L synchronization
→ Subsystem R/F/L completion
→ allocation / traceability audit
→ implementation consistency audit
```

Only corrections after freeze.

### Thesis content freeze

Target: `Day 27`.

Days 28–30 are QA / correction only.

## 11. Evidence reuse strategy

Reuse rather than recreate:

- authoritative CATIA `.mdzip`;
- `collaboration/CATIAMSOSA_TextualNotation.txt`;
- accepted ADRs;
- SSOT checkpoints;
- WP-12 findings / protocol / evaluation evidence;
- Project `000116` Gate-3 evidence;
- Golden E2E evidence;
- Multi-Source BLK-002 evidence after closure;
- complete regression results;
- real SYSIDE validation;
- presentation diagrams where useful;
- LSP / LSR and bibliography from the thesis repository.

The thesis shall explain and synthesize evidence, not paste internal repository documents verbatim.

## 12. Immediate next actions

Next technical chat:

```text
BLK-002 read-only audit
→ minimal contract
→ accepted slices
→ bounded implementation
```

Parallel thesis work:

```text
final thesis structure audit
→ Research Question / Claim / Evidence matrix
→ begin stable chapter content
```

Parallel CATIA planning:

```text
final System-level delta
→ define approximately 8–9 Subsystem decomposition
→ freeze Subsystem modeling DoD
→ model systematically
```

## 13. Completion principle

The project now contains more technical material than the thesis should reproduce. The remaining challenge is:

```text
select
→ structure
→ trace
→ explain
→ evaluate
→ discuss
```

rather than inventing more implementation.

Final governing statement:

> The thesis shall tell one coherent evidence-backed story: how heterogeneous legacy engineering information is transformed through a source-grounded, traceable and Human-governed architecture into an externally validated SysML v2 artifact — and what was learned from engineering and implementing that architecture with LLM assistance.
