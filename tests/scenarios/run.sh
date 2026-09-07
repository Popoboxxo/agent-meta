#!/bin/bash
# Regression-runs the scenario catalog (tests/scenarios/configs/*.project.yaml)
# against the sync.py in THIS checkout. Each scenario is synced into a fresh
# temp project directory (never against this repo itself), then dry-run,
# real sync and --validate are exercised.
#
# Usage:
#   tests/scenarios/run.sh                # run all scenarios
#   tests/scenarios/run.sh 01 12 17       # run only the given scenario id prefixes
#
# See tests/scenarios/registry.md for what each scenario covers and why.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIGS_DIR="$SCRIPT_DIR/configs"

FILTERS=("$@")

pass=0
fail=0
failed_names=()

matches_filter() {
    local id="$1"
    if [ "${#FILTERS[@]}" -eq 0 ]; then
        return 0
    fi
    for f in "${FILTERS[@]}"; do
        case "$id" in
            "$f"*) return 0 ;;
        esac
    done
    return 1
}

for cfg in "$CONFIGS_DIR"/*.project.yaml; do
    name="$(basename "$cfg" .project.yaml)"
    matches_filter "$name" || continue

    tmp_dir="$(mktemp -d)"
    mkdir -p "$tmp_dir/.meta-config"
    cp "$cfg" "$tmp_dir/.meta-config/project.yaml"

    log_dir="$tmp_dir/.scenario-logs"
    mkdir -p "$log_dir"

    (
        cd "$tmp_dir" || exit 1
        python3 "$REPO_ROOT/scripts/sync.py" --dry-run >"$log_dir/dryrun.log" 2>&1
        echo $? >"$log_dir/dryrun.rc"
        python3 "$REPO_ROOT/scripts/sync.py" >"$log_dir/sync.log" 2>&1
        echo $? >"$log_dir/sync.rc"
        python3 "$REPO_ROOT/scripts/sync.py" --validate >"$log_dir/validate.log" 2>&1
        echo $? >"$log_dir/validate.rc"
    )

    dry_rc="$(cat "$log_dir/dryrun.rc" 2>/dev/null || echo 1)"
    sync_rc="$(cat "$log_dir/sync.rc" 2>/dev/null || echo 1)"
    val_rc="$(cat "$log_dir/validate.rc" 2>/dev/null || echo 1)"

    if [ "$dry_rc" = "0" ] && [ "$sync_rc" = "0" ] && [ "$val_rc" = "0" ]; then
        echo "PASS  $name"
        pass=$((pass + 1))
        rm -rf "$tmp_dir"
    else
        echo "FAIL  $name  (dry-run=$dry_rc sync=$sync_rc validate=$val_rc)  logs kept at: $tmp_dir/.scenario-logs"
        fail=$((fail + 1))
        failed_names+=("$name")
    fi
done

echo "----"
echo "Scenarios: $((pass + fail))  Passed: $pass  Failed: $fail"

if [ "$fail" -gt 0 ]; then
    echo "Failed: ${failed_names[*]}"
    exit 1
fi
exit 0
