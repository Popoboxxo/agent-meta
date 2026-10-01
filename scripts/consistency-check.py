#!/usr/bin/env python3
"""
agent-meta consistency-check.py
================================
Validates agent templates, commands and cross-references for consistency.

Usage:
  # Check all agents + commands in agent-meta:
  py scripts/consistency-check.py

  # Check only git-changed files (fast, for pre-commit / CI):
  py scripts/consistency-check.py --changed

  # Check a specific file:
  py scripts/consistency-check.py --file agents/1-generic/my-agent.md

  # JSON output (for CI pipelines):
  py scripts/consistency-check.py --json

  # Strict mode: warnings also fail (exit 1):
  py scripts/consistency-check.py --strict

Exit codes:
  0 = no errors (warnings allowed unless --strict)
  1 = one or more errors found
  2 = script error (file not found, git unavailable, etc.)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

# ── path setup ────────────────────────────────────────────────────────────────
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

_AGENT_META_ROOT = _SCRIPTS_DIR.parent

from lib.consistency.commands import check_command_frontmatter, check_duplicate_commands
from lib.consistency.context_size import check_context_file_size
from lib.consistency.context_topology import check_context_topology_consistency
from lib.consistency.crossrefs import (
    check_changelog_mentions_new_files,
    check_orchestrator_table,
    check_role_defaults_coverage,
    check_role_defaults_has_generic_source,
    check_schema_refs,
)
from lib.consistency.docs import (
    check_docs_facts_fresh,
    check_docs_index_completeness,
    check_internal_links,
    check_no_manual_counts,
    check_readme_docs_index,
    check_role_generation_parity,
    check_sync_cli_docs,
    check_ui_help_mappings,
    check_wiki_staleness,
)
from lib.consistency.frontmatter import check_agent_frontmatter
from lib.consistency.fanout_contracts import check_fanout_backend_contract
from lib.consistency.handoff_contracts import check_handoff_contracts
from lib.consistency.placeholders import check_placeholders, load_project_vars
from lib.consistency.python_compat import check_fstring_backslash_hazard, check_py39_union_syntax
from lib.consistency.reference_standards import check_reference_standards
from lib.consistency.repo_containment import check_repo_containment_templates
from lib.consistency.report import Finding, Severity, print_json_report, print_report
from lib.consistency.subagent_permissions import check_subagent_permission_templates
from lib.io import load_yaml_file


# --------------------------------------------------------------------------
# Documentation checks V1…V9 — the registration (IC-05, plan task W2-7)
# --------------------------------------------------------------------------
# This table is the **only** place where a documentation check is registered,
# and it is reached exclusively through the facade ``lib.consistency.docs``
# (K20): the name must be in that module's ``__all__``, otherwise the import
# above breaks. Registration is therefore what proves the facade contract, and
# no count derived from the ``--json`` report can stand in for it — the report
# counts checks that *produced findings*, not checks that *exist*.
#
# V8 (``check_spec_plan_path_convention``, W6-2) and V9
# (``check_stale_backups``, W8-4) are not implemented yet; their owners append
# the import and the entry here.
_PROJECT_CONFIG_RELPATH = ".meta-config/project.yaml"


def _readme_docs_index(root: Path, config: dict) -> list[Finding]:
    """V4 adapter — IC-05/K59 pins ``check_readme_docs_index(root)`` at one argument.

    The common gate hands every registered check the project config; V4 is not
    allowed to *accept* it. Dropping it here keeps the registry on one call
    shape instead of teaching the loop about two.
    """
    return check_readme_docs_index(root)


#: The registered documentation checks, in IC-05 order. Each entry takes
#: ``(root, config)``. **The check id is not written here** — it is owned by the
#: family module as ``*_CHECK_ID``, and the comments below only point at that
#: constant: re-spelling the seven ids next to the seven names would be a
#: second, unpinned source that can only drift. The ids are read off the checks
#: at *runtime* by ``tests/test_doc_facts.py::
#: test_the_docs_registry_covers_exactly_what_the_facade_exports``, which derives
#: them by calling every entry and fails when the registry and the facade's
#: exported checks disagree.
DOCS_CHECKS: tuple[Callable[[Path, dict], list[Finding]], ...] = (
    check_no_manual_counts,          # V1 — id: V1_CHECK_ID (docs_freshness)
    check_docs_index_completeness,   # V2 — id: V2_CHECK_ID (docs_index)
    check_internal_links,            # V3 — id: V3_CHECK_ID (docs_links)
    _readme_docs_index,              # V4 — id: V4_CHECK_ID (docs_links; the
                                     #        facade does not re-export it)
    check_role_generation_parity,    # V5 — id: V5_CHECK_ID (docs_freshness_v5)
    check_docs_facts_fresh,          # V6 — id: V6_CHECK_ID (docs_freshness)
    check_wiki_staleness,            # V7 — id: V7_CHECK_ID (docs_wiki)
)


def load_project_config(root: Path) -> dict:
    """The project config every V-check reads as its ``config`` argument.

    Loaded through ``lib.io.load_yaml_file`` with ``on_error="default"`` — the
    same fail-soft loader ``placeholders.load_project_vars`` and the V5/V6
    checks use. A missing or malformed ``project.yaml`` therefore yields ``{}``
    rather than an exception, and ``{}`` closes the common gate below, which is
    the same observation as "the key is absent" (IC-22).
    """
    data = load_yaml_file(
        Path(root) / _PROJECT_CONFIG_RELPATH, on_error="default", default=None
    )
    return data if isinstance(data, dict) else {}


def docs_consolidation_enabled(config: dict | None) -> bool:
    """The IC-05 common gate: only ``docs-consolidation.enabled`` being true opens it.

    Fail-off, the ``knowledge.py:127`` precedence IC-22 names: a missing block,
    a non-mapping block and an explicit ``false`` are observationally identical.
    That is what keeps scenarios 50–56 and every consumer project green (AC-38,
    NG-10) and why there is no "does this look like agent-meta?" heuristic gate
    beside it.

    **What the gate is, precisely: a property of the call site, not of the
    checks.** It decides whether ``run_checks()`` enters its registered block at
    all; a check called **directly** reports regardless of the switch — measured
    on this repository, 6 of the 7 registered checks report findings with the
    config that closes the gate (only V5 refuses on its own, because it reads
    the ``se`` activation gate and not this key). So "V1–V9 are a no-op without
    the key" is true **of the runner**, which is where AC-38 and every scenario
    exercise it, and is **not** a claim about the check functions. A future
    caller that bypasses ``run_checks()`` inherits the calls, not the gate —
    which is why the gate is one ``if`` at the single place all seven calls go
    through, and why moving it into the seven functions would be seven copies
    of one decision.

    The value is compared with ``is True`` rather than tested for truth, so a
    schema-invalid value (``"false"``, ``1``) closes the gate instead of opening
    it. ``config/project-config.schema.json`` types the key as a boolean, so on
    every valid input the two readings are identical; they differ only where the
    answer is undefined, and there the direction that keeps the checks silent is
    the one IC-22's fail-off name asks for.

    """
    block = (config or {}).get("docs-consolidation")
    return isinstance(block, dict) and block.get("enabled") is True

# ── git helpers ───────────────────────────────────────────────────────────────

def get_changed_files(root: Path) -> set[str]:
    """Return set of files changed vs HEAD (staged + unstaged + untracked agents/commands)."""
    changed: set[str] = set()
    try:
        # Tracked changes vs HEAD
        for flag in [["git", "diff", "--name-only", "HEAD"],
                     ["git", "diff", "--name-only", "--cached"]]:
            r = subprocess.run(flag, cwd=str(root), capture_output=True, text=True, timeout=10)  # noqa: PLW1510
            if r.returncode == 0:
                changed.update(l.strip() for l in r.stdout.splitlines() if l.strip())
        # Untracked new files (agents + commands only)
        r = subprocess.run(  # noqa: PLW1510
            ["git", "ls-files", "--others", "--exclude-standard", "agents/", "commands/"],
            cwd=str(root), capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            changed.update(l.strip() for l in r.stdout.splitlines() if l.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return changed


def get_new_files_vs_main(root: Path) -> list[str]:
    """Return files added in this branch vs main/master (for changelog check)."""
    for base in ("main", "master"):
        try:
            r = subprocess.run(  # noqa: PLW1510
                ["git", "diff", "--name-only", "--diff-filter=A", f"{base}...HEAD"],
                cwd=str(root), capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0:
                return [l.strip() for l in r.stdout.splitlines() if l.strip()]
        except (OSError, subprocess.SubprocessError):
            pass
    return []


# ── file collection ───────────────────────────────────────────────────────────

def collect_agent_files(root: Path, only: set[str] | None = None) -> list[Path]:
    """Collect agent .md files from agents/ (1-generic and 2-platform)."""
    files: list[Path] = []
    for layer in ("1-generic", "2-platform"):
        d = root / "agents" / layer
        if not d.exists():
            continue
        for md in sorted(d.glob("*.md")):
            if md.name.startswith("_"):
                continue
            rel = str(md.relative_to(root)).replace("\\", "/")
            if only is None or rel in only:
                files.append(md)
    return files


def collect_command_files(root: Path, only: set[str] | None = None) -> list[Path]:
    """Collect command .md files from commands/."""
    files: list[Path] = []
    for layer in ("1-generic", "2-platform", "0-external"):
        d = root / "commands" / layer
        if not d.exists():
            continue
        for md in sorted(d.glob("*.md")):
            rel = str(md.relative_to(root)).replace("\\", "/")
            if only is None or rel in only:
                files.append(md)
    return files


# ── main check runner ─────────────────────────────────────────────────────────

def run_checks(
    root: Path,
    changed_only: bool = False,
    specific_file: Path | None = None,
) -> list[Finding]:
    findings: list[Finding] = []

    changed_files: set[str] | None = None
    if changed_only or specific_file:
        changed_files = get_changed_files(root) if changed_only else None

    project_vars = load_project_vars(root)

    # Determine which files to check
    if specific_file:
        rel = str(specific_file.relative_to(root)).replace("\\", "/")
        if "commands/" in str(specific_file):
            cmd_files = [specific_file]
            agent_files = []
        else:
            agent_files = [specific_file]
            cmd_files = []
        only_set = {rel}
    else:
        only_set = changed_files if changed_only else None
        agent_files = collect_agent_files(root, only_set)
        cmd_files = collect_command_files(root, only_set)

    # ── per-file: agent frontmatter + placeholders ────────────────────────────
    for path in agent_files:
        content = _read(path)
        if content is None:
            continue
        findings += check_agent_frontmatter(path, content, root, changed_files)
        findings += check_reference_standards(path, content, root, changed_files)
        findings += check_placeholders(path, content, root, project_vars)

    # ── per-file: command checks ──────────────────────────────────────────────
    for path in cmd_files:
        content = _read(path)
        if content is None:
            continue
        findings += check_command_frontmatter(path, content, root)

    # ── global cross-reference checks (skip in single-file mode) ─────────────
    if not specific_file:
        findings += check_role_defaults_coverage(root)
        findings += check_role_defaults_has_generic_source(root)
        findings += check_orchestrator_table(root)
        findings += check_duplicate_commands(root)
        findings += check_schema_refs(root)
        findings += check_handoff_contracts(root)
        findings += check_fanout_backend_contract(root)
        findings += check_subagent_permission_templates(root)
        findings += check_py39_union_syntax(root)
        findings += check_fstring_backslash_hazard(root)
        findings += check_repo_containment_templates(_AGENT_META_ROOT)

        # Phase 5: Documentation & UI Consistency
        findings.extend(check_sync_cli_docs(_AGENT_META_ROOT))
        findings.extend(check_ui_help_mappings(_AGENT_META_ROOT))

        # The IC-05 common gate is the **first** condition of the whole
        # registered V1…V7 block: with the switch absent or false not a single
        # documentation check runs, which is the whole of AC-38. It is read from
        # the *checked* root, not from this checkout, so `--root` and a consumer
        # project each get their own answer.
        project_config = load_project_config(root)
        if docs_consolidation_enabled(project_config):
            for docs_check in DOCS_CHECKS:
                findings.extend(docs_check(root, project_config))

        # Context size guard (issue #540, C2): warn on oversized generated
        # provider context files without acknowledgment (WARNING only).
        findings.extend(check_context_file_size(root))

        # Context topology consistency (SPEC-CONTEXT-FILE-MODES, AC-19):
        # WARNING-only validation of context_file.topology / adapter keys.
        findings.extend(check_context_topology_consistency(root))

        # Changelog check: only meaningful when checking changed/new files
        new_files = get_new_files_vs_main(root)
        if new_files:
            findings += check_changelog_mentions_new_files(root, new_files)

    return findings


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"  ⚠️  Cannot read {path}: {e}", file=sys.stderr)
        return None


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate agent-meta agents, commands and cross-references.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--changed", action="store_true",
        help="Only check files changed vs HEAD (staged, unstaged, untracked in agents/ + commands/).",
    )
    parser.add_argument(
        "--file", metavar="PATH",
        help="Check a single file only.",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output findings as JSON (machine-readable, for CI pipelines).",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Exit 1 on warnings too (not just errors).",
    )
    parser.add_argument(
        "--root", metavar="DIR", default=None,
        help="agent-meta root directory (default: parent of scripts/).",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else _AGENT_META_ROOT

    specific_file: Path | None = None
    if args.file:
        specific_file = Path(args.file).resolve()
        if not specific_file.exists():
            print(f"ERROR: File not found: {specific_file}", file=sys.stderr)
            return 2

    findings = run_checks(root, changed_only=args.changed, specific_file=specific_file)

    if args.json:
        exit_code = print_json_report(findings)
    else:
        exit_code = print_report(findings, root, args.changed)

    if args.strict and any(f.severity == Severity.WARNING for f in findings):
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
