---
pipeline_stages:
  implement: 1
status: DRAFT
date: 2026-11-11
base-commit: 9aa0e0c0
branch: feat/phase-g-provider
trace:
  - roadmap-2026-11-10-phase-G
---

# Phase G — Provider (Gemini/Antigravity/Opencode/Hermes) — Implementation Plan

> Status: DRAFT (2026-11-11). Dieser Plan implementiert nichts, committet nichts, ändert keine Issues.
> Basis: `origin/main 9aa0e0c0` (Review 2026-11-11: alle Zeilenanker gegen diesen Stand neu gemessen; seit `a3d65da4` haben sich von den referenzierten Dateien nur `scripts/lib/config.py` und `scripts/lib/agent_sync.py` geändert, Anker korrigiert). Roadmap: `docs/superpowers/plans/2026-11-10-backlog-roadmap.md` (APPROVED), Phase G, Welle 4.
> Issues: #854, #860, #1160, #1171, #1175, #800, #814.
> Abhängigkeiten (Roadmap §3): Welle 4 hängt von A (Labels `blocked` für #860/#854), B (#1170 vor #854) und dem #1085/#1155-Flag aus C (`--fail-on-p0`, Entscheidung 4/38b) ab; parallel zu H. Der Bezug von G zum C-Flag ist in der Roadmap nicht begründet (siehe "Nicht verifiziert"). #860 ist extern blockiert (`agy` SIGILL, Owner-Kommentare 2026-10-27/29).
> Branch: `feat/phase-g-provider`. Höchstens zwei PRs für Phase G, ein Commit je Task (Entscheidungen 17 und 52; weicht von Roadmap §3 "Teil-PRs bei Feature-Arbeit" ab, Roadmap-Text nicht geändert): **G-PR1 (Phasen-PR)** enthält nur die derzeit ausführbaren Tasks; **G-PR2 (Nachfolge-PR derselben Phase)** enthält die gesperrten/spec-gesteuerten Tasks, sobald ihre Sperren gefallen sind. Ausnahme von "ein PR je Phase" neben #1086i und #1209 (Entscheidung 52). Schnitt siehe "PR-Schnitt (Entscheidung 52)".
> Revision: Entscheidungen 52 (G-O2 beantwortet) und 56 (O-H7: G vor H mergen) eingearbeitet. G-O1 und G-O3 bleiben offen (Roadmap 7d "Weiterhin offen nach Teil 4").

**Goal:** Die sieben Provider-Issues so ordnen, dass der entscheidungsfreie Teil sofort umsetzbar ist (Hermes-Export fail-closed, Konsistenztest für das Gemini-Toolvokabular, Opencode-Beleg-Doku, Probe-Runbooks) und der Rest hinter Spec-Gate bzw. Runtime-Probe (#860) wartet.
**Architecture:** Provider-Unterschiede bleiben Config-Keys/Capability-Flags (`config/ai-providers.yaml`, `config/provider-capabilities.yaml`, `config/provider-tools.yaml`); kein `if provider == "Name"`. `mcp_provider_config.py` wird format-gesteuert erweitert (Format-Wert, nie Providername). Probe-Ergebnisse landen als Evidenzdokumente unter `docs/analysis/evidence/`.
**Tech Stack:** Python 3.9 (stdlib + PyYAML), pytest, YAML/Markdown.
**Spec:** keine (Spec-Gates: Task 0a/0b/0c)

## Klassifizierung (Spec/Plan-Gate)

| Issue | Klasse | Spec-Gate | Begründung |
|---|---|---|---|
| #860 | S (Tracking) | nein | kein Code; Probe-Runbook (Task 4) vorbereiten, Probe-Lauf (Task 5) extern blockiert |
| #1175 | S (Doku) + Probe (Task 3 und 6) | nein | Teilantwort steht im Repo (Evidenz `docs/analysis/evidence/2026-09-30-runtime-opencode-v1.md`); Request-Body-Capture braucht Opencode-Runtime |
| #1160 | M (Schritt 2/3) | ja, Task 0c | Schritt 1 ist erledigt (PR #1165, `config/provider-capabilities.yaml:289`); Schritt 2/3 blockiert durch Runtime-Probe (#860/#854) |
| #1171 | S, aber entscheidungsabhängig von #1160 | über Task 0c | xfail-Konsistenztest sofort (Task 2); Angleichung erst nach #1160-Entscheidung (Task 9) |
| #854 | M | ja, Task 0c | Entscheidung 10: Commands auf Skills umziehen, erst nach Runtime-Probe (#860); neues `commands_format` für Ordner-pro-Skill nötig |
| #800 | L | ja, Task 0b | Hermes als Provider-Target, Option A fest (Entscheidung 34, G-N1; final nach Probe-Evidenz); der Teil "fail-closed Export" ist eigenständig S (Task 1) |
| #814 | M | ja, Task 0a | neues Katalogfeld `cwd`, zwei Ausgabeformate, Validierung unbekannter Keys, Route (b) External-Tool-Modus `config-generated-by` fest (Entscheidung 27); Format-Matrix bleibt Spec-Gate |

Jede der 7 Nummern wird genau einmal abgedeckt (siehe Self-Review).

## Global Constraints

- Python 3.9 kompatibel (kein `X | Y` als Laufzeit-Typ ohne `from __future__ import annotations`, kein `match`).
- Nur stdlib + PyYAML; keine neue Abhängigkeit.
- Provider-agnostisch: Unterschiede über Config-Keys/Capability-Flags (Format-Wert wie `fmt == "opencode-json"`), nie `if provider == "Name"` (`knowledge/wiki/concepts/provider-agnostic-policy.md`; ein Skill `provider-agnostic` unter `.claude/skills/` wurde in W nicht gefunden).
- Commits: Conventional Commits, Englisch, Betreff höchstens 72 Zeichen, Imperativ, kein BOM. Commit-/PR-Texte werden später als Datei bereitgestellt; hier nur Betreffzeilen. Trailer (z. B. Co-Authored-By) schreibt der Task-Prompt vor; der git-Agent übernimmt sie verbatim, der Plan setzt keine eigenen (Entscheidung 25).
- Kein `isolation: "worktree"`. Kein Push/Tag/Branch durch Worker (nur `git`-Rolle).
- Commit-/PR-Texte ohne Closing-Schlüsselwörter (Closes/Fixes/Resolves); Issues nur nach Freigabe mit Evidenz-Kommentar manuell schließen (Entscheidung 38e).
- Kostenpflichtige Läufe (echte Provider-/Agent-Läufe, API-Calls, z. B. Task 5 und Task 6): nur nach Kostenschätzung und ausdrücklichem User-Ja (Roadmap §4).
- Destruktive Git-Befehle werden nie umgangen; blockiert der Guard, liefert der Assistent die Befehle, der User führt sie per `!` aus (Roadmap §4). Dieser Plan sieht keine vor.
- Tests: `python3 -m pytest <datei>::<test>`; Gesamtprüfung `python3 scripts/sync.py --validate`.
- Pro Task: roter Test, Implementierung, grün, ein Commit auf dem Phasen-Branch (Entscheidung 17: ein Commit je Task; Entscheidung 52: max. 2 PRs je Phase). Spec-/Probe-gesperrte Tasks sind nicht ausführbar, bevor ihre Sperre aufgehoben ist (Spalte "Sperre"), und landen in G-PR2.
- Vor Ausführung: Freshness-Check (`check_plan_refs.py`; liegt nicht auf `origin/main`, sondern im Review-Worktree `.tmp/wt-check-plan-refs/scripts/`) gegen `origin/main`; Zeilenanker gelten für `9aa0e0c0`. Nackte `:NNNN`-Anker prüft das Skript nicht, sie sind von Hand nachzumessen (nach C, D und B verschieben sich u. a. `mcp_provider_config.py` und `config/ai-providers.yaml`).
- Phase B löscht `scripts/lib/provider_transform.py::_map_claude_tools_to_gemini_tools` (#1170) und entkoppelt die Notiz G4-2 in `config/provider-capabilities.yaml`. G fasst diese Funktion nicht an; Task 2 und 9 rebasen auf den Stand nach B.

## File Structure

- Modify: `scripts/hermes_export.py` — fail-closed bei fehlendem PyYAML (#800, Task 1)
- Modify: `tests/test_hermes_export.py` — Tests für den fail-closed-Pfad (#800, Task 1)
- Create: `tests/test_gemini_tool_vocabulary_consistency.py` — Invariante: ein Terminal-Toolname je Oberfläche, xfail(strict) bis #1160 entschieden (#1171, Task 2)
- Modify: `config/ai-providers.yaml` — Kommentar am Opencode-`allowed-fields` um Evidenz- und Restunsicherheit erweitern (#1175, Task 3); später Hermes-Eintrag (Task 8), ggf. `bash_tool_name`/`commands_*` für Gemini (Task 9/10)
- Create: `tests/test_opencode_options_passthrough_note.py` — pinnt die drei Keys in `allowed-fields` und den Evidenzverweis (#1175, Task 3)
- Create: `docs/analysis/runbooks/antigravity-runtime-probe.md` — Probe-Runbook G-1/G-2/G-3/G-7, H2/H3 (#860, Task 4)
- Create: `docs/analysis/evidence/<datum>-runtime-antigravity-pclmul.md` — Probe-Ergebnis (#860, Task 5, blockiert)
- Create: `docs/analysis/runbooks/opencode-request-options-probe.md` — Runbook Request-Body-Capture (#1175, Task 6)
- Create: `docs/analysis/evidence/<datum>-runtime-opencode-request-options.md` — Probe-Ergebnis (#1175, Task 6, gesperrt)
- Create: `tests/test_antigravity_probe_runbook.py` — Runbook-Stichworte (#860, Task 4)
- Create: `tests/test_opencode_probe_runbook.py` — Runbook-Stichworte (#1175, Task 6)
- Create: `tests/test_hermes_provider_target.py` — (#800, Task 8)
- Create: `docs/specs/2026-11-11-814-mcp-stdio-cwd-spec.md` — Spec (Task 0a)
- Create: `docs/specs/2026-11-11-800-hermes-provider-target-spec.md` — Spec (Task 0b)
- Create: `docs/specs/2026-11-11-gemini-target-platform-spec.md` — Spec/ADR-Entwurf für #1160/#1171/#854 (Task 0c)
- Modify: `scripts/lib/mcp_provider_config.py` — `cwd`, Unbekannt-Key-Warnung, External-Tool-Modus (#814, Task 7)
- Modify: `tests/test_mcp_config.py` — Regressionstests #814 (Task 7)
- Modify: `config/plugin-catalog.yaml` — Eintrag `projectatlas` nach Spec (#814, Task 7)
- Modify: `scripts/lib/commands.py` — `commands_format: skill` (#854, Task 10)
- Create: `tests/test_commands_skill_format.py` — (#854, Task 10)
- Create: `docs/guides/hermes-integration.md` — Consumer-Vertrag (#800, Task 8)
- Modify: `config/provider-bootstrap.yaml`, `config/provider-capabilities.yaml`, `.meta-config/project.yaml`-Schema (Hermes-Eintrag, Task 8; Details laut Spec 0b)

## Abweichungen zur Roadmap und zu den Issue-Texten

- **Abweichung zur Roadmap:** #1171-Beleg `config/provider-tools.yaml:142` `Gemini: code_execution` stimmt. Zusätzlich dasselbe Vokabular in `config/provider-tools.yaml:41` (Kommentar `Bash -> code_execution`) und `config/ai-providers.yaml:203` (`bash_tool_name: code_execution`).
- **Abweichung zur Roadmap:** Roadmap "ai-providers.yaml:180-182" für #854 stimmt (`commands_dir` 180, `commands_ext` 181, `commands_format` 182; `has_commands` steht auf 179).
- **Abweichung zur Roadmap:** #1175 ist nicht rein "nicht verifizierbar". Der Allow-list-Kommentar in `config/ai-providers.yaml:399-405` (Issue nennt `378-391`, verschoben) belegt per Evidenz `docs/analysis/evidence/2026-09-30-runtime-opencode-v1.md:63-74`: `version`, `prompt_mode`, `generated-from` landen im Harness-Bucket `options` (VERIFIED). Ob ein Provider sie als Request-Optionen akzeptiert, ist laut `:131-132` UNVERIFIABLE ohne Request-Body-Capture. Die Frage ist also halb aus W beantwortbar, die andere Hälfte ist eine Recherche-/Probe-Aufgabe.
- **Abweichung (Issue #814):** Der Stdio-Zweig steht in `scripts/lib/mcp_provider_config.py:261-275`, nicht `134-147`. `_build_connection_entry` beginnt `:187`. `scripts/lib/plugins.py:84,89` liest `binary`/`connection.command` und `connection.url` (Issue-Anker stimmt). Das Verwerfen unbekannter Keys ist weiter wahr (kein `cwd`-Lesen im Builder).
- **Abweichung (Issue #800):** Hermes ist weiterhin kein Provider (Treffer nur in `scripts/hermes_export.py`, vier Testdateien). Aber der Export hat sich seit dem Issue geändert (#1094): Skill-Ordner heißt `roles/agent-meta-<role>/` (`scripts/hermes_export.py:125`, nicht `roles/<role>/`), und ein Basistemplate ohne `role-defaults`-Eintrag bekommt `balanced` **ohne** Warnung (`collect_role_meta`, `:292-295`). Damit ist das im Issue beschriebene irreführende "no abstract tier"-Diagnosemuster ohne PyYAML nicht mehr sichtbar: `load_roles_config` liefert leere Rollen (`scripts/lib/roles.py:71-72`), also läuft der Export still mit Exit 0 durch (nur die allgemeine stderr-Zeile aus `scripts/lib/io.py:71-73`, Issue nennt `66-69`). Das Risiko ist damit eher größer.
- **Abweichung (Issue #800):** Das Fail-closed-Muster aus dem Issue (`scripts/lib/config.py:242-245`) steht jetzt in `scripts/lib/config.py:354-356` (`print("ERROR: PyYAML not installed but ...")` + `sys.exit(1)`); `resolve_abstract_tier` steht `scripts/hermes_export.py:217` (nicht `~199-230`).
- **Abweichung (Roadmap Phase G):** Titel nennt Mammouth; kein Issue der Phase betrifft Mammouth. Nichts zu planen.

## Entscheidungen (beantwortet)

Quelle: Roadmap-Entscheidungen 17-34 (user-beantwortet, `.tmp/decisions-part2.md`) und 52 (Roadmap Abschnitt 7c). Original-IDs in Klammern.

**Gate (explizit):** G-N1, G-N3 und G-N4 sind beantwortet, aber **vorläufig final**: Die Festlegung wird erst nach Probe-Evidenz final. Bis dahin baut keine Task-Ausführung darauf auf, die nicht ohnehin gesperrt ist.

- **N2 / Entscheidung 27 (#814):** Route (b) fest: dokumentierter External-Tool-Modus `config-generated-by` mit `cwd`-Emission und Fail-closed-/Warn-Aktivierung. Route (a) entfällt. Format-Matrix bleibt Spec-Gate (Task 0a). Auswirkung: Tasks 0a, 7.
- **N1 / Entscheidung 34 G-N1 (#800):** Hermes-Target Option A (dünnes Target: `hermes_export.py` bleibt Generator, Provider-Eintrag deklariert nur Ziel/Gitignore-Roots). Option B entfällt für diese Phase. **Status: beantwortet, FINAL erst nach Probe-Evidenz (Gate).** Auswirkung: Tasks 0b, 8.
- **N3 / Entscheidung 34 G-N3 (#1160 Schritt 2):** Gemini CLI bleibt Default (so in `config/provider-capabilities.yaml:289` dokumentiert), Antigravity bleibt opt-in. **Status: beantwortet, FINAL erst nach Probe-Evidenz (Gate).** Auswirkung: Tasks 0c, 2 (xfail bleibt bis final), 9.
- **N4 / Entscheidung 34 G-N4 (#1175):** Die drei Opencode-Keys (`version`, `prompt_mode`, `generated-from`) bleiben. **Status: beantwortet, FINAL erst nach Probe-Evidenz (Gate, Task 6).** Auswirkung: Tasks 3, 6.
- **Entscheidung 10 (#854):** Commands werden erst nach Runtime-Probe #860 auf Skills umgezogen. Auswirkung: Tasks 0c, 5, 10.
- **Entscheidung 17 (Cross-Cutting):** Ein Phasen-PR, ein Commit je Task. Durch Entscheidung 52 ergänzt. Auswirkung: Kopf, Global Constraints, Task 5.
- **Entscheidung 52 (G-O2):** Phasen-PR enthält nur derzeit ausführbare Tasks; gesperrte/spec-gesteuerte Tasks laufen in einem Nachfolge-PR derselben Phase (max. 2 PRs je Phase; Ausnahme neben #1086i und #1209). Auswirkung: Kopf, Global Constraints, Task 5, Abschnitt "PR-Schnitt (Entscheidung 52)".
- **Entscheidung 56 (O-H7, Plan H):** G merged vor H (Merge-Reihenfolge). Auswirkung: Ausführungsreihenfolge.
- **Entscheidung 25 (Trailer):** Trailer kommen aus dem Task-Prompt, der git-Agent übernimmt sie verbatim. Der Plan enthält keine eigenen Trailer-Vorgaben. Auswirkung: Global Constraints.

## Offene Entscheidungen (neu, ungeklaert)

Nicht durch 17-34 und 39-53 gedeckt, nicht geraten:

- **G-O1 (OFFEN):** Probe-Art und Evidenzpfad für G-N1 (#800) sind nicht benannt. Task 0b-Spec muss sie vorschlagen und zur Freigabe stellen. Bis dahin bleibt Task 8 gesperrt.
- ~~**G-O2:** Abschluss/Merge des Phasen-PRs, solange Tasks 5, 6, 0c, 8, 9, 10 gesperrt sind.~~ **Beantwortet durch Entscheidung 52:** G-PR1 mit den ausführbaren Tasks mergen, gesperrte Tasks in G-PR2 (siehe "PR-Schnitt (Entscheidung 52)").
- **G-O3 (OFFEN):** Kostenfreigabe für Task 5 und Task 6 (echte Provider-/Agent-Läufe). Vor Ausführung Kostenschätzung vorlegen; ohne ausdrückliches User-Ja kein Lauf (Roadmap §4).
- Ob die `gemini`-CLI auf dem Host probebar ist (ungeprüft), von dem das Finalisieren von G-N3 abhängt.

---

### Task 0a: Spec #814 schreiben + Freigabe-Gate (Spec-Gate 1)
**Agent:** requirements
**Files:** Create `docs/specs/2026-11-11-814-mcp-stdio-cwd-spec.md`
**Interfaces:** Produces: freigegebene Spec (`Status: APPROVED`); Consumes: Entscheidung 27 (Route b, vormals N2), Issue #814 AC 1 bis 6
- [ ] Step 1: Spec mit Route (b) laut Entscheidung 27 (vormals N2), Matrix "Format x cwd-Unterstützung" (je Format belegt oder `UNVERIFIED`), Fehlerverhalten bei unbekannten `connection`-Keys (Warnung vs Fehler), Migration für bestehende Katalogeinträge.
- [ ] Step 2: Review, Freigabe durch User. Verifikation: `grep -n "Status: APPROVED" docs/specs/2026-11-11-814-mcp-stdio-cwd-spec.md` liefert 1 Treffer (Marker in der Form, die `_APPROVED_RE` in `scripts/lib/consistency/spec_plan.py:85-87` erkennt: `> Status: APPROVED` oder `**Status:** APPROVED`; die Form `Status: **APPROVED**` erkennt das Gate nicht).
- [ ] Step 3: commit `docs: add spec for stdio MCP cwd support (#814)`
Sperre für Task 7: bis Status APPROVED.

### Task 0b: Spec #800 schreiben + Freigabe-Gate (Spec-Gate 2)
**Agent:** requirements
**Files:** Create `docs/specs/2026-11-11-800-hermes-provider-target-spec.md`
**Interfaces:** Produces: freigegebene Spec; Consumes: Entscheidung 34 (G-N1: Option A, vormals N1; final nach Probe-Evidenz), `config/ai-providers.yaml` (Provider-Schema), `scripts/lib/agent_sync.py` (Ziel-Auflösung `target_dir = project_root / pc['agents_dir']`, jetzt `:483`; Issue-Anker `:417` veraltet)
- [ ] Step 1: Spec (Option A, dünnes Target): Provider-Eintrag (Capability-Flags, `fanout_mechanism`, `barrier_collect`, `provider_root_dirs`), Bootstrap-Eintrag, Projekt-Opt-in `hermes-export`, Stale-File-Cleanup über `.agent-meta-managed`, Konsumentenvertrag (Tier-zu-Modell, Installpfad, Refresh, Contracts-zu-Harness). Ohne Modell-IDs im Pack.
- [ ] Step 2: Review/Freigabe. Verifikation wie Task 0a.
- [ ] Step 3: commit `docs: add spec for Hermes provider target (#800)`
Sperre für Task 8: bis Status APPROVED und G-N1 final (Probe-Evidenz, Gate; Probe-Art siehe "Offene Entscheidungen (neu, ungeklaert)").

### Task 0c: Spec/ADR Gemini-Zielplattform + Commands→Skills (Spec-Gate 3)
**Agent:** requirements
**Files:** Create `docs/specs/2026-11-11-gemini-target-platform-spec.md`
**Interfaces:** Produces: freigegebene Spec für #1160 Schritt 2/3, #1171, #854; Consumes: Probe-Evidenz aus Task 5 (Gemini-CLI-Teil ggf. unabhängig von `agy`: ob die `gemini`-CLI auf diesem Host läuft, ist nicht verifiziert)
- [ ] Step 1: Spec: Entscheidung G-N3 (Gemini CLI Default, Antigravity opt-in; final nach Probe-Evidenz; vormals N3), Tool-/Hook-/Ablageort-Vokabular je Oberfläche, Umzug `.gemini/commands/*.toml` zu `.gemini/skills/<name>/SKILL.md` (Entscheidung 10; nur nach Runtime-Probe #860, Task 5), Behandlung der Gemini-CLI-Custom-Commands (laut `docs/analysis/2026-09-30-provider-audit-docs-part1.md:132` ein gültiges Gemini-CLI-Format, kein Antigravity-Vertrag), Migrationspfad (alte TOML über `.agent-meta-managed` entfernen).
- [ ] Step 2: Freigabe. Sperre: Task 5 abgeschlossen oder ausdrücklich per User auf "nur Gemini CLI ohne Probe" reduziert.
- [ ] Step 3: commit `docs: add spec for Gemini target platform and skills (#1160)`
Sperre für Task 9 und 10.

---

### Task 1: #800 — Hermes-Export fail-closed ohne PyYAML (S, sofort)
**Agent:** developer
**Files:** Modify `scripts/hermes_export.py`; Modify `tests/test_hermes_export.py`
**Interfaces:** Consumes: `scripts/hermes_export.py::export_skill_pack(agent_meta_root: Path, output_dir: Path, roles: list[str] | None = None, tier_overrides: dict[str, str] | None = None, dry_run: bool = False) -> dict` (`:486-492`, Modul hat `from __future__ import annotations` `:85`; liest `load_roles_config` bei `:542`), Modulflag `_YAML_AVAILABLE` (`:98-102`), `main()` fängt `(ValueError, FileNotFoundError, RuntimeError, OSError)` und gibt 1 zurück (`:679-681`). Produces: `export_skill_pack` wirft `RuntimeError("PyYAML required ...")` vor jeder Dateiausgabe, wenn `_YAML_AVAILABLE` falsch ist.
- [ ] Step 1: Roter Test in `tests/test_hermes_export.py` (Klasse nach Muster `TestExportSkillPackMiniRepo`, Fixture `mini_meta` `:122`):
  ```python
  def test_missing_pyyaml_fails_closed(self, mini_meta, tmp_path, monkeypatch, capsys):
      monkeypatch.setattr(hermes_export, "_YAML_AVAILABLE", False)
      out = tmp_path / "pack"
      with pytest.raises(RuntimeError, match="PyYAML"):
          hermes_export.export_skill_pack(mini_meta, out)
      assert not (out / "manifest.yaml").exists()

  def test_main_exits_nonzero_without_pyyaml(self, mini_meta, tmp_path, monkeypatch, capsys):
      monkeypatch.setattr(hermes_export, "_YAML_AVAILABLE", False)
      monkeypatch.setattr(sys, "argv", ["hermes_export.py", "--root", str(mini_meta), "--output", str(tmp_path / "p")])
      assert hermes_export.main() == 1
      assert "PyYAML" in capsys.readouterr().err
  ```
  Platzierung: erster Test in `TestExportSkillPackMiniRepo` (`:245`), zweiter in `TestCli` (`:565`, dort Helfer `_run_main` nutzen). Der Monkeypatch betrifft nur `hermes_export._YAML_AVAILABLE`, nicht den Loader in `scripts/lib/io.py`; der Export läuft also heute durch (Plan-Erwartung, nicht ausgeführt).
  Verifikation rot: `python3 -m pytest tests/test_hermes_export.py -k "fails_closed or without_pyyaml" -q` → 2 failed (kein RuntimeError bzw. `main()` gibt 0 zurück).
- [ ] Step 2: Implementierung: als erste Anweisung von `export_skill_pack` nach dem Docstring (vor `generic_dir = ...` `:512`; Docstring-Abschnitt `Raises:` um `RuntimeError` ergänzen) `if not _YAML_AVAILABLE: raise RuntimeError("PyYAML required to read config/role-defaults.yaml; run: pip install pyyaml (or: uv run --with pyyaml python3 scripts/hermes_export.py ...)")`. Kein `tier: balanced`-Fallback für nicht lesbare Metadaten. `--require-metadata` aus dem Issue wird bewusst nicht gebaut (Zusatzwunsch "optional", durch den Fail-closed-Pfad überflüssig; als Abweichung im Spec 0b festzuhalten).
- [ ] Step 3: grün: `python3 -m pytest tests/test_hermes_export.py -q` (alle bestehenden Tests inkl. Modell-ID-Scan bleiben grün; Erwartung: keine Regression, da PyYAML in Testumgebung vorhanden ist).
- [ ] Step 4: commit `fix: fail closed in hermes export when PyYAML is missing`

### Task 2: #1171 — Konsistenztest Toolvokabular Gemini (xfail strict, nach B)
**Agent:** tester
**Files:** Create `tests/test_gemini_tool_vocabulary_consistency.py`
**Interfaces:** Consumes: `config/ai-providers.yaml` (`Gemini.bash_tool_name` `:203`, `Gemini.agent-transform.tool-name-map.Bash` `:250`), `config/provider-tools.yaml` (`terminal_tool.Gemini` `:142`); lesbar über `scripts/lib/providers.py::load_providers_config` (Aufruf in `scripts/lib/viz.py:711-712`) und `scripts/lib/frontmatter.py::load_provider_tools_config` (`viz.py:699-700`). Produces: pinnt die Invariante, ohne den Wert zu ändern.
- [ ] Step 1: Test schreiben, `@pytest.mark.xfail(strict=True, reason="#1171 pending #1160 target decision")`:
  ```python
  def test_bash_vocabulary_is_single_per_gemini_surface():
      pc = load_providers_config(ROOT)["Gemini"]
      mapped = pc["agent-transform"]["tool-name-map"]["Bash"]
      terminal = load_provider_tools_config(ROOT)["terminal_tool"]["Gemini"]
      assert pc["bash_tool_name"] == terminal == mapped
  ```
  Aktuell: `code_execution == code_execution != run_command` → Assertion schlägt fehl, xfail erwartet das.
- [ ] Step 2: zweiter, nicht xfail-Test: für jeden Provider mit nicht leerem `tool-name-map["Bash"]` ist `terminal_tool[<Provider>]` ebenfalls gesetzt (Datengetrieben über die YAML-Schlüssel, kein Providername im Test-Code). Erwartung grün: statisch geprüft gegen `origin/main` `config/ai-providers.yaml`, nur Gemini hat `tool-name-map["Bash"]` (`run_command`, `:250`), `terminal_tool` (`config/provider-tools.yaml:139-148`) hat alle 9 Provider.
- [ ] Step 3: `python3 -m pytest tests/test_gemini_tool_vocabulary_consistency.py -q` → 1 xfailed, 1 passed.
- [ ] Step 4: commit `test: pin gemini terminal tool vocabulary invariant (#1171)`
Hinweis Wirkung: In W liest nur `scripts/lib/viz.py::_get_terminal_tool` (`:689-712`) die Namen (Prompt-Text für das Viz-Fallback). Die Guards bekommen über den Hook-Adapter bereits normalisierte Namen (`tests/test_antigravity_hooks_registration.py:361` `run_command -> Bash`; `tests/test_hook_common_lib.py:375`). Das beantwortet AC 2 von #1171 für Guards statisch; Laufzeit unverifiziert.

### Task 3: #1175 — Evidenz im Opencode-Allow-list-Kommentar festhalten (S)
**Agent:** developer
**Files:** Modify `config/ai-providers.yaml` (Kommentar `:399-405`); Create `tests/test_opencode_options_passthrough_note.py`
**Interfaces:** Consumes: `Opencode.agent-transform.allowed-fields` (`config/ai-providers.yaml:387-414`), Evidenzdatei `docs/analysis/evidence/2026-09-30-runtime-opencode-v1.md`. Produces: dokumentierter Stand "Harness VERIFIED, Provider-Request UNVERIFIED, Probe-Runbook verlinkt".
- [ ] Step 1: roter Test:
  ```python
  def test_opencode_allowlist_documents_provider_request_gap():
      text = (ROOT / "config/ai-providers.yaml").read_text(encoding="utf-8")
      assert "#1175" in text
      assert "opencode-request-options-probe" in text
  def test_opencode_allowlist_keeps_three_keys():
      fields = load_providers_config(ROOT)["Opencode"]["agent-transform"]["allowed-fields"]
      assert {"version", "prompt_mode", "generated-from"} <= set(fields)
  ```
  Der zweite Test ist bereits grün (Absicherung), der erste rot.
- [ ] Step 2: Kommentar ergänzen: "Provider-seitige Weitergabe der Keys als Request-Optionen UNVERIFIED (#1175); Probe: docs/analysis/runbooks/opencode-request-options-probe.md". Keine Wertänderung: die drei Keys bleiben (Entscheidung 34, G-N4; final erst nach Probe-Evidenz, Task 6).
- [ ] Step 3: `python3 -m pytest tests/test_opencode_options_passthrough_note.py -q` grün; `python3 scripts/sync.py --validate` grün.
- [ ] Step 4: commit `docs: record opencode options passthrough evidence gap (#1175)`

### Task 4: #860 — Probe-Runbook Antigravity vorbereiten (S, Doku)
**Agent:** developer
**Files:** Create `docs/analysis/runbooks/antigravity-runtime-probe.md`
**Interfaces:** Produces: ausführbares Runbook; Consumes: Issue-Verdikte G-1, G-2, G-3, G-7, H2, H3 (`docs/analysis/2026-09-30-provider-audit-docs-part1.md:155-156,330`, `docs/analysis/2026-09-30-provider-audit-runtime-consolidation.md:42-43`, nicht neu gelesen)
- [ ] Step 1: Test `tests/test_antigravity_probe_runbook.py` (rot): Datei existiert und enthält die Zeichenfolgen `agy --help`, `G-1`, `G-2`, `G-3`, `G-7`, `H2`, `H3`, `#1032`, "Exit 132".
- [ ] Step 2: Runbook: Vorbedingung `agy --help` Exit 0 auf `pclmul`-fähigem Host (`grep -c pclmul /proc/cpuinfo` ≥ 1) oder echte AGY-IDE-Session; Schritte je Verdikt; Evidenz-Template mit Feldern Host, CPU-Flags, Befehl, Ausgabe (Secrets redigiert), Verdikt.
- [ ] Step 3: grün: `python3 -m pytest tests/test_antigravity_probe_runbook.py -q`
- [ ] Step 4: commit `docs: add antigravity runtime probe runbook (#860)`

### Task 5: #860 — Probe ausführen (BLOCKIERT, extern)
**Agent:** tester
**Files:** Create `docs/analysis/evidence/<datum>-runtime-antigravity-pclmul.md`
**Interfaces:** Consumes: Runbook aus Task 4. Produces: Evidenz, aktualisierte Verdikte, Freigabe der Sperre für Task 0c (und #1032, laut Owner-Kommentar ebenfalls blockiert, nicht in Phase G).
Sperre: erst ausführbar, wenn `agy --help` auf einem Host Exit 0 liefert. Jeder echte Agent-/Provider-Lauf in der Probe erst nach Kostenschätzung und ausdrücklichem User-Ja. Phase A setzt das Label `blocked`. Kein Commit, solange blockiert; Task 5 gehört in G-PR2 (Entscheidungen 17, 52; Kostenfreigabe G-O3 offen); #860 bleibt offen.
- [ ] Step 1: Vorbedingung prüfen (siehe Runbook). Nicht erfüllt → Task bleibt offen, kein Commit.
- [ ] Step 2: Runbook abarbeiten, Evidenz schreiben, Verdikte in `docs/analysis/2026-09-30-provider-audit-docs-part1.md` aktualisieren.
- [ ] Step 3: commit `docs: add antigravity runtime evidence (#860)`

### Task 6: #1175 — Request-Body-Capture-Probe (Recherche/Probe, Opencode-Runtime nötig)
**Agent:** tester
**Files:** Create `docs/analysis/runbooks/opencode-request-options-probe.md`; Create `docs/analysis/evidence/<datum>-runtime-opencode-request-options.md`
**Interfaces:** Consumes: ein generierter Agent `.opencode/agents/<role>.md` mit den drei Keys, lokaler Capture-Proxy oder Provider-Debug-Log (Verfügbarkeit in W nicht geprüft, Opencode-Quelle wurde nicht gelesen). Produces: Request-Payload (Secrets redigiert) und Verdikt "Keys erreichen den Provider: ja/nein".
Sperre: Opencode-Binary und ein Capture-Weg auf dem Host (nicht verifiziert). Step 2 schickt echte Requests an einen Provider: erst nach Kostenschätzung und ausdrücklichem User-Ja (G-O3 offen). Task 6 gehört in G-PR2 (Entscheidung 52).
- [ ] Step 1: Runbook schreiben (Test `tests/test_opencode_probe_runbook.py` prüft Existenz und Stichworte `options`, `request`, `redact`).
- [ ] Step 2: Probe laufen lassen, Payload dokumentieren. Ergebnis macht G-N4 final (Keys bleiben) oder verlangt Neuentscheidung (Sidecar oder streichen).
- [ ] Step 3: G-N4 final in `config/ai-providers.yaml` oder ADR festhalten (Akzeptanzkriterium 2 von #1175).
- [ ] Step 4: commit `docs: record opencode request options probe result (#1175)`

### Task 7: #814 — `cwd`, Unbekannt-Key-Warnung, External-Tool-Modus (M, gesperrt durch Task 0a)
**Agent:** developer
**Files:** Modify `scripts/lib/mcp_provider_config.py`; Modify `tests/test_mcp_config.py`; Modify `config/plugin-catalog.yaml`
**Interfaces:** Consumes: `_build_connection_entry(conn: dict, secrets: dict | None, fmt: str | None = None, *, resolve_interpreter: bool = False) -> dict` (`:187`), Stdio-Zweig `:261-275`, `_build_mcp_entries(...)` (`:292`), `_resolve_stdio_command` (`:167`), Format-Flags `is_opencode` etc. (`:222-227`). Produces: optionaler Eintrag `cwd` (Opencode: `[cmd]+args` plus `cwd`; sonst `command`/`args`/`cwd`), neue reine Funktion `unknown_connection_keys(conn: dict) -> list` (Name vorläufig, Spec 0a legt fest); Modus `config-generated-by` für extern erzeugte Host-Configs (Entscheidung 27, Route b).
Testfälle (konkretisiert nach Spec; Namen jetzt festgelegt):
- [ ] Step 1: rote Tests in `tests/test_mcp_config.py` (Nähe `test_stdio_command_*` `:1078-1102`):
  `test_stdio_cwd_emitted_for_generic_format` (`fmt="claude-settings"`, `conn={"type":"stdio","command":"x","args":[],"cwd":"/abs"}` → `entry["cwd"] == "/abs"`),
  `test_stdio_cwd_emitted_for_opencode_json` (`entry["command"] == ["x"]`, `entry["cwd"] == "/abs"`),
  `test_unknown_connection_key_is_reported` (`unknown_connection_keys({"type":"stdio","command":"x","bogus":1}) == ["bogus"]`),
  `test_catalog_has_no_unknown_connection_keys` (alle Einträge in `config/plugin-catalog.yaml`: Liste leer; verhindert Lärm),
  `test_external_tool_entry_not_activated_silently` (Entscheidung 27: Aktivierung eines `config-generated-by`-Eintrags ist fail-closed bzw. warnt, nie still; Abgrenzung je Fall in Spec 0a).
- [ ] Step 2: implementieren laut Spec; kein `if provider == ...`. Ob ein Format `cwd` unterstützt, kommt aus Daten (Format-Wert), unterstützte Formate je Spec-Matrix.
- [ ] Step 3: `python3 -m pytest tests/test_mcp_config.py -q` und `python3 scripts/sync.py --validate` grün; `python3 scripts/sync.py --check` im Self-Host: erwartet keine Drift der committed Configs (committed Config bleibt hostunabhängig, vgl. Kommentar `:158-163`).
- [ ] Step 4: commit `feat: support cwd in stdio MCP builder (#814)`

### Task 8: #800 — Hermes als Provider-Target (L, gesperrt durch Task 0b und G-N1; Option A, Entscheidung 34)
**Agent:** senior-developer
**Files:** Modify `config/ai-providers.yaml`, `config/provider-bootstrap.yaml`, `config/provider-capabilities.yaml`; Modify `scripts/hermes_export.py` (Sync-Anbindung bei Option A); Create `docs/guides/hermes-integration.md`; Create `tests/test_hermes_provider_target.py`
**Interfaces:** Consumes: Provider-Schema in `config/ai-providers.yaml` (Provider-Registry; `_validate_providers` in `scripts/lib/config.py:717` verwirft unbekannte Provider fail-closed, bleibt so); Produces: `Hermes`-Eintrag mit Capability-Flags `fanout_mechanism: native-batch`, `barrier_collect: true`, `provider_root_dirs`, Projekt-Opt-in `hermes-export`.
- [ ] Step 1: rote Tests (Auswahl): `test_hermes_in_provider_registry` (`"Hermes" in load_providers_config(ROOT)`), `test_validate_green_with_hermes_enabled` (Sync-Lauf mit Hermes in Tmp-Projekt endet 0), `test_hermes_pack_idempotent_and_stale_cleanup` (zweiter Lauf ändert nichts, Fremddatei bleibt, verwaiste verwaltete Datei wird entfernt), `test_no_provider_name_branch` (kein Literal `"Hermes"` in `scripts/lib/*.py` außer Export-Tooling).
- [ ] Step 2: implementieren laut Spec 0b (Option A, Entscheidung 34; Option B entfällt). Modell-IDs bleiben im Pack verboten (bestehender Scan in `tests/test_hermes_export.py`).
- [ ] Step 3: `python3 -m pytest tests/test_hermes_provider_target.py tests/test_hermes_export.py -q`; `python3 scripts/sync.py --validate`.
- [ ] Step 4: commit `feat: add Hermes as provider target (#800)`
Hinweis: Zahlen im Issue (82 Rollen, Description-Längen) nicht nachgemessen.

### Task 9: #1160 Schritt 2/3 und #1171 — Gemini-Vokabular angleichen (gesperrt durch Task 0c, Task 5)
**Agent:** developer
**Files:** Modify `config/ai-providers.yaml` (`Gemini.bash_tool_name`, ggf. `agent-transform.tool-name-map`), `config/provider-tools.yaml` (`terminal_tool.Gemini` `:142`, Kommentar `:41`), `config/provider-capabilities.yaml` (Notizen G4-1..G4-3 `:289-291`); Modify `tests/test_gemini_tool_vocabulary_consistency.py` (xfail entfernen); Modify `tests/test_provider_config_contracts.py` (`_ANTIGRAVITY_TOOL_NAME_MAP`, `"Bash": "run_command"` `:60`)
**Interfaces:** Consumes: Entscheidung 34 (G-N3: Gemini CLI Default, Antigravity opt-in; vormals N3; final nach Probe-Evidenz). Produces: ein Vokabular je Oberfläche; Test aus Task 2 ohne xfail grün.
- [ ] Step 1 (erst nach finaler G-N3): xfail-Marker entfernen → Test rot (strict würde sonst XPASS-Fehler zeigen, erst nach Angleichung).
- [ ] Step 2: Werte laut Spec angleichen (Ziel: Gemini CLI, Antigravity nur opt-in); Guards/Adapter-Tests prüfen (`tests/test_antigravity_hooks_registration.py`, `tests/test_hook_common_lib.py`).
- [ ] Step 3: `python3 -m pytest tests/test_gemini_tool_vocabulary_consistency.py tests/test_antigravity_hooks_registration.py tests/test_provider_config_contracts.py -q`; `python3 scripts/sync.py --validate`.
- [ ] Step 4: commit `fix: align gemini tool vocabulary to one target (#1171)`
- Defaults (Agent-Discovery, Ablageort) werden nur laut Spec 0c geändert, nie vorher (#1160 Vorschlag 3).

### Task 10: #854 — Gemini-Commands auf Skills umziehen (gesperrt durch Task 0c und Task 5, nach B)
**Agent:** senior-developer
**Files:** Modify `scripts/lib/commands.py` (`sync_commands_for_provider` `:147`, Format-Dispatch `:259-266`); Modify `config/ai-providers.yaml` (`Gemini.has_commands`/`commands_dir`/`commands_ext`/`commands_format` `:179-182`, Skills-Ziel `skills_dir: .gemini/skills` `:214`); Create `tests/test_commands_skill_format.py`; Modify `config/provider-capabilities.yaml` (`commands`-Verdikt)
**Interfaces:** Consumes: Spec 0c; Umzug erst nach Runtime-Probe #860 (Entscheidung 10, Task 5); bisherige Formate `markdown|continue|toml` (`commands.py:165-167`, unbekannter Wert wirft einen Fehler `:263-266`). Produces: neues datengesteuertes `commands_format: skill` (Ordner `<name>/SKILL.md`, Frontmatter `name`/`description`), Cleanup alter `.gemini/commands/*.toml` über das Managed-Index-Muster.
- [ ] Step 1: rote Tests: `test_skill_format_writes_folder_per_command` (Ausgabe `<dir>/<stem>/SKILL.md`), `test_old_toml_commands_removed_via_managed_index`, `test_unknown_commands_format_still_fails`, `test_no_provider_name_branch_in_commands_py`.
- [ ] Step 2: implementieren; Provider-Verhalten nur über `commands_format`.
- [ ] Step 3: `python3 -m pytest tests/test_commands_skill_format.py tests/test_commands_requires_roles.py -q`; `python3 scripts/sync.py --validate`.
- [ ] Step 4: commit `feat: emit gemini commands as skills (#854)`

## Ausführungsreihenfolge

Sofort nach Wellenstart (entscheidungsfrei): Task 1, 2 (nach B), 3, 4, dann 0a, 0b parallel zu Spec-Arbeit. Probe-gesperrt: 5, 6, 0c, 9, 10. Spec-gesperrt: 7 (0a), 8 (0b). Dateikonflikt: `config/ai-providers.yaml` wird von Task 3, 8, 9, 10 berührt, daher strikt sequentiell (3 vor 8 vor 9 vor 10); `scripts/lib/mcp_provider_config.py` nur Task 7.

Merge-Reihenfolge (Entscheidung 56, O-H7): G merged vor H.

### PR-Schnitt (Entscheidung 52)

Stand der Sperren laut Task-Texten (2026-11-11). G-PR1 wird ohne die gesperrten Tasks gemergt; G-PR2 wird auf den gemergten G-PR1 rebased und erst geöffnet, wenn mindestens ein gesperrter Task entsperrt ist. Fallen nicht alle Sperren, enthält G-PR2 nur die entsperrten Tasks; ein dritter PR ist nicht vorgesehen (max. 2 PRs je Phase), Rest-Tasks bleiben offen.

| PR | Task | Issue | Status heute | Sperre / Voraussetzung |
|---|---|---|---|---|
| G-PR1 | Task 1 | #800 (fail-closed) | ausführbar | — |
| G-PR1 | Task 2 | #1171 | ausführbar nach Phase B (Welle vor G) | Phase B gemergt |
| G-PR1 | Task 3 | #1175 | ausführbar | — |
| G-PR1 | Task 4 | #860 | ausführbar | — |
| G-PR1 | Task 0a | #814 | Step 1 ausführbar; Commit (Step 3) erst nach Freigabe | Fehlt die Freigabe beim Merge von G-PR1, wandert der Commit in G-PR2 |
| G-PR1 | Task 0b | #800 | Step 1 ausführbar; Commit (Step 3) erst nach Freigabe | wie 0a; Probe-Art/Evidenzpfad (G-O1) offen |
| G-PR2 | Task 5 | #860 | gesperrt | extern (`agy --help` Exit 0), Kostenfreigabe (G-O3) |
| G-PR2 | Task 6 | #1175 | gesperrt | Opencode-Runtime + Capture-Weg, Kostenfreigabe (G-O3) |
| G-PR2 | Task 0c | #1160, #1171, #854 | gesperrt | Task 5 oder User-Reduktion "nur Gemini CLI ohne Probe" |
| G-PR2 | Task 7 | #814 | spec-gesteuert | Task 0a APPROVED |
| G-PR2 | Task 8 | #800 | gesperrt | Task 0b APPROVED, G-N1 final (Probe-Evidenz, G-O1) |
| G-PR2 | Task 9 | #1160, #1171 | gesperrt | Task 0c, Task 5, G-N3 final |
| G-PR2 | Task 10 | #854 | gesperrt | Task 0c, Task 5 |

Phasenübergreifend (Review 2026-11-11, gegen die Phasenpläne in `docs/superpowers/plans/`):
- Phase H läuft laut Roadmap §3 parallel zu G, die Dateilisten sind aber nicht disjunkt: H Task 8 (Mini-Spec, O-H1, Capability-Flag `roster_in_harness`) legt einen Flag-Ort in `config/provider-capabilities.yaml` oder `config/ai-providers.yaml` fest (H-Plan `:96`), H Task 24 (F-OC2, H-Plan `:347-349`) liest die Opencode-Allow-list in `config/ai-providers.yaml` (dieselbe Stelle wie Task 3). Roadmap-Regel "parallel nur bei disjunkter `Files:`-Liste": G und H sequentiell oder mit Rebase auf den jeweils gemergten PR.
- Phase D (Welle 3) ändert `config/ai-providers.yaml` (Capability, D-Plan `:253`); Phase B ändert `config/provider-capabilities.yaml` (G4-2-Notiz) und `scripts/lib/provider_transform.py`; Phase C ändert `scripts/lib/mcp_provider_config.py` (`_config_rel_label` und Aufrufer). Alle laufen vor G; Anker von Task 3, 7, 9, 10 danach neu messen.
- #1086i (`context.py`-Split) berührt G nicht.

## Frische-Check-Referenzen

- scripts/hermes_export.py
- scripts/hermes_export.py::export_skill_pack
- scripts/hermes_export.py::resolve_abstract_tier
- scripts/hermes_export.py::collect_role_meta
- scripts/hermes_export.py::main
- scripts/hermes_export.py::_YAML_AVAILABLE
- scripts/lib/roles.py::load_roles_config
- scripts/lib/io.py
- scripts/lib/config.py
- scripts/lib/config.py::_validate_providers
- scripts/lib/viz.py::_get_terminal_tool
- scripts/lib/providers.py::load_providers_config
- scripts/lib/frontmatter.py::load_provider_tools_config
- scripts/lib/provider_transform.py::_map_claude_tools_to_gemini_tools
- scripts/lib/mcp_provider_config.py
- scripts/lib/mcp_provider_config.py::_build_connection_entry
- scripts/lib/mcp_provider_config.py::_build_mcp_entries
- scripts/lib/mcp_provider_config.py::_resolve_stdio_command
- scripts/lib/plugins.py
- scripts/lib/commands.py::sync_commands_for_provider
- scripts/lib/agent_sync.py
- config/ai-providers.yaml
- config/provider-tools.yaml
- config/provider-capabilities.yaml
- config/provider-bootstrap.yaml
- config/plugin-catalog.yaml
- config/role-defaults.yaml
- tests/test_hermes_export.py
- tests/test_mcp_config.py
- tests/test_commands_requires_roles.py
- tests/test_antigravity_hooks_registration.py
- tests/test_hook_common_lib.py
- tests/test_provider_config_contracts.py
- tests/test_gemini_tool_vocabulary_consistency.py
- tests/test_opencode_options_passthrough_note.py
- tests/test_antigravity_probe_runbook.py
- tests/test_opencode_probe_runbook.py
- tests/test_hermes_provider_target.py
- tests/test_commands_skill_format.py
- docs/analysis/evidence/2026-09-30-runtime-opencode-v1.md
- docs/analysis/2026-09-30-provider-audit-docs-part1.md
- docs/analysis/2026-09-30-provider-audit-runtime-consolidation.md
- docs/analysis/runbooks/antigravity-runtime-probe.md
- docs/analysis/runbooks/opencode-request-options-probe.md
- docs/guides/hermes-integration.md
- docs/specs/2026-11-11-814-mcp-stdio-cwd-spec.md
- docs/specs/2026-11-11-800-hermes-provider-target-spec.md
- docs/specs/2026-11-11-gemini-target-platform-spec.md
- knowledge/wiki/concepts/provider-agnostic-policy.md
- #854
- #860
- #1160
- #1165
- #1171
- #1175
- #800
- #814
- #1170
- #1032
- #1094
- #527
- #1218 (gemergt, origin/main 9aa0e0c0)

## Nicht verifiziert

- Keine Tests und kein `--validate` ausgeführt; rote/grüne Erwartungen sind Plan-Werte. `check_plan_refs.py` lief im Review (2026-11-11). Skill `provider-agnostic` ist nicht versioniert (generiert, liegt nur im Main-Checkout unter `.claude/skills/`), daher Verweis auf die Wiki-Seite. Graphify-Hook verlangte `graphify query`, das Werkzeug stand nicht zur Verfügung; Orientierung nur per Grep/Read.
- Opencode-Quelle nicht gelesen; Aussagen zu `options`-Bucket stammen aus der Evidenzdatei, nicht aus Opencode-Code. Ob ein Capture-Weg für Request-Bodies existiert, ungeprüft.
- Antigravity-Runtime (`agy`) nicht verfügbar; `pclmul`-Status dieses Hosts nicht geprüft; ob die `gemini`-CLI separat probebar ist, ungeprüft.
- `cwd`-Unterstützung der Zielformate (`.mcp.json`, Opencode, weitere) nur aus dem Issue-Text, nicht aus Herstellerdoku; Spec 0a muss das belegen.
- Wo ein Warn-/Validierungslauf für unbekannte `connection`-Keys sinnvoll sitzt (Schreibpfad in `mcp_provider_config.py` jenseits `:320` nicht gelesen); `scripts/lib/plugins.py` hat keinen Validator (nur `probe_plugin_availability` `:77`).
- Messzahlen in #800 (82 Rollen, Description-Längen) nicht nachgemessen; Hermes-seitige Fakten (Skill-Discovery, `delegate_task`) nur aus dem Issue.
- Bezug von Phase G zum #1085/#1155-Flag aus Phase C: nicht begründet in der Roadmap, hier übernommen.
- Provider-Cache in `load_roles_config` (Prozess-Cache laut Docstring `scripts/lib/roles.py:56-59`): Tests nutzen frische Tmp-Roots wie in `tests/test_hermes_export.py`; das Verhalten bei `monkeypatch` von `_YAML_AVAILABLE` wurde nicht gelaufen.
- Probe-Art und Evidenzpfad für G-N1 (#800) sind in Entscheidung 34 nicht benannt; nicht geraten, siehe "Offene Entscheidungen (neu, ungeklaert)".

## Self-Review

- Jeder der 7 Issues genau einmal: #860 (Task 4, 5), #1175 (Task 3, 6), #1160 (Task 0c, 9), #1171 (Task 2, 9), #854 (Task 0c, 10), #800 (Task 0b, 1, 8), #814 (Task 0a, 7).
- Spec-Gates: 3 (Task 0a, 0b, 0c); M/L/XL-Tasks (7, 8, 9, 10) sind bis Freigabe nicht ausführbar; S-Tasks (1 bis 4) direkt.
- Signaturen mit Datei:Zeile aus W belegt: `_build_connection_entry` (`mcp_provider_config.py:187`), `_resolve_stdio_command` (`:167`), `export_skill_pack` (`hermes_export.py:486-492`), `main` (`:655`), `resolve_abstract_tier` (`:217`), `load_roles_config` (`roles.py:53`), `_get_terminal_tool` (`viz.py:689`), `sync_commands_for_provider` (`commands.py:147`). Neue Symbole (`unknown_connection_keys`, `commands_format: skill`) sind als "Produces" markiert.
- Keine TBD/TODO-Platzhalter außer ausdrücklich gesperrten, benannten Gates; N1 bis N4 sind über 17-34 beantwortet (G-N1, G-N3, G-N4 vorläufig final bis Probe-Evidenz); ungeklärt bleibt nur die Liste "Offene Entscheidungen (neu, ungeklaert)".
- PR-Schnitt (Entscheidung 52): G-PR1 = Task 1, 2, 3, 4 (+ 0a/0b bei Freigabe); G-PR2 = Task 5, 6, 0c, 7, 8, 9, 10 (+ 0a/0b ohne Freigabe). G-O2 beantwortet; G-O1, G-O3 offen.
- Entscheidungen eingearbeitet: 10 (#854 erst nach #860), 17 (ein Commit je Task), 52 (max. 2 PRs je Phase), 25 (Trailer verbatim vom Task-Prompt), 27 (#814 Route b; N2 erledigt), 34 (G-N1 Option A, G-N3 Gemini CLI Default, G-N4 Keys bleiben; Gate Probe-Evidenz explizit).
- Provider-Differenzen nur über Config-Keys/Format-Werte; Test auf Provider-Namensliteral in Task 8/10.
