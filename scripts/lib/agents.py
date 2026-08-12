"""Agent file generation: frontmatter, composition, sync logic."""
from __future__ import annotations

import re
from pathlib import Path

from .io import safe_path, write_checked
from .log import SyncLog

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

AGENTS_DIR = "agents"
GENERIC_DIR = "1-generic"
PLATFORM_DIR = "2-platform"
PROJECT_DIR = "3-project"
EXTERNAL_DIR = "0-external"
SKILL_WRAPPER = "_skill-wrapper.md"
EXT_SUFFIX = "-ext"
PROVIDER_TOOLS_CONFIG = "config/provider-tools.yaml"

# Cache for provider tools config
_provider_tools_cache: dict | None = None


def load_provider_tools_config(agent_meta_root: Path) -> dict:
    """Load config/provider-tools.yaml. Returns empty dict if unavailable."""
    global _provider_tools_cache
    if _provider_tools_cache is not None:
        return _provider_tools_cache
    try:
        config_path = agent_meta_root / PROVIDER_TOOLS_CONFIG
        if config_path.exists():
            if _YAML_AVAILABLE:
                with open(config_path, encoding="utf-8") as f:
                    _provider_tools_cache = _yaml.safe_load(f) or {}
            else:
                _provider_tools_cache = {}
        else:
            _provider_tools_cache = {}
    except Exception:  # noqa: BLE001
        _provider_tools_cache = {}
    return _provider_tools_cache


def _validate_tools_against_whitelist(
    tools: list, provider: str, agent_meta_root: Path, log: SyncLog, role: str,
) -> list:
    """Validate tool names against provider whitelist.

    Returns filtered list of valid tools.
    Logs WARNING for unknown tools (does NOT abort). Tools listed under
    '<provider>-silent' are known-unsupported by design and dropped as INFO.
    """
    config = load_provider_tools_config(agent_meta_root)
    whitelist = config.get(provider.lower(), [])
    if not whitelist:
        # No whitelist configured — allow all tools (backward compat)
        return tools
    silent = config.get(f"{provider.lower()}-silent", []) or []

    def matches(t: str, patterns: list) -> bool:
        return any(
            w.endswith("*") and t.startswith(w[:-1]) or w == t
            for w in patterns
        )

    valid: list = []
    for t in tools:
        if not isinstance(t, str):
            continue
        if matches(t, whitelist):
            valid.append(t)
        elif matches(t, silent):
            log.info(
                f"{provider}/{role}",
                f"tool '{t}' not supported by {provider} — dropped by design",
            )
        else:
            log.warning(
                f"{provider}/{role}: tool '{t}' not supported by {provider} — skipping (see config/provider-tools.yaml)",
            )
    return valid

def _update_frontmatter_dict(content: str, updates: dict, removes: list | None = None) -> str:
    """Update YAML frontmatter fields in content using PyYAML.

    If PyYAML is available, splits content into frontmatter and body,
    parses frontmatter, updates fields, removes specified fields,
    serializes back to YAML and rejoins the body.
    """
    if not _YAML_AVAILABLE:
        return content

    fm_block, body = _split_frontmatter(content)
    if fm_block:
        inner = re.sub(r"^---\n?", "", fm_block)
        inner = re.sub(r"\n?---\s*$", "", inner)
        try:
            fm_dict = _yaml.safe_load(inner)
            if not isinstance(fm_dict, dict):
                fm_dict = {}
        except _yaml.YAMLError:
            fm_dict = {}
    else:
        fm_dict = {}
        body = content

    # Apply updates
    for k, v in updates.items():
        if v is not None:
            fm_dict[k] = v
        else:
            fm_dict.pop(k, None)

    # Apply removes
    if removes:
        for k in removes:
            fm_dict.pop(k, None)

    try:
        new_fm_inner = _yaml.dump(fm_dict, allow_unicode=True, default_flow_style=False,
                                  sort_keys=False).rstrip("\n")
        new_fm_block = f"---\n{new_fm_inner}\n---"
        if body.startswith("\n"):
            return new_fm_block + body
        return new_fm_block + "\n" + body
    except _yaml.YAMLError:
        return content


def extract_frontmatter_field(content: str, field: str) -> str | None:
    """Extract a YAML frontmatter field value.

    Uses PyYAML if available; falls back to regex.
    """
    if _YAML_AVAILABLE:
        fm = _parse_frontmatter_yaml(content)
        val = fm.get(field)
        if val is not None:
            if isinstance(val, (str, type(None))):
                return val
            return str(val)

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


def _tools_can_spawn(tools) -> bool:
    """Return True if a frontmatter `tools` value grants sub-agent spawning.

    Spawning requires the `Agent` or `Task` tool (or a `*` wildcard granting all
    tools). Accepts the value in its raw frontmatter forms: a YAML list, a
    comma/space-separated string, or `*`. Anything else → cannot spawn.
    """
    if tools is None:
        return False
    if isinstance(tools, str):
        if tools.strip() == "*":
            return True
        items = re.split(r"[,\s]+", tools)
    elif isinstance(tools, (list, tuple)):
        if "*" in tools:
            return True
        items = tools
    else:
        return False
    names = {str(i).strip() for i in items if str(i).strip()}
    return "Agent" in names or "Task" in names


def resolve_mcp_tools_for_role(
    role: str,
    config: dict,
    agent_meta_root: Path,
    project_root: Path | None = None,
) -> list[str]:
    """Return the namespaced MCP tool names a role may use, e.g. ``mcp__playwright__browser_click``.

    A role opts in via ``mcp-servers:`` in ``config/role-defaults.yaml`` (or
    ``mcp-role-overrides.<role>`` in project.yaml, which wins). Only servers
    that are actually active for the project contribute tools, and only the
    server's ``tools.allowed`` entries — ``tools.blocked`` never leaks in.

    Without this the generated frontmatter lists just the base tools, so a role
    documented as MCP-capable (e2e-tester + playwright) starts a session with
    none of those tools bound (issue #467).
    """
    from .mcp import load_mcp_registry, resolve_active_mcp_servers
    from .roles import load_roles_config

    overrides = config.get("mcp-role-overrides", {}) or {}
    if role in overrides:
        wanted = overrides.get(role) or []
    else:
        role_cfg = load_roles_config(agent_meta_root)["roles"].get(role, {}) or {}
        wanted = role_cfg.get("mcp-servers", []) or []
    if isinstance(wanted, str):
        wanted = [wanted]
    if not wanted:
        return []

    active = set(resolve_active_mcp_servers(config, agent_meta_root, project_root))
    registry = load_mcp_registry(agent_meta_root, config, project_root)

    tools: list[str] = []
    for server in wanted:
        if server not in active:
            continue
        allowed = (registry.get(server, {}).get("tools", {}) or {}).get("allowed", []) or []
        for tool in allowed:
            name = f"mcp__{server}__{tool}"
            if name not in tools:
                tools.append(name)
    return tools


def append_frontmatter_tools(content: str, extra_tools: list[str]) -> str:
    """Append extra_tools to the frontmatter `tools` list, preserving order.

    No-op when there is nothing to add or when the template grants `*`
    (a wildcard already covers every tool).
    """
    if not extra_tools:
        return content
    fm = _parse_frontmatter_yaml(content)
    current = fm.get("tools")
    if current is None:
        return content
    if isinstance(current, str):
        if current.strip() == "*":
            return content
        current = [t for t in re.split(r"[,\s]+", current) if t]
    elif isinstance(current, (list, tuple)):
        if "*" in current:
            return content
        current = list(current)
    else:
        return content
    merged = list(current) + [t for t in extra_tools if t not in current]
    if merged == list(current):
        return content
    return _update_frontmatter_dict(content, {"tools": merged})


def is_deprecated_template(content: str) -> bool:
    """Return True if the template frontmatter declares `deprecated: true`.

    A template is deprecated only when the field is explicitly truthy. Absent
    field or any other value (False, missing) means the template is active
    (backward-compatible default: not deprecated).
    """
    if _YAML_AVAILABLE:
        fm = _parse_frontmatter_yaml(content)
        return fm.get("deprecated") is True

    # Regex fallback when PyYAML is unavailable: match `deprecated: true`
    # (case-insensitive value), allowing optional surrounding quotes.
    match = re.search(
        r"^deprecated:\s*['\"]?(true)['\"]?\s*$",
        content, flags=re.MULTILINE | re.IGNORECASE,
    )
    return match is not None


def build_frontmatter(content: str, name: str, description: str,
                      generated_from: str | None = None) -> str:
    """Replace name and description in YAML frontmatter.

    Preserves existing version/based-on fields.
    Emits generated-from field for template traceability.
    """
    if _YAML_AVAILABLE:
        removes = []
        updates = {"name": name, "description": description}
        if generated_from:
            updates["generated-from"] = generated_from
        else:
            removes.extend(["generated-from", "generated_from"])
        # D15: drop a redundant `hint` when it is identical to the description.
        # `hint` and `description` come from different template fields but often
        # carry the same text, wasting tokens in every generated agent file. The
        # AGENT_HINTS table is built from the source templates (build_agent_hints),
        # not from generated files, so dropping the duplicate here loses nothing.
        existing_hint = _parse_frontmatter_yaml(content).get("hint")
        if isinstance(existing_hint, str) and existing_hint.strip() == (description or "").strip():
            removes.append("hint")
        return _update_frontmatter_dict(
            content,
            updates=updates,
            removes=removes,
        )

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
    # Update or remove generated-from field
    if generated_from:
        if re.search(r'^generated-from:', content, flags=re.MULTILINE):
            content = re.sub(
                r'^generated-from:.*$',
                f'generated-from: {generated_from}',
                content, count=1, flags=re.MULTILINE,
            )
        else:
            content = re.sub(
                r'(^name:.*\n)',
                rf'\1generated-from: {generated_from}\n',
                content, count=1, flags=re.MULTILINE,
            )
    else:
        content = re.sub(
            r'^generated-from:.*\n',
            '',
            content, flags=re.MULTILINE,
        )
    return content


def inject_permission_mode_field(content: str, permission_mode: str) -> str:
    """Insert or update the permissionMode: field in YAML frontmatter.

    If permission_mode is empty, removes any existing permissionMode: field.
    If set, inserts/updates after the memory: line (or model: or name: as fallback).
    """
    if _YAML_AVAILABLE:
        if not permission_mode:
            return _update_frontmatter_dict(content, {}, removes=["permissionMode"])
        return _update_frontmatter_dict(content, {"permissionMode": permission_mode})

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
    if _YAML_AVAILABLE:
        if not memory:
            return _update_frontmatter_dict(content, {}, removes=["memory"])
        return _update_frontmatter_dict(content, {"memory": memory})

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
    if _YAML_AVAILABLE:
        if not model:
            return _update_frontmatter_dict(content, {}, removes=["model"])
        return _update_frontmatter_dict(content, {"model": model})

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



def target_filename(role: str, role_map: dict) -> str | None:
    """Return the output filename for a role, or None if not in role_map."""
    name = role_map.get(role)
    return (name + ".md") if name else None


def ext_target_filename(role: str, prefix: str) -> str:
    """Extension file name: <prefix>-<role>-ext.md (or <role>-ext.md if no prefix)."""
    if prefix:
        return f"{prefix}-{role}{EXT_SUFFIX}.md"
    return f"{role}{EXT_SUFFIX}.md"


def role_from_platform_file(filename: str, platforms: list[str]) -> str | None:
    stem = Path(filename).stem
    for platform in platforms:
        if stem.startswith(f"{platform}-"):
            return stem[len(platform) + 1:]
    return None


def _is_role_enabled(role: str, config: dict) -> bool:
    """Check if a role is enabled based on project config (e.g. systems-engineering flag)."""
    if role.startswith("se-"):
        se_config = config.get("systems-engineering") or {}
        return se_config.get("enabled", True)
    if role.startswith("knowledge-"):
        ke_config = config.get("knowledge-engine") or {}
        return ke_config.get("enabled", False)
    return True


# ---------------------------------------------------------------------------
# XML Section Wrapping — wraps Markdown sections in XML tags for LLM parsing
# ---------------------------------------------------------------------------

def wrap_sections_in_xml(content: str) -> str:
    """Wrap Markdown heading sections in XML tags.

    Transforms:
        ## Section Name
        content...
        ## Next Section

    Into:
        <section name="section-name">
        ## Section Name
        content...
        </section>
        <section name="next-section">
        ## Next Section
        ...
        </section>

    Only processes ## level headings (not # title or ### sub-sections).
    The XML tag name is derived from the heading: lowercase, spaces->hyphens,
    special chars removed.
    """
    lines = content.splitlines(keepends=True)
    if not lines:
        return content

    result = []
    current_section = None
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip('\n').rstrip('\r')

        # Detect ## level heading (exactly ##, not ### or higher)
        if stripped.startswith('## ') and not stripped.startswith('###'):
            # Close previous section if open
            if current_section is not None:
                result.append('</section>\n')

            # Derive XML-safe tag name from heading
            heading_text = stripped[3:].strip()  # Remove '## '
            tag_name = _make_xml_tag_name(heading_text)
            current_section = tag_name

            # Open new section
            result.append(f'<section name="{tag_name}">\n')
            result.append(line)
        else:
            result.append(line)

        i += 1

    # Close last section
    if current_section is not None:
        result.append('</section>\n')

    return ''.join(result)


def _make_xml_tag_name(heading: str) -> str:
    """Convert a Markdown heading to an XML-safe tag name.

    Rules: lowercase, spaces->hyphens, remove special chars,
    collapse multiple hyphens, strip leading/trailing hyphens.
    """
    name = heading.lower()
    name = name.replace(' ', '-')
    name = re.sub(r'[^a-z0-9-]', '', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    return name


# ---------------------------------------------------------------------------
# Critical Rules Footer — appends critical rules to the end of agent files
# ---------------------------------------------------------------------------

_CRITICAL_RULES = [
    "branch-guard",
    "commit-conventions",
    "dod-criteria",
]


def _extract_and_append_critical_footer(
    content: str,
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    provider: str = "Claude",
) -> str:
    """Append critical rules as a footer to generated agent content.

    Reads critical rule files, substitutes variables, strips frontmatter,
    and appends them as a '## Critical Rules' section at the end.

    Only rules that exist and are active (per rules-preset) are included.
    """
    from .config import substitute
    from .rules import collect_rule_sources, resolve_rules

    rule_options = resolve_rules(config, agent_meta_root)
    platforms = config.get("platforms", [])
    sources = collect_rule_sources(agent_meta_root, platforms)

    # Build a lookup: rule_stem -> source_path
    source_map: dict[str, Path] = {}
    for source_path, output_name in sources:
        rule_stem = Path(output_name).stem
        if rule_stem in _CRITICAL_RULES:
            source_map[rule_stem] = source_path

    footer_sections: list[str] = []
    for rule_name in _CRITICAL_RULES:
        source_path = source_map.get(rule_name)
        if not source_path or not source_path.exists():
            continue

        opts = rule_options.get(rule_name, {})
        # Skip if rule is disabled via rules-preset
        if opts.get("alwaysApply") is False and opts.get("embed") is False:
            continue

        rule_content = source_path.read_text(encoding="utf-8")
        rel_source = f"rules/{source_path.parts[-2]}/{source_path.name}"
        rule_content = substitute(rule_content, variables, rel_source, log)

        # Strip frontmatter if present
        body = _strip_frontmatter(rule_content).strip()
        if body:
            footer_sections.append(body)

    if not footer_sections:
        return content

    footer = "\n\n---\n\n## Critical Rules\n\n" + "\n\n---\n\n".join(footer_sections)
    return content.rstrip() + footer


# ---------------------------------------------------------------------------
# Path-based Contextual Rules — inject rules based on file path patterns
# ---------------------------------------------------------------------------

def apply_path_rules(
    content: str,
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    role: str,
) -> str:
    """Apply path-based contextual rules to agent content.

    Reads `pathRules` from config. Each rule has:
      - path: glob pattern (e.g. "*.py", "scripts/**", "agents/**/*.md")
      - rule: rule file name (stem) to include (e.g. "python-conventions")
      - agents: optional list of agent roles this rule applies to (default: all)

    Matching rules are read, variables substituted, and appended as
    "## Contextual Rules" section.
    """
    from .config import substitute
    from .rules import collect_rule_sources, resolve_rules

    path_rules = config.get("pathRules", [])
    if not path_rules:
        return content

    # Build rule lookup: stem -> source_path
    platforms = config.get("platforms", [])
    sources = collect_rule_sources(agent_meta_root, platforms)
    rule_options = resolve_rules(config, agent_meta_root)
    source_map: dict[str, Path] = {}
    for source_path, output_name in sources:
        rule_stem = Path(output_name).stem
        source_map[rule_stem] = source_path

    matched_sections: list[str] = []
    for rule_def in path_rules:
        path_pattern = rule_def.get("path", "")
        rule_name = rule_def.get("rule", "")
        agents = rule_def.get("agents")  # None = all agents

        # Check if rule applies to this agent
        if agents is not None and role not in agents:
            continue

        source_path = source_map.get(rule_name)
        if not source_path or not source_path.exists():
            log.warning(f"pathRules: rule file '{rule_name}' not found (pattern: '{path_pattern}')")
            continue

        opts = rule_options.get(rule_name, {})
        if opts.get("alwaysApply") is False and opts.get("embed") is False:
            continue

        rule_content = source_path.read_text(encoding="utf-8")
        rel_source = f"rules/{source_path.parts[-2]}/{source_path.name}"
        rule_content = substitute(rule_content, variables, rel_source, log)
        body = _strip_frontmatter(rule_content).strip()

        if body:
            matched_sections.append(f"### Rule for `{path_pattern}`\n\n{body}")

    if not matched_sections:
        return content

    footer = "\n\n---\n\n## Contextual Rules\n\n" + "\n\n---\n\n".join(matched_sections)
    return content.rstrip() + footer

def _split_frontmatter(content: str) -> tuple[str, str]:
    """Split content into (frontmatter_block, body).

    Returns ('', content) if no frontmatter found.
    frontmatter_block includes the surrounding '---' delimiters.
    """
    if not content.startswith("---"):
        return "", content
    end = content.find("\n---", 3)
    if end == -1:
        return "", content
    fm_block = content[: end + 4]   # includes closing ---
    body = content[end + 4:]        # everything after closing ---
    return fm_block, body


def _parse_frontmatter_yaml(content: str) -> dict:
    """Parse YAML frontmatter into a dict. Returns {} on failure or missing yaml."""
    if not _YAML_AVAILABLE:
        return {}
    fm_block, _ = _split_frontmatter(content)
    if not fm_block:
        return {}
    # Strip the --- delimiters for yaml.safe_load
    inner = re.sub(r"^---\n?", "", fm_block)
    inner = re.sub(r"\n?---\s*$", "", inner)
    try:
        result = _yaml.safe_load(inner)
        return result if isinstance(result, dict) else {}
    except _yaml.YAMLError:
        return {}


def _find_section_bounds(lines: list[str], anchor: str) -> tuple[int, int] | None:
    """Find (start, end) line indices for a section.

    Supports two anchor modes:
    - XML-tag anchor (e.g. '<workflow>'): start = line with opening tag,
      end = line after the matching closing '</tag>' (inclusive of close line).
    - Markdown heading anchor (e.g. '## Don\\'ts'): start = heading line,
      end = first line of next section at same or higher level (exclusive).
    """
    anchor_stripped = anchor.strip()

    # XML-anchor mode: anchor starts with '<' (e.g. '<workflow>')
    if anchor_stripped.startswith("<") and not anchor_stripped.startswith("</"):
        tag = anchor_stripped.strip("<>").strip()
        open_tag = f"<{tag}>"
        close_tag = f"</{tag}>"
        start_idx = None
        for i, line in enumerate(lines):
            if start_idx is None and open_tag in line:
                start_idx = i
            elif start_idx is not None and close_tag in line:
                return (start_idx, i + 1)
        return None  # tag not found or unclosed

    anchor_level = len(anchor_stripped) - len(anchor_stripped.lstrip("#"))

    start_idx = None
    for i, line in enumerate(lines):
        if line.rstrip() == anchor_stripped:
            start_idx = i
            break

    if start_idx is None:
        return None

    in_fence = False
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level <= anchor_level:
                return (start_idx, i)

    return (start_idx, len(lines))


def _dominant_newline(lines: list[str]) -> str:
    """Return the majority line-ending style ('\\r\\n' or '\\n') of a splitlines(keepends=True) list."""
    crlf_count = sum(1 for line in lines if line.endswith("\r\n"))
    lf_count = sum(1 for line in lines if line.endswith("\n") and not line.endswith("\r\n"))
    return "\r\n" if crlf_count > lf_count else "\n"


def _patch_append_after(content: str, anchor: str, patch_content: str,
                        log: SyncLog, source_label: str) -> str:
    """Insert patch_content after the section identified by anchor."""
    lines = content.splitlines(keepends=True)
    bounds = _find_section_bounds(lines, anchor)
    if bounds is None:
        log.warning(f"Composition patch 'append-after': anchor '{anchor}' not found in {source_label}")
        return content
    _, end_idx = bounds
    nl = _dominant_newline(lines)
    normalized_patch = patch_content.replace("\r\n", "\n").rstrip("\n").replace("\n", nl)
    patch_lines = (nl + nl + normalized_patch + nl + nl).splitlines(keepends=True)
    result_lines = lines[:end_idx] + patch_lines + lines[end_idx:]
    return "".join(result_lines)


def _patch_replace(content: str, anchor: str, patch_content: str,
                   log: SyncLog, source_label: str) -> str:
    """Replace the entire section identified by anchor with patch_content."""
    lines = content.splitlines(keepends=True)
    bounds = _find_section_bounds(lines, anchor)
    if bounds is None:
        log.warning(f"Composition patch 'replace': anchor '{anchor}' not found in {source_label}")
        return content
    start_idx, end_idx = bounds
    nl = _dominant_newline(lines)
    normalized_patch = patch_content.replace("\r\n", "\n").rstrip("\n").replace("\n", nl)
    patch_lines = (normalized_patch + nl).splitlines(keepends=True)
    result_lines = lines[:start_idx] + patch_lines + lines[end_idx:]
    return "".join(result_lines)


def _patch_delete(content: str, anchor: str, log: SyncLog, source_label: str) -> str:
    """Delete the entire section identified by anchor."""
    lines = content.splitlines(keepends=True)
    bounds = _find_section_bounds(lines, anchor)
    if bounds is None:
        log.warning(f"Composition patch 'delete': anchor '{anchor}' not found in {source_label}")
        return content
    start_idx, end_idx = bounds
    # Also remove leading blank line before section if present
    trim_start = start_idx
    if trim_start > 0 and lines[trim_start - 1].strip() == "":
        trim_start -= 1
    result_lines = lines[:trim_start] + lines[end_idx:]
    return "".join(result_lines)


def apply_patch(content: str, patch: dict, log: SyncLog, source_label: str) -> str:
    """Apply a single composition patch to content."""
    op = patch.get("op", "")
    anchor = patch.get("anchor", "")
    patch_content = patch.get("content", "")

    if op == "append":
        lines = content.splitlines(keepends=True)
        nl = _dominant_newline(lines)
        normalized_patch = patch_content.replace("\r\n", "\n").rstrip("\n").replace("\n", nl)
        return content.rstrip("\n").rstrip("\r") + nl + nl + normalized_patch + nl
    elif op == "append-after":
        return _patch_append_after(content, anchor, patch_content, log, source_label)
    elif op == "replace":
        return _patch_replace(content, anchor, patch_content, log, source_label)
    elif op == "delete":
        return _patch_delete(content, anchor, log, source_label)
    else:
        log.warning(f"Composition: unknown patch op '{op}' in {source_label}")
        return content


def _merge_frontmatter(base_content: str, override_fm: dict) -> str:
    """Replace the frontmatter block in base_content with values from override_fm.

    Fields 'extends' and 'patches' are stripped (composition metadata).
    All other override fields (name, version, description, hint, tools, based-on) win.
    """
    _, body = _split_frontmatter(base_content)
    if not _YAML_AVAILABLE:
        return base_content  # Cannot merge without yaml — return base unchanged

    # Parse base frontmatter
    base_fm = _parse_frontmatter_yaml(base_content)

    # Merge: base first, then override wins
    merged = {**base_fm, **override_fm}

    # Strip composition-only keys from the output frontmatter
    for key in ("extends", "patches"):
        merged.pop(key, None)

    # Serialize back to YAML
    try:
        new_fm_inner = _yaml.dump(merged, allow_unicode=True, default_flow_style=False,
                                  sort_keys=False).rstrip("\n")
    except _yaml.YAMLError:
        return base_content

    new_fm_block = f"---\n{new_fm_inner}\n---"
    return new_fm_block + body


def compose_agent(
    base_path: Path,
    override_content: str,
    log: SyncLog,
) -> str:
    """Load base template, apply patches from override frontmatter, merge frontmatter.

    Returns the composed document ready for variable substitution.
    """
    if not _YAML_AVAILABLE:
        log.warning(
            "PyYAML not available — composition skipped. "
            "Install it with: pip install pyyaml"
        )
        return override_content

    if not base_path.exists():
        log.warning(f"Composition: base template not found: {base_path}")
        return override_content

    base_content = base_path.read_text(encoding="utf-8")
    override_fm = _parse_frontmatter_yaml(override_content)
    patches = override_fm.get("patches") or []

    # Start from base, apply each patch
    result = base_content
    source_label = base_path.name
    for patch in patches:
        result = apply_patch(result, patch, log, source_label)

    # Merge frontmatter: override fields win over base fields
    result = _merge_frontmatter(result, override_fm)

    return result


def collect_sources(
    agent_meta_root: Path,
    platforms: list[str],
) -> tuple[dict[str, Path], set[str]]:
    """
    Returns (overrides, known_ext_roles).

    overrides: role → source_path for generated agents (.claude/agents/)
      Priority: 1-generic < 2-platform < 3-project/<role>.md (full override)

    known_ext_roles: roles that have a 3-project/<role>-ext.md in meta-repo.
      These are NOT used as templates — just signals that the role supports extensions.
      (Currently unused since 3-project/ in meta-repo has no templates by design.)
    """
    overrides: dict[str, Path] = {}
    known_ext_roles: set[str] = set()

    # 1. Generic agents (skip files starting with _ — reserved for resources/templates)
    generic_dir = agent_meta_root / AGENTS_DIR / GENERIC_DIR
    for f in sorted(generic_dir.glob("*.md")):
        if not f.name.startswith("_"):
            role = f.stem
            overrides[role] = f

    # 2. Platform agents
    platform_dir = agent_meta_root / AGENTS_DIR / PLATFORM_DIR
    for platform in platforms:
        for f in sorted(platform_dir.glob(f"{platform}-*.md")):
            role = role_from_platform_file(f.name, platforms)
            if role:
                overrides[role] = f

    # 3. Project-level agents (in meta-repo 3-project/)
    project_dir = agent_meta_root / AGENTS_DIR / PROJECT_DIR
    if project_dir.exists():
        for f in sorted(project_dir.glob("*.md")):
            stem = f.stem
            if stem.endswith(EXT_SUFFIX):
                known_ext_roles.add(stem[: -len(EXT_SUFFIX)])
            else:
                overrides[stem] = f

    # Filter out deprecated templates. Applied after the full override chain is
    # resolved so a non-deprecated 2-platform/3-project override can still win
    # over a deprecated 1-generic base (and vice versa: a deprecated override
    # removes the role entirely). This is the single central gate — all
    # consumers (agent generation, viz, CLAUDE.md hints/table) inherit it.
    for role in list(overrides):
        source_path = overrides[role]
        if is_deprecated_template(source_path.read_text(encoding="utf-8")):
            del overrides[role]

    return overrides, known_ext_roles


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
    if _YAML_AVAILABLE:
        return _update_frontmatter_dict(content, {}, removes=fields)

    import re as _re
    for field in fields:
        content = _re.sub(
            rf'^{_re.escape(field)}:.*\n', '', content, count=1, flags=_re.MULTILINE,
        )
    return content


def transform_agent_content_for_provider(
    content: str,
    provider: str,
    role: str,
    name: str,
    description: str,
    generated_from: str,
    config: dict,
    agent_meta_root: Path,
    project_root: Path,
    target_path: Path,
    provider_config: dict,
    log: SyncLog,
) -> str:
    from .roles import (        load_roles_config,        resolve_max_tokens,        resolve_memory,        resolve_model,        resolve_permission_mode,        resolve_steps,        resolve_temperature,    )
    if provider == 'Continue':
        # Continue agents: preserve original frontmatter, inject model/memory, add alwaysApply
        content = build_frontmatter(content, name, description, generated_from=generated_from)
        model = resolve_model(role, config, agent_meta_root,
                              provider=provider, provider_config=provider_config, log=log)
        if not model:
            # Continue has no model-tiers mapping; fall back to raw role-defaults value
            roles_cfg = load_roles_config(agent_meta_root)
            raw = roles_cfg["roles"].get(role, {}).get("model", "")
            if raw:
                model = raw
        content = inject_model_field(content, model)
        if model:
            po = config.get('model-overrides', {})
            is_override = (role in po.get('Continue', {})) or (
                role in po and not isinstance(po.get(role), dict)
            )
            src = 'project override' if is_override else 'meta default'
            log.info(str(target_path.relative_to(project_root)), f'model: {model} (from {src})')
        memory = resolve_memory(role, config, agent_meta_root)
        content = inject_memory_field(content, memory)
        if memory:
            src = 'project override' if role in config.get('memory-overrides', {}) else 'meta default'
            log.info(str(target_path.relative_to(project_root)), f'memory: {memory} (from {src})')
        permission_mode = resolve_permission_mode(role, config, agent_meta_root)
        content = inject_permission_mode_field(content, permission_mode)
        if permission_mode:
            src = 'project override' if role in config.get('permission-mode-overrides', {}) else 'meta default'
            log.info(str(target_path.relative_to(project_root)), f'permissionMode: {permission_mode} (from {src})')
        content = _update_frontmatter_dict(content, {"alwaysApply": False})
        # Continue has no frontmatter tools model — validate and remove template tools
        _continue_fm = _parse_frontmatter_yaml(content)
        _continue_tools = _continue_fm.get('tools')
        if isinstance(_continue_tools, list):
            _validate_tools_against_whitelist(
                _continue_tools, provider, agent_meta_root, log, role,
            )
        content = _remove_frontmatter_fields(content, ['tools'])
        body = _strip_frontmatter(content)
        body = _strip_claude_specific_lines(body)
        
        # Sanitize standalone --- in the body to avoid breaking Continue's YAML parsing
        import re as _re
        body = _re.sub(r'(?m)^---$', '___', body)
        
        fm_end = content.find('\n---', 3)
        if fm_end != -1:
            content = content[:fm_end + 4] + '\n' + body.lstrip('\n')
    else:
        content = build_frontmatter(content, name, description, generated_from=generated_from)

        if provider == 'Claude':
            model = resolve_model(role, config, agent_meta_root,
                                  provider=provider, provider_config=provider_config, log=log)
            content = inject_model_field(content, model)
            if model:
                po = config.get('model-overrides', {})
                is_override = (role in po.get('Claude', {})) or (
                    role in po and not isinstance(po.get(role), dict)
                )
                src = 'project override' if is_override else 'meta default'
                log.info(str(target_path.relative_to(project_root)), f'model: {model} (from {src})')

            memory = resolve_memory(role, config, agent_meta_root)
            content = inject_memory_field(content, memory)
            if memory:
                src = 'project override' if role in config.get('memory-overrides', {}) else 'meta default'
                log.info(str(target_path.relative_to(project_root)), f'memory: {memory} (from {src})')

            permission_mode = resolve_permission_mode(role, config, agent_meta_root)
            content = inject_permission_mode_field(content, permission_mode)
            if permission_mode:
                src = 'project override' if role in config.get('permission-mode-overrides', {}) else 'meta default'
                log.info(str(target_path.relative_to(project_root)), f'permissionMode: {permission_mode} (from {src})')

            # Validate tools against whitelist — log warnings but keep tools (Claude supports them natively)
            _claude_fm = _parse_frontmatter_yaml(content)
            _claude_tools = _claude_fm.get('tools')
            if isinstance(_claude_tools, list):
                _validate_tools_against_whitelist(
                    _claude_tools, provider, agent_meta_root, log, role,
                )

        elif provider == 'Gemini':
            # Gemini: provider-mapped model only; strip unsupported sampling
            # parameters (temperature, top_p, top_k, stop_sequences,
            # max_output_tokens) plus memory and permissionMode, then
            # strip Claude-specific lines.
            model = resolve_model(role, config, agent_meta_root,
                                  provider=provider, provider_config=provider_config, log=log)
            content = inject_model_field(content, model)
            if model:
                po = config.get('model-overrides', {})
                is_override = role in po.get('Gemini', {})
                src = 'project override' if is_override else 'meta default'
                log.info(str(target_path.relative_to(project_root)), f'model: {model} (from {src})')
            # Map generic tool names to Gemini-native tools
            _gemini_fm = _parse_frontmatter_yaml(content)
            _gemini_tools = _gemini_fm.get('tools')
            if isinstance(_gemini_tools, list):
                # Validate against provider whitelist first
                _gemini_valid_tools = _validate_tools_against_whitelist(
                    _gemini_tools, provider, agent_meta_root, log, role,
                )
                content = _update_frontmatter_dict(content, {'tools': _gemini_valid_tools})
            content = _remove_frontmatter_fields(
                content,
                [
                    'memory',
                    'permissionMode',
                    'temperature',
                    'top_p',
                    'top_k',
                    'stop_sequences',
                    'max_output_tokens',
                ]
            )
            body = _strip_frontmatter(content)
            body = _strip_claude_specific_lines(body)
            fm_end = content.find('\n---', 3)
            if fm_end != -1:
                # Gemini agents are API-registered, not file-discovered —
                # without the session bootstrap this file has no effect.
                registration_note = (
                    "> **Registrierung erforderlich:** Dieser Agent wird zur Laufzeit "
                    "via `define_subagent` registriert — er ist NICHT automatisch aktiv. "
                    f"Bootstrap-Instruktionen: `{provider_config.get(provider, {}).get('context_file', '.gemini/GEMINI.md')}` "
                    "(Block `agent-meta:bootstrap`).\n"
                )
                content = (content[:fm_end + 4] + '\n' + registration_note
                           + '\n' + body.lstrip('\n'))

        elif provider == 'Opencode':
            # Opencode: native frontmatter (description + mode: subagent + model)
            # Model IDs use "provider/model-id" format (e.g. anthropic/claude-sonnet-4-6)
            model = resolve_model(role, config, agent_meta_root,
                                  provider=provider, provider_config=provider_config, log=log)
            if model:
                po = config.get('model-overrides', {})
                is_override = role in po.get('Opencode', {})
                src = 'project override' if is_override else 'meta default'
                log.info(str(target_path.relative_to(project_root)), f'model: {model} (from {src})')
            temperature = resolve_temperature(role, config, agent_meta_root)
            if temperature:
                src = 'project override' if role in config.get('temperature-overrides', {}) else 'meta default'
                log.info(str(target_path.relative_to(project_root)), f'temperature: {temperature} (from {src})')
            max_tokens = resolve_max_tokens(role, config, agent_meta_root)
            if max_tokens:
                mt_src = 'project override' if role in config.get('max-tokens-overrides', {}) else 'meta default'
                log.info(str(target_path.relative_to(project_root)), f'max_tokens: {max_tokens} (from {mt_src})')
            steps = resolve_steps(role, config, agent_meta_root)
            if steps:
                src = 'project override' if role in config.get('steps-overrides', {}) else 'meta default'
                log.info(str(target_path.relative_to(project_root)), f'steps: {steps} (from {src})')
            # Validate tools against provider whitelist before transformation
            _opencode_fm = _parse_frontmatter_yaml(content)
            _opencode_raw_tools = _opencode_fm.get('tools')
            if isinstance(_opencode_raw_tools, list):
                _opencode_valid_tools = _validate_tools_against_whitelist(
                    _opencode_raw_tools, provider, agent_meta_root, log, role,
                )
                # Replace tools with validated subset before transformation
                content = _update_frontmatter_dict(content, {'tools': _opencode_valid_tools})
            content = _transform_frontmatter_for_opencode(
                content, name, description, model, steps, generated_from, agent_meta_root, temperature
            )

        elif provider == 'Copilot':
            # Copilot: frontmatter without model/memory/permissionMode/tools
            # Uses IDE-configured models — no per-agent model field
            content = build_frontmatter(content, name, description, generated_from=generated_from)
            content = _remove_frontmatter_fields(content, [
                'memory', 'permissionMode', 'temperature', 'top_p', 'top_k',
                'stop_sequences', 'max_output_tokens', 'tools',
            ])
            body = _strip_frontmatter(content)
            body = _strip_claude_specific_lines(body)
            fm_end = content.find('\n---', 3)
            if fm_end != -1:
                content = content[:fm_end + 4] + '\n' + body.lstrip('\n')
            else:
                content = body.lstrip('\n')

        elif provider == 'Mammouth':
            # Mammouth Code agent: supports model, permissionMode, and tools fields.
            content = build_frontmatter(content, name, description, generated_from=generated_from)
            model = resolve_model(role, config, agent_meta_root,
                                  provider=provider, provider_config=provider_config, log=log)
            content = inject_model_field(content, model)
            if model:
                po = config.get('model-overrides', {})
                is_override = (role in po.get('Mammouth', {})) or (
                    role in po and not isinstance(po.get(role), dict)
                )
                src = 'project override' if is_override else 'meta default'
                log.info(str(target_path.relative_to(project_root)), f'model: {model} (from {src})')

            permission_mode = resolve_permission_mode(role, config, agent_meta_root)
            content = inject_permission_mode_field(content, permission_mode)
            if permission_mode:
                src = 'project override' if role in config.get('permission-mode-overrides', {}) else 'meta default'
                log.info(str(target_path.relative_to(project_root)), f'permissionMode: {permission_mode} (from {src})')

            _mammouth_fm = _parse_frontmatter_yaml(content)
            _mammouth_tools = _mammouth_fm.get('tools')
            if isinstance(_mammouth_tools, list):
                _validate_tools_against_whitelist(
                    _mammouth_tools, provider, agent_meta_root, log, role,
                )

            content = _remove_frontmatter_fields(content, [
                'memory', 'temperature', 'top_p', 'top_k',
                'stop_sequences', 'max_output_tokens',
            ])
            body = _strip_frontmatter(content)
            body = _strip_claude_specific_lines(body)
            fm_end = content.find('\n---', 3)
            if fm_end != -1:
                content = content[:fm_end + 4] + '\n' + body.lstrip('\n')
            else:
                content = body.lstrip('\n')

    # Visualization: inject event-logging prompt block when dynamic/full mode is enabled
    # Applies to ALL providers — every generated agent gets the viz reporting block
    viz_cfg = config.get('viz', {})
    if viz_cfg.get('enabled', False) and viz_cfg.get('mode') in ('dynamic', 'full'):
        from .viz import inject_viz_prompt_block
    return content


def sync_agents_for_provider(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict,
    platform_vars: dict | None = None,
    debug_mode: bool = False,
):
    """Generate agent files for a specific provider.

    Claude:    .claude/agents/<role>.md   — full frontmatter, all fields
    Gemini:    .gemini/agents/<role>.md   — frontmatter without permissionMode/memory
    Continue:  .continue/agents/<role>.md — minimal frontmatter (name, description, alwaysApply: false)
    """
    from .config import strip_inactive_conditional_blocks, substitute
    from .pipelines import (
        apply_overrides,
        inject_pipeline_blocks,
        load_quality_pipelines,
    )
    from .platform import substitute_platform
    from .roles import (
        build_role_map,
        load_roles_config,
        resolve_max_tokens,
        resolve_memory,
        resolve_model,
        resolve_permission_mode,
        resolve_steps,
        resolve_temperature,
    )
    from .skills import _skill_is_active, _normalize_project_skills, load_external_skills_config

    pc = provider_config.get(provider)
    if not pc:
        log.warning(f"Unknown provider '{provider}' — skipping agent sync")
        return

    role_map = build_role_map(agent_meta_root)
    platforms = config.get('platforms', [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    target_dir = project_root / pc['agents_dir']

    allowed_roles = set(config['roles']) if 'roles' in config else None

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    expected_filenames: set = set()
    project_name = config.get('project', {}).get('name', 'unknown')

    for role, source_path in overrides.items():
        filename = target_filename(role, role_map)
        if not filename:
            if provider == 'Claude':
                log.skip(str(source_path.name), 'role not in ROLE_MAP')
            continue

        if allowed_roles is not None and role not in allowed_roles:
            if provider == 'Claude':
                rel = (str(target_dir / filename)
                       .replace(str(project_root) + '/', '')
                       .replace(str(project_root) + chr(92), ""))
                log.skip(rel, f"role '{role}' not in config['roles']")
            continue

        if not _is_role_enabled(role, config):
            if provider == 'Claude':
                rel = (str(target_dir / filename)
                       .replace(str(project_root) + '/', '')
                       .replace(str(project_root) + chr(92), ""))
                if role.startswith("knowledge-"):
                    log.skip(rel, "knowledge-engine is disabled")
                else:
                    log.skip(rel, "systems-engineering is disabled")
            continue

        # Skip orchestrator agent file in main-chat mode — no orchestrator subagent
        # is spawned; the main chat acts as router + worker. Not added to
        # expected_filenames so any stale orchestrator.md gets pruned.
        if role == "orchestrator" and variables.get("ORCH_MODE_MAIN_CHAT") == "true":
            if provider == 'Claude':
                rel = (str(target_dir / filename)
                       .replace(str(project_root) + '/', '')
                       .replace(str(project_root) + chr(92), ""))
                log.skip(rel, "orchestrator skipped — ORCH_MODE_MAIN_CHAT active")
            continue

        expected_filenames.add(filename)
        target_path = safe_path(target_dir, filename)
        content = source_path.read_text(encoding='utf-8')

        # Composition mode
        extends_base = extract_frontmatter_field(content, 'extends')
        if extends_base:
            base_path = agent_meta_root / AGENTS_DIR / extends_base
            content = compose_agent(base_path, content, log)
            if provider == 'Claude':
                log.info(
                    str(target_path.relative_to(project_root)),
                    f'composed from {extends_base} + {source_path.name}',
                )

        # Capture spawn capability from the (composed) source frontmatter before
        # any provider-specific tool transformation mangles the tools field.
        _can_spawn = _tools_can_spawn(_parse_frontmatter_yaml(content).get('tools'))

        rel_source = str(source_path.relative_to(agent_meta_root))
        source_version = extract_frontmatter_field(content, 'version')
        template_description = extract_frontmatter_field(content, 'description')
        description = (template_description or f'Agent for {project_name}.')
        description = description.replace('{{PROJECT_NAME}}', project_name)

        # Merge provider-specific variables (extension paths, snippets dir, parallel patterns, etc.)
        from .delegation_syntax import DelegationSyntaxEngine
        _ds_engine = DelegationSyntaxEngine(config_dir=agent_meta_root / "config")
        file_based = _ds_engine.has_file_based_agents(provider)
        provider_vars = {
            'EXTENSION_DIR': pc.get('extension_dir', f".{provider.lower()}/3-project"),
            'SNIPPETS_DIR': pc.get('snippets_dir', f".{provider.lower()}/snippets"),
            'PENDING_TASKS_FILE': pc.get('pending_tasks_file', f".{provider.lower()}/pending-tasks.md"),
            'SKILLS_DIR': pc.get('skills_dir', f".{provider.lower()}/skills"),
            'CONTEXT_FILE': pc.get('context_file', f"{provider.upper()}.md"),
            'FILE_BASED_AGENTS': 'true' if file_based else 'false',
        }
        merged_vars = {**variables, **provider_vars}

        # Inject provider-specific pipeline blocks before standard substitution
        pipelines = load_quality_pipelines(str(agent_meta_root))
        pipeline_overrides = config.get("quality-pipelines", {})
        effective = apply_overrides(pipelines, pipeline_overrides)
        if effective:
            from .dod import resolve_dod

            dod_resolved = resolve_dod(config, agent_meta_root)
            content = inject_pipeline_blocks(content, effective, provider, dod_resolved)

        content = substitute(content, merged_vars, rel_source, log)
        # Apply PAL delegation syntax per provider (Issue #277).
        # Must run BEFORE strip_inactive_conditional_blocks — its final cleanup
        # removes ALL {{#if}} markers, which would strip {{#if PAL_*}} blocks
        # before the engine can evaluate them per provider.
        from .delegation_syntax import DelegationSyntaxEngine
        pal_engine = DelegationSyntaxEngine(config_dir=agent_meta_root / "config")
        content = pal_engine.apply(content, provider, log=log)
        content = strip_inactive_conditional_blocks(content, variables)
        # Apply platform-config substitution ({{platform.*}} placeholders)
        if platform_vars is not None:
            content = substitute_platform(content, platform_vars, rel_source, log)

        name = Path(filename).stem
        layer = source_path.parts[-2]
        source_label = f'{layer}/{source_path.name}'
        generated_from = f'{source_label}@{source_version}' if source_version else source_label

        content = transform_agent_content_for_provider(
            content=content,
            provider=provider,
            role=role,
            name=name,
            description=description,
            generated_from=generated_from,
            config=config,
            agent_meta_root=agent_meta_root,
            project_root=project_root,
            target_path=target_path,
            provider_config=provider_config,
            log=log,
        )

        # MCP toolset: bind the servers this role opted into (issue #467).
        # Claude-only — `mcp__<server>__<tool>` is Claude Code's namespacing;
        # other providers surface MCP tools through their own config, not
        # through agent frontmatter.
        if provider == 'Claude':
            mcp_tools = resolve_mcp_tools_for_role(role, config, agent_meta_root, project_root)
            if mcp_tools:
                before = content
                content = append_frontmatter_tools(content, mcp_tools)
                if content != before:
                    servers = ', '.join(sorted({t.split('__')[1] for t in mcp_tools}))
                    log.info(str(target_path.relative_to(project_root)),
                             f'mcp tools: +{len(mcp_tools)} from {servers}')

        # Visualization: inject event-logging prompt block when dynamic/full mode is enabled
        # Applies to ALL providers — every generated agent gets the viz reporting block
        viz_cfg = config.get('viz', {})
        if viz_cfg.get('enabled', False) and viz_cfg.get('mode') in ('dynamic', 'full'):
            from .viz import inject_viz_prompt_block
            content = inject_viz_prompt_block(content, role, provider, viz_enabled=viz_cfg.get('enabled', False), agent_meta_root=agent_meta_root,
                                              viz_debug=viz_cfg.get("debug", False))

        if debug_mode:
            content = inject_debug_block(content, name)

        # Critical Rules Footer: append critical rules to end of agent files
        footer_cfg = config.get('critical-rules-footer', {})
        if footer_cfg.get('enabled', False):
            content = _extract_and_append_critical_footer(
                content, agent_meta_root, config, variables, log, provider
            )

        # Path-based Contextual Rules: inject rules based on path patterns
        path_rules_cfg = config.get('pathRules', [])
        if path_rules_cfg:
            content = apply_path_rules(
                content, agent_meta_root, config, variables, log, role
            )

        # XML Section Wrapping: wrap Markdown ## sections in XML tags
        xml_cfg = config.get('xml-section-wrapping', {})
        if xml_cfg.get('enabled', False):
            content = wrap_sections_in_xml(content)

        # Singleton-Constraint: inject guard block into all non-orchestrator agent files
        SINGLETON_CONSTRAINT_BLOCK = (
            "\n\n## Singleton-Regel: Orchestrator-Spawn (auto-generated)\n\n"
            "**NIEMALS** `task(subagent_type=\"orchestrator\", ...)` oder "
            "`Agent(subagent_type=\"orchestrator\", ...)` aufrufen.\n\n"
            "- Es existiert genau **EIN Orchestrator** pro Session — der vom `main_chat` gespawnte.\n"
            "- Mehrere Orchestrator-Instanzen verursachen Routing-Konflikte und Session-State-Korruption.\n"
            "- Bei unklarem Routing: Ergebnis an den Aufrufer zurückgeben, nicht weiter delegieren.\n\n"
            "> Durchgesetzt via `rules/1-generic/a2a-delegation-gates.md` Gate #5.\n"
        )
        # Only agents that can actually spawn sub-agents (Agent/Task tool) need
        # the singleton guard — injecting it into non-spawning agents is wasted context.
        if role != "orchestrator" and not role.endswith("-iteration") and _can_spawn:
            content = content.rstrip() + SINGLETON_CONSTRAINT_BLOCK

        rel_label = str(source_path.relative_to(agent_meta_root / AGENTS_DIR))
        rel_out = str(target_path.relative_to(project_root))
        allow_secrets = config.get("allow-committed-secrets", False) if config else False
        if write_checked(target_path, content, log, rel_label, config=config, dry_run=dry_run, allow_secrets=allow_secrets):
            log.action('WRITE', rel_out, rel_label)
        else:
            log.skip(rel_out, 'unchanged')

    # External skill filenames are always in .claude/agents/ (Claude only)
    if provider == 'Claude':
        ext_config = load_external_skills_config(agent_meta_root)
        project_skills = _normalize_project_skills(config.get('external-skills', {}))
        for skill_name, skill_cfg in ext_config.get('skills', {}).items():
            if _skill_is_active(skill_name, skill_cfg, project_skills):
                ext_role = skill_cfg.get('role', skill_name)
                expected_filenames.add(f'{ext_role}.md')

    # Remove stale agent files
    if target_dir.exists():
        managed_index = target_dir / '.agent-meta-managed'
        previously_managed: set = set()
        if managed_index.exists():
            for line in managed_index.read_text(encoding='utf-8').splitlines():
                if line.strip():
                    previously_managed.add(line.strip())

        for existing_file in sorted(target_dir.glob('*.md')):
            if existing_file.name not in expected_filenames:  # noqa: SIM102
                if not managed_index.exists() or existing_file.name in previously_managed:
                    log.action('DELETE', str(existing_file.relative_to(project_root)),
                               'role removed from config')
                    if not dry_run:
                        existing_file.unlink()

        if not dry_run and expected_filenames:
            managed_index.write_text(
                '\n'.join(sorted(expected_filenames)) + '\n', encoding='utf-8'
            )

    # Gemini Bootstrap: inject session-start instructions into GEMINI.md (Issue #277)
    if provider == "Gemini":
        _inject_gemini_bootstrap(provider, target_dir, agent_meta_root, project_root, pc, log, dry_run)

    # Continue Bootstrap: update .continue/config.yaml with agent entries (Issue #277)
    if provider == "Continue":
        from .bootstrap import BootstrapEngine
        bootstrap_engine = BootstrapEngine(config_dir=agent_meta_root / "config")
        bootstrap_config = bootstrap_engine.get_bootstrap_config(provider)
        if bootstrap_config.get("action") == "update-config":
            result = bootstrap_engine.run_bootstrap(provider, target_dir, project_root)
            if result.get("status") == "success":
                rel_target = str(target_dir.relative_to(project_root))
                log.info(rel_target, f"Continue config updated: {result.get('agent_count', 0)} agents")


def _inject_gemini_bootstrap(
    provider: str,
    target_dir: Path,
    agent_meta_root: Path,
    project_root: Path,
    pc: dict[str, str],
    log: SyncLog,
    dry_run: bool,
) -> None:
    from .bootstrap import BootstrapEngine

    bootstrap_engine = BootstrapEngine(config_dir=agent_meta_root / "config")
    bootstrap_config = bootstrap_engine.get_bootstrap_config(provider)

    if bootstrap_config.get("action") != "inject-bootstrap-instructions":
        return

    bootstrap_instructions = bootstrap_engine.generate_gemini_bootstrap_instructions(target_dir)
    if not bootstrap_instructions:
        return

    context_file = pc.get("context_file", ".gemini/GEMINI.md")
    # Validate context_file does not escape project_root (path traversal guard)
    resolved = (project_root / context_file).resolve()
    if project_root.resolve() not in resolved.parents and resolved != project_root.resolve():
        log.warning(f"{context_file} path escapes project root — skipping bootstrap injection")
        return

    gemini_md_path = project_root / context_file
    if not gemini_md_path.exists():
        log.warning(f"{gemini_md_path.relative_to(project_root)!s} does not exist — cannot inject bootstrap instructions")
        return

    existing = gemini_md_path.read_text(encoding="utf-8")
    bootstrap_marker_begin = "<!-- agent-meta:bootstrap-begin -->"
    bootstrap_marker_end = "<!-- agent-meta:bootstrap-end -->"
    bootstrap_block = f"{bootstrap_marker_begin}\n{bootstrap_instructions}\n{bootstrap_marker_end}"

    if bootstrap_marker_begin in existing:
        pattern = re.compile(
            re.escape(bootstrap_marker_begin) + ".*?" + re.escape(bootstrap_marker_end),
            re.DOTALL,
        )
        new_content = pattern.sub(bootstrap_block, existing, count=1)
    else:
        new_content = existing.rstrip("\n") + "\n\n" + bootstrap_block + "\n"

    if new_content != existing:
        log.action("UPDATE", str(gemini_md_path.relative_to(project_root)), "bootstrap instructions")
        if not dry_run:
            gemini_md_path.write_text(new_content, encoding="utf-8")
    else:
        log.skip(str(gemini_md_path.relative_to(project_root)), "bootstrap instructions unchanged")


_DEBUG_BLOCK_MARKER = "<!-- agent-meta:debug-mode -->"

_DEBUG_BLOCK_TEMPLATE = """\

---

{marker}
## Debug-Modus

**Aktiv.** Starte jede Antwort mit: `[Agent: {agent_name}]`

Bei jeder Delegation an einen Sub-Agenten:
```
→ Delegiere an: <agent-name> — <kurze Aufgabenbeschreibung>
```

Am Ende jeder Antwort:
```
✓ [Agent: {agent_name}] fertig
```
"""


def inject_debug_block(content: str, agent_name: str) -> str:
    """Append a debug-mode instructions block to agent content.

    Only called when debug-mode: true is set in project.yaml.
    When not called (debug-mode: false, the default), content is unchanged.
    """
    if _DEBUG_BLOCK_MARKER in content:
        return content
    return content.rstrip("\n") + _DEBUG_BLOCK_TEMPLATE.format(
        marker=_DEBUG_BLOCK_MARKER,
        agent_name=agent_name,
    )


def _map_claude_tools_to_gemini_tools(tools: list) -> list[str]:
    """Map Claude Code tool names to Gemini native tool names.

    Gemini available tools: code_execution, google_search, url_context.
    File system tools (Read, Write, Edit, Glob, Grep) are automatically
    active in the Gemini sandbox and don't need explicit mapping.
    """
    mapping = {
        "Bash": "code_execution",
        "WebSearch": "google_search",
        "WebFetch": "url_context",
    }
    mapped: set[str] = set()
    for t in tools:
        if isinstance(t, str) and t in mapping:
            mapped.add(mapping[t])
    return sorted(mapped)


def _map_claude_tools_to_opencode_permissions(
    tools: list,
    deny_list: list[str] | None = None,
) -> dict[str, str]:
    """Map Claude Code tool names to opencode permission keys.

    opencode uses a permission-based model (tools frontmatter is deprecated).
    Each mapped key is set to 'allow'. Unknown tools are ignored.

    If deny_list is provided, those permissions are set to 'deny'
    when not explicitly allowed by the template tools.

    Known mappings:
      Bash -> bash
      Read -> read
      Write / Edit -> edit  (write/edit/apply_patch gated by edit permission)
      Glob -> glob
      Grep -> grep
      WebFetch -> webfetch
      WebSearch -> websearch
      Agent -> task          (subagent invocation via task tool)
      TodoWrite -> todowrite
    """
    mapping = {
        "Agent": "task",
        "TodoWrite": "todowrite",
        "Bash": "bash",
        "Read": "read",
        "Write": "edit",
        "Edit": "edit",
        "Glob": "glob",
        "Grep": "grep",
        "WebFetch": "webfetch",
        "WebSearch": "websearch",
    }
    perms: dict[str, str] = {}

    # Allow-mapping
    for t in tools:
        if isinstance(t, str) and t in mapping:
            perms[mapping[t]] = "allow"

    # Deny-mapping
    if deny_list:
        for tool_name in deny_list:
            if tool_name in mapping and mapping[tool_name] not in perms:
                perms[mapping[tool_name]] = "deny"

    return perms


def _transform_frontmatter_for_opencode(
    content: str,
    name: str,
    description: str,
    model: str,
    steps: str,
    generated_from: str,
    agent_meta_root: Path,
    temperature: str = "",
) -> str:
    """Build opencode-native agent frontmatter.

    opencode frontmatter schema:
      name: <role>
      description: "..."
      mode: subagent
      model: provider/model-id (optional)
      steps: <int> (optional)
      permission:             (mapped from template frontmatter tools)
        <key>: allow
    """
    body = _strip_frontmatter(content)
    body = _strip_claude_specific_lines(body)

    template_fm = _parse_frontmatter_yaml(content)

    # Preserve original fields and add/update opencode-specific ones
    updates: dict = {
        "name": name,
        "description": description,
        "mode": template_fm.get("mode") or "subagent",
    }
    if template_fm.get("version"):
        updates["version"] = template_fm.get("version")
    if generated_from:
        updates["generated-from"] = generated_from
    if model:
        updates["model"] = model
    if steps:
        updates["steps"] = steps
    if "steps" in template_fm:
        updates["steps"] = template_fm["steps"]
    if "maxSteps" in template_fm:
        updates["steps"] = template_fm["maxSteps"]

    # Map template tools to opencode permission block
    template_tools = template_fm.get("tools")
    if isinstance(template_tools, list) and template_tools:
        provider_tools_cfg = load_provider_tools_config(agent_meta_root)
        deny_list = provider_tools_cfg.get("opencode_deny_critical", [])
        perms = _map_claude_tools_to_opencode_permissions(
            template_tools, deny_list=deny_list
        )
        if perms:
            updates["permission"] = perms

    # Preserve temperature: template frontmatter takes precedence over role defaults
    if "temperature" in template_fm:
        updates["temperature"] = template_fm["temperature"]
    elif temperature:
        updates["temperature"] = float(temperature)

    # Preserve max_tokens: template frontmatter takes precedence over role defaults
    if "max_tokens" in template_fm:
        updates["max_tokens"] = template_fm["max_tokens"]

    removes = [
        "tools",
        "generated_from",
        "permissionMode",
        "alwaysApply",
        "top_p",
        "top_k",
        "stop_sequences",
        "max_output_tokens",
        "hint",
        "based-on",
        "based_on",
        "maxSteps",
        "memory",
    ]

    content = _update_frontmatter_dict(content, updates, removes=removes)

    # Replace body with stripped version
    fm_end = content.find('\n---', 3)
    if fm_end != -1:
        content = content[:fm_end + 4] + '\n' + body.lstrip('\n')

    return content


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


def _make_slim_body(content: str) -> str:
    """Reduce agent body to a compact prompt-friendly version.

    Keeps: role description, active DoD table, core workflow steps, Don'ts.
    Strips: extension hooks, verbose sub-sections, examples.
    """
    lines = content.splitlines()
    out = []
    skip_section = False
    slim_stop_anchors = {
        "## Workflow",
        "## Workflows",
        "## Schritt-für-Schritt",
        "## Beispiele",
        "## Beispiel",
        "## Anhang",
    }

    for line in lines:
        stripped = line.strip()
        # Skip extension-hook lines (Claude-specific)
        if stripped.startswith("> **Extension:**"):
            continue
        # Detect section changes
        if stripped.startswith("## "):
            skip_section = stripped in slim_stop_anchors
        if not skip_section:
            out.append(line)

    # Cap at ~80 lines for slim mode
    if len(out) > 80:
        out = out[:80]
        out.append("\n\n*[Prompt truncated — use agent mode for full context]*")

    return "\n".join(out)


def build_knowledge_engine_hints(config: dict) -> str:
    """Generate the Knowledge Engine instructions block if enabled in config."""
    lines = []
    ke_config = config.get("knowledge-engine", {})
    if ke_config.get("enabled", False):
        bundle = ke_config.get("bundle-path", "knowledge")
        domain = ke_config.get("domain", "research")
        wiki = f"{bundle}/wiki"
        sources = f"{bundle}/sources"

        lines.append("## Knowledge Engine")
        lines.append("")
        lines.append(f"Die Knowledge Engine ist aktiviert. Domäne: **{domain}**.")
        lines.append("")
        lines.append(f"**Bundle-Pfad:** `{bundle}/`")
        lines.append("| Pfad | Zweck |")
        lines.append("|------|-------|")
        lines.append(f"| `{bundle}/schema.md` | Steuerungsdokument — Konventionen, Concept Types, Workflows |")
        lines.append(f"| `{sources}/` | Immutable Raw Sources — LLM liest, modifiziert NIEMALS |")
        lines.append(f"| `{wiki}/` | OKF Knowledge Bundle — LLM-owned, strukturiertes Wiki |")
        lines.append(f"| `{wiki}/index.md` | Content-Katalog aller Wiki-Seiten (OKF §6) |")
        lines.append(f"| `{wiki}/log.md` | Chronologisches Event-Log (OKF §7) |")
        lines.append("")
        lines.append("### Knowledge-Agenten")
        lines.append(f"- **Schema-Owner:** `knowledge-curator` verwaltet `{bundle}/schema.md` und Concept-Type-Konventionen")
        lines.append("")
        lines.append("### Knowledge-Workflows")
        lines.append(f"- **Ingest:** Source in `{sources}/` ablegen → `knowledge-ingestor` verarbeitet → Wiki aktualisiert")
        lines.append("- **Query:** Frage stellen → `knowledge-querier` durchsucht Index → synthetisiert Antwort")
        lines.append("- **Lint:** `knowledge-linter` prüft Wiki-Gesundheit (Widersprüche, Orphans, OKF-Compliance)")
        lines.append("- **Migration:** `knowledge-migrator` räumt vorhandene Inhalte auf und migriert ins OKF-Format")
        lines.append("- **Gardening:** `knowledge-gardener` pflegt Links, Tags, Typos, Timestamps")
        
    return "\n".join(lines)


def build_agent_hints(config: dict, agent_meta_root: Path, include_table: bool = True) -> str:
    """Generate agent usage hints for {{AGENT_HINTS}}.

    Reads hint (preferred) or description from each active agent's template frontmatter.
    If orchestrator is active, adds a prominent start hint.

    include_table:
      True  → full output: entry-point hint + per-agent role/description table.
      False → entry-point hint only. Used for providers (e.g. Claude) that inject
              agent descriptions natively — the table would be a ~1.5 KB duplication.
    """
    from .roles import build_role_map

    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    role_map = build_role_map(agent_meta_root)
    allowed_roles: set[str] | None = None
    if "roles" in config:
        allowed_roles = set(config["roles"])

    lines = []
    # Determine if main-chat mode is active (no orchestrator subagent in this mode)
    _orch_cfg = config.get("orchestrator", {})
    _orch_mode_explicit = _orch_cfg.get("mode")
    if _orch_mode_explicit is not None:
        _is_main_chat_mode = str(_orch_mode_explicit).strip().lower() == "main-chat"
    else:
        # Legacy fallback: enabled=false was the old way to disable orchestrator
        _is_main_chat_mode = not _orch_cfg.get("enabled", True)

    has_orchestrator = (
        "orchestrator" in overrides
        and (allowed_roles is None or "orchestrator" in allowed_roles)
        and not _is_main_chat_mode
    )
    if has_orchestrator:
        lines.append(
            "> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben — Ausnahmen siehe Abschnitt »Orchestrator — Universal Router«."
        )
    elif _is_main_chat_mode:
        lines.append(
            "> **Einstiegspunkt:** Du bist im `main-chat` Modus. Du agierst direkt als Router und Worker (siehe `use-orchestrator.md`)."
        )

    if include_table:
        if has_orchestrator:
            lines.append("")
        lines.append("| Agent | Zuständigkeit |")
        lines.append("|-------|--------------|")
        for role, source_path in sorted(overrides.items()):
            if allowed_roles is not None and role not in allowed_roles:
                continue
            if not _is_role_enabled(role, config):
                continue
            if not target_filename(role, role_map):
                continue
            content = source_path.read_text(encoding="utf-8")
            hint = extract_frontmatter_field(content, "hint") \
                or extract_frontmatter_field(content, "description") \
                or ""
            lines.append(f"| `{role}` | {hint} |")

    # Knowledge Engine hints (only when enabled). Emitted regardless of
    # include_table — this section is not a per-agent table duplication, it's
    # entry-point orientation that every provider (including Claude, which
    # gets AGENT_HINTS_CLAUDE with include_table=False) needs to see.
    ke_hints = build_knowledge_engine_hints(config)
    if ke_hints:
        lines.append("")
        lines.append(ke_hints)

    return "\n".join(lines)


def build_agent_table(config: dict, agent_meta_root: Path) -> tuple[str, list[str]]:
    """Generate markdown table for {{AGENT_TABLE}}. Returns (table, unmapped_warnings).

    Only includes roles present in config['roles'] whitelist (if set).
    """
    from .roles import build_role_map

    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    role_map = build_role_map(agent_meta_root)
    allowed_roles: set[str] | None = None
    if "roles" in config:
        allowed_roles = set(config["roles"])

    rows = []
    unmapped = []
    for role, source_path in sorted(overrides.items()):
        if allowed_roles is not None and role not in allowed_roles:
            continue
        if not _is_role_enabled(role, config):
            continue
        filename = target_filename(role, role_map)
        if not filename:
            unmapped.append(
                f"Role '{role}' ({source_path.name}) not in ROLE_MAP — skipped in AGENT_TABLE"
            )
            continue
        agent_name = Path(filename).stem
        layer = source_path.parts[-2]
        rows.append(f"| `{agent_name}` | `{source_path.name}` | {layer} |")

    header = "| Agent | Quelle | Layer |\n|-------|--------|-------|"
    return header + "\n" + "\n".join(rows), unmapped
