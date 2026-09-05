from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCOUT = (REPO_ROOT / "agents" / "1-generic" / "agent-meta-scout.md").read_text(encoding="utf-8")


def test_scout_references_plugin_catalog():
    assert "config/plugin-catalog.yaml" in SCOUT


def test_scout_still_read_only():
    # role must not gain write tools — Layer 4 is read-only recommendation
    assert "- Read" in SCOUT
    assert "- Write" not in SCOUT and "- Edit" not in SCOUT
