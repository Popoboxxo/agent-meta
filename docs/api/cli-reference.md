# CLI Reference: `sync.py`

The `sync.py` script is the central entry point of the agent-meta framework. It generates agents, manages provider configurations, and validates templates.

## Core Sync Operations

| Flag | Description |
|------|-------------|
| `--config CONFIG` | Path to the `project.yaml` (Default: `.meta-config/project.yaml`) |
| `--init` | Generates the provider-specific configuration (e.g., `CLAUDE.md`) from templates if they do not already exist. |
| `--only-variables` | Substitutes variables (`{{VARIABLE}}`) in the existing configuration without generating new agents. |
| `--dry-run` | Simulates the sync process without writing any files to disk. |
| `--check` | Exits with code 1 if context files (`CLAUDE.md`, `AGENTS.md`) are out of sync, otherwise 0. (Crucial for CI/CD). |
| `--validate` | Performs a full sync into a test repository. Results are in `sync.log`. |
| `--test-plugin ID` | Runs the health check for one plugin from the plugin catalog and exits. |
| `--render-standalone` | Renders fully self-contained, English-only copies of the pilot `1-generic` agent templates into `standalone/agents/` — no Python/`project.yaml` needed to use them. Combine with `--check` for a read-only CI drift gate. |
| `--fill-defaults` | Writes missing configuration fields with default values into the `project.yaml`. |
| `--setup` | Starts an interactive setup wizard for guided creation of the `project.yaml` and then runs `--init`. |
| `--audit-config` | Compares the project configuration against the templates (checks for `roles_without_template`, `deprecated_roles`). |
| `--apply` | Used in combination with `--audit-config`: Rewrites the `project.yaml` and comments out deprecated roles. |

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
