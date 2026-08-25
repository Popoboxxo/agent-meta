"""Platform-level config defaults for project.yaml keys.

A platform listed in `platforms:` may supply default values for arbitrary
project.yaml keys via config/platform-defaults.yaml. This is NOT a fifth preset
system — it fills the *selectors* of the four existing preset systems
(dod-preset, rules-preset, tier-preset, conventions-preset) plus any other
project.yaml scalar/list key, but never touches a preset's internal per-field
override blocks (dod:/conventions:).

Two clearly separated responsibilities live here:

  1. apply_platform_defaults() — a pure value-fill function with NO side effects
     (writes nothing). Called after every load_config() in sync.py so all
     downstream consumers (build_variables, resolve_rules, delegation_table, ...)
     see the already-platform-defaulted config dict. Runs on every sync, dry-run
     and test-repo path alike.

  2. Provenance/state management (load/save state, diff, adopt/ignore/track,
     drift logging) — writes the sidecar .meta-config/platform-defaults-state.json
     and (for adopt/ignore) project.yaml. Only runs on real sync runs and for the
     dedicated --platform-defaults-* CLI flags, never inside build_variables().

Precedence (scalar keys):  project-explicit > platform-default > framework-default.
Precedence (list keys):    additive union — all platform lists ∪ project list, deduped.
                           Exception: `roles:` — a missing roles: key means
                           "all roles active"; a platform roles default is then a
                           No-Op (must not shrink the active role set).

Merge semantics mirror docs/concepts/2026-08-25-platform-defaults.md (sections 3-5).
The context.py sidecar-hash store is the blueprint for the key-level state here.
"""
from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

from .io import _load_yaml_or_json, _write_yaml, content_hash

PLATFORM_DEFAULTS_CONFIG_YAML = "config/platform-defaults.yaml"
PROJECT_CONFIG_SCHEMA_JSON = "config/project-config.schema.json"

_STATE_DIR = ".meta-config"
_STATE_FILE = "platform-defaults-state.json"
_PROJECT_CONFIG_DIR = ".meta-config"
_PROJECT_CONFIG_CANDIDATES = ("project.yaml", "project.yml", "project.json")

# Keys where an absent value is a "means all" sentinel rather than "empty".
# For these, an additive platform-default merge is a No-Op when the project has
# no explicit list — materializing the platform list would shrink the active set.
# roles: is currently the only such key (verified against project-config.schema.json).
_ABSENT_MEANS_ALL_KEYS = frozenset({"roles"})


# ---------------------------------------------------------------------------
# Loading + schema classification
# ---------------------------------------------------------------------------

def load_platform_defaults(agent_meta_root: Path) -> dict:
    """Load config/platform-defaults.yaml -> {platform_name: {defaults: {...}}}.

    Same loader pattern conventions.py uses for config/conventions-presets.yaml.
    Returns {} when the file is missing/empty.
    """
    data, _ = _load_yaml_or_json(agent_meta_root / PLATFORM_DEFAULTS_CONFIG_YAML)
    if not data:
        return {}
    platforms = data.get("platforms", {})
    if not isinstance(platforms, dict):
        return {}
    return {k: v for k, v in platforms.items() if not k.startswith("_")}


def _load_schema(agent_meta_root: Path) -> dict:
    """Load config/project-config.schema.json (returns {} if absent/invalid)."""
    data, _ = _load_yaml_or_json(agent_meta_root / PROJECT_CONFIG_SCHEMA_JSON)
    return data or {}


def _is_list_key(key: str, schema: dict) -> bool:
    """Classify a project.yaml key as list vs scalar via the JSON schema.

    Looks up schema['properties'][key]['type'] == 'array'. Unknown/custom keys
    without a schema entry (e.g. anything under variables:) are treated
    conservatively as scalar — a misclassification there would risk a wrong
    additive merge, so the safe default is "no merge".
    """
    prop = schema.get("properties", {}).get(key)
    if not isinstance(prop, dict):
        return False
    return prop.get("type") == "array"


def _dedupe(items: list) -> list:
    """Return items with duplicates removed, preserving first-seen order.

    Falls back to identity comparison for unhashable elements so list-of-dict
    values (should any platform define them) do not raise.
    """
    seen: list = []
    result: list = []
    for item in items:
        try:
            if item in seen:
                continue
            seen.append(item)
        except TypeError:
            if item in result:
                continue
        result.append(item)
    return result


# ---------------------------------------------------------------------------
# Resolution across active platforms
# ---------------------------------------------------------------------------

def _resolve_with_sources(
    active_platforms: list[str], agent_meta_root: Path
) -> tuple[dict, dict]:
    """Merge platform defaults across all active platforms, tracking sources.

    Returns (values, sources):
      - values[key]  : resolved platform value (scalar = last-platform-wins,
                       list = deduped union across all platforms).
      - sources[key] : ordered list of platforms that contributed to key.

    Scalar conflicts: the later platform in active_platforms wins (section 3B).
    List keys: unioned across all platforms with no winner concept (dedup only).
    """
    all_defaults = load_platform_defaults(agent_meta_root)
    schema = _load_schema(agent_meta_root)

    values: dict = {}
    sources: dict = {}

    for platform in active_platforms:
        entry = all_defaults.get(platform)
        if not isinstance(entry, dict):
            continue
        defaults = entry.get("defaults", {})
        if not isinstance(defaults, dict):
            continue
        for key, pval in defaults.items():
            sources.setdefault(key, [])
            if platform not in sources[key]:
                sources[key].append(platform)
            if _is_list_key(key, schema):
                existing = values.get(key, [])
                incoming = list(pval) if isinstance(pval, list) else [pval]
                values[key] = _dedupe(list(existing) + incoming)
            else:
                # Scalar: later platform overwrites -> last entry wins.
                values[key] = pval

    return values, sources


def resolve_platform_defaults(active_platforms: list[str], agent_meta_root: Path) -> dict:
    """Merge platform defaults across all active platforms (section 3B).

    Returns a flat {key: resolved_platform_value}. Scalars resolve to a single
    value (last active platform wins on conflict); list keys resolve to the
    union across all platforms (deduped), not yet merged with the project value.
    """
    values, _ = _resolve_with_sources(active_platforms, agent_meta_root)
    return values


# ---------------------------------------------------------------------------
# Pure value fill (side-effect free) — the sync.py integration point
# ---------------------------------------------------------------------------

def apply_platform_defaults(config: dict, agent_meta_root: Path) -> dict:
    """Fill missing project.yaml keys from active platform defaults. SIDE-EFFECT FREE.

    Returns a NEW dict (the original is never mutated). Reads config['platforms']
    (existing key), resolves platform defaults, then per key:
      - Scalar missing in project -> filled with the platform default.
      - Scalar present in project  -> kept (project wins).
      - List key -> additive union of platform list + project list (deduped),
        EXCEPT the roles: No-Op guard: if roles: is absent (None sentinel), the
        platform roles default is skipped entirely so the "all roles" set is not
        silently shrunk. roles: [] (explicit empty) still participates in the merge.

    With an empty/entry-less config/platform-defaults.yaml this is a pure no-op:
    apply_platform_defaults(config) == config (migration invariant).
    """
    result = copy.deepcopy(config)
    active = config.get("platforms") or []
    if not active:
        return result

    values, _ = _resolve_with_sources(active, agent_meta_root)
    if not values:
        return result

    schema = _load_schema(agent_meta_root)

    for key, pval in values.items():
        if _is_list_key(key, schema):
            if key in _ABSENT_MEANS_ALL_KEYS and config.get(key) is None:
                # No-Op guard: absent "means all" sentinel is preserved.
                continue
            project_list = config.get(key) or []
            platform_list = list(pval) if isinstance(pval, list) else [pval]
            result[key] = _dedupe(platform_list + list(project_list))
        else:
            # Scalar: project value wins when explicitly set.
            if config.get(key) is None:
                result[key] = pval

    return result


# ---------------------------------------------------------------------------
# Sidecar state store
# ---------------------------------------------------------------------------

def _state_path(project_root: Path) -> Path:
    return project_root / _STATE_DIR / _STATE_FILE


def load_platform_defaults_state(project_root: Path) -> dict:
    """Read .meta-config/platform-defaults-state.json; return {} if absent/invalid."""
    path = _state_path(project_root)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_platform_defaults_state(project_root: Path, state: dict, dry_run: bool) -> None:
    """Write the sidecar state store (no-op in dry_run). Mirrors _save_context_hashes()."""
    if dry_run:
        return
    path = _state_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "keys": state.get("keys", {})}
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Raw project.yaml access + small helpers
# ---------------------------------------------------------------------------

def _project_config_path(project_root: Path) -> Path:
    """Locate the raw project config file (yaml preferred, json fallback)."""
    base = project_root / _PROJECT_CONFIG_DIR
    for name in _PROJECT_CONFIG_CANDIDATES:
        candidate = base / name
        if candidate.exists():
            return candidate
    return base / _PROJECT_CONFIG_CANDIDATES[0]


def _load_raw_project_config(project_root: Path) -> dict:
    """Load the raw, unmerged project.yaml (to tell explicit vs. platform-filled keys)."""
    data, _ = _load_yaml_or_json(_project_config_path(project_root))
    return data or {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _value_hash(value) -> str:
    """Stable hash of a resolved platform value (scalar or list)."""
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return f"sha256:{content_hash(payload)}"


def _values_equal(a, b, is_list: bool) -> bool:
    """Compare a project value against a platform default.

    List keys compare order-independently (the union is order-agnostic); scalars
    compare directly.
    """
    if is_list:
        try:
            return set(a or []) == set(b or [])
        except TypeError:
            return list(a or []) == list(b or [])
    return a == b


# ---------------------------------------------------------------------------
# Diff / compare
# ---------------------------------------------------------------------------

def compute_platform_defaults_diff(
    config: dict, agent_meta_root: Path, project_root: Path
) -> list[dict]:
    """Per-key compare of platform defaults against the active project config.

    Shared by `sync.py --platform-defaults-diff` and the Admin-UI
    GET /api/platform-defaults/diff. Returns one dict per key supplied by at
    least one active platform:
      {key, platform_default, source_platform, active_value, status}
    with status in {inherited, overridden, ignored} per section 4:
      - state marks key 'ignored' -> 'ignored' (regardless of value comparison).
      - key not explicit in the raw project.yaml -> 'inherited'.
      - key explicit but differs from the current platform default -> 'overridden'.
      - key explicit but identical to the platform default -> 'inherited'.

    Reads the raw project.yaml separately (not the already-merged `config`) to
    distinguish explicit-vs-filled keys.
    """
    active = config.get("platforms") or []
    values, sources = _resolve_with_sources(active, agent_meta_root)
    if not values:
        return []

    raw = _load_raw_project_config(project_root)
    state_keys = load_platform_defaults_state(project_root).get("keys", {})
    schema = _load_schema(agent_meta_root)

    entries: list[dict] = []
    for key in values:
        pdefault = values[key]
        is_list = _is_list_key(key, schema)
        explicit = key in raw
        st = state_keys.get(key, {})

        if st.get("status") == "ignored":
            status = "ignored"
        elif not explicit:
            status = "inherited"
        elif _values_equal(raw.get(key), pdefault, is_list):
            status = "inherited"
        else:
            status = "overridden"

        entries.append({
            "key": key,
            "platform_default": pdefault,
            "source_platform": ", ".join(sources.get(key, [])),
            "active_value": config.get(key),
            "status": status,
        })

    return entries


def format_platform_defaults_diff_table(entries: list[dict]) -> str:
    """Render diff entries as a plain-text table (CLI --platform-defaults-diff)."""
    header = ("Key", "Platform-Default (Quelle)", "Projekt-Wert", "Status")
    rows = [header]
    for e in entries:
        default = f"{_fmt(e['platform_default'])} ({e['source_platform']})"
        rows.append((
            str(e["key"]),
            default,
            _fmt(e["active_value"]),
            str(e["status"]),
        ))
    widths = [max(len(r[i]) for r in rows) for i in range(len(header))]
    lines = []
    for idx, row in enumerate(rows):
        lines.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
        if idx == 0:
            lines.append("  ".join("-" * widths[i] for i in range(len(header))))
    return "\n".join(lines)


def _fmt(value) -> str:
    if value is None:
        return "(nicht gesetzt)"
    if isinstance(value, list):
        return "[" + ", ".join(str(v) for v in value) + "]"
    return str(value)


# ---------------------------------------------------------------------------
# State transitions: adopt / ignore / track
# ---------------------------------------------------------------------------

def _entry_for(state: dict, key: str) -> dict:
    return state.setdefault("keys", {}).setdefault(key, {})


def adopt_platform_default(
    key: str, project_root: Path, agent_meta_root: Path, dry_run: bool
) -> None:
    """--platform-defaults-adopt: hand control of `key` back to the platform.

    Removes the explicit key from project.yaml (if present) and sets state to
    'inherited'. No value is written explicitly — the project then follows the
    live platform default again (section 4: adopt = give control back, not
    "take the current value once").
    """
    raw = _load_raw_project_config(project_root)
    path = _project_config_path(project_root)
    active = raw.get("platforms") or []
    values, sources = _resolve_with_sources(active, agent_meta_root)

    if key in raw:
        del raw[key]
        if not dry_run:
            _write_yaml(path, raw)

    state = load_platform_defaults_state(project_root)
    entry = _entry_for(state, key)
    entry["status"] = "inherited"
    if key in values:
        entry["source_platform"] = ", ".join(sources.get(key, []))
        entry["last_platform_value"] = values[key]
        entry["last_platform_value_hash"] = _value_hash(values[key])
    entry.pop("project_value", None)
    entry.pop("ignored_at", None)
    entry["last_synced"] = _now_iso()
    save_platform_defaults_state(project_root, state, dry_run)


def ignore_platform_default(
    key: str, project_root: Path, agent_meta_root: Path, dry_run: bool
) -> None:
    """--platform-defaults-ignore: pin `key` against the current platform default.

    If the key is currently inherited (not explicit in project.yaml), the current
    platform default value is materialized explicitly into project.yaml (otherwise
    there is nothing to freeze). Status -> 'ignored'. last_platform_value/_hash are
    FROZEN at this moment and not refreshed by future syncs until re-track
    (section 4, MAJOR-3 fix).
    """
    raw = _load_raw_project_config(project_root)
    path = _project_config_path(project_root)
    active = raw.get("platforms") or []
    values, sources = _resolve_with_sources(active, agent_meta_root)

    was_explicit = key in raw
    if not was_explicit and key in values:
        raw[key] = values[key]
        if not dry_run:
            _write_yaml(path, raw)
        project_value = values[key]
    else:
        project_value = raw.get(key)

    state = load_platform_defaults_state(project_root)
    entry = _entry_for(state, key)
    entry["status"] = "ignored"
    if key in values:
        entry["source_platform"] = ", ".join(sources.get(key, []))
        entry["last_platform_value"] = values[key]
        entry["last_platform_value_hash"] = _value_hash(values[key])
    entry["project_value"] = project_value
    entry["ignored_at"] = _now_iso()
    entry["last_synced"] = _now_iso()
    save_platform_defaults_state(project_root, state, dry_run)


def track_platform_default(
    key: str, project_root: Path, agent_meta_root: Path, dry_run: bool
) -> None:
    """--platform-defaults-track (re-track): lift an 'ignored' pin.

    The project value is left unchanged; last_platform_value/_hash are reset to
    the CURRENT platform default (baseline reset) so the next sync does not report
    spurious drift against the frozen ignore baseline. The new status is computed
    now: inherited if the project has no explicit value or it equals the current
    default, else overridden.
    """
    raw = _load_raw_project_config(project_root)
    active = raw.get("platforms") or []
    values, sources = _resolve_with_sources(active, agent_meta_root)
    schema = _load_schema(agent_meta_root)

    state = load_platform_defaults_state(project_root)
    entry = _entry_for(state, key)

    if key in values:
        entry["source_platform"] = ", ".join(sources.get(key, []))
        entry["last_platform_value"] = values[key]
        entry["last_platform_value_hash"] = _value_hash(values[key])
    entry.pop("ignored_at", None)

    explicit = key in raw
    if not explicit:
        entry["status"] = "inherited"
        entry.pop("project_value", None)
    elif key in values and _values_equal(raw.get(key), values[key], _is_list_key(key, schema)):
        entry["status"] = "inherited"
        entry["project_value"] = raw.get(key)
    else:
        entry["status"] = "overridden"
        entry["project_value"] = raw.get(key)

    entry["last_synced"] = _now_iso()
    save_platform_defaults_state(project_root, state, dry_run)


# ---------------------------------------------------------------------------
# Drift logging (once per real sync run)
# ---------------------------------------------------------------------------

def log_platform_defaults_drift(
    config: dict, agent_meta_root: Path, project_root: Path, log, dry_run: bool
) -> None:
    """Emit info lines for platform-default drift and refresh the state baseline.

    Called ONCE per real sync run (not per build_variables() call). For each
    'inherited' key whose current platform default differs from the stored
    last_platform_value, an [INFO] line is logged and the state baseline for that
    key is refreshed. 'overridden' keys are summarized in a single line.
    'ignored' keys are silent (freeze principle). No fail/abort — pure transparency.
    """
    active = config.get("platforms") or []
    if not active:
        return

    entries = compute_platform_defaults_diff(config, agent_meta_root, project_root)
    if not entries:
        return

    state = load_platform_defaults_state(project_root)
    state_keys = state.setdefault("keys", {})

    overridden_count = 0
    changed_state = False

    for e in entries:
        key = e["key"]
        pdefault = e["platform_default"]
        status = e["status"]
        st = state_keys.setdefault(key, {})

        if status == "ignored":
            # Frozen: keep last_platform_value untouched, only touch last_synced.
            st["last_synced"] = _now_iso()
            changed_state = True
            continue

        if status == "overridden":
            overridden_count += 1
            st["status"] = "overridden"
            st["source_platform"] = e["source_platform"]
            st["last_platform_value"] = pdefault
            st["last_platform_value_hash"] = _value_hash(pdefault)
            st["last_synced"] = _now_iso()
            changed_state = True
            continue

        # inherited
        stored = st.get("last_platform_value")
        had_baseline = "last_platform_value" in st
        if had_baseline and stored != pdefault:
            log.info(  # noqa: PLE1205
                "platform-defaults",
                f"'{key}' (Plattform '{e['source_platform']}') geändert: "
                f"{_fmt(stored)} → {_fmt(pdefault)} — automatisch übernommen "
                f"(inherited, kein Override in project.yaml)",
            )
        st["status"] = "inherited"
        st["source_platform"] = e["source_platform"]
        st["last_platform_value"] = pdefault
        st["last_platform_value_hash"] = _value_hash(pdefault)
        st["last_synced"] = _now_iso()
        changed_state = True

    if overridden_count:
        log.info(  # noqa: PLE1205
            "platform-defaults",
            f"{overridden_count} Key(s) weichen von Platform-Defaults ab "
            f"(overridden). Details: sync.py --platform-defaults-diff",
        )

    if changed_state:
        save_platform_defaults_state(project_root, state, dry_run)
