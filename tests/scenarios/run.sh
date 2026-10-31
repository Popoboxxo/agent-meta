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
# Usage (three modes):
#   tests/scenarios/run.sh                # run all scenarios
#   tests/scenarios/run.sh 01 12 17       # run only the given scenario id prefixes
#   tests/scenarios/run.sh --list         # print the selected names, run nothing
#
#   SCENARIO_SHARD=2 SCENARIO_TOTAL=4 tests/scenarios/run.sh
#                                         # run only shard 2 of 4 (CI matrix)
#
#   SCENARIO_JOBS=2 tests/scenarios/run.sh
#                                         # run the selected scenarios two at a
#                                         # time inside this shard (default 1 =
#                                         # strictly sequential). Output order
#                                         # stays the selection order.
#
# Selection order is fixed: (1) the positional prefix filters narrow the
# catalog (prefix match on the scenario name), then (2) a shard selection is
# applied to the *remaining*, locale-independently sorted list --
# 0-based index % SCENARIO_TOTAL == SCENARIO_SHARD - 1. Both SCENARIO_SHARD
# and SCENARIO_TOTAL must be set together as positive integers with
# 1 <= SCENARIO_SHARD <= SCENARIO_TOTAL. `--list` applies the same selection
# and prints one scenario name per line, which makes shard coverage provable
# without running sync.
#
# See tests/scenarios/registry.md for what each scenario covers and why.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIGS_DIR="$SCRIPT_DIR/configs"

usage() {
    cat >&2 <<'EOF'
Usage: tests/scenarios/run.sh [--list] [<scenario-id-prefix> ...]

  (no args)        run every scenario
  <prefix> ...     run only scenarios whose name starts with a prefix
  --list           print the selected scenario names (one per line), run nothing

Environment:
  SCENARIO_SHARD=<i>  which shard to run (1-based)
  SCENARIO_TOTAL=<n>  number of shards; both must be set together
  SCENARIO_JOBS=<n>   scenarios to run concurrently inside this shard
                      (default 1 = sequential)
EOF
}

LIST_ONLY=0
FILTERS=()
for arg in "$@"; do
    case "$arg" in
        --list)
            LIST_ONLY=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            echo "error: unknown option '$arg'" >&2
            usage
            exit 2
            ;;
        *)
            FILTERS+=("$arg")
            ;;
    esac
done

# --- shard validation -------------------------------------------------------
SHARD="${SCENARIO_SHARD:-}"
TOTAL="${SCENARIO_TOTAL:-}"
shard_active=0

if [ -n "$SHARD" ] || [ -n "$TOTAL" ]; then
    if [ -z "$SHARD" ] || [ -z "$TOTAL" ]; then
        echo "error: SCENARIO_SHARD and SCENARIO_TOTAL must be set together" >&2
        exit 2
    fi
    case "$SHARD" in
        ''|*[!0-9]*)
            echo "error: SCENARIO_SHARD must be a positive integer (got '$SHARD')" >&2
            exit 2
            ;;
    esac
    case "$TOTAL" in
        ''|*[!0-9]*)
            echo "error: SCENARIO_TOTAL must be a positive integer (got '$TOTAL')" >&2
            exit 2
            ;;
    esac
    if [ "$SHARD" -lt 1 ] || [ "$TOTAL" -lt 1 ]; then
        echo "error: SCENARIO_SHARD and SCENARIO_TOTAL must be positive integers" >&2
        exit 2
    fi
    if [ "$SHARD" -gt "$TOTAL" ]; then
        echo "error: SCENARIO_SHARD ($SHARD) must be <= SCENARIO_TOTAL ($TOTAL)" >&2
        exit 2
    fi
    shard_active=1
fi

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

# Sorted, locale-independent scenario name list. `LC_ALL=C sort` keeps the
# order identical on every runner; no `mapfile` (absent in macOS bash 3.2).
SCENARIO_NAMES=()
while IFS= read -r name; do
    SCENARIO_NAMES+=("$name")
done < <(
    for cfg in "$CONFIGS_DIR"/*.project.yaml; do
        [ -e "$cfg" ] || continue
        basename "$cfg" .project.yaml
    done | LC_ALL=C sort
)

# Prefix filter first, then shard selection over the filtered, sorted list.
SELECTED=()
index=0
for name in ${SCENARIO_NAMES[@]+"${SCENARIO_NAMES[@]}"}; do
    matches_filter "$name" || continue
    if [ "$shard_active" -eq 1 ] && [ $((index % TOTAL)) -ne $((SHARD - 1)) ]; then
        index=$((index + 1))
        continue
    fi
    SELECTED+=("$name")
    index=$((index + 1))
done

if [ "$LIST_ONLY" -eq 1 ]; then
    for name in ${SELECTED[@]+"${SELECTED[@]}"}; do
        printf '%s\n' "$name"
    done
    exit 0
fi

# --- execution --------------------------------------------------------------
# Every scenario builds its own mktemp directory and never touches the checkout,
# so scenarios are independent by construction. Inside a shard they were run
# strictly sequentially (~880 s per shard for 22 scenarios), while the CI matrix
# already fans out over four shards. SCENARIO_JOBS runs them N-at-a-time INSIDE
# the shard instead of adding another matrix leg: the runner pool (20 concurrent
# jobs per account), not the CPU, is what is actually scarce.
#
# Results are buffered per scenario and replayed in selection order, so a
# parallel run produces the same PASS/FAIL listing as a serial one. No `wait -n`
# (absent in bash 3.2): workers get round-robin batches and are joined with a
# plain `wait`.

SCENARIO_JOBS="${SCENARIO_JOBS:-1}"
case "$SCENARIO_JOBS" in
    ''|*[!0-9]*)
        echo "error: SCENARIO_JOBS must be a positive integer (got '$SCENARIO_JOBS')" >&2
        exit 2
        ;;
esac
if [ "$SCENARIO_JOBS" -lt 1 ]; then
    echo "error: SCENARIO_JOBS must be at least 1 (got '$SCENARIO_JOBS')" >&2
    exit 2
fi

RESULTS_DIR="$(mktemp -d)"

# Runs one scenario and records its verdict in $RESULTS_DIR.
# .out    human-readable block (replayed in order by the caller)
# .status 0 = pass, 1 = fail
run_one() {
    local name="$1"
    local tmp_dir log_dir dry_rc sync_rc val_rc assert_script assert_rc

    tmp_dir="$(mktemp -d)"
    mkdir -p "$tmp_dir/.meta-config"
    cp "$CONFIGS_DIR/$name.project.yaml" "$tmp_dir/.meta-config/project.yaml"

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
        printf 'PASS  %s\n' "$name" >"$RESULTS_DIR/$name.out"
        printf '0\n' >"$RESULTS_DIR/$name.status"
        rm -rf "$tmp_dir"
    else
        local assert_note=""
        if [ -x "$assert_script" ]; then
            assert_note=" assert=${assert_rc:-skipped}"
        fi
        {
            printf 'FAIL  %s  (dry-run=%s sync=%s validate=%s%s)  logs kept at: %s\n' \
                "$name" "$dry_rc" "$sync_rc" "$val_rc" "$assert_note" "$log_dir"
            if [ -n "$assert_rc" ] && [ "$assert_rc" != "0" ]; then
                echo "------ assertion output ($name) ------"
                cat "$log_dir/assert.log"
                echo "--------------------------------------"
            fi
        } >"$RESULTS_DIR/$name.out"
        printf '1\n' >"$RESULTS_DIR/$name.status"
    fi
}

if [ "${#SELECTED[@]}" -gt 0 ]; then
    if [ "$SCENARIO_JOBS" -le 1 ]; then
        for name in "${SELECTED[@]}"; do
            run_one "$name"
            cat "$RESULTS_DIR/$name.out"
        done
    else
        workers="$SCENARIO_JOBS"
        if [ "$workers" -gt "${#SELECTED[@]}" ]; then
            workers="${#SELECTED[@]}"
        fi
        w=0
        while [ "$w" -lt "$workers" ]; do
            (
                i="$w"
                while [ "$i" -lt "${#SELECTED[@]}" ]; do
                    run_one "${SELECTED[$i]}"
                    i=$((i + workers))
                done
            ) &
            w=$((w + 1))
        done
        wait
        for name in "${SELECTED[@]}"; do
            cat "$RESULTS_DIR/$name.out"
        done
    fi
fi

pass=0
fail=0
failed_names=()
for name in ${SELECTED[@]+"${SELECTED[@]}"}; do
    if [ "$(cat "$RESULTS_DIR/$name.status" 2>/dev/null || echo 1)" = "0" ]; then
        pass=$((pass + 1))
    else
        fail=$((fail + 1))
        failed_names+=("$name")
    fi
done

rm -rf "$RESULTS_DIR"

echo "----"
if [ "$shard_active" -eq 1 ]; then
    echo "Scenarios (shard $SHARD/$TOTAL): $((pass + fail))  Passed: $pass  Failed: $fail"
else
    echo "Scenarios: $((pass + fail))  Passed: $pass  Failed: $fail"
fi

if [ "$fail" -gt 0 ]; then
    echo "Failed: ${failed_names[*]}"
    exit 1
fi
exit 0
