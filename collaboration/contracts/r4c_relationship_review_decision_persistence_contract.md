# R4c.5b.4 Relationship Review Decision Persistence

Relationship hypotheses remain pre-model engineering semantics.

One directed tuple `(source SUBJ, relationship kind, target SUBJ)` has exactly
one Human decision owner: the source Subject card. Incoming display on the
target card is read-only.

Decisions are `accepted`, `rejected` or `deferred`. Rejection requires a
rationale.

Every decision is an immutable append-only `SRD-*` record bound to the exact
Project, Review Document, Review Version, Review Revision, source Review Card
fingerprint, relationship tuple, reviewer and timestamp. A changed decision
creates a successor that names its predecessor.

Records live project-locally under
`subject_review_relationship_decisions/<RVD>/<RVV>/`, outside the generic
ReviewWorkspace directory schema. This keeps existing ReviewWorkspace scanning
and serialization unchanged.

This slice does not infer a SysML relationship representation and does not yet
promote relationship decisions into Approved Engineering Information.
