"""Finding dataclass and report formatting."""

import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# ASCII fallbacks for terminals without Unicode support (e.g. Windows cp1252)
_UNICODE = sys.stdout.encoding and sys.stdout.encoding.lower().startswith("utf")
_ICON = {
    "ERROR":   "XX" if not _UNICODE else "ERR",
    "WARNING": "!!" if not _UNICODE else "WRN",
    "INFO":    "--" if not _UNICODE else "INF",
}
_OK   = "[OK]"   if not _UNICODE else "[OK]"
_FILE = ">>>" if not _UNICODE else ">>>"
_PASS = "[PASS]" if not _UNICODE else "[PASS]"
_FAIL = "[FAIL]" if not _UNICODE else "[FAIL]"


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Finding:
    severity: Severity
    check: str       # e.g. "frontmatter.version-bump"
    file: str        # relative path
    message: str
    suggestion: str = ""

    def __str__(self) -> str:
        icon = _ICON.get(self.severity.value, "  ")
        lines = [f"  [{icon}] [{self.check}] {self.message}"]
        if self.suggestion:
            lines.append(f"      -> {self.suggestion}")
        return "\n".join(lines)


def print_report(findings: list[Finding], agent_meta_root: Path, changed_only: bool) -> int:
    """Print human-readable report. Returns exit code (0=ok, 1=errors found)."""
    by_file: dict[str, list[Finding]] = {}
    for f in findings:
        by_file.setdefault(f.file, []).append(f)

    errors = [f for f in findings if f.severity == Severity.ERROR]
    warnings = [f for f in findings if f.severity == Severity.WARNING]

    print()
    print("=" * 64)
    print("  agent-meta consistency-check")
    if changed_only:
        print("  Mode: changed files only (git diff HEAD)")
    print("=" * 64)

    if not findings:
        print()
        print(f"  {_OK}  No issues found.")
        print()
        _print_summary(errors, warnings)
        return 0

    for filepath, file_findings in sorted(by_file.items()):
        print()
        print(f"  {_FILE}  {filepath}")
        for f in sorted(file_findings, key=lambda x: x.severity.value):
            print(str(f))

    print()
    _print_summary(errors, warnings)
    return 1 if errors else 0


def print_json_report(findings: list[Finding]) -> int:
    """Print JSON report to stdout. Returns exit code."""
    errors = [f for f in findings if f.severity == Severity.ERROR]
    data = {
        "findings": [
            {
                "severity": f.severity.value,
                "check": f.check,
                "file": f.file,
                "message": f.message,
                "suggestion": f.suggestion,
            }
            for f in findings
        ],
        "summary": {
            "total": len(findings),
            "errors": len(errors),
            "warnings": len([f for f in findings if f.severity == Severity.WARNING]),
        },
    }
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 1 if errors else 0


def _print_summary(errors: list, warnings: list) -> None:
    total = len(errors) + len(warnings)
    print("-" * 64)
    if not errors and not warnings:
        print(f"  {_PASS}  All checks passed.")
    else:
        parts = []
        if errors:
            parts.append(f"{len(errors)} error(s)")
        if warnings:
            parts.append(f"{len(warnings)} warning(s)")
        status = _FAIL if errors else "WARN"
        print(f"  [{status}]  {', '.join(parts)} found  ({total} total findings)")
    print()
