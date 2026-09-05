"""DoD preset loading and resolution."""

import sys
from pathlib import Path

from .io import _load_yaml_or_json

DOD_PRESETS_CONFIG_YAML = "config/dod-presets.yaml"
_DOD_PRESETS_CONFIG_LEGACY = "dod-presets.config.yaml"
_DOD_PRESETS_CONFIG_JSON = "dod-presets.config.json"  # legacy fallback


def load_dod_presets(agent_meta_root: Path) -> dict:
    """Load config/dod-presets.yaml with fallback to legacy paths."""
    data, _ = _load_yaml_or_json(
        agent_meta_root / DOD_PRESETS_CONFIG_YAML,
        agent_meta_root / _DOD_PRESETS_CONFIG_LEGACY,
        agent_meta_root / _DOD_PRESETS_CONFIG_JSON,
    )
    if not data:
        return {}
    presets = data.get("presets", {})
    # Strip comment keys (JSON legacy: keys starting with "_")
    return {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")}
            for k, v in presets.items() if not k.startswith("_")}


def resolve_dod(config: dict, agent_meta_root: Path) -> dict:
    """Resolve effective DoD values from preset + overrides.

    Precedence (highest to lowest):
    1. Project override:  config["dod"][key]
    2. Preset default:    dod-presets.config.yaml[preset][key]
    3. "full" preset:     fallback if preset not found
    """
    presets = load_dod_presets(agent_meta_root)
    preset_name = config.get("dod-preset", "full") or "full"

    # Fallback to "full" preset when named preset not found
    if preset_name not in presets:
        if preset_name != "full":
            print(f"  !  Unknown dod-preset '{preset_name}' — falling back to 'full'",
                  file=sys.stderr)
        preset_name = "full"

    preset_values = presets.get(preset_name, {})

    dod_overrides = config.get("dod", {})

    # All known DoD keys — sourced from the full preset as authoritative key set
    full_preset = presets.get("full", {
        "req-traceability": True,
        "tests-required": True,
        "codebase-overview": True,
        "security-audit": False,
        "ai-security-review": False,
        "prompt-governance": False,
        "lifecycle-ownership": False,
        "se-required": "false",
    })

    resolved = {}
    for key, default_val in full_preset.items():
        # "release-gates" is a nested dict, not a flat dod field — it has its
        # own resolver (resolve_release_gates()) and its own project.yaml
        # override axis (top-level `release-gates:`, not `dod:`). Excluded
        # here so resolve_dod()'s contract stays "flat bool/string values only".
        if key == "release-gates":
            continue
        if key in dod_overrides:
            resolved[key] = dod_overrides[key]
        elif key in preset_values:
            resolved[key] = preset_values[key]
        else:
            resolved[key] = default_val
    return resolved


def resolve_release_gates(config: dict, agent_meta_root: Path) -> dict[str, bool]:
    """Resolve enabled/disabled defaults for release-gate scripts (issue #558).

    Two independent sources merge here — deliberately NOT part of the flat
    `dod` block resolved by resolve_dod():

    1. Preset defaults for the built-in gate names, nested under the active
       DoD preset's `release-gates:` key in config/dod-presets.yaml.
    2. Project overrides: the top-level `release-gates:` key in
       .meta-config/project.yaml — highest precedence. Accepts either
       `{name: {enabled: bool, ...}}` (extra keys ignored here, reserved for
       the gate script itself to read) or a bare `{name: bool}`. Can name
       project-specific gates unknown to any preset.

    Returns a dict of gate-name -> bool for every name known to either
    source. A name absent from both (e.g. a project-authored custom gate
    with no project.yaml entry) is intentionally NOT included — callers
    (scripts/lib/hook_plugins.py::sync_release_gates()) fall back to that gate
    script's own `enabled_by_default` header in that case.
    """
    presets = load_dod_presets(agent_meta_root)
    preset_name = config.get("dod-preset", "full") or "full"
    if preset_name not in presets:
        preset_name = "full"
    preset_gates = presets.get(preset_name, {}).get("release-gates", {}) or {}

    resolved: dict[str, bool] = {k: bool(v) for k, v in preset_gates.items()}

    project_gates_cfg = config.get("release-gates", {}) or {}
    for name, entry in project_gates_cfg.items():
        if isinstance(entry, dict) and "enabled" in entry:
            resolved[name] = bool(entry["enabled"])
        elif isinstance(entry, bool):
            resolved[name] = entry
    return resolved
