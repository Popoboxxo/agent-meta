"""WARNING-only depth-coherence check (PR 0.3 / E-05, O10).

Cross-checks the three delegation-depth notions named in the master roadmap:

* ``orchestrator.delegation.max_depth`` (``.meta-config/project.yaml``) — the
  project's hard delegation ceiling;
* the provider capability ``required_depth`` (``config/provider-capabilities.yaml``) —
  the minimum depth a provider needs for multi-agent dispatch;
* the emitted depth — ``experimental.subagent_depth`` / ``subagent_depth``
  (v2/v1 JSON settings) or ``[agents] max_depth`` (TOML committed config).

A provider whose required depth exceeds either the configured delegation
ceiling or the depth actually emitted is reported as a ``Severity.WARNING``.
The check is read-only, provider-agnostic (no provider name is branched on),
emits at most one finding per check ID and provider, and never raises —
malformed or missing input degrades to the findings collected so far.

The separate ``dispatch-depth-missing`` doctor seed (``config/known-issues.yaml``)
is intentionally left untouched; this is an advisory consistency check, not a
reimplementation of that subsystem.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from .report import Finding, Severity
from ..dispatch_depth import _config_file, required_depth_int
from ..io import safe_path

_PROJECT_CONFIG = ".meta-config/project.yaml"

# Stable check IDs.
CHECK_DELEGATION_BELOW_REQUIRED = "depth-coherence.delegation-below-required"
CHECK_EMITTED_BELOW_REQUIRED = "depth-coherence.emitted-below-required"
CHECK_DELEGATION_BELOW_EMITTED = "depth-coherence.delegation-below-emitted"

# TOML ``[agents] max_depth = N`` (dispatch_depth._render_block).
_MAX_DEPTH_RE = re.compile(r"^\s*max_depth\s*=\s*(\d+)\s*$", re.MULTILINE)


def _positive_int(value) -> Optional[int]:
    """Coerce to a positive int (bool rejected), else ``None``."""
    if isinstance(value, int) and not isinstance(value, bool) and value >= 1:
        return value
    return None


def _emitted_depth(path: Path) -> Optional[int]:
    """Read the emitted depth from a provider config file, else ``None``.

    Supports both documented emission forms: the v2/v1 JSON
    ``experimental.subagent_depth`` / ``subagent_depth`` keys and the TOML
    ``[agents] max_depth`` table. Any read/parse problem is fail-soft.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return None

    try:
        document = json.loads(text)
    except (ValueError, TypeError):
        document = None
    if isinstance(document, dict):
        experimental = document.get("experimental")
        if isinstance(experimental, dict):
            depth = _positive_int(experimental.get("subagent_depth"))
            if depth is not None:
                return depth
        depth = _positive_int(document.get("subagent_depth"))
        if depth is not None:
            return depth

    match = _MAX_DEPTH_RE.search(text)
    if match:
        return _positive_int(int(match.group(1)))
    return None


def _resolve_emitted_depth(root: Path, provider_config: dict, pc: dict) -> Optional[int]:
    """Emitted depth from the same committed config path the writers use.

    ``dispatch_depth.write_dispatch_depth_config`` writes the per-provider
    ``mcp-config.committed-file`` (TOML ``[agents] max_depth``);
    ``opencode_v2_config`` writes ``experimental.subagent_depth`` into the v2
    surface *owner's* committed file. Reading only a provider-local MCP
    committed file misses Claude/Gemini, whose own files carry no depth keys —
    the emitted-below-required branch was unreachable for them. Resolve both
    writer sources through ``io.safe_path`` so an absolute or ``../`` path
    cannot escape the project root. Fail-soft: returns ``None`` when no source
    is readable or carries a depth.
    """
    candidates: list[str] = []
    local = _config_file(pc)
    if isinstance(local, str) and local.strip():
        candidates.append(local)
    try:
        from ..opencode_v2_config import _owned_committed_file
        owner = _owned_committed_file(provider_config)
        if isinstance(owner, str) and owner.strip() and owner not in candidates:
            candidates.append(owner)
    except Exception:  # noqa: BLE001 — optional surface, fail soft
        pass
    for rel in candidates:
        try:
            depth = _emitted_depth(safe_path(root, rel))
        except Exception:  # noqa: BLE001 — unreadable/unsafe path -> skip it
            depth = None
        if depth is not None:
            return depth
    return None


def _append_once(
    findings: list,
    seen: set,
    check: str,
    message: str,
    suggestion: str,
) -> None:
    """Append at most one finding per (check ID, provider) and run."""
    if check in seen:
        return
    seen.add(check)
    findings.append(Finding(
        severity=Severity.WARNING,
        check=check,
        file=_PROJECT_CONFIG,
        message=message,
        suggestion=suggestion,
    ))


def check_depth_coherence(
    root: Path,
    config: dict | None = None,
    provider_config: dict | None = None,
) -> list[Finding]:
    """WARNING findings for depth incoherence across the three depth notions.

    Args:
        root: Framework/project checkout holding ``config/`` and the emitted
            provider config artifacts.
        config: Loaded ``.meta-config/project.yaml`` mapping.
        provider_config: Pre-loaded ``ai-providers.yaml`` mapping. Loaded when
            omitted.

    Returns:
        WARNING findings; never raises.
    """
    findings: list[Finding] = []
    try:
        config = config if isinstance(config, dict) else {}
        if provider_config is None:
            from ..providers import load_providers_config

            provider_config = load_providers_config(root, config)
        if not isinstance(provider_config, dict):
            provider_config = {}

        from ..providers import load_provider_capabilities, resolve_providers

        capabilities = load_provider_capabilities(root)
        if not isinstance(capabilities, dict):
            capabilities = {}
        providers = resolve_providers(config, provider_config)

        orch = config.get("orchestrator")
        delegation = orch.get("delegation") if isinstance(orch, dict) else None
        max_depth = (
            delegation.get("max_depth") if isinstance(delegation, dict) else None
        )
        max_depth = _positive_int(max_depth)

        for provider in providers:
            seen: set = set()
            caps = capabilities.get(provider) or {}
            caps = caps if isinstance(caps, dict) else {}
            required = required_depth_int(caps)
            if required is None:
                continue

            pc = provider_config.get(provider) or {}
            pc = pc if isinstance(pc, dict) else {}
            emitted = _resolve_emitted_depth(root, provider_config, pc)

            if max_depth is not None and max_depth < required:
                _append_once(
                    findings,
                    seen,
                    CHECK_DELEGATION_BELOW_REQUIRED,
                    f"orchestrator.delegation.max_depth ({max_depth}) for provider "
                    f"'{provider}' is below its required_depth ({required}); "
                    "delegation would be hard-rejected before reaching the "
                    "required depth.",
                    f"Raise orchestrator.delegation.max_depth to at least {required} "
                    f"for provider '{provider}'.",
                )

            if emitted is not None and emitted < required:
                _append_once(
                    findings,
                    seen,
                    CHECK_EMITTED_BELOW_REQUIRED,
                    f"emitted dispatch depth ({emitted}) for provider '{provider}' "
                    f"is below its required_depth ({required}); child agents lose "
                    "their multi-agent dispatch tools.",
                    f"Raise the emitted subagent_depth / [agents] max_depth to at "
                    f"least {required} for provider '{provider}'.",
                )

            if emitted is not None and max_depth is not None and max_depth < emitted:
                _append_once(
                    findings,
                    seen,
                    CHECK_DELEGATION_BELOW_EMITTED,
                    f"orchestrator.delegation.max_depth ({max_depth}) for provider "
                    f"'{provider}' is below the emitted dispatch depth ({emitted}); "
                    "the configured ceiling is lower than what is emitted.",
                    f"Align orchestrator.delegation.max_depth with the emitted depth "
                    f"({emitted}) for provider '{provider}'.",
                )
    except Exception as exc:  # noqa: BLE001 — a checker must never fail the suite
        # Fail-soft: surface the checker bug as INFO (never WARNING/ERROR, so
        # --strict and the exit code stay unaffected), then return what we have.
        findings.append(Finding(
            severity=Severity.INFO,
            check="depth-coherence.check-error",
            file=_PROJECT_CONFIG,
            message=f"depth coherence check failed: {type(exc).__name__}",
            suggestion="Inspect the checker",
        ))
        return findings

    return findings
