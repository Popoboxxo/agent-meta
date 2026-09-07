# Cross-Harness Dev-Isolation via Separate Git Checkouts

Issue #547 (RFC). One AI coding tool ("harness") per top-level Git checkout,
with a framework-level harness abstraction (`config/harnesses/*.yaml`) that
sync.py enforces: **a harness writes only into its own checkout.**

This guide covers the *developer-level* multi-checkout workflow. It is a
different topic from the subagent-level isolation guides:
[agent-isolation.md](features/agent-isolation.md) (`isolation: worktree` for
single agent runs) and the no-worktree-isolation rule for subagents.

---

## Why separate checkouts, not worktrees?

Running multiple harnesses (Claude Code + Opencode + a third tool) in the
same working directory causes cross-harness interference: generated
directories (`.claude/`, `.opencode/`, ...), context files and rules land in
one shared tree while each harness expects to own its own.

**Git worktrees were considered and deliberately rejected as the primary
solution.** agent-meta repos regularly contain Git submodules (`external/`,
`.agent-meta/`); submodules inside worktrees are a known breakage source
(missing submodule init per worktree, ambiguous `.git` file layout), and
sync.py's generated-output contract assumes a full checkout. Worktrees also
share the same branch namespace, which collides with the per-harness branch
strategy below.

The robust alternative: **one plain Git checkout per harness**, in a
per-harness top-level directory. Each checkout is a complete, independent
repository clone — submodules, sync.py and every generated directory behave
exactly as in a single-harness setup.

---

## Checkout convention

```
~/repos/<repo>       Claude Code harness
~/repos-oc/<repo>    Opencode harness
~/repos-x/<repo>     third harness slot (any additional tool)
```

- Every directory is an independent `git clone` (or `git init` + remote setup)
  of the same repository. `~/repos*` directories themselves are NOT Git
  repositories.
- Example:

  ```bash
  git clone git@github.com:owner/agent-meta.git ~/repos/agent-meta
  git clone git@github.com:owner/agent-meta.git ~/repos-oc/agent-meta
  ```

- One checkout is checked out on `main` (or a review branch) at a time; each
  harness works on its own branch in its own checkout (below).

## Branch strategy

| Checkout        | Branch            | Purpose                                  |
|-----------------|-------------------|------------------------------------------|
| `~/repos/<repo>`    | `agent/claude`  | work branch of the Claude harness        |
| `~/repos-oc/<repo>` | `agent/opencode`| work branch of the Opencode harness      |
| `~/repos-x/<repo>`  | `agent/third`   | work branch of the third harness         |

Flow: each harness commits to its own `agent/<name>` branch and delivers
changes exclusively via **pull requests into `main`**. A harness never
pushes into another harness's branch; `main` is the only integration point
(other branches are pulled/fetched from the shared remote as needed).

---

## Harness abstraction (`config/harnesses/*.yaml`)

The framework expresses harness differences purely as data — one YAML file
per harness in the agent-meta framework root. Python code stays provider-
and harness-agnostic: no `if harness == "..."` / `if provider == "..."`
branches (same policy as the capability-flag pattern in
`config/provider-capabilities.yaml`).

### Schema

```yaml
harness:
  name: opencode              # required, must equal the file stem
  description: "..."          # optional, human-readable summary
  checkout-root: ~/repos-oc   # required — dir holding this harness's checkouts
  root-env: AGENT_META_HARNESS_ROOT  # optional env var overriding checkout-root
  branch: agent/opencode      # optional branch convention (informational)
  default-providers:          # optional task-partitioning hint (informational)
    - Opencode
```

| Field              | Required | Meaning                                                                 |
|--------------------|----------|-------------------------------------------------------------------------|
| `name`             | yes      | Harness id; must match the config file stem (`opencode.yaml` → `opencode`). |
| `description`      | no       | Free-text summary shown in CLI messages.                                |
| `checkout-root`    | yes      | Absolute path (or `~/...`) of the directory that holds this harness's Git checkouts. sync.py refuses to run when the project root lies outside it. |
| `root-env`         | no       | Name of an environment variable that overrides `checkout-root` (default `AGENT_META_HARNESS_ROOT`) — for machines whose home layout differs. |
| `branch`           | no       | Branch convention for this harness. Informational — enforced by convention only, not by tooling. |
| `default-providers`| no       | Which provider(s) this harness normally drives. Informational task-partitioning hint; not enforced at runtime (see Follow-ups). |

Shipped defaults: `claude.yaml` (~/repos, `agent/claude`), `opencode.yaml`
(~/repos-oc, `agent/opencode`), `third.yaml` (~/repos-x, `agent/third`).

### Loader API (`scripts/lib/harnesses.py`)

| Symbol | Purpose |
|--------|---------|
| `HarnessConfig` | Frozen dataclass for one parsed harness definition. |
| `list_harness_names(root)` | Sorted harness ids (pure directory listing, no parsing). |
| `list_harnesses(root, env)` | Parse every harness config — fail-closed on schema violations. |
| `load_harness(root, name, env)` | Load one harness by name; unknown names raise `SyncError` listing the available ones. |
| `resolve_active_harness(root, cli_value, env)` | Activation resolution (precedence below); `None` when no harness is active. |
| `ensure_write_isolation(harness, target, log, strict=...)` | The guard: `strict=True` raises `SyncError`, `strict=False` warns and allows. |

### Activation

| Precedence | Mechanism | Example |
|------------|-----------|---------|
| 1 | CLI flag | `python .agent-meta/scripts/sync.py --harness opencode` |
| 2 | Environment variable | `AGENT_META_HARNESS=opencode` (ideal for a per-checkout direnv `.envrc`) |

There is deliberately **no project.yaml key for activation**: project.yaml is
committed and travels with the repo into every checkout, so a project-scoped
activation would activate the same harness everywhere and defeat the
isolation. Harness activation is per-machine/per-checkout — exactly what an
env var (or a one-off CLI flag) expresses.

### Write-isolation guard semantics

`sync.py` resolves the project root (from `--config`) as usual, then — only
when a harness is active — verifies it lies inside the harness's declared
`checkout-root`:

- **Inside** → sync proceeds; the harness, its branch convention and its
  provider hint are logged.
- **Outside** → sync **refuses** (exit 1) with the offending path, the
  declared checkout root and a remedy hint. Fail-closed: no partial writes.
  The project root is the single choke point all sync writes flow through,
  so this guard covers every write-capable mode (`sync`, `--init`,
  `--create-ext`, `--fill-defaults`, ...).
- **`--validate` test repo** → warn-only. The test repo is a deliberate
  scratch write; a hard fail would break CI setups that keep it outside all
  harness checkouts.

Because every harness checkout is its own clone, "sync writes only into its
own checkout" reduces to "the harness only ever runs sync from within its
own checkout" — which the guard now enforces mechanically.

```bash
# In ~/repos-oc/<repo> (Opencode checkout):
export AGENT_META_HARNESS=opencode
python .agent-meta/scripts/sync.py
# → harness active: opencode (checkout=~/repos-oc, branch=agent/opencode)

# Same command in ~/repos/<repo> with the env var still set:
#   !  harness 'opencode' write isolation violated: project-root
#      '/home/you/repos/<repo>' lies outside the declared checkout root
#      '/home/you/repos-oc' ...
```

### Backwards compatibility

With no harness active (no `--harness` flag, no `AGENT_META_HARNESS` env
var) every code path is inert: no config is read, no guard runs, behavior is
byte-identical to before. The `config/harnesses/` files are inert data until
explicitly activated.

---

## Open points / Follow-ups

Deliberately out of scope for the issue #547 implementation; tracked for
follow-up work:

1. **Strategy A vs. Strategy B (full multi-checkout runtime).** This
   implementation ships the config schema, the loader and the sync
   write-isolation guard (Strategy A: harnesses are independent plain
   checkouts, no cross-linking). Strategy B would additionally link the
   checkouts at runtime (e.g. shared worktree links or cross-checkout
   source sharing) so all harnesses can read the same source tree — larger
   change to sync.py, needs its own RFC round.
2. **Third-harness selection.** `config/harnesses/third.yaml` documents the
   generic third slot, but there is no mechanism yet for *how* a third tool
   claims it (config, CLI flag naming, or a dedicated file) — open question.
3. **Task partitioning per harness.** `default-providers` is an
   informational hint only. Enforcing it (e.g. sync suggesting the
   harness's providers, or orchestration refusing delegation outside the
   partition) is future work.
4. **Branch purge of ~30 merged local branches.** The multi-checkout
   workflow accumulates merged `agent/*` and `feat/*` branches on each
   checkout; a documented, safe purge routine (and whether it belongs in
   sync.py, a script or a documented git one-liner) is an open follow-up.
   Destructive git operations remain consent-gated (see AGENTS.md).
5. **Per-harness vs. central config dir.** Each checkout currently carries
   its own `.meta-config/`. Whether harness-specific config fragments
   should live per-checkout, in `config/harnesses/`, or in a shared
   central config directory is an open RFC question (cross-checkout config
   drift vs. single source of truth).
