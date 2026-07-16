"""Dual-tree parity check: agents/1-generic/ vs agents/1-generic-modern/.

Every role template in one tree must have a same-named counterpart in the
other tree, so that switching a role to modern prompt mode never falls back
to a missing template. A real bug (e2e-tester.md missing in 1-generic-modern/)
motivated this check.
"""

from pathlib import Path

from .report import Finding, Severity

_LEGACY_DIR = "1-generic"
_MODERN_DIR = "1-generic-modern"


def _role_files(tree_dir: Path) -> set[str]:
    """Return the set of role template filenames in a tree.

    Skips underscore-prefixed files (``_wf-*`` workflow helpers and other
    internal templates), which are not required to exist in both trees.
    """
    if not tree_dir.exists():
        return set()
    return {
        md.name
        for md in tree_dir.glob("*.md")
        if not md.name.startswith("_")
    }


def check_dual_tree_parity(agent_meta_root: Path) -> list[Finding]:
    """Warn when a role template exists in only one of the two generic trees.

    This caused a real bug (e2e-tester.md missing in 1-generic-modern/) — the
    parity check prevents recurrence.
    """
    findings: list[Finding] = []
    legacy_dir = agent_meta_root / "agents" / _LEGACY_DIR
    modern_dir = agent_meta_root / "agents" / _MODERN_DIR

    # If the modern tree does not exist at all, there is nothing to compare
    # against — dual-tree parity is not applicable for this project.
    if not legacy_dir.exists() or not modern_dir.exists():
        return findings

    legacy_files = _role_files(legacy_dir)
    modern_files = _role_files(modern_dir)

    context = ("This caused a real bug (e2e-tester.md missing in "
               "1-generic-modern/) — add parity to prevent recurrence.")

    for name in sorted(legacy_files - modern_files):
        findings.append(Finding(
            Severity.WARNING, "dual-tree.missing-in-modern",
            f"agents/{_LEGACY_DIR}/{name}",
            f"Missing in {_MODERN_DIR}: {name}",
            context,
        ))

    for name in sorted(modern_files - legacy_files):
        findings.append(Finding(
            Severity.WARNING, "dual-tree.missing-in-legacy",
            f"agents/{_MODERN_DIR}/{name}",
            f"Missing in {_LEGACY_DIR}: {name}",
            context,
        ))

    return findings
