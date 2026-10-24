# Tmp-Sink-Injektion — Spec

> Status: Entwurf
>
> **Revision 3 — Nutzerentscheidungen (2026-10-24):** Revision 3 besteht aus zwei Teilen — diesem
> Block und dem darunter folgenden Re-Review-Iteration-2-Block (inhaltlich unverändert gültig).
> Festgelegt sind vier Fragen:
>
> - **Q3 — Toolchain-Caches per Opt-in erlaubt.** Config-Key
>   `repo_containment.tmp-sink.system-temp-exception.toolchain-caches` (Default `false`, YAML plural
>   kebab-case; das Python-Feld bleibt `SystemTempException.toolchain_cache`). Nur bei `true` **und**
>   `enabled: true` pinnt der Builder `PIP_CACHE_DIR=<abs>/cache/pip` und
>   `npm_config_cache=<abs>/cache/npm` in den Env-Pin-Block; `tmp_env` bleibt cache-neutral.
>   Begründung: Default aus bricht keine Toolchain, und ein In-Repo-Cache wächst in Backup/CI/Submodul,
>   wird von `cleanup: on-sync` gelöscht und zeigt nach einem Repo-Umzug bis zum Re-Sync auf einen toten
>   Pfad — deshalb Opt-in, nicht Default (ADR-13, AC-38).
> - **Q6 — Allowlist-Schema ist strikt.** `.meta-config/temp-literal-allowlist.yaml` verlangt `path`,
>   `pattern` und `reason`, optional `owner`; `expires` ist **kein** Schema-Teil. Ein Eintrag ohne
>   `reason` oder mit einem nicht unterstützten Feld unterdrückt die Meldung nicht.
>   Begründung: `expires` bräuchte einen Ablauf-Job, den es nicht gibt; eine Pseudo-Ablaufsemantik wäre
>   eine stille Ausnahme (ADR-14, AC-39).
> - **Q10 — Der Antigravity-Adapter mappt `args.FilePath` → `tool_input.file_path`.** Begründung:
>   `ARG_KEY_MAP` (`antigravity-json-adapter.sh:111`) enthält nur `CommandLine`/`Cwd`; `FilePath` fällt
>   unverändert durch, der Hook sucht `tool_input.file_path` (`repo-containment-impl.sh:391-397`) und
>   blockt damit jeden Antigravity-Write fail-closed (ADR-15, AC-40).
> - **Q11 — §5.5 nennt `PYTEST_BASETEMP`/den Config-Key statt eines `/tmp`-Literals.** Die Pflichtregel
>   („Basetemp NIE im Arbeitsbaum") bleibt wörtlich erhalten; nur die Literal-Verbreitung im Regeltext
>   verschwindet. Begründung: der Regeltext darf nicht selbst die Form tragen, die er verbietet
>   (ADR-16, AC-41).
>
> Status bleibt Entwurf, kein Approval.
>
> **Revision 3 — Re-Review Iteration 2 (2026-10-24):** Befunde aus
> `docs/reviews/2026-10-24-tmp-sink-injection-spec-review.md` (Abschnitt „Re-Review (Iteration 2)")
> eingearbeitet: RVW2-01 ist **entschieden** — der Env-Pin-Block setzt `TMPDIR`/`TEMP`/`TMP`
> **absolut** (wie `TmpPaths.env`), weil diese Variablen prozess-global sind und von Kindprozessen
> gegen **deren** `cwd` interpretiert werden; Template-Beispiele bleiben relativ
> (`{{TMP_SINK_PATH}}`, gültig ab Repo-Root). Die daraus folgende Move-Unsicherheit des gerenderten
> Blocks ist als benannte Ausnahme (ADR-12, zu ADR-02/IC-13) mit Laufzeit-Selbstprüfung ausgewiesen.
> Zusätzlich: ADR-07 präzisiert (RVW2-02), Threat-Model-Zeile korrigiert (RVW2-03), Traceability
> repariert (RVW2-04), `_tmp_sink_gitignore_entry`-Signatur (RVW2-05), AC-28-Scope (RVW2-06) und
> `owner` als optionales Allowlist-Feld (RVW2-07). Status bleibt Entwurf, kein Approval.
>
> **Revision 2 (2026-10-24):** Review-Befunde aus
> `docs/reviews/2026-10-24-tmp-sink-injection-spec-review.md` (CHANGES_REQUESTED, 4 BLOCKER)
> eingearbeitet: eine Resolver-Semantik (nicht werfend, Schreib-APIs werfend), `standalone/agents/**`
> als Injektionspunkt 11, `config/routing/reviewers.yaml` als Test-Fixture aus dem Scope genommen,
> `cwd`-Regel ohne Provider-Selbstausschluss (Anker aus dem Zielpfad); Q1/Q2/Q4/Q5/Q7/Q8/Q9 entschieden.
> Status bleibt Entwurf, kein Approval.
>
> **Betroffener Bereich:** `repo_containment.tmp-sink` (Resolver, Sync-Validierung, Template-Variablen,
> PreToolUse-Hook `repo-containment`, Backup-Staging, Opencode-Permission-Scope, Test-/Golden-Infrastruktur).
> **Umfang:** Eine Quelle der Wahrheit für den Scratch-Pfad, vollständige Injektion an allen
> Schreib-/Temp-Punkten, Default „im Repo", fail-closed statt Adeln des Arbeitsverzeichnisses,
> entliteralisiertes `pytest --basetemp` (plattformneutral, konfiguriert). Revision 3 ergänzt vier
> Nutzerentscheidungen: Toolchain-Cache-Opt-in (Q3), striktes Allowlist-Schema ohne `expires` (Q6),
> Adapter-Mapping `args.FilePath` → `tool_input.file_path` (Q10) und einen literal-freien
> §5.5-Regeltext, der auf `PYTEST_BASETEMP`/den Config-Key verweist (Q11).
> **Nicht in diesem Dokument:** Implementierung, Code-Änderungen, Commits, `sync.py`-Läufe, Plan.
> **Belege:** Zeilenangaben beziehen sich auf Branch `docs/tmp-sink-injection-spec`, Stand 2026-10-24.
> Maßgeblich sind die Symbole, nicht die Zeilennummern.
> **Terminologie:** „Convention boundary" / „security boundary" exakt wie in
> `.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`.
> **Trace-Anker:** `spec-id: SPEC-tmp-sink-injection`

---

## Problem

Der Scratch-Sink ist konfigurierbar, aber **nicht die einzige Quelle der Wahrheit**. Neben dem
konfigurierten Pfad existieren heute mehrere konkurrierende, hartkodierte Wahrheiten. Ein Agent, der
diesem Repository folgt, bekommt damit widersprüchliche Anweisungen: eine konfigurierbare und viele
fest verdrahtete.

1. **18 System-Temp-Literale in 7 generischen Templates.** Alle sind Schreibziele in Bash-Beispielen
   (`docker logs … > /tmp/…`, `tee /tmp/run-$RANDOM.log`, `npm run e2e > /tmp/e2e.log`):
   `agents/1-generic/developer.md:47,50,154,163` (4 Treffer),
   `code-reviewer.md:221,229`, `tester.md:71,74,141,143`, `validator.md:76,79`,
   `docker.md:128,130`, `devops-engineer.md:202,204`, `e2e-tester.md:154,156` (je 2).
   Dieselben Literale stehen als **eingecheckte Artefakte** in `standalone/agents/**` (18 `/tmp`-Treffer in
   7 Dateien), weil der Standalone-Export aus denselben Templates rendert (Abschnitt K) — dort sind sie
   kein Rendering-Zufall, sondern ausgelieferter Text.
2. **4 Sink-Literale statt Platzhalter, plus eine Routing-Notiz.** `ai-security-guardian.md:111`,
   `app-lifecycle-governor.md:100`, `prompt-governor.md:120`, `security-auditor.md:217` schreiben
   `.tmp/<role>-<topic>.md` fest, obwohl der Platzhalter `{{TMP_SINK_PATH}}` bereits existiert und an
   anderer Stelle korrekt genutzt wird (`agents/1-generic/meta-doctor.md:35,36`,
   `meta-optimizer.md:43,75,91`, `agent-meta-manager.md:304`). Ein konfigurierter Sink (`path: scratch/out`)
   würde dort ins Leere zeigen. `config/routing/reviewers.yaml:28` nennt `.tmp/…` in `notes:`; diese Datei
   hat **keinen Renderer und keinen Produktions-Konsumenten** — einziger Leser ist
   `tests/test_review_fleet.py:13` (`ROUTING_FILE`), und `scripts/lib/rules.py:269` speist
   `_merged_rule_vars` für Regel-Templates, nicht Routing-YAML. Sie ist deshalb aus dem Injektions-Scope
   ausgenommen (Abschnitt D, ADR-10).
3. **Literal-Verbreitung bei inhaltlich korrekter Regel.** §5.5
   (`docs/concepts/repo-containment-prison-mode.md:404-439`) verlangt inhaltlich „Der pytest-Basetemp
   darf NIE im Arbeitsbaum liegen" und nennt `--basetemp=/tmp/<user>` ausdrücklich als **Beispiel**
   („z. B.", `:410-411`, mit dem Zusatz „oder `TMPDIR` entsprechend"). Literal durchgereicht wird es im
   kanonischen Aufruf (Punkt 5, `:428-429`) und in den ausgelieferten Werten
   (`.meta-config/project.yaml:194` `TEST_COMMANDS`, `:249` `CODE_QUALITY_RULES`). Die Regel ist damit
   inhaltlich richtig; das Problem ist die **Literal-Verbreitung**, nicht ein Regelwiderspruch. Die
   Begründung ist belegt (Plattenvorfall 2026-09-19/20: 16 GB, 432.138 Einträge; 13 zusätzliche
   Testfehlschläge 2026-09-20).
4. **Vage Temp-Anweisungen ohne Pflicht-Ort.** 13 Rollen (12 SE-Rollen + `test-executor`) sagen „write … to a temporary file" /
   „temp → rename" / „scratch/output path", ohne den Sink zu nennen (Details in
   [Ist-Zustand](#ist-zustand-verifiziert-2026-10-24) Punkt E). Der Agent muss raten — und rät
   typischerweise auf den System-Temp.
5. **Ein fail-open-Pfad im Hook — und ein leerer `cwd` beim zweiten Hook-Provider.**
   `hooks/1-generic/repo-containment-impl.sh:151-180` adelt das Arbeitsverzeichnis des Hook-Prozesses zum
   Repo-Root, wenn der Payload kein `cwd` liefert oder oberhalb kein `.meta-config/` liegt. Ein `Write`
   nach `/tmp/x` bei `cwd=/tmp` ist dann „innerhalb des Roots" und wird erlaubt (`exit 0`) — obwohl
   derselbe Hook an allen anderen Stellen bewusst fail-closed ist. Gleichzeitig kann der
   Antigravity-Adapter `cwd` als **leere Zeichenkette** liefern
   (`hooks/1-generic/antigravity-json-adapter.sh:122-127`: `d.get('cwd')` → `workspacePaths[0]` →
   `args.Cwd` → `''`). Eine Regel „`cwd` fehlt ⇒ Exit 2" würde diesen Provider pauschal schreibunfähig
   machen. Die Revision ersetzt sie durch eine Anker-Regel (Abschnitt F, ADR-08).
6. **Der hook-lose Provider hat keinen datengetriebenen Scope.** `config/ai-providers.yaml:252`
   (`has_hooks: false`) schaltet die Runtime-Durchsetzung für Opencode ab; der einzige vorhandene
   Schreib-Scope `config/provider-tools.yaml:61-66` enthält das Literal `.tmp/**` und kennt den
   konfigurierten Sink-Pfad nicht.
7. **Tooling schreibt am Sink vorbei — und parst die Config erneut.** `scripts/lib/backup.py:340` legt
   sein Staging-Verzeichnis per `tempfile.TemporaryDirectory()` ohne `dir=` im System-Temp an, obwohl das
   Backup-Ziel im Repo liegt. `scripts/lib/repo_containment.py:739-748` (`work_dir_env`) wird nur an zwei
   Stellen genutzt (`scripts/lib/context_report.py:340`, `scripts/lib/meta_optimizer.py:1508`). Zwei
   weitere Konsumenten lesen den Sink **unabhängig** vom Resolver: der Managed-`.gitignore`-Block
   (`scripts/lib/gitignore.py::_tmp_sink_gitignore_entry`, eigener
   `resolve_effective_repo_containment`-Aufruf) und der Doctor-Check
   (`scripts/lib/doctor_detectors.py::_sink_hits`, eigener `get_path` plus eigene Validierung).

**Kern des Problems:** Es gibt keinen Ort, an dem „der temporäre Ordner" bestimmt wird, den alle
Konsumenten zwingend benutzen. Es gibt einen Resolver für Tool-Output und daneben viele Ausnahmen sowie
zwei Stellen, die die Config erneut selbst interpretieren.


---

## Ziel

**Ein Satz:** `repo_containment.tmp-sink.path` ist die einzige konfigurierbare Quelle; daraus wird
**einmal** ein aufgelöster Pfad berechnet und an **jedem** Schreib-, Temp-, Hook-, Backup-, Permission-,
Standalone- und Test-Punkt injiziert — mit „in der Regel im Repo" als Default und fail-closed statt
Adelung.

Konkret:

- **Eine Quelle:** `scripts/lib/tmp_paths.py::resolve_tmp_paths(project_root, config) -> TmpPaths`
  liefert `relative` (move-safe, für Templates), `absolute` (realpath, für Env/Backup/Diagnose; `None`
  bei deaktiviertem Sink), `enabled`, `system_temp_exception`, `pytest_basetemp`, `env`. Alle anderen
  Stellen lesen dieses Ergebnis oder leiten daraus ab; keine Stelle parst `repo_containment` erneut
  (auch der Managed-`.gitignore`-Block und der Doctor-Check nicht).
- **Nicht werfend, wo nichts geschrieben wird:** `resolve_tmp_paths` wirft **nicht**, nur weil der Sink
  deaktiviert ist; es liefert `enabled=False`. Werfend sind ausschließlich die **Schreib**-APIs
  `resolve_output_dir` / `resolve_work_dir` / `resolve_out_path` (bestehendes `TmpSinkError`-Verhalten)
  und `tmp_env` (kein Env-Pin ohne Sink). Begründung: ADR-07.
- **Vollständige Injektion:** Template-Platzhalter, `TEST_COMMANDS`/`CODE_QUALITY_RULES`,
  Subprozess-Env (`TMPDIR`/`TEMP`/`TMP`, absolut), Backup-Staging, Hook-Pfadauflösung und -Meldungen,
  Opencode-Edit-Scope, Guards/Goldens, Managed-`.gitignore`, Doctor-Check, Standalone-Export — je mit
  definiertem Fehlerverhalten ([Injektionspunkte](#injektionspunkte-vollständiges-inventar)).
- **„In der Regel im Repo":** Default-Sink bleibt `.tmp` im Projekt-Root; der Agent schreibt nicht
  außerhalb. System-Temp ist nur als **eng begrenzte, dokumentierte, konfigurierte** Ausnahme zulässig
  und niemals als Literal im gerenderten Text.
- **Fail-closed mit Anker:** Kein Projekt-Root auflösbar ⇒ Block (Exit 2) mit stabiler Fehlerklasse,
  nicht „Arbeitsverzeichnis wird Root". Fehlt `cwd` (oder ist es leer), wird **nicht** `$PWD` geadelt,
  sondern der Zielpfad selbst zum Anker, sofern er absolut ist; ein relatives Ziel ohne `cwd` ist nicht
  auflösbar und blockt. Damit bleibt ein Provider mit leerem `cwd` schreibfähig (ADR-08).
- **`enabled: false` bleibt wirksam**, aber nur für ein Projekt, dessen Root tatsächlich auflösbar ist.
- **Provider-agnostisch:** Jede Durchsetzung läuft über Config-Keys/Capability-Flags. Keine
  `if provider == "Name"`-Verzweigung; was ohne Hook nicht durchsetzbar ist, wird als WARNING sichtbar
  und bleibt advisory.


---

## Nicht-Ziele

- **Kein OS-Sandboxing.** Keine Container, Mount-Namespaces, seccomp/Landlock, ACLs oder dedizierter
  OS-User. Die Durchsetzung bleibt eine **Convention boundary** (Definition siehe
  `docs/concepts/repo-containment-prison-mode.md:38-40`).
- **Keine Umkehr der Default-AN-Policy.** `repo_containment.enabled` bleibt per Framework-Default `true`
  (`scripts/lib/repo_containment.py:36`); `tmp-sink.enabled` bleibt `true` (`:37`).
- **Keine inhaltliche Umkehr von §5.5.** Der Basetemp bleibt außerhalb des Arbeitsbaums
  (`docs/concepts/repo-containment-prison-mode.md:410-411`). Die in Revision 1 als Alternative genannte
  Variante „`system-temp-exception` per Default aus" ist **nicht** Teil dieser Spec: sie würde den
  Default-Basetemp unter `<sink>/pytest` legen und damit §5.5 inhaltlich umkehren. Q1 ist auf „Default
  an" entschieden; eine Umkehr bräuchte eine eigene Nutzerentscheidung und einen eigenen Änderungsantrag.
  Die in Q11 (ADR-16) entschiedene Ersetzung des `/tmp`-Literals im Regeltext durch den Verweis auf
  `PYTEST_BASETEMP` bzw. den Config-Key `system-temp-exception` ist ausdrücklich **keine** inhaltliche
  Umkehr: die Pflichtregel „Der pytest-Basetemp darf NIE im Arbeitsbaum liegen" bleibt wörtlich erhalten.
- **Kein Test-only-Bypass im Produktionscode.** Fail-closed-Hook-Tests erzwingen ihre Isolation im Test
  (Fixture außerhalb des Repo-Baums, siehe AC-03/AC-05/AC-07/AC-28/AC-29), nicht über ein neues
  Root-Override-Feld im Hook.
- **Keine Änderung an `orchestrator-guard` / `branch-guard`.** Die Hooks koexistieren unverändert.
- **Keine Umleitung der Toolchain-Caches per Default.** pip/npm bleiben im Nutzer-Cache außerhalb des
  Repos; ein In-Repo-Cache ist nur als ausdrückliches, sichtbares Opt-in zulässig
  (`system-temp-exception.toolchain-caches: true`, Q3/ADR-13). `docker` wird weiterhin nicht umgeleitet —
  siehe [Toolchain-Ausnahme](#toolchain-ausnahme).
- **Keine Implementierung in diesem Dokument.** Keine Code-Änderungen, keine Commits, kein Sync-Lauf.
- **Keine Migration bestehender `.tmp`-Inhalte.** Kein Umzug, kein Löschen, keine Cleanup-Semantik-
  Änderung (`cleanup: manual` bleibt Default).
- **Kein Provider-Namens-Branching** und keine providerspezifische Sonderlogik in Templates oder
  Resolvern.
- **Kein Umbau der Test-Suite-Architektur** über die in
  [Entscheidungsvorlage](#entscheidungsvorlage-pytest---basetemp) genannten Maßnahmen hinaus.
- **Kein Umbau des `TMP_SINK_PATH`-Vertrags** für Templates: der Platzhalter bleibt die *relative* Form.

---

## Ist-Zustand (verifiziert, 2026-10-24)

### A — Soll-Zustand ist bereits dokumentiert und implementiert

| Baustein | Beleg |
|---|---|
| Schreiben nur Repo-Root + `.tmp/` | `docs/concepts/repo-containment-prison-mode.md:19-23` |
| Sink-Konfiguration | `.meta-config/project.yaml:396-402` (`repo_containment.tmp-sink.{enabled,path,gitignore,cleanup}`), Schema `config/project-config.schema.json` |
| Framework-Defaults | `scripts/lib/repo_containment.py:36-41` |
| Resolver | `scripts/lib/repo_containment.py:473-558` `resolve_effective_repo_containment` |
| Pfad-Validierung | `:330-357` `tmp_sink_path_error`, `:360-381` `tmp_sink_location_error` (Sink darf nicht ins System-Temp auflösen) |
| Verzeichnisauflösung | `:304-327` `_resolve_sink_dir` (realpath, Link-Schutz) |
| Provisionierung | `:704-736` `ensure_tmp_sink`, `:795` `ensure_tmp_sink_gitignore` |
| Ausgabe-Pfad-API | `:641-668` `resolve_output_dir` / `resolve_work_dir` (kein System-Temp-Fallback; `TmpSinkError` mit `tmp-sink.disabled`, `tmp-sink.invalid-path`, `tmp-sink.invalid-segment`, `out-outside-tmp-sink`) |
| Env-Pin | `:739-748` `work_dir_env` setzt `TMPDIR`/`TEMP`/`TMP` |
| Builder-Variable | `scripts/lib/config.py:1539-1542` setzt `TMP_SINK_PATH` (relativ), registriert in `scripts/lib/consistency/placeholders.py:136` |
| Hart-Validator | `scripts/lib/config.py:483` `_validate_repo_containment` (`_fail` in `:496` ⇒ Exit 1), nutzt `tmp_sink_path_error` + `tmp_sink_location_error` (`:576-587`) |

### B — §5.5: inhaltlich korrekt, literal verbreitet

| Fakt | Beleg |
|---|---|
| Pflichtregel „Basetemp NIE im Arbeitsbaum", `/tmp/<user>` nur als Beispiel („z. B.", alternativ zu `TMPDIR`) | `docs/concepts/repo-containment-prison-mode.md:410-411` |
| Begründung 1: Rekursion/Platte (16 GB, 432.138 Einträge bzw. 13 GB `/var/tmp` am 2026-09-19) | ebd. `:414-422`, `tests/test_knowledge_engine.py:21-36` |
| Begründung 2: 13 zusätzliche Fehlschläge durch Repo-Wurzel-Erkennung | ebd. `:431-439` |
| Literal im kanonischen Aufruf (Punkt 5) | ebd. `:428-429` |
| Literal in ausgelieferten Werten | `.meta-config/project.yaml:194` (`TEST_COMMANDS`), `:249` (`CODE_QUALITY_RULES`) |
| Soll (Rev. 3): Regeltext nennt `PYTEST_BASETEMP` bzw. den Config-Key `system-temp-exception`, kein `/tmp`-Literal in der Vorschrift | Entscheidung Q11 (IC-21, AC-41, ADR-16); die Doku-Änderung selbst ist ein Plan-Schritt, nicht Teil dieser Spec |
| Folge | Die Dateien, die den Agenten instruieren, tragen das Literal — die Regel selbst bleibt gültig |

### C — 18 `/tmp`-Literale in 7 Templates

| Template | Zeilen | Form |
|---|---|---|
| `agents/1-generic/developer.md` | 47, 50, 154, 163 | `docker logs > /tmp/…`, `tee /tmp/run-$RANDOM.log`, `npm run e2e > /tmp/e2e.log`, `tail -50 /tmp/e2e.log` |
| `agents/1-generic/code-reviewer.md` | 221, 229 | `npm run lint > /tmp/lint.log`, `tail -50 /tmp/lint.log` |
| `agents/1-generic/tester.md` | 71, 74, 141, 143 | `docker logs`, `tee`, `tail` |
| `agents/1-generic/validator.md` | 76, 79 | `docker logs`, `tee` |
| `agents/1-generic/docker.md` | 128, 130 | `docker logs`, `tail` |
| `agents/1-generic/devops-engineer.md` | 202, 204 | `docker logs`, `tail` |
| `agents/1-generic/e2e-tester.md` | 154, 156 | `docker logs`, `tail` |

Alle Treffer sind **Schreibbefehle in Bash-Beispielen**, also ausführbare Anweisungen an den Agenten.

### D — 4 Sink-Literale in Templates, 1 Routing-Notiz ohne Renderer

`agents/1-generic/ai-security-guardian.md:111`, `app-lifecycle-governor.md:100`,
`prompt-governor.md:120`, `security-auditor.md:217` schreiben `.tmp/<role>-<topic>.md` fest.
Korrektes Gegenmuster: `agents/1-generic/meta-doctor.md:35,36` (`{{TMP_SINK_PATH}}/doctor/`,
`{{TMP_SINK_PATH}}/context-report/`), `meta-optimizer.md:43,75,91`, `agent-meta-manager.md:304`.

**Sonderfall `config/routing/reviewers.yaml:28`:** Die Datei enthält `.tmp/<role>-<topic>.md` nur im
`notes:`-Fließtext. Sie wird von **keinem** Renderer verarbeitet und von **keinem** Produktionscode
gelesen; einziger Leser ist `tests/test_review_fleet.py:13` (`ROUTING_FILE`, strukturelle Prüfung der
Routing-Matrix). `scripts/lib/rules.py:269` setzt `repo_containment_variables` für
`_merged_rule_vars` (Regel-Templates), nicht für Routing-YAML. Ein `{{TMP_SINK_PATH}}` dort bliebe als
Literal stehen und würde eine Variable vortäuschen, die niemand ersetzt. **Entscheidung:** kein
Injektionspunkt, keine Platzhalter-Erwartung (ADR-10). Soll-Zustand ist ein generischer Satz („in den
konfigurierten Scratch-Sink") ohne `.tmp/` — eine reine Textänderung ohne Renderer-Abhängigkeit. Ein
produktiver Konsument wäre die **Voraussetzung** für eine spätere Injektion und ist heute nicht
vorhanden (nicht behauptet).

**Konflikt:** `tests/test_template_report_paths.py:68-71` (`test_writable_auditor_reports_into_repo_tmp`)
prüft heute genau das Literal-Muster `` `\.tmp/[a-z0-9-]+-<topic>\.md` `` in den vier Templates. Die
Umstellung bricht diesen Guard-Test; er muss auf den Platzhalter rebased werden (Plan-Schritt, nicht Teil
dieser Spec).


### E — Vage Temp-Anweisungen ohne Pflicht-Ort

| Datei | Zeile | Wortlaut (gekürzt) |
|---|---|---|
| `agents/1-generic/se-validator.md` | 192-193 | „Write … to a temporary file" / „Rename temp file" |
| `agents/1-generic/se-developer.md` | 202-203 | dito |
| `agents/1-generic/se-verifier.md` | 206-207 | dito |
| `agents/1-generic/se-integration-and-test-manager.md` | 277-279 | dito |
| `agents/1-generic/se-interface-mgr.md` | 168-169 | dito |
| `agents/1-generic/se-junior-developer.md` | 185-186 | dito |
| `agents/1-generic/se-termination.md` | 169-170 | dito |
| `agents/1-generic/se-requirements.md` | 186 | „Atomic write: temp → rename" |
| `agents/1-generic/se-critic.md` | 120 | dito (Protokoll/Endreport) |
| `agents/1-generic/se-architect.md` | 116 | dito |
| `agents/1-generic/se-senior-developer.md` | 138 | dito |
| `agents/1-generic/se-component-requirements.md` | 283 | dito (Component-Zelle) |
| `agents/1-generic/test-executor.md` | 30, 87 | „ephemeral run artifacts … under a scratch/output path" / „scratch/output paths only" |

Kein Schutzziel, mehrere Orte möglich — der Agent entscheidet selbst und landet im System-Temp.

### F — Hook: fail-open an genau zwei Stellen

| Stelle | Beleg | Verhalten |
|---|---|---|
| `cwd` fehlt im Payload | `hooks/1-generic/repo-containment-impl.sh:151-154` | `WORKDIR="$PWD"` (Prozess-Arbeitsverzeichnis, nicht das Verzeichnis des Tool-Calls) |
| `cwd` ist leer (Antigravity) | `hooks/1-generic/antigravity-json-adapter.sh:122-127` setzt `out['cwd'] = ''`; der Hook behandelt `''` wie „fehlt" (`:152`) | derselbe `$PWD`-Rückfall |
| kein `.meta-config/`-Ancestor | `:160-180` | `resolve_repo_root` schlägt fehl ⇒ `REPO_ROOT="$WORKDIR"`; Arbeitsverzeichnis wird zum Root „geadelt" |
| relativer Zielpfad | `:347` | Basis ist `WORKDIR` (= `cwd`). Das ist **korrekt**, solange `WORKDIR` der echte `cwd` ist: Prüf-Ort und Schreib-Ort sind dann identisch (RVW-12, Annahme A1 in R11). |
| Write/Edit-Ziel aus Antigravity trägt `args.FilePath` (PascalCase) | `hooks/1-generic/antigravity-json-adapter.sh:111` `ARG_KEY_MAP = {'CommandLine': 'command', 'Cwd': 'cwd'}` ⇒ `FilePath` fällt unverändert als `tool_input.FilePath` durch; der Hook liest `tool_input.file_path` (`repo-containment-impl.sh:391-397`) | Exit 2 fail-closed **ohne Pfadprüfung** — jeder Antigravity-Write wird pauschal blockiert (Q10 entschieden, ADR-15) |
| alles andere | `:99-103` (fehlendes `hook_common.sh`), `:105-110` (kein Python), `:113-126` (leerer/kaputter Payload), `:391-397` (fehlendes `file_path`) | Exit 2, fail-closed |
| Exit-Codes | — | `0` = allow, `2` = block |

**Zentraler Fail-open-Pfad:** `Write` nach `/tmp/x` mit `cwd=/tmp` ⇒ `REPO_ROOT=/tmp` ⇒ Ziel liegt
innerhalb ⇒ `exit 0`.

`tests/test_repo_containment_hook.py:213-218` (`test_missing_config_defaults_to_containment_on`,
Docstring: „No `.meta-config/` anywhere: the hook resolves to ENABLED") **deckt diesen Fail-open nicht
ab**: der Test erwartet Exit 2 und erreicht ihn nur, weil das Ziel `root.parent/outside.py` außerhalb
des geadelten Roots liegt. Bei `cwd=<fixture>` und Ziel `<fixture>/x` wäre dasselbe Setup erlaubt — der
eigentliche Fail-open-Fall (`cwd=/tmp`, Ziel `/tmp/x`) hat heute keinen Test (siehe AC-05).


### G — Opencode (hook-loser Provider)

| Fakt | Beleg |
|---|---|
| `has_hooks: false` | `config/ai-providers.yaml:252` ⇒ `provider_hooks_supported(pc) == false` (`scripts/lib/providers.py:700`) ⇒ kein Runtime-Gate |
| Globale Deny-Regel | `opencode.json:39-46` (`permission.edit."**" = deny`, `permission.bash."**" = deny`), `default_agent: orchestrator` (`:47`) |
| Pro-Rolle-Allow überschreibt faktisch | `.opencode/agents/developer.md:10-16` (`bash: allow`, `edit: allow`), `junior-developer.md` (allow), `intern-developer.md` (deny) — generiert aus den Frontmatter-Tools |
| Einziger datengetriebener Schreib-Scope | `config/provider-tools.yaml:61-66` `opencode_primary_edit_allow: [".tmp/**", ".meta-viz/**"]` |
| Konsum | `scripts/lib/provider_transform.py:477-484` (liest die Liste), `:985-998` (baut `{"*": "deny", <path>: "allow"}`) |
| Generiertes Ergebnis | `.opencode/agents/orchestrator.md:13-16` (`'*': deny`, `.tmp/**: allow`, `.meta-viz/**: allow`) |
| Deny-Liste | `config/provider-tools.yaml:56-59` `opencode_deny_critical: [Bash, Write, Edit]` (Konsum `provider_transform.py:980`) |

Der `.tmp/**`-Eintrag ist das **zweite** Sink-Literal in ausgelieferter Konfiguration und kennt einen
konfigurierten Sink (`path: scratch/out`) nicht.

**UNVERIFIED:** Ob die hier geprüfte Opencode-Version einen Key `permission.external_directory` kennt,
ist in diesem Repository-Stand **nicht belegt**. Er darf deshalb nicht tragende Maßnahme sein
(siehe [Provider-Agnostik](#provider-agnostik)).

### H — Backup/Staging

`scripts/lib/backup.py:340` `tempfile.TemporaryDirectory()` ohne `dir=` ⇒ System-Temp, obwohl das
Archivziel im Repo liegt (`:338` legt `backup_dir` im Projekt an).

### I — Goldens und Guards, die Literale einfrieren

| Datei | Beleg | Inhalt |
|---|---|---|
| `tests/test_template_slimming_equivalence.py` | Blöcke `OG-TAIL-DOCKER` (deckt `devops-engineer`, `docker`, `e2e-tester`, `tester`), `OG-TAIL-DEV` (`developer`), `OG-PASS-CODE-REVIEWER` (`code-reviewer`); maßgeblich sind die Bezeichner, nicht die Zeilennummern | `/tmp`-Literale byte-genau in `inline=`/`retained=` |
| `tests/fixtures/slimming-golden/tester.md:51`, `test-executor.md:33,41`, `e2e-tester.md:73`, `documenter.md:68` | — | `--basetemp=/tmp/$USER/pytest-agent-meta` aus `TEST_COMMANDS` eingefroren |
| `tests/conftest.py:28` | `_EXTERNAL_BASETEMP_HINT = "--basetemp=/tmp/$USER/pytest-agent-meta"` | Warntext mit Literal |
| `tests/test_template_report_paths.py:42-48` | `test_no_provider_tmp_path_in_agents` | verbietet nur `/tmp/opencode`, kein generelles Verbot |
| `tests/test_template_report_paths.py:68-71` | `test_writable_auditor_reports_into_repo_tmp` | erzwingt `.tmp`-Literal |

### J — Rekursionsmechanik und die 13 Fehlschläge

`tests/test_knowledge_engine.py:19-94` hält den Vorfall fest und enthält **bereits alle Netze**:

- `_COPY_IGNORE` schließt `.tmp` und die übrigen lokalen Bäume aus (`:37-49`),
- `_assert_copy_dest_is_safe` bricht laut ab statt zu rekursieren (`:64-83`),
- `shutil.copytree(..., symlinks=True)` (`:89-93`),
- Regressionstests `:489-546` (auch: „An in-repo basetemp under the ignored `.tmp` sink is allowed", `:546`).

**Die 13 Fehlschläge haben eine andere Ursache als Rekursion.** Tests, deren Fixture-Wurzel absichtlich
**kein** `.meta-config/` hat (z. B. `tests/test_repo_containment_hook.py:213-218`: `root = tmp_path / "bare"`),
verlassen sich darauf, dass oberhalb nichts liegt. Liegt der Basetemp im Repo, findet die
Ancestor-Suche das **echte** Repo (`<repo>/.meta-config`) ⇒ Ziel gilt als „inside root" ⇒ Test erwartet
Exit 2, bekommt Exit 0. Betroffen laut Messung 2026-09-20: `test_repo_containment_hook`,
`test_spec_plan_group_consistency`, `test_dod_push_check_hook`, `test_file_affinity`
(`docs/concepts/repo-containment-prison-mode.md:435-437`). Tests laufen mit einem externen Basetemp fehlerfrei. Diese Ursache ist durch den
Rekursionsschutz **nicht** heilbar.

### K — Standalone-Export: Literale und Platzhalter-Notizen

`standalone/agents/**` wird aus `agents/1-generic/<role>.md` gerendert
(`scripts/lib/standalone.py::render_standalone_agent`, `:289-337`) und ist als Artefakt eingecheckt.
Gemessen am 2026-10-24:

| Befund | Anzahl | Dateien |
|---|---|---|
| `/tmp`-Literale | 18 | `developer.md` (30,33,130,139), `tester.md` (55,58,125,127), `validator.md` (47,50), `docker.md` (115,117), `devops-engineer.md` (185,187), `e2e-tester.md` (126,128), `code-reviewer.md` (206,214) |
| `.tmp/`-Sink-Literale | 4 | `ai-security-guardian.md:96`, `app-lifecycle-governor.md:90`, `prompt-governor.md:106`, `security-auditor.md:201` |
| gerenderte Platzhalter-Notiz `[TMP_SINK_PATH — not available outside a full agent-meta install]` | 12 Vorkommen in 3 Dateien | `meta-doctor.md` (23,24,43,55,65,106,128,129), `meta-optimizer.md` (32,64,80), `agent-meta-manager.md` (288) |

Ursache der Notiz: `_standalone_variables` (`scripts/lib/standalone.py:254-282`) setzt `TMP_SINK_PATH`
nicht; der Safety-Net-Regex (`:313-319`) ersetzt jeden übrigen Platzhalter durch
`[<NAME> — not available outside a full agent-meta install]`. Ursache der Literale: der Export inlinet
den Template-Text unverändert (`:294-311`).

**Soll-Regel (keine Implementierung):** Standalone hat bewusst **keine** Projekt-Config — der einzige
ehrliche Wert ist der Framework-Default des Sinks. `_standalone_variables` setzt deshalb
`TMP_SINK_PATH = ".tmp"`; die Platzhalter-Notiz verschwindet damit für alle Report-Ziele, und der
vorhandene Scope-Hinweis im Kopf („no project-specific config", `:327-336`) bleibt die Offenlegung, dass
dieser Wert nicht projektspezifisch ist. `TMP_SINK_ENV_PIN_BLOCK` wird dort als **leerer** String gesetzt:
ohne Projekt-Config gäbe es nur einen Maschinenpfad (ADR-12) oder eine neue Platzhalter-Notiz (IC-15). Die
`/tmp`- und `.tmp/`-Literale verschwinden **nicht** durch
einen Standalone-Sonderweg, sondern durch die Template-Korrektur (Punkte 1/2 des Inventars) plus
Regeneration. Regeneration/Drift-Gate existiert bereits: `sync.py --render-standalone --check`
(`scripts/lib/cli_commands.py:496-508`, Exit 1 bei Drift).

### L — Zwei weitere Sink-Konsumenten mit eigener Auflösung

| Konsument | Beleg | Befund |
|---|---|---|
| Managed-`.gitignore`-Block | `scripts/lib/gitignore.py::_tmp_sink_gitignore_entry` (`:324-339`), aufgerufen aus `:317-319` | Ruft `resolve_effective_repo_containment({"repo_containment": …}, None)` selbst auf und leitet den Eintrag aus `effective.tmp_sink_path` ab. Zweiter Gitignore-Mechanismus neben `ensure_tmp_sink_gitignore` (`repo_containment.py:795`); bei fehlendem Block greift der Framework-Default (`.tmp/`). |
| Doctor-Check `CHECK_TMP_SINK` | `scripts/lib/doctor_detectors.py::_sink_hits` (`:403-411`) | Liest `repo_containment.tmp-sink.path` per `get_path` und validiert mit `tmp_sink_path_error` + `tmp_sink_location_error` erneut — eine dritte Auslegung derselben Config. |

Beide sind **Konsumenten** von `TmpPaths` (Inventar 9 und 10), nicht eigenständige Auflösungen; der
Doctor behält seine eigene *Meldung* (Finding mit `CHECK_TMP_SINK`), aber nicht seine eigene *Auflösung*.

### M — Antigravity-Adapter: `mktemp` im System-Temp

`hooks/1-generic/antigravity-json-adapter.sh:167` legt pro Hook-Lauf eine Datei über `mktemp` an
(`_ERR_FILE`, für stderr des Ziel-Hooks), gelöscht per `trap … EXIT` (`:168`). Eigenschaften: ephemer,
namenlos im Inhalt (nur stderr des geblockten Calls), maximal ein Lauf, kein Repo-Bezug. Eine Umleitung
in den Sink wäre **schädlich**: wenn der Sink deaktiviert oder nicht beschreibbar ist, dürfte die
Block-Meldung nicht an der Ablage scheitern — der Guard würde sich selbst aussperren. Deshalb
**dokumentierte Ausnahme** (Inventar 12, ADR-11), nicht Injektionspunkt.

Der Adapter bleibt darüber hinaus unverändert; **eine** Ergänzung ist entschieden: `ARG_KEY_MAP` bekommt
den Eintrag `'FilePath': 'file_path'` (Q10, ADR-15, AC-40), damit ein Write geprüft statt pauschal
blockiert wird. Die `mktemp`-Ausnahme aus dem vorigen Absatz bleibt davon unberührt.

### N — Weitere Treffer, bewusst außerhalb des Scopes

| Ort | Beleg | Einordnung |
|---|---|---|
| `rules/2-platform/_wf-sharkord-docker-binaries.md:26-31` | `/tmp/ffmpeg.tar.xz`, `/tmp/ffmpeg-extract` in einem `docker compose`-Build-Step | **Ausnahme:** Die Schreibziele liegen im Container-Layer (`init-binaries`), nicht im Host-Repo. Zusätzlich ist die Datei durch den `_`-Präfix von der Regel-Auslieferung ausgenommen (`scripts/lib/rules.py:229-231` überspringt `_`-Dateien; das Glob `f"{platform}-*.md"` trifft `_wf-…` ohnehin nicht) — sie ist lazy-geladene Knowledge, kein gerenderter Regeltext. |
| `scripts/hermes_export.py:26-29` | `/tmp/...` in der CLI-Usage-Docstring | **Ausnahme:** Beispiel für ein `--output`-Ziel eines Operator-Kommandos, keine Agenten-Anweisung, nicht gerendert. |
| `tests/test_knowledge_engine.py:81`, `tests/test_provider_reactivation_artifacts.py:16,65` | `/tmp` in Fehler-/Hinweistexten | **Ausnahme:** Testdiagnose, nicht ausgeliefert; wird beim Basetemp-Rebase (AC-19) mit angepasst, ist aber kein Injektionspunkt. |
| `scripts/*.py` (12 Aufrufe) | `admin-server.py:609,618,644,1243,1625,5799,5805,5830`, `consistency-check.py:79,83,98`, `run_role_routing_eval.py:727` | **Im Scope von Inventar 3**, nicht ausgenommen: AC-11 gilt für `scripts/**`, nicht nur `scripts/lib/**`. |

---

## Design-Kern: eine Quelle der Wahrheit

### Resolver-Vertrag

Ein einziger Einstiegspunkt, an dem die Konfiguration gelesen und in **alle** benötigten Formen
überführt wird:

```python
# scripts/lib/tmp_paths.py  (neu)
@dataclass(frozen=True)
class SystemTempException:
    enabled: bool          # repo_containment.tmp-sink.system-temp-exception.enabled
    reason: str            # Pflichttext, wenn enabled (Dokumentationspflicht)
    pytest_basetemp: bool  # Ausnahme gilt fuer pytest --basetemp
    toolchain_cache: bool  # YAML-Key `toolchain-caches` (Default false); gilt fuer pip/npm, nie fuer docker

@dataclass(frozen=True)
class TmpPaths:
    relative: str                 # validiert, z. B. ".tmp" (Template-Form); auch bei enabled=False gesetzt
    absolute: Path | None         # realpath innerhalb project_root; None genau dann, wenn enabled=False
    enabled: bool                 # tmp-sink aktiv (kein Fehlerzustand)
    system_temp_exception: SystemTempException
    pytest_basetemp: str          # fertiger argv-Wert, plattformneutral (bei Bedarf shell-gequotet)
    env: dict[str, str]           # TMPDIR/TEMP/TMP -> absolute Pfade; {} genau dann, wenn enabled=False

def resolve_tmp_paths(project_root: Path, config: dict | None) -> TmpPaths: ...
```

Regeln:

- **`resolve_tmp_paths` wirft nicht wegen eines deaktivierten Sinks.** `tmp-sink.enabled: false` ist ein
  gültiger Config-Zustand und liefert `TmpPaths(enabled=False, relative=<validiert>, absolute=None,
  env={}, …)`. Nur so kann `_build_orch_variables` weiterhin `TMP_SINK_PATH` setzen (die
  Fehlermatrix verlangt „Sync ok") und `tmp_sink_enabled` bleibt als Information erhalten; `enabled`
  wäre sonst toter Zustand. Diese Semantik folgt der bestehenden Konvention in
  `repo_containment.py`: `resolve_effective_repo_containment` (`:473-558`) ist ausdrücklich
  **nicht-exitierend** und liefert Flags statt Exceptions; geworfen wird erst dort, wo tatsächlich ein
  Pfad zum Schreiben gebraucht wird (`_active_sink_dir`, `:579-601`).
- **Werfend sind für den deaktivierten Sink ausschließlich die Schreib-/Verbrauchs-APIs** —
  unverändertes Bestandsverhalten: `resolve_output_dir` / `resolve_work_dir` / `resolve_out_path`
  (`:641-701`), `tmp_env` und `tmp_sink_env_pin_block` (beide `tmp-sink.disabled`). Config-Fehler wirft
  bereits der Resolver (nächster Punkt). Kein Verhalten ändert sich für bestehende Aufrufer.
- **Konfigurationsfehler bleiben Fehler:** `resolve_tmp_paths` wirft `TmpSinkError` für einen ungültigen
  Pfad (`tmp-sink.invalid-path`, aus `tmp_sink_path_error`/`tmp_sink_location_error`) und für eine
  wirkungslose System-Temp-Ausnahme (`tmp-sink.system-temp-exception`). Das ist kein
  „disabled"-Fall und wird nicht stillschweigend zu `enabled=False`.
- **Kein `sys.exit`** in `tmp_paths.py` (Bibliotheks-Doktrin von `repo_containment.py:1-8`); der
  Sync-Validator wandelt `TmpSinkError` in `_fail` (Exit 1). Es gibt **keinen stillen Fallback**.
- `relative` wird mit `tmp_sink_path_error` validiert (lexikalisch + realpath, `repo_containment.py:330-357`);
  `tmp_sink_location_error` (`:360-381`) bleibt die Prüfung „nicht im System-Temp". Validierung findet
  auch bei `enabled=False` statt: ein kaputter Pfad bleibt ein Config-Fehler, unabhängig vom Schalter
  (dieselbe Begründung wie `_validate_repo_containment`: „so enabling it later never surfaces a dormant
  misconfiguration", `config.py:486-490`).
- `absolute` = realpath von `<project_root>/<relative>`; identisch zu `_resolve_sink_dir` (`:304-327`),
  damit es genau eine Auflösungslogik gibt (keine zweite Implementierung). Bei `enabled=False`
  **nicht** berechnet (`None`) — ein deaktivierter Sink hat keinen Schreibort.
- `pytest_basetemp`:
  - `system_temp_exception.enabled and system_temp_exception.pytest_basetemp` ⇒
    `<tempfile.gettempdir()>/<user>/pytest-agent-meta`, wobei `<user>` aus `USER`/`USERNAME` mit
    `getpass.getuser()`-Fallback kommt. **Kein** `/tmp`-Literal, kein Shell-Ausdruck.
  - sonst und `enabled` ⇒ `<absolute>/pytest`.
  - sonst und `enabled=False` ⇒ derselbe System-Temp-Pfad, aber **nur** wenn
    `system_temp_exception.pytest_basetemp` gilt; andernfalls
    `TmpSinkError("tmp-sink.system-temp-exception", …)` — ein deaktivierter Sink darf nicht
    stillschweigend zum Basetemp-Ort werden.
  - Liegt `tempfile.gettempdir()` selbst **innerhalb** des Projekts, ist die Ausnahme wertlos ⇒
    `TmpSinkError("tmp-sink.system-temp-exception", …)` (laut, kein stiller Wechsel).
  - Einbettung in `TEST_COMMANDS` erfolgt **shell-gequotet**: `--basetemp="<path>"`; der Wert darf kein
    `"` enthalten (Validierung), damit Pfade mit Leerzeichen (Windows/macOS) den Aufruf nicht brechen.
- `env` wird aus demselben `absolute` gebaut; die Umsetzung ruft `work_dir_env(absolute)` auf, statt die
  Drei-Keys-Logik zu duplizieren (`repo_containment.py:739-748`). Bei `enabled=False` bleibt `env == {}`.
  Die Werte sind **ausschließlich absolut** — nie `relative`, auch nicht als Präfix.
- **`tmp_sink_env_pin_block(paths)`** erzeugt den Prompt-Block für Agenten-Bash und setzt `TMPDIR`, `TEMP`
  und `TMP` auf **denselben absoluten** Wert (`str(paths.absolute)`); ein relativer Env-Wert ist
  ausgeschlossen (Begründung und Abgrenzung zu den Template-Beispielen:
  [Env-Pin absolut](#env-pin-absolut-template-beispiele-relativ--der-unterschied), ADR-12). Bei
  `enabled=False` wirft die Funktion `TmpSinkError("tmp-sink.disabled", …)`; der Builder setzt die
  Variable dann nicht.


### Relative vs. absolute Form

| Verwendung | Form | Begründung |
|---|---|---|
| Template-Beispiele, Rollen-Anweisungen, Report-Ziele | **relativ** — `{{TMP_SINK_PATH}}` (bestehend, `config.py:1542`) | move-safe: Repo verschieben, Submodul-Mount, anderer Rechner; Agenten-cwd ist der Repo-Root |
| Subprozess-Env `TMPDIR`/`TEMP`/`TMP` — `TmpPaths.env` **und** `TMP_SINK_ENV_PIN_BLOCK` | **absolut** | Die Variablen sind prozess-global: Kindprozesse erben den Wert und interpretieren einen relativen Wert gegen **ihr eigenes** `cwd`; ein relativer Env-Wert würde Temp-Writes je nach Prozess fehlleiten |
| Backup-Staging (`dir=`) | **absolut** | `tempfile` verlangt einen realen Pfad |
| Hook-Meldungen, Diagnose | **absolut**, zur Laufzeit berechnet | Operator muss den Pfad ohne Kopfrechnen prüfen können |
| pytest-Basetemp | **absolut** (oder System-Temp-Root, s. Ausnahme) | pytest-argv; in `TEST_COMMANDS` shell-gequotet |
| Consistency-Findings | **beide** (`relative` + `absolute`) | Reviewbarkeit |

**Neue Builder-Variable `TMP_SINK_ABS_PATH`** (entschieden, Q2): absolut, realpath, nur für Punkte, die
zwingend absolut sind. Sie darf **nicht** in Templates gerendert werden (Maschinenpfad im generierten
Artefakt = kaputt nach Umzug). Einzige Ausnahme mit absoluten Werten im gerenderten Artefakt ist der
Env-Pin-Block (ADR-12). Der Hook bekommt sie ebenfalls nicht gebacken, sondern berechnet
`<root>/<sink>` zur Laufzeit aus der Config — die Sink-Berechnung liegt in `read_effective_containment`
(`repo-containment-impl.sh:186-301`), der Wert wird bei `:348` (`sink_root`) verwendet, damit eine
Config-Änderung ohne Re-Sync wirkt.


**Bestehende `TMP_SINK_PATH` bleibt die relative Form** — kein Vertragsbruch für Downstream-Projekte.

#### Env-Pin absolut, Template-Beispiele relativ — der Unterschied

Der Env-Pin-Block ist **absolut**, die Template-Beispiele bleiben **relativ**. Beides ist bewusst und folgt
aus der Lebensdauer des jeweiligen Werts:

- **Template-Beispiele** (`docker logs … > {{TMP_SINK_PATH}}/x.log`) führt die Agenten-Shell aus, deren
  `cwd` per Konvention der Repo-Root ist. Der relative Wert gilt genau dort, ist move-safe und bricht bei
  Submodul-Mount oder Umzug nicht.
- **Env-Pin** (`TMPDIR`/`TEMP`/`TMP`) wird dagegen **vererbt**: jeder Kindprozess sieht denselben Wert und
  löst einen relativen Wert gegen *sein* `cwd` auf. Deshalb muss der zugewiesene Wert absolut sein; ein
  relativer `TMPDIR` ist ein Fehler, kein Move-Vorteil (RVW2-01).

Konsequenz: Der gerenderte `TMP_SINK_ENV_PIN_BLOCK` trägt damit einen Maschinenpfad. Das ist die **einzige**
Ausnahme von der Move-Safe-Regel aus ADR-02 (ADR-12; IC-13 nennt sie ausdrücklich). Sie ist dreifach
begrenzt: `TMP_SINK_ABS_PATH` bleibt in Templates
verboten (IC-13), der Block prüft die Existenz **vor** dem Export und meldet den Reparaturweg
(`python scripts/sync.py`), und der Standalone-Export setzt die Variable leer (IC-15) — dort gibt es keine
Projekt-Config, also auch keinen Maschinenpfad im Release-Artefakt.

---

## Injektionspunkte (vollständiges Inventar)

| # | Punkt | Ist | Soll | Wer injiziert | Wann | Fehlerverhalten |
|---|---|---|---|---|---|---|
| 1 | Template-Platzhalter `{{TMP_SINK_PATH}}` | vorhanden und registriert (`config.py:1542`, `consistency/placeholders.py:136`), aber 4 Literale daneben (D) | **alle** Report-Ziele über den Platzhalter; die 4 Literale ersetzt | `scripts/lib/config.py::_build_orch_variables` (`:1539-1542`) → Template-Renderer | Sync | Unbekannter Platzhalter ⇒ bestehender Placeholder-Drift (`consistency/placeholders.py`); Literal ⇒ neuer Consistency-Check (Punkt 7) |
| 2 | `{{TEST_COMMANDS}}` / `CODE_QUALITY_RULES` | `/tmp/$USER/pytest-agent-meta` literal (`.meta-config/project.yaml:194,249`) | Token `{{PYTEST_BASETEMP}}` in beiden Werten; Builder ersetzt es durch `TmpPaths.pytest_basetemp`, shell-gequotet | `scripts/lib/config.py::_build_orch_variables` (nach `:1542`) | Sync | Token bleibt unersetzt ⇒ `_fail` (Exit 1), Code `tmp-sink.pytest-token` |
| 3 | Subprozess-Env `TMPDIR`/`TEMP`/`TMP` | `work_dir_env` nur an 2 Stellen (`context_report.py:340`, `meta_optimizer.py:1508`); alle anderen Starts erben System-Temp — **12 Aufrufe** in `scripts/*.py` (Abschnitt N) | jeder Framework-Subprozessstart in `scripts/**` (auch `scripts/*.py`), der Temp-Dateien erzeugen kann, erhält `TmpPaths.env` oder steht in einer begründeten Allowlist; Agenten-Bash erhält einen Prompt-Block mit `export TMPDIR=<absoluter Sink>`, `TEMP` und `TMP` — **absolute** Werte aus `TmpPaths.absolute`, kein relativer Env-Wert (RVW2-01, ADR-12) | `scripts/lib/tmp_paths.py::tmp_env` (neu, delegiert an `work_dir_env`), Builder-Variable `TMP_SINK_ENV_PIN_BLOCK` via `tmp_sink_env_pin_block` | Sync (Block) / Laufzeit (Env) | Sink aus ⇒ `TmpSinkError` beim Aufruf von `tmp_env` **und** von `tmp_sink_env_pin_block` (kein Env-Pin auf einen deaktivierten Sink; der Builder setzt die Variable dann nicht); fehlender Pin ⇒ Consistency-WARNING `temp-literal.subprocess-env` |
| 4 | Backup/Staging | `scripts/lib/backup.py:340` `TemporaryDirectory()` ohne `dir=` | `TemporaryDirectory(dir=<absolute>/backup-staging)`; bei deaktiviertem Sink expliziter, geloggter Fallback auf System-Temp | `scripts/lib/backup.py::create_backup` via `resolve_output_dir` (`repo_containment.py:641-652`) | Laufzeit (CLI/Agent) | Sink aktiv + nicht auflösbar ⇒ Abbruch mit `TmpSinkError`; Sink aus ⇒ WARNING `backup.staging-system-temp` + System-Temp |
| 5 | Hooks (Pfadauflösung + Meldungen) | `repo-containment-impl.sh:151-180` adelt `$PWD` (auch bei leerem `cwd`); `:347` Basis `WORKDIR`; Meldungen `:370-388` relativ | **Anker-Regel:** `cwd` fehlt/leer ⇒ kein `$PWD`; Anker = Verzeichnis des Ziels, wenn das Ziel absolut ist, sonst Exit 2 `repo-containment.no-root`. Kein Ancestor mit `.meta-config/` ⇒ Exit 2. Relative Ziele gegen `cwd` (Prüf-Ort = Schreib-Ort). Meldungen mit absolutem Sink. Der Antigravity-Adapter mappt `args.FilePath` → `tool_input.file_path` (Q10, ADR-15) | Hook-Implementierung selbst (kein Sync-Placeholder) | Laufzeit pro Tool-Call | Exit 2 mit stabiler Fehlerklasse ([Fail-closed-Design](#fail-closed-design-hook)) |
| 6 | Opencode-Permissions / edit-Scope | `config/provider-tools.yaml:64-66` Literal `.tmp/**`; generiert nach `.opencode/agents/orchestrator.md:13-16` | Scope wird zur Sync-Zeit aus `TmpPaths.relative` abgeleitet (`<relative>/**` + `.meta-viz/**`); Sink aus ⇒ nur `.meta-viz/**` | `scripts/lib/provider_transform.py:477-484` (Einlesen) + `:985-998` (Scope-Bau) | Sync | Fehlende Ableitung ⇒ Consistency-WARNING `repo-containment.no-hook-support` bleibt; Scope-Bau fällt auf `edit: deny` zurück (`:998`) |
| 7 | Tests / Goldens / Guards / Check-Scope | Goldens frieren `/tmp` ein (I); Report-Guard erzwingt `.tmp`-Literal (`test_template_report_paths.py:68-71`); kein generelles Verbot (`:42-48`) | Goldens rebased; neuer Check `temp-literal.*` (WARNING) über `agents/**`, `standalone/**`, `rules/1-generic/**`, `config/**`, `tests/fixtures/slimming-golden/**`, `tests/conftest.py`; Allowlist `.meta-config/temp-literal-allowlist.yaml` | `scripts/lib/consistency/temp_literals.py` (neu), registriert im `_strict_findings`-Block (`scripts/lib/cli_commands.py:1411-1426`) | Sync-Validierung `--validate` | Verstoß ohne Allowlist-Eintrag ⇒ WARNING (nicht Exit), damit Bestandsprojekte nicht hart brechen; `--strict`-Pfad bleibt unverändert |
| 8 | Sink-Provisionierung / `ensure_tmp_sink_gitignore` | `sync_pipeline.py:238-269`; `ensure_tmp_sink` + `ensure_tmp_sink_gitignore`; `_resolve_sink_dir` liefert `None` bei deaktiviertem Sink | unverändert, aber gespeist aus `resolve_tmp_paths` (eine Auflösung) | `scripts/lib/sync_pipeline.py::_sync_tmp_sink` | Sync | Sink aus ⇒ `log.skip` (bestehend, `:238-240`); Pfad ungültig ⇒ Exit 1 (Validator) |
| 9 | Managed-`.gitignore`-Block | `scripts/lib/gitignore.py::_tmp_sink_gitignore_entry` (`:324-339`) ruft `resolve_effective_repo_containment` selbst auf; Eintrag aus `effective.tmp_sink_path`, Default `.tmp/` | Eintrag kommt aus `TmpPaths.relative`; kein eigener Resolver-Aufruf; bei `enabled=False` kein Eintrag | `scripts/lib/gitignore.py::collect_gitignore_entries` (Aufrufstelle `:317-319`) | Sync (Gitignore-Generierung) | `enabled=False` ⇒ kein Eintrag (bestehend); ungültiger Pfad ⇒ Exit 1 (Validator, nicht Gitignore) |
| 10 | Doctor-Check `CHECK_TMP_SINK` | `scripts/lib/doctor_detectors.py::_sink_hits` (`:403-411`) parst `repo_containment.tmp-sink.path` selbst und validiert erneut | Finding bleibt (`CHECK_TMP_SINK`, `Severity.ERROR`), die **Auflösung** kommt aus `TmpPaths`; kein dritter Parser | `scripts/lib/doctor_detectors.py::_sink_hits` (Konsument) | Laufzeit `--doctor` | `enabled=False` ⇒ kein Sink-Finding; ungültiger Pfad ⇒ Finding mit `reason` aus dem Resolver |
| 11 | `standalone/agents/**` + Standalone-Fallback für `{{TMP_SINK_PATH}}` | 18 `/tmp`, 4 `.tmp/`-Sink-Literale, 12 Platzhalter-Notizen (Abschnitt K); `_standalone_variables` (`standalone.py:254-282`) setzt `TMP_SINK_PATH` nicht | `_standalone_variables` setzt `TMP_SINK_PATH = ".tmp"` (Framework-Default, da Standalone keine Projekt-Config hat) und `TMP_SINK_ENV_PIN_BLOCK = ""` (kein Maschinenpfad, IC-15); Literale verschwinden über die Template-Korrektur; `sync.py --render-standalone --check` ist grün | `scripts/lib/standalone.py::_standalone_variables` + `render_standalone_agent` | `sync.py --render-standalone` | Drift ⇒ Exit 1 (bestehend, `cli_commands.py:496-508`); Literal ⇒ WARNING `temp-literal.system-temp` (Punkt 7 deckt `standalone/**` ab) |
| 12 | Antigravity-Adapter: `mktemp`-stderr-Datei | `hooks/1-generic/antigravity-json-adapter.sh:167` `_ERR_FILE=$(mktemp)`, `trap … EXIT` (`:168`) | **bewusste Ausnahme:** bleibt im System-Temp; eine Umleitung in den Sink würde die Block-Meldung von der Schreibfähigkeit des Sinks abhängig machen (Selbstausschluss) | keine Injektion | Laufzeit pro Hook-Lauf | Datei verschwindet per `trap`; Fehler beim Anlegen darf den Adapter nicht blocken (heutiges Verhalten bleibt) |
| 13 | `.tmp`-Literal in Regeln | `rules/1-generic/plan-ledger.md:67` („Schreiben nur im Projektroot und in `.tmp/`") | Regeltext nennt den Platzhalter bzw. „im konfigurierten Scratch-Sink" | Template-Renderer | Sync | Check 7 meldet verbleibende Literale |
| 14 | §5.5-Regeltext | `docs/concepts/repo-containment-prison-mode.md:404-439`: Pflichtregel inhaltlich korrekt, aber `/tmp/<user>` als Beispiel (`:410-411`) und im kanonischen Aufruf (`:428-429`) noch literal | Regeltext verweist auf `PYTEST_BASETEMP` bzw. den Config-Key `system-temp-exception`; die Pflichtregel („Basetemp NIE im Arbeitsbaum") bleibt **wörtlich** erhalten; kein `--basetemp=/tmp`-Literal in der Vorschrift | kein Renderer — redaktionelle Änderung am Konzeptdokument (Doku-Task im Plan, Q11/ADR-16) | Doku-Schritt im Plan (nicht Teil dieser Spec) | Kein Laufzeit-Fehlerpfad; AC-41 prüft den Regeltext |
| — | `config/routing/reviewers.yaml:28` | `.tmp/…` im `notes:`-Text; **kein** Renderer, **kein** Produktions-Konsument (nur `tests/test_review_fleet.py:13`) | **ausgenommen** (Test-Fixture/Framework-Doku); der Satz nennt nur noch „den konfigurierten Scratch-Sink"; keine Platzhalter-Erwartung | keine | — | Kein Fehlerpfad; ein späterer Renderer wäre die Voraussetzung für Injektion (ADR-10) |
| — | `rules/2-platform/_wf-sharkord-docker-binaries.md:26-31` | `/tmp` in einem Container-Build-Step; Datei ist `_`-präfixiert und wird nicht als Regel gerendert (`rules.py:229-231`) | **ausgenommen:** Schreibziel im Container-Layer, nicht im Host-Repo | keine | — | — |
| — | `scripts/hermes_export.py:26-29` | `/tmp/...` in der CLI-Usage-Docstring | **ausgenommen:** Operator-Beispiel, keine Agenten-Anweisung | keine | — | — |
| — | `tests/test_knowledge_engine.py:81`, `tests/test_provider_reactivation_artifacts.py:16,65` | `/tmp` in Fehler-/Hinweistexten | **ausgenommen:** Testdiagnose; wird beim Rebase (AC-19) mitgeführt | keine | — | — |


---

## Entscheidungsvorlage: pytest --basetemp

Ausgangslage: `.meta-config/project.yaml:194` ist der kanonische Suite-Aufruf; §5.5
(`docs/concepts/repo-containment-prison-mode.md:404-439`) begründet die Ausnahme mit **zwei
unabhängigen** Effekten — Plattenrekursion (J, Absatz 1) und Ancestor-Kollision in 13 Tests
(J, Absatz 2).

### Option A — Basetemp unter dem Sink, technisch abgesichert

`--basetemp=<sink>/pytest`.

- **Evidenz:** Die Rekursionsnetze existieren bereits vollständig
  (`tests/test_knowledge_engine.py:37-49,64-83,89-93`) und der Guard erlaubt ein Ziel unter einem
  ignorierten Top-Level-Pfad ausdrücklich (`:67-76`, Test `:546`). Der Plattenvorfall ist damit
  technisch adressiert.
- **Bewertung:** Löst **die Rekursion**, aber **nicht** die 13 Fehlschläge. Deren Ursache ist die
  Ancestor-Suche nach `.meta-config/` (J, Absatz 2) — ein Schutz gegen Rekursion ändert daran nichts.
- **Zusatzmaßnahmen, falls A gewählt wird:**
  1. **Fixture-Sentinel statt Ancestor-Suche:** Tests, die „kein Projekt oberhalb" brauchen, stellen
     ihre Isolation explizit her (Fixture-Wurzel außerhalb des Repo-Baums, siehe AC-03/AC-05/AC-07),
     statt sich auf die Abwesenheit von `.meta-config/` zu verlassen. Betroffen:
     `test_repo_containment_hook`, `test_spec_plan_group_consistency`, `test_dod_push_check_hook`,
     `test_file_affinity`. Ein Monkeypatch des Resolvers hilft nur **in-process**; die Hook-Tests starten
     ein Subprozess-Skript und brauchen deshalb die physische Isolation.
  2. **conftest-Warnung bleibt** (`tests/conftest.py:56-65`) und wird um den Hinweis ergänzt, dass ein
     In-Repo-Basetemp die Sentinel-Tests ebenfalls beeinflusst.
  3. `cleanup`-Semantik: `ensure_tmp_sink` löscht nie (`repo_containment.py:704-736`); ein wachsender
     `pytest-*`-Baum im Sink muss über `cleanup: on-sync` oder manuell entsorgt werden — das ist eine
     neue Betriebslast.
- **Restrisiken:** Symlink `pytest-current` im Sink (durch `symlinks=True` entschärft, aber vorhanden);
  Repo-Größe wächst im CI-Cache; fremde Projekte mit anderer Test-Infrastruktur erben die Sentinel-Pflicht.
- **Unabhängig von der Optionswahl:** Die Sentinel-/Isolationspflicht gilt für **alle** neuen
  Fail-closed-Hook-ACs (RVW-07, Q8 entschieden) — auch Option C heilt die Ancestor-Kollision der neuen
  Tests nicht, weil `tmp_path` bei C zwar außerhalb liegt, die Tests ihre Wurzel aber bewusst ohne
  `.meta-config/` bauen.


### Option B — System-Temp als enge, dokumentierte, konfigurierte Ausnahme

`--basetemp=<tempfile.gettempdir()>/<user>/pytest-agent-meta`, gesteuert über Config-Key.

- **Bewertung:** Hält die Testisolation (13 Fehlschläge bleiben aus) und den Plattenvorfall fern, ist aber
  weiterhin „außerhalb". Zulässig nur, wenn der Wert **niemals** als Literal erscheint, sondern aus dem
  Resolver kommt.
- **Schwäche allein:** Der Agent selbst schreibt weiterhin in den System-Temp, sobald eine Anweisung
  fehlt (Punkte 1/3/4 der Ist-Analyse). B löst nur das Basetemp-Problem.

### Option C — Hybrid (Empfehlung)

- **Default:** Sink für **alles, was der Agent selbst schreibt** (Templates, Report-Ziele, Bash-Beispiele,
  Backup-Staging, Hook-Verdict, Env-Pin).
- **Ausnahme:** System-Temp **ausschließlich** für `pytest --basetemp`, gesteuert über einen expliziten
  Config-Key und den plattformneutralen Temp-Root (`tempfile.gettempdir()`, **kein** `/tmp`-Literal).

```yaml
repo_containment:
  tmp-sink:
    enabled: true
    path: .tmp
    gitignore: true
    cleanup: manual
    system-temp-exception:
      enabled: true                 # entschieden (Q1): Default an, kein Literal
      reason: "pytest basetemp must stay outside the repo (ancestor-collision, 13 failures 2026-09-20)"
      pytest-basetemp: true
      toolchain-caches: false       # Opt-in (Q3): true => pip/npm-Cache in den Env-Pin-Block
```

**Begründung der Empfehlung:**

1. **13-Fehlschläge-Mechanik:** Option A kann sie nicht heilen (J, Absatz 2); nur ein Basetemp außerhalb
   des Repo-Baums hält `tmp_path` aus dem Ancestor-Bereich des echten `.meta-config/`. C behält diese
   Isolation, ohne sie zu verstecken.
2. **Nutzerregel „in der Regel nicht außerhalb":** C macht die Ausnahme **eine**, nicht viele: genau ein
   Zweck, ein Key, ein dokumentierter Grund, ein sichtbarer Wert im gerenderten Kommando. „In der Regel"
   bleibt erfüllt, weil alle Agenten-Schreibziele im Sink liegen.
3. **Keine Umkehr von §5.5 (Q1 entschieden):** Die Regel bleibt inhaltlich bestehen — der Basetemp liegt
   weiterhin außerhalb des Arbeitsbaums. Sie wird nur **konfigurierbar** und **literal-frei**; die
   Begründung wird als `reason` mitgeführt, damit sie nicht aus dem Regelwerk verschwindet. Die in
   Revision 1 erwogene Alternative „Default aus" wäre dagegen exakt die in „Nicht-Ziele" ausgeschlossene
   Umkehr und ist verworfen.
4. **Rückwärtskompatibilität:** Projekte ohne den neuen Key erhalten `enabled: true` + `pytest-basetemp:
   true` (Framework-Default) — identisches Verhalten wie heute, nur ohne Literal.

**Quoting:** `TEST_COMMANDS` ist ein einzeiliger Shell-String; der eingesetzte Basetemp wird deshalb als
`--basetemp="<path>"` gerendert. Der Pfad darf kein `"`, keinen Zeilenumbruch und kein `$` enthalten
(Validator); damit funktionieren auch Pfade mit Leerzeichen (Windows/macOS-Profilordner) ohne
Worttrennung (AC-34).


**Verworfene Variante:** System-Temp pauschal für alle Tool-Ausgaben („einfach alles nach `/tmp`") —
widerspricht dem Ziel und dem Gefängnis-Modus; nicht weiterverfolgt.

---

## Fail-closed-Design (Hook)

### Vertrag

1. **Der Hook braucht einen Anker, nicht zwingend `cwd`.** Anker ist `cwd`, wenn der Key vorhanden und
   nicht leer ist (`repo-containment-impl.sh:151`). Fehlt er oder ist er leer (Antigravity-Adapter,
   `antigravity-json-adapter.sh:122-127`), wird **nicht** `$PWD` geadelt (`:152-154` entfällt), sondern:
   - Zielpfad **absolut** ⇒ Anker = `realpath(dirname(ziel))`. Der Root wird von dort per
     Ancestor-Suche gesucht. Damit bleibt ein Provider mit leerem `cwd` für Schreibziele **innerhalb**
     seines Projekts voll funktionsfähig; `/tmp/x` findet keinen Root und wird geblockt.
   - Zielpfad **relativ** (und kein `cwd`) ⇒ nicht absolut auflösbar ⇒ Exit 2,
     Code `repo-containment.no-root`.
   Begründung: der Zielpfad ist der Pfad, der tatsächlich geschrieben wird — ihn als Anker zu nehmen
   validiert genau den Schreibort und ist kein „Adeln" eines fremden Arbeitsverzeichnisses. Variante (i)
   aus dem Review („absolutes Ziel ohne Root direkt prüfen") wäre ein pauschaler Block, weil der Guard
   ohne Root keinen erlaubten Bereich kennt und damit jeden Write verweigern würde; sie ist verworfen.
2. **Kein Root ⇒ Block.** Findet `resolve_repo_root` (`:160-173`) vom Anker aus keinen Ancestor mit
   `.meta-config/`, wird **nicht** geadelt (`:175-180` entfällt), sondern Exit 2, Code
   `repo-containment.no-root`.
3. **Symlink-`cwd`:** `cwd` wird vor der Ancestor-Suche mit `realpath` normalisiert. Ist das Ergebnis
   abweichend, wird der aufgelöste Pfad als Basis verwendet und in der Meldung mitgenannt. Ein Symlink
   darf weder Root noch Basis stillschweigend verschieben.
4. **Relativer Zielpfad:** Basis ist `WORKDIR` (= aufgelöster `cwd`), **nicht** `REPO_ROOT`. Begründung:
   Prüf-Ort muss der Schreib-Ort sein. Ein relativer `file_path` wird provider-/tool-seitig gegen `cwd`
   aufgelöst; würde der Guard gegen `REPO_ROOT` prüfen, könnte er bei flachem `cwd` einen Write
   freigeben, der real woanders landet (Fail-open) oder einen legitimen In-Root-Write blocken.
   Payload-Evidenz: der Antigravity-Adapter mappt `args.Cwd` auf `cwd` (`:111`) und der Hook normalisiert
   `WORKDIR` (`:155-158`) — für Antigravity ist die Basis damit belegt; für Claude Code ist `cwd` das
   dokumentierte Payload-Feld und die Auflösungsbasis (Annahme A1, R11, mit AC-06/AC-33 verifiziert).
5. **Reihenfolge:** Root-Auflösung **vor** dem `enabled: false`-Kurzschluss (`:316-319`). Begründung:
   ohne Root ist die Config nicht lesbar; ein Opt-out eines fremden Projekts darf keinen Write außerhalb
   freischalten.
6. **`enabled: false`** bleibt wirksam und erlaubt weiterhin auch Outside-Writes innerhalb **dieses**
   Projekts (bestehender Test `tests/test_repo_containment_hook.py:151` bleibt gültig), sobald der Root
   auflösbar ist.

### Fehlermeldungen (verbindliche Form)

```
REPO_CONTAINMENT: no project root found above /tmp (code repo-containment.no-root).
  A project root is a directory that contains `.meta-config/`.
  This guard never promotes the working directory to a project root.
  target:    /tmp/x.py
  anchor:    /tmp            (payload `cwd`, or the target's own directory when `cwd` is missing)
  allowed:   only inside a project root (plus its configured tmp-sink)
  repair:    run `python scripts/sync.py` in the project, or open the session
             inside the project directory
  opt-out:   repo_containment.enabled: false in <project>/.meta-config/project.yaml
```

```
REPO_CONTAINMENT: no project root found for a relative target without `cwd`
(code repo-containment.no-root).
  A relative path cannot be anchored: the payload carried no `cwd` (or an empty one)
  and the target is not absolute. Failing closed.
  target:    notes.md
  repair:    re-run `python scripts/sync.py` for this provider (hook payload contract, issue #630);
             send an absolute `file_path`, or include `cwd` in the payload
```

Blockierte Ziele nennen künftig den **absoluten** Sink:
`allowed: paths under <abs root> and under <abs sink>`, nicht mehr `$REPO_ROOT/$SINK_PATH`
(`:381-386`). Es gibt **einen** Fehlercode für fehlenden Anker (`repo-containment.no-root`);
`repo-containment.no-cwd` entfällt, weil ein fehlendes `cwd` kein eigener Fehlerfall mehr ist.

### Bewusste Test-Änderung

`tests/test_repo_containment_hook.py:213-218` (`test_missing_config_defaults_to_containment_on`) **deckt
den Fail-open nicht ab** (Fixture ohne `.meta-config/`, Erwartung Exit 2, erreicht Exit 2 nur, weil das
Ziel `root.parent` außerhalb des geadelten Roots liegt — bei `cwd=/tmp` wäre es erlaubt). Dieser Test
wird **bewusst invertiert** und umbenannt (`test_missing_config_fails_closed`): Fixture ohne
`.meta-config/` ⇒ Exit 2 **mit** `repo-containment.no-root`, unabhängig davon, ob das Ziel unterhalb
oder oberhalb des `cwd` liegt. Zusätzlich entsteht ein Regressionstest für den eigentlichen
Fail-open-Fall (`cwd=/tmp`, Ziel `/tmp/x` ⇒ Exit 2) — dieser Fall ist heute **nicht** abgedeckt.

### Reparatur-Kanal

Vorhanden ist genau ein Signal: `scripts/lib/consistency/hook_drift.py::check_stale_deployed_hooks`
(aufgerufen im `_strict_findings`-Block, `scripts/lib/cli_commands.py:1418`) erkennt **Versionsdrift**
der deployten Hooks und meldet sie in `--validate`; die Block-Meldung selbst verweist auf `sync.py`.
Eine **Aggregation/Häufigkeitszählung** von `repo-containment.no-root` existiert nicht — der Hook
schreibt nur nach stderr an das Modell, es gibt keine Telemetrie. Diese Spec behauptet keine Zählung:
der Reparaturweg ist „Drift-Warnung plus Reparaturzeile plus erneuter Sync", nicht „gehäuftes Auftreten
wird erkannt". Wer eine persistente Senke will, braucht einen eigenen Beschluss (nicht Teil dieser Spec).

---

## Konfigurierbarkeit & Fehlerverhalten

| Fall | Sync-Zeit (Hard-Exit) | Laufzeit (Hook) | Template-Rendering | Fehlercode / Beispieltext |
|---|---|---|---|---|
| `repo_containment.enabled: false` | ok | Exit 0 (nur wenn Root auflösbar) | unverändert | — |
| `tmp-sink.enabled: false` | ok (`log.skip`, `sync_pipeline.py:238-240`); `resolve_tmp_paths` liefert `enabled=False`, **kein** Fehler | Ziele im Sink ⇒ Exit 2 (`BLOCK_SINK`) | `TMP_SINK_PATH` bleibt gesetzt (validiert, relativ); `TMP_SINK_ABS_PATH` und `TMP_SINK_ENV_PIN_BLOCK` entfallen; Report-Ziele bleiben benannt | Schreib-APIs werfen `tmp-sink.disabled` (bestehend, `repo_containment.py:582-587`); `tmp_env` und `tmp_sink_env_pin_block` ebenso |
| relativer Pfad (`scratch/out`) | ok | Sink = `<root>/scratch/out` | `{{TMP_SINK_PATH}}` = `scratch/out` | — |
| absoluter Pfad (`/var/tmp/x`) | **Exit 1** | — | — | `invalid 'repo_containment.tmp-sink.path' '/var/tmp/x': must be relative to the project root (absolute and UNC paths are not allowed). Migration: change tmp-sink.path to a relative path inside the repo, e.g. '.tmp' (default) or 'scratch/out'.` (`config.py:583-587`, `repo_containment.py:235-236`) |
| `..`-Escape (`../out`) | **Exit 1** | — | — | `must not contain '..' segments` (`repo_containment.py:243`) |
| Symlink im Pfad / als letztes Segment | **Exit 1** | Hook blockt Ziel (realpath) | — | `must not be a symlink, junction or reparse point` (`:290-292`) |
| Sink löst ins System-Temp auf | **Exit 1** | — | — | `resolves into the system temp directory` (`:376-378`) |
| Sink löst aus dem Repo hinaus | **Exit 1** | — | — | `resolves outside the project root` (`:379-380`) |
| nicht beschreibbarer Pfad | nicht geprüft (bewusst) | kein Block — der Hook prüft nur die Lage, nicht die Schreibbarkeit | — | Betriebsfehler des Tools, nicht des Guards (Convention boundary) |
| `system-temp-exception` nicht Mapping | **Exit 1** | Defaults (sicher) | — | `invalid 'repo_containment.tmp-sink.system-temp-exception': expected a mapping, got str.` |
| `system-temp-exception.enabled: false` + `pytest-basetemp: true` | **Exit 1** | — | — | `invalid 'repo_containment.tmp-sink.system-temp-exception': 'pytest-basetemp: true' requires 'enabled: true'.` |
| `system-temp-exception.enabled: false` + `toolchain-caches: true` | **Exit 1** | — | — | `invalid 'repo_containment.tmp-sink.system-temp-exception': 'toolchain-caches: true' requires 'enabled: true'.` (Q3) |
| `system-temp-exception.enabled: true` ohne `reason` | **Exit 1** | — | — | `invalid 'repo_containment.tmp-sink.system-temp-exception.reason': required when the exception is enabled (document why writes leave the repo).` |
| `gettempdir()` liegt im Projekt | **Exit 1** | — | — | `tmp-sink.system-temp-exception: platform temp root <dir> is inside the project root — the exception cannot take effect.` |
| `{{PYTEST_BASETEMP}}` bleibt unersetzt | **Exit 1** | — | — | `tmp-sink.pytest-token: '{{PYTEST_BASETEMP}}' was not resolved in TEST_COMMANDS/CODE_QUALITY_RULES.` |
| kein Projekt-Root zur Laufzeit | — | **Exit 2** | — | `repo-containment.no-root` |
| `cwd` fehlt/leer, Ziel absolut | — | normales Verdict (Anker = Zielverzeichnis) | — | kein Fehler; bei fehlendem Root `repo-containment.no-root` |
| `cwd` fehlt/leer, Ziel relativ | — | **Exit 2** | — | `repo-containment.no-root` (Meldung: „relative target without `cwd`") |
| Sink aktiv, aber Backup-Staging nicht auflösbar | — | Abbruch der Backup-Operation (Exit ≠ 0 der CLI) | — | `backup.tmp-sink.invalid-path` |
| Sink aus + Backup | — | WARNING + System-Temp (bewusst, damit Backup nie blockiert) | — | `backup.staging-system-temp` |
| Temp-Literal in Template/Standalone/Regel | — | — | WARNING in `--validate` | `temp-literal.system-temp` |

**Neue Fehlercodes (vollständig):** `repo-containment.no-root` (einziger Hook-Code für fehlenden Anker),
`tmp-sink.system-temp-exception`, `tmp-sink.pytest-token`, `backup.tmp-sink.invalid-path`,
`backup.staging-system-temp` (WARNING), `temp-literal.system-temp` (WARNING),
`temp-literal.sink-relative` (WARNING), `temp-literal.subprocess-env` (WARNING),
`temp-literal.toolchain-cache-in-repo` (WARNING), `temp-literal.provider-advisory` (WARNING).

**Bestehende Codes bleiben unverändert** (Downstream-Kompatibilität): `tmp-sink.disabled`,
`tmp-sink.invalid-path`, `tmp-sink.invalid-segment`, `out-outside-tmp-sink`,
`repo-containment.no-hook-support`. **Entfallen:** `repo-containment.no-cwd` (siehe Vertrag Punkt 1),
`tmp-sink.abs-path-unresolved` (nie eingeführt; `absolute` ist immer bestimmbar oder `None`).


---

## Provider-Agnostik

- **Durchsetzung ohne Hook (Opencode).** `has_hooks: false` (`config/ai-providers.yaml:252`) und
  `provider_hooks_supported(pc) == false` (`scripts/lib/providers.py:700`) bedeuten: kein Runtime-Gate.
  Die einzige verfügbare Schranke ist der datengetriebene Edit-Scope. Er wird deshalb **aus dem Sink
  abgeleitet** statt fest verdrahtet:
  - Eingelesen in `scripts/lib/provider_transform.py:477-484` aus der Provider-Tools-Config,
  - Scope-Bau in `:985-998` (`{"*": "deny", "<sink>/**": "allow", ".meta-viz/**": "allow"}`),
  - Quelle der Wahrheit ist `TmpPaths.relative`, nicht `config/provider-tools.yaml:64-66`.
  - Die statische Liste bleibt als **Fallback** für Aufrufer ohne Config-Kontext; sie darf dann nur
    `.meta-viz/**` enthalten, nicht `.tmp/**`.
- **Kein `if provider == "Name"`.** Die Ableitung hängt am Capability-Flag, nicht am Provider-Namen
  (Policy: `docs/concepts/repo-containment-prison-mode.md:31`, Skill `provider-agnostic`).
- **Was advisory bleibt (ehrlich benannt):**
  - Bash-Beispiele in Templates (Punkt 1 des Inventars) sind Prompt-Konvention. Ein hook-loser Provider
    kann sie nicht erzwingen; er kann nur den Edit-Scope begrenzen.
  - Pro-Rolle-`edit: allow` (`.opencode/agents/developer.md:13`) hebt die globale Deny-Regel
    (`opencode.json:39-46`) faktisch auf — das ist heute so und wird durch diese Spec **nicht** still
    verschärft (sonst brechen alle Worker-Rollen). Sichtbarkeit statt Verhalten:
    `check_repo_containment_support` (`scripts/lib/consistency/repo_containment.py:77-114`) meldet
    weiterhin `repo-containment.no-hook-support` als WARNING.
  - **Neu:** ein WARNING `temp-literal.provider-advisory` für Rollen, die im generierten Frontmatter
    `edit: allow` ohne Pfad-Scope tragen, solange der Provider keine Hooks hat.
- **UNVERIFIED:** Ein `permission.external_directory`-Key ist in diesem Repo-Stand **nicht belegt**. Er
  wird hier nur als Beobachtungspunkt genannt, **nicht** als tragende Maßnahme, und darf nicht zur
  einzigen Absicherung werden. Sollte er existieren, ist er ein zusätzlicher Defense-in-depth-Layer,
  dessen Semantik zuerst verifiziert werden muss.

---

## Toolchain-Ausnahme

**Default bleibt Nutzer-Cache außerhalb des Repos** (`~/.cache/pip`, `~/.npm/_cacache`,
`/var/lib/docker` bzw. Plattform-Pendants). Begründung:

1. **Repo-Größe:** Ein In-Repo-Cache wächst in den Arbeitsbaum, wird von Backups/Repo-Kopien erfasst
   (`tests/test_knowledge_engine.py:37-49` schließt nur bekannte Bäume aus) und macht das Repo als
   Submodul untragbar.
2. **Offline-/CI-Verhalten:** Ein Cache im Repo ist nicht teilbar und wird bei jedem fresh clone neu
   gefüllt; Nutzer-Caches sind über Runs hinweg warm.
3. **Cleanup-Semantik:** `cleanup: manual|on-sync` (`repo_containment.py:41,759`) löscht Top-Level-Einträge
   im Sink. Ein Cache dort würde bei `on-sync` mitgelöscht — stiller Performance-Verlust.

**Warum das „in der Regel im Repo" nicht verletzt:** Der Agent schreibt dort **nicht selbst**; der Cache
wird von der Toolchain verwaltet und ist kein Schreibziel einer Rollen-Anweisung. Die Regel adressiert
Agenten-Schreibzugriffe, nicht Tool-Interna.

**Enge, dokumentierte Ausnahme (Opt-in, Q3/ADR-13):**

```yaml
repo_containment:
  tmp-sink:
    system-temp-exception:
      toolchain-caches: false   # Default: false. true => pip/npm-Cache wird in den Sink gepinnt
```

- **Default ist bewusst `false`**, damit Toolchains nicht brechen: `pip`/`npm` nutzen weiter den warmen
  Nutzer-Cache, ohne dass ein Projekt etwas konfigurieren muss. Das Opt-in ist damit **bewusst und
  sichtbar** — es gibt keinen stillen Wechsel.
- Nur wenn `toolchain-caches: true` **und** `system-temp-exception.enabled: true`, setzt der Builder
  `PIP_CACHE_DIR=<absolute>/cache/pip` und `npm_config_cache=<absolute>/cache/npm` in
  `TMP_SINK_ENV_PIN_BLOCK` (dieselbe absolute Basis wie die dortigen `TMPDIR`/`TEMP`/`TMP`, ADR-12).
  `TmpPaths.env`/`tmp_env` bleiben **cache-neutral**: sie setzen ausschließlich `TMPDIR`/`TEMP`/`TMP`.
- `toolchain-caches: true` bei `enabled: false` ist wirkungslos und deshalb ein Config-Fehler ⇒ `_fail`
  mit Exit 1 (analog zur bestehenden `pytest-basetemp`-Regel).
- `docker` wird **nicht** umgeleitet (Daemon-Konfiguration außerhalb des Repos; nicht Agenten-schreibbar).
- Ein Opt-in erzeugt eine WARNING `temp-literal.toolchain-cache-in-repo` in `--validate`, damit die
  Entscheidung sichtbar bleibt. **Begründung der WARNING:** Ein In-Repo-Cache wächst in Backup, CI-Cache
  und Submodul-Mount hinein; `cleanup: on-sync` würde ihn löschen (stiller Performance-Verlust); und nach
  einem Repo-Umzug zeigt der Pin bis zum Re-Sync auf einen toten Pfad. Der Fehlercode ist ein Code, kein
  Config-Key — er bleibt unverändert, obwohl der Config-Key plural `toolchain-caches` heißt.

---

## Threat-Model (4 Fragen)

### 1. Was wird gebaut?

Ein Resolver, der den Scratch-Pfad einmalig auflöst, plus Injektion dieses Pfads an vierzehn Inventar-
Punkten — elf aktive Injektionen (Templates, Test-Kommandos, Subprozess-Env, Backup, Hook,
Provider-Scope, Guards, Provisionierung, Standalone-Export, Regeln, §5.5-Regeltext), zwei Konsumenten
(Managed-`.gitignore`, Doctor-Check) und eine dokumentierte Ausnahme (Adapter-`mktemp`) — sowie ein
fail-closed Hook-Verdict. Vier weitere Treffer sind begründet ausgenommen (Abschnitt N).


### 2. Was kann schiefgehen?

| Risiko | Auslöser | Wirkung |
|---|---|---|
| Anker aus dem Zielverzeichnis | leerer `cwd` und ein absolutes Ziel in einem fremden Baum, der ein `.meta-config/` trägt | dieser fremde Baum wird zum Root — dieselbe Vertrauensannahme wie beim `cwd` (ADR-08), bisher von keinem Test beobachtet (AC-37) |
| Guard-Selbstblockade | Hook blockt `.tmp`-Schreibzugriffe durch falsche Basis (relativer Pfad gegen `REPO_ROOT`) oder durch ein relatives Ziel bei fehlendem/leerem `cwd` | Agent kann seinen sanktionierten Scratch nicht mehr nutzen |
| Symlink/TOCTOU | Sink oder `cwd` ist ein Link, der zwischen Prüfung und Write getauscht wird | Prüfung sagt „innen", Write landet „außen" |
| Rekursion/Plattenplatz | Basetemp im Repo, Repo-Kopie ohne `.tmp`-Ausschluss | Unbegrenztes Wachstum (Vorfall 2026-09-19/20) |
| Falsche Erwartung auf hook-losen Providern | Opencode: kein Runtime-Gate | Nutzer glaubt an Durchsetzung, die es nicht gibt |
| Test-Suite rot | Neue Guards/geänderte Goldens | CI blockiert; Fehlschläge werden „weggefixt" und der Guard verliert Wirkung |
| Verhaltenswechsel bei Bestandsprojekten | Hook blockt plötzlich Writes, die vorher durchgingen | Arbeit stockt; Nutzer schaltet Containment ab (schlimmer als vorher) |
| Env-Pin bricht Fremd-Tools | `TMPDIR` zeigt auf einen fehlenden Pfad (Repo verschoben, kein Re-Sync) | Tool-Fehler, die wie Guard-Fehler aussehen; der Block prüft die Existenz vor dem Export (AC-36) |

### 3. Gegenmaßnahmen (mit ehrlicher Einordnung)

| Maßnahme | Einordnung |
|---|---|
| Exit 2 bei fehlendem Anker/Root, definierte Codes, Reparatur-Kanal | **Convention boundary** — blockt Akzident und naive Automatisierung, nicht einen gezielten Angreifer |
| Anker aus dem Zielpfad bei fehlendem/leerem `cwd` | **Convention boundary**; verhindert Provider-Selbstausschluss, ohne eine Write-Freigabe zu erzeugen (der geprüfte Pfad ist der Schreibpfad) |
| realpath vor Ancestor-Suche, realpath-Vergleich im Verdict | **Convention boundary**; TOCTOU bleibt offen (kein `O_NOFOLLOW`-Write im Hook möglich) |
| `TmpPaths.env` für alle Subprozesse, Env-Pin-Block für Agenten-Bash (beide absolut, ADR-12) | **Convention boundary**; ein `TMPDIR`-Override im Befehl umgeht sie |
| Backup-Staging im Sink | Betriebs-Hygiene, kein Sicherheitsgewinn |
| Opencode-Edit-Scope aus dem Sink | **Convention boundary** auf Provider-Ebene, aber immerhin runtime-nah (Permission-Layer) |
| Consistency-WARNINGs statt Hard-Exit für Literale | Bewusste Schwäche: Bestandsprojekte bleiben grün |
| Goldens/Guards für den Repo-eigenen Baum | Schutz gegen Regression im Framework selbst, nicht gegen Nutzerprojekte |
| Kein stiller Fallback in `resolve_*` | Fail-closed auf Bibliotheksebene; `TmpSinkError` statt System-Temp |

**Nicht behauptet:** OS-Sandbox, Schutz gegen bösartige Tool-Calls, Schutz gegen `eval`/`xargs`-
Indirektion in Bash (bekannte Grenze, `rules/1-generic/branch-guard.md:27,32`).

### 4. Konsequenzen

- **Worst Case legitime Writes blockiert:** Ein Agent arbeitet in einem Verzeichnis ohne
  `.meta-config/`-Ancestor (z. B. `/tmp`, `$HOME`) und wird beim ersten Write blockiert. Gewollt — die
  Meldung nennt Reparatur und Opt-out.
- **Test-Suite rot durch neue Guards:** Goldens, `test_writable_auditor_reports_into_repo_tmp`
  (`tests/test_template_report_paths.py:68-71`) und `test_missing_config_defaults_to_containment_on`
  (`tests/test_repo_containment_hook.py:213-218`) müssen **im selben** Plan-Schritt rebased werden, sonst
  ist die Suite dauerhaft rot und der Guard wird abgeschaltet.
- **Verhaltenswechsel bei Bestandsprojekten:** Projekte, die heute implizit im System-Temp arbeiten
  (Bash-Beispiele, Backup-Staging), schreiben künftig im Repo. Das ist gewollt, erzeugt aber neue
  Verzeichnisse im Sink und ggf. `.gitignore`-Bedarf (`ensure_tmp_sink_gitignore`, `:795`).
- **Betriebslast:** Ein `.tmp`-Basetemp (Option A) würde Cleanup erfordern; Option C vermeidet das.

---

## Interface Contracts

Legende: **neu** = existiert nicht, **erweitert** = Signatur/Verhalten ändert sich, **unverändert** =
nur zusätzlicher Konsument.

| Datei:Symbol | Signatur | Fehlerpfade | Status |
|---|---|---|---|
| `scripts/lib/tmp_paths.py::resolve_tmp_paths` | `(project_root: Path, config: dict \| None) -> TmpPaths` | **wirft nicht bei deaktiviertem Sink** (`enabled=False`); wirft `TmpSinkError`: `tmp-sink.invalid-path`, `tmp-sink.system-temp-exception`; nie `sys.exit` | neu |
| `scripts/lib/tmp_paths.py::SystemTempException` | `@dataclass(frozen=True)` Felder `enabled: bool`, `reason: str`, `pytest_basetemp: bool`, `toolchain_cache: bool`; das Feld `toolchain_cache` liest den YAML-Key `toolchain-caches` (Default `false`, Q3) | keine (reine Datenklasse; Validierung im Resolver: `tmp-sink.system-temp-exception`, inklusive `toolchain-caches: true` bei `enabled: false` ⇒ `_fail`/Exit 1) | neu |
| `scripts/lib/tmp_paths.py::TmpPaths` | `@dataclass(frozen=True)` Felder `relative: str`, `absolute: Path \| None`, `enabled: bool`, `system_temp_exception: SystemTempException`, `pytest_basetemp: str`, `env: dict[str, str]`; `env` enthält **ausschließlich absolute** Werte (`str(paths.absolute)`) | keine (reine Datenklasse); Invariante: `enabled is False` ⇔ `absolute is None` und `env == {}` | neu |
| `scripts/lib/tmp_paths.py::tmp_env` | `(paths: TmpPaths, base: dict \| None = None) -> dict[str, str]`; delegiert an `work_dir_env`, Werte immer absolut | `TmpSinkError` mit `tmp-sink.disabled`, wenn `paths.enabled is False` | neu |
| `scripts/lib/tmp_paths.py::tmp_sink_env_pin_block` | `(paths: TmpPaths) -> str`; POSIX-sh-Block, der `TMPDIR`, `TEMP` und `TMP` auf **denselben absoluten** Wert setzt (`str(paths.absolute)`, kein `relative`), mit Existenzprüfung **vor** dem Export; **nur bei `toolchain_cache: true`** zusätzlich `PIP_CACHE_DIR=<abs>/cache/pip` und `npm_config_cache=<abs>/cache/npm` (Q3, ADR-13) | `TmpSinkError` mit `tmp-sink.disabled`, wenn `paths.enabled is False` (der Builder setzt die Variable dann nicht) | neu |
| `scripts/lib/tmp_paths.py::resolve_pytest_basetemp` | `(project_root: Path, paths: TmpPaths) -> str` | `tmp-sink.system-temp-exception` (Temp-Root im Projekt, Ausnahme ohne `enabled`, Wert mit `"`) | neu |
| `scripts/lib/repo_containment.py::resolve_output_dir` | `(project_root: Path, config: dict \| None, subdir: str, *, tool: str = "") -> Path` | bestehend: `tmp-sink.disabled`, `tmp-sink.invalid-path`, `tmp-sink.invalid-segment`, `out-outside-tmp-sink` | unverändert (neuer Konsument: `backup.py`) |
| `scripts/lib/repo_containment.py::resolve_work_dir` | `(project_root, config, subdir, run_id, *, tool="") -> Path` | wie oben | unverändert |
| `scripts/lib/repo_containment.py::resolve_out_path` | `(project_root: Path, config: dict \| None, out: str, *, tool: str = "") -> Path`; validiert ein explizites `--out` per `realpath` gegen den Sink | bestehend: `tmp-sink.disabled`, `<tool>.out-outside-tmp-sink` | unverändert (Konsument in AC-24, bestehend `:671-701`) |
| `scripts/lib/repo_containment.py::work_dir_env` | `(work_dir: Path, base: dict \| None = None) -> dict` | keine (reine Env-Konstruktion; schreibt nicht) | unverändert (Aufruf nur noch über `tmp_env`) |
| `scripts/lib/repo_containment.py::resolve_effective_repo_containment` | `(config: dict \| None, provider: str \| None = None) -> ResolvedRepoContainment` | keine (nicht-exitierend) | unverändert; `tmp_paths.py` baut darauf auf |
| `scripts/lib/config.py::_build_orch_variables` | `(variables, config, …) -> None`; setzt neu `TMP_SINK_ABS_PATH`, `PYTEST_BASETEMP`, `TMP_SINK_ENV_PIN_BLOCK` (aus `tmp_sink_env_pin_block`, **absolute** Werte, ADR-12; Cache-Keys nur bei `toolchain-caches: true`) und ersetzt `{{PYTEST_BASETEMP}}` in `TEST_COMMANDS`/`CODE_QUALITY_RULES`; bei `enabled=False` entfallen `TMP_SINK_ABS_PATH` und `TMP_SINK_ENV_PIN_BLOCK` | `_fail`: `tmp-sink.pytest-token` (unersetztes Token) | erweitert (`:1539-1542` bestehend) |
| `scripts/lib/config.py::_validate_repo_containment` | `(config: dict, config_path: Path) -> None` | `_fail` (Exit 1) für `system-temp-exception`-Struktur, Widerspruch `pytest-basetemp`/`enabled`, Widerspruch `toolchain-caches`/`enabled` (Q3), fehlenden `reason`, `gettempdir()` im Projekt | erweitert (`:483-587`) |
| `scripts/lib/consistency/placeholders.py::_BUILTIN_VARS` | `set[str]`; neu `TMP_SINK_ABS_PATH`, `PYTEST_BASETEMP`, `TMP_SINK_ENV_PIN_BLOCK` | keine eigenen Fehlerpfade (Registrierung; Drift meldet der bestehende Placeholder-Check) | erweitert (`:136` bestehend) |
| `scripts/lib/consistency/temp_literals.py::check_temp_literals` | `(agent_meta_root: Path, project_root: Path, config: dict \| None) -> list[Finding]`; Scope `agents/**`, `standalone/**`, `rules/1-generic/**`, `config/**`, `tests/fixtures/slimming-golden/**`, `tests/conftest.py` | Findings `temp-literal.system-temp`, `temp-literal.sink-relative`, `temp-literal.subprocess-env`, `temp-literal.toolchain-cache-in-repo`, `temp-literal.provider-advisory` (alle WARNING) | neu |
| `scripts/lib/cli_commands.py` (`_strict_findings`-Block) | Aufruf `_strict_findings += check_temp_literals(...)` vor `print_report` (`:1411-1426`) | keine eigenen Fehlerpfade; Exit-Code kommt aus `print_report` | erweitert |
| `hooks/1-generic/repo-containment-impl.sh::resolve_repo_root` | `(dir) -> 0\|1`; kein Fallback auf `$PWD`; Aufrufer wählt den Anker (`cwd` oder Zielverzeichnis) | Exit 2 + `repo-containment.no-root` beim Aufrufer | erweitert (`:160-180`) |
| `hooks/1-generic/repo-containment-impl.sh::containment_verdict` | `(raw_target) -> "ALLOW"\|"BLOCK"\|"BLOCK_SINK"`; Basis für relative Ziele = `WORKDIR` (realpath von `cwd`) | leerer Output ⇒ BLOCK (bestehend) | Basis unverändert (`:347`), Verdict-Aufrufer neu |
| `scripts/lib/gitignore.py::_tmp_sink_gitignore_entry` | `(paths: TmpPaths) -> str \| None`; Eintrag aus `paths.relative`, kein eigener Resolver-Aufruf | `enabled=False` ⇒ `None` (kein Eintrag) | erweitert (`:324-339`) |
| `scripts/lib/doctor_detectors.py::_sink_hits` | `(env: Env) -> list[Hit]`; Finding bleibt `CHECK_TMP_SINK`, Auflösung aus `TmpPaths` | `enabled=False` ⇒ kein Sink-Finding | erweitert (`:403-411`) |
| `scripts/lib/standalone.py::_standalone_variables` | `(agent_meta_root: Path) -> dict`; setzt zusätzlich `TMP_SINK_PATH = ".tmp"` und `TMP_SINK_ENV_PIN_BLOCK = ""` (kein Maschinenpfad, keine Platzhalter-Notiz) | keine (Fallbacks statt Fehler; Standalone hat keine Projekt-Config) | erweitert (`:254-282`) |
| `scripts/lib/backup.py::create_backup` | Staging via `TemporaryDirectory(dir=<abs>/backup-staging)`; Fallback nur bei `tmp-sink.disabled` | `backup.tmp-sink.invalid-path`; WARNING `backup.staging-system-temp` | erweitert (`:338-341`) |
| `scripts/lib/provider_transform.py::_transform_frontmatter_for_opencode` | zusätzlicher Parameter `edit_allow_paths` **aus `TmpPaths`** statt aus der statischen Liste | `deny_edit` + leere Pfade ⇒ `edit: deny` (bestehend `:998`) | erweitert (`:477-484`, `:985-998`) |
| `scripts/lib/sync_pipeline.py::_sync_tmp_sink` | nutzt `resolve_tmp_paths` statt eigener Auflösung; unverändertes Provisionierungsverhalten | keine neuen Fehlerpfade; bei deaktiviertem Sink `log.skip` (bestehend) | erweitert (`:238-269`) |
| `hooks/1-generic/antigravity-json-adapter.sh` | `ARG_KEY_MAP` wird um `'FilePath': 'file_path'` erweitert (Q10, ADR-15), damit `args.FilePath` als `tool_input.file_path` beim Hook ankommt; `_ERR_FILE` bleibt `mktemp` im System-Temp (`:167-168`) | keine Änderung am Deny/Allow-Vertrag; ohne den Eintrag blockt der Hook jeden Write fail-closed (`repo-containment-impl.sh:391-397`) | erweitert (Mapping) / unverändert (`mktemp`-Ausnahme, ADR-11) |
| `.meta-config/temp-literal-allowlist.yaml` | Liste mit **Pflichtfeldern** `path`, `pattern`, `reason` und optional `owner`; `expires` ist **kein** Schema-Teil (Q6, ADR-14) | vollständiger Eintrag ⇒ Verstoß unterdrückt; fehlendes `reason` oder nicht unterstütztes Feld (z. B. `expires`) ⇒ Verstoß bleibt WARNING **und** der ungültige Eintrag wird als WARNING derselben Check-Familie gemeldet; unbekannter Verstoß ohne Eintrag ⇒ WARNING | neu |
| `.meta-config/temp-env-allowlist.yaml` | Liste `{path, symbol, reason}` für Subprozesse ohne Env-Pin (Inventar 3) | unbegründeter Aufruf ⇒ WARNING `temp-literal.subprocess-env` | neu |
| `tests/conftest.py::_EXTERNAL_BASETEMP_HINT` | statischer Text ohne `/tmp`-Literal; Hinweis verweist auf `PYTEST_BASETEMP` | keine (statischer Hinweistext) | erweitert (`:28`) |


---

## Datenfluss

### Sync-Zeit

```
.meta-config/project.yaml
  └─ load_config → _validate_repo_containment           # Exit 1 bei ungueltiger Config
       └─ resolve_tmp_paths(project_root, config)        # relative + absolute + basetemp + env
            ├─ _build_orch_variables
            │    ├─ TMP_SINK_PATH          (relativ)     → Template-Render (agents/**, rules/**)
            │    ├─ TMP_SINK_ABS_PATH      (absolut)     → nur Python-Konsumenten (Backup, Meldungen)
            │    ├─ PYTEST_BASETEMP        (absolut/plattformneutral)
            │    │    └─ Token-Ersetzung in TEST_COMMANDS / CODE_QUALITY_RULES
            │    └─ TMP_SINK_ENV_PIN_BLOCK (export TMPDIR=<absolut>, ADR-12
            │         + PIP_CACHE_DIR/npm_config_cache nur bei toolchain-caches: true) → Agenten-Prompt
            ├─ provider_transform: edit_allow_paths = [<relative>/** , .meta-viz/**]
            ├─ hooks: Wrapper/Impl deployen (Provider gebacken, Sink NICHT gebacken)
            ├─ gitignore: _tmp_sink_gitignore_entry(<relative>) → Managed-Block
            ├─ doctor: _sink_hits(<TmpPaths>) → CHECK_TMP_SINK (nur Meldung)
            ├─ standalone: _standalone_variables(TMP_SINK_PATH=".tmp", TMP_SINK_ENV_PIN_BLOCK="") → standalone/agents/**
            └─ _sync_tmp_sink: cleanup → ensure_tmp_sink (MKDIR) → ensure_tmp_sink_gitignore
```

Bei `enabled: false` endet der Baum nach `_build_orch_variables`: `TMP_SINK_PATH` ist gesetzt,
`TMP_SINK_ABS_PATH`/`TMP_SINK_ENV_PIN_BLOCK` fehlen, `_sync_tmp_sink` läuft `log.skip`, der
Managed-`.gitignore`-Eintrag entfällt, Schreib-APIs werfen `tmp-sink.disabled` erst bei Bedarf.

### Laufzeit (Hook pro Write/Edit/Bash)

```
Payload {tool_name, tool_input.file_path|command, cwd}
  └─ Anker bestimmen:
       ├─ cwd vorhanden und nicht leer → realpath(cwd)
       └─ cwd fehlt/leer:
            ├─ Ziel absolut   → realpath(dirname(ziel))          [kein $PWD, kein Adeln]
            └─ Ziel relativ   → Exit 2  (repo-containment.no-root)
  └─ resolve_repo_root (Ancestor mit .meta-config/)
       ├─ nicht gefunden → Exit 2  (repo-containment.no-root)
       └─ gefunden → read_effective_containment(REPO_ROOT)      [safe-side Defaults]
            └─ enabled == false → Exit 0
                 └─ containment_verdict:
                      Ziel = realpath(raw) bei absolutem Pfad
                             realpath(WORKDIR / raw) bei relativem Pfad   [Pruef-Ort = Schreib-Ort]
                      Sink = realpath(REPO_ROOT / sink)
                      ├─ im Sink  → ALLOW (Sink an) / BLOCK_SINK (Sink aus)
                      ├─ im Root  → ALLOW
                      └─ sonst    → BLOCK (Exit 2, absolute Pfade in der Meldung)
```

Antigravity-Sonderfall: Der Adapter liefert `cwd=''`, wenn weder `cwd`, `workspacePaths` noch
`args.Cwd` gefüllt sind (`antigravity-json-adapter.sh:122-127`); der Anker kommt dann aus dem Ziel.
Ein Write mit absolutem Pfad innerhalb des Workspace bleibt erlaubt; `/tmp/x` bleibt blockiert.

Der Adapter normalisiert die AGY-Argumentnamen vor dem Hook: `args.CommandLine` → `command`,
`args.Cwd` → `cwd` und — **neu entschieden (Q10/ADR-15)** — `args.FilePath` → `file_path`
(`ARG_KEY_MAP`, `antigravity-json-adapter.sh:111`). Ohne den dritten Eintrag fällt `FilePath`
unverändert durch, der Hook findet kein `tool_input.file_path` (`repo-containment-impl.sh:391-397`) und
blockt den Write fail-closed ohne Pfadprüfung.

### Test-Lauf

```
Builder → PYTEST_BASETEMP (Config + system-temp-exception)
  └─ TEST_COMMANDS-Render: python3 -m pytest tests/ --basetemp="<PYTEST_BASETEMP>"
       └─ pytest startet → tests/conftest.py prüft effective_basetemp gegen Repo-Root
            ├─ innerhalb  → Warning (Warning-only bleibt, tests/conftest.py:56-65)
            └─ ausserhalb → kein Hinweis; Suite laeuft isoliert (13 Fehlschlaege bleiben aus)
```

Fail-closed-Hook-Tests brauchen zusätzlich eine **eigene** Isolation: ihre Fixture-Wurzel muss
physisch außerhalb des Repo-Baums liegen, sonst findet die Ancestor-Suche das echte `.meta-config/`
(Abschnitt J). Das gilt unabhängig davon, ob Option A oder C gewählt wird.


---

## Acceptance Criteria

**AC-01 — Kein System-Temp-Literal in Agenten-Templates.**
Gegeben: `agents/**`. Wenn: mit dem exakten Muster `(^|[^A-Za-z0-9_.-])(/tmp/|%TEMP%|[A-Za-z]:\\\\Temp\\\\)`
(case-sensitive, Pfadkontext, keine Treffer in „Template"/„temporary") gesucht wird. Dann: keine Treffer
außer den in `.meta-config/temp-literal-allowlist.yaml` deklarierten, vollständigen Einträgen
(`path`, `pattern`, `reason`; optional `owner` — Schema nach Q6/IC-11).
Test: `tests/test_temp_literals.py::test_no_system_temp_literal_in_agents`.

**AC-02 — Kein Sink-Literal in Report-Ziel-Anweisungen der vier Templates.**
Gegeben: `agents/1-generic/ai-security-guardian.md`, `app-lifecycle-governor.md`, `prompt-governor.md`,
`security-auditor.md`. Wenn: gerendert. Dann: das Report-Ziel enthält `{{TMP_SINK_PATH}}`; `\.tmp/` kommt
in dieser Ziel-Anweisung nicht mehr vor.
Test: `tests/test_template_report_paths.py::test_writable_auditor_reports_into_configured_sink`
(ersetzt `:68-71`).

**AC-03 — Hook fail-closed ohne Projekt-Root.**
Vorbedingung (basetemp-unabhängig, RVW-07): die Fixture-Wurzel liegt physisch außerhalb des Repo-Baums
(`tempfile.mkdtemp(dir=tempfile.gettempdir())`, per Assertion geprüft, dass kein Ancestor `.meta-config/`
enthält) — nicht `tmp_path`, dessen Lage vom gewählten Basetemp abhängt.
Gegeben: Fixture ohne `.meta-config/`-Ancestor, Payload mit `cwd=<fixture>` und Ziel innerhalb `<fixture>`.
Wenn: Hook läuft. Dann: Exit 2 und stderr enthält `repo-containment.no-root`.
Test: `tests/test_repo_containment_hook.py::test_missing_config_fails_closed` (ersetzt `:213-218`).

**AC-04 — Relative Ziele ohne `cwd` sind nicht auflösbar.**
Vorbedingung: wie AC-03 (Fixture außerhalb des Repo-Baums).
Gegeben: Payload ohne `cwd`-Key, `tool_name=Write`, `file_path` relativ. Wenn: Hook läuft. Dann: Exit 2,
stderr enthält `repo-containment.no-root` und den Hinweis „relative target without `cwd`".
Test: `tests/test_repo_containment_hook.py::test_relative_target_without_cwd_fails_closed`.

**AC-05 — Der echte Fail-open-Fall ist blockiert.**
Vorbedingung: wie AC-03; `cwd` und Ziel liegen im System-Temp (nicht im Repo).
Gegeben: `cwd=/tmp` (bzw. `tempfile.gettempdir()`), Ziel `<temp>/x.py`, kein `.meta-config/` oberhalb.
Wenn: Hook läuft. Dann: Exit 2 mit `repo-containment.no-root`.
Test: `tests/test_repo_containment_hook.py::test_cwd_outside_project_cannot_be_adopted`.

**AC-06 — Relativer Zielpfad wird gegen `cwd` geprüft (Prüf-Ort = Schreib-Ort).**
Vorbedingung: wie AC-03 nur für den Negativfall; der Positivfall nutzt eine Fixture mit `.meta-config/`.
Gegeben: `cwd=<fixture>/.tmp/sub`, `file_path="notes.md"`. Wenn: Hook läuft. Dann: Exit 0, und die
Auswertung bezieht sich auf `<fixture>/.tmp/sub/notes.md` (denselben Pfad, den das Tool schreiben würde).
Test: `tests/test_repo_containment_hook.py::test_relative_target_resolves_against_cwd`.

**AC-07 — Symlink-`cwd` wird aufgelöst.**
Vorbedingung: wie AC-03 (Symlink zeigt auf ein Verzeichnis außerhalb jedes Projekts).
Gegeben: `cwd` ist ein Symlink auf ein Verzeichnis außerhalb jedes Projekts. Wenn: Hook läuft. Dann:
Exit 2 (`repo-containment.no-root`) und stderr nennt den realpath.
Test: `tests/test_repo_containment_hook.py::test_symlinked_cwd_uses_realpath`.

**AC-08 — `enabled: false` bleibt bei auflösbarem Root projektlokal wirksam.**
Gegeben: gültiger Root mit `repo_containment.enabled: false`. Wenn: Outside-Write im Payload. Dann:
Exit 0 (bestehendes Verhalten).
Test: `tests/test_repo_containment_hook.py::test_disabled_mode_allows_even_an_outside_write` (bleibt).


**AC-09 — Backup-Staging liegt im Sink.**
Gegeben: Sink aktiv (`path: .tmp`), Backup-Lauf. Wenn: `create_backup` läuft. Dann: das Staging-Verzeichnis
liegt unter `<repo>/.tmp/...`; `tempfile.gettempdir()` wird nicht als Staging-Basis verwendet.
Test: `tests/test_backup_round_trip_804.py::test_staging_dir_is_inside_tmp_sink`.

**AC-10 — Backup ohne Sink bleibt funktionsfähig und laut.**
Gegeben: `tmp-sink.enabled: false`. Wenn: `create_backup` läuft. Dann: System-Temp-Staging **mit**
WARNING `backup.staging-system-temp`; Backup-Ergebnis unverändert erfolgreich.
Test: `tests/test_backup_robustness.py::test_staging_falls_back_to_system_temp_with_warning`.

**AC-11 — Alle Framework-Subprozesse erhalten das Env-Pinning.**
Gegeben: `scripts/**` (nicht nur `scripts/lib/**`; die 12 Aufrufe in `scripts/*.py` sind namentlich
bekannt). Wenn: jeder `subprocess.run`/`Popen`-Aufruf geprüft wird. Dann: jeder, der Temp-Dateien
erzeugen kann, übergibt `env=tmp_env(...)`; alle übrigen stehen mit `{path, symbol, reason}` in
`.meta-config/temp-env-allowlist.yaml` (Kriterium für „kann Temp-Dateien erzeugen": der Aufruf startet
kein `git`-Plumbing und keinen reinen Lese-Befehl, oder er erzeugt nachweislich keine temporären
Dateien).
Test: `tests/test_tmp_sink_env_coverage.py::test_subprocess_calls_pin_temp_env`.


**AC-12 — `TMPDIR`/`TEMP`/`TMP` zeigen auf den absoluten Sink.**
Gegeben: `TmpPaths` mit `relative=".tmp"`. Wenn: `tmp_env()` aufgerufen wird. Dann: alle drei Keys sind
absolut (`os.path.isabs()` wahr, also kein relativer Env-Wert), existieren als Verzeichnis und liegen unter
dem Projekt-Root.
Test: `tests/test_tmp_sink_output_dirs.py::test_tmp_env_pins_absolute_sink`.

**AC-13 — `TEST_COMMANDS` und `CODE_QUALITY_RULES` sind literal-frei.**
Gegeben: gerenderte Variablen mit `system-temp-exception.enabled: true`. Wenn: `build_variables` läuft.
Dann: beide Werte enthalten kein `/tmp`, `%TEMP%`, `C:\\Temp` und keinen `$USER`-Shell-Ausdruck; der
`--basetemp`-Wert ist absolut oder ein plattformneutraler Temp-Root-Pfad und **shell-gequotet**.
Test: `tests/test_tmp_sink_output_dirs.py::test_test_commands_have_no_system_temp_literal`.


**AC-14 — Unersetztes Token bricht den Sync hart.**
Gegeben: `TEST_COMMANDS` enthält `{{PYTEST_BASETEMP}}`, während der Builder keinen aufgelösten Wert hat
(Regression: Token-Ersetzung entfernt oder übersprungen). Wenn: Sync läuft. Dann: Exit 1 mit
`tmp-sink.pytest-token` — ein Literal oder ein stehengebliebenes Token wird nie still ausgeliefert.
Test: `tests/test_repo_containment_validate.py::test_unresolved_pytest_token_fails_sync`.

**AC-15 — `system-temp-exception` ist validiert (ein Test je Fall).**
Gegeben: die Matrix aus [Konfigurierbarkeit](#konfigurierbarkeit--fehlerverhalten) — vier Fälle: kein
Mapping, `pytest-basetemp: true` bei `enabled: false`, fehlender `reason`, `gettempdir()` im Projekt.
Wenn: `sync.py --validate` läuft. Dann: Exit 1 mit dem dokumentierten Fehlertext — **ein eigener
Testparameter je Fall**, kein Sammelassert. Der fünfte Matrixfall (`toolchain-caches: true` bei
`enabled: false`, Q3) ist bewusst **nicht** Teil dieser AC, sondern hat seinen eigenen Test in AC-38.
Test: `tests/test_repo_containment_schema.py::test_system_temp_exception_matrix`
(parametrisiert, 4 Fälle) und
`tests/test_repo_containment_validate.py::test_system_temp_exception_rejects_invalid_config`.


**AC-16 — `TMP_SINK_PATH` bleibt relativ, `TMP_SINK_ABS_PATH` ist absolut.**
Gegeben: `path: .tmp`. Wenn: `build_variables` läuft. Dann: `TMP_SINK_PATH == ".tmp"`,
`TMP_SINK_ABS_PATH == <repo>/.tmp` (realpath, `os.path.isabs()` wahr, kein Symlink-Endsegment).
Test: `tests/test_tmp_sink_output_dirs.py::test_relative_and_absolute_sink_variables`.

**AC-17 — Opencode-Edit-Scope folgt dem konfigurierten Sink.**
Gegeben: `path: scratch/out`, `orchestrator.mode: strict`, Runtime-Gate aktiv. Wenn: der Opencode-Orchestrator
generiert wird. Dann: `permission.edit = {"*": "deny", "scratch/out/**": "allow", ".meta-viz/**": "allow"}`;
`.tmp/**` erscheint nicht.
Test: `tests/test_opencode_primary_edit_lock.py::test_edit_allow_derived_from_tmp_sink`.

**AC-18 — Hook-Meldungen nennen absolute Pfade.**
Gegeben: geblockter Outside-Write mit Sink `.tmp`. Wenn: Hook blockt. Dann: stderr enthält den absoluten
Repo-Root **und** den absoluten Sink; kein `$REPO_ROOT/$SINK_PATH`-Konstrukt.
Test: `tests/test_repo_containment_hook.py::test_block_message_uses_absolute_sink`.

**AC-19 — Goldens sind rebased.**
Gegeben: `tests/test_template_slimming_equivalence.py` und `tests/fixtures/slimming-golden/**`. Wenn: die
Suite läuft. Dann: alle Varianten (`OG-TAIL-DOCKER`, `OG-TAIL-DEV`, `OG-PASS-CODE-REVIEWER`,
Fixture-Rollen) sind grün und enthalten kein `/tmp`-Literal.
Test: `tests/test_template_slimming_equivalence.py` (bestehend, Golden-Daten aktualisiert).

**AC-20 — Provider ohne Hooks bleiben advisory, aber sichtbar.**
Gegeben: Opencode aktiv, `has_hooks: false`. Wenn: `sync.py --validate` läuft. Dann: WARNING
`repo-containment.no-hook-support` wird ausgegeben und der Lauf endet mit Exit 0.
Test: `tests/test_repo_containment_consistency.py::test_no_hook_support_warning_still_emitted`.

**AC-21 — Temp-Literal-Check ist wirksam und nicht blockierend.**
Gegeben: ein Template mit `/tmp/x`. Wenn: `--validate` läuft. Dann: WARNING `temp-literal.system-temp` mit
Datei und Zeile; Exit 0. Mit einem **vollständigen** Allowlist-Eintrag (`path`, `pattern`, `reason`):
keine Meldung. Ein Eintrag ohne `reason` oder mit einem nicht unterstützten Feld (z. B. `expires`)
unterdrückt die Meldung **nicht** — der Verstoß bleibt WARNING, und der ungültige Eintrag wird
zusätzlich als WARNING derselben Check-Familie gemeldet (Q6, ADR-14; Schema-Details IC-11, Tests AC-39).
Test: `tests/test_consistency_temp_literals.py::test_warning_and_allowlist`.

**AC-22 — Vage Temp-Anweisungen sind ersetzt.**
Gegeben: die 13 Rollen aus Ist-Zustand E (12 SE-Rollen + `test-executor`). Wenn: gerendert. Dann: nennt jede Anweisung den
konfigurierten Sink (`{{TMP_SINK_PATH}}`) als Schreibort für das Zwischenartefakt, oder begründet explizit
einen anderen Ort.
Test: `tests/test_template_report_paths.py::test_atomic_write_names_tmp_sink`.

**AC-23 — `resolve_tmp_paths` wirft nicht bei deaktiviertem Sink.**
Gegeben: `repo_containment.tmp-sink.enabled: false`, `path: .tmp`. Wenn: `resolve_tmp_paths` aufgerufen
wird. Dann: Rückgabe ohne Exception mit `enabled is False`, `relative == ".tmp"`, `absolute is None`,
`env == {}`.
Test: `tests/test_tmp_sink_output_dirs.py::test_resolver_does_not_raise_when_sink_disabled`.

**AC-24 — Schreib-APIs werfen weiterhin `tmp-sink.disabled`.**
Gegeben: dieselbe Config (`enabled: false`). Wenn: `resolve_output_dir`, `resolve_work_dir`,
`resolve_out_path` oder `tmp_env` aufgerufen wird. Dann: jeweils `TmpSinkError` mit Code
`tmp-sink.disabled` (bzw. `<tool>.tmp-sink.disabled`).
Test: `tests/test_tmp_sink_output_dirs.py::test_writers_still_raise_when_sink_disabled`.

**AC-25 — Sync mit deaktiviertem Sink ist erfolgreich und setzt `TMP_SINK_PATH`.**
Gegeben: `enabled: false`. Wenn: `sync.py --dry-run` läuft. Dann: Exit 0, `TMP_SINK_PATH` ist gesetzt
(relativ, validiert), `TMP_SINK_ABS_PATH` und `TMP_SINK_ENV_PIN_BLOCK` sind nicht gesetzt,
`_sync_tmp_sink` protokolliert `log.skip`.
Test: `tests/test_repo_containment_validate.py::test_disabled_sink_sync_is_not_an_error`.

**AC-26 — Standalone-Export ist literal-frei und drift-frei.**
Gegeben: `standalone/agents/**` nach Regeneration. Wenn: `sync.py --render-standalone --check` läuft und
der Temp-Literal-Check über `standalone/**` läuft. Dann: Exit 0 (kein Drift) und kein Treffer für
`/tmp/` bzw. `.tmp/<role>-` außer Allowlist-Einträgen.
Test: `tests/test_temp_literals.py::test_no_system_temp_literal_in_standalone`
plus bestehendes Drift-Gate (`cli_commands.py:496-508`).

**AC-27 — Standalone nennt den Framework-Default-Sink statt einer Platzhalter-Notiz.**
Gegeben: `standalone/agents/meta-doctor.md`, `meta-optimizer.md`, `agent-meta-manager.md`. Wenn:
gerendert. Dann: Report-Ziele nennen `.tmp/...`; die Zeichenkette
`[TMP_SINK_PATH — not available outside a full agent-meta install]` kommt in `standalone/**` nicht mehr
vor.
Test: `tests/test_standalone_render.py::test_tmp_sink_path_uses_framework_default`.

**AC-28 — Leerer `cwd`: der Anker kommt aus dem Zielverzeichnis (Hook-Unit-Test).**
Vorbedingung: Fixture mit `.meta-config/`; Payload-Feld `cwd` vorhanden, aber `""`. Der Test prüft die
Ankerwahl auf Hook-Ebene; die Adapter-Zuordnung `args.FilePath` → `tool_input.file_path` ist mit Q10
entschieden (ADR-15) und wird in AC-40 geprüft, nicht hier.
Gegeben: `cwd=""`, `tool_name=Write`, `tool_input.file_path=<fixture>/notes.md` (absolut, innerhalb des
Roots). Wenn: Hook läuft. Dann: Exit 0, und der Anker ist das Verzeichnis des Ziels, nicht `$PWD`.
Test: `tests/test_repo_containment_hook.py::test_empty_cwd_anchors_on_absolute_target`.

**AC-29 — Leerer `cwd` plus Ziel im System-Temp bleibt blockiert.**
Vorbedingung: `cwd=""`, Ziel absolut im System-Temp, kein `.meta-config/` oberhalb des Ziels.
Gegeben: `file_path=<temp>/x.py`. Wenn: Hook läuft. Dann: Exit 2 mit `repo-containment.no-root`.
Test: `tests/test_repo_containment_hook.py::test_empty_cwd_does_not_allow_system_temp`.

**AC-30 — Adapter-Ausnahme bleibt lokal und wird aufgeräumt.**
Gegeben: Adapter-Lauf mit einem Ziel-Hook, der blockt. Wenn: der Lauf endet. Dann: der Deny-Vertrag auf
stdout ist unverändert, im Repo-Arbeitsbaum entsteht keine neue Datei, und die `mktemp`-Datei existiert
nach Prozessende nicht mehr.
Test: `tests/test_antigravity_hooks_registration.py::test_adapter_temp_file_is_cleaned_up`.

**AC-31 — Managed-`.gitignore`-Eintrag folgt dem konfigurierten Sink.**
Gegeben: `repo_containment.tmp-sink.path: scratch/out`, `gitignore: true`. Wenn: der Managed-Block
generiert wird. Dann: der Eintrag lautet `scratch/out/`; bei `enabled: false` entfällt der Eintrag.
Test: `tests/test_gitignore_managed_block.py::test_tmp_sink_entry_uses_resolved_path`.

**AC-32 — Doctor-Finding nutzt dieselbe Auflösung.**
Gegeben: `tmp-sink.path: ../out`. Wenn: `--doctor` läuft. Dann: Finding `CHECK_TMP_SINK` mit
`reason == "must not contain '..' segments"` — identisch zum Validator-Text, ohne eigene Parser-Kopie.
Test: `tests/test_doctor.py::test_tmp_sink_check_uses_resolver_reason`.

**AC-33 — Relativer Zielpfad mit `cwd`-Tiefe wird am realen Ziel geprüft.**
Vorbedingung: Fixture mit `.meta-config/`, Ziel existiert als `<fixture>/x`.
Gegeben: `cwd=<fixture>/a/b`, `file_path="../../x"`. Wenn: Hook läuft. Dann: Exit 0; bei
`cwd=<fixture>/a/b`, `file_path="../../../../etc/passwd"` dagegen Exit 2 (Ziel außerhalb des Roots).
Test: `tests/test_repo_containment_hook.py::test_relative_target_is_judged_at_its_real_location`.

**AC-34 — Basetemp mit Leerzeichen bricht den Suite-Aufruf nicht.**
Gegeben: `system-temp-exception.enabled: true` und ein Temp-Root, der ein Leerzeichen enthält (per
Monkeypatch von `tempfile.gettempdir()`). Wenn: `TEST_COMMANDS` gerendert und durch die Shell geparst
wird. Dann: `--basetemp="<path with space>"` ergibt genau ein Argument; das Verzeichnis wird von pytest
angelegt.
Test: `tests/test_tmp_sink_output_dirs.py::test_basetemp_with_spaces_is_single_argument`.

**AC-35 — `TMP_SINK_ENV_PIN_BLOCK` setzt ausschließlich absolute Werte.**
Gegeben: `path: .tmp`, Sink aktiv. Wenn: `build_variables` läuft. Dann: der Block setzt `TMPDIR`, `TEMP` und
`TMP` jeweils auf denselben Wert, jeder Wert erfüllt `os.path.isabs()` und ist identisch mit
`TMP_SINK_ABS_PATH`; ein relativer Wert (`.tmp`) erscheint nicht als Zuweisung.
Test: `tests/test_tmp_sink_output_dirs.py::test_env_pin_block_is_absolute`.

**AC-36 — Env-Pin-Block exportiert keinen toten Pfad.**
Vorbedingung: gerenderter Block; das genannte Sink-Verzeichnis existiert nicht (Repo verschoben, kein
Re-Sync).
Gegeben: der Block wird in einer POSIX-Shell ausgeführt. Wenn: das Verzeichnis fehlt. Dann: `TMPDIR`, `TEMP`
und `TMP` bleiben unverändert (kein Export auf den toten Pfad) und stderr nennt den Reparaturweg
`python scripts/sync.py`.
Test: `tests/test_tmp_sink_output_dirs.py::test_env_pin_block_refuses_missing_directory`.

**AC-37 — Anker aus dem Ziel bei leerem `cwd` wählt das Projekt des Ziels (dokumentierte Annahme).**
Gegeben: `cwd=""`, Ziel absolut in einem fremden Baum, der ein `.meta-config/` trägt, kein weiterer Root
oberhalb. Wenn: Hook läuft. Dann: Exit 0, und als Root gilt der fremde Baum — der Test hält die in ADR-08
offengelegte Vertrauensannahme fest, statt sie ungetestet zu lassen.
Test: `tests/test_repo_containment_hook.py::test_empty_cwd_uses_project_of_absolute_target`.

**AC-38 — Toolchain-Caches sind ein Opt-in und niemals Default (Q3).**
Gegeben: Default-Config (`system-temp-exception.enabled: true`, `toolchain-caches` nicht gesetzt). Wenn:
`build_variables` läuft. Dann: `TMP_SINK_ENV_PIN_BLOCK` enthält weder `PIP_CACHE_DIR` noch
`npm_config_cache`; `TmpPaths.env` bleibt cache-neutral (`TMPDIR`/`TEMP`/`TMP`). Bei
`toolchain-caches: true` **und** `enabled: true` enthalten beide Keys absolute Pfade unter
`<absolute>/cache/…` (`<absolute>/cache/pip`, `<absolute>/cache/npm`) — dieselbe absolute Basis wie
`TMPDIR`. Bei `toolchain-caches: true` und `enabled: false` beendet `sync.py --validate` den Lauf mit
Exit 1 und dem dokumentierten Fehlertext. `docker` wird in keinem Fall umgeleitet.
Test: `tests/test_tmp_sink_output_dirs.py::test_toolchain_cache_opt_in_is_off_by_default`,
`tests/test_tmp_sink_output_dirs.py::test_toolchain_cache_opt_in_pins_cache_dirs`,
`tests/test_repo_containment_validate.py::test_toolchain_cache_requires_enabled_exception`.

**AC-39 — Allowlist-Schema ist strikt: `reason` ist Pflicht, `expires` existiert nicht (Q6).**
Gegeben: `.meta-config/temp-literal-allowlist.yaml`. Wenn: `--validate` läuft. Dann: ein Eintrag mit
`path`, `pattern` und `reason` unterdrückt die WARNING für den passenden Verstoß; ein Eintrag ohne
`reason` unterdrückt sie **nicht** (der Verstoß bleibt WARNING, der ungültige Eintrag wird zusätzlich als
WARNING derselben Check-Familie gemeldet); ein Eintrag mit dem Feld `expires` wird ebenso behandelt —
`expires` ist **kein** Schema-Teil. `owner` bleibt optional und ändert das Ergebnis nicht.
Test: `tests/test_consistency_temp_literals.py::test_allowlist_requires_reason`,
`tests/test_consistency_temp_literals.py::test_allowlist_rejects_expires_field`.

**AC-40 — Der Antigravity-Adapter mappt `args.FilePath` → `tool_input.file_path` (Q10).**
Gegeben: AGY-Payload `{"toolCall": {"name": "write_to_file", "args": {"FilePath": "/ws/a.md"}},
"workspacePaths": ["/ws"]}`. Wenn: der Adapter läuft. Dann: das an den Ziel-Hook gereichte JSON enthält
`tool_name == "Write"` **und** `tool_input.file_path == "/ws/a.md"` — der Hook prüft den Write, statt ihn
am fehlenden `file_path` fail-closed zu blockieren. Der Regressionsfall wird im bestehenden Adapter-Test
ergänzt; ein separater PascalCase-Contract-Test ist **nicht** gefordert.
Test: `tests/test_antigravity_hooks_registration.py::test_adapter_normalizes_edit_tool_names`
(ergänzte Assertion `received["tool_input"]["file_path"] == "/ws/a.md"`).

**AC-41 — §5.5 verweist auf `PYTEST_BASETEMP`/den Config-Key statt auf ein `/tmp`-Literal (Q11).**
Gegeben: `docs/concepts/repo-containment-prison-mode.md`, Abschnitt 5.5. Wenn: der Abschnitt geprüft
wird. Dann: er nennt `PYTEST_BASETEMP` bzw. den Config-Key `system-temp-exception` als Quelle des
Basetemp-Werts und enthält kein `--basetemp=/tmp`-Literal; die Pflichtregel „Der pytest-Basetemp darf
NIE im Arbeitsbaum liegen" bleibt wörtlich enthalten. Die Änderung ist ein Doku-Schritt des Plans, nicht
Teil dieser Spec.
Test: `tests/test_docs_tmp_sink_injection.py::test_prison_mode_section_uses_basetemp_variable`.


---

## Risiken

| # | Risiko | Eintritt | Wirkung | Gegenmaßnahme |
|---|---|---|---|---|
| R1 | Hook-Fail-closed blockiert legitime Arbeit in Verzeichnissen ohne `.meta-config/` | mittel | hoch (Arbeitsstopp) | präzise Meldung mit Reparatur + Opt-out; Doku-Absatz; Rollout mit `sync.py --validate`-Hinweis |
| R2 | Golden-/Guard-Rebase wird vergessen | hoch (wenn nicht im selben Plan-Schritt) | mittel (Suite rot, Guard verliert Vertrauen) | AC-19/AC-02/AC-03 als ein Plan-Schritt; Tests zuerst |
| R3 | Env-Pin (`TMPDIR`) bricht Fremd-Tools | mittel | mittel | nur absolute Werte (ADR-12) und ein existierendes, absolut auflösbares Verzeichnis; Existenzprüfung vor dem Export (AC-36); `TmpSinkError` statt leerem Wert |
| R4 | `system-temp-exception` wird zum Schlupfloch (alles nach System-Temp) | niedrig | hoch | Key-Granularität (`pytest-basetemp`, `toolchain-caches`, Default `false`), `reason`-Pflicht, WARNING bei Inanspruchnahme |
| R5 | Symlink/TOCTOU im Sink bleibt ausnutzbar | mittel | mittel | realpath + `_ensure_inside_sink` (`repo_containment.py:617-638`); Restrisiko dokumentiert |
| R6 | Opencode-Scope-Ableitung ist advisory und wird als Garantie missverstanden | hoch | mittel | WARNING + Doku; `external_directory` ausdrücklich UNVERIFIED |
| R7 | Repo-Wachstum durch neue In-Repo-Artefakte (Backup-Staging, Bash-Logs) | mittel | niedrig | `.gitignore`-Block (`ensure_tmp_sink_gitignore`), `cleanup: manual` unverändert |
| R8 | Token-Ersetzung `{{PYTEST_BASETEMP}}` kollidiert mit fremden Configs | niedrig | mittel | unbekanntes Token ist ein No-op; nur dieses eine Token wird ersetzt, hart validiert |
| R9 | Zwei Wahrheiten bleiben bei dritten Parteien (Fremd-Projekte mit eigenen Templates) | mittel | niedrig | Consistency-WARNING im Zielprojekt; Doku in §5.5 aktualisiert |
| R10 | `TMP_SINK_ABS_PATH` landet versehentlich in einem Template | mittel | mittel | AC-16 + Render-Verbot im Template-Lint (Variable nicht in `agents/**` erlaubt) |
| R11 | Provider löst relative Tool-Pfade anders auf als `cwd` (Annahme A1) | niedrig | mittel (Fehlblockade oder Fehlfreigabe bei relativen Zielen) | AC-06/AC-33 prüfen den realen Zielpfad; `cwd` ist bei allen aktiven Providern das Payload-Feld (`antigravity-json-adapter.sh:111`, Hook `:151-158`); Abweichung würde durch AC-33 sichtbar, nicht still akzeptiert |
| R12 | Neue Fail-closed-Hook-ACs sind selbst basetemp-abhängig (Ancestor-Kollision) | hoch, wenn Fixture aus `tmp_path` gebaut wird | hoch (Test grün/rot je nach Aufruf, Guard verliert Beweiskraft) | Vorbedingung in AC-03/04/05/07: Fixture per `mkdtemp` im System-Temp plus Assertion „kein `.meta-config/` im Ancestor-Pfad"; gilt unabhängig von Option A/C (RVW-07) |
| R13 | `standalone/**` wird nach der Template-Korrektur nicht regeneriert | mittel | mittel (ausgelieferte Personas behalten Literale und Platzhalter-Notizen) | `--render-standalone --check` als Gate (AC-26); der Temp-Literal-Check deckt `standalone/**` ab |
| R14 | Antigravity-Writes tragen `args.FilePath` (PascalCase) statt `tool_input.file_path` | war hoch (jeder Write fail-closed blockiert) | **entschieden und mitigiert (Q10/ADR-15):** `ARG_KEY_MAP` mappt `FilePath` → `file_path`, der Hook prüft den Write statt ihn pauschal zu blocken | der Regressionsfall in `test_adapter_normalizes_edit_tool_names` (AC-40) hält das Mapping fest; Restrisiko: weitere, heute unbekannte PascalCase-Argumente bleiben unmapped und damit fail-closed |


---

## ADRs (Entscheidungsregister)

Format: MADR-minimal (Kontext / Entscheidung / Konsequenzen). Alle Entscheidungen sind Vorschläge dieser
Spec und werden mit ihr freigegeben oder verworfen. Zuordnung der entschiedenen Fragen: Revision 2
entschied Q1, Q2, Q4, Q5, Q7, Q8 und Q9; Revision 3 entschied durch Nutzerentscheidung Q3 (ADR-13),
Q6 (ADR-14), Q10 (ADR-15) und Q11 (ADR-16). Alle sind in
[Offene Fragen](#offene-fragen) als entschieden markiert.


### ADR-01 — Ein Resolver, keine zweite Auflösung

- **Kontext:** Sink-Pfad wird heute an mehreren Stellen interpretiert (`repo_containment.py:304-327`,
  Hook-Inline-Python `:186-301`, `provider-tools.yaml`-Literal, `config.py`-Builder).
- **Entscheidung:** `resolve_tmp_paths` ist der einzige Ort, der Config → Pfade überführt; alle anderen
  konsumieren `TmpPaths`.
- **Konsequenzen:** (+) eine Wahrheit, testbar, provider-agnostisch. (−) Hook bleibt sprachlich getrennt
  (Bash/Python), muss also den Vertrag spiegeln — daher ein Shared-Contract-Test, der `relative`/`absolute`
  zwischen Hook-Ausgabe und `TmpPaths` vergleicht.

### ADR-02 — Relative Form für Templates, absolute Form für Laufzeit

- **Kontext:** Ein absoluter Pfad im generierten Artefakt bricht bei Umzug/Submodul-Mount.
- **Entscheidung:** `{{TMP_SINK_PATH}}` bleibt relativ; `TMP_SINK_ABS_PATH`/`TmpPaths.absolute` nur für
  Env, Backup, Diagnose.
- **Konsequenzen:** (+) move-safe, abwärtskompatibel. (−) Zwei Formen müssen konsistent bleiben (AC-16).

### ADR-03 — System-Temp-Ausnahme nur für pytest-basetemp (Option C)

- **Kontext:** §5.5 begründet die Ausnahme mit zwei Effekten; nur einer ist durch Rekursionsschutz heilbar.
- **Entscheidung:** Default Sink für Agenten-Schreibziele; System-Temp ausschließlich für `--basetemp`,
  über `system-temp-exception` mit `reason`-Pflicht.
- **Konsequenzen:** (+) 13 Fehlschläge bleiben aus, Regel bleibt inhaltlich bestehen. (−) Eine
  konfigurierte Ausnahme mehr, die sichtbar bleiben muss (WARNING, `reason`).

### ADR-04 — Hook fail-closed statt Adelung

- **Kontext:** `repo-containment-impl.sh:175-180` macht `$PWD` zum Root; das öffnet das Jail.
- **Entscheidung:** Fehlender Root ist ein Block (Exit 2, `repo-containment.no-root`); `enabled: false`
  gilt nur bei auflösbarem Root. Anker ist `cwd` oder — bei fehlendem/leerem `cwd` — das Zielverzeichnis
  (ADR-08).
- **Konsequenzen:** (+) konsistent mit allen anderen Hook-Fehlerpfaden. (−) Bestandsprojekte, die aus
  `/tmp` heraus arbeiten, werden blockiert (R1) — bewusst, mit Reparatur-Kanal.

### ADR-05 — Provider-Agnostik über Capability + Daten, nicht über Namen

- **Kontext:** Opencode hat keine Hooks; der einzige Hebel ist der Permission-Layer.
- **Entscheidung:** Scope-Liste wird aus `TmpPaths.relative` abgeleitet und über
  `provider_transform.py:985-998` angewandt; kein Provider-Name im Code.
- **Konsequenzen:** (+) gleiche Logik für alle Provider, neue Provider erben sie. (−) Auf hook-losen
  Providern bleibt die Durchsetzung advisory (nur Permission-Layer, keine Pfadprüfung).

### ADR-06 — Literal-Verbot als WARNING, nicht als Hard-Exit

- **Kontext:** Ein Hard-Exit auf `/tmp` in Templates würde jedes Bestandsprojekt beim ersten Sync
  blockieren, das noch alte Artefakte hat.
- **Entscheidung:** Der neue Check meldet WARNING mit Allowlist; Hard-Exit bleibt der Config-Validierung
  vorbehalten.
- **Konsequenzen:** (+) kein Bruch, schrittweise Migration. (−) Das Verbot ist nicht erzwungen — bewusste
  Convention-boundary-Entscheidung.

### ADR-07 — Resolver wirft nicht, Verbraucher werfen (RVW-01)

- **Kontext:** Revision 1 ließ `resolve_tmp_paths` bei `tmp-sink.enabled: false` werfen, während die
  Fehlermatrix „Sync ok" und einen gesetzten `TMP_SINK_PATH` zusagte. Beides ist unvereinbar; `enabled`
  wäre toter Zustand.
- **Entscheidung:** `resolve_tmp_paths` ist ein **nicht-werfender** Resolver (disabled ⇒
  `enabled=False, absolute=None, env={}`). Werfend sind die Schreib-/Verbrauchs-APIs
  `resolve_output_dir` / `resolve_work_dir` / `resolve_out_path` / `tmp_env` /
  `tmp_sink_env_pin_block`; **zusätzlich** wirft `resolve_tmp_paths` für Config-Fehler
  (`tmp-sink.invalid-path`, `tmp-sink.system-temp-exception`) — „ausschließlich" gilt also nur für den
  deaktivierten Sink, nicht für ungültige Konfiguration (RVW2-02).
- **Konsequenzen:** (+) deckungsgleich mit der bestehenden Konvention in `repo_containment.py`
  (`resolve_effective_repo_containment` ist nicht-exitierend, `_active_sink_dir` wirft erst beim
  Schreiben); (+) Fehlermatrix, Datenfluss und AC-23..AC-25 sind widerspruchsfrei; (+) `enabled` hat eine
  Bedeutung. (−) Zwei Fehler-Zeitpunkte (Config-Validierung vs. Schreibzugriff) müssen dokumentiert
  bleiben — genau das leisten Fehlermatrix und AC-24.

### ADR-08 — Kein Provider-Selbstausschluss: Anker aus dem Zielpfad (RVW-04)

- **Kontext:** Der Antigravity-Adapter kann `cwd=""` liefern; „`cwd` fehlt ⇒ Exit 2" würde für diesen
  Provider jeden Write blockieren (`antigravity-json-adapter.sh:122-127`).
- **Entscheidung:** Anker ist `cwd`, wenn vorhanden und nicht leer; sonst das Verzeichnis des absoluten
  Zielpfads. Ein relatives Ziel ohne `cwd` ist nicht auflösbar und blockt mit
  `repo-containment.no-root`. Variante (i) „absolutes Ziel ohne Root direkt prüfen" ist verworfen, weil
  der Guard ohne Root keinen erlaubten Bereich hat und damit pauschal blocken würde.
- **Konsequenzen:** (+) Antigravity bleibt für In-Workspace-Writes funktionsfähig; (+) `/tmp`-Writes
  bleiben blockiert, weil dort kein `.meta-config/`-Ancestor existiert; (+) derselbe Fehlercode statt
  zweier Codes. (−) Der Anker stammt aus dem Payload — wer einen `.meta-config/`-Ancestor neben dem Ziel
  platzieren kann, kann den Root bestimmen; das ist dieselbe Vertrauensannahme wie beim `cwd` und in
  [Threat-Model](#threat-model-4-fragen) als Convention boundary eingeordnet.

### ADR-09 — Standalone nennt den Framework-Default-Sink (RVW-02)

- **Kontext:** `standalone/**` wird ohne Projekt-Config gerendert; `_standalone_variables` setzt
  `TMP_SINK_PATH` nicht, wodurch 12 Platzhalter-Notizen entstehen (`standalone.py:313-319`).
- **Entscheidung:** `_standalone_variables` setzt `TMP_SINK_PATH = ".tmp"` (Framework-Default). Die
  Literale verschwinden über die Template-Korrektur plus Regeneration, nicht über einen
  Standalone-Sonderweg.
- **Konsequenzen:** (+) ehrlicher, konkreter Wert statt Platzhalter-Rauschen; (+) konsistent mit dem
  Default, den ein Zielprojekt ohne eigene Konfiguration bekommt; (+) ein Drift-Gate existiert bereits.
  (−) Der Wert ist im Standalone-Artefakt nicht projektspezifisch — das bleibt durch den Scope-Hinweis im
  Kopf offengelegt.

### ADR-10 — `reviewers.yaml` ist Test-Fixture, kein Injektionspunkt (RVW-03)

- **Kontext:** Revision 1 behauptete einen Renderer über `rules.py:269`. Es gibt keinen: die Datei liest
  nur `tests/test_review_fleet.py:13`; `rules.py:269` speist Regel-Templates.
- **Entscheidung:** Die Datei wird aus dem Injektions-Scope genommen; kein `{{TMP_SINK_PATH}}` dort. Der
  `notes:`-Satz bleibt generisch oder entfällt (Textänderung des Plans).
- **Konsequenzen:** (+) keine unbelegte Behauptung, kein Literal, das als Platzhalter getarnt stehen
  bleibt; (+) AC-02 prüft nur noch die vier Templates. (−) Wird später ein produktiver Konsument
  eingeführt, ist die Injektion erneut zu bewerten — dann mit Beleg (Datei:Zeile) als Voraussetzung.

### ADR-11 — Adapter-`mktemp` bleibt System-Temp (RVW-08)

- **Kontext:** `antigravity-json-adapter.sh:167` legt pro Lauf eine stderr-Datei im System-Temp an.
- **Entscheidung:** dokumentierte Ausnahme. Die Datei bleibt, wo sie ist; sie wird per `trap` entfernt.
- **Konsequenzen:** (+) der Adapter kann eine Block-Meldung auch dann ausgeben, wenn der Sink deaktiviert
  oder defekt ist (kein Selbstausschluss des Guards); (+) keine Repo-Verschmutzung. (−) Ein ephemerer
  System-Temp-Schreibzugriff bleibt außerhalb des Sinks — bewusst und begründet, nicht still.

### ADR-12 — Env-Pin ist absolut; benannte Ausnahme zu ADR-02 (RVW2-01)

- **Kontext:** Revision 2 forderte in Injektionspunkt 3 einen **relativen** `TMPDIR`
  (`export TMPDIR=<relativer Sink>`), während die Formtabelle und AC-12 **absolute** Werte verlangen.
  `TMPDIR`/`TEMP`/`TMP` sind prozess-global: Kindprozesse erben den Wert und interpretieren einen relativen
  Wert gegen **ihr eigenes** `cwd`. Ein relativer Pin lenkt Temp-Writes je nach gestartetem Prozess an
  verschiedene Orte — der Fehler tritt still auf.
- **Entscheidung:** Der Env-Pin-Block setzt **absolute** Werte (`str(paths.absolute)`, identisch zu
  `TmpPaths.env`); relative Env-Werte sind ausgeschlossen. Das ist die **einzige** Ausnahme von der
  Move-Safe-Regel aus ADR-02: der gerenderte Block trägt einen Maschinenpfad (IC-13 nennt diese Ausnahme
  ausdrücklich). Template-Beispiele bleiben relativ (`{{TMP_SINK_PATH}}`), weil sie als Shell-Kommando ab
  Repo-Root gelten und ihr Pfad nicht an Kindprozesse weitergegeben wird — der Unterschied ist in
  [Relative vs. absolute Form](#relative-vs-absolute-form) ausgeführt.
- **Konsequenzen:** (+) Env-Semantik ist korrekt und deckungsgleich mit `TmpPaths.env`, AC-12 und AC-35;
  (+) ein Wert für alle drei Keys. (−) Nach einem Repo-Umzug ist der Block veraltet, bis
  `python scripts/sync.py` erneut läuft; deshalb prüft der Block die Existenz **vor** dem Export und meldet
  den Reparaturweg, statt still auf einen toten Pfad zu zeigen (AC-36). (−) Der Standalone-Export setzt die
  Variable leer, weil er keine Projekt-Config hat (IC-15).

### ADR-13 — Toolchain-Caches nur per Opt-in, Default aus (Q3)

- **Kontext:** `system-temp-exception` war bisher nur für `pytest --basetemp` gedacht; pip/npm schreiben
  weiter in den Nutzer-Cache (`~/.cache/pip`, `~/.npm/_cacache`). Ein In-Repo-Cache wäre bequemer für
  Offline-Läufe, wächst aber im Arbeitsbaum und wird von Backups/CI erfasst.
- **Entscheidung:** Der Config-Key
  `repo_containment.tmp-sink.system-temp-exception.toolchain-caches` (plural, kebab-case; Default `false`)
  erlaubt ein Opt-in. Nur bei `true` **und** `enabled: true` pinnt der Builder
  `PIP_CACHE_DIR=<abs>/cache/pip` und `npm_config_cache=<abs>/cache/npm` in `TMP_SINK_ENV_PIN_BLOCK`
  (dieselbe absolute Basis wie `TMPDIR`/`TEMP`/`TMP`, ADR-12). `tmp_env` bleibt cache-neutral.
  `toolchain-caches: true` bei `enabled: false` ⇒ `_fail` Exit 1. `docker` wird nie umgeleitet. Das
  Python-Feld heißt weiterhin `SystemTempException.toolchain_cache`.
- **Konsequenzen:** (+) keine gebrochenen Toolchains durch einen Default-Wechsel; die Entscheidung ist
  sichtbar (explizites Opt-in plus WARNING `temp-literal.toolchain-cache-in-repo`). (−) Wer den Cache im
  Repo will, muss ihn auch entsorgen: er wächst in Backup/CI/Submodul, `cleanup: on-sync` löscht ihn, und
  nach einem Repo-Umzug zeigt der Pin bis zum Re-Sync auf einen toten Pfad. (−) `toolchain-caches` bei
  `enabled: false` ist ein zusätzlicher Config-Fehlerfall in der Fehlermatrix.

### ADR-14 — Allowlist-Schema mit `reason`-Pflicht, ohne `expires` (Q6)

- **Kontext:** Revision 2 ließ die Allowlist-Frage offen und führte `owner` bereits als optionales Feld;
  ein `expires`-Feld stand im Raum, ohne dass ein Ablaufmechanismus existiert.
- **Entscheidung:** `.meta-config/temp-literal-allowlist.yaml` verlangt `path`, `pattern` und `reason`;
  `owner` ist optional; `expires` ist **kein** Schema-Teil. Ein Eintrag ohne `reason` oder mit einem nicht
  unterstützten Feld (z. B. `expires`) unterdrückt die Meldung nicht — der Verstoß bleibt WARNING, und der
  ungültige Eintrag wird als WARNING derselben Check-Familie gemeldet.
- **Konsequenzen:** (+) jede Ausnahme trägt ihre Begründung im Artefakt; (+) keine Pseudo-Ablaufsemantik,
  die niemand durchsetzt. (−) Projekte mit `expires` in einer Altliste bekommen zwei WARNINGs statt einer
  Unterdrückung — bewusst laut, nicht still.

### ADR-15 — Der Antigravity-Adapter mappt `FilePath` → `file_path` (Q10)

- **Kontext:** `ARG_KEY_MAP` (`antigravity-json-adapter.sh:111`) enthält nur `CommandLine` und `Cwd`.
  `args.FilePath` fällt unverändert als `tool_input.FilePath` durch; der Hook liest ausschließlich
  `tool_input.file_path` (`repo-containment-impl.sh:391-397`) und blockt deshalb jeden Antigravity-Write
  fail-closed, ohne den Pfad je zu prüfen.
- **Entscheidung:** Der Adapter-Vertrag wird um `'FilePath': 'file_path'` erweitert. Der `mktemp`-Pfad des
  Adapters bleibt unverändert (ADR-11). Der Regressionsfall wird im bestehenden Test
  `tests/test_antigravity_hooks_registration.py::test_adapter_normalizes_edit_tool_names` ergänzt
  (`received["tool_input"]["file_path"] == "/ws/a.md"`); ein separater PascalCase-Contract-Test ist nicht
  gefordert.
- **Konsequenzen:** (+) Antigravity-Writes werden geprüft statt pauschal blockiert; (+) das Mapping bleibt
  eine Tabellenzeile, keine Provider-Verzweigung. (−) Ein weiteres AGY-Argument mit anderem Namen bleibt
  unmapped und damit fail-closed — dokumentiert als Restrisiko in R14.

### ADR-16 — §5.5 verweist auf den Config-Key statt auf ein `/tmp`-Literal (Q11)

- **Kontext:** §5.5 (`docs/concepts/repo-containment-prison-mode.md:404-439`) verlangt inhaltlich korrekt,
  dass der Basetemp nie im Arbeitsbaum liegt, nennt aber `--basetemp=/tmp/<user>` als Beispiel
  (`:410-411`) und im kanonischen Aufruf (`:428-429`). Der Regeltext trägt damit selbst die Form, die er
  verbietet.
- **Entscheidung:** Der Regeltext verweist künftig auf `PYTEST_BASETEMP` bzw. den Config-Key
  `system-temp-exception`; ein `/tmp`-Literal bleibt in der Vorschrift nicht stehen. Die Pflichtregel
  („Der pytest-Basetemp darf NIE im Arbeitsbaum liegen") bleibt wörtlich erhalten. Das ist eine reine
  Doku-Änderung; der Task gehört in den Plan, nicht in diese Spec (Inventar 14).
- **Konsequenzen:** (+) die Regel ist literal-frei und damit konsistent mit AC-01/AC-13; (+) keine
  inhaltliche Umkehr (Nicht-Ziele). (−) `docs/concepts/**` hat keinen Renderer, die Änderung ist deshalb
  redaktionell und wird nur durch AC-41 (Doku-Test) abgesichert.


---

## IC-IDs

- **IC-01** — `resolve_tmp_paths` liefert `TmpPaths` (`relative`, `absolute`, `enabled`,
  `system_temp_exception`, `pytest_basetemp`, `env`), **wirft nicht bei deaktiviertem Sink**
  (`enabled=False` ⇒ `absolute=None`, `env={}`) und wirft `TmpSinkError` nur für Config-Fehler
  (`tmp-sink.invalid-path`, `tmp-sink.system-temp-exception`); nie `sys.exit`.
- **IC-02** — `absolute` ist realpath-aufgelöst, liegt im Projekt-Root und ist identisch mit der
  `_resolve_sink_dir`-Auflösung; bei `enabled=False` ist es `None`.
- **IC-03** — `relative` erfüllt `tmp_sink_path_error` + `tmp_sink_location_error` (relativ, kein `..`,
  kein System-Temp, kein Symlink-Escape) — auch bei `enabled=False`, damit kein schlafender Config-Fehler
  entsteht.
- **IC-04** — `pytest_basetemp` ist absolut und literal-frei: entweder `<absolute>/pytest` oder
  `<tempfile.gettempdir()>/<user>/pytest-agent-meta`; in `TEST_COMMANDS` shell-gequotet, kein `"` im Wert.
- **IC-05** — Builder-Vertrag: `TMP_SINK_PATH` (relativ, immer gesetzt), `TMP_SINK_ABS_PATH` (absolut),
  `PYTEST_BASETEMP`, `TMP_SINK_ENV_PIN_BLOCK` (absolut, aus `tmp_sink_env_pin_block`); der Block enthält
  `PIP_CACHE_DIR` und `npm_config_cache` **nur** bei `toolchain-caches: true` (Q3) — `tmp_env` bleibt
  cache-neutral; Token `{{PYTEST_BASETEMP}}` wird in `TEST_COMMANDS` und `CODE_QUALITY_RULES` ersetzt,
  unersetzt ⇒ Exit 1; bei `enabled=False` entfallen `TMP_SINK_ABS_PATH` und `TMP_SINK_ENV_PIN_BLOCK`.
- **IC-06** — `tmp_env(paths)` setzt `TMPDIR`/`TEMP`/`TMP` auf `paths.absolute`; bei `enabled=False`
  `TmpSinkError` mit `tmp-sink.disabled`.
- **IC-07** — Hook-Verdict: Anker = `cwd` (nicht leer) oder Zielverzeichnis bei absolutem Ziel; relative
  Ziele ohne `cwd` ⇒ Exit 2; Ancestor-Suche ohne Adelung; relative Ziele gegen `cwd` (Prüf-Ort =
  Schreib-Ort); Exit 2 mit `repo-containment.no-root`.
- **IC-08** — Hook-Meldungen nennen absolute Pfade (Root, Sink, Anker) und eine Reparaturzeile.
- **IC-09** — Backup-Staging: `dir=<absolute>/backup-staging` bei aktivem Sink; bei deaktiviertem Sink
  System-Temp + WARNING `backup.staging-system-temp`.
- **IC-10** — Opencode-Edit-Scope wird aus `TmpPaths.relative` abgeleitet (`<relative>/**` +
  `.meta-viz/**`); leere Ableitung ⇒ `edit: deny`.
- **IC-11** — Consistency-Check `check_temp_literals` meldet WARNINGs mit Allowlist
  `.meta-config/temp-literal-allowlist.yaml`; Scope inklusive `standalone/**`; registriert im
  `_strict_findings`-Block (`cli_commands.py:1411-1426`). Allowlist-Schema (Q6): Pflichtfelder `path`,
  `pattern`, `reason`, optional `owner`; `expires` ist kein Schema-Teil. Ein Eintrag ohne `reason` oder mit
  einem nicht unterstützten Feld unterdrückt den Verstoß nicht, sondern erzeugt zusätzlich eine WARNING
  derselben Check-Familie.
- **IC-12** — Config-Schema/Validator: `system-temp-exception.{enabled,reason,pytest-basetemp,
  toolchain-caches}` (YAML-Key plural/kebab-case, Python-Feld `toolchain_cache`; `toolchain-caches`
  Default `false`, `true` bei `enabled: false` ⇒ `_fail` Exit 1) mit den Fehlerfällen aus
  [Konfigurierbarkeit](#konfigurierbarkeit--fehlerverhalten).
- **IC-13** — `TMP_SINK_ABS_PATH` darf in `agents/**` und `standalone/**` nicht gerendert werden
  (Template-Lint). Davon getrennt und ausdrücklich erlaubt ist der `TMP_SINK_ENV_PIN_BLOCK` mit absoluten
  Env-Werten (ADR-12).
- **IC-14** — Bestehende Codes (`tmp-sink.*`, `out-outside-tmp-sink`, `repo-containment.no-hook-support`)
  bleiben unverändert; `repo-containment.no-cwd` und `tmp-sink.abs-path-unresolved` entfallen.
- **IC-15** — `standalone/agents/**` rendert `TMP_SINK_PATH` als Framework-Default `.tmp` und
  `TMP_SINK_ENV_PIN_BLOCK` als leeren String (kein Maschinenpfad, keine Platzhalter-Notiz); die Notiz
  `[TMP_SINK_PATH — not available outside a full agent-meta install]` kommt dort nicht mehr vor;
  `--render-standalone --check` ist das Drift-Gate.
- **IC-16** — Managed-`.gitignore`-Eintrag und Doctor-Finding werden aus `TmpPaths` gespeist; kein
  weiterer `resolve_effective_repo_containment`-Aufruf und kein dritter Parser in
  `gitignore.py::_tmp_sink_gitignore_entry` / `doctor_detectors.py::_sink_hits`.
- **IC-17** — Der Antigravity-Adapter mappt `args.FilePath` → `tool_input.file_path` (`ARG_KEY_MAP`
  erweitert um `'FilePath': 'file_path'`, Q10/ADR-15); sein `mktemp`-stderr-Pfad bleibt unverändert die
  dokumentierte Ausnahme (ADR-11) und wird per `trap` entfernt.
- **IC-18** — Subprozess-Env-Pin gilt für `scripts/**` (inkl. `scripts/*.py`); Ausnahmen stehen mit
  Begründung in `.meta-config/temp-env-allowlist.yaml`.
- **IC-19** — `TMP_SINK_ENV_PIN_BLOCK` (erzeugt von `tmp_sink_env_pin_block(paths)`) setzt `TMPDIR`,
  `TEMP` und `TMP` ausschließlich auf absolute Werte (`str(paths.absolute)`, identisch zu `TmpPaths.env`),
  prüft die Existenz vor dem Export und ist die einzige Ausnahme zu ADR-02/IC-13 (ADR-12); zusätzlich
  setzt derselbe Block `PIP_CACHE_DIR=<abs>/cache/pip` und `npm_config_cache=<abs>/cache/npm`, **wenn**
  `toolchain_cache` aktiv ist (Q3/ADR-13) — ohne Opt-in enthält der Block keinen Cache-Key; bei
  `enabled=False` wirft die Funktion `tmp-sink.disabled` und der Builder setzt die Variable nicht.
- **IC-20** — `resolve_out_path(project_root, config, out, *, tool="") -> Path` validiert ein explizites
  `--out` per `realpath` gegen den Sink; Fehler `tmp-sink.disabled` und `<tool>.out-outside-tmp-sink`;
  Verhalten unverändert.
- **IC-21** — §5.5 (`docs/concepts/repo-containment-prison-mode.md:404-439`) verweist auf
  `PYTEST_BASETEMP` bzw. den Config-Key `system-temp-exception` und enthält kein `--basetemp=/tmp`-Literal
  in der Vorschrift; die Pflichtregel „Der pytest-Basetemp darf NIE im Arbeitsbaum liegen" bleibt wörtlich
  erhalten (Q11/ADR-16, AC-41). Umsetzung als Doku-Task im Plan, nicht in dieser Spec.


---

## Traceability

| AC | IC | Injektionspunkt (# aus dem Inventar) |
|---|---|---|
| AC-01 | IC-11, IC-13 | 1, 7 |
| AC-02 | IC-05, IC-11 | 1 |
| AC-03 | IC-07, IC-08 | 5 |
| AC-04 | IC-07 | 5 |
| AC-05 | IC-07, IC-08 | 5 |
| AC-06 | IC-07 | 5 |
| AC-07 | IC-07 | 5 |
| AC-08 | IC-07, IC-14 | 5 |
| AC-09 | IC-01, IC-09 | 4 |
| AC-10 | IC-09, IC-14 | 4 |
| AC-11 | IC-06, IC-18 | 3 |
| AC-12 | IC-02, IC-06 | 3 |
| AC-13 | IC-04, IC-05 | 2 |
| AC-14 | IC-05, IC-12 | 2 |
| AC-15 | IC-12 | — |
| AC-16 | IC-01, IC-05, IC-13 | 1, 3 |
| AC-17 | IC-10 | 6 |
| AC-18 | IC-08 | 5 |
| AC-19 | IC-11 | 7 |
| AC-20 | IC-14 | 6 |
| AC-21 | IC-11 | 7 |
| AC-22 | IC-05, IC-11 | 1 |
| AC-23 | IC-01, IC-03 | 1 |
| AC-24 | IC-06, IC-14, IC-20 | 3, 4 |
| AC-25 | IC-03, IC-05, IC-14 | 1, 8 |
| AC-26 | IC-11, IC-13, IC-15 | 7, 11 |
| AC-27 | IC-15 | 11 |
| AC-28 | IC-07 | 5 |
| AC-29 | IC-07, IC-08 | 5 |
| AC-30 | IC-17 | 12 |
| AC-31 | IC-16 | 9 |
| AC-32 | IC-16 | 10 |
| AC-33 | IC-07 | 5 |
| AC-34 | IC-04 | 2 |
| AC-35 | IC-05, IC-19 | 3 |
| AC-36 | IC-19 | 3 |
| AC-37 | IC-07, IC-08 | 5 |
| AC-38 | IC-05, IC-12, IC-19 | 3 |
| AC-39 | IC-11 | 7 |
| AC-40 | IC-17 | 5 |
| AC-41 | IC-21 | 14 |


---

## Offene Fragen

**Legende:** „Entschieden (Rev. 2)" = in Revision 2 festgelegt; „Entschieden (Rev. 3)" = in Revision 3
durch Nutzerentscheidung festgelegt. Es bleibt **keine offene Frage**: alle elf Fragen sind entschieden.
Die ACs hängen bewusst an den Entscheidungen — Q3 → AC-38, Q6 → AC-39, Q10 → AC-40, Q11 → AC-41.

- **Q1** — Soll die System-Temp-Ausnahme (`system-temp-exception.enabled`, `pytest-basetemp: true`) im
  Framework-Default **an** oder **aus** sein? — **Entschieden (Rev. 2): an.** Begründung: „aus" würde den
  Default-Basetemp unter `<sink>/pytest` legen und damit §5.5 inhaltlich umkehren; das ist als Nicht-Ziel
  ausgeschlossen (ADR-03, AC-13).
- **Q2** — Soll `TMP_SINK_ABS_PATH` als eigene Builder-Variable eingeführt werden? — **Entschieden
  (Rev. 2): ja.** Absolute Konsumenten (Backup, Meldungen, Diagnose) bekommen damit eine stabile Quelle;
  in Templates bleibt sie verboten (IC-13, AC-16).
- **Q3** — Dürfen Toolchain-Caches (pip/npm) per Opt-in in den Sink gepinnt werden, oder bleibt das
  dauerhaft ausgeschlossen? — **Entschieden (Rev. 3): Opt-in erlaubt, Default aus.** Config-Key
  `repo_containment.tmp-sink.system-temp-exception.toolchain-caches` (Default `false`); nur bei `true`
  **und** `enabled: true` pinnt der Builder `PIP_CACHE_DIR=<abs>/cache/pip` und
  `npm_config_cache=<abs>/cache/npm` in den Env-Pin-Block, `tmp_env` bleibt cache-neutral, `docker` wird
  nie umgeleitet (AC-38, IC-05/IC-12/IC-19, ADR-13,
  [Toolchain-Ausnahme](#toolchain-ausnahme)). Begründung: Default aus bricht keine Toolchain; der
  In-Repo-Cache wächst in Backup/CI/Submodul, `cleanup: on-sync` würde ihn löschen, und nach einem
  Repo-Umzug zeigt der Pin bis zum Re-Sync auf einen toten Pfad — deshalb ausdrückliches, sichtbares
  Opt-in statt Default.
- **Q4** — Soll `repo_containment.enabled: false` weiterhin Vorrang haben, wenn **kein** Projekt-Root
  auflösbar ist? — **Entschieden (Rev. 2): nein, Root-Auflösung geht vor.** Ohne Root ist die Config nicht
  lesbar; ein Opt-out eines fremden Projekts darf keinen Write außerhalb freischalten (AC-08 bleibt
  projektlokal, AC-03/AC-29 decken den Fall ohne Root).
- **Q5** — Ist „`cwd` fehlt ⇒ Exit 2" für alle Provider-Payload-Verträge akzeptabel? — **Entschieden
  (Rev. 2): nein.** Ersetzt durch die Anker-Regel (ADR-08): `cwd` fehlt/leer + absolutes Ziel ⇒ Anker aus
  dem Ziel; relatives Ziel ohne `cwd` ⇒ Exit 2 `repo-containment.no-root` (AC-28/AC-29).
- **Q6** — Wo soll die Allowlist für Temp-Literale liegen und wie streng soll sie sein (nur
  Pfad+Pattern, oder zusätzlich `owner`/`expires`)? — **Entschieden (Rev. 3):**
  `.meta-config/temp-literal-allowlist.yaml` mit den Pflichtfeldern `path`, `pattern`, `reason` und dem
  optionalen `owner`; `expires` ist **kein** Schema-Teil. Ein Eintrag ohne `reason` oder mit einem nicht
  unterstützten Feld (z. B. `expires`) unterdrückt die Meldung nicht — der Verstoß bleibt WARNING, und der
  ungültige Eintrag wird als WARNING derselben Check-Familie gemeldet (AC-21, AC-39, IC-11, ADR-14).
  Begründung: `expires` bräuchte einen Ablauf-Job, den es nicht gibt; eine Pseudo-Ablaufsemantik wäre eine
  stille Ausnahme, `owner` dagegen nur ein Nachverfolgungs-Hinweis.
- **Q7** — Soll ein Backup bei deaktiviertem Sink auf System-Temp ausweichen oder hart abbrechen? —
  **Entschieden (Rev. 2): ausweichen, mit WARNING.** Ein Backup darf nie an der Sink-Konfiguration
  scheitern (AC-10).
- **Q8** — Sollen die 13 Ancestor-Kollisionen technisch geheilt werden (Fixture-Sentinel) oder bleibt das
  eine Betriebsregel? — **Entschieden (Rev. 2): Sentinel-Pflicht für die neuen Hook-ACs, unabhängig von
  Option A/C.** Option C bleibt die Empfehlung für den Basetemp; die Test-Isolation ist davon entkoppelt
  (AC-03/AC-04/AC-05/AC-07, R12).
- **Q9** — Soll `rules/1-generic/plan-ledger.md:67` den konfigurierten Sink nennen? — **Entschieden
  (Rev. 2): ja**, über den Platzhalter bzw. „im konfigurierten Scratch-Sink" (Inventar 13, AC-21).
- **Q10** — Antigravity-Writes tragen laut Adapter-Testfixture `args.FilePath` (PascalCase,
  `tests/test_antigravity_hooks_registration.py:331`); der Adapter mappt nur `CommandLine`/`Cwd`
  (`antigravity-json-adapter.sh:111`), die `file_path`-Suche des Hooks (`:391-397`) findet dann nichts.
  Wird `FilePath` → `file_path` künftig gemappt (Adapter-Vertrag), oder bleibt der Write-Pfad für
  Antigravity fail-closed blockiert? — **Entschieden (Rev. 3): Der Adapter mappt `args.FilePath` →
  `tool_input.file_path`.** `ARG_KEY_MAP` wird um `'FilePath': 'file_path'` erweitert, damit Writes
  geprüft statt pauschal blockiert werden. Der Regressionsfall wird im bestehenden Test
  `tests/test_antigravity_hooks_registration.py::test_adapter_normalizes_edit_tool_names` ergänzt
  (`received["tool_input"]["file_path"] == "/ws/a.md"`); ein separater PascalCase-Contract-Test ist
  **kein** Pflichtumfang (AC-40, IC-17, ADR-15, R14 entschieden/mitigiert).
- **Q11** — Soll §5.5 (`docs/concepts/repo-containment-prison-mode.md:404-439`) selbst auf
  `PYTEST_BASETEMP`/den Config-Key verweisen, oder bleibt der Regeltext als Beispiel-Formulierung
  unverändert? — **Entschieden (Rev. 3): §5.5 verweist auf `PYTEST_BASETEMP` bzw. den Config-Key
  `system-temp-exception`, kein `/tmp`-Literal mehr in der Vorschrift.** Die inhaltliche Pflichtregel
  („Der pytest-Basetemp darf NIE im Arbeitsbaum liegen") bleibt **wörtlich** erhalten; das ist ein
  Doku-Soll, dessen Task im Plan liegt (AC-41, IC-21, ADR-16, Inventar 14).


---

## Formale Einordnung

Dieses Artefakt ist eine **Spec**, kein Plan. Der Validator klassifiziert Artefakte namensbasiert
(`scripts/lib/consistency/spec_plan.py::_classify`, `:318-323`): `-design.md` ⇒ Spec-Rolle,
`-spike.md` ⇒ Spike, alles andere — auch `*-spec.md` — ⇒ Plan-Rolle. Für diese Datei prüft er deshalb
zusätzlich die Plan-Template-Felder.

Damit die namensbasierte Klassifikation keine Fehlbefunde erzeugt, trägt dieses Dokument die
Plan-Pflichtangaben in ausdrücklich markierter, selbstreferenzieller Form. Die folgende Zeile ist eine
**Selbstreferenz** (dieses Dokument ist selbst die Spec) und kein Plan-Bezug:

**Spec:** docs/specs/2026-10-24-tmp-sink-injection-spec.md

Die übrigen Plan-Template-Felder sind **nicht** Inhalt des Dokuments, weil der Plan separat entsteht;
hier nur zur Abgrenzung als nicht zutreffend genannt: `**Goal:**`, `**Architecture:**`,
`**Tech Stack:**`, `pipeline_stages`, `## Global Constraints` und `## File Structure`.

Der Inhalt bleibt eine Spec: alle Pflichtabschnitte aus `REQUIRED_SPEC_SECTIONS`
(`scripts/lib/consistency/spec_plan.py:31-35`) sind vorhanden.

Der Formkompromiss (Feldnamen als Backtick-Zitate, Substring-Prüfung `spec_plan.py:353-354`) ist
**bewusst akzeptiert** (RVW-21); der Plan hält diese Einordnung fest, statt die Datei in `-design.md`
umzubenennen — dann würden die inhaltlich passenden `REQUIRED_SPEC_SECTIONS` greifen, aber alle
bestehenden Verweise auf diesen Pfad brechen.


---

## Trace-Anker

spec-id: SPEC-tmp-sink-injection
