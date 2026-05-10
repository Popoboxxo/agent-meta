"""Cross-reference checks: role-defaults, orchestrator table, CHANGELOG."""

import re
from pathlib import Path

from .report import Finding, Severity


def check_role_defaults_coverage(agent_meta_root: Path) -> list[Finding]:
    """Every 1-generic agent (non-workflow) must have an entry in role-defaults.yaml."""
    findings = []
    roles_path = agent_meta_root / "config" / "role-defaults.yaml"
    if not roles_path.exists():
        return [Finding(Severity.ERROR, "crossrefs.role-defaults-missing",
                        "config/role-defaults.yaml", "File not found.")]

    role_names = _load_role_names(roles_path)
    agents_dir = agent_meta_root / "agents" / "1-generic"
    if not agents_dir.exists():
        return findings

    for md in sorted(agents_dir.glob("*.md")):
        if md.name.startswith("_"):
            continue  # workflow helpers (_wf-*.md) are not roles
        role = md.stem
        if role not in role_names:
            findings.append(Finding(
                Severity.ERROR, "crossrefs.role-not-in-role-defaults",
                f"agents/1-generic/{md.name}",
                f"Agent '{role}' has no entry in config/role-defaults.yaml.",
                f"Add a '{role}:' block under 'roles:' in config/role-defaults.yaml.",
            ))
    return findings


def check_orchestrator_table(agent_meta_root: Path) -> list[Finding]:
    """All required/recommended roles in role-defaults must appear in orchestrator agent table."""
    findings = []
    roles_path = agent_meta_root / "config" / "role-defaults.yaml"
    orch_path = agent_meta_root / "agents" / "1-generic" / "orchestrator.md"

    if not roles_path.exists() or not orch_path.exists():
        return findings

    roles_data = _load_roles_with_tiers(roles_path)
    orch_content = orch_path.read_text(encoding="utf-8")

    for role, tier in roles_data.items():
        if role == "orchestrator":
            continue  # orchestrator doesn't list itself
        if tier not in ("required", "recommended"):
            continue  # optional roles are not required in the table
        # Check if role appears as a table row: | `role` |
        pattern = rf'\|\s*`{re.escape(role)}`\s*\|'
        if not re.search(pattern, orch_content):
            findings.append(Finding(
                Severity.WARNING, "crossrefs.orchestrator-table-incomplete",
                "agents/1-generic/orchestrator.md",
                f"Role '{role}' (workflow_tier: {tier}) is not listed in the orchestrator agent table.",
                f"Add a row: | `{role}` | <description> |",
            ))
    return findings


def check_changelog_mentions_new_files(agent_meta_root: Path,
                                        new_files: list[str]) -> list[Finding]:
    """New agent/command files should be mentioned in CHANGELOG.md [Unreleased] section."""
    findings = []
    if not new_files:
        return findings

    changelog_path = agent_meta_root / "CHANGELOG.md"
    if not changelog_path.exists():
        return findings

    content = changelog_path.read_text(encoding="utf-8")
    # Only check within the [Unreleased] section
    unreleased_match = re.search(r'## \[Unreleased\](.*?)(?=\n## \[|\Z)', content, re.DOTALL)
    if not unreleased_match:
        # No Unreleased section — warn for each new agent/command
        for f in new_files:
            if _is_agent_or_command(f):
                findings.append(Finding(
                    Severity.WARNING, "crossrefs.changelog-no-unreleased",
                    "CHANGELOG.md",
                    f"New file '{f}' added but CHANGELOG has no [Unreleased] section.",
                    "Add ## [Unreleased] with a description of the new files.",
                ))
        return findings

    unreleased_text = unreleased_match.group(1)
    for f in new_files:
        if not _is_agent_or_command(f):
            continue
        # Check if the filename stem appears in the unreleased section
        stem = Path(f).stem
        if stem not in unreleased_text and f not in unreleased_text:
            findings.append(Finding(
                Severity.WARNING, "crossrefs.changelog-missing-entry",
                "CHANGELOG.md",
                f"New file '{f}' not mentioned in [Unreleased] section.",
                f"Add an entry for '{stem}' in the [Unreleased] changelog section.",
            ))
    return findings


def check_role_defaults_has_generic_source(agent_meta_root: Path) -> list[Finding]:
    """Every role in role-defaults.yaml should have a corresponding 1-generic source file."""
    findings = []
    roles_path = agent_meta_root / "config" / "role-defaults.yaml"
    if not roles_path.exists():
        return findings

    role_names = _load_role_names(roles_path)
    agents_dir = agent_meta_root / "agents" / "1-generic"

    for role in role_names:
        agent_file = agents_dir / f"{role}.md"
        if not agent_file.exists():
            findings.append(Finding(
                Severity.WARNING, "crossrefs.role-defaults-orphan",
                "config/role-defaults.yaml",
                f"Role '{role}' defined in role-defaults.yaml has no agents/1-generic/{role}.md.",
                f"Create agents/1-generic/{role}.md or remove the role entry.",
            ))
    return findings


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_role_names(roles_path: Path) -> set[str]:
    try:
        import yaml
        data = yaml.safe_load(roles_path.read_text(encoding="utf-8")) or {}
    except (ImportError, Exception):
        data = _parse_role_names_regex(roles_path)
    return set(data.get("roles", {}).keys())


def _load_roles_with_tiers(roles_path: Path) -> dict[str, str]:
    try:
        import yaml
        data = yaml.safe_load(roles_path.read_text(encoding="utf-8")) or {}
    except (ImportError, Exception):
        return {}
    return {
        name: (cfg or {}).get("workflow_tier", "")
        for name, cfg in data.get("roles", {}).items()
    }


def _parse_role_names_regex(roles_path: Path) -> dict:
    """Minimal regex fallback to extract role names from role-defaults.yaml."""
    content = roles_path.read_text(encoding="utf-8")
    names = re.findall(r'^\s{2}(\w[\w-]+):\s*$', content, re.MULTILINE)
    return {"roles": {n: {} for n in names}}


def _is_agent_or_command(filepath: str) -> bool:
    return "agents/" in filepath or "commands/" in filepath
