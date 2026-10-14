#!/bin/bash
# Scenario assert for 77-meta-doctor-role
# (IC-23/IC-28, Task 0e.2: meta-doctor installation-diagnosis role).
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate. This scenario proves the generated `meta-doctor`:
#   1. is generated at all for every active provider,
#   2. has no `Write`/`Edit`/`Agent` in its tools frontmatter, and
#      `edit: deny` in the Opencode permission block,
#   3. has no `model:` field in its SOURCE template (models come from
#      tier-presets/role-defaults, never from the template),
#   4. resolves all placeholders except escaped doc examples,
#   5. has NO keyword rule in routing rules (addressability: name_only; it stays
#      name-dispatchable via target_agents/name_index),
#   7. contains no `.tmp` literal (configured sink `scratch/out` is rendered instead),
#      no "strict(ly) read-only" wording, and the exact bash allowlist lines.
#   6. still carries the mandatory STATUS/RESULT/ARTIFACTS output contract and the
#      `doctor-findings-v1` contract marker.
# Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (77-meta-doctor-role): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (77-meta-doctor-role): $*"
    exit 1
}

# 1. generated for both active providers (Claude + Opencode).
for prov in .claude .opencode; do
    [ -f "$prov/agents/meta-doctor.md" ] || fail "meta-doctor.md missing for $prov"
done

# 2. tool set without Write/Edit/Agent in the Claude frontmatter.
CLAUDE_TOOLS="$(sed -n '/^---$/,/^---$/p' .claude/agents/meta-doctor.md | sed -n '/^tools:/,/^[a-z]/p')"
for forbidden in Write Edit Agent; do
    if printf '%s\n' "$CLAUDE_TOOLS" | grep -qE "^[-[:space:]]*${forbidden}\$"; then
        fail "meta-doctor declares forbidden tool '${forbidden}' in Claude frontmatter"
    fi
done
# Opencode must deny edits explicitly.
grep -q 'edit: deny' .opencode/agents/meta-doctor.md \
    || fail "Opencode permission block does not deny edit (no Write/Edit tools)"

# 3. source template declares no model: field (model resolution stays in config).
SOURCE="$REPO_ROOT/agents/1-generic/meta-doctor.md"
[ -f "$SOURCE" ] || fail "source template missing: $SOURCE"
if sed -n '/^---$/,/^---$/p' "$SOURCE" | grep -qE '^model:'; then
    fail "source template declares a model: field — model resolution belongs in tier-presets/role-defaults"
fi

# 4. unresolved placeholders: only the escaped doc example {{ALLEVAR}} may survive.
for prov in .claude .opencode; do
    leftover="$(grep -oE '\{\{[A-Za-z][A-Za-z0-9_]*\}\}' "$prov/agents/meta-doctor.md" | sort -u | grep -v '^{{ALLEVAR}}$' || true)"
    if [ -n "$leftover" ]; then
        fail "$prov output has unresolved placeholders: $leftover"
    fi
done

# 5. addressability name_only: no keyword rule for the role in routing.rules
#    (IC-28 Nr. 6); it must still be name-dispatchable (target_agents + name_index).
REPO_ROOT="$REPO_ROOT" python3 - <<'PY' || fail "meta-doctor routing is not name_only (keyword rule present or name entry missing)"
import os, sys
sys.path.insert(0, os.environ["REPO_ROOT"])
from pathlib import Path
from scripts.lib.delegation_table import get_routing_rules

rules = get_routing_rules(Path(os.environ["REPO_ROOT"]), {}, {})
if any(r.get("agent") == "meta-doctor" for r in rules["rules"]):
    sys.exit(1)
if "meta-doctor" not in rules["target_agents"]:
    sys.exit(1)
entry = [n for n in rules["name_index"] if n.get("agent") == "meta-doctor"]
sys.exit(0 if entry and entry[0].get("addressability") == "name_only" else 1)
PY

# 6. mandatory output contract markers present.
for marker in 'STATUS:' 'RESULT:' 'ARTIFACTS:' 'doctor-findings-v1'; do
    grep -q "$marker" .claude/agents/meta-doctor.md \
        || fail "output contract marker '$marker' missing"
done

# 7. AC-88/AC-95: sink path rendered from the configured sink (scratch/out), no `.tmp`
#    literal, no "strict(ly) read-only" wording, exact allowlist lines.
for prov in .claude .opencode; do
    f="$prov/agents/meta-doctor.md"
    if grep -qE '(^|[^A-Za-z0-9_])\.tmp([^A-Za-z0-9_]|$)' "$f"; then
        fail "$f contains a literal .tmp (sink must come from {{TMP_SINK_PATH}})"
    fi
    grep -q 'scratch/out/doctor/' "$f" || fail "$f does not render the configured sink scratch/out/doctor/"
    if grep -qiE 'strict(ly)?[ -]read-only|strikt read-only' "$f"; then
        fail "$f calls meta-doctor strictly read-only (AC-95)"
    fi
    for line in \
        'python3 .agent-meta/scripts/sync.py --doctor --json' \
        'python3 .agent-meta/scripts/sync.py --doctor --json --out scratch/out/doctor/<YYYYMMDD-HHMMSS>.json' \
        'python3 .agent-meta/scripts/sync.py --check --dry-run' \
        'python3 .agent-meta/scripts/sync.py --context-report --json' \
        'python3 .agent-meta/scripts/sync.py --cleanup-preview' \
        'git status --short [-- <rel-path>]' \
        'git log --oneline -n <N> [-- <rel-path>]' \
        'git diff --stat [-- <rel-path>]' \
        'git diff --name-only [-- <rel-path>]'; do
        grep -qxF "$line" "$f" || fail "$f: allowlist line missing: $line"
    done
    for dropped in '--strict' '--provider <P>'; do
        if grep -qF -- "$dropped" "$f"; then fail "$f: dropped allowlist form present: $dropped"; fi
    done
done

echo "ASSERT OK (77-meta-doctor-role): generated, no Write/Edit tools, no model field, placeholders resolved, name_only routing (no keyword rule), output contract present, no .tmp literal, no strict-read-only wording, exact allowlist"
