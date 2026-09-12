#!/bin/bash
# version: 1.0.0
# Real repo-containment ("prison mode") logic. NOT a standalone hook —
# invoked by repo-containment.sh (thin self-health wrapper, issue #630), which
# pipes the PreToolUse JSON payload to this script's stdin after syntax-
# checking it. Do not register this file directly in settings.json (it has no
# `# hook:`/`# event:` header on purpose, so scripts/lib/hooks.py never
# registers it as its own hook entry).
# The `# version:` line above IS still read by check_stale_deployed_hooks()
# (scripts/lib/consistency/hook_drift.py, issue #630) so a project that
# doesn't re-sync after this file changes gets a drift warning — bump it
# whenever this file's logic changes, independent of the wrapper's version.
#
# What this hook does (spec docs/concepts/repo-containment-prison-mode.md §4.1):
#   * Write/Edit  -> resolve tool_input.file_path and allow it only when it is
#                    inside the repo root. <repo root>/<tmp-sink.path> is a
#                    special carve-out: allowed when the sink is enabled,
#                    blocked when it is disabled (spec §7: ".tmp mit aktivem
#                    Sink -> 0; .tmp ohne Sink -> 2"), even though it sits
#                    inside the root.
#   * Bash        -> best-effort tokenized detection of write-ish commands /
#                    redirections; block obvious writes outside the allowed
#                    roots, allow reads.
#   * All other tools (Read/Glob/Grep/...) exit 0 untouched.
#
# Config & precedence: the master switch and tmp-sink settings live in
# .meta-config/project.yaml. Precedence mirrors scripts/lib/repo_containment.py
# §2.3 exactly:
#     provider-override > project repo_containment.enabled > default true
# We deliberately do NOT import scripts/lib/repo_containment.py at runtime:
# that module is an agent-meta-internal, sync-time library and is NOT deployed
# into target projects together with the hooks (only hooks/ is), so importing
# it would fail in exactly the projects this guard protects. Instead we reuse
# the SAME config-reading mechanism as orchestrator-guard-impl.sh (python3 +
# yaml.safe_load on .meta-config/project.yaml, passing the path as argv so
# backslash-bearing Windows paths are never string-interpolated) and mirror
# the resolver's precedence and safe-side rules inline. The tmp-sink path is
# re-validated (relative, non-empty, no drive-letter prefix, no '..' segments,
# not the repo root itself) before it widens the allow-list.
#
# Provider identity: `AGENT_META_PROVIDER` is substituted per provider by
# sync.py's per-provider copy step (scripts/lib/hooks.py:470,
# `source_content.replace("Gemini", provider)`), exactly like
# orchestrator-guard-impl.sh. That is the one reliable provider signal
# available to a hook at runtime (the PreToolUse payload carries no provider
# field and no documented provider env var exists), so we use it. When the
# file is run straight from source (never synced) the placeholder is left
# literal — it is then treated as "no provider", so precedence falls back to
# the project value > default. No `if provider == "Name"` branch exists here:
# the override lookup is a plain dict keyed by the provided name.
#
# Fail-mode (issue #630): the wrapper owns the missing-/broken-impl handling.
# This impl itself fails CLOSED on a missing helper lib, a missing python
# interpreter (issue #595 posture) and on an empty/malformed payload.
#
# Safe-side (F4): a missing, unreadable or unparseable config resolves to
# ENABLED, and a present-but-non-boolean `enabled` also resolves to ENABLED —
# the hook never silently opens on doubt. The sync-time validator
# (scripts/lib/config.py::_validate_repo_containment) hard-exits on a
# non-boolean value; the runtime safe-side rule below does not contradict
# that, it only prevents the hook from opening in the meantime.
#
# Coexistence: this hook is independent of orchestrator-guard.sh — same
# PreToolUse event, separate concern (containment vs. delegation/git gates).
# Both run; neither reads the other's state. Unlike orchestrator-guard, this
# hook imposes no role/sentinel logic.
#
# Best-effort boundary (issue #592, deliberate): the Bash path is a
# convention boundary, NOT a security boundary — see
# .claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-
# security-boundary. Command substitution, indirection (`eval`, `xargs`,
# `$()`), interpreters (`python -c "open(...,'w')"`), and many tools not in
# the small write-command set below can still smuggle a write outside the
# root, because the hook neither executes nor fully parses the shell. Closing
# that would need a real shell interpreter, which is disproportionate here.
#
# Exit codes: 0 = allow, 2 = block. As with orchestrator-guard (issue #396)
# every block reason is written to stderr — the harness feeds stderr back to
# the model and ignores stdout on exit 2.

set -uo pipefail

# --- Shared helper lib + fail-closed python check (issue #595) ---------
# Missing lib/hook_common.sh (deployment bug) or a missing python interpreter
# (PATH manipulation) must not silently allow writes through: both fail
# CLOSED. Same posture as orchestrator-guard.sh.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! source "$SCRIPT_DIR/lib/hook_common.sh" 2>/dev/null; then
  echo "REPO_CONTAINMENT: required helper $SCRIPT_DIR/lib/hook_common.sh is missing or unreadable." >&2
  echo "Failing closed (issue #595) — re-run sync.py to redeploy the hooks/lib/ directory." >&2
  exit 2
fi

if ! hook_have_python; then
  echo "REPO_CONTAINMENT: no python/python3 interpreter found on PATH." >&2
  echo "Failing closed (issue #595) — this guard cannot evaluate write targets without one." >&2
  echo "Install python3 or restore PATH to unblock this guard." >&2
  exit 2
fi
_PY="$(hook_python_bin)"

INPUT=$(cat)

TOOL_NAME=$(hook_json_get "$INPUT" "tool_name")

# Empty/malformed payload -> fail CLOSED. This intentionally differs from
# orchestrator-guard-impl, which exits 0 when tool_name is empty (it treats
# that as a non-tool event). A containment guard cannot tell a benign
# non-tool event from a truncated payload, so it takes the safe side (F4):
# an unevaluable payload must never open the jail.
if [ -z "$TOOL_NAME" ]; then
  echo "REPO_CONTAINMENT: empty or unparseable PreToolUse payload (no tool_name)." >&2
  echo "Failing closed so an unknown tool call cannot write outside the repo root." >&2
  exit 2
fi

# Only write-capable tools are intercepted; reads (Read/Glob/Grep) and every
# other tool pass through untouched.
case "$TOOL_NAME" in
  Write|Edit|Bash) ;;
  *) exit 0 ;;
esac

# --- Provider identity -------------------------------------------------
# Baked per provider at sync time (scripts/lib/hooks.py:470). Stays the
# literal placeholder only when this file was never synced (run straight from
# hooks/1-generic/), which is treated as "no provider override applies".
AGENT_META_PROVIDER="Gemini"
PROVIDER=""
case "$AGENT_META_PROVIDER" in
  ''|*'{{'*) PROVIDER="" ;;
  *) PROVIDER="$AGENT_META_PROVIDER" ;;
esac

# --- Workdir + repo root ----------------------------------------------
# The payload `cwd` is the directory the tool call runs in. Repo root is the
# nearest ancestor directory that contains a `.meta-config/` directory — NOT
# the git toplevel (a project may live inside a larger git repo; containment
# must follow the agent-meta project root).
WORKDIR=$(hook_json_get "$INPUT" "cwd")
if [ -z "$WORKDIR" ]; then
  WORKDIR="$PWD"
fi
case "$WORKDIR" in
  /*) ;;
  *) WORKDIR="$PWD/$WORKDIR" ;;
esac

resolve_repo_root() {
  local dir="$1" parent
  while [ -n "$dir" ]; do
    if [ -d "$dir/.meta-config" ]; then
      printf '%s' "$dir"
      return 0
    fi
    [ "$dir" = "/" ] && break
    parent="$(dirname "$dir")"
    [ "$parent" = "$dir" ] && break
    dir="$parent"
  done
  return 1
}

REPO_ROOT="$(resolve_repo_root "$WORKDIR")" || REPO_ROOT=""
if [ -z "$REPO_ROOT" ]; then
  # No .meta-config/ anywhere above the workdir: treat the workdir itself as
  # the root and let the safe-side config defaults apply (containment ON).
  REPO_ROOT="$WORKDIR"
fi
CONFIG_FILE="$REPO_ROOT/.meta-config/project.yaml"

# --- Effective config resolution (mirrors scripts/lib/repo_containment.py) ---
# Prints exactly three KEY=VALUE lines; ALWAYS exits 0. Any failure (file
# missing, PyYAML missing, unparseable YAML) prints the safe-side defaults.
read_effective_containment() {
  "$_PY" - "$1" "$2" <<'PYEOF'
import os
import re
import sys

CONFIG_FILE, PROVIDER = sys.argv[1], sys.argv[2]

# Mirrors scripts/lib/repo_containment.py::tmp_sink_path_error.
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")


def emit(enabled, sink_enabled, sink_path):
    print("ENABLED=%d" % (1 if enabled else 0))
    print("SINK_ENABLED=%d" % (1 if sink_enabled else 0))
    print("SINK_PATH=%s" % sink_path)


try:
    import yaml

    with open(CONFIG_FILE, encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    raw = config.get("repo_containment")
    rc = raw if isinstance(raw, dict) else {}

    # Master switch: provider-override > project value > default True.
    # A present-but-non-boolean value resolves safe-side to True (F4).
    enabled = True
    handled = False
    overrides = rc.get("provider-overrides")
    if isinstance(overrides, dict) and isinstance(PROVIDER, str) and PROVIDER:
        entry = overrides.get(PROVIDER)
        if isinstance(entry, dict) and "enabled" in entry:
            value = entry["enabled"]
            enabled = value if isinstance(value, bool) else True
            handled = True
    if not handled and "enabled" in rc:
        value = rc["enabled"]
        enabled = value if isinstance(value, bool) else True

    # tmp-sink settings (independent of the master switch; framework defaults).
    sink_raw = rc.get("tmp-sink")
    sink = sink_raw if isinstance(sink_raw, dict) else {}
    sink_enabled = sink.get("enabled", True)
    if not isinstance(sink_enabled, bool):
        sink_enabled = True

    path = sink.get("path", ".tmp")
    valid = (
        isinstance(path, str)
        and bool(path.strip())
        and not os.path.isabs(path)
        and not _WINDOWS_DRIVE_RE.match(path)
        and path not in (".", "..")
    )
    if valid:
        segments = path.replace("\\", "/").split("/")
        valid = not any(segment == ".." for segment in segments)
    if valid:
        # A path whose normalized form is the root itself (".", "./.", "") or
        # escapes it is refused, mirroring the sync validator. The commonpath
        # re-check in the hook would otherwise treat the repo root as the sink.
        normalized = os.path.normpath(path)
        valid = normalized not in ("", ".", "..") and not normalized.startswith(
            ".." + os.sep
        )
    if not valid:
        path = ".tmp"

    emit(enabled, sink_enabled, path)
except Exception:
    # F4 safe-side: missing/unreadable/unparseable config never opens silently.
    emit(True, True, ".tmp")
PYEOF
}

CONFIG_OUT="$(read_effective_containment "$CONFIG_FILE" "$PROVIDER")"
ENABLED="1"
SINK_ENABLED="1"
SINK_PATH=".tmp"
while IFS='=' read -r _key _value; do
  case "$_key" in
    ENABLED) ENABLED="$_value" ;;
    SINK_ENABLED) SINK_ENABLED="$_value" ;;
    SINK_PATH) SINK_PATH="$_value" ;;
  esac
done < <(printf '%s\n' "$CONFIG_OUT")

# enabled: false -> no enforcement at all (spec §4.1).
if [ "$ENABLED" != "1" ]; then
  exit 0
fi

# --- Path containment verdict -----------------------------------------
# Prints ALLOW / BLOCK_SINK / BLOCK for the (possibly relative) target.
# Semantics (spec §7 test table): a target inside the repo root is allowed;
# a target inside <repo root>/<tmp-sink.path> is allowed ONLY while the sink
# is enabled — a disabled sink excludes its own subtree even though that
# subtree physically sits inside the root (`.tmp` with sink -> 0, `.tmp`
# without sink -> 2). Everything else is BLOCK.
# Uses os.path.realpath so symlinks pointing outside the root are refused
# too; realpath also normalises a not-yet-existing Write target (equivalent
# to `realpath -m`). On any python error nothing is printed, which the caller
# treats as BLOCK (fail closed).
containment_verdict() {
  "$_PY" - "$REPO_ROOT" "$WORKDIR" "$SINK_ENABLED" "$SINK_PATH" "$1" <<'PYEOF'
import os
import sys

root = os.path.realpath(sys.argv[1])
workdir = os.path.realpath(sys.argv[2])
sink_enabled = sys.argv[3] == "1"
sink_path = sys.argv[4]
raw = sys.argv[5]

if not raw:
    print("BLOCK")
    sys.exit(0)

target = os.path.realpath(raw if os.path.isabs(raw) else os.path.join(workdir, raw))
sink_root = os.path.realpath(os.path.join(root, sink_path))


def within(base):
    try:
        return os.path.commonpath([base, target]) == base
    except ValueError:
        return False


if within(sink_root):
    print("ALLOW" if sink_enabled else "BLOCK_SINK")
    sys.exit(0)

if within(root):
    print("ALLOW")
    sys.exit(0)

print("BLOCK")
PYEOF
}

block_write() {
  local target="$1" reason="${2:-outside}"
  if [ "$reason" = "sink-disabled" ]; then
    echo "REPO_CONTAINMENT: write target is inside the configured but DISABLED tmp-sink (prison mode)." >&2
    echo "  target:    $target" >&2
    echo "  reason:    the tmp-sink ($REPO_ROOT/$SINK_PATH) is writable only when" >&2
    echo "             repo_containment.tmp-sink.enabled: true." >&2
  else
    echo "REPO_CONTAINMENT: write target is outside the repository root (prison mode)." >&2
    echo "  target:    $target" >&2
    echo "  repo root: $REPO_ROOT" >&2
    if [ "$SINK_ENABLED" = "1" ]; then
      echo "  allowed:   paths under $REPO_ROOT and under $REPO_ROOT/$SINK_PATH" >&2
    else
      echo "  allowed:   paths under $REPO_ROOT (the tmp-sink subtree is disabled)" >&2
    fi
  fi
  echo "  Opt-out: set repo_containment.enabled: false in .meta-config/project.yaml." >&2
}

# --- Write/Edit: check the explicit target path ------------------------
if [ "$TOOL_NAME" = "Write" ] || [ "$TOOL_NAME" = "Edit" ]; then
  FILE_PATH=$(hook_json_get "$INPUT" "tool_input.file_path")
  if [ -z "$FILE_PATH" ]; then
    echo "REPO_CONTAINMENT: no tool_input.file_path in the payload for $TOOL_NAME." >&2
    echo "Failing closed — the write target cannot be evaluated." >&2
    exit 2
  fi
  case "$(containment_verdict "$FILE_PATH")" in
    ALLOW) exit 0 ;;
    BLOCK_SINK)
      block_write "$FILE_PATH" "sink-disabled"
      exit 2
      ;;
    *)
      block_write "$FILE_PATH" "outside"
      exit 2
      ;;
  esac
fi

# --- Bash: best-effort tokenized write detection (issue #592) ---------
# The detector below tokenizes with shlex (punctuation-aware) and splits on
# raw shell control operators / newlines, mirroring the inline tokenizer style
# of orchestrator-guard-impl.sh. It reports candidate write targets, one per
# line; each is then run through the same containment_verdict as Write/Edit.
# A missing command (nothing to do) exits 0; a detector internal error yields
# no candidates and therefore no block, which is consistent with this path's
# documented best-effort status (the config-doubt safe-side rule above is
# unaffected).
if [ "$TOOL_NAME" = "Bash" ]; then
  BASH_CMD=$(hook_json_get "$INPUT" "tool_input.command")
  if [ -z "$BASH_CMD" ]; then
    exit 0
  fi

  WRITE_TARGETS=$(printf '%s' "$BASH_CMD" | "$_PY" -c '
import os
import re
import shlex
import sys

command = sys.stdin.read()

# Commands whose operands are created / modified / removed outright.
WRITE_ALL = {
    "touch", "mkdir", "rmdir", "rm", "truncate", "mkfifo", "mknod", "tee",
}
# Commands whose LAST non-flag operand is the destination write target.
WRITE_DEST = {"cp", "install", "rsync", "scp", "ln"}
# In-place editors: only the operands are written when -i/--in-place is set.
INPLACE = {"sed", "perl", "ruby"}
# Wrapper prefixes skipped before the real command name.
WRAPPERS = {"sudo", "env", "command", "nohup", "time", "nice", "ionice", "stdbuf"}


def tokenize(chunk):
    if not chunk.strip():
        return []
    try:
        lex = shlex.shlex(chunk, posix=True, punctuation_chars="();<>|&")
        lex.whitespace_split = True
        lex.commenters = ""
        return list(lex)
    except Exception:
        return chunk.split()


def is_flag(token):
    return token.startswith("-") and token != "-"


def is_dev_target(target):
    return (
        target in ("/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty", "/dev/zero")
        or target.startswith("/dev/fd/")
        or target.startswith("/proc/self/fd/")
    )


def is_skippable(target):
    return (
        not target
        or target == "-"
        or target.startswith("&")
        or target.startswith("$")
        or is_dev_target(target)
    )


targets = []

# Best-effort statement split on shell control operators AND newlines (same
# approach as orchestrator-guard-impl.sh) so a write target is not attributed
# across unrelated commands.
for line in command.split("\n"):
    for chunk in re.split(r"&&|\|\||;|\||&", line):
        tokens = tokenize(chunk)
        if not tokens:
            continue

        # Redirection operators `>`, `>>`, `>|` (and `&>` once the `&` split
        # above has peeled it); the following token is the write target.
        i = 0
        while i < len(tokens):
            if tokens[i] in (">", ">>", ">|"):
                if i + 1 < len(tokens) and not is_skippable(tokens[i + 1]):
                    targets.append(tokens[i + 1])
                i += 2
                continue
            i += 1

        # Locate the command, skipping wrapper prefixes and KEY=VALUE tokens.
        idx = 0
        while idx < len(tokens):
            head = os.path.basename(tokens[idx])
            if head in WRAPPERS or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[idx]):
                idx += 1
                continue
            break
        if idx >= len(tokens):
            continue
        cmd = os.path.basename(tokens[idx])
        args = tokens[idx + 1:]

        if cmd in WRITE_ALL:
            for arg in args:
                if not is_skippable(arg):
                    targets.append(arg)
        elif cmd in WRITE_DEST:
            positionals = [a for a in args if not is_skippable(a)]
            if positionals:
                targets.append(positionals[-1])
        elif cmd == "mv":
            for arg in args:
                if not is_skippable(arg):
                    targets.append(arg)
        elif cmd == "dd":
            for arg in args:
                if arg.startswith("of=") and not is_skippable(arg[3:]):
                    targets.append(arg[3:])
        elif cmd in INPLACE:
            inplace = "--in-place" in args or any(
                a == "-i" or a.startswith("-i.")
                for a in args
            )
            if inplace:
                positionals = [a for a in args if not is_skippable(a)]
                for arg in positionals[1:]:
                    targets.append(arg)

for target in targets:
    print(target)
' 2>/dev/null || true)

  BLOCKED_TARGET=""
  BLOCKED_REASON="outside"
  if [ -n "$WRITE_TARGETS" ]; then
    while IFS= read -r candidate; do
      [ -n "$candidate" ] || continue
      case "$(containment_verdict "$candidate")" in
        ALLOW) ;;
        BLOCK_SINK)
          BLOCKED_TARGET="$candidate"
          BLOCKED_REASON="sink-disabled"
          break
          ;;
        *)
          BLOCKED_TARGET="$candidate"
          BLOCKED_REASON="outside"
          break
          ;;
      esac
    done < <(printf '%s\n' "$WRITE_TARGETS")
  fi

  if [ -n "$BLOCKED_TARGET" ]; then
    block_write "$BLOCKED_TARGET" "$BLOCKED_REASON"
    echo "  (detected in Bash command: $(printf '%s' "$BASH_CMD" | head -c 200))" >&2
    echo "Best-effort tokenized detection (issue #592) — review the command or write inside the repo root." >&2
    exit 2
  fi

  exit 0
fi

exit 0
