"""Call-site gate for the opencode v2 writers (#1254, spec A3).

Gate = owns surface OR state file present (Q2); no provider-name comparison.
Run: python3 -m pytest tests/test_opencode_gate_call_site.py -q
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from lib import isolation  # noqa: E402
from lib.opencode_v2_config import (  # noqa: E402
    opencode_writers_reachable,
    owns_opencode_surface,
)

_OWNER = {"P": {"mcp-config": {
    "surface-formats": {"v2": "opencode-json-v2"},
    "committed-file": "opencode.json",
}}}
_OTHER = {"Q": {"mcp-config": {"format": "json"}}}


def test_owner_reachable_without_state(tmp_path):
    assert owns_opencode_surface(_OWNER, "P")
    assert opencode_writers_reachable(tmp_path, _OWNER, "P")


def test_non_owner_without_state_not_reachable(tmp_path):
    assert not opencode_writers_reachable(tmp_path, _OTHER, "Q")


def test_non_owner_with_state_reachable(tmp_path):
    state = tmp_path / isolation._OPENCODE_STATE_FILE
    state.parent.mkdir(parents=True)
    state.write_text("{}")
    assert opencode_writers_reachable(tmp_path, _OTHER, "Q")


def test_no_provider_name_comparison_in_pipeline():
    src = (ROOT / "scripts/lib/sync_pipeline.py").read_text()
    assert not re.search(r"\bprovider\s*(==|!=)\s*[\"']", src)


def test_pipeline_gates_both_writers():
    src = (ROOT / "scripts/lib/sync_pipeline.py").read_text()
    assert src.count("opencode_writers_reachable(") == 1
    assert src.count("if _opencode_v2_reachable:") == 2
