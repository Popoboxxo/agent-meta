# Slimming Golden Baseline

Committed golden fixtures of the **generated agent output** for every active
role. They exist to back the equivalence gate of spec AC **B2** (see
`docs/specs/2026-09-19-dynamic-routing-template-slimming.md`, §3.7 and AC B2):

- **B2a** — every occurrence that was pre-classified as byte-identical to the
  canonical snippet text (including matching original indentation) must still be
  byte-identical to this baseline after the slimming change.
- **B2b** — every normalized near-duplicate must be listed in the diff manifest
  and be section-level semantically equivalent (no mandatory sentence lost).

This fixture set is the *target* of that comparison, not a rendering of the
templates.

## Freeze point

These files are frozen **after Block A (commit `62876f49`), before Block B**.
They are the pre-slimming reference output and must **not** be regenerated
casually — an incidental re-render would silently move the B2 goalposts.

## How the fixtures were generated

The fixtures come from the **real sync path** (never a re-implementation). The
test-repo mechanism performs a full sync of the main repo's templates and main
config into the target path:

```bash
mkdir -p .tmp/slimming-golden-gen
AGENT_META_TEST_REPO="$PWD/.tmp/slimming-golden-gen" python3 scripts/sync.py --validate
```

- **Provider:** `Claude` — output lands in `.claude/agents/` (see
  `config/ai-providers.yaml`, `agents_dir: .claude/agents`). The other active
  providers (Opencode, Gemini) are not part of this baseline.
- **Active roles:** **58** (`agent-meta` role whitelist in
  `.meta-config/project.yaml` lists 59; `se-component-requirements` is gated out
  by the `systems-engineering.enabled: false` activation gate).
- The harvested `<target>/.claude/agents/<role>.md` files are copied verbatim to
  `<role>.md` in this directory (role = file stem).
- `--validate` exited with rc `0`.

## Reproducibility check

Re-render into a second directory and byte-compare:

```bash
mkdir -p .tmp/slimming-golden-gen2
AGENT_META_TEST_REPO="$PWD/.tmp/slimming-golden-gen2" python3 scripts/sync.py --validate
diff -r .tmp/slimming-golden-gen/.claude/agents .tmp/slimming-golden-gen2/.claude/agents
```

A clean run of this check produced `diff -r` rc `0` (byte-identical, zero
differing files). If any file other than the `{{AGENT_META_DATE}}` line in
`agent-meta-manager.md` differs, stop — do not invent a normalization.

## `{{AGENT_META_DATE}}` coupling

`{{AGENT_META_DATE}}` is resolved by `_resolve_agent_meta_date` in
`scripts/lib/config.py` (lines 1085-1145) from the dated CHANGELOG heading. It is
the only non-deterministic placeholder in the generated output and renders solely
in `agent-meta-manager.md`:

```
**Version info:** v{{AGENT_META_VERSION}} ({{AGENT_META_DATE}})
```

For this baseline it resolved to `v1.2.0-beta.2 (2026-09-13)`. Consequence: if
the CHANGELOG's newest dated heading changes, `agent-meta-manager.md` legitimately
changes in that one line; every other fixture file must stay stable. No absolute
paths, hostnames or SHAs appear in any generated agent file.

## Update rule

Any update to this baseline requires an entry in the diff manifest
(`docs/plans/2026-09-19-dynamic-routing-template-slimming-diff-manifest.md`,
Task 16). Updating the fixtures without a manifest entry invalidates the B2 gate.
