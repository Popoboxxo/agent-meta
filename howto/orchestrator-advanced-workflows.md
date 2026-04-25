# Orchestrator — Erweiterte Workflows

Diese Datei enthält seltene Orchestrator-Workflows die nur auf explizite Anfrage geladen werden.
Der Orchestrator liest diese Datei mit dem Read-Tool wenn der Nutzer einen der unten genannten
Trigger-Begriffe verwendet.

---

## Workflow H2: Auf neue agent-meta Version upgraden

Trigger: "Upgrade agent-meta", "Neue agent-meta Version", "agent-meta aktualisieren"

```
1. Aktuelle Version prüfen:
   cat .agent-meta/VERSION
   cat .meta-config/project.yaml  # → "agent-meta-version"

2. CHANGELOG der neuen Version lesen (Breaking Changes?):
   cd .agent-meta && git fetch && git log --oneline HEAD..v<neue-version> && cd ..
   cat .agent-meta/CHANGELOG.md

3. Submodul auf neue Version ziehen:
   cd .agent-meta && git checkout v<neue-version> && cd ..

4. agent-meta-version in .meta-config/project.yaml aktualisieren

5. Dry-Run:
   python .agent-meta/scripts/sync.py --config .meta-config/project.yaml --dry-run
   → sync.log prüfen: neue Warnungen = fehlende Variablen

6. Fehlende Variablen in .meta-config/project.yaml ergänzen
   (Referenz: cat .agent-meta/howto/project.yaml.example)

7. Sync ausführen:
   python .agent-meta/scripts/sync.py --config .meta-config/project.yaml

8. Extensions aktualisieren:
   python .agent-meta/scripts/sync.py --config .meta-config/project.yaml --update-ext

9. git → Commit: "chore: upgrade agent-meta to v<neue-version>"
   Dateien: .claude/agents/ .claude/3-project/ .agent-meta .meta-config/project.yaml
```

---

## Workflow L: GitHub Issue bearbeiten

Trigger: "schau dir Issue #X an", "fix Issue", "bearbeite offene Issues"

```
0. git          → Issue(s) abrufen: gh issue list / gh issue view <id>
1. git          → Branch-Guard (→ fix/<issue> oder feat/<issue>)
2. requirements → Issue als REQ aufnehmen oder bestehende REQ-ID zuordnen
3. tester       → Reproduzierenden Test schreiben (bei Bugs: Red Phase)
4. developer    → Fix oder Feature implementieren
5. tester       → Tests ausführen, Regression prüfen
6. validator    → DoD-Check
7. documenter   → Doku aktualisieren falls nötig
8. git          → Commit + Push + Issue schließen:
                  gh issue close <id> --comment "Fixed in <commit>"
```

Bug vs. Feature:
- Bug → Schritt 3 zuerst (reproduzierender Test), dann Fix
- Feature → wie Workflow A, Ausgangspunkt ist das Issue

---

## Workflow M: Claude-Ökosystem scouten

Trigger: "Scout neue Skills", "Was gibt es Neues im Claude-Ökosystem?", "Bewerte <Repo-URL>",
         "Entdecke neue Agenten / Rules / Patterns", "Suche Skills für <Thema>"

**Nur auf explizite Nutzer-Anfrage — NIEMALS automatisch starten.**

```
1. agent-meta-scout → Scouting, Evaluation und Empfehlungs-Bericht
```

Ergebnis: Strukturierter Bericht mit bewerteten Kandidaten und Einbindungsvorschlägen.

---

## Workflow N: Externes Skill-Repo vorgeschlagen

Trigger: "Schau dir dieses Repo an: <URL>", "Könnte man das als Skill einbinden?",
         "Ich habe ein nützliches Repo gefunden", User teilt GitHub-Link zu spezialisiertem Repo

```
1. agent-meta-scout → Repo evaluieren (Qualität, Scope, SKILL.md vorhanden?)
                      Ergebnis: Bewertung + Empfehlung

2. Entscheidung:
   ├─ Empfehlung: External Skill
   │   → agent-meta-manager → --add-skill ausführen
   │   → agent-meta-manager → Skill im Projekt aktivieren
   │   → git → Commit: "feat: add external skill <name>"
   │
   ├─ Empfehlung: Besser als Rule/Extension
   │   → User informieren + ggf. Rule/Extension anlegen
   │
   └─ Empfehlung: Nicht geeignet
       → User informieren + ggf. meta-feedback
```

**Wichtig:** Immer erst evaluieren (Scout), nie blind `--add-skill` ausführen.
Neuer Skill startet mit `approved: false` — explizite User-Bestätigung nötig.

---

## Workflow K: Feedback an agent-meta

Trigger: Nutzer hat Feedback zum Framework, oder am Session-Ende

```
1. meta-feedback → Feedback aufbereiten + als GitHub Issue formulieren
2. meta-feedback → Issue erstellen (nach Nutzer-Bestätigung)
```

Am Session-Ende aktiv nachfragen:
> "Gab es etwas, das im agent-meta-Framework fehlt, unklar war oder verbessert werden könnte?"
