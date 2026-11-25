#!/bin/bash
# hook: artifact-path-guard
# version: 1.1.0
# event: PreToolUse
# matcher: ""
# description: Route artifact writes into the configured artifact-locations class path.
# changelog: 1.1.0: issue #1251 -- read the project anchor exclusively from adapter-owned AM_PROJECT_DIR; preserve payload-cwd walk-up and fail-open missing-data behavior
# enabled_by_default: false

# Routing convention, NOT a security boundary (issue #1186, T16, spec §4.5).
# AC-09 is fulfilled in two stages: the consistency check always warns (T14),
# this hook blocks legacy[] targets (both modes) and misroutes (strict only)
# once a project deliberately opts in.  Opt-in is why enabled_by_default is
# false: a default-active hook would block existing projects' audit-*.md files
# before the migration is even described.  Missing/corrupt data fails open.
#
# Reads <root>/.meta-config/artifact-locations.resolved.json (Stage 14c, T15),
# the single pre-resolved data file -- no Python resolver and no YAML per call.
# Marker -> unmanaged -> legacy -> class path -> managed tree -> root (D3).
# No content, extension or branch inspection; nothing is rewritten.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/hook_common.sh
source "$SCRIPT_DIR/lib/hook_common.sh"

INPUT=$(cat)

TOOL_NAME=$(hook_json_get "$INPUT" "tool_name")
FILE_PATH=$(hook_json_get "$INPUT" "tool_input.file_path")

# This hook only classifies targets for tool names the framework knows.  An
# unknown tool is not evidence of a misroute -- fail open (routing convention).
if ! hook_known_tool_name "$TOOL_NAME"; then
  exit 0
fi

# No target path: nothing to route.
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Resolve the project root: $AM_PROJECT_DIR when it carries .meta-config/,
# else the nearest ancestor of the payload cwd holding the resolved data file.
ROOT=""
if [ -n "${AM_PROJECT_DIR:-}" ] && [ -d "$AM_PROJECT_DIR/.meta-config" ]; then
  ROOT="$AM_PROJECT_DIR"
else
  CWD_RAW=$(hook_json_get "$INPUT" "cwd")
  case "$CWD_RAW" in
    /*)
      dir="$CWD_RAW"
      while [ -n "$dir" ] && [ "$dir" != "/" ]; do
        if [ -f "$dir/.meta-config/artifact-locations.resolved.json" ]; then
          ROOT="$dir"
          break
        fi
        dir="$(dirname "$dir")"
      done
      ;;
  esac
fi
if [ -z "$ROOT" ]; then
  ROOT="${AM_PROJECT_DIR:-}"
fi

DATA_FILE="$ROOT/.meta-config/artifact-locations.resolved.json"

# Missing data file -> never block (fail-open, one warning line).
if [ ! -f "$DATA_FILE" ]; then
  echo "artifact-path-guard: WARN: data file $DATA_FILE missing; allowing (fail-open)" >&2
  exit 0
fi

MARKERS=".gitkeep .gitignore .keep"

# One stdlib JSON pass over the pre-resolved file; emits one status line:
# ALLOW | WARN:<message> | BLOCK:<message> | FAIL:<message>.
RESULT="$(python3 - "$DATA_FILE" "$FILE_PATH" "$ROOT" "$MARKERS" <<'PY'
import fnmatch
import json
import os
import sys

data_path, file_path, root, markers_raw = sys.argv[1:5]
markers = set(markers_raw.split())

try:
    with open(data_path, encoding="utf-8") as fh:
        data = json.load(fh)
except Exception:
    print("FAIL:artifact-path-guard: WARN: unreadable data file (corrupt JSON); allowing (fail-open)")
    sys.exit(0)


def matches(relpath, pattern):
    """Mirror lib.artifact_status._pattern_matches (framework preset shapes)."""
    pattern = pattern.replace("\\", "/")
    if not pattern:
        return False
    if pattern.endswith("/**"):
        return relpath.startswith(pattern[:-2])
    if pattern.endswith("/"):
        return relpath.startswith(pattern)
    if "**" in pattern:
        return relpath.startswith(pattern.split("**", 1)[0])
    if any(c in pattern for c in "*?["):
        return fnmatch.fnmatchcase(relpath, pattern)
    return relpath == pattern or relpath.startswith(pattern + "/")


def matches_any(relpath, patterns):
    return any(matches(relpath, p) for p in (patterns or []))


# Normalize the target to a project-relative POSIX path.
target = file_path.replace("\\", "/")
if os.path.isabs(target):
    root_norm = os.path.realpath(root)
    target_norm = os.path.realpath(target)
    try:
        rel = os.path.relpath(target_norm, root_norm).replace("\\", "/")
    except ValueError:
        rel = target_norm.replace("\\", "/")
    if rel == ".." or rel.startswith("../") or os.path.isabs(rel):
        print("ALLOW")  # outside the project root: repo-containment's job
        sys.exit(0)
else:
    rel = target
    while rel.startswith("./"):
        rel = rel[2:]
    if not rel or rel == "." or rel.startswith("../"):
        print("ALLOW")
        sys.exit(0)

# 1. Directory markers are never blocked (scaffold exception, §3.5).
if os.path.basename(rel) in markers:
    print("ALLOW")
    sys.exit(0)

classes = data.get("classes") or []
legacy = data.get("legacy") or []
unmanaged = data.get("unmanaged") or []
strict = bool(data.get("strict", False))

# 2. unmanaged[] -> allow in both modes (D-8).
if matches_any(rel, unmanaged):
    print("ALLOW")
    sys.exit(0)

# 3. legacy[] -> block in both modes.  Legacy is BEFORE class-path release,
#    otherwise the flat ADR legacy glob inside docs/adr would be ineffective.
if matches_any(rel, legacy):
    print("BLOCK:artifact-path-guard: '%s' targets a legacy[] path; place new artifacts under an artifact-locations class path or add a legacy entry." % rel)
    sys.exit(0)

# 4. Class path (or a declared file-set file) -> allow.
for cls in classes:
    path = cls.get("path")
    if path:
        path = path.replace("\\", "/").rstrip("/")
        if rel == path or rel.startswith(path + "/"):
            print("ALLOW")
            sys.exit(0)
    else:
        for pat in (cls.get("patterns") or []):
            pat = pat.replace("\\", "/")
            if not any(c in pat for c in "*?{}[]") and rel == pat:
                print("ALLOW")
                sys.exit(0)

# Guess the intended class from a path segment, for the repair hint.
expected = None
expected_cls = None
for cls in classes:
    name = cls.get("name") or ""
    path = cls.get("path")
    if path and name and name in rel.split("/"):
        expected = path.replace("\\", "/").rstrip("/")
        expected_cls = name
        break

# 5. Managed tree (top-level segment of a declared class path) -> misroute.
managed_roots = set()
for cls in classes:
    path = cls.get("path")
    if path:
        first = path.replace("\\", "/").strip("/").split("/", 1)[0]
        if first:
            managed_roots.add(first)

if rel.split("/", 1)[0] in managed_roots:
    hint = ("expected '%s' (classes.%s.path)" % (expected, expected_cls)
            if expected else "expected a declared artifact-locations class path")
    message = ("artifact-path-guard: '%s' is a misroute in a managed tree; %s; "
               "add to artifact-locations.classes.<x>.path or a legacy entry." % (rel, hint))
    print(("BLOCK:" if strict else "WARN:") + message)
    sys.exit(0)

# 6. Root: outside all managed trees -> allow.
print("ALLOW")
PY
)"

case "$RESULT" in
  ALLOW)   exit 0 ;;
  WARN:*)  echo "${RESULT#WARN:}" >&2;  exit 0 ;;
  BLOCK:*) echo "${RESULT#BLOCK:}" >&2; exit 2 ;;
  FAIL:*)  echo "${RESULT#FAIL:}" >&2;  exit 0 ;;
  *)       exit 0 ;;   # unknown status -> fail open
esac
