# Dynamic Routing + Template Slimming — Task 17 Verification Report

> **Ergebnis: PASSED / VERIFIED**  
> **Abschlussentscheidung: Task 17 bleibt bis zum separaten Ledger-Update uncompleted.**

## Status

Die finale Gate-Evidenz ist grün: Die vollständige Test-Suite endet mit Exit 0, A7 ist mit 14 bestandenen Tests grün, B2/B3 ist mit 19 bestandenen Tests grün, der Model-Discovery-Testfile mit 34 bestandenen Tests grün und der fokussierte Browser-Satz mit 8 bestandenen Tests grün. Der vollständige Browser-Satz umfasst 38 passed, 2 skipped, Exit 0.

Der finale Lauf wurde ausdrücklich im **socket-free profile** mit `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` ausgeführt. Es wurde **kein** normaler Plugin-Autoload-Lauf als dieser Nachweis behauptet. Die Playwright-Browser wurden extern bereitgestellt; es wurde kein Repository-Socket-Bypass committed.

Die früheren FAILED-Evidenzstände bleiben als supersedierte Historie nachvollziehbar, sind aber nicht der aktuelle Gate-Status. In diesem Dispatch wurden ausschließlich dieser Report geändert; Plan und Ledger wurden nicht angefasst.

## Scope/Traceability

- **Branch:** `feat/dynamic-routing-template-slimming`
- **Plan:** `docs/plans/2026-09-19-dynamic-routing-template-slimming-plan.md:522-538` — Task 17
- **Spec:** `docs/specs/2026-09-19-dynamic-routing-template-slimming.md`, Status `APPROVED`, Revision 4
- **REQ-ID:** n/a
- **Task-17-Ziele:** A7, B4, B5
- **A7:** Capability-Unverändertheit und `ROUTE_INTENT_CALLABLE`-Fallback — bestanden.
- **B2/B3:** Equivalence-/Copy-Gate — bestanden, 19/19.
- **B4:** Vollständige Suite grün und Sync-Dry-Run fehlerfrei — bestanden; Sync-Warnings bleiben Follow-ups.
- **B5:** Zeilen-/Byte-Reduktion — weiterhin nur Metrik, kein Hard-Gate.

**Gate-Text-Revision (uncommitted):** Die uncommitted Planrevision hat den Task-17-Gate-Text von der früheren fokussierten Kommandoform mit der Sequenz `--validate && --dry-run` auf die aufgezeichnete Form `python3 scripts/sync.py --validate --dry-run` plus die vollständige Verifikation `python3 -m pytest tests/ -q` erweitert. Dieser Report verifiziert die aufgezeichnete erweiterte Form; am Plan wurde nichts geändert.

## Commands and Results

### Vollständige Test-Suite

**Finaler Befehl:**

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PLAYWRIGHT_BROWSERS_PATH=/var/tmp/opencode/ms-playwright python3 -m pytest tests/ -q -rs
```

- **Exit-Code:** 0
- **Passed:** 3154
- **Skipped:** 2
- **Warnings:** 102
- **Zusätzliche bestandene Subtests:** 11
- **Laufzeit:** ca. 564 s (`564.98s` im Log)
- **Errors:** keine
- **Collection failures:** keine

**Exakte, bestehende Skips:**

- `tests/browser/test_admin_ui_consistency_p1.py:37` — `no backups present to render a Delete button against`
- `tests/browser/test_admin_ui_consistency_p3.py:82` — `no backups present to render a Delete button against`

Beide sind datenabhängige, bestehende Guards. Es wurden keine neuen Skip-Marker und keine unerwarteten Skips hinzugefügt.

**Evidenz:**

- `/var/tmp/opencode/val/full.log`
- `/var/tmp/opencode/val/validation-report-models-page.md`
- `/var/tmp/opencode/t17-full2.log` — unabhängiger weiterer Vollsuite-Nachweis mit gleicher grüner Ergebnislinie

### Fokussierte Läufe

| Suite | Ergebnis | Evidenz |
|---|---:|---|
| `tests/test_model_discovery.py` | 34 passed, Exit 0 | `/var/tmp/opencode/am-testrun/01-model-discovery.log` |
| `tests/test_snippet_copy_contract.py` + `tests/test_template_slimming_equivalence.py` | 19 passed, Exit 0 | `/var/tmp/opencode/am-testrun/02-slimming.log` |
| Browser: `test_routing.py`, `test_project_form_editors.py`, `test_tier_presets_save.py` | 8 passed, Exit 0 | `/var/tmp/opencode/am-testrun/03-browser.log` |
| A7: `test_no_role_routes_in_templates.py` + `test_route_guard_snippets.py` | 14 passed, Exit 0 | `/var/tmp/opencode/am-testrun/04-route-guard.log` |
| Vollständiger Browser-Satz `tests/browser/` | 38 passed, 2 skipped, Exit 0 | `/var/tmp/opencode/val/browser.log` |

Der Model-Discovery-Follow-up ist damit erledigt; der vorherige Live-Netzfehler ist nicht mehr aufgetreten.

### Models-Page-Korrektur

Die letzte Korrektur betraf ausschließlich `tests/browser/test_models_page.py` und ist test-only. Der Test leitet den aktiven Provider-Vertrag aus `.meta-config/project.yaml::ai-providers` ab (Claude, Opencode, Gemini) und nutzt Show-all/Catalog-Scope für Curated-/Provenance-Abdeckung. **Die Aussage zu fehlenden Config-, Server-, UI- oder Socket-Änderungen gilt ausschließlich für diese Models-Page-Korrektur, nicht für den gesamten dirty Working Tree.** Der Working Tree enthält weiterhin Earlier-Phase-Änderungen in `docs/ui/admin-ui.html`, `.meta-config/project.yaml`, `config/tier-presets.yaml`, `scripts/lib/model_discovery.py`, `scripts/lib/frontmatter.py`, zugehörigen Tests und dem Diff-Manifest.

- **Evidenz:** `/var/tmp/opencode/val/validation-report-models-page.md`
- **Models-Page-Diff:** `/var/tmp/opencode/val/models_page.diff`
- **Aktiver Providervertrag:** `/var/tmp/opencode/val/cfg.txt`

Der Projekt-Hash war vor und nach den Browser-Läufen stabil:

- `/var/tmp/opencode/am-verify/hash-before.txt`
- `/var/tmp/opencode/am-verify/hash-final.txt`
- `/var/tmp/opencode/am-testrun/03a-config-before.log`
- `/var/tmp/opencode/am-testrun/03b-config-after.log`

### Validierung und Dry-Run

**Befehl:** `python3 scripts/sync.py --validate --dry-run`

- **Exit-Code:** 0
- **Schreibvorgänge:** keine
- **Sync errors:** keine
- **Follow-up-Warnungen:** bestehende Befunde, kein Task-17-Hard-Gate:
  - 1 Versionsformat-Warnung (`agent-meta-version`)
  - 85 Consistency Findings: 82 `placeholders.unknown`, 3 `crossrefs.changelog-missing-entry`
  - 1 `repo-containment.no-hook-support` für Provider `Opencode`
  - **Beobachtete Summe:** 87

**Evidenz:**

- `/var/tmp/opencode/val/syncvalidate.log`
- `/var/tmp/opencode/am-testrun/11-sync-summary.log`

### Socket-free Verifikationsprofil

Der finale Lauf verwendete `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; der normale Plugin-Autoload wurde nicht als Verifikationslauf ausgeführt. Die Playwright-Runtime war extern:

- **Playwright:** 1.62.0
- **Chromium/Chrome for Testing:** 151.0.7922.34
- **Browser-Pfad:** `/var/tmp/opencode/ms-playwright`
- **Evidenz:** `/var/tmp/opencode/runtime-final.txt`, `/var/tmp/opencode/val/validation-report-models-page.md`

Es gibt keine committed Repository-Socket-Umgehung; `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` ist eine Verifikationsumgebung, kein Repository-Workaround.

## A7

**A7: PASSED.**

Alle neun Provider besitzen unverändert `route_intent_tool=False`:

| Provider | Beobachtung | Fundstelle |
|---|---|---|
| Claude | `route_intent_tool=False` | `config/provider-capabilities.yaml:69` |
| Opencode | `route_intent_tool=False` | `config/provider-capabilities.yaml:89` |
| Gemini | `route_intent_tool=False` | `config/provider-capabilities.yaml:109` |
| Continue | `route_intent_tool=False` | `config/provider-capabilities.yaml:135` |
| Copilot | `route_intent_tool=False` | `config/provider-capabilities.yaml:158` |
| Mammouth | `route_intent_tool=False` | `config/provider-capabilities.yaml:188` |
| Codex | `route_intent_tool=False` | `config/provider-capabilities.yaml:222` |
| ZCode | `route_intent_tool=False` | `config/provider-capabilities.yaml:253` |
| KimiCode | `route_intent_tool=False` | `config/provider-capabilities.yaml:284` |

Der Vergleich mit Baseline `9c020125` ergab für jeden Provider `added=[]` und `removed=[]`; Provider-Set und Capability-Matrix blieben unverändert. Der Fallback-Zweig ist vorhanden:

- `agents/1-generic/orchestrator.md:92-98`: `ROUTE_INTENT_CALLABLE`-`if`/`else`
- `scripts/lib/agent_sync.py:473`: Verdrahtung
- `scripts/lib/delegation_syntax.py:553-562`: Fail-safe-Getter

**Capability-Diff-Evidenz:** `/var/tmp/opencode/task17-verification/a7-capability-key-diff.txt`

## B2/B3 Gate Evidence

**Fokussiertes B2/B3-Gate: bestanden.**

- **Befehl:** `python3 -m pytest tests/test_snippet_copy_contract.py tests/test_template_slimming_equivalence.py -q`
- **Ergebnis:** 19 passed, Exit 0
- **Evidenz:** `/var/tmp/opencode/am-testrun/02-slimming.log`
- **Copy-/Snippet-Nachweis:** 3 Block-Snippets und 2 synthetische Copy-Pfade in `tests/test_snippet_copy_contract.py:46-58`

## Informational Metrics

Die Reduktionsmetriken und der beobachtete Skip-Count sind keine zusätzlichen Hard-Gates. Der finale Lauf beobachtete **2 skipped**; beide sind bestehende, datenabhängige Browser-Guards. Collection failures wären Hard-Gate-Fehler; im finalen Lauf wurden keine Collection failures beobachtet.

**Evidenzquellen:**

- `/var/tmp/opencode/task17-verification/informational-metrics.txt`
- `/var/tmp/opencode/task17-verification/reduction-metrics-freeze-ref.txt`
- `/var/tmp/opencode/task17-verification/reduction-metrics-by-layer.txt`

- **Templates:** 101 insgesamt — 83 generic, 18 platform.
- **Golden roles:** 58.
- **Registry-Pfade:** 21 `anti-recursion`, 48 `output-guard`, 39 `parse-input`; Union 74.
- **Varianten:** 28 insgesamt — Verteilung 13/6/9 nach Art; 2 B2a, 26 B2b; 5 passthrough; 52 Pfad-Referenzen, davon 48 eindeutig.
- **Reduktion gegen Freeze-Ref `62876f49`:** 14,890 → 14,576 Zeilen (−314, 2.11 %); 707,843 → 680,242 Bytes (−27,601, 3.90 %).
- **Layer:** `1-generic` −309 Zeilen/−27,144 Bytes; `2-platform` −5 Zeilen/−457 Bytes.

## Blockers

**Keine Task-17-Hard-Gate-Blocker.** A7, B2/B3, B4 und der vollständige Browser-/Modell-Nachweis sind grün. Die 2 Skips sind bestehende Daten-Guards, nicht Blocker. Sync-Warnungen sind Follow-ups.

### Optionale, nicht blockierende Follow-ups

1. Sync-Warnungen: Versionsformat, 82 unbekannte Platzhalter, 3 fehlende Changelog-Einträge und `repo-containment.no-hook-support` für Opencode.
2. Qualitätsbeobachtungen aus dem Models-Page-Review: ungenutztes `model_count`, veralteter Testname, fehlendes Settle nach Provider-Auswahl und die dokumentierte Helper-/UI-Divergenz.
3. Optionale Commit-Hygiene: Working-Tree-Änderungen nach dem vorgeschriebenen Ledger-/Commit-Schritt trennen.

## Superseded Prior Evidence

Die folgenden früheren Beobachtungen bleiben zur Nachvollziehbarkeit erhalten, sind aber nicht aktuelle Blocker:

- `/var/tmp/opencode/agent-meta-test-executor-20260925/first/` und `/force/` — vorherige Läufe mit Model-/Browser-Blockern.
- Früherer B2/B3-Fehlschlag: `test_golden_equivalence_and_normalization_marking` durch den persistierten E2E-Marker; nach Marker-Entfernung und aktueller Equivalence-Korrektur behoben.
- `/var/tmp/opencode/task17-verification/pytest-full-rerun.log` mit `.meta` und `pytest-rerun-analysis.txt` — Auto-Commit-Blocker vor dessen Behebung.
- `/var/tmp/opencode/am-test-executor-task17/logs/01-full-suite.log` — vorheriger Lauf mit Golden-/E2E-Marker und 35 Socket-Fixture-Fehlern.
- `/var/tmp/opencode/agent-meta-test-executor-20260925/second/` — ungültige `--disable-socket`-Optionsprobe.

## Decision

**PASSED / VERIFIED.**

- A7: 14 passed, Exit 0; neun Provider unverändert `route_intent_tool=False`, kein Capability-Key-Delta.
- B2/B3: 19 passed, Exit 0.
- Model-Discovery: 34 passed, Exit 0.
- Browser-Fokus: 8 passed, Exit 0; vollständiger Browser-Satz 38 passed, 2 bestehende Skips, Exit 0.
- Vollständige Suite: 3154 passed, 2 bestehende Skips, 102 Warnings, 11 Subtests, Exit 0.
- Sync-Dry-Run: Exit 0, keine Schreibvorgänge, keine Sync errors; bestehende Warnungen bleiben Follow-ups.
- **Task 17 ist damit eligible für den vorgeschriebenen Ledger-Writer.** Der Report nimmt selbst keine Plan-/Ledger-Änderung vor; Task 17 bleibt bis dahin uncompleted.

## Next Actions

1. Den separaten Ledger-Writer die geprüfte Evidenz und den PASSED/VERIFIED-Status übergeben; Plan und Ledger nicht in diesem Dispatch ändern.
2. Die nicht blockierenden Sync-Warnungen und Models-Page-Qualitätsbeobachtungen als optionale Follow-ups erfassen.
3. Falls ein normaler Plugin-Autoload-Profil-Lauf zusätzlich gewünscht wird, ihn separat beauftragen und als eigenen Evidenzstand dokumentieren; der vorliegende PASSED-Nachweis basiert ausdrücklich auf `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.
