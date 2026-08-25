"""Deterministic local reference evidence for bounded Target-Model Formulation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

from .errors import TargetModelFormulationError


_STAKEHOLDER_PART_USAGE = re.compile(
    r"ownedStakeholderParameter\s*:\s*PartUsage",
    re.IGNORECASE,
)
_TRACE_TERMS = re.compile(
    r"TraceUsage|TraceDefinition|TraceRelationship|traces_to|traceability|\btrace\b|\btraces\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class LocalReferenceAssessment:
    sysml_release_root: str
    sysml_release_fingerprint: str
    stakeholder_part_usage_found: bool
    stakeholder_evidence_locator: str | None
    stakeholder_evidence_note: str
    trace_syntax_match_count: int
    trace_evidence_locator: str
    trace_evidence_note: str
    tn003_allows_stakeholder: bool
    tn004_allows_stakeholder: bool
    target_notation_fingerprint: str
    stakeholder_fixture_validated: bool = False
    stakeholder_fixture_id: str | None = None
    stakeholder_fixture_locator: str | None = None
    stakeholder_fixture_status: str | None = None


def assess_local_references(
    *,
    sysml_release_root: Path | str,
    target_notation_path: Path | str,
) -> LocalReferenceAssessment:
    """Assess only local deterministic evidence; no LLM and no web access."""

    release_root = Path(sysml_release_root)
    notation_path = Path(target_notation_path)
    if not release_root.is_dir():
        raise TargetModelFormulationError(
            "Local SysML v2 release repository is unavailable."
        )
    if not notation_path.is_file():
        raise TargetModelFormulationError(
            "Target Notation artifact is unavailable."
        )

    stakeholder_locator = None
    stakeholder_note = (
        "No explicit StakeholderMembership-to-PartUsage evidence found."
    )
    trace_matches = 0
    file_digests = []

    for path in _text_files(release_root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        relative = path.relative_to(release_root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        file_digests.append((relative, digest))

        if stakeholder_locator is None:
            for index, line in enumerate(text.splitlines(), start=1):
                if _STAKEHOLDER_PART_USAGE.search(line):
                    stakeholder_locator = f"{relative}:{index}"
                    stakeholder_note = (
                        "SysML release metadata defines ownedStakeholderParameter "
                        "as PartUsage. This supports PartUsage capability in stakeholder "
                        "parameter contexts, but does not by itself authorize a standalone "
                        "stakeholder representation."
                    )
                    break

        trace_matches += len(_TRACE_TERMS.findall(text))

    notation_bytes = notation_path.read_bytes()
    notation = json.loads(notation_bytes.decode("utf-8"))
    tn003 = _construct(notation, "TN_003")
    tn004 = _construct(notation, "TN_004")
    (
        stakeholder_fixture_validated,
        stakeholder_fixture_id,
        stakeholder_fixture_locator,
        stakeholder_fixture_status,
    ) = _stakeholder_fixture_evidence(tn003)

    release_fingerprint = _fingerprint(
        {
            "files": [
                {"path": path, "sha256": digest}
                for path, digest in sorted(file_digests)
            ]
        }
    )

    trace_note = (
        "Repository-wide local SysML v2 release scan found no trace/traces/"
        "traces_to/TraceUsage/TraceDefinition/TraceRelationship syntax evidence."
        if trace_matches == 0
        else (
            f"Repository-wide local SysML v2 release scan found "
            f"{trace_matches} trace-related lexical match(es); manual qualification "
            "is required before any formal trace syntax may be proposed."
        )
    )

    return LocalReferenceAssessment(
        sysml_release_root=release_root.as_posix(),
        sysml_release_fingerprint=release_fingerprint,
        stakeholder_part_usage_found=stakeholder_locator is not None,
        stakeholder_evidence_locator=stakeholder_locator,
        stakeholder_evidence_note=stakeholder_note,
        trace_syntax_match_count=trace_matches,
        trace_evidence_locator=(
            f"{release_root.as_posix()}:repository-wide-trace-scan"
        ),
        trace_evidence_note=trace_note,
        tn003_allows_stakeholder=_allows_stakeholder(tn003),
        tn004_allows_stakeholder=_allows_stakeholder(tn004),
        target_notation_fingerprint=hashlib.sha256(
            notation_bytes
        ).hexdigest(),
        stakeholder_fixture_validated=stakeholder_fixture_validated,
        stakeholder_fixture_id=stakeholder_fixture_id,
        stakeholder_fixture_locator=stakeholder_fixture_locator,
        stakeholder_fixture_status=stakeholder_fixture_status,
    )


def _stakeholder_fixture_evidence(
    tn003: dict,
) -> tuple[bool, str | None, str | None, str | None]:
    evidence = tn003.get("syntax_evidence")
    if not isinstance(evidence, dict):
        return False, None, None, None

    fixture_id = evidence.get("fixture_id")
    fixture_path = evidence.get("fixture_path")
    status = evidence.get("validation_status")
    valid_statuses = {
        "passed",
        "passed_with_nonblocking_warning",
    }
    valid = (
        fixture_id == "SFX-C6C3-001"
        and fixture_path
        == "context/sysml/fixtures/c6c3/stakeholder_role_part_definition.sysml"
        and status in valid_statuses
    )
    return (
        valid,
        fixture_id if isinstance(fixture_id, str) else None,
        fixture_path if isinstance(fixture_path, str) else None,
        status if isinstance(status, str) else None,
    )


def _construct(notation: dict, construct_id: str) -> dict:
    stack = [notation]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            if value.get("construct_id") == construct_id:
                return value
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)

    raise TargetModelFormulationError(
        f"Target Notation construct {construct_id} is unavailable."
    )


def _allows_stakeholder(construct: dict) -> bool:
    text = json.dumps(construct, ensure_ascii=False).lower()
    return "stakeholder" in text


def _text_files(root: Path):
    allowed = {
        ".sysml",
        ".kerml",
        ".txt",
        ".md",
        ".json",
        ".xml",
        ".properties",
        ".java",
        ".py",
    }
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in allowed:
            continue
        yield path


def _fingerprint(payload: dict) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
