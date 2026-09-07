"""Hooks layer: collect, sync, create."""
from __future__ import annotations

import json
import posixpath
import re
from pathlib import Path

from .io import is_unchanged, load_json_file, safe_path, write_checked
from .log import SyncLog
from .providers import provider_hooks_supported

HOOKS_DIR = "hooks"
CLAUDE_HOOKS_DIR = ".claude/hooks"

# The translating adapter every Antigravity-protocol hook registration goes
# through (issue #674 Phase 3.1). Lives in hooks/1-generic/ and is mirrored
# next to the hook scripts like any other 1-generic script.
ANTIGRAVITY_ADAPTER_SCRIPT = "antigravity-json-adapter.sh"

# Antigravity events whose entry shape is a FLAT command list directly under
# the event key (no matcher, no nested hooks array). PreToolUse/PostToolUse
# use the matcher + nested hooks shape instead (verified contract,
# antigravity.google/docs/hooks — issue #674 Phase 3.1).
ANTIGRAVITY_FLAT_SHAPE_EVENTS = frozenset({"Stop", "PreInvocation", "PostInvocation"})

HOOK_TEMPLATE_SH = """\
#!/bin/bash
# hook: %(stem)s
# version: 1.0.0
# event: PreToolUse
# matcher: Bash
# description: %(description)s
# enabled_by_default: false

# Claude Code passes hook context as JSON on stdin.
# Exit 0 = allow, exit 2 = block (stdout shown to Claude as context).
# See docs/guides/hooks.md for full documentation.

INPUT=$(cat)

# TODO: implement hook logic here
# tip: use python3 to parse JSON from $INPUT
# example check:
#   TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_name',''))")

exit 0
"""


def parse_hook_metadata(script_content: str) -> dict:
    """Read # key: value header comments from a hook script.

    Reads from the top of the file; stops at first non-comment / non-shebang line.
    Expected keys: hook, version, event, matcher, description, enabled_by_default
    """
    meta: dict = {}
    for line in script_content.splitlines():
        line = line.rstrip()
        if line.startswith("#!"):
            continue  # skip shebang
        if not line.startswith("#"):
            break
        m = re.match(r"^#\s*([\w-]+):\s*(.+)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
            meta[key] = value
    return meta


def collect_hook_sources(
    agent_meta_root: Path, platforms: list[str], subdir: str = ""
) -> list[tuple[Path, str]]:
    """Collect hook scripts from 0-external, 1-generic and 2-platform layers.

    Returns list of (source_path, output_filename) tuples.
    Layer priority (highest wins for same output filename):
      2-platform  >  1-generic  >  0-external

    ``subdir``: restrict collection to a subdirectory within each layer
    (e.g. "release-gates" for hooks/1-generic/release-gates/*.sh). The glob
    itself is non-recursive (`*.sh`, not `**/*.sh`), so the default (no
    subdir) never picks up files that live in a subdirectory — release-gate
    scripts are never double-collected as regular top-level hooks.
    """
    seen: dict[str, Path] = {}

    def _layer_dir(layer: str) -> Path:
        base = agent_meta_root / HOOKS_DIR / layer
        return base / subdir if subdir else base

    # 0-external
    ext_dir = _layer_dir("0-external")
    if ext_dir.exists():
        for f in sorted(ext_dir.glob("*.sh")):
            seen[f.name] = f

    # 1-generic
    generic_dir = _layer_dir("1-generic")
    if generic_dir.exists():
        for f in sorted(generic_dir.glob("*.sh")):
            seen[f.name] = f

    # 2-platform (strip platform prefix, e.g. sharkord-dod-push-check.sh → dod-push-check.sh)
    platform_dir = _layer_dir("2-platform")
    if platform_dir.exists():
        for platform in platforms:
            for f in sorted(platform_dir.glob(f"{platform}-*.sh")):
                output_name = f.name[len(platform) + 1:]
                seen[output_name] = f

    return [(src, name) for name, src in seen.items()]


def _hook_settings_command(output_filename: str, hooks_dir: str = CLAUDE_HOOKS_DIR) -> str:
    """Return the shell command string registered in settings.json for a hook."""
    return f"bash {hooks_dir}/{output_filename}"


def _update_settings_hooks(
    project_root: Path,
    previously_managed: set[str],
    now_managed: set[str],
    active_entries: list[dict],
    log: SyncLog,
    dry_run: bool,
    settings_path_rel: str = ".claude/settings.json",
    hooks_dir: str = CLAUDE_HOOKS_DIR,
) -> None:
    """Merge managed hook entries into settings.json.

    - Removes entries for stale managed hooks (in previously_managed but not now_managed)
    - Removes then re-adds entries for active hooks (clean replace)
    - Preserves all non-managed entries (user hooks, permissions, etc.)

    Hooks are identified in settings.json by their command string
    ``bash <hooks_dir>/<filename>``.
    """
    settings_path = project_root / settings_path_rel

    all_managed = previously_managed | now_managed
    if not all_managed and not settings_path.exists():
        return  # nothing to do

    # Load or initialise settings. Canonical JSON loader (Issue #479),
    # fail-soft with the original specific warning message preserved: a
    # None result (missing → n/a here, unreadable or malformed) keeps the
    # old "warn and abort the hooks update" behavior.
    if settings_path.exists():
        settings = load_json_file(settings_path, on_error="default", default=None)
        if settings is None:
            log.warning("settings.json could not be parsed — hooks section not updated")
            return
    else:
        if not active_entries:
            return
        settings = {"permissions": {"allow": [], "deny": []}}

    hooks_section: dict = settings.get("hooks", {})

    # All commands we might have ever written (to remove stale + re-add active)
    all_managed_cmds = {_hook_settings_command(n, hooks_dir) for n in all_managed}

    # Strip all managed entries from every event bucket
    for event_name in list(hooks_section.keys()):
        cleaned = [
            entry for entry in hooks_section[event_name]
            if not ({h.get("command", "") for h in entry.get("hooks", [])} & all_managed_cmds)
        ]
        if cleaned:
            hooks_section[event_name] = cleaned
        else:
            del hooks_section[event_name]

    # Add back currently active entries
    for entry_meta in active_entries:
        event = entry_meta["event"]
        matcher = entry_meta.get("matcher", "")
        command = entry_meta["command"]
        hook_entry: dict = {"hooks": [{"type": "command", "command": command}]}
        if matcher:
            hook_entry["matcher"] = matcher
        hooks_section.setdefault(event, []).append(hook_entry)  # type: ignore[attr-defined]

    # Update or remove hooks key
    if hooks_section:
        settings["hooks"] = hooks_section
    else:
        settings.pop("hooks", None)

    new_content = json.dumps(settings, indent=2, ensure_ascii=False) + "\n"

    stale = previously_managed - now_managed
    settings_rel = str(settings_path_rel)
    if not stale and not active_entries:
        return  # no effective change

    # Only report an action when the file content would actually change, so
    # dry-run counts (used by --check) reflect real pending changes.
    if is_unchanged(settings_path, new_content):
        log.skip(settings_rel, "hooks registration unchanged")
        return

    if stale:
        log.action("UPDATE", settings_rel,
                   f"removed stale hooks: {', '.join(Path(s).stem for s in sorted(stale))}")
    if active_entries:
        names = ", ".join(e["name"] for e in active_entries)
        log.action("UPDATE", settings_rel, f"registered hooks: {names}")

    if not dry_run:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(new_content, encoding="utf-8")


def _antigravity_adapter_command(
    target_filename: str, hooks_dir_rel: str, config_path_rel: str
) -> str:
    """Command string registered in hooks.json for one Antigravity hook.

    Every mirrored hook is executed THROUGH the translating adapter (payload
    keys, tool names and deny-JSON semantics differ from the Claude contract
    the hook scripts are written against — see config/ai-providers.yaml,
    issue #674 Phase 3.1). The command path is relative to the hooks.json
    directory: Antigravity resolves relative command paths against the
    location of the hooks.json that declares them (verified AGY IDE behavior
    — third-party empirical report, P6 real-repo re-check).
    """
    config_dir = posixpath.dirname(config_path_rel.rstrip("/")) or "."
    rel = posixpath.relpath(posixpath.normpath(hooks_dir_rel), posixpath.normpath(config_dir))
    if not rel.startswith("."):
        rel = f"./{rel}"
    return f"bash {rel}/{ANTIGRAVITY_ADAPTER_SCRIPT} {target_filename}"


def _update_antigravity_hooks_json(
    project_root: Path,
    previously_managed: set[str],
    now_managed: set[str],
    active_entries: list[dict],
    log: SyncLog,
    dry_run: bool,
    provider_config: dict,
) -> None:
    """Merge managed hook entries into a provider's Antigravity hooks.json.

    Registration artifact for hook_protocol ``antigravity-hooks-json``
    (issue #674 Phase 3.1). Written in the verified Antigravity schema:

        { "<hook-name>": { "<Event>": [ ...handlers... ] } }

    - PreToolUse/PostToolUse handlers: ``{"matcher": "*", "hooks": [...]}``.
      The matcher is ALWAYS "*" (match all tools): Claude-contract matcher
      names (Bash/Edit/Write) would never match AGY's native tool names, and
      every generic hook script gates on the tool name internally anyway
      (after the adapter's tool-name translation).
    - PreInvocation/PostInvocation/Stop handlers: flat
      ``{"type": "command", "command": ...}`` list (verified flat shape).
    - Commands go through hooks/1-generic/antigravity-json-adapter.sh, which
      translates the AGY payload to the Claude contract and maps exit 2 +
      stderr to ``{"decision": "deny", "reason": ...}``.
    - Removals/additions are keyed by top-level hook NAME (previously-/now_
      managed hold hook filenames; the stem is the hooks.json key), so user-
      authored hooks under other names are preserved untouched.
    """
    config_path_rel = provider_config.get("hooks_config_file")
    hooks_dir_rel = provider_config.get("hooks_dir", CLAUDE_HOOKS_DIR)
    if not config_path_rel:
        log.warning(
            "hooks: hook_protocol 'antigravity-hooks-json' requires a "
            "'hooks_config_file' key in config/ai-providers.yaml — "
            "hooks registration skipped"
        )
        return

    config_path = project_root / config_path_rel
    all_managed = previously_managed | now_managed
    if not all_managed and not config_path.exists():
        return  # nothing to do

    if config_path.exists():
        hooks_json = load_json_file(config_path, on_error="default", default=None)
        if hooks_json is None:
            log.warning(f"{config_path_rel} could not be parsed — hooks registration not updated")
            return
        # Valid-but-non-dict JSON (e.g. [] or "x") must not crash the sync or
        # be silently overwritten — mirror the _read_existing_json_dict guard
        # in mcp_provider_config.py: warn + skip, file stays untouched.
        if not isinstance(hooks_json, dict):
            log.warning(
                f"{config_path_rel} is not a JSON object — hooks registration not updated"
            )
            return
    else:
        if not active_entries:
            return
        hooks_json: dict = {}

    # Strip stale/rewritten managed hooks (identified by top-level key = hook
    # name stem), keep every foreign (user-authored) top-level entry.
    stale_names = {Path(s).stem for s in (previously_managed - now_managed)}
    rewritten_names = {e["name"] for e in active_entries}
    hooks_json = {
        k: v for k, v in hooks_json.items() if k not in stale_names and k not in rewritten_names
    }

    for entry_meta in active_entries:
        event = entry_meta["event"]
        command = _antigravity_adapter_command(
            entry_meta["file"], hooks_dir_rel, config_path_rel
        )
        handler = {"type": "command", "command": command}
        if event in ANTIGRAVITY_FLAT_SHAPE_EVENTS:
            handlers = [handler]
        else:
            handlers = [{"matcher": "*", "hooks": [handler]}]
        hooks_json[entry_meta["name"]] = {event: handlers}

    new_content = json.dumps(hooks_json, indent=2, ensure_ascii=False) + "\n"

    stale = previously_managed - now_managed
    if not stale and not active_entries:
        return  # no effective change

    if is_unchanged(config_path, new_content):
        log.skip(config_path_rel, "hooks registration unchanged")
        return

    if stale:
        log.action("UPDATE", config_path_rel,
                   f"removed stale hooks: {', '.join(sorted(stale_names))}")
    if active_entries:
        names = ", ".join(e["name"] for e in active_entries)
        log.action("UPDATE", config_path_rel, f"registered hooks: {names}")

    if not dry_run:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(new_content, encoding="utf-8")


# Registration writer per hook_protocol (issue #674 Phase 3.1). Keys are
# `hook_protocol` values from config/ai-providers.yaml — NOT provider names —
# per the provider-agnostic syncer policy: a new provider speaking an already
# implemented protocol needs zero Python changes. A missing/unknown protocol
# falls back to the legacy Claude settings.json writer (which the #630
# protocol-revocation cleanup path relies on for has_hooks providers without
# a verified hook_protocol, e.g. Mammouth/Codex).
#
# Known limitation: if an adapter-based hook_protocol (e.g. antigravity-hooks-json)
# is ever revoked, the fallback cleanup deletes stale files but leaves registration
# keys in hooks_config_file (degraded-but-safe; warnings may reference settings.json wording).
_HOOK_REGISTRATION_WRITERS: dict = {
    "claude-code-json": _update_settings_hooks,
    "antigravity-hooks-json": _update_antigravity_hooks_json,
}


def sync_hooks(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str = "Claude",
    provider_config: dict | None = None,
) -> None:
    """Copy hook scripts from agent-meta/hooks/ layers to the provider hooks directory.

    Layer priority (same as rules and agents):
      2-platform  >  1-generic  >  0-external

    All hook scripts are always copied (like rules — no opt-in needed for the file).
    Registration in settings.json is opt-in per project:

      .meta-config/project.yaml:
        hooks: { dod-push-check: { enabled: true } }

    Stale managed hooks (tracked in <hooks_dir>/.agent-meta-managed) are deleted.
    Project-owned hook scripts (not in .agent-meta-managed) are never touched.

    Note: hooks/1-generic/pre-release-check.sh is a plain top-level hook like
    any other (copied here as-is, no special-cased placeholders). It is a
    pure dispatcher for the release-gates/ plugin directory — see
    hook_plugins.py::sync_release_gates() for the gate scripts it runs at
    release time.
    """
    pc = (provider_config or {}).get(provider, {})
    hooks_dir_rel = pc.get("hooks_dir", CLAUDE_HOOKS_DIR)
    settings_file_rel = pc.get("settings_file", ".claude/settings.json")

    platforms = config.get("platforms", [])
    sources = collect_hook_sources(agent_meta_root, platforms)

    target_dir = project_root / hooks_dir_rel
    managed_index_path = target_dir / ".agent-meta-managed"

    # has_hooks: true alone does not mean this provider's hook event/payload
    # model is verified to match the contract these scripts are written
    # against (issue #630) — provider_hooks_supported() also requires a
    # matching hook_protocol. If protocol support was revoked/never granted,
    # deploy nothing new but still fall through to the cleanup logic below so
    # any PREVIOUSLY deployed hooks/settings.json entries get removed instead
    # of silently going stale forever. Only gated when a real provider_config
    # was supplied -- direct/low-level callers without one (e.g. unit tests)
    # keep the pre-#630 always-deploy behavior, matching the provider="Claude"
    # default.
    if provider_config is not None and not provider_hooks_supported(pc):
        if sources:
            log.note("hooks", f"{provider}: has_hooks=true but no verified "
                               "hook_protocol (issue #630) — not deploying hooks, "
                               "cleaning up any previously deployed ones")
        sources = []

    if not sources and not managed_index_path.exists():
        return

    previously_managed: set[str] = set()
    if managed_index_path.exists():
        for line in managed_index_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                previously_managed.add(line.strip())

    now_managed: set[str] = set()
    project_hooks_cfg = config.get("hooks", {})
    active_entries: list[dict] = []

    # Viz mode: conditional hooks (viz-log) are only managed when viz is enabled
    # and mode is dynamic/full.
    viz_cfg = config.get("viz", {})
    viz_enabled = viz_cfg.get("enabled", False)
    viz_mode = viz_cfg.get("mode", "off")
    viz_active = viz_enabled and viz_mode in ("dynamic", "full")

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    for source_path, output_name in sources:
        target_path = safe_path(target_dir, output_name)
        source_content = source_path.read_text(encoding="utf-8")
        # Hook scripts get no general {{VARIABLE}} substitution (unlike
        # agents/rules) — this one placeholder is the exception. It lets a
        # hook resolve `orchestrator.provider-overrides.<provider>` at
        # runtime without the provider identity gap that affects everything
        # else (see hooks/1-generic/orchestrator-guard.sh and issue #390):
        # sync.py bakes the provider into each provider's own generated
        # copy at build time instead.
        source_content = source_content.replace("{{AGENT_META_PROVIDER}}", provider)
        meta = parse_hook_metadata(source_content)
        layer = source_path.parts[-2]
        hook_stem = Path(output_name).stem


        # Provider filter: skip hook if it declares a specific provider that doesn't match
        hook_provider = meta.get("provider", "")
        if hook_provider and hook_provider != provider:
            log.skip(str(target_path.relative_to(project_root)),
                     f"provider-specific hook ({hook_provider} only)")
            continue

        now_managed.add(output_name)
        rel_out = str(target_path.relative_to(project_root))
        rel_source = f"hooks/{layer}/{source_path.name}"
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if write_checked(target_path, source_content, log, rel_source, dry_run=dry_run):
                log.action("COPY", rel_out, rel_source)
            else:
                log.skip(rel_out, "unchanged")
        except Exception as exc:
            log.warning(f"Failed to deploy hook {rel_out}: {exc}")
            continue

        # Post-write verification: confirm hook file exists on disk
        if not dry_run and not target_path.exists():
            log.warning(
                f"Hook file {rel_out} was not created — "
                f"check filesystem permissions. "
                f"Registered command 'bash {hooks_dir_rel}/{output_name}' "
                f"will fail with 'No such file or directory'."
            )

        # Auto-enable viz-log when viz mode is dynamic/full
        if hook_stem == "viz-log" and viz_active:
            is_enabled = True
        else:
            enabled_by_default = meta.get("enabled_by_default", "false").lower() == "true"
            is_enabled = project_hooks_cfg.get(hook_stem, {}).get("enabled", enabled_by_default)

        if is_enabled:
            event = meta.get("event", "PreToolUse")
            active_entries.append({
                "name": hook_stem,
                "event": event,
                "matcher": meta.get("matcher", ""),
                "command": _hook_settings_command(output_name, hooks_dir_rel),
                # Deployed filename — the protocol-specific registration
                # writers build their own command strings from it (the
                # Antigravity writer routes every hook through the
                # translating adapter, issue #674 Phase 3.1).
                "file": output_name,
            })
            log.note(str(target_path.relative_to(project_root)),
                     f"registered in settings.json (event: {event})")
        else:
            log.note(str(target_path.relative_to(project_root)),
                     f"copied (not enabled) — add \"hooks\": {{\"{hook_stem}\": {{\"enabled\": true}}}} to activate")

    # Remove stale hook scripts
    if target_dir.exists():
        for existing in sorted(target_dir.glob("*.sh")):
            if existing.name not in now_managed and existing.name in previously_managed:
                log.action("DELETE", str(existing.relative_to(project_root)),
                           "hook removed from agent-meta sources")
                if not dry_run:
                    existing.unlink()

    # Update .agent-meta-managed index. Also rewritten (to empty) when
    # now_managed is empty but previously_managed was not (issue #630
    # protocol-revocation cleanup) so the index doesn't keep listing files
    # that were just deleted by the stale-hook-script pass above.
    if not dry_run and (now_managed or previously_managed):
        managed_index_path.write_text(
            "\n".join(sorted(now_managed)) + ("\n" if now_managed else ""),
            encoding="utf-8",
        )

    # Merge hooks into the provider's registration artifact. The writer is
    # selected by `hook_protocol` (dispatch table above — never a provider
    # name): the Claude contract registers in settings.json, the Antigravity
    # contract in its hooks.json (issue #674 Phase 3.1).
    registration_writer = _HOOK_REGISTRATION_WRITERS.get(
        pc.get("hook_protocol"), _update_settings_hooks
    )
    if registration_writer is _update_settings_hooks:
        registration_writer(
            project_root, previously_managed, now_managed, active_entries, log, dry_run,
            settings_path_rel=settings_file_rel,
            hooks_dir=hooks_dir_rel,
        )
    else:
        registration_writer(
            project_root, previously_managed, now_managed, active_entries, log, dry_run,
            provider_config=pc,
        )

    # Final verification: check all registered hook files exist on disk
    if not dry_run:
        for entry in active_entries:
            hook_file = project_root / hooks_dir_rel / Path(entry["command"].split("/")[-1])
            if not hook_file.exists():
                log.warning(
                    f"Hook '{entry['name']}' is registered in {settings_file_rel} "
                    f"but {hooks_dir_rel}/{hook_file.name} does not exist — "
                    f"the hook will fail at runtime. "
                    f"Re-run sync.py to deploy the missing hook file."
                )


def create_hook(
    project_root: Path,
    name: str,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Create .claude/hooks/<name>.sh from template (never overwrites).

    The created file is a project-owned hook — it will never be touched by sync.py
    (not added to .agent-meta-managed).  To register it in settings.json, add
    it to .meta-config/project.yaml:  hooks: <name>: enabled: true
    """
    if not name.endswith(".sh"):
        name = f"{name}.sh"
    target_path = safe_path(project_root, CLAUDE_HOOKS_DIR, name)

    if target_path.exists():
        log.skip(str(target_path.relative_to(project_root)),
                 "hook already exists — edit it manually")
        return

    stem = Path(name).stem
    description = f"{stem.replace('-', ' ').replace('_', ' ').title()} hook"
    content = HOOK_TEMPLATE_SH % {"stem": stem, "description": description}

    log.action("CREATE", str(target_path.relative_to(project_root)),
               f"--create-hook {stem}")
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
