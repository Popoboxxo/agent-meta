---
spec-id: SPEC-GUARD-DESTRUCTIVE-ASK-2026-11-11
title: ask-Approval-Pfad für destruktive Git-Operationen im Orchestrator-Guard
status: DRAFT
approval-withdrawn: 2026-11-14 (User: parked as DRAFT, not to be implemented yet)
issue: "#1217"
plan: docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md (Task 1, Task 9)
datum: 2026-11-13 (Entwurf); 2026-11-14 (Entscheidungen E1-E3 eingearbeitet; Freigabe zurückgezogen)
autor: concept-specifier (Subagent, Auftrag via orchestrator)
related-spec: SPEC-GUARD-ROLE-ATTRIBUTION-2026-11-11 (#1210)
---

# ask-Approval-Pfad für destruktive Git-Operationen — Spec

> **Status: DRAFT.** Approval withdrawn 2026-11-14: parked as DRAFT, not to be implemented yet.
> Die Entscheidungen E1-E3 des Nutzers (AskUserQuestion, 2026-11-14)
> sind in §3.4, §4, §6-§10, §13 und §14 eingearbeitet; Änderungsprotokoll am Ende. Kein Reviewer-Lauf.
> Diese Datei enthält Contracts und Akzeptanzkriterien, keine Implementierung. Neue Contract-Teile sind mit
> „Soll“ gekennzeichnet.
> Trace-Anker: `spec-id: SPEC-GUARD-DESTRUCTIVE-ASK-2026-11-11`.
>
> **Issue:** #1217 — statt hartem `exit 2` soll für (Teile der) destruktive(n) Git-Operationen ein
> `ask`-Pfad existieren, damit der Nutzer im Harness-Prompt zustimmen kann. Das Issue behauptet (laut
> Aufrufer-Zusammenfassung, Issue-Text nicht eingesehen), das Repo nutze `ask` bereits über
> `docs/agent-templates/hooks/review-policy-gate.sh`. **Nicht belegt:** der Plan hat gemessen, dass diese
> Datei in `9aa0e0c0` nicht existiert (Plan Zeile 78); in diesem Worktree wurde das nicht erneut geprüft
> (Hooks-Verzeichnis `hooks/1-generic` enthält keine Treffer für `permissionDecision`/`hookSpecificOutput`,
> Grep 2026-11-13). Es gibt also keinen Repo-Präzedenzfall für `ask`.
> **Klasse:** M (Verhaltensänderung im Guard). **Messstand:** Worktree `wt-phase-d1`, 2026-11-13; Zeilenanker
> unten an diesem Stand nachgemessen.

## 1. Problem / Ziel / Nicht-Ziele

### 1.1 Problem

Das Destructive-Gate blockt **jede** als destruktiv klassifizierte Operation hart mit `exit 2` und
Stderr-Text „requires explicit user approval … Ask the user to approve and run this command manually"
(`hooks/1-generic/orchestrator-guard-impl.sh:1383-1392`; Bedingung `:1384`, `exit 2` `:1391`). Der Nutzer muss
den Befehl danach selbst per `!` im Chat ausführen (Plan Entscheidung 12, Zeile 33). Das Gate gilt unabhängig
vom Sentinel (Kommentar `:1383`; Hook-Kopf `:79-84`).

Der Klassifikator `is_destructive` (`:895`) ist ein Tokenizer-Ergebnis ohne Abstufung: er liefert nur
`True`/`False`. Alle folgenden Fälle enden gleich in `exit 2`: Force-Push (jeder Branch, `:909-930`),
Remote-Ref-Löschung (`:920`), `reset --hard` (`:931-932`), `clean -f` (`:933-936`), `branch -D`/`-f`
(`:941-950`), Whole-Tree-Checkout (`:951-969`), `stash drop/clear` (`:937-938`), Dateisystem (`rm -rf` auf
gefährliches Ziel, `is_fs_destructive`, `:1262-1271`), Fork-Bombe (`fork_bomb`, `:1283-1284`, Scope
`forkbomb` `:1325`).

Das Gate kennt **keine** Branch-Semantik: „Force-Push auf `main`" ist heute nicht von einem Force-Push auf
einen Feature-Branch unterscheidbar (`:909-912` prüft nur Flags, nicht das Ziel); ebenso kennt es keinen
„PR-gemergten Branch". Der Plan (Zeile 143) setzt diese Unterscheidungen voraus, sie sind **nicht
implementiert** (siehe OQ-1, §4).

### 1.2 Ziel

Eine konfigurierbare Teilmenge der destruktiven Operationen (**ask-Klasse**, Default „Aufräum-Set“, §4,
Entscheidung E1) läuft nicht mehr in `exit 2`, sondern liefert dem Harness eine `ask`-Entscheidung (JSON,
`exit 0`) mit dem **vollständigen** Befehl, damit der Nutzer genau diesen Befehl im Harness-Prompt freigeben
kann. Alle übrigen Operationen (**immer-hart**) behalten `exit 2`. Providerunterschiede über Capability-Flag,
nie über Providername. Headless bleibt fail closed. Der ask-Pfad wird gebaut, ist aber **per Default AUS**
(`exit 2` wie heute), bis ein dokumentierter Live-Test ihn freigibt (E2, §6).

### 1.3 Nicht-Ziele

- Keine Lockerung der immer-harten Klassen (§4).
- Keine Änderung der Rollenbindung (#1210); Sentinel bleibt für das Destructive-Gate wirkungslos (§8).
- Kein Eingriff in den Claude-Code-Auto-Mode-Classifier (außerhalb des Repos, §11).
- Kein Audit von `approved`/`denied` ohne belegtes Signal (§7).
- Keine Änderung der Tokenizer-/Parse-Logik über die Unterklassen-Ausgabe hinaus (AC-6).
- Keine Implementierung (Plan Task 9 nach Freigabe).

## 2. Evidenz

### 2.1 Was belegt ist

| Aussage | Beleg |
|---|---|
| `ask` ist für Claude Code interaktiv (PreToolUse) unterstützt; Form `hookSpecificOutput.permissionDecision: "ask"` + `permissionDecisionReason`, exit 0, JSON auf stdout | `docs/analysis/2026-11-11-hook-api-ask-permission.md` §3.1 (Extraktion eines Recherche-Agenten, WebFetch 2026-11-13, **kein Rohtext**) |
| Rangfolge mehrerer Hooks: deny > defer > ask > allow | derselbe Beleg, §3.1 |
| Exit 2 schlägt JSON: „Exit 2 blocks even when your hook prints JSON"; `ask` und exit 2 sind pro Aufruf nicht kombinierbar | analysis §3.2 (Extraktion) |
| Permission-Rules (deny/ask) gelten unabhängig vom Hook-Ergebnis | analysis §3.6 (Extraktion) |
| Im Repo gibt es keine Hook-JSON-Ausgabe: der Guard nutzt nur exit 0/2 + Stderr | Grep `permissionDecision\|hookSpecificOutput` in `hooks/1-generic`: keine Treffer (2026-11-13); Hook-Kommentar zu exit 2 `orchestrator-guard-impl.sh:45-49` laut analysis §3.2 |
| Im Hook wird `permission_mode` nirgends gelesen; kein Headless-Merkmal ausgewertet | Grep `permission_mode\|headless` (case-insens.) in `hooks/1-generic`: keine Treffer, 2026-11-13 |
| Audit-Mechanik: `hook_audit_log_append <logfile> <line>` (redigiert Credentials, 600-Rechte, Rotation, Best-Effort) | `hooks/1-generic/lib/hook_common.sh:251-289` (Funktion `:264`) |
| Audit-Aufruf heute nur für Sentinel-Elevation (`_AUDIT_ROLE` gesetzt), Log `$PROJECT_ROOT/.claude/hooks/.guard-audit.log`, Zeile `<ts> role=<r> cmd=<erste 200 Zeichen>` | `orchestrator-guard-impl.sh:482-501` (Pfad `:496`, Zeilenbau `:497-499`, Aufruf `:500`) |
| Keine Provider außer Claude hat belegtes `ask` | analysis §2 (Provider-Tabelle), §5 |

### 2.2 Reale Reibung (belegt in dieser Session)

(a) **Nutzer muss Befehl selbst tippen.** Der Guard liefert bei jeder destruktiven Operation „Ask the user to
approve and run this command manually" (`:1390`); die Projektregeln machen daraus „Assistent liefert den
fertigen Befehl, User führt ihn per `!` aus" (Plan Zeile 33, Entscheidung 12). Der Ablauf ist nicht
reproduzierbar belegt in einem Test, sondern Projektkonvention.

(b) **`git checkout -- <Datei>` wird hart geblockt (#516-Linie).** Am 2026-11-13 forderte das beim
Zurücksetzen einer generierten Datei (z. B. einer regenerierten Hash-Datei) den Nutzer auf, den Befehl per
`!` selbst auszuführen. Das ist der Anwendungsfall des Approval-Pfads: der Nutzer möchte **einen einzelnen,
exakten Befehl** im Harness-Prompt bestätigen statt ihn zu tippen. Wichtig zur Einordnung (nachgemessen):

- Der Single-Path-Restore `git checkout -- <path>` ist **nicht** im Destructive-Gate, sondern eine
  **Mutation**: `is_destructive` lässt „A single-path restore stay a mutation" (`:951-957`); Test pinnt das:
  `"git checkout -- path/file.txt"` ist „allowed WITH the git sentinel (not destructive)"
  (`tests/test_orchestrator_guard_hook.py:1687-1691`) und als Mutation klassifiziert (`:325`).
- Geblockt wird er über das **Mutations-Gate** für Aufrufer ohne `git`-Sentinel: `:1535`, Meldung für
  Subagenten `:1537`, für den Main-Chat `:1539`; Strict-Mode zusätzlich `:1505-1523`.
- Das Destructive-Gate trifft `checkout` erst bei Whole-Tree-Pathspecs (`git checkout -- '*'`, `.`, `./`,
  `:/`; `is_whole_tree_pathspec`, Aufruf `:968-969`; Tests `:1912-1918`) oder `-f`/`-B`.

**Konsequenz für diese Spec:** Die konkrete Reibung (b) wird durch einen `ask`-Pfad **im Destructive-Gate
allein nicht behoben**, solange `checkout -- <file>` Mutation bleibt; ein `ask` dort wäre ein zweiter,
neuer Pfad im **Mutations-Gate** (`:1535`) und damit Scope-Erweiterung von #1217. Das ist eine Nutzer-
Entscheidung (OQ-2). Hier nicht entschieden. Der Issue-Text wurde nicht eingesehen; ob #1217 das
Mutations-Gate meint, ist ungeprüft.

(c) **Tokenizer-Fragilität.** Fehlalarme auf gequoteten Text (Gate hält Text für einen Befehl) wurden mehrfach
behoben: #1226/#1229/#1232 (laut Aufrufer; Commit-Titel `b36184b5 fix: ignore quoted text of non-git
commands in push guard (#1232)` im Repo-Log sichtbar; #1226/#1229 in dieser Session nicht nachgeprüft).
Im Hook belegt: Tokenizer statt Raw-Regex für den Destructive-Gate (`:91-99`), Tests gegen Text-Fehlalarme
(`:539-558` #602, `:414-440` #542, Fork-Bombe-Text `:1396`, `:2177-2185`). Relevanz: ein **Fehlalarm** des
Klassifikators endet heute in `exit 2` (Nutzer muss tippen); als `ask` wäre er ein bestätigbarer Prompt.
Das senkt die Fehlalarm-Kosten **nur** für die ask-Klasse; für die immer-harte Klasse bleibt ein Fehlalarm
ein Hard Block (Risiko §12).

(d) Querverweis #1210-Spec (`docs/specs/2026-11-11-guard-role-attribution-spec.md` §2.2): Sentinel-/Classifier-
Reibung wird dort behandelt und hier **nicht** wiederholt.

## 3. Interface Contracts

Spec ist freigegeben (2026-11-14); alle Contracts sind „Soll“ (noch nicht implementiert). Der ask-Pfad ist
erst wirksam, wenn das Aktivierungs-Flag gesetzt ist (§3.4, §6). Ziel-Symbole für Plan Task 9.

### 3.1 Klassifikator-Ausgabe

| Aspekt | Festlegung |
|---|---|
| Ort | Python-Heredoc `_GIT_SCAN_SRC`, `is_destructive` (`orchestrator-guard-impl.sh:895`), Aggregation `:1292-1326`, Ausgabe `print(f'{category} {scope} {bom}')` `:1326` |
| Heute | `category ∈ {destructive, mutation, none}`; `scope ∈ {broad, narrow, forkbomb}`; Parse der Ausgabe `:1330ff` (Whitelist `broad\|narrow\|forkbomb` `:1353`) |
| Soll | Zusätzlich je `destructive`-Verdikt eine **Unterklasse** `hard` oder `ask` als **zusätzliches Feld** im Scan-Output (E3; kein Umbau der Scope-Werte). Default bei jedem unklassifizierbaren Fall: `hard` (fail closed). Der Scan liefert `ask` nur für Operationen, die laut §3.4 in der wirksamen ask-Liste stehen |
| Aggregation | Enthält ein Befehl mehrere Statements (`:1292`), gilt die **strengste** Unterklasse: eine `hard`-Operation macht den Gesamtbefehl `hard` (z. B. `git branch -D x && git reset --hard`) |
| Fork-Bombe, `is_fs_destructive` | immer `hard` (`:1262`, `:1284`) |
| Fehlerpfad | Scan-Fehler (RC ≠ 0, `:1330ff`) bleibt wie heute (fail closed, nicht Teil dieser Spec; Verhalten bei fehlendem `python3` laut `.claude/rules/branch-guard.md`: fail-closed, #595) |

### 3.2 Gate-Verzweigung

Ziel: `orchestrator-guard-impl.sh:1384-1392`.

| Unterklasse | Capability/Aktivierung `hook-ask-permission` (Arbeitsname) | Headless | Ausgabe | Exit |
|---|---|---|---|---|
| `hard` | beliebig | beliebig | Stderr-Text wie heute (`:1385-1390`) | 2 |
| `ask` | **aus / unbekannt / Platzhalter literal** (Default) | beliebig | wie `hard` (Fallback) | 2 |
| `ask` | an | headless oder nicht positiv interaktiv | wie `hard` (fail closed, §6) | 2 |
| `ask` | an | positiv interaktiv festgestellt | JSON nach §3.3 auf stdout | 0 |

Soll: `ask` wird **nach** allen anderen Gates (Strict-Mode, Mutations-Gate) ausgegeben, damit kein späterer
Block verschluckt wird (E3, §5).

Das Gate bleibt **vor** der Sentinel-Auswertung und gilt unabhängig von ihr (§8).

### 3.3 ask-Ausgabe (JSON)

Form laut analysis §3.1 (Extraktion, gegen Rohtext vor Implementierung prüfen):

```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"<Text>"}}
```

- Exit-Code **0**; **nichts** auf stderr mit exit 2 kombinieren (exit 2 würde das JSON übersteuern,
  analysis §3.2).
- `permissionDecisionReason` enthält den **vollständigen** Befehl (nicht auf 200 Zeichen gekürzt wie in
  `:1386`, `head -c 200`), die Klasse und die Operation in Klartext. Soll (E3): JSON-Escaping über einen
  `python3`-Helfer, nicht per `printf` (Ort der Hilfsfunktion in `hook_common.sh` in dieser Session nicht
  gemessen). Der Befehl wird unverändert und vollständig bis **2000 Zeichen** angezeigt; darüber wird gekürzt
  mit Hinweis „[gekürzt]“ und Angabe der Gesamtlänge. Credentials werden wie im Audit redigiert angezeigt.
- Der Befehl darf vor der Ausgabe **nicht** verändert/umgeschrieben werden (der Nutzer bestätigt exakt den
  Befehl, der ausgeführt wird).
- Fehlerpfad: kann das JSON nicht erzeugt werden (kein Interpreter, Escaping-Fehler) → `exit 2` mit dem
  heutigen Stderr-Text (fail closed).

### 3.4 Capability-Flag

- Soll: Neuer Eintrag in `config/ai-providers.yaml` (Nachbar von `hook-agent-id`, `:64`); Arbeitsname
  `hook-ask-permission`. Wert nur bei Claude überhaupt setzbar (Providerumfang E3). **Default AUS für alle
  Provider einschließlich Claude** (E2); das Setzen auf an für Claude ist eine eigene spätere Änderung nach
  bestandenem Live-Test (§6).
- Wird beim Sync in den Hook gebacken (Muster Platzhalter `{{AGENT_META_HOOK_AGENT_ID}}`,
  `orchestrator-guard-impl.sh:360`); ungesyncte Quellkopie (Platzhalter literal) verhält sich wie `false`
  (also `exit 2`).
- Keine Verzweigung nach Providername im Hook oder in `scripts/lib/` (Provider-Agnostik, CLAUDE.md).
- Ort der Backing-Logik (`scripts/lib/hooks.py`) in dieser Session **nicht** gemessen; Plan Task 9 misst.

**Konfigurierbare ask-Liste (Soll, E1):**

- Projekt-Config-Key, **Arbeitsname** `guard.ask-operations`: Liste von Operations-Bezeichnern. Genauer
  Key-Name, Ablageort in der Projekt-Config und Schema sind Umsetzungsdetail (Task 9 misst und legt fest;
  Arbeitsnamen der Bezeichner unten sind ebenfalls Arbeitsnamen).
- **Default** („Aufräum-Set“): `branch-delete` (`git branch -D`), `remote-ref-delete` (`git push origin
  --delete <b>` inkl. `:<b>`-Form), `worktree-remove-force` (`git worktree remove --force`).
- **Erlaubte Obermenge** (fest im Hook definiert, nicht per Config erweiterbar): Aufräum-Set plus
  `stash-drop-clear` (`git stash drop`/`clear`) und `branch-force-move` (`git branch -f`). Die Config darf nur
  Einträge aus dieser Obermenge aktivieren.
- **Nicht konfigurierbar** (immer `hard`): `reset --hard`, `clean -f`, `filter-branch`/`filter-repo`,
  Working-Tree-Wipe, `rm -rf` auf gefährliches Ziel, Force-Push (jeder Branch), Fork-Bombe, `update-ref -d`,
  `reflog`, `gc --prune=now`, `checkout -f`/`-B`, `switch -C`/`--discard-changes`, `push --mirror`/`--prune`.
- **Unbekannte oder nicht erlaubte Config-Einträge:** ignorieren, Sync-Warnung ausgeben, Verhalten bleibt
  `hard`. Die Auswertung ist fail closed: nicht lesbare/ungültige Config -> leere ask-Liste (alles `hard`).
- Die Config wird beim Sync in den Hook gebacken (analog Capability-Flag); eine ask-Entscheidung braucht
  zusätzlich Aktivierung (Flag an), §3.2.

### 3.5 Betroffene Stellen (Ziel-Symbole für Task 9)

| Datei | Stelle | Änderung |
|---|---|---|
| `hooks/1-generic/orchestrator-guard-impl.sh` | `:895-1005`, `:1292-1326` | Unterklasse ausgeben |
| `hooks/1-generic/orchestrator-guard-impl.sh` | `:1329-1360` | Parse der erweiterten Ausgabe |
| `hooks/1-generic/orchestrator-guard-impl.sh` | `:1383-1392` | Verzweigung §3.2, JSON §3.3 |
| `hooks/1-generic/orchestrator-guard-impl.sh` | `:496-500` | Audit-Zeile `asked` (§7) |
| `config/ai-providers.yaml` | neben `:64` | Capability-Flag (Default aus) |
| Projekt-Config / Sync (`scripts/lib/`, Ort in Task 9 messen) | — | `guard.ask-operations`, Validierung gegen Obermenge, Sync-Warnung (§3.4) |
| `docs/analysis/` | neue Datei (Name in Task 9) | Live-Test-Nachweis (§6) |
| `rules/1-generic/branch-guard.md`, `rules/1-generic/a2a-delegation-gates.md` | „Bekannte Grenzen" | Doku (Plan Zeile 293, 300) |
| `tests/test_orchestrator_guard_hook.py`, `tests/test_hook_drift.py` | — | Testmatrix §10 |

## 4. Klassen: immer-hart vs. ask-Klasse

Zuordnung entschieden am 2026-11-14 durch Nutzer (E1). Die Tabelle zeigt das heutige Verhalten (gemessen)
und die Soll-Klasse. Spalte „Soll-Klasse“: `hard` (nicht konfigurierbar), `ask-Default` (im Default-
Aufräum-Set, abschaltbar), `ask-optional` (nur per Config aus der erlaubten Obermenge aktivierbar, Default
`hard`). `ask` gilt jeweils nur bei aktivem Flag (§3.2), sonst `exit 2`.

| Operation | Heute (Anker) | Soll-Klasse | Ausgabe |
|---|---|---|---|
| `git reset --hard` | destructive `:931-932` | hard (nicht konfigurierbar) | exit 2 |
| `git clean -f…` | destructive `:933-936` | hard (nicht konfigurierbar) | exit 2 |
| `git filter-branch` / `filter-repo` | destructive `:939-940` | hard (nicht konfigurierbar) | exit 2 |
| Working-Tree-Wipe (`git checkout -- '*'`, `.`, `:/`; `git restore '*'`) | destructive `:951-969`, `:986-987` | hard (nicht konfigurierbar) | exit 2 |
| `rm -rf` auf gefährliches Ziel | destructive `:1262-1271` | hard (nicht konfigurierbar) | exit 2 |
| Fork-Bombe | destructive `:1283-1284` | hard (nicht konfigurierbar) | exit 2 |
| **Force-Push (jeder Branch)** | destructive `:909-930`; Ziel-Branch wird **nicht** geprüft | hard (nicht konfigurierbar); fail closed, solange keine Default-Branch-Erkennung existiert | exit 2 |
| `git branch -D <b>` | destructive `:941-950` | ask-Default (`branch-delete`); keine Unterscheidung merged/unmerged | ask (Flag an) sonst exit 2 |
| `git push origin --delete <b>` / `:<b>` | destructive `:920-927` | ask-Default (`remote-ref-delete`) | ask (Flag an) sonst exit 2 |
| `git push --mirror` / `--prune` | destructive `:920-927` | hard (nicht konfigurierbar) | exit 2 |
| `git worktree remove --force` | destructive `:970-1004` | ask-Default (`worktree-remove-force`) | ask (Flag an) sonst exit 2 |
| `git stash drop` / `clear` | destructive `:937-938` | ask-optional (`stash-drop-clear`), Default hard | exit 2 (Default) |
| `git branch -f` | destructive `:948` | ask-optional (`branch-force-move`), Default hard | exit 2 (Default) |
| `checkout -B`, `switch -C` | destructive `:965-967` | hard (nicht konfigurierbar) | exit 2 |
| `git checkout -f` / `switch --discard-changes` | destructive `:961-964` | hard (nicht konfigurierbar) | exit 2 |
| `git update-ref -d`, `reflog expire/delete`, `gc --prune=now`, RCE-Config-Keys | destructive `:970-1004`, `:900-905` | hard (nicht konfigurierbar) | exit 2 |
| **`git checkout -- <file>`** (Single-Path) | **kein** Destructive-Verdikt; **Mutation** `:951-957`, Test `:1691`; Block über `:1535` für Nicht-`git`-Rolle | **unverändert Mutation**; ask dort ist NICHT Teil von #1217 (E3) | heute exit 2 (Mutations-Gate, Meldung `:1537`/`:1539`) |

Regeln:

- Eine Operation gilt als ask-Klasse **nur**, wenn sie in der wirksamen `guard.ask-operations`-Liste steht
  und zur erlaubten Obermenge gehört (§3.4); Default für jede nicht genannte Operation ist `hard`.
- Der Test `test_destructive_ops_blocked_even_with_git_sentinel` (`:407`, Fälle `:398-406`) enthält
  `push --force`, `reset --hard`, `clean -fd`, `stash drop`, `stash clear`, `filter-branch`. Mit Default-
  Config (Aufräum-Set) bleiben **alle** diese Fälle `exit 2` (Force-Push, reset, clean, filter-branch hart;
  `stash drop/clear` nur per Config ask-fähig, Default hard) — der Test bleibt unverändert grün.
- Die Einstufung „Destructive-Gate = Security-Eigenschaft“ gilt für die `hard`-Klassen unverändert; die
  konfigurierbare ask-Klasse ist eine bewusste, bestätigbare Convention-boundary-Ausnahme (E3, §12, AC-10).

## 5. Datenfluss

```
PreToolUse-Payload (Bash)
  -> Tokenizer-Scan (_GIT_SCAN_SRC, :1292-1326)  -> category + scope (+ Unterklasse, neu)
  -> Leading-BOM-Gate (:1377)                     (unberührt)
  -> Destructive-Gate (:1384)
        hard                                -> Stderr + exit 2          (wie heute)
        ask + Flag aus/Platzhalter          -> Stderr + exit 2          (Fallback, Default)
        ask + Flag an + Headless/unbestimmt -> Stderr + exit 2          (fail closed, §6)
        ask + Flag an + interaktiv          -> merken (Ergebnis "ask pending"), weiter zu den Gates
  -> Strict-Mode (:1505) -> Mutations-Gate (:1535) -> jeder Block: exit 2
  -> erst danach, wenn kein Gate blockt: Audit "asked" -> JSON stdout -> exit 0
```

Soll (E3, Entscheidung zu OQ-10): `ask` wird **nach** allen anderen Gates (Strict-/Mutations-Gate)
ausgegeben. Ein späteres Block-Verdikt (exit 2) gewinnt; ein `ask` verschluckt keinen Block. Das Audit
`asked` entsteht erst bei der tatsächlichen Ausgabe des JSON.

Persistenz: nur Audit-Log (Append, §7). Das Flag entsteht beim Sync.

## 6. Headless

**Ziel:** Ohne interaktiven Nutzer darf `ask` niemals zu einer Freigabe führen; fail closed.

**Verifiziert (aus Repo):** Der Hook wertet heute weder `permission_mode` noch ein Headless-Merkmal aus
(Grep 2026-11-13, keine Treffer); es gibt keine Headless-Erkennung im Guard.

**Belegt nur als Extraktion (analysis §3.3, nicht Rohtext):** In einem Manual-Mode-`claude -p`-Lauf wird ein
Call, der eine Freigabe braucht, verweigert, sofern nichts ihn freigibt (PermissionRequest-Hook,
`--permission-prompt-tool`); `dontAsk` verweigert jeden Call, der sonst fragen würde. Daraus ist abgeleitet:
ein PreToolUse-`ask` endet headless wahrscheinlich als deny. **Das ist abgeleitet, nicht belegt.**

**Nicht verifiziert:**

- Verhalten eines PreToolUse-`ask` im `-p`-Modus, insbesondere unter Auto-Mode oder `bypassPermissions`.
  Wenn dort ein `ask` still als `allow` behandelt würde, wäre das ein Fail-open gegenüber heutigem `exit 2`
  (Risiko §12, deshalb Default aus bis Live-Test, E2).
- Welche Payload-Felder Headless zuverlässig anzeigen (`permission_mode` kommt laut analysis §3.5 im
  Payload vor; ob es `-p` unterscheidet: nicht verifiziert).

**Contract (Soll, Entscheidung E2 vom 2026-11-14):**

- Der ask-Pfad wird gebaut, ist aber **per Default AUS** (Capability-/Aktivierungs-Flag aus, `exit 2` wie
  heute), bis ein **dokumentierter Live-Test** bestätigt: (a) `ask` erscheint interaktiv im Harness,
  (b) Headless (`claude -p`) und Auto-Mode enden in deny/exit-2-Verhalten (nicht allow).
- Nachweis als Datei unter `docs/analysis/`. Erst danach wird der Default **per eigener Änderung** (eigener
  Task im Plan) auf an gestellt.
- Der Hook gibt `ask` **nur** aus, wenn er eine interaktive Lage **positiv** feststellen kann; im Zweifel
  (Feld fehlt, Wert unbekannt, Headless nicht ausschließbar) `exit 2`. Das konkrete Interaktiv-Merkmal
  (Payload-Feld `permission_mode`, Umgebungsvariable o. ä.) ist Umsetzungsdetail und wird durch den Live-Test
  (b) festgelegt; ohne positive Feststellung bleibt es bei `exit 2`.

## 7. Audit

- Heute: Audit-Zeilen entstehen nur bei Sentinel-Elevation (`_AUDIT_ROLE`, `:482-501`); das Destructive-Gate
  schreibt **kein** Audit.
- Entschieden am 2026-11-14 (vom Nutzer pauschal übernommen, E3): **nur `asked` auditieren**; kein
  `approved`/`denied`, kein `blocked`-Audit.
- **Soll:** bei jeder ausgegebenen `ask`-Entscheidung genau eine Zeile `asked` über
  `hook_audit_log_append "$_AUDIT_LOG" "<line>"` (`hook_common.sh:264`) in dieselbe Datei
  `.claude/hooks/.guard-audit.log` (Pfad `:496`). Zeilenform (Vorschlag):
  `<ts> decision=asked class=<Unterklasse> cmd=<erste 200 Zeichen, Tabs/Newlines ersetzt>`; Redaktion greift
  (Funktion redigiert Credentials, `:251-253`). Bei `exit 2` aus dem Destructive-Gate: kein Pflicht-Audit
  (heutiges Verhalten); `blocked`-Zeilen werden nicht geschrieben (E3).
- **`approved`/`denied` werden nicht geschrieben.** Bei `ask` entscheidet der Harness **nach** dem Hook; ob
  ein Hook die Nutzerentscheidung überhaupt sieht, ist **nicht verifiziert** (analysis §3.4, §6): es
  wurde kein „approved"-Event gefunden; PermissionRequest läuft *bevor* gefragt wird; PermissionDenied feuert
  nur im Auto-Mode und nicht bei manuellem Ablehnen oder PreToolUse-Block; PostToolUse läuft nur nach
  erfolgreichem Call (ein ausgeführter Befehl wäre ein indirekter Beleg für „approved", ein nicht
  ausgeführter nicht eindeutig für „denied"). Folge laut Plan Task 1 Step 2 (Zeile 144): Audit auf `asked`
  begrenzt, bis ein Signal belegt ist. Ein `approved`/`denied`-Audit braucht ein eigenes Design
  (PermissionRequest/PostToolUse-Hook, Korrelation über `tool_use_id`); das ist **nicht Teil dieser Spec**
  (OQ-4, entschieden E3).
- Die Zeile `asked` ist **kein** Nachweis einer Ausführung, nur dass dem Nutzer ein Prompt angeboten wurde;
  das muss die Doku aussprechen (AC-10).

## 8. Sentinel kann nie approven

- Das Destructive-Gate liegt vor und unabhängig von der Sentinel-Auswertung (`:1383`; Test
  `test_destructive_ops_blocked_even_with_git_sentinel` `:407`; `test_non_git_agent_cannot_use_fake_sentinel_for_destructive`
  `:565`; `test_auto_commit_destructive_gate_still_blocks_an_allowlisted_role` `:1002`).
- Contract (Soll, E3): Der Sentinel hat nie Wirkung. Ausgabe (hard/ask/JSON-Inhalt) und Exit-Code sind
  **bytegleich** mit und ohne `#agent-meta:agent=<rolle>`-Zeile (auch `git`, `orchestrator`, Allowlist-
  Rolle). Ein Sentinel kann weder eine `ask`-Klasse zu `allow` machen noch eine `hard`-Klasse zu `ask`.
- Ein Hook gibt **nie** `permissionDecision: "allow"` für ein Destructive-Verdikt aus (Allow würde die
  Rückfrage des Harness überspringen; nur `ask` oder exit 2).
- Die Freigabe kommt ausschließlich vom Nutzer im Harness. Das ist ein Eigenschaft der Ausgabe, kein
  Identitätsnachweis (Convention boundary, siehe §12).

## 9. Interaktion mit Entscheidung 12 (#946) und Mehrfach-Hook-Verhalten

### 9.1 Entscheidung 12 / #946

- Entscheidung 12 (Plan Zeilen 33, 37): blockiert der Guard (exit 2), liefert der Assistent den fertigen
  Befehl und der Nutzer führt ihn per `!` aus; der Phase-A-Löschpfad für Branches/Stash (#946) hängt vom
  Guard-Verhalten `exit 2` (`orchestrator-guard-impl.sh:1384-1392`) ab.
- Bis #1217 gemergt **und** der ask-Pfad nach bestandenem Live-Test (E2) aktiviert ist, gilt `exit 2` +
  `!`-Weg weiter (Plan Zeile 37). Der Phase-A-Löschpfad darf `ask` erst **nach Merge UND nach bestandenem
  Live-Test** nutzen (Plan Zeile 300; E3, Entscheidung zu OQ-7). Diese Spec ändert den Löschpfad nicht.
- Der Wortlaut von Entscheidung 12 wird dann in einem **eigenen Schritt** angepasst; das ist hier
  **nicht** Teil der Änderung.

### 9.2 Mehrfach-Hook-Rangfolge (analysis §3.1, §3.2 — Extraktion)

- Rangfolge deny > defer > ask > allow. Folge: ein weiterer Hook (Nutzer-/Projekt-Hooks, andere Guards)
  mit `deny` oder `exit 2` übersteuert unser `ask`; ein `allow` eines anderen Hooks hebt unser `ask` nicht
  auf.
- **exit 2 schlägt JSON:** gibt ein anderer Hook exit 2, ist unser `ask` wirkungslos. Gibt unser Hook JSON
  `ask` **und** exit 2 aus, zählt exit 2; deshalb §3.3 (ask nur mit exit 0).
- **Permission-Regeln gelten weiter:** `deny`/`ask`-Regeln der Harness-Konfiguration werden unabhängig vom
  Hook-Ergebnis ausgewertet (analysis §3.6). Ein Hook-`ask` kann eine `deny`-Regel nicht aufheben; eine
  `allow`-Regel hebt ein Hook-`ask` laut analysis nicht auf („don't bypass permission rules", genaue
  Auflösung von Rule-`allow` gegen Hook-`ask` nicht gesondert verifiziert).
- **Auto-Mode-Classifier:** Interaktion Hook-`ask` mit dem Classifier (kann er ein `ask` überstimmen oder
  verweigern?) ist **nicht verifiziert** (analysis §3.6, §6); wird vom Live-Test (E2, §6) abgedeckt.

## 10. Provider-Matrix (aus Task 1a)

Quelle: `docs/analysis/2026-11-11-hook-api-ask-permission.md` §2, §5. Alle Zeilen außer Claude: Beleg fehlt.

| Provider | `ask` | Headless | Verhalten der Guard |
|---|---|---|---|
| claude | ja (interaktiv, Extraktion; Live-Test ausstehend) | unbekannt/teilweise | Flag Default aus -> exit 2; `ask` erst nach Live-Test (E2) und nur positiv interaktiv |
| codex | unbekannt (Repo kennt nur `deny`, `docs/providers/codex.md:144`) | unbekannt | exit 2 |
| gemini | unbekannt (`docs/providers/gemini-cli.md:168`) | unbekannt | exit 2 |
| opencode | unbekannt (`docs/providers/opencode.md:172-173`, Plugin-Protokoll) | unbekannt | exit 2 |
| continue | unbekannt | unbekannt | exit 2 |
| copilot | unbekannt | unbekannt | exit 2 |
| mammouth | unbekannt | unbekannt | exit 2 |
| zcode | unbekannt (Projekt-Hooks vom Harness ignoriert, `docs/providers/zcode.md:160-166`) | unbekannt | exit 2 (Hooks laufen dort nicht) |
| kimi-code | unbekannt (`permissionDecision` unterstützt, Werte nicht genannt, `docs/providers/kimi-code.md:129`) | unbekannt; Exit-Codes ≠ 0/2 fail-open (`:127-129`) | exit 2 |

Regel: Provider ohne **belegtes** `ask` behalten `exit 2`; gesteuert über Capability-Flag (§3.4), nicht über
Providername. Hinweis kimi-code: dort sind andere Exit-Codes als 0/2 fail-open; ein `ask`-JSON mit exit 0
wäre dort mit unbekannter Wirkung (Risiko §12). Providerumfang entschieden (E3, vom Nutzer pauschal
übernommen): nur Claude (Capability-Flag), alle anderen Provider `exit 2`.

## 11. Fail-Verhalten (Zusammenfassung)

- Unklassifizierbar, Interpreter fehlt, JSON nicht erzeugbar, Scan-Fehler, Headless nicht auszuschließen,
  Flag fehlt/aus, Config ungültig: `exit 2` mit heutigem Stderr-Text (E3).
- Kein Pfad schwächt heutiges `exit 2` für `hard`-Klassen oder für Provider ohne Flag.
- Der Stderr-Text bei `exit 2` bleibt (Testbasis `"user approval" in result.stderr`, `:411`).

## 12. Risiken

- **Fehlklassifikation:** Eine zu großzügige ask-Klasse schwächt den Schutz; ein Klassifikator-Fehlalarm in
  `hard` bleibt Hard Block (siehe §2.2 (c)). Gegenmaßnahme: Default `hard` (§4), Tokenizer-Regression
  (AC-6).
- **`ask` headless als `allow` (Fail-open):** nicht ausgeschlossen (§6). Gegenmaßnahme: positives
  Interaktiv-Merkmal als Voraussetzung, ask-Pfad per Default aus bis dokumentierter Live-Test (E2).
- **Auto-Mode-Classifier** könnte `ask` verweigern oder den Befehl vorher ablehnen (z. B. „Undermining
  Oversight" laut #1210-Spec §2.2): nicht verifiziert; die Reibung kann bestehen bleiben.
- **Convention boundary:** Der Guard bleibt Tokenizer-basiert, kein Schutz gegen deliberate Umgehung; Einstufung
  laut `.claude/rules/branch-guard.md` („Security-Eigenschaften nur für das Destructive-Gate und den DoD-
  Push-Check“). Entschieden (E3): das Destructive-Gate bleibt Security-Eigenschaft für die `hard`-Klassen;
  die konfigurierbare ask-Klasse ist eine bewusste, bestätigbare Convention-boundary-Ausnahme, zu
  dokumentieren in `rules/1-generic/branch-guard.md` (AC-10).
- **Konfigurierbarkeit:** eine zu weit gefasste Projekt-Config könnte den Schutz schwächen; begrenzt durch
  die fest im Hook definierte Obermenge (§3.4) und fail-closed-Auswertung.
- **Prompt-Müdigkeit:** häufige `ask`-Prompts führen zu Reflex-Zustimmung; keine Messung vorhanden.
- **Gate-Reihenfolge:** durch Ausgabe von `ask` nach allen anderen Gates entschärft (§5, E3).
- Dateikonflikt: `orchestrator-guard-impl.sh` wird sequentiell erst von #1169/#1210 geändert (Plan Task 7, 8);
  Task 9 läuft danach (Plan Zeile 292).

## 13. Offene Fragen an den Nutzer

Alle Fragen sind am 2026-11-14 entschieden (Nutzer, AskUserQuestion). Offen bleiben nur die zwei
Folgepunkte unten.

1. **Welche Operationen sind ask-Klasse?** Entschieden am 2026-11-14 durch Nutzer (E1): konfigurierbar
   (`guard.ask-operations`, Arbeitsname); Default Aufräum-Set `git branch -D`, `git push origin --delete`
   (inkl. `:<b>`), `git worktree remove --force`; erlaubte Obermenge zusätzlich `stash drop/clear`, `branch
   -f`; alles andere (u. a. Force-Push jeder Branch, bis eine Default-Branch-Erkennung existiert) hart und
   nicht konfigurierbar; unbekannte Config-Einträge -> ignorieren + Sync-Warnung (§3.4, §4).
2. **`git checkout -- <file>`:** Entschieden am 2026-11-14 durch Nutzer (E3, vom Nutzer pauschal
   übernommen): bleibt Mutation; ask dort ist NICHT Teil von #1217. Reibung (b) wird separat behandelt.
3. **Headless:** Entschieden am 2026-11-14 durch Nutzer (E2): ask nur bei positiv festgestellter
   interaktiver Lage; Headless (`claude -p`) und Auto-Mode müssen im Live-Test in deny/exit 2 enden (§6).
4. **Audit `approved`/`denied`:** Entschieden am 2026-11-14 (vom Nutzer pauschal übernommen, E3): nein, nur
   `asked`.
5. **Auto-Mode-Classifier und `ask`:** Entschieden am 2026-11-14 durch Nutzer (E2): ask-Pfad gebaut, per
   Default AUS bis dokumentierter Live-Test (§6).
6. **Audit `blocked`:** Entschieden am 2026-11-14 (vom Nutzer pauschal übernommen, E3): nein.
7. **#946-Löschpfad:** Entschieden am 2026-11-14 (vom Nutzer pauschal übernommen, E3): `ask` erst nach
   Merge UND bestandenem Live-Test; Wortlaut von Entscheidung 12 wird dann in einem eigenen Schritt
   angepasst (§9.1).
8. **Format in `permissionDecisionReason`:** Entschieden am 2026-11-14 (vom Nutzer pauschal übernommen, E3):
   Befehl bis 2000 Zeichen unverändert, darüber „[gekürzt]“ mit Länge; Credentials redigiert; JSON-Escaping
   über `python3`-Helfer (§3.3).
9. **Namen:** Entschieden am 2026-11-14 (vom Nutzer pauschal übernommen, E3): Capability-Flag
   `hook-ask-permission` (Arbeitsname, `config/ai-providers.yaml`); Unterklasse `hard|ask` als zusätzliches
   Feld im Scan-Output, Default `hard`.
10. **Gate-Reihenfolge:** Entschieden am 2026-11-14 (vom Nutzer pauschal übernommen, E3): `ask` nach allen
    anderen Gates (§5).
11. **Providerumfang:** Entschieden am 2026-11-14 (vom Nutzer pauschal übernommen, E3): nur Claude
    (Capability-Flag), andere Provider `exit 2`. Live-Test ist erforderlich (E2).
12. **Einstufung:** Entschieden am 2026-11-14 (vom Nutzer pauschal übernommen, E3): Destructive-Gate bleibt
    Security-Eigenschaft für die `hard`-Klassen; die konfigurierbare ask-Klasse ist eine bewusste,
    bestätigbare Convention-boundary-Ausnahme, dokumentiert in `rules/1-generic/branch-guard.md` (AC-10).

**Offen gebliebene Folgepunkte (keine Freigabeblocker):**

- **Live-Test** (E2): Durchführung und Nachweis unter `docs/analysis/`; erst danach eigene Änderung, die
  das Flag für Claude auf an stellt.
- **Eigenes Issue für `git checkout -- <file>`** (Reibung (b)): Titelvorschlag „Guard: bestätigbarer Pfad
  für `git checkout -- <file>` (Single-Path-Restore) im Mutations-Gate“. Issue ist nicht angelegt.

## 14. Acceptance Criteria

Voraussetzung: Spec `APPROVED` (derzeit DRAFT, Freigabe 2026-11-14 zurückgezogen). Format Given/When/Then; Contract-Bezug in Klammern. Spiegelt
Plan Task 9 (Zeilen 296-303). „Aktiv“ bedeutet: Capability-/Aktivierungs-Flag an und Interaktiv-Lage positiv
festgestellt; „Default-Config“ bedeutet das Aufräum-Set (§3.4).

1. **AC-1 Hart bleibt hart** (§3.2, §4): Given Operation der `hard`-Klasse (`git reset --hard`, `git clean
   -fd`, `rm -rf /`, Fork-Bombe), When der Hook läuft, Then `exit 2`, Stderr enthält `user approval`, stdout
   enthält **kein** `permissionDecision`. Entspricht `test_reset_hard_still_exit_2`.
2. **AC-2 Branch löschen -> ask** (§3.2, §3.3, §3.4): Given Flag an, interaktive Lage, Default-Config und
   `git branch -D x`, When der Hook läuft, Then `exit 0` und stdout ist ein JSON mit
   `hookSpecificOutput.permissionDecision == "ask"` und `permissionDecisionReason` enthält den vollständigen
   Befehl (`test_branch_delete_returns_ask_decision`).
3. **AC-3 Remote-Ref löschen -> ask** (§3.2, §3.4): Given dasselbe für `git push origin --delete x` und
   `git push origin :x`, Then wie AC-2 (`test_push_delete_returns_ask_decision`).
4. **AC-4 Headless fail closed** (§6): Given Flag an und Payload/Umgebung, die nicht positiv als
   interaktiv festgestellt werden kann (Feld fehlt, Wert unbekannt, Headless), When `git branch -D x`,
   Then `exit 2`, kein JSON (`test_headless_fails_closed`).
5. **AC-5 Sentinel kann nicht approven** (§8): Given `#agent-meta:agent=git` (und `orchestrator`, Allowlist-
   Rolle) als erste Zeile vor `git branch -D x` bzw. `git reset --hard`, When der Hook läuft, Then stdout,
   stderr und Exit-Code identisch zum Aufruf ohne Sentinel (`test_sentinel_cannot_approve_ask`); nie
   `"allow"`.
6. **AC-6 Tokenizer unverändert** (§3.1): Given die Fälle aus #542 (`:414-451`), #551/#590 (`:463-476`), #591
   (`:703`), #602 (`:539-565`), When der Hook läuft, Then bleibt die Klassifikation `destructive` bzw. „kein
   Verdikt" unverändert; nur die Unterklasse kommt hinzu (`test_tokenizer_cases_unchanged`). Hinweis: #551/
   #590 sind in dieser Session nur über Testkommentar-Zeilen verortet, die endgültige Fallliste misst Task 9.
7. **AC-7 Provider ohne Flag / Default aus** (§3.4, §6, §10): Given Flag aus (Default) oder Platzhalter
   literal, When `git branch -D x`, Then `exit 2` wie vor der Änderung; bestehende Tests grün.
8. **AC-8 Mehrfach-Statement** (§3.1): Given `git branch -D x && git reset --hard`, Then `hard` (`exit 2`).
9. **AC-9 Audit asked** (§7): Given AC-2, Then enthält `.claude/hooks/.guard-audit.log` im tmp-Projekt genau
   eine Zeile mit `decision=asked`; kein `approved`/`denied` irgendwo (Test liest die Datei).
10. **AC-10 Doku** (§7, §12): Given Merge, Then nennen `rules/1-generic/branch-guard.md` und
    `rules/1-generic/a2a-delegation-gates.md` die Klassen, dass `asked` keine Ausführung belegt, Headless
    fail closed, dass der #946-Löschpfad `ask` erst nach Merge UND bestandenem Live-Test nutzen darf, und
    `branch-guard.md` dokumentiert die konfigurierbare ask-Klasse als bewusste, bestätigbare Convention-
    boundary-Ausnahme (hard-Klassen bleiben Security-Eigenschaft).
11. **AC-11 Fail-Pfad JSON** (§3.3): Given kein JSON erzeugbar (simuliert), Then `exit 2` mit Stderr-Text.
12. **AC-12 Charakterisierung** (§8): `test_destructive_ops_blocked_even_with_git_sentinel` (`:407`),
    `test_non_git_agent_cannot_use_fake_sentinel_for_destructive` (`:565`),
    `test_auto_commit_destructive_gate_still_blocks_an_allowlisted_role` (`:1002`) bleiben für die `hard`-
    Klassen grün; bei Default-Config bleiben alle Fälle der Tests exit 2 (§4, Regeln), es ist keine
    Testanpassung nötig.
13. **AC-13 Provider-Agnostik**: Given der Diff, When nach `provider ==`/Providernamen im Hook-/Sync-Code
    gesucht wird, Then kein neuer Treffer.
14. **AC-14 Validierung**: `python3 -m pytest tests/test_orchestrator_guard_hook.py tests/test_hook_drift.py`
    grün; `python3 scripts/sync.py --validate` Exit 0.
15. **AC-15 Checkout-Single-Path** (§4): Given `git checkout -- path/file.txt` (auch bei aktivem Flag),
    Then bleibt das Verhalten unverändert Mutation (`:1691`-Test grün, Mutations-Meldung `:1537`/`:1539`),
    kein `ask`.
16. **AC-16 Worktree-Remove-Force -> ask** (§3.4, §4): Given Flag an, interaktive Lage, Default-Config und
    `git worktree remove --force <pfad>`, When der Hook läuft, Then `exit 0`, JSON `ask` mit vollständigem
    Befehl; ohne Flag `exit 2` (`test_worktree_remove_force_returns_ask_decision`).
17. **AC-17 Konfigurierbarkeit** (§3.4): Given `guard.ask-operations` (Arbeitsname) ohne Eintrag
    `worktree-remove-force` (z. B. nur `branch-delete`), Flag an, interaktiv, When
    `git worktree remove --force x`, Then `exit 2`; Given Config um `stash-drop-clear` erweitert,
    When `git stash drop`, Then `ask`; Given Default-Config, When `git stash drop`, Then `exit 2`.
18. **AC-18 Nicht konfigurierbare Obermenge** (§3.4): Given Config enthält Einträge außerhalb der erlaubten
    Obermenge (z. B. `reset-hard`, `clean`, `filter-branch`, `rm-rf`, `fork-bomb`, `force-push`), Flag an,
    interaktiv, When die jeweilige Operation läuft, Then `exit 2`, kein JSON.
19. **AC-19 Unbekannte Config-Einträge** (§3.4): Given Config mit unbekanntem oder nicht erlaubtem Eintrag,
    When Sync läuft, Then Sync-Warnung (benennt den Eintrag), Eintrag wird ignoriert, Verhalten für diese
    Operation bleibt `hard`; Given ungültige/nicht lesbare Config, Then leere ask-Liste (alles `hard`).
20. **AC-20 Default aus bis Live-Test** (§6, §3.4): Given ausgelieferter Default, Then ist
    `hook-ask-permission` (Arbeitsname) für alle Provider aus und die Hook-Ausgabe für `git branch -D x`
    ist `exit 2`; das Anschalten für Claude ist eine eigene Änderung mit Nachweisdatei unter
    `docs/analysis/`, die (a) interaktives `ask` und (b) deny/exit-2-Verhalten bei Headless (`claude -p`) und
    Auto-Mode dokumentiert.
21. **AC-21 Gate-Reihenfolge** (§5): Given ein Befehl, den das Mutations-Gate oder der Strict-Mode für den
    Aufrufer blockt und der zugleich ask-Klasse wäre, Flag an, interaktiv, Then `exit 2` (Block gewinnt),
    kein JSON, kein `asked`-Audit.
22. **AC-22 Force-Push hart** (§4): Given `git push --force origin <beliebiger Branch>`, Flag an,
    Default-Config und jede erlaubte Konfiguration, Then `exit 2`.
23. **AC-23 permissionDecisionReason** (§3.3): Given Befehl mit Quotes/Zeilenumbruch, Then ist das JSON
    gültig (python3 parsebar) und der Befehl unverändert enthalten; Given Befehl > 2000 Zeichen, Then
    gekürzt mit „[gekürzt]“ und Länge; Credentials im Befehl erscheinen redigiert.

## 15. Testmatrix

Test-Infrastruktur: `_run_hook` (`tests/test_orchestrator_guard_hook.py:110`), `_bash_payload` (`:122`),
`_run_with` (`:1543`). Spiegelt Plan Task 9 Step 2 (Zeile 297).

Spalte „Flag“: Aktivierungs-Flag `hook-ask-permission` (Arbeitsname); „true“ = an, „false“ = aus (Default).
Spalte „Config“ (nur wo abweichend): `guard.ask-operations` (Arbeitsname); sonst Default-Config.

| Fall | Flag | Lage | Sentinel | Kommando | Erwartet | Test (neu) |
|---|---|---|---|---|---|---|
| T1 | true | interaktiv | — | `git branch -D x` | rc 0, JSON `ask`, voller Befehl | `test_branch_delete_returns_ask_decision` |
| T2 | true | interaktiv | — | `git push origin --delete x`, `git push origin :x` | rc 0, JSON `ask` | `test_push_delete_returns_ask_decision` |
| T3 | true | interaktiv | — | `git reset --hard` | rc 2, `user approval` | `test_reset_hard_still_exit_2` |
| T4 | true | headless/unbestimmt | — | `git branch -D x` | rc 2, kein JSON | `test_headless_fails_closed` |
| T5 | true | interaktiv | `git` | `git branch -D x` | wie T1, bytegleich | `test_sentinel_cannot_approve_ask` |
| T6 | true | interaktiv | `git` | `git reset --hard` | wie T3, bytegleich | `test_sentinel_cannot_approve_ask` |
| T7 | false | beliebig | — | `git branch -D x` | rc 2 | Provider-ohne-ask-Test |
| T8 | true | interaktiv | — | `git branch -D x && git reset --hard` | rc 2 | Mehrfach-Statement-Test |
| T9 | true | interaktiv | — | Fälle #542/#551/#590/#591/#602 | Klassifikation unverändert | `test_tokenizer_cases_unchanged` |
| T10 | true | interaktiv | — | `git branch -D x` | Audit-Zeile `decision=asked`, kein `approved` | Audit-Test (liest `.guard-audit.log`) |
| T11 | true | interaktiv | — | `rm -rf /`, Fork-Bombe | rc 2 | Hard-Klassen-Test (`:1325-1356`, `:1386`) |
| T12 | true | interaktiv | — | `git checkout -- path/file.txt` | unverändert (Mutation), kein ask (AC-15) | Charakterisierung |
| T13 | true | interaktiv | — | `git worktree remove --force x` | rc 0, JSON `ask` (AC-16) | `test_worktree_remove_force_returns_ask_decision` |
| T14 | false | beliebig | — | `git worktree remove --force x` | rc 2 | Default-aus-Test |
| T15 | true; Config nur `branch-delete` | interaktiv | — | `git worktree remove --force x` | rc 2 (AC-17) | Konfigurations-Test |
| T16 | true; Config + `stash-drop-clear` | interaktiv | — | `git stash drop` | rc 0, JSON `ask` (AC-17) | Konfigurations-Test |
| T17 | true; Default-Config | interaktiv | — | `git stash drop`, `git stash clear` | rc 2 (AC-17) | Konfigurations-Test |
| T18 | true; Config mit `reset-hard`/`clean`/`filter-branch`/`rm-rf`/`fork-bomb`/`force-push` | interaktiv | — | jeweilige Operation | rc 2, kein JSON (AC-18) | Obermengen-Test |
| T19 | — | — | — | Sync mit unbekanntem Config-Eintrag | Warnung, Eintrag ignoriert, Operation `hard` (AC-19) | Sync-Test |
| T20 | true | interaktiv | — | `git push --force origin feat/x`, `git push -f origin main` | rc 2 (AC-22) | Force-Push-Test |
| T21 | true | interaktiv | — | ask-Klasse-Befehl, den Mutations-/Strict-Gate blockt | rc 2, kein JSON, kein `asked`-Audit (AC-21) | Gate-Reihenfolge-Test |
| T22 | true | interaktiv | — | `git branch -D` mit Quotes, Zeilenumbruch, > 2000 Zeichen, Credential | gültiges JSON, ungekürzt/gekürzt „[gekürzt]“, redigiert (AC-23) | Reason-Test |
| T23 | Ausgeliefertes Default | — | — | `git branch -D x` | rc 2 (AC-20) | Default-aus-Test (Drift) |

Zusätzlich: Drift-Test `tests/test_hook_drift.py` (Hash/Platzhalter), datengetriebener Flag-Test (AC-13).

## 16. Out-of-scope

- Änderung der Classifier-/Auto-Mode-Logik des Harness.
- Audit von `approved`/`denied` (nur `asked`, §7), PermissionRequest-/PostToolUse-Hooks.
- Rollenbindung (#1210), Auto-Commit-Allowlist (#1181).
- Schließen der Tokenizer-/Indirektionslücken (`eval`, `$(...)`, `xargs`; `.claude/rules/branch-guard.md`).
- Anpassung des #946-Löschpfads und des Wortlauts von Entscheidung 12 (eigener Schritt nach Merge und
  bestandenem Live-Test, §9.1).
- Durchführung des Live-Tests und das Anschalten des Flags für Claude (eigener Task im Plan, E2).
- `ask` für `git checkout -- <file>` (Mutations-Gate): eigenes Issue, Titelvorschlag in §13.
- Default-Branch-Erkennung (Force-Push bleibt bis dahin hart).
- Neue Hook-Events oder Provider-Plugins für Provider ohne belegtes `ask`.
- Neuerfinden einer Referenz `docs/agent-templates/hooks/review-policy-gate.sh` (existiert laut Plan nicht).

## 17. Nicht verifiziert

- Rohtext der Claude-Code-Hook-/Permissions-/Headless-Doku (alle `ask`-Aussagen sind Fetch-Extraktionen,
  Hooks-Seite ab Byte-Offset 200000 ungelesen, analysis Caveat).
- PreToolUse-`ask` im `-p`-Modus (Ergebnis), unter Auto-/`bypassPermissions`; Live-Test steht aus (E2,
  Aktivierung bleibt bis dahin aus).
- Konkreter Key-Name/Schema/Ablageort von `guard.ask-operations` und die Bezeichner der Operationen
  (Arbeitsnamen), Name der Nachweisdatei unter `docs/analysis/`.
- Ob `git worktree remove --force` im Klassifikator unter den in §4 genannten Zeilen `:970-1004`
  tatsächlich als eigenes Verdikt geführt wird (aus der Entwurfsfassung übernommen, nicht neu nachgemessen).
- Ob ein Hook die Nutzerentscheidung zu einem `ask` sieht (analysis §3.4).
- Interaktion Hook-`ask` mit dem Auto-Mode-Classifier; Auflösung Rule-`allow` gegen Hook-`ask`.
- `ask`-Support und Headless-Verhalten aller Nicht-Claude-Provider.
- Existenz/Inhalt von `docs/agent-templates/hooks/review-policy-gate.sh` (laut Plan nicht vorhanden; hier
  nicht erneut per Glob geprüft) und des Issue-Texts von #1217.
- #1226/#1229 (nur über den Aufrufer bekannt; #1232 im Repo-Log sichtbar).
- Ort der Backing-Logik des Capability-Flags (`scripts/lib/hooks.py`) und eine JSON-Escape-Hilfsfunktion in
  `hook_common.sh`.
- Wortlaut von Entscheidung 1 und 12 im Plan über die in den Zeilen 33/37 genannten Auszüge hinaus.
- Dass die am 2026-11-13 beobachtete `!`-Aufforderung beim `git checkout --` vom Mutations-Gate (`:1539`)
  und nicht vom Destructive-Gate ausging: aus dem Code abgeleitet (Single-Path ist keine destructive-
  Klasse, `:951-957`), die konkrete Hook-Meldung der Beobachtung liegt nicht vor.

## 18. Änderungsprotokoll

- 2026-11-13: Entwurf (DRAFT).
- 2026-11-14: Nutzerentscheidungen (AskUserQuestion) eingearbeitet (Status zunächst `APPROVED`, Freigabe am selben Tag zurückgezogen, jetzt `DRAFT`):
  - **E1** (OQ-1): ask-Klasse konfigurierbar (`guard.ask-operations`, Arbeitsname); Default Aufräum-Set
    (`branch -D`, `push origin --delete` inkl. `:<b>`, `worktree remove --force`); erlaubte Obermenge
    zusätzlich `stash drop/clear`, `branch -f`; alles andere hart und nicht konfigurierbar (Force-Push jeder
    Branch fail closed); unbekannte Einträge ignorieren + Sync-Warnung.
  - **E2** (OQ-5/OQ-3): ask-Pfad gebaut, Default AUS bis dokumentierter Live-Test (interaktiv `ask`;
    Headless und Auto-Mode deny/exit 2); Nachweis unter `docs/analysis/`; Anschalten als eigener Task.
  - **E3** (OQ-2, 4, 6-12, pauschal übernommen): nur `asked` auditieren; nur Claude; `ask` nach allen
    Gates; Sentinel ohne Wirkung; alle Fehlerfälle exit 2; `checkout -- <file>` bleibt Mutation (eigenes
    Issue); #946-Löschpfad erst nach Merge und Live-Test; Namen `hook-ask-permission`, Feld `hard|ask`;
    Reason bis 2000 Zeichen; Einstufung Convention-boundary-Ausnahme für konfigurierbare ask-Klasse.

## 19. Trace-Anker

`spec-id: SPEC-GUARD-DESTRUCTIVE-ASK-2026-11-11`
