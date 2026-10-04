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

## 9. Re-Baseline der Golden-Baseline für `documenter` (PR #828)

Derselbe Verfahrensfall wie Abschnitt 8, angewandt auf die zweite der beiden nachträglich
eingefrorenen Golden-Fixtures. Die CI auf PR #828 (`feat/audit-documenter-workpapers`, Head
`b33541c4`) schlug ausschließlich hier fehl.

> **Autor:** Doku-Agent `documenter` (Orchestrator-Delegation); namentliche Autorschaft wird hier
> nicht geführt — Nachweis ist der Diff-Scope in 9.5.
> **Commit:** **noch nicht vorhanden** — die Re-Baseline wurde bewusst **nicht** committet; die
> Aufgabengrenze verbietet Git-Mutationen (`commit`/`add`/`push`). Der Diff-Scope ist daher
> **im Arbeitsbaum** gemessen (9.5) und wird erst mit dem Folge-Commit des `git`-Agenten zur
> SHA. Abweichend von Abschnitt 8 wird hier deshalb **keine** Commit-SHA zitiert; eine erfundene
> wäre eine Falschangabe.
> **Gegenstand:** `tests/fixtures/slimming-golden/documenter.md` — 1 von **58** eingefrorenen
> Golden-Fixtures (Aktive-Rollen-Menge, `tests/fixtures/slimming-golden/README.md:36-38`; neu
> gemessen: `len(_golden_roles()) == _GOLDEN_ROLE_COUNT == 58`).
> **Klassifikation:** **Baseline-Update nach Update-Regel**
> (`tests/fixtures/slimming-golden/README.md:73-77`) — **kein B2a-/B2b-Fall**; siehe 9.2 und 9.7.

### 9.1 Auslöser

Commit `a24c1ddf` (`feat(agents): working-paper discipline for documenter (#827)`, Basis von PR
#828) hob `agents/1-generic/documenter.md` von `version: "1.10.0"` auf `version: "1.11.0"`
(+37/−3). Der Folge-Commit `d087d0d8` (`fix(agents): sync homeassistant documenter override to
1.11.0`) zog den Plattform-Override `agents/2-platform/homeassistant-documenter.md` nach
(`version: 1.2.0`, `based-on: …@1.11.0`).

Inhaltliche Änderungen — **vollständig, 5 Deltas** (aus dem Render-Diff Fixture ↔ Ist-Render
gemessen, 9.5):

1. Frontmatter-`description` **umformuliert** (… „and session insights — **as artefacts that stand
   alone and stay traceable**.").
2. Versionsfeld `1.10.0` → `1.11.0` **sowie** das daraus abgeleitete
   `generated-from: 1-generic/documenter.md@1.11.0`.
3. Neuer Abschnitt `## 8. Documentation that stands alone (audit register)` (10 Aufzählungspunkte
   plus Einleitungssatz).
4. **Umnummerierung** des bestehenden Output-Abschnitts `## 8. Return` → `## 9. Return`. Das ist
   **kein neuer Abschnitt** — der Abschnitt bestand bereits und rutscht durch den eingefügten
   Abschnitt 3 um eine Nummer.
5. Neuer `## Provenance`-Block im `<context>` (beide Packt-Kurse mit Zeitmarken-Belegen) und drei
   zusätzliche `<constraints>`-Klauseln.

Wie in 8.1 ist der Versionssprung **orthogonal** zur Slimming-Änderung: er betrifft den Inhalt der
Rolle, nicht die Block-Extraktion.

### 9.2 Mechanismus des Fehlschlags

**Unterschied zu 8.2, der die Fehlschlagsursache bestimmt:** `effort-estimator` stand in
**keiner** Registry; `documenter` steht sehr wohl in `_MIGRATED_PATHS` (neu gemessen:
`'agents/1-generic/documenter.md' in _MIGRATED_PATHS` → `True`; Registry-Fundstelle
`tests/test_template_slimming_equivalence.py:195` in `_PARSE_INPUT_MIGRATED`). Die Rolle nimmt also
den **Normalisierungs-Zweig** des Gates, nicht den Byte-Identitäts-Zweig.

Damit greift `tests/test_template_slimming_equivalence.py:1114-1126` mit
`_normalize(golden, variables)` und der Assertion `:1148`, und die Fehlermeldung lautet folglich
nicht „unexpected diff on an unmigrated role" (8.2), sondern:

```
documenter (agents/1-generic/documenter.md): diff not attributable to declared normalizations
```

Die einzige für `documenter` deklarierte Normalisierung ist `PI-BLANK`
(Manifest-Tabelle 3.2, Fundstelle `tests/test_template_slimming_equivalence.py:675`); sie absorbiert
ausschließlich die Leerzeile zwischen `## 1. Parse input` und dem A2A-Satz. Die Deltas 1–5 aus
9.1 liegen außerhalb des Normalisierungsmodells: `_LOCATORS`
(`tests/test_template_slimming_equivalence.py:348-353`) und `_normalize()` (`:1073-1097`) arbeiten
ausschließlich auf den vier Block-Kinds aus `_KIND_CANONICAL_VAR`
(`tests/test_template_slimming_equivalence.py:245-250`) und erkennen Sektionen anhand von
Heading-/Tag-Regexen, **keine Versionsstrings und keine Abschnittslisten**. Eine erfundene
`retained`-Klausel oder eine neue Variante hätte den Vertrag verletzt statt eingehalten — gleiche
Lage wie 8.2, nur mit dem Unterschied, dass hier der Normalisierungs-Zweig betroffen ist.

### 9.3 Gewählte Fix-Route und Vertragsbeleg

Bewusste, über den **echten Sync-Pfad** erzeugte Re-Baseline nach dem Verfahrensvertrag
(`tests/fixtures/slimming-golden/README.md:22-41`), ausdrücklich **nicht** als „incidental
re-render" (`:18-20`) und **nicht** als Handedit.

| Option | Bewertung |
|---|---|
| Golden-Fixture auf 1.10.0 belassen | Nicht möglich — das Template steht auf 1.11.0, der Render ist 1.11.0 |
| Rolle künstlich migrieren / neue B2b-Variante für die Deltas 1–5 erfinden | Vertragsbruch (9.2) |
| `{{AGENT_META_DATE}}`-Sonderregel ausweiten | Nicht anwendbar — der Platzhalter rendert ausschließlich in `agent-meta-manager.md` (`:57-71`) |
| **Bewusste Re-Baseline + Manifest-Eintrag** | **Gewählt** — genau der in R8 und in der Update-Regel vorgesehene Weg |

**Grenze des Fixes (bewusst eingehalten):** es wurde **ausschließlich diese eine** Fixture
angefasst. Die beiden Sync-Läufe rendern alle 58 Rollen, aber kopiert wurde nur
`documenter.md`; ein Bulk-Kopieren des gesamten Zielbaums hätte die 57 anderen eingefrorenen
Fixtures verschoben und das Gate damit stillschweigend ausgehebelt. Nachweis über den
Diff-Scope in 9.5.

### 9.4 Nachweis der Herkunft (keine Handpflege)

- **Erzeugung über den realen Sync-Pfad**, wörtlich der Verfahrensvertrag
  (`tests/fixtures/slimming-golden/README.md:29-31`):

  ```bash
  mkdir -p .tmp/slimming-golden-gen
  AGENT_META_TEST_REPO="$PWD/.tmp/slimming-golden-gen" python3 scripts/sync.py --validate
  ```

  `sync --validate` rc `0` (361 Aktionen, 41 übersprungen, 2 Warnungen — vorbestehend und
  unabhängig von dieser Änderung).
- sha256 der Fixture identisch mit dem Sync-Render: Kopie per `cp` aus
  `.tmp/slimming-golden-gen/.claude/agents/documenter.md`, danach `cmp` rc `0`, sha256
  `4d4ceb3567b23631900b0cbfa2c5243b2f6cb09a14dd27dd448ddcfc57cfe38d` — in beiden Render-Verzeichnissen
  und in der Fixture identisch.
- **Determinismus-Nachweis (Zweitrender) — durchgeführt.** Wie in 8.4 über zwei getrennte
  temporäre Zielverzeichnisse, anschließend der Vergleich aus
  `tests/fixtures/slimming-golden/README.md:50`:

  ```bash
  mkdir -p .tmp/slimming-golden-gen2
  AGENT_META_TEST_REPO="$PWD/.tmp/slimming-golden-gen2" python3 scripts/sync.py --validate
  diff -r .tmp/slimming-golden-gen/.claude/agents .tmp/slimming-golden-gen2/.claude/agents
  ```

  Ergebnis: **`diff -r` rc `0`** — byte-identisch, null abweichende Dateien im gesamten Zielbaum.
  Damit ist zugleich belegt, dass der Render **kein** `{{AGENT_META_DATE}}`-Drift trägt (9.6).
- Die Fixture enthält **keinen** Absolutpfad, **keinen** Hostnamen, **keinen** Commit-SHA, **kein**
  `{{AGENT_META_DATE}}` und **keinen** unaufgelösten Platzhalter (je `grep -c` = 0).
- Frontmatter konsistent: `version: 1.11.0` und `generated-from: 1-generic/documenter.md@1.11.0`
  (`tests/fixtures/slimming-golden/documenter.md:3` und `:15`).

### 9.5 Verifikation

Verifikationslauf im Arbeitsbaum auf Head `b33541c4` (Branch `feat/audit-documenter-workpapers`):

| Prüfung | Ergebnis |
|---|---|
| `pytest tests/test_template_slimming_equivalence.py -q` | **8 passed**, rc 0 — inkl. `test_golden_equivalence_and_normalization_marking`, `test_no_declared_normalization_is_dead` und der `_GOLDEN_ROLE_COUNT`-Prüfung (`:1301-1302`, `58 == 58`, unverändert) |
| `python3 scripts/sync.py --validate` | rc `0` |
| Vorher-Zustand desselben Laufs | **1 failed, 7 passed** — `test_golden_equivalence_and_normalization_marking` (reproduziert vor dem Fix, identisch zur CI-Meldung auf py3.9/3.11/3.12) |
| `git status --short` | genau 2 Dateien: `tests/fixtures/slimming-golden/documenter.md`, `docs/plans/2026-09-19-dynamic-routing-template-slimming-diff-manifest.md` |
| Diff-Scope der Fixture | `tests/fixtures/slimming-golden/documenter.md \| 43 ++++++++++++++++----` → **+38/−5** |

> **Nicht durchgeführt und deshalb nicht behauptet:** ein voller `pytest tests/`-Lauf. Wie in 8.5
> vermerkt, sammelt ein solcher Lauf umgebungsabhängige Admin-UI-/Django-Collection-Fehler, die
> nichts mit dieser Änderung zu tun haben; die Aussage dieses Eintrags ist **module-genau** und
> deckt sich mit 8.5.

### 9.6 Bestandsaufnahme aller 58 Goldens

Vollständig über alle 58 Fixtures neu gemessen (Byte-Vergleich Fixture ↔ Render, Aufteilung nach
`_MIGRATED_PATHS`). Anders als in 8.6 wurde hier **frisch gemessen**, nicht übernommen: über das
`render_env`-Fixture des Äquivalenz-Moduls selbst (unwrapped aufgerufen, Renderziel ein
Wegwerf-Verzeichnis außerhalb des Repos), damit Rollen→Template-Zuordnung und Renderpfad die des
Gates sind und keine Nachbildung.

**(a) Test-native — die Definition, die das Gate durchsetzt:**

| Kategorie | Anzahl | Veränderung ggü. 8.6 |
|---|---|---|
| byte-identisch (unmigriert) | 11 | unverändert |
| deklariert migriert | 47 | unverändert |
| **echter Skew** | **0** | unverändert |

**(b) Raw-Byte — ohne Normalisierung:**

| Kategorie | Anzahl | Veränderung ggü. 8.6 |
|---|---|---|
| byte-identisch zum Render | 33 | **+1** |
| raw-abweichend | 25 | **−1** |
| **echter Skew** | **0** | unverändert |

Die Verschiebung 32 → 33 bzw. 26 → 25 ist **genau diese eine Rolle**: `documenter` ist nach der
Re-Baseline raw-byte-identisch, weil die neue Fixture den geslimmten `PARSE_INPUT`-Block bereits
**ohne** Leerzeile enthält und damit mit dem Ist-Render übereinstimmt. Vor der Re-Baseline stand
`documenter` in der 26er-Gruppe (allein der `PI-BLANK`-Delta); es ist inzwischen einer der 33
byte-identischen Render-Treffer, ohne dass eine `_NORMALIZATIONS`-Eintragung nötig war — die
deklarierte `PI-BLANK`-Normalisierung bleibt als **lebende** Deklaration erhalten und wird von
`test_no_declared_normalization_is_dead` weiterhin als nicht-tot bestätigt.

Zusätzlich bestätigt: **keine Orphan-Fixture** und **kein Golden ohne Render-Gegenstück** (58 = 58,
0 Orphans). `agent-meta-manager.md` — die einzige `{{AGENT_META_DATE}}`-Fixture
(`tests/fixtures/slimming-golden/README.md:57-71`) — ist **unverändert**; der `diff -r` über den
gesamten Zielbaum (9.4) zeigt keinen Datumsdrift. Die Scratch-Verzeichnisse
`.tmp/slimming-golden-gen{,2}` wurden nach der Messung entfernt.

### 9.7 Status B2a

B2a ist durch die Re-Baseline **wiederhergestellt**, nicht abgeschwächt: die Fixture enthält exakt
den vom aktuellen Template erzeugten Output, die Update-Regel ist erfüllt (dieser Eintrag), und
das Gate ist grün (9.5). Die Deltas aus 9.1 sind orthogonale Inhaltsänderungen der Rolle; an
`_MIGRATED_PATHS`, `_NORMALIZATIONS`, `_LOCATORS` oder `_GOLDEN_ROLE_COUNT` wurde **nichts**
angefasst — das Gate behält seine Zähne.

Klarstellung zur Einordnung wie in 8.7: dies ist eine **Statusaussage** über B2a, keine
Klassifikation der Änderung als B2a-Fall. Die Änderung selbst ist ein Baseline-Update nach
Update-Regel (Kopf-Block dieses Abschnitts, Vertrag
`tests/fixtures/slimming-golden/README.md:73-77`), weil keine Near-Duplikat-Variante für die
Deltas 1–5 und keine Block-Migration vorliegt (9.2).

## 10. Re-Baseline der Golden-Baseline für `dependency-auditor` (PR #825)

Derselbe Verfahrensfall wie Abschnitt 8 (effort-estimator) und Abschnitt 9 (documenter), angewandt
auf die dritte nachträglich veränderte aktive Rolle. Die CI auf PR #825
(`feat/audit-role-disciplines-cybersecurity`, Head `4816c3e6`) schlug ausschließlich hier fehl.

> **Autor:** Develop-Agent `senior-developer` (Orchestrator-Delegation); namentliche Autorschaft wird
> hier nicht geführt — Nachweis ist der Diff-Scope in 10.5.
> **Commit:** **noch nicht vorhanden** — die Re-Baseline wurde bewusst **nicht** committet; die
> Aufgabengrenze verbietet Git-Mutationen (`commit`/`add`/`push`). Der Diff-Scope ist daher
> **im Arbeitsbaum** gemessen (10.5) und wird erst mit dem Folge-Commit des `git`-Agenten zur
> SHA. Abweichend von Abschnitt 8 wird hier deshalb **keine** Commit-SHA zitiert; eine erfundene
> wäre eine Falschangabe.
> **Gegenstand:** `tests/fixtures/slimming-golden/dependency-auditor.md` — 1 von **58** eingefrorenen
> Golden-Fixtures (Aktive-Rollen-Menge, `tests/fixtures/slimming-golden/README.md:36-38`; neu
> gemessen: `len(_golden_roles()) == _GOLDEN_ROLE_COUNT == 58`).
> **Klassifikation:** **Baseline-Update nach Update-Regel**
> (`tests/fixtures/slimming-golden/README.md:73-77`) — **kein B2a-/B2b-Fall**; siehe 10.2 und 10.7.
> **Nicht Gegenstand:** `security-auditor` — siehe 10.2, Absatz „Nicht-aktive Rolle".

### 10.1 Auslöser

Der Inhalts-Commit `16b5adb6` (`feat(agents): cybersecurity-audit discipline for security roles`)
führte die Vendor-/Lieferanten-Assurance-Disziplin in die Security-Rollen ein. Der Folge-Commit
`4816c3e6` (`fix(agents): bump security role versions for audit discipline`) hob **ausschließlich die
Versionsfelder** in zwei Templates nach (2 Dateien, +2/−2): `agents/1-generic/dependency-auditor.md`
(`version: "1.6.0"` → `"1.7.0"`) und `agents/1-generic/security-auditor.md` (`"2.5.0"` → `"2.6.0"`).

Inhaltliche Änderungen an `dependency-auditor` — **vollständig, 5 Deltas** (aus dem Diff der Fixture
gemessen, 10.5):

1. Versionsfeld `1.6.0` → `1.7.0` **sowie** das daraus abgeleitete
   `generated-from: 1-generic/dependency-auditor.md@1.7.0`.
2. Neuer Workflow-Schritt `5. VENDOR` im ```-Block (Assurance-Evidenz für Vendor-/Cloud-Komponenten:
   SOC 2 Type 1 vs. Type 2, ISO/IEC 27001 Scope und Datum, PCI DSS; Nachfragen nach Zeitraum,
   Prüfer und Verwertung der Zertifizierung; Schwachstellen-Nachverfolgung; unveränderte
   Vendor-Defaults als Supply-Chain-Exposition).
3. **Umnummerierung** der bestehenden Schritte `5. FINDINGS` → `6. FINDINGS` und `6. HANDOFF` →
   `7. HANDOFF`. Das sind **keine neuen Schritte** — sie rutschen durch den eingefügten Schritt 2
   um eine Nummer.
4. Neuer Abschnitt `## 5. Vendor and service-provider evidence` (Einleitungssatz + 6 Aufzählungspunkte
   inkl. FP-Guard) mit **Umnummerierung** des bestehenden Abschnitts `## 5. Findings structure` →
   `## 6. Findings structure`.
5. Neuer `## Provenance`-Block im `<context>` (Packt-Kurs mit Zeitmarken-Belegen) **sowie** die neue
   Zeile `VENDOR_EVIDENCE_FINDINGS: <count>` im `<output>`-Vertrag.

Wie in 8.1 und 9.1 ist der Versionssprung **orthogonal** zur Slimming-Änderung: er betrifft den Inhalt
der Rolle, nicht die Block-Extraktion.

### 10.2 Mechanismus des Fehlschlags

**Wie in 9.2 ist `dependency-auditor` in `_MIGRATED_PATHS` enthalten** (neu gemessen:
`agents/1-generic/dependency-auditor.md` in der Menge → `True`; Fundstelle
`tests/test_template_slimming_equivalence.py:144`). Die Rolle nimmt also wie `documenter` den
**Normalisierungs-Zweig** des Gates, nicht den Byte-Identitäts-Zweig. Damit greift
`tests/test_template_slimming_equivalence.py:1114-1126` mit `_normalize(golden, variables)` und die
Assertion `:1148`; die Fehlermeldung lautet folglich:

```
dependency-auditor (agents/1-generic/dependency-auditor.md): diff not attributable to declared normalizations
```

Für `dependency-auditor` sind genau **zwei** Normalisierungen deklariert (aus der Attributions-Liste
des Fehlschlags): `OUTPUT_GUARD` → `OG-CANON` (B2a) und `PARSE_INPUT` → `PI-PASS-DEP` (B2b). Sie
absorbieren ausschließlich die Marker-Position des Output-Guards bzw. die A2A-Parse-Zeile. Die Deltas
1–5 aus 10.1 liegen außerhalb des Normalisierungsmodells: `_LOCATORS`
(`tests/test_template_slimming_equivalence.py:348-353`) und `_normalize()` (`:1073-1097`) arbeiten
ausschließlich auf den vier Block-Kinds aus `_KIND_CANONICAL_VAR`
(`tests/test_template_slimming_equivalence.py:245-250`) und erkennen Sektionen anhand von
Heading-/Tag-Regexen, **keine Versionsstrings, keine Schrittlisten und keine Abschnittslisten**. Eine
erfundene `retained`-Klausel oder eine neue Variante hätte den Vertrag verletzt statt eingehalten —
gleiche Lage wie 8.2 und 9.2, mit demselben Unterschied wie in 9.2: hier ist der
Normalisierungs-Zweig betroffen.

**Nicht-aktive Rolle `security-auditor` (ausdrücklich geprüft, kein Re-Baseline-Bedarf):**
`security-auditor` steht zwar ebenfalls in `_MIGRATED_PATHS`
(`tests/test_template_slimming_equivalence.py:169`), ist aber **keine aktive Rolle** dieser
Repo-Konfiguration. Neu gemessen:

- `security-auditor` steht **nicht** in der `roles:`-Whitelist `.meta-config/project.yaml`
  (59 Einträge, Zeilen 9–67; `dependency-auditor` steht in Zeile 60, `security-auditor` kommt
  **nicht** vor);
- es existiert **keine** Fixture `tests/fixtures/slimming-golden/security-auditor.md`;
- der Sync rendert **keine** `.claude/agents/security-auditor.md` — weder in Render 1 noch in
  Render 2.

Folge: das Gate iteriert über `_golden_roles()` (58 Rollen) und **`security-auditor` wird nie
besucht**; ein Re-Baseline ist für diese Rolle weder nötig noch möglich. Der Versionssprung auf
`2.6.0` in `agents/1-generic/security-auditor.md` hat daher **keine** Wirkung auf die
Golden-Baseline. Die Aufgabenstellung hatte hier eine Fehlannahme (Verwechslung von
`_MIGRATED_PATHS`-Mitgliedschaft mit Fixture-/Render-Präsenz); sie wurde vor dem Kopieren empirisch
korrigiert, und `security-auditor` wurde **nicht** angefasst.

### 10.3 Gewählte Fix-Route und Vertragsbeleg

Bewusste, über den **echten Sync-Pfad** erzeugte Re-Baseline nach dem Verfahrensvertrag
(`tests/fixtures/slimming-golden/README.md:22-41`), ausdrücklich **nicht** als „incidental
re-render" (`:18-20`) und **nicht** als Handedit.

| Option | Bewertung |
|---|---|
| Golden-Fixture auf 1.6.0 belassen | Nicht möglich — das Template steht auf 1.7.0, der Render ist 1.7.0 |
| Rolle künstlich migrieren / neue B2b-Variante für die Deltas 1–5 erfinden | Vertragsbruch (10.2) |
| `{{AGENT_META_DATE}}`-Sonderregel ausweiten | Nicht anwendbar — der Platzhalter rendert ausschließlich in `agent-meta-manager.md` (`:57-71`) |
| `security-auditor`-Fixture „vorsorglich" anlegen | Vertragsbruch — die Rolle ist nicht aktiv und wird nicht gerendert; eine erfundene Fixture würde `_GOLDEN_ROLE_COUNT == 58` und die Nicht-Orphan-Zählung brechen (10.2, 10.6) |
| **Bewusste Re-Baseline + Manifest-Eintrag** | **Gewählt** — genau der in R8, R9 und in der Update-Regel vorgesehene Weg |

**Grenze des Fixes (bewusst eingehalten):** es wurde **ausschließlich diese eine** Fixture
angfasst. Die beiden Sync-Läufe rendern alle 58 aktiven Rollen, aber kopiert wurde nur
`dependency-auditor.md`; ein Bulk-Kopieren des gesamten Zielbaums hätte die 57 anderen eingefrorenen
Fixtures verschoben und das Gate damit stillschweigend ausgehebelt. Nachweis über den
Diff-Scope in 10.5 und über die vollständige Bestandsaufnahme in 10.6.

### 10.4 Nachweis der Herkunft (keine Handpflege)

- **Erzeugung über den realen Sync-Pfad**, wörtlich der Verfahrensvertrag
  (`tests/fixtures/slimming-golden/README.md:29-31`):

  ```bash
  mkdir -p .tmp/slimming-golden-gen
  AGENT_META_TEST_REPO="$PWD/.tmp/slimming-golden-gen" python3 scripts/sync.py --validate
  ```

  `sync --validate` rc `0` (361 Aktionen, 41 übersprungen, 2 Warnungen — vorbestehend und
  unabhängig von dieser Änderung, identisch zu 9.4).
- sha256 der Fixture identisch mit dem Sync-Render: Kopie per `cp` aus
  `.tmp/slimming-golden-gen/.claude/agents/dependency-auditor.md`, danach `cmp` rc `0`, sha256
  `b43d54e13dc23b56780ecd61af78a36a7293504c5dc57a16e162173b478b05f3` — in beiden Render-Verzeichnissen
  und in der Fixture identisch.
- **Determinismus-Nachweis (Zweitrender) — durchgeführt.** Wie in 8.4 und 9.4 über zwei getrennte
  temporäre Zielverzeichnisse, anschließend der Vergleich aus
  `tests/fixtures/slimming-golden/README.md:50`:

  ```bash
  mkdir -p .tmp/slimming-golden-gen2
  AGENT_META_TEST_REPO="$PWD/.tmp/slimming-golden-gen2" python3 scripts/sync.py --validate
  diff -r .tmp/slimming-golden-gen/.claude/agents .tmp/slimming-golden-gen2/.claude/agents
  ```

  Ergebnis: **`diff -r` rc `0`** — byte-identisch, null abweichende Dateien im gesamten Zielbaum.
  Damit ist zugleich belegt, dass der Render **kein** `{{AGENT_META_DATE}}`-Drift trägt (10.6).
- Die Fixture enthält **keinen** Absolutpfad, **keinen** Hostnamen, **keinen** Commit-SHA, **kein**
  `{{AGENT_META_DATE}}` und **keinen** unaufgelösten Platzhalter (je `grep -c` = 0 für `{{`,
  `/home/`, `4816c3e6`, `http://`).
- Frontmatter konsistent: `version: 1.7.0` und `generated-from: 1-generic/dependency-auditor.md@1.7.0`
  (`tests/fixtures/slimming-golden/dependency-auditor.md:3` und `:17`).

### 10.5 Verifikation

Verifikationslauf im Arbeitsbaum auf Head `4816c3e6` (Branch
`feat/audit-role-disciplines-cybersecurity`):

| Prüfung | Ergebnis |
|---|---|
| `pytest tests/test_template_slimming_equivalence.py -q` | **8 passed**, rc 0 — inkl. `test_golden_equivalence_and_normalization_marking`, `test_no_declared_normalization_is_dead` und der `_GOLDEN_ROLE_COUNT`-Prüfung (`:1301-1302`, `58 == 58`, unverändert) |
| `python3 scripts/sync.py --validate` | rc `0` |
| Vorher-Zustand desselben Laufs | **1 failed, 7 passed** — `test_golden_equivalence_and_normalization_marking` (reproduziert vor dem Fix, identisch zur CI-Meldung) |
| `git status --short` | genau 2 Dateien: `tests/fixtures/slimming-golden/dependency-auditor.md`, `docs/plans/2026-09-19-dynamic-routing-template-slimming-diff-manifest.md` |
| Diff-Scope der Fixture | `tests/fixtures/slimming-golden/dependency-auditor.md \| 34 +++++++++++++++` → **+29/−5** |

> **Nicht durchgeführt und deshalb nicht behauptet:** ein voller `pytest tests/`-Lauf. Wie in 8.5
> und 9.5 vermerkt, sammelt ein solcher Lauf umgebungsabhängige Admin-UI-/Django-Collection-Fehler,
> die nichts mit dieser Änderung zu tun haben; die Aussage dieses Eintrags ist **module-genau** und
> deckt sich mit 8.5 und 9.5.

### 10.6 Bestandsaufnahme aller 58 Goldens

Vollständig über alle 58 Fixtures neu gemessen (Byte-Vergleich Fixture ↔ Render, Aufteilung nach
`_MIGRATED_PATHS`), wie in 9.6 frisch gemessen und nicht übernommen:

**(a) Test-native — die Definition, die das Gate durchsetzt:**

| Kategorie | Anzahl | Veränderung ggü. 9.6 |
|---|---|---|
| byte-identisch (unmigriert) | 11 | unverändert |
| deklariert migriert | 47 | unverändert |
| **echter Skew** | **0** | unverändert |

**(b) Raw-Byte — ohne Normalisierung:**

| Kategorie | Anzahl | Veränderung ggü. 9.6 |
|---|---|---|
| byte-identisch zum Render | 33 | unverändert |
| raw-abweichend | 25 | unverändert |
| **echter Skew** | **0** | unverändert |

`dependency-auditor` stand vor der Re-Baseline in der 26er-Gruppe der raw-abweichenden Fixtures
(alleiniger Delta-Skew: VENDOR-Schritt, Vendor-Evidenz-Abschnitt, Provenance-Block, Versionsfeld) und
ist nach der Re-Baseline in die 33er-Gruppe der byte-identischen Render-Treffer gewechselt. Damit
steht der Bestand **exakt** auf dem in 9.6 dokumentierten Stand zurück — ein unabhängiger Beleg
dafür, dass durch diese Re-Baseline **keine** andere eingefrorene Fixture verschoben wurde.

Die deklarierten Normalisierungen `OG-CANON` und `PI-PASS-DEP` für `dependency-auditor` bleiben als
**lebende** Deklarationen erhalten und werden von `test_no_declared_normalization_is_dead` weiterhin
als nicht-tot bestätigt; es war **keine** Eintragung, Entfernung oder Änderung an `_NORMALIZATIONS`
nötig.

Zusätzlich bestätigt: **keine Orphan-Fixture** und **kein Golden ohne Render-Gegenstück** (58 = 58,
0 Orphans, Summe der Bestandsaufnahme 58). `agent-meta-manager.md` — die einzige
`{{AGENT_META_DATE}}`-Fixture (`tests/fixtures/slimming-golden/README.md:57-71`) — ist
**unverändert**; der `diff -r` über den gesamten Zielbaum (10.4) zeigt keinen Datumsdrift. Die
Scratch-Verzeichnisse `.tmp/slimming-golden-gen{,2}` wurden nach der Messung entfernt.

### 10.7 Status B2a

B2a ist durch die Re-Baseline **wiederhergestellt**, nicht abgeschwächt: die Fixture enthält exakt
den vom aktuellen Template erzeugten Output, die Update-Regel ist erfüllt (dieser Eintrag), und
das Gate ist grün (10.5). Die Deltas aus 10.1 sind orthogonale Inhaltsänderungen der Rolle; an
`_MIGRATED_PATHS`, `_NORMALIZATIONS`, `_LOCATORS` oder `_GOLDEN_ROLE_COUNT` wurde **nichts**
angefasst — das Gate behält seine Zähne.

Klarstellung zur Einordnung wie in 8.7 und 9.7: dies ist eine **Statusaussage** über B2a, keine
Klassifikation der Änderung als B2a-Fall. Die Änderung selbst ist ein Baseline-Update nach
Update-Regel (Kopf-Block dieses Abschnitts, Vertrag
`tests/fixtures/slimming-golden/README.md:73-77`), weil keine Near-Duplikat-Variante für die
Deltas 1–5 und keine Block-Migration vorliegt (10.2).

## 11. Re-Baseline der Golden-Baseline für `orchestrator` (PR #822)

Derselbe Verfahrensfall wie Abschnitt 8 (effort-estimator), Abschnitt 9 (documenter) und
Abschnitt 10 (dependency-auditor), angewandt auf die vierte nachträglich veränderte aktive
Rolle. Die CI auf PR #822 (`feat/agent-audit-roles`, Head `3015f2cf`) war an **fünf** Stellen
rot; **eine** davon — `test_golden_equivalence_and_normalization_marking` — ist Gegenstand dieses
Eintrags, die übrigen vier waren Registrierungs-Lücken der zwei neuen Rollen
(`tests/test_role_addressability_coverage.py` und `tests/test_unified_active_set.py`) und haben
mit der Golden-Baseline nichts zu tun. Sie sind in 11.5 nur der Vollständigkeit des
Arbeitsbaum-Umfangs halber genannt.

> **Autor:** Develop-Agent `senior-developer` (Orchestrator-Delegation); namentliche Autorschaft wird
> hier nicht geführt — Nachweis ist der Diff-Scope in 11.5.
> **Commit:** **noch nicht vorhanden** — die Re-Baseline wurde bewusst **nicht** committet; die
> Aufgabengrenze verbietet Git-Mutationen (`commit`/`add`/`push`). Der Diff-Scope ist daher
> **im Arbeitsbaum** gemessen (11.5) und wird erst mit dem Folge-Commit des `git`-Agenten zur
> SHA. Abweichend von Abschnitt 8 wird hier deshalb **keine** Commit-SHA zitiert; eine erfundene
> wäre eine Falschangabe.
> **Gegenstand:** `tests/fixtures/slimming-golden/orchestrator.md` — 1 von **58** eingefrorenen
> Golden-Fixtures (Aktive-Rollen-Menge, `tests/fixtures/slimming-golden/README.md:36-38`; neu
> gemessen: `len(_golden_roles()) == _GOLDEN_ROLE_COUNT == 58`).
> **Klassifikation:** **Baseline-Update nach Update-Regel**
> (`tests/fixtures/slimming-golden/README.md:73-77`) — **kein B2a-/B2b-Fall**; siehe 11.2 und 11.7.
> **Nicht Gegenstand:** die beiden neuen Rollen `risk-based-audit-planner` und
> `control-framework-assessor` — sie sind **keine** aktiven agent-meta-Rollen (kein Eintrag in der
> `roles:`-Whitelist `.meta-config/project.yaml`), werden nicht gerendert und besitzen keine
> Fixture; siehe 11.2, Absatz „Nicht-aktive Rollen".

### 11.1 Auslöser

Der PR #822 fügte mit `control-framework-assessor` eine neue Audit-Rolle ein. Ihre
Handoff-Deklaration in `config/role-defaults.yaml` lautet:

```yaml
handoff:
  output_contract: control-assessment-v1
  target_roles:
  - feedback
  - orchestrator
```

Der Output-Vertrag `control-assessment-v1` wird damit von zwei Zielrollen konsumiert. Die
Routing-Tabelle des `orchestrator` — ein **generierter** Block, der je Zielrolle deren
konsumierbare `input_contracts` auflistet — führt `control-assessment-v1` deshalb ab sofort im
Eintrag der Rolle `feedback` mit.

Inhaltliche Änderung an `orchestrator` — **vollständig, 1 Delta** (aus dem Diff der Fixture
gemessen, 11.5):

1. Neuer Listeneintrag `"control-assessment-v1"` in `input_contracts` der `feedback`-Zeile der
   generierten Routing-Tabelle (Fixture `orchestrator.md:763`). Reines Anfügen eines
   JSON-Listenelements; **keine** bestehende Zeile geändert, **keine** Struktur-, Versions- oder
   Workflow-Änderung.

Das Delta ist **orthogonal** zur Slimming-Änderung: es betrifft generierten Routing-Inhalt, nicht
die Block-Extraktion (vgl. 8.1, 9.1, 10.1).

### 11.2 Mechanismus des Fehlschlags

**`orchestrator` nimmt den Byte-Identitäts-Zweig, nicht den Normalisierungs-Zweig.** Neu gemessen
über die Definition des Gates:

- `agents/1-generic/orchestrator.md in _MIGRATED_PATHS` → `False` (`_MIGRATED_PATHS` ist ein
  `frozenset` von 74 Template-Pfaden, definiert in
  `tests/test_template_slimming_equivalence.py:235`; die Rollen `documenter` und
  `dependency-auditor` stehen darin, `orchestrator` und `effort-estimator` nicht);
- `"orchestrator" in _NORMALIZATIONS` → `False` (`_NORMALIZATIONS` ist ein Tupel von 28
  Deklarationen).

Damit greift der Zweig `tests/test_template_slimming_equivalence.py:1114-1127` — `if template not
in _MIGRATED_PATHS: if golden != current: failures.append(...)` gefolgt von `continue`. Der
`_normalize()`-Pfad wird **gar nicht** betreten; die Assertion `:1148` meldet folglich:

```
orchestrator (agents/1-generic/orchestrator.md): unexpected diff on an unmigrated role
```

Das ist strukturell derselbe Fall wie Abschnitt 8 (effort-estimator, ebenfalls nicht migriert) und
**nicht** derselbe Fall wie 9 und 10 (dort beide migriert, Fehlermeldung
`diff not attributable to declared normalizations`). Für `orchestrator` existiert kein
Normalisierungsmodell, das das Delta aus 11.1 abdecken könnte: `_LOCATORS` und `_normalize()`
arbeiten ausschließlich auf den vier Block-Kinds aus `_KIND_CANONICAL_VAR`
(`tests/test_template_slimming_equivalence.py:245-250`) — sie erkennen Sektionen anhand von
Heading-/Tag-Regexen und erkennen **weder** JSON-Listen in generierten Routing-Tabellen **noch**
Output-Contract-Strings. Eine erfundene Variante hätte den Vertrag verletzt statt eingehalten.

**Nicht-aktive Rollen (ausdrücklich geprüft, kein Re-Baseline-Bedarf):** `risk-based-audit-planner`
und `control-framework-assessor` sind **keine** aktiven agent-meta-Rollen dieser
Repo-Konfiguration. Neu gemessen:

- keine der beiden steht in der `roles:`-Whitelist `.meta-config/project.yaml`;
- für keine der beiden existiert eine Fixture unter `tests/fixtures/slimming-golden/`;
- der Sync rendert **keine** `.claude/agents/risk-based-audit-planner.md` und **keine**
  `.claude/agents/control-framework-assessor.md` — weder in Render 1 noch in Render 2 (58
  gerenderte `.md` in beiden Läufen, 58 Fixtures, 0 Orphans in beide Richtungen).

Folge: das Gate iteriert über `_golden_roles()` (58 Rollen) und **besucht beide neuen Rollen
nie**. Ihr Einfluss auf die Golden-Baseline ist **ausschließlich** indirekt — über den
generierten Routing-Inhalt des `orchestrator` (11.1). Es wurde **keine** Fixture für sie angelegt;
eine erfundene Fixture würde `_GOLDEN_ROLE_COUNT == 58`
(`tests/test_template_slimming_equivalence.py:1301-1302`) brechen.

### 11.3 Gewählte Fix-Route und Vertragsbeleg

Bewusste, über den **echten Sync-Pfad** erzeugte Re-Baseline nach dem Verfahrensvertrag
(`tests/fixtures/slimming-golden/README.md:22-41`), ausdrücklich **nicht** als „incidental
re-render" (`:18-20`) und **nicht** als Handedit.

| Option | Bewertung |
|---|---|
| Golden-Fixture auf dem alten Stand belassen | Nicht möglich — das Template rendert den neuen Vertrag, der Render enthält ihn |
| Rolle künstlich migrieren / neue B2b-Variante für das Delta aus 11.1 erfinden | Vertragsbruch (11.2) — und für `orchestrator` ist der Normalisierungs-Zweig gar nicht erreichbar |
| `{{AGENT_META_DATE}}`-Sonderregel ausweiten | Nicht anwendbar — der Platzhalter rendert ausschließlich in `agent-meta-manager.md` (`:57-71`) |
| Die 25 raw-abweichenden Fixtures „vorsorglich" mitkopieren | Vertragsbruch — 10.6 belegt, dass diese 25 Deltas **alle** von deklarierten Normalisierungen absorbiert werden und **null** echten Skew tragen |
| **Bewusste Re-Baseline + Manifest-Eintrag** | **Gewählt** — genau der in R8, R9, R10 und in der Update-Regel vorgesehene Weg |

**Grenze des Fixes (bewusst eingehalten):** es wurde **ausschließlich diese eine** Fixture
angefasst. Die beiden Sync-Läufe rendern alle 58 aktiven Rollen, aber kopiert wurde nur
`orchestrator.md`; ein Bulk-Kopieren des gesamten Zielbaums hätte die 57 anderen eingefrorenen
Fixtures verschoben und das Gate damit stillschweigend ausgehebelt. Nachweis über den
Diff-Scope in 11.5 und über die vollständige Bestandsaufnahme in 11.6.

### 11.4 Nachweis der Herkunft (keine Handpflege)

- **Erzeugung über den realen Sync-Pfad**, wörtlich der Verfahrensvertrag
  (`tests/fixtures/slimming-golden/README.md:29-31`):

  ```bash
  mkdir -p .tmp/slimming-golden-gen
  AGENT_META_TEST_REPO="$PWD/.tmp/slimming-golden-gen" python3 scripts/sync.py --validate
  ```

  `sync --validate` rc `0` (361 Aktionen, 43 übersprungen, 2 Warnungen). Die Warnungen sind
  vorbestehend und unabhängig von dieser Änderung (ein `placeholders.unknown` für `ROLE` in
  `agents/2-platform/agent-meta-mammouth-expert.md` sowie der Submodul-Hinweis für
  `external/awesome-claude-code`); sie sind **keine** Folge des Renderings und stehen im
  Verhält zu 9.4/10.4 unverändert, bis auf die um 2 gestiegene Zahl der übersprungenen Aktionen
  (Folge der zwei neuen Rollen in der Merge-Basis).
- sha256 der Fixture identisch mit dem Sync-Render: Kopie per `cp` aus
  `.tmp/slimming-golden-gen/.claude/agents/orchestrator.md`, danach `cmp` rc `0`, sha256
  `b428893e48937f0d33f856f0eda20119d32f14c665410a39960b3144574d46b1` — in **beiden**
  Render-Verzeichnissen **und** in der Fixture identisch.
- **Determinismus-Nachweis (Zweitrender) — durchgeführt.** Wie in 8.4, 9.4 und 10.4 über zwei
  getrennte temporäre Zielverzeichnisse, anschließend der Vergleich aus
  `tests/fixtures/slimming-golden/README.md:50`:

  ```bash
  mkdir -p .tmp/slimming-golden-gen2
  AGENT_META_TEST_REPO="$PWD/.tmp/slimming-golden-gen2" python3 scripts/sync.py --validate
  diff -r .tmp/slimming-golden-gen/.claude/agents .tmp/slimming-golden-gen2/.claude/agents
  ```

  Ergebnis: **`diff -r` rc `0`** — byte-identisch, null abweichende Dateien im gesamten Zielbaum
  (je Lauf 58 `.md`). Damit ist zugleich belegt, dass der Render **kein**
  `{{AGENT_META_DATE}}`-Drift trägt (11.6).
- Die Fixture enthält **keinen** Absolutpfad, **keinen** Hostnamen, **keinen** Commit-SHA, **kein**
  `{{AGENT_META_DATE}}` und **keinen** unaufgelösten Platzhalter (je `count` = 0 für `{{`, `/home/`,
  `/tmp/` und die Head-SHA `3015f2cf`).
- Frontmatter konsistent: `version: 8.2.0` und
  `generated-from: 1-generic/orchestrator.md@8.2.0`
  (`tests/fixtures/slimming-golden/orchestrator.md:3` und `:14`).

### 11.5 Verifikation

Verifikationslauf im Arbeitsbaum auf Head `3015f2cf` (Branch `feat/agent-audit-roles`):

| Prüfung | Ergebnis |
|---|---|
| `pytest tests/test_role_addressability_coverage.py tests/test_unified_active_set.py tests/test_template_slimming_equivalence.py tests/test_auto_commit_coverage.py tests/test_contract_labels.py -q` | **30 passed**, rc 0 |
| `pytest tests/test_template_slimming_equivalence.py -q` | **8 passed**, rc 0 — inkl. `test_golden_equivalence_and_normalization_marking`, `test_no_declared_normalization_is_dead` und der `_GOLDEN_ROLE_COUNT`-Prüfung (`:1301-1302`, `58 == 58`, unverändert) |
| `python3 scripts/sync.py --validate` | rc `0` |
| Vorher-Zustand desselben Laufs | **5 failed, 25 passed** — reproduziert vor dem Fix, identisch zur CI-Meldung (siehe Kopf dieses Abschnitts) |
| `git status --short` | genau 4 Dateien: `tests/fixtures/slimming-golden/orchestrator.md` (Gegenstand dieses Eintrags), `config/role-defaults.yaml` und `tests/test_role_addressability_coverage.py` (Registrierungs-Vollständigkeit der zwei neuen Rollen, **ohne** Bezug zur Golden-Baseline) sowie dieses Manifest |
| Diff-Scope der Fixture | `tests/fixtures/slimming-golden/orchestrator.md \| 2 +−1` → **+2/−1** — genau das Delta aus 11.1, keine weitere Zeile |

Die drei übrigen geänderten Dateien betreffen **nicht** die Golden-Baseline und sind hier nur der
Vollständigkeit des Arbeitsbaum-Umfangs halber genannt: die Fixture-Änderung ist exakt auf
`orchestrator.md` begrenzt, und der Test-Korpus blieb unangetastet (kein Eingriff in
`_MIGRATED_PATHS`, `_NORMALIZATIONS`, `_LOCATORS`, `_KIND_REGISTRY` oder `_GOLDEN_ROLE_COUNT`).

> **Nicht durchgeführt und deshalb nicht behauptet:** ein voller `pytest tests/`-Lauf. Wie in 8.5,
> 9.5 und 10.5 vermerkt, sammelt ein solcher Lauf umgebungsabhängige Admin-UI-/Django-Collection-
> Fehler, die nichts mit dieser Änderung zu tun haben; die Aussage dieses Eintrags ist
> **module-genau** und deckt sich mit 8.5, 9.5 und 10.5.

### 11.6 Bestandsaufnahme aller 58 Goldens

Vollständig über alle 58 Fixtures neu gemessen, mit dem `render_env`-Fixture des Gates selbst
(Byte-Vergleich Fixture ↔ Render, Aufteilung nach `_MIGRATED_PATHS`), wie in 9.6 und 10.6 frisch
gemessen und nicht übernommen:

**(a) Test-native — die Definition, die das Gate durchsetzt:**

| Kategorie | Anzahl | Veränderung ggü. 10.6 |
|---|---|---|
| byte-identisch (unmigriert) | 11 | unverändert |
| deklariert migriert | 47 | unverändert |
| **echter Skew** | **0** | unverändert |

Die 11 unmigrierten byte-identischen Rollen sind `agent-meta-scout`, `claude-expert`,
`continue-expert`, `copilot-expert`, `effort-estimator`, `gemini-expert`, `ideation`,
`intern-developer`, `mammouth-expert`, `opencode-expert` und — nach dieser Re-Baseline neu
hinzugekommen — `orchestrator`.

**(b) Raw-Byte — ohne Normalisierung:**

| Kategorie | Anzahl | Veränderung ggü. 10.6 |
|---|---|---|
| byte-identisch zum Render | 33 | unverändert |
| raw-abweichend | 25 | unverändert |
| **echter Skew** | **0** | unverändert |

`orchestrator` stand vor der Re-Baseline in der 25er-Gruppe der raw-abweichenden Fixtures
(alleiniger Delta-Skew: `control-assessment-v1` in der `feedback`-Zeile) und ist nach der
Re-Baseline in die 33er-Gruppe der byte-identischen Render-Treffer gewechselt. Damit steht der
Bestand **exakt** auf dem in 10.6 dokumentierten Stand — ein unabhängiger Beleg dafür, dass durch
diese Re-Baseline **keine** andere eingefrorene Fixture verschoben wurde.

Dies ist zugleich der empirische Beleg für die Vorwarnung, dass ein naiver `diff` hier in die
Irre führt: **26** Fixtures weichen roh vom Render ab, das Gate meldet aber **0** echten Skew.
Die 25 verbleibenden Roh-Deltas sind sämtlich Absatz-/Marker-Verschiebungen (`PARSE_INPUT`,
`OUTPUT_GUARD`, `ANTI_RECURSION`) und werden von den deklarierten Normalisierungen absorbiert.
Maßgeblich ist deshalb das Gate, nicht der Byte-Vergleich.

Zusätzlich bestätigt: **keine Orphan-Fixture** und **kein Golden ohne Render-Gegenstück** (58 = 58,
0 Orphans in beide Richtungen, Summe der Bestandsaufnahme 58). `agent-meta-manager.md` — die
einzige `{{AGENT_META_DATE}}`-Fixture (`tests/fixtures/slimming-golden/README.md:57-71`) — ist
**unverändert**; der `diff -r` über den gesamten Zielbaum (11.4) zeigt keinen Datumsdrift. Die
Scratch-Verzeichnisse `.tmp/slimming-golden-gen{,2}` wurden nach der Messung entfernt.

### 11.7 Status B2a

B2a ist durch die Re-Baseline **wiederhergestellt**, nicht abgeschwächt: die Fixture enthält exakt
den vom aktuellen Template erzeugten Output, die Update-Regel ist erfüllt (dieser Eintrag), und
das Gate ist grün (11.5). Das Delta aus 11.1 ist eine orthogonale Inhaltsänderung der generierten
Routing-Tabelle; an `_MIGRATED_PATHS`, `_NORMALIZATIONS`, `_LOCATORS`, `_KIND_REGISTRY` oder
`_GOLDEN_ROLE_COUNT` wurde **nichts** angefasst — das Gate behält seine Zähne.

Klarstellung zur Einordnung wie in 8.7, 9.7 und 10.7: dies ist eine **Statusaussage** über B2a,
keine Klassifikation der Änderung als B2a-Fall. Die Änderung selbst ist ein Baseline-Update nach
Update-Regel (Kopf-Block dieses Abschnitts, Vertrag
`tests/fixtures/slimming-golden/README.md:73-77`), weil für `orchestrator` weder eine
Near-Duplikat-Variante für das Delta aus 11.1 noch eine Block-Migration vorliegt (11.2).

## 12. Re-Baseline der Golden-Baseline für `orchestrator` (PR #824, nach dem Merge)

Erneuter, **zweiter** Re-Baseline-Fall auf **derselben** Fixture, den Abschnitt 11 für PR #822
dokumentiert hat. Neu ist die Reihenfolge: die Re-Baseline musste **nach** dem Merge mit
`origin/main` erfolgen, weil erst der Merge die Reihenfolge von
`feedback.handoff.input_contracts` endgültig auflöst (12.1). Vor dem Merge hätte dieselbe
Fixture zwei konkurrierende, unabhängige Staleness-Ursachen gehabt; nur der Merge macht sichtbar,
dass die aufgelöste Reihenfolge jetzt `… lifecycle-audit-v1`, **`fraud-risk-assessment-v1`**,
`control-assessment-v1` lautet.

> **Autor:** Develop-Agent `senior-developer` (Orchestrator-Delegation); namentliche Autorschaft
> wird hier nicht geführt — Nachweis ist der Diff-Scope in 12.5.
> **Commit:** **noch nicht vorhanden** — die Re-Baseline wurde bewusst **nicht** committet; die
> Aufgabengrenze verbietet Git-Mutationen (`commit`/`add`/`push`). Der Diff-Scope ist daher
> **im Arbeitsbaum** gemessen (12.5). Abweichend von den Abschnitten 8-11 wird hier deshalb
> **keine** Commit-SHA zitiert; eine erfundene wäre eine Falschangabe. Messbasis ist der
> Arbeitsbaum auf Head `9ed2c701` (Branch `feat/agent-fraud-risk-role`, Merge-Commit mit zwei
> Eltern, in Sync mit `origin`).
> **Gegenstand:** `tests/fixtures/slimming-golden/orchestrator.md` — dieselbe 1 von **58**
> eingefrorenen Golden-Fixtures wie in Abschnitt 11 (Aktive-Rollen-Menge,
> `tests/fixtures/slimming-golden/README.md:36-38`; neu gemessen:
> `len(_golden_roles()) == _GOLDEN_ROLE_COUNT == 58`).
> **Klassifikation:** **Baseline-Update nach Update-Regel**
> (`tests/fixtures/slimming-golden/README.md:73-77`) — **kein B2a-/B2b-Fall**; siehe 12.2 und 12.7.
> **Nicht Gegenstand:** die neue Rolle `fraud-risk-assessor` selbst — sie ist **keine** aktive
> agent-meta-Rolle (kein Eintrag in der `roles:`-Whitelist `.meta-config/project.yaml`), wird nicht
> gerendert und besitzt keine Fixture; siehe 12.2, Absatz „Nicht-aktive Rolle".

### 12.1 Auslöser

PR #824 fügte mit `fraud-risk-assessor` eine neue Rolle ein. Ihre Handoff-Deklaration in
`config/role-defaults.yaml` lautet:

```yaml
handoff:
  output_contract: fraud-risk-assessment-v1
  target_roles:
  - feedback
  - orchestrator
```

Der Output-Vertrag `fraud-risk-assessment-v1` wird damit — wie `control-assessment-v1` in 11.1 —
von zwei Zielrollen konsumiert. Die Routing-Tabelle des `orchestrator` — ein **generierter**
Block, der je Zielrolle deren konsumierbare `input_contracts` auflistet — führt
`fraud-risk-assessment-v1` deshalb ab sofort im Eintrag der Rolle `feedback` mit.

**Die Reihenfolge ist mergebedingt und deshalb der eigentliche Auslöser.** `feedback` ist eine der
beiden Rollen, die sowohl `fraud-risk-assessment-v1` als auch `control-assessment-v1` konsumieren.
Die aufgelöste `input_contracts`-Liste wird aus den Handoff-Deklarationen der Zulieferrollen
abgeleitet; auf dem Branch vor dem Merge fehlte `control-assessment-v1` (aus PR #822), danach ist
es vorhanden. Neu gemessene, aufgelöste Reihenfolge in der Fixture
(`tests/fixtures/slimming-golden/orchestrator.md:759-765`):

| Position | Eintrag | Herkunft |
|---|---|---|
| 1 | `dependency-audit-v1` | dependency-auditor |
| 2 | `prompt-governance-v1` | prompt-governor |
| 3 | `lifecycle-audit-v1` | app-lifecycle-governor |
| **4** | **`fraud-risk-assessment-v1`** | **fraud-risk-assessor (neu, PR #824)** |
| 5 | `control-assessment-v1` | control-framework-assessor (PR #822, via Merge) |

Inhaltliche Änderung an `orchestrator` — **vollständig, 1 Delta** (aus dem Diff der Fixture
gemessen, 12.5):

1. Neuer Listeneintrag `"fraud-risk-assessment-v1"` an Position 4 in `input_contracts` der
   `feedback`-Zeile der generierten Routing-Tabelle (Fixture `orchestrator.md:763`). Reines
   Anhängen eines JSON-Listenelements; **keine** bestehende Zeile geändert, **keine** Struktur-,
   Versions- oder Workflow-Änderung.

Das Delta ist **orthogonal** zur Slimming-Änderung: es betrifft generierten Routing-Inhalt, nicht
die Block-Extraktion (vgl. 8.1, 9.1, 10.1, 11.1). `feedback` selbst ist **keine** Golden-Fixture —
`feedback` steht in keinem der drei Migrations-Register, ist damit **unmigriert** und byte-identisch
zum Render (12.6); der Vertrag folgt also **nicht** aus einer Änderung an `feedback.md`.

### 12.2 Mechanismus des Fehlschlags

**`orchestrator` nimmt — wie in 11.2 — den Byte-Identitäts-Zweig, nicht den Normalisierungs-Zweig.**
Neu gemessen über die Definition des Gates:

- `agents/1-generic/orchestrator.md in _MIGRATED_PATHS` → `False` (`_MIGRATED_PATHS` ist ein
  `frozenset` von 74 Template-Pfaden, definiert in
  `tests/test_template_slimming_equivalence.py:235`; die Rollen `documenter` und
  `dependency-auditor` stehen darin, `orchestrator` und `effort-estimator` nicht);
- `"orchestrator" in _NORMALIZATIONS` → `False` (`_NORMALIZATIONS` ist ein Tupel von 28
  Deklarationen, `tests/test_template_slimming_equivalence.py:385`).

Damit greift der Zweig `tests/test_template_slimming_equivalence.py:1114-1127` — `if template not
in _MIGRATED_PATHS: if golden != current: failures.append(...)` gefolgt von `continue`. Der
`_normalize()`-Pfad wird **gar nicht** betreten; die Assertion `:1148` meldet folglich:

```
orchestrator (agents/1-generic/orchestrator.md): unexpected diff on an unmigrated role
```

Das ist strukturell derselbe Fall wie Abschnitt 8 (effort-estimator, ebenfalls nicht migriert) und
**nicht** derselbe Fall wie 9 und 10 (dort beide migriert, Fehlermeldung
`diff not attributable to declared normalizations`). Für `orchestrator` existiert kein
Normalisierungsmodell, das das Delta aus 12.1 abdecken könnte: `_LOCATORS` (`:348`) und
`_normalize()` arbeiten ausschließlich auf den vier Block-Kinds aus `_KIND_CANONICAL_VAR`
(`tests/test_template_slimming_equivalence.py:245-250`) — sie erkennen Sektionen anhand von
Heading-/Tag-Regexen und erkennen **weder** JSON-Listen in generierten Routing-Tabellen **noch**
Output-Contract-Strings. Eine erfundene Variante hätte den Vertrag verletzt statt eingehalten.

**Vorher-Messung des Gates (vor dem Kopieren, nach allen Template-Änderungen):** der Lauf von
`test_golden_equivalence_and_normalization_marking` meldete **genau einen** Fehler und **keinen
zweiten** — `orchestrator` allein, mit einem Unified-Diff von **einer** hinzugefügten Zeile
(`+ "fraud-risk-assessment-v1",`) und **null** entfernten Zeilen. Diese Vorher-Messung ist die
Bedingung dafür, dass die nachfolgende Kopie ausschließlich `orchestrator.md` betrifft; ein
Bulk-Kopieren wäre nicht zulässig gewesen, weil es 57 weitere Fixtures verschoben hätte
(12.3).

**Nicht-aktive Rolle (ausdrücklich geprüft, kein Re-Baseline-Bedarf):** `fraud-risk-assessor` ist
**keine** aktive agent-meta-Rolle dieser Repo-Konfiguration. Neu gemessen:

- keine der Rolle steht in der `roles:`-Whitelist `.meta-config/project.yaml` (auch die beiden
  Rollen aus 11.2 stehen dort nicht);
- für die Rolle existiert **keine** Fixture unter `tests/fixtures/slimming-golden/`;
- der Sync rendert **keine** `.claude/agents/fraud-risk-assessor.md` — weder in Render 1 noch in
  Render 2 (je Lauf 58 gerenderte `.md`, 58 Fixtures, 0 Orphans in beide Richtungen, 12.6).

Folge: das Gate iteriert über `_golden_roles()` (58 Rollen) und **besucht die neue Rolle nie**.
Ihr Einfluss auf die Golden-Baseline ist **ausschließlich** indirekt — über den generierten
Routing-Inhalt des `orchestrator` (12.1). Es wurde **keine** Fixture für sie angelegt; eine
erfundene Fixture würde `_GOLDEN_ROLE_COUNT == 58`
(`tests/test_template_slimming_equivalence.py:1301-1302`) brechen.

### 12.3 Gewählte Fix-Route und Vertragsbeleg

Bewusste, über den **echten Sync-Pfad** erzeugte Re-Baseline nach dem Verfahrensvertrag
(`tests/fixtures/slimming-golden/README.md:22-41`), ausdrücklich **nicht** als „incidental
re-render" (`:18-20`) und **nicht** als Handedit.

| Option | Bewertung |
|---|---|
| Golden-Fixture auf dem alten Stand belassen | Nicht möglich — das Template rendert den neuen Vertrag, der Render enthält ihn |
| Rolle künstlich migrieren / neue B2b-Variante für das Delta aus 12.1 erfinden | Vertragsbruch (12.2) — und für `orchestrator` ist der Normalisierungs-Zweig gar nicht erreichbar |
| Re-Baseline **vor** dem Merge mit `origin/main` | Fachlich falsch — die Reihenfolge von `input_contracts` ist vor dem Merge nicht die endgültige; das Ergebnis wäre sofort wieder stale gewesen (12.1) |
| `{{AGENT_META_DATE}}`-Sonderregel ausweiten | Nicht anwendbar — der Platzhalter rendert ausschließlich in `agent-meta-manager.md` (`:57-71`) |
| Die 25 raw-abweichenden Fixtures „vorsorglich" mitkopieren | Vertragsbruch — 12.6 belegt, dass diese 25 Deltas **alle** von deklarierten Normalisierungen absorbiert werden und **null** echten Skew tragen |
| **Bewusste Re-Baseline + Manifest-Eintrag** | **Gewählt** — genau der in R8, R9, R10, R11 und in der Update-Regel vorgesehene Weg |

**Grenze des Fixes (bewusst eingehalten):** es wurde **ausschließlich diese eine** Fixture
angefasst. Die beiden Sync-Läufe rendern alle 58 aktiven Rollen, aber kopiert wurde nur
`orchestrator.md` per Einzel-`cp`; ein Bulk-Kopieren des gesamten Zielbaums hätte die 57 anderen
eingefrorenen Fixtures verschoben und das Gate damit stillschweigend ausgehebelt. Unabhängiger
Gegenbeleg: der nach dem Kopieren erneut gefahrene `diff -r` zwischen Render-Baum und Golden-Verzeichnis
listet **dieselben 25** raw-abweichenden Fixtures wie zuvor — `orchestrator.md` ist darin **nicht**
mehr enthalten, ist also in die byte-identische Gruppe gewechselt. Nachweis über den Diff-Scope in
12.5 und über die vollständige Bestandsaufnahme in 12.6.

### 12.4 Nachweis der Herkunft (keine Handpflege)

- **Erzeugung über den realen Sync-Pfad**, wörtlich der Verfahrensvertrag
  (`tests/fixtures/slimming-golden/README.md:29-31`):

  ```bash
  mkdir -p .tmp/slimming-golden-gen
  AGENT_META_TEST_REPO="$PWD/.tmp/slimming-golden-gen" python3 scripts/sync.py --validate
  ```

  `sync --validate` rc `0` (361 Aktionen, 44 übersprungen, 2 Warnungen). Die erste Warnung ist
  vorbestehend und unabhängig von dieser Änderung (`placeholders.unknown` für `ROLE` in
  `agents/2-platform/agent-meta-mammouth-expert.md`). Die zweite ist der Submodul-Hinweis für
  `external/awesome-claude-code`; sie entsteht **allein** daraus, dass das Render-Zielverzeichnis
  unter dem in dieser Umgebung gitignorierten `.tmp/` liegt, und ist **keine** Folge der Templates
  oder dieser Änderung — dieselbe Warnung tritt bei jedem Render in ein `.tmp/`-Ziel auf. Keine
  der beiden Warnungen betrifft `orchestrator` oder die Fixture.
- sha256 der Fixture identisch mit dem Sync-Render: Kopie per `cp` aus
  `.tmp/slimming-golden-gen/.claude/agents/orchestrator.md`, sha256
  `ca322e1a0980ce9913b5ddc3f8200c373d6a5832953864377113802013a317cc` — in **beiden**
  Render-Verzeichnissen **und** in der Fixture identisch.
- **Determinismus-Nachweis (Zweitrender) — durchgeführt.** Wie in 8.4, 9.4, 10.4 und 11.4 über zwei
  getrennte temporäre Zielverzeichnisse, anschließend der Vergleich aus
  `tests/fixtures/slimming-golden/README.md:50`:

  ```bash
  mkdir -p .tmp/slimming-golden-gen2
  AGENT_META_TEST_REPO="$PWD/.tmp/slimming-golden-gen2" python3 scripts/sync.py --validate
  diff -r .tmp/slimming-golden-gen/.claude/agents .tmp/slimming-golden-gen2/.claude/agents
  ```

  Ergebnis: **`diff -r` rc `0`** — byte-identisch, null abweichende Dateien im gesamten Zielbaum
  (je Lauf 58 `.md`). Damit ist zugleich belegt, dass der Render **kein**
  `{{AGENT_META_DATE}}`-Drift trägt (12.6).
- Die Fixture enthält **keinen** Absolutpfad, **keinen** Hostnamen, **keinen** Commit-SHA, **kein**
  `{{AGENT_META_DATE}}` und **keinen** unaufgelösten Platzhalter (je `count` = 0 für `{{`, `/home/`,
  `/tmp/` und die Head-SHA `9ed2c701`).
- Frontmatter konsistent: `version: 8.2.0` und
  `generated-from: 1-generic/orchestrator.md@8.2.0`
  (`tests/fixtures/slimming-golden/orchestrator.md:3` und `:14`) — beide unverändert gegenüber dem
  Stand aus 11.4, da das Delta reine Listeninhalte der Routing-Tabelle betrifft.

### 12.5 Verifikation

Verifikationslauf im Arbeitsbaum auf Head `9ed2c701` (Branch `feat/agent-fraud-risk-role`, nach dem
Merge mit `origin/main`):

| Prüfung | Ergebnis |
|---|---|
| `pytest tests/test_auto_commit_coverage.py tests/test_contract_labels.py tests/test_role_addressability_coverage.py tests/test_unified_active_set.py tests/test_template_slimming_equivalence.py -q` | **30 passed**, rc 0 |
| `python3 -m pytest tests/ -q --ignore=tests/browser --ignore=tests/test_knowledge_engine.py --timeout=120` | **3082 passed**, 11 Subtests, rc 0, **0 failed** |
| `python3 scripts/sync.py --validate` | rc `0`; die Warnung `crossrefs.changelog-missing-entry` für `agents/1-generic/fraud-risk-assessor.md` ist **beseitigt** (CHANGELOG-Eintrag unter `[Unreleased] → ### Added` mit PR-Referenz #824) |
| Vorher-Zustand des Gates | **1 failed** — reproduziert vor dem Fix, `orchestrator` allein (12.2) |
| `git status --short` | genau **6** Dateien: `tests/fixtures/slimming-golden/orchestrator.md` (Gegenstand dieses Eintrags), `agents/1-generic/fraud-risk-assessor.md`, `config/role-defaults.yaml`, `tests/test_role_addressability_coverage.py` (Registrierungs-Vollständigkeit der neuen Rolle: `routing.addressability` plus die Erwartungszahlen 87 / `keyword` 84) sowie `CHANGELOG.md` und dieses Manifest — **keine** davon betrifft die Golden-Baseline außer `orchestrator.md` |
| Diff-Scope der Fixture | `tests/fixtures/slimming-golden/orchestrator.md` → `git diff --numstat` = **1 / 0** — genau das Delta aus 12.1, keine weitere Zeile |

Der Test-Korpus blieb unangetastet: **kein** Eingriff in `_MIGRATED_PATHS`, `_NORMALIZATIONS`,
`_LOCATORS`, `_KIND_REGISTRY` oder `_GOLDEN_ROLE_COUNT`; die Fixture-Änderung ist exakt auf
`orchestrator.md` begrenzt. Die beiden geänderten Konfig-/Testdateien betreffen die
Registrierungs-Vollständigkeit der neuen Rolle und sind hier nur der Vollständigkeit des
Arbeitsbaum-Umfangs halber genannt.

> **Abweichung von 8.5, 9.5, 10.5 und 11.5:** ein voller `pytest tests/`-Lauf wurde hier
> **durchgeführt** (Zeile 2 der Tabelle) und ist mit **0 failed** grün. Der Vorbehalt der früheren
> Abschnitte zu umgebungsabhängigen Admin-UI-/Collection-Fehlern hat sich für diesen Lauf nicht
> bestätigt. Die am Vortag beobachtete, netzabhängige Flake
> (`test_model_discovery.py::test_fetch_anthropic_models_respects_blacklist`, Sandbox ohne
> Netz) trat in diesem Lauf **nicht** auf — `tests/test_model_discovery.py` wurde separat mit
> **34 passed** nachgemessen. An Test oder Produktionscode dieser Datei wurde **nichts** geändert;
> die Flake ist damit als nicht reproduzierend dokumentiert und **nicht** behoben worden.

### 12.6 Bestandsaufnahme aller 58 Goldens

Vollständig über alle 58 Fixtures neu gemessen (Byte-Vergleich Fixture ↔ Render aus beiden
Sync-Läufen, Aufteilung nach `_MIGRATED_PATHS`), wie in 9.6, 10.6 und 11.6 frisch gemessen und
nicht übernommen:

**(a) Test-native — die Definition, die das Gate durchsetzt:**

| Kategorie | Anzahl | Veränderung ggü. 11.6 |
|---|---|---|
| byte-identisch (unmigriert) | 11 | unverändert |
| deklariert migriert | 47 | unverändert |
| **echter Skew** | **0** | unverändert |

Die 11 unmigrierten byte-identischen Rollen sind `agent-meta-scout`, `claude-expert`,
`continue-expert`, `copilot-expert`, `effort-estimator`, `gemini-expert`, `ideation`,
`intern-developer`, `mammouth-expert`, `opencode-expert` und `orchestrator`. Die Template-Zuordnung
wurde je Fixture über ihr eigenes `generated-from:`-Frontmatter-Feld aufgelöst und gegen
`_MIGRATED_PATHS` geprüft, nicht über eine heuristische Namensliste.

**(b) Raw-Byte — ohne Normalisierung:**

| Kategorie | Anzahl | Veränderung ggü. 11.6 |
|---|---|---|
| byte-identisch zum Render | 33 | unverändert |
| raw-abweichend | 25 | unverändert |
| **echter Skew** | **0** | unverändert |

`orchestrator` stand vor dieser Re-Baseline erneut in der 25er-Gruppe der raw-abweichenden
Fixtures (alleiniger Delta-Skew: `fraud-risk-assessment-v1` an Position 4 der `feedback`-Zeile) und
ist nach der Re-Baseline in die 33er-Gruppe der byte-identischen Render-Treffer gewechselt. Damit
steht der Bestand **exakt** auf dem in 11.6 dokumentierten Stand — ein unabhängiger Beleg dafür,
dass durch diese Re-Baseline **keine** andere eingefrorene Fixture verschoben wurde.

Dies ist zugleich der empirische Beleg für die Vorwarnung, dass ein naiver `diff` hier in die
Irre führt: **25** Fixtures weichen roh vom Render ab, das Gate meldet aber **0** echten Skew.
Die 25 verbleibenden Roh-Deltas sind sämtlich Absatz-/Marker-Verschiebungen (`PARSE_INPUT`,
`OUTPUT_GUARD`, `ANTI_RECURSION`) und werden von den deklarierten Normalisierungen absorbiert.
Maßgeblich ist deshalb das Gate, nicht der Byte-Vergleich.

Zusätzlich bestätigt: **keine Orphan-Fixture** und **kein Golden ohne Render-Gegenstück** (58 = 58,
0 Orphans in beide Richtungen, Summe der Bestandsaufnahme 58). `agent-meta-manager.md` — die
einzige `{{AGENT_META_DATE}}`-Fixture (`tests/fixtures/slimming-golden/README.md:57-71`) — ist
**unverändert**; der `diff -r` über den gesamten Zielbaum (12.4) zeigt keinen Datumsdrift. Die
Scratch-Verzeichnisse `.tmp/slimming-golden-gen{,2}` wurden nach der Messung entfernt.

### 12.7 Status B2a

B2a ist durch die Re-Baseline **wiederhergestellt**, nicht abgeschwächt: die Fixture enthält exakt
den vom aktuellen Template erzeugten Output, die Update-Regel ist erfüllt (dieser Eintrag), und
das Gate ist grün (12.5). Das Delta aus 12.1 ist eine orthogonale Inhaltsänderung der generierten
Routing-Tabelle; an `_MIGRATED_PATHS`, `_NORMALIZATIONS`, `_LOCATORS`, `_KIND_REGISTRY` oder
`_GOLDEN_ROLE_COUNT` wurde **nichts** angefasst — das Gate behält seine Zähne.

Klarstellung zur Einordnung wie in 8.7, 9.7, 10.7 und 11.7: dies ist eine **Statusaussage** über B2a,
keine Klassifikation der Änderung als B2a-Fall. Die Änderung selbst ist ein Baseline-Update nach
Update-Regel (Kopf-Block dieses Abschnitts, Vertrag
`tests/fixtures/slimming-golden/README.md:73-77`), weil für `orchestrator` weder eine
Near-Duplikat-Variante für das Delta aus 12.1 noch eine Block-Migration vorliegt (12.2).

Verhältnis zu Abschnitt 11: die Fixture ist **zweimal** am selben Gegenstand re-baselined worden —
einmal für `control-assessment-v1` (PR #822, vor dem Merge) und einmal für
`fraud-risk-assessment-v1` (PR #824, nach dem Merge). Die Abschnitte ersetzen sich **nicht**; beide
Einträge bleiben Teil des Nachweises, weil sie zwei verschiedene, unabhängige Delta-Ursachen auf
derselben Fixture dokumentieren. Sollte künftig ein weiterer PR erneut am `feedback`-Vertrag
drehen, ist Abschnitt 12 der Präzedenzfall für die Reihenfolge „Merge zuerst, dann re-baselinen".

## 13. Re-Baseline der Golden-Baseline für 7 Rollen (PR #840, nach dem Merge)

Erster Re-Baseline-Fall, der **mehrere** Fixtures zugleich betrifft. Die Abschnitte 8–12
deckten jeweils **eine** Fixture (`effort-estimator` #833, `documenter` #828, `dependency-auditor`
#825, `orchestrator` #822 und #824). PR #840 verändert **neun** bestehende Rollen-Templates
inhaltlich; davon besitzen sieben eine eingefrorene Fixture und rutschen damit alle aus der
eingefrorenen Baseline heraus.

> **Autor:** Develop-Agent `senior-developer` (Orchestrator-Delegation); namentliche Autorschaft
> wird hier nicht geführt — Nachweis ist der Diff-Scope in 13.5.
> **Commit:** **noch nicht vorhanden** — die Re-Baseline wurde bewusst **nicht** committet; die
> Aufgabengrenze verbietet Git-Mutationen (`commit`/`add`/`push`). Abweichend von Abschnitt 8 wird
> deshalb **keine** Commit-SHA zitiert; eine erfundene wäre eine Falschangabe. Messbasis ist der
> Arbeitsbaum auf `bb27e210` (Branch `feat/ai-agent-roles-literature-2026`, Merge-Commit mit zwei
> Eltern `27ba699b` + `01dc2ced`, in Sync mit `origin`).
> **Gegenstand:** 7 von **58** eingefrorenen Golden-Fixtures (Aktive-Rollen-Menge,
> `tests/fixtures/slimming-golden/README.md:36-38`; neu gemessen:
> `len(_golden_roles()) == _GOLDEN_ROLE_COUNT == 58`).
> **Klassifikation:** **Baseline-Update nach Update-Regel**
> (`tests/fixtures/slimming-golden/README.md:73-77`) — **kein B2a-/B2b-Fall**; siehe 13.2 und 13.7.
> **Nicht Gegenstand:** die vier neuen Rollen `llm-evaluator`, `rag-engineer`,
> `ai-governance-engineer` und `ai-observability-engineer` — sie sind **keine** aktiven
> agent-meta-Rollen (kein Eintrag in der `roles:`-Whitelist `.meta-config/project.yaml`), werden
> nicht gerendert und besitzen keine Fixture. Ebenso nicht Gegenstand: `se-verifier` und
> `sre-engineer` — sie wurden von PR #840 ebenfalls inhaltlich geändert, besitzen aber **keine**
> Fixture und sind damit vom Gate nicht erfasst.

### 13.1 Auslöser

Der Merge-Zustand `bb27e210` enthält `01dc2ced` (`feat(agents): add fraud risk assessment role
(#824)`) als zweiten Eltern. PR #840 (`27ba699b`) verändert die Rollen-Templates additiv — neue
Persona-Abschnitte mit Buch-Belegen, neue Scope-Abgrenzungen, neue Routing-Verweise:

| Rolle | `git diff 01dc2ced..HEAD` (Template) | Delta-Klasse | Migrationsstatus |
|---|---|---|---|
| `orchestrator` | +4 | Persona-Erweiterung (Decompositions-Begründung, Review-Loop-Governance) | **unmigriert** |
| `api-specialist` | +4 | Persona-Erweiterung (Swiss-Army-Knife-Verbot, MCP-Grenze) | migriert |
| `code-reviewer` | +9 | Persona-Erweiterung (`blocking` / `claim_type` pro Finding) | migriert |
| `data-engineer` | +2 | Scope-Abgrenzung gegen `rag-engineer` | migriert |
| `principal-developer` | +4 | Persona-Erweiterung (Existenz-Begründung, Anti-Pattern) | migriert |
| `prompt-engineer` | +10 | Persona-Erweiterung (Guardrail-Klassen, keine Universalformel) | migriert |
| `validator` | +4 | Persona-Erweiterung (verifiable ≠ plausible, Claim-Typing) | migriert |
| `se-verifier` | +10 | zwei neue Abschnitte (Zero-Product-Regel L1–Ln, verifiable over plausible) | migriert, **ohne Fixture** |
| `sre-engineer` | +4 | Scope-Abgrenzung gegen `ai-observability-engineer` | migriert, **ohne Fixture** |

Zusätzlich wurden im selben Arbeitsbaum die **Frontmatter-Versionen** dieser neun Templates
gemäß `conventions`-Invariante #2 minor gehoben (additive Inhaltsänderung → Minor `x.Y.0`, siehe
13.3). Beides zusammen — Persona-Delta **und** Versionsfeld — verschiebt das gerenderte Frontmatter
(`version:` **und** `generated-from: …@<version>`) und damit die Fixture.

Der Merge lieferte für `orchestrator.md` bereits eine re-baselined Fixture (Abschnitte 11 und 12,
mit `control-assessment-v1` bzw. `fraud-risk-assessment-v1`). Diese Re-Baseline wurde
**darüber** gelegt; die Fixture wurde zu keinem Zeitpunkt aus `origin/main` zurückgespielt. Der
Bestandsnachweis in 13.6 belegt, dass beide Main-Einträge erhalten geblieben sind.

### 13.2 Mechanismus des Fehlschlags

Das Gate `test_golden_equivalence_and_normalization_marking`
(`tests/test_template_slimming_equivalence.py:1105-1150`) verzweigt nach der Template-Zuordnung der
Rolle, aufgelöst über das eigene `generated-from:`-Frontmatter-Feld der Fixture gegen
`_MIGRATED_PATHS` (`:1113-1114`):

- **unmigriert** (`orchestrator`): `golden != current` ⇒ `unexpected diff on an unmigrated role`
  (`:1116-1127`). **Byte-Identität** ist hier die vertragliche Anforderung.
- **migriert** (die übrigen sechs): `_normalize(golden, variables)` (`:1129`) liefert den
  normalisierten Text; `normalized != current` ⇒ `diff not attributable to declared normalizations`
  (`:1136-1149`). Die deklarierten Normalisierungen decken **ausschließlich** die vier Block-Kinds
  aus `_KIND_CANONICAL_VAR` ab (`ANTI_RECURSION`, `OUTPUT_GUARD`, `BACKGROUND_PROCESS_GUARD`,
  `PARSE_INPUT`); `_LOCATORS` (`:348-353`) erkennen Sektionen über Heading-/Tag-Regexe, **keine
  Versionsstrings und keine Persona-Absätze**.

Beide Zweige sind für dieses Delta blind: das Versions- und Persona-Delta liegt außerhalb des
Normalisierungsmodells. Eine erfundene `retained`-Klausel, eine neue B2b-Variante oder eine
Lockerung von `_MIGRATED_PATHS` hätte den Vertrag verletzt statt eingehalten. Der Vorher-Zustand
wurde vor dem Kopieren reproduziert und nannte **genau diese sieben** Rollen (8 Regex-Treffer, 7
eindeutige Namen) — kein achter.

### 13.3 Gewählte Fix-Route und Vertragsbeleg

Bewusste, über den **echten Sync-Pfad** erzeugte Re-Baseline nach dem Verfahrensvertrag
(`tests/fixtures/slimming-golden/README.md:22-41`), ausdrücklich **nicht** als „incidental
re-render" (`:18-20`) und **nicht** als Handedit. Optionen:

| Option | Bewertung |
|---|---|
| Fixtures auf dem alten Stand belassen | Nicht möglich — die Templates sind Vorgänger im Merge-Ref, der Render ist der neue Stand |
| Rolle künstlich migrieren / B2b-Variante erfinden | Vertragsbruch (13.2) |
| `{{AGENT_META_DATE}}`-Sonderregel ausweiten | Nicht anwendbar — der Platzhalter rendert ausschließlich in `agent-meta-manager.md` (`:57-71`) |
| Bulk-Kopieren des gesamten `agents`-Baums in den Fixture-Ordner | **Verworfen** — würde die 51 nicht betroffenen eingefrorenen Fixtures still überschreiben und genau die Verschiebung erzeugen, die 12.6 als Fehler benennt |
| **Bewusste Re-Baseline der 7 benannten Fixtures + Manifest-Eintrag** | **Gewählt** — genau der in R8 und in der Update-Regel vorgesehene Weg |

Maßgeblich war die Reihenfolge: das Gate wurde **zuerst** laufen gelassen und seine Namensliste als
Arbeitsauftrag übernommen; erst danach wurde kopiert. Der Byte-Vergleich gegen den Render wurde
**nicht** als Auswahlkriterium verwendet — 24 Fixtures weichen roh vom Render ab (13.6b) und sind
trotzdem korrekt.

Ebenfalls in diesem Arbeitsbaum, aus derselben Ursache (Inhaltsänderung ohne Versionshub):
Neun Template-Versionen minor gehoben, additiv, ohne Verhaltens- oder Variablenumbau:

| Template | vorher | nachher |
|---|---|---|
| `agents/1-generic/api-specialist.md` | `1.6.0` | `1.7.0` |
| `agents/1-generic/code-reviewer.md` | `1.8.0` | `1.9.0` |
| `agents/1-generic/data-engineer.md` | `0.5.0` | `0.6.0` |
| `agents/1-generic/orchestrator.md` | `8.2.0` | `8.3.0` |
| `agents/1-generic/principal-developer.md` | `1.5.0` | `1.6.0` |
| `agents/1-generic/prompt-engineer.md` | `1.10.0` | `1.11.0` |
| `agents/1-generic/se-verifier.md` | `1.7.0` | `1.8.0` |
| `agents/1-generic/sre-engineer.md` | `0.6.0` | `0.7.0` |
| `agents/1-generic/validator.md` | `4.6.0` | `4.7.0` |

Die vier neuen Templates (`llm-evaluator`, `rag-engineer`, `ai-governance-engineer`,
`ai-observability-engineer`) stehen korrekt auf `1.0.0` und wurden nicht gehoben.

### 13.4 Nachweis der Herkunft (keine Handpflege)

- Erzeugung über den echten Sync-Pfad, Provider `Claude` (`config/ai-providers.yaml`:
  `agents_dir: .claude/agents`), wie in `README.md:22-41` vorgeschrieben:
  `AGENT_META_TEST_REPO="$PWD/.tmp/slimming-golden-gen" python3 scripts/sync.py --validate`
  (rc `0`, 58 gerenderte Rollen) und ein zweiter Lauf in `.tmp/slimming-golden-gen2`.
- **Determinismus-Nachweis (Zweitrender) — durchgeführt.** Verfahrensvertrag
  `tests/fixtures/slimming-golden/README.md:43-55`:
  `diff -r .tmp/slimming-golden-gen/.claude/agents .tmp/slimming-golden-gen2/.claude/agents`
  ⇒ **rc `0`, 0 Byte Ausgabe, 58 = 58 Dateien**. Keine Abweichung, insbesondere nicht in der
  `{{AGENT_META_DATE}}`-Zeile.
- **Kopiert wurden ausschließlich die 7 vom Gate benannten Fixtures**, einzeln und verbatim; `cmp`
  bestätigt für jeden der sieben Dateien Byte-Gleichheit mit **beiden** Renders. `git status`
  weist unter `tests/fixtures/slimming-golden/` genau diese 7 als geändert aus — keine der 51
  übrigen Fixtures wurde angefasst.
- sha256 der sieben Fixtures im Arbeitsbaum (identisch zum jeweiligen Sync-Render):

  | Fixture | sha256 |
  |---|---|
  | `orchestrator.md` | `5016fd71154ad3db835d06ec13ef4cf0803100f0f557d819237f4747660ab192` |
  | `api-specialist.md` | `cbce9b31d481e8c1a825608b4968bfa58737ac35b76751d36b366376822c2350` |
  | `code-reviewer.md` | `ff5c67079efab52347026f463a88d8ef412a98189b4f287ff658ded698bf5ea8` |
  | `data-engineer.md` | `8d033b0aebe1f53272eaf73d19764de0c31c0bc84024d26fe9727bbf0be7c11f` |
  | `principal-developer.md` | `c40189b4d54eff073434a9f5e2b83c436ffd6f4fa8383558979dc45cc67e799f` |
  | `prompt-engineer.md` | `ad489a123eb0f15ee0b67f1bd78714c7f84208d79b39f5eb55a80e3b4c2e0b4d` |
  | `validator.md` | `5b783e0da8aa6ff44bc46cb9f07da2a8aa3fd85108da136cd90213ab2c6f5168` |

- Keine der 58 Fixtures enthält einen Absolutpfad, einen Hostnamen, eine 40-stellige Commit-SHA
  oder `{{AGENT_META_DATE}}` (über das gesamte Verzeichnis geprüft).
- Frontmatter konsistent je Fixture: `version:` **und** `generated-from: <pfad>@<version>` tragen
  denselben Wert (`1.7.0`, `1.9.0`, `0.6.0`, `8.3.0`, `1.6.0`, `1.11.0`, `4.7.0`).
- **Merge-Einträge erhalten:** `orchestrator.md` enthält weiterhin `fraud-risk-assessment-v1` und
  `control-assessment-v1` (je 1 Treffer) und zusätzlich die neuen Verweise `llm-evaluator`,
  `ai-governance-engineer`, `ai-security-guardian`. Die Fixture wurde auf dem gemergten Stand
  **weitergeschrieben**, nicht aus `origin/main` restauriert.

### 13.5 Verifikation

Verifikationslauf im Arbeitsbaum auf `bb27e210` (nach dem Merge, Git-Mutationen verboten):

| Prüfung | Ergebnis |
|---|---|
| `pytest tests/test_role_addressability_coverage.py tests/test_routing_tool_definitions.py tests/test_unified_active_set.py tests/test_template_slimming_equivalence.py -q` | **46 passed**, rc 0 |
| `pytest tests/test_template_slimming_equivalence.py -q` | **8 passed**, rc 0 |
| `python3 -m pytest tests/ -q --ignore=tests/browser --ignore=tests/test_knowledge_engine.py --timeout=120` | **3082 passed**, 11 Subtests, rc 0, **0 failed** |
| `bash tests/scenarios/run.sh` | **63 von 63 Szenarien PASS**, 0 FAIL, rc 0 (`Scenarios: 63  Passed: 63  Failed: 0`) |
| `python3 scripts/sync.py --validate` | rc `0`, **0 Errors**. Die drei `crossrefs.changelog-missing-entry`-Warnungen betreffen `snippets/agents/{background-process-guard,output-guard,parse-input}.md` — Added by `3c46920a` (PR #833), **nicht** durch PR #840; für die von diesem PR veränderten Dateien besteht keine Warnung. Der CHANGELOG-Eintrag für PR #840 liegt bereits unter `[Unreleased]` |
| Vorher-Zustand des Gates | **1 failed** — reproduziert vor dem Fix, nannte genau diese 7 Rollen (13.2) |
| `git status --short` | genau **19** Dateien: die 7 Fixtures (Gegenstand dieses Eintrags), 9 Template-Versionen (13.3), `config/role-defaults.yaml`, `tests/test_role_addressability_coverage.py`, dieses Manifest; `CHANGELOG.md` ist **unverändert** — **keine** Datei außerhalb des zulässigen Rahmens |
| Diff-Scope der Fixtures | `git diff --numstat`: `api-specialist` 6/2, `code-reviewer` 11/3, `data-engineer` 4/2, `orchestrator` 20/6, `principal-developer` 6/2, `prompt-engineer` 12/2, `validator` 6/2 |

Der Test-Korpus blieb unangetastet: **kein** Eingriff in `_MIGRATED_PATHS`, `_NORMALIZATIONS`,
`_LOCATORS`, `_KIND_REGISTRY` oder `_GOLDEN_ROLE_COUNT` (58, unverändert); keine Assertion in
`tests/test_role_addressability_coverage.py` wurde geschwächt, übersprungen oder gelockert — dort
wurden ausschließlich die beiden Re-Baseline-Konstanten `_EXPECTED_TOTAL` (87 → 91) und
`_EXPECTED_DISTRIBUTION` (`keyword` 84 → 88) an den real gemessenen Bestand angepasst; das
Modul-Docstring zitiert bewusst weiterhin die eingefrorene 84er-Baseline der Spec.

> **Grenze der Aussage:** die beiden Konfig-/Testdateien (`config/role-defaults.yaml`,
> `tests/test_role_addressability_coverage.py`) sind **kein** Teil der Golden-Baseline. Sie gehören
> zur Registrierungs-Vollständigkeit der vier neuen Rollen (`routing.addressability: keyword` als
> erster Key unter `routing:`, `routing_patterns.keywords` byte-identisch zu
> `routing.intent_keywords`) und sind hier nur der Vollständigkeit des Arbeitsbaum-Umfangs halber
> genannt. Sie müssen **gemeinsam** mit den Fixtures landen, sonst regressiert
> `test_keyword_roles_have_non_empty_patterns`.

### 13.6 Bestandsaufnahme aller 58 Goldens

Vollständig über alle 58 Fixtures neu gemessen (Byte-Vergleich Fixture ↔ Render aus beiden
Sync-Läufen, Aufteilung nach `_MIGRATED_PATHS`, Template-Zuordnung je Fixture über das eigene
`generated-from:`-Frontmatter-Feld), wie in 9.6, 10.6, 11.6 und 12.6 frisch gemessen und nicht
übernommen:

**(a) Test-native — die Definition, die das Gate durchsetzt:**

| Kategorie | Anzahl | Veränderung ggü. 12.6 |
|---|---|---|
| byte-identisch (unmigriert) | 11 | unverändert |
| deklariert migriert | 47 | unverändert |
| **echter Skew** | **0** | unverändert |

Die 11 unmigrierten byte-identischen Rollen sind `agent-meta-scout`, `claude-expert`,
`continue-expert`, `copilot-expert`, `effort-estimator`, `gemini-expert`, `ideation`,
`intern-developer`, `mammouth-expert`, `opencode-expert` und `orchestrator`. `orchestrator` ist
darin **unverändert** enthalten: der Byte-Identitätszweig des Gates ist nach der Re-Baseline
wieder erfüllt, die Rolle ist **nicht** und **darf nicht** migriert werden.

**(b) Raw-Byte — ohne Normalisierung:**

| Kategorie | vorher | nachher | Veränderung |
|---|---|---|---|
| byte-identisch zum Render | 27 | **34** | +7 |
| raw-abweichend | 31 | **24** | −7 |

Die 7 roh abweichenden Fixtures waren **exakt** die 7 in 13.2 genannten; alle 7 sind nach der
Re-Baseline in die byte-identische Gruppe gewechselt. Die verbleibenden 24 Roh-Deltas sind
**mengengleich und setzgleich** mit den 24 aus 12.6 — als Mengenvergleich vor und nach dem Kopieren
verifiziert. Sie sind sämtlich Absatz-/Marker-Verschiebungen (`PARSE_INPUT`, `OUTPUT_GUARD`,
`ANTI_RECURSION`) und werden von den deklarierten Normalisierungen absorbiert. Maßgeblich ist
deshalb das Gate, nicht der Byte-Vergleich — die Re-Baseline hat **keine** andere eingefrorene
Fixture verschoben.

Zusätzlich bestätigt: **keine Orphan-Fixture** und **kein Golden ohne Render-Gegenstück** (58 = 58,
0 Orphans in beide Richtungen). `agent-meta-manager.md` — die einzige `{{AGENT_META_DATE}}`-Fixture
(`tests/fixtures/slimming-golden/README.md:57-71`) — ist **unverändert**; die Zeile
`**Version info:** v1.2.0-beta.2 (2026-09-13)` ist identisch mit `HEAD`, der `diff -r` über den
gesamten Zielbaum (13.4) zeigt keinen Datumsdrift. Die Scratch-Verzeichnisse
`.tmp/slimming-golden-gen{,2}` wurden nach der Messung entfernt.

### 13.7 Status B2a

B2a ist durch die Re-Baseline **wiederhergestellt**, nicht abgeschwächt: jede der 7 Fixtures
enthält exakt den vom aktuellen Template erzeugten Output, die Update-Regel ist erfüllt (dieser
Eintrag), und das Gate ist grün (13.5). Die Deltas aus 13.1 sind orthogonale Inhalts- und
Versionsänderungen der generierten Rollen; an `_MIGRATED_PATHS`, `_NORMALIZATIONS`, `_LOCATORS`,
`_KIND_REGISTRY` oder `_GOLDEN_ROLE_COUNT` wurde **nichts** angefasst — das Gate behält seine
Zähne.

Klarstellung zur Einordnung wie in 8.7, 9.7, 10.7, 11.7 und 12.7: dies ist eine **Statusaussage**
über B2a, keine Klassifikation der Änderung als B2a-Fall. Die Änderung selbst ist ein
Baseline-Update nach Update-Regel (Kopf-Block dieses Abschnitts, Vertrag
`tests/fixtures/slimming-golden/README.md:73-77`), weil für keine der sieben Rollen eine
Near-Duplikat-Variante für das Delta aus 13.1 vorliegt (13.2).

Verhältnis zu den Abschnitten 11 und 12: `orchestrator.md` ist damit **drittmal** am selben
Gegenstand re-baselined worden — `control-assessment-v1` (PR #822, vor dem Merge),
`fraud-risk-assessment-v1` (PR #824, nach dem Merge) und nun das Persona-/Versions-Delta aus
PR #840. Die Abschnitte ersetzen sich **nicht**; alle drei Einträge bleiben Teil des Nachweises,
weil sie drei unabhängige Delta-Ursachen auf derselben Fixture dokumentieren. Für die Reihenfolge
bleibt Abschnitt 12 der Präzedenzfall („Merge zuerst, dann re-baselieren") — die vorliegende
Re-Baseline folgt ihm.

## 14. Re-Baseline der Golden-Baseline für 3 Rollen (Task 12 Provider-Neutralität)

Erster Re-Baseline-Fall aus der **Provider-Audit-Opencode-v2**-Linie (nicht aus der
Slimming-Migration). Task 12 („Provider-neutral template body references", Commit `f41fe4e5`)
ersetzt fünf `.claude/`-literale Body-Referenzen durch provider-neutrale Formulierungen und hebt
`version` + `generated-from` der drei betroffenen Templates patchweise an. Drei dieser Rollen
besitzen eine eingefrorene Fixture und rutschen damit aus der Baseline.

> **Commit:** **noch nicht vorhanden** — die Re-Baseline wurde bewusst **nicht** committet
> (Aufgabengrenze: keine Git-Mutationen). Messbasis ist der Arbeitsbaum auf `a64412ac`
> (Branch `feat/provider-audit-opencode-v2`).
> **Gegenstand:** 3 von **58** eingefrorenen Golden-Fixtures.
> **Klassifikation:** **Baseline-Update nach Update-Regel**
> (`tests/fixtures/slimming-golden/README.md:73-77`) — **kein B2a-/B2b-Fall**; siehe 14.2/14.3.

### 14.1 Auslöser

Task 12 ändert drei `1-generic`-Templates inhaltlich (provider-neutrale Referenzen) und hebt
`version` patchweise:

| Rolle | Template | `version` | Delta |
|---|---|---|---|
| `agent-meta-manager` | `agents/1-generic/agent-meta-manager.md` | `1.22.0 → 1.22.1` | `.claude/skills/model-override-all/SKILL.md` → `{{SKILLS_DIR}}/…`; Sync-Workflow- und Handoff-Prosa provider-neutral |
| `agent-meta-scout` | `agents/1-generic/agent-meta-scout.md` | `1.5.0 → 1.5.1` | `tools: +Glob`; `evaluate-repository`-Locator via `Glob` statt hartem `.claude/`-Pfad |
| `release` | `agents/1-generic/release.md` | `1.12.0 → 1.12.1` | `pre-release-check.sh`-Pfad provider-neutral (`<provider-hooks-dir>`) + `Glob`-Locator |

Die Versionsfelder (`version:` **und** `generated-from: …@<version>`) verschieben das gerenderte
Frontmatter; die Body-Refs verschieben den gerenderten Body.

### 14.2 Mechanismus des Fehlschlags

Das Gate verzweigt (siehe 13.2): `agent-meta-scout` ist **unmigriert** ⇒ Byte-Identitätszweig
(`unexpected diff on an unmigrated role`); `agent-meta-manager`/`release` sind migriert, aber ihr
Delta ist **nicht** auf die vier Block-Kinds (`ANTI_RECURSION`, `OUTPUT_GUARD`,
`BACKGROUND_PROCESS_GUARD`, `PARSE_INPUT`) zurückführbar ⇒
`diff not attributable to declared normalizations`. `_LOCATORS` erkennt keine Versionsstrings und
keine Inline-Body-Prosa; eine erfundene Normalisierung hätte den Vertrag gebrochen.

### 14.3 Gewählte Fix-Route und Vertragsbeleg

Bewusste, über den **echten Sync-Pfad** erzeugte Re-Baseline nach dem Verfahrensvertrag
(`tests/fixtures/slimming-golden/README.md:22-41`), ausdrücklich **nicht** als Handedit und
**nicht** als Bulk-Kopie des gesamten `agents`-Baums (vgl. 13.3). Kein Eingriff in
`_MIGRATED_PATHS`, `_NORMALIZATIONS`, `_LOCATORS`, `_KIND_REGISTRY` oder `_GOLDEN_ROLE_COUNT`.

### 14.4 Nachweis der Herkunft (keine Handpflege)

- Erzeugung über den echten Sync-Pfad, Provider `Claude`:
  `AGENT_META_TEST_REPO="$PWD/.tmp/slimming-golden-gen" python3 scripts/sync.py --validate`
  (58 gerenderte Rollen) und ein zweiter Lauf in `.tmp/slimming-golden-gen2`.
- **Determinismus-Nachweis (Zweitrender):**
  `diff -r .tmp/slimming-golden-gen/.claude/agents .tmp/slimming-golden-gen2/.claude/agents`
  ⇒ **rc `0`, 0 Byte Ausgabe, 58 = 58 Dateien**.
- **Kopiert wurden ausschließlich die 3 vom Gate benannten Fixtures**, einzeln und verbatim; `cmp`
  bestätigt für jede Datei Byte-Gleichheit mit **beiden** Renders. Unter
  `tests/fixtures/slimming-golden/` weist `git status` genau diese 3 als geändert aus.
- sha256 der drei Fixtures im Arbeitsbaum (identisch zum jeweiligen Sync-Render):

  | Fixture | sha256 |
  |---|---|
  | `agent-meta-manager.md` | `01c47f8733310be5a2d316c2f1fa9d3e6862357e2afdfea79fa0592fab26d8b1` |
  | `agent-meta-scout.md` | `02ef5ebcbcbf066fba3c27b6dce615c3b4483b932ba228502c0d99e882be863e` |
  | `release.md` | `b2ac10db7a2d73ddb220fef2d1846d9c77c13bcf5ac3740e7639827e9a2ab155` |

### 14.5 Verifikation

| Prüfung | Ergebnis |
|---|---|
| `python3 -m pytest tests/test_template_slimming_equivalence.py -q` | **8 passed**, rc 0 |
| Vorher-Zustand des Gates | **1 failed** (7 passed) — nannte genau die 3 Rollen |
| Diff-Scope der Fixtures | `git diff --numstat`: `agent-meta-manager` 4/4, `agent-meta-scout` 7/3, `release` 7/7 |

Der Test-Korpus blieb unangetastet: **kein** Eingriff in `_MIGRATED_PATHS`, `_NORMALIZATIONS`,
`_LOCATORS`, `_KIND_REGISTRY` oder `_GOLDEN_ROLE_COUNT` (58, unverändert); keine Assertion wurde
geschwächt, übersprungen oder gelockert — das Gate behält seine Zähne.

### 14.6 Bestandsaufnahme

Die 3 re-baselined Fixtures sind nach dem Kopieren byte-identisch zum Render. Die übrigen 24 roh
abweichenden Fixtures bleiben von den deklarierten Normalisierungen absorbiert (mengen- und
setzgleich zu 13.6b) — die Re-Baseline hat keine andere eingefrorene Fixture verschoben.

### 14.7 Status B2a

B2a ist durch die Re-Baseline **wiederhergestellt**, nicht abgeschwächt: jede der 3 Fixtures
enthält exakt den vom aktuellen Template erzeugten Output, die Update-Regel ist erfüllt (dieser
Eintrag), und das Gate ist grün (14.5). Die Deltas aus 14.1 sind orthogonale Inhalts- und
Versionsänderungen; dies ist eine **Statusaussage** über B2a, keine Klassifikation der Änderung
als B2a-Fall (vgl. 8.7/13.7).

## 15. Re-Baseline der Golden-Baseline für 4 Rollen (Issue #826, pytest-Basetemp)

Derselbe Baseline-Update-Fall wie Abschnitt 14, diesmal ausgelöst **nicht** durch eine
Template-Inhaltsänderung, sondern durch eine **Projekt-Config-Änderung**: der #826-Fix ersetzt in
`.meta-config/project.yaml` (`TEST_COMMANDS`, Zeile 194) den bisherigen Testlauf durch den
kanonischen pytest-Aufruf mit externem Basetemp. Diese Variable wird in vier generierte Rollen
substituiert; deren eingefrorene Golden-Fixtures driften dadurch ausschließlich in dieser einen
Zeile.

> **Commit:** **noch nicht vorhanden** — die Re-Baseline wurde bewusst **nicht** committet
> (Aufgabengrenze: keine Git-Mutationen). Messbasis ist der Arbeitsbaum auf Tip `ff34638f`
> (Branch `fix/test-copytree-basetemp-recursion`, rebased auf `origin/main` `4bf62652`).
> **Gegenstand:** **4 von 58** eingefrorenen Golden-Fixtures:
> `tests/fixtures/slimming-golden/{documenter,e2e-tester,test-executor,tester}.md`
> (Aktive-Rollen-Menge, `tests/fixtures/slimming-golden/README.md:36-38`;
> `len(_golden_roles()) == _GOLDEN_ROLE_COUNT == 58`, unverändert).
> **Klassifikation:** **Baseline-Update nach Update-Regel**
> (`tests/fixtures/slimming-golden/README.md:90-94`) — **kein B2a-/B2b-Fall**.

### 15.1 Auslöser

Der Commit `ff34638f` (`chore(config): use external pytest basetemp in TEST_COMMANDS`) ändert
`TEST_COMMANDS` in `.meta-config/project.yaml` auf:

```
python scripts/sync.py --dry-run && python scripts/sync.py --validate && python3 -m pytest tests/ --basetemp=/tmp/$USER/pytest-agent-meta
```

und behält die bisherige Kette `python scripts/sync.py --dry-run && python scripts/sync.py --validate`
als Präfix bei. Der kanonische Aufruf ist ausdrücklich Teil des #826-Fixes
(`docs/RELEASE_GATES.md:425-446`) und darf nicht revertiert werden. `{{TEST_COMMANDS}}` ist in
genau vier aktiven Templates referenziert und rendert damit in vier Goldens:

| Rolle | Fixture-Zeile(n) | Template-Referenz |
|---|---|---|
| `documenter` | `:68` | `agents/1-generic/documenter.md:65` (`{{DEV_COMMANDS}}`/`{{TEST_COMMANDS}}`) |
| `e2e-tester` | `:73` | `agents/1-generic/e2e-tester.md:53` |
| `test-executor` | `:33`, `:41` | `agents/1-generic/test-executor.md:29,37` |
| `tester` | `:51` | `agents/1-generic/tester.md:48` |

Es handelt sich um eine **Konfigurationswert-Drift**, nicht um eine Änderung an Templates oder an
der Block-Extraktion; die Rollen-Templates selbst bleiben unverändert.

### 15.2 Mechanismus des Fehlschlags

Alle vier Rollen stehen in `_MIGRATED_PATHS`, nehmen also den Normalisierungs-Zweig des Gates
(`tests/test_template_slimming_equivalence.py:1176-1195`). Die einzige nicht absorbierte Abweichung
ist der `TEST_COMMANDS`-Literaltext in der jeweiligen Zeile; die Fehlermeldung nennt genau die vier
Rollen:

```
documenter (agents/1-generic/documenter.md): diff not attributable to declared normalizations
e2e-tester (agents/1-generic/e2e-tester.md): diff not attributable to declared normalizations
test-executor (agents/1-generic/test-executor.md): diff not attributable to declared normalizations
tester (agents/1-generic/tester.md): diff not attributable to declared normalizations
```

`_LOCATORS`/`_normalize` (`:348-353`, `:1073-1115`) arbeiten ausschließlich auf den vier
Block-Kinds aus `_KIND_CANONICAL_VAR` und erkennen keine Config-Literaltexte; eine erfundene
Normalisierung wäre ein Vertragsbruch. Zusätzlich trägt `documenter.md:60` das
**release-volatile** Projekt-Meta-Versionstoken (Freeze-Wert `1.2.0-beta.2`), das bereits durch
`_port_golden_meta_tokens` (`:1123-1147`) aus dem Render portiert wird — es ist **nicht** Teil der
gemeldeten, unattribuierten Drift.

### 15.3 Gewählte Fix-Route und Vertragsbeleg

**Bewusste Re-Baseline nach der Update-Regel** (`README.md:90-94`): ausschließlich die vier vom Gate
benannten Fixtures werden angepasst, **nur** an der `TEST_COMMANDS`-Fundstelle, exakt auf den Wert
aus dem realen Sync-Render (15.4). Kein Eingriff in `_MIGRATED_PATHS`, `_NORMALIZATIONS`,
`_LOCATORS`, `_KIND_REGISTRY`, `_GOLDEN_ROLE_COUNT` oder `_port_golden_meta_tokens`.

| Option | Bewertung |
|---|---|
| Alten `TEST_COMMANDS`-Wert in den Fixtures belassen | Nicht möglich — rendert den neuen kanonischen Aufruf, Gate rot |
| `TEST_COMMANDS` analog zu `{{AGENT_META_VERSION}}`/`{{AGENT_META_DATE}}` forward-porten | Nicht gewählt — das README deklariert den Forward-Port ausdrücklich für **release-volatile Meta-Tokens** (`:73-88`), nicht für beliebige Projekt-Config-Variablen; die gewählte Baseline-Aktualisierung hält die Forward-Port-Menge bewusst eng |
| **Verbatim-Kopie der ganzen Fixtures aus dem Render** (Muster 14.4) | **Nicht gewählt** — siehe Abgrenzung unten |
| **Gezielte Re-Baseline nur der `TEST_COMMANDS`-Fundstelle + Manifest-Eintrag** | **Gewählt** |

**Abgrenzung zur Verbatim-Kopie (bewusst, nicht als Bequemlichkeit):** Eine vollständige
Verbatim-Kopie der vier Fixtures wäre hier **schädlich**:

1. Sie würde in `documenter.md:60` das **release-volatile** Projekt-Versionstoken auf den aktuellen
   Wert (`2.0.0-beta.1`) einfrieren. Genau das soll der Forward-Port vermeiden: der eingefrorene
   Wert `_GOLDEN_META_VERSION` wäre danach ein toter Treffer, und beim **nächsten** Release würde
   die Fixture erneut reißen (vgl. `README.md:73-81`, „force a fixture rebaseline on every
   release"). Alle Fixtures, die das Projekt-Meta-Versionstoken tragen (`agent-meta-manager`,
   `agent-meta-scout`, `documenter`, `meta-feedback`), tragen weiterhin den Freeze-Wert
   `1.2.0-beta.2`; keine der 58 enthält `2.0.0-beta.1` (neu gemessen).
2. Sie würde in `tester`/`e2e-tester`/`test-executor` zusätzlich die **B2a-normalisierten** Regionen
   (Leerzeile unter `## 1. Parse input`, Output-Guard-Markerposition) auf den Post-Slimming-Stand
   ziehen. Diese Regionen werden derzeit noch von der deklarierten Normalisierung absorbiert und
   sind damit Teil der Gate-Zähne; eine Kopie würde diese Abdeckung stillschweigend entfernen
   („mask future regressions").

Die gezielte Ersetzung ändert daher **genau eine** unattribuierte Drift pro Fixture (bei
`test-executor` zwei identische Vorkommen) und lässt jede andere eingefrorene Zeile — inklusive
aller B2a-/B2b-Belegregionen und der release-volatilen Meta-Tokens — unangetastet.

### 15.4 Nachweis der Herkunft (keine Handpflege)

- Erzeugung über den **echten Sync-Pfad**, Provider `Claude`, wörtlich der Verfahrensvertrag
  (`README.md:29-31`):

  ```bash
  mkdir -p .tmp/golden826
  AGENT_META_TEST_REPO="$PWD/.tmp/golden826" python3 scripts/sync.py --validate
  ```

  Ergebnis: rc `0` (58 gerenderte Rollen).
- Der Render-Diff `diff tests/fixtures/slimming-golden/<rolle>.md .tmp/golden826/.claude/agents/<rolle>.md`
  zeigt für die vier Rollen **nur** die `TEST_COMMANDS`-Zeile(n) plus (bei `documenter`)
  das bereits forward-portete Projekt-Versionstoken sowie die deklarierten
  Normalisierungsregionen. Die neue `TEST_COMMANDS`-Zeile wurde **verbatim** aus dem Render
  übernommen, nicht aus der Config abgeschrieben.
- Das substituierte Literal ist umgebungsunabhängig (kein absoluter Pfad, kein Hostname, keine
  SHA); es ist exakt der in `.meta-config/project.yaml:194` definierte kanonische Aufruf
  (`docs/RELEASE_GATES.md:441-443`).

### 15.5 Verifikation

| Prüfung | Ergebnis |
|---|---|
| Vorher: `pytest …::test_golden_equivalence_and_normalization_marking` | **1 failed**, rc `1` — nannte genau `documenter`, `e2e-tester`, `test-executor`, `tester` |
| Nachher: dieselbe Test-Node | **1 passed**, rc `0` |
| `pytest tests/test_template_slimming_equivalence.py -q` (ganze Datei) | **8 passed**, rc `0` |
| `python3 scripts/sync.py --validate` | rc `0` (82 vorbestehende Konsistenz-Warnungen, unverändert) |
| Diff-Scope `git diff --numstat` | genau 4 Fixtures: `documenter.md` 1/1, `e2e-tester.md` 1/1, `test-executor.md` 2/2, `tester.md` 1/1 |
| Konfliktmarker in den geänderten Dateien | keine |

### 15.6 Bestandsaufnahme aller 58 Goldens

`git status --short` weist nach der Änderung genau die vier genannten Fixtures als geändert aus;
die übrigen **54** Fixtures und der Gate-Korpus (`_GOLDEN_ROLE_COUNT == 58`, keine Assertion
gelockert) bleiben unangetastet. Die Re-Baseline hat keine andere eingefrorene Fixture verschoben.

### 15.7 Status B2a

B2a ist durch die Re-Baseline **wiederhergestellt**, nicht abgeschwächt: die vier Fixtures enthalten
an der `TEST_COMMANDS`-Fundstelle exakt den vom aktuellen Sync-Pfad erzeugten Output, die
Update-Regel ist erfüllt (dieser Eintrag), und das Gate ist grün (15.5). Die Änderung ist eine
orthogonale Config-Wert-Aktualisierung; dies ist eine **Statusaussage** über B2a, keine
Klassifikation der Änderung als B2a-Fall (vgl. 8.7/14.7).
