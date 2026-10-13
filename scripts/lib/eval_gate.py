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

Gate input (``evaluate_gate``), metric values in percent (0-100;
``language_delta`` -100..100)::

    baseline  = {"corpus_hash", "model_ids",
                 "model_classes": {cls: {metric: [run, ...]}}}
    candidate = {"corpus_hash", "model_ids",
                 "model_classes": {cls: {metric: value}}}

Deliberately deferred: the paired McNemar test (IC-36 "preferred"). The
interface carries only aggregate values, no paired per-case results. Consequence:
only the tau = max(1 pp, k*sigma) criterion is applied, which is the
conservative fallback; a significant paired degradation inside tau is not
detected.
"""

from __future__ import annotations

import hashlib
import json
import math
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

_APPROVAL_TOKENS = frozenset({"yes", "ja"})

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
# Task prompt (case text + instructions) added to the context per call.
DEFAULT_TASK_TOKENS_PER_CASE = 150
DEFAULT_MAX_PRICE_AGE_DAYS = 90
SKIP_RECORD_DIR = "tests/routing-llm-eval/roles/runs"


def _context_tokens(report: Mapping) -> int:
    """Largest per-provider ``always-loaded`` + ``orchestrator`` tokens.

    Falls back to a flat ``tokens_est``. Missing data yields 0 (-> unverified).
    """
    if "tokens_est" in report:
        return _as_int(report["tokens_est"])
    best = 0
    for key, artifacts in report.items():
        if key == "pricing" or not isinstance(artifacts, Mapping):
            continue
        total = 0
        for name in ("always-loaded", "orchestrator"):
            entry = artifacts.get(name)
            if isinstance(entry, Mapping):
                total += _as_int(entry.get("tokens_est", 0))
        best = max(best, total)
    return best


def _as_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _price_current(
    source: Any, price_date: Any, max_age_days: int, today: Optional[str]
) -> bool:
    if not source or not price_date:
        return False
    try:
        age = (date.fromisoformat(today) if today else date.today()) - date.fromisoformat(
            str(price_date)
        )
    except ValueError:
        return False
    return 0 <= age.days <= max_age_days


def estimate_cost(
    cases: int,
    models: Sequence[str],
    runs: int,
    report: dict,
    *,
    task_tokens_per_case: int = DEFAULT_TASK_TOKENS_PER_CASE,
    max_age_days: int = DEFAULT_MAX_PRICE_AGE_DAYS,
    today: Optional[str] = None,
) -> dict:
    """Cost estimate: cases x models x runs calls (IC-36).

    Input tokens per call = max over providers of (``always-loaded`` +
    ``orchestrator``) from the ``measure_artifacts`` report (or flat
    ``tokens_est``) + ``task_tokens_per_case`` (default 150). Optional report
    keys: ``output_tokens_per_call`` (default 200) and ``pricing`` =
    ``{model: {input_per_mtok, output_per_mtok}, _source, _date}``.

    ``unverified`` is true when the context tokens are 0/missing, a price is
    missing, or the price ``_date`` is not an ISO date within ``max_age_days``
    (default 90). ``cost_usd`` is ``None`` without prices or context tokens.
    """
    calls = int(cases) * len(models) * int(runs)
    context = _context_tokens(report)
    in_per_call = context + int(task_tokens_per_case)
    out_per_call = int(
        report.get("output_tokens_per_call", DEFAULT_OUTPUT_TOKENS_PER_CALL)
    )
    pricing = report.get("pricing") or {}
    per_model_calls = int(cases) * int(runs)
    cost: Optional[float] = 0.0 if context > 0 else None
    for model in models:
        if cost is None:
            break
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
    current = _price_current(source, price_date, max_age_days, today)
    return {
        "cases": int(cases),
        "models": list(models),
        "runs": int(runs),
        "calls": calls,
        "input_tokens": calls * in_per_call,
        "output_tokens": calls * out_per_call,
        "cost_usd": None if cost is None else round(cost, 6),
        "price_assumption": (
            {"source": source, "date": price_date} if cost is not None else None
        ),
        "unverified": cost is None or context <= 0 or not current,
    }


def estimate_hash(estimate: Mapping) -> str:
    """Stable SHA-256 of the estimate; binds an approval to one estimate."""
    blob = json.dumps(estimate, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def skip_record_path(root: Path, run_date: str, scope: str) -> Path:
    """``<root>/tests/routing-llm-eval/roles/runs/<date>-<scope>.json``."""
    return Path(root) / SKIP_RECORD_DIR / f"{run_date}-{scope}.json"


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
        f"  estimate hash: {estimate_hash(estimate)}",
    ]
    assumption = estimate.get("price_assumption")
    if assumption:
        lines.append(
            f"  price assumption: source={assumption.get('source')}, "
            f"date={assumption.get('date')}"
        )
    if estimate.get("unverified"):
        lines.append("  UNVERIFIED: tokens or price assumption missing/stale")
    return "\n".join(lines)


def request_approval(estimate: dict, approval_input: Optional[str]) -> bool:
    """True only for exactly ``yes`` / ``ja`` (case-insensitive, trimmed)."""
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
    emit: Callable[[str], None],
    reason: str = "declined by user",
    *,
    approved_estimate_hash: Optional[str] = None,
    today: Optional[str] = None,
) -> dict:
    """Single entry point to paid runs: estimate first, runners only if approved.

    ``emit`` is mandatory: the estimate is always shown before anything else.
    - ``approval_input`` None/empty/whitespace: 0 runner calls, status
      ``awaiting-approval``, no file.
    - ``approved_estimate_hash`` given but different from
      ``estimate_hash(estimate)``: awaiting (approval was for another estimate).
    - Other non-affirmative input: 0 calls, ``SKIPPED-BY-USER`` file.
    - ``yes``/``ja``: runners are called in order, results collected.
    """
    text = format_estimate(estimate)
    emit(text)
    waiting = {"status": AWAITING_APPROVAL, "estimate_text": text, "results": []}
    if approval_input is None or not approval_input.strip():
        return waiting
    if approved_estimate_hash is not None and approved_estimate_hash != estimate_hash(
        estimate
    ):
        return waiting
    if not request_approval(estimate, approval_input):
        write_skip_record(skip_path, estimate, reason, today=today)
        return {"status": SKIPPED_BY_USER, "estimate_text": text, "results": []}
    results = [runner() for runner in runners]
    return {"status": APPROVED, "estimate_text": text, "results": results}


def _valid(value: Any, direction: str) -> bool:
    """Finite number within 0..100 (-100..100 for ``abs_delta``); no bools."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if math.isnan(value) or math.isinf(value):
        return False
    low = -100.0 if direction == "abs_delta" else 0.0
    return low <= value <= 100.0


def _tolerance(values: Sequence[float], k: float) -> tuple:
    """Return ``(mean, tau)`` with tau = max(1 pp, k * sample sigma)."""
    return statistics.mean(values), max(MIN_TOLERANCE_PP, k * statistics.stdev(values))


def _baseline_sufficient(classes: Mapping) -> bool:
    """>= 2 classes and >= 3 valid runs per metric.

    Applies to ``zero`` metrics too, on purpose: a baseline that cannot
    establish sigma for the other metrics is not evidence for the gate as a
    whole, and one uniform rule avoids per-metric special cases.
    Invalid baseline values (None/NaN/out of range) make it insufficient.
    """
    if len(classes) < MIN_MODEL_CLASSES:
        return False
    for metrics in classes.values():
        if not isinstance(metrics, Mapping) or not metrics:
            return False
        for metric, runs in metrics.items():
            if metric not in METRIC_DIRECTIONS:
                raise ValueError(f"unknown eval metric: {metric}")
            if not isinstance(runs, (list, tuple)) or len(runs) < MIN_BASELINE_RUNS:
                return False
            if not all(_valid(v, METRIC_DIRECTIONS[metric]) for v in runs):
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

    ``not-evidenced`` (never ``passed``) when the comparison itself is not
    valid: skipped candidate, baseline with < 2 model classes / < 3 runs /
    invalid values, ``corpus_hash`` or ``model_ids`` missing on either side or
    different. Invalid candidate values (None, NaN, bool, out of range 0..100;
    -100..100 for ``language_delta``) or missing candidate classes/metrics
    never raise; they make that metric unevidenced. A definite miss on any
    other present metric wins: ``failed`` dominates ``not-evidenced``.
    Unknown metric names raise ``ValueError``.
    """
    if candidate.get("status") == SKIPPED_BY_USER:
        return NOT_EVIDENCED
    classes = baseline.get("model_classes")
    if not isinstance(classes, Mapping) or not _baseline_sufficient(classes):
        return NOT_EVIDENCED
    for key in ("corpus_hash", "model_ids"):
        b_val, c_val = baseline.get(key), candidate.get(key)
        if not b_val or not c_val or b_val != c_val:
            return NOT_EVIDENCED
    cand_classes = candidate.get("model_classes")
    if not isinstance(cand_classes, Mapping):
        return NOT_EVIDENCED
    failed = False
    unevidenced = False
    for cls in sorted(classes):
        cand_metrics = cand_classes.get(cls)
        if not isinstance(cand_metrics, Mapping):
            unevidenced = True
            continue
        for metric in sorted(classes[cls]):
            direction = METRIC_DIRECTIONS[metric]
            value = cand_metrics.get(metric)
            if not _valid(value, direction):
                unevidenced = True
                continue
            if not _metric_ok(direction, classes[cls][metric], float(value), k):
                failed = True
    if failed:
        return FAILED
    return NOT_EVIDENCED if unevidenced else PASSED
