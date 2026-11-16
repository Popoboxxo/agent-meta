# Temp-Root-Determinismus und ReqogniLoom-Doppel-Einbindung — Spec
> Status: DRAFT (noch nicht freigegeben)
> Datum: 2026-11-16 | Plan: `docs/plans/2026-11-14-bugfix-batch-3-plan.md` (PR 3, Tasks 3.1-3.3) | Entscheidungen: E-02 (#1246, Variante B+), E-09 (#1261, nur WARN) | Refs #1246, #1261
> Klasse: M (Schema-Key, 2 Lib-Module, neuer Check, 4 Testdateien)

## Problem / Ziel / Nicht-Ziele

### Problem

**#1246 — Basetemp hängt von `TMPDIR` ab.** `PYTEST_BASETEMP` wird in `scripts/lib/config.py:2134` aus `resolve_tmp_paths(...)` injiziert. `scripts/lib/tmp_paths.py:252-258` (`resolve_pytest_basetemp`) ruft `rc.system_temp_root(...)`; dieses liefert in `scripts/lib/repo_containment.py:635` `tempfile.gettempdir()` verbatim zurück (Zweig `:644`), solange der Wert nicht der Sink ist. `gettempdir()` honoriert `TMPDIR`/`TEMP`/`TMP`. Folge: Der gerenderte Pfad (`<root>/<user>/pytest-agent-meta`) in 12 Agent-Dateien und `.claude/settings.local.json` ist je nach Shell-Umgebung `/var/tmp/...` oder `/tmp/...`; `sync.py --check` meldet Drift (laut Issue 13 Dateien vs. 0).

**#1261 — ReqogniLoom doppelt.** `config/plugin-catalog.yaml:151` definiert den Katalog-Server `reqogniloom` (Env `MCP_REQOGNILOOM_*`, `:249-256`). Parallel kann das externe Claude-Plugin (`REQOGNILOOM_MCP_URL`) aktiv sein. Beide laufen, jeder braucht eigene Env-Variablen; fehlende Variablen führen zu `INVALID_CONFIG`. Heute existiert nur ein Prosa-Hinweis (`plugin-catalog.yaml:245`), kein Laufzeit-Check.

### Ziele

- Gerenderter Basetemp ist unabhängig von `TMPDIR`/`TEMP`/`TMP` der aufrufenden Shell.
- Neuer optionaler Config-Key `temp-root` erlaubt Projekten, den Root explizit zu pinnen (agent-meta selbst: `/var/tmp`, damit Render byte-identisch bleibt, kein Rebaseline, Nutzer-Allowlist `/var/tmp/hermes/pytest-agent-meta` bleibt gültig).
- Sync gibt genau eine WARN mit Handlungsanweisung aus, wenn ReqogniLoom als externes Plugin UND als Katalog-Server aktiv ist.

### Nicht-Ziele

- Keine Harmonisierung der Env-Namen/Auth (`REQOGNILOOM_*` vs. `MCP_REQOGNILOOM_*`) — Server-Verhalten unverifiziert (E-09).
- Kein automatisches Deaktivieren des Katalog-Servers, kein Hard-Fail.
- Kein neues Plugin-Provider-Konzept über das eine Capability-Flag hinaus; kein Provider-Literal im Syncer.
- Keine Änderung an `toolchain-caches`-Semantik und am Sink-Pfad (`tmp-sink.path`).
- Keine Closing-Keywords in Commits/PR (nur `Refs #1246, #1261`).

## Verifizierte Code-Befunde (Worktree `.tmp/wt-batch3-pr3`)

1. **Schema-Ort.** `system-temp-exception` ist **kein** Top-Level-Key und liegt nicht unter `viz.properties`, sondern verschachtelt: `repo_containment` (`config/project-config.schema.json:2746`) → `properties.tmp-sink` (`:2767`) → `properties.system-temp-exception` (`:2795`, `additionalProperties: false` auf `:2825`-Ebene). Unterkeys: `enabled`, `reason`, `pytest-basetemp`, `toolchain-caches`. Ein neuer Key `temp-root` muss dort ergänzt werden, sonst lehnt das Schema ihn ab.
2. **Leser.**
   - Validierung/Matrix: `scripts/lib/config.py:893-960` (Typprüfung `:903-910`, `enabled`/`reason`-Regeln `:911-932`, Aufruf `system_temp_root` `:940`, Inside-Project-Check `:947`).
   - Auflösung: `scripts/lib/repo_containment.py:621-663` `system_temp_root(project_root, sink_dir)`; Kandidaten `_candidate_temp_dirs()` (`:~600-618`, enthält `/tmp`, `/var/tmp`, `/usr/tmp`).
   - Builder: `scripts/lib/tmp_paths.py:231-258` `resolve_pytest_basetemp`; `_system_temp_basetemp` `:219-221` hängt `<user>/pytest-agent-meta` an; `resolve_tmp_paths` ruft den Resolver am Ende (`:~202`).
   - Injektion: `scripts/lib/config.py:2119-2134` (`variables["PYTEST_BASETEMP"]`), Token-Ersatz `:774-788`.
   - Weitere Konsumenten von `TmpSinkError`/Resolver: `doctor_detectors.py:429`, `provider_transform.py:290`, `consistency/temp_literals.py:484`. Diese bleiben unverändert (Fehlercode `tmp-sink.system-temp-exception` bleibt).
   - Consumer-Konfig agent-meta: `.meta-config/project.yaml:398-407`.
3. **Doppel-Erkennung (Hook-Punkt).**
   - `scripts/lib/mcp_health.py:42` `check_mcp_health(agent_meta_root, project_root, config, log, env=None)` lädt Registry und aktive Server (`resolve_active_mcp_servers`, `registry_query.py:~140-172`) und ist bereits advisory (`except Exception` → `log.debug`, "never breaks the sync"). Aufgerufen genau einmal: `scripts/lib/sync_pipeline.py:378`. Das ist der natürliche Hook-Punkt: aktive Server stehen bereits bereit.
   - `scripts/lib/mcp.py` rendert Artefakte (`generate_mcp_artifacts`), ist für einen Read-only-Check ungeeignet; `registry_query.py` liefert nur die Aktivmenge.
   - `config/provider-capabilities.yaml` enthält kein Plugin-System-Flag (Treffer für "plugin" nur Runtime-Gate/Agent-Discovery). `config/ai-providers.yaml:1-12` (`providers.Claude`) trägt providerweise Werte-Keys ohne Code-Verzweigung (`surface-version`, `agent-discovery`, `model-format`); Defaults in `scripts/lib/providers.py:~384` (`settings_file: .claude/settings.json`). Hier gehört das neue Flag hin.
   - Kein bestehender Code liest `enabledPlugins` oder `external_plugins_file` (Grep über `scripts config docs`: nur der Plan).

## Interface Contracts

### IC-1: Schema-Key `temp-root`

- Ort: `repo_containment.tmp-sink.system-temp-exception.temp-root` in `config/project-config.schema.json` (nach `:2820`).
- Typ: `string`, optional, **ohne `default`** (damit `fill_defaults()` — `config.py:1321`, vgl. `_SYNC_SKIPPED_DEFAULT_KEYS` `:184` — den Key nie in Consumer-`project.yaml` schreibt; Kommentar-Verlust #1074).
- Semantik: absoluter Pfad des Platform-Temp-Roots für den pytest-Basetemp (`<temp-root>/<user>/pytest-agent-meta`).
- Validierung (`config.py` im Block `:893-960`, ein `_fail`):
  - Typ ≠ str oder leer → Fehler `invalid '...system-temp-exception.temp-root': expected a non-empty string`.
  - Nicht absolut (`os.path.isabs`) → Fehler; Builder-Ebene: `TmpSinkError("tmp-sink.system-temp-exception", ...)`.
  - Enthält `"`, `\n`, `\r` → Fehler (Einbettung `--basetemp="<path>"`, bestehende Prüfung `tmp_paths.py:266`).
  - Liegt innerhalb des Projekt-Roots → Fehler (bestehender Inside-Check `config.py:947` gilt auch für den expliziten Wert).
  - Nur zusammen mit `enabled: true` und `pytest-basetemp: true` wirksam; sonst ignoriert (kein Fehler).

### IC-2: `system_temp_root(project_root, sink_dir, explicit_root=None) -> str`

- Datei: `scripts/lib/repo_containment.py:621`. Neuer optionaler Parameter, rückwärtskompatibel.
- Präzedenz:
  1. `explicit_root` gesetzt → validiert zurückgeben (absolut, existierendes Verzeichnis, nicht Sink, nicht im Projekt; sonst `TmpSinkError("tmp-sink.system-temp-exception", ...)`).
  2. sonst **env-freier Default**: erster Kandidat aus plattformspezifischer Liste ohne `TMPDIR`/`TEMP`/`TMP` (Linux/macOS: `/tmp`, dann `/var/tmp`, `/usr/tmp`; Windows: bisheriges Verhalten über `_candidate_temp_dirs()`), gleiche Filter wie heute (absolut, existiert, nicht Sink, nicht im Projekt).
  3. kein Kandidat → `TmpSinkError` wie heute (Meldung ohne den Hinweis "set TMPDIR", stattdessen "set temp-root").
- Der Pin-Fall (`gettempdir()` == Sink, `:644`) entfällt als Sonderpfad, weil `TMPDIR` nicht mehr gelesen wird.
- Offene Umsetzungsentscheidung: Windows behält `gettempdir()` (siehe Offene Fragen Q2).

### IC-3: `resolve_pytest_basetemp(project_root, paths)`

- Datei: `scripts/lib/tmp_paths.py:231`. Beide Zweige, die `rc.system_temp_root` rufen (`:252`, `:257`), reichen `paths.system_temp_exception.temp_root` durch.
- `TmpSystemTempException` (Dataclass in `tmp_paths.py`) erhält Feld `temp_root: Optional[str] = None`; `resolve_tmp_paths` befüllt es aus dem Config-Mapping.
- Docstring-Präzedenz-Liste um "explizites `temp-root` vor env-freiem Default" ergänzen.

### IC-4: Capability-Flag `external_plugins_file`

- Ort: `config/ai-providers.yaml`, pro Provider optional; Claude: 
  ```yaml
  external_plugins_file:
    path: ~/.claude/settings.json
    enabled_key: enabledPlugins
  ```
  Provider ohne Flag: Check entfällt (kein `if provider`).
- Katalog-Ergänzung `config/plugin-catalog.yaml` (Eintrag `reqogniloom`, `:151`): optionales Feld `external-plugin-id-prefix: reqogniloom@` (Präfix-Match auf die Schlüssel von `enabledPlugins`). Plugin-ID steht nur im Katalog, nicht im Syncer-Code.
- Schema: beide Strukturen in den jeweiligen Schemas/Registry-Validatoren zulassen (`additionalProperties`-Prüfung beachten; bei Umsetzung `--validate` laufen lassen).

### IC-5: `check_external_plugin_duplicates(...)`

- Datei: `scripts/lib/mcp_health.py` (neue Funktion, Aufruf am Ende von `check_mcp_health`, nach der Aktivmengen-Berechnung; best-effort, im vorhandenen `except Exception`-Schutz bzw. eigener Schutz).
- Signatur: `(registry: dict, active: list[str], provider_cfgs: Mapping, log: SyncLog, home: Optional[Path] = None) -> None`; `home` für Tests (Default `Path.home()`).
- Ablauf: je aktivem Server mit `external-plugin-id-prefix` und je aktivem Provider mit `external_plugins_file`: Datei lesen (JSON, read-only, `~` expandieren), `enabled_key`-Mapping prüfen, Schlüssel mit Präfix und Wert `true` → genau eine `log.warn`-Meldung je Server/Provider: Server-Name, Fundstelle, Handlungsanweisung ("Katalog-Server in `plugins:` mit `enabled: false` deaktivieren oder Plugin deaktivieren; sonst beide Env-Variablensätze setzen").
- Fehlerpfade: Datei fehlt, unlesbar, kein JSON, Key fehlt/falscher Typ → keine WARN, nur `log.debug` (best-effort). Niemals Exception nach außen, niemals Schreibzugriff, niemals Exit-Code-Änderung.
- Kein Aufruf bei `--dry-run`-Sonderbehandlung nötig (read-only).

### IC-6: Doku-Verweise

- `config/plugin-catalog.yaml:245` Prosa und Skill `mcp-reqogniloom` (laut Plan `SKILL.md:95`; im Worktree nicht vorhanden, da `.claude/skills` generiert/untracked — Quelle bei Umsetzung ermitteln) verweisen auf den Sync-Check.

## Datenfluss

**#1246:** `project.yaml` → `config.py` Validierung (`:893-960`, inkl. `temp-root`) → `resolve_tmp_paths` (`tmp_paths.py`) → `resolve_pytest_basetemp` → `system_temp_root(explicit_root=...)` → `<root>/<user>/pytest-agent-meta` → `variables["PYTEST_BASETEMP"]` (`config.py:2134`) → Render in Agent-Templates und `settings.local.json` → Hash in `generated-file-hashes.json`. `TMPDIR` fließt nirgends mehr ein.

**#1261:** Sync → `sync_pipeline.py:378` `check_mcp_health` → Aktivmenge (`resolve_active_mcp_servers`) → je Server mit `external-plugin-id-prefix` + je Provider mit `external_plugins_file` → Datei lesen → Treffer → `log.warn`.

## Task-3.1-Reproduktion (nur Beschreibung, nicht ausgeführt)

Auf frischem Branch, Konfig wie im Worktree:

```
TMPDIR=/var/tmp python3 scripts/sync.py --check --config <worktree>/.meta-config/project.yaml
TMPDIR=/tmp     python3 scripts/sync.py --check --config <worktree>/.meta-config/project.yaml
```

Beide Ausgaben nach `.tmp/plans/scratch/1246-repro.txt`. Erwartet (Issue): erster Lauf 0 abweichende Dateien (committeter Hash enthält `/var/tmp/hermes/pytest-agent-meta`), zweiter Lauf 13 (12 Agent-Dateien + `settings.local.json`) mit Pfad `/tmp/<user>/pytest-agent-meta`. Zusatzbeobachtung: `PYTEST_BASETEMP` im gerenderten `.claude/agents/tester.md:45`. Wenn beide Läufe 0 Drift zeigen, Issue als "nicht reproduzierbar" kommentieren und IC-1 bis IC-3 entfallen. Hinweis: `--check` ist dry-run-artig; trotzdem im Worktree (nicht im Hauptcheckout) ausführen.

## Acceptance Criteria

1. AK-1: `system_temp_root` liefert für `TMPDIR=/var/tmp` und `TMPDIR=/tmp` (monkeypatch) und ohne `explicit_root` dasselbe Ergebnis.
2. AK-2: Mit `explicit_root="/var/tmp"` ist das Ergebnis `/var/tmp` unabhängig von `TMPDIR`.
3. AK-3: Relativer `temp-root` führt zu `TmpSinkError` (Code `tmp-sink.system-temp-exception`); in `config.py` zu einem Validierungsfehler mit Key-Pfad.
4. AK-4: `temp-root` innerhalb des Projekt-Roots oder gleich Sink → Fehler.
5. AK-5: `resolve_pytest_basetemp` übernimmt `temp-root` vor dem Default; `basetemp_dirs` (`test_settings_dirs.py`) folgt.
6. AK-6: `fill_defaults()` schreibt `temp-root` nie in eine Consumer-`project.yaml` (Key ohne Schema-Default); bestehender Test zu `fill_defaults`-Byte-Stabilität bleibt grün.
7. AK-7: `.meta-config/project.yaml` setzt `temp-root: /var/tmp`; `sync.py --check` unter `TMPDIR=/tmp` und `TMPDIR=/var/tmp` meldet identisch 0 Drift; `generated-file-hashes.json` unverändert (kein Rebaseline).
8. AK-8: Ohne `temp-root` ändert sich der Render für Projekte ohne `TMPDIR`-Abweichung höchstens auf den env-freien Default; die Änderung ist im CHANGELOG als Verhaltensänderung vermerkt.
9. AK-9: Mit `enabledPlugins: {"reqogniloom@reqogniloom-marketplace": true}` in der (per `HOME` umgeleiteten) Provider-Datei und aktivem Katalog-Server erscheint genau eine WARN mit Handlungsanweisung; ohne Datei, mit `false`-Wert oder deaktiviertem Katalog-Server keine WARN.
10. AK-10: Defekte Datei (kein JSON, falscher Typ) erzeugt keine Exception und keine WARN; Sync-Exit-Code unverändert.
11. AK-11: Kein Provider-Name im Syncer-Code (Grep `if provider ==` im geänderten Code leer); Plugin-ID nur in Katalog/Config.
12. AK-12: `python3 scripts/sync.py --validate`, betroffene Testdateien und `tests/test_context_budgets.py` grün.

## Tests

- `tests/test_tmp_sink_system_temp_root.py` (erweitern): TMPDIR-Unabhängigkeit (AK-1), `explicit_root` (AK-2), Fehlerfälle (AK-3, AK-4).
- `tests/test_tmp_paths_builder.py` (erweitern): `temp-root` wird übernommen, relativ → `TmpSinkError`, Präzedenz.
- `tests/test_settings_dirs.py` (erweitern): `basetemp_dirs` folgt dem expliziten Root.
- Config-Validierung (bestehende Datei zu `system-temp-exception`, bei Umsetzung per `grep -l system-temp-exception tests`): Typ-/Leer-/Absolut-Fälle, `fill_defaults`-Stabilität (AK-6).
- `tests/test_mcp_duplicate_plugin_warning.py` (neu): AK-9, AK-10 mit `tmp_path` als `home`.
- Manuell/PR-Text: Task-3.1-Beleg und AK-7 (zwei `--check`-Läufe).

## Offene Fragen + Risiken

### Offene Fragen

- Q1: Soll der env-freie Default (Variante A-Anteil von B+) auf Linux `/tmp` fest nehmen, oder `/tmp` vor `/var/tmp` priorisieren wie `tempfile` (`_candidate_temp_dirs`)? Vorschlag: Reihenfolge der vorhandenen Liste beibehalten.
- Q2: Windows/macOS: `gettempdir()` beibehalten (nicht env-frei) oder auch dort Liste? macOS `TMPDIR` ist per-User-Verzeichnis `/var/folders/...`, ein env-freier Default `/tmp` ändert dort bestehende Pfade.
- Q3: Wo liegt das Pluginschema — nur im Katalog (`external-plugin-id-prefix`) oder zusätzlich als Config-Override pro Projekt? Vorschlag: nur Katalog.
- Q4: Flag-Form `external_plugins_file` als Mapping (`path` + `enabled_key`) oder nur Pfad mit festem Key? Vorschlag: Mapping, da andere Provider andere Schlüssel haben.
- Q5: Quelle des Skills `mcp-reqogniloom` (Plan zitiert `SKILL.md:95`) im Worktree nicht auffindbar; bei Umsetzung Master-Quelle bestimmen.
- Q6: `--check` auf allen Providern: Soll die WARN auch bei `--dry-run`/`--check` erscheinen? Vorschlag: ja (read-only).

### Risiken

- R1: Env-freier Default ändert den Render für alle Consumer-Projekte mit nicht-`/tmp` `TMPDIR` und ohne `temp-root` (Drift beim nächsten Sync, Rebaseline). Mitigation: CHANGELOG, Doku-Satz, agent-meta selbst pinnt `/var/tmp`.
- R2: Nutzer-Harness-Allowlist (`/var/tmp/hermes/pytest-agent-meta`) läuft ins Leere, falls `temp-root` fehlt oder der Default `/tmp` ist.
- R3: Neuer Schema-Key ohne Default: `--fill-defaults` listet ihn nicht; Admin-UI-Formular muss ihn optional behandeln.
- R4: `~/.claude/settings.json` ist Nutzer-Datei außerhalb des Repos; Lesen ist best-effort, Format kann sich ändern (daher WARN statt Fehler, `log.debug` bei Parse-Fehler).
- R5: Plugin-Marketplace-Name kann abweichen; Präfix-Match `reqogniloom@` ist toleranter als Vollname, kann aber Fremd-Plugins treffen.
- R6: Python 3.9-Kompatibilität (kein `X | Y`, `from __future__ import annotations`); Modulgröße `repo_containment.py`/`mcp_health.py` ≤ 600 Zeilen prüfen.
- R7: Spec-Plan-Abgleich: Plan nennt `ai-providers.yaml`-Flag als Config-Key; Schema-/Registry-Validatoren müssen den neuen Key kennen, sonst `--validate`-Fehler.

## Trace-Anker

spec-id: SPEC-temp-root-and-reqogniloom-duplicate
