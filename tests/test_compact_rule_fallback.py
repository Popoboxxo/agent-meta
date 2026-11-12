"""#1183: compact profile never drops a rule silently (warning + skill pointer line)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from lib.config import build_variables  # noqa: E402
from lib.context import _build_managed_block, rule_reachable_in_compact  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.providers import load_providers_config  # noqa: E402
from test_compact_rule_channels import _PROVIDER, _fixture_config  # noqa: E402


def test_reachable_matrix():
    kw = dict(gate_stems=frozenset({"g"}), skill_stems=frozenset({"s"}))
    assert rule_reachable_in_compact("g", native_rules=False, **kw)
    assert rule_reachable_in_compact("s", native_rules=False, **kw)
    assert rule_reachable_in_compact("x", native_rules=True, **kw)
    assert not rule_reachable_in_compact("x", native_rules=False, **kw)


def _render(tmp_path, monkeypatch, channels=None):
    if channels is not None:
        import lib.providers as providers

        real = providers.load_provider_capabilities

        def _caps(root):
            caps = {n: dict(e or {}) for n, e in real(root).items()}
            caps[_PROVIDER]["rules_read_channels"] = channels
            return caps

        monkeypatch.setattr(providers, "load_provider_capabilities", _caps)
    config = _fixture_config(profile="compact", preset="default")
    variables, _w = build_variables(config, ROOT, tmp_path)
    log = SyncLog()
    block = _build_managed_block(
        ROOT, config, variables, log, provider=_PROVIDER,
        provider_config=load_providers_config(ROOT), project_root=tmp_path,
        active_set=frozenset(),
    )
    return block, [w for w in log.warnings if "context.rule-compacted-away" in w]


def test_without_skills_channel_warns_per_rule_once(tmp_path, monkeypatch):
    block, warns = _render(tmp_path, monkeypatch, channels=["embedded"])
    assert warns
    assert len(warns) == len({w for w in warns})
    assert "Weitere Regeln als Skills" not in block


def test_with_skills_channel_names_skills_in_one_pointer_line(tmp_path, monkeypatch):
    block, warns = _render(tmp_path, monkeypatch)
    lines = [ln for ln in block.splitlines() if ln.startswith("Weitere Regeln als Skills:")]
    assert len(lines) == 1
    stems = [s.strip() for s in lines[0].split(":", 1)[1].split(",")]
    assert stems == sorted(stems) and stems
    assert not any(f"rule {s}" in w for s in stems for w in warns)
