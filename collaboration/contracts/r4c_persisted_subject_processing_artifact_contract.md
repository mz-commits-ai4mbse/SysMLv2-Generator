# R4c.5b.1 Persisted Subject Processing Artifact Contract

## Purpose

R4c.5b.1 moves the accepted R4c Subject identity and interpretation chain from
temporary live-probe memory into the immutable Processing Attempt artifact
lifecycle.

Human Review must not perform fresh Subject Discovery or Persona
interpretation when a Review Workspace is opened.

## Published Authority Chain

One successful Subject-centric Processing Attempt writes exactly these four
work outputs beneath `phase_f/consensus_reports/`:

1. `canonical_subject_set.json`
2. `subject_interpretations.json`
3. `subject_consensus.json`
4. `subject_review_bundle.json`

The existing `ProjectIngestionPublisher` publishes them through the normal P5
`consensus_reports` artifact path.

Each artifact is bound to:

- Project ID;
- Source ID;
- Source SHA-256;
- Source Projection ID;
- Processing Run ID;
- Processing Attempt ID.

The artifact envelope carries an internal canonical content fingerprint in
addition to the immutable P5 file fingerprint.

## Authority

`canonical_subject_set.json` is the persisted Subject identity authority for
the Attempt.

Persona interpretation, consensus and Human Review projection must bind the
exact ordered `SUBJ-*` population from that artifact.

Later Review opening is read-only over these published outputs. It must not
rerun Discovery or an LLM.

## Compatibility Boundary

The existing shared-Evidence Review artifacts remain temporarily generated as
a compatibility shadow while R4c.5b is integrated.

When a complete Subject Review artifact chain is present on the latest
Attempt, the Subject-centric Review route has precedence. Legacy
shared-Evidence/P9 routing remains fallback only when the new chain is absent.

Removal of the compatibility shadow is a later cleanup step and is not part of
R4c.5b.1.
