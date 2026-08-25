#!/usr/bin/env python3
"""Interactive Human Target-Model Formulation review for one authority-backed IEM."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.target_model_formulation import (  # noqa: E402
    TargetModelFormulationError,
    TargetModelFormulationLiveReviewService,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Review reference-grounded Target-Model Formulation proposals "
            "and persist explicit Human authority."
        )
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--iem", required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument(
        "--revise-existing",
        action="store_true",
        help=(
            "Re-review already effective decisions by writing immutable "
            "successor TFDs. Existing TFD/TFA artifacts are never overwritten."
        ),
    )
    return parser


def _yes_no(prompt: str) -> bool:
    while True:
        value = input(prompt).strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no", ""}:
            return False
        print("Enter y or n.")


def _multiline_rationale(prompt: str) -> str:
    """Collect pasted rationale lines before any later y/N prompt."""

    print(prompt)
    print(
        "Enter one or more lines. Finish with an empty line or a line containing only .done."
    )
    lines = []
    while True:
        value = input("> ")
        if value.strip() == ".done":
            break
        if not value.strip():
            if lines:
                break
            continue
        lines.append(value.rstrip())
    return " ".join(item.strip() for item in lines).strip()


def _candidate_text(candidate) -> str:
    parts = [
        f"Candidate: {candidate.candidate_id}",
        f"Outcome:   {candidate.relevance_outcome}",
    ]
    if candidate.target_model_pattern_id:
        parts.append(
            f"Pattern:   {candidate.target_model_pattern_id}"
        )
    if candidate.target_notation_construct_id:
        parts.append(
            f"Notation:  {candidate.target_notation_construct_id}"
        )
    if candidate.formulation_text:
        parts.append(
            f"Form:      {candidate.formulation_text}"
        )
    parts.append(f"Rationale: {candidate.rationale}")
    return "\n".join(parts)


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    reviewer = args.reviewer.strip()
    if not reviewer:
        print("ERROR: --reviewer must not be empty.", file=sys.stderr)
        return 2

    service = TargetModelFormulationLiveReviewService(
        projects_root=ROOT / "data/projects",
        repo_root=ROOT,
    )

    try:
        review = service.prepare_review(
            project_id=args.project,
            internal_engineering_model_id=args.iem,
        )
        state = service.state(review)
    except TargetModelFormulationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print()
    print("Target-Model Formulation Human Review")
    print(f"Project: {review.project_id}")
    print(f"Review:  {review.review_id}")
    print(
        "Source:  "
        f"{review.source_internal_engineering_model_id} / "
        f"{review.final_model_review_decision_id}"
    )
    print()

    effective_by_subject = {
        item.authority_subject_id: item
        for item in state.effective_decisions
    }

    for item in review.items:
        existing = effective_by_subject.get(item.authority_subject_id)
        print("=" * 78)
        print(
            f"{item.subject_kind.upper()} {item.authority_subject_id}"
        )
        print(
            f"Current engineering type: {item.current_engineering_type}"
        )
        print(
            "Current target representation: "
            f"{item.current_target_representation}"
        )

        if existing is not None:
            print(
                f"ALREADY DECIDED: {existing.decision_id} -> "
                f"{existing.selected_candidate_id} "
                f"({existing.selected_relevance_outcome})"
            )
            print(f"Current Human rationale: {existing.rationale}")
            if not args.revise_existing:
                continue

            matching = tuple(
                candidate
                for candidate in item.candidates
                if candidate.candidate_id == existing.selected_candidate_id
            )
            if len(matching) != 1:
                print(
                    "ERROR: effective decision no longer binds exactly one "
                    "candidate in the immutable review.",
                    file=sys.stderr,
                )
                return 1
            candidate = matching[0]
            print()
            print(_candidate_text(candidate))
            print()
            if not _yes_no(
                f"Write successor for {existing.decision_id}, keeping "
                f"{candidate.candidate_id}? [y/N] "
            ):
                print("Existing decision remains effective.")
                continue

            rationale = _multiline_rationale(
                "Replacement Human rationale (required):"
            )
            if not rationale:
                print(
                    "Review stopped: rationale is required. "
                    "No successor decision was written."
                )
                return 0

            try:
                decision = service.record_selection(
                    review=review,
                    authority_subject_id=item.authority_subject_id,
                    selected_candidate_id=candidate.candidate_id,
                    reviewer_identity=reviewer,
                    rationale=rationale,
                )
            except TargetModelFormulationError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                return 1

            print(
                f"RECORDED SUCCESSOR: {decision.decision_id} supersedes "
                f"{existing.decision_id} -> {decision.selected_candidate_id}"
            )
            print()
            continue

        if len(item.candidates) != 1:
            print(
                "ERROR: bounded live recovery expects exactly one candidate "
                "per review item.",
                file=sys.stderr,
            )
            return 1

        candidate = item.candidates[0]
        print()
        print(_candidate_text(candidate))
        print()

        if not _yes_no(
            f"Authorize {candidate.candidate_id} for "
            f"{item.authority_subject_id}? [y/N] "
        ):
            print(
                "Review stopped without authorizing this item. "
                "Persisted prior decisions remain immutable."
            )
            return 0

        rationale = _multiline_rationale(
            "Human rationale (required):"
        )
        if not rationale:
            print(
                "Review stopped: rationale is required. "
                "No decision was written for this item."
            )
            return 0

        try:
            decision = service.record_selection(
                review=review,
                authority_subject_id=item.authority_subject_id,
                selected_candidate_id=candidate.candidate_id,
                reviewer_identity=reviewer,
                rationale=rationale,
            )
        except TargetModelFormulationError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

        print(
            f"RECORDED: {decision.decision_id} -> "
            f"{decision.selected_candidate_id}"
        )
        print()

    try:
        state = service.state(review)
    except TargetModelFormulationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if len(state.effective_decisions) != len(review.items):
        print(
            "Review remains incomplete; no authority set can be finalized."
        )
        return 0

    if state.authority_set is not None and tuple(
        item.content_fingerprint
        for item in state.authority_set.effective_decisions
    ) == tuple(
        item.content_fingerprint
        for item in state.effective_decisions
    ):
        print(
            f"Authority already finalized: "
            f"{state.authority_set.authority_set_id}"
        )
        return 0

    print("=" * 78)
    if not _yes_no(
        "All review items are decided. Finalize immutable "
        "Target-Model Formulation Authority Set? [y/N] "
    ):
        print("Decisions persisted; authority set not finalized.")
        return 0

    try:
        authority = service.finalize(review)
    except TargetModelFormulationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print()
    print(
        f"FINALIZED: {authority.authority_set_id} "
        f"({authority.content_fingerprint})"
    )
    print(
        "No Internal Model successor or SysML generation was performed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
