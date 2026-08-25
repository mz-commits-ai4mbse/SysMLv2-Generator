"""Regression guard for BLK-007 Model Assembly authority boundary."""

from __future__ import annotations

import inspect

from modules.model_candidates.derivation_workflow import (
    ModelDerivationWorkflowService,
)


def test_model_assembly_does_not_invoke_model_placement_personas_for_relationships():
    source = inspect.getsource(
        ModelDerivationWorkflowService.assemble_model_draft
    )

    assert "_semantic_relationship_executor_factory" not in source
    assert "relationship_executor=None" in source
    assert "output_dir=None" in source
