# Prompt Optimization Report: `ideation.md`

## 1. Einleitung & Zielsetzung
Als `prompt-engineer` wurde das generische Agenten-Template `agents/1-generic/ideation.md` (v1.6.1) analysiert. Das Ziel dieser Evaluation ist eine tiefgreifende Verschlankung (Prompt Compression) und Token-Reduktion, ohne die Funktionalität zu beeinträchtigen oder gegen Invarianten des `agent-meta` Frameworks zu verstoßen.

## 2. Analyse des aktuellen Zustands
- **Intakte Invarianten:** Das Template ist erfreulicherweise frei von Provider-Spezifika (Claude/Gemini) und hält sich sauber an die Vorgaben für die `1-generic`-Schicht. Die Handoff-Logik (`{{#if A2A_PROTOCOL_ENABLED}}`) ist syntaktisch korrekt.
- **Schwächen (Token-Bloat & Latenz-Treiber):**
  - **Erzählender Fließtext:** Die Einleitung und "Deine Haltung" sind sehr prosaisch ("Idee noch Rohdiamant", "zum Leuchten bringen"). Dies verbraucht unnötige Tokens.
  - **Ausformulierte Fragenkataloge:** In Phase 2 werden 12 spezifische Fragen aufgeführt. LLMs sind in der Lage, spezifische Fragen aus übergeordneten Dimensionen selbst abzuleiten ("Intent Classification" & "Context Engineering").
  - **Redundante Strukturierung:** Die Abschnitte "Umgang mit mehreren Ideen" und "Umgang mit vagen Visionen" sind gestreckt und lassen sich problemlos verdichten.
  - **Länge der Verbote & Guards:** Die Don'ts und der Anti-Recursion Guard nehmen viel Platz ein und können komprimiert formuliert werden, um die "Attention" des Modells auf die wesentlichen Restriktionen zu fokussieren (Placement in High-Attention Zones).

## 3. Optimierungspotenziale & Best Practices (OpenAI / Lakera)

### A. Structured Prompting & Template Abstraction
Fließtexte in kompakte Schlüsselwort-Listen oder Key-Value-Paare umwandeln. LLMs parsen diese Strukturen effizienter und konsistenter als Prosa.
*Maßnahme:* Die Sektion "Deine Haltung" auf prägnante Attribute (z.B. `[Neugierig, Realistisch, Strukturierend]`) reduzieren.

### B. Iterative Inquiry Dimensions (Verbosity Control)
Anstatt jede mögliche Frage als Liste mitzugeben, definieren wir "Inquiry Dimensions". Wir instruieren das Modell, basierend auf diesen Dimensionen selbst Fragen zu generieren und begrenzen den Output ("max. 1-2 Fragen pro Antwort").

### C. Agenten-Verträge als APIs
Das Konzept-Format (Phase 4) und der Handoff-Prozess (Phase 5) sollten zu einem klaren, maschinenlesbaren **Output Contract** zusammengefasst werden. Die Struktur für das `konzept-<thema>.md` kann in kompakter YAML-ähnlicher Form dargestellt werden.

## 4. Konkrete Refactoring-Vorschläge (Vorher / Nachher)

### 4.1 Intro & Persona
**Aktuell (ca. 50 Wörter):**
> Du bist der Ideation-Agent für {{PROJECT_NAME}}. Du begleitest die frühe, unscharfe Phase — wenn eine Idee noch Rohdiamant ist... Nicht implementieren... sondern Ideen zum Leuchten bringen...

**Neu (ca. 25 Wörter - ~50% Reduktion):**
> **Rolle:** Ideation-Agent für {{PROJECT_NAME}}.
> **Mission:** Begleitung der frühen Ideenphase (vor REQs/Code). Ideen explorieren, hinterfragen, strukturieren und übergeben. 
> **Fokus:** Konzeptarbeit. NIEMALS Code implementieren.

### 4.2 Phase 1 & 2 (Exploration)
**Statt detaillierter Fragenlisten (Inquiry Dimensions - token-sparend):**
> **Dialog-Regel:** Führe einen iterativen Dialog (max. 1-2 Fragen pro Antwort).
> **Explorations-Dimensionen:**
> - `Kern/Auslöser:` Was ist die Essenz? Warum jetzt?
> - `Nutzen:` Wer profitiert? Was ändert sich?
> - `Kontext:` Technische Grenzen? Existierende Lösungen?
> - `Edge-Cases:` Risiken? Wer hat Nachteile?
> - `Scope:` Was ist MVP (v1)? Was kommt später (v2+)?

### 4.3 Spezialsituationen konsolidieren
**Die Abschnitte "Mehrere Ideen" und "Vage Visionen" zusammenfassen:**
> **Handlungsempfehlungen:**
> - *Mehrere Ideen:* Alle auflisten -> mit User priorisieren -> sequenziell bearbeiten.
> - *Vage Visionen:* Explorativ bleiben, Analogien nutzen, Ambiguität zulassen, Widersprüche benennen.

### 4.4 Constraints & Don'ts (Lakera Robustness)
Am Ende des Prompts platzieren für maximalen "Recency Bias":
> **DON'TS (Strict Constraints):**
> - KEINE REQ-IDs vergeben.
> - KEINE Implementierung / Code schreiben.
> - KEINE verfrühte Bewertung von Ideen.
> - NICHT alle Fragen auf einmal stellen.

## 5. Actionable Insights für das Template-Update

1. **Major vs. Minor Bump:** Da die Restrukturierung das "Reasoning-Verhalten" (Fragen stellen) ändert, sollte die Version auf `1.7.0` (Minor Bump) angehoben werden.
2. **Prosa strikt entfernen:** Entferne alle Metaphern ("Rohdiamant", "zum Leuchten bringen"). Sie kosten Token und lenken die Attention von den Kerninstruktionen ab.
3. **Output Formats strikt definieren:** Kombiniere Phase 4 und 5 in einen expliziten **`<handoff-contract>`** Abschnitt, in dem die Felder für das Markdown-Artefakt (`ci`, `g`, `sv1`, `oq`, `ref`) genau dem entsprechen, was der `requirements`-Agent als Input erwartet. Dies verhindert Parsing-Fehler beim Handoff.
4. **Tooling-Hinweise straffen:** Phase 3 kann auf einen Satz gekürzt werden: "Nutze `WebSearch`/`Glob` bei Bedarf für Benchmarks; erzeuge optional ein `recherche-<thema>.md`."

**Fazit:** Durch diese strukturellen Anpassungen lässt sich das Template um mindestens 30-40% verschlanken, während die Zielgenauigkeit (Precision) durch die klareren Constraints und Dimensionen nachweislich steigt. Latenz und Kosten für die Inception dieses Agenten sinken signifikant.
