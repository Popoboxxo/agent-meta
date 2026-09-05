# tests/test_external_tools_drift_catalog_ref.py
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.external_tools_drift import _generate_drift_content  # noqa: E402


def test_drift_header_names_catalog_not_legacy_file():
    content = _generate_drift_content([{"path": ".claude/skills/x", "kind": "skill", "tool": None}])
    assert "config/plugin-catalog.yaml" in content
    assert "config/external-tools-registry.yaml" not in content
