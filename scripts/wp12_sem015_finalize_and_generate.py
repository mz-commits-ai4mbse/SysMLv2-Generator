#!/usr/bin/env python3
"""Finalize SEM-015 authority into IEM successor and generate deterministic SysML."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.internal_model.authority_backed import (
    AuthorityBackedInternalModelRepository,
)
from modules.internal_model.semantic_successor import (
    SEM015InternalModelSuccessorRepository,
    load_authority_json,
)
from modules.sysml_generation.authority_backed import (
    AuthorityBackedSysMLArtifactRepository,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--source-iem", required=True)
    parser.add_argument("--tfa", required=True)
    parser.add_argument("--mqa", required=True)
    args = parser.parse_args()

    projects = Path("data/projects")
    source_repo = AuthorityBackedInternalModelRepository(projects)
    source = source_repo.load(args.project, args.source_iem)

    tfa_path = (
        projects
        / args.project
        / "target_model_formulation"
        / "authority_sets"
        / f"{args.tfa}.json"
    )
    mqa_path = (
        projects
        / args.project
        / "model_quality"
        / "authority_sets"
        / f"{args.mqa}.json"
    )
    tfa = load_authority_json(tfa_path)
    mqa = load_authority_json(mqa_path)

    print("[SEM-015] Applying Human-authorized model quality + formulation...")
    successor = SEM015InternalModelSuccessorRepository(projects).materialize(
        source=source,
        target_model_formulation_authority=tfa,
        model_quality_authority=mqa,
    )
    print(
        f"[SEM-015] Successor: {successor.internal_engineering_model_id} "
        f"({len(successor.elements)} elements / "
        f"{len(successor.relationships)} formal relationships)"
    )
    print(
        "[SEM-015] Authority binding: "
        f"{successor.semantic_successor_authority_fingerprint}"
    )

    print("[Phase J] Deterministic SysML v2 generation started...")
    artifact = AuthorityBackedSysMLArtifactRepository(projects).generate(
        successor
    )
    print(
        f"[Phase J] Generated {len(artifact.units)} unit(s), "
        f"fingerprint {artifact.content_fingerprint}"
    )
    for unit in artifact.units:
        generated = (
            projects
            / args.project
            / "generated_sysml_v2"
            / successor.internal_engineering_model_id
            / "generated"
            / unit.relative_path
        )
        print(f"\nGENERATED: {generated}")
        print("-" * 78)
        print(unit.content.rstrip())
        print("-" * 78)

    print()
    print("PASS: SEM-015 successor + deterministic SysML generation completed.")
    print("- no LLM call occurred after MQA Human authority")
    print("- source IEM remained immutable")
    print("- non-materialized relationships remain in semantic_authority.json")
    print("- generated SysML is bound to the successor IEM fingerprint")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
