# Prompt-Optimization Report: `_wf-feedback.md`

## 1. Aktueller Status (Current State)
Die Datei `_wf-feedback.md` dient im `agent-meta` Framework als nachladbares "Lazy-Load Knowledge File". Sie hat derzeit einen Umfang von 10 Zeilen (310 Bytes) und beinhaltet narrativen Text sowie einen Markdown-Code-Block.

```markdown
# Workflow K: Feedback an agent-meta

```
1. meta-feedback → Feedback aufbereiten + als GitHub Issue formulieren
2. meta-feedback → Issue erstellen (nach Nutzer-Bestätigung)
```

Am Session-Ende aktiv fragen:
> "Gab es etwas, das im agent-meta-Framework fehlt, unklar war oder verbessert werden könnte?"
```

## 2. Evaluation & Findings
Auch wenn die Datei bereits sehr kurz ist, lässt sie sich nach den Prinzipien des **Context Engineering** und der **Prompt Compression** (aus `prompt-engineer.md`) noch effizienter gestalten.
Besondere Analyse-Punkte:

1. **Strukturelles Overhead (Code-Block):** Der Einsatz des dreifachen Backticks (` ``` `) suggeriert Code, fügt dem LLM-Verständnis hier aber keinen Mehrwert hinzu und verbraucht unnötige Tokens ("Formatting-Overhead").
2. **Redundanz in A2A-Handoffs:** Der Akteur `meta-feedback` wird für beide Einzelschritte explizit wiederholt.
3. **Fließtext-Instruktionen:** Die Anweisung `"Am Session-Ende aktiv fragen:"` ist erzählend. Kompakte Schlüsselbegriffe (z. B. `Trigger:`) werden von LLMs schneller erfasst.
4. **Bezeichner:** Der Titel `"Workflow K"` ist vermutlich ein Überbleibsel (Legacy) und verbraucht Tokens, ohne semantischen Nutzen zu liefern, da die Zuordnung über den Dateinamen (`_wf-feedback.md`) geschieht.
5. **Output Shaping & Verbosity:** Die vom LLM erwartete Frage an den User ist recht ausformuliert. LLMs interpolieren Intent sehr gut, daher reicht ein semantischer Kern aus.

## 3. Actionable Insights (Verschlankung)

* **Listen-Optimierung & Chain-of-Symbol:** Nutze kompakte Aufzählungen oder Symbole (z.B. `->`), um den Workflow als Prozesskette zu definieren, ohne den Agenten-Namen zu wiederholen.
* **Event-Driven Formatting:** Deklariere Auslöser explizit als `[Trigger]`. Das erzeugt High-Attention-Zonen im Context Window.
* **Reduktion der Phrase:** Der Vorschlagstext für den User kann verdichtet werden.

## 4. Spezifische Optimierungsvorschläge (Refactorings)

### Variante A: Strukturierte Kompression (Empfohlen)
Eine saubere, minimal strukturierte Version, die den Vertrag (Handoff) und den Trigger deutlich isoliert.

```markdown
# WF: agent-meta Feedback

**Akteur:** `meta-feedback`
1. Issue draften (Feedback aufbereiten)
2. Issue erstellen (Nur nach User-Bestätigung!)

**Trigger @ Session-End:**
> "Gibt es Feedback oder Verbesserungswünsche zum agent-meta Framework?"
```

### Variante B: Maximal komprimiert (Context Window Optimizer)
Diese Variante nutzt Chain-of-Symbol und verdichtet alles auf zwei Zeilen für minimale Latenz (Generation Speed).

```markdown
# WF: agent-meta Feedback
- **Task:** `meta-feedback` -> Issue draften -> User-Approve -> Issue erstellen
- **Trigger @ Session-End:** Frage User nach "Feedback/Verbesserungswünschen zu agent-meta?"
```

## 5. Fazit
Durch die Entfernung der Markdown-Code-Blöcke, das "Flattening" der Delegation (`meta-feedback`) und die Nutzung kompakter Trigger-Keywords ("Trigger @ Session-End") lässt sich die Datei um ca. 25-35 % an Token-Volumen reduzieren. Gleichzeitig bleibt die funktionale Integrität (Handoff an `meta-feedback` und Pflicht zur User-Bestätigung) uneingeschränkt erhalten. Dies verbessert die LLM-Parsing-Geschwindigkeit und minimiert den Token-Footprint bei jedem Lazy-Load.
