# A2A Anti-Re-Delegation Gates

Provider-agnostische Regeln für A2A-Handoffs zwischen Agenten. Verhindert Delegations-Schleifen und unkontrollierten Spec-Dump in `payload.t`.

## Hard Reject Gates (jeder Verstoß → Dispatch ablehnen, User informieren)

1. **Self-Handoff verboten:** `source_agent == target_agent` ist ein harter Strukturfehler. Niemals akzeptieren.
2. **Tiefenlimit:** `delegation_depth` darf maximal `10` sein (konfigurierbar via `orchestrator.delegation.max_depth` in project.yaml, Default 10). Tiefer = struktureller Fehler im Aufrufer. Gilt nur für Provider ohne Plattform-Limit. **Claude Code: hardes Plattform-Limit von 5 Delegations-Ebenen** — nicht konfigurierbar (Subagents-Doc v2.1.198). Für Claude-Code-Projekte: A2A_MAX_DEPTH ≤ 5 in `.meta-config/project.yaml` setzen.
3. **T-Size-Limit:** `payload.t` darf maximal `300 Zeichen` umfassen. Bei Überschreitung → kein Dispatch, User informieren.
4. **Re-Delegation-Detection:** Wenn `payload.t` mit "Du bist" / "Du bist ein" / "Du bist eine" beginnt → das ist ein Re-Delegations-Versuch. Ablehnen, User informieren.

## Werte

- `delegation_depth`:
  - `0` = Hauptchat (User-Eingang)
  - `1` = Orchestrator (Routing-Ebene)
  - `2+` = Worker / Sub-Worker (Ausführungs-Ebene, bis 10)
- Hochzählen: bei jeder Delegation inkrementiert der Absender das Feld um 1.

## Verhalten bei Verstoß

| Verstoß | Aktion |
|---------|--------|
| `source_agent == target_agent` | HARD REJECT, keine Ausführung, User informieren |
| `delegation_depth > 10` | HARD REJECT, User informieren |
| `payload.t > 300 Zeichen` | KEIN Dispatch, User informieren ("kürze auf einen Satz") |
| `payload.t` startet mit "Du bist..." | HARD REJECT, User informieren ("Re-Delegation erkannt") |

## Singleton-Regel: Orchestrator-Spawn

**NUR der `main_chat` darf den `orchestrator` spawnen. Worker-Agents niemals.**

- `delegation_depth >= 2` → kein `subagent_type="orchestrator"` Dispatch erlaubt
- Verstoß → HARD REJECT, User informieren: "Singleton-Regel verletzt: Orchestrator darf nur vom main_chat gespawnt werden."

| Verstoß | Aktion |
|---------|--------|
| Worker ruft `task(subagent_type="orchestrator", ...)` | HARD REJECT, User informieren |
| Worker ruft `Agent(subagent_type="orchestrator", ...)` | HARD REJECT, User informieren |

> **Warum:** Mehrere parallele Orchestrator-Instanzen verursachen Konflikte in Routing, Checkpointing und Session-State. Es existiert genau EIN Orchestrator pro Session — der vom main_chat gespawnte.

## Execution-Trace-Isolation

Worker-Output an den Orchestrator muss eine **strukturierte Zusammenfassung** sein — keine rohen Execution-Traces propagieren.

**Pflicht:**
- Ergebnis in Kategorien: STATUS, RESULT, ARTIFACTS, ERRORS
- Interne Zwischenschritte (Tool-Calls, Reasoning) nicht an übergeordnete Agenten weitergeben
- Orchestrator fasst BARRIER-Ergebnisse weiter zusammen (Context Pollution verhindern)

**Verboten:**
- Rohe Bash-Outputs (Hunderte Zeilen) als Ergebnis zurückgeben
- Vollständige Datei-Inhalte in Ergebnis einbetten (→ Artifact Pattern verwenden)
- Sub-Agent-Kontexte mit Orchestrator-Kontext mischen

> Hintergrund: Context-Pollution durch Worker-State-Propagation ist einer der häufigsten Failure-Modi in Multi-Agent-Systemen (MAST-Paper, arXiv:2503.13657: 38% der Failures).

## Provider-Limits

| Provider | Max. Tiefe | Konfigurierbar? | Empfehlung |
|----------|-----------|-----------------|-----------|
| Claude Code | 5 | Nein (Plattform-Limit) | `A2A_MAX_DEPTH: 5` in project.yaml |
| Gemini / OpenCode / Continue | kein Limit bekannt | via `A2A_MAX_DEPTH` | Default 10 ausreichend |

Auf Claude Code erhält kein Subagent bei `delegation_depth >= 5` mehr das Agent-Tool (gilt ab Subagents-Doc v2.1.198).

## Propagation

Diese Regel wird via `sync.py` automatisch in alle Provider-Rules-Verzeichnisse propagiert:
- `.claude/rules/a2a-delegation-gates.md`
- `.gemini/rules/a2a-delegation-gates.md`
- `.continue/rules/a2a-delegation-gates.md`
