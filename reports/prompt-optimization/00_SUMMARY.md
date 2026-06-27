# Abschlussbericht & Architektur-Empfehlungen: Context Engineering 2026

Dieser detaillierte Bericht fasst die systemweite Evaluierung aller 55 generischen Agenten des `agent-meta` Frameworks zusammen. Er formuliert **übergreifende, strategische Empfehlungen** für den anstehenden Umbau des Repositories. Die Evaluierung wurde durch den `prompt-engineer` Subagenten durchgeführt, mit striktem Fokus auf Verschlankung, Token-Effizienz (Latenz- und Kostenreduktion) und Framework-Compliance.

Alle 55 detaillierten Berichte mit den spezifisch optimierten Entwürfen liegen im Ordner: `reports/prompt-optimization/`

---

## 🔬 1. State of the Art: Context Engineering (Research 2026)

Aktuelle Internet-Recherchen zu Best Practices in der Entwicklung von Multi-Agenten-Systemen (Stand Mitte 2026) zeigen einen klaren Paradigmenwechsel auf, der die Richtung für `agent-meta` vorgibt:

1. **Vom Prompting zum Context Engineering:** Die Disziplin hat sich von "cleveren Text-Hacks" hin zu einem rigorosen Management des "Context-RAMs" entwickelt. Die wichtigste Metrik ist die Informationsdichte. Jedes redundante Wort erhöht die Latenz (Time-to-First-Token) und das Risiko von Halluzinationen. "Deletion-based Compaction" (das gezielte Löschen von Füllwörtern) ist heute Standard.
2. **Struktur über Prosa:** Moderne Frontier-Modelle (Claude 3.5+, GPT-4o+, Gemini 1.5+) reagieren wesentlich präziser auf maschinenlesbare Strukturen. XML-Tags zur Sektionierung und TypeScript-Interfaces zur Datendefinition schlagen klassische Markdown-Header deutlich.
3. **TOON (Tabular Object-Oriented Notation):** Ein neuer Standard, der JSON für große Input-Datenmengen ersetzt. TOON verhält sich wie eine Mischung aus YAML (Einrückung) und CSV (Tabellenstruktur) und spart bis zu 60% der Struktur-Tokens. JSON bleibt der Standard für *Outputs*, da es maschinell nahtlos verarbeitet werden kann. TOON wird genutzt, um das Modell mit riesigen Kontexten kostengünstig zu "füttern".

---

## 📊 2. Zentrale Befunde aus der Analyse der 55 Agenten

Die Analyse der 55 Agenten in `agent-meta/agents/1-generic` hat konsistente Anti-Patterns aufgedeckt, die den aktuellen 2026-Standards widersprechen:

### A. JSON Mock-Data Bloat
* **Befund:** Fast alle Agenten (insb. `api-specialist`, `code-reviewer`, `se-architect`) nutzen massive, vollständig ausformulierte JSON-Beispiele (teils 50-90 Zeilen), um A2A-Handoff-Payloads zu definieren.
* **Risiko:** Hoher Token-Verbrauch. Noch kritischer: LLMs neigen dazu, sich an den Mock-Daten (z.B. dem oft genutzten "Heating Controller" Beispiel) festzubeißen und diese in echte Outputs zu halluzinieren.
* **Lösung:** Umstellung auf **kompakte TypeScript-Interfaces**.
  * *Vorher:* `{"status": "success", "data": {"user_id": 123, "name": "Test"}}` (Viel Rauschen durch Klammern/Quotes).
  * *Nachher:* `interface Response { status: 'success'|'error'; data: UserData; }`

### B. "Erzählender Fließtext" & Narrative Workflows
* **Befund:** Arbeitsabläufe, Rollenbeschreibungen und Verhaltensregeln werden als narrative Absätze formuliert (z.B. "Du bist ein erfahrener Experte, der Code prüft. Wenn du einen Fehler findest, dann...").
* **Risiko:** Geringe Informationsdichte. Das LLM muss "zwischen den Zeilen" lesen.
* **Lösung:** Konsequente Nutzung von **Structured Prompting** und **Chain-of-Symbol**.
  * *Vorher:* "Lies zuerst die Datei. Danach prüfst du sie auf Fehler. Am Ende schreibst du einen Report."
  * *Nachher:* `Workflow: [Read File] -> [Audit Rules] -> [Generate Report]`

### C. Schwache Strukturierung (Markdown vs. XML)
* **Befund:** `agent-meta` trennt Sektionen aktuell fast ausschließlich durch Markdown-Header (`#`, `##`).
* **Risiko:** In massiven Kontexten verschwimmen Markdown-Texte und Markdown-Header stark. Es gibt keine klare, syntaktische Schließung einer Sektion.
* **Lösung:** Einführung des branchenüblichen **6-Block-Templates mit XML-Tags**. Prompts werden in harte, maschinenlesbare Blöcke gefasst: `<persona>`, `<workflow>`, `<context>`, `<output_contract>`, `<constraints>`.

### D. Redundanz & "Lost in the Middle"
* **Befund:** Verbotene Aktionen (Constraints) sind über den gesamten Prompt verstreut (unter "Arbeitsablauf", "Warnung", "Anti-Recursion Guard").
* **Risiko:** Das LLM "vergisst" Anweisungen aus der Mitte des Prompts ("Lost in the Middle"-Phänomen).
* **Lösung:** Alle strikten Restriktionen in einem verdichteten `<constraints>` Block bündeln und **zwingend an das Ende des Prompts** stellen. Dies maximiert den *Recency Bias* (das Modell fokussiert sich auf die zuletzt gelesenen Tokens).

### E. Framework-Verletzungen im `1-generic` Layer
* **Befund:** Einige generische Agenten enthielten anbieterspezifische Pfade (z.B. `.claude/rules/` im `developer`) oder Tool-Commands (z.B. `bun test` im `release`).
* **Lösung:** Diese wurden in den Reports durch universelle Placeholder (z.B. `{{TEST_COMMAND}}`, `{{RULES_PATH}}`) ersetzt, um die zwingende provider-agnostische Architektur des Frameworks zu wahren.

---

## 🚀 3. Übergreifende Empfehlungen & Architektur-Umbau

Basierend auf den Befunden und dem 2026-Stand der Technik empfehle ich dringend einen strukturellen Umbau des `agent-meta` Repositories in drei Phasen:

### Phase 1: Die "Structure & Contract" Migration (Sofort-Maßnahme)
Wir schreiben die Templates nicht nur um, wir verändern ihr Paradigma: Prompts sind keine Texte mehr, sondern **API-Verträge**.

1. **XML-Standardisierung:** Ersetze die obersten Markdown-Strukturen durch harte XML-Tags.
   * Jeder Agent muss zwingend mit `<persona>` beginnen.
   * Jeder Agent muss zwingend mit `<constraints>` und `<output_contract>` enden.
   * *Warum?* Starke Abgrenzung für das Attention-Netzwerk des LLMs.
2. **TypeScript-Interfaces für Handoffs:** Alle A2A-Payloads (`payload.t`) und JSON-Schemas werden von JSON auf kompakte TypeScript-Interfaces umgeschrieben.

### Phase 2: Die "Compaction" (Token-Diät)
1. **Fließtext-Löschung:** Rigorose Entfernung von "Erklärbär"-Texten. Die LLMs wissen, was "Big O Notation" (siehe `performance-optimizer`) oder "Top-Down Integration" (siehe `se-test-engineer`) ist. Wir geben nur noch Heuristiken und Befehle vor, keine Definitionen.
2. **Tabellen-Kompression:** Breite Markdown-Tabellen (wie sie oft für den Anti-Recursion-Guard genutzt wurden) werden in dichte, einzeilige Listen überführt. Tabellen verbrauchen durch Padding und Pipes (`|`) unzählige sinnlose Tokens.

### Phase 3: Framework-Anpassungen (Mittelfristig)
1. **Prüfung von TOON:** Für Agenten, die große Mengen an Log-Daten oder Code-Strukturen als reinen Input verarbeiten (z.B. `log-analyzer`, `explorer`), sollte `sync.py` oder ein Tooling-Wrapper evaluiert werden, der Input-Daten on-the-fly in das **TOON-Format** konvertiert. Dies kann die Betriebskosten drastisch senken.
2. **Output Shaping:** Explizite Anweisungen im `<output_contract>`, dass das Modell sich extrem kurz fassen soll ("Keine Einleitung, kein Fazit, nur das reine JSON.").
3. **Zentralisierung von A2A-Rules:** Die immer gleichen Anti-Recursion-Guards blähen 55 Prompts auf. Wir sollten prüfen, ob `sync.py` diese Regeln dynamisch als Include-Block (`{{ANTI_RECURSION_GUARD}}`) anhängen kann, statt sie 55x hart in den Prompts zu pflegen.

---

## 🛠️ Nächste konkrete Schritte für das Team

1. **Sichten der Reports:** Wirf einen Blick in `reports/prompt-optimization/` (z.B. `orchestrator.md_report.md` oder `developer.md_report.md`), um die konkreten Vorher/Nachher-Entwürfe zu sehen.
2. **Proof of Concept (PoC):** Übertrage die vorgeschlagenen XML- und TypeScript-Strukturen testweise auf **3 Kernagenten** (z.B. `orchestrator`, `developer`, `code-reviewer`).
3. **Build & Test:** Führe einen `sync.py` Lauf durch. Teste die Agenten in einem Dummy-Projekt auf Latenz (TTFT) und Regeltreue (Handoffs).
4. **Rollout:** Bei Erfolg: Automatisierte oder manuelle Übernahme der Optimierungen auf alle restlichen 52 Agenten basierend auf den von mir erstellten Drafts.
