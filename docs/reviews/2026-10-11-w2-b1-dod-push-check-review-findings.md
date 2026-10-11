# Review-Befunde W2-B1 — `dod-push-check.sh` (SR-B-02/03/04/21, SR-B-07)

> **Zweck:** Vollständige Liste aller Befunde aus allen Review-Runden für Cluster W2-B1,
> mit Schweregrad, Status, Reproduktion und Fix-Fundstelle — als eigenständiges Nachweisdokument
> für spätere Leser (Maintainer, andere Agenten, externe Prüfer).
> **Stand:** 2026-10-11 · **Autor:** `documenter` (agent-meta) · **Review-Status:** formal beendet
> durch Nutzerentscheidung, Runde-3-Fixes **nicht** unabhängig nachgeprüft (siehe [Review-Status](#5-review-status)).

---

## 1. Kopf

### Scope

| Datei | Änderung |
|---|---|
| `hooks/1-generic/dod-push-check.sh` | Push-Erkennung per Command-Word (SR-B-03/04), Ziel-Ref-Prüfung im Branch-Guard (SR-B-02), kein SIGPIPE-Fail-Open (SR-B-21), Boundary-Wording (SR-B-07) |
| `hooks/1-generic/lib/hook_common.sh` | `hook_json_get` gibt bei Lone-Surrogate/ungültigem UTF-8 nicht mehr `""` zurück (R2S-2) |

Nicht im Scope: `orchestrator-guard*.sh` (nur als Referenz für den Statement-Splitter/`GLOBAL_OPTS_WITH_VALUE`), generierte Kopien unter `.claude/hooks/`.

### Branch / Commits

Branch `fix/sr-b-02-dod-push-check-hardening`, Basis `60dda829`, HEAD `4750487e`.

| Commit | Inhalt | Version |
|---|---|---|
| `0d7c1fc6` | Erstumsetzung SR-B-02/03/04/21/07 | Hook 2.1.0 |
| `675e0852` | Hash-Regenerierung generierter Dateien | — |
| `ba53c796` | `fix(hooks): close dod-push-check DWIM, here-string and quote bypasses` (Runde-2-Fixes) | Hook 2.1.1 |
| `bb8c94b0` | Hash-Regenerierung nach Runde 2 | — |
| `dfa3d119` | `fix(hooks): keep undecodable JSON values in hook_json_get` | Lib 1.0.1 |
| `4750487e` | `fix(hooks): close dod-push-check exec, alias and size bypasses` (Runde-3-Fixes) | Hook 2.1.2 |

Hinweis zur Herkunft: Die Zuordnung Commit → Inhalt stützt sich auf Commit-Subjects, den Changelog
im Hook-Header (Zeile 9) und den Lib-Changelog (`hook_common.sh` Zeile 5). Die Diffs der einzelnen
Commits wurden für dieses Dokument nicht einzeln geöffnet.

### Versionen

- Hook: **2.0.3 → 2.1.0 → 2.1.1 → 2.1.2** (`hooks/1-generic/dod-push-check.sh`, Header Zeile 3/9)
- Lib: **1.0.0 → 1.0.1** (`hooks/1-generic/lib/hook_common.sh`, Header Zeile 5)

### Methodik

| Runde | Durchführung | Werkzeuge / Umfang | Ergebnis |
|---|---|---|---|
| 1 — Qualität | unabhängiger Opus-`code-reviewer` | Code-Lesen, Einzelproben | APPROVED_WITH_RECOMMENDATIONS, kein Blocker |
| 1 — Security | unabhängiger Opus-`code-reviewer` | PreToolUse-JSON-Payloads gegen alt/neu; `--dry-run`-Pushes gegen Sandbox-Bare-Repos; rc-Tabelle 166 Payloads × {main, feature, detached} = 498 Zeilen alt/neu (`.tmp/sec-review-b1/table*.out`) | CHANGES_REQUESTED, 2 Blocker |
| 2 — Security (Re-Review) | unabhängiger Opus-`code-reviewer` | 538 Payloads × 3 = 1614 Fälle gegen v2.0.3 / v2.1.0 / v2.1.1 (`.tmp/sec-review-b1r2/mono.out`), Profiling (`prof.out`), Surrogate-Proben (`surr.out`) | CHANGES_REQUESTED, 2 Blocker; nur teilweise durchgeführt (siehe R2S-7) |
| 3 | **kein Review** — Nutzer hat das Review beendet; nur Entwickler-Fixes + Entwickler-Tests | — | — |

Ergebnis der Vergleichstabelle Runde 1: 0 unerwartet schwächere Zeilen, außer gewollt harmlosem
SR-B-04-Text (`echo …`) und der dokumentierten Indirektion `echo … | sh`.
Ergebnis Runde 2: 0 Fälle schwächer als v2.1.0; 39 Fälle (13 Payloads × 3) schwächer als v2.0.3 —
davon gewollt SR-B-04-Text (`echo`, `gh pr create --body`, `git commit -m`, `cat`, …) und echte
Regressionen bei `submodule foreach` / `bisect run` (→ R2S-1).

### Legende

| Feld | Werte |
|---|---|
| Schweregrad | **Blocker** (Merge-verhindernd) · **Hoch** · **Mittel** · **Niedrig** · **Info** |
| Status | **fixed** (im Code + Test nachgewiesen) · **offen** · **teilweise** (Teil fixed, Rest offen) · **akzeptiert** (bewusster Trade-off) · **abgelöst** (in anderem Befund aufgegangen) · **kein Defekt** · **nicht geprüft** |
| Verifikation | **V** = Fix in Code und Test auf HEAD `4750487e` nachgelesen · **nV** = Fix behauptet, nicht verifiziert |
| ID | R1Q = Runde 1 Qualität · R1S = Runde 1 Security · R2S = Runde 2 Security |

Separate R2Q-Befunde (Runde-2-Qualität) wurden nicht erhoben; die Qualitäts-Fixes der Runde 2
laufen unter den Fix-Labels QF1/QF5 (siehe R1Q-1, R1Q-5). Die Runde-2-Fix-Labels F1/F2/A2–A5
entsprechen R1S-1/R1S-2/R1S-4–R1S-7, die Runde-3-Labels R2-1…R2-5 entsprechen R2S-1…R2S-5.

---

## 2. Kennzahlen

| Runde | Befunde | Blocker | fixed | offen / teilweise | akzeptiert | sonstige |
|---|---|---|---|---|---|---|
| R1 Qualität | 10 | 0 | 2 | 4 / 2 | 0 | 1 abgelöst, 1 kein Defekt |
| R1 Security | 11 | 2 | 8 | 2 / 0 | 1 | — |
| R2 Security | 7 | 2 | 5 | 0 / 0 | 1 | 1 nicht geprüft |
| R3 | — | — | — | — | — | kein Review durchgeführt |
| **Summe** | **28** | **4** | **15** | **6 / 2** | **2** | **3** |

Alle 4 Blocker sind im Code gefixt; die beiden Runde-2-Blocker (R2S-1, R2S-2) wurden nach dem Fix
**nicht** erneut unabhängig geprüft.

---

## 3. Befunde

Fundstellen beziehen sich auf HEAD `4750487e`. Tests: `tests/test_dod_push_check_hook.py`.

### 3.1 Runde 1 — Qualität (R1Q)

| ID | Schweregrad | Befund / Reproduktion | Status | Fix-Fundstelle / Commit | Verif. |
|---|---|---|---|---|---|
| R1Q-1 | Mittel | Gequoteter Separator vor dem Refspec versteckt das Ziel: Payload `git push -o "ci.variable=A;B" origin HEAD:main` lief nur in den Test-Gate statt Block. | fixed | QF1: Statements quote-aware + Legacy-Sicht, BLOCK gewinnt; `test_qf1_quoted_separator_before_refspec` (`QF1_TABLE`); `ba53c796` (v2.1.1) | V |
| R1Q-2 | Mittel (Verfügbarkeit) | Heredoc/mehrzeiliger Text (PR-Body, Commit-Message) mit einer Zeile, die mit `git push … main` beginnt, blockiert hart; Meldung lautet „Push blocked", obwohl der Befehl `gh`/`commit` ist. | offen | Issue #943 (W2-B2b, Scope-Punkt j); Workaround `--body-file` / `-F` | — |
| R1Q-3 | Niedrig | Kommentar `# main` nach einem Push zählt als Refspec, da `lex.commenters = ""` (`dod-push-check.sh` Z. 605, unverändert). | offen | — | — |
| R1Q-4 | Niedrig (Wartbarkeit) | Flag-/Short-Cluster-Walk (~25 Zeilen) doppelt in `stmt_is_tag_only` und `destination_block`. | offen | — | — |
| R1Q-5 | Mittel | `man`, `less`, `more`, `ack`, `gh` in `NON_EXEC`, obwohl sie Befehle ausführen können (`man -P`, `LESSOPEN`, `ack --pager`). | fixed | QF5: man/less/more/ack aus `NON_EXEC` entfernt, man-Sonderregel, `gh`-`!alias`-Grenze dokumentiert (Header Z. 534–541); `test_qf5_exec_capable_pagers_are_not_text`, `test_qf5_reading_docs_is_not_a_push`; `ba53c796` | V |
| R1Q-6 | Niedrig | (a) `xargs git push origin < refs` läuft nur in den Test-Gate (Ziel unbekannt); (b) `{}`-Platzhalter; (c) Block-Meldung bei `$(git branch --show-current)` sollte auf `HEAD` hinweisen. | offen | — (Block bei `$(…)` selbst ist in `B02_TABLE` getestet, der Meldungshinweis fehlt) | — |
| R1Q-7 | Mittel (Performance) | 7,45 s für eine unbalancierte 300-KB-Einzelzeile (shlex, 3 Durchläufe). | abgelöst | aufgegangen in R2S-3 | — |
| R1Q-8 | Niedrig (Testlücken) | Fehlende Tests: GIT_MAIN_BRANCH aus `project.yaml`, gleichnamiger Tag/Branch, NUL, 300-KB-Einzelzeile, `-C other`, `_run_hook` scrubbt `AGENT_META_*` nicht. | teilweise | Adressiert: NUL (`test_r2_2_unextractable_bash_command_blocked`, `\u0000`), 300-KB-Einzelzeile (`test_r2_3_many_statements_and_nesting_fast`, id `ident-300K`). Offen: Main-Branch nur per Env (`test_custom_main_branch_is_protected_destination`), nicht aus `project.yaml`; kein Test gleichnamiger Tag/Branch; `-C` nur mit `.`; `_run_hook` (Z. 42–54) setzt weiterhin kein bereinigtes Env (nur `_assert_outcome` entfernt `AGENT_META_MAIN_BRANCH`). | V |
| R1Q-9 | Mittel | `git -C <other> push` bzw. `cd other && git push` wird gegen das cwd-Repo beurteilt. | teilweise | Explizite Refs werden geprüft; refspec-lose/`HEAD`-Pushes mit `-C`/`--git-dir`/`--work-tree`/`GIT_DIR` blocken (`test_a4_other_repository_push`, `ba53c796`). Offen: der `cd other && …`-Fall. | V |
| R1Q-10 | Info | Auftrag nannte `.agents/hooks/dod-push-check.sh`; existiert nicht (generierte Kopie nur unter `.claude/hooks/`). | kein Defekt | — | — |

### 3.2 Runde 1 — Security (R1S)

| ID | Schweregrad | Befund / Reproduktion | Status | Fix-Fundstelle / Commit | Verif. |
|---|---|---|---|---|---|
| R1S-1 | **Blocker** | DWIM-Ziel-Bypass über `heads/main`: Payloads `feature:heads/main`, `+feature:heads/main`, `:heads/main`, `--delete heads/main`, `-d origin heads/main` nach dem Subcommand `push`; per `--dry-run` gegen Bare-Repo bestätigt, dass git sie auf `refs/heads/main` auflöst. | fixed | F1: Normalisierung in `is_protected` (heads/…, remotes/<r>/…, refs/…); `tags/main` bleibt ungeschützt; `test_f1_dwim_destination_spellings` (`F1_TABLE`, 6 Schreibweisen × 9 Formen × 3 Zustände + Negativfälle); `ba53c796` | V |
| R1S-2 | **Blocker** | Pre-Filter fail-open: `grep … <<<"$COMMAND"; [ $? -eq 1 ] && exit 0` — kann die Here-String-Tempdatei nicht angelegt werden (> Pipe-Größe bei `ulimit -f 64`, volles `/tmp`), liefert grep rc 1 ⇒ exit 0. Reproduziert mit ~160-KB-Befehl. | fixed | F2: Pre-Filter als reines Bash `[[ =~ ]]` (Z. 105–109), `trap '' XFSZ` (Z. 61), leere Klassifizierer-Ausgabe blockt; `test_f2_here_string_failure_fails_closed` (mit/ohne XFSZ-Trap, `ulimit -f 64`), `test_f2_one_megabyte_non_push_is_fast`; `ba53c796` | V |
| R1S-3 | Mittel (Verfügbarkeit) | Mehrzeiliger Text blockiert hart — identisch mit R1Q-2. | offen | Issue #943 (W2-B2b) | — |
| R1S-4 | Mittel (DoS) | Ein `git rev-parse` pro Ref: 10 000 Refs ≈ 22 s. | fixed | A2: ein `for-each-ref`-Snapshot (Z. 284–289); `test_a2_many_tag_pushes_are_fast` (5000 Tag-Pushes < 10 s); `ba53c796` | V |
| R1S-5 | Mittel | Refspec-loser Push wird über Config umgeleitet (`push.default=upstream` + `branch.<n>.merge=refs/heads/main`, `remote.<r>.push`); ausnutzbar nur mit Nicht-Default-Config. | fixed | A3: Config-Auswertung inkl. `-c`/`GIT_CONFIG*`-Overrides (Header Z. 211–214); `test_a3_push_destination_from_config`, `test_a3_tag_push_mapped_onto_main_is_not_tag_only`; `ba53c796` | V |
| R1S-6 | Mittel | `git -C other` / `--git-dir` ohne Refspec bzw. mit `HEAD` wird gegen das cwd-Repo beurteilt. | fixed | A4: Block (Header Z. 209–211); `test_a4_other_repository_push`; `ba53c796` | V |
| R1S-7 | Hoch | Direkte Aufrufe, die alt und neu verfehlten: `git $'push'`, `$'git' push`, `git {push,} origin main`, `git-push`, `/usr/lib/git-core/git-push`. | fixed | A5: berechnete Wörter ⇒ UNRESOLVED (Block), Basename `git-push`; `test_a5_expanded_push_forms_blocked` (`A5_FORMS`), `test_a5_expanded_refs_from_feature`; `ba53c796` | V |
| R1S-8 | Info | Dokumentierte Indirektion (#592): `bash -c`, Backticks, `printf … \| sh`, `man -P`, `rg --pre`, variablengebautes `git ${p}sh`, gh-Alias. | akzeptiert | Convention boundary, Header Z. 25–29 und `.claude/rules/branch-guard.md`. Teilweise inzwischen trotzdem geblockt (`man -P`, `rg --pre`: R1Q-5/R2S-5). | — |
| R1S-9 | Hoch | Lone Surrogate im Befehl leert `COMMAND` in `hook_json_get` ⇒ exit 0 (vorbestehend). | fixed | in Runde 3 als R2S-2 behoben | V |
| R1S-10 | Niedrig | `--recurse-submodules=on-demand` pusht Submodul-Commits mit deren eigener Push-Config, ohne Zielprüfung. | offen | — (Option steht in der Liste verstandener Optionen, Z. 553–554; keine Submodul-Zielprüfung gefunden) | — |
| R1S-11 | Niedrig | Header-Wording SR-B-07 („security boundary" pauschal). | fixed | „security boundary" nur für den #595-Abhängigkeitscheck, sonst convention boundary (Header Z. 19–29); `0d7c1fc6` (v2.1.0) | V |

### 3.3 Runde 2 — Security-Re-Review (R2S)

| ID | Schweregrad | Befund / Reproduktion | Status | Fix-Fundstelle / Commit | Verif. |
|---|---|---|---|---|---|
| R2S-1 | **Blocker** (Abschwächung ggü. v2.0.3) | `git submodule foreach git push origin main`, `git submodule foreach --recursive git push origin HEAD:main`, `git bisect run git push origin main` ergaben `none` (v2.0.3: block/gate). | fixed | Nicht-Push-Subcommands außer reinen Text-Subcommands werden wie Wrapper gescannt (Header Z. 354–357); `test_r2_1_command_running_subcommands_blocked` (`R2_1_BLOCKED`), `test_r2_1_resolved_aliases_and_text`; `4750487e` (v2.1.2) | V, **nicht re-reviewt** |
| R2S-2 | **Blocker** | Lone Surrogate (`"git push origin main\ud800"`; `\udcff` unter `de_DE.UTF-8`) ⇒ leerer Befehl ⇒ exit 0. | fixed | `hook_common.sh` v1.0.1: `hook_json_get` decodiert mit `surrogateescape`/schreibt mit `surrogatepass` (Lib Z. 69–89, `dfa3d119`); `dod-push-check.sh` blockt, wenn ein nicht-leerer Bash-Befehl nicht extrahiert werden konnte (Z. 67–91, `4750487e`); `test_r2_2_lone_surrogate_does_not_skip_guard` (3 Locales × 4 Payloads), `test_r2_2_unextractable_bash_command_blocked`, `test_r2_2_empty_command_for_non_bash_or_empty_bash_allowed` | V, **nicht re-reviewt** |
| R2S-3 | **Hoch** (Fail-Open über Hook-Timeout) | Superlineare Klassifizierer-Laufzeit: 1 MB Identifier+Push 32,6 s, 1 MB `$` 31,0 s, 1 MB Backslashes 8,2 s, 300 KB Identifier 3,0 s (Profil: `shlex.read_token`, `.tmp/sec-review-b1r2/prof.out`). Hook-Timeout = nicht-blockierender Fehler = Durchlass. | fixed | Zeitbudget `CLASSIFY_BUDGET=20` ⇒ Block bei Überschreitung (Z. 233–236) plus lineare Verbesserungen (shlex-Token-Puffer, Brace-/Nested-Scans, Z. 325–338); `test_r2_3_huge_push_commands_block_in_time` (< 25 s), `test_r2_3_many_statements_and_nesting_fast`, `test_r2_3_classifier_over_budget_blocks`, `test_r2_3_normal_push_stays_fast`; `4750487e`. **Messwerte nach dem Fix nur laut Tests, nicht unabhängig nachgemessen.** | V (Code/Test), Messung nV |
| R2S-4 | Hoch | Zeilenfortsetzung im Wort `push` (`git pu\<NL>sh origin main`) umgeht den Pre-Filter. | fixed | Pre-Filter toleriert `\<NL>` zwischen den Buchstaben (Z. 96–106); `test_r2_4_line_continuation_inside_push`; `4750487e` | V, **nicht re-reviewt** |
| R2S-5 | Hoch | Rest-Bypässe: `git -c alias.p=push p origin main`, `git -c alias.x='!git push origin main' x`, `--config-env=alias.*`, `git rebase -x`, `filter-branch --tree-filter`, `difftool -x`, `-c core.pager` / `core.sshCommand`, `rg --pre`. | fixed (mit dokumentierter Restgrenze) | Siehe Abdeckung unten; `test_r2_1_command_running_subcommands_blocked`, `test_r2_1_resolved_aliases_and_text`; `4750487e` | V, **nicht re-reviewt** |
| R2S-6 | Mittel (Verfügbarkeit) | Neue harte Blocks ggü. v2.1.0: `git -C . push origin HEAD`, `--git-dir`, `GIT_DIR=.git` vor dem Push, `git -c push.default=current\|upstream push`, gequotetes `;`/`\|`/`&` im Push-Statement, `LESSOPEN`/`less`. | akzeptiert | entspricht dokumentierter Absicht (A4, A3, QF1, QF5) | — |
| R2S-7 | — | Im Re-Review **nicht geprüft**: `GIT_CONFIG_COUNT`/`GIT_CONFIG_PARAMETERS`/Includes in der Tiefe (Checkliste 3a/3b/3f); fehlschlagendes/langsames `git config`; fehlschlagendes `for-each-ref`; fehlendes python3 und PATH-Shim mit Müll-Ausgabe; `push.default`-Matrix und Submodul-Repos; Byte-Identität der deployten Guard-Kopien ggü. `origin/main` (v1.7.0/3.2.0 nach Downgrade auf alter Basis von Hand aus Sync-Backups wiederhergestellt — Rebase soll das bereinigen); pytest-Lauf und Mutationsprüfung von 5 neuen Tests. | nicht geprüft (offen) | — | — |

#### R2S-5 — Abdeckung im Detail (laut Header Z. 9, 30–38, 348–357 und `R2_1_BLOCKED`)

Abgedeckt (geblockt, getestet):

- Aliase, die **auf derselben Befehlszeile** deklariert sind: `-c alias.p=push` (auch Großschreibung `ALIAS.p`, Alias-Ketten `alias.q=p`), `-c alias.x='!git push …'`, `-c alias.x='!sh -c "git push …"'`, `--config-env=alias.p=VAR`, `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_0`/`GIT_CONFIG_VALUE_0` mit Alias. Ein aufgelöster Alias auf einen Feature-Branch läuft regulär in den Test-Gate.
- Ausführende Subcommands mit `git … push` im Argument: `submodule foreach`, `bisect run`, `rebase -x`/`--exec`, `filter-branch --tree-filter`, `difftool -x`, `git config alias.x '!git push …'`.
- Exec-Config auf der Befehlszeile: `core.pager`, `core.sshCommand`, `core.editor`, `sequence.editor` — sowohl wenn der Wert einen Push enthält als auch generell auf einem Push-Statement.
- `rg --pre`, `ack --pager`.

Bleibt offen (dokumentierte Grenze, Header Z. 30–38):

- Aliase oder Exec-Config aus Config-Dateien (Repo, global, `GIT_CONFIG_GLOBAL=<file>`, `include.path`) oder aus einem früheren Statement/Aufruf (`git config alias.p push` in einem Aufruf, Nutzung in einem späteren) — der Pre-Filter sieht kein `push`.
- Skripte, die per `rebase -x`, `bisect run`, `submodule foreach`, Hooks oder Filter laufen und deren Text kein `git … push` enthält (z. B. `git rebase -x ./deploy.sh`).

---

## 4. Offene Befunde → Issues

| ID | Kurzbeschreibung | Issue |
|---|---|---|
| R1Q-2 / R1S-3 | Heredoc/mehrzeiliger Text blockiert hart, irreführende Meldung | #943 (W2-B2b, Scope-Punkt j) — Zuordnung laut Orchestrator, hier nicht gegen den Issue-Text geprüft |
| R1Q-3 | `# main`-Kommentar als Refspec (`lex.commenters = ""`) | wird nach PR-Erstellung ergänzt (Kandidat für #943) |
| R1Q-4 | doppelter Flag-/Short-Cluster-Walk | wird nach PR-Erstellung ergänzt |
| R1Q-6 | `xargs`-Push nur Gate, `{}`-Platzhalter, `HEAD`-Hinweis in der Meldung | wird nach PR-Erstellung ergänzt |
| R1Q-8 (Rest) | Testlücken: Main-Branch aus `project.yaml`, Tag/Branch gleichen Namens, `-C other`, `_run_hook`-Env | wird nach PR-Erstellung ergänzt |
| R1Q-9 (Rest) | `cd other && …` gegen cwd-Repo beurteilt | wird nach PR-Erstellung ergänzt |
| R1S-10 | `--recurse-submodules=on-demand` ohne Submodul-Zielprüfung | wird nach PR-Erstellung ergänzt |
| R2S-7 | nicht geprüfte Re-Review-Punkte | wird nach PR-Erstellung ergänzt |

---

## 5. Review-Status

- **Drei Runden**: Runde 1 (Qualität + Security) und Runde 2 (Security-Re-Review) wurden von
  unabhängigen Opus-`code-reviewer`-Agenten durchgeführt.
- **Runde 3 fand nicht statt.** Der Nutzer hat das Review nach Runde 2 beendet (keine weiteren Runden).
- Die Fixes für **R2S-1 … R2S-5** (Commits `dfa3d119`, `4750487e`; Hook v2.1.2, Lib v1.0.1) sind
  durch Entwickler-Tests abgedeckt — laut Testlauf auf dem committeten Stand 530 grüne Hook-Tests
  (Zahl vom Orchestrator übermittelt; für dieses Dokument nicht selbst ausgeführt) —, wurden aber
  **nicht unabhängig nachgeprüft**. Insbesondere die beiden Runde-2-Blocker R2S-1 und R2S-2 haben
  keinen Reviewer-Sign-off.
- Für dieses Dokument wurden Code und Tests auf HEAD `4750487e` gelesen: Für jeden als „fixed"
  markierten Befund existieren die genannte Code-Stelle und ein passender Testfall. Das ersetzt kein
  Review (Tests wurden weder ausgeführt noch mutiert).
- **Formaler Status:** beendet durch Nutzerentscheidung · letzte Review-Entscheidung: CHANGES_REQUESTED
  (Runde 2) · Nachfolgende Fixes: nur Entwickler-verifiziert.

---

## 6. Nicht geprüft / Grenzen

- Alle unter R2S-7 genannten Punkte.
- Laufzeitmessungen nach dem R2S-3-Fix: nur über die Zeitgrenzen der Tests (< 25 s / < 10 s / < 2 s), keine unabhängige Messreihe.
- Byte-Identität der generierten/deployten Hook-Kopien (`.claude/hooks/`) mit den Quellen in `hooks/1-generic/`.
- Das Dokument beruht auf: Hook-Header und -Code, `hook_common.sh`, `tests/test_dod_push_check_hook.py`,
  Review-Artefakten in `.tmp/sec-review-b1/`, `.tmp/sec-review-b1r2/`, `.tmp/srb02-review/`,
  `.tmp/srb02-round2/` sowie Commit-Subjects. Commit-Diffs und Issue #943 wurden nicht im Detail gelesen.
- Der Hook bleibt außerhalb des #595-Abhängigkeitschecks eine **convention boundary**
  (`.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`):
  gezielte Indirektion (#592) ist weiterhin möglich.
- Aufbewahrung: Dieses Dokument bleibt bis zur Schließung aller oben gelisteten Issues in `docs/reviews/`;
  `.tmp/`-Artefakte sind flüchtig und nicht Teil des Nachweises.
