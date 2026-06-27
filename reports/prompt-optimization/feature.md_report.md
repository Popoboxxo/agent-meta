# Prompt Engineering Report: Streamlining `feature.md`

**Agent Persona:** `prompt-engineer`
**Target File:** `agents/1-generic/feature.md`
**Zielsetzung:** Maximale Verschlankung (Token-Reduktion) und Latenz-Optimierung ohne Verlust von Funktionalität oder Framework-Compliance (agent-meta).

---

## 1. Analyse des Ist-Zustands

Die Datei `feature.md` implementiert den Feature-Lifecycle als Worker-Agent, der Aufgaben delegiert. Aktuell umfasst sie 278 Zeilen. Aus Sicht des **Context Engineerings 2026** leidet sie unter "Prompt-Bloat":
- **Übermäßige Prosa:** Die Schritte 1 bis 8 sind jeweils als eigene Markdown-Header mit ausführlichen, textuellen Delegations-Beispielen ausformuliert. Das kostet viele Token und erschwert dem LLM das schnelle Parsen ("Lost in the Middle"-Gefahr).
- **Redundante Payload-Beispiele:** Das A2A-Handoff-Format (Zeilen 78-88) und das Kontext-Format (Zeilen 94-109) enthalten große Code-Beispiele, obwohl das Framework ohnehin auf Schemata verweist.
- **Fehlende Komprimierung:** Anweisungen sind stark erzählend statt strukturiert.

## 2. Actionable Insights & Optimierungsvorschläge

Gemäß den Best Practices für **Prompt Compression** und **Latency Reduction** können wir die Token-Last signifikant senken:

### 2.1. Structured Prompting für den Lifecycle (Größte Einsparung)
**Problem:** Die Sektionen "Schritt 1" bis "Schritt 8" nehmen über 120 Zeilen ein. Jede Sektion wiederholt Phrasen wie "Delegiere an: X" und "Aufgabe: Y".
**Lösung:** Wandle die narrativen Einzelschritte in eine kompakte **State-Machine-Tabelle** um. LLMs sind exzellent darin, tabellarische Workflows systematisch abzuarbeiten.

*Vorher:* (15+ Zeilen pro Schritt)
```markdown
## Schritt 3 — Tests schreiben (TDD Red Phase)
Delegiere an `tester`:
...
Delegiere an: tester
Aufgabe: Schreibe Tests für [REQ-ID]...
```

*Nachher:* (Alle Schritte in einer Tabelle, ca. 20 Zeilen gesamt)
```markdown
## Lifecycle-Steps (State Machine)
Führe diese Schritte sequenziell (bzw. parallel wo `∥` markiert) aus.
| Step | Target Agent | Payload / Task | Erfolgskriterium |
|---|---|---|---|
| 1 | `git` | Branch `feat/<name>` von main erstellen | Branch existiert |
| 2?| `requirements`| User-Anforderung übergeben | `REQ-ID` erhalten |
| 3?| `tester` | TDD Red: Tests für `[REQ-ID]` schreiben | Tests existieren (failen) |
| 4 | `developer` | TDD Green: `[REQ-ID]` implementieren | Code implementiert |
| 5?| `tester` | Tests für `[REQ-ID]` ausführen | Alle Tests grün |
| 6∥| `validator` | DoD-Check, Traceability prüfen | Validierung bestanden |
| 7?∥|`documenter` | CODEBASE_OVERVIEW.md aktualisieren | Doku aktuell |
| 8 | `git` | Commit `feat([REQ-ID])` + Push + PR | PR erstellt |

*(? = optional je nach aktivem DoD. ∥ = Parallele Ausführung möglich)*
```

### 2.2. Template-Abstraktion: A2A-Envelope & Kontext-Format
**Problem:** Große Code-Blöcke visualisieren das JSON-Format und das Kontext-Format. Das ist für ein LLM, das ohnehin mit strukturierten APIs arbeitet, oft nicht nötig, wenn ein Schema existiert.
**Lösung:** Verweise strikt auf die Verträge (Instruction Referencing), statt sie im Prompt zu duplizieren. Reduziere auf die absoluten Pflichtfelder.

*Nachher:*
```markdown
## A2A Handoff & Kontext (Compact)
- **Eingehend:** Extrahiere `payload` (`t`, `ctx`, `pri`, `con`, `refs`).
- **Ausgehend:** Sende A2A-Envelope (`schema_ref: schemas/handoffs/task-spec.schema.json`).
- **Payload-Pflicht:** Definiere bei JEDER Delegation präzise `TASK` und `EXPECTED_OUTPUT`.
- **HITL:** Bei `requires_human_approval: true` frage: "[Aufgabe]. Soll ich ausführen? (yes/no)".
```
*Einsparung: ~30 Zeilen und zahlreiche JSON/Format-Tokens.*

### 2.3. Output Shaping & Chain-of-Symbol für Error Handling
Die Tabellen für "Fehlerbehandlung" und die "Don'ts" Liste können in eine sehr kompakte Regel-Checkliste zusammengeführt werden. Nutze Symbole (`->`) statt langer Sätze.

*Nachher:*
```markdown
## Rules & Fallbacks
- 🚫 **Verbot:** Selbst Code schreiben/editieren oder vorgegebene Schritte überspringen.
- 🚫 **Verbot:** Commit ohne grüne Tests & bestandene Validierung.
- ❗ **Fallback [REQ-ID fehlt]:** Workflow abbrechen.
- ❗ **Fallback [Test/Validation Fail]:** `-> developer` mit Fehlermeldung delegieren.
- **Abschluss:** Berichte kurz: REQ-ID, Branch, PR-Link, Summary.
```

## 3. Framework Compliance Check

Bei der Umsetzung der Verschlankung müssen folgende Prinzipien des `agent-meta` Frameworks strikt gewahrt bleiben:
- **Anti-Recursion Guard:** Muss im vollen Wortlaut erhalten bleiben. Dies ist eine harte Invariante, um Endlosschleifen zu vermeiden.
- **Template-Variablen (`{{PROJECT_NAME}}`, Handlebars `{{#if...}}`):** Die Konditionen im Header (Zeilen 33-41) bleiben intakt, da sie zur Build-Zeit via `sync.py` evaluiert werden.
- **1-generic Prinzip:** Es werden weiterhin keine LLM-spezifischen oder Provider-spezifischen Termini eingeführt.

## 4. Fazit

Durch den konsequenten Einsatz von **Structured Prompting** (Tabellen) und **Instruction Referencing** (Verzicht auf ausufernde JSON-Beispiele) lässt sich das `feature.md` Template voraussichtlich von 278 Zeilen auf **unter 100 Zeilen** komprimieren. 

**Vorteile:**
1. **Reduzierte Latenz & Kosten:** Ein deutlich schlankerer Context-Input beschleunigt das LLM (Time-to-First-Token).
2. **Präzisere Execution:** Das Modell muss nicht in narrativer Prosa suchen, in welchem Schritt es sich befindet, sondern arbeitet eine klare State-Machine ab.
3. **Striktere Verträge:** Die A2A-Handoffs werden auf das Wesentliche (Task & Expected Output) fokussiert.
