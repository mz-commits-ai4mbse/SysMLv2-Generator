# WP-12 Findings — Turing Generator

<!-- BEGIN SSOT UPDATE 2026-08-29 MULTISOURCE DEMO TRANSITION -->
## 2026-08-29 — BLK-002 priority / acceptance decision

This block does not close or technically alter BLK-002.

```text
BLK-002 — Cross-Source Processing Artifact Identity Collision
status: OPEN / BLOCKING
priority: THESIS-CRITICAL + DEMO-CRITICAL
```

The PoC shall demonstrate multiple heterogeneous legacy Sources contributing to
one project-level engineering result. Repeated independent single-source runs are
not sufficient.

Bounded acceptance semantics:

- no a-priori Source authority hierarchy;
- exact Source / Run / Attempt / Artifact provenance retained;
- equivalent engineering meaning may consolidate across Sources while retaining
  all contributing evidence;
- Source-unique information remains available;
- cross-source contradiction / material variance remains explicit;
- Human Review resolves engineering authority;
- no silent winner selection by Source order / type;
- no Project-specific special case.

BLK-002 may close only after technical reproduction/correction, focused tests,
complete regression, a real joint Multi-Source Project reaching project-level
Human Review, demonstrated cross-source consolidation with provenance, preserved
source-unique information, explicit conflict handling, and successful continuation
through the existing governed downstream model / SysML / validation path.

Implementation must occur on the disposable branch:

`feature/blk-002-multi-source`

If the correction ceases to be bounded or destabilizes Known-Good single-source
behavior, stop and reassess before integration.
<!-- END SSOT UPDATE 2026-08-29 MULTISOURCE DEMO TRANSITION -->

<!-- BEGIN WP12 GOLDEN CLOSEOUT STATUS 2026-08-25 -->
## 2026-08-25 — Golden E2E closeout / current finding status authority

This block supersedes older "current status" wording below while preserving those
sections as historical test evidence.

Current result:

```text
WP-12 single-source Golden E2E: PASS
Formal multi-source Stage-A: FAILED WITH BLOCKER — BLK-002
Current blocking finding for multi-source acceptance: BLK-002 only
```

Known-Good baseline:

```text
924bf27d2ee4ca07c1d04da2c777ce31b7632e97
wp12-golden-e2e-2026-08-25
```

Current dispositions relevant to the completed single-source path:

```text
BLK-003  semantic recovery             RESOLVED / single-source E2E validated
BLK-004  Approved Input promotion      RESOLVED / live retest PASS
BLK-005  AEI -> model handoff           RESOLVED / live retest PASS
BLK-006  model-generation recovery     RESOLVED BY ARCHITECTURAL CORRECTION /
                                        Golden E2E retest PASS
BLK-007  Assembly responsibility       RESOLVED / live retest PASS

SEM-012  meaning vs representation     IMPLEMENTED IN CURRENT SINGLE-SOURCE PATH
SEM-015  Target-Model Formulation      PARTIALLY IMPLEMENTED /
                                        Golden E2E scope validated;
                                        general target-type coverage OPEN
SEM-015-F01                            DEFERRED / non-blocking

WP12-BLK-SEM015-L-001
          Final Review handoff         RESOLVED / FRV-000002 -> FRD-000001 ->
                                        OUT-000001
```

`SEM-015` is no longer unimplemented: its architecture and the exact Golden-E2E
scope are live validated. It is, however, not yet complete as a general target-model
formulation capability. The current formulation proposal builder is deliberately
bounded to the BLK-006 recovery population (`stakeholder` elements and `traces_to`
relationships). General coverage must be extended together with SEM-011 target-model
construct coverage. `SEM-015-F01` remains a separate deferred optimization.

Historical sections below that state `BLK-006 OPEN`, `SEM-015 OPEN` or
`WP-12 overall FAILED WITH BLOCKER` describe the system at the time those findings
were observed. They must not be read as the current single-source status.

Thesis-oriented synthesis:

`collaboration/audits/wp12_formative_self_test_report.md`
<!-- END WP12 GOLDEN CLOSEOUT STATUS 2026-08-25 -->

<!-- BEGIN FINDINGS UPDATE 2026-08-25 TARGET MODEL TEMPLATES -->
## SEM-015 preparation status update — 25.08.2026

The non-production scaffolding for `SEM-015` has now been created and JSON-validated:

```text
context/requirements/requirements_authoring_profile.json
context/sysml/sysml_v2_target_model_profile.json
```

This changes only the preparation state of the finding.

`SEM-015` remains:

```text
ACCEPTED MAJOR FINDING / OPEN
```

The full Target-Model Formulation architecture, source-derived Requirements
Authoring rules, Human authority integration and downstream processing changes have
**not** been implemented.

Current WP-12 priority remains `BLK-006` and completion of the same Project `120412`
single-source E2E.

<!-- END FINDINGS UPDATE 2026-08-25 TARGET MODEL TEMPLATES -->


<!-- BEGIN FINDINGS UPDATE 2026-08-25 C6 -->
## WP-12 Live Update — 25.08.2026

Current Project `120412` live chain:

```text
Human Engineering Review
→ Approved Engineering Information
→ Model Placement Review
→ Model Assembly
→ Final Model Review
→ IEM-000001
→ SysML v2 generation preflight BLOCKED
```

`IEM-000001`: 13 elements, 3 relationships.

Current BLK-006 evidence is no longer an opaque LLM-generation failure. The
authority-backed SysML builder reaches the existing Phase-J preflight and is blocked
by exactly four unsupported mappings:

```text
IME-000001 stakeholder -> J2_ELEMENT_001 unsupported
IME-000003 stakeholder -> J2_ELEMENT_001 unsupported
IMR-000001 traces_to   -> J2_REL_009 unsupported
IMR-000003 traces_to   -> J2_REL_009 unsupported
```

The `dependency` Relationship passes.

BLK-007, discovered while retesting BLK-006, has been corrected and live retested
PASS: Model Assembly no longer invokes the Model Placement persona team for
Relationship representation.

New accepted MAJOR finding:

```text
SEM-015 — Target-Model Formulation is missing as an explicit processing stage
for all target-model element and relationship representations.
```

Additional accepted principle:

```text
Relevant/context information is not automatically model content.
```

The current product-overview source is retained intentionally as a difficult
mixed/context-heavy boundary case.

A Requirements Authoring / Target Model template patch has been prepared but NOT
applied and is not part of the current implementation baseline.
<!-- END FINDINGS UPDATE 2026-08-25 C6 -->


**Stand:** 24.08.2026
**Basis:** bisherige WP-12 Dry-Run-, Architektur-Recovery-, Live-E2E- und Demo-Hardening-Evidenz bis zum aktuellen Live-Checkpoint vom 24.08.2026.
**Formaler Stage-A-Test:** `WP12-E2E-DRY-001`, Project `308131`
**R4c Single-Source Recovery-/Live-E2E-Evidenz:** Project `120412`, `RUN-000001`, `ATT-000001`
**Aktueller WP-12-Verifikationsstatus:** `FAILED WITH BLOCKER` — aktive Blocker: `BLK-002`, `BLK-006`

> Hinweis: Dieses Dokument ist das kanonische WP-12 Finding Register. Historische Beobachtungen bleiben als Evidenz erhalten. Ein Finding wird nur durch explizite Korrektur + Retest als geschlossen/corrected markiert.

### Teststatus-Regel ab 24.08.2026

```text
PASS
PASS WITH FINDINGS
FAILED WITH BLOCKER
BLOCKER RESOLVED -> RETEST -> PASS / PASS WITH FINDINGS
```

Die frühere Statusformulierung `IN PROGRESS / INTERRUPTED FOR BLOCKING DEFECT CORRECTION` wird als historische Beschreibung erhalten, aber für die aktuelle Testklassifikation durch die obige Regel ersetzt. Ein `FAILED WITH BLOCKER` bedeutet **nicht**, dass der Testlauf verworfen oder neu gestartet wird: Project, Run und Defektevidenz bleiben erhalten und der Test wird nach der Korrektur am betroffenen Gate fortgesetzt/retestet.

---

## 1. Kurzfassung

WP-12 hat mehrere echte Architektur-, Integrations-, Governance- und UX-Defekte sichtbar gemacht und damit die Recovery-Richtung wesentlich geprägt. Die frühere semantische Architektur wurde durch die R4c-Kette mit source-grounded Evidence, gemeinsamer Subject Discovery, Canonical Subjects vor der Persona-Interpretation und expliziter Human Authority korrigiert.

Der aktuelle Single-Source-Live-E2E-Pfad auf Project `120412` hat inzwischen live nachgewiesen:

- real LLM Processing bis Human Review,
- 24 Canonical Subjects mit fachlich plausibler Subject-/Classification-Qualität,
- vollständige Subject- und Relationship-Entscheidungen,
- erfolgreiche Finalization,
- 17 aktive Approved Inputs,
- erfolgreiche Ableitung von Approved Engineering Information,
- korrekten Phase-H-Handoff mit 17 Approved Subjects und 21 accepted semantic Relationships,
- explizite Behandlung von 6 Relationships zu nicht model-promotierbaren Open Questions als `intentionally_not_projected`.

Dabei wurden `BLK-004` und `BLK-005` entdeckt, korrigiert und im selben Live-Pfad erfolgreich retestet. Der erste echte LLM-assisted Model-Proposal-Generierungsversuch ist aktuell jedoch an `BLK-006` fehlgeschlagen.

Parallel bleibt `BLK-002` für den formalen Multi-Source-Stage-A-Test offen. Deshalb ist der **gesamte WP-12-Verifikationsstatus aktuell `FAILED WITH BLOCKER`**. Nach Auflösung und erfolgreichem Retest aller aktiven Blocker kann der Test bei verbleibenden nicht-blockierenden Findings auf `PASS WITH FINDINGS` wechseln.


---

# 2. Technische und architektonische Findings

## BLK-001 — Derivation Producer Contract zu permissiv

**Status:** `CORRECTED / focused validation passed`

### Beobachtung
Der Output-Contract des Derivation-Assessor war zunächst zu offen formuliert. Dadurch konnten formal plausible Agent Outputs entstehen, die der strikt validierende Downstream-Adapter nicht zuverlässig akzeptieren konnte.

In einer frühen Verifikation war nur ein Teil der erzeugten Derivation Outputs strikt adaptierbar. Nach der Härtung des Producer Contracts wurde die strikte Adaptation für die relevante Testkonfiguration erfolgreich verifiziert.

### Bedeutung
Der Finding zeigt, dass der Agent Output nicht nur semantisch sinnvoll, sondern auch maschinell eindeutig und stabil strukturiert sein muss. Gleichzeitig darf semantische Unsicherheit nicht mit einem Integritätsfehler verwechselt werden.

### Konsequenz
- Prompt-/Schema-Contract wurde gehärtet.
- Unklare Modellierungsinterpretationen dürfen als Human-Review-Frage weitergereicht werden.
- Verletzungen von Identität, Provenance oder struktureller Integrität bleiben fail-closed.

---

## BLK-002 — Cross-Source Processing Artifact Identity Collision

**Status:** `OPEN / BLOCKING`

### Beobachtung
Im Multi-Document-Pfad kann eine Processing-Artifact-Identität über mehrere Source Runs hinweg referenziert werden. Dadurch ist die Eindeutigkeit der Artifact-Zuordnung im projektweiten Multi-Source-Processing nicht ausreichend abgesichert.

### Bedeutung
Die Traceability- und Identity-Garantie des Systems ist an dieser Stelle verletzt. Solange nicht eindeutig feststeht, zu welchem Source/Run ein Artifact gehört, darf die Verarbeitung nicht als belastbarer Multi-Document-End-to-End-Pfad akzeptiert werden.

### Konsequenz
- Multi-Document-Processing ist formal noch nicht akzeptiert.
- `WP12-E2E-DRY-001` ist als `FAILED WITH BLOCKER — BLK-002` klassifiziert; Project und Evidenz bleiben erhalten und nach der Korrektur wird am betroffenen Gate retestet.
- Demo-/Live-Pfad bleibt zunächst **Single-Source**.
- Kein Multi-Source-Happy-Path darf als verifiziert dargestellt werden.

---

## BLK-003 — Semantic Effectiveness / Engineering-Subject Quality

**Status:** `RECOVERY IMPLEMENTED / LIVE SINGLE-SOURCE VALIDATED / CLOSURE PENDING COMPLETE E2E`

BLK-003 war der zentrale semantische Finding des früheren WP-12-Pfads. Die ursprüngliche Persona-first-/nachgelagerte Konsolidierungsarchitektur wurde durch die R4c-Architektur ersetzt. Der Live-Run auf Project `120412` zeigt eine deutlich verbesserte source-grounded Subject Formation und brauchbare Engineering-Semantik. BLK-003 wird dennoch erst nach erfolgreichem vollständigem E2E-Abschluss geschlossen; aktuell blockiert `BLK-006` den Downstream-Nachweis.

### BLK-003.1 — Robustheitskorrekturen

Folgende Sub-Findings wurden technisch adressiert:

- **Evidence Identity Correction:** gleiche Agent-lokale IDs dürfen nicht zu falschen source-übergreifenden Identitäten führen.
- **Human Escalation for unresolved relationship endpoints:** nicht eindeutig auflösbare Relationship-Endpunkte sollen als Human-Review-Frage erhalten bleiben, statt den kompletten Processing Run hart abzubrechen.
- **Service Failure Taxonomy:** semantische Unsicherheit und echte Integritäts-/Vertrauensfehler werden getrennt behandelt.

Leitprinzip:

```text
semantic uncertainty
→ Human Review

untrustworthy identity / evidence / provenance
→ Processing Failure
```


---

## BLK-004 — Approved Input Promotion fails for R4c semantic classification

**Status:** `CORRECTED / LIVE VALIDATED`

### Beobachtung
Im finalisierten R4c-Review konnte die Approved-Input-Promotion zunächst nicht abgeschlossen werden. Ursache war ein Contract-Mismatch: die R4c-Klassifikation ist ein semantisches Tupel aus `information_type`, `modality` und `epistemic_status`, während der Legacy-Promotion-Pfad einen einzelnen skalaren `selected_classification`-Wert erwartete.

### Korrektur / Retest
Die Promotion-Materialisierung wurde an der Boundary gehärtet. Der R4c-Live-Retest auf Project `120412` war erfolgreich:

```text
Created Approved Inputs: 17
Reused:                  0
Skipped Open Questions:  7
Active Approved Inputs: 17
```

Die Human Overrides, u. a. `SUBJ-000007 -> logical_element` und `SUBJ-000015 -> unclassified`, blieben erhalten.

**Testdisposition:** `BLOCKER RESOLVED -> RETEST PASS`

---

## BLK-005 — Approved Engineering Information not authoritative Phase-H input

**Status:** `CORRECTED / LIVE VALIDATED`

### Beobachtung
Die Phase-H-Modellableitung verwendete zunächst ausschließlich aktive `ApprovedInputManifest`s. Accepted semantic Relationships aus dem finalisierten Human Review waren damit nicht Teil des autoritativen Model-Derivation-Handoffs.

### Korrektur
Der Phase-H-Request bindet jetzt:

```text
approved_inputs
+
approved_engineering_information
  - approved Subjects
  - accepted semantic Relationships
```

Die AEI-Authority wird kryptographisch in den Generation Context Fingerprint gebunden. Relationships werden als eigene semantische Phase-H-Eingänge behandelt und nicht als künstliche Approved Inputs materialisiert.

Accepted Open Questions bleiben nicht model-promotierbar. Accepted Relationships mit mindestens einem solchen Endpoint bleiben Teil der Engineering Authority, werden aber explizit als `intentionally_not_projected` geführt.

### Live-Retest Project 120412

```text
Approved Subjects:               17
  mapped                           3
  ambiguous                        8
  unmapped                         6

Accepted semantic Relationships: 21
  mapped                           1
  ambiguous                        0
  unmapped                        14
  intentionally not projected      6
```

**Testdisposition:** `BLOCKER RESOLVED -> RETEST PASS WITH FINDINGS`

---

## BLK-006 — LLM-assisted Model Proposal generation fails in live E2E

**Status:** `OPEN / BLOCKING`

### Beobachtung
Der erste echte LLM-assisted Model-Proposal-Generierungsversuch im R4c-Live-E2E auf Project `120412` endet fail-safe mit:

```text
Model Proposal generation failed safely.
No Candidate Set was treated as approved.
```

### Bedeutung
Der Phase-H-Readiness-/Coverage-Pfad ist erfolgreich, aber der eigentliche Candidate-Generation-Pfad ist noch nicht bis zu einem reviewbaren Candidate Set nachgewiesen. Damit kann der Live-E2E aktuell nicht in Candidate Review / Internal Model / SysML-v2-Downstream fortgesetzt werden.

### Aktueller Stand
- Root Cause: noch nicht diagnostiziert.
- Kein erneuter Generate-Versuch bis zur Diagnose.
- Fail-safe behavior ist positiv: kein fehlgeschlagener Candidate Set wurde als approved behandelt.

**Testdisposition:** `FAILED WITH BLOCKER`

## SEM-001 — Source Purity Regression

**Status:** `CORRECTED IN R4c / LIVE SINGLE-SOURCE VALIDATED; MULTI-SOURCE NOT YET REVALIDATED`

### Beobachtung
Orchestrierungs-, Task- und Prozessinformationen wurden teilweise als positive Engineering Information interpretiert.

Beobachtete Beispiele waren u. a.:

- Raw-input artifact path
- Markdown ingestion report
- Document status heading
- structured placeholder feedback file
- traceability record / placeholder
- task-file content completeness constraint
- project traceability / human-review constraint

### Bedeutung
Diese Inhalte gehören zum Processing-Kontext des Turing Generators, nicht zum fachlichen Systemmodell des analysierten Legacy-Systems. Wenn solche Informationen zu Requirements, System Elements oder anderen Engineering Subjects werden, ist die Source Boundary falsch gesetzt.

### Konsequenz
Es muss technisch erzwungen werden:

```text
Reference / Prompt / Task / Orchestration Context
≠
Engineering Evidence
```

Nur Source-grounded Content aus der eigentlichen Engineering Source darf positive Engineering Information erzeugen.

---

## SEM-002 — Model Relevance Regression

**Status:** `SUBJECT-LEVEL RECOVERY LIVE VALIDATED / MODEL-DERIVATION E2E PENDING BLK-006; TYPE-COVERAGE LIMITATION TRACKED AS SEM-011`

### Beobachtung
Die Kandidatengenerierung beantwortete nicht mehr zuverlässig die zentrale Frage:

> Welches konkrete, SysML-v2-relevante Engineering Concept wird hier vorgeschlagen?

Statt klarer Actors, Requirements, Functions, Interfaces, Constraints, Items oder System-/Component-Kandidaten entstanden teilweise sehr generische Artifact-/Process-Subjects.

### Bedeutung
Ein semantisch plausibler Text ist noch kein guter Modellkandidat. Der Human Reviewer muss sofort erkennen können, welchen fachlichen Modellinhalt der Agent aus der Source ableitet.

### Konsequenz
Die Verarbeitung muss wieder stärker zwischen folgenden Ebenen unterscheiden:

1. Source Evidence finden,
2. Engineering Meaning interpretieren / klassifizieren,
3. erst später daraus Architecture / Model Candidates ableiten.

---

## SEM-003 — Persona-driven Subject Multiplication

**Status:** `CORRECTED ARCHITECTURALLY / LIVE VALIDATED`

### Beobachtung
Personas erzeugten weitgehend unabhängige Proposal-Populationen. Die Identität eines Engineering Subjects entstand damit zu spät und zu stark aus Agent-generiertem Namen, Typ oder Relationship-Wording.

### Bedeutung
Wenn drei Personas denselben source-grounded Sachverhalt unterschiedlich formulieren, dürfen daraus nicht automatisch drei unabhängige Engineering Subjects entstehen.

Zielinvariante:

```text
Review Subjects ∝ distinct source-grounded engineering information

nicht:

Review Subjects ∝ source subjects × personas × runs
```

### Konsequenz
Die gemeinsame Evidence Identity muss **vor** der Persona-Verzweigung existieren. Personas sollen dieselbe Evidence interpretieren und ihre Unterschiede als Consensus/Variance sichtbar machen.

---

## SEM-004 — Cross-Unit Consolidation war empirisch ineffektiv

**Status:** `SUPERSEDED BY R4c ARCHITECTURE / HISTORICAL FINDING`

### Beobachtung
Im realen Single-Source-Retest `877791 / RUN-000001` entstanden:

```text
D3 local subjects:       109
D4 synthesized subjects: 109
```

Damit erfolgte im D4-Schritt praktisch keine Cross-Unit-Zusammenführung, obwohl sichtbar ähnliche bzw. nahe beieinanderliegende Engineering Statements vorhanden waren.

### Bedeutung
Eine rein nachgelagerte semantische Konsolidierung ist kein ausreichend robuster Ersatz für eine saubere upstream Evidence-/Subject-Identity.

### Konsequenz
D3/D4 dürfen nicht die Verantwortung bekommen, eine zuvor falsch gesetzte Subject Identity nachträglich vollständig zu reparieren.

---

## SEM-005 — Review-Item Count ist kein Optimierungsziel

**Status:** `ACCEPTED INTERPRETATION OF TEST RESULT`

### Beobachtung
Frühere Arbeiten fokussierten stark auf die Reduktion der Anzahl von Review Items. Der Test zeigte, dass die reine Anzahl dafür kein geeignetes Qualitätsmaß ist.

### Bedeutung
Viele Review Items können korrekt sein, wenn die Source tatsächlich viele unabhängige Engineering Claims enthält. Problematisch ist nur künstliche Vervielfachung durch Personas, Runs oder Wording-Varianten.

### Konsequenz
Die Qualitätsreihenfolge lautet:

1. Source Purity
2. Model Relevance
3. Exact Source Grounding
4. korrekte Persona-Behandlung derselben Evidence
5. nutzbarer Consensus / Variance
6. Human Review Usability
7. Review-Item Count nur als Diagnosewert

---

## SEM-006 — Human Review Cards zu textlastig

**Status:** `OPEN / UX + ENGINEERING PRESENTATION`

### Beobachtung
Agent-Proposal-Cards verlangten zu viel Lesen von Rationale-/Detailtext, bevor klar wurde, was überhaupt als Engineering Concept vorgeschlagen wurde.

### Bedeutung
Der Reviewer muss das eigentliche Engineering Proposal vor technischen Metadaten und Langtext erkennen können.

### Soll-Darstellung
Eine Review Card sollte unmittelbar zeigen:

```text
Proposed model kind / classification
Proposed name
Concrete engineering meaning
Source statement
Agent / Persona
Confidence
```

---

## SEM-007 — Source-wide Completeness Request skaliert schlecht

**Status:** `HISTORICAL / PRODUCTIVE R4c PATH SUPERSEDES SOURCE-WIDE COMPLETENESS`

### Beobachtung
Im Run `691616` mit `3 Personas × 2 Runs` wurden 198 erfolgreiche Stage-01..03-LLM-Responses erzeugt. Die source-weite Completeness-Anfrage überschritt dabei eine praktisch sinnvolle Prompt-Größe.

### Bedeutung
Ein globaler Komplettheits-/Vergleichsschritt über große Proposal-Mengen skaliert schlecht und erhöht Kosten, Laufzeit und Fehlerrisiko.

### Konsequenz
Künftige Completeness-/Consensus-Prüfungen sollten auf klar begrenzten, source-grounded Arbeitseinheiten operieren statt auf einer großen globalen Proposal-Menge.

---

## SEM-008 — Legitimate uncertainty funktioniert als Human-Review-Fall

**Status:** `POSITIVE FINDING`

### Beobachtung
Im Run `877791` entstand neben 109 Element-/Relationship-Review-Subjects genau eine Open Question. Diese bezog sich auf eine legitime Klassifikationsunsicherheit für `microscope workstation`.

### Bedeutung
Nicht jede Unsicherheit ist ein Fehler. Die Architektur kann Unsicherheit erhalten und an den Menschen eskalieren, ohne Information zu erfinden oder den Run zwingend abzubrechen.

---

## SEM-009 — Semantically equivalent Relationship hypotheses not consolidated across predicate variants

**Status:** `OPEN / NON-BLOCKING SEMANTIC QUALITY`

### Beobachtung
Semantisch nahe bzw. äquivalente Relationship-Hypothesen können getrennt bleiben, wenn unterschiedliche Prädikate verwendet werden. Beobachtetes Beispiel:

```text
session information depends_on -> later review possible
session information provides   -> later review possible
```

Die Human Review konnte die Redundanz auflösen, die Discovery-/Consolidation-Schicht konsolidiert solche Prädikatsvarianten aber noch nicht zuverlässig.

---

## SEM-010 — Relationship lifecycle not automatically aligned with rejected Subject disposition

**Status:** `OPEN / NON-BLOCKING GOVERNANCE + SEMANTIC LIFECYCLE`

### Beobachtung
Eine zuvor akzeptierte Relationship zu einem später abgelehnten Subject bleibt zunächst accepted und blockiert dadurch die Finalization. Im Live-Run musste eine solche Relationship manuell wieder geöffnet und abgelehnt werden.

### Soll
Wenn ein Endpoint-Subject abgelehnt wird, soll die Relationship nachvollziehbar invalidiert bzw. `not_applicable` werden, ohne die Audit-Historie zu verlieren.

---

## SEM-011 — Incomplete SysML element-type coverage in current semantic/modeling taxonomy

**Status:** `OPEN / ACCEPTED MVP LIMITATION / NON-BLOCKING FOR CURRENT WP-12 GATE`

### Beobachtung
Die aktuelle Engineering-Information-Taxonomie deckt nicht jeden relevanten SysML-v2-Elementtyp direkt ab, z. B. spezifische Ports, Interfaces, Parts, Actions/Functions, States oder Occurrences.

### Einordnung
Engineering Information Classification und spätere SysML-v2-Model-Element-Repräsentation müssen nicht 1:1 identisch sein. Die Lücke darf deshalb nicht durch eine ad-hoc Shadow-Taxonomie im Review geschlossen werden; die spätere Model-Derivation muss profilkontrolliert die Zielrepräsentation bestimmen.

# 3. Empirische Run-Evidenz

## Formaler WP-12-Test — Project 308131

```text
WP12-E2E-DRY-001
controlled synthetic multi-document end-to-end dry run
Current classification: FAILED WITH BLOCKER
Active blocker: BLK-002
```

Der formale Test bleibt erhalten und wird nicht neu gestartet, nur um Findings zu überschreiben. Die frühere Beschreibung `IN PROGRESS / INTERRUPTED FOR BLOCKING DEFECT CORRECTION` bleibt historische Evidenz; ab 24.08.2026 wird der Status nach der vereinbarten Testregel als `FAILED WITH BLOCKER` klassifiziert. Nach Korrektur von BLK-002 wird am betroffenen Gate retestet.

## Project 887027

- früher BLK-003 POST-Retest
- 112 Review Items
- wichtiges Evidenzbeispiel für Singleton-Degradation / fehlende semantische Gruppierung

## Project 159161

- PRE BLK-003.1A/1B Failure Evidence
- dokumentiert den Zustand vor den Robustheitskorrekturen

## Project 691616

- `3 Personas × 2 Runs`
- 198 erfolgreiche Stage-01..03-LLM-Responses
- zeigt Kosten-/Skalierungsproblem source-weiter Completeness-Verarbeitung
- bleibt als historische Stabilitäts-/Repetition-Evidenz erhalten

## Project 877791 / RUN-000001

```text
single source
3 Personas × 1 run
real LLM

93 Element proposals
41 Relationship proposals
134 raw proposals

D3:
70 Element subjects
39 Relationship subjects
109 total

D4:
70 synthesized Elements
39 synthesized Relationships
109 total

Human Review:
70 Element Items
39 Relationship Items
1 Open Question
110 total
```

### Aussage dieses Runs

**Technisch:** D4 → Human Review Routing funktioniert.
**Semantisch:** Source Purity, Model Relevance und Subject Formation sind nicht akzeptiert.

## Project 120412 / RUN-000001 / ATT-000001 — R4c Live E2E

```text
Source: legacy/demo/wp12/01_product_overview.md
Mode: real LLM
Published Processing outputs: 17
Canonical Subjects: 24
Final Review Revision: RVR-000062
Finalization Decision: HRD-000001
Approved Inputs: 17
Accepted semantic Relationships entering Phase H: 21
```

### Gate-Ergebnisse

```text
Processing -> Human Review                         PASS WITH FINDINGS
Subject + Relationship Review                     PASS WITH FINDINGS
Review Finalization                               PASS WITH FINDINGS
Approved Input Promotion                          BLK-004 -> RESOLVED -> RETEST PASS
Approved Engineering Information -> Phase H       BLK-005 -> RESOLVED -> RETEST PASS
Phase-H Readiness / Coverage                      PASS WITH FINDINGS
LLM-assisted Model Proposal generation            FAILED WITH BLOCKER (BLK-006)
```

Die semantische Qualität war gegenüber den früheren BLK-003-Runs deutlich verbessert. Zwei Discovery-False-Positives (`not yet been agreed`, `acceptable`) konnten im Human Review sicher abgelehnt werden. Dies stützt die R4c-Responsibility-Boundary, ohne die noch offenen Precision-/Lifecycle-Findings zu verschweigen.

---

# 4. Formative UX- und Integrations-Findings

> Statusregel: Solange kein expliziter Retest ein Finding geschlossen hat, bleiben die folgenden Beobachtungen `OPEN / NOT YET REVALIDATED`.

## OBS-001 — Project selection lost on toggle

**Priorität:** UX / State Management

Beim Umschalten eines UI-Modus bzw. Controls ging die aktive Project Selection verloren oder wurde nicht stabil gehalten. Das erhöht das Risiko, dass der Benutzer nach einer UI-Aktion in einem anderen oder keinem Projektkontext weiterarbeitet.

---

## OBS-002 — Add-first-source route / discoverability

**Priorität:** UX

Der Weg zum Hinzufügen der ersten Source ist nicht unmittelbar genug erkennbar. Gerade im leeren Projektzustand muss die primäre nächste Aktion eindeutig sein.

---

## OBS-003 — Duplicate Create Project interaction

**Priorität:** UX

Die UI bietet mehr als einen Create-Project-Einstieg bzw. doppelte Interaktionen für denselben Zweck. Das erzeugt unnötige Entscheidungspunkte und wirkt inkonsistent.

---

## OBS-004 — Multi-file visual plus / affordance

**Priorität:** UX

Die visuelle Affordance für das Hinzufügen mehrerer Dateien ist nicht eindeutig genug. Ein Plus-/Add-Control muss klar vermitteln, ob eine weitere Source, mehrere Dateien oder eine andere Aktion ausgelöst wird.

---

## OBS-005 — Drag-and-drop first-click behavior

**Priorität:** UX

Beim initialen Drag-and-drop-/Upload-Flow verhält sich der erste Klick bzw. die erste Interaktion nicht so eindeutig wie erwartet. Das erschwert den Einstieg in die Source-Registrierung.

---

## OBS-006 — Row-action selection scalability

**Priorität:** `MUST`

Zeilenbezogene Actions/Selection skalieren bei vielen Sources oder Items nicht ausreichend. Bei wachsenden Listen darf die Bedienung nicht von einer unübersichtlichen Anzahl einzelner Inline-Actions abhängen.

---

## OBS-007 — Long Processing feedback

**Priorität:** `MUST`

Länger laufendes Processing liefert zu wenig verständliches Fortschrittsfeedback. Der Benutzer kann nicht gut erkennen, welcher Verarbeitungsschritt aktuell läuft und ob das System noch aktiv arbeitet.

### Abgeleitete UX-Regel
Fortschritt soll über geplante Work Units dargestellt werden, nicht über erfundene Zeitprognosen:

```text
PENDING → RUNNING → COMPLETED
                  → SKIPPED
                  → FAILED
```

---

## OBS-008 — Processing cancellation architecture

**Priorität:** `SHOULD`

Für lange Processing Runs fehlt ein sauber definierter Cancel-/Abort-Pfad. Eine zukünftige Abbruchfunktion muss persistierte Zustände, bereits erzeugte Evidence und Run-Historie konsistent behandeln.

---

## OBS-009 — Optional tips / guidance

**Priorität:** UX / low priority

Kontextuelle Hilfen könnten den Workflow verständlicher machen, ohne die Engineering UI mit permanentem Erklärungstext zu überladen.

---

## OBS-010 — Agent scope label clarity

**Priorität:** UX

Die Darstellung des Agent-/Persona-Scope ist nicht eindeutig genug. Der Benutzer sollte erkennen können, welche Agenten auf welche Source bzw. welche Processing Unit angewendet werden.

---

## OBS-011 — Live state inconsistent after source change

**Priorität:** Integration / State Management

Nach Änderungen an der Source kann die sichtbare UI-State-Darstellung von der tatsächlich persistierten Processing-/Project-State abweichen. Das birgt das Risiko einer falschen Interpretation des aktuellen Systemzustands.

---

## OBS-012 — Processing coupled to active Streamlit page run

**Priorität:** Integration / demo-critical

Das laufende Processing ist noch an den aktiven Streamlit-Seitenlauf gekoppelt. Während eines Runs sollte deshalb nicht einfach auf andere Seiten navigiert werden.

### Bedeutung
Background Execution und UI-Lifecycle sind noch nicht vollständig entkoppelt. Ein langlebiger Processing Run sollte langfristig unabhängig davon laufen, welche UI-Seite gerade gerendert wird.

---

## OBS-013 — Review Queue shows misleading zero before workspace materialization

**Priorität:** UX / State Presentation

Vor der eigentlichen Review-Workspace-Materialisierung kann die Review Queue `0` anzeigen, obwohl bereits Processing Evidence existiert, aus der später Review Items entstehen.

### Risiko
Der Benutzer kann `0` fälschlich als „nichts zu reviewen“ interpretieren, obwohl der Review-Schritt lediglich noch nicht materialisiert wurde.

---

## OBS-014 — Reviewer identity confirmation

**Priorität:** Governance / UX

Bei Human-Review-Entscheidungen sollte die aktive Reviewer Identity explizit sichtbar bzw. bestätigbar sein. Die Entscheidung erhält Engineering Authority und muss deshalb nachvollziehbar einer Person/Identity zugeordnet werden.

---

## OBS-015 — No explicit reprocessing of an already processed Source

**Priorität:** Integration / Workflow

Die Guided UI bietet derzeit keinen klaren Reprocessing-Flow für eine bereits processierte Source.

### Konsequenz
Für einen kontrollierten Live-Rerun wurde ein frisches Projekt bzw. eine neue Source verwendet. Langfristig braucht Reprocessing eine explizite, nachvollziehbare Run-/Supersession-Semantik.

---

## OBS-016 — Persona configuration presentation

**Priorität:** UX

Die konfigurierte Persona-/Agent-Kombination wird in der UI nicht ausreichend verständlich dargestellt. Der Benutzer sollte erkennen können, welche Perspektiven eingesetzt werden und wie viele Runs/Repetitions geplant sind.

---

## OBS-017 — Long-running Processing feedback / performance

**Priorität:** UX + Performance

Neben dem reinen Fortschrittsfeedback ist die Dauer des Agenten-Workflows selbst ein praktischer Finding. Mehrstufige Agentenverarbeitung kann mehrere Minuten benötigen und muss deshalb sowohl performant als auch transparent orchestriert werden.

---

## OBS-018 — Global Project Selector session-state conflict

**Priorität:** Integration / State Management

Der globale Project Selector kann mit lokalem Streamlit Session State konkurrieren. Dadurch besteht das Risiko, dass verschiedene Views unterschiedliche Project-Kontexte darstellen oder eine Auswahl unbeabsichtigt überschrieben wird.

---

## OBS-019 — Subject Discovery over-generation / insufficient abstention

**Status:** `OPEN / NON-BLOCKING QUALITY`

Die gemeinsame Subject Discovery erzeugte einzelne Phrasen ohne ausreichende eigenständige Engineering-Bedeutung, u. a. `not yet been agreed` und `acceptable`. Human Review konnte diese False Positives sicher ablehnen. Discovery sollte künftig stärker abstain/omit bevorzugen, wenn eine Phrase kein eigenständiges Engineering Subject trägt.

---

## OBS-020 — Editing a Human Review decision did not change action semantics

**Status:** `CORRECTED / FOCUSED + LIVE VALIDATED`

Vor der Decision-Lifecycle-Korrektur konnten geänderte Classification-/Rationale-Werte beim anschließenden Accept nicht zuverlässig als autoritative Änderung erkennbar werden. Der korrigierte Flow unterscheidet nun explizit Accept-as-generated und Accept-with-modification; Live-Reopen-/Korrektur wurde mit `SUBJ-000007` und `SUBJ-000015` validiert.

---

## OBS-021 — Plain Accept persisted as accepted_with_modification

**Status:** `CORRECTED FOR NEW DECISIONS / FOCUSED + LIVE VALIDATED`

Unverändertes Accept wird jetzt als `accepted_as_generated`, echte Bearbeitung als `accepted_with_modification` persistiert. Historische Entscheidungen aus dem bereits laufenden Review bleiben unverändert erhalten und werden nicht rückwirkend umgeschrieben.

---

## OBS-022 — Review Queue crash when Decisions Required reaches zero

**Status:** `CORRECTED / RETESTED`

Beim letzten Subject konnte ein ungültiger Streamlit-Button-Typ (`type=None`) die Review Queue zum Absturz bringen. Die UI wurde korrigiert; Finalization des Live-Runs war anschließend erfolgreich. Es trat kein Datenverlust auf.

---

## OBS-023 — Relationship Review too hidden / blocker navigation unclear

**Status:** `OPEN / UX`

Relationship Decisions sind in einzelnen Subject-Bereichen zu versteckt. Bei Finalization-Blockern ist nicht unmittelbar sichtbar, welche konkrete Relationship noch eine Entscheidung benötigt bzw. welcher Blocker angesprungen werden muss.

---

## OBS-024 — Relationship review ID-centric / not human-readable enough

**Status:** `OPEN / UX`

Relationship-Hypothesen wurden primär ID-zentriert dargestellt, z. B. `SUBJ-000007 uses -> SUBJ-000005`. Primäre Darstellung sollte fachliche Labels verwenden und IDs sekundär zeigen. Incoming/read-only und outgoing/decidable Beziehungen sollten klarer getrennt werden.

---

## OBS-025 — Accepted Subject decisions could not be reopened/corrected

**Status:** `CORRECTED / LIVE VALIDATED`

Der Decision-Lifecycle-Slice führt `Reopen Subject decision` ein. Live-Korrekturen wurden erfolgreich durchgeführt und anschließend erneut persistiert.

---

## OBS-026 — Decision controls remained active after Relationship decision

**Status:** `CORRECTED / LIVE VALIDATED`

Entschiedene Relationships werden nun read-only dargestellt und besitzen einen expliziten `Reopen relation decision`-Pfad. Dadurch wird eine versehentliche zweite Entscheidung vermieden.

---

## OBS-027 — Finalized Review Report has no explicit export/download capability

**Status:** `OPEN / SHOULD`

Der finalisierte Review Report ist aktuell primär über Browser-/Print-to-PDF verfügbar. Gewünscht ist mindestens ein deterministischer `.md`-Export der exakten finalisierten Revision inklusive IDs/Fingerprints; später optional deterministisches PDF.

---

## OBS-028 — Cross-layer identity transition insufficiently explained

**Status:** `OPEN / UX + TRACEABILITY EXPLANATION`

Im Review arbeitet der Benutzer mit `SUBJ-*`; der finalisierte Report verwendet primär `RIT-*` als Governance Wrapper. Die technische Bindung ist vorhanden, aber die Darstellung sollte deutlicher z. B. `RIT-... · Review of SUBJ-... · <title>` zeigen.

---

## OBS-029 — Post-promotion same-render status stale

**Status:** `OPEN / LOW UX`

Direkt nach erfolgreicher Approved-Input-Promotion zeigte derselbe Streamlit-Render teilweise noch den alten Queue-Status (`Ready to promote`, Approved Inputs `0`), obwohl darunter bereits 17 aktive Approved Inputs sichtbar waren. Nach Reload war der Status korrekt. Persistenz ist nicht betroffen.

---

## OBS-030 — No visible processing state during Model Proposal generation

**Status:** `OPEN / SHOULD / DEMO-CRITICAL UX`

Nach Klick auf `Generate model proposal` fehlt während des potenziell langen LLM-assisted Calls ein sichtbarer Running State. Es erscheint weder ein Spinner/Status noch die aus anderen Verarbeitungsschritten bekannte Informationsbox. Der Screen wirkt während der Anfrage unverändert.

### Risiko
Der Benutzer kann annehmen, dass der Klick nicht angenommen wurde, erneut auslösen oder den Workflow unnötig unterbrechen.

### Soll
Unmittelbar nach Triggern:

```text
Generating model proposal...
LLM-assisted modeling personas are processing approved engineering information.
```

Zusätzlich soll Duplicate Triggering während des aktiven Calls verhindert werden.

# 5. Positive / bestätigte Findings

## PASS-001 — Project Setup und Source Registration grundsätzlich funktionsfähig

Die formale Projektanlage sowie die separate Registrierung mehrerer Sources funktionierten grundsätzlich. Provenance wurde dabei erhalten; die weitere Multi-Source-Verarbeitung ist jedoch wegen BLK-002 blockiert.

## PASS-002 — D4 → Human Review Routing technisch funktionsfähig

Der reale Run `877791` erreichte erfolgreich den Review Workspace. Damit ist die technische Integration vom Processing bis zur Human-Review-Materialisierung grundsätzlich vorhanden.

## PASS-003 — Human-in-the-Loop Authority Boundary bleibt erhalten

Agent Agreement bzw. Consensus erzeugt keine automatische Engineering Approval. Human Review bleibt die Authority Boundary vor Approved Engineering Information.

## PASS-004 — Semantische Unsicherheit kann reviewbar bleiben

Nicht eindeutig lösbare Klassifikationen oder Relationship-Endpunkte können als Open Question erhalten werden, statt automatisch erfunden oder als harte Processing Failure behandelt zu werden.

## PASS-005 — Grundaufgabe ist für ein LLM prinzipiell lösbar

Ein externer qualitativer Benchmark mit `01_product_overview.md` zeigte, dass ein allgemeines LLM mit einer einfachen, source-bounded Aufgabenstellung sinnvoll source-grounded Engineering Information identifizieren kann. Das unterstützt die Hypothese, dass das Kernproblem primär in Pipeline-/Responsibility-Boundaries liegt und nicht darin, dass die Aufgabe grundsätzlich zu schwierig für ein LLM wäre.


## PASS-006 — R4c source-grounded semantic recovery is live-demonstrable

Der Live-Run `120412` erreichte mit realem LLM einen Subject-centric Human Review mit 24 Canonical Subjects. Frühere Orchestrierungs-/Artifact-Contamination dominierte den Review nicht mehr; fachlich relevante Actors, Functions, Constraints und andere Engineering Information waren erkennbar.

## PASS-007 — Subject/Relationship Review and Finalization are authority-preserving

24 Subject Decisions und 30 ausgehende Relationship Decisions konnten explizit getroffen werden. Finalization blieb fail-closed, bis eine accepted Relationship zu einem rejected Subject korrigiert wurde. Die finale Revision `RVR-000062` wurde anschließend erfolgreich finalisiert.

## PASS-008 — Approved Input Promotion works for R4c semantic classification

17 model-promotierbare accepted Subjects wurden erfolgreich zu aktiven Approved Inputs materialisiert. Open Questions wurden bewusst nicht als Approved Inputs erzwungen.

## PASS-009 — Approved Engineering Information is handed to Phase H

Phase H bindet jetzt sowohl die 17 Approved Subjects als auch 21 accepted semantic Relationships. Semantische Relationships werden nicht vorzeitig in Legacy-Relationship-ApprovedInputs umgedeutet.

## PASS-010 — Phase-H readiness transparently separates Subject and Relationship populations

Der Model-Proposal-Screen zeigt die beiden Authority-Populationen getrennt und erklärt 6 accepted Relationships zu nicht model-promotierbaren Open Questions als `Not projected`.

---

# 6. Noch erforderliche Verifikation

### BLK-006 Root-Cause + Candidate-Generation Retest

Nächster zwingender Testschritt:

```text
diagnose exact generation exception
→ verify no unsafe partial Candidate authority
→ bounded correction
→ focused tests
→ full regression
→ same Project 120412 generation retest
```

Erwartete Testdisposition nach erfolgreichem Retest:

```text
BLK-006 RESOLVED
Model Proposal generation PASS / PASS WITH FINDINGS
```

### BLK-002 Multi-Source Identity Retest

Der formale Stage-A-Test `WP12-E2E-DRY-001` bleibt `FAILED WITH BLOCKER`, bis die Cross-Source Processing Artifact Identity eindeutig korrigiert und im bestehenden formalen Testkontext retestet wurde.

## Candidate Review -> Internal Model -> SysML v2 downstream

Nach BLK-006 muss der Live-E2E noch nachweisen:

```text
reviewable Candidate Set
→ explicit Human Candidate Review
→ accepted Candidate Set
→ Internal Engineering Model
→ SysML v2 generation
→ validation / final review / publication path as applicable
```

## Offene nicht-blockierende Findings

Alle `OPEN`-Findings im Register bleiben bestehen. Sie verhindern einen `PASS` ohne Zusatz, müssen aber nicht zwingend einen `PASS WITH FINDINGS` verhindern, sofern keine Authority-, Integrity-, Safety- oder E2E-Gate-Verletzung vorliegt.

## Full Regression

Letzter bestätigter vollständiger Repository-Stand vor diesem SSOT-Checkpoint:

```text
5889 passed, 1 skipped in 15.28s
git diff --check PASS
```

Vor jedem Blocker-Retest bzw. WP-12-Abschluss erneut:

```text
focused corrected suites
+ relevant workflow regression
+ complete repository regression
+ git diff --check
```


---

# 7. Gesamtfazit des bisherigen WP-12 Tests

WP-12 hat seinen Zweck erfüllt: reale End-to-End-Ausführung hat Defekte sichtbar gemacht, die durch reine Unit-/Regression-Tests nicht aufgefallen waren. Besonders wichtig war die Erkenntnis, dass Evidence Detection, Engineering Subject Identity, Persona Interpretation, Human Authority und spätere Model Derivation klar getrennte Verantwortlichkeiten benötigen.

Die R4c-Recovery hat diese Architektur im Single-Source-Live-Pfad deutlich verbessert und bis zum Phase-H-Readiness-Gate empirisch bestätigt. `BLK-004` und `BLK-005` wurden während desselben Live-E2E entdeckt, korrigiert und erfolgreich retestet.

Aktuell gilt jedoch:

```text
WP-12 overall: FAILED WITH BLOCKER

active blockers:
- BLK-002  Multi-Source Processing Artifact Identity
- BLK-006  LLM-assisted Model Proposal generation
```

Sobald ein Blocker korrigiert ist, wird nicht ein neuer „schöner“ Testlauf erzeugt. Der bestehende Test-/Recovery-Kontext wird am betroffenen Gate retestet und der Blocker im Protokoll auf `RESOLVED -> RETEST PASS` gesetzt.

Wenn alle Blocker aufgelöst sind, aber nicht-blockierende Findings verbleiben, ist der korrekte Abschlussstatus:

```text
PASS WITH FINDINGS
```

Ein uneingeschränktes `PASS` ist erst gerechtfertigt, wenn auch die für den jeweiligen Release-/Demo-Gate als relevant klassifizierten Findings geschlossen oder explizit akzeptiert sind.


---

## Quellen im Repository

- `collaboration/checkpoints/2026-08-19_presentation_wp12_demo_ssot.md`
- `collaboration/checkpoints/2026-08-20_wp12_demo_architecture_recovery_ssot.md`
- `collaboration/checkpoints/2026-08-24_wp12_r4c_live_e2e_ssot.md`
- `collaboration/audits/wp12_findings.md`
- `collaboration/handovers/current_chat_handover.md`
- `collaboration/audits/wp12_multi_document_dry_run_test_protocol.md`
- `collaboration/ux/wp12_formative_self_evaluation_log.md`
- `collaboration/decisions/ADR-025-semantic-proposal-consolidation-and-persona-aware-consensus.md`
- `collaboration/decisions/ADR-026-source-anchored-multi-persona-interpretation-and-cross-unit-synthesis.md`
- `collaboration/decisions/ADR-027-source-grounded-evidence-detection-and-persona-interpretation-architecture.md`

---

## BLK-007 — Model Assembly invoked Model Placement personas for Relationship representation

**Status:** `CORRECTED / LIVE RETEST PASS`

The first live Assembly attempt failed because relationship representation was
delegated to the Model Placement team. This crossed the accepted responsibility
boundary.

Correction:

```text
Model Assembly is deterministic.
Exact authorized Relationship semantics may map deterministically.
Non-exact accepted semantics remain unresolved for Human Final Model Review.
No LLM/persona relationship projection occurs during Assembly.
```

Live retest Project `120412`:

```text
Assembly Draft created
13 elements
3 relationships
0 relationship variance
3 unresolved/unmapped target Relationship representations
```

**Test disposition:** `BLOCKER RESOLVED -> RETEST PASS`

---

## SEM-012 — Engineering Information type and Target Model representation are insufficiently separated

**Status:** `ACCEPTED FINDING / OPEN`

Engineering classification describes what information means in the Engineering
Information layer. It does not uniquely prescribe the target-model construct.

Observed live example:

```text
Engineering Information: constraint
Target Model representation: stakeholder requirement
```

Both identities and their traceability must be preserved.

---

## SEM-013 — Shared placement ambiguity is conflated with Persona variance

**Status:** `ACCEPTED FINDING / OPEN`

If all Placement personas return the same multi-option set, the result is shared
ambiguity, not inter-Persona disagreement.

Distinguish:

```text
consensus on one placement
shared ambiguity
actual Persona variance
```

---

## SEM-014 — Unresolved target Relationship representation requires explicit Human selection

**Status:** `ACCEPTED FINDING / OPEN`

An unresolved Relationship representation must begin unselected. A substantive UI
default must not become engineering authority.

The Human reviewer must explicitly select a target semantic, intentionally decline
formal materialization, or otherwise resolve the case through the accepted review
workflow.

---

## SEM-015 — MAJOR: Target-Model Formulation is missing as an explicit processing stage

**Status:** `ACCEPTED MAJOR FINDING / OPEN — IMPLEMENT AFTER CURRENT WP-12 E2E`

The current pipeline moves too directly from approved Engineering Meaning and
representation/placement toward deterministic SysML serialization.

Required separation:

```text
Engineering Meaning
≠ Target-Model Representation
≠ Target-Model Formulation
≠ SysML v2 Serialization
```

This applies to Requirements, Functions, Stakeholders, Use Cases, Logical/Physical
Elements, information/data representations, Relationships and future constructs.

Target-Model Formulation may be LLM-assisted, but it must preserve Human-approved
meaning, follow explicit model-/element-specific authoring rules, avoid inventing
engineering content, retain traceability and remain Human-reviewable before becoming
target-model authority.

Model relevance must allow:

```text
materialize formally
retain as context only
intentionally not materialized
unresolved / Human review
```

Relevant extracted/context information is not automatically formal model content.

A purchased copy of INCOSE *Guide to Writing Requirements*, Rev 4
(`INCOSE-TP-2010-006-04`, 1 July 2023, ISBN `978-1-93707-05-4`) is available to
derive a curated Requirements Authoring Profile after WP-12 closeout. The purchased
source itself must not be distributed or committed.

---

## OBS-031 — Human Model Placement Review requires excessive interaction

**Status:** `ACCEPTED FINDING / OPEN`

Desired interaction:

```text
single consensus placement
→ one-click accept; rationale normally unnecessary

shared ambiguity
→ Human selects among shared alternatives

actual Persona variance / override / rejection
→ explicit decision and rationale as appropriate
```

This is UX/governance simplification, not a weakening of Human authority.

### SEM-015-F01 — Dependency-aware in-review regeneration

**Status:** DEFERRED / NOT REQUIRED FOR CURRENT PoC

The current SEM-015 implementation deliberately uses two Human review stages.
Human-reviewed target classification and placement are inputs to a focused LLM
model-quality refinement call. The refined wording is then reviewed before
Internal Model successor materialization.

A future implementation may automatically invalidate and regenerate only the
downstream wording/formulation affected by an in-review classification change.
For the current PoC, a changed classification produces a different
classification/request fingerprint and therefore requires a new refinement
run. This favors implementation effectiveness and traceable model quality over
runtime/call efficiency.

This finding shall not block the single-source PoC or current demo completion.
