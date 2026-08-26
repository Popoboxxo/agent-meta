# Issue #540 — Context-Baseline (Phase A2)

> Vor-Komprimierung-Messung als Referenz für Phase D2 (Vorher/Nachher-Report).
> Gemessen mit `python3 scripts/measure_context.py` (Tokens approximiert als Bytes/4).

## Messung

| Metadatum | Wert |
|---|---|
| Datum | 2026-08-25 |
| Commit | `1538c887541a59122b22ccfc11dbbaa88882d512` (`feat/context-compression`) |
| Skript | `scripts/measure_context.py` |

| Datei | Zeilen | Bytes | Tokens (~) |
|---|---:|---:|---:|
| CLAUDE.md | 151 | 5437 | 1359 |
| AGENTS.md | 1082 | 44004 | 11001 |
| MAMMOUTH.md | 173 | 10378 | 2594 |
| **TOTAL** | **1406** | **59819** | **14954** |

Nicht vorhandene Provider-Contextfiles (`.continue/rules/project-context.md`, `.github/copilot/COPILOT.md`) werden vom Skript übersprungen. GEMINI.md existiert in diesem Repo nicht — Gemini teilt sich AGENTS.md.

## AGENTS.md Sektions-Gliederung (Ist)

Zeilenbereiche zum Vergleich nach Phase B (Details und Klassifizierung: `docs/guides/context-block-inventory.md`):

| Bereich | Zeilen | Quelle | Kategorie |
|---|---|---|---|
| Z1–79 Projekt-Overviews | ~79 | `templates/context/partials/project-metadata.md` | OVERVIEW/METADATEN |
| Z81–87 Managed-Header (ROUTING/ENTRY/Version) | ~7 | `templates/context/partials/header.md` | METADATEN |
| Z90–239 Embedded Rules (14 Generic-Rules) | ~150 | `rules/1-generic/*.md` via `rules-embedded.md` | INSTRUKTION |
| Z240–397 Platform-Rules (Schichten, Conventions, Provider-Agnostic) | ~158 | `rules/2-platform/agent-meta-*.md` | gemischt (siehe Inventory) |
| Z398–513 sync.py Interface | ~116 | `rules/2-platform/agent-meta-sync-interface.md` | OVERVIEW |
| Z514–730 MCP-Sektionen (4 Server) | ~217 | generiert aus `config/mcp-registry.yaml` (`scripts/lib/mcp.py`) | INSTRUKTION + OVERVIEW + METADATEN |
| Z731–758 External Tool graphify | ~28 | generiert aus `config/external-tools-registry.yaml` | INSTRUKTION + METADATEN |
| Z760–871 Agent Directory (53 Einträge) | ~112 | `agents-location.md` + `agents-table.md` | OVERVIEW |
| Z873–894 Knowledge Engine | ~22 | `knowledge-engine-hints.md` | METADATEN/OVERVIEW |
| Z902–1025 Bootstrap-Block (Gemini) | ~124 | `scripts/lib/bootstrap.py` (`generate_gemini_bootstrap_instructions`) | OVERVIEW (Kern-Instruktion erhalten) |
| Z1028–1082 RTK/graphify-Fremdinjektionen | ~55 | Drittanbieter-Installer (nicht sync.py) | außerhalb Scope |

## Plan-Soll (Referenz)

| Metrik | Ist | Soll |
|---|---:|---|
| AGENTS.md Zeilen | 1082 | <200 inkl. B6; <400 Zwischenziel ohne B6 |
| Token-Last pro Run (AGENTS.md) | ~11k | <2k |

## Nachher (Phase D2)

### Default/full-Modus

Gemessen am 2026-08-25 auf `feat/context-compression` @ `6ea6a8a8` nach Phase A/C1/B/C.
Der Default ist `full` (fehlender `context_file.mode`-Key → safe-side FULL), daher
ist der Output byte-identisch zur Vorher-Messung — erwartungsgemäß keine Differenz:

| Datei | Zeilen | Bytes | Tokens (~) | Δ vs. Vorher |
|---|---:|---:|---:|---|
| CLAUDE.md | 151 | 5437 | 1359 | ±0 |
| AGENTS.md | 1082 | 44004 | 11001 | ±0 |
| MAMMOUTH.md | 173 | 10378 | 2594 | ±0 |
| **TOTAL** | **1406** | **59819** | **14954** | **±0** |

### compact-Modus — Iteration 1 (Phase B, nur Nicht-Rules-Fläche)

Einmalig real gemessen: temporär `context_file.mode: compact` gesetzt, `sync.py`
gelaufen, gemessen, zurückgesetzt (Working Tree danach wieder clean).
Ergebnis aus den B-Ergebnissen (**AGENTS.md ≈779 Zeilen**):

| Datei | Zeilen | Bytes | Tokens (~) | Δ Zeilen | Δ Tokens (~) |
|---|---:|---:|---:|---:|---:|
| CLAUDE.md | 100 | 4165 | 1041 | −34% | −23% |
| AGENTS.md | 779 | 31681 | 7920 | −28% | −28% |
| MAMMOUTH.md | 122 | 9106 | 2276 | −29% | −12% |
| **TOTAL** | **1001** | **44952** | **11237** | **−28,8%** | **−24,9%** |

Iteration 1 fasste die als OVERVIEW klassifizierten Platform-Rules
(`sync-interface`, `architecture`, `conventions`) noch NICHT an — sie wurden als
„#192 Phase-2-Territorium" zurückgestellt. Damit wurde das Plan-Soll (<200/<400)
verfehlt.

### compact-Modus — Iteration 2 (nach Einbeziehung #192-Phase-2-Territorium, Nutzer-Entscheidung)

Auf ausdrückliche Nutzer-Entscheidung wurde die zurückgestellte OVERVIEW-Fläche
der drei agent-meta-Platform-Rules jetzt einbezogen — **dichte-only**: nur die
bereits als OVERVIEW klassifizierten Sektionen (Schichten-Modell, Composition-
Syntax, Platzhalter-Escape, Smart-Context-Changelog, Naming/Bleed/Change-
Checklists) werden im Embed durch einen Pointer ersetzt; alle INSTRUKTION-Anteile
(Hard Invariants, Branch-Guard-Erweiterung, Abhängigkeitsprinzip) bleiben in
BEIDEN Modi verbatim. Compact ist jetzt im Repo aktiv committet (nicht nur die
Config — der generierte Output liegt mit im Commit):

| Datei | Zeilen | Bytes | Tokens (~) | Δ Zeilen vs. voll | Δ Tokens vs. voll |
|---|---:|---:|---:|---:|---:|
| CLAUDE.md | 100 | 4165 | 1041 | −34% | −23% |
| AGENTS.md | 570 | 23751 | 5937 | −47% | −46% |
| MAMMOUTH.md | 122 | 9106 | 2276 | −29% | −12% |
| **TOTAL** | **792** | **37022** | **9254** | **−44%** | **−38%** |

**Wurde `<200`/`<400` erreicht? Nein — ehrliche Begründung (kein Ziel-Retrofit):**

AGENTS.md hat einen harten Floor von **~570 Zeilen**, der NICHT weiter senkbar
ist ohne Instruktions-Verlust:

- **Opencode `has_rules: false`** (`config/ai-providers.yaml`): Regeln haben bei
  Opencode keinen nativen Kanal → die 14 Generic-Rule-Bodies (~150 Z, alle
  INSTRUKTION) MÜSSEN embedded in AGENTS.md bleiben.
- **MCP-Tool-Listen** (Erlaubt/Verboten, reqogniloom allein ~77 Z) sind
  INSTRUKTION (Allow/Deny-Listen steuern Tool-Nutzung) → bleiben.
- Zusammen ~300 Zeilen reine INSTRUKTION + Agent-Directory (60, dichte
  Keyword-Zeilen, routing-relevant) + Bootstrap-Kern + Projekt-Metadaten.

Die Plan-Streckziele `<200` (inkl. B6) und `<400` setzten implizit voraus, dass
die embedded Rules verschwinden könnten — das ist bei einem `has_rules:false`-
Provider architekturell ausgeschlossen. Für die `has_rules:true`-Provider
(Claude/Continue/Copilot/Mammouth) liegen die Regeln nativ/lazy und CLAUDE.md
erreicht bereits 100 Zeilen. Der ehrliche Endstand: **AGENTS.md 570 (−47%)**,
Test-Schwelle in `tests/test_context_compact_mode.py` auf diesen gemessenen
Floor gesetzt (relativ zum Full-Render, mit Begründungs-Kommentar), NICHT ans
Ergebnis geschönt.

### Provider-Matrix (Iteration 2, alle 6 Provider real gerendert)

`config/ai-providers.yaml` kennt 6 Provider. Compact wurde für JEDEN real
gerendert (Test: `test_540_compact_matrix_*`, auch für die in `project.yaml`
inaktiven Continue/Copilot):

| Provider | Context-File | has_rules | Compact-Wirkung | Marker-frei |
|---|---|---|---|---|
| Claude | CLAUDE.md | true | Rules nativ (`.claude/skills/*` lazy, FULL); Compact wirkt auf Directory/Knowledge-Hints | ✓ |
| Gemini | AGENTS.md (geteilt) | true→embed¹ | Rules embedded compact (3 Platform-Rules → Pointer) | ✓ |
| Opencode | AGENTS.md (geteilt) | false | Rules embedded compact — MÜSSEN embedded bleiben | ✓ |
| Continue | .continue/rules/project-context.md | true | Rules nativ (FULL); Compact wirkt auf Managed-Block-Rest | ✓ |
| Copilot | .github/copilot/COPILOT.md | true | Rules nativ (FULL); Compact wirkt auf Managed-Block-Rest | ✓ |
| Mammouth | MAMMOUTH.md | true | Rules nativ (FULL); Compact wirkt auf Rest | ✓ |

¹ Gemini `has_rules:true`, teilt sich aber AGENTS.md mit Opencode
(`has_rules:false`) → `context.py` erzwingt embed für beide (Ping-Pong-
Vermeidung). Die drei Platform-Rules bleiben für alle `has_rules:true`-Provider
in ihrem nativen Rules-/Skill-Kanal FULL — verifiziert (Test
`test_540_compact_native_rules_providers_keep_platform_rules_full`): Compaction
ist embed-only, kein Semantik-Verlust im nativen Kanal.

### D4 — Smoke-Test (committeter compact-Output)

Committete Dateien wie ein Agent gelesen: alle Pflicht-Anker auffindbar —
`CRITICAL GATE`, `# Branch-Guard`, `# Commit-Konventionen`/`Conventional
Commits`, `# Sprachregeln`, MCP-Verbote (`delete_conclusion`,
`browser_run_code_unsafe`, `workspace.delete`), `## Regeln`, `## Agent
Directory`, `orchestrator`-Routing. CLAUDE.md: `AI ROUTING`, `orchestrator`,
`Knowledge Engine`. Keine Leftover-Template-Marker in CLAUDE.md/AGENTS.md/
MAMMOUTH.md.

### Mechanismus (D-Entscheidung)

Rohe `{{#if COMPACT_MODE}}`-Marker im Rohtext einer Rule-Quelldatei funktionieren
NICHT (empirisch verifiziert): `strip_inactive_conditional_blocks`
(`scripts/lib/config.py`) verarbeitet nur eine Whitelist von Variablennamen —
`COMPACT_MODE` ist nicht dabei —, und die finale Orphan-Cleanup strippt die
Marker verbatim, sodass BEIDE Branches erhalten bleiben. Zudem läuft dieselbe
Funktion im NATIVE-Rules-Pfad (`scripts/lib/rules.py`); eine Whitelist-Erweiterung
würde native Rules für Claude/Mammouth fälschlich komprimieren. Gewählt wurde
daher eine dedizierte Transform-Funktion `compact_embedded_rule()` in
`scripts/lib/context.py`, die NUR im Embedded-Loop (Opencode/Gemini AGENTS.md)
läuft — analog zum bestehenden `compact=`-Parameter-Pattern (MCP, External-Tools,
Knowledge, Bootstrap). Sie behält Preamble + eine Allowlist von INSTRUKTION-
Sektionen verbatim und ersetzt den Rest durch einen Pointer.
