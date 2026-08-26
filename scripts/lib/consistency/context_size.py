"""Provider context file size guard (issue #540, Phase C2).

Warns when a sync-generated provider context file (CLAUDE.md, AGENTS.md,
MAMMOUTH.md, ...) exceeds a soft line limit without explicit acknowledgment.
This is a WARNING-level signal, never an error: oversized context files are
a compression target (#540), not a hard failure.

Acknowledgment lives in .meta-config/project.yaml::

    context_file:
      max_lines: 250                  # soft limit (default: 250)
      oversize_acknowledged: true     # suppresses the warning for ALL files

Files without the agent-meta managed-block marker are not sync output and
are therefore never reported.
"""

from __future__ import annotations

from pathlib import Path

from .report import Finding, Severity

DEFAULT_MAX_LINES = 250
_PROJECT_CONFIG = ".meta-config/project.yaml"
# Substring marker of a sync-generated managed region (context.py writes
# "<!-- agent-meta:managed-begin -->"; substring match tolerates whitespace
# variants and keeps this module independent of context.py internals).
_MANAGED_MARKER = "agent-meta:managed-begin"


def _load_project_config(root: Path) -> dict:
    """Load the full project config from root. Returns {} on absence.

    Uses the shared lenient loader so a missing PyYAML install or a missing
    project.yaml degrades to "no guard config" instead of crashing the suite.
    """
    from ..io import _load_yaml_or_json

    config, _ = _load_yaml_or_json(root / _PROJECT_CONFIG)
    return config


def check_context_file_size(
    root: Path,
    config: dict | None = None,
    provider_config: dict | None = None,
) -> list[Finding]:
    """Warn when generated provider context files exceed the line limit.

    Args:
        root: Project root that holds both the generated context files and
            .meta-config/project.yaml (self-hosted agent-meta layout).
        config: Pre-loaded project config dict. Loaded from ``root`` when None
            (injection keeps the check unit-testable without fixtures).
        provider_config: Pre-loaded ai-providers mapping. Loaded via
            lib.providers when None.

    Returns:
        Findings with Severity.WARNING — at most one per distinct file.
    """
    findings: list[Finding] = []

    if config is None:
        config = _load_project_config(root)
    cfg = config.get("context_file")
    cfg = cfg if isinstance(cfg, dict) else {}

    max_lines = cfg.get("max_lines", DEFAULT_MAX_LINES)
    if not isinstance(max_lines, int) or isinstance(max_lines, bool) or max_lines < 1:
        max_lines = DEFAULT_MAX_LINES
    acknowledged = cfg.get("oversize_acknowledged", False) is True

    if acknowledged:
        return findings

    if provider_config is None:
        from ..providers import load_providers_config, resolve_providers

        provider_config = load_providers_config(root)
        active = resolve_providers(config, provider_config)
    else:
        # Injected mapping (tests): treat every entry as active so the guard
        # stays decoupled from provider-deactivation semantics.
        active = [p for p in provider_config
                  if isinstance(provider_config[p], dict)]

    # Several providers may share one context file (Gemini + Opencode both
    # write AGENTS.md) — report each distinct file exactly once.
    seen_paths: set[Path] = set()
    for provider in active:
        pc = provider_config.get(provider)
        if not isinstance(pc, dict):
            continue
        rel = pc.get("context_file")
        if not rel:
            continue
        path = (root / rel).resolve()
        if path in seen_paths or not path.is_file():
            continue
        seen_paths.add(path)

        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if _MANAGED_MARKER not in content:
            continue  # hand-written file, not sync output

        lines = content.splitlines()
        if len(lines) <= max_lines:
            continue

        findings.append(Finding(
            severity=Severity.WARNING,
            check="context.size_guard",
            file=rel,
            message=(
                f"Generated context file has {len(lines)} lines "
                f"(limit: {max_lines}) without acknowledged oversize"
            ),
            suggestion=(
                f"Reduce the file size (context_file.mode: compact, issue #540), "
                f"raise context_file.max_lines, or set "
                f"context_file.oversize_acknowledged: true in {_PROJECT_CONFIG}."
            ),
        ))

    return findings
