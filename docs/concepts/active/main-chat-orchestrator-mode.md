# Konzept: Main-Chat-Orchestrator-Modus

> Status: **Umgesetzt — aktiv**
> Verwandt: `docs/concepts/active/singleton-orchestrator-architecture.md`
> Betroffen: `rules/1-generic/use-orchestrator.md`, `scripts/lib/config.py`, `agents/1-generic/orchestrator.md`, `docs/admin-ui.html`
> Kern-These: **Der `main-chat`-Modus soll ein vollwertiger, schlanker Betriebsmodus sein — nicht nur ein leerer Stub.** Der `main_chat` übernimmt Router- UND Worker-Rolle ohne separaten Orchestrator-Subagenten.

---

## 1. Ist-Zustand / Problem

### 1.1 ORCH_MODE_DISABLED ist heute ein Stub

`sync.py` leitet aus `orchestrator.enabled`/`orchestrator.strict` drei sich gegenseitig ausschließende Flags ab (`scripts/lib/config.py`):

```python
variables["ORCH_MODE_DISABLED"] = "true" if not _orch_enabled else "false"
variables["ORCH_MODE_STRICT"]   = "true" if (_orch_enabled and _orch_strict) else "false"
variables["ORCH_MODE_ADVISORY"] = "true" if (_orch_enabled and not _orch_strict) else "false"
```

In `rules/1-generic/use-orchestrator.md` erzeugt der `DISABLED`-Zweig heute nur:

```markdown
{{#if ORCH_MODE_DISABLED}}
# Main-Chat Mode

Orchestrator is disabled. All tasks run in the main chat. Subagent delegation is optional.
{{/if}}
```

Das ist ein reiner Platzhalter ohne echte Routing-Logik. Es fehlt: Intent-Erkennung, Tier-Auswahl, HITL-Gates, klare Anweisung, wie der `main_chat` selbst arbeitet.

### 1.2 Git-Delegation-Lücke im Disabled-Modus

Die Git-Delegation-Hard-Rule steht im Template unter `{{#unless ORCH_MODE_DISABLED}}`:

```markdown
{{#unless ORCH_MODE_DISABLED}}
## Git Delegation — Hard Rule
...
{{/unless}}
```

**Konsequenz:** Im `main-chat`-Modus wird die Git-Delegation komplett übersprungen — es gibt keinerlei Aussage, ob der `main_chat` git direkt ausführen darf oder weiterhin über den `git`-Agenten gehen soll.

**Entschiedene Frage:** Soll der `main_chat` im `main-chat`-Modus git direkt ausführen dürfen, oder weiterhin über den `git`-Agenten?

- **Option A (git direkt):** Konsistent mit „alles läuft im main_chat" — weniger Delegations-Overhead. Risiko: keine atomare, isolierte Git-Operation; Fehler direkt auf main.
- **Option B (weiterhin git-Agent):** Git bleibt kontrolliert und atomar, auch ohne Orchestrator. Der `git`-Agent ist ein Terminal-Worker und modusunabhängig sinnvoll.

**Entscheidung (User):** Option B als Standard — Delegation über den `git`-Agenten bleibt der DEFAULT-Pfad, auch im `main-chat`-Modus. Ausnahme: Bei expliziter User-Anweisung (z.B. „mach es direkt", „ohne Agent") darf `main_chat` Git-Mutationen für diese eine Aktion selbst ausführen. Git-Disziplin ist orthogonal zur Routing-Frage.

---

## 2. Ziel-Architektur

### 2.1 Grundprinzip

Der `main_chat` übernimmt im `main-chat`-Modus **Router- UND Worker-Rolle** in einer Person. Es wird **kein** separater `orchestrator`-Subagent gespawnt. Der `main_chat` erkennt den Intent, wählt das passende Tier und führt die Aufgabe direkt aus oder delegiert optional an einen einzelnen Worker.

### 2.2 Was aus orchestrator.md in eine schlanke main-chat-Variante wandert

| Verantwortlichkeit | Übernahme im main-chat-Modus |
|--------------------|------------------------------|
| **Intent-Erkennung** | Ja — main_chat klassifiziert die Aufgabe (Feature, Bugfix, Doku, …) |
| **Tier-Auswahl** | Ja — main_chat wählt junior/developer/senior bzw. entscheidet selbst auszuführen |
| **HITL-Gates** | Ja — Human-in-the-Loop-Bestätigungen bleiben (z.B. vor riskanten Operationen) |
| **BARRIER/FANOUT** | Nein — kein Multi-Agent-Fan-out; sequentielle Einzelausführung |
| **A2A-Protokoll-Envelopes** | Nein — kein Envelope-Overhead bei direkter Ausführung |
| **Checkpointing/Session-State** | Reduziert — kein Orchestrator-State-Management nötig |
| **Delegations-Tiefe/Gates** | Vereinfacht — meist Tiefe 0 (main_chat) → 1 (Worker) |

### 2.3 Ohne Multi-Agent-Overhead

Der `main-chat`-Modus verzichtet bewusst auf das A2A-Protokoll, BARRIER-Synchronisation und FANOUT-Parallelisierung. Diese lohnen sich erst bei echter Multi-Agent-Koordination. Für Einzelprojekte mit linearer Arbeitsweise ist der Overhead unnötig — der `main_chat` arbeitet direkt und delegiert höchstens an einen einzelnen Worker.

---

## 3. Modusunabhängige Rules

Folgende Rules sind **orthogonal zum Orchestrator-Modus** und bleiben unverändert — sie brauchen **keine** `ORCH_MODE`-Bedingung:

| Rule | Warum modusunabhängig |
|------|-----------------------|
| `branch-guard.md` | Feature-Branch-Pflicht gilt immer, egal wer committet |
| `commit-conventions.md` | Conventional-Commits-Format ist unabhängig vom Routing |
| `dod-criteria.md` | Definition of Done gilt für jede Aufgabe |
| `issue-lifecycle.md` | GitHub-Issue-Abschluss ist modusunabhängig |

**Entscheidung zur Git-Lücke (siehe 1.2):** Die Git-Delegation-Hard-Rule aus `use-orchestrator.md` wird ebenfalls modusunabhängig — d.h. aus dem `{{#unless ORCH_MODE_DISABLED}}`-Block herausgelöst und immer generiert. Damit schließt sich die Lücke aus Abschnitt 1.2 automatisch. Die Ausnahme (explizite User-Anweisung erlaubt direktes Git im `main-chat`-Modus) wird in der Rule explizit dokumentiert.

---

## 4. sync.py-Verhalten

### 4.1 Orchestrator-Template nicht generieren

Im `main-chat`-Modus soll `agents/1-generic/orchestrator.md` **gar nicht** in `.claude/agents/orchestrator.md` (bzw. die anderen Provider-Verzeichnisse) generiert werden.

- Kein totes `.claude/agents/orchestrator.md` im Zielprojekt
- `sync.py` überspringt die Orchestrator-Rolle, wenn `orchestrator.mode == main-chat`
- Die Delegationstabellen und Routing-Sektionen, die sonst in orchestrator.md landen, entfallen

### 4.2 Konsequenzen für abgeleitete Artefakte

- `INTENT_ROUTING_TABLE` (bisher nur für `orchestrator.md` verwendet) wird für den `main_chat` (in `use-orchestrator.md`) aufbereitet statt der vollen `AGENT_DELEGATION_TABLE` — vermeidet Duplikation der Agent-Beschreibungen, die Claude Code bereits nativ über Subagent-Descriptions injiziert
- Routing-Tabellen wandern in die Main-Chat-Rule
- Der Singleton-Guard-Hook (`orchestrator-guard.sh`) entfällt oder wird deaktiviert, da es keinen Orchestrator gibt

---

## 5. Config-Simplification-Vorschlag

### 5.1 Ist-Zustand: zwei Booleans

Heute steuern zwei Booleans den Modus:

```yaml
orchestrator:
  enabled: true    # true/false
  strict: true     # true/false
```

Daraus werden drei sich gegenseitig ausschließende Flags abgeleitet — ein impliziter Enum, verteilt über zwei Felder. Das ist fehleranfällig (`enabled: false, strict: true` ist ein sinnloser, aber möglicher Zustand).

### 5.2 Vorschlag: expliziter Enum

```yaml
orchestrator:
  mode: strict | advisory | main-chat
```

| `mode` | Bedeutung |
|--------|-----------|
| `strict` | Orchestrator zwingend, kein direkter Dispatch, kein User-Override |
| `advisory` | Orchestrator empfohlen, User-Override und Direct-Dispatch erlaubt |
| `main-chat` | Kein Orchestrator — main_chat ist Router + Worker |

### 5.3 Migrationspfad

`sync.py` leitet den Enum aus den Alt-Feldern ab (Backward-Compatibility), bis Projekte migriert sind:

| Alt (`enabled` / `strict`) | Neu (`mode`) |
|----------------------------|--------------|
| `enabled: false` (strict egal) | `main-chat` |
| `enabled: true` + `strict: true` | `strict` |
| `enabled: true` + `strict: false` | `advisory` |

Ist `orchestrator.mode` gesetzt, hat es Vorrang. Fehlt es, greift die Ableitung aus den Alt-Feldern. So bleiben bestehende `project.yaml`-Dateien funktionsfähig.

---

## 6. Admin-UI-Auswirkung (nur dokumentiert, NICHT Teil dieses Konzepts)

Die Admin-UI rendert den Orchestrator-Modus aktuell über zwei Checkboxen (`docs/admin-ui.html`, General-Panel):

```javascript
genPanel.appendChild(checkboxField("enabled", orch.enabled, ...));
genPanel.appendChild(checkboxField("strict", orch.strict, ...));   // ~Zeile 4249
```

Bei Umsetzung des Enum-Vorschlags (Abschnitt 5) müsste die `strict`-Checkbox durch ein Select mit drei Modi (`strict` / `advisory` / `main-chat`) ersetzt werden. **Diese Änderung ist hier nur dokumentiert, nicht Teil dieses Konzepts.**

---

## 7. Status-Tabelle

| Aspekt | Status |
|--------|--------|
| Problem-Diagnose (Stub + Git-Lücke) | ✓ entschieden |
| Ziel-Architektur (main_chat = Router + Worker) | ✓ entschieden |
| Modusunabhängige Rules identifiziert | ✓ entschieden |
| Git direkt vs. git-Agent im main-chat-Modus | ✓ entschieden (Option B als Default, Ausnahme bei expliziter User-Anweisung) |
| Git-Delegation modusunabhängig machen | ✓ entschieden (aus `{{#unless ORCH_MODE_DISABLED}}`-Block herauslösen) |
| Config-Enum `orchestrator.mode` | ✓ umgesetzt |
| Migrationspfad enabled/strict → mode | ✓ umgesetzt |
| sync.py: orchestrator.md nicht generieren | ✓ umgesetzt (Hook-Deaktivierung bleibt offenes Follow-up) |
| Ausformulierte Main-Chat-Routing-Logik in use-orchestrator.md | ✓ umgesetzt |
| Admin-UI: Checkbox → Select | ✓ umgesetzt |
