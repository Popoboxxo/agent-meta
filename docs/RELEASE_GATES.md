# Mechanized Pre-Release Gates

> Umsetzung von Issue #558. Zielgruppe: Entwickler in Consumer-Projekten, die `agent-meta`
> als Submodule unter `.agent-meta/` einbinden und den `release`-Agenten nutzen.

## Motivation

Der `release`-Agent führt schon eine manuelle Pre-Release-Checkliste aus (Tests, DoD, CHANGELOG,
Versionsbump). Manche Fehlerklassen lassen sich aber besser **mechanisch** prüfen als von einem
LLM-Agenten "gedanklich" abgehakt werden — z. B. "wurde das generierte Artefakt wirklich neu
gebaut?", "hat das Docker-Base-Image bekannte HIGH/CRITICAL-CVEs?", "zeigt ein gepinnter
GitHub-Action-Tag/SHA noch auf einen existierenden Commit upstream?". `pre-release-check.sh`
bündelt das als eine **Plugin-Pipeline**: drei eingebaute Gates, beliebig erweiterbar um eigene.

## Architektur: Dispatcher + Plugin-Verzeichnis

`pre-release-check.sh` enthält selbst **keine** Gate-Logik. Es ist ein reiner Dispatcher: er
führt jedes `*.sh`-Script in seinem eigenen `release-gates/`-Unterverzeichnis der Reihe nach aus,
sammelt die Exit-Codes und liefert am Ende Exit 1, falls mindestens eines fehlgeschlagen ist —
sonst Exit 0. Kein Gate-Script ist dem Dispatcher namentlich bekannt; er entscheidet auch nicht,
ob ein Gate aktiv ist — das entscheidet jedes Gate-Script an seinem eigenen Anfang selbst.

```
<hooks_dir>/
  pre-release-check.sh          # Dispatcher (agent-meta-managed)
  release-gates/
    .agent-meta-managed         # Allowlist Teil 1: eingebaute Gate-Dateinamen (agent-meta-managed)
    .allowed-gates               # Allowlist Teil 2: projekteigene Gate-Dateinamen (sync.py fasst das NIE an)
    artifact-freshness.sh       # eingebaut (agent-meta-managed)
    docker-image-scan.sh        # eingebaut (agent-meta-managed)
    action-pin-validation.sh    # eingebaut (agent-meta-managed)
    my-project-custom-check.sh  # projekteigen — sync.py fasst das NIE an, muss zusätzlich in .allowed-gates stehen (issue #598)
```

(`<hooks_dir>` = `.claude/hooks` bei Claude, `.mammouth/hooks` bei Mammouth — der einzige aktuell
aktive Provider mit Hook-Unterstützung neben Claude, siehe `config/ai-providers.yaml: has_hooks`.)

- Quelle der eingebauten Gates: `hooks/1-generic/release-gates/*.sh` in diesem Repo, layered wie
  jeder andere Hook (`2-platform` > `1-generic` > `0-external`, siehe
  `scripts/lib/hooks.py::collect_hook_sources()`).
- `sync.py` kopiert Dispatcher UND eingebaute Gates automatisch in jeden aktiven Provider mit
  Hook-Unterstützung — kein providerspezifischer Zusatzaufwand nötig
  (`scripts/lib/hooks.py::sync_release_gates()`).
- Anders als die übrigen Hooks wird `pre-release-check.sh` **nicht** über native Tool-Events
  (`PreToolUse` etc.) automatisch ausgelöst. Sein Metadata-Header trägt `event: Manual` als
  Konvention. Er wird **nicht** über
  ```yaml
  # .meta-config/project.yaml
  hooks:
    pre-release-check:
      enabled: true
  ```
  aktiviert — dieser Mechanismus ist ausschließlich für native, automatisch gefeuerte Events
  gedacht. Stattdessen prüft der `release`-Agent selbst, ob die Datei existiert, und führt sie bei
  Bedarf per `Bash` aus, bevor ein Tag/Release gepusht wird (siehe `agents/1-generic/release.md`,
  Workflow-Schritt "0. Mechanized pre-release gates").
- Fehlt der Hook in einem Projekt (z. B. weil `sync.py` noch nicht mit dieser Version gelaufen
  ist, oder weil ein Provider ohne Hook-Unterstützung genutzt wird), überspringt der
  `release`-Agent den Schritt einfach — rein additiv, kein Breaking Change.

## Eigene Gates hinzufügen (der zentrale Erweiterungspunkt)

Ein Projekt legt eine eigene `.sh`-Datei direkt in `<hooks_dir>/release-gates/` ab —
`sync.py` fasst projekteigene Dateien dort **nie** an (nicht im `release-gates/.agent-meta-managed`
Index getrackt, exakt wie projekteigene Hooks über `--create-hook`).

**Allowlist-Pflicht (issue #598):** seit Version 3.0.0 des Dispatchers führt `pre-release-check.sh`
NICHT mehr automatisch jede `.sh`-Datei aus, die im Verzeichnis liegt — das war ein
Supply-Chain-Risiko (versehentlich abgelegte, per kompromittierter Dependency eingeschleuste oder
über eine bösartige PR hinzugefügte Datei hätte sonst unkontrolliert im Release-Prozess mitgelaufen).
Ein Gate-Script läuft nur, wenn sein Dateiname in einer der beiden Allowlist-Dateien steht:

- `release-gates/.agent-meta-managed` — eingebaute Gates, von `sync.py` verwaltet.
- `release-gates/.allowed-gates` — projekteigenes Manifest, **von `sync.py` nie angefasst**. Eine
  Zeile pro erlaubtem Dateinamen, `#`-Kommentare und Leerzeilen werden ignoriert.

Ein Skript in `release-gates/`, das in KEINER der beiden Dateien steht, wird mit `[SKIP] ... not on
the release-gates allowlist` übersprungen — nicht als Fehlschlag gewertet, aber auch nicht
ausgeführt. Um ein eigenes Gate zu aktivieren, zusätzlich zum Ablegen der `.sh`-Datei:

```bash
echo "no-todo-in-changelog.sh" >> .claude/hooks/release-gates/.allowed-gates
```

Danach findet und führt der Dispatcher es automatisch mit aus, weiterhin ganz ohne
`sync.py`-Lauf oder Framework-Änderung — nur die eine zusätzliche Manifest-Zeile ist neu
gegenüber früheren Versionen.

**Vertrag für ein Gate-Script** (egal ob eingebaut oder projekteigen):

- Exit `0` = bestanden (oder selbst-übersprungen, z. B. weil deaktiviert oder eine Voraussetzung
  fehlt).
- Exit ungleich `0` = fehlgeschlagen, blockiert den Release.
- Muss eigenständig lauffähig sein (`bash release-gates/mein-check.sh`), nicht nur über den
  Dispatcher.
- Ein Metadata-Header (`# hook:`, `# version:`, `# description:`, `# enabled_by_default:` — wie
  bei jedem anderen Hook, siehe `parse_hook_metadata()`) ist **optional** für projekteigene Gates
  — nur eingebaute Gates aus `agent-meta` brauchen ihn (für die sync-time-Default-Injektion, s. u.).
  Wie ein projekteigenes Gate seine eigene Konfiguration liest (Env-Var, eigenes YAML, hart
  kodiert), ist bewusst offen — das Framework schreibt hier nichts vor.

**Minimalbeispiel** — `.claude/hooks/release-gates/no-todo-in-changelog.sh`:

```bash
#!/bin/bash
# Eigenes, minimales Gate ohne Metadata-Header — völlig ausreichend.
set -u
cd "${PROJECT_ROOT:-$PWD}" || exit 1

if [ -f CHANGELOG.md ] && grep -q "TODO" CHANGELOG.md; then
  echo "[FAIL] no-todo-in-changelog: CHANGELOG.md enthält noch TODO-Marker"
  exit 1
fi
echo "[INFO] no-todo-in-changelog: OK"
exit 0
```

Kein Eintrag in `project.yaml` nötig, kein `sync.py`-Lauf nötig — Datei ablegen UND ihren Namen in
`release-gates/.allowed-gates` eintragen (s. o.), dann wird sie beim nächsten
`bash .claude/hooks/pre-release-check.sh` automatisch mitgeführt.

## Die drei eingebauten Gates

Jedes Gate übersprint sich **selbst graceful** (Exit 0, `[SKIP]`-Log), wenn es deaktiviert ist oder
eine Voraussetzung im jeweiligen Projekt fehlt. Kein Gate führt zu einem Hard-Fail nur weil ein
Tool/eine Config nicht vorhanden ist.

### `artifact-freshness` — Generic Artifact Freshness Check

Prüft, ob generierte Artefakte (Build-Output, kompilierte Schemas, Bundles, …) tatsächlich neu
gebaut wurden, nachdem sich ihre Quelle geändert hat.

**Aktivierung:** siehe [Konfiguration](#konfiguration-projectyaml--dod-preset) unten UND Datei
`.agent-meta/generated-artifacts.yaml` im Consumer-Projekt-Root. Fehlt die Config-Datei komplett,
wird das Gate unabhängig von der Enabled-Konfiguration übersprungen (rein opt-in).

**Config-Format** (stdlib-only Parser, **kein vollständiger YAML-Parser** — unterstützt nur dieses
eingeschränkte Subset):

```yaml
artifacts:
  - source: VERSION
    generated: dist/manifest.json
  - source: src/schema.py
    generated: docs/api/schema.json
```

Unterstützt:
- Genau ein Top-Level-Key `artifacts:` mit einer Liste.
- Jeder Eintrag: `- source: <Pfad-oder-Glob>` gefolgt von `generated: <Pfad-oder-Glob>` auf der
  Folgezeile (oder beide Keys als separate `- `-Einträge — beide Schreibweisen funktionieren).
- Kein Nesting, keine Anchors/Aliases, keine mehrzeiligen Scalars, keine Kommentare hinter Werten.

**Logik je Paar:** ist `source` (per Datei-mtime, `git log -1 --format=%ct` als Fallback wenn die
Datei nicht mehr existiert) neuer als `generated`? Wenn ja → Gate-Fehler. Fehlt `generated`
komplett → ebenfalls Gate-Fehler ("Artefakt nie gebaut").

### `docker-image-scan` — Docker Base Image Security Scan

Scannt die Base-Images eines `Dockerfile` mit [Trivy](https://github.com/aquasecurity/trivy) auf
bekannte HIGH/CRITICAL-CVEs, bevor ein Release-Image darauf aufbaut.

**Voraussetzung:** siehe [Konfiguration](#konfiguration-projectyaml--dod-preset) UND ein
`Dockerfile` existiert UND `trivy` ist im `PATH` verfügbar. Fehlt eines der beiden Letzteren →
Gate übersprungen (Info-Log).

**Konfigurierbarer Pfad:** Env-Var `PRE_RELEASE_DOCKERFILE_PATH` (Default: `Dockerfile`) — dies ist
die einzige Zusatzkonfiguration, die dieses eingebaute Gate über `enabled` hinaus konsumiert;
weitere Schlüssel im `release-gates.docker-image-scan`-Block von `project.yaml` (das Schema erlaubt
sie, `additionalProperties: true`) werden von diesem Script derzeit ignoriert.

Extrahiert alle `FROM`-Zeilen, filtert Referenzen auf vorherige Build-Stages heraus (z. B.
`FROM build AS test` referenziert die Stage `build`, kein pullbares Image), und ruft für jedes
verbleibende Image `trivy image --severity HIGH,CRITICAL --exit-code 1 <image>` auf.

### `action-pin-validation` — GitHub Action Pin Validation

Prüft, ob alle in `.github/workflows/*.yml` gepinnten GitHub Actions (`uses: owner/repo@ref`) noch
auf existierende Refs upstream zeigen — der Fehlerfall aus Issue #558 ist ein gelöschter/rebaster
Tag oder SHA, der eine CI-Pipeline unbemerkt bricht oder ein Supply-Chain-Risiko öffnet.

**Voraussetzung:** siehe [Konfiguration](#konfiguration-projectyaml--dod-preset) UND
`.github/workflows/*.yml` existieren UND die `gh` CLI ist installiert und authentifiziert
(`gh auth status`). Fehlt eines der beiden Letzteren → Gate übersprungen.

- **Tag-Pins** (`uses: actions/checkout@v4`): Existenz via
  `gh api repos/{owner}/{repo}/git/ref/tags/{ref}` prüfen.
- **Volle 40-Zeichen-SHA-Pins** (`uses: actions/checkout@a1b2c3...`): Existenz via
  `gh api repos/{owner}/{repo}/commits/{sha}` prüfen (404 = Commit upstream gelöscht/rebased).

## Konfiguration: project.yaml + DoD-Preset

Ob ein eingebautes Gate standardmäßig aktiv ist, wird deklarativ über die neue, offene
`release-gates:`-Sektion in `.meta-config/project.yaml` gesteuert — **keine feste Enum**, beliebige
Gate-Namen erlaubt (auch projekteigene):

```yaml
# .meta-config/project.yaml
release-gates:
  artifact-freshness: { enabled: true }
  docker-image-scan: { enabled: true, dockerfile: Dockerfile }
  action-pin-validation: { enabled: false }
  my-project-custom-check: { enabled: true }   # eigener Name, kein Preset kennt ihn — geht trotzdem
```

`config/project-config.schema.json` definiert dafür `release-gates` als offenes Objekt
(`additionalProperties: { type: object, properties: { enabled: boolean }, additionalProperties: true }`)
— das deckt sowohl "Schritte aktivieren/deaktivieren" als auch "Schritte mit Zusatzkonfig
anpassen" ab (Zusatzschlüssel neben `enabled` sind für das jeweilige Gate-Script reserviert, s. o.
bei `docker-image-scan`).

**Precedence (höchste zuerst):**

1. `release-gates.<name>.enabled` in `project.yaml` (Projekt-Override, auch für unbekannte Namen).
2. Preset-Default: `config/dod-presets.yaml` → `presets.<dod-preset>.release-gates.<name>`
   (nur für die drei eingebauten Gate-Namen definiert).
3. Der `enabled_by_default`-Header des jeweiligen Gate-Scripts selbst (Fallback — greift z. B. für
   ein neues eingebautes Gate, das noch in keinem Preset gepflegt ist).

DoD-Preset-Defaults für die drei eingebauten Gates (spiegelt bewusst das bestehende
`security-audit`-Muster — CVE-/Pin-Scans sind security-audit-artige Checks):

| Preset | `artifact-freshness` | `docker-image-scan` | `action-pin-validation` |
|---|---|---|---|
| `full` | aus | aus | aus |
| `standard` | aus | aus | aus |
| `rapid-prototyping` | aus | aus | aus |
| `spec-optional` | aus | aus | aus |
| `spec-driven` | aus | aus | aus |
| `spec-certified` | **an** | **an** | **an** |

Diese Auflösung passiert **zu `sync.py`-Build-Zeit**: `scripts/lib/dod.py::resolve_release_gates()`
liefert die effektiven Enabled-Werte, `scripts/lib/hooks.py::sync_release_gates()` schreibt sie als
festen `{{RELEASE_GATE_ENABLED_DEFAULT}}`-Wert direkt in jedes kopierte, eingebaute Gate-Script
(dasselbe sync-time-Platzhalter-Muster wie `{{AGENT_META_PROVIDER}}` bei den anderen Hooks —
wirkungslos für projekteigene Gates, da sie nie durch `sync.py` laufen). Nach jeder Änderung an
`dod-preset` oder `release-gates` in `project.yaml` muss `sync.py` erneut laufen, damit die
eingebauten Gates die neuen Defaults tragen.

## One-off-Override per Umgebungsvariable

Jedes eingebaute Gate-Script liest zusätzlich `PRE_RELEASE_GATE_ENABLED` (`: "${PRE_RELEASE_GATE_ENABLED:=<sync-time-default>}"`
— greift nur, wenn die Variable beim Aufruf noch nicht gesetzt ist). Für einen einzelnen,
gezielten Lauf lässt sich damit ein einzelnes Gate-Script direkt (nicht über den Dispatcher)
übersteuern, ohne `project.yaml` anzufassen oder `sync.py` erneut laufen zu lassen:

```bash
PRE_RELEASE_GATE_ENABLED=true bash .claude/hooks/release-gates/docker-image-scan.sh
```

**Wichtige Einschränkung:** alle eingebauten Gate-Scripts nutzen denselben Variablennamen
(`PRE_RELEASE_GATE_ENABLED`). Setzt man die Variable stattdessen beim Aufruf des **Dispatchers**
(`pre-release-check.sh`), erben alle Kind-Prozesse (jedes gestartete Gate-Script) denselben Wert —
der Override wirkt dann auf **alle** eingebauten Gates gleichzeitig, nicht nur auf eines. Für einen
selektiven One-off-Override ein einzelnes Gate-Script direkt aufrufen (wie oben), nicht den
Dispatcher.

## Beispiele

### Beispiel 1: Django + Docker + GitHub Actions

`.meta-config/project.yaml`:

```yaml
dod-preset: spec-driven
release-gates:
  artifact-freshness: { enabled: true }
  docker-image-scan: { enabled: true }
  action-pin-validation: { enabled: true }
```

`.agent-meta/generated-artifacts.yaml`:

```yaml
artifacts:
  - source: pyproject.toml
    generated: dist/django_app-*.whl
  - source: locale/
    generated: locale/de/LC_MESSAGES/django.mo
```

`Dockerfile` (wird automatisch von `docker-image-scan` erkannt, kein Extra-Setup nötig):

```dockerfile
FROM python:3.13-slim AS build
COPY . /app
RUN pip wheel --wheel-dir=/wheels /app

FROM python:3.13-slim
COPY --from=build /wheels /wheels
RUN pip install /wheels/*.whl
```

`.github/workflows/ci.yml` — Action-Pins werden automatisch erkannt, solange `gh` im
Release-Environment installiert und authentifiziert ist. Kein weiteres Setup nötig. Nach dem
nächsten `sync.py`-Lauf: `bash .claude/hooks/pre-release-check.sh` (der `release`-Agent macht das
automatisch).

### Beispiel 2: Next.js + CDN, kein Docker, plus eigenes Gate

`.meta-config/project.yaml`:

```yaml
dod-preset: standard
release-gates:
  artifact-freshness: { enabled: true }
  lighthouse-budget-check: { enabled: true }   # projekteigenes Gate, kein Preset kennt es
```

```yaml
# .agent-meta/generated-artifacts.yaml
artifacts:
  - source: src/
    generated: .next/BUILD_ID
  - source: package.json
    generated: public/sitemap.xml
```

`.claude/hooks/release-gates/lighthouse-budget-check.sh` (projekteigen, sync.py fasst es nie an):

```bash
#!/bin/bash
set -u
cd "${PROJECT_ROOT:-$PWD}" || exit 1
: "${PRE_RELEASE_GATE_ENABLED:=false}"   # eigener Default, keine Sync-Time-Injektion nötig
[ "$PRE_RELEASE_GATE_ENABLED" = "true" ] || { echo "[SKIP] lighthouse-budget-check: disabled"; exit 0; }

npx lighthouse-ci autorun --config=.lighthouserc.json
```

Zusätzlich einmalig in `.claude/hooks/release-gates/.allowed-gates` eintragen (issue #598 —
sonst wird die Datei mit `[SKIP] ... not on the release-gates allowlist` übersprungen):

```bash
echo "lighthouse-budget-check.sh" >> .claude/hooks/release-gates/.allowed-gates
```

Kein `Dockerfile` vorhanden → `docker-image-scan` überspringt sich automatisch (kein Setup nötig,
kein Fehlschlag, unabhängig von seiner Enabled-Konfiguration). `action-pin-validation` ist hier gar
nicht erst in `release-gates:` gelistet → fällt auf den Preset-Default (`standard` → aus) zurück.
Ergebnis: `artifact-freshness` und das projekteigene `lighthouse-budget-check` laufen aktiv,
`docker-image-scan` und `action-pin-validation` liefern `[SKIP]` — genau das gewünschte Verhalten
für diesen Stack.

## Manuelles Ausführen (ohne Release-Agent)

```bash
bash .claude/hooks/pre-release-check.sh
echo $?   # 0 = alle Gates bestanden/übersprungen, 1 = mind. ein Gate fehlgeschlagen

# Ein einzelnes eingebautes Gate direkt aufrufen (z. B. zum Debuggen):
bash .claude/hooks/release-gates/docker-image-scan.sh

# One-off-Override für genau dieses eine Gate:
PRE_RELEASE_GATE_ENABLED=true bash .claude/hooks/release-gates/docker-image-scan.sh
```
