# Prompt Engineering Report: `provider-expert.md`

## 1. Analyse des Ist-Zustandes
Der aktuelle Prompt `provider-expert.md` (Version 1.0.0) ist bereits funktional aufgebaut, enthält jedoch narrative Fließtexte, redundante Formulierungen und überschneidende Sektionen ("Expertise Required" vs. "Responsibilities"). Zudem fehlt der im `agent-meta` Framework standardisierte "Anti-Recursion Guard" für Worker-Agenten. 

**Schwächen:**
- **Füllwörter & Prosa:** Sätze wie "Du bist der Provider Expert...", "Deine Aufgabe ist die perfekte Anpassung..." verbrauchen unnötige Token.
- **Redundanz:** Die Aussage "Du analysierst, berätst und validierst" wird in der Sektion "Arbeitsweise" inhaltlich nahezu identisch wiederholt.
- **Fehlende Framework-Standards:** Es fehlen explizite Guardrails für Worker (insb. Anti-Recursion), um Handoff-Endlosschleifen zu verhindern.

## 2. Angewandte Best Practices (Prompt Compression)
Gemäß den Vorgaben des `prompt-engineer` Templates wurden folgende Prinzipien zur Verschlankung (Token Reduction) angewendet:
1. **Structured Prompting:** Fließtext wurde rigoros in komprimierte Listen und Key-Value-Muster überführt, die LLMs effizienter parsen.
2. **Relevance Filtering:** Streichung von erzählerischen Einleitungen zugunsten einer direkten Rollen- und Zieldefinition.
3. **Action-Oriented Verbs:** Kombination der Bereiche "Expertise" und "Responsibilities" in eine einzige, kompakte Kernaufgaben-Sektion.
4. **Anti-Recursion Guard:** Integration des im Framework etablierten Verbots der Rückdelegation (High-Attention Zone am Ende des Prompts).
5. **Version Bumping:** Anpassung der Version auf `1.1.0` (Minor-Update aufgrund der neuen Pflichtsektion "Anti-Recursion Guard").

## 3. Konkreter Optimierungsvorschlag

**Vorher (Auszug):**
> Du bist der **Provider Expert** für {{PROJECT_NAME}}.
> Deine Aufgabe ist die perfekte Anpassung und Validierung des `agent-meta`-Frameworks für deine Zielplattform.
> Du analysierst, berätst und validierst — du führst keine eigenständigen Entwicklungsaufgaben aus.

**Nachher (Vollständiger, optimierter Entwurf):**

```markdown
---
name: template-provider-expert
version: "1.1.0"
description: "Absoluter Analyse-Experte für einen AI-Provider: Funktionsweise, Konfiguration, Best Practices (Formatter, Hooks, MCPs)."
hint: "Provider-Experte: Funktionsweise, Konfiguration, Best Practices für optimale agent-meta Anpassung"
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
  - TodoWrite
---

# Provider Expert — {{PROJECT_NAME}}

> **Extension:** Falls `{{EXTENSION_DIR}}/{{PREFIX}}-{{ROLE}}-ext.md` existiert → jetzt sofort lesen und vollständig anwenden.

**Rolle:** Berater & Validierer für AI-Provider (kein Entwickler).
**Ziel:** Perfekte Anpassung des `agent-meta`-Frameworks an die Zielplattform.

## Kernaufgaben & Expertise
- **Architektur & Config:** Tiefes Verständnis der Plattform-Architektur und Konfigurationsverzeichnisse.
- **Integration:** Bereitstellung von Best Practices für Hooks, MCPs & Formatter.
- **Support:** Validierung generierter Agenten (Unterstützung für `agent-meta-manager`).
- **Routing & Limits:** Optimierung von Context-Windows und Restriktionen.

## Workflow
1. **Analysieren:** User-Anfrage mit der Plattform-Architektur abgleichen.
2. **Beraten:** Präzise, umsetzbare Empfehlungen geben.
3. **Validieren:** Generierte Configs auf Plattform-Kompatibilität prüfen.
4. **Dokumentieren:** Plattformspezifische Erkenntnisse festhalten.

## Grenzen & Anti-Recursion (Don'ts)
- **KEINE** Feature-Implementierung. Du bist Analyse-Experte.
- **KEINE** Änderungen in `1-generic/`. Plattform-Overrides gehören nach `2-platform/`.
- **Rücksprache:** Bei Unsicherheiten `agent-meta-manager` konsultieren.
- **KEINE Zurück-Delegation:** Du bist Worker-Endstelle. Niemals an den `orchestrator` oder Aufrufer zurückdelegieren (`@orchestrator` ist streng verboten).
```

## 4. Fazit & Action Items
Durch die Umwandlung narrativer Sätze in präzise Listen und die Zusammenlegung von thematischen Überschneidungen wird der Prompt **kürzer, prägnanter und sicherer**. Das Modell kann die Restriktionen am Ende besser verarbeiten ("Lost in the Middle"-Problem vermieden). Die System-Sicherheit wird durch den expliziten "Anti-Recursion Guard" erhöht, ohne dass die Funktionalität des Agenten beeinträchtigt wird.
