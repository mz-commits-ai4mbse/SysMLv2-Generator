"""Controlled SYSIDE Modeler CLI adapter for Phase-K external validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Callable

from modules.sysml_generation.types import GeneratedSysMLArtifactSet

from .finding_support import sort_validation_findings
from .fingerprints import calculate_json_fingerprint
from .types import (
    SysMLExternalValidationEvidence,
    SysMLExternalValidationRun,
    SysMLExternalValidatorIdentity,
    SysMLValidationFinding,
    SysMLValidationLocation,
)
from .validation_profile import (
    EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID,
    EXPECTED_EXTERNAL_TOOL_NAME,
    EXPECTED_EXTERNAL_VALIDATOR_ID,
)


SYSIDE_EXECUTABLE_NAME = "syside"
SYSIDE_CHECK_COMMAND_CONFIGURATION = {
    "command": "check",
    "diagnose": "project",
    "colour": "no",
    "crash_reports": "ignore",
    "threads": 1,
    "warnings_as_errors": False,
    "input_scope": "explicit_generated_units",
    "workspace_mode": "isolated_exact_units_utf8",
    "config_file": None,
    "standard_library": "validator_bundled",
}

_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_DIAGNOSTIC_HEADER = re.compile(
    r"^(?P<path>.*):(?P<line>[0-9]+):(?P<column>[0-9]+): "
    r"(?P<severity>error|warning|info)"
    r"(?: \((?P<rule>[^)]+)\))?: (?P<message>.*)$"
)
_SYNTAX_RULE_TOKENS = ("syntax", "parse", "parser", "lex", "grammar")
_BENIGN_NON_DIAGNOSTIC_LINES = frozenset({"All checks passed!"})

Runner = Callable[..., subprocess.CompletedProcess[str]]
Finder = Callable[[str], str | None]


@dataclass(frozen=True, slots=True)
class _ResolvedValidator:
    identity: SysMLExternalValidatorIdentity
    executable: str | None
    resolution_status: str
    resolution_exit_code: int | None = None


@dataclass(frozen=True, slots=True)
class _ParsedDiagnostics:
    findings: tuple[SysMLValidationFinding, ...]
    normalization_failed: bool


class SysideCliValidator:
    """Run non-mutating SYSIDE checks in an isolated temporary workspace.

    The generated units are copied byte-for-byte from the Phase-J artifact into
    a fresh workspace. Only those explicit unit paths are passed to SYSIDE.
    No repository model files or ambient project configuration are included.
    """

    def __init__(
        self,
        *,
        executable_name: str = SYSIDE_EXECUTABLE_NAME,
        timeout_seconds: int = 120,
        executable_finder: Finder = shutil.which,
        command_runner: Runner = subprocess.run,
    ) -> None:
        if not isinstance(timeout_seconds, int) or timeout_seconds < 1:
            raise ValueError("timeout_seconds must be a positive integer.")
        self._executable_name = executable_name
        self._timeout_seconds = timeout_seconds
        self._executable_finder = executable_finder
        self._command_runner = command_runner

    @property
    def configuration_fingerprint(self) -> str:
        """Fingerprint only controlled semantic command configuration."""

        return calculate_json_fingerprint(SYSIDE_CHECK_COMMAND_CONFIGURATION)

    def validate(
        self,
        artifact_set: GeneratedSysMLArtifactSet,
    ) -> SysMLExternalValidationRun:
        """Execute SYSIDE or return explicit unavailable/failed evidence."""

        resolved = self._resolve_validator()
        if resolved.resolution_status != "completed":
            return self._infrastructure_run(
                identity=resolved.identity,
                execution_status=resolved.resolution_status,
                exit_code=resolved.resolution_exit_code,
                code=(
                    "K4_SYSIDE_UNAVAILABLE"
                    if resolved.resolution_status == "unavailable"
                    else "K4_SYSIDE_IDENTITY_FAILED"
                ),
                message=(
                    "Required SYSIDE Modeler CLI is unavailable."
                    if resolved.resolution_status == "unavailable"
                    else "SYSIDE validator identity could not be resolved."
                ),
            )

        assert resolved.executable is not None
        try:
            with tempfile.TemporaryDirectory(prefix="turing-syside-") as raw_root:
                root = Path(raw_root)
                relative_paths = self._materialize_units(artifact_set, root=root)
                command = self._check_command(
                    executable=resolved.executable,
                    relative_paths=relative_paths,
                )
                try:
                    completed = self._run(command, cwd=root)
                except FileNotFoundError:
                    return self._infrastructure_run(
                        identity=resolved.identity,
                        execution_status="unavailable",
                        exit_code=None,
                        code="K4_SYSIDE_UNAVAILABLE",
                        message="Required SYSIDE Modeler CLI became unavailable.",
                    )
                except subprocess.TimeoutExpired:
                    return self._infrastructure_run(
                        identity=resolved.identity,
                        execution_status="failed",
                        exit_code=None,
                        code="K4_SYSIDE_EXECUTION_FAILED",
                        message="SYSIDE validation did not complete successfully.",
                    )
                except OSError:
                    return self._infrastructure_run(
                        identity=resolved.identity,
                        execution_status="failed",
                        exit_code=None,
                        code="K4_SYSIDE_EXECUTION_FAILED",
                        message="SYSIDE validation could not be executed.",
                    )

                parsed = self._normalize_diagnostics(
                    artifact_set=artifact_set,
                    root=root,
                    stdout=completed.stdout or "",
                    stderr=completed.stderr or "",
                )
                findings = parsed.findings
                has_error = any(item.severity == "error" for item in findings)
                unexplained_nonzero = completed.returncode != 0 and not has_error
                if parsed.normalization_failed or unexplained_nonzero:
                    infra = self._infrastructure_finding(
                        code="K4_SYSIDE_OUTPUT_UNTRUSTED",
                        message=(
                            "SYSIDE execution completed, but its output could not "
                            "be normalized completely and deterministically."
                        ),
                    )
                    findings = sort_validation_findings((*findings, infra))
                    status = "failed"
                else:
                    status = "completed"

                diagnostic_count = sum(
                    item.validator_id == EXPECTED_EXTERNAL_VALIDATOR_ID
                    and item.category != "validator_infrastructure"
                    for item in findings
                )
                evidence = SysMLExternalValidationEvidence(
                    validator_identity=resolved.identity,
                    execution_status=status,
                    exit_code=completed.returncode,
                    normalized_diagnostic_count=diagnostic_count,
                )
                return SysMLExternalValidationRun(
                    evidence=evidence,
                    findings=findings,
                )
        except (ValueError, UnicodeError, OSError):
            return self._infrastructure_run(
                identity=resolved.identity,
                execution_status="failed",
                exit_code=None,
                code="K4_SYSIDE_WORKSPACE_FAILED",
                message=(
                    "Generated artifact units could not be materialized in the "
                    "isolated SYSIDE validation workspace."
                ),
            )

    def _resolve_validator(self) -> _ResolvedValidator:
        executable = self._executable_finder(self._executable_name)
        base = self._identity(tool_version=None)
        if executable is None:
            return _ResolvedValidator(
                identity=base,
                executable=None,
                resolution_status="unavailable",
            )

        try:
            completed = self._run((executable, "--version"), cwd=None)
        except FileNotFoundError:
            return _ResolvedValidator(
                identity=base,
                executable=None,
                resolution_status="unavailable",
            )
        except (subprocess.TimeoutExpired, OSError):
            return _ResolvedValidator(
                identity=base,
                executable=executable,
                resolution_status="failed",
            )

        version = self._normalize_version_output(
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )
        if completed.returncode != 0 or version is None:
            return _ResolvedValidator(
                identity=base,
                executable=executable,
                resolution_status="failed",
                resolution_exit_code=completed.returncode,
            )
        return _ResolvedValidator(
            identity=self._identity(tool_version=version),
            executable=executable,
            resolution_status="completed",
        )

    def _identity(self, *, tool_version: str | None) -> SysMLExternalValidatorIdentity:
        return SysMLExternalValidatorIdentity(
            validator_id=EXPECTED_EXTERNAL_VALIDATOR_ID,
            tool_name=EXPECTED_EXTERNAL_TOOL_NAME,
            tool_version=tool_version,
            command_contract_id=EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID,
            configuration_fingerprint=self.configuration_fingerprint,
        )

    def _run(
        self,
        command: tuple[str, ...],
        *,
        cwd: Path | None,
    ) -> subprocess.CompletedProcess[str]:
        return self._command_runner(
            command,
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self._timeout_seconds,
            check=False,
        )

    @staticmethod
    def _materialize_units(
        artifact_set: GeneratedSysMLArtifactSet,
        *,
        root: Path,
    ) -> tuple[str, ...]:
        seen: set[str] = set()
        paths: list[str] = []
        for unit in artifact_set.units:
            relative = unit.relative_path.replace("\\", "/")
            candidate = Path(relative)
            if (
                not relative
                or candidate.is_absolute()
                or ".." in candidate.parts
                or relative in seen
            ):
                raise ValueError("Generated unit path is unsafe or duplicated.")
            seen.add(relative)
            target = root.joinpath(*candidate.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(unit.content.encode("utf-8"))
            paths.append(relative)
        if not paths:
            raise ValueError("External validation requires at least one unit.")
        return tuple(sorted(paths))

    @staticmethod
    def _check_command(
        *,
        executable: str,
        relative_paths: tuple[str, ...],
    ) -> tuple[str, ...]:
        return (
            executable,
            "check",
            "--diagnose",
            "project",
            "--colour",
            "no",
            "--crash-reports",
            "ignore",
            "-j",
            "1",
            *relative_paths,
        )

    def _normalize_diagnostics(
        self,
        *,
        artifact_set: GeneratedSysMLArtifactSet,
        root: Path,
        stdout: str,
        stderr: str,
    ) -> _ParsedDiagnostics:
        findings: list[SysMLValidationFinding] = []
        normalization_failed = False
        seen_header = False
        combined = "\n".join(value for value in (stdout, stderr) if value)
        text = _ANSI.sub("", combined).replace("\r\n", "\n").replace("\r", "\n")

        for raw_line in text.split("\n"):
            line = raw_line.rstrip()
            if not line:
                continue
            if line in _BENIGN_NON_DIAGNOSTIC_LINES:
                continue
            match = _DIAGNOSTIC_HEADER.match(line)
            if match is None:
                if not seen_header:
                    normalization_failed = True
                # Once a diagnostic header has been seen, remaining non-header
                # lines are presentation-only snippets/carets and are discarded.
                continue

            seen_header = True
            unit = self._resolve_unit(
                artifact_set=artifact_set,
                raw_path=match.group("path"),
            )
            if unit is None:
                normalization_failed = True
                continue

            line_number = int(match.group("line"))
            column = int(match.group("column"))
            severity = match.group("severity")
            rule = match.group("rule")
            category = self._diagnostic_category(severity=severity, rule=rule)
            symbol = self._symbol_at_line(
                artifact_set=artifact_set,
                unit_id=unit.unit_id,
                line_number=line_number,
            )
            message = self._sanitize_message(match.group("message"), root=root)
            finding = SysMLValidationFinding(
                code=self._diagnostic_code(severity=severity, rule=rule),
                category=category,
                severity=severity,
                blocking=severity == "error",
                message=message,
                generated_unit_id=unit.unit_id,
                generated_symbol_id=symbol,
                generated_location=SysMLValidationLocation(
                    start_line=line_number,
                    end_line=line_number,
                    start_column=column,
                    end_column=None,
                ),
                validator_id=EXPECTED_EXTERNAL_VALIDATOR_ID,
                validator_rule_id=rule,
            )
            findings.append(finding)

        return _ParsedDiagnostics(
            findings=sort_validation_findings(findings),
            normalization_failed=normalization_failed,
        )

    @staticmethod
    def _resolve_unit(*, artifact_set: GeneratedSysMLArtifactSet, raw_path: str):
        normalized = raw_path.strip().replace("\\", "/")
        matches = []
        for unit in artifact_set.units:
            relative = unit.relative_path.replace("\\", "/").lstrip("./")
            if normalized == relative or normalized.endswith("/" + relative):
                matches.append((len(relative), unit))
        if not matches:
            return None
        matches.sort(key=lambda item: item[0], reverse=True)
        if len(matches) > 1 and matches[0][0] == matches[1][0]:
            return None
        return matches[0][1]

    @staticmethod
    def _symbol_at_line(
        *,
        artifact_set: GeneratedSysMLArtifactSet,
        unit_id: str,
        line_number: int,
    ) -> str | None:
        matches: list[tuple[int, str]] = []
        for entry in artifact_set.traceability_entries:
            if entry.generated_unit_id != unit_id or entry.generated_location is None:
                continue
            location = entry.generated_location
            if location.start_line <= line_number <= location.end_line:
                matches.append(
                    (
                        location.end_line - location.start_line,
                        entry.generated_symbol_id,
                    )
                )
        if not matches:
            return None
        matches.sort(key=lambda item: (item[0], item[1]))
        return matches[0][1]

    @staticmethod
    def _diagnostic_category(*, severity: str, rule: str | None) -> str:
        if severity == "warning":
            return "external_warning"
        lowered = (rule or "").lower()
        if any(token in lowered for token in _SYNTAX_RULE_TOKENS):
            return "external_syntax"
        return "external_semantics"

    @staticmethod
    def _diagnostic_code(*, severity: str, rule: str | None) -> str:
        if rule:
            token = re.sub(r"[^A-Za-z0-9]+", "_", rule).strip("_").upper()
            if token:
                return f"SYSIDE_{token}"
        return f"SYSIDE_{severity.upper()}"

    @staticmethod
    def _sanitize_message(message: str, *, root: Path) -> str:
        result = _ANSI.sub("", message).strip()
        for workspace in {str(root), root.as_posix()}:
            if workspace:
                result = result.replace(workspace, "<generated-workspace>")
        return result

    @staticmethod
    def _normalize_version_output(*, stdout: str, stderr: str) -> str | None:
        combined = "\n".join(value for value in (stdout, stderr) if value)
        text = _ANSI.sub("", combined).replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if len(lines) != 1:
            return None
        return lines[0]

    @staticmethod
    def _infrastructure_finding(*, code: str, message: str) -> SysMLValidationFinding:
        # Infrastructure failures block publication but do not make the generated
        # model invalid. K5 classifies these findings as Phase-K ``incomplete``.
        return SysMLValidationFinding(
            code=code,
            category="validator_infrastructure",
            severity="error",
            blocking=True,
            message=message,
            validator_id=EXPECTED_EXTERNAL_VALIDATOR_ID,
        )

    def _infrastructure_run(
        self,
        *,
        identity: SysMLExternalValidatorIdentity,
        execution_status: str,
        exit_code: int | None,
        code: str,
        message: str,
    ) -> SysMLExternalValidationRun:
        finding = self._infrastructure_finding(code=code, message=message)
        return SysMLExternalValidationRun(
            evidence=SysMLExternalValidationEvidence(
                validator_identity=identity,
                execution_status=execution_status,
                exit_code=exit_code,
                normalized_diagnostic_count=0,
            ),
            findings=(finding,),
        )
