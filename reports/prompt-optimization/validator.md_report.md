# Evaluation Report: `validator.md`

## 1. Ausgangslage (Current State)
Die aktuelle Agenten-Definition `validator.md` (v4.1.0) umfasst 215 Zeilen und ca. 7,7 KB. Der Prompt ist funktional ausgereift und nutzt fortgeschrittene Features des `agent-meta` Frameworks wie bedingte Blöcke (`{{#if}}`) und Injection von Kontext. 
Allerdings enthält er redundante Sektionen, fachliche Altlasten (z.B. Code-Qualitäts-Prüfungen, die er nicht mehr durchführt) und sehr detaillierte, weitschweifige Markdown-Templates. Diese verbrauchen unnötige Tokens, erhöhen das Risiko von Halluzinationen und beeinträchtigen die Latenz ("Generation Speed").

## 2. Findings & Actionable Insights (Gemäß Prompt-Engineer Best Practices)

### Finding A: Redundante Traceability-Sektionen (Relevance Filtering)
**Beobachtung:** Abschnitt 1 (Anforderungs-Validierung) und Abschnitt 3 (Traceability-Audit) sind beide vom Feature-Flag `req-traceability` abhängig und behandeln stark überlappende Themengebiete (Mapping von REQ zu Code zu Test). 
**Optimierung:** Führe Sektion 1 und 3 zu einer einzigen Sektion "Traceability & Anforderungs-Validierung" zusammen. Ein kombinierter Workflow reduziert redundante Anweisungen und verringert kognitive Sprünge für das LLM.

### Finding B: Altlasten in "Code-Qualität" (Context Limits & Principle of Least Privilege)
**Beobachtung:** Abschnitt 4 heißt "Code-Qualitäts-Prüfung", erklärt dann aber explizit, dass der Validator genau das **nicht** mehr tut. Dennoch wird die Variable `{{CODE_QUALITY_RULES}}` injiziert. Im Berichtsformat unten wird ebenfalls nochmals "Code-Qualität" referenziert.
**Optimierung:** Entferne Sektion 4 und die Variable `{{CODE_QUALITY_RULES}}` komplett aus diesem Prompt. Ergänze stattdessen in der Sektion "DoD Checkliste" einen einfachen Satz: *"Prüfe, ob der `code-reviewer` gelaufen ist. Führe selbst KEINE Code-Qualitäts-Prüfungen durch."* Das spart massiv Context-Tokens und verhindert, dass das LLM die injizierten Qualitätsregeln fälschlicherweise selbst anwendet.

### Finding C: Verbose Output Templates (Output Shaping & Structured Prompting)
**Beobachtung:** Der Prompt enthält drei ausführliche Markdown-Blöcke für den Output (Validierungsbericht, Traceability-Matrix, Berichtsformat). 
**Optimierung:** Reduziere dies auf ein einziges, kompaktes Berichtsformat am absoluten Ende des Prompts (High-Attention Zone). Die Tabellenstrukturen können als einfache Spalten-Definitionen (z.B. `Tabelle: [REQ-ID | Code | Test | Status]`) anstatt als vollwertige, token-intensive Markdown-Mockups beschrieben werden.

### Finding D: Verstreute Regeln zu Delegation & Don'ts (Template-Abstraktion)
**Beobachtung:** Es gibt eine "Don'ts"-Liste, eine "Delegation"-Liste und den "Anti-Recursion Guard", die sich konzeptionell überschneiden.
**Optimierung:** Führe die "Delegation"-Verweise (an wen bei welchem Problem verwiesen wird) als kompaktes Mapping (`Code → developer`, `Tests → tester`) direkt in die Sektion "Anti-Recursion Guard" oder "Don'ts" ein. 

### Finding E: Weitschweifiger A2A Handoff Block (Chain-of-Symbol & Latency Reduction)
**Beobachtung:** Die Reject-Bedingungen für den `validate_handoff` sind sehr textlastig ausformuliert.
**Optimierung:** Konvertiere die Error-Strings in ein striktes, symbolisches Mapping. Z.B. `source == target -> HARD REJECT("Self-handoff")`. Dies beschleunigt das Parsing für das Modell.

---

## 3. Konkrete Umsetzungsvorschläge (Refactoring)

### Vorschlag 1: Konsolidierung der Sections 1 & 3
Statt zweier `{{#if DOD_REQ_TRACEABILITY}}` Blöcke, erstelle einen kompakten Workflow:
```markdown
{{#if DOD_REQ_TRACEABILITY}}
### 1. Traceability & REQ-Audit
Prüfe die Umsetzung aller Anforderungen (`docs/REQUIREMENTS.md`):
1. **Trace:** Identifiziere das Mapping: REQ-ID → `src/` (Code) → `tests/` (Test).
2. **Validierung:** Erfüllt der Code alle in der REQ geforderten Aspekte? (Melde Lücken oder Over-Engineering).
3. **Ausgabe:** Erstelle eine kompakte Traceability-Matrix (Spalten: REQ-ID, Code-Files, Test-Files, Status ✅/❌/⚠️).
{{/if}}
```

### Vorschlag 2: Entfernung der Sektion 4 (Zeile 107-114)
Lösche diesen Block vollständig. Die Injektion `{{CODE_QUALITY_RULES}}` bläht den Context Window unnötig auf.

### Vorschlag 3: Kompaktes Berichtsformat (ersetzt Zeile 133-158)
Ersetze das lange Mockup durch kompakte Strukturvorgaben:
```markdown
## Berichtsformat
Antworte prägnant in folgender Struktur:
- **Scope:** [Geprüfte Dateien/REQs]
- **Traceability Matrix:** [Tabelle] (nur falls req-traceability aktiv)
- **DoD & Regressions-Tests:** [Status der aktiven Kriterien & Testergebnisse]
- **Fazit & Action Items:** [✅ Bestanden / ❌ Nicht bestanden] - [Fehlende Aspekte mit Verweis auf Folgeagenten, z.B. `developer` oder `tester`]
```
*(Hinweis: Der Verweis auf `any`/`var` in Zeile 150/151 muss gelöscht werden, da keine Code-Quality geprüft wird).*

## 4. Fazit
Durch die Umsetzung dieser Maßnahmen (Entfernen der inaktiven Code-Qualitäts-Regeln, Zusammenfassen der REQ-Traceability, Komprimieren der Templates) kann der Validator-Prompt um schätzungsweise **30-40% an Tokens reduziert** werden. 
Dies führt zu einer schärferen Persona, geringeren Latenzen bei der Token-Generierung und vermeidet "Lost in the Middle"-Effekte, ohne dass essenzielle Validierungs-Regeln des Frameworks verloren gehen.
