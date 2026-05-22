# Orchestrator — Universal Router

**JEDE Entwicklungsaufgabe geht über den Orchestrator.**

## Immer über Orchestrator

Feature | Bugfix | Refactoring | Analyse | Design | Konzept |
Recherche | Implementierung | Tests | Audit | Release | Docker |
Anforderungen | Validierung | Dokumentation | Log-Analyse | Ideation

Der Orchestrator zerlegt komplexe Aufgaben in Sub-Tasks, parallelisiert
unabhängige Arbeiten und delegiert an spezialisierte Worker-Agenten.

## Ausnahmen — direkter Dispatch

NUR für atomare Einzeloperationen (ein Schritt, ein Agent, keine Abhängigkeiten):

| Operation | Direkt an | Bedingung |
|-----------|-----------|-----------|
| Commit, Push, Branch, Tag, PR | `git` | Einzelner Git-Befehl |
| Sync, Upgrade, Meta-Konfiguration | `agent-meta-manager` | Reine agent-meta-Operation |
| Bug/Feature/Verbesserung melden | `feedback` | Issue-Erstellung |
| Session-Erkenntnisse speichern | `documenter` | Nur bei Session-Ende |

> **Faustregel:** Wenn du >1 Tool-Call brauchst → Orchestrator.
> Wenn du unsicher bist → Orchestrator.
> Wenn du Code lesen/analysieren/schreiben willst → Orchestrator.

## Die Smarte Kommunikationsoberfläche (Hauptchat)

Der Hauptchat ist die intelligente Schnittstelle zum Nutzer. Er darf und soll:
- Dateien lesen und den Kontext analysieren
- Befehle ausführen, um den Ist-Zustand zu begreifen (z.B. Git-Status, Tests)
- Architekturen und Konzepte im Dialog mit dem Nutzer schärfen

**Aber:** Sobald es an die eigentliche *Ausführung* von Entwicklungsaufgaben, tiefgreifenden Prüfungen oder Multi-Step-Workflows geht, tritt die automatische Delegationspflicht in Kraft. Direkte Delegation an Worker-Agenten (developer, tester etc.) ist im Hauptchat weiterhin verboten — all dies geht über den Orchestrator.

## User-Override: Bewusste Hauptchat-Ausführung

Der User hat jederzeit das Recht, die Orchestrator-Pflicht zu umgehen und den Auftrag direkt im Hauptchat ausführen zu lassen.

### Trigger-Sätze (User sagt explizit)

- "Nicht delegieren"
- "Mach das hier"
- "Im Hauptchat bitte"
- "Kein Orchestrator"
- "Ohne Orchestrator"
- "Ich will hier arbeiten"
- "Delegiere nicht"

### Verhalten bei User-Override

```
1. Trigger-Satz erkannt
2. Bestätigung: "Ich arbeite den Auftrag im Hauptchat selbst ab."
3. Main-Chat führt die Aufgabe aus:
   - Liest Dateien selbst
   - Schreibt Code selbst
   - Führt Befehle aus
   - Führt Multi-Step-Workflows aus
   → Kurzfristig verhält sich der Hauptchat wie ein klassischer Agent
4. Nach Abschluss:
   → "Soll ich für zukünftige ähnliche Anfragen ebenfalls im Hauptchat
      arbeiten, oder wieder über den Orchestrator routen?"
   → Optionen:
      - "Immer Hauptchat" → setze unknown-fallback=main-chat (project.yaml)
      - "Immer Orchestrator" → strict=true bleibt
      - "Frag jedes Mal" → unknown-fallback=ask-user
      - "Nur dieses Mal" → Einzel-Override, kein Persistenz
```

### Regeln für den Override

- Der Override gilt NUR für die aktuelle Anfrage (oder persistiert wenn User das wünscht)
- Der Override hebt die "Verboten im Hauptchat"-Regel auf
- Alle anderen Rules (branch-guard, commit-conventions, language, etc.) bleiben aktiv
- Meta-Feedback wird trotzdem erstellt: "User wollte Hauptchat-Modus für: [anonymisierter Intent]"

## Konfiguration: Orchestrator-Schalter

Das Verhalten wird zentral in `.meta-config/project.yaml` gesteuert:

```yaml
orchestrator:
  enabled: true        # true = Orchestrator aktiv, false = Main-Chat-Modus
  strict: true         # true = Immer delegieren, false = Fallback erlaubt
  unknown-fallback:
    meta-feedback: true   # Send anonymized feedback to agent-meta (default: true)
    main-chat: true       # Allow main chat to handle task (default: true)
    ask-user: false       # Ask user for preference (default: false)
```

| Modus | enabled | strict | meta-feedback | main-chat | ask-user | Verhalten bei unbekanntem Intent |
|-------|---------|--------|---------------|-----------|----------|-----------------------------------|
| **Strict** | true | true | true | false | false | Meta-Feedback, NICHT selbst ausführen |
| **Relaxed** | true | false | true | true | false | Main-Chat arbeitet selbst + Meta-Feedback |
| **Ask-First** | true | — | — | — | true | User gefragt: "Hier oder Feedback?" |
| **Disabled** | false | — | — | — | — | Kein Orchestrator, Main-Chat macht alles selbst |
| **Custom** | true | false | true | true | true | User gefragt → dann entscheiden |

**Fallback-Priorität:**
1. `ask-user=true` → Immer User fragen (höchste Priorität)
2. `strict=true` + `meta-feedback=true` → Feedback + Nachfrage
3. `strict=false` + `main-chat=true` → Main-Chat selbst + ggf. Feedback
4. Kein Fallback aktiv → Klärungsfrage

**Empfehlung:** Default ist `strict` für Produktionsprojekte, `relaxed` für Prototypen, `disabled` für kleine Einzelnutzer-Projekte.

## Automatische Delegationspflicht (Auto-Handoff)

Wenn der Hauptchat eine Anfrage erhält, die nicht unter "Ausnahmen — direkter Dispatch" fällt, und kein expliziter Trigger-Satz für einen User-Override vorliegt, greift der automatische Handoff an den Orchestrator.

Der Hauptchat weigert sich **niemals** mit einem Text-Block. Statt den Nutzer aufzufordern, den Orchestrator manuell aufzurufen, übernimmt der Hauptchat dies selbstständig im Hintergrund.

### Ablauf des Auto-Handoffs

1. **Kontext-Phase:** Der Hauptchat liest Dateien, führt Recherche-Tools aus und spricht mit dem Nutzer, um den genauen Umfang der Aufgabe zu verstehen.
2. **Delegations-Phase:** Sobald der Intent klar ist und die Ausführung beginnen soll, ruft der Hauptchat zwingend das systemeigene Tool zur Orchestrator-Delegation auf.
3. **Übergabe:** Der Orchestrator übernimmt als "Verwaltungs-Bestie" im Hintergrund die Task-Zerlegung und Parallelisierung der Worker-Agenten.

### Technische Durchsetzung auf LLM-Ebene

Jeder Provider-Agent liest diese Datei als System-Instruktion ein. Sobald ein auszuführender Entwicklungs-, Architektur- oder Prüf-Auftrag ansteht:
1. **Kein Redirection-Text:** Gib NIEMALS eine Textnachricht aus, die den Nutzer bittet, den Orchestrator manuell aufzurufen.
2. **Tool-Pflicht:** Nutze die für deinen Provider verfügbare Methodik (- **In Continue (IDE):** Tippt `@orchestrator` gefolgt von Eurer Aufgabe ein.), um den Orchestrator lautlos zu starten und ihm den Auftrag (inkl. deiner Kontext-Erkenntnisse) zu übergeben.

## Hauptchat ohne Orchestrator (Fallback)

Wenn der Orchestrator nicht verfügbar ist:
- Branch-Guard manuell: `git branch --show-current`
- Auf `main`/`master` → Branch anlegen
- Keine parallelen Tasks möglich
- Sequentieller Workflow selbst koordinieren

