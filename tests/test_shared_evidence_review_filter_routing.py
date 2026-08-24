"""Regression tests for corrected shared-Evidence Review filter routing."""

from types import SimpleNamespace

import modules.review_workspace.shared_evidence_review_adapter as adapter
from modules.review_workspace.shared_evidence_review_adapter import (
    SharedEvidenceReviewArtifacts,
    load_shared_evidence_review_consensus_filter_facts,
)


def _artifacts():
    reference = SimpleNamespace(
        artifact_id="ART-000123",
        repository_relative_path=(
            "data/projects/318604/runs/RUN-000001/"
            "shared_evidence_review_input.json"
        ),
        content_fingerprint="a" * 64,
    )
    return SharedEvidenceReviewArtifacts(
        primary_review_report=SimpleNamespace(),
        structured_review_input=reference,
    )


def test_shared_consensus_filter_facts_bind_exact_review_input(monkeypatch):
    payload = {
        "subjects": [
            {
                "source_evidence_id": "EVD-000001",
                "consensus_content_fingerprint": "b" * 64,
                "consensus": {
                    "supporting_personas": [],
                    "dissenting_personas": [
                        "PERSONA_1",
                        "PERSONA_2",
                        "PERSONA_3",
                    ],
                    "omitting_personas": [],
                    "review_required": True,
                },
            }
        ]
    }
    monkeypatch.setattr(
        adapter,
        "_load_review_input",
        lambda reference, *, repository_root: payload,
    )

    facts = load_shared_evidence_review_consensus_filter_facts(
        _artifacts(),
        repository_root=SimpleNamespace(),
    )

    assert len(facts) == 1
    assert facts[0].artifact_id == "ART-000123"
    assert facts[0].evidence_locator == (
        "/subjects/EVD-000001/consensus"
    )
    assert facts[0].evidence_content_fingerprint == "b" * 64
    assert facts[0].agreement_level == "conflict"
    assert facts[0].review_required is True


def test_shared_consensus_filter_state_preserves_disagreement_degree():
    state = adapter._shared_consensus_filter_state

    assert state(
        {
            "supporting_personas": ["A", "B"],
            "dissenting_personas": ["C"],
            "omitting_personas": [],
        }
    ) == "majority_with_disagreement"

    assert state(
        {
            "supporting_personas": ["A"],
            "dissenting_personas": ["B", "C"],
            "omitting_personas": [],
        }
    ) == "minority_interpretation"

    assert state(
        {
            "supporting_personas": ["A", "B", "C"],
            "dissenting_personas": [],
            "omitting_personas": [],
        }
    ) == "unanimous"

    assert state(
        {
            "supporting_personas": ["A", "B"],
            "dissenting_personas": [],
            "omitting_personas": ["C"],
        }
    ) == "incomplete_consensus"

def test_shared_evidence_open_question_does_not_enter_p9_relationship_resolution(
    monkeypatch,
    tmp_path,
):
    """Corrected open questions must not be interpreted as legacy P9 relationships."""

    from types import SimpleNamespace

    import modules.review_workspace.shared_evidence_review_adapter as shared_adapter
    from modules.review_workspace.workflow_service import (
        ReviewApprovalWorkflowService,
    )

    item = SimpleNamespace(
        review_item_id="RIT-000001",
        review_item_kind="open_question",
    )
    view = SimpleNamespace(
        document=SimpleNamespace(
            processing_run_id="RUN-000001",
        ),
        revision=SimpleNamespace(
            review_items=(item,),
        ),
    )
    history = SimpleNamespace()

    service = ReviewApprovalWorkflowService.__new__(
        ReviewApprovalWorkflowService
    )
    service.repository_root = tmp_path
    service.workspace_view = lambda *args: view
    service._review_item_from_view = lambda current_view, item_id: item
    service._processing_repository = SimpleNamespace(
        load_run=lambda *args: history,
    )

    def must_not_enter_p9(*args, **kwargs):
        raise AssertionError(
            "Corrected shared-Evidence open question entered legacy P9."
        )

    service._p9_evidence_selector = must_not_enter_p9
    service._p9_proposal_adapter = must_not_enter_p9

    monkeypatch.setattr(
        shared_adapter,
        "select_shared_evidence_review_artifact",
        lambda current_history: SimpleNamespace(),
    )

    assert service.relationship_resolution_candidates(
        "318604",
        "RVD-000001",
        "RVV-000001",
        "RIT-000001",
    ) == ()
