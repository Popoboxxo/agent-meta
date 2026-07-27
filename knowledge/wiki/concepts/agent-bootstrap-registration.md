---
type: "Concept"
title: "Konzept: Agent Bootstrap & Subagent Registration"
description: "Spezifikation der Laufzeit-Agenten-Registrierung für Provider ohne automatische Dateisystem-Agenten-Erkennung (z.B. Gemini / Antigravity via define_subagent)."
tags: [concept, runtime, bootstrap, status:active]
timestamp: "2026-07-27"
resource: "AGENTS.md"
migrated_from: "AGENTS.md"
---
# Konzept: Agent Bootstrap & Subagent Registration

> Status: **Umgesetzt — aktiv**  
> Verwandt: [SE-Cascade auf Gemini / Antigravity](../topics/se-cascade-gemini.md), [Layer Model](architecture-layer-model.md)  
> Betroffen: `AGENTS.md`, `.gemini/agents/`  

---

## 1. Problemstellung

Verschiedene AI-Plattformen handhaben die Entdeckung und Registrierung von Agenten-Rollen unterschiedlich:
- **Claude Code / Opencode**: Lesen Agenten-Prompts automatisch aus vordefinierten Verzeichnissen (`.claude/agents/` oder `.opencode/agents/`).
- **Gemini / Antigravity**: Erfordern eine explizite Laufzeit-Registrierung aller verfügbaren Subagenten per API-Aufruf (`define_subagent`) zu Beginn jeder Session.

Ohne diesen Registrierungsschritt existieren die Agenten nicht in der Antigravity-Runtime, und der Orchestrator kann keine Aufgaben delegieren.

---

## 2. Der Session-Bootstrap-Prozess

Zu Beginn JEDER Antigravity/Gemini Session gilt folgende verpflichtende Abfolge:

```
  Session-Start
        │
        ▼
  1. Dateisystem-Scan: Lies alle .md Dateien aus .gemini/agents/
        │
        ▼
  2. Iterative Registrierung via API:
     define_subagent(name="<agent-name>", description=..., system_prompt=...)
        │
        ▼
  3. Runtime betriebsbereit: Orchestrator kann nun frei delegieren
```

---

## 3. Registrierte Agenten-Rollen

Der Bootstrap-Prozess schaltet das gesamte Portfolio von 58 standardisierten Agenten-Rollen frei (u.a. `developer`, `tester`, `orchestrator`, `knowledge-migrator`, `security-auditor`, `refactoring-specialist` etc.).

---

## 4. Schutz vor Laufzeitfehlern

Wird der Bootstrap-Schritt übersprungen, schlagen Delegationsversuche mit Fehlermeldungen fehl (Subagent `name` nicht gefunden). Der Bootstrap-Block in `AGENTS.md` ist daher als kritische Laufzeitanweisung hervorgehoben.