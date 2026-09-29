---
spec-id: SPEC-PROGRESS-PATHS-CONFIG-2026-09-13
title: Configurable Progress / Checkpoint Paths
status: APPROVED
related-spec: SPEC-PROGRESS-LEDGER-2026-09-13
---

# Configurable Progress / Checkpoint Paths — Technical Specification

> Status: APPROVED — this document is a specification only. It defines interface
> contracts and acceptance criteria; it contains no implementation. The final
> approval marker `Status: APPROVED` is set by `concept-reviewer` after re-review,
> never by this document.
> Trace anchor: `spec-id: SPEC-PROGRESS-PATHS-CONFIG-2026-09-13`.
> Related spec: `SPEC-PROGRESS-LEDGER-2026-09-13`
> (`docs/specs/2026-09-13-progress-ledger-system-design.md`) — this spec extends
> it and keeps its checkpoint identity, path and wiring decisions. It supersedes
> only the direct `CheckpointStore(project_root)` construction named there (see
> the recorded supersession in IC-04 and under Trace-Anker).

### Revision — incorporated review findings

| Finding | Change |
|---|---|
| F1 | Empty/whitespace-only vs. non-string unified: empty/whitespace-only resolves to the framework default with source `default` and no finding; only a non-string `type` mismatch yields a `safe-fallback` finding (IC-02, AC-05). |
| F2 | IC-02 import contract made implementable: `from .io import SyncError, _load_yaml_or_json` is an allowed import and the "only stdlib" phrasing is dropped (IC-02). |
| F3 | Supersession of the related spec's direct construction recorded: `from_config` supersedes `CheckpointStore(project_root)` at the named sites; behaviour identical for defaults (related-spec note, IC-04, Trace-Anker). |
| F4 | Problem bullet 1 reworded: the "only non-test consumer used to build a path" is `external_tools_drift.py:125`; `providers.py:87` merely supplies the fallback value (Problem). |
| F5 | Status marker kept at `DRAFT` in frontmatter and body; the document states that `concept-reviewer` sets the final marker (frontmatter/status block). |

## Problem

The progress / checkpoint store writes two hardcoded directories that a consuming
project cannot move:

- `scripts/lib/checkpoint.py:37` — `CHECKPOINT_DIR = ".meta-viz/checkpoints"`.
- `scripts/lib/checkpoint.py:41` — `_PROGRESS_DIR = ".meta-viz/progress"`.

`CheckpointStore.__init__` (`scripts/lib/checkpoint.py:324`) builds
`self.checkpoint_dir = self.project_root / CHECKPOINT_DIR` from the module
constant (`:334`), and `_write_progress_file` (`:473`) builds
`self.project_root / _PROGRESS_DIR / "current.md"` inline. There is no
`progress_dir` attribute. A project that wants to relocate its operational
progress data — for a separate mount, a different tooling root or a monorepo
layout — has no supported override; it must patch the template.

The `progress:` key does not exist in `.meta-config/project.yaml` today (only
`orchestrator.checkpointing: true` at `:312` and `viz.event_log` at `:321`);
`config/project-config.schema.json` has no top-level `progress` block. The
repository already has a proven resolver pattern for exactly this shape — a
framework default plus a project override, findings instead of exceptions, and a
traversal-safe path validator (`scripts/lib/repo_containment.py:321
resolve_effective_repo_containment` + `:189 tmp_sink_path_error`) — and a
best-effort project-config loader (`scripts/lib/recovery.py:83`, backed by
`scripts/lib/io.py:60`).

### Decision — the provider-scoped `checkpoint_dir` key (binding)

`config/ai-providers.yaml` carries `checkpoint_dir: .meta-viz` for all nine
providers and `scripts/lib/providers.py:87` repeats `.meta-viz` as the fallback
default. Recon evidence:

1. **No production code consumes it to build a path.** The only non-test
   consumer used to build a path is `scripts/lib/external_tools_drift.py:125`,
   where the key sits in `_INFRA_ROOT_KNOWN_KEYS`, a flat list of infra-root path
   keys used as metadata — not as a path source. `scripts/lib/providers.py:87`
   merely supplies `.meta-viz` as the fallback value; it does not turn the key
   into a path.
2. **Granularity mismatch.** The key is a *parent* directory (`.meta-viz`). The
   binding user decision introduces *child* directories
   (`.meta-viz/progress`, `.meta-viz/checkpoints`). Feeding `.meta-viz` into the
   new resolver would not produce either child path without inventing an
   undocumented naming convention on top of it.
3. **Pinned by a ratchet.** `tests/test_provider_hooks_config.py:192-199`
   asserts `pcfg.get("checkpoint_dir") == ".meta-viz"` for every provider, and
   the key is deliberately **excluded** from the provider-config collision sweep
   (`_COLLISION_PATH_KEYS` does not contain it) because the viz directory is
   shared infrastructure.

**Decision: option (b).** `checkpoint_dir` is treated as a vestigial,
provider-scoped metadata key and is **not** fed into the new resolver. The new
resolution path reads exactly one configuration source — the top-level
`progress:` block — over exactly one framework default set
(`.meta-viz/progress`, `.meta-viz/checkpoints`).

**Consequence — no contradictory double source exists.** The provider key is not
consulted at any point in resolution, so there is no second, competing source of
truth for the same path. The provider ratchet test is **not modified** by this
spec, and no provider-level path behaviour is introduced. Removal of the key is
explicitly out of scope (see Nicht-Ziele) and tracked as an open question.

## Ziel

Make the progress / checkpoint storage location configurable, with a framework
default and a project override, following the existing resolver conventions of
this repository:

1. **New top-level `progress:` block** in `.meta-config/project.yaml` with two
   optional string properties:
   - `dir` — progress-file directory; framework default `.meta-viz/progress`.
   - `checkpoint-dir` — checkpoint directory; framework default
     `.meta-viz/checkpoints`.
2. **One resolver** that turns `(project_root, config)` into resolved paths with
   precedence *explicit project value > framework default*, returning findings
   instead of raising (mirrors `resolve_effective_repo_containment`).
3. **`CheckpointStore` uses resolved paths** passed via constructor, not module
   constants; backward-compatible factory `from_config` for production call
   sites.
4. **Traversal safety** at least as strong as today: configured paths stay inside
   `project_root`; the existing session-id confinement in
   `CheckpointStore._session_file` / `_session_raw_dir` keeps holding for a
   custom checkpoint directory.
5. **Byte-identical defaults:** with no `progress:` block, all paths and files
   are exactly as before (`.meta-viz/progress/current.md`,
   `.meta-viz/checkpoints/<session>.json`).
6. **Provider-agnostic:** no provider literal and no `if provider == …` in any
   new or changed module; provider-scoped behaviour is not introduced.

## Nicht-Ziele

- No implementation, no schema edit, no config/template edit and no plan in this
  document.
- No migration, move or deletion of existing `.meta-viz` data; existing files
  stay where they are and remain readable.
- No change to the legacy checkpoint format, the checkpoint JSON schema, or the
  checkpoint identity rules of `SPEC-PROGRESS-LEDGER-2026-09-13`.
- No provider-scoped path override. The vestigial provider key `checkpoint_dir`
  stays untouched; its removal is a separate follow-up.
- No relaxation of repo-containment. Configured paths remain inside
  `project_root`; the only sanctioned scratch exception stays the existing
  repo-containment tmp-sink.
- No new gitignore automation for relocated directories (see Offene Fragen /
  Risiken).
- No system redesign; this is a bounded M-sized change on existing machinery.
- No role routing in generic templates and no provisioning of a second progress
  format.

## Interface Contracts

All new/changed symbols are listed as `file:Symbol`. New modules must use
`from __future__ import annotations` and `typing.Optional` / `typing.Tuple` /
`typing.List`; PEP 604 (`X | Y`) annotations are not introduced in new modules
(Python 3.9 compatibility, enforced by `scripts/consistency-check.py`).
No external dependencies: new modules use the standard library plus existing
repo-local helpers only (see IC-02 for the exact import list).

### IC-01 — `config/project-config.schema.json:progress` (new top-level block)

Insert one new member into the root `properties` object, after the last existing
top-level property (`repo_containment`) and immediately before the `},` that
precedes `"required"` (currently line 2276). Root `additionalProperties` stays
`true`; the new block itself is closed.

```json
"progress": {
  "type": "object",
  "description": "Storage location of the progress / checkpoint store. Relative paths are resolved against the project root; the framework defaults keep the historical .meta-viz layout.",
  "properties": {
    "dir": {
      "type": "string",
      "default": ".meta-viz/progress",
      "description": "Directory (relative to the project root) for progress files such as current.md. Framework default: .meta-viz/progress."
    },
    "checkpoint-dir": {
      "type": "string",
      "default": ".meta-viz/checkpoints",
      "description": "Directory (relative to the project root) for per-session checkpoint files. Framework default: .meta-viz/checkpoints."
    }
  },
  "additionalProperties": false
}
```

- Both properties are optional and `type: string`; absence means the framework
  default (documented in `default` and in the description).
- Key style `checkpoint-dir` follows the existing hyphenated convention in this
  schema (`repo_containment.tmp-sink`, `spec-plan-workflow.recovery.max-age-seconds`).
- `additionalProperties: false` deliberately rejects typos inside the block
  (same guard style as the `viz` block at lines 1986-2060).
- The schema contract is documentation/typo-guard only: runtime resolution must
  still be defensive (IC-02) because a consumer config can be loaded without
  schema validation.

### IC-02 — `scripts/lib/progress_paths.py` (new leaf module)

Leaf module whose imports are `dataclasses`, `os`, `re`, `pathlib`, `typing`
plus the repo-local loader `from .io import SyncError, _load_yaml_or_json`. It
must not import `checkpoint` (no import cycle). It owns the framework defaults
and the resolution + validation logic. The `.io` import is required by the
`config is None` best-effort read below — the same import and except clause as
`scripts/lib/recovery.py:83 _load_project_config`; it is a repo-local helper,
not an external dependency.

```python
DEFAULT_PROGRESS_DIR = ".meta-viz/progress"
DEFAULT_CHECKPOINT_DIR = ".meta-viz/checkpoints"

SOURCE_PROJECT = "project"
SOURCE_DEFAULT = "default"
SOURCE_SAFE_FALLBACK = "safe-fallback"

@dataclass
class ProgressPathFinding:
    level: str      # "warning"
    code: str       # e.g. "progress.dir-type", "progress.checkpoint-dir-traversal"
    message: str

@dataclass
class ResolvedProgressPaths:
    progress_dir: Path            # absolute, confined under project_root
    checkpoint_dir: Path          # absolute, confined under project_root
    progress_rel: str             # normalized, posix, relative to project_root
    checkpoint_rel: str           # normalized, posix, relative to project_root
    progress_source: str          # SOURCE_PROJECT | SOURCE_DEFAULT | SOURCE_SAFE_FALLBACK
    checkpoint_source: str        # SOURCE_PROJECT | SOURCE_DEFAULT | SOURCE_SAFE_FALLBACK
    findings: Tuple[ProgressPathFinding, ...]

def resolve_progress_paths(
    project_root: Path,
    config: Optional[dict] = None,
) -> ResolvedProgressPaths
def progress_path_error(path: object, project_root: Optional[Path] = None) -> Optional[str]
```

- `resolve_progress_paths` precedence: explicit `progress.<key>` value from
  `config` > framework default. There is no provider level and no second source.
- `config is None` → best-effort load of `<project_root>/.meta-config/project.yaml`
  via `_load_yaml_or_json`, catching `SyncError` and `OSError` (identical to
  `scripts/lib/recovery.py:83 _load_project_config`); an unreadable,
  non-mapping or missing config yields `{}` and never raises.
- `progress` present but not a mapping, or `dir` / `checkpoint-dir` present but
  **not a string** (e.g. integer, list, mapping) → a `warning` finding with a
  stable `code` (`progress.not-mapping`, `progress.dir-type`,
  `progress.checkpoint-dir-type`) and the framework default as
  `SOURCE_SAFE_FALLBACK`. The function **never raises and never exits**.
- **Empty/whitespace-only string semantics (binding, shared with AC-05):** a
  `dir` / `checkpoint-dir` value that is a string but empty or whitespace-only
  (`""`, `"   "`, `"\t"`) is treated as **absent**: it resolves to the framework
  default with source `SOURCE_DEFAULT` and produces **no finding**. This matches
  `_resolve_*` leniency in the existing resolver. Only a non-string `type`
  mismatch produces a `safe-fallback` finding; there is no other path to
  `safe-fallback`.
- Returned absolute paths are derived with `os.path.abspath(os.path.join(...))`
  under the project root and validated by `progress_path_error`; a value that
  fails validation falls back to the framework default and adds a
  `*-traversal` / `*-invalid` finding.
- `progress_rel` / `checkpoint_rel` expose the normalized, posix-form relative
  path for documentation and for callers that only need the string.

Path-traversal contract (`progress_path_error`, same guarantee class as
`scripts/lib/repo_containment.py:189 tmp_sink_path_error`):

1. Must be a string.
2. Must not be empty or whitespace-only.
3. Must be relative (no `os.path.isabs`), no drive-letter path
   (`^[A-Za-z]:`).
4. Must not be `.` or `..` and must not contain a `..` segment
   (after normalizing `\` to `/`).
5. After `os.path.normpath`, the normalized path must not be empty, `.`, `..`
   or start with `..<sep>`.
6. When `project_root` is given, `os.path.abspath(os.path.join(root, normalized))`
   must satisfy `os.path.commonpath([root, target]) == root`; a `ValueError`
   from `commonpath` is a violation.

Any violation returns a non-empty error string; `None` means valid.
`resolve_progress_paths` is the single place that maps that string to a finding,
so the validator and the resolver share exactly one rule set.

### IC-03 — `scripts/lib/checkpoint.py:CheckpointStore` (changed)

Paths are injected, not read from module constants. The constructor stays
backward compatible for every existing call and test.

```python
def __init__(
    self,
    project_root=None,
    agent_meta_root=None,
    progress_dir=None,
    checkpoint_dir=None,
) -> None
@classmethod
def from_config(
    cls,
    project_root,
    config=None,
    agent_meta_root=None,
) -> "CheckpointStore"

def _write_progress_file(self, session_data: dict) -> None
```

- `__init__`: when `checkpoint_dir` is `None`, keep
  `self.checkpoint_dir = self.project_root / DEFAULT_CHECKPOINT_DIR`; when
  `progress_dir` is `None`, set
  `self.progress_dir = self.project_root / DEFAULT_PROGRESS_DIR`. **The defaults
  are byte-identical to today.** `progress_dir` is the new attribute; existing
  attributes (`project_root`, `agent_meta_root`, `checkpoint_dir`) keep their
  names and semantics. Passing an explicit path uses it as given (absolute
  paths) and does not re-join it to `project_root`.
- `from_config`: calls `progress_paths.resolve_progress_paths(project_root,
  config)` and constructs the store with the resolved directories. Existing
  callers `CheckpointStore(project_root=…)` remain valid and behave exactly as
  before.
- `_write_progress_file`: replaces
  `self.project_root / _PROGRESS_DIR / "current.md"` with
  `self.progress_dir / "current.md"`. Before writing, the resolved path is
  confined with a `resolve()` + `relative_to(self.progress_dir.resolve())`
  check (defense-in-depth, same guarantee class as `_session_file` at `:339`)
  and a violation must not write outside the resolved directory.
- `_session_file` (`:339`) and `_session_raw_dir` (`:356`) are unchanged: they
  already confine the session path to `self.checkpoint_dir`, so a custom
  checkpoint directory inherits the same traversal guarantee.
- Module constants become compatibility aliases owned by the new module:
  `CHECKPOINT_DIR = DEFAULT_CHECKPOINT_DIR` and
  `_PROGRESS_DIR = DEFAULT_PROGRESS_DIR`, retained only for backward-compatible
  imports and marked deprecated in their docstring. They are no longer the
  source of truth for path building when an explicit directory is injected.

### IC-04 — production call sites (changed)

Every production site that constructs the store must use `from_config` so a
project override applies consistently to writes and reads. Otherwise a write
would land in the default directory while a read would look in the override
directory (split-brain).

- `scripts/lib/checkpoint_record.py:83` — write path (`--checkpoint`).
- `scripts/lib/rehydrate.py:71` — read path (`--rehydrate`).
- `scripts/lib/recovery.py:363` — read path (recovery resolver).
- `scripts/lib/consistency/ledger_drift.py:154` — read path (ledger drift).

Each site changes `CheckpointStore(project_root=project_root)` to
`CheckpointStore.from_config(project_root)`. The optional `config` argument is
used where the caller already holds a loaded config. No new parameter and no new
CLI flag is introduced by this spec.

**Recorded supersession.** The related spec `SPEC-PROGRESS-LEDGER-2026-09-13`
(IC-04 / IC-11) literally names the direct form `CheckpointStore(project_root)`
at `rehydrate.py:71` and `checkpoint_record.py`. This spec supersedes direct
construction at exactly those sites with `from_config`; when no `progress:`
override is present, the resolved paths and written bytes are identical
(AC-07). This is a recorded supersession, not a claim of "no contradiction".

### IC-05 — tests and scenario (new/changed)

- New unit test module `tests/test_progress_paths.py`: defaults, project
  override, partial override, invalid type, traversal/absolute/drive/`..`/escape,
  findings-not-raise, and `from_config` wiring.
- Existing schema test coverage extends to the new block (the repository's
  schema tests validate the shipped JSON Schema; the `progress` block must be
  accepted and an unknown sub-key rejected).
- New scenario `60-progress-paths-config` in `tests/scenarios/registry.md`, with
  `tests/scenarios/configs/60-progress-paths-config.project.yaml` and
  `tests/scenarios/asserts/60-progress-paths-config.sh`; the scenario proves
  **default vs. override** (one run without `progress:`, one run with an
  override) and asserts the swapped directories at runtime.
- The scenario ID `60` is the next free ID (registry currently ends at
  `59-progress-ledger`).

### IC-06 — documentation references (changed)

- `snippets/orchestrator/checkpointing.md` — replace the two hardcoded path
  statements (`.meta-viz/checkpoints/<session>.json`, `.meta-viz/progress/current.md`)
  with a reference to the configurable `progress.dir` / `progress.checkpoint-dir`
  and their defaults.
- `rules/1-generic/plan-ledger.md` — the `barrier.checkpoint_ref` example path
  stays illustrative but must state that the checkpoint root is configurable.
- `rules/1-generic/session-recovery.md` — same note for the checkpoint store
  location.
- The CLI/config reference and any doc that names `.meta-viz/progress` or
  `.meta-viz/checkpoints` as a fixed location gets the override note. This
  spec does not edit those files; it names them for the implementation.

## Datenfluss

1. `.meta-config/project.yaml` (and, when present, a JSON variant) is loaded by
   the existing loader `scripts/lib/io.py::_load_yaml_or_json`; a missing or
   unreadable file yields an empty mapping.
2. `scripts/lib/progress_paths.py::resolve_progress_paths(project_root, config)`
   reads the top-level `progress` block once and resolves two independent paths:
   `progress.dir` (default `.meta-viz/progress`) and `progress.checkpoint-dir`
   (default `.meta-viz/checkpoints`). Per-path precedence: explicit project
   value > framework default. Invalid values never abort; they emit a finding
   and fall back to the default.
3. `scripts/lib/checkpoint.py::CheckpointStore.from_config(project_root, config)`
   consumes the resolved directories and constructs a store whose
   `progress_dir` and `checkpoint_dir` are absolute paths under `project_root`.
   Direct construction `CheckpointStore(project_root=…)` keeps the framework
   defaults.
4. Write path: `save_checkpoint` resolves the session file through
   `_session_file` → `<checkpoint_dir>/<session>.json`, then calls
   `_write_progress_file` → `<progress_dir>/current.md`. Both writes stay
   confined to their resolved directory.
5. Read path: `recovery.py`, `rehydrate.py` and `consistency/ledger_drift.py`
   use the same `from_config` factory, so they observe exactly the directories
   the writer used.
6. Fallback / no-op path: no `progress` block or an invalid value → framework
   defaults; the resulting files, paths and bytes are identical to the
   pre-change behaviour. The vestigial provider key `checkpoint_dir` is never
   read in any of these steps.

## Acceptance Criteria

Each criterion is testable and observable. "Resolver" means
`scripts/lib/progress_paths.py::resolve_progress_paths`.

1. **AC-01 (default resolution).** Given a project root without any `progress`
   block, when the resolver runs, then `progress_rel == ".meta-viz/progress"`,
   `checkpoint_rel == ".meta-viz/checkpoints"`, both absolute paths resolve under
   `project_root`, both sources are `default`, and no finding is produced.
2. **AC-02 (progress dir override).** Given `progress: {dir: .run/progress}`,
   when the resolver runs, then `progress_rel == ".run/progress"`,
   `progress_source == "project"`, and `checkpoint_rel` stays the framework
   default.
3. **AC-03 (checkpoint dir override).** Given
   `progress: {checkpoint-dir: .run/checkpoints}`, when the resolver runs, then
   `checkpoint_rel == ".run/checkpoints"`,
   `checkpoint_source == "project"`, and `progress_rel` stays the framework
   default.
4. **AC-04 (partial override).** Given only `progress.dir`, when the resolver
   runs, then the two paths are resolved independently: the overridden key uses
   its project value, the absent key uses its framework default.
5. **AC-05 (invalid value, no raise).** Given `progress.dir` (or
   `checkpoint-dir`) set to a **non-string type** (integer, list, mapping), when
   the resolver runs, then it returns the framework default for that path, adds
   a `warning` finding with a stable `code`, sets that path's source to
   `safe-fallback`, and never raises. Given `progress.dir` set to an
   **empty/whitespace-only string** (`""`, `"   "`, `"\t"`), when the resolver
   runs, then the value is treated as absent: the path resolves to the framework
   default with source `default` and **no finding** is produced (identical to
   the IC-02 semantics). The two cases are asserted separately.
6. **AC-06 (traversal rejected).** Given `progress.dir` equal to an absolute
   path, a drive-letter path, `.`, `..`, a path containing a `..` segment, or a
   normalized path that escapes `project_root`, when the resolver runs, then it
   returns the framework default for that path with a traversal finding, and no
   resolved absolute path lies outside `project_root`.
7. **AC-07 (defaults byte-identical, backwards compatible).** Given
   `CheckpointStore(project_root=tmp)` with no `progress` block, when a
   checkpoint is saved, then the session JSON is written to
   `.meta-viz/checkpoints/<session>.json` and the progress file to
   `.meta-viz/progress/current.md`, exactly as before; the existing test suite
   passes unchanged and the constructor accepts the previous two-argument form.
8. **AC-08 (store honours resolved dirs).** Given `from_config` with an override
   for both keys, when a checkpoint is saved, then the session JSON and
   `current.md` are written under the overridden directories and not under
   `.meta-viz`.
9. **AC-09 (all call sites consistent).** Given any of the four production call
   sites (`checkpoint_record`, `rehydrate`, `recovery`, `ledger_drift`), when a
   project with an override is used, then read and write observe the same
   overridden directories (no split-brain).
10. **AC-10 (schema validation).** Given the shipped
    `config/project-config.schema.json`, when a config containing a valid
    `progress` block is validated, then it is accepted; when it contains an
    unknown sub-key under `progress`, then validation rejects it; a non-string
    `dir`/`checkpoint-dir` is rejected.
11. **AC-11 (provider-agnostic).** Given the new and changed modules, when
    scanned, then they contain no provider literal and no `if provider == …`
    branch, and provider-scoped resolution does not exist.
12. **AC-12 (Python 3.9 syntax).** Given the new module, when the consistency
    check runs, then it is importable under Python 3.9, uses
    `from __future__ import annotations` and contains no PEP 604 union
    annotation in a new module.
13. **AC-13 (scenario 60, default vs. override).** Given scenario
    `60-progress-paths-config` with one default config and one override config,
    when the scenario harness runs, then the default run produces the historical
    `.meta-viz` paths and the override run produces the configured paths, and the
    registry entry plus the assert script reflect both outcomes.
14. **AC-14 (docs/rule/snippet references).** Given the changed documentation
    references listed in IC-06, when reviewed, then none of them state the two
    directories as a fixed, unconfigurable location.
15. **AC-15 (test coverage).** Given the test suite, when it runs, then it
    contains explicit cases for: default resolution, full project override,
    partial override, invalid value, absolute/drive/`..`/escape traversal, the
    schema accept/reject cases, and `from_config` wiring honouring the override.

## Offene Fragen / Risiken

Each item states the recommended handling and what remains open. No
implementation starts while an item is open and blocking.

1. **Split-brain across call sites (risk, blocking).** Four production sites
   construct the store; missing one would make writes and reads disagree.
   Recommended: migrate all four in one change and let AC-09 guard it. Open:
   whether a follow-up test should assert there is no remaining direct
   `CheckpointStore(project_root=…)` construction in `scripts/`.
2. **Gitignore coverage for relocated directories (risk).** A project that
   points `progress.dir` outside `.meta-viz` may stop being ignored by the
   managed gitignore block. Recommended: out of scope here; document the
   consequence and track as a separate follow-up. Open: whether sync should
   derive gitignore entries from the resolved paths later.
3. **Deprecation/removal of the provider `checkpoint_dir` key (open).**
   Recommended: keep it untouched for now (decision option b). Open: when it is
   formally declared deprecated and whether the ratchet is replaced by a
   presence-only assertion at that time (the ratchet must not be changed silently
   by this change).
4. **Alias lifetime for `CHECKPOINT_DIR` / `_PROGRESS_DIR` (open).** Recommended:
   keep both as deprecated aliases for backward-compatible imports. Open: whether
   a later cleanup removes them once no importer remains.
5. **Relocated paths and repo-containment symlinks (risk, low).** The validator
   uses `abspath` + `commonpath` (portable, mirrors the existing scratch-sink
   rule); a symlinked parent inside the project root is accepted. Open: whether a
   stricter `realpath`-based check is required for a relocated directory.
6. **Merge order with the in-flight adjacent spec (risk, low).** The adjacent
   change adds a recovery/checkpoint wiring on the same modules. Recommended:
   apply this change first or coordinate the shared files (`checkpoint.py`,
   `recovery.py`, `rehydrate.py`, `checkpoint_record.py`) to avoid conflicting
   edits.

## Trace-Anker

- `spec-id: SPEC-PROGRESS-PATHS-CONFIG-2026-09-13` — plans reference this value
  via their `**Spec:**` field. A plan for this spec is authored separately and is
  out of scope for this document.
- Related spec: `SPEC-PROGRESS-LEDGER-2026-09-13` — checkpoint identity, the
  `.meta-viz` default layout and the read/write wiring stay as specified there.
  **Recorded supersession:** that spec's IC-04/IC-11 name the direct constructor
  `CheckpointStore(project_root)` at `rehydrate.py:71` and `checkpoint_record.py`;
  this spec re-points those call sites (IC-04) to
  `CheckpointStore.from_config(project_root)`. For the framework defaults the
  behaviour is identical (same `.meta-viz` paths, same bytes); `from_config`
  supersedes direct construction at exactly those sites.
- Interface-contract to acceptance-criteria mapping:

  | Interface contract | Acceptance criteria |
  |---|---|
  | IC-01 (`progress` schema block) | AC-01, AC-02, AC-03, AC-04, AC-10 |
  | IC-02 (`progress_paths` resolver + traversal validator) | AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-11, AC-12 |
  | IC-03 (`CheckpointStore` paths via params + `from_config`) | AC-07, AC-08, AC-11, AC-12, AC-15 |
  | IC-04 (call-site migration) | AC-09, AC-15 |
  | IC-05 (tests + scenario 60) | AC-10, AC-13, AC-15 |
  | IC-06 (docs/rules/snippets) | AC-14 |

- Binding frame: `scripts/lib/repo_containment.py` (resolver precedent,
  findings-not-raise + path validator), `scripts/lib/io.py::_load_yaml_or_json`
  (config loader), `tests/scenarios/registry.md` (scenario 60).
