"""Frontmatter validation checks for agent templates."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .report import Finding, Severity
from ..agent_sync import _find_section_bounds
from ..frontmatter import _fm_inner, split_frontmatter

_SEMVER_RE = re.compile(r'^\d+\.\d+\.\d+$')
_VALID_WORKFLOW_TIERS = {"required", "recommended", "optional"}
_VALID_MEMORY_SCOPES = {"project", "local", "user", ""}
_VALID_PERMISSION_MODES = {"default", "acceptEdits", "bypassPermissions", "plan", ""}


def check_agent_frontmatter(path: Path, content: str, agent_meta_root: Path,
                             changed_files: set[str] | None) -> list[Finding]:
    """Run all frontmatter checks on an agent .md file."""
    findings: list[Finding] = []
    rel = _rel(path, agent_meta_root)

    fm = _parse_frontmatter(content)
    if fm is None:
        findings.append(Finding(
            Severity.ERROR, "frontmatter.missing", rel,
            "No YAML frontmatter found (--- block missing or malformed).",
            "Add --- delimited frontmatter with at least name, version, description, tools.",
        ))
        return findings

    # version: present + valid semver
    version = fm.get("version", "")
    if not version:
        findings.append(Finding(
            Severity.ERROR, "frontmatter.version-missing", rel,
            "Frontmatter has no 'version:' field.",
            "Add: version: \"1.0.0\"",
        ))
    elif not _SEMVER_RE.match(str(version).strip('"').strip("'")):
        findings.append(Finding(
            Severity.WARNING, "frontmatter.version-format", rel,
            f"version '{version}' is not valid semver (expected X.Y.Z).",
            "Use format: version: \"1.2.3\"",
        ))

    # version bump check (only for git-changed files)
    if version and changed_files is not None and rel in changed_files:
        head_version = _get_head_version(path, agent_meta_root)
        if head_version and head_version == str(version).strip('"').strip("'"):
            findings.append(Finding(
                Severity.ERROR, "frontmatter.version-bump", rel,
                f"File changed but version '{version}' was not bumped (same as HEAD).",
                "Increment version per conventions: patch=text, minor=new section, major=behaviour change.",
            ))

    # name: present
    if not fm.get("name"):
        findings.append(Finding(
            Severity.WARNING, "frontmatter.name-missing", rel,
            "Frontmatter has no 'name:' field.",
        ))

    # description: present
    if not fm.get("description"):
        findings.append(Finding(
            Severity.WARNING, "frontmatter.description-missing", rel,
            "Frontmatter has no 'description:' field.",
        ))

    # tools: must be a list
    tools = fm.get("tools")
    if tools is not None and not isinstance(tools, list):
        findings.append(Finding(
            Severity.ERROR, "frontmatter.tools-not-list", rel,
            f"'tools:' must be a YAML list, got: {type(tools).__name__}.",
            "Use:\n  tools:\n    - Bash\n    - Read",
        ))

    # workflow_tier: valid value if present
    wt = fm.get("workflow_tier", "")
    if wt and wt not in _VALID_WORKFLOW_TIERS:
        findings.append(Finding(
            Severity.ERROR, "frontmatter.workflow-tier-invalid", rel,
            f"Invalid workflow_tier '{wt}'.",
            f"Use one of: {', '.join(sorted(_VALID_WORKFLOW_TIERS))}",
        ))

    # 2-platform specific checks
    is_platform = "2-platform" in str(path)
    if is_platform:
        if not fm.get("based-on"):
            findings.append(Finding(
                Severity.WARNING, "frontmatter.based-on-missing", rel,
                "2-platform agent has no 'based-on:' field.",
                "Add: based-on: \"1-generic/<role>.md@<version>\"",
            ))
        extends = fm.get("extends", "")
        if extends:
            findings += _check_extends(extends, rel, agent_meta_root)
            # check patch anchors resolve in base file
            patches = fm.get("patches", [])
            if isinstance(patches, list):
                findings += _check_patch_anchors(patches, extends, rel, agent_meta_root)

    return findings


def _check_extends(extends: str, rel: str, agent_meta_root: Path) -> list[Finding]:
    findings = []
    base_path = agent_meta_root / "agents" / extends
    if not base_path.exists():
        findings.append(Finding(
            Severity.ERROR, "frontmatter.extends-not-found", rel,
            f"extends: '{extends}' — base file not found: agents/{extends}",
            "Check the path is correct relative to agents/.",
        ))
    return findings


def _check_patch_anchors(patches: list, extends: str, rel: str,
                          agent_meta_root: Path) -> list[Finding]:
    findings = []
    base_path = agent_meta_root / "agents" / extends
    if not base_path.exists():
        return findings  # already reported by _check_extends

    base_content = base_path.read_text(encoding="utf-8")
    for i, patch in enumerate(patches):
        if not isinstance(patch, dict):
            continue
        op = patch.get("op", "")
        anchor = patch.get("anchor", "")
        if op == "append":
            continue  # append has no anchor requirement
        if not anchor:
            findings.append(Finding(
                Severity.WARNING, "frontmatter.patch-anchor-missing", rel,
                f"patches[{i}] op='{op}' has no 'anchor:' field.",
            ))
            continue
        # XML-anchor: check tag exists anywhere in base content
        if anchor.startswith("<") and not anchor.startswith("</"):
            if anchor not in base_content:
                findings.append(Finding(
                    Severity.ERROR, "frontmatter.patch-anchor-not-found", rel,
                    f"patches[{i}] XML anchor not found in base file '{extends}': {anchor!r}",
                    "The opening XML tag must appear in the base file.",
                ))
            continue  # skip the plain-text anchor check below
        base_lines = base_content.splitlines(keepends=True)
        if _find_section_bounds(base_lines, anchor) is None:
            findings.append(Finding(
                Severity.ERROR, "frontmatter.patch-anchor-not-found", rel,
                f"patches[{i}] anchor not found in base file '{extends}': {anchor!r}",
                "The anchor string must appear verbatim as a heading line in the base file "
                "(exact match, not a substring of a longer heading).",
            ))
    return findings


def _parse_frontmatter(content: str) -> dict | None:
    """Parse YAML frontmatter block. Returns dict or None if absent/malformed.

    Handles both normal agents (frontmatter + markdown body) and composition-only
    platform files where the entire file is a single frontmatter block.

    Block-boundary detection delegates to the canonical
    ``lib.frontmatter.split_frontmatter`` (Issue #473). Two behaviors are kept
    on purpose as documented exceptions to the canonical fail-soft parse:

    * strict malformed-YAML→``None`` semantics — this checker must report
      ``frontmatter.missing`` (as before) rather than silently treating a
      malformed block as an empty one;
    * the no-PyYAML regex fallback (`_parse_frontmatter_regex`) — the
      consistency checker must never crash just because PyYAML is absent.

    A strict opening-fence guard preserves the old ``^---\\s*\\n`` requirement
    (fence on its own line): the canonical splitter leniently accepts any
    ``---``-prefixed opening, which would parse garbage instead of reporting
    the missing/malformed frontmatter error.
    """
    try:
        import yaml
    except ImportError:
        return _parse_frontmatter_regex(content)

    # Strict opening-fence precheck (exact emulation of the former regex
    # semantics): the old parser required the opening fence to end in a
    # newline (`^---\s*\n`) and then a further `\n---` *after* that
    # terminator. The canonical splitter is more lenient on both ends
    # (any `---`-suffixed opening fence accepted; the fence's own
    # terminator newline may double as the closing fence's separator, so
    # an adjacent-fence block `---\n---` parsed as empty instead of
    # reporting missing). Reproduce the strict view exactly: `[^\S\n]*`
    # (not `\s*`) keeps the prefix minimal — a blank line between the
    # fences must stay available as the closing fence's own separator,
    # matching the old regex's backtracking behavior (Issue #473).
    opening = re.match(r"^---[^\S\n]*\n", content)
    if opening is None or content.find("\n---", opening.end()) == -1:
        return None
    fm_block, _ = split_frontmatter(content)
    inner = _fm_inner(fm_block)
    try:
        return yaml.safe_load(inner) or {}
    except yaml.YAMLError:
        return None


def _parse_frontmatter_regex(content: str) -> dict | None:
    """Fallback regex-based frontmatter parser (no PyYAML)."""
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None
    result = {}
    for line in match.group(1).splitlines():
        m = re.match(r'^(\w[\w_-]*):\s*(.*)$', line)
        if m:
            key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
            result[key] = val
    return result


def _get_head_version(path: Path, agent_meta_root: Path) -> str | None:
    """Get the version field from the HEAD version of this file via git show."""
    try:
        rel = path.relative_to(agent_meta_root)
        result = subprocess.run(  # noqa: PLW1510
            ["git", "show", f"HEAD:{rel.as_posix()}"],
            cwd=str(agent_meta_root),
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return None
        fm = _parse_frontmatter(result.stdout)
        if fm is None:
            return None
        return str(fm.get("version", "")).strip('"').strip("'") or None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)
