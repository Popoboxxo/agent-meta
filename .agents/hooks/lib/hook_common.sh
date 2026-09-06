#!/bin/bash
# lib: hook_common
# version: 1.0.0
# description: Shared helper functions sourced by other hook scripts (issue #601 dedup)
#
# NOT a hook itself — no `event`/`matcher` header, sync.py never registers it
# in settings.json. Deployed verbatim to <hooks_dir>/lib/hook_common.sh
# alongside the hook scripts that source it
# (scripts/lib/hooks.py::sync_hook_lib()). Every hook that sources this file
# does so via a path relative to its own location:
#
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   source "$SCRIPT_DIR/lib/hook_common.sh"
#
# Security-boundary hooks (orchestrator-guard.sh, dod-push-check.sh) treat a
# failed `source` (this file missing/unreadable) as fail-closed, not
# fail-open — see the sourcing snippet at the top of each of those scripts.
# Non-security hooks may fail open on a missing lib, matching their prior
# fail-open behavior on a missing python3 (issue #595 only hardens the two
# hooks that are actual security controls, not every hook that happens to
# use python3).
#
# Every function here is stdlib-only (python3/python, common POSIX
# utilities) — no new external dependency for consumer projects.

# --- Python interpreter resolution -------------------------------------

# hook_have_python: return code 0 if "python3" or "python" is on PATH.
hook_have_python() {
  command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1
}

# hook_python_bin: prints "python3" or "python" (whichever is found first),
# prints nothing if neither is available. Callers that must fail closed on a
# missing interpreter (issue #595) check hook_have_python explicitly BEFORE
# relying on this — an empty result here must never be silently treated as
# "allow", the call site decides.
hook_python_bin() {
  if command -v python3 >/dev/null 2>&1; then
    printf '%s' "python3"
  elif command -v python >/dev/null 2>&1; then
    printf '%s' "python"
  fi
}

# --- JSON field extraction ----------------------------------------------

# hook_json_get <json-string> <dotted.path> [default]
# Extracts a nested scalar field from a JSON object via a dotted path
# (e.g. "tool_input.command"). Prints <default> ("" if omitted) when the
# path does not resolve, the value is an object/array, or the JSON itself
# fails to parse. Never raises — always safe to use in a guard's hot path.
#
# Replaces the near-identical
#   read -r -d '' _PARSE <<'PYEOF' ... python3 -c "$_PARSE" ... | head -N
# pattern that used to be copy-pasted across dod-push-check.sh,
# lifecycle-check.sh, sync-on-config-change.sh and orchestrator-guard.sh
# (issue #601).
hook_json_get() {
  local json="$1" path="$2" default="${3:-}"
  local py
  py="$(hook_python_bin)"
  if [ -z "$py" ]; then
    printf '%s' "$default"
    return 0
  fi
  printf '%s' "$json" | "$py" -c "
import json, sys

path, default = sys.argv[1], sys.argv[2]
try:
    d = json.load(sys.stdin)
except Exception:
    print(default)
    sys.exit(0)

cur = d
for key in path.split('.'):
    if isinstance(cur, dict):
        cur = cur.get(key)
    else:
        cur = None
        break

if cur is None or isinstance(cur, (dict, list)):
    print(default)
else:
    print(cur)
" "$path" "$default" 2>/dev/null || printf '%s' "$default"
}

# --- Credential redaction (issue #596) -----------------------------------

# hook_redact_secrets <text>
# Best-effort masking of common credential shapes in a raw string before it
# is written anywhere persistent (e.g. an audit log): URL-embedded
# basic-auth (scheme://user:pass@host), "Authorization: Bearer <token>",
# key=value / key: value pairs for common credential key names, common CLI
# --token/--password flags, and a handful of well-known token prefixes
# (GitHub PATs, Slack, AWS access keys).
#
# NOT an exhaustive secret scanner (that is a different, much larger class
# of tool) — this closes the specific gap of a raw shell command containing
# an obvious credential ending up verbatim in a plaintext, previously
# world-readable audit log (issue #596). Order matters: the specific
# Bearer-token pattern runs before the generic key=value pattern so
# "Authorization: Bearer xyz" doesn't leak "xyz" via a partial first match.
hook_redact_secrets() {
  local text="$1"
  local py
  py="$(hook_python_bin)"
  if [ -z "$py" ]; then
    # No interpreter to redact with — refuse to pass the raw text through
    # unredacted; the caller (hook_audit_log_append) treats an empty
    # result as "do not log this line" rather than logging it verbatim.
    return 0
  fi
  printf '%s' "$text" | "$py" -c "
import re, sys

s = sys.stdin.read()

patterns = [
    # URL-embedded basic-auth credentials: scheme://user:pass@host
    (re.compile(r'([a-zA-Z][a-zA-Z0-9+.\-]*://)([^/\s:@]+):([^/\s@]+)@'), r'\1***:***@'),
    # Authorization: Bearer <token>
    (re.compile(r'(?i)\bauthorization\s*:\s*bearer\s+\S+'), 'Authorization: Bearer ***'),
    (re.compile(r'(?i)\bbearer\s+[A-Za-z0-9\-_.=]{6,}'), 'Bearer ***'),
    # key=value / key: value pairs for common credential key names
    (re.compile(r'(?i)\b(token|api[_-]?key|apikey|secret|password|passwd|pwd|auth|authorization)\b(\s*[:=]\s*)(\S+)'),
     r'\1\2***'),
    # --token <value> / --password <value> style (space-separated)
    (re.compile(r'(?i)(--?(?:token|password|passwd|secret|api-key|apikey)\s+)(\S+)'), r'\1***'),
    # Well-known token prefixes (GitHub, Slack, AWS)
    (re.compile(r'\b(ghp_|gho_|ghs_|ghu_|ghr_|github_pat_)[A-Za-z0-9_]+'), r'\1***'),
    (re.compile(r'\bxox[baprs]-[A-Za-z0-9\-]+'), '***SLACK_TOKEN***'),
    (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), '***AWS_KEY***'),
]
for pat, repl in patterns:
    s = pat.sub(repl, s)
sys.stdout.write(s)
" 2>/dev/null
}

# --- Audit log append: redaction + permission hardening + rotation -------
# (issues #596/#597)

# hook_audit_log_append <logfile> <line>
# Appends one already-formatted line to <logfile> after redacting secrets
# (hook_redact_secrets). Creates the file with 600 permissions if it does
# not exist yet, and re-tightens it to 600 on every call in case something
# else loosened it in between. Truncates the file to the newest
# HOOK_AUDIT_LOG_KEEP_LINES (default 1000) lines once it grows past
# HOOK_AUDIT_LOG_MAX_LINES (default 2000) — simple unbounded-growth cap,
# not a full logrotate replacement. Both env vars are overridable, mainly
# for tests that need a small cap to exercise rotation quickly.
#
# Never fails the caller — logging is best-effort, all errors swallowed
# (mirrors the prior inline `>> "$_AUDIT_LOG" 2>/dev/null || true` behavior
# in orchestrator-guard.sh).
hook_audit_log_append() {
  local logfile="$1" line="$2"
  local max="${HOOK_AUDIT_LOG_MAX_LINES:-2000}"
  local keep="${HOOK_AUDIT_LOG_KEEP_LINES:-1000}"

  mkdir -p "$(dirname "$logfile")" 2>/dev/null || return 0

  if ! hook_have_python; then
    # No interpreter to redact with — refuse to write the raw,
    # potentially credential-bearing line at all (issue #596: silently
    # dropping this one entry is safer than logging it unredacted).
    return 0
  fi
  local redacted
  redacted="$(hook_redact_secrets "$line")"
  printf '%s\n' "$redacted" >> "$logfile" 2>/dev/null || return 0
  chmod 600 "$logfile" 2>/dev/null || true

  local lines
  lines=$(wc -l < "$logfile" 2>/dev/null)
  case "$lines" in
    ''|*[!0-9]*) lines=0 ;;
  esac
  if [ "$lines" -gt "$max" ]; then
    tail -n "$keep" "$logfile" > "$logfile.tmp" 2>/dev/null && mv "$logfile.tmp" "$logfile" 2>/dev/null
    chmod 600 "$logfile" 2>/dev/null || true
  fi
  return 0
}

# --- GRAPHIFY_BIN validation (issue #599) --------------------------------

# hook_resolve_graphify_bin
# Prints the executable path/name to use for graphify. Never trusts an
# arbitrary $GRAPHIFY_BIN value outright — a process able to set that env
# var could otherwise get its own arbitrary binary executed on every
# Read/Glob/Bash/Grep call that fires the graphify guards. A candidate from
# $GRAPHIFY_BIN is only accepted if it is:
#   1) an absolute path (rejects PATH-search-relative injection),
#   2) an existing, executable, regular file,
#   3) named exactly "graphify" (or "graphify.exe" on Windows) — rejects
#      pointing at an unrelated/malicious binary via a misleadingly-named
#      env var,
#   4) not group- or world-writable (rejects a binary an attacker could
#      still overwrite after the fact even at a nominally-trusted path).
# Any check failing falls back to the literal command name "graphify"
# resolved via a plain PATH lookup by the caller (`command -v graphify`),
# same fallback as before this hook could be configured via env var at all.
hook_resolve_graphify_bin() {
  local candidate="${GRAPHIFY_BIN:-}"
  local base
  base="$(basename "$candidate" 2>/dev/null)"

  case "$candidate" in
    /*) ;;   # absolute path — keep validating
    *) candidate="" ;;
  esac

  if [ -n "$candidate" ] && { [ "$base" != "graphify" ] && [ "$base" != "graphify.exe" ]; }; then
    candidate=""
  fi

  if [ -n "$candidate" ] && { [ ! -f "$candidate" ] || [ ! -x "$candidate" ]; }; then
    candidate=""
  fi

  if [ -n "$candidate" ] && command -v stat >/dev/null 2>&1; then
    # Reject if either the group or the other write bit is set — check the
    # last two octal digits individually (not as a combined 2-char glob),
    # so a set GROUP-write bit isn't missed just because OTHER is 0 (and
    # vice versa).
    local perm go
    perm="$(stat -c '%a' "$candidate" 2>/dev/null || stat -f '%Lp' "$candidate" 2>/dev/null || echo "")"
    if [ -n "$perm" ]; then
      go="${perm: -2}"
      case "${go:0:1}${go:1:1}" in
        *[2367]*) candidate="" ;;
      esac
    fi
  fi

  if [ -n "$candidate" ]; then
    printf '%s' "$candidate"
  else
    printf '%s' "graphify"
  fi
}
