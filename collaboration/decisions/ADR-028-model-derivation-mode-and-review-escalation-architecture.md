# ADR-028 — Model Derivation Mode and Review Escalation Architecture

## Status

Accepted

## Date

2026-08-21

## Context

The corrected WP12 architecture establishes source-grounded Evidence before
persona interpretation and introduces Human Engineering Review before target
model derivation.

Phase H already consumes only active Approved Inputs and already supports both
strict deterministic profile projection and LLM-assisted hybrid projection.
The Human Model Candidate Review remains mandatory regardless of the selected
derivation strategy.

The project owner accepted an explicit energy-saving mode and a Human-controlled
escalation path:

- model derivation may run without any LLM call,
- LLM assistance is optional rather than mandatory,
- the system may recommend a strategy based on deterministic projection
  coverage,
- the Human remains free to select the strategy,
- and a rejected deterministic Candidate may be regenerated with LLM assistance
  without repeating the upstream Engineering Review.

A further architectural issue follows from ADR-020 H9-05. The normal hybrid path
does not send deterministically mapped Approved Inputs to the LLM. A Candidate
that was deterministically mapped successfully but later rejected by the Human
Model Review therefore requires an explicit escalation exception: the Approved
Inputs supporting that rejected predecessor Candidate must become eligible for
LLM re-proposal even if deterministic coverage still reports them as `mapped`.

---

## Decision

### R5-01 — Two explicit derivation modes

The supported Human-selectable derivation modes are:

- `eco_deterministic`
- `llm_assisted`

`eco_deterministic` performs no LLM request.

`llm_assisted` remains deterministic-first but may invoke bounded modeling LLM
reasoning for eligible Approved Inputs.

The selected mode does not remove the downstream Model Candidate Review.

---

### R5-02 — Strategy recommendation is advisory

Before Candidate generation, deterministic projection coverage shall be
assessed.

The system may recommend:

- `eco_deterministic` when all projectable Approved Inputs are deterministically
  mapped,
- `llm_assisted` when projection remains ambiguous or unmapped,
- or `llm_assisted` when a predecessor Candidate has been rejected and explicit
  Human escalation is requested.

The recommendation is advisory. It shall not silently select or approve a
derivation strategy on behalf of the Human.

---

### R5-03 — Eco mode remains fail-closed

Eco mode shall not weaken deterministic profile safety.

If deterministic projection cannot establish the target mapping required to
generate a complete Candidate Set, the strict deterministic deriver may fail
closed.

The system shall not force a target mapping merely to keep the no-LLM path
running.

---

### R5-04 — Human Model Review remains mandatory

Candidate Sets generated in either mode shall pass the same Candidate Review
authority boundary.

A deterministic result is not approved merely because it was reproducible.

An LLM-assisted result is not approved merely because multiple modeling
perspectives agree.

---

### R5-05 — Review rejection may escalate to LLM-assisted regeneration

A rejected predecessor Candidate may trigger a successor Candidate Set with:

- `predecessor_candidate_set_id`,
- a non-empty `regeneration_reason`,
- and derivation mode `llm_assisted`.

The predecessor Candidate Set remains immutable and traceable.

---

### R5-06 — Explicit escalation eligibility

For review-driven regeneration, the system shall resolve each currently rejected
predecessor Candidate to its immutable Approved Input references.

Those Approved Input IDs become explicit escalation targets.

Explicit escalation targets may enter LLM-assisted modeling even when the
deterministic resolver still classifies them as `mapped`.

This is the only accepted exception to the normal ADR-020 rule that uniquely
mapped inputs are not sent to the LLM.

The exception requires an explicit Human Model Review rejection bound to the
exact predecessor Candidate snapshot.

---

### R5-07 — No upstream reinterpretation

Review escalation shall not return to Source Evidence Detection, pre-review
persona interpretation, or Human Engineering Review unless the Human explicitly
changes the approved engineering information itself.

The LLM escalation task remains target-model derivation only.

---

### R5-08 — Modeling personas are LLM-mode only

The modeling persona team is not executed in Eco mode.

In `llm_assisted` mode, eligible Approved Inputs may be assessed by the accepted
modeling perspectives:

- rules-focused,
- architecture-focused,
- conservative review.

All modeling personas receive the same Approved Input identities and the same
profile-controlled target options.

---

### R5-09 — Modeling comparison is bounded by profile rules

Modeling-persona comparison shall operate on profile-controlled mapping results,
not free-form semantic subjects.

Agreement may yield one proposed mapping.

Material disagreement shall remain explicit variance / ambiguity.

No comparison step may invent new Approved Engineering Information.

---

## Target lifecycle

```text
Approved Engineering Information
        |
        v
Deterministic Projection Coverage
        |
        +--> Recommendation: Eco / LLM-assisted
        |
        v
Human-selected Derivation Mode
   |                         |
   | Eco                     | LLM-assisted
   v                         v
Strict deterministic      deterministic-first
projection               + modeling personas
   |                         |
   +------------+------------+
                v
        Model Candidate Set
                |
                v
        Human Model Review
          |             |
       accepted       rejected
          |             |
          v             v
     Internal Model   Regenerate successor
                        |
                        +--> LLM-assisted escalation
                             of rejected Candidate's
                             Approved Input support
```

---

## Consequences

### Positive

- zero-LLM model derivation remains available,
- deterministic results still receive Human authorization,
- LLM use becomes targeted and explainable,
- review rejection becomes a first-class feedback mechanism,
- successful upstream Engineering Review is not repeated unnecessarily,
- and predecessor/successor Candidate Sets preserve full traceability.

### Trade-offs

- the LLM-assisted executor must distinguish normal unresolved targets from
  explicit review-escalation targets,
- the recommendation layer is not itself an authority decision,
- and deterministic Eco mode may legitimately fail when the selected profile
  cannot resolve the approved information.

---

## Implementation decomposition

```text
R5a  Derivation mode, recommendation and review-escalation contract
R5b  Modeling-persona execution and bounded comparison for LLM-assisted mode
R5c  Guided Workflow integration and full regression / demo path
```

R5a introduces no new LLM call.
