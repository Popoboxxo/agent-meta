"""Dispatch-table tests (#1253): unknown format keys fail with the valid-key list."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib import isolation  # noqa: E402
from lib.log import SyncLog  # noqa: E402


def test_unknown_isolation_mechanism_exits_with_key_list(tmp_path: Path):
    cfg = {
        "A": {"isolation-dirs": [".a/"], "isolation-mechanism": "claude-settings-deny"},
        "B": {"isolation-dirs": [".b/"], "isolation-mechanism": "bogus-mechanism"},
    }
    log = SyncLog()
    with pytest.raises(SystemExit) as exc:
        isolation.sync_provider_isolation(tmp_path, ["A", "B"], cfg, log, dry_run=True)
    assert exc.value.code == 1
    text = " ".join(log.errors)
    assert "bogus-mechanism" in text
    for key in isolation._ISOLATION_MECHANISM_HANDLERS:
        assert key in text


def test_unknown_mcp_format_reports_valid_key_list(tmp_path: Path):
    from lib import mcp_provider_config as mpc

    log = SyncLog()
    path = tmp_path / "c.json"
    mpc._write_provider_config(path, {}, "mystery-format", log, dry_run=False, allow_secrets=True)
    text = " ".join(log.warnings)
    assert "mystery-format" in text and not path.exists()
    for key in mpc._FORMAT_WRITERS:
        assert key in text


def test_no_fmt_comparison_chain_in_mcp_modules():
    import re

    lib = Path(__file__).resolve().parent.parent / "scripts" / "lib"
    pat = re.compile(r"^\s*(?:if|elif)\b[^#\n]*\bfmt\s*(==|in)\b", re.M)
    for name in ("mcp_provider_config.py", "mcp.py", "opencode_v2_config.py", "sync_pipeline.py"):
        assert not pat.findall((lib / name).read_text(encoding="utf-8")), name
