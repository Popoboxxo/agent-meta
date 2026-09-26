# Dynamic Routing + Template Slimming — B2b-Diff-Manifest

> **Status:** abgeschlossen (Task 16)
> **Trace-Anker:** `spec-id: SPEC-dynamic-routing-template-slimming` (Status APPROVED, Revision 4)
> **Branch:** `feat/dynamic-routing-template-slimming`
> **Ziel-AK:** B2b (normalisierte Near-Duplikate), B3 (Snippet-Kopiervertrag)
> **Quelle der Klassifikation:** `tests/test_template_slimming_equivalence.py` — `_NORMALIZATIONS` (deklarative Variantentabelle) und `_KIND_REGISTRY` (Migrierte-Datei-Registry).
> **Migrations-Commits:** `166dbcf7` (se-*, Task 12), `1d849173` (knowledge-*, Task 13), `0951dd19` (übrige `1-generic`, Task 14), `b8a921fd` (2-platform, Task 15).

## 1. Zweck und Abgrenzung

Dieses Manifest dokumentiert für **jedes normalisierte Near-Duplikat** der Slimming-Migration
(Tasks 12–15) die Datei, den Block, die B2a/B2b-Klassifikation und den abschnittsweisen
Äquivalenz-Nachweis. Grundlage ist ausschließlich die reale, committete Klassifikationstabelle
`_NORMALIZATIONS` sowie die realen Diffs der vier Migrations-Commits — keine Annahme.

Zwei Ausprägungen werden unterschieden (Spec §5.5 / AC B2):

- **B2a — im aktuellen LF-Korpus text-identisch:** Der Inline-Block entspricht exakt dem
  kanonischen Snippet-Text der Block-Variable. Die Kanonisierung ist eine Identitätstransformation;
  der generierte UTF-8-Text bleibt im aktuellen LF-Korpus identisch zur Golden-Baseline
  (`tests/fixtures/slimming-golden/`). Das ist eine Text-/Zeilenenden-Evidenz, keine
  Raw-Byte-Identitätsaussage für CRLF-Eingaben.
- **B2b — normalisiert:** Der Inline-Block weicht vom kanonischen Snippet-Text ab
  (Leerzeilen, rollenspezifische Zusätze, weitere Prosa). Die Abweichung ist hier mit genau
  deklariertem Normalisierungsschritt und Nachweis gelistet.

Die Klassifikation wird im Gate ausschließlich aus `_NORMALIZATIONS` abgeleitet
(`tests/test_template_slimming_equivalence.py:383-966`); ein nicht deklariertes Near-Duplikat
lässt das Gate fehlschlagen.

## 2. Kanonische Blöcke (Ziel-Text)

| Block-Variable | Quelle (Inlining-Pfad) | Kanonischer Inhalt |
|---|---|---|
| `PARSE_INPUT_BLOCK` | `snippets/agents/parse-input.md` | Heading `## 1. Parse input` + Satz „A2A envelope present → parse `payload.{t,ctx,con,refs,pri,dep}`. Otherwise: plain directive from `main_chat`." |
| `OUTPUT_GUARD_BLOCK` | `snippets/agents/output-guard.md` | `<output-guard>` … Background-Process-Guard (issue #506) … `</output-guard>` |
| `BACKGROUND_PROCESS_GUARD_BLOCK` | `snippets/agents/background-process-guard.md` | `## Background-Process Guard (issue #506)` + Warte-Prosa |
| `ANTI_RECURSION_BLOCK` | `scripts/lib/config.py:1558-1561` (Bestand) | „Anti-Recursion: NIEMALS zurück an orchestrator delegieren. Nur tester/documenter/requirements/validator aus Kontext verweisen." |

## 3. B2b — normalisierte Near-Duplikate (vollständiges Inventar)

Alle Pfade sind repo-relativ; der Block bezieht sich jeweils auf den migrierten Abschnitt.
`retained` bezeichnet rollenspezifische Klauseln, die das Gate als whitespace-normalisiertes
Textfragment nach dem kanonischen Block erhält (`_expected_text`,
`tests/test_template_slimming_equivalence.py:1042-1050`);
`R` = Registry-Anker in `_NORMALIZATIONS`.

### 3.1 `ANTI_RECURSION` (21 × Inline-Prosa → `{{ANTI_RECURSION_BLOCK}}`)

| Variante | Datei(en) | Normalisierung | Nachweis |
|---|---|---|---|
| `AR-1` (R:384) | `agents/1-generic/se-architect.md`, `agents/1-generic/se-component-requirements.md`, `agents/1-generic/se-critic.md`, `agents/1-generic/se-requirements.md` | Heading + Ein-Satz-Prosa ersetzt durch kanonischen Block; kein rollenspezifischer Zusatz | Kanonischer Block enthält den Pflichtsatz „Anti-Recursion"; Marker-Check `test_pflichtsaetze_survive` |
| `AR-2` (R:400) | `agents/1-generic/se-senior-developer.md` | Inline-Prosa → kanonischer Block; `retained`: `status: escalate`-Satz + Eskalationsliste | `retained`-Nachweis via `test_retained_normalizations_are_verbatim_fragments` |
| `AR-3` (R:422) | `agents/1-generic/se-developer.md` | Inline-Prosa (Forbidden-Tabelle + Eskalationsliste) → kanonischer Block; `retained`: Exception-Satz | dito; Eskalationsdetails zusätzlich rollenintern (`agents/1-generic/se-developer.md:93,108,121-138`) |
| `AR-4` (R:455) | `agents/1-generic/se-junior-developer.md` | Inline-Prosa (Tabelle + Liste) → kanonischer Block; `retained`: Exception-Satz | dito; Eskalationsdetails rollenintern (`agents/1-generic/se-junior-developer.md:92,119-127`) |
| `AR-5` (R:488) | `agents/1-generic/se-integration-and-test-manager.md`, `agents/1-generic/se-interface-mgr.md`, `agents/1-generic/se-termination.md`, `agents/1-generic/se-test-engineer.md`, `agents/1-generic/se-testreviewer.md` | Inline-Prosa → kanonischer Block; `retained`: „Andere Worker-Rolle nötig …"-Satz | dito |
| `AR-6` (R:517) | `agents/1-generic/se-validator.md`, `agents/1-generic/se-verifier.md` | Inline-Prosa → kanonischer Block; `retained`: Ausnahme-Satz | dito |
| `AR-K1` (R:539) | `agents/1-generic/knowledge-curator.md` | Inline-Prosa (Heading + Verboten + Ausnahme) → kanonischer Block | Pflichtsatz „Anti-Recursion" via Kanonblock; Ausnahme-Inhalt rollenintern erhalten (`agents/1-generic/knowledge-curator.md:47-50,71,76-77`) |
| `AR-K2` (R:558) | `agents/1-generic/knowledge-gardener.md` | Inline-Prosa → kanonischer Block | Ausnahme-Inhalt rollenintern (`agents/1-generic/knowledge-gardener.md:17,43,49,58`) |
| `AR-K3` (R:573) | `agents/1-generic/knowledge-indexer.md` | Inline-Prosa → kanonischer Block | Delegationsauftrag rollenintern (`agents/1-generic/knowledge-indexer.md:99`) |
| `AR-K4` (R:585) | `agents/1-generic/knowledge-ingestor.md` | Inline-Prosa → kanonischer Block | Delegationsauftrag rollenintern (`agents/1-generic/knowledge-ingestor.md:56,63,105,112`) |
| `AR-K5` (R:600) | `agents/1-generic/knowledge-linter.md` | Inline-Prosa → kanonischer Block | Findings-Weitergabe rollenintern (`agents/1-generic/knowledge-linter.md:35-49,60`) |
| `AR-K6` (R:615) | `agents/1-generic/knowledge-migrator.md` | Inline-Prosa → kanonischer Block | Phasen-Delegation rollenintern (`agents/1-generic/knowledge-migrator.md:67-69`) |
| `AR-K7` (R:630) | `agents/1-generic/knowledge-querier.md` | Inline-Prosa → kanonischer Block | File-Back-Delegation rollenintern (`agents/1-generic/knowledge-querier.md:36-38`) |

Gate-Nachweis für alle AR-Varianten: `test_golden_equivalence_and_normalization_marking`
(Golden + Normalisierung-Attribution), `test_migrated_templates_have_no_inline_variant_regions`
(0 verbleibende Inline-Regionen), `test_migrated_templates_render_canonical_blocks`
(Kanonblock im Render).

### 3.2 `PARSE_INPUT` (normalisierte Varianten)

| Variante | Datei(en) | Normalisierung | Nachweis |
|---|---|---|---|
| `PI-BLANK` (R:659) | `agents/1-generic/code-reviewer.md`, `agents/1-generic/concept-architect.md`, `agents/1-generic/concept-reviewer.md`, `agents/1-generic/concept-specifier.md`, `agents/1-generic/documenter.md`, `agents/1-generic/e2e-tester.md`, `agents/1-generic/export-manager.md`, `agents/1-generic/feedback.md`, `agents/1-generic/meta-feedback.md`, `agents/1-generic/requirements.md`, `agents/1-generic/security-auditor.md`, `agents/1-generic/test-executor.md`, `agents/1-generic/tester.md`, `agents/2-platform/homeassistant-documenter.md` | Leerzeile zwischen Heading und Satz entfällt (Kanonblock ohne Leerzeile) | Kanonsatz identisch, nur Blank-Line normalisiert; `test_golden_equivalence_and_normalization_marking` |
| `PI-TAIL-BATCH` (R:716) | `agents/1-generic/junior-developer.md` | Kanonblock + `retained`: `batch: true`-Klausel | `test_retained_normalizations_are_verbatim_fragments` |
| `PI-TAIL-ESC` (R:731) | `agents/1-generic/senior-developer.md` | Kanonblock + `retained`: Eskalations-`ctx.findings`-Klausel | dito |
| `PI-TAIL-CONTRACTS-DB` (R:746) | `agents/1-generic/database-engineer.md` | Kanonblock + `retained`: Input-Contract-Klausel | dito |
| `PI-TAIL-CONTRACTS-REF` (R:761) | `agents/1-generic/refactoring-specialist.md` | Kanonblock + `retained`: Input-Contract-Klausel | dito |
| `PI-BLANK-SOURCES` (R:776) | `agents/1-generic/planner.md` | Leerzeile entfällt + Kanonblock + `retained`: „Accepted sources"-Klausel | `test_retained_normalizations_are_verbatim_fragments` |
| `PI-PASS-ORCH` (R:688) | `agents/1-generic/ai-security-guardian.md`, `agents/1-generic/app-lifecycle-governor.md`, `agents/1-generic/prompt-governor.md` | **Passthrough:** bewusst inline belassen (Satz endet auf ` / orchestrator.`, eine Trennung würde ein Fragment verwaisen) | `passthrough=True`, `_expected_text` = Identität; kein Inline-Region-Check für `PARSE_INPUT` |
| `PI-PASS-DEP` (R:703) | `agents/1-generic/dependency-auditor.md` | **Passthrough:** bewusst inline belassen (Direkt-Delegations-Zusatz) | dito |

### 3.3 `OUTPUT_GUARD` (normalisierte Varianten)

| Variante | Datei(en) | Normalisierung | Nachweis |
|---|---|---|---|
| `OG-TAIL-DOCKER` (R:792) | `agents/1-generic/devops-engineer.md`, `agents/1-generic/docker.md`, `agents/1-generic/e2e-tester.md`, `agents/1-generic/tester.md` | Kanon-`<output-guard>` + `retained`: rollenspezifisches Docker-Wait-Beispiel | `test_retained_normalizations_are_verbatim_fragments`; Marker `<output-guard>`/`</output-guard>` in `test_pflichtsaetze_survive` |
| `OG-TAIL-DEV` (R:833) | `agents/1-generic/developer.md` | Kanon-`<output-guard>` + `retained`: Polling-Beispiel | dito |
| `OG-PASS-PLANNER` (R:879) | `agents/1-generic/planner.md` | **Passthrough:** Silent-Truncation-Guard (issue #514) bewusst inline belassen (nicht der kanonische Block) | `passthrough=True`, `_expected_text` = Identität |
| `OG-PASS-EXPLORER` (R:904) | `agents/1-generic/explorer.md` | **Passthrough:** Silent-Truncation-Guard inline | dito |
| `OG-PASS-CODE-REVIEWER` (R:925) | `agents/1-generic/code-reviewer.md` | **Passthrough:** Silent-Truncation-Guard inline | dito |

## 4. B2a — text-identische Near-Duplikate im aktuellen LF-Korpus

Diese Vorkommen entsprachen vor der Migration dem kanonischen Snippet-Text mit LF-Zeilenenden;
die Referenzierung ist eine Identitätstransformation. Der generierte UTF-8-Text bleibt im
aktuellen LF-Korpus identisch zur Golden-Baseline; daraus wird keine Raw-Byte-Identität für
andere Eingabe-Zeilenenden abgeleitet. Sie werden über die Terminierungs-Varianten
`OG-CANON` (R:647) und `PI-CANON` (R:653) mit `inline="__CANONICAL__"` klassifiziert.

| Variante | Anzahl | Datei-Set (Registry) |
|---|---|---|
| `OG-CANON` | 43 | `_OUTPUT_GUARD_MIGRATED` ohne die fünf `OG-TAIL-*`-Pfade |
| `PI-CANON` | 20 | `_PARSE_INPUT_MIGRATED` ohne die `PI-BLANK`- und `PI-TAIL-*`-Pfade |

**`OG-CANON` (43 Dateien):** `agents/1-generic/se-architect.md`, `agents/1-generic/se-component-requirements.md`,
`agents/1-generic/se-critic.md`, `agents/1-generic/se-developer.md`, `agents/1-generic/se-junior-developer.md`, `agents/1-generic/se-requirements.md`,
`agents/1-generic/se-senior-developer.md`, `agents/1-generic/se-test-engineer.md`, `agents/1-generic/se-validator.md`, `agents/1-generic/se-verifier.md`,
`agents/1-generic/knowledge-migrator.md`, `agents/1-generic/accessibility-specialist.md`, `agents/1-generic/agent-meta-manager.md`,
`agents/1-generic/ai-security-guardian.md`, `agents/1-generic/api-specialist.md`, `agents/1-generic/app-lifecycle-governor.md`,
`agents/1-generic/bug-feature-analyzer.md`, `agents/1-generic/data-engineer.md`, `agents/1-generic/database-engineer.md`, `agents/1-generic/dependency-auditor.md`,
`agents/1-generic/design-system-architect.md`, `agents/1-generic/export-manager.md`, `agents/1-generic/feedback.md`,
`agents/1-generic/frontend-component-engineer.md`, `agents/1-generic/git.md`, `agents/1-generic/incident-responder.md`, `agents/1-generic/junior-developer.md`,
`agents/1-generic/log-analyzer.md`, `agents/1-generic/mammouth-expert.md`, `agents/1-generic/meta-feedback.md`, `agents/1-generic/openscad-developer.md`,
`agents/1-generic/performance-optimizer.md`, `agents/1-generic/principal-developer.md`, `agents/1-generic/prompt-engineer.md`, `agents/1-generic/prompt-governor.md`,
`agents/1-generic/provider-expert.md`, `agents/1-generic/refactoring-specialist.md`, `agents/1-generic/release.md`, `agents/1-generic/security-auditor.md`,
`agents/1-generic/senior-developer.md`, `agents/1-generic/sre-engineer.md`, `agents/1-generic/ui-ux-designer.md`, `agents/1-generic/validator.md`.

**`PI-CANON` (20 Dateien):** `agents/1-generic/_reference-agent.md`, `agents/1-generic/accessibility-specialist.md`,
`agents/1-generic/api-specialist.md`, `agents/1-generic/data-engineer.md`, `agents/1-generic/design-system-architect.md`, `agents/1-generic/developer.md`,
`agents/1-generic/devops-engineer.md`, `agents/1-generic/docker.md`, `agents/1-generic/explorer.md`, `agents/1-generic/frontend-component-engineer.md`, `agents/1-generic/git.md`,
`agents/1-generic/openscad-developer.md`, `agents/1-generic/performance-optimizer.md`, `agents/1-generic/product-manager.md`, `agents/1-generic/sre-engineer.md`,
`agents/1-generic/technical-writer.md`, `agents/1-generic/ui-ux-designer.md`, `agents/2-platform/agent-meta-developer.md`,
`agents/2-platform/homeassistant-developer.md`, `agents/2-platform/sharkord-developer.md`.

> **Plattform-Overrides (Task 15):** Die Inline-Blöcke der 2-platform-Dateien liegen in
> YAML-Block-Skalaren (`patches[].content: |`). Nach dem YAML-Decoding ist ihr Text
> LF-text-identisch zum Kanon → `PI-CANON` (B2a); es ist **keine** B2b-Normalisierung nötig.
> `agents/2-platform/homeassistant-documenter.md` trägt dagegen eine Leerzeile und ist deshalb
> als `PI-BLANK` (B2b) registriert. Der Vergleich entfernt die YAML-Einrückung über
> `_dedent` (`tests/test_template_slimming_equivalence.py:271-273`), ohne den Inhalt zu ändern.

## 5. Pflichtsatz-Nachweis (kein verlorener Pflichtsatz)

Die B2b-Anforderung verlangt den Erhalt der vier Pflichtbereiche. `test_pflichtsaetze_survive`
(`tests/test_template_slimming_equivalence.py:1198-1208`) prüft Marker, die in der Golden-Baseline
vorhanden sind, gegen den neu gerenderten Output; `_PFLICHTSATZ_MARKERS` (R:1190-1195) definiert:

| Pflichtbereich | Marker | Erhalt über |
|---|---|---|
| Input-Parsing | `Parse input` | `PARSE_INPUT_BLOCK` (identisch bzw. nur Blank-Line-normalisiert; Tails retained) |
| Output-Guard | `<output-guard>`, `</output-guard>` | `OUTPUT_GUARD_BLOCK` (identisch bzw. Kanonblock + retained Beispiel) |
| Handoff-Format | `Handoff` | `A2A_HANDOFF_BLOCK` (`config.py:1551-1557`) — von keiner Slimming-Migration berührt |
| Anti-Recursion | `Anti-Recursion` | `ANTI_RECURSION_BLOCK` (`config.py:1558-1561`) |

Zusätzliche Nachweise im Gate:

- `test_golden_equivalence_and_normalization_marking` — jeder normalisierte Block wird genau einer
  deklarierten Variante zugeordnet; der normalisierte Render ist identisch zum aktuellen Render.
- `test_retained_normalizations_are_verbatim_fragments` — jede `retained`-Klausel ist ein
  whitespace-normalisiertes Textfragment des Vor-Migrations-Textes (kein erfundenes Retainment).
- `test_migrated_templates_render_canonical_blocks` — im Render steht der kanonische Blocktext,
  kein unersetztes `{{*_BLOCK}}`-Platzhalter.

**Feststellung:** Kein Pflichtsatz der vier Bereiche ist verloren. Rollenspezifische
Eskalations-/Delegationsdetails, die nicht als `retained`-Klausel übernommen wurden, sind in der
jeweils zugehörigen Rollen-Sektion weiterhin dokumentiert (Nachweise in den Tabellen 3.1–3.3).

## 6. B3 — Snippet-Kopiervertrag (`*_SNIPPETS_PATH`)

Es gibt **zwei getrennte Snippet-Mechanismen** (Spec §1.7), die nicht verwechselt werden dürfen:

1. **Inlining-Pfad (`*_BLOCK`):** `scripts/lib/config.py:1858-1935` (`_build_snippet_variables`)
   lädt die Block-Snippet-Dateien aus `snippets/agents/` über `_load_block_snippet`
   (`config.py:1839-1855`). Angewandter Transform: führendes YAML-Frontmatter strippen,
   Zeilenenden auf `\n` normalisieren, `strip("\n")`. Verdrahtung in `build_variables`
   (`config.py:2041`).
2. **Kopierpfad (`*_SNIPPETS_PATH`):** `scripts/lib/context.py:2183-2250`
   (`sync_snippets_for_provider`) sammelt alle Variablenwerte, deren Key auf `_SNIPPETS_PATH`
   endet und nicht leer ist, löscht nicht mehr referenzierte Zieldateien und kopiert genau die
   referenzierten Dateien als UTF-8-Text (Frontmatter bleibt erhalten) nach
   `<project_root>/<snippets_dir>/<rel_path>`. `read_text()` nutzt Universal-Newline-Decoding:
   CRLF/CR werden dabei zu `\n` normalisiert; der Vertrag gilt nicht als Raw-Byte-Garantie.

Verankerung in diesem Repo: `.meta-config/project.yaml:251-252` setzt
`TESTER_SNIPPETS_PATH: ''` und `DEVELOPER_SNIPPETS_PATH: ''` — die Kopiermenge ist hier leer.

Der B3-Vertrag wird durch `tests/test_snippet_copy_contract.py` gegen die realen Funktionen
gepinnt:

- (a) kopierte Dateimenge == Menge der referenzierten `*_SNIPPETS_PATH`-Snippets; nicht
  referenzierte Dateien (inkl. Block-Snippet-Dateien) werden nicht kopiert und veraltete
  Zieldateien werden entfernt;
- (b) der Inlining-Pfad entfernt Frontmatter/Whitespace-Rauschen, der Kopierpfad behält den
  UTF-8-Text und das Frontmatter; CRLF/CR-Eingaben werden beim `read_text()` zu `\n`
  normalisiert (keine Raw-Byte-Garantie);
- (c) beide Pfade sind deterministisch über zwei Invokationen.

## 7. Re-Planning-Hinweis

Dieses Manifest ist der Gate-Nachweis für AC B2b und die Vertragsreferenz für AC B3. Es wird
durch Task 17 (Abschluss-Verifikation) konsumiert. Ändert eine spätere Migration eine B2b-Variante,
muss zuerst `_NORMALIZATIONS` in `tests/test_template_slimming_equivalence.py` und danach dieses
Manifest aktualisiert werden; ein undeklariertes Near-Duplikat lässt das Äquivalenz-Gate
fehlschlagen.

## 8. Re-Baseline der Golden-Baseline (außerhalb der Slimming-Migration)

Dieser Abschnitt ist der von der Update-Regel der Golden-Baseline verlangte Manifest-Eintrag für
eine **bewusste Baseline-Aktualisierung** (Vertrag: `tests/fixtures/slimming-golden/README.md:73-77`;
Risiko R8: `docs/specs/2026-09-19-dynamic-routing-template-slimming.md:689`). Er ist **keine**
B2b-Near-Duplikat-Variante und erscheint daher bewusst nicht in den Inventar-Tabellen 3.1–3.3:
Es wurde kein Block migriert, sondern eine eingefrorene Fixture an eine bereits stattgefundene,
vorgelagerte Template-Änderung nachgezogen.

> **Autor:** Doku-Agent `documenter` (Orchestrator-Delegation); namentliche Autorschaft wird hier
> nicht geführt — Nachweis ist der Commit `3874c74b`.
> **Commit:** `3874c74b` — `fix(tests): re-baseline effort-estimator golden fixture to 1.4.0`
> (nur `tests/fixtures/slimming-golden/effort-estimator.md`, +39/−4 laut Commit-Stat — Diff-Stat in
> dieser Doku-Runde nicht neu gemessen; nachgeholt, weil `docs/` zum Commit-Zeitpunkt gesperrt war).
> **Datum:** 2026-09-26 (Commit-Datum von `3874c74b`; belegt über den Reflog-Eintrag
> `.git/logs/refs/heads/feat/dynamic-routing-template-slimming:37`, Zeitstempel `1790375112 +0200`,
> aufgelöst zu 2026-09-26 00:25:12 +0200).
> **Primärbeleg:** CI zu PR #833 auf Head-SHA `3874c74b` (alle 5 Checks grün, siehe 8.5). Der lokale
> Wegwerf-Klon `/var/tmp/opencode/ci833-verify2` ist nur reproduzierbarer Zusatz und trägt allein
> nicht als Nachweis, weil er flüchtig und maschinenlokal ist und nicht Teil dieses Repos ist.
> **Voraussetzung für 8.2/8.5/8.7:** Diese Abschnitte setzen den Merge-Zustand voraus, der lokal erst
> nach `git fetch origin main` auflösbar ist, solange `2e8b1708` fehlt (rc 128; Ref-Lage siehe 8.1).
> **Gegenstand:** `tests/fixtures/slimming-golden/effort-estimator.md` — 1 von **58** eingefrorenen
> Golden-Fixtures (Aktive-Rollen-Menge, `tests/fixtures/slimming-golden/README.md:36-38`).
> **Klassifikation:** **Baseline-Update nach Update-Regel**
> (`tests/fixtures/slimming-golden/README.md:73-77`) — **kein B2a-/B2b-Fall**; siehe 8.2 und 8.7.

### 8.1 Auslöser

Base-Commit `2e8b1708` (`feat(agents): estimation discipline for effort-estimator (#829) (#830)`)
hob `agents/1-generic/effort-estimator.md` von `version: "1.3.0"` auf `version: "1.4.0"`
(+37/−3). Inhaltliche Änderungen — **vollständig, 7 Deltas**:

1. Frontmatter-`description` **umformuliert** (… „based on task type and LLM capabilities **— with named
   assumptions, lead time and slack instead of a bare point value.**").
2. Versionsfeld `1.3.0` → `1.4.0`.
3. Neuer Abschnitt `## 7. Provision for the unknowns (audit planning register)`.
4. **Umnummerierung** des bestehenden Output-Abschnitts `## 7. Output` → `## 8. Output`. Das ist
   **kein neuer Abschnitt** — der Abschnitt bestand bereits und rutscht durch den eingefügten
   Abschnitt 3 um eine Nummer.
5. Neuer `## Provenance`-Block im `<context>` (hinter `## Task Type Catalog`).
6. Zusätzliche Zeile `Unknowns & Assumptions: [named assumptions, lead time, slack, unproven parts]`
   im Output-Block.
7. Drei zusätzliche `<constraints>`-Klauseln (Planungs-Reserve, Scope-Change, Qualitäts-/Termin-Konflikt).

Die Golden-Fixture blieb auf 1.3.0 (eingefrorener Stand nach Block A, vor Block B,
`tests/fixtures/slimming-golden/README.md:16-20`). Der Versionssprung ist **orthogonal** zur
Slimming-Änderung: er betrifft den Inhalt der Rolle, nicht die Block-Extraktion.

> **Reproduktionsfalle — nicht „Commit fehlt", sondern veralteter lokaler Ref:** Sowohl der lokale
> `main`-Ref als auch der Remote-Tracking-Ref `origin/main` stehen auf `deb115aa` und sind gegenüber
> dem echten Upstream-`main` (`2e8b1708`) **veraltet**. Deshalb scheitern sowohl
> `git cat-file -t 2e8b1708` als auch `git fetch origin 2e8b1708`, obwohl der Commit upstream
> existiert (per `git ls-remote` verifiziert; Subject wortgleich zu `2e8b1708`). Der inhaltsgleiche
> Parent vor dem Squash ist `d45b5bfb` auf `origin/feat/audit-effort-estimator-planning` (dieser Ref
> ist lokal vorhanden). **Folge:** der Merge-Zustand ist lokal nicht reproduzierbar; der Nachweis
> erfolgt über CI bzw. nach `git fetch origin main`.

### 8.2 Mechanismus des Fehlschlags

`effort-estimator` steht in **keiner** Registry des Äquivalenz-Moduls (0 Treffer in
`tests/test_template_slimming_equivalence.py`). Damit greift der Byte-Identitäts-Zweig für
nicht migrierte Rollen (`tests/test_template_slimming_equivalence.py:1114-1126`, Assertion
`:1148`): `golden != current` wird als „unexpected diff on an unmigrated role" gewertet.

Eine Markierung als migriert (B2b) war **strukturell nicht möglich**: `_LOCATORS`
(`tests/test_template_slimming_equivalence.py:348-353`) und `_normalize()`
(`tests/test_template_slimming_equivalence.py:1073-1097`) arbeiten ausschließlich auf den vier
Block-Kinds aus `_KIND_CANONICAL_VAR` (`tests/test_template_slimming_equivalence.py:245-250`)
(`ANTI_RECURSION`, `OUTPUT_GUARD`, `BACKGROUND_PROCESS_GUARD`, `PARSE_INPUT`). Sie erkennen
Sektionen anhand von Heading-/Tag-Regexen, **keine Versionsstrings** — ein 1.3.0→1.4.0-Delta
liegt außerhalb des Modells. Eine erfundene `retained`-Klausel oder eine neue Variante hätte den
Vertrag verletzt statt eingehalten.

### 8.3 Gewählte Fix-Route und Vertragsbeleg

Bewusste, über den **echten Sync-Pfad** erzeugte Re-Baseline nach dem Verfahrensvertrag
(`tests/fixtures/slimming-golden/README.md:22-41`), ausdrücklich **nicht** als „incidental
re-render" (`:18-20`) und **nicht** als Handedit. Die Optionen waren damit:

| Option | Bewertung |
|---|---|
| Golden-Fixture auf 1.3.0 belassen | Nicht möglich — Template `2e8b1708` ist Vorgänger im Merge-Ref, der Render ist 1.4.0 |
| Rolle künstlich migrieren / B2b-Variante erfinden | Vertragsbruch (8.2) |
| `{{AGENT_META_DATE}}`-Sonderregel ausweiten | Nicht anwendbar — der Platzhalter rendert ausschließlich in `agent-meta-manager.md` (`:57-71`) |
| **Bewusste Re-Baseline + Manifest-Eintrag** | **Gewählt** — genau der in R8 und in der Update-Regel vorgesehene Weg |

### 8.4 Nachweis der Herkunft (keine Handpflege)

- sha256 der Fixture identisch in Arbeitsbaum, Verify-Klon und frischem Sync-Render:
  `936c2b78556d901fa25129edd094e2d24eef629dc2b5cbdde52ffda00337b8b5`.
- **Determinismus-Nachweis (Zweitrender) — durchgeführt.** Der Verfahrensvertrag
  `tests/fixtures/slimming-golden/README.md:43-55` schreibt einen Vergleich zweier Render-Läufe vor
  (`diff -r` über zwei Zielverzeichnisse, rc 0). Umgesetzt als zwei frische Sync-Läufe des
  **echten Sync-Pfads** in zwei getrennte temporäre Zielverzeichnisse, anschließend `cmp` über den
  gesamten Zielbaum: **byte-identisch, `sync` rc 0**. (Vergleichsform `cmp` je Datei statt `diff -r`
  — gleiche Byte-Aussage, siehe Verfahrensfundstelle oben.)
- Die Fixture enthält **keinen** Absolutpfad, **keinen** Hostnamen, **keinen** Commit-SHA und
  **kein** `{{AGENT_META_DATE}}` (geprüft über das gesamte Verzeichnis
  `tests/fixtures/slimming-golden/`; der einzige Treffer liegt in dessen `README.md`).
- Frontmatter konsistent: `version: 1.4.0` und `generated-from: 1-generic/effort-estimator.md@1.4.0`
  (`tests/fixtures/slimming-golden/effort-estimator.md:3` und `:13`).

### 8.5 Verifikation

Verifikationslauf im **Merge-Zustand** (base + head, Wegwerf-Klon `/var/tmp/opencode/ci833-verify2`
auf dem Merge-Commit, identisch zum CI-Ref):

| Prüfung | Ergebnis |
|---|---|
| `pytest tests/test_template_slimming_equivalence.py -q -rs` | **8 passed**, rc 0 |
| `pytest tests/ -q -rs` (Merge-Klon) | **3118 passed, 0 failed, 18 skipped**, rc 0 — *in der Fix-Runde gemessen, in der Verifikationsrunde **nicht** mit voller Suite wiederholt; umgebungsabhängig* (lokal können Admin-UI-/Django-Setup-Fehler hinzukommen, s. u.) |
| `python scripts/sync.py --validate` | rc 0 |
| `python scripts/sync.py --check` | rc 0 |
| CI (PR #833, Head `3874c74b`) | alle 5 Checks grün |

> **Bewusste Abweichung auf dem ungemergten Branch-Head:** Auf dem ungemergten Head ist das Gate
> **rot** (inverse Diff: Golden 1.4.0 gegen Render 1.3.0). Das ist kein Regression, sondern
> notwendige Konsequenz: `2e8b1708` ist Base des PRs und im lokalen Arbeitsbaum nicht enthalten —
> `agents/1-generic/effort-estimator.md:3` steht dort weiterhin auf `version: "1.3.0"`. Eine
> Golden-Datei kann nicht 1.3.0 und 1.4.0 gleichzeitig matchen. Da die CI auf dem Merge-Ref rechnet,
> ist der Merge-Zustand maßgeblich (zur veralteten Ref-Lage siehe 8.1).
>
> **Grenze der Aussage (module-genau, nicht suite-weit):** Im B2-Gate-Modul
> `tests/test_template_slimming_equivalence.py` zeigt ein lokaler Lauf ohne Merge des Base-Branches
> **genau diesen einen** Fehlschlag: `::test_golden_equivalence_and_normalization_marking` (`:1148`),
> gemessen 1 failed / 7 passed. Für `pytest tests/` gilt diese Aussage **nicht**: dort kommen
> umgebungsbedingte Admin-UI-/Django-Setup-Fehler hinzu (lokal gemessen 1 failed / 3131 passed /
> 35 errors) — unabhängig von dieser Änderung und ohne Bezug zum Golden-Baseline-Vertrag.
>
> **Die suite-weiten Summen der beiden Läufe sind nicht gegeneinander zu rechnen:** Merge-Klon und
> lokaler Lauf sammeln **unterschiedliche Testkollektionen** (unterschiedliche Umgebung →
> unterschiedliche Collection-/Import-Fehler → verschiedene `passed`-Zahlen). Die Differenz ist damit
> kein Widerspruch zwischen zwei Messungen derselben Kollektion, sondern ein Umgebungsunterschied.

### 8.6 Bestandsaufnahme aller 58 Goldens

Vorsorge gegen weiteren Skew, vollständig über alle 58 Fixtures (Byte-Vergleich Fixture ↔ gerenderte
Rolle, Aufteilung nach `_MIGRATED_PATHS`, `tests/test_template_slimming_equivalence.py:235-239`).
**Zahlenbasis:** eigenständige Nachmessung des test-executors über alle 58 Fixtures; in dieser
Doku-Runde **nicht** erneut ausgeführt (kein Shell-Tool) — daher als Nachmessung gekennzeichnet, nicht
als frisch gemessen.

Es existieren **zwei verschiedene Partitionen**; die jeweilige Definition wird hier ausdrücklich
benannt, weil beide Zahlen jeweils „richtig", aber nur unter ihrer Definition sind:

**(a) Test-native — die Definition, die das Gate durchsetzt** (Zweig
`tests/test_template_slimming_equivalence.py:1114-1126`): hier gilt „byte-identisch" nur für Rollen
**außerhalb** von `_MIGRATED_PATHS`; migrierte Rollen werden über `_normalize()` (`:1073-1097`)
bewertet, nicht byteweise.

| Kategorie | Anzahl | Bedeutung |
|---|---|---|
| byte-identisch (unmigriert) | 11 | nicht in `_MIGRATED_PATHS`, Golden == Render |
| deklariert migriert | 47 | in `_MIGRATED_PATHS`, Abweichung wird von `_NORMALIZATIONS` absorbiert (3.1–3.3) |
| **echter Skew** | **0** | — |

`_MIGRATED_PATHS` umfasst 74 Pfade, davon **47 aktive Rollen** (Pfad- und Rollenmenge weichen ab,
weil die Registry auch nicht aktive Pfade enthält).

**(b) Raw-Byte — ohne Normalisierung** (Fixture-Text byteweise gegen den unnormalisierten Render):

| Kategorie | Anzahl | Bedeutung |
|---|---|---|
| byte-identisch zum Render | 32 | die 11 unmigrierten aus (a) plus 21 weitere Rollen, deren Delta die Normalisierung nicht berührt (11 + 21 = 32; die Aufteilung 11/21 ist aus der Differenz 32 − 11 abgeleitet, nicht separat gemessen) |
| raw-abweichend — **alle deklariert migriert** | 26 | werden von `_NORMALIZATIONS` absorbiert (3.1–3.3) |
| **echter Skew** | **0** | — |

**Stand nach dem Fix (Merge-Zustand, Post-Fix): (b) 32 / 26 / 0 — kein Skew**; in der
gate-durchgesetzten Definition (a) 11 / 47 / 0.

**Vorher-Zustand / Ausgangslage (Pre-Fix): 31 / 26 / 1.** Genau dieser eine Skew — `effort-estimator`,
Golden 1.4.0 gegen Render 1.3.0 im ungemergten Baum — war der **Anlass dieses Eintrags**; 31 = 32 −
`effort-estimator`, also dieselbe Zählweise wie (b). Er ist mit `3874c74b` behoben. Die 31/26/1 sind
ausdrücklich **Vorher-Stand**, nicht das Ergebnis des Fixes.

Zusätzlich bestätigt: **keine Orphan-Fixture** und **kein Golden ohne Render-Gegenstück** — jede der
58 Fixtures hat eine gerenderte Rolle, jede gerenderte Rolle eine Fixture.

`agent-meta-manager.md` — die **einzige** Fixture mit `{{AGENT_META_DATE}}`-Sonderfall
(`tests/fixtures/slimming-golden/README.md:57-71`) — ist durch den Fix **unverändert** geblieben: der
Re-Baseline-Commit `3874c74b` fasst ausschließlich `tests/fixtures/slimming-golden/effort-estimator.md`
an, die `{{AGENT_META_DATE}}`-Ausnahme wird also weder neu justiert noch erweitert (8.3).

### 8.7 Status B2a

B2a (Output-Äquivalenz gegen die eingefrorene Baseline) ist durch den Fix **wiederhergestellt**,
nicht abgeschwächt: das 1.3.0→1.4.0-Delta ist orthogonal zur Slimming-Änderung, und die Fixture
enthält nach dem Re-Baseline exakt den vom migrierten Template erzeugten Output. Die
Update-Regel ist erfüllt (Eintrag vorhanden), das Gate ist im Merge-Zustand grün.

Klarstellung zur Einordnung: dies ist eine **Statusaussage** über B2a, keine Klassifikation der
Änderung als B2a-Fall. Die Änderung selbst ist ein Baseline-Update nach Update-Regel (Kopf-Block
dieses Abschnitts, Vertrag `tests/fixtures/slimming-golden/README.md:73-77`), weil keine
Near-Duplikat-Variante und keine Block-Migration vorliegt (8.2).
