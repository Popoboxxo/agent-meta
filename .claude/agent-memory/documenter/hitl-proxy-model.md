---
name: hitl-proxy-model
description: HITL-Gates müssen main_chat als gültigen User-Proxy anerkennen, sonst Deadlock
metadata:
  type: feedback
---

# HITL-Gate-Deadlock: main_chat als User-Proxy

## Die Regel

HITL-Gates ("Destruktive Aktionen bestätigen") müssen `main_chat` **als gültigen User-Proxy** anerkennen. Der User hat keinen direkten Kanal zum Orchestrator — alle Freigaben kommen via main_chat. Wenn der Orchestrator diese ignoriert, entsteht eine Endlosschleife.

**Why:** Delegationskette ist User → main_chat → orchestrator. Der Orchestrator hat keine separate Verbindung zum User. main_chat ist sein einziger User-Interface. Freigaben durch main_chat sind gültige User-Freigaben.

## Betroffenes Artefakt (Session 2026-07-01)

- Commit 139eab7: agents/1-generic/orchestrator.md v6.2.0 (Legacy) + agents/1-generic-modern/orchestrator.md v7.2.0 (Modern)
- Docs: `CLAUDE.md` Singleton-Regel aktualisiert mit Proxy-Klärung

## Das Problem: Deadlock-Zyklus

**Alt (falsch):**
```
User sagt: "mach jetzt"
  ↓
main_chat relaytet: "User freigeben"
  ↓
Orchestrator: "Destruktive Aktion! Bitte bestätigen."
  ↓
User: "ich hab doch schon freigegeben!"
  ↓
main_chat relaytet nochmal: "User freigeben"
  ↓
Orchestrator: [schleife]
```

**Die Wurzel:** Orchestrator-Dokumentation sagte "IMMER bestätigen — auch bei explizitem Befehl". Das machte main_chat-Relays ungültig.

## Die Lösung: Proxy-Modell Explicit

**Neu (richtig):**
```
Orchestrator <persona>:
> main_chat ist dein User-Proxy: seine Anweisungen und ausdrücklich relayten 
> Freigaben tragen User-Autorität — der User hat keinen direkten Kanal zu dir.
```

**Verhalten:**
1. Wenn main_chat "User freigeben" relaytet → als gültig akzeptieren
2. TROTZDEM warnen/dokumentieren (Schutzwirkung bleibt)
3. Aber nicht erneut bestätigen (Deadlock-Brecher)
4. Agent-zu-Agent-Freigaben (worker → orchestrator) sind weiter ungültig

## Wichtige Grenzen

Dieses Proxy-Modell gilt **nur für main_chat**:
- `junior-developer` fragt Orchestrator: "Darf ich löschen?" → NEIN, warte auf User
- `code-reviewer` empfiehlt Löschung → NEIN, Warnung
- Nur main_chat-Freigaben zählen als User-Freigaben

## Verknüpfte Begriffe

[[singleton-orchestrator-guard]] — Orchestrator ist Singleton, nur main_chat darf ihn spawnen
[[template-migration-pitfalls]] — Andere große Bug-Klasse dieser Session (guards bei Classic→Modern Port)

---

**Fix in Production:** agents/1-generic/orchestrator.md v6.2.0 + agents/1-generic-modern/orchestrator.md v7.2.0
**Dokumentation:** CLAUDE.md Singleton-Regel, Abschnitt "Orchestrator — Universal Router"
