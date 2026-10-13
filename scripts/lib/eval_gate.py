"""Eval tolerance model and execution-approval wrapper (IC-36).

No network, no LLM calls, no keys. Prices and models are plain parameters
(``report["pricing"]``); the paid runner is only ever reached through
:func:`run_with_approval`, which is the single sanctioned path to a paid run.

Schemas
-------
Estimate (``estimate_cost``)::

    {"cases", "models", "runs", "calls", "input_tokens", "output_tokens",
     "cost_usd" (float | None), "price_assumption" (dict | None),
     "unverified" (bool)}

Skip record (``write_skip_record``)::

    {"status": "SKIPPED-BY-USER", "date": "YYYY-MM-DD",
     "estimate": {...}, "reason": "..."}

Gate input (``evaluate_gate``), metric values in percent (0-100)::

    baseline  = {"corpus_hash"?, "model_classes": {cls: {metric: [run, ...]}}}
    candidate = {"corpus_hash"?, "model_classes": {cls: {metric: value}}}
"""

from __future__ import annotations

import json
import statistics
from datetime import date
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

SKIPPED_BY_USER = "SKIPPED-BY-USER"
AWAITING_APPROVAL = "awaiting-approval"
APPROVED = "approved"

PASSED = "passed"
FAILED = "failed"
NOT_EVIDENCED = "not-evidenced"

MIN_BASELINE_RUNS = 3
MIN_MODEL_CLASSES = 2
MIN_TOLERANCE_PP = 1.0
_EPS = 1e-9

_APPROVAL_TOKENS = frozenset({"yes", "y", "ja", "j"})

# Metric -> direction (IC-36 table). Unknown metrics are rejected.
#   higher    : candidate >= baseline_mean - tau
#   lower     : candidate <= baseline_mean + tau
#   zero      : candidate == 0 (absolute, no sigma needed)
#   abs_delta : |candidate| <= |baseline_mean| + tau (language delta)
METRIC_DIRECTIONS: dict = {
    "top1_accuracy": "higher",
    "collision_accuracy": "higher",
    "ambiguity_clarify_rate": "higher",
    "wrong_pipeline_rate": "lower",
    "over_clarify_rate": "lower",
    "escalation_correct": "higher",
    "inactive_role_dispatch": "zero",
    "language_delta": "abs_delta",
}

DEFAULT_OUTPUT_TOKENS_PER_CALL = 200


def _input_tokens_per_call(report: Mapping) -> int:
    """Largest ``always-loaded`` token estimate over providers (or flat key)."""
    if "tokens_est" in report:
        return int(report["tokens_est"])
    best = 0
    for key, artifacts in report.items():
        if key == "pricing" or not isinstance(artifacts, Mapping):
            continue
        entry = artifacts.get("always-loaded")
        if isinstance(entry, Mapping):
            best = max(best, int(entry.get("tokens_est", 0)))
    return best


def estimate_cost(
    cases: int, models: Sequence[str], runs: int, report: dict
) -> dict:
    """Cost estimate: cases x models x runs calls (IC-36).

    ``report`` is the ``measure_artifacts`` result (or a dict with
    ``tokens_est``). Optional keys: ``output_tokens_per_call`` and
    ``pricing`` = ``{model: {input_per_mtok, output_per_mtok}}`` plus
    ``pricing["_source"]`` / ``pricing["_date"]``. Without complete prices
    ``cost_usd`` is ``None`` and the estimate is marked ``unverified``.
    """
    calls = int(cases) * len(models) * int(runs)
    in_per_call = _input_tokens_per_call(report)
    out_per_call = int(
        report.get("output_tokens_per_call", DEFAULT_OUTPUT_TOKENS_PER_CALL)
    )
    pricing = report.get("pricing") or {}
    per_model_calls = int(cases) * int(runs)
    cost: Optional[float] = 0.0
    for model in models:
        price = pricing.get(model)
        if not isinstance(price, Mapping):
            cost = None
            break
        cost += per_model_calls * (
            in_per_call * float(price["input_per_mtok"])
            + out_per_call * float(price["output_per_mtok"])
        ) / 1_000_000
    source = pricing.get("_source")
    price_date = pricing.get("_date")
    assumption = None
    if cost is not None:
        assumption = {"source": source, "date": price_date}
    return {
        "cases": int(cases),
        "models": list(models),
        "runs": int(runs),
        "calls": calls,
        "input_tokens": calls * in_per_call,
        "output_tokens": calls * out_per_call,
        "cost_usd": None if cost is None else round(cost, 6),
        "price_assumption": assumption,
        "unverified": cost is None or not source or not price_date,
    }


def format_estimate(estimate: Mapping) -> str:
    """Human-readable estimate block shown before every paid run."""
    cost = estimate.get("cost_usd")
    cost_txt = "unknown (no price data)" if cost is None else f"{cost:.4f} USD"
    lines = [
        "Eval cost estimate (IC-36):",
        f"  cases x models x runs: {estimate['cases']} x "
        f"{len(estimate['models'])} x {estimate['runs']} = {estimate['calls']} calls",
        f"  models: {', '.join(estimate['models'])}",
        f"  est. input tokens: {estimate['input_tokens']}, "
        f"output tokens: {estimate['output_tokens']}",
        f"  est. cost: {cost_txt}",
    ]
    assumption = estimate.get("price_assumption")
    if assumption:
        lines.append(
            f"  price assumption: source={assumption.get('source')}, "
            f"date={assumption.get('date')}"
        )
    if estimate.get("unverified"):
        lines.append("  UNVERIFIED: price assumption missing or not current")
    return "\n".join(lines)


def request_approval(estimate: dict, approval_input: Optional[str]) -> bool:
    """True only for an explicit affirmative (yes/y/ja/j, case-insensitive)."""
    if approval_input is None:
        return False
    return approval_input.strip().lower() in _APPROVAL_TOKENS


def write_skip_record(
    path: Path, estimate: dict, reason: str, *, today: Optional[str] = None
) -> None:
    """Persist a ``SKIPPED-BY-USER`` record (date, estimate, reason)."""
    record = {
        "status": SKIPPED_BY_USER,
        "date": today or date.today().isoformat(),
        "estimate": estimate,
        "reason": reason,
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run_with_approval(
    estimate: dict,
    approval_input: Optional[str],
    runners: Sequence[Callable[[], Any]],
    skip_path: Path,
    reason: str = "declined by user",
    emit: Optional[Callable[[str], None]] = None,
    *,
    today: Optional[str] = None,
) -> dict:
    """Single entry point to paid runs: estimate first, runners only if approved.

    - ``approval_input is None``: estimate emitted, 0 runner calls, status
      ``awaiting-approval``, no file.
    - Explicit non-affirmative input: 0 runner calls, ``SKIPPED-BY-USER`` file.
    - Affirmative: runners are called in order, results collected.
    """
    text = format_estimate(estimate)
    if emit is not None:
        emit(text)
    if approval_input is None:
        return {"status": AWAITING_APPROVAL, "estimate_text": text, "results": []}
    if not request_approval(estimate, approval_input):
        write_skip_record(skip_path, estimate, reason, today=today)
        return {"status": SKIPPED_BY_USER, "estimate_text": text, "results": []}
    results = [runner() for runner in runners]
    return {"status": APPROVED, "estimate_text": text, "results": results}


def _tolerance(values: Sequence[float], k: float) -> tuple:
    """Return ``(mean, tau)`` with tau = max(1 pp, k * sample sigma)."""
    return statistics.mean(values), max(MIN_TOLERANCE_PP, k * statistics.stdev(values))


def _baseline_sufficient(baseline: Mapping, classes: Mapping) -> bool:
    if len(classes) < MIN_MODEL_CLASSES:
        return False
    for metrics in classes.values():
        if not isinstance(metrics, Mapping) or not metrics:
            return False
        for runs in metrics.values():
            if not isinstance(runs, (list, tuple)) or len(runs) < MIN_BASELINE_RUNS:
                return False
    return True


def _metric_ok(direction: str, base_runs: Sequence[float], value: float, k: float) -> bool:
    mean, tau = _tolerance(base_runs, k)
    if direction == "higher":
        return value >= mean - tau - _EPS
    if direction == "lower":
        return value <= mean + tau + _EPS
    if direction == "zero":
        return abs(value) <= _EPS
    return abs(value) <= abs(mean) + tau + _EPS  # abs_delta


def evaluate_gate(baseline: dict, candidate: dict, k: float = 2.0) -> str:
    """Return ``passed`` | ``failed`` | ``not-evidenced`` (IC-36).

    ``not-evidenced`` (never ``passed``) for: a skipped candidate, fewer than
    2 model classes or fewer than 3 baseline runs per metric (no sigma),
    differing corpus hashes, or candidate values missing for a baseline
    class/metric. Unknown metric names raise ``ValueError``.
    """
    if candidate.get("status") == SKIPPED_BY_USER:
        return NOT_EVIDENCED
    classes = baseline.get("model_classes")
    if not isinstance(classes, Mapping) or not _baseline_sufficient(baseline, classes):
        return NOT_EVIDENCED
    b_hash, c_hash = baseline.get("corpus_hash"), candidate.get("corpus_hash")
    if b_hash is not None and c_hash is not None and b_hash != c_hash:
        return NOT_EVIDENCED
    cand_classes = candidate.get("model_classes")
    if not isinstance(cand_classes, Mapping):
        return NOT_EVIDENCED
    failed = False
    for cls in sorted(classes):
        cand_metrics = cand_classes.get(cls)
        if not isinstance(cand_metrics, Mapping):
            return NOT_EVIDENCED
        for metric in sorted(classes[cls]):
            if metric not in METRIC_DIRECTIONS:
                raise ValueError(f"unknown eval metric: {metric}")
            if metric not in cand_metrics:
                return NOT_EVIDENCED
            direction = METRIC_DIRECTIONS[metric]
            if not _metric_ok(direction, classes[cls][metric], float(cand_metrics[metric]), k):
                failed = True
    return FAILED if failed else PASSED
