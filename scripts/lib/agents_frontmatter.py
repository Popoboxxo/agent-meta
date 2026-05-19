"""Frontmatter manipulation utilities for agent templates."""

import re
from pathlib import Path

from .log import SyncLog
from .io import _yaml, _YAML_AVAILABLE


def extract_frontmatter_field(content: str, field: str) -> str | None:
    """Extract a YAML frontmatter field value.

    Handles three forms:
      field: single line value
      field: "quoted value that may wrap\n  across lines"
      field: 'single-quoted value'
    """
    # First try: quoted value that may span multiple lines (YAML block scalar after yaml.dump)
    # Matches: field: "...\n  ..." collecting continuation lines indented with 2+ spaces
    multi = re.search(
        rf'^{re.escape(field)}:\s+"((?:[^"\\]|\\.|\n  )*)"',
        content, flags=re.MULTILINE,
    )
    if multi:
        val = multi.group(1).replace('\n  ', ' ').strip()
        return val if val else None

    # Second try: single-line (quoted or unquoted)
    single = re.search(
        rf"^{re.escape(field)}:\s*['\"]?([^'\"\n]+)['\"]?\s*$",
        content, flags=re.MULTILINE,
    )
    return single.group(1).strip() if single else None


def build_frontmatter(content: str, name: str, description: str,
                      generated_from: str | None = None) -> str:
    """Replace name and description in YAML frontmatter.

    Preserves existing version/based-on fields.
    Inserts/updates generated-from when generated_from is provided.
    """
    content = re.sub(
        r"(^---\n.*?^name:\s*)(.+?)(\n)",
        lambda m: f"{m.group(1)}{name}{m.group(3)}",
        content, count=1, flags=re.MULTILINE | re.DOTALL,
    )
    content = re.sub(
        r"(^description:\s*\")(.+?)(\"\n)",
        lambda m: f'{m.group(1)}{description}{m.group(3)}',
        content, count=1, flags=re.MULTILINE,
    )
    if generated_from is not None:
        # Update existing generated-from field, or insert after description line
        if re.search(r"^generated-from:", content, flags=re.MULTILINE):
            content = re.sub(
                r'^generated-from:.*$',
                f'generated-from: "{generated_from}"',
                content, count=1, flags=re.MULTILINE,
            )
        else:
            # Match the full description field including multiline YAML continuations
            # (continuation lines start with whitespace in YAML)
            content = re.sub(
                r'(^description:(?:.*\n)(?:[ \t]+.*\n)*)',
                rf'\1generated-from: "{generated_from}"\n',
                content, count=1, flags=re.MULTILINE,
            )
    return content


def inject_permission_mode_field(content: str, permission_mode: str) -> str:
    """Insert or update the permissionMode: field in YAML frontmatter.

    If permission_mode is empty, removes any existing permissionMode: field.
    If set, inserts/updates after the memory: line (or model: or name: as fallback).
    """
    if not permission_mode:
        content = re.sub(r"^permissionMode:.*\n", "", content, count=1, flags=re.MULTILINE)
        return content

    if re.search(r"^permissionMode:", content, flags=re.MULTILINE):
        return re.sub(
            r"^permissionMode:.*$",
            f"permissionMode: {permission_mode}",
            content, count=1, flags=re.MULTILINE,
        )

    # Insert after memory: if present, else after model:, else after name:
    if re.search(r"^memory:", content, flags=re.MULTILINE):
        anchor = r"^memory:.*$"
    elif re.search(r"^model:", content, flags=re.MULTILINE):
        anchor = r"^model:.*$"
    else:
        anchor = r"^name:.*$"

    return re.sub(
        rf"({anchor}\n)",
        rf"\1permissionMode: {permission_mode}\n",
        content, count=1, flags=re.MULTILINE,
    )


def inject_memory_field(content: str, memory: str) -> str:
    """Insert or update the memory: field in YAML frontmatter.

    If memory is empty, removes any existing memory: field.
    If memory is set, inserts/updates after the model: line (or name: if no model:).
    """
    if not memory:
        content = re.sub(r"^memory:.*\n", "", content, count=1, flags=re.MULTILINE)
        return content

    # Update existing memory: field
    if re.search(r"^memory:", content, flags=re.MULTILINE):
        return re.sub(
            r"^memory:.*$",
            f"memory: {memory}",
            content, count=1, flags=re.MULTILINE,
        )

    # Insert after model: if present, else after name:
    anchor = r"^model:.*$" if re.search(r"^model:", content, flags=re.MULTILINE) else r"^name:.*$"
    return re.sub(
        rf"({anchor}\n)",
        rf"\1memory: {memory}\n",
        content, count=1, flags=re.MULTILINE,
    )


def inject_model_field(content: str, model: str) -> str:
    """Insert or update the model: field in YAML frontmatter.

    If model is empty, removes any existing model: field (clean slate).
    If model is set, inserts/updates after the name: line.
    """
    if not model:
        # Remove existing model: field if present
        content = re.sub(r"^model:.*\n", "", content, count=1, flags=re.MULTILINE)
        return content

    # Update existing model: field
    if re.search(r"^model:", content, flags=re.MULTILINE):
        return re.sub(
            r"^model:.*$",
            f"model: {model}",
            content, count=1, flags=re.MULTILINE,
        )

    # Insert after name: line
    return re.sub(
        r"(^name:.*\n)",
        rf"\1model: {model}\n",
        content, count=1, flags=re.MULTILINE,
    )


def inject_temperature_field(content: str, temperature: str) -> str:
    """Insert or update the temperature: field in YAML frontmatter.

    If temperature is empty, removes any existing temperature: field.
    Inserted after permissionMode: (or memory:, model:, name: as fallback).
    """
    if not temperature:
        content = re.sub(r"^temperature:.*\n", "", content, count=1, flags=re.MULTILINE)
        return content
    if re.search(r"^temperature:", content, flags=re.MULTILINE):
        return re.sub(r"^temperature:.*$", f"temperature: {temperature}",
                      content, count=1, flags=re.MULTILINE)
    for anchor in (r"^permissionMode:.*$", r"^memory:.*$", r"^model:.*$", r"^name:.*$"):
        if re.search(anchor, content, flags=re.MULTILINE):
            return re.sub(anchor, rf"\g<0>\ntemperature: {temperature}",
                          content, count=1, flags=re.MULTILINE)
    return content


def inject_max_tokens_field(content: str, max_tokens: str) -> str:
    """Insert or update the maxTokens: field in YAML frontmatter.

    If max_tokens is empty, removes any existing maxTokens: field.
    Inserted after temperature: (or permissionMode:, memory:, model:, name:).
    """
    if not max_tokens:
        content = re.sub(r"^maxTokens:.*\n", "", content, count=1, flags=re.MULTILINE)
        return content
    if re.search(r"^maxTokens:", content, flags=re.MULTILINE):
        return re.sub(r"^maxTokens:.*$", f"maxTokens: {max_tokens}",
                      content, count=1, flags=re.MULTILINE)
    for anchor in (r"^temperature:.*$", r"^permissionMode:.*$", r"^memory:.*$",
                   r"^model:.*$", r"^name:.*$"):
        if re.search(anchor, content, flags=re.MULTILINE):
            return re.sub(anchor, rf"\g<0>\nmaxTokens: {max_tokens}",
                          content, count=1, flags=re.MULTILINE)
    return content


def inject_agent_fields(
    content: str,
    role: str,
    config: dict,
    agent_meta_root: "Path",
    provider: str = "Claude",
    provider_config: dict | None = None,
    log: "SyncLog | None" = None,
    project_root: "Path | None" = None,
) -> str:
    """Inject all resolved frontmatter fields (model, memory, permissionMode, temperature, maxTokens).

    Consolidates the five inject_*_field() + resolve_*() call pairs that appear
    identically in sync_agents_for_claude() and sync_agents_for_provider().
    Only memory and permissionMode are injected for non-Claude providers.
    """
    from .roles import resolve_model, resolve_memory, resolve_permission_mode, resolve_temperature, resolve_max_tokens

    model = resolve_model(role, config, agent_meta_root, provider=provider,
                          provider_config=provider_config or {})
    content = inject_model_field(content, model)
    if model and log and project_root:
        src = "project override" if role in config.get("model-overrides", {}) else "meta default"
        log.info(str(project_root), f"model: {model} (from {src})")

    memory = resolve_memory(role, config, agent_meta_root)
    content = inject_memory_field(content, memory)
    if memory and log and project_root:
        src = "project override" if role in config.get("memory-overrides", {}) else "meta default"
        log.info(str(project_root), f"memory: {memory} (from {src})")

    permission_mode = resolve_permission_mode(role, config, agent_meta_root)
    content = inject_permission_mode_field(content, permission_mode)
    if permission_mode and log and project_root:
        src = "project override" if role in config.get("permission-mode-overrides", {}) else "meta default"
        log.info(str(project_root), f"permissionMode: {permission_mode} (from {src})")

    temperature = resolve_temperature(role, config, agent_meta_root)
    content = inject_temperature_field(content, temperature)
    if temperature and log and project_root:
        src = "project override" if role in config.get("temperature-overrides", {}) else "meta default"
        log.info(str(project_root), f"temperature: {temperature} (from {src})")

    max_tokens = resolve_max_tokens(role, config, agent_meta_root)
    content = inject_max_tokens_field(content, max_tokens)
    if max_tokens and log and project_root:
        src = "project override" if role in config.get("max-tokens-overrides", {}) else "meta default"
        log.info(str(project_root), f"maxTokens: {max_tokens} (from {src})")

    return content


def _strip_frontmatter(content: str) -> str:
    """Remove the YAML frontmatter block from content entirely."""
    if not content.startswith('---'):
        return content
    end = content.find('\n---', 3)
    if end == -1:
        return content
    return content[end + 4:].lstrip('\n')


def _remove_frontmatter_fields(content: str, fields: list) -> str:
    """Remove specific fields from YAML frontmatter."""
    import re as _re
    for field in fields:
        content = _re.sub(
            rf'^{_re.escape(field)}:.*\n', '', content, count=1, flags=_re.MULTILINE,
        )
    return content


def _transform_frontmatter_for_opencode(
    content: str,
    name: str,
    description: str,
    model: str,
    generated_from: str,
) -> str:
    """Build opencode-native agent frontmatter.

    opencode frontmatter schema (all others stripped):
      name: <role>             (required — used to invoke the agent)
      description: "..."       (required)
      mode: subagent           (all agent-meta agents are subagents)
      model: provider/model-id (optional — only when tier maps to a model ID)
      generated-from: "..."    (traceability, kept for diffability)
    """
    body = _strip_frontmatter(content)
    body = _strip_claude_specific_lines(body)

    lines = [f'name: {name}', f'description: "{description}"', 'mode: subagent']
    if model:
        lines.append(f'model: {model}')
    if generated_from:
        lines.append(f'generated-from: "{generated_from}"')

    return '---\n' + '\n'.join(lines) + '\n---\n' + body


def _strip_claude_specific_lines(content: str) -> str:
    """Remove Claude Code-specific lines that are meaningless in other providers.

    Currently strips:
    - Extension-Hook lines: > **Extension:** Falls `.claude/3-project/...` existiert → ...
    - Read-Tool instructions referencing .claude/ paths
    """
    lines = content.splitlines(keepends=True)
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("> **Extension:**") and ".claude/3-project/" in stripped:
            continue
        out.append(line)
    return "".join(out)
