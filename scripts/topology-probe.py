#!/usr/bin/env python3
"""Read-only orchestrator-topology probe harness (issue #1077, P0).

One probe per provider answers — or explicitly cannot answer — the question
from the orchestrator-topology design §16 Nr. 2–6 and emits one structured
record per probe. The harness is the evidence source for
``docs/spikes/2026-11-03-issue-1077-topology-probe.md`` (Task 3); it never
upgrades a capability cell on its own.

Safety contract
---------------
* **Read-only.** The script reads ``.meta-config/project.yaml`` (for the
  tmp-sink env pin) and starts the provider CLI's own read-only
  ``--version`` / ``--help`` / ``agent list`` command. It never calls
  ``sync.py``, never starts an interactive session and never touches the
  network beyond what that CLI command does.
* **Bounded.** Every child process is killed after ``--timeout`` seconds
  (default 20).
* **No silent writes.** The only file it ever writes is the optional
  ``--out`` path.
* **Absence is a result.** A missing CLI yields exactly
  ``not run — CLI unavailable`` with the reason in ``observed``; exit code 0.
* **No guessing.** A probe whose question cannot be observed by a
  non-interactive command stays ``inconclusive`` even when the CLI runs
  cleanly; only a descriptor with an explicit evidence pattern can return
  ``evidence``.

Record (JSON object, one per probe)
-----------------------------------
``provider``, ``probe_id``, ``question``, ``cli_path``, ``command``,
``exit_code``, ``result`` (``evidence`` | ``not run — CLI unavailable`` |
``inconclusive``), ``observed``, ``timestamp``, ``provider_version``.

Usage
-----
    python3 scripts/topology-probe.py --list
    python3 scripts/topology-probe.py --probe P0-2 --dry-run
    python3 scripts/topology-probe.py --out .tmp/topology-probes.json
    python3 scripts/topology-probe.py --only Opencode --only P0-5
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple

_SCRIPTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

#: Hard ceiling per child process (seconds). Modest on purpose: a probe is a
#: read-only diagnostic, never a model turn.
PROBE_TIMEOUT_SECONDS = 20

#: Maximum length of the factual ``observed`` line.
_OBSERVED_LIMIT = 240

NOT_RUN = "not run — CLI unavailable"
EVIDENCE = "evidence"
INCONCLUSIVE = "inconclusive"

_RESULTS = (EVIDENCE, NOT_RUN, INCONCLUSIVE)


@dataclass(frozen=True)
class ProbeDescriptor:
    """Static description of one probe question.

    ``answerable`` + ``evidence_pattern`` encode what a *non-interactive*
    command can actually prove. When ``answerable`` is false the harness still
    runs the safe diagnostic (to capture the provider version and raw output)
    but must not label the run as evidence.
    """

    probe_id: str
    provider: str
    cli: str
    question: str
    args: Tuple[str, ...]
    answerable: bool = False
    evidence_pattern: Optional[str] = None
    unanswerable_reason: str = ""


# Design §16 Nr. 2–6, in order. Probe IDs are stable: Task 3 records them.
PROBES: Tuple[ProbeDescriptor, ...] = (
    ProbeDescriptor(
        probe_id="P0-1",
        provider="Opencode",
        cli="opencode",
        question=(
            "Is a mode: primary role additionally spawnable via "
            "task(subagent_type: \"orchestrator\")?"
        ),
        args=("agent", "list"),
        unanswerable_reason=(
            "task(subagent_type) spawnability cannot be observed by a "
            "non-interactive agent listing"
        ),
    ),
    ProbeDescriptor(
        probe_id="P0-2",
        provider="Claude",
        cli="claude",
        question=(
            "Is `claude --agent orchestrator` a primary with the same main-chat "
            "context identity and hook-payload semantics?"
        ),
        args=("--help",),
        unanswerable_reason=(
            "context identity and hook-payload semantics cannot be observed by "
            "a non-interactive command"
        ),
    ),
    ProbeDescriptor(
        probe_id="P0-3",
        provider="Codex",
        cli="codex",
        question=(
            "Is main_agent_selectable true, and which mechanism selects the "
            "main agent?"
        ),
        args=("--help",),
        unanswerable_reason=(
            "the main-agent selection mechanism is not observable from a "
            "non-interactive help/version run"
        ),
    ),
    ProbeDescriptor(
        probe_id="P0-4",
        provider="Mammouth",
        cli="mammouth",
        question=(
            "Does Mammouth support mode: primary / default_agent for an "
            "orchestrator entry point?"
        ),
        args=("agent", "list"),
        unanswerable_reason=(
            "config-key support is not observable from a non-interactive "
            "agent listing"
        ),
    ),
    ProbeDescriptor(
        probe_id="P0-5",
        provider="KimiCode",
        cli="kimi",
        question=(
            "Which mechanism selects the main agent: a CLI flag or a config "
            "field?"
        ),
        args=("--help",),
        answerable=True,
        evidence_pattern=r"--agent(?:\s+<[^>]+>)?",
    ),
)


def timestamp_utc() -> str:
    """Stable ISO-8601 UTC timestamp for a record."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _short(text: str, limit: int = _OBSERVED_LIMIT) -> str:
    """Collapse whitespace and truncate for the one-line ``observed`` field."""
    collapsed = " ".join((text or "").split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1].rstrip() + "…"


def _first_line(text: str) -> str:
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


def _probe_tmp_env(project_root: Optional[Path] = None) -> dict:
    """Return the inherited environment with the tmp-sink pin merged in.

    Mirrors the framework's AC-11 contract for subprocess starts
    (``scripts/**``): when the repo config resolves an enabled tmp sink, its
    ``TMPDIR``/``TEMP``/``TMP`` values win; otherwise the caller environment is
    inherited unchanged. Resolution is deliberately read-only — unlike
    ``lib.tmp_paths.tmp_env`` it never provisions a directory, because this
    harness must not create files.
    """
    env = dict(os.environ)
    root = Path(project_root) if project_root is not None else _REPO_ROOT
    try:
        from lib.io import load_yaml_file
        from lib.tmp_paths import resolve_tmp_paths

        config_path = root / ".meta-config" / "project.yaml"
        config = load_yaml_file(config_path) if config_path.is_file() else {}
        paths = resolve_tmp_paths(root, config if isinstance(config, dict) else {})
        env.update(paths.env)
    except Exception:
        # A read-only probe must never fail because tmp-sink resolution does.
        return env
    return env


def _run(
    argv: Sequence[str],
    *,
    timeout: float,
    runner: Callable,
    env: dict,
) -> Tuple[Optional[int], str, str, bool, str]:
    """Start *argv*, bounded by *timeout*.

    Returns ``(exit_code, stdout, stderr, timed_out, exec_error)``. ``env`` is
    derived from :func:`_probe_tmp_env`, satisfying the framework's
    subprocess-pin convention without creating any directory.
    """
    try:
        completed = runner(
            list(argv),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return None, "", "", True, ""
    except OSError as exc:
        return None, "", "", False, f"could not execute {argv[0]}: {exc}"
    return (
        completed.returncode,
        completed.stdout or "",
        completed.stderr or "",
        False,
        "",
    )


def _provider_version(
    cli_path: str, *, timeout: float, runner: Callable, env: dict
) -> str:
    """Best-effort ``<cli> --version`` (read-only, bounded, never fatal)."""
    exit_code, stdout, stderr, timed_out, exec_error = _run(
        [cli_path, "--version"], timeout=timeout, runner=runner, env=env
    )
    if timed_out or exec_error or exit_code != 0:
        return ""
    return _first_line(stdout) or _first_line(stderr)


def classify(
    descriptor: ProbeDescriptor,
    *,
    exit_code: Optional[int],
    stdout: str,
    stderr: str,
    timed_out: bool,
    exec_error: str,
    timeout: float,
) -> Tuple[str, str]:
    """Map a finished run onto ``(result, observed)`` without guessing."""
    if timed_out:
        return INCONCLUSIVE, f"timeout after {timeout:g}s"
    if exec_error:
        return INCONCLUSIVE, _short(exec_error)
    combined = "\n".join(part for part in (stdout, stderr) if part)
    if exit_code != 0:
        detail = _short(combined) or "no output"
        return INCONCLUSIVE, f"exit {exit_code}: {detail}"

    if descriptor.answerable and descriptor.evidence_pattern:
        match = re.search(
            descriptor.evidence_pattern, combined, re.IGNORECASE | re.MULTILINE
        )
        if match is None:
            detail = _short(_first_line(combined)) or "no output"
            return (
                INCONCLUSIVE,
                f"evidence pattern {descriptor.evidence_pattern!r} not found; {detail}",
            )
        return EVIDENCE, f"matched {match.group(0)!r} in CLI output"

    reason = (
        descriptor.unanswerable_reason
        or "question is not answerable by a non-interactive command"
    )
    first = _short(_first_line(combined))
    if first:
        return INCONCLUSIVE, f"{reason}; CLI output: {first}"
    return INCONCLUSIVE, reason


def _record(
    descriptor: ProbeDescriptor,
    *,
    cli_path: Optional[str],
    command: Sequence[str],
    exit_code: Optional[int],
    result: str,
    observed: str,
    provider_version: str,
) -> dict:
    return {
        "provider": descriptor.provider,
        "probe_id": descriptor.probe_id,
        "question": descriptor.question,
        "cli_path": cli_path,
        "command": list(command),
        "exit_code": exit_code,
        "result": result,
        "observed": observed,
        "timestamp": timestamp_utc(),
        "provider_version": provider_version,
    }


def run_probe(
    descriptor: ProbeDescriptor,
    *,
    which: Callable[[str], Optional[str]] = shutil.which,
    runner: Callable = subprocess.run,
    timeout: float = PROBE_TIMEOUT_SECONDS,
    project_root: Optional[Path] = None,
) -> dict:
    """Run one probe and return its structured record.

    A missing binary is a valid outcome, never an error.
    """
    cli_path = which(descriptor.cli)
    command = [cli_path or descriptor.cli, *descriptor.args]
    if cli_path is None:
        return _record(
            descriptor,
            cli_path=None,
            command=command,
            exit_code=None,
            result=NOT_RUN,
            observed=f"{descriptor.cli} not found on PATH",
            provider_version="",
        )

    env = _probe_tmp_env(project_root)
    version = _provider_version(
        cli_path, timeout=timeout, runner=runner, env=env
    )
    exit_code, stdout, stderr, timed_out, exec_error = _run(
        command, timeout=timeout, runner=runner, env=env
    )
    result, observed = classify(
        descriptor,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
        exec_error=exec_error,
        timeout=timeout,
    )
    return _record(
        descriptor,
        cli_path=cli_path,
        command=command,
        exit_code=exit_code,
        result=result,
        observed=observed,
        provider_version=version,
    )


def run_probes(
    descriptors: Sequence[ProbeDescriptor],
    *,
    which: Callable[[str], Optional[str]] = shutil.which,
    runner: Callable = subprocess.run,
    timeout: float = PROBE_TIMEOUT_SECONDS,
    project_root: Optional[Path] = None,
) -> list:
    """Run *descriptors* in order and return one record each."""
    return [
        run_probe(
            descriptor,
            which=which,
            runner=runner,
            timeout=timeout,
            project_root=project_root,
        )
        for descriptor in descriptors
    ]


def _split_tokens(values: Optional[Sequence[str]]) -> list:
    tokens = []
    for value in values or ():
        tokens.extend(part.strip() for part in value.split(",") if part.strip())
    return tokens


def select_probes(
    probe_ids: Optional[Sequence[str]] = None,
    only: Optional[Sequence[str]] = None,
    descriptors: Sequence[ProbeDescriptor] = PROBES,
) -> list:
    """Filter descriptors by probe id (``--probe``) or provider/id (``--only``)."""
    selected = list(descriptors)
    if probe_ids:
        wanted = {token.upper() for token in _split_tokens(probe_ids)}
        known = {descriptor.probe_id.upper() for descriptor in descriptors}
        unknown = sorted(wanted - known)
        if unknown:
            raise ValueError(
                f"unknown probe id(s): {', '.join(unknown)}; "
                f"known: {', '.join(sorted(known))}"
            )
        selected = [
            descriptor
            for descriptor in selected
            if descriptor.probe_id.upper() in wanted
        ]
    if only:
        tokens = {token.lower() for token in _split_tokens(only)}
        selected = [
            descriptor
            for descriptor in selected
            if descriptor.provider.lower() in tokens
            or descriptor.probe_id.lower() in tokens
        ]
    return selected


def _format_argv(argv: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in argv)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="topology-probe.py",
        description=(
            "Read-only probe harness for the orchestrator-topology P0 questions "
            "(issue #1077). Emits one JSON record per provider; never starts an "
            "interactive session."
        ),
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list the five probes (id, provider, question) and exit",
    )
    parser.add_argument(
        "--probe",
        action="append",
        metavar="ID",
        help="run only this probe id (repeatable, comma-separated accepted)",
    )
    parser.add_argument(
        "--only",
        action="append",
        metavar="PROVIDER|ID",
        help="filter by provider or probe id (repeatable, comma-separated accepted)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the exact argv per selected probe; run nothing",
    )
    parser.add_argument(
        "--out",
        metavar="PATH",
        help="write the JSON records to PATH instead of stdout (no other writes)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=PROBE_TIMEOUT_SECONDS,
        metavar="SECONDS",
        help=f"per-child-process timeout (default: {PROBE_TIMEOUT_SECONDS})",
    )
    return parser


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    which: Callable[[str], Optional[str]] = shutil.which,
    runner: Callable = subprocess.run,
    project_root: Optional[Path] = None,
    stdout=None,
) -> int:
    """CLI entry point. Always returns 0 for a valid run (even if absent)."""
    out_stream = stdout if stdout is not None else sys.stdout
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.list:
        for descriptor in PROBES:
            print(
                f"{descriptor.probe_id}\t{descriptor.provider}\t{descriptor.question}",
                file=out_stream,
            )
        return 0

    try:
        selected = select_probes(args.probe, args.only)
    except ValueError as exc:
        parser.error(str(exc))

    if args.dry_run:
        for descriptor in selected:
            cli_path = which(descriptor.cli) or descriptor.cli
            print(
                f"{descriptor.probe_id}: {_format_argv([cli_path, *descriptor.args])}",
                file=out_stream,
            )
        return 0

    records = run_probes(
        selected,
        which=which,
        runner=runner,
        timeout=args.timeout,
        project_root=project_root,
    )
    payload = json.dumps(records, indent=2, ensure_ascii=False) + "\n"

    if args.out:
        try:
            Path(args.out).write_text(payload, encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: cannot write {args.out}: {exc}", file=sys.stderr)
            return 2
    else:
        out_stream.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
