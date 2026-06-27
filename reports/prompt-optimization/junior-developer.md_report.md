# Prompt Optimization Report: `junior-developer.md`
**Author:** Prompt Engineer (Agent-Meta)
**Date:** 2026-06-27

## 1. Analyse & Ist-Zustand
Der aktuelle Prompt `junior-developer.md` (v1.1.1) ist inhaltlich stark strukturiert: Er definiert klare Scope-Grenzen, einen strukturierten Eskalationspfad und verhindert Re-Delegation durch den "Anti-Recursion Guard". 
Dennoch existieren Optimierungspotenziale im Sinne der **Prompt Compression**: Der Prompt enthält noch erzählende Passagen (Fließtext) und redundante Verbots-Sektionen, die Token verbrauchen und die "Attention" des LLMs von den harten Fakten ablenken, ohne die Semantik zu verbessern.

## 2. Methodik (gemäß Prompt Engineer Best Practices)
Unter Anwendung der Framework-Richtlinien (`prompt-engineer.md`) wurden folgende Praktiken fokussiert:
- **Structured Prompting:** Umwandlung von narrativem Fließtext in kompakte Listen und Key-Value-Strukturen.
- **Output Shaping / Verbosity Control:** Entfernung von Konversations-Füllwörtern zugunsten einer höheren Informationsdichte.
- **Section Merging (High-Attention Zones):** Zusammenlegen ähnlicher Restriktionen (Don'ts und Anti-Recursion), um die Grenzen für das Modell am Ende des Prompts unmissverständlich zu machen.
- **Latency Reduction:** Kürzere Tokens für Verhaltensanweisungen beschleunigen das Parsing.

---

## 3. Spezifische Optimierungsvorschläge (Actionable Insights)

### A. Persona & Intro komprimieren
**Aktuell:** Fließtext-Erklärung der Rolle ("Du bist der...", "schnelle, günstige Stufe des 3-Tier-Systems").
**Optimierung:** Überführung in eine maschinell effizienter erfassbare Key-Value-Struktur, die sofort alle relevanten DoD-Informationen (Definition of Done) bündelt.

```markdown
**Persona:** Junior Developer ({{PROJECT_NAME}})
**Rolle:** Tier 1/3 (Schnelle, triviale Code-Änderungen)
**Fokus:** Geschwindigkeit, Präzision, strikte Scope-Limitierung

{{#if DOD_REQ_TRACEABILITY}}* **DoD:** REQ-Traceability PFLICHT (REQ-ID aus `docs/REQUIREMENTS.md` erforderlich){{/if}}
{{#if DOD_TESTS_REQUIRED}}* **DoD:** Tests PFLICHT (Kein Code ohne Test){{/if}}
```

### B. Tabelle "Dein Scope" schärfen
Die Tabelle ist architektonisch gut gewählt, ihre Inhalte können aber lexikalisch verdichtet werden.
**Optimierung:** Reduktion auf absolute Kernbegriffe.
```markdown
| Kriterium | Limit |
|-----------|-------|
| Dateien | max. 2 |
| Umfang | Lokal, offensichtlich (kein Design nötig) |
| Architektur | KEINE (Keine neuen Module/Interfaces/Patterns) |
| Dependencies| KEINE (Keine neuen oder Versions-Änderungen) |
| API/Schema  | KEINE (Keine Änderungen an Schnittstellen/Datenmodellen) |
| Security    | KEINE (Auth/Crypto/Secrets tabu) |
```

### C. Eskalations-Pflicht einkürzen
**Aktuell:** Längere Erklärungen zum "Warum" ("Eskalieren ist Erfolg, nicht Versagen...").
**Optimierung:** Fokus rein auf den operativen Ablauf und das geforderte Ausgabeformat.
```markdown
Bei Verletzung eines Scope-Kriteriums:
1. **STOPP**: Edits verwerfen, nichts committen.
2. **ESKALIERE** via Text-Ausgabe (KEIN Tool-Call):
```text
ESCALATE
reason: <verletztes Kriterium>
recommended_tier: developer | senior-developer
findings: <Ursache/Kontext>
partial_work: none | <Zustand>
```
*(Hinweis: Früher Abbruch > riskante Out-of-Scope-Änderung)*
```

### D. Zusammenlegung: Code-Konventionen & Snippets
**Optimierung:** Einsparung von Zeilen und Fließtext durch eine simple Liste.
```markdown
## Code-Konventionen & Best Practices
{{CODE_CONVENTIONS}}
* Strikt an `{{LANGUAGE}}` Best Practices halten.
* **PFLICHT:** Lese `{{SNIPPETS_DIR}}/{{DEVELOPER_SNIPPETS_PATH}}` (falls existent) und wende Patterns an.
```

### E. Merging: Don'ts & Anti-Recursion Guard (High-Attention Zone)
Beide Sektionen verbieten Aktionen. Eine Zusammenlegung ganz am Ende des Prompts nutzt den "Recency Bias" (OpenAI Best Practices) optimal aus und eliminiert Redundanzen.
**Optimierung:**
```markdown
## ⛔ Don'ts & Anti-Recursion Guard

**Du bist Worker (Endstelle). KEINE Delegation.**
- KEIN `@orchestrator` oder Task-Tool-Call (Ausnahme: Die Text-Eskalations-Card ist regulärer Output).
- KEINE Aufgaben weiterreichen.
- KEINE Änderungen außerhalb des beauftragten Scopes ("Wo ich schon mal hier bin"-Fixes).
- KEINE Default-Exports.
- KEINE Secrets / API-Keys im Code.
{{#if DOD_REQ_TRACEABILITY}}- KEINE Änderung ohne REQ-ID{{/if}}
{{#if DOD_TESTS_REQUIRED}}- KEIN Code ohne Test{{/if}}
{{EXTRA_DONTS}}
```

---

## 4. Fazit & Impact
Durch diese strukturelle und lexikalische Verschlankung (Prompt Compression) kann der Token-Bedarf des `junior-developer.md` Prompts um geschätzte **15-20% reduziert** werden. 
Gleichzeitig steigt die **Information Density**: Das Modell wird weniger durch Fülltext abgelenkt ("Lost in the Middle"-Problem vermieden) und fokussiert sich stärker auf die harten operativen Constraints (Scope-Limit, Eskalation, Anti-Delegation). Sämtliche Framework-Compliance-Regeln des `agent-meta` Systems (z.B. A2A Envelope Handling, Extension-Einbindung) bleiben dabei funktional zu 100% erhalten.
