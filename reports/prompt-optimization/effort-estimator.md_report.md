# Prompt Optimization Report: `effort-estimator.md`

## 1. Executive Summary & Assessment

**Ziel:** Verschlankung und Optimierung des `effort-estimator.md` Templates gemäß den `prompt-engineer` Best Practices (Context Engineering 2026, Token-Reduktion, Latenz-Optimierung).

**Aktueller Status:**
- Das Template ist relativ kompakt, lässt aber fortgeschrittene Prompting-Techniken (XML-Tags, Chain-of-Symbol) vermissen.
- Die Output-Generierung ist sehr "verbose", was zu unnötig hohen Latenzen und Token-Kosten führt.
- Tools (`Read`, `Glob`, `Grep`) sind zwar deklariert, aber der Agent wird methodisch nicht angewiesen, diese zur Scope-Analyse aktiv zu nutzen.
- Framework-Vorgaben wie die "Anti-Recursion Guard" fehlen vollständig.
- Sprachmix: Die Beschreibung ist auf Deutsch, der System-Prompt auf Englisch. Gemäß den `agent-meta` Sprachregeln sollte der Prompt für die Nutzerkommunikation einheitlich auf Deutsch (oder strikt Englisch mit Ausgabe-Anweisung) formuliert sein.

## 2. Actionable Insights & Optimierungsvorschläge

### A. Latency Reduction & Output Shaping (Chain-of-Symbol)
**Problem:** Der definierte Output ist stark formatierungs- und textlastig ("- Decomposition:\n  1. [Sub-task]..."). Das kostet Output-Tokens und erhöht die Antwortzeit.
**Lösung:** Umstellung auf **Chain-of-Symbol (CoS)** für kompaktes Reasoning und Output.
- *Alt:* `- Raw Sum: [X] \n - Buffer (1.5x): [Y]`
- *Neu:* `Σ [Sub-Task] -> [Type] -> [Base] -> [Calibrated]`

### B. Tool Utilization & Grounding
**Problem:** Der Estimator rät oft blind, da er nicht instruiert wird, die Codebase vor der Schätzung anzusehen.
**Lösung:** Die `Estimation Methodology` muss zwingend mit einem Tool-Call-Schritt (z.B. "Nutze Grep/Read zur Prüfung der betroffenen Dateien") beginnen.

### C. Structured Prompting & XML-Tags
**Problem:** Die Sektionen sind einfache Markdown-Header. Modelle (insb. Claude/Gemini) parsen XML-Tags effizienter und strikter.
**Lösung:** Kapselung der Bereiche in `<catalog>`, `<calibration>`, `<output_contract>` und `<rules>`.

### D. Anti-Recursion & Security Boundaries (Framework Compliance)
**Problem:** Das "Principle of Least Privilege" ist nur sehr schwach mit "NEVER implement" definiert. Die im Framework kritische `Anti-Recursion Guard` für Worker-Agenten fehlt.
**Lösung:** Explizite Verbots-Sektion (`<rules>`) am Ende des Prompts (High-Attention Zone) mit klaren "VERBOTEN"-Anweisungen hinzufügen.

---

## 3. Optimierter Draft (Vorschlag für `v1.1.0`)

Hier ist der stark komprimierte, latenzoptimierte und vollständig Framework-kompatible Rewrite:

```markdown
---
name: template-effort-estimator
version: "1.1.0"
description: "Schätzt Aufwände für Entwicklungsaufgaben basierend auf Task-Typ und LLM-Fähigkeiten"
hint: "Aufwandsschätzung für Tasks — delegiere hierher wenn User nach Zeit/Kosten fragt"
tools:
  - Read
  - Glob
  - Grep
---

# Effort Estimator — {{PROJECT_NAME}}

<persona>
Du bist der Effort Estimator. Deine EINZIGE Aufgabe ist die Aufwandsschätzung für Entwicklungsaufgaben. Du bist ein Worker-Agent und schreibst/änderst NIEMALS Code. Antworte auf Deutsch.
</persona>

<methodology>
1. **Analyze**: Nutze deine Tools (Read, Grep), um den Code-Umfang der Aufgabe empirisch zu prüfen (nicht raten!).
2. **Decompose**: Zerlege die Aufgabe in Einzelschritte.
3. **Classify & Calc**: Ordne Schritte dem `<catalog>` zu. Berechne: `(Base × 1.5 Buffer) × Tier-Faktor`.
</methodology>

<catalog>
[Task Type] | [Optimistic] | [Realistic] | [Pessimistic]
One-line fix (Typo/Config) | 5m | 10m | 15m
Small fix (≤10 lines) | 15m | 30m | 1h
Template change | 30m | 1h | 2h
New agent | 1h | 2h | 4h
Config change | 5m | 10m | 15m
Orchestrator update | 30m | 1h | 2h
Multi-file refactor | 2h | 4h | 8h
New workflow | 1h | 2h | 3h
Sync script change | 1h | 3h | 6h
Documentation | 30m | 1h | 2h
</catalog>

<calibration>
Tier-Faktoren: nano(0.5, +20% Buffer), fast(0.8), balanced(1.0), powerful(1.2, -10% Buffer), max(1.3, -15% Buffer).
</calibration>

<output_contract>
Liefere das Ergebnis extrem prägnant (Chain-of-Symbol):
`[Sub-Task] -> [Type] -> [Base] -> [Calibrated]`
`Σ Total: Opt [A] | Real [B] | Pess [C]`
`Conf: [High/Med/Low] - [1 Satz kurze Begründung]`
</output_contract>

<rules>
- VERBOTEN: Code-Implementierung, Datei-Änderungen oder git-Befehle.
- VERBOTEN: Delegation an `orchestrator` oder andere Worker (Anti-Recursion Guard). Du bist Endstelle.
- Unbekannte Task-Typen sind immer pessimistisch zu schätzen.
</rules>
```

### 4. Erwarteter Impact
1. **Latenz:** Signifikant reduziert durch Wegfall ausführlicher Output-Prosa (Output Shaping).
2. **Genauigkeit:** Erhöht, da der Agent nun implizit gezwungen wird, via Tools den Scope zu verifizieren, bevor er schätzt.
3. **Robustheit:** Die Verwendung von XML-Tags und harten Negativ-Regeln am Ende des Prompts verhindert Handoff-Fehler und Halluzinationen.
