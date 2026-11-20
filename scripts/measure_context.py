#!/usr/bin/env python3
"""Measure generated provider context files (lines, bytes, approximated tokens).

Part of the issue #540 context compression plan (Phase A2). Discovers the
provider context files declared in ``config/ai-providers.yaml`` (e.g.
AGENTS.md, CLAUDE.md, GEMINI.md, MAMMOUTH.md), skips files that do not exist,
and reports line count, byte size and approximated tokens (bytes / 4) per file
plus a totals row. An optional positional path measures an extra target file.

Stdlib only — the provider config is parsed with a line regex instead of a
YAML library so the script runs in any bare Python 3.8+ environment.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import agent_report  # noqa: E402 -- per-role measurement (Task 1.1)
from lib.context_report import (  # noqa: E402 -- shared measurement function (IC-11)
    count_text_stats,
    measure_artifacts,
    merge_provider_mappings,
    render_table as render_artifact_table,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

PROVIDERS_CONFIG = "config/ai-providers.yaml"

#: Default rendered agent directory for ``--per-agent`` (OQ-4).
AUTO_AGENTS_DIR = ".claude/agents"

CONTEXT_FILE_PATTERN = re.compile(r"^\s*context_file:\s*[\"']?([^\s\"'#]+)", re.MULTILINE)

FALLBACK_CONTEXT_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "MAMMOUTH.md",
)

BYTES_PER_TOKEN = 4


def discover_context_files(repo_root: Path) -> list[str]:
    """Return the deduplicated context file paths declared for all providers.

    Reads ``config/ai-providers.yaml`` with a regex scan; falls back to a
    static list of well-known root-level context files if the config is
    missing or declares nothing.

    Args:
        repo_root: Repository root containing the agent-meta checkout.

    Returns:
        Repo-root-relative context file paths, first declaration first.
    """
    config_path = repo_root / PROVIDERS_CONFIG
    if config_path.exists():
        matches = CONTEXT_FILE_PATTERN.findall(config_path.read_text(encoding="utf-8"))
    else:
        matches = []
    if not matches:
        matches = list(FALLBACK_CONTEXT_FILES)
    seen: set[str] = set()
    ordered: list[str] = []
    for path in matches:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def measure_file(path: Path) -> dict[str, object]:
    """Measure one context file.

    Args:
        path: Existing, readable file path.

    Returns:
        Dict with ``path``, ``lines``, ``bytes`` and ``tokens_approx`` keys.
        ``path`` is relative to the repository root when possible.
    """
    content = path.read_bytes()
    try:
        display_path = str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        display_path = str(path)
    stats = count_text_stats(content)
    return {
        "path": display_path,
        "lines": stats["lines"],
        "bytes": stats["bytes"],
        "tokens_approx": stats["tokens_est"],
    }


def resolve_path(repo_root: Path, candidate: str) -> Path:
    """Resolve a candidate path against the repository root.

    Args:
        repo_root: Repository root containing the agent-meta checkout.
        candidate: Repo-root-relative or absolute file path.

    Returns:
        Absolute path for the candidate.
    """
    path = Path(candidate)
    if not path.is_absolute():
        path = repo_root / path
    return path


def collect_measurements(repo_root: Path, extra_target: str | None) -> list[dict[str, object]]:
    """Measure every existing context file plus an optional extra target.

    Missing default candidates are silently skipped as specified by plan task
    A2; a missing extra target is an error because it was requested explicitly.

    Args:
        repo_root: Repository root containing the agent-meta checkout.
        extra_target: Optional additional file path to measure.

    Returns:
        Measurement dicts, one per measured file, in discovery order with the
        extra target appended last when given.

    Raises:
        FileNotFoundError: The extra target was given but does not exist.
    """
    results: list[dict[str, object]] = []
    for candidate in discover_context_files(repo_root):
        path = resolve_path(repo_root, candidate)
        if path.is_file():
            results.append(measure_file(path))
    if extra_target is not None:
        path = resolve_path(repo_root, extra_target)
        if not path.is_file():
            raise FileNotFoundError(f"target not found: {extra_target}")
        results.append(measure_file(path))
    return results


def render_table(measurements: list[dict[str, object]]) -> str:
    """Render measurements as an aligned ASCII table with a totals row.

    Args:
        measurements: Measurement dicts as returned by ``collect_measurements``.

    Returns:
        Multi-line table string without a trailing newline.
    """
    headers = ("File", "Lines", "Bytes", "Tokens (~)")
    rows = [
        (
            str(m["path"]),
            str(m["lines"]),
            str(m["bytes"]),
            str(m["tokens_approx"]),
        )
        for m in measurements
    ]
    total_lines = sum(int(m["lines"]) for m in measurements)
    total_bytes = sum(int(m["bytes"]) for m in measurements)
    total_tokens = sum(int(m["tokens_approx"]) for m in measurements)
    rows.append(("TOTAL", str(total_lines), str(total_bytes), str(total_tokens)))
    widths = [max(len(headers[i]), *(len(r[i]) for r in rows)) for i in range(len(headers))]
    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
    separator = "-+-".join("-" * w for w in widths)
    body = "\n".join(" | ".join(c.ljust(w) for c, w in zip(row, widths)) for row in rows)
    return "\n".join((header_line, separator, body))


def build_json(measurements: list[dict[str, object]]) -> dict[str, object]:
    """Build the machine-readable report structure.

    Args:
        measurements: Measurement dicts as returned by ``collect_measurements``.

    Returns:
        Dict with ``files`` and aggregated ``totals`` entries.
    """
    return {
        "files": measurements,
        "totals": {
            "files": len(measurements),
            "lines": sum(int(m["lines"]) for m in measurements),
            "bytes": sum(int(m["bytes"]) for m in measurements),
            "tokens_approx": sum(int(m["tokens_approx"]) for m in measurements),
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        Parsed namespace with ``target`` and ``json`` attributes.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Measure generated provider context files "
            "(lines, bytes, approximated tokens)."
        )
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="optional additional file to measure (missing defaults are skipped)",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="measure the rendered artifacts of a project per provider "
        "(same function as sync.py --context-report)",
    )
    parser.add_argument(
        "--per-agent",
        action="store_true",
        help="measure rendered agent roles per provider "
        "(requires --project; reads <project>/" + AUTO_AGENTS_DIR + ")",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of a table",
    )
    return parser.parse_args(argv)


def run_project_report(project: Path, as_json: bool) -> int:
    """Report per-provider artifact sizes of *project* via ``measure_artifacts``."""
    from lib.config import load_config
    from lib.providers import (
        load_provider_capabilities,
        load_providers_config,
        resolve_providers,
    )

    config_path = project / ".meta-config" / "project.yaml"
    if not config_path.is_file():
        print(f"error: no project config at {config_path}", file=sys.stderr)
        return 1
    config = load_config(config_path)
    provider_config = load_providers_config(REPO_ROOT, config)
    providers = resolve_providers(config, provider_config)
    mappings = merge_provider_mappings(
        provider_config, load_provider_capabilities(REPO_ROOT))
    report = measure_artifacts(project, providers, mappings)
    if not report:
        print("error: no provider context files found", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2) if as_json else render_artifact_table(report))
    return 0


def _empty_stat() -> dict:
    return {"bytes": 0, "lines": 0, "tokens_est": 0}


def _add_file(acc: dict, path: Path) -> None:
    if path.is_file():
        stats = count_text_stats(path.read_bytes())
        for key in acc:
            acc[key] += stats[key]


def _to_approx(acc: dict) -> dict:
    return {
        "bytes": acc["bytes"],
        "lines": acc["lines"],
        "tokens_approx": acc["bytes"] // 4,
    }


def _measure_always_on(agents_dir: Path) -> dict:
    """Measure the three always-on components (OQ-3), provider-agnostically.

    ``entry-file`` comes from the context files discovered in the project root;
    ``rules`` from the sibling ``rules/`` directory; ``descriptions`` from the
    frontmatter description lines of the rendered role files. No provider name
    is branched on.
    """
    root = agents_dir.resolve()
    project_root = root.parent.parent
    entry = _empty_stat()
    for relative in discover_context_files(project_root):
        _add_file(entry, resolve_path(project_root, relative))

    rules = _empty_stat()
    rules_dir = root.parent / "rules"
    if rules_dir.is_dir():
        for path in sorted(rules_dir.rglob("*")):
            _add_file(rules, path)

    descriptions = _empty_stat()
    for path in sorted(root.glob("*/*.md")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            if line.lstrip().startswith("description:"):
                raw = line.encode("utf-8")
                descriptions["bytes"] += len(raw)
                descriptions["lines"] += 1
                descriptions["tokens_est"] += len(raw) // 4

    return {
        "entry-file": _to_approx(entry),
        "rules": _to_approx(rules),
        "descriptions": _to_approx(descriptions),
    }


def run_agent_report(agents_dir: str | Path = AUTO_AGENTS_DIR,
                     as_json: bool = False) -> int:
    """Report per-role sizes of *agents_dir* plus a top-level session sum (OQ-2).

    Providers are discovered as the immediate subdirectories of *agents_dir*,
    so behaviour is driven by data rather than hardcoded provider names.
    """
    root = Path(agents_dir)
    if not root.is_dir():
        print(f"error: agents dir not found: {root}", file=sys.stderr)
        return 1
    providers = sorted(child.name for child in root.iterdir() if child.is_dir())
    if not providers:
        print("error: no agent roles found", file=sys.stderr)
        return 1
    try:
        agents = agent_report.measure_agents(root, providers)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    report = agent_report.build_agent_report(agents, _measure_always_on(root))
    print(json.dumps(report, indent=2) if as_json
          else agent_report.render_agent_table(report))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the measurement and print the report.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code: 0 on success, 1 when no context file was found or
        the extra target does not exist, 2 on invalid flag combinations.
    """
    args = parse_args(argv)
    if args.per_agent:
        if args.project is None:
            print("error: --per-agent requires --project", file=sys.stderr)
            return 2
        agents_dir = Path(args.project) / AUTO_AGENTS_DIR
        return run_agent_report(agents_dir, args.json)
    if args.project is not None:
        return run_project_report(Path(args.project), args.json)
    try:
        measurements = collect_measurements(REPO_ROOT, args.target)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not measurements:
        print("error: no provider context files found", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(build_json(measurements), indent=2))
    else:
        print(render_table(measurements))
    return 0


if __name__ == "__main__":
    sys.exit(main())
