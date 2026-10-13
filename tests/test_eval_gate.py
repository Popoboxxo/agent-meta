"""Tests for scripts/lib/eval_gate.py (IC-36, AC-86)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "lib"))

import eval_gate as eg  # noqa: E402

REPORT = {
    "claude": {"always-loaded": {"tokens_est": 1000}},
    "pricing": {
        "m1": {"input_per_mtok": 3.0, "output_per_mtok": 15.0},
        "_source": "test",
        "_date": "2026-10-01",
    },
}


def _est():
    return eg.estimate_cost(10, ["m1"], 3, REPORT, today="2026-10-13")


class _Mock:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return "ok"


def test_estimate_values_and_determinism():
    e = _est()
    assert e["calls"] == 30
    assert e["input_tokens"] == 30 * (1000 + 150)
    assert e["output_tokens"] == 6000
    assert e["cost_usd"] == round((30 * 1150 * 3 + 6000 * 15) / 1e6, 6)
    assert not e["unverified"]
    assert e == _est()


def test_estimate_without_prices_is_unverified():
    e = eg.estimate_cost(2, ["x"], 1, {"tokens_est": 50})
    assert e["cost_usd"] is None and e["unverified"]


def test_estimate_adds_orchestrator_and_takes_max_provider():
    rep = {
        "a": {"always-loaded": {"tokens_est": 100}, "orchestrator": {"tokens_est": 50}},
        "b": {"always-loaded": {"tokens_est": 120}},
    }
    e = eg.estimate_cost(1, ["x"], 1, rep, task_tokens_per_case=10)
    assert e["input_tokens"] == 160


def test_estimate_zero_or_missing_tokens_unverified():
    for rep in ({"tokens_est": 0}, {}, {"a": {"always-loaded": {}}}):
        rep = dict(rep, pricing=REPORT["pricing"])
        e = eg.estimate_cost(1, ["m1"], 1, rep, today="2026-10-13")
        assert e["unverified"] and e["cost_usd"] is None


def test_estimate_price_date_staleness():
    def un(d, **kw):
        rep = dict(REPORT, pricing=dict(REPORT["pricing"], _date=d))
        return eg.estimate_cost(1, ["m1"], 1, rep, today="2026-10-13", **kw)["unverified"]
    assert not un("2026-10-13") and not un("2026-07-15")
    assert un("2026-07-14")  # 91 days
    assert not un("2026-07-14", max_age_days=100)
    assert un("garbage") and un("2027-01-01")  # invalid / future


def test_no_approval_zero_calls_and_prints_estimate():
    mock, out = _Mock(), []
    r = eg.run_with_approval(_est(), None, [mock, mock], Path("unused.json"), out.append)
    assert mock.calls == 0
    assert r["status"] == eg.AWAITING_APPROVAL
    assert out and "30 calls" in out[0] and "USD" in out[0]


def test_rejection_writes_skip_file(tmp_path):
    mock = _Mock()
    p = tmp_path / "runs" / "2026-10-13-x.json"
    r = eg.run_with_approval(_est(), "no", [mock], p, lambda t: None, "too expensive", today="2026-10-13")
    assert mock.calls == 0 and r["status"] == eg.SKIPPED_BY_USER
    rec = json.loads(p.read_text(encoding="utf-8"))
    assert rec["status"] == "SKIPPED-BY-USER"
    assert rec["date"] == "2026-10-13"
    assert rec["reason"] == "too expensive"
    assert rec["estimate"]["calls"] == 30


def test_approval_runs_callbacks(tmp_path):
    mock = _Mock()
    r = eg.run_with_approval(_est(), " YES ", [mock, mock], tmp_path / "s.json", lambda t: None)
    assert mock.calls == 2 and r["status"] == eg.APPROVED
    assert not (tmp_path / "s.json").exists()


def test_request_approval_tokens():
    assert eg.request_approval({}, "yes") and eg.request_approval({}, " Ja ")
    assert not eg.request_approval({}, None)
    for bad in ("", "  ", "maybe", "y", "j", "yes please"):
        assert not eg.request_approval({}, bad)


def test_blank_input_is_awaiting_without_skip_record(tmp_path):
    mock, p = _Mock(), tmp_path / "s.json"
    for blank in ("", "   "):
        r = eg.run_with_approval(_est(), blank, [mock], p, lambda t: None)
        assert r["status"] == eg.AWAITING_APPROVAL
    assert mock.calls == 0 and not p.exists()


def test_y_is_rejection(tmp_path):
    mock, p = _Mock(), tmp_path / "s.json"
    r = eg.run_with_approval(_est(), "y", [mock], p, lambda t: None)
    assert r["status"] == eg.SKIPPED_BY_USER and mock.calls == 0 and p.exists()


def test_approval_bound_to_estimate_hash(tmp_path):
    mock, p = _Mock(), tmp_path / "s.json"
    good = eg.estimate_hash(_est())
    r = eg.run_with_approval(_est(), "yes", [mock], p, lambda t: None, approved_estimate_hash="bad")
    assert r["status"] == eg.AWAITING_APPROVAL and mock.calls == 0
    r = eg.run_with_approval(_est(), "yes", [mock], p, lambda t: None, approved_estimate_hash=good)
    assert r["status"] == eg.APPROVED and mock.calls == 1


def test_skip_record_path():
    p = eg.skip_record_path(Path("/r"), "2026-10-13", "qg1")
    assert p == Path("/r/tests/routing-llm-eval/roles/runs/2026-10-13-qg1.json")


def _baseline(metric="top1_accuracy", runs=(90.0, 90.0, 90.0), classes=("a", "b")):
    return {
        "corpus_hash": "h",
        "model_ids": {c: c + "-1" for c in classes},
        "model_classes": {c: {metric: list(runs)} for c in classes},
    }


def _cand(value, metric="top1_accuracy", classes=("a", "b")):
    return {
        "corpus_hash": "h",
        "model_ids": {c: c + "-1" for c in classes},
        "model_classes": {c: {metric: value} for c in classes},
    }


def test_thin_baseline_not_evidenced():
    assert eg.evaluate_gate(_baseline(classes=("a",)), _cand(95, classes=("a",))) == eg.NOT_EVIDENCED
    assert eg.evaluate_gate(_baseline(runs=(90, 90)), _cand(95)) == eg.NOT_EVIDENCED
    assert eg.evaluate_gate({}, _cand(95)) == eg.NOT_EVIDENCED


def test_skipped_candidate_not_evidenced():
    assert eg.evaluate_gate(_baseline(), {"status": "SKIPPED-BY-USER"}) == eg.NOT_EVIDENCED


def test_missing_candidate_and_corpus_mismatch():
    c = _cand(90)
    del c["model_classes"]["b"]
    assert eg.evaluate_gate(_baseline(), c) == eg.NOT_EVIDENCED
    b = _baseline()
    b["corpus_hash"] = "x"
    c = _cand(90)
    c["corpus_hash"] = "y"
    assert eg.evaluate_gate(b, c) == eg.NOT_EVIDENCED


def test_missing_corpus_hash_either_side():
    assert eg.evaluate_gate(_baseline(), _cand(99)) == eg.PASSED
    for side in ("b", "c"):
        b, c = _baseline(), _cand(99)
        del (b if side == "b" else c)["corpus_hash"]
        assert eg.evaluate_gate(b, c) == eg.NOT_EVIDENCED
    b, c = _baseline(), _cand(99)
    del b["corpus_hash"], c["corpus_hash"]
    assert eg.evaluate_gate(b, c) == eg.NOT_EVIDENCED


def test_model_ids_mismatch_or_missing():
    c = _cand(99)
    c["model_ids"]["a"] = "a-2"
    assert eg.evaluate_gate(_baseline(), c) == eg.NOT_EVIDENCED
    c = _cand(99)
    del c["model_ids"]
    assert eg.evaluate_gate(_baseline(), c) == eg.NOT_EVIDENCED


def test_invalid_values_not_evidenced_no_exception():
    nan = float("nan")
    for bad in (None, nan, 101, -1, True, "x"):
        assert eg.evaluate_gate(_baseline(), _cand(bad)) == eg.NOT_EVIDENCED
    assert eg.evaluate_gate(_baseline(runs=(90, nan, 90)), _cand(90)) == eg.NOT_EVIDENCED
    assert eg.evaluate_gate(_baseline(runs=(90, None, 90)), _cand(90)) == eg.NOT_EVIDENCED
    assert eg.evaluate_gate(_baseline(runs=(90, 90, 150)), _cand(90)) == eg.NOT_EVIDENCED


def test_failed_dominates_not_evidenced():
    c = {
        "corpus_hash": "h",
        "model_ids": _cand(1)["model_ids"],
        "model_classes": {"a": {"top1_accuracy": 10}, "b": {"top1_accuracy": None}},
    }
    assert eg.evaluate_gate(_baseline(), c) == eg.FAILED
    c["model_classes"]["a"]["top1_accuracy"] = 95
    assert eg.evaluate_gate(_baseline(), c) == eg.NOT_EVIDENCED


def test_higher_better_directions():
    for m in ("top1_accuracy", "collision_accuracy", "ambiguity_clarify_rate", "escalation_correct"):
        b = _baseline(m)
        assert eg.evaluate_gate(b, _cand(95, m)) == eg.PASSED  # better
        assert eg.evaluate_gate(b, _cand(89.5, m)) == eg.PASSED  # within tau
        assert eg.evaluate_gate(b, _cand(85, m)) == eg.FAILED  # worse


def test_lower_better_directions():
    for m in ("wrong_pipeline_rate", "over_clarify_rate"):
        b = _baseline(m, runs=(10.0, 10.0, 10.0))
        assert eg.evaluate_gate(b, _cand(5, m)) == eg.PASSED
        assert eg.evaluate_gate(b, _cand(10.5, m)) == eg.PASSED
        assert eg.evaluate_gate(b, _cand(15, m)) == eg.FAILED


def test_inactive_dispatch_absolute_zero():
    b = _baseline("inactive_role_dispatch", runs=(0.0, 0.0, 0.0))
    assert eg.evaluate_gate(b, _cand(0, "inactive_role_dispatch")) == eg.PASSED
    assert eg.evaluate_gate(b, _cand(0.5, "inactive_role_dispatch")) == eg.FAILED


def test_language_delta_uses_magnitude():
    b = _baseline("language_delta", runs=(-3.0, -3.0, -3.0))
    assert eg.evaluate_gate(b, _cand(3.5, "language_delta")) == eg.PASSED
    assert eg.evaluate_gate(b, _cand(-2.0, "language_delta")) == eg.PASSED
    assert eg.evaluate_gate(b, _cand(-5.0, "language_delta")) == eg.FAILED


def test_k_boundaries():
    # runs 88, 90, 92 -> sample sigma 2.0; k=2 -> tau 4.0; k=0.1 -> tau floor 1.0
    b = _baseline(runs=(88.0, 90.0, 92.0))
    assert eg.evaluate_gate(b, _cand(86.0), k=2.0) == eg.PASSED  # exactly mean - tau
    assert eg.evaluate_gate(b, _cand(85.9), k=2.0) == eg.FAILED
    assert eg.evaluate_gate(b, _cand(89.0), k=0.1) == eg.PASSED  # floor 1 pp
    assert eg.evaluate_gate(b, _cand(88.9), k=0.1) == eg.FAILED
    assert eg.evaluate_gate(b, _cand(86.0), k=3.0) == eg.PASSED  # larger k widens


def test_one_failing_class_fails_and_determinism():
    b = _baseline()
    c = _cand(95)
    c["model_classes"]["b"]["top1_accuracy"] = 70
    assert eg.evaluate_gate(b, c) == eg.FAILED
    assert eg.evaluate_gate(b, c) == eg.evaluate_gate(b, c)


def test_unknown_metric_raises():
    try:
        eg.evaluate_gate(_baseline("bogus"), _cand(1, "bogus"))
    except ValueError:
        return
    raise AssertionError("expected ValueError")
