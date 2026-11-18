---
pipeline_stages:
  implement: 1
status: geplant
date: 2026-11-18
spec: docs/plans/2026-11-18-1300-speech-mode-embed-channel.md
spec-status: APPROVED
klasse: M (Architectural nach F7)
branch: fix/1300-speech-mode-embed
---

# Speech-Mode Embed-Kanal für has_rules:false-Provider — Spec + Plan

> Status: APPROVED
> Kombiniertes Dokument: Teil A = Spec, Teil B = Plan. Plan erst nach `Status: APPROVED` (nur der Nutzer gibt frei) ausführbar.

# Teil A — Spec

## Problem / Ziel / Nicht-Ziele

**Problem (Issue #1300):** `speech-mode` (z.B. `caveman`) wird für Provider mit `has_rules: false` (Opencode, mammouth) still ignoriert. Die Speech-Regel wird nur nach `.claude/rules/speech-mode.md` geschrieben und nie in `AGENTS.md` eingebettet.

**Verifizierte Ursache:**
- `scripts/lib/sync_pipeline.py:1543` — `if pc.get("has_rules", False):` umschließt den einzigen Aufruf von `sync_speech_mode` (`:1546`).
- `scripts/lib/rules.py:821-830` — `sync_speech_mode()` hat keinen Provider-Parameter; `rules_dir` fällt auf `CLAUDE_RULES_DIR` zurück (`:838-839`) und schreibt ausschließlich `.claude/rules/speech-mode.md`.
- `scripts/lib/cli_commands.py:327-333` — dasselbe `has_rules`-Gate im Test-Pfad.
- `config/project-config.schema.json:722` — Beschreibung behauptet fälschlich, die Regel werde immer nach `.claude/rules` kopiert.
- `speech/<mode>.md` liegt außerhalb von `rules/`; `collect_rule_sources` erfasst es nicht, daher greift der bestehende Embed-Kanal (`scripts/lib/context.py`, Embedded-Rules-Zweig ~`:2939`) nicht.

**Ziel:** Für `has_rules: false`-Provider wird `speech/<mode>.md` in den verwalteten Block der `context_file` (`AGENTS.md`) eingebettet. Für `has_rules: true`-Provider bleibt das Verhalten (Datei in `.claude/rules`) byte-identisch. Mode `full` erzeugt weiterhin nichts.

**Nicht-Ziele:**
- Keine neue Config-Option, keine Änderung der Speech-Mode-Inhalte (`speech/*.md`).
- Kein Umbau des Embed-Kanals für reguläre Rules.
- Keine Golden-/Pin-Rebaselines ohne ausdrückliche Nutzerfreigabe.
- Keine lokalen Szenario-Läufe (nur CI).
- Keine Provider-Namensabfragen im Syncer-Code (`provider-agnostic`).

## Interface Contracts

- `scripts/lib/rules.py:sync_speech_mode(agent_meta_root, project_root, config, log, dry_run, <bestehende Parameter>, provider_config=None) -> None`
  - Neuer optionaler Parameter `provider_config` (Capability-Flags des Providers). Bei `provider_config` mit `has_rules: false` schreibt die Funktion NICHT nach `CLAUDE_RULES_DIR`; sie entfernt/erzeugt dort nichts. Default `None` = bisheriges Verhalten (Rückwärtskompatibilität).
  - Fehlerpfad: fehlende Quelle `speech/<mode>.md` → `log.warning` + Skip (unverändert), kein Raise.
- `scripts/lib/rules.py:load_speech_rule_text(agent_meta_root, config, log) -> Optional[str]` (neu, Produces): liefert Inhalt von `speech/<mode>.md`; `None` bei Mode `full` oder fehlender Quelle (mit Warnung). Einzige Quelle für Datei- und Embed-Kanal.
- `scripts/lib/context.py` Embedded-Rules-Zweig (~`:2939`): konsumiert `load_speech_rule_text`; hängt den Text deterministisch (feste Position nach den regulären Rules, fester Abschnittskopf, Trailing-Newline-Normalisierung) in den verwalteten Block ein — nur wenn der Provider `has_rules: false` hat und der Embed-Kanal aktiv ist. Bei `None` unverändert (byte-identisch zu heute).
- `scripts/lib/sync_pipeline.py` (~`:1543-1546`) und `scripts/lib/cli_commands.py` (~`:327-333`): Aufruf von `sync_speech_mode` nicht mehr hinter `has_rules`-Gate; Provider-Kontext wird durchgereicht.
- `config/project-config.schema.json:722`: Beschreibung korrigiert (Datei nur für `has_rules: true`, sonst Einbettung in die Kontextdatei).

## Datenfluss

```
config["speech-mode"] ──> load_speech_rule_text ──┬─> sync_speech_mode ──> .claude/rules/speech-mode.md   (has_rules: true)
                                                  └─> context.py Embed-Zweig ──> managed block in AGENTS.md (has_rules: false)
mode == "full" ──> None ──> weder Datei noch Embed (stale Datei wie bisher entfernt, nur has_rules: true)
```

## Acceptance Criteria

1. AC-1: Opencode-Sync mit `speech-mode: caveman` → verwalteter Block in `AGENTS.md` enthält den Inhalt von `speech/caveman.md` (Test prüft Substring und Position innerhalb des Blocks).
2. AC-2: Für `has_rules: false`-Provider wird `.claude/rules/speech-mode.md` weder erzeugt noch verändert (kein `CLAUDE_RULES_DIR`-Fallback).
3. AC-3: Claude-Sync (`has_rules: true`) erzeugt `.claude/rules/speech-mode.md` byte-identisch zu vor der Änderung; `AGENTS.md`/`CLAUDE.md` enthalten keine doppelte Speech-Einbettung.
4. AC-4: `speech-mode: full` → keine Datei, kein Embed, Kontextdatei byte-identisch zu vor der Änderung.
5. AC-5: Zweimaliger Sync liefert byte-identische `AGENTS.md` (Idempotenz des verwalteten Blocks); Moduswechsel `caveman` → `full` entfernt den Embed-Abschnitt vollständig.
6. AC-6: Fehlende Quelle `speech/<mode>.md` → Warnung, kein Crash, kein Embed.
7. AC-7: Schema-Beschreibung nennt den Einbettungspfad für `has_rules: false`; `python3 scripts/sync.py --validate` grün.
8. AC-8: Kein `if provider == "<Name>"` im Diff (`tests/test_provider_agnostic_dispatch.py` grün).
9. AC-9: Bestehende Tests grün ohne Rebaseline: `tests/test_embed_rules_channel.py`, `tests/test_managed_index_alignment.py`, `tests/test_opencode_v2_surface.py`, `tests/test_context_managed_block_shrink.py`.

## Offene Fragen + Risiken

- **R-1 Managed-Block-Identität/Idempotenz:** Die Einbettung ändert den Block nur bei `speech-mode != full` und `has_rules: false`; Standardkonfigurationen (`full`) bleiben byte-identisch. Absicherung über AC-4/AC-5.
- **R-2 Digest-Pins:** Mögliche AGENTS.md-Pins/Goldens in `tests/` (compact-golden, topology-golden, ac01-baseline), falls deren Fixtures `speech-mode != full` mit Opencode/mammouth nutzen. Task 5 prüft das. **Bricht ein Pin: STOP, keine Rebaseline, Nutzer fragen.**
- **R-3 Budget-Ceilings:** Der Embed-Abschnitt erhöht die Größe von `AGENTS.md` nur in der betroffenen Konfiguration; `test_context_managed_block_shrink.py` ist Prüfstein. Ceiling-Änderung nur nach Nutzerfreigabe.
- **OF-1:** Position/Kopf des Embed-Abschnitts im Block (Vorschlag: nach den regulären Rules, Kopf `## Speech-Mode`). Freigabe der Spec bestätigt diesen Vorschlag.
- **OF-2:** Soll bei `has_rules: false` eine zuvor existierende `.claude/rules/speech-mode.md` aufgeräumt werden? Vorschlag: nein (Provider-fremder Pfad, nicht anfassen).

Klassifikation: M (Dateizahl 3–8), zusätzlich Architectural nach F7 (öffentliche Config-Semantik + mehrere Subsysteme: rules, context, pipeline, cli).

## Trace-Anker

spec-id: SPEC-1300-speech-mode-embed-channel

---

# Teil B — Plan

**Goal:** Speech-Mode wird für `has_rules: false`-Provider in den verwalteten Block der Kontextdatei eingebettet, ohne das `has_rules: true`-Verhalten zu ändern (Issue #1300).

**Architecture:** Eine zentrale Textquelle (`load_speech_rule_text`) speist zwei Kanäle: Datei (`sync_speech_mode`, nur `has_rules: true`) und Embed (`context.py`, nur `has_rules: false`). Der Aufruf wird vom `has_rules`-Gate gelöst; die Kanalwahl erfolgt über Capability-Flags.

**Tech Stack:** Python 3.9 (nur Stdlib), pytest, YAML/JSON-Schema.

**Spec:** docs/plans/2026-11-18-1300-speech-mode-embed-channel.md (Teil A, `spec-id: SPEC-1300-speech-mode-embed-channel`, Status: DRAFT — Ausführung erst nach `Status: APPROVED`)

## Global Constraints

- Nur Stdlib; Python-3.9-kompatibel (kein `X | Y`, kein `match`).
- Provider-Unterschiede nur über Capability-Flags, nie `if provider == "Name"`.
- Keine Golden-/Pin-/Ceiling-Rebaselines ohne ausdrückliche Nutzerfreigabe; bricht ein Pin: STOP und Nutzer fragen.
- Keine lokalen Szenario-Läufe (nur CI). Lokale Gates: `python3 scripts/sync.py --validate` und `python3 scripts/sync.py --check`.
- Kein `print()` in `scripts/lib/`.
- Branch `fix/1300-speech-mode-embed`; PR-Text `Resolves #1300`; Push/Tag/Branch nur durch Rolle `git`.
- Commit-Betreff Englisch, Imperativ, ≤ 72 Zeichen (`fix: ...`).
- Tasks 1 und 4 sind ownership-disjunkt und dürfen parallel laufen; alle übrigen sequentiell.

## File Structure

- Modify: `scripts/lib/rules.py` — `load_speech_rule_text`, `sync_speech_mode(provider_config)`
- Modify: `scripts/lib/context.py` — Embed-Zweig für Speech-Text
- Modify: `scripts/lib/sync_pipeline.py` — Gate lösen, Provider-Kontext durchreichen
- Modify: `scripts/lib/cli_commands.py` — Gate im Test-Pfad lösen
- Modify: `config/project-config.schema.json` — Beschreibung `speech-mode`
- Create: `tests/test_speech_mode_provider_channels.py` — AC-1…AC-6
- Modify: `tests/test_embed_rules_channel.py`, `tests/test_opencode_v2_surface.py` — Ergänzungen
- Modify: `CHANGELOG.md` — Eintrag

## Tasks

### Task 1: Zentrale Textquelle und provider-bewusstes sync_speech_mode
**Agent:** developer
**Depends on:** keine
**Files:**
- Modify: `scripts/lib/rules.py`
- Create: `tests/test_speech_mode_provider_channels.py`

**Interfaces:** Produces: `load_speech_rule_text(...)`, `sync_speech_mode(..., provider_config=None)`; Consumes: `speech/<mode>.md`, `config["speech-mode"]`.
- [ ] Step 1: Tests schreiben (fail): AC-2 (kein Schreiben nach `CLAUDE_RULES_DIR` bei `has_rules: false`), AC-3 (Datei byte-identisch bei `has_rules: true`), AC-4 (`full` → `None`), AC-6 (fehlende Quelle → Warnung)
- [ ] Step 2: `load_speech_rule_text` extrahieren; `sync_speech_mode` nutzt sie, bekommt `provider_config`, fällt bei `has_rules: false` nicht auf `CLAUDE_RULES_DIR` zurück
- [ ] Step 3: `python3 -m pytest tests/test_speech_mode_provider_channels.py` grün
- [ ] Step 4: Commit-Vorschlag `fix: gate speech-mode file channel on has_rules`

**Akzeptanz:** AC-2, AC-3, AC-4, AC-6 grün; `git diff scripts/lib/rules.py` enthält kein `provider ==`.

### Task 2: Embed-Kanal in der Kontextdatei
**Agent:** developer
**Depends on:** 1
**Files:**
- Modify: `scripts/lib/context.py`
- Modify: `tests/test_embed_rules_channel.py`

**Interfaces:** Consumes: `load_speech_rule_text`; Produces: Speech-Abschnitt im verwalteten Block bei `has_rules: false`.
- [ ] Step 1: Tests ergänzen (fail): AC-1 (Substring + Position im Block), AC-5 (Idempotenz, Moduswechsel `caveman` → `full` entfernt Abschnitt), AC-4 (Kontextdatei bei `full` byte-identisch)
- [ ] Step 2: Embed-Zweig (~`:2939`) um den Speech-Text erweitern; deterministische Reihenfolge und Newline-Normalisierung; Muster aus dem bestehenden Embed-Kanal wiederverwenden
- [ ] Step 3: `python3 -m pytest tests/test_embed_rules_channel.py tests/test_managed_index_alignment.py tests/test_context_managed_block_shrink.py` grün
- [ ] Step 4: Commit-Vorschlag `fix: embed speech-mode into managed block for has_rules false`

**Akzeptanz:** AC-1, AC-4, AC-5 grün; die drei genannten Testdateien ohne Fixture-/Pin-Änderung grün.

### Task 3: Aufruf vom has_rules-Gate lösen
**Agent:** developer
**Depends on:** 1, 2
**Files:**
- Modify: `scripts/lib/sync_pipeline.py`
- Modify: `scripts/lib/cli_commands.py`
- Modify: `tests/test_opencode_v2_surface.py`

**Interfaces:** Consumes: `sync_speech_mode(provider_config=...)`; Produces: Pipeline- und CLI-Pfad rufen `sync_speech_mode` unabhängig von `has_rules` auf und reichen `pc` durch.
- [ ] Step 1: Test in `test_opencode_v2_surface.py` ergänzen (fail): Opencode-Sync mit `speech-mode: caveman` enthält Speech-Text in `AGENTS.md`, keine `.claude/rules/speech-mode.md`
- [ ] Step 2: Gate in `sync_pipeline.py` (~`:1543`) und `cli_commands.py` (~`:327-333`) entfernen bzw. verschieben; `provider_config` übergeben
- [ ] Step 3: `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_speech_mode_provider_channels.py` grün
- [ ] Step 4: Commit-Vorschlag `fix: call sync_speech_mode independent of has_rules`

**Akzeptanz:** AC-1, AC-2, AC-3 end-to-end über Pipeline grün; `has_rules: true`-Output byte-identisch.

### Task 4: Schema-Beschreibung und Changelog
**Agent:** documenter
**Depends on:** keine
**Files:**
- Modify: `config/project-config.schema.json`
- Modify: `CHANGELOG.md`

**Interfaces:** Produces: korrigierte `speech-mode`-Beschreibung (`:722`), Changelog-Eintrag `Resolves #1300`.
- [ ] Step 1: Beschreibung korrigieren (Datei für `has_rules: true`, Einbettung in Kontextdatei sonst)
- [ ] Step 2: Changelog-Eintrag unter Fixed
- [ ] Step 3: `python3 scripts/sync.py --validate` grün
- [ ] Step 4: Commit-Vorschlag `docs: correct speech-mode schema description`

**Akzeptanz:** AC-7; JSON bleibt valide (`python3 -c "import json;json.load(open('config/project-config.schema.json'))"` ohne Fehler). Hinweis: Schema-Änderung kann einen Schema-Pin berühren — dann STOP und Nutzer fragen.

### Task 5: Verifikation und Pin-Prüfung
**Agent:** tester
**Depends on:** 1, 2, 3, 4
**Files:**
- (keine Schreibzugriffe; nur Ausführung)

**Interfaces:** Consumes: alle vorherigen Tasks; Produces: Prüfbericht.
- [ ] Step 1: `Grep` in `tests/` nach AGENTS.md-Digest-Pins, Goldens, Ceilings; prüfen, ob deren Fixtures `speech-mode != full` mit `has_rules: false` nutzen
- [ ] Step 2: `python3 -m pytest tests/test_speech_mode_provider_channels.py tests/test_embed_rules_channel.py tests/test_managed_index_alignment.py tests/test_opencode_v2_surface.py tests/test_context_managed_block_shrink.py tests/test_provider_agnostic_dispatch.py`
- [ ] Step 3: `python3 scripts/sync.py --validate` und `python3 scripts/sync.py --check`
- [ ] Step 4: Bericht; bei gebrochenem Pin: **STOP, keine Rebaseline, Nutzer fragen**

**Akzeptanz:** AC-8, AC-9 grün; beide sync-Gates Exit 0; kein Pin gebrochen oder Nutzerfreigabe dokumentiert.

## Self-Review

- Jeder Task mappt auf genau eine Rolle (developer, documenter, tester); jedes Akzeptanzkriterium ist messbar.
- `Files:`/`Interfaces:` vollständig; Parallelgruppe (Task 1 + 4) ohne Dateiüberlappung.
- `pipeline_stages` (`implement: 1`) im Frontmatter vorhanden; keine Platzhalter.
- Spec-Status ist DRAFT; Plan nicht ausführbar vor Nutzerfreigabe (`Status: APPROVED`).

**Annahmen:** Embed-Zweig in `context.py` ist ohne Strukturumbau um einen Zusatzabschnitt erweiterbar (wenn falsch: Task 2 wird L, Re-Planung). Kein Pin nutzt `speech-mode != full` mit `has_rules: false` (wenn falsch: STOP gemäß R-2).
**Re-Planning:** Nach Task 2 und nach Task 5 Annahmen prüfen und Plan anpassen.
**Aufwand:** Schätzung durch `effort-estimator` (Textreferenz; M, 5 Tasks).
