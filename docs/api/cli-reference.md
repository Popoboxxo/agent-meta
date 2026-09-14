# CLI Reference: `sync.py`

The `sync.py` script is the central entry point of the agent-meta framework. It generates agents, manages provider configurations, and validates templates.

## Core Sync Operations

| Flag | Description |
|------|-------------|
| `--config CONFIG` | Path to the `project.yaml` (Default: `.meta-config/project.yaml`) |
| `--init` | Generates the provider-specific configuration (e.g., `CLAUDE.md`) from templates if they do not already exist. |
| `--only-variables` | Substitutes variables (`{{VARIABLE}}`) in the existing configuration without generating new agents. |
| `--cleanup-preview` | Planning-only, side-effect-free JSON preview of the stale agent files a sync would remove (dry-run gate). Emits exactly one JSON object on stdout and writes nothing (no index write, no unlink, no backup, no clone/submodule). Exit 0 even for a non-empty stale set, 1 only on internal failure. |
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
