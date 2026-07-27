# ADR-013

Preliminary Coverage and Potential Model Support Assessment

Status

Accepted

Date

2026-07-27

Context

Phase P introduces project-oriented processing around the completed Phase F
agentic ingestion pipeline.

P1 implemented the versioned Turing RFLP Framework with three levels and twelve
stable mapping targets.

P2 implemented the persistent Project Workspace.

P3 implemented mandatory project assignment, immutable registered sources and
the explicit source roles `engineering_source` and `context_only`.

P4 implemented source-traceable Information Units, Framework Assignment
Candidates and exact Human Review Decisions.

P5 implemented project-local Processing Runs, immutable Event Histories,
Processing Decisions, artifact lifecycle, source disposition, recovery behavior
and source-level and project-level processing aggregation.

The existing artifacts establish traceable candidate evidence. They do not yet
provide a deterministic answer to the following project-level questions:

- which framework nodes have preliminary evidence
- which framework nodes remain uncovered
- which nodes contain ambiguous or conflicting evidence
- which framework levels are partially or completely covered
- which model scopes may be potentially supported by the available evidence
- whether a result is candidate evidence or reviewed candidate evidence
- whether Approved Generation Readiness is currently available

P6 introduces deterministic Preliminary Coverage and potential model-support
assessment.

P6 shall not perform:

- Approved Input Promotion
- Approved Generation Readiness assessment
- model-candidate generation
- internal model generation
- SysML v2 generation
- engineering approval
- automatic CATIA model mutation

Approved Input Promotion and Approved Generation Readiness remain assigned to
Phase G and later responsible phases.

Decision

## Assessment Authority

Preliminary Coverage is a derived, non-authoritative project assessment.

It is calculated from validated project records and may be deleted and
regenerated without loss of authoritative engineering or processing
information.

The assessment shall not replace or modify the authority of:

- the CATIA SysML v2 engineering model
- the Project Manifest
- registered Source Manifests
- Processing Run Manifests and Event Histories
- Information Unit Manifests
- Framework Assignment Candidates
- Human Review Decisions
- accepted architecture decisions

Implementation reality and derived coverage evidence do not automatically
become normative engineering requirements.

## Preliminary Coverage and Approved Readiness

P6 distinguishes strictly between:

```text
Preliminary Coverage
Approved Generation Readiness
```

Preliminary Coverage:

- is available in Phase P
- is based on eligible candidate evidence
- does not require Human Review confirmation
- may distinguish unreviewed and reviewed candidate evidence
- does not authorize Approved Input Promotion
- does not authorize model generation

Approved Generation Readiness:

- is not available in Phase P
- is not calculated by P6
- becomes available from Phase G or its responsible successor phase
- requires approved engineering input
- requires the responsible Human-in-the-Loop authority

P6 shall expose:

```text
approved_readiness_status = not_available
approved_readiness_available_from_phase = G
```

P6 shall not expose `approved_readiness = false`, because `false` could imply
that an available readiness assessment was executed and failed.

## Assessment Inputs

A project assessment may reference only validated project-local records.

Required input categories are:

```text
Framework Template
Preliminary Support Profile
registered Sources
effective Source Processing Dispositions
Processing Run and artifact lifecycle state
Framework Assignment Candidates
Human Review Decisions
```

Every referenced artifact shall remain bound through its stable identifier and
content fingerprint where the source contract provides one.

Cross-project references are invalid.

Unknown sources, framework nodes, candidates, decisions, runs or fingerprints
are invalid.

Blocking persistence or reference issues shall remain visible in the derived
assessment.

## Eligible Sources

A source may contribute Preliminary Coverage only when all of the following are
true:

1. the source belongs to the assessed project
2. the registered source role is `engineering_source`
3. the effective P5 Source Processing Disposition is `in_scope`
4. the source fingerprint matches the referenced processing and semantic
   records
5. the relevant Processing Run and artifact references are valid
6. the referenced evidence is not invalidated

A source shall not contribute Preliminary Coverage when its effective
disposition is:

```text
context_only
out_of_scope
```

A Processing Decision shall not elevate a source registered as `context_only`
into an engineering-coverage source.

Context-only and out-of-scope sources remain registered and auditable.

## Eligible Framework Assignment Evidence

One Framework Assignment Candidate may contribute Preliminary Coverage only
when all of the following are true:

1. `project_id` matches the assessed project
2. `source_id` references an eligible source
3. `information_unit_id` references the exact source-traceable Information Unit
4. the Framework Template identifier and version match the assessment template
5. `assignment_status` is `assigned`
6. every counted proposal references a valid mapping-target node
7. the candidate and its referenced artifacts are not invalidated
8. the latest exact Human Review Decision does not reject the candidate or
   request changes

The candidate confidence, consensus and variance values remain review evidence.

They shall not independently authorize:

- coverage
- publication
- Approved Input Promotion
- generation readiness
- model generation

Confidence, consensus and variance may be displayed as supporting evidence but
shall not be converted into a numeric maturity or readiness score.

## Non-covering Assignment States

Framework Assignment Candidates with these states shall not create coverage:

```text
unassigned
ambiguous
conflict
```

Their interpretation is:

```text
unassigned
→ explicit uncovered evidence

ambiguous
→ no coverage and attention evidence

conflict
→ no coverage and attention evidence
```

A node may have valid covering evidence and separate ambiguous or conflicting
evidence at the same time.

Coverage and attention are therefore separate dimensions.

## Human Review Resolution

Preliminary Coverage does not require Human Review confirmation.

The latest exact Human Review Decision bound to the candidate content and
reference-validation fingerprints determines the review state of that
candidate.

The effects are:

```text
no exact decision
→ unreviewed candidate evidence
→ may create candidate coverage

confirm
→ reviewed candidate evidence
→ may create reviewed candidate coverage

reject
→ excluded from coverage

request_changes
→ excluded from coverage
→ attention required
```

A confirmation in P6 confirms only the exact Framework Assignment Candidate.

It does not mean:

- Approved Input
- Engineering Approval
- Approved Generation Readiness
- model acceptance
- generation authorization

Stale decisions bound to an older candidate or validation fingerprint shall not
control current coverage.

## Framework Node Coverage

P6 assesses every mapping-target node defined by the active Framework Template.

The canonical node coverage states are:

```text
uncovered
candidate_covered
reviewed_candidate_covered
```

`uncovered` means that no eligible covering candidate evidence exists.

`candidate_covered` means that at least one eligible unreviewed Framework
Assignment Candidate maps an Information Unit to the node.

`reviewed_candidate_covered` means that at least one eligible Framework
Assignment Candidate with a latest exact `confirm` decision maps an Information
Unit to the node.

When both reviewed and unreviewed eligible evidence exist,
`reviewed_candidate_covered` is the displayed coverage state while all evidence
counts remain available.

Attention is represented separately:

```text
attention_required = true | false
```

Attention may result from:

- ambiguous assignment evidence
- conflicting assignment evidence
- `request_changes`
- invalid or stale references
- invalidated evidence
- blocking source, processing, assignment or review issues
- multiple incompatible current evidence chains

One node may therefore be covered and require attention simultaneously.

## Framework Node Coverage Record

The derived Framework Node Coverage record contains at least:

```text
framework_node_id
mapping_key
node_name
level_node_id
coverage_state
attention_required
eligible_source_count
information_unit_count
assignment_candidate_count
confirmed_candidate_count
unreviewed_candidate_count
rejected_candidate_count
ambiguous_candidate_count
conflicting_candidate_count
source_ids
information_unit_ids
framework_assignment_candidate_ids
human_review_decision_ids
issue_codes
```

Identifiers shall be unique and deterministically sorted.

Counts shall equal the corresponding unique reference sets.

Rejected or request-changes candidates remain auditable but shall not be counted
as covering candidates.

## Framework Level Coverage

The Framework Template defines three assessment levels:

```text
Stakeholder Level
System Level
Subsystem Level
```

Each level contains four mapping-target nodes.

The canonical level coverage states are:

```text
uncovered
partially_covered
covered
```

`uncovered` means that none of the level's mapping-target nodes has candidate or
reviewed candidate coverage.

`partially_covered` means that at least one but not all mapping-target nodes
have candidate or reviewed candidate coverage.

`covered` means that every mapping-target node in the level has candidate or
reviewed candidate coverage.

The level assessment contains at least:

```text
level_node_id
level_name
coverage_state
covered_node_count
total_node_count
candidate_covered_node_count
reviewed_candidate_covered_node_count
attention_node_count
covered_node_ids
uncovered_node_ids
attention_node_ids
```

P6 shall not calculate a weighted maturity or readiness percentage.

A UI may display exact ratios such as:

```text
3 of 4 framework nodes preliminarily covered
```

## Project Coverage

The project assessment aggregates all Framework Node and Framework Level
Coverage records.

The canonical project coverage states are:

```text
uncovered
partially_covered
covered
attention_required
```

The displayed project state follows this precedence:

1. `attention_required` when a blocking assessment issue exists
2. `covered` when every mapping-target node is covered and no blocking issue
   exists
3. `partially_covered` when at least one but not every node is covered
4. `uncovered` when no node is covered

Non-blocking node attention remains visible even when the overall project state
is `partially_covered` or `covered`.

The project assessment shall preserve exact counts and identifiers rather than
derive a synthetic maturity score.

## Preliminary Support Profile

Potential model support shall be defined by a separate versioned profile.

The initial profile is:

```text
context/frameworks/turing_preliminary_support_profile.json
```

The profile is not engineering-model authority.

It defines deterministic dependency rules for the derived P6 support
assessment.

The profile shall bind at least:

```text
schema_version
profile_id
profile_version
framework_template_id
framework_template_version
support_targets
```

Each support target contains at least:

```text
support_target_id
name
support_target_type
required_framework_node_ids
required_support_target_ids
```

Unknown or duplicate references are invalid.

A profile bound to another Framework Template identifier or version is invalid.

## Conservative Support Chain

The initial potential-support chain is:

```text
Stakeholder Model
→ System Model
→ Subsystem Model
```

### Stakeholder Model

Potential support requires coverage for:

```text
Stakeholders
User Needs
Stakeholder Requirements
Use Cases
```

### System Model

Potential support requires:

```text
potential Stakeholder Model support
System Requirements
System Functional
System Logical
System Physical
```

### Subsystem Model

Potential support requires:

```text
potential System Model support
Subsystem Requirements
Subsystem Functional
Subsystem Logical
Subsystem Physical
```

The dependency chain is conservative and monotonic.

A downstream support target shall not become potentially supported while an
upstream required support target is not potentially supported.

## Potential Support States

The canonical potential-support states are:

```text
not_supported
partially_supported
potentially_supported
attention_required
```

`not_supported` means that none of the directly required framework-node
coverage exists and no required upstream support target is satisfied.

`partially_supported` means that some but not all direct and upstream
requirements are satisfied.

`potentially_supported` means that every direct framework-node requirement and
every required upstream support target is preliminarily satisfied.

`attention_required` means that the support dependencies would otherwise be
satisfied but blocking or conflicting evidence prevents an unqualified support
indication.

`potentially_supported` shall always be interpreted as:

> The versioned Preliminary Support Profile requirements possess eligible
> Preliminary Coverage evidence.

It shall not be interpreted as:

- complete
- correct
- validated
- approved
- generation-ready
- accepted by the engineering authority

## Support Assessment Record

A derived potential-support record contains at least:

```text
support_target_id
name
support_target_type
support_state
required_framework_node_ids
covered_framework_node_ids
missing_framework_node_ids
required_support_target_ids
satisfied_support_target_ids
unsatisfied_support_target_ids
attention_required
issue_codes
```

All identifiers shall be unique and deterministically sorted.

## Issue Handling

P6 issue levels are:

```text
warning
blocking
```

Warnings remain visible but do not automatically suppress valid coverage.

Blocking issues prevent the affected evidence from contributing to coverage.

A project-wide blocking integrity or reference issue changes the displayed
project coverage state to `attention_required`.

Representative blocking issue categories include:

- mixed project references
- unknown source
- unknown Information Unit
- unknown Framework Assignment Candidate
- unknown Framework node
- Framework Template version mismatch
- Preliminary Support Profile mismatch
- source fingerprint mismatch
- invalidated current evidence
- stale exact-review binding
- inconsistent duplicate identities
- invalid support dependency graph
- support dependency cycle

## Determinism and Ordering

All derived records shall use stable ordering.

Unless a stricter domain order is defined:

- framework levels follow Framework Template order
- framework nodes follow parent level and node order
- sources follow `source_id`
- Information Units follow `information_unit_id`
- Framework Assignment Candidates follow their identifiers
- Human Review Decisions follow their identifiers
- support targets follow profile order
- issue codes and identifier sets are sorted deterministically

Equivalent validated inputs shall produce exactly equivalent derived
assessments.

## Assessment Fingerprint

Every project assessment shall contain an
`assessment_input_fingerprint`.

The fingerprint binds the canonical representation of at least:

```text
Framework Template identifier and version
Preliminary Support Profile identifier and version
eligible registered Source identities and fingerprints
effective Source Processing Dispositions
relevant Processing Run and artifact lifecycle identities
Framework Assignment Candidate identities and content fingerprints
latest exact Human Review Decision identities and fingerprints
assessment algorithm identifier and version
```

The fingerprint is evidence of reproducibility.

It is not a mutable project status and does not become an independent authority.

## Persistence

P6 shall not persist a mutable current Coverage state.

Coverage and potential-support assessments are calculated on demand by:

```text
ProjectCoverageService.assess_project(project_id)
```

A caller may serialize or cache a complete derived assessment for UI or report
purposes only when:

- the derived status is explicitly marked non-authoritative
- the assessment input fingerprint is preserved
- the cache may be deleted and regenerated
- stale caches are never treated as current authority

P7 may use the P6 assessment as a read-only dashboard projection.

## Module Structure

The initial P6 module structure is:

```text
modules/project_coverage/
├── __init__.py
├── errors.py
├── types.py
├── profile.py
├── evidence.py
├── coverage.py
├── support.py
└── service.py
```

Responsibilities are:

```text
errors.py
→ P6 validation, reference, integrity and assessment errors

types.py
→ immutable coverage, support, issue and assessment types

profile.py
→ versioned Preliminary Support Profile parsing and validation

evidence.py
→ candidate eligibility and latest exact Human Review resolution

coverage.py
→ node, level and project Preliminary Coverage

support.py
→ potential Model and SubModel support

service.py
→ project-local repository scans and complete assessment assembly
```

The public package API is added only after the internal contracts are stable.

## Implementation Sequence

P6 implementation follows:

```text
P6-A1  Architecture and ADR-013
P6-I1  Errors, types and Preliminary Support Profile
P6-I2  Evidence eligibility and Human Review resolution
P6-I3  Node, level and project Preliminary Coverage
P6-I4  Preliminary Model and SubModel support
P6-I5  Coverage Service and public API
P6-I6  Integration, regression and P6 acceptance
```

Implementation staging and commit may be deferred until the complete P6
implementation is ready, except that this accepted architecture decision shall
be recorded before implementation depends on it.

Consequences

Positive consequences:

- Preliminary Coverage becomes deterministic and reproducible.
- Coverage remains distinct from Approved Generation Readiness.
- Context-only and out-of-scope sources cannot silently create engineering
  evidence.
- Ambiguity and conflict remain visible without being misrepresented as
  coverage.
- Human Review improves evidence classification without becoming model
  generation authority.
- Model and SubModel support indications are based on an explicit versioned
  dependency profile.
- P7 receives a stable read-only data contract for dashboard visualization.
- Existing P1 through P5 authority boundaries remain unchanged.

Trade-offs:

- The conservative support chain may understate potential support.
- A single uncovered required node prevents `potentially_supported`.
- Coverage does not measure semantic completeness inside one framework node.
- The absence of weighted scoring provides less visual simplicity but avoids
  false precision.
- Recalculation requires scanning several validated project repositories.

Risks and mitigations:

- Risk: candidate evidence may be misunderstood as approved readiness.
  Mitigation: explicit state names and `approved_readiness_status =
  not_available`.

- Risk: stale Human Review decisions could affect current coverage.
  Mitigation: only the latest exact content- and validation-fingerprint binding
  is relevant.

- Risk: invalidated artifacts remain referenced by old candidates.
  Mitigation: P5 lifecycle validation excludes invalidated current evidence.

- Risk: support rules become hidden implementation logic.
  Mitigation: versioned Preliminary Support Profile.

- Risk: generated assessment caches become a second authority.
  Mitigation: derived, regenerable, fingerprint-bound and non-authoritative
  cache rules.

Rejected Alternatives

## Count only confirmed Framework Assignment Candidates

Rejected because Preliminary Coverage is explicitly available without Human
Approval.

This alternative would collapse Preliminary Coverage into a later approval
concept.

## Count every Framework Assignment Candidate

Rejected because `unassigned`, `ambiguous`, `conflict`, rejected and
request-changes candidates do not provide valid covering evidence.

## Confidence-weighted coverage score

Rejected because confidence is review evidence and not an authority boundary.

A weighted percentage would imply a precision and engineering maturity model
that has not been defined.

## Persist mutable Coverage status

Rejected because derived coverage could become stale and duplicate the
authority of existing project records.

## Calculate Approved Generation Readiness in P6

Rejected because Approved Generation Readiness is unavailable in Phase P and
belongs to Phase G or its responsible successor phase.

## Infer potential model support directly in the dashboard

Rejected because support dependencies would become hidden UI logic.

The rules belong in a versioned support profile and deterministic P6 service.

## Allow System or Subsystem support without upstream support

Rejected for the initial profile.

The accepted initial profile uses the conservative dependency chain:

```text
Stakeholder Model
→ System Model
→ Subsystem Model
```

Future profiles may define different support targets only through an explicit
versioned architecture and validation change.
