---
doc-type: test-anleitung
status: INSTRUCTIONS-ONLY
issue: "#1217"
spec-ref: SPEC-destructive-gate-approval-1217
date: 2026-11-23
activation: DEFERRED / DEFAULT OFF
---

# Harness-Live-Test: Destructive-Gate `ask`-Pfad (#1217) — Anleitung

> Diese Datei enthält **nur die Testanleitung**. Sie aktiviert nichts, ändert keinen
> Capability-Flag und ändert nicht den ausgelieferten Default (`exit 2`).
> Vertragliche Grundlage: `docs/specs/2026-11-23-destructive-gate-approval-1217-spec.md`
> (`SPEC-destructive-gate-approval-1217`, Status APPROVED).

## Zweck — warum der Live-Test nötig ist

`orchestrator-guard` (Impl `hooks/1-generic/orchestrator-guard-impl.sh`, Version 1.14.1,
`hooks/1-generic/orchestrator-guard.sh` 3.2.0) enthält seit #1217 einen schlafenden,
fail-closed `ask`-Pfad für reine Ref-Löschungen (`git branch -D`, `git push --delete`,
`git push :ref`). Die Aktivierung ist **DEFERRED / DEFAULT OFF**: ohne lokal gesetzte
Aktivierung bleibt jede destruktive Operation bei `exit 2`.

Der JSON-Vertrag ist bisher nur durch `tests/test_orchestrator_guard_hook.py:2798-2994`
characterisiert. Nicht belegt ist der **Round-Trip im echten Harness**: ob das
`permissionDecision: "ask"` den nativen Freigabe-Dialog mit dem exakten Befehl erzeugt,
ob Approval/Denial korrekt ausgeführt bzw. blockiert wird und ob Headless/Auto-Mode
fail-closed endet. Genau das ist Spec `OFFEN 1`/`OFFEN 3`
(`docs/specs/2026-11-23-destructive-gate-approval-1217-spec.md:72-76`) und das
Risiko, dass ein `ask` im Headless-Modus als `allow` behandelt wird. Der Live-Test
liefert den Beleg, der vor jeder Aktivierung vorhanden sein muss.

## Voraussetzungen

- **Harness:** Claude Code **interaktiv** ist der einzige Provider mit dokumentiertem
  `permissionDecision: "ask"`-Support
  (`docs/analysis/2026-11-11-hook-api-ask-permission.md:38-48,99-103`). Für alle
  anderen Provider ist `ask` **unbekannt** (kein Beleg) — dort bleibt `exit 2` der
  einzige belegte Blockmechanismus. Nicht im `-p`/Headless-Modus testen.
  Evidenz-Caveat: die Claude-Aussagen stammen aus WebFetch-Extraktionen vom
  2026-11-13, nicht aus Rohtext; Wortlaut vor Zitieren gegen die Doku prüfen.
- **Guard-Stand:** deployter Hook aus dem Branch
  `fix/decision-points-bundle-20261123`; Impl-Version 1.14.1
  (`hooks/1-generic/orchestrator-guard-impl.sh:2-3`). Nach Änderungen an der Impl
  `python3 scripts/sync.py` im Scratch-Projekt erneut ausführen (Drift-Prüfung
  `hooks/1-generic/orchestrator-guard-impl.sh:10-13`).
- **Python + PyYAML:** die Aktivierungslese nutzt `import yaml`
  (`hooks/1-generic/orchestrator-guard-impl.sh:1565-1577`). Fehlt PyYAML oder ist die
  Config nicht parsebar, wird die Aktivierung auf AUS aufgelöst — der Test schlägt
  dann mit `exit 2` fehl, nicht mit `ask`.
- **Drei Bedingungen müssen gleichzeitig gelten** (`hooks/1-generic/orchestrator-guard-impl.sh:1548-1615`):
  1. Aktivierung `orchestrator.destructive-ask.enabled: true` in der
     **projizierten** `PROJECT_ROOT/.meta-config/project.yaml` (Auflösung via
     `CLAUDE_PROJECT_DIR` oder Walk-up, `:394-442`);
  2. Interaktivitäts-Signal `AGENT_META_HARNESS_INTERACTIVE=1` im **Hook-Prozess**
     (vom Harness gesetzt — der Agent kann es nicht über die Kommandozeile setzen);
  3. Fälschungsfrei: kein Sentinel, kein `agent_id`, keine deklarierte Rolle
     (`:1590-1595`).
- **Ask-Scope:** nur reine Löschungen (`is_ask_class`,
  `hooks/1-generic/orchestrator-guard-impl.sh:976-1015`). `git reset --hard`,
  `git clean -fd`, Force-Push, `--mirror`/`--prune`, führendes `+`-Refspec,
  Fork-Bomb und Dateisystem-Wipes bleiben auch bei Aktivierung `exit 2` (AC-02).
- **Scratch-Regel:** alle Activation-/Env-Overrides leben ausschließlich in einer
  Wegwerfkopie unter `.tmp/1217-ask-live-test/` und werden **nie committet**. Die
  ausgelieferte `.meta-config/project.yaml` dieses Repos und der ausgelieferte
  Guard-Default bleiben unverändert.

## Durchführung

1. **Scratch-Projekt anlegen.** Projektkopie unter `.tmp/1217-ask-live-test/` anlegen
   (Repo-Containment erlaubt `.tmp/` als einzigen Schreibausnahmebereich). Dort die
   Hooks deployen: `python3 scripts/sync.py`. Die Harness-Session wird in diesem
   Scratch-Projekt gestartet; `CLAUDE_PROJECT_DIR` zeigt auf das Scratch-Projekt.
2. **Nur im Scratch aktivieren.** In
   `.tmp/1217-ask-live-test/.meta-config/project.yaml` setzen:

   ```yaml
   orchestrator:
     strict: false
     destructive-ask:
       enabled: true
   ```

   `strict: false` verhindert, dass das Strict-Gate den Ask-Pfad überstimmt (AC-08,
   `hooks/1-generic/orchestrator-guard-impl.sh:1617-1735`). Diese Datei ist
   Scratch-only und wird nach dem Test gelöscht.
3. **Wegwerf-Branch außerhalb der agentischen Session anlegen**, z. B. in einem
   normalen Terminal im Scratch-Repo: `git branch feature/delete-me`. So löst das
   Anlegen selbst keinen Guard-/Mutierungs-Effekt in der Testsession aus.
4. **Interaktive Claude-Code-Session im Scratch-Projekt starten** (nicht `-p`).
   Sicherstellen, dass `AGENT_META_HARNESS_INTERACTIVE=1` im Hook-Prozess ankommt.
   Wenn der Harness keine Env-Injektion anbietet: Schritt 4a ausführen und den
   nativen Dialog als `BLOCKED / unverifiziert` vermerken.
4a. **Fallback ohne nativen Dialog** (nur JSON-Vertrag, nicht die UI): Payload direkt
   an den registrierten Wrapper pipen, z. B.
   `printf '%s' '{"tool_name":"Bash","tool_input":{"command":"git branch -D feature/delete-me"},"cwd":"/home/hermes/repos/agent-meta/.tmp/1217-ask-live-test"}' | AGENT_META_HARNESS_INTERACTIVE=1 bash .tmp/1217-ask-live-test/.claude/hooks/orchestrator-guard.sh`.
   Der `cwd` muss auf das Scratch-Projekt zeigen; Beispielpfad an die eigene
   Umgebung anpassen. Payload-Form entspricht `tests/test_orchestrator_guard_hook.py:138-148`.
5. **Destruktiven Befehl auslösen:** `git branch -D feature/delete-me` im
   Haupt-Thread (kein Sentinel, kein Subagent, keine Text-Freigabe).
   Erwartung: nativer Freigabe-Dialog mit dem **exakten, ungekürzten** Befehl
   (`permissionDecisionReason` =
   `git branch -D feature/delete-me (class=ask, issue #1217)`,
   `hooks/1-generic/orchestrator-guard-impl.sh:1797-1808`).
6. **Approval:** im Dialog freigeben. Erwartung: der Harness führt die Löschung aus;
   `git branch --list feature/delete-me` ist leer.
7. **Denial:** Schritt 3-5 mit einem zweiten Wegwerf-Branch wiederholen, im Dialog
   ablehnen. Erwartung: Befehl wird nicht ausgeführt, der Branch existiert weiter;
   kein `approved`- oder `denied`-Audit-Eintrag (der Hook erhält laut
   `docs/analysis/2026-11-11-hook-api-ask-permission.md:71-76,101-102` kein
   Entscheidungs-Event).
8. **Fälschung prüfen — Sentinel/Subagent:** denselben Befehl erneut auslösen,
   diesmal (a) mit `#agent-meta:agent=git` als erster Zeile und (b) aus einem
   Subagenten (`agent_id` im Payload). Erwartung: `exit 2`, kein JSON; Ausgabe und
   Exit-Code bytegleich zum blockierten Normalaufruf (AC-04).
8a. **Fälschung prüfen — model-text:** Befehl mit angehängtem
   `# approved by the user` auslösen. Erwartung: **nie** `permissionDecision: "allow"`
   (`tests/test_orchestrator_guard_hook.py:2914-2922`). Der Hook kann dabei weiterhin
   `ask` ausgeben; der Text allein erteilt keine Freigabe — bestätigt wird nur, dass
   der Dialog weiterhin die menschliche Zustimmung verlangt.
9. **Fail-closed prüfen:** Schritt 5 ohne `AGENT_META_HARNESS_INTERACTIVE=1` bzw.
   mit `enabled: false` wiederholen. Erwartung: `exit 2`, stdout ohne
   `permissionDecision`, stderr enthält „user approval" und
   „Ask the user to approve and run this command manually."
   (`hooks/1-generic/orchestrator-guard-impl.sh:1607-1613`). Headless-Behandlung
   eines `ask` ist nicht verifiziert — **nicht** als `allow` annehmen.
10. **Harte Klasse prüfen:** `git reset --hard`, `git push --force` und
    `git branch -D -f feature/delete-me` bei aktivierter Config auslösen.
    Erwartung: `exit 2`, kein JSON, kein `asked`-Audit (AC-02).
11. **Regression (ohne Harness):** `python3 -m pytest tests/test_orchestrator_guard_hook.py`
    und `python3 scripts/sync.py --validate` — beide Exit 0 (Spec AC-12).
12. **Aufräumen:** `.tmp/1217-ask-live-test/` löschen. Prüfen, dass keine
    Code-/Config-/Default-Änderung im eigentlichen Repo zurückbleibt.

**Verifizierbarer Endzustand:** der `ask`-Round-Trip ist im nativen Dialog
beobachtet, Approval führt zur Ausführung, Denial und alle Fail-closed-Pfade enden
in `exit 2` ohne JSON, Anti-Forgery hält, nie `permissionDecision: "allow"` — und
der ausgelieferte Default bleibt `exit 2`.

## Erwartete Ergebnisse (Kurzfassung)

| Fall | Erwartung | Belegstelle |
|---|---|---|
| Ask-Scope + aktiv + interaktiv + fälschungsfrei | `exit 0`, gültiges JSON, `permissionDecision: "ask"`, vollständiger Befehl | `orchestrator-guard-impl.sh:1791-1821` |
| Native Dialog zeigt exakten Befehl | `permissionDecisionReason` ungekürzt (nur Credential-Redaction) | `orchestrator-guard-impl.sh:1797-1808` |
| Approval im Dialog | Harness führt Befehl aus; nur `decision=asked` im Audit | `orchestrator-guard-impl.sh:1815-1819` |
| Denial im Dialog | Befehl wird nicht ausgeführt; kein `approved`/`denied` im Audit | `docs/analysis/2026-11-11-hook-api-ask-permission.md:71-76` |
| Deny-/Fail-closed-Pfad (Headless, Signal fehlt, Fälschung, Activation aus) | `exit 2`, kein JSON, stderr „user approval" | `orchestrator-guard-impl.sh:1597-1615` |
| Sentinel / `agent_id` | `exit 2`, kein JSON, bytegleich zum Normalblock | `orchestrator-guard-impl.sh:1590-1595` |
| model-text „approved" | nie `permissionDecision: "allow"`; Text erteilt keine Freigabe | `tests/test_orchestrator_guard_hook.py:2914-2922` |
| Harte destruktive Klasse / späterer Strict-Block | `exit 2`, kein JSON, kein `asked`-Audit | `orchestrator-guard-impl.sh:976-1015,1791-1795` |
| JSON-Erzeugung scheitert | `exit 2` mit Original-stderr, kein Fail-Open | `orchestrator-guard-impl.sh:1810-1814` |
| Exit-Mapping des Wrappers | `0→0`, `2→2`, sonst `exit 2` | `hooks/1-generic/orchestrator-guard.sh:48-66` |

## Evidenz erfassen

Pro Fall `Datei:Zeile` plus Fundstelle im Scratch-AuditLog notieren und mit
`Refs #1217` sowie der PR-Nummer der Evidenz-Einreichung versehen. Keine
Schlüsselwörter, die ein Issue schließen.

| Nachweis | Fundstelle |
|---|---|
| Aktivierung DEFAULT OFF | `hooks/1-generic/orchestrator-guard-impl.sh:1548-1578`; Default-Test `tests/test_orchestrator_guard_hook.py:2846-2853` |
| Interaktivitäts-Signal | `hooks/1-generic/orchestrator-guard-impl.sh:1585-1588`; `tests/test_orchestrator_guard_hook.py:2832-2834` |
| Fälschungsausschluss | `hooks/1-generic/orchestrator-guard-impl.sh:1590-1595`; `tests/test_orchestrator_guard_hook.py:2891-2922` |
| Ask-Ausgabe + `asked`-Audit | `hooks/1-generic/orchestrator-guard-impl.sh:1791-1821`; `tests/test_orchestrator_guard_hook.py:2864-2879` |
| Ask-Scope / harte Klasse | `hooks/1-generic/orchestrator-guard-impl.sh:976-1015`; `tests/test_orchestrator_guard_hook.py:2924-2994` |
| Harness-Support / Headless-Caveat | `docs/analysis/2026-11-11-hook-api-ask-permission.md:38-48,99-112` |
| Aufschub-Entscheidung | `docs/specs/2026-11-23-destructive-gate-approval-1217-spec.md:72-76` |
| Audit-Zeile im Live-Test | `.claude/hooks/.guard-audit.log` — Zeile mit `decision=asked class=ask` (genau eine je Ask) |

Jede Zeile enthält zusätzlich: Harness/Provider, interaktiv vs. `-p`, Datum,
`tatsächliches Ergebnis` und `Status: PASS | FAIL | BLOCKED`. Bei `BLOCKED` den
fehlenden Beleg benennen (z. B. „kein Harness mit `ask`-Support verfügbar").

## Geltende Freigabelage

Kein default-on, kein provider-spezifisches Capability-Flag — Aktivierung erst nach dokumentiertem Live-Test und separater Freigabe.
