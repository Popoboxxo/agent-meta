# CLI Reference: `sync.py`

The `sync.py` script is the central entry point of the agent-meta framework. It generates agents, manages provider configurations, and validates templates.

## Core Sync Operations

| Flag | Description |
|------|-------------|
| `--config CONFIG` | Path to the `project.yaml` (Default: `.meta-config/project.yaml`) |
| `--init` | Generates the provider-specific configuration (e.g., `CLAUDE.md`) from templates if they do not already exist. |
| `--only-variables` | Substitutes variables (`{{VARIABLE}}`) in the existing configuration without generating new agents. |
| `--cleanup-preview` | Planning-only, side-effect-free JSON preview of the stale agent files a sync would remove (dry-run gate). Emits exactly one JSON object on stdout and writes nothing (no index write, no unlink, no backup, no clone/submodule). Exit 0 even for a non-empty stale set, 1 only on internal failure. |
| `--context-report [--json] [--profile full\|compact\|both]` | Measures the rendered context artifacts (entry file, rules, orchestrator, harness roster, always-loaded set) per active provider: bytes, lines, estimated tokens (bytes / 4) and the capability caps (IC-09). Renders the project into a work directory below the tmp-sink subdirectory `context-report/` and writes only there (the report is also stored as `report.json`); nothing is written into the project and the system temp directory is never used. Exit 0; exit 1 only on `context.over-hard-cap`; exit 2 with `tmp-sink.disabled` when `repo_containment.tmp-sink.enabled` is `false`, and exit 2 with `context-report.render-failed` when the render fails (including missing `git`); an empty report prints a warning to stderr and exits 0. Limitation: the project is rendered with `sync.py --init` on a copy of `project.yaml` only, so project-local files outside `.meta-config` (`.claude/3-project/*-ext.md`, project-owned rules and hooks, the "Eigene Notizen" section of CLAUDE.md) are missing and the measurement can underestimate the real always-loaded footprint. `--json` emits `{provider: {artifact: {bytes, lines, tokens_est, cap, cap_kind}}}`. `--profile compact` really renders the opt-in `compact` profile into a work directory below the tmp-sink subdirectory `context-report/` (via `resolve_work_dir`, IC-34), injecting `context-profile: compact` into the work-dir *copy* of `project.yaml` only — the project config on disk is never modified; `--profile both` renders `full` and `compact` and reports the `full` ↔ `compact` delta (`profiles`, `full`, `compact`, `delta`). `compact` is opt-in and unverified (IC-36): every `compact`/`both` report carries the machine-readable `targets_note` (the AC-26 size targets are ESTIMATES, Spec section 11, not measurements) and prints the same note to stderr. Shares `measure_artifacts` (`scripts/lib/context_report.py`) with `scripts/measure_context.py --project <path>`. |
| `--doctor` | Diagnoses the installation against the known-issues registry (`config/known-issues.yaml`, the only registry source; a project-level registry is ignored). Deterministic, no LLM. Writes nothing into the project or into agent-meta; the only write target is one JSON report via `--out` inside `<tmp-sink>/doctor/`. Flags and exit codes: see the section "`--doctor` installation diagnosis" below. |
| `--optimize-config [--json] [--out DIR]` and `--include-semantic` | Read-only config optimizer (IC-24/IC-25, package 2d). Proposes removal candidates for `.meta-config/project.yaml` and proves (L0) that removing every deterministic candidate keeps every generated artifact of every active provider byte-identical: a sentinel render (every text value under `variables:` wrapped in `QZ<NAME>QZ…ZQ<NAME>ZQ`) counts the per-variable fan-out, and the L0 proof renders the config verbatim and again without the removable keys and compares both trees — including the render-derived sidecars `.meta-config/auto-commit-allowlist.json`, `.meta-config/generated-file-hashes.json` and `.meta-config/context-hashes.json` (AC-55 Rev. 3), whose hashes are recorded before/after in `proof.json` (a sidecar missing from the render fails the proof). Writes exactly three artifacts below `<tmp-sink>/meta-optimizer/<YYYYMMDD-HHMMSS>-<pid>/` — `proposal.json` (candidates with `id`, `kind`, `yaml_path`, `scope`, `marks`, `approval_level`, `warnings`, `deterministic`, `applicable`, `proof_level_required`, `yaml_bytes_saved`, `injected_bytes_saved_est`, `rationale`, `hunks`; `fan_out`; `generator_options`; `agent_meta_version`; `project_yaml_sha256`), `proposal.diff` and `proof.json` (L0 report plus the hash comparison of the three sidecars) — all mode `0600`. `fan_out` lists every text variable under `variables:` (occurrences, files, injected bytes, per provider) and, for conditional variables (`{{#if X}}`/`{{#unless X}}` usage or the render's conditional list), an entry with `occurrences: null`, `files: null`, `injected_bytes: 0`, zeroed `per_provider` and `conditional: true` (they are never sentinel-wrapped). The sentinel render and the two proof renders live in `<sink>/meta-optimizer/<run_id>[-before|-after]/work/` via `resolve_work_dir` (IC-34, never the system temp dir) and are removed before the command returns, so only the three artifacts remain below the sink (AC-89: no credential byte sequence survives). Credential paths (IC-35 `credentials`: name patterns, explicit keys, the registry's `value_scan`) are excluded completely — no candidate, no hint, no `FanOutEntry`, and credential lines inside diff context are replaced by a redaction marker (AC-89); a missing/invalid registry is a hard error (`meta-optimizer.credential-registry-invalid`, exit 2). `--include-semantic` additionally reports hint-only kinds (`duplicate-value`, `relocate-*`, `semantic-merge`) that carry `deterministic: false`, `applicable: false`, `hunks == ()` and `proof_level_required: "none"` (AC-57/91); without the flag those kinds are filtered out. Exit 0 when the proposal and the proof were written (also with candidates); exit 1 on `meta-optimizer.proof-failed` (nothing but `proof.json` written); exit 2 on usage errors, `tmp-sink.disabled`, `meta-optimizer.credential-registry-invalid`, `meta-optimizer.render-failed`, `meta-optimizer.out-write-failed`, `optimize-config.out-outside-tmp-sink` or when combined with `--fill-defaults` (`meta-optimizer.lossy-flag`). `--out DIR` selects the artifact directory inside `<tmp-sink>/meta-optimizer/` (default: a fresh timestamped subdirectory). `--json` emits the proposal object on stdout. |
| `--apply-config-patch FILE --accept ID… [--accept-runtime ID…] (--dry-run \| --preview FILE)` | Remove-only config patch applier (IC-24 "Applier", package 2d.3). Reads **only** `project_yaml_sha256`, the candidate IDs, `agent_meta_version` and `generator_options` from the `proposal.json` written by `--optimize-config`; the candidates and their hunks are recomputed with `collect_candidates`, and the file hunks are only *reconciled*: a hunk that inserts a line is not remove-only (`meta-optimizer.not-remove-only`), a hunk that differs from the recomputed (redacted) one is `rejected: hunk-mismatch`. `--accept` is **mandatory** (there is no implicit application) and lists the IDs the user approved; `--accept-runtime` additionally confirms the candidates with `approval_level: confirm-runtime` (runtime readers) — otherwise they are `rejected: needs-runtime-confirmation`. Hints (`applicable: false`, e.g. `dead-variable-content-loss`, `structural-simplify`, `relocate-*`) are `rejected: not-applicable`; an ID that the recomputation does not produce is `rejected: not-reproducible`; a credential path would be `rejected: credential-key`. A `proposal.json` from another framework version is `meta-optimizer.version-mismatch`; a config changed since the proposal was written is `meta-optimizer.stale-proposal` (also re-checked immediately before `os.replace`). `--dry-run` writes only `<tmp-sink>/meta-optimizer/<ts>/preview.json` (0600: `accept_ids`, `accept_runtime_ids`, `project_yaml_sha256`, `agent_meta_version`, `generator_options`, per ID the newly recomputed redacted hunk/`kind`/`marks`/`warnings`, `rejected` with reason, the L0 `proof` section and the binding `preview_sha256`) and never touches `project.yaml`. An application requires `--preview FILE` and is bound to it (identical ID sets, hash, version and recomputed hunks), otherwise `meta-optimizer.preview-mismatch`. All-or-nothing: any rejection, a failed L0 proof (`meta-optimizer.proof-failed`), a version/TOCTOU/preview mismatch or a sink on a different device (`meta-optimizer.cross-device`) leaves the config untouched. On success the config is replaced atomically from a transient scratch file inside the run dir; the sink then holds `applied.json` (`approval_source: "relayed"`, `accept_ids`, `accept_runtime_ids`, `rejected`, both hashes, `preview_sha256`, `agent_meta_version`, `generator_options`, `timestamp`, `backup_redacted_keys` — key *names* only) and `project.yaml.bak` with the credential values replaced by the deterministic redaction marker — both mode `0600`. Comments and key order survive (remove-only; `analyze_roundtrip`, AC-56). Exit 0 when every accepted ID was applied without a rejection (with `--dry-run`: the preview was written without a rejection); exit 1 on any rejection or a global mismatch (`meta-optimizer.version-mismatch`, `meta-optimizer.stale-proposal`, `meta-optimizer.preview-mismatch`, `meta-optimizer.not-remove-only`, `meta-optimizer.proof-failed`, `meta-optimizer.cross-device`) with nothing written; exit 2 on usage errors (missing `--accept`, neither `--dry-run` nor `--preview`, unreadable or invalid proposal/config), `tmp-sink.disabled`, `meta-optimizer.credential-registry-invalid`, `meta-optimizer.render-failed`, `meta-optimizer.out-write-failed` or `--fill-defaults` in the same invocation (`meta-optimizer.lossy-flag`). Never uses the system temp directory (AC-94); the render scratch is removed before returning (AC-89). `--json` emits the `ApplyReport` object. |
| `--dry-run` | Simulates the sync process without writing any files to disk. |
| `--check` | Exits with code 1 if context files (`CLAUDE.md`, `AGENTS.md`) are out of sync, otherwise 0. (Crucial for CI/CD). |
| `--validate` | Performs a full sync into a test repository. Results are in `sync.log`. |
| `--validate-se` | Standalone, read-only SE-cascade validation (issue #338): checks the project's `docs/se` artifacts against the #339 conventions (B1–B5). Exit 0 when clean or when no SE artifacts exist; exit 1 with a findings list otherwise. |
| `--validate-spec-plan` | Standalone, read-only spec/plan-workflow validation (F12): checks the project's configured spec/plan/spike directories (defaults `docs/specs`, `docs/plans`, `docs/spikes`, plus configured legacy dirs) for required sections, placeholders, traceability, approval markers, ledger format and the plan task graph; unchanged artifacts are skipped when `scan.changed-files-only` is true. Exit 0 when clean, when no artifacts exist, or when the workflow is disabled; exit 1 with a findings list otherwise. |
| `--scan-staged` | Scans git-staged file contents for secrets (issue #694 pre-commit gate) and exits. |
| `--test-plugin ID` | Runs the health check for one plugin from the plugin catalog and exits. |
| `--render-standalone` | Renders fully self-contained, English-only copies of the pilot `1-generic` agent templates into `standalone/agents/` — no Python/`project.yaml` needed to use them. Combine with `--check` for a read-only CI drift gate. |
| `--fill-defaults` | Writes missing configuration fields with default values into the `project.yaml`. |
| `--setup` | Starts an interactive setup wizard for guided creation of the `project.yaml` and then runs `--init`. |
| `--audit-config` | Compares the project configuration against the templates (checks for `roles_without_template`, `deprecated_roles`). |
| `--apply` | Used in combination with `--audit-config`: Rewrites the `project.yaml` and comments out deprecated roles. |

### `--cleanup-preview` output contract

`--cleanup-preview` runs the planning half of the agent sync for every active provider
and prints **exactly one JSON object** on stdout (indent 2, UTF-8). It is side-effect-free:
it writes no managed index, unlinks no file, creates no `.sync-backup-*` sibling and neither
clones nor de-inits a skill submodule. Diagnostics are collected, never written to stderr,
so stdout stays machine-consumable.

Exit code 0 even when the stale set is non-empty; exit code 1 only on an internal failure
(then stdout is `{"version": 1, "error": "<ExceptionType>: <message>"}`).

```json
{
  "version": 1,
  "generated_at": "2026-09-14T12:00:00Z",
  "providers": [
    {
      "provider": "<active-provider>",
      "stale": [
        {
          "path": ".claude/agents/stale-role.md",
          "reason": "role removed from config",
          "tracked": true,
          "adopted": false
        }
      ],
      "foreign": [
        {
          "path": ".claude/agents/handwritten.md",
          "legacy_unmarked": true
        }
      ],
      "backups_to_prune": [".claude/agents/bar.md.sync-backup-20260801-101010"]
    }
  ],
  "fingerprint": "sha256:<64 hex chars>"
}
```

- `stale[]` — project-relative `path`, `reason` (`"role removed from config"` or
  `"skill deactivated"`), `tracked` (listed in the managed index) and `adopted` (a
  provenance-carrying external-skill wrapper reconciled despite a readable index).
- `foreign[]` — files that survive by design; `legacy_unmarked` is `true` for files
  without a recognised agent-meta provenance marker (OQ-3: manual removal only).
- `backups_to_prune[]` — recomputed would-be prune set for the provider's agent dir
  (the backup pruner itself is a no-op during a preview).
- `fingerprint` — stable `sha256:…` hash over the canonical stale set (sorted by
  provider/path/reason/tracked/adopted). Pass it to `POST /api/roles/cleanup/apply` so
  the server can reject a stale preview.

### `--doctor` installation diagnosis

`sync.py --doctor [--json] [--strict] [--provider P ...] [--out FILE]` evaluates the registry
entries per active provider (predicates, detectors, severity cap) and reports the findings sorted by
severity, issue id, provider and file. It is not strictly read-only: its write boundary is the
resolved tmp-sink (IC-34), nothing else.

| Flag | Description |
|------|-------------|
| `--json` | Prints exactly one deterministic JSON object on stdout (`findings[]`, `summary` with `total`, `errors`, `warnings`, `infos`, `registry_version`, `agent_meta_version`, `skipped[]`, `severity[]`). Banners and diagnostics go to stderr. Without it a text report is printed. |
| `--strict` | CI mode: a WARNING finding also exits 1, and an invalid registry entry (`doctor.registry-invalid`, reported as WARNING otherwise) becomes an ERROR and exits 2. Intended for the agent-meta CI on matrix fixtures. |
| `--provider P ...` | Restricts the run to the named providers. Unknown or inactive names are ignored and reported as INFO `doctor.provider-filter`. |
| `--out FILE` | Also writes the JSON report to `FILE`. `FILE` must lie inside `<tmp-sink>/doctor/` of the configured sink (e.g. `.tmp/doctor/<YYYYMMDD-HHMMSS>.json`); the check compares `realpath`s, so `..` and symlink escapes are rejected. Without `--out` nothing is written. |

Exit codes:

| Exit | Meaning |
|------|---------|
| 0 | No finding with effective severity ERROR (INFO and WARNING findings do not fail the run without `--strict`). |
| 1 | At least one effective ERROR finding, or at least one WARNING finding with `--strict`. |
| 2 | Runtime error (`doctor.internal-error`), `--strict` with `doctor.registry-invalid`, `--out` outside `<tmp-sink>/doctor/` (`doctor.out-outside-tmp-sink`), or `--out` with `repo_containment.tmp-sink.enabled: false` (`doctor.tmp-sink.disabled`, takes precedence). The target is checked before the run starts, so a rejected `--out` costs no runtime. |

Behavior with a disabled tmp-sink: `--doctor` without `--out` runs normally (stdout/JSON complete); `command`
detectors that would write below the sink are skipped (`detector-unavailable`), stdout-only commands
(`--check --dry-run`) still run, and the `tmp-sink-outside-repo-or-system-temp` seed is skipped.

Write boundary: like `--cleanup-preview`, `--doctor` forces dry-run and redirects stdout to stderr
before the context is built (no schema-enum update when self-hosting), then marks the run read-only
so the common tail writes neither `sync.log` nor env scripts. Bytecode caches are not written either.

Runtime: the `sync-pending` seed runs `sync.py --check --dry-run` as a subprocess (timeout 60 s per
`command` detector). Expect about 25-30 s on the agent-meta repository itself and about 7 s on a small
project; all other detectors are file reads and take well under a second. Run it deliberately, not in a
tight loop.

## Context Profiles (`context-profile`) — opt-in, unverified

`context-profile: full|compact` (default `full`) is a top-level `project.yaml` key that
bundles the context-density measures of the profile axis; a per-provider scope is available
via `provider-overrides.<Provider>.context-profile`. Resolution precedence per single
setting: explicit sub-setting (`context_file.mode`) > `provider-overrides.<Provider>.context-profile`
> `context-profile` > default. `compact` implies `context_file.mode: compact` only while the
mode is not explicitly set.

`compact` ships **opt-in and unverified**: the role-routing eval that would evidence AC-25
has not run because its `full` baseline (AC-02) was skipped by the user (0f.3,
`SKIPPED-BY-USER`). While no passing `compact` evaluation exists, a sync with
`context-profile: compact` writes the INFO `context-profile.unverified` per compact provider
to `sync.log`; the proof is planned in package 2f (separate user approval with a cost
estimate first). No default changes: a missing key or `full` leaves every render
byte-identical (AC-35). A context file shared by several active providers renders `full` as
soon as one sharer resolves to `full` (safe side, ADR-5), and a requested `compact` is
downgraded with a single WARN `context-profile.shared-file-downgrade` per file, naming the
requesting providers.

`--context-report --profile compact|both` (IC-11) renders the profile into a work directory below
the tmp-sink and reports the `full` ↔ `compact` delta; `--profile compact` injects
`context-profile: compact` into the work-dir *copy* of `project.yaml` only — the project config on
disk is never modified. The profile is a pure switch: the documentation makes no claim beyond
"opt-in, unverified" and does not put the requested profile into the project configuration.

### AC-26 size targets are ESTIMATES

The `compact` size targets of AC-26 (Claude orchestrator ≤ 32 KB; AGENTS.md single provider ≤ 8 KB;
AGENTS.md multi provider ≤ 12 KB and < 32,768 B; Gemini AGENTS.md ≤ 9 KB; Continue always-on rules
≤ 2 KB; Copilot instruction file ≤ 4,000 chars) are **ESTIMATES** (Spec section 11), not
measurements. They are recorded as data: test pins plus the capability config keys
`Codex.context_hard_cap_bytes: 32768` and `Copilot.context_soft_cap_chars: 4000`, surfaced by the
report as the artifact's `cap`/`cap_kind`. The measured values are reported by `--context-report`
and pinned as regression ceilings (`COMPACT_BUDGET_CEILINGS` in `tests/test_context_budgets.py`).
This documentation does **not claim** the targets are met — several are currently missed (a
documented deviation, to be resolved by a later spec revision per AC-26; out of scope here).

## Session Resume & Checkpointing

| Flag | Description |
|------|-------------|
| `--rehydrate` | Read-only resume path: prints the resume context of the newest unfinished session (plan/task/checkpoint identity, next open task, drift). Writes nothing, runs no sync, and exits 0 even when there is nothing to resume. |
| `--checkpoint` | Write mode: appends one checkpoint to the session store (`.meta-viz/checkpoints/` — the framework default of `progress.checkpoint-dir` — plus its progress write-through under `.meta-viz/progress/`, the default of `progress.dir`; both are overridable via the top-level `progress` block in `.meta-config/project.yaml`). Requires `--session-id`, `--task`, `--agent` and `--status`; plan identity is explicit only via `--plan-id` or `--plan <path>`. Exit 1 on missing arguments or a store error, 0 after a successful write. |
| `--session-id ID` | Session id for `--checkpoint` (one file per session under `.meta-viz/checkpoints/`, the framework default of `progress.checkpoint-dir`). |
| `--agent NAME` | Agent name for `--checkpoint`. |
| `--plan PATH` | Plan path for `--checkpoint`; its plan id is derived from the document (or its file-stem slug), never random. Ignored when `--plan-id` is given. |
| `--plan-id ID` | Explicit plan id for `--checkpoint`. Takes precedence over `--plan`. |
| `--description TEXT` | Task description for `--checkpoint`. |
| `--summary TEXT` | Status summary for `--checkpoint`. |
| `--next-step TEXT` | Next step for `--checkpoint`. |
| `--status STATUS` | With `--checkpoint`: one of `completed`, `failed`, `timeout`, `in_progress`. With `--update-plan-ledger`: value for the first `Status:` header line of the plan. |

## Plan Ledger

| Flag | Description |
|------|-------------|
| `--update-plan-ledger PLAN` | Write mode: rewrites the leading task checkboxes and/or the first `Status:` header of `PLAN` (path inside the project root). Mark tasks done with `--task <id>...`, reset them with `--open`, set the status via `--status <s>`. Combine with `--dry-run` for a preview; exit 1 on missing arguments, a missing plan or an unmatched task id. |
| `--task ID...` | Task id(s) for `--update-plan-ledger` (normalized, e.g. `1` or `task-1`); for `--checkpoint` the first id is normalized and recorded. |
| `--open` | With `--update-plan-ledger --task`: reset the task checkboxes to `- [ ]` instead of marking them done. |
| `--status STATUS` | With `--update-plan-ledger`: value for the first `Status:` header line of the plan. See also the Session Resume & Checkpointing section. |

## Extensions, Rules, Hooks

| Flag | Description |
|------|-------------|
| `--create-ext ROLE` | Creates an extension file for the specified `ROLE` (or `all`). |
| `--update-ext` | Updates the "managed block" in all existing extension files. |
| `--create-rule NAME` | Creates a template for a provider rule (`.claude/rules/<NAME>.md`). |
| `--create-hook NAME` | Creates a template for a provider hook (`.claude/hooks/<NAME>.sh`). |
| `--create-command NAME` | Creates a template for a provider command (`.claude/commands/<NAME>.md`). |

## Visualization

| Flag | Description |
|------|-------------|
| `--viz` | Generates a static agent visualization (Mindmap + interactive HTML). |
| `--viz-mode {off,static,dynamic,full}` | Sets the level of detail for the visualization. |
| `--viz-only` | Only generates the visualization, skipping the agent sync. |
| `--viz-cleanup` | Cleans up old visualization sessions and logs. |

## Provider Management

| Flag | Description |
|------|-------------|
| `--deactivate-providers [PROVIDER ...]` | Zips and removes the specified provider directories from the project. |
| `--activate-providers [PROVIDER ...]` | Restores the specified providers from backup zips. |
| `--deactivation-status` | Displays the current deactivation status of all providers. |

## Backup & Restore

| Flag | Description |
|------|-------------|
| `--backup [PROVIDER ...]` | Creates a timestamped backup of the current configuration and agents. |
| `--label TEXT` | Optional label for the created backup. |
| `--restore ARCHIVE` | Restores an environment from a backup archive. |
| `--restore-providers [...]` | Specifies which providers should be considered during the restore. |
| `--force` | Forces overwrite during restore. |
| `--list-backups` | Lists all available backup archives with metadata. |
| `--delete-backup ARCHIVE` | Deletes a specific backup archive. |
| `--prune-backups` | Deletes old backups according to the defined retention policy. |

## Cache & Discovery

| Flag | Description |
|------|-------------|
| `--clear-cache` | Clears the outcome cache. |
| `--update-models` | Updates the model registry from provider APIs (OpenRouter, Zen, Go). |
| `--harness NAME` | Activates a harness from `config/harnesses/<NAME>.yaml` and enforces its write isolation: sync refuses to run when the project root lies outside the harness's declared checkout-root. Overrides the `AGENT_META_HARNESS` environment variable. See [Cross-Harness Dev-Isolation](../guides/cross-harness-dev-isolation.md). |

## Admin UI & External Skills

| Flag | Description |
|------|-------------|
| `--admin` | Starts the Admin UI Server after the sync (Default port: 7420). |
| `--admin-only` | Only starts the Admin UI Server without running the sync. |
| `--admin-port PORT` | Overrides the port for the Admin UI Server. |
| `--add-skill REPO_URL` | Registers a new external skill (Git Submodule Add + Config entry). |
| `--skill-name NAME` | Sets the name for the newly added skill. |
| `--source PATH` | The source path within the skill repository. |
| `--role ROLE` | The agent role name to which the skill is assigned. |
| `--entry FILE` | The entry file for the skill. |
