#!/bin/bash
# Scenario assert for 107-commands-system (commands system gaps, AC-6.1/6.2)
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold.
#
# Config-driven: the expectations are derived from config/ai-providers.yaml
# (has_commands, commands_dir, commands_ext, commands_format, agents_dir),
# not from provider names. Providers without has_commands must emit no
# commands/prompts dir next to their agents dir.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (107-commands-system): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (107-commands-system): $*"
    exit 1
}

# Provider capability table for the providers configured in this scenario.
TABLE="$(REPO_ROOT="$REPO_ROOT" python3 - <<'PY'
import os, sys, yaml
root = os.environ["REPO_ROOT"]
with open(os.path.join(root, "config", "ai-providers.yaml"), encoding="utf-8") as fh:
    providers = yaml.safe_load(fh)["providers"]
with open(".meta-config/project.yaml", encoding="utf-8") as fh:
    wanted = yaml.safe_load(fh)["ai-providers"]
for name in wanted:
    pc = providers[name]
    print("\t".join([
        name,
        "1" if pc.get("has_commands") else "0",
        pc.get("commands_dir") or "-",
        pc.get("commands_ext") or "-",
        pc.get("commands_format") or "-",
        pc.get("commands_managed_index") or "-",
        pc.get("agents_dir") or "-",
    ]))
PY
)" || fail "could not derive provider capabilities"

[ -n "$TABLE" ] || fail "empty provider capability table"

ref_count=""
declared_dirs=""
seen_with=0
seen_without=0
while IFS=$'\t' read -r name has dir ext fmt index agents_dir; do
    if [ "$has" = "0" ]; then
        seen_without=$((seen_without + 1))
        # No command surface: derive the provider root from the configured
        # agents_dir; neither commands/ nor prompts/ may exist below it.
        [ "$agents_dir" != "-" ] || fail "$name: no agents_dir configured, cannot derive provider root"
        root="$(dirname "$agents_dir")"
        [ "$root" != "." ] || fail "$name: agents_dir '$agents_dir' has no provider root"
        for sub in commands prompts; do
            [ ! -e "$root/$sub" ] || fail "$name has no command surface but $root/$sub exists"
        done
        continue
    fi
    seen_with=$((seen_with + 1))
    [ -d "$dir" ] || fail "$name: command dir missing: $dir"
    declared_dirs="$declared_dirs $dir"
    count=$(find "$dir" -maxdepth 1 -type f -name "*$ext" ! -name ".*" | wc -l)
    [ "$count" -gt 0 ] || fail "$name: no *$ext command files in $dir"
    if [ -z "$ref_count" ]; then
        ref_count="$count"
    else
        [ "$count" = "$ref_count" ] || fail "$name: $count commands in $dir, expected $ref_count (same role filter for all providers)"
    fi
    [ -f "$dir/doc-now$ext" ] || fail "$name: $dir/doc-now$ext missing"
    # Role filter (negative): release-check has requires_roles: [release]
    # (commands/1-generic/release-check.md); the release role is not active here.
    [ ! -f "$dir/release-check$ext" ] || fail "$name: role-filtered release-check$ext emitted in $dir"
    if grep -q "requires_roles" "$dir/doc-now$ext"; then
        fail "$name: requires_roles leaked into $dir/doc-now$ext"
    fi
    case "$fmt" in
        toml)
            grep -q '^prompt = ' "$dir/doc-now$ext" || fail "$name: toml command lacks prompt key"
            ;;
        markdown|continue)
            head -1 "$dir/doc-now$ext" | grep -q '^---$' || fail "$name: command lacks frontmatter: $dir/doc-now$ext"
            ;;
        *) fail "$name: unknown commands_format '$fmt'" ;;
    esac
    if [ "$index" != "-" ]; then
        [ -f "$dir/$index" ] || fail "$name: managed index missing: $dir/$index"
        grep -q "doc-now$ext" "$dir/$index" || fail "$name: index $dir/$index does not list doc-now$ext"
    fi
done <<< "$TABLE"

[ "$seen_with" -ge 4 ] || fail "expected >= 4 command-capable providers, saw $seen_with"
[ "$seen_without" -ge 2 ] || fail "expected >= 2 command-less providers, saw $seen_without"

# Global counter-check: doc-now.* may only exist under declared commands_dir paths.
while IFS= read -r hit; do
    ok=0
    for d in $declared_dirs; do
        case "$hit" in ./"$d"/*) ok=1 ;; esac
    done
    [ "$ok" = 1 ] || fail "doc-now file outside declared commands_dir: $hit"
done < <(find . -name 'doc-now.*' -not -path './.scenario-logs/*')

# Idempotence: a second sync must not change any generated file.
# Hash set excludes volatile diagnostics (same exclusions as scenario 71).
snapshot() {
    local out
    out="$(find . -type f \
        -not -path './.git/*' \
        -not -path './.scenario-logs/*' \
        -not -name '*.log' \
        -not -name 'external-tools-drift.md' \
        -not -name '*.sync-backup-*' \
        -print0 | LC_ALL=C sort -z | xargs -0 -r sha256sum)" || return 1
    [ -n "$out" ] || return 1
    printf '%s\n' "$out"
}
before="$(snapshot)" || fail "snapshot before second sync failed or empty"
if ! python3 "$REPO_ROOT/scripts/sync.py" >.scenario-logs/sync2.log 2>&1; then
    tail -30 .scenario-logs/sync2.log
    fail "second sync failed (log above)"
fi
after="$(snapshot)" || fail "snapshot after second sync failed or empty"
[ "$before" = "$after" ] || fail "second sync changed files: $(diff <(echo "$before") <(echo "$after") | head -5)"

echo "ASSERT OK (107-commands-system): $seen_with command providers, $seen_without without, idempotent"
