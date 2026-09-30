"""Gate for block inlining: the re-indentation contract plus a render-level
check of ``2-platform`` overrides.

Why this module exists
----------------------
``tests/test_template_slimming_equivalence.py`` guards the *source-level*
migration (no inline block text left, canonical block present). It has two blind
spots for ``agents/2-platform/`` overrides, both addressed here:

1. Its comparison normalizes with ``_dedent()`` and ``_parse_input_regions()``
   skips blank lines between a heading and its sentence, so neither the exact
   post-render indentation nor the paragraph structure of an inlined block is
   ever asserted.
2. Its ``render_env`` fixture renders only the platforms of this repo's
   ``.meta-config/project.yaml`` (``agent-meta``), so the ``sharkord`` and
   ``homeassistant`` overrides — which carry their block reference inside a
   YAML literal ``patches: … content: |`` block — are never rendered at all.

This module has two test groups, and they prove different things:

*Unit level* — pins the re-indentation contract of ``substitute()`` itself.
These are the tests that **verify the transform**: they fail without
``_reindent_to_placeholder`` and pass with it.

*Render level* — renders a real 2-platform override through the production
pipeline (``_resolve_sync_targets`` → ``_compose_role_content`` →
``_apply_content_pipeline`` → ``_finalize_agent_content``) and asserts the
*exact* rendered bytes of the inlined block region. No ``_dedent``, no
normalization. These tests are **no-op guards**: they are green with *and*
without the transform, because the canonical block reaches the body at column
0. Their value is proving that the transform changes nothing in production,
not that it does something.

Indentation contract (scripts/lib/variables.py, ``_reindent_to_placeholder``):
a multi-line value is emitted with every content line carrying the indentation
of the line its placeholder sits on; blank lines stay blank (no whitespace-only
lines). Column-0 and single-line placeholders are unchanged, which is what
keeps the ``1-generic`` corpus byte-identical.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts.lib.agent_sync import (
    _apply_content_pipeline,
    _build_provider_vars,
    _compose_role_content,
    _finalize_agent_content,
    _resolve_sync_targets,
    _should_skip_role,
)
from scripts.lib.config import build_variables, load_config, load_providers_config
from scripts.lib.log import SyncLog
from scripts.lib.roles import resolve_activation_gates
from scripts.lib.variables import substitute

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PROVIDER = "Claude"

# 2-platform overrides that reference {{PARSE_INPUT_BLOCK}} from inside a
# 6-space YAML literal `content: |` patch block. Each override renames a role
# whose name collides across platforms, so one platform is rendered per case.
_PARSE_INPUT_OVERRIDES = {
    "sharkord": "agents/2-platform/sharkord-developer.md",
    "homeassistant": "agents/2-platform/homeassistant-developer.md",
    "agent-meta": "agents/2-platform/agent-meta-developer.md",
}
_DOCUMENTER_OVERRIDE = "agents/2-platform/homeassistant-documenter.md"


@dataclass(frozen=True)
class Rendered:
    role: str
    content: str
    canonical: str


@pytest.fixture(scope="module")
def target_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Render target root — never inside the repository."""
    return tmp_path_factory.mktemp("block-inlining-target")


def _render_platform_override(rel_path: str, platform: str, target_root: Path) -> Rendered:
    """Render one 2-platform override exactly the way sync.py renders a role."""
    log = SyncLog()
    config = load_config(_REPO_ROOT / ".meta-config" / "project.yaml")
    # Force the platform under test — sharkord/homeassistant are not this
    # repo's active platforms, which is precisely why the slimming fixture
    # never renders them.
    config["platforms"] = [platform]
    variables, _warnings = build_variables(config, _REPO_ROOT, target_root)
    provider_config = load_providers_config(_REPO_ROOT)
    pc, role_map, overrides, target_dir = _resolve_sync_targets(
        _PROVIDER, provider_config, _REPO_ROOT, target_root, config, True, log
    )
    assert pc is not None, "provider config missing"
    gates = resolve_activation_gates(_REPO_ROOT, config)
    allowed_roles = set(config["roles"]) if "roles" in config else None
    project_name = config.get("project", {}).get("name", "unknown")

    rendered: dict[str, Rendered] = {}
    for role, source_path in sorted(overrides.items()):
        if source_path != _REPO_ROOT / rel_path:
            continue
        skip, filename = _should_skip_role(
            role, source_path, _PROVIDER, pc, role_map, allowed_roles, config,
            variables, target_root, target_dir, log, gates=gates,
        )
        assert not skip, f"{rel_path}: role unexpectedly skipped"
        target_path = target_dir / filename
        content, can_spawn, rel_source, source_version, description = (
            _compose_role_content(
                source_path, _PROVIDER, project_name, _REPO_ROOT, target_root,
                target_path, log, pc=pc,
            )
        )
        merged = _build_provider_vars(
            pc, _PROVIDER, variables, _REPO_ROOT, config=config
        )
        content = _apply_content_pipeline(
            content, config, _PROVIDER, merged, rel_source, None, _REPO_ROOT, log
        )
        content = _finalize_agent_content(
            content, role, filename, source_path, _PROVIDER, provider_config,
            source_version, description, can_spawn, config, _REPO_ROOT, target_root,
            target_path, variables, False, log,
        )
        rendered[role] = Rendered(role, content, variables["PARSE_INPUT_BLOCK"])
    assert rendered, f"{rel_path}: override did not render under platform {platform!r}"
    return next(iter(rendered.values()))


def _workflow_lines(content: str) -> list[str]:
    """Lines of the rendered ``<workflow>`` section, verbatim (no dedent)."""
    match = re.search(r"^<workflow>$(.*?)^</workflow>$", content, re.M | re.S)
    assert match, "rendered agent has no <workflow> section"
    return match.group(1).split("\n")


# ---------------------------------------------------------------------------
# Unit level — the re-indentation contract of substitute()
# ---------------------------------------------------------------------------

def test_multiline_value_is_reindented_to_the_placeholder_indent():
    log = SyncLog()
    text = "content: |\n      {{BLK}}\n      tail\n"
    out = substitute(text, {"BLK": "head\nsecond\nthird"}, "t.md", log)
    assert out == (
        "content: |\n"
        "      head\n"
        "      second\n"
        "      third\n"
        "      tail\n"
    )


def test_column_zero_placeholder_is_untouched():
    log = SyncLog()
    text = "<workflow>\n{{BLK}}\n\n2. next\n"
    out = substitute(text, {"BLK": "head\nsecond"}, "t.md", log)
    assert out == "<workflow>\nhead\nsecond\n\n2. next\n"


def test_single_line_value_at_indent_is_untouched():
    log = SyncLog()
    out = substitute("      {{BLK}}\n", {"BLK": "one line"}, "t.md", log)
    assert out == "      one line\n"


def test_inline_placeholder_in_a_sentence_is_untouched():
    """Only a placeholder that starts its own line has a line indentation."""
    log = SyncLog()
    out = substitute("prefix {{BLK}} suffix\n", {"BLK": "head\nsecond"}, "t.md", log)
    assert out == "prefix head\nsecond suffix\n"


def test_reindenting_keeps_the_yaml_literal_block_parseable():
    yaml = pytest.importorskip("yaml")

    log = SyncLog()
    template = "patches:\n  - op: replace\n    content: |\n      {{BLK}}\n"
    rendered = substitute(
        template, {"BLK": "## 1. Parse input\nA2A envelope present."}, "t.md", log
    )
    parsed = yaml.safe_load(rendered)
    # Without the re-indent the second line lands on column 0 and the literal
    # block ends there — the A2A sentence would leak out of `content:`.
    assert parsed["patches"][0]["content"].strip("\n") == (
        "## 1. Parse input\nA2A envelope present."
    )


def test_reindenting_does_not_indent_blank_lines():
    """Regression: indenting blank lines emits whitespace-only lines.

    Block snippets are immune (``strip("\\n")`` in the inlining transform), but
    project variables from a YAML literal are not — a value with an inner blank
    line or a trailing newline would render trailing whitespace and trip
    ``git diff --check`` / trailing-whitespace hooks in consumer projects.
    """
    log = SyncLog()

    out = substitute(
        "content: |\n      {{BLK}}\n      tail\n",
        {"BLK": "head\n\nsecond\n"},
        "t.md",
        log,
    )
    assert out == "content: |\n      head\n\n      second\n\n      tail\n"
    assert not [ln for ln in out.split("\n") if ln and not ln.strip()]

    out = substitute(
        "      {{BLK}}\n", {"BLK": "head\n"}, "t.md", log
    )
    assert out == "      head\n\n"
    assert not [ln for ln in out.split("\n") if ln and not ln.strip()]


# ---------------------------------------------------------------------------
# Render level — real 2-platform overrides, exact bytes.
# No-op guards: green with and without the transform (see module docstring).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("platform,rel_path", sorted(_PARSE_INPUT_OVERRIDES.items()))
def test_platform_override_renders_block_at_column_zero(
    platform, rel_path, target_root
):
    """The YAML patch literal is YAML-parsed before substitution, so the
    inlined block must land in the body at column 0 — heading and sentence
    both, with exactly one blank line before the numbered continuation."""
    rendered = _render_platform_override(rel_path, platform, target_root)
    lines = _workflow_lines(rendered.content)

    start = lines.index(rendered.canonical.split("\n")[0])
    block = lines[start:start + len(rendered.canonical.split("\n"))]
    assert block == rendered.canonical.split("\n"), (
        f"{rel_path}: inlined block not rendered at column 0:\n{block!r}"
    )
    # paragraph structure: one blank line after the block, then the numbering
    assert lines[start + len(block)] == ""
    assert lines[start + len(block) + 1].startswith("2. "), (
        f"{rel_path}: expected the numbered workflow to resume after the block, "
        f"got {lines[start + len(block) + 1]!r}"
    )
    # the placeholder is fully resolved
    assert "{{PARSE_INPUT_BLOCK}}" not in rendered.content
    assert "## 1. Parse input" in rendered.content


def test_homeassistant_documenter_override_renders_same_block_structure(target_root):
    """homeassistant-documenter.md carried a blank line between the heading and
    the A2A sentence before the slimming. The canonical snippet does not, so the
    post-migration output drops it. That is a *whitespace* normalization only —
    an ATX heading followed directly by a paragraph is valid GFM and renders
    identically — and it is the same structure the other ~50 roles now render.
    Pinned here so the structure is an asserted contract, not an accident.
    """
    rendered = _render_platform_override(
        _DOCUMENTER_OVERRIDE, "homeassistant", target_root
    )
    lines = _workflow_lines(rendered.content)
    start = lines.index("## 1. Parse input")
    assert lines[start + 1] == rendered.canonical.split("\n")[1]
    assert "A2A envelope present" in lines[start + 1]
    assert lines[start + 2] == ""
    assert lines[start + 3].startswith("## 2."), (
        f"expected the documenter workflow to resume, got {lines[start + 3]!r}"
    )


def test_source_templates_reference_the_block_inside_a_yaml_literal():
    """Guards the premise of the tests above: the placeholder really does sit at
    6 spaces inside a `content: |` patch block, not at column 0 of the body."""
    for rel_path in (*_PARSE_INPUT_OVERRIDES.values(), _DOCUMENTER_OVERRIDE):
        text = (_REPO_ROOT / rel_path).read_text(encoding="utf-8")
        lines = [
            ln for ln in text.split("\n") if "{{PARSE_INPUT_BLOCK}}" in ln
        ]
        assert lines, f"{rel_path}: no {{{{PARSE_INPUT_BLOCK}}}} reference"
        for line in lines:
            indent = len(line) - len(line.lstrip(" "))
            assert indent == 6, f"{rel_path}: expected 6-space YAML literal indent"
