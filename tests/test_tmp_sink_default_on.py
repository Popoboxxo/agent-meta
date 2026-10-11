"""AC-92 (IC-15 Nr. 26): tmp-sink gitignore entry is ON without a block.

Run: python -m pytest tests/test_tmp_sink_default_on.py -q
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.gitignore import _tmp_sink_gitignore_entry, compute_base_gitignore_entries

_CLAUDE = {"Claude": {"has_dedicated_context_file": True}}


def _entries(cfg):
    return compute_base_gitignore_entries(["Claude"], _CLAUDE, {}, cfg)


def test_no_block_yields_default_entry():
    assert ".tmp/" in _entries(None)


def test_non_mapping_block_yields_default_entry():
    assert _tmp_sink_gitignore_entry("garbage") == ".tmp/"  # type: ignore[arg-type]
    assert _tmp_sink_gitignore_entry(None) == ".tmp/"


def test_custom_path_entry():
    cfg = {"enabled": True, "tmp-sink": {"enabled": True, "path": "scratch/out"}}
    assert "scratch/out/" in _entries(cfg)
    assert ".tmp/" not in _entries(cfg)


def test_gitignore_false_yields_no_entry():
    cfg = {"enabled": True, "tmp-sink": {"gitignore": False}}
    assert _tmp_sink_gitignore_entry(cfg) is None
    assert ".tmp/" not in _entries(cfg)


def test_sink_disabled_yields_no_entry():
    cfg = {"enabled": True, "tmp-sink": {"enabled": False}}
    assert _tmp_sink_gitignore_entry(cfg) is None
    assert ".tmp/" not in _entries(cfg)


def test_entry_computation_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _entries(None)
    assert list(tmp_path.iterdir()) == []
