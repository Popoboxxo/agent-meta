## Status-Tabelle (Pflicht, Issue #678)

Nach jedem Abschluss eines Batch-Mitglieds (FANOUT/PARALLEL_GROUP) und spätestens
bei jedem BARRIER-Punkt eine kompakte Status-Tabelle ausgeben — nicht erst am Ende
der gesamten Pipeline/Session.

| Agent | Task | Status |
|-------|------|--------|
| `<agent>` | `<Ein-Satz-Task>` | `pending` \| `in_progress` \| `done` \| `failed` |

- Eine Zeile pro Batch-Mitglied, in Dispatch-Reihenfolge.
- `Status` wird bei jedem eingehenden Tool-Ergebnis aktualisiert, nicht erst am Ende gesammelt.
- Ersetzt NICHT die BARRIER-Zusammenfassung — sie ist der sichtbare Zwischenstand
  während des laufenden Batches, kein Duplikat.
