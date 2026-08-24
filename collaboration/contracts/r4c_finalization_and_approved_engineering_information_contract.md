# R4c.5c Finalization and Approved Engineering Information Closeout

## Finalization Governance

Subject-centric Review finalization is blocked until every outgoing pre-model
relationship hypothesis has an explicit Human decision.

`accepted`, `rejected` and `deferred` are all explicit decisions. Missing
decisions block finalization.

An accepted relationship also requires both endpoint Subjects to have accepted
Review outcomes. A relationship cannot become approved semantic information
when one of its endpoint Subjects was rejected or deferred.

## Finalization Confirmation Freshness

Every relationship decision advances the Review Version by one content-identical
immutable Review Revision before the append-only `SRD-*` record is written.

The generic finalization assessment already fingerprints the exact Review
Revision. Therefore any relationship decision made after a finalization
confirmation invalidates that prior confirmation without adding a second
finalization fingerprint mechanism.

If the subsequent `SRD-*` write fails, the new Review Revision remains as a
safe invalidation boundary and the missing relationship decision blocks
finalization. No stale confirmation can become authoritative.

## Approved Engineering Information

Approved Engineering Information is a derived read authority, not a replacement
for existing Approved Input manifests.

The Subject portion is composed only from active Approved Inputs belonging to
the exact finalized Subject Review Version.

The relationship portion is composed only from latest `accepted` `SRD-*`
records whose source and target canonical Subjects both exist in the approved
Subject set.

Rejected and deferred relationships remain traceable in their append-only
decision history but are not exposed as approved semantic relationships.

No SysML relationship construct, profile mapping or textual notation is created
by this projection. Concrete model derivation remains downstream.
