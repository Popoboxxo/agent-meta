# Viz-Architektur-Entscheidungen

Dokumentation wichtiger Design-Entscheidungen im Visualisierungs-System.

## Stabile Edge-IDs (`edge-FROM-TO`)

**Entscheidung:** Cytoscape-Kanten verwenden das Schema `edge-<from>-<to>` statt `edge-<index>`.

**Begründung:**
- Idempotente Graph-Updates: Ein erneutes Hinzufügen einer bekannten Kante erhöht nur den `count`-Counter statt eine neue Kante anzulegen.
- Verhindert visuelles Aufblähen des Graphen bei Polling-Updates (alle 2 Sekunden im Live-Modus).
- Konsistente Identität: Die Kante zwischen zwei Agenten hat immer dieselbe ID, unabhängig davon wie oft sie aktualisiert wird.

**Trade-offs:**
- Keine Unterscheidung zwischen mehreren parallelen Delegationen mit unterschiedlichen Tasks. Der `tasks`-Array auf der Kante sammelt alle Task-Namen.
- Bei sehr langen Agenten-Namen können IDs lang werden. Praktisch irrelevant bei unseren Kurznamen.

**Implementierung:**
- `viz-report.py`: `edge_map: dict[tuple, dict]` akkumuliert Kanten über `(from, to)` als Key.
- `live-dashboard.html`: `applyStateToGraph()` erzeugt IDs via `` `edge-${e.from}-${e.to}` ``.

---

## Zwei-Modi-System (Live vs. Replay)

| Modus | Datenabruf | Mechanismus | State-Strategie |
|-------|-----------|-------------|-----------------|
| Live  | Polling alle 2s `/api/state?window=X` | `setInterval` | Vollzustand wird immer ersetzt |
| Replay| Einmalig `/api/events?window=X` | `setTimeout`-Chain | Inkrementeller Aufbau Event für Event |

Beide Modi teilen `applyStateToGraph()`, `renderAgents()`, `renderTimeline()`.

---

## Inactivity-Watcher

**Prinzip:** Der Server beendet sich selbst wenn keine Aktivität mehr festgestellt wird.

**Aktivitätsdefinition:** `max(last_request_time[0], event_log.stat().st_mtime)`

- `last_request_time[0]`: Zeitpunkt des letzten HTTP-Requests (Browser-Polling zählt als Aktivität).
- `st_mtime`: Zeitpunkt der letzten Logfile-Änderung (neue Events).

**Warum beides?** Ein User kann das Dashboard offen haben und aktiv zuschauen, ohne dass neue Events geschrieben werden (z.B. während einer langen Agenten-Ausführung). HTTP-Polling ist das korrekte Aktivitätssignal für "jemand schaut zu".

---

## Thread-Safety

`events.jsonl` ist append-only. Trotzdem schützt ein `threading.RLock` in `lib/viz.py` alle Lese- und Schreiboperationen, da:

1. Der WSGI-Server ist threaded (`ThreadingMixIn`).
2. Paralleles Lesen (`/api/state`) und Schreiben (Agenten-Events) könnte zu halb gelesenen JSONL-Zeilen führen.
3. `clear-log` führt einen atomaren `open(path, "w")` unter dem Lock durch.
