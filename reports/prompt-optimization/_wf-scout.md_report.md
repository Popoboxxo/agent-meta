# Prompt Engineering Report: `_wf-scout.md`

## 1. Ausgangslage (Current State)
Die Datei `_wf-scout.md` definiert zwei Workflows (M und N) für das Scouting und Einbinden von externen Skills im `agent-meta` Framework. 

**Identifizierte Probleme & Ineffizienzen:**
1. **Verletzung der Schichten-Architektur (Provider-Agnostik):**
   In Sektion M wird explizit das "Claude-Ökosystem" genannt. Da die Datei im `1-generic` Verzeichnis liegt, ist dies ein harter Regelverstoß (siehe Best Practice 5.1). `1-generic` Templates müssen strikt provider-agnostisch sein.
2. **Token-Ineffizienz durch ASCII-Art:**
   Der Einsatz von `├─` und `└─` zur Darstellung eines Entscheidungsbaums kostet unnötig Tokens, erhöht die Latenz (Generation Speed) und ist anfällig für Parsing-Fehler seitens des LLMs.
3. **Redundanz & Verbosity:**
   Prosa-Formulierungen wie "Immer erst evaluieren — nie blind `--add-skill`. Neuer Skill startet mit `approved: false`" können durch kompaktes *Structured Prompting* direkt als Constraints in die Routing-Logik integriert werden.

## 2. Optimierungs-Strategie (Actionable Insights)
Basierend auf den Best Practices des Prompt-Engineer-Agenten wurden folgende Techniken angewandt:
- **Context Engineering 2026 (Schichten-Korrektur):** Ersetzung von "Claude" durch neutrale Begriffe wie "KI" oder "Agent".
- **Chain-of-Symbol (CoS):** Ersatz der aufwändigen ASCII-Bäume durch kompakte, lineare Repräsentationen (`[Condition] -> Action`), was das Reasoning des Modells beschleunigt und Token spart (Best Practice 4.3).
- **Structured Prompting:** Reduktion von textuellen Code-Blöcken zugunsten von extrem kompakten Key-Value/Bullet-Listen (Best Practice 3.1).

## 3. Konkreter Optimierungsvorschlag

**Aktueller Code (~24 Zeilen):**
```markdown
# Workflow M+N: Scouting & externes Skill-Repo

## M: Claude-Ökosystem scouten
Nur auf explizite Anfrage — NIEMALS automatisch.

```
1. agent-meta-scout → Scouting, Evaluation, Empfehlungs-Bericht
```

## N: Externes Repo als Skill einbinden
Trigger: User teilt Repo-URL, "als Skill einbinden?"

```
1. agent-meta-scout → Repo evaluieren (Qualität, Scope, SKILL.md vorhanden?)

2. Entscheidung:
   ├─ External Skill → agent-meta-manager: --add-skill + aktivieren
   │                 → git: "feat: add external skill <name>"
   ├─ Besser als Rule/Extension → User informieren
   └─ Nicht geeignet → User informieren + ggf. meta-feedback
```

Immer erst evaluieren — nie blind `--add-skill`. Neuer Skill startet mit `approved: false`.
```

**Optimierter Code (Verschlankung & Token-Reduktion):**
```markdown
# WF M+N: Scouting & External Skills

## M: KI-Ökosystem scouten
- **Trigger**: Explizite User-Anfrage (NIEMALS automatisch)
- **Action**: `agent-meta-scout` -> Scouting, Evaluation, Bericht

## N: Externes Repo als Skill einbinden
- **Trigger**: User-URL + "Skill einbinden?"
- **Schritt 1 Eval**: `agent-meta-scout` -> Qualität, Scope, `SKILL.md` prüfen. (PFLICHT: Nie blind `--add-skill`!)
- **Schritt 2 Decision Routing**:
  - `[Is Skill]` -> `agent-meta-manager` (`--add-skill`, init: `approved: false`) -> `git` ("feat: add external skill <name>")
  - `[Is Rule/Ext]` -> User informieren
  - `[Unfit]` -> User informieren -> `meta-feedback`
```

## 4. Fazit
Die optimierte Version ist robuster, hält die `1-generic`-Vorgaben des Frameworks ein und senkt den Token-Verbrauch durch eine drastische Reduktion von Prosa und ASCII-Formatierungen. Durch *Chain-of-Symbol*-Pfade und kompakte Constraints steigt die semantische Dichte, wodurch Agenten den Workflow zuverlässiger und schneller ausführen können.
