"""Hooks layer: collect, sync, create."""

import json
import re
from pathlib import Path

from .log import SyncLog

HOOKS_DIR = "hooks"
CLAUDE_HOOKS_DIR = ".claude/hooks"

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
# See howto/hooks.md for full documentation.

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
            meta[m.group(1)] = m.group(2).strip()
    return meta


def collect_hook_sources(
    agent_meta_root: Path, platforms: list[str]
) -> list[tuple[Path, str]]:
    """Collect hook scripts from 0-external, 1-generic and 2-platform layers.

    Returns list of (source_path, output_filename) tuples.
    Layer priority (highest wins for same output filename):
      2-platform  >  1-generic  >  0-external
    """
    seen: dict[str, Path] = {}

    # 0-external
    ext_dir = agent_meta_root / HOOKS_DIR / "0-external"
    if ext_dir.exists():
        for f in sorted(ext_dir.glob("*.sh")):
            seen[f.name] = f

    # 1-generic
    generic_dir = agent_meta_root / HOOKS_DIR / "1-generic"
    if generic_dir.exists():
        for f in sorted(generic_dir.glob("*.sh")):
            seen[f.name] = f

    # 2-platform (strip platform prefix, e.g. sharkord-dod-push-check.sh → dod-push-check.sh)
    platform_dir = agent_meta_root / HOOKS_DIR / "2-platform"
    if platform_dir.exists():
        for platform in platforms:
            for f in sorted(platform_dir.glob(f"{platform}-*.sh")):
                output_name = f.name[len(platform) + 1:]
                seen[output_name] = f

    return [(src, name) for name, src in seen.items()]


def _hook_settings_command(output_filename: str) -> str:
    """Return the shell command string registered in settings.json for a hook."""
    return f"bash .claude/hooks/{output_filename}"


def _update_settings_hooks(
    project_root: Path,
    previously_managed: set[str],
    now_managed: set[str],
    active_entries: list[dict],
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Merge managed hook entries into .claude/settings.json.

    - Removes entries for stale managed hooks (in previously_managed but not now_managed)
    - Removes then re-adds entries for active hooks (clean replace)
    - Preserves all non-managed entries (user hooks, permissions, etc.)

    Hooks are identified in settings.json by their command string
    ``bash .claude/hooks/<filename>``.
    """
    settings_path = project_root / ".claude" / "settings.json"

    all_managed = previously_managed | now_managed
    if not all_managed and not settings_path.exists():
        return  # nothing to do

    # Load or initialise settings
    if settings_path.exists():
        try:
            with settings_path.open(encoding="utf-8") as f:
                settings = json.load(f)
        except (json.JSONDecodeError, OSError):
            log.warn("settings.json could not be parsed — hooks section not updated")
            return
    else:
        if not active_entries:
            return
        settings = {"permissions": {"allow": [], "deny": []}}

    hooks_section: dict = settings.get("hooks", {})

    # All commands we might have ever written (to remove stale + re-add active)
    all_managed_cmds = {_hook_settings_command(n) for n in all_managed}

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
        hooks_section.setdefault(event, []).append(hook_entry)

    # Update or remove hooks key
    if hooks_section:
        settings["hooks"] = hooks_section
    else:
        settings.pop("hooks", None)

    new_content = json.dumps(settings, indent=2, ensure_ascii=False) + "\n"

    stale = previously_managed - now_managed
    if stale:
        log.action("UPDATE", ".claude/settings.json",
                   f"removed stale hooks: {', '.join(Path(s).stem for s in sorted(stale))}")
    if active_entries:
        names = ", ".join(e["name"] for e in active_entries)
        log.action("UPDATE", ".claude/settings.json", f"registered hooks: {names}")
    elif not stale:
        return  # no effective change

    if not dry_run:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(new_content, encoding="utf-8")


def sync_hooks(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Copy hook scripts from agent-meta/hooks/ layers to .claude/hooks/ in the project.

    Layer priority (same as rules and agents):
      2-platform  >  1-generic  >  0-external

    All hook scripts are always copied (like rules — no opt-in needed for the file).
    Registration in .claude/settings.json is opt-in per project:

      .meta-config/project.yaml:
        hooks: { dod-push-check: { enabled: true } }

    Stale managed hooks (tracked in .claude/hooks/.agent-meta-managed) are deleted.
    Project-owned hook scripts (not in .agent-meta-managed) are never touched.
    """
    platforms = config.get("platforms", [])
    sources = collect_hook_sources(agent_meta_root, platforms)

    if not sources:
        return

    target_dir = project_root / CLAUDE_HOOKS_DIR
    managed_index_path = target_dir / ".agent-meta-managed"

    previously_managed: set[str] = set()
    if managed_index_path.exists():
        for line in managed_index_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                previously_managed.add(line.strip())

    now_managed: set[str] = set()
    project_hooks_cfg = config.get("hooks", {})
    active_entries: list[dict] = []

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    for source_path, output_name in sources:
        target_path = target_dir / output_name
        source_content = source_path.read_text(encoding="utf-8")
        meta = parse_hook_metadata(source_content)
        layer = source_path.parts[-2]

        log.action("COPY", str(target_path.relative_to(project_root)),
                   f"hooks/{layer}/{source_path.name}")
        now_managed.add(output_name)

        if not dry_run:
            target_path.write_text(source_content, encoding="utf-8")

        hook_stem = Path(output_name).stem
        is_enabled = project_hooks_cfg.get(hook_stem, {}).get("enabled", False)

        if is_enabled:
            event = meta.get("event", "PreToolUse")
            active_entries.append({
                "name": hook_stem,
                "event": event,
                "matcher": meta.get("matcher", ""),
                "command": _hook_settings_command(output_name),
            })
            log.info(str(target_path.relative_to(project_root)),
                     f"registered in settings.json (event: {event})")
        else:
            log.info(str(target_path.relative_to(project_root)),
                     f"copied (not enabled) — add \"hooks\": {{\"{hook_stem}\": {{\"enabled\": true}}}} to activate")

    # Remove stale hook scripts
    if target_dir.exists():
        for existing in sorted(target_dir.glob("*.sh")):
            if existing.name not in now_managed and existing.name in previously_managed:
                log.action("DELETE", str(existing.relative_to(project_root)),
                           "hook removed from agent-meta sources")
                if not dry_run:
                    existing.unlink()

    # Update .agent-meta-managed index
    if not dry_run and now_managed:
        managed_index_path.write_text(
            "\n".join(sorted(now_managed)) + "\n", encoding="utf-8"
        )

    # Merge hooks into settings.json
    _update_settings_hooks(
        project_root, previously_managed, now_managed, active_entries, log, dry_run
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
    target_path = project_root / CLAUDE_HOOKS_DIR / name

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
