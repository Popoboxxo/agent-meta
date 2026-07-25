"""Cross-reference checks: role-defaults, orchestrator table, CHANGELOG."""

import re
from pathlib import Path

from .report import Finding, Severity


def _parse_frontmatter_yaml(path: Path) -> dict:
    """Parse YAML frontmatter from a markdown file. Returns empty dict on failure."""
    try:
        import yaml
    except ImportError:
        return {}
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except Exception:
        return {}


def _load_based_on_references(agent_meta_root: Path) -> dict[str, set[str]]:
    """Scan 2-platform overrides for based-on references.

    Returns: {generic_template_stem: set of role_names}
    e.g. {"provider-expert": {"claude-expert", "gemini-expert", ...}}
    """
    from collections import defaultdict
    refs: dict[str, set[str]] = defaultdict(set)
    platform_dir = agent_meta_root / "agents" / "2-platform"
    if not platform_dir.exists():
        return dict(refs)

    # Build role-name → 2-platform-stem mapping by parsing {{PREFIX}} from name field
    for md in sorted(platform_dir.glob("*.md")):
        fm = _parse_frontmatter_yaml(md)
        based_on = fm.get("based-on", "")
        if not based_on or not based_on.startswith("1-generic/"):
            continue
        # Strip version suffix (@1.0.0) and extract stem
        generic_stem = Path(based_on.split("@")[0]).stem

        # Extract role name from the 'name' field (e.g. "{{PREFIX}}claude-expert")
        name_field = fm.get("name", "")
        role = name_field.replace("{{PREFIX}}", "").lstrip("-")
        if not role:
            continue
        refs[generic_stem].add(role)
    return {k: v for k, v in refs.items()}


def get_based_on_role_names(agent_meta_root: Path) -> set[str]:
    """Return the flat set of role names generated via ``based-on`` references.

    Public wrapper around :func:`_load_based_on_references` that collapses the
    ``{generic_stem: {role, ...}}`` mapping into a single set of role names.

    These roles do not have their own ``agents/1-generic/<role>.md`` file —
    they are produced by a 2-platform override extending a multi-instance base
    template (e.g. ``provider-expert.md`` → ``claude-expert``,
    ``gemini-expert``, ...). Callers that check for "role has no template"
    must exclude these names to avoid false-positives.

    Args:
        agent_meta_root: Repository root containing ``agents/2-platform/``.

    Returns:
        Flat set of role names. Empty when no based-on references exist.
    """
    refs = _load_based_on_references(agent_meta_root)
    result: set[str] = set()
    for roles in refs.values():
        result.update(roles)
    return result


def check_role_defaults_coverage(agent_meta_root: Path) -> list[Finding]:
    """Every 1-generic agent (non-workflow) must have an entry in role-defaults.yaml.

    Skips base templates that are only used via based-on from 2-platform overrides.
    """
    findings = []
    roles_path = agent_meta_root / "config" / "role-defaults.yaml"
    if not roles_path.exists():
        return [Finding(Severity.ERROR, "crossrefs.role-defaults-missing",
                        "config/role-defaults.yaml", "File not found.")]

    role_names = _load_role_names(roles_path)
    agents_dir = agent_meta_root / "agents" / "1-generic"
    if not agents_dir.exists():
        return findings

    # Templates that serve as base for 2-platform overrides (via based-on)
    based_on_refs = _load_based_on_references(agent_meta_root)
    base_template_stems = set(based_on_refs.keys())

    for md in sorted(agents_dir.glob("*.md")):
        if md.name.startswith("_"):
            continue  # workflow helpers (_wf-*.md) are not roles
        role = md.stem
        if role in base_template_stems:
            continue  # base template used by 2-platform overrides
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

    # The agent table is generated at sync time from the {{AGENT_DELEGATION_TABLE}}
    # placeholder (see scripts/lib/delegation_table.py), which lists every role from
    # role-defaults.yaml. When the placeholder is still present in the source template
    # the table is not hand-maintained, so per-role literal checks would only produce
    # false positives — skip them.
    if "{{AGENT_DELEGATION_TABLE}}" in orch_content:
        return findings

    for role, tier in roles_data.items():
        if role == "orchestrator":
            continue  # orchestrator doesn't list itself
        if tier not in ("required", "recommended"):
            continue  # optional roles are not required in the table
        # Check if role appears inside any table cell: | ... `role` ... |
        # (roles may share a cell, e.g. "`feature` (komplex) oder `developer`")
        pattern = rf'\|[^|\n]*`{re.escape(role)}`[^|\n]*\|'
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
    """Every role in role-defaults.yaml should have a corresponding 1-generic source file.

    Also accepts roles that have a 2-platform override with based-on pointing
    to an existing 1-generic base template (e.g. claude-expert → provider-expert.md).
    """
    findings = []
    roles_path = agent_meta_root / "config" / "role-defaults.yaml"
    if not roles_path.exists():
        return findings

    role_names = _load_role_names(roles_path)
    agents_dir = agent_meta_root / "agents" / "1-generic"

    # Roles covered by 2-platform based-on references (generic_stem → {roles})
    based_on_refs = _load_based_on_references(agent_meta_root)
    covered_roles: set[str] = set()
    for generic_stem, roles in based_on_refs.items():
        if (agents_dir / f"{generic_stem}.md").exists():
            covered_roles.update(roles)

    for role in role_names:
        agent_file = agents_dir / f"{role}.md"
        if not agent_file.exists() and role not in covered_roles:
            findings.append(Finding(
                Severity.WARNING, "crossrefs.role-defaults-orphan",
                "config/role-defaults.yaml",
                f"Role '{role}' defined in role-defaults.yaml has no agents/1-generic/{role}.md.",
                f"Create agents/1-generic/{role}.md or remove the role entry.",
            ))
    return findings


def check_schema_refs(agent_meta_root: Path) -> list[Finding]:
    """Every "schema_ref" value in an agent source file must point to an existing file.

    Scans agents/1-generic/*.md and agents/2-platform/*.md (NOT generated outputs)
    for occurrences of `"schema_ref": "<path>"` and reports an ERROR for each path
    that does not resolve under the agent-meta root.
    """
    findings: list[Finding] = []
    pattern = re.compile(r'"schema_ref"\s*:\s*"([^"]+)"')

    for layer in ("1-generic", "2-platform"):
        layer_dir = agent_meta_root / "agents" / layer
        if not layer_dir.exists():
            continue
        for md in sorted(layer_dir.glob("*.md")):
            try:
                content = md.read_text(encoding="utf-8")
            except OSError:
                continue
            rel_file = str(md.relative_to(agent_meta_root)).replace("\\", "/")
            for match in pattern.finditer(content):
                ref = match.group(1)
                # Skip angle-bracket placeholders like "<schema-uri>" — these are
                # documentation examples, not real file paths.
                if ref.startswith("<") and ref.endswith(">"):
                    continue
                ref_path = agent_meta_root / ref
                if not ref_path.exists():
                    findings.append(Finding(
                        Severity.ERROR, "crossrefs.schema-ref-missing",
                        rel_file,
                        f"schema_ref '{ref}' in {rel_file} does not exist.",
                        f"Create '{ref}' or fix the schema_ref value.",
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
    name = filepath.rsplit("/", 1)[-1]
    if name.startswith("."):
        return False  # marker files like .agent-meta-managed
    return "agents/" in filepath or "commands/" in filepath
