#!/bin/bash
# lib: hook_common
# version: 1.7.0
# description: Shared helper functions sourced by other hook scripts (issue #601 dedup)
# changelog: v1.7.0: hook_shell_scan_py — is_fork_bomb ends a function body at the depth-matching '}' inside the 512-character window instead of the first unquoted one, so bombs with a brace or ${...} before the self-call are detected (#1050); an exhausted window still fails closed; v1.6.0: hook_known_tool_name knows Agent, SendMessage and the other current built-ins (Agent replaced Task, so the closed allow-list blocked all delegation); EnterWorktree/ExitWorktree stay blocked on purpose (no-worktree-isolation); v1.5.0: hook_shell_scan_py — the fork-bomb detector reads a function name exactly at any length (the 64-character cap is gone; the reverse scans of two '()' pairs cannot overlap, so it stays linear) and fails closed when a body has no unquoted '}' in its first 512 characters, blocking the candidate instead of skipping it (deliberate false-alarm class: long inline function bodies); the body still ends at the first unquoted '}' without brace nesting — known gap, documented in `rules/1-generic/branch-guard.md` (#943 follow-up); v1.4.0: hook_shell_resolver_py — one command-word resolver (wrapper grammar with positional arity, transparent '--', `case … in` arms, function bodies, subshells/groups, leading keywords) shared by the fail-closed guards instead of a per-hook copy; repo-containment-impl.sh uses it so its write-target detector resolves the same command word orchestrator-guard-impl.sh does (its inline copy is unchanged here, see the emitter's adoption note); v1.3.1: hook_shell_scan_py now keeps its quote state in sync for ANSI-C ($'...') and locale ($"...") quoting (review finding F1), stops tracking a heredoc delimiter it cannot resolve so the body is over-scanned instead of hiding the rest of the command (F2, deliberate divergence from bash: bash does not expand the delimiter either, but an unknown delimiter must not license skipping input), and cuts a trailing '#' comment from the cleaned code as well as from the statement stream (F4); v1.3.0: hook_shell_scan_py — one quote/heredoc-aware shell statement splitter plus the linear-time fork-bomb detector, shared by both fail-closed guards (#943 (a)/(c)/(j), #944 SR-B-16); hook_is_meta_submodule_dir — the project-root walk-ups skip a nested .agent-meta checkout's own .meta-config/ when an enclosing project has one (#943 (l)); v1.2.0: hook_known_tool_name is the single allow-list both fail-closed guards use before classifying a payload — an empty, non-string or unrecognized tool_name now blocks instead of falling through their `*) exit 0` allow branch (review finding M2, #954 follow-up), and the header names the three guards that source this lib and verify the interpreter; v1.1.0: hook_protected_branches + hook_push_arg_parser_py — the protected-branch set and the git-push flag/short-cluster walk of dod-push-check.sh live here once instead of being built twice (#949), hook_json_usable detects an interpreter that exits 0 with garbage, exits non-zero or is missing — the probe sentinel now lives in the payload and its fallback default is distinct, so a failing interpreter can no longer look usable (#954); v1.0.1: hook_json_get no longer returns "" for a present field whose value holds a lone surrogate or whose payload holds invalid UTF-8 (W2-B1 R2-2)
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
# Security-boundary hooks (orchestrator-guard-impl.sh,
# repo-containment-impl.sh, dod-push-check.sh) treat a failed `source` (this
# file missing/unreadable) as fail-closed, not fail-open — see the sourcing
# snippet at the top of each of those scripts. All three additionally call
# hook_json_usable() before trusting any field, so a python3/python that is
# missing, exits non-zero or exits 0 while printing garbage also fails closed.
# Non-security hooks may fail open on a missing lib, matching their prior
# fail-open behavior on a missing python3 (issue #595 only hardens the hooks
# that are actual security controls, not every hook that happens to use
# python3).
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
  # Bytes in, bytes out (W2-B1 R2-2): invalid UTF-8 in the payload and a
  # lone surrogate escape ("\ud800") in a value used to make the decode or
  # print() raise under a strict UTF-8 locale, so a present field came back
  # as "" (a guard then saw no command at all). Undecodable input bytes are
  # passed through as-is (surrogateescape), lone surrogates are written as
  # their raw 3-byte encoding (surrogatepass) -- never dropped.
  printf '%s' "$json" | "$py" -c "
import json, sys

path, default = sys.argv[1], sys.argv[2]


def emit(text):
    try:
        data = text.encode('utf-8', 'surrogateescape')
    except UnicodeEncodeError:
        data = text.encode('utf-8', 'surrogatepass')
    sys.stdout.buffer.write(data + b'\n')


try:
    d = json.loads(sys.stdin.buffer.read().decode('utf-8', 'surrogateescape'))
except Exception:
    emit(default)
    sys.exit(0)

cur = d
for key in path.split('.'):
    if isinstance(cur, dict):
        cur = cur.get(key)
    else:
        cur = None
        break

if cur is None or isinstance(cur, (dict, list)):
    emit(default)
else:
    emit(str(cur))
" "$path" "$default" 2>/dev/null || printf '%s' "$default"
}

# hook_json_usable
# Returns 0 only when hook_json_get round-trips a sentinel through a real
# JSON parse. A python3/python on PATH that EXITS 0 but prints garbage (a
# broken or hostile PATH shim) cannot be told apart from a working
# interpreter by exit status alone: hook_json_get would hand its garbage
# back as the field value, and a security hook that treats "no command" as
# "allow" would then let a push through (issue #954). Security hooks call
# this once before trusting any field and fail closed on a non-zero result
# (orchestrator-guard-impl.sh, repo-containment-impl.sh, dod-push-check.sh).
#
# The sentinel travels in the PAYLOAD and the fallback default is a DISTINCT
# value (#954 follow-up): with the sentinel as the default, an interpreter
# that fails (exit 1, no output -> hook_json_get's `|| printf default` or its
# missing-interpreter branch) printed the sentinel and looked usable. Now only
# a real parse of a real payload can produce it — a failing interpreter yields
# 'hook-json-bad', a garbage one its own output, both != sentinel.
hook_json_usable() {
  [ "$(hook_json_get '{"__hook_json_probe__": "hook-json-ok"}' \
        '__hook_json_probe__' 'hook-json-bad')" = "hook-json-ok" ]
}

# hook_known_tool_name <tool_name>
# Returns 0 when <tool_name> is a tool name the framework's hook contract
# knows, 1 for anything else (including the empty string). Single source of
# truth for the two fail-closed guards (orchestrator-guard-impl.sh,
# repo-containment-impl.sh): both used to let a tool_name they did not
# recognize fall through `case "$TOOL_NAME" in Write|Edit|Bash) ;; *) exit 0`
# — i.e. an unknown value (a broken interpreter's junk before issue #954, a
# non-string or misspelled field today) silently ALLOWED the call (review
# finding M2). Both now call this helper and block on a non-zero result.
#
# Why a closed set: a tool name this hook was never taught about cannot be
# classified — it may be a write-capable tool (NotebookEdit, a provider's
# own file tool) or junk. Silence is not evidence of harmlessness, so the
# unknown case fails closed. What is deliberately allowed:
#   * Claude Code's built-in tool set — the `claude-code-json` contract these
#     hooks are written against (Write/Edit/Bash are the intercepted ones;
#     every other name is a pass-through tool in both guards),
#   * Claude Code's MCP namespace `mcp__<server>__<tool>`: open-ended by
#     design and never classified as a write tool by either guard, so
#     blocking it would break every MCP call without protecting anything.
# Raw provider-native tool names (Antigravity's `write_to_file`,
# `run_command`, ...) are deliberately NOT listed: hooks only ever see the
# normalized Claude names because antigravity-json-adapter.sh translates
# them, and accepting a raw name would let it slip past the Write/Bash
# interception as an "unknown but allowed" tool.
# `EnterWorktree`/`ExitWorktree` are deliberately NOT listed either: both
# create directories, which rules/1-generic/no-worktree-isolation.md forbids,
# so their calls must keep failing closed here.
# Maintenance: a new built-in tool (or provider surface) must be added here;
# until then its calls block with a message naming this function. That is the
# intended fail-closed direction, not an accident.
hook_known_tool_name() {
  case "$1" in
    # Claude Code's open-ended MCP namespace (mcp__server__tool).
    mcp__?*__?*) return 0 ;;
    # Claude Code built-ins. Write/Edit/Bash are intercepted by both guards;
    # the others pass through untouched, but must still be identifiable.
    # Agent is the delegation tool (it replaced Task, which stays listed for
    # older harnesses); SendMessage is the Tier-A progress push.
    Agent|Bash|BashOutput|Edit|ExitPlanMode|Glob|Grep|KillBash|KillShell|LS) return 0 ;;
    ListMcpResources|MultiEdit|NotebookEdit|NotebookRead|Read|ReadMcpResource) return 0 ;;
    SendMessage|Skill|SlashCommand|Task|TaskOutput|TaskStop|TodoWrite|WebFetch|WebSearch) return 0 ;;
    Write|AskUserQuestion) return 0 ;;
  esac
  return 1
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

# --- Release-gate enabled/disabled check ---------------------------------

# hook_gate_check_enabled <gate_name>
# Prints "[SKIP] <gate_name>: gate disabled (release-gates.<gate_name>.enabled=false)"
# and returns 1 when the gate is disabled; returns 0 (silent) when enabled.
# Caller does `hook_gate_check_enabled "$GATE_NAME" || exit 0`.
#
# Baked at sync-time by scripts/lib/hooks.py::sync_release_gates() from
# dod.resolve_release_gates() (project.yaml `release-gates.<gate_name>.enabled`
# > dod-preset default > the gate script's own `enabled_by_default` header).
# The `:=` form only assigns when PRE_RELEASE_GATE_ENABLED is still unset, so
# an explicit `PRE_RELEASE_GATE_ENABLED=false bash release-gates/<gate>.sh`
# always wins for a one-off, single-gate override.
#
# Replaces the identical block that used to be copy-pasted across every
# release-gates/*.sh script.
hook_gate_check_enabled() {
  local gate_name="$1"
  : "${PRE_RELEASE_GATE_ENABLED:=false}"
  if [ "$PRE_RELEASE_GATE_ENABLED" != "true" ]; then
    echo "[SKIP] $gate_name: gate disabled (release-gates.$gate_name.enabled=false)"
    return 1
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

# --- Project-root walk-up helpers (issue #943 (l)) -----------------------

# hook_is_meta_submodule_dir <path>
# Returns 0 when <path> looks like a nested agent-meta checkout: its basename
# is `.agent-meta`, or it is `external/agent-meta`. Such a checkout carries its
# own `.meta-config/`, so a naive walk-up from a payload `cwd` inside it found
# the submodule as the project root instead of the enclosing project that owns
# the session (issue #943 (l), non-Claude providers without
# $CLAUDE_PROJECT_DIR). Both fail-closed guards skip these candidates while
# walking upward but keep the first one as a fallback: a session opened ONLY
# inside the submodule (no enclosing `.meta-config/`) still resolves to it.
hook_is_meta_submodule_dir() {
  local path="${1:-}" base parent
  base="$(basename -- "$path" 2>/dev/null)"
  case "$base" in
    .agent-meta) return 0 ;;
    agent-meta)
      parent="$(basename -- "$(dirname -- "$path" 2>/dev/null)" 2>/dev/null)"
      [ "$parent" = "external" ] && return 0
      ;;
  esac
  return 1
}

# --- Shell statement scanning (issues #943 / #944) -----------------------

# hook_shell_scan_py
# Emits the Python implementation of the shared shell scanner. One definition
# keeps the two fail-closed guards from drifting (they used to embed their own
# splitter each, #943 (j) / #944 SR-B-16):
#
# split_shell_statements(command) -> [(statement, [heredoc_body, ...]), ...]
# split_shell_statements_and_clean(command) -> (statements, code):
#   the same scan also returns the original code with heredoc BODY lines
#   removed (opening line and terminator kept, operators preserved), for the
#   fork-bomb scanner -- a bomb in a heredoc is prose, but ':(){ :|:& };:' must
#   stay one line for the scanner.
#   * splits on && || ; | & and newlines, but only OUTSIDE '...', "...",
#     $'...' (ANSI-C), $"..." (locale), $(...) and backticks;
#   * a backslash escapes the next character and backslash-newline joins the
#     lines (issue #943 (c): the old split-on-'\n' broke 'git push \\\n
#     --force' into two statements, so the force flag was never seen);
#   * $'...' is ANSI-C quoting: inside it a backslash escapes the next
#     character, so \' does NOT close the string (review finding F1 -- before
#     the fix 'echo $'it\'s'; git push --force' never closed the quote and the
#     rest of the command was swallowed);
#   * a '#' at word start starts a comment, so a commented-out command (or the
#     '#agent-meta:agent=...' sentinel line) is not classified as code. The
#     comment is cut from BOTH the statement stream and the cleaned code, so
#     a trailing '# :(){ :|:& };:' never reaches the fork-bomb scan either
#     (review finding F4);
#   * heredoc bodies (<<WORD, <<-WORD, quoted WORD) are removed from the
#     command stream and attached to the statement that opened them, so prose
#     such as a markdown blockquote '> /etc/x' cannot fake a write target,
#     while a real command AFTER the terminator is still returned as its own
#     statement (#944 SR-B-16);
#   * a heredoc delimiter word containing '$' or a backtick is NOT tracked:
#     its body stays in the command stream. Deliberate divergence from bash --
#     bash does not expand the delimiter (verified: '<<$X' wants the literal
#     '$X'), but a delimiter the hook cannot resolve is treated as
#     unclassifiable rather than as license to skip an unknown amount of
#     input, so the body is over-scanned (fail closed, review finding F2).
#   * this is a splitter, not a shell parser: command-substitution contents
#     stay opaque and the hook never executes anything (documented gap #592).
#
# strip_quoted(command) removes quoted spans (fork-bomb false positives from a
# quoted string argument, issues #602/#809).
#
# is_fork_bomb(command) is linear in the input length: the old
# '([A-Za-z_:][A-Za-z0-9_:]*)\s*\(\s*\)\s*\{([^}]*)\}' rescanned the rest of a
# long identifier chain from every position (quadratic; 20 KB ~ 5 s, so the
# hook timeout disabled the gate -- a fail-open, issue #943 (a)).
#   * the function name is scanned exactly, at any length: a backward scan
#     starts only at a '(' followed by ')', and the identifier in front of it
#     ends at that '(', so the scans of two '()' pairs never overlap (O(n)
#     overall). The former 64-character cap skipped longer names, a second
#     fail-open (issue #943);
#   * the body ends at the DEPTH-MATCHING '}' (brace nesting counted, so
#     '{ ...; }' and '${...}' before the self-call do not cut the body short),
#     and is detected even when such a brace precedes the self-call (#1050);
#   * the body search is bounded at 512 characters: a body that exhausts that
#     window without a depth-matching '}' FAILS CLOSED (block instead of
#     allow). A long inline function body without closing braces in it is
#     thereby blocked -- the accepted false-alarm class (spec RK-1).
# No exception is swallowed: a failure propagates as a non-zero hook exit
# (which the guards treat as a block) instead of silently returning False.
hook_shell_scan_py() {
  cat <<'PY'
_IDENT_CHARS = frozenset(
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_:'
)
_WS = ' \t'
_MAX_FUNC_BODY = 512


def split_shell_statements_and_clean(command):
    """Return (statements, code_without_heredoc_bodies).

    The second value keeps the original operators/quotes but drops heredoc
    body lines and trailing comments (the same comment rule the statement
    stream uses -- review finding F4), so a fork-bomb-shaped STRING in a
    heredoc or a comment is not misclassified while ':(){ :|:& };:' (split
    into statements by the operators) is still seen as one line by the
    fork-bomb scanner.
    """
    statements = []
    bodies = []
    pending = []  # (delimiter, strip_leading_tabs, statement_index)
    kept_lines = []
    buf = []
    quote = None
    subst = 0
    backtick = False
    word_start = True
    lines = command.split('\n')
    li = 0

    def flush():
        text = ''.join(buf).strip()
        del buf[:]
        if text:
            statements.append(text)
            bodies.append([])

    while li < len(lines):
        line = lines[li]
        li += 1
        i = 0
        continued = False
        # Index where a trailing comment starts (len(line) = no comment). The
        # cleaned code keeps only line[:comment_at], matching the statement
        # stream, which drops the comment text as well (review finding F4).
        comment_at = len(line)
        while i < len(line):
            c = line[i]
            if quote == "'":
                buf.append(c)
                i += 1
                if c == "'":
                    quote = None
                continue
            if quote == 'ansi':
                # $'...' (ANSI-C quoting): a backslash escapes the next
                # character, so \' does not terminate the string (review
                # finding F1). This is the one shell mode whose escaping
                # differs from a plain single-quoted string.
                if c == '\\':
                    if i + 1 < len(line):
                        buf.append(line[i:i + 2])
                        i += 2
                    else:
                        continued = True
                        i += 1
                    continue
                buf.append(c)
                i += 1
                if c == "'":
                    quote = None
                continue
            if quote == '"' or quote == 'locale':
                # Plain double quotes and $"..." (locale translation) share
                # the same delimiter rules. The scanner treats a backslash as
                # escaping ANY next character (bash only special-cases $, `,
                # ", \ and newline) -- a superset that keeps the closing quote
                # correct without changing where the region ends.
                if c == '\\':
                    if i + 1 < len(line):
                        buf.append(line[i:i + 2])
                        i += 2
                    else:
                        continued = True
                        i += 1
                    continue
                buf.append(c)
                i += 1
                if c == '"':
                    quote = None
                continue
            # unquoted context
            if c == '\\':
                if i + 1 < len(line):
                    buf.append(line[i:i + 2])
                    i += 2
                else:
                    continued = True
                    i += 1
                word_start = False
                continue
            if backtick:
                buf.append(c)
                i += 1
                if c == '`':
                    backtick = False
                continue
            if c == '`':
                backtick = True
                buf.append(c)
                i += 1
                word_start = False
                continue
            if c == '$' and i + 1 < len(line) and line[i + 1] == '(':
                subst += 1
                buf.append('$(')
                i += 2
                word_start = False
                continue
            if c == '$' and i + 1 < len(line) and line[i + 1] in ("'", '"'):
                # $'...' / $"...": the '$' prefixes the quoting mode instead
                # of being ordinary text. Without this the single quote inside
                # $'it\'s' was read as a plain quote and closed on the \' .
                quote = 'ansi' if line[i + 1] == "'" else 'locale'
                buf.append(line[i:i + 2])
                i += 2
                word_start = False
                continue
            if subst > 0:
                if c == '(':
                    subst += 1
                elif c == ')':
                    subst -= 1
                buf.append(c)
                i += 1
                word_start = False
                continue
            if c == "'" or c == '"':
                quote = c
                buf.append(c)
                i += 1
                word_start = False
                continue
            if c == '#' and word_start:
                comment_at = i  # comment runs to end of line
                i = len(line)
                break
            if c in _WS:
                buf.append(c)
                i += 1
                word_start = True
                continue
            if c in (';', '|', '&'):
                if line[i:i + 2] in ('&&', '||'):
                    i += 2
                else:
                    i += 1
                flush()
                word_start = True
                continue
            if c == '<' and i + 1 < len(line) and line[i + 1] == '<':
                j = i + 2
                strip_tabs = False
                if j < len(line) and line[j] == '-':
                    strip_tabs = True
                    j += 1
                while j < len(line) and line[j] in _WS:
                    j += 1
                delim = ''
                if j < len(line) and line[j] in ("'", '"'):
                    q = line[j]
                    j += 1
                    start = j
                    while j < len(line) and line[j] != q:
                        j += 1
                    delim = line[start:j]
                    if j < len(line):
                        j += 1
                else:
                    if j < len(line) and line[j] == '\\':
                        j += 1  # <<\EOF: the backslash escapes the delimiter
                    start = j
                    while j < len(line) and line[j] not in ' \t;&|<>()':
                        j += 1
                    delim = line[start:j]
                if delim and '$' not in delim and '`' not in delim:
                    pending.append((delim, strip_tabs, len(statements)))
                buf.append(line[i:j])
                i = j
                word_start = False
                continue
            buf.append(c)
            i += 1
            word_start = False

        # Keep only the code part of the physical line (a trailing comment is
        # NOT code). This is appended before heredoc bodies are consumed below,
        # so an opening line is kept while its body is dropped.
        kept_lines.append(line[:comment_at])
        # End of physical line. A still-open quote / substitution / backtick
        # keeps accumulating (a newline inside it is literal); a trailing
        # backslash joins the NEXT line without inserting a newline.
        if quote is not None or subst > 0 or backtick:
            buf.append('\n')
            continue
        if continued:
            continue
        flush()
        for delim, strip_tabs, idx in pending:
            body_lines = []
            while li < len(lines):
                raw = lines[li]
                li += 1
                check = raw.lstrip('\t') if strip_tabs else raw
                if check.rstrip('\r').rstrip() == delim:
                    kept_lines.append(raw)  # keep the terminator, drop the body
                    break
                body_lines.append(raw)
            if idx < len(bodies):
                bodies[idx].append('\n'.join(body_lines))
        pending = []
        word_start = True

    if quote is not None or subst > 0 or backtick:
        buf.append('\n')
    flush()
    return list(zip(statements, bodies)), '\n'.join(kept_lines)


def split_shell_statements(command):
    return split_shell_statements_and_clean(command)[0]


def strip_quoted(command):
    # Remove single/double-quoted spans so a fork-bomb-looking STRING literal
    # (e.g. an echo argument) is not misclassified (#602/#809). Best-effort:
    # backslash-escaped quotes are honoured, no full shell parse.
    out = []
    quote = None
    i = 0
    n = len(command)
    while i < n:
        c = command[i]
        if quote is not None:
            if c == '\\' and quote == '"' and i + 1 < n:
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c == '"' or c == "'":
            quote = c
            i += 1
            continue
        if c == '\\' and i + 1 < n:
            out.append(command[i:i + 2])
            i += 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def _body_calls_itself_piped(body, name):
    start = 0
    ln = len(body)
    nl = len(name)
    while True:
        k = body.find(name, start)
        if k < 0:
            return False
        start = k + 1
        if k > 0 and (body[k - 1].isalnum() or body[k - 1] in '_:'):
            continue
        j = k + nl
        while j < ln and body[j] in _WS:
            j += 1
        if j >= ln or body[j] != '|':
            continue
        j += 1
        while j < ln and body[j] in _WS:
            j += 1
        if body.startswith(name, j):
            end = j + nl
            if end >= ln or not (body[end].isalnum() or body[end] in '_:'):
                return True


def is_fork_bomb(command):
    # Linear scan for a function definition whose body pipes the function into
    # itself (':(){ :|:& };:' / 'bomb(){ bomb|bomb& }' / 'bomb ( ) { ... }').
    n = len(command)
    i = 0
    while True:
        p = command.find('(', i)
        if p < 0:
            return False
        i = p + 1
        q = p + 1
        while q < n and command[q] in _WS:
            q += 1
        if q >= n or command[q] != ')':
            continue
        e = p
        while e > 0 and command[e - 1] in _WS:
            e -= 1
        s = e
        while s > 0 and command[s - 1] in _IDENT_CHARS:
            s -= 1
        name = command[s:e]
        if not name:
            continue
        if not (name[0].isalpha() or name[0] in '_:'):
            continue
        j = q + 1
        while j < n and command[j] in _WS:
            j += 1
        if j >= n or command[j] != '{':
            continue
        # End the body at the DEPTH-MATCHING '}' inside the window: count the
        # braces (so '{ ...; }' and '${...}' before the self-call do not cut
        # the body short). One forward pass over at most _MAX_FUNC_BODY
        # characters per candidate keeps the scan linear (#1050).
        close = -1
        depth = 1
        end = j + 1 + _MAX_FUNC_BODY
        if end > n:
            end = n
        k = j + 1
        while k < end:
            c = command[k]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    close = k
                    break
            k += 1
        if close < 0:
            # No depth-matching '}' in the first _MAX_FUNC_BODY characters: the
            # body cannot be inspected, so fail closed (block) instead of
            # skipping the header -- a skip is an allow (issue #943).
            return True
        body = command[j + 1:close]
        if name in body and _body_calls_itself_piped(body, name):
            return True
        i = j + 1
    return False
PY
}

# hook_shell_resolver_py
# Emits the Python command-word resolver used by the fail-closed guards to
# find the command a statement really runs, after keywords, grouping, `case`
# arm syntax, inline function-definition prefixes and command wrappers.
#
# command_start(toks) -> int
#   Index of the real command word in ONE statement's tokens (as returned by
#   split_shell_statements), or len(toks) when the statement runs no command.
#   Tokenisation stays with the caller, because the two guards want different
#   punctuation sets: this resolver only reads the token list. The calling
#   code must import `os` and `re` (the emitted text does not, matching
#   hook_shell_scan_py).
#   * a lone '--' at command position is transparent: end-of-options markers
#     can follow a wrapper's option parser, its positional prefix
#     (DURATION/FILE/ROOT) or stand directly before the command word, and the
#     wrapped command is what runs in every case. Without this,
#     `timeout 5 -- touch /outside` resolved to no command at all and the
#     containment detector silently allowed the write (review finding
#     F-NEW-1 / containment wrapper blind spot);
#   * `in` (a bash reserved word) and the open/close grouping tokens are
#     skipped, so a `case WORD in PATTERN) COMMAND` arm split across
#     statements is still classified, as is the one-line form;
#   * a bare word directly followed by a ')' run is a case-pattern prefix;
#     the run may be several characters wide for an extglob (`@(a|b))`);
#   * `NAME() { … }` and `function NAME { … }` prefixes are skipped so the
#     body's first command is found;
#   * WRAPPERS carries the grammar, not guesswork: each entry maps a wrapper
#     to (options that consume a value, count of leading positional arguments
#     before the wrapped command). 'timeout DURATION', 'flock FILE' and
#     'chroot NEWROOT' each own exactly one.
#
# Adoption note: orchestrator-guard-impl.sh still carries its own inline copy
# of WRAPPERS/command_start (it was extracted here when repo-containment
# needed the same walk). Switching the guard over is a mechanical but wide
# diff in a 64 KB security-sensitive hook (drop the inline table/helpers,
# prepend this emitter), and it must re-run the guard's 400+ test suite plus
# the hook-drift/AC-01 baselines; it is deliberately left for a follow-up so
# this change stays inside the containment fix. Until then this emitter is
# the single definition new code should call, and the guard's inline copy is
# the one duplicate left -- NOT replaced by a third copy inside the
# containment hook.
hook_shell_resolver_py() {
  cat <<'PY'
# Shell keywords / grouping tokens that may precede the real command word.
# `in` is a bash reserved word, never a command: it is the separator a `case`
# list carries when the splitter cuts `case WORD` and `in PATTERN)` onto
# different statements.
LEADING_KEYWORDS = {
    '!', '(', ')', '{', '}', 'if', 'then', 'else', 'elif', 'while', 'until',
    'do', 'done', 'fi', 'esac', 'in',
}
# Command wrappers whose option-before-command form must not hide the real
# command word. Maps a wrapper to (its short/long options that consume a
# value token, its count of leading non-option arguments before the wrapped
# command word).
WRAPPERS = {
    'sudo': ({'-u', '-g', '-p', '-C', '-T', '-r', '-t', '--user', '--group',
              '--prompt', '--chdir'}, 0),
    'doas': ({'-u', '-C'}, 0),
    'env': ({'-u', '--unset', '-C', '--chdir', '-S', '--split-string'}, 0),
    'command': (set(), 0),
    'builtin': (set(), 0),
    'nohup': (set(), 0),
    'exec': ({'-a'}, 0),
    'time': ({'-f', '-o', '--format', '--output'}, 0),
    'nice': ({'-n', '--adjustment'}, 0),
    'ionice': ({'-c', '-n', '-p', '-P', '-u', '--class', '--classdata',
                '--pid', '--pgid', '--uid'}, 0),
    'stdbuf': ({'-i', '-o', '-e', '--input', '--output', '--error'}, 0),
    'xargs': ({'-I', '-n', '-P', '-d', '-L', '-s', '-a', '-E', '-e'}, 0),
    'timeout': ({'-s', '--signal', '-k', '--kill-after'}, 1),
    'flock': ({'-w', '--timeout', '-E', '--conflict-exit-code'}, 1),
    # setsid has NO option that consumes a value (-c/-f/-w are all flags);
    # listing them as value-taking would swallow the wrapped command word.
    'setsid': (set(), 0),
    'watch': ({'-n', '--interval', '-q', '--equexit'}, 0),
    'strace': ({'-o', '--output', '-p', '--attach', '-e', '--trace',
                '-s', '--string-limit', '-u', '--user', '-a', '--columns',
                '-b', '-I', '-O', '-S', '-X', '-E', '-P'}, 0),
    'chroot': ({'-u', '--userspec', '-g', '--groups'}, 1),
    'busybox': (set(), 0),
}


def _empty_parens(toks, i):
    # shlex with punctuation_chars groups ADJACENT punctuation as one token,
    # so 'f()' yields the pair '()' while '( git' yields '('.
    if i < len(toks) and toks[i] == '()':
        return 1
    if i + 1 < len(toks) and toks[i] == '(' and toks[i + 1] == ')':
        return 2
    return 0


def _close_paren_run(tok):
    # A case-pattern terminator. shlex groups ADJACENT punctuation into one
    # token, so the ')' closing a pattern can arrive as ')' or -- for an
    # extglob pattern such as `@(a|b))` -- as '))'.
    return bool(tok) and tok.strip(')') == ''


def command_start(toks):
    i, n = 0, len(toks)
    while i < n:
        t = toks[i]
        base = os.path.basename(t)
        if t == '--':
            i += 1
            continue
        if t in LEADING_KEYWORDS:
            i += 1
            continue
        if t and t.strip('()') == '':
            i += 1
            continue
        if re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', t):
            i += 1
            continue
        if t == 'case':
            i += 1
            if i < n:                      # the case subject word
                i += 1
            if i < n and toks[i] == 'in':
                i += 1
            while i < n and not _close_paren_run(toks[i]):
                i += 1
            if i < n:
                i += 1                     # the pattern's closing ')' run
            continue
        # A later case arm arrives as its own statement
        # ('PATTERN) command'); a bare word directly followed by a ')' run
        # is never a command outside `case`.
        if i + 1 < n and _close_paren_run(toks[i + 1]):
            i += 2
            continue
        parens = _empty_parens(toks, i + 1)
        if parens and re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', t):
            i += 1 + parens
            if i < n and toks[i] == '{':
                i += 1
            continue
        if t == 'function':
            i += 1
            if i < n:                      # the function name
                i += 1
            i += _empty_parens(toks, i)
            if i < n and toks[i] == '{':
                i += 1
            continue
        if base in WRAPPERS:
            value_opts, skip_args = WRAPPERS[base]
            i += 1
            while i < n:
                opt = toks[i]
                if opt == '--':
                    i += 1
                    break
                if opt.startswith('--'):
                    name = opt.split('=', 1)[0]
                    has_value = '=' in opt
                    i += 1
                    if not has_value and name in value_opts and i < n:
                        i += 1
                    continue
                if opt.startswith('-') and opt != '-':
                    i += 1
                    if opt in value_opts and i < n:
                        i += 1
                    continue
                break
            # Skip the wrapper's own positional prefix (DURATION, FILE, ROOT).
            while skip_args > 0 and i < n:
                i += 1
                skip_args -= 1
            continue
        break
    return i
PY
}

# --- Branch-Guard push helpers (issues #949 / #1033) ---------------------

# hook_protected_branches [main_branch]
# Prints the Branch-Guard's protected-branch set as a space-separated,
# de-duplicated list: main + master + the configured main branch, with the
# configured branch first when it is neither main nor master (the order the
# block message in dod-push-check.sh has always used, #1033). Git ref names
# cannot contain whitespace, so a space-separated list is unambiguous.
# Single source of truth for both the classifier's PROTECTED set and the
# block message, which used to be built separately (#949).
hook_protected_branches() {
  local main="${1:-main}"
  case "$main" in
    main|master) printf '%s' "main master" ;;
    *) printf '%s' "$main main master" ;;
  esac
}

# hook_push_arg_parser_py
# Emits the Python implementation of the git-push argument walk as source
# text. dod-push-check.sh concatenates it with its classifier and pipes
# both to python3: its tag-only detection and its destination check used to
# carry a ~25-line copy of this walk each (issue #949), so a fix in one
# could miss the other. Keeping one implementation in this lib (D6) makes
# them share the exact same positionals.
#
# walk_push_args(args, opts_with_value) -> (pos, opts)
#   pos  — positionals in order, after the first '--' everything is one
#   opts — (name, value, raw) in order; a value of None means the spelling
#          carried no value ('='-form or a plain flag), "" means an empty
#          one. '-o' (short) and every name in opts_with_value consume the
#          next token when they have no attached value — that rule must not
#          be re-implemented by a caller (it is how '-o --tags' keeps
#          '--tags' as the option's value instead of a tag flag).
# The walk only splits option syntax; deciding whether an option is
# allowed/known/unknown stays with the callers (tag-only allowlist vs.
# destination check), which is why both keep their own policy tables.
hook_push_arg_parser_py() {
  cat <<'PY'
def walk_push_args(args, opts_with_value):
    pos, opts = [], []
    i = 0
    while i < len(args):
        a = args[i]
        i += 1
        if a == "--":
            pos += args[i:]
            break
        if not a.startswith("-") or a == "-":
            pos.append(a)
            continue
        if a.startswith("--"):
            name, eq, val = a.partition("=")
            if eq:
                opts.append((name, val, a))
            elif name in opts_with_value:
                opts.append((name, args[i] if i < len(args) else "", a))
                i += 1
            else:
                opts.append((name, None, a))
            continue
        # short cluster: one option per character; 'o' takes the rest of
        # the cluster ('-o<val>') or the next token ('-o <val>') as value
        rest = a[1:]
        for k, ch in enumerate(rest):
            if ch == "o":
                if k + 1 < len(rest):
                    opts.append(("-o", rest[k + 1:], a))
                else:
                    opts.append(("-o", args[i] if i < len(args) else "", a))
                    i += 1
                break
            opts.append(("-" + ch, None, a))
    return pos, opts
PY
}
