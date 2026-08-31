#!/bin/bash
# hook: artifact-freshness
# version: 1.0.0
# event: Manual
# description: Pre-release gate — blocks release if a generated artifact is older than the source it was built from (config: .agent-meta/generated-artifacts.yaml)
# enabled_by_default: false

# --- Gate contract (see docs/RELEASE_GATES.md) ---
# Run standalone (`bash release-gates/artifact-freshness.sh`) or via the
# release-gates/ dispatcher (pre-release-check.sh). Exit 0 = pass or
# self-skip (disabled, or prerequisites missing). Exit non-zero = fail,
# blocks the release.

set -u

PROJECT_ROOT="${PROJECT_ROOT:-$PWD}"
cd "$PROJECT_ROOT" || exit 1

GATE_NAME="artifact-freshness"

# --- Enabled/disabled ---
# Baked at sync-time by scripts/lib/hooks.py::sync_release_gates() from
# dod.resolve_release_gates() (project.yaml `release-gates.artifact-freshness.enabled`
# > dod-preset default > this header's `enabled_by_default`). The `:=` form
# only assigns when the var is still unset, so an explicit
# `PRE_RELEASE_GATE_ENABLED=false bash release-gates/artifact-freshness.sh`
# always wins for a one-off, single-gate override.
: "${PRE_RELEASE_GATE_ENABLED:={{RELEASE_GATE_ENABLED_DEFAULT}}}"

if [ "$PRE_RELEASE_GATE_ENABLED" != "true" ]; then
  echo "[SKIP] $GATE_NAME: gate disabled (release-gates.artifact-freshness.enabled=false)"
  exit 0
fi

# --- Config convention ---
# .agent-meta/generated-artifacts.yaml at the consumer project root.
# Supported subset (stdlib-only, NOT a full YAML parser):
#
#   artifacts:
#     - source: VERSION
#       generated: dist/manifest.json
#     - source: src/schema.py
#       generated: docs/api/schema.json
#
# One list under a single top-level `artifacts:` key; each entry is a
# `- source: <path-or-glob>` / `generated: <path-or-glob>` pair on two
# consecutive lines. No nesting, no anchors, no multi-line scalars.
CONFIG_FILE=".agent-meta/generated-artifacts.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "[SKIP] $GATE_NAME: no $CONFIG_FILE found — opt-in check not configured"
  exit 0
fi

if ! command -v python3 &>/dev/null; then
  echo "[SKIP] $GATE_NAME: python3 not available — cannot parse config"
  exit 0
fi

python3 - "$CONFIG_FILE" "$GATE_NAME" <<'PYEOF'
import sys
import subprocess
import glob as globmod
import os

config_path, gate_name = sys.argv[1], sys.argv[2]

# --- minimal stdlib-only parser for the documented subset ---
pairs = []
with open(config_path, encoding="utf-8") as f:
    lines = f.readlines()

in_artifacts = False
current = {}
for raw in lines:
    line = raw.rstrip("\n")
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        continue
    if stripped == "artifacts:":
        in_artifacts = True
        continue
    if not in_artifacts:
        continue
    if stripped.startswith("- source:"):
        if current.get("source") and current.get("generated"):
            pairs.append(current)
        current = {"source": stripped[len("- source:"):].strip().strip('"\'')}
    elif stripped.startswith("source:"):
        current["source"] = stripped[len("source:"):].strip().strip('"\'')
    elif stripped.startswith("generated:"):
        current["generated"] = stripped[len("generated:"):].strip().strip('"\'')
if current.get("source") and current.get("generated"):
    pairs.append(current)

def newest_mtime(pattern):
    matches = globmod.glob(pattern, recursive=True)
    if not matches:
        return None
    return max(os.path.getmtime(m) for m in matches if os.path.isfile(m))

def git_mtime(pattern):
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", pattern],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            return float(out.stdout.strip())
    except Exception:
        pass
    return None

errors = []
checked = 0
for pair in pairs:
    source, generated = pair["source"], pair["generated"]
    src_mtime = newest_mtime(source) or git_mtime(source)
    gen_mtime = newest_mtime(generated)
    if src_mtime is None:
        print(f"[SKIP] {gate_name}: source not found: {source}")
        continue
    checked += 1
    if gen_mtime is None:
        errors.append(f"{generated} (from {source}) — generated artifact missing")
        continue
    if src_mtime > gen_mtime:
        errors.append(f"{generated} is older than its source {source} — rebuild required")

for e in errors:
    print(f"[FAIL] {gate_name}: {e}")
if not errors:
    print(f"[INFO] {gate_name}: checked {checked} artifact pair(s), all fresh")

sys.exit(1 if errors else 0)
PYEOF
