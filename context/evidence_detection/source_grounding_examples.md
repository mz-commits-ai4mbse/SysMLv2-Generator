# Source-Grounded Evidence Detection Examples

Purpose: `context_only` guidance for the specialized Evidence Detection Agent.
These examples teach what kinds of passages may be worth selecting. They are
never positive evidence for a Project.

The runtime prompt assigns deterministic candidate IDs such as `CAND-001` to
exact Source Analysis Unit spans. The detector selects IDs only. It must never
copy, paraphrase or reconstruct source text in its JSON response.

## Relevant capability / participants

Source passage:

> The Remote Microscope Collaboration capability allows a microscope operator to share a live microscope view with a remote expert during a session.

Expected behavior: `relevant`; select the candidate ID that contains this
passage.

## Relevant permission / control

Source passage:

> During the session, the expert may also take temporary control of the microscope when the operator permits it.

Expected behavior: `relevant`; select the corresponding candidate ID.

## Relevant unresolved engineering information

Source passage:

> The exact information to retain and the retention period have not yet been agreed.

Expected behavior: `uncertain`; select the corresponding candidate ID.

## Not relevant administrative prose

Source passage:

> Legacy product note. The statements below are intentionally informal and incomplete.

Expected behavior: `not_relevant`.

## Boundary rule

Reference examples answer: "What kinds of information should I look for?"
Only the current registered Engineering Source answers:
"What information exists in this Project?"

Candidate IDs are temporary addressing aids only. They are not Engineering
Evidence and are never persisted as Engineering authority.
