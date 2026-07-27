---
type: "Guide"
title: "Provider Abstraction Layer (PAL) — Syntax-Isolation"
description: "agent-meta generiert Agenten-Templates für 5 Provider aus einer 1-generic-Quelle. Das funktioniert nur wenn die Templates provider-agnostisch sind — sie dürfen keine..."
tags: [guide, feature]
timestamp: "2026-07-27"
resource: "../../sources/docs/guides/features/provider-abstraction-layer.md"
migrated_from: "docs/guides/features/provider-abstraction-layer.md"
---
# Provider Abstraction Layer (PAL) — Syntax-Isolation

> Dieses Dokument beschreibt den Provider Abstraction Layer: wie agent-meta abstrakte Delegations-Platzhalter
> in Templates verwendet und diese pro Provider in die native Syntax übersetzt — sowie wie Bootstrap-Mechanismen
> die Agent-Registrierung für verschiedene Provider-Modelle sicherstellen.

---

## Das Problem: Syntax Leaks

agent-meta generiert Agenten-Templates für 5 Provider aus **einer** `1-generic`-Quelle. Das funktioniert
nur wenn die Templates **provider-agnostisch** sind — sie dürfen keine provider-spezifische Syntax enthalten.

In der Praxis enthielt `1-generic/orchestrator.md`:

```
Agent(subagent_type="validator", prompt="Prüfe...")     ← Claude-only
task(subagent_type="developer", description="...", ...)  ← Opencode-only
@orchestrator <Aufgabe>                                   ← Funktioniert nur in Claude
```

Diese Syntax landete ungefiltert in **allen** Providern — Gemini, Continue, Copilot erhielten dieselben
Instruktionen mit Tools die dort nicht existieren. Ergebnis: Orchestrator-Delegation brach zusammen.

Zusätzlich: Gemini/Antigravity hat **keine** dateibasierte Agent-Registry — `.gemini/agents/*.md` sind
für die Runtime bedeutungslos. Agenten müssen per `define_subagent` API-Call **pro Session** registriert werden.
agent-meta hatte dafür keinen Mechanismus.

---

## Lösung: Drei-Schichten-Modell

```
1-generic Templates
    Verwenden NUR abstrakte Platzhalter:
    {{PAL_DELEGATE}}, {{PAL_FANOUT}}, {{PAL_PARALLEL_GROUP}}, {{PAL_FALLBACK}}
    ↓
Provider Abstraction Layer (PAL)
    ┌─────────────────────────────────────────────────────┐
    │ DelegationSyntaxEngine    BootstrapEngine           │
    │ (Syntax-Substitution)     (Agent-Registrierung)     │
    │                                                     │
    │ Liest:                    Liest:                    │
    │ • delegation-syntax.yaml  • provider-bootstrap.yaml │
    │ • provider-capabilities   • provider-capabilities   │
    └─────────────────────────────────────────────────────┘
    ↓
5 Provider — jeder mit seiner nativen Syntax
    Claude    | Gemini     | Opencode   | Continue   | Copilot
    Agent()   | Text-Mode  | task()     | @agent     | @agent
```

**Kernidee:** Templates deklarieren WAS getan werden soll (delegieren, parallelisieren, fallen back).
PAL entscheidet WIE — pro Provider in dessen nativer Syntax.

---

## PAL-Platzhalter

In `1-generic` Templates werden ausschließlich abstrakte Platzhalter verwendet:

| Platzhalter | Bedeutung | Beispiel-Output (Claude) |
|-------------|-----------|--------------------------|
| `{{PAL_DELEGATE}}` | Agent-Delegation | `Agent(subagent_type="dev", prompt="...")` |
| `{{PAL_FANOUT}}` | Parallele gleiche Agenten | `# FANOUT: Launch all agents in ONE response` |
| `{{PAL_PARALLEL_GROUP}}` | Parallele verschiedene Agenten | `# Gleichzeitig im Hintergrund:` |
| `{{PAL_FALLBACK}}` | Fallback wenn Tool-Calls fehlen | `Delegiere folgende Aufgabe an den Orchestrator:` |

Templates verwenden **niemals** provider-spezifische Tool-Namen oder Syntax.

---

## Delegationssyntax pro Provider

Definiert in `config/delegation-syntax.yaml`:

| Provider | delegate | parallel | fallback |
|----------|----------|----------|----------|
| **Claude** | `Agent(subagent_type=...)` | native parallel (Hintergrund) | Text-Delegation |
| **Opencode** | `task(subagent_type=...)` | native parallel (eine Antwort) | `@orchestrator` |
| **Gemini** | Text-basiert ("Rufe den ...-Agenten auf") | auto-parallel (Runtime) | "Bearbeite selbst" |
| **Continue** | `@agent Aufgabe` | sequentiell (kein Parallel) | `@orchestrator` |
| **Copilot** | `@agent Aufgabe` | sequentiell | "Bearbeite:" |

Jeder Provider bekommt genau die Syntax die in seiner Umgebung funktioniert — kein Syntax-Leak mehr.

---

## Bootstrap: Agent-Registrierung pro Provider

Nicht alle Provider laden Agenten automatisch aus Dateien. Definiert in `config/provider-bootstrap.yaml`:

| Provider | Mechanismus | Was sync.py tut |
|----------|------------|-----------------|
| **Claude, Opencode, Copilot** | file-based | Dateien in `agents/` ablegen — Runtime lädt automatisch |
| **Gemini** | api-based | Bootstrap-Instruktionen in `GEMINI.md` injizieren. Bei Session-Start muss der Hauptchat alle Agenten via `define_subagent` registrieren |
| **Continue** | config-based | Agenten-Metadaten in `.continue/config.yaml` eintragen |

### Gemini-Bootstrap im Detail

`sync.py` injiziert in `GEMINI.md` einen managed block mit Bootstrap-Instruktionen:

```
<!-- agent-meta:bootstrap-begin -->
## Agent Bootstrap — Session-Start Pflicht
...
1. Lies alle Agenten-Dateien aus `.gemini/agents/`
2. Registriere jeden Agenten via define_subagent API-Call
3. Erst danach: Bearbeite User-Anfragen
<!-- agent-meta:bootstrap-end -->
```

Ohne diese Registrierung existieren die 25+ Agenten **nicht** in der Gemini-Runtime.

---

## Capability Matrix

`config/provider-capabilities.yaml` dokumentiert was jeder Provider unterstützt:

```yaml
Claude:    subagent_dispatch: true,  parallel: true,  file_based: true,  hooks: true
Opencode:  subagent_dispatch: true,  parallel: true,  file_based: true,  hooks: false
Gemini:    subagent_dispatch: true,  parallel: true,  file_based: false, hooks: false
Continue:  subagent_dispatch: false, parallel: false, file_based: false, hooks: false
Copilot:   subagent_dispatch: false, parallel: false, file_based: true,  hooks: false
```

Diese Matrix wird von `DelegationSyntaxEngine` verwendet um zu entscheiden:
- Ob `{{PAL_TOOL_PREAMBLE}}` gerendert wird (nur für Provider mit Tool-Auflistungen)
- Ob Bootstrap nötig ist (`bootstrap_required: true` → Gemini)
- Ob parallele Ausführung unterstützt wird

---

## Neuen Provider anbinden

Um einen neuen Provider an PAL anzubinden sind 3 Schritte nötig:

1. **Delegationssyntax definieren** in `config/delegation-syntax.yaml`:
   ```yaml
   delegation_syntax:
     MeinProvider:
       delegate: '...'
       fanout: '...'
       fallback: '...'
       bootstrap: 'file-based'  # oder api-based oder config-based
   ```

2. **Capabilities deklarieren** in `config/provider-capabilities.yaml`:
   ```yaml
   capabilities:
     MeinProvider:
       subagent_dispatch: true
       parallel_execution: false
       file_based_agents: true
       ...
   ```

3. **Bootstrap konfigurieren** in `config/provider-bootstrap.yaml`:
   ```yaml
   bootstrap:
     MeinProvider:
       mechanism: 'file-based'
       action: 'none'
   ```

Keine Änderungen an Templates, Python-Code oder sync.py nötig — PAL ist rein Config-getrieben.

---

## Verwandte Dateien

| Datei | Zweck |
|-------|-------|
| `config/delegation-syntax.yaml` | Provider-spezifische Delegationssyntax |
| `config/provider-capabilities.yaml` | Was jeder Provider unterstützt |
| `config/provider-bootstrap.yaml` | Wie Agenten registriert werden |
| `scripts/lib/delegation_syntax.py` | `DelegationSyntaxEngine` |
| `scripts/lib/bootstrap.py` | `BootstrapEngine` |
| `templates/bootstrap/gemini-session-bootstrap.md` | Bootstrap-Template für Gemini |
| `agents/1-generic/orchestrator.md` | Verwendet `{{PAL_FALLBACK}}` Platzhalter |