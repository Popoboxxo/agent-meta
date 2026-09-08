#!/bin/bash
# Regression-runs the scenario catalog (tests/scenarios/configs/*.project.yaml)
# against the sync.py in THIS checkout. Each scenario is synced into a fresh
# temp project directory (never against this repo itself), then dry-run,
# real sync and --validate are exercised.
#
# Per-scenario content assertions (optional):
#   If tests/scenarios/asserts/<scenario-name>.sh exists and is executable,
#   it is run after the --validate step (only when dry-run/sync/validate
#   all passed), with cwd = the scenario's temp project dir, and REPO_ROOT
#   (path to THIS agent-meta checkout) provided BOTH as env var and as $1.
#   A non-zero exit marks the scenario FAIL: the assertion's stdout/stderr
#   is printed and kept in <tmp>/.scenario-logs/assert.log. Scenarios
#   without an assert file behave exactly as before.
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

    # Optional per-scenario content assertions (see header comment). Only
    # run against a fully successful sync; absence of an assert file means
    # zero behavior change for that scenario.
    assert_script="$SCRIPT_DIR/asserts/$name.sh"
    assert_rc=""
    if [ -x "$assert_script" ] && [ "$dry_rc" = "0" ] && [ "$sync_rc" = "0" ] && [ "$val_rc" = "0" ]; then
        (
            cd "$tmp_dir" || exit 1
            REPO_ROOT="$REPO_ROOT" "$assert_script" "$REPO_ROOT"
        ) >"$log_dir/assert.log" 2>&1
        assert_rc=$?
    fi

    if [ "$dry_rc" = "0" ] && [ "$sync_rc" = "0" ] && [ "$val_rc" = "0" ] && [ "${assert_rc:-0}" = "0" ]; then
        echo "PASS  $name"
        pass=$((pass + 1))
        rm -rf "$tmp_dir"
    else
        assert_note=""
        if [ -x "$assert_script" ]; then
            assert_note=" assert=${assert_rc:-skipped}"
        fi
        echo "FAIL  $name  (dry-run=$dry_rc sync=$sync_rc validate=$val_rc${assert_note})  logs kept at: $log_dir"
        if [ -n "$assert_rc" ] && [ "$assert_rc" != "0" ]; then
            echo "------ assertion output ($name) ------"
            cat "$log_dir/assert.log"
            echo "--------------------------------------"
        fi
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
