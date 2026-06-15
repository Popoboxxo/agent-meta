"""Integrations framework — registry loading, two-gate resolution, MCP wiring.

Manages pip/uv-installed tools with an install/init/index lifecycle that
expose themselves as MCP servers (e.g. semble). Two-Gate activation:

    approved (Meta-Maintainer gate)  AND  enabled (Project gate)

Public interface:
    load_integrations_registry(registry_path)
        → dict of approved+unapproved integrations from
          config/integrations-registry.yaml

    resolve_enabled_integrations(registry, project_config)
        → dict of {name: merged_entry} for integrations where the registry
          marks approved=true AND the project config sets enabled=true

    validate_options(name, user_options, registry_options_schema)
        → (valid: bool, errors: list[str])
          Validates user-supplied options against the registry's options block.

    build_mcp_entries(enabled_integrations)
        → list of {"name", "command", "transport"} dicts ready for the
          provider config writer.

    build_tool_awareness(enabled_integrations)
        → Markdown string with tool hints per enabled integration.
          Used for rules/integrations.md and the INTEGRATION_TOOLS_HINT
          template variable.

    write_pending_marker(target_path, pending_integrations)
        → Writes .claude/pending-integrations.json when init is still
          outstanding (or removes the marker when empty).

This module is stdlib-only with a graceful PyYAML fallback for the
registry loader. No hardcoded integration names — fully generic.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


# ---------------------------------------------------------------------------
# Registry loading
# ---------------------------------------------------------------------------

def load_integrations_registry(registry_path) -> dict:
    """Load and parse config/integrations-registry.yaml.

    Returns a dict {integration_name: entry_dict} or an empty dict when
    the file is missing. Uses PyYAML when available; falls back to a
    minimal key-value parser otherwise (sufficient for the simple
    structures the registry uses at the top level — nested structures
    are best-effort).
    """
    path = Path(registry_path)
    if not path.exists():
        return {}

    if _YAML_AVAILABLE:
        try:
            with path.open(encoding="utf-8") as f:
                data = _yaml.safe_load(f) or {}
        except _yaml.YAMLError as e:
            import sys
            print(f"[integrations] Warning: Failed to parse integrations-registry.yaml: {e}", file=sys.stderr)
            return {}
    else:
        data = _parse_registry_minimal(path)

    if not isinstance(data, dict):
        return {}
    integrations = data.get("integrations", {})
    if not isinstance(integrations, dict):
        return {}
    return integrations


def _parse_registry_minimal(path: Path) -> dict:
    """Minimal YAML fallback parser for integrations-registry.yaml.

    Handles the subset actually used: top-level keys, nested dicts and
    flow-style lists. Strips comments and trims whitespace. This is
    best-effort — if PyYAML is not available the registry contents will
    parse only structurally, and complex option validation degrades to
    type-level checks only.
    """
    result: dict = {"integrations": {}}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return result

    # Strip comments and blank-only lines while preserving structure
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        # remove '# ...' comments outside of quotes (registry has no quoted '#')
        stripped = re.sub(r"\s+#.*$", "", raw)
        stripped = re.sub(r"^#.*$", "", stripped)
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        lines.append((indent, stripped.strip()))

    # Walk lines: top-level "integrations:" section, then per-integration
    # blocks indented under it. We keep only name + a flat marker dict so
    # downstream code can still see entries exist; full structure decoding
    # requires PyYAML.
    in_integrations = False
    current_name: str | None = None
    for indent, line in lines:
        if indent == 0 and line.startswith("integrations:"):
            in_integrations = True
            continue
        if indent == 0:
            in_integrations = False
            continue
        if not in_integrations:
            continue
        if indent == 2 and line.endswith(":"):
            current_name = line[:-1].strip()
            result["integrations"][current_name] = {
                "approved": False,
                "_partial": True,
            }
            continue
        if current_name and indent == 4:
            m = re.match(r"^(\w+):\s*(.*)$", line)
            if not m:
                continue
            key, value = m.group(1), m.group(2).strip()
            if value == "":
                continue
            # Coerce booleans
            if value.lower() in ("true", "false"):
                result["integrations"][current_name][key] = value.lower() == "true"
            else:
                result["integrations"][current_name][key] = value.strip('"').strip("'")
    return result


# ---------------------------------------------------------------------------
# Two-Gate resolution
# ---------------------------------------------------------------------------

def resolve_enabled_integrations(registry: dict, project_config: dict) -> dict:
    """Return the set of integrations active for this project.

    Two-Gate semantics:
        registry[name].approved == True  AND  project.integrations[name].enabled == True

    The result merges per-integration registry data with project-level
    options (project options override registry defaults via dict merge).
    Integrations missing in the registry are skipped silently — calling
    code may warn separately.
    """
    if not isinstance(registry, dict) or not isinstance(project_config, dict):
        return {}

    project_integrations = project_config.get("integrations") or {}
    if not isinstance(project_integrations, dict):
        return {}

    enabled: dict = {}
    for name, user_cfg in project_integrations.items():
        if not isinstance(user_cfg, dict):
            continue
        if not user_cfg.get("enabled"):
            continue
        registry_entry = registry.get(name)
        if not isinstance(registry_entry, dict):
            continue
        if not registry_entry.get("approved"):
            continue
        # Shallow merge: registry first, then project options on top
        merged = dict(registry_entry)
        for key, value in user_cfg.items():
            if key == "enabled":
                continue
            merged[key] = value
        enabled[name] = merged
    return enabled


# ---------------------------------------------------------------------------
# Options validation
# ---------------------------------------------------------------------------

def validate_options(
    integration_name: str,
    user_options: dict,
    registry_options_schema: dict,
) -> tuple[bool, list[str]]:
    """Validate user-supplied options against the registry options schema.

    Returns (valid, errors). Supported schema features:
        type: string | integer | array
        items: list of allowed enum values (for arrays)
        default: ignored here (handled at consumption time)

    Unknown user options are reported as errors. Missing schema entries
    degrade gracefully (treated as untyped — accepted).
    """
    errors: list[str] = []
    if not isinstance(user_options, dict):
        return True, []
    if not isinstance(registry_options_schema, dict):
        # No schema available — accept (graceful degradation, e.g. when
        # the registry was parsed without PyYAML and nested structures
        # could not be reconstructed).
        return True, []

    for key, value in user_options.items():
        spec = registry_options_schema.get(key)
        if spec is None:
            errors.append(
                f"{integration_name}: unknown option '{key}' — not declared in registry"
            )
            continue
        if not isinstance(spec, dict):
            continue
        declared_type = spec.get("type")
        if declared_type == "string":
            if not isinstance(value, str):
                errors.append(
                    f"{integration_name}.{key}: expected string, got {type(value).__name__}"
                )
        elif declared_type == "integer":
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(
                    f"{integration_name}.{key}: expected integer, got {type(value).__name__}"
                )
        elif declared_type == "array":
            if not isinstance(value, list):
                errors.append(
                    f"{integration_name}.{key}: expected array, got {type(value).__name__}"
                )
                continue
            allowed_items = spec.get("items")
            if isinstance(allowed_items, list) and allowed_items:
                for item in value:
                    if item not in allowed_items:
                        errors.append(
                            f"{integration_name}.{key}: value '{item}' not in allowed "
                            f"items {allowed_items}"
                        )
        # Unknown declared_type → no enforcement (forward-compat).

    return (len(errors) == 0), errors


# ---------------------------------------------------------------------------
# MCP entry construction
# ---------------------------------------------------------------------------

def build_mcp_entries(enabled_integrations: dict) -> list[dict]:
    """Build a list of MCP entries from enabled integrations.

    Each entry has the shape:
        {"name": str, "command": list[str], "transport": str}

    Source: registry_entry["mcp"]["command"] / ["transport"].
    Integrations without an mcp block are skipped silently — they may
    still be installed and indexed via the lifecycle without exposing
    an MCP server.
    """
    entries: list[dict] = []
    if not isinstance(enabled_integrations, dict):
        return entries
    for name, entry in enabled_integrations.items():
        if not isinstance(entry, dict):
            continue
        mcp = entry.get("mcp")
        if not isinstance(mcp, dict):
            continue
        command = mcp.get("command")
        transport = mcp.get("transport")
        if not command or not transport:
            continue
        if not isinstance(command, list):
            # Tolerate string command — wrap in list for uniformity.
            command = [str(command)]
        entries.append({
            "name": name,
            "command": list(command),
            "transport": str(transport),
        })
    return entries


# ---------------------------------------------------------------------------
# Tool-awareness Markdown for rules/integrations.md
# ---------------------------------------------------------------------------

def build_tool_awareness(enabled_integrations: dict) -> str:
    """Generate Markdown describing the tools each enabled integration offers.

    Used both as content for rules/integrations.md and as the
    INTEGRATION_TOOLS_HINT template variable. Returns an empty string
    when no integrations are enabled or when none expose mcp tools.
    """
    if not isinstance(enabled_integrations, dict) or not enabled_integrations:
        return ""

    sections: list[str] = []
    for name, entry in enabled_integrations.items():
        if not isinstance(entry, dict):
            continue
        mcp = entry.get("mcp")
        if not isinstance(mcp, dict):
            continue
        tools = mcp.get("tools")
        if not isinstance(tools, list) or not tools:
            continue

        description = entry.get("description", "")
        header_lines: list[str] = [f"### {name}"]
        if description:
            header_lines.append("")
            header_lines.append(str(description).strip())
        header_lines.append("")
        header_lines.append("Available tools:")
        header_lines.append("")

        tool_lines: list[str] = []
        for tool in tools:
            if not isinstance(tool, dict):
                continue
            tool_name = tool.get("name")
            tool_hint = tool.get("hint", "")
            if not tool_name:
                continue
            if tool_hint:
                tool_lines.append(f"- `{tool_name}` — {str(tool_hint).strip()}")
            else:
                tool_lines.append(f"- `{tool_name}`")

        if not tool_lines:
            continue
        sections.append("\n".join(header_lines + tool_lines))

    if not sections:
        return ""
    return "\n\n".join(sections) + "\n"


# ---------------------------------------------------------------------------
# Pending-init marker
# ---------------------------------------------------------------------------

def write_pending_marker(target_path, pending_integrations: list[str]) -> None:
    """Write or remove the .claude/pending-integrations.json marker.

    When pending_integrations is non-empty, writes a JSON document:
        {"pending": [...], "created_at": "<ISO-8601>"}

    When empty, removes the marker file if present so downstream checks
    do not see stale state. Missing parent directories are created.
    """
    path = Path(target_path)
    if not pending_integrations:
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass
        return

    payload = {
        "pending": list(pending_integrations),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
