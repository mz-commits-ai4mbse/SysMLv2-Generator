# Turing Generator

The Turing Generator is a Streamlit-based research prototype for traceable,
Human-governed transformation of heterogeneous engineering sources into
validated SysML v2 output.

The implemented end-to-end engineering flow is:

```text
Source
→ Processing Run
→ Human Review
→ Approved Input
→ Model Candidates
→ Candidate Human Review
→ Internal Engineering Model
→ deterministic SysML v2 Generation
→ automated Validation
→ Final Model Human Review
→ explicit Human Release Approval
→ immutable Versioned Output Package
```

## Primary Streamlit application

Run from the repository root:

```bash
streamlit run app/turing_generator_app.py
```

This opens the common application shell with:

- Engineering Workspace
- Project Dashboard
- Processing
- Human Review & Approval
- Model Proposal
- Final Model Review
- Published Output
- global Project selection
- optional Technical details

## Legacy ingestion skeleton

`app/ui_app.py` is retained only as the original early MVP ingestion/review
skeleton. It is not the primary application entry point.

If the legacy two-tab skeleton is intentionally required:

```bash
streamlit run app/ui_app.py
```

## Published output

Human-approved and validation-bound SysML v2 output is written only below:

```text
data/output/<project_id>/<output_package_id>/
```

Generated or reviewed SysML before release remains project-local evidence and is
not final published output.

## Development state

The authoritative implementation status, roadmap, accepted decisions and current
work package are maintained under:

```text
collaboration/
```

Start with:

```text
collaboration/current_state.md
collaboration/roadmap.md
collaboration/handovers/current_chat_handover.md
```
