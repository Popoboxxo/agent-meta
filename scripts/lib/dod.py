"""DoD preset loading and resolution."""

import sys
from pathlib import Path

from .io import _load_yaml_or_json
from .log import SyncLog

DOD_PRESETS_CONFIG_YAML = "dod-presets.config.yaml"
_DOD_PRESETS_CONFIG_JSON = "dod-presets.config.json"  # legacy fallback


def load_dod_presets(agent_meta_root: Path) -> dict:
    """Load dod-presets.config.yaml (or .json fallback) from agent-meta root."""
    data, _ = _load_yaml_or_json(
        agent_meta_root / DOD_PRESETS_CONFIG_YAML,
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
    preset_name = config.get("dod-preset", "full")
    preset_values = presets.get(preset_name, {})

    # Fallback to "full" preset when named preset not found
    if preset_name not in presets:
        if preset_name != "full":
            print(f"  !  Unknown dod-preset '{preset_name}' — falling back to 'full'",
                  file=sys.stderr)
        preset_values = presets.get("full", {})

    dod_overrides = config.get("dod", {})

    # All known DoD keys — sourced from the full preset as authoritative key set
    full_preset = presets.get("full", {
        "req-traceability": True,
        "tests-required": True,
        "codebase-overview": True,
        "security-audit": False,
    })

    resolved = {}
    for key, default_val in full_preset.items():
        if key in dod_overrides:
            resolved[key] = dod_overrides[key]
        elif key in preset_values:
            resolved[key] = preset_values[key]
        else:
            resolved[key] = default_val
    return resolved
