# R4c.5b.2 Subject Review Workspace Routing Contract

## Purpose

R4c.5b.2 routes a complete persisted Subject Review artifact chain into the
existing immutable ReviewDocument / ReviewVersion / ReviewRevision
infrastructure.

No Discovery, Persona interpretation or consensus calculation occurs while the
Review Workspace is opened.

## Route Precedence

For the latest Processing Attempt:

1. complete R4c Subject Review artifact chain;
2. corrected shared-Evidence compatibility route;
3. historical P9/P4 route.

If a Subject Review Bundle is present but its required published artifact chain
is incomplete, Review opening fails closed. It must not silently fall back.

## Review Item Identity

The exact engineering identity remains the persisted canonical
`canonical_subject_id`, for example `SUBJ-000001`.

The legacy ReviewWorkspace `stable_subject_key` field currently has a lowercase
identifier invariant. R4c.5b.2 does not broaden that generic invariant.
Instead it uses a technical ReviewWorkspace alias:

`subject:subj-000001`

The exact canonical ID remains explicit in the persisted Review Bundle,
`original_report_locator`, evidence locators, UI presentation and Human
decision binding.

This alias is not a new engineering identity.

## Initial Review State

Each canonical Subject becomes exactly one initial Review Item.

The item:

- is always initially `open`;
- carries no Agent proposal references;
- binds exact persisted Subject Review evidence and consensus;
- uses the canonical Subject label as title;
- carries only a visible draft statement as editable starting content;
- never counts the draft as Human approval.

Open-question/gap/ambiguity/risk subjects are presented in the
`open_questions` section. All other canonical Subjects are presented as
`elements`.

Relationships remain nested Subject Review hypotheses at this stage and are
not duplicated into independent legacy relationship Review Items.

## Human Review

Human Review remains mandatory for every Subject, including unanimous/high
classification.

R4c.5b.3 provides the dedicated Subject-centric Streamlit editor. The generic
proposal-centric editor remains the Legacy fallback.
