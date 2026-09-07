# SE-Kaskade: ADR-Standard

Verbindlicher MADR-Minimal-Standard für Architecture Decision Records in der
SE-Kaskade (Issue #339 B1). Normativ nur bei aktiver SE-Kaskade.

{{#if SE_ENABLED}}

## Verzeichnis- und Namenskonvention

- Ablageort: `{{SE_BASE_DIR}}/ADR/ADR-NNN_kurztitel.md`
- `NNN` = 3-stellig, monoton steigend (ADR-001, ADR-002, …), niemals wiederverwendet.
- `kurztitel` = lowercase snake_case, ASCII, ohne Versions- oder Datumssuffix
  (Versionierung via Git, siehe Artefakt-Taxonomie).

## Frontmatter-Pflichtfelder

| Feld | Typ | Werte |
|------|-----|-------|
| `adr_id` | string | `ADR-NNN` |
| `title` | string | Kurztitel |
| `status` | enum | `proposed \| review \| accepted \| deprecated \| superseded` |
| `date` | date | ISO-8601 (`YYYY-MM-DD`) |
| `deciders` | array | Agenten-/Rollen-Namen, die entschieden haben |
| `affected_reqs` | array | REQ-IDs, die diese Entscheidung betreffen (mind. 1) |
| `superseded_by` | string | `ADR-NNN` — nur wenn `status: superseded` |

Schema: `schemas/se-adr.schema.json`.

## Body-Struktur (MADR-Minimal)

- `## Kontext` — Problem, Constraints, Treiber
- `## Alternativen` — **mindestens 2** Optionen mit Abwägung, inkl. rejected
- `## Entscheidung` — die gewählte Lösung, präzise und prüfbar
- `## Konsequenzen` — positive UND negative Folgen

## Lifecycle

```
proposed → review → accepted
                  → deprecated
                  → superseded (Referenz auf Nachfolge-ADR via superseded_by)
```

- `proposed` löst automatisch den Review-Trigger aus (`se-critic` prüft gegen
  Architekturgesetze und betroffene REQs).
- Nur `se-architect` ändert den Status; Statuswechsel werden in der ADR-Datei
  dokumentiert (Datum + Grund).
- Ein `superseded`-ADR bleibt erhalten (Audit-Trail) und verweist via
  `superseded_by` auf den Nachfolger.

## REQ ↔ ADR-Verlinkung

- Jedes ADR referenziert **mindestens eine** REQ-ID in `affected_reqs`.
- Jede REQ listet die sie betreffenden, noch nicht `accepted` ADRs im
  Frontmatter-Feld `open_adrs: []`.
- Beim Statuswechsel auf `accepted` (oder `deprecated`/`superseded`) entfernt
  `se-architect` die ADR-ID aus `open_adrs` aller `affected_reqs`; die
  Rückverfolgbarkeit bleibt über `affected_reqs` im ADR erhalten.
- Architektur-relevante REQs (`arch_impact: true`) ohne ADR-Bezug sind ein
  Kaskaden-Verstoß: `se-architect` legt für jeden `arch_trigger` einen ADR an
  oder referenziert den bestehenden.

## ADR-Template

```markdown
---
adr_id: ADR-NNN
title: "<kurztitel>"
status: proposed
date: <YYYY-MM-DD>
deciders: [se-architect, user]
affected_reqs: [REQ-L{n}-NNN]
superseded_by: null
---

# <Titel>

## Kontext
<Problem, Constraints, Treiber — Problem-Statement, keine Lösung>

## Alternativen
- <Option 1> — <Abwägung>
- <Option 2 (rejected)> — <Abwägung>

## Entscheidung
<Die gewählte Lösung, präzise und prüfbar formuliert.>

## Konsequenzen
- Positiv: <…>
- Negativ: <…>
```

## Verantwortlichkeit

- **Erstellen:** `se-architect` (bei `arch_impact: true` / `arch_trigger`, bei
  Architektur-Blockern aus V&V, bei Entscheidungen mit Wirkung über eine Zelle hinaus).
- **Review:** `se-critic` (Lifecycle `proposed → review`).
- **Impact-Prüfung:** `se-requirements` matcht neue REQs per Keyword gegen
  ADR-Titel und trägt Treffer in `open_adrs` ein (Bottom-Up, Issue #339 B6).

{{/if}}
