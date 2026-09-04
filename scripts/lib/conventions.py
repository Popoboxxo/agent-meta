"""Conventions layer: naming/versioning convention presets rendered into blocks.

Generic foundation (preset resolution + role-gating) plus per-domain renderers
that turn structured preset data into the exact markdown used in the release/git
agent templates. Mirrors the rules.py preset+override pattern (resolve_rules).

The 'default' preset reproduces today's hardcoded release.md/git.md text
byte-for-byte — see tests/test_conventions_migration_invariant.py.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

from .io import _deep_merge, _load_yaml_or_json
from .log import SyncLog

CONVENTIONS_PRESETS_CONFIG_YAML = "config/conventions-presets.yaml"

# Per keep-a-changelog section: the descriptive example bullet used today in
# release.md. Kept as an explicit map so the 'default' preset stays byte-
# identical (each section has its own wording). Unknown sections fall back to a
# generic placeholder.
_KEEP_A_CHANGELOG_EXAMPLES = {
    "Added": "[feature description]",
    "Fixed": "[bugfix description]",
    "Changed": "[change]",
    "Removed": "[what was removed]",
}


def load_conventions_presets(agent_meta_root: Path) -> dict:
    """Load config/conventions-presets.yaml. Same loader pattern as resolve_rules()."""
    data, _ = _load_yaml_or_json(agent_meta_root / CONVENTIONS_PRESETS_CONFIG_YAML)
    if not data:
        return {}
    presets = data.get("presets", {})
    return {k: v for k, v in presets.items() if not k.startswith("_")}


def resolve_conventions(config: dict, agent_meta_root: Path) -> dict:
    """Resolve effective conventions from preset + project overrides.

    Precedence (highest to lowest):
      1. config["conventions"][domain][field]  — project override
      2. conventions-preset[domain][field]     — preset default
      3. 'default' preset

    Deep-merges the project 'conventions' block over the selected preset,
    per-domain and per-field (same merge semantics as resolve_rules()).

    v1 constraint: for each domain, 'applies_to_roles' must resolve to a list of
    length exactly 1. Raises ValueError (naming the offending domain) if a preset
    or override declares more than one role for a domain — the caller catches
    this, surfaces it via log.warning, and continues with conventions skipped.
    """
    presets = load_conventions_presets(agent_meta_root)
    preset_name = config.get("conventions-preset", "default") or "default"

    if preset_name not in presets and preset_name != "default":
        print(f"  !  Unknown conventions-preset '{preset_name}' — falling back to 'default'",
              file=sys.stderr)
        preset_name = "default"

    resolved = copy.deepcopy(presets.get(preset_name, {}))
    project_overrides = config.get("conventions", {}) or {}
    _deep_merge(resolved, copy.deepcopy(project_overrides))

    for domain, spec in resolved.items():
        if not isinstance(spec, dict):
            continue
        declared_roles = spec.get("applies_to_roles", [])
        if len(declared_roles) != 1:
            raise ValueError(
                f"conventions domain '{domain}': applies_to_roles must declare "
                f"exactly one role in v1, got {declared_roles!r}"
            )

    return resolved


def render_convention_block(
    domain: str, spec: dict, active_roles: set | None, log: SyncLog
) -> dict | None:
    """Generic layer: role-gate a domain against active_roles, then dispatch.

    Role-gate uses spec['applies_to_roles'][0] (v1: exactly one role, enforced by
    resolve_conventions). active_roles None = all roles active (delegation_table
    pattern). If the role is not active, log.skip and return None — no variable is
    computed at all (not even an empty string), per Konzept Abschnitt C: the
    role's template is not generated when the role is inactive, so its placeholder
    is irrelevant.

    Otherwise dispatch to the domain-specific renderer(s) and return a dict of
    {variable_name: markdown}. The 'release' domain produces two variables
    (versioning table + changelog code block) from two separate renderers; the
    concept declares this dict return (Abschnitt 4B signature).
    """
    declared_roles = spec.get("applies_to_roles", [])
    role = declared_roles[0] if declared_roles else None

    if active_roles is not None and role not in active_roles:
        log.skip(
            f"conventions.{domain}",
            f"Rolle '{role}' nicht in project.yaml roles: — Konvention "
            f"'{domain}' wird nicht injiziert (kein Platzhalter berechnet)",
        )
        return None

    if domain == "release":
        return {
            "RELEASE_VERSIONING_BLOCK": _render_release_versioning(spec),
            "RELEASE_CHANGELOG_BLOCK": _render_release_changelog(spec),
            "RELEASE_CUSTOM_CHECKLIST_BLOCK": _render_release_custom_checklist(spec),
        }
    if domain == "issues":
        return {"GIT_ISSUE_NAMING_BLOCK": _render_git_issue_naming(spec)}

    return None


def _bump_label(bump: str) -> str:
    """Uppercase a bump kind for the versioning table's Bump column.

    Generic .upper() so new bump kinds (e.g. calver's 'month') render as MONTH
    without a hardcoded map. 'suffix' is the single documented exception: today's
    release.md renders the pre-release bump as title-case 'Suffix', not 'SUFFIX'
    — preserved to keep the default preset byte-identical.
    """
    if bump == "suffix":
        return "Suffix"
    return bump.upper()


def _format_bump_example(bump: str, example: str) -> str:
    """Format a bump rule's Example cell.

    Suffix examples list pre-release identifiers; today's release.md wraps each
    dash-bearing token in backticks (`-alpha.x` / `-beta.x`). Only applied to
    suffix bumps so ordinary examples that merely contain '-' stay plain.
    """
    if bump == "suffix":
        parts = [f"`{p}`" if "-" in p else p for p in example.split(" / ")]
        return " / ".join(parts)
    return example


def _render_release_versioning(spec: dict) -> str:
    """Render spec['versioning'] into today's release.md '## 2. Versioning' table."""
    versioning = spec.get("versioning", {})
    lines = ["| Change | Bump | Example |", "|--------|------|---------|"]
    for rule in versioning.get("bump_rules", []):
        bump = rule.get("bump", "")
        lines.append(
            f"| {rule.get('trigger', '')} | {_bump_label(bump)} | "
            f"{_format_bump_example(bump, rule.get('example', ''))} |"
        )
    return "\n".join(lines)


def _render_release_custom_checklist(spec: dict) -> str:
    """Render spec['custom_checklist'] into extra rows for release.md's checklist.

    Each entry is a {task, verification} pair, appended as additional
    '| <task> | <verification> |' rows in the same format as the hardcoded
    '## 1. Pre-release checklist' table. Returns "" (empty string, no header,
    no dangling table) when the list is empty or absent — this keeps the
    generated release.md byte-identical for projects without a custom_checklist
    (migration invariant, see tests/test_conventions_migration_invariant.py).
    Entries missing a 'verification' render an empty second cell.
    """
    entries = spec.get("custom_checklist", []) or []
    rows = [
        f"| {e.get('task', '')} | {e.get('verification', '')} |"
        for e in entries
        if isinstance(e, dict) and e.get("task")
    ]
    return "\n".join(rows)


def _render_release_changelog(spec: dict) -> str:
    """Render spec['changelog'] into a markdown code block.

    keep-a-changelog reproduces today's release.md '## 3. CHANGELOG.md format'
    exactly (header '## [x.y.z] — YYYY-MM-DD', one '### <Section>' per section
    with an example bullet; entry_prefix is prepended unless empty, but 'Removed'
    never carries the prefix even when one is set). angular renders a compact
    Angular-style changelog example.
    """
    changelog = spec.get("changelog", {})
    fmt = changelog.get("format", "keep-a-changelog")
    sections = changelog.get("sections", [])

    if fmt == "angular":
        return _render_changelog_angular(sections)
    return _render_changelog_keep_a_changelog(sections, changelog.get("entry_prefix", ""))


def _render_changelog_keep_a_changelog(sections: list, entry_prefix: str) -> str:
    lines = ["```markdown", "## [x.y.z] — YYYY-MM-DD", ""]
    for i, section in enumerate(sections):
        lines.append(f"### {section}")
        # 'Removed' never carries the entry prefix, even when one is set — matches
        # today's release.md ('- [what was removed]', no 'REQ-xxx: ').
        prefix = "" if section == "Removed" else entry_prefix
        example = _KEEP_A_CHANGELOG_EXAMPLES.get(section, "[...]")
        lines.append(f"- {prefix}{example}")
        if i < len(sections) - 1:
            lines.append("")
    lines.append("```")
    return "\n".join(lines)


def _render_changelog_angular(sections: list) -> str:
    lines = ["```markdown", "## [x.y.z] (YYYY-MM-DD)", ""]
    for i, section in enumerate(sections):
        lines.append(f"### {section}")
        lines.append("- <scope>: <description> (<commit-hash>)")
        if i < len(sections) - 1:
            lines.append("")
    lines.append("```")
    return "\n".join(lines)


def _render_git_issue_naming(spec: dict) -> str:
    """Render issue-naming fields into the git.md GIT_ISSUE_NAMING_BLOCK.

    Format per Konzept Abschnitt 5. title_format/labels.namespace use {field}
    templating in the preset; rendered here as <field> angle-bracket placeholders.
    """
    title = spec.get("title_format", "").replace("{", "<").replace("}", ">")
    types = ", ".join(f"`{t}`" for t in spec.get("types", []))
    namespace = spec.get("labels", {}).get("namespace", "").replace("{", "<").replace("}", ">")
    keywords = ", ".join(f"`{kw} #123`" for kw in spec.get("closing_keywords", []))
    return (
        f"**Issue-Titel-Format:** `{title}` — Types: {types} "
        f"(identisch zum Commit-Type-Vokabular, siehe `commit-conventions.md`).\n"
        f"**Labels:** `{namespace}` (Namespace-Label je Issue-Type).\n"
        f"**Closing-Keywords:** {keywords} im PR/Commit."
    )
