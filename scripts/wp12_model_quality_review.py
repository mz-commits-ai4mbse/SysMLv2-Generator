#!/usr/bin/env python3
"""SEM-015 Review 2: LLM-refined model wording before IEM successor/generation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.model_quality import (  # noqa: E402
    ModelQualityError,
    ModelQualityLiveService,
)


def _parser():
    parser = argparse.ArgumentParser(
        description=(
            "Run classification-dependent semantic model refinement and "
            "Human Review 2."
        )
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--iem", required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--model", default="gpt-5.5")
    return parser


def _choice(prompt):
    while True:
        value = input(prompt).strip().lower()
        if value in {"a", "o", "r", "q"}:
            return value
        print("Enter a, o, r or q.")


def _multiline(prompt):
    print(prompt)
    print("Finish with an empty line or .done.")
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


def _progress(message):
    print(f"[SEM-015] {message}", flush=True)


def main(argv=None):
    args = _parser().parse_args(argv)
    reviewer = args.reviewer.strip()
    if not reviewer:
        print("ERROR: --reviewer must not be empty.", file=sys.stderr)
        return 2

    service = ModelQualityLiveService(
        projects_root=ROOT / "data/projects",
        repo_root=ROOT,
        provider=args.provider,
        model=args.model,
    )
    try:
        request, bundle = service.prepare(
            project_id=args.project,
            internal_engineering_model_id=args.iem,
            progress=_progress,
        )
        existing = {
            item.internal_model_element_id: item
            for item in service.effective_decisions(bundle)
        }
    except ModelQualityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    by_input = {
        item.internal_model_element_id: item
        for item in request.elements
    }

    print()
    print("SEM-015 Model Quality Review 2")
    print(f"Project: {bundle.project_id}")
    print(f"Source:  {bundle.source_internal_engineering_model_id}")
    print(f"Review:  {bundle.review_id}")
    print(
        "This review approves the LLM-refined model-facing wording. "
        "Target classification/placement is already authoritative."
    )

    for proposal in bundle.proposals:
        source = by_input[proposal.internal_model_element_id]
        print()
        print("=" * 78)
        print(
            f"{source.internal_model_element_id} · "
            f"{source.element_type} · {source.model_area}"
        )
        print(f"Framework: {source.framework_assignment}")
        print()
        print(f"ORIGINAL NAME: {source.original_name}")
        if source.original_description:
            print(f"ORIGINAL TEXT: {source.original_description}")
        print()
        print(f"PROPOSED NAME: {proposal.refined_name}")
        if proposal.refined_description:
            print(f"PROPOSED TEXT: {proposal.refined_description}")
        print(
            "Quality flags: "
            f"meaning_preserved={proposal.meaning_preserved}, "
            f"unsupported_added={proposal.unsupported_information_added}, "
            f"human_attention={proposal.requires_human_attention}"
        )
        if proposal.quality_findings:
            print("Findings:")
            for finding in proposal.quality_findings:
                print(f"  - {finding}")
        print(f"LLM rationale: {proposal.rationale}")

        current = existing.get(source.internal_model_element_id)
        if current is not None:
            print(
                f"ALREADY REVIEWED: {current.decision_id} · "
                f"{current.decision}"
            )
            continue

        choice = _choice(
            "[a]pprove proposal / [o]verride wording / "
            "[r]eject / [q]uit: "
        )
        if choice == "q":
            print("Review stopped. Existing decisions remain persisted.")
            return 0
        if choice == "a":
            rationale = (
                "Human reviewed source meaning, target classification and "
                "refined wording and accepted the proposal."
            )
            decision = "approved"
            approved_name = None
            approved_description = None
        elif choice == "o":
            approved_name = input("Approved model name: ").strip()
            if not approved_name:
                print("Override requires a model name; review stopped.")
                return 0
            print(
                "Approved description. Enter '-' for no description; "
                "otherwise finish multiline input with empty line."
            )
            raw_description = _multiline("Approved description:")
            approved_description = (
                None if raw_description.strip() == "-" else raw_description
            )
            rationale = _multiline(
                "Human rationale for wording override:"
            )
            if not rationale:
                print("Override rationale is required; review stopped.")
                return 0
            decision = "overridden"
        else:
            rationale = _multiline(
                "Reason for rejection / required upstream correction:"
            )
            if not rationale:
                print("Reject rationale is required; review stopped.")
                return 0
            decision = "rejected"
            approved_name = None
            approved_description = None

        try:
            value = service.decide(
                bundle=bundle,
                internal_model_element_id=source.internal_model_element_id,
                decision=decision,
                reviewer_identity=reviewer,
                rationale=rationale,
                approved_name=approved_name,
                approved_description=approved_description,
            )
        except ModelQualityError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"RECORDED: {value.decision_id} · {value.decision}")

        if decision == "rejected":
            print(
                "Review 2 remains intentionally incomplete. Correct the "
                "upstream classification/meaning and rerun refinement."
            )
            return 0

    try:
        effective = service.effective_decisions(bundle)
        if len(effective) != len(bundle.proposals):
            print("Review 2 is incomplete; no quality authority set finalized.")
            return 0
        authority = service.finalize(bundle)
    except ModelQualityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print()
    print(
        f"FINALIZED: {authority.authority_set_id} "
        f"({authority.content_fingerprint})"
    )
    print(
        "Model wording is Human-authorized. No IEM successor or SysML "
        "generation was performed yet."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
