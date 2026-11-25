# Systemaudit & Umsetzungsplan — agent-meta

> Branch: `feat/provider-agnostic-sync-hooks-wave-5`  
> Stand: 2026-11-25  
> VERSION: `2.0.0`  
> Uncommitted change: `opencode.json` (ReqogniLoom-MCP entfernt)

---

## 1. Ausgangslage

- Aktueller Branch ist der neueste nicht-`main` Branch (`feat/provider-agnostic-sync-hooks-wave-5`).
- **Wave 5** = Provider-agnostische Sync-Hooks (Issues #1248, #1269, #1086).
- Code-Review für die drei neuen/veränderten Hooks vergibt **CHANGES_REQUESTED** (Rating C = mangelhafte Code-Qualität im Review-Raster) — Merge des Branches ist aktuell blockiert.
- Knowledge-Wiki ist strukturell aktuell (letztes Update 2026-11-21), enthält aber Widersprüche.
- Mehrere Must- und Should-Requirements aus `docs/REQUIREMENTS.md` sind noch offen.

---

## 2. Branch Merge-Blocker (P1 — blockiert Wave 5)

Diese Punkte müssen vor dem Merge von `feat/provider-agnostic-sync-hooks-wave-5` in `main` gelöst werden.

| # | Befund | Ort | Konsequenz |
|---|---|---|---|
| MB-1 | `dod-push-check.sh` verletzt SRP massiv (~1644 Zeilen, untestbar) | `hooks/1-generic/dod-push-check.sh` | Keine gezielten Tests, hohe Regressiongefahr |
| MB-2 | `lifecycle-check.sh` erkennt Git-Befehle mit fragilen Regex | `hooks/1-generic/lifecycle-check.sh` | Falsch-Positive/-Negative möglich |
| MB-3 | `sync-on-config-change.sh` ruft `lifecycle_check.py` statt `sync.py` auf | `hooks/1-generic/sync-on-config-change.sh` | Naming/Verhalten inkonsistent |
| MB-4 | Hook-Template enthält leeren TODO-Stub | `scripts/lib/hooks.py:51` | Jeder neue Hook startet mit Copy-Paste-Code |
| MB-5 | Provider-Agnostik-Verstoß im Commands-System | `scripts/lib/commands.py:259` (`if commands_format == "continue":`) | Verstößt gegen `REQ-PROV-01` |
| MB-6 | Uncommitted change in `opencode.json` | `opencode.json` | Muss vor Merge aufgelöst werden |

---

## 3. Offene Must-Requirements (P1 — blockiert Produkt, nicht Wave 5)

Diese Requirements sind in `docs/REQUIREMENTS.md` als Must markiert, blockieren aber nicht den aktuellen Branch. Sie werden in eigenen Epic-Branches umgesetzt.

| # | Requirement | Inhalt |
|---|---|---|
| MR-1 | `REQ-CMD-01..10` | Commands-System (Layer-Modell, Stale-Tracking, Provider-Sync) |
| MR-2 | `REQ-SE-01..13` | SE-Pipeline: Teilresultat-Protokoll, Rollentrennung |
| MR-3 | `REQ-ADM-01..03` | Admin-UI Setup-Modus |

---

## 4. Verbesserungen & Tech Debt (P2)

| # | Befund | Ort / Referenz |
|---|---|---|
| TD-1 | Composition-Anti-Pattern in `agents/2-platform/` | 12/17 Dateien Full-Replacement statt `extends`+`patches` |
| TD-2 | `docs/architecture/02-sync-flow.md` veraltet | Referenziert nicht mehr existierende Config-Dateien |
| TD-3 | `config/prompt-modes.yaml` widerspricht Doku | Existiert nicht, wird aber in Docs referenziert |
| TD-4 | `ARCHITECTURE.md` Header veraltet | Zeigt `0.92.0` statt `2.0.0` |
| TD-5 | 4 Reviewer-Templates ohne `<output_contract>` | `backend-reviewer.md`, `database-reviewer.md`, `frontend-reviewer.md`, `ui-reviewer.md` |
| TD-6 | Fehlende Unit-Tests für `scripts/lib/*`-Module | `hook_drift.py`, `mcp_registry.py`, `variables.py`, `agent_sync.py`, `yaml_roundtrip.py`, `substitution.py`, `artifact_validate.py`, `analysis.py`, `settings_dirs.py` |
| TD-7 | Knowledge-Wiki-Widersprüche | `dynamic-model-presets.md` als `planned` trotz umgesetztem Code; `architecture.md` veraltet |
| TD-8 | Kein Archivierungskonzept für `docs/plans/` | Abgeschlossene und aktive Pläne flach gemischt |
| TD-9 | Tote Konfiguration? | `config/provider-migrations.yaml` Verwendung unklar |

---

## 5. Strategische Themen & Improvements (P3)

| # | Befund | Referenz |
|---|---|---|
| ST-1 | Konfigurierbare Merge-Policy | Issue #783 |
| ST-2 | HACS-Best-Practice-Gaps | Issue #676 |
| ST-3 | Intent-Routing: fehlende Keywords, überlappende Keywords, DE/EN-Mismatch | Issue #779 |
| ST-4 | Liveness-Verification für lange Subagent-Dispatches | Issue #681 |
| ST-5 | `web-best-practices` Platform-Preset | Issue #679 |
| ST-6 | Cross-Cutting Literature Findings | Issue #778 |
| ST-7 | RFC Meta-Agent-Manager Framework | Issue #548 |
| ST-8 | SE-Metrics / Baseline & Change-Control | Issues #330 / #329 |
| ST-9 | SE-Cascade: reaktivieren oder archivieren | `.meta-config/project.yaml`: `systems-engineering.enabled: false` |
| ST-10 | Provider Context — projektspezifische Notizen überarbeiten | `REQ-CTX-01` |
| ST-11 | `provider-expert`-Template-Zweck klären | Kein `role-defaults.yaml`-Eintrag |

---

## 6. Priorisierter Umsetzungsplan

### Phase 1: Branch merge-fähig machen (Wave 5)
**Ziel:** `feat/provider-agnostic-sync-hooks-wave-5` kann in `main` gemerged werden.  
**Zeit:** S–M (1–3 Tage)  
**Exit-Kriterien:**
- `python scripts/sync.py --validate` ist grün.
- Alle MB-* aus §2 sind erledigt.
- Code-Review-Befunde sind als Checkliste im PR abgearbeitet.
- Betroffene Szenarien in `tests/scenarios/asserts/` laufen grün.

1. **Hooks refactoren**
   - `dod-push-check.sh` in kleine, getestete Funktionen/Module aufteilen (Parser, Policy-Engine, Reporter)
   - `lifecycle-check.sh` auf robuste Git-Command-Erkennung umstellen (Tokenizer statt Regex)
   - `sync-on-config-change.sh` korrigieren: Aufruf von `sync.py` statt `lifecycle_check.py`
2. **Hook-Template bereinigen**
   - `scripts/lib/hooks.py:51` TODO ersetzen durch sinnvolle Starter-Logik oder klare Dokumentation
3. **Provider-Agnostik-Verstoß fixen**
   - `scripts/lib/commands.py:259` (`if commands_format == "continue":`) durch Capability-Key ersetzen
4. **Uncommitted change auflösen**
   - `opencode.json`: ReqogniLoom-Entfernung entweder committen oder reverten
5. **Validation & Tests**
   - `python scripts/sync.py --validate` sauber durchlaufen lassen
   - Betroffene Szenarien ergänzen/ausführen

### Phase 2: Commands-System Epic
**Ziel:** `REQ-CMD-01..10` umsetzen.  
**Zeit:** L (1–2 Wochen)  
**Exit-Kriterien:**
- `scripts/lib/commands.py` implementiert und getestet.
- Stale-Tracking für `.claude/commands/` und `.continue/prompts/` funktioniert.
- `/doc-now`-Command existiert.
- Scenario-Tests für Commands-System grün.

1. `scripts/lib/commands.py` mit `collect_command_sources()` und `sync_commands_for_provider()`
2. Stale-Tracking für `.claude/commands/` und `.continue/prompts/`
3. Generischer `/doc-now`-Command
4. Dokumentation in `docs/guides/features/commands.md`
5. Projekt-spezifische Commands via `--create-command <name>`

### Phase 3: Admin-UI Setup-Modus Epic
**Ziel:** `REQ-ADM-01..03` umsetzen.  
**Zeit:** M–L (3–10 Tage)  
**Exit-Kriterien:**
- `admin-server.py` startet ohne `project.yaml` im Wizard-Modus.
- Schreibversuche auf schreibgeschützte Sections liefern 4xx.
- Erst-Instanziierung via UI funktioniert.

1. `admin-server.py` ohne `project.yaml` im Setup-Modus starten
2. Geführter Assistent für initiale `.meta-config/project.yaml`
3. `sync.py`-Erstausführung aus der UI heraus
4. 4xx-Fehlerbehandlung für schreibgeschützte Sections

### Phase 4: SE-Pipeline Epic
**Ziel:** `REQ-SE-01..13` umsetzen.  
**Zeit:** L–XL (2–4 Wochen)  
**Exit-Kriterien:**
- Teilresultat-Protokoll schreibt atomar in `docs/se/<projekt>/`.
- `.se-state.yaml` funktioniert als Wiederaufnahme-Pointer.
- `se-requirements` hält Architektur-Rollentrennung ein.
- `se-critic` führt Role-Boundary-Check durch.

1. Atomares Schreiben in `docs/se/<projekt>/`
2. `.se-state.yaml` als Wiederaufnahme-Pointer
3. Iterations-Suffix-Konvention (`*.iter-N.md`, `*.final.md`)
4. Rollentrennung Requirements vs. Architect
5. Pipeline-Trennung (optional: `REQ-SE-20..22`)

### Phase 5: Tech Debt & Doku-Konsistenz
**Ziel:** Wartbarkeit und Vertrauen in die Doku erhöhen.  
**Zeit:** M (1 Woche)  
**Exit-Kriterien:**
- Keine offenen Widersprüche zwischen Code, Config und Doku.
- Unit-Test-Abdeckung für genannte Module vorhanden.
- Composition-Migration abgeschlossen oder bewusst verschoben.

1. **Doku-Drift beheben**
   - `docs/architecture/02-sync-flow.md` neu schreiben
   - `config/prompt-modes.yaml` bereinigen oder korrigieren
   - `ARCHITECTURE.md` Header auf `2.0.0` aktualisieren
   - `knowledge/wiki/concepts/dynamic-model-presets.md` auf `active`/`implemented` setzen
   - `knowledge/wiki/concepts/architecture.md` aktualisieren oder als historisch markieren
2. **Composition in `agents/2-platform/` fixen**
   - 12 Full-Replacement-Dateien auf `extends`+`patches` migrieren
3. **Unit-Tests nachziehen**
   - Mindestens `hook_drift.py`, `mcp_registry.py`, `variables.py`, `agent_sync.py`
   - Zusätzlich: `yaml_roundtrip.py`, `substitution.py`, `artifact_validate.py`, `analysis.py`, `settings_dirs.py`
4. **Reviewer-Templates vervollständigen**
   - `<output_contract>` in 4 Reviewer-Templates ergänzen
5. **`docs/plans/`-Archivierungskonvention einführen**
   - Abgeschlossene Reports nach `docs/plans/archive/` verschieben
6. **Tote Konfiguration prüfen**
   - Verwendung von `config/provider-migrations.yaml` klären

### Phase 6: Improvements (Sub-Streams)
**Ziel:** Offene Issues und Should-Requirements angehen.  
**Zeit:** je Sub-Stream S–M  
**Exit-Kriterien pro Sub-Stream:** Issue geschlossen oder PR approved & merged.

**Priorisierung (P2 → niedrigere Prio):**
1. 6.1 Intent-Routing (#779) — betrifft alle Routings-Entscheidungen
2. 6.3 Liveness-Verification (#681) — betrifft Dispatch-Zuverlässigkeit
3. 6.2 HACS-Best-Practices (#676) — betrifft HACS-Plattform
4. 6.4 Merge-Policy (#783) — betrifft git-Rolle
5. 6.7 Provider Context — User Notes (`REQ-CTX-01`) — betrifft Context-Files
6. 6.8 Post-Upgrade-Cleanup (#1359) — betrifft Upgrade-Erfahrung
7. 6.5 Web-Best-Practices Preset (#679) — neues Platform-Preset
8. 6.6 Cross-Cutting Literature Findings (#778) — rein informativ

#### 6.1 Intent-Routing (#779)
- `openscad-developer` in `config/routing/intents.yaml` und `role-defaults.yaml` aufnehmen
- `provider-expert`-Orphan klären
- Überlappende Keywords disjunkt machen
- Deutsch/Englisch-Mismatch bereinigen
- Tests ergänzen

#### 6.2 HACS-Best-Practices (#676)
- `runtime_data`-Muster in `hacs-developer`-Template integrieren
- Branding-/IQS-Regeln ergänzen
- Linting-Empfehlungen als Snippet bereitstellen
- Szenario-Assertions erweitern

#### 6.3 Liveness-Verification (#681)
- Heartbeat/Timeout-Mechanismus für lange Subagent-Dispatches spezifizieren
- In `orchestrator`-Template und `runtime.py` integrieren
- Tests für Dispatch-Timeout ergänzen

#### 6.4 Merge-Policy (#783)
- `project.yaml`-Schlüssel für Merge-Policy definieren
- `git`-Agent-Template und `dod-push-check.sh` anpassen
- Doku in `docs/guides/ci/` ergänzen

#### 6.5 Web-Best-Practices Preset (#679)
- Neues Platform-Preset unter `platform-configs/web-best-practices.yaml`
- Rollen/Templates für Web-Stack ergänzen
- Szenario erstellen

#### 6.6 Cross-Cutting Literature Findings (#778)
- Erkenntnisse in Knowledge-Wiki einpflegen
- Ggf. Prompt-Optimierungen ableiten

#### 6.7 Provider Context — User Notes (`REQ-CTX-01`)
- Starr generierten Hinweistext ersetzen
- Externe Custom-Notiz-Dateien aus `.meta-config/notes/` via Partials einbinden
- Migrationspfad dokumentieren

#### 6.8 Post-Upgrade-Cleanup (#1359)
- Leitfaden für Backup-/Artefakt-Aufräumen erstellen
- Automatisches Pruning alter `.sync-backup-*`-Dateien prüfen

### Phase 7: Strategische Entscheidungen
**Ziel:** Langfristige Richtung klären.  
**Zeit:** n/a (Entscheidungen)  
**Exit-Kriterien:** Go/No-Go-Entscheidungen dokumentiert.

1. **SE-Cascade:** Reaktivieren vs. archivieren
   - Kosten/Nutzen-Abwägung durch `product-manager`
   - Falls reaktivieren: `systems-engineering.enabled: true` setzen + Tests
   - Falls archivieren: `se-*`-Rollen und Doku in `docs/concepts/archive/` verschieben
2. **Meta-Agent-Manager-RFC** (#548)
   - Sammel-Issue in konkrete Sub-Issues zerlegen
   - Priorisierung mit `product-manager`
   - Proof-of-Concept für `agent-meta-manager`-Erweiterung
3. **SE-Metrics / Baseline** (#330/#329)
   - Metrik-Schema für Requirements-Traceability definieren
   - Baseline-/Change-Control-Prozess in `docs/se/` dokumentieren
4. **`provider-expert`-Template-Zweck klären**
   - Entscheidung: eigene Rolle aktivieren oder als Basis-Vorlage für `*-expert`-Rollen dokumentieren

---

## 7. Out-of-Scope / Bereits umgesetzt

| Requirement | Status | Begründung |
|---|---|---|
| `REQ-MOD-01..07` | Bereits umgesetzt | Code in `scripts/lib/model_discovery.py` und `config/tier-presets.yaml`; nur Wiki-Status in Phase 5 korrigieren |
| `REQ-SYNC-01` | Bereits umgesetzt | Backup vor Sync-Overwrite existiert; Post-Upgrade-Cleanup wird in Phase 6.8 behandelt |
| `REQ-SYNC-02` | Bereits umgesetzt | Audit-Modus `--audit-config` ist read-only; ggf. Tests ergänzen |
| `REQ-GEN-01` | Bereits umgesetzt | Deprecation-Filter existiert; ggf. Tests in Phase 5 ergänzen |

---

## 8. Empfohlene Rollen / Subagenten

| Aufgabe | Rolle |
|---|---|
| Phase 1 (Hooks, Validate, opencode.json) | `senior-developer` + `tester` |
| Phase 2 (Commands-System) | `senior-developer` + `api-specialist` |
| Phase 3 (Admin-UI Setup) | `frontend-component-engineer` + `senior-developer` |
| Phase 4 (SE-Pipeline) | `concept-architect` + `senior-developer` |
| Phase 5 (Tech Debt / Doku) | `knowledge-gardener` + `documenter` + `refactoring-specialist` |
| Phase 6 (Improvements) | `developer` + `tester` |
| Phase 7 (Strategische Entscheidungen) | `product-manager` + `concept-architect` |
| Reviews | `code-reviewer` + `validator` |

---

## 9. Risiken & Abhängigkeiten

- **Blast-Radius:** `dod-push-check.sh` wird als Hook in vielen Projekten ausgeführt — Regressionen sind hochkritisch.
- **Scope-Creep:** Phase 6 enthält viele Verbesserungen — ohne harte Priorisierung wird der Branch überladen.
- **Wissenslücken:** Mehrere Issues (#548, #330/#329, SE-Cascade) erfordern Produktentscheidungen, bevor sie umgesetzt werden können.
- **Konfigurationsdrift:** `config/prompt-modes.yaml` vs. `prompt-modernization.md` kann Agenten-Sessions irreführen.
- **Uncommitted change:** `opencode.json` muss vor dem Merge von Phase 1 aufgelöst werden.
- **Test-Infrastruktur:** Neue Unit-Tests und Szenarien setzen voraus, dass der Test-Harness stabil läuft (aktuell: `tests/scenarios/run.sh` + pytest).
- **Ressourcen:** Phasen 2–4 sind mehrwöchige Epics; ohne klare Zuordnung droht Verzug.

---

## 10. Sofortmaßnahmen (nächste 24h)

1. `opencode.json`-Änderung committen oder reverten.
2. `python scripts/sync.py --validate` laufen lassen und Fehler fixen.
3. `dod-push-check.sh`, `lifecycle-check.sh`, `sync-on-config-change.sh` bereinigen.
4. Code-Review-Befunde als Checkliste in den Branch-PR übernehmen.
5. Phase 1 an `senior-developer` + `tester` delegieren.
