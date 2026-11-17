#!/bin/bash
# Scenario assert for 99-artifact-locations-matrix (Issue #1186, plan T21).
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (99-artifact-locations-matrix): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (99-artifact-locations-matrix): $*"
    exit 1
}

# --- standard sync output ---------------------------------------------------
[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
[ -d ".claude/agents" ] || fail "agent directory missing: .claude/agents"

# --- Stage 14c resolved data file ------------------------------------------
[ -f ".meta-config/artifact-locations.resolved.json" ] || \
    fail "resolved data file missing: .meta-config/artifact-locations.resolved.json"

python3 - <<'PY' || fail "resolved artifact-locations contract violated"
import json
from pathlib import Path

payload = json.loads(Path(".meta-config/artifact-locations.resolved.json").read_text())
assert payload["schema_version"] == "1", payload.get("schema_version")
assert payload["enabled"] is True, payload.get("enabled")
assert payload["preset"] == "default", payload.get("preset")

classes = {entry["name"]: entry for entry in payload["classes"]}
assert len(classes) == 23, sorted(classes)
assert classes["specs"]["path"] == "docs/specs", classes["specs"]
assert classes["specs"]["mode"] == "files", classes["specs"]
assert classes["adr"]["naming"] == "ADR-{nnn}_{slug}.md", classes["adr"]
assert classes["scratch"]["path"] == ".tmp", classes["scratch"]
assert "project-docs" in classes, sorted(classes)

assert "docs/plans/audit-*.md" in payload["legacy"], payload["legacy"]
assert "docs/adr/[0-9][0-9][0-9][0-9]-*.md" in payload["legacy"], payload["legacy"]
assert ".meta-config/issue-labels-state.json" in payload["unmanaged"], payload["unmanaged"]

baseline = payload["baseline"]
assert set(baseline) == {"generated_at", "legacy_files"}, sorted(baseline)
assert isinstance(baseline["legacy_files"], list), baseline
PY

# --- scaffold markers: 11 files classes + D-6 conclusions ------------------
for dir in \
    docs/specs docs/plans docs/concepts docs/spikes \
    docs/reviews docs/audits docs/analysis docs/reports \
    docs/adr docs/traceability docs/runbooks docs/conclusions; do
    [ -f "$dir/.gitkeep" ] || fail "missing scaffold marker: $dir/.gitkeep"
done
[ -f ".tmp/.gitkeep" ] && fail "ephemeral scratch must not be scaffolded: .tmp/.gitkeep"

# --- generated class table reflects the resolved matrix --------------------
RULE=".claude/rules/artifact-locations.md"
[ -f "$RULE" ] || fail "generated artifact-locations rule missing: $RULE"
grep -q 'docs/specs' "$RULE" || fail "generated class table misses docs/specs"
grep -q 'docs/adr' "$RULE" || fail "generated class table misses docs/adr"
grep -q 'ARTIFACT_' "$RULE" || fail "generated rule misses ARTIFACT_* guidance"

# --- no unresolved builder placeholders ------------------------------------
if grep -rq '{{ARTIFACT_' .claude 2>/dev/null; then
    fail "unresolved {{ARTIFACT_ placeholder in generated output"
fi

echo "ASSERT OK (99-artifact-locations-matrix): resolved matrix, scaffold and generated table verified"
