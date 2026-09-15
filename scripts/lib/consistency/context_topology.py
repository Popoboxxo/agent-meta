"""Consistency checks for the context-file topology (SPEC-CONTEXT-FILE-MODES).

Topology (``context_file.topology``) is the sibling of the density switch
(``context_file.mode``): ``unified`` renders one shared context file, while
``per-provider`` renders a canonical core (``context_file.core_file``) plus
provider-native adapter files. This module validates the *configuration* of
that switch — never the rendered output of a single provider (that is the
size guard's job in :mod:`scripts.lib.consistency.context_size`):

* an out-of-enum ``context_file.topology`` (project or per-provider override)
  is a silent config bug — the resolver fails safe to ``unified``, so the
  author's intent is never surfaced without a WARNING;
* every adapter-capable provider must name a ``context_adapter_file``;
* two adapter-capable providers must not point at the same adapter file
  (collision) — one would overwrite the other;
* in ``per-provider`` an adapter must reference the core file (via the
  provider-native import syntax with its ``{core}`` placeholder, or the
  generated pointer line);
* in ``unified`` an existing adapter file that differs from the provider's
  normal context file and has no managed-index entry is an orphan — the
  rollback (``context.py::rollback_context_adapters``) never ran or lost its
  index; the finding points at that rollback.

All findings are WARNINGs (the repo convention for "config looks wrong but is
not fatal"): the checks never raise and degrade to ``[]`` on malformed input.
Dispatch is key-driven throughout — ``context_adapter*`` keys and the
``context_topology`` resolver, never a provider-name literal.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .report import Finding, Severity

_PROJECT_CONFIG = ".meta-config/project.yaml"
_VALID_TOPOLOGIES = ("unified", "per-provider")
_DEFAULT_CORE_FILE = "AGENTS.md"
# Managed index authorizing generated adapter files (context.py).
_ADAPTER_MANAGED_INDEX = ".agent-meta-context-adapters-managed"
_POINTER_TEMPLATE = "Read `{core}` for the shared project context."


def _load_project_config(root: Path) -> dict:
    """Load the full project config from ``root``. Returns ``{}`` on absence."""
    from ..io import _load_yaml_or_json

    config, _ = _load_yaml_or_json(root / _PROJECT_CONFIG)
    return config if isinstance(config, dict) else {}


def _core_file(config: dict) -> str:
    """Resolve ``context_file.core_file`` with the same fail-safe as the renderer."""
    block = config.get("context_file") if isinstance(config, dict) else None
    if isinstance(block, dict):
        core = block.get("core_file")
        if isinstance(core, str) and core.strip():
            return core
    return _DEFAULT_CORE_FILE


def _reference_line(config: dict, pc: dict) -> str:
    """The core reference line the adapter renderer would emit.

    Mirrors ``context.py::_adapter_reference_line``: an explicit
    ``context_adapter_import_supported: true`` with a non-blank
    ``context_adapter_import`` renders that syntax with ``{core}`` substituted;
    every other combination falls back to the pointer line.
    """
    core = _core_file(config)
    syntax = pc.get("context_adapter_import")
    if (
        pc.get("context_adapter_import_supported") is True
        and isinstance(syntax, str)
        and syntax.strip()
    ):
        return syntax.replace("{core}", core).strip()
    return _POINTER_TEMPLATE.format(core=core)


def _active_providers(provider_config: dict) -> list:
    """Active providers — mirrors :func:`context_size.check_context_file_size`.
    """
    return [p for p in provider_config if isinstance(provider_config[p], dict)]


def _severity_finding(check: str, file: str, message: str, suggestion: str) -> Finding:
    return Finding(
        severity=Severity.WARNING,
        check=check,
        file=file,
        message=message,
        suggestion=suggestion,
    )


def check_context_topology_consistency(
    root: Path,
    config: dict = None,
    provider_config: dict = None,
) -> list[Finding]:
    """WARNING-only findings for the ``context_file`` topology configuration.

    Args:
        root: Project root holding ``.meta-config/project.yaml`` and the
            adapter managed index.
        config: Pre-loaded project config. Loaded from ``root`` when None.
        provider_config: Pre-loaded ``ai-providers.yaml`` mapping. Loaded via
            ``lib.providers`` when None.

    Returns:
        Findings with Severity.WARNING; never raises.
    """
    findings: list[Finding] = []
    try:
        if config is None:
            config = _load_project_config(root)
        if not isinstance(config, dict):
            config = {}

        if provider_config is None:
            from ..providers import load_providers_config, resolve_providers

            provider_config = load_providers_config(root)
            if not isinstance(provider_config, dict):
                provider_config = {}
            active = resolve_providers(config, provider_config)
        else:
            if not isinstance(provider_config, dict):
                provider_config = {}
            active = _active_providers(provider_config)

        from ..providers import context_topology

        block = config.get("context_file") if isinstance(config.get("context_file"), dict) else {}

        # 1. Valid enum for the project switch and every provider override.
        project_value = block.get("topology")
        if project_value is not None and project_value not in _VALID_TOPOLOGIES:
            findings.append(_severity_finding(
                "context.topology",
                _PROJECT_CONFIG,
                f"context_file.topology={project_value!r} is not a valid topology "
                f"(expected one of: {', '.join(_VALID_TOPOLOGIES)}) — it resolves "
                "fail-safe to 'unified', so the configured intent is silently ignored.",
                "Set context_file.topology to 'unified' or 'per-provider', or "
                "remove the key (absent means 'unified').",
            ))
        overrides = block.get("provider-overrides")
        if isinstance(overrides, dict):
            for provider, entry in overrides.items():
                if not isinstance(entry, dict):
                    continue
                override = entry.get("topology")
                if override is not None and override not in _VALID_TOPOLOGIES:
                    findings.append(_severity_finding(
                        "context.topology",
                        _PROJECT_CONFIG,
                        f"context_file.provider-overrides.{provider}.topology="
                        f"{override!r} is not a valid topology (expected one of: "
                        f"{', '.join(_VALID_TOPOLOGIES)}) — it resolves fail-safe "
                        "to the project value.",
                        "Set the override to 'unified' or 'per-provider', or remove "
                        "the 'topology' key for that provider.",
                    ))

        # 2. Adapter-capability registry invariants (key-driven).
        adapter_files: dict[str, list[str]] = {}
        for provider in active:
            pc = provider_config.get(provider)
            if not isinstance(pc, dict) or pc.get("context_adapter") is not True:
                continue
            adapter_file = pc.get("context_adapter_file")
            if not isinstance(adapter_file, str) or not adapter_file.strip():
                findings.append(_severity_finding(
                    "context.adapter_missing_file",
                    _PROJECT_CONFIG,
                    f"Provider '{provider}' is adapter-capable "
                    "(context_adapter: true) but has no non-empty "
                    "context_adapter_file — the adapter render is skipped.",
                    f"Add context_adapter_file: <path> for '{provider}' in "
                    "config/ai-providers.yaml, or drop context_adapter.",
                ))
                continue
            adapter_files.setdefault(adapter_file, []).append(provider)

        for adapter_file, providers in sorted(adapter_files.items()):
            if len(providers) > 1:
                findings.append(_severity_finding(
                    "context.adapter_collision",
                    _PROJECT_CONFIG,
                    f"Providers {', '.join(sorted(providers))} share the adapter file "
                    f"'{adapter_file}' — each per-provider render would overwrite the "
                    "other.",
                    "Give every adapter-capable provider its own "
                    "context_adapter_file in config/ai-providers.yaml.",
                ))

        # 3. per-provider: the adapter must reference the core file.
        index_path = root / _ADAPTER_MANAGED_INDEX
        managed = _read_index(index_path)
        for provider in active:
            pc = provider_config.get(provider)
            if not isinstance(pc, dict) or pc.get("context_adapter") is not True:
                continue
            adapter_file = pc.get("context_adapter_file")
            if not isinstance(adapter_file, str) or not adapter_file.strip():
                continue
            if context_topology(config, provider) == "per-provider":
                core = _core_file(config)
                line = _reference_line(config, pc)
                if core not in line:
                    findings.append(_severity_finding(
                        "context.adapter_core_reference",
                        _PROJECT_CONFIG,
                        f"Provider '{provider}' adapter '{adapter_file}' renders no "
                        f"reference to the core file '{core}' "
                        f"(context_adapter_import={pc.get('context_adapter_import')!r}).",
                        "Include the '{core}' placeholder in context_adapter_import "
                        f"(e.g. '@{{core}}' → '@{core}') or clear the import so the "
                        "pointer line is generated.",
                    ))
                continue

            # unified: an existing dedicated adapter file without an index entry
            # is orphaned (the rollback never ran or lost its index).
            context_file = pc.get("context_file")
            if adapter_file == context_file:
                continue  # same path as the regular context file: not an orphan
            if adapter_file in managed:
                continue
            if not (root / adapter_file).is_file():
                continue
            findings.append(_severity_finding(
                "context.adapter_orphan",
                adapter_file,
                f"Adapter file '{adapter_file}' exists while the topology is "
                f"'unified' for provider '{provider}', but it has no entry in "
                f"'{_ADAPTER_MANAGED_INDEX}' — it is orphaned and would be read by "
                "nobody.",
                "Run a sync to roll back the per-provider adapters "
                "(rollback_context_adapters), or delete the orphaned file.",
            ))
    except Exception:
        # Contract: this check never raises — a malformed config degrades to the
        # findings collected so far instead of failing the consistency suite.
        return findings

    return findings


def _read_index(index_path: Path) -> set:
    """Read the newline-delimited adapter managed index (empty on absence)."""
    try:
        if not index_path.exists():
            return set()
        return {
            line.strip()
            for line in index_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    except OSError:
        return set()
