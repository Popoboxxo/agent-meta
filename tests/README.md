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
parallelen Shards, sondern seriell (`-n 0`). Die einzige maßgebliche Liste ist
`env: SUBPROCESS_HEAVY` in `.github/workflows/orchestration-test.yml`; die
Shards bauen daraus ihre `--ignore=<file>`-Argumente, der Job
`subprocess-serial` übergibt dieselbe Liste als Positionsargumente. Aktuell
sind es 15 Module mit 451 Tests.

Aufnahmekriterium: das Modul startet `sync.py` mehr als einmal pro Modul-Lauf
(Fixture-Sync plus Test-Syncs) oder es ruft den repo-weiten `--validate`-Pfad.
Beispiele: `tests/test_provider_matrix_sync.py` (mehrfacher `sync.py`-Lauf) und
`tests/test_sync_validation_gate.py` (`--validate`). Der Eintrag gehört in
dieselbe Änderung wie das Modul, damit Shards und Serial-Job nicht
auseinanderlaufen.

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
| `orchestration-test.yml` → `test` | Suite ohne `SUBPROCESS_HEAVY`, aufgeteilt in 3 Shards, Python 3.9 und 3.12 | `-n 2 --dist loadfile`, `--splits 3` |
| `orchestration-test.yml` → `subprocess-serial` | `SUBPROCESS_HEAVY` auf Python 3.9 und 3.12 | `-n 0` |
| `orchestration-test.yml` → `compat-311` | TOML-Boundary + Code-Hygiene-Dateien sowie zwei subprozess-lastige Sync-Module (`test_provider_matrix_sync.py`, `test_sync_validation_gate.py`) auf Python 3.11 | `-n 0` |
| `validate.yml` → `scenarios` | `tests/scenarios/run.sh` in 4 Shards | kein pytest |
| `validate.yml` → `validate` | Sync-Output erzeugen, Drift-Gate, `--validate`, Frontmatter-Lint | kein pytest |

Damit sind die Endpunkte 3.9 und 3.12 vollständig abgedeckt (Shards **und**
Serial-Job), 3.11 nur mit den version-spezifischen Gates.
