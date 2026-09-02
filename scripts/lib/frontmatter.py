"""Frontmatter parsing, field injection, and agent-source discovery.

Neutral, cycle-free bottom layer of the agent pipeline (Issue #561 split of the
former agents.py). Contains only pure YAML-frontmatter parsing/manipulation, the
agent-directory layer constants, and filesystem discovery of agent source files
(collect_sources). Depends solely on the stdlib + optional PyYAML — it must
never import config/agents/provider_transform/agent_sync/mcp/rules/skills/viz,
which is what keeps the scripts/lib dependency graph acyclic (Issue #565).
"""
from __future__ import annotations

import re
from pathlib import Path

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

def _insert_after_frontmatter(content: str, comment: str) -> str:
    """Insert `comment` as the first line of the body, right after the
    closing frontmatter '---'. No-op (returns content unchanged) if no
    frontmatter block is found."""
    fm_block, body = _split_frontmatter(content)
    if not fm_block:
        return content
    return f"{fm_block}\n{comment}{body}"

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
                      generated_from: str | None = None,
                      strip_fields: list[str] | None = None) -> str:
    """Replace name and description in YAML frontmatter.

    Preserves existing version/based-on fields.
    Emits generated-from field for template traceability.

    strip_fields: frontmatter keys to omit for providers with strict schema
    validation that reject fields outside their own agent-definition schema
    (issue #505 — e.g. a strict validation layer in front of an Opencode-
    shaped agent format rejecting agent-meta's own `version`/`prompt_mode`/
    `generated-from` bookkeeping fields). Their pre-strip values (including
    the `generated_from` this call would otherwise have written) are
    preserved in an `agent-meta-provenance` HTML comment right after the
    frontmatter, so traceability and version-bump enforcement (Hard
    Invariant #2) survive the strip. A field absent from the source is
    silently skipped, not fabricated into the comment.
    """
    provenance_comment = None
    if strip_fields:
        existing_fm = _parse_frontmatter_yaml(content)
        preserved = {k: existing_fm[k] for k in strip_fields if k in existing_fm}
        if generated_from and "generated-from" in strip_fields:
            preserved["generated-from"] = generated_from
        if preserved:
            pairs = " ".join(f"{k}={v}" for k, v in preserved.items())
            provenance_comment = f"<!-- agent-meta-provenance: {pairs} -->"

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
        if strip_fields:
            removes.extend(strip_fields)
        result = _update_frontmatter_dict(
            content,
            updates=updates,
            removes=removes,
        )
        if provenance_comment:
            result = _insert_after_frontmatter(result, provenance_comment)
        return result

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

def parse_frontmatter_file(path: Path) -> dict:
    """Parse the YAML frontmatter block of a Markdown file directly from disk.

    Canonical file-reading wrapper around `_parse_frontmatter_yaml` (Issue #571)
    for callers that only have a `Path`, not already-loaded content (e.g.
    config_audit.py's template inspection). Returns `{}` on any I/O error,
    missing frontmatter, or YAML parse failure/unavailability — mirrors
    `_parse_frontmatter_yaml`'s fail-soft contract so callers never need their
    own try/except around this call.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    return _parse_frontmatter_yaml(text)

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
