# Spec/Plan-Workflow (Master-Rule)

Verbindlicher Ablauf für jede Feature-/Change-Anfrage, die nicht als reine
Kleinständerung (S) durchgeht. Normativ nur, solange der Spec/Plan-Workflow im
Projekt aktiviert ist (`spec-plan-workflow.enabled`); ist er deaktiviert, wird
diese Rule gar nicht ausgeliefert.

## Phasen

```
classify → spec → approve → plan → execute
```

1. **classify** — jede Anfrage VOR jeder Implementierung klassifizieren (siehe unten).
2. **spec** — bei Bounded/Architectural eine Spec nach dem Pflicht-Template schreiben,
   Self-Review, danach `concept-reviewer` (bei L/XL verbindlich).
3. **approve** — explizite Freigabe abwarten; ohne `Status: APPROVED` kein Plan und
   kein Code.
4. **plan** — nach der Freigabe MUSS ein Plan entstehen (`writing-plans`); kein
   Direkteinstieg in Code.
5. **execute** — taskweise Ausführung nach `plan-ledger`.

## Klassifikation (S/M/L/XL ↔ Klasse)

Angekoppelt an das bestehende S/M/L/XL-Routing des Orchestrators:

| Task-Size | Klasse | Route | Artefakt |
|---|---|---|---|
| **S** (≤2 Dateien) | *(Workflow übersprungen)* | direkt `junior-developer` | keines |
| **M** (3–8 Dateien) | **Bounded** | `concept-specifier` → `planner` | Spec + Plan |
| **L** (9–20 Dateien) | **Bounded** (mit Review-Loop) | `concept-specifier` + `concept-reviewer` → `planner` | Spec + Plan |
| **XL** (>20 Dateien) | **Architectural** | `concept-architect` → `concept-specifier` → `planner` | Design + Spec + Plan |
| Recherche ohne Produktionsänderung | **Spike** | `explorer` (Spike-Modus) / `ideation` | Spike-Doc |

**Architectural — qualitatives Zusatzkriterium (F7):** `XL → Architectural` ist NICHT
exklusiv an `>20 Dateien` gebunden. Unabhängig von der Dateizahl ist eine Anfrage
zusätzlich als **Architectural** einzustufen, sobald eines der folgenden Kriterien
zutrifft:

- **öffentliche Schnittstellen/Contracts** sind betroffen,
- **Datenmodell/Schema** ist betroffen,
- **mehr als eine Subsystem-/Komponentengrenze** wird überschritten.

Die Dateizahl bleibt als zusätzliches Signal erhalten.

## Approval-Gate (Convention boundary)

Das Approval-Gate ist eine **Convention boundary** gegen akzidentellen Missbrauch,
keine Security boundary (Terminologie:
`.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`).

- Vollständig greift der Gate nur über die Pipeline-Route (`requires_approval`-Stage).
- Ad-hoc-Dispatches sowie `quick-fix`/`bugfix` haben keine Classify-/Approve-Stage —
  dort ist der Gate rein regelbasiert.
- Ohne explizite Freigabe (`Status: APPROVED`) darf weder ein Plan noch eine
  Implementierung entstehen.

## Spec-Template (Pflichtsektionen)

```markdown
# <Topic> — Spec
> Status: Entwurf | APPROVED (Datum)        # Approval-Marker (maschinenlesbar)
## Problem / Ziel / Nicht-Ziele
## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)
## Datenfluss
## Acceptance Criteria (nummeriert, testbar)
## Offene Fragen + Risiken
## Trace-Anker: spec-id: SPEC-<slug>        # Plan referenziert diesen Wert
```

- Ablage: Specs liegen unter `{{SPEC_PLAN_SPECS_DIR}}`.
- Approval-Marker: `Status: APPROVED` (maschinenlesbar, Datum ergänzen).
- Trace-Anker: `spec-id: SPEC-<slug>` — der Plan referenziert diesen Wert.
- Fragen werden einzeln gestellt (nicht als Fragenkatalog), Lösungen als 2–3 Ansätze
  mit Trade-offs; das Design wird abschnittsweise abgenommen.

## SE-Abgrenzung

Der Spec/Plan-Workflow startet **keine** SE-Kaskade automatisch. Die SE-Kaskade
(`se-cascade-*.md`, Master-Switch `systems-engineering.enabled`) bleibt ein eigener,
explizit aktivierter Prozess. Wird ein Feature als `Architectural` eingestuft, ist ein
optionaler SE-Aufstieg möglich — aber **kein Auto-Start**. Beide Switches bleiben
unabhängig.

## Rollen

Keine neue Rolle: `ideation`, `concept-architect`, `concept-specifier`,
`concept-reviewer`, `planner` und `orchestrator` tragen den Ablauf.
