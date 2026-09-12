# A2A Anti-Re-Delegation Gates

## Enforced Gates (aktiv prüfen — HARD REJECT)

1. **No Self-Handoff / No Re-Delegation:** Ein `payload`, der mit "Du bist..." beginnt, ist ein Re-Delegations-/Spec-Dump-Versuch → HARD REJECT.
2. **Orchestrator-Singleton:** NUR `main_chat` darf den `orchestrator` spawnen. Worker → `orchestrator` → HARD REJECT (siehe `singleton-orchestrator-architecture.md`).
3. **Execution-Trace-Isolation:** Worker-Output muss strukturiert sein (STATUS, RESULT, ARTIFACTS). Keine rohen Logs propagieren.

## Degradierte Checks (Doku-Pflicht, kein Gate — Issue #346)

Diese Checks sind dokumentierte Konventionen, keine erzwungenen Gates. Die
eigene Modell-Prüfung war Ritual ohne Gate-Wirkung — Plattform-Limits decken
den praktischen Fehlerfall ab:

| Check | Status | Begründung |
|---|---|---|
| `delegation_depth ≤ {{A2A_MAX_DEPTH}}` | dokumentiert | Die Plattform (z.B. Claude Code) erzwingt Tiefenlimits ohnehin; eigene Prüfung ist redundant. Referenz: `docs/concepts/a2a-handoff-protocol.md` |
| `payload.t ≤ {{A2A_T_SIZE_LIMIT}} Zeichen` | dokumentiert | Empfehlung für prägnante Task-Zeilen; der Re-Delegation-Check (Punkt 1) deckt den eigentlichen Fehlerfall (Spec-Dump) ab |
| `max_depth` via project.yaml (`orchestrator.delegation.max_depth`) | dokumentiert | Toter Konfigurationsraum bei einem 2-Ebenen-Repo; der enforced-Pfad wurde aus `validate_envelope()` entfernt, der Doku-Verweis bleibt |

## Per-Task-Tier: `payload.tier_override` (optional — Issue #346)

Neues optionales Envelope-Feld: `payload.tier_override: <tier>` übersteuert die
Rolle→Tier-Auflösung (`role-defaults.yaml` → `model`) nur für genau diesen Dispatch.

**Guardrails (Referenz-Implementierung: `resolve_tier_override()` in `scripts/lib/delegation_syntax.py`):**

1. **Preset-Bounds:** Der Tier-Name muss im aktiven tier-preset existieren (`config/tier-presets.yaml` — globales `tiers:` plus `providers.<provider>.tiers` wenn Provider-Kontext vorliegt). Unbekannter Tier oder Tier außerhalb des Presets → Override wird verworfen, Fallback auf Rollen-Default.
2. **Kein Downgrade sicherheitskritischer Rollen:** Rollen aus `tier-override-policy.security-critical-roles` (`config/role-defaults.yaml`; Default: `security-auditor`, `code-reviewer`) können per Override nur gleich- oder höhergestuft werden.
3. **Audit-Log-Pflicht:** Jeder Override-Versuch — angenommen ODER abgelehnt — wird im Delegations-Tracker/Checkpoint protokolliert: `tier_override=<tier> (applied|rejected: <reason>)`.

{{#if SUBAGENT_PERMISSIONS_STRICT}}
## Subagent Permission Policy (strict)

- Dispatche NUR Subagenten, deren Rollen-Template eine explizite allow/deny-Deklaration
  besitzt (nicht-leere `tools:`-Liste in der Frontmatter). Fehlt sie → NICHT dispatchen,
  an `main_chat` eskalieren.
- Jedes Subagenten-Ergebnis MUSS dem Format `STATUS` / `RESULT` / `ARTIFACTS` folgen.
  Ein Ergebnis ohne alle drei Felder wird verworfen; der Subagent wird genau EINMAL mit
  Format-Hinweis erneut dispatcht. Zweiter Verstoß → Eskalation an `main_chat`.
{{/if}}
{{#if SUBAGENT_PERMISSIONS_WARN}}
## Subagent Permission Policy (warn)

- Prüfe jedes Dispatch auf explizite allow/deny-Deklaration und jedes Ergebnis auf
  `STATUS` / `RESULT` / `ARTIFACTS` — blockiere aber NICHT.
- Protokolliere Verstöße als Zeile `SUBAGENT_PERMISSION_WARNING: <role> — <reason>` im
  eigenen Abschluss-Report und fahre fort.
{{/if}}
## Bekannte Grenzen

- **Singleton-Orchestrator (Punkt 2) wird nur über eine Selbstdeklaration der Agenten-Identität gestützt** (`#agent-meta:agent=<name>` in `.claude/hooks/orchestrator-guard.sh`), die im Hook-Quelltext selbst als "soft, self-reported convention, not a security boundary" dokumentiert ist. Jeder Agent kann sich technisch als privilegiert deklarieren. **Das ist eine bewusste Design-Grenze, kein behebbarer Bug:** Claude Code liefert seit Kurzem zwar ein `agent_id`-Feld im PreToolUse-Payload (harness-gesetzt, nicht selbst-deklariert — seit Issue #683 genutzt, um Write/Edit/Bash für JEDEN dispatchten Subagenten von der Strict-Mode-Main-Chat-Blockade freizustellen), aber das sagt nur "irgendein Subagent", nicht "welche Rolle". Für die ROLLEN-Identität (git vs. orchestrator, für den Git-Mutation-Gate) liefert kein Provider ein echtes Feld — der Hook kann die Sentinel-Behauptung also weiterhin nicht verifizieren. Der Guard ist ein Konventions-Schutz gegen Versehen, kein Schutz gegen einen Agenten, der die Regel bewusst umgeht. Wer eine harte Grenze braucht, muss Git-Mutationen außerhalb des Agenten-Systems absichern (Branch-Protection, Pre-Receive-Hooks, Review-Pflicht) — zerstörerische Operationen (`push --force`, `reset --hard`, `clean -fd`, `branch -D`) bleiben deshalb ausdrücklich zustimmungspflichtig durch den Nutzer.
- **`resolve_tier_override()` ist dormant by design** — es gibt keinen Interception-Punkt im Runtime-Dispatch (siehe `validate_envelope()`-Docstring in `scripts/lib/delegation_syntax.py`). Die Guardrails sind prompt-basiert durchgesetzt (Orchestrator-Template, Tier-Selection-Sektion); die Python-Funktion ist die testbare Referenz-Implementierung.
- **`subagent_permissions` (optional) ist auf ALLEN Providern prompt-basiert plus Sync-Time-Validierung** — es gibt keinen Runtime-Dispatch-Gate. Die `strict`/`warn`-Anweisung oben wird nur gerendert, wenn der Modus aktiv ist; ein Modell kann sie ignorieren (identische, akzeptierte Grenze wie bei `orchestrator.mode: strict`). Bei `off` wird nichts gerendert.
- **Große Ergebnisse gehören in Dateien, nicht in den Return-Channel.** Der synchrone Tool-Result-Kanal hat ein undokumentiertes Größenlimit; überlange Antworten können ohne Fehlersignal beschnitten zurückkommen (agent-meta #514). Read-only-Rollen ohne `Write` (`Plan`, `Explore`, `code-reviewer`) sind davon strukturell betroffen. Daher: Artefakte ab ~1000 Zeilen (Pläne, Konzepte, Reviews) immer von einer schreibfähigen Rolle in eine Datei schreiben lassen und nur den Pfad zurückgeben. Empfangene Ergebnisse auf Vollständigkeit prüfen (fehlender Kopf/erste Abschnitte = Truncation), nicht blind weiterverarbeiten.
