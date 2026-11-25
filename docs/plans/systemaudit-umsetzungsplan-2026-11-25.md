# Systemaudit & Umsetzungsplan — agent-meta

> Branch: `feat/provider-agnostic-sync-hooks-wave-5`  
> Stand: 2026-11-25  
> VERSION: `2.0.0`  
> Uncommittete Änderung: `opencode.json` (ReqogniLoom-MCP entfernt)

---

## 1. Ausgangslage

- Aktueller Branch ist der neueste nicht-`main` Branch (`feat/provider-agnostic-sync-hooks-wave-5`).
- Branch bearbeitet Wave 5 der Provider-agnostischen Sync-Hooks (#1248, #1269, #1086).
- Code-Review vergibt **CHANGES_REQUESTED** (Rating C) für die drei neuen/veränderten Hooks.
- Knowledge-Wiki ist strukturell aktuell (letztes Update 2026-11-21), enthält aber Widersprüche.
- Mehrere REQUIREMENTS aus `docs/REQUIREMENTS.md` sind noch offen (Commands-System, SE-Pipeline, Admin-UI, Context-Notizen).

---

## 2. Kritische Befunde (P1) — Merge-Blocker

| # | Befund | Ort | Konsequenz |
|---|---|---|---|
| 2.1 | `dod-push-check.sh` verletzt SRP massiv (~1644 Zeilen, untestbar) | `hooks/1-generic/dod-push-check.sh` | Keine gezielten Tests, hohe Regressiongefahr |
| 2.2 | `lifecycle-check.sh` erkennt Git-Befehle mit fragilen Regex | `hooks/1-generic/lifecycle-check.sh` | Falsch-Positive/-Negative möglich |
| 2.3 | `sync-on-config-change.sh` ruft `lifecycle_check.py` statt `sync.py` auf | `hooks/1-generic/sync-on-config-change.sh` | Naming/Verhalten inkonsistent |
| 2.4 | Hook-Template enthält leeren TODO-Stub | `scripts/lib/hooks.py:51` | Jeder neue Hook startet mit Copy-Paste-Code |
| 2.5 | Post-Upgrade-Cleanup fehlt | Issue #1359 | Backups/Artefakte ohne Guidance |
| 2.6 | Commands-System noch nicht umgesetzt | `docs/REQUIREMENTS.md` REQ-CMD-01..10 | Mehrere Must-Requirements offen |
| 2.7 | SE-Pipeline-Teilresultat-Protokoll & Rollentrennung offen | `docs/REQUIREMENTS.md` REQ-SE-01..13 | Keine persistente SE-Ausführung |
| 2.8 | Admin-UI Setup-Modus offen | `docs/REQUIREMENTS.md` REQ-ADM-01..03 | Server bricht ohne `project.yaml` ab |
| 2.9 | Composition-Anti-Pattern in `agents/2-platform/` | 12/17 Dateien Full-Replacement | Keine strukturelle Garantie bei Basis-Template-Änderungen |
| 2.10 | Dynamische Modellerfassung: Status-Widerspruch | `knowledge/wiki/concepts/dynamic-model-presets.md` als `planned`, Code bereits in `scripts/lib/model_discovery.py` | Inkonsistenter Projektstatus |
| 2.11 | Provider-Agnostik-Verstoß in Commands-System | `scripts/lib/commands.py:259` (`if commands_format == "continue":`) | Verstößt gegen `REQ-PROV-01` |
| 2.12 | `ARCHITECTURE.md` Header veraltet | `ARCHITECTURE.md:1-4` | Zeigt `0.92.0`, obwohl VERSION `2.0.0` |

---

## 3. Verbesserungen & Tech Debt (P2)

| # | Befund | Ort / Referenz |
|---|---|---|
| 3.1 | Konfigurierbare Merge-Policy | Issue #783 |
| 3.2 | HACS-Best-Practice-Gaps | Issue #676 |
| 3.3 | Intent-Routing: fehlende Keywords, überlappende Keywords, DE/EN-Mismatch | Issue #779 |
| 3.4 | Liveness-Verification für lange Subagent-Dispatches | Issue #681 |
| 3.5 | Fehlende Unit-Tests für neue `scripts/lib/*`-Module | 8/9 Module ohne eigenes `test_*.py` |
| 3.6 | `docs/architecture/02-sync-flow.md` veraltet | Referenziert nicht mehr existierende Config-Dateien |
| 3.7 | `config/prompt-modes.yaml` widerspricht `docs/architecture/prompt-modernization.md` | Totes Legacy-Fragment |
| 3.8 | 4 Reviewer-Templates ohne `<output_contract>` | `backend-reviewer.md`, `database-reviewer.md`, `frontend-reviewer.md`, `ui-reviewer.md` |
| 3.9 | Knowledge-Wiki-Seite `architecture.md` veraltet | `knowledge/wiki/concepts/architecture.md` (`stale-upstream`) |
| 3.10 | Kein Archivierungskonzept für `docs/plans/` | 12+ Dateien flach gemischt |
| 3.11 | Fehlende Unit-Tests für weitere `scripts/lib/*`-Module | `yaml_roundtrip.py`, `substitution.py`, `artifact_validate.py`, `analysis.py`, `settings_dirs.py` |
| 3.12 | Tote Konfiguration? | `config/provider-migrations.yaml` Verwendung unklar |

---

## 4. Strategische/Themen (P3)

| # | Befund | Referenz |
|---|---|---|
| 4.1 | `web-best-practices` Platform-Preset | Issue #679 |
| 4.2 | Cross-Cutting Literature Findings | Issue #778 |
| 4.3 | RFC Meta-Agent-Manager Framework | Issue #548 |
| 4.4 | SE-Metrics / Baseline & Change-Control | Issues #330 / #329 |
| 4.5 | SE-Cascade: reaktivieren oder archivieren | `.meta-config/project.yaml`: `systems-engineering.enabled: false` |
| 4.6 | `provider-expert`-Template-Zweck klären | Kein `role-defaults.yaml`-Eintrag |
| 4.7 | Provider Context — projektspezifische Notizen überarbeiten | `docs/REQUIREMENTS.md` REQ-CTX-01 |

---

## 5. Priorisierter Umsetzungsplan

### Phase 1: Merge-Blocker auf aktuellem Branch (Wave 5)
**Ziel:** Branch merge-fähig machen.

1. **Hooks refactoren**
   - `dod-push-check.sh` in kleine, getestete Funktionen/Module aufteilen (z. B. Parser, Policy-Engine, Reporter)
   - `lifecycle-check.sh` auf robuste Git-Command-Erkennung umstellen (z. B. Tokenizer statt Regex)
   - `sync-on-config-change.sh` korrigieren: Aufruf von `sync.py` statt `lifecycle_check.py`
2. **Hook-Template bereinigen**
   - `scripts/lib/hooks.py:51` TODO ersetzen durch sinnvolle Starter-Logik oder klare Dokumentation
3. **Provider-Agnostik-Verstoß im Commands-System fixen**
   - `scripts/lib/commands.py:259` (`if commands_format == "continue":`) durch Capability-Key ersetzen
4. **Validation & Tests**
   - `python scripts/sync.py --validate` muss sauber durchlaufen
   - Betroffene Szenarien aus `tests/scenarios/asserts/` ergänzen/ausführen
5. **Uncommittete Änderung entscheiden**
   - `opencode.json`: ReqogniLoom-Entfernung entweder committen oder reverten

### Phase 2: Offene REQUIREMENTS abarbeiten
**Ziel:** Must-Requirements schließen.

6. **Commands-System implementieren** (`REQ-CMD-01..10`)
   - `scripts/lib/commands.py` mit `collect_command_sources()` und `sync_commands_for_provider()`
   - Stale-Tracking für `.claude/commands/` und `.continue/prompts/`
   - Generischer `/doc-now`-Command
7. **Admin-UI Setup-Modus** (`REQ-ADM-01..03`)
   - `admin-server.py` ohne `project.yaml` im Wizard-Modus starten
   - 4xx-Fehler für schreibgeschützte Sections
8. **SE-Pipeline Teilresultat-Protokoll** (`REQ-SE-01..05`)
   - Atomares Schreiben in `docs/se/<projekt>/`
   - `.se-state.yaml` als Wiederaufnahme-Pointer
9. **SE-Rollentrennung** (`REQ-SE-10..13`)
   - `se-requirements` darf keine Architektur festlegen
   - `se-critic` erhält Role-Boundary-Check

### Phase 3: Tech Debt & Doku-Konsistenz
**Ziel:** Wartbarkeit und Vertrauen in die Doku erhöhen.

10. **Doku-Drift beheben**
    - `docs/architecture/02-sync-flow.md` neu schreiben
    - `config/prompt-modes.yaml` bereinigen oder korrigieren
    - `ARCHITECTURE.md` Header auf `2.0.0` aktualisieren
    - `knowledge/wiki/concepts/dynamic-model-presets.md` auf `active`/`implemented` setzen
    - `knowledge/wiki/concepts/architecture.md` aktualisieren oder als historisch markieren
11. **Composition in `agents/2-platform/` fixen**
    - 12 Full-Replacement-Dateien auf `extends`+`patches` migrieren
12. **Unit-Tests nachziehen**
    - Mindestens `hook_drift.py`, `mcp_registry.py`, `variables.py`, `agent_sync.py`
    - Zusätzlich: `yaml_roundtrip.py`, `substitution.py`, `artifact_validate.py`, `analysis.py`, `settings_dirs.py`
13. **Reviewer-Templates vervollständigen**
    - `<output_contract>` in 4 Reviewer-Templates ergänzen
14. **`docs/plans/`-Archivierungskonvention einführen**
    - Abgeschlossene Reports nach `docs/plans/archive/` verschieben
15. **Tote Konfiguration prüfen**
    - Verwendung von `config/provider-migrations.yaml` klären

### Phase 4: Bugs & Improvements
**Ziel:** Bekannte Issues und Verbesserungen angehen.

16. **Post-Upgrade-Cleanup** (#1359)
    - Leitfaden für Backup-/Artefakt-Aufräumen nach `sync.py`/`upgrade-meta` erstellen
    - Automatisches Pruning alter `.sync-backup-*`-Dateien prüfen/ergänzen
17. **Intent-Routing aufräumen** (#779)
    - `openscad-developer` in `config/routing/intents.yaml` und `role-defaults.yaml` aufnehmen
    - `provider-expert`-Orphan klären (Rolle aktivieren oder als interne Basis-Vorlage dokumentieren)
    - Überlappende Keywords identifizieren und disjunkt machen
    - Deutsch/Englisch-Mismatch in `intent_keywords` bereinigen
    - Dedizierte Tests für Intent-Routing-Tabelle ergänzen
18. **HACS-Best-Practices** (#676)
    - `runtime_data`-Muster in `hacs-developer`-Template integrieren
    - Branding-/IQS-Regeln ergänzen
    - Linting-Empfehlungen (`pylint`, `ruff`) als Snippet bereitstellen
    - Szenario-Assertions für HACS-Plattform erweitern
19. **Liveness-Verification** (#681)
    - Heartbeat/Timeout-Mechanismus für lange Subagent-Dispatches spezifizieren
    - In `orchestrator`-Template und ggf. `runtime.py` integrieren
    - Tests für Dispatch-Timeout ergänzen
20. **Merge-Policy konfigurierbar machen** (#783)
    - `project.yaml`-Schlüssel für Merge-Policy definieren (`merge.policy: rebase|squash|merge`)
    - `git`-Agent-Template und `dod-push-check.sh` entsprechend anpassen
    - Dokumentation in `docs/guides/ci/` ergänzen
21. **`web-best-practices` Platform-Preset** (#679)
    - Neues Platform-Preset unter `platform-configs/web-best-practices.yaml` anlegen
    - Rollen/Templates für Web-Stack (HTML/CSS/JS/Accessibility) ergänzen
    - Szenario für Web-Preset erstellen
22. **Cross-Cutting Literature Findings** (#778)
    - Literatur-Erkenntnisse zu generischen Agenten-Prompts in Knowledge-Wiki einpflegen
    - Ggf. Prompt-Optimierungen aus `concepts/prompt-modernization.md` ableiten
23. **Provider Context — projektspezifische Notizen** (`REQ-CTX-01`)
    - Starr generierten Hinweistext in Provider-Context-Files ersetzen
    - Externe Custom-Notiz-Dateien aus `.meta-config/notes/` via Partials einbinden
    - Migrationspfad für bestehende Projekte dokumentieren

### Phase 5: Strategische Entscheidungen
**Ziel:** Langfristige Richtung klären.

24. **SE-Cascade:** Reaktivieren vs. archivieren entscheiden
    - Kosten/Nutzen-Abwägung durch `product-manager`
    - Falls reaktivieren: `systems-engineering.enabled: true` setzen + Tests
    - Falls archivieren: `se-*`-Rollen und Doku in `docs/concepts/archive/` verschieben
25. **Meta-Agent-Manager-RFC** (#548)
    - Sammel-Issue in konkrete Sub-Issues zerlegen
    - Priorisierung mit `product-manager`
    - Proof-of-Concept für `agent-meta-manager`-Erweiterung
26. **SE-Metrics / Baseline** (#330/#329)
    - Metrik-Schema für Requirements-Traceability definieren
    - Baseline-/Change-Control-Prozess in `docs/se/` dokumentieren
27. **`provider-expert`-Template-Zweck klären**
    - Entscheidung: eigene Rolle aktivieren oder als Basis-Vorlage für `*-expert`-Rollen dokumentieren

---

## 6. Empfohlene Rollen / Subagenten

| Aufgabe | Rolle |
|---|---|
| Hooks refactoren | `senior-developer` + `tester` |
| Commands-System | `senior-developer` |
| Admin-UI Setup | `frontend-component-engineer` + `senior-developer` |
| SE-Pipeline | `concept-architect` + `senior-developer` |
| Doku-Drift / Wiki | `knowledge-gardener` + `documenter` |
| Composition-Migration | `refactoring-specialist` |
| Intent-Routing / HACS / Web-Preset | `developer` + `tester` |
| Provider Context / User Notes | `concept-architect` + `frontend-component-engineer` |
| Issue-Triage / Planung | `product-manager` + `planner` |
| Reviews | `code-reviewer` + `validator` |

---

## 7. Risiken & Abhängigkeiten

- **Blast-Radius:** `dod-push-check.sh` wird als Hook in vielen Projekten ausgeführt — Regressionen sind hochkritisch.
- **Zeitaufwand:** Phase 2 (REQUIREMENTS) ist mehrere Tage Arbeit.
- **Abhängigkeit:** SE-Cascade-Entscheidung blockiert Teile von Phase 2 und Phase 5.
- **Konfigurationsdrift:** `config/prompt-modes.yaml` vs. `prompt-modernization.md` kann Agenten-Sessions irreführen.
- **Scope-Creep:** Phase 4 enthält viele Verbesserungen (#779, #676, #681, #783, #679, #778, REQ-CTX-01) — ohne harte Priorisierung wird der Branch überladen.
- **Wissenslücken:** Mehrere Issues (#548, #330/#329, SE-Cascade) erfordern Produktentscheidungen, bevor sie umgesetzt werden können.
- **Uncommittete Änderung:** `opencode.json` muss vor weiteren Commits aufgelöst werden.

---

## 8. Sofortmaßnahmen (nächste 24h)

1. `opencode.json`-Änderung committen oder reverten.
2. `python scripts/sync.py --validate` laufen lassen und Fehler fixen.
3. `dod-push-check.sh`, `lifecycle-check.sh`, `sync-on-config-change.sh` bereinigen.
4. Code-Review-Befunde als Checkliste in den Branch-PR übernehmen.
5. Diesen Plan im Team absprechen / approven.
