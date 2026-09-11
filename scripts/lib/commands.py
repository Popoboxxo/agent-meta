"""Commands layer: collect, sync, create — analog to rules.py."""
from __future__ import annotations

import re
from pathlib import Path

from .frontmatter import _split_frontmatter
from .io import SyncError, safe_path, write_checked
from .log import SyncLog

COMMANDS_DIR = "commands"
CLAUDE_COMMANDS_DIR = ".claude/commands"


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
    fm_block, body = _split_frontmatter(content)
    if not fm_block:
        return content
    inner = fm_block[3:-4]  # strip surrounding '---'/'\n---' fences
    if field in inner:
        return content
    insertion = f"\n{field}: {value}"
    return "---" + inner + insertion + "\n---" + body


def _md_to_toml(content: str, stem: str) -> str:
    """Convert a Claude-style .md command to a Gemini .toml command.

    Extracts description from frontmatter and the body as prompt.
    Replaces $ARGUMENTS with double-brace args (Gemini syntax).

    TOML escaping: basic multiline strings cannot contain 3+ consecutive
    quotes. We escape the third quote so the sequence no longer terminates
    the string (e.g., \"\"\" becomes \"\"\\\").
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

    # TOML basic multiline strings process backslash escapes — double them
    # first so regex/Windows-path content (\s, C:\dir) survives parsing.
    escaped = body.replace("\\", "\\\\")
    # They also cannot contain 3+ consecutive quotes — escape the third quote
    # so the sequence no longer terminates the string.
    escaped = escaped.replace('"""', '""\\"')

    desc_escaped = description.replace("\\", "\\\\").replace('"', '\\"')
    return f'description = "{desc_escaped}"\nprompt = """\n{escaped}\n"""\n'


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

    Dispatch is capability-driven (issue #735): the boolean ``commands`` flag in
    config/provider-capabilities.yaml gates the path, and the target directory,
    output extension and content format come from config/ai-providers.yaml
    (``commands_dir`` / ``commands_ext`` / ``commands_format`` /
    ``commands_managed_index``). No provider-name branching:
      - ``commands_format: markdown`` — copied as-is (.md)
      - ``commands_format: continue`` — ``invokable: true`` injected into frontmatter
      - ``commands_format: toml``     — converted from .md to provider TOML

    An unsupported provider gets one explicit INFO line instead of the old
    silent ``return``; a provider that declares support without a
    ``commands_dir`` fails loudly.

    Variables substitution: {{VAR}} placeholders are substituted like rules.
    Stale-tracking via the managed index in the target directory.
    """
    from .config import substitute
    from .providers import load_provider_capabilities, provider_commands_supported

    pc = (provider_config or {}).get(provider, {})
    capabilities = load_provider_capabilities(agent_meta_root).get(provider, {})
    if not provider_commands_supported(capabilities):
        log.note(
            "commands",
            f"{provider}: not supported "
            "(config/provider-capabilities.yaml commands: false) — no commands written",
        )
        return

    platforms = config.get("platforms", [])
    sources = collect_command_sources(agent_meta_root, platforms)

    if not sources:
        return

    commands_dir_rel = pc.get("commands_dir")
    if not commands_dir_rel:
        raise SyncError(
            f"Provider '{provider}' declares commands support "
            "(config/provider-capabilities.yaml: commands: true) but has no "
            "commands_dir in config/ai-providers.yaml — refusing to guess a "
            "target directory (issue #735)."
        )
    target_dir = project_root / commands_dir_rel
    managed_index_path = target_dir / pc.get("commands_managed_index", ".agent-meta-managed")
    output_ext = pc.get("commands_ext", ".md")
    commands_format = pc.get("commands_format", "markdown")

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
        target_path = safe_path(target_dir, final_name)
        content = source_path.read_text(encoding="utf-8")
        layer = source_path.parts[-2]
        rel_source = f"commands/{layer}/{source_path.name}"

        if variables is not None:
            content = substitute(content, variables, rel_source, log)

        if commands_format == "continue":
            content = _add_frontmatter_field(content, "invokable", "true")
        elif commands_format == "toml":
            content = _md_to_toml(content, stem)
        elif commands_format != "markdown":
            raise SyncError(
                f"Provider '{provider}': unknown commands_format "
                f"{commands_format!r} — supported: markdown, continue, toml "
                "(issue #735)."
            )

        now_managed.add(final_name)
        rel_out = str(target_path.relative_to(project_root))
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        if write_checked(target_path, content, log, rel_source, dry_run=dry_run):
            log.action("COPY", rel_out, rel_source)
        else:
            log.skip(rel_out, "unchanged")

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
