"""Per-role x provider measurement for the agent improvement loop (Task 1.1).

Implements SPEC-AGENT-LOOP-BATCH0-2026-11-20 IC-1/IC-1b:

* :func:`measure_agents` returns exactly
  ``{provider: {role: {bytes, lines, tokens_approx}}}``. ``tokens_approx`` is
  the bytes/4 proxy from :func:`lib.context_report.count_text_stats` (no
  tiktoken, ADR-1). Providers are data (arguments / mappings), never literal
  branches (AC-12).
* :func:`session_sum` aggregates only the always-on components
  (``entry-file`` + ``rules`` + ``descriptions``, OQ-3); role bodies present in
  the same view are deliberately ignored.
* :func:`build_agent_report` attaches the result under the reserved
  top-level key ``session-sum`` next to the provider keys (OQ-2, no wrapper).
* :func:`render_agent_table` renders an ASCII table with ``TOTAL`` and
  ``SESSION-SUM`` rows.

Measurement reads rendered agent ``*.md`` files (OQ-4); the directory is
always passed in by the caller, so source-template measurements stay possible.
Stdlib only. No ``print()`` — this module is pure.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

from lib.context_report import count_text_stats

AGENT_EXT = ".md"
SESSION_SUM_KEY = "session-sum"
ALWAYS_ON_COMPONENTS = ("entry-file", "rules", "descriptions")
_NO_ROLES = "no agent roles found"


def _role_stats(path: Path) -> dict:
    """Return the stat triple for one rendered agent file."""
    stats = count_text_stats(path.read_bytes())
    return {
        "bytes": stats["bytes"],
        "lines": stats["lines"],
        "tokens_approx": stats["tokens_est"],
    }


def _measure_provider_dir(provider_dir: Path, ext: str = AGENT_EXT) -> dict:
    """Measure all ``*<ext>`` files directly inside *provider_dir*."""
    roles: dict = {}
    for path in sorted(provider_dir.glob("*" + ext)):
        if path.is_file():
            roles[path.stem] = _role_stats(path)
    return roles


def measure_agents(
    agents_dir,
    providers: Sequence[str],
    mappings: Mapping[str, Mapping] | None = None,
) -> dict:
    """Measure every provider's roles under *agents_dir*.

    Two call shapes are supported:

    * ``measure_agents(agents_dir, providers)`` — the per-agent CLI shape.
      Roles live in ``agents_dir/<provider>/*.md``. A missing base or provider
      directory raises :class:`FileNotFoundError`; no providers raises
      :class:`ValueError`.
    * ``measure_agents(project_root, providers, mappings)`` — the IC-1 shape
      used by the budget-ratchet integration test. Each provider's
      ``mappings[provider]["agents_dir"]`` / ``"agent_ext"`` selects its
      directory relative to *project_root*. A missing directory yields an
      empty mapping for that provider (no crash); no roles at all raises
      :class:`ValueError`.

    Returns the pure ``{provider: {role: {bytes, lines, tokens_approx}}}``
    mapping (AC-1). No provider names are hardcoded.
    """
    if not providers:
        raise ValueError(_NO_ROLES)
    root = Path(agents_dir)
    if mappings is not None:
        return _measure_with_mappings(root, providers, mappings)
    return _measure_single_dir(root, providers)


def _measure_single_dir(root: Path, providers: Sequence[str]) -> dict:
    if not root.is_dir():
        raise FileNotFoundError(f"agents dir not found: {root}")
    report: dict = {}
    for provider in providers:
        provider_dir = root / str(provider)
        if not provider_dir.is_dir():
            raise FileNotFoundError(f"agents dir not found: {provider_dir}")
        report[provider] = _measure_provider_dir(provider_dir)
    if not any(report.values()):
        raise ValueError(_NO_ROLES)
    return report


def _measure_with_mappings(
    root: Path,
    providers: Sequence[str],
    mappings: Mapping[str, Mapping],
) -> dict:
    report: dict = {}
    for provider in providers:
        caps = mappings.get(provider) or {}
        rel = caps.get("agents_dir")
        ext = caps.get("agent_ext") or AGENT_EXT
        provider_dir = (root / rel) if rel else (root / str(provider))
        roles = _measure_provider_dir(provider_dir, ext) if provider_dir.is_dir() else {}
        if roles:
            report[provider] = roles
    if not report:
        raise ValueError(_NO_ROLES)
    return report


def session_sum(
    report: Mapping,
    always_on: Sequence[str] = ALWAYS_ON_COMPONENTS,
) -> dict:
    """Sum only the named always-on components of *report*.

    *report* typically contains both always-on component stats
    (``entry-file``, ``rules``, ``descriptions``) and provider-to-role
    mappings. Only the keys listed in *always_on* contribute; role bodies are
    excluded by construction (OQ-3). A stat missing ``tokens_approx`` falls
    back to ``bytes // 4`` so stats from ``count_text_stats`` (``tokens_est``)
    work unchanged.

    Returns ``{"bytes": int, "lines": int, "tokens_approx": int}``.
    """
    total = {"bytes": 0, "lines": 0, "tokens_approx": 0}
    for key in always_on:
        stat = report.get(key)
        if stat is None:
            continue
        total["bytes"] += int(stat["bytes"])
        total["lines"] += int(stat["lines"])
        total["tokens_approx"] += int(
            stat.get("tokens_approx", int(stat["bytes"]) // 4))
    return total


def build_agent_report(agents: Mapping, always_on: Mapping) -> dict:
    """Attach the always-on sum as a top-level reserved sibling (OQ-2).

    Returns ``{provider: {role: {...}}, "session-sum": {...}}`` — no
    ``"providers"`` wrapper. Provider role entries are present in the view
    passed to :func:`session_sum` but are not part of the sum.
    """
    view = dict(always_on)
    view.update(agents)
    report = dict(agents)
    report[SESSION_SUM_KEY] = session_sum(view, ALWAYS_ON_COMPONENTS)
    return report


def render_agent_table(report: Mapping) -> str:
    """Render the report as an ASCII table with TOTAL and SESSION-SUM rows."""
    headers = ("Provider", "Role", "Bytes", "Lines", "Tokens (~)")
    rows: list = []
    total = {"bytes": 0, "lines": 0, "tokens_approx": 0}
    for provider, roles in report.items():
        if provider == SESSION_SUM_KEY:
            continue
        for role, stat in roles.items():
            rows.append((provider, role, str(stat["bytes"]), str(stat["lines"]),
                         str(stat["tokens_approx"])))
            total["bytes"] += stat["bytes"]
            total["lines"] += stat["lines"]
            total["tokens_approx"] += stat["tokens_approx"]
    rows.append(("TOTAL", "-", str(total["bytes"]), str(total["lines"]),
                 str(total["tokens_approx"])))
    summary = report.get(SESSION_SUM_KEY) or {}
    rows.append(("SESSION-SUM", "-", str(summary.get("bytes", 0)),
                 str(summary.get("lines", 0)),
                 str(summary.get("tokens_approx", 0))))
    widths = [max([len(h)] + [len(r[i]) for r in rows]) for i, h in enumerate(headers)]
    lines = [" | ".join(h.ljust(w) for h, w in zip(headers, widths)),
             "-+-".join("-" * w for w in widths)]
    lines += [" | ".join(c.ljust(w) for c, w in zip(row, widths)) for row in rows]
    return "\n".join(lines)
