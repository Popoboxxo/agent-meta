# Plattform-Presets für project.yaml — Design-Spec

> Status: Entwurf, brainstormed mit Nutzer 2026-09-09. Noch nicht implementiert.

## Problem

`.meta-config/project.yaml` hat ein `platforms:`-Feld (z.B. `[hacs]`, `[sharkord]`) und pro
Plattform existiert bereits `platform-configs/<name>.defaults.yaml`, das `{{platform.<name>.*}}`-
Platzhalter für Templates befüllt. Diese Plattform-Zuordnung ist aber komplett getrennt von den
project.yaml-Feldern, die eigentlich plattformtypisch sind (`dod-preset`, `TEST_COMMANDS`,
`CODE_CONVENTIONS`, etc.) — jedes neue Projekt auf derselben Plattform tippt dieselben Werte
erneut ab.

Zusätzlich existiert bereits eine faktische Dopplung: `platform-configs/sharkord.defaults.yaml`
pflegt `service_name`, `host_lan_ip` als Plattform-Konstanten im `{{platform.sharkord.*}}`-
Namespace, obwohl `variables.SERVICE_NAME`/`CONTAINER_NAME`/`HOST_LAN_IP` in project.yaml
dieselbe Sache generisch (aber unverknüpft) abbilden.

## Ziel

Plattform-Presets für einen kuratierten Satz von project.yaml-Feldern, mit klarer
Override-Kaskade und expliziter additiver Erweiterung — ohne eine neue Config-Datei-Art
einzuführen.

## Nicht-Ziele (v1)

- Keine Preset-Vererbung für bereits domänenspezifische Preset-Systeme (`tier-presets.yaml`,
  `rules-presets.yaml`) — die bleiben unangetastet, kein Overlap.
- Keine Deep-Merge-Semantik für verschachtelte Dicts (`hooks`, `mcp-role-overrides`,
  `model-overrides`, `gitignore`-Policy etc.) — bewusst außen vor, zu riskant/komplex für v1.
- Keine automatische Platform-Erkennung — `platforms:` bleibt eine explizite Nutzerwahl im Wizard.

## Kuratierte Feldliste (v1)

**Scalar, nur Override (kein `+`):**

- `dod-preset`
- `conventions-preset`
- `variables.PLATFORM`
- `variables.RUNTIME`
- `variables.LANGUAGE`
- `variables.PROJECT_LANGUAGES`
- `variables.SYSTEM_DEPENDENCIES`
- `variables.ENTRY_POINT_PATTERN`
- `variables.GIT_MAIN_BRANCH`
- `variables.SERVICE_NAME`
- `variables.CONTAINER_NAME`
- `variables.HOST_LAN_IP`

**Additiv-fähig (`<FELD>+` hängt an, `<FELD>` ersetzt komplett):**

- `variables.TEST_COMMAND` / `variables.TEST_COMMANDS`
- `variables.DEV_COMMANDS`
- `variables.BUILD_COMMAND` / `variables.BUILD_COMMANDS`
- `variables.CODE_CONVENTIONS`

Alle anderen project.yaml-Felder bleiben wie bisher rein projekt-individuell, keine
Plattform-Kopplung.

## Architektur

### 1. Quelle: bestehende `platform-configs/<name>.defaults.yaml` erweitern

Statt einer neuen Datei bekommt jede bestehende Plattform-Defaults-Datei drei neue optionale
Top-Level-Sektionen:

```yaml
# platform-configs/sharkord.defaults.yaml (Auszug, erweitert)
dod-preset: standard
conventions-preset: docker-service
variables:
  SERVICE_NAME: sharkord
  CONTAINER_NAME: sharkord
  HOST_LAN_IP: "127.0.0.1"
  TEST_COMMANDS+: "docker compose run --rm test"
  CODE_CONVENTIONS: "Go, gofmt, golangci-lint"

# bestehende {{platform.*}}-Platzhalter-Sektion bleibt unverändert daneben bestehen
service_name: sharkord   # TODO Migration: nach variables.SERVICE_NAME migrieren, alte
                          # {{platform.sharkord.service_name}}-Verwendungsstellen umbiegen
```

Die Migration der bestehenden `service_name`/`host_lan_ip`-Duplikate ist Teil der
Implementierung, kein Blocker fürs Grunddesign.

### 2. Resolver: `scripts/lib/platform.py` erweitern

`load_platform_config()` liefert heute nur `{{platform.*}}`-Werte. Neue Funktion
`resolve_platform_defaults(platforms: list[str]) -> dict` liest für jede Plattform in
`platforms:` (Listenreihenfolge) die neuen `dod-preset`/`conventions-preset`/`variables`-
Sektionen und merged sie:

- **Scalar-Felder:** letzte Plattform in der Liste gewinnt bei Konflikt (analog zu
  `filter_redundant_provider_entries`-Reihenfolgeprinzip in `gitignore.py`).
- **Additiv-Felder (`<FELD>+`):** Werte aller Plattformen werden in Listenreihenfolge
  aneinandergehängt (bei den aktuell string-wertigen `variables.*`-Feldern: `&&`-Join, konsistent
  mit dem bestehenden Muster `TEST_COMMANDS: "... && ..."` in diesem Repo).

### 3. Kaskade in `build_variables()` (`scripts/lib/config.py`)

Bisherige Kaskade für die kuratierten Felder wird um eine Stufe erweitert:

```
project.yaml expliziter Wert
  > (falls project.yaml <FELD>+ gesetzt) resolve_platform_defaults()[FELD] + project-Zusatz
  > resolve_platform_defaults()[FELD]   (aus platforms:)
  > bisheriger hartcodierter Framework-Default (unverändert als letzte Stufe)
```

Analog für `dod-preset` (`scripts/lib/dod.py`) und `conventions-preset`
(`scripts/lib/conventions.py`): neue Zwischenstufe zwischen "project override" und
`"full"`/`"default"`.

### 4. Materialisierte, sichtbare Resolved-Datei

`sync.py` schreibt bei jedem Lauf `.meta-config/platform-defaults.resolved.yaml` — die
gemergten (aber noch nicht mit project.yaml-Werten kombinierten) Plattform-Defaults für die
aktuell gewählten `platforms:`. Rein informativ/generiert, nicht Teil der Resolution-Logik
selbst (die läuft direkt über `resolve_platform_defaults()`), sondern für den Nutzer, um ohne
Blick in `platform-configs/` zu sehen, was aktuell wirkt.

- Hash-Schutz über die **bestehende** `.meta-config/generated-file-hashes.json`-Infrastruktur
  (gleicher Mechanismus wie für alle anderen generierten Dateien) — keine neue
  Drift-Detection bauen.
- Manuelle Edits werden wie bei jeder anderen generierten Datei beim nächsten Sync
  überschrieben und im Hash-Diff sichtbar.

### 5. Setup-Wizard

Keine strukturelle Änderung an `scripts/lib/setup.py` nötig — die Platform-Frage existiert
schon (Zeile 265). Die nachfolgenden Fragen (DoD-Preset, Test-Command, etc.) können optional
mit dem plattform-aufgelösten Wert vorbelegt werden (`default=resolved[...]` im `_ask`-Call)
statt mit dem generischen Framework-Default — kleine Änderung, kein neuer Fragenblock.

Wichtig: Die Kaskade wirkt **live bei jedem `sync.py`-Lauf**, nicht nur beim Init (Option B aus
dem Brainstorming) — ein bestehendes Projekt bekommt neue Plattform-Defaults automatisch, sobald
sich `platform-configs/<name>.defaults.yaml` ändert, außer explizit in project.yaml
überschrieben.

## Beispiel

`platforms: [hacs]`, project.yaml setzt nichts zu `TEST_COMMANDS`:

```yaml
# platform-configs/hacs.defaults.yaml
variables:
  PLATFORM: "Home Assistant Custom Component"
  RUNTIME: "Python 3.13 (HA Core)"
  PROJECT_LANGUAGES: "Python"
  TEST_COMMANDS: "pytest tests/ --cov"
```

→ generiertes CLAUDE.md bekommt `TEST_COMMANDS: pytest tests/ --cov` ohne dass der Nutzer es
eingetippt hat.

Projekt will zusätzlich einen HACS-Validator-Lauf, ohne die Basis zu verlieren:

```yaml
# .meta-config/project.yaml
variables:
  TEST_COMMANDS+: "hacs-validate ."
```

→ resolviert zu `pytest tests/ --cov && hacs-validate .`

## Offene Implementierungs-Punkte (nicht blockierend fürs Design)

1. Migration der bestehenden `service_name`/`host_lan_ip`-Duplikate in `sharkord.defaults.yaml`
   — vor dem Entfernen der alten `{{platform.sharkord.*}}`-Werte grep-Check aller
   Template-Verwendungsstellen.
2. `build_variables()` in `config.py` ist laut Issue #452/#482 bereits als "God Function"
   markiert (Refactor-Issue) — die neue Kaskadenstufe sollte dort sauber eingehängt werden,
   idealerweise im Zuge/nach #482, nicht als weiterer Ast in der bestehenden Funktion.
3. Additiv-Join-Zeichen (`&&`) ist eine Annahme aus dem bestehenden `TEST_COMMANDS`-Beispiel in
   diesem Repo — bei Feldern, die keine Shell-Commands sind (z.B. `CODE_CONVENTIONS`), ist ein
   Newline-Join wahrscheinlich sinnvoller. Pro Feld im Resolver festlegen, nicht global.

## Tests

Neues Szenario in `tests/scenarios/` (Infrastruktur aus PR #705 wiederverwenden): Projekt mit
`platforms: [hacs]` + einem additiven `TEST_COMMANDS+`-Override, Assert prüft den resolvierten
Wert in der generierten Ausgabe UND den Inhalt von
`.meta-config/platform-defaults.resolved.yaml`.
