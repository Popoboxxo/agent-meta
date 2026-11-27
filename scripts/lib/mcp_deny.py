"""MCP tool deny enforcement (issue #1263).

The ``blocked`` list in ``config/plugin-catalog.yaml`` is rendered into the
always-on MCP guardrail rule, but a prompt convention is not enforcement.
This module projects the same source into two enforcement surfaces, chosen by
declared capability only:

* providers that declare ``supports-permission-deny`` get the rule merged into
  their native ``permissions.deny`` (Claude-style settings file);
* providers with a verified hook protocol but WITHOUT that capability get a
  flat ``mcp-deny.json`` manifest next to the deployed hook lib, which
  ``hooks/1-generic/lib/hook_common.sh`` (``hook_mcp_tool_denied``) consults
  for every ``mcp__<server>__<tool>`` call — the hook fallback (issue #1263b);
* providers with neither capability keep the prompt convention and are logged.

Provider-agnostic by construction: the decision is keyed on the declared
``isolation-mechanism``, the ``supports-permission-deny`` capability in
``config/provider-capabilities.yaml`` and the verified ``hook_protocol`` in
``config/ai-providers.yaml`` — never on a provider name.

No file is deleted here; managed deny entries are merged with user entries and
tracked in the companion state file so a re-sync cannot orphan or duplicate
them. Both surfaces are fed by :func:`build_mcp_deny_rules` — one deny source,
never a second list.
"""
from __future__ import annotations

import json
from pathlib import Path

from .hook_plugins import HOOK_LIB_SUBDIR
from .hooks import CLAUDE_HOOKS_DIR
from .io import read_json_lenient, safe_path, write_atomic, write_checked
from .log import SyncLog
from .providers import load_provider_capabilities, provider_hooks_supported

#: Capability in ``config/provider-capabilities.yaml`` (opt-in, fail-safe).
MCP_DENY_CAPABILITY = "supports-permission-deny"
#: Namespace in the companion state file — disjoint from isolation/runtime-gate.
MCP_DENY_STATE_KEY = "mcp-deny"
#: Claude-native MCP tool namespace used by ``permissions.deny``.
MCP_TOOL_PREFIX = "mcp__"
#: Config-declared deny mechanism (``config/ai-providers.yaml``).
_DENY_MECHANISM = "claude-settings-deny"
_STATE_PROVENANCE_KEY = "_agent-meta"
_STATE_PROVENANCE_VALUE = "agent-meta managed — do not edit manually"
#: Hook-fallback manifest, deployed next to ``hook_common.sh`` in ``lib/``.
MCP_HOOK_MANIFEST_NAME = "mcp-deny.json"


def build_mcp_deny_rules(registry: dict, active_servers: list[str]) -> list[str]:
    """Return sorted ``mcp__<server>__<tool>`` rules for active servers.

    Only servers that are actually active and only their ``tools.blocked``
    entries are projected; ``allowed`` tools and inactive servers never become
    deny rules.
    """
    rules: set[str] = set()
    for name in active_servers:
        server = registry.get(name) or {}
        blocked = (server.get("tools") or {}).get("blocked") or []
        for tool in blocked:
            rules.add(f"{MCP_TOOL_PREFIX}{name}__{tool}")
    return sorted(rules)


def _load_json_object(path: Path) -> dict | None:
    """Return a dict for an existing parseable JSON(C) file, else ``None``.

    ``None`` means either "absent" (the caller may create it) or "unparseable"
    (the caller must skip the write to avoid data loss); the distinction is
    made by the caller checking ``path.exists()``.
    """
    if not path.exists():
        return {}
    data = read_json_lenient(path)
    return data if isinstance(data, dict) else None


def _deny_target(
    project_root: Path,
    provider: str,
    provider_config: dict,
    capabilities: dict,
) -> tuple[Path, Path] | None:
    """Resolve (settings file, companion state file) or ``None`` if unsupported.

    A provider supports the native deny surface only when BOTH the declared
    mechanism and the capability opt-in are present. Missing capability is a
    deliberate fail-safe: keep the prompt convention instead of guessing a
    permission format.
    """
    pc = provider_config.get(provider) or {}
    caps = capabilities.get(provider) or {}
    if pc.get("isolation-mechanism") != _DENY_MECHANISM:
        return None
    if caps.get(MCP_DENY_CAPABILITY) is not True:
        return None
    settings_rel = pc.get("settings_file")
    if not isinstance(settings_rel, str) or not settings_rel:
        return None
    settings_path = safe_path(project_root, settings_rel)
    return settings_path, settings_path.parent / "agent-meta-state.json"


def _capabilities(
    agent_meta_root: Path | None, capabilities: dict | None,
) -> dict:
    if capabilities is not None:
        return capabilities
    if agent_meta_root is None:
        return {}
    return load_provider_capabilities(agent_meta_root) or {}


def hook_deny_manifest_path(
    project_root: Path, provider: str, provider_config: dict,
) -> Path | None:
    """Resolve the hook-fallback manifest path or ``None`` if unsupported.

    Only a provider with a verified hook protocol has a deployed
    ``<hooks_dir>/lib/`` to read the manifest from. The location is derived
    from the provider's declared ``hooks_dir`` — never a provider name.
    """
    pc = provider_config.get(provider) or {}
    if not provider_hooks_supported(pc):
        return None
    hooks_dir = pc.get("hooks_dir") or CLAUDE_HOOKS_DIR
    return safe_path(
        project_root, hooks_dir, HOOK_LIB_SUBDIR, MCP_HOOK_MANIFEST_NAME,
    )


def _is_managed_hook_manifest(path: Path) -> bool:
    """True when *path* exists and carries our provenance marker."""
    if not path.exists():
        return False
    data = _load_json_object(path)
    return isinstance(data, dict) and data.get(_STATE_PROVENANCE_KEY) == _STATE_PROVENANCE_VALUE


def _drop_hook_manifest(
    project_root: Path, path: Path, log: SyncLog, dry_run: bool,
) -> None:
    rel = path.relative_to(project_root).as_posix()
    if not dry_run:
        path.unlink()
    log.action("DELETE", rel, "mcp-deny: hook fallback rules no longer apply")


def _sync_hook_deny_manifest(
    project_root: Path,
    provider: str,
    provider_config: dict,
    rules: list[str],
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Write (or clear) the hook-fallback manifest for a provider.

    Fail-open by design (convention boundary): the manifest is only an
    additional blocking surface. A provider without a verified hook protocol
    keeps the prompt convention and is logged, exactly like an absent
    manifest at runtime.
    """
    manifest_path = hook_deny_manifest_path(project_root, provider, provider_config)
    if manifest_path is None:
        log.note(
            "mcp-deny",
            f"{provider}: no permission-deny or hook capability — prompt convention only",
        )
        return

    exists = manifest_path.exists()
    if exists and not _is_managed_hook_manifest(manifest_path):
        if _load_json_object(manifest_path) is None:
            log.warning("mcp-deny: hook manifest unparseable — skipping to avoid data loss")
        else:
            log.warning(
                "mcp-deny: hook manifest without agent-meta provenance — skipping",
            )
        return

    if not rules:
        if exists:
            _drop_hook_manifest(project_root, manifest_path, log, dry_run)
        else:
            log.note("mcp-deny", f"{provider}: no blocked MCP tools — nothing to write")
        return

    payload = {_STATE_PROVENANCE_KEY: _STATE_PROVENANCE_VALUE, "rules": rules}
    content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    rel = manifest_path.relative_to(project_root).as_posix()
    if not dry_run:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
    if write_checked(manifest_path, content, log, rel, dry_run=dry_run):
        log.action("WRITE", rel, f"mcp-deny hook fallback: {len(rules)} rule(s)")
    else:
        log.note_unchanged(rel)


def sync_mcp_deny(
    project_root: Path,
    provider: str,
    provider_config: dict,
    registry: dict,
    active_servers: list[str],
    log: SyncLog,
    dry_run: bool,
    agent_meta_root: Path | None = None,
    capabilities: dict | None = None,
) -> None:
    """Merge native MCP deny rules into the provider settings file.

    Providers without the native capability fall through to the hook manifest
    (:func:`_sync_hook_deny_manifest`); a provider with neither mechanism keeps
    the prompt convention and is logged.

    Previously managed rules are removed from ``permissions.deny`` before the
    current rules are appended, so deactivating a server cannot orphan its
    deny entry. User-authored deny entries (everything not in the managed state
    namespace) survive verbatim.
    """
    caps = _capabilities(agent_meta_root, capabilities)
    rules = build_mcp_deny_rules(registry, active_servers)
    target = _deny_target(project_root, provider, provider_config, caps)
    if target is None:
        _sync_hook_deny_manifest(
            project_root, provider, provider_config, rules, log, dry_run,
        )
        return
    # A provider that gained the native capability must not keep a stale hook
    # fallback: two surfaces would block on different rule sets after a config
    # flip. Only a manifest carrying our provenance marker is removed.
    stale_manifest = hook_deny_manifest_path(project_root, provider, provider_config)
    if stale_manifest is not None and _is_managed_hook_manifest(stale_manifest):
        _drop_hook_manifest(project_root, stale_manifest, log, dry_run)

    settings_path, state_path = target

    # Empty deny list and no existing settings file: there is nothing to
    # enforce and nothing to clean up, so do not materialise a file that would
    # only carry ``"deny": []``. Same rationale as the empty companion state
    # file below — a freshly created empty surface is a foreign injection for
    # the external-tools drift scanner. An EXISTING file still runs through the
    # merge, so managed rules of a deactivated server are removed.
    if not rules and not settings_path.exists():
        log.note("mcp-deny", f"{provider}: no blocked MCP tools — nothing to write")
        return

    existing = _load_json_object(settings_path)
    if existing is None and settings_path.exists():
        log.warning("mcp-deny: settings file unparseable — skipping to avoid data loss")
        return
    existing = existing or {}

    state = _load_json_object(state_path) or {}
    previously_managed = [
        entry for entry in (state.get(MCP_DENY_STATE_KEY) or [])
        if isinstance(entry, str)
    ]

    permissions = existing.setdefault("permissions", {})
    current_deny = permissions.get("deny", [])
    if not isinstance(current_deny, list):
        current_deny = []
    user_deny = [entry for entry in current_deny if entry not in previously_managed]
    permissions["deny"] = user_deny + rules

    settings_content = json.dumps(existing, indent=2, ensure_ascii=False) + "\n"
    rel_settings = settings_path.relative_to(project_root).as_posix()
    if not dry_run:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
    if write_checked(settings_path, settings_content, log, rel_settings, dry_run=dry_run):
        log.action("WRITE", rel_settings, f"mcp-deny: {len(rules)} rule(s)")
    else:
        log.note_unchanged(rel_settings)

    new_state = dict(state)
    if rules:
        new_state[MCP_DENY_STATE_KEY] = rules
    else:
        new_state.pop(MCP_DENY_STATE_KEY, None)
    # Never materialise an EMPTY companion file: with no active MCP server it
    # would be a spurious artifact, flagged as a foreign injection by the
    # external-tools drift scanner and breaking AC-01 render identity.
    if not new_state:
        return
    new_state.setdefault(_STATE_PROVENANCE_KEY, _STATE_PROVENANCE_VALUE)
    state_content = json.dumps(new_state, indent=2, ensure_ascii=False) + "\n"
    if not dry_run:
        write_atomic(state_path, state_content)


def validate_mcp_deny(
    project_root: Path,
    provider: str,
    provider_config: dict,
    registry: dict,
    active_servers: list[str],
    agent_meta_root: Path | None = None,
    capabilities: dict | None = None,
) -> list[str]:
    """Return messages for blocked tools lacking a native deny rule.

    Empty for providers without the capability: there the prompt convention is
    the documented (and logged) mechanism, so a missing native rule is not a
    finding.
    """
    caps = _capabilities(agent_meta_root, capabilities)
    target = _deny_target(project_root, provider, provider_config, caps)
    if target is None:
        return []
    settings_path, _ = target
    existing = _load_json_object(settings_path) or {}
    deny = set((existing.get("permissions") or {}).get("deny") or [])
    missing = set(build_mcp_deny_rules(registry, active_servers)) - deny
    return [f"{provider}: missing permission deny for {rule}" for rule in sorted(missing)]
