"""IC-29 Phase 0: routing.keyword-overlap check and examples-language fallback log (AC-63)."""
import sys
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from lib.active_set import compute_active_set  # noqa: E402
from lib.consistency import active_set_refs as asr  # noqa: E402
from lib.consistency.report import Severity  # noqa: E402
from lib.delegation_table import _select_examples, get_routing_rules  # noqa: E402
from tests.test_routing_overlap import KNOWN_KEYWORD_OVERLAPS  # noqa: E402

_FIX = Path(__file__).resolve().parent / "fixtures" / "active-set"


def _active(name, all_gates=False):
    root = _FIX / name
    cfg = yaml.safe_load((root / ".meta-config" / "project.yaml").read_text(encoding="utf-8"))
    if all_gates:
        # The bare pall fixture leaves gated groups (SE, knowledge, developer
        # tiers) off; AC-63 needs every role active, so enable all gates in memory.
        known = sorted(compute_active_set(cfg, _ROOT, root).known_roles)
        cfg = dict(cfg, roles=known,
                   **{"systems-engineering": {"enabled": True},
                      "knowledge-engine": {"enabled": True}})
    return root, compute_active_set(cfg, _ROOT, root)


def _tokens(findings):
    return sorted(f.message.split("'")[1] for f in findings)


def test_all_roles_fixture_reports_all_nine_overlap_tokens():
    root, active = _active("pall", all_gates=True)
    assert KNOWN_KEYWORD_OVERLAPS and all(r in active.routable
                                          for rs in KNOWN_KEYWORD_OVERLAPS.values() for r in rs)
    findings = asr.check_keyword_overlap(root, ["Claude"], {}, active)
    assert all(f.check == "routing.keyword-overlap" and f.severity == Severity.INFO
               for f in findings)
    assert _tokens(findings) == sorted(KNOWN_KEYWORD_OVERLAPS)
    assert len(findings) == 9


def test_p10_reports_only_pairs_with_all_roles_active():
    root, active = _active("p10")
    findings = asr.check_keyword_overlap(root, ["Claude"], {}, active)
    expected = sorted(tok for tok, roles in KNOWN_KEYWORD_OVERLAPS.items()
                      if len(roles & active.routable) >= 2)
    assert _tokens(findings) == expected
    assert len(expected) < 9
    for f in findings:  # no inactive role may appear in the message
        assert not any(r in f.message for r in active.known_roles - active.roles
                       if r in KNOWN_KEYWORD_OVERLAPS[f.message.split("'")[1]])


def test_overlap_check_is_deterministic():
    root, active = _active("pall")
    a = asr.check_keyword_overlap(root, ["Claude"], {}, active)
    b = asr.check_keyword_overlap(root, ["Claude"], {}, active)
    assert [str(f) for f in a] == [str(f) for f in b]


def test_language_fallback_is_logged_not_rendered():
    examples = {"Deutsch": ["a"], "English": ["b"]}
    sink: list = []
    assert _select_examples(examples, "Francais", role="r1", info_sink=sink) == ["a"]
    assert len(sink) == 1
    assert "routing.examples-language-fallback" in sink[0] and "r1" in sink[0]
    # no fallback, no log; render result identical with and without a sink
    sink.clear()
    assert _select_examples(examples, "English", role="r1", info_sink=sink) == ["b"]
    assert _select_examples(["x"], "Francais", role="r1", info_sink=sink) == ["x"]
    assert sink == []
    assert _select_examples(examples, "Francais") == ["a"]


def test_get_routing_rules_threads_info_sink(monkeypatch):
    import lib.delegation_table as dt
    real = dt.load_roles_config

    def fake(root):
        cfg = real(root)
        cfg = dict(cfg)
        roles = dict(cfg["roles"])
        dev = dict(roles["developer"])
        dev["routing_patterns"] = {"keywords": ["k"], "examples": {"Deutsch": ["a"]}}
        roles["developer"] = dev
        cfg["roles"] = roles
        return cfg

    monkeypatch.setattr(dt, "load_roles_config", fake)
    sink: list = []
    rules = get_routing_rules(_ROOT, {}, {}, language="English", info_sink=sink)
    assert any("routing.examples-language-fallback" in m and "developer" in m for m in sink)
    assert [r for r in rules["rules"] if r["agent"] == "developer"][0]["examples"] == ["a"]
