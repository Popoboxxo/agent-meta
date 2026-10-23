"""Provider isolation: prevent AI providers from reading each other's directories.

When multiple providers are active (e.g. Claude + Gemini + Opencode), sync.py
generates hard-block configurations so each provider cannot read or write files
managed by other providers.

Mechanisms per provider:
  Claude   — permissions.deny in .claude/settings.json (glob patterns)
  Opencode — permission.read + permission.edit in opencode.json (glob patterns, last-match-wins)
  Gemini   — TOML policy file .gemini/policies/provider-isolation.toml (regex on tool arguments)
  Continue — soft rule .continue/rules/provider-isolation.md (no native hard block available)

Trigger: only when len(active_providers) > 1 AND project.yaml does not have
provider-isolation: disabled.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import providers
from .providers import load_provider_capabilities
from .consistency.orchestrator_strict import _resolve_effective_strict
from .io import read_json_lenient, safe_path, write_atomic, write_checked
from .log import SyncLog

# Companion state files — store agent-meta tracking data outside tool JSON schemas.
# Both Claude Code and Opencode use strict schema validation (Zod .strict() /
# JSON Schema) and reject unknown root keys, making the entire config file invalid.
# Tracking data is therefore stored in separate companion files that are not
# subject to those schemas.
_CLAUDE_STATE_FILE = ".claude/agent-meta-state.json"
_OPENCODE_STATE_FILE = ".opencode/agent-meta-state.json"

# Namespaced managed state (IC-09): the shared Opencode state file carries one
# record per writer, updated with read-modify-write so no writer clobbers the
# other. ``isolation-deny`` is the pre-existing namespace (list[str]);
# ``runtime-gate-deny`` is the A2 namespace (dict[str, dict]) and
# ``default-agent`` the entry-point namespace (dict).
_STATE_ISOLATION_KEY = "isolation-deny"
_STATE_RUNTIME_GATE_KEY = "runtime-gate-deny"
# Entry-point namespace (#1006/IC-5): value ``{"value": <role>,
# "prior": <str | None>}`` where ``value`` is the ``default_agent`` the merge
# wrote and ``prior`` the user's previous value (``None`` = key was absent).
_STATE_DEFAULT_AGENT_KEY = "default-agent"

# A2 root-deny (IC-09): the managed glob and decision written INSIDE each
# permission family mapping. The glob is disjoint from every ``_dir_to_glob``
# key the isolation writer manages (``**/file`` / ``dir/**``), so the two
# writers never collide on a JSON key.
_RUNTIME_GATE_GLOB = "**"
_RUNTIME_GATE_DECISION = "deny"
_RUNTIME_GATE_FAMILIES = ("edit", "bash")

# Entry-point key inside opencode.json (#1006/IC-6): written by the managed
# merge only for an explicit AND generated primary role, tracked in the
# ``default-agent`` state namespace so a rollback can remove/restore it.
_DEFAULT_AGENT_JSON_KEY = "default_agent"

_GEMINI_POLICIES_DIR = ".gemini/policies"
_GEMINI_ISOLATION_FILE = ".gemini/policies/provider-isolation.toml"
_CONTINUE_ISOLATION_FILE = ".continue/rules/provider-isolation.md"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def _provider_reads_dir(
    provider: str,
    provider_pc: dict,
    capabilities: dict,
    directory: str,
) -> bool:
    """Whether *provider* actively reads *directory* as its own context file.

    Provider-agnostic (IC-15 Nr. 16 / F-17): a foreign isolation-dir that is
    the target provider's declared ``context_file`` must not be denied when the
    ``agents_md_visible_to_subagents`` capability marks the provider as an
    active reader of that shared core (e.g. an ``AGENTS.md`` reader in a
    multi-provider project). Keyed on declared data only — never a provider-name
    literal.
    """
    context_file = provider_pc.get("context_file")
    if not (isinstance(context_file, str) and context_file == directory):
        return False
    caps = capabilities.get(provider) if isinstance(capabilities, dict) else None
    return isinstance(caps, dict) and caps.get("agents_md_visible_to_subagents") is True


def sync_provider_isolation(
    project_root: Path,
    providers: list[str],
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
    agent_meta_root: Path | None = None,
) -> None:
    """Generate provider isolation blocks for all active providers.

    Does nothing when fewer than 2 providers are active (no cross-provider
    isolation needed).

    A foreign isolation-dir that the target provider reads as its own context
    file (capability ``agents_md_visible_to_subagents`` true) is skipped, so a
    shared core such as ``AGENTS.md`` is never denied to an active reader
    (IC-15 Nr. 16). ``agent_meta_root`` locates the capability registry; when it
    is omitted no capability data is available and every foreign dir is kept
    (fail-safe, byte-compatible with the previous behaviour).
    """
    if len(providers) < 2:
        log.skip("provider-isolation", f"only {len(providers)} provider active — skipping")
        return

    capabilities: dict = {}
    if agent_meta_root is not None:
        try:
            capabilities = load_provider_capabilities(agent_meta_root) or {}
        except Exception:
            capabilities = {}

    log.note("provider-isolation", f"generating isolation for: {', '.join(providers)}")

    for provider in providers:
        # foreign_dirs = isolation-dirs of all OTHER active providers.
        # dir_owner tracks which provider each dir belongs to (used for
        # human-readable deny messages instead of guessing from the path).
        provider_pc = provider_config.get(provider, {})
        foreign_dirs: list[str] = []
        dir_owner: dict[str, str] = {}
        for other in providers:
            if other == provider:
                continue
            other_pc = provider_config.get(other, {})
            for d in other_pc.get("isolation-dirs", []):
                if d in foreign_dirs:
                    continue
                if _provider_reads_dir(provider, provider_pc, capabilities, d):
                    continue
                foreign_dirs.append(d)
                dir_owner[d] = other

        if not foreign_dirs:
            log.skip(f"provider-isolation/{provider}", "no foreign dirs found")
            continue

        # Which mechanism (if any) generates isolation for `provider` is a
        # capability flag from config/ai-providers.yaml::isolation-mechanism,
        # not a literal `if provider == "Name"` branch (issue #627) — a
        # provider without the key (e.g. Copilot, Mammouth) simply has no
        # isolation mechanism implemented yet.
        mechanism = provider_config.get(provider, {}).get("isolation-mechanism")
        handler = _ISOLATION_MECHANISM_HANDLERS.get(mechanism)
        if handler:
            handler(project_root, foreign_dirs, dir_owner, provider_config, log, dry_run)
        else:
            log.skip(f"provider-isolation/{provider}", "no isolation mechanism defined for this provider")


# ---------------------------------------------------------------------------
# JSON helpers (shared by Claude and Opencode)
# ---------------------------------------------------------------------------

def _read_json_safe(path: Path, log: SyncLog | None = None) -> dict | None:
    """Read a JSON file, tolerating JSONC-style // line comments.

    Returns None if the file does not exist.
    Returns None (with a warning) if the file exists but cannot be parsed —
    callers must skip their update to avoid silent data loss.
    """
    if not path.exists():
        return None
    parsed = read_json_lenient(path)
    if parsed is None and log:
        log.warning(f"{path.name}: could not parse JSON — skipping isolation update to avoid data loss")
    return parsed


def _load_state_data(state_path: Path) -> dict:
    """Load the namespaced managed-state record; an absent or unparseable file
    yields ``{}`` (optional-file semantics — it is agent-meta's own tracker)."""
    if not state_path.exists():
        return {}
    data = read_json_lenient(state_path)
    return data if isinstance(data, dict) else {}


def _read_state(state_path: Path, key: str = _STATE_ISOLATION_KEY):
    """Read ONE namespaced managed record from the shared state file.

    Returns the namespace's empty value when the file or the namespace is
    missing/unparseable: a dict for the dict-valued namespaces
    (``runtime-gate-deny``, ``default-agent``), a list otherwise.
    """
    value = _load_state_data(state_path).get(key)
    if key in (_STATE_RUNTIME_GATE_KEY, _STATE_DEFAULT_AGENT_KEY):
        return value if isinstance(value, dict) else {}
    return value if isinstance(value, list) else []


def _write_state(state_path: Path, value, dry_run: bool,
                 key: str = _STATE_ISOLATION_KEY) -> None:
    """Read-modify-write the shared state file, replacing ONLY ``key``.

    Every sibling namespace is preserved verbatim, so the isolation writer and
    the runtime-gate writer never clobber each other (IC-09). An empty value
    removes the namespace again (rollback). ``dry_run`` never writes.
    """
    if dry_run:
        return
    data = _load_state_data(state_path)
    if value:
        data[key] = value
    else:
        data.pop(key, None)
    # Provenance marker: recognize this companion file as agent-meta's own
    # product (the injection-drift scanner's is_managed_artifact predicate
    # checks file content for the canonical sentinel "agent-meta managed —
    # do not edit manually"). Free-form key read by no
    # code — the state readers only look up their own namespace keys — so it
    # cannot collide with isolation-deny / runtime-gate-deny. Without it,
    # `.claude/agent-meta-state.json` / `.opencode/agent-meta-state.json` were
    # misread as foreign artifacts on the first post-sync scan (issue #802).
    data.setdefault("_agent-meta", "agent-meta managed — do not edit manually")
    write_atomic(
        state_path,
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
    )


def _dir_to_glob(directory: str) -> str:
    """Convert an isolation-dir path to a glob pattern.

    Examples:
      '.claude/'    → '.claude/**'
      'opencode.json' → '**/opencode.json'   (file, must look like a glob)
      'AGENTS.md'   → '**/AGENTS.md'

    File paths are prefixed with ``**/`` so Claude Code treats them as glob
    patterns in ``permissions.deny``. Without a glob special character,
    bare file names such as ``opencode.json`` are misinterpreted as tool
    names and rejected because they do not start with an uppercase letter.
    """
    if directory.endswith("/"):
        return directory + "**"
    return f"**/{directory}"


def _permission_mapping(value) -> dict:
    """Normalise an Opencode permission family to a glob->decision mapping.

    ``opencode.json`` historically allowed a scalar shorthand (e.g.
    ``permission.edit: "ask"``); the isolation merge path assumed a mapping and
    raised on a scalar. A dict passes through, a scalar string becomes
    ``{"**": value}`` and anything else is treated as empty (D-C4).
    """
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        return {_RUNTIME_GATE_GLOB: value}
    return {}


# ---------------------------------------------------------------------------
# Claude: permissions.deny in .claude/settings.json
# ---------------------------------------------------------------------------

def _sync_claude_isolation(
    project_root: Path,
    foreign_dirs: list[str],
    dir_owner: dict[str, str],
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Inject/replace provider isolation entries in .claude/settings.json.

    Tracking data (previously managed patterns) is stored in a companion file
    .claude/agent-meta-state.json to avoid polluting settings.json with unknown
    root keys — Claude Code rejects the entire file when unknown root keys are present.

    Strategy:
    - Read previously managed patterns from companion state file.
    - Read existing settings.json; skip on parse error (data-loss guard).
    - Remove old managed deny entries from permissions.deny.
    - Append new managed entries; write settings.json + state file.
    """
    settings_path = safe_path(project_root, ".claude", "settings.json")
    state_path = safe_path(project_root, _CLAUDE_STATE_FILE)

    prev_managed = _read_state(state_path)
    new_managed: list[str] = [_dir_to_glob(d) for d in foreign_dirs]

    existing = _read_json_safe(settings_path, log)
    if existing is None and settings_path.exists():
        return  # parse error — warning already emitted, skip to avoid data loss
    existing = existing or {}

    permissions = existing.setdefault("permissions", {})
    current_deny: list[str] = permissions.get("deny", [])
    user_deny = [p for p in current_deny if p not in prev_managed]
    permissions["deny"] = user_deny + new_managed

    settings_content = json.dumps(existing, indent=2, ensure_ascii=False) + "\n"
    rel_settings = ".claude/settings.json"

    if not dry_run:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
    if write_checked(settings_path, settings_content, log, rel_settings, dry_run=dry_run):
        log.action("WRITE", rel_settings, f"provider-isolation deny: {', '.join(new_managed)}")
    else:
        log.skip(rel_settings, "provider-isolation unchanged")
    _write_state(state_path, new_managed, dry_run)


# ---------------------------------------------------------------------------
# Opencode: permission.read + permission.edit in opencode.json
# ---------------------------------------------------------------------------

def _sync_opencode_isolation(
    project_root: Path,
    foreign_dirs: list[str],
    dir_owner: dict[str, str],
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Inject/replace provider isolation entries in opencode.json.

    Tracking data is stored in .opencode/agent-meta-state.json to avoid
    polluting opencode.json with unknown root keys — Opencode uses Zod .strict()
    validation and rejects the entire config when unknown root keys are present.

    opencode uses last-match-wins glob permission rules.
    """
    settings_path = safe_path(project_root, "opencode.json")
    state_path = safe_path(project_root, _OPENCODE_STATE_FILE)

    prev_managed = _read_state(state_path)
    new_entries: dict[str, str] = {_dir_to_glob(d): "deny" for d in foreign_dirs}
    new_managed_keys = list(new_entries.keys())

    existing = _read_json_safe(settings_path, log)
    if existing is None and settings_path.exists():
        return  # parse error — warning already emitted, skip to avoid data loss
    existing = existing or {}

    permission = existing.setdefault("permission", {})
    # Tolerate scalar permission families (D-C4): a scalar is normalised to a
    # mapping before the managed keys are filtered/merged, so a user's
    # ``"ask"`` shorthand can never make the isolation writer raise. A2's
    # managed ``"**"`` glob is not in ``prev_managed`` and therefore survives.
    read_perms: dict[str, str] = {k: v for k, v in _permission_mapping(permission.get("read")).items()
                                   if k not in prev_managed}
    edit_perms: dict[str, str] = {k: v for k, v in _permission_mapping(permission.get("edit")).items()
                                   if k not in prev_managed}
    read_perms.update(new_entries)
    edit_perms.update(new_entries)
    permission["read"] = read_perms
    permission["edit"] = edit_perms

    settings_content = json.dumps(existing, indent=2, ensure_ascii=False) + "\n"
    rel_settings = "opencode.json"

    if not dry_run:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
    if write_checked(settings_path, settings_content, log, rel_settings, dry_run=dry_run):
        log.action("WRITE", rel_settings, f"provider-isolation deny: {', '.join(new_managed_keys)}")
    else:
        log.skip(rel_settings, "provider-isolation unchanged")
    _write_state(state_path, new_managed_keys, dry_run)


# ---------------------------------------------------------------------------
# Opencode A2: Main-Chat runtime-gate deny (permission tier)
# ---------------------------------------------------------------------------

def _opencode_runtime_gate_entries(
    config: dict,
    provider: str,
    agent_meta_root: Path,
    provider_config: dict,
) -> dict:
    """Return the Main-Chat deny entries in MAPPING form (IC-09).

    ``{'edit': {'**': 'deny'}, 'bash': {'**': 'deny'}}`` only when the
    provider's resolved gate tier is ``permission`` **and** ``orchestrator.
    strict`` is effectively active for it (three-tier precedence, shared with
    ``orchestrator_strict._resolve_effective_strict``); ``{}`` otherwise.

    Provider-agnostic: the tier comes from the IC-03 resolver, never a provider
    literal and never the ``isolation-mechanism`` key (F-07).
    """
    try:
        capabilities = providers.load_provider_capabilities(agent_meta_root)
    except Exception:  # noqa: BLE001 - unreadable registry degrades to advisory
        capabilities = {}
    caps = capabilities.get(provider, {}) if isinstance(capabilities, dict) else {}

    # Accept the full provider registry (the sync dispatch path) as well as a
    # direct per-provider entry (``pc``) — both are plain dicts keyed by
    # arbitrary provider names, so detect the registry shape defensively.
    if isinstance(provider_config, dict) and isinstance(provider_config.get(provider), dict):
        pc = provider_config.get(provider, {})
    elif isinstance(provider_config, dict):
        pc = provider_config
    else:
        pc = {}

    if providers.provider_runtime_gate_tier(pc, caps) != "permission":
        return {}

    orch = config.get("orchestrator", {}) if isinstance(config, dict) else {}
    if not _resolve_effective_strict(orch, provider):
        return {}

    return {
        family: {_RUNTIME_GATE_GLOB: _RUNTIME_GATE_DECISION}
        for family in _RUNTIME_GATE_FAMILIES
    }


def opencode_runtime_gate_wanted(
    config: dict,
    provider: str,
    agent_meta_root: Path,
    provider_config: dict,
) -> bool:
    """True iff the tier-``permission`` gate is requested (IC-4).

    Exactly ``bool(_opencode_runtime_gate_entries(...))`` — one decision
    source, so the edit-lock (IC-3) and the gate writer never disagree.
    """
    return bool(
        _opencode_runtime_gate_entries(config, provider, agent_meta_root, provider_config)
    )


def _opencode_entry_point(
    provider: str,
    provider_config: dict,
    active_set,
) -> str | None:
    """Primary role of *provider* if explicit AND generated, else ``None``.

    ``provider_config`` must be the resolved provider registry
    (``{provider: {...}}``), never a single provider entry — the lookup is
    keyed by ``provider`` (``providers.explicit_primary_role``).

    Explicit: ``providers.explicit_primary_role`` (IC-1 — no code default, so
    a provider without ``primary-role`` never emits an entry point). Generated:
    ``active_set is None`` (no active-set information ⇒ fail-open) or the role
    is a member of ``active_set.roles``.
    """
    role = providers.explicit_primary_role(provider_config, provider)
    if role is None:
        return None
    if active_set is not None and role not in active_set.roles:
        return None
    return role


def _merge_default_agent(
    existing: dict,
    desired: str | None,
    st: dict,
    gate_effective: bool,
    log: SyncLog,
) -> dict:
    """Merge the managed ``default_agent`` into *existing*; return new state.

    Mutates ``existing["default_agent"]`` in place and returns the value of the
    ``default-agent`` state namespace (``{}`` removes it). ``desired`` is the
    explicit AND generated primary role (``_opencode_entry_point``) or
    ``None``. The user's value always wins: a differing user value is never
    overwritten, only warned about — with the gate consequence appended when
    ``gate_effective`` (IC-6, AC-06…AC-09).

    A state record without a non-empty ``str`` ``value`` counts as "no state".
    The warning text stays provider-agnostic and names the entry point role;
    a value the user deleted (``None``) gets its own sentence instead of the
    literal ``'None'``.
    """
    state_value = st.get("value") if isinstance(st, dict) else None
    if not (isinstance(state_value, str) and state_value):
        st = {}
        state_value = None

    current = existing.get(_DEFAULT_AGENT_JSON_KEY)

    def _warn() -> None:
        if current is None:
            message = (
                "default_agent is missing (removed after the managed write) "
                f"but the entry point role is '{desired}'; leaving it untouched"
            )
        else:
            message = (
                f"default_agent is '{current}' but the entry point role is "
                f"'{desired}'; leaving the user value untouched"
            )
        if gate_effective:
            if current is None:
                message += (
                    " — the runtime gate is active, so no agent is "
                    f"pre-selected: set default_agent to '{desired}' or disable "
                    "strict for this provider via orchestrator.provider-overrides"
                )
            else:
                message += (
                    f" — the runtime gate is active, so '{current}' is locked: "
                    f"set default_agent to '{desired}' or disable strict for "
                    "this provider via orchestrator.provider-overrides"
                )
        log.warning(message)

    if desired is not None and not st:
        if current is None:
            existing[_DEFAULT_AGENT_JSON_KEY] = desired
            return {"value": desired, "prior": None}
        if current == desired:
            # The user already set exactly our entry point: remember it so a
            # later rollback leaves the value alone (AC-08).
            return {"value": desired, "prior": desired}
        _warn()
        return {}

    if desired is not None:
        if current != state_value:
            # Changed or deleted by the user after the managed write: leave it.
            _warn()
            return st
        if desired != state_value:
            existing[_DEFAULT_AGENT_JSON_KEY] = desired
            return {**st, "value": desired}
        return st

    if not st:
        return {}

    # Rollback: restore only a still-managed value, then drop the namespace.
    if current == state_value:
        prior = st.get("prior")
        if isinstance(prior, str) and prior:
            existing[_DEFAULT_AGENT_JSON_KEY] = prior
        else:
            existing.pop(_DEFAULT_AGENT_JSON_KEY, None)
    return {}


def _sync_opencode_runtime_gate(
    project_root: Path,
    config: dict,
    provider: str,
    provider_config: dict,
    agent_meta_root: Path,
    log: SyncLog,
    dry_run: bool,
    active_set=None,
) -> None:
    """Merge the Main-Chat runtime-gate deny and ``default_agent`` into the
    EXISTING opencode.json.

    Uses the same managed merge path as provider isolation
    (``_read_json_safe`` / ``write_checked``) — never
    ``context._init_provider_settings_json`` (#747). The deny is exactly one
    mapping-form glob ``"**"`` inside ``permission.edit`` / ``permission.bash``
    (disjoint from isolation's ``_dir_to_glob`` keys). The prior user value at
    that key is recorded in the ``runtime-gate-deny`` state namespace, so a
    later non-strict sync removes only the managed deny and restores the prior
    value exactly (IC-09, AC-10/AC-11).

    In addition (#1006/IC-6) the explicit + generated primary role
    (``_opencode_entry_point``) is written as ``default_agent``; its prior
    value lives in the separate ``default-agent`` namespace and is
    removed/restored on rollback. A differing user value is never overwritten,
    only warned about. Both writers share the state file with read-modify-write
    per namespace. ``active_set=None`` treats the entry point as generated.
    A parse error in ``opencode.json`` returns before any write (AC-14).

    The deny is coupled to the entry point (#1006/IC-6 step 2): when the gate
    is wanted but no explicit + generated primary role exists, no deny is
    written (it would lock every agent), a warning explains why, and a managed
    deny from an earlier sync is rolled back by the regular rollback branch.

    ``provider_config`` is the resolved provider registry (``{provider: …}``),
    never a single provider entry: both the gate-tier lookup
    (``_opencode_runtime_gate_entries``) and the entry-point lookup
    (``_opencode_entry_point``) index it by ``provider``.
    """
    settings_path = safe_path(project_root, "opencode.json")
    state_path = safe_path(project_root, _OPENCODE_STATE_FILE)

    existing = _read_json_safe(settings_path, log)
    if existing is None and settings_path.exists():
        return  # parse error — warning already emitted, skip to avoid data loss
    existing = existing or {}

    state = _read_state(state_path, _STATE_RUNTIME_GATE_KEY)
    gate_state = state.get(_RUNTIME_GATE_GLOB)
    if not isinstance(gate_state, dict):
        gate_state = {}

    entries = _opencode_runtime_gate_entries(config, provider, agent_meta_root, provider_config)

    # Entry point (#1006/IC-6): an explicit AND generated primary role.
    entry = _opencode_entry_point(provider, provider_config, active_set)

    # Gate-deny coupled to the entry point (#1006/IC-6 step 2): without an
    # explicit and generated primary role the deny would lock EVERY agent —
    # there would be no agent left able to edit or run a shell. In that case
    # write no deny at all; a managed deny from an earlier sync is taken back
    # by the rollback branch below (``entries`` empty), and the user is told
    # how to restore the entry point.
    if entries and entry is None:
        log.warning(
            "runtime gate (permission.edit/bash deny) NOT written for "
            f"provider '{provider}': no explicit and generated primary-role — "
            "the gate would lock every agent; declare primary-role in "
            "config/ai-providers.yaml and keep that role in the active set"
        )
        entries = {}

    da_state = _read_state(state_path, _STATE_DEFAULT_AGENT_KEY)
    before_default_agent = existing.get(_DEFAULT_AGENT_JSON_KEY)
    new_da_state = _merge_default_agent(
        existing, entry, da_state, bool(entries), log
    )

    permission = existing.get("permission")
    if not isinstance(permission, dict):
        permission = {}
    permission_changed = False
    deny_written = False
    deny_removed = False
    state_changed = False

    for family in _RUNTIME_GATE_FAMILIES:
        mapping = _permission_mapping(permission.get(family))
        current = mapping.get(_RUNTIME_GATE_GLOB)

        if entries:
            # Strict: record the prior user value once, then claim the glob.
            if family not in gate_state:
                gate_state[family] = current
                state_changed = True
            if current != _RUNTIME_GATE_DECISION:
                mapping[_RUNTIME_GATE_GLOB] = _RUNTIME_GATE_DECISION
                permission[family] = mapping
                permission_changed = True
                deny_written = True
        else:
            # Non-strict rollback: only remove OUR deny, then restore the prior.
            if family in gate_state:
                if current == _RUNTIME_GATE_DECISION:
                    prior = gate_state.get(family)
                    if prior is None:
                        mapping.pop(_RUNTIME_GATE_GLOB, None)
                    else:
                        mapping[_RUNTIME_GATE_GLOB] = prior
                    permission[family] = mapping
                    permission_changed = True
                    deny_removed = True
                gate_state.pop(family, None)
                state_changed = True

    if permission_changed:
        existing["permission"] = permission

    settings_content = json.dumps(existing, indent=2, ensure_ascii=False) + "\n"
    rel_settings = "opencode.json"

    if not dry_run:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
    default_agent_changed = existing.get(_DEFAULT_AGENT_JSON_KEY) != before_default_agent
    # Compose only the parts that actually changed: a non-strict sync writes no
    # deny, so "runtime-gate deny: …" would be misleading there.
    action_parts = []
    if deny_written:
        action_parts.append("runtime-gate deny: permission.edit/bash '**'")
    elif deny_removed:
        action_parts.append("runtime-gate deny removed: permission.edit/bash '**'")
    if default_agent_changed:
        action_parts.append("default_agent")
    if write_checked(settings_path, settings_content, log, rel_settings, dry_run=dry_run):
        log.action("WRITE", rel_settings, ", ".join(action_parts) or "runtime-gate")
    else:
        log.skip(rel_settings, "runtime-gate unchanged")
    if state_changed:
        _write_state(
            state_path,
            {_RUNTIME_GATE_GLOB: gate_state} if gate_state else {},
            dry_run,
            _STATE_RUNTIME_GATE_KEY,
        )
    if new_da_state != da_state:
        _write_state(state_path, new_da_state, dry_run, _STATE_DEFAULT_AGENT_KEY)


# ---------------------------------------------------------------------------
# Gemini: TOML policy file .gemini/policies/provider-isolation.toml
# ---------------------------------------------------------------------------

def _isolation_display_name(provider: str, provider_config: dict) -> str:
    """Human-readable provider name for isolation deny-messages.

    Sourced from config/ai-providers.yaml::isolation-display-name. Falls back
    to the raw provider registry key when no override is configured — true
    for e.g. Opencode/Continue, whose key already matches the desired label.
    Replaces the former directory-substring guessing (issue #627): ownership
    is already known by the caller, no need to re-derive it from the path.
    """
    if not provider:
        return "another provider"
    return provider_config.get(provider, {}).get("isolation-display-name", provider)


def _build_gemini_toml_rule(directory: str, priority_offset: int, owner_provider: str, provider_config: dict) -> str:
    """Build a single [[rule]] TOML block for a foreign directory.

    Gemini policy rules match on tool argument patterns (regex on JSON-serialised
    arguments). The argsPattern targets file_path and path keys commonly used by
    file-reading and file-writing tools.
    """
    # Escape the directory path for use as a TOML inline string and regex literal
    # Dots must be escaped in regex; slashes are literal
    pattern_dir = re.escape(directory).replace("/", "/")

    # Build the deny message — strip trailing slash for readability
    display_dir = directory.rstrip("/")
    provider_name = _isolation_display_name(owner_provider, provider_config)

    priority = 900 + priority_offset

    lines = [
        "[[rule]]",
        'toolName = ["read_file", "write_file", "replace", "list_directory"]',
        f'argsPattern = \'"(?:file_path|path)":"[^"]*{pattern_dir}\'',
        'decision = "deny"',
        f"priority = {priority}",
        f'denyMessage = "Provider isolation: {display_dir} is managed by {provider_name} only."',
    ]
    return "\n".join(lines)


def _sync_gemini_isolation(
    project_root: Path,
    foreign_dirs: list[str],
    dir_owner: dict[str, str],
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Generate .gemini/policies/provider-isolation.toml with one rule per foreign dir."""
    target_path = safe_path(project_root, _GEMINI_ISOLATION_FILE)
    rel = _GEMINI_ISOLATION_FILE

    rule_blocks = []
    for idx, d in enumerate(foreign_dirs):
        rule_blocks.append(_build_gemini_toml_rule(d, idx, dir_owner.get(d, ""), provider_config))

    content_lines = [
        "# agent-meta managed — do not edit manually",
        "# Generated by sync.py — provider isolation rules for Gemini CLI",
        "# One [[rule]] block per foreign provider directory.",
        "",
    ]
    content_lines.extend("\n".join(rule_blocks[i:i+1]) for i in range(len(rule_blocks)))
    content = "\n\n".join(content_lines[:4] + rule_blocks) + "\n"

    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
    if write_checked(target_path, content, log, rel, dry_run=dry_run):
        log.action("WRITE", rel, f"provider-isolation ({len(foreign_dirs)} rule(s))")
    else:
        log.skip(rel, "provider-isolation unchanged")


# ---------------------------------------------------------------------------
# Continue: soft rule .continue/rules/provider-isolation.md
# ---------------------------------------------------------------------------

def _sync_continue_isolation(
    project_root: Path,
    foreign_dirs: list[str],
    dir_owner: dict[str, str],
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Generate .continue/rules/provider-isolation.md (soft guidance, no native hard block)."""
    target_path = safe_path(project_root, _CONTINUE_ISOLATION_FILE)
    rel = _CONTINUE_ISOLATION_FILE

    # Build list items grouped by provider
    dir_lines = []
    for d in foreign_dirs:
        provider_name = _isolation_display_name(dir_owner.get(d, ""), provider_config)
        display = d.rstrip("/")
        dir_lines.append(f"- `{display}` — {provider_name} only")

    dirs_block = "\n".join(dir_lines)

    content = (
        "# Provider Isolation\n"
        "\n"
        "This project uses multiple AI providers. Do not read or write files in directories\n"
        "managed by other providers:\n"
        "\n"
        f"{dirs_block}\n"
        "\n"
        "Only read files in your own provider directory (`.continue/`) unless explicitly\n"
        "asked by the user to inspect another provider's configuration.\n"
        "\n"
        "<!-- agent-meta managed — do not edit manually -->\n"
    )

    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
    if write_checked(target_path, content, log, rel, dry_run=dry_run):
        log.action("WRITE", rel, f"provider-isolation ({len(foreign_dirs)} dir(s))")
    else:
        log.skip(rel, "provider-isolation unchanged")


# ---------------------------------------------------------------------------
# Mechanism dispatch table (config/ai-providers.yaml::isolation-mechanism -> handler)
# ---------------------------------------------------------------------------

_ISOLATION_MECHANISM_HANDLERS = {
    "claude-settings-deny": _sync_claude_isolation,
    "opencode-permissions": _sync_opencode_isolation,
    "gemini-toml-policy": _sync_gemini_isolation,
    "continue-soft-rule": _sync_continue_isolation,
}
