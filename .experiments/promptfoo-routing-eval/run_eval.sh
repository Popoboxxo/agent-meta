#!/bin/bash
# Fallback runner mirroring promptfooconfig.yaml's test cases 1:1, for use
# if the real `promptfoo` CLI can't be installed (e.g. slow npm registry in
# a sandboxed environment). Same provider script, same test cases, same
# pass/fail semantics -- just orchestrated by hand instead of the binary.
#
# Grading is an exact, normalized one-word match (trim + lowercase) instead
# of a loose substring check, so a model that rambles instead of answering
# with the one required word is correctly counted as a failure.
#
# Each case runs REPEAT times (default 3) to surface flakiness -- override
# with `REPEAT=1 ./run_eval.sh` for a fast smoke run.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

REPEAT="${REPEAT:-3}"

# entry format: "task|expected[,expected2,...]" -- a comma-separated
# expected list means any of those answers is acceptable (used for the
# genuinely ambiguous multi-intent case).
declare -a TASKS=(
  "Bitte behebe den Bug in der Login-Funktion, wo Passwörter falsch validiert werden.|bugfix"
  "Der Sortier-Algorithmus liefert bei negativen Zahlen ein falsches Ergebnis, das muss korrigiert werden.|bugfix"
  "Bitte behebe den Rundungsfehler in der Preisberechnung.|bugfix"
  "Wir brauchen ein komplett neues Feature: ein Dark-Mode-Umschalter in den Einstellungen.|feature-lifecycle"
  "Wir wollen die Möglichkeit einbauen, dass Nutzer ein eigenes Profilbild hochladen können.|feature-lifecycle"
  "Bitte aktualisiere die README mit den neuen Installationsschritten.|docs-update"
  "Der Leitfaden für Endnutzer beschreibt noch den alten Login-Ablauf, das muss korrigiert werden.|docs-update"
  "Räum bitte den Code in diesem Modul auf, da ist viel Duplikation drin.|refactor"
  "Diese Funktion ist 400 Zeilen lang und erledigt fünf verschiedene Dinge gleichzeitig, das sollte man aufteilen.|refactor"
  "Erstelle ein Konzept-Dokument, das die Trade-offs zwischen den beiden Architektur-Ansätzen abwägt.|concept-development"
  "Bevor wir loslegen, sollten wir aufschreiben, welche Architekturoptionen es gibt und was für und gegen jede spricht.|concept-development"
  "Produktions-Hotfix: die App crasht gerade für alle Nutzer, wir brauchen SOFORT einen schnellen Fix.|quick-fix"
  "Wir müssen die eingehenden Störungsmeldungen triagieren und priorisieren, bevor wir irgendwas fixen.|quick-fix"
  "Wie ist das Wetter heute in Berlin?|none"
  "Führe bitte die Test-Suite aus und sag mir, ob sie durchläuft.|none"
  "Erklär mir bitte, wie die Authentifizierung in diesem Projekt aktuell funktioniert.|none"
  "Es gibt einen Bug, den wir dringend fixen und deployen müssen, aber der Code drumherum sollte dabei auch gleich aufgeräumt werden.|bugfix,quick-fix,refactor"
)

PROMPT_TMPL='User-Anfrage: "%s"
Antworte NUR mit dem Namen der passenden Pipeline aus der Intent-Routing-Tabelle
(bugfix, concept-development, docs-update, feature-lifecycle, quick-fix, refactor)
oder mit "none", falls keine passt. Keine Erklärung, kein Fließtext -- nur das eine Wort.'

cases_total=0
cases_stable_pass=0
cases_flaky=0
cases_stable_fail=0

printf "%-90s %-25s %-10s\n" "TASK" "EXPECTED" "RESULT"
for entry in "${TASKS[@]}"; do
  task="${entry%%|*}"
  expected_raw="${entry##*|}"
  IFS=',' read -ra expected_list <<< "$expected_raw"
  prompt=$(printf "$PROMPT_TMPL" "$task")

  run_pass=0
  results=()
  for ((i = 1; i <= REPEAT; i++)); do
    actual=$(./provider.sh "$prompt" 2>/dev/null | tr -d '\n')
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
  if [[ "$run_pass" -eq "$REPEAT" ]]; then
    status="PASS"
    cases_stable_pass=$((cases_stable_pass + 1))
  elif [[ "$run_pass" -eq 0 ]]; then
    status="FAIL"
    cases_stable_fail=$((cases_stable_fail + 1))
  else
    status="FLAKY"
    cases_flaky=$((cases_flaky + 1))
  fi

  printf "%-90s %-25s %-10s (%d/%d, got: %s)\n" \
    "${task:0:88}" "$expected_raw" "$status" "$run_pass" "$REPEAT" "$(IFS=/; echo "${results[*]}")"
done

echo ""
echo "SUMMARY: $cases_total cases -- $cases_stable_pass stable-pass, $cases_flaky flaky, $cases_stable_fail stable-fail (repeat=$REPEAT)"
