# Evaluation & Streamlining Report: `feedback.md`

**Datum:** 2026-06-27
**Agent:** prompt-engineer (Template Evaluation)
**Target File:** `/home/dduchrow/Repos/agent-meta/agents/1-generic/feedback.md`

## 1. Management Summary
Der `feedback.md`-Agentenprompt wurde einer tiefgehenden Analyse basierend auf den `agent-meta` Prompt-Engineering Best Practices (insb. *Structured Prompting* und *Relevance Filtering*) unterzogen. 
Der aktuelle Prompt ist mit **217 Zeilen** extrem lang und enthält redundante Strukturen. Durch die Eliminierung von Doppelungen, die Konsolidierung von Tabellen und den Ersatz stark ausformulierter Markdown-Templates durch kompakte Vorgaben, lässt sich der Prompt um **ca. 50-60% komprimieren**. Dies führt zu signifikant reduzierten Token-Kosten, niedrigerer Latenz und einem geschärften Fokus (Attention) des LLMs, ohne dass die Ausgabequalität leidet.

## 2. Ist-Zustand & Identifizierte Schwachstellen

- **Redundante Klassifizierung:** Die Sektionen *Entscheidungsbaum* und *Typ-Matrix* stellen inhaltlich dasselbe dar (Trigger-Bedingung vs. Typ-Name). Das LLM muss zwei Strukturen evaluieren, um eine Entscheidung zu treffen.
- **Extrem verbose Body-Templates (Token-Fresser):** Die Sektion *Body-Templates nach Typ* nimmt mit über 80 Zeilen fast 40% des gesamten Prompts ein. LLMs besitzen ein starkes "Prior Knowledge" für gängige GitHub Issue-Formate. Die explizite Angabe kompletter Markdown-Gerüste mit erklärenden Platzhaltern (z.B. `[Brief summary of the problem]`) ist für moderne Modelle unnötig detailliert.
- **Streuung von Constraints:** Anweisungen zur Erstellung (Bash-Snippet), "Qualitätskriterien" und "Don'ts" sind in drei separate Blöcke aufgeteilt, die sich inhaltlich wiederholen (z.B. die mehrfache Erwähnung "Keine mehreren Probleme in ein Issue" vs. "Atomar").
- **Doppelte Meta-Abgrenzung:** Die Unterscheidung zwischen `feedback` und `meta-feedback` wird im Intro erklärt, erhält eine eigene Tabelle ("Abgrenzung") und taucht in den Don'ts nochmal auf.

## 3. Konkrete Optimierungsvorschläge (Actionable Insights)

### Proposal 1: Konsolidierung der Issue-Typen (Structured Prompting)
**Methode:** Zusammenführung von Entscheidungsbaum, Typ-Matrix und den 80 Zeilen Body-Templates in eine einzige, dichte Markdown-Tabelle. Wir nutzen das semantische Verständnis des Modells, indem wir nur noch die erwarteten *Headings* vorgeben.

**Neuer Entwurf:**
```markdown
## Issue-Typen & Formatierung (Structured Prompting)

Wähle den passenden Typ und strukturiere den Issue-Body (`--body`) mit den genannten Markdown-Headings:

| Typ | Wann nutzen? (Trigger) | Titel-Präfix | Label | Erforderliche Body-Sections (Markdown) |
|---|---|---|---|---|
| `bug` | Reproduzierbares Fehlverhalten | `fix:` | `bug` | Description, Steps to Reproduce, Expected vs. Actual, Environment |
| `feat` | Neue Fähigkeit / Feature | `feat:` | `enhancement` | Problem/Motivation, Proposed Solution, Alternatives |
| `improvement`| Bestehendes verbessern | `improvement:`| `improvement` | Current Behavior, Improvement Proposal, Expected Benefit |
| `docs` | Doku-Lücke oder veraltet | `docs:` | `documentation` | Affected Document, Missing/Outdated Info, Expected Content |
| `security` | Sicherheitsrelevantes | `security:` | `security` | Description, Impact, Reproducible?, Recommended Action |
| `question` | Klärungsbedarf | `question:` | `question` | Question, Context, Affected Area |
```

### Proposal 2: Straffung der Constraints & Workflow-Regeln (Relevance Filtering)
**Methode:** Führe "Qualitätskriterien", "Don'ts", die Info zum `gh` CLI Workflow und die Meta-Abgrenzung in einer einzigen, klaren und handlungsorientierten Sektion zusammen. 

**Neuer Entwurf:**
```markdown
## Workflow & Constraints

- **Scope:** Ausschließlich Feedback für `{{PROJECT_NAME}}`. Feedback zum Framework selbst strikt ablehnen (verweise auf den `meta-feedback` Agenten). Du bist die Standardinstanz für Issues (kein Umweg über den `git` Agenten).
- **Atomarität:** Genau 1 Issue = 1 Problem/Idee. Niemals Sammel-Issues erstellen.
- **Titel:** Präzise, handlungsfähig und zwingend mit dem Typ-Präfix starten (z.B. `fix: Crash on startup`).
- **CLI-Ausführung:** 
  1. Repo ermitteln: `gh repo view --json nameWithOwner -q .nameWithOwner`
  2. Issue anlegen: `gh issue create --title "..." --label "..." --body "..."`
- **Kein Bestätigungs-Loop:** Das Issue sofort und ohne Rückfrage erstellen. Die finale Kontrolle/Bestätigung liegt beim orchestrierenden Aufrufer.
```

### Proposal 3: Sprache & Meta-Regeln (High-Attention Zone)
**Methode:** Positioniere die strikten Constraints (Output Shaping) am Ende des Prompts.
Behalte die `Anti-Recursion Guard` unverändert bei, da sie Framework-Standard ist. Die Sprachregeln können als kompakter 3-Zeiler darunter platziert werden.

## 4. Fazit & Nächster Schritt
Die konsequente Umsetzung dieser Vorschläge transformiert den Prompt von einer narrativen Dokumentation in eine **maschinenoptimierte Instruktionsmatrix (Context Engineering)**.
- **Tokens gespart:** > 50%
- **Action:** Der aktuelle Inhalt von `feedback.md` zwischen dem Intro und der Anti-Recursion Guard kann gefahrlos durch die in Proposal 1 & 2 genannten konsolidierten Blöcke ersetzt werden.
