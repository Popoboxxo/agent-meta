# Evaluierungsbericht: `agent-meta-manager` Prompt-Optimierung

## 1. Executive Summary
Basierend auf den Best Practices des `prompt-engineer` (OpenAI & Lakera, Context Engineering 2026) wurde der Agent `agent-meta-manager` evaluiert. Ziel ist eine signifikante Verschlankung (Token-Reduktion) und Latenz-Optimierung durch Structured Prompting, Entfernen von Redundanzen und Konsolidierung von Verhaltensregeln, ohne die strikten Framework-Regeln (Advisory Mode, Anti-Recursion) zu verletzen.

## 2. Ist-Zustand (Current State)
- **Datei**: `agents/1-generic/agent-meta-manager.md`
- **Umfang**: 290 Zeilen, ca. 10.6 KB
- **Diagnose**: Der Prompt ist stark erzählend (Fließtext) und wiederholt wichtige Konzepte an mehreren Stellen (z. B. Advisory Mode in Abschnitt 0 und Don'ts in Abschnitt 10). Code-Beispiele und CLI-Kommandos sind über viele Sektionen verstreut.

## 3. Findings & Schwachstellen
1. **Redundante Sicherheitsregeln**: Die "Bestätigungspflicht" (Abschnitt 0) und die "Don'ts" (Abschnitt 10) überschneiden sich stark. Das führt zu Recency Bias Problemen und verschwendet Token.
2. **Ausufernde Erklärungen**: Abschnitt 1a (Update vs. Upgrade) verwendet viel Fließtext, um eine einfache If-Then-Logik zu erklären. 
3. **Verteilte CLI-Befehle**: Befehle zum Status (1), Upgrade (2), Update (3), Commands (6), Skills (7) und Consistency-Check (8) sind über den gesamten Prompt verteilt, was das "Parsing" für das LLM erschwert.
4. **Gesprächige Beispiele**: Die "Tradeoffs erklären"-Beispiele in Abschnitt 0 sind zu lang und können abstrahiert werden.
5. **Boilerplate-Text**: Beschreibungen wie in Abschnitt 11 (SE Kaskade) sind unnötig ausschweifend für eine einfache Konfigurationsanweisung.

## 4. Konkrete Optimierungsvorschläge (Actionable Insights)

### Vorschlag 1: "Constraints & Don'ts" konsolidieren (Principle of Least Privilege)
Führe Abschnitt 0 und 10 in einer einzigen, extrem prägnanten "Hard Constraints"-Sektion am Ende des Prompts (High-Attention Zone) zusammen.
**Vorher:** Viel Fließtext, zwei getrennte Listen.
**Nachher (Konzept):**
```markdown
## STRICT CONSTRAINTS (Advisory Mode)
1. **Zustimmungspflicht:** NIEMALS Dateien löschen, Model-Tier ändern, Rollen/Presets anpassen, `sync.py` ausführen oder Major-Upgrades durchführen ohne explizite User-Bestätigung.
2. **Tradeoffs:** Bei Konfigurationsänderungen immer Vor-/Nachteile (z.B. Kosten vs. Qualität) benennen.
3. **Dry-Run:** Zeige bei Änderungen erst einen kompakten Plan (Was ändert sich?).
4. **Code-Boundaries:** Keine manuellen Edits in `.claude/agents/` oder in managed blocks.
```

### Vorschlag 2: Logik in Tabellen/Mapping komprimieren (Structured Prompting)
Abschnitt 1a, 2 und 3 behandeln Versionierung und Updates. Diese sollten in eine kompakte Entscheidungsmatrix (Decision Table) überführt werden, um "Reasoning Effort" zu minimieren.
**Nachher (Konzept):**
```markdown
## Update vs. Upgrade
| User Intent | Aktion | Kommando / Workflow | Commit-Message |
|-------------|--------|---------------------|----------------|
| Nur generieren | Update | `sync.py --config ...` | `chore: regenerate agents` |
| Neue Version | Upgrade | `git checkout v<Tag>` → `sync.py` | `chore: upgrade agent-meta to v<X.Y.Z>` |
*Sonderfall:* Wenn aktuelles Tag == remote Tag → Update durchführen, NIE Upgrade.
```

### Vorschlag 3: Command Cheat-Sheet bündeln (Relevance Filtering)
Fasse die verstreuten Sektionen (6, 7, 8) in einem kompakten Code-Block zusammen. LLMs parsen dichte Code-Blöcke effizienter als mehrfach unterbrochene Absätze.
**Nachher (Konzept):**
```markdown
## Command Reference
- **Status:** `cat .agent-meta/VERSION`, `git submodule status .agent-meta`
- **Extensions:** `sync.py ... --create-rule <name>`, `--create-ext <rolle>`, `--create-command <name>`
- **Skills (Ref: _wf-skill-lifecycle.md):** `sync.py ... --add-skill <url> --skill-name <n> ...`
- **Consistency-Check:** `.agent-meta/scripts/consistency-check.py [--changed | --file <pfad>]`
```

### Vorschlag 4: Routing kompakt darstellen (Intent Classification)
Sektionen 4, 5 und Teile von 6 können auf eine einfache Routing-Liste reduziert werden:
- Feature für alle Projekte? → `meta-feedback` (Label: new-agent)
- Feature für eine Plattform? → `meta-feedback` (Label: new-platform-agent)
- Projektweites Wissen? → `--create-rule`
- Agenten-spezifisches Wissen? → `--create-ext <rolle>`
- Kurzer Hauptchat-Workflow? → `--create-command <name>`
- Komplett anderer Workflow? → Override in `{{EXTENSION_DIR}}/<rolle>.md`

## 5. Erwartetes Ergebnis
Durch diese Strukturierung kann der Prompt schätzungsweise von **290 Zeilen auf ca. 140-150 Zeilen** gekürzt werden (etwa 50% Token-Reduktion).
- **Latenz:** Sinkt, da weniger Kontext-Token verarbeitet werden müssen und Chain-of-Symbol/Structured Logic das interne Reasoning beschleunigt.
- **Robustheit:** Die Hard Constraints sind gebündelt und damit prägnanter und sicherer (Post-Prompting-Effekt).
