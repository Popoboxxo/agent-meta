# SE-Cascade auf Gemini / Antigravity

## Problem

Auf Gemini/Antigravity unterstützt die Umgebung kein natives Subagent-Dispatch-Tool (`Agent` ist unsupported). Die SE-Cascade (Systems Engineering Kaskade) kann deshalb nicht über den `se-orchestrator` mit paralleler Worker-Delegation ausgeführt werden.

## Lösung: `scripts/run-cascade.py`

Das Skript `scripts/run-cascade.py` erzeugt **strukturierte Prompt-Dateien** für jede SE-Stufe. Der User kopiert den Prompt in seine IDE (Gemini, Claude, Opencode, etc.) und speichert das Ergebnis zurück. Das Skript selbst ruft **keine LLM-API** auf — es ist vollständig provider-agnostisch.

## Schritt-für-Schritt Anleitung

### 1. Cascade starten

```bash
# Direkte Eingabe
python scripts/run-cascade.py --input "System needs to process video streams"

# Oder aus Datei
python scripts/run-cascade.py --input-file docs/stakeholder_needs.md
```

Ausgabe:
```
Created session: cascade-20260529-143022-abc12345
Session directory: .se-cascade/cascade-20260529-143022-abc12345

  [l1-requirements] Prompt -> .se-cascade/cascade-.../prompts/stage_00_l1-requirements.md
  [l1-critic]       Prompt -> .se-cascade/cascade-.../prompts/stage_01_l1-critic.md
  ...

Next step:
  1. Open: .se-cascade/cascade-.../prompts/stage_00_l1-requirements.md
  2. Copy the prompt into your IDE / LLM.
  3. Save the response to the indicated output file.
  4. Resume: python scripts/run-cascade.py --resume cascade-20260529-143022-abc12345
```

### 2. Prompt ausführen

Öffne die generierte Prompt-Datei:

```bash
cat .se-cascade/<session>/prompts/stage_00_l1-requirements.md
```

Kopiere den Inhalt in Gemini/Antigravity (oder Claude, Opencode, etc.) und führe ihn aus.

### 3. Ergebnis speichern

Speichere die Antwort des LLM in die im Prompt angegebene Datei:

```bash
# Beispiel für Stage 0
.se-cascade/<session>/stage_0_l1_requirements.md
```

### 4. Nächste Stufe starten

```bash
python scripts/run-cascade.py --resume <session-id>
```

Das Skript erkennt automatisch, welche Stufen bereits abgeschlossen sind, und zeigt den Prompt für die nächste Stufe an.

### 5. Repeat

Wiederhole Schritte 2–4 bis alle 9 Stufen durchlaufen sind.

## Stufen-Übersicht

| # | Stage | Agent | Beschreibung |
|---|-------|-------|-------------|
| 0 | `l1-requirements` | `se-requirements` | Stakeholder Needs → Formal Requirements |
| 1 | `l1-critic` | `se-critic` | Kritische Prüfung der L1 Requirements |
| 2 | `l2-architecture` | `se-architect` | White-Box Dekomposition |
| 3 | `l2-critic` | `se-critic` | Kritische Prüfung der L2 Architektur |
| 4 | `interface-sync` | `se-interface-mgr` | Signal Flow & Interface Registry |
| 5 | `termination-check` | `se-termination` | Leaf or Recurse Entscheidung |
| 6 | `validation` | `se-validator` | L1 User-Journey Validation |
| 7 | `verification` | `se-verifier` | Multi-Level Verification |
| 8 | `integration-test` | `se-integration-and-test-manager` | V&V Orchestration |

## Fortsetzung nach Unterbrechung

Jede Session bekommt eine eindeutige ID (`cascade-YYYYMMDD-HHMMSS-<hash>`).

```bash
# Status prüfen
python scripts/run-cascade.py --status <session-id>

# Alle Sessions anzeigen
python scripts/run-cascade.py --list-sessions

# Fortsetzen
python scripts/run-cascade.py --resume <session-id>
```

## Aufräumen

```bash
# Sessions älter als 7 Tage löschen
python scripts/run-cascade.py --clean-old --max-age 7
```

## Alternativen

| Plattform | Empfohlene Methode |
|-----------|-------------------|
| **Claude** | Native Subagent-Support → `se-orchestrator` verwenden |
| **Opencode** | Native Subagent-Support → `se-orchestrator` verwenden |
| **Gemini / Antigravity** | `run-cascade.py` (diese Anleitung) |

> **Hinweis:** `run-cascade.py` funktioniert auch auf Claude und Opencode. Es ist eine portable Fallback-Lösung für alle Umgebungen ohne native Orchestrator-Delegation.
