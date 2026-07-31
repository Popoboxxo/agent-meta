# Fix Sync-Engine & Claude-Best-Practices Audit Findings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the critical and important bugs found in the 2026-07-31 audit of agent-meta's sync/composition engine and its Claude Code best-practices posture (settings.json hooks, permissions, templates), each with a regression test that would have caught it.

**Architecture:** Each finding gets its own bite-sized task: write a failing regression test against the current (buggy) behavior, fix the minimal code/config, verify the test passes, commit. Tasks are ordered by severity (kritisch → wichtig → gering) and are independent of each other except Task 10, which is the final full-repo verification and must run last.

**Tech Stack:** Python 3.x stdlib (`re`, `json`, `argparse`), `pytest` (already used by `tests/test_deprecated_filter.py` etc. via `sys.path.insert(scripts/)` + `from lib.X import Y`), no new dependencies.

## Global Constraints

- Branch-Guard (`.claude/rules/branch-guard.md`): all work happens on a feature branch (`fix/sync-admin-audit-findings`), never on `main`.
- Commit-Konventionen (`.claude/rules/commit-conventions.md`): Conventional Commits, English description, max 72 chars first line, imperative.
- Conventions (`.claude/rules/conventions.md`): bump the affected script/module version where frontmatter version fields exist; `.claude/agents/*` is generated output — never hand-edit it, only regenerate via `python scripts/sync.py`.
- Python-Conventions (`.claude/rules/python-conventions.md`): PEP8, type hints, docstrings for new functions/classes.
- No test file may import anything outside the existing `sys.path.insert(str(_SCRIPTS_DIR), 0)` + `from lib.X import Y` pattern already used by `tests/test_deprecated_filter.py` — this repo has no `pyproject.toml`/`pytest.ini`, tests run via `python -m pytest tests/ -q` from the repo root.
- Submodule-Schutzkonzept: none of this touches `.agent-meta/` or `external/*/` — all target files are native to this repo (`scripts/`, `hooks/`, `templates/`, `agents/0-external/`, `.claude/rules/`).

---

### Task 1: Fenced-code-block tracking in `_find_section_bounds`

**Files:**
- Modify: `scripts/lib/agents.py:652-694` (`_find_section_bounds`)
- Test: `tests/test_composition_engine.py` (new)

**Interfaces:**
- Consumes: nothing new.
- Produces: `_find_section_bounds(lines: list[str], anchor: str) -> tuple[int, int] | None` — same signature, now correctly skips `#`-prefixed lines that are inside fenced code blocks (` ``` ` or `~~~`) when scanning for the next heading.

Current buggy behavior: any line starting with `#` terminates a section, even a Bash comment (`# Build`) inside a ` ```bash ` block, because there is no fenced-code-block tracking.

- [ ] **Step 1: Write the failing test**

```python
"""Regression tests for the composition/patch engine (scripts/lib/agents.py).

Run: python -m pytest tests/test_composition_engine.py -v
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.agents import _find_section_bounds, apply_patch
from lib.log import SyncLog


SECTION_WITH_CODE_BLOCK = """## Build & Development

```bash
# Build
python scripts/sync.py

# Tests
python scripts/sync.py --validate
```

## Next Section

Some other content.
"""


def test_find_section_bounds_skips_hash_comments_in_fenced_code_block():
    lines = SECTION_WITH_CODE_BLOCK.splitlines(keepends=True)
    bounds = _find_section_bounds(lines, "## Build & Development")
    assert bounds is not None
    start, end = bounds
    # The section must extend up to (not into) "## Next Section", i.e. it must
    # include the full fenced code block including its "# Build" / "# Tests" comments.
    section_text = "".join(lines[start:end])
    assert "python scripts/sync.py --validate" in section_text
    assert "## Next Section" not in section_text


def test_patch_replace_does_not_truncate_at_code_block_comment():
    log = SyncLog()
    patch = {
        "op": "replace",
        "anchor": "## Build & Development",
        "content": "## Build & Development\n\nReplaced entirely.\n",
    }
    result = apply_patch(SECTION_WITH_CODE_BLOCK, patch, log, "test-source")
    assert "Replaced entirely." in result
    # Old code-block remnants must be fully gone, not just the heading.
    assert "python scripts/sync.py --validate" not in result
    assert "## Next Section" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_composition_engine.py -v -k "code_block"`
Expected: FAIL — `test_find_section_bounds_skips_hash_comments_in_fenced_code_block` fails because `bounds` ends at the `# Build` line inside the fenced block, so `"python scripts/sync.py --validate" in section_text` is `False`. `test_patch_replace_does_not_truncate_at_code_block_comment` fails because the leftover `python scripts/sync.py --validate` and dangling fence remain in `result`.

- [ ] **Step 3: Write minimal implementation**

Replace `scripts/lib/agents.py:687-694` (the scan loop inside `_find_section_bounds`) with fence-aware scanning:

```python
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
```

This treats any line whose stripped form starts with ` ``` ` or `~~~` as a fence toggle (matching CommonMark fenced code blocks, which is the only fence style used in this repo's templates — confirmed by grep over `agents/1-generic/*.md`), and skips heading detection while inside one.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_composition_engine.py -v -k "code_block"`
Expected: PASS (both tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/agents.py tests/test_composition_engine.py
git commit -m "fix: track fenced code blocks in section-bounds scanner"
```

---

### Task 2: Align anchor validation with the patch engine's exact-match rule

**Files:**
- Modify: `scripts/lib/consistency/frontmatter.py:149-154` (`_check_patch_anchors` plain-text anchor branch)
- Test: `tests/test_composition_engine.py` (extend from Task 1)

**Interfaces:**
- Consumes: `_find_section_bounds` from `lib.agents` (Task 1's fixed version).
- Produces: no new public function; `_check_patch_anchors` now reports `frontmatter.patch-anchor-not-found` exactly when `apply_patch` would actually fail to find the anchor — i.e. same exact-line-match semantics, not substring.

Current bug: `frontmatter.py:149` does `if anchor not in base_content` (substring anywhere in the file), while `agents.py:680` requires `line.rstrip() == anchor_stripped` (exact full-line match after a heading). An anchor like `## Config` that only appears as `## Configuration` or inside a code comment passes validation but silently fails at patch time (`apply_patch` just returns the content unchanged with a `log.warning`, no exit code).

- [ ] **Step 1: Write the failing test**

Add to `tests/test_composition_engine.py`:

```python
from lib.consistency.frontmatter import _check_patch_anchors


def test_validator_rejects_anchor_that_is_only_a_substring(tmp_path):
    base_path = tmp_path / "agents" / "1-generic" / "example.md"
    base_path.parent.mkdir(parents=True)
    base_path.write_text("## Configuration\n\nSome text.\n", encoding="utf-8")

    patches = [{"op": "replace", "anchor": "## Config", "content": "## Config\n\nNew.\n"}]
    findings = _check_patch_anchors(
        patches, "1-generic/example.md", "some/override.md", tmp_path,
    )
    check_ids = [f.check for f in findings]
    assert "frontmatter.patch-anchor-not-found" in check_ids
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_composition_engine.py -v -k substring`
Expected: FAIL — `findings` is empty because `"## Config" in base_content` is `True` (it's a substring of `"## Configuration"`), so no `Finding` is appended.

- [ ] **Step 3: Write minimal implementation**

In `scripts/lib/consistency/frontmatter.py`, add the import and replace the plain-text check:

```python
from ..agents import _find_section_bounds
```//top of file, with the other imports

Replace lines 149-154:

```python
        base_lines = base_content.splitlines(keepends=True)
        if _find_section_bounds(base_lines, anchor) is None:
            findings.append(Finding(
                Severity.ERROR, "frontmatter.patch-anchor-not-found", rel,
                f"patches[{i}] anchor not found in base file '{extends}': {anchor!r}",
                "The anchor string must appear verbatim as a heading line in the base file "
                "(exact match, not a substring of a longer heading).",
            ))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_composition_engine.py -v -k substring`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/consistency/frontmatter.py tests/test_composition_engine.py
git commit -m "fix: validate patch anchors with same exact-match rule as patch engine"
```

---

### Task 3: `--check` must not write real files without `--dry-run`

**Files:**
- Modify: `scripts/sync.py` (main(), right after `args = parser.parse_args()`)
- Test: `tests/test_sync_check_flag.py` (new)

**Interfaces:**
- Consumes: nothing new.
- Produces: `_normalize_check_dry_run(args: argparse.Namespace) -> None` — mutates `args.dry_run` in place to `True` whenever `args.check` is truthy. Pure, side-effect-only-on-args function so it's unit-testable without touching the filesystem.

Current bug: `--check` alone runs the full sync (writes files), then at the very end (`sync.py:1227`) checks `len(log.actions)` to decide the exit code. The help text says "(use with --dry-run)" but nothing enforces it.

- [ ] **Step 1: Write the failing test**

```python
"""Regression test: --check must force --dry-run so CI never gets real writes.

Run: python -m pytest tests/test_sync_check_flag.py -v
"""

import sys
from argparse import Namespace
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from sync import _normalize_check_dry_run


def test_check_without_dry_run_forces_dry_run():
    args = Namespace(check=True, dry_run=False)
    _normalize_check_dry_run(args)
    assert args.dry_run is True


def test_check_with_dry_run_stays_dry_run():
    args = Namespace(check=True, dry_run=True)
    _normalize_check_dry_run(args)
    assert args.dry_run is True


def test_no_check_leaves_dry_run_untouched():
    args = Namespace(check=False, dry_run=False)
    _normalize_check_dry_run(args)
    assert args.dry_run is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sync_check_flag.py -v`
Expected: FAIL with `ImportError: cannot import name '_normalize_check_dry_run' from 'sync'` (function does not exist yet).

- [ ] **Step 3: Write minimal implementation**

In `scripts/sync.py`, add the function near the top of `main()` (or just above it) and call it immediately after argument parsing:

```python
def _normalize_check_dry_run(args) -> None:
    """--check is a read-only CI gate: it must never allow real writes.

    If the caller forgot --dry-run, force it rather than silently writing files.
    """
    if getattr(args, "check", False) and not getattr(args, "dry_run", False):
        args.dry_run = True
```

Find the line `args = parser.parse_args()` in `main()` and add directly after it:

```python
    args = parser.parse_args()
    _normalize_check_dry_run(args)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sync_check_flag.py -v`
Expected: PASS (3 tests)

Also manually verify end-to-end: `python scripts/sync.py --check` on this repo must now print no `WRITE`/`UPDATE` actions to disk (check `git status` shows no changes) and exit 0 or 1 based on drift only.

- [ ] **Step 5: Commit**

```bash
git add scripts/sync.py tests/test_sync_check_flag.py
git commit -m "fix: --check now forces --dry-run to prevent CI writes"
```

---

### Task 4: Hook-metadata parser must strip quoted matcher values

**Files:**
- Modify: `scripts/lib/hooks.py:37-53` (`parse_hook_metadata`)
- Test: `tests/test_hook_metadata.py` (new)

**Interfaces:**
- Consumes: nothing new.
- Produces: `parse_hook_metadata(script_content: str) -> dict` — same signature; string values wrapped in a single pair of matching double quotes now have the quotes stripped, so `# matcher: ""` yields `meta["matcher"] == ""` instead of the literal two-character string `'""'`.

Current bug: `hooks/1-generic/orchestrator-guard.sh:5` has `# matcher: ""` (intending "no restriction — match all tools"). The regex `r"^#\s*([\w-]+):\s*(.+)$"` captures group 2 as the literal string `""` (a quote, a quote — 2 chars, truthy). `sync_hooks` (`hooks.py:296`) then does `"matcher": meta.get("matcher", "")` and `_update_settings_hooks` (`hooks.py:152-156`) does `if matcher: hook_entry["matcher"] = matcher` — since `'""'` is truthy, it writes `"matcher": "\"\""` into `.claude/settings.json`. Claude Code's hook matcher is a regex tested against the tool name; a 2-character string of literal quote marks never matches any real tool name, so the entire hook is dead. This is exactly what's committed at `.claude/settings.json:52` today.

- [ ] **Step 1: Write the failing test**

```python
"""Regression test: hook header `# matcher: ""` must parse to an empty string,
not the literal two-character string of quote marks.

Run: python -m pytest tests/test_hook_metadata.py -v
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.hooks import parse_hook_metadata


def test_quoted_empty_matcher_parses_to_empty_string():
    content = (
        "#!/bin/bash\n"
        "# hook: orchestrator-guard\n"
        '# matcher: ""\n'
        "# event: PreToolUse\n"
    )
    meta = parse_hook_metadata(content)
    assert meta.get("matcher", "") == ""


def test_unquoted_matcher_is_unaffected():
    content = (
        "#!/bin/bash\n"
        "# hook: dod-push-check\n"
        "# matcher: Bash\n"
        "# event: PreToolUse\n"
    )
    meta = parse_hook_metadata(content)
    assert meta["matcher"] == "Bash"


def test_orchestrator_guard_source_file_parses_to_empty_matcher():
    """Guards against the real header regressing back to a quoted literal."""
    path = _REPO_ROOT / "hooks" / "1-generic" / "orchestrator-guard.sh"
    meta = parse_hook_metadata(path.read_text(encoding="utf-8"))
    assert meta.get("matcher", "") == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_hook_metadata.py -v`
Expected: FAIL — `test_quoted_empty_matcher_parses_to_empty_string` and `test_orchestrator_guard_source_file_parses_to_empty_matcher` fail because `meta.get("matcher", "")` is `'""'`, not `''`.

- [ ] **Step 3: Write minimal implementation**

Replace `scripts/lib/hooks.py:50-52` inside `parse_hook_metadata`:

```python
        m = re.match(r"^#\s*([\w-]+):\s*(.+)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
            meta[key] = value
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_hook_metadata.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/hooks.py tests/test_hook_metadata.py
git commit -m "fix: strip quoted values in hook metadata header parsing"
```

---

### Task 5: Regenerate this repo's own `.claude/settings.json` and verify the hook actually fires

**Files:**
- Modify (generated, via sync.py — do not hand-edit): `.claude/settings.json`
- Verify: `hooks/1-generic/orchestrator-guard.sh` (no change expected, just confirms Task 4 fixed the consumer)

**Interfaces:**
- Consumes: Task 4's fixed `parse_hook_metadata`.
- Produces: nothing new — this task is pure verification + regeneration, no new code.

agent-meta dogfoods itself: this repo's own `.claude/` is generated by its own `scripts/sync.py` against its own `.meta-config/project.yaml`. Task 4 fixes the parser; this task actually re-runs the generator so the fix takes effect in the committed file, and proves it end-to-end.

- [ ] **Step 1: Dry-run first to see the diff**

Run: `python scripts/sync.py --dry-run`
Expected output includes a line like `UPDATE  .claude/settings.json  registered hooks: orchestrator-guard` (or similar — the important part is that `.claude/settings.json` is listed as changing).

- [ ] **Step 2: Run for real**

Run: `python scripts/sync.py`

- [ ] **Step 3: Verify the fix took effect**

Run: `python -c "import json; d=json.load(open('.claude/settings.json')); print(d['hooks']['PreToolUse'])"`
Expected: the `orchestrator-guard` entry's dict has **no** `"matcher"` key at all (correctly omitted per `hooks.py:155-156` since the now-empty string is falsy), instead of `"matcher": "\"\""`.

- [ ] **Step 4: Confirm no other unrelated diffs snuck in**

Run: `git diff --stat`
Expected: only `.claude/settings.json` (and possibly `.meta-config/context-hashes.json` / `.claude/sync.log` if tracked) changed — no unrelated file churn. If other files show up, stop and investigate before committing (do not blindly commit unexpected changes).

- [ ] **Step 5: Commit**

```bash
git add .claude/settings.json
git commit -m "chore: regenerate settings.json with fixed hook matcher"
```

---

### Task 6: Default permission deny-list for new Claude projects

**Files:**
- Modify: `templates/configs/CLAUDE.settings-template.json`
- Test: `tests/test_settings_template.py` (new)

**Interfaces:**
- Consumes: nothing new.
- Produces: no new functions — a data-only template change. `_init_provider_settings_json` (`scripts/lib/context.py:695`) copies this file verbatim (via `substitute()`, no placeholders used here) into a brand-new project's `.claude/settings.json` on first `--init`/first sync. Existing projects' `settings.json` are **never overwritten** by this template (confirmed at `context.py:710-713`), so this only affects newly instantiated projects — it is safe to change without a migration step.

Current gap: `templates/configs/CLAUDE.settings-template.json` ships `"deny": []` — no defense-in-depth against destructive shell operations if a hook is ever misconfigured or disabled (as Task 4/5 just proved can happen silently).

- [ ] **Step 1: Write the failing test**

```python
"""Regression test: the Claude settings template ships a non-empty default
permission deny-list for destructive shell operations.

Run: python -m pytest tests/test_settings_template.py -v
"""

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATE = _REPO_ROOT / "templates" / "configs" / "CLAUDE.settings-template.json"

REQUIRED_DENY_PREFIXES = (
    "Bash(rm -rf",
    "Bash(git push --force",
    "Bash(git reset --hard",
)


def test_settings_template_has_default_deny_list():
    data = json.loads(_TEMPLATE.read_text(encoding="utf-8"))
    deny = data["permissions"]["deny"]
    assert isinstance(deny, list) and len(deny) > 0
    for prefix in REQUIRED_DENY_PREFIXES:
        assert any(entry.startswith(prefix) for entry in deny), (
            f"expected a deny entry starting with {prefix!r}, got {deny!r}"
        )


def test_settings_template_is_still_valid_json():
    # Guards against a hand-edit breaking JSON syntax.
    json.loads(_TEMPLATE.read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_settings_template.py -v`
Expected: FAIL — `data["permissions"]["deny"]` is `[]`, so `len(deny) > 0` is `False`.

- [ ] **Step 3: Write minimal implementation**

Replace the full content of `templates/configs/CLAUDE.settings-template.json`:

```json
{
  "permissions": {
    "allow": [],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(git push --force:*)",
      "Bash(git push -f:*)",
      "Bash(git reset --hard:*)"
    ]
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_settings_template.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add templates/configs/CLAUDE.settings-template.json tests/test_settings_template.py
git commit -m "feat: default permission deny-list for destructive shell ops in new projects"
```

---

### Task 7: Remove unnecessary `Agent` tool from the external-skill wrapper template

**Files:**
- Modify: `agents/0-external/_skill-wrapper.md:6-11`
- Test: `tests/test_skill_wrapper_tools.py` (new)

**Interfaces:**
- Consumes: nothing new.
- Produces: no new functions — frontmatter data change. Every generated skill-wrapper agent (via `config/skills-registry.yaml`) inherits this `tools:` list, so removing `Agent` here narrows the blast radius of every external-skill-wrapper agent generated from this template.

Current gap: `_skill-wrapper.md` grants `Agent` to every skill wrapper, letting a supposedly narrow, single-purpose skill agent delegate to arbitrary other agents — wider blast radius than the wrapper's stated purpose ("hochspezialisiert... verweise an den `developer`-Agenten" — i.e. it's supposed to hand off by *recommending*, not by *calling* `Agent` itself).

- [ ] **Step 1: Write the failing test**

```python
"""Regression test: the external-skill wrapper template must not grant the
Agent tool — it should recommend delegation in text, not perform it itself.

Run: python -m pytest tests/test_skill_wrapper_tools.py -v
"""

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATE = _REPO_ROOT / "agents" / "0-external" / "_skill-wrapper.md"


def test_skill_wrapper_does_not_grant_agent_tool():
    content = _TEMPLATE.read_text(encoding="utf-8")
    fm_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert fm_match, "frontmatter block not found"
    fm_block = fm_match.group(1)
    tools_match = re.search(r"^tools:\n((?:\s*-\s*.+\n?)+)", fm_block, re.MULTILINE)
    assert tools_match, "tools: list not found in frontmatter"
    tools = [line.strip("- ").strip() for line in tools_match.group(1).splitlines() if line.strip()]
    assert "Agent" not in tools, f"expected no Agent tool, got {tools!r}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_skill_wrapper_tools.py -v`
Expected: FAIL — `tools` includes `"Agent"`.

- [ ] **Step 3: Write minimal implementation**

In `agents/0-external/_skill-wrapper.md`, change the frontmatter `tools:` block (lines 6-11) from:

```yaml
tools:
  - Read
  - Bash
  - Glob
  - Grep
  - Agent
```

to:

```yaml
tools:
  - Read
  - Bash
  - Glob
  - Grep
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_skill_wrapper_tools.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agents/0-external/_skill-wrapper.md tests/test_skill_wrapper_tools.py
git commit -m "fix: remove Agent tool from external-skill wrapper template"
```

---

### Task 8: Fix escape-syntax documentation to match the actual code

**Files:**
- Modify: `.claude/rules/architecture.md:63-65` and its source `rules/1-generic/architecture.md` (same section — check both; `.claude/rules/` is generated from `rules/1-generic/` per the sync pipeline, so the source-of-truth edit belongs in `rules/1-generic/architecture.md`, then regenerate)
- Test: `tests/test_escape_syntax_docs.py` (new)

**Interfaces:**
- Consumes: nothing new.
- Produces: no new functions — doc text fix so it matches `substitute()`'s real escape token (`{{%VAR%}}`), confirmed at `scripts/lib/config.py:903-916`.

Current bug: the doc says `` `{{VAR}}` → rendert als `{{VAR}}` ohne Substitution `` but the code's actual escape regex is `r"\{\{%([A-Z0-9_]+)%\}\}"` — i.e. the real escape syntax is `{{%VAR%}}`, not `{{VAR}}` (which is just the normal substitution token and gets replaced or warned about, never left literal).

- [ ] **Step 1: Write the failing test**

```python
"""Regression test: the documented placeholder-escape syntax must match
scripts/lib/config.py's actual `substitute()` implementation.

Run: python -m pytest tests/test_escape_syntax_docs.py -v
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SOURCE_RULE = _REPO_ROOT / "rules" / "1-generic" / "architecture.md"


def test_architecture_doc_documents_real_escape_syntax():
    content = _SOURCE_RULE.read_text(encoding="utf-8")
    assert "{{%VAR%}}" in content, (
        "architecture.md must document the real escape token {{%VAR%}} "
        "(see scripts/lib/config.py substitute())"
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_escape_syntax_docs.py -v`
Expected: FAIL — `"{{%VAR%}}"` is not in the current doc text (it documents `{{VAR}}` instead).

- [ ] **Step 3: Write minimal implementation**

In `rules/1-generic/architecture.md`, find the `## Platzhalter-Escape` section (mirrors `.claude/rules/architecture.md:63-65`) and change:

```markdown
## Platzhalter-Escape

`{{VAR}}` → rendert als `{{VAR}}` ohne Substitution (für Dokumentation in Templates)
```

to:

```markdown
## Platzhalter-Escape

`{{%VAR%}}` → rendert als `{{VAR}}` ohne Substitution (für Dokumentation in Templates)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_escape_syntax_docs.py -v`
Expected: PASS

Then regenerate the derived copy: `python scripts/sync.py --dry-run` should show `.claude/rules/architecture.md` as changing; run `python scripts/sync.py` for real and confirm `git diff .claude/rules/architecture.md` shows the same one-line fix propagated.

- [ ] **Step 5: Commit**

```bash
git add rules/1-generic/architecture.md .claude/rules/architecture.md tests/test_escape_syntax_docs.py
git commit -m "docs: fix placeholder-escape syntax example to match substitute()"
```

---

### Task 9: CRLF-safe patch content insertion

**Files:**
- Modify: `scripts/lib/agents.py:697-757` (`_patch_append_after`, `_patch_replace`, `apply_patch`'s `"append"` branch)
- Test: `tests/test_composition_engine.py` (extend from Tasks 1-2)

**Interfaces:**
- Consumes: nothing new.
- Produces: a small private helper `_dominant_newline(lines: list[str]) -> str` returning `"\r\n"` or `"\n"` based on the majority line ending in the base file; the three patch functions now normalize inserted `patch_content` to that ending before splicing.

Current bug: `patch_content.rstrip("\n") + "\n\n"` etc. always inserts bare `\n` line endings, while `content.splitlines(keepends=True)` preserves whatever the base file used (`\r\n` on a CRLF-saved Windows template). Splicing LF-only patch lines into a CRLF base file produces a mixed-line-ending file — noisy git diffs and inconsistent output.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_composition_engine.py`:

```python
def test_patch_replace_preserves_base_file_crlf_line_endings():
    base = "## Section\r\n\r\nOld content.\r\n\r\n## Next\r\n\r\nOther.\r\n"
    patch = {"op": "replace", "anchor": "## Section", "content": "## Section\n\nNew content.\n"}
    log = SyncLog()
    result = apply_patch(base, patch, log, "test-source")
    # Every line in the result must end with \r\n, matching the CRLF base file.
    for line in result.splitlines(keepends=True):
        if line.strip("\r\n"):
            assert line.endswith("\r\n"), f"expected CRLF line ending, got {line!r}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_composition_engine.py -v -k crlf`
Expected: FAIL — the lines coming from `patch_content` (which used `\n`) fail the `line.endswith("\r\n")` assertion.

- [ ] **Step 3: Write minimal implementation**

Add a helper near the top of the patch functions in `scripts/lib/agents.py`:

```python
def _dominant_newline(lines: list[str]) -> str:
    """Return the majority line-ending style ('\\r\\n' or '\\n') of a splitlines(keepends=True) list."""
    crlf_count = sum(1 for line in lines if line.endswith("\r\n"))
    lf_count = sum(1 for line in lines if line.endswith("\n") and not line.endswith("\r\n"))
    return "\r\n" if crlf_count > lf_count else "\n"
```

Then in `_patch_append_after` (around line 706), `_patch_replace` (around line 720), and `apply_patch`'s `"append"` branch (line 748), normalize the patch content's newlines to the base file's dominant style before splicing. For `_patch_append_after`:

```python
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
```

Apply the same `nl = _dominant_newline(lines); normalized_patch = patch_content.replace("\r\n", "\n").rstrip("\n").replace("\n", nl)` pattern to `_patch_replace` and to the `"append"` branch in `apply_patch` (there, compute `nl` from `content.splitlines(keepends=True)`).

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_composition_engine.py -v -k crlf`
Expected: PASS

Also re-run the full file to make sure Tasks 1-2's tests still pass (they use LF-only fixtures, so `_dominant_newline` must default to `"\n"` when there are zero or equal CRLF/LF lines — verify this by re-running the whole test module):

Run: `python -m pytest tests/test_composition_engine.py -v`
Expected: PASS (all tests in the file)

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/agents.py tests/test_composition_engine.py
git commit -m "fix: preserve base file's line-ending style when splicing patches"
```

---

### Task 10: Submodule-protection save/restore key symmetry in the Admin UI backend

**Files:**
- Modify: `scripts/admin-server.py:1297-1303` (`_write_submodule_protection`, non-restore branch)
- Test: `tests/test_admin_server.py` (extend existing file — check its imports/fixtures first, this file already exists and has admin-server test infrastructure)

**Interfaces:**
- Consumes: nothing new.
- Produces: no new functions — `_write_submodule_protection`'s save path now also removes the stale nested `project_config["rules"]["submodule-protection"]` key when writing the flat key, mirroring what `restore_default` already does, so a project never ends up with both a flat and a nested override key.

Current bug: `restore_default` (lines 1277-1284) cleans up three possible key locations (`submodule-protection`, `submodule_protection`, `rules.submodule-protection`), but the normal save path (lines 1297-1300) only ever writes the flat `submodule-protection` key — it never removes a pre-existing nested `rules.submodule-protection` key. Reads happen to still resolve correctly today (flat key wins per `_get_submodule_protection_status:3649`), but the stale nested key lingers in `project.yaml` indefinitely after every save, which is exactly the kind of config drift `.claude/rules/conventions.md`'s "Instruction Bleed" section warns about for composition-adjacent config.

- [ ] **Step 1: Write the failing test**

First, read `tests/test_admin_server.py`'s existing setup (imports, how `config_manager`/`root` class attributes are stubbed, or if it spins up a real `http.server` instance) before writing this — match its existing test style exactly. Assuming it already has a pattern for constructing a request handler instance with a stubbed `config_manager`, add:

```python
def test_save_removes_stale_nested_rules_key(admin_handler_with_config):
    """Saving a flat submodule-protection override must clean up any stale
    nested rules.submodule-protection key left over from an older save.
    """
    handler = admin_handler_with_config({
        "rules": {"submodule-protection": "old nested override text"},
    })
    handler._write_submodule_protection_body = {
        "restore_default": False,
        "enabled": True,
        "override_text": "new override text",
    }
    handler._write_submodule_protection()

    saved = handler.__class__.config_manager.read("project")
    assert saved.get("submodule-protection") == "new override text"
    assert "submodule-protection" not in saved.get("rules", {})
```

(This test skeleton assumes a fixture `admin_handler_with_config` exists or can be trivially added following the file's existing conventions — inspect `tests/test_admin_server.py` first and adapt the construction/mocking approach to whatever pattern it already uses, e.g. it may already expose a helper to build a handler instance with a fake `config_manager` and a way to inject the parsed JSON body instead of reading from a real HTTP request. If `_write_submodule_protection` reads the body via `self._read_body()`, mock that method instead of setting an attribute directly — check the real method name and adapt.)

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_admin_server.py -v -k stale_nested`
Expected: FAIL — `saved["rules"]["submodule-protection"]` still equals `"old nested override text"` because the save path never touches `rules`.

- [ ] **Step 3: Write minimal implementation**

In `scripts/admin-server.py`, change the non-restore branch of `_write_submodule_protection` (lines 1297-1303):

```python
        if not enabled:
            project_config["submodule-protection"] = False
        else:
            project_config["submodule-protection"] = override_text

        # Clean up a stale nested override so only one representation exists.
        if "rules" in project_config and isinstance(project_config["rules"], dict):
            project_config["rules"].pop("submodule-protection", None)

        self.__class__.config_manager.write("project", project_config)
        return self._send_json({"status": "saved"})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_admin_server.py -v -k stale_nested`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/admin-server.py tests/test_admin_server.py
git commit -m "fix: clean up stale nested rules key when saving submodule-protection override"
```

---

### Task 11: Full-repo verification and final re-sync

**Files:** none modified — verification only.

**Interfaces:** none.

This task is the barrier at the end: it re-runs everything to make sure Tasks 1-10 compose correctly and nothing regressed.

- [ ] **Step 1: Run the full test suite**

Run: `python -m pytest tests/ -q --no-header -p no:cacheprovider`
Expected: all tests pass, including every new test file from Tasks 1-10 and every pre-existing test (`test_config_audit.py`, `test_deprecated_filter.py`, `test_model_discovery.py`, etc.).

- [ ] **Step 2: Run the consistency checker**

Run: `python scripts/consistency-check.py`
Expected: no new `frontmatter.patch-anchor-not-found` or other errors introduced by Tasks 1-10's own template/doc edits.

- [ ] **Step 3: Full dry-run sync**

Run: `python scripts/sync.py --dry-run`
Expected: no unexpected file changes beyond what Tasks 5 and 8 already committed (i.e. running it again should now report everything unchanged, proving idempotency after the fixes).

- [ ] **Step 4: Full real sync + validate**

Run: `python scripts/sync.py --validate`
Expected: exits 0 — the sync-into-test-repo validation (per `--validate`'s docstring at `scripts/sync.py:455-459`) reports no errors.

- [ ] **Step 5: Final commit (if Step 3/4 produced any residual diffs)**

```bash
git status
# If clean, nothing to commit — this task is verification-only.
# If sync.py --dry-run in Step 3 revealed anything, run sync.py for real and:
git add -A
git commit -m "chore: final re-sync after audit fixes"
```

---

## Deferred / Not in this plan (deliberately out of scope)

- **Wiring the 3 remaining unregistered hooks** (`lifecycle-check.sh`, `sync-on-config-change.sh`, `viz-log.sh`) into `settings.json` events: `dod-push-check` is already `enabled: true` in `.meta-config/project.yaml:110-111` and just needs a fresh `sync.py` run (covered incidentally by Task 5/11) — but the other three are `enabled_by_default: false` by design (opt-in per project, per `sync_hooks`'s own docstring at `hooks.py:204-208`). Deciding whether agent-meta itself *should* opt into them is a product decision for the user, not a bug fix — flag it back to them separately.
- **Stripping non-standard frontmatter fields** (`version`, `hint`, `prompt_mode`, `generated-from`, `based-on`) from generated `.claude/agents/*.md`: `hint` in particular feeds `AGENT_HINTS` generation for the routing table per `conventions.md`'s change checklist, and `based-on`/`generated-from` feed the Admin UI's provenance display. Removing them needs a full consumer audit (viz generator, admin-server.py, consistency-check.py) before touching the generated schema — too large to scope safely into this plan without that investigation.
- **Duplicate-identical-heading edge case** (`_find_section_bounds` matches only the first occurrence of an anchor): very low severity, no known real occurrence in current templates; revisit only if it actually bites someone.
- **Model-ID aliasing** (`claude-haiku-4-5-20251001` → `haiku`) and **routing-table size reduction** in `use-orchestrator.md`: cosmetic/maintenance nice-to-haves from the claude-howto audit, not bugs — candidates for a separate, non-urgent cleanup pass.
- **`orchestrator-guard.sh`'s exemption logic doesn't recognize main-chat-as-orchestrator or the `git` delegate agent** (discovered while executing Task 5 on this very repo, once the fix made the hook live for the first time): the hook only exempts calls where `agent_name` contains the substring `"orchestrator"`, but this repo's own configured mode (`.meta-config/project.yaml`: `orchestrator.strict: true`, `direct-dispatch-enabled: true`; `.claude/rules/use-orchestrator.md`: "Kein Orchestrator-Subagent. Du bist der Orchestrator!") has the main chat session act as the orchestrator directly, and routes git mutations to a separate `git` agent — neither of which matches that substring check. This is a real, previously-untriggered gap (dormant only because Task 4's bug kept the hook dead) with real operational impact (it blocked — and in one case appears to have caused a runtime hook error during — the Task 5 implementer's own commit). Out of scope for this plan; needs its own investigation and a decision from the user on the intended exemption rule before touching `orchestrator-guard.sh`'s logic.

---

## Self-Review Notes

- Spec coverage: all 4 kritisch findings (Tasks 1, 3, 4+5) and all 4 wichtig findings (Tasks 2, 6, 7, plus test-coverage itself being the point of every task here) have a task; all 3 gering findings (Tasks 8, 9, 10) have a task except the duplicate-heading edge case, explicitly deferred above with justification.
- Placeholder scan: every code step above shows the actual diff/replacement text, not a description of one; the one intentionally-loose step (Task 10 Step 1) explicitly says why (this repo's existing `test_admin_server.py` fixture pattern must be inspected first — matching an unknown existing test harness precisely without reading it first would be a placeholder in disguise).
- Type/name consistency: `_find_section_bounds` (Task 1) is reused unchanged in Task 2's validator fix and Task 9's newline fix; `_normalize_check_dry_run` (Task 3) and `_dominant_newline` (Task 9) are each defined once and used exactly where named.
