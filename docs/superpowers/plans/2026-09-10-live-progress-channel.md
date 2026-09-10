# Live-Progress-Kanal für Orchestrator + Planungspipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give a running Orchestrator/Planungspipeline session a live progress signal that reaches the user during the run (not only at the final task result), staged by what each provider platform actually supports, plus a root-cause fix for the existing provider-blind `.claude/progress/current.md` path.

**Architecture:** `scripts/lib/checkpoint.py` gets a provider-neutral write target (`.meta-viz/progress/current.md`, consistent with the already provider-neutral `.meta-viz/checkpoints/`) and a Tier resolver reusing `scripts/lib/providers.py::provider_hooks_supported()` — Tier A (Claude, Gemini: verified `hook_protocol`) keeps the existing overwrite-per-save behavior plus a new prompt-level `SendMessage(to:"main")` push instruction in `orchestrator.md`, gated by a new `PROGRESS_CHAT_PUSH_ENABLED` sync variable; Tier B (the other seven providers) switches to append-with-session-start-rotation because the file is their only channel. Checkpoints gain an optional `pipeline`/`stage` field so concurrently running pipelines (`se-cascade`, `concept-driven-dev`) are distinguishable in the shared file.

**Tech Stack:** Python 3.9+ stdlib only (`config/ai-providers.yaml` via the existing `scripts/lib/io._load_yaml_or_json` loader), pytest, `tests/scenarios/` harness (dry-run + sync + `--validate` + assert-script in a temp dir).

**Spec:** `docs/superpowers/specs/2026-09-10-live-progress-channel-design.md`

## Global Constraints

- `.meta-viz/progress/current.md` is the **sole** new write target for **every** provider (spec Architecture §2, Entscheidung Option b) — no provider-specific path, no new `progress_dir` config key.
- Tier A (overwrite + chat-push instruction) only when **every** active provider has a verified `hook_protocol` — reuse `scripts/lib/providers.py::provider_hooks_supported(pc)` (today true for Claude, Gemini only). A mixed active-provider set (e.g. Claude + Opencode) falls back to Tier B — never silently drop the only channel a hook-less provider has.
- No stall-/hang-detection (Issue #681, explicit Nicht-Ziel in the spec) — out of scope for every task below.
- `snippets/orchestrator/status-table.md` content itself is **not** touched (spec Nicht-Ziele) — only where/how it additionally lands.
- The old `.claude/progress/current.md` is never deleted, moved, or migrated (spec Rollout section) — new writes go exclusively to the new path; `.gitignore`'s existing `.claude/progress/` entry (line 24) stays as-is.
- `.meta-viz/` is already fully gitignored (`.gitignore:54`) — `.meta-viz/progress/` needs **no new** `.gitignore` entry; a regression test guards this instead of adding a redundant line.
- No external Python dependencies — stdlib only (`CLAUDE.md` Code-Konventionen); PyYAML is an existing soft dependency already used via `scripts/lib/io._load_yaml_or_json`, not a new one.
- Provider differences are expressed via config/capability flags (`config/ai-providers.yaml` `hook_protocol`, `providers.provider_hooks_supported()`), never `if provider == "Name"` (`CLAUDE.md` Code-Konventionen, `provider-agnostic` skill).
- Rotation cap for the Tier-B file: **200,000 bytes** (`_PROGRESS_MAX_BYTES`), this plan's concrete answer to the spec's open implementation point 3 — chosen as roughly 4x the existing 50 KB JSON-checkpoint budget documented in `snippets/orchestrator/checkpointing.md`, since rendered markdown entries run more verbose per checkpoint than the JSON they mirror.
- Every new/changed `tests/scenarios/` entry follows the Framework-Szenario-Konvention (`tests/scenarios/registry.md`): concrete effect assertions (not just file existence), added in the **same** task as the feature it covers, plus a `registry.md` catalog row.
- `Checkpoint.pipeline`/`Checkpoint.stage` are optional and default to `None` — old checkpoint JSON without these keys must still load (`Checkpoint.from_dict` backward-compat convention already established for `status_summary`).

---

### Task 1: Root-cause path fix — `.claude/progress` → `.meta-viz/progress`

**Files:**
- Modify: `scripts/lib/checkpoint.py:32` (`_PROGRESS_DIR` constant), `:235-239` (`_write_progress_file` docstring)
- Modify: `tests/test_progress_file.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `_PROGRESS_DIR = ".meta-viz/progress"` — every later task in this plan writes/reads under this constant, never a literal path string.

- [ ] **Step 1: Update the existing tests to expect the new path**

  Replace `tests/test_progress_file.py` with:

  ```python
  """.meta-viz/progress/current.md write-through on every checkpoint save
  (issue #682 §6, Option A; path made provider-neutral by the live-progress-
  channel design, 2026-09-10) -- human-readable progress snapshot, overwritten
  each time on Tier-A providers, not historized. Reuses the same table format
  as the orchestrator status-table snippet (issue #678) so the text can be
  copy-pasted between the two surfaces."""

  import sys
  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(_REPO_ROOT / "scripts"))

  from lib.checkpoint import Checkpoint, CheckpointStore  # noqa: E402


  def _store(tmp_path: Path) -> CheckpointStore:
      return CheckpointStore(project_root=tmp_path)


  def test_save_checkpoint_writes_progress_file(tmp_path):
      store = _store(tmp_path)
      cp = Checkpoint(
          task_id="t1", agent="developer", task_description="implement X",
          status="completed", status_summary="On track.",
      )
      store.save_checkpoint("sess1", cp)
      progress_path = tmp_path / ".meta-viz" / "progress" / "current.md"
      assert progress_path.exists()
      content = progress_path.read_text(encoding="utf-8")
      assert "developer" in content
      assert "implement X" in content
      assert "completed" in content
      assert "On track." in content


  def test_progress_file_is_overwritten_not_appended(tmp_path):
      store = _store(tmp_path)
      store.save_checkpoint(
          "sess1", Checkpoint(task_id="t1", agent="developer", task_description="first", status="completed")
      )
      store.save_checkpoint(
          "sess1", Checkpoint(task_id="t2", agent="tester", task_description="second", status="in_progress")
      )
      content = (tmp_path / ".meta-viz" / "progress" / "current.md").read_text(encoding="utf-8")
      # Both checkpoints of the session appear (cumulative table), but the
      # file itself was overwritten (single write_atomic call), not appended to.
      # Default tier (no .meta-config/project.yaml present) resolves to
      # Tier A -- see Task 5 -- so overwrite semantics stay the pre-existing
      # default for this bare-tmp_path fixture shape.
      assert "first" in content
      assert "second" in content
      assert content.count("| Agent | Task | Status |") == 1


  def test_progress_file_survives_corrupt_existing_session_json(tmp_path):
      store = _store(tmp_path)
      # Simulate a corrupt session file (#576 fail-soft contract) -- must not
      # crash the progress write either.
      store.checkpoint_dir.mkdir(parents=True)
      (store.checkpoint_dir / "sess1.json").write_text("{not valid json", encoding="utf-8")
      store.save_checkpoint(
          "sess1", Checkpoint(task_id="t1", agent="developer", task_description="x", status="pending")
      )
      assert (tmp_path / ".meta-viz" / "progress" / "current.md").exists()
  ```

- [ ] **Step 2: Run the tests, confirm they fail against the unchanged source**

  Run: `pytest tests/test_progress_file.py -v`
  Expected: FAIL — files still land under `tmp_path/.claude/progress/current.md`, not `.meta-viz/progress/current.md`.

- [ ] **Step 3: Fix the constant in `checkpoint.py`**

  ```python
  # scripts/lib/checkpoint.py:32
  _PROGRESS_DIR = ".meta-viz/progress"
  ```

  And update the `_write_progress_file` docstring (`checkpoint.py:236`):

  ```python
      def _write_progress_file(self, session_data: dict) -> None:
          """Write .meta-viz/progress/current.md -- see _render_progress_markdown.
          Provider-neutral path (live-progress-channel design, 2026-09-10) --
          was hardcoded to the Claude-specific .claude/progress/ before.
          """
  ```

- [ ] **Step 4: Run the tests again, confirm they pass**

  Run: `pytest tests/test_progress_file.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**

  ```bash
  git add scripts/lib/checkpoint.py tests/test_progress_file.py
  git commit -m "fix: write progress file to provider-neutral .meta-viz/progress"
  ```

---

### Task 2: Documentation update — `.claude/progress` references

**Files:**
- Modify: `snippets/orchestrator/checkpointing.md:37-43`
- Modify: `agents/1-generic/orchestrator.md:173`
- Modify: `tests/test_progress_file_documented.py`

**Interfaces:**
- Consumes: `_PROGRESS_DIR` from Task 1 (the literal path string `.meta-viz/progress/current.md`).
- Produces: nothing new consumed by later tasks — pure documentation surface.

- [ ] **Step 1: Update the doc-location test first**

  Replace `tests/test_progress_file_documented.py` with:

  ```python
  """Progress-file behavior (issue #682 §6, live-progress-channel design
  2026-09-10) must be documented where a developer would look for
  checkpoint/progress semantics."""

  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parents[1]


  def test_checkpointing_snippet_documents_progress_file():
      content = (_REPO_ROOT / "snippets" / "orchestrator" / "checkpointing.md").read_text(encoding="utf-8")
      assert ".meta-viz/progress/current.md" in content


  def test_orchestrator_section_9_documents_progress_file():
      content = (_REPO_ROOT / "agents" / "1-generic" / "orchestrator.md").read_text(encoding="utf-8")
      section_9_start = content.index("## 9. Context guard & checkpointing")
      section_10_start = content.index("## 10. Delegation failure recovery")
      section_9 = content[section_9_start:section_10_start]
      assert ".meta-viz/progress/current.md" in section_9
      assert "Tier-A" in section_9 or "Tier A" in section_9
      assert "Tier-B" in section_9 or "Tier B" in section_9
  ```

- [ ] **Step 2: Run it, confirm FAIL**

  Run: `pytest tests/test_progress_file_documented.py -v`
  Expected: FAIL — old docs still say `.claude/progress/current.md` and don't mention Tier A/B.

- [ ] **Step 3: Update `snippets/orchestrator/checkpointing.md`**

  Replace the `**Progress-Datei (issue #682 §6):**` paragraph (lines 37-43) with:

  ```markdown
  **Progress-Datei (issue #682 §6, Tier-Modell — live-progress-channel, 2026-09-10):** Falls die
  Laufzeit `CheckpointStore.save_checkpoint()` (Python-API in `scripts/lib/checkpoint.py`,
  kein manuell vom Agenten geschriebenes Format) aufruft, schreibt sie `.meta-viz/progress/current.md`
  — auf Tier-A-Providern (verifiziertes `hook_protocol`, z.B. Claude/Gemini) überschreibend
  (nicht historisiert), auf allen anderen (Tier-B-)Providern anhängend mit Rotation beim
  Start einer neuen Session, weil die Datei dort der einzige Live-Kanal ist. Für Resume-Logik
  weiterhin die JSON-Checkpoints verwenden, `current.md` ist nur für den schnellen menschlichen
  Blick in den Fortschritt gedacht — kein Ersatz für das oben beschriebene, manuell geschriebene
  Checkpoint-Format.
  ```

- [ ] **Step 4: Update `agents/1-generic/orchestrator.md` §9**

  Replace line 173 with:

  ```markdown
  **Progress file (issue #682 §6, Tier model — live-progress-channel design, 2026-09-10):** if the runtime calls `CheckpointStore.save_checkpoint()` (the Python API in `scripts/lib/checkpoint.py` — distinct from the manually-written checkpoint format above), it writes `.meta-viz/progress/current.md` — overwritten (non-historized) on Tier-A providers (verified `hook_protocol`, e.g. Claude/Gemini — see the chat-push instruction in §7), appended with session-start rotation on every Tier-B provider, since the file is their only live channel. Resume logic still reads the JSON checkpoints; `current.md` is for a human glancing at the repo, not parsed by any code path.
  ```

- [ ] **Step 5: Run the tests, confirm PASS**

  Run: `pytest tests/test_progress_file_documented.py -v`
  Expected: PASS

- [ ] **Step 6: Commit**

  ```bash
  git add snippets/orchestrator/checkpointing.md agents/1-generic/orchestrator.md tests/test_progress_file_documented.py
  git commit -m "docs: point progress-file docs at .meta-viz/progress + Tier A/B"
  ```

---

### Task 3: Scenario 48 — provider-neutral progress path

**Files:**
- Create: `tests/scenarios/configs/48-progress-provider-neutral-path.project.yaml`
- Create: `tests/scenarios/asserts/48-progress-provider-neutral-path.sh` (executable)
- Modify: `tests/scenarios/registry.md`

**Interfaces:**
- Consumes: `_PROGRESS_DIR`/`CheckpointStore` from Task 1 (real library import inside the assert script — the scenario harness already exposes `REPO_ROOT` as `$1`/env var per the existing assert-script contract).
- Produces: nothing consumed by later tasks — first of the 3 required new scenarios (registry IDs continue at 46).

- [ ] **Step 1: Create the scenario config** (deliberately Opencode-only — a non-Claude, hook-less provider, to directly target the regression the spec's Problem section describes: "für jedes Nicht-Claude-Projekt landet die Datei an einem Claude-spezifischen Pfad")

  `tests/scenarios/configs/48-progress-provider-neutral-path.project.yaml`:

  ```yaml
  agent-meta-version: 0.101.0
  ai-providers:
  - Opencode
  dod-preset: standard
  platforms: []
  roles:
  - orchestrator
  - developer
  - git
  orchestrator:
    mode: strict
    checkpointing: true
  project:
    name: scenario-progress-provider-neutral-path
    prefix: s48
    short: scenario-progress-neutral
  variables:
    PROJECT_NAME: scenario-progress-provider-neutral-path
    PROJECT_DESCRIPTION: Provider-neutral progress path regression test (live-progress-channel design, 2026-09-10).
    PROJECT_GOAL: Verify CheckpointStore never writes .claude/progress/ for a non-Claude provider and always writes .meta-viz/progress/current.md.
    GIT_PLATFORM: GitHub
    GIT_REMOTE_URL: https://github.com/example/scenario-progress-neutral
    GIT_MAIN_BRANCH: main
  rules-preset: default
  speech-mode: full
  tier-preset: Normal
  se-focus: false
  max-parallel-agents: 2
  conventions-preset: default
  debug-mode: false
  allow-committed-secrets: false
  ```

- [ ] **Step 2: Create the assert script**

  `tests/scenarios/asserts/48-progress-provider-neutral-path.sh` (`chmod +x`):

  ```bash
  #!/bin/bash
  # Scenario assert for 48-progress-provider-neutral-path
  #
  # Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
  # agent-meta checkout path.
  set -u

  REPO_ROOT="${1:-${REPO_ROOT:-}}"
  if [ -z "$REPO_ROOT" ]; then
      echo "ASSERT ERROR (48-progress-provider-neutral-path): REPO_ROOT missing (pass as \$1 or env var)"
      exit 2
  fi

  fail() {
      echo "ASSERT FAIL (48-progress-provider-neutral-path): $*"
      exit 1
  }

  python3 - "$REPO_ROOT" <<'PYEOF' || fail "python check failed"
  import sys
  from pathlib import Path

  repo_root = Path(sys.argv[1])
  sys.path.insert(0, str(repo_root / "scripts"))
  from lib.checkpoint import Checkpoint, CheckpointStore

  store = CheckpointStore(project_root=Path("."), agent_meta_root=repo_root)
  store.save_checkpoint(
      "sess1", Checkpoint(task_id="t1", agent="developer", task_description="path-check", status="completed")
  )
  assert Path(".meta-viz/progress/current.md").exists(), (
      "progress file must land at the provider-neutral .meta-viz/progress/ path"
  )
  assert not Path(".claude/progress/current.md").exists(), (
      "must never write the old Claude-specific path for a non-Claude provider"
  )
  PYEOF

  grep -rl ".meta-viz/progress/current.md" . >/dev/null 2>&1 \
      || fail "no generated file references the provider-neutral progress path .meta-viz/progress/current.md"

  echo "ASSERT OK (48-progress-provider-neutral-path): provider-neutral path verified"
  ```

- [ ] **Step 3: Register the scenario in the catalog**

  In `tests/scenarios/registry.md`, append to the `## Katalog` table:

  ```markdown
  | `46-progress-tierb-append-rotation` | Opencode | strict (default), `checkpointing: true` | Tier-B (hook-less provider) progress file appends per checkpoint + rotates on new session (live-progress-channel design, 2026-09-10) |
  | `47-progress-pipeline-stage-field` | Opencode | strict (default), `checkpointing: true` | `Pipeline/Stage`-Spalte unterscheidet gleichzeitige `se-cascade`/`concept-driven-dev`-Einträge in der Tier-B-Datei (live-progress-channel design) |
  | `48-progress-provider-neutral-path` | Opencode | strict (default), `checkpointing: true` | Root-Cause-Fix: `.meta-viz/progress/current.md` statt hartcodiertem `.claude/progress/` für einen Nicht-Claude-Provider (live-progress-channel design) |
  ```

  (All three rows are added now so the catalog table reads as one contiguous block; Tasks 7 and 9 below create the corresponding `configs/`/`asserts/` files for `46` and `47`.)

- [ ] **Step 4: Run the scenario**

  Run: `tests/scenarios/run.sh 48`
  Expected: `PASS`

- [ ] **Step 5: Commit**

  ```bash
  git add tests/scenarios/configs/48-progress-provider-neutral-path.project.yaml \
          tests/scenarios/asserts/48-progress-provider-neutral-path.sh \
          tests/scenarios/registry.md
  git commit -m "test: scenario 48 — provider-neutral progress path"
  ```

---

### Task 4: Migration/rollout regression test

**Files:**
- Create: `tests/test_progress_file_migration.py`

**Interfaces:**
- Consumes: `_PROGRESS_DIR` from Task 1.
- Produces: nothing new — pure regression guard, no source change (behavior is already correct after Task 1: the old path is a dead constant, never referenced again).

- [ ] **Step 1: Write the regression test**

  ```python
  """Rollout/migration regression (spec 2026-09-10-live-progress-channel-design.md,
  Rollout/Migration section): an existing .claude/progress/current.md from before
  the provider-neutral path fix must survive a checkpoint save untouched, and
  .gitignore must already cover the new path without a dedicated entry."""

  import sys
  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(_REPO_ROOT / "scripts"))

  from lib.checkpoint import Checkpoint, CheckpointStore  # noqa: E402


  def test_legacy_claude_progress_file_is_left_untouched(tmp_path):
      legacy_dir = tmp_path / ".claude" / "progress"
      legacy_dir.mkdir(parents=True)
      legacy_path = legacy_dir / "current.md"
      legacy_path.write_text("# stale pre-migration snapshot\n", encoding="utf-8")

      store = CheckpointStore(project_root=tmp_path)
      store.save_checkpoint(
          "sess1", Checkpoint(task_id="t1", agent="developer", task_description="x", status="completed")
      )

      assert legacy_path.read_text(encoding="utf-8") == "# stale pre-migration snapshot\n"
      assert (tmp_path / ".meta-viz" / "progress" / "current.md").exists()


  def test_gitignore_already_covers_meta_viz_progress_without_a_new_entry():
      gitignore = (_REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
      lines = [l.strip() for l in gitignore.splitlines()]
      assert ".meta-viz/" in lines, (
          "the existing generic .meta-viz/ entry must keep covering "
          ".meta-viz/progress/ -- if this line is ever narrowed, a "
          "dedicated .meta-viz/progress/ entry must be added at the same time"
      )
  ```

- [ ] **Step 2: Run it**

  Run: `pytest tests/test_progress_file_migration.py -v`
  Expected: PASS immediately — regression guard, not a bug fix (Task 1 already made the old path a dead constant).

- [ ] **Step 3: Commit**

  ```bash
  git add tests/test_progress_file_migration.py
  git commit -m "test: guard rollout invariants for the progress-file path migration"
  ```

---

### Task 5: `CheckpointStore.agent_meta_root` + Tier resolver

**Files:**
- Modify: `scripts/lib/checkpoint.py` (imports, `CheckpointStore.__init__`, new `_active_providers`/`_progress_tier` functions)
- Create: `tests/test_progress_tier_resolution.py`

**Interfaces:**
- Consumes: `providers.load_providers_config`, `providers.resolve_providers`, `providers.provider_hooks_supported` (`scripts/lib/providers.py`, unchanged signatures); `io._load_yaml_or_json` (`scripts/lib/io.py`, unchanged signature).
- Produces: `CheckpointStore(project_root=..., agent_meta_root=...)` (new optional kwarg, defaults to `project_root`) and `_progress_tier(project_root: Path, agent_meta_root: Path) -> str` (`"A"` or `"B"`) — consumed by Task 6's `_write_progress_file`.

- [ ] **Step 1: Write the failing tests**

  Create `tests/test_progress_tier_resolution.py`:

  ```python
  """Tier resolution for the progress file (design doc
  2026-09-10-live-progress-channel-design.md, Architecture §1): Tier A only
  when EVERY active provider has a verified hook_protocol."""

  import sys
  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(_REPO_ROOT / "scripts"))

  from lib.checkpoint import _progress_tier  # noqa: E402


  def test_tier_a_when_no_project_yaml_defaults_to_claude(tmp_path):
      # No .meta-config/project.yaml at all -- resolve_providers() falls back
      # to "Claude" (its own documented default), which has a verified
      # hook_protocol -- Tier A. Matches the pre-existing overwrite tests that
      # use a bare tmp_path with no project.yaml (Task 1).
      assert _progress_tier(tmp_path, _REPO_ROOT) == "A"


  def test_tier_b_for_hookless_provider(tmp_path):
      (tmp_path / ".meta-config").mkdir()
      (tmp_path / ".meta-config" / "project.yaml").write_text(
          "ai-providers: [Opencode]\n", encoding="utf-8"
      )
      assert _progress_tier(tmp_path, _REPO_ROOT) == "B"


  def test_mixed_provider_set_falls_back_to_tier_b(tmp_path):
      (tmp_path / ".meta-config").mkdir()
      (tmp_path / ".meta-config" / "project.yaml").write_text(
          "ai-providers: [Claude, Opencode]\n", encoding="utf-8"
      )
      assert _progress_tier(tmp_path, _REPO_ROOT) == "B"


  def test_tier_a_for_gemini_alone(tmp_path):
      (tmp_path / ".meta-config").mkdir()
      (tmp_path / ".meta-config" / "project.yaml").write_text(
          "ai-providers: [Gemini]\n", encoding="utf-8"
      )
      assert _progress_tier(tmp_path, _REPO_ROOT) == "A"
  ```

- [ ] **Step 2: Run, confirm FAIL**

  Run: `pytest tests/test_progress_tier_resolution.py -v`
  Expected: FAIL with `ImportError: cannot import name '_progress_tier'`.

- [ ] **Step 3: Implement in `checkpoint.py`**

  Add imports (top of `scripts/lib/checkpoint.py`, next to the existing `.io`/`.json_persistence` imports):

  ```python
  from .io import _load_yaml_or_json, write_atomic
  from .providers import load_providers_config, provider_hooks_supported, resolve_providers
  ```

  Add module-level functions (below `_PROGRESS_DIR`):

  ```python
  def _active_providers(project_root: Path, agent_meta_root: Path) -> list:
      """Resolve active providers for tier detection. Falls back to the same
      "Claude" default resolve_providers() itself uses when no project.yaml
      is found -- matches the pre-existing CheckpointStore test fixtures that
      use a bare tmp_path with no .meta-config/project.yaml (Task 1).
      """
      config, _ = _load_yaml_or_json(project_root / ".meta-config" / "project.yaml")
      provider_config = load_providers_config(agent_meta_root)
      return resolve_providers(config or {}, provider_config)


  def _progress_tier(project_root: Path, agent_meta_root: Path) -> str:
      """Tier "A" (overwrite + chat push) only when EVERY active provider has
      a verified hook_protocol (providers.provider_hooks_supported) -- design
      doc 2026-09-10-live-progress-channel-design.md, Architecture §1. A
      mixed Tier-A/Tier-B provider set falls back to Tier B (append) so no
      provider silently loses its only progress signal.
      """
      provider_config = load_providers_config(agent_meta_root)
      active = _active_providers(project_root, agent_meta_root)
      if active and all(provider_hooks_supported(provider_config.get(p, {})) for p in active):
          return "A"
      return "B"
  ```

  Update `CheckpointStore.__init__` (`checkpoint.py:132-134`):

  ```python
      def __init__(self, project_root: Path | str | None = None, agent_meta_root: Path | str | None = None):
          self.project_root = Path(project_root) if project_root else Path.cwd()
          self.agent_meta_root = Path(agent_meta_root) if agent_meta_root else self.project_root
          self.checkpoint_dir = self.project_root / CHECKPOINT_DIR
  ```

- [ ] **Step 4: Run, confirm PASS**

  Run: `pytest tests/test_progress_tier_resolution.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**

  ```bash
  git add scripts/lib/checkpoint.py tests/test_progress_tier_resolution.py
  git commit -m "feat: resolve progress-file Tier A/B from active provider capabilities"
  ```

---

### Task 6: Tier A/B branching + Tier-B append & rotation in `_write_progress_file`

**Files:**
- Modify: `scripts/lib/checkpoint.py` (`_write_progress_file`, new `_render_progress_entry`, `_trim_oldest_entries`, `_PROGRESS_MAX_BYTES`, `_ENTRY_MARKER`)
- Create: `tests/test_progress_file_tier_b_append.py`

**Interfaces:**
- Consumes: `_progress_tier` (Task 5), `_render_progress_markdown` (unchanged Tier-A path).
- Produces: `_render_progress_entry(session_id: str, checkpoint: dict) -> str` (single-entry Tier-B block) and `_PROGRESS_MAX_BYTES` (module constant, monkeypatchable in tests) — consumed by Task 8's pipeline/stage rendering.

- [ ] **Step 1: Write the failing tests**

  Create `tests/test_progress_file_tier_b_append.py`:

  ```python
  """Tier-B append + rotation for the progress file (design doc
  2026-09-10-live-progress-channel-design.md, Architecture §1)."""

  import sys
  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(_REPO_ROOT / "scripts"))

  from lib import checkpoint as checkpoint_lib  # noqa: E402
  from lib.checkpoint import Checkpoint, CheckpointStore  # noqa: E402


  def _tier_b_store(tmp_path: Path) -> CheckpointStore:
      (tmp_path / ".meta-config").mkdir()
      (tmp_path / ".meta-config" / "project.yaml").write_text(
          "ai-providers: [Opencode]\n", encoding="utf-8"
      )
      return CheckpointStore(project_root=tmp_path, agent_meta_root=_REPO_ROOT)


  def test_tier_b_appends_both_checkpoints(tmp_path):
      store = _tier_b_store(tmp_path)
      store.save_checkpoint(
          "sess1", Checkpoint(task_id="t1", agent="developer", task_description="first", status="completed")
      )
      store.save_checkpoint(
          "sess1", Checkpoint(task_id="t2", agent="tester", task_description="second", status="in_progress")
      )
      content = (tmp_path / ".meta-viz" / "progress" / "current.md").read_text(encoding="utf-8")
      assert "first" in content
      assert "second" in content
      assert content.count("| Agent | Task | Status | Pipeline/Stage |") == 2


  def test_tier_b_rotates_on_new_session(tmp_path):
      store = _tier_b_store(tmp_path)
      store.save_checkpoint(
          "sessA", Checkpoint(task_id="t1", agent="developer", task_description="session-a-entry", status="completed")
      )
      store.save_checkpoint(
          "sessB", Checkpoint(task_id="t1", agent="developer", task_description="session-b-entry", status="completed")
      )
      content = (tmp_path / ".meta-viz" / "progress" / "current.md").read_text(encoding="utf-8")
      assert "session-a-entry" not in content
      assert "session-b-entry" in content


  def test_tier_b_trims_oldest_entries_over_byte_budget(tmp_path, monkeypatch):
      monkeypatch.setattr(checkpoint_lib, "_PROGRESS_MAX_BYTES", 500)
      store = _tier_b_store(tmp_path)
      for i in range(20):
          store.save_checkpoint(
              "sess1", Checkpoint(task_id=f"t{i}", agent="developer", task_description=f"entry-{i}", status="in_progress")
          )
      content = (tmp_path / ".meta-viz" / "progress" / "current.md").read_text(encoding="utf-8")
      assert len(content.encode("utf-8")) <= 500
      assert "entry-19" in content
      assert "entry-0" not in content
  ```

- [ ] **Step 2: Run, confirm FAIL**

  Run: `pytest tests/test_progress_file_tier_b_append.py -v`
  Expected: FAIL — `_write_progress_file` still unconditionally overwrites via `_render_progress_markdown`.

- [ ] **Step 3: Implement in `checkpoint.py`**

  Add near `_PROGRESS_DIR`:

  ```python
  _PROGRESS_MAX_BYTES = 200_000  # ~4x the 50 KB JSON-checkpoint budget (checkpointing.md) --
                                  # rendered markdown entries run more verbose per checkpoint.
  _ENTRY_MARKER = "\n## "
  ```

  Add a single-entry renderer (below `_render_progress_markdown`):

  ```python
  def _render_progress_entry(session_id: str, checkpoint: dict) -> str:
      """Render ONE checkpoint as a Tier-B append block (design doc
      2026-09-10, Architecture §1). Unlike _render_progress_markdown
      (Tier A, whole-session cumulative table), this renders only the
      newest checkpoint so appending it never duplicates entries already
      on disk. Always starts with _ENTRY_MARKER so _trim_oldest_entries
      can split entries unambiguously.
      """
      agent = checkpoint.get("agent", "?")
      task = checkpoint.get("task_description", "?")
      status = checkpoint.get("status", "?")
      pipeline = checkpoint.get("pipeline")
      stage = checkpoint.get("stage")
      pipeline_cell = f"{pipeline} / {stage}" if pipeline and stage else (pipeline or "")
      ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(checkpoint.get("timestamp") or time.time()))
      return (
          f"{_ENTRY_MARKER}{ts} — session `{session_id}`\n\n"
          f"| Agent | Task | Status | Pipeline/Stage |\n"
          f"|-------|------|--------|----------------|\n"
          f"| `{agent}` | {task} | `{status}` | {pipeline_cell} |\n"
      )


  def _trim_oldest_entries(content: str, max_bytes: int) -> str:
      """Drop oldest Tier-B entries (see _render_progress_entry) from the
      front until content fits max_bytes. Always keeps at least the newest
      entry, even if that single entry alone exceeds max_bytes -- never
      truncates mid-entry, which would produce broken markdown.
      """
      if len(content.encode("utf-8")) <= max_bytes:
          return content
      entries = content.split(_ENTRY_MARKER)[1:]  # [0] is the "" prefix before the first marker
      while len(entries) > 1 and len("".join(_ENTRY_MARKER + e for e in entries).encode("utf-8")) > max_bytes:
          entries.pop(0)
      return "".join(_ENTRY_MARKER + e for e in entries)
  ```

  Replace `_write_progress_file` (`checkpoint.py:235-239`):

  ```python
      def _write_progress_file(self, session_data: dict) -> None:
          """Write .meta-viz/progress/current.md -- see _render_progress_markdown
          and _render_progress_entry. Tier A: overwrite (unchanged pre-existing
          behavior). Tier B: append the newest checkpoint only, with a rotation
          reset on the first checkpoint of a new session, and a running byte
          cap (design doc 2026-09-10, Architecture §1).
          """
          progress_path = self.project_root / _PROGRESS_DIR / "current.md"
          progress_path.parent.mkdir(parents=True, exist_ok=True)
          tier = _progress_tier(self.project_root, self.agent_meta_root)
          if tier == "A":
              write_atomic(progress_path, _render_progress_markdown(session_data))
              return
          checkpoints = session_data.get("checkpoints", [])
          latest = checkpoints[-1] if checkpoints else {}
          entry = _render_progress_entry(session_data.get("session_id", "unknown"), latest)
          is_new_session = len(checkpoints) == 1
          existing = "" if is_new_session or not progress_path.exists() else progress_path.read_text(encoding="utf-8")
          combined = existing + entry
          combined = _trim_oldest_entries(combined, _PROGRESS_MAX_BYTES)
          write_atomic(progress_path, combined)
  ```

- [ ] **Step 4: Run, confirm PASS**

  Run: `pytest tests/test_progress_file_tier_b_append.py tests/test_progress_file.py tests/test_progress_file_migration.py -v`
  Expected: all PASS (Tier-A tests in `test_progress_file.py` still pass unchanged since their bare-`tmp_path` fixture resolves to Tier A per Task 5).

- [ ] **Step 5: Commit**

  ```bash
  git add scripts/lib/checkpoint.py tests/test_progress_file_tier_b_append.py
  git commit -m "feat: Tier-B progress file appends with session-start rotation + byte cap"
  ```

---

### Task 7: Scenario 46 — Tier-B append + rotation

**Files:**
- Create: `tests/scenarios/configs/46-progress-tierb-append-rotation.project.yaml`
- Create: `tests/scenarios/asserts/46-progress-tierb-append-rotation.sh` (executable)

**Interfaces:**
- Consumes: `CheckpointStore`/`Checkpoint` from Task 6 (real library import inside the assert script, same pattern as Task 3).
- Produces: nothing consumed by later tasks. (Registry row already added in Task 3, Step 3.)

- [ ] **Step 1: Create the scenario config**

  `tests/scenarios/configs/46-progress-tierb-append-rotation.project.yaml`:

  ```yaml
  agent-meta-version: 0.101.0
  ai-providers:
  - Opencode
  dod-preset: standard
  platforms: []
  roles:
  - orchestrator
  - developer
  - git
  orchestrator:
    mode: strict
    checkpointing: true
  project:
    name: scenario-progress-tierb
    prefix: s46
    short: scenario-progress-tierb
  variables:
    PROJECT_NAME: scenario-progress-tierb
    PROJECT_DESCRIPTION: Tier-B append+rotation progress-file behavior (live-progress-channel design, 2026-09-10).
    PROJECT_GOAL: Verify CheckpointStore appends (not overwrites) progress entries and rotates on new session for hook-less providers.
    GIT_PLATFORM: GitHub
    GIT_REMOTE_URL: https://github.com/example/scenario-progress-tierb
    GIT_MAIN_BRANCH: main
  rules-preset: default
  speech-mode: full
  tier-preset: Normal
  se-focus: false
  max-parallel-agents: 2
  conventions-preset: default
  debug-mode: false
  allow-committed-secrets: false
  ```

- [ ] **Step 2: Create the assert script**

  `tests/scenarios/asserts/46-progress-tierb-append-rotation.sh` (`chmod +x`):

  ```bash
  #!/bin/bash
  # Scenario assert for 46-progress-tierb-append-rotation
  set -u

  REPO_ROOT="${1:-${REPO_ROOT:-}}"
  if [ -z "$REPO_ROOT" ]; then
      echo "ASSERT ERROR (46-progress-tierb-append-rotation): REPO_ROOT missing (pass as \$1 or env var)"
      exit 2
  fi

  fail() {
      echo "ASSERT FAIL (46-progress-tierb-append-rotation): $*"
      exit 1
  }

  python3 - "$REPO_ROOT" <<'PYEOF' || fail "python check failed"
  import sys
  from pathlib import Path

  repo_root = Path(sys.argv[1])
  sys.path.insert(0, str(repo_root / "scripts"))
  from lib.checkpoint import Checkpoint, CheckpointStore

  store = CheckpointStore(project_root=Path("."), agent_meta_root=repo_root)
  store.save_checkpoint(
      "sessA", Checkpoint(task_id="t1", agent="developer", task_description="first-entry", status="completed")
  )
  store.save_checkpoint(
      "sessA", Checkpoint(task_id="t2", agent="tester", task_description="second-entry", status="in_progress")
  )
  content = Path(".meta-viz/progress/current.md").read_text(encoding="utf-8")
  assert "first-entry" in content, "tier-B must append the first checkpoint"
  assert "second-entry" in content, "tier-B must append the second checkpoint"
  assert content.count("| Agent | Task | Status | Pipeline/Stage |") == 2, (
      "tier-B must render one table per appended entry, not overwrite"
  )

  store.save_checkpoint(
      "sessB", Checkpoint(task_id="t1", agent="developer", task_description="rotated-entry", status="completed")
  )
  content = Path(".meta-viz/progress/current.md").read_text(encoding="utf-8")
  assert "first-entry" not in content, "a new session's first checkpoint must rotate (clear) the tier-B file"
  assert "rotated-entry" in content
  PYEOF

  echo "ASSERT OK (46-progress-tierb-append-rotation): tier-B append + rotation verified"
  ```

- [ ] **Step 3: Run the scenario**

  Run: `tests/scenarios/run.sh 46`
  Expected: `PASS`

- [ ] **Step 4: Commit**

  ```bash
  git add tests/scenarios/configs/46-progress-tierb-append-rotation.project.yaml \
          tests/scenarios/asserts/46-progress-tierb-append-rotation.sh
  git commit -m "test: scenario 46 — tier-B progress append + rotation"
  ```

---

### Task 8: Pipeline/Stage field on `Checkpoint`

**Files:**
- Modify: `scripts/lib/checkpoint.py` (`Checkpoint.__init__`, `to_dict`, `from_dict`, `_render_progress_markdown`)
- Create: `tests/test_progress_pipeline_field.py`

**Interfaces:**
- Consumes: `_render_progress_entry`/`_render_progress_markdown` (Tasks 6, existing) — both already read `checkpoint.get("pipeline")`/`checkpoint.get("stage")` per Task 6's implementation, so this task only has to make `Checkpoint` actually populate those keys.
- Produces: `Checkpoint(..., pipeline: str | None = None, stage: str | None = None)` — consumed by Task 9's scenario and Task 11's orchestrator instructions (documentation only, no code dependency).

- [ ] **Step 1: Write the failing tests**

  Create `tests/test_progress_pipeline_field.py`:

  ```python
  """Checkpoint.pipeline/.stage fields (design doc 2026-09-10-live-progress-
  channel-design.md, Architecture §3): optional, backward compatible."""

  import sys
  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(_REPO_ROOT / "scripts"))

  from lib.checkpoint import Checkpoint  # noqa: E402


  def test_pipeline_and_stage_round_trip_through_to_dict_from_dict():
      cp = Checkpoint(
          task_id="t1", agent="se-requirements", task_description="L1 REQs",
          status="in_progress", pipeline="se-cascade", stage="l1-requirements",
      )
      restored = Checkpoint.from_dict(cp.to_dict())
      assert restored.pipeline == "se-cascade"
      assert restored.stage == "l1-requirements"


  def test_pipeline_and_stage_default_to_none():
      cp = Checkpoint(task_id="t1", agent="developer", task_description="x", status="pending")
      assert cp.pipeline is None
      assert cp.stage is None


  def test_from_dict_without_pipeline_keys_does_not_crash():
      # Simulates a checkpoint JSON written before this field existed.
      legacy_dict = {
          "task_id": "t1", "agent": "developer", "task_description": "x",
          "status": "completed",
      }
      restored = Checkpoint.from_dict(legacy_dict)
      assert restored.pipeline is None
      assert restored.stage is None
  ```

- [ ] **Step 2: Run, confirm FAIL**

  Run: `pytest tests/test_progress_pipeline_field.py -v`
  Expected: FAIL — `Checkpoint.__init__` doesn't accept `pipeline`/`stage`.

- [ ] **Step 3: Implement in `checkpoint.py`**

  Update `Checkpoint.__init__` (`checkpoint.py:79-98`):

  ```python
      def __init__(
          self,
          task_id: str,
          agent: str,
          task_description: str,
          status: str,  # "pending", "in_progress", "completed", "failed"
          result: str | None = None,
          next_step: str | None = None,
          status_summary: str | None = None,
          pipeline: str | None = None,
          stage: str | None = None,
          timestamp: float | None = None,
      ):
          self.id = str(uuid.uuid4())
          self.task_id = task_id
          self.agent = agent
          self.task_description = task_description
          self.status = status
          self.result = result
          self.next_step = next_step
          self.status_summary = status_summary
          self.pipeline = pipeline
          self.stage = stage
          self.timestamp = timestamp or time.time()
  ```

  Update `to_dict` (`checkpoint.py:100-111`):

  ```python
      def to_dict(self) -> dict:
          return {
              "id": self.id,
              "task_id": self.task_id,
              "agent": self.agent,
              "task_description": self.task_description,
              "status": self.status,
              "result": self.result,
              "next_step": self.next_step,
              "status_summary": self.status_summary,
              "pipeline": self.pipeline,
              "stage": self.stage,
              "timestamp": self.timestamp,
          }
  ```

  Update `from_dict` (`checkpoint.py:113-126`):

  ```python
      @classmethod
      def from_dict(cls, data: dict) -> "Checkpoint":
          cp = cls(
              task_id=data["task_id"],
              agent=data["agent"],
              task_description=data["task_description"],
              status=data["status"],
              result=data.get("result"),
              next_step=data.get("next_step"),
              status_summary=data.get("status_summary"),
              pipeline=data.get("pipeline"),
              stage=data.get("stage"),
              timestamp=data.get("timestamp"),
          )
          cp.id = data.get("id", cp.id)
          return cp
  ```

  Update `_render_progress_markdown` (`checkpoint.py:65-71`, Tier-A cumulative table) to add the same `Pipeline/Stage` column `_render_progress_entry` already renders (Task 6):

  ```python
      lines.append("| Agent | Task | Status | Pipeline/Stage |")
      lines.append("|-------|------|--------|----------------|")
      for cp in checkpoints:
          agent = cp.get("agent", "?")
          task = cp.get("task_description", "?")
          status = cp.get("status", "?")
          pipeline = cp.get("pipeline")
          stage = cp.get("stage")
          pipeline_cell = f"{pipeline} / {stage}" if pipeline and stage else (pipeline or "")
          lines.append(f"| `{agent}` | {task} | `{status}` | {pipeline_cell} |")
  ```

- [ ] **Step 4: Run, confirm PASS**

  Run: `pytest tests/test_progress_pipeline_field.py tests/test_checkpoint_status_summary.py tests/test_progress_file.py -v`
  Expected: all PASS (the `| Agent | Task | Status |` substring count assertion in `test_progress_file.py` still passes — it's a prefix of the new 4-column header).

- [ ] **Step 5: Commit**

  ```bash
  git add scripts/lib/checkpoint.py tests/test_progress_pipeline_field.py
  git commit -m "feat: add Checkpoint.pipeline/.stage fields + Pipeline/Stage column"
  ```

---

### Task 9: Scenario 47 — Pipeline/Stage field distinguishes concurrent pipelines

**Files:**
- Create: `tests/scenarios/configs/47-progress-pipeline-stage-field.project.yaml`
- Create: `tests/scenarios/asserts/47-progress-pipeline-stage-field.sh` (executable)

**Interfaces:**
- Consumes: `Checkpoint(pipeline=, stage=)` (Task 8) + Tier-B append (Task 6) — both required for this scenario's assertion (Tier A would overwrite and only show the last-saved session, which is the acknowledged v1 limitation documented in the spec's Risks section, not what this scenario tests).
- Produces: nothing consumed by later tasks. (Registry row already added in Task 3, Step 3.)

- [ ] **Step 1: Create the scenario config** (Opencode = Tier B, so both simulated pipelines' entries coexist in the appended file)

  `tests/scenarios/configs/47-progress-pipeline-stage-field.project.yaml`:

  ```yaml
  agent-meta-version: 0.101.0
  ai-providers:
  - Opencode
  dod-preset: standard
  platforms: []
  roles:
  - orchestrator
  - developer
  - git
  orchestrator:
    mode: strict
    checkpointing: true
  project:
    name: scenario-progress-pipeline-field
    prefix: s47
    short: scenario-progress-pipeline
  variables:
    PROJECT_NAME: scenario-progress-pipeline-field
    PROJECT_DESCRIPTION: Pipeline/Stage field distinguishes concurrent se-cascade / concept-driven-dev entries (live-progress-channel design, 2026-09-10).
    PROJECT_GOAL: Verify two concurrently running pipelines produce distinguishable Pipeline/Stage cells in the shared tier-B progress file.
    GIT_PLATFORM: GitHub
    GIT_REMOTE_URL: https://github.com/example/scenario-progress-pipeline
    GIT_MAIN_BRANCH: main
  rules-preset: default
  speech-mode: full
  tier-preset: Normal
  se-focus: false
  max-parallel-agents: 2
  conventions-preset: default
  debug-mode: false
  allow-committed-secrets: false
  ```

- [ ] **Step 2: Create the assert script**

  `tests/scenarios/asserts/47-progress-pipeline-stage-field.sh` (`chmod +x`):

  ```bash
  #!/bin/bash
  # Scenario assert for 47-progress-pipeline-stage-field
  set -u

  REPO_ROOT="${1:-${REPO_ROOT:-}}"
  if [ -z "$REPO_ROOT" ]; then
      echo "ASSERT ERROR (47-progress-pipeline-stage-field): REPO_ROOT missing (pass as \$1 or env var)"
      exit 2
  fi

  fail() {
      echo "ASSERT FAIL (47-progress-pipeline-stage-field): $*"
      exit 1
  }

  python3 - "$REPO_ROOT" <<'PYEOF' || fail "python check failed"
  import sys
  from pathlib import Path

  repo_root = Path(sys.argv[1])
  sys.path.insert(0, str(repo_root / "scripts"))
  from lib.checkpoint import Checkpoint, CheckpointStore

  store = CheckpointStore(project_root=Path("."), agent_meta_root=repo_root)
  # Two independently running pipelines, simulated as two sessions -- tier-B
  # appends both, so a user tail -f-ing the file can distinguish them.
  store.save_checkpoint(
      "sess-se",
      Checkpoint(
          task_id="t1", agent="se-requirements", task_description="L1 REQs",
          status="in_progress", pipeline="se-cascade", stage="l1-requirements",
      ),
  )
  store.save_checkpoint(
      "sess-cdd",
      Checkpoint(
          task_id="t1", agent="concept-specifier", task_description="Spec draft",
          status="in_progress", pipeline="concept-driven-dev", stage="specify",
      ),
  )
  content = Path(".meta-viz/progress/current.md").read_text(encoding="utf-8")
  assert "se-cascade / l1-requirements" in content, "se-cascade entry must carry its Pipeline/Stage cell"
  assert "concept-driven-dev / specify" in content, "concept-driven-dev entry must carry its Pipeline/Stage cell"
  PYEOF

  echo "ASSERT OK (47-progress-pipeline-stage-field): concurrent pipelines distinguishable"
  ```

- [ ] **Step 3: Run the scenario**

  Run: `tests/scenarios/run.sh 47`
  Expected: `PASS`

- [ ] **Step 4: Commit**

  ```bash
  git add tests/scenarios/configs/47-progress-pipeline-stage-field.project.yaml \
          tests/scenarios/asserts/47-progress-pipeline-stage-field.sh
  git commit -m "test: scenario 47 — Pipeline/Stage field for concurrent pipelines"
  ```

---

### Task 10: `PROGRESS_CHAT_PUSH_ENABLED` sync variable

**Files:**
- Modify: `scripts/lib/config.py:40` (import), `scripts/lib/config.py:837-841` (`_build_orch_variables`)
- Modify: `scripts/lib/variables.py:108` (`conditional_vars`)
- Create: `tests/test_progress_chat_push_variable.py`

**Interfaces:**
- Consumes: `providers.provider_hooks_supported`, `providers.resolve_providers`, `providers.load_providers_config` (all unchanged, already imported in `config.py`).
- Produces: `variables["PROGRESS_CHAT_PUSH_ENABLED"]` (`"true"`/`"false"`) — consumed by Task 11's `{{#if PROGRESS_CHAT_PUSH_ENABLED}}` block in `agents/1-generic/orchestrator.md`.

- [ ] **Step 1: Write the failing tests**

  Create `tests/test_progress_chat_push_variable.py`:

  ```python
  """PROGRESS_CHAT_PUSH_ENABLED variable (design doc 2026-09-10-live-progress-
  channel-design.md, Architecture §1 Tier-A gate)."""

  import sys
  from pathlib import Path

  _REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(_REPO_ROOT / "scripts"))

  from lib.config import build_variables  # noqa: E402


  def _config(providers):
      return {
          "project": {"name": "t", "prefix": "t"},
          "ai-providers": providers,
          "roles": ["orchestrator", "developer"],
      }


  def test_true_for_claude_only():
      variables, _ = build_variables(_config(["Claude"]), _REPO_ROOT)
      assert variables["PROGRESS_CHAT_PUSH_ENABLED"] == "true"


  def test_false_for_opencode_only():
      variables, _ = build_variables(_config(["Opencode"]), _REPO_ROOT)
      assert variables["PROGRESS_CHAT_PUSH_ENABLED"] == "false"


  def test_false_for_mixed_claude_and_opencode():
      variables, _ = build_variables(_config(["Claude", "Opencode"]), _REPO_ROOT)
      assert variables["PROGRESS_CHAT_PUSH_ENABLED"] == "false"
  ```

- [ ] **Step 2: Run, confirm FAIL**

  Run: `pytest tests/test_progress_chat_push_variable.py -v`
  Expected: FAIL with `KeyError: 'PROGRESS_CHAT_PUSH_ENABLED'`.

- [ ] **Step 3: Implement in `config.py`**

  Update the import at `scripts/lib/config.py:40`:

  ```python
  from .providers import load_providers_config, provider_hooks_supported, resolve_providers
  ```

  Insert right after the `CHECKPOINTING_ENABLED` assignment (`config.py:839-841`, inside `_build_orch_variables`):

  ```python
      # PROGRESS_CHAT_PUSH_ENABLED (design doc 2026-09-10-live-progress-channel-
      # design.md, Architecture §1 Tier A): true only when EVERY active
      # provider has a verified hook_protocol (providers.provider_hooks_supported)
      # -- gates the Tier-A "also SendMessage(to:"main")" instruction in
      # orchestrator.md §7 so hook-less providers never see an instruction
      # they cannot follow.
      _pcpe_provider_config = load_providers_config(agent_meta_root)
      _pcpe_active = resolve_providers(config, _pcpe_provider_config)
      variables["PROGRESS_CHAT_PUSH_ENABLED"] = (
          "true"
          if _pcpe_active and all(
              provider_hooks_supported(_pcpe_provider_config.get(p, {})) for p in _pcpe_active
          )
          else "false"
      )
  ```

- [ ] **Step 4: Register as a conditional variable**

  In `scripts/lib/variables.py:108`, add `"PROGRESS_CHAT_PUSH_ENABLED"` to the set literal:

  ```python
  conditional_vars.update({k for k in variables if k in ("ORCHESTRATOR_ENABLED", "ORCHESTRATOR_STRICT", "DIRECT_DISPATCH_ENABLED", "UNKNOWN_FALLBACK_ASK_USER", "UNKNOWN_FALLBACK_META_FEEDBACK", "UNKNOWN_FALLBACK_MAIN_CHAT", "A2A_PROTOCOL_ENABLED", "ORCHESTRATOR_OUTCOME_CACHING", "CHECKPOINTING_ENABLED", "NATIVE_EXTENSIONS_ENABLED", "NATIVE_EXTENSIONS_WHITELIST_ACTIVE", "ANALYSIS_ENABLED", "FILE_BASED_AGENTS", "AUTO_COMMIT_ENABLED", "PROGRESS_CHAT_PUSH_ENABLED")})
  ```

- [ ] **Step 5: Run, confirm PASS**

  Run: `pytest tests/test_progress_chat_push_variable.py -v`
  Expected: PASS

- [ ] **Step 6: Commit**

  ```bash
  git add scripts/lib/config.py scripts/lib/variables.py tests/test_progress_chat_push_variable.py
  git commit -m "feat: add PROGRESS_CHAT_PUSH_ENABLED sync variable"
  ```

---

### Task 11: Tier-A `SendMessage` push instruction in `orchestrator.md`

**Files:**
- Modify: `agents/1-generic/orchestrator.md:158` (§7, right after `{{STATUS_TABLE_BLOCK}}`)
- Modify: `tests/test_progress_file_documented.py` (append one more test function)

**Interfaces:**
- Consumes: `PROGRESS_CHAT_PUSH_ENABLED` (Task 10).
- Produces: nothing consumed by later tasks — closes out the concretely implementable part of the plan (Task 12 is a verification task, not new code).

- [ ] **Step 1: Extend the doc test**

  Append to `tests/test_progress_file_documented.py`:

  ```python
  def test_orchestrator_section_7_documents_tier_a_chat_push():
      content = (_REPO_ROOT / "agents" / "1-generic" / "orchestrator.md").read_text(encoding="utf-8")
      section_7_start = content.index("## 7. BARRIER protocol")
      section_8_start = content.index("## 8. Reflection loop")
      section_7 = content[section_7_start:section_8_start]
      assert "PROGRESS_CHAT_PUSH_ENABLED" in section_7
      assert 'SendMessage(to:"main"' in section_7
  ```

- [ ] **Step 2: Run, confirm FAIL**

  Run: `pytest tests/test_progress_file_documented.py::test_orchestrator_section_7_documents_tier_a_chat_push -v`
  Expected: FAIL — §7 doesn't mention either string yet.

- [ ] **Step 3: Edit `agents/1-generic/orchestrator.md`**

  Insert right after `{{STATUS_TABLE_BLOCK}}` (line 158), before the `Artifact pattern` paragraph:

  ```markdown
  {{#if PROGRESS_CHAT_PUSH_ENABLED}}
  **Tier-A chat push (live-progress-channel design, 2026-09-10):** on this hook-capable provider, additionally call `SendMessage(to:"main", content:<the status table above>)` once per batch-member completion / BARRIER cycle — same cadence as the status table above, never per individual tool call.
  {{/if}}
  ```

- [ ] **Step 4: Run, confirm PASS**

  Run: `pytest tests/test_progress_file_documented.py -v`
  Expected: PASS (all functions in the file, including the two updated in Task 2).

- [ ] **Step 5: Run the full progress-file test surface once more**

  Run: `pytest tests/test_progress_file.py tests/test_progress_file_documented.py tests/test_progress_file_migration.py tests/test_progress_tier_resolution.py tests/test_progress_file_tier_b_append.py tests/test_progress_pipeline_field.py tests/test_progress_chat_push_variable.py tests/test_checkpoint_status_summary.py tests/test_checkpoint_raw_output.py -v`
  Expected: all PASS.

- [ ] **Step 6: Commit**

  ```bash
  git add agents/1-generic/orchestrator.md tests/test_progress_file_documented.py
  git commit -m "feat: Tier-A SendMessage push instruction in orchestrator §7"
  ```

---

### Task 12: Gemini `send_message` push verification (spec open point #1)

**Files:**
- No source files modified as part of writing this plan — this task's *output* is a decision that lands in one of two pre-written follow-up edits below, executed by whichever branch the verification confirms.

**Interfaces:**
- Consumes: `PROGRESS_CHAT_PUSH_ENABLED` (Task 10), `provider_hooks_supported` (`scripts/lib/providers.py`).
- Produces: either "no change" (Gemini confirmed) or a one-line predicate narrowing (Gemini demoted to Tier-B-only for the chat-push half, file-write half unaffected).

- [ ] **Step 1: Run the verification dispatch**

  In a project with `ai-providers: [Gemini]` synced (e.g. re-run `tests/scenarios/run.sh` with a temporary `ai-providers: [Gemini]` override of any existing scenario config, or a fresh manual project), dispatch a background orchestrator subagent via the Gemini/Antigravity harness that, mid-run, calls `send_message` targeting the parent/main thread with a short marker string (e.g. `"live-progress-channel verification ping"`).

- [ ] **Step 2: Observe the result**

  Check whether the marker string arrives in the main/parent conversation **while the background dispatch is still running** (a true push) versus only appearing bundled into the final aggregated subagent report (delegation-only, per the existing documented concern in `docs/concepts/active/singleton-orchestrator-architecture.md:354`).

- [ ] **Step 3a: If confirmed as a real push — no code change**

  Document the finding as a one-line addendum under the spec's "Offene Implementierungspunkte" section 1 (`docs/superpowers/specs/2026-09-10-live-progress-channel-design.md`):

  ```markdown
  **Verified 2026-09-10 (post-implementation):** `send_message` confirmed as a real push-to-parent
  channel on Gemini/Antigravity — Tier A stands for Gemini unchanged.
  ```

- [ ] **Step 3b: If confirmed as delegation-only — narrow the Tier-A predicate**

  Modify `scripts/lib/providers.py::provider_hooks_supported` is **not** touched (it stays the general Tier-A-for-file-writing predicate — Gemini keeps Tier-A overwrite behavior for the file). Instead, narrow only the chat-push variable in `scripts/lib/config.py`'s `PROGRESS_CHAT_PUSH_ENABLED` block (Task 10) to exclude Gemini specifically via a **new capability flag**, not a literal name check:

  ```yaml
  # config/ai-providers.yaml, Gemini entry
  send_message_push_to_parent: false  # verified 2026-09-10: delegation-only, see live-progress-channel-design.md open point 1
  ```

  ```python
  # scripts/lib/config.py, PROGRESS_CHAT_PUSH_ENABLED block (Task 10)
  variables["PROGRESS_CHAT_PUSH_ENABLED"] = (
      "true"
      if _pcpe_active and all(
          provider_hooks_supported(_pcpe_provider_config.get(p, {}))
          and _pcpe_provider_config.get(p, {}).get("send_message_push_to_parent", True)
          for p in _pcpe_active
      )
      else "false"
  )
  ```

  Add a regression test to `tests/test_progress_chat_push_variable.py`:

  ```python
  def test_false_for_gemini_if_push_capability_flag_is_false():
      # Only meaningful if Step 3b's finding applies -- config/ai-providers.yaml
      # must carry send_message_push_to_parent: false for Gemini at that point.
      variables, _ = build_variables(_config(["Gemini"]), _REPO_ROOT)
      assert variables["PROGRESS_CHAT_PUSH_ENABLED"] == "false"
  ```

- [ ] **Step 4: Commit whichever branch applied**

  ```bash
  git add docs/superpowers/specs/2026-09-10-live-progress-channel-design.md
  # and, only for branch 3b:
  git add config/ai-providers.yaml scripts/lib/config.py tests/test_progress_chat_push_variable.py
  git commit -m "docs: verify Gemini send_message push capability (live-progress-channel open point 1)"
  ```

---

## Self-Review

**1. Spec coverage:**

- Problem/Root-cause (`.claude/progress` hardcoded, provider-blind) → Task 1.
- Provider-Fähigkeitsmatrix / Tier A vs. Tier B → Task 5 (`_progress_tier`), reusing the existing `providers.provider_hooks_supported` predicate instead of hardcoding Claude/Gemini.
- Tier A: overwrite unchanged + chat push → Task 6 (overwrite branch preserved) + Task 10/11 (`PROGRESS_CHAT_PUSH_ENABLED` + `SendMessage` instruction).
- Tier B: append + rotation → Task 6 + Scenario 46 (Task 7).
- Root-cause fix decision (Option b, `.meta-viz/progress/`) → Task 1, exact path `.meta-viz/progress/current.md` used verbatim throughout, including Scenario 48 (Task 3).
- Planungspipeline-Anbindung (Pipeline/Stage field) → Task 8 + Scenario 47 (Task 9).
- Betroffene Dateien: `checkpoint.py` ✓ (Tasks 1/5/6/8), `orchestrator.md` ✓ (Tasks 2/11), `status-table.md` — explicitly untouched per Nicht-Ziele ✓, hook configuration (`.claude/settings.json`/Gemini `hooks.json`) — no shell-hook wiring exists for `CheckpointStore.save_checkpoint()` yet (confirmed: no call site in `scripts/lib/orchestration.py` as of this plan, `tests/scenarios/registry.md`'s own "Bewusste Auslassungen" note), so the Tier-A push is implemented at the prompt level (`SendMessage` instruction, Task 11) rather than as a new shell hook — consistent with the spec's own framing of `SendMessage(to:"main")` as something the orchestrator agent calls, not something a `PostToolUse` shell hook can trigger. `role-defaults.yaml` — explicitly no structural change needed per spec ✓, not touched.
- Rollout/Migration (old file untouched, no auto-migration, `.gitignore` already covers new path) → Task 4.
- Risks: chat-push frequency → addressed by cadence wording in Task 11 tied 1:1 to the existing status-table cadence; Gemini uncertain → Task 12; unbounded Tier-B growth → Task 6's byte cap; pipeline field ambiguity on parallel Tier-A sessions → explicitly called out as an accepted v1 limitation in Task 9's Interfaces note (not silently "fixed" beyond spec scope).
- Tests section (spec's own list): Pfadauflösung ✓ Task 1/3, Append/Overwrite ✓ Task 5/6, Rotation ✓ Task 6, Kadenz des Chat-Pushs — cadence is prompt-text now (Task 11), not a countable harness event, since no automatic call site exists yet to script a count against; documented as text-presence instead (`test_orchestrator_section_7_documents_tier_a_chat_push`), Pipeline/Stage-Szenario ✓ Task 9, Migration ✓ Task 4.
- Task-instruction's 3 mandatory scenarios: `46-progress-tierb-append-rotation` (Task 7), `47-progress-pipeline-stage-field` (Task 9), `48-progress-provider-neutral-path` (Task 3) — all embedded at the point their functionality is complete, all three registry rows added together in Task 3 Step 3 to keep the catalog table contiguous.

**2. Placeholder scan:** no "TBD"/"implement later"/"add appropriate error handling" strings anywhere above; Task 12 is the one task without pre-determined final code, but both of its possible outcomes (3a, 3b) are fully written out, not deferred.

**3. Type consistency:** `_progress_tier(project_root, agent_meta_root) -> str` (Task 5) is called identically in Task 6's `_write_progress_file`. `_render_progress_entry(session_id, checkpoint) -> str` (Task 6) and `_render_progress_markdown(session_data) -> str` (pre-existing, extended in Task 8) both read `checkpoint.get("pipeline")`/`checkpoint.get("stage")` — matching the exact dict keys `Checkpoint.to_dict()` produces after Task 8. `CheckpointStore(project_root=, agent_meta_root=)` kwarg names (Task 5) match every later `CheckpointStore(...)` call site in Tasks 6/7/9's test and scenario code. `PROGRESS_CHAT_PUSH_ENABLED` string is identical across Task 10 (producer) and Task 11 (template consumer) and Task 12's regression test.
