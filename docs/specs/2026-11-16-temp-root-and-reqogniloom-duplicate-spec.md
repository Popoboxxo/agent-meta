# Temp-Root-Determinismus und ReqogniLoom-Doppel-Einbindung — Spec
> Status: DRAFT (noch nicht freigegeben)
> Datum: 2026-11-16 | Plan: `docs/plans/2026-11-14-bugfix-batch-3-plan.md` (PR 3, Tasks 3.1-3.3) | Entscheidungen: E-02 (#1246, Variante B+), E-09 (#1261, nur WARN) | Refs #1246, #1261
> Klasse: M (Schema-Key, 2 Lib-Module, neuer Check, 5 Testbereiche: 3 erweiterte Testdateien + Config-Validierungstest + 1 neue Testdatei, siehe Abschnitt Tests)

## Problem / Ziel / Nicht-Ziele

### Problem

**#1246 — Basetemp hängt von `TMPDIR` ab.** `PYTEST_BASETEMP` wird in `scripts/lib/config.py:2134` aus `resolve_tmp_paths(...)` injiziert. `scripts/lib/tmp_paths.py:252-258` (`resolve_pytest_basetemp`) ruft `rc.system_temp_root(...)`; dieses liefert in `scripts/lib/repo_containment.py:635` `tempfile.gettempdir()` verbatim zurück (observed-Return `:642-643`), solange der Wert nicht der Sink ist. `gettempdir()` honoriert `TMPDIR`/`TEMP`/`TMP`. Folge: Der gerenderte Pfad (`<root>/<user>/pytest-agent-meta`) in 12 Agent-Dateien und `.claude/settings.local.json` ist je nach Shell-Umgebung `/var/tmp/...` oder `/tmp/...`; `sync.py --check` meldet Drift (laut Issue 13 Dateien vs. 0).

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
- Entschieden (Q2): macOS/Windows bleiben bei `tempfile.gettempdir()`; die dortige Abhängigkeit von `TMPDIR`/`TEMP`/`TMP` bleibt bestehen (dort nur über `temp-root` pinbar). Env-Freiheit gilt nur für Linux.
- Die Abhängigkeit des Basetemp von `USER`/`USERNAME` (`tmp_paths.py:207-216`, `_current_user`) bleibt unverändert.
- Keine Prosa-/Skill-Verweise auf den neuen WARN-Check (ehemals IC-6): eigener S-PR mit Rebaseline (Follow-up, siehe Offene Fragen).
- Kein Lesen projektlokaler/weiterer Plugin-Settings: nur die User-Ebene (siehe R4).

## Verifizierte Code-Befunde (Worktree `.tmp/wt-batch3-pr3`)

1. **Schema-Ort.** `system-temp-exception` ist **kein** Top-Level-Key und liegt nicht unter `viz.properties`, sondern verschachtelt: `repo_containment` (`config/project-config.schema.json:2744`) → `properties.tmp-sink` (`:2767`) → `properties.system-temp-exception` (`:2795`, `additionalProperties: false` auf `:2820`). Unterkeys: `enabled`, `reason`, `pytest-basetemp`, `toolchain-caches` (`:2814-2818`). Ein neuer Key `temp-root` muss dort ergänzt werden, sonst lehnt das Schema ihn ab.
2. **Leser.**
   - Validierung/Matrix: `scripts/lib/config.py:893-960` (Typprüfung `:903-910`, `enabled`/`reason`-Regeln `:911-932`, Aufruf `system_temp_root` `:940-942`, Inside-Project-Check `:945`, Meldung `:947-951`).
   - Auflösung: `scripts/lib/repo_containment.py:621-663` `system_temp_root(project_root, sink_dir)`; Kandidaten `_candidate_temp_dirs()` (`:602-618`; liest `TMPDIR`/`TEMP`/`TMP` `:608-611` und hängt `os.getcwd()` an `:617`, daher als Quelle für eine env-freie Liste ungeeignet).
   - Builder: `scripts/lib/tmp_paths.py:231-258` `resolve_pytest_basetemp`; `_system_temp_basetemp` `:219-221` hängt `<user>/pytest-agent-meta` an; `resolve_tmp_paths` ruft den Resolver am Ende (`:204`); Dataclass `SystemTempException` (`:57`), befüllt in `_resolve_system_temp_exception` (`:93-142`); `resolve_tmp_paths` ist pur (keine Dateisystem-Zugriffe, `:153`).
   - Injektion: `scripts/lib/config.py:2119-2134` (`variables["PYTEST_BASETEMP"]`), Token-Ersatz `:774-788`.
   - Weitere Konsumenten von `TmpSinkError`/Resolver: `doctor_detectors.py:429`, `provider_transform.py:290`, `consistency/temp_literals.py:484`. Diese bleiben unverändert (Fehlercode `tmp-sink.system-temp-exception` bleibt).
   - Consumer-Konfig agent-meta: `.meta-config/project.yaml:398-407`.
3. **Doppel-Erkennung (Hook-Punkt).**
   - `scripts/lib/mcp_health.py:42` `check_mcp_health(agent_meta_root, project_root, config, log, env=None)` (`:42-48`) lädt Registry und aktive Server (`:52-57`, `resolve_active_mcp_servers`, `registry_query.py:~140-172`) und ist bereits advisory (`except Exception` → `log.debug`, `:59-61`, "never breaks the sync"). Aufgerufen genau einmal: `scripts/lib/sync_pipeline.py:378`. Das ist der natürliche Hook-Punkt: aktive Server stehen bereits bereit. `ai-providers.yaml` wird dort **nicht** geladen; der Aufrufer lädt es (IC-5).
   - `scripts/lib/mcp.py` rendert Artefakte (`generate_mcp_artifacts`), ist für einen Read-only-Check ungeeignet; `registry_query.py` liefert nur die Aktivmenge.
   - `config/provider-capabilities.yaml` enthält kein Plugin-System-Flag (Treffer für "plugin" nur Runtime-Gate/Agent-Discovery). `config/ai-providers.yaml:1-12` (`providers.Claude`) trägt providerweise Werte-Keys ohne Code-Verzweigung (`surface-version`, `agent-discovery`, `model-format`); Defaults in `scripts/lib/providers.py:~384` (`settings_file: .claude/settings.json`). Hier gehört das neue Flag hin.
   - Kein bestehender Code liest `enabledPlugins` oder `external_plugins_file` (Grep über `scripts config docs`: nur der Plan).

## Interface Contracts

### IC-1: Schema-Key `temp-root`

- Ort: `repo_containment.tmp-sink.system-temp-exception.temp-root` in `config/project-config.schema.json`: neues Property nach `toolchain-caches` (endet `:2818`), vor der schließenden Klammer `:2819` des `properties`-Objekts (`additionalProperties: false` folgt `:2820`).
- Typ: `string`, optional, **ohne `default`** (damit `fill_defaults()` — `config.py:1321`, vgl. `_SYNC_SKIPPED_DEFAULT_KEYS` `:184` — den Key nie in Consumer-`project.yaml` schreibt; Kommentar-Verlust #1074).
- Semantik: absoluter Pfad des Platform-Temp-Roots für den pytest-Basetemp (`<temp-root>/<user>/pytest-agent-meta`).
- Validierung ausschließlich **lexikalisch** (keine Dateisystem-Zugriffe, Purity von `resolve_tmp_paths`, `tmp_paths.py:153`). Zwei Ebenen: `config.py` (Block `:893-960`, ein `_fail`) und Builder (`TmpSinkError("tmp-sink.system-temp-exception", ...)`):
  - Typ ≠ str oder leer → Fehler `invalid '...system-temp-exception.temp-root': expected a non-empty string`.
  - Nicht absolut → Fehler. Prüfung: `posixpath.isabs(v) or (ntpath.isabs(v) and ntpath.splitdrive(v)[0] != "")` (d.h. POSIX-Absolutpfad ODER Windows-Laufwerks-/UNC-Pfad), **nicht** plattformabhängiges `os.path.isabs`. Begründung: ab Python 3.13 liefert `ntpath.isabs("/var/tmp")` unter Windows `False`; der Config-Wert `/var/tmp` soll in einer geteilten `project.yaml` plattformunabhängig gleich bewertet werden (posixpath-Semantik für Slash-Pfade). Ob die CI-Windows-Matrix das trägt, ist UNBELEGT (siehe R8).
    - UNC-Wurzel ohne Unterpfad (`\\host\share`) ist **UNGÜLTIG** festgelegt: `ntpath.isabs` ist dafür versionsabhängig (Python 3.9-3.12 `False`, >=3.13 `True`); die Festlegung macht das Verhalten versionsunabhängig. Testfall: `\\host\share` → Fehler; `\\host\share\x` → gültig.
    - Konsequenz: `/var/tmp` wird auch auf Windows-Hosts akzeptiert (geteilte `project.yaml`), ergibt dort keinen sinnvollen Pfad; gewollt.
  - Enthält `"`, `\n`, `\r` → Fehler (Einbettung `--basetemp="<path>"`, bestehende Prüfung `tmp_paths.py:266`).
  - Entspricht lexikalisch dem Sink (normalisierter Pfadvergleich ohne `realpath`) → Fehler.
  - Liegt lexikalisch innerhalb des Projekt-Roots → Fehler (bestehender Inside-Check `config.py:945` gilt auch für den expliziten Wert).
  - Kein Existenz-/`isdir`-Check für `temp-root` (Existenz wird nicht geprüft; ein nicht vorhandener Root scheitert erst beim Anlegen durch pytest).
  - Nur zusammen mit `enabled: true` und `pytest-basetemp: true` wirksam; sonst ignoriert (kein Fehler).

### IC-2: `system_temp_root(project_root, sink_dir, explicit_root=None) -> str`

- Datei: `scripts/lib/repo_containment.py:621`. Neuer optionaler Parameter, rückwärtskompatibel.
- Präzedenz:
  1. `explicit_root` gesetzt → lexikalisch validiert zurückgeben (absolut, nicht Sink, nicht im Projekt; kein Existenzcheck; sonst `TmpSinkError("tmp-sink.system-temp-exception", ...)`).
  2. sonst **Linux (`sys.platform.startswith("linux")`)**: env-freier Default aus einer **festen Liste** als **Modulkonstante** `_LINUX_TEMP_ROOTS = ("/tmp", "/var/tmp", "/usr/tmp")` in `repo_containment.py` (**nicht** `_candidate_temp_dirs()`: dessen Env-Anteile `:608-611` und `os.getcwd()` `:617` sind ungeeignet). Tests ersetzen die Konstante per `monkeypatch.setattr(rc, "_LINUX_TEMP_ROOTS", (...))` (nötig für den Fall "kein Kandidat → raise"). Erster Eintrag, der absolut ist, als Verzeichnis existiert, nicht der Sink und nicht im Projekt liegt. `TMPDIR`/`TEMP`/`TMP` werden nicht gelesen.
  3. sonst **macOS/Windows**: bisheriges Verhalten (`tempfile.gettempdir()` verbatim, bei Sink-Treffer Fallback über `_candidate_temp_dirs()` wie heute, `:642-663`); bleibt env-abhängig (Nicht-Ziel, Q2 entschieden).
  4. kein Kandidat → `TmpSinkError` wie heute (Meldung `:658-663`: Hinweis "set TMPDIR" ersetzen durch "set system-temp-exception.temp-root").
- Der Pin-Fall (`gettempdir()` == Sink, `:642-643`) entfällt unter Linux als Sonderpfad, weil `TMPDIR` dort nicht mehr gelesen wird.
- Diese Spec **überholt #1189-IC-1 für Linux**: AC-1189-01/02/10/11/30 gelten unter Linux nur noch teilweise (Linux liest `_candidate_temp_dirs()`/`gettempdir()` nicht mehr); auf macOS/Windows unverändert. Betroffene Tests: siehe Abschnitt Tests.
- Python 3.9: keine neuen Laufzeit-Unions (`X | Y`); Signatur `explicit_root: Optional[str] = None`.

### IC-3: `resolve_pytest_basetemp(project_root, paths)`

- Datei: `scripts/lib/tmp_paths.py:231`. Beide Zweige, die `rc.system_temp_root` rufen (`:252`, `:257`), reichen `paths.system_temp_exception.temp_root` als `explicit_root` durch.
- `SystemTempException` (frozen Dataclass, `tmp_paths.py:57`) erhält Feld `temp_root: Optional[str] = None`; `_resolve_system_temp_exception` (`:93-142`) befüllt es aus `raw_exception.get("temp-root")` (nur nicht-leerer `str`, sonst `TmpSinkError` gemäß IC-1) und reicht es im `return` (`:137-142`) durch.
- `config.py:940` ruft `system_temp_root(project_root, resolve_sink_absolute(...), explicit_root=<temp-root aus Config>)`; die Inside-Check-Meldung `:947-951` verweist bei gesetztem `temp-root` auf diesen Key statt auf "stale framework pin / new shell".
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
- Parameterfluss (festgelegt): Der Aufrufer `_sync_stage_claude_base` (`scripts/lib/sync_pipeline.py:311`, Aufruf `check_mcp_health` `:378`) hat `ai-providers.yaml` bereits als Parameter `provider_config` (`:313`) geladen; kein zweiter Parser. Verifiziert per Read: `provider_config` enthält die Konfiguration **aller** übergebenen `providers` (vgl. `:340-343`), nicht nur der aktiven. Daher übergibt der Aufrufer nur AKTIVE Provider, analog `:335`: `{p: provider_config[p] for p in providers if is_provider_active(config, p) and p in provider_config}`. Hinweis: Der Filter wird neu berechnet; `active_providers` aus `:335` existiert nur innerhalb von `if _context_auto_generate` und ist nicht wiederverwendbar. Dieses Mapping geht als neuer Parameter `provider_cfgs` an `check_mcp_health` (`mcp_health.py:42-48`, neuer optionaler Parameter `provider_cfgs: Optional[Mapping[str, Mapping]] = None`, `home: Optional[Path] = None`) übergeben. `check_mcp_health` lädt die Datei nicht selbst; bei `provider_cfgs is None` entfällt der Check (rückwärtskompatibel, bestehende Tests unverändert).
- Signatur: `check_external_plugin_duplicates(registry: dict, active: list, provider_cfgs: Mapping, log: SyncLog, home: Optional[Path] = None) -> None` (Python 3.9: `list`/`Optional`, keine Laufzeit-Unions); `home` für Tests (Default `Path.home()`).
- Ablauf: je aktivem Server mit `external-plugin-id-prefix` und je Provider in `provider_cfgs` mit `external_plugins_file`: Datei lesen (JSON, read-only). `~` wird **relativ zum `home`-Parameter** aufgelöst: beginnt `path` mit `~/`, dann `home / path[2:]` (kein `os.path.expanduser`, da dieses `HOME` statt `home` folgt); sonst Pfad unverändert. `enabled_key`-Mapping prüfen, Schlüssel mit Präfix und Wert `true` → genau eine `log.warn`-Meldung je Server/Provider: Server-Name, Fundstelle, Handlungsanweisung ("Katalog-Server in `plugins:` mit `enabled: false` deaktivieren oder Plugin deaktivieren; sonst beide Env-Variablensätze setzen").
- Fehlerpfade: Datei fehlt, unlesbar, kein JSON, Key fehlt/falscher Typ → keine WARN, nur `log.debug` (best-effort). Niemals Exception nach außen, niemals Schreibzugriff, niemals Exit-Code-Änderung.
- Kein Aufruf bei `--dry-run`-Sonderbehandlung nötig (read-only); WARN erscheint auch bei `--dry-run`/`--check` (Q6 entschieden).

### IC-6: entfällt (aus PR 3 herausgenommen)

- Der Prosa-Hinweis (`config/plugin-catalog.yaml:245`, agent-hint) und der Skill `mcp-reqogniloom` werden in PR 3 **nicht** angefasst: eine agent-hint-Änderung ändert generierte Artefakte und erzwingt ein Rebaseline. Follow-up: eigener S-PR "Prosa/Skill verweisen auf den Sync-WARN-Check" inklusive Rebaseline (Master-Quelle des Skills dort ermitteln).

## Datenfluss

**#1246:** `project.yaml` → `config.py` Validierung (`:893-960`, inkl. `temp-root`) → `resolve_tmp_paths` (`tmp_paths.py`) → `resolve_pytest_basetemp` → `system_temp_root(explicit_root=...)` → `<root>/<user>/pytest-agent-meta` → `variables["PYTEST_BASETEMP"]` (`config.py:2134`) → Render in Agent-Templates und `settings.local.json` → Hash in `generated-file-hashes.json`. `TMPDIR` fließt nirgends mehr ein.

**#1261:** Sync → `sync_pipeline.py` `_sync_stage_claude_base`: `provider_config` gefiltert auf aktive Provider (`provider_cfgs`) → `:378` `check_mcp_health(..., provider_cfgs=...)` → Aktivmenge (`resolve_active_mcp_servers`) → je Server mit `external-plugin-id-prefix` + je Provider mit `external_plugins_file` → Datei lesen → Treffer → `log.warn`.

## Task-3.1-Reproduktion (nur Beschreibung, nicht ausgeführt)

Auf frischem Branch, Konfig wie im Worktree:

```
TMPDIR=/var/tmp python3 scripts/sync.py --check --config <worktree>/.meta-config/project.yaml
TMPDIR=/tmp     python3 scripts/sync.py --check --config <worktree>/.meta-config/project.yaml
```

Beide Ausgaben nach `.tmp/plans/scratch/1246-repro.txt`. Erwartet (Issue): erster Lauf 0 abweichende Dateien (committeter Hash enthält `/var/tmp/hermes/pytest-agent-meta`), zweiter Lauf 13 (12 Agent-Dateien + `settings.local.json`) mit Pfad `/tmp/<user>/pytest-agent-meta`. Zusatzbeobachtung: `PYTEST_BASETEMP` im gerenderten `.claude/agents/tester.md:45`. Wenn beide Läufe 0 Drift zeigen, Issue als "nicht reproduzierbar" kommentieren und IC-1 bis IC-3 entfallen. Hinweis: `--check` ist dry-run-artig; trotzdem im Worktree (nicht im Hauptcheckout) ausführen.

## Acceptance Criteria

1. AK-1: Unter Linux liefert `system_temp_root` ohne `explicit_root` für `TMPDIR=/var/tmp` und `TMPDIR=/tmp` (`monkeypatch.setenv`; zusätzlich `monkeypatch.setattr(tempfile, "tempdir", None)`, damit kein gecachtes `gettempdir()`-Ergebnis den Test maskiert) dasselbe Ergebnis; Test mit `skipif` für Nicht-Linux (IC-2).
2. AK-2: Mit `explicit_root="/var/tmp"` ist das Ergebnis `/var/tmp` unabhängig von `TMPDIR` und ohne Existenzprüfung (auch ein nicht existierender absoluter Pfad wird unverändert zurückgegeben).
3. AK-3: Relativer `temp-root` führt zu `TmpSinkError` (Code `tmp-sink.system-temp-exception`); in `config.py` zu einem Validierungsfehler mit Key-Pfad.
4. AK-4: `temp-root` lexikalisch innerhalb des Projekt-Roots oder gleich Sink → Fehler.
5. AK-5: `resolve_pytest_basetemp` übernimmt `temp-root` vor dem Default; `basetemp_dirs` (`test_settings_dirs.py`) folgt.
6. AK-6: `fill_defaults()` schreibt `temp-root` nie in eine Consumer-`project.yaml` (Key ohne Schema-Default); bestehender Test zu `fill_defaults`-Byte-Stabilität bleibt grün.
7. AK-7: `.meta-config/project.yaml` setzt `temp-root: /var/tmp`; `sync.py --check` unter `TMPDIR=/tmp` und `TMPDIR=/var/tmp` meldet identisch 0 Drift; kein Rebaseline **durch #1246** (`generated-file-hashes.json` ändert sich durch diesen PR nicht aufgrund von `temp-root`/`system_temp_root`; ein Rebaseline aus anderen Quellen ist nicht Teil dieses Kriteriums).
8. AK-8: Ohne `temp-root` rendert Linux den env-freien Default (erster existierender Eintrag aus `/tmp`, `/var/tmp`, `/usr/tmp`); macOS/Windows rendern unverändert über `gettempdir()`. Die Änderung ist im CHANGELOG als Verhaltensänderung (Linux) vermerkt.
9. AK-9: Mit `enabledPlugins: {"reqogniloom@reqogniloom-marketplace": true}` in `<home>/.claude/settings.json` (`home` als Parameter an `check_external_plugin_duplicates` übergeben, `~/` wird relativ zu `home` aufgelöst, kein `HOME`-Monkeypatch nötig) und aktivem Katalog-Server erscheint genau eine WARN mit Handlungsanweisung; ohne Datei, mit `false`-Wert oder deaktiviertem Katalog-Server keine WARN.
10. AK-10: Defekte Datei (kein JSON, falscher Typ) erzeugt keine Exception und keine WARN; Sync-Exit-Code unverändert.
11. AK-11: Kein Provider-Name im Syncer-Code (Grep `if provider ==` im geänderten Code leer); Plugin-ID nur in Katalog/Config.
12. AK-12: `python3 scripts/sync.py --validate`, betroffene Testdateien und `tests/test_context_budgets.py` grün.

## Tests

- `tests/test_tmp_sink_system_temp_root.py` (erweitern): TMPDIR-Unabhängigkeit (AK-1), `explicit_root` (AK-2), Fehlerfälle (AK-3, AK-4).
  - **Bestehende #1189-Tests brechen unter Linux** (patchen `gettempdir`/`_candidate_temp_dirs`/`TMPDIR`, die Linux nicht mehr liest). Diese 5 Tests per `skipif(sys.platform.startswith("linux"))` auf Nicht-Linux beschränken ODER für Linux umschreiben (Ersatz: `_LINUX_TEMP_ROOTS` per Monkeypatch setzen):
    - `test_no_sink_returns_gettempdir` (`:48-51`)
    - `test_observed_root_not_sink_returns_unchanged` (`:72-77`)
    - `test_sink_candidate_is_skipped` (`:107-116`)
    - `test_no_candidate_outside_root_raises` (`:119-129`; Linux-Variante: `_LINUX_TEMP_ROOTS=()` bzw. nur ungültige Einträge → `TmpSinkError`)
    - `test_normcase_comparison_windows` (`:132-142`)
  - Weiterlaufend ohne Änderung: `test_pin_returns_existing_dir_outside_root`, `test_tmpdir_only_pin_matches_all_keys_pin`, `test_environ_and_tempdir_cache_unchanged` (`:80`), `test_concurrent_calls_agree` (`:91`). Die Pin-Tests sind unter Linux nur noch trivial grün (prüfen den Pin-Pfad nicht mehr).
  - Zeilenangaben vor Umsetzung per Read erneut verifizieren.
- `tests/test_tmp_paths_builder.py` (erweitern): `temp-root` wird übernommen, relativ → `TmpSinkError`, Präzedenz.
- `tests/test_settings_dirs.py` (erweitern): `basetemp_dirs` folgt dem expliziten Root.
- Config-Validierung (bestehende Datei zu `system-temp-exception`, bei Umsetzung per `grep -l system-temp-exception tests`): Typ-/Leer-/Absolut-Fälle, `fill_defaults`-Stabilität (AK-6).
- `tests/test_mcp_duplicate_plugin_warning.py` (neu): AK-9, AK-10 mit `tmp_path` als `home`-Parameter und selbst gebautem `provider_cfgs`-Mapping (kein Laden von `ai-providers.yaml` im Test nötig).
- Manuell/PR-Text: Task-3.1-Beleg und AK-7 (zwei `--check`-Läufe).

## Offene Fragen + Risiken

### Offene Fragen

- Q1 (ENTSCHIEDEN): Linux nutzt eine feste, env-freie Liste `/tmp`, `/var/tmp`, `/usr/tmp` (erster existierender, gültiger Eintrag), nicht `_candidate_temp_dirs()`.
- Q2 (ENTSCHIEDEN, Nutzer): Nur Linux env-frei. macOS/Windows behalten `gettempdir()`; die verbleibende Env-Abhängigkeit dort ist Nicht-Ziel (macOS `TMPDIR` = `/var/folders/...`, Änderung würde bestehende Pfade brechen).
- Follow-up (kein Teil von PR 3): eigener S-PR für Prosa-/Skill-Verweis auf den Sync-WARN-Check (ehemals IC-6) mit Rebaseline.
- Q3 (ENTSCHIEDEN): Pluginschema nur im Katalog (`external-plugin-id-prefix`), kein Config-Override pro Projekt.
- Q4 (ENTSCHIEDEN): Flag-Form `external_plugins_file` als Mapping (`path` + `enabled_key`), siehe IC-4.
- Q5: Quelle des Skills `mcp-reqogniloom` (Plan zitiert `SKILL.md:95`): entfällt für PR 3 (siehe Follow-up-S-PR).
- Q6 (ENTSCHIEDEN): Die WARN erscheint auch bei `--dry-run`/`--check` (read-only), siehe IC-5.

### Risiken

- R1: Env-freier Default (nur Linux) ändert den Render für Linux-Consumer-Projekte mit nicht-`/tmp` `TMPDIR` und ohne `temp-root` (Drift beim nächsten Sync, Rebaseline). macOS/Windows bleiben env-abhängig (Nicht-Ziel). Mitigation: CHANGELOG, Doku-Satz, agent-meta selbst pinnt `/var/tmp`.
- R2: Nutzer-Harness-Allowlist (`/var/tmp/hermes/pytest-agent-meta`) läuft ins Leere, falls `temp-root` fehlt oder der Default `/tmp` ist.
- R3: Neuer Schema-Key ohne Default: `--fill-defaults` listet ihn nicht; Admin-UI-Formular muss ihn optional behandeln.
- R4: `~/.claude/settings.json` ist Nutzer-Datei außerhalb des Repos; Lesen ist best-effort, Format kann sich ändern (daher WARN statt Fehler, `log.debug` bei Parse-Fehler). Grenze: gelesen wird nur die User-Ebene; projekt-/lokal-gescopte Plugin-Aktivierungen (z.B. `<projekt>/.claude/settings.json`, `settings.local.json`) werden nicht erkannt (False Negative, bewusst akzeptiert, kein Hard-Fail).
- R5: Plugin-Marketplace-Name kann abweichen; Präfix-Match `reqogniloom@` ist toleranter als Vollname, kann aber Fremd-Plugins treffen.
- R6: Python 3.9-Kompatibilität (kein `X | Y`, `from __future__ import annotations`); Modulgröße `repo_containment.py`/`mcp_health.py` ≤ 600 Zeilen prüfen.
- R7: Spec-Plan-Abgleich: Plan nennt `ai-providers.yaml`-Flag als Config-Key; Schema-/Registry-Validatoren müssen den neuen Key kennen, sonst `--validate`-Fehler.

- R8: Python >= 3.13 unter Windows: `ntpath.isabs("/var/tmp")` ist `False`. Mitigation: `temp-root` wird lexikalisch mit posixpath- ODER ntpath-Absolutheit geprüft (IC-1), nicht mit dem plattformabhängigen `os.path.isabs`. Ob die CI-Windows-Matrix (Python-Versionen, Windows-Läufer) existiert und dies abdeckt: UNBELEGT, bei Umsetzung prüfen.

## Trace-Anker

spec-id: SPEC-temp-root-and-reqogniloom-duplicate
