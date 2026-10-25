# Review — Tmp-Sink-Injektion Spec

**Datum:** 2026-10-24
**Geprüftes Artefakt:** `docs/specs/2026-10-24-tmp-sink-injection-spec.md`
**Trace-Anker:** `spec-id: SPEC-tmp-sink-injection`
**Review-Rolle:** Concept Reviewer (Critic, Phase vor REQ/Plan/Code)
**Prüfmaßstab:** Struktur, Faktenrichtigkeit gegen den Code, Vollständigkeit des Injektions-Inventars, interne Konsistenz, Fail-closed-Design, Provider-Agnostik, Threat-Model, Formregeln, Nutzerauftrag. Die Spec ist ein Entwurf; das Fehlen von Implementierung, Plan und Approval-Marker ist kein Befund.

## Verdict

**CHANGES_REQUESTED** — Der Design-Kern (ein Resolver, relative/absolute Form, fail-closed Hook, Option C) ist tragfähig und die Entscheidungsvorlage ist inhaltlich korrekt, aber vier blockierende Punkte verhindern die Freigabe: ein widersprüchlicher Resolver-Vertrag bei deaktiviertem Sink, ein nachweislich unvollständiges Injektions-Inventar (u. a. `standalone/`, ein Hook-`mktemp`), ein nicht existierender Renderer für `config/routing/reviewers.yaml` und ein potenzieller Selbstausschluss des Guards auf Antigravity.

## Findings

| ID | Severity | Ort | Befund | Geforderte Änderung |
|---|---|---|---|---|
| RVW-01 | BLOCKER | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:648` gegen `:493` | `resolve_tmp_paths` soll laut IC-Tabelle `tmp-sink.disabled` werfen; die Fehlermatrix verlangt für `tmp-sink.enabled: false` aber „ok“ beim Sync und einen weiterhin gesetzten relativen `TMP_SINK_PATH`. Beides ist unvereinbar: wirft der Resolver, kann `_build_orch_variables` keinen `TMP_SINK_PATH` setzen und der Sync endet mit Exit 1. Auch `TmpPaths.enabled: bool` wäre dann toter Zustand. | Vertrag eindeutig festlegen: entweder `resolve_tmp_paths` wirft bei deaktiviertem Sink **nicht** (nur `tmp_env`/Verbraucher werfen), oder die Fehlermatrix/`TMP_SINK_PATH`-Zusage wird korrigiert. `TmpPaths.enabled`-Semantik explizit an die Fehlermatrix koppeln. |
| RVW-02 | BLOCKER | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:328-341`, `:729-734` | Das „vollständige“ Inventar übersieht die ausgelieferten `standalone/agents/**`: dort stehen 18 `/tmp`-Literale und 4 `.tmp/`-Sink-Literale (`standalone/agents/developer.md:30,33,130,139`, `tester.md:55,58,125,127`, `validator.md:47,50`, `docker.md:115,117`, `devops-engineer.md:185,187`, `e2e-tester.md:126,128`, `code-reviewer.md:206,214`, `ai-security-guardian.md:96`, `app-lifecycle-governor.md:90`, `prompt-governor.md:106`, `security-auditor.md:201`). Zusätzlich fehlt eine Standalone-Auflösung für `{{TMP_SINK_PATH}}`: unbekannte Platzhalter werden zu `[TMP_SINK_PATH — not available outside a full agent-meta install]` (`scripts/lib/standalone.py:313-319`), sichtbar in `standalone/agents/meta-doctor.md:23-24,43`. AC-02 macht dieses Verhalten für vier weitere Rollen zum Regelfall. | `standalone/agents/**` als Injektionspunkt und als Check-Scope (Inventar 1/7) aufnehmen; Entscheidung für einen Standalone-Fallback (`TMP_SINK_PATH` = `.tmp` oder expliziter Hinweis) treffen; AC für `--render-standalone` ergänzen. |
| RVW-03 | BLOCKER | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:340`, `:730-732` | Injektionspunkt 9 behauptet, ein „Renderer“ setze den Sink in `config/routing/reviewers.yaml` ein, mit `scripts/lib/rules.py:269` als Variablenquelle. Es gibt keinen Renderer und keinen Produktions-Konsumenten dieser Datei; der einzige Leser ist `tests/test_review_fleet.py:13`. `rules.py:269` speist Regel-Templates, nicht Routing-YAML. Ein `{{TMP_SINK_PATH}}` dort bliebe als Literal stehen. | Entweder Injektionspunkt 9 und die `reviewers.yaml`-Klausel in AC-02 streichen, oder einen konkreten Renderer/Konsumenten mit Datei:Zeile benennen und die Zustellung an Zielprojekte belegen. |
| RVW-04 | BLOCKER | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:429-430`, `:994-996`; `hooks/1-generic/antigravity-json-adapter.sh:123-134` | „`cwd` fehlt ⇒ Exit 2“ ist für den einzigen weiteren hook-fähigen Provider nicht abgesichert: der Antigravity-Adapter setzt `out['cwd'] = cwd` auch dann, wenn `cwd` die leere Zeichenkette ist (`d.get('cwd')`/`workspacePaths[0]`/`Args.Cwd` alle leer). Damit würde jeder Write/Edit auf Antigravity blockiert. Q5 stellt die Frage, verschiebt aber eine gate-relevante Entscheidung. Zudem prüft AC-04 „Payload ohne `cwd`-Key“, während der reale Fehlerfall der leere Wert ist. | Verhalten für alle vier Fälle explizit definieren (Key fehlt / Wert leer / Symlink / relativ) und für Antigravity belegen; AC-04 um den Leerwert-Fall ergänzen; Q5 vor Freigabe entscheiden. |
| RVW-05 | MAJOR | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:984-1000` gegen `:762-766`, `:773-776`, `:807-810` | Offene Fragen entscheiden Sachverhalte, die die ACs bereits als gegeben festschreiben: Q2 stellt `TMP_SINK_ABS_PATH` infrage, AC-16/IC-05/IC-13 verlangen sie; Q4 stellt den Root-Vorrang infrage, AC-08 fordert „ohne Root ⇒ Exit 2“; Q7 stellt den Backup-Fallback infrage, AC-10 fordert ihn. Ein AC, dessen Erwartung von einer offenen Frage abhängt, ist nicht prüfbar. | Entweder Frage schließen und AC behalten, oder AC als „abhängig von Qx“ markieren und bis zur Entscheidung aus der Traceability nehmen. |
| RVW-06 | MAJOR | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:984-986` gegen `:414-416`; `docs/concepts/repo-containment-prison-mode.md:410-411` | Die in Q1 angebotene Alternative „Default aus“ würde den Basetemp per Default unter `<sink>/pytest` legen und damit §5.5 Punkt 1 („Basetemp nie im Arbeitsbaum“) inhaltlich umkehren — genau die Umkehr, die die Spec unter „Keine stille Umkehr“ ausschließt. | Q1 auf die Variante „Default an“ zuschneiden oder die Alternative ausdrücklich als §5.5-Änderung mit eigener Begründung/Nutzerentscheidung kennzeichnen; Nicht-Ziel „§5.5 bleibt inhaltlich bestehen“ an Q1 koppeln. |
| RVW-07 | MAJOR | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:736-760`; `tests/test_repo_containment_hook.py:213-218` | Die neuen Fail-closed-ACs sind selbst basetemp-abhängig: liegt `tmp_path` (und damit die Fixture-Wurzel) im Repo, findet die Ancestor-Suche das echte `.meta-config/` und AC-03/AC-05/AC-07 liefern Exit 0 statt 2. Das ist exakt der in Abschnitt J (`:249-256`) beschriebene Mechanismus. Option A sieht dafür einen Fixture-Sentinel vor (Punkt 1), Option C wendet ihn auf die neuen Tests nicht an. | Sentinel/Root-Injektion (`AGENT_META_PROJECT_ROOT` oder Resolver-Monkeypatch) für alle neuen Hook-ACs verbindlich machen, unabhängig von Option A/C; im AC-Text als Vorbedingung nennen. |
| RVW-08 | MAJOR | `hooks/1-generic/antigravity-json-adapter.sh:167` | Der ausgelieferte Hook-Adapter legt bei jedem Lauf eine Datei per `mktemp` im System-Temp an (`_ERR_FILE`). Injektionspunkt 5 deckt nur Pfadauflösung und Meldungen ab; dieser Schreibpunkt fehlt im Inventar und in der Fehlermatrix. | Als Injektionspunkt 11 aufnehmen oder als bewusste, dokumentierte Ausnahme (analog Toolchain-Cache) mit Begründung und Fehlerverhalten führen. |
| RVW-09 | MAJOR | `scripts/lib/gitignore.py:324-339`; `scripts/lib/doctor_detectors.py:403-411`; gegen `docs/specs/2026-10-24-tmp-sink-injection-spec.md:76-79`, `:328-341` | Zwei weitere Sink-Konsumenten fehlen: der Managed-`.gitignore`-Block leitet den Eintrag aus `effective.tmp_sink_path` ab (getrennter Mechanismus von `ensure_tmp_sink_gitignore`, Injektionspunkt 8), und der Doctor prüft `repo_containment.tmp-sink.path` erneut mit eigener Validierung. Beides widerspricht „keine Stelle parst `repo_containment` erneut“. | Beide als Konsumenten von `TmpPaths` in Inventar und IC-Tabelle aufnehmen (oder begründet ausnehmen). |
| RVW-10 | MAJOR | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:39-44`; `docs/concepts/repo-containment-prison-mode.md:410-411` | Die Problemdarstellung behauptet, §5.5 schreibe `--basetemp=/tmp/<user>` „zwingend“ vor. Der Regeltext verlangt „außerhalb“ und nennt `/tmp/<user>` als Beispiel („z. B.“), ausdrücklich alternativ zu `TMPDIR`. Die Formulierung „zwei widersprüchliche Regeln“ überzeichnet damit den Ist-Zustand. | Wortlaut korrigieren: §5.5 ist inhaltlich korrekt und literal nur im Beispiel und in den ausgelieferten Config-Werten; Problem bleibt die Literal-Verbreitung, nicht die Regel. |
| RVW-11 | MAJOR | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:495-496`; `scripts/lib/repo_containment.py:235-243` | Die Fehlermatrix verspricht konkrete Texte, liefert aber nicht existierende: „expected a relative path …“ gibt es nicht, real ist `must be relative to the project root (absolute and UNC paths are not allowed)`; die zitierte Stelle `repo_containment.py:339-341` ist ein Docstring, nicht die Fehlerquelle. Ebenso heißt es real `must not contain '..' segments` (Plural, `:243`), nicht `'..' segment`. | Beispieltexte wörtlich aus dem Code übernehmen und auf die tatsächlichen Zeilen (`:233-243`) verweisen. |
| RVW-12 | MAJOR | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:436-438`, `:752-755` | Die Basis für relative Ziele (`REPO_ROOT` statt `WORKDIR`) wird mit einer Prompt-Annahme begründet, nicht mit einem Payload-Vertrag. Relative Tool-Pfade werden provider-/tool-seitig üblicherweise gegen `cwd` aufgelöst; die Änderung kann je nach `cwd`-Tiefe falsch erlauben oder falsch blocken (z. B. `cwd=<repo>/a/b`, Ziel `../../x`). AC-06 prüft die interne Basis, nicht den tatsächlichen Schreibort. | Payload-/Tool-Semantik je Provider belegen oder die Entscheidung als offene Annahme (Q) führen; AC-06 auf den real erwarteten Zielpfad beziehen. |
| RVW-13 | MINOR | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:723-726`, `:762-766`, `:800-805` | Mehrere ACs bündeln mehrere prüfbare Aussagen: AC-01 sucht das unqualifizierte Pfadsegment `Temp` (trifft „Template“/„temporary“), AC-03 fordert zusätzlich ein unscharfes „`REPO_ROOT` erscheint nicht als `cwd`“, AC-08 und AC-15 enthalten je zwei bzw. vier Fälle. | Pro AC genau eine Aussage; AC-01 mit exaktem Regex (Groß-/Kleinschreibung, Wortgrenze, Pfadkontext) präzisieren; AC-08/AC-15 in Einzel-ACs splitten. |
| RVW-14 | MINOR | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:512-515` gegen `:648` | `tmp-sink.abs-path-unresolved` wird in der IC-Tabelle als Fehlerpfad eingeführt, fehlt aber in der Liste „Neue Fehlercodes (vollständig)“. | Code in die vollständige Liste aufnehmen oder aus der IC-Tabelle entfernen. |
| RVW-15 | MINOR | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:778-781` | AC-11 prüft nur `scripts/lib/**`; Subprozesse existieren auch in `scripts/*.py` (`scripts/admin-server.py:609,618,644,1243,1625,5799,5805,5830`; `scripts/consistency-check.py:79,83,98`; `scripts/run_role_routing_eval.py:727`). Die Design-Aussage „jeder Framework-Subprozessstart“ ist damit breiter als die Durchsetzung. | AC-Scope auf `scripts/**` ausdehnen oder die Ausnahme `scripts/*.py` mit Begründung in die Allowlist aufnehmen; „kann Temp-Dateien erzeugen“ durch ein prüfbares Kriterium ersetzen. |
| RVW-16 | MINOR | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:282`, `:790-791` | `pytest_basetemp` wird als absoluter, „plattformneutraler“ argv-Wert in `TEST_COMMANDS` eingesetzt, ohne Shell-Quoting zu definieren. Pfade mit Leerzeichen (Windows/macOS) brechen den kanonischen Suite-Aufruf. | Quoting-Regel (z. B. `--basetemp="<path>"`) und einen AC für Pfade mit Leerzeichen ergänzen. |
| RVW-17 | MINOR | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:200-204` gegen `:471-477`; `tests/test_repo_containment_hook.py:213-218` | Abschnitt F sagt, der Test halte „dieses Verhalten bewusst fest“ (Fail-open). Der Test beobachtet den Fail-open gar nicht: er erwartet Exit 2 und erreicht ihn nur, weil das Ziel außerhalb des geadelten Roots liegt — was die Spec später (`:471-477`) korrekt analysiert. | Formulierung in F an die korrekte Analyse angleichen („deckt den Fail-open nicht ab“). |
| RVW-18 | MINOR | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:479-484` | Der Reparatur-Kanal beruht auf „meldet ein Hook `repo-containment.no-root` gehäuft“. Der Hook schreibt nur nach stderr an das Modell; es gibt keine Aggregation/Telemetrie. `check_stale_deployed_hooks` (`scripts/lib/consistency/hook_drift.py:29`) erkennt Versionsdrift unabhängig davon, nicht Häufungen. | Anspruch auf das tatsächlich Vorhandene reduzieren (Versionsdrift-Warnung + Reparaturzeile) oder eine persistente Senke definieren. |
| RVW-19 | MINOR | `rules/2-platform/_wf-sharkord-docker-binaries.md:26-31` | Eine über die 2-platform-Regelschicht (`scripts/lib/rules.py:224-226`) ausgelieferte Workflow-Regel schreibt mehrfach nach `/tmp/...`; der neue Literal-Check (Inventar 7) deckt `rules/2-platform/**` nicht ab. | Entweder Scope-Begründung (projektspezifisch, bewusst ausgenommen) oder Regel migrieren und Check-Scope erweitern. |
| RVW-20 | NIT | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:234-235`, `:338`, `:661` | Zeilenbereiche driften: `OG-TAIL-DEV` beginnt real bei `tests/test_template_slimming_equivalence.py:931` (Spec: 930), `OG-PASS-CODE-REVIEWER` bei `:1023` (Spec: 1022); der Strict-Block wird einmal mit `:1404-1423`, einmal mit `:1404-1426` zitiert. | Auf die Symbol-/Blockgrenzen vereinheitlichen (die Spec erklärt Symbole für maßgeblich — dann konsequent nutzen). |
| RVW-21 | NIT | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:1008-1026` | Die Spec ist nach `_classify` (`scripts/lib/consistency/spec_plan.py:318-323`) ein Plan-Artefakt und erfüllt `REQUIRED_PLAN_SECTIONS` nur, weil sie die Feldnamen als Backtick-Zitate enthält (Substring-Prüfung `:353-354`). Das ist ein bewusster Trick, aber ein Formkompromiss. | Im Plan explizit als akzeptiert festhalten oder die Datei als `-design.md` führen (dann greifen die inhaltlich passenden `REQUIRED_SPEC_SECTIONS`). |

## Faktenprüfung

Stichprobe gegen den echten Code auf Branch `docs/tmp-sink-injection-spec`. 42 Belege geprüft, 35 OK, 7 ABWEICHUNG.

| Beleg | behauptet | verifiziert | Ergebnis |
|---|---|---|---|
| `scripts/lib/repo_containment.py:473-558` | `resolve_effective_repo_containment` | vorhanden, exakt | OK |
| `repo_containment.py:330-357` | `tmp_sink_path_error` | vorhanden | OK |
| `repo_containment.py:360-381` | `tmp_sink_location_error` | vorhanden | OK |
| `repo_containment.py:304-327` | `_resolve_sink_dir` (realpath) | vorhanden | OK |
| `repo_containment.py:641-668` | `resolve_output_dir`/`resolve_work_dir` inkl. `out-outside-tmp-sink` | Funktionen vorhanden; `out-outside-tmp-sink` stammt aus `resolve_out_path` `:671-701` | ABWEICHUNG (Zitat) |
| `repo_containment.py:739-748` | `work_dir_env` setzt `TMPDIR`/`TEMP`/`TMP` | exakt | OK |
| `repo_containment.py:704-736` | `ensure_tmp_sink` löscht nie | exakt (Docstring + Code) | OK |
| `repo_containment.py:290-292` | Symlink-Fehlertext | exakt `must not be a symlink, junction or reparse point` | OK |
| `repo_containment.py:376-380` | System-Temp-/Outside-Texte | exakt | OK |
| `repo_containment.py:582-587` | `tmp-sink.disabled` | exakt | OK |
| `repo_containment.py:36-41` | Framework-Defaults inkl. Cleanup-Modi | exakt | OK |
| `repo_containment.py:561-572` | `TmpSinkError` | exakt | OK |
| `hooks/1-generic/repo-containment-impl.sh:151-154` | `cwd` fehlt ⇒ `WORKDIR=$PWD` | exakt | OK |
| `hooks/...:160-180` | kein `.meta-config/` ⇒ `REPO_ROOT=$WORKDIR` | Funktion `:160-173`, Fallback `:175-180` | OK |
| `hooks/...:347` | relatives Ziel gegen `WORKDIR` | exakt | OK |
| `hooks/...:99-103,105-110,113-126,391-397` | Fail-closed-Stellen | vorhanden; `file_path`-Prüfung exakt `:393-397` | OK |
| `hooks/...:332-368` | `containment_verdict` | exakt | OK |
| `hooks/...:304-314` | Hook berechnet `<root>/<sink>` dort | dort wird nur die Ausgabe geparst; Berechnung in `read_effective_containment` `:186-302` und `:348` | ABWEICHUNG |
| `scripts/lib/config.py:1539-1542` | setzt `TMP_SINK_PATH` (relativ) | gesetzt in `:1542` | OK |
| `config.py:483,496,576-587` | `_validate_repo_containment`, `_fail`, Pfadprüfung | exakt | OK |
| `scripts/lib/consistency/placeholders.py:136` | `TMP_SINK_PATH` registriert | exakt | OK |
| `scripts/lib/backup.py:340` | `TemporaryDirectory()` ohne `dir=` | exakt (Backup-Ziel `:296`) | OK |
| `scripts/lib/providers.py:700` | `provider_hooks_supported` | exakt | OK |
| `config/ai-providers.yaml:252` | `has_hooks: false` (Opencode) | exakt | OK |
| `opencode.json:39-46,47` | `edit`/`bash` deny, `default_agent` | exakt | OK |
| `config/provider-tools.yaml:56-59,61-66` | Deny-Liste, Edit-Scope `.tmp/**` | Key `opencode_primary_edit_allow` `:64-66` | OK |
| `provider_transform.py:477-484,980,985-998` | Konsum + Scope-Bau | exakt | OK |
| `.opencode/agents/orchestrator.md:13-16`; `developer.md:10-16` | generierte Permissions | exakt | OK |
| `.opencode/agents/intern-developer.md` | `edit: deny` | `:14-15` `bash: deny`, `edit: deny` | OK |
| `tests/test_template_report_paths.py:42-48,68-71` | Guard-Scope | exakt | OK |
| `tests/test_repo_containment_hook.py:213-218` | Test hält Fail-open „bewusst“ fest | Test existiert, beobachtet den Fail-open aber nicht | ABWEICHUNG (Deutung) |
| `tests/conftest.py:28,56-65` | Literal-Hinweis, Warnung | exakt (`:55-69`) | OK |
| `tests/fixtures/slimming-golden/{tester,test-executor,e2e-tester,documenter}.md` | eingefrorene Basetemp-Literale | exakt (51 / 33,41 / 73 / 68) | OK |
| `tests/test_template_slimming_equivalence.py:890-929,930-975,1022-1062` | Golden-Blöcke | IDs bei 890/931/1023 | OK (Drift, RVW-20) |
| `tests/test_knowledge_engine.py:19-94,37-49,64-83,89-93,489-546,546` | Rekursionsnetze, Sentinel-Test | exakt | OK |
| `docs/concepts/repo-containment-prison-mode.md:404-439` | §5.5 | exakt | OK |
| §5.5 „schreibt `--basetemp=/tmp/<user>` zwingend vor“ | Pflicht-Literal | Text: „gehört außerhalb, z. B. …“ (`:410-411`) | ABWEICHUNG |
| `.meta-config/project.yaml:194,249,396-402` | Literale + Sink-Block | exakt | OK |
| Fehlertext „expected a relative path …“ | Fehlermatrix | real `must be relative to the project root (absolute and UNC paths are not allowed)` (`:235-236`) | ABWEICHUNG |
| Fehlertext `must not contain a '..' segment` | Fehlermatrix | real `must not contain '..' segments` (`:243`) | ABWEICHUNG |
| `config/routing/reviewers.yaml:28` | `.tmp`-Literal | exakt | OK |
| `reviewers.yaml` wird gerendert (`rules.py:269`) | Renderer existiert | kein Renderer/Konsument; nur `tests/test_review_fleet.py:13` liest die Datei | ABWEICHUNG |

## Vollständigkeitsprüfung Injektions-Inventar

Geprüfte Muster: `tempfile`, `TemporaryDirectory`, `mkdtemp`, `mkstemp`, `NamedTemporaryFile`, `gettempdir`, `TMPDIR`, `mktemp`, `/tmp/`, `%TEMP%`, `.tmp/` in `scripts/**`, `hooks/**`, `snippets/**`, `templates/**`, `agents/**`, `standalone/**`, `rules/**`, `config/**`; `docs/**` nur soweit ausgeliefert.

Bestätigt (in der Spec korrekt erfasst): 18 `/tmp`-Literale in 7 `agents/1-generic`-Templates (exakt die genannten Zeilen), 4 `.tmp`-Sink-Literale in `agents/1-generic`, `config/provider-tools.yaml:65`, `config/routing/reviewers.yaml:28`, `.meta-config/project.yaml:194,249`, `tests/conftest.py:28`, `scripts/lib/backup.py:340`.

Gefundene Lücken (8):

1. `standalone/agents/**` — 23 Treffer (18 `/tmp`, 4 `.tmp/`-Sink-Literale, 1 Code-Hinweis auf `doctor.tmp-sink.disabled`), generiert aus den Templates, aber als Artefakt eingecheckt; kein Injektionspunkt, kein Check-Scope, kein Standalone-Fallback. Siehe RVW-02.
2. `hooks/1-generic/antigravity-json-adapter.sh:167` — `mktemp` schreibt bei jedem Hook-Lauf in den System-Temp. Siehe RVW-08.
3. `scripts/lib/gitignore.py:324-339` — Managed-`.gitignore`-Eintrag aus `effective.tmp_sink_path` (zweiter Gitignore-Mechanismus neben `ensure_tmp_sink_gitignore`). Siehe RVW-09.
4. `scripts/lib/doctor_detectors.py:403-411` — eigener Parse + eigene Validierung von `repo_containment.tmp-sink.path`. Siehe RVW-09.
5. `scripts/*.py` — 12 Subprozess-Aufrufe außerhalb von `scripts/lib/**`, die AC-11 nicht abdeckt. Siehe RVW-15.
6. `rules/2-platform/_wf-sharkord-docker-binaries.md:26-31` — `/tmp`-Schreibziele in einer über die 2-platform-Schicht ausgelieferten Regel. Siehe RVW-19.
7. `scripts/hermes_export.py:26-29` — `/tmp`-Beispiele in einem ausgelieferten CLI-Docstring (niedrige Priorität, keine Agenten-Anweisung).
8. `tests/test_knowledge_engine.py:81`, `tests/test_provider_reactivation_artifacts.py:16,65` — `/tmp`-Hinweise in Fehlertexten; nicht im Check-Scope (niedrige Priorität; nur testseitig).

Nicht gefunden (Negativbefund): `snippets/**` enthält keine Temp-Literale; `templates/**` nur `.tmp` in `templates/configs/project.yaml.example:164-172`; `agents/1-generic/**` enthält keine weiteren `/tmp`-Treffer über die 18 hinaus.

## Entscheidungsvorlage basetemp

**Evidenz korrekt.** `_COPY_IGNORE` enthält `.tmp` (`tests/test_knowledge_engine.py:37-49`), `shutil.copytree(..., symlinks=True)` (`:89-93`), der Fail-loud-Guard bricht ab statt zu rekursieren (`:64-83`), und `test_repo_copy_allows_dest_under_ignored_tmp` (`:545-551`) erlaubt ein Ziel unter `.tmp` ausdrücklich.

**13 Fehlschläge = Ancestor-Kollision, nicht Rekursion.** Bestätigt: `tests/conftest.py:10-11` benennt genau diesen zweiten Effekt (Tests, die die Repo-Wurzel-Erkennung prüfen, finden das echte Repo), und `tests/test_repo_containment_hook.py:215-217` ist ein konkretes Beispiel (`root = tmp_path / "bare"`). Die Bewertung von Option A („löst die Rekursion, nicht die Fehlschläge“) ist damit korrekt; die Zusatzmaßnahmen (Fixture-Sentinel) sind sachlich richtig. Die Option-C-Empfehlung ist begründet: nur ein Basetemp außerhalb des Repo-Baums hält `tmp_path` aus dem Ancestor-Bereich, und sie macht die Ausnahme explizit, statt sie zu verstecken.

**Keine stille Umkehrung: ja**, aber nur unter der Bedingung, dass Q1 mit „Default an“ beantwortet wird. §5.5 verlangt inhaltlich „Basetemp außerhalb des Arbeitsbaums“ (`docs/concepts/repo-containment-prison-mode.md:410-411`); Option C hält das ein und macht nur die Form literal-frei und konfigurierbar. Die in Q1 angebotene Alternative „Default aus“ wäre dagegen eine stille Umkehrung, weil dann `<sink>/pytest` der Default würde — siehe RVW-06. §5.5 bleibt inhaltlich bestehen; die Spec sollte das ausdrücklich an die Q1-Antwort koppeln.

## Gate-Status

Es wurde kein Approval-Marker gesetzt. Die Spec bleibt Entwurf. Plan und Implementierung sind erst nach Nutzerfreigabe zulässig; dieses Review ist eine Analyse, keine Freigabe.

## Freigabe-Empfehlung

Vor einer Freigabe müssen die BLOCKER aufgelöst werden:

1. RVW-01 — Resolver-Vertrag bei `tmp-sink.enabled: false` eindeutig und widerspruchsfrei zu Fehlermatrix und `TMP_SINK_PATH`-Zusage.
2. RVW-02 — `standalone/agents/**` als Injektionspunkt/Check-Scope aufnehmen und Standalone-Fallback für `{{TMP_SINK_PATH}}` entscheiden.
3. RVW-03 — `config/routing/reviewers.yaml` aus Injektionspunkt 9 und AC-02 entfernen oder Renderer/Konsument belegen.
4. RVW-04 — `cwd`-Verhalten für Antigravity (leerer Wert) definieren, Q5 vor Freigabe entscheiden, AC-04 ergänzen.

Zusätzlich vor Freigabe zu adressieren (MAJOR): RVW-05 (ACs nicht von offenen Fragen abhängig machen), RVW-06 (Q1 nicht als §5.5-Umkehr), RVW-07 (neue Hook-ACs basetemp-unabhängig), RVW-08 (Adapter-`mktemp`), RVW-09 (zwei ungenannte Sink-Konsumenten), RVW-10 (§5.5-Wortlaut), RVW-11 (Fehlertexte wörtlich), RVW-12 (Basis relativer Ziele belegen).

Nach Auflösung von 1–4 und Einarbeitung der MAJOR-Punkte ist ein `APPROVED` mit anschließendem Übergang in `quality_pipelines.concept-driven-dev` (Plan) vertretbar; die Design-Substanz (ein Resolver, relative/absolute Trennung, fail-closed Hook, Option C) bleibt dabei unverändert.

---

## Re-Review (Iteration 2, 2026-10-24)

Fokussiertes Re-Review der Revision 2 (`docs/specs/2026-10-24-tmp-sink-injection-spec.md`, 1468 Zeilen). Prüfauftrag: Schließung der vier BLOCKER aus Iteration 1, Regressionscheck der acht MAJOR-Lücken, Formregeln, keine neue Unschärfe. Kein Voll-Review; die Design-Substanz wurde nur insoweit geprüft, wie sie die Blocker berührt. Alle Zeilenangaben beziehen sich auf Revision 2.

### Verdict

**CHANGES_REQUESTED** — Die vier BLOCKER sind inhaltlich und belegbar geschlossen (4/4 CLOSED); der Regressionscheck zeigt keine offene MAJOR-Lücke aus Iteration 1. Revision 2 führt jedoch mit RVW2-01 eine neue MAJOR-Inkonsistenz ein: der Agenten-Env-Pin-Block soll `export TMPDIR=<relativer Sink>` setzen, während die Formtabelle und AC-12 für `TMPDIR`/`TEMP`/`TMP` absolute Werte verlangen. Dieser Konflikt ist eine offene Designentscheidung (absolute Form ist move-unsicher im gerenderten Artefakt, relative Form ist cwd-abhängig) und vor einer Freigabe zu entscheiden. Die übrigen neuen Findings sind MINOR/INFO und blockieren nicht.

### Blocker-Status

| RVW-ID | Status | Beleg (Datei:Zeile in der Spec) | Anmerkung |
|---|---|---|---|
| RVW-01 | CLOSED | `docs/specs/2026-10-24-tmp-sink-injection-spec.md:405-421`, `:682`, `:845`, `:897-899`, `:1083-1099` | Die Semantik ist jetzt eindeutig: `resolve_tmp_paths` wirft nicht wegen eines deaktivierten Sinks (`enabled=False`, `absolute=None`, `env={}`), wirft aber weiterhin bei Config-Fehlern (`tmp-sink.invalid-path`, `tmp-sink.system-temp-exception`); werfend sind die Schreib-/Verbrauchs-APIs (`resolve_output_dir`, `resolve_work_dir`, `resolve_out_path`, `tmp_env`). Design-Kern, IC-Tabelle, IC-01, Fehlermatrix, Datenfluss und AC-23/AC-24/AC-25 stimmen überein. Rest: ADR-07 formuliert „ausschließlich" zu eng (RVW2-02). |
| RVW-02 | CLOSED | `:484` (Injektionspunkt 11), `:319-343` (Abschnitt K), `:1101-1113` (AC-26/AC-27), `:1335-1337` (IC-15) | Injektionspunkt 11 enthält Ist/Soll/Wer/Wann/Fehlerverhalten, AC-26 und AC-27 sind daraus abgeleitet. Zahlen gegen `standalone/agents/**` nachgeprüft und exakt bestätigt: 18 `/tmp`-Treffer in 7 Dateien mit den genannten Zeilen, 4 `.tmp/`-Sink-Literale (`ai-security-guardian.md:96`, `app-lifecycle-governor.md:90`, `prompt-governor.md:106`, `security-auditor.md:201`), 12 Platzhalter-Notizen in `meta-doctor.md`, `meta-optimizer.md`, `agent-meta-manager.md`. Die Standalone-Ursachen (`standalone.py:254-282`, Safety-Net `:313-319`) und das Drift-Gate (`cli_commands.py:496-508`) sind korrekt zitiert. |
| RVW-03 | CLOSED | `:46-50`, `:209-218`, `:487`, `:952-957`, `:1278-1286` | Die Einordnung ist belegt und die unbelegte Renderer-Behauptung ist entfernt: einziger Leser von `config/routing/reviewers.yaml` ist `tests/test_review_fleet.py:13` (`ROUTING_FILE`); `rules.py:269` liegt in `_merged_rule_vars` und speist Regel-Templates. Die Datei ist als „—"-Zeile (Test-Fixture, keine Injektion) aus dem Inventar genommen, AC-02 prüft nur noch die vier Templates, ADR-10 nennt die Voraussetzung für eine spätere Injektion. |
| RVW-04 | CLOSED | `:594-624` (Vertrag), `:696-697` (Fehlermatrix), `:903-925` (Datenfluss), `:1115-1124` (AC-28/AC-29), `:1252-1264` (ADR-08) | Die vier Fälle sind explizit definiert (Key fehlt, Wert leer, Symlink, relativ) und der Leerwert ist über AC-28/AC-29 abgedeckt. Payload-Evidenz geprüft: der Adapter mappt `Cwd` → `cwd` (`antigravity-json-adapter.sh:111`) und setzt `out['cwd'] = cwd` mit `''`-Fallback (`:122-127`, Zuweisung `:134`); der Hook behandelt `''` wie „fehlt" (`repo-containment-impl.sh:151-154`). Anker-Sicherheit: der Anker stammt aus dem Zielpfad, geprüft wird genau der Pfad, der geschrieben wird (`containment_verdict` `:347`); ein Angreifer kann damit kein Repo-Root „verschieben", weil ein von ihm angelegtes `.meta-config/` nur Writes in seinem eigenen Verzeichnis erlaubt (kein Zugewinn gegenüber dem Verzeichnisbesitz). Die verbleibende Vergrößerung — bei leerem `cwd` kann ein fremdes Projekt zum Root werden — ist in ADR-08 `:1262-1264` als dieselbe Vertrauensannahme offengelegt; sie ist kein Blocker, aber ungetestet (RVW2-07). |

**Regressionscheck der acht MAJOR-Lücken aus Iteration 1 (alle eingeordnet):**

- RVW-05 (ACs vs. offene Fragen): Q1, Q2, Q4, Q5, Q7, Q8, Q9 sind entschieden, Q3/Q6/Q10/Q11 ohne AC-Abhängigkeit (`:1393-1433`). Rest: Q6 ist über das Allowlist-Schema mit `owner` teilweise vorweggenommen (RVW2-07), Q10 berührt AC-28 (RVW2-06).
- RVW-06 (Q1 als §5.5-Umkehr): ausdrücklich als Nicht-Ziel ausgeschlossen (`:137-141`), Q1 auf „Default an" entschieden (`:571-575`, `:1396-1399`).
- RVW-07 (neue Hook-ACs basetemp-abhängig): Vorbedingung „Fixture außerhalb des Repo-Baums" in AC-03/AC-04/AC-05/AC-07 (`:960-964`, `:968`, `:974`, `:986`), Risiko R12 (`:1173`).
- RVW-08 (Adapter-`mktemp`): Injektionspunkt 12 (`:485`), Abschnitt M (`:355-362`), AC-30 (`:1126-1130`), ADR-11 (`:1288-1294`). `mktemp`/`trap` in `antigravity-json-adapter.sh:167-168` bestätigt.
- RVW-09 (zwei ungenannte Sink-Konsumenten): Injektionspunkte 9/10 (`:482-483`), Abschnitt L (`:345-353`), IC-16 (`:1338-1340`), AC-31/AC-32 (`:1132-1140`). Beide Funktionen im Code bestätigt (`gitignore.py:324-339`, `doctor_detectors.py:403-411`).
- RVW-10 (§5.5-Wortlaut): Problem Punkt 3 korrigiert (`:51-59`), Abschnitt B (`:177-186`).
- RVW-11 (Fehlertexte wörtlich): Fehlermatrix `:684-692`; gegen `repo_containment.py:235-236` (`must be relative to the project root (absolute and UNC paths are not allowed)`) und `:243` (`must not contain '..' segments`) verifiziert.
- RVW-12 (Basis relativer Ziele): Entscheidung „Prüf-Ort = Schreib-Ort" (`:253`, `:612-618`), AC-33 prüft den realen Zielpfad (`:1142-1146`), Annahme als R11 geführt (`:1172`).

Die acht Inventar-Lücken aus der Vollständigkeitsprüfung sind ebenfalls vollständig zugeordnet: 1 → Injektionspunkt 11, 2 → 12, 3 → 9, 4 → 10, 5 → Abschnitt N/Inventar 3 + AC-11 (`:1007-1014`), 6 → Abschnitt N (Ausnahme), 7 → Abschnitt N (Ausnahme), 8 → Abschnitt N (Ausnahme). Keine Lücke bleibt unerwähnt.

**Formregeln:** eingehalten. Kein Approval-Marker, die Spec trägt ausschließlich die bestehende Entwurfszeile (`:3`). Keine `TODO`/`TBD`/`<platzhalter>`-Platzhalter, keine Zeile, die nur `...` enthält, kein leeres `Interfaces:`. Alle Pflicht-Überschriften vorhanden: `## Problem`, `## Ziel`, `## Nicht-Ziele`, `## Interface Contracts`, `## Datenfluss`, `## Acceptance Criteria`, `## Offene Fragen`, `## Trace-Anker` (plus die plan-seitigen Feldnamen in der „Formalen Einordnung"). Trace-Anker `spec-id: SPEC-tmp-sink-injection` in `## Trace-Anker` (`:1466-1468`).

**Traceability-Prüfmatrix:** 37 ACs, 20 ICs, 13 numerierte Injektionspunkte plus 4 begründete Ausnahmen; keine doppelten Punktnummern. Jede AC hat einen IC-Bezug. Lücken (Stand Iteration 2): IC-03 ohne AC-Bezug, `resolve_out_path` ohne IC-Zeile, AC-15 einem Injektionspunkt zugeordnet (RVW2-04).

### Neue Findings

| ID | Severity | Fundstelle | Befund | Geforderte Änderung |
|---|---|---|---|---|
| RVW2-01 | MAJOR | `:476` gegen `:452`, `:774`, `:1017-1020` | Injektionspunkt 3 fordert für Agenten-Bash einen Prompt-Block `export TMPDIR=<relativer Sink>`. Die Formtabelle verlangt für `TMPDIR`/`TEMP`/`TMP` **absolut** („Env-Werte müssen absolut sein"); AC-12 prüft absolute Werte; der Toolchain-Block setzt `<absolute>`. Ein relativer `TMPDIR` wird gegen das jeweilige Prozess-cwd aufgelöst und lenkt Temp-Writes bei abweichendem cwd fehl. Gleichzeitig ist die absolute Form im gerenderten Agenten-Artefakt move-unsicher (ADR-02/IC-13) — die Spec entscheidet diesen Zielkonflikt nicht. | Form von `TMP_SINK_ENV_PIN_BLOCK` festlegen: absolut mit dokumentierter Move-Unsicherheit als benannte Ausnahme zu IC-13, oder zur Laufzeit relativ zum Repo-Root aufgelöst (z. B. Shell-Präfix mit Projekt-Root-Ermittlung). Entscheidung plus AC ergänzen. |
| RVW2-02 | MINOR | `:1243-1245` gegen `:416-419`, `:845`, `:1301-1304` | ADR-07 sagt „Werfend bleiben ausschließlich die Schreib-APIs"; Design-Kern und IC-01 erlauben zusätzlich `TmpSinkError` für Config-Fehler. Die Aussage ist zu absolut und widerspricht der eigenen IC-Tabelle. | ADR-07 um „(außer Config-Fehlern: `tmp-sink.invalid-path`, `tmp-sink.system-temp-exception`)" ergänzen. |
| RVW2-03 | MINOR | `:796` gegen `:600-608`, `:696-697` | Die Threat-Model-Risikozeile nennt „`cwd` fehlt/leer und Ziel relativ" als Fail-open. Vertrag und Fehlermatrix definieren genau diesen Fall als Exit 2 (`repo-containment.no-root`). Die Zeile ist aus Revision 1 stehengeblieben. | Zeile ersetzen, z. B. „Anker aus dem Zielverzeichnis kann bei leerem `cwd` ein fremdes Projekt als Root wählen". |
| RVW2-04 | MINOR | `:1351-1386`; `:1089-1093`; `:1367` | IC-03 (relative Validierung auch bei `enabled=False`) hat keinen AC-Bezug in der Traceability; AC-24 nutzt `resolve_out_path`, für den es keine IC-Zeile gibt; AC-15 (Config-Validierung) ist Punkt 2 zugeordnet, obwohl es kein Injektionspunkt ist. | IC-03 einer AC zuordnen (z. B. AC-23/AC-25), IC-Zeile für `resolve_out_path` ergänzen, AC-15 in der Punktspalte mit „—" führen. |
| RVW2-05 | MINOR | `:861` | Die Signatur von `_tmp_sink_gitignore_entry` bleibt `(repo_containment_cfg: dict \| None) -> str \| None`, während die Beschreibung „Eingabe künftig `TmpPaths` statt eigener Resolver-Aufruf" verlangt. | Signatur auf `(paths: TmpPaths) -> str \| None` ändern oder eine Adapter-Funktion explizit benennen. |
| RVW2-06 | MINOR | `:1115-1119` gegen `:1425-1430`, `:1175`; `hooks/1-generic/repo-containment-impl.sh:391-397` | AC-28 heißt „Leerer `cwd` blockiert In-Project-Writes nicht (Antigravity)", prüft aber nur die Ankerwahl mit synthetischem `file_path`. Q10/R14 halten fest, dass der Adapter `FilePath` nicht auf `file_path` mappt; real blockt der Hook dann am fehlenden `file_path`. Der AC-Titel verspricht mehr, als der Test zeigt. | Titel/Scope auf „Ankerwahl bei leerem `cwd`" zuschneiden oder AC-28 ausdrücklich als Hook-Unit-Test mit Adapter-Vorbedingung Q10 kennzeichnen. |
| RVW2-07 | INFO | `:868` gegen `:1413-1415`; `:1262-1264` | Das Allowlist-Schema enthält `owner`, obwohl Q6 `owner`/`expires` ausdrücklich offenlässt (nur additiv, kein AC-Bruch). Die Anker-Regel erlaubt bei leerem `cwd` Writes in jeden Baum mit `.meta-config/` (fremdes Projekt); ADR-08 dokumentiert die Vertrauensannahme, kein AC prüft sie. | Q6-Formulierung an das Schema angleichen oder `owner` als optional markieren; optional einen AC für den Cross-Projekt-Fall ergänzen. |

### Gate-Status

Es wurde kein Approval-Marker gesetzt; die Spec bleibt Entwurf (`:3`). Dieses Re-Review ist eine Analyse, keine Freigabe. Plan und Implementierung bleiben gesperrt, bis RVW2-01 entschieden und die MINOR-Punkte eingearbeitet sind. Das Iteration-1-Verdict oben bleibt unverändert Teil der Historie.
