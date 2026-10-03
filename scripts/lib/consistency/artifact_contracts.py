"""Generated-artifact consistency check (registry-driven).

Plan Task 2 (SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30), AC-13 (consistency
side) + AC-17. Iterates ``config/ai-providers.yaml`` and validates the
generated artifacts that are present in the agent-meta tree against the
format contract declared for each provider:

* Markdown agents (``agents_dir`` / ``agent_ext``) — ``validate_frontmatter``
  against the declared ``agent-transform.allowed-fields`` / ``reject-fields``.
* ``frontmatter-mechanism: codex-toml`` agents — ``validate_toml``.
* The committed MCP document — ``validate_json_document`` for the JSON
  formats that have a declared key-shape contract (``opencode-json`` /
  ``opencode-json-v2``); the TOML MCP document is parsed with
  ``validate_toml``.

Provider-agnostic by construction: the iteration is registry-driven and every
dispatch reads a declared config **value** (``frontmatter-mechanism``,
``mcp-config.format``); no branch reads a provider name.

The ``allowed-fields`` allow-list is the **v2 silent-drop guard**
(spec §5, design §4.3), so it is enforced on the v2 surface only; the v1 byte
shape keeps its unknown keys, which the runtime normalizes internally. This is
conservative (no false positives on the v1 tree) and keeps the emitted-vs-
declared contract fail-loud exactly where the runtime drops keys silently.

Missing or unusable registry / artifacts are skipped, never guessed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

from ..artifact_validate import (
    resolve_artifact_contract,
    validate_artifact,
    validate_json_document,
    validate_toml,
)
from ..providers import load_providers_config
from .report import Finding, Severity

# JSON MCP formats that ``artifact_validate.validate_json_document`` knows a
# key-shape contract for (all other formats are YAML / provider-specific and
# are not guessed here).
_JSON_FORMATS = frozenset({"opencode-json", "opencode-json-v2"})
# TOML MCP format (Codex): the committed document must parse as TOML.
_TOML_FORMATS = frozenset({"codex-toml-mcp"})


def _iter_artifacts(directory: Path, ext: str) -> Iterator[Path]:
    if not directory.is_dir():
        return
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.name.endswith(ext):
            yield path


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def check_artifact_contracts(
    agent_meta_root: Path, project_config: dict | None = None
) -> list[Finding]:
    """Validate generated artifacts present in ``agent_meta_root``.

    *project_config* is the effective project configuration
    (``.meta-config/project.yaml``); it is threaded into
    :func:`load_providers_config` so this registry-wide check resolves the same
    ``mcp-config.format`` / ``frontmatter-mechanism`` surface that generation
    emitted (D2). ``None`` keeps the historic registry-only behavior.

    Returns ``Severity.ERROR`` findings; an absent registry, an absent
    artifact directory, or a format without a declared contract yields no
    findings (conservative, no false positives).

    Overlap note (quality review WARN-4): the sync-time gate
    (``agent_sync.collect_artifact_findings``) validates the same committed
    artifacts for a project-scoped, capability-aware fail-loud signal. This
    check is deliberately the framework-tree, registry-wide counterpart used by
    ``consistency-check.py``; the two cannot diverge because both resolve the
    contract via :func:`artifact_validate.resolve_artifact_contract` and
    validate via :func:`artifact_validate.validate_artifact` (single source of
    truth).
    """
    findings: list[Finding] = []
    providers = load_providers_config(agent_meta_root, project_config)
    if not isinstance(providers, dict):
        return findings

    for cfg in providers.values():
        if not isinstance(cfg, dict):
            continue
        contract = resolve_artifact_contract(cfg)

        agents_dir = cfg.get("agents_dir")
        if agents_dir:
            ext = str(cfg.get("agent_ext", ".md"))
            directory = agent_meta_root / str(agents_dir)
            for path in _iter_artifacts(directory, ext):
                text = _read(path)
                if text is None:
                    continue
                rel = _rel(path, agent_meta_root)
                findings += validate_artifact(text, contract, rel)

        findings += _check_mcp_document(cfg, agent_meta_root)

    return findings


def _check_mcp_document(cfg: dict, agent_meta_root: Path) -> list[Finding]:
    mcp = cfg.get("mcp-config")
    if not isinstance(mcp, dict):
        return []
    committed = mcp.get("committed-file")
    fmt = mcp.get("format")
    if not committed or not isinstance(fmt, str):
        return []

    path = agent_meta_root / str(committed)
    if not path.is_file():
        return []
    text = _read(path)
    if text is None:
        return []
    rel = _rel(path, agent_meta_root)

    if fmt in _JSON_FORMATS:
        return validate_json_document(text, fmt, rel)
    if fmt in _TOML_FORMATS:
        return validate_toml(text, rel)
    return []
