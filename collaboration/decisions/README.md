# Architecture Decision Records (ADR)

## Purpose

This directory contains all accepted architectural decisions of the Turing Generator.

The objective is to preserve the rationale behind major engineering decisions throughout the project lifecycle.

Architecture Decision Records (ADRs) complement the source code and the SysML v2 model by documenting **why** architectural decisions were made.

---

# Scope

ADRs document architectural decisions only.

Typical examples include

- software architecture
- pipeline design
- communication mechanisms
- data persistence
- review workflow
- project organization
- technology selection
- architectural constraints

The following topics shall **not** be documented as ADRs:

- implementation details
- bug fixes
- temporary experiments
- feature requests
- roadmap items
- brainstorming results

---

# ADR Lifecycle

Every ADR follows the same lifecycle.

```
Proposed

↓

Discussed

↓

Accepted

↓

Implemented

↓

Superseded (optional)
```

Only **Accepted** ADRs are considered authoritative.

---

# Naming Convention

```
ADR-001-short-title.md

ADR-002-short-title.md

ADR-003-short-title.md
```

Numbers are never reused.

If an ADR is replaced, its status changes to **Superseded**.

---

# ADR Template

Every ADR shall contain the following sections.

```
# ADR-XXX

Title

Status

Date

Context

Decision

Consequences

Affected Components

Supersedes

Related Roadmap Phase

Related Implementation
```

---

# Status Values

The following status values are permitted.

| Status | Meaning |
|----------|---------|
| Proposed | Initial proposal under discussion |
| Accepted | Official project decision |
| Implemented | Decision fully implemented |
| Superseded | Replaced by a newer ADR |

---

# Relationship to the SysML Model

The SysML v2 model remains the authoritative source for the engineering model.

ADRs shall never redefine

- Stakeholders
- User Needs
- Stakeholder Requirements
- Use Cases
- System Architecture

Instead, ADRs may reference stable model element identifiers where appropriate.

---

# Relationship to the Repository

The repository contains the implementation.

ADRs describe the architectural rationale behind that implementation.

Whenever the implementation changes due to an architectural decision, the corresponding ADR shall be updated through the SSOT UPDATE process.

---

# Relationship to the Collaboration Knowledge Base

The Collaboration Knowledge Base references accepted ADRs.

It shall never duplicate their contents.

---

# Current ADR Roadmap

The following ADRs are expected during the MVP.

| ADR | Planned Topic |
|------|---------------|
| ADR-001 | Memory-Based Stage Handover |
| ADR-002 | Single Responsibility Agent Architecture |
| ADR-003 | Deterministic Review Report |
| ADR-004 | Human-in-the-Loop Review Strategy |
| ADR-005 | Project Workspace Architecture |
| ADR-006 | Approved Input Promotion |
| ADR-007 | Model Candidate Layer |
| ADR-008 | SysML v2 Generation Strategy |

Additional ADRs may be introduced whenever major architectural decisions are made.

---

# Updating ADRs

Architecture decisions become authoritative only after

1. discussion
2. explicit agreement
3. SSOT UPDATE

Chat conversations alone never establish an architectural decision.