# Kontext-Messung: Bytes und Token je Artefakt

> Status: Messung Bytes real, Token **approximiert (Bytes / 4)** — Tokenizer-Verhältnisse **UNVERIFIED**
> **AC-05 OFFEN (kein Tokenizer verfügbar)** — `tiktoken` ist installierbar, lädt aber das Vokabular (`cl100k_base`) nur über `openaipublic.blob.core.windows.net`; der Proxy liefert 403. Keine Bytes/Token-Werte erfunden.
> Bezug: #964, SPEC-CONTEXT-PROFILES-2026-10-11 (AC-05, K-a…K-c), Studie `2026-10-11-context-budget-provider-study.md`

## Methode

- Bytes: `python3 scripts/sync.py --context-report --json` (rendert in den tmp-sink, Bericht unter `context-report/`; `measure_artifacts`, `scripts/lib/context_report.py`). Projekt: agent-meta (Self-Hosting), Stand 2026-10-12.
- Token: `tokens_est = bytes // 4` (Studie U-10). Die Studie enthält **keine** gemessenen Tokenizer-Verhältnisse.
- Echte Verhältnisse: `tests/manual/measure_tokens.py` (optional `tiktoken`, nur manuell, nicht im Framework). Ohne Tokenizer endet das Skript mit Hinweis (Exit 0; mit `--strict` Exit 3). Versuch am 2026-10-12: `pip install tiktoken` gelingt, `tiktoken.get_encoding("cl100k_base")` scheitert am Vokabular-Download (Proxy 403) → Skript meldet „kein Tokenizer". Alle Token-Werte unten sind UNVERIFIED.

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

## Abweichungen und Erklärung

- **Gemini Rules 60,601 B vs. 17,880 B (Studie/gemini-cli.md):** Self-Hosting setzt `rules-preset: lazy` (`.meta-config/project.yaml`). Claude hat dadurch nur 11 always-on Rules in `.claude/rules` (8,708 B auf Platte; Report 8,552 B), der Rest läuft als Skills. Gemini hat keinen Skill-Kanal und rendert alle 35 Rules nach `.gemini/rules` (59,905 B auf Platte; Report 60,601 B, Differenz ≈ 700 B = Stand-Drift zwischen Messung und aktuellem Render, **UNVERIFIED**). Die Studie misst ein Konsumentenprojekt mit 19 Rules (17,880 B). Die Rules sind für Gemini zudem inert (von keinem Harness gelesen), zählen aber in „always-loaded".
- **Claude Rules 8,552 B (Self-Hosting) vs. Spec 18.3 KB:** gleiche Ursache — `lazy`-Preset im Self-Hosting (11 statt 19 Rules always-on); die Spec misst das `full`-Profil eines Konsumentenprojekts (19 Rules, 17.9–18.3 KB). Nicht vergleichbar.

## Einordnung K-a…K-c

- K-a: Orchestrator §12 ist ein 3-Zeilen-Pointer (188 B), kein 8.5-KB-Inline — kein Kompaktierungshebel (Studie §9).
- K-b/K-c: CLAUDE.md ist klein (hier 4,461 B); Claude ignoriert AGENTS.md, wenn CLAUDE.md existiert. Last liegt bei Rules, Roster und Orchestrator.

## Offene Punkte

- **AC-05 OFFEN:** Tokenizer-Lauf auf einem Rechner mit Zugriff auf das Vokabular (Netz/Cache): `pip install tiktoken`, dann `python3 tests/manual/measure_tokens.py --strict --files CLAUDE.md AGENTS.md` (Exit 3 = kein Tokenizer) und die Spalte „Token" mit echten Werten ersetzen — **UNVERIFIED** bis dahin.
- Verhältnis Bytes/Token ist modell-/tokenizer-abhängig; `tiktoken cl100k_base` ist nicht der Tokenizer von Claude/Gemini/Codex/Kimi und liefert nur einen Anhaltswert.
