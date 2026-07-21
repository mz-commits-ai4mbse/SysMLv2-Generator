# Framework Templates

## Purpose

This directory contains versioned, machine-readable framework templates used
as stable mapping structures for project information units.

Framework templates define coordination and mapping structures. They do not
replace or redefine engineering knowledge from the authoritative CATIA SysML
v2 model.

---

## Initial MVP Template

The initial MVP template is:

`context/frameworks/turing_rflp_framework.json`

Template ID:

`TURING_RFLP_FRAMEWORK`

The template implements the accepted Phase P framework:

- Stakeholder Level
  - Stakeholders
  - User Needs
  - Stakeholder Requirements
  - Use Cases
- System Level
  - Requirements
  - Functional
  - Logical
  - Physical
- Subsystem Level
  - Requirements
  - Functional
  - Logical
  - Physical

Additional framework templates are outside the MVP scope.

---

## Stable Identifiers

Every level and framework node has a stable `node_id`.

Human-readable names may be clarified in later template versions, but existing
node IDs shall not be silently renamed or reused for another meaning.

Only nodes with

`"mapping_target": true`

may be referenced by framework assignments.

Framework hierarchy is defined explicitly through `parent_node_id`. File or
folder position alone does not define hierarchy.

---

## Information-Unit Mapping

An engineering information unit may map to zero, one or multiple framework
nodes.

Every assignment shall reference a valid framework `node_id`.

Unknown framework-node IDs shall be rejected.

Only information originating from an `engineering_source` may create
framework-mapped engineering information units.

A `context_only` source may support terminology or interpretation but shall not
create framework mappings or engineering evidence.

---

## Preliminary Coverage

Preliminary coverage indicates that unreviewed engineering information may
support a framework node.

Preliminary coverage:

- may use information from an `engineering_source`
- does not represent human approval
- does not establish generation readiness
- does not authorize model generation
- shall be visibly labelled as preliminary

Preliminary coverage is available during Phase P.

---

## Approved Generation Readiness

Approved generation readiness is separate from preliminary coverage.

Approved readiness:

- requires human-approved engineering information
- excludes `context_only` information
- remains unavailable during Phase P
- becomes possible only after Phase G supplies approved inputs
- shall not be inferred from preliminary coverage

The framework template defines this boundary but does not implement approval or
readiness calculation.

---

## Apollo 11 Reference

The Apollo 11 SysML v2 repository is a non-normative structural reference.

Reviewed observations are documented in:

`context/examples/apollo11_structure_reference.md`

Only explicitly accepted structural patterns may influence the framework
template.

The following are not transferred:

- Apollo engineering content
- the CoSMA five-layer framework
- the Apollo package hierarchy
- Apollo-specific identifiers
- Apollo-specific requirements or traceability relationships

The accepted Stakeholder/System/Subsystem framework remains unchanged.

---

## Source Authority

The following hierarchy applies:

1. CATIA SysML v2 model for engineering knowledge
2. committed repository source for implementation reality
3. Collaboration Knowledge Base for roadmap and coordination
4. chat history and generated artifacts as non-authoritative context

The temporary shadow model under `model/` may supplement unavailable CATIA
information until Phase N but shall never override or contradict CATIA.

---

## P1 Boundary

This directory defines the framework-template contract only.

P1 does not define:

- project persistence
- project manifests
- source registries
- information-unit storage
- coverage calculation
- approval workflows
- model candidates
- model generation

Project persistence belongs to P2 and shall not be implemented before the
Project Workspace architecture has been discussed and accepted in ADR-005.