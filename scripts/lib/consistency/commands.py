"""Consistency checks specific to commands/*.md files."""

import re
from pathlib import Path

from .report import Finding, Severity


def check_command_frontmatter(path: Path, content: str, agent_meta_root: Path) -> list[Finding]:
    """Validate frontmatter fields required for command files."""
    findings = []
    rel = _rel(path, agent_meta_root)

    fm_raw = _extract_frontmatter_raw(content)
    if fm_raw is None:
        findings.append(Finding(
            Severity.ERROR, "commands.frontmatter-missing", rel,
            "Command file has no YAML frontmatter.",
            "Add --- block with at least: description, allowed-tools.",
        ))
        return findings

    fm = _parse_frontmatter(fm_raw)

    # description: required
    if not fm.get("description", "").strip():
        findings.append(Finding(
            Severity.ERROR, "commands.description-missing", rel,
            "Command frontmatter has no 'description:' field.",
            "Add: description: What this command does",
        ))

    # allowed-tools: required + must be a list
    allowed_tools = fm.get("allowed-tools")
    if allowed_tools is None:
        findings.append(Finding(
            Severity.WARNING, "commands.allowed-tools-missing", rel,
            "Command frontmatter has no 'allowed-tools:' field.",
            "Add: allowed-tools: [\"Bash\", \"Read\"]",
        ))
    elif isinstance(allowed_tools, str):
        # Common mistake: allowed-tools: "Bash" instead of ["Bash"]
        findings.append(Finding(
            Severity.ERROR, "commands.allowed-tools-not-list", rel,
            f"'allowed-tools' must be a JSON/YAML array, got string: {allowed_tools!r}",
            "Use: allowed-tools: [\"Bash\", \"Read\"]",
        ))

    # argument-hint: recommended
    if "argument-hint" not in fm:
        findings.append(Finding(
            Severity.INFO, "commands.argument-hint-missing", rel,
            "Command has no 'argument-hint:' field.",
            "Add: argument-hint: \"[optional args]\" to improve UX.",
        ))

    # body must reference $ARGUMENTS if argument-hint suggests args
    hint = fm.get("argument-hint", "")
    body = content[content.index("---", 3) + 3:].strip() if content.count("---") >= 2 else content
    if hint and "[" in hint and "$ARGUMENTS" not in body:
        findings.append(Finding(
            Severity.WARNING, "commands.arguments-not-used", rel,
            "Command has argument-hint but body does not reference $ARGUMENTS.",
            "Add $ARGUMENTS to the command body to pass user arguments to the agent.",
        ))

    return findings


def check_duplicate_commands(agent_meta_root: Path) -> list[Finding]:
    """Detect commands with overlapping purpose (same delegation target + type)."""
    findings = []
    commands_dir = agent_meta_root / "commands"
    if not commands_dir.exists():
        return findings

    # Collect all command files across layers
    cmd_files: list[Path] = []
    for layer in ("1-generic", "2-platform", "0-external"):
        layer_dir = commands_dir / layer
        if layer_dir.exists():
            cmd_files.extend(layer_dir.glob("*.md"))

    # Build map: stem -> files (duplicates across layers are intentional overrides, same layer = problem)
    by_layer_stem: dict[str, list[Path]] = {}
    for f in cmd_files:
        layer = f.parent.name
        key = f"{layer}/{f.stem}"
        by_layer_stem.setdefault(key, []).append(f)

    for key, files in by_layer_stem.items():
        if len(files) > 1:
            findings.append(Finding(
                Severity.WARNING, "commands.duplicate-in-layer",
                str(files[0].relative_to(agent_meta_root)).replace("\\", "/"),
                f"Multiple command files with same name in same layer: {[str(f.name) for f in files]}",
            ))

    return findings


# ── helpers ───────────────────────────────────────────────────────────────────

def _extract_frontmatter_raw(content: str) -> str | None:
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    return match.group(1) if match else None


def _parse_frontmatter(raw: str) -> dict:
    try:
        import yaml
        return yaml.safe_load(raw) or {}
    except (ImportError, Exception):  # noqa: BLE001
        result = {}
        for line in raw.splitlines():
            m = re.match(r'^([\w-]+):\s*(.*)$', line)
            if m:
                key, val = m.group(1), m.group(2).strip()
                # Try to detect JSON array
                if val.startswith("["):
                    try:
                        import json
                        result[key] = json.loads(val)
                        continue
                    except Exception:  # noqa: BLE001, S110
                        pass
                result[key] = val.strip('"').strip("'")
        return result


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)
