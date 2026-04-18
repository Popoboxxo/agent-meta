"""Commands layer: collect, sync, create — analog to rules.py."""

import re
from pathlib import Path

from .log import SyncLog

COMMANDS_DIR = "commands"
CLAUDE_COMMANDS_DIR = ".claude/commands"
CONTINUE_COMMANDS_DIR = ".continue/prompts"


def collect_command_sources(agent_meta_root: Path, platforms: list[str]) -> list[tuple[Path, str]]:
    """Collect command files from 0-external, 1-generic and 2-platform layers.

    Returns list of (source_path, output_filename) tuples.
    Later entries override earlier ones with the same output filename —
    platform commands override generic commands of the same name.
    """
    seen: dict[str, Path] = {}

    # 0-external: commands from external skill repos
    ext_dir = agent_meta_root / COMMANDS_DIR / "0-external"
    if ext_dir.exists():
        for f in sorted(ext_dir.glob("*.md")):
            seen[f.name] = f

    # 1-generic
    generic_dir = agent_meta_root / COMMANDS_DIR / "1-generic"
    if generic_dir.exists():
        for f in sorted(generic_dir.glob("*.md")):
            seen[f.name] = f

    # 2-platform (platform-prefixed, e.g. sharkord-deploy.md → deploy.md)
    platform_dir = agent_meta_root / COMMANDS_DIR / "2-platform"
    if platform_dir.exists():
        for platform in platforms:
            for f in sorted(platform_dir.glob(f"{platform}-*.md")):
                output_name = f.name[len(platform) + 1:]
                seen[output_name] = f

    return [(src, name) for name, src in seen.items()]


def _add_frontmatter_field(content: str, field: str, value: str) -> str:
    """Add a frontmatter field if the frontmatter block exists and the field is absent."""
    if not content.startswith("---"):
        return content
    end = content.find("\n---", 3)
    if end == -1:
        return content
    frontmatter = content[3:end]
    if field in frontmatter:
        return content
    insertion = f"\n{field}: {value}"
    return "---" + frontmatter + insertion + content[end:]


def _md_to_toml(content: str, stem: str) -> str:
    """Convert a Claude-style .md command to a Gemini .toml command.

    Extracts `description` from frontmatter and the body as `prompt`.
    Replaces $ARGUMENTS with {{args}} (Gemini syntax).
    """
    description = stem.replace("-", " ").replace("_", " ").title()
    body = content

    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            fm = content[3:end]
            m = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
            if m:
                description = m.group(1).strip().strip('"').strip("'")
            body = content[end + 4:].lstrip("\n")

    body = body.replace("$ARGUMENTS", "{{args}}")
    body = body.strip()

    # TOML multiline string
    escaped = body.replace('"""', '\\"\\"\\"')
    return f'description = "{description}"\nprompt = """\n{escaped}\n"""\n'


def sync_commands_for_provider(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict | None = None,
    variables: dict | None = None,
):
    """Copy command files to the provider-specific target directory.

    Claude   → .claude/commands/      (.md, as-is)
    Continue → .continue/prompts/     (.md, invokable: true injected)
    Gemini   → .gemini/commands/      (.toml, converted from .md)

    Variables substitution: {{VAR}} placeholders are substituted like rules.
    Stale-tracking via .agent-meta-managed in the target directory.
    """
    from .config import substitute

    pc = (provider_config or {}).get(provider, {})
    platforms = config.get("platforms", [])
    sources = collect_command_sources(agent_meta_root, platforms)

    if not sources:
        return

    if provider == "Claude":
        target_dir = project_root / CLAUDE_COMMANDS_DIR
        managed_index_path = target_dir / ".agent-meta-managed"
        output_ext = ".md"
    elif provider == "Continue":
        target_dir = project_root / CONTINUE_COMMANDS_DIR
        # Use a separate managed index to avoid collision with sync_prompts_for_continue
        managed_index_path = target_dir / ".agent-meta-commands-managed"
        output_ext = ".md"
    elif provider == "Gemini":
        commands_dir = pc.get("commands_dir", ".gemini/commands")
        target_dir = project_root / commands_dir
        managed_index_path = target_dir / ".agent-meta-managed"
        output_ext = pc.get("commands_ext", ".toml")
    else:
        return

    previously_managed: set[str] = set()
    if managed_index_path.exists():
        for line in managed_index_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                previously_managed.add(line)

    now_managed: set[str] = set()

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    for source_path, output_name in sources:
        # Rewrite extension for providers that use a different format (e.g. Gemini → .toml)
        stem = Path(output_name).stem
        final_name = stem + output_ext
        target_path = target_dir / final_name
        content = source_path.read_text(encoding="utf-8")
        layer = source_path.parts[-2]
        rel_source = f"commands/{layer}/{source_path.name}"

        if variables is not None:
            content = substitute(content, variables, rel_source, log)

        if provider == "Continue":
            content = _add_frontmatter_field(content, "invokable", "true")
        elif provider == "Gemini":
            content = _md_to_toml(content, stem)

        log.action("COPY", str(target_path.relative_to(project_root)), rel_source)
        now_managed.add(final_name)

        if not dry_run:
            target_path.write_text(content, encoding="utf-8")

    for stale_name in sorted(previously_managed - now_managed):
        stale_path = target_dir / stale_name
        if stale_path.exists():
            log.action("DELETE", str(stale_path.relative_to(project_root)),
                       "command removed from agent-meta sources")
            if not dry_run:
                stale_path.unlink()

    if not dry_run and now_managed:
        managed_index_path.write_text("\n".join(sorted(now_managed)) + "\n", encoding="utf-8")


def create_command(
    project_root: Path,
    name: str,
    log: SyncLog,
    dry_run: bool,
):
    """Create .claude/commands/<name>.md as an empty template (never overwrites)."""
    if not name.endswith(".md"):
        name = f"{name}.md"
    target_path = project_root / CLAUDE_COMMANDS_DIR / name

    if target_path.exists():
        log.skip(str(target_path.relative_to(project_root)),
                 "command already exists — edit it manually")
        return

    title = Path(name).stem.replace("-", " ").replace("_", " ").title()
    content = f"""\
---
description: {title}
allowed-tools: []
---

# {title}

<!-- This file lives in .claude/commands/ and is available as a Claude slash-command. -->
<!-- Add your command logic here. Use $ARGUMENTS to receive optional user input. -->

"""
    log.action("CREATE", str(target_path.relative_to(project_root)),
               f"--create-command {name}")
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
