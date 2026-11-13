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


def _render(tmp_path, monkeypatch, channels=None, soft_cap=None):
    if channels is not None or soft_cap is not None:
        import lib.providers as providers

        real = providers.load_provider_capabilities

        def _caps(root):
            caps = {n: dict(e or {}) for n, e in real(root).items()}
            if channels is not None:
                caps[_PROVIDER]["rules_read_channels"] = channels
            if soft_cap is not None:
                caps[_PROVIDER]["context_soft_cap_chars"] = soft_cap
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


def test_warning_wording_no_channel(tmp_path, monkeypatch):
    _b, no_chan = _render(tmp_path, monkeypatch, channels=["embedded"])
    assert no_chan and all(w.endswith("without a skills channel") for w in no_chan)


def test_warning_wording_channel_present_but_no_skill(tmp_path, monkeypatch):
    _b, with_chan = _render(tmp_path, monkeypatch)
    assert with_chan
    assert all("skills channel" not in w and w.endswith("and no skill exists for it") for w in with_chan)


def _full_vs_compact(tmp_path, monkeypatch):
    """(rules absent from compact, pointer stems, warnings) judged by each rule's H1 line."""
    from lib.rules import collect_rule_sources

    full, _w = _render_profile(tmp_path, monkeypatch, "full")
    compact, warns = _render_profile(tmp_path, monkeypatch, "compact")
    config = _fixture_config(profile="full", preset="default")
    missing = []
    for src, out in collect_rule_sources(ROOT, config.get("platforms", []), config=config):
        h1 = next((ln for ln in src.read_text(encoding="utf-8").splitlines() if ln.startswith("# ")), None)
        if h1 and h1 in full and h1 not in compact:
            missing.append(Path(out).stem)
    ptr = [ln for ln in compact.splitlines() if ln.startswith("Weitere Regeln als Skills:")]
    pointed = {s.strip() for s in ptr[0].split(":", 1)[1].split(",")} if ptr else set()
    return missing, pointed, warns


def _render_profile(tmp_path, monkeypatch, profile):
    config = _fixture_config(profile=profile, preset="default")
    variables, _w = build_variables(config, ROOT, tmp_path)
    log = SyncLog()
    block = _build_managed_block(
        ROOT, config, variables, log, provider=_PROVIDER,
        provider_config=load_providers_config(ROOT), project_root=tmp_path,
        active_set=frozenset(),
    )
    return block, [w for w in log.warnings if "context.rule-compacted-away" in w]


def test_every_rule_missing_in_compact_is_pointed_or_warned_once(tmp_path, monkeypatch):
    # AC-1183-1
    missing, pointed, warns = _full_vs_compact(tmp_path, monkeypatch)
    assert missing
    for stem in missing:
        n = sum(f"rule '{stem}' " in w for w in warns)
        assert (stem in pointed) != (n == 1), (stem, stem in pointed, n)
        assert n <= 1


def test_no_reference_skill_without_pointer(tmp_path, monkeypatch):
    # AC-1183-2: every skill the writer would emit is named in the pointer line.
    from lib.context import compact_reference_skill_rules

    _m, pointed, _w = _full_vs_compact(tmp_path, monkeypatch)
    config = _fixture_config(profile="compact", preset="default")
    variables, _w = build_variables(config, ROOT, tmp_path)
    written = {s for s, *_ in compact_reference_skill_rules(
        ROOT, config, variables, SyncLog(), [_PROVIDER])}
    assert written and written <= pointed


def test_soft_cap_overflow_warns_once_and_removes_no_rule(tmp_path, monkeypatch):
    # AC-1183-5: exceeding the soft cap only warns; the render is not trimmed to fit.
    from lib.consistency import context_budget as cb

    base_block, base_warns = _render(tmp_path, monkeypatch)
    cap = len(base_block) - 1
    block, warns = _render(tmp_path, monkeypatch, soft_cap=cap)
    assert (block, warns) == (base_block, base_warns)

    (tmp_path / "AGENTS.md").write_text(block, encoding="utf-8")
    caps = {_PROVIDER: {"context_file": "AGENTS.md", "context_soft_cap_chars": cap}}
    findings = cb.check_over_soft_cap(tmp_path, [_PROVIDER], caps, None)
    assert [f.check for f in findings] == ["context.over-soft-cap"]
