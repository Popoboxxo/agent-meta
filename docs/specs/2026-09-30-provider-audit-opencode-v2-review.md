# Review — Provider-Audit Gap Closure + Opencode v2 Support (Spec + Design)

- **Review-Gegenstand:** `docs/specs/2026-09-30-provider-audit-opencode-v2.md` (Spec, DRAFT) und
  `docs/specs/2026-09-30-provider-audit-opencode-v2-design.md` (Systemdesign)
- **Reviewer:** concept-reviewer · **Datum:** 2026-10-01
- **Branch/HEAD:** `feat/provider-audit-opencode-v2` @ `65a493ec` (read-only)
- **Faktenbasis:** `docs/analysis/2026-09-30-provider-audit-runtime-consolidation.md` (H1–H10, N1–N20, A1–A11),
  `docs/analysis/evidence/2026-09-30-*.md`, `docs/analysis/2026-09-30-provider-audit-{generation,docs-part1,docs-part2}.md`
- **Verdikt:** **CHANGES_REQUESTED**

---

## Scope

Geprüft wurden die 10 geforderten Kriterien: Faktenintegrität, Provider-Agnostik-Constraint,
Opencode v1/v2-Trennung, Akzeptanzkriterien, Idempotenz/`--check`, Bootstrap-Kollision (D8),
Vollständigkeit gegen die 10-HYPOTHESEN-Matrix/N1–N20, Logik/Risiken/Feasibility,
Threat-Model (4 Fragen), Nicht-Ziele/Scope. Zusätzlich Pflichtsektionen/Trace-Anker/Approval-Marker
(Spec-Review-Modus §7.1).

Die Faktenbasis ist **stark**: F1–F11, N1–N20 und A1–A11 sind in der Spec korrekt zitiert und
physisch in der Evidenz nachvollziehbar (Codex-Toml 2/58, Kimi `kimi-code/`-Prefix, Mammouth
`tools`-Map, Continue-`config.local.yaml`-required-Felder, Copilot-Pfade, Opencode-v2-Silent-Drop,
D8-Bootstrap-Kollision). Die Config-Dispatch-Architektur (DECISION-1/2/5) ist konsistent und
provider-neutral. Die Befunde unten betreffen nicht die Faktenlage, sondern (a) einen
**evidenztreuen Umsetzungsweg**, der an **zwei konkreten Stellen fehlt**, und (b) **testbare ACs**.

---

## Findings by severity

### HIGH

**H-1 — Opencode v2 nested `mcp.servers` formt den bestehenden MCP-Writer nicht um; `surface-version` ist in §3.4 nicht als Format verankert.**
- **Dimension:** Logic gap / Feasibility; **Belege:** `scripts/lib/mcp_provider_config.py:633-635`
  (`_update_json_config(path, "mcp", …)` — flacher Top-Level-Key), `config/ai-providers.yaml:225-228`
  (`mcp-config.format: opencode-json`), Spec §2.1/§2.5/§3.4, Design §4.1.
- **Befund:** F4/N5 fordert nested `mcp.servers` für v2. Der Spec nennt die Zielform (`mcp.servers`)
  und den Schalter (`surface-version: v2`), aber die **Interface-Contract-Tabelle §2.5/§3.4 lässt den
  Format-Pfad auf `opencode-json` stehen** (Zeile „`opencode-json` | `opencode.json` `mcp` (v1) /
  `mcp.servers` (v2)"). Damit existieren zwei Lesarten: (i) `surface-version` verzweigt **innerhalb**
  des Writers (neuer provider-gekoppelter, wenn auch flag-getriebener Pfad), oder (ii) es braucht einen
  **eigenen Format-Wert** (`opencode-json-v2`), der den bestehenden Dispatch `if fmt == …`
  (`mcp_provider_config.py:633`) mit einem neuen Key versorgt. Der Spec legt keine der beiden fest und
  liefert **kein** AC, das die Writer-Wahl prüft. Bei Lesart (i) landet ein faktisch
  provider-spezifischer Zweig im Writer — genau das Anti-Pattern, das AC-14 absichern soll.
- **Gefordertes Fix:** In §2.5/§3.4 die Dispatch-Regel eindeutig machen (empfohlen: neuer
  Format-Wert `opencode-json-v2` mit eigener Zeile in der Format-Tabelle, `mcp.servers` als
  Contract) **und** ein AC ergänzen, das nach `surface-version: v2` das Vorhandensein von
  `mcp.servers` (und das Fehlen von flachem `mcp`) am erzeugten `opencode.json` prüft. V1-Byte-Form
  explizit als unverändert fixieren.

**H-2 — Kein Migrations-/Rollback-Pfad für die Copilot-/Antigravity-Pfadänderung (SemVer-Bruch ohne Übergang).**
- **Dimension:** Risks / Migration; **Belege:** Design §6.1–§6.2 (`EXTRA_DONTS: no breaking changes
  without major version bump`), Spec §11, AC-8/AC-9; Code: `config/ai-providers.yaml:317`
  (`.github/copilot/agents`, `:319` `.github/copilot/COPILOT.md`, `:328` rules; `:99` `.gemini/agents`).
- **Befund:** Die Spec klassifiziert Copilot- und Antigravity-Pfadänderungen als **major für den
  betroffenen Provider** und die Bereinigung als „stale-cleanup inside the managed agent dir". Der
  echte Bruch ist aber nicht nur das Agent-Verzeichnis: Copilot-Context-File
  (`.github/copilot/COPILOT.md` → `.github/copilot-instructions.md`) und Rules
  (`.github/copilot/rules` → `.github/instructions/*.instructions.md`) sind **eigene Config-Keys**,
  deren Alt-Pfade außerhalb der `agents_dir` liegen. Für diese Keys fehlen (1) ein expliziter
  Cleanup-/Backup-Nachweis, (2) eine dokumentierte Reihenfolge „neuer Pfad schreiben, dann Alt-Pfad
  entfernen" und (3) ein Rollback. Ein Major-Bump ohne Migrationspfad verstößt gegen die projekt-
  eigene `EXTRA_DONTS`-Regel, die die Spec selbst zitiert.
- **Gefordertes Fix:** §11/Design §6.2 um eine migrierbare Tabelle erweitern: pro geändertem Key
  (agents_dir, context_file, rules_dir) alter Pfad → neuer Pfad, Cleanup-Mechanik (managed-marker +
  `.sync-backup-<ts>`), und ein Rollback-Schritt. Ein AC, das nach dem Sync in einem Bestandsprojekt
  „alter Pfad entfernt, neuer Pfad vorhanden, keine Nutzerdatei gelöscht" prüft.

### MEDIUM

**M-3 — AC-3 (`--check` rc=0) vermischt Repo-Drift und Generator-Korrektheit; ein grüner AC-3 würde die Branch-Drift verstecken.**
- **Dimension:** Acceptance criteria / Non-goals; **Belege:** Spec §8 AC-3, §9, ADR-8;
  `docs/analysis/evidence/2026-09-30-regression-tests.md` §6 (`27 file(s) out of sync`, rc=1).
- **Befund:** §9 empfiehlt korrekt, den 27-Datei-Drift **in-scope** zu beheben (AC-3 erfordert
  rc=0 auf clean tree). Diese Entscheidung ist als `DECISION-NEEDED` markiert, aber **AC-3 bleibt
  ein einziger Pass/Fail-Satz auf dem Repo-Root**. Wird der Scope-Split gewählt (Alternative in §9),
  wird AC-3 stillschweigend unerfüllbar oder — schlimmer — durch ein `git checkout`/Regenerate
  „grün", ohne dass der Generator-Drift gegen die Templates tatsächlich behoben ist. Der Spec fehlt
  eine **explizite Trennung**: „Repo-Artifakte regeneriert" vs. „Generator erzeugt driftfreie
  Artifakte".
- **Gefordertes Fix:** AC-3 in zwei Kriterien teilen: (AC-3a) Scratch-Consumer-Projekt: `--check`
  rc=0 nach sauberem Sync (Generator-Korrektheit, immer prüfbar); (AC-3b) Repo-Root: `--check` rc=0
  **nur** nach dem Regenerate-Commit (Branch-Hygiene, Scope-abhängig). Bei Scope-Split muss AC-3a
  bestehen bleiben.

**M-4 — AC-19 nennt „63 existing + scenarios 64–72" als Run-Kommando ohne Bezug auf das 63-Katalog-Inventar; der Katalog läuft bereits, aber Scenario 71 „all 9 providers" ist nicht abgedeckt.**
- **Dimension:** Acceptance criteria / Verification commands; **Belege:** Spec §8 AC-19,
  `tests/scenarios/run.sh`, `tests/scenarios/registry.md` (62/63 vorhanden),
  `tests/scenarios/configs/62-*.project.yaml`.
- **Befund (a):** AC-19 verlangt `run.sh`-PASS über 63 Bestandsszenarien + 64–72. Der Baseline-Report
  bestätigt 63 PASS, die neuen IDs sind sauber. **Aber:** Scenario 71 (`--check`-Idempotenz **all 9
  providers**) setzt voraus, dass ein Multi-Provider-Szenario **alle 9 Provider gleichzeitig** in einer
  Generation aktiviert — der Bestandskatalog hat 62/63, aber die Abdeckung „all 9 inkl. Copilot/ZCode/
  KimiCode" ist im Scenario-Bestand nicht belegt. Ein reiner `run.sh`-Aufruf verifiziert das nicht.
- **Befund (b):** AC-19 enthält keinen Bezug auf die **asserts-Konvention** (`asserts/<id>.sh` +
  registry.md-Zeile), obwohl §7.1/§10.1 das für jede neue ID fordert. Damit ist nicht sichergestellt,
  dass 64–72 nicht als No-Op-Szenarien durchlaufen.
- **Gefordertes Fix:** In AC-19 explizit auf die 9 neuen `asserts/`-Skripte + Registry-Zeilen
  verweisen; für Scenario 71 ein Fixture-Profil „all-9-providers" benennen, das die Provider-Liste
  enthält (und belegen, dass es existiert oder neu angelegt wird).

**M-5 — `skills: true` wird für ZCode + KimiCode gesetzt, während `ai-providers.yaml` die `skills`-Capability nicht deklariert; Interaktion mit dem three-file-invariant-Test unklar.**
- **Dimension:** Consistency / Datenintegrität; **Belege:** `config/ai-providers.yaml:503-507` (ZCode
  capabilities ohne `skills`), `:554-557` (KimiCode ohne `skills`), `:521`/`:571` (skills_dir
  vorhanden), `tests/test_provider_three_file_invariant.py:44-90` (sweept **nur** ai-providers ↔
  provider-capabilities/bootstrap/delegation-syntax), Spec §2.2/AC-15.
- **Befund:** Die Spec fordert `skills: true` in `provider-capabilities.yaml` für ZCode/KimiCode als
  „verifizierte" Capability. Die tatsächliche Artefakt-Erzeugung wird jedoch in `ai-providers.yaml`
  über das `skills`-Listenelement bzw. `skills_dir` gesteuert (siehe `scripts/lib/skills.py`,
  `rules.py`). Solange `ai-providers.yaml` bei ZCode/KimiCode kein `skills`-Listenelement trägt,
  bleibt `skills: true` in der Capabilities-Datei ein **deklarativer Widerspruch** zur
  Generator-Realität. AC-15 („every provider declares skills and artifact-validation") prüft nur die
  Deklaration, nicht die Konsistenz zwischen beiden Dateien. Der Baseline-Report (F9/N13) zeigt genau
  diesen Fehler für Copilot („skills empty").
- **Gefordertes Fix:** In §2.2 und AC-15 fordern, dass `skills: true` **beide** Stellen konsistent
  hält (Capability-Flag **und** `ai-providers.yaml capabilities`/`skills_dir`), und den
  three-file-invariant-Test bzw. einen neuen Konsistenz-Check auf diese Kopplung erweitern.

**M-6 — Race-Condition der Bootstrap-Sub-Marker in Multi-Provider-Projekten: `marker_id` defaultet auf Provider-Namen, aber nur Gemini/ZCode injizieren — Spec sagt nicht, wie die übrigen 5 AGENTS.md-Provider den Bootstrap-Block behandeln.**
- **Dimension:** Completeness / Bootstrap-Kollision (D8); **Belege:** Design §3.5, Spec §2.4/§7;
  `config/ai-providers.yaml:101,176,437,496,548` (5 Provider teilen `AGENTS.md`),
  `config/provider-bootstrap.yaml` (nur Gemini/ZCode `inject-bootstrap-instructions`); F10 §6.
- **Befund:** Das Sub-Marker-Design löst D8 für Gemini+ZCode korrekt. Offen bleibt: von den 5
  AGENTS.md-Providern (Gemini/Opencode/Codex/ZCode/KimiCode) haben 3 (`action: none`) keinen
  Bootstrap. Der Spec beschreibt den Cleanup nur für Provider mit `inject`-Action (korrekt), aber
  nicht, wie sichergestellt wird, dass ein **fremder, alter** generischer Marker
  (`<!-- agent-meta:bootstrap-begin -->` ohne `:id`) im ersten Sync eindeutig einem Provider
  zugeordnet wird. Die Migration „alter Marker → provider-scoped pair" setzt voraus, dass
  erkennbar ist, welcher Provider den Alt-Marker geschrieben hat — im Kollisionsfall (ZCode überschrieb
  Gemini) ist das exakt **nicht** eindeutig. Die Spec lässt offen, welcher Provider den Alt-Marker
  erbt.
- **Gefordertes Fix:** §7/Design §3.5 um eine Migrationsregel ergänzen: Alt-Marker ohne `:id` wird
  beim ersten Sync von **jedem** `inject`-Provider neu geschrieben (d. h. Alt-Marker entfernen, dann
  pro Provider eigenen Sub-Marker setzen), Reihenfolge deterministisch, ohne Anspruch auf
  Rekonstruktion des Verursachers. Ein AC, das aus dem Zustand „nur ZCode-Alt-Marker vorhanden" nach
  Sync in einem Gemini+ZCode-Projekt **beide** Sub-Marker erwartet.

### LOW

**L-7 — AC-14 („no new provider-name branch") ist als grep-basierter Test deklariert, aber der bestehende Test seedet nur eine feste Modulliste; neue Module (`artifact_validate.py`, `consistency/artifact_contracts.py`, `consistency/model_contracts.py`) sind nicht automatisch erfasst.**
- **Dimension:** Consistency; **Belege:** `tests/test_provider_agnostic_dispatch.py:27-56` (`_TOUCHED_MODULES`
  explizite Liste), Spec AC-14/§10.2.
- **Befund:** AC-14 verspricht „no new `if provider == …`". Die bestehende Liste ist statisch; die in
  dieser Spec neu eingeführten Module fehlen darin. Ohne Erweiterung kann genau das Anti-Pattern in
  den neuen Dateien entstehen, ohne dass AC-14 greift.
- **Gefordertes Fix:** AC-14/§10.2 verlangen, `_TOUCHED_MODULES` um die neuen Module zu erweitern
  (oder auf ein Verzeichnis-Sweep über `scripts/lib/**` umzustellen).

**L-8 — `artifact-validation: true` (default) ist ein globaler Opt-out pro Provider; die Spec nennt keinen Provider, der ihn braucht, und keine Begründungsschranke, die der Three-File-Test erzwingt.**
- **Dimension:** Completeness / Risks; **Belege:** Spec §2.2 („false only with a documented reason"),
  Design §3.2, AC-15; Code: kein Konsument existiert (Grep `artifact-validation` → 0 Treffer).
- **Befund:** Der Key wird neu eingeführt, aber der Three-File-Test prüft nur **Präsenz**, nicht die
  Begründungspflicht bei `false`. Ein Provider könnte sich still der Validierung entziehen (genau die
  Fail-open-Klasse, die das Threat-Model unter 2(b) nennt).
- **Gefordertes Fix:** Entweder Begründungsfeld (`artifact-validation-reason`) und Test darauf, oder
  `false` nur zulassen, wenn ein zweiter Key den Grund trägt.

**L-9 — Risiko-Tabelle nennt nur 5 Risiken, aber SemVer-Bruch für Copilot/Antigravity fehlt explizit.**
- **Dimension:** Risks; **Belege:** Design §8.1, Spec §13.2 (7 Risiken).
- **Befund:** Der Major-Bump für Pfadänderungen (H-2) ist in §6.1 erwähnt, aber **nicht** als Risiko
  in §13.2 gelistet. Ein Konsument, der semantisch auf „major" reagiert (Release-Pipeline), findet kein
  Motivationsrisiko.
- **Gefordertes Fix:** Risikozeile „Major-Bump für Pfadänderungen bricht Bestands-Consumer" mit
  Mitigation (Migrations-/Rollback-Pfad aus H-2) ergänzen.

**L-10 — AC-13 (`--validate` rc 1 bei `allowed-fields`-Verstoß) ist nur über einen synthetischen Verstoß testbar; der Spec nennt kein Fixture.**
- **Dimension:** Acceptance criteria; **Belege:** Spec AC-13, §5; `tests/test_artifact_contracts.py`
  (neu, kein Fixture benannt).
- **Befund:** AC-13 verlangt einen v2-Artefakt mit einem Key außerhalb `allowed-fields`. Wie dieser
  Zustand im Testlauf hergestellt wird (Fixture-Provider, injizierte Frontmatter, Test-Repo), bleibt
  offen — sonst ist der Test nicht reproduzierbar.
- **Gefordertes Fix:** Fixture-Mechanismus im Spec benennen (z. B. ein Test-Provider-Config mit
  engem `allowed-fields` oder eine manipulierte generierte Datei in einem Scratch-Repo).

### INFO

**I-11 — AC-1/AC-2/AC-6 nennen reale Harness-Kommandos (`codex mcp list`, `kimi acp`,
`mammouth agent list`), die in der Audit-Umgebung teils SIGILL/UNVERIFIABLE sind.**
- **Beleg:** F6 (`agy` SIGILL), F9 (kein Copilot) — die Runtime-STATIC-Spalte in §10.3/§7.4 ist
  vorbildlich, aber AC-1/AC-2/AC-6 lesen sich als **verpflichtende** Kommandos. Empfehlung: in der
  AC-Tabelle mit „VERIFIED method, harness-dependent" markieren, damit der Plan sie nicht als
  CI-Pflicht interpretiert.

**I-12 — Die Spec schreibt STATIC-Aussagen korrekt als STATIC; die Design-§0-Tabelle mischt jedoch `VERIFIED` (F3) mit `F4` (v2-Runtime), ohne die v2-Aussagen auf Runtime-Ausführung in dieser Umgebung zu relativieren.**
- **Beleg:** Design §0 F4; Evidence `runtime-opencode-v2.md` §1 (v2 installiert in Scratch, nur
  `debug agents` ausgeführt, kein Session-Turn). v2-Load ist ein **Runtime-Parse**, nicht ein
  vollständiger Session-/Turn-Beweis (siehe v2-Evidenz „not run" §4). Die Spec hebt das in §10.3
  korrekt auf STATIC ab — das Design sollte die F4-Zeile entsprechend qualifizieren.
- **Empfehlung:** F4-Zeile auf „VERIFIED (parse/debug), Session-Turn UNVERIFIABLE" schärfen.

**I-13 — Non-Goal „Fixing the 85 consistency warnings" schließt `CO-2` (`templates/configs/CONTINUE.config-template.yaml:28` `roles: [chat, edit, agent]`) nicht explizit ein.**
- **Beleg:** N11 (`runtime-continue.md` §3/§8), Spec §1.3/§2.1. Die Spec adressiert `config.local.yaml`
  required-Felder und `.continue/config.yaml` Zod-Fehler über `continue-yaml`, aber das
  **Template** `CONTINUE.config-template.yaml:28` bleibt unerwähnt. Wenn der Generator das Template
  rendert, ist CO-2 ein **Erzeuger**-Defekt (nicht nur ein Warning).
- **Empfehlung:** Entweder in Scope aufnehmen (Template-Zeile `roles`-Enum-konform machen) oder
  unter Non-Goals explizit als separate Follow-up-ID führen — nicht implizit offen lassen.

---

## Threat-model check (4 Fragen, knapp)

1. **Was wird gebaut?** Sync-zeitiger Artefakt-Generator + Validator für 9 Harnesses, erweitert um
   provider-neutrale Config-Contracts und eine Opencode-v2-Fläche (§2, §8.2).
2. **Was kann schiefgehen?** (a) Silent-Drop bleibt unbemerkt, wenn der Validator nicht im
   `--check`-Pfad hängt; (b) Fail-open: `artifact-validation: false` ohne Begründungsschranke (L-8);
   (c) Migration löscht Nutzerinhalte außerhalb Managed-Marker (H-2, M-6); (d) v2-Writer wird
   faktisch provider-gekoppelt (H-1).
3. **Mitigations?** Allow-list + Parse-Validatoren fail-loud in CI; managed-marker-scoped Writes +
   `.sync-backup-<ts>`; config-key-only Dispatch (AC-14, L-7); `model-catalog` (OQ-3).
4. **Konsequenzen?** Höhere Sync-Laufzeit + gepflegter Contract pro Provider; Antigravity/Copilot/
   ZCode-workspace bleiben runtime-unverifizierbar (STATIC/HYPOTHESIS) — bewusst und dokumentiert.

Das Threat-Model ist als knappe Vier-Fragen-Antwort vorhanden (§8.2) und deckt die Risiken ab, mit
Ausnahme der H-1/H-2/L-8-Lücken oben.

---

## Verdikt

**CHANGES_REQUESTED.**

Begründung: Die Faktenbasis ist evidenztreu und die Architektur (Config-Contracts, Fail-loud-
Validator, v1/v2-Trennung) ist tragfähig. Zwei **HIGH**-Befunde sind blockierend für den Plan, weil
sie die Umsetzung an konkreten Stellen unbestimmt lassen bzw. einen SemVer-Bruch ohne Migrationspfad
einführen: **(H-1)** der v2-MCP-Nesting-Pfad ist im Interface-Contract/AC nicht verankert;
**(H-2)** Copilot/Antigravity-Pfadänderungen haben keinen Migrations-/Rollback-Pfad. Hinzu kommen vier
MEDIUM-Befunde (AC-Schärfung AC-3/AC-19, skills-Konsistenz, Bootstrap-Migrationsregel) und fünf
LOW/INFO-Präzisierungen. Nach Auflösung von H-1 und H-2 sowie der AC-Schärfungen ist die Spec
approval-fähig; sie ist **nicht** BLOCKED, da die Lösungspfade klar umrissen und die Faktenlage
verifiziert ist.

Zusätzlich (Spec-Review-Modus): **Trace-Anker** vorhanden (`spec-id: SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30`,
§0/§2 und Trace anchor am Ende). **Pflichtsektionen** vollständig. **Approval-Marker** korrekt als
`Status: DRAFT — PENDING APPROVAL` markiert; da die Spec fünf `DECISION-NEEDED`-OQs plus die
Scope-Entscheidung (§9) explizit offen hält, ist der DRAFT-Status konsistent — der Reviewer setzt
`Status: APPROVED` erst nach Auflösung der OQs und der obigen Findings.

Sprachhinweis: Findings sind in der Sprache der eingehenden Spec (Englisch) gehalten.

---

## Trace anchor

`spec-id: SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30`

---

## Iteration 2 (fokussierte Nachprüfung, 2026-10-01)

**Gegenstand:** `…opencode-v2.md` + `…opencode-v2-design.md` (beide seit Iteration 1 geändert).
**Verdikt:** **APPROVED** (alle Iteration-1-Findings H-1…I-13 umgesetzt; nur Minor-Restone).

Verifizierte Code-Anker (read-only, HEAD `65a493ec`): `mcp_provider_config.py:633-635` = flat-`mcp`-Zweig,
`_write_provider_config:619-653`, `_update_zcode_json_config:266-287` (nested `setdefault("mcp",{})["servers"]` :285);
`ai-providers.yaml` Copilot `:317/:319/:328`, Gemini `:99/:104/:143`, ZCode capabilities `:503-507` / `skills_dir:521`,
KimiCode `:554-557` / `skills_dir:571`, shared `AGENTS.md` `:101/:176/:437/:496/:548`;
`test_provider_agnostic_dispatch.py:_TOUCHED_MODULES:27-56`; `registry.md:37-42/44-46`;
`CONTINUE.config-template.yaml:28` (`roles: [chat, edit, agent]`) + Header `:6` ("NEVER overwritten");
`skills.py:376`, `skill_channel.py:42`, `plugins.py:66`; `provider-bootstrap.yaml:16/49/11/44/77`;
`context.py:753/759-762/765`; `bootstrap.py:152-153`; `generated_file_drift.py:357-388`; `rule_index.py:122-146`;
`consistency-check.py:140`; `pipelines.py:757`.

**Resolution je Finding:** H-1 ok (§2.5/§2.6 Dispatch-Regel + neuer Formatwert `opencode-json-v2`, v1 eingefroren;
Design §3.4/DECISION-7/§3.6; AC-21/AC-23). H-2 ok (Design §6.2.1 5-Schritt-Sequenz + per-Key-Tabelle inkl.
context_file/rules_dir, User-File-Guard, Rollback; Spec §11.1 + AC-22; Major-Bump-Begründung §6.1/ADR-9).
M-3 ok (AC-3a/3b, §9). M-4 ok (AC-19 asserts/<id>.sh + registry-Zeile + Fixture-Profil all-9-providers, §10.1).
M-5 ok (Spec §2.2 Kopplungsregel + AC-15(c)/AC-25 + Risikozeile §13.2; Code-Anker korrekt).
M-6 ok (§2.4/§7 + Design §3.5 Determinismus, AC-16(c), Scenario 70). L-7 ok (AC-14/§10.2 Sweep oder erweiterte Liste).
L-8 ok (`artifact-validation-reason` + AC-24). L-9 ok (Risikozeile Spec §13.2 + Design §8.1). L-10 ok (AC-13 Fixture).
I-11 ok (AC-1/2/6 „CI-mandatory / VERIFIED method, harness-dependent"). I-12 ok (F4 parse/debug, Session-Turn UNVERIFIABLE).
I-13 ok (CO-2 unter Non-Goals §1.3 + Design OQ-9).

**Neue Wahrnehmungen (MINOR, non-blocking — Spec bleibt maßgeblich, AC-23 bindend):**
- Design §3.1-Zeile `surface-version` sagt „Consumed by … the MCP writer" und widerspricht damit DECISION-7/§3.4/AC-23 („writer never branches on surface-version"); Formulierung auf „selects the `mcp-config.format` value, consumed by the format-dispatched writer" schärfen.
- Design §3.2/§7.2 spiegeln die Spec-§2.2-Härtungen (`artifact-validation-reason`-Gate L-8, `skills`↔`capabilities`/`skills_dir`-Kopplung M-5) nicht explizit; Design-Testzeile nur „skills + artifact-validation declared".
- Design §3.3 nennt `action_* (v2 action names)` in der pipeline_notation; `_PROVIDER_NOTATION:757-828` hat keinen `action_*`-Key und Spec §2.3 listet ihn nicht → Design-Ergänzung präzisieren oder streichen.

Keine neuen CRITICAL/HIGH-Befunde. Die `DECISION-NEEDED`-OQs (OQ-1/4/5/7/8 + Scope §9) bleiben bewusst offen und sind
Approval-Gate-Entscheidungen, keine Review-Findings.

