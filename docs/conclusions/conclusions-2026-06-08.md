# Erkenntnisse — 8. Juni 2026

## Session-Zusammenfassung

Bugfix-Session auf Branch `fix/bugfix-session-june-2026` — 12 Bugs gefixt, A2A-Core-Engine implementiert (Phase 0), PAL um A2A-Handoff erweitert (Phase 1), Orchestrator-Guard-Hook entwickelt.

---

## 1. A2A-Core-Engine — Phase 0

### Problem
A2A-Envelope-Runtime fehlte vollständig — nur Papier-Spezifikation (Schema + Concept Doc), kein Code. Orchestrator konnte keine A2A-Envelopes erzeugen.

### Lösung
`scripts/lib/a2a.py` — A2AEnvelope-Klasse:
- `generate_handoff_id()` — thread-safe ID-Generierung (HOFF-YYYYMMDD-NNN)
- `A2AEnvelope.create()` — Factory + Validierung in einem Schritt
- `A2AEnvelope.validate()` — jsonschema + manuelles Fallback
- `A2AEnvelope.to_json()` / `from_json()` — Serialisierung mit JSON-Roundtrip
- `__slots__` — Speichereffizienz
- Vollständige Abdeckung von optionalen Feldern: `schema_ref`, `trace_parent`, `trace_context`, `retry_count`, `max_retries`, `batch`, `requires_human_approval`, `negotiated_format`, `supersession`, `metadata`

### Tests
`tests/test_a2a.py` — 31 Tests: ID-Format, Thread-Safety, Factory, Validierung (11 Fehlerfälle), Serialisierung (JSON-Roundtrip), Gleichheit, Repr.

---

## 2. PAL A2A-Handoff — Phase 1

### Problem
DelegationSyntaxEngine konnte keine A2A-Envelopes erzeugen; `{{A2A_ENVELOPE}}`-Platzhalter wurden nicht behandelt.

### Lösung
- `delegation_syntax.py`: `build_handoff()` erzeugt A2AEnvelope + provider-spezifische Delegations-Syntax in einem Schritt
- `delegation_syntax.py`: `apply()` ersetzt `{{A2A_ENVELOPE}}` durch Runtime-Placeholder-Kommentar
- `delegation_syntax.py`: `_RUNTIME_PLACEHOLDERS`-Konstante (agent, task, A2A_ENVELOPE) — preserved von `apply()`
- `config.py` `substitute()`: Runtime-Whitelist für `agent`, `task`, `A2A_ENVELOPE` — diese Platzhalter werden nicht gewarnt sondern durchgereicht
- `config/delegation-syntax.yaml`: `handoff:`-Block für alle 5 Provider (Claude, Opencode, Gemini, Continue, Copilot) — alle mit `{{A2A_ENVELOPE}}`-Platzhalter

### Tests
`tests/test_delegation_syntax.py` — 19 Tests: build_handoff() (7 Szenarien), apply() A2A_ENVELOPE (5 Szenarien), apply() PAL (4 Szenarien), RuntimePlaceholders (3 Szenarien)

---

## 3. Viz-Bash-Hardcode #248

### Problem
`scripts/lib/viz.py` hatte hardcoded `"Bash"` (capital B) als Terminal-Tool-Name — Opencode-Agenten crashten weil Opencode `"bash"` (lowercase) erwartet.

### Lösung
`_PROVIDER_TERMINAL_TOOL`-Dictionary in `viz.py`:
| Provider | Terminal Tool |
|----------|--------------|
| claude | `Bash` |
| gemini | `code_execution` |
| opencode | `bash` |
| continue | `None` (kein Terminal-Tool) |
| copilot | `None` |

Zusätzlich: `_get_terminal_tool()` liest aus `config/provider-tools.yaml` (falls vorhanden), fallback auf Hardcoded-Map.
Case-insensitive Lookup für Provider-Namen.

### Gemini/Antigravity-Probleme
MCP-Tools werden in Gemini nicht supported → `_GEMINI_VIZ_BLOCK` als file-based Logging graceful degradation.

---

## 4. Provider-Awareness in sync-Pipeline

### Problem
`scripts/lib/agents.py` hatte `provider: str = "Claude"` als Default — andere Provider (Opencode, Gemini) bekamen falsche Defaults.

### Lösung
- `sync_agents_for_provider()`: Provider-wird explizit übergeben (kein Hardcoded-Default mehr)
- Provider-spezifische Frontmatter-Felder: `model`, `memory`, `permission_mode` via `provider-config`
- Provider-Whitelist für Tools via `config/provider-tools.yaml`
- PAL-Delegation-Syntax wird jetzt für ALLE Provider angewendet (nicht nur Claude)

---

## 5. Orchestrator-Guard Hook

### Neu: `hooks/1-generic/orchestrator-guard.sh`
PreToolUse-Hook (enabled_by_default: false) — blockiert direkte Worker-Aufrufe aus dem Hauptchat.

**Logik:**
1. Parsed Tool-Call aus stdin (JSON)
2. Erlaubt `task()`/`Agent()`/`Task()` Aufrufe nur wenn:
   - `AGENT_NAME=orchestrator` (Orchestrator-Kontext)
   - Oder Subagent ∈ {orchestrator, git, agent-meta-manager, feedback, documenter} (Dispatch-Ausnahmen)
3. Alle anderen Worker-Aufrufe → Exit 2 mit Blockierungs-Meldung

### Neu: `rules/1-generic/use-orchestrator.md`
Subagent Invocation Policy: Hauptchat darf nur orchestrator aufrufen, nie direkt Worker.
4 Dispatch-Ausnahmen dokumentiert + Anti-Recursion-Guard.

### Neu im Orchesterator-Template
`agents/1-generic/orchestrator.md` — Delegate-First Guard bei Line 59:
> **Delegate-First Guard:** Bei Intent 'Code ändern' → SOFORT an `developer` delegieren.

---

## 6. Bug-Klassifikation bug-feature-analyzer

### Erkenntnis
bug-feature-analyzer klassifizierte oft als "Feature" was User als "Bug" empfindet (#289, #272, #253).

### Entscheidung
User-Entscheidung ist immer ausschlaggebend. Der Analyzer liefert eine Einordnung, der User entscheidet.

---

## 7. Dateien (neu/geändert)

| Datei | Status | Zweck |
|-------|--------|-------|
| `scripts/lib/a2a.py` | **NEU** | A2AEnvelope-Klasse (Phase 0) |
| `tests/test_a2a.py` | **NEU** | 31 A2A-Tests |
| `tests/test_delegation_syntax.py` | **NEU** | 19 PAL-Tests |
| `scripts/lib/delegation_syntax.py` | GEÄNDERT | build_handoff() + A2A_ENVELOPE |
| `scripts/lib/config.py` | GEÄNDERT | Runtime-Whitelist in substitute() |
| `scripts/lib/viz.py` | GEÄNDERT | Provider-spezifischer Terminal-Tool |
| `scripts/lib/agents.py` | GEÄNDERT | Provider statt hardcoded "Claude" |
| `config/delegation-syntax.yaml` | GEÄNDERT | handoff:-Blöcke für 5 Provider |
| `config/role-defaults.yaml` | GEÄNDERT | bugfix-Pipeline erweitert |
| `hooks/1-generic/orchestrator-guard.sh` | **NEU** | PreToolUse Hook |
| `rules/1-generic/use-orchestrator.md` | **NEU** | Subagent Invocation Policy |
| `agents/1-generic/orchestrator.md` | GEÄNDERT | Delegate-First Guard |
| `README.md`, `docs/testing/manual-test-scenarios.md` | GEÄNDERT | Versionen aktualisiert |
| `tests/unit/`, `tests/integration/`, `.github/workflows/tests.yml` | GEÄNDERT | Test-Suite |

## 8. Offene Follow-ups

- #289 Phase 2-4 (Return-Standard, Retry/Timeout, Context-Management) — für A2A-Protokoll
- Orchestrator-Template muss `{{PAL_HANDOFF}}` nutzen (im Template, nicht nur in PAL-Engine)
- 12 Bugs in diesem Branch gefixt, nicht gepusht
