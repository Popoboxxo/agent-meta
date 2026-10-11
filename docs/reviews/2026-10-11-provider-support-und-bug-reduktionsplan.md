# Provider-Support-Analyse und Bug-Reduktionsplan — 2026-10-11

> **Zweck:** Beantwortet (1) werden alle 9 Provider sauber unterstützt und (2) wie sinkt die Zahl der Bugs drastisch.
> **Baseline:** Branch `claude/adoring-keller-c12ws0` (= `main` @ `1cc7d1f`).
> **Methode:** Echte `sync.py --init`-Läufe in 9 Scratch-Projekten (je ein Provider), automatische Prüfung der erzeugten Artefakte (TOML-/YAML-Parsing, Platzhalter, `.claude/`-Reste, `.gitignore`), `sync.py --validate`, Auswertung von `config/`, `scripts/lib/`, CI-Workflows und der vorhandenen Reviews (`2026-10-07-system-review.md`, Provider-Audits vom 2026-09-30).
> **Grenzen:** Die Testsuite (`pytest tests`, ~3100 Tests) wurde gestartet, war beim Schreiben noch nicht durch (rund 20 %, bis dahin keine Fehler). Es wurde nur die Generierung geprüft, kein Lauf der Provider-Tools selbst (kein Codex/Gemini/… installiert).

---

## 1. Kurzfazit

1. **Generierung ist für alle 9 Provider technisch sauber.** Alle Läufe enden mit rc 0, 0 kaputte TOML-Dateien (Codex: 62/62 parsen; frühere Blocker D1 behoben), 0 kaputte Frontmatter, 0 `.claude/`-Reste in Nicht-Claude-Agenten.
2. **Gleichwertig sind die Provider aber nicht** — und das ist überwiegend Plattform-bedingt, nicht Bug: Nur Claude und Gemini haben einen Hook-basierten Runtime-Gate (`runtime_gate: hook`), Opencode `permission` (teilweise), die anderen 6 nur `advisory` (Prompt-Konvention). Das ist deklariert, aber der Nutzer erfährt es nur über Warnungen im Konsistenz-Check.
3. **Es gibt weiterhin echte Provider-Lücken**, am deutlichsten: Nicht-Claude-Projekte bekommen unvollständige `.gitignore`-Einträge (verifiziert, siehe 2.2). Die Review-Befunde SR-A-11/12/31/33 stehen im Review-Dokument weiter auf „offen" und lassen sich reproduzieren.
4. **Die Bug-Quelle ist strukturell, nicht zufällig.** Das Muster aus dem System-Review (139 Befunde) ist immer dasselbe: *Claude-Pfad vollständig, die anderen sind Teilkopien*, *Handkopien derselben Logik* (Validate-Loop, Backup-Prune, Deaktivierungsfilter 4×), *Fail-open-Guards*. Diese Klassen kann man mit wenigen Maßnahmen systematisch abbauen (Abschnitt 4), statt weiter Einzelbefunde zu jagen.

---

## 2. Provider-Status (verifiziert)

### 2.1 Matrix

| Provider | Sync rc | Agent-Artefakte | Format valide | Runtime-Gate | Hooks | Commands | Fan-out/Barrier | Bewertung |
|---|---|---|---|---|---|---|---|---|
| Claude | 0 | 84 `.md` | ja | hook | ja | ja | native-batch ✓ | **voll** |
| Gemini | 0 | 62 `.md` + 22 `.toml` | ja | hook | ja (Antigravity-Adapter) | ja (`.toml`) | native-batch ✓ | **voll** |
| Opencode | 0 | 84 `.md` | ja | permission (teilweise) | nein | ja | native-batch ✓ | gut, Gate ohne Delegations-Provenienz |
| Continue | 0 | 84 `.md` | ja | advisory | nein | ja | sequentiell | Basis |
| Copilot | 0 | 84 `.md` | ja | advisory | nein | ja | sequentiell | Basis |
| Mammouth | 0 | 84 `.md` | ja | advisory | `has_hooks: true`, aber kein `hook_protocol` → nichts registriert | ja | sequentiell | **Basis, Hook-Flag irreführend** |
| Codex | 0 | 62 `.toml` | ja (62/62) | advisory | `has_hooks: true`, kein `hook_protocol` | nein (dokumentiert) | tool-mediated ✓ | Basis |
| ZCode | 0 | 84 `.md` | ja | advisory | nein | ja | sequentiell | Basis |
| KimiCode | 0 | 62 `.md` | ja | advisory | nein | nein (dokumentiert) | swarm ✓ | Basis |

Frühere Befunde aus `2026-09-30-provider-audit-generation.md`: D1 (ungültiges Codex-TOML) und D5 (`.claude/`-Verweise im Body) sind **behoben** (0 Treffer bei allen 8 Nicht-Claude-Providern).

### 2.2 Offene, reproduzierte Provider-Defizite

| # | Befund | Beleg (diese Analyse) | Review-ID | Schwere |
|---|---|---|---|---|
| P1 | **`.gitignore` unvollständig bei Nicht-Claude-Projekten.** In einem Projekt mit nur Gemini, Codex, Mammouth oder KimiCode fehlen `AGENTS.personal.md`, `.meta-config/env*` und `sync.log` in `.gitignore`. Nur Opencode ignoriert `AGENTS.personal.md`. Folge: persönliche Notizen und Env-Defaults mit Secrets landen bei `git add -A` im Commit. | `grep` in den 5 Scratch-`.gitignore`: personal 0/0/0/0/1, env 0/0/0/0/0, sync.log 0/… | SR-A-11, -12, -31, -33 | **medium (Datenleck)** |
| P2 | **`has_hooks: true` ohne `hook_protocol`** bei Mammouth und Codex: Hook-Dateien werden nicht registriert, das Flag suggeriert aber Hook-Support. | `config/ai-providers.yaml`, `scripts/lib/hooks.py` (Kommentar „has_hooks providers without a verified hook_protocol") | — | low (Erwartungsfehler) |
| P3 | **Provider-Literale im Code**, die der Guard nicht sieht: z. B. `context.py` (`"Continue"` beim Prompt-Commands-Sync), `rules.py`/`roles.py` (Defaults `"Opencode"`/`"Claude"`), `gitignore.py:213` (`"Claude" not in providers`). Gesamt 35 Literal-Vorkommen in `scripts/lib`, 8 davon in `providers.py` (erlaubt, Registry-Fallback). Ein neuer Provider verhält sich dadurch anders als dokumentiert. | `grep` Provider-Namen in `scripts/lib` | SR-A-06, -12, -13, -21 | medium |
| P4 | **`--validate` prüft nicht die echte Pipeline** (eigener Handkopie-Loop in `cli_commands.py`; bewertet teils altes `sync.log`). Provider-Fehler können dadurch grün durchgehen. | System-Review | SR-A-24, -25 | medium |
| P5 | **`{{EXTRA_DONTS}}` / `{{PLATFORM}}` bleiben roh stehen**, wenn die Variable nicht in `project.yaml` steht (29 Dateien pro Provider in meinem Minimal-Projekt). Der Sync warnt dazu in `sync.log` (`Variable … not in config — placeholder remains`), setzt aber keinen Default; `--fill-defaults` löst es. *Korrektur (Umsetzung):* Es ist also keine stille Lücke, sondern eine Designentscheidung; M0.3 entfällt. | Scratch-Sync, `sync.log` | neu | low |
| P6 | **88 Validate-Warnungen sind False Positives**: `{{OUTPUT_GUARD_BLOCK}}`, `{{PARSE_INPUT_BLOCK}}` u. a. sind Block-Inlining-Variablen (`context.py`), kennt der Placeholder-Check aber nicht. Echte Warnungen gehen im Rauschen unter. | `sync.py --validate` (88 WRN, alle `placeholders.unknown`) | neu | low, aber hoher Folgeschaden |
| P7 | **Fallback ohne PyYAML**: Registry fällt still auf „nur Claude" zurück, Sync meldet Erfolg. | System-Review | SR-A-16 | low |
| P8 | **Dateimodus**: `write_atomic` setzt 0600 und entfernt `+x` auf allen generierten Dateien (Hooks laufen nur dank `bash`-Präfix). Betrifft Teams/Container mit anderer UID. | System-Review | SR-A-15 | medium |

Den Status der übrigen 130+ Befunde pflegt das Review-Dokument (Abschnitt 7); dort stehen alle noch auf „offen", obwohl seitdem mehrere Hook-Fixes gemergt wurden (#926–#955). Die Tabelle ist damit selbst eine Fehlerquelle (siehe M7).

### 2.3 Provider-bedingte Grenzen (kein Bug, aber transparent machen)

- 6 von 9 Providern erzwingen die Regel „Main-Chat darf nicht selbst editieren" nur per Prompt. Der Nutzer sieht das nur als `[INF]/[WRN]` im Konsistenz-Check (z. B. `repo-containment.no-hook-support` für Opencode im eigenen Projekt).
- 5 Provider haben nur sequentiellen Fan-out; parallele Pipelines laufen dort langsamer, nicht falsch.

---

## 3. Warum entstehen so viele Bugs? (Ursachenklassen)

Aus 139 Review-Befunden und den Provider-Audits:

| Klasse | Beispiele | Anteil (grob) |
|---|---|---|
| **A. Claude-first, andere nachgezogen** | P1, P3, SR-A-13/21/29, SR-A-31 | ~20 % |
| **B. Doppelte Logik / Handkopien** | Validate-Loop, Backup-Prune, Deaktivierungsfilter 4×, `init_*_personal` | ~15 % |
| **C. Fail-open statt fail-closed** | Guards: SR-B-08/09/10/15, SR-A-16/17 | ~15 % |
| **D. Toter Code, Naming-Debt** | SR-A-36–40 | ~10 % |
| **E. Rohes Parsing statt Tokenizer** (Shell/YAML/Null-Blöcke) | SR-B-01–04, SR-A-07/22/28 | ~20 % |
| **F. Tests prüfen Einzelfälle, nicht Invarianten** | Provider-Matrix wird nicht über alle 9 durchgespielt | quer |

Positiv: Es gibt schon ~3100 Tests, einen Provider-Agnostik-Guard (`tests/test_provider_agnostic_dispatch.py`) und 76 Szenario-Asserts. Das Problem ist weniger „zu wenig testen" als **falsche Hebel**: Die Tests sichern Einzelverhalten ab, aber Klassen A–E bleiben unsichtbar.

---

## 4. Plan zur drastischen Bug-Reduktion

Leitidee: **Klassen statt Einzelbugs eliminieren.** Jede Maßnahme tötet eine ganze Befundklasse und bekommt einen Test, der sie dauerhaft verhindert.

### Phase 0 — Sofort (1–2 Tage, hoher Hebel, kleines Risiko)

| ID | Maßnahme | Wirkung | Aufwand |
|---|---|---|---|
| M0.1 | **P1 fixen**: `.gitignore`-Basisblock = Vereinigung der `gitignore_entries` aller aktiven Provider (kein Namens-Gate); `personal_file` als Registry-Key | schließt Datenleck bei 5+ Providern (SR-A-11/12/31/33) | S |
| M0.2 | **P6 fixen**: Block-Inlining-Variablen im Placeholder-Check bekannt machen | `--validate` wieder lesbar (88 → ~0 Warnungen) | XS |
| M0.3 | ~~P5~~ entfällt: Sync warnt bereits (siehe P5) | — | — |
| M0.4 | **Guards fail-closed**: SR-B-08 war bereits behoben; SR-B-09 (ungültiges JSON) umgesetzt; SR-B-15 offen | stoppt stilles Abschalten der Schutzschicht | XS |
| M0.5 | Review-Statusliste (Abschnitt 7) mit tatsächlich gemergten PRs abgleichen | Wahrheit statt „alles offen" | XS |

### Phase 1 — Struktur (1–2 Wochen)

| ID | Maßnahme | Wirkung |
|---|---|---|
| M1.1 | **`--validate` nutzt die produktive Pipeline** (`_sync_stage_*` mit `project_root=test_repo`), Exit-Code aus `log.errors` des aktuellen Laufs (SR-A-24/25) | Ende des „grün, obwohl kaputt" |
| M1.2 | **Provider-Literal-Guard erweitern**: erkennt Namen in Call-Args, `.get()`-Keys, Subscripts, Default-Parametern. Danach P3 abarbeiten (Registry-Keys `personal_file`, `prompt_commands_dir`) | Klasse A bricht ab; neue Provider brauchen nur Config |
| M1.3 | **Eine Quelle pro Logik**: `resolve_providers` ↔ `deactivation.is_provider_active`; `plan_sync_backup_prune` gemeinsam für Preview/Prune; ein `init_personal_file(pc)` | Klasse B |
| M1.4 | **Hook-Tokenizer wiederverwenden** (`parse_git` aus `orchestrator-guard-impl.sh`) in `dod-push-check.sh` und Co. (SR-B-01–04) | Klasse E für Hooks |
| M1.5 | Helper `_as_dict()` für alle Config-Block-Reader (SR-A-07/22/28) | Null-/Typ-Abstürze weg |
| M1.6 | PyYAML-Pflicht: Registry-Load ohne PyYAML **bricht ab** statt Fallback (SR-A-16) | Klasse C in sync |

### Phase 2 — Test-Architektur (parallel, 2–3 Wochen)

| ID | Maßnahme | Wirkung |
|---|---|---|
| M2.1 | **Provider-Matrix-Test**: ein parametrisierter Test, der pro Provider (9) und pro Kombination (Einzel, alle, ohne Claude) den echten Sync fährt und prüft: valides Format (TOML/YAML/JSON), keine Roh-Platzhalter, keine `.claude/`-Reste, `.gitignore` vollständig, Idempotenz (2. Lauf = 0 Änderungen). **Das ist das, was ich hier manuell gemacht habe, als CI-Test.** | fängt P1, P5 und jede Regression der Klasse A automatisch |
| M2.2 | **Golden-Snapshots** der erzeugten Agent-Frontmatter pro Provider (klein, nur Header) | unbeabsichtigte Format-Änderungen sofort sichtbar |
| M2.3 | **Property-Test „neuer Provider"**: Dummy-Provider nur über Config registrieren → Sync darf keinen Code-Pfad mit Namen brauchen | beweist Provider-Agnostik |
| M2.4 | **Fail-closed-Tests für jeden Guard** (kaputtes JSON, fehlendes Python-Modul, Unterverzeichnis-`cwd`) | Klasse C |
| M2.5 | **Fuzz/Matrix für Shell-Parsing** der Hooks (`git -C . push`, `--tags`, Heredoc, Pfade mit Leerzeichen) | Klasse E |

### Phase 3 — Prozess und CI (1 Woche)

| ID | Maßnahme | Wirkung |
|---|---|---|
| M3.1 | CI zusammenführen: `validate.yml` führt **kein pytest** aus, `orchestration-test.yml` führt `pytest tests/` aus. Beide als Pflicht-Checks für `main`; Matrix Python 3.11/3.13 | Tests gaten Merges verlässlich |
| M3.2 | Test-Laufzeit senken (die Suite braucht lokal deutlich länger als 10 min): `pytest-xdist`, Slow-Marker, Smoke-Subset für PRs | schnelles Feedback, höhere Disziplin |
| M3.3 | **Warnungs-Budget**: `--validate` darf 0 unerwartete WRN haben, sonst CI rot (nach M0.2) | Rauschen bleibt weg |
| M3.4 | **Mutation-/Coverage-Gate** auf `scripts/lib/providers.py`, `agent_sync.py`, `sync_pipeline.py` (z. B. ≥ 85 % Branch) | Kernpfade gesichert |
| M3.5 | PR-Template mit Pflichtfeld „betroffene Provider" + Szenario in `tests/scenarios/registry.md` (existiert als Konvention, nicht erzwungen) | Klasse A schon im Review |
| M3.6 | Toten Code löschen (SR-A-36–40) und Naming-Debt (`is_claude` → `has_dedicated_ctx`) | weniger Fläche für Fehler |

### Phase 4 — Provider-Transparenz (nach Phase 1)

- Konsistenz-Check erzeugt **einen** Provider-Fähigkeitsbericht („Provider X: Gate = advisory, Hooks = nein, Fan-out = sequentiell") bei jedem Sync, statt verstreuter INF/WRN.
- `has_hooks` ohne `hook_protocol` → eindeutiger Zustand (`has_hooks: false` oder Protokoll ergänzen) (P2).
- `docs/providers/multi-provider.md` um die Matrix aus 2.1 ergänzen und aus der Config generieren (keine Handpflege).

---

## 5. Erwartete Wirkung

| Maßnahme | Befunde, die sofort entfallen | Befundklasse dauerhaft verhindert |
|---|---|---|
| Phase 0 | ~10 (P1, P5, P6, SR-B-08/09/15, SR-A-31/33) | Datenleck, Rauschen |
| Phase 1 | ~35 (SR-A-05–08, 12–13, 21–25, 28–29, 41; SR-B-01–04) | A, B, E |
| Phase 2 | — (Prävention) | A, C, E automatisch bei jedem PR |
| Phase 3 | ~10 (tote Funktionen, Naming) | F, Regressionen |

Realistisch: **60–70 % der aktuell offenen Befunde** fallen in Phase 0/1 weg, und die Phase-2-Tests verhindern, dass dieselben Klassen nach neuen Providern oder Features wieder auftreten. Der Rest (Admin-UI/A11y, SR-D) ist unabhängig und läuft im bestehenden Bugfix-Plan (`docs/plans/2026-10-07-bugfix-batch-2.md`) weiter.

## 6. Empfohlene Reihenfolge

1. **M0.1 + M0.2 + M0.4** (Datenleck, Warn-Rauschen, Guards) — eine Wave, ein PR.
2. **M2.1** (Provider-Matrix-Test) direkt danach: Er sichert M0 ab und ist der größte Einzelhebel gegen Klasse A.
3. **M1.1 + M1.2** (Validate-Pipeline, Literal-Guard).
4. Rest nach Phasenplan.

## 7. Nicht untersucht / offen

- Vollständiger Testsuite-Lauf (nur teilweise gelaufen).
- Verhalten der Provider-Tools zur Laufzeit (nur Generierung geprüft).
- Multi-Provider-Szenario (alle 9 gleichzeitig) und Zweitlauf-Idempotenz in dieser Analyse nicht erneut gefahren; die Audits vom 2026-09-30 nennen dort die Bootstrap-Kollision D8.
- Admin-Server/-UI (Dimension d) wurde bewusst ausgespart.

## 8. Umsetzungsstand Phase 0 (2026-10-11)

| Maßnahme | Stand |
|---|---|
| M0.1 `.gitignore`-Leck (P1) | **umgesetzt**: Baseline-Einträge auf dem Nicht-Claude-Pfad, `AGENTS.personal.md` per Registry bei 5 Providern. Vorher 8 von 9 Provider-Tests rot, jetzt grün. |
| M0.2 Validate-Fehlalarme (P6) | **umgesetzt**: `placeholders.unknown` 88 → 0. |
| M0.3 | entfällt (siehe P5). |
| M0.4 Guards | SR-B-09 **umgesetzt**; SR-B-08 war schon behoben; SR-B-15 offen. |
| M2.1 Provider-Matrix-Test | **umgesetzt**: `tests/test_provider_matrix_sync.py`, 45 Fälle (9 Provider × 5 Invarianten). Laufzeit ca. 3 min; Teil von M3.2 (Test-Laufzeit). |

## 9. Umsetzungsstand Phase 1 (2026-10-11)

| Maßnahme | Stand |
|---|---|
| M1.1 `--validate` | **teilweise**: Exit-Code zählt jetzt die Fehler des aktuellen Laufs (SR-A-24, 3 Tests, vorher rot). Die Handkopie der Pipeline (SR-A-25, Wiederverwendung der `_sync_stage_*`) ist **noch offen**; das ist ein eigener Refactor (M). |
| M1.2 Provider-Literal-Guard | **umgesetzt**: neuer AST-Guard `test_no_provider_literal_usage_in_lib`. Echte Verstöße behoben: `sync_prompts_for_continue` (SR-A-06), `.gitignore`-Basisblock per Capability (SR-A-12), Flat-Override-Warnung per Capability (SR-A-13). 10 alte Default-Parameter-Stellen stehen auf einer Ratchet-Allowlist (SR-A-21 bleibt dafür offen). |
| M1.3 Doppelte Logik | offen |
| M1.4 Hook-Tokenizer | **entfällt**: #955 hat SR-B-01–04 bereits behoben (nachgeprüft: `--tags`, `git -C . push`, `/usr/bin/git push` blockieren, `grep … git push` nicht). |
| M1.5 Null-Helper | **teilweise**: `unknown-fallback` (SR-A-28) behoben. Das Schema lehnt verschachtelte Nulls beim Laden ohnehin ab, erreichbar nur für programmatische Configs. |
| M1.6 PyYAML | **umgesetzt** (SR-A-16): Registry-Load bricht laut ab. |
