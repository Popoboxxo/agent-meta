# Prompt Optimization Report: `_wf-issue.md`

## 1. Ausgangsanalyse (Current State)
Das Template `_wf-issue.md` definiert den "Workflow L: GitHub Issue bearbeiten" als kompakte Liste. 

**Stärken:**
- Es nutzt bereits **Strukturiertes Prompting** (nummerierte Liste).
- Es setzt konsequent auf **Chain-of-Symbol (CoS)** (Verwendung von `→` statt langer Instruktionen, was den "Reasoning-Buffer" schont).
- Der Token-Fußabdruck ist mit 17 Zeilen und ~687 Bytes bereits sehr gering.

**Schwächen & Optimierungspotenzial:**
- **Markdown Code-Blöcke (```)**: Das Einwickeln der Liste in Code-Tags kostet unnötige Tokens. Ein LLM kann eine reine Markdown-Liste genauso gut parsen.
- **Redundante Delegationsschritte**: Die Schritte 0 und 1 werden beide vom `git`-Agenten ausgeführt. In einem Multi-Agenten-Setup (wie im `agent-meta` Framework) suggeriert dies zwei separate Task-Zuweisungen. Sie sollten atomar zusammengefasst werden.
- **Füllwörter (Verbosity)**: Phrasen wie "Reproduzierenden Test schreiben", "falls nötig" oder "zuordnen oder neu vergeben" verschwenden Tokenkapazität. Ein KI-Agent versteht Abkürzungen wie `(opt)` oder `Test (Red Phase)` perfekt.
- **Bedingte Logik (Flow Control)**: Der Text unter der Liste ("Bug → Schritt 3 zuerst. Feature → wie Workflow A...") ist ein stilistischer Bruch und zwingt das Modell, nachträglich die Liste neu zu bewerten. Dies kann effizienter gelöst werden.

## 2. Optimierungsmaßnahmen (Verschlankung)

Gemäß den Vorgaben für **Context Engineering 2026** und **Prompt Compression**:

1. **Entfernung syntaktischen Overheads**: Löschen der ``` Code-Tags.
2. **Task-Konsolidierung**: Zusammenlegen der Schritte 0 und 1 (beide `git`), um Handoff-Overhead zu reduzieren.
3. **Output Shaping & Relevance Filtering**:
   - `gh issue list / gh issue view <id>` → `gh issue view <id>` (ist präziser, List ist impliziert, falls ID unbekannt).
   - `(fix/<issue> oder feat/<issue>)` → `Branch-Guard (fix/feat)`.
   - `zuordnen oder neu vergeben` → `REQ-ID`.
   - `falls nötig` → `(opt)`.
4. **Inline-Steuerung**: Die Unterscheidung zwischen Bug und Feature wird teilweise direkt als Tag (`[nur Bug]`) in den Workflow integriert, um die lineare Abarbeitung zu stärken.

## 3. Vorschlag für das optimierte Template

```markdown
# Workflow L: GitHub Issue bearbeiten

1. git          → gh issue view <id> & Branch-Guard (fix/feat)
2. requirements → REQ-ID vergeben/zuordnen
3. tester       → Test (Red Phase) [nur Bug]
4. developer    → Fix/Feature implementieren
5. tester       → Tests ausführen & Regression
6. validator    → DoD-Check
7. documenter   → Doku-Update (opt)
8. git          → Commit, Push, gh issue close <id> --comment "Fixed in <commit>"

> **Note:** Feature → Ablauf wie Workflow A (Start ist das Issue).
```

## 4. Evaluierung der Framework-Regeln (agent-meta)
- **1-generic Konformität:** Der Workflow bleibt absolut provider-agnostisch (keine Erwähnung von Claude, Gemini, etc.).
- **Anti-Re-Delegation & Handoffs:** Durch die straffere Aufteilung und Reduktion der Schritte sinkt das Risiko von Endlosschleifen und unnötiger `delegation_depth`.
- **Token Impact:** Die Textgröße wurde weiter reduziert, Füllwörter wurden durch kompakte Instruktionen ersetzt, was die Verarbeitungs-Latenz (Latency Reduction) marginal, aber systematisch verbessert.
