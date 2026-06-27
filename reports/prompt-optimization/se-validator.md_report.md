# Prompt Optimization Report: `se-validator`

**Datum:** 2026-06-27
**Agent:** prompt-engineer
**Target:** `agents/1-generic/se-validator.md`

---

## 1. Status Quo & Analyse (Best Practices Assessment)

Das Template `se-validator.md` ist inhaltlich bereits sehr stark. Die Trennung zwischen System-Validierung (L1, Black-Box, *Did we build the right system?*) und Verifizierung (White-Box, *Did we build it right?*) ist vorbildlich.

**Identifizierte Probleme & Verschlankungspotenzial:**
1. **Redundanz im Output-Format:** Es gibt ein textbasiertes "User Journey Template" UND ein massives "JSON Output Schema". Da der Agent am Ende ein JSON generieren soll, ist das Text-Template toter Code und verwirrt die Instruction-Following-Logik.
2. **Token-Verschwendung (Verbosity):** Das JSON-Beispiel ist sehr lang (über 40 Zeilen) und nutzt geschwätzige Keys (`stakeholder_needs_reviewed`, `validation_verdict`).
3. **Fehlender Reasoning-Space (Chain-of-Thought):** Der Agent soll Journeys "simulieren" und analysieren. Wenn er jedoch direkt JSON ausgeben soll ("Return your final output only as a JSON object"), fehlt ihm der Raum zum "Denken". Dies führt zu schlechteren Validierungsergebnissen.
4. **Widersprüchliche Output-Instruktionen:** Es heißt einerseits "Return your final output only as a JSON object" und andererseits "Write full output (frontmatter + JSON) to a temporary file". Dies muss entflochten werden (Was geht ins Tool, was in den Chat?).
5. **Verteilte Regeln:** "Strict Scope Boundary" und "Generic Validation Laws" überlappen sich inhaltlich.

---

## 2. Konkrete Optimierungsvorschläge (Actionable Insights)

### A. TypeScript Interface statt JSON-Beispiel (Prompt Compression)
Ersetze das lange JSON-Beispiel durch ein kompaktes TypeScript Interface. LLMs parsen TypeScript überragend gut, es spart ca. 50% der Token in diesem Abschnitt und zwingt das Modell zu einem exakten Schema mit kürzeren Keys.

### B. Reasoning-Block einführen (OpenAI Best Practice)
Erlaube dem Agenten explizit, in einem `<simulation>` XML-Block laut nachzudenken, *bevor* er das finale File schreibt. Dort kann er die Journeys gedanklich durchspielen, was Fehler reduziert.

### C. Redundanzen radikal löschen (Verschlankung)
- **Löschen:** Die Sektion `## User Journey Template` kann ersatzlos gestrichen werden, da die Struktur im JSON/TS-Schema impliziert ist.
- **Zusammenfassen:** "Post-Validation Handoff" und "Delegation" zu `## Handoff & Delegation` mergen. "Strict Scope Boundary" und "Generic Validation Laws" zu `## Core Principles` vereinen.

### D. Workflow-Vertrag schärfen (Agent-Meta Framework)
Definiere den Ablauf präzise als Vertrag:
1. **Denken:** Im Chat-Output mit `<simulation>` Block.
2. **Speichern:** Nutze das Bash/Write Tool, um das File mit Frontmatter + JSON zu schreiben.
3. **Antworten:** Beende den Turn mit einer ultrakurzen Handoff-Message an den Orchestrator (Verdict + Pfad).

---

## 3. Refactored Prompt Proposal (Auszug für Verschlankung)

Hier ist ein Vorschlag, wie die zentralen Sektionen massiv verschlankt und modernisiert werden können, ohne Funktionalität zu verlieren:

```markdown
## Core Principles (Scope & Laws)
- **L1 Black-Box Only:** No code/implementation inspection. Validate inputs -> expected outcomes based on stakeholder needs. Internal inspection belongs to `se-verifier`.
- **User-Centricity:** Validate from the user's perspective.
- **Question:** "Did we build the **right** system?" (Stakeholder Value)

## Responsibilities & Workflow
1. **Load Needs:** Read L1 stakeholder requirements (`se-requirements` output).
2. **Simulate Journeys:** Construct and mentally walk through End-to-End journeys for each need inside a `<simulation>` block.
3. **Evaluate Coverage:** Map journey results to needs (Fulfilled / Partially / Not / Over-Engineered).
4. **Persist Report:** Write the final validation report (Frontmatter + JSON) to the file system using the defined path.
5. **Handoff:** Return a brief summary and the file path to the caller.

## Output Schema (TypeScript Contract)
The written report file MUST contain standard YAML frontmatter followed by a JSON block matching this schema:

```typescript
interface ValidationReport {
  id: string; // e.g. VAL-001
  level: "L1";
  needs: {
    id: string; // REQ-001
    journeys: { 
      name: string, actor: string, trigger: string, 
      steps: string[], outcome: string, signal: string, 
      coverage: "Fulfilled"|"Partially"|"Not"|"Over-Engineered", 
      gaps: string[] 
    }[];
    status: "Fulfilled"|"Partially"|"Not";
  }[];
  blocking_issues: string[];
  warnings: { need_id: string, issue: string, recommendation: string }[];
  verdict: "APPROVED" | "APPROVED_WITH_WARNINGS" | "BLOCKED";
  rationale: string;
}
```

## Step Persistence & Handoff
1. Write the file to: `{SE_BASE_DIR}/{parent_path}/L{level}/{FolderName}/validation/L{level}_{FolderName}_Validation.md`
2. **File Format:**
   ```yaml
   ---
   step: validation
   agent: se-validator
   status: done
   ---
   ```
   `[INSERT JSON REPORT HERE]`
3. **Escalation / Handoff:**
   - APPROVED / WARNINGS: Hand over to `se-orchestrator`.
   - BLOCKED: Hand over to `se-orchestrator` (cascade to `se-requirements` or `se-architect`).
```

**Ergebnis der Verschlankung:**
- Reduktion von ca. 200 Zeilen auf ca. 120 Zeilen (40% Token-Ersparnis beim Lesen des System Prompts).
- Deutlich verbesserte Maschinenlesbarkeit durch TS-Interface.
- Bessere Validierungsqualität durch den expliziten `<simulation>` Block für Chain-of-Thought.
