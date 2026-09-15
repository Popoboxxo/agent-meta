#!/bin/bash
# Scenario assert for 63-context-file-modes
# SPEC-CONTEXT-FILE-MODES-2026-09-13, AC-21 (context_file.topology switch).
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate in the default `unified` topology. This assert drives the switch
# itself and proves three behaviours deterministically and offline:
#   1. default `unified` — byte-identical to the legacy state (no adapter index,
#      no `@AGENTS.md` reference, no GATE_NEUTRAL block; explicit
#      `topology: unified` renders byte-identically to the absent default);
#   2. `per-provider` opt-in — canonical core `AGENTS.md` carries the neutral
#      gate directive, the Claude adapter `CLAUDE.md` references `@AGENTS.md`,
#      and every non-adapter provider stays a direct reader of the core;
#   3. switch back to `unified` — the index-tracked adapter is torn down
#      backup-first and the tree converges (`--check` reports no pending).
# Exit 0 = all assertions hold; non-zero = first violated assertion.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (63-context-file-modes): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (63-context-file-modes): $*"
    exit 1
}

CONFIG=".meta-config/project.yaml"
CORE="AGENTS.md"
ADAPTER="CLAUDE.md"
INDEX=".agent-meta-context-adapters-managed"
NEUTRAL_MARK="# CRITICAL GATE (neutral)"
NEUTRAL_DIRECTIVE='MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`.'
WEAKEST_TIER_MARK="runtime-partially enforced"
SYNC_LOG=".scenario-63-sync.log"

[ -f "$CONFIG" ] || fail "project config missing: $CONFIG"
[ -f "$CORE" ] || fail "unified default: canonical core missing: $CORE"
[ -f "$ADAPTER" ] || fail "unified default: Claude context file missing: $ADAPTER"

# Run sync.py with the given CLI args; abort on a non-zero exit.
run_sync() {
    local rc=0
    python3 "$REPO_ROOT/scripts/sync.py" "$@" > "$SYNC_LOG" 2>&1 || rc=$?
    if [ "$rc" -ne 0 ]; then
        cat "$SYNC_LOG"
        fail "sync.py $* rc=$rc"
    fi
}

# Rewrite the project's context_file.topology (creating the block if absent).
set_topology() {
    local topology="$1"
    python3 - "$CONFIG" "$topology" <<'PY'
import re
import sys

path, topology = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8").read()
if re.search(r"(?m)^context_file:", text):
    text = re.sub(r"(?m)^  topology: .*$", "  topology: " + topology, text, count=1)
else:
    text = text.rstrip("\n") + (
        "\ncontext_file:\n  topology: " + topology + "\n  core_file: AGENTS.md\n"
    )
open(path, "w", encoding="utf-8").write(text)
PY
}

# ---------------------------------------------------------------- 1. unified --
[ ! -e "$INDEX" ] || fail "unified default wrote an adapter index: $INDEX"
grep -q '@AGENTS.md' "$ADAPTER" && fail "unified default rendered an adapter reference in $ADAPTER"
grep -qF "$NEUTRAL_MARK" "$CORE" && fail "unified default rendered the GATE_NEUTRAL core block"
grep -qF "$WEAKEST_TIER_MARK" "$CORE" \
    || fail "unified default core lost the shared weakest-tier gate block"

cp "$CORE" "$CORE.unified-baseline"
cp "$ADAPTER" "$ADAPTER.unified-baseline"

# Explicit `topology: unified` must render byte-identically to the absent default.
set_topology unified
run_sync
cmp -s "$CORE" "$CORE.unified-baseline" \
    || fail "explicit topology: unified changed $CORE vs. the absent default"
cmp -s "$ADAPTER" "$ADAPTER.unified-baseline" \
    || fail "explicit topology: unified changed $ADAPTER vs. the absent default"
[ ! -e "$INDEX" ] || fail "explicit topology: unified wrote an adapter index"

run_sync --check || fail "unified default: --check reported pending drift"

# ----------------------------------------------------------- 2. per-provider --
set_topology per-provider
run_sync

grep -q '@AGENTS.md' "$ADAPTER" \
    || fail "per-provider: Claude adapter $ADAPTER does not reference @AGENTS.md"
grep -qF "$NEUTRAL_MARK" "$CORE" \
    || fail "per-provider: canonical core $CORE lacks the neutral gate heading"
grep -qF "$NEUTRAL_DIRECTIVE" "$CORE" \
    || fail "per-provider: canonical core $CORE lacks the neutral gate directive"
grep -qF "$WEAKEST_TIER_MARK" "$CORE" \
    && fail "per-provider: canonical core still carries a weakest-tier runtime promise"
grep -qF "$NEUTRAL_MARK" "$ADAPTER" \
    && fail "per-provider: Claude adapter leaked the neutral core block"

[ -f "$INDEX" ] || fail "per-provider: adapter managed index missing: $INDEX"
[ "$(cat "$INDEX")" = "$ADAPTER" ] \
    || fail "per-provider: adapter index must list exactly $ADAPTER (direct readers stay on the core), got: $(tr '\n' ' ' < "$INDEX")"

# ------------------------------------------------------------- 3. rollback ----
cp "$ADAPTER" "$ADAPTER.adapter-baseline"
set_topology unified
run_sync

grep -q '@AGENTS.md' "$ADAPTER" \
    && fail "rollback: Claude adapter still references @AGENTS.md"
[ ! -e "$INDEX" ] || fail "rollback: adapter managed index was not removed"

backup="$(find . -maxdepth 1 -name "$ADAPTER.sync-backup-*" -print -quit)"
[ -n "$backup" ] || fail "rollback: adapter was not removed backup-first (no $ADAPTER.sync-backup-*)"
cmp -s "$backup" "$ADAPTER.adapter-baseline" \
    || fail "rollback: backup does not carry the pre-delete adapter content"

grep -qF "$WEAKEST_TIER_MARK" "$CORE" \
    || fail "rollback: unified core did not restore the shared weakest-tier block"

run_sync --check || fail "rollback: --check still reports pending drift (no convergence)"

echo "ASSERT OK (63-context-file-modes): unified default byte-identical; per-provider core+adapter; rollback backup-first and converged"
