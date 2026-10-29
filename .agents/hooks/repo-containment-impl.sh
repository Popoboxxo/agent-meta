#!/bin/bash
# version: 1.5.0
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
# re-validated before it widens the allow-list with the SAME rule set as
# scripts/lib/repo_containment.py::tmp_sink_path_error (IC-15 Nr. 27 a/b, hook
# mirror f; parity enforced by tests/test_tmp_sink_path_parity.py over the
# shared corpus tests/fixtures/tmp-sink-path-corpus.json): relative only (no
# absolute/UNC/drive paths), no '..' segment, no reserved Windows device
# names, no trailing dot/space, ':' or <>"|?* / control characters, no
# protected directory (case-insensitive), not the repo root itself. The
# accepted path is used in its canonical form (backslash -> slash before
# normpath). An invalid path keeps falling back to '.tmp' (never aborts at
# runtime); only the decision and canonical form must match Python. The
# protected provider directories are embedded below (config/ai-providers.yaml
# is not deployed); the parity test fails when they drift from
# provider_root_dirs.
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
# interpreter (issue #595 posture), an interpreter that exits 0 while
# printing garbage, an empty/malformed payload, a missing or unrecognized
# tool_name (v1.3.0, review finding M2), and a crashing write-target detector
# (v1.4.0, #944 verifier note: the detector used to end in `|| true`, so a
# Python crash silently ALLOWED the command). The recognized-name list is
# shared with orchestrator-guard-impl.sh (hook_known_tool_name in
# lib/hook_common.sh): a new built-in tool must be added there, and until
# then its calls block on purpose (fail-closed).
#
# Fixed jail root (v1.4.0, #944 SR-B-18): the repo root prefers an anchor that
# does NOT come from the payload, in this order:
#   1. $CLAUDE_PROJECT_DIR, when it carries `.meta-config/`;
#   2. the deployment layout `<root>/.claude/hooks/` this file lives in, when
#      `<root>` carries `.meta-config/`.
# Before this, a session whose shell was outside the project (or a forged
# payload `cwd`) made the payload directory its own jail root, so a write
# outside the real project was judged "inside". Only when neither fixed anchor
# exists (e.g. the file is run straight from the source tree) does the guard
# fall back to the payload anchor below.
#
# Anchor rule (fail-closed root resolution, spec §Fail-closed-Design):
# the repo root is searched from an explicit ANCHOR — the payload `cwd` when
# present and non-empty, or the directory of an absolute Write/Edit target when
# `cwd` is missing/empty. `$PWD` is NEVER adopted: the guard process' working
# directory says nothing about the project a tool call belongs to. If no
# ancestor of the anchor carries `.meta-config/`, this hook exits 2 with the
# single code `repo-containment.no-root` instead of promoting the anchor to a
# root (that promotion was the fail-open this rule closes). A nested
# agent-meta submodule's own `.meta-config/` is skipped in favour of the
# enclosing project (#943 (l)); it remains the fallback when nothing encloses
# it. A Bash call has no path-shaped target to anchor on (a command may write
# zero, one or many targets), so Bash without `cwd` fails closed with the same
# code.
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
# security-boundary. The Bash detector is a best-effort token scan:
#   * command substitution / backticks / `eval` / `xargs`, interpreters
#     (`python -c "open(...,'w')"`), and tools outside the write-command set
#     below can still smuggle a write outside the root;
#   * statements are split by the shared quote/heredoc-aware splitter
#     (hook_shell_scan_py), so a quoted operator is not a separator and a
#     heredoc body is prose, not commands (#944 SR-B-16). A real command
#     AFTER the heredoc terminator is still scanned;
#   * `perl -pi`, `sed -Ei`/`-ni`-style clusters, `cp -t DIR` and trailing
#     flags are recognised (#944 SR-B-19); other in-place spellings are not;
#   * the command word is resolved by the SHARED resolver
#     (hook_shell_resolver_py, hook_common.sh v1.4.0), the same walk the
#     orchestrator guard uses: wrapper grammar with positional arity
#     (`timeout DURATION`, `flock FILE`, `chroot NEWROOT`), a transparent
#     `--` at command position, one-line and split `case … in` arms, function
#     bodies, subshells/groups, and `if`/`for`/`while` bodies. Before v1.5.0
#     this hook had its own wrapper-name-only skip loop and knew none of
#     these, so `timeout 5 -- touch /outside`, `flock -w 5 /x -- touch
#     /outside`, `chroot /x -- touch /outside`, `case … in …) touch
#     /outside`, `f() { touch /outside; }`, `( touch /outside )` and `if
#     true; then touch /outside; fi` ALL resolved to no write target and were
#     allowed (the wrapper blind spot the guard fixed in v1.9.2).
# Closing the rest would need a real shell interpreter, which is
# disproportionate here.
#
# Known gaps (issue #944 SR-B-20, #943 (m)): the config reader uses
# yaml.safe_load. When PyYAML is unavailable (or the file is unparseable) the
# guard stays ENABLED and now writes a warning to stderr; `enabled: false`
# cannot be honoured in that state, and the warning says so instead of
# ignoring the opt-out silently. Honouring the opt-out without PyYAML needs
# the shared stdlib YAML subset reader (tracked in the plan), not a second
# ad-hoc line scan that could open the jail on a misparse.
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

# The shared helper functions this guard relies on must actually be there:
# a deployed lib/hook_common.sh from before they existed (sync.py not re-run
# after an agent-meta update) would otherwise make the calls below fail
# obscurely. Fail closed, same as a missing lib (issue #595).
if ! declare -F hook_json_usable >/dev/null 2>&1 \
   || ! declare -F hook_known_tool_name >/dev/null 2>&1 \
   || ! declare -F hook_shell_scan_py >/dev/null 2>&1 \
   || ! declare -F hook_shell_resolver_py >/dev/null 2>&1 \
   || ! declare -F hook_is_meta_submodule_dir >/dev/null 2>&1; then
  echo "REPO_CONTAINMENT: $SCRIPT_DIR/lib/hook_common.sh is outdated (shared guard helpers missing)." >&2
  echo "Failing closed — re-run sync.py to redeploy the hooks/lib/ directory." >&2
  exit 2
fi

# Issue #954 / review finding M2: a python3 on PATH that EXITS 0 while
# printing garbage (broken or hostile PATH shim) is indistinguishable from a
# working interpreter by exit status alone. Before this gate it handed junk
# back as tool_name, which matched the `*) exit 0` allow branch below -- a
# fail-open. Verify the interpreter before trusting any field (shared helper,
# not a second copy of the probe).
if ! hook_json_usable; then
  echo "REPO_CONTAINMENT: the python/python3 on PATH does not behave like a Python interpreter." >&2
  echo "Failing closed (M2/#954) — the hook payload cannot be read reliably." >&2
  exit 2
fi

INPUT=$(cat)

TOOL_NAME=$(hook_json_get "$INPUT" "tool_name")

# Empty/malformed payload -> fail CLOSED: a containment guard cannot tell a
# benign non-tool event from a truncated payload, so an unevaluable payload
# must never open the jail. (orchestrator-guard-impl.sh now takes the same
# safe side, review finding M2; before that it exited 0 here.)
if [ -z "$TOOL_NAME" ]; then
  echo "REPO_CONTAINMENT: empty or unparseable PreToolUse payload (no tool_name)." >&2
  echo "Failing closed so an unknown tool call cannot write outside the repo root." >&2
  exit 2
fi

# M2: an unrecognized tool_name used to fall through the `*) exit 0` branch
# below. The known-name allow-list lives in lib/hook_common.sh so both
# security guards share one definition (see hook_known_tool_name there for
# what is allowed and why).
if ! hook_known_tool_name "$TOOL_NAME"; then
  echo "REPO_CONTAINMENT: unknown tool_name '$TOOL_NAME' in the PreToolUse payload." >&2
  echo "Failing closed (M2) — an unrecognized tool could write outside the repo root." >&2
  echo "If it is a legitimate tool, add it to hook_known_tool_name in lib/hook_common.sh." >&2
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

# --- Realpath helper ---------------------------------------------------
# stdlib-only (python is already required above), works for a path that does
# not exist yet, and normalizes symlinks on every platform. Prints "" when the
# interpreter fails, so callers can treat an unnormalizable anchor as missing.
resolve_realpath() {
  "$_PY" -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1" 2>/dev/null
}

# --- Target extraction -------------------------------------------------
# Extracted before the anchor: with a missing/empty `cwd`, an absolute
# Write/Edit target is what the anchor is derived from.
FILE_PATH=$(hook_json_get "$INPUT" "tool_input.file_path")
BASH_CMD=$(hook_json_get "$INPUT" "tool_input.command")

if [ "$TOOL_NAME" = "Write" ] || [ "$TOOL_NAME" = "Edit" ]; then
  if [ -z "$FILE_PATH" ]; then
    echo "REPO_CONTAINMENT: no tool_input.file_path in the payload for $TOOL_NAME." >&2
    echo "Failing closed — the write target cannot be evaluated." >&2
    exit 2
  fi
fi

# A commandless Bash call cannot write anything and needs no anchor.
if [ "$TOOL_NAME" = "Bash" ] && [ -z "$BASH_CMD" ]; then
  exit 0
fi

# --- Fixed jail root (issue #944 SR-B-18) -----------------------------
# Preferred over every payload-derived anchor. 1) the harness-set
# $CLAUDE_PROJECT_DIR when it carries .meta-config/; 2) the deployment layout
# <root>/.claude/hooks/ this script was synced into. Running straight from the
# source tree (agent-meta's hooks/1-generic/) matches neither, so the tests
# and ad-hoc runs keep the documented payload-anchor behaviour below.
#
# Return contract:
#   0  fixed root selected and printed (never empty)
#   1  no fixed root applies -- the payload anchor is the intended fallback
#   2  a fixed root WAS selected but could not be resolved -> fail closed
# A selected-but-unresolvable root must never degrade to the payload anchor
# (review finding F5): that silently lets a payload cwd choose the jail.
resolve_fixed_root() {
  local candidate root
  if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR/.meta-config" ]; then
    root="$(resolve_realpath "$CLAUDE_PROJECT_DIR")"
    if [ -z "$root" ]; then
      return 2
    fi
    printf '%s\n' "$root"
    return 0
  fi
  # Deployment layout, provider-neutral: sync copies the hooks into
  # <provider-root>/hooks (e.g. .claude/hooks, .agents/hooks) or, for a custom
  # layout, <root>/hooks. The source tree is hooks/1-generic/, so its basename
  # is not 'hooks' and this never mistakes agent-meta itself for the jail.
  if [ "$(basename -- "$SCRIPT_DIR" 2>/dev/null)" = "hooks" ]; then
    for candidate in \
      "$(dirname -- "$SCRIPT_DIR")" \
      "$(dirname -- "$(dirname -- "$SCRIPT_DIR")")"; do
      if [ -d "$candidate/.meta-config" ]; then
        root="$(resolve_realpath "$candidate")"
        if [ -z "$root" ]; then
          return 2
        fi
        printf '%s\n' "$root"
        return 0
      fi
    done
  fi
  return 1
}

_FIXED_ROOT_RC=0
FIXED_ROOT="$(resolve_fixed_root)" || _FIXED_ROOT_RC=$?
if [ "$_FIXED_ROOT_RC" -eq 1 ] && [ -z "$FIXED_ROOT" ]; then
  : # no fixed root applies; the payload anchor is the documented fallback
elif [ "$_FIXED_ROOT_RC" -ne 0 ] || [ -z "$FIXED_ROOT" ]; then
  echo "REPO_CONTAINMENT: the fixed jail root (\$CLAUDE_PROJECT_DIR or the deployment layout) could not be resolved." >&2
  echo "Failing closed (review finding F5) — a selected root must never degrade to the payload anchor." >&2
  exit 2
fi

# --- Anchor ------------------------------------------------------------
# Anchor precedence (spec §Fail-closed-Design "Vertrag" point 1):
#   1. payload `cwd` present, non-empty and absolute -> realpath(cwd)
#   2. else target absolute (Write/Edit)             -> realpath(dirname(target))
#   3. else                                          -> no anchor, fail closed
# `$PWD` is never a fallback, not even implicitly: a RELATIVE `cwd` is ignored
# as an anchor (resolving it would silently adopt the guard's own working
# directory). Providers send an absolute `cwd`; a relative one is treated like
# a missing one, so an absolute Write/Edit target can still anchor the search.
# The anchor is used to resolve RELATIVE targets and to locate the root only
# when FIXED_ROOT is absent; it never replaces a fixed root.
CWD_RAW=$(hook_json_get "$INPUT" "cwd")
WORKDIR=""
ANCHOR_SOURCE="none"
case "$CWD_RAW" in
  /*)
    WORKDIR="$(resolve_realpath "$CWD_RAW")"
    ANCHOR_SOURCE="cwd"
    ;;
esac

if [ -z "$WORKDIR" ]; then
  case "$TOOL_NAME" in
    Write|Edit)
      case "$FILE_PATH" in
        /*)
          WORKDIR="$(resolve_realpath "$(dirname "$FILE_PATH")")"
          ANCHOR_SOURCE="target"
          ;;
      esac
      ;;
    # Bash deliberately has no target-derived anchor: a command is not a path,
    # and picking one of its (possibly many, possibly computed) write targets as
    # the anchor would trust more parse evidence than this best-effort detector
    # claims. No `cwd` therefore means no anchor -> fail closed below.
  esac
fi

# --- Repo root (no promotion, no $PWD) --------------------------------
# The nearest ancestor of the ANCHOR that contains a `.meta-config/`
# directory — NOT the git toplevel (a project may live inside a larger git
# repo; containment must follow the agent-meta project root).
# Issue #943 (l): a nested agent-meta checkout (.agent-meta/ or
# external/agent-meta) is skipped in favour of the enclosing project, but kept
# as a fallback so a session opened only inside the submodule still resolves.
resolve_repo_root() {
  local dir="$1" parent first_skipped=""
  while [ -n "$dir" ]; do
    if [ -d "$dir/.meta-config" ]; then
      if hook_is_meta_submodule_dir "$dir"; then
        [ -n "$first_skipped" ] || first_skipped="$dir"
      else
        printf '%s' "$dir"
        return 0
      fi
    fi
    [ "$dir" = "/" ] && break
    parent="$(dirname "$dir")"
    [ "$parent" = "$dir" ] && break
    dir="$parent"
  done
  if [ -n "$first_skipped" ]; then
    printf '%s' "$first_skipped"
    return 0
  fi
  return 1
}

# Print a human-readable, absolute form of a target for a block message.
# Falls back to the raw value when it cannot be normalized (python failure).
display_target() {
  local raw="${1:-}" resolved=""
  case "$raw" in
    '') printf '%s' "(none)"; return 0 ;;
    /*) resolved="$(resolve_realpath "$raw")" ;;
    *)
      if [ -n "$WORKDIR" ]; then
        resolved="$(resolve_realpath "$WORKDIR/$raw")"
      fi
      ;;
  esac
  printf '%s' "${resolved:-$raw}"
}

# Message for "anchor exists, but no project root above it" (spec §Fehlermeldungen).
no_root_block() {
  local target="$1"
  echo "REPO_CONTAINMENT: no project root found above $WORKDIR (code repo-containment.no-root)." >&2
  echo "  A project root is a directory that contains \`.meta-config/\`." >&2
  echo "  This guard never promotes the working directory to a project root." >&2
  echo "  target:    $target" >&2
  echo "  anchor:    $WORKDIR            (payload \`cwd\`, or the target's own directory when \`cwd\` is missing)" >&2
  if [ -n "$CWD_RAW" ] && [ "$CWD_RAW" != "$WORKDIR" ]; then
    echo "  resolved:  payload \`cwd\` $CWD_RAW -> $WORKDIR (resolved)" >&2
  fi
  echo "  allowed:   only inside a project root (plus its configured tmp-sink)" >&2
  echo "  repair:    run \`python scripts/sync.py\` in the project, or open the session" >&2
  echo "             inside the project directory" >&2
  echo "  opt-out:   repo_containment.enabled: false in <project>/.meta-config/project.yaml" >&2
}

# Message for "no anchor at all": a relative Write/Edit target without `cwd`
# (spec §Fehlermeldungen, second skeleton). Same code, distinct reason.
no_anchor_block() {
  local target="$1"
  echo "REPO_CONTAINMENT: no project root found for a relative target without \`cwd\`" >&2
  echo "(code repo-containment.no-root)." >&2
  echo "  A relative path cannot be anchored: the payload carried no \`cwd\` (or an empty one)" >&2
  echo "  and the target is not absolute. Failing closed." >&2
  echo "  target:    $target" >&2
  if [ -n "$CWD_RAW" ]; then
    echo "  note:      payload \`cwd\` '$CWD_RAW' is not absolute and cannot anchor a root search." >&2
  fi
  echo "  repair:    re-run \`python scripts/sync.py\` for this provider (hook payload contract, issue #630);" >&2
  echo "             send an absolute \`file_path\`, or include \`cwd\` in the payload" >&2
}

# Message for Bash without an anchor. There is no spec skeleton for this case
# (the anchor rule is path-shaped); documented reading: fail closed with the
# same single code rather than guess an anchor from a command string.
bash_no_anchor_block() {
  local command="$1"
  echo "REPO_CONTAINMENT: no project root found for a Bash command without \`cwd\`" >&2
  echo "(code repo-containment.no-root)." >&2
  echo "  A Bash command is not a path: unlike Write/Edit it has no single target" >&2
  echo "  directory to anchor a project-root search on. Failing closed." >&2
  echo "  command:   $command" >&2
  if [ -n "$CWD_RAW" ]; then
    echo "  note:      payload \`cwd\` '$CWD_RAW' is not absolute and cannot anchor a root search." >&2
  fi
  echo "  repair:    re-run \`python scripts/sync.py\` for this provider (hook payload contract, issue #630);" >&2
  echo "             include \`cwd\` in the payload" >&2
}

if [ -z "$WORKDIR" ]; then
  if [ "$TOOL_NAME" = "Bash" ]; then
    bash_no_anchor_block "$(printf '%s' "$BASH_CMD" | head -c 200)"
  else
    no_anchor_block "$FILE_PATH"
  fi
  exit 2
fi

if [ -n "$FIXED_ROOT" ]; then
  # SR-B-18: a fixed anchor wins over the payload-derived root, so a cwd (or a
  # forged payload) can never redefine the jail.
  REPO_ROOT="$FIXED_ROOT"
else
  REPO_ROOT="$(resolve_repo_root "$WORKDIR")" || REPO_ROOT=""
fi
if [ -z "$REPO_ROOT" ]; then
  # No `.meta-config/` above the anchor: do NOT invent a root from the anchor
  # (the old fail-open) and do NOT read any config — a foreign project's
  # `enabled: false` must never unlock a write outside it.
  if [ "$TOOL_NAME" = "Bash" ]; then
    no_root_block "$(printf '%s' "$BASH_CMD" | head -c 200)"
  else
    no_root_block "$(display_target "$FILE_PATH")"
  fi
  exit 2
fi
CONFIG_FILE="$REPO_ROOT/.meta-config/project.yaml"

# --- Effective config resolution (mirrors scripts/lib/repo_containment.py) ---
# Prints exactly three KEY=VALUE lines; ALWAYS exits 0. Any failure (file
# missing, PyYAML missing, unparseable YAML) prints the safe-side defaults.
read_effective_containment() {
  "$_PY" - "$1" "$2" <<'PYEOF'
import os
import posixpath
import re
import sys

CONFIG_FILE, PROVIDER = sys.argv[1], sys.argv[2]

# Mirrors scripts/lib/repo_containment.py::tmp_sink_path_error (lexical rules).
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_RESERVED = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + ["COM%d" % i for i in range(1, 10)]
    + ["LPT%d" % i for i in range(1, 10)]
)
_FORBIDDEN_CHARS = frozenset('<>"|?*')
# Lower-cased protected segment prefixes (framework dirs + provider_root_dirs).
_PROTECTED = (
    (".git",), (".claude",), (".meta-config",), (".agents",), (".codex",),
    (".continue",), (".gemini",), (".github", "copilot"), (".kimi-code",),
    (".mammouth",), (".opencode",), (".zcode",),
)


def canonical_path(path):
    """Backslash -> slash BEFORE normpath, always POSIX-style."""
    return posixpath.normpath(path.replace("\\", "/"))


def path_error(path):
    """Return an error string for an unsafe sink path, else None."""
    if not isinstance(path, str) or not path.strip():
        return "empty or not a string"
    if _WINDOWS_DRIVE_RE.match(path):
        return "drive-letter path"
    if path[:1] in ("/", "\\"):
        return "absolute or UNC path"
    if any(ord(ch) < 32 for ch in path):
        return "control character"
    if path in (".", ".."):
        return "root or parent"
    segments = path.replace("\\", "/").split("/")
    if any(segment == ".." for segment in segments):
        return "'..' segment"
    for segment in segments:
        if segment in ("", "."):
            continue
        if ":" in segment:
            return "':' in segment"
        if any(ch in _FORBIDDEN_CHARS for ch in segment):
            return "forbidden character"
        if segment[-1] in (".", " "):
            return "trailing dot or space"
        if segment.split(".", 1)[0].rstrip(" ").upper() in _RESERVED:
            return "reserved Windows name"
    normalized = canonical_path(path)
    if normalized in ("", ".", "..") or normalized.startswith("../"):
        return "escapes the root"
    lowered = tuple(seg.lower() for seg in normalized.split("/"))
    for prefix in _PROTECTED:
        if lowered[: len(prefix)] == prefix:
            return "protected directory"
    return None


def emit(enabled, sink_enabled, sink_path, rejected=False):
    # SINK_REJECTED is observed only by tests/test_tmp_sink_path_parity.py
    # (AC-97); the shell consumer deliberately ignores it (silent fallback).
    print("ENABLED=%d" % (1 if enabled else 0))
    print("SINK_ENABLED=%d" % (1 if sink_enabled else 0))
    print("SINK_PATH=%s" % sink_path)
    print("SINK_REJECTED=%d" % (1 if rejected else 0))


try:
    import yaml

    with open(CONFIG_FILE, encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    raw = config.get("repo_containment")  # runtime-reader:repo_containment
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
    # Same decision and canonical form as Python; invalid => safe fallback.
    rejected = path_error(path) is not None
    path = ".tmp" if rejected else canonical_path(path)

    emit(enabled, sink_enabled, path, rejected)
except Exception as exc:
    # F4 safe-side: missing/unreadable/unparseable config never opens silently.
    # SR-B-20: this used to be silent, so a project that had explicitly set
    # repo_containment.enabled: false (and whose hook interpreter lacks
    # PyYAML) kept failing closed with no explanation. The guard still fails
    # CLOSED -- honouring the opt-out here would need the shared stdlib YAML
    # subset reader, and a misparse must never open the jail -- but the
    # ignored opt-out is now visible on stderr.
    print(
        "REPO_CONTAINMENT: warning: could not read " + CONFIG_FILE
        + " with PyYAML (" + type(exc).__name__ + "); containment stays ENABLED."
        + " A configured repo_containment.enabled: false is NOT honoured in"
        + " this state (fail-closed). Install PyYAML for the hook interpreter"
        + " or run the project sync.",
        file=sys.stderr,
    )
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

# Absolute sink for messages and for the allow-list text (AC-18): the hook's
# effective sink is the realpath of <root>/<sink>, matching
# scripts/lib/tmp_paths.py::resolve_tmp_paths(...).absolute (shared contract,
# tests/test_repo_containment_hook.py::test_hook_sink_matches_tmp_paths).
SINK_ABS="$(resolve_realpath "$REPO_ROOT/$SINK_PATH")"

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

# How the anchor was obtained, for block messages (the no-root message keeps
# the spec's fixed parenthetical instead).
anchor_label() {
  case "$ANCHOR_SOURCE" in
    target) printf '%s' "the target's own directory; payload carried no \`cwd\`" ;;
    *) printf '%s' "payload \`cwd\`" ;;
  esac
}

block_write() {
  local target="$1" reason="${2:-outside}" absolute
  absolute="$(display_target "$target")"
  if [ "$reason" = "sink-disabled" ]; then
    echo "REPO_CONTAINMENT: write target is inside the configured but DISABLED tmp-sink (prison mode)." >&2
    echo "  target:    $absolute" >&2
    echo "  reason:    the tmp-sink ($SINK_ABS) is writable only when" >&2
    echo "             repo_containment.tmp-sink.enabled: true." >&2
    echo "  anchor:    $WORKDIR            ($(anchor_label))" >&2
    echo "  repair:    set repo_containment.tmp-sink.enabled: true in" >&2
    echo "             $REPO_ROOT/.meta-config/project.yaml, or write outside the tmp-sink." >&2
  else
    echo "REPO_CONTAINMENT: write target is outside the repository root (prison mode)." >&2
    echo "  target:    $absolute" >&2
    echo "  repo root: $REPO_ROOT" >&2
    if [ "$SINK_ENABLED" = "1" ]; then
      echo "  allowed:   paths under $REPO_ROOT and under $SINK_ABS" >&2
    else
      echo "  allowed:   paths under $REPO_ROOT (the tmp-sink subtree $SINK_ABS is disabled)" >&2
    fi
    echo "  anchor:    $WORKDIR            ($(anchor_label))" >&2
    echo "  repair:    write inside $REPO_ROOT (or its tmp-sink), or re-run" >&2
    echo "             \`python scripts/sync.py\` in the project" >&2
  fi
  echo "  opt-out:   repo_containment.enabled: false in $REPO_ROOT/.meta-config/project.yaml" >&2
}

# --- Write/Edit: check the explicit target path ------------------------
# FILE_PATH was extracted above (the anchor may depend on it).
if [ "$TOOL_NAME" = "Write" ] || [ "$TOOL_NAME" = "Edit" ]; then
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
# The detector below tokenizes with shlex (punctuation-aware) and uses the
# shared quote/heredoc-aware splitter (hook_shell_scan_py) instead of a raw
# `re.split` on control operators. That fixes two opposite errors:
#   * a quoted operator / heredoc body is no longer split into fake commands
#     (#944 SR-B-16), while a real command after the heredoc terminator is
#     still scanned;
#   * `perl -pi`, `sed -Ei`/`sed -ni`, `cp -t DIR` and trailing flags are
#     recognised as writes (#944 SR-B-19).
# It reports candidate write targets, one per line; each is then run through
# the same containment_verdict as Write/Edit.
# Fail-closed (#944 verifier note): a detector crash used to be swallowed by
# `|| true`, so the command was ALLOWED. A non-zero detector exit now blocks.
if [ "$TOOL_NAME" = "Bash" ]; then
  # BASH_CMD was extracted above (an empty one already exited 0 before the
  # anchor step).
  _DETECTOR_SRC=$(hook_shell_scan_py
hook_shell_resolver_py
cat <<'PYEOF'
import os
import re
import shlex
import sys

# Bytes-in (surrogateescape): invalid UTF-8 / a lone surrogate in the command
# must not crash the detector (the crash used to be a silent allow).
command = sys.stdin.buffer.read().decode('utf-8', 'surrogateescape')

# Commands whose operands are created / modified / removed outright.
WRITE_ALL = {
    "touch", "mkdir", "rmdir", "rm", "truncate", "mkfifo", "mknod", "tee",
}
# Commands whose LAST non-flag operand (or -t/--target-directory value) is
# the destination write target.
WRITE_DEST = {"cp", "install", "rsync", "scp", "ln"}
# In-place editors: only the operands are written when -i/--in-place is set.
INPLACE = {"sed", "perl", "ruby"}
# Short options of the INPLACE editors that consume a value: the rest of a
# cluster after them is a script/program, not a flag (so '-e' does not hide a
# later 'i' in a script argument, and '-e' alone is not an in-place edit).
INPLACE_VALUE_OPTS = {"e", "f"}


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


def split_flags(args):
    """Return (positionals, target_dir) with flags and -t values removed.

    Trailing flags must not be mistaken for the destination: `cp a /etc/b -v`
    used to append '-v' (inside the repo) as the "destination" and allow the
    command (issue #944 SR-B-19).
    """
    positionals = []
    target_dir = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--":
            i += 1
            continue
        if a in ("-t", "--target-directory"):
            if i + 1 < len(args):
                target_dir = args[i + 1]
                i += 2
            else:
                i += 1
            continue
        if a.startswith("--target-directory="):
            target_dir = a.split("=", 1)[1]
            i += 1
            continue
        if a.startswith("-t") and len(a) > 2:
            target_dir = a[2:]
            i += 1
            continue
        if is_flag(a):
            i += 1
            continue
        if not is_skippable(a):
            positionals.append(a)
        i += 1
    return positionals, target_dir


def inplace_requested(args):
    for a in args:
        if a == "--in-place" or a.startswith("--in-place="):
            return True
        if a == "-i" or a.startswith("-i."):
            return True
        if a.startswith("-") and not a.startswith("--") and a != "-":
            for c in a[1:]:
                if c == "i":
                    return True
                if c in INPLACE_VALUE_OPTS:
                    break
    return False


def inplace_operands(args):
    """Operands that the editor writes: script values are not targets."""
    operands = []
    used_e = False
    skip_next = False
    for a in args:
        if skip_next:
            skip_next = False
            continue
        if a in ("-e", "--expression"):
            used_e = True
            skip_next = True
            continue
        if a.startswith("-e") and len(a) > 2 and not a.startswith("--"):
            used_e = True
            continue
        if a in ("-f", "--file"):
            skip_next = True
            continue
        if a.startswith("-f") and len(a) > 2 and not a.startswith("--"):
            continue
        if is_flag(a):
            continue
        if not is_skippable(a):
            operands.append(a)
    if not used_e and operands:
        # sed/perl/ruby: the first non-option operand is the script itself.
        operands = operands[1:]
    return operands


targets = []

for statement, _heredocs in split_shell_statements(command):
    tokens = tokenize(statement)
    if not tokens:
        continue

    # Redirection operators `>`, `>>`, `>|` (and `&>` once the `&` split above
    # has peeled it); the following token is the write target. shlex emits the
    # punctuation as single-character tokens, so collapse a run of '>'/'|'
    # before taking the target ('>> file' must not target '>').
    i = 0
    while i < len(tokens):
        if tokens[i] in (">", ">>", ">|"):
            j = i + 1
            while j < len(tokens) and tokens[j] in (">", "|", ">>", ">|"):
                j += 1
            if j < len(tokens) and not is_skippable(tokens[j]):
                targets.append(tokens[j])
            i = j + 1
            continue
        i += 1

    # Locate the command with the SHARED resolver (hook_common.sh
    # hook_shell_resolver_py): keywords, `case … in` arms, function bodies,
    # grouping, KEY=VALUE assignments, wrappers (with their positional
    # arity) and a transparent `--` are all handled there, not here. See the
    # header note for the shapes this closed in v1.5.0.
    idx = command_start(tokens)
    if idx >= len(tokens):
        continue
    cmd = os.path.basename(tokens[idx])
    args = tokens[idx + 1:]

    if cmd in WRITE_ALL:
        positionals, _target_dir = split_flags(args)
        targets.extend(positionals)
    elif cmd in WRITE_DEST:
        positionals, target_dir = split_flags(args)
        if target_dir is not None:
            if not is_skippable(target_dir):
                targets.append(target_dir)
        elif positionals:
            targets.append(positionals[-1])
    elif cmd == "mv":
        positionals, _target_dir = split_flags(args)
        targets.extend(positionals)
    elif cmd == "dd":
        for arg in args:
            if arg.startswith("of=") and not is_skippable(arg[3:]):
                targets.append(arg[3:])
    elif cmd in INPLACE:
        if inplace_requested(args):
            targets.extend(inplace_operands(args))

for target in targets:
    print(target)
PYEOF
)
  _DETECTOR_RC=0
  WRITE_TARGETS=$(printf '%s' "$BASH_CMD" | "$_PY" -c "$_DETECTOR_SRC" 2>/dev/null) || _DETECTOR_RC=$?
  if [ "$_DETECTOR_RC" != "0" ]; then
    echo "REPO_CONTAINMENT: the Bash write-target detector exited rc=$_DETECTOR_RC." >&2
    echo "Failing closed (#944) — a command the detector cannot evaluate must not be allowed." >&2
    exit 2
  fi

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
