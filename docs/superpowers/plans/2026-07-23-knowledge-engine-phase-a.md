# Knowledge Engine Phase A — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the zero-overhead activation mechanism and idempotent bundle-scaffolding for the Knowledge Engine (Phase A), reusing the existing `systems-engineering` cascade pattern — no agent templates, no AdminUI, just the config flag, variables, scaffolding module and sync phase.

**Architecture:** A new `knowledge-engine:` config block drives three additions: (1) a `knowledge-` prefix branch in `_is_role_enabled()`, (2) three derived `KNOWLEDGE_*` variables in `build_variables()`, and (3) a new sync phase `sync_knowledge_engine()` that scaffolds a `knowledge/` bundle (schema.md, wiki/index.md, wiki/log.md, empty subdirs with `.gitkeep`) the first time it runs, then only tops up missing `.gitkeep` markers on every subsequent run.

**Tech Stack:** Python 3.x stdlib only (pathlib, no new dependencies), pytest for tests, YAML config via existing `lib/io.py` helpers.

## Global Constraints

- No new Python dependencies beyond stdlib (project convention: `Keine externen Python-Dependencies außer Stdlib`).
- `knowledge-engine.enabled` defaults to `false` — every existing project must see zero output/behavior change (Zero-Overhead-Garantie, spec line 104).
- Domain enum is exactly `research | personal | business | book | custom` (spec line 34) — no other values.
- Bundle scaffolding is idempotent: never overwrite `schema.md`, `wiki/index.md`, `wiki/log.md` once they exist (spec line 120).
- No `KNOWLEDGE_SCHEMA_PATH` / `KNOWLEDGE_WIKI_DIR` / `KNOWLEDGE_SOURCES_DIR` / `KNOWLEDGE_CONCEPT_TYPES` variables in Phase A (spec line 70) — only `KNOWLEDGE_ENGINE_ENABLED`, `KNOWLEDGE_DOMAIN`, `KNOWLEDGE_BUNDLE_PATH`.
- No `detect_target_repo()`, no migration logic, no 7 `knowledge-*` agents, no AdminUI — all deferred to Phase B/C/D (spec lines 98, 157-162).
- Commit messages: Conventional Commits, imperative mood, English description, max 72 chars first line, **no REQ-ID** (this project has `req-traceability: false`), type `feat` for new capability.
- Every mutating git command (`git add`, `git commit`, etc.) must go through the `git` agent per `use-orchestrator.md` — do not run them directly from the main chat/worker.

---

## File Structure

| File | Responsibility |
|---|---|
| `scripts/lib/knowledge.py` (new) | `DOMAIN_CONCEPT_TYPES` map, `generate_schema()`, `generate_initial_index()`, `generate_initial_log()` — pure string-rendering, no I/O side effects beyond reading the template. |
| `templates/knowledge-schema.template.md` (new) | Single generic schema template with `{{KNOWLEDGE_DOMAIN}}` / `{{KNOWLEDGE_CONCEPT_TYPES}}` placeholders. |
| `scripts/lib/agents.py` (modify) | `_is_role_enabled()` gets a `knowledge-` branch, analogous to the existing `se-` branch. |
| `scripts/lib/config.py` (modify) | `build_variables()` gets 3 new `KNOWLEDGE_*` entries, injected right after the existing SE block. |
| `scripts/sync.py` (modify) | New `sync_knowledge_engine()` function (Phase 2.5) + call site between the per-provider loop and provider-isolation. |
| `config/project-config.schema.json` (modify) | New `knowledge-engine` property (enabled/domain/bundle-path). |
| `.meta-config/project.yaml` (modify) | New `knowledge-engine: {enabled: false, ...}` block (this repo self-hosts its own generated config). |
| `tests/test_knowledge_engine.py` (new) | Unit tests: `generate_schema()` per domain, `generate_initial_index/log()`, `_is_role_enabled()` knowledge branch, `build_variables()` KE vars, schema JSON validity. |
| `tests/test_knowledge_sync_integration.py` (new) | Integration tests: scaffolding on fresh bundle, idempotency on second run, zero-overhead regression when disabled, error cases (bad domain, bundle-path is a file). |

---

### Task 1: `scripts/lib/knowledge.py` + `templates/knowledge-schema.template.md`

**Files:**
- Create: `scripts/lib/knowledge.py`
- Create: `templates/knowledge-schema.template.md`
- Test: `tests/test_knowledge_engine.py`

**Interfaces:**
- Produces: `DOMAIN_CONCEPT_TYPES: dict[str, list[str]]`, `generate_schema(domain: str, bundle_path: str, agent_meta_root: Path) -> str` (raises `ValueError` for unknown domain), `generate_initial_index() -> str`, `generate_initial_log() -> str`.
- Consumes: nothing from other tasks (foundation module).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_knowledge_engine.py`:

```python
"""Tests for scripts/lib/knowledge.py — Knowledge Engine Phase A scaffolding helpers."""
from pathlib import Path

import pytest

from scripts.lib.knowledge import (
    DOMAIN_CONCEPT_TYPES,
    generate_schema,
    generate_initial_index,
    generate_initial_log,
)

_AGENT_META_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# DOMAIN_CONCEPT_TYPES
# ---------------------------------------------------------------------------

def test_domain_concept_types_has_all_five_domains():
    assert set(DOMAIN_CONCEPT_TYPES.keys()) == {
        "research", "personal", "business", "book", "custom",
    }


def test_domain_concept_types_values_are_nonempty_lists():
    for domain, types in DOMAIN_CONCEPT_TYPES.items():
        assert isinstance(types, list)
        assert len(types) >= 1
        for t in types:
            assert isinstance(t, str)


# ---------------------------------------------------------------------------
# generate_schema() — one case per domain
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("domain", ["research", "personal", "business", "book", "custom"])
def test_generate_schema_renders_domain_and_concept_types(domain):
    rendered = generate_schema(domain, "knowledge", _AGENT_META_ROOT)
    assert domain in rendered
    for concept_type in DOMAIN_CONCEPT_TYPES[domain]:
        assert f"- {concept_type}" in rendered
    assert "{{KNOWLEDGE_DOMAIN}}" not in rendered
    assert "{{KNOWLEDGE_CONCEPT_TYPES}}" not in rendered


def test_generate_schema_unknown_domain_raises_value_error():
    with pytest.raises(ValueError, match="Unknown knowledge-engine domain"):
        generate_schema("nonexistent-domain", "knowledge", _AGENT_META_ROOT)


# ---------------------------------------------------------------------------
# generate_initial_index() / generate_initial_log()
# ---------------------------------------------------------------------------

def test_generate_initial_index_has_expected_sections():
    content = generate_initial_index()
    assert "# Knowledge Index" in content
    assert "## Concepts" in content
    assert "## Entities" in content
    assert "## Topics" in content


def test_generate_initial_log_has_expected_sections():
    content = generate_initial_log()
    assert "# Knowledge Log" in content
    assert "## Format" in content
    assert "## Entries" in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_knowledge_engine.py -v`
Expected: `ModuleNotFoundError: No module named 'scripts.lib.knowledge'` (or ImportError) — module does not exist yet.

- [ ] **Step 3: Write the template file**

Create `templates/knowledge-schema.template.md`:

```markdown
# Knowledge Schema — {{KNOWLEDGE_DOMAIN}}

> Generated by agent-meta knowledge-engine. Defines the concept types available
> in this knowledge bundle. Not automatically regenerated on domain change —
> see sync.py log output for a warning if the domain was switched after this
> file was first created.

## Domain

`{{KNOWLEDGE_DOMAIN}}`

## Concept Types

{{KNOWLEDGE_CONCEPT_TYPES}}

## Usage

Each concept type above maps to a Markdown file under `wiki/concepts/<type>/`.
Entities, topics and sources are tracked separately under `wiki/entities/`,
`wiki/topics/` and `wiki/sources/`. `wiki/index.md` is the entry point;
`wiki/log.md` is the append-only change log.
```

- [ ] **Step 4: Write the implementation**

Create `scripts/lib/knowledge.py`:

```python
"""Knowledge Engine Phase A — bundle scaffolding helpers.

Pure rendering functions only. No filesystem writes happen here — callers
(sync_knowledge_engine() in scripts/sync.py) own all I/O and idempotency
decisions.
"""

from pathlib import Path

DOMAIN_CONCEPT_TYPES: dict[str, list[str]] = {
    "research": ["paper", "finding", "method", "dataset"],
    "personal": ["person", "event", "place", "memory"],
    "business": ["customer", "deal", "product", "decision"],
    "book": ["character", "location", "theme", "chapter"],
    "custom": ["concept"],
}

_TEMPLATE_REL_PATH = ("templates", "knowledge-schema.template.md")


def generate_schema(domain: str, bundle_path: str, agent_meta_root: Path) -> str:
    """Render knowledge-schema.template.md for the given domain.

    Raises ValueError when domain is not a key of DOMAIN_CONCEPT_TYPES —
    callers must treat this as a hard sync error (SyncError), not a silent
    fallback, per the Phase A error-handling contract.
    """
    if domain not in DOMAIN_CONCEPT_TYPES:
        raise ValueError(
            f"Unknown knowledge-engine domain '{domain}' — must be one of: "
            + ", ".join(sorted(DOMAIN_CONCEPT_TYPES))
        )
    template_path = agent_meta_root.joinpath(*_TEMPLATE_REL_PATH)
    template = template_path.read_text(encoding="utf-8")
    concept_list = "\n".join(f"- {c}" for c in DOMAIN_CONCEPT_TYPES[domain])
    return (
        template
        .replace("{{KNOWLEDGE_DOMAIN}}", domain)
        .replace("{{KNOWLEDGE_CONCEPT_TYPES}}", concept_list)
    )


def generate_initial_index() -> str:
    """Render the empty index.md skeleton for a freshly scaffolded bundle."""
    return (
        "# Knowledge Index\n\n"
        "> Auto-maintained entry point into the knowledge bundle. Lists all "
        "concepts, entities and topics as they are added.\n\n"
        "## Concepts\n\n"
        "(none yet)\n\n"
        "## Entities\n\n"
        "(none yet)\n\n"
        "## Topics\n\n"
        "(none yet)\n"
    )


def generate_initial_log() -> str:
    """Render the empty log.md skeleton with header + format documentation."""
    return (
        "# Knowledge Log\n\n"
        "> Append-only change log for the knowledge bundle. One entry per "
        "ingest/update/query operation.\n\n"
        "## Format\n\n"
        "```\n"
        "YYYY-MM-DD HH:MM — <operation> — <summary>\n"
        "```\n\n"
        "## Entries\n\n"
        "(none yet)\n"
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_knowledge_engine.py -v`
Expected: all 8 tests `PASS`.

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/knowledge.py templates/knowledge-schema.template.md tests/test_knowledge_engine.py
git commit -m "feat: add knowledge-engine schema/index/log generators"
```

---

### Task 2: `_is_role_enabled()` knowledge- branch

**Files:**
- Modify: `scripts/lib/agents.py:393-398`
- Test: `tests/test_knowledge_engine.py` (append)

**Interfaces:**
- Consumes: nothing new.
- Produces: `_is_role_enabled("knowledge-x", config)` returns `False` when `config.get("knowledge-engine", {}).get("enabled")` is falsy/absent, `True` when explicitly `true`. Existing `se-` behavior and the `True` default for all other roles are unchanged.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_knowledge_engine.py`:

```python
from scripts.lib.agents import _is_role_enabled


# ---------------------------------------------------------------------------
# _is_role_enabled() — knowledge- prefix branch
# ---------------------------------------------------------------------------

def test_knowledge_role_enabled_when_config_true():
    config = {"knowledge-engine": {"enabled": True}}
    assert _is_role_enabled("knowledge-curator", config) is True


def test_knowledge_role_disabled_when_config_false():
    config = {"knowledge-engine": {"enabled": False}}
    assert _is_role_enabled("knowledge-curator", config) is False


def test_knowledge_role_disabled_when_config_missing():
    assert _is_role_enabled("knowledge-curator", {}) is False


def test_knowledge_role_disabled_when_block_present_but_empty():
    assert _is_role_enabled("knowledge-curator", {"knowledge-engine": {}}) is False


def test_se_role_still_defaults_to_enabled_unaffected():
    """Regression: existing se- behavior must not change."""
    assert _is_role_enabled("se-architect", {}) is True


def test_non_prefixed_role_always_enabled():
    """Regression: roles without se-/knowledge- prefix are unaffected."""
    assert _is_role_enabled("developer", {"knowledge-engine": {"enabled": False}}) is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_knowledge_engine.py -k knowledge_role -v`
Expected: FAIL — `knowledge-curator` returns `True` (falls through to the final `return True`), not `False`.

- [ ] **Step 3: Write the implementation**

Edit `scripts/lib/agents.py:393-398`:

```python
def _is_role_enabled(role: str, config: dict) -> bool:
    """Check if a role is enabled based on project config (e.g. systems-engineering flag)."""
    if role.startswith("se-"):
        se_config = config.get("systems-engineering") or {}
        return se_config.get("enabled", True)
    if role.startswith("knowledge-"):
        ke_config = config.get("knowledge-engine") or {}
        return ke_config.get("enabled", False)
    return True
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_knowledge_engine.py -v`
Expected: all tests `PASS` (14 total so far).

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/agents.py tests/test_knowledge_engine.py
git commit -m "feat: gate knowledge- roles behind knowledge-engine.enabled"
```

---

### Task 3: `build_variables()` KNOWLEDGE_* variables

**Files:**
- Modify: `scripts/lib/config.py:511` (insert directly after the existing SE-cascade-defaults loop, before the `A2A_T_SIZE_LIMIT` comment)
- Test: `tests/test_knowledge_engine.py` (append)

**Interfaces:**
- Consumes: `generate_schema` not needed here (only in Task 4).
- Produces: `variables["KNOWLEDGE_ENGINE_ENABLED"]` (`"true"`/`"false"` string), `variables["KNOWLEDGE_DOMAIN"]` (string, default `"research"`), `variables["KNOWLEDGE_BUNDLE_PATH"]` (string, default `"knowledge"`) — all consumed by later Phase B agent templates via `{{VAR}}` substitution.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_knowledge_engine.py`:

```python
from scripts.lib.config import build_variables

_TEST_REPO_ROOT = Path(__file__).resolve().parent.parent


def _minimal_config(**overrides) -> dict:
    config = {
        "project": {"name": "test-proj", "prefix": "tp", "short": "test-proj"},
        "ai-providers": ["Claude"],
    }
    config.update(overrides)
    return config


# ---------------------------------------------------------------------------
# build_variables() — KNOWLEDGE_* injection
# ---------------------------------------------------------------------------

def test_build_variables_knowledge_defaults_when_block_absent():
    variables = build_variables(_minimal_config(), _AGENT_META_ROOT)
    assert variables["KNOWLEDGE_ENGINE_ENABLED"] == "false"
    assert variables["KNOWLEDGE_DOMAIN"] == "research"
    assert variables["KNOWLEDGE_BUNDLE_PATH"] == "knowledge"


def test_build_variables_knowledge_enabled_true():
    config = _minimal_config(**{
        "knowledge-engine": {"enabled": True, "domain": "personal", "bundle-path": "kb"},
    })
    variables = build_variables(config, _AGENT_META_ROOT)
    assert variables["KNOWLEDGE_ENGINE_ENABLED"] == "true"
    assert variables["KNOWLEDGE_DOMAIN"] == "personal"
    assert variables["KNOWLEDGE_BUNDLE_PATH"] == "kb"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_knowledge_engine.py -k build_variables_knowledge -v`
Expected: FAIL — `KeyError: 'KNOWLEDGE_ENGINE_ENABLED'`.

Note: if `build_variables()` requires additional config keys not present in `_minimal_config()`, the test will instead fail with a different `KeyError`/`AttributeError` from an unrelated section — if so, add the missing minimal key (e.g. `"platforms": []`) to `_minimal_config()` rather than changing the assertions.

- [ ] **Step 3: Write the implementation**

Edit `scripts/lib/config.py`, inserting directly after line 511 (the `_se_vars_defaults` loop) and before the `A2A_T_SIZE_LIMIT` comment:

```python
    # KNOWLEDGE_ENGINE_ENABLED / KNOWLEDGE_DOMAIN / KNOWLEDGE_BUNDLE_PATH —
    # Phase A of the Knowledge Engine. Mirrors the SE block above; consumed by
    # Phase B knowledge-* agent templates once they exist.
    ke_config = config.get("knowledge-engine", {})
    variables["KNOWLEDGE_ENGINE_ENABLED"] = "true" if ke_config.get("enabled", False) else "false"
    variables["KNOWLEDGE_DOMAIN"] = ke_config.get("domain", "research")
    variables["KNOWLEDGE_BUNDLE_PATH"] = ke_config.get("bundle-path", "knowledge")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_knowledge_engine.py -v`
Expected: all tests `PASS` (16 total so far).

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/config.py tests/test_knowledge_engine.py
git commit -m "feat: inject KNOWLEDGE_* variables in build_variables"
```

---

### Task 4: `sync_knowledge_engine()` — Phase 2.5 in `scripts/sync.py`

**Files:**
- Modify: `scripts/sync.py` (imports near line 88, new function placed in the "Helpers" section after `_collect_skill_gitignore_entries` around line 147, call site inserted between line 877 and line 878)
- Test: `tests/test_knowledge_sync_integration.py` (new)

**Interfaces:**
- Consumes: `generate_schema`, `generate_initial_index`, `generate_initial_log` from `scripts.lib.knowledge` (Task 1); `write_checked`, `safe_path`, `SyncError` from `scripts.lib.io`; `SyncLog` from `scripts.lib.log`.
- Produces: `sync_knowledge_engine(agent_meta_root: Path, project_root: Path, config: dict, log: SyncLog, dry_run: bool) -> None`. Raises `SyncError` when `bundle-path` points at an existing non-directory file, or when `domain` is invalid.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_knowledge_sync_integration.py`:

```python
"""Integration tests for scripts/sync.py::sync_knowledge_engine() (Phase 2.5)."""
from pathlib import Path
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.log import SyncLog  # noqa: E402
from lib.io import SyncError  # noqa: E402
import sync as sync_module  # noqa: E402

sync_knowledge_engine = sync_module.sync_knowledge_engine

_AGENT_META_ROOT = _REPO_ROOT


def _config(enabled=True, domain="research", bundle_path="knowledge"):
    return {
        "knowledge-engine": {
            "enabled": enabled,
            "domain": domain,
            "bundle-path": bundle_path,
        }
    }


# ---------------------------------------------------------------------------
# Disabled — zero-overhead regression
# ---------------------------------------------------------------------------

def test_disabled_is_a_complete_noop(tmp_path):
    log = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, {}, log, dry_run=False)
    assert not (tmp_path / "knowledge").exists()
    assert not log.actions


def test_disabled_explicitly_is_a_complete_noop(tmp_path):
    log = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(enabled=False), log, dry_run=False)
    assert not (tmp_path / "knowledge").exists()
    assert not log.actions


# ---------------------------------------------------------------------------
# Fresh scaffolding
# ---------------------------------------------------------------------------

def test_fresh_bundle_creates_expected_files(tmp_path):
    log = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(), log, dry_run=False)

    bundle = tmp_path / "knowledge"
    assert (bundle / "schema.md").exists()
    assert (bundle / "wiki" / "index.md").exists()
    assert (bundle / "wiki" / "log.md").exists()
    for sub in ["sources/assets", "wiki/concepts", "wiki/entities",
                "wiki/topics", "wiki/sources", "wiki/queries"]:
        assert (bundle / sub / ".gitkeep").exists(), f"missing .gitkeep in {sub}"

    schema_text = (bundle / "schema.md").read_text(encoding="utf-8")
    assert "research" in schema_text
    assert "- paper" in schema_text


def test_fresh_bundle_dry_run_writes_nothing(tmp_path):
    log = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(), log, dry_run=True)
    assert not (tmp_path / "knowledge").exists()


def test_custom_bundle_path_and_domain(tmp_path):
    log = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(domain="book", bundle_path="kb"), log, dry_run=False)
    bundle = tmp_path / "kb"
    assert (bundle / "schema.md").exists()
    schema_text = (bundle / "schema.md").read_text(encoding="utf-8")
    assert "book" in schema_text
    assert "- character" in schema_text


# ---------------------------------------------------------------------------
# Idempotency — second run must not overwrite
# ---------------------------------------------------------------------------

def test_second_run_does_not_overwrite_existing_bundle_files(tmp_path):
    log = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(), log, dry_run=False)

    bundle = tmp_path / "knowledge"
    (bundle / "schema.md").write_text("# hand-edited by user\n", encoding="utf-8")
    (bundle / "wiki" / "index.md").write_text("# hand-edited index\n", encoding="utf-8")
    (bundle / "wiki" / "log.md").write_text("# hand-edited log\n", encoding="utf-8")

    log2 = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(), log2, dry_run=False)

    assert (bundle / "schema.md").read_text(encoding="utf-8") == "# hand-edited by user\n"
    assert (bundle / "wiki" / "index.md").read_text(encoding="utf-8") == "# hand-edited index\n"
    assert (bundle / "wiki" / "log.md").read_text(encoding="utf-8") == "# hand-edited log\n"


def test_second_run_fills_in_missing_gitkeep_only(tmp_path):
    log = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(), log, dry_run=False)

    bundle = tmp_path / "knowledge"
    (bundle / "wiki" / "concepts" / ".gitkeep").unlink()
    assert not (bundle / "wiki" / "concepts" / ".gitkeep").exists()

    log2 = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(), log2, dry_run=False)
    assert (bundle / "wiki" / "concepts" / ".gitkeep").exists()


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_bundle_path_is_existing_file_raises_sync_error(tmp_path):
    (tmp_path / "knowledge").write_text("not a directory\n", encoding="utf-8")
    log = SyncLog()
    with pytest.raises(SyncError, match="not a directory"):
        sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(), log, dry_run=False)


def test_invalid_domain_raises_sync_error(tmp_path):
    log = SyncLog()
    with pytest.raises(SyncError, match="Unknown knowledge-engine domain"):
        sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(domain="not-a-real-domain"), log, dry_run=False)
    assert not (tmp_path / "knowledge").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_knowledge_sync_integration.py -v`
Expected: `AttributeError: module 'sync' has no attribute 'sync_knowledge_engine'` on every test.

- [ ] **Step 3: Add the import in `scripts/sync.py`**

Edit `scripts/sync.py:88` (the existing `from lib.io import SyncError` line):

```python
from lib.io import SyncError, safe_path, write_checked
```

- [ ] **Step 4: Add the import for the knowledge helpers**

Edit `scripts/sync.py`, right after the `lib.viz` import block (line 94-97):

```python
from lib.viz import (
    generate_viz, get_gitignore_entries as viz_gitignore_entries,
    cleanup_old_sessions,
)
from lib.knowledge import generate_schema, generate_initial_index, generate_initial_log
```

- [ ] **Step 5: Write `sync_knowledge_engine()`**

Edit `scripts/sync.py`, inserting a new function directly after `_collect_skill_gitignore_entries` (after line 147, before the `# Test-Repository Validation` section header):

```python
# ---------------------------------------------------------------------------
# Knowledge Engine — Phase A scaffolding (sync Phase 2.5)
# ---------------------------------------------------------------------------

_KNOWLEDGE_GITKEEP_SUBDIRS = [
    Path("sources", "assets"),
    Path("wiki", "concepts"),
    Path("wiki", "entities"),
    Path("wiki", "topics"),
    Path("wiki", "sources"),
    Path("wiki", "queries"),
]


def sync_knowledge_engine(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Phase 2.5 — scaffold the knowledge/ bundle when knowledge-engine.enabled is true.

    No-op (zero-overhead) when disabled or absent. Idempotent: never
    overwrites existing schema.md/wiki/index.md/wiki/log.md, only fills in
    missing .gitkeep markers in empty subdirectories on subsequent runs.
    """
    ke_config = config.get("knowledge-engine") or {}
    if not ke_config.get("enabled", False):
        log.skip("knowledge-engine", "disabled in project.yaml")
        return

    domain = ke_config.get("domain", "research")
    bundle_rel = ke_config.get("bundle-path", "knowledge")
    bundle_dir = safe_path(project_root, bundle_rel)

    if bundle_dir.exists() and not bundle_dir.is_dir():
        raise SyncError(
            f"knowledge-engine.bundle-path '{bundle_rel}' points to an existing "
            f"file, not a directory: {bundle_dir}"
        )

    bundle_exists = bundle_dir.is_dir()

    if not bundle_exists:
        try:
            schema_content = generate_schema(domain, bundle_rel, agent_meta_root)
        except ValueError as exc:
            raise SyncError(f"knowledge-engine: {exc}") from exc

        if not dry_run:
            (bundle_dir / "wiki").mkdir(parents=True, exist_ok=True)

        schema_path = bundle_dir / "schema.md"
        rel_schema = f"{bundle_rel}/schema.md"
        if write_checked(schema_path, schema_content, log, rel_schema, dry_run=dry_run):
            log.action("CREATE", rel_schema, "knowledge-engine scaffolding")

        index_path = bundle_dir / "wiki" / "index.md"
        rel_index = f"{bundle_rel}/wiki/index.md"
        if write_checked(index_path, generate_initial_index(), log, rel_index, dry_run=dry_run):
            log.action("CREATE", rel_index, "knowledge-engine scaffolding")

        log_path = bundle_dir / "wiki" / "log.md"
        rel_log = f"{bundle_rel}/wiki/log.md"
        if write_checked(log_path, generate_initial_log(), log, rel_log, dry_run=dry_run):
            log.action("CREATE", rel_log, "knowledge-engine scaffolding")
    else:
        log.info(
            "knowledge-engine",
            f"{bundle_rel}/ already exists — schema.md/index.md/log.md not "
            "regenerated. If domain changed, verify schema.md manually "
            "(not auto-migrated in Phase A)."
        )

    for rel_subdir in _KNOWLEDGE_GITKEEP_SUBDIRS:
        target_dir = bundle_dir / rel_subdir
        gitkeep_path = target_dir / ".gitkeep"
        rel_gitkeep = f"{bundle_rel}/{rel_subdir.as_posix()}/.gitkeep"
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
        if write_checked(gitkeep_path, "", log, rel_gitkeep, dry_run=dry_run):
            log.action("CREATE", rel_gitkeep, "knowledge-engine scaffolding")
```

- [ ] **Step 6: Wire the call site**

Edit `scripts/sync.py`, inserting between the end of the per-provider `for provider in providers:` loop (line 877, `sync_external_skills_for_provider(...)`) and the provider-isolation block (line 878, `isolation_mode = config.get("provider-isolation")`):

```python
            sync_external_skills_for_provider(agent_meta_root, project_root, config, variables,
                                              log, args.dry_run, provider, provider_config)
        # Knowledge Engine — Phase A scaffolding (no-op unless knowledge-engine.enabled)
        try:
            sync_knowledge_engine(agent_meta_root, project_root, config, log, args.dry_run)
        except SyncError as exc:
            print(f"\n  !!  Knowledge Engine sync aborted: {exc}", file=sys.stderr)
            sys.exit(1)
        # Provider isolation: hard-block cross-provider directory access
        isolation_mode = config.get("provider-isolation")
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python -m pytest tests/test_knowledge_sync_integration.py -v`
Expected: all 10 tests `PASS`.

- [ ] **Step 8: Run the full existing test suite to check for regressions**

Run: `python -m pytest tests/ -v --ignore=tests/browser --ignore=tests/manual --ignore=tests/automated`
Expected: all pre-existing tests still `PASS` (no regressions from the new import or call site).

- [ ] **Step 9: Run sync.py --dry-run on agent-meta itself to confirm zero-overhead**

Run: `python scripts/sync.py --dry-run`
Expected: exit code `0`; log output contains `[SKIP]   knowledge-engine` (since `.meta-config/project.yaml` will not yet have `knowledge-engine.enabled: true` until Task 5); no `knowledge/` directory created in the repo root.

- [ ] **Step 10: Commit**

```bash
git add scripts/sync.py tests/test_knowledge_sync_integration.py
git commit -m "feat: add sync_knowledge_engine bundle scaffolding phase"
```

---

### Task 5: Config schema + self-hosting `project.yaml` entry

**Files:**
- Modify: `config/project-config.schema.json` (insert after the `admin-ui` block, i.e. after line 852, before the `viz` block at line 854)
- Modify: `.meta-config/project.yaml` (insert after the existing `systems-engineering:` block, lines 10-11)
- Test: `tests/test_knowledge_engine.py` (append)

**Interfaces:**
- Consumes: nothing (pure config/schema data).
- Produces: `knowledge-engine` becomes a documented, IDE-autocompletable top-level key; this repo's own `.meta-config/project.yaml` gets the block with `enabled: false` (matches Phase A default — no scaffolding runs for agent-meta itself yet).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_knowledge_engine.py`:

```python
import json


# ---------------------------------------------------------------------------
# config/project-config.schema.json — knowledge-engine property
# ---------------------------------------------------------------------------

def test_schema_has_knowledge_engine_property():
    schema_path = _AGENT_META_ROOT / "config" / "project-config.schema.json"
    with schema_path.open(encoding="utf-8") as f:
        schema = json.load(f)
    ke_schema = schema["properties"]["knowledge-engine"]
    assert ke_schema["type"] == "object"
    assert ke_schema["properties"]["enabled"]["type"] == "boolean"
    assert ke_schema["properties"]["enabled"]["default"] is False
    assert set(ke_schema["properties"]["domain"]["enum"]) == set(DOMAIN_CONCEPT_TYPES.keys())
    assert ke_schema["properties"]["bundle-path"]["type"] == "string"


def test_self_hosting_project_yaml_has_knowledge_engine_block():
    import yaml
    project_yaml_path = _AGENT_META_ROOT / ".meta-config" / "project.yaml"
    with project_yaml_path.open(encoding="utf-8") as f:
        project_config = yaml.safe_load(f)
    assert project_config["knowledge-engine"]["enabled"] is False
    assert project_config["knowledge-engine"]["domain"] in DOMAIN_CONCEPT_TYPES
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_knowledge_engine.py -k "schema_has_knowledge or self_hosting_project_yaml" -v`
Expected: FAIL — `KeyError: 'knowledge-engine'` on both tests.

- [ ] **Step 3: Edit the schema**

Edit `config/project-config.schema.json`, inserting between the `admin-ui` block (ends at line 852 with `"additionalProperties": false\n    },`) and the `viz` block (line 854):

```json
    "knowledge-engine": {
      "type": "object",
      "description": "Knowledge Engine — opt-in bundle for structured, queryable project/domain knowledge (Phase A: activation + scaffolding only, no agents yet).",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false,
          "description": "Enable the Knowledge Engine. When true, sync.py scaffolds the bundle-path directory on first run."
        },
        "domain": {
          "type": "string",
          "enum": ["research", "personal", "business", "book", "custom"],
          "default": "research",
          "description": "Concept-type preset for schema.md generation. See scripts/lib/knowledge.py DOMAIN_CONCEPT_TYPES."
        },
        "bundle-path": {
          "type": "string",
          "default": "knowledge",
          "description": "Root directory of the knowledge bundle, relative to the project root."
        }
      },
      "additionalProperties": false
    },
```

- [ ] **Step 4: Edit `.meta-config/project.yaml`**

Edit `.meta-config/project.yaml`, inserting directly after the existing block (lines 10-11):

```yaml
systems-engineering:
  enabled: false
knowledge-engine:
  enabled: false
  domain: research
  bundle-path: knowledge
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_knowledge_engine.py tests/test_knowledge_sync_integration.py -v`
Expected: all tests `PASS` (schema + self-hosting tests plus every test from Tasks 1-4).

- [ ] **Step 6: Run agent-meta's own consistency validation**

Run: `python scripts/sync.py --dry-run --validate`
Expected: exit code `0` — no new consistency errors from the schema addition (schema is additive, `additionalProperties` unset at the root level per existing convention).

- [ ] **Step 7: Run full sync.py --dry-run one more time**

Run: `python scripts/sync.py --dry-run`
Expected: exit code `0`; log still shows `[SKIP]   knowledge-engine` (agent-meta's own `knowledge-engine.enabled` stays `false` in Phase A — activation for real use is a separate, later decision).

- [ ] **Step 8: Commit**

```bash
git add config/project-config.schema.json .meta-config/project.yaml tests/test_knowledge_engine.py
git commit -m "feat: document knowledge-engine block in schema and self-hosting config"
```

---

## Final Verification

- [ ] **Run the complete new + existing test suite**

Run: `python -m pytest tests/test_knowledge_engine.py tests/test_knowledge_sync_integration.py tests/ -v --ignore=tests/browser --ignore=tests/manual --ignore=tests/automated`
Expected: 0 failures.

- [ ] **Confirm zero-overhead for a knowledge-engine-less project**

Run a scratch check: create a temp project config without any `knowledge-engine` key, run `sync_knowledge_engine()` against it (covered by `test_disabled_is_a_complete_noop`), confirm no `knowledge/` directory and no log actions — already covered in Task 4 but re-run explicitly as a final gate:

Run: `python -m pytest tests/test_knowledge_sync_integration.py -k noop -v`
Expected: 2 tests `PASS`.

- [ ] **Manual smoke test: enable it in a scratch directory**

```bash
mkdir -p /tmp/ke-smoke-test/.meta-config
cat > /tmp/ke-smoke-test/.meta-config/project.yaml <<'EOF'
ai-providers: [Claude]
project:
  name: ke-smoke-test
  prefix: kst
  short: ke-smoke-test
knowledge-engine:
  enabled: true
  domain: personal
  bundle-path: knowledge
EOF
cd /tmp/ke-smoke-test && python /path/to/agent-meta/scripts/sync.py --config .meta-config/project.yaml --dry-run
```

Expected: log shows `CREATE   knowledge/schema.md`, `CREATE   knowledge/wiki/index.md`, `CREATE   knowledge/wiki/log.md`, and 6 `.gitkeep` creates — with `--dry-run` no files are actually written; re-run without `--dry-run` to verify the files land on disk with `personal` domain concept types (`person`, `event`, `place`, `memory`) in `schema.md`.
