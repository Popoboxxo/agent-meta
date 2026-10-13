"""Context-size measurement and the ``--context-report`` CLI mode (IC-11).

``measure_artifacts`` is the single shared measurement function: the CLI
report, ``scripts/measure_context.py`` and the doctor ``file-size`` detector
(IC-22) all use it. It is a pure function of the files on disk plus the
per-provider capability mapping -- no provider names, no rendering.

``run_context_report`` renders the project into a work directory below the
configured tmp-sink (``resolve_work_dir``, IC-34), measures the rendered
artifacts and writes the report into the sink subdir ``context-report``.
It never writes into the project proper and never touches the system temp
directory.

Limitation: the project is rendered by ``sync.py --init`` on a copy of
``project.yaml`` only. Project-local files outside ``.meta-config``
(``.claude/3-project/*-ext.md``, project-owned rules and hooks, the "Eigene
Notizen" section of CLAUDE.md) are absent from the render, so the measurement
can underestimate the real always-loaded footprint.

Exit codes: 0 ok, 1 only for ``context.over-hard-cap``, 2 for tmp-sink errors
and for render failures (``context-report.render-failed``).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Mapping, Optional, Sequence

from lib.rules import CLAUDE_RULES_DIR
from lib.repo_containment import (
    TmpSinkError,
    resolve_output_dir,
    resolve_work_dir,
    work_dir_env,
)

REPORT_SUBDIR = "context-report"
BYTES_PER_TOKEN = 4
DEFAULT_AGENT_EXT = ".md"
ORCHESTRATOR_STEM = "orchestrator"
GIT_INIT_TIMEOUT_S = 60
RENDER_FAILED_CODE = "context-report.render-failed"

# (capability key, cap_kind) in precedence order: a hard cap wins over a soft
# cap, bytes win over chars over lines.
_CAP_KEYS = (
    ("context_hard_cap_bytes", "hard-bytes"),
    ("context_soft_cap_bytes", "soft-bytes"),
    ("context_soft_cap_chars", "soft-chars"),
    ("context_soft_cap_lines", "soft-lines"),
)


def count_text_stats(data: bytes) -> dict:
    """Return ``bytes``, ``lines`` and ``tokens_est`` (bytes // 4) for *data*."""
    text = data.decode("utf-8", errors="replace")
    return {
        "bytes": len(data),
        "lines": len(text.splitlines()),
        "tokens_est": len(data) // BYTES_PER_TOKEN,
    }


def _sum_stats(stats: Sequence[dict]) -> dict:
    return {
        "bytes": sum(s["bytes"] for s in stats),
        "lines": sum(s["lines"] for s in stats),
        "tokens_est": sum(s["tokens_est"] for s in stats),
    }


def _stat_file(path: Path) -> Optional[dict]:
    try:
        return count_text_stats(path.read_bytes())
    except OSError:
        return None


def _stat_dir(path: Path, suffix: Optional[str] = None) -> Optional[dict]:
    if not path.is_dir():
        return None
    stats = []
    for child in sorted(path.iterdir()):
        if child.is_file() and (suffix is None or child.name.endswith(suffix)):
            stat = _stat_file(child)
            if stat is not None:
                stats.append(stat)
    return _sum_stats(stats) if stats else None


def _cap_for(caps: Mapping) -> tuple:
    """Return ``(cap, cap_kind)`` of the first declared cap key, else ``(None, None)``."""
    for key, kind in _CAP_KEYS:
        value = caps.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value, kind
    return None, None


def _entry(stat: dict, cap=None, cap_kind=None) -> dict:
    out = dict(stat)
    out["cap"] = cap
    out["cap_kind"] = cap_kind
    return out


def measure_artifacts(
    project_root: Path,
    active_providers: Sequence[str],
    capabilities: Mapping[str, Mapping],
) -> dict:
    """Measure the context artifacts of every active provider (IC-11).

    ``capabilities[provider]`` is the provider's merged mapping: the cap /
    channel keys of ``config/provider-capabilities.yaml`` (IC-09) plus the
    path keys of ``config/ai-providers.yaml`` (``context_file``, ``agents_dir``,
    ``agent_ext``, ``rules_dir``, ``has_rules``); without ``rules_dir`` rules are skipped
    (``merge_provider_mappings`` supplies it). Artifacts that do not exist
    are omitted.

    Returns ``{provider: {artifact: {bytes, lines, tokens_est, cap, cap_kind}}}``
    with the artifacts ``entry-file``, ``rules``, ``orchestrator``,
    ``harness-roster`` (all agent files, only when ``roster_in_harness``) and
    ``always-loaded`` (entry-file + rules + roster estimate).
    """
    root = Path(project_root)
    report: dict = {}
    for provider in active_providers:
        caps = capabilities.get(provider) or {}
        artifacts: dict = {}
        always: list = []

        context_file = caps.get("context_file")
        entry = _stat_file(root / context_file) if context_file else None
        if entry is not None:
            cap, kind = _cap_for(caps)
            artifacts["entry-file"] = _entry(entry, cap, kind)
            always.append(entry)

        rules_dir = caps.get("rules_dir")
        if caps.get("has_rules") and rules_dir:
            rules = _stat_dir(root / rules_dir)
            if rules is not None:
                artifacts["rules"] = _entry(rules)
                always.append(rules)

        agents_dir = caps.get("agents_dir")
        if agents_dir:
            ext = caps.get("agent_ext") or DEFAULT_AGENT_EXT
            orch = _stat_file(root / agents_dir / (ORCHESTRATOR_STEM + ext))
            if orch is not None:
                artifacts["orchestrator"] = _entry(orch)
            if caps.get("roster_in_harness"):
                roster = _stat_dir(root / agents_dir, ext)
                if roster is not None:
                    artifacts["harness-roster"] = _entry(roster)
                    always.append(roster)

        if always:
            artifacts["always-loaded"] = _entry(_sum_stats(always))
        if artifacts:
            report[provider] = artifacts
    return report


def find_over_hard_cap(report: Mapping[str, Mapping]) -> list:
    """Return ``context.over-hard-cap`` findings as message strings.

    Boundary is inclusive (``bytes >= cap``, IC-06/IC-10): an artifact exactly
    at the hard cap is already truncated by the reader.
    """
    findings = []
    for provider, artifacts in report.items():
        for artifact, stat in artifacts.items():
            if stat.get("cap_kind") == "hard-bytes" and stat["bytes"] >= stat["cap"]:
                findings.append(
                    "context.over-hard-cap: {}/{} {} >= {} bytes".format(
                        provider, artifact, stat["bytes"], stat["cap"]))
    return findings


def merge_provider_mappings(provider_config: Mapping, capabilities: Mapping) -> dict:
    """Merge ai-providers entries with the capability matrix per provider."""
    merged: dict = {}
    for name, entry in (provider_config.get("providers") or provider_config).items():
        if not isinstance(entry, Mapping):
            continue
        combined = dict(entry)
        combined.update(capabilities.get(name) or {})
        if combined.get("has_rules") and not combined.get("rules_dir"):
            # Same fallback sync_rules() applies to rules_dir-less providers.
            combined["rules_dir"] = CLAUDE_RULES_DIR
        merged[name] = combined
    return merged


def render_table(report: Mapping[str, Mapping]) -> str:
    """Render the report as an aligned text table."""
    headers = ("Provider", "Artifact", "Bytes", "Lines", "Tokens(~)", "Cap")
    rows = []
    for provider, artifacts in report.items():
        for artifact, s in artifacts.items():
            cap = "-" if s["cap"] is None else "{} ({})".format(s["cap"], s["cap_kind"])
            rows.append((provider, artifact, str(s["bytes"]), str(s["lines"]),
                         str(s["tokens_est"]), cap))
    widths = [max([len(h)] + [len(r[i]) for r in rows]) for i, h in enumerate(headers)]
    lines = [" | ".join(h.ljust(w) for h, w in zip(headers, widths)),
             "-+-".join("-" * w for w in widths)]
    lines += [" | ".join(c.ljust(w) for c, w in zip(r, widths)) for r in rows]
    return "\n".join(lines)


def _prune_old_work_dirs(output_dir: Path, keep_run_id: str) -> None:
    """Drop work dirs of earlier runs so repeated reports do not accumulate."""
    if not output_dir.is_dir():
        return
    for child in output_dir.iterdir():
        work = child / "work"
        if child.name != keep_run_id and work.is_dir():
            shutil.rmtree(work, ignore_errors=True)


def render_into_work_dir(agent_meta_root: Path, config_path: Path, work_dir: Path) -> None:
    """Render the project config into *work_dir* via the regular sync codepath.

    The sync runs as a subprocess with *work_dir* as cwd and as its temp-dir
    environment, so nothing lands in the real project or in the system temp
    directory (IC-34).
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    cfg_dir = work_dir / ".meta-config"
    cfg_dir.mkdir(exist_ok=True)
    target_cfg = cfg_dir / "project.yaml"
    shutil.copyfile(config_path, target_cfg)
    env = work_dir_env(work_dir)
    sync_script = Path(agent_meta_root) / "scripts" / "sync.py"
    subprocess.run(["git", "init", "-q"], cwd=str(work_dir), check=False,
                   capture_output=True, env=env, timeout=GIT_INIT_TIMEOUT_S)
    result = subprocess.run(
        [sys.executable, str(sync_script), "--config", str(target_cfg), "--init"],
        cwd=str(work_dir), env=env, capture_output=True, text=True, timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError("render failed (rc {}): {}".format(
            result.returncode, (result.stdout + result.stderr)[-800:]))


def run_context_report(
    *,
    project_root: Path,
    agent_meta_root: Path,
    config_path: Path,
    config: dict,
    providers: Sequence[str],
    mappings: Mapping[str, Mapping],
    as_json: bool = False,
    profile: str = "full",
) -> int:
    """Render, measure and report; returns the process exit code (0, 1 over-hard-cap, 2 error)."""
    run_id = "{}-{}".format(datetime.now().strftime("%Y%m%d-%H%M%S"), os.getpid())
    try:
        output_dir = resolve_output_dir(project_root, config, REPORT_SUBDIR)
        work_dir = resolve_work_dir(project_root, config, REPORT_SUBDIR, run_id)
    except TmpSinkError as exc:
        print("error: {}: {}".format(exc.code, exc.message), file=sys.stderr)
        return 2
    if profile != "full":
        print("note: profile '{}' is not implemented yet (Phase 2); "
              "reporting 'full' only".format(profile), file=sys.stderr)
    try:
        render_into_work_dir(agent_meta_root, config_path, work_dir)
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        print("error: {}: {}".format(RENDER_FAILED_CODE, exc), file=sys.stderr)
        return 2
    _prune_old_work_dirs(output_dir, run_id)
    report = measure_artifacts(work_dir, list(providers), mappings)
    if not report:
        print("warning: context-report: no artifacts measured "
              "(empty report); check providers and path mappings", file=sys.stderr)
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    report_dir = output_dir / run_id
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "report.json").write_text(payload + "\n", encoding="utf-8")
    print(payload if as_json else render_table(report))
    over = find_over_hard_cap(report)
    for finding in over:
        print(finding, file=sys.stderr)
    return 1 if over else 0
