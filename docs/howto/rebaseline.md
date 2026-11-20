# Rebaseline Helper

`scripts/rebaseline.py` performs a deterministic, ordered rebaseline of the
generated artifacts and their pin fixtures after a source change (agent
templates, rules, hooks or config). It replaces a sequence of manual commands
with one auditable run: measure the impact first, write only expected changes,
roll back on an unexpected change, verify the result and record why it happened.

The helper is provider-agnostic and stdlib-only. It never dispatches on a
provider or model name; provider differences stay in the config registries.
No template, rule or config source is edited by the helper itself.

> The root is derived from the helper location (`scripts/..`), not from the
> current working directory. Every `sync.py` subprocess runs with
> `cwd=<ROOT>` and an explicit `--config <ROOT>/.meta-config/project.yaml`.
> Use `--root DIR` to target a different checkout (e.g. a worktree).

## Quick start

Report drift without touching the repository (scratch only):

```bash
python3 scripts/rebaseline.py --check-only --root .
```

Apply a rebaseline after an intentional source change:

```bash
python3 scripts/rebaseline.py --reason "regenerate after role rename" --root .
```

A second write run with no source change is a no-op (exit 0, no new log line).

## CLI flags

| Flag | Semantics |
|---|---|
| `--reason TEXT` | Required in write mode (at least 10 non-empty characters). Free text recorded in the log; optional with `--check-only`. |
| `--expect GLOB` | Repeatable. Additional repo-relative path (POSIX, `fnmatch`) the diff gate may accept. |
| `--expect-key GLOB` | Repeatable. Additional key in `hashes.json` / `generated-file-hashes.json` / `context-hashes.json` the gate may accept. |
| `--base REF` | Diff base, default `origin/main`. Falls back to local `main` with a warning when no remote base is reachable. |
| `--check-only` / `--dry-run` | Synonyms. Measure and report only; no repository writes outside the scratch sink. |
| `--root DIR` | Override the repo root (default: parent of the helper's `scripts/` directory). |
| `--steps LIST` | Comma-separated subset of `ac01,standalone,sync,topology,digests,ceilings`. The fixed order is preserved. |
| `--skip-verify` | Skip the targeted pin-test verification (diagnosis only; noted in the log). |
| `--json` | Additionally emit the report as one JSON object (`pre`, `steps`, `post`, `result`). |

## Fixed step order

1. `ac01` — render the provider matrix into scratch and patch only differing
   keys in `tests/fixtures/ac01-baseline/hashes.json`.
2. `standalone` — `sync.py --render-standalone`, gate on `standalone/**`.
3. `sync` — normal `sync.py`, gate on generated hash files and tracked sync
   outputs.
4. `topology` — regenerate the a2a delegation fixtures.
5. `digests` — patch only the `_FIXTURE_TREES` digest literals in
   `tests/test_opencode_v2_surface.py`; the surrounding log comments are never
   touched.
6. `ceilings` — measure context ceilings and print an exact re-pin block on
   overshoot; no file is changed.

After the steps, a second check-only pass proves idempotency, targeted pin
tests verify the pins, and the log is written only when files actually changed.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK. Write mode: changes applied and gate-conformant. Check-only: no drift. |
| 1 | Check-only only: drift present (listed in the report). |
| 2 | Usage / preflight error: missing `--reason`, missing config, dirty rebaseline artifacts, unknown step, or disabled tmp sink. No write. |
| 3 | Diff-gate violation (unexpected file or key). All touched files restored byte-exact. |
| 4 | A step subprocess failed (non-zero from render / `sync.py`). Restored byte-exact. |
| 5 | Post-verification red (a targeted pin test failed). Changes remain; log records `verify: failed`. |
| 6 | Residual drift in the second check-only pass (idempotency broken). Changes remain; report lists `RESIDUAL`, log records `idempotency: failed`. Verification and logging still run. |

When both 5 and 6 apply, 5 wins.

## Diff gate

The gate is a **convention boundary against accidental mis-writes, not a
security boundary**. It compares against the preflight dirty set:

- Uncommitted source changes (templates, rules, config) are the baseline and
  are **not** violations — they define the rebaseline scope.
- The expected set is the union of the artifact allowlist, the stems derived
  from sources changed against `--base`, and explicit `--expect` /
  `--expect-key` globs.
- Sources without a stem mapping (e.g. `config/**`, `scripts/lib/**`) allow no
  keys automatically: pass `--expect-key` explicitly (fail-closed).
- Any changed file or changed JSON hash key outside the expected set is a
  violation: exit 3 and byte-exact rollback of everything the helper touched.
  `tests/test_opencode_v2_surface.py` is checked linewise — only edits to the
  `_FIXTURE_TREES` lines are accepted.

Hand-maintained golden files (slimming/compact goldens,
`topology-golden/schema-property-paths.json`, ceiling tables) are never written
by the helper. They are report-only and may remain dirty as input.

## Log

`python3 scripts/rebaseline.py --reason ...` appends exactly one JSON line per
changing run to `.meta-config/rebaseline-log.jsonl` (tracked, append-only,
outside `tests/fixtures/` so the AC-T4 digests are unaffected):

```json
{"ts": "...", "reason": "...", "base": "origin/main", "head": "...", "steps": ["ac01"], "changed_files": ["..."], "changed_keys": ["..."], "gate": "ok", "verify": "ok", "idempotency": "ok"}
```

No log line is written for check-only runs or write runs with zero changes.

## Scratch and tmp sink

Snapshots and scratch artifacts live in the repository tmp sink (`.tmp/`,
resolved via `resolve_tmp_paths`), never in the system temp directory
(repo containment). If the sink is disabled, the helper exits 2 instead of
falling back to an uncontrolled location.

## Notes

- To document the command in the `conventions` skill, add a reference in the
  howto/docs only. The skill source is generated; editing a template source
  would itself require a rebaseline. That reference is deferred to a follow-up
  change with the released helper (spec OF-7).
