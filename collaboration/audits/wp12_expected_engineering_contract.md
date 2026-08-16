# WP-12 Expected Engineering Contract — Multi-Document Dry Run

## Purpose

This document defines the semantic expectations for the synthetic multi-document
dry run. It is an acceptance oracle at the level of engineering meaning, not an
exact expected SysML structure.

The test shall not require a predetermined number of model elements or exact wording.
A result may differ structurally while still satisfying the contract if the meaning,
authority boundaries and traceability are preserved.

## Minimum engineering meaning expected

### Roles / external participants

The combined interpretation should identify at least the following participant
concepts:

- microscope operator
- remote expert

### Core capability / behavior concepts

The combined interpretation should identify engineering meaning corresponding to:

- starting or establishing a collaboration/streaming session
- remote expert joining/participating in the session
- live microscope image viewing/streaming
- requesting microscope control
- granting/rejecting or otherwise explicitly deciding normal control transfer
- temporary remote microscope adjustment/control
- restoring/revoking remote control after connection loss
- session/control-event traceability

### Constraint / requirement meaning

The combined interpretation should preserve at least:

- only one active controller at a time
- normal operator-to-expert transfer requires an explicit request and decision
- the current controller is visible
- remote authority is revoked on expert connection loss
- session lifecycle and control-authority changes are recorded

### Technical concepts

The combined interpretation should expose, without overcommitting deployment:

- microscope workstation
- remote client
- streaming responsibility
- control responsibility
- session/audit responsibility

The system may derive different modeling abstractions if they remain supported by
the source evidence.

## Cross-document expectations

### MD-01 — Overlap / consolidation

The capability to remotely view the microscope is described across multiple
documents. The system should avoid treating simple restatements as unrelated
engineering concepts solely because the wording differs.

PASS intent:

- overlap is recognizable or consolidatable
- provenance from the contributing sources remains accessible
- no source is silently discarded

### MD-02 — Complementary synthesis

Control behavior is distributed across product, workflow, requirement and technical
architecture notes.

PASS intent:

- control request / decision / authority / command-routing concepts can coexist in
  one coherent model proposal
- the model does not require one document to contain the entire concept
- traceability remains source-specific underneath the combined proposal

### MD-03 — Controlled semantic tension

The normal workflow states that the operator explicitly decides transfer to the
remote expert. The connection-loss path automatically revokes remote authority and
returns to a locally safe state.

PASS intent:

- the system does not flatten these into a false contradiction
- normal transfer and exceptional recovery may be represented distinctly
- if the system flags an ambiguity, it is surfaced for Human review rather than
  silently resolved

### MD-04 — Missing-information discipline

The source set intentionally omits exact values for latency, bandwidth, retention,
deployment topology, protocol, persistence technology and cybersecurity targets.

PASS intent:

- these values are not invented
- missing information may be surfaced explicitly
- lack of those values does not block extraction of supported engineering meaning

## Non-acceptance examples

The dry run shall be considered semantically failed if any of the following occurs
without explicit Human correction and documented disposition:

- more than one simultaneous controller is normalized as acceptable behavior
- operator approval is silently removed from normal operator-to-expert transfer
- automatic disconnect recovery is interpreted as proof that every transfer is
  automatic
- unsupported latency, bandwidth, protocol, retention or deployment facts are
  invented and treated as approved engineering truth
- source provenance is lost during cross-document synthesis
- Candidate or model content is treated as Human-approved without the required gate
