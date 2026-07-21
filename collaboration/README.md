# Collaboration Knowledge Base

## Purpose

This directory is the single source of truth for project coordination between the project owner and AI assistants.

It does **not** replace the authoritative CATIA SysML v2 engineering model or the repository implementation. It captures:

- current project status
- roadmap and phase scope
- accepted implementation and architecture decisions
- working rules
- project handovers
- collaboration context

Future chats shall use these files instead of previous conversation history.

---

# Source Hierarchy

The following priority always applies.

## Level 1 — Engineering Authority

The CATIA Magic Systems of Systems Architect SysML v2 model is authoritative for engineering knowledge, including stakeholders, needs, requirements, use cases, architecture and model relationships.

If required engineering information is not yet available in CATIA, the temporary shadow model under `model/` may supplement CATIA until Phase N. It shall never override or contradict CATIA.

## Level 2 — Implementation Authority

The GitHub repository source code on the authoritative branch is authoritative for committed implementation, module structure, recipes, agents, prompts, configuration and data structures.

## Level 3 — Coordination Authority

The Collaboration Knowledge Base is authoritative for the current roadmap, implementation status, accepted decisions, working rules and chat handovers.

## Level 4 — Non-authoritative Context

Chat history, generated reports, generated Markdown and temporary summaries are not authoritative.

---

# Conflict Rules

- CATIA overrides the shadow model and all other representations of engineering knowledge.
- The shadow model may only fill information that is not yet available in CATIA.
- Repository source code overrides Collaboration files when determining committed implementation reality.
- Collaboration files define the accepted roadmap, status and coordination rules.
- Previous chat history never overrides the sources above.

---

# Updating

The Collaboration Knowledge Base is updated through an explicit `SSOT UPDATE`.

Only explicitly accepted decisions are transferred. Brainstorming and rejected ideas are never added automatically. An update is complete only after the changed files have been committed, pushed and verified on the authoritative repository branch.
