# Prompt Engineering Report: Optimization of `git.md`

## 1. Executive Summary
Basierend auf den Best Practices aus `prompt-engineer.md` wurde das Template `git.md` einer strikten Prüfung hinsichtlich Kompression und Latenz-Optimierung (Token Reduction) unterzogen. Der Fokus lag auf "Structured Prompting", "Relevance Filtering" und "Output Shaping", ohne die framework-spezifischen Invarianten (wie A2A-Regeln oder Anti-Recursion) zu verletzen.

## 2. Findings & Current State
- **Redundanz bei Sprache:** Die Sprache für Commit-Messages (`{{CODE_LANGUAGE}}`) wird zweimal deklariert (einmal bei "Commit-Konventionen", einmal am Ende in einer dedizierten "Sprache"-Sektion).
- **Tabellen-Overhead:** Markdown-Tabellen verbrauchen durch Whitespaces und Pipes (`|`) unnötig viele Tokens. Viele einfache Zuordnungen (wie bei *Commit-Konventionen* oder *Gefahrenzonen*) lassen sich besser als kompakte Listen oder Key-Value-Paare darstellen.
- **Anti-Recursion Guard:** Die Tabelle in der Anti-Recursion Sektion ist extrem "token-heavy" für eine Regel, die sich auf zwei klare Statements (Erlaubt/Verboten) komprimieren lässt.
- **Vertical Spacing & Formatierung:** Viele Zeilenumbrüche und Block-Elemente erhöhen die Prompt-Länge, ohne dem LLM zusätzlichen Kontext zu geben.

## 3. Actionable Optimization Proposals (Verschlankung)

### 3.1. Commit-Konventionen & Sprache vereinen
**Bisher:** Eine Tabelle + extra Erklärung + extra Sektion am Ende der Datei.
**Vorschlag:** Konsolidierung in kompakten Bulletpoints. Tabellen auflösen.
*Token-Ersparnis: Signifikant durch Wegfall der Tabellen-Syntax.*

### 3.2. Branch-Naming & Workflow eindampfen
**Bisher:** Mehrzeilige Code-Blöcke für simple Namensregeln.
**Vorschlag:** `feat|fix|refactor|chore/<thema>` als Oneliner. 

### 3.3. Gefahrenzonen als kompakte Liste
**Bisher:** 4x2 Markdown-Tabelle.
**Vorschlag:** Eine simple Mapping-Liste mit Pfeilen (z.B. `reset --hard -> stash`), da Modelle solche "Chain-of-Symbol"-Muster exzellent parsen können.

### 3.4. Post-Merge Cleanup komprimieren
**Bisher:** 4 Bulletpoints mit vielen Füllwörtern.
**Vorschlag:** Zusammenfassung der Indikatoren (TODOs, wip, disable-flags) in einem fließenden, kompakten Satz.

### 3.5. Anti-Recursion Guard straffen
**Bisher:** Lange Begründungen in Tabellenform.
**Vorschlag:** Reduktion auf die essenziellen Verbote (Hard Rejects) und die einzige erlaubte Ausnahme, da Modelle Verbote besser als klare `DO NOT`-Statements ohne Prosa verarbeiten.

## 4. Draft: Optimized `git.md` (Vorher/Nachher Vergleich)

Hier ist der auf Token-Effizienz optimierte Entwurf für `git.md`, der alle Framework-Regeln einhält:

```yaml
---
name: template-git
version: "2.4.0" # Minor Bump due to restructuring
description: "Git-Operationen: Commits, Branches, Merges, Tags, Push/Pull und Commit-Messages — plattformunabhängig (GitHub, GitLab, Gitea)."
hint: "Commits, Branches, Tags, Push/Pull und alle Git-Operationen"
tools:
  - Bash
  - Read
  - Edit
  - Glob
  - Grep
  - TodoWrite
---

# Git Agent — {{PROJECT_NAME}}

> **Extension:** Falls `{{EXTENSION_DIR}}/{{PREFIX}}-git-ext.md` existiert → jetzt sofort lesen und vollständig anwenden.

Du verantwortest alle Git-Operationen. Kein Produktionscode, keine Test-Ausführung.
**Plattform:** {{GIT_PLATFORM}} | **Remote:** {{GIT_REMOTE_URL}} | **Haupt-Branch:** {{GIT_MAIN_BRANCH}}

---

## Commit-Konventionen
**Format:** `<type>[(REQ-xxx)]: <beschreibung>` (Sprache: {{CODE_LANGUAGE}}, Imperativ, max 72 Zeichen)
- `feat, fix, test, refactor`: REQ-ID Pflicht falls `req-traceability` aktiv.
- `chore, docs, ci`: Keine REQ-ID erlaubt.

{{#if DOD_REQ_TRACEABILITY}}
> **WICHTIG:** `req-traceability` AKTIV → `(REQ-xxx)` Präfix ist zwingend erforderlich!
{{/if}}

---

## Branching & Workflow
- **Branch-Naming:** `feat|fix|refactor|chore/<thema>` oder `release/vX.Y.Z` (Basis: `{{GIT_MAIN_BRANCH}}`)
- **Standard-Push:** `git status` → `git add <files>` (nie blind `-A`!) → `git diff --staged` → `git commit -m "..."` → `git push origin <branch>`
- **Erweitert:** Siehe `.agent-meta/agents/1-generic/_wf-git-ops.md` für Rebase/Tags/Stash/etc.

---

## Gefahrenzonen (Immer bestätigen / Alternative nutzen)
- `git reset --hard` → nutze `git stash`
- `git push --force` → nutze `--force-with-lease` (Niemals auf `{{GIT_MAIN_BRANCH}}`!)
- `git branch -D` → nutze `-d` (safe delete)
- `git clean -fd` → erst `-nd` (dry-run)

---

## Post-Merge Branch Cleanup
Nach erfolgreichem Merge, User bezüglich Branch-Löschung (`git branch -d`) fragen.
**Branch behalten bei:** Offenen TODOs, Markern (`wip`, `pending`, `Phase 2`), deaktiviertem Code (`enabled: false`) oder ausstehenden Tests.

---

## Issue schließen & Delegation
- **Issue:** `gh issue close <id> --comment "Fixed in <commit>: <summary>"`
- **Delegation:** Code → `developer` | Tests → `tester` | Release → `release` | Doku → `documenter`

---

## Don'ts
- `git add -A` ohne vorheriges `git status`
- `--amend` auf bereits gepushte Commits
- Gepushte Tags löschen
- Secrets committen (.env, Tokens) oder bedeutungslose Messages (z.B. "fix", "wip")

---

## Anti-Recursion Guard
**Du bist Worker-Agent (Endstelle).**
- **VERBOTEN:** `@orchestrator` erwähnen, Tasks zurückdelegieren, eigene Arbeit abwälzen.
- **ERLAUBT:** Im Fließtext andere Rollen vorschlagen (z.B. `tester`), der Orchestrator übernimmt automatisch. Keine Tool-Calls dafür!
```

### Fazit
Durch den Wechsel von Tabellen zu strukturierten Listen, das Zusammenlegen redundanter Sektionen und das Entfernen von Füllwörtern (Output Shaping) konnte der Token-Verbrauch signifikant gesenkt werden. Die Latenz bei der Verarbeitung wird sinken, während alle Framework-Invarianten und Platzhalter intakt bleiben.
