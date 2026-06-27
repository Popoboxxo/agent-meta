# Prompt Engineering Evaluation: se-integration-and-test-manager

**Datum:** 2026-06-27
**Agent:** prompt-engineer
**Target:** `agents/1-generic/se-integration-and-test-manager.md`

## 1. Zielsetzung & Analysekriterien
Das Ziel dieses Reviews ist die maximale Verschlankung (Token-Reduktion) und Struktur-Optimierung des System-Prompts, ohne fachliche Funktionalität oder Meta-Framework-Regeln zu verletzen. Die Evaluierung basiert auf:
- Token-Kompression (Structured Prompting)
- Latenz-Optimierung (Output Shaping)
- Robustheit (XML-Delimiters, Contract-First A2A)

---

## 2. Ist-Zustand (Findings)

**Positive Aspekte (beibehalten):**
- Starke Nutzung von Tabellen (Integrationsstrategie), was dem *Structured Prompting* entspricht.
- Klare Persona-Definition am Anfang.
- Robuste Handlebar-Bedingungen (`{{#if DOD_REQ_TRACEABILITY}}`) verhindern unnötigen Kontext bei inaktiven Features.

**Schwachstellen (Optimierungspotenzial):**
1. **Token-Heavy JSON Schema (Zeile 113-172):** Ein massives JSON-Beispiel (ca. 60 Zeilen) verbraucht durch Quotes, Braces und Whitespaces extrem viele Tokens.
2. **Redundante Delegations-Instruktionen:** Delegation wird an drei separaten Stellen erklärt ("Delegations-Protokoll" Tabelle, "Delegations-Sequenz" Liste, und am Ende unter "Delegation"). Das ist ineffizient und fehleranfällig.
3. **Fehlende XML-Delimiters:** Instruktionen, Formate und Projektkontext verschwimmen als reine Markdown-Headings. Gemäß OpenAI/Lakera sollten System-Limits und Output-Formate in XML-Tags gekapselt werden.
4. **Boilerplate Templates (Zeile 98 & 174):** Hardcodierte Checklisten und Report-Templates sind langatmig.
5. **Kein Output-Shaping:** Es fehlen Anweisungen zur Reduzierung der "Chattiness" (Latenz-Treiber bei der Generierung).

---

## 3. Konkrete Optimierungsvorschläge (Actionable Insights)

### Vorschlag 1: Migration des Output-Schemas von JSON zu YAML oder TypeScript-Interface
**Aktion:** Ersetze das lange JSON-Beispiel durch ein kompaktes YAML-Schema oder ein TypeScript-Interface.
**Begründung:** LLMs verstehen YAML/TS exzellent. Dies spart ca. 30-40% der Tokens in diesem Block, da Klammern und Anführungszeichen wegfallen.
**Beispiel:**
```yaml
integration_plan_id: "INT-001"
strategy: "Bottom-Up"
strategy_rationale: "..."
integration_levels:
  - level: 1
    components: ["COMP-001"]
    test_agent: "se-test-engineer"
```

### Vorschlag 2: Konsolidierung der Handoff-Contracts (A2A) via XML
**Aktion:** Führe die drei Delegations-Abschnitte (Tabelle, Sequenz, Aufzählung) in einem einzigen `<handoff-contracts>` XML-Block zusammen.
**Begründung:** Folgt dem Paradigma "Agenten-Verträge & Handoffs als APIs" aus den 2026 Context Engineering Best Practices.
**Beispiel:**
```xml
<handoff-contracts>
  <contract target="se-test-engineer" input="Component spec" output="Test cases"/>
  <contract target="se-verifier" input="Requirement" output="Verification report"/>
  <contract target="se-validator" input="L1 spec" output="Validation report"/>
</handoff-contracts>
<workflow>
  1. Integrationsplan erstellen.
  2. Pro Komponente iterieren: Test-Definition -> Verifizierung.
  3. Vollintegration -> System-Level Validierung.
</workflow>
```

### Vorschlag 3: Komprimierung der Templates ("V&V-Gesamtbericht" & "TodoWrite")
**Aktion:** Statt das gesamte Markdown-Template auszuschreiben, beschreibe die Struktur deklarativ.
**Begründung:** Reduziert redundante Wörter.
**Beispiel:** Statt eines kompletten Tabellen-Mockups, schreibe:
*"Der V&V-Bericht muss enthalten: Integrationsstrategie, Status-Tabelle pro Ebene (L3-L1 mit Raten), Offene Issues und (falls zutreffend) Traceability-Matrix."*

### Vorschlag 4: Strikte Strukturierung durch Delimiter
**Aktion:** Kapsle den Input (`{{PROJECT_CONTEXT}}`), die Regeln (`<rules>`) und das Output-Format (`<output-schema>`) in klar definierte Tags.
**Begründung:** Schützt vor Indirect Prompt Injections (Lakera) und lenkt die Attention des LLMs präzise.

### Vorschlag 5: Output Shaping (Latency Reduction)
**Aktion:** Füge eine "Verbosity Control"-Regel hinzu.
**Begründung:** "Weniger Output-Tokens" ist die wichtigste Latenz-Metrik.
**Zusatz im Prompt:** *"Output Shaping: Antworte extrem prägnant. Verwende für Koordination kurze Bullet-Points. Vermeide erklärende Prosa."*

---

## 4. Fazit
Durch die Konsolidierung der Delegations-Regeln, die Umstellung auf YAML/TS-Schemas und die Einführung von XML-Tags kann der Prompt schätzungsweise um **25-35% der Tokens gekürzt** werden. Dies wird die Latenz (Time-to-First-Token) des Integrations-Managers deutlich verbessern und die A2A-Handoffs robuster gegen "Drift" machen.
