---
spec-id: SPEC-destructive-gate-approval-1217
status: APPROVED
approval: "User, 2026-11-23, generelle Freigabe (Bug-Welle)"
---

# Destructive-Gate: user-approval path (#1217) — Spec
> Status: APPROVED (User, 2026-11-23, generelle Freigabe)

## Problem / Ziel / Nicht-Ziele

**Problem (Issue #1217, wörtlich):**
> "the `orchestrator-guard` destructive-operation gate (#516) hard-blocks `git branch -D` and `git push origin --delete` with exit 2 and gives the user no way to approve the operation inside the session. When the user has **explicitly asked** for exactly this operation in the chat, the agent cannot carry it out."
> "A user-approved destructive operation should be possible **without** the agent being able to forge the approval."
> "Return `permissionDecision: \"ask\"` instead of a hard `exit 2` for destructive git operations. Claude Code then shows its native confirmation dialog with the exact command, and the user approves or denies in the UI. The approval is given by the human in the harness, not by text the model could fabricate."

**Gemessener Ist-Zustand (Branch `fix/bug-wave2-20261123`, `.git/HEAD` = `refs/heads/fix/bug-wave2-20261123`):**

| Messung | Ergebnis |
|---|---|
| `hooks/1-generic/orchestrator-guard-impl.sh:1479-1488` | unverändert harter `exit 2`, Meldung `:1486` „Ask the user to approve and run this command manually." |
| `permissionDecision\|hookSpecificOutput\|permission_mode\|headless` in `hooks/` | **0 Treffer** (Grep, kein ask-Pfad, keine Headless-Erkennung) |
| `is_destructive` `orchestrator-guard-impl.sh:976`, Scan-Ausgabe `:1425` | nur `destructive\|mutation\|none`, keine Unterklasse |
| Audit `hook_audit_log_append` `:459-463`, `:573-577` | heute nur Rollen-/Elevation-Ereignisse, kein `asked` |
| `config/ai-providers.yaml` / `scripts/lib/hooks.py:12,291-353` | Capability-/Config-Backing vorhanden (`provider_has_capability`), kein ask-Capability-Eintrag |

**Ziel:** Für die im Ask-Scope liegenden destruktiven Git-Operationen (`git branch -D`, `git push origin --delete` / `:<ref>`; Approvals für weitere Operationen sind OFFEN, s. §Offene Fragen) einen Harness-`ask`-Pfad mit dem **vollständigen, unveränderten** Befehl bereitstellen, den ausschließlich der Mensch im Harness freigibt. Alle übrigen Fälle bleiben `exit 2`.

**Nicht-Ziele:** Keine Änderung des Tokenizers/der Klassifikationslogik über eine Ask-Unterklasse hinaus; keine Auto-Freigabe; keine Rollen-/Sentinel-basierte Freigabe; kein Eingriff in den Harness-Auto-Mode-Classifier; kein `approved`/`denied`-Audit ohne belegtes Harness-Signal; keine Implementierung in diesem Schritt.

**Sicherheitsinvarianten (nicht verhandelbar):**
1. **FAIL-CLOSED im Headless-Modus.** Ohne positiv festgestellten interaktiven Nutzer gilt unverändert `exit 2`. Wird Interaktivität nicht zweifelsfrei erkannt, wird blockiert.
2. **Keine Fälschung der Freigabe.** Ein Agent, Subagent, Sentinel (`#agent-meta:agent=…`) oder eine vom Modell geschriebene Textzeile darf niemals eine Freigabe erzeugen oder vortäuschen. Die Freigabe kommt ausschließlich über den User-/main_chat-Kanal des Harness, nicht aus model-generiertem Inhalt. Der Hook gibt nie `permissionDecision: "allow"` für ein destruktives Verdikt aus.
3. **Keine Auto-Freigabe.** `ask` ist immer opt-in; der Default bleibt `exit 2`. Eine Freigabe ohne explizite menschliche Bestätigung im Harness existiert nicht.
4. **Sentinel-Unabhängigkeit.** Destructive-Gate-Ausgabe und Exit-Code sind bytegleich mit und ohne Sentinel; ein Sentinel kann weder `ask` noch Freigabe auslösen. Der ask-Pfad erzeugt keinen Bypass: ein späteres bzw. strengeres Block-Verdikt (Strict-/Mutations-Gate, AC-08) gewinnt immer über `ask` und führt zu `exit 2`. Fail-closed bleibt damit unverändert erhalten.

## Interface Contracts

| Datei:Symbol | Signatur / Typ | Rolle & Fehlerpfad |
|---|---|---|
| `hooks/1-generic/orchestrator-guard-impl.sh:1479-1488` (Destructive-Gate) | `if [ "$TOOL_NAME" = "Bash" ] && [ "$_GIT_SCAN" = "destructive" ]; then … fi` | Heute: Stderr + `exit 2`. Soll: Verzweigung — Ask-Scope + positiv interaktiv + Activation an → `ask`-JSON (stdout, `exit 0`); jeder andere Fall → unverändert `exit 2` mit dem heutigen Stderr-Text („user approval"). Kein `exit 2` zusammen mit JSON (exit 2 übersteuert JSON). |
| `hooks/1-generic/orchestrator-guard-impl.sh:976` `is_destructive(subcmd, args, config_values, stdin_bodies=None) -> bool`; `:1425` `_GIT_SCAN_RAW` | Python-Scan liefert `category scope bom` | Soll: zusätzliche Ask-Unterklasse pro `destructive`-Verdikt; Default bei Unklarheit `hard`. Multi-Statement: strengste Klasse gewinnt. Tokenizer-Semantik bleibt unverändert (Regression #542/#551/#590/#591/#602). |
| `hooks/1-generic/orchestrator-guard.sh:48-67` (Exit-Status-Mapping) | `0 → 0`, `2 → 2`, sonst `exit 2` (fail closed) | Bleibt unverändert. `ask` nutzt `exit 0`; kein neuer Exit-Code, kein Fail-Open-Pfad. |
| `hooks/1-generic/lib/hook_common.sh:hook_audit_log_append` (Aufruf `:459-463`, `:573-577`) | `hook_audit_log_append <logfile> <line>`; Ziel `PROJECT_ROOT/.claude/hooks/.guard-audit.log` | Soll: genau eine `decision=asked`-Zeile je ausgegebener ask-Entscheidung. Keine `approved`/`denied`-Zeilen ohne Harness-Signal. `asked` belegt nur das Angebot eines Prompts, keine Ausführung. |
| `config/ai-providers.yaml` + `scripts/lib/hooks.py:12,291-353` | config-getriebene Capability (`provider_has_capability`), beim Sync in den Hook gebacken | Soll: Ask-Activation als config-key, **Default AUS**; provider-agnostisch über Capability-Key, nie `if provider == "…"`. Ungesyncte Quellkopie (Platzhalter literal) → `exit 2`. |
| `rules/1-generic/branch-guard.md:18` (`## Bekannte Grenzen`), `rules/1-generic/a2a-delegation-gates.md:115` (`## Bekannte Grenzen`) | Dokumentation | Soll: beschreibt Ask-Pfad, Headless-fail-closed, Sentinel-/Modell-Fälschungsausschluss, `asked` ≠ Ausführung, Default aus. |
| `tests/test_orchestrator_guard_hook.py:126` `_run_hook(payload: dict) -> CompletedProcess`, `:138` `_bash_payload(command: str) -> dict`; Charakterisierung `:473`, `:631`, `:1179` | pytest | Neue Fälle für Ask/Deny/Headless/Fälschung; bestehende destructive-Sentinel-Tests bleiben für die Hart-Klasse grün. |

**Ask-Ausgabe (Vertrag):** `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"<vollständiger Befehl + Klasse>"}}`, `exit 0`. Der Befehl wird unverändert (kein Umschreiben, keine 200-Zeichen-Kürzung wie `:1482`), als gültiges JSON (geparst) und mit redigierten Credentials ausgegeben. Erzeugung scheitert → `exit 2` + Stderr-Text. Die Harness-UI zeigt den exakten Befehl; Approval/Denial erfolgt durch den Menschen, nicht durch Hook-Logik.

## Datenfluss

`PreToolUse-Payload (Bash)` → Tokenizer-Scan (`:1425`, Ask-Unterklasse, Default `hard`) → Leading-BOM-Gate (`:1473-1477`, unberührt) → Destructive-Gate (`:1479-1488`): Ask-Scope + Activation an + interaktiv positiv → `asked`-Audit + ask-JSON → Harness-Dialog → Mensch bestätigt/verweigert → Harness führt Befehl aus oder nicht. Jeder andere Fall → `exit 2` (Stderr), kein JSON. Danach unverändert Strict-/Mutations-Gate und Sentinel-Auswertung; ask wird erst nach allen blockierenden Gates emittiert (ein späterer Block gewinnt). Keine Persistenz außer dem Audit-Log.

## Acceptance Criteria

1. **AC-01 (Ask):** Given `git branch -D x` / `git push origin --delete x`, Activation an und positiv interaktiver Harness, When der Hook läuft, Then `exit 0` und stdout ist gültiges JSON mit `permissionDecision == "ask"` und dem vollständigen, unveränderten Befehl in `permissionDecisionReason`.
2. **AC-02 (Hart bleibt hart):** Given `git reset --hard`, `git clean -fd`, Force-Push oder Fork-Bombe, When der Hook läuft (auch mit Activation an), Then `exit 2`, Stderr enthält „user approval", stdout ohne `permissionDecision`.
3. **AC-03 (Headless fail closed):** Given Activation an, aber keine positiv festgestellte Interaktivität (Headless/unbekannt/ Feld fehlt), When `git branch -D x`, Then `exit 2`, kein JSON, keine Freigabe.
4. **AC-04 (Keine Fälschung):** Given `#agent-meta:agent=git` / `orchestrator` / Allowlist-Rolle oder eine model-geschriebene „approved"-Zeile, When `git branch -D x` läuft, Then Ausgabe/Exit code identisch zum Aufruf ohne diese Zeile; nie `permissionDecision: "allow"`, nie Freigabe durch Text.
5. **AC-05 (Default aus):** Given ausgelieferter Default (Activation aus bzw. Platzhalter literal), When destruktiver Befehl, Then `exit 2` wie vor der Änderung.
6. **AC-06 (Audit):** Given AC-01, Then genau eine `decision=asked`-Zeile in `.claude/hooks/.guard-audit.log`; keine `approved`/`denied`-Zeile; `asked` belegt keine Ausführung (Doku).
7. **AC-07 (JSON-Fehlerpfad):** Given `ask`-JSON nicht erzeugbar, When der Hook läuft, Then `exit 2` mit heutigem Stderr-Text — nie Fail-Open.
8. **AC-08 (Gate-Reihenfolge):** Given ein ask-Klassen-Befehl, den zugleich das Strict-/Mutations-Gate blockt, When der Hook läuft, Then `exit 2`, kein JSON, kein `asked`-Audit.
9. **AC-09 (Tokenizer-Regression):** Given die Fälle #542/#551/#590/#591/#602, When der Hook läuft, Then Klassifikation `destructive`/„kein Verdikt" unverändert; nur die Unterklasse kommt hinzu.
10. **AC-10 (Provider-Agnostik):** Given der Diff, When nach `provider ==`/Providernamen im Hook-/Sync-Code gesucht wird, Then kein neuer Treffer; Activation rein config-/capability-getrieben.
11. **AC-11 (Doku):** Given der Merge, Then nennen beide Regeldateien (`:18`, `:115`) den Ask-Pfad, Headless-fail-closed, Fälschungsausschluss und `asked` ≠ Ausführung.
12. **AC-12 (Validierung):** Given der Branch, When `python3 -m pytest tests/test_orchestrator_guard_hook.py` und `python3 scripts/sync.py --validate` laufen, Then beide Exit 0; Charakterisierungstests `:473`, `:631`, `:1179` grün.

## Offene Fragen + Risiken

- **OFFEN 1 (aufschiebbares Implementierungsdetail, kein blockierendes Product Decision):** exakter Aktivierungszeitpunkt des `ask`-Protokolls. Der Freigabe-Mechanismus selbst ist vom Issue vorgegeben (`permissionDecision: "ask"`) und wird unverändert als Vertrag übernommen — hier bleibt keine Produktentscheidung offen. Die Aktivierung bleibt Default AUS, bis ein dokumentierter Harness-Live-Test bestätigt, dass `ask` interaktiv erscheint und headless/Auto-Mode in deny/`exit 2` endet. Das ausgelieferte Verhalten ist unverändert `exit 2`; der Live-Test ist eine eigene, spätere Änderung. Kein eigener Protocol-Entwurf, keine Auto-Aktivierung.
- **OFFEN 2:** genaue Ask-Unterklassen-Menge (nur die zwei genannten Löschoperationen, oder auch `worktree remove --force`, `stash drop/clear`, `branch -f`?). Der Vertrag erlaubt nur explizit freigegebene Operationen, Default `hard`. Eine Ausweitung ist eine eigene, freizugebende Entscheidung — hier nicht erfunden.
- **OFFEN 3:** konkretes Harness-Signal für „positiv interaktiv" (Payload-Feld vs. Umgebungsmerkmal). Bis zur Messung im Live-Test gilt: Zweifel → `exit 2`.
- **OFFEN 4:** Audit von `approved`/`denied` benötigt ein belegtes Harness-Event; ohne Nachweis nur `asked`.
- **Risiko:** Ein `ask` im Headless-Modus könnte vom Harness als `allow` behandelt werden — durch Default AUS, positives Interaktiv-Merkmal und Live-Test-Gate (OFFEN 1) eingedämmt; bis dahin bleibt `exit 2` die einzige ausgelieferte Verhalten.
- **Risiko:** Prompt-Müdigkeit bei häufigen Prompts; keine Messung vorhanden.
- **Hinweis:** Ein älterer Entwurf `docs/specs/2026-11-11-guard-destructive-ask-spec.md` ist DRAFT (Freigabe 2026-11-14 zurückgezogen); diese Spec ist die freigegebene, knappe Fassung für die Bug-Welle und ersetzt jenen Entwurf für #1217.

## Trace-Anker: spec-id: SPEC-destructive-gate-approval-1217
