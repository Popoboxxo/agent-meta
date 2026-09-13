#!/bin/bash
# Scenario assert for 50-spec-plan-workflow
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (50-spec-plan-workflow): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (50-spec-plan-workflow): $*"
    exit 1
}

# (a) docs/specs, docs/plans, docs/spikes sind gescaffoldet (R1)
[ -d "docs/specs" ] || fail "docs/specs not scaffolded"
[ -d "docs/plans" ] || fail "docs/plans not scaffolded"
[ -d "docs/spikes" ] || fail "docs/spikes not scaffolded"

# (b) spec-plan-workflow-SKILL.md nur bei enabled (rules-preset lazy -> skill channel)
[ -f ".claude/skills/spec-plan-workflow/SKILL.md" ] || fail "spec-plan-workflow SKILL.md missing"

# (c) dod_flag im generierten Pipeline-Block (Approval-Zeile)
grep -R "Abnahme erforderlich" .claude/ >/dev/null || fail "approval gate line missing"

# (d) file-index-Fallback greift real (KE off + external-system-override enabled)
[ -f "docs/INDEX.md" ] || fail "file-index fallback docs/INDEX.md missing"
[ ! -e "knowledge/wiki/index.md" ] || fail "KE index.md unexpectedly written"

# (e) enabled:false ist ein harter No-op (--validate-spec-plan Exit 0)
disabled_dir="$(mktemp -d)"
mkdir -p "$disabled_dir/.meta-config"
printf '%s\n' \
    'ai-providers:' \
    '- Claude' \
    'dod-preset: rapid-prototyping' \
    'platforms: []' \
    'knowledge-engine:' \
    '  enabled: false' \
    'spec-plan-workflow:' \
    '  enabled: false' \
    > "$disabled_dir/.meta-config/project.yaml"
( cd "$disabled_dir" && python3 "$REPO_ROOT/scripts/sync.py" --validate-spec-plan )
rc=$?
rm -rf "$disabled_dir"
[ "$rc" = "0" ] || fail "--validate-spec-plan nonzero for enabled:false (rc=$rc)"

echo "ASSERT OK (50-spec-plan-workflow): all markers present"
