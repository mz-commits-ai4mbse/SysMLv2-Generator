# R4c.5b.3 Subject-Centric Streamlit Review Contract

## Purpose

R4c.5b.3 makes the persisted R4c Subject Review authority the primary Human
Engineering Review presentation whenever the selected ReviewDocument is bound
to a complete Subject Review artifact chain.

It does not rerun Source Discovery, Persona interpretation, consensus or any
other LLM operation.

## Presentation

Each canonical `SUBJ-*` Review card shows:

- exact canonical Subject identity and label;
- exact source-grounded Mention text and `EVD-*` provenance;
- Information Type, Statement Modality and Epistemic Class consensus;
- full value distributions and agreement state;
- Persona interpretation variants;
- uncertainties and missing evidence;
- incoming/outgoing pre-model relationship hypotheses and their support.

Classification attention is shown prominently. Relationship variance is shown
locally with the relevant hypothesis instead of turning most Subject cards into
global warning states.

## Subject Decision

The Reviewer explicitly edits or confirms:

- engineering statement;
- Information Type;
- Statement Modality;
- Epistemic Class.

The UI supports Accept, Defer and Reject.

Because existing G6 evidence-only Review Items have no selectable Agent
proposal authority, an accepted Subject is persisted through the existing
`accepted_with_modification` technical outcome with zero selected proposal
keys. This is a compatibility mapping only; the UI presents the Human action as
Accept.

If accepted content/classification differs from the current draft, a rationale
is mandatory. Reject always requires a rationale.

Every write uses the exact current Review Revision ID and Review Item content
fingerprint and creates the next immutable Review Revision through
`save_item_review`.

## Relationship Boundary

R4c.5b.3 displays relationship hypotheses but does not yet persist independent
per-relationship Accept/Reject/Defer decisions.

That authority is added in the next bounded slice. Until then relationships are
never auto-accepted, normalized or converted to SysML representation.

## Legacy Compatibility

The generic proposal-centric Human Review editor remains unchanged and is used
only when no persisted Subject Review Bundle is available.

The Subject-centric route returns before advanced split/merge, legacy P9
relationship resolution and proposal controls are rendered.
