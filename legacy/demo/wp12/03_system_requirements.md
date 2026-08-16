# Remote Microscope Collaboration — Draft System Requirements

## Document status

Draft legacy system requirements. Identifiers are local to this document and are
not authoritative Turing Generator identifiers.

### RSC-001 — Single active controller

The system shall prevent more than one participant from having active microscope
control authority at the same time.

### RSC-002 — Explicit normal control transfer

During normal connected operation, transfer of microscope control from the operator
to the remote expert shall require an explicit control request and an explicit
operator decision.

### RSC-003 — Control-owner visibility

The system shall indicate the current microscope controller to the participating
users whenever a collaboration session is active.

### RSC-004 — Connection-loss revocation

If the remote expert disconnects while holding microscope control authority, the
system shall revoke that remote control authority and restore a locally safe control
state.

### RSC-005 — Session traceability

The system shall record the start and end of a collaboration session and shall record
control-authority changes that occur during the session.

### RSC-006 — Remote viewing

A connected remote expert shall be able to view the microscope image stream during
an active collaboration session.

## Known gaps

No quantitative latency, bandwidth, availability, retention-time, deployment, or
cybersecurity requirement is defined in this draft.
