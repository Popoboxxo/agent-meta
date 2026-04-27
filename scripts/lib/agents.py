"""Agent file generation: frontmatter, composition, sync logic."""

import re
from pathlib import Path

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


def extract_frontmatter_field(content: str, field: str) -> str | None:
    """Extract a single-line YAML frontmatter field value (unquoted or quoted)."""
    match = re.search(
        rf'^{re.escape(field)}:\s*"?([^"\n]+)"?\s*$',
        content, flags=re.MULTILINE,
    )
    return match.group(1).strip() if match else None


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


# ---------------------------------------------------------------------------
# Composition engine (extends: / patches: system)
# ---------------------------------------------------------------------------

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
    except Exception:
        return {}


def _find_section_bounds(lines: list[str], anchor: str) -> tuple[int, int] | None:
    """Find (start, end) line indices for a Markdown section.

    anchor must match the heading line exactly (e.g. '## Don\\'ts').
    start is inclusive (the heading line).
    end is exclusive (first line of next section at same or higher level, or len(lines)).
    """
    anchor_stripped = anchor.strip()
    anchor_level = len(anchor_stripped) - len(anchor_stripped.lstrip("#"))

    start_idx = None
    for i, line in enumerate(lines):
        if line.rstrip() == anchor_stripped:
            start_idx = i
            break

    if start_idx is None:
        return None

    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level <= anchor_level:
                return (start_idx, i)

    return (start_idx, len(lines))


def _patch_append_after(content: str, anchor: str, patch_content: str,
                        log: SyncLog, source_label: str) -> str:
    """Insert patch_content after the section identified by anchor."""
    lines = content.splitlines(keepends=True)
    bounds = _find_section_bounds(lines, anchor)
    if bounds is None:
        log.warn(f"Composition patch 'append-after': anchor '{anchor}' not found in {source_label}")
        return content
    _, end_idx = bounds
    patch_lines = ("\n\n" + patch_content.rstrip("\n") + "\n\n").splitlines(keepends=True)
    result_lines = lines[:end_idx] + patch_lines + lines[end_idx:]
    return "".join(result_lines)


def _patch_replace(content: str, anchor: str, patch_content: str,
                   log: SyncLog, source_label: str) -> str:
    """Replace the entire section identified by anchor with patch_content."""
    lines = content.splitlines(keepends=True)
    bounds = _find_section_bounds(lines, anchor)
    if bounds is None:
        log.warn(f"Composition patch 'replace': anchor '{anchor}' not found in {source_label}")
        return content
    start_idx, end_idx = bounds
    patch_lines = (patch_content.rstrip("\n") + "\n").splitlines(keepends=True)
    result_lines = lines[:start_idx] + patch_lines + lines[end_idx:]
    return "".join(result_lines)


def _patch_delete(content: str, anchor: str, log: SyncLog, source_label: str) -> str:
    """Delete the entire section identified by anchor."""
    lines = content.splitlines(keepends=True)
    bounds = _find_section_bounds(lines, anchor)
    if bounds is None:
        log.warn(f"Composition patch 'delete': anchor '{anchor}' not found in {source_label}")
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
        return content.rstrip("\n") + "\n\n" + patch_content.rstrip("\n") + "\n"
    elif op == "append-after":
        return _patch_append_after(content, anchor, patch_content, log, source_label)
    elif op == "replace":
        return _patch_replace(content, anchor, patch_content, log, source_label)
    elif op == "delete":
        return _patch_delete(content, anchor, log, source_label)
    else:
        log.warn(f"Composition: unknown patch op '{op}' in {source_label}")
        return content


def _merge_frontmatter(base_content: str, override_fm: dict) -> str:
    """Replace the frontmatter block in base_content with values from override_fm.

    Fields 'extends' and 'patches' are stripped (composition metadata).
    All other override fields (name, version, description, hint, tools, based-on) win.
    """
    fm_block, body = _split_frontmatter(base_content)
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
    except Exception:
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
        log.warn(
            "PyYAML not available — composition skipped. "
            "Install it with: pip install pyyaml"
        )
        return override_content

    if not base_path.exists():
        log.warn(f"Composition: base template not found: {base_path}")
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
    agent_meta_root: Path, platforms: list[str]
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
            overrides[f.stem] = f

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

    return overrides, known_ext_roles


def sync_agents(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Generate all .claude/agents/*.md files (legacy Claude-only path)."""
    from .config import substitute, strip_inactive_dod_blocks
    from .roles import build_role_map, resolve_model, resolve_memory, resolve_permission_mode
    from .skills import load_external_skills_config, _skill_is_active

    CLAUDE_AGENTS_DIR = ".claude/agents"
    role_map = build_role_map(agent_meta_root)
    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    target_dir = project_root / CLAUDE_AGENTS_DIR

    # Optional role whitelist — if "roles" key is absent, all roles are generated
    allowed_roles: set[str] | None = None
    if "roles" in config:
        allowed_roles = set(config["roles"])

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    # Track which filenames will be written in this sync
    expected_filenames: set[str] = set()

    project_name = config["project"]["name"]
    for role, source_path in overrides.items():
        filename = target_filename(role, role_map)
        if not filename:
            log.skip(str(source_path.name), "role not in ROLE_MAP")
            continue

        if allowed_roles is not None and role not in allowed_roles:
            log.skip(str(target_dir / filename).replace(str(project_root) + "/", "").replace(str(project_root) + "\\", ""),
                     f"role '{role}' not in config['roles']")
            continue

        expected_filenames.add(filename)
        target_path = target_dir / filename
        content = source_path.read_text(encoding="utf-8")

        # Composition mode: if 'extends:' present in frontmatter, compose from base
        extends_base = extract_frontmatter_field(content, "extends")
        if extends_base:
            base_path = agent_meta_root / AGENTS_DIR / extends_base
            content = compose_agent(base_path, content, log)
            log.info(
                str(target_path.relative_to(project_root)),
                f"composed from {extends_base} + {source_path.name}",
            )

        rel_source = str(source_path.relative_to(agent_meta_root))
        source_version = extract_frontmatter_field(content, "version")
        template_description = extract_frontmatter_field(content, "description")
        description = (template_description or f"Agent for {project_name}.")
        description = description.replace("{{PROJECT_NAME}}", project_name)
        content = substitute(content, variables, rel_source, log)
        content = strip_inactive_dod_blocks(content, variables)
        name = Path(filename).stem
        layer = source_path.parts[-2]
        source_label = f"{layer}/{source_path.name}"
        generated_from = f"{source_label}@{source_version}" if source_version else source_label
        content = build_frontmatter(content, name, description,
                                    generated_from=generated_from)

        model = resolve_model(role, config, agent_meta_root)
        content = inject_model_field(content, model)
        if model:
            model_src = "project override" if role in config.get("model-overrides", {}) else "meta default"
            log.info(str(target_path.relative_to(project_root)), f"model: {model} (from {model_src})")

        memory = resolve_memory(role, config, agent_meta_root)
        content = inject_memory_field(content, memory)
        if memory:
            memory_src = "project override" if role in config.get("memory-overrides", {}) else "meta default"
            log.info(str(target_path.relative_to(project_root)), f"memory: {memory} (from {memory_src})")

        permission_mode = resolve_permission_mode(role, config, agent_meta_root)
        content = inject_permission_mode_field(content, permission_mode)
        if permission_mode:
            pm_src = "project override" if role in config.get("permission-mode-overrides", {}) else "meta default"
            log.info(str(target_path.relative_to(project_root)), f"permissionMode: {permission_mode} (from {pm_src})")

        rel_label = str(source_path.relative_to(agent_meta_root / AGENTS_DIR))
        log.action("WRITE", str(target_path.relative_to(project_root)), rel_label)
        if not dry_run:
            target_path.write_text(content, encoding="utf-8")

    # Also track external skill agent filenames (they are not in overrides)
    ext_config = load_external_skills_config(agent_meta_root)
    project_skills = config.get("external-skills", {})
    for skill_name, skill_cfg in ext_config.get("skills", {}).items():
        if _skill_is_active(skill_name, skill_cfg, project_skills):
            role = skill_cfg.get("role", skill_name)
            expected_filenames.add(f"{role}.md")

    # Remove stale agent files that are no longer in the active role set
    if target_dir.exists():
        for existing_file in sorted(target_dir.glob("*.md")):
            if existing_file.name not in expected_filenames:
                log.action("DELETE", str(existing_file.relative_to(project_root)),
                           "role removed from config")
                if not dry_run:
                    existing_file.unlink()


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
    from .config import substitute, strip_inactive_dod_blocks
    from .platform import substitute_platform
    from .roles import build_role_map, resolve_model, resolve_memory, resolve_permission_mode
    from .skills import load_external_skills_config, _skill_is_active

    pc = provider_config.get(provider)
    if not pc:
        log.warn(f"Unknown provider '{provider}' — skipping agent sync")
        return

    role_map = build_role_map(agent_meta_root)
    platforms = config.get('platforms', [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    target_dir = project_root / pc['agents_dir']

    allowed_roles = set(config['roles']) if 'roles' in config else None

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    expected_filenames: set = set()
    project_name = config['project']['name']

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

        expected_filenames.add(filename)
        target_path = target_dir / filename
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

        rel_source = str(source_path.relative_to(agent_meta_root))
        source_version = extract_frontmatter_field(content, 'version')
        template_description = extract_frontmatter_field(content, 'description')
        description = (template_description or f'Agent for {project_name}.')
        description = description.replace('{{PROJECT_NAME}}', project_name)
        content = substitute(content, variables, rel_source, log)
        content = strip_inactive_dod_blocks(content, variables)
        # Apply platform-config substitution ({{platform.*}} placeholders)
        if platform_vars is not None:
            content = substitute_platform(content, platform_vars, rel_source, log)
        name = Path(filename).stem
        layer = source_path.parts[-2]
        source_label = f'{layer}/{source_path.name}'
        generated_from = f'{source_label}@{source_version}' if source_version else source_label

        if provider == 'Continue':
            # Continue agents: minimal frontmatter (name + description only)
            # alwaysApply: false — agent is invoked by name, not auto-loaded
            fm = f"---\nname: {name}\ndescription: \"{description}\"\nalwaysApply: false\n---\n"
            body = _strip_frontmatter(content)
            body = _strip_claude_specific_lines(body)
            content = fm + body
        else:
            content = build_frontmatter(content, name, description, generated_from=generated_from)

            if provider == 'Claude':
                model = resolve_model(role, config, agent_meta_root,
                                      provider=provider, provider_config=provider_config)
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

            elif provider == 'Gemini':
                # Gemini: provider-mapped model only; strip memory, permissionMode, Claude-specific lines
                model = resolve_model(role, config, agent_meta_root,
                                      provider=provider, provider_config=provider_config)
                content = inject_model_field(content, model)
                if model:
                    po = config.get('model-overrides', {})
                    is_override = role in po.get('Gemini', {})
                    src = 'project override' if is_override else 'meta default'
                    log.info(str(target_path.relative_to(project_root)), f'model: {model} (from {src})')
                content = _remove_frontmatter_fields(content, ['memory', 'permissionMode'])
                body = _strip_frontmatter(content)
                body = _strip_claude_specific_lines(body)
                fm_end = content.find('\n---', 3)
                if fm_end != -1:
                    content = content[:fm_end + 4] + '\n' + body.lstrip('\n')

        if debug_mode:
            content = inject_debug_block(content, name)

        rel_label = str(source_path.relative_to(agent_meta_root / AGENTS_DIR))
        log.action('WRITE', str(target_path.relative_to(project_root)), rel_label)
        if not dry_run:
            target_path.write_text(content, encoding='utf-8')

    # External skill filenames are always in .claude/agents/ (Claude only)
    if provider == 'Claude':
        ext_config = load_external_skills_config(agent_meta_root)
        project_skills = config.get('external-skills', {})
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
            if existing_file.name not in expected_filenames:
                if not managed_index.exists() or existing_file.name in previously_managed:
                    log.action('DELETE', str(existing_file.relative_to(project_root)),
                               'role removed from config')
                    if not dry_run:
                        existing_file.unlink()

        if not dry_run and expected_filenames:
            managed_index.write_text(
                '\n'.join(sorted(expected_filenames)) + '\n', encoding='utf-8'
            )


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
    keep_sections = {
        "## Don'ts",
        "## Donts",
        "## Don",
        "## Kernregeln",
        "## Aktive DoD",
        "## DoD",
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


def build_agent_hints(config: dict, agent_meta_root: Path) -> str:
    """Generate agent usage hints for {{AGENT_HINTS}}.

    Reads hint (preferred) or description from each active agent's template frontmatter.
    If orchestrator is active, adds a prominent start hint.
    """
    from .roles import build_role_map

    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    role_map = build_role_map(agent_meta_root)
    allowed_roles: set[str] | None = None
    if "roles" in config:
        allowed_roles = set(config["roles"])

    lines = []
    has_orchestrator = (
        "orchestrator" in overrides
        and (allowed_roles is None or "orchestrator" in allowed_roles)
    )
    if has_orchestrator:
        lines.append(
            "> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben."
        )
        lines.append("")

    lines.append("| Agent | Zuständigkeit |")
    lines.append("|-------|--------------|")
    for role, source_path in sorted(overrides.items()):
        if allowed_roles is not None and role not in allowed_roles:
            continue
        if not target_filename(role, role_map):
            continue
        content = source_path.read_text(encoding="utf-8")
        hint = extract_frontmatter_field(content, "hint") \
            or extract_frontmatter_field(content, "description") \
            or ""
        lines.append(f"| `{role}` | {hint} |")

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
