# Re-Review: Opencode-Einstiegspunkt (#1006) — Spec Rev. 1.1 + Plan

> Reviewte Dateien: `docs/specs/2026-10-22-opencode-entrypoint-1006-spec.md` (Rev. 1.1, Status: Entwurf),
> `docs/plans/2026-10-22-opencode-entrypoint-1006-plan.md` (Status: Entwurf)
> Vorheriges Review: `docs/reviews/2026-10-22-opencode-entrypoint-1006-spec-review.md` (CHANGES_REQUESTED)
> Spec-ID: `SPEC-OPENCODE-ENTRYPOINT-1006-2026-10-22`
> Reviewer: concept-reviewer · Datum: 2026-10-22 · Modus: fokussierter Re-Review (Reflection-Loop R2)

## Scope

1. Nachprüfung MAJOR-1..3 und MINOR-1..6 aus dem Erst-Review, plus Suche nach neuen Widersprüchen
   (ADR-5 scoped allow-list, Config-Key `opencode_primary_edit_allow`, Serializer für verschachteltes `permission`).
2. Plan: AC-Abdeckung, Existenz von Pfaden/Symbolen, TDD-Reihenfolge, Abhängigkeiten, `parallel_group`-Disjunktheit.

Gegen Code geprüft: `scripts/lib/{provider_transform,isolation,providers,frontmatter,sync_pipeline,cli_commands,active_set,log}.py`,
`config/provider-tools.yaml`, `tests/{test_transform_contracts,test_opencode_runtime_gate,test_runtime_gate_wiring,test_ac01_render_identity}.py`,
`tests/scenarios/asserts/69-opencode-v2-surface.sh`, `rules/1-generic/plan-ledger.md`, `agents/1-generic/orchestrator.md`,
opencode.ai/docs/permissions.

## Formale Checks (§8)

| Check | Ergebnis |
|---|---|
| Pflichtsektionen | grün |
| Trace-Anker | grün (Frontmatter + Sektion; Plan referenziert ihn) |
| Approval-Marker | grün (`Entwurf`, konsistent; OQ-3 Nutzerbestätigung offen) |
| No-Placeholder | grün |

## Status der Erst-Review-Findings

| Finding | Status | Beleg |
|---|---|---|
| MAJOR-1 AC-01 | behoben | AC-01: 2 geändert + 1 hinzugefügt, Matrix nicht-strikt, Goldens unverändert. Hash-Normalisierung (`_hash_file` reduziert `generated-file-hashes.json` auf Pfadmenge) stützt „2+1"; Plan Task 11 hat Stop-Kriterium. |
| MAJOR-2 Test-Impact | behoben | AC-15(b) 1–5 mit Soll-Assertion; Zählungen im Plan stimmen (9 Tests in `test_opencode_runtime_gate.py`, 10 in `test_runtime_gate_wiring.py`). |
| MAJOR-3 edit-deny/Alternative | behoben (mit neuem Folgefund, siehe MAJOR-A) | ADR-5 wägt A vs. B, R-2 konkretisiert, AC-11 beide Varianten. |
| MINOR-1 OQ-1 per Doku | behoben | Zitat + URL in Problem/OQ-1, ADR-2 zitiert v1-Evidenz. |
| MINOR-2 Verhaltensänderung | behoben | Ziel 1, R-8, ADR-6 (`mode: all` verworfen), CHANGELOG, `orchestrator_hint` (IC-8). |
| MINOR-3 Lockout | behoben | R-9, Warntext AC-07/IC-6. |
| MINOR-4 Lazy-Imports | behoben | `explicit_primary_role` in `providers.py`; nur ein Lazy-Import (`provider_transform` → `isolation`). |
| MINOR-5 v2-Rollback | behoben | ADR-3 „bewusste Grenze" + AC-08. |
| MINOR-6 Pfad | behoben | `python3 scripts/sync.py --validate`. |

Verifiziert: `config/provider-tools.yaml` existiert, flache Top-Level-Keys, `opencode_deny_critical` an `:56`;
`load_provider_tools_config` (frontmatter.py:61) ist einziger Loader, keine Key-Iteration, die einen neuen
Listen-Key falsch interpretieren würde. Serializer `_update_frontmatter_dict` nutzt
`yaml.dump(default_flow_style=False, sort_keys=False)` — verschachtelte Mappings in Einfügereihenfolge, `'*'` wird
gequotet; Task 4 als Charakterisierung angemessen.

## Findings

### MAJOR

**MAJOR-A · Logik/Risiken · IC-3-Prämisse falsch: `edit` steht IMMER im Mapping — scoped allow-list kann Rechte erweitern**
IC-3: „`deny_edit=True` ersetzt `perms["edit"]` (nur falls `edit` im Mapping vorkommt, **d.h. Rolle hat `Write`/`Edit`**)".
Das stimmt nicht: `_map_claude_tools_to_opencode_permissions` (`provider_transform.py:746-749`) setzt über
`opencode_deny_critical: [Bash, Write, Edit]` für jede Rolle OHNE `Write`/`Edit` `edit: "deny"`. Folge:
- Vertrag wie geschrieben macht aus `edit: "deny"` einer Primary-Rolle ohne Write-Tool `{"*": "deny", ".tmp/**": "allow", …}` —
  **Rechte-Erweiterung** durch einen Sperr-Mechanismus.
- Plan Task 8 Test 7 (`tools: [Read]` → `"edit" not in permission`) ist gegen den Code falsch und wird rot
  (erwartet ist real `edit == "deny"`); die Rot/Grün-Prognose „4 failed, 4 passed" stimmt damit ebenfalls nicht.
Real-Output heute unbetroffen (Orchestrator hat `Write`), aber Vertrag und Test sind fehlerhaft.
*Fix:* IC-3 auf „nur wenn `perms.get("edit") == "allow"`" präzisieren (sonst unverändert); AC-11 um „Primary-Rolle ohne
Write/Edit → `edit == "deny"` unverändert" ergänzen; Plan Task 8 Interface + Test 7 entsprechend umstellen.

### MINOR

**MINOR-A · Konsistenz · AC-12(a) widerspricht ADR-5-Default**
AC-12(a) fordert für den Self-Sync `edit: deny`; nach ADR-5/OQ-3-Default B ist es das Mapping
`{"*": deny, ".tmp/**": allow, ".meta-viz/**": allow}` (so erwartet es auch Plan Task 12 Step 2).
*Fix:* AC-12(a) auf „`permission.edit` gemäß AC-11 (Option laut OQ-3)" umformulieren.

**MINOR-B · Annahmen · Pfad-Semantik der allow-list unbelegt**
opencode.ai/docs/permissions definiert `*`/`?`, nicht `**`, und sagt nicht, ob `edit`-Patterns gegen relative oder
absolute Pfade matchen (Beispiele mischen beides). Matcht Opencode absolut, greifen `.tmp/**`/`.meta-viz/**` nie →
Option B degradiert stillschweigend zu A (fail-closed, kein Sicherheitsproblem, aber ADR-5-Ziel verfehlt). Task 1 Probe
deckt das ab, ist aber optional; `CONFIRMED_BY_DOC` reicht als Gate für Task 8.
*Fix:* R-2 um dieses Restrisiko ergänzen; im Plan Task 1 die Pfad-Semantik als eigene Zeile im Evidenzdokument
(„nicht belegt" zulässig) und in Task 8 als markierte Unsicherheit führen.

**MINOR-C · Vollständigkeit · R-2 nennt Plan-Ledger-Fallback nicht**
`rules/1-generic/plan-ledger.md:36-38`: Checkbox-Pflege der Plan-Datei (`docs/plans/*.md`) erfolgt per Writer-Skript
(braucht `bash`, ohnehin `deny`) mit manuellem Edit als Fallback — beides ist dem Opencode-Orchestrator unter Strict
verwehrt, auch mit Option B. Außerdem ist `progress.checkpoint-dir` konfigurierbar (R-2 erwähnt Drift, aber keine Ableitung).
*Fix:* R-2 um „Plan-Ledger-Checkboxen nur via Subagent" ergänzen (akzeptiert oder Folge-Issue).

**MINOR-D · Plan/TDD · Falsche Rot-Prognosen in Task 5 und Task 6**
- Task 5 Step 2: Modul-Konstante `_DEFAULT_AGENT_KEY = isolation._STATE_DEFAULT_AGENT_KEY` wirft beim Import →
  Collection-Error der ganzen Datei (`1 error`), nicht „5 failed, 9 passed".
- Task 6 Step 2: der Helfer `_sync(...)` übergibt immer `active_set=` → auch Test 9 und 10 scheitern mit `TypeError`
  → „10 failed", nicht „8 failed".
*Fix:* Erwartungen korrigieren (oder Konstante lazy im Test lesen / Helfer `active_set` nur bei Bedarf übergeben).

**MINOR-E · Plan · Aussage zur Rot-Phase von Szenario 69 falsch**
Global Constraints: „Szenario 69 bleibt bis Task 10 grün (kein v1-`default_agent`-Assert greift vor Task 6)". Tatsächlich
wird `69-opencode-v2-surface.sh:141` (`assert "default_agent" not in doc`) ab Task 6 rot (Merge schreibt `default_agent`
auf v1 mit realem `primary-role`) und erst mit Task 10 wieder grün. Kein Blocker (Tasks 6–9 laufen keine Szenarien).
*Fix:* Rot-Phase „Szenario 69: Task 6 → Task 10" analog zu AC-01 deklarieren.

### INFO

- **INFO-A** Plan weicht bewusst von IC-3 ab (Rückgabetyp von `_map_claude_tools_to_opencode_permissions` bleibt `dict[str, str]`,
  Ersetzung im Transform) — dokumentiert, verhaltensgleich, ok.
- **INFO-B** R-8: der neue Default-Agent in nicht-strikten Projekten hat `bash: deny` (aus `opencode_deny_critical`) — der Main
  Chat verliert gegenüber `build` die Shell. Ein Halbsatz in R-8/CHANGELOG würde die Verhaltensänderung vollständig benennen.
- **INFO-C** `_opencode_entry_point` könnte `active_set.has(role)` statt `role in active_set.roles` nutzen (beides existiert,
  `active_set.py:66`).

## Plan-Prüfung

| Prüfpunkt | Ergebnis |
|---|---|
| AC-Abdeckung | vollständig: AC-01→11, 02–04→2/3, 05→3/15, 06–09/14→6, 10→7, 11→1/4/8, 12→12, 13→5, 15→3/7/10/11/15, 16→14; OQ-5 (mit/ohne `active_set`) über Task 5/7. |
| Pfade/Symbole | existieren: `_apply_agent_transform`, `_transform_frontmatter_for_opencode`, `_map_claude_tools_to_opencode_permissions`, `_update_frontmatter_dict`, `_read_state`/`_write_state`, `_opencode_runtime_gate_entries`, `_sync_stage_per_provider` (Param `active_set`), `cli_commands.py:221` `active_set`, `ActiveSet.roles`, `SyncLog.warnings`, `_orchestrator_hints`, alle referenzierten Testdateien, `routing-llm-eval/provider-opencode.sh`. |
| TDD-Reihenfolge | korrekt bis auf Prognosen (MINOR-D, MAJOR-A Test 7). Task 6 lässt bestehende Fixtures ohne `primary-role` → kein `default_agent` → Altvergleiche bleiben grün; Kopplung erst Task 7 — sauber gestaffelt. |
| Abhängigkeiten | konsistent mit DAG-Zeile; keine Zyklen. Task 8 korrekt auf 1/3/4/5 gegated. |
| `parallel_group` g1 | {1, 2, 4, 13} dateidisjunkt (docs/analysis · providers.py + neuer Test · test_agents_frontmatter.py + frontmatter.py · 3 docs/specs). |

## Verdict

**CHANGES_REQUESTED** (Iteration 2)

Begründung: Alle Erst-Review-Findings sind sauber behoben, Config-Key/Datei und Serializer-Annahme halten. Ein neuer MAJOR
blockiert: der IC-3-Vertrag beruht auf einer falschen Prämisse (`edit` ist dank `opencode_deny_critical` immer im Mapping)
und würde einer Primary-Rolle ohne Write-Tool Schreibrechte gewähren; der zugehörige Plan-Test ist gegen den Code falsch.
Fix ist eine Ein-Satz-Präzisierung in IC-3/AC-11 plus Anpassung Task 8. MINOR-A..E sind schnell nachziehbar; danach
genügt eine Prüfung von MAJOR-A und MINOR-A.

### correction_hints

1. IC-3/AC-11: Ersetzung nur bei `perms.get("edit") == "allow"`; Fall „Primary ohne Write → `edit: deny` unverändert" als AC.
2. Plan Task 8: Interface + Test 7 (`edit == "deny"`) + Rot-Prognose anpassen.
3. AC-12(a): `edit` gemäß AC-11/OQ-3 statt `edit: deny`.
4. R-2: Pfad-Semantik-Restrisiko (relativ/absolut, `**`) und Plan-Ledger-Fallback ergänzen; Task 1 dokumentiert Pfad-Semantik.
5. Plan: Rot-Prognosen Task 5/6 und Szenario-69-Rot-Phase (Task 6→10) korrigieren.
