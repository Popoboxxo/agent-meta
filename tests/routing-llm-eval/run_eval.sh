#!/bin/bash
# Generalized runner for the routing-llm-eval catalog. Reads test cases from
# catalog.generated.yaml + catalog.manual.yaml (merged via list_cases.py)
# instead of a hardcoded TASKS array, and dispatches them to a
# `provider-<name>.sh "<prompt>"` script selected via --provider (default:
# claude, currently the only implemented provider -- Opencode/Antigravity
# are Phase 2/3, see docs/concepts/planned/orchestrator-routing-test-suite.md).
#
# Promoted + generalized from the PoC at
# .experiments/promptfoo-routing-eval/run_eval.sh (PR #497). Same grading
# semantics: exact, normalized one-word match (trim + lowercase) instead of
# a loose substring check, so a model that rambles instead of answering with
# the one required word is correctly counted as a failure.
#
# Each case runs REPEAT times (default 3) to surface flakiness -- override
# with `REPEAT=1 ./run_eval.sh` for a fast smoke run during development.
#
# Usage:
#   ./run_eval.sh                     # provider=claude, REPEAT=3
#   ./run_eval.sh --provider claude
#   REPEAT=1 ./run_eval.sh            # fast smoke run
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

REPEAT="${REPEAT:-3}"
PROVIDER="claude"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --provider)
      PROVIDER="$2"
      shift 2
      ;;
    --provider=*)
      PROVIDER="${1#*=}"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: $0 [--provider claude]" >&2
      exit 2
      ;;
  esac
done

PROVIDER_SCRIPT="./provider-${PROVIDER}.sh"
if [[ ! -x "$PROVIDER_SCRIPT" ]]; then
  echo "No provider script found/executable at $PROVIDER_SCRIPT" >&2
  echo "Currently implemented: claude. Opencode/Antigravity are Phase 2/3 (not yet built)." >&2
  exit 2
fi

PROMPT_TMPL='User-Anfrage: "%s"
Antworte NUR mit dem Namen der passenden Pipeline aus der Intent-Routing-Tabelle
(bugfix, concept-development, docs-update, feature-lifecycle, quick-fix, refactor)
oder mit "none", falls keine passt. Keine Erklärung, kein Fließtext -- nur das eine Wort.'

SEP=$'\x1f'

cases_total=0
cases_stable_pass=0
cases_flaky=0
cases_stable_fail=0

declare -A cat_total
declare -A cat_pass

printf "%-24s %-90s %-25s %-10s\n" "ID" "TASK" "EXPECTED" "RESULT"

while IFS="$SEP" read -r id pipeline category expected_raw source_keyword task <&3; do
  [[ -z "$id" ]] && continue
  IFS=',' read -ra expected_list <<< "$expected_raw"
  prompt=$(printf "$PROMPT_TMPL" "$task")

  run_pass=0
  results=()
  for ((i = 1; i <= REPEAT; i++)); do
    actual=$("$PROVIDER_SCRIPT" "$prompt" </dev/null 2>/dev/null | tr -d '\n')
    actual_norm=$(echo "$actual" | tr '[:upper:]' '[:lower:]' | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')
    matched=false
    for exp in "${expected_list[@]}"; do
      if [[ "$actual_norm" == "$exp" ]]; then
        matched=true
        break
      fi
    done
    if [[ "$matched" == true ]]; then
      run_pass=$((run_pass + 1))
    fi
    results+=("$actual_norm")
  done

  cases_total=$((cases_total + 1))
  cat_total["$category"]=$(( ${cat_total["$category"]:-0} + 1 ))
  if [[ "$run_pass" -eq "$REPEAT" ]]; then
    status="PASS"
    cases_stable_pass=$((cases_stable_pass + 1))
    cat_pass["$category"]=$(( ${cat_pass["$category"]:-0} + 1 ))
  elif [[ "$run_pass" -eq 0 ]]; then
    status="FAIL"
    cases_stable_fail=$((cases_stable_fail + 1))
  else
    status="FLAKY"
    cases_flaky=$((cases_flaky + 1))
  fi

  printf "%-24s %-90s %-25s %-10s (%d/%d, got: %s)\n" \
    "$id" "${task:0:88}" "$expected_raw" "$status" "$run_pass" "$REPEAT" "$(IFS=/; echo "${results[*]}")"
done 3< <(python3 ./list_cases.py)

if [[ "$cases_total" -eq 0 ]]; then
  echo "ERROR: no test cases loaded (broken/empty catalog?) -- refusing to report a false-green summary." >&2
  exit 1
fi

echo ""
echo "By category:"
for cat in "${!cat_total[@]}"; do
  echo "  $cat: ${cat_pass[$cat]:-0}/${cat_total[$cat]} stable-pass"
done

echo ""
echo "SUMMARY: provider=$PROVIDER, $cases_total cases -- $cases_stable_pass stable-pass, $cases_flaky flaky, $cases_stable_fail stable-fail (repeat=$REPEAT)"
