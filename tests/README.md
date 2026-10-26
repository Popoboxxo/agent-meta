# Test-Suite

> Zwei Test-Ebenen: die pytest-Suite (`tests/test_*.py`) prüft Sync-Logik,
> Templates und Runtime-Verhalten; das Szenario-Harness
> (`tests/scenarios/run.sh`) synct reale Consumer-Configs in frische
> Temp-Verzeichnisse. Diese Datei beschreibt, wie beide lokal und in CI
> laufen — und an welchen Stellen Worker-Begrenzung Pflicht ist.

## Lokal ausführen

```bash
python3 -m pytest -q -n 8 --dist loadfile        # Standard: gecappt, dateiweise verteilt
python3 -m pytest -q -n 0 tests/test_sync_validation_gate.py   # ein Modul seriell
```

`--dist loadfile` hält ein Test-Modul bei genau einem Worker. Auf geteilten
Hosts ist `-n 8` die Obergrenze.

## Worker-Cap: niemals `-n auto`

**Niemals `-n auto` — auf keinem Host.**

Grund: Jede Worker-Kopie startet ihre eigenen `sync.py`-Subprozesse (Fixtures,
`--validate`, `--check`). `-n auto` skaliert mit der Kernzahl des Hosts und
fächert damit beliebig viele parallele `sync.py`-Läufe auf — `sync.py
--validate` fährt repo-weit die komplette Consistency-Suite, entsprechend
teuer. Die Folge sind Timeout-Flakes und ein überlasteter Host, nicht mehr
Durchsatz. CI nutzt bewusst `-n 2` (Runner-Größe wird als 2-Kern angenommen).

## Subprozess-lastige Module: `-n 0`

Module, die `sync.py` wiederholt per Subprozess treiben, laufen **nie** in den
parallelen Shards, sondern seriell (`-n 0`). Die einzige maßgebliche Quelle sind
die drei `env:`-Gruppen `SUBPROCESS_SHARD_1`, `SUBPROCESS_SHARD_2` und
`SUBPROCESS_SHARD_3` in `.github/workflows/orchestration-test.yml`. Der Job
`subprocess-shard` übergibt genau eine Gruppe als Positionsargumente, die
`test`-Shards bauen aus der Vereinigung ihre `--ignore=<file>`-Argumente.
Aktuell sind es 15 Module mit 451 Tests in drei disjunkten Gruppen
(78 / 183 / 190 Tests).

Die Gruppen sind modul-disjunkt, und der `test`-Job prüft das bei jedem Lauf:
Vereinigung exakt 15 Dateien, keine Datei in zwei Gruppen, jede Datei existiert
— sonst bricht der Job laut ab. Dadurch bleibt die Modul-Isolation erhalten:
kein Modul liegt in zwei Jobs, seine Subprozesse können sich also nicht
stapeln.

Aufnahmekriterium: das Modul startet `sync.py` mehr als einmal pro Modul-Lauf
(Fixture-Sync plus Test-Syncs) oder es ruft den repo-weiten `--validate`-Pfad.
Beispiele: `tests/test_provider_matrix_sync.py` (mehrfacher `sync.py`-Lauf) und
`tests/test_sync_validation_gate.py` (`--validate`). Der Eintrag gehört in
dieselbe Änderung wie das Modul, damit Count-Shards und `subprocess-shard` nicht
auseinanderlaufen.

## Shard-Balance

Die `test`-Shards sind **kein** reiner Count-Split. 17 Dateien sind
setup-dominiert: ihre Repo-Copy-/Render-Fixtures sind modul-scoped, pytest
rechnet ihr Setup also dem ersten Test zu, der sie instanziiert. Die gemessenen
40–260 s gelten pro Fixture-Instanziierung (pro Modul), nicht pro Test; die
Platzierungsgewichte sind pro Datei. Ein reiner Count-Split verteilt diese
Dateien unregelmäßig, und genau das hat die Shard-Laufzeiten auseinandergezogen
(gemessen 1007/501/102 s auf 3.9 und 1000/887/89 s auf 3.12, kritischer Pfad
vorher der serielle Subprozess-Job mit 1864 s).

Deshalb:

- `HEAVY_FIXTURE_SHARD_1`, `HEAVY_FIXTURE_SHARD_2` und `HEAVY_FIXTURE_SHARD_3`
  (env im Workflow) platzieren diese 17 Dateien explizit und disjunkt. Jeder
  `test`-Shard fährt zuerst seinen Heavy-Slice, danach den Rest.
- Der Rest — alle übrigen Dateien — wird weiterhin per Testanzahl aufgeteilt
  (`--splits 3`); die 32 explizit platzierten Dateien (15 Subprozess + 17
  Heavy-Fixture) werden dort per `--ignore` ausgeschlossen.
- Es ist **keine** `.test_durations`-Datei eingecheckt. `--splitting-algorithm
  least_duration` hätte auf einem kalten Runner also keine Lerndaten; die
  Platzierung beruht auf dem gemessenen Setup-Bracket, nicht auf erfundenen
  Dauern.
- Follow-up (optional): ein `workflow_dispatch`-Job mit `--store-durations` und
  danach die Umstellung auf `--splitting-algorithm least_duration`, sobald die
  Datei frisch ist.

## Keine volle Suite lokal

Die komplette Suite dauert lokal rund 50 Minuten (Erfahrungswert auf diesem
Host, keine CI-Zahl) und lastet den geteilten Host stark aus. Lokal deshalb
gezielt einzelne Module/Dateien ausführen; die volle Suite ist Aufgabe der
CI-Shards.

## Zentrale Timeouts

`tests/timeouts.py` bündelt die Subprozess-Timeouts (Hang-Guard, keine
Performance-Zusicherung):

| Konstante | Default | Override |
|-----------|---------|----------|
| `SYNC_TIMEOUT` | 180 s | `AGENT_META_SYNC_TIMEOUT` |
| `SYNC_VALIDATE_TIMEOUT` | 180 s (fällt auf `SYNC_TIMEOUT` zurück) | `AGENT_META_SYNC_VALIDATE_TIMEOUT` |
| `SCRIPT_TIMEOUT` | 60 s | `AGENT_META_SCRIPT_TIMEOUT` |

`SYNC_VALIDATE_TIMEOUT=180` gilt für den repo-weiten `sync.py --validate`-Lauf.
Ein nicht-ganzzahliger, leerer oder nicht-positiver Env-Wert fällt auf den
Default zurück; der Import wirft nie. Neue Subprozess-Tests importieren die
Konstanten, statt eigene Timeouts zu setzen.

Weitere Heavy-Module nutzen noch modul-lokale Obergrenzen; Vereinheitlichung
ist ein Follow-up.

## Szenario-Harness sharden

```bash
bash tests/scenarios/run.sh --list                                  # nur Namen ausgeben
SCENARIO_SHARD=2 SCENARIO_TOTAL=4 bash tests/scenarios/run.sh       # Shard 2 von 4
```

`SCENARIO_SHARD` und `SCENARIO_TOTAL` müssen zusammen gesetzt werden
(1-basiert, `SCENARIO_SHARD <= SCENARIO_TOTAL`). `--list` wendet dieselbe
Auswahl an, ohne ein Szenario zu syncen — damit ist Shard-Abdeckung ohne Lauf
prüfbar. Inhaltliche Abdeckung je Szenario: `tests/scenarios/registry.md`.

## CI-Jobs

| Workflow / Job | Was läuft | Parallelität |
|----------------|-----------|--------------|
| `orchestration-test.yml` → `test` | Erst der Heavy-Fixture-Slice des Shards (5 / 4 / 8 explizit platzierte, setup-dominierte Dateien, 121 / 101 / 224 Tests), dann der Rest der Suite ohne die 32 explizit platzierten Dateien, per Count-Split; Python 3.9 und 3.12 | `-n 2 --dist loadfile`, Rest zusätzlich `--splits 3` |
| `orchestration-test.yml` → `subprocess-shard` | `SUBPROCESS_SHARD_1..3` (5 / 4 / 6 Module, 78 / 183 / 190 Tests) auf Python 3.9 und 3.12, Timeout 30 min | `-n 0` |
| `orchestration-test.yml` → `compat-311` | TOML-Boundary + Code-Hygiene-Dateien sowie zwei subprozess-lastige Sync-Module (`test_provider_matrix_sync.py`, `test_sync_validation_gate.py`) auf Python 3.11 | `-n 0` |
| `validate.yml` → `scenarios` | `tests/scenarios/run.sh` in 4 Shards | kein pytest |
| `validate.yml` → `validate` | Sync-Output erzeugen, Drift-Gate, `--validate`, Frontmatter-Lint | kein pytest |

Damit sind die Endpunkte 3.9 und 3.12 vollständig abgedeckt (Count-Shards,
Heavy-Slices **und** Subprozess-Gruppen), 3.11 nur mit den version-spezifischen
Gates.

`sync.py --validate` läuft bewusst in **beiden** Workflows: hier im
`test`-Job auf 3.9 und 3.12 (gemessen 12–38 s pro Aufruf, deckt das
Cross-Version-Delta ab), in `validate.yml` auf 3.11 zusammen mit Drift-Gate und
Frontmatter-Lint (gemessen 55 s für den kompletten Job). Keine der beiden
Kopien wird entfernt — die Zusatzkosten sind vernachlässigbar, der
Cross-Version-Nutzen ist real.
