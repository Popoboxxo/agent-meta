"""Baseline/skip artifact schema for the role-routing eval (IC-13, IC-36).

Pure offline checks: no LLM call, no network. The runner is exercised through
its pure aggregation helpers; repository artifacts are validated only when
present (a real baseline requires an approved paid run). The skip record is
produced with the shared ``eval_gate.write_skip_record`` so its schema cannot
drift from the gate.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

import pytest
import yaml

from scripts import gen_role_routing_eval_catalog as gen
from scripts import run_role_routing_eval as runner
from scripts.lib import eval_gate as eg

REPO_ROOT = Path(__file__).resolve().parents[1]
ROLES_DIR = REPO_ROOT / "tests" / "routing-llm-eval" / "roles"
BASELINE_DIR = ROLES_DIR / "baseline"
RUNS_DIR = ROLES_DIR / "runs"

CASES = [
    {
        "id": "c-keyword",
        "role": "developer",
        "category": "keyword",
        "lang": "de",
        "task": "Bitte übernimm: Bugfix.",
        "expected": {"target": "developer", "tier_escalation": False},
    },
    {
        "id": "c-collision",
        "role": "developer",
        "category": "collision",
        "lang": "de",
        "task": "Fix the bug. Stichwort: Bugfix.",
        "overlap_token": "bugfix",
        "expected": {"target": "developer", "tier_escalation": False},
    },
    {
        "id": "c-ambiguous",
        "role": "orchestrator",
        "category": "ambiguous",
        "lang": "de",
        "task": "Kümmere dich um: bugfix.",
        "overlap_token": "bugfix",
        "expected": {"target": "ASK", "tier_escalation": False},
    },
    {
        "id": "c-pair-de",
        "role": "developer",
        "category": "paraphrase",
        "lang": "de",
        "pair_id": "c-pair",
        "task": "Baue die Exportfunktion ein.",
        "expected": {"target": "developer", "tier_escalation": False},
    },
    {
        "id": "c-pair-en",
        "role": "developer",
        "category": "paraphrase",
        "lang": "en",
        "pair_id": "c-pair",
        "task": "Add the export function.",
        "expected": {"target": "developer", "tier_escalation": False},
    },
]


def _pred(target: str, tier: bool = False) -> dict:
    return {"target": target, "tier_escalation": tier}


def _all_correct() -> dict:
    return {
        case["id"]: _pred(case["expected"]["target"], case["expected"]["tier_escalation"])
        for case in CASES
    }


def _prediction_sets() -> list:
    """Three runs with deliberately different outcomes (sigma > 0)."""
    first = _all_correct()
    second = _all_correct()
    second["c-collision"] = _pred("ASK")
    second["c-pair-en"] = _pred("ASK")
    third = _all_correct()
    third["c-ambiguous"] = _pred("developer")
    third["c-pair-de"] = _pred("ASK")
    return [first, second, third]


def _parameters(repeat: int) -> dict:
    return {
        "repeat": repeat,
        "k": 2.0,
        "temperature": None,
        "timeout_s": 180.0,
        "provider_filter": ["opencode"],
        "task_tokens_per_case": eg.DEFAULT_TASK_TOKENS_PER_CASE,
        "output_tokens_per_call": eg.DEFAULT_OUTPUT_TOKENS_PER_CALL,
        "price_assumption": {
            "source": "config/pricing-overlay.yaml",
            "date": "2026-10-17",
        },
        "estimate_hash": "a" * 64,
        "estimate_unverified": False,
        "case_count": len(CASES),
        "calls": len(CASES) * 2 * repeat,
        "contract": "tests/routing-llm-eval/output-contract.md",
        "models": ["small-model", "balanced-model"],
    }


def _baseline(class_names: tuple = ("small", "balanced"), repeat: int = 3) -> dict:
    sets = _prediction_sets()[:repeat]
    class_runs = {}
    for name in class_names:
        class_runs[name] = [
            {
                "run": index + 1,
                "metrics": runner.compute_metrics(CASES, predictions),
                "errors": [],
            }
            for index, predictions in enumerate(sets)
        ]
    return runner.build_baseline(
        cases=CASES,
        class_runs=class_runs,
        model_ids={name: "{}-model".format(name) for name in class_names},
        providers={name: "opencode" for name in class_names},
        parameters=_parameters(repeat),
        corpus_hash=gen.corpus_hash(ROLES_DIR),
        profile="full",
        run_date="2026-10-17",
        label="+".join(class_names),
    )


def test_corpus_hash_is_deterministic_and_covers_generated_plus_manual():
    cases, corpus_hash = runner.load_catalog(ROLES_DIR)
    assert cases
    assert len(corpus_hash) == 64
    int(corpus_hash, 16)
    assert corpus_hash == gen.corpus_hash(ROLES_DIR)
    assert cases == gen._load_cases(ROLES_DIR / "catalog.generated.yaml") + gen._load_cases(
        ROLES_DIR / "catalog.manual.yaml"
    )


def test_baseline_schema_contains_runs_sigma_parameters_and_evidence():
    baseline = _baseline()
    assert baseline["schema_version"] == runner.SCHEMA_VERSION
    assert baseline["kind"] == "role-routing-baseline"
    assert baseline["profile"] == "full"
    assert baseline["date"] == "2026-10-17"
    assert baseline["corpus_hash"] == gen.corpus_hash(ROLES_DIR)
    assert baseline["model_ids"] == {
        "small": "small-model",
        "balanced": "balanced-model",
    }
    assert set(baseline["model_classes"]) == {"small", "balanced"}

    for model_class, metrics in baseline["model_classes"].items():
        assert set(metrics) == set(runner.REQUIRED_METRICS), model_class
        for metric, values in metrics.items():
            assert len(values) == 3, (model_class, metric)
            assert all(
                isinstance(value, (int, float)) and not isinstance(value, bool)
                for value in values
            ), (model_class, metric)
            low = -100 if metric == "language_delta" else 0
            assert all(low <= value <= 100 for value in values), (model_class, metric)
        assert "collision_accuracy" in metrics
        assert "language_delta" in metrics

    for model_class, metrics in baseline["sigma"].items():
        for metric, value in metrics.items():
            assert isinstance(value, float), (model_class, metric)
            assert value == pytest.approx(
                statistics.stdev(baseline["model_classes"][model_class][metric]),
                abs=1e-6,
            ), (model_class, metric)

    params = baseline["parameters"]
    assert params["repeat"] == 3
    assert params["k"] == 2.0
    assert params["price_assumption"]["date"] == "2026-10-17"
    assert params["estimate_hash"]
    assert params["case_count"] == len(CASES)
    assert params["calls"] == len(CASES) * 2 * 3
    assert baseline["runs"]
    assert {run["run"] for run in baseline["runs"]} == {1, 2, 3}
    assert baseline["evidence"]["status"] == "evidenced"
    assert baseline["evidence"]["reasons"] == []
    assert runner.validate_baseline(baseline) == []


def test_single_model_class_is_valid_but_not_evidenced():
    baseline = _baseline(class_names=("deepseek",))
    assert baseline["evidence"]["status"] == "not-evidenced"
    assert baseline["evidence"]["observed_model_classes"] == 1
    assert any("model class" in reason for reason in baseline["evidence"]["reasons"])
    assert runner.validate_baseline(baseline) == []


def test_too_few_runs_are_valid_but_not_evidenced():
    baseline = _baseline(repeat=2)
    assert baseline["evidence"]["status"] == "not-evidenced"
    assert any("run" in reason for reason in baseline["evidence"]["reasons"])
    assert runner.validate_baseline(baseline) == []


def test_language_delta_uses_only_paired_de_en_cases():
    predictions = _all_correct()
    de, en = gen.language_pairs({"cases": CASES})[0]
    predictions[en["id"]] = _pred("ASK")
    metrics = runner.compute_metrics(CASES, predictions)
    assert metrics["language_delta"] == 100.0


def test_collision_ambiguity_and_escalation_metrics():
    metrics = runner.compute_metrics(CASES, _all_correct())
    assert metrics["top1_accuracy"] == 100.0
    assert metrics["collision_accuracy"] == 100.0
    assert metrics["ambiguity_clarify_rate"] == 100.0
    assert metrics["wrong_pipeline_rate"] == 0.0
    assert metrics["over_clarify_rate"] == 0.0
    assert metrics["escalation_correct"] == 100.0
    assert metrics["inactive_role_dispatch"] == 0.0


def test_missing_prediction_counts_as_failure():
    predictions = _all_correct()
    del predictions["c-ambiguous"]
    metrics = runner.compute_metrics(CASES, predictions)
    assert metrics["top1_accuracy"] == 80.0
    assert metrics["ambiguity_clarify_rate"] == 0.0


def test_output_contract_parser_accepts_exact_json_and_embedded_json():
    assert runner.parse_prediction('{"target":"developer","tier_escalation":false}') == {
        "target": "developer",
        "tier_escalation": False,
    }
    assert runner.parse_prediction('Answer: {"target": "ASK"}')["target"] == "ASK"
    assert runner.parse_prediction(
        '```json\n{"target":"pipeline:bugfix"}\n```'
    )["target"] == "pipeline:bugfix"
    for bad in ("", "no json here", '{"target": 3}', '{"tier_escalation": true}'):
        with pytest.raises(ValueError):
            runner.parse_prediction(bad)


def test_skip_record_schema_is_written_by_eval_gate(tmp_path):
    estimate = eg.estimate_cost(
        5,
        ["m1"],
        3,
        {
            "tokens_est": 1000,
            "pricing": {
                "m1": {"input_per_mtok": 1.0, "output_per_mtok": 2.0},
                "_source": "test",
                "_date": "2026-10-17",
            },
        },
        today="2026-10-17",
    )
    path = tmp_path / "runs" / "2026-10-17-qg1-deepseek.json"
    eg.write_skip_record(path, estimate, "declined by user", today="2026-10-17")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["status"] == "SKIPPED-BY-USER"
    assert record["date"] == "2026-10-17"
    assert record["reason"] == "declined by user"
    assert record["estimate"] == estimate
    assert runner.validate_skip_record(record) == []


def test_estimate_only_path_never_calls_a_provider(monkeypatch, capsys):
    called = []

    def _forbidden(*args, **kwargs):
        called.append((args, kwargs))
        raise AssertionError("estimate-only must not call a provider")

    monkeypatch.setattr(runner, "call_provider", _forbidden)
    monkeypatch.setattr(
        runner, "build_context_report", lambda *args, **kwargs: {"tokens_est": 1000}
    )
    rc = runner.main(
        [
            "--estimate-only",
            "--provider",
            "opencode",
            "--model-class",
            "deepseek=opencode/opencode-go/deepseek-v4-flash",
            "--price-date",
            "2026-10-17",
            "--out-dir",
            str(ROLES_DIR),
        ]
    )
    assert rc == 0
    assert not called
    output = capsys.readouterr().out
    assert "Eval cost estimate" in output
    assert "calls" in output


def _synthetic_out_dir(tmp_path: Path) -> Path:
    out = tmp_path / "roles"
    out.mkdir()
    (out / "catalog.generated.yaml").write_text("cases: []\n", encoding="utf-8")
    (out / "catalog.manual.yaml").write_text(
        yaml.safe_dump({"cases": CASES}, allow_unicode=True),
        encoding="utf-8",
    )
    return out


def _fake_provider(*args, **kwargs):
    return json.dumps({"target": "developer", "tier_escalation": False})


def test_approved_run_writes_a_valid_two_class_baseline(tmp_path, monkeypatch):
    out = _synthetic_out_dir(tmp_path)
    monkeypatch.setattr(
        runner, "build_context_report", lambda *args, **kwargs: {"tokens_est": 1000}
    )
    monkeypatch.setattr(runner, "call_provider", _fake_provider)
    rc = runner.main(
        [
            "--provider",
            "claude",
            "--provider",
            "opencode",
            "--model-class",
            "a=claude/model-a",
            "--model-class",
            "b=opencode/model-b",
            "--repeat",
            "3",
            "--date",
            "2026-10-17",
            "--approval",
            "yes",
            "--out-dir",
            str(out),
        ]
    )
    assert rc == 0
    path = out / "baseline" / "2026-10-17-a-b-full.json"
    assert path.is_file()
    baseline = json.loads(path.read_text(encoding="utf-8"))
    assert runner.validate_baseline(baseline) == []
    assert baseline["model_ids"] == {"a": "model-a", "b": "model-b"}
    assert baseline["evidence"]["status"] == "evidenced"
    assert baseline["parameters"]["repeat"] == 3
    assert set(baseline["model_classes"]) == {"a", "b"}


def test_declined_run_writes_a_valid_skip_record(tmp_path, monkeypatch):
    out = _synthetic_out_dir(tmp_path)
    monkeypatch.setattr(
        runner, "build_context_report", lambda *args, **kwargs: {"tokens_est": 1000}
    )
    called = []
    monkeypatch.setattr(
        runner, "call_provider", lambda *args, **kwargs: called.append(args)
    )
    rc = runner.main(
        [
            "--provider",
            "opencode",
            "--model-class",
            "deepseek=opencode/opencode-go/deepseek-v4-flash",
            "--date",
            "2026-10-17",
            "--approval",
            "no",
            "--out-dir",
            str(out),
        ]
    )
    assert rc == 3
    assert not called
    path = out / "runs" / "2026-10-17-qg1-deepseek.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    assert runner.validate_skip_record(record) == []
    assert record["status"] == "SKIPPED-BY-USER"


def test_call_provider_passes_wsl_safe_env_and_relative_script(monkeypatch):
    captured = {}

    class _Proc:
        returncode = 0
        stdout = '{"target": "developer"}'
        stderr = ""

    def _fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["env"] = kwargs.get("env") or {}
        captured["cwd"] = kwargs.get("cwd")
        return _Proc()

    monkeypatch.setattr(runner.subprocess, "run", _fake_run)
    monkeypatch.setattr(
        runner.shutil, "which", lambda name: "/usr/bin/bash" if name == "bash" else None
    )
    text = runner.call_provider(
        "opencode",
        "opencode-go/deepseek-v4-flash",
        "task",
        Path(runner.DEFAULT_CONTRACT),
        5.0,
        Path(runner.EVAL_DIR),
    )
    assert text == '{"target": "developer"}'
    assert captured["argv"][0] == "/usr/bin/bash"
    assert captured["argv"][1] == "provider-opencode.sh"
    assert captured["argv"][2:] == ["--agent", "orchestrator", "task"]
    assert captured["cwd"] == str(runner.EVAL_DIR)
    env = captured["env"]
    assert env["OPENCODE_ROUTING_EVAL_MODEL"] == "opencode-go/deepseek-v4-flash"
    assert env["EVAL_OUTPUT_CONTRACT"].endswith("output-contract.md")
    assert "\\" not in env["EVAL_OUTPUT_CONTRACT"]
    assert "EVAL_OUTPUT_CONTRACT/p" in env["WSLENV"]
    assert "OPENCODE_ROUTING_EVAL_MODEL" in env["WSLENV"]


def test_call_provider_raises_on_nonzero_exit(monkeypatch):
    class _Proc:
        returncode = 2
        stdout = ""
        stderr = "boom"

    monkeypatch.setattr(runner.subprocess, "run", lambda *args, **kwargs: _Proc())
    monkeypatch.setattr(runner.shutil, "which", lambda name: "/usr/bin/bash")
    with pytest.raises(runner.ProviderError):
        runner.call_provider(
            "opencode",
            "m",
            "task",
            Path(runner.DEFAULT_CONTRACT),
            5.0,
            Path(runner.EVAL_DIR),
        )


def test_baseline_filename_matches_ic13_naming_scheme():
    assert runner.baseline_filename("2026-10-17", "deepseek", "full") == (
        "2026-10-17-deepseek-full.json"
    )
    assert runner.baseline_filename("2026-10-17", "small+balanced", "full") == (
        "2026-10-17-small-balanced-full.json"
    )


def test_repository_artifacts_are_valid_when_present():
    if BASELINE_DIR.is_dir():
        for path in sorted(BASELINE_DIR.glob("*.json")):
            errors = runner.validate_baseline(
                json.loads(path.read_text(encoding="utf-8"))
            )
            assert not errors, "{}: {}".format(path, errors)
    if RUNS_DIR.is_dir():
        for path in sorted(RUNS_DIR.glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("status") == eg.SKIPPED_BY_USER:
                errors = runner.validate_skip_record(record)
                assert not errors, "{}: {}".format(path, errors)
