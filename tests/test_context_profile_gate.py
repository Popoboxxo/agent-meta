"""Tests for scripts/lib/context_profile_gate.py (2a.5, IC-36, AC-86 profile part).

The gate reads eval evidence only from the agent-meta root
(``tests/routing-llm-eval/roles/{baseline,runs}``) and evaluates it with
``eval_gate.evaluate_gate``. Without a passing ``compact`` evaluation a sync
with ``context-profile: compact`` logs the INFO ``context-profile.unverified``;
a full/default profile never logs it.
"""
import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from lib.context_profile import ResolvedContextProfile  # noqa: E402
from lib.context_profile_gate import (  # noqa: E402
    context_profile_gate_state,
    context_profile_info_lines,
)
from lib.log import SyncLog  # noqa: E402
from lib.sync_pipeline import _sync_stage_context_checks  # noqa: E402

_ROLES = Path("tests") / "routing-llm-eval" / "roles"

_METRICS = {
    "top1_accuracy": 90.0,
    "collision_accuracy": 90.0,
    "ambiguity_clarify_rate": 90.0,
    "wrong_pipeline_rate": 5.0,
    "over_clarify_rate": 5.0,
    "escalation_correct": 90.0,
    "inactive_role_dispatch": 0.0,
    "language_delta": 0.0,
}

_CLASSES = ("model-a", "model-b")


def _write(root: Path, subdir: str, name: str, doc: dict) -> None:
    path = root / _ROLES / subdir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc), encoding="utf-8")


def _baseline_doc(profile: str, status: str = "evidenced") -> dict:
    return {
        "kind": "role-routing-baseline",
        "profile": profile,
        "corpus_hash": "a" * 64,
        "model_ids": {name: "provider/" + name for name in _CLASSES},
        "model_classes": {
            name: {metric: [value, value, value] for metric, value in _METRICS.items()}
            for name in _CLASSES
        },
        "evidence": {"status": status, "reasons": []},
    }


def _candidate_doc(profile: str, top1: float = 90.0) -> dict:
    classes = {name: dict(_METRICS) for name in _CLASSES}
    for name in _CLASSES:
        classes[name]["top1_accuracy"] = top1
    return {
        "kind": "role-routing-baseline",
        "profile": profile,
        "corpus_hash": "a" * 64,
        "model_ids": {name: "provider/" + name for name in _CLASSES},
        "model_classes": classes,
        "evidence": {"status": "evidenced", "reasons": []},
    }


def _resolved(provider: str, profile: str) -> ResolvedContextProfile:
    return ResolvedContextProfile(
        provider=provider,
        profile=profile,
        context_file_mode=profile,
        rules_preset="default",
        sources={
            "profile": "profile" if profile == "compact" else "default",
            "context_file_mode": "profile" if profile == "compact" else "default",
            "rules_preset": "default",
        },
    )


def test_gate_not_evidenced_without_evidence(tmp_path):
    assert context_profile_gate_state(tmp_path) == "not-evidenced"


def test_gate_evidenced_with_passing_compact_candidate(tmp_path):
    _write(tmp_path, "baseline", "2026-10-17-model-full.json", _baseline_doc("full"))
    _write(tmp_path, "baseline", "2026-10-17-model-compact.json",
           _candidate_doc("compact"))
    assert context_profile_gate_state(tmp_path) == "evidenced"


def test_gate_not_evidenced_without_full_baseline(tmp_path):
    _write(tmp_path, "baseline", "2026-10-17-model-compact.json",
           _candidate_doc("compact"))
    assert context_profile_gate_state(tmp_path) == "not-evidenced"


def test_gate_not_evidenced_when_candidate_degrades(tmp_path):
    _write(tmp_path, "baseline", "2026-10-17-model-full.json", _baseline_doc("full"))
    _write(tmp_path, "baseline", "2026-10-17-model-compact.json",
           _candidate_doc("compact", top1=80.0))
    assert context_profile_gate_state(tmp_path) == "not-evidenced"


def test_gate_ignores_skip_records(tmp_path):
    _write(tmp_path, "runs", "2026-10-17-qg1-model.json",
           {"status": "SKIPPED-BY-USER", "date": "2026-10-17",
            "estimate": {}, "reason": "declined"})
    assert context_profile_gate_state(tmp_path) == "not-evidenced"


def test_info_line_per_compact_provider_without_evidence(tmp_path):
    lines = context_profile_info_lines(
        [_resolved("Claude", "compact"), _resolved("Gemini", "full")], tmp_path)
    assert len(lines) == 1
    assert "Claude" in lines[0]
    assert "context-profile.unverified" in lines[0]


def test_no_info_when_evidenced(tmp_path):
    _write(tmp_path, "baseline", "2026-10-17-model-full.json", _baseline_doc("full"))
    _write(tmp_path, "baseline", "2026-10-17-model-compact.json",
           _candidate_doc("compact"))
    assert context_profile_info_lines([_resolved("Claude", "compact")], tmp_path) == []


def test_no_info_without_opt_in(tmp_path):
    assert context_profile_info_lines(
        [_resolved("Claude", "full"), _resolved("Gemini", "full")], tmp_path) == []


def test_drain_reaches_sync_log(tmp_path, monkeypatch):
    import lib.context_profile_gate as gate

    monkeypatch.setattr(gate, "context_profile_gate_state",
                        lambda root: "not-evidenced")
    log = SyncLog()
    _sync_stage_context_checks(_ROOT, tmp_path, {"context-profile": "compact"},
                               None, log)
    assert any("context-profile.unverified" in i for i in log.infos)
    assert not any("context-profile.unverified" in w for w in log.warnings)
