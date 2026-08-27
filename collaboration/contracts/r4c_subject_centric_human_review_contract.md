# R4c.5a Subject-Centric Human Engineering Review Contract

## Purpose

R4c.5a projects the fixed canonical `SUBJ-*` population, Persona interpretations
and deterministic field-level consensus into one content-first Human Review card
per engineering Subject.

It does not create a second Subject identity, ontology, framework mapping or
SysML representation.

## Review Unit

The Human Review unit is exactly one existing `canonical_subject_id`.

One card contains:

- canonical Subject label;
- all source-grounded `MNT-*` occurrences for that Subject;
- field-level consensus for Information Type, Statement Modality and Epistemic
  Class;
- all Persona interpretation variants;
- all preserved uncertainty and missing-evidence information;
- incoming and outgoing pre-model relationship consensus involving the Subject.

The Reviewer therefore sees the engineering meaning and variance directly,
rather than proposal-centric infrastructure metadata.

## Source Evidence

Source evidence is shown through the exact already established Mention text and
its `EVD-*` references.

R4c.5a performs no new evidence discovery and no source paraphrasing.

## Classification Display

Each structured field exposes:

- `selected_value` when deterministic consensus has one;
- `consensus_level`;
- `confidence`;
- full value distribution;
- supporting, dissenting and unstable Personas;
- explicit review-attention flag.

A low/divergent field with no selected value remains unresolved until Human
Review. The system must not manufacture a value.

## Persona Interpretation Display

Every Persona interpretation is preserved.

Free-text statements are not automatically merged into one synthetic statement.
The Human Reviewer must establish the reviewed engineering statement explicitly.

## Relationship Display

Relationship consensus remains pre-model semantics.

Each card shows every incoming and outgoing relationship key touching its
`SUBJ-*`, with independent Persona support and statement variants.

Relationship consensus does not create an ontology relation or SysML
relationship.


## Review Attention Dimensions

Review attention is exposed in separate dimensions:

- `classification_review_attention_required` covers structured classification
  variance and preserved Subject-level interpretation uncertainty;
- `relationship_review_attention_required` is true when any incoming or
  outgoing relationship hypothesis on the card is not high/unanimous;
- `review_attention_required` is the aggregate OR of both dimensions.

The UI must not reduce these dimensions to one generic warning. A Subject may
have high classification agreement while its relationship semantics still
require explicit Human Review.

## Human Decision

A Subject decision is bound to the exact immutable Review Card fingerprint.

Allowed outcomes are:

- `accepted`;
- `accepted_with_modification`;
- `rejected`.

An accepted Subject requires an explicit Human-reviewed:

- engineering statement;
- Information Type;
- Statement Modality;
- Epistemic Class.

This remains true even when all Personas agree. High confidence assists the
Reviewer; it never substitutes Human Engineering Approval.

Canonical Subject Review is proposal-free. Persona interpretations are
immutable evidence and are never selected as a "winning" Agent proposal.

For each structured field, deterministic consensus governs only the proposed
default:

- `unanimous` and `majority` expose the deterministic `selected_value` as the
  preselected Human Review value;
- `divergent` and `indeterminate` expose no selected value and require an
  explicit Human field selection.

Consensus never creates approval authority. An unchanged consensus-backed
Subject still requires an explicit Human Accept action.

The existing ReviewWorkspace compatibility representation persists an accepted
proposal-free canonical Subject as `accepted_with_modification` with
`selected_proposal_keys=()`. When the Human accepts all displayed canonical
values unchanged, this persistence label does not imply that engineering
content was semantically modified.

A rationale is required when the Human changes accepted engineering content or
classification from the displayed canonical proposal.

`rejected` requires a rationale and must not carry approved engineering fields.

## Relationship Decisions

Visible relationship keys may independently be:

- accepted;
- rejected;
- deferred.

A rejected relationship requires a rationale.

A relationship decision may only reference a relationship actually visible on
the exact Subject Review Card.

## Persistence Boundary

R4c.5a defines immutable projection and decision contracts only.

It does not yet mutate the existing ReviewWorkspace or produce Approved
Engineering Information persistence.

R4c.5b integrates these contracts with ReviewWorkspace persistence and the
Streamlit Human Review UI.
