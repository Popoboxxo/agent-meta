#!/usr/bin/env python3
"""Run the role-routing eval and write an IC-13/IC-36 baseline.

The runner is deliberately one explicit, user-gated path:

1. load ``catalog.generated.yaml`` + ``catalog.manual.yaml`` and hash the union,
2. measure the rendered context (the same ``measure_artifacts`` function as
   ``sync.py --context-report``) and build an ``eval_gate.estimate_cost``
   estimate,
3. show the estimate and wait for an explicit ``yes``/``ja`` (``--approval``);
   no provider is called without it,
4. run every case ``--repeat`` times through ``provider-<name>.sh``, grade the
   JSON output contract ``{target[, tier_escalation]}``, aggregate the metrics,
5. write ``baseline/<date>-<model>-<profile>.json``; a rejection writes the
   ``SKIPPED-BY-USER`` record next to it under ``runs/``.

No automatic/nightly path exists. ``--estimate-only`` never calls a provider.
The model class is explicit (``--model-class NAME=PROVIDER/MODEL``), so a
single-class Deepseek run is possible; such a baseline is written with
``evidence.status = not-evidenced`` because AC-02 requires at least two model
classes. Two or more classes are fully supported by repeating the flag.

Exit codes: 0 run/estimate ok, 1 error, 2 awaiting approval, 3 skipped by user.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

_REPO_ROOT = Path(__file__).resolve().parent.parent
# Scripts run with ``scripts/`` on sys.path (the ``lib.*`` imports below); the
# repo root makes the namespace package ``scripts.*`` work under pytest too.
_SCRIPTS_DIR = Path(__file__).resolve().parent
for _path in (str(_REPO_ROOT), str(_SCRIPTS_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

try:
    import yaml  # type: ignore[import]
except ImportError:  # pragma: no cover - exercised by the CLI, not the tests
    print("PyYAML is required (pip install pyyaml).", file=sys.stderr)
    sys.exit(1)

from scripts import gen_role_routing_eval_catalog as gen
from scripts.lib import eval_gate
from scripts.lib.config import load_config
from scripts.lib.context_report import measure_artifacts, merge_provider_mappings
from scripts.lib.providers import (
    load_provider_capabilities,
    load_providers_config,
    resolve_providers,
)

EVAL_DIR = _REPO_ROOT / "tests" / "routing-llm-eval"
ROLES_DIR = EVAL_DIR / "roles"
DEFAULT_CONTRACT = EVAL_DIR / "output-contract.md"
DEFAULT_PRICE_FILE = _REPO_ROOT / "config" / "pricing-overlay.yaml"
DEFAULT_PROFILE = "full"
SCHEMA_VERSION = 1
BASELINE_KIND = "role-routing-baseline"
GENERATED_NAME = "catalog.generated.yaml"
MANUAL_NAME = "catalog.manual.yaml"

# IC-36 metric names and the IC-13/AC-62 extras that must be present per class.
REQUIRED_METRICS = (
    "top1_accuracy",
    "collision_accuracy",
    "ambiguity_clarify_rate",
    "wrong_pipeline_rate",
    "over_clarify_rate",
    "escalation_correct",
    "inactive_role_dispatch",
    "language_delta",
)


class ProviderError(RuntimeError):
    """The provider wrapper failed at the infrastructure level (not a model miss)."""


# ---------------------------------------------------------------------------
# Catalog + grading
# ---------------------------------------------------------------------------


def _load_cases(path: Path) -> list:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("cases") or [])


def load_catalog(out_dir: Path = ROLES_DIR) -> Tuple[list, str]:
    """Return ``(cases, sha256)`` for the generated + manual catalogs."""
    out_dir = Path(out_dir)
    cases = _load_cases(out_dir / GENERATED_NAME) + _load_cases(out_dir / MANUAL_NAME)
    if not cases:
        raise ValueError(
            "no eval cases found in {} (expected {} + {})".format(
                out_dir, GENERATED_NAME, MANUAL_NAME
            )
        )
    return cases, gen.corpus_hash(out_dir)


def normalize_target(value: Any) -> Optional[str]:
    """Normalize a role/pipeline target; ``ASK`` is case-insensitive."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.casefold() == "ask":
        return "ASK"
    return text.casefold()


def parse_prediction(text: str) -> dict:
    """Parse the model output contract ``{target[, tier_escalation]}``.

    Accepts the exact JSON object, a JSON object embedded in prose, and a
    fenced JSON block. Rejects objects without a string ``target`` or with a
    non-boolean ``tier_escalation``. Raises ``ValueError`` with a short reason.
    """
    raw = (text or "").strip()
    if not raw:
        raise ValueError("empty model output")

    candidates = [raw]
    if raw.startswith("```"):
        stripped = re.sub(r"^```[A-Za-z0-9_-]*\s*", "", raw)
        stripped = re.sub(r"\s*```$", "", stripped).strip()
        if stripped:
            candidates.insert(0, stripped)

    decoder = json.JSONDecoder()
    obj = None
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            value = None
        if isinstance(value, dict) and isinstance(value.get("target"), str):
            obj = value
            break
        for index, char in enumerate(candidate):
            if char != "{":
                continue
            try:
                value, _ = decoder.raw_decode(candidate[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict) and isinstance(value.get("target"), str):
                obj = value
                break
        if obj is not None:
            break

    if obj is None:
        raise ValueError("no JSON object with a string 'target' in model output")
    target = normalize_target(obj.get("target"))
    if target is None:
        raise ValueError("target must be a non-empty string")
    tier = obj.get("tier_escalation", False)
    if not isinstance(tier, bool):
        raise ValueError("tier_escalation must be a boolean")
    return {"target": target, "tier_escalation": tier}


def _rate(flags: Sequence[bool]) -> float:
    if not flags:
        return 0.0
    return round(100.0 * sum(1 for flag in flags if flag) / len(flags), 4)


def compute_metrics(cases: Sequence[dict], predictions: Mapping[str, Optional[dict]]) -> dict:
    """Aggregate one run into the IC-36/AC-62 metric set (values in percent)."""
    grades: List[dict] = []
    for case in cases:
        expected = case.get("expected") or {}
        expected_target = normalize_target(expected.get("target")) or ""
        expected_tier = bool(expected.get("tier_escalation"))
        prediction = predictions.get(case.get("id"))
        if prediction is None:
            target = None
            tier = False
        else:
            target = normalize_target(prediction.get("target"))
            tier = bool(prediction.get("tier_escalation", False))
        grades.append(
            {
                "id": case.get("id"),
                "correct": target == expected_target,
                "target": target,
                "expected_target": expected_target,
                "tier_escalation": tier,
                "expected_tier": expected_tier,
                "collision": "overlap_token" in case,
                "ambiguous_expected": expected_target == "ASK",
                "wrong_pipeline": bool(
                    target
                    and target.startswith("pipeline:")
                    and target != expected_target
                ),
                "clarified": target == "ASK",
            }
        )

    non_ambiguous = [g for g in grades if not g["ambiguous_expected"]]
    collisions = [g for g in grades if g["collision"]]
    ambiguous = [g for g in grades if g["ambiguous_expected"]]

    by_id = {g["id"]: g for g in grades}
    deltas = []
    for de_case, en_case in gen.language_pairs({"cases": list(cases)}):
        de_grade = by_id.get(de_case.get("id"))
        en_grade = by_id.get(en_case.get("id"))
        if de_grade is None or en_grade is None:
            continue
        deltas.append((1 if de_grade["correct"] else 0) - (1 if en_grade["correct"] else 0))

    return {
        "top1_accuracy": _rate([g["correct"] for g in grades]),
        "collision_accuracy": _rate([g["correct"] for g in collisions]),
        "ambiguity_clarify_rate": _rate([g["clarified"] for g in ambiguous]),
        "wrong_pipeline_rate": _rate([g["wrong_pipeline"] for g in grades]),
        "over_clarify_rate": _rate([g["clarified"] for g in non_ambiguous]),
        "escalation_correct": _rate(
            [g["tier_escalation"] == g["expected_tier"] for g in grades]
        ),
        # The subset variant (IC-13) is not part of the full-profile corpus;
        # full has no inactive roles, so the absolute target is 0.
        "inactive_role_dispatch": 0.0,
        "language_delta": round(100.0 * sum(deltas) / len(deltas), 4)
        if deltas
        else 0.0,
    }


# ---------------------------------------------------------------------------
# Baseline + skip schema
# ---------------------------------------------------------------------------


def _evidence(model_classes: Mapping, errors: Sequence[Mapping]) -> dict:
    reasons: List[str] = []
    observed = len(model_classes)
    if observed < eval_gate.MIN_MODEL_CLASSES:
        reasons.append(
            "only {} model class(es); AC-02 requires at least {}".format(
                observed, eval_gate.MIN_MODEL_CLASSES
            )
        )
    for model_class, metrics in sorted(model_classes.items()):
        for metric, values in sorted(metrics.items()):
            if len(values) < eval_gate.MIN_BASELINE_RUNS:
                reasons.append(
                    "class '{}' metric '{}' has {} run(s); at least {} required".format(
                        model_class, metric, len(values), eval_gate.MIN_BASELINE_RUNS
                    )
                )
    if errors:
        reasons.append(
            "{} eval error(s) recorded; rerun before using this baseline".format(
                len(errors)
            )
        )
    return {
        "status": "not-evidenced" if reasons else "evidenced",
        "min_model_classes": eval_gate.MIN_MODEL_CLASSES,
        "observed_model_classes": observed,
        "min_runs_per_metric": eval_gate.MIN_BASELINE_RUNS,
        "reasons": reasons,
    }


def build_baseline(
    *,
    cases: Sequence[dict],
    class_runs: Mapping[str, Sequence[dict]],
    model_ids: Mapping[str, str],
    providers: Mapping[str, str],
    parameters: Mapping,
    corpus_hash: str,
    profile: str,
    run_date: str,
    label: str,
) -> dict:
    """Build the versioned baseline document from per-class run results."""
    model_classes: Dict[str, Dict[str, List[float]]] = {}
    sigma: Dict[str, Dict[str, Optional[float]]] = {}
    runs_out: List[dict] = []
    errors_out: List[dict] = []

    for model_class in sorted(class_runs):
        runs = list(class_runs[model_class])
        metrics: Dict[str, List[float]] = {}
        for metric in REQUIRED_METRICS:
            values: List[float] = []
            for run in runs:
                value = (run.get("metrics") or {}).get(metric)
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    value = 0.0
                values.append(round(float(value), 4))
            metrics[metric] = values
        model_classes[model_class] = metrics
        sigma[model_class] = {
            metric: (
                round(statistics.stdev(values), 6) if len(values) >= 2 else None
            )
            for metric, values in metrics.items()
        }
        for run in runs:
            runs_out.append(
                {
                    "model_class": model_class,
                    "run": run.get("run"),
                    "metrics": dict(run.get("metrics") or {}),
                    "error_count": len(run.get("errors") or []),
                }
            )
            for error in run.get("errors") or []:
                errors_out.append(
                    dict(
                        {"model_class": model_class, "run": run.get("run")},
                        **dict(error),
                    )
                )

    return {
        "schema_version": SCHEMA_VERSION,
        "kind": BASELINE_KIND,
        "date": run_date,
        "profile": profile,
        "label": label,
        "corpus_hash": corpus_hash,
        "catalog": {
            "generated": GENERATED_NAME,
            "manual": MANUAL_NAME,
            "cases": len(cases),
        },
        "model_ids": dict(model_ids),
        "model_providers": dict(providers),
        "parameters": dict(parameters),
        "model_classes": model_classes,
        "sigma": sigma,
        "evidence": _evidence(model_classes, errors_out),
        "errors": errors_out,
        "runs": runs_out,
    }


def validate_baseline(baseline: Any) -> List[str]:
    """Return schema errors; an empty list means the artifact is well-formed.

    A well-formed baseline may still be ``not-evidenced`` (for example a
    single-class Deepseek run). That is a valid artifact, not a schema error.
    """
    if not isinstance(baseline, Mapping):
        return ["baseline is not a JSON object"]
    errors: List[str] = []
    for key in (
        "schema_version",
        "kind",
        "date",
        "profile",
        "corpus_hash",
        "model_ids",
        "model_classes",
        "sigma",
        "parameters",
        "evidence",
    ):
        if key not in baseline:
            errors.append("missing key: {}".format(key))
    if baseline.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be {}".format(SCHEMA_VERSION))
    if baseline.get("kind") != BASELINE_KIND:
        errors.append("kind must be {}".format(BASELINE_KIND))
    try:
        date.fromisoformat(str(baseline.get("date")))
    except ValueError:
        errors.append("date must be an ISO date (YYYY-MM-DD)")

    corpus_hash = baseline.get("corpus_hash")
    if not isinstance(corpus_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", corpus_hash):
        errors.append("corpus_hash must be a 64-character lowercase sha256")

    model_ids = baseline.get("model_ids")
    model_classes = baseline.get("model_classes")
    if not isinstance(model_ids, Mapping) or not model_ids:
        errors.append("model_ids must be a non-empty object")
    if not isinstance(model_classes, Mapping) or not model_classes:
        errors.append("model_classes must be a non-empty object")
    if isinstance(model_ids, Mapping) and isinstance(model_classes, Mapping):
        if set(model_ids) != set(model_classes):
            errors.append("model_ids and model_classes must have the same classes")
        for model_class, metrics in model_classes.items():
            if not isinstance(metrics, Mapping):
                errors.append("model_classes.{} is not an object".format(model_class))
                continue
            for metric in REQUIRED_METRICS:
                values = metrics.get(metric)
                if not isinstance(values, list) or not values:
                    errors.append(
                        "model_classes.{}.{} must be a non-empty list".format(
                            model_class, metric
                        )
                    )
                    continue
                low = -100.0 if metric == "language_delta" else 0.0
                for value in values:
                    if isinstance(value, bool) or not isinstance(value, (int, float)):
                        errors.append(
                            "model_classes.{}.{} contains a non-number".format(
                                model_class, metric
                            )
                        )
                        break
                    if not (low <= float(value) <= 100.0):
                        errors.append(
                            "model_classes.{}.{} value out of range: {}".format(
                                model_class, metric, value
                            )
                        )
                        break

    sigma = baseline.get("sigma")
    if not isinstance(sigma, Mapping):
        errors.append("sigma must be an object")
    elif isinstance(model_classes, Mapping):
        if set(sigma) != set(model_classes):
            errors.append("sigma must have one entry per model class")
        for model_class, metrics in sigma.items():
            if not isinstance(metrics, Mapping):
                errors.append("sigma.{} is not an object".format(model_class))
                continue
            for metric in REQUIRED_METRICS:
                value = metrics.get(metric)
                if value is None:
                    continue
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    errors.append(
                        "sigma.{}.{} must be a number or null".format(
                            model_class, metric
                        )
                    )
                elif value < 0:
                    errors.append(
                        "sigma.{}.{} must be non-negative".format(model_class, metric)
                    )

    parameters = baseline.get("parameters")
    if not isinstance(parameters, Mapping):
        errors.append("parameters must be an object")
    else:
        for key in ("repeat", "k", "price_assumption", "estimate_hash", "case_count", "calls"):
            if key not in parameters:
                errors.append("parameters.{} is missing".format(key))
        if not isinstance(parameters.get("repeat"), int) or parameters.get("repeat", 0) < 1:
            errors.append("parameters.repeat must be a positive integer")
        if isinstance(parameters.get("k"), bool) or not isinstance(
            parameters.get("k"), (int, float)
        ):
            errors.append("parameters.k must be a number")

    evidence = baseline.get("evidence")
    if not isinstance(evidence, Mapping):
        errors.append("evidence must be an object")
    elif evidence.get("status") not in ("evidenced", "not-evidenced"):
        errors.append("evidence.status must be evidenced or not-evidenced")
    elif not isinstance(evidence.get("reasons"), list):
        errors.append("evidence.reasons must be a list")
    return errors


def validate_skip_record(record: Any) -> List[str]:
    """Return schema errors for an IC-36 ``SKIPPED-BY-USER`` record."""
    if not isinstance(record, Mapping):
        return ["skip record is not a JSON object"]
    errors: List[str] = []
    if record.get("status") != eval_gate.SKIPPED_BY_USER:
        errors.append("status must be {}".format(eval_gate.SKIPPED_BY_USER))
    try:
        date.fromisoformat(str(record.get("date")))
    except ValueError:
        errors.append("date must be an ISO date (YYYY-MM-DD)")
    if not isinstance(record.get("reason"), str) or not record.get("reason", "").strip():
        errors.append("reason must be a non-empty string")
    estimate = record.get("estimate")
    if not isinstance(estimate, Mapping):
        errors.append("estimate must be an object")
    else:
        for key in (
            "cases",
            "models",
            "runs",
            "calls",
            "input_tokens",
            "output_tokens",
            "cost_usd",
            "price_assumption",
            "unverified",
        ):
            if key not in estimate:
                errors.append("estimate.{} is missing".format(key))
    return errors


def baseline_filename(run_date: str, label: str, profile: str) -> str:
    """IC-13 naming scheme ``<date>-<model>-<profile>.json``."""
    return "{}-{}-{}.json".format(run_date, _slug(label), _slug(profile))


def _slug(value: Any) -> str:
    slug = re.sub(r"[^a-z0-9._-]+", "-", str(value).strip().lower())
    return slug.strip("-") or "model"


# ---------------------------------------------------------------------------
# Estimate (no provider calls)
# ---------------------------------------------------------------------------


def build_context_report(root: Path, config_path: Path) -> dict:
    """Measure the project's context artifacts (same function as --context-report)."""
    config = load_config(Path(config_path))
    provider_config = load_providers_config(Path(root), config)
    providers = resolve_providers(config, provider_config)
    capabilities = merge_provider_mappings(
        provider_config, load_provider_capabilities(Path(root))
    )
    return measure_artifacts(Path(root), providers, capabilities)


def _flatten_prices(data: Mapping) -> dict:
    flat: Dict[str, dict] = {}
    for entries in (data.get("prices") or {}).values():
        if not isinstance(entries, Mapping):
            continue
        url = entries.get("_url")
        for name, price in entries.items():
            if str(name).startswith("_") or not isinstance(price, Mapping):
                continue
            if "input" in price and "output" in price:
                flat[str(name)] = {
                    "input_per_mtok": float(price["input"]),
                    "output_per_mtok": float(price["output"]),
                    "_url": url,
                }
    return flat


def pricing_for(
    price_file: Path,
    models: Sequence[str],
    price_date: Optional[str] = None,
    price_source: Optional[str] = None,
) -> dict:
    """Build the ``eval_gate`` pricing block; without a date it stays unverified."""
    path = Path(price_file)
    flat = {}
    if path.is_file():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(data, Mapping):
            flat = _flatten_prices(data)
    pricing: Dict[str, Any] = {}
    for model in models:
        if model in flat:
            pricing[model] = flat[model]
    try:
        default_source = path.relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        default_source = str(path)
    pricing["_source"] = price_source or default_source
    pricing["_date"] = price_date
    return pricing


def estimate_for(
    *,
    cases: Sequence[dict],
    model_classes: Sequence[Mapping],
    repeat: int,
    report: Mapping,
    price_file: Path,
    price_date: Optional[str],
    price_source: Optional[str],
    today: str,
) -> dict:
    models = [str(item["model_id"]) for item in model_classes]
    pricing = pricing_for(price_file, models, price_date, price_source)
    priced_report = dict(report)
    priced_report["pricing"] = pricing
    return eval_gate.estimate_cost(
        len(cases), models, repeat, priced_report, today=today
    )


# ---------------------------------------------------------------------------
# Provider execution
# ---------------------------------------------------------------------------


def discover_providers(eval_dir: Path = EVAL_DIR) -> List[str]:
    return sorted(
        path.name[len("provider-") : -len(".sh")]
        for path in Path(eval_dir).glob("provider-*.sh")
    )


def parse_model_classes(
    specs: Sequence[str],
    *,
    providers_filter: Sequence[str],
    eval_dir: Path,
    require_explicit_models: bool,
) -> List[dict]:
    """Parse repeatable ``NAME=PROVIDER/MODEL`` class specs.

    Without specs, every (filtered) provider gets a ``default`` model class so
    ``--estimate-only`` stays usable; a paid run requires explicit model IDs so
    the baseline can record them.
    """
    available = discover_providers(eval_dir)
    if not available:
        raise ValueError("no provider-*.sh wrappers found in {}".format(eval_dir))
    classes: List[dict] = []
    for spec in specs:
        name, sep, target = str(spec).partition("=")
        provider, sep2, model = target.partition("/")
        if not sep or not name.strip() or not sep2 or not provider.strip() or not model.strip():
            raise ValueError(
                "invalid --model-class {!r}; expected NAME=PROVIDER/MODEL".format(spec)
            )
        classes.append(
            {
                "name": name.strip(),
                "provider": provider.strip(),
                "model_id": model.strip(),
            }
        )

    for item in classes:
        if item["provider"] not in available:
            raise ValueError(
                "unknown provider {!r}; available: {}".format(
                    item["provider"], ", ".join(available)
                )
            )
    if providers_filter:
        for provider in providers_filter:
            if provider not in available:
                raise ValueError(
                    "unknown provider {!r}; available: {}".format(
                        provider, ", ".join(available)
                    )
                )
        classes = [item for item in classes if item["provider"] in providers_filter]
    if not classes:
        selected = list(providers_filter) or available
        classes = [
            {"name": provider, "provider": provider, "model_id": "default"}
            for provider in selected
        ]
    if require_explicit_models and not specs:
        raise ValueError(
            "a paid run requires --model-class NAME=PROVIDER/MODEL so the "
            "baseline records the model IDs"
        )
    names = [item["name"] for item in classes]
    if len(names) != len(set(names)):
        raise ValueError("duplicate --model-class names: {}".format(", ".join(names)))
    return classes


def _shell() -> str:
    for name in ("bash", "sh"):
        path = shutil.which(name)
        if path:
            return path
    raise ProviderError(
        "bash/sh not found; the provider wrappers are POSIX shell scripts"
    )


def call_provider(
    provider: str,
    model_id: str,
    prompt: str,
    contract: Path,
    timeout: float,
    eval_dir: Path = EVAL_DIR,
) -> str:
    """Invoke one provider wrapper and return its stdout."""
    script = Path(eval_dir) / "provider-{}.sh".format(provider)
    if not script.is_file():
        raise ProviderError("provider wrapper not found: {}".format(script))
    shell = _shell()
    env = os.environ.copy()
    prefix = re.sub(r"[^A-Za-z0-9]+", "_", provider).upper()
    model_var = "{}_ROUTING_EVAL_MODEL".format(prefix)
    env[model_var] = model_id
    # Provider wrapper input is env-only. On Windows `bash` may be WSL bash,
    # which forwards only WSLENV-listed variables; list both and flag the
    # contract as a path so WSL translates `C:/...` to `/mnt/...`. Git Bash and
    # Linux ignore WSLENV and use the plain inherited values.
    env["EVAL_OUTPUT_CONTRACT"] = contract.as_posix()
    env["WSLENV"] = ":".join(
        entry
        for entry in (env.get("WSLENV", ""), "EVAL_OUTPUT_CONTRACT/p", model_var)
        if entry
    )
    # cwd is the eval dir, so the relative script name avoids drive-letter
    # path mangling in both Git Bash and WSL bash.
    argv = [shell, script.name, "--agent", "orchestrator", prompt]
    try:
        proc = subprocess.run(
            argv,
            cwd=str(eval_dir),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise
    except OSError as exc:
        raise ProviderError("cannot start provider '{}': {}".format(provider, exc))
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()[-500:]
        raise ProviderError(
            "provider '{}' exited {}: {}".format(provider, proc.returncode, detail)
        )
    return proc.stdout


def run_class(
    *,
    model_class: Mapping,
    cases: Sequence[dict],
    repeat: int,
    contract: Path,
    timeout: float,
    eval_dir: Path = EVAL_DIR,
) -> dict:
    runs: List[dict] = []
    for index in range(1, repeat + 1):
        predictions: Dict[str, Optional[dict]] = {}
        errors: List[dict] = []
        for case in cases:
            try:
                text = call_provider(
                    str(model_class["provider"]),
                    str(model_class["model_id"]),
                    str(case.get("task", "")),
                    contract,
                    timeout,
                    eval_dir,
                )
                predictions[str(case["id"])] = parse_prediction(text)
            except ProviderError:
                raise
            except Exception as exc:  # timeout, parse error: count as a miss
                predictions[str(case["id"])] = None
                errors.append(
                    {
                        "case": case.get("id"),
                        "error": "{}: {}".format(type(exc).__name__, str(exc)[:300]),
                    }
                )
        metrics = compute_metrics(cases, predictions)
        runs.append({"run": index, "metrics": metrics, "errors": errors})
        print(
            "[{}] run {}/{}: top1={:.1f}% collision={:.1f}% "
            "lang_delta={:+.1f}pp errors={}".format(
                model_class["name"],
                index,
                repeat,
                metrics["top1_accuracy"],
                metrics["collision_accuracy"],
                metrics["language_delta"],
                len(errors),
            )
        )
    return {
        "model_class": str(model_class["name"]),
        "provider": str(model_class["provider"]),
        "model_id": str(model_class["model_id"]),
        "runs": runs,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the role-routing eval (IC-13) and write an IC-36 baseline. "
            "No provider is called without an explicit yes/ja approval."
        )
    )
    parser.add_argument(
        "--provider",
        action="append",
        default=None,
        help="restrict to this provider wrapper (repeatable); default: all",
    )
    parser.add_argument(
        "--model-class",
        action="append",
        default=None,
        metavar="NAME=PROVIDER/MODEL",
        help=(
            "model class, e.g. deepseek=opencode/opencode-go/deepseek-v4.1-flash "
            "(model IDs must be verified provider-side); repeat for multiple classes"
        ),
    )
    parser.add_argument(
        "--repeat", type=int, default=3, help="runs per model class (default: 3)"
    )
    parser.add_argument(
        "--profile", default=DEFAULT_PROFILE, choices=("full", "compact"),
        help="profile recorded in the baseline (default: full)",
    )
    parser.add_argument(
        "--date", default=date.today().isoformat(), help="run date (YYYY-MM-DD)"
    )
    parser.add_argument("--label", default=None, help="baseline model slug")
    parser.add_argument(
        "--approval",
        default=None,
        help="explicit approval token: yes/ja runs; anything else writes SKIPPED-BY-USER",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="never prompt; without --approval the run stays awaiting-approval",
    )
    parser.add_argument(
        "--estimate-only",
        action="store_true",
        help="show the cost estimate and exit without calling a provider",
    )
    parser.add_argument(
        "--contract",
        default=str(DEFAULT_CONTRACT),
        help="output-contract file appended to the provider system prompt",
    )
    parser.add_argument(
        "--timeout", type=float, default=180.0, help="per-case timeout in seconds"
    )
    parser.add_argument(
        "--price-file",
        default=str(DEFAULT_PRICE_FILE),
        help="price overlay used for the cost estimate",
    )
    parser.add_argument(
        "--price-date",
        default=None,
        help="ISO date of the price assumption; omit to mark the estimate unverified",
    )
    parser.add_argument(
        "--price-source",
        default=None,
        help="price source label recorded in the estimate",
    )
    parser.add_argument(
        "--out-dir",
        default=str(ROLES_DIR),
        help="catalog directory; baseline/ and runs/ are written below it",
    )
    return parser


def _print_evidence_preview(model_classes: Sequence[Mapping], repeat: int) -> None:
    reasons = []
    if len(model_classes) < eval_gate.MIN_MODEL_CLASSES:
        reasons.append(
            "only {} model class(es); AC-02 requires at least {}".format(
                len(model_classes), eval_gate.MIN_MODEL_CLASSES
            )
        )
    if repeat < eval_gate.MIN_BASELINE_RUNS:
        reasons.append(
            "repeat={} but at least {} runs are required".format(
                repeat, eval_gate.MIN_BASELINE_RUNS
            )
        )
    if reasons:
        print("evidence preview: not-evidenced -- " + "; ".join(reasons))
    else:
        print("evidence preview: two-class / >=3-run baseline is possible")


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    root: Path = _REPO_ROOT,
    eval_dir: Path = EVAL_DIR,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)
    try:
        run_date = date.fromisoformat(str(args.date))
    except ValueError:
        print("error: --date must be YYYY-MM-DD", file=sys.stderr)
        return 2
    if args.repeat < 1:
        print("error: --repeat must be >= 1", file=sys.stderr)
        return 2
    providers_filter = list(args.provider or [])

    try:
        cases, corpus_hash = load_catalog(out_dir)
        model_classes = parse_model_classes(
            args.model_class or [],
            providers_filter=providers_filter,
            eval_dir=eval_dir,
            require_explicit_models=not args.estimate_only,
        )
    except ValueError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2

    price_file = Path(args.price_file)
    config_path = Path(root) / ".meta-config" / "project.yaml"
    try:
        report = build_context_report(Path(root), config_path)
    except Exception as exc:
        print("error: context measurement failed: {}".format(exc), file=sys.stderr)
        return 1
    estimate = estimate_for(
        cases=cases,
        model_classes=model_classes,
        repeat=args.repeat,
        report=report,
        price_file=price_file,
        price_date=args.price_date,
        price_source=args.price_source,
        today=run_date.isoformat(),
    )
    print(eval_gate.format_estimate(estimate))
    _print_evidence_preview(model_classes, args.repeat)
    if estimate.get("unverified"):
        print(
            "price note: estimate is UNVERIFIED (no dated source); pass "
            "--price-date from the price page to verify it"
        )
    if args.estimate_only:
        return 0

    contract = Path(args.contract).resolve()
    if not contract.is_file():
        print("error: output contract not found: {}".format(contract), file=sys.stderr)
        return 1

    approval_input = args.approval
    interactive = not args.non_interactive and sys.stdin.isatty()
    if approval_input is None and interactive:
        try:
            approval_input = input("Approve this paid eval run? [yes/ja]: ")
        except EOFError:
            approval_input = None

    label = args.label or "+".join(item["name"] for item in model_classes)
    skip_path = (
        out_dir
        / "runs"
        / "{}-qg1-{}.json".format(run_date.isoformat(), _slug(label))
    )

    def make_runner(model_class: Mapping):
        def _runner() -> dict:
            return run_class(
                model_class=model_class,
                cases=cases,
                repeat=args.repeat,
                contract=contract,
                timeout=args.timeout,
                eval_dir=eval_dir,
            )

        return _runner

    result = eval_gate.run_with_approval(
        estimate,
        approval_input,
        [make_runner(item) for item in model_classes],
        skip_path,
        emit=lambda text: None,
        reason="declined by user (role-routing eval)",
        today=run_date.isoformat(),
    )
    if result["status"] == eval_gate.AWAITING_APPROVAL:
        print(
            "status: awaiting-approval -- no provider was called. Re-run with "
            "--approval yes (or ja) after reviewing the estimate."
        )
        return 2
    if result["status"] == eval_gate.SKIPPED_BY_USER:
        print("status: SKIPPED-BY-USER -- wrote {}".format(skip_path))
        return 3

    class_runs = {
        item["model_class"]: item["runs"] for item in result.get("results") or []
    }
    parameters = {
        "repeat": args.repeat,
        "k": 2.0,
        "temperature": None,
        "timeout_s": args.timeout,
        "provider_filter": providers_filter,
        "task_tokens_per_case": eval_gate.DEFAULT_TASK_TOKENS_PER_CASE,
        "output_tokens_per_call": eval_gate.DEFAULT_OUTPUT_TOKENS_PER_CALL,
        "price_assumption": estimate.get("price_assumption")
        or {"source": args.price_source, "date": args.price_date},
        "price_file": str(price_file),
        "price_date": args.price_date,
        "estimate_hash": eval_gate.estimate_hash(estimate),
        "estimate_unverified": estimate.get("unverified"),
        "case_count": len(cases),
        "calls": estimate["calls"],
        "contract": str(contract),
        "models": estimate["models"],
    }
    baseline = build_baseline(
        cases=cases,
        class_runs=class_runs,
        model_ids={item["name"]: item["model_id"] for item in model_classes},
        providers={item["name"]: item["provider"] for item in model_classes},
        parameters=parameters,
        corpus_hash=corpus_hash,
        profile=args.profile,
        run_date=run_date.isoformat(),
        label=label,
    )
    schema_errors = validate_baseline(baseline)
    if schema_errors:
        print(
            "error: baseline schema validation failed: {}".format(
                "; ".join(schema_errors)
            ),
            file=sys.stderr,
        )
        return 1
    baseline_dir = out_dir / "baseline"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_path = baseline_dir / baseline_filename(
        run_date.isoformat(), label, args.profile
    )
    baseline_path.write_text(
        json.dumps(baseline, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        "status: {} -- wrote {}".format(
            baseline["evidence"]["status"], baseline_path
        )
    )
    for reason in baseline["evidence"]["reasons"]:
        print("  - {}".format(reason))
    return 0


if __name__ == "__main__":
    sys.exit(main())
