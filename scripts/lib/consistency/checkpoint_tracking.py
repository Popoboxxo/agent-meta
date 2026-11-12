"""Checkpoint-tracking checks (#1000): gitignored dirs and dangling references.

Both checks fail soft: without a usable git repo they report nothing.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from ..io import run_git_check_ignore
from ..progress_paths import resolve_progress_paths
from .report import Finding, Severity

_DIR_CODES = ("progress.checkpoint-dir-ignored", "progress.progress-dir-ignored")
_REFERENCE_RE = re.compile(r"[^\s`'\"()<>]*checkpoint[^\s`'\"()<>]*\.json")
_SUGGESTION = ("Cite resume state from a tracked path or commit it in the same PR "
               "(see snippets/orchestrator/checkpointing.md).")


def check_checkpoint_dir_ignored(project_root: Path, config: dict) -> list[Finding]:
    """WARNING per gitignored progress/checkpoint directory."""
    paths = resolve_progress_paths(Path(project_root), config)
    return [
        Finding(Severity.WARNING, f.code, ".meta-config/project.yaml", f.message)
        for f in paths.findings if f.code in _DIR_CODES
    ]


def check_checkpoint_references(
    project_root: Path, plan_files: Iterable[Path],
) -> list[Finding]:
    """ERROR for cited checkpoint files that are missing or gitignored."""
    root = Path(project_root)
    findings: list[Finding] = []
    for plan in plan_files:
        try:
            text = Path(plan).read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            rel_plan = str(Path(plan).relative_to(root))
        except ValueError:
            rel_plan = str(plan)
        for ref in sorted(set(_REFERENCE_RE.findall(text))):
            if "{{" in ref:
                continue
            probe = run_git_check_ignore(ref, str(root))
            if probe is None or probe.returncode not in (0, 1):
                return []  # no usable git: skip the whole check
            if not (root / ref).exists():
                code = "checkpoint.reference-missing"
                msg = f"cited checkpoint '{ref}' does not exist"
            elif probe.returncode == 0:
                code = "checkpoint.reference-ignored"
                msg = f"cited checkpoint '{ref}' is gitignored (dangles in fresh clones)"
            else:
                continue
            findings.append(Finding(Severity.ERROR, code, rel_plan, msg, _SUGGESTION))
    return findings
