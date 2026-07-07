# Turing Generator MVP Skeleton

This skeleton implements the first executable MVP workflow:

1. Read a task file.
2. Read the selected recipe.
3. Load required context files.
4. Read raw legacy input artifacts.
5. Create a human-readable ingestion report.
6. Create placeholder feedback and traceability artifacts.
7. Stop before approved input promotion.

The implementation intentionally does not generate SysML v2 output yet.

## Expected existing workspace files

The skeleton expects that these files already exist in your workspace:

- `context/global/project_principles.md`
- `context/sources/source_manifest.json`
- `context/sysml/sysml_v2_spec_reference.json`
- `context/sysml/sysml_v2_target_notation.json`
- `context/mapping/sysml_model_derivation_rules.json`
- `agents/systems_engineer.md`
- `agents/completeness_checker.md`
- `recipes/ingestion/create_ingestion_artifact.recipe.md`
- `tasks/task_001_ingest_example_model.json`
- `legacy/raw/example_legacy_model_description.md`

## Run from workspace root

```bash
python scripts/run_task.py tasks/task_001_ingest_example_model.json
```

## Optional Streamlit UI

```bash
streamlit run app/ui_app.py
```

## Output

The first task should create:

- `data/ingestion_reports/task_001_ingestion_report.md`
- `data/feedback/task_001_ingestion_feedback.json`
- `data/traceability/task_001_ingestion_traceability.json`

It will not create approved input, approved model data or SysML v2 output.
