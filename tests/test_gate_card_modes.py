"""#1182: gate card tolerates modes whose rule lacks the gate heading."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.context import build_gate_card
from lib.context_profile import context_profile_override_warnings
from lib.io import SyncError
from lib.log import SyncLog

_FLAGS = {
    "advisory": ("true", "false", "false"),
    "main-chat": ("false", "false", "true"),
}


def _vars(mode):
    adv, strict, main = _FLAGS[mode]
    return {
        "ORCH_MODE_ADVISORY": adv,
        "ORCH_MODE_STRICT": strict,
        "ORCH_MODE_MAIN_CHAT": main,
    }


@pytest.mark.parametrize("mode", ["advisory", "main-chat"])
def test_missing_heading_warns_and_skips(mode):
    log = SyncLog()
    config = {"platforms": [], "orchestrator": {"mode": mode}}
    card = build_gate_card(ROOT, config, _vars(mode), log)
    hits = [w for w in log.warnings if "CRITICAL GATE" in w and mode in w]
    assert len(hits) == 1
    assert "Git Delegation" in card


def test_missing_rule_still_raises(monkeypatch):
    from lib import context

    monkeypatch.setattr(context, "_load_gate_card_sections", lambda _r: ["no-such-rule#X"])
    with pytest.raises(SyncError, match="context.gate-card: rule"):
        build_gate_card(ROOT, {"platforms": []}, _vars("advisory"), SyncLog())


def test_override_warning():
    cfg = {"context-profile": "compact", "context_file": {"mode": "full"}}
    out = context_profile_override_warnings(cfg, ["Opencode"], {"Opencode": "AGENTS.md"})
    assert out == [
        "context-profile.mode-override: 'AGENTS.md' renders context_file.mode=full "
        "while context-profile=compact is active; the compact render (gate card, "
        "roster, reference skills) still applies"
    ]
    assert context_profile_override_warnings({"context-profile": "compact"}, ["Opencode"]) == []


def test_e2e_compact_advisory(tmp_path):
    cfg = tmp_path / ".meta-config" / "project.yaml"
    cfg.parent.mkdir()
    cfg.write_text(
        'agent-meta-version: "2.0.0-beta.8"\nai-providers:\n- Opencode\n'
        "dod-preset: rapid-prototyping\ncontext-profile: compact\n"
        "orchestrator:\n  mode: advisory\n"
        "variables:\n  PROJECT_NAME: t\n  PROJECT_PREFIX: t\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync.py"), "--config", str(cfg), "--init"],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=300,
    )
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    assert (tmp_path / "AGENTS.md").exists()
