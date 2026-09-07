# Generated-File Drift Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Warn when a sync.py-generated file (agent/rule/hook/command/skill/pipeline-detail — anything tracked via `.agent-meta-managed`) was manually edited since the last sync, without changing write behavior, with a per-path allowlist to silence expected edits.

**Architecture:** One new module `scripts/lib/generated_file_drift.py` provides a pure scan function (compares current file hashes against a stored baseline) and a capture function (writes a fresh baseline after sync finishes writing). Two new stages in the existing `_sync_stage_*` pipeline (`scripts/lib/sync_pipeline.py`) call these: an early scan-and-warn stage inserted *before* the per-provider write stage (so it sees pre-overwrite state), and a late capture stage at the very end of `_handle_sync` (so it captures post-write state).

**Tech Stack:** Python 3.9+ stdlib only (`fnmatch`, `hashlib` via the existing `content_hash()` helper, `pathlib`), reusing this repo's existing `scripts/lib/io.py` loaders (`load_json_file`, `load_yaml_file`, `write_atomic`) and `scripts/lib/rule_index.py`'s `read_managed_index`.

**Spec:** `docs/superpowers/specs/2026-09-07-generated-file-drift-detection-design.md`

## Global Constraints

- Python 3.9 floor: no bare `X | Y` union syntax without `from __future__ import annotations` as the first statement after the module docstring (this repo's CI matrix includes 3.9; `scripts/lib/consistency/python_compat.py::check_py39_union_syntax` enforces this on `scripts/lib/` and `tests/`).
- No f-string with a backslash inside a `{...}` expression (breaks on Python < 3.12; `check_fstring_backslash_hazard` enforces this on the same two trees).
- Provider-agnostic credo: never branch on `if provider == "Name"` in `scripts/lib/*.py` — express differences via `provider_config`/capability flags (`pc.get("has_hooks", False)`, etc.).
- This phase is warn-only: detecting drift must never change which files get written or what content they get. No skip-overwrite, no reverting, no interactive prompts.
- Reuse existing helpers verbatim where they exist: `content_hash()` (`scripts/lib/io.py:347`), `read_managed_index()` (`scripts/lib/rule_index.py:21`), `load_json_file()`/`load_yaml_file()`/`write_atomic()` (`scripts/lib/io.py`), `get_active_providers()` (`scripts/lib/deactivation.py`), `resolve_pipeline_details_dir()` (`scripts/lib/pipelines.py:856`). Do not reimplement any of these.
- Byte-identity invariant: this feature must not change a single byte of any file sync.py already writes today — it only adds a new sidecar file, a new optional config file, and warning log lines.

---

### Task 1: Hash-store and allowlist I/O helpers

**Files:**
- Create: `scripts/lib/generated_file_drift.py`
- Test: `tests/test_generated_file_drift.py`

**Interfaces:**
- Consumes: `content_hash(text: str) -> str` (`scripts/lib/io.py`), `load_json_file(path, *, on_error, default) -> dict` (`scripts/lib/io.py`), `load_yaml_file(path, *, on_error, default) -> dict` (`scripts/lib/io.py`), `write_atomic(path: Path, content: str) -> None` (`scripts/lib/io.py`).
- Produces (for Task 2/3/4): `GENERATED_FILE_HASHES_DIR = ".meta-config"`, `GENERATED_FILE_HASHES_FILE = "generated-file-hashes.json"`, `DRIFT_ALLOWLIST_FILE = "drift-allowlist.yaml"`, `_hashes_path(project_root: Path) -> Path`, `_load_hashes(project_root: Path) -> dict[str, str]`, `_save_hashes(project_root: Path, hashes: dict[str, str], dry_run: bool) -> None`, `_load_allowlist_patterns(project_root: Path) -> list[str]`, `is_allowlisted(rel_path: str, patterns: list[str]) -> bool`, `is_drift_detection_enabled(config: dict) -> bool`.

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for scripts/lib/generated_file_drift.py.

Detects when a sync.py-generated file (anything tracked via
.agent-meta-managed) was manually edited since the last sync, via a
content-hash sidecar store. Warn-only -- write behavior is unaffected.
Spec: docs/superpowers/specs/2026-09-07-generated-file-drift-detection-design.md
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.generated_file_drift import (
    _hashes_path,
    _load_allowlist_patterns,
    _load_hashes,
    _save_hashes,
    is_allowlisted,
    is_drift_detection_enabled,
)


def test_hashes_path_is_meta_config_generated_file_hashes_json(tmp_path: Path) -> None:
    assert _hashes_path(tmp_path) == tmp_path / ".meta-config" / "generated-file-hashes.json"


def test_load_hashes_returns_empty_dict_when_file_absent(tmp_path: Path) -> None:
    assert _load_hashes(tmp_path) == {}


def test_save_then_load_hashes_round_trips(tmp_path: Path) -> None:
    _save_hashes(tmp_path, {".claude/agents/developer.md": "abc123"}, dry_run=False)
    assert _load_hashes(tmp_path) == {".claude/agents/developer.md": "abc123"}


def test_save_hashes_is_noop_in_dry_run(tmp_path: Path) -> None:
    _save_hashes(tmp_path, {"x": "y"}, dry_run=True)
    assert not _hashes_path(tmp_path).exists()


def test_load_hashes_returns_empty_dict_on_malformed_json(tmp_path: Path) -> None:
    path = _hashes_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("not json", encoding="utf-8")
    assert _load_hashes(tmp_path) == {}


def test_load_allowlist_patterns_returns_empty_list_when_file_absent(tmp_path: Path) -> None:
    assert _load_allowlist_patterns(tmp_path) == []


def test_load_allowlist_patterns_reads_yaml_list(tmp_path: Path) -> None:
    meta = tmp_path / ".meta-config"
    meta.mkdir()
    (meta / "drift-allowlist.yaml").write_text(
        "allow-edits:\n  - .claude/commands/my-cmd.md\n  - .opencode/rules/*.md\n",
        encoding="utf-8",
    )
    assert _load_allowlist_patterns(tmp_path) == [
        ".claude/commands/my-cmd.md", ".opencode/rules/*.md",
    ]


def test_is_allowlisted_matches_exact_path() -> None:
    assert is_allowlisted(".claude/commands/my-cmd.md", [".claude/commands/my-cmd.md"])


def test_is_allowlisted_matches_glob() -> None:
    assert is_allowlisted(".opencode/rules/foo.md", [".opencode/rules/*.md"])


def test_is_allowlisted_false_when_no_pattern_matches() -> None:
    assert not is_allowlisted(".claude/agents/developer.md", [".claude/commands/*.md"])


def test_is_allowlisted_false_for_empty_patterns() -> None:
    assert not is_allowlisted(".claude/agents/developer.md", [])


def test_is_drift_detection_enabled_defaults_true_when_key_absent() -> None:
    assert is_drift_detection_enabled({}) is True


def test_is_drift_detection_enabled_false_when_explicitly_disabled() -> None:
    assert is_drift_detection_enabled({"drift-detection": {"enabled": False}}) is False


def test_is_drift_detection_enabled_true_when_explicitly_enabled() -> None:
    assert is_drift_detection_enabled({"drift-detection": {"enabled": True}}) is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_generated_file_drift.py -v -o consider_namespace_packages=true`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.lib.generated_file_drift'` (or `ImportError`).

- [ ] **Step 3: Write the implementation**

```python
"""Generated-file drift detection: warn when a sync.py-owned file
(anything tracked via .agent-meta-managed) was manually edited since the
last sync. Warn-only for this phase -- write behavior is unaffected.

Split into two halves, mirroring context.py's context-hashes.json pattern:
- scan_generated_file_drift() (Task 2): pure, compares current file
  content hashes against the stored baseline, called BEFORE the
  per-provider write stage so it sees pre-overwrite state.
- capture_generated_file_hashes() (Task 3): writes a fresh baseline from
  the now-written files, called AFTER every writer has run.

Spec: docs/superpowers/specs/2026-09-05-generated-file-drift-detection-design.md
"""
from __future__ import annotations

import fnmatch
from pathlib import Path

from .io import load_json_file, load_yaml_file, write_atomic

GENERATED_FILE_HASHES_DIR = ".meta-config"
GENERATED_FILE_HASHES_FILE = "generated-file-hashes.json"
DRIFT_ALLOWLIST_FILE = "drift-allowlist.yaml"


def _hashes_path(project_root: Path) -> Path:
    return project_root / GENERATED_FILE_HASHES_DIR / GENERATED_FILE_HASHES_FILE


def _load_hashes(project_root: Path) -> dict[str, str]:
    """Read the hash-store sidecar; {} if absent or malformed (fail-soft,
    same contract as context.py's _load_context_hashes)."""
    data = load_json_file(_hashes_path(project_root), on_error="default", default={})
    hashes = data.get("hashes") if isinstance(data, dict) else None
    return hashes if isinstance(hashes, dict) else {}


def _save_hashes(project_root: Path, hashes: dict[str, str], dry_run: bool) -> None:
    """Write the hash-store sidecar (no-op in dry_run)."""
    if dry_run:
        return
    path = _hashes_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    import json
    payload = {"version": 1, "hashes": hashes}
    write_atomic(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _allowlist_path(project_root: Path) -> Path:
    return project_root / GENERATED_FILE_HASHES_DIR / DRIFT_ALLOWLIST_FILE


def _load_allowlist_patterns(project_root: Path) -> list[str]:
    """Read .meta-config/drift-allowlist.yaml's `allow-edits` list; []
    if absent or malformed (fail-soft, matching every other optional
    config file in this repo)."""
    data = load_yaml_file(_allowlist_path(project_root), on_error="default", default={})
    patterns = data.get("allow-edits") if isinstance(data, dict) else None
    return [p for p in patterns if isinstance(p, str)] if isinstance(patterns, list) else []


def is_allowlisted(rel_path: str, patterns: list[str]) -> bool:
    """True when rel_path matches any glob pattern in patterns (fnmatch semantics)."""
    return any(fnmatch.fnmatch(rel_path, pattern) for pattern in patterns)


def is_drift_detection_enabled(config: dict) -> bool:
    """True unless project.yaml explicitly sets drift-detection.enabled: false."""
    return bool(config.get("drift-detection", {}).get("enabled", True))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_generated_file_drift.py -v -o consider_namespace_packages=true`
Expected: 14 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/generated_file_drift.py tests/test_generated_file_drift.py
git commit -m "feat: add hash-store and allowlist I/O helpers for generated-file drift detection"
```

---

### Task 2: Managed-file enumeration and drift scan

**Files:**
- Modify: `scripts/lib/generated_file_drift.py` (append)
- Modify: `tests/test_generated_file_drift.py` (append)

**Interfaces:**
- Consumes: everything from Task 1; `read_managed_index(index_path: Path) -> set[str]` (`scripts/lib/rule_index.py`); `resolve_pipeline_details_dir(pc: dict, provider: str) -> str` (`scripts/lib/pipelines.py:856`); `get_active_providers(config: dict, provider_config: dict) -> list[str]` (`scripts/lib/deactivation.py`); `content_hash(text: str) -> str` (`scripts/lib/io.py:347`).
- Produces (for Task 3/4): `_iter_managed_files(agent_meta_root: Path, project_root: Path, provider: str, pc: dict) -> list[Path]` (absolute paths), `scan_generated_file_drift(agent_meta_root: Path, project_root: Path, config: dict, provider_config: dict) -> list[dict]` (each finding: `{"path": str, "provider": str}`, path relative to project_root, POSIX separators).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_generated_file_drift.py`:

```python
from scripts.lib.generated_file_drift import scan_generated_file_drift


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _managed_index(root: Path, dir_rel: str, *names: str) -> None:
    index_path = root / dir_rel / ".agent-meta-managed"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(names) + "\n", encoding="utf-8")


def _provider_config() -> dict:
    return {"Claude": {
        "agents_dir": ".claude/agents", "skills_dir": ".claude/skills",
        "hooks_dir": ".claude/hooks", "rules_dir": ".claude/rules",
        "commands_dir": ".claude/commands",
        "has_hooks": True, "has_rules": True, "has_commands": True,
    }}


def test_scan_flags_agent_file_whose_content_changed_since_last_hash(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "edited by hand")
    _managed_index(project_root, ".claude/agents", "developer.md")
    from scripts.lib.generated_file_drift import content_hash
    _save_hashes(project_root, {".claude/agents/developer.md": content_hash("original content")}, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    paths = [f["path"] for f in findings]
    assert ".claude/agents/developer.md" in paths


def test_scan_does_not_flag_file_with_no_stored_hash_yet(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "brand new")
    _managed_index(project_root, ".claude/agents", "developer.md")

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    assert findings == []


def test_scan_does_not_flag_unchanged_file(tmp_path: Path) -> None:
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "same content")
    _managed_index(project_root, ".claude/agents", "developer.md")
    _save_hashes(project_root, {".claude/agents/developer.md": content_hash("same content")}, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    assert findings == []


def test_scan_respects_allowlist(tmp_path: Path) -> None:
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/commands/my-cmd.md", "edited by hand")
    _managed_index(project_root, ".claude/commands", "my-cmd.md")
    _save_hashes(project_root, {".claude/commands/my-cmd.md": content_hash("original")}, dry_run=False)
    meta = project_root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "drift-allowlist.yaml").write_text(
        "allow-edits:\n  - .claude/commands/*.md\n", encoding="utf-8",
    )

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    assert findings == []


def test_scan_covers_rules_dir_hooks_dir_and_pipeline_details(tmp_path: Path) -> None:
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/rules/branch-guard.md", "edited")
    _managed_index(project_root, ".claude/rules", "branch-guard.md")
    _write(project_root, ".claude/hooks/dod-push-check.sh", "edited")
    _managed_index(project_root, ".claude/hooks", "dod-push-check.sh")
    _write(project_root, ".claude/pipeline-details/bugfix.md", "edited")
    _managed_index(project_root, ".claude/pipeline-details", "bugfix.md")
    _save_hashes(project_root, {
        ".claude/rules/branch-guard.md": content_hash("orig"),
        ".claude/hooks/dod-push-check.sh": content_hash("orig"),
        ".claude/pipeline-details/bugfix.md": content_hash("orig"),
    }, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    paths = {f["path"] for f in findings}
    assert paths == {
        ".claude/rules/branch-guard.md",
        ".claude/hooks/dod-push-check.sh",
        ".claude/pipeline-details/bugfix.md",
    }


def test_scan_covers_nested_managed_subdirs(tmp_path: Path) -> None:
    """hooks/lib/ and hooks/release-gates/ carry their OWN .agent-meta-managed
    index (issue #558) -- must be recursed into, not just the top-level hooks/."""
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/hooks/lib/hook_common.sh", "edited")
    _managed_index(project_root, ".claude/hooks/lib", "hook_common.sh")
    _managed_index(project_root, ".claude/hooks")  # empty top-level index
    _save_hashes(project_root, {".claude/hooks/lib/hook_common.sh": content_hash("orig")}, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    paths = {f["path"] for f in findings}
    assert ".claude/hooks/lib/hook_common.sh" in paths


def test_scan_unions_rules_sidecar_indexes(tmp_path: Path) -> None:
    """rules/ has THREE index files (.agent-meta-managed, -mcp, -tools) for
    three different writers -- all three contribute managed filenames."""
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/rules/mcp-honcho.md", "edited")
    (project_root / ".claude" / "rules").mkdir(parents=True, exist_ok=True)
    (project_root / ".claude" / "rules" / ".agent-meta-managed").write_text("", encoding="utf-8")
    (project_root / ".claude" / "rules" / ".agent-meta-managed-mcp").write_text("mcp-honcho.md\n", encoding="utf-8")
    _save_hashes(project_root, {".claude/rules/mcp-honcho.md": content_hash("orig")}, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    paths = {f["path"] for f in findings}
    assert ".claude/rules/mcp-honcho.md" in paths


def test_scan_only_covers_active_providers(tmp_path: Path) -> None:
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".gemini/agents/developer.md", "edited")
    _managed_index(project_root, ".gemini/agents", "developer.md")
    _save_hashes(project_root, {".gemini/agents/developer.md": content_hash("orig")}, dry_run=False)

    provider_config = {
        "Claude": _provider_config()["Claude"],
        "Gemini": {"agents_dir": ".gemini/agents", "skills_dir": ".gemini/skills"},
    }
    # config has no "ai-providers" key -> resolve_providers() defaults to
    # ["Claude"] only (see scripts/lib/providers.py) -- Gemini is not active.
    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, provider_config)
    assert findings == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_generated_file_drift.py -v -o consider_namespace_packages=true`
Expected: the 8 new tests FAIL with `ImportError: cannot import name 'scan_generated_file_drift'`.

- [ ] **Step 3: Write the implementation**

Append to `scripts/lib/generated_file_drift.py`:

```python
from .deactivation import get_active_providers
from .io import content_hash
from .pipelines import resolve_pipeline_details_dir
from .rule_index import read_managed_index


def _managed_names(dir_path: Path, *extra_index_names: str) -> set[str]:
    """Union of every managed-index file's entries for dir_path.

    A directory can carry more than one index (rules/ has
    .agent-meta-managed, -mcp, -tools -- one per writer, issue #478/#613);
    extra_index_names lists the sidecar suffixes beyond the base
    .agent-meta-managed.
    """
    names = read_managed_index(dir_path / ".agent-meta-managed")
    for suffix in extra_index_names:
        names |= read_managed_index(dir_path / f".agent-meta-managed-{suffix}")
    return names


def _iter_managed_files(agent_meta_root: Path, project_root: Path, provider: str, pc: dict) -> list[Path]:
    """Absolute paths of every file this provider's writers track via a
    .agent-meta-managed index (or its -mcp/-tools sidecars), across
    agents/rules/hooks(+lib+release-gates)/commands/skills/pipeline-details.

    Default literal fallbacks (".claude/hooks" etc.) mirror the same
    established pattern in scan_injection_drift()
    (scripts/lib/external_tools_drift.py) -- correct today because only
    Claude omits these keys from ai-providers.yaml while having the
    capability; any provider without the capability flag never reaches
    the fallback at all.
    """
    files: list[Path] = []

    dir_specs: list[tuple[str, list[str]]] = [
        (pc.get("skills_dir", ".claude/skills"), []),
        (pc.get("agents_dir", ".claude/agents"), []),
    ]
    if pc.get("has_hooks", False):
        dir_specs.append((pc.get("hooks_dir", ".claude/hooks"), []))
    if pc.get("has_rules", False):
        dir_specs.append((pc.get("rules_dir", ".claude/rules"), ["mcp", "tools"]))
    if pc.get("has_commands", False):
        dir_specs.append((pc.get("commands_dir", ".claude/commands"), []))
    dir_specs.append((resolve_pipeline_details_dir(pc, provider), []))

    for dir_rel, extra_index_names in dir_specs:
        dir_path = project_root / dir_rel
        if not dir_path.is_dir():
            continue
        for name in sorted(_managed_names(dir_path, *extra_index_names)):
            candidate = dir_path / name
            if candidate.is_file():
                files.append(candidate)
        # Nested self-managed subdirectories (hooks/lib/, hooks/release-gates/,
        # issue #558) carry their OWN .agent-meta-managed index -- recurse
        # one level to pick those up too (mirrors scan_injection_drift's
        # "child.is_dir() and (child / '.agent-meta-managed').exists()" check).
        for child in sorted(dir_path.iterdir()):
            if child.is_dir() and (child / ".agent-meta-managed").exists():
                for name in sorted(_managed_names(child)):
                    nested_candidate = child / name
                    if nested_candidate.is_file():
                        files.append(nested_candidate)

    return files


def scan_generated_file_drift(
    agent_meta_root: Path, project_root: Path, config: dict, provider_config: dict,
) -> list[dict]:
    """Compare every active provider's managed files against the stored
    hash baseline. Pure -- no writes, no warnings emitted (the caller,
    the sync_pipeline stage, turns findings into log.warning() calls).

    A file with no stored hash yet (first sync, or newly added to a
    managed index) is never a finding -- there is nothing to compare
    against yet.
    """
    stored_hashes = _load_hashes(project_root)
    allowlist = _load_allowlist_patterns(project_root)
    active_providers = set(get_active_providers(config, provider_config))

    findings: list[dict] = []
    for provider, pc in provider_config.items():
        if provider not in active_providers:
            continue
        for abs_path in _iter_managed_files(agent_meta_root, project_root, provider, pc):
            rel_path = abs_path.relative_to(project_root).as_posix()
            stored = stored_hashes.get(rel_path)
            if stored is None:
                continue
            current = content_hash(abs_path.read_text(encoding="utf-8"))
            if current == stored:
                continue
            if is_allowlisted(rel_path, allowlist):
                continue
            findings.append({"path": rel_path, "provider": provider})

    return findings
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_generated_file_drift.py -v -o consider_namespace_packages=true`
Expected: 22 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/generated_file_drift.py tests/test_generated_file_drift.py
git commit -m "feat: add scan_generated_file_drift() managed-file content-hash comparison"
```

---

### Task 3: Hash-baseline capture

**Files:**
- Modify: `scripts/lib/generated_file_drift.py` (append)
- Modify: `tests/test_generated_file_drift.py` (append)

**Interfaces:**
- Consumes: `_iter_managed_files` and `_save_hashes` from Task 1/2.
- Produces (for Task 4): `capture_generated_file_hashes(agent_meta_root: Path, project_root: Path, config: dict, provider_config: dict, dry_run: bool) -> None`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_generated_file_drift.py`:

```python
from scripts.lib.generated_file_drift import capture_generated_file_hashes, content_hash


def test_capture_writes_hash_for_every_managed_file(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "fresh content")
    _managed_index(project_root, ".claude/agents", "developer.md")

    capture_generated_file_hashes(tmp_path / "agent-meta", project_root, {}, _provider_config(), dry_run=False)

    assert _load_hashes(project_root) == {
        ".claude/agents/developer.md": content_hash("fresh content"),
    }


def test_capture_is_noop_in_dry_run(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "fresh content")
    _managed_index(project_root, ".claude/agents", "developer.md")

    capture_generated_file_hashes(tmp_path / "agent-meta", project_root, {}, _provider_config(), dry_run=True)

    assert _load_hashes(project_root) == {}


def test_capture_then_scan_round_trip_finds_no_drift(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "content v1")
    _managed_index(project_root, ".claude/agents", "developer.md")

    capture_generated_file_hashes(tmp_path / "agent-meta", project_root, {}, _provider_config(), dry_run=False)
    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())

    assert findings == []


def test_capture_overwrites_stale_hash_for_regenerated_content(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "content v1")
    _managed_index(project_root, ".claude/agents", "developer.md")
    _save_hashes(project_root, {".claude/agents/developer.md": content_hash("stale")}, dry_run=False)

    capture_generated_file_hashes(tmp_path / "agent-meta", project_root, {}, _provider_config(), dry_run=False)

    assert _load_hashes(project_root) == {
        ".claude/agents/developer.md": content_hash("content v1"),
    }
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_generated_file_drift.py -v -o consider_namespace_packages=true`
Expected: the 4 new tests FAIL with `ImportError: cannot import name 'capture_generated_file_hashes'`.

- [ ] **Step 3: Write the implementation**

Append to `scripts/lib/generated_file_drift.py`:

```python
def capture_generated_file_hashes(
    agent_meta_root: Path, project_root: Path, config: dict, provider_config: dict, dry_run: bool,
) -> None:
    """Recompute and persist the complete hash baseline from the CURRENT
    on-disk state of every active provider's managed files. Called once,
    at the very end of the sync pipeline, after every writer has run --
    the on-disk content at this point is exactly what the next sync's
    scan_generated_file_drift() call should compare against.
    """
    active_providers = set(get_active_providers(config, provider_config))
    hashes: dict[str, str] = {}
    for provider, pc in provider_config.items():
        if provider not in active_providers:
            continue
        for abs_path in _iter_managed_files(agent_meta_root, project_root, provider, pc):
            rel_path = abs_path.relative_to(project_root).as_posix()
            hashes[rel_path] = content_hash(abs_path.read_text(encoding="utf-8"))
    _save_hashes(project_root, hashes, dry_run)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_generated_file_drift.py -v -o consider_namespace_packages=true`
Expected: 26 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/generated_file_drift.py tests/test_generated_file_drift.py
git commit -m "feat: add capture_generated_file_hashes() baseline writer"
```

---

### Task 4: Wire into the sync pipeline

**Files:**
- Modify: `scripts/lib/sync_pipeline.py`
- Modify: `scripts/lib/cli_commands.py`
- Modify: `templates/configs/project.yaml.example` (document the new keys)
- Test: `tests/test_generated_file_drift_pipeline_wiring.py`

**Interfaces:**
- Consumes: `scan_generated_file_drift`, `capture_generated_file_hashes`, `is_drift_detection_enabled` (Tasks 1-3).
- Produces: `_sync_stage_generated_file_drift_scan(agent_meta_root: Path, project_root: Path, config: dict, provider_config: dict, args: argparse.Namespace, log: SyncLog) -> None`, `_sync_stage_generated_file_hash_capture(agent_meta_root: Path, project_root: Path, config: dict, provider_config: dict, args: argparse.Namespace, log: SyncLog) -> None` (both in `scripts/lib/sync_pipeline.py`).

- [ ] **Step 1: Write the failing test**

Create `tests/test_generated_file_drift_pipeline_wiring.py`:

```python
"""Integration test: the two generated-file-drift stages are wired into
_handle_sync in the right order relative to _sync_stage_per_provider (the
stage that does all the actual overwriting) -- see
docs/superpowers/specs/2026-09-07-generated-file-drift-detection-design.md
("early scan before overwrite, late capture after everything is written").
"""
from __future__ import annotations

import inspect

from scripts.lib import cli_commands


def test_drift_scan_stage_runs_before_per_provider_write_stage() -> None:
    source = inspect.getsource(cli_commands._handle_sync)
    scan_pos = source.index("_sync_stage_generated_file_drift_scan(")
    per_provider_pos = source.index("_sync_stage_per_provider(")
    assert scan_pos < per_provider_pos, (
        "the drift-scan stage must run BEFORE _sync_stage_per_provider "
        "overwrites anything, or it can never see a manual edit"
    )


def test_hash_capture_stage_runs_after_every_other_stage() -> None:
    source = inspect.getsource(cli_commands._handle_sync)
    capture_pos = source.index("_sync_stage_generated_file_hash_capture(")
    other_stage_calls = [
        "_sync_stage_per_provider(", "_sync_stage_drift_and_plugins(",
        "_sync_stage_knowledge_and_isolation(", "_sync_stage_gitignore(",
        "_sync_stage_config_audit(",
    ]
    for call in other_stage_calls:
        assert capture_pos > source.index(call), (
            f"hash-capture must run after {call} so it captures fully "
            "post-write state"
        )


def _write(root, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_drift_scan_stage_skips_and_warns_nothing_when_disabled(tmp_path) -> None:
    from scripts.lib.log import SyncLog
    from scripts.lib.sync_pipeline import _sync_stage_generated_file_drift_scan
    import argparse

    project_root = tmp_path / "project"
    from scripts.lib.generated_file_drift import content_hash
    _write(project_root, ".claude/agents/developer.md", "edited by hand")
    index_path = project_root / ".claude" / "agents" / ".agent-meta-managed"
    index_path.write_text("developer.md\n", encoding="utf-8")
    hashes_path = project_root / ".meta-config" / "generated-file-hashes.json"
    hashes_path.parent.mkdir(parents=True, exist_ok=True)
    hashes_path.write_text(
        '{"version": 1, "hashes": {".claude/agents/developer.md": "' + content_hash("original") + '"}}',
        encoding="utf-8",
    )
    provider_config = {"Claude": {"agents_dir": ".claude/agents", "skills_dir": ".claude/skills"}}
    log = SyncLog()
    args = argparse.Namespace(dry_run=False)

    _sync_stage_generated_file_drift_scan(
        tmp_path / "agent-meta", project_root, {"drift-detection": {"enabled": False}},
        provider_config, args, log,
    )

    assert log.warnings == []


def test_hash_capture_stage_writes_nothing_when_disabled(tmp_path) -> None:
    from scripts.lib.log import SyncLog
    from scripts.lib.sync_pipeline import _sync_stage_generated_file_hash_capture
    import argparse

    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "fresh content")
    index_path = project_root / ".claude" / "agents" / ".agent-meta-managed"
    index_path.write_text("developer.md\n", encoding="utf-8")
    provider_config = {"Claude": {"agents_dir": ".claude/agents", "skills_dir": ".claude/skills"}}
    log = SyncLog()
    args = argparse.Namespace(dry_run=False)

    _sync_stage_generated_file_hash_capture(
        tmp_path / "agent-meta", project_root, {"drift-detection": {"enabled": False}},
        provider_config, args, log,
    )

    assert not (project_root / ".meta-config" / "generated-file-hashes.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_generated_file_drift_pipeline_wiring.py -v -o consider_namespace_packages=true`
Expected: FAIL with `ValueError: substring not found` (the stage names don't exist in `_handle_sync` yet) for the first two tests, and `ImportError: cannot import name '_sync_stage_generated_file_drift_scan'` for the two new ones.

- [ ] **Step 3: Implement the wiring**

In `scripts/lib/sync_pipeline.py`, add near the top of the imports section:

```python
from lib.generated_file_drift import (
    capture_generated_file_hashes,
    is_drift_detection_enabled,
    scan_generated_file_drift,
)
```

Then add these two functions right after `_sync_stage_legacy_cleanup` (before `_sync_stage_per_provider`):

```python
def _sync_stage_generated_file_drift_scan(
    agent_meta_root: Path, project_root: Path, config: dict,
    provider_config: dict, args: argparse.Namespace, log: SyncLog,
) -> None:
    """Early drift scan -- runs BEFORE _sync_stage_per_provider overwrites
    anything, so it can still see a manual edit made since the last sync.
    Warn-only: never changes what gets written (issue: user feature
    request, 2026-09-07, spec in docs/superpowers/specs/)."""
    if not is_drift_detection_enabled(config):
        log.skip("generated-file-drift-scan", "disabled (drift-detection.enabled: false)")
        return
    findings = scan_generated_file_drift(agent_meta_root, project_root, config, provider_config)
    for finding in findings:
        log.warning(
            f"generated-file-drift: '{finding['path']}' was manually edited "
            f"since the last sync (provider '{finding['provider']}') -- this "
            "sync will overwrite it. Add it to .meta-config/drift-allowlist.yaml "
            "if this edit should be preserved going forward."
        )
```

Then add this function right after `_sync_stage_config_audit` (as the very last stage function in the file):

```python
def _sync_stage_generated_file_hash_capture(
    agent_meta_root: Path, project_root: Path, config: dict,
    provider_config: dict, args: argparse.Namespace, log: SyncLog,
) -> None:
    """Late hash-baseline capture -- runs after every writer has run, so
    it captures the fully post-write on-disk state for the NEXT sync's
    drift scan to compare against."""
    if not is_drift_detection_enabled(config):
        return
    capture_generated_file_hashes(agent_meta_root, project_root, config, provider_config, args.dry_run)
```

In `scripts/lib/cli_commands.py`, add the two new names to the existing `from lib.sync_pipeline import (...)` block (keep the list alphabetically sorted, matching the existing style):

```python
    _sync_stage_claude_base,
    _sync_stage_config_and_presets,
    _sync_stage_config_audit,
    _sync_stage_contexts,
    _sync_stage_drift_and_plugins,
    _sync_stage_external_skills_check,
    _sync_stage_generated_file_drift_scan,
    _sync_stage_generated_file_hash_capture,
    _sync_stage_gitignore,
    _sync_stage_knowledge_and_isolation,
    _sync_stage_legacy_cleanup,
    _sync_stage_per_provider,
```

Then in `_handle_sync`, insert the early-scan call between the existing `_sync_stage_legacy_cleanup(...)` call and the `_sync_stage_per_provider(...)` call:

```python
    # Stage 5: legacy-provider cleanup.
    _sync_stage_legacy_cleanup(ctx.project_root, config, provider_config,
                               providers, ctx.args, ctx.log)
    # Stage 5b: generated-file drift scan -- MUST run before stage 6
    # overwrites anything (see docs/superpowers/specs/2026-09-07-generated-file-drift-detection-design.md).
    _sync_stage_generated_file_drift_scan(ctx.agent_meta_root, ctx.project_root,
                                          config, provider_config, ctx.args, ctx.log)
    # Stage 6: per-provider main loop; mcp_gitignore_extras crosses the
    # stage boundary by reference.
    _sync_stage_per_provider(ctx.agent_meta_root, ctx.project_root, config,
                             provider_config, providers, ctx.variables,
                             platform_vars, debug_mode, allow_committed_secrets,
                             mcp_gitignore_extras, ctx.args, ctx.log)
```

And insert the late-capture call as the very last statement before `ctx.config = config`:

```python
    # Stage 12: lightweight config-audit summary.
    _sync_stage_config_audit(ctx.agent_meta_root, ctx.config_path, ctx.log)
    # Stage 13: generated-file hash-baseline capture -- MUST run last, after
    # every writer above, so it captures fully post-write state.
    _sync_stage_generated_file_hash_capture(ctx.agent_meta_root, ctx.project_root,
                                            config, provider_config, ctx.args, ctx.log)

    ctx.config = config
    ctx.mode = mode
```

In `templates/configs/project.yaml.example`, add documentation for the new keys near the `allow-committed-secrets` comment block:

```yaml
# Generated-file drift detection (default: enabled) — warns when a
# sync.py-generated file (agent/rule/hook/command/skill/pipeline-detail)
# was manually edited since the last sync. Warn-only: the file is still
# regenerated as usual. Paths where manual edits are expected go in
# .meta-config/drift-allowlist.yaml (allow-edits: list of glob patterns
# against the deployed path, e.g. ".claude/commands/my-cmd.md").
# drift-detection:
#   enabled: false
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_generated_file_drift_pipeline_wiring.py -v -o consider_namespace_packages=true`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/sync_pipeline.py scripts/lib/cli_commands.py templates/configs/project.yaml.example tests/test_generated_file_drift_pipeline_wiring.py
git commit -m "feat: wire generated-file drift scan + hash capture into sync pipeline"
```

---

### Task 5: End-to-end verification and full test suite

**Files:**
- Test: `tests/test_generated_file_drift_e2e.py`

**Interfaces:**
- Consumes: `scripts.sync` CLI entry point (invoked as a subprocess, same pattern as `tests/test_harness_sync_guard.py`), everything from Tasks 1-4.

- [ ] **Step 1: Write the failing test**

Create `tests/test_generated_file_drift_e2e.py`:

```python
"""End-to-end: a real `python scripts/sync.py` run detects a manual edit
made between two syncs, warns about it, and a subsequent sync with the
edited path allowlisted produces no warning."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SYNC_PY = _REPO_ROOT / "scripts" / "sync.py"


def _run_sync(project_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SYNC_PY), "--config", str(project_root / ".meta-config" / "project.yaml")],
        capture_output=True, text=True, cwd=str(project_root),
    )


def _write_minimal_project_yaml(project_root: Path) -> None:
    meta = project_root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "project.yaml").write_text(
        "ai-providers: [Claude]\n"
        "dod-preset: rapid-prototyping\n"
        "roles: [developer]\n"
        "project: {name: e2e-drift-test, prefix: e2e, short: e2e-drift}\n"
        "variables: {PROJECT_NAME: e2e-drift-test}\n",
        encoding="utf-8",
    )


def test_manual_edit_produces_warning_on_next_sync(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write_minimal_project_yaml(project_root)

    first = _run_sync(project_root)
    assert first.returncode == 0, first.stderr

    developer_md = project_root / ".claude" / "agents" / "developer.md"
    assert developer_md.is_file()
    developer_md.write_text(developer_md.read_text(encoding="utf-8") + "\n<!-- hand edit -->\n", encoding="utf-8")

    second = _run_sync(project_root)
    assert "generated-file-drift" in second.stderr, second.stderr
    assert ".claude/agents/developer.md" in second.stderr


def test_allowlisted_edit_produces_no_warning(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write_minimal_project_yaml(project_root)
    _run_sync(project_root)

    developer_md = project_root / ".claude" / "agents" / "developer.md"
    developer_md.write_text(developer_md.read_text(encoding="utf-8") + "\n<!-- hand edit -->\n", encoding="utf-8")

    meta = project_root / ".meta-config"
    (meta / "drift-allowlist.yaml").write_text(
        "allow-edits:\n  - .claude/agents/developer.md\n", encoding="utf-8",
    )

    second = _run_sync(project_root)
    assert "generated-file-drift" not in second.stderr, second.stderr
```

- [ ] **Step 2: Run tests to verify they fail (or pass for the wrong reason)**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_generated_file_drift_e2e.py -v -o consider_namespace_packages=true`
Expected: without Tasks 1-4 these would fail (no drift warning ever appears); with Tasks 1-4 already implemented in this same plan run, this should already PASS at this point — this task is a verification checkpoint, not new production code.

- [ ] **Step 3: If either test fails, fix the wiring from Task 4** (no new production code is expected here — if a test fails, re-check the stage insertion points and `is_drift_detection_enabled` wiring from Task 4 before writing any new code)

- [ ] **Step 4: Run the full test suite**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q -o consider_namespace_packages=true`
Expected: all tests pass, including the pre-existing suite (no regressions). Also run `python3 scripts/consistency-check.py` and confirm exit code 0.

**Known side effect to check for and revert before committing:** running the full suite has previously stripped 2 comment lines each from `.meta-config/project.yaml` and `config/tier-presets.yaml` (a test-isolation gap unrelated to this feature). Run `git diff -- .meta-config/project.yaml config/tier-presets.yaml` — if it shows only comment-line deletions, run `git checkout -- .meta-config/project.yaml config/tier-presets.yaml` before staging anything.

- [ ] **Step 5: Run a real sync against this repo itself**

Run: `python3 scripts/sync.py`
Expected: exits 0, and (since agent-meta's own `.meta-config/project.yaml` sets no `drift-detection` key, so the new feature defaults to enabled) a brand-new `.meta-config/generated-file-hashes.json` appears — this is agent-meta's own repo getting its first-ever baseline for this feature, expected and correct, not a bug. No `generated-file-drift` warnings should appear on this first run (there is no prior baseline yet for any file, so nothing can be flagged as drifted — see the "no stored hash yet -> never a finding" rule from Task 2). Run `git status --short` and confirm only `.meta-config/generated-file-hashes.json` is new/untracked, plus the two known side-effect files from Step 4 if the pytest run happened first (revert those the same way).

- [ ] **Step 6: Commit**

```bash
git add tests/test_generated_file_drift_e2e.py .meta-config/generated-file-hashes.json
git commit -m "test: add end-to-end verification for generated-file drift detection"
```
