# Audit-Priorisierung agent-meta — 2026-11-14

- **Status:** Analyse (kein Beschluss)
- **Datum:** 2026-11-14
- **Quelle:** Fable-Grobaudit, nicht gegen Code vollständig verifiziert
- **Issues:** #1237–#1276 (Audit-Folgeissues), #1276 (Folge-Audit)
- **Zugehörige Berichte:** docs/analysis/2026-11-14-fable-concept-audit.md, docs/analysis/2026-11-14-fable-provider-hooks-audit.md, docs/analysis/2026-11-14-fable-viz-extensions-audit.md, docs/analysis/2026-11-14-audit-prioritization.md

Grundlage: drei Fable-Audits (`docs/analysis/2026-11-14-fable-*.md`, Abschnitte „Nicht geprüft“), Issue #1276, offene Issues #1237–#1276, Roadmap-Phasen D–I (`docs/superpowers/plans/2026-11-10-backlog-roadmap.md:145-156`), Churn 90 Tage (`origin/main`), Modulgrößen. Read-only; keine Tests/Syncs ausgeführt. **(U)** = unverifiziert.

## Messwerte (Evidenz)

- Größe: `scripts/admin-server.py` 6473 Z., `scripts/lib/context.py` 3838, `config.py` 2907, `meta_optimizer.py` 2365, `isolation.py` 2237, `sync_pipeline.py` 2114 (Issue #1273 adressiert Split).
- Churn 90 d (Commits je Datei): `CHANGELOG.md` 117, `.meta-config/generated-file-hashes.json` 92, `config.py` 63, `tests/test_opencode_v2_surface.py` 61, `tests/fixtures/ac01-baseline/hashes.json` 61, `sync_pipeline.py` 49, `context.py` 43, `admin-server.py` 41, `docs/ui/admin-ui.html` 32, `consistency/placeholders.py` 30.
- Tests: 458 Dateien, 120.928 Zeilen; 96 Dateien mit `subprocess.run/Popen`; 30 skip/xfail-Marker; 4 mit `time.sleep`; CI: `orchestration-test.yml` pytest-split-Shards, `validate.yml:75` Szenario-Job `timeout-minutes: 30`, 4 Shards.
- Supply-Chain: `requirements.txt` = nur `PyYAML>=6.0.3`; `package.json` = `@opencode-ai/models ^0.0.19`; 1 CDN-Load `mermaid@10` (Minor unpinned); Actions gemischt Tag-Pin (`checkout@v7`, `setup-python@v7`) vs. SHA-Pin; `scorecard.yml` vorhanden.
- Secrets: 20 `secrets.local`-Referenzen in `scripts/`; `admin-server.py:1482` `chmod 0o600`, Token-File-Hinweis `:1202-1217`; `.gitignore:32` schließt `secrets.local.yaml` aus.
- Admin-UI: `docs/ui/admin-ui.html` 11.558 Z., 18 `aria-/role=`-Attribute, 2 `<button>` (U: Rest vermutlich Div-Buttons).
- Doku: 348 Markdown-Dateien, 163.529 Zeilen; `docs/CODEBASE_OVERVIEW.md:3` zuletzt 2026-09-11 (2251 Z., 2 Monate alt); **admin-ui-architecture.md (unter docs/guides/) existiert nicht** — #1276 und das viz-Audit (`…-fable-viz-extensions-audit.md:177`) referenzieren eine Phantom-Datei.
- Knowledge Engine: 211 Dateien unter `knowledge/`, `knowledge/wiki/index.md` 181 Z., `log.md` 33 Z.; Code `scripts/lib/knowledge.py`.
- Fleet/A2A: nur Konzept/Plan (`docs/plans/2026-10-23-fleet-server-f1-plan.md`, `knowledge/sources/docs/concepts/a2a-handoff-protocol.md`), 36 `a2a`-Referenzen in `scripts/lib`, kein Fleet-Code.
- Eval/Token: `scripts/lib/eval_gate.py` 372 Z. (`:28` Per-Testfall bewusst aufgeschoben, Roadmap Entsch. 11 → Phase H), `scripts/run_role_routing_eval.py` 1124 Z.
- Provider: Phase G deckt Gemini/Antigravity/Opencode/Mammouth; Codex/Kimi/Copilot nicht (`ai-providers.yaml:735` `hooks_dir: .codex/hooks` ungeprüft); Windows: nur 8 `os.name/sys.platform`-Stellen in `scripts/`.

## Kandidaten-Tabelle

| # | Bereich | Warum jetzt (Evidenz) | Ertrag | Aufwand (Tok, Agent) | Überlappung | Empf. | Reihe |
|---|---|---|---|---|---|---|---|
| 1 | Test-Suite: Lauf, Dauer, Flakiness, Abdeckung admin-server/viz | 120.928 Testzeilen, 96 subprocess-Dateien, 30 skip-Marker, CI-Timeout 30 min; alle 3 Audits „Tests nicht ausgeführt“ (`concept:203`, `hooks:189`, `viz:178`) | hoch: sichert alle 40 Audit-Issues ab; findet Laufzeitfresser/Flakes | 60–90k, `test-executor` + `log-analyzer` (Durations-Report) | #1276 (1), #1240, #1237 (Baseline-Drift), #1246 | **JA jetzt** | 1 |
| 2 | Dashboard-/Admin-UI Sicherheit + Doku-Phantom | `admin-ui.html` 11.558 Z./32 Commits; `viz-report.py` 1049 Z. ohne erkennbares HTML-Escaping (U, grep leer); admin-ui-architecture.md fehlt (Ersatz: `docs/api/admin-ui-reference.md`) | hoch: XSS/Auth-Fläche, falsche Doku-Verweise | 40–60k, `code-reviewer` (+ `security-review`-Skill) | #1276 (2,3), #1272, #1271 | **JA jetzt** | 2 |
| 3 | Admin-UI Accessibility | 2 `<button>` auf 11.558 Z., 18 ARIA-Attribute | mittel: Tastatur/Screenreader; Pflicht laut ponytail-Nie-kürzen | 30–40k, `accessibility-specialist` | keine (kein Issue) | **JA jetzt** (mit #2 bündeln) | 3 |
| 4 | Doku-Wahrheitsgehalt (CODEBASE_OVERVIEW, guides, providers) | 163k Doku-Zeilen; Overview seit 2026-09-11 stale; Phantom-Guide; `use-lazy-rules.md:17` vs. #1186 (`viz:183`) | mittel-hoch: Agenten lesen Doku als Wahrheit → Fehlrouting | 50–70k, `documenter` (Diff-Liste) + `knowledge-linter`-Muster; stichprobenbasiert | #1276 (2), #1180, Phase E | **JA jetzt** (nach 1–2) | 4 |
| 5 | Baseline-/Drift-Mechanismen (Hash-Dateien, AC-01, Golden) | `generated-file-hashes.json` 92 und `ac01-baseline/hashes.json` 61 Commits in 90 d; `concept:123` fünf parallele Mechanismen | hoch: Merge-Konflikte, Rebaseline-Toil bei jedem PR | 30–40k, Fable konzeptionell (`concept-reviewer`) | #1237, #1246 — bereits als Issues | später (Issue-Umsetzung statt Audit) | 7 |
| 6 | Secrets-Handling / Validate-Escalation | 20 `secrets.local`-Stellen, chmod nur in `admin-server.py:1482`; `viz:175` Werte nicht gelesen | mittel: Leak-Risiko lokal gering (gitignored), Fehlkonfig häufiger | 20–30k, `code-reviewer` + `security-paved-roads` | #1262, #1261 | später (als Teil von #1262) | 8 |
| 7 | Supply-Chain/Dependencies | 1 Py-Dep, 1 npm-Dep, 1 CDN, Actions teils Tag-gepinnt, Scorecard aktiv | niedrig: Fläche minimal | 15k, `dependency-auditor` | keine | nein (Action-SHA-Pin als S-Issue reicht) | – |
| 8 | CI/Release-Prozess | 738 Workflow-Zeilen, Shard-Logik `orchestration-test.yml:59-73` mit Follow-up-Kommentaren; `release_checklist.py`/`release_scaffold.py` | mittel: Shard-Ungleichgewicht, Release-Gates nicht runtime-geprüft | 30–40k, `devops-engineer` | hängt an #1 (Durations) | später (nach #1) | 6 |
| 9 | Monolith-Split-Readiness (admin-server, context, sync_pipeline, cli_commands) | 6473/3838/2114/1804 Z., Churn 41/43/49/40 | hoch, aber Issue existiert | 40k, `refactoring-specialist` | #1273 deckt es | nein (Plan statt Audit) | – |
| 10 | Knowledge Engine (Wiki-Gesundheit, Phase-C-Integration) | 211 Dateien, `index.md` 181 Z., Phase-C-Design existiert; Linter-Agent vorhanden | mittel: eigener Agent macht es billig | 15–25k, `knowledge-linter` | Phase I? keine Issue-Nr. | JA (günstig, parallelisierbar) | 5 |
| 11 | Fleet/A2A | nur Konzept, kein Code | niedrig: nichts zu auditieren | – | Phase I | nein | – |
| 12 | Eval/Token-Messung | `eval_gate.py:28` Aufschub, Token-Zahlen Bytes/4-Proxy (`concept:208`) | mittel, aber vollständig in Phase H geplant | 30k, Fable | Phase H (#969, #1161, #1014…), #1244 | später (Phase H) | – |
| 13 | Codex/Kimi/Copilot/Continue-Provider-Spezifika | Phase G nennt sie nicht; `hooks_dir: .codex/hooks` ohne Evidenz; `hooks:210` Protokolle ungeprüft | mittel: stille Fehl-Deployments (vgl. #1252) | 30–40k, `copilot-expert`/Fable konzeptionell | #1252, #1248, #1257, Phase G | später (nach #1257-Epic) | 9 |
| 14 | Migrations-/Upgrade-Pfad Consumer (hacs/sharkord/homeassistant-Overrides) | `agents/2-platform/` 18 Overrides, 10 `migrat*`-Funktionen, `upgrade` 1 Ref in `cli_commands.py`; keine Upgrade-Howto in `docs/howto` | mittel-hoch: Consumer-Breaks bei Beta-Releases unsichtbar | 40–50k, Fable konzeptionell + 1 Consumer-Dry-Run | #1242 (Migration-Stages), #1269 (Extensions-Drift) | später (vor 2.0.0 GA) | 10 |
| 15 | Windows-Pfade | 8 Plattform-Checks, keine CI-Matrix auf Windows | niedrig (U: keine Windows-Nutzer bekannt) | 15k | #1276 (4) | nein, außer Nutzer meldet | – |
| 16 | Plugin-Tool-Namensauflösung ReqogniLoom | #1276 (5); braucht echten Claude-Code-Lauf mit MCP | hoch für #1261/#1264/#1265-Entscheidung | 10k, manueller Runtime-Test (kein Audit) | #1261, #1264 | JA, aber als Verifikationsschritt, nicht als Audit | 0 (Vorbedingung) |

## Top-5

1. **Test-Suite-Lauf + Laufzeit/Flakiness** — einzige Maßnahme, die alle 40 offenen Audit-Issues auf Code-Beweise stellt statt auf Docstrings; CI-Timeout 30 min und 96 subprocess-Tests sind Kostentreiber. Agent: `test-executor` (Durations), `log-analyzer`.
2. **Admin-/Dashboard-UI Sicherheit** — größte UI-Datei mit hohem Churn, Escaping (U) ungeprüft, Phantom-Doku-Referenz in #1276 korrigieren. Agent: `code-reviewer` + `security-review`-Skill.
3. **Accessibility Admin-UI** — mit #2 bündeln (gleiche Datei), eigener Spezialagent vorhanden, kein offenes Issue deckt es.
4. **Doku-Wahrheitsgehalt** — 163k Zeilen, Overview 2 Monate stale, Phantom-Guide; Agenten konsumieren Doku als Routing-Wahrheit. Stichprobe (CODEBASE_OVERVIEW, providers/, guides/) statt Volllauf.
5. **Knowledge-Engine-Lint** — billig (eigener Agent, 15–25k), ungeprüft, parallelisierbar.

Vorbedingung (Zeile 16): ReqogniLoom-Toolnamen in einem echten Lauf verifizieren (10k) — entscheidet #1261/#1264/#1265.

## Fable (konzeptionell) vs. Standard-/Spezialagent

- Fable konzeptionell: Baseline/Drift-Konsolidierung (#5), Consumer-Upgrade-Pfad (#14), Provider-Spezifika Codex/Kimi/Copilot (#13), Eval/Token (#12) — Architekturfragen, wenig Runtime.
- Spezialagent: `test-executor`/`log-analyzer` (#1), `code-reviewer` + security-Skills (#2, #6), `accessibility-specialist` (#3), `documenter` (#4), `knowledge-linter` (#10), `devops-engineer` (#8), `dependency-auditor` (#7 — nicht empfohlen).

## Nicht lohnend

- Supply-Chain (#7): 2 Abhängigkeiten, Scorecard aktiv; Action-SHA-Pin als S-Issue, kein Audit.
- Monolith-Split (#9): #1273 existiert; Audit würde Issue duplizieren.
- Fleet/A2A (#11): kein Code.
- Windows (#15): 8 Stellen, keine Nutzer-Evidenz (U).
- Eval/Token (#12) und Provider Phase-G-Themen: Roadmap-Phasen G/H decken sie; Audit vor Phasenstart wäre Doppelarbeit.

## Gesamt-Token-Schätzung Top-5

- 1: 60–90k · 2+3: 70–100k · 4: 50–70k · 5: 15–25k · Vorbedingung: 10k → **~205–295k** (ohne Fix-Umsetzung).

## Nicht geprüft / Annahmen

- Keine Tests/Syncs/Hooks ausgeführt; alle Laufzeitaussagen aus Code-Zählung.
- Escaping in `viz-report.py` nur per grep (`innerHTML|escape`) negativ geprüft — kann über andere Mechanismen erfolgen (U).
- Issue-Bodies außer #1276 nicht gelesen; Überlappung nur per Titel.
- Churn über `git log origin/main --since=90 days` inkl. Merge-Commits; Tag-Liste nicht abgefragt (Orchestrator-Guard-False-Positive bei `git tag`, vgl. #1258).
- graphify-Graph teils stale; nur zur Orientierung genutzt.

**Korrektur Phantom-Referenz:** die Datei docs/guides/admin-ui-architecture.md existiert nicht (weder #1276 noch dieses Audit hätten darauf verweisen dürfen). Die tatsächlich vorhandene Admin-UI-Doku ist `docs/api/admin-ui-reference.md` (Howto: `docs/howto/admin-ui-remote-access.md`).
