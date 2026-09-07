# SE-Kaskade: Review-Lifecycle

Verbindlicher Review-Lifecycle mit Protokoll-Pflicht und RVW-Finding-IDs für die
SE-Kaskade (Issue #339 B5). Normativ nur bei aktiver SE-Kaskade.

{{#if SE_ENABLED}}

## Lifecycle

```
Open ──► Review (Iteration N) ──► Response ──► Closed
            │                                  ▲
            └─► Iteration N+1 (Re-Review) ─────┘
```

- Jede Iteration ist ein eigener, nummerierter Review-Zyklus — keine
  statuslosen Ad-hoc-Reviews.
- `review_iteration` im REQ-Frontmatter wird mit jeder Iteration inkrementiert
  (monoton steigend, Startwert 0).

## IDs

- **Review-ID:** `RVW-YYYY-MM-DD-NNN` (NNN = 3-stellig, pro Tag monoton steigend).
- **Finding-ID:** `RVW-YYYY-MM-DD-NNN-<k>` (k = 2-stellig innerhalb des Protokolls,
  z. B. `RVW-2026-06-28-001-01`). Jeder Befund trägt eine stabile, referenzierbare ID.
- REQ-Dateien referenzieren Befunde ausschließlich über die Review-ID
  (`review_id:` im Frontmatter) — **nie inline** (siehe L2-Trennregel, B4).

## Review-Protokoll (Pflicht)

Jede Review-Iteration erzeugt ein Protokoll:

- Ablageort: `{{SE_BASE_DIR}}/reviews/REVIEW_<YYYY-MM-DD>_<scope>.md`
  (`scope` = REQ-ID oder Zell-/Systemname, lowercase).
- Frontmatter (Schema: `schemas/se-review.schema.json`):

```yaml
---
review_id: RVW-YYYY-MM-DD-NNN
target_req: REQ-L{n}-NNN
iteration: 1
status: open          # open | response | closed
date: YYYY-MM-DD
reviewer: se-critic
findings:
  - id: RVW-YYYY-MM-DD-NNN-01
    severity: major   # major | minor | info
    category: "<Kategorie, z. B. 'Akzeptanzkriterium unvollstaendig'>"
    description: "<Befund>"
    suggested_fix: "<Konkreter Fix-Vorschlag>"
---
```

- Protokoll-Status folgt dem Lifecycle: `open` (Befunde offen) → `response`
  (Generator hat reagiert) → `closed` (Befunde abgearbeitet).
- Befunde werden im Protokoll beschrieben, NICHT in REQ-Dateien kopiert.

## REQ-Frontmatter-Sync

Nach Abschluss einer Iteration aktualisiert `se-critic` die betroffene REQ:
`review_state` (`open | reviewed | approved`), `last_reviewed` (ISO-8601),
`reviewer` (`se-critic`), `review_iteration` (+1). Bei `approved` zusätzlich
`implementation_state`/`test_status` unangetastet lassen (gehört dem rechten Flügel).

## Suspect-Mark (Bottom-Up, Issue #339 B6)

Setzt `se-critic`, wenn ein Befund an einer REQ eine Re-Derivation des Parents
erfordert:

- Parent-REQ: `review_state: open` + `suspect_children: [<child-req-id>]` im
  Frontmatter + Eskalationsverweis auf die `review_id` des auslösenden Protokolls.
- Suspect-Marks fließen nach oben (Child → Parent) bis zur höchsten betroffenen
  Ebene; der ADR-Impact-Check (siehe ADR-Standard) läuft parallel.
- Max. 2 automatische Re-Derivations-Iterationen, danach User-Approval erzwingen
  (Kaskaden-Bomben-Schutz, Konzept §13).

## Akzeptanzkriterium

Jede REQ mit `review_state: reviewed` oder `approved` hat genau eine
korrespondierende Protokoll-Datei in `{{SE_BASE_DIR}}/reviews/` mit passender
`review_id`. Reviews ohne Protokoll, ohne Iterationsnummer oder ohne formalen
Abschluss-Status sind Kaskaden-Verstöße.

{{/if}}
