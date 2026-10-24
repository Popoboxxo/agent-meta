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
* Settings files — a provider ``settings_file`` with a ``.jsonc`` twin in the
  same directory is a ``Severity.WARNING`` (spec §3.9 / AC-D9): the runtime
  merges the ``.jsonc`` over the managed ``.json`` and lets it win per key.

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
    v2_connection_key_violations,
    validate_artifact,
    validate_mcp_document,
)
from ..providers import load_providers_config, resolve_providers
from ..registry_query import load_mcp_registry
from .report import Finding, Severity

#: Check label of the merged-catalog connection-key check (spec §3.5 (b)). The
#: message carries the same prefix, so a CI grep sees one stable string.
CHECK_MCP_CONNECTION_KEY = "mcp-connection-key"

#: AC-D9-mandated label of the settings-file duplicate guard (spec §3.9). This
#: is a finding label, not a provider dispatch: the check iterates the provider
#: registry and composes the message from the actual file names, so it fires for
#: any provider whose ``settings_file`` is shadowed by a ``.jsonc`` twin.
CHECK_SETTINGS_FILE_DUPLICATE = "opencode-config-duplicate"

#: Extension of the shadowing twin. The runtime merges a content-bearing
#: ``.jsonc`` over the managed ``.json`` (last write wins, evidence doc
#: ``docs/analysis/evidence/2026-10-22-opencode-jsonc-loading.md`` §3), so a
#: silent override of generated values is exactly what this guard prevents.
_SHADOWING_SETTINGS_EXT = ".jsonc"

#: Extension the evidence covers as the shadowed source. Only a ``.json``
#: settings file is probed for a ``.jsonc`` twin (QA-E-01): ``Path.with_suffix``
#: on a YAML settings file would invent a ``config.jsonc`` sibling check the
#: evidence never showed.
_SHADOWING_SOURCE_EXT = ".json"

#: Framework catalog that hosts the MCP registry (no JSON schema exists for it,
#: which is why this check duplicates the declared types in code).
_MCP_CATALOG_FILE = "config/plugin-catalog.yaml"


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


def check_mcp_connection_keys(
    agent_meta_root: Path, project_config: dict | None = None
) -> list[Finding]:
    """Validate the opencode v2 connection keys of the merged MCP catalog.

    Spec §3.5 (b): the framework catalog (``config/plugin-catalog.yaml``) has no
    JSON schema, so the types of the optional v2 keys are checked here instead
    of at the document level. The **merged** catalog is validated — framework,
    then ``.meta-config/plugin-catalog.yaml``, then the inline
    ``plugin-catalog`` block of the project config, each deep-merged over the
    previous one (``registry_query.load_mcp_registry``), so a project override
    is checked exactly as generation would read it.

    Only MCP-server entries are considered (the catalog also hosts cli-tools).
    Absent keys are valid; a violation is a ``Severity.ERROR`` with the stable
    message ``mcp-connection-key: <server>.<key> invalid`` and the concrete
    sub-key detail in the suggestion. No provider name is read anywhere: the
    keys are provider-agnostic catalog data and the v2-only consumption happens
    in the v2 format branch of the writer.
    """
    findings: list[Finding] = []
    registry = load_mcp_registry(
        agent_meta_root, project_config, project_root=agent_meta_root
    )
    if not isinstance(registry, dict):
        return findings
    catalog_file = _rel(agent_meta_root / _MCP_CATALOG_FILE, agent_meta_root)

    for name in sorted(registry):
        server = registry[name]
        if not isinstance(server, dict):
            continue
        for key, detail in v2_connection_key_violations(server.get("connection")):
            findings.append(
                Finding(
                    Severity.ERROR,
                    CHECK_MCP_CONNECTION_KEY,
                    catalog_file,
                    f"{CHECK_MCP_CONNECTION_KEY}: {name}.{key} invalid",
                    f"connection.{key} {detail}.",
                )
            )
    return findings


def _active_provider_names(providers: dict, project_config: dict | None) -> list[str]:
    """Provider names whose ``settings_file`` participates in the check.

    An explicit ``ai-providers``/``ai-provider`` selection in *project_config*
    is resolved through :func:`resolve_providers` (so deactivation is honoured);
    without one every registry entry counts. Falling back to the full registry —
    instead of the ``resolve_providers`` default provider — keeps a partial
    project config from silently narrowing the check to a hard-wired default.
    """
    if isinstance(project_config, dict) and (
        "ai-providers" in project_config or "ai-provider" in project_config
    ):
        try:
            return list(resolve_providers(project_config, providers))
        except (TypeError, ValueError):
            return sorted(providers)
    return sorted(providers)


def _settings_file_duplicate_findings(
    providers: dict, agent_meta_root: Path, project_config: dict | None
) -> list[Finding]:
    """WARNING for each active provider whose settings file has a ``.jsonc`` twin."""
    findings: list[Finding] = []
    seen: set[Path] = set()
    for name in _active_provider_names(providers, project_config):
        entry = providers.get(name)
        if not isinstance(entry, dict):
            continue
        settings_file = entry.get("settings_file")
        if not isinstance(settings_file, str) or not settings_file.strip():
            continue
        settings_path = agent_meta_root / settings_file
        # The shadowing evidence covers ``.json`` only: the runtime probes the
        # sibling ``.jsonc`` of a JSON settings file. A YAML/TOML settings file
        # (e.g. ``.continue/config.yaml``) has no ``config.jsonc`` twin that
        # could override it, so probing one would report a phantom duplicate
        # (QA-E-01).
        if settings_path.suffix != _SHADOWING_SOURCE_EXT:
            continue
        if not settings_path.is_file():
            continue
        jsonc_path = settings_path.with_suffix(_SHADOWING_SETTINGS_EXT)
        if not jsonc_path.is_file() or jsonc_path in seen:
            continue
        seen.add(jsonc_path)
        findings.append(
            Finding(
                Severity.WARNING,
                CHECK_SETTINGS_FILE_DUPLICATE,
                _rel(jsonc_path, agent_meta_root),
                f"{CHECK_SETTINGS_FILE_DUPLICATE}: {settings_path.name} and "
                f"{jsonc_path.name} both present; keep one",
                f"Remove {jsonc_path.name}; agent-meta manages {settings_path.name}.",
            )
        )
    return findings


def check_settings_file_duplicates(
    agent_meta_root: Path, project_config: dict | None = None
) -> list[Finding]:
    """Warn when a provider settings file is shadowed by a ``.jsonc`` twin.

    Spec §3.9 / AC-D9: the runtime loads both files and lets the ``.jsonc``
    value win per key (evidence doc §3), so a content-bearing twin silently
    overrides the managed settings file. For every **active** provider — the
    ``ai-providers`` selection of *project_config* when present, the whole
    registry otherwise — the resolved ``settings_file`` is checked for a file
    with the same stem and the ``.jsonc`` extension in the same directory. Only
    a ``.json`` settings file is eligible: the evidence covers JSON shadowing,
    so a YAML/TOML settings file is never probed for an invented ``.jsonc``
    twin (QA-E-01).

    Yields a ``Severity.WARNING`` (never an error: consumers decide via
    ``consistency-check.py --strict``) with the stable message
    ``opencode-config-duplicate: <name>.json and <name>.jsonc both present;
    keep one``. The label is a constant; the message is composed from the actual
    file names, so the rule is provider-agnostic and no provider name is read
    anywhere.
    """
    providers = load_providers_config(agent_meta_root, project_config)
    if not isinstance(providers, dict):
        return []
    return _settings_file_duplicate_findings(providers, agent_meta_root, project_config)


def check_artifact_contracts(
    agent_meta_root: Path, project_config: dict | None = None
) -> list[Finding]:
    """Validate generated artifacts present in ``agent_meta_root``.

    *project_config* is the effective project configuration
    (``.meta-config/project.yaml``); it is threaded into
    :func:`load_providers_config` so this registry-wide check resolves the same
    ``mcp-config.format`` / ``frontmatter-mechanism`` surface that generation
    emitted (D2). ``None`` keeps the historic registry-only behavior.

    Returns ``Severity.ERROR`` findings for contract violations and
    ``Severity.WARNING`` findings for a shadowed settings file; an absent
    registry, an absent artifact directory, or a format without a declared
    contract yields no findings (conservative, no false positives).

    Overlap note (quality review WARN-4, extended by issue #849): the sync-time
    gate (``agent_sync.collect_artifact_findings``) validates the same committed
    artifacts for a project-scoped, capability-aware fail-loud signal. This
    check is deliberately the framework-tree, registry-wide counterpart used by
    ``consistency-check.py``; the two cannot diverge because both resolve the
    agent contract via :func:`artifact_validate.resolve_artifact_contract` /
    :func:`artifact_validate.validate_artifact` and the committed MCP document
    via :func:`artifact_validate.validate_mcp_document` (single source of
    truth).
    """
    findings: list[Finding] = []
    # Catalog-level check (spec §3.5 (b)): independent of the provider registry,
    # so it runs even when no provider config is resolvable.
    findings += check_mcp_connection_keys(agent_meta_root, project_config)

    providers = load_providers_config(agent_meta_root, project_config)
    if not isinstance(providers, dict):
        return findings

    # Settings-file duplicate guard (spec §3.9 / AC-D9): WARNING only.
    findings += _settings_file_duplicate_findings(
        providers, agent_meta_root, project_config
    )

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

        findings += validate_mcp_document(cfg.get("mcp-config"), agent_meta_root)

    return findings
