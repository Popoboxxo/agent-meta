# Implementation Plan: #540 Context-File-Overhead Compression

> Refs #540, #192, #457 · Paper: arXiv:2602.11988 · Status: geplant

## 1. Ist-Analyse

Gemessen auf main (4f86c4b):

| Artefakt | Größe | Paper-Bewertung |
|---|---|---|
| AGENTS.md | 1082 Zeilen / 44 KB | Deutlich über Issue-Schätzung (860+) — Drift seit RFC bestätigt auch #457 |
| CLAUDE.md | 151 Zeilen / 5 KB | Bereits schlank |
| Embedded Rules Block (~Z90–239) | ~150 Zeilen | Instruktionen = Gold, aber nicht alle brauchen Always-On |
| Projekt-Overviews (Z1–89) | Architektur-Baum, Tech-Stack, Build | Paper: nutzlos (via ls/find discoverable) |
| Dev-Conventions (Z240–397) | ~158 Zeilen | Referenz-Doku, kein Runtime-Bedarf |
| sync.py Interface (Z398–513) | ~116 Zeilen inkl. Feature-Changelog | Changelog-Charakter = Ballast |
| MCP-Sektionen | ~250 Zeilen (reqogniloom allein 101) | Verbotslisten behalten, Verbindungsdetails raus |
| Agent Directory | 53 Einträge | Beschreibungen → 1–3 Keywords oder streichen |

Wichtigster Befund: Phase 2 aus #192 (embed:false) ist bereits implementiert — config/rules-presets.yaml kennt embed:false, alwaysApply:false und channel:skill (echter Lazy-Kanal). Das Repo läuft auf dem lazy-Preset. Was fehlt: die Fläche außerhalb der Rules (Partials, Agent Directory, Overviews, MCP-Sektionen).

Technische Angriffspunkte:
- templates/context/partials/ — 7 Partials (agents-location, agents-table, header, knowledge-engine-hints, project-metadata, rules-embedded, rules-pointer)
- scripts/lib/context_templates/builder.py — Partial-/Loop-/Conditional-Auflösung
- scripts/lib/context.py — Managed-Block-Zusammensetzung
- config/rules-presets.yaml — Presets existieren, kein Preset ist Default

Fix 4 (Routing) ist ein Verifikations-No-Op: Intent-Routing-Tabellen sind bereits entfernt (nur Einzeiler-Referenz AI ROUTING, CLAUDE.md Z109) — Issue-Ist-Beschreibung überholt.

Paper-Kernerkenntnisse (arXiv:2602.11988): Context-Files verbessern Success Rate nicht (p=0.87 SWE-Bench); LLM-generierte Files verschlechtern Performance in 5/8 Settings; Kosten +~20%; Repository-Overviews nutzlos; Instruktionen wirken (uv 1.6x vs 0.01x); Dev-written > LLM-generated (p=0.038).

## 2. Spezifikation

Zielregel: Discoverable via ls/find/Read → raus aus dem Context-File. Instruktion/Konvention → drin bleiben (oder lazy laden).

| Metrik | Ist | Soll |
|---|---|---|
| AGENTS.md Zeilen | 1082 | <200 inkl. B6; <400 als Zwischenziel falls B6 entfällt |
| Token-Last pro Run | ~11k Tokens | <2k Tokens |
| Accuracy | Baseline | keine Regression |

Rechnung: Ohne B6 bleibt der Bootstrap-Block (~180 Zeilen) bestehen. Zusammen mit ~150 Zeilen Embedded Rules und dem Rest (MCP, Directory kompakt, Metadaten) landet das Ergebnis bei ≈ >400 Zeilen — <200 ist nur MIT B6 erreichbar. Daher: <200 als Ziel inkl. B6, <400 als Zwischenziel falls B6 entfällt.

### Akzeptanzkriterien je Fix

Fix 1 (P0): AGENTS.md <200 Zeilen
1. Overviews (header.md Architektur-Baum, agents-location.md Directory-Tabelle) per Config abschaltbar
2. Agent Directory: name + max. 3 Keywords statt Full-Description (53 Einträge; Leerzeilen-Trennung mitentfernen halbiert zusätzlich)
3. MCP-Sektionen komprimiert: nur Tool-Listen (erlaubt/verboten), keine Agent-Hinweise-Prosa, keine Verbindungsdetails

Fix 2 (P0): Instruktions-Filter
1. Entscheidungsmatrix im Template-Header jedes Partials dokumentiert
2. project-metadata.md: Tech-Stack/Build nur wenn nicht discoverable
3. Konsistenz-Check warnt wenn generierter Context-Block >250 Zeilen ohne compact-Freigabe

Fix 3 (P1): sync.py Defaults
1. Neuer Key context_file.mode: full | compact (Default künftig compact)
2. build_variables() leitet explizit Boolean COMPACT_MODE aus context_file.mode ab (true nur bei mode: compact); B2 nutzt {{#if COMPACT_MODE}}
3. Fail-Richtung dokumentieren: fehlender Key muss zu FULL führen (Default safe-side), nicht Compact
4. Generiertes Agent-Frontmatter bleibt minimal (name, model, tools) — verifizieren
5. context-hashes.json-Mechanik unverändert

Fix 4 (P1): Routing aus Context-File — Verifikations-No-Op
1. Ist: Intent-Routing-Tabellen sind bereits entfernt (nur Einzeiler-Referenz AI ROUTING, CLAUDE.md Z109) — Issue-Ist-Beschreibung überholt; kein Code-Change nötig
2. Fix 4 bleibt als reiner Verifikationsschritt in Phase D

Fix 5 (P2): Auto-Generation-Default
1. context_file.auto_generate Default false für neue Projekte (howto/configs/project.yaml.example)
2. Bestehende Projekte: Migration-Hinweis, kein Breaking Change

Non-Goals: Phase 3 (#192: Result Caching/Batching/Pooling), #395 Headroom-Runtime-Kompression, Referenzdoku-Body-Umzug (Dev-Conventions, Sync-Interface: „nur Pointer, Body lazy als Rule/Skill") = #192 Phase 2 Territorium (channel:skill-Umzug), keine Semantik-Änderungen an Rules-Inhalten (nur Location/Dichte).

## 3. Detaillierter Plan

Reihenfolge: A → C1 → B → C → D (C1 vor B2, damit der Compact-Path sofort testbar ist).

### Phase A — Vorbereitung (P0, ~0,5 Tag)

| # | Task | Files |
|---|---|---|
| A1 | Branch feat/context-compression (Branch-Guard) | — |
| A2 | Token-Baseline messen: alle 6 Provider-Contextfiles, Skript scripts/measure_context.py (Zeilen + approx. Tokens) | neu |
| A3 | Partial-Inventory: jede Quelle des Managed Blocks klassifizieren (Instruktion/Overview/Metadaten) | docs/guides/ |

### Phase C1 — Config-Key zuerst (P1, zieht vor B2)

| # | Task | Files |
|---|---|---|
| C1 | context_file.mode + Schema-Enum | .meta-config/project.yaml-Schema, config/project-config.schema.json |

### Phase B — Partials komprimieren (P0, ~1 Tag)

| # | Task | Files |
|---|---|---|
| B1 | agents-table.md: Description → Keywords | templates/context/partials/agents-table.md, ggf. builder.py |
| B2 | Conditional {{#if COMPACT_MODE}} im Builder; Overviews nur bei mode:full | context_templates/builder.py, partials/header.md |
| B3 | MCP-Sektionen listen-only (Agent-Hinweise → 1 Zeile) | scripts/lib/mcp.py, Templates |
| B4 | build_variables() leitet explizit Boolean COMPACT_MODE aus context_file.mode ab (true nur bei mode: compact; fehlender Key → FULL, safe-side) | scripts/lib/config.py |
| B5 | Version-Bumps nach Change-Checkliste (AGENTS.md) | Frontmatter |
| B6 | Bootstrap-Block komprimieren — die ~180-zeilige Gemini-Registrierungsprosa (AGENTS.md Z902–1082) auf Kurzform reduzieren (‚Lies alle .md in .gemini/agents/ und registriere sie'), die explizite 53-fache Agentenliste streichen | scripts/lib/bootstrap.py (managed-agents-Block, Z136ff) |
| B8 | Knowledge-Engine-Hints + graphify-Sektion nach Zielregel prüfen/komprimieren (discoverable → raus) | templates/context/partials/knowledge-engine-hints.md, External-Tool-Sektion |

### Phase C — Restliche Defaults (P1, ~0,5 Tag)

| # | Task | Files |
|---|---|---|
| C2 | Konsistenz-Warnung >250 Zeilen ohne Freigabe | scripts/lib/consistency/ |
| C3 | auto_generate: false für neue Projekte; Preset-Doku in project.yaml.example ist veraltet (Z52ff: nur default/minimal/silent, lazy fehlt) — im selben Zug fixen | howto/configs/project.yaml.example |
| C4 | CLAUDE.md-Variablen-Doku (generiert, via sync.py) | CLAUDE.md |

### Phase D — Validierung (P0, ~0,5 Tag)

| # | Task | Methode |
|---|---|---|
| D1 | python scripts/sync.py --validate grün | Test-Suite |
| D2 | Vorher/Nachher-Token-Report | Skript aus A2 |
| D3 | Regressionstest: Pflicht-Instruktionen erhalten (CRITICAL GATE, Branch-Guard, Commit-Conventions, MCP-Prohibitions, Sprachregeln) | Grep-Assert in tests/ |
| D3a | Idempotenz-Test: bei mode:full muss der Output byte-identisch zum heutigen sein (anschlussfähig an tests/test_context_agents_md_idempotency.py falls vorhanden) | Test-Suite |
| D3b | Provider-Matrix-Test Claude×Opencode für Compact×Full | Test-Suite |
| D4 | Smoke-Test Konsumentenprojekt (Sync-Lauf, Agent-Session, Routing) | manuell |
| D5 | Kommentar auf #192 mit Ergebnis, Querverweis #457 | gh issue comment |

## 4. Risiken & Gegenmaßnahmen

| Risiko | Gegenmaßnahme |
|---|---|
| Kritische Regel versehentlich raus-komprimiert | D3-Checkliste als automatisierter Test (Fail bei fehlendem Pflicht-Anchor) |
| Instruction Bleed durch Composition der komprimierten Partials | Bleed-Checkliste vor Patch-Commit; Overrides nur replace, keine additiven Appends auf geänderte Sections |
| Konsumenten mit eigenem rules:-Override brechen | mode:full als Fallback; Migration-Hinweis in Release Notes |
| Opencode has_rules:false → braucht Embedding | Compact-Mode respektiert Provider-Caps (analog channel:skill in skill_channel.py PROVIDERS) — Opencode kriegt kompakte Embeds statt Separation |
| Erster Sync nach Umschaltung kann flächig context-hashes Backup-Warnungen auslösen (Drift-Erkennung in context.py) | Migration-Hinweis in Release Notes verweist explizit darauf |

## 5. Abhängigkeiten

A (Baseline) → C1 (mode-Key) → B (Partials) → C (Defaults) → D (Validierung)
