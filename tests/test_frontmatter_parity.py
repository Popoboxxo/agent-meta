"""Parity-golden tests: canonical frontmatter API vs. the former duplicates (#473).

The canonical public API in ``lib.frontmatter`` (``split_frontmatter``,
``parse_frontmatter_text``, ``strip_frontmatter``) replaced four independently
written frontmatter parsers:

1. ``lib.pipelines.parse_plan_ref``    — inline regex ``^---\\s*\\n(.*?)\\n---`` + inline yaml
2. ``lib.context_templates.builder``   — ``content.split('---', 2)`` (×2 sites)
3. ``lib.consistency.frontmatter``     — own two-regex boundary + strict None-on-malformed
4. ``lib.consistency.crossrefs``       — ``content.split('---', 2)`` + fail-soft {}

The old implementations are frozen below as reference functions so the parity
holds even after the originals were deleted (strangler migration). Fixtures in
``EQUIVALENT_FIXTURES`` are inputs every real template satisfies (newline fence
convention); ``KNOWN_DELTAS`` documents the deliberately accepted semantic
differences on pathological inputs (see module docstring of lib.frontmatter
and the migration notes in #473).
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import yaml  # noqa: E402  (test env always has PyYAML; parity for the no-yaml path is n/a here)

from lib.frontmatter import (  # noqa: E402
    parse_frontmatter_text,
    split_frontmatter,
    strip_frontmatter,
)


# --- frozen reference implementations (the former duplicates) ----------------

def old_pipelines_plan_ref_fm(content: str):
    """Old pipelines.parse_plan_ref boundary: regex + safe_load, fail-soft {}."""
    m = __import__("re").match(r'^---\s*\n(.*?)\n---', content, __import__("re").DOTALL)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def old_builder_strip(content: str) -> str:
    """Old builder.py strip: split('---', 2) + parts[2].lstrip()."""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            return parts[2].lstrip()
    return content


def old_crossrefs_parse(content: str) -> dict:
    """Old consistency/crossrefs.py parse: split('---', 2), fail-soft {}."""
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except Exception:  # noqa: BLE001
        return {}


def old_consistency_frontmatter_parse(content: str):
    """Old consistency/frontmatter.py parse: strict dict|None semantics."""
    match = __import__("re").match(r'^---\s*\n(.*?)\n---\s*$', content, __import__("re").DOTALL)
    if not match:
        match = __import__("re").match(r'^---\s*\n(.*?)\n---\s*\n', content, __import__("re").DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return None


def old_commands_extract(content: str):
    """Old consistency/commands.py raw extractor: inline regex, inner text or None."""
    match = __import__("re").match(r'^---\s*\n(.*?)\n---', content, __import__("re").DOTALL)
    return match.group(1) if match else None


def old_commands_parse(raw: str) -> dict:
    """Old consistency/commands.py parse: safe_load or {}, line fallback on
    any failure (incl. JSON-array values)."""
    try:
        return yaml.safe_load(raw) or {}
    except Exception:  # noqa: BLE001
        result = {}
        for line in raw.splitlines():
            m = __import__("re").match(r'^([\w-]+):\s*(.*)$', line)
            if m:
                key, val = m.group(1), m.group(2).strip()
                if val.startswith("["):
                    try:
                        import json
                        result[key] = __import__("json").loads(val)
                        continue
                    except Exception:  # noqa: BLE001
                        pass
                result[key] = val.strip('"').strip("'")
        return result


# --- fixtures ----------------------------------------------------------------

VALID_FM = "---\nname: developer\nversion: 1.0.0\ntools:\n  - Bash\n---\n# Body\n"
EQUIVALENT_FIXTURES = {
    "valid_fm": VALID_FM,
    "valid_fm_no_body": "---\nname: x\n---",
    "valid_fm_trailing_newline_eof": "---\nname: x\n---\n",
    "valid_fm_space_after_opening_fence": "--- \nname: x\n---\nbody",
    "no_frontmatter": "plain body\nno fences here\n",
    "unclosed_fm": "---\nname: x\nno closing fence",
    "empty_fm_block": "---\n---\nbody\n",
    "empty_fm_block_eof": "---\n---",
    "fm_at_eof_without_newline": "---\nname: x\n---",
    "dashes_inside_body": "---\nname: x\n---\n--- not a fence\nbody\n",
    "malformed_yaml": "---\nname: [unclosed\n---\nBody\n",
    "blank_fm_whitespace": "---\n\n---\nbody\n",
    "crlf_fences": "---\r\nname: x\r\n---\r\nbody",
}


# --- equivalence: parse_frontmatter_text vs. old parsers ---------------------

def test_parity_parse_frontmatter_text_vs_pipelines_regex():
    for label, content in EQUIVALENT_FIXTURES.items():
        assert parse_frontmatter_text(content) == old_pipelines_plan_ref_fm(content), label


def test_parity_parse_frontmatter_text_vs_crossrefs_split():
    for label, content in EQUIVALENT_FIXTURES.items():
        assert parse_frontmatter_text(content) == old_crossrefs_parse(content), label


def test_parity_split_block_boundaries():
    """fm_block from split_frontmatter must yield the same inner YAML the old
    regexes extracted, for every fixture."""
    import re
    for label, content in EQUIVALENT_FIXTURES.items():
        fm_block, _body = split_frontmatter(content)
        old = old_pipelines_plan_ref_fm(content)
        if not fm_block:
            assert old == {}, label
            continue
        inner = re.sub(r"^---\n?", "", fm_block)
        inner = re.sub(r"\n?---\s*$", "", inner)
        try:
            parsed = yaml.safe_load(inner)
        except yaml.YAMLError:
            parsed = None
        parsed = parsed if isinstance(parsed, dict) else {}
        assert parsed == old, label


def test_parity_consistency_strict_parse():
    """Strict parity: absent/malformed → None, present → dict (same as old)."""
    from lib.consistency.frontmatter import _parse_frontmatter
    strict = {**EQUIVALENT_FIXTURES}
    for label, content in strict.items():
        assert _parse_frontmatter(content) == old_consistency_frontmatter_parse(content), label


# --- equivalence: strip_frontmatter vs. old builder strip --------------------

def test_parity_strip_frontmatter_vs_builder_split():
    for label, content in EQUIVALENT_FIXTURES.items():
        if label == "crlf_fences":
            continue  # documented delta: see test_delta_strip_keeps_crlf_carriage_returns
        assert strip_frontmatter(content) == old_builder_strip(content), label


# --- parity: commands.py raw extraction + line-fallback parse (Issue #473) ---

def test_parity_commands_extract():
    """The commands checker's raw extractor must preserve the old inline-
    regex *behavior*: None exactly when the old regex found no block, and a
    raw inner text that PARSES identically (the raw string may keep leading
    whitespace the old regex's ``\\s*`` consumed — semantically irrelevant,
    see the exceptions below)."""
    from lib.consistency.commands import _parse_frontmatter, _extract_frontmatter_raw
    # fixtures where the old regex's `\s*` ate whitespace between the fence
    # and its terminating newline — raw strings differ, parsed dicts don't:
    raw_insensitive = {"valid_fm_space_after_opening_fence", "crlf_fences"}
    for label, content in EQUIVALENT_FIXTURES.items():
        old_raw = old_commands_extract(content)
        new_raw = _extract_frontmatter_raw(content)
        assert (old_raw is None) == (new_raw is None), label
        if old_raw is None:
            continue
        if label not in raw_insensitive:
            assert new_raw == old_raw, label
        assert _parse_frontmatter(new_raw) == old_commands_parse(old_raw), label


def test_parity_commands_parse_valid_and_line_fallback():
    """Valid YAML parses identically; malformed YAML falls back to the line
    parser in BOTH implementations (old behavior preserved — not swallowed
    to {} like parse_frontmatter_text)."""
    from lib.consistency.commands import _parse_frontmatter

    assert _parse_frontmatter("description: Deploy main\n") == {"description": "Deploy main"}
    assert _parse_frontmatter("") == {}

    malformed = 'description: [unclosed\nallowed-tools: ["Bash", "Read"]\n'
    old = old_commands_parse(malformed)
    new = _parse_frontmatter(malformed)
    assert new == old
    assert new["allowed-tools"] == ["Bash", "Read"]  # JSON array survives the fallback
    assert new["description"] == "[unclosed"  # non-JSON scalar kept as string


# --- documented deltas (deliberately accepted, pathological inputs only) -----

def test_delta_builder_no_newline_fence():
    """builder's split accepted '---x---' without any newline; the canonical
    core requires '\\n---'. No agent-meta template uses the no-newline form —
    documented accepted delta (analysis §6a, Semantik-Delta)."""
    content = "---x---\nbody"
    assert old_builder_strip(content) == "body"
    assert strip_frontmatter(content) == content  # unchanged (no closing fence found)


def test_delta_split_lenient_opening_fence():
    """Mirror image: canonical splitter accepts any '---'-suffixed opening
    fence, the old pipelines regex required '\\s*\\n' right after '---'.
    Real templates always use a bare '---\\n' opening fence."""
    content = "---x\nfm\n---\nbody"
    assert old_pipelines_plan_ref_fm(content) == {}
    assert parse_frontmatter_text(content) == {}  # lenient split → 'x\\nfm' is a scalar → {}


def test_delta_split_parses_fence_suffixed_yaml():
    """Explicit old != new on a fence-suffixed opening that carries valid
    YAML: the old regex bailed out entirely ({}), the canonical splitter
    recovers the mapping. Both behaviors agree on every bare-fence file —
    this documents the accepted delta on the pathological form."""
    content = "---a: 1\n---\nbody"
    assert old_pipelines_plan_ref_fm(content) == {}
    assert parse_frontmatter_text(content) == {"a": 1}
    assert old_pipelines_plan_ref_fm(content) != parse_frontmatter_text(content)


def test_delta_strip_keeps_crlf_carriage_returns():
    """The old builder strip lstripped ALL whitespace (including \\r); the
    canonical core strips only newlines. No agent-meta template uses CRLF
    fences (verified repo-wide) — documented accepted delta."""
    content = "---\r\nname: x\r\n---\r\nbody"
    assert old_builder_strip(content) == "body"
    assert strip_frontmatter(content) == "\r\nbody"


def test_delta_strip_keeps_body_indentation():
    """The old builder strip lstripped ALL whitespace of the body; the
    canonical core only strips newlines right after the closing fence. No
    template's body starts with spaces/tabs (verified repo-wide)."""
    content = "---\nname: x\n---\n  indented"
    assert old_builder_strip(content) == "indented"
    assert strip_frontmatter(content) == "  indented"


def test_delta_consistency_closing_fence_glued_to_body():
    """Old consistency regex required '\\n' after the closing fence; the
    canonical splitter does not. '---body' glued closing now parses instead
    of reporting frontmatter.missing."""
    content = "---\nname: x\n---body"
    assert old_consistency_frontmatter_parse(content) is None


def test_delta_crossrefs_dashes_inside_block_scalar():
    """Old crossrefs split cut at the first literal '---' anywhere (also
    inside a YAML block scalar), truncating the block scalar; the canonical
    splitter finds the real closing fence and parses the full document."""
    content = "---\nkey: |\n  x\n  ---\n  y\n---\nbody"
    assert old_crossrefs_parse(content) == {"key": "x\n"}  # truncated block scalar
    assert parse_frontmatter_text(content) == {"key": "x\n---\ny"}


# --- public API basics --------------------------------------------------------

def test_split_frontmatter_returns_block_and_body():
    fm_block, body = split_frontmatter(VALID_FM)
    assert fm_block == "---\nname: developer\nversion: 1.0.0\ntools:\n  - Bash\n---"
    assert body == "\n# Body\n"


def test_parse_frontmatter_text_fail_soft_contract():
    assert parse_frontmatter_text("no fm") == {}
    assert parse_frontmatter_text("---\nname: [broken\n---\n") == {}
    assert parse_frontmatter_text("---\njust a string\n---\n") == {}  # non-mapping → {}
    assert parse_frontmatter_text("---\nname: x\n---\n")["name"] == "x"


def test_strip_frontmatter_without_fm_returns_content_unchanged():
    assert strip_frontmatter("plain content") == "plain content"
    assert strip_frontmatter("---\nunclosed") == "---\nunclosed"
