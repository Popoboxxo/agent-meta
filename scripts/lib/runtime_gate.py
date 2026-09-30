"""Runtime-gate seam: canonical tier vocabulary for provider gate enforcement.

The CRITICAL GATE ("MAIN CHAT darf nicht selbst editieren. ALLES ->
``orchestrator``. Keine Ausnahmen.") is only as strong as the provider runtime
that backs it. This module owns the canonical vocabulary that names **how** a
provider enforces the gate, so every consumer (resolver, rendering, consistency)
speaks the same four tiers:

``hook``
    Verified PreToolUse hook contract (the provider mirrors the framework hook
    scripts and the runtime blocks the tool call).
``plugin``
    Verified native plugin runtime (Phase 1, capability-gated; DEFERRED until
    the P6 real-repo verification is recorded).
``permission``
    Native permission layer blocks Main-Chat writes. **Partial**: the block
    carries no delegation provenance (a delegated child session is not
    distinguishable from the Main Chat).
``advisory``
    Prompt adherence only — no runtime enforcement. This is the fail-safe
    default for a provider without a resolved, stronger tier.

Seam boundary (IC-03): this module owns the tier vocabulary and the weak->strong
fold. The tier *resolver* (`provider_runtime_gate_tier`) lives in
``providers.py`` next to the other capability resolvers, so there is exactly one
source of truth. Phase 1 (IC-08) adds the capability-gated plugin generator
below; it ships ``observe`` only and never blocks a tool call.

This module also owns the weak→strong ordering ``RUNTIME_GATE_TIER_RANK`` and
``weakest_runtime_gate_tier``, which folds several tiers to the weakest one.
That fold is the shared-context-file guarantee: a context file rendered for
several providers is only as strong as its weakest reader, so every sharer
must render the same (weakest) gate bundle.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Set, Tuple

from .io import load_yaml_file, safe_path, write_checked
from .log import SyncLog

#: Canonical gate tiers, ordered strongest first. Consumers must treat any
#: value outside this tuple as an unknown tier and fail safe to ``advisory``.
RUNTIME_GATE_TIERS: Tuple[str, ...] = ("hook", "plugin", "permission", "advisory")

#: Explicit weak -> strong order for the weakest-tier resolution of a shared
#: context file (SPEC-CONTEXT-FILE-MODES-2026-09-13, IC-01). ``RUNTIME_GATE_TIERS``
#: keeps its historic strong -> weak order and is intentionally NOT reordered.
RUNTIME_GATE_TIER_RANK: Mapping[str, int] = {
    "advisory": 0,
    "permission": 1,
    "plugin": 2,
    "hook": 3,
}

_ADVISORY_TIER = "advisory"


def weakest_runtime_gate_tier(tiers: Iterable[str]) -> str:
    """Return the minimum tier by ``RUNTIME_GATE_TIER_RANK`` (weak -> strong).

    A context file shared by several providers is only as strong as its weakest
    reader, so the effective gate tier is the minimum over all provided tiers.
    Unknown names are ignored for the minimum but do not raise; ``None``, an
    empty iterable or a non-iterable input yields ``"advisory"`` (the weakest
    assumed tier — fail-safe). A bare tier-name string is treated as a single
    tier (``"hook"`` -> ``"hook"``), never iterated character by character.
    This function never raises.
    """
    if isinstance(tiers, str):
        tiers = (tiers,)
    try:
        known = [t for t in tiers if t in RUNTIME_GATE_TIER_RANK]
    except TypeError:
        return _ADVISORY_TIER
    if not known:
        return _ADVISORY_TIER
    return min(known, key=RUNTIME_GATE_TIER_RANK.__getitem__)


# --- Phase 1 plugin generator (IC-08) -------------------------------------
#
# Capability-gated native gate artifact. It maps a provider's declared
# ``plugin_protocol`` (a config key, never a provider name) to a template and
# deploys it into the provider's ``plugin_dir``. Task 8 ships ``MODE=observe``
# only: the artifact annotates proposed tool calls and never blocks. The
# ``enforce`` mode stays locked until the P6 real-repo verification (plan
# Task 9) records that ``tool.execute.before`` fires in subagent sessions and
# that the Main Chat is distinguishable.

PLUGIN_TEMPLATE_BY_PROTOCOL: Dict[str, str] = {
    "opencode-plugin-js": "templates/plugins/runtime-gate.opencode-plugin.js.tmpl",
}

PLUGIN_STEM = "agent-meta-runtime-gate"

MANAGED_INDEX_NAME = ".agent-meta-managed"

#: The only plugin mode this module ever bakes. ``"enforce"`` is intentionally
#: not modelled here: it stays locked until the P6 real-repo verification
#: (plan Task 9), so no code path can emit it early.
PLUGIN_MODE_OBSERVE = "observe"


def runtime_gate_plugin_relpath(pc: Optional[dict]) -> Optional[str]:
    """Return ``plugin_dir/<PLUGIN_STEM><plugin_ext>`` or ``None``.

    ``None`` when ``has_plugins`` is falsy or ``plugin_dir``/``plugin_ext`` is
    missing. Provider-agnostic — only config keys are read, never a provider
    name at this seam. Never raises.
    """
    if not isinstance(pc, dict) or not pc.get("has_plugins", False):
        return None
    plugin_dir = pc.get("plugin_dir")
    plugin_ext = pc.get("plugin_ext")
    if not plugin_dir or not plugin_ext:
        return None
    return f"{str(plugin_dir).rstrip('/')}/{PLUGIN_STEM}{plugin_ext}"


def _baked_plugin_mode() -> str:
    """Return the plugin mode baked into the generated artifact.

    Task 8 (Phase 1, observe) always bakes ``observe``: the ``enforce`` opt-in
    is unlocked only after the P6 real-repo verification (plan Task 9), so no
    generated artifact ever carries ``MODE=enforce`` before then. The Phase-0
    ``runtime-gate.plugin-mode`` schema key remains declarative here.
    """
    return PLUGIN_MODE_OBSERVE


def _plugin_agent_allowlist(agent_meta_root: Path) -> List[str]:
    """Return the delegated role names baked into the artifact allowlist.

    The allowlist is the framework's registered role inventory
    (``config/role-defaults.yaml``) so a future enforce path never treats a
    dispatched subagent role as the Main Chat. Provider-agnostic; a missing or
    malformed registry yields ``[]`` (fail-safe, never raises).
    """
    data = load_yaml_file(
        agent_meta_root / "config" / "role-defaults.yaml",
        on_error="default",
        default={},
    )
    roles = data.get("roles") if isinstance(data, dict) else None
    if not isinstance(roles, dict):
        return []
    return sorted(str(name) for name in roles)


def _render_plugin_template(template_text: str, mode: str, allowlist: List[str]) -> str:
    """Substitute the sync-time-baked constants into the plugin template.

    ``STRICT`` is baked ``false`` in Task 8: the enforce path (which would use
    it) is P6-gated (plan Task 9).
    """
    return (
        template_text.replace("{{RUNTIME_GATE_PLUGIN_MODE}}", mode)
        .replace("{{RUNTIME_GATE_PLUGIN_STRICT}}", "false")
        .replace("{{RUNTIME_GATE_PLUGIN_AGENT_ALLOWLIST}}", json.dumps(allowlist))
    )


def _read_managed_index(path: Path) -> Set[str]:
    """Return the tracked filenames from a ``.agent-meta-managed`` index."""
    if not path.is_file():
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def sync_runtime_gate_plugins(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: Optional[dict] = None,
) -> None:
    """Deploy the provider-native gate artifact, capability-gated (IC-08).

    Mirrors ``hook_plugins.sync_release_gates``' always-copy /
    ``.agent-meta-managed`` / never-touch-project-owned pattern for the gate
    plugin directory. The artifact is deployed only when
    ``provider_runtime_gate_supported(pc)`` is true (``has_plugins`` plus a
    verified ``plugin_protocol``). When the capability is off, the previously
    managed artifact is removed and project-owned files are left untouched.

    Task 8 ships ``MODE=observe`` only: the artifact annotates tool calls and
    never blocks. ``enforce`` stays locked until the P6 real-repo verification
    (plan Task 9).

    Error paths (AC-18): an unsupported ``plugin_protocol`` or a missing
    template logs a warning and writes nothing — never silent, never a crash.
    ``dry_run`` never writes. Provider-agnostic: only config keys and the
    resolver are used, never a provider literal.
    """
    pc = (provider_config or {}).get(provider, {}) if isinstance(provider_config, dict) else {}
    if not isinstance(pc, dict):
        pc = {}

    plugin_dir_rel = pc.get("plugin_dir")
    if not plugin_dir_rel:
        # Capability declared but no directory to write into (IC-08): never
        # silent, but also nothing to deploy or roll back. A provider without
        # the capability stays a no-op.
        if pc.get("has_plugins", False):
            log.warning(
                f"runtime-gate plugin: {provider} declares has_plugins but no "
                "plugin_dir; nothing written"
            )
        return

    target_dir = project_root / str(plugin_dir_rel)
    managed_index_path = target_dir / MANAGED_INDEX_NAME
    previously_managed = _read_managed_index(managed_index_path)

    # Deferred import: ``providers`` imports this module at its top (for
    # ``weakest_runtime_gate_tier``), so a module-level import would cycle.
    from .providers import provider_runtime_gate_supported

    now_managed: Set[str] = set()
    prune_managed = False

    if provider_runtime_gate_supported(pc):
        relpath = runtime_gate_plugin_relpath(pc)
        if relpath is None:
            log.warning(
                f"runtime-gate plugin: {provider} declares has_plugins but no "
                "plugin_dir/plugin_ext; nothing written"
            )
        else:
            output_name = Path(relpath).name
            template_rel = PLUGIN_TEMPLATE_BY_PROTOCOL.get(pc.get("plugin_protocol"))
            template_path = agent_meta_root / template_rel if template_rel else None
            if template_path is None or not template_path.is_file():
                log.warning(
                    "runtime-gate plugin: no template for plugin_protocol "
                    f"{pc.get('plugin_protocol')!r}; nothing written"
                )
            else:
                content = _render_plugin_template(
                    template_path.read_text(encoding="utf-8"),
                    _baked_plugin_mode(),
                    _plugin_agent_allowlist(agent_meta_root),
                )
                target_path = safe_path(target_dir, output_name)
                now_managed.add(output_name)
                prune_managed = True
                rel_out = str(target_path.relative_to(project_root))
                rel_source = str(template_path.relative_to(agent_meta_root))
                if not dry_run:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    if write_checked(target_path, content, log, rel_source, dry_run=dry_run):
                        log.action("COPY", rel_out, rel_source)
                    else:
                        log.skip(rel_out, "unchanged")
                except Exception as exc:  # noqa: BLE001 — mirror hook_plugins fail-soft
                    log.warning(f"Failed to deploy runtime-gate plugin {rel_out}: {exc}")
                    now_managed.discard(output_name)
                    prune_managed = False
    elif pc.get("has_plugins", False):
        # has_plugins=true but no verified plugin_protocol -> warn, no write,
        # and leave any previously managed artifact in place (conservative).
        log.warning(
            "runtime-gate plugin: unsupported plugin_protocol "
            f"{pc.get('plugin_protocol')!r}; nothing written"
        )
    else:
        # Capability off -> remove the previously managed artifact.
        prune_managed = True

    if prune_managed and target_dir.is_dir():
        for name in sorted(previously_managed - now_managed):
            stale = safe_path(target_dir, name)
            if not stale.is_file():
                continue
            log.action(
                "DELETE",
                str(stale.relative_to(project_root)),
                "runtime-gate plugin removed (capability off)",
            )
            if not dry_run:
                stale.unlink()

    if not dry_run:
        if now_managed:
            managed_index_path.parent.mkdir(parents=True, exist_ok=True)
            managed_index_path.write_text(
                "\n".join(sorted(now_managed)) + "\n", encoding="utf-8"
            )
        elif managed_index_path.exists():
            managed_index_path.unlink()
