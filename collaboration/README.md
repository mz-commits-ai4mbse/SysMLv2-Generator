# Collaboration Knowledge Base

## Purpose

This directory is the single source of truth for the collaboration between the project owner and AI assistants.

It does **not** replace the SysML v2 model and it does **not** replace the implementation.

Instead, it captures:

- current project status
- roadmap
- accepted implementation decisions
- working rules
- project handovers
- collaboration context

The objective is to ensure that future chats always continue with the current project state without relying on previous conversation history.

---

# Source Hierarchy

The following priority always applies.

## Level 1 (Authoritative)

CATIA Magic SysML v2 Model

Authoritative for:

- Stakeholders
- User Needs
- Stakeholder Requirements
- Use Cases
- System Architecture
- Model Relationships

---

## Level 2 (Authoritative)

Repository Source Code

Authoritative for:

- implementation
- module structure
- recipes
- agents
- prompts
- configuration
- data structures

---

## Level 3 (Authoritative)

Collaboration Knowledge Base

Authoritative for:

- current roadmap
- implementation status
- accepted implementation decisions
- collaboration rules
- chat handovers

---

## Level 4 (Derived)

Generated reports

Generated markdown

Temporary summaries

These files are never authoritative.

---

# Rules

If contradictions occur:

CATIA Model

overrides

Repository Documentation

Repository Code

overrides

Collaboration Files

Collaboration Files

override

older chat conversations.

---

# Updating

The collaboration knowledge base is updated using the keyword

SSOT UPDATE

Only explicitly accepted decisions are transferred.

Brainstorming and rejected ideas are never added automatically.