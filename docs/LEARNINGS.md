# LEARNINGS.md — Cross-Plugin Lessons Learned

> This file lives in the meta-repo and aggregates lessons from bugs, incidents, and discoveries across all plugins.

## Format

Use `.agent-meta/templates/learning-capture.md` for new entries.

---

## BUG-001: Mediasoup announcedAddress must match Docker host IP

**Context:** sharkord-vid-with-friends — voice channel initialization  
**Problem:** Mediasoup transport creation failed silently because `announcedAddress` was set to `127.0.0.1` inside Docker  
**Solution:** Use `HOST_LAN_IP` env variable in `docker-compose.dev.yml`; never hardcode `127.0.0.1` for WebRTC  
**Applies to:** ALL Sharkord plugins using voice/streaming  
**Date:** 2026-05-14  
**Source:** vid-with-friends@a1b2c3d

---

## DISCOVERY-001: Timestamp builds vs. 1:1 copy builds

**Context:** Release process for vid-with-friends vs. hero-introducer  
**Problem:** Inconsistent build outputs across plugins made automated release verification difficult  
**Solution:** Standardized two build variants (Variant A: Timestamp, Variant B: 1:1 Copy) with clear decision criteria  
**Applies to:** ALL Sharkord plugins  
**Date:** 2026-05-14  
**Source:** sharkord-release.md v1.3.2

---

## DISCOVERY-002: Provider-Configs können implizite Verzeichnisse haben

**Context:** agent-meta sync.py — `clean_generated_files()` in `scripts/lib/io.py`
**Problem:** Provider-Configs wie Claude haben keine expliziten `rules_dir`/`hooks_dir`/`commands_dir` Keys. Der Sync-Code nutzt Fallback-Defaults (`has_rules` Flag + Provider-Naming-Konvention `.{provider}/{dirname}`). Neue Funktionen die über Provider-Verzeichnisse iterieren MÜSSEN diese implizite Auflösung nachbilden, sonst werden Verzeichnisse übersehen.
**Solution:** `_resolve_dir()` Hilfsfunktion in `clean_generated_files()` die zuerst explizite Keys prüft, dann aus `has_*` Flags + Provider-Namen inferiert (`.{provider.lower()}/{dir_name}`). Diese Logik muss in allen neuen Funktionen repliziert werden die Provider-Verzeichnisse scannen.
**Applies to:** Alle zukünftigen sync.py-Erweiterungen die über Provider-Output-Verzeichnisse iterieren (clean, audit, migrate)
**Date:** 2026-05-17
**Source:** agent-meta@feat/super-fix-session

---

## BUG-002: Windows-Inkompatibilitäten in globalen Node.js CLIs (`opencode-pixel-office` v1.2.2)

**Context:** `opencode-pixel-office` — global installierte npm CLI (`bin/opencode-pixel-office.js`), ausgeführt auf Windows  
**Problem:** Drei Unix-spezifische Aufrufe scheitern auf Windows mit ENOENT:

1. **`spawn('tsx', ...)`** — `spawn()` kann Unix-Shebang-Skripte aus `node_modules/.bin/` auf Windows nicht ausführen
   - **Fix:** Plattform-Prüfung: Windows nutzt `node --import <tsx/dist/loader.mjs> server/index.ts` statt `spawn('tsx', ...)`. Fallback: `cmd /c tsx.cmd`

2. **`execSync('lsof -t -i :PORT')`** — `lsof` existiert nicht auf Windows
   - **Fix:** Neue Funktion `getPidsOnPort()`: Auf Windows `Get-NetTCPConnection -LocalPort PORT` via PowerShell. Betroffen: `stopServer`, `status`, `start` already-running-check

3. **`execSync('start URL')`** — `start` ist ein cmd.exe-Builtin, kein Binary
   - **Fix:** `execSync('start "" "URL"')` — leeres Titel-Argument ist bei URLs Pflicht

4. **Zusätzlich:** Import von `pathToFileURL` aus `node:url` für `--import` Flag benötigt

**Solution:** Alle vier Stellen plattformabhängig machen (`process.platform === 'win32'`). Import: `import { pathToFileURL } from 'node:url'`  
**Applies to:** ALLE Node.js CLIs die `spawn()`, `lsof`, oder `start` verwenden — insbesondere globale npm-Pakete mit Unix-Annahmen  
**Date:** 2026-05-19  
**Source:** opencode-pixel-office@local-fix (globales npm-Paket, noch kein Upstream-PR)  
**Follow-up:** GitHub Issue + PR an https://github.com/ddx-510/opencode-pixel-office erforderlich. Lokale Fixes werden bei `npm update -g` überschrieben.

---

*Add new learnings via PR against this file. Reference the originating plugin and commit for traceability.*

---

## DISCOVERY-003: Orchestrator-Optimierung nach Agent-Orchestration-Best-Practices

**Context:** agent-meta Orchestrator-Template v2.9.0 → v3.0.0  
**Source:** Forbes Technology Council — "Agent Orchestration: Best Practices And Pitfalls" + Multi-Agent-Design-Patterns  
**Date:** 2026-05-19

**Fünf Adaptionen implementiert:**

1. **Map-Reduce-Pattern:** Orchestrator kann jetzt unabhängige Teilaufgaben parallel an Worker delegieren und Ergebnisse aggregieren. Reduziert sequenzielle Latenz bei Splits/Analysen.

2. **Context-Management:** Regel "Übergib Workern nur das Nötigste" explizit dokumentiert. Verhindert Context Bloat — Worker bekommen nur Task + Dateipfade, nie den gesamten Session-Verlauf.

3. **Resilienz & Fehlerbehandlung:** Max. 2 Retries pro Worker, Fallback an User bei wiederholtem Scheitern. Idempotenz-Prüfung vor Retry. Validierung vor Merge/Commit.

4. **Schnell-Routing (Keyword→Agent):** Explizite Keyword-Tabelle für deterministisches Routing. Reduziert LLM-Aufrufe für triviale Routing-Entscheidungen. Confidence < 85% → Rückfrage statt Fehlrouting.

5. **Agenten-Contracts (input/output):** Optionale Felder in `role-defaults.yaml` dokumentieren Ein-/Ausgangsverträge von Agenten. Orchestrator liest diese vor erster Delegation.

**Applies to:** Alle Projekte die agent-meta Orchestrator nutzen  
**Architecture-Decision:** Keine strukturellen Änderungen an sync.py nötig — alle Optimierungen sind Template-Text. input/output-Felder sind rein dokumentarisch (keine automatisierte Validierung).

---

## DISCOVERY-004: Generischer Evaluator-Optimizer-Loop

**Context:** agent-meta v0.42.0 — Evaluator-Optimizer-Loop Feature  
**Source:** Issue #163 — Konzept für generische Generator-Evaluator-Pairs  
**Date:** 2026-05-19

**Problem:** Bisher war Quality-Loop nur als starres Developer↔Reviewer-Pattern denkbar. Nicht erweiterbar, keine konfigurierbaren Kriterien, kein generischer Ansatz.

**Lösung:** Generisches Evaluator-Optimizer-Loop-System implementiert:
- **Config-basiert:** `evaluator-optimizer:` Sektion in `.meta-config/project.yaml` mit `enabled`, `auto_approve`, und `pairs`-Array
- **6 vorkonfigurierte Pairs** (alle default `enabled: false`): developer→reviewer, requirements→reviewer, documenter→reviewer, tester→validator, developer→security-auditor, release→validator
- **Schema-Validierung:** `project-config.schema.json` erweitert um `evaluator-optimizer`-Objekt
- **Variablen-Injektion:** `build_variables()` generiert `EVALUATOR_OPTIMIZER_ENABLED`, `EVALUATOR_OPTIMIZER_AUTO_APPROVE`, `EVALUATOR_OPTIMIZER_PAIR_COUNT`, und pro Pair `EVALUATOR_OPTIMIZER_PAIR_N_GENERATOR` etc.
- **Bedingte Template-Sektionen:** `{{#if EVALUATOR_OPTIMIZER_ENABLED}}` — bei `enabled: false` KEIN Verhalten geändert
- **Evaluator-Critique-JSON:** Strukturiertes Format mit `criteria_evaluated`, `critique`-Objekt, `must_fix`, `suggestions`
- **Generator-Iteration-Mode:** Jeder Generator-Agent kann Critique-JSON verarbeiten und iterieren
- **Orchestrator-Workflow-Fork:** Iteriert über Pairs, filtert nach `modes`, führt Loop durch

**Architektur-Entscheidungen:**
1. **Bedingte Sektionen via `{{#if}}`** — Zero-Impact wenn deaktiviert
2. **JSON-basierte Critique** — maschinenlesbar, konsistent zwischen allen Evaluator-Agenten
3. **Modes-Filterung** — nicht alle Pairs triggern bei jedem Workflow-Typ
4. **max_iterations pro Pair** — Token-Kosten kontrollierbar
5. **auto_approve als globaler Fallback** — User hat letzte Entscheidung

**Applies to:** Alle Projekte die agent-meta nutzen  
**Architecture-Decision:** Keine Breaking Changes — alle neuen Sektionen sind conditional. sync.py benötigt keine strukturellen Änderungen außer `build_variables()`-Erweiterung.
