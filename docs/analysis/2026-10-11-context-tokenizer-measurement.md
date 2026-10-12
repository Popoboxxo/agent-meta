# Kontext-Messung: Bytes und Token je Artefakt

> Status: Messung Bytes real, Token **approximiert (Bytes / 4)** — Tokenizer-Verhältnisse **UNVERIFIED**
> Bezug: #964, SPEC-CONTEXT-PROFILES-2026-10-11 (AC-05, K-a…K-c), Studie `2026-10-11-context-budget-provider-study.md`

## Methode

- Bytes: `python3 scripts/sync.py --context-report --json` (rendert in den tmp-sink, Bericht unter `context-report/`; `measure_artifacts`, `scripts/lib/context_report.py`). Projekt: agent-meta (Self-Hosting), Stand 2026-10-12.
- Token: `tokens_est = bytes // 4` (Studie U-10). Die Studie enthält **keine** gemessenen Tokenizer-Verhältnisse.
- Echte Verhältnisse: `tests/manual/measure_tokens.py` (optional `tiktoken`, nur manuell, nicht im Framework). Ohne Tokenizer endet das Skript mit Hinweis (Exit 0). Bisher **nicht ausgeführt** (kein Tokenizer lokal verfügbar) → alle Token-Werte unten sind UNVERIFIED.

## Messtabelle (agent-meta, Bytes real, Token ≈ Bytes/4 UNVERIFIED)

| Provider | Artefakt | Bytes | Token (approx., UNVERIFIED) |
|---|---|---:|---:|
| Claude | Einstiegsdatei (CLAUDE.md) | 4,461 | 1,115 |
| Claude | Rules | 8,552 | 2,132 |
| Claude | Orchestrator | 88,847 | 22,211 |
| Claude | Harness-Roster (alle Agenten) | 555,675 | 138,895 |
| Claude | always-loaded (Summe) | 568,688 | 142,142 |
| Opencode | Einstiegsdatei (AGENTS.md) | 13,872 | 3,468 |
| Opencode | Orchestrator | 88,542 | 22,135 |
| Opencode | Harness-Roster | 550,136 | 137,510 |
| Opencode | always-loaded (Summe) | 564,008 | 141,002 |
| Gemini | Einstiegsdatei (AGENTS.md) | 13,872 | 3,468 |
| Gemini | Rules (`.gemini/rules`, von keinem Harness gelesen) | 60,601 | 15,150 |
| Gemini | Orchestrator | 88,685 | 22,171 |
| Gemini | always-loaded (Summe) | 74,473 | 18,603 |

Hinweis: Die Bytes stammen aus dem Self-Hosting-Lauf dieses Repos (Provider Claude, Opencode, Gemini); die Studie misst andere Projektstände (z. B. AGENTS.md 25,560 B bei Codex) — Werte sind nicht direkt vergleichbar. Die Zeile „always-loaded" ist die vom Report definierte Summe, nicht das, was ein Harness real pro Turn sendet (Studie: gemessene Main-Turns pro Provider).

## Einordnung K-a…K-c

- K-a: Orchestrator §12 ist ein 3-Zeilen-Pointer (188 B), kein 8.5-KB-Inline — kein Kompaktierungshebel (Studie §9).
- K-b/K-c: CLAUDE.md ist klein (hier 4,461 B); Claude ignoriert AGENTS.md, wenn CLAUDE.md existiert. Last liegt bei Rules, Roster und Orchestrator.

## Offene Punkte

- Tokenizer-Lauf: `pip install tiktoken` lokal, dann `python3 tests/manual/measure_tokens.py --files CLAUDE.md AGENTS.md` und die Spalte „Token" mit echten Werten ersetzen — **UNVERIFIED** bis dahin.
- Verhältnis Bytes/Token ist modell-/tokenizer-abhängig; `tiktoken cl100k_base` ist nicht der Tokenizer von Claude/Gemini/Codex/Kimi und liefert nur einen Anhaltswert.
