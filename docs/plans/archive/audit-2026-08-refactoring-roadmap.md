# Refactoring-Roadmap — Deep-Dive-Audit 2026-08-31 (Issues #560–#602)

## STATUS

**done** — 43 Issues gruppiert/sequenziert, Entscheidungen getroffen, alle 10 Waves umgesetzt
(zuletzt Wave 10 / #579 — Issue-Sprach-Konfigurierbarkeit).
Waves liefen **sequenziell** (ein Feature-Branch nach dem anderen) — dieses Repo hat kein Worktree-Isolation
für Subagenten (`.claude/rules/no-worktree-isolation.md`), daher war echte Parallel-Entwicklung auf mehreren
Branches im selben Checkout nicht möglich.

## Entscheidungen (User, 2026-08-31)

- **#598 Release-Gates:** Allowlist jetzt umsetzen (Teil von Wave 3). Signatur/Checksumme → neues Backlog-Issue (P3, kein aktiver Wave-Slot).
- **#560 Override-Drift:** `extends:`+`patches:`-Mechanismus (Architektur-Umbau statt Quick-Fix) → Wave 2 Aufwand entsprechend hoch (L statt S).
- **#577 Admin-Token:** Bearer-only für `/api/*`, Breaking Change akzeptiert — Remote-Admin-UI-Nutzer müssen migrieren (Doku-Hinweis in `docs/howto/admin-ui-remote-access.md` nötig).
- **Rollout:** Alle Waves jetzt beauftragen, sequenziell nach diesem Plan.

## Kontext

5 parallele Audits (Hooks/Guards, Agenten-Definitionen, sync.py-Core, admin-server.py, Support-Module)
haben 43 Findings ergeben, alle als atomare GitHub-Issues gefiled (#560–#602). Dieser Plan gruppiert sie
in 10 Waves nach Risiko, Abhängigkeit und PR-Größe, sodass jede Wave in einer Session/einem PR bearbeitbar ist.

**Dedup-Fund:** #551 (bereits offen seit #542-Follow-up, `P3/refactor`) beschreibt exakt denselben Fix-Scope
wie #590/#591/#592/#602 (Tokenisierung der Destructive-Pattern-Erkennung in `orchestrator-guard.sh`).
Ursache aller vier ist dieselbe Zeilen-Scoping-Regex. → Wave 1 bearbeitet #551 zusammen mit #590/#591/#592/#602
in EINEM Tokenizer-Rewrite statt getrennt; #551s Priorität wird durch die konkreten Bypässe faktisch von
P3 auf P0/P1 angehoben.

---

## Wave 1 — Branch-Guard Tokenizer-Rewrite (P0, zuerst)

| Issue | Titel |
|---|---|
| #551 | refactor: tokenize orchestrator-guard destructive patterns (pre-existing, jetzt Leit-Issue) |
| #590 | force-push via `+`-refspec nicht erkannt |
| #591 | `git -c key=val` bypasst Mutation-Scan + RCE via `core.pager` |
| #592 | Command-Substitution/`xargs` bypassen Scan |
| #602 | False-Positives auf harmlose Befehle (Substring-Match ohne Tokenisierung) |

**Ansatz:** Ein Tokenizer-Rewrite der Destructive-Gate-Logik in `orchestrator-guard.sh`, der (a) echte git-Statements
korrekt erkennt (behebt #590/#591 Miss-Detection), (b) Scans auf erkannte git-Statements beschränkt statt global auf
den Roh-String (behebt #602 False-Positives), (c) `+`-Refspecs und `-c key=val` korrekt konsumiert.
**#592 (Command-Substitution) wird NICHT vollständig gefixt** — bewusst als 4. dokumentierte Grenze in
`.claude/rules/branch-guard.md` ergänzt (Präzedenzfall: #551 dokumentiert dieselbe Art Rest-Limitation für
Subcommand+Flag im selben Text-Argument). Ein vollständiger Shell-Parser wäre unverhältnismäßig aufwändig
für ein Konventions-Tool, keine harte Sicherheitsgrenze.
**Agent:** `senior-developer` (Sicherheits-kritisch, hohe Test-Sorgfalt nötig). **Aufwand:** L.
**Vorher:** #551-Body lesen (enthält bereits Risiko-Analyse aus #542-Audit).

---

## Wave 2 — Agenten-Definitionen: Sicherheitskritisch (P0)

| Issue | Titel |
|---|---|
| #562 | Prompt-Injection-Abwehr fehlt framework-weit |
| #560 | Layer-Override-Drift (developer.md-Overrides veraltet) |

Unabhängig voneinander, parallel bearbeitbar. #562: neuer wiederverwendbarer Snippet-Baustein
(`<constraints>`-Zusatz) in alle Rollen mit WebFetch/Sources-Zugriff. #560: **Fix-Ansatz ist offene Frage
— siehe unten** (Quick-Fix vs. Architektur-Änderung).
**Agent:** `developer` (#562, Template-Änderung), `senior-developer` (#560, falls Architektur-Ansatz gewählt wird).
**Aufwand:** M (#562), S–L je nach Ansatz (#560).

---

## Wave 3 — Hook-Härtung (übrige Findings)

| Issue | Titel |
|---|---|
| #593 | Block-Meldungen auf stdout statt stderr |
| #594 | Synchroner Testlauf blockiert jeden Push |
| #595 | Fail-open bei fehlendem python3/graphify |
| #596 | Credential-Leak im Audit-Log |
| #597 | Keine Log-Rotation |
| #598 | release-gates/ führt jede .sh ungeprüft aus |
| #599 | GRAPHIFY_BIN ungeprüft |
| #600 | artifact-freshness.sh mtime unzuverlässig |
| #601 | Hook-Hygiene-Bundle (quoting, set -e, Dedup, +x) |

Alle in `.claude/hooks/*`, unabhängig, guter Batch für einen "Hook-Hardening"-PR. **#598: Fix-Ansatz ist
offene Frage** (Allowlist vs. Signatur). Reihenfolge innerhalb der Wave beliebig.
**Agent:** `developer`. **Aufwand:** M (gesamte Wave als ein PR).

---

## Wave 4 — Admin-Server: Tests zuerst (P1)

| Issue | Titel |
|---|---|
| #569 | Keine Tests für `_verify_token`/`_check_origin` |
| #588 | Keine Tests für Origin-Header-Edge-Case |
| #577 | Token als Query-Param leakbar |
| #581 | Interne Exception-Messages an Client geleakt |
| #584 | `sys.path` wächst unbegrenzt |
| #585 | `_read_body` ohne Größenlimit (DoS) |
| #587 | `consistency-check.py`-Pfad bricht im Submodul-Modus |
| #589 | Permissions + TZ-Bundle |

**Reihenfolge zwingend:** #569/#588 (Tests) **vor** Wave 5 (God-Object-Split) — sonst läuft der Split ohne
Regressions-Schutz auf den Auth-Kontrollen. #577: **Fix-Ansatz ist offene Frage** (Breaking Change möglich).
Rest unabhängig, ein Batch-PR.
**Agent:** `tester` (#569/#588), `developer` (Rest). **Aufwand:** M.

---

## Wave 5 — Admin-Server: God-Object-Split (P1, NACH Wave 4)

| Issue | Titel |
|---|---|
| #572 | `AdminRequestHandler` (~3450 Zeilen) in Service-Klassen aufteilen |

Eigener dedizierter Slot, kein Bundling. Hohe Blast-Radius (4881-Zeilen-Datei). Voraussetzung: Wave 4
abgeschlossen (Tests als Sicherheitsnetz).
**Agent:** `senior-developer` oder `principal-developer` (Größe/Risiko rechtfertigt Eskalationsstufe).
**Aufwand:** XL.

---

## Wave 6 — sync.py-Core: God-Module-Split (P1)

| Issue | Titel |
|---|---|
| #565 | Deferred-Import-Zyklus entwirren (zuerst — Voraussetzung für sauberen Split) |
| #561 | `agents.py` (2094 Z.) aufteilen |
| #563 | `main()`-Dispatcher (930 Z.) refactoren |

Reihenfolge: #565 zuerst (entkoppelt agents/config/context, macht #561 erst sauber möglich), dann #561,
dann #563 (kann parallel zu #561 laufen, da unabhängiger Funktions-Scope). Nach jedem Schritt volle
Testsuite + `sync.py --validate`.
**Agent:** `senior-developer`/`principal-developer`. **Aufwand:** XL (Kern-Infrastruktur, alle Sync-Pfade betroffen).

---

## Wave 7 — sync.py-Core: Kleinere Refactors (P2)

| Issue | Titel |
|---|---|
| #566 | `build_variables` (502 Z.) dekomponieren |
| #568 | `except: pass` durch spezifische Exceptions ersetzen |
| #571 | YAML-/Frontmatter-Parsing zentralisieren |
| #574 | `SyncLog.info` umbenennen (44 noqa) |
| #578 | Provider-Pfad-Auflösung zentralisieren |

Kann nach oder parallel zu Wave 6 laufen (geringeres Risiko, unabhängige Funktionen). Ein Batch-PR.
**Agent:** `developer`. **Aufwand:** M.

---

## Wave 8 — Support-Module: Persistenz-Robustheit (P2)

| Issue | Titel |
|---|---|
| #573 | Atomarer Write-Helper (zuerst — wird von #576/#580 mitgenutzt) |
| #576 | Checkpoint-Parse-Crash bei korrupter Datei |
| #580 | Cache-Race bei parallelem Zugriff |
| #582 | Backup-Timestamp-Kollision |
| #583 | Backup schluckt Restore-Fehler still |
| #586 | Secrets/Isolation/DRY-Bundle |

Reihenfolge: #573 zuerst (liefert `io.py`-Helper `atomic_write`), #576/#580 nutzen ihn direkt mit. Rest unabhängig.
**Agent:** `developer`. **Aufwand:** M.

---

## Wave 9 — Agenten-Definitionen: Konsistenz (P2/P3)

| Issue | Titel |
|---|---|
| #564 | 3-Tier- vs. 4-Tier-Doku-Widerspruch (principal-developer) |
| #567 | Verwaiste `</output>`-Tags in 40 Templates |
| #570 | Template-Generationen vereinheitlichen (Domain-Reviewer) |
| #575 | Tool-Least-Privilege + Längen-Bundle |

Unabhängig, niedriges Risiko, guter "Template-Cleanup"-Batch-PR.
**Agent:** `developer`. **Aufwand:** S–M.

---

## Wave 10 — Framework-Design: Issue-Sprach-Konfigurierbarkeit (P3)

| Issue | Titel |
|---|---|
| #579 | Issue-Sprache/-Defaults projekt-konfigurierbar machen |

Eigenständige Design-Entscheidung + Umsetzung (`conventions.issue-language` in `project.yaml`,
Default `english`, `feedback.md` liest den Wert; `meta-feedback.md` bleibt fest Englisch).
**Agent:** `agent-meta-manager` oder `developer`. **Aufwand:** M.

---

## Offene Fragen (aufgelöst / zur Klärung)

**Aufgelöst (Recherche, keine Wertentscheidung nötig):**
- #551-Dedup → siehe oben, Wave 1 bündelt.
- #592 Command-Substitution-Fix → als dokumentierte Grenze behandeln (Präzedenzfall #551), nicht voll fixen.

**Geklärt (User-Entscheidung 2026-08-31):** siehe Abschnitt "Entscheidungen" oben — alle vier offenen Fragen sind aufgelöst.

## ARTIFACTS

- Diese Datei: `docs/plans/archive/audit-2026-08-refactoring-roadmap.md`
- Quell-Issues: `Popoboxxo/agent-meta#551`, `#560–#602`
