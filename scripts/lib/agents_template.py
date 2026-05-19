"""Template composition, source collection and filename utilities."""

import re
from pathlib import Path

from .log import SyncLog
from .io import safe_path, _yaml, _YAML_AVAILABLE

AGENTS_DIR = "agents"
GENERIC_DIR = "1-generic"
PLATFORM_DIR = "2-platform"
PROJECT_DIR = "3-project"
EXTERNAL_DIR = "0-external"
SKILL_WRAPPER = "_skill-wrapper.md"
EXT_SUFFIX = "-ext"


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
    except _yaml.YAMLError:
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
