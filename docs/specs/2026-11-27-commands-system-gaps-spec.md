# Commands-System Restlücken (REQ-CMD-01..10) — Spec
> Status: APPROVED (2026-11-27)
> Klasse: **L / Bounded** (ca. 12-16 Dateien: 1 Code-Modul, 1 Config-Pfad, 3 Test-Dateien neu/erweitert, 1 Szenario-Trio, REQUIREMENTS.md, 3-4 Doku-Dateien, 2 `.gitkeep`) mit Review-Loop. Kein Architectural-Trigger (keine neue öffentliche Schnittstelle, kein Schema), solange 1B/2B gewählt wird; Option 1A/2A würde Contract/Baseline berühren (dann Neubewertung).
> Eingaben: `.tmp/phase2-inventory.md` (Explorer), `docs/plans/systemaudit-umsetzungsplan-2026-11-25.md` Phase 2 (Z. 106-119), `docs/REQUIREMENTS.md` REQ-CMD-01..10 (Z. 13-22)

## Problem / Ziel / Nicht-Ziele

**Problem:** Das Commands-System (`scripts/lib/commands.py`, 368 Zeilen) ist funktional vorhanden; 9 Lücken zwischen REQ-Wortlaut, Code, Doku und Tests blockieren das Phase-2-Exit-Kriterium.

**Ziel:** REQ, Code, Doku und Tests konsistent machen; jede Lücke mit testbarem AC schließen.

**Nicht-Ziele:**
- Keine Provider-Namenslogik (`if provider == "..."`); alles über Config-Keys/Capability-Flags (Dispatch-Tabelle `COMMAND_FORMAT_TRANSFORMS`, `commands.py:166-170`, bleibt).
- Kein Umbau von `--create-command` auf Multi-Provider (Claude-only, `commands.py:18,343`) — nur Test (Lücke 8); Erweiterung = offene Frage OF-5.
- Keine neuen Commands, kein Umbau von `context.py:sync_prompts_for_continue`.
- Keine Implementierung in dieser Spec.

## Entscheidungs-Optionen (ADR-Kurzform)

### ADR-1 — Continue-Index-Name (Lücke 1, REQ-CMD-03)
Kontext: REQ nennt `.continue/prompts/.agent-meta-managed`; Code setzt `commands_managed_index: .agent-meta-commands-managed` (`config/ai-providers.yaml:470`). Verifiziert: `scripts/lib/context.py:3756` schreibt für Continue-Rollen-Prompts (`generate-prompts: true`) **denselben Ordner** `.continue/prompts` mit Index `.agent-meta-managed`. Der Sondername verhindert die Kollision zweier Generatoren auf einem Index.

| | Option A: Code an REQ anpassen (Index → `.agent-meta-managed`) | Option B: REQ an Code anpassen (REQ-CMD-03 → `.agent-meta-commands-managed`) |
|---|---|---|
| Änderung | `ai-providers.yaml:470` Key entfernen + Merge-Logik, damit Commands und Rollen-Prompts einen Index teilen (oder Prompts umziehen) | Nur REQ-Text + Guide `:69` |
| Migrationsrisiko | **Hoch:** zwei Writer überschreiben sich gegenseitig den Index (`write_managed_index` schreibt Gesamtmenge) → Stale-Cleanup löscht fremde Dateien; Bestandsprojekte haben alte `.agent-meta-commands-managed` (Waise, nie bereinigt); Baseline `tests/fixtures/ac01-baseline/hashes.json:372` bricht | **Keines** (Doku-only) |
| Aufwand | M-L + Migrationspfad | S |

**Empfehlung: Option B.** Begründung: Kollision mit Rollen-Prompts ist real, Code ist bewusst abweichend, kein Konsument erwartet den REQ-Namen. Zusätzlich Test (siehe AC-1.2), der die Trennung festschreibt.

### ADR-2 — `requires_roles`-Strip (Lücke 2, REQ-CMD-06)
Kontext: `_strip_requires_roles` (`commands.py:60-65`, Aufruf `:298`) entfernt `requires_roles` aus der Ausgabe; REQ: „Kein anderes Frontmatter-Feld wird verändert oder entfernt". Zusätzlich verändert `{{VAR}}`-Substitution (`:300-302`) und Continue-`invokable`-Injektion den Text. `requires_roles` ist Generator-Direktive (IC-18 Nr. 9), Guide `commands.md:93` dokumentiert das bereits.

| | Option A: Code an REQ anpassen (Key im Output belassen) | Option B: REQ an Code anpassen (Ausnahme für Generator-Direktiven) |
|---|---|---|
| Änderung | `_strip_requires_roles` + Aufruf entfernen | REQ-CMD-06 Satz 3 ergänzen: „… außer der Generator-Direktive `requires_roles`, die nach der Auswertung entfernt wird; `{{VAR}}`-Platzhalter werden substituiert." |
| Migrationsrisiko | **Mittel:** generierte `doc-now.md` ändert sich in allen Zielprojekten (Drift/`--check`-Diff, Baselines `ac01-baseline`); unbekannter Key im Frontmatter kann von Providern mit striktem Schema (z. B. Continue `invokable`-Prompts, TOML-Konverter ignoriert) abgelehnt/gewarnt werden; Test `test_commands_requires_roles.py` (Strip-Assertions) muss invertiert werden | **Keines** (Doku-only); Test `test_commands_requires_roles.py` bleibt maßgeblich |
| Aufwand | M | S |

**Empfehlung: Option B.** Begründung: Direktive ist generator-intern; Leak in Zielprojekte wäre ein Defekt, nicht Konformität.

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

Bestehende Signaturen bleiben unverändert, außer wo genannt.

| ID | Ziel | Contract |
|----|------|----------|
| IC-1 | `docs/REQUIREMENTS.md` REQ-CMD-03 | Text: Stale-Tracking via `.continue/prompts/.agent-meta-commands-managed` (Begründung: eigener Index neben Rollen-Prompt-Index) — nur bei ADR-1 = B |
| IC-2 | `docs/REQUIREMENTS.md` REQ-CMD-06 | Ausnahmeklausel `requires_roles` + Substitution — nur bei ADR-2 = B |
| IC-3 | `scripts/lib/commands.py:sync_commands_for_provider` | Zeilen 244-256: Guard `if not sources: return` **entfällt**. Vertrag: Provider mit `provider_commands_supported(caps) == True` und fehlendem/leerem `commands_dir` → `raise SyncError("Provider '<p>' declares commands support … no commands_dir …")` unabhängig von der Quellenmenge. Signatur unverändert. |
| IC-4 | `commands/0-external/.gitkeep`, `commands/2-platform/.gitkeep` | Leere Marker-Dateien (kein `*.md`, sonst würde `collect_command_sources` sie als Command globben; **keine README.md** in diesen Ordnern). |
| IC-5 | `tests/test_commands_layers.py` (neu) | Tests für `collect_command_sources(agent_meta_root: Path, platforms: list[str]) -> list[tuple[Path, str]]` auf tmp-Baum. |
| IC-6 | `tests/test_commands_hard_error.py` (neu) | Tests für IC-3 und die „not supported"-Info (`commands.py:231-237`). |
| IC-7 | `tests/test_commands_create_command.py` (neu) | Tests für `create_command(project_root, name, log, dry_run)` (`commands.py:334`). |
| IC-8 | `tests/test_commands_gate_consistency.py` (neu) | Konsistenztest `config/ai-providers.yaml:has_commands` vs. `config/provider-capabilities.yaml:commands`, via `load_provider_capabilities` + `provider_commands_supported` (`providers.py:850`). |
| IC-9 | `tests/test_managed_index_alignment.py` (erweitern) oder neu `tests/test_commands_continue_stale.py` | Continue-Stale-Test inkl. Index-Namens-Trennung. |
| IC-10 | `tests/scenarios/configs/107-commands-system.project.yaml`, `tests/scenarios/asserts/107-commands-system.sh`, Zeile in `tests/scenarios/registry.md` Katalog | Neues Szenario (ID 107; 94-98 reserviert, 103 frei/ungenutzt — Prüfung bei Umsetzung). Assert-Skript-Contract wie `07-new-providers.sh` (cwd = Temp-Projekt, `REPO_ROOT` als `$1`/Env, `fail()`-Muster). |
| IC-11 | Doku | `docs/guides/features/commands.md`, `docs/guides/setup/instantiate-project.md`, `templates/configs/CLAUDE.project-template.md` (Quelle von `CLAUDE.md`/`AGENTS.md`-Abschnitt; **`CLAUDE.md` nicht von Hand editieren, sondern per Sync erzeugen**, `knowledge/wiki/topics/commands.md` + `knowledge/sources/…` nur über Knowledge-Workflow). |

Fehlerpfade: unbekanntes `commands_format` → `SyncError` (besteht, `commands.py:173-186`); unlesbarer Index → warn + leer (besteht, `:267-275`).

## Datenfluss

`commands/{0-external,1-generic,2-platform}/*.md` → `collect_command_sources` (Priorität 0 < 1 < 2, platform-Präfix gestrippt) → pro Provider: Gate (`has_commands` in `sync_pipeline.py:1784` UND `commands` in capabilities `commands.py:231`) → `requires_roles`-Filter → Strip → `{{VAR}}`-Substitution → Format-Transform → `write_checked` → Managed-Index (`commands_managed_index`, Default `.agent-meta-managed`) → `cleanup_stale_managed_files`. Persistenz: Zielverzeichnis + Index. Tests lesen nur tmp-Bäume.

## Acceptance Criteria

Format Given/When/Then; Testverweis in Klammern. Alle Tests vom Entwickler zu schreiben, nicht in dieser Phase.

**Lücke 1 — REQ-03 Continue-Index**
- AC-1.1 Given ADR-1 = B, When `docs/REQUIREMENTS.md` gelesen, Then REQ-CMD-03 nennt `.agent-meta-commands-managed` und Guide `commands.md` enthält überall konsistente Namen (Test: Grep-basierter Doku-Test in `tests/test_commands_gate_consistency.py` ODER Konsistenz-Check, siehe AC-3.2). → IC-1
- AC-1.2 Given Continue mit `generate-prompts: true` und Commands, When Sync zweimal läuft, Then existieren `.continue/prompts/.agent-meta-managed` (nur Rollen-Prompts) und `.agent-meta-commands-managed` (nur Commands), disjunkt, und ein entferntes Command wird gelöscht, ohne ein Rollen-Prompt zu löschen. (IC-9; ergänzt Szenario 73/72)
- AC-1.3 Given ein Command wird aus den Quellen entfernt, When Continue-Sync, Then wird die Datei in `.continue/prompts/` gelöscht und Index aktualisiert (IC-9, Continue-Stale-Test; schließt Inventar-Lücke „kein Continue-Stale-Test").

**Lücke 2 — REQ-06 requires_roles**
- AC-2.1 Given ADR-2 = B, When REQ-CMD-06 gelesen, Then enthält es die Ausnahme für `requires_roles` (Doku-Review; IC-2).
- AC-2.2 Given Quelle mit `requires_roles: [documenter]` und aktivem documenter, When Sync, Then Output enthält Feld `requires_roles` nicht und alle übrigen Frontmatter-Felder (`description`, `allowed-tools`, `argument-hint`) byte-identisch (bestehend: `tests/test_commands_requires_roles.py`; ggf. Assertion „andere Felder unverändert" ergänzen).
- AC-2.3 Given Option A gewählt (Abweichung von Empfehlung), Then Test invertiert und Baselines `ac01-baseline` neu erzeugt — nur bei Entscheidung A.

**Lücke 3 — REQ-09 Doku**
- AC-3.1 `templates/configs/CLAUDE.project-template.md` enthält Commands-Abschnitt (Verzeichnisstruktur `commands/0-external|1-generic|2-platform`, Sync-Verhalten-Tabelle je `commands_dir`); nach Sync enthält `CLAUDE.md` und `AGENTS.md` den Abschnitt (Test: Szenario 107 Assert grep + `--validate` rc 0).
- AC-3.2 `docs/guides/features/commands.md` ist widerspruchsfrei: `:69` und `:143` nennen beide die Ausnahme Continue (`.agent-meta-commands-managed`); `:70`/`:222-223` analog. (Test: Doku-Konsistenztest, der in der Datei jedes Vorkommen von `.agent-meta-managed` im Continue-Kontext prüft, oder manuelle Review-Checkliste — OF-4.)
- AC-3.3 `instantiate-project.md` und Guide beschreiben projekt-eigene Commands direkt in `.claude/commands/` (keine 3-project-Schicht); bei Namenskollision mit einem agent-meta-Command wird die Projektdatei ohne Backup überschrieben; die Doku nennt `3-project/commands` nicht. (Test: Grep-Assertion „`3-project/commands`" nicht in Guide und instantiate-project.md.)
- AC-3.4 Command-Liste in Guide (`:181-192`) deckt alle `commands/1-generic/*.md` ab (aktuell 24, Guide 10), vorzugsweise generiert/geprüft: Test vergleicht Dateiliste mit Guide-Tabelle (IC-11; Test `tests/test_commands_gate_consistency.py` oder eigener Doku-Test).

**Lücke 4 — REQ-01 Layer**
- AC-4.1 Given `commands/0-external/` und `commands/2-platform/` im Repo, Then beide existieren (`.gitkeep`) und erzeugen keinen Command im Output (IC-4; Test in `test_commands_layers.py`: `collect_command_sources(real_root, [])` enthält keinen Eintrag mit Namen `.gitkeep`).
- AC-4.2 Given tmp-Baum mit gleichnamigem `x.md` in 0-external, 1-generic und `p-x.md` in 2-platform, When `collect_command_sources(root, ["p"])`, Then genau ein Eintrag `x.md`, Quelle = 2-platform; mit `platforms=[]` Quelle = 1-generic; ohne 1-generic Quelle = 0-external. (IC-5)
- AC-4.3 Given `p-x.md` und `platforms=["q"]`, Then nicht enthalten; Präfix-Strip `p-deploy.md` → `deploy.md`. (IC-5)

**Lücke 5 — REQ-10**
- AC-5.1 Given Provider mit `commands: true`, `commands_dir` fehlt/leer und **leere** Quellen (tmp-`agent_meta_root` ohne Commands), When `sync_commands_for_provider`, Then `SyncError` mit „commands_dir". (IC-3, IC-6)
- AC-5.2 Dito mit nichtleeren Quellen → `SyncError` (Regression des bestehenden Verhaltens). (IC-6)
- AC-5.3 Given Provider mit `commands: false`, When Sync, Then genau eine INFO-Zeile „not supported" in `SyncLog`, keine Dateien geschrieben. (IC-6)
- AC-5.4 Given alle 9 Provider in der Real-Config, When Sync (Szenario 71), Then kein neuer Fehler (Regression: Real-Config hat stets `1-generic`-Quellen).

**Lücke 6 — Szenario**
- AC-6.1 `tests/scenarios/run.sh 107` ist PASS; Szenario deckt: Claude+Continue+Opencode (markdown), Gemini (toml), Codex/KimiCode (kein Commands-Dir), `doc-now.md` ohne `requires_roles` (documenter aktiv), `.continue/prompts/.agent-meta-commands-managed` vorhanden, zweiter Sync idempotent. (IC-10)
- AC-6.2 Katalogzeile in `registry.md` mit ID, Providern und Feature (Konvention Z. 16-25). Dev- und release-Profil identisches PASS.

**Lücke 7 — Gate-Doppelung**
- AC-7.1 Given jeder Provider in `config/ai-providers.yaml`, Then `has_commands` (bool) == `provider_commands_supported(capabilities[provider])`; Fehlermeldung nennt Provider und beide Werte. (IC-8)
- AC-7.2 Given `has_commands: true`, Then `commands_dir` nicht leer und `commands_format ∈ COMMAND_FORMAT_TRANSFORMS` (IC-8). Der Test enthält keine Provider-Namen als Fixture-Annahme (iteriert Config).

**Lücke 8 — REQ-08**
- AC-8.1 Given existierende `.claude/commands/<name>.md` mit eigenem Inhalt, When `create_command` und `--create-command`, Then Datei byte-identisch, Log-Eintrag SKIP. (IC-7)
- AC-8.2 Given Datei fehlt, Then angelegt, `.md`-Suffix idempotent (`foo` und `foo.md` → `foo.md`), nicht im Managed-Index. (IC-7)
- AC-8.3 Given angelegtes Projekt-Command und nachfolgender normaler Sync (Claude), Then Datei bleibt unangetastet und wird nicht gelöscht (Stale-Cleanup greift nur Index-Einträge). (IC-7)
- AC-8.4 `dry_run=True` → keine Datei.

Jedes AC mappt auf mindestens einen IC; Gesamtgate: `python3 scripts/sync.py --validate` und `tests/scenarios/run.sh` PASS.

## Offene Fragen + Risiken

Entscheidungen (vom User im Dialog freigegeben, 2026-11-27) — alle Fragen aufgelöst:
- **OF-1 (ADR-1): ENTSCHIEDEN = Option B.** REQ-CMD-03 wird an den Code angepasst; Index bleibt `.agent-meta-managed` für Rollen-Prompts, Commands nutzen separaten Index (Code-Stand unverändert).
- **OF-2 (ADR-2): ENTSCHIEDEN = Option B.** REQ-CMD-06 erhält Ausnahme für die Generator-Direktive `requires_roles`; Strip im Code bleibt.
- **OF-3 (Gate-Doppelung, Lücke 7): ENTSCHIEDEN = Gate nur per Test absichern** (IC-8); kein Konsolidieren.
- **OF-4 (AC-3.2/3.4): ENTSCHIEDEN = Doku-Konsistenz automatisiert testen.**
- **OF-5: ENTSCHIEDEN = `--create-command` bleibt Claude-only.**
- **OF-6: ENTSCHIEDEN = Hard-Error bei leeren Quellen akzeptiert** (IC-3).

Offene Fragen: keine.

Risiken:
- R-1: `CLAUDE.md`/`AGENTS.md` sind generiert; Handedit wird überschrieben → nur Template ändern (AC-3.1).
- R-2: `.gitkeep`/README in `commands/0-external|2-platform` — README würde als Command gesynct; nur `.gitkeep` (IC-4). Prüfen, dass `--validate`/Consistency-Checks keine Leer-Ordner beanstanden.
- R-3: Knowledge-Bundle-Kopien (`knowledge/wiki/topics/commands.md`, `knowledge/sources/…`) tragen denselben Doku-Widerspruch → über Knowledge-Workflow (Ingest) nachziehen, nicht in dieser Spec.
- R-4: Szenario-ID 107: Kollision mit parallelen Branches prüfen.
- R-5: Nicht geprüft: Existenz des `documenter`-Agenten (REQ-07); Tests nicht ausgeführt.

## Trace-Anker: spec-id: SPEC-COMMANDS-SYSTEM-GAPS-2026-11-27
