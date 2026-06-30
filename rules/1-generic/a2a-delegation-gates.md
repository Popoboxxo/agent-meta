# A2A Anti-Re-Delegation Gates

Provider-agnostische Regeln für A2A-Handoffs zwischen Agenten. Verhindert Delegations-Schleifen und unkontrollierten Spec-Dump in `payload.t`.

## Hard Reject Gates (jeder Verstoß → Dispatch ablehnen, User informieren)

1. **Self-Handoff verboten:** `source_agent == target_agent` ist ein harter Strukturfehler. Niemals akzeptieren.
2. **Tiefenlimit:** `delegation_depth` darf maximal `{{A2A_MAX_DEPTH}}` sein (konfigurierbar via `orchestrator.delegation.max_depth` in project.yaml, Default 10). Tiefer = struktureller Fehler im Aufrufer.
3. **T-Size-Limit:** `payload.t` darf maximal `{{A2A_T_SIZE_LIMIT}} Zeichen` umfassen. Bei Überschreitung → kein Dispatch, User informieren.
4. **Re-Delegation-Detection:** Wenn `payload.t` mit "Du bist" / "Du bist ein" / "Du bist eine" beginnt → das ist ein Re-Delegations-Versuch. Ablehnen, User informieren.

## Werte

- `delegation_depth`:
  - `0` = Hauptchat (User-Eingang)
  - `1` = Orchestrator (Routing-Ebene)
  - `2+` = Worker / Sub-Worker (Ausführungs-Ebene, bis {{A2A_MAX_DEPTH}})
- Hochzählen: bei jeder Delegation inkrementiert der Absender das Feld um 1.

## Verhalten bei Verstoß

| Verstoß | Aktion |
|---------|--------|
| `source_agent == target_agent` | HARD REJECT, keine Ausführung, User informieren |
| `delegation_depth > {{A2A_MAX_DEPTH}}` | HARD REJECT, User informieren |
| `payload.t > {{A2A_T_SIZE_LIMIT}} Zeichen` | KEIN Dispatch, User informieren ("kürze auf einen Satz") |
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

## Propagation

Diese Regel wird via `sync.py` automatisch in alle Provider-Rules-Verzeichnisse propagiert:
- `.claude/rules/a2a-delegation-gates.md`
- `.gemini/rules/a2a-delegation-gates.md`
- `.continue/rules/a2a-delegation-gates.md`
