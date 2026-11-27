#!/bin/bash
# version: 1.10.0
# changelog: 1.10.0: issue #1275b -- resolve repo_containment.protected_paths with the syncer's default-replace-plus-gitmodules merge contract, emit the effective list as one JSON line, forward it to the path module as a single quoted argv without eval/splitting, fail safe to defaults plus gitmodules on invalid/unreadable config, and describe .gitmodules as conditional; 1.9.0: issue #1275a -- block Write/Edit/NotebookEdit and detected Bash writes under external/, .agent-meta/ and existing .gitmodules submodule paths; AM_ALLOW_PROTECTED_WRITE=1 bypasses only the protected-path gate, never root containment or the tmp-sink rule; mirror the decision in the non-deployed kernel and pin hook/kernel parity; convention boundary only; 1.8.0: issue #1238b1 -- extract config resolution, path verdicts and Bash write-target detection into flat hook_containment_*.py modules deployed beside hook_common.sh; preserve output, exit codes and fail-closed behavior, with only the trivial realpath -c one-liner retained; 1.7.0: issue #1251 -- fixed jail root and Bash variable expansion use adapter-owned AM_PROJECT_DIR exclusively; deployment-layout and payload-anchor fallbacks remain unchanged; 1.6.1: issue #1161 Pkt5 -- all payload fields are read in ONE hook_json_get_many parse (ok-trailer fail-closed check) instead of five separate field-read interpreter starts; the hook_json_usable / hook_known_tool_name fail-closed probes are unchanged; 1.6.0: issue #1151 (audit G1) -- NotebookEdit (tool_input.notebook_path) and MultiEdit are judged like Edit, PowerShell like Bash (F6-01); '~', '$HOME' and '${HOME}' targets are expanded, and curl -o/--output/--output-dir, wget -O/-o/-a/-P, tar -C (extract) / -f (create), unzip -d and git clone <dir> are write targets (F6-06); cd/pushd/popd are tracked: a relative target is judged against every directory the command may be in ('&&' moves it, any other separator keeps the old one too) and an unresolvable cd target blocks a later relative write (F6-07); a cd inside $(...) or a '( ... )' subshell is scoped to it and does not move the outer command, the hook-environment project-dir variable and $PWD (current directory set) are resolved as cd/write targets, and an old-style tar cluster ('tar cf /etc/x.tar .') yields its -f/-C values (review follow-up); bodies of $(...)/backtick substitutions are scanned (shared splitter, F6-03); the provider placeholder is no longer spelled out in a comment the sync-time replace rewrote (F6-12).
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
#                    inside the root. Protected paths default to external/,
#                    .agent-meta/ and existing .gitmodules entries; a configured
#                    repo_containment.protected_paths list replaces the defaults.
#                    Writes are blocked unless AM_ALLOW_PROTECTED_WRITE=1 is set;
#                    that override never widens the jail root or the sink rule.
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
# it would fail in exactly the projects this guard protects. Instead the
# deployed hook_containment_config.py uses the SAME config-reading mechanism
# as orchestrator-guard-impl.sh (python3 + yaml.safe_load on
# .meta-config/project.yaml, passing the path as argv so backslash-bearing
# Windows paths are never string-interpolated) and mirrors the resolver's
# precedence and safe-side rules. The tmp-sink path is
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
# protected provider directories are embedded in hook_containment_config.py
# (config/ai-providers.yaml is not deployed); the parity test fails when they
# drift from provider_root_dirs.
#
# Protected write paths (#1275b) live in the deployed flat
# hook_containment_path.py: repo_containment.protected_paths replaces the
# defaults external/ and .agent-meta/ when present; an existing
# <root>/.gitmodules always contributes every valid root-relative path = entry.
# Without .gitmodules and without config only the defaults apply. The config
# module emits the effective list as one JSON line; the shell forwards it as a
# single quoted argv value (never eval/splitting). Without
# AM_ALLOW_PROTECTED_WRITE=1 the gate stays active; root containment and the
# tmp-sink rule stay active even with the override. This is a convention
# boundary, not a security boundary. The non-deployed kernel/containment.py
# mirrors the default/gitmodules block/allow decision (tests/test_protected_paths.py).
#
# T24 (D1): the SCRATCH SINK PATH has a single source with this precedence:
# ARTIFACT_SCRATCH_DIR env -> classes[scratch].path from
# .meta-config/artifact-locations.resolved.json -> repo_containment.tmp-sink.path
# -> .tmp. Candidate paths pass through the SAME unchanged path_error() below;
# an unsafe value is ignored (fail-closed). The sink_enabled switch stays with
# repo_containment, and SINK_PATH emitted by the reader stays the raw
# project.yaml value so the parity suite keeps pinning the lexical rules.
#
# Provider identity: `AGENT_META_PROVIDER` is substituted per provider by
# sync.py's per-provider copy step (scripts/lib/hooks.py, which replaces the
# braced AGENT_META_PROVIDER placeholder with the provider name), exactly like
# orchestrator-guard-impl.sh. The placeholder itself is spelled out only on
# the assignment line below, so the replace never rewrites this comment
# (#1151 F6-12). That is the one reliable provider signal
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
#   1. $AM_PROJECT_DIR, when it carries `.meta-config/`;
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
#   * `eval` / `xargs` / `bash -c` strings, interpreters (`python -c
#     "open(...,'w')"`), targets in an arbitrary `$VAR`, and tools outside the
#     write-command set below can still smuggle a write outside the root.
#     Command substitutions ($(...), backticks, also inside double quotes)
#     are split and scanned since #1151; `~`/`$HOME` targets are expanded
#     and cd/pushd/popd are tracked (relative targets are judged against
#     every directory the command may be in; a cd inside $(...) or a
#     '( ... )' subshell stays scoped to it, a cd inside a `case` is not
#     scoped (over-blocks));
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
   || ! declare -F hook_json_get_many >/dev/null 2>&1 \
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

# #1161 Pkt5: ONE interpreter start reads every payload field this guard uses
# (hook_json_get_many, SPEC-HOOK-SINGLE-PARSE §2). The `ok` trailer tells a
# failed parse (rc 1, no output) from a missing field, so a malformed payload
# fails closed here. bash 3.2 compatible: `read -r -d ''` only, no
# eval/mapfile/namerefs. The hook_json_usable and hook_known_tool_name probes
# above stay unchanged.
_P_FAIL=0
{
  IFS= read -r -d '' _P_TOOL_NAME     || _P_FAIL=1
  IFS= read -r -d '' _P_FILE_PATH     || _P_FAIL=1
  IFS= read -r -d '' _P_NOTEBOOK_PATH || _P_FAIL=1
  IFS= read -r -d '' _P_COMMAND       || _P_FAIL=1
  IFS= read -r -d '' _P_CWD           || _P_FAIL=1
  IFS= read -r -d '' _P_TRAILER       || _P_FAIL=1
} < <(hook_json_get_many "$INPUT" \
       tool_name tool_input.file_path tool_input.notebook_path \
       tool_input.command cwd)
if [ "$_P_FAIL" -ne 0 ] || [ "${_P_TRAILER:-}" != "ok" ]; then
  echo "REPO_CONTAINMENT: empty or unparseable PreToolUse payload (cannot read fields)." >&2
  echo "Failing closed so an unknown tool call cannot write outside the repo root." >&2
  exit 2
fi

TOOL_NAME="$_P_TOOL_NAME"
FILE_PATH="$_P_FILE_PATH"
if [ -z "$FILE_PATH" ]; then
  FILE_PATH="$_P_NOTEBOOK_PATH"
fi
BASH_CMD="$_P_COMMAND"
CWD_RAW="$_P_CWD"

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

# Write-capable tools without their own branch map onto the one they behave
# like (#1151 F6-01): NotebookEdit/MultiEdit write a file like Edit (the
# notebook target is tool_input.notebook_path, read below), PowerShell runs a
# shell command in tool_input.command like Bash (best-effort: the detector
# reads it with shell grammar; PowerShell cmdlets are not write commands it
# knows, redirections are).
case "$TOOL_NAME" in
  NotebookEdit|MultiEdit) TOOL_NAME="Edit" ;;
  PowerShell) TOOL_NAME="Bash" ;;
esac

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

# The executable Python lives in flat modules beside hook_common.sh so sync.py
# deploys the same files to every provider's hooks/lib directory. A partial
# deployment must fail CLOSED (#595), never fall back to embedded Python.
for _containment_module in \
  hook_containment_config.py \
  hook_containment_path.py \
  hook_containment_shell.py; do
  if [ ! -r "$SCRIPT_DIR/lib/$_containment_module" ]; then
    echo "REPO_CONTAINMENT: required module $SCRIPT_DIR/lib/$_containment_module is missing or unreadable." >&2
    echo "Failing closed (issue #595) — re-run sync.py to redeploy the hooks/lib/ directory." >&2
    exit 2
  fi
done

# --- Realpath helper ---------------------------------------------------
# stdlib-only (python is already required above), works for a path that does
# not exist yet, and normalizes symlinks on every platform. Prints "" when the
# interpreter fails, so callers can treat an unnormalizable anchor as missing.
resolve_realpath() {
  "$_PY" -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1" 2>/dev/null
}

# --- Target extraction -------------------------------------------------
# FILE_PATH / BASH_CMD / CWD_RAW were read in the single parse above (the
# file_path -> notebook_path fallback is already applied there). They are
# extracted before the anchor: with a missing/empty `cwd`, an absolute
# Write/Edit target is what the anchor is derived from.

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
# $AM_PROJECT_DIR when it carries .meta-config/; 2) the deployment layout
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
  if [ -n "${AM_PROJECT_DIR:-}" ] && [ -d "$AM_PROJECT_DIR/.meta-config" ]; then
    root="$(resolve_realpath "$AM_PROJECT_DIR")"
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
  echo "REPO_CONTAINMENT: the fixed jail root (\$AM_PROJECT_DIR or the deployment layout) could not be resolved." >&2
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
# Prints ENABLED/SINK_ENABLED/SINK_PATH/SINK_REJECTED, PROTECTED_PATHS_JSON and
# SCRATCH_PATH. Config failures exit 0 with safe defaults. The JSON list stays
# on one physical line and is passed to the path module as one quoted argv.
read_effective_containment() {
  "$_PY" "$SCRIPT_DIR/lib/hook_containment_config.py" "$1" "$2" \
    "--include-protected-paths"
}

CONFIG_OUT="$(read_effective_containment "$CONFIG_FILE" "$PROVIDER")"
ENABLED="1"
SINK_ENABLED="1"
SINK_PATH=".tmp"
SCRATCH_PATH=""
PROTECTED_PATHS_JSON="null"
while IFS='=' read -r _key _value; do
  case "$_key" in
    ENABLED) ENABLED="$_value" ;;
    SINK_ENABLED) SINK_ENABLED="$_value" ;;
    SINK_PATH) SINK_PATH="$_value" ;;
    SCRATCH_PATH) SCRATCH_PATH="$_value" ;;
    PROTECTED_PATHS_JSON) PROTECTED_PATHS_JSON="$_value" ;;
  esac
done < <(printf '%s\n' "$CONFIG_OUT")

# T24 (D1): the resolved matrix (or the exported env var) is the single source
# for the scratch sink; the legacy project.yaml key is only a fallback. The
# sink_enabled switch and the lexical rules are unchanged.
if [ -n "$SCRATCH_PATH" ]; then
  SINK_PATH="$SCRATCH_PATH"
fi

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
# Prints ALLOW / BLOCK_SINK / BLOCK_PROTECTED / BLOCK for the (possibly
# relative) target. Semantics (spec §7 test table): a target inside a protected
# submodule path is blocked unless AM_ALLOW_PROTECTED_WRITE=1; otherwise a
# target inside the repo root is allowed; a target inside
# <repo root>/<tmp-sink.path> is allowed ONLY while the sink is enabled — a
# disabled sink excludes its own subtree even though that subtree physically
# sits inside the root (`.tmp` with sink -> 0, `.tmp` without sink -> 2).
# Everything else is BLOCK.
# Uses os.path.realpath so symlinks pointing outside the root are refused
# too; realpath also normalises a not-yet-existing Write target (equivalent
# to `realpath -m`). On any python error nothing is printed, which the caller
# treats as BLOCK (fail closed).
containment_verdict() {
  # PROTECTED_PATHS_JSON defaults to JSON null on config-reader failure, which
  # selects the path module's legacy defaults + existing .gitmodules fallback.
  "$_PY" "$SCRIPT_DIR/lib/hook_containment_path.py" \
    "$REPO_ROOT" "$WORKDIR" "$SINK_ENABLED" "$SINK_PATH" "$1" \
    "$PROTECTED_PATHS_JSON"
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
  if [ "$reason" = "cwd-unknown" ]; then
    echo "REPO_CONTAINMENT: relative write target after a directory change the hook cannot resolve (prison mode)." >&2
    echo "  target:    $target (relative to an unknown directory)" >&2
    echo "  reason:    a cd/pushd/popd to a computed path ('\$VAR', 'cd -', popd) hides where it lands (#1151)." >&2
    echo "  repair:    use a literal directory or an absolute target inside $REPO_ROOT" >&2
  elif [ "$reason" = "protected" ]; then
    echo "REPO_CONTAINMENT: write target is inside a protected path (prison mode)." >&2
    echo "  target:    $absolute" >&2
    echo "  reason:    protected paths come from repo_containment.protected_paths" >&2
    echo "             (default external/, .agent-meta/) plus all valid path =" >&2
    echo "             entries in an existing .gitmodules file." >&2
    echo "  override:  AM_ALLOW_PROTECTED_WRITE=1 allows this protected-path write only;" >&2
    echo "             writes outside $REPO_ROOT remain blocked." >&2
    echo "  boundary:  best-effort convention boundary, not a security boundary." >&2
  elif [ "$reason" = "sink-disabled" ]; then
    echo "REPO_CONTAINMENT: write target is inside the configured but DISABLED tmp-sink (prison mode)." >&2
    echo "  target:    $absolute" >&2
    echo "  reason:    the tmp-sink ($SINK_ABS) is writable only when" >&2
    echo "             repo_containment.tmp-sink.enabled: true." >&2
    echo "             Its path comes from artifact-locations.classes.scratch.path" >&2
    echo "             (fallback: repo_containment.tmp-sink.path)." >&2
    echo "  anchor:    $WORKDIR            ($(anchor_label))" >&2
    echo "  repair:    set repo_containment.tmp-sink.enabled: true in" >&2
    echo "             $REPO_ROOT/.meta-config/project.yaml, adjust" >&2
    echo "             artifact-locations.classes.scratch.path, or write outside the tmp-sink." >&2
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
    BLOCK_PROTECTED)
      block_write "$FILE_PATH" "protected"
      exit 2
      ;;
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
  _DETECTOR_RC=0
  WRITE_TARGETS=$(printf '%s' "$BASH_CMD" | "$_PY" "$SCRIPT_DIR/lib/hook_containment_shell.py" "$WORKDIR" 2>/dev/null) || _DETECTOR_RC=$?
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
      # Relative target after a cd/pushd the detector cannot resolve
      # ('cd "$DIR"', 'cd -', popd): its real location is unknown (#1151 F6-07).
      if [ "${candidate:0:1}" = $'\x01' ]; then
        BLOCKED_TARGET="${candidate:1}"
        BLOCKED_REASON="cwd-unknown"
        break
      fi
      case "$(containment_verdict "$candidate")" in
        ALLOW) ;;
        BLOCK_PROTECTED)
          BLOCKED_TARGET="$candidate"
          BLOCKED_REASON="protected"
          break
          ;;
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
