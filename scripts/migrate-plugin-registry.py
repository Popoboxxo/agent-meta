"""One-time migration: rewrite a project.yaml's legacy `mcp-servers:` list and
`external-tools:` dict into the unified `plugins:` block. Order of the mcp
entries is preserved so the resolved active-server sequence (and thus
.mcp.json) stays byte-identical. Wegwerf-Werkzeug — delete after all consumer
projects migrated.

Usage: python3 scripts/migrate-plugin-registry.py .meta-config/project.yaml
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml


def build_plugins_block(config: dict) -> dict:
    """Legacy activation -> {plugin_id: {'enabled': bool}} preserving mcp order."""
    block: dict = {}
    for name in config.get("mcp-servers", []) or []:
        block[name] = {"enabled": True}
    tools = config.get("external-tools", {})
    if isinstance(tools, list):
        for name in tools:
            block[name] = {"enabled": True}
    elif isinstance(tools, dict):
        for name, val in tools.items():
            block[name] = {"enabled": bool((val or {}).get("enabled", True))}
    return block


def migrate_file(path: Path) -> bool:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if "mcp-servers" not in data and "external-tools" not in data:
        return False
    data["plugins"] = build_plugins_block(data)
    data.pop("mcp-servers", None)
    data.pop("external-tools", None)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return True


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".meta-config/project.yaml")
    print("migrated" if migrate_file(target) else "nothing to migrate", "-", target)
